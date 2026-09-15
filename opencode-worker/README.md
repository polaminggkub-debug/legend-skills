# OpenCode Worker

A local CLI that delegates coding to **OpenCode → OpenRouter → your selected
model**, then owns the declared checks, attributed Git commits, and usage report.
Python 3.9+, standard library only. Supported desktop targets: macOS and Windows.

After [one-time installation](INSTALL_FOR_AI.md), tell Codex:

> ให้ OpenCode แก้งานนี้ ทำรอบเดียว แล้วรายงานเวลา โทเค็น ค่าใช้จ่าย และ commit

The coordinating agent constructs the command. You do not need to remember a
CLI invocation. A different model can be selected per run or saved as the
default. OpenCode, OpenRouter, and Codex remain separate products: updating one
does not update the others.

## What runs automatically

1. Check Git state, lock the repository, validate the project's workflow, and
   resolve declared executables **before making a model request**.
2. Start one OpenCode CLI session. Capture events privately and check the local
   process every five seconds. There is no default total job timeout.
3. Run declared `before_commit` checks and create source commit **A**, with
   OpenCode/OpenRouter attribution, actual observed model, and usage evidence.
4. If declared, run deterministic metadata commands using A as the source
   revision, then create metadata commit **B**. These steps make no worker
   model request and do not count the source tokens again.
5. Run declared `after_commit` checks against the final revision. Save final
   results outside the project so recording a successful build cannot change
   the revision that was just built.

No automatic repair, retry, push, deploy, or recurring Codex task is installed.
The local heartbeat makes no model/API calls and does not stream repeated status
messages to Codex. Dispatching through Codex still consumes the coordinating
turn's tokens; an installed skill and short global registration also have some
discovery/context overhead. This is not a claim of zero total Codex overhead.

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

Read [the workflow contract](references/workflow.md) when selecting checks or
setting up a source/metadata/final-build sequence. Never copy an example without
checking the project's actual commands. Contract creation is setup work: commit
only the authorized contract changes, and preserve existing user changes in an
isolated worktree when necessary.

## CLI for the coordinating agent

Use the Python and absolute entrypoint recorded by the installer in `SKILL.md`.
In the examples below, `worker` means that two-part invocation, not another
installed shell command.

```text
worker doctor --dir PROJECT
worker inspect --dir PROJECT
worker run --dir PROJECT --title "Fix navigation" "Implement the requested fix"
worker run --dir PROJECT --model provider/model-id "Implement the requested fix"
worker stats --format csv
worker verify --dir PROJECT --commit HEAD
worker cancel --run RUN_UUID
worker auth status
worker auth login
```

`doctor`, `inspect`, `stats`, `verify`, `cancel`, and `auth status` make no model
request. `doctor` checks dependencies/workflow, not application correctness or
provider connectivity. `auth login` uses hidden terminal input and stores the
key in macOS Keychain or Windows Credential Manager. `OPENROUTER_API_KEY` is
also supported. Never put a key in prompts, Git, settings, or command arguments.

Fresh settings default to `deepseek/deepseek-v4.1-flash`; model availability is
controlled by OpenRouter and is not guaranteed by the wrapper. `--model` selects
an OpenRouter model ID. `--variant` passes an OpenCode variant. Existing settings
are preserved during updates. No model is silently substituted if observed
usage identifies a different model.

## Results and failure behavior

- **`committed`** means attributed local commits exist. Check `checks.status`
  separately: `passed`, `passed_with_warnings`, or `not_declared`.
- A required check failure returns nonzero. Before A, changes remain uncommitted;
  after A/B, existing commits remain and the report identifies the failed stage.
  The worker never resets user work to hide a failure.
- Missing/malformed metrics, a changed contract, unexpected HEAD changes,
  out-of-scope writes, or repository hook rejection stop successful finalization.
- Cancellation is observed locally. The default permits long quiet jobs; process
  liveness is not proof of useful progress. There is no automatic stall detector.
  An optional finite `default_job_timeout_seconds` limits the model process;
  individual contract steps have their own optional timeout.

Each run records model/provider/version, run ID, elapsed time, input/output/
reasoning/cache tokens, estimated cost, changed files and inserted/deleted lines,
source/final commits, and check results. These are diff line counts, not a claim
that every inserted line is source code. Interrupted runs retain available
completed-step usage as **partial**, never as complete billing. OpenCode cost is
an estimate, not an OpenRouter receipt; it excludes Codex orchestration cost.

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

## Development

```text
python -m unittest discover -s opencode-worker/tests -v
```

Tests use temporary Git repositories and a fake OpenCode CLI. They cover runtime
behavior and failure modes without provider credits. GitHub Actions runs the
same suite on macOS and Windows. Real model quality, changing provider APIs,
and every possible project workflow are outside these offline tests.
