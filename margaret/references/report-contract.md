# Markdown audit report contract

1. Scope, mode, detected stack/versions, assumptions, and sources.
2. Verdict: `PASS`, `CONDITIONAL PASS`, or `FAIL` with a one-sentence reason.
3. Findings ordered by severity. Each includes confidence, `file:line`, evidence,
   trigger scenario, impact, verification, and smallest safe fix.
4. File/flow coverage: `REVIEWED`, `FINDING`, `SKIPPED — reason`, `COVERAGE GAP`.
5. Previous findings: `OPEN`, `FIXED`, or `REGRESSED`.
6. Prioritized actions and residual risk.

Verdict guidance: FAIL for any confirmed critical risk or several confirmed high
risks without containment; CONDITIONAL PASS for bounded known risk with an owner
or workaround; PASS when no confirmed critical/high risk remains in reviewed
scope. Never turn missing coverage into false confidence.
