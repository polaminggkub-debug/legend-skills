"""Put real speaker names into every transcript part in one command.

    python3 apply_speaker_names.py names.json      # {"S1": "real name", "S2": "...", ...}
    python3 apply_speaker_names.py --reset         # back to S1..Sn
Usage: python3 apply_speaker_names.py names.json|--reset   (run in $MEETING_OUT, or set MEETING_OUT)

names.json is what the labelling page ($MEETING_AUDIO/speakers/index.html) copies.
Each segment keeps `speaker_id` (S1..Sn, never changed); `speaker` becomes "name (S3)" or, with
--reset, "S3" again. A segment with "speaker_unsure": true gets " ?" after its label. The Markdown
files and notes/weak-spots.md are re-rendered from the JSON.
Plain Python 3.8+, no extra packages (does not read meeting.json).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

OUT = Path(os.environ.get("MEETING_OUT", Path.cwd())).resolve()
sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import render  # noqa: E402


def load_names(arg: str) -> dict:
    if arg == "--reset":
        return {}
    raw = json.loads(Path(arg).read_text(encoding="utf-8"))
    names = raw.get("names", raw) if isinstance(raw, dict) else {}
    bad = [k for k in names if not (k.startswith("S") and k[1:].isdigit())]
    if bad:
        sys.exit(f"names.json keys must look like S1, S2 …; got {bad}")
    return {k: str(v).strip() for k, v in names.items() if str(v).strip()}


def label(sid, names: dict):
    if sid is None:
        return None
    return f"{names[sid]} ({sid})" if sid in names else sid


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    names = load_names(sys.argv[1])
    index = json.loads((OUT / "transcript" / "index.json").read_text(encoding="utf-8"))
    changed = 0
    for part in index:
        path = OUT / "transcript" / f"{part['file']}.json"
        segs = json.loads(path.read_text(encoding="utf-8"))
        for s in segs:
            if s.get("speaker_id"):
                s["speaker"] = label(s["speaker_id"], names) + (" ?" if s.get("speaker_unsure") else "")
        path.write_text(json.dumps(segs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        path.with_suffix(".md").write_text(render(part, segs), encoding="utf-8")
        changed += 1
    weak = Path(__file__).resolve().with_name("weak_spots.py")
    if weak.exists():
        import runpy
        runpy.run_path(str(weak), run_name="__main__")
    print(f"{changed} parts rewritten with {len(names)} names" if names else f"{changed} parts reset to S1..Sn")


if __name__ == "__main__":
    main()
