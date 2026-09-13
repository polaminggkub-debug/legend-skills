# Guardrails and CI

Read when designing or auditing machine-enforced constraints, connecting local
checks to CI, or protecting verification policy from unnoticed changes.

## Choose a rule for a concrete failure

Start from the project's requirement and actual code/configuration. Prefer an
existing checker that catches the failure with useful diagnostics. Adopt a rule
when its protection warrants runtime, false positives, and exception maintenance.
A large project's rule is a precedent to evaluate, not a universal requirement.

| Constraint | Candidate mechanism | Boundary to inspect |
|---|---|---|
| Layers or packages must not import each other | Restricted imports, dependency graph, compiler project boundaries | Aliases, re-exports, dynamic imports, generated files |
| Avoid a statically identifiable unsafe construct | Type checker or AST lint rule | Typed information, exclusions, rule severity |
| Reject a domain-invalid outcome | Unit or integration invariant | Real state and independent expected values |
| Keep generated files in sync | Regenerate and compare expected files | Tool version, tracked/untracked files, deterministic output |
| Preserve an external interface | Contract/schema compatibility check | Consumer expectations and supported versions |
| Formatting or repository hygiene | Formatter, whitespace/file policy check | Check mode versus auto-fix mode |

Static syntax checks cannot prove general runtime properties. Select the test
boundary through [Acceptance and evidence](acceptance-evidence.md) when needed.
Write down the rule, scope, allowed exceptions, expected diagnostic, and cost
only to the extent these are not clear in the authoritative configuration.

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

Report the highest evidenced stage: **configured**, **locally demonstrated**,
**CI demonstrated**, or **required for merge**. Explain gaps between stages.
A successful command with no selected files or a skipped job is not equivalent
to having checked the intended code.

## Prove the rule's behavior

For a new or materially changed rule, use a minimal violating example that
fails for the intended reason and a valid example that passes. Exercise the
actual command path, including its exit status. Use fixtures or a disposable
worktree; keep deliberate violations out of normal source and the final diff.
Validate important evasion paths implied by the requirement, rather than trying
to prove a syntax checker rejects every possible runtime behavior.

An expected-failure lab may return success because its bad fixtures failed as
expected. Such a lab runner is not a production source-check command. Adapt
examples to the repository's files, scripts, tool versions, and CI contract.

Completion means the agreed rule detects its intended violation, accepts valid
code, and reaches the requested enforcement stage. If CI/settings access is
missing, identify the demonstrated stage and remaining setup precisely.

## Review changes to the checks themselves

When a diff changes lint/config, test selection, assertions, generated baselines,
CI workflows, or exceptions, explain whether protection changed. Keep necessary
policy changes explicit in the diff and rationale. A failing check alone is not
a reason to lower severity, broaden ignores, skip coverage, or replace expectations.
Use the agreed contract and a demonstrated failure cause to justify updates.

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
