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
   destinations. Defaults respect `OPENROUTER_WORKER_HOME` and `CODEX_HOME`.
4. Run the same installer without `--check`. It copies only program/docs/example
   files, renders absolute paths in the skill, and adds a small owned block to
   global `AGENTS.md`. Backups stay outside skill discovery folders. Existing
   settings, credentials, and run history are preserved.
5. Invoke the returned entrypoint with that Python: `auth status`, then
   `doctor --dir PROJECT`. For a fresh machine, arrange hidden terminal input
   for `auth login`; each person supplies their own OpenRouter key. Do not read
   another person's credential or distribute it with this repository.
6. Read back the installed skill, registration, and `installation.json`.
   Confirm paths and hashes, preserved settings/history, and unresolved
   dependency/project setup issues. An existing application session may need
   a refresh/restart to discover a newly installed skill; file existence alone
   is not evidence that the UI has refreshed.

On Windows, use an argument vector or PowerShell's call operator for a quoted
Python path. The worker supports the official npm OpenCode shim through its
Node entrypoint. Unknown batch shims are rejected: use the program's real
executable or a repository script launched with an explicit interpreter.

## Update and recovery

Fetch the requested Legend Skills revision in a checkout outside skill
directories, inspect its changes, and rerun the tests/preflight/installer.
An unchanged managed copy can be updated. Locally edited files cause an error
before writes; compare and preserve customizations before retrying. Existing
legacy `codex-openrouter` files can migrate when their recorded verification
hashes match. Do not overwrite a conflict merely to make installation pass.

`installation.json` records managed file hashes, registration ownership, and a
timestamped backup path. Backups use a path hash plus filename; compare them
against the manifest destinations before restoring. Installation preflights all
known conflicts but is not a filesystem-wide transaction if the disk fails
mid-write; preserve the backup and rerun from a known source revision.

The worker does not change Codex models, reasoning effort, MCP servers, global
Git hooks, project CI, provider keys, or the official OpenCode package. Do not
install scheduled polling: heartbeat processing already happens inside the
running Python process with no model request.

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
