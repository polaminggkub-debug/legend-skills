# Bounded repair and execution budgets

Use this reference when dispatching a job, changing its limits, or interpreting
why a run stopped. The Python worker enforces these limits outside the model.
Calling the raw OpenCode CLI bypasses this policy.

## Defaults and scope

| Setting in `execution_limits` | Default | Scope |
|---|---:|---|
| `max_model_steps` | 100 | Observed model iterations across all attempts |
| `max_wall_seconds` | 3600 | One whole job, including checks and repair attempts |
| `max_repair_attempts` | 2 | Additional model invocations after eligible check failures |
| `check_timeout_seconds` | 600 | Each declared command without an explicit timeout |
| `max_repeated_tool_failures` | 3 | Consecutive identical failed tool actions |
| `max_tokens` | null | Optional observed token threshold |
| `max_cost_usd` | null | Optional observed estimated-cost threshold |

A model step is an iteration within an OpenCode session, not one user task and
not one API transport retry. One initial invocation and two repair invocations
share the same budget; starting a repair does not grant another 100 steps or
another hour. A command uses the smaller of its own timeout and the remaining
job time. A quiet model is not automatically considered stuck.

These are user-selected defaults, not values prescribed by an upstream project.
An explicit existing `default_job_timeout_seconds` remains an additional limit
on an individual model process. Its legacy `null` value does not disable the
new whole-job budget. Existing settings files remain intact on update; missing
`execution_limits` fields receive the defaults above at runtime.

## Repair sequence

1. Run OpenCode with the original task, scope, and project instructions.
2. Execute the committed project's declared checks in their specified order.
3. If a required command exits nonzero, return bounded failure output to OpenCode
   within the original task. This applies before or after source/metadata commits.
4. Recheck the same contract, scope, and source/metadata/check ordering. Stop
   after two additional attempts, on repeated failure without source progress,
   or when the shared budget is exhausted.
5. Save the final outcome, partial work, usage, attempt history, and stop reason.

A missing executable, timed-out command, provider failure, cancellation,
changed contract, unexpected Git revision, or other guard violation does not
start a repair. Deterministic metadata command failures also stop. Optional
checks retain warning semantics. An empty check list stays empty; the worker
does not invent a build or spend a repair attempt on work without checks.

Existing commits are retained, and later repairs create new commits. A commit
is evidence of saved work, not evidence that the final build passed. The final
private report distinguishes these outcomes. Reported total job usage includes
repair attempts; source-commit attribution must not count the same model usage
again in a subsequent source or deterministic metadata commit. Commit duration
trailers are elapsed job snapshots, so do not sum them; use the final job row
for total duration. CSV exports include repair count, stop reason, and effective
step/time limits alongside the existing usage and timing fields.

The coordinator starts one job and consumes its terminal result. It does not
inspect code, write repair prompts, or silently start a new budget after failure.
A new attempt after terminal failure is a new user decision.

## Overrides

Use `worker run --help` for the exact installed CLI options. For an explicit
one-shot/no-repair request, add `--max-repairs 0`. The model-step and wall-time
limits still apply. Normal tasks use the defaults without additional flags.

For persistent machine defaults, set selected fields in the worker's private
`settings.json`, for example:

```json
{
  "execution_limits": {
    "max_model_steps": 100,
    "max_wall_seconds": 3600,
    "max_repair_attempts": 2,
    "check_timeout_seconds": 600
  }
}
```

Merge this object into existing settings; preserve the provider, model, CLI,
and unrelated fields. Do not put API keys in this file. A per-job override
should not alter the saved defaults or another active job.

## Evidence and limits

The five-second local monitor reads process and event information without an AI
request. It can terminate local processes when a limit is observed. This is not
an exact provider billing cap: events arrive after work has started, a poll can
see multiple completed steps, and terminating a local client does not prove
that remote processing or billing stopped immediately. In-flight usage may be
missing from an interrupted report. A token/cost threshold requires relevant
telemetry; unavailable evidence must be reported, not treated as zero. Go cost
estimates do not prove whether quota or Zen balance paid for a request.

Repeated failure detection is deliberately narrow: identical failed tool
input/output patterns, and unchanged source after a failed repair. Successful
repeated reads and silence do not establish a loop. This does not prove useful
progress for every possible agent trajectory; the whole-job limit is the final
bound. The policy cannot guarantee that a model solves the task faster.

## Upstream comparison

Reviewed 2026-09-17 against primary source code and documentation:

- [Aider's reflection loop](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L924-L944)
  caps additional reflections at three. Failed lint/test output can become repair
  feedback. This supports bounded feedback, but that count is not a universal
  recommendation and is separate from API retries and spend limits.
- [mini-SWE-agent's default agent](https://mini-swe-agent.com/latest/reference/agents/default/)
  checks iteration, cost, and wall-time limits before queries and saves its
  trajectory. A between-query check alone cannot interrupt a hung active query;
  the worker also observes its subprocess while running.
- The installed OpenCode 1.18.31's
  [last-step prompt](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/session/prompt.ts#L1276-L1285)
  still passes tools to the model. Its
  [`--auto` permission handling](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/cli/cmd/run.ts#L801-L809)
  can approve permission requests. The worker therefore does not treat a model
  prompt or permission-based doom-loop warning as its hard execution boundary.

This adapts the common pattern of bounded feedback, independent execution
limits, and preserved failure evidence. It does not replace OpenCode's harness
or introduce another model to supervise each heartbeat.
