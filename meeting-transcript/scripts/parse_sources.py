"""Parse the raw Plaud MCP dumps and Wispr Flow files into one common segment format.

Each output row (WORK/parsed/<tx>.jsonl) is
  {"tx", "audio", "pos_start_ms", "pos_end_ms", "speaker", "text"}
where pos_* are positions inside the source audio file `audio` (see config.SOURCES).
Plaud photo marks go to WORK/parsed/marks.json. Mapping to wall clock happens later
(config.source_to_epoch_ms) once offsets are measured.
Usage: python parse_sources.py
"""
from __future__ import annotations

import json
import re

from config import SOURCES, SRC, WORK

WRAP = re.compile(r'source="[^"]*">\s*(.*?)\s*</untrusted-user-data-[0-9a-f]+>\s*$', re.S)


def plaud_payload(path):
    """Return the JSON inside the untrusted-data wrapper, or None if the block is missing."""
    text = json.loads(path.read_text())["result"]["content"][0]["text"]
    m = WRAP.search(text)
    return json.loads(m.group(1)) if m else None


def parse_plaud(src: str) -> tuple[list[dict], list[dict]]:
    folder = SRC / "plaud" / SOURCES[src]["id"]
    rows, marks = [], []
    tr = plaud_payload(folder / "transcript.transaction.p0.json")
    if tr:
        assert tr.get("next_cursor") is None and tr["returned"] == tr["total"], src
        polish = plaud_payload(folder / "transcript.transaction_polish.p0.json")
        if polish and [s["content"] for s in polish["segments"]] != [s["content"] for s in tr["segments"]]:
            print(f"NOTE {src}: transaction_polish differs from transaction")
        for s in tr["segments"]:
            rows.append({"tx": f"plaud:{src}", "audio": src, "pos_start_ms": s["start_time"],
                         "pos_end_ms": s["end_time"], "speaker": s["speaker"], "text": s["content"].strip()})
    mm = plaud_payload(folder / "transcript.mark_memo.p0.json")
    for m in (mm or {}).get("marks", []):
        marks.append({"audio": src, "pos_ms": m["timestamp"], "mark_id": m["mark_id"], "type": m.get("mark_type"),
                      "caption": m.get("mark_content"), "plaud_file": SOURCES[src]["id"]})
    return rows, marks


def mmss_to_ms(stamp: str) -> int:
    m, s = stamp.split(":")
    return (int(m) * 60 + int(s)) * 1000


def parse_wispr(src: str) -> dict[str, list[dict]]:
    folder = SRC / "wispr" / SOURCES[src]["id"]
    live = []
    for line in open(folder / "live.ndjson"):
        r = json.loads(line) if line.strip() else {}
        if "startRecordingMs" in r and r.get("text", "").strip():
            live.append({"tx": f"wispr-live:{src}", "audio": src, "pos_start_ms": r["startRecordingMs"],
                         "pos_end_ms": r["endRecordingMs"], "speaker": f"W{r['speaker']['id']}" if r.get("speaker") else "?",
                         "text": r["text"].strip()})
    refined = []
    lines = [json.loads(line) for line in open(folder / "refined.ndjson") if line.strip()]
    for i, r in enumerate(lines):
        start = mmss_to_ms(r["timestamp"])
        nxt = mmss_to_ms(lines[i + 1]["timestamp"]) if i + 1 < len(lines) else start + 5000
        refined.append({"tx": f"wispr-refined:{src}", "audio": src, "pos_start_ms": start,
                        "pos_end_ms": max(nxt, start + 1000), "speaker": f"W{r['speaker']['id']}",
                        "text": r["text"].strip(), "end_estimated": True})
    return {f"wispr-live:{src}": live, f"wispr-refined:{src}": refined}


def main():
    out = WORK / "parsed"
    out.mkdir(parents=True, exist_ok=True)
    all_marks = []
    for src, meta in SOURCES.items():
        if meta["kind"] == "plaud":
            rows, marks = parse_plaud(src)
            all_marks += marks
            txs = {f"plaud:{src}": rows} if rows else {}
        elif meta["kind"] == "wispr":
            txs = parse_wispr(src)
        else:
            txs = {}
        for tx, rows in txs.items():
            with open(out / f"{tx.replace(':', '__')}.jsonl", "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            chars = sum(len(r["text"]) for r in rows)
            print(f"{tx:28s} segments {len(rows):5d} chars {chars:7d}")
    (out / "marks.json").write_text(json.dumps(all_marks, ensure_ascii=False, indent=1))
    print("marks", len(all_marks))


if __name__ == "__main__":
    main()
