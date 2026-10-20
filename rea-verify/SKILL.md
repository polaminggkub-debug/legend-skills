---
name: rea-verify
description: >
  Verify a release of the user's own program from the shipped file, not its source: reverse
  engineer it with REA, check every promise from the Issues and guides, run black-box checks on the
  worker machine, and give a per-version verdict with suspected bugs. Use when the user asks to
  check, verify, audit or black-box test a built exe/app/package against its requirements, compare
  what a release really does with what was promised, or find bugs in a shipped version
  ("ตรวจตัวที่ส่งจริง", "reverse engineer โปรแกรมเรา", "เช็คว่าทำงานตาม requirement").
---

# REA verify

Treat the **shipped file** as the only witness. Source code shows what someone meant to build; the
file the customer runs shows what was built. Each run checks one version against its **promises**
(what the Issues, guides and release notes say it does) and ends with a **verdict** per promise.

Scope: programs the user owns or builds. Someone else's program is out of scope for this skill.

## 1. Pin the target

- Take the file from where it ships (release host, install kit). Record name, version and sha256, and
  match the sha256 against the published manifest or release note. A mismatch is the first finding.
- Work in a scratch folder outside every repository. Put the shipped file in its own empty folder.
- Keep the source tree closed for the whole run. The value of this check is independence: a promise
  is judged from the requirement text and the file, never from what the code was meant to do.

Done when the target's sha256 is written down and matches its release record (or the mismatch is).

## 2. Write the promises (the oracle)

Load the `chris` skill and turn every requirement into a checkable promise, `F1`…`Fn`, each citing its
source (Issue number, guide section, release note). Sources: closed Issues touching the program since
the previous verified version, the user guide shipped with it, the release notes, and the **approved
UX**: mock-ups and screens the owner approved (artifact links and acceptance lists in those Issues).
Each approved behaviour (which filter a column opens, what a screen shows, how fast it answers) is its
own promise, so a release that fixes bugs but loses approved UX gets a Different verdict. For a new version,
start from the previous version's `checklist.md` and add the promises closed since.

Done when every closed Issue for this program since the last verified version maps to at least one
promise or is listed as "no observable promise".

## 3. Open the file

Route by format; [references/formats.md](references/formats.md) has the commands.

- .NET single-file exe: REA reports `not-managed`, because the app hides inside the apphost. Unpack
  with `scripts/unbundle.py`, then point REA at the app DLLs.
- Plain .NET assembly: REA `inspect-managed-members --format json`.
- Electron / JavaScript: REA `analyze-javascript-application`.
- Native: REA `open_binary` with Ghidra/IDA, or `inspect-go-binary` / `inspect-rust-binary`.
- Web app: see "Web apps" below.

Done when every app module (not framework files) has REA evidence saved to disk.

### Web apps: the fast pipeline

The shipped file of a web app is the bundle the live site serves. Run REA on it as **one scripted
batch**, never one model turn per click. A previous agent-driven run took 56 minutes and $17.73.
A scripted run of the same scenarios found the same request bugs in 3 minutes for $0.17. The model's
time is the cost, so the model writes the scenarios and reads short flag lists. Scripts do the
clicking, capturing and counting.

1. **Reuse first.** Copy the previous version's `scripts/` folder (stack setup, seed, local server,
   browser launcher, scenario file). Write setup only for what is missing.
2. **Write scenarios once, as data.** One REA `capture-browser-scenario` input per scenario, with the
   same step ids on every build. Cover every promise that needs runtime, plus one scenario for each
   page that uses a shared component under check. A shared component has no page of its own, so its
   bugs show through the pages that use it. Each scenario does what a user does: open, sort, filter,
   search, page, open a row, edit and save. Over-fetch and duplicate writes only show when the page
   is used.
3. **Run everything in one shell command, in parallel.** Every scenario gets a fresh browser with its
   own CDP port, and every build gets a stack reset. The script also runs `list-browser-targets`,
   `analyze-web-bundle`, `export-web-scripts` and `compare-web-captures`. Raw output goes to disk only.
