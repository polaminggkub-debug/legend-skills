# Playwright E2E research, 2026-10

Collected 2026-10-10 (Asia/Bangkok) to make the Chris skill demand fast,
measured suites. Playwright was at v1.64.0 (released 2026-10-07). Version tags
such as "1.57+" in the skill mark the release that added a feature.

Doc findings cite the published page and its source file, pinned. Project
findings cite files pinned to the commits below. "Carried by" names the skill
file that now holds the rule: `SKILL` = SKILL.md, `speed` =
references/test-speed.md, `pw` = references/playwright.md, `review` =
references/reviewing-tests.md, `guard` = references/guardrails-and-ci.md,
`E1`–`E6` = cases in references/cases/e2e-at-scale.md.

## Pinned revisions

| Source | Commit |
|---|---|
| microsoft/playwright (docs and its own tests) | `b79c59928e2766873b22af5997b219b34fed1352` |
| grafana/grafana | `f88eb8d3f50f765adf42e802282ef20096b7fbe4` |
| calcom/cal.com | `54343aa685ae8f33159d2f485ec4a57bad5c574a` |
| n8n-io/n8n | `feed158ba2274d360b84cfdb93e85e619a8e795d` |
| element-hq/element-web | `795a9315b7034d2402f8d70b2c61f4a4207e4626` |
| immich-app/immich | `b4f35cb43d74969af0cfa146676eb26df9fcfd8c` |
| supabase/supabase | `eeae6027d5dc658932c6bd496a8c13e0277b7fdb` |
| playwright-community/eslint-plugin-playwright (v2.12.1, 2026-10-05) | `e3eaf6c0a6ec468f9073c33d46da0774ccb213dd` |
| sveltejs/cli | `7bbb1c36dd92a649216a239963841240f3eff710` |

## Project lessons (the owner's suite, 2026-10)

| # | Lesson | Carried by |
|---|---|---|
| O1 | Video and trace were recorded for every test; `retain-on-failure` still records every run. | speed §2 Recording; E1; eval 1 |
| O2 | Each test ran at 2–5 viewport sizes. | speed §3 One browser and one screen; pw walkthrough ban on `setViewportSize`; eval 1 |
| O3 | Every flow was walked twice, through two entry paths. | speed §3 One entry path; review audit step 5; eval 1 |
| O4 | Tests hit the Vite dev server instead of the built app. | speed §2 Server; E2; eval 1 |
| O5 | One feature grew to 15 spec files and 44 tests, one new file per review round. | speed §3 One spec file, §7 Guard; review step 5; E6 |
| O6 | A spec filter also matched the worktree directory name and silently ran the whole suite. | speed §1.1; pw Select tests; eval 2 |
| O7 | Worker count was guessed, never measured; a 96-thread server was no faster than a laptop. | speed §5 Workers by measurement; E3; eval 2 |
| O8 | A review missed every speed cause; its only speed line asked whether setup was justified. | review (measured run, verdict cap); SKILL route rows and Evaluate step; evals 1–2 |
| O9 | The walkthrough lint bans (sleeps, retries and `toPass`, force, page scripting, CSS selectors, every test asserts) lived only in one project's ESLint config. | pw Acceptance walkthroughs; eval 3 |
| O10 | Speed stopgap of 2026-10-09: recording off, built app, deep links, one viewport, one entry path, one file per feature, push logic down, measured workers, guards. | speed (rewritten and kept) |

## Playwright documentation

