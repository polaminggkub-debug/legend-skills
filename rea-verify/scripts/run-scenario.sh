#!/bin/bash
# One `rea capture-browser-scenario` run on a fresh Chromium (chrome.sh), so scenarios never share cookies or cache
# and can run in parallel on different CDP ports.
# usage: run-scenario.sh <scenario.json> <cdp-port> <out.json>
#   scenario.json  a full capture-browser-scenario input; its `browser` block is replaced with connect mode on this
#                  Chromium (cdp_endpoint + a new target), so one file works for every run
#   out.json       raw REA result (full output; read it with web_compact.py, never in context); stderr -> out.json.stderr
# env: WORK (default ~/rea-work) gets rea-commands.txt; chrome.sh env (ALLOW_HOSTS, BROWSER_TZ, ...) passes through.
# exit: REA's exit code.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
IN=${1:?scenario.json}; P=${2:?cdp-port}; OUT=${3:?out.json}; WORK=${WORK:-$HOME/rea-work}
mkdir -p "$WORK" "$(dirname "$OUT")"
docker rm -f "rea-chrome-$P" >/dev/null 2>&1
nohup "$HERE/chrome.sh" "$P" > "$WORK/chrome-$P.log" 2>&1 &
trap 'docker rm -f "rea-chrome-$P" >/dev/null 2>&1' EXIT
curl -s --retry 60 --retry-connrefused --retry-delay 1 "127.0.0.1:$P/json/version" >/dev/null || { echo "chrome on $P not up: $WORK/chrome-$P.log" >&2; exit 3; }
T=$(curl -s -X PUT "http://127.0.0.1:$P/json/new?about:blank" | python3 -I -c 'import json,sys;print(json.load(sys.stdin)["id"])')
RUN_IN="$OUT.input.json"
python3 -I -c '
import json, sys
s = json.load(open(sys.argv[1]))
s["browser"] = {"mode": "connect", "cdp_endpoint": sys.argv[2], "target_id": sys.argv[3]}
json.dump(s, open(sys.argv[4], "w"), ensure_ascii=False, indent=1)' "$IN" "http://127.0.0.1:$P" "$T" "$RUN_IN"
rea capture-browser-scenario "$RUN_IN" --format json --full-output > "$OUT" 2> "$OUT.stderr"; RC=$?
echo "rea capture-browser-scenario $RUN_IN | exit $RC" >> "$WORK/rea-commands.txt"
exit $RC
