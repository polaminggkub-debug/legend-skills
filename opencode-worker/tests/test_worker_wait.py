"""Offline tests for quiet, resumable worker waiting."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker_wait import (  # noqa: E402
    InvalidRunIdError,
    MissingReportError,
    MissingRunError,
    RunTimeoutError,
    StaleRunError,
    TerminalOpenCodeError,
    active_runs,
    wait_for_run,
)


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0

    def monotonic(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class WorkerWaitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="worker-wait-tests-")
        self.base = Path(self.temp_dir.name)
        self.run_id = str(uuid.uuid4())
        self.run_dir = self.base / "runs" / self.run_id
        self.run_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _report(self, **updates):
        value = {
            "schema_version": 1,
            "run_id": self.run_id,
            "status": "running",
            "phase": "model",
            "finalized": False,
            "launcher_pid": os.getpid(),
            "observed_models": [],
            "metrics": {},
            "git": {"commit": None},
            "checks": {"status": "pending"},
        }
        value.update(updates)
        return value

    def _write_report(self, value):
        target = self.run_dir / "report.json"
        temp = target.with_name(target.name + ".tmp")
        temp.write_text(json.dumps(value) + "\n", encoding="utf-8")
        temp.replace(target)

    def test_invalid_run_and_missing_report_fail_clearly(self):
        with self.assertRaises(InvalidRunIdError):
            wait_for_run(self.base, "not-a-uuid")
        with self.assertRaises(InvalidRunIdError):
            wait_for_run(self.base, self.run_id.upper())

        missing = str(uuid.uuid4())
        with self.assertRaises(MissingRunError):
            wait_for_run(self.base, missing)

        error = None
        try:
            wait_for_run(self.base, self.run_id)
        except MissingReportError as exc:
            error = exc
        self.assertIsNotNone(error)
        self.assertIn("run report is missing", str(error))

    def test_subprocess_completion_returns_compact_report_without_stdout(self):
        self._write_report(self._report())
        final = self._report(
            status="committed",
            phase="finished",
            finalized=True,
            observed_models=["openrouter/test-model"],
            metrics={"tokens": {"total": 3}, "completed": True},
            git={"commit": "abc123"},
            elapsed_seconds=0.08,
        )
        report_path = self.run_dir / "report.json"
        payload = json.dumps(final)
        script = (
            "import json, pathlib, sys, time; "
            "time.sleep(0.08); "
            "p=pathlib.Path(sys.argv[1]); t=p.with_name(p.name+'.tmp'); "
            "t.write_text(sys.argv[2]+'\\n', encoding='utf-8'); t.replace(p)"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", script, str(report_path), payload],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = wait_for_run(
                    self.base,
                    self.run_id,
                    interval_seconds=0.01,
                    process_probe=lambda pid: pid == os.getpid(),
                )
        finally:
            process.wait(timeout=3)

        self.assertEqual(output.getvalue(), "")
        self.assertEqual(result["status"], "committed")
        self.assertEqual(result["run_id"], self.run_id)
        self.assertEqual(result["commit"], "abc123")
        self.assertEqual(result["model"], ["openrouter/test-model"])
        self.assertEqual(result["report"], str(report_path))
        self.assertNotIn("prompt_sha256", result)

    def test_quiet_job_can_wait_beyond_twenty_minutes_without_default_timeout(self):
        clock = FakeClock()
        self._write_report(self._report())

        def sleep(seconds):
            clock.advance(seconds)
            if clock.current >= 1205 and json.loads(
                (self.run_dir / "report.json").read_text(encoding="utf-8")
            )["finalized"] is False:
                self._write_report(
                    self._report(
                        status="no_changes",
                        phase="finished",
                        finalized=True,
                        elapsed_seconds=1205,
                    )
                )

        result = wait_for_run(
            self.base,
            self.run_id,
            interval_seconds=5,
            process_probe=lambda pid: True,
            sleep_fn=sleep,
            clock=clock.monotonic,
        )
        self.assertEqual(result["status"], "no_changes")
        self.assertEqual(clock.current, 1205)

    def test_cancel_request_is_left_to_worker_and_wait_returns_interrupted_report(self):
        self._write_report(self._report())
        cancel = self.run_dir / "cancel.request"
        cancel.write_text('{"requested":true}\n', encoding="utf-8")
        finished = []

        def sleep(_seconds):
            if not finished:
                self._write_report(
                    self._report(status="interrupted", finalized=True, error="cancelled")
                )
                finished.append(True)

        result = wait_for_run(
            self.base,
            self.run_id,
            interval_seconds=0.01,
            cancel_path=cancel,
            process_probe=lambda pid: True,
            sleep_fn=sleep,
        )
        self.assertEqual(result["status"], "interrupted")
        self.assertTrue(cancel.exists())

    def test_dead_recorded_wrapper_fails_but_legacy_silence_does_not(self):
        self._write_report(self._report(launcher_pid=999999))
        with self.assertRaises(StaleRunError):
            wait_for_run(self.base, self.run_id, process_probe=lambda pid: False)

        legacy_report = self._report()
        legacy_report.pop("launcher_pid", None)
        self._write_report(legacy_report)
        clock = FakeClock()
        with self.assertRaises(RunTimeoutError):
            wait_for_run(
                self.base,
                self.run_id,
                interval_seconds=5,
                timeout_seconds=10,
                process_probe=lambda pid: False,
                sleep_fn=clock.advance,
                clock=clock.monotonic,
            )
        self.assertEqual(clock.current, 10)

    def test_active_runs_uses_recorded_pid_and_excludes_exited_legacy_reports(self):
        self._write_report(self._report(launcher_pid=101))
        legacy_id = str(uuid.uuid4())
        legacy = self.base / "runs" / legacy_id
        legacy.mkdir()
        legacy_report = dict(self._report(launcher_pid=None))
        legacy_report["run_id"] = legacy_id
        legacy_report.pop("launcher_pid", None)
        (legacy / "report.json").write_text(json.dumps(legacy_report) + "\n", encoding="utf-8")
        (legacy / "heartbeat.json").write_text(
            json.dumps({"pid": 202, "process_running": True}) + "\n", encoding="utf-8"
        )
        exited_id = str(uuid.uuid4())
        exited = self.base / "runs" / exited_id
        exited.mkdir()
        exited_report = dict(legacy_report)
        exited_report["run_id"] = exited_id
        (exited / "report.json").write_text(json.dumps(exited_report) + "\n", encoding="utf-8")
        (exited / "heartbeat.json").write_text(
            json.dumps({"pid": 303, "process_running": False}) + "\n", encoding="utf-8"
        )

        alive = {101, 202}
        result = active_runs(self.base, process_probe=lambda pid: pid in alive)
        self.assertEqual(result, sorted([self.run_id, legacy_id]))

    def test_transient_error_is_not_terminal_but_explicit_nonretryable_is(self):
        self._write_report(self._report())
        events = self.run_dir / "events.jsonl"
        events.write_text(
            json.dumps(
                {
                    "type": "error",
                    "error": {"name": "Retryable", "data": {"isRetryable": True}},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        clock = FakeClock()
        with self.assertRaises(RunTimeoutError):
            wait_for_run(
                self.base,
                self.run_id,
                interval_seconds=5,
                timeout_seconds=5,
                process_probe=lambda pid: True,
                sleep_fn=clock.advance,
                clock=clock.monotonic,
            )

        events.write_text(
            json.dumps(
                {
                    "type": "error",
                    "error": {"name": "Quota Error/secret", "data": {"isRetryable": False}},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(TerminalOpenCodeError) as raised:
            wait_for_run(self.base, self.run_id, process_probe=lambda pid: True)
        self.assertEqual(raised.exception.name, "Quota_Error_secret")


if __name__ == "__main__":
    unittest.main()
