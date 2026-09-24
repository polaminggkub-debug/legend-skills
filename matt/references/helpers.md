# Helper selection

Read only the row matching the current decision. Matt's authorization and the
project's requirements govern the work; selecting a helper grants no additional
authority. Resolve a named skill through the runtime catalog or installed skill
directories and read it before use. Reading instructions is sufficient to apply
them when no dedicated skill-invocation tool exists.

| Need | Helper or action |
|---|---|
| Product requirements needing structured questions | `$grill-with-docs` in a repository, `$grill-me` elsewhere; `$grilling` for an explicitly requested intensive interview |
| External technical uncertainty or repeated expensive exploration | `$research` against primary sources |
| Unsettled interaction, state model, or integration design | `$prototype` for a bounded experiment; verify existing behavior directly when that is the actual question |
| An effort too large to plan coherently in one session | `$wayfinder` |
| Settled decisions needing a buildable spec/plan | `$to-spec`, compatible with the chosen spec system |
| Multiple assignable outcomes needing tracker items | `$to-tickets` only if compatible with the selected tracker; otherwise use its actual CLI/API and accepted plan |
| Implementation of an accepted bounded change | `$implement` only if compatible with the actual spec/tracker and Chris's test policy; otherwise implement directly within that contract |
| Acceptance, tests, TDD, coverage, or CI guardrails | `$chris`; its internal TDD guide owns the test-first loop in this workflow |
| A hard bug without a tight reproduction | `$diagnosing-bugs`, with Chris governing test scope and evidence |
| A completed diff needing Standards and Spec review | `$code-review`; supply the accepted task/spec and review base |
| An in-progress merge/rebase conflict | `$resolving-merge-conflicts` |
| Unclear module boundaries or architecture health | `$improve-codebase-architecture`, supported by `$codebase-design` |
| Domain vocabulary or a durable architecture decision | `$domain-modeling` |
| Raw incoming requests needing disposition | `$triage` |
| Human-only credentials, dashboard access, or provisioning | `$wizard` only for the human-only part |
| Unfinished work crossing a real session/worker boundary | `$handoff` |
| A question owned by another person | `$to-questionnaire`; drafting does not authorize sending |
| Communication that did not land | `$wait-what` |
| Multi-session learning | `$teach` |
| Agent-facing instructions or skill design | `$writing-for-agents` and the available skill-creation workflow |
| Explicit tracker/bootstrap setup | `$setup-matt-pocock-skills` if compatible with the selected systems |
| The upstream course or rationale itself | `$ask-matt` or the relevant section of [course summary](course-summary.md) |

## Compatibility and missing helpers

Check the selected helper, not all installed skills. A customized `$to-tickets`
may require Beads; `$implement` may require OpenSpec or prescribe a full suite.
Do not change the user's tracker, spec, or Chris's Full E2E policy to satisfy a
helper. State the mismatch briefly and perform the equivalent authorized step
with compatible tools when its requirements are known. Preserve helper files.
If a necessary capability or policy is missing, block that dependent action and
name the missing requirement; discovery can still continue.

For Matt's testing work use Chris rather than the separately installed upstream
`$tdd`. The lock retains the original suite for installation compatibility; it
does not mandate executing every helper or following two TDD policies.

## Decomposition and handoff

Split by an outcome with its own owner/check, not merely by files. Record each
slice's scope, AC, prerequisite contract, check, and integration obligation.
Hierarchy describes containment; dependencies describe what must exist first.
For Projects use [its workflow](github-projects.md); otherwise use the selected
tracker's convention. With no tracker, keep work items in the accepted plan.

Give a shared interface one owner before parallel implementation; independent
branches do not prove compatibility. Keep verifier authorship away from the
implementer it judges.
Transfer source pointers, revision/working changes, observed results, remaining
findings and decisions, authority limits, and the next checkable action in the
existing task record rather than creating a competing tracker.

## Natural-language requests

- **“Build Search; handle it.”** Inspect existing search/data permissions and the
  accepted behavior. Resolve material product choices; otherwise establish AC
  with Chris and implement/verify a bounded slice. Do not invent ranking rules
  or ask the user to pick a skill.
- **“What should I do next?”** Inspect current task/diff/results and identify the
  unmet condition. Complete the advice; continue execution only if the existing
  task authorization calls for it. Do not reset a partly completed workflow.
- **“Tests pass; finish it.”** Check what ran on which revision, review findings,
  the delivery target, and existing authority. Resolve missing evidence; complete
  authorized delivery without treating a green check as acceptance by itself.

The [course summary](course-summary.md) explains historical teaching material.
Consult its relevant section for a requested explanation, not every routing
decision. Its examples of human checkpoints and session resets are not additional
mandatory stages in the current Matt workflow.
