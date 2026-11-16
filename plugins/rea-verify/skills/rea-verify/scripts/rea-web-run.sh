#!/bin/bash
# One-command runner for a web app's rea-verify suite: stack up, REA scenarios, REA bundle and diff, flags, sweep,
# promise checks, one verdict line per promise. The model starts it and reads its last lines; it drives no step.
# The contract of a suite folder is in references/web-runner.md.
#
# usage: [ONLY=<names>] [PREV=<older WORK>] [KEEP=1] rea-web-run.sh <suite-dir>
#   ONLY  comma list of scenario and check names; the run is then PARTIAL, never a release verdict
#   PREV  WORK folder of the last verified version (its raw/ feeds compare-web-captures)
#   KEEP  1 leaves the stack up (down.sh not called)
# env: WORK (default ~/rea-work/<suite>-<sha>), PORT_BASE (default 9400), TAG (default git short sha)
# out: $WORK/evidence/{rea-bundle.json,rea-session-<scenario>.json,rea-diff.json,web-flags.txt,bundle-sweep.txt,
#      results.txt}; raw REA output stays in $WORK/raw
# exit: 0 no FAIL, 1 a FAIL, 2 BLOCKED (a required tool or the stack could not run), 64 bad usage
set -u
T0=$(date +%s); HERE=$(cd "$(dirname "$0")" && pwd)
SUITE=$(cd "${1:?usage: rea-web-run.sh <suite-dir>}" && pwd) || exit 64
NAME=$(basename "$SUITE")
TAG=${TAG:-$(git -C "$SUITE" rev-parse --short=9 HEAD 2>/dev/null || echo notag)}
export WORK=${WORK:-$HOME/rea-work/$NAME-$TAG} SUITE TAG
RAW=$WORK/raw; EV=$WORK/evidence; RES=$EV/results.txt; PORT_BASE=${PORT_BASE:-9400}
mkdir -p "$RAW" "$EV" "$WORK/scn" "$WORK/compact"; : > "$RES"
export REA_LOG=$WORK/rea-commands.txt
blocked() { echo "BLOCKED: $*" | tee -a "$RES"; finish 2; }
finish() {
  [ "${KEEP:-0}" = 1 ] || { [ -x "$SUITE/down.sh" ] && "$SUITE/down.sh" > "$WORK/down.log" 2>&1; }
  [ -n "${ONLY:-}" ] && echo "PARTIAL RUN — not a release verdict (ONLY=$ONLY)"
  echo "rea-web-run $NAME $TAG: $(grep -c '^PASS ' "$RES") pass, $(grep -c '^FAIL ' "$RES") fail," \
    "$(grep -c '^NOT-CHECKED ' "$RES") not checked, $(( $(date +%s) - T0 )) s; evidence $EV"
  exit "$1"
}
rea_run() { # rea_run <out> <timeout> <rea args...>: raw output to $RAW/<out>, one line in rea-commands.txt
  local out=$1 to=$2; shift 2
  timeout "$to" rea "$@" --format json --full-output > "$RAW/$out" 2> "$RAW/$out.stderr"; local rc=$?
  echo "rea $1 | exit $rc" >> "$REA_LOG"; return $rc
}
command -v rea >/dev/null || blocked "rea not on PATH"
command -v docker >/dev/null || blocked "docker not on PATH"
[ -f "$SUITE/suite.env" ] && { set -a; . "$SUITE/suite.env"; set +a; }

