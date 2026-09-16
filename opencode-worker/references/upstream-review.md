# Upstream architecture review

Checked 2026-09-15. I recorded the branch refs with `git ls-remote` and used the
official repository pages and documentation below. GitHub star counts are UI
snapshots and are intentionally approximate.

| Project | Checked ref | Approx. stars at check | Primary evidence |
| --- | --- | ---: | --- |
| [anomalyco/opencode](https://github.com/anomalyco/opencode) | `v1.18.31` `014614d35b397775e5d397a490fc72368c894ec2` | ~207k | [commit](https://github.com/anomalyco/opencode/commit/014614d35b397775e5d397a490fc72368c894ec2) |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | `main` `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` | ~49k | [commit](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c) |
| [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) | `main` `b054a2fe99173baee47897e4f3af7a910d3aab1e` | ~1.1k | [commit](https://github.com/OpenHands/software-agent-sdk/commit/b054a2fe99173baee47897e4f3af7a910d3aab1e) |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | `main` `82203bb1011cdf0e6eb318a32111806a6f6f734a` | ~88k | [commit](https://github.com/OpenHands/OpenHands/commit/82203bb1011cdf0e6eb318a32111806a6f6f734a) |

The comparison is structural. It is evidence about boundaries and documented
behavior, not a benchmark, a billing audit, or proof that any implementation
automatically preserves semantic intent.

For the authorized OpenCode Go migration, see the source-backed
[Go balance and model switching research](go-balance-model-switching-research.md).
It points to the pinned OpenCode CLI/model seams and the official Go **Use
balance** behavior; those sources support the provider and billing policy, not
unstated worker APIs.

| Concern | Local `opencode-worker` | Upstream evidence | Assessment |
| --- | --- | --- | --- |
| Waiting while a job runs | `worker_runtime.py` starts one child process and `worker_monitor.py` waits on `Popen`, recording a private atomic heartbeat on each local interval. The monitor has no model or network path. | OpenCode's [session processor](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/session/processor.ts) handles step events and usage; Aider's [scripting interface](https://aider.chat/docs/scripting.html) sends one message and exits; the [OpenHands main repository](https://github.com/OpenHands/OpenHands/blob/82203bb1011cdf0e6eb318a32111806a6f6f734a/README.md) describes local-stack orchestration while its [SDK quick start](https://github.com/OpenHands/software-agent-sdk/blob/b054a2fe99173baee47897e4f3af7a910d3aab1e/README.md) calls `conversation.run()` for the agent/tool loop. | A local process/event wait seam is complementary to an agent's model loop. It should be judged by child lifecycle and heartbeat tests, not by prompt quality. |
| Prompts and project instructions | The launcher supplies a fixed wrapper prompt, selected agent/model, and a bounded private snapshot of selected project guidance with source hashes. Project discovery reports candidates; the committed contract selects executable checks. | OpenCode documents that [project `AGENTS.md` rules enter model context](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/web/src/content/docs/rules.mdx), while its [instruction loader](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/session/instruction.ts) gates startup/system project-rule lookup on `OPENCODE_DISABLE_PROJECT_CONFIG`. Aider makes file context explicit and supports one-shot `--message` in its [usage](https://aider.chat/docs/usage.html) and [scripting](https://aider.chat/docs/scripting.html) docs. OpenHands passes an explicit agent, tools, and workspace in its [SDK example](https://github.com/OpenHands/software-agent-sdk/blob/b054a2fe99173baee47897e4f3af7a910d3aab1e/README.md). | Explicit context and a committed project plan are the right control points. The snapshot gives the model bounded guidance while the disabled project-config flag keeps project config/plugins out of startup loading. |
| `--pure` and configuration isolation | The runtime invokes `run --pure` and also sets `OPENCODE_DISABLE_PROJECT_CONFIG`, `OPENCODE_DISABLE_EXTERNAL_SKILLS`, and related environment controls. | OpenCode's [CLI entry point](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/index.ts) maps `--pure` to `OPENCODE_PURE`, whose documented purpose is to run without external plugins. Its [config loader](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/config/config.ts) and [instruction loader](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/session/instruction.ts) treat `OPENCODE_DISABLE_PROJECT_CONFIG` separately. | `--pure` is not a synonym for “ignore project rules.” The additional project-config flag is a deliberate security choice but also suppresses tracked `AGENTS.md`/`CLAUDE.md` discovery; see the resolved mechanism below. |
| Project checks and policy | `.opencode/worker.json` contains explicit argv, cwd, stage, timeout, required, scope, and optional handoff metadata. Commands are resolved and validated before model spend and run later without shell interpolation. Discovery remains informational and never claims a candidate passed. | Aider exposes configurable [test/lint and commit options](https://aider.chat/docs/git.html). OpenHands' [development guide](https://github.com/OpenHands/software-agent-sdk/blob/b054a2fe99173baee47897e4f3af7a910d3aab1e/DEVELOPMENT.md) names repository-specific format, lint, pre-commit, and pytest commands. OpenHands' SDK is a general agent/workspace API, not a universal test policy. | A project-owned contract is safer than guessing one test command for every repository. Candidate discovery can guide setup, but only declared checks can support a delivery claim. |
| Session and usage persistence | The launcher keeps private JSONL events, a run report, a local SQLite index, and model attribution from OpenCode's data store. Metrics sum only validated completed step-finish records; partial accounting is labeled as such, and the report says its cost is an OpenCode estimate rather than a provider receipt. | OpenCode's [step processor](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/session/processor.ts) records step usage/cost, and its [stats command](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/cli/cmd/stats.ts) aggregates session tokens and cost. OpenHands documents durable [base state, event files, and statistics](https://docs.openhands.dev/sdk/guides/convo-persistence), and its [state model](https://github.com/OpenHands/software-agent-sdk/blob/b054a2fe99173baee47897e4f3af7a910d3aab1e/openhands-sdk/openhands/sdk/conversation/state.py) keeps event/state persistence separate. Aider's [coder state](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py) tracks conversation history, tokens, and cost in its own process. | Persisting run identity, events, usage, and hashes is the right audit direction. It still cannot turn an interrupted stream into a complete billing record or establish that the model obeyed a requested change. |
| Git and delivery stages | The launcher requires a clean repo, locks the repository, blocks worker-side Git hooks, checks HEAD and scope, runs before-commit checks, writes a hashed report, creates an attributed source commit, optionally creates a direct metadata handoff commit, then runs after-commit checks. | Aider's [Git integration](https://aider.chat/docs/git.html) auto-commits its edits and can commit pre-existing dirty files separately. OpenHands describes the contributor sequence as [branch, change, checks, push, pull request](https://github.com/OpenHands/software-agent-sdk/blob/b054a2fe99173baee47897e4f3af7a910d3aab1e/DEVELOPMENT.md), with pre-commit hooks on commit. These are different product policies; neither is evidence that OpenCode supplies this wrapper's staged delivery contract. | The staged source/metadata boundary is a reasonable local policy for attributed delivery. It is a custom composition, not an upstream guarantee or a copied Aider/OpenHands workflow. |
| Implementation language | The boundary is Python 3.9+ standard library, with subprocess, filesystem, JSONL, SQLite, and Git seams kept local. | Aider is Python; OpenHands explicitly provides Python and TypeScript APIs; OpenCode's inspected implementation is TypeScript. | Python is not inherently the cause of a long-running job. Provider/model latency, child-process work, tool commands, and orchestration dominate elapsed time; the important property is that waiting is observable and does not spend another model request. |

The evidence supports the direction: keep model execution, local process observation,
validated project policy, persisted usage, and Git delivery as separate seams. The
upstream projects demonstrate related pieces, but they do not establish an
identical end-to-end A-to-B design. A passing local check proves only that the
declared command exited as expected; it does not prove semantic correctness,
complete provider billing, or instruction compliance.

The Go research also supports treating provider selection, local waiting, and
usage evidence as separate seams. OpenCode Go's post-quota Zen-balance behavior
is a native same-service billing rule; it is not evidence for an OpenRouter
failover path. Keep the worker's selected provider and observed billing evidence
in the final report when the provider exposes them.

## Resolved findings and remaining limits

1. **Pinned OpenCode has a native instruction seam that preserves isolation.**
   In v1.18.31, `OPENCODE_DISABLE_PROJECT_CONFIG=true` suppresses automatic
   project `AGENTS.md`/`CLAUDE.md` lookup during startup/system assembly. However, the same pinned
   [`instruction.ts`](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/src/session/instruction.ts#L123-L140)
   resolves absolute entries in `config.instructions` through its absolute-path
   branch, independently of that flag, and then reads them into the model's
   system instructions. The official [config docs](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/web/src/content/docs/config.mdx#L815-L823)
   document `instructions` as file paths/globs; their [path notes](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/web/src/content/docs/config.mdx#L939-L942)
   include absolute paths.

   The launcher now snapshots the bounded project instruction files it
   selected, records each source path and hash before the paid call, and sets
   `OPENCODE_CONFIG_CONTENT` to a JSON object such as
   `{"instructions":["/absolute/run-dir/instructions.md"]}` while retaining
   `OPENCODE_DISABLE_PROJECT_CONFIG=true` and `--pure`. A relative
   `"AGENTS.md"` entry is unsafe for this purpose: the pinned resolver routes
   relative entries to the isolated global config directory when the flag is set.
   The resolver's separate tool-read path can still attach nearby instruction files
   while a file is read, so the flag is not a universal semantic guarantee; the
   coordinator should test and record the intended bounded instruction set.
   The absolute path must be coordinator-controlled and inside the private run
   directory; this is provenance and containment policy supplied by the launcher,
   not a guarantee provided by OpenCode.

2. **Metrics remain conservative around interrupted streams.**
   Usage sums only validated completed `step-finish` records. If there are no
   completed steps, usage and cost remain unavailable in the empty metrics object;
   no zero usage is invented. Partial parsing marks `completed: false`, since an
   abnormal process exit supplies no proof of a terminal stop. Only the explicitly
   partial path may interpret an invalid unterminated trailing record as a truncated
   write; strict parsing still rejects it and validates complete records. These
   semantics describe accounting limits, not provider billing guarantees.
   Strict parsing now rejects a new step after a terminal stop; identical repeated
   finish events are still deduplicated without double-counting usage.

3. **The pinned Windows npm entry point is a native executable behind a shim.**
   The exact [npm registry manifest for `opencode-ai@1.18.31`](https://registry.npmjs.org/opencode-ai/1.18.31)
   declares `bin/opencode.exe`. OpenCode's pinned
   [`postinstall.mjs`](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/script/postinstall.mjs#L23-L29)
   selects `opencode.exe` for Windows and copies the selected optional native
   package into that path before verifying it with `--version`
   ([selection and copy](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/script/postinstall.mjs#L96-L139),
   [verification](https://github.com/anomalyco/opencode/blob/014614d35b397775e5d397a490fc72368c894ec2/packages/opencode/script/postinstall.mjs#L146-L163)).
   npm documents that Windows installs create a `.cmd` file for a package's
   `bin` entry, and the pinned [`cmd-shim`](https://github.com/npm/cmd-shim/blob/v8.0.0/lib/index.js)
   source says a target without a shebang is treated as a compiled executable and
   called directly ([target selection](https://github.com/npm/cmd-shim/blob/v8.0.0/lib/index.js#L38-L55),
   [direct command form](https://github.com/npm/cmd-shim/blob/v8.0.0/lib/index.js#L67-L73)).
   The shell-free resolver should therefore verify the shim's trusted
   `opencode-ai/bin/opencode.exe` reference, package manifest, and PE `MZ` header,
   then execute the native path directly with `shell=False`; it should reject
   arbitrary `.cmd`/`.bat` files and never route this entry point through
   `cmd.exe`. Node-backed resolution remains appropriate only for genuinely
   script-backed shims such as `npm.cmd`.

## Validation limits

- The upstream refs and star counts are time-sensitive. Stars are rounded here;
  the exact branch SHAs are recorded so the source links remain reviewable.
- This review used official GitHub source/docs and did not run an upstream agent,
  make a model request, or inspect credentials or source payloads.
- No claim is made that a future OpenCode release preserves the inspected CLI or
  environment semantics. In particular, the launcher should keep a pinned CLI
  probe and tests for `--pure`, project-rule loading, data-directory placement,
  Windows shims, and interrupted event streams.
