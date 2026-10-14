"""Show the segments around every window join so duplicates or gaps can be checked by eye, and
list source text (WL/WR/PL) that starts within 15 s before a join but runs past it.
Usage: python join_check.py [meeting ...]"""
from __future__ import annotations

import json
import sys

from config import MEETINGS, WORK, hms
from timeline import service_segments

if __name__ == "__main__":
    wins = json.loads((WORK / "merge" / "windows.json").read_text())
    for meeting in sys.argv[1:] or list(MEETINGS):
        ws = wins[meeting]
        for i in range(1, len(ws)):
            a, b = f"{meeting}-{i:02d}", f"{meeting}-{i + 1:02d}"
            pa, pb = WORK / "merge" / "out" / f"{a}.json", WORK / "merge" / "out" / f"{b}.json"
            if not (pa.exists() and pb.exists()):
                continue
            left = [s for s in json.loads(pa.read_text()) if s.get("type") != "mark"][-2:]
            right = [s for s in json.loads(pb.read_text()) if s.get("type") != "mark"][:2]
            cut = ws[i][0]
            print(f"\n== join {a} | {b} at {hms(cut)}")
            for s in left:
                print(f"  L {s['start']}-{s['end']} {s['speaker']}: {s['text'][-110:]}")
            for s in right:
                print(f"  R {s['start']}-{s['end']} {s['speaker']}: {s['text'][:110]}")
            for s in service_segments(meeting):
                if s["tag"] in ("WR", "PL") and cut - 15000 <= s["start"] < cut < s["end"] - 1500:
                    print(f"  ! {s['tag']} {hms(s['start'])}-{hms(s['end'])} crosses the join: {s['text'][-110:]}")
