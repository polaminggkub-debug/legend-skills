# Debugging tests

Reproduce with the narrowest command. Separate product failure, stale
expectation, isolation leak, timing/race, environment/config, and flaky external
dependency. Fix the cause, rerun the focused test, then the affected suite.
Do not hide failures with retries, sleeps, or weakened assertions.
