# Reviewing and auditing tests

## Review lenses

- **Validity:** would the test fail when the promised behavior breaks?
- **Architecture:** does it exercise a clear unit or boundary contract?
- **Value:** does it protect a meaningful risk without duplicating another test?
- **Reliability:** can time, order, shared state, network, or retries change it?
  Read the flaky outcomes of the measured run; new specs need a burn-in per
  [Playwright](playwright.md#flaky-tests).
- **Speed:** judged from the measured run of [Test speed](test-speed.md)
  step 1 (wall-clock, workers, machine, slowest tests, per-file totals). Each
  overhead and repetition suspect from steps 2–3 is named and costed.
- **Coverage gap:** which source behaviors have no test at any level?

Every review states its measured run time. Without a measured run, Speed is
`NOT MEASURED`, config-level suspects are listed as unconfirmed, and the
verdict is at most `CONDITIONAL PASS` on that condition.

## Audit workflow

1. Manifest in-scope source, tests, config, fixtures, and CI files.
2. Measure: list the in-scope selection and run it once with timing reporters
   ([Test speed](test-speed.md) step 1).
3. Inventory externally observable source behaviors before reading coverage.
4. Map tests to unit/boundary specs; mark each file `REVIEWED`, `FINDING`,
   `SKIPPED — reason`, or `COVERAGE GAP`.
5. Flag circular tests, weak existence-only assertions, implementation coupling,
   fake integration through mocks, arbitrary sleeps/retries, shared mutable data,
   and repetition: one flow walked at several viewports or from several entry
   paths, review-round files that repeat earlier tests, and E2E twins of
   unit-proven behavior.
6. Verify CRITICAL/HIGH findings with `file:line`, evidence, failure scenario,
   impact, verification, and confidence (`CONFIRMED`, `LIKELY`, or `NEEDS REVIEW`).
7. Recommend `KEEP`, `REWRITE`, `DOWNGRADE`, `REMOVE`, or `ADD` with reason.

Report the verdict, evidence, measured run time, risk, smallest fix, and tests
to add or remove.

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
