# Context discovery

Use this reference to resolve the knowledge needed for Matt's next transition. It applies across trackers and repositories. The workflow is a synthesis from public artifacts, not a reconstruction of hidden agent searches. Matt's task record and authorization rules govern implementation and other downstream actions.

## Assess what is already known

Start from the active task, agreed outcome/scope, current workspace/revision, and available context. A task boundary and a session boundary are separate: a new task can reuse applicable knowledge, while the same task can need new context after code, requirements, or evidence changes.

Check relevance and freshness before searching. Carry forward sources that still apply; refresh the specific path, contract, or result affected by a change. Having read a reference earlier does not establish that repository facts are still current. A new session or worker should verify its handoff against the actual checkout and current task.

Identify the unanswered question that changes the next action. Discoverable facts call for a targeted read or bounded investigation; an unresolved product/authority decision calls for the appropriate human decision after available evidence is inspected. Use Matt's diagnosis routes for the resulting action. Context sufficiency can justify implementation within existing task authorization; it does not establish acceptance or grant additional permission.

## Discover only what answers the question

Follow this route as needed, starting at the first gap rather than repeating completed discovery:

1. **Task and applicable instructions.** Read the accepted request/spec/AC and the instructions that apply to the workspace and affected paths under the active runtime's rules. Follow conditional pointers for the module or operation being considered. A file's existence does not prove an agent received it; distinguish instructions already supplied from pointers still needing inspection. Use the repository's actual layout, not mandatory filenames invented by this reference.
2. **Entry point and implementation.** Search filenames, symbols, error text, routes, or test names before reading bodies. Trace the smallest path from the triggering input through state/data ownership to the observable result. Expand to callers or consumers where that path crosses a shared boundary.
3. **Analogue and contract.** Inspect a comparable implementation for the same responsibility, then verify why its behavior applies here. Check relevant types/schema, architecture decisions, code comments, API contracts for the installed version, and producer/consumer behavior. Similar appearance alone does not justify copying an analogue.
4. **Verification.** Find the check that would distinguish a wrong implementation from the requested behavior. Read its assertions, fixtures, mocks, and execution path; a nearby test may cover a different function or lifecycle. Use the repository's current commands and identify missing integration/runtime coverage.
5. **Sufficiency.** Decide whether the evidence supports the next bounded action using the conditions below. Broaden discovery only where a material question remains.

Use `rg --files` and scoped `rg` searches when available. A repository-wide symbol inventory can locate affected consumers without loading every file body. For an empty search, try the repository's vocabulary or adjacent callers before concluding a path does not exist. For truncated results, retrieve the missing relevant section and record any remaining coverage gap.

Treat sources by their role: the accepted task describes intended behavior, code describes current behavior, tests prove only the behavior their execution observes, and comments/docs describe constraints with an applicability/version context. When these disagree, establish which revision and contract each describes; use a bounded reproduction to settle factual behavior and surface unresolved requirement choices. Preserve material uncertainty rather than silently making one source authoritative for every question.

## Decide when context is sufficient

For a bounded implementation, be able to point to:

- the requested observable change and its scope;
- the likely change location and the execution/data path it affects;
- the invariants and relevant consumers that must remain compatible;
- a verification method that can expose the targeted wrong behavior;
- a disposition for unknowns that could change the design, shared contract, or acceptance.

Scale these conditions to the change: a local wording fix needs much less discovery than a persistence migration. Already evidenced answers need no new reading. Stop searching when the next action is supported and further reading would not change its scope or verification; repository completeness is not the criterion.

When material facts remain unknown, name the narrow question and the next source or experiment likely to answer it. A diagnostic reproduction or exploratory test may begin before implementation is justified. Apply Matt's boundaries to any resulting design/API/scope decision. If relevant accessible sources are exhausted, report what is still unknown and what would unblock it instead of continuing undirected searches or guessing.

## Adjust the route to the task

| Task | Context that usually determines the next action | Signal to discover more |
|---|---|---|
| Bug fix | Reproduction/version, failing path, state owner, callers, behavior contract, regression check | Reproduction differs, ownership is unclear, or the proposed test misses the symptom |
| Feature | Outcome, architecture boundary, existing analogue, API/data contract, end-to-end consumer | A new dependency or consumer appears, or the built feature fails the user journey |
| Refactor/migration | Preserved invariants, old/new representations, writers/readers, stored data, failure and compatibility paths | A reader/exporter is omitted, legacy data fails, or a fixture changes the test's meaning |
| UI | Observed state, component/routing, established primitives, data flow, applicable keyboard/loading/error/lifecycle behavior | Click and keyboard differ, reconnect exposes a different path, or a previously untested state appears |
| Cross-module change | Trigger-to-consumer path, shared interfaces and owners, lifecycle/concurrency, integration check | A new persistence/process boundary or incompatible consumer appears |

Use a row to choose relevant questions, not to mandate every listed activity for every task.

## Reopen discovery from feedback

Turn a finding or failed check into: **challenged assumption → source to inspect → observation that would settle it**. Verify the finding against the current candidate before prescribing a fix; keep claims about earlier revisions separate.

- A green unit test with a failing journey calls for inspection of the runtime path and what the test mocks out.
- A mount test with a reconnect bug calls for the reconnect lifecycle, subscriptions, and persisted state.
- A new storage envelope breaking export calls for the exporter and legacy readers, not just the writer's new type.
- An API error after a version change calls for that installed version's signatures and actual call site.

Return to the affected step of discovery. New context can reveal either an in-scope fix or a separate decision/follow-up; apply the task's existing scope and review policy rather than expanding the change automatically. After a change, refresh affected verification at the resulting revision.

## Keep discovery transferable

Delegate independent questions or module investigations when they can proceed without conflicting ownership. Give each investigator a bounded question and the relevant task/revision pointers. Request conclusions with source locations, applicable contracts, and unresolved questions; do not substitute another agent's confidence for inspectable evidence.

At a handoff, add the discovery state to the existing task/handoff record: what is known and where it was verified, material assumptions, uninspected or truncated context, and the next question/action. Include revision and relevant uncommitted changes so the receiver can determine what still applies. Reuse the configured tracker's handoff format when one exists rather than creating a second report.

Distinguish observed artifacts/results, someone else's report, reasonable inference, and unknown information where that distinction affects the decision. A summary saying "all tests pass" without a command/result/revision is a report to verify. Without session logs, file-read order and private prompt contents remain unknown; commits, repository instructions, and merge events cannot fill those gaps.

Keep context through pointers to authoritative task/spec and repository sources. Load details on demand and preserve enough evidence to revisit a decision. Session resets, compaction, and subagent dispatch depend on the actual runtime and task; reading this reference does not perform them or monitor future work.

## Basis

These examples support specific observations; the route and stopping conditions above are proposed practice, not observed internal stopping rules or a measured token-saving claim.

- **Direct artifact/report:** [Dyad review points to the existing deployment analogue](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709212241), followed by [a reply reporting additional contract findings](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547) and [a concrete fix](https://github.com/dyad-sh/dyad/commit/43110685df945df319bf0cea53030707f2ffbf26). This motivates analogue and consumer discovery; the implementer's earlier read order is unknown.
- **Direct review artifact:** [Roo's migration review identifies an export reader that still parses the old representation](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794507746). This motivates inventorying consumers beyond the main execution path; it does not establish why the implementer missed the issue.
- **Published trace:** [Aider's complex-change example](https://aider.chat/examples/complex-change.html) shows added file/API context and revisions after feedback. It is an older, selected transcript with user-provided context, not a complete trace of an autonomous large-repository workflow.
