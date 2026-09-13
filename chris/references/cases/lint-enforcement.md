# Lint enforcement precedents

### L1 — Configuration is not enforcement (VS Code + Ruff)

**Use when:** an AI changes a lint rule, severity, wrapper script, workflow, or ignores a warning.

**Observed facts**

- VS Code configures `code-layering` as warn and an internal-import rule as error; its ESLint wrapper throws when either warnings or errors remain, and the PR job runs the lint/layer checks ([config](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/eslint.config.js#L114-L140), [wrapper](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/build/eslint.ts#L26-L50), [PR workflow](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.github/workflows/pr.yml#L89-L107)).
- Ruff keeps some disallowed-method lints at warn in source, while CI invokes Clippy with `-D warnings`; its result aggregator exits 1 for a non-success/non-skipped job ([crate lint level](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/crates/ty_python_core/src/lib.rs#L1-L4), [Clippy command](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L311-L331), [aggregator](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L1400-L1423)).

**Decision and verification**

- Treat config, invocation, CI execution, failure propagation, and required-merge policy as separate claims. A warning may be useful feedback without being a gate.
- Create one known bad and one valid case. Run the exact wrapper on the relevant revision; record exit status, diagnostic, file scope, and workflow job. Inspect `if`, path filters, `continue-on-error`, and `|| true`.
- Treat a skipped job as a missing observation. Inspect event/path selection and current provider rules before drawing a merge-eligibility conclusion.

**Solo adaptation (inference):** keep one short local check and one CI entry point; protect the policy files by review. Leave advisory rules diagnostic until their false-positive cost is understood. Do not claim required merge without repository settings.

**Limitations:** snapshots show configured and CI-running paths, not branch-protection settings. Ruff’s aggregator accepting skipped jobs is not an assertion that the skipped behavior ran.

### L2 — Generated output is a source-of-truth contract (Kubernetes + Moby)

**Use when:** source/schema/codegen changes must ship with generated files.

**Observed facts**

- Kubernetes starts from a clean worktree, runs the generator, checks `git status`, and returns failure on changes; `make verify` dispatches repository verification scripts ([generated helper](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/lib/verify-generated.sh#L22-L61), [codegen entry](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/verify-codegen.sh#L17-L29), [verify dispatcher](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/make-rules/verify.sh#L235-L251)).
- Moby regenerates Swagger output in a temporary location, diffs generated files, and runs separate API validation targets in CI ([validator](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/api/scripts/validate-swagger-gen.sh#L11-L50), [targets](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/api/Makefile#L54-L60), [CI invocation](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/.github/workflows/test.yml#L209-L226)).

**Decision and verification**

- AC: “Given canonical source X, regeneration with pinned inputs produces the committed output tree exactly, including added and removed files; the consumer contract still passes.”
- Run the real generator from a clean or isolated worktree and compare the intended output tree. Add a consumer/schema check when the acceptance contract also requires compatibility. Record generator/tool version, input revision, diff status, and any ignored/untracked-file policy.
- Skip this card when no generated artifact exists. If generation is nondeterministic, fix that or state why the comparison is only advisory.

**Solo adaptation (inference):** pair every update command with a verify command and a diagnostic that tells the AI what to regenerate. Keep codegen out of pre-commit when it is slow; run it in CI or before release.

**Limitations:** drift detection does not prove generator semantics, runtime compatibility, or every consumer. The source projects' environment and scripts are heavier than a small application.

### L3 — Custom semantic lint needs a real domain invariant (React + Next.js)

**Use when:** built-in lint cannot express a recurring, high-cost project rule.

**Observed facts**

- React makes production logging, production error-code mapping, coercion, and target-specific syntax custom ESLint rules; its lint script exits 1 and CI invokes it ([rule config](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/.eslintrc.js#L292-L318), [runner](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/tasks/eslint.js#L13-L26), [CI invocation](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/.github/workflows/shared_lint.yml#L41-L60), [custom rule](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/eslint-rules/no-production-logging.js#L39-L82)).
- Next.js registers AST rules for server/browser and async patterns, but its CLI config explicitly disables `no-floating-promises`; its AST action is a separate CI job ([rule wiring](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/package.json#L63-L76), [rules](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.config/ast-grep/rules/no-typeof-window-require.yml#L3-L32), [scope/CI](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.github/workflows/build_and_test.yml#L361-L373), [disabled rule note](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/eslint.cli.config.mjs#L9-L41)).

**Decision and verification**

- Create a custom rule only after writing the invariant, scope, replacement, valid/invalid fixtures, and known false negatives. Run the checker directly and through its CI path on the target revision.
- Treat AST matches as syntax evidence. Test aliases, re-exports, dynamic paths, and runtime behavior only when the requirement needs them.

**Solo adaptation (inference):** start with one rule tied to a repeated incident and an existing public wrapper/API. Do not copy React’s `__DEV__`, target assumptions, or Next’s disabled-rule choices into another stack.

**Limitations:** custom rules are maintenance code; static matching cannot prove authorization, runtime state, or all semantic aliases.
