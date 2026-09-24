# OpenCode Worker

A local CLI that delegates coding through the official OpenCode CLI, then owns
the declared checks, attributed Git commits, and usage report. Python 3.9+,
standard library only. Supported desktop targets: macOS and Windows.

New installations are Go-only and use OpenCode Go (`opencode-go`) with DeepSeek
V4.1 Flash (`deepseek-v4.1-flash`) as the default. In the OpenCode Go console,
enable **Use balance** so Go can continue against available Zen balance after
its quota under the same Go service. That is native Go billing, not a provider
fallback to the separate Zen provider; a Go run does not fall back to
OpenRouter. Existing OpenRouter installations remain supported, and
`openrouter-worker` remains the backwards-compatible alias for the
provider-neutral `opencode-worker` entrypoint. Each provider has a separate
credential, and API keys stay out of prompts, command arguments, and Git.

After [one-time installation](INSTALL_FOR_AI.md), tell Codex:

> ให้ OpenCode แก้งานนี้ แล้วรายงานเวลา โทเค็น ค่าใช้จ่าย และ commit

The coordinating agent constructs the command. You do not need to remember a
CLI invocation. A different model can be selected per run or saved as the
default. OpenCode, OpenRouter, and Codex remain separate products: updating one
does not update the others.

## What runs automatically

1. Check Git state, lock the repository, validate the project's workflow, and
   resolve declared executables **before making a model request**.
2. Start OpenCode, capture events privately, and check the local process every
   five seconds. The Python monitor makes no model or API calls. A shared job
   budget defaults to 100 model steps and 60 minutes, including repair/check time.
3. Run declared `before_commit` checks and create source commit **A**, with
   OpenCode, selected-provider, observed-model, and usage evidence.
4. If declared, run deterministic metadata commands using A as the source
   revision, then create metadata commit **B**. These steps make no worker
   model request and do not count the source tokens again.
5. Run declared `after_commit` checks against the final revision. Save final
   results outside the project so recording a successful build cannot change
   the revision that was just built.

A failed required check may send its output back to OpenCode for at most two
repair attempts within the same job budget. Repeated failure without source
progress stops early. No automatic push, deploy, or recurring Codex task is installed.
The local heartbeat stays private and does not stream repeated status messages to
Codex. Completion is reported in Codex's final turn, which is available on
mobile when the host session is reachable. The worker has no OS-only notifier or
detached completion path. Dispatching through Codex and any tool continuations
consume coordinating turns; the worker makes no claim of zero total Codex token
use. `hello --timeout 10` is a CLI probe, not a coding-job deadline.

## Bounded repairs

The executable enforces the limits; Codex does not supervise each repair.
[The repair and budget reference](references/bounded-repairs.md) explains eligible
failures, shared accounting, overrides, and the polling/billing limits. Say
“ทำรอบเดียว ห้ามแก้ซ้ำ” to dispatch with `--max-repairs 0`. That disables
additional worker sessions, while retaining model-step and wall-time guards.

## Waiting and timing

Use one foreground `run` call and keep its returned handle. When an outer tool
call yields, continue that existing handle or cell; do not start another worker,
read the heartbeat repeatedly, or emit unchanged status. The exact code-mode
continuation recipe, one-shot `wait --run RUN_UUID` recovery rule, Codex/mobile
reporting contract, and optional timing semantics are in
[references/waiting-and-timing.md](references/waiting-and-timing.md).

The existing `elapsed_seconds` value is total wrapper wall time. A
timing-enabled report may include an optional breakdown with phase wall
durations, event-derived tool overlap, and an estimated non-tool interval that
includes model/provider latency and streaming. Timing is supplemental evidence:
it never establishes true TTFT, and unavailable legacy values are unknown
(`null`), not zero. This breakdown requires no new CLI flag.

## Fast dispatch

A dispatched job is only as fast as what it has to figure out on its own. If a
job spends most of its steps exploring — reading source/doc files, poking the
app to find selectors, retrying slowly — fix the dispatch, not the budget: the
orchestrating agent should gather those facts first (ideally with a script,
not a model call) and hand the worker a numbered spec, not a flow to go learn.
[The fast-dispatch reference](references/fast-dispatch.md) covers building
that context pack, writing a spec-style prompt, safe parallelization
(including a verified finding that the repository lock is shared across
worktrees of one repo, so parallel units need separate clones), tight
fail-fast caps, scoped checks, and measuring runs via `runs.sqlite3` against a
baseline.

## First use in a project

The agent runs `inspect --dir PROJECT` and uses project instructions, package
scripts, and CI files to select real checks. Discovery is bounded and
informational: it does not execute candidates or understand every business rule.
If these workflow signals exist without a contract, `run` stops before model
spend. The agent encodes the applicable plan once in a **committed**
`.opencode/worker.json`. A deliberate `checks: []` is valid for work that needs
no build. A plain-file repository without workflow signals needs no contract.

The contract travels with the project. Other sessions and teammates reuse the
same executable plan. A new technology or special release process may need a
project command/adapter once; the generic worker cannot infer hidden policy or
prove arbitrary application correctness.

Project configuration stays isolated from the worker's provider/model setup.
Applicable root-to-working-directory guidance is snapshotted privately and
loaded through OpenCode's explicit `instructions` setting; paths and hashes
are recorded. More specific directory guidance still applies when editing
there. Oversized guidance fails preflight instead of being silently truncated.

Read [the workflow contract](references/workflow.md) when selecting checks or
setting up a source/metadata/final-build sequence. Never copy an example without
checking the project's actual commands. Contract creation is setup work: commit
only the authorized contract changes, and preserve existing user changes in an
isolated worktree when necessary.

## CLI for the coordinating agent

