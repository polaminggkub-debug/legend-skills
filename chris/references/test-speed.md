# Test speed

A slow suite gets skipped, and a skipped suite proves nothing. Treat run time
as a defect with a measured cause. Reading config and code finds *suspects*; a
measured run ranks them and proves each gain. Work the steps in order.
Selection, isolation, and flake mechanics live in [Playwright](playwright.md).

## 1. Measure

1. List the selection before timing it (`npx playwright test --list`, or the
   runner's equivalent) and check the test count per project and file. A file
   filter is a regular expression over the full path, so a short pattern can
   match a directory name and select the whole suite.
2. Run that selection once, as CI runs it, with timing reporters:
   `PLAYWRIGHT_JSON_OUTPUT_NAME=results.json npx playwright test --reporter=list,html,json,perfetto`
   (Vitest: `--reporter=json`). The HTML report's Speedboard tab ranks tests
   by duration (1.57+). The Perfetto timeline (1.63+) draws one lane per
   worker; idle gaps are lost parallelism.
3. Record wall-clock, test count, workers, server start-up time, and the
   machine (CPU threads, load average).

Done when the 20 slowest tests, the per-file totals, and those run facts are
written down for the machine you will compare on.

## 2. Per-test overhead

Every test pays overhead, so it multiplies. Name each suspect, then cost it
with one run with it and one without:

- **Recording**: trace and video modes `on` and `retain-on-failure` record
  every run; `retain-on-failure` only deletes the passing files. Normal runs
  keep trace, video, and failure screenshots `off`, or `on-first-retry` where
  CI retries. Record on demand: rerun a failure with `--trace on`, or record a
  review run the owner asked for.
- **Server**: tests hit the production build (`build && preview`, or the
  framework's `start`), built once and shared by every worker and shard. A dev
  server transforms each module when the browser requests it. A reused server
  (`reuseExistingServer`) keeps serving its old build, so rebuild after source
  changes.
- **Setup**: sign in once in a setup project and load its `storageState`.
  Create test data through the API; drive the UI only for the behaviour under
  test.
- **Navigation**: open the state under test directly (deep link or seeded
  state). Replay a long flow only in the one test that owns that flow.
- **Waiting**: every wait ends on a condition. Set `actionTimeout` and
  `navigationTimeout` (both unlimited by default) to about 10–15 s, so a
  missing control fails fast; give any `toPass` an explicit `timeout`. When
  motion is not the criterion and the app honours it, `reducedMotion: 'reduce'`
  shortens the wait for animated elements to settle before each action.

Done when each suspect is either costed by a with/without run or cleared.

## 3. Repetition

The same check run twice costs twice and catches nothing new:

- **One browser and one screen per change run**: Playwright runs every project
  (browser, device, viewport) by default, and each one repeats its tests; a
  viewport loop inside a spec repeats them the same way. Per-change runs use
  the product's primary browser and screen, set once in the config; other
  projects run at a later tier (step 6) or stay in the config with
  `default: false` (1.64+). A second viewport earns its place only when the
  requirement is responsive layout.
- **One entry path per flow**: a second entry path gets a small test of just
  its difference.
- **One spec file per feature**: review rounds edit that file, and a superseded
  round's tests are deleted.

Done when every repeated walk is removed or traced to a requirement that needs
it.

## 4. Push logic down

Pure logic (state, maths, mapping) gets unit tests that run in milliseconds.
Iterate on those, and run E2E once the unit tests are green. A behaviour proven
by a unit test keeps only that cheaper test; E2E covers what needs a rendered
screen or a real boundary.

Done when each remaining E2E test names what only the rendered screen or a
real boundary can show.

## 5. Parallelism

- **Independent tests**: set `fullyParallel: true` and split a long serial
  test into independent tests. Under `fullyParallel`, `beforeAll` repeats in
  every worker that runs the file's tests, so per-test state lives in
  `beforeEach` or a fixture.
- **Workers by measurement**: Playwright defaults to half the logical cores.
  Time 2–3 worker counts on the target machine and keep the fastest that adds
  no timeouts. The app server or database often saturates before the CPU does.
- **Shards when one machine is full**: with `fullyParallel`, shards balance by
  test; without it, by file. Reuse one build across shards and merge their
  blob reports. Each shard pays fixed setup, so cap the count at
  `total test time ÷ target shard time`, and rebalance from fresh durations.

Done when the chosen worker and shard counts each cite a timed comparison.

## 6. Run less

- **Per change**: run the affected specs, each with its reason. Impact
  selection only narrows: an unknown file or a stale map selects more tests.
  `--only-changed` is a quick first pass, never the whole gate.
- **Tiers**: per-change runs cover the core project and untagged tests; the
  gate the project names runs other projects and tagged slow tests
  (`--grep`, `--grep-invert`), within the
  [release policy](../SKILL.md#release-test-decisions).
- **Reruns**: run only the failures (`--last-failed`), then one clean pass of
  the affected specs.
- **Fail fast**: set `maxFailures` on CI so a broken build stops early.

Done when each per-change selection states its reason and the full run's gate
is named.

## 7. Guard

Guard a fix whose cost would grow back unnoticed, and keep the guard tight
([Guards inside an agent's loop](guardrails-and-ci.md#guards-inside-an-agents-loop)):

- lint bans on cost multipliers: fixed sleeps, unbounded `toPass`, viewport
  resizing inside tests ([Playwright](playwright.md#acceptance-walkthroughs));
- a check that allows one spec file per feature, plus duplicate-test detection;
- `reportSlowTests` set to the project's per-file threshold (default 5 minutes);
- `globalTimeout` on CI below the job limit, so a growing suite stops with a
  report instead of being killed;
- per-file durations kept from each CI run and compared over time.

Done when each guarded fix has a guard shown to fail on its violation, and the report
gives before and after wall-clock on the same machine at similar load. For
precedents from large projects, read the [case index](cases/index.md).
