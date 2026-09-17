"""Offline acceptance tests for deterministic delivery-step execution."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import worker_delivery_support
import worker_delivery  # noqa: E402


class DeliveryTests(unittest.TestCase):
    def _resolver(self, calls=None):
        def command_argv(step, repo):
            if calls is not None:
                calls.append((step, repo))
            argv = list(step["argv"])
            if argv and argv[0] == "{python}":
                argv[0] = sys.executable
            return argv

        return command_argv

    def _run(self, steps, run_dir, *, env=None, resolver=None, **kwargs):
        resolver = resolver or self._resolver()
        project = types.SimpleNamespace(command_argv=resolver)
        with mock.patch.object(worker_delivery_support, "worker_project", project):
            return worker_delivery.run_steps(
                steps,
                repo=run_dir,
                run_dir=run_dir / "run",
                stage="checks",
                env=env,
                **kwargs,
            )

    def test_literal_argv_environment_filter_and_private_logs(self):
        argument = "name with spaces; & $HOME 'quoted'"
        code = (
            "import json, os, sys; "
            "print(json.dumps({'arg': sys.argv[1], "
            "'api': os.environ.get('OPENROUTER_API_KEY'), "
            "'git': os.environ.get('GIT_DIR'), "
            "'worker': os.environ.get('WORKER_CONTEXT'), "
            "'unsafe': os.environ.get('UNSAFE')}))"
        )
        steps = [
            {
                "id": "../check name *?",
                "kind": "test",
                "argv": ["{python}", "-c", code, argument],
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "ambient-secret",
                    "GIT_DIR": "ambient-git",
                    "WORKER_AMBIENT": "discard-me",
                },
                clear=False,
            ):
                results = self._run(
                    steps,
                    root,
                    env={
                        "OPENROUTER_API_KEY": "passed-secret",
                        "GIT_INDEX_FILE": "passed-git",
                        "WORKER_CONTEXT": "passed",
                        "UNSAFE": "discard-me",
                    },
                )

            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["stage"], "checks")
            self.assertEqual(result["kind"], "test")
            self.assertEqual(result["required"], True)
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["argv"][-1], argument)
            stdout_path = Path(result["stdout_path"])
            stderr_path = Path(result["stderr_path"])
            self.assertEqual(stdout_path.name, "stdout.log")
            self.assertEqual(stderr_path.name, "stderr.log")
            self.assertTrue(stdout_path.is_relative_to(root / "run" / "checks"))
            if os.name != 'nt':
                self.assertEqual(stdout_path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(stdout_path.parent.stat().st_mode & 0o777, 0o700)
            observed = json.loads(stdout_path.read_text(encoding="utf-8"))
            self.assertEqual(observed, {
                "api": None,
                "arg": argument,
                "git": None,
                "unsafe": None,
                "worker": "passed",
            })
            self.assertNotIn("/", stdout_path.parent.name)
            self.assertNotIn("\\", stdout_path.parent.name)

    def test_required_failure_is_reported_once_without_retry(self):
        calls = []
        code = "import sys; print('failure', file=sys.stderr); raise SystemExit(17)"
        steps = [{"id": "required", "kind": "lint", "argv": ["{python}", "-c", code]}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = types.SimpleNamespace(command_argv=self._resolver(calls))
            with mock.patch.object(worker_delivery_support, "worker_project", project):
                with self.assertRaises(worker_delivery.DeliveryError) as raised:
                    worker_delivery.run_steps(
                        steps,
                        repo=root,
                        run_dir=root / "run",
                        stage="checks",
                    )

            self.assertEqual(len(calls), 1)
            self.assertEqual(len(raised.exception.results), 1)
            result = raised.exception.results[0]
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["exit_code"], 17)
            self.assertEqual(Path(result["stderr_path"]).read_text().strip(), "failure")

    def test_optional_failure_allows_the_next_step(self):
        code_fail = "raise SystemExit(9)"
        code_pass = "from pathlib import Path; Path('completed').write_text('yes')"
        steps = [
            {
                "id": "optional",
                "kind": "lint",
                "argv": ["{python}", "-c", code_fail],
                "required": False,
            },
            {"id": "next", "kind": "test", "argv": ["{python}", "-c", code_pass]},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = self._run(steps, root)
            self.assertEqual([item["status"] for item in results], ["failed", "passed"])
            self.assertFalse(results[0]["required"])
            self.assertTrue((root / "completed").is_file())

    def test_timeout_is_per_step_and_stops_the_process(self):
        code = "import time; time.sleep(60)"
        steps = [
            {
                "id": "slow",
                "kind": "build",
                "argv": ["{python}", "-c", code],
                "timeout_seconds": 0.1,
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = time.monotonic()
            with self.assertRaises(worker_delivery.DeliveryError) as raised:
                self._run(steps, root)
            self.assertLess(time.monotonic() - started, 3)
            result = raised.exception.results[0]
            self.assertEqual(result["status"], "timed_out")
            self.assertEqual(result["timeout_seconds"], 0.1)
            self.assertIsNotNone(result["exit_code"])

    def test_remaining_job_time_bounds_each_subprocess(self):
        steps = [
            {
                "id": "quick",
                "kind": "test",
                "argv": ["{python}", "-c", "pass"],
            },
            {
                "id": "slow",
                "kind": "build",
                "argv": ["{python}", "-c", "import time; time.sleep(60)"],
            },
        ]
        remaining_values = iter((0.2, 0.05))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = time.monotonic()
            with self.assertRaises(worker_delivery.DeliveryError) as raised:
                self._run(
                    steps,
                    root,
                    default_timeout_seconds=2,
                    remaining_seconds=lambda: next(remaining_values),
                )
            self.assertLess(time.monotonic() - started, 3)
            results = raised.exception.results
            self.assertEqual([item["status"] for item in results], ["passed", "timed_out"])
            self.assertEqual(results[0]["timeout_seconds"], 0.2)
            self.assertEqual(results[1]["timeout_seconds"], 0.05)
            self.assertIsNotNone(results[1]["exit_code"])

    def test_guard_during_running_step_stops_child_and_preserves_exception(self):
        class BudgetExceeded(RuntimeError):
            pass

        expected = BudgetExceeded("shared job budget exhausted")
        calls = []

        def guard():
            calls.append(time.monotonic())
            # The first call is before launch.  The next call comes from the
            # monitor's first poll while the child is still sleeping.
            if len(calls) >= 2:
                raise expected

        steps = [{
            "id": "guarded",
            "kind": "build",
            "argv": ["{python}", "-c", "import time; time.sleep(60)"],
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = time.monotonic()
            with self.assertRaises(BudgetExceeded) as raised:
                self._run(steps, root, guard=guard)
            self.assertLess(time.monotonic() - started, 3)
            self.assertIs(raised.exception, expected)
            self.assertEqual(len(raised.exception.delivery_results), 1)
            result = raised.exception.delivery_results[0]
            self.assertEqual(result["status"], "budget_exceeded")
            self.assertIsNotNone(result["exit_code"])
            self.assertGreaterEqual(len(calls), 2)

    def test_keyboard_interrupt_stops_process_and_carries_partial_results(self):
        code = "import time; time.sleep(60)"

        class InterruptingMonitor:
            def __init__(self, *args, **kwargs):
                self.kwargs = kwargs

            def wait(self, process):
                raise KeyboardInterrupt()

            def record(self, process, state=None):
                return {"state": state}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = types.SimpleNamespace(command_argv=self._resolver())
            monitor_holder = {}

            class CapturingInterruptingMonitor(InterruptingMonitor):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    monitor_holder["kwargs"] = kwargs

            with mock.patch.object(worker_delivery_support, "worker_project", project):
                with mock.patch.object(worker_delivery_support, "ProcessMonitor", CapturingInterruptingMonitor):
                    with self.assertRaises(worker_delivery.DeliveryInterrupted) as raised:
                        worker_delivery.run_steps(
                            [{"id": "cancelled", "argv": ["{python}", "-c", code]}],
                            repo=root,
                            run_dir=root / "run",
                            stage="checks",
                        )

            self.assertIsInstance(raised.exception, KeyboardInterrupt)
            self.assertEqual(len(raised.exception.results), 1)
            self.assertEqual(raised.exception.results[0]["status"], "interrupted")
            self.assertEqual(monitor_holder["kwargs"]["interval_seconds"], 5)
            self.assertEqual(monitor_holder["kwargs"]["cancel_path"], root / "run" / "cancel.request")

    def test_preexisting_cancel_request_launches_no_command(self):
        calls = []
        code = "raise SystemExit(99)"
        steps = [{"id": "already-cancelled", "argv": ["{python}", "-c", code]}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            run_dir.mkdir()
            (run_dir / "cancel.request").write_text("cancel\n", encoding="utf-8")
            project = types.SimpleNamespace(command_argv=self._resolver(calls))
            with mock.patch.object(worker_delivery_support, "worker_project", project):
                with mock.patch.object(worker_delivery.subprocess, "Popen") as popen:
                    with self.assertRaises(worker_delivery.DeliveryInterrupted) as raised:
                        worker_delivery.run_steps(
                            steps,
                            repo=root,
                            run_dir=run_dir,
                            stage="checks",
                        )

            popen.assert_not_called()
            self.assertEqual(calls, [])
            self.assertEqual(len(raised.exception.results), 1)
            self.assertEqual(raised.exception.results[0]["status"], "interrupted")

    def test_stage_and_digest_keep_colliding_log_directories_distinct(self):
        def command(label):
            return {
                "id": label,
                "kind": "test",
                "argv": ["{python}", "-c", "import sys; print(sys.argv[1])", label],
            }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = types.SimpleNamespace(command_argv=self._resolver())
            with mock.patch.object(worker_delivery_support, "worker_project", project):
                same_stage = worker_delivery.run_steps(
                    [command("unit/a"), command("unit_a"), command("Check"), command("check")],
                    repo=root,
                    run_dir=root / "run",
                    stage="before_commit",
                )
                before = worker_delivery.run_steps(
                    [command("same")],
                    repo=root,
                    run_dir=root / "run",
                    stage="before_commit",
                )[0]
                after = worker_delivery.run_steps(
                    [command("same")],
                    repo=root,
                    run_dir=root / "run",
                    stage="after_commit",
                )[0]

            same_paths = [Path(item["stdout_path"]) for item in same_stage]
            self.assertEqual(len({path.parent.name.casefold() for path in same_paths}), 4)
            for item in same_stage:
                self.assertEqual(
                    Path(item["stdout_path"]).read_text(encoding="utf-8").strip(),
                    item["id"],
                )
            self.assertNotEqual(Path(before["stdout_path"]).parent, Path(after["stdout_path"]).parent)
            self.assertIn("before_commit", Path(before["stdout_path"]).parent.name)
            self.assertIn("after_commit", Path(after["stdout_path"]).parent.name)
            self.assertEqual(Path(before["stdout_path"]).read_text(encoding="utf-8").strip(), "same")
            self.assertEqual(Path(after["stdout_path"]).read_text(encoding="utf-8").strip(), "same")


if __name__ == "__main__":
    unittest.main()
