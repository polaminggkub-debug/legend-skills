# Legend Skills: instructions for the installing agent

Use native file operations available in the agent environment. Preserve
unrelated files and never replace a user-modified managed file without explicit
approval.

## 1. Preflight

1. Identify the requested platform: Codex or Claude Code.
2. Identify the requested components from the general-skills table below.
3. Resolve the platform skill destination:
   - Codex: `${CODEX_HOME:-~/.codex}/skills`
   - Claude Code: `${CLAUDE_CODE_SKILLS_DIR:-~/.claude/skills}`
4. Inspect each destination for conflicts before mutating it. Put any
   timestamped backups outside the destination being replaced.

## 2. Install general skills

Copy the requested repository directories into the platform skill destination:

| Source | Destination name |
|---|---|
| `chris` | `chris` |
| `formpress` | `formpress` |
| `margaret` | `margaret` |
| `matt` | `matt` |
| `ship` | `ship` |
| `update-all` | `update-all` |
| `steve-design-suite/skills/steve` | `steve` |
| `steve-design-suite/skills/ui-ux-pro-max` | `ui-ux-pro-max` |

If a destination exists and is not recorded as an unchanged Legend-managed
copy, preserve it and ask before replacement. Never delete unrelated files.

### Chris global installation

For Codex, install Chris in the user-scoped `~/.agents/skills/chris` location so
it is available in every project. Keep this repository checkout outside a skill
discovery directory. For Claude Code, retain the platform skill destination.

Before copying, inventory existing Chris entries in user, legacy, project, and
plugin skill locations, including symlinks and nested backups. Compare their
contents and preserve meaningful customizations. Preserve an existing target's
`agents/openai.yaml` invocation policy; a fresh install uses the repository
metadata, which permits implicit invocation by default.

When duplicate cleanup is authorized, move redundant copies to a timestamped
backup outside every skill discovery directory. Preserve distinct project or
plugin configuration unless the requested consolidation covers it. Install the
complete Chris directory, including references and UI metadata. Verify the
intended global entry and report intentionally retained project or plugin
copies separately. If the UI has not refreshed, follow the host's reload or
restart guidance; a file inventory does not confirm that its picker refreshed.

See [official Codex skill locations](https://learn.chatgpt.com/docs/build-skills)
for user and repository scopes and refresh behavior.

### Matt prerequisite and setup

When `matt` is requested, read and follow [matt/INSTALL_FOR_AI.md](matt/INSTALL_FOR_AI.md).
Installation is incomplete until its interactive bootstrap is completed or
explicitly reported as deferred. This prerequisite may require Node.js and
`npx`; copying Legend Skills itself does not.

## 3. Verify

Read back every requested destination. Confirm that each skill has its expected
`SKILL.md` and, when present in the source, its UI metadata and references.
When `chris` was requested for Codex, confirm the intended global entry and
resolve every local reference. When `matt` was requested, confirm its locked
prerequisites are available to every selected agent and report whether global
defaults were configured or deferred.

Report installed paths, backups, skipped conflicts, and any manual action still
required. These rules apply equally on Windows, macOS, and Linux.
