---
name: rea-verify
description: >
  Verify a release of the user's own program from the shipped file, not its source: reverse
  engineer it with REA, check every promise from the Issues and guides, run black-box checks on the
  worker machine, and give a per-version verdict with suspected bugs. Use when the user asks to
  check, verify, audit or black-box test a built exe/app/package against its requirements, compare
  what a release really does with what was promised, or find bugs in a shipped version
  ("ตรวจตัวที่ส่งจริง", "reverse engineer โปรแกรมเรา", "เช็คว่าทำงานตาม requirement").
---

# REA verify

The **shipped file** is the witness: source shows what someone meant to build, the shipped file shows
what was built. Each run checks one version against its **promises** (what Issues, guides and release
notes say it does) and gives each promise a **verdict**. Only for programs the user owns or builds.

## 1. Pin the target

Take the file from where it ships (release host, install kit). Record name, version and sha256, and
match the sha256 against the release record; a mismatch is the first finding. Work in a scratch folder
outside every repository, with the shipped file in its own empty folder. Keep the source tree closed
until step 3's tracing: a promise is judged from the requirement and the file, which is what makes
the check independent.

Done when the sha256 is written down and matches its release record (or the mismatch is recorded).

## 2. Write the promises

Load `chris` and turn each requirement into a checkable promise `F1`…`Fn` with its source. Sources:
Issues closed since the last verified version, the shipped guide, release notes, and **approved UX**
(mock-ups and acceptance lists the owner approved). Each approved behaviour is its own promise, so a
release that fixes bugs but loses approved UX shows as Different. A new version starts from the
previous version's `checklist.md`.

Done when every closed Issue maps to a promise or is listed as "no observable promise".

## 3. Open the file and gather evidence

Route by format ([references/formats.md](references/formats.md) has the commands):

- .NET single-file exe: REA says `not-managed`; unpack with `scripts/unbundle.py`, then open the app DLLs.
- Plain .NET assembly: `inspect-managed-members --format json`.
- Electron / JavaScript: `analyze-javascript-application`.
- Native: `open_binary` (Ghidra/IDA), or `inspect-go-binary` / `inspect-rust-binary`.
- **Web app:** follow [references/web.md](references/web.md), the scripted pipeline with its
  required REA tools and evidence files.

Raw REA output is large: keep it on disk and read it through `scripts/managed_evidence.py`, `jq` or
`grep`. Server-side promises (database functions, row-level security, API rules) are not in the file:
check them through the public API, signed in as each kind of user.

Done when every app module (not framework files) has REA evidence saved to disk.

## 4. Static checks

For each promise, find the code that carries it and the fact that proves or breaks it (a literal, a
constant, a call edge). Then sweep for what no promise mentions:

- **Suspected bugs:** decompile and review the code behind each promise: swallowed exceptions,
  endless retries, local-vs-UTC time, nulls, SQL built from strings, writes where reads were promised.
- **Version diff:** `compare-managed-members` (or `compare-web-captures`) against the last verified
  version; an unexplained change is a finding.
- **Secrets, dependencies, extras:** keys and private URLs in strings, bundled libraries with CVEs,
  features no promise asked for.

Done when every promise has static evidence or is marked "needs runtime".

## 5. Runtime checks on the worker

Static evidence proves code is wired, not that it works. Run on the worker machine named in
`~/.claude/docs/work-routing.md` (brief it with `poo-handoff`), otherwise the machine the user names,
in a VM or container matching the customer's OS, with copies of data. Scenario kinds, the 10-minute
budget and the one-command runners are in [references/runtime-checks.md](references/runtime-checks.md).
When the program has a runner, run it: that is the runtime check. Otherwise reuse the previous
version's `scripts/`.

Done when every "needs runtime" promise has a result or a stated reason it could not run.

## 6. Report

One folder per version; layout and template in [references/report-layout.md](references/report-layout.md).
Each promise gets one verdict with its evidence (static or runtime):

- **Match**: the file does what the promise says.
- **Different**: it does something else (state both); the owner picks: fix the file or the promise.
- **Bug suspect**: likely defect; say what would confirm it.
- **Partial**: some proven, the rest open.
- **Not checked**: with the reason.

If a required tool cannot run, write `BLOCKED: <tool> <reason>` and stop for the owner, so a weaker
method is never passed off as the real one.

Done when every promise has a verdict, the README version table has the new row, evidence is free of
secrets and customer data, and the owner's open questions are listed.

## 7. Record the verdict

Only when the repository has `docs/verification/modules.json`: open the bug Issues, tag the checked
commit, and update the status board as in [references/record-verdict.md](references/record-verdict.md).
Every run records its verdict, including a "report only" run or a re-check after fixes: the owner reads
the board, and the board moves only on a `rea/` tag. A merge of a PR that adds a report folder with no
tag naming it is blocked by the `rea-verdict-guard.sh` hook.