4. **Read only short text:**
   - `scripts/web_compact.py <raw> > <compact>` for each capture.
   - `scripts/web_flags.py <compactDir> --new <tag> [--old <prevTag>] <scenarios…>`: flags for
     select=*, wide or oversized responses, duplicate writes or RPCs in one step, repeated GETs,
     failing requests and console lines, plus the diff against the previous version.
   - `scripts/bundle_sweep.py <servedDistOrExportedScripts>`: keys, JWT roles, local and private
     URLs, console calls, demo or test code, source maps and third-party hosts.

   Never open a raw capture or bundle JSON in context. Use `jq`, `grep` or a short script for a
   single field.
5. **Turn each flag into a finding or a stated "not a bug" reason.** Trace each kept finding with
   `trace-web-source-location`, using a source-mapped build of the same commit (never deployed). It
   then cites a source file and line. A flag that only the test harness causes (blocked fonts, an
   isolated network) is noted as harness, not as a bug.
6. **Promises:** every runtime promise gets its observable from the same captures, or from the
   previous version's one-command checks (Playwright or similar) run once. Never re-drive a promise by
   hand when a script already checks it.

Spend model turns on choosing scenarios, judging flags and tracing; never on waiting or clicking.
Start the run in the background, and do static work (promises, bundle sweep) while it runs. Re-run
only the scenarios whose code changed, and only to confirm a fix.

| Required REA tool | Evidence file in the report folder |
|---|---|
| `list-browser-targets`, then `analyze-web-bundle <endpoint> <targetId>`: inventory of the shipped scripts, routes, endpoints, strings, libraries | `evidence/rea-bundle.json` (trimmed) plus `bundle_sweep.py` output |
| `capture-browser-scenario` (or `observe-web-session`) for every runtime scenario: all requests and responses, console, errors | `evidence/rea-session-<scenario>.json` (the `web_compact.py` output) |
| `compare-web-captures` against the previous verified version's sessions (first version: write `no previous`) | `evidence/rea-diff.json` plus `web_flags.py` output |
| `trace-web-source-location` for every finding, mapping minified code back to its module | cited in the finding |

The tools are required, not suggestions. If a tool cannot run, write `BLOCKED: <tool> <reason>` in the
report and stop for the owner. Never switch method silently.

Commit proof: `compare-source-to-bundle <inputJson>` needs source maps. When the live bundle has
none, build the candidate commit with source maps on the worker (never deploy it) and compare that,
or byte-compare a clean production rebuild with build ids and chunk hashes masked. Record which one
ran. The proven commit is the one the verdict and its tag belong to.

What counts as a finding, even when no promise mentions it:
- requests that fetch more columns or rows than the screen shows
- repeated or failing requests that the page hides
- console warnings and errors
- strings or code that should not ship (keys, test or demo code, local or private URLs, debug logs)
- any session difference against the previous version that no promise or release note explains

Server-side promises (database functions, row-level security, API rules) are not in the bundle.
Check them through the public API, signed in as each kind of user, never from the bundle or with an
admin key.

## 4. Static checks

Read evidence through `scripts/managed_evidence.py` (strings, callers, IL constants) so large JSON
never enters context. For each promise, find the code that carries it and the facts that prove or
break it: the literal that names the file, the constant that sets the timing, the call edge that
proves who reads the secret. Then sweep for what the promises never mention:

- **Suspected bugs:** decompile the methods behind each promise (ILSpy for .NET) and review them; use
  the finecomb plugin checklist when installed. Look for swallowed exceptions, endless retries,
  local-vs-UTC time, null handling, SQL built from strings, writes where only reads were promised.
- **Version diff:** compare members with the previous verified version (`compare-managed-members`).
  A change no promise or release note explains is a finding.
- **Secrets:** scan all string literals for keys, tokens, passwords, private URLs.
- **Dependencies:** list bundled libraries and versions; check them for known CVEs.
- **Extras:** features in the file that no promise asked for.