# Names: scenarios/<name>.json and checks/<name>.*; ONLY must name known ones.
SCN=$(cd "$SUITE/scenarios" 2>/dev/null && ls *.json 2>/dev/null | sed 's/\.json$//')
CHK=$(cd "$SUITE/checks" 2>/dev/null && ls 2>/dev/null)
if [ -n "${ONLY:-}" ]; then
  for o in ${ONLY//,/ }; do
    echo "$SCN $CHK" | tr ' ' '\n' | sed 's/\..*$//' | grep -qx "${o%%.*}" \
      || { echo "unknown ONLY name: $o. Valid: $(echo $SCN $CHK)"; exit 64; }
  done
fi
want() { [ -z "${ONLY:-}" ] || echo ",$ONLY," | grep -q ",${1%%.*},"; }

# 1. The suite's own stack and production build. up.sh writes $WORK/env: APP_URL, DIST_DIR, ALLOW_HOSTS, plus
#    anything its checks need.
[ -x "$SUITE/up.sh" ] || blocked "$SUITE/up.sh missing"
"$SUITE/up.sh" > "$WORK/up.log" 2>&1 || blocked "up.sh failed: tail $WORK/up.log"
set -a; . "$WORK/env"; set +a
: "${APP_URL:?up.sh must write APP_URL to \$WORK/env}"
export ALLOW_HOSTS=${ALLOW_HOSTS:-127.0.0.1,localhost}

# 2. REA scenarios: ${APP_URL} filled in, fresh Chromium each. Read-only ones in parallel, SERIAL ones in order.
i=0; PIDS=""
run_scn() { "$HERE/run-scenario.sh" "$WORK/scn/$1.json" "$2" "$RAW/scn-$1.json"; echo $? > "$RAW/scn-$1.rc"; }
for s in $SCN; do
  sed "s#\${APP_URL}#$APP_URL#g" "$SUITE/scenarios/$s.json" > "$WORK/scn/$s.json"
  want "$s" || continue
  i=$((i + 1))
  case " ${SERIAL:-} " in *" $s "*) continue;; esac
  run_scn "$s" $((PORT_BASE + i)) & PIDS="$PIDS $!"
done
[ -n "$PIDS" ] && wait $PIDS
for s in ${SERIAL:-}; do want "$s" && [ -f "$WORK/scn/$s.json" ] && run_scn "$s" "$PORT_BASE"; done
RAN=""
for s in $SCN; do
  [ -f "$RAW/scn-$s.rc" ] || continue
  RAN="$RAN $s"
  python3 -I "$HERE/web_compact.py" "$RAW/scn-$s.json" > "$WORK/compact/$s-$TAG.json" 2> "$RAW/scn-$s.compact.err" \
    && cp "$WORK/compact/$s-$TAG.json" "$EV/rea-session-$s.json"
  FAILED=$(python3 -I -c 'import json,sys; print("; ".join(json.load(open(sys.argv[1]))["steps_failed"]))' \
    "$WORK/compact/$s-$TAG.json" 2>/dev/null || echo "no readable capture")
  if [ "$(cat "$RAW/scn-$s.rc")" != 0 ] || [ -n "$FAILED" ]; then
    echo "FAIL scenario:$s rea exit $(cat "$RAW/scn-$s.rc") ${FAILED:0:160}" >> "$RES"
  else echo "PASS scenario:$s all steps completed" >> "$RES"; fi
done
[ -n "$SCN" ] && [ -z "$RAN" ] && [ -z "${ONLY:-}" ] && blocked "no scenario ran"
[ -n "$SCN" ] || echo "NOT-CHECKED rea-evidence suite has no scenarios/, so no REA capture, bundle or diff" >> "$RES"

# 3. Bundle: sign in with the first BUNDLE_STEPS actions of BUNDLE_SCENARIO on a kept browser, then analyze it.
#    Steps 3 to 5 run on a PARTIAL run too: a re-check round still owes the three evidence files.
if [ -n "$SCN" ]; then
  P=$((PORT_BASE + 90)); B=${BUNDLE_SCENARIO:-$(echo $SCN | cut -d' ' -f1)}
  docker rm -f "rea-chrome-$P" >/dev/null 2>&1; nohup "$HERE/chrome.sh" "$P" > "$WORK/chrome-$P.log" 2>&1 &
  curl -s --retry 60 --retry-connrefused --retry-delay 1 "127.0.0.1:$P/json/version" >/dev/null
  TID=$(curl -s -X PUT "http://127.0.0.1:$P/json/new?about:blank" | python3 -I -c 'import json,sys;print(json.load(sys.stdin)["id"])')
  python3 -I -c '
