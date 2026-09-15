"""Offline tests for project discovery and the worker contract boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import worker_project  # noqa: E402


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _write_contract(repo: Path, value) -> Path:
    path = repo / ".opencode" / "worker.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        _write_json(path, value)
    return path


class WorkerProjectTests(unittest.TestCase):
    def test_discovery_is_bounded_informational_and_handles_multiple_projects(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            _write_json(
                repo / "package.json",
                {
                    "workspaces": ["packages/*"],
                    "scripts": {"build": "echo build", "test": "echo test"},
                },
            )
            _write_json(repo / "packages" / "web" / "package.json", {"scripts": {"lint": "echo lint"}})
            _write_json(repo / "node_modules" / "ignored" / "package.json", {"scripts": {"test": "bad"}})
            _write_json(repo / ".git" / "ignored" / "package.json", {"scripts": {"test": "bad"}})
            (repo / "pyproject.toml").write_text(
                "[tool.pytest.ini_options]\naddopts = '-q'\n\n[tool.ruff]\nline-length = 88\n",
                encoding="utf-8",
            )
            (repo / "Makefile").write_text("test:\n\techo test\nbuild: test\n\techo build\n", encoding="utf-8")
            (repo / ".github" / "workflows" / "ci.yml").parent.mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("instructions\n", encoding="utf-8")
            (repo / "CLAUDE.md").write_text("instructions\n", encoding="utf-8")

            with mock.patch.object(worker_project.worker_platform.subprocess, "run", side_effect=AssertionError("must not execute")):
                inspected = worker_project.inspect_project(repo)
                with self.assertRaises(worker_project.ProjectError):
                    worker_project.load_project(repo)

            package_candidates = [
                item for item in inspected["candidates"] if item["source"] == "package.json"
            ]
            self.assertEqual(
                {(item["path"], item["name"]) for item in package_candidates},
                {("package.json", "build"), ("package.json", "test"), ("packages/web/package.json", "lint")},
            )
            self.assertFalse(any("node_modules" in item["path"] for item in inspected["candidates"]))
            self.assertFalse(any(".git/" in item["path"] for item in inspected["candidates"]))
            self.assertEqual(inspected["presence"]["agents"], ["AGENTS.md"])
            self.assertEqual(inspected["presence"]["claude"], ["CLAUDE.md"])
            self.assertEqual(inspected["presence"]["ci"], [".github/workflows/ci.yml"])

            plain_repo = repo / "plain"
            plain_repo.mkdir()
            plain_plan = worker_project.load_project(plain_repo)
            self.assertEqual(plain_plan["source"], "discovery")
            self.assertIsNone(plain_plan["contract_sha256"])
            self.assertEqual(plain_plan["write_paths"], ["**"])
            self.assertEqual(plain_plan["checks"], [])
            self.assertIsNone(plain_plan["handoff"])
            self.assertNotIn("passed", json.dumps(plain_plan).lower())

    def test_valid_contract_normalises_defaults_hashes_and_preflights_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            contract = _write_contract(
                repo,
                {
                    "schema_version": 1,
                    "write_paths": ["src/**", "README.md"],
                    "checks": [
                        {"id": "unit", "kind": "test", "argv": ["{python}", "-m", "unittest"]},
                        {"id": "style", "kind": "lint", "argv": ["echo", "lint"], "required": False, "timeout_seconds": 3},
                    ],
                    "handoff": {
                        "write_paths": ["docs/**"],
                        "metadata": [{"id": "receipt", "argv": ["{python}", "-c", "pass"]}],
                    },
                },
            )
            expected_hash = hashlib.sha256(contract.read_bytes()).hexdigest()
            with mock.patch.object(worker_project.worker_platform.subprocess, "run", side_effect=AssertionError("must not execute")):
                plan = worker_project.load_project(repo)

            self.assertEqual(plan["source"], "contract")
            self.assertEqual(plan["contract_sha256"], expected_hash)
            self.assertEqual(plan["write_paths"], ["src/**", "README.md"])
            self.assertEqual(plan["checks"][0]["cwd"], ".")
            self.assertEqual(plan["checks"][0]["stage"], "before_commit")
            self.assertTrue(plan["checks"][0]["required"])
            self.assertIsNone(plan["checks"][0]["timeout_seconds"])
            self.assertEqual(plan["checks"][1]["required"], False)
            self.assertEqual(plan["handoff"]["write_paths"], ["docs/**"])
            self.assertNotIn("kind", plan["handoff"]["metadata"][0])
            self.assertNotIn("stage", plan["handoff"]["metadata"][0])
            self.assertEqual(worker_project.command_argv(plan["checks"][0], repo)[0], sys.executable)
            self.assertEqual(
                worker_project.metadata_environment(repo, "abc123", "run-1"),
                {
                    "WORKER_REPO_ROOT": str(repo.resolve()),
                    "WORKER_SOURCE_COMMIT": "abc123",
                    "WORKER_RUN_ID": "run-1",
                },
            )

    def test_contract_rejects_unknown_duplicate_invalid_and_secret_fields(self):
        invalid_contracts = [
            {"schema_version": 1, "unexpected": True},
            {
                "schema_version": 1,
                "checks": [
                    {"id": "same", "kind": "test", "argv": ["{python}"]},
                    {"id": "same", "kind": "lint", "argv": ["{python}"]},
                ],
            },
            {"schema_version": 1, "write_paths": ["../outside"]},
            {
                "schema_version": 1,
                "checks": [{"id": "secret", "kind": "check", "argv": ["echo", "api_key=literal-secret-value-1234"]}],
            },
            {"schema_version": 1, "checks": [{"id": "shell", "kind": "check", "argv": ["sh", "-c", "echo unsafe"]}]},
            {"schema_version": 1, "checks": [{"id": "powershell", "kind": "check", "argv": ["pwsh", "-Command", "Write-Output unsafe"]}]},
            {"schema_version": 1, "handoff": {"metadata": []}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for value in invalid_contracts:
                with self.subTest(value=value):
                    _write_contract(repo, value)
                    with self.assertRaises(worker_project.ProjectError):
                        worker_project.load_project(repo)

            _write_contract(repo, '{"schema_version": 1, "checks": [], "timeout": NaN}\n')
            with self.assertRaises(worker_project.ProjectError):
                worker_project.load_project(repo)

    def test_missing_explicit_executable_fails_before_any_process_call(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            _write_contract(
                repo,
                {
                    "schema_version": 1,
                    "checks": [{"id": "missing", "kind": "check", "argv": ["worker-command-does-not-exist-xyz"]}],
                },
            )
            with mock.patch.object(worker_project.worker_platform.subprocess, "run", side_effect=AssertionError("must not execute")):
                with self.assertRaises(worker_project.ProjectError):
                    worker_project.load_project(repo)

    def test_scope_matching_and_contract_tampering_include_appearance_and_disappearance(self):
        self.assertTrue(worker_project.path_allowed("README.md", ["**"]))
        self.assertTrue(worker_project.path_allowed("src/app/main.py", ["**/*.py"]))
        self.assertTrue(worker_project.path_allowed("main.py", ["**/*.py"]))
        self.assertTrue(worker_project.path_allowed("src/app.py", ["src/**"]))
        self.assertFalse(worker_project.path_allowed("docs/readme.md", ["src/**"]))
        self.assertFalse(worker_project.path_allowed("../outside", ["**"]))
        self.assertFalse(worker_project.path_allowed("/absolute/path", ["**"]))

        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            contract = _write_contract(repo, {"schema_version": 1, "checks": []})
            plan = worker_project.load_project(repo)
            self.assertTrue(worker_project.assert_unchanged(repo, plan))

            contract.write_text('{"schema_version": 1, "checks": [], "write_paths": ["src/**"]}\n', encoding="utf-8")
            with self.assertRaises(worker_project.ProjectError):
                worker_project.assert_unchanged(repo, plan)
            contract.unlink()
            with self.assertRaises(worker_project.ProjectError):
                worker_project.assert_unchanged(repo, plan)

            discovery_plan = worker_project.load_project(repo)
            _write_contract(repo, {"schema_version": 1, "checks": []})
            with self.assertRaises(worker_project.ProjectError):
                worker_project.assert_unchanged(repo, discovery_plan)

    def test_contract_rejects_write_scope_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside_directory:
            repo = Path(directory)
            outside = Path(outside_directory)
            link = repo / "linked"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            _write_contract(repo, {"schema_version": 1, "write_paths": ["linked/**"], "checks": []})
            with self.assertRaises(worker_project.ProjectError):
                worker_project.load_project(repo)


if __name__ == "__main__":
    unittest.main()
