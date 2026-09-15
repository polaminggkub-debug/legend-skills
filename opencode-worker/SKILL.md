---
name: opencode-worker
description: Delegate a coding task to OpenCode through OpenRouter with executable project workflow checks, usage accounting, and attributed commits. Use when the user asks OpenCode, OpenRouter, DeepSeek, or GLM to do coding work.
---

Read [the installed worker guide]({{WORKER_README}}). Invoke the worker directly with Python `{{WORKER_PYTHON}}` and entrypoint `{{WORKER_ENTRYPOINT}}`; an intermediate Codex subagent is unnecessary. Handle command construction and the saved credential for the user.

Inspect the project before the first dispatch. Reuse its committed `.opencode/worker.json` when present. For unfamiliar delivery rules, determine the real commands and ordering from the project's instructions and CI, then encode that plan once using the guide. Discovery candidates alone are not validated policy. Preserve the user's requested scope; ordinary file edits need no invented build.

Give one focused implementation prompt. The executable owns declared checks, commits, metadata stages, and local waiting. Report its compact final result and distinguish code committed from application checks passed. A one-way request has no orchestrator repair or automatic retry. Use the worker's cancellation command when the user asks to stop its run.
