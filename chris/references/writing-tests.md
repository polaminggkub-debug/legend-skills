# Writing tests

## Testing invariants

1. Keep a Functional Core / Imperative Shell: test pure logic directly and I/O
   at controlled boundaries.
2. Keep UI/orchestrator tests thin; reserve E2E/contract tests for critical flows.
3. Test the happy path, then distinct edge/error risks. Assert observable or
   independently derived behavior; avoid circular tests and implementation coupling.
4. Keep tests readable Arrange, Act, Assert sequences without hidden control flow.
5. Run the narrowest relevant test before and after a change; expand only when
   risk justifies it, within the
   [release policy](../SKILL.md#release-test-decisions).

## Shape of a test

Name `[unit] — [scenario] — [expected result]`. Seed only the inputs needed;
calculate expected values independently. Prefer public contracts and
accessible user interactions. State why each E2E test is worth its runtime and
maintenance cost. Browser tests follow [Playwright](playwright.md).
