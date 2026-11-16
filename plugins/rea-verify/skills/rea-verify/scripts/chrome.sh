#!/bin/bash
# Headless Chromium in Docker for REA connect mode (`capture-browser-scenario` with browser.mode=connect).
# Host network, so CDP and the app under test share 127.0.0.1. CDP listens on 127.0.0.1 only. Every host not in
# ALLOW_HOSTS resolves to NOTFOUND, so the run cannot reach live services by mistake.
# usage: chrome.sh <cdp-port>   (container rea-chrome-<port>; stop it with `docker rm -f rea-chrome-<port>`)
# env:   ALLOW_HOSTS  comma list of hosts that resolve (default 127.0.0.1,localhost)
#        BROWSER_TZ   browser time zone (default UTC; set the customer's zone, e.g. Asia/Bangkok)
#        BROWSER_LANG Chromium --lang (default en-US)
#        WINDOW       window size (default 1440,900)
#        IMAGE        Playwright image (default mcr.microsoft.com/playwright:v1.57.0-noble)
P=${1:?usage: chrome.sh <cdp-port>}
ALLOW_HOSTS=${ALLOW_HOSTS:-127.0.0.1,localhost}
RULES="MAP * ~NOTFOUND"
IFS=, read -ra HOSTS <<< "$ALLOW_HOSTS"
for h in "${HOSTS[@]}"; do RULES="$RULES, EXCLUDE $h"; done
exec docker run --rm --name "rea-chrome-$P" --network host --ipc=host \
  -e TZ="${BROWSER_TZ:-UTC}" --user 1001:1001 --mount type=tmpfs,destination=/tmp/prof \
  "${IMAGE:-mcr.microsoft.com/playwright:v1.57.0-noble}" \
  sh -c 'exec /ms-playwright/chromium-*/chrome-linux64/chrome "$@"' chrome \
  --headless=new --no-sandbox --remote-debugging-port="$P" --remote-debugging-address=127.0.0.1 \
  "--host-resolver-rules=$RULES" --user-data-dir=/tmp/prof --lang="${BROWSER_LANG:-en-US}" \
  --window-size="${WINDOW:-1440,900}" --no-first-run --no-default-browser-check \
  --disable-background-networking --disable-component-update --disable-sync --disable-domain-reliability about:blank
