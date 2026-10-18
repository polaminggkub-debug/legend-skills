---
name: ship
description: >
  Use when explicitly asked to deploy a ready revision to production/live via
  $ship, "ship it", "deploy production/live", or "ขึ้น prod". Do not use for
  commit, push, build-only, setup, debugging, rollback, or non-production deploys.
---

# Ship — Production Deployment

**Production only.** This skill ships a known-ready revision to live production;
it is not a general git, build, CI/CD, staging, or troubleshooting helper.

## Required project contract

Before any mutation, locate documented commands for: production target, deploy,
smoke verification, and rollback. Also identify migration ownership and the
release revision. If deploy, smoke, or rollback is undocumented/ambiguous, stop
and ask; do not infer destructive production commands.

## Workflow

1. Confirm target is production/live and show revision plus deploy, smoke,
   rollback, and migration commands.
2. Check working tree, branch/revision, required credentials, and pre-deploy
   verification. Do not commit, push, stage, stash, or resolve conflicts. The
   one push this skill makes is a live tag (step 7).
3. Run the documented pre-deploy checks. Stop on failure.
4. Run only documented, compatible migrations. Stop on failure; use the project
   rollback plan where appropriate.
5. Deploy the exact revision with the documented production command.
6. Run smoke checks and record evidence. If smoke fails, execute the documented
   rollback procedure when it is safe and authorized by that procedure; report
   the resulting state immediately.
7. If the repository has `docs/verification/modules.json`, record the live
   tags (next section). Otherwise skip this step.

## Live tags (only with `docs/verification/modules.json`)

Run only after smoke passed. For each target deployed in this run (for example
`erp` for hosting, `db` for migrations; use the target names that file uses):

- Tag the exact deployed commit, never a later one:
  `git tag -a live/<target>/<UTC YYYYMMDD-HHMM> <commit> -m "<verdict> <target>"`.
  Take the time from the deploy, in UTC.
- A target whose release carries its own version tag (for example
  `<app>-vX.Y.Z`) keeps that tag; add no live tag for it.
- Push each tag alone: `git push <remote> refs/tags/<tag>`, to the remote the
  release revision came from. Push no branch.
- Run `npm run verify:status -- --no-write` and put its table in the report, so
  the owner sees which commit is live per module and whether it was verified.

## Report

Write Markdown: target, revision, commands/results, migration state, smoke
evidence, rollback state, live tags pushed (with the status table, when step 7
ran), and `PASS`, `CONDITIONAL PASS`, or `FAIL`. Never claim
production success without successful smoke evidence.

## Constraints

Use only commands documented by the project and detect the host OS/shell. Never
assume Bash, a package manager, a cloud provider, or a git remote. Keep secrets
out of output.
