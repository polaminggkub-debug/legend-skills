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

Treat the **shipped file** as the only witness. Source code shows what someone meant to build; the
file the customer runs shows what was built. Each run checks one version against its **promises**
(what the Issues, guides and release notes say it does) and ends with a **verdict** per promise.

Scope: programs the user owns or builds. Someone else's program is out of scope for this skill.

## 1. Pin the target

- Take the file from where it ships (release host, install kit). Record name, version and sha256, and
  match the sha256 against the published manifest or release note. A mismatch is the first finding.
- Work in a scratch folder outside every repository. Put the shipped file in its own empty folder.
- Keep the source tree closed for the whole run. The value of this check is independence: a promise
  is judged from the requirement text and the file, never from what the code was meant to do.

Done when the target's sha256 is written down and matches its release record (or the mismatch is).

## 2. Write the promises (the oracle)

Load the `chris` skill and turn every requirement into a checkable promise, `F1`…`Fn`, each citing its
source (Issue number, guide section, release note). Sources: closed Issues touching the program since
the previous verified version, the user guide shipped with it, the release notes. For a new version,
start from the previous version's `checklist.md` and add the promises closed since.

Done when every closed Issue for this program since the last verified version maps to at least one
promise or is listed as "no observable promise".

## 3. Open the file

Route by format; [references/formats.md](references/formats.md) has the commands.

- .NET single-file exe: REA reports `not-managed`, because the app hides inside the apphost. Unpack
  with `scripts/unbundle.py`, then point REA at the app DLLs.
- Plain .NET assembly: REA `inspect-managed-members --format json`.
- Electron / JavaScript: REA `analyze-javascript-application`.
- Native: REA `open_binary` with Ghidra/IDA, or `inspect-go-binary` / `inspect-rust-binary`.

Done when every app module (not framework files) has REA evidence saved to disk.

## 4. Static checks

Read evidence through `scripts/managed_evidence.py` (strings, callers, IL constants) so large JSON
never enters context. For each promise, find the code that carries it and the facts that prove or
break it: the literal that names the file, the constant that sets the timing, the call edge that
proves who reads the secret. Then sweep for what the promises never mention:

- **Suspected bugs:** decompile the methods behind each promise (ILSpy for .NET) and review them; use
  the finecomb plugin checklist when installed. Look for swallowed exceptions, endless retries,
  local-vs-UTC time, null handling, SQL built from strings, writes where only reads were promised.
- **Version diff:** compare members with the previous verified version (`compare-managed-members`).
  A change no promise or release note explains is a finding.
- **Secrets:** scan all string literals for keys, tokens, passwords, private URLs.
- **Dependencies:** list bundled libraries and versions; check them for known CVEs.
- **Extras:** features in the file that no promise asked for.

Done when every promise has static evidence or is marked "needs runtime".

## 5. Runtime checks on the worker

Static evidence proves code is present and wired; it cannot prove it works. Every runtime check runs
on the worker machine: the one named in `~/.claude/docs/work-routing.md` when that file exists
(brief it with `poo-handoff` when installed), otherwise the machine the user names. Run inside a VM
or container that matches the customer's OS; the user's own computer only reads results. REA
`capture-process` records Linux/macOS processes only; on Windows trace with ProcMon or ETW.

Build scenarios from the promises: [references/runtime-checks.md](references/runtime-checks.md)
lists the kinds. Each scenario names the promise, the steps, and the observable that turns it pass
or fail. Use copies of data, never the customer's live data.

Done when every promise marked "needs runtime" has a scenario result or a stated reason it could
not run.

## 6. Report

Write one folder per version; [references/report-layout.md](references/report-layout.md) has the
layout and template. Each promise gets one verdict, with its evidence and whether that evidence is
static or runtime:

- **Match**: the file does what the promise says.
- **Different**: the file does something else (state both). The owner decides: fix the file, or fix
  the promise.
- **Bug suspect**: evidence of a likely defect; say what would confirm it.
- **Partial**: some of the promise proven, the rest open.
- **Not checked**: with the reason.

Done when every promise has a verdict, the folder README's version table has the new row, every
evidence file is free of secrets and customer data, and the owner's open questions are listed.
