# Guardrails and CI

Read when designing or auditing machine-enforced constraints, connecting local
checks to CI, or protecting verification policy from unnoticed changes.

## Choose a rule for a concrete failure

Start from the project's requirement and actual code/configuration. Prefer an
existing checker that catches the failure with useful diagnostics. Adopt a rule
when its protection warrants runtime, false positives, and exception maintenance.
When existing code already violates it, commit a baseline so only new
violations fail, and review baseline edits like rule edits. A large project's
rule is a precedent to evaluate, not a universal requirement.

| Constraint | Candidate mechanism | Boundary to inspect |
|---|---|---|
| Layers or packages must not import each other | Restricted imports, dependency graph, compiler project boundaries | Aliases, re-exports, dynamic imports, generated files |
| Avoid a statically identifiable unsafe construct | Type checker or AST lint rule | Typed information, exclusions, rule severity |
| Reject a domain-invalid outcome | Unit or integration invariant | Real state and independent expected values |
| Keep generated files in sync | Regenerate and compare expected files | Tool version, tracked/untracked files, deterministic output |
| Preserve an external interface | Contract/schema compatibility check | Consumer expectations and supported versions |
| Formatting or repository hygiene | Formatter in write mode ([autofix](#fix-before-you-fail)) | Pinned config; only the files it owns |
| A test passes without the behavior being true | Test lint bans ([Playwright](playwright.md#acceptance-walkthroughs)) | Rule severity: warnings exit 0 |
| Suite run time or size creeps up | Slow-file report, run budget, spec-count and duplicate checks ([Test speed](test-speed.md#7-guard)) | Same selection and machine over time |

Static syntax checks cannot prove runtime or rendered behavior; select that
boundary through [Acceptance and evidence](acceptance-evidence.md). A guard
larger than the code it protects needs owner approval.

## Fix before you fail

When a script can compute the right code, make the rule an *autofix*: the
script rewrites the code and the agent never sees a failure, so there is no
run → fail → run cycle. Pick the strongest rung that fits:

1. **Default.** The shared component already does it (every button red by
   default), so there is nothing to enforce.
2. **Autofix.** A codemod or an ESLint rule with `meta.fixable` and a `fix`
   (a `suggest` is never applied by `--fix`) runs after the agent's commit and
   commits its result as a separate *Autofix* commit, so the version before and
   after the script both stay in history.
3. **Guard.** Keep a failing check only where the fix needs a choice (where to
   split a long function, which layer owns a module, whether a test proves the
   behavior) or the criterion is behavioral or rendered.

Typical autofixes: formatting, a native element to its shared component, a deep
import to the public index, a dropped `.only`/`.skip`, a removed fixed sleep or
`force: true`, a missing `await`. Write each one tight:

- **Parse, then edit.** Work on the syntax tree (the language's parser, or
  `vue-eslint-parser` for SFCs), never on regex matches of the text.
- **Find, check, fix.** Code that is already right stays untouched, so a second
  run changes nothing.
- **Unsure means leave it.** A case it cannot change safely (a `ref` on the
  element, a dynamic value) is left as is and listed; the remaining guard
  catches what is left.
- **Honor reviewed exceptions.** A disable comment marks a deliberate case (a
  sleep that proves nothing moves); the fix keeps it.
- **Prove it on pairs.** Before/after fixture files (`x.input.*` → `x.output.*`)
  plus a second-run test, the Next.js codemod pattern.
- **Run the affected checks after.** An autofix is a code change: when it can
  change behavior (a swapped component, a deleted sleep, a test that now runs),
  the affected walkthroughs still run on the result.

Replacing a guard with an autofix is one change: add the fix with its pairs,
remove the guard, its lint-proof fixture and its docs line, and wire the fix to
run after the agent's commit (a non-blocking PostToolUse hook on `git commit`,
or the project's fix command).

## Guards inside an agent's loop

A guard an agent runs every turn (a Stop or PostToolUse hook, a per-commit
script) is also a prompt: its output lands in the agent's context and picks the
next action. Each added rule lowers the chance that all of them hold at once,
and each failure log crowds out earlier context, so loose guards turn into
run → fail → run cycles that cost more than the defects they catch. Keep every
in-loop guard *tight*:

- **Deterministic and fast.** Same input, same verdict, within seconds, on the
  changed files. Full suites, mutation runs, and visual or LLM-as-judge review
  run at the gate or in CI ([Test speed](test-speed.md#6-run-less)); a judgement
  of how something looks goes to the owner or a sampled review.
- **Quiet pass, short fail.** One line on success. On failure, the first few
  violations as `file:line rule → fix`, so the message says what to change;
  the full log goes to a file the agent can open.
- **Bounded.** The same check failing twice on the same cause ends the loop:
  report the evidence to the owner. A Claude Code Stop hook reads
  `stop_hook_active` and exits 0 when it is already re-running.
- **Locked.** The judged agent cannot edit the guard, its config, or the tests
  it runs (hard rule 5). Mechanical locks answer gaming; extra written rules do
  not.

Prose rules in CLAUDE.md or a skill are advisory. A rule that must always hold
becomes a hook or lint rule; a rule the agent already follows by default is
deleted.

**Keep the set small.** Before adding a guard, ask whether a script can make
the fix ([Fix before you fail](#fix-before-you-fail)). Each guard names the defect it exists to catch, and
keeps a ledger: runs, failures, and failures that were real defects. Remove a
guard, or move it to CI, when it fails often without real defects or judges
what the owner reviews directly. When one guard keeps catching the same
mistake, fix the instruction or example that leads the agent there instead of
adding a retry or a second guard. Adding a guard to the loop is a policy
change: state its run time and the defect it catches.

## Trace enforcement end to end

Trace the actual chain, including wrappers and conditional steps:

`rule -> selected files -> command -> nonzero failure -> CI job -> required merge check`

1. Inspect rule configuration, severity, target files, ignores, inline disables,
   baselines, and supported tool versions. Warnings may still exit successfully.
2. Follow the command invoked locally and in CI, including nested scripts.
   Verify failures propagate through catches, pipelines, `|| true`, and
   continue-on-error behavior. A documented command may never be invoked.
3. Compare local/CI rule sources, dependencies, arguments, environment, and
   selection. Reuse a shared check entrypoint where practical; document intentional
   differences. Inspect path filters, event filters, matrices, and aggregation.
4. Verify required-check/ruleset settings for the target branch when accessible.
   Configuration in Git establishes neither current settings nor their historical
   state. Report unavailable settings as unknown, not as enforcement.

State how far enforcement was actually shown (config only, local run, CI run,
or required for merge). A command with no selected files or a skipped job has
not checked the intended code.

## Prove the rule's behavior

For a new or materially changed rule, use a minimal violating example that
fails for the intended reason and a valid example that passes. Exercise the
actual command path, including its exit status. Use fixtures or a disposable
worktree; keep deliberate violations out of normal source and the final diff.
Validate important evasion paths implied by the requirement, rather than trying
to prove a syntax checker rejects every possible runtime behavior.

An expected-failure lab that succeeds because its bad fixtures failed is not a
production check command.

Completion means the agreed rule detects its intended violation, accepts valid
code, and reaches the requested enforcement stage. If CI/settings access is
missing, identify the demonstrated stage and remaining setup precisely.

## Review changes to the checks themselves

When a diff changes lint/config, test selection, assertions, baselines, CI
workflows, or exceptions, explain whether protection changed. A failing check
alone is not a reason to lower severity, broaden ignores, skip coverage, or
replace expectations. The agent implementing a change must not edit the checks
it is judged by; lock them with CODEOWNERS, protected paths, or hooks.

For an authorized policy-change notification workflow, derive watched paths
from actual enforcement files and include the detector plus its watched-path
configuration. Observe base/PR metadata or diffs from a trusted execution context.
If using a privileged event such as GitHub `pull_request_target`, follow current
provider documentation and keep untrusted PR code out of privileged execution.
Validate an ordinary change, a watched policy change, and a detector change.

Keep notification and blocking separate. Repository settings changed outside
Git need their own supported event/audit coverage; a file-diff detector cannot
see them. Use the project's recipients and permissions. An account that can
change both code and protection retains that authority; alerts are not an
immutable security boundary. This guidance does not itself authorize changing
repository settings, sending messages, or performing merges.

For real project precedents, choose a matching entry from the
[case index](cases/index.md). Use local cases for their recorded observations;
verify current provider behavior and syntax before implementing against it.
