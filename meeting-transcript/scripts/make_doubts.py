"""Cut a short clip for every doubtful line and build one local review page for the owner.

Usage: python make_doubts.py questions.json OUT_DIR

questions.json:
  {"names": ["Alice", "Bob"],                       # optional; default meeting.json "speaker_names"
   "speaker": [{"part": "folder/name", "time": "HH:MM:SS", "why": "label looks wrong because ..."}],
   "number":  [{"part": "folder/name", "from": "HH:MM:SS", "to": "HH:MM:SS", "what": "price of ..."}],
   "number_pattern": "regex"}                       # optional; default: Thai money words and 000-numbers
`part` is a transcript part as listed in transcript/index.json (or a path to its .json). Speaker questions
play the sentence at `time` with its neighbours; number questions play the first segments with an amount
between `from` and `to`. Audio comes from the original files (config SOURCES, segment audio_pos_s, else
start_ms from the part's origin). Filler clips (< 12 characters left after Thai fillers, or < 3 s) are skipped.
Writes OUT_DIR/index.html + q01.m4a ... (open it locally; the page copies the answers as JSON).
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from clips import audio_for, card, cut_clip, hms_of, is_filler, line, load_part, page, radios, seg_dur_s
from config import SPEAKER_NAMES

MONEY = r"บาท|หมื่น|แสน|ล้าน|\d[\d,]*000"
PAD_S, MAX_CLIP_S = 4.0, 75.0
OTHER = "คนอื่น"


def pick(segs: list[dict], t: str) -> int:
    """Index of the last segment starting at or before HH:MM:SS."""
    return max((k for k, s in enumerate(segs) if hms_of(s) <= t), default=0)


def clip_for(segs, meta, first: int, last: int, dst: Path):
    """Cut the audio from segment `first` to `last` (+- padding)."""
    a = segs[first]["start_ms"] / 1000 - PAD_S
    b = segs[last]["end_ms"] / 1000 + PAD_S
    src, pos = audio_for(segs[first], meta)
    cut_clip(src, pos - PAD_S, min(b - a, MAX_CLIP_S), dst)


def speaker_card(n: int, q: dict, names: list[str], out: Path):
    segs, meta = load_part(q["part"])
    i = pick(segs, q["time"])
    if is_filler(segs[i]["text"], seg_dur_s(segs[i])):
        print(f"skip speaker question at {q['time']}: filler clip")
        return None
    clip_for(segs, meta, max(i - 1, 0), min(i + 1, len(segs) - 1), out / f"q{n:02d}.m4a")
    ctx = [line(segs[k], k == i) for k in range(max(i - 2, 0), min(i + 3, len(segs)))]
    field = (f'<div class="opts" data-q="q{n}" data-t="{q["time"]}" data-was="{html.escape(segs[i]["speaker"])}">'
             f'{radios(f"q{n}", names)}<input class="note" placeholder="ชื่อคนอื่น / หมายเหตุ"></div>')
    return card(n, f"{q['time']} คนพูดประโยคสีเหลืองคือใคร? ({q['why']})", f"q{n:02d}.m4a", ctx, field)


def number_card(n: int, q: dict, pattern: re.Pattern, out: Path):
    segs, meta = load_part(q["part"])
    hits = [k for k, s in enumerate(segs) if q["from"] <= hms_of(s) <= q["to"] and pattern.search(s["text"])]
    i = hits[0] if hits else pick(segs, q["from"])
    j = min((hits[-1] if hits else i) + 1, len(segs) - 1)
    if segs[j]["start_ms"] - segs[i]["start_ms"] > 60000:
        j = i + 1
    text = " ".join(s["text"] for s in segs[i:j + 1])
    if is_filler(text, (segs[j]["end_ms"] - segs[i]["start_ms"]) / 1000):
        print(f"skip number question {q['what']!r}: filler clip")
        return None
    clip_for(segs, meta, i, j, out / f"q{n:02d}.m4a")
    ctx = [line(segs[k], k in hits) for k in range(max(i - 1, 0), min(j + 2, len(segs)))]
    field = (f'<div class="opts" data-q="q{n}" data-t="{hms_of(segs[i])}" data-was="number">'
             '<input class="note wide" placeholder="ตัวเลขที่ได้ยิน"></div>')
    return card(n, f"{hms_of(segs[i])} {q['what']}: ได้ยินตัวเลขเท่าไร?", f"q{n:02d}.m4a", ctx, field)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    qs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    names = list(qs.get("names") or SPEAKER_NAMES) + [OTHER]
    pattern = re.compile(qs.get("number_pattern") or MONEY)
    cards = []
    for q in qs.get("speaker", []):
        c = speaker_card(len(cards) + 1, q, names, out)
        cards += [c] if c else []
    for q in qs.get("number", []):
        c = number_card(len(cards) + 1, q, pattern, out)
        cards += [c] if c else []
    intro = ("กดฟัง แล้วเลือกว่าใครพูดประโยค<b>สีเหลือง</b> หรือพิมพ์ตัวเลขที่ได้ยิน ข้อที่ไม่แน่ใจข้ามได้ "
             "เสร็จแล้วกดปุ่มล่างสุดแล้ววางให้ผม")
    (out / "index.html").write_text(page("ฟังจุดที่สงสัย", intro, cards), encoding="utf-8")
    print(len(cards), "questions ->", out / "index.html")


if __name__ == "__main__":
    main()
