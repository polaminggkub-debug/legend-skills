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
