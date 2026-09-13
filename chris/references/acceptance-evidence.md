# Acceptance and evidence

Read when deriving acceptance criteria, selecting checks, or assessing whether
a change meets its requirements. Scale the record to the task: a short change
may need one sentence; several independent criteria may warrant a table.

## Define the observable promise

An acceptance criterion states behavior under a condition. A verification
method describes how to check it. Evidence records what actually happened.
A completion condition states what must be true before accepting the task.

Derive criteria from the agreed request/specification. Identify material unknowns
without silently adding business rules, platforms, concurrency guarantees, or
performance targets. Continue independent work while resolving those unknowns.

For each important criterion, identify its input/state, observable outcome,
relevant boundary, and a plausible wrong implementation that the check should
reject. If the wrong implementation still passes, strengthen the observation
or choose a better boundary. Coverage and assertion counts cannot answer this.

## Choose the smallest check that observes the promise

| Promise | Usually useful verification | What this alone cannot establish |
|---|---|---|
| Import direction, forbidden API, static type constraint | Lint, dependency rule, compiler | Runtime authorization or persisted behavior |
| Calculation or state transition without I/O | Unit test with independent expected values | Database/provider semantics |
| Persistence, transaction, authorization, adapter behavior | Integration at the actual responsible boundary | Entire user journey across other boundaries |
| Compatibility between producer and consumer | Contract check against the agreed interface | Unchecked end-to-end side effects |
| Critical interaction spanning browser and services | Targeted E2E with meaningful outcomes | Every workflow or full-suite coverage |
| Visual or usability criterion | Rendered inspection or a focused interaction | Backend correctness |

Inspect the implementation and existing tests before choosing. Add evidence
where a distinct risk is uncovered; reuse sufficient existing checks. Calling
mocked internals an integration test does not establish the real boundary.
For static constraints, use [Guardrails and CI](guardrails-and-ci.md).

## Example: retry without duplicate creation

Given an agreed sequential retry contract for the same request ID:

- Both calls return the same record ID.
- Independent observation at the persistence boundary shows exactly one new
  record for that request ID.

A test asserting equal return values can miss duplicate writes. Use controlled
storage at the responsible service/database boundary to observe both promises.
This does not establish concurrent retries, payload-conflict behavior, or an
idempotency retention window; include those only when the requirements need them.

## Connect criteria to actual evidence

For consequential acceptance decisions, record enough to reproduce or inspect:

`criterion -> boundary -> revision -> command/action -> assertion -> result -> limits`

Identify the tested commit or working-tree state, relevant environment, and
whether a result was personally run or retrieved from a source. A proposed test
is `PLANNED`; an unexecuted test is `NOT RUN`; missing relevant provenance is
`UNVERIFIED`; an observed outcome is `PASS` or `FAIL`. A skipped check supplies
no behavioral observation, even if the host permits its status for merging.

After relevant edits, determine which earlier evidence is invalidated and rerun
the affected checks. Compare PR-head, base, and synthetic merge revisions when
the CI event makes that distinction matter. Keep unaffected evidence when its
applicability is established; do not require a full rerun for unrelated edits.

## Acceptance recommendation

- `PASS`: the agreed criteria and required checks have sufficient applicable
  evidence, with no unresolved blocking finding.
- `CONDITIONAL PASS`: state the exact unresolved condition or limitation. Pending
  required evidence means acceptance is still pending; this label does not waive it.
- `FAIL`: a criterion is violated or a required check fails; explain the failure
  and the smallest next verification or correction.

Repository merge eligibility is a separate observed fact. Successful CI does not
by itself prove acceptance or authorize a merge. Follow existing authorization
and the repository's required checks; apply the Full E2E policy in
[Chris](../SKILL.md#release-test-decisions).

For questions about real examples of incomplete evidence, read the matching
entry in the [case index](cases/index.md).
