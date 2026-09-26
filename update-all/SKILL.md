---
name: update-all
description: >
  Use when asked to bulk-update the agent ecosystem: Codex, Claude Code,
  plugins, marketplaces, skills, Steve Design Suite, or supported config via
  /update-all, "update everything", "อัพเดททุกอย่าง", or "อัพเดทล่าสุด".
---

# Update All — Agent Ecosystem

Default scope: Codex, Claude Code, plugins/marketplaces, skills, the Steve
Design Suite, and supported agent-config migrations. It does not silently update
the OS, Homebrew, global npm, project dependencies, or arbitrary developer tools.

## Transaction

1. Discover installed components, install source, version, update candidate,
   dirty state, and available rollback method.
2. Present a concise plan. Invoking this skill authorizes safe agent updates;
   ask only for a major/breaking/no-rollback change.
3. Snapshot current versions/configuration. Never auto-stash, auto-merge, reset,
   or resolve conflicts in a user repository.
4. Update one component at a time using its documented installer/marketplace.
5. Verify command availability, version, and plugin/skill discovery after each.
   Stop and rollback the affected component where the documented rollback exists;
   otherwise stop and report the failure without further changes.
6. Write a Markdown report with updated, skipped, failed, rollback, and restart
   requirements.

## Optional developer tools

Suggest (do not run) a developer-tool update only when it is likely under five
minutes, non-breaking, no reboot, no dirty repository impact, and has rollback.
Run it only after explicit opt-in.

## Constraints

Use OS-specific adapters discovered at runtime; no fixed shell, `python3`, home
directory, package manager, or invented CLI command. The suite uses verified
releases only: never pull untested latest at runtime.

RTK, Graphify, Caveman, and Cavecrew are retired. Never install, update,
restore, recommend, or re-enable them. If discovered, report them as retired
and skip them. Treat an explicit removal request as separate destructive work:
verify exact targets and document rollback before deleting anything.
