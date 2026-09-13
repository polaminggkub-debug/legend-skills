# Acceptance and review precedents

### A1 — Distinguish regression proof from additional coverage (FastAPI)

**Use when:** an AI adds a test for a bug fix or claims a test proves a regression.

**Observed facts**

- FastAPI applies the changed-test patch to the base revision; when the base still passes, the workflow writes a warning/summary rather than failing that job. The test aggregator exists, but branch protection was not verified ([base comparison](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/test.yml#L200-L268), [aggregator](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/test.yml#L313-L332)).

**Decision and verification**

- A useful regression proof is the same test failing for the defect on the affected base and passing on the fixed revision. If base passes, report what the test actually proves; it may exercise coverage without reproducing the defect. Decide separately whether the diagnostic should block.
- Run the narrow test with the same test patch on base and current head; record both SHAs, command, environment, exit result, and pre-existing failures. Rerun when a review patch changes the behavior or verification under assessment.
- A skipped platform/dependency run is a coverage gap, not a passing behavior assertion.

**Solo adaptation (inference):** use this only for defects where a reproducible base failure is cheap. Otherwise report “regression proof unavailable” and keep a boundary/behavior test.

**Limitations:** base and head may resolve different dependencies or environments. The workflow's warning path is not a hard failure, and no branch-protection setting was observed.

### A2 — Test the shipped artifact through its real consumer (Omarchy)

**Use when:** a fix changes installers, migrations, packaged files, hardware configuration, or any path where source success can differ from delivered behavior.

**Observed facts**

- Omarchy narrowed the hardware scope and removed an unnecessary migration before merging #5435 ([scope/review](https://github.com/omacom/omarchy/issues/5423#issuecomment-4313024503), [migration decision](https://github.com/omacom/omarchy/pull/5435#discussion_r3142496458), [removal commit](https://github.com/omacom/omarchy/commit/e28d4955caac33ecda8bf8b50f8d0c1c90325762)).
- After merge, manual editing had worked but the packaged install path placed the file where the consumer did not read it. The replacement #6093 was closed unmerged; #6388 remained open while a probe/read-back and non-target checks improved evidence ([post-merge report](https://github.com/omacom/omarchy/pull/5435#issuecomment-4616309590), [replacement history](https://github.com/omacom/omarchy/pull/6093), [probe and hardware report](https://github.com/omacom/omarchy/pull/6388#issuecomment-5321029803)).

**Decision and verification**

- Candidate criteria for this class of change: the shipped installer/package writes where the real consumer reads; target behavior works. Add non-target and safe-rerun guarantees when the requested contract needs them.
- Verify from a clean install/package, read back through the real consumer, and record target/version/path. Include non-target and repeat-run observations when those guarantees apply. Do not substitute a manual edit or source-file assertion.
- Review current head after force-push; use merged-at/merge SHA to distinguish merged, replaced, and still-open work.

**Solo adaptation (inference):** for software, replace hardware with the closest real boundary: built package, container, CLI entry point, or migration from the prior schema. Keep a fake/in-memory test as a fast unit, then add one real-consumer check for the critical path.

**Limitations:** hardware and post-merge reports are contributor/tester evidence; BIOS changes confounded one result. #6388 was still open at the snapshot, so improved evidence did not equal merged behavior.

### A3 — Put the guard before the costly side effect (Goose)

**Use when:** invalid input/capability can trigger retries, inference, billing, writes, or another expensive/irreversible action.

**Observed facts**

- Goose required unsupported structured output to be rejected in both state-machine and legacy paths before retry/nudge and before model inference. Review found the legacy guard too late and moved it earlier, adding legacy coverage ([PR/acceptance](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828196036), [move-before-inference commit](https://github.com/aaif-goose/goose/commit/d656b43bfddc7df8bfdd49da13c3efbc896c99d0), [initial commit](https://github.com/aaif-goose/goose/commit/5372cf21c4c043cb25959d08529c766012cdbd48)).
- The PR reported build/tests/lint and CI success, but one pre-existing failing test was author-attributed and not independently baselined in the captured evidence ([CI records](https://github.com/aaif-goose/goose/actions/runs/32462933787)).

**Decision and verification**

- For a fail-before-side-effect requirement, include a temporal observation: unsupported capability returns the intended error before the side effect, with zero relevant boundary calls on each in-scope execution path.
- Use a spy/fake at the expensive boundary; cover the in-scope paths and distinct valid/invalid behavior; check recovery text when it is part of the contract. Record the revision and side-effect count.
- A final error after spending the cost is not “fail fast.” A successful CI job does not close a missing assertion or a pre-existing-failure gap.

**Solo adaptation (inference):** put cheap preconditions before payment/API/write/destructive operations and assert that the operation was never called. Keep recovery behavior explicit.

**Limitations:** source evidence includes author-reported test counts and a claimed pre-existing failure; no branch-protection setting was verified, and a separate follow-up issue remained out of scope.
