"""Merge one window by script, no LLM (an LLM merge of ~6 h of audio cost > USD 270; this takes seconds).

Text: Wispr refined first (clearest mic), then Plaud, Wispr live, Whisper-th only to fill gaps none of
them cover. Speaker: diarization id with the most time inside the segment. Confidence: how closely the
other sources heard the same words in the same seconds (difflib ratio). Low-confidence segments keep
the other sources' text in `note` so a reader can check them. Writes WORK/merge/out/<pid>.json
(list of {start, end, speaker, text, sources, confidence, note?, speaker_note?}); windows that already
have a result are left alone. pid = <meeting>-<NN> as listed in WORK/merge/windows.json.
Usage: python auto_merge.py [pid ...]   (no args: every window without a result)
"""
from __future__ import annotations

import difflib
import json
import sys
from datetime import datetime

from config import TZ, WORK
from timeline import asr_segments, diar_turns, service_segments, speakers_in

ORDER = ("WR", "PL", "WL", "TH")  # accuracy order: Wispr refined > Plaud > Wispr live > Whisper-th (gap filler)
OVERLAP_SKIP = 0.5  # drop a lower-priority segment when half of it is already covered


def stamp(ms: float) -> str:
    return datetime.fromtimestamp(ms / 1000, TZ).strftime("%H:%M:%S.%f")[:10]


def norm(t: str) -> str:
    return "".join(t.split())


def heard_by_others(seg: dict, pool: list[dict]) -> dict[str, str]:
    """Text each other source has in the same seconds (±1 s)."""
    out: dict[str, list[str]] = {}
    for s in pool:
        if s["tag"] == seg["tag"] or s["tag"] not in ("WR", "PL", "WL", "TH"):
            continue
        if s["end"] > seg["start"] - 1000 and s["start"] < seg["end"] + 1000:
            out.setdefault(s["tag"], []).append(s["text"])
    return {k: " ".join(v) for k, v in out.items()}


def found(mine: str, other: str) -> float:
    """Share of this segment's characters that the other source also has, in order."""
    if not mine:
        return 0.0
    blocks = difflib.SequenceMatcher(None, mine, norm(other), autojunk=False).get_matching_blocks()
    return sum(b.size for b in blocks) / len(mine)


def confidence(seg: dict, others: dict[str, str]) -> tuple[str, list[str]]:
    mine = norm(seg["text"])
    score = {t: found(mine, txt) for t, txt in others.items()}
    agree = [t for t, v in score.items() if v >= 0.6]
    if agree:
        return "high", agree
    if any(v >= 0.35 for v in score.values()) or not others:
        return "medium", []
    return "low", []


def nearest_speaker(meeting: str, t: float) -> str:
    turns = diar_turns(meeting)
    return min(turns, key=lambda x: min(abs(x[0] - t), abs(x[1] - t)))[2] if turns else "S0"  # S0 = no speaker known


def merge(pid: str) -> list[dict]:
    meeting, idx = pid.rsplit("-", 1)
    a, b = json.loads((WORK / "merge" / "windows.json").read_text())[meeting][int(idx) - 1]
    pool = [s for s in service_segments(meeting) + asr_segments(meeting) if a - 5000 < s["start"] < b + 5000]
    chosen: list[dict] = []
    for tag in ORDER:
        for s in (x for x in pool if x["tag"] == tag and a <= x["start"] < b and x["text"].strip()):
            dur = max(s["end"] - s["start"], 1)
            covered = sum(max(0, min(s["end"], c["end"]) - max(s["start"], c["start"])) for c in chosen)
            if covered / dur < OVERLAP_SKIP:
                chosen.append(s)
    chosen.sort(key=lambda s: s["start"])
    out, prev_end = [], a
    for s in chosen:
        start, end = max(s["start"], prev_end), max(s["end"], max(s["start"], prev_end) + 100)
        if start >= b and out:  # pushed past the window by an earlier overlap: keep its words on the previous line
            out[-1]["text"] += " " + s["text"].strip()
            continue
        spk = speakers_in(meeting, start, end)
        others = heard_by_others(s, pool)
        conf, agree = confidence(s, others)
        seg = {"start": stamp(start), "end": stamp(end), "speaker": spk[0][0] if spk else nearest_speaker(meeting, start),
               "text": s["text"].strip(), "sources": [s["tag"], *agree], "confidence": conf}
        if conf == "low":
            seg["note"] = "other sources heard: " + " | ".join(f"{k}: {v[:300]}" for k, v in others.items())
        if s["tag"] in ("PL", "WL") and s.get("label"):
            seg["speaker_note"] = f"{s['tag']} label {s['label']}"
        out.append(seg)
        prev_end = end
    return out


def main():
    windows = json.loads((WORK / "merge" / "windows.json").read_text())
    pids = sys.argv[1:] or [f"{m}-{i + 1:02d}" for m, ws in windows.items() for i in range(len(ws))]
    for pid in pids:
        path = WORK / "merge" / "out" / f"{pid}.json"
        if path.exists() and not sys.argv[1:]:
            continue
        segs = merge(pid)
        path.write_text(json.dumps(segs, ensure_ascii=False, indent=1))
        conf = {c: sum(1 for s in segs if s["confidence"] == c) for c in ("high", "medium", "low")}
        print(pid, len(segs), conf)


if __name__ == "__main__":
    main()
