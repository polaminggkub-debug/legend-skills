# Web apps: the scripted pipeline

The shipped file is the bundle the live site serves. Scripts do the clicking, capturing and counting
in one batch; the model writes scenarios, reads short flag lists and traces findings. Model turns are
the cost, so spend them on judgment, not on waiting or clicking.

## Steps

1. **Reuse the previous version's `scripts/`** (stack setup, seed, server, browser launcher,
   scenarios). Stack name, ports and paths come from environment variables with defaults
   (`STACK=${STACK:-srea3}`, `PORT_BASE=…`, `WORK=…`); if a copied script hardcodes them, make them
   variables once and commit that. Each run gets its own stack, ports and browser port.
2. **Scenarios as data:** one `capture-browser-scenario` input per scenario, same step ids on every
   build. Cover every runtime promise, plus one scenario per page that uses a shared component under
   check (a shared component has no page of its own). Do what a user does: open, sort, filter,
   search, page, open a row, edit, save; over-fetch and duplicate writes only show under use.
3. **One background shell command:** fresh browser and CDP port per scenario, stack reset per build.
   `scripts/run-scenario.sh <scenario.json> <cdp-port> <out.json>` does one scenario: it starts
   `scripts/chrome.sh` (headless Chromium in Docker, only `ALLOW_HOSTS` resolve, time zone from
   `BROWSER_TZ`), points the scenario's `browser` block at it, runs `capture-browser-scenario`, and
   removes the browser. Write each scenario file once without a `browser` block; secrets come from
   environment variables named in its `secrets` list. Read-only scenarios run in parallel, e.g.
   `run-scenario.sh a.json 9401 raw/a.json & run-scenario.sh b.json 9402 raw/b.json & wait`;
   writing scenarios run one after another after a reset (or on their own stack). Wait with
   `curl --retry N --retry-connrefused`, `timeout` or `docker wait`. The same command runs
   `list-browser-targets`, `analyze-web-bundle`, `export-web-scripts` and `compare-web-captures`,
   raw output to disk.
4. **While it runs:** write promises, run the bundle sweep, and start one read-only static-review
   subagent per shared component under check. It reads the component's model files and lists logic
   bugs with file:line (wrong-day dates, server vs client mismatch, unescaped search, retried writes,
   missed events). Flags only catch request-shaped bugs; wrong-data bugs come from this review.
5. **Read short text only:**
   - `scripts/web_compact.py <raw> > <compact>` per capture.
   - `scripts/web_flags.py <compactDir> --new <tag> [--old <prevTag>] <scenarios…>`: select=*, wide
     or oversized responses, duplicate writes or RPCs in one step, repeated GETs, failing requests,
     console lines, diff against the previous version.
   - `scripts/bundle_sweep.py <servedDistOrExportedScripts>`: keys, JWT roles, local and private
     URLs, console calls, demo or test code, source maps, third-party hosts.

   For one field of a raw file use `jq` or `grep`. `export-web-scripts` takes the plain capture
   result: capture without `--full-output`, or pass `.data` only.
6. **Every flag and sweep hit becomes a finding or a "not a bug" reason.** That includes select=* and
   wide reads, and sweep hits under secret-key, demo-test-code, private-ip, local-url and
   console-call: demo code and private IPs in a production bundle are for the owner to judge.
   Harness-only flags (blocked fonts, isolated network) are noted as harness.
7. **Trace every finding.** Build the same commit once with `vite build --sourcemap` (not deployed),
   serve it, capture one page of it with `inspect-web-page --include-script-sources`, and run
   `export-web-scripts` on that result's `.data`. Then per finding:
   `MAP_DIR=<build>/assets MAP_URL=http://127.0.0.1:<port>/assets scripts/trace.py <id> <label> <exportDir> <chunk-suffix> <literal> [occurrence]`
   finds the literal in that chunk, runs `trace-web-source-location`, and appends the result to
   `evidence/rea-trace.json`. A finding cites the traced `file:line`; one without a traced line is
   marked `untraced`.
8. **Promises** take their observable from the same captures, or from the previous version's
   one-command checks (Playwright or similar) run once. Re-run only scenarios whose code changed.

## Required REA tools and evidence

| REA tool | Evidence file |
|---|---|
| `list-browser-targets`, then `analyze-web-bundle <endpoint> <targetId>` | `evidence/rea-bundle.json` (trimmed) plus `bundle_sweep.py` output |
| `capture-browser-scenario` (or `observe-web-session`) per scenario | `evidence/rea-session-<scenario>.json` (`web_compact.py` output) |
| `compare-web-captures` against the previous verified version (first: `no previous`) | `evidence/rea-diff.json` plus `web_flags.py` output |
| `trace-web-source-location` per finding | cited in the finding |

A web report missing any of these files (without a `BLOCKED` line) has no verdict and gets no tag.

**Commit proof:** `compare-source-to-bundle <inputJson>` needs source maps. When the live bundle has
none, compare a source-map build of the candidate commit on the worker, or byte-compare a clean
production rebuild with build ids and chunk hashes masked. Record which ran; the proven commit is the
one the verdict and tag belong to.

## Findings even without a promise

- requests fetching more columns or rows than the screen shows
- repeated or failing requests the page hides
- console warnings and errors
- strings or code that should not ship (keys, demo or test code, local or private URLs, debug logs)
- session differences against the previous version that no promise or release note explains
