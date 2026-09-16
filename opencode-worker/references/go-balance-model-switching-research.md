# Go balance and model switching research

Checked 2026-09-16. This is a bounded comparison of official source/docs at
these refs: [OpenCode `e03db9b`](https://github.com/anomalyco/opencode/tree/e03db9bc6908f75c9334d8aa997deeaac81c0298),
[Pi `6671c60`](https://github.com/earendil-works/pi/tree/6671c604766b3670ed95f405aa7856835d0ca702),
and [OpenHands SDK `22c85eb`](https://github.com/OpenHands/software-agent-sdk/tree/22c85eb0e0db8f4386380d095e9fe6933af2e65f).
No OpenCode coding worker was launched and no paid provider request was made.

## Verified upstream behavior

OpenCode has a first-class headless seam. Its CLI documents `opencode run
[message..]`, per-run `--model provider/model`, `--format json` for raw event
output, and `--attach` to a running headless server ([CLI docs](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/web/src/content/docs/cli.mdx#L339-L385)).
The inspected `run.ts` creates or resumes a session, subscribes to one event
stream, mirrors completed text/tool/step parts, and ends its event loop when
the session reports `idle` ([source](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/opencode/src/cli/cmd/run.ts#L456-L560),
[completion loop](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/opencode/src/cli/cmd/run.ts#L600-L730)).
The same CLI exposes `opencode models` and `opencode stats` for model discovery
and token/cost statistics ([CLI docs](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/web/src/content/docs/cli.mdx#L325-L345),
[stats](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/web/src/content/docs/cli.mdx#L447-L462)).
Provider setup is separate from the model reference: the provider docs cover
OpenCode Zen and OpenRouter credentials, and custom providers expose endpoint,
key, headers, and model entries ([Zen/OpenRouter](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/web/src/content/docs/providers.mdx#L87-L110),
[custom provider](https://github.com/anomalyco/opencode/blob/e03db9bc6908f75c9334d8aa997deeaac81c0298/packages/web/src/content/docs/providers.mdx#L2616-L2645)).

One limitation matters for an unattended supervisor: an OpenCode repository
issue reports a headless `run` process remaining alive after a non-retryable
monthly-quota error ([issue #42268](https://github.com/anomalyco/opencode/issues/42268)).
That is an issue report, not a guarantee about every release, but it supports
retaining explicit terminal-error detection and cancellation outside the CLI.
It does not justify restoring the arbitrary 20-minute job cutoff rejected by
the user.

Pi (the `badlogic/pi-mono` URL now resolves to the maintained
`earendil-works/pi` repository) provides the same broad integration shapes:
print-and-exit mode, JSON event mode, and RPC mode; `--provider` and
`--model` accept provider/model selection ([README](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/coding-agent/README.md#L631-L655)).
Its JSON mode emits session events as JSON lines, including `agent_end` and
the stronger `agent_settled` event that follows retries, compaction retries,
and queued continuations ([JSON event docs](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/coding-agent/docs/json.md#L1-L29),
[settled event](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/coding-agent/docs/rpc.md#L860-L911)).
RPC also exposes `set_model`, `get_available_models`, and JSONL command/event
framing ([RPC model commands](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/coding-agent/docs/rpc.md#L238-L299),
[RPC framing](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/coding-agent/docs/rpc.md#L215-L232)).
At the lower-level agent API, `waitForIdle()` resolves after `agent_end`
listeners settle, while a new prompt is rejected during an active run
([agent source](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/agent/src/agent.ts#L240-L253),
[wait/prompt](https://github.com/earendil-works/pi/blob/6671c604766b3670ed95f405aa7856835d0ca702/packages/agent/src/agent.ts#L318-L358)).

OpenHands SDK is an in-process alternative rather than a CLI wrapper. Its
official quick start constructs an `LLM`, `Agent`, and `Conversation`, queues
a message, calls blocking `conversation.run()`, and continues after it
returns ([README](https://github.com/OpenHands/software-agent-sdk/blob/22c85eb0e0db8f4386380d095e9fe6933af2e65f/README.md#L13-L52)).
The base contract says `run()` processes the current message until completion
or the iteration limit ([base interface](https://github.com/OpenHands/software-agent-sdk/blob/22c85eb0e0db8f4386380d095e9fe6933af2e65f/openhands-sdk/openhands/sdk/conversation/base.py#L198-L225)).
`LocalConversation` accepts event and token callbacks; its default callback
persists events before user callbacks are called ([local conversation](https://github.com/OpenHands/software-agent-sdk/blob/22c85eb0e0db8f4386380d095e9fe6933af2e65f/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L212-L245),
[callback chain](https://github.com/OpenHands/software-agent-sdk/blob/22c85eb0e0db8f4386380d095e9fe6933af2e65f/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L417-L483)).
Its state names `FINISHED`, `ERROR`, and `STUCK` as terminal, with explicit
`PAUSED` and `WAITING_FOR_CONFIRMATION` states ([state enum](https://github.com/OpenHands/software-agent-sdk/blob/22c85eb0e0db8f4386380d095e9fe6933af2e65f/openhands-sdk/openhands/sdk/conversation/state.py#L48-L79)).
The SDK includes explicit model/profile switching and per-profile usage
metrics: the example switches profiles between two `run()` calls and reports
metrics per model ([switching example](https://github.com/OpenHands/software-agent-sdk/blob/22c85eb0e0db8f4386380d095e9fe6933af2e65f/examples/01_standalone_sdk/44_model_switching_in_convo.py#L15-L49)).

## Fit with the authorized design

The evidence supports the current boundary. A coordinator can launch one
headless child, let that child own the agent/model loop, wait on the child
process, and retain the event stream for usage and completion evidence. This
matches OpenCode's event subscription and idle completion, Pi's settled event,
and OpenHands' blocking run/callback model. That conclusion is a design
inference from the cited interfaces, not a claim that the projects share one
protocol.

The five-second Python monitor is also the right kind of seam for this goal:
the installed monitor records a private atomic heartbeat and waits on the
child process with a bounded local interval; its module and implementation
contain no model request path ([worker monitor](https://github.com/polaminggkub-debug/legend-skills/blob/f08389d66637ef4f49a6e681aa6c18898ee2b88f/opencode-worker/scripts/worker_monitor.py#L1-L96)).
The coordinator therefore does not need repeated LLM status prompts. It still
needs terminal-state handling and cancellation because process liveness is
not proof of useful progress. Any optional stall or job timeout must have an
explicit policy; elapsed time alone must not terminate a legitimate long job.
The outer Codex tool may still yield and require continuation; reducing those
wakeups must not be represented as proven zero coordinator-token overhead.

Usage metadata and attributed source/metadata commits remain local delivery
policy. The upstream projects expose useful usage/events or persistence, but
the inspected sources do not promise this exact commit staging and provenance
contract; keep those checks in the wrapper and do not infer semantic
correctness from a clean process exit. This is an inference from the cited
upstream interfaces and the local worker contract.

## Model-switching consequence

At the OpenCode CLI layer, switching a future run is mechanically simple:
pass another `provider/model` value, after that provider is configured and
authenticated. The same is true for Pi's `--model`; Pi additionally has an
RPC `set_model` for a live session. OpenHands can swap an `LLM` or saved
profile between runs, but adopting that SDK would be an engine change and is
outside this comparison.

The migration crosses four coordinated seams: provider credential lookup,
isolated OpenCode configuration, model normalization, and report attribution.
A global OpenCode config edit cannot switch an isolated worker to
`opencode-go`; provider and model selection must be explicit at the worker job
boundary. This note records the upstream interfaces and billing behavior; the
exact worker API and settings schema belong to the coordinated implementation.

The authorized `opencode-go/deepseek-v4.1-flash` default and Zen-balance/quota
policy should be treated as one provider/accounting contract. The official
[Go documentation](https://opencode.ai/docs/go/#usage-beyond-limits) explicitly
states that enabling Use balance continues requests against available Zen
balance after Go limits are reached. This is native service billing behavior,
not a client-side switch to the separate Zen provider. The same page lists
DeepSeek V4.1 Flash and the Go endpoint. Therefore this plan does not need an
OpenRouter failover chain. No paid account-specific overflow test was made;
credit availability and billing limits still apply.

Keep the explicit no-OpenRouter-fallback policy in the worker and verify its
selected provider, model, credential scope, and report attribution during
implementation. An in-flight job receives its child environment
at launch; changing defaults for later jobs should not be treated as a
mid-run switch. OpenCode supports a [default model](https://opencode.ai/docs/models/#set-a-default)
and per-run `--model`; expose those as separate user intents. `hello --timeout
10` is an acceptance probe, not a coding-job timeout.

The practical estimate is: easy per-run selection after migration; moderate
wrapper work to migrate provider credential/report semantics; no reason to
change the coordinator's wait/heartbeat architecture. The exact credential
names, report schema, and compatibility-alias layout remain implementation
questions for the coordinated change; this note records the upstream evidence
and billing boundary only.
