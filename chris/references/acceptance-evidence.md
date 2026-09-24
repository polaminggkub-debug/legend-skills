# Acceptance and evidence

Read when deriving acceptance criteria, selecting checks, or judging whether a
change meets its requirements. Keep the record short: one sentence for a small
change, a short checklist for several criteria. Apply Chris's
[hard rules](../SKILL.md#hard-rules) first.

## Define the observable promise

An acceptance criterion states behavior under a condition. Derive it from the
owner's current request or plan, not from older documents the owner has not
reconfirmed. Name material unknowns instead of silently adding business rules,
platforms, concurrency guarantees, or performance targets.

For each important criterion, name its input/state, observable outcome,
boundary, and a plausible wrong implementation the check must reject. If the
wrong implementation still passes, strengthen the observation or move to a
better boundary. Coverage and assertion counts cannot answer this.

## Choose the smallest check that observes the promise

| Promise | Usually useful verification | What this alone cannot establish |
|---|---|---|
| Import direction, forbidden API, static type constraint | Lint, dependency rule, compiler | Runtime authorization or persisted behavior |
| Calculation or state transition without I/O | Unit test with independent expected values | Database/provider semantics |
| Persistence, transaction, authorization, adapter behavior | Integration at the actual responsible boundary | Entire user journey across other boundaries |
| Compatibility between producer and consumer | Contract check against the agreed interface | Unchecked end-to-end side effects |
| Critical interaction spanning browser and services | Targeted E2E with meaningful outcomes | Every workflow or full-suite coverage |
| Visual, usability, or demo criterion | Rendered walkthrough with a screenshot per criterion, reviewed by the owner | Backend correctness |

Source, text, or label presence never proves a rendered or behavioral promise:
a name printed in a `<div>` does not show that a screen focuses that item.
Reuse sufficient existing checks. Calling mocked internals an integration test
does not establish the real boundary. For static constraints, use
[Guardrails and CI](guardrails-and-ci.md).

## Example: retry without duplicate creation

Given an agreed sequential retry contract for the same request ID, both calls
return the same record ID, and the persistence boundary shows exactly one new
record. A test asserting equal return values can miss duplicate writes, so
observe storage at the responsible boundary. This does not establish concurrent
retries or payload conflicts; add those only when the requirements need them.

## Evidence

State what ran, on which revision, and the result; say what it does not prove.
A skipped or unexecuted check supplies no behavioral observation. After edits,
rerun the affected checks; keep unaffected evidence only when it still applies.

## Review verdict

- `PASS`: agreed criteria have applicable evidence and no blocking finding.
- `CONDITIONAL PASS`: name the exact unresolved condition; it waives nothing.
- `FAIL`: a criterion is violated or a required check fails; give the smallest
  next correction or verification.

A verdict is a recommendation. Acceptance is the owner's decision, and green CI
neither proves acceptance nor authorizes a merge. Apply the Full E2E policy in
[Chris](../SKILL.md#release-test-decisions). For real examples of incomplete
evidence, read the matching entry in the [case index](cases/index.md).