Done when every promise has static evidence or is marked "needs runtime".

## 5. Runtime checks on the worker

Static evidence proves code is present and wired; it cannot prove it works. Every runtime check runs
on the worker machine: the one named in `~/.claude/docs/work-routing.md` when that file exists
(brief it with `poo-handoff` when installed), otherwise the machine the user names. Run inside a VM
or container that matches the customer's OS; the user's own computer only reads results. REA
`capture-process` records Linux/macOS processes only; on Windows trace with ProcMon or ETW.

Build scenarios from the promises: [references/runtime-checks.md](references/runtime-checks.md)
lists the kinds. Each scenario names the promise, the steps, and the observable that turns it pass
or fail. Use copies of data, never the customer's live data.

The 10-minute budget in that file covers each run, and each re-check run after a fix too. When the
program has a **one-command runner** (listed under "One-command runners" in that file), run it: it
is the runtime check. Otherwise start from the previous version's `scripts/` folder (report
layout) instead of writing setup again.

Done when every promise marked "needs runtime" has a scenario result or a stated reason it could
not run.

## 6. Report

Write one folder per version; [references/report-layout.md](references/report-layout.md) has the
layout and template. Each promise gets one verdict, with its evidence and whether that evidence is
static or runtime:

- **Match**: the file does what the promise says.
- **Different**: the file does something else (state both). The owner decides: fix the file, or fix
  the promise.
- **Bug suspect**: evidence of a likely defect; say what would confirm it.
- **Partial**: some of the promise proven, the rest open.
- **Not checked**: with the reason.

A web report without `evidence/rea-bundle.json`, `evidence/rea-session-*.json` and
`evidence/rea-diff.json` (or a `BLOCKED` line for each missing one) has no verdict: tag nothing.

Done when every promise has a verdict, the folder README's version table has the new row, every
evidence file is free of secrets and customer data, and the owner's open questions are listed.

## 7. Record the verdict (only with `docs/verification/modules.json`)

Skip this step when the program's repository has no `docs/verification/modules.json`.

1. Open the bug Issues: one per Bug suspect, or one parent Issue that lists them. Each bug Issue
   names the approved-UX promises (`Fn`) its screen carries under **Must keep**, so the fix is
   judged on both: the bug gone and every Must keep promise still Match. Add label
   `rea-verify` to every Issue this run opened (create the label once if the repo lacks it).
2. Tag the commit the checked build came from (the release tag's commit, or the commit
   `compare-source-to-bundle` proved live), with the module id from `modules.json`:
   `git tag -a rea/<module-id>/<version-or-short-sha> <commit> -F <message-file>`.
   Message line 1 is one of:
   - `PASS`: every promise is Match.
   - `FAIL <n> bugs #<issue>`: `n` Bug suspect verdicts; `#<issue>` is the single or parent Issue.
   - `PARTIAL <n> #<issue>`: no Bug suspect, but `n` promises Different, Partial or Not checked.

   Line 2 is the report folder path, relative to the repository root.
3. Push the tag alone: `git push <remote> refs/tags/<tag>`.
4. Run `npm run verify:status` and commit the regenerated `docs/verification/README.md` in the same
   PR as the report folder.
5. **Required:** update the status board, the GitHub Project named in `docs/verification/project.json`
   (one row per module), with `npm run verify:project`. The owner checks that board, not the Issues
   list, to see what was verified, at which commit, and how far live has moved since. A run that
   skips it is lost to the owner. The `rea-status-project.sh` hook runs it after a tag push. Still
   run it yourself, and read its last line: `N cells updated`. If it fails (for example, `gh` lacks
   the `project` scope), write `BLOCKED: verify:project <reason>` in the report and tell the owner.

Done when the tag is on the remote, every bug Issue carries `rea-verify`, the report PR holds the
regenerated status README, and the Project row for the module shows the new tag and verdict.
