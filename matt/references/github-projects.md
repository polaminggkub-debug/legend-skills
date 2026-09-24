# GitHub Projects workflow

Use this reference when Matt routes work tracked with repository Issues and GitHub Projects. These are reusable conventions synthesized from public work and GitHub capabilities, not a claim that every cited team follows this protocol. Matt's task authorization, applicable repository policy, and runtime permissions govern actions here too.

Read the section needed for the next transition: **Repository mapping**, **Ready and decomposition**, **Assignment and handoff**, **Review and acceptance**, or **Automation and recovery**. Sources explain provenance and product behavior; load them when those facts need checking.

## Repository mapping

Read `docs/agents/issue-tracker.md` and its pointers. Use `docs/agents/matt-workflow.md` for the spec system and any linked acceptance/authority policy. Reuse existing configuration rather than creating another source of truth. For Projects setup, extend the repository's tracker configuration with:

- Repository and execution Project URL/owner/number; which Project controls dispatch if an Issue appears in several.
- Existing Status field and the meaning of its options; resolve API field/option/item IDs from the live Project when needed.
- Where the accepted spec and AC live, the delivery target, and who can accept, close, merge, or deploy.
- Pointers to verification commands/CI and any task-specific evidence requirements. Read commands from the repository's scripts rather than caching a second copy.
- Coordinator/worker assignment convention and any automation that changes Issue state or Project Status.

Only record facts that the workflow needs. Missing Project identity blocks Project writes, but independent authorized work can continue from a known Issue/spec. Discover linked Projects before asking; never choose an unrelated board or create one just because the global tracker says Projects. Installation alone does not change an existing tracker or spec choice.

| Artifact | Responsibility |
|---|---|
| Repository Issue | Stable task identity, outcome, scope, AC or links to canonical spec clauses, delivery target |
| Project item | Queue, ownership visibility, and current workflow state; retain its source Issue identity |
| Sub-issue | Part of a larger outcome with its own owner or checkable exit |
| Blocked by / Blocking | Prerequisite relationship, separate from parent/child hierarchy |
| Pull request | Implementation, code review, and fixes |
| Test/check/artifact | Evidence for named AC at a known revision/environment |
| Acceptance receipt | Decision record on the Issue linking evidence, remaining obligations, and acceptance authority |

Draft Project items can hold intake ideas. Convert to a repository Issue before dispatch when repository identity, relationships, or review linkage are needed. An existing canonical spec such as OpenSpec stays canonical: link its relevant clauses instead of maintaining duplicate requirements in the Issue.

## Ready and decomposition

Determine readiness from the task facts: bounded outcome and AC, known prerequisites satisfied, workable verification, and an available authorized owner. A Ready label or unblocked indicator alone does not establish those conditions.

Use existing Status names. For a new workflow, these five meanings are a starting point, not required custom fields:

| Meaning | Evidence for the state |
|---|---|
| Backlog | Outcome captured; scope, prerequisites, or verification still need resolution |
| Ready | The readiness conditions above hold |
| In progress | An identified worker owns an active bounded attempt |
| In review | Implementation and relevant verification are ready for required review/acceptance; record any outstanding delivery step |
| Done | The acceptance conditions below hold for this task's delivery target |

A blocker may occur at any stage: record the dependency or external decision, owner, and next unblock action without multiplying statuses. GitHub Issue open/closed and close reason are distinct from Project Status. Cancellation, duplicate, or not-planned disposition is not evidence of successful delivery; use the repository's terminal disposition and archive/filter policy.

Split when separate assignment, prerequisite ordering, or independent verification becomes useful. Prefer checkable outcomes; a file boundary alone does not justify another task. Keep a narrow cross-module change together when splitting would break its contract. For migrations, sequence compatibility expansion, independently safe batches, and removal; when intermediate changes cannot stand alone, name the integration branch/task and its final verification obligation.

Use sub-issues for containment and native dependencies for prerequisites. Parent completion requires its combined outcome and integration evidence, not only all children closed. Describe what each prerequisite must deliver; an auto-closed blocker may still leave the consumer's required contract unproven.

For approved task creation, create the Issues, capture their returned identities, then add hierarchy/dependencies and Project membership. Read back every declared relationship and the intended ready frontier. Use the installed CLI/API's current supported operations. Use `$to-tickets` with the discovered repository workflow and preserve the selected spec.

For a preparation-only request, finish the requested draft Issue payloads and dependency mapping from available facts before seeking execution approval. Leave missing facts explicit. Preparing a reviewable draft and writing it to GitHub are separate actions; a request to defer execution does not defer the authorized drafting work.

## Assignment and handoff

Parallelize only after identifying independent outcomes or edit ownership, stable interfaces, and an integration owner. Give a shared interface one owner or an explicit coordinated change plan. Separate worktrees isolate edits, but do not resolve contract disagreements. If two slices must land together, retain that integration obligation even when development runs in parallel.

Use one coordinator or an existing dispatch system to serialize claims for the execution queue. A normal assignee or Status update is not an atomic lease for local agents. Before launching, check current assignment and active sessions; record Issue, worker/run identity, branch/worktree, and scope. Reconcile an uncertain launch before retrying so duplicate processing does not start duplicate workers.

Treat assigning an enabled agent app as a possible execution trigger, not merely bookkeeping. Check the selected agent's actual capabilities and authorization before assigning it. Projects visibility alone does not establish that an agent was invoked or received context.

At a real handoff, send a compact packet through the receiving runtime's supported channel:

