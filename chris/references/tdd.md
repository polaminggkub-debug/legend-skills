# TDD

1. Name the behavior and observable contract.
2. Write the smallest failing happy-path test.
3. Implement only enough to pass.
4. Refactor without changing the contract.
5. Add an edge/error test only for a distinct, valuable risk.

If a test needs complicated setup, first create an explicit seam or a focused
fixture. Never fake an integration test with assertions against mocked internals.
