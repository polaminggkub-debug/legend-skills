# Opening the shipped file

REA install (once): `npm install --global rea-agents@<version>`; MCP registration for one client:
`rea setup --client claude_code --dry-run`, then `--yes` after the user approves the plan. The REA
CLI and MCP tools take the same inputs; the CLI writes complete JSON to disk, which suits large
evidence. Commands below use the CLI.

## .NET single-file exe

Signs: one large PE (tens of MB) for a small app; `rea inspect-managed-artifact` reports
`classification.status: not-managed` with `cli-directory-absent`.

```bash
python3 -I scripts/unbundle.py <app.exe> <new-empty-dir>
```

It prints `kind  size  path` per bundled file (kind 1 = assembly, 2 = native, 3 = deps.json,
4 = runtimeconfig.json) and decompresses compressed entries. App modules are the assemblies that are
not framework files (`System.*`, `Microsoft.*`, WPF/WinForms): usually `<App>.dll` plus its own
libraries. Keep `runtimeconfig.json` and `deps.json`: they give the .NET version and every bundled
dependency version.

## .NET assembly

```bash
rea inspect-managed-members <App.dll> --format json > members-<App>.json
rea inspect-managed-native-boundaries <App.dll> --format json > native-<App>.json
```

`members` holds types, methods, member refs, call edges, field accesses, IL anchors and every string
literal. Query it with `scripts/managed_evidence.py`:

- `dump` writes types/methods and strings as text files for the report's `evidence/`.
- `where '<literal>'` and `grep '<regex>'` find which methods use a string (file names, SQL, URLs,
  messages).
- `callers <method> [<type>]` answers "who calls X", e.g. who loads the config holding the token.
- `il <Type> <method>` resolves constants: `1 FromSeconds …Settle` reads as a 1-second setting.

Limits to state in the report: call edges are direct calls only (no reflection, delegates passed
around, or DI resolution); async and lambda callers appear as `<Name>d__N.MoveNext`.

REA has no C# decompiler. For reading method bodies use ILSpy (`ilspycmd <dll> -t <Type>`), on the
worker if it is not installed locally.

## Version diff

```bash
rea compare-managed-members --help
```

Compare the previous verified version's DLL with this one by declared type, name and signature. It
compares members, not string literals: diff the two `*-strings.txt` files for those.

## Other formats

- Electron / extracted JS / ASAR: `rea analyze-javascript-application <path> --format json`;
  `trace-application-feature` and `compare-source-to-bundle` work on its evidence.
- Go / Rust: `rea inspect-go-binary <file>`, `rea inspect-rust-binary <file>` (modules, build
  settings, dependency lists; no toolchain needed).
- Other native code: REA `open_binary` with a Ghidra or IDA provider (`rea doctor` shows which is set
  up), then the native function tools.
- PE resources (icons, manifests, version info): `rea inspect-pe-resources <file>`.
