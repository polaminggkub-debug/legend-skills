# Retire RTK, Graphify, and Caveman

## Goal

Remove RTK, Graphify, and the complete Caveman ecosystem from active local use, prevent `update-all` from reinstalling or updating them, and publish the `update-all` policy change to `polaminggkub-debug/legend-skills`.

## Scope

- Add an explicit retired-tools constraint to `update-all` for RTK, Graphify, Caveman, and Cavecrew.
- Remove installed Caveman and Cavecrew skill directories from `.codex/skills` and `.agents/skills`.
- Remove their entries from `.agents/.skill-lock.json`.
- Remove active Caveman response-style instructions from `.codex/AGENTS.md` while preserving GPT-5.6 routing.
- Remove local Caveman source/work clones and Graphify retirement artifacts.
- Remove Caveman task-parent remnants, rollback instructions that would re-enable Caveman, and the current RTK-named task workspace/trust entry last.
- Delete the remote GitHub repository `polaminggkub-debug/caveman-thai-fork` after confirming the authenticated owner and retaining its local clone until remote deletion succeeds.
- Remove Graphify and Caveman usage references from canonical user-authored Markdown/config files and generated Codex worktree copies. Replace executable command prefixes with native commands where applicable; delete obsolete instruction lines.
- Verify RTK remains absent.

## Non-goals

- Do not change unrelated tools, skills, PATH entries, project code, or historical Codex session JSON.
- Preserve unrelated dirty worktree content while removing only the approved tool directives and command references.
- Do not edit unrelated uses of common words or third-party product names.

## Safety and rollback

- Resolve every recursive deletion target to an exact absolute path and reject unexpected leaf names.
- Never use wildcards for deletion.
- Preserve shared parent directories and unrelated dirty worktree changes.
- Tracked Markdown/config changes remain recoverable through Git. Deleted upstream source clones can be cloned again. Installed skills can be reinstalled from their recorded GitHub source.
- Graphify backup artifacts and untracked local runtime data are intentionally removed without creating another local copy.
- Keep the local `caveman-pr-thai` clone only as a temporary rollback source. Delete it after the remote fork deletion is verified; recreating the deleted GitHub repository afterward would require creating a new repository and pushing from another surviving source.

## Validation

- `update-all` passes skill validation and explicitly rejects the retired tools.
- No installed Caveman/Cavecrew directories or lock entries remain.
- Active global instructions contain no Caveman directive.
- RTK and Graphify commands remain unresolved and no matching services/tasks/packages exist.
- GitHub reports `polaminggkub-debug/caveman-thai-fork` as absent after deletion.
- Scoped Markdown/config scans find no active RTK, Graphify, Caveman, or Cavecrew usage references.
- Git diffs contain only intended documentation/config changes and pass `git diff --check`.

## Publication

Commit only the `legend-skills` policy/spec changes on `agent/retire-rtk-graphify-caveman`, push to `origin`, and open a draft pull request against the default branch.
