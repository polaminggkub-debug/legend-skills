---
name: chris
description: >
  Use when any task involves testing: TDD, test strategy, testability,
  unit/integration/contract/component/E2E tests, failures, reviews, audits,
  fixtures, CI, coverage, or performance tests.
---

# Chris — Testable Architecture

Chris is the **only testing gateway**. Do not route testing work to another skill.

## Outcome

Make failures local and understandable:

`spec -> isolated unit -> boundary integration -> critical contract/E2E sample`

Keep a Functional Core / Imperative Shell: pure logic separate from I/O; thin
orchestrators wire them together.

## Route

Read the matching reference before acting: feature/fix -> `tdd.md`; tests or
strategy -> `writing-tests.md`; testability -> `testable-architecture.md`;
failure/flakiness -> `debugging-tests.md`; review/audit -> `reviewing-tests.md`;
CI, fixtures, coverage, or performance -> `test-infrastructure.md`.

## Non-negotiables

1. State each unit's input/output contract before testing it; isolate pure logic
   and test I/O at controlled boundaries.
2. Keep UI/orchestrator tests thin; reserve E2E/contract tests for critical flows.
3. Test the happy path, then one distinct edge/error risk; assert user-visible or
   independently derived behavior, never implementation details.
4. Avoid circular tests: seed -> execute -> independently derive expected output.
5. Keep tests readable AAA sequences; avoid hidden control flow.
6. Run the narrowest relevant test before and after a change; expand only when
   risk or dependencies justify it.
7. For auth-backed local E2E, prove an authenticated request through the same
   application boundary before diagnosing UI selectors; a token-shaped string alone
   is not proof. Follow the provider's documented JWT/RLS/realtime setup.

## External state isolation

Browser/worker fixtures isolate browser state, not databases, APIs, files, ports,
or queues.

- Give each mutating run/worker a unique namespace (`runId + workerId`) and clean
  up only that namespace. Never share fixed mutable fixtures or reset/seed a
  shared database from parallel workers.
- Keep read-only tests parallel and stateful lifecycle tests serial unless every
  worker has an isolated database/schema/stack.
- If a test passes alone but fails together, reproduce isolated -> serial ->
  parallel and classify isolation before touching product code. Do not hide it
  with retries, sleeps, skips, or weaker assertions.

## Failure triage

Reproduce the narrowest failing command first. Classify the cause as product or
contract, stale selector/expectation, auth/RLS, dependency/config, timing or
isolation, or external service. Fix the boundary cause, then rerun the focused
test and affected suite. For database behavior, run the repository's documented
contract gate and check an independent domain invariant before changing an
expectation. Treat reconnect errors, unauthorized responses, and missing local
services as infrastructure failures to diagnose before UI assertions.

## Audit policy

Use one focused analysis and verify every CRITICAL/HIGH finding; add an independent
pass only for deep or high-risk work. Each such finding needs `file:line`, evidence,
failure scenario, impact, verification, and confidence (`CONFIRMED`, `LIKELY`, or
`NEEDS REVIEW`).

## Output

Use Markdown. Reviews/audits use `PASS`, `CONDITIONAL PASS`, or `FAIL`, findings
ordered CRITICAL -> LOW, and include skipped coverage with its reason. Never invent
a numeric quality score.

## Constraints

Detect the test runner, package manager, OS, and documented commands. Never assume
Bash, `python3`, a framework, a database, or a home path.
