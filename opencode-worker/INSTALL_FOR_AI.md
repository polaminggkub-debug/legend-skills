# Install or update OpenCode Worker

Use this installer for the executable **and** its Codex registration. Do not
copy the templated `SKILL.md` through the generic skill-copy procedure.

## Prerequisites and installation

1. Read `README.md`. Inspect the target machine for Python 3.9+, Git, the
   official OpenCode CLI, and the intended Codex home. macOS and Windows are
   supported. Use the official [OpenCode installation guide](https://opencode.ai/docs/)
   when a prerequisite is missing. Preserve an existing OpenCode installation
   and configuration; an update is a separate action.
2. Run the package tests from the repository root:
   `python -m unittest discover -s opencode-worker/tests -v`.
   On macOS the available command may be `python3`; on Windows it may be
   `py -3`. Use the selected interpreter consistently.
3. Preflight with `python opencode-worker/scripts/install.py --check`.
   Optional `--base`, `--codex-home`, and `--skill-root` select explicit
   destinations. Existing legacy worker homes remain valid; preserve their
   settings and credentials during an update.
4. Run the same installer without `--check`. It copies only program/docs/example
   files, renders absolute paths in the skill, and adds a small owned block to
   global `AGENTS.md`. Backups stay outside skill discovery folders. Existing
   settings, credentials, and run history are preserved.
5. Invoke the returned provider-neutral `opencode-worker` entrypoint with that
   Python, then run `doctor --dir PROJECT`. For a new installation, run
   `auth status --provider opencode-go`. New installations are Go-only: they
   default to OpenCode Go (`opencode-go`) and `deepseek-v4.1-flash` (DeepSeek
   V4.1 Flash). If the credential is absent, arrange hidden terminal input for
   `auth login --provider opencode-go`; each person supplies their own provider
   key. Configure the isolated default with
   `configure --provider opencode-go --model deepseek-v4.1-flash`; this persists
   the provider and model. In the OpenCode Go console, enable **Use balance** so
   Go can continue against available Zen balance after Go quota under the same
   Go service. This is native Go billing through Go, not a switch to the
   separate Zen provider or an OpenRouter fallback. For an existing legacy
   installation, use `auth status --provider openrouter` and preserve its
   OpenRouter selection and credential; any Go migration is explicit. Do not
   read another person's credential or distribute it with this repository.
   Credentials remain separate per provider; keep API keys in private local
   storage and out of prompts, CLI arguments, and committed files.
6. Read back the installed skill, registration, and `installation.json`.
   Confirm paths and hashes, preserved settings/history, and unresolved
   dependency/project setup issues. An existing application session may need
   a refresh/restart to discover a newly installed skill; file existence alone
   is not evidence that the UI has refreshed.

On Windows, use an argument vector or PowerShell's call operator for a quoted
Python path. The worker supports the official npm OpenCode shim through its
native executable (or a recognized older Node entrypoint). Unknown batch shims
are rejected: use the program's real executable or a repository script launched
with an explicit interpreter. New installations expose `opencode-worker`;
existing installations keep `openrouter-worker` as a backwards-compatible
alias.

## Update and recovery

Fetch the requested Legend Skills revision in a checkout outside skill
directories, inspect its changes, and rerun the tests/preflight/installer.
An unchanged managed copy can be updated. Locally edited files cause an error
before writes; compare and preserve customizations before retrying. Existing
legacy OpenRouter worker files can migrate when their recorded verification
hashes match. Keep legacy OpenRouter credentials separate from the new
OpenCode Go credential, and do not overwrite a conflict merely to make
installation pass.

`installation.json` records managed file hashes, registration ownership, and a
timestamped backup path. Backups use a path hash plus filename; compare them
against the manifest destinations before restoring. Installation preflights all
known conflicts but is not a filesystem-wide transaction if the disk fails
mid-write; preserve the backup and rerun from a known source revision.

The worker does not change Codex models, reasoning effort, MCP servers, global
Git hooks, project CI, provider keys, or the official OpenCode package. Do not
install scheduled polling: heartbeat processing already happens inside the
running Python process with no model request.
`hello --timeout 10` probes the actual OpenCode CLI without modifying project
files; its ten-second limit is a probe limit, not a coding-job deadline.
If Go reports `RegionError`, explain the required hosting-region consent and
obtain the account owner's decision before enabling it in the Go console.
Do not silently change models or providers to make the probe pass.

## Project setup

The first coordinating session runs `inspect` and reads relevant project
instructions/CI. Commit one `.opencode/worker.json` describing the applicable
commands and ordering; use [the schema](references/workflow.md). A deliberate
empty check list is supported. Do not fabricate a generic build command.
Reuse this committed plan in later sessions and on other machines. Preflight
missing dependencies before delegation, preserving unrelated work.

Installation provides a reusable executor and a discoverable Codex entrypoint.
It cannot supply another person's secrets, infer undocumented business checks,
or guarantee model correctness on every repository.
