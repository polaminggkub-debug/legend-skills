# Debugging tests

Reproduce the narrowest failing command first. Classify the cause as product or
contract, stale selector/expectation, auth/RLS, dependency/config, timing or
isolation, or external service. Fix the boundary cause, then rerun the focused
test and affected suite. Do not hide failures with retries, sleeps, skips, or
weakened assertions.

For database behavior, run the repository's documented contract gate and check
an independent domain invariant before changing an expectation. Treat reconnect
errors, unauthorized responses, and missing local services as infrastructure
failures to diagnose before UI assertions.

## Authentication boundary

For auth-backed local E2E, prove an authenticated request through the same
application boundary before diagnosing selectors; a token-shaped string alone
is not proof. Follow the provider's documented JWT/RLS/realtime setup.

## Isolation

If a test passes alone but fails together, read
[External state isolation](test-infrastructure.md#external-state-isolation)
before changing product code.