- Issue/spec/AC and bounded scope, including the shared contract and owner;
- branch/worktree and revision, changes completed, and current diff when uncommitted;
- verification command/result/artifact, failed or missing checks, and review findings;
- prerequisites, next action, stop condition, and remaining delivery/acceptance obligation.

Link reusable context instead of copying the whole repository or transcript. Confirm the receiving agent can access it. Posting an Issue comment is not proof of delivery to an active session: for example, Copilot cloud agent's issue-assignment flow uses the initial Issue context and directs later feedback to the PR. Check other agents' supported channels separately.

## Review and acceptance

Classify each actionable finding against the agreed AC/scope. Work necessary for the current AC stays in the same task through rework and relevant re-verification. An independent improvement may become a linked follow-up with an owner and reason for deferral. If deferral changes acceptance, obtain the required scope decision; creating a follow-up does not silently remove an unmet AC. Record rejected findings with rationale and the applicable decision authority.

A finding on an earlier revision remains an obligation to disposition, not proof that the current candidate still has the defect. Inspect or reproduce it on the current candidate before prescribing a fix. If rework changes the candidate, identify the resulting revision and verify that revision rather than reporting the pre-fix SHA as tested.

Collect evidence while working. For each AC, link a check or artifact and the tested revision; failed, skipped, or stale results need an explicit disposition. For UI/demo work the evidence is one screenshot per AC from the rendered app, which the owner can judge in minutes. A green aggregate check does not prove an unexecuted scenario.

Before accepting, verify:

1. Agreed AC are satisfied, or an authorized scope change explicitly revises them.
2. Relevant verification and review cover the current candidate; blocking findings have a recorded resolution.
3. The owner's acceptance is present and the task's delivery target is achieved. Agents never record their own work as accepted.
4. Evidence links and decisions are accessible to the next reviewer/agent.

These conditions define the tracker acceptance transition. `merge-ready` is not Done for a task whose target is merge; merge is not Done for a task that also promises deployment, docs, or downstream integration. Use the target actually agreed for the task, not a universal deploy requirement. Matt's action-specific authorization boundaries still apply.

Record one identifiable acceptance receipt on the Issue. Keep it as small as the decision permits; link an existing PR checklist or report instead of retyping it. A useful shape is:

```text
Acceptance: accepted | not ready
Candidate: PR / revision / environment
AC evidence: clause -> check/result/artifact
Review: findings and dispositions; required acceptance
Delivery: agreed target and observed result
Decision: actor/authority and time
Remaining: obligation, owner, next action, linked follow-up
```

The receipt is the decision record; linked runs, patches, and reviews remain primary evidence. An editable Issue comment is not an immutable audit log. Preserve the previous decision/revision when updating it. After new commits or changed AC, reassess affected evidence and review; link fresh verification or justify which prior evidence still applies. Reuse is a reasoned coverage decision, not an old pass silently carried forward.

Only an authorized acceptance transition may record accepted, close the Issue as completed, and project that outcome to Done. If evidence or authority is missing, report the specific missing obligation and executable next action through Matt rather than declaring completion.

## Automation and recovery

Inspect actual Project workflows, repository auto-close settings, and PR closing links. Projects can set Done on issue/PR closure or merge; these events do not themselves evaluate this acceptance protocol. For a Project adopting this protocol, configure event-to-Done and Status-to-close behavior so it cannot substitute for acceptance. Make workflow changes only within the authorized setup scope.

Use closing keywords or other auto-closing PR links only when their merge fulfills the Issue's remaining obligations under the repository policy. For a parent still waiting on docs, deploy, or integration, use a plain reference and let the acceptance coordinator close it later. A manual Development link may also auto-close; it is not a guaranteed non-closing alternative.

The proposed coordinator sequence is: refresh task/candidate/evidence, apply the acceptance conditions, record the decision, then reconcile Issue state and Project Status. These are separate operations. Use stable Issue/item/run identities, read back results, and retry only incomplete authorized writes. On uncertain acceptance or a newer candidate, reassess before retrying. Preserve an accurate receipt if a Project write fails, and report the mismatch; never fabricate success from an API error. Respect Matt's bounded retry rule.

Issue/PR/test updates can supply facts to an existing coordinator or Actions integration. A skill reference does not install a runner, polling loop, review bot, or enforcement. Before proposing such automation, inspect available integration and permissions: repository credentials may not grant access to a user/org Project. Required checks and review rules protect configured merge paths; they do not prevent every manual Issue closure or Done edit. Report and reconcile contradictory states under the repository policy.

When a post-merge report arrives, link the original Issue/PR, failing run or reproduction, and revision; keep cause unknown until diagnosed. Reopen when the original task was closed with obligations unmet, or create a linked repair when an accepted delivery later regresses or the repair has distinct scope. Follow the repository's policy, preserve what was previously accepted, and re-evaluate the Project state and affected dependents. An unrelated failing CI run alone does not prove causation.

For an authorized tracker migration, move active outcomes and needed prerequisites first, retain legacy IDs/history, map hierarchy separately from blocking edges, and recalculate readiness from evidence. Choose one dispatch authority before resuming workers; avoid two trackers launching the same work. Closed history can remain archived in the old tracker.

## Basis and capability references

A synthesis, not a measured guarantee. Precedents: [OpenHands #2841](https://github.com/OpenHands/software-agent-sdk/pull/2841), [Dyad #4187](https://github.com/dyad-sh/dyad/pull/4187), [Goose #11307](https://github.com/aaif-goose/goose/pull/11307). GitHub docs: [dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies), [sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues), [automations](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations), [PR-to-Issue linking](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue), [Copilot cloud agent](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github), [Projects API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects), [Projects with Actions](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions). Verify current product behavior before relying on it.
