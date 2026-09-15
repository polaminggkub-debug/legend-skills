"""Acceptance coverage for the repository-local workflow contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SCRIPTS = ROOT / "scripts"
for path in (TESTS, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

class WorkerWorkflowTests(unittest.TestCase):
    """Compose the runtime fixture without inheriting its test methods."""

    def setUp(self):
        # Import the fixture locally so unittest discovery does not mistake
        # the composed fixture class for another set of tests in this module.
        from test_worker_runtime import WorkerRuntimeAcceptanceTests

        self.runtime = WorkerRuntimeAcceptanceTests("runTest")
        self.runtime.setUp()
        self.addCleanup(self.runtime.tearDown)

    def _write_contract(self, repo: Path, contract, *, commit: bool = True) -> Path:
        path = repo / ".opencode" / "worker.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        if commit:
            self.runtime.git(repo, "add", ".opencode/worker.json")
            self.runtime.git(repo, "commit", "-qm", "declare worker workflow")
        return path

    @staticmethod
    def _check(step_id: str, code: str, *, stage: str = "before_commit"):
        return {
            "id": step_id,
            "kind": "test",
            "stage": stage,
            "argv": ["{python}", "-c", code],
        }

    @staticmethod
    def _metadata(step_id: str, code: str):
        return {"id": step_id, "argv": ["{python}", "-c", code]}

    def test_invalid_contract_and_missing_executable_fail_before_fake_worker(self):
        invalid_repo = self.runtime.make_repo("invalid-contract")
        self._write_contract(invalid_repo, {"schema_version": 1, "unexpected": True})
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(invalid_repo), "--model", "deepseek/deepseek-v4.1-flash", "invalid contract"]
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(self.runtime.run_rows(), [])
        self.assertNotIn('"kind": "run"', self.runtime.log.read_text(encoding="utf-8") if self.runtime.log.exists() else "")
        self.assertTrue(stderr)

        missing_repo = self.runtime.make_repo("missing-executable")
        self._write_contract(
            missing_repo,
            {
                "schema_version": 1,
                "write_paths": ["src/**"],
                "checks": [self._check("missing", "pass") | {"argv": ["worker-command-does-not-exist-xyz"]}],
            },
        )
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(missing_repo), "--model", "deepseek/deepseek-v4.1-flash", "missing executable"]
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(self.runtime.run_rows(), [])
        self.assertTrue(stderr)

    def test_before_commit_check_failure_prevents_source_commit(self):
        repo = self.runtime.make_repo("before-check-failure")
        self._write_contract(
            repo,
            {
                "schema_version": 1,
                "write_paths": ["src/**"],
                "checks": [self._check("before", "import sys; sys.exit(17)")],
            },
        )
        before = self.runtime.run_head(repo)
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(repo), "--model", "deepseek/deepseek-v4.1-flash", "before check"],
        )
        self.assertNotEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(self.runtime.run_head(repo), before)
        rows = self.runtime.central_rows()
        self.assertEqual(len(rows), 1)
        report = self.runtime.report_for_row(rows[0])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["git"]["commit"], None)
        self.assertEqual(report["checks"]["status"], "failed")
        self.assertEqual(report["checks"]["results"][0]["argv"][0], sys.executable)

    def test_after_commit_check_failure_keeps_attributed_source_commit(self):
        repo = self.runtime.make_repo("after-check-failure")
        self._write_contract(
            repo,
            {
                "schema_version": 1,
                "write_paths": ["src/**"],
                "checks": [self._check("after", "import sys; sys.exit(23)", stage="after_commit")],
            },
        )
        before = self.runtime.run_head(repo)
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(repo), "--model", "deepseek/deepseek-v4.1-flash", "after check"],
        )
        self.assertNotEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        after = self.runtime.run_head(repo)
        self.assertNotEqual(after, before)
        rows = self.runtime.central_rows()
        self.assertEqual(len(rows), 1)
        report = self.runtime.report_for_row(rows[0])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["git"]["commit"], after)
        self.assertEqual(report["checks"]["status"], "failed")
        self.assertEqual(report["checks"]["results"][0]["argv"][0], sys.executable)
        body = self.runtime.git(repo, "show", "-s", "--format=%B", after).stdout
        self.assertIn("OpenCode", body)
        self.assertIn("OpenRouter", body)

    def test_handoff_metadata_commits_after_source_and_after_check_verifies_it(self):
        repo = self.runtime.make_repo("metadata-handoff")
        write_code = (
            "import json, os; from pathlib import Path; "
            "p=Path('docs/metadata.json'); p.parent.mkdir(parents=True, exist_ok=True); "
            "p.write_text(json.dumps({'source_commit': os.environ['WORKER_SOURCE_COMMIT']}, sort_keys=True)+'\\n')"
        )
        verify_code = (
            "import json, subprocess; from pathlib import Path; "
            "p=Path('docs/metadata.json'); d=json.loads(p.read_text()); source=d['source_commit']; "
            "assert subprocess.run(['git','merge-base','--is-ancestor',source,'HEAD']).returncode == 0; "
            "assert p.read_bytes() == subprocess.check_output(['git','show','HEAD:docs/metadata.json'])"
        )
        self._write_contract(
            repo,
            {
                "schema_version": 1,
                "write_paths": ["src/**"],
                "checks": [self._check("after", "pass", stage="after_commit")],
                "handoff": {
                    "write_paths": ["docs/**"],
                    "metadata": [self._metadata("receipt", write_code)],
                },
            },
        )
        before = self.runtime.run_head(repo)
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(repo), "--model", "deepseek/deepseek-v4.1-flash", "metadata handoff"],
        )
        self.assertEqual(code, 0, stderr)
        result = self.runtime.result_json(stdout)
        self.assertEqual(result["status"], "committed")
        self.assertEqual(len(self.runtime.run_rows()), 1)
        run_id = result["run_id"]
        report = json.loads(self.runtime.report_path(result, run_id).read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "committed")
        source_commit = report["delivery"]["source_commit"]
        metadata_commit = report["delivery"]["metadata_commit"]
        self.assertNotEqual(source_commit, before)
        self.assertNotEqual(metadata_commit, source_commit)
        self.assertEqual(self.runtime.git(repo, "show", "-s", "--format=%P", source_commit).stdout.strip(), before)
        self.assertEqual(
            self.runtime.git(repo, "show", "-s", "--format=%P", metadata_commit).stdout.strip(),
            source_commit,
        )
        self.assertEqual(report["delivery"]["results"][0]["argv"][0], sys.executable)
        metadata_path = ".opencode/runs/%s-metadata.json" % run_id
        metadata = json.loads(self.runtime.git(repo, "show", metadata_commit + ":" + metadata_path).stdout)
        self.assertEqual(metadata["source_commit"], source_commit)
        docs_bytes = self.runtime.git(repo, "show", metadata_commit + ":docs/metadata.json").stdout.encode()
        self.assertEqual(docs_bytes, self.runtime.git(repo, "show", "HEAD:docs/metadata.json").stdout.encode())
        self.assertEqual(
            self.runtime.call_main(["verify", "--dir", str(repo), "--commit", "HEAD"])[0],
            0,
        )
        self.assertEqual(len(self.runtime.run_rows()), 1)

    def test_contract_tamper_and_metadata_out_of_scope_mutation_fail(self):
        tamper_repo = self.runtime.make_repo("contract-tamper")
        tamper_code = "from pathlib import Path; p=Path('.opencode/worker.json'); p.write_text(p.read_text()+'\\n')"
        self._write_contract(
            tamper_repo,
            {
                "schema_version": 1,
                "write_paths": ["src/**"],
                "checks": [self._check("tamper", tamper_code)],
            },
        )
        before = self.runtime.run_head(tamper_repo)
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(tamper_repo), "--model", "deepseek/deepseek-v4.1-flash", "tamper contract"]
        )
        self.assertNotEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(self.runtime.run_head(tamper_repo), before)
        report = self.runtime.report_for_row(self.runtime.central_rows()[-1])
        self.assertEqual(report["status"], "failed")

        outscope_repo = self.runtime.make_repo("metadata-outscope")
        outscope_code = "from pathlib import Path; Path('outside.txt').write_text('out of scope\\n')"
        self._write_contract(
            outscope_repo,
            {
                "schema_version": 1,
                "write_paths": ["src/**"],
                "handoff": {
                    "write_paths": ["docs/**"],
                    "metadata": [self._metadata("outscope", outscope_code)],
                },
            },
        )
        before = self.runtime.run_head(outscope_repo)
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(outscope_repo), "--model", "deepseek/deepseek-v4.1-flash", "metadata outscope"]
        )
        self.assertNotEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertNotEqual(self.runtime.run_head(outscope_repo), before)
        report = self.runtime.report_for_row(self.runtime.central_rows()[-1])
        self.assertEqual(report["status"], "failed")
        self.assertIsNone(report["delivery"].get("metadata_commit"))

    def test_cancel_request_cli_interrupts_live_worker_without_commit(self):
        """The local cancel command is the portable cancellation interface."""
        repo = self.runtime.make_repo("cancel-request")
        before = self.runtime.run_head(repo)
        pid_path = self.runtime.base / "cancel.pid"
        process = self.runtime.subprocess_main(
            ["--dir", str(repo), "cancel worker"],
            behavior="lock_probe",
            FAKE_ACTIVE=str(self.runtime.base / "cancel.active"),
            FAKE_OVERLAP=str(self.runtime.base / "cancel.overlap"),
            FAKE_PID=str(pid_path),
            FAKE_SLEEP_SECONDS="30",
        )
        try:
            deadline = time.monotonic() + 5
            while (
                not pid_path.exists()
                and process.poll() is None
                and time.monotonic() < deadline
            ):
                time.sleep(0.02)
            self.assertTrue(pid_path.exists(), "fixture did not start")

            run_dir = None
            deadline = time.monotonic() + 5
            while process.poll() is None and time.monotonic() < deadline:
                candidates = sorted((self.runtime.base / "runs").glob("*/report.json"))
                for report_path in candidates:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    if report.get("status") == "running":
                        run_dir = report_path.parent
                        break
                if run_dir is not None:
                    break
                time.sleep(0.02)
            self.assertIsNotNone(run_dir, "live run report was not persisted")
            run_id = run_dir.name

            code, stdout, stderr = self.runtime.call_main(["cancel", "--run", run_id])
            self.assertEqual(code, 0, stderr)
            cancellation = self.runtime.result_json(stdout)
            self.assertEqual(cancellation, {"status": "cancellation_requested", "run_id": run_id})
            self.assertTrue((run_dir / "cancel.request").is_file())

            stdout, stderr = process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0)
            result = self.runtime.result_json(stderr if stderr.strip() else stdout)
            self.assertEqual(result["status"], "interrupted")
            final_report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(final_report["status"], "interrupted")
            heartbeat = json.loads((run_dir / "heartbeat.json").read_text(encoding="utf-8"))
            self.assertEqual(heartbeat["state"], "interrupted")
            self.assertFalse(heartbeat["process_running"])
            self.assertEqual(before, self.runtime.run_head(repo))
            self.assertEqual(len(self.runtime.run_rows()), 1)
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=10)

    def test_non_ascii_thai_project_path_title_and_prompt_survive_delegation(self):
        repo = self.runtime.make_repo("โปรเจกต์ภาษาไทย")
        title = "แก้ข้อความภาษาไทย รอบเดียว"
        prompt = "ช่วยแก้ข้อความในโปรเจกต์ของฉัน"
        code, stdout, stderr = self.runtime.call_main(
            ["--dir", str(repo), "--model", "deepseek/deepseek-v4.1-flash",
             "--title", title, prompt],
        )
        self.assertEqual(code, 0, stderr)
        result = self.runtime.result_json(stdout)
        self.assertEqual(result["status"], "committed")
        rows = self.runtime.run_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["repo"], str(repo.resolve()))
        self.assertEqual(rows[0]["title"], title)
        self.assertEqual(rows[0]["argv"][rows[0]["argv"].index("--title") + 1], title)
        report = json.loads(Path(result["report"]).read_text(encoding="utf-8"))
        self.assertEqual(report["git"]["parent_repo"], str(repo.resolve()))


if __name__ == "__main__":
    unittest.main()
