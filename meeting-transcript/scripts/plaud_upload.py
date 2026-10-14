"""Put a corrected transcript back into one Plaud recording, safely (see references/plaud-upload.md).

Usage:
    python plaud_upload.py snapshot --file-id ID --auth auth.json --out DIR
    python plaud_upload.py speakers --file-id ID --auth auth.json --out DIR --map map.json [--apply]
    python plaud_upload.py replace  --file-id ID --auth auth.json --out DIR --part part.json
                                    --plaud-start YYYY-MM-DDTHH:MM:SS+07:00 [--apply]

Without --apply nothing is written: the target, a report and hashes land in DIR for review. --apply\nwrites only if Plaud and the target still match that reviewed dry run.
Only the polished source (`transaction_polish`) is ever written, through POST /ai/update_source_info;
the raw source (`transaction`) must stay byte-identical, proven by a read after the write. Any mismatch
rolls back automatically. `speakers` (relabel only) is the path tested live; `replace` (new text) is not.

auth.json (mode 0600, never committed, deleted after the run):
    {"token": "<bearer token>", "api_base": "https://api.plaud.ai", "headers": {"x-pld-user": "..."}}
The token is sent only to api_base, never to the signed storage links. Plain Python 3.8+, no packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
MAX_SEG_MS = 60_000  # replace mode: join same-speaker lines into paragraphs up to this length


def canon(segs) -> str:
    """Same bytes as JavaScript JSON.stringify for these arrays."""
    return json.dumps(segs, ensure_ascii=False, separators=(",", ":"))


def sha(segs) -> str:
    return hashlib.sha256(canon(segs).encode("utf-8")).hexdigest()


class Plaud:
    def __init__(self, auth_path: Path):
        mode = stat.S_IMODE(os.stat(auth_path).st_mode)
        if mode & 0o077:
            sys.exit(f"{auth_path} must be mode 0600 (is {oct(mode)})")
        a = json.loads(auth_path.read_text())
        self.base = a.get("api_base", "https://api.plaud.ai").rstrip("/")
        self.headers = {"Authorization": f"bearer {a['token']}", "User-Agent": UA,
                        "Content-Type": "application/json", **a.get("headers", {})}

    def call(self, method: str, path: str, body=None) -> dict:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=self.headers)
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read().decode("utf-8"))
        if out.get("status") == -302 and out.get("data", {}).get("domains", {}).get("api"):
            self.base = out["data"]["domains"]["api"].rstrip("/")  # user region mismatch
            return self.call(method, path, body)
        return out

    def sources(self, file_id: str) -> dict:
        d = self.call("GET", f"/file/detail/{file_id}")
        if d.get("status") != 0:
            sys.exit(f"file/detail failed: status {d.get('status')} {d.get('msg', '')}")
        found = {}
        for c in d["data"].get("content_list", []):
            if c.get("data_type") in ("transaction", "transaction_polish"):
                req = urllib.request.Request(c["data_link"], headers={"User-Agent": UA, "Cache-Control": "no-cache"})
                with urllib.request.urlopen(req, timeout=60) as r:  # signed link: no Authorization header
                    found[c["data_type"]] = {"data_id": c["data_id"], "segments": json.loads(r.read().decode("utf-8"))}
        return found


def snapshot(p: Plaud, file_id: str, out: Path) -> dict:
    src = p.sources(file_id)
    if "transaction_polish" not in src:
        sys.exit("This recording has no polished transcript in Plaud, so there is nothing to update. "
                 "No endpoint that creates one is known; keep the transcript in the repo instead.")
    out.mkdir(parents=True, exist_ok=True)
    meta = {}
    for kind, v in src.items():
        (out / f"before.{kind}.json").write_text(canon(v["segments"]), encoding="utf-8")
        meta[kind] = {"data_id": v["data_id"], "count": len(v["segments"]), "sha256": sha(v["segments"])}
    (out / "before.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return src


def target_speakers(polish: list, mapping: dict) -> list:
    tgt = [dict(s, speaker=mapping.get(s.get("speaker"), s.get("speaker"))) for s in polish]
    strip = lambda a: [{k: v for k, v in s.items() if k != "speaker"} for s in a]  # noqa: E731
    assert strip(tgt) == strip(polish), "speaker-only edit changed another field"
    return tgt


def target_replace(polish: list, part: list, plaud_start: str) -> list:
    t0 = datetime.fromisoformat(plaud_start).timestamp() * 1000
    keys = set().union(*(s.keys() for s in polish)) if polish else {"start_time", "end_time", "content", "speaker"}
    out = []
    for s in part:
        a = datetime.fromisoformat(s["start_local"]).timestamp() * 1000 - t0
        b = datetime.fromisoformat(s["end_local"]).timestamp() * 1000 - t0
        if a < 0 or not s.get("text"):
            continue
        spk = s.get("speaker") or "Unknown"
        if out and out[-1]["speaker"] == spk and b - out[-1]["start_time"] <= MAX_SEG_MS:
            out[-1]["end_time"] = int(b)
            out[-1]["content"] += " " + s["text"]
        else:
            out.append({"start_time": int(a), "end_time": int(b), "content": s["text"], "speaker": spk})
    if "original_speaker" in keys:
        for s in out:
            s["original_speaker"] = s["speaker"]
    return out


def publish(p: Plaud, file_id: str, kind: str, data_id: str, segs: list) -> None:
    r = p.call("POST", "/ai/update_source_info", {"file_id": file_id, "source_type": kind,
                                                 "source_id": data_id, "source_content": canon(segs)})
    if r.get("status") != 0:
        raise RuntimeError(f"update_source_info {kind}: status {r.get('status')} {r.get('msg', '')}")


def verify(p: Plaud, file_id: str, want: dict) -> bool:
    for _ in range(5):
        now = p.sources(file_id)
        if all(sha(now[k]["segments"]) == h for k, h in want.items() if k in now):
            return True
        time.sleep(3)  # storage may lag behind the write
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["snapshot", "speakers", "replace"])
    ap.add_argument("--file-id", required=True)
    ap.add_argument("--auth", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--map", type=Path, help="speakers: {\"Speaker 1\": \"Name\", ...}")
    ap.add_argument("--part", type=Path, help="replace: transcript part JSON from this pipeline")
    ap.add_argument("--plaud-start", help="replace: recording start, ISO with offset")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    p = Plaud(a.auth)
    reviewed = None
    if a.apply:  # --apply only after a dry run in the same --out was reviewed
        try:
            reviewed = json.loads((a.out / "report.json").read_text())
        except FileNotFoundError:
            sys.exit("Run once without --apply, review DIR/report.json and the target, then add --apply.")
    src = snapshot(p, a.file_id, a.out)
    raw, pol = src.get("transaction"), src["transaction_polish"]
    if a.mode == "snapshot":
        print(json.dumps(json.loads((a.out / "before.meta.json").read_text()), indent=1))
        return
    if a.mode == "speakers":
        tgt = target_speakers(pol["segments"], json.loads(a.map.read_text(encoding="utf-8")))
    else:
        tgt = target_replace(pol["segments"], json.loads(a.part.read_text(encoding="utf-8")), a.plaud_start)
    (a.out / "target.transaction_polish.json").write_text(canon(tgt), encoding="utf-8")
    changed = sum(1 for x, y in zip(pol["segments"], tgt) if x != y) + abs(len(tgt) - len(pol["segments"]))
    report = {"mode": a.mode, "before": len(pol["segments"]), "after": len(tgt), "segments_changed": changed,
              "before_sha256": sha(pol["segments"]), "target_sha256": sha(tgt),
              "raw_sha256": sha(raw["segments"]) if raw else None, "applied": False}
    if a.apply:
        same = {k: reviewed.get(k) == report[k] for k in ("before_sha256", "target_sha256", "raw_sha256")}
        if not all(same.values()):
            sys.exit(f"Plaud or the target changed since the reviewed dry run {same}; dry-run again.")
        publish(p, a.file_id, "transaction_polish", pol["data_id"], tgt)
        want = {"transaction_polish": report["target_sha256"]}
        if raw:
            want["transaction"] = report["raw_sha256"]
        if verify(p, a.file_id, want):
            report["applied"] = True
        else:
            publish(p, a.file_id, "transaction_polish", pol["data_id"], pol["segments"])
            if raw and sha(p.sources(a.file_id)["transaction"]["segments"]) != report["raw_sha256"]:
                publish(p, a.file_id, "transaction", raw["data_id"], raw["segments"])
            back = {"transaction_polish": report["before_sha256"]}
            if raw:
                back["transaction"] = report["raw_sha256"]
            report["rollback"] = "ROLLED_BACK" if verify(p, a.file_id, back) else "ROLLBACK_UNVERIFIED"
    (a.out / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


main()
