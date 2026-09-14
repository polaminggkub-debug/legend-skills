# Matt and Chris: coordinate from evidence

Date: 2026-09-14. Supersedes the Guided/Autopilot routing and bootstrap requirements
in the [August plan](2026-08-23-matt-workflow-advisor.md).

## Requested outcome

A user can name an outcome or ask what comes next without choosing stages or
helper skills. Matt inspects current work and continues authorized execution;
Chris establishes acceptance, selects checks, and assesses evidence. Advice-only
requests remain advice. The user requested global and GitHub updates, preservation
of capability with simpler instructions, and no model/behavioral testing.

## Design decisions

- Give Matt one loop with observable exit conditions. Move installer mechanics
  and specialist selection out of the main path; check only selected helpers.
- Preserve task state in the existing task/plan and refresh it from actual evidence.
  Use conditional Context Discovery and Projects references rather than loading
  the research library or restarting every session.
- Use existing task authorization across phases. Keep material product decisions,
  scope expansion, and externally consequential actions bound to applicable
  authorization. Do not change platform permissions or repository enforcement.
- Give Chris ownership of testing policy, including its internal TDD guide.
  Retain diagnosis and whole-diff review as distinct responsibilities. Preserve
  customized upstream helpers and choose compatible execution paths.
- Preserve focused verification, independently observable AC, current evidence,
  review disposition, handoff, integration ownership, and post-merge obligations.
  Full E2E still requires an explicit user request; an unmet required gate remains
  visible rather than being waived.
- Keep user configuration and invocation policies. Core installation is Matt plus
  Chris; the unchanged pinned 25-helper lock describes the optional full bundle.

## Official sources and interpretation

Sources were inspected on 2026-09-14. Model pages describe API capabilities;
particular Codex account/runtime availability is a separate fact.

- [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
  recommends direct prompts, clear goals/constraints, and avoiding unnecessary
  requests to expose step-by-step reasoning. This supports concise decision rules.
- [Astra model guidance](https://developers.openai.com/api/docs/guides/latest-model)
  discusses multistep work and reviewing stale, conflicting instructions. This
  supports resolving policy conflicts rather than merely shortening wording.
- [Sol model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
  describes a flagship for complex professional work, high reasoning support,
  and tool/skill capabilities.
- [Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
  describes a model for cost-sensitive workloads, max reasoning support, and
  tool/skill capabilities. These capabilities alone do not establish coordination
  reliability or equivalence to a larger model.

Reasonable inference: this structure is feasible for the named model families
and should reduce avoidable interpretation and routing burden. For a less capable
worker, bounded outcomes, explicit checks, and external task state are preferable
to reliance on recalling a long conversation. Complex architecture, diagnosis,
and acceptance judgment can still exceed a model's capability; a skill does not
remove that limitation.

Unknown: compliance rates for these exact skills on Astra low, Sol high, or Luna
max; equivalence to the previous version; and how much human supervision is
reduced. No model benchmark or behavioral simulation was requested or run.

## Validation scope

Static validation covers skill frontmatter, local reference targets, preserved
Full E2E policy, unchanged upstream lock, ownership/authorization consistency,
and agreement between installed files and the reviewed repository revision.
Independent document review checks for contradictory instructions and lost
requirements. These checks do not establish model behavior. Publication and
installation outcomes are recorded in the associated pull request and task.
