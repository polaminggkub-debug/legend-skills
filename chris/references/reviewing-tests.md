# Reviewing and auditing tests

## Review lenses

- **Validity:** would the test fail when the promised behavior breaks?
- **Architecture:** does it exercise a clear unit or boundary contract?
- **Value:** does it protect a meaningful risk without duplicating another test?
- **Reliability:** can time, order, shared state, network, or retries change it?
- **Speed:** is expensive setup/UI traversal justified at this test level?
- **Coverage gap:** which source behaviors have no test at any level?

## Audit workflow

1. Manifest in-scope source, tests, config, fixtures, and CI files.
2. Inventory externally observable source behaviors before reading coverage.
3. Map tests to unit/boundary specs; mark each file `REVIEWED`, `FINDING`,
   `SKIPPED — reason`, or `COVERAGE GAP`.
4. Flag circular tests, weak existence-only assertions, implementation coupling,
   fake integration through mocks, arbitrary sleeps/retries, shared mutable data,
   and repeated E2E coverage.
5. Verify CRITICAL/HIGH findings with `file:line`, evidence, failure scenario,
   impact, verification, and confidence (`CONFIRMED`, `LIKELY`, or `NEEDS REVIEW`).
6. Recommend `KEEP`, `REWRITE`, `DOWNGRADE`, `REMOVE`, or `ADD` with reason.

Report verdict, evidence, risk, smallest fix, and tests to add/remove. Do not use
HTML or numeric scores.

## Review closure and acceptance

Use one focused analysis; add an independent pass for deep or high-risk work.
Treat a finding as a claim to verify against the current code and agreed contract.
Resolve it as valid, invalid with evidence, or deferred with explicit remaining
risk. For a valid finding, connect the correction to a rerun of the affected
check. An "addressed" comment or a changed line alone does not establish closure.

When asked whether to accept the work, use
[Acceptance and evidence](acceptance-evidence.md) to connect important criteria
to the actual revision and results. Inspect changes to verification policy via
[Guardrails and CI](guardrails-and-ci.md) when the diff changes enforcement.

For a defect that escaped review, identify which check or observation missed it.
Add or repair the smallest regression test or guardrail that would expose it;
change shared instructions only when the failure demonstrates a reusable gap.