| # | Finding | Source | Carried by |
|---|---|---|---|
| D1 | Trace and video modes: `on`, `retain-on-failure`, and `retain-on-failure-and-retries` record every run; `on-first-retry` records only the first retry; recording is off by default. | [Recording options](https://playwright.dev/docs/test-use-options#recording-options), [source](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-use-options-js.md#L125-L206) | speed §2; E1 |
| D2 | Trace `on` is "performance heavy"; CI traces belong on the first retry; `retain-on-failure` "Record[s] a trace for each test". | [Trace viewer](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/trace-viewer.md#L90-L128), [best practices](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/best-practices-js.md#L281-L287) | speed §2; E1 |
| D3 | `--trace <mode>` forces a tracing mode for one run. | [CLI](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-cli-js.md#L114) | speed §2; pw Flaky tests |
| D4 | `workers` defaults to half the logical cores; it also accepts a percentage. | [TestConfig.workers](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L831-L837) | speed §5; E3 |
| D5 | CI docs recommend one worker for stability and sharding for wider parallelism. | [CI: workers](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/ci.md#L48-L60) | E3 |
| D6 | Always set `globalTimeout` in CI: without it a suite that "slowly grows past the job limit" is killed and produces no report. | [CI: global timeout](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/ci.md#L62-L78), [TestConfig.globalTimeout](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L202-L214) | speed §7 |
| D7 | `--only-changed` runs changed test files and test files that import changed files; it is a heuristic, so the full suite still runs. Added in 1.46. | [CI: fail-fast](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/ci.md#L421-L427), [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L1638-L1647) | speed §6; pw Select tests; E4 |
| D8 | By default only files run in parallel; `fullyParallel` also parallelizes tests inside a file. | [Parallelism](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-parallel-js.md#L8-L14) | speed §5 |
| D9 | Serial mode is "not recommended"; a serial group is retried together. | [Parallelism: serial](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-parallel-js.md#L94-L101) | pw Isolate |
| D10 | Test locks (`lock`, 1.63) serialize only the tests that share a named resource. | [Parallelism: locks](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-parallel-js.md#L128-L160), [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L190-L203) | pw Isolate |
| D11 | Parallel tests need their own backend data; one dataset per worker through a worker-scoped fixture keyed by worker index. | [Parallelism: shared state](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-parallel-js.md#L181-L208), [worker isolation](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-parallel-js.md#L256-L290), [fixtures](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-fixtures-js.md#L351-L357) | pw Isolate |
| D12 | `maxFailures` / `-x` stop a broken run early. | [Parallelism: fail fast](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-parallel-js.md#L228-L245), [TestConfig.maxFailures](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L270-L282) | speed §6 |
| D13 | With `fullyParallel` shards balance by test, without it by file; blob reports merge with `merge-reports`. | [Sharding](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-sharding-js.md#L30-L70) | speed §5; E3 |
| D14 | A test that fails and then passes on retry is "flaky"; such a run exits 0 unless `--fail-on-flaky-tests` (1.45) or `failOnFlakyTests` (1.52) is set. | [Retries](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-retries-js.md#L81-L96), [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L1738), [TestConfig.failOnFlakyTests](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L113-L126) | pw Flaky tests; E5 |
| D15 | `forbidOnly` fails a run that contains `.only`. | [TestConfig.forbidOnly](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L131-L143) | pw Flaky tests |
| D16 | `reportSlowTests` reports slow files, defaulting to a 5-minute per-file threshold and 5 files. | [TestConfig.reportSlowTests](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L475-L493) | speed §7 |
| D17 | Defaults: test timeout 30 s, expect timeout 5 s, action and navigation timeouts unlimited. | [Timeouts](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-timeouts-js.md#L8-L11), [advanced](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-timeouts-js.md#L154-L162) | speed §2 Waiting |
| D18 | `reuseExistingServer: true` reuses whatever already serves the URL; `!process.env.CI` is the usual setting. | [Web server](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-webserver-js.md#L39) | speed §2 Server; E2 |
| D19 | Playwright runs every project by default; `default: false` (1.64) keeps a project configured but unselected; `TestProject.workers` (1.52) limits one project's workers. | [Projects](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-projects-js.md#L65-L67), [release notes 1.64](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L74-L95), [release notes 1.52](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L1217-L1218) | speed §3; pw Isolate |
| D20 | Project dependencies are the recommended setup mechanism (report, trace, fixtures); filters select primary tests and dependencies still run; `--no-deps` skips them. | [Global setup](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-global-setup-teardown-js.md#L8-L16), [Projects: filtering](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-projects-js.md#L219-L223) | pw Select tests (confirm with `--list`) |
| D21 | Reusing authenticated state "speeds up test execution"; a setup project for read-only tests, one account per worker for tests that change server state; redoing login slows tests. | [Auth](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/auth.md#L8), [shared account](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/auth.md#L37-L40), [per worker](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/auth.md#L132-L135), [login cost](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/auth.md#L264-L266) | speed §2 Setup; pw Isolate |
| D22 | API requests prepare server state before a browser test. | [API testing](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/api-testing-js.md#L14-L15) | speed §2 Setup |
| D23 | A file argument is "a regular expression matched against the full test file path"; `--list`, `--test-list` (1.56), `-g`, `--pass-with-no-tests`, `--repeat-each`, `--shuffle` (1.64), `--last-failed` (1.44). | [CLI](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-cli-js.md#L81-L114), [test list](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-cli-js.md#L123-L158) | speed §1, §6; pw Select tests, Flaky tests |
| D24 | Tags (`{ tag: '@slow' }`) select subsets with `--grep` / `--grep-invert`. | [Annotations: tags](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-annotations-js.md#L68-L153) | speed §6; pw Select tests |
| D25 | The HTML report's Speedboard tab sorts tests by slowness (1.57) and shows a timeline for merged reports (1.58). | [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L905-L955) | speed §1 |
| D26 | The Perfetto reporter (1.63) draws the run as a timeline with one lane per worker. | [Reporters: Perfetto](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-reporters-js.md#L490-L515), [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L292) | speed §1 |
| D27 | The JSON reporter writes to a file named by `PLAYWRIGHT_JSON_OUTPUT_NAME`. | [Reporters: JSON](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-reporters-js.md#L409-L417) | speed §1 |
| D28 | Best practices: test user-visible behaviour; isolate tests; prefer user-facing locators to CSS/XPath; use web-first assertions, since manual assertions do not wait; lint with `no-floating-promises` and run `tsc --noEmit`; mock third parties the team does not control. | [Best practices](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/best-practices-js.md#L12-L60), [locators](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/best-practices-js.md#L91-L106), [assertions](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/best-practices-js.md#L162-L189), [lint](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/best-practices-js.md#L500-L503) | pw Write, Acceptance walkthroughs |
| D29 | CSS and XPath locators are "not recommended"; `first()`, `last()`, `nth()` are not recommended. | [Locators](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/locators.md#L76), [CSS/XPath](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/locators.md#L697), [nth](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/locators.md#L1781) | pw Write, walkthrough table |
| D30 | Actions wait until the element is stable, "not animating or completed animation"; `reducedMotion` became a standalone option in 1.63. | [Actionability](https://playwright.dev/docs/actionability#stable), [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L281) | speed §2 Waiting |
| D31 | Screenshot rendering varies by OS, browser, settings, hardware, and headless mode; baselines need the same environment. | [Snapshots](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-snapshots-js.md#L20) | pw Screenshot comparison |
| D32 | The healer agent "automatically repairs failing tests" and outputs a passing test "or a skipped test if the healer believes that functionality is broken". | [Test agents](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-agents-js.md#L194-L213), [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L1030-L1052) | pw Test agents |
| D33 | `npx playwright trace` explores traces from the command line for agents (1.59). | [release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L798-L826) | pw Flaky tests |

## Large projects

| # | Finding | Source | Carried by |
|---|---|---|---|
| P1 | Playwright's own library suite: video and trace only via `PWTEST_VIDEO`/`PWTEST_TRACE`; test timeout doubles when video is on; CI retries 3; `forbidOnly`; `globalTimeout` 2 h; `maxFailures` 200. | [config](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/tests/library/playwright.config.ts#L38-L106) | E1; E5 |
| P2 | Playwright's CI skips doc-only paths and weights shards with the undocumented `PWTEST_SHARD_WEIGHTS`. | [workflow](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/.github/workflows/tests_primary.yml#L9-L15) | context for E4; weights not carried |
| G1 | Grafana: `fullyParallel`, CI retries 1, CI workers 4, `retain-on-failure` traces, failure screenshots, auth setup project with `storageState`. | [config](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/playwright.config.ts#L10-L47) | E1; E3; E5 |
| G2 | Grafana: one Playwright project per feature folder; two projects that toggle one fixture are serialized through `dependencies`. | [config](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/playwright.config.ts#L59-L226) | context for pw Isolate |
| G3 | Grafana: E2E runs only when change detection reports relevant changes, always on main; 8 shards, `fail-fast: false`, 20-minute jobs. | [workflow](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L17-L37), [shards](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L143-L153) | speed §6 Tiers; E3; E4 |
| G4 | Grafana: tests a "standalone prod-ish Grafana distribution"; rebuilds small test plugins per shard because it is quicker. | [workflow](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L165-L169) | speed §2 Server; E2 |
| G5 | Grafana: shards upload blob reports; a merged JSON report feeds a benchmark job that records durations. | [run](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L236-L263), [bench](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L338-L380) | speed §7 (durations over time) |
| G6 | Grafana alerting guide: under `fullyParallel`, `beforeAll` runs once per worker; prefer `beforeEach`; serial only for unavoidable shared state; names unique per invocation (`randomUUID`), not `testInfo.testId`; cleanup by deleting one parent folder. | [guide](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/e2e-playwright/alerting-suite/AGENTS.md#L10-L50) | speed §5; pw Isolate |
| G7 | Grafana alerting guide: CLI file filters also filtered its setup project, which then produced no storage state. | [guide](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/e2e-playwright/alerting-suite/AGENTS.md#L104-L127) | pw Select tests (confirm with `--list`); see Conflicts |
| G8 | Grafana alerting guide: SQLite pool limits cause flakes under sustained parallel writes. | [guide](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/e2e-playwright/alerting-suite/AGENTS.md#L129-L135) | speed §5 (server saturates first) |
| G9 | Grafana dashboard guide: the test owns the assertion; no speculative page-object methods; no waits or retries in page objects; burn in with `--repeat-each=3`. | [guide](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/e2e-playwright/dashboard-new-layouts/AGENTS.md#L127-L163) | pw Write, Flaky tests; E6 |
| G10 | Grafana style guide: no stubs or mocks, to simulate a real user; page objects; `data-testid` selectors. | [guide](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/contribute/style-guides/e2e-playwright.md#L5-L18) | pw Acceptance walkthroughs (real app) |
| C1 | cal.com: the local dev server "can be slow to start up and process requests"; CI action and navigation timeouts of 10 s to "fail fast". | [config](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/playwright.config.ts#L13-L22), [timeouts](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/playwright.config.ts#L84-L87) | speed §2 Server, Waiting; E2 |
| C2 | cal.com: `webServer` runs `next start` on a cached production build; E2E jobs depend on the build job. | [config](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/playwright.config.ts#L30-L40), [start](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/apps/web/package.json#L22), [cache](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/actions/cache-build/action.yml#L1-L24), [needs](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/pr.yml#L375-L378) | speed §2 Server; E2 |
| C3 | cal.com: `forbidOnly`, CI retries 2, `maxFailures` 10 headless, `fullyParallel`, blob reporter on CI, `retain-on-failure` traces. | [config](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/playwright.config.ts#L94-L115) | speed §6 Fail fast; E1; E5 |
| C4 | cal.com: 8 shards × 4 workers, 20-minute jobs, cached database and build. | [workflow](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/e2e.yml#L44-L101) | E3 |
| C5 | cal.com: docs-only changes skip E2E; E2E needs a `ready-for-e2e` label; a skipped E2E leaves the required check failing. | [filters](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/pr.yml#L190-L205), [label](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/pr.yml#L227-L286), [rule](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/agents/rules/testing-playwright.md#L27-L37) | E4 |
| N1 | n8n: local workers capped at 6 because "higher causes instability in the local server"; all cores on CI. | [config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/playwright.config.ts#L39-L45) | speed §5; E3 |
| N2 | n8n: trace, video, and screenshot `on`; CI retries 2; `forbidOnly`; one MacBook-sized viewport. | [config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/playwright.config.ts#L16), [run policy](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/playwright.config.ts#L118-L144) | E1; E5; speed §3 (one screen) |
| N3 | n8n: shards packed by measured per-spec duration; ~3.4 minutes fixed setup per shard caps the count at total time ÷ 5 minutes; 196 minutes over 20 shards; stale durations unbalanced shards (9.7 predicted, 8.6–18.5 actual). | [orchestration](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/docs/ORCHESTRATION.md#L1-L48), [metrics](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/docs/ORCHESTRATION.md#L147-L168) | speed §5; E3 |
| N4 | n8n: a CI re-run executes only the specs that failed, failing open; `test.fixme` specs leave CI distribution. | [orchestration](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/docs/ORCHESTRATION.md#L114-L146) | speed §6 Reruns; pw Flaky tests; E5 |
| N5 | n8n: coverage impact map selects affected specs and "only narrows" (unmapped → directory specs; missing or stale → all). | [impact map](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/scripts/impact-map.md#L1-L113) | speed §6; E4 |
| N6 | n8n: `eslint-plugin-playwright` `flat/recommended` plus `no-conditional-in-test` as error. | [eslint config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/eslint.config.mjs#L6-L37) | pw Acceptance walkthroughs |
| N7 | n8n janitor: flags selector duplication, copy-pasted tests across files, dead page-object methods, orphaned data; a baseline fails only new violations and its commit tool refuses baseline edits. | [config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/janitor.config.mjs#L54-L74), [README](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/janitor/README.md#L5-L16), [baseline](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/janitor/README.md#L124-L152), [duplicate-logic](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/janitor/README.md#L600-L610) | speed §7; guard (baseline); E6 |
| N8 | n8n: quarantine by title from a central list, failing open. | [fixture](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/fixtures/quarantine.ts#L49-L65) | pw Flaky tests; E5 |
| N9 | n8n guide: create data through API helpers, `nanoid()` names, assert by identity rather than count; review checklist bans `waitForTimeout`. | [AGENTS.md](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/AGENTS.md#L14-L20), [checklist](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/CONTRIBUTING.md#L497-L511) | pw Isolate; walkthrough table |
| E-1 | Element: CI serves the built `webapp`; workers 1; CI retries 2 with `retryStrategy: 'isolated'`; `maxFailures` 10; traces on first retry; failing videos kept; one viewport; screenshots compared only in Chrome (`ignoreSnapshots`). | [config](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/apps/web/playwright.config.ts#L36-L110) | E1; E2; E3; E5; pw Screenshot comparison |
| E-2 | Element: PRs run Chrome only and skip `@mergequeue` ("Slow or flaky tests covering rarely-updated app areas"); merge queue and nightly run every project; a label forces all. | [docs](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/docs/playwright.md#L81-L91), [tags](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/docs/playwright.md#L393-L416), [workflow](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/.github/workflows/build-and-test.yaml#L135-L182) | speed §3, §6 Tiers; E4 |
| E-3 | Element: builds once and uploads the app; 4 runners on PRs, 1 on the nightly full run. | [workflow](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/.github/workflows/build-and-test.yaml#L49-L50), [upload](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/.github/workflows/build-and-test.yaml#L95-L104) | E2; E3 |
| E-4 | Element: set up state through REST APIs and drive the UI only for the behaviour under test; avoid explicit waits; screenshot baselines only in a Linux Docker environment, tagged `@screenshot`. | [practices](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/docs/playwright.md#L239-L320), [screenshots](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/docs/playwright.md#L322-L391) | speed §2 Setup; pw Screenshot comparison |
| E-5 | Element: a reporter files or updates a `Z-Flaky-Test` GitHub issue for each flaky outcome; crashes are recorded as app faults. | [reporter](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/packages/playwright-common/src/flaky-reporter.ts#L9-L120) | pw Flaky tests; E5 |
| I1 | Immich: real-server specs run with 1 worker, network-mocked UI specs fully parallel with 3 CI workers; CI retries 4; traces on first retry. | [config](https://github.com/immich-app/immich/blob/b4f35cb43d74969af0cfa146676eb26df9fcfd8c/e2e/playwright.config.ts#L16-L54) | pw Isolate (stateful project `workers: 1`); E5 |
| I2 | Immich: Docker Compose stack started with `--wait` before tests; installs only `chromium --only-shell`; path filters and an aggregate success job. | [workflow](https://github.com/immich-app/immich/blob/b4f35cb43d74969af0cfa146676eb26df9fcfd8c/.github/workflows/test.yml#L586-L600), [aggregate](https://github.com/immich-app/immich/blob/b4f35cb43d74969af0cfa146676eb26df9fcfd8c/.github/workflows/test.yml#L649-L659) | not carried (CI setup detail) |
| S1 | Supabase Studio: CI retries 5, `maxFailures` 3, 3 workers (1 against the rate-limited platform), `retain-on-failure` video and trace, screenshots off, `reducedMotion: 'reduce'`, setup project with `storageState`. | [config](https://github.com/supabase/supabase/blob/eeae6027d5dc658932c6bd496a8c13e0277b7fdb/e2e/studio/playwright.config.ts#L46-L148) | speed §2 Waiting; E5 |
| S2 | Supabase Studio: builds Studio, then runs Playwright against that build in 2 shards. | [workflow](https://github.com/supabase/supabase/blob/eeae6027d5dc658932c6bd496a8c13e0277b7fdb/.github/workflows/studio-e2e-test.yml#L15-L22), [build and run](https://github.com/supabase/supabase/blob/eeae6027d5dc658932c6bd496a8c13e0277b7fdb/.github/workflows/studio-e2e-test.yml#L123-L135) | speed §2 Server; E2 |

## Other primary sources

| # | Finding | Source | Carried by |
|---|---|---|---|
| X1 | Next.js recommends running Playwright "against your production code to more closely resemble how your application will behave" (docs v16.4.0, updated 2026-09-28). | [Next.js guide](https://nextjs.org/docs/app/guides/testing/playwright) | speed §2 Server; E2 |
| X2 | The SvelteKit Playwright add-on's config runs `npm run build && npm run preview`. | [sv add-on config](https://github.com/sveltejs/cli/blob/7bbb1c36dd92a649216a239963841240f3eff710/packages/sv/src/cli/tests/snapshots/create-with-all-addons/playwright.config.ts#L4) | speed §2 Server; E2 |
| X3 | Vite's dev server "transforms each file as it's requested". | [Vite: why](https://vite.dev/guide/why) | speed §2 Server; E2 |
| X4 | eslint-plugin-playwright `flat/recommended` (v2.12.1) sets `no-wait-for-timeout`, `no-force-option`, `no-eval`, `no-conditional-in-test`, `expect-expect`, `no-skipped-test` to `warn`, and `no-focused-test`, `prefer-web-first-assertions`, `missing-playwright-await` to `error`. | [plugin.ts](https://github.com/playwright-community/eslint-plugin-playwright/blob/e3eaf6c0a6ec468f9073c33d46da0774ccb213dd/src/plugin.ts#L146-L182) | pw Acceptance walkthroughs |
| X5 | Opt-in plugin rules: `no-raw-locators`, `no-restricted-matchers`, `no-nth-methods`; `require-to-pass-timeout` exists because `toPass` defaults to timeout 0 and retries until the test timeout. | [rule docs](https://github.com/playwright-community/eslint-plugin-playwright/tree/e3eaf6c0a6ec468f9073c33d46da0774ccb213dd/docs/rules), [require-to-pass-timeout](https://github.com/playwright-community/eslint-plugin-playwright/blob/e3eaf6c0a6ec468f9073c33d46da0774ccb213dd/docs/rules/require-to-pass-timeout.md) | pw walkthrough enforcement; speed §2 Waiting |

## Secondary sources (reported by a research helper, not verified, not carried)

- Rippling on duration-based batching and changed-file tagging: https://rippling.com/blog/revisiting-end-to-end-testing
- Grafana on measuring flakiness by rerunning one commit: https://grafana.com/blog/2023/02/09/how-we-reduced-flaky-tests-using-grafana-prometheus-grafana-loki-and-drone-ci
- Currents customer story on n8n's migration: https://currents.dev/posts/currents-and-n8n
- PayPay's Cypress-to-Playwright migration: https://blog.paypay.ne.jp/en/modernising-e2e-testing-by-migrating-from-cypress-to-playwright/
- Playwright Test Agents walkthrough by a Playwright team member: https://dev.to/playwright/playwright-agents-planner-generator-and-healer-in-action-5ajh

## Conflicts and open questions

1. **Filters and setup projects.** Playwright's docs say location filters select
   primary tests and dependency projects still run (D20); Grafana reports file
   filters skipping its setup project (G7). The skill states only the
   checkable part: confirm the selection, setup projects included, with
   `--list`.
2. **Unique data ids.** Playwright's docs derive ids from `testInfo.testId`
   (D11); Grafana rejects `testId` because it is stable across runs and leaves
   orphans (G6). The skill uses an id unique to the run.
3. **CI workers.** Playwright recommends 1 (D5); projects use 1 (Element),
   4 (Grafana, cal.com), or every core (n8n). The skill requires measuring.
4. **Recording.** n8n records everything; Grafana, cal.com, and Supabase keep
   failures; Element and Immich record first retries; Playwright's own suite
   records nothing by default. The skill keeps recording off by default (O1)
   and asks for a measured A/B (E1).
5. **Retries.** CI retries range from 1 to 5. The skill allows retries only
   with a record (`failOnFlakyTests` or a tracked issue) and keeps acceptance
   walkthroughs at 0.
6. **`toPass`.** Grafana keeps `toPass()` in specs for timing-sensitive
   mechanics (G9); acceptance walkthroughs ban it (O9); other suites give it an
   explicit timeout (X5).

## Not included, and why

- `PWTEST_SHARD_WEIGHTS` (P2, Supabase S2): undocumented internal variable that
  can change without notice.
- n8n's custom shard orchestrator and fixture-pool grouping: needs a duration
  store and many worker configurations; the underlying rules (measured
  durations, setup-cost cap) are carried.
- cal.com's 80% coverage rule: conflicts with Chris's stance that coverage is a
  navigation signal, not proof.
- `retryStrategy: 'isolated'`, `Reporter.preprocess`, WebMCP, screencast video
  receipts, and the 1.62 component-testing model: marginal for speed and
  reliability here.
- Supabase's long list of Chrome launch flags: unmeasured micro-tuning.
- Browser caching and `--only-shell` installs (I2, S2): CI setup details;
  Playwright advises against caching browsers.
- `webServer` readiness endpoints (n8n) and Docker `--wait` (I2): reliability
  details outside this speed-focused pass.
- Vendor and secondary posts: not primary, not verified.
