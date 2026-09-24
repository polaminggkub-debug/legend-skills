---
name: opencode-worker
description: Delegate a coding task to the official OpenCode CLI through the configured provider, with executable project workflow checks, usage accounting, and attributed commits. Use when the user asks OpenCode, OpenCode Go, OpenRouter, DeepSeek, or GLM to do coding work.
---

Read [the installed worker guide]({{WORKER_README}}). Invoke the worker directly with Python `{{WORKER_PYTHON}}` and entrypoint `{{WORKER_ENTRYPOINT}}`; an intermediate Codex subagent is unnecessary. Handle command construction and the saved credential for the user.

Fresh installations are Go-only: they expose the provider-neutral `opencode-worker` entrypoint, use OpenCode Go (`opencode-go`), and default to DeepSeek V4.1 Flash (`deepseek-v4.1-flash`). Configure that provider with `auth login --provider opencode-go` and `configure --provider opencode-go --model deepseek-v4.1-flash`; `configure` persists the selected provider and model, while `auth status --provider opencode-go` inspects its credential. Provider credentials remain separate and API keys stay outside prompts, arguments, and Git. Existing OpenRouter installations remain supported through the backwards-compatible `openrouter-worker` alias; provider selection is explicit and a Go run has no implicit OpenRouter fallback. The worker is isolated, so global OpenCode model settings do not control its default.

Inspect the project before the first dispatch. Reuse its committed `.opencode/worker.json` when present. For unfamiliar delivery rules, determine the real commands and ordering from the project's instructions and CI, then encode that plan once using the guide. Discovery candidates alone are not validated policy. Preserve the user's requested scope; ordinary file edits need no invented build.

Give one focused implementation prompt and invoke the foreground worker once. The executable owns declared checks, bounded repair attempts, commits, metadata stages, and local waiting. Defaults are 100 model steps and 60 minutes shared across the entire job, with at most two additional repair attempts. For an explicit no-repair/one-shot request, use `--max-repairs 0`; see the installed guide’s **Bounded repairs** section for overrides and stop reasons. When the native tool yields, keep the same handle and follow the installed guide's **Waiting and timing** section for continuation, final-report recovery, and timing interpretation. The Python monitor checks locally every five seconds without model/API calls, and there is no fixed 20-minute job cap. `hello --timeout 10` probes the actual OpenCode CLI without modifying project files; its timeout is not a coding-job deadline.

Report the compact final result in the Codex turn and distinguish code committed from application checks passed. If the wrapper crashes, exits nonzero, or leaves no final report, report failure or unknown in Codex and recover once with `wait --run RUN_UUID` when the run ID is available; never launch a fresh job or reset its budget automatically after final failure. The executable already owns its bounded repairs. The final Codex result is the reporting surface on desktop and mobile when the host session is reachable; there is no OS-only notification or detached completion path. Preserve usage, model, provider, OpenCode version, elapsed time, changed-file and diff-line counts, commits, and check results. Cost is an estimate, not a billing receipt; for Go, quota-versus-Zen-balance billing is unknown unless the provider emits evidence. Dispatch and tool continuations can consume Codex tokens, so make no zero-total-token claim. Use the worker's cancellation command when the user asks to stop its run.

## Fast dispatch

If a job is slow, the fix is almost always upstream of dispatch, not a bigger
budget: the worker should write, not explore. Before dispatch, build a context
pack (ideally from a script, e.g. a Playwright run dumping `ariaSnapshot()` per
step) with the exact facts the worker needs, and write the prompt as a
numbered spec ("do not explore beyond these files"), not a pointer to go learn
a flow. One independent unit per job; run independent units in parallel only
across separate clones (a shared repo's worktrees share one lock file and will
block each other for the whole job, not just at commit time — see the
reference for the exact mechanism). Start with tight caps (`--max-job-seconds
1800 --max-model-steps 80`) and fix the pack/prompt on failure instead of
raising them. Scope checks to what changed, and measure every run's wall time,
steps, cost, and check result (via `runs.sqlite3`) against a baseline so
regressions are visible. Full detail, including the verified worktree-lock
finding: [`references/fast-dispatch.md`](references/fast-dispatch.md).
