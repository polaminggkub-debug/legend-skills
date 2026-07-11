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

| Request | Read first | Deliver |
|---|---|---|
| new feature/fix | `references/tdd.md` | failing test, minimal implementation, verified test |
| write tests/test strategy | `references/writing-tests.md` | test plan or tests |
| improve testability | `references/testable-architecture.md` | unit map and refactor seam |
| failed/flaky test | `references/debugging-tests.md` | reproduced cause and verified repair |
| review/audit tests | `references/reviewing-tests.md` | concise Markdown review/audit |
| CI, fixtures, coverage, performance | `references/test-infrastructure.md` | smallest reliable configuration |

## Non-negotiables

1. State each unit's input/output spec before testing it.
2. Test pure logic in isolation. Test I/O at boundaries with controlled data.
3. Keep UI/orchestrator tests thin; use E2E/contract tests only for critical flows.
4. Happy path first, then a distinct edge/error risk. Assert user-visible or
   spec-derived values, never implementation details.
5. No circular tests: seed input -> execute system -> assert independently
   derived expectation.
6. Tests are readable AAA sequences; avoid test control flow and hidden logic.
7. Run the narrowest relevant test before and after a change; expand only when
   risk or dependencies justify it.

## Audit policy

Default: one focused analysis plus mandatory verification of every CRITICAL/HIGH
finding. Add an independent pass only for deep or high-risk work; do not ask
for a pass count by default. For very large targets, state the estimate first.

Every CRITICAL/HIGH finding needs: `file:line`, code/config evidence, a failure
scenario, impact, and verification. Mark confidence `CONFIRMED`, `LIKELY`, or
`NEEDS REVIEW`.

## Output

Use Markdown. Reviews/audits use `PASS`, `CONDITIONAL PASS`, or `FAIL`, then
findings ordered `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. Include skipped coverage
and why; never invent a numeric quality score.

## Constraints

Detect the project's test runner, package manager, OS, and commands. Use only
documented project commands. Never assume Bash, `python3`, a home-directory
path, a framework, or a database is available.
