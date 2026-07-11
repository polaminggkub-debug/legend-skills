# Personal skills modernization

> **Owner decision:** implement on `codex/skill-modernization`; do not commit, push, or deploy.

## Scope

Modernize `chris`, `margaret`, `ship`, `steve`, and `update-all`. Preserve each skill's purpose while making execution cross-platform, concise, evidence-based, and usable by Codex, Claude Code, and cloud agents.

## Task 1 — Baseline validation

1. Add `scripts/validate-skills.py` with standard-library-only checks.
2. Check YAML front matter, required cross-platform language, report policy, no hard-coded legacy runtime path, and target `SKILL.md` size.
3. Run it before edits; record known failures as the baseline.

## Task 2 — Chris: single testing gateway

1. Replace `chris/SKILL.md` with a short router for every testing task.
2. Add progressive references for testable architecture, TDD/writing, debugging, reviewing/auditing, and infrastructure.
3. Keep the functional-core / imperative-shell test order: isolated unit spec -> boundary integration -> critical contract/E2E sample.
4. Use Markdown reporting, evidence, adaptive audit depth, and a mandatory verification pass.

## Task 3 — Margaret: adaptable module audit

1. Replace the fixed 7-agent workflow with standard/deep modes and 2–7 relevant lenses.
2. Add framework profiles and an official-documentation-on-demand rule after version detection.
3. Add file-coverage state, prior-finding state, evidence gates, and a Markdown report location.

## Task 4 — Ship and Update All: bounded production/update operations

1. Make Ship production-only: documented deploy/smoke/rollback commands are required; no implicit commit/push/build-only behavior.
2. Add production safety gates and Markdown ship report.
3. Make Update All agent-ecosystem-first, transactional, cross-platform, and safe for dirty repositories.
4. Require an explicit opt-in only for optional developer-tool updates.

## Task 5 — Steve Design Suite

1. Replace Steve's fixed audit and HTML score behavior with a concise design decision workflow and Markdown evidence report.
2. Create `steve-design-suite` bundle manifests for Codex and Claude Code.
3. Add bundled `ui-ux-pro-max`, lock metadata, and a cross-platform query helper. Steve invokes it for implementation work but loads only the relevant domain.
4. Keep Apple-quality product judgment as Steve's north star, distinguish it from the implementation toolkit, and never hardcode a user-home path or `python3`.

## Task 6 — Distribution and verification

1. Replace Bash-only installer with portable Python installer plus small shell/PowerShell launchers.
2. Update README with supported installation/update paths and the design-suite release model.
3. Run validator, compile Python, inspect diff, and record a Markdown implementation report.

## Acceptance checks

- All five `SKILL.md` files are ≤150 lines and route detailed behavior into references.
- Chris remains the only testing gateway and preserves testable architecture.
- Audit/report skills use Markdown with `PASS` / `CONDITIONAL PASS` / `FAIL`, evidence, and adaptive depth.
- Ship cannot trigger or operate as a general git/build helper.
- No tracked skill file contains a hard-coded legacy skill path, hard-coded `python3` command, or a mandatory “How many audit passes?” prompt.
- Steve and UIUX Pro Max distribute as one versioned suite with both platform manifests.
- Validation passes on Windows without nonstandard dependencies.
