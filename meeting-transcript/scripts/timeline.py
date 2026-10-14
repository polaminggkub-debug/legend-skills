"""Load every hypothesis (Plaud, Wispr live/refined, Whisper passes, diarization, marks) on the
wall clock, so packets, assembly and coverage all read the same data.

All times returned are epoch ms (shown in the configured time zone via config.hms / local_str).
Library module: imported by the other scripts, nothing to run.
Usage: from timeline import service_segments, asr_segments, diar_turns, marks, meeting_spans
"""
from __future__ import annotations

import json
from functools import lru_cache

from config import MEETINGS, SOURCES, WORK, source_span_epoch_ms, source_to_epoch_ms

# Short source tags used in packets, transcripts and coverage
TAGS = {"plaud": "PL", "wispr-live": "WL", "wispr-refined": "WR", "th": "TH", "v3": "V3", "th-alt": "TA"}
NAMES = {"PL": "Plaud transcript", "WL": "Wispr live", "WR": "Wispr refined", "TH": "Whisper Thai fine-tune",
         "V3": "Whisper large-v3", "TA": "Whisper Thai on 2nd recording"}


def meeting_of(src: str) -> list[str]:
    return [m for m, meta in MEETINGS.items() if src in meta["sources"]]


@lru_cache(maxsize=None)
def service_segments(meeting: str) -> list[dict]:
    """Plaud + Wispr transcript segments of one meeting on the wall clock."""
    out = []
    for f in sorted((WORK / "parsed").glob("*.jsonl")):
        kind, src = f.stem.split("__")
        if src not in MEETINGS[meeting]["sources"]:
            continue
        for line in open(f):
            r = json.loads(line)
            out.append({"tag": TAGS[kind], "src": src, "start": source_to_epoch_ms(src, r["pos_start_ms"]),
                        "end": source_to_epoch_ms(src, r["pos_end_ms"]), "label": r["speaker"], "text": r["text"],
                        "pos_ms": r["pos_start_ms"]})
    return sorted(out, key=lambda s: s["start"])


@lru_cache(maxsize=None)
def asr_segments(meeting: str) -> list[dict]:
    """Whisper segments (th, v3, th-alt) of one meeting on the wall clock, with words."""
    out = []
    for model, tag in (("th", "TH"), ("v3", "V3"), ("th-alt", "TA")):
        for f in sorted((WORK / "asr" / model).glob("*.json")) if (WORK / "asr" / model).exists() else []:
            doc = json.loads(f.read_text())
            if doc["meeting"] != meeting:
                continue
            src = doc["src"]
            for s in doc["segments"]:
                if not s["text"]:
                    continue
                out.append({"tag": tag, "src": src, "start": source_to_epoch_ms(src, s["start"] * 1000),
                            "end": source_to_epoch_ms(src, s["end"] * 1000), "text": s["text"],
                            "logprob": s["avg_logprob"], "pos_ms": s["start"] * 1000,
                            "words": [(source_to_epoch_ms(src, w[0] * 1000), source_to_epoch_ms(src, w[1] * 1000), w[2], w[3])
                                      for w in s["words"]]})
    return sorted(out, key=lambda s: s["start"])


@lru_cache(maxsize=None)
def diar_turns(meeting: str) -> list[tuple[float, float, str]]:
    """Diarization turns (epoch start, end, global speaker id) for the meeting's main recordings."""
    p = WORK / "diar" / "turns.json"
    if not p.exists():
        return []
    turns = json.loads(p.read_text()).get(meeting, [])
    return [tuple(t) for t in turns]


def speakers_in(meeting: str, a: float, b: float) -> list[tuple[str, float]]:
    """Speaker shares (id, seconds) inside [a, b] from diarization, largest first."""
    share: dict[str, float] = {}
    for t0, t1, spk in diar_turns(meeting):
        ov = min(b, t1) - max(a, t0)
        if ov > 0:
            share[spk] = share.get(spk, 0) + ov / 1000
    return sorted(share.items(), key=lambda kv: -kv[1])


@lru_cache(maxsize=None)
def marks(meeting: str) -> list[dict]:
    out = []
    for m in json.loads((WORK / "parsed" / "marks.json").read_text()):
        if m["audio"] in MEETINGS[meeting]["sources"]:
            out.append({**m, "epoch": source_to_epoch_ms(m["audio"], m["pos_ms"])})
    return sorted(out, key=lambda m: m["epoch"])


def meeting_spans(meeting: str) -> list[tuple[float, float]]:
    """Union of the wall-clock spans of all recordings of the meeting."""
    spans = sorted(s for src in MEETINGS[meeting]["sources"] for s in source_span_epoch_ms(src))
    out = []
    for a, b in spans:
        if out and a <= out[-1][1] + 2000:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def recordings_at(meeting: str, t: float) -> list[str]:
    return [src for src in MEETINGS[meeting]["sources"] if any(a <= t <= b for a, b in source_span_epoch_ms(src))]


def kind_of(src: str) -> str:
    return SOURCES[src]["kind"]
