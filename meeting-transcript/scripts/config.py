"""Shared paths and the recording map for one set of meeting transcripts.

Every pipeline script imports this module. Nothing about a specific meeting lives in code: it all comes
from a JSON file (see meeting.example.json). Library module, nothing to run.
Usage: MEETING_AUDIO=<audio folder> MEETING_OUT=<project folder> python -c "import config; print(config.SOURCES)"

Environment
  MEETING_OUT     project folder holding meeting.json, sources/, transcript/, notes/ (default: cwd)
  MEETING_CONFIG  path of meeting.json (default: $MEETING_OUT/meeting.json)
  MEETING_AUDIO   folder with the original audio + manifest.json (required)
  MEETING_WORK    scratch folder for decoded audio, ASR output, embeddings (default ~/work/tools/meetings-work)
  MEETING_MODELS  folder with the converted Whisper models (default ~/work/tools/models)

meeting.json keys
  title      text used in generated pages
  timezone   IANA name or "+HH:MM"; the zone times are shown in (default UTC)
  sources    {src: {"kind": "wispr|plaud|quicktime", "id": text, "files": [path under MEETING_AUDIO]}}
  meetings   {meeting: {"date", "title", "slug", "sources": [src], "topic"}}  one wall-clock timeline each
  parts      [[meeting, cut "HH:MM:SS" or null, folder, slug, title]]  transcript files to write; a part runs
             from its cut to the next cut of the same meeting
  topics     {folder: label}
  speaker_names  optional names offered on the doubt pages
  aliases / corrections  optional post-merge fixes used by assemble.py
  align      {"pairs": [[target, wispr reference]], "borrow_offset": {target: donor},
              "gap_fix": {"src", "break_s": [a, b], "audio_end_s", "via", "next"}}      (align.py)
  asr        {"best": [[meeting, src, start_s, end_s|null]], "alt": [...]}                (run_asr.py)
  diarize    {"embed": [src], "recs": {key: [src, from_s|null, to_s|null, merge_sim|null]},
              "simultaneous": [[key, key]], "main": {meeting: [[key, from_s, to_s]]}}     (diarize_*.py)
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_tz(spec: str):
    """IANA name ("Region/City") or fixed offset ("+07:00")."""
    m = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", spec)
    if m:
        delta = timedelta(hours=int(m[2]), minutes=int(m[3]))
        return timezone(delta if m[1] == "+" else -delta)
    if spec in ("UTC", "Z"):
        return timezone.utc
    from zoneinfo import ZoneInfo
    return ZoneInfo(spec)


OUT = Path(os.environ.get("MEETING_OUT", Path.cwd())).resolve()
CONFIG_PATH = Path(os.environ.get("MEETING_CONFIG", OUT / "meeting.json"))
if not CONFIG_PATH.exists():
    sys.exit(f"meeting config not found: {CONFIG_PATH} (set MEETING_CONFIG or MEETING_OUT; see meeting.example.json)")
if "MEETING_AUDIO" not in os.environ:
    sys.exit("set MEETING_AUDIO to the folder with the original audio and manifest.json")
CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

TZ = parse_tz(CFG.get("timezone", "UTC"))
TITLE = CFG.get("title", "")
SRC = OUT / "sources"
AUDIO = Path(os.environ["MEETING_AUDIO"])
WORK = Path(os.environ.get("MEETING_WORK", Path.home() / "work/tools/meetings-work"))
MODELS = Path(os.environ.get("MEETING_MODELS", Path.home() / "work/tools/models"))
SPEAKERS_DIR = AUDIO / "speakers"

# Source id -> kind (plaud | wispr | quicktime), id of the original recording, audio file(s) relative to AUDIO.
SOURCES = CFG["sources"]
# Meetings = one wall-clock timeline each. Sources listed in the order they were checked.
MEETINGS = CFG["meetings"]
# Parts written to transcript/<folder>/<date>_<HHMM>_<slug>.{json,md}. A part starts at the first
# segment at or after `cut` (None = meeting start) and ends where the next part of the meeting starts.
PARTS = [tuple(p) for p in CFG["parts"]]
TOPIC_TH = CFG["topics"]
SPEAKER_NAMES = CFG.get("speaker_names", [])
ALIASES = CFG.get("aliases", {})
CORRECTIONS = CFG.get("corrections", [])


def manifest() -> dict:
    return json.loads((AUDIO / "manifest.json").read_text())


def manifest_by_file() -> dict:
    return {f["file"].split("/", 1)[1]: f for f in manifest()["files"]}


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def nominal_start_epoch_ms(src: str) -> int:
    """Start of the source audio per manifest (device clock), epoch ms."""
    mf = manifest_by_file()[SOURCES[src]["files"][0]]
    return round(parse_iso(mf["start_utc"]).timestamp() * 1000)


def source_duration_s(src: str) -> float:
    mbf = manifest_by_file()
    return sum(mbf[f]["duration_s"] for f in SOURCES[src]["files"])


_OFFS: dict | None = None


def offsets() -> dict:
    """Measured clock maps from align.py: {src: {"pieces": [[pos_a, pos_b, epoch_a, epoch_b], ...]}}."""
    global _OFFS
    if _OFFS is None:
        _OFFS = json.loads((WORK / "offsets.json").read_text())
    return _OFFS


def source_to_epoch_ms(src: str, pos_ms: float) -> float:
    """Position inside a source's audio (ms) -> corrected wall-clock epoch ms (piecewise linear)."""
    pcs = offsets()[src]["pieces"]
    for a, b, ea, eb in pcs:
        if a <= pos_ms <= b:
            return ea + (pos_ms - a) * ((eb - ea) / (b - a) if b > a else 1.0)
    a, b, ea, eb = pcs[0] if pos_ms < pcs[0][0] else pcs[-1]
    return ea + pos_ms - a if pos_ms < a else eb + pos_ms - b


def epoch_to_source_ms(src: str, epoch_ms: float) -> float | None:
    """Inverse map; None when the source was not recording at that moment (pause or outside)."""
    for a, b, ea, eb in offsets()[src]["pieces"]:
        if ea <= epoch_ms <= eb and eb > ea:
            return a + (epoch_ms - ea) * (b - a) / (eb - ea)
    return None


def source_span_epoch_ms(src: str) -> list[tuple[float, float]]:
    """Wall-clock spans (epoch ms) during which the source was recording (pauses excluded)."""
    spans = []
    for a, b, ea, eb in offsets()[src]["pieces"]:
        if spans and abs(spans[-1][1] - ea) < 1500:
            spans[-1] = (spans[-1][0], eb)
        else:
            spans.append((ea, eb))
    return spans


def local_str(epoch_ms: float, with_ms: bool = False) -> str:
    dt = datetime.fromtimestamp(epoch_ms / 1000, TZ)
    return dt.isoformat(timespec="milliseconds" if with_ms else "seconds")


def hms(epoch_ms: float) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, TZ).strftime("%H:%M:%S")


def wav_path(src: str) -> Path:
    return WORK / "wav" / f"{src}.wav"
