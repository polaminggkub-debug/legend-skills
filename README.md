# Personal agent skills

Focused skills for testing, module audits, live production shipping, product
design, and agent-environment updates.

| Skill | Use |
|---|---|
| `chris` | **all** testing work; testable architecture remains the core |
| `formpress` | precise positioning for printing onto pre-printed forms |
| `margaret` | deep module/system audit |
| `ship` | live production deployment only |
| `steve` + `ui-ux-pro-max` | product design decision + implementation guidance |
| `update-all` | safe agent ecosystem update |

## Install

The portable installer needs Python 3. It copies skills directly, so it works
for local Codex, Claude Code, and compatible cloud workspaces that expose a
writable skills directory.

```powershell
python install.py --platform codex
python install.py --platform claude
```

```sh
python3 install.py --platform codex
python3 install.py --platform claude
```

Override the destination with `CODEX_HOME` or `CLAUDE_CODE_SKILLS_DIR`.
Restart the agent if discovery is not immediate.

## Steve Design Suite

`steve-design-suite/` is a versioned bundle: installing it supplies both
`steve` and `ui-ux-pro-max` together. `dependency-lock.json` records the tested
pair. Release a new suite only after validation; consumers update to that
verified release and can reinstall the preceding release to roll back.

The repository includes Codex and Claude Code plugin manifests for marketplace
distribution. A marketplace/managed-plugin installation can provide platform
updates; direct skill installation is intentionally pinned until the user runs
an update.

## Validate

```sh
python scripts/validate-skills.py
```

The validator is standard-library-only and runs on Windows, macOS, and Linux.
