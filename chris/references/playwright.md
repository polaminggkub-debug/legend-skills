# Playwright

Rules for writing, selecting, isolating, and trusting Playwright tests. Speed
settings (recording, server, workers, shards, projects) live in
[Test speed](test-speed.md).

## Write

- Locate like a user: `getByRole`, `getByLabel`, `getByText`, and
  `getByTestId` as an explicit contract. Scope a locator to the region that
  owns the element.
- Assert with retrying web-first assertions (`toBeVisible`, `toHaveText`,
  `toHaveValue`, `toHaveURL`). A one-shot read such as `isVisible()` checks
  once and does not wait.
- The test owns its assertions. Page objects and fixtures return locators and
  perform actions; waits, retries, and assertions stay in the spec.
- Lint with `@typescript-eslint/no-floating-promises` and run `tsc --noEmit`,
  so every Playwright call is awaited and typed.

## Acceptance walkthroughs

A walkthrough is the judge for a UI criterion: one fixed path that drives the
real app like a user and asserts what the user sees. Lint it so a pass means
the behaviour is true:

| Write this | Lint bans |
|---|---|
| Every test runs | `.only`, `.skip`, `.fixme` |
| One fixed path, read top to bottom | `if`, ternaries, or-fallbacks, loops, `try` in a test |
| Wait for a visible outcome with `expect` | `waitForTimeout`, `setTimeout`, `toPass` |
| Retrying assertions on what the user sees | one-shot reads (`isVisible()`, `textContent()`, `count()`), weak matchers (`toBeTruthy`, `toBeDefined`) |
| Role, label, text, or test-id locators | CSS-class, XPath, and DOM-structure selectors |
| Clicks a user can make | `force: true` |
| The real, unscripted app | `evaluate`, `$eval`, `addInitScript`, `exposeFunction`, `route`, `routeFromHAR` |
| The configured screen | `setViewportSize` in a test |
| Judgement from the rendered UI only | imports of app source |
| At least one `expect` per test | a test with no assertion |

Walkthroughs run with `retries: 0`: a miss must fail.

Enforce with `eslint-plugin-playwright` `flat/recommended` and raise these
rules to `error`: the preset ships `no-wait-for-timeout`, `no-force-option`,
`no-eval`, `no-conditional-in-test`, `expect-expect`, and `no-skipped-test` as
warnings, and warnings exit 0. Add `no-raw-locators` and
`no-restricted-matchers`. Cover what the plugin lacks (page scripting,
routing, viewport resizing, app-source imports) with `no-restricted-syntax`,
and prove each rule per
[Guardrails and CI](guardrails-and-ci.md#prove-the-rules-behavior).

Other E2E suites may route third-party services the team does not control.

## Select tests

- A file argument is a regular expression matched against the full file path.
  Select by exact path, a `--test-list` file (1.56+), or a title with `-g`,
  and confirm with `--list` that the test count and the setup projects are
  the ones intended.
- Tags (`test('…', { tag: '@slow' }, …)`) mark run tiers; select them with
  `--grep` and `--grep-invert`. A sharded run whose grep empties a shard needs
  `--pass-with-no-tests`.
- `--only-changed[=ref]` (1.46+) runs changed test files and the test files
  that import changed files; it is a heuristic first pass. `--last-failed`
  (1.44+) reruns the previous failures.

## Isolate

Each test gets its own browser context, so cookies and storage are already
isolated; flakes come from state outside the browser.

- **Sign-in**: authenticate once in a setup project and load its
  `storageState`. When tests change server-side state, give each worker its
  own account through a worker-scoped fixture keyed by `parallelIndex`.
- **Data**: create it through the API under a name unique to this run (a
  random id made in `beforeEach`), so parallel workers and leftovers from a
  crashed run cannot collide. Own it under one parent resource and delete
  that parent at the end.
- **Shared resources**: tests that touch one shared resource take the same
  `lock` (1.63+), so only they serialize; or a stateful project runs with
  `workers: 1` while other projects stay parallel. Serial mode is the last
  resort: it pins the file to one worker and retries the group together.

For databases, queues, and files, apply
[External state isolation](test-infrastructure.md#external-state-isolation).

## Flaky tests

A flaky test failed, then passed on retry. Keep every flake on the record:

- **Retries with a record**: a suite that retries on CI also fails on flakes
  (`failOnFlakyTests: !!process.env.CI`, 1.52+) or files a tracked issue for
  each flaky outcome from a reporter. Set `forbidOnly: !!process.env.CI`.
- **Quarantine** a known flake by title in one list with an owner and an
  issue. The list fails open (unavailable means every test runs) and stays
  short; `test.fixme` is the in-code form.
- **Burn in** each new or changed spec before it judges anything:
  `--repeat-each=3`, plus one `--shuffle` run (1.64+) to expose order
  dependence.
- **Diagnose from evidence**: rerun the failure with recording on
  (`--last-failed --trace on`; for a flake that passed on retry,
  `-g "<title>" --repeat-each=10 --trace retain-on-failure`), read the trace
  (`npx playwright trace` gives agents a CLI view, 1.59+), then fix the cause
  per [Debugging tests](debugging-tests.md).

## Screenshot comparison

Rendering varies with OS, browser version, fonts, and headless mode, so
`toHaveScreenshot` baselines are generated and compared in one pinned
environment (a Linux container) and one browser project
(`ignoreSnapshots: true` on the others). Tag screenshot tests (`@screenshot`)
so they run and update on their own.

## Test agents

Playwright's healer agent edits failing tests (locators, waits, data) or marks
them skipped. A healer edit to an approved verifier is a verifier change and
goes to the owner under [hard rule 5](../SKILL.md#hard-rules); a healed skip
is a coverage gap. Planner and generator output is a draft test: check it
against the acceptance criterion before it becomes a judge.

For how large projects apply these rules, read the [case index](cases/index.md).
