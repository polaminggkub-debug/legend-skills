# Retire RTK, Graphify, and Caveman Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove RTK, Graphify, Caveman, and Cavecrew from active local use, prevent their return through `update-all`, and delete the user-owned Caveman GitHub fork.

**Architecture:** Treat retirement as a transaction: establish a policy guard first, remove active integrations and documentation references second, publish the surviving policy repository third, and delete the Caveman fork/local sources last. Exact-path guards and fresh scans prove each destructive step stayed in scope.

**Tech Stack:** Markdown agent skills, PowerShell, Git, GitHub CLI, JSON, ripgrep

---

### Task 1: Prove the current `update-all` policy lacks an explicit retirement guard

**Files:**
- Test: `update-all/SKILL.md`

- [ ] **Step 1: Run the failing policy assertion**

```powershell
$text = Get-Content -Raw update-all/SKILL.md
foreach ($name in 'RTK','Graphify','Caveman','Cavecrew') {
  if ($text -notmatch [regex]::Escape($name)) { throw "Missing retired-tool policy: $name" }
}
```

Expected: FAIL with `Missing retired-tool policy: RTK`.

- [ ] **Step 2: Record the baseline behavior scenario**

Ask an isolated evaluator to use the unchanged `update-all` skill for a machine where a retired tool appears installed and determine whether the skill explicitly refuses to update or recommend it.

Expected: the evaluator cannot cite an explicit RTK/Graphify/Caveman/Cavecrew retirement rule.

### Task 2: Add and validate the retired-tools policy

**Files:**
- Modify: `update-all/SKILL.md`
- Modify: `C:\Users\i9-14900K\.codex\skills\update-all\SKILL.md`

- [ ] **Step 1: Add the minimal constraint**

Add this paragraph under `## Constraints` in both files:

```markdown
RTK, Graphify, Caveman, and Cavecrew are retired. Never install, update,
restore, recommend, or re-enable them. If discovered, report them as retired
and skip them unless the user explicitly requests removal.
```

- [ ] **Step 2: Run the policy assertion again**

Run the assertion from Task 1.

Expected: exit 0.

- [ ] **Step 3: Validate both skill copies**

```powershell
python C:\Users\i9-14900K\.codex\skills\.system\skill-creator\scripts\quick_validate.py update-all
python C:\Users\i9-14900K\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\i9-14900K\.codex\skills\update-all
```

Expected: both validations succeed.

- [ ] **Step 4: Re-run the evaluator scenario**

Expected: the evaluator cites the explicit retirement rule and refuses installation/update/recommendation.

### Task 3: Remove active Caveman/Cavecrew installation and configuration

**Files:**
- Modify: `C:\Users\i9-14900K\.codex\AGENTS.md`
- Modify: `C:\Users\i9-14900K\.agents\.skill-lock.json`
- Delete: `C:\Users\i9-14900K\.codex\skills\caveman*` exact seven named directories
- Delete: `C:\Users\i9-14900K\.codex\skills\cavecrew`
- Delete: `C:\Users\i9-14900K\.agents\skills\caveman*` exact seven named directories
- Delete: `C:\Users\i9-14900K\.agents\skills\cavecrew`

- [ ] **Step 1: Remove the global Caveman response-style section**

Delete `# Global Response Style` and its four Caveman-oriented bullets. Preserve the `legend-skills:gpt56-router` block byte-for-byte.

- [ ] **Step 2: Remove lock entries structurally**

Parse `.agents/.skill-lock.json`, remove only `cavecrew`, `caveman`, `caveman-commit`, `caveman-compress`, `caveman-help`, `caveman-review`, `caveman-stats`, and `caveman-th`, then serialize valid JSON.

- [ ] **Step 3: Delete the sixteen exact installed-skill directories**

Resolve each literal path, require the leaf to equal one of the eight approved names, clear read-only attributes inside it, and delete only that directory. Do not delete `.codex/skills` or `.agents/skills`.

- [ ] **Step 4: Verify active removal**

```powershell
Get-ChildItem C:\Users\i9-14900K\.codex\skills,C:\Users\i9-14900K\.agents\skills -Directory |
  Where-Object Name -in 'caveman','caveman-commit','caveman-compress','caveman-help','caveman-review','caveman-stats','caveman-th','cavecrew'
```

Expected: no output. JSON parsing of `.agents/.skill-lock.json` succeeds and none of the eight keys exists.

### Task 4: Remove Graphify and Caveman usage references

**Files:**
- Modify: canonical Markdown/config files under `C:\Users\i9-14900K\Documents`
- Modify: generated Markdown/config copies under `C:\Users\i9-14900K\.codex\worktrees`, `C:\Users\i9-14900K\.codex\visualizations`, and `C:\Users\i9-14900K\.config\superpowers\worktrees`
- Delete: `C:\Users\i9-14900K\Documents\Codex\2026-07-15\superpowers-receiving-code-review-c-users\work\graphify-removal-backup-20260715.zip`
- Delete: `C:\Users\i9-14900K\Documents\Codex\2026-07-15\superpowers-receiving-code-review-c-users\outputs\2026-07-15-complete-graphify-retirement-plan.md`