Use the Python and absolute entrypoint recorded by the installer in `SKILL.md`.
In the examples below, `worker` means the provider-neutral `opencode-worker`
entrypoint plus that Python invocation. Existing installations may continue to
use `openrouter-worker` as a compatibility alias.
Legacy installations keep their explicit `openrouter` provider and credential;
the worker never selects it implicitly for a Go run.

```text
worker doctor --dir PROJECT
worker inspect --dir PROJECT
worker auth status --provider opencode-go
worker auth login --provider opencode-go
worker configure --provider opencode-go --model deepseek-v4.1-flash
worker hello --timeout 10
worker run --dir PROJECT --title "Fix navigation" "Implement the requested fix"
worker run --dir PROJECT --model deepseek-v4.1-flash "Implement the requested fix"
worker wait --run RUN_UUID
worker stats --format csv
worker verify --dir PROJECT --commit HEAD
worker cancel --run RUN_UUID
```

`doctor`, `inspect`, `stats`, `verify`, `cancel`, and `auth status` make no model
request. `doctor` checks dependencies/workflow, not application correctness or
provider connectivity. `auth login --provider PROVIDER` uses hidden terminal
input for that provider. Credentials remain separate, and API keys are never
placed in prompts, Git, settings, or command arguments. Legacy OpenRouter
installations may continue to use `OPENROUTER_API_KEY`.

Fresh settings default to `opencode-go/deepseek-v4.1-flash`; configure the
OpenCode Go console's **Use balance** option separately so post-quota requests
can use available Zen balance through Go. A Go run does not silently route to
OpenRouter. `--model` is an explicit per-run override of the installed default
and must use the configured provider. `configure` persists the selected
provider and model. The worker runs OpenCode with isolated config/data roots, so
global OpenCode model settings do not control it. Existing settings are
preserved during updates. No model is silently substituted if observed usage
identifies a different model.

## Results and failure behavior

- **`committed`** means attributed local commits exist. Check `checks.status`
  separately: `passed`, `passed_with_warnings`, or `not_declared`.
- A required check failure still present after bounded repairs returns nonzero.
  Before A, changes remain uncommitted; after A/B, existing commits remain and
  the report identifies the failed stage.
  The worker never resets user work to hide a failure.
- Missing/malformed metrics, a changed contract, unexpected HEAD changes,
  out-of-scope writes, or repository hook rejection stop successful finalization.
- Cancellation and the shared 60-minute job budget are observed locally. Quiet
  output alone is not a stall. Three consecutive identical failed tool actions
  trigger a stop. Each declared command defaults to a ten-minute timeout, bounded
  by the remaining job time; the project can set an explicit command timeout.
  An existing finite `default_job_timeout_seconds` also limits each model process.

Each run records model/provider/version, run ID, elapsed time, input/output/
reasoning/cache tokens, estimated cost, changed files and inserted/deleted lines,
source/final commits, and check results. These are diff line counts, not a claim
that every inserted line is source code. Interrupted runs retain available
completed-step usage as **partial**, never as complete billing. OpenCode cost is
an estimate, not a provider billing receipt; for Go, quota-versus-Zen-balance
billing remains unknown unless the provider emits evidence. The estimate excludes
Codex orchestration and tool-continuation cost.

When present, the optional timing object is read alongside these fields. It
describes observed phase wall durations and an event-tool interval union; the
derived non-tool duration remains an estimate that can include model/provider
waiting and streamed output. Consumers preserve `null` for missing or legacy
timing evidence and reserve zero for a measured zero duration. See the timing
reference for the evidence boundary and source links.

Current source and metadata commits also carry `Provider-ID`, `Billing-Source`,
and `Cost-Basis` trailers. Verification checks them against the source report,
and CSV exports retain those accounting fields. Legacy version 3 records remain
verifiable without the new fields.

`verify` validates committed provenance and statistics. It does **not** rerun
application checks or certify that the change solves the user's problem. The
source report is a pre-commit snapshot; final checks live in the external run
report/database and can be exported for analysis.

## Storage, updates, and boundaries

| Item | Location |
|---|---|
| Maintained source | This repository's `opencode-worker/` directory |
| macOS executable/settings/history | `~/.local/share/codex-openrouter/` |
| Windows executable/settings/history | `%LOCALAPPDATA%/OpenRouterWorker/` |
| Optional state override | `OPENROUTER_WORKER_HOME` |
| Project plan | `.opencode/worker.json` |
| Committed provenance | `.opencode/runs/<run-id>.json` and optional metadata record |
| Final/private results | Worker state `runs/<run-id>/report.json`, logs, `runs.sqlite3` |

Follow [the installer guide](INSTALL_FOR_AI.md) for updates. The installer
preserves settings, credentials, history, and unrelated Codex instructions;
it backs up managed files and refuses unrecognized local edits. A hash manifest
records installed ownership. It does not auto-update OpenCode or download a
model. The source package's `SKILL.md` contains installer substitution markers;
install it with the script, rather than copying that template as a ready skill.

Guards apply to this executable's workflow. Calling raw OpenCode bypasses them.
They detect/report policy violations; they are not an operating-system sandbox
against a hostile agent. Project commands run with the user's privileges and
must be trusted. Do not put model calls inside deterministic metadata/check
commands if you want zero extra model usage from those stages.

The upstream comparison and its limits are recorded in
[the architecture review](references/upstream-review.md).
The OpenCode Go model-switching and balance evidence is recorded in
[the Go research note](references/go-balance-model-switching-research.md).

## Development

```text
python -m unittest discover -s opencode-worker/tests -v
```

Tests use temporary Git repositories and a fake OpenCode CLI. They cover runtime
behavior and failure modes without provider credits. GitHub Actions runs the
same suite on macOS and Windows. Real model quality, changing provider APIs,
and every possible project workflow are outside these offline tests.
