"""List the stretches the owner should check by ear: notes/weak-spots.md.

A weak stretch = consecutive speech segments (gap < 3 s) whose text contains `[?]` or `[ไม่ได้ยิน]`,
longer than 10 s in total. Second list: low-confidence stretches longer than 30 s.
Reads transcript/*.json (+ index.json) and, if present, meeting.json (for audio file names), so it runs
anywhere with plain Python 3.8+. Run in $MEETING_OUT (or set MEETING_OUT).
Usage: python3 weak_spots.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

OUT = Path(os.environ.get("MEETING_OUT", Path.cwd())).resolve()


def audio_names() -> dict:
    """src -> audio file name(s) from meeting.json, so a reader knows which file to open."""
    path = Path(os.environ.get("MEETING_CONFIG", OUT / "meeting.json"))
    if not path.exists():
        return {}
    srcs = json.loads(path.read_text(encoding="utf-8")).get("sources", {})
    return {k: Path(v["files"][0]).name + (f" (+{len(v['files']) - 1} parts)" if len(v["files"]) > 1 else "")
            for k, v in srcs.items()}


AUDIO_NAMES = audio_names()


def mmss(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def stretches(segs, flagged, min_ms, gap_ms=3000):
    out, cur = [], []
    for s in segs:
        if s.get("kind", "speech") != "speech":
            continue
        if flagged(s):
            if cur and s["start_ms"] - cur[-1]["end_ms"] > gap_ms:
                out.append(cur)
                cur = []
            cur.append(s)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [c for c in out if c[-1]["end_ms"] - c[0]["start_ms"] >= min_ms]


def block(part: str, run: list) -> list[str]:
    a, b = run[0], run[-1]
    dur = (b["end_ms"] - a["start_ms"]) / 1000
    who = ", ".join(sorted({s["speaker"] for s in run}))
    pos = ", ".join(f"{AUDIO_NAMES.get(k, k)} @ {mmss(v)}" for k, v in a.get("audio_pos_s", {}).items())
    text = " / ".join(s["text"] for s in run)
    if len(text) > 400:
        text = text[:400] + " …"
    return [f"### {a['start_local'][11:19]}–{b['end_local'][11:19]} ({dur:.0f} วิ) · `{part}`",
            f"- ผู้พูด: {who} · ความเชื่อมั่น: {', '.join(sorted({s['confidence'] for s in run}))}",
            f"- ฟังที่: {pos or '—'}", f"- ข้อความ: {text}", ""]


def main():
    index = json.loads((OUT / "transcript" / "index.json").read_text(encoding="utf-8"))
    unsure = lambda s: "[?]" in s["text"] or "[ไม่ได้ยิน" in s["text"]  # noqa: E731
    low = lambda s: s["confidence"] == "low"  # noqa: E731
    sec1, sec2, n1, n2 = [], [], 0, 0
    for part in index:
        segs = json.loads((OUT / "transcript" / f"{part['file']}.json").read_text(encoding="utf-8"))
        for run in stretches(segs, unsure, 10_000):
            sec1 += block(part["file"], run)
            n1 += 1
        for run in stretches(segs, low, 30_000):
            sec2 += block(part["file"], run)
            n2 += 1
    lines = ["# จุดที่ควรฟังซ้ำ (weak spots)", "",
             "สร้างอัตโนมัติด้วย `weak_spots.py` จาก transcript JSON (อย่าแก้มือ — แก้ transcript แล้วรันใหม่)", "",
             f"- ส่วนที่ 1: ช่วงที่มี `[?]` หรือ `[ไม่ได้ยิน]` ต่อเนื่องเกิน 10 วินาที — {n1} ช่วง",
             f"- ส่วนที่ 2: ช่วงความเชื่อมั่น low ต่อเนื่องเกิน 30 วินาที — {n2} ช่วง",
             "- \"ฟังที่\" = ตำแหน่งในไฟล์เสียงต้นฉบับ (ชั่วโมง:นาที:วินาที นับจากต้นไฟล์) ใน $MEETING_AUDIO",
             "", "## ส่วนที่ 1: `[?]` / `[ไม่ได้ยิน]` เกิน 10 วินาที", ""]
    lines += sec1 or ["ไม่มี", ""]
    lines += ["## ส่วนที่ 2: ความเชื่อมั่น low เกิน 30 วินาที", ""]
    lines += sec2 or ["ไม่มี", ""]
    (OUT / "notes").mkdir(exist_ok=True)
    (OUT / "notes" / "weak-spots.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"weak-spots.md: {n1} unsure stretches > 10 s, {n2} low-confidence stretches > 30 s")


if __name__ == "__main__":
    main()
