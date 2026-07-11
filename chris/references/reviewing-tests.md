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
5. Verify CRITICAL/HIGH findings by showing the current code and a failure path.
6. Recommend `KEEP`, `REWRITE`, `DOWNGRADE`, `REMOVE`, or `ADD` with reason.

Report verdict, evidence, risk, smallest fix, and tests to add/remove. Do not use
HTML or numeric scores.
