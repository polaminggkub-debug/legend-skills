# E2E at scale: precedents from large projects

### E1 — Recording is a measured choice (Playwright, n8n, Grafana, Element)

**Use when:** choosing trace, video, or screenshot settings, or a suite is slow on CPU.

**Observed facts**

- Trace and video modes `on` and `retain-on-failure` record every run; `retain-on-failure` keeps only failing runs ([mode tables](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-use-options-js.md#L155-L206)). The docs call trace `on` "very performance heavy" and set CI traces to the first retry ([best practices](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/best-practices-js.md#L281-L287)).
- Playwright's own library suite records video and trace only when `PWTEST_VIDEO`/`PWTEST_TRACE` is set, and doubles the test timeout when video is on ([config](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/tests/library/playwright.config.ts#L40-L66)).
- n8n records trace, video, and screenshot `on` for every test ([config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/playwright.config.ts#L133-L137)); Grafana keeps `retain-on-failure` traces ([config](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/playwright.config.ts#L35-L44)); Element records traces on the first retry and keeps failing videos ([config](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/apps/web/playwright.config.ts#L86-L92)).

**Decision and verification**

- Choose recording from an A/B run: same selection and machine, recording on versus off; record wall-clock and CPU load. Keep the cheapest mode whose failure evidence someone reads.
- With recording off, the debugging path is a rerun of the failure with `--trace on`.

**Solo adaptation (inference):** a laptop or shared server without a failure dashboard gains little from recording passing tests; keep recording off and rerun failures with it on.

**Limitations:** the projects' settings show chosen tradeoffs, not measured costs; n8n's CI budget and dashboard differ from a single machine.

### E2 — Test the production build, built once (cal.com, Grafana, Element, Supabase)

**Use when:** `webServer` starts a dev server, or each shard rebuilds the app.

**Observed facts**

- cal.com's config notes that the local dev server "can be slow to start up and process requests"; its E2E serves `next start` from a cached production build ([config](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/playwright.config.ts#L13-L40), [start script](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/apps/web/package.json#L22), [cache action](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/actions/cache-build/action.yml#L1-L24), [job needs build](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/pr.yml#L375-L378)).
- Element builds the web app once, uploads it, and serves the built `webapp` on CI; the dev server runs only locally ([workflow](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/.github/workflows/build-and-test.yaml#L95-L104), [config](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/apps/web/playwright.config.ts#L93-L99)). Supabase builds Studio, then runs Playwright "against local studio build" ([workflow](https://github.com/supabase/supabase/blob/eeae6027d5dc658932c6bd496a8c13e0277b7fdb/.github/workflows/studio-e2e-test.yml#L123-L135)).
- Grafana tests a "standalone prod-ish Grafana distribution" stitched from build artifacts, yet rebuilds its small test plugins in each shard because that is quicker than moving them ([workflow](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L165-L169)).
- Next.js recommends running Playwright "against your production code" ([guide](https://nextjs.org/docs/app/guides/testing/playwright)); the SvelteKit add-on's config runs `npm run build && npm run preview` ([config](https://github.com/sveltejs/cli/blob/7bbb1c36dd92a649216a239963841240f3eff710/packages/sv/src/cli/tests/snapshots/create-with-all-addons/playwright.config.ts#L4)). Vite's dev server "transforms each file as it's requested" ([Vite](https://vite.dev/guide/why)).

**Decision and verification**

- `webServer` builds and serves the production bundle. CI builds once and hands the artifact to every shard, unless a rebuild is measured faster than the transfer.
- Verify with server start-up time and per-test durations, dev versus built, on the same selection.

**Solo adaptation (inference):** `vite build && vite preview` (or the framework's `start`) in `webServer`. A reused server (`reuseExistingServer`) still serves its old build, so rebuild after source changes.

**Limitations:** dev-only behaviour (hot reload, dev warnings) is not exercised; keep a dev-mode smoke test if the project depends on it.

### E3 — Size workers and shards from measured durations (n8n, cal.com, Grafana, Element)

**Use when:** picking a worker count, adding shards, or shards finish unevenly.

**Observed facts**

- Playwright defaults to half the logical cores ([config docs](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L831-L837)) and recommends one CI worker for stability, with sharding for wider parallelism ([CI docs](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/ci.md#L48-L60)).
- n8n caps local workers at 6 because "higher causes instability in the local server" and uses every core on CI ([config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/playwright.config.ts#L39-L45)). cal.com runs 8 shards of 4 workers ([workflow](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/e2e.yml#L75-L94)); Grafana 8 shards with 4 CI workers ([config](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/playwright.config.ts#L24-L27), [workflow](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L143-L153)); Element 4 shards of 1 worker ([config](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/apps/web/playwright.config.ts#L102), [workflow](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/.github/workflows/build-and-test.yaml#L49-L50)).
- n8n packs shards by measured per-spec duration. Each shard pays about 3.4 minutes of fixed setup, so the shard count is capped at total test time ÷ a 5-minute target. A 3-month-stale duration file predicted 9.7-minute shards that took 8.6 to 18.5 minutes ([orchestration](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/docs/ORCHESTRATION.md#L18-L48), [stale metrics](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/docs/ORCHESTRATION.md#L160-L163)).
- Built-in sharding balances by test with `fullyParallel`, and by file without it ([sharding docs](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-sharding-js.md#L30-L47)).

**Decision and verification**

- Choose workers by timing 2–3 counts on the target machine; keep the fastest that adds no timeouts. Watch the app server and database: they often saturate first.
- Add shards only when one machine is full; cap them by fixed setup cost and rebalance from fresh durations.

**Solo adaptation (inference):** on one machine, time for example 2, 4, and 8 workers; stop where wall-clock stops falling or timeouts appear.

**Limitations:** n8n's packer and duration data are its own tooling; the worker counts reflect each project's runners and backends.

### E4 — Run tiers: core per change, the rest at the gate (Element, Grafana, cal.com, n8n)

**Use when:** every change runs everything, or someone proposes skipping E2E on some changes.

**Observed facts**

- Element PRs run Chrome only and skip `@mergequeue` tests ("Slow or flaky tests covering rarely-updated app areas"); the merge queue and nightly runs cover all browsers, and a label forces the full set ([docs](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/docs/playwright.md#L81-L91), [tags](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/docs/playwright.md#L393-L416), [workflow](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/.github/workflows/build-and-test.yaml#L135-L182)).
- Grafana runs E2E when change detection reports relevant changes, and always on main ([workflow](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/.github/workflows/pr-e2e-tests.yml#L17-L37)). cal.com skips docs-only changes and runs E2E on a `ready-for-e2e` label; a skipped E2E leaves the required check failing, so nothing merges without it ([filters](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/pr.yml#L190-L205), [label](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/.github/workflows/pr.yml#L227-L286), [rule](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/agents/rules/testing-playwright.md#L33-L37)).
- n8n selects affected specs from a coverage impact map that "only narrows": an unmapped file selects its directory's specs, and a missing or stale map selects all ([impact map](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/scripts/impact-map.md#L100-L113)).
- Playwright calls `--only-changed` a heuristic that "might miss tests" and runs the full suite after it ([CI docs](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/ci.md#L421-L427)).

**Decision and verification**

- Per-change runs: affected specs on the core project. Gate runs: the remaining projects and tagged slow tests. Selection by impact fails toward running more.
- A skipped required E2E job is a missing observation, never a pass.

**Solo adaptation (inference):** per change, run the affected specs; at the release gate, run what the project's release policy names (see [Chris](../../SKILL.md#release-test-decisions)).

**Limitations:** merge queues, labels, and required checks are repository settings that code alone does not establish.

### E5 — Retries that leave a record (Element, n8n, Playwright)

**Use when:** adding retries, seeing "flaky" in a report, or quarantining a test.

**Observed facts**

- CI retry counts vary: Grafana 1, cal.com, n8n, and Element 2, Playwright's own suite 3, Immich 4, Supabase Studio 5 ([Grafana](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/playwright.config.ts#L26), [cal.com](https://github.com/calcom/cal.com/blob/54343aa685ae8f33159d2f485ec4a57bad5c574a/playwright.config.ts#L96), [n8n](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/playwright.config.ts#L122), [Element](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/apps/web/playwright.config.ts#L103), [Playwright](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/tests/library/playwright.config.ts#L70), [Immich](https://github.com/immich-app/immich/blob/b4f35cb43d74969af0cfa146676eb26df9fcfd8c/e2e/playwright.config.ts#L21), [Supabase](https://github.com/supabase/supabase/blob/eeae6027d5dc658932c6bd496a8c13e0277b7fdb/e2e/studio/playwright.config.ts#L51)).
- Element's reporter files or updates a GitHub issue labelled `Z-Flaky-Test` for each flaky outcome, and records crashes as app faults rather than test flakes ([reporter](https://github.com/element-hq/element-web/blob/795a9315b7034d2402f8d70b2c61f4a4207e4626/packages/playwright-common/src/flaky-reporter.ts#L9-L53)).
- n8n skips tests named on a central quarantine list and fails open when the list is unavailable ([fixture](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/fixtures/quarantine.ts#L49-L65)); `test.fixme` specs leave CI distribution ([orchestration](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/docs/ORCHESTRATION.md#L114-L131)).
- By default a run whose failures recover on retry exits 0; `--fail-on-flaky-tests` (1.45) and `failOnFlakyTests` (1.52) make it fail ([release notes](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/release-notes-js.md#L1738), [config docs](https://github.com/microsoft/playwright/blob/b79c59928e2766873b22af5997b219b34fed1352/docs/src/test-api/class-testconfig.md#L113-L126)).

**Decision and verification**

- Retry only with a record: `failOnFlakyTests` on CI, or a reporter that opens a tracked issue per flake. Quarantine by name with an owner. Acceptance walkthroughs keep `retries: 0`.
- Verify the record: a deliberately flaky fixture test must fail the run or open its issue.

**Solo adaptation (inference):** with no issue bot, `failOnFlakyTests: !!process.env.CI` is the whole mechanism.

**Limitations:** issue filing needs a token and repository permission; whether a flake count blocks merging is a repository setting.

### E6 — Keep test code from growing (n8n, Grafana)

**Use when:** a suite grows by copy-paste, review rounds add files, or page objects bloat.

**Observed facts**

- n8n's janitor statically flags selector duplication, copy-pasted test bodies across files, unused page-object methods, and orphaned test data ([why](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/janitor/README.md#L5-L16), [duplicate-logic](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/janitor/README.md#L600-L610), [config](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/playwright/janitor.config.mjs#L54-L74)). A committed baseline fails only new violations, and its automated commit path refuses baseline edits ([baseline](https://github.com/n8n-io/n8n/blob/feed158ba2274d360b84cfdb93e85e619a8e795d/packages/quality/testing/janitor/README.md#L124-L152)).
- Grafana's agent guide: page objects get only methods a current spec needs, the test owns the assertion, page objects hold no waits or retries, and a changed spec is burned in with `--repeat-each=3` ([guide](https://github.com/grafana/grafana/blob/f88eb8d3f50f765adf42e802282ef20096b7fbe4/e2e-playwright/dashboard-new-layouts/AGENTS.md#L127-L163)).

**Decision and verification**

- One spec file per feature; a review round edits it and deletes superseded tests. A duplicate-test check with a baseline holds the line on existing debt.
- Verify a guard with one copied test body (fails) and one distinct test (passes).

**Solo adaptation (inference):** a short script that counts spec files per feature and fails above one covers most of the growth; adopt janitor-style duplicate detection when copies keep appearing.

**Limitations:** static detection finds copies, not two different tests that prove the same behaviour; that still needs review.
