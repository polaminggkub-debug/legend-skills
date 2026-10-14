"""Copy staged audio into the audio repo layout and write manifest.json (no transcript text is printed).

Usage: python build_audio_repo.py STAGING REPO NAME [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--tz ZONE]
           [--backup-start ISO_UTC] [--backup-original TEXT] [--skipped skipped.json]

STAGING layout (made by plaud-dump.mjs, gather_wispr.py and by hand):
  plaud/of_*/get_file.json + audio.<ext>      one folder per Plaud file (get_file has "start_at", UTC)
  wispr/meetings-table.json + wispr/<id>/upload.ogg   (gather_wispr.py output)
  quicktime/*.part*.m4a                      optional backup recording, parts in name order
Result: REPO/NAME/{plaud,wispr,quicktime}/... and REPO/NAME/manifest.json (sha256, duration, start in UTC and
in ZONE). --from/--to (local dates, inclusive) keep only Plaud files and Wispr meetings starting inside the
range. The backup recording starts at --backup-start (UTC; its parts follow each other). --skipped is a
JSON list of {"path", "reason"} for files left out on purpose. ZONE is an IANA name (default UTC).
Needs ffprobe.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def payload(path):
    text = json.loads(path.read_text())["result"]["content"][0]["text"]
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc(text):
    """ISO / Wispr-style ("2000-01-01 10:00:00.000 +00:00") timestamp -> aware UTC datetime."""
    dt = datetime.fromisoformat(text.replace(" +", "+").replace(" -", "-").replace("Z", "+00:00"))
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("staging", type=Path)
    ap.add_argument("repo", type=Path)
    ap.add_argument("name")
    ap.add_argument("--from", dest="first")
    ap.add_argument("--to", dest="last")
    ap.add_argument("--tz", default="UTC")
    ap.add_argument("--backup-start")
    ap.add_argument("--backup-original", default="backup recording")
    ap.add_argument("--skipped", type=Path)
    args = ap.parse_args()
    staging, repo, out = args.staging, args.repo, args.repo / args.name
    tz = ZoneInfo(args.tz) if args.tz != "UTC" else timezone.utc

    def in_range(start):
        day = start.astimezone(tz).date().isoformat()
        return (not args.first or day >= args.first) and (not args.last or day <= args.last)

    def entry(src, dest, source, original, start_utc, extra):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return {"file": str(dest.relative_to(repo)), "source": source, "original_path": original,
                "sha256": sha(dest), "bytes": dest.stat().st_size, "duration_s": probe(dest),
                "start_utc": start_utc.isoformat().replace("+00:00", "Z"),
                "start_local": start_utc.astimezone(tz).isoformat(), **extra}

    items = []
    for d in sorted((staging / "plaud").glob("of_*")):
        f = payload(d / "get_file.json")
        start = utc(f["start_at"])
        if not in_range(start):
            continue
        audio = next(d.glob("audio.*"))
        tx = d / "transcript.transaction.p0.json"
        items.append(entry(audio, out / "plaud" / f"{d.name}{audio.suffix}", "plaud", f"Plaud cloud file {d.name}",
                           start, {"plaud_file_id": d.name, "name": f.get("name") or f.get("filename"),
                                   "has_plaud_transcript": tx.exists() and '"total": 0' not in tx.read_text()}))

    skipped = json.loads(args.skipped.read_text()) if args.skipped else []
    table = staging / "wispr" / "meetings-table.json"
    rows = {r["id"]: r for r in json.loads(table.read_text())} if table.exists() else {}
    for d in sorted(p for p in (staging / "wispr").glob("*") if p.is_dir()):
        row = rows.get(d.name, {})
        start = utc(row["createdAt"]) if "createdAt" in row else None
        if start is None or not in_range(start):
            continue
        if not (d / "upload.ogg").exists():
            skipped.append({"path": f"wispr meeting {d.name}", "reason": "no audio on disk"})
            continue
        items.append(entry(d / "upload.ogg", out / "wispr" / f"{d.name}.ogg", "wispr-flow",
                           f"Wispr Flow meetings/{d.name}/upload.ogg", start,
                           {"wispr_meeting_id": d.name, "name": row.get("title"), "recorded_ms": row.get("recordedMs"),
                            "note": "createdAt is when the meeting was created; audio may start slightly later"}))

    parts = sorted((staging / "quicktime").glob("*.part*.m4a"))
    if parts and not args.backup_start:
        raise SystemExit("quicktime parts found: give --backup-start (UTC ISO time of the recording start)")
    offset = 0.0
    for p in parts:
        e = entry(p, out / "quicktime" / p.name, "quicktime-screen-recording", args.backup_original,
                  utc(args.backup_start) + timedelta(seconds=offset), {"part_offset_s": offset, "name": "backup recording"})
        offset += e["duration_s"]
        items.append(e)

    manifest = {"created": datetime.now(tz).isoformat(),
                "timezone_note": f"start_utc is UTC; start_local is {args.tz}",
                "skipped": skipped, "files": items}
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    for i in items:
        print(i["file"], i["bytes"], round(i["duration_s"]), i["start_local"])


if __name__ == "__main__":
    main()
