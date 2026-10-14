"""Helpers shared by make_doubts.py and make_group_check.py: load a transcript part, cut a short clip from
the ORIGINAL audio (read only), skip filler clips and fill the review page template.

Where a segment's audio is: `audio_pos_s` ({src: seconds}, written by assemble.py) -> the clearest source
(Wispr, then Plaud, then the backup recording); without it, `start_ms` counted from the part's origin source.
Library module, nothing to run. Usage: from clips import load_part, audio_for, cut_clip, is_filler, page
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from config import AUDIO, MEETINGS, OUT, SOURCES, epoch_to_source_ms, manifest_by_file

# A clip is skipped when it is only back-channel noise: < 12 characters left after removing these Thai
# fillers, or shorter than 3 s (nothing to decide by ear in it).
FILLER = re.compile(r"อ๋อ|อืม|ครับ|ค่ะ|อ่า|เออ|ฮะ|โอเค|ใช่|[\s,.?!ๆ]")
MIN_CHARS, MIN_CLIP_S = 12, 3.0
PREFER = ["wispr", "plaud", "quicktime"]
TEMPLATE = Path(__file__).with_name("doubts_tpl.html")


def load_part(part: str) -> tuple[list[dict], dict | None]:
    """Segments of a transcript part ("folder/name" as in transcript/index.json, or a path to the .json)
    and its index entry (None if the part is not in the index)."""
    path = Path(part)
    path = path.resolve() if path.suffix == ".json" and path.exists() else OUT / "transcript" / f"{part}.json"
    segs = json.loads(path.read_text(encoding="utf-8"))
    index = OUT / "transcript" / "index.json"
    entries = json.loads(index.read_text(encoding="utf-8")) if index.exists() else []
    try:
        stem = path.relative_to(OUT / "transcript").with_suffix("").as_posix()
    except ValueError:
        stem = None
    return segs, next((e for e in entries if e["file"] == stem), None)


def hms_of(seg: dict) -> str:
    return seg["start_local"][11:19]


def is_filler(text: str, dur_s: float) -> bool:
    return len(FILLER.sub("", text)) < MIN_CHARS or dur_s < MIN_CLIP_S


def seg_dur_s(seg: dict) -> float:
    return (seg["end_ms"] - seg["start_ms"]) / 1000


def origin_source(meta: dict) -> tuple[str, float]:
    """The meeting source whose audio starts nearest the part's origin, and the position there (s).
    Without measured offsets (WORK/offsets.json): the meeting's first source, position 0."""
    srcs = MEETINGS[meta["meeting"]]["sources"]
    try:
        origin = datetime.fromisoformat(meta["origin_local"]).timestamp() * 1000
        first = min(srcs, key=lambda s: abs(epoch_to_source_ms(s, origin + 1) or 1e12))
        return first, (epoch_to_source_ms(first, origin + 1) or 0.0) / 1000
    except (FileNotFoundError, KeyError):
        return srcs[0], 0.0


def audio_for(seg: dict, meta: dict | None) -> tuple[str, float]:
    """(source id, position in that source's audio in seconds) of a segment's start."""
    pos = seg.get("audio_pos_s") or {}
    if pos:
        src = min(pos, key=lambda s: PREFER.index(SOURCES[s]["kind"]))
        return src, pos[src]
    if meta is None:
        raise SystemExit(f"segment at {hms_of(seg)} has no audio_pos_s and its part is not in index.json")
    src, base = origin_source(meta)
    return src, base + seg["start_ms"] / 1000


def locate(src: str, pos_s: float) -> tuple[Path, float]:
    """Original file and offset inside it (a source may be several files, e.g. backup parts, in order)."""
    files = SOURCES[src]["files"]
    mbf = manifest_by_file()
    for i, f in enumerate(files):
        dur = mbf[f]["duration_s"] if f in mbf else float("inf")
        if pos_s < dur or i == len(files) - 1:
            return AUDIO / f, pos_s
        pos_s -= dur
    raise AssertionError("unreachable")


def cut_clip(src: str, start_s: float, dur_s: float, dst: Path):
    """Mono AAC clip of the original audio. Wispr files are stereo (mic, system audio): take the mic."""
    path, off = locate(src, max(start_s, 0.0))
    chan = ["-af", "pan=mono|c0=c0"] if SOURCES[src]["kind"] == "wispr" else ["-ac", "1"]
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{off:.2f}", "-t", f"{dur_s:.2f}",
                    "-i", str(path), *chan, "-c:a", "aac", "-b:a", "64k", str(dst)], check=True)


def line(seg: dict, hot: bool) -> str:
    style = ' class="hot"' if hot else ""
    return f'<li{style}><b>[{hms_of(seg)}] {html.escape(seg["speaker"])}:</b> {html.escape(seg["text"])}</li>'


def radios(qid: str, names: list[str]) -> str:
    return "".join(f'<label><input type="radio" name="{qid}" value="{html.escape(x)}"> {html.escape(x)}</label>' for x in names)


def card(n: int, title: str, clip: str, ctx: list[str], field: str) -> str:
    return (f'<section><h2>{n}. {html.escape(title)}</h2><audio controls preload="none" src="{clip}"></audio>'
            f'<ul>{"".join(ctx)}</ul>{field}</section>')


def page(heading: str, intro: str, cards: list[str]) -> str:
    return (TEMPLATE.read_text(encoding="utf-8").replace("{{HEADING}}", html.escape(heading))
            .replace("{{INTRO}}", intro).replace("{{CARDS}}", "\n".join(cards)))
