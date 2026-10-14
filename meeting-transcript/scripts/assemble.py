"""Join the merge results (auto_merge.py) of every window into transcript parts (JSON + Markdown).

Per meeting: windows in order -> duplicate check at each join -> speaker check against diarization
-> silence / pause / Plaud-mark entries -> split into PARTS (config) -> write
transcript/<folder>/<date>_<HHMM>_<slug>.json and .md, plus transcript/index.json (one entry per
part with the header data the Markdown needs). Meetings with missing merge results are skipped.
Join and speaker decisions go to WORK/merge/assemble_log.json. meeting.json "aliases" (speaker id
renames) and "corrections" (reviewed text fixes) are applied on top of the merge results.
Usage: python assemble.py [meeting ...]
"""
from __future__ import annotations

import difflib
import json
import sys
from datetime import datetime

from config import ALIASES, CORRECTIONS, MEETINGS, OUT, PARTS, SOURCES, TOPIC_TH, TZ, WORK, epoch_to_source_ms, hms, local_str
from render import render
from timeline import marks, meeting_spans, recordings_at, speakers_in

TAG_NAMES = {"WL": "wispr-live", "WR": "wispr-refined", "PL": "plaud", "TH": "whisper-th",
             "V3": "whisper-large-v3", "TA": "whisper-th-2nd-mic"}
SILENCE_MS = 60_000


def to_epoch(meeting: str, hhmmss: str) -> float:
    return datetime.fromisoformat(f"{MEETINGS[meeting]['date']}T{hhmmss}").replace(tzinfo=TZ).timestamp() * 1000


def fix(pid: str, r: dict) -> dict:
    r = {**r, "speaker": ALIASES.get(r.get("speaker"), r.get("speaker"))}
    for c in CORRECTIONS:
        if c["packet"] == pid and r.get("start") == c["start"] and c["old"] in r["text"]:
            r["text"] = r["text"].replace(c["old"], c["new"])
            r["note"] = (r.get("note", "") + " " + c["note"]).strip()
    return r


def load_windows(meeting: str, log: list) -> list[dict]:
    wins = json.loads((WORK / "merge" / "windows.json").read_text())[meeting]
    out = []
    for i, _ in enumerate(wins, 1):
        rows = json.loads((WORK / "merge" / "out" / f"{meeting}-{i:02d}.json").read_text())
        segs = []
        for r in rows:
            r = fix(f"{meeting}-{i:02d}", r)
            t0 = to_epoch(meeting, r["start"])
            t1 = to_epoch(meeting, r.get("end", r["start"]))
            segs.append({**r, "t0": t0, "t1": max(t1, t0), "window": i})
        if out and segs:  # duplicate check across the join
            for s in segs[:3]:
                for p in out[-3:]:
                    same = difflib.SequenceMatcher(None, p["text"], s["text"]).ratio()
                    if same > 0.6 and min(p["t1"], s["t1"]) - max(p["t0"], s["t0"]) > 0:
                        s["drop"] = True
                        log.append({"join": f"{meeting}-{i - 1:02d}/{i:02d}", "dropped": s["start"], "kept": p["start"],
                                    "similarity": round(same, 2)})
        out += [s for s in segs if not s.get("drop")]
    return sorted(out, key=lambda s: s["t0"])


def check_speaker(meeting: str, s: dict, log: list) -> str:
    shares = speakers_in(meeting, s["t0"], s["t1"])
    total = sum(v for _, v in shares) or 1
    mine = dict(shares).get(s["speaker"], 0) / total
    if shares and mine < 0.2 and shares[0][1] / total > 0.7 and not s.get("speaker_note") and s["t1"] - s["t0"] > 2000:
        log.append({"speaker_override": f"{meeting} {s['start']}", "from": s["speaker"], "to": shares[0][0]})
        return shares[0][0]
    return s["speaker"]


def audio_pos(meeting: str, t: float) -> dict:
    out = {}
    for src in recordings_at(meeting, t):
        pos = epoch_to_source_ms(src, t)
        if pos is not None:
            out[src] = round(pos / 1000, 1)
    return out


