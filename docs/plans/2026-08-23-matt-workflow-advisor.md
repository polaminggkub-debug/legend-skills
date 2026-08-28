# Matt guided workflow router implementation plan

> Owner decision: preserve the current checkout, validate the global installation and repository copy, and require separate approval before push, PR, merge, or publication.

## Goal

Add a model-invoked `matt` skill that uses current evidence to guide work to the next safe, observable transition. The course-derived workflow selects the stage; installed stable skills from `mattpocock/skills` remain the source of truth for executing each stage.

## Work

1. Add a concise root-level `matt/SKILL.md`, Codex UI metadata, an English course reference, and a verified upstream dependency lock.
2. Make Guided mode the default: report state, evidence, a compact task contract, the next executable action, and HITL/AFK-ready status. Ask before an AFK-ready transition unless the current user message explicitly enables Autopilot.
3. Gate routing on the stable Engineering and Productivity skills in the lock. Ask before any installation, and generate a global Skills CLI command for the selected agent targets.
4. Capture global tracker/spec defaults in the OS-native user configuration directory. Read repository tracker configuration from `docs/agents/issue-tracker.md` and store only the repository's spec override in `docs/agents/matt-workflow.md`.
5. Add `matt` to repository discovery and installation documentation while preserving existing backup, conflict, and cross-platform rules.
6. Stop in every mode for scope expansion, architecture/dependency/schema/API changes, merge, deploy, Production, destructive work, insufficient evidence, or retry-budget exhaustion.
7. Validate structure, English-only content, dependency completeness, installation behavior, and the six Guided/Autopilot scenarios. Finish with independent Standards and Spec reviews.

## Acceptance

- `matt/SKILL.md` is at most 150 lines and remains implicitly invokable.
- Every file under `matt/` is English.
- The dependency lock contains exactly the 25 stable upstream skills published in the reviewed manifest, with no in-progress, misc, or deprecated paths.
- Missing prerequisites produce an installation gate; normal routing never silently falls back.
- Responses foreground an evidence-backed next action and its approval boundary; unsupported runtimes provide an exact handoff rather than claiming automation.
- Guided mode never starts an AFK-ready action before approval, and Autopilot never crosses a mandatory HITL boundary.
- README and installing-agent instructions include `matt` once.
- Global installation and repository copies match after validation; push, PR, merge, and publication remain separately authorized actions.
