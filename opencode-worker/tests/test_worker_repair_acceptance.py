"""Provider-free acceptance of repair cycles through real Git and subprocesses."""
import json
import csv
import io
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))


class BoundedRepairAcceptanceTests(unittest.TestCase):
    def setUp(self):
        from test_worker_runtime import WorkerRuntimeAcceptanceTests, FAKE_OPENCODE
        self.runtime = WorkerRuntimeAcceptanceTests('runTest')
        self.runtime.setUp()
        self.addCleanup(self.runtime.tearDown)
        original = 'source.write_text("worker output\\n", encoding="utf-8")'
        replacement = '''sequence = json.loads(os.environ.get("FAKE_REPAIR_CONTENTS", '["bad", "good"]'))
        count = sum(json.loads(line).get("kind") == "run" for line in Path(os.environ["FAKE_LOG"]).read_text().splitlines())
        source.write_text(sequence[min(count - 1, len(sequence) - 1)] + "\\n", encoding="utf-8")
        if source.read_text().strip() == "crash":
            return 17'''
        self.assertIn(original, FAKE_OPENCODE)
        self.runtime.fake.write_text(FAKE_OPENCODE.replace(original, replacement), encoding='utf-8')
        self.repo = self.runtime.make_repo()

    def contract(self, stage='before_commit', metadata=False, check_code=None, checks=True):
        check_code = check_code or (
            "from pathlib import Path; import sys; "
            "good=Path('src/app.txt').read_text().strip()=='good'; "
            "print('EXPECTED_GOOD_SOURCE' if not good else 'PASS'); sys.exit(0 if good else 1)"
        )
        plan = {'schema_version': 1, 'write_paths': ['src/**'], 'checks': []}
        if checks:
            plan['checks'] = [{'id': 'build', 'kind': 'build', 'stage': stage,
                               'argv': ['{python}', '-c', check_code]}]
        if metadata:
            plan['handoff'] = {
                'write_paths': ['docs/**'],
                'metadata': [{'id': 'receipt', 'argv': ['{python}', '-c',
                    "from pathlib import Path; import os; "
                    "Path('docs').mkdir(exist_ok=True); "
                    "Path('docs/source.txt').write_text(os.environ['WORKER_SOURCE_COMMIT'])"]}],
            }
        path = self.repo / '.opencode' / 'worker.json'
        path.parent.mkdir()
        path.write_bytes((json.dumps(plan) + '\n').encode())
        self.runtime.git(self.repo, 'add', '.opencode/worker.json')
        self.runtime.git(self.repo, 'commit', '-qm', 'declare checks')
        self.base_commit = self.runtime.run_head(self.repo)

    def run_worker(self, sequence=('bad', 'good'), flags=()):
        code, out, err = self.runtime.call_main(
            ['run', '--dir', str(self.repo), *flags, 'Implement the requested source change'],
            FAKE_REPAIR_CONTENTS=json.dumps(sequence))
        rows = self.runtime.central_rows()
        self.assertEqual(len(rows), 1, err)
        return code, out, err, json.loads(rows[0]['report_json'])

    def assert_verified(self, commits):
        for commit in commits:
            code, _, err = self.runtime.call_main(['verify', '--dir', str(self.repo), '--commit', commit])
            self.assertEqual(code, 0, err)

    def test_before_commit_repair_passes_and_accounts_both_invocations_once(self):
        self.contract()
        code, _, err, report = self.run_worker()
        self.assertEqual(code, 0, err)
        self.assertEqual(report['checks']['status'], 'passed')
        self.assertEqual(report['metrics']['tokens']['total'], 54)
        self.assertEqual(report['metrics']['model_steps'], 2)
        self.assertEqual(report['timing']['events']['model_steps'], 2)
        self.assertEqual(len(self.runtime.run_rows()), 2)
        self.assertIn('EXPECTED_GOOD_SOURCE', self.runtime.run_rows()[1]['argv'][-1])
        commits = self.runtime.git(self.repo, 'rev-list', self.base_commit + '..HEAD').stdout.split()
        self.assertEqual(len(commits), 1)
        self.assert_verified(commits)
        self.assertEqual(self.runtime.git(self.repo, 'status', '--porcelain').stdout, '')
        export_code, output, error = self.runtime.call_main(['stats', '--format', 'csv'])
        self.assertEqual(export_code, 0, error)
        row = next(csv.DictReader(io.StringIO(output)))
        self.assertEqual(row['repair_attempts'], '1')
        self.assertEqual(row['max_model_steps'], '100')
        self.assertEqual(row['max_wall_seconds'], '3600')

    def test_after_commit_repair_preserves_history_and_refreshes_metadata(self):
        self.contract(stage='after_commit', metadata=True)
        code, _, err, report = self.run_worker()
        self.assertEqual(code, 0, err)
        self.assertEqual(report['checks']['status'], 'passed')
        self.assertEqual(report['metrics']['tokens']['total'], 54)
        commits = self.runtime.git(self.repo, 'rev-list', '--reverse', self.base_commit + '..HEAD').stdout.split()
        self.assertEqual(len(commits), 4)
        self.assert_verified(commits)
        path = '.opencode/runs/' + report['run_id'] + '.json'
        for commit in commits[::2]:
            record = json.loads(self.runtime.git(self.repo, 'show', commit + ':' + path).stdout)
            self.assertEqual(record['metrics']['tokens']['total'], 27)
            self.assertIsNone(record['git']['source_commit'])
            self.assertNotIn('delivery', record)
        self.assertEqual((self.repo / 'docs/source.txt').read_text(), commits[2])

    def test_two_repairs_share_one_budget_and_exhaust_without_rolling_back(self):
        self.contract()
        code, _, _, report = self.run_worker(('bad-1', 'bad-2', 'bad-3', 'good'))
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.runtime.run_rows()), 3)
        self.assertEqual(report['repairs']['attempts'], 2)
        self.assertEqual(report['metrics']['tokens']['total'], 81)
        self.assertEqual(self.runtime.run_head(self.repo), self.base_commit)
        self.assertEqual((self.repo / 'src/app.txt').read_text().strip(), 'bad-3')
        self.assertIn('max_repair', json.dumps(report['repairs']))

    def test_unchanged_failed_repair_stops_before_second_repair(self):
        self.contract()
        code, _, _, report = self.run_worker(('bad', 'bad', 'good'))
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.runtime.run_rows()), 2)
        self.assertEqual(report['repairs']['stop_reason'], 'no_progress')

    def test_zero_repairs_still_runs_initial_attempt(self):
        self.contract()
        code, _, _, report = self.run_worker(flags=('--max-repairs', '0'))
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.runtime.run_rows()), 1)
        self.assertEqual(report['repairs']['attempts'], 0)

    def test_step_cap_is_shared_and_stops_another_invocation(self):
        self.contract()
        code, _, _, report = self.run_worker(flags=('--max-model-steps', '1'))
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.runtime.run_rows()), 1)
        self.assertEqual(report['budget']['stop_reason'], 'max_model_steps')

    def test_success_on_last_allowed_step_can_finish_checks_and_commit(self):
        self.contract()
        code, _, err, report = self.run_worker(('good',), flags=('--max-model-steps', '1'))
        self.assertEqual(code, 0, err)
        self.assertEqual(report['checks']['status'], 'passed')
        self.assert_verified([self.runtime.run_head(self.repo)])

    def test_empty_checks_do_not_invent_build_or_repair(self):
        self.contract(checks=False)
        code, _, err, report = self.run_worker(('bad',))
        self.assertEqual(code, 0, err)
        self.assertEqual(report['checks']['status'], 'not_declared')
        self.assertEqual(len(self.runtime.run_rows()), 1)

    def test_failing_check_that_changes_source_is_not_sent_for_repair(self):
        self.contract(check_code="from pathlib import Path; import sys; Path('src/app.txt').write_text('changed by check'); sys.exit(1)")
        code, _, _, report = self.run_worker()
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.runtime.run_rows()), 1)
        self.assertTrue(report['finalized'])

    def test_whole_job_deadline_interrupts_running_check_without_repair(self):
        self.contract(check_code="import time; time.sleep(30)")
        started = time.monotonic()
        code, _, _, report = self.run_worker(flags=('--max-job-seconds', '2'))
        self.assertNotEqual(code, 0)
        self.assertLess(time.monotonic() - started, 8)
        self.assertEqual(len(self.runtime.run_rows()), 1)
        self.assertEqual(report['repairs']['attempts'], 0)
        self.assertEqual(report['budget']['stop_reason'], 'max_wall_seconds')

    def test_failed_repair_without_telemetry_does_not_claim_complete_job_usage(self):
        self.contract()
        code, _, _, report = self.run_worker(('bad', 'crash'))
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.runtime.run_rows()), 2)
        self.assertEqual(report['metrics']['tokens']['total'], 27)
        self.assertFalse(report['metrics']['completed'])
        self.assertEqual(report['metrics']['accounting_scope'], 'partial_completed_steps')


if __name__ == '__main__':
    unittest.main()
