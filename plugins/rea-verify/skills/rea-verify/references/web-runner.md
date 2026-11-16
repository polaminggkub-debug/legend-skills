# Web runner: one command per suite

`scripts/rea-web-run.sh <suite-dir>` runs a whole web check and prints one verdict line per promise.
The runner is the same for every project; the **suite** is the project's part and lives in its
repository, one folder per module (in a repository with `docs/verification/modules.json`:
`docs/verification/rea/<module-id>/`). A module gets its suite on its first run; later rounds and
versions run it again and add to it.

## Suite folder

| Path | What it is |
|---|---|
| `up.sh` | Brings up this suite's own local stack (database, API, auth, seed data) and serves a production build of the checked-out commit. Safe to run twice. Writes `$WORK/env` with `APP_URL`, `DIST_DIR` (the served build folder), `ALLOW_HOSTS`, and anything its checks need. Stack name and ports come from variables with defaults. |
| `down.sh` | Removes that stack and server. |
| `suite.env` | Optional settings: `BROWSER_TZ`, `BROWSER_LANG`, `SERIAL="a b"` (scenarios that write, run one after another), `BUNDLE_SCENARIO` and `BUNDLE_STEPS` (the scenario whose first N actions sign in before `analyze-web-bundle`). |
| `scenarios/<name>.json` | One `capture-browser-scenario` input per scenario, without a `browser` block; `${APP_URL}` is filled in. Same step ids on every version, so versions diff. |
| `checks/<name>` | Executables. Each proves promises and prints one line per promise: `PASS <id> <fact>`, `FAIL <id> <what was seen>` or `NOT-CHECKED <id> <reason>`. `<id>` is the promise (`F12`) or the Issue. They read `$WORK/env`. |

A check judges what a user or the public API can observe: a rendered screen, a downloaded file, an
API answer as each kind of user. A check that reads the source tree proves nothing about the shipped
build.

## Running

```bash
rea-web-run.sh docs/verification/rea/<module-id>              # full run: the verdict
PREV=~/rea-work/<module>-<old-sha> rea-web-run.sh <suite>     # also diffs against the last verified version
ONLY=users-page,api-roles rea-web-run.sh <suite>              # re-check round or while fixing: PARTIAL
```

- Start it in the background with a log and wait for it; read only its last lines and
  `$WORK/evidence/results.txt`, `web-flags.txt` and `bundle-sweep.txt`.
- Exit 0: no FAIL. Exit 1: a FAIL line. Exit 2: `BLOCKED: <reason>`; report that line and stop.
- `$WORK/evidence/` already holds the three required files (`rea-bundle.json`, `rea-session-*.json`,
  `rea-diff.json`); copy that folder into the report. Raw REA output stays in `$WORK/raw`.
- A scenario with a failed step, a check that prints no verdict line, and a check that exits non-zero
  are each a FAIL. Silence is never a pass.
- `ONLY` takes scenario and check names (an unknown name stops the run and lists the valid ones).
  That run prints `PARTIAL RUN — not a release verdict`; it still writes the bundle, diff and sweep
  evidence, which a re-check round's report needs.

## What stays with the model

Writing the suite on a module's first run, turning each flag and sweep hit into a finding or a "not
a bug" reason, tracing findings, and the report. A new promise or bug gets a scenario or a check in
the suite, never a one-off script.
