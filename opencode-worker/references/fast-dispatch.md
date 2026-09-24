# Fast dispatch

Use this when a job is running much slower or costlier than it should. A real
job (three Playwright walkthrough test files) took over 75 minutes and 160+
model steps on a fast model because the worker spent most of its steps
exploring: reading around ten source/doc files, launching the app with ad-hoc
scripts to discover button names, and retrying slowly. Fix this before the
job runs, not during it: the orchestrator (the expensive model driving this
skill) does the exploring, and the worker only writes.

## 1. Context pack first

Before dispatch, gather the facts the worker would otherwise explore. Prefer a
script over a model call for this — it is cheaper and more reliable:

- For UI/E2E tests: a small Playwright script that plays the target flow and
  dumps `await locator.ariaSnapshot()` after each step to a file, so the
  worker gets real selectors and labels instead of guessing them.
- Exact file paths to edit or create.
- Exact commands (install, run, check).

Put the pack inline in the prompt, or save it to a file and name that file in
the prompt. Either way, the worker must not need to run its own discovery
commands to get this information.

## 2. Prompt is a spec, not research

Write the prompt as a checklist of concrete, individually-verifiable
acceptance items, not a description of a flow to go learn. Name at most ~5
files the worker may read, and say explicitly "do not explore beyond these."

Avoid: "learn the login flow from `LoginPage.vue`, `auth.ts`, and the E2E
README, then write a test for it."

Prefer: "write `tests/e2e/login.spec.ts`. Steps: 1) goto `/login` 2) fill
`#email` with `test@example.com` 3) fill `#password` with `Password1` 4) click
the button labeled 'Sign in' (see `references/login-snapshot.txt` line 12) 5)
expect URL `/dashboard`. Read only `tests/e2e/fixtures.ts` and
`playwright.config.ts` if you need setup. Do not explore beyond these."

## 3. One unit per job; parallelize across separate clones, not worktrees of the same repo

Give each job exactly one independent unit of work, and run independent units
concurrently when there is more than one — each in its own clean tree via
`--dir`.

**Verified finding: the worker's repository lock is keyed on
`git rev-parse --git-common-dir`, not on the worktree path** (see
`worker_job.py`, `RepositoryLock` in `worker_platform.py`). For a repo checked
out with `git worktree add`, every worktree shares the same `--git-common-dir`
(the main checkout's `.git`), so two `worker run` calls against two worktrees
of the *same* repository still collide: the second fails immediately with
"Another audited OpenCode worker is using this repository," and the lock is
held for the whole job (acquired before the model runs, released only in the
job's `finally`), not just around the commit.

To actually run jobs in parallel, give each unit its own **separate `git
clone`** (each clone has its own `.git`, hence its own `--git-common-dir` and
its own lock) rather than worktrees of one shared repo. A worktree still
works for isolating file changes in a single, sequential job.

Separately, `configure` (which sets the saved default provider/model) refuses
outright while *any* run tracked by this installation is active, regardless
of which directory it targets; use `worker wait --run RUN_UUID` to recover a
known active run before changing configuration.

## 4. Tight caps, fail fast

Per unit, start around `--max-job-seconds 1800 --max-model-steps 80`. If a job
hits the cap, treat that as a signal that the context pack or prompt was
under-specified — fix those and redispatch, rather than raising the caps on
the same pack.

## 5. Fast checks

Scope the job's checks to what the unit actually touches; do not run the
whole suite for a one-file change. Reuse an already-running dev server when
the test config allows connecting to one instead of starting a new one, and
keep assertion timeouts short so a real failure surfaces quickly instead of
stalling out the job's wall-clock budget.

## 6. Isolate from other heavy work

Do not run a dispatch alongside other heavy jobs (benchmarks, full test
suites) on the same machine; they compete for CPU and skew both jobs' timing.

## 7. Model choice

The default model is whatever the last `configure --provider opencode-go
--model <m>` set (only change this when the owner asks); override per job
with `--model` on `worker run`. A well-specified context pack and a narrow
spec (points 1-2) suit a fast "flash"-class model well — the model does not
need to explore, so it does not need to reason as much.

## 8. Measure every run

Record, per run: wall seconds, model steps, estimated cost, and check
pass/fail. The report already carries these fields (`elapsed_seconds`,
`metrics`, `checks.status`, `budget`); `runs.sqlite3` (table `runs`, columns
`run_id`, `status`, `report_json`) stores every run's full report, so query it
directly instead of re-deriving these numbers:

```sql
select run_id, status, json_extract(report_json, '$.elapsed_seconds'),
       json_extract(report_json, '$.metrics'),
       json_extract(report_json, '$.checks.status')
from runs order by rowid desc limit 20;
```

`worker_attempt_stats.py` aggregates telemetry *within* one run across its
repair attempts; it is not a cross-run comparison tool, so use the query above
(or the CLI's own report/CSV export) to compare runs against a baseline.
Baseline example from the job that motivated this section: 3 test files, a
fast model, over 75 minutes, 160+ model steps.
