# Legend Skills

Portable agent skills for Codex and Claude Code.

| Component | Codex | Claude Code | Requirement |
|---|---:|---:|---|
| General skills | Yes | Yes | None |
| Matt workflow coordinator | Yes | Yes | Bundled Chris; optional pinned helper suite |
| Steve Design Suite | Yes | Yes | None |
| [OpenCode Worker](opencode-worker/README.md) | Yes | CLI can be invoked separately | Python 3.9+, Git, official OpenCode CLI, own provider credential; macOS/Windows |

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

Copying the general skill files requires no installer runtime and works on
Windows, macOS, and Linux. OpenCode Worker has its own Python installer for
macOS/Windows. Matt's optional upstream helper bundle requires Node.js and `npx`.

General skills: `chris`, `formpress`, `margaret`, `matt`, `ship`, `steve`,
`ui-ux-pro-max`, and `update-all`.

`opencode-worker` delegates coding through the official OpenCode CLI. Fresh
installations are Go-only: they use OpenCode Go (`opencode-go`) with DeepSeek
V4.1 Flash (`deepseek-v4.1-flash`) as the default. In the OpenCode Go console,
enable **Use balance** so Go can continue against available Zen balance after
Go quota under the same Go service; a Go run does not fall back to OpenRouter or
the separate Zen provider. Existing OpenRouter installations remain usable,
while new installs expose the provider-neutral `opencode-worker` entrypoint and
keep `openrouter-worker` as a backwards-compatible alias. Credentials stay
separate per provider, and API keys stay out of prompts, arguments, and Git.

Its executable enforces declared project checks, source/metadata commit ordering,
usage records, and local process monitoring without extra model prompts. It
includes a Codex entrypoint, an installer that preserves private
settings/history, and offline macOS/Windows CI. Use [its installer](opencode-worker/INSTALL_FOR_AI.md);
each machine supplies its own credential and each special project workflow is
declared once in that project's committed contract.

The worker keeps completion in the Codex conversation, including the mobile view
when the host session is reachable. Read its [waiting and timing guide](opencode-worker/references/waiting-and-timing.md)
for the continuation recipe and optional report timing fields.

`chris` connects acceptance criteria to focused tests, lint/guardrails, and actual
CI evidence. Its short entrypoint routes to operating guides and a local case
library with pinned source links; cases are read only when relevant. It preserves
the explicit user-request requirement for a Full E2E run. For Codex, install one
global copy at `~/.agents/skills/chris`; the [installation guide](INSTALL_FOR_AI.md#chris-global-installation) covers duplicate cleanup and preservation of an existing invocation preference.

`matt` coordinates work from a broad goal or the current task state:
inspect, choose, act, verify, and reassess. A request to build or fix authorizes
ordinary implementation, relevant verification, and in-scope rework without
repeated phase approvals. Advice-only requests remain advice. Material unresolved
decisions and actions beyond existing authority still require the user's decision.

Matt selects and reads Chris for acceptance, testing, and TDD; the user does not
need to choose the testing stage. Diagnosis and whole-diff review helpers retain
their separate roles. Customized helpers are checked for tracker/spec/test-policy
compatibility before use. Matt does not route testing through a second `$tdd`
policy or change a helper's configuration to fit a task.

Examples:

- “Use $matt to build Search; handle the implementation and verification.”
- “Use $matt to inspect where this task stands and recommend the next step.”
- “Use $chris to check whether this change meets its acceptance criteria.”

[Context Discovery](matt/references/context-discovery.md) is selected for missing,
conflicting, stale, or handed-off knowledge. Applicable context is reused; a new
task or message does not force a session reset or a full repository read.
[GitHub Projects](matt/references/github-projects.md) supplies readiness,
dependencies, handoff, and evidence-backed acceptance when Projects is selected.
Its global availability does not migrate tasks or change tracker defaults.

Follow [Matt's installer](matt/INSTALL_FOR_AI.md) for installation/update. The
core workflow installs Matt and Chris; the pinned upstream suite supplies optional
specialized helpers. Routine work checks its selected helper rather than auditing
all 25. Existing defaults are preserved; missing setup files do not block
independent work, and tracker identity is resolved before writes.

The [design note](docs/plans/2026-09-14-matt-chris-workflow.md) records the
simplification, official prompting/model sources, and validation limits. These
skills specify a workflow; they do not install an autonomous background runner
or guarantee identical performance across models.

## Repository rename

This project was previously named `claude-skills`. GitHub redirects old links
after the repository is renamed to `legend-skills`.