import json, sys
s = json.load(open(sys.argv[1])); s["actions"] = s["actions"][:int(sys.argv[4])]
s["browser"] = {"mode": "connect", "cdp_endpoint": sys.argv[2], "target_id": sys.argv[3]}
json.dump(s, open(sys.argv[5], "w"))' "$WORK/scn/$B.json" "http://127.0.0.1:$P" "$TID" "${BUNDLE_STEPS:-999}" "$WORK/scn/_bundle.json"
  rea_run bundle-signin.json 300 capture-browser-scenario "$WORK/scn/_bundle.json"
  rea_run targets.json 300 list-browser-targets "http://127.0.0.1:$P" --allowed-origins "$APP_URL"
  rea_run bundle.json 600 analyze-web-bundle "http://127.0.0.1:$P" "$TID" --allowed-origins "$APP_URL"; BRC=$?
  docker rm -f "rea-chrome-$P" >/dev/null 2>&1
  [ $BRC = 0 ] || blocked "rea analyze-web-bundle exit $BRC: $RAW/bundle.json.stderr"
  python3 -I "$HERE/trim_json.py" "$RAW/bundle.json" > "$EV/rea-bundle.json"

  # 4. Diff against the last verified version's captures, scenario by scenario.
  norm() { python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); d=d.get("data",d); json.dump(d.get("normalized_result",d),open(sys.argv[2],"w"))' "$1" "$2"; }
  if [ -n "${PREV:-}" ] && [ -d "$PREV/raw" ]; then
    echo '{"previous": "'"$PREV"'", "scenarios": {' > "$EV/rea-diff.json"; SEP=""
    for s in $RAN; do
      [ -f "$PREV/raw/scn-$s.json" ] || continue
      norm "$PREV/raw/scn-$s.json" "$RAW/norm-old-$s.json"; norm "$RAW/scn-$s.json" "$RAW/norm-new-$s.json"
      rea_run "diff-$s.json" 300 compare-web-captures "$RAW/norm-old-$s.json" "$RAW/norm-new-$s.json" \
        || blocked "rea compare-web-captures $s failed: $RAW/diff-$s.json.stderr"
      printf '%s"%s": ' "$SEP" "$s" >> "$EV/rea-diff.json"; python3 -I "$HERE/trim_json.py" "$RAW/diff-$s.json" >> "$EV/rea-diff.json"; SEP=","
      cp "$PREV"/compact/"$s"-*.json "$WORK/compact/" 2>/dev/null
    done
    echo '}}' >> "$EV/rea-diff.json"
    OLDTAG=$(ls "$PREV/compact" 2>/dev/null | sed -n 's/.*-\([^-]*\)\.json$/\1/p' | head -1)
  else echo '{"previous": "no previous"}' > "$EV/rea-diff.json"; fi

  # 5. Flags and sweep: short text for the model; every hit becomes a finding or a "not a bug" reason.
  python3 -I "$HERE/web_flags.py" "$WORK/compact" --new "$TAG" ${OLDTAG:+--old "$OLDTAG"} $RAN > "$EV/web-flags.txt" 2>&1
  [ -n "${DIST_DIR:-}" ] && python3 -I "$HERE/bundle_sweep.py" "$DIST_DIR" > "$EV/bundle-sweep.txt" 2>&1
fi

# 6. Promise checks: each prints PASS|FAIL|NOT-CHECKED <id> <reason> lines. A check that prints none, or dies,
#    is a FAIL: silence never counts as a pass.
for c in $CHK; do
  want "$c" || continue
  OUT=$(cd "$SUITE/checks" && timeout "${CHECK_TIMEOUT:-600}" "./$c" 2> "$WORK/check-$c.err"); RC=$?
  LINES=$(echo "$OUT" | grep -E '^(PASS|FAIL|NOT-CHECKED) [^ ]+')
  echo "$LINES" | grep . >> "$RES"
  [ -n "$LINES" ] || echo "FAIL check:$c printed no verdict line (exit $RC): $WORK/check-$c.err" >> "$RES"
  [ $RC = 0 ] || echo "$LINES" | grep -q '^FAIL ' || echo "FAIL check:$c exit $RC with no FAIL line: $WORK/check-$c.err" >> "$RES"
done

cat "$RES"
[ -f "$EV/web-flags.txt" ] && grep -E '^  [^ ]+: select' "$EV/web-flags.txt" | sed 's/^/flags/'
grep -q '^FAIL ' "$RES" && finish 1
finish 0
