# TDD

1. Name the behavior and observable contract.
2. Write the smallest failing happy-path test.
3. Implement only enough to pass.
4. Refactor without changing the contract.
5. Add an edge/error test only for a distinct, valuable risk.

If a test needs complicated setup, first create an explicit seam or a focused
fixture. Never fake an integration test with assertions against mocked internals.

When the promise includes persistence or other side effects beyond a return
value, use [Acceptance and evidence](acceptance-evidence.md) to choose the
observable boundary before writing the test. For a static architectural rule,
use [Guardrails and CI](guardrails-and-ci.md) to select and demonstrate the
checker instead of forcing the constraint into a runtime unit test.
