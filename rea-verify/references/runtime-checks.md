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

A scenario that cannot run (missing OS, hardware, licence) gets verdict **Not checked** with that
reason, never a silent skip.
