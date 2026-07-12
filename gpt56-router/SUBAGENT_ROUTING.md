# Legend GPT-5.6 routing

## Compatibility gate

Apply this profile only when runtime metadata identifies `gpt-5.6-luna`,
`gpt-5.6-terra`, or `gpt-5.6-sol`. If the active family is not GPT-5.6, stop
using this profile. Tell the user to ask an agent to follow the safe-removal
section in `gpt56-router/INSTALL_FOR_AI.md`. Never silently map these roles onto
another model family.

## Default control plane

The recommended parent is **Sol medium**. Normal planning, routing, synthesis,
UX judgment, and routine review stay with the parent.

- Known target, at most two files or directories -> `legend-targeted-scout`
  (`gpt-5.6-luna`, high).
- Unknown target, broad repository search, contract tracing, or large context ->
  `legend-repo-explorer` (`gpt-5.6-terra`, high).
- Implementation, tests, frontend work, and ordinary debugging ->
  `legend-builder` (`gpt-5.6-terra`, high).
- Security, auth, production, migration, destructive actions, architecture
  spanning three or more systems, conflicting agent conclusions, or a failed
  approach -> `legend-guardian` (`gpt-5.6-sol`, high).
- Commit and push, only after explicit user authorization ->
  `legend-publisher` (`gpt-5.6-luna`, low).

## Planning

Gather broad repository evidence with `legend-repo-explorer`, then let the Sol
medium parent write the plan. Use `legend-guardian` before implementation when
the plan is security-sensitive, production-facing, destructive, migration-heavy,
cross-system, or costly to reverse.

## Manual-only effort

Sol xhigh, max, and ultra are manual only. Recommend xhigh after Sol high cannot
resolve conflicting evidence; recommend max for a deep problem that cannot be
split; recommend ultra only when at least three independent workstreams can run
in parallel. State the reason and wait for user approval.
