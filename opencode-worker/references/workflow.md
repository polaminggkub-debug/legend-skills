# Project workflow contract (schema 1)

Commit `.opencode/worker.json` before dispatch. The worker hashes it at preflight
and rejects changes to it during the run. Unknown fields, unsafe paths, missing
executables, and invalid values fail before model spend. Do not store secrets
or machine-specific absolute paths in this file.

## Ordinary checks, including no-build work

```json
{
  "schema_version": 1,
  "write_paths": ["src/**", "tests/**", "docs/**"],
  "checks": [
    {
      "id": "unit",
      "kind": "test",
      "argv": ["{python}", "-m", "unittest", "discover", "-s", "tests"],
      "cwd": ".",
      "stage": "before_commit",
      "required": true,
      "timeout_seconds": null
    }
  ]
}
```

Use only if that is the project's actual test command. For a plain edit needing
no executable check, `"checks": []` is valid and produces `not_declared`.
The worker does not invent `build`, require Node.js, or claim tests passed.

| Field | Meaning |
|---|---|
| `schema_version` | Required integer `1` |
| `write_paths` | Relative glob list for source changes; default `["**"]` |
| `checks` | Ordered list, default empty |
| check `id` | Unique identifier; used in results and local log directories |
| `kind` | `test`, `lint`, `build`, or `check` |
| `argv` | Nonempty list of literal arguments; never a shell command string |
| `cwd` | Existing directory inside the repo; default `.` |
| `stage` | `before_commit` (default) or `after_commit` |
| `required` | Boolean, default true; false preserves failure as a warning |
| `timeout_seconds` | Positive finite number; null uses the worker command default (600 seconds). Always bounded by remaining job time |

`{python}` in argv[0] means the worker's interpreter. Other command names are
resolved on PATH; repository executables resolve relative to `cwd`. Arguments
are not expanded by a shell. Put complex logic in a reviewed repository script,
then invoke its interpreter explicitly. Cross-platform availability of Git does
not imply availability of `make`, a particular package manager, or a test runner.

## Source → metadata → final build

Use a handoff only when project metadata needs a real source commit before
the final build. It is not needed for ordinary source edits.

```json
{
  "schema_version": 1,
  "write_paths": ["src/**", "tests/**", "review/**"],
  "checks": [
    {
      "id": "final-build",
      "kind": "build",
      "argv": ["npm", "run", "build"],
      "cwd": ".",
      "stage": "after_commit"
    }
  ],
  "handoff": {
    "metadata": [
      {
        "id": "record-source",
        "argv": ["{python}", "scripts/record_source.py"],
        "cwd": "."
      }
    ],
    "write_paths": ["metadata/source.json"]
  }
}
```

The project supplies `scripts/record_source.py`; this is not a bundled command.
The metadata command receives:

- `WORKER_SOURCE_COMMIT`: source commit A.
- `WORKER_RUN_ID`: the run UUID.
- `WORKER_REPO_ROOT`: the absolute project root.

It should read exact files from A, verify any required prepared semantic review,
and write only declared metadata paths. It must fail on missing/mismatched
evidence, not manufacture a review verdict. The worker only records that the
command passed; the project owns the meaning of that validation.
If checks compare file bytes with Git blobs, the project must account for Git's
newline filters; use canonical byte writes or appropriate `.gitattributes` when
byte-for-byte equality is required across Windows and macOS.

The worker verifies A is unchanged, commits metadata as B, and runs the final
checks on B. If metadata writes nothing, A remains the final revision. If the
model made no source changes, a declared handoff fails because there is no new
attributed source commit. Metadata records attribute A and report zero **worker**
model calls/tokens for this deterministic stage; all model cost belongs to A.

After-commit commands must leave HEAD and tracked/untracked source files clean.
Build artifacts normally belong in ignored output paths. The final external
report binds check results to the exact checked revision; it is not committed
after the build, which would change HEAD and invalidate a revision-bound stamp.

## Ownership and limits

The worker serializes its own jobs by Git common directory and requires a clean
repository with an existing HEAD and Git identity. It does not prevent another
editor/process from changing files; detected concurrent changes fail rather
than being silently accepted. The model cannot modify the committed plan or
reserved provenance paths within a successful wrapper run.

Checks and metadata are trusted local programs, not sandboxed code. The wrapper
does not disable their own network or child-process capabilities. Keep them
deterministic and model-free if measuring a one-way coding run. Calling a raw
OpenCode executable bypasses this workflow entirely.
