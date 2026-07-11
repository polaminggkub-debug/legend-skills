---
name: margaret
description: >
  Use when auditing a module or codebase for bugs, security, reliability, data
  integrity, coverage gaps, systematic review, or "what are we missing?". Not
  for a single-file quick review.
---

# Margaret — Deep Module Audit

Audit a module as a system, not a pile of files. Find real, reproducible risks;
verify before reporting them.

## Start

Identify module boundary, source/tests/config/migrations, user flows, and known
pain. Detect language, framework, package versions, and deployment model. Read
official documentation only when a version-sensitive behavior matters; record
sources and assumptions.

Choose mode:

| Mode | Use when | Lenses |
|---|---|---|
| Standard | ordinary module audit | 2–4 relevant lenses |
| Deep | security, data, critical flow, large change | 4–7 relevant lenses |

Possible lenses: behavior, data/integration, security/access, error/recovery,
UI/flow, tests/observability, performance. Do not force irrelevant lenses.

Read `references/audit-lenses.md` for selected lenses. After stack detection,
read `references/profiles.md`. For security/data scope, also read
`references/security-data.md`. Before reporting, read
`references/report-contract.md`.

## Workflow

1. Create a deterministic manifest; mark every in-scope file `REVIEWED`,
   `FINDING`, `SKIPPED — reason`, or `COVERAGE GAP`.
2. Inspect each selected lens independently where useful.
3. Verify every CRITICAL/HIGH finding against current code and a concrete path.
4. Compare previous reports: `OPEN`, `FIXED`, or `REGRESSED`.
5. State uncertainty rather than guessing.

Default: one analysis plus mandatory verification. Add an independent pass only
for deep/high-risk audits. For very large scope, state an estimate before work;
do not ask for a pass count by default.

## Evidence and report

Every CRITICAL/HIGH finding requires `file:line`, code/config evidence, trigger
scenario, impact, and verification. Mark it `CONFIRMED`, `LIKELY`, or `NEEDS
REVIEW`.

Write Markdown to `docs/audit/{module}-audit-report.md` unless the project says
otherwise. Start with `PASS`, `CONDITIONAL PASS`, or `FAIL`; order findings
`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`; include coverage, assumptions, sources,
previous-finding status, and smallest safe next action. No HTML or numeric score.

## Constraints

Use project-native commands and platform-neutral paths. Never assume Vue,
Supabase, Bash, `python3`, a fixed home directory, or a specific agent tool.
