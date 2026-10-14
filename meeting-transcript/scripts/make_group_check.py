"""Spot-check the speaker moves proposed by relabel_by_anchors.py: three short clips per group of moves.

Usage: python make_group_check.py result.json part OUT_DIR

result.json is the output of relabel_by_anchors.py for transcript part `part` (as listed in
transcript/index.json, or a path to its .json). Moves are grouped by (old id, new id); only sure moves
and groups of at least 5 segments are checked, with 3 sampled segments each. The owner picks who speaks
in each clip; names come from meeting.json "speaker_names" (else the ids found in result.json).
Filler clips (< 12 characters left after Thai fillers, or < 3 s) are skipped. Needs ffmpeg and the
original audio (config AUDIO). Writes OUT_DIR/index.html + g01.m4a ...
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from clips import audio_for, card, cut_clip, hms_of, is_filler, load_part, page, radios, seg_dur_s
from config import SPEAKER_NAMES

MIN_GROUP = 5
SAMPLES = (0, 2, 3)  # quartile positions inside a group (first, middle, upper)
PAD_S, MAX_CLIP_S = 1.0, 20.0
OTHER = "คนอื่น"


def groups_of(res: dict, segs: list[dict]) -> dict:
    groups: dict[tuple, list[int]] = {}
    for i, v in res.items():
        s = segs[int(i)]
        if v["sure"] and not is_filler(s["text"], seg_dur_s(s)):
            groups.setdefault((v["old"], v["new"]), []).append(int(i))
    return {k: sorted(v) for k, v in sorted(groups.items()) if len(v) >= MIN_GROUP}


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["segments"]
    segs, meta = load_part(sys.argv[2])
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    groups = groups_of(result, segs)
    names = (SPEAKER_NAMES or sorted({x for v in result.values() for x in (v["old"], v["new"])})) + [OTHER]
    cards = []
    for (old, new), ix in groups.items():
        for i in [ix[len(ix) * k // 4] for k in SAMPLES]:
            n = len(cards) + 1
            s = segs[i]
            src, pos = audio_for(s, meta)
            cut_clip(src, pos - PAD_S, min(seg_dur_s(s) + 2 * PAD_S, MAX_CLIP_S), out / f"g{n:02d}.m4a")
            field = (f'<div class="opts" data-q="g{n}" data-t="{hms_of(s)}" data-was="{html.escape(old)}>{html.escape(new)}">'
                     f'{radios(f"g{n}", names)}<input class="note" placeholder="หมายเหตุ"></div>')
            cards.append(card(n, f"[{hms_of(s)}] ใครพูด?", f"g{n:02d}.m4a", [f'<li class="hot">{html.escape(s["text"])}</li>'], field))
    intro = "เลือกว่าใครพูด (คลิปสั้นประโยคเดียว) ข้อที่ไม่แน่ใจข้ามได้ เสร็จแล้วกดปุ่มล่างสุดแล้ววางให้ผม"
    (out / "index.html").write_text(page("ตรวจกลุ่มเสียง", intro, cards), encoding="utf-8")
    print(len(cards), "clips", {f"{o}>{w}": len(v) for (o, w), v in groups.items()})


if __name__ == "__main__":
    main()
