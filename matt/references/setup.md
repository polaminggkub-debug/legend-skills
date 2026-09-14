# Setup and configuration

Use for explicit installation/repair, saving defaults, or resolving configuration
needed by the next action. Ordinary work does not repeat installer verification.
For installation follow [Install Matt](../INSTALL_FOR_AI.md).

## Discover configuration

Resolve the platform's native user configuration directory without a hard-coded
home path, then look for `legend-skills/matt.md`. Use the runtime/environment's
actual path resolver: Application Support on macOS, the configured XDG location
on Linux, or the appropriate application-data directory on Windows.

Task-specific choices override repository tracker/spec choices, which override
global defaults. Read applicable instructions and any
`docs/agents/issue-tracker.md` or `docs/agents/matt-workflow.md`. One task's choice
does not rewrite persistent configuration.

Without global defaults, use established repository conventions. Without tracker
details, retain a bounded plan in the current task and resolve identity/access
before writes. Do not create a board, Beads project, or OpenSpec installation as
a side effect of an ordinary feature request. Explain missing setup only when
it affects the next action.

## Save defaults when requested

Obtain missing agent targets, default tracker, and default spec system together.
Trackers include none, GitHub Issues, GitHub Projects with repository Issues,
Beads, or a named custom tracker. Spec systems include none, Markdown PRD/plan,
OpenSpec, or a named custom system.

Prepare the English managed block from confirmed choices:

```text
# BEGIN legend-skills:matt
Agent targets: <values>
Default tracker: <value>
Default spec system: <value>
# END legend-skills:matt
```

If saving those choices is already authorized, write and read back the block.
Otherwise show it and obtain the missing decision/authorization. Preserve content
outside the block. Before changing an existing block, make a timestamped backup
outside skill-discovery directories. Resolve conflicting choices with the user;
a previously authorized specific change needs no second approval.

For repository setup, use the selected tracker's actual configuration and record
only `Spec system: <value>` in the managed block of `docs/agents/matt-workflow.md`
when that file is the project's chosen convention. Apply the same preservation
rules. Projects setup additionally uses [GitHub Projects](github-projects.md).

## Helper installation and repair

`dependency-lock.json` pins the original upstream 25-skill bundle. The lock is
installation metadata, not a gate on every task. Chris supplies Matt's acceptance
and testing workflow separately from those upstream helpers.

For a full helper installation, resolve missing names together and follow the
installer. During work, first determine whether a missing helper is necessary
using [helper selection](helpers.md). Report partial capability accurately and
complete independent authorized work.

Preserve custom local skills and existing invocation policies. Update the pinned
upstream version/commit/manifest only as a separately requested and reviewed
release. Routine routing never runs `npx skills update` or downloads a suite.