- [ ] **Step 1: Classify exact references**

Use standalone-name searches for `Graphify`, `graphify-out`, `Caveman`, `caveman-th`, the other Caveman skill names, and `Cavecrew`. Exclude `.git`, dependency caches, Codex sessions, archived sessions, and `.codex-global-state.json`.

- [ ] **Step 2: Apply scoped rewrites**

Delete obsolete instruction lines and Graphify commands. Remove references to reading `graphify-out/GRAPH_REPORT.md`. Remove Caveman style directives and skill-path references. Preserve surrounding project instructions and unrelated natural-language/transcript uses.

- [ ] **Step 3: Delete the two Graphify retirement artifacts by literal path**

Expected: both paths return `False` from `Test-Path`.

- [ ] **Step 4: Verify reference removal**

Run the same scoped searches.

Expected: zero active-use hits; any preserved hit must be an unrelated natural-language occurrence and be listed explicitly.

### Task 5: Publish the surviving `legend-skills` policy change

**Files:**
- Commit: `update-all/SKILL.md`
- Commit: `docs/superpowers/specs/2026-07-23-retire-rtk-graphify-caveman-design.md`
- Commit: `docs/superpowers/plans/2026-07-23-retire-rtk-graphify-caveman.md`

- [ ] **Step 1: Verify repository scope**

```powershell
git status --short --branch
git diff --check
git diff origin/main...HEAD --stat
```

Expected: only the retirement spec, plan, and `update-all` policy are in scope.

- [ ] **Step 2: Commit the policy and plan**

```powershell
git add update-all/SKILL.md docs/superpowers/plans/2026-07-23-retire-rtk-graphify-caveman.md
git commit -m "chore: retire legacy agent tools"
```

- [ ] **Step 3: Verify GitHub authentication and push**

```powershell
gh auth status
git push -u origin agent/retire-rtk-graphify-caveman
```

Expected: authenticated as `polaminggkub-debug`; branch is tracking origin.

- [ ] **Step 4: Open a draft pull request**

Create a draft PR against `main` describing the retired tools, local impact, and validation evidence.

Expected: a GitHub draft PR URL.

### Task 6: Delete the user-owned Caveman fork, then local sources

**Files:**
- Delete remote: `polaminggkub-debug/caveman-thai-fork`
- Delete local: `C:\Users\i9-14900K\Documents\Codex\2026-06-29\github\work\caveman-pr-thai`
- Delete local: `C:\Users\i9-14900K\Documents\Codex\2026-04-27\github-caveman-windows-windows-application-cli\caveman`

- [ ] **Step 1: Verify the remote and authorization**

```powershell
gh repo view polaminggkub-debug/caveman-thai-fork --json nameWithOwner,isFork,parent,viewerPermission
gh auth status
```

Expected: exact repository `polaminggkub-debug/caveman-thai-fork`, authenticated owner/admin permission, and no ambiguity with upstream `JuliusBrussee/caveman`.

- [ ] **Step 2: Keep the local fork clone until remote deletion completes**

Confirm branch `codex/add-caveman-th` and commit `7285fa9` exist locally. Do not delete the local clone yet.

- [ ] **Step 3: Delete the exact remote repository**

```powershell
gh repo delete polaminggkub-debug/caveman-thai-fork --yes
```

Expected: exit 0. If GitHub requires `delete_repo`, stop and obtain that scope; do not delete local rollback sources first.

- [ ] **Step 4: Verify remote absence**

```powershell
gh repo view polaminggkub-debug/caveman-thai-fork
```

Expected: repository not found.

- [ ] **Step 5: Delete the two exact local source clones**

Resolve each literal path, require leaf names `caveman-pr-thai` and `caveman`, clear read-only attributes, then delete. Preserve parent task/output directories.

### Task 7: Final verification

**Files:**
- Verify only; no new files

- [ ] **Step 1: Verify RTK and Graphify remain absent**

```powershell
Get-Command rtk,graphify -All -ErrorAction SilentlyContinue
where.exe rtk
where.exe graphify
```

Expected: no commands resolve.

- [ ] **Step 2: Verify retired skill discovery and locks**

Expected: no Caveman/Cavecrew directories, lock entries, or active global directives.

- [ ] **Step 3: Verify scoped references and exact deleted paths**

Expected: zero active-use references and every approved deletion target absent.

- [ ] **Step 4: Verify Git and GitHub state**

Expected: `legend-skills` branch pushed, draft PR exists, remote Caveman fork is absent, and unrelated dirty project changes remain untouched.
