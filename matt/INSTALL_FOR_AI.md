# Install Matt

Installation is interactive and is not complete when the files are merely copied.

1. Resolve the target agents and their global skill directories.
2. Preserve any existing `matt` destination. If it is not an unchanged managed copy, create a timestamped backup and ask before replacement.
3. Copy this entire `matt` directory to each approved global skill directory.
4. Read `dependency-lock.json`, fetch the official manifest from the pinned GitHub `installSource`, and require the manifest version, commit, and 25 stable Engineering/Productivity paths to match the lock before continuing.
5. Verify all 25 required skill names in every selected agent target. Prefer registry provenance from `mattpocock/skills`; when a receipt is absent, use the GitHub fallback in `SKILL.md`. Preserve matching local skills and report modifications.
6. If any required skill is missing, build one pinned Skills CLI command containing every missing `--skill` and selected `--agent`. Explain that the dependency download is required to complete installation, ask once, then run it after approval. Re-check all targets and do not report installation complete until all 25 are present. Preserve explicit source conflicts and ask separately before replacement.
7. Resolve the OS-native user configuration directory and inspect `legend-skills/matt.md`.
8. If the global configuration is absent, immediately ask for:
   - agent targets;
   - default tracker: none, GitHub Issues, Beads, or a named custom tracker;
   - default spec system: Markdown PRD/plan, OpenSpec, none, or a named custom system.
9. Show the English managed block from `SKILL.md`. Write it only after approval. Preserve unrelated content and apply the backup and conflict rules in `SKILL.md`.
10. Read back the installed skill and configuration. Report installed paths, backups, prerequisite status, and any deferred action.

If the user declines a required dependency download or defers configuration, report installation as partial. A raw download or Skills CLI copy cannot execute setup by itself; the installing agent must perform these steps or the user must invoke `$matt initialize` once.
