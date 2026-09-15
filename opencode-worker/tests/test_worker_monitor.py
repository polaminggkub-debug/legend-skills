"""Focused, offline tests for the long running worker process monitor."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import worker_monitor  # noqa: E402  (the module under test lives at repo root)


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0

    def monotonic(self) -> float:
        return self.current

    def time(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class FakeProcess:
    """Small Popen-shaped process; it never starts a child or emits stdout."""

    def __init__(
        self,
        clock: FakeClock,
        *,
        exit_after: float | None = None,
        exit_code: int = 0,
        initial_returncode: int | None = None,
        on_wait=None,
    ) -> None:
        self.clock = clock
        self.pid = 4242
        self.args = ["mock-opencode", "run"]
        self.exit_after = exit_after
        self.exit_code = exit_code
        self._returncode = initial_returncode
        self.on_wait = on_wait
        self.poll_calls = 0
        self.wait_timeouts = []
        self.terminate_calls = 0
        self.kill_calls = 0

    @property
    def returncode(self):
        return self._returncode

    def poll(self):
        self.poll_calls += 1
        self._finish_if_due()
        return self._returncode

    def wait(self, timeout=None):
        self.wait_timeouts.append(timeout)
        if self._returncode is not None:
            return self._returncode
        if timeout is None:
            raise AssertionError("the monitor must use a bounded process wait")
        self.clock.advance(timeout)
        if self.on_wait is not None:
            self.on_wait(self)
        self._finish_if_due()
        if self._returncode is None:
            raise subprocess.TimeoutExpired("mock-opencode", timeout)
        return self._returncode

    def terminate(self):
        self.terminate_calls += 1
        raise AssertionError("termination belongs to the caller")

    def kill(self):
        self.kill_calls += 1
        raise AssertionError("termination belongs to the caller")

    def _finish_if_due(self) -> None:
        if (
            self._returncode is None
            and self.exit_after is not None
            and self.clock.current >= self.exit_after
        ):
            self._returncode = self.exit_code


class ProcessMonitorTests(unittest.TestCase):
    def _clock(self, clock: FakeClock):
        """Make monitor timing deterministic without sleeping."""

        return mock.patch.multiple(
            worker_monitor.time,
            monotonic=mock.Mock(side_effect=clock.monotonic),
            time=mock.Mock(side_effect=clock.time),
        )

    def _snapshot(self, run_dir: Path):
        return json.loads((run_dir / "heartbeat.json").read_text(encoding="utf-8"))

    def test_constructor_rejects_nonfinite_or_nonpositive_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            for value in (0, -1, float("inf"), float("-inf"), float("nan")):
                with self.subTest(field="interval", value=value):
                    with self.assertRaises(ValueError):
                        worker_monitor.ProcessMonitor(run_dir, interval_seconds=value)
                with self.subTest(field="timeout", value=value):
                    with self.assertRaises(ValueError):
                        worker_monitor.ProcessMonitor(run_dir, timeout_seconds=value)

            monitor = worker_monitor.ProcessMonitor(run_dir, timeout_seconds=None)
            self.assertEqual(monitor.timeout_seconds, None)

    def test_record_writes_private_atomic_snapshot_and_accepts_supplied_state(self):
        clock = FakeClock()
        process = FakeProcess(clock)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            (run_dir / "events.jsonl").write_bytes(b"abc")
            (run_dir / "stderr.log").write_bytes(b"xy")
            with self._clock(clock):
                monitor = worker_monitor.ProcessMonitor(run_dir, interval_seconds=5)
                monitor.record(process, state="paused")

            snapshot = self._snapshot(run_dir)
            self.assertEqual(snapshot["state"], "paused")
            self.assertTrue(snapshot["process_running"])
            self.assertIsNone(snapshot["exit_code"])
            self.assertEqual(snapshot["elapsed_seconds"], 0)
            self.assertEqual(snapshot["interval_seconds"], 5)
            self.assertIsNone(snapshot["timeout_seconds"])
            self.assertEqual(snapshot["events_bytes"], 3)
            self.assertEqual(snapshot["stderr_bytes"], 2)
            self.assertEqual(snapshot["heartbeat_count"], 1)
            self.assertIsInstance(snapshot["checked_at"], str)
            self.assertTrue(snapshot["checked_at"])
            if os.name != "nt":
                self.assertEqual((run_dir / "heartbeat.json").stat().st_mode & 0o777, 0o600)
            self.assertFalse(list(run_dir.glob("heartbeat.json*.tmp")))

    def test_quiet_process_survives_more_than_1200_seconds_with_five_second_checks(self):
        clock = FakeClock()
        process = FakeProcess(clock, exit_after=1205, exit_code=0)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            with self._clock(clock):
                monitor = worker_monitor.ProcessMonitor(run_dir)
                result = monitor.wait(process)

            snapshot = self._snapshot(run_dir)
            self.assertEqual(result, 0)
            self.assertEqual(snapshot["state"], "exited")
            self.assertFalse(snapshot["process_running"])
            self.assertEqual(snapshot["exit_code"], 0)
            self.assertEqual(snapshot["elapsed_seconds"], 1205)
            self.assertEqual(snapshot["interval_seconds"], 5)
            self.assertIsNone(snapshot["timeout_seconds"])
            self.assertGreater(snapshot["heartbeat_count"], 200)
            self.assertEqual(process.wait_timeouts, [5] * 241)
            self.assertEqual(process.terminate_calls, 0)
            self.assertEqual(process.kill_calls, 0)

    def test_active_process_survives_more_than_1200_seconds_and_sizes_are_refreshed(self):
        clock = FakeClock()
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            events_path = run_dir / "events.jsonl"
            stderr_path = run_dir / "stderr.log"

            def append_activity(_process):
                with events_path.open("ab") as stream:
                    stream.write(b"e")
                with stderr_path.open("ab") as stream:
                    stream.write(b"err")

            process = FakeProcess(clock, exit_after=1210, on_wait=append_activity)
            with self._clock(clock):
                monitor = worker_monitor.ProcessMonitor(run_dir)
                result = monitor.wait(process)

            snapshot = self._snapshot(run_dir)
            self.assertEqual(result, 0)
            self.assertEqual(snapshot["state"], "exited")
            self.assertEqual(snapshot["events_bytes"], 242)
            self.assertEqual(snapshot["stderr_bytes"], 726)
            self.assertEqual(snapshot["elapsed_seconds"], 1210)
            self.assertGreater(snapshot["heartbeat_count"], 200)
            self.assertEqual(process.wait_timeouts, [5] * 242)

    def test_early_zero_and_nonzero_exit_are_recorded_without_extra_wait(self):
        for exit_code in (0, 17):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as directory:
                clock = FakeClock()
                process = FakeProcess(clock, initial_returncode=exit_code)
                run_dir = Path(directory)
                with self._clock(clock):
                    monitor = worker_monitor.ProcessMonitor(run_dir)
                    result = monitor.wait(process)

                snapshot = self._snapshot(run_dir)
                self.assertEqual(result, exit_code)
                self.assertEqual(snapshot["state"], "exited")
                self.assertFalse(snapshot["process_running"])
                self.assertEqual(snapshot["exit_code"], exit_code)
                self.assertGreaterEqual(snapshot["heartbeat_count"], 1)
                self.assertEqual(process.wait_timeouts, [])
                self.assertEqual(process.terminate_calls, 0)
                self.assertEqual(process.kill_calls, 0)

    def test_explicit_timeout_checks_remaining_time_and_leaves_termination_to_caller(self):
        clock = FakeClock()
        process = FakeProcess(clock)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            with self._clock(clock):
                monitor = worker_monitor.ProcessMonitor(run_dir, timeout_seconds=12)
                with self.assertRaises(subprocess.TimeoutExpired):
                    monitor.wait(process)

            snapshot = self._snapshot(run_dir)
            self.assertEqual(snapshot["state"], "running")
            self.assertTrue(snapshot["process_running"])
            self.assertIsNone(snapshot["exit_code"])
            self.assertEqual(snapshot["elapsed_seconds"], 12)
            self.assertEqual(snapshot["interval_seconds"], 5)
            self.assertEqual(snapshot["timeout_seconds"], 12)
            self.assertGreaterEqual(snapshot["heartbeat_count"], 3)
            self.assertEqual(process.wait_timeouts, [5, 5, 2])
            self.assertEqual(process.terminate_calls, 0)
            self.assertEqual(process.kill_calls, 0)


if __name__ == "__main__":
    unittest.main()
