# Legend Skills

Portable agent skills for Codex and Claude Code.

| Component | Codex | Claude Code | Requirement |
|---|---:|---:|---|
| General skills | Yes | Yes | None |
| Matt guided workflow router | Yes | Yes | Stable `mattpocock/skills` suite |
| Steve Design Suite | Yes | Yes | None |

## Learning resources

[Learning Resources](learning-resources/README.md) collects Thai self-study
lessons, research evidence, and offline labs for AI Delivery, Context Discovery,
Task Orchestration with GitHub Projects, and Guardrails/Lint. Start from its
topic index to choose a lesson or exercise.

## Install

Give this repository to your coding agent and say:

```text
Read INSTALL_FOR_AI.md and install the components I request.
Follow every compatibility, backup, ownership, and verification rule.
```

Installing files from this repository requires no installer runtime. The same
instruction works on Windows, macOS, and Linux. If `matt` prerequisites are
missing, their separate upstream installation requires Node.js and `npx`.

General skills: `chris`, `formpress`, `margaret`, `matt`, `ship`, `steve`,
`ui-ux-pro-max`, and `update-all`.

`chris` connects acceptance criteria to focused tests, lint/guardrails, and actual
CI evidence. Its short entrypoint routes to operating guides and a local case
library with pinned source links; cases are read only when relevant. It preserves
the explicit user-request requirement for a Full E2E run. For Codex, install one
global copy at `~/.agents/skills/chris`; the [installation guide](INSTALL_FOR_AI.md#chris-global-installation) covers duplicate cleanup and preservation of an existing invocation preference.

`matt` uses current evidence to identify the next safe workflow action and its
approval boundary. Guided mode asks before starting an AFK-ready action;
Autopilot must be explicitly enabled for the current request and still stops at
scope, architecture, merge, deploy, Production, and destructive boundaries. On
first use Matt checks for the reviewed stable skills from
[`mattpocock/skills`](https://github.com/mattpocock/skills), asks before any
external installation, and captures tracker/spec defaults.

On each invocation, Matt assesses the active task and the context already
available. It consults [Context Discovery](matt/references/context-discovery.md)
for missing or conflicting knowledge, targeted code/contract discovery, and
handoff verification. Applicable, current context can be reused across tasks in
the same session; a task change does not require a session reset or a full repository read.

For repositories using GitHub Projects, Matt loads a
[shared workflow reference](matt/references/github-projects.md) for readiness,
dependencies, agent handoff, and acceptance backed by current evidence. The
global skill reuses each repository's Project mapping and policy; installing it
does not migrate tasks or change an existing tracker default.

For a complete `matt` installation, tell the installing agent to read and
follow `matt/INSTALL_FOR_AI.md`. Copying or downloading the directory alone is
only a partial installation. The installer verifies the pinned GitHub manifest,
downloads every missing upstream dependency after one approval, and completes
configuration immediately or on the first `$matt` invocation.

## Repository rename

This project was previously named `claude-skills`. GitHub redirects old links
after the repository is renamed to `legend-skills`.
