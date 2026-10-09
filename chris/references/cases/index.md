# Case index

Read these cases when the user requests examples or evidence from real projects,
or when comparing approaches whose tradeoffs a precedent can clarify. Choose
one relevant section; routine development does not require reading this library.

| Question | Read |
|---|---|
| Does configured lint actually fail the invoked command and CI? | [L1: VS Code and Ruff](lint-enforcement.md#l1--configuration-is-not-enforcement-vs-code--ruff) |
| How can generated files be checked against their source? | [L2: Kubernetes and Moby](lint-enforcement.md#l2--generated-output-is-a-source-of-truth-contract-kubernetes--moby) |
| When is custom semantic lint worth maintaining? | [L3: React and Next.js](lint-enforcement.md#l3--custom-semantic-lint-needs-a-real-domain-invariant-react--nextjs) |
| Does a test actually reproduce a fixed defect? | [A1: FastAPI](acceptance-and-review.md#a1--distinguish-regression-proof-from-additional-coverage-fastapi) |
| Why can source/manual success miss a broken delivered artifact? | [A2: Omarchy](acceptance-and-review.md#a2--test-the-shipped-artifact-through-its-real-consumer-omarchy) |
| How do we prove rejection happens before an expensive side effect? | [A3: Goose](acceptance-and-review.md#a3--put-the-guard-before-the-costly-side-effect-goose) |
| Should normal runs record trace, video, or screenshots? | [E1: Playwright, n8n, Grafana, Element](e2e-at-scale.md#e1--recording-is-a-measured-choice-playwright-n8n-grafana-element) |
| Dev server or production build; build once or per shard? | [E2: cal.com, Grafana, Element, Supabase](e2e-at-scale.md#e2--test-the-production-build-built-once-calcom-grafana-element-supabase) |
| How many workers and shards, and why are shards uneven? | [E3: n8n, cal.com, Grafana, Element](e2e-at-scale.md#e3--size-workers-and-shards-from-measured-durations-n8n-calcom-grafana-element) |
| What runs on every change, and what waits for the gate? | [E4: Element, Grafana, cal.com, n8n](e2e-at-scale.md#e4--run-tiers-core-per-change-the-rest-at-the-gate-element-grafana-calcom-n8n) |
| May CI retry flaky tests, and how is each flake tracked? | [E5: Element, n8n, Playwright](e2e-at-scale.md#e5--retries-that-leave-a-record-element-n8n-playwright) |
| How do large suites keep test code from growing? | [E6: n8n, Grafana](e2e-at-scale.md#e6--keep-test-code-from-growing-n8n-grafana) |

L and A cases were collected on **2026-09-13**, E cases on **2026-10-10**
(Asia/Bangkok); the research notes for E cases are in
[research/playwright-2026-10.md](../../research/playwright-2026-10.md). File links
pin commits; PR comments and runs describe the recorded event. Later PR status,
repository settings, and tool behavior can change. Branch-protection settings
were not established by these cases. Contributor reports are identified where
independent execution was not observed.

Use the local facts and adaptations to explain the recorded case without a new
search. For a current API/configuration question, a changed version, or a claim
these cases do not support, inspect the target repository and current primary
sources. Separate observed facts, adaptation, and remaining uncertainty. Explain
why the original constraint does or does not match the user's project. Cite the
linked primary sources when attributing behavior to a project.
