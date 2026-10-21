# Record the verdict

Only for repositories with `docs/verification/modules.json`.

1. **Bug Issues:** one per Bug suspect, or one parent Issue listing them. Each names the approved-UX
   promises (`Fn`) of its screen under **Must keep**, so a fix is judged on both: bug gone, every
   Must keep promise still Match. Label every Issue this run opened `rea-verify` (create the label
   once if missing).
2. **Module id:** an app module, or a shared component (`"kind": "shared"`, id `shared-<name>`, e.g.
   `shared-table` for AppTable) when the run checked one shared piece on its own. A shared component
   missing from `modules.json` gets an entry first (its `paths` under `apps/erp/src/shared/ui/`). Never
   tag a whole module for a run that checked only one shared component.
3. **Tag** the checked commit (the release tag's commit, or the one `compare-source-to-bundle` proved
   live) with the module id from `modules.json`:
   `git tag -a rea/<module-id>/<version-or-short-sha> <commit> -F <message-file>`.
   Message line 1:
   - `PASS`: every promise Match.
   - `FAIL <n> bugs #<issue>`: `n` Bug suspects; `#<issue>` is the single or parent Issue.
   - `PARTIAL <n> #<issue>`: no Bug suspect, `n` promises Different, Partial or Not checked.

   Line 2: the report folder path, relative to the repository root.
4. **Push the tag alone:** `git push <remote> refs/tags/<tag>`.
5. **Status README:** `npm run verify:status`, committed in the same PR as the report folder.
6. **Status board:** `npm run verify:project` updates the GitHub Project named in
   `docs/verification/project.json`. The owner reads that board, so the final state must reach it, but
   run it **once per batch, never per verdict**. GitHub's secondary limits (80 writes/min, 500/hour,
   shared with PRs, comments and commit statuses on the same account) blocked merges for hours on
   2026-10-21 when every tag push re-ran it. No hook runs it any more.
   - Working alone: run it once, after the report PR merges, and check its last line `N cells updated`.
   - A child of a MASTER session: never run it and make no `gh` calls; tell the MASTER the tag is pushed.
     The MASTER runs it once after a batch of merges.
   - On a rate-limit error: stop, wait at least 5 minutes, try once. Never loop. On another failure
     (e.g. `gh` lacks the `project` scope) write `BLOCKED: verify:project <reason>` in the report.

The board (GitHub Project #3 "REA verify status") has views All, Modules and Shared components; the script
keeps their columns. A ship that stops before its `live/*` tags (e.g. a failed smoke) leaves the Live
column old: push `live/erp|db/<UTC YYYYMMDD-HHMM>` on the deployed commit by hand.

Done when the tag is on the remote, every bug Issue has `rea-verify`, the report PR holds the
regenerated status README, and the module's Project row shows the new tag and verdict (after the batch's single `verify:project` run).
