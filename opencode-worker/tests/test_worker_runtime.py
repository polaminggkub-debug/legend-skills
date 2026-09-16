"""Acceptance tests for the OpenCode/OpenRouter worker runtime.

The tests deliberately use only the Python standard library.  The fake
OpenCode executable emits the JSONL event shape used by the recorded Dino
runs, and writes the assistant model row that a real OpenCode run leaves in
its SQLite database.  No network, keychain, or installed OpenCode process is
needed to run this suite.
"""

from __future__ import annotations

import contextlib
import csv
import io
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import worker_runtime  # noqa: E402  (the module under test lives at repo root)


MODEL = "deepseek/deepseek-v4.1-flash"
PYTHON = sys.executable


# This is intentionally a small projection of the event shape in
# runs/dino-one-way/events.jsonl.  The runtime must use metadata from the
# step_finish event; it must not need to inspect tool/text content.
FAKE_OPENCODE = r'''#!/usr/bin/python3
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid


MODEL = "deepseek/deepseek-v4.1-flash"


def append_log(entry):
    path = Path(os.environ["FAKE_LOG"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, sort_keys=True) + "\n")


def option(args, name, default=None):
    try:
        return args[args.index(name) + 1]
    except (ValueError, IndexError):
        return default


def event(kind, session_id, part):
    return {
        "type": kind,
        "timestamp": int(time.time() * 1000),
        "sessionID": session_id,
        "part": part,
    }


def emit(events):
    for item in events:
        print(json.dumps(item, separators=(",", ":")), flush=True)


def put_model_observation(session_id, provider="openrouter", model_id=MODEL):
    provider = os.environ.get("FAKE_PROVIDER", provider)
    if model_id == MODEL:
        model_id = os.environ.get("FAKE_MODEL", model_id)
    # The worker points OpenCode at an isolated XDG data directory.  The
    # explicit fixture override keeps this fake deterministic when the test
    # calls the runtime in-process.
    data_home = Path(os.environ.get("FAKE_DATA_HOME", os.environ.get("XDG_DATA_HOME", ".")))
    db_path = data_home / "opencode" / "opencode.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS message (session_id TEXT, data TEXT)"
        )
        connection.execute(
            "INSERT INTO message(session_id, data) VALUES (?, ?)",
            (
                session_id,
                json.dumps(
                    {
                        "role": "assistant",
                        "providerID": provider,
                        "modelID": model_id,
                    },
                    separators=(",", ":"),
                ),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def main():
    args = sys.argv[1:]
    behavior = os.environ.get("FAKE_BEHAVIOR", "success")
    append_log({"kind": "invocation", "argv": args, "behavior": behavior})

    if "--version" in args or args[:1] == ["version"]:
        if behavior == "version_failure":
            print("fixture version probe failed", file=sys.stderr, flush=True)
            return 23
        if behavior == "version_bad":
            print("fixture", flush=True)
            return 0
        print("opencode 1.18.31", flush=True)
        return 0

    if not args or args[0] != "run":
        print("unsupported fake OpenCode invocation", file=sys.stderr, flush=True)
        return 24

    repo = Path(option(args, "--dir", ".")).resolve()
    model = option(args, "--model")
    output_format = option(args, "--format")
    title = option(args, "--title")
    session_id = "ses_fixture_" + uuid.uuid4().hex
    step_id = "prt_fixture_" + uuid.uuid4().hex
    message_id = "msg_fixture_" + uuid.uuid4().hex
    finish_id = "prt_fixture_" + uuid.uuid4().hex
    append_log(
        {
            "kind": "run",
            "argv": args,
            "repo": str(repo),
            "model": model,
            "format": output_format,
            "title": title,
            "sessionID": session_id,
        }
    )

    if behavior == "lock_probe":
        active = Path(os.environ["FAKE_ACTIVE"])
        overlap = Path(os.environ["FAKE_OVERLAP"])
        pid_path = os.environ.get("FAKE_PID")
        if pid_path:
            Path(pid_path).write_text(str(os.getpid()), encoding="utf-8")
        if active.exists():
            overlap.write_text("concurrent fake invocation\n", encoding="utf-8")
        active.write_text(session_id, encoding="utf-8")
        time.sleep(float(os.environ.get("FAKE_SLEEP_SECONDS", "0.8")))
        try:
            active.unlink()
        except FileNotFoundError:
            pass
        put_model_observation(session_id)
        emit(
            [
                event(
                    "step_start",
                    session_id,
                    {
                        "id": step_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-start",
                    },
                ),
                event(
                    "step_finish",
                    session_id,
                    {
                        "id": finish_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-finish",
                        "reason": "stop",
                        "tokens": {
                            "total": 27,
                            "input": 10,
                            "output": 7,
                            "reasoning": 4,
                            "cache": {"read": 3, "write": 3},
                        },
                        "cost": 0.00125,
                    },
                ),
            ]
        )
        return 0

    if behavior == "sleep_then_success":
        time.sleep(float(os.environ.get("FAKE_SLEEP_SECONDS", "0.8")))

    if behavior in ("success", "commit_hook", "head_change", "sleep_then_success"):
        source = repo / "src" / "app.txt"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("worker output\n", encoding="utf-8")
        if behavior == "head_change":
            subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), "add", "src/app.txt"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "-C",
                    str(repo),
                    "commit",
                    "-m",
                    "unrelated worker head change",
                ],
                check=True,
            )
        put_model_observation(session_id)
        emit(
            [
                event(
                    "step_start",
                    session_id,
                    {
                        "id": step_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-start",
                    },
                ),
                event(
                    "step_finish",
                    session_id,
                    {
                        "id": finish_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-finish",
                        "reason": "stop",
                        "tokens": {
                            "total": 27,
                            "input": 10,
                            "output": 7,
                            "reasoning": 4,
                            "cache": {"read": 3, "write": 3},
                        },
                        "cost": 0.00125,
                    },
                ),
            ]
        )
        return 0

    if behavior == "no_change":
        put_model_observation(session_id)
        emit(
            [
                event(
                    "step_start",
                    session_id,
                    {
                        "id": step_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-start",
                    },
                ),
                event(
                    "step_finish",
                    session_id,
                    {
                        "id": finish_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-finish",
                        "reason": "stop",
                        "tokens": {
                            "total": 27,
                            "input": 10,
                            "output": 7,
                            "reasoning": 4,
                            "cache": {"read": 3, "write": 3},
                        },
                        "cost": 0.00125,
                    },
                ),
            ]
        )
        return 0

    if behavior in ("missing_model", "mismatching_model"):
        # Valid telemetry with absent or contradictory assistant evidence lets
        # the runtime distinguish requested model text from observed evidence.
        if behavior == "mismatching_model":
            put_model_observation(session_id, model_id="some-other-model")
        emit(
            [
                event(
                    "step_finish",
                    session_id,
                    {
                        "id": finish_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-finish",
                        "reason": "stop",
                        "tokens": {
                            "total": 27,
                            "input": 10,
                            "output": 7,
                            "reasoning": 4,
                            "cache": {"read": 3, "write": 3},
                        },
                        "cost": 0.00125,
                    },
                )
            ]
        )
        return 0

    if behavior == "missing_telemetry":
        put_model_observation(session_id)
        emit(
            [
                event(
                    "step_start",
                    session_id,
                    {
                        "id": step_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-start",
                    },
                )
            ]
        )
        return 0

    if behavior == "malformed_telemetry":
        put_model_observation(session_id)
        print(json.dumps({"type": "step_finish", "part": {"reason": "stop"}}), flush=True)
        return 0

    if behavior == "failure":
        put_model_observation(session_id)
        emit(
            [
                event(
                    "step_finish",
                    session_id,
                    {
                        "id": finish_id,
                        "messageID": message_id,
                        "sessionID": session_id,
                        "type": "step-finish",
                        "reason": "stop",
                        "tokens": {
                            "total": 27,
                            "input": 10,
                            "output": 7,
                            "reasoning": 4,
                            "cache": {"read": 3, "write": 3},
                        },
                        "cost": 0.00125,
                    },
                )
            ]
        )
        print("fixture worker failed", file=sys.stderr, flush=True)
        return 17

    print("unknown fixture behavior", file=sys.stderr, flush=True)
    return 25


if __name__ == "__main__":
    raise SystemExit(main())
'''


class WorkerRuntimeAcceptanceTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="worker-runtime-tests-")
        self.tmp = Path(self.temp_dir.name).resolve()
        self.base = self.tmp / "worker-state"
        self.base.mkdir()
        self.fake = self.tmp / "fake-opencode.py"
        self.fake.write_text(FAKE_OPENCODE, encoding="utf-8")
        self.fake.chmod(0o755)
        self.log = self.base / "fake-invocations.jsonl"
        self.fake_data_home = self.base / "data"
        self.settings = {
            "default_model": MODEL,
            "cli_binary": str(self.fake),
            "default_job_timeout_seconds": None,
            "heartbeat_interval_seconds": 0.05,
            "hello_timeout_seconds": 3,
        }
        (self.base / "settings.json").write_text(
            json.dumps(self.settings, indent=2) + "\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_repo(self, name="repo"):
        repo = self.tmp / name
        repo.mkdir()
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.name", "Worker Test")
        self.git(repo, "config", "user.email", "worker-test@example.invalid")
        source = repo / "src" / "app.txt"
        source.parent.mkdir(parents=True)
        source.write_text("initial\n", encoding="utf-8")
        self.git(repo, "add", "src/app.txt")
        self.git(repo, "commit", "-qm", "initial source")
        return repo

    @staticmethod
    def git(repo, *args, check=True):
        return subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def env_for(self, behavior="success", **extra):
        env = {
            "FAKE_BEHAVIOR": behavior,
            "FAKE_LOG": str(self.log),
            "FAKE_DATA_HOME": str(self.fake_data_home),
        }
        env.update(extra)
        return env

    def call_main(self, argv, behavior="success", **extra_env):
        env = self.env_for(behavior, **extra_env)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with mock.patch.dict(os.environ, env, clear=False):
                try:
                    code = worker_runtime.main(
                        list(argv),
                        base=self.base,
                        credential_reader=lambda: "fixture-key",
                    )
                except SystemExit as error:
                    code = error.code
        if code is None:
            code = 0
        return int(code), stdout.getvalue(), stderr.getvalue()

    def subprocess_main(self, argv, behavior="success", **extra_env):
        snippet = textwrap.dedent(
            """
            import os
            import sys
            from pathlib import Path
            import worker_runtime
            raise SystemExit(worker_runtime.main(
                sys.argv[1:],
                base=Path(os.environ["WORKER_TEST_BASE"]),
                credential_reader=lambda: "fixture-key",
            ))
            """
        )
        env = os.environ.copy()
        env.update(self.env_for(behavior, **extra_env))
        env["WORKER_TEST_BASE"] = str(self.base)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.Popen(
            [PYTHON, "-c", snippet] + list(argv),
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def invocation_rows(self):
        if not self.log.exists():
            return []
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def run_rows(self):
        return [row for row in self.invocation_rows() if row.get("kind") == "run"]

    def result_json(self, stdout):
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        self.assertTrue(lines, "runtime did not print a JSON result")
        try:
            return json.loads(lines[-1])
        except json.JSONDecodeError as error:
            self.fail("runtime stdout was not compact JSON: %r (%s)" % (stdout, error))

    def run_head(self, repo):
        return self.git(repo, "rev-parse", "HEAD").stdout.strip()

    def central_rows(self):
        db_path = self.base / "runs.sqlite3"
        if not db_path.exists():
            return []
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in connection.execute(
                "SELECT run_id, status, report_json FROM runs ORDER BY rowid"
            )]
        finally:
            connection.close()

    def report_for_row(self, row):
        raw = row["report_json"]
        try:
            report = json.loads(raw)
            if isinstance(report, dict):
                return report
        except (TypeError, json.JSONDecodeError):
            pass
        path = Path(str(raw))
        if not path.is_absolute():
            path = self.base / path
        self.assertTrue(path.exists(), "report_json did not contain JSON or a report path")
        return json.loads(path.read_text(encoding="utf-8"))

    def report_path(self, result, run_id):
        value = result.get("report") or result.get("report_path")
        self.assertIsNotNone(value, "successful result omitted report path")
        path = Path(str(value))
        if not path.is_absolute():
            path = self.base / path
        self.assertTrue(path.exists(), "report path does not exist: %s" % path)
        self.assertEqual(path, self.base / "runs" / run_id / "report.json")
        return path

    def assert_failed_record(self, before_head, repo):
        self.assertEqual(before_head, self.run_head(repo))
        rows = self.central_rows()
        self.assertTrue(rows, "failed run was not recorded")
        row = rows[-1]
        self.assertEqual(row["status"], "failed")
        report = self.report_for_row(row)
        self.assertEqual(report.get("run_id"), row["run_id"])
        return row, report

    def stats_from_report(self, report):
        stats = report.get("stats") or report.get("metrics") or report.get("statistics")
        self.assertIsInstance(stats, dict, "report lacks stats object")
        self.assertIn("tokens", stats)
        self.assertTrue(
            "timing" in stats
            or "elapsed" in stats
            or "elapsed_seconds" in stats
            or "elapsed_seconds" in report
        )
        tokens = stats["tokens"]
        if isinstance(tokens, dict):
            self.assertEqual(tokens.get("total"), 27)
        else:
            self.assertEqual(tokens, 27)
        return stats

    def test_success_commits_source_manifest_and_report_with_observed_attribution(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, stderr = self.call_main(
            [
                "--dir",
                str(repo),
                "--model",
                MODEL,
                "--title",
                "Acceptance fixture",
                "--format",
                "json",
                "update source",
            ]
        )
        self.assertEqual(code, 0, stderr)
        result = self.result_json(stdout)
        self.assertEqual(result.get("status"), "committed")
        self.assertRegex(result.get("commit", ""), r"^[0-9a-f]{40}$")
        run_id = result.get("run_id")
        self.assertTrue(run_id)
        self.assertNotEqual(result["commit"], before)
        report_path = self.report_path(result, run_id)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report.get("run_id"), run_id)
        self.assertEqual(report.get("git", {}).get("commit"), result["commit"])
        self.assertEqual(report.get("provider"), "OpenRouter")
        self.assertEqual(report.get("engine"), "OpenCode")
        self.assertEqual(report.get("requested_model"), "openrouter/" + MODEL)
        self.assertEqual(report.get("observed_models"), ["openrouter/" + MODEL])
        stats = self.stats_from_report(report)
        changes = report.get("changes")
        self.assertIsInstance(changes, dict)
        self.assertGreaterEqual(changes["insertions"], 1)
        self.assertGreaterEqual(changes["deletions"], 0)

        manifest_path = repo / ".opencode" / "runs" / (run_id + ".json")
        self.assertTrue(manifest_path.exists(), "committed manifest is missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("run_id"), run_id)
        self.assertEqual(manifest.get("git", {}).get("commit"), None)
        self.assertEqual(manifest.get("run_id"), run_id)
        tree = self.git(repo, "ls-tree", "-r", "--name-only", result["commit"]).stdout.splitlines()
        self.assertIn("src/app.txt", tree)
        self.assertIn(".opencode/runs/%s.json" % run_id, tree)

        body = self.git(repo, "show", "-s", "--format=%B", result["commit"]).stdout
        self.assertIn("OpenCode", body)
        self.assertIn("OpenRouter", body)
        self.assertIn(MODEL, body)
        self.assertEqual(self.run_head(repo), result["commit"])

        rows = self.central_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_id"], run_id)
        self.assertEqual(rows[0]["status"], "committed")

        runs = self.run_rows()
        self.assertEqual(len(runs), 1)
        self.assertIn("--format", runs[0]["argv"])
        self.assertEqual(runs[0]["format"], "json")
        self.assertEqual(runs[0]["model"], "openrouter/" + MODEL)
        self.assertEqual(runs[0]["repo"], str(repo.resolve()))

    def test_go_run_commits_correct_provider_and_verifies_without_openrouter(self):
        self.settings.update(default_provider="opencode-go", default_model="deepseek-v4.1-flash",
                             allowed_providers=["opencode-go"])
        (self.base / "settings.json").write_text(json.dumps(self.settings))
        repo = self.make_repo()
        code, stdout, stderr = self.call_main(
            ["run", "--dir", str(repo), "update source"],
            FAKE_PROVIDER="opencode-go", FAKE_MODEL="deepseek-v4.1-flash")
        self.assertEqual(code, 0, stderr)
        result = self.result_json(stdout)
        self.assertEqual(result["provider"], "OpenCode Go")
        self.assertEqual(result["model"], ["opencode-go/deepseek-v4.1-flash"])
        body = self.git(repo, "show", "-s", "--format=%B", result["commit"]).stdout
        self.assertIn("Via: OpenCode Go", body)
        self.assertIn("Provider-ID: opencode-go", body)
        self.assertIn("Billing-Source: provider_managed_unobserved", body)
        self.assertIn("Cost-Basis: OpenCode-reported estimate", body)
        self.assertNotIn("OpenRouter", body)
        self.assertEqual(worker_runtime.verify_commit(repo, "HEAD"), result["commit"])
        report = json.loads(Path(result["report"]).read_text())
        self.assertEqual(report["billing_source"], "provider_managed_unobserved")

    def test_go_only_policy_rejects_openrouter_before_model_or_credential_call(self):
        self.settings.update(default_provider="opencode-go", default_model="deepseek-v4.1-flash",
                             allowed_providers=["opencode-go"])
        (self.base / "settings.json").write_text(json.dumps(self.settings))
        repo = self.make_repo()
        code, stdout, stderr = self.call_main(
            ["run", "--dir", str(repo), "--model", "openrouter/" + MODEL, "update source"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.run_rows(), [])

    def test_json_format_is_forced_when_caller_omits_format(self):
        repo = self.make_repo()
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "update source"]
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(self.result_json(stdout).get("status"), "committed")
        runs = self.run_rows()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["format"], "json")

    def test_dirty_or_staged_preexisting_work_is_rejected_before_fake_executes(self):
        for state in ("dirty", "staged"):
            with self.subTest(state=state):
                repo = self.make_repo(state)
                before = self.run_head(repo)
                source = repo / "src" / "app.txt"
                source.write_text("preexisting change\n", encoding="utf-8")
                if state == "staged":
                    self.git(repo, "add", "src/app.txt")
                code, stdout, stderr = self.call_main(
                    ["--dir", str(repo), "--model", MODEL, "guardrail"]
                )
                self.assertNotEqual(code, 0)
                self.assertEqual(stdout, "")
                self.assertIn("clean", stderr.lower())
                self.assertEqual(before, self.run_head(repo))
                self.assertEqual(len(self.run_rows()), 0)

    def test_poisoned_git_index_cannot_hide_dirty_real_work(self):
        repo = self.make_repo()
        before_head = self.run_head(repo)
        before_index = self.git(repo, "write-tree").stdout.strip()
        source = repo / "src" / "app.txt"
        source.write_text("real dirty work\n", encoding="utf-8")
        before_content = source.read_text(encoding="utf-8")
        poisoned_index = self.base / "poisoned.index"
        poisoned_env = os.environ.copy()
        poisoned_env["GIT_INDEX_FILE"] = str(poisoned_index)
        subprocess.run(
            ["git", "-C", str(repo), "read-tree", "HEAD"],
            check=True,
            env=poisoned_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "poisoned index"],
            GIT_INDEX_FILE=str(poisoned_index),
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr.strip())
        self.assertEqual(before_head, self.run_head(repo))
        self.assertEqual(before_index, self.git(repo, "write-tree").stdout.strip())
        self.assertEqual(source.read_text(encoding="utf-8"), before_content)
        self.assertIn(" M src/app.txt", self.git(repo, "status", "--porcelain").stdout)
        self.assertEqual(self.run_rows(), [])

    def test_missing_or_malformed_telemetry_fails_without_commit(self):
        for behavior in ("missing_telemetry", "malformed_telemetry"):
            with self.subTest(behavior=behavior):
                repo = self.make_repo(behavior)
                before = self.run_head(repo)
                code, stdout, _ = self.call_main(
                    ["--dir", str(repo), "--model", MODEL, "telemetry"],
                    behavior=behavior,
                )
                self.assertNotEqual(code, 0)
                if stdout.strip():
                    failure = self.result_json(stdout)
                    self.assertNotEqual(failure.get("status"), "committed")
                row, report = self.assert_failed_record(before, repo)
                self.assertEqual(row["status"], "failed")
                self.assertEqual(report.get("status"), "failed")

    def test_missing_assistant_model_database_evidence_fails_without_commit(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, _ = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "missing model evidence"],
            behavior="missing_model",
        )
        self.assertNotEqual(code, 0)
        if stdout.strip():
            self.assertNotEqual(self.result_json(stdout).get("status"), "committed")
        row, report = self.assert_failed_record(before, repo)
        self.assertEqual(row["status"], "failed")
        self.assertEqual(report.get("model_evidence"), "unavailable")
        self.assertEqual(report.get("observed_models"), [])

    def test_mismatching_observed_model_database_evidence_fails_without_commit(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, _ = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "mismatching model evidence"],
            behavior="mismatching_model",
        )
        self.assertNotEqual(code, 0)
        if stdout.strip():
            self.assertNotEqual(self.result_json(stdout).get("status"), "committed")
        row, report = self.assert_failed_record(before, repo)
        self.assertEqual(row["status"], "failed")
        self.assertEqual(report.get("observed_models"), ["openrouter/some-other-model"])
        self.assertNotEqual(report.get("observed_models"), ["openrouter/" + MODEL])

    def test_fake_process_failure_has_no_commit_and_keeps_failure_record(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "failure"], behavior="failure"
        )
        self.assertNotEqual(code, 0)
        self.assertIn("failed", (stdout + stderr).lower())
        row, report = self.assert_failed_record(before, repo)
        self.assertEqual(report.get("status"), "failed")
        self.assertTrue(report.get("error"))
        self.assertEqual(row["run_id"], report.get("run_id"))
        self.assertEqual(len(self.run_rows()), 1, "failed worker was retried automatically")

    def test_commit_hook_rejection_propagates_and_retains_failed_report(self):
        repo = self.make_repo()
        hook = repo / ".git" / "hooks" / "pre-commit"
        hook.write_bytes(b"#!/bin/sh\necho 'fixture hook rejected commit' >&2\nexit 42\n")
        hook.chmod(0o755)
        before = self.run_head(repo)
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "hook"], behavior="commit_hook"
        )
        self.assertNotEqual(code, 0)
        self.assertTrue(stdout or stderr)
        row, report = self.assert_failed_record(before, repo)
        self.assertEqual(row["status"], "failed")
        self.assertEqual(report.get("status"), "failed")
        self.assertTrue((self.base / "runs" / row["run_id"] / "report.json").exists())

    def test_unrelated_worker_head_change_is_rejected(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "head change"],
            behavior="head_change",
        )
        self.assertNotEqual(code, 0)
        self.assertIn("head", (stdout + stderr).lower())
        self.assertNotEqual(before, self.run_head(repo))
        self.assertIn(
            "unrelated worker head change",
            self.git(repo, "show", "-s", "--format=%s", "HEAD").stdout,
        )
        rows = self.central_rows()
        self.assertTrue(rows)
        self.assertEqual(rows[-1]["status"], "failed")

    def test_no_change_is_successful_run_without_commit(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "no change"], behavior="no_change"
        )
        self.assertEqual(code, 0, stderr)
        result = self.result_json(stdout)
        self.assertEqual(result.get("status"), "no_changes")
        self.assertEqual(result.get("commit"), None)
        self.assertEqual(before, self.run_head(repo))
        rows = self.central_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_id"], result.get("run_id"))
        self.assertEqual(rows[0]["status"], "no_changes")

    def test_version_failure_does_not_create_run_record_or_api_job(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "version probe"],
            behavior="version_failure",
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr.strip())
        self.assertEqual(before, self.run_head(repo))
        # A failed audit record is allowed, but no executable OpenCode run
        # (and therefore no API job) may be created after the version probe.
        self.assertTrue(self.central_rows())
        self.assertEqual(self.central_rows()[-1]["status"], "failed")
        self.assertEqual(self.run_rows(), [])

    def test_per_repository_lock_serializes_concurrent_runs(self):
        repo = self.make_repo()
        active = self.base / "active.fake"
        overlap = self.base / "overlap.fake"
        common_dir = Path(self.git(repo, "rev-parse", "--git-common-dir").stdout.strip())
        if not common_dir.is_absolute():
            common_dir = (repo / common_dir).resolve()
        lock_path = common_dir / "opencode-worker.lock"

        first = self.subprocess_main(
            ["--dir", str(repo), "--model", MODEL, "lock one"],
            behavior="lock_probe",
            FAKE_ACTIVE=str(active),
            FAKE_OVERLAP=str(overlap),
            FAKE_SLEEP_SECONDS="0.9",
        )
        deadline = time.time() + 5
        while time.time() < deadline and not active.exists():
            time.sleep(0.02)
        self.assertTrue(active.exists(), "first fake run did not reach its critical section")
        second = self.subprocess_main(
            ["--dir", str(repo), "--model", MODEL, "lock two"],
            behavior="lock_probe",
            FAKE_ACTIVE=str(active),
            FAKE_OVERLAP=str(overlap),
            FAKE_SLEEP_SECONDS="0.2",
        )
        first_out, first_err = first.communicate(timeout=10)
        second_out, second_err = second.communicate(timeout=10)
        self.assertEqual(first.returncode, 0, first_err + first_out)
        self.assertNotEqual(second.returncode, 0, second_err + second_out)
        self.assertFalse(overlap.exists(), "two fake runs entered one repo concurrently")
        self.assertTrue(lock_path.exists(), "per-repository common-dir lock was not created")
        self.assertEqual(len(self.run_rows()), 1)

    def test_quiet_worker_heartbeats_without_extra_invocations(self):
        repo = self.make_repo()
        active = self.base / "heartbeat.active"
        process = self.subprocess_main(
            ["--dir", str(repo), "quiet worker"], behavior="lock_probe",
            FAKE_ACTIVE=str(active), FAKE_OVERLAP=str(self.base / "overlap"),
            FAKE_SLEEP_SECONDS="0.7",
        )
        observed = None
        try:
            deadline = time.monotonic() + 5
            while process.poll() is None and time.monotonic() < deadline:
                for path in (self.base / "runs").glob("*/heartbeat.json"):
                    snapshot = json.loads(path.read_text())
                    if snapshot["state"] == "running" and snapshot["heartbeat_count"] >= 2:
                        observed = snapshot
                        break
                if observed:
                    break
                time.sleep(0.02)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIsNotNone(observed, "quiet live worker had no recurring local heartbeat")
            self.assertTrue(observed["process_running"])
            self.assertEqual(observed["events_bytes"], 0)
            self.assertIsNone(observed["timeout_seconds"])
            self.assertEqual(len(stdout.strip().splitlines()), 1, "heartbeats leaked into model-visible output")
            result = self.result_json(stdout)
            final = json.loads((Path(result["report"]).parent / "heartbeat.json").read_text())
            if os.name != "nt":
                self.assertEqual((Path(result["report"]).parent / "heartbeat.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(final["state"], "exited")
            self.assertFalse(final["process_running"])
            self.assertEqual(final["exit_code"], 0)
            self.assertGreater(final["events_bytes"], 0)
            self.assertEqual(len(self.run_rows()), 1, "monitoring dispatched another worker prompt")
            self.assertEqual(result["metrics"]["tokens"]["total"], 27)
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=10)

    @unittest.skipIf(os.name == "nt", "Windows uses cancel.request; POSIX signal test")
    def test_user_interrupt_stops_unlimited_worker_and_records_final_heartbeat(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        pid_path = self.base / "interrupt.pid"
        process = self.subprocess_main(
            ["--dir", str(repo), "interrupt worker"], behavior="lock_probe",
            FAKE_ACTIVE=str(self.base / "interrupt.active"),
            FAKE_OVERLAP=str(self.base / "interrupt.overlap"),
            FAKE_PID=str(pid_path), FAKE_SLEEP_SECONDS="30",
        )
        try:
            deadline = time.monotonic() + 5
            while not pid_path.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(pid_path.exists(), "fixture did not start")
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0)
            result = self.result_json(stderr)
            self.assertEqual(result["status"], "interrupted")
            heartbeat = json.loads((Path(result["report"]).parent / "heartbeat.json").read_text())
            self.assertEqual(heartbeat["state"], "interrupted")
            self.assertFalse(heartbeat["process_running"])
            self.assertEqual(before, self.run_head(repo))
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pid_path.read_text()), 0)
            self.assertEqual(len(self.run_rows()), 1)
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=10)

    def test_timeout_kills_worker_without_commit_and_records_timed_out(self):
        repo = self.make_repo()
        before = self.run_head(repo)
        active = self.base / "timeout.active"
        pid_path = self.base / "timeout.pid"
        timeout_settings = dict(self.settings)
        timeout_settings["default_job_timeout_seconds"] = 0.2
        (self.base / "settings.json").write_text(
            json.dumps(timeout_settings, indent=2) + "\n", encoding="utf-8"
        )

        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "timeout fixture"],
            behavior="lock_probe",
            FAKE_ACTIVE=str(active),
            FAKE_OVERLAP=str(self.base / "timeout.overlap"),
            FAKE_PID=str(pid_path),
            FAKE_SLEEP_SECONDS="5",
        )
        self.assertNotEqual(code, 0)
        payload = self.result_json(stderr if stderr.strip() else stdout)
        self.assertEqual(payload.get("status"), "timed_out")
        self.assertEqual(before, self.run_head(repo))
        rows = self.central_rows()
        self.assertTrue(rows)
        self.assertEqual(rows[-1]["status"], "timed_out")
        report = self.report_for_row(rows[-1])
        self.assertEqual(report.get("status"), "timed_out")
        heartbeat = json.loads((self.base / "runs" / rows[-1]["run_id"] / "heartbeat.json").read_text())
        self.assertEqual(heartbeat["state"], "timed_out")
        self.assertFalse(heartbeat["process_running"])
        self.assertEqual(len(self.run_rows()), 1)

        self.assertTrue(pid_path.exists(), "timeout fixture never started")
        worker_pid = int(pid_path.read_text(encoding="utf-8"))
        deadline = time.time() + 2
        while time.time() < deadline:
            if os.name == "nt":
                listed = subprocess.run(
                    ["tasklist", "/FI", "PID eq " + str(worker_pid), "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, check=True,
                )
                if not any(len(row) > 1 and row[1] == str(worker_pid)
                           for row in csv.reader(io.StringIO(listed.stdout))):
                    break
                time.sleep(0.02)
                continue
            try:
                os.kill(worker_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            self.fail("timed-out fake OpenCode process was not cleaned up")

    def test_stats_csv_includes_attribution_run_and_usage_columns(self):
        repo = self.make_repo()
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "stats fixture"]
        )
        self.assertEqual(code, 0, stderr)
        result = self.result_json(stdout)
        stats_out = io.StringIO()
        stats_err = io.StringIO()
        with contextlib.redirect_stdout(stats_out), contextlib.redirect_stderr(stats_err):
            code = worker_runtime.main(
                ["stats", "--format", "csv"],
                base=self.base,
                credential_reader=lambda: "fixture-key",
            )
        self.assertEqual(code, 0, stats_err.getvalue())
        rows = list(csv.DictReader(io.StringIO(stats_out.getvalue())))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        for column in (
            "provider",
            "engine",
            "requested_model",
            "run_id",
            "commit",
            "tokens_total",
            "elapsed_seconds",
            "estimated_cost_usd",
            "status",
        ):
            self.assertIn(column, row)
        self.assertEqual(row["provider"], "OpenRouter")
        self.assertEqual(row["provider_id"], "openrouter")
        self.assertEqual(row["billing_source"], "provider_managed_unobserved")
        self.assertIn("OpenCode-reported estimate", row["cost_basis"])
        self.assertEqual(row["engine"], "OpenCode")
        self.assertEqual(row["requested_model"], "openrouter/" + MODEL)
        self.assertEqual(row["run_id"], result["run_id"])
        self.assertEqual(row["commit"], result["commit"])
        self.assertEqual(int(float(row["tokens_total"])), 27)
        self.assertGreaterEqual(float(row["elapsed_seconds"]), 0.0)
        self.assertGreaterEqual(float(row["estimated_cost_usd"]), 0.0)
        self.assertEqual(row["status"], "committed")

    def test_verify_accepts_valid_commit_and_rejects_tampered_manifest(self):
        repo = self.make_repo()
        code, stdout, stderr = self.call_main(
            ["--dir", str(repo), "--model", MODEL, "verify fixture"]
        )
        self.assertEqual(code, 0, stderr)
        result = self.result_json(stdout)
        verify_out = io.StringIO()
        verify_err = io.StringIO()
        with contextlib.redirect_stdout(verify_out), contextlib.redirect_stderr(verify_err):
            code = worker_runtime.main(
                ["verify", "--dir", str(repo), "--commit", "HEAD"],
                base=self.base,
                credential_reader=lambda: "fixture-key",
            )
        self.assertEqual(code, 0, verify_err.getvalue() + verify_out.getvalue())

        manifest_path = repo / ".opencode" / "runs" / (result["run_id"] + ".json")
        original = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(original)
        manifest["report_sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
        self.git(repo, "add", ".opencode/runs/%s.json" % result["run_id"])
        self.git(repo, "commit", "--amend", "--no-edit")
        verify_out = io.StringIO()
        verify_err = io.StringIO()
        with contextlib.redirect_stdout(verify_out), contextlib.redirect_stderr(verify_err):
            code = worker_runtime.main(
                ["verify", "--dir", str(repo), "--commit", "HEAD"],
                base=self.base,
                credential_reader=lambda: "fixture-key",
            )
        self.assertNotEqual(code, 0)
        self.assertTrue(verify_err.getvalue() or verify_out.getvalue())

    def test_verify_rejects_missing_current_accounting_even_with_recomputed_digest(self):
        repo = self.make_repo()
        code, stdout, stderr = self.call_main(["--dir", str(repo), "--model", MODEL, "accounting fixture"])
        self.assertEqual(code, 0, stderr)
        result = self.result_json(stdout)
        relative = ".opencode/runs/" + result["run_id"] + ".json"
        path = repo / relative
        original = path.read_bytes()
        body = self.git(repo, "show", "-s", "--format=%B", "HEAD").stdout
        original_digest = hashlib.sha256(original).hexdigest()
        for field in ("provider_id", "billing_source", "cost_basis"):
            with self.subTest(field=field):
                report = json.loads(original)
                report.pop(field)
                path.write_bytes((json.dumps(report) + "\n").encode("utf-8"))
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.git(repo, "add", relative)
                self.git(repo, "commit", "--amend", "-m", body.replace(original_digest, digest))
                with self.assertRaisesRegex(worker_runtime.GuardrailError, field):
                    worker_runtime.verify_commit(repo, "HEAD")

        # Version 3 commits did not require the new provenance fields.
        report = json.loads(original)
        report["launcher_version"] = "3.0.0"
        for field in ("provider_id", "billing_source", "cost_basis"):
            report.pop(field)
        path.write_bytes((json.dumps(report) + "\n").encode("utf-8"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        message = worker_runtime.commit_message(report, relative, digest, "legacy fixture")
        self.git(repo, "add", relative)
        self.git(repo, "commit", "--amend", "-m", message)
        self.assertEqual(worker_runtime.verify_commit(repo, "HEAD"), self.run_head(repo))


if __name__ == "__main__":
    unittest.main()
