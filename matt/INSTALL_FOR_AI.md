# Install or update Matt

Matt coordinates work; the bundled Chris skill owns acceptance and testing.
Install both for the complete core workflow. The pinned upstream helper suite
adds specialized capabilities. Installation and configuration are separate from
ordinary task routing.

## Core installation or update

1. Resolve the requested agent targets and actual global skill directories using
   the [repository installer](https://github.com/polaminggkub-debug/legend-skills/blob/main/INSTALL_FOR_AI.md). For Codex, Matt uses the
   configured Codex skill directory; Chris uses the user-scoped agents directory.
2. Inventory existing Matt/Chris copies and invocation policies. Preserve unrelated
   files and customizations. Make timestamped backups outside skill-discovery
   directories before an authorized replacement. Resolve an unapproved conflicting
   customization before replacing it; existing authorization for the exact change
   does not require another confirmation.
3. Copy the complete Matt and Chris directories, including references and metadata.
   Preserve an existing target's invocation policy. Matt can read an installed
   Chris by name/path without enabling its independent automatic discovery.
4. Preserve existing tracker/spec defaults. If saving new defaults was requested,
   use [setup](references/setup.md) to obtain only missing decisions and write the
   managed block. Otherwise report defaults as unset when absent; this does not
   block a task that has enough repository/context information.
5. Read back the installed files, resolve local references, validate frontmatter,
   and confirm the intended global locations. Report core installation separately
   from optional helper availability and any deferred configuration. File checks
   do not prove that a running app has refreshed its skill picker.

For an update of an existing installation, update only the requested bundled
skills. Do not reinstall or upgrade the upstream suite as a side effect.

## Full upstream helper bundle

Use this section when the user requests the full bundle or helper repair.

1. Read `dependency-lock.json`. Fetch the official manifest at the pinned
   `upstream.installSource`; require its version, commit, and 25 stable
   Engineering/Productivity paths to match the lock.
2. Check required skill names/frontmatter for the selected targets. Prefer an
   installer registry recording source `mattpocock/skills`. Without provenance,
   a matching local name and corresponding official pinned path satisfies presence;
   report preserved content differences. Explicit conflicting source provenance
   requires a decision before replacement.
3. Collect all missing names. Build the command below, appending one `--skill`
   argument per missing name and one `--agent` per selected target:

   ```text
   npx skills@latest add https://github.com/mattpocock/skills/tree/5b15a47f2d7150f545fbcacbfe381787fc0230dc --global
   ```

   Verify the URL exactly equals `upstream.installSource`. Explain the external
   dependency installation; run only when authorized. Preserve conflicting custom
   copies. Re-check every selected target after installation.
4. Report the full bundle complete only when all 25 are present. Otherwise list
   missing capabilities; core Matt/Chris and independent work remain usable.

The upstream `$tdd` may remain installed for compatibility. Matt's testing route
uses Chris's internal TDD guide. Never run `npx skills update` during routing.
Changing the lock needs a separately requested, reviewed release of the version,
commit, manifest, and stable skill set together.
