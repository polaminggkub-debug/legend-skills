# Legend Skills: instructions for the installing agent

Perform installation with native file operations available in your agent
environment. Preserve unrelated files. Never replace user-modified managed
files without explicit approval.

## 1. Preflight

1. Identify the requested platform: Codex or Claude Code.
2. Identify the requested components: general skills, GPT-5.6 Router, or both.
3. Resolve destinations:
   - Codex home: `${CODEX_HOME:-~/.codex}`
   - Claude skills: `${CLAUDE_CODE_SKILLS_DIR:-~/.claude/skills}`
4. Before any mutation, inspect all destinations for conflicts and create a
   timestamped backup outside the destination being replaced.

For GPT-5.6 Router, inspect runtime model metadata. Continue only when the
platform is Codex and the model is exactly `gpt-5.6-luna`, `gpt-5.6-terra`, or
`gpt-5.6-sol`. Otherwise skip it, explain incompatibility, and recommend the
safe-removal procedure below if an older installation exists.

## 2. Install general skills

Copy these repository directories into the platform skills directory:

| Source | Destination name |
|---|---|
| `chris` | `chris` |
| `formpress` | `formpress` |
| `margaret` | `margaret` |
| `ship` | `ship` |
| `update-all` | `update-all` |
| `steve-design-suite/skills/steve` | `steve` |
| `steve-design-suite/skills/ui-ux-pro-max` | `ui-ux-pro-max` |

If a destination exists and is not recorded as an unchanged Legend-managed
copy, preserve it and ask before replacement. Never delete unrelated files.

## 3. Install GPT-5.6 Router

1. Copy all five `gpt56-router/agents/*.toml` files to
   `<CODEX_HOME>/agents/`.
2. Copy `gpt56-router/SUBAGENT_ROUTING.md` to
   `<CODEX_HOME>/SUBAGENT_ROUTING.md`.
3. Add this exact managed block to `<CODEX_HOME>/AGENTS.md`, replacing
   `<absolute-path>` with the absolute path to the copied routing document:

```text
# BEGIN legend-skills:gpt56-router
@<absolute-path>/SUBAGENT_ROUTING.md
# END legend-skills:gpt56-router
```

4. Do not rewrite `config.toml`. Recommend `gpt-5.6-sol` with medium reasoning
   as the parent. Only if the user asks, back up `config.toml`, then merge the
   relevant values from `gpt56-router/config.example.toml` without disturbing
   unrelated settings.
5. Record every installed path, pre-existing backup path, and installed content
   hash in `<CODEX_HOME>/.legend-skills/gpt56-router-state.md`.

## 4. Verify

Read back each copied file. Confirm the five roles and models:

- `legend-targeted-scout` -> Luna high
- `legend-repo-explorer` -> Terra high
- `legend-builder` -> Terra high
- `legend-guardian` -> Sol high
- `legend-publisher` -> Luna low

Confirm `AGENTS.md` contains one exact managed block. Report installed paths,
backups, skipped conflicts, and any manual action still required.

## 5. Safe removal

1. Read `<CODEX_HOME>/.legend-skills/gpt56-router-state.md`.
2. For each managed file, compare its current hash with the recorded installed
   hash. Remove or restore it only when unchanged.
3. Preserve modified files and warn the user.
4. Remove the managed `AGENTS.md` block only when it still matches exactly.
5. Restore pre-existing backups only to their original paths.
6. Never delete or alter `config.toml` automatically.
7. Remove the state record only after every managed item is removed, restored,
   or explicitly preserved and reported.

These rules apply equally on Windows, macOS, and Linux.