def entries(meeting: str, log: list) -> list[dict]:
    rows = []
    for s in load_windows(meeting, log):
        if s.get("type") == "mark":
            continue  # marks come from the source list below (exact times)
        rows.append({"t0": s["t0"], "t1": s["t1"], "kind": "speech", "speaker": check_speaker(meeting, s, log),
                     "text": s["text"].strip(), "sources": [TAG_NAMES[x] for x in s["sources"]],
                     "confidence": s["confidence"], **({"note": s["note"]} if s.get("note") else {}),
                     **({"speaker_note": s["speaker_note"]} if s.get("speaker_note") else {})})
    for m in marks(meeting):
        rows.append({"t0": m["epoch"], "t1": m["epoch"], "kind": "mark", "speaker": "—",
                     "text": f"Plaud mark (ภาพถ่าย; คำบรรยายภาพโดย AI ของ Plaud): {m['caption']}",
                     "sources": [f"plaud-mark:{m['plaud_file']}#{m['mark_id']}"], "confidence": "high"})
    spans = meeting_spans(meeting)
    speech = sorted((r for r in rows if r["kind"] == "speech"), key=lambda r: r["t0"])
    edges = [(spans[0][0], spans[0][0])] + [(r["t0"], r["t1"]) for r in speech] + [(spans[-1][1], spans[-1][1])]
    for (a0, a1), (b0, _) in zip(edges, edges[1:]):
        gap_from = max(a1, a0)
        for s0, s1 in spans:  # silence only inside recorded spans
            lo, hi = max(gap_from, s0), min(b0, s1)
            if hi - lo >= SILENCE_MS:
                recs = sorted({x for t in (lo, hi - 1) for x in recordings_at(meeting, t)})
                rows.append({"t0": lo, "t1": hi, "kind": "silence", "speaker": "—",
                             "text": f"[ไม่มีเสียงพูด ~{round((hi - lo) / 60000)} นาที]",
                             "sources": recs, "confidence": "high"})
    for (_, e0), (s1, _) in zip(spans, spans[1:]):
        rows.append({"t0": e0, "t1": s1, "kind": "paused", "speaker": "—",
                     "text": f"[หยุดอัดเสียง {hms(e0)}–{hms(s1)}: ไม่มีเครื่องใดอัดอยู่]", "sources": [], "confidence": "high"})
    return sorted(rows, key=lambda r: (r["t0"], r["kind"] != "speech"))


def finish(meeting: str, rows: list[dict], origin: float) -> list[dict]:
    out = []
    for r in rows:
        seg = {"start_ms": round(r["t0"] - origin), "end_ms": round(r["t1"] - origin),
               "start_local": local_str(r["t0"]), "end_local": local_str(r["t1"]),
               "speaker": r["speaker"], "speaker_id": r["speaker"] if r["kind"] == "speech" else None,
               "text": r["text"], "sources": r["sources"], "confidence": r["confidence"]}
        if r["kind"] != "speech":
            seg["kind"] = r["kind"]
        else:
            seg["audio_pos_s"] = audio_pos(meeting, r["t0"])
        for k in ("note", "speaker_note"):
            if r.get(k):
                seg[k] = r[k]
        out.append(seg)
    return out


def write_part(part: tuple, sel: list[dict], lo: float, hi: float, origin: float, first: str) -> dict:
    m, _, folder, slug, title = part
    spans = meeting_spans(m)
    start = sel[0]["t0"] if lo == origin else lo
    end = min(hi, max(r["t1"] for r in sel)) if hi != float("inf") else spans[-1][1]
    name = f"{MEETINGS[m]['date']}_{datetime.fromtimestamp(start / 1000, TZ):%H%M}_{slug}"
    segs = finish(m, sel, origin)
    recs = ", ".join(f"{SOURCES[s]['kind']} `{SOURCES[s]['id']}`" for s in MEETINGS[m]["sources"]
                     if any(epoch_to_source_ms(s, t) is not None for t in (start + 1, (start + end) / 2, end - 1)))
    meta = {"date": MEETINGS[m]["date"], "start_hm": hms(start)[:5], "title": title, "start_hms": hms(start),
            "end_hms": hms(end), "topic_th": TOPIC_TH[folder], "recordings": recs,
            "origin_local": local_str(origin), "origin_note": f"จุดเริ่มของไฟล์เสียง `{SOURCES[first]['id']}`"}
    d = OUT / "transcript" / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1) + "\n")
    (d / f"{name}.md").write_text(render(meta, segs))
    print(f"{folder}/{name}: {len(segs)} entries")
    return {"file": f"{folder}/{name}", "meeting": m, **meta}


def complete(meeting: str) -> bool:
    n = len(json.loads((WORK / "merge" / "windows.json").read_text())[meeting])
    return all((WORK / "merge" / "out" / f"{meeting}-{i:02d}.json").exists() for i in range(1, n + 1))


def main():
    log, written = [], []
    for meeting in sys.argv[1:] or list(MEETINGS):
        if not complete(meeting):
            print(f"SKIP {meeting}: merge results missing")
            continue
        rows = entries(meeting, log)
        origin = meeting_spans(meeting)[0][0]
        first = min(MEETINGS[meeting]["sources"], key=lambda s: abs(epoch_to_source_ms(s, origin + 1) or 1e12))
        parts = [p for p in PARTS if p[0] == meeting]
        cuts = [to_epoch(meeting, p[1]) if p[1] else origin for p in parts] + [float("inf")]
        for part, lo, hi in zip(parts, cuts, cuts[1:]):
            sel = [r for r in rows if lo <= r["t0"] < hi]
            if sel:
                written.append(write_part(part, sel, lo, hi, origin, first))
    index = OUT / "transcript" / "index.json"
    old = [e for e in json.loads(index.read_text()) if e["meeting"] not in {w["meeting"] for w in written}] if index.exists() else []
    index.write_text(json.dumps(sorted(old + written, key=lambda e: (e["date"], e["start_hms"])), ensure_ascii=False, indent=1) + "\n")
    (WORK / "merge" / "assemble_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1))
    print(f"{len(written)} parts, {len(log)} join/speaker decisions logged")


if __name__ == "__main__":
    main()
