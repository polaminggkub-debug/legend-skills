# Report layout

One folder per program, one subfolder per verified version, inside the program's own repository
(for example `docs/<area>/<program>-reverse-check/`):

```
<program>-reverse-check/
├── README.md          version table + how to check the next version
├── tools/             helper scripts copied from this skill, if the repo wants them pinned
└── <version>/
    ├── report.md      verdict per promise, limits, open questions
    ├── checklist.md   the promises F1…Fn with their sources
    ├── scripts/       runtime scenario and setup scripts; the next version starts from a copy
    └── evidence/      sha256.txt, bundle file list, runtimeconfig/deps, *-types.txt,
                       *-strings.txt, runtime traces and logs (trimmed)
```

Keep raw REA JSON out of the repository (megabytes, and rebuildable from the shipped file). Before
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
