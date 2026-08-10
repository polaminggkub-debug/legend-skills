# Test infrastructure

## Determinism

Control clocks, randomness, IDs, locale, timezone, seeds, fixtures, and cleanup.
Give each test isolated data. Avoid order dependencies and shared mutable state.
Use local/ephemeral dependencies where practical; keep secrets out of output.

## Boundary and UI tests

Use contract tests at service boundaries. For browser tests, prefer semantic
role/label selectors, condition-based waiting, direct API/DB setup, and explicit
state cleanup. Never use fixed sleeps to hide races. Keep E2E to critical user
journeys and assert meaningful values, not visibility alone.

## CI, coverage, and performance

Use project-documented commands and reproduce CI locally when possible. Record
runtime and flaky retries. Treat coverage percentages as a navigation signal,
not proof; map uncovered important behavior instead. Performance tests need a
stable environment, defined workload, warmup policy, baseline, threshold, and
actionable failure output.

## Release decisions

When a repository defines a release test contract, run its affected tests and
fixed critical gate in the documented order. Keep critical selections explicit
and small; do not replace an allowlist with a broad project or suite selector.

Full E2E requires explicit semantic user intent for the complete suite. A
generic request to ship, test, or run tests does not authorize it. Equivalent
wording in another language can authorize it when the meaning clearly requests
the complete suite. Risk signals and stale or unknown status never authorize an
automatic run. Report status read-only, and record a new successful result only
after that explicitly authorized suite succeeds.
