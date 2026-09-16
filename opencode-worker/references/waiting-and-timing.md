# Waiting and timing

Use this guide when a worker run is still active, a native tool call yields, a
final report is missing, or a run report needs its timing breakdown interpreted.
The worker owns one foreground OpenCode process. Its Python monitor records a
private heartbeat every five seconds without a model or API request. The default
total job timeout is `None`, so a quiet job can run longer than twenty minutes.
No recurring Codex task, MCP server, or background notifier is involved.

## Continue one wait

Start one `worker run` call and keep the returned process handle. For the
code-mode continuation used by this host, put the longer outer wait directive on
the first line and leave a margin inside `write_stdin`:

```javascript
// @exec: {"yield_time_ms":60000,"max_output_tokens":1500}
text(await tools.write_stdin({session_id:SESSION_ID,chars:"",yield_time_ms:55000,max_output_tokens:1500}));
```

Replace `SESSION_ID` with the session ID returned by the existing worker call.
The observed nested-tool trace has a 30-second default outer `functions.exec`
wait around a 60-second `write_stdin`; the outer wait can yield while the inner
wait is still open and cause an unnecessary `functions.wait` inference. The
55/60-second values are host-tool tuning for this code mode, not an upstream
standard. Python can keep the worker's local heartbeat and process wait quiet,
but it cannot enforce a model-host cadence or promise zero coordinator-token
usage.

A provider-free boundary check with a synthetic 45-second local process showed
the difference: the default 30-second outer wait around a 55-second nested wait
needed a later cell continuation, while the 60-second outer directive with the
55-second inner wait completed in one `functions.exec` call. This is host-boundary
evidence for fewer continuations, not a general token-saving or completion-time
guarantee.

If the outer `functions.exec` returns `Script running with cell ID ...`, resume
that same cell with `functions.wait` using the returned cell ID. Keep the worker
process session ID for the next `write_stdin`; do not invoke a new shell command
or start a second worker. If the resumed result still has a running
`session_id`, repeat the same bounded 60-second outer directive and 55-second
inner `write_stdin` against that session until the process actually exits. Use
the same cell first whenever the outer call yielded, and keep at most one wait
active for the session; never start concurrent waits or turn this into one
unbounded tool call. A completed cell or process is the completion criterion:
consume its final report once. While the state is unchanged, leave the private
heartbeat alone and send no repeated status message.

## Consume the final report

At process exit, read the compact JSON result and the report path once. Treat
`status=committed` or `status=no_changes` as delivery outcomes, then inspect
`checks.status` separately (`passed`, `passed_with_warnings`, or
`not_declared`). Preserve the run ID, commit(s), provider/model, elapsed time,
usage, changed-file and diff-line counts, and check results in the Codex turn.

If the wrapper crashes, exits nonzero, or has no readable finalized report,
report failure or unknown in Codex. When a `RUN_UUID` is available and the
worker may still be finalizing, run this local recovery command once:

```text
worker wait --run RUN_UUID
```

Consume the returned terminal report, including its failure status, and stop.
There is no rerun or automatic repair path. If no run ID or final report exists,
keep the outcome unknown and state the evidence that is missing. A failed check
or failed delivery stage remains a failure even when an earlier source commit
exists; distinguish the commit from the application-check result.

The Codex turn is the completion and failure reporting surface on desktop and
mobile when the host session is reachable. A disconnected host cannot guarantee
mobile delivery. The worker has no OS-only notification or detached completion
mode, so keep the final status, report path, and recovery result in Codex.

## Read optional timing fields

The existing top-level `elapsed_seconds` is total wrapper wall time from run
start through finalization. A timing-enabled report may add an optional
`timing` object with these fields:

- `elapsed_seconds`, the same total wall duration, and `active_phase`, which is
  `null` in the finalized private report;
- `phases_seconds`, a map of phase wall durations measured by the local
  monotonic clock, such as `preflight`, `model`, `before_commit`, `metadata`,
  `after_commit`, `commit`, and `finalize`; and
- `events`, including `model_steps`, `tool_execution_seconds` for the
  event-derived tool interval union, `non_tool_seconds` for the derived
  estimate, and `availability` for event coverage.

Overlapping tool intervals count once in `tool_execution_seconds`, rather than
once per event. The committed source report is a pre-commit snapshot, so its
`active_phase` can still identify the phase in progress; inspect the finalized
private report for the terminal `null` value.

The non-tool estimate includes model/provider waiting, streamed output, and
other orchestration that is outside the event-derived tool intervals. It is an
estimate, never true time-to-first-token (TTFT). Event timestamps and process
clocks do not prove TTFT, and the report must not label this estimate as TTFT.
The event breakdown describes work inside the `model` phase; do not add it to
the phase totals again. Model-phase wall time also includes CLI startup and
shutdown outside the event span.

Timing is report metadata and requires no new CLI command or flag. Consumers
should treat missing timing evidence in legacy reports as `null` (unknown),
never as `0`. A zero is meaningful only when instrumentation measured a real
zero-duration phase. Missing event timestamps, malformed intervals, and a
phase that did not run remain unknown. Timing does not change commit or check
status. If timing collection itself fails, `timing.availability` is
`unavailable`, its durations are `null` or absent, and the existing top-level
elapsed duration and delivery/failure report are preserved.

The evidence boundary is deliberate:

- OpenCode's pinned [`run.ts`](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/cli/cmd/run.ts#L657-L752)
  shows the native event stream and completion/idle boundary. It supports
  event-based observation, not a promise about Codex host wake cadence.
- OpenHands' [`remote_conversation.py`](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py)
  provides a comparable events-first, polling-fallback observation seam; it is
  not an API contract for this local worker.
- [Codex issue #42981](https://github.com/openai/codex/issues/42981) records a
  user-observed 60-second update/wait behavior. It is an issue report, not
  maintainer evidence that every host uses that cadence.
