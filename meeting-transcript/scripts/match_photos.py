"""Copy meeting photos into the transcript folder and pair each with its Plaud photo mark by time.

Usage: python match_photos.py OUT_DIR --photos FILE... --plaud ID=START_ISO [--plaud ...] [--sources DIR]
                              [--max-gap 120]

Plaud's MCP gives each photo mark's time, AI caption and OCR link, but not the image. The owner saves
the photos from the Plaud app (e.g. into ~/Downloads); this pairs them by capture time (macOS
kMDItemContentCreationDate, else file mtime) with the nearest mark within --max-gap seconds.
--plaud ID=START_ISO: a recording id and its start (ISO with offset), whose marks are read from
SOURCES/<ID>/transcript.mark_memo.p0.json (plaud-dump.mjs output; default --sources sources/plaud).
Writes OUT_DIR/photos/<date>_<HHMMSS>.<ext>, photos/index.json and photos/README.md. Originals are only read.
"""
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def marks(sources: Path, rec: str):
    fid, start = rec.split("=", 1)
    d = json.loads((sources / fid / "transcript.mark_memo.p0.json").read_text(encoding="utf-8"))
    text = d["result"]["content"][0]["text"] if "result" in d else json.dumps(d)
    body = json.loads(text[text.index("{"):text.rindex("}") + 1])
    t0 = datetime.fromisoformat(start)
    return [(t0 + timedelta(milliseconds=int(m["timestamp"])), fid, m.get("mark_content") or "")
            for m in body.get("marks", []) if str(m.get("mark_type")) == "2"]  # 2 = photo


def taken(path: str, tz):
    out = subprocess.run(["mdls", "-raw", "-name", "kMDItemContentCreationDate", path],
                         capture_output=True, text=True).stdout.strip() if shutil.which("mdls") else ""
    if out and out != "(null)":
        return datetime.strptime(out, "%Y-%m-%d %H:%M:%S %z").astimezone(tz)
    return datetime.fromtimestamp(os.path.getmtime(path), tz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--photos", nargs="+", required=True)
    ap.add_argument("--plaud", action="append", default=[])
    ap.add_argument("--sources", type=Path, default=Path("sources/plaud"))
    ap.add_argument("--max-gap", type=float, default=120)
    a = ap.parse_args()
    ms = sorted(m for rec in a.plaud for m in marks(a.sources, rec))
    tz = ms[0][0].tzinfo if ms else datetime.now().astimezone().tzinfo
    dest = a.out / "photos"
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for dt, f in sorted((taken(p, tz), p) for p in a.photos):
        best = min(ms, key=lambda m: abs((m[0] - dt).total_seconds()), default=None)
        ok = best is not None and abs((best[0] - dt).total_seconds()) <= a.max_gap
        name = f"{dt:%Y-%m-%d_%H%M%S}{Path(f).suffix.lower()}"
        shutil.copy2(f, dest / name)
        rows.append({"file": name, "taken_local": dt.isoformat(), "plaud_file": best[1] if ok else None,
                     "plaud_mark_time": best[0].isoformat() if ok else None, "plaud_caption": best[2] if ok else None})
        print(name, "matched" if ok else "no mark")
    (dest / "index.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# Photos", "", "Captions are Plaud's AI text, unchecked.", "", "| Time | Photo | Plaud caption |", "|---|---|---|"]
    md += [f'| {r["taken_local"][11:19]} | [{r["file"]}]({r["file"]}) | '
           f'{(r["plaud_caption"] or "—").replace("|", "/").replace(chr(10), " ")} |' for r in rows]
    (dest / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")


main()
