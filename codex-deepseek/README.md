# DeepSeek through Codex

An opt-in direct API route using the official Codex CLI as the coding agent.
Astra and the normal Luna subagent remain unchanged. This does not invoke
OpenCode or charge Go/Zen credits; requests are billed by DeepSeek directly.

## Setup

Install the official Codex CLI (verified with 0.147.0). Create the private
directory `~/.local/share/codex-deepseek/home`, and copy `run.py` into its parent.
Obtain the current `models.json` from the official
[DeepSeek Codex integration guide](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/)
and put it inside `home`. Keep the supplied catalog intact; its model metadata
is needed for Codex compatibility. The API model identifier is `deepseek-flash`.

Create `home/config.toml`, substituting the absolute catalog path:

```toml
model = "deepseek-flash"
model_provider = "deepseek"
model_reasoning_effort = "high"
web_search = "disabled"
model_catalog_json = "/absolute/path/to/codex-deepseek/home/models.json"

[model_providers.deepseek]
name = "DeepSeek direct"
base_url = "https://api.deepseek.com"
wire_api = "responses"
env_key = "DEEPSEEK_API_KEY"
```

Provide `DEEPSEEK_API_KEY` through the environment, or store it in the private
`~/.local/share/codex-deepseek/api-key` file. On macOS/Linux restrict the directory
to mode 700 and the key to 600; on Windows restrict its ACL to the owner.
Credentials are never part of this repository or a task prompt.

## Explicit delegation

When the user says “ให้ DeepSeek ทำผ่าน Codex”, write a focused task prompt to
a temporary file, then invoke the installed `run.py` with `--repo` and
`--prompt-file`. Use `--read-only` for questions and Hello probes. Keep the same
foreground process handle until it finishes and report the final JSON usage
and result. Check failures as failures; a nonzero exit is not completion.

The separate `CODEX_HOME` avoids loading the coordinator's global skills,
plugins and MCP configuration. The target repository's own instructions still
apply. The prompt enters via explicit stdin, so unrelated parent stdin is not
accidentally appended. Coding runs use Codex's workspace-write sandbox.

This route currently uses native Codex execution, not OpenCode Worker's
100-step budget, bounded build repairs, automatic attributed commits or CSV
reporting. Do not describe those protections as installed on this route.
The coding harness has a prompt/token overhead even for Hello.

References: [DeepSeek Responses API](https://api-docs.deepseek.com/guides/responses_api/),
[Codex provider configuration](https://developers.openai.com/codex/config-advanced/).
