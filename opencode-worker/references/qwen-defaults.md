# Qwen defaults through OpenCode Go

Merge `examples/qwen-go-agents.json` into the native OpenCode global config,
preserving unrelated settings and backing up before replacing existing agents.
Connect the `opencode-go` provider with the user's Go credential. The API key
belongs in OpenCode's credential store, never in the example or Git.

Native OpenCode starts the `orchestrator` primary agent on Qwen3.8 Max. Its task
permission allows only the `coder` subagent on Qwen3.8 Flash. The primary agent
cannot edit files or run shell commands itself. `build` also uses Flash, and
`plan` uses Max. Explicit per-run model/agent choices can override defaults.

The audited worker has a different coordinator: Codex already owns planning.
Select Flash there with `opencode-worker configure --provider opencode-go
--model qwen3.8-flash`. Its isolated configuration keeps native subagent
delegation separate, retaining the worker's existing budget and accounting
scope. Max does not run inside this worker route. Native OpenCode subagent runs
do not inherit the Python worker's 100-step/60-minute shared budget or reports.

Smoke test each model with the installed worker's `hello --model MODEL
--timeout 10`, then verify a native orchestrator task calls `coder`, uses Flash
in the child session, and creates the requested file. API-only Hello results
are not evidence of a working coding client.

Verified on macOS with OpenCode 1.18.31. The JSON configuration uses native
OpenCode settings; Windows users use their OpenCode global config directory.

Sources: [OpenCode agents](https://opencode.ai/docs/agents/),
[Go endpoints](https://opencode.ai/docs/go/#endpoints).
