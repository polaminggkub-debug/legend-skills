# Report layout

One folder per program, one subfolder per verified version, inside the program's own repository
(for example `docs/<area>/<program>-reverse-check/`):

```
<program>-reverse-check/
├── README.md          version table + how to check the next version
└── <version>/
    ├── report.md      verdict per promise, limits, open questions (short: see the template)
    └── checklist.md   the promises F1…Fn with their sources
```

**Only `report.md`, `checklist.md` and the README row go to the main branch** (owner 2026-10-25:
one release's raw evidence was 17k–91k lines and hundreds of screenshots). The evidence and scripts
(`evidence/`: sha256.txt, bundle file list, trimmed traces and logs, web apps also rea-bundle.json,
rea-session-<scenario>.json, rea-diff.json; `scripts/`: scenario and setup scripts the next version
copies) are committed on the report branch that the `rea/` tag points to, and are never merged: the
tag keeps them (`git show <tag>:<path>`). The main-branch PR checks them out of the report branch
file by file (report.md, checklist.md) and adds the README row. Links from the report to evidence
use the tag form, not a relative path.

Keep raw REA JSON out of every commit (megabytes, and rebuildable from the shipped file). Before
saving evidence, scan it for keys, tokens, passwords, personal names and customer data; trim or drop
any file that carries them.

## README version table

| Version | Verdict | Report |
|---|---|---|
| 1.3.0 | 10 of 12 Match; 2 Different (owner to decide) | [1.3.0/report.md](1.3.0/report.md) |

## report.md template

```markdown
# <Program> <version>: reverse check (<date>)

- Target: <file>, sha256 `<hash>`, matches <manifest / release note>.
- Promises: [checklist.md](checklist.md), from <Issues, guide, release notes>.
- Tools: REA <version>, <unpacker>, <runtime: VM / OS / tracer>.

Keep it to about one screen per 10 promises: one table row per promise, one line per finding,
no pasted logs or captures (cite the evidence file on the tag instead).

## Result per promise

| # | Promise (source) | Evidence (static / runtime) | Verdict |
|---|---|---|---|

## Found outside the promises
Suspected bugs, version-diff surprises, secrets, dependency CVEs, extra features.

## Limits
What static evidence cannot show here; scenarios that could not run, and why.

## Open for the owner
One numbered question per Different or Bug suspect verdict.
```
