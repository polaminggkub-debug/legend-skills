"""Cut each meeting into ~10 min windows (the units auto_merge.py merges) and, with --md, write one
readable packet per window for checking by eye.

Windows are cut in the longest pause near every 10 minutes. Output: WORK/merge/windows.json.
A packet (WORK/merge/in/<meeting>-<NN>.md) lists, in 30 s slots, every hypothesis of that stretch on the
wall clock: DIAR (speaker turns, global ids), WL/WR (Wispr live/refined), PL (Plaud), TH (Whisper Thai),
V3 (Whisper large-v3), TA (Whisper Thai on the 2nd recording) and Plaud photo marks; 20 s of context
on each side.
Usage: python build_packets.py [--md] [meeting ...]
"""
from __future__ import annotations

import json
import sys

from config import MEETINGS, WORK, hms
from timeline import NAMES, asr_segments, diar_turns, marks, meeting_spans, service_segments

WINDOW_MS = 600_000
SLOT_MS = 30_000
CONTEXT_MS = 20_000


def all_segments(meeting: str) -> list[dict]:
    return sorted(service_segments(meeting) + asr_segments(meeting), key=lambda s: s["start"])


def cut_windows(meeting: str) -> list[tuple[float, float]]:
    """~10 min windows inside the recorded spans, each cut in the longest pause within +-90 s."""
    segs = all_segments(meeting)
    busy = sorted((s["start"], s["end"]) for s in segs if s["tag"] in ("WL", "PL", "TH"))
    out = []
    for a, b in meeting_spans(meeting):
        start = a
        while b - start > WINDOW_MS * 1.4:
            target = start + WINDOW_MS
            best, best_gap = target, -1.0
            prev_end = None
            for s0, s1 in busy:
                if prev_end is not None and target - 90_000 <= (prev_end + s0) / 2 <= target + 90_000:
                    gap = s0 - prev_end
                    if gap > best_gap:
                        best, best_gap = (prev_end + s0) / 2, gap
                prev_end = max(prev_end or s1, s1)
            out.append((start, best))
            start = best
        out.append((start, b))
    return out


def fmt(t: float) -> str:
    return hms(t) + f".{int(t % 1000) // 100}"


def seg_line(s: dict) -> str:
    label = f" [{s['label']}]" if s.get("label") else ""
    lp = f" (lp {s['logprob']:.2f})" if "logprob" in s else ""
    return f"{s['tag']} {fmt(s['start'])}–{fmt(s['end'])}{label}{lp} | {s['text']}"


def diar_line(meeting: str, a: float, b: float) -> str:
    parts = [f"{fmt(max(a, t0))}–{fmt(min(b, t1))} {spk}" for t0, t1, spk in diar_turns(meeting) if t1 > a and t0 < b]
    return "DIAR " + (" · ".join(parts) if parts else "(no speech detected)")


def packet(meeting: str, idx: int, a: float, b: float) -> str:
    segs = all_segments(meeting)
    inside = [s for s in segs if a <= s["start"] < b]
    tags = sorted({s["tag"] for s in inside})
    lines = [f"# Packet {meeting}-{idx:02d}: {MEETINGS[meeting]['date']} {hms(a)} → {hms(b)}",
             "", f"Window (segments that START inside it belong to it): {fmt(a)} → {fmt(b)}",
             "Sources here: " + ", ".join(f"{t} = {NAMES[t]}" for t in tags), ""]
    for m in marks(meeting):
        if a <= m["epoch"] < b:
            lines.append(f"PLAUD MARK at {fmt(m['epoch'])} (photo mark pressed on the recorder; Plaud AI caption: {m['caption']})")
    lines += ["", "## Context before the window (context only)"]
    lines += [seg_line(s) for s in segs if a - CONTEXT_MS <= s["start"] < a and s["tag"] in ("WL", "PL", "TH")]
    lines += ["", "## Window"]
    t = a
    while t < b:
        u = min(b, t + SLOT_MS)
        slot = [s for s in inside if t <= s["start"] < u]
        lines += ["", f"### {fmt(t)} – {fmt(u)}", diar_line(meeting, t, u)]
        lines += [seg_line(s) for s in sorted(slot, key=lambda s: (s["tag"], s["start"]))]
        t = u
    lines += ["", "## Context after the window (context only)"]
    lines += [seg_line(s) for s in segs if b <= s["start"] < b + CONTEXT_MS and s["tag"] in ("WL", "PL", "TH")]
    return "\n".join(lines) + "\n"


def main():
    args = sys.argv[1:]
    md = "--md" in args
    meetings = [a for a in args if a != "--md"] or list(MEETINGS)
    for d in ("in", "out"):
        (WORK / "merge" / d).mkdir(parents=True, exist_ok=True)
    wpath = WORK / "merge" / "windows.json"
    windows = json.loads(wpath.read_text()) if wpath.exists() else {}
    for meeting in meetings:
        wins = cut_windows(meeting)
        windows[meeting] = [[a, b] for a, b in wins]
        for i, (a, b) in enumerate(wins, 1):
            if md:
                (WORK / "merge" / "in" / f"{meeting}-{i:02d}.md").write_text(packet(meeting, i, a, b))
            print(f"{meeting}-{i:02d} {hms(a)}–{hms(b)}")
    wpath.write_text(json.dumps(windows, indent=1))


if __name__ == "__main__":
    main()
