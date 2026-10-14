"""Mac only: copy the Wispr Flow meeting folders that started in a local date range, and export their database rows.

Usage: python gather_wispr.py DEST --from YYYY-MM-DD --to YYYY-MM-DD [--tz ZONE] [--wispr-dir DIR] [--list]

Reads <wispr-dir>/flow.sqlite with `sqlite3 -readonly` (the Wispr store is never written) and copies, for every
meeting whose start falls in the range (local dates, inclusive; ZONE = IANA name, default the Mac's zone):
  DEST/<meeting id>/{upload.ogg, live.ndjson, refined.ndjson, *.json}   from <wispr-dir>/meetings/<id>/
  DEST/meetings-table.json   the matching rows of table Meetings (all columns; input of build_audio_repo.py)
  DEST/notes-table.json      the matching rows of table Notes (if the table exists)
The schema is read at run time (`.schema Meetings`); the start column is the first of startedAt, startAt,
startTime, createdAt, created_at that exists. If sqlite3 or the schema fails, folder file times (mtime of
live.ndjson or upload.ogg, i.e. the END of the recording) are used and no table rows are exported.
--list only prints what would be copied. Times in the database are UTC.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_DIR = Path.home() / "Library/Application Support/Wispr Flow"
START_COLUMNS = ["startedAt", "startAt", "startTime", "createdAt", "created_at"]
COPY_NAMES = ["upload.ogg", "live.ndjson", "refined.ndjson", "*.json"]


def sqlite(db: Path, sql: str, *options: str) -> str:
    """Run one statement or dot-command against the Wispr database, read-only."""
    r = subprocess.run(["sqlite3", "-readonly", *options, str(db), sql], capture_output=True, text=True, check=True)
    return r.stdout


def columns(db: Path, table: str) -> list[str]:
    """Column names of `table` from its `.schema`; [] if the table does not exist."""
    ddl = sqlite(db, ".schema " + table)
    m = re.search(r"CREATE TABLE\s+[`\"\[]?" + table + r"[`\"\]]?\s*\((.*?)\);", ddl, re.S | re.I)
    return re.findall(r"[`\"\[](\w+)[`\"\]]\s+[A-Za-z]", m.group(1)) if m else []


def rows(db: Path, table: str) -> list[dict]:
    out = sqlite(db, f"SELECT * FROM {table}", "-json")
    return json.loads(out) if out.strip() else []


def parse_utc(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace(" +", "+").replace(" -", "-").replace("Z", "+00:00"))
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def pick_start_column(cols: list[str]) -> str | None:
    return next((c for c in START_COLUMNS if c in cols), None)


def mtime_start(folder: Path) -> datetime | None:
    for name in ("live.ndjson", "upload.ogg"):
        if (folder / name).exists():
            return datetime.fromtimestamp((folder / name).stat().st_mtime, timezone.utc)
    return None


def copy_folder(src: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    for pattern in COPY_NAMES:
        for f in src.glob(pattern):
            if f.is_file():
                shutil.copy2(f, dest / f.name)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest", type=Path)
    ap.add_argument("--from", dest="first", required=True)
    ap.add_argument("--to", dest="last", required=True)
    ap.add_argument("--tz")
    ap.add_argument("--wispr-dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    tz = ZoneInfo(args.tz) if args.tz else datetime.now().astimezone().tzinfo

    def in_range(start: datetime) -> bool:
        return args.first <= start.astimezone(tz).date().isoformat() <= args.last

    db, meetings = args.wispr_dir / "flow.sqlite", args.wispr_dir / "meetings"
    picked: dict[str, datetime] = {}
    table_rows: list[dict] = []
    notes_rows: list[dict] = []
    try:
        cols = columns(db, "Meetings")
        col = pick_start_column(cols)
        if not col or "id" not in cols:
            raise ValueError(f"Meetings has no usable id/start column: {cols}")
        print(f"Meetings columns: {len(cols)}; start column: {col}")
        for r in rows(db, "Meetings"):
            if r.get(col) and in_range(parse_utc(r[col])):
                table_rows.append(r)
                picked[r["id"]] = parse_utc(r[col])
        ncols = columns(db, "Notes")
        ncol = pick_start_column(ncols)
        if ncol:
            notes_rows = [r for r in rows(db, "Notes") if r.get(ncol) and in_range(parse_utc(r[ncol]))]
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"sqlite failed ({e}); falling back to folder file times (end of recording)", file=sys.stderr)
        table_rows, notes_rows = [], []
        for d in sorted(p for p in meetings.glob("*") if p.is_dir()):
            t = mtime_start(d)
            if t and in_range(t):
                picked[d.name] = t

    for mid, start in sorted(picked.items(), key=lambda kv: kv[1]):
        folder = meetings / mid
        state = "folder" if folder.is_dir() else "NO FOLDER (deleted?)"
        print(f"{mid}  {start.astimezone(tz).isoformat(timespec='seconds')}  {state}")
        if not args.list and folder.is_dir():
            copy_folder(folder, args.dest / mid)
    print(f"{len(picked)} meetings, {len(notes_rows)} notes in range")
    if not args.list:
        args.dest.mkdir(parents=True, exist_ok=True)
        if table_rows:
            (args.dest / "meetings-table.json").write_text(json.dumps(table_rows, ensure_ascii=False, indent=1))
        if notes_rows:
            (args.dest / "notes-table.json").write_text(json.dumps(notes_rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
