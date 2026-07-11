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
   verification. Do not commit, push, stage, stash, or resolve conflicts.
3. Run the documented pre-deploy checks. Stop on failure.
4. Run only documented, compatible migrations. Stop on failure; use the project
   rollback plan where appropriate.
5. Deploy the exact revision with the documented production command.
6. Run smoke checks and record evidence. If smoke fails, execute the documented
   rollback procedure when it is safe and authorized by that procedure; report
   the resulting state immediately.

## Report

Write Markdown: target, revision, commands/results, migration state, smoke
evidence, rollback state, and `PASS`, `CONDITIONAL PASS`, or `FAIL`. Never claim
production success without successful smoke evidence.

## Constraints

Use only commands documented by the project and detect the host OS/shell. Never
assume Bash, a package manager, a cloud provider, or a git remote. Keep secrets
out of output.
