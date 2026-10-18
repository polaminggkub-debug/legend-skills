# Runtime check kinds

Each scenario: promise ID, setup, steps, observable, pass/fail rule. Scripts never wait for a click:
they set their own permissions, network and time limits, so a stuck step fails fast instead of
hanging. Use copies of customer data; the original stays untouched (hash it before and after).

| Kind | What it proves | How on Windows | How on Linux/macOS |
|---|---|---|---|
| Behaviour trace | Files, registry keys, network hosts and processes the program really touches; read-only where read-only was promised | ProcMon capture filtered to the process, or ETW | REA `capture-process` (terminal, process tree, file snapshots) |
| Network scope | It talks only to the promised hosts | ProcMon network events, `netstat`, firewall log | REA `capture-process`, `tcpdump` + REA `inspect-pcap-capture` |
| Happy path | The promise works end to end (data in → expected result out) | Scripted run in the VM, then query the result | same |
| Timing | Promised intervals and delays (settle time, polling, retry backoff) | Timestamps from the trace or the program's log | same |
| Negative | It refuses what it must refuse: tampered or unsigned update, wrong token, bad config | Serve a broken manifest/file locally and watch the outcome | same |
| Recovery | Crash on start, no heartbeat, killed mid-write, disk full, locked file | Kill/lock in the VM, watch rollback or retry | same |
| Odd data | Empty, null, huge, out-of-range, duplicate, wrong-timezone input | Edit a copy of the data store, run once | same |
| Install and permissions | Folder ACLs, secret file ACLs, service account, start mode, per-user parts | `icacls`, `sc qc`, `Get-Acl` in the VM | `ls -l`, `stat`, service unit files |
| Upgrade | Old version → new version keeps config and data | Install previous release, then update | same |

## Time budget: the whole runtime run finishes in about 10 minutes

The owner reads the result, not the log. Ten minutes is already long for them, so plan the
run to give its verdict inside that budget:

- Never wait for the program's own slow timer (hourly retry, nightly job). Trigger the work
  instead: its "send now" or command file, a restart, a config value that shortens the
  interval, or a clock moved forward in the VM.
- Run independent scenarios at the same time on separate data copies or VM folders, not one
  after another.
- Keep one wait to 2 minutes at most. A behaviour that only shows after a longer wait gets
  **Not checked (needs N min)** with the trigger that would show it sooner.
- Size huge-data tests down: grow the data until the trend is clear (memory, duration), then
  estimate the large case. Building a multi-million-row copy is not worth the minutes.
- Reuse the previous run's setup scripts so the first minutes are not spent on plumbing.

If the plan cannot fit, cut scenarios and list them as Not checked. Do not stretch the run.

A scenario that cannot run (missing OS, hardware, licence) gets verdict **Not checked** with that
reason, never a silent skip.

## One-command runners

A runner is one command that runs every scenario of a program and prints one `PASS|FAIL|NOT-CHECKED
<id> <reason>` line per Issue and promise, plus the total wall-clock. The AI starts it and reads the
result; it does not drive the steps.

- `ONLY=<ids>` while fixing a bug (e.g. `ONLY=447`, `ONLY=444,F12`): the report says `PARTIAL RUN —
  not a release verdict`. An unknown id stops the run at once and lists the valid ids.
- The full run (no `ONLY`) before every release: that run is the verdict.
- A new bug or promise gets its check added to the runner, not a one-off script.

| Program | Machine | Command | Notes |
|---|---|---|---|
| HipAgent (ssp-erp) | poo | `[ONLY=<ids>] tools/hip-agent/scripts/vm-regression.sh <HipAgent.exe> [--long]` | Parallel clones of the golden Windows image `~/vm/hip-golden/` (RAM snapshot, 6 s per clone), private Supabase stack `hipfast`. Full run 6:31 on 1.3.0; `ONLY=<one id>` about 3:45. A trap removes every clone and the stack, leaving only `win-test`. `--long` adds the 2M-row DB and hourly cases. Golden eval expires 2027-01-15: rebuild with `vm-golden-build.sh all` (about 1 h) before then. |
