#!/usr/bin/env bash
# PreToolUse(Bash), part of the rea-verify plugin. In a repository that has docs/verification/modules.json it
# blocks `gh pr merge <N>` when the PR adds a rea-verify report folder
# (**/*rea-verify/<run>/report.md or **/*web-reverse-check/<run>/report.md) that
# 1. no `rea/<module>/<sha>` tag names on its message line 2, or
# 2. is new in this PR and lacks the REA evidence files of the skill's references/web.md
#    (evidence/rea-bundle.json, rea-diff.json, one rea-session-*.json), unless report.md has a `BLOCKED:` line.
# Why: the owner reads the REA board (GitHub Project #3), which only moves on a rea/ tag. On 2026-10-21 an AppTable
# run merged its reports with no tag, so the board showed nothing (rea-verify skill, references/record-verdict.md).
# Why 2: on 2026-10-20 the HR attendance run was tagged from curl, grep and Playwright alone; no REA tool ran
# and nothing showed it (audit 2026-11-16).
# Bypass for one run that is deliberately not a verdict (e.g. a pre-fix round folded into a later tag):
# put REA_NO_VERDICT=1 in the command.
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])gh[[:space:]]+pr[[:space:]]+merge([[:space:]]|$)' || exit 0
echo "$CMD" | grep -q 'REA_NO_VERDICT=1' && exit 0
PR=$(echo "$CMD" | sed -E 's/.*gh[[:space:]]+pr[[:space:]]+merge//' | grep -oE '(^|[[:space:]])[0-9]+' | head -1 | tr -d ' ')
[ -n "$PR" ] || exit 0
REPO=$(git -C "${CWD:-.}" rev-parse --show-toplevel 2>/dev/null)
[ -n "$REPO" ] && [ -f "$REPO/docs/verification/modules.json" ] || exit 0

PRJSON=$(cd "$REPO" && gh pr view "$PR" --json files,headRefOid,baseRefName 2>/dev/null)
RUNS=$(echo "$PRJSON" | jq -r '.files[].path' 2>/dev/null \
  | grep -E '(^|/)[^/]*(rea-verify|web-reverse-check)/[^/]+/report\.md$' | sed 's#/report\.md$##' | sort -u)
[ -n "$RUNS" ] || exit 0
HEAD=$(echo "$PRJSON" | jq -r '.headRefOid // empty')
BASE=$(echo "$PRJSON" | jq -r '.baseRefName // empty')

git -C "$REPO" fetch -q origin 'refs/tags/rea/*:refs/tags/rea/*' 2>/dev/null
# Every line of every rea/ tag message; line 2 names the run folder.
NAMED=$(git -C "$REPO" for-each-ref --format='%(contents)' 'refs/tags/rea/')
MISSING=""
for run in $RUNS; do
  echo "$NAMED" | grep -qE "^/?${run}(/report\.md)?/?[[:space:]]*$" || MISSING="$MISSING $run"
done

# REA evidence of each report this PR adds (a report already on the base branch is an old run: skipped).
NOEVID=""
if [ -n "$HEAD" ]; then
  git -C "$REPO" cat-file -e "$HEAD^{commit}" 2>/dev/null || git -C "$REPO" fetch -q origin "$HEAD" 2>/dev/null
  if git -C "$REPO" cat-file -e "$HEAD^{commit}" 2>/dev/null; then
    for run in $RUNS; do
      git -C "$REPO" cat-file -e "origin/$BASE:$run/report.md" 2>/dev/null && continue
      git -C "$REPO" show "$HEAD:$run/report.md" 2>/dev/null | grep -qE '^[-*> ]*BLOCKED: ' && continue
      EV=$(git -C "$REPO" ls-tree -r --name-only "$HEAD" -- "$run/evidence" 2>/dev/null | sed "s#^$run/evidence/##")
      LACK=""
      echo "$EV" | grep -qx 'rea-bundle.json' || LACK="$LACK rea-bundle.json"
      echo "$EV" | grep -qx 'rea-diff.json' || LACK="$LACK rea-diff.json"
      echo "$EV" | grep -qE '^rea-session-.+\.json$' || LACK="$LACK rea-session-<scenario>.json"
      [ -n "$LACK" ] && NOEVID="$NOEVID
  $run: missing evidence/{$(echo $LACK | tr ' ' ',')}"
    done
  fi
fi
if [ -n "$NOEVID" ]; then
  echo "rea-verdict guard: PR $PR adds REA web report(s) without REA evidence:$NOEVID
The shipped bundle was not opened with REA, so the report has no verdict (rea-verify skill, references/web.md,
\"Required REA tools and evidence\"). Run analyze-web-bundle, capture-browser-scenario and compare-web-captures
on the worker and commit their trimmed output, or, when a tool cannot run, put a line
\"BLOCKED: <tool> <reason>\" in report.md and stop for the owner.
A run that is deliberately not a verdict: add REA_NO_VERDICT=1 to the merge command." >&2
  exit 2
fi
[ -z "$MISSING" ] && exit 0
echo "rea-verdict guard: PR $PR adds REA report(s) with no rea/ tag:$MISSING
Record the verdict first (rea-verify skill, references/record-verdict.md): rea-verify Issue, then
git tag -a rea/<module-id>/<short-sha> <commit> -F <msg> (line 1 PASS|FAIL n bugs #i|PARTIAL n #i, line 2 the run folder),
git push origin refs/tags/<tag>, npm run verify:status in this PR; verify:project runs once after the batch (MASTER only, Project #3).
A run that is deliberately not a verdict: add REA_NO_VERDICT=1 to the merge command." >&2
exit 2
