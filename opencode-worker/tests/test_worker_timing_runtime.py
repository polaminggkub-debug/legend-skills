"""Persisted timing evidence across model, checks, commits, and failures."""
import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import worker_runtime
import worker_job


class RuntimeTimingTests(unittest.TestCase):
    def setUp(self):
        from test_worker_runtime import WorkerRuntimeAcceptanceTests
        self.fixture = WorkerRuntimeAcceptanceTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def test_final_report_and_csv_distinguish_model_checks_and_commit(self):
        repo = self.fixture.make_repo()
        contract = repo / '.opencode' / 'worker.json'
        contract.parent.mkdir()
        contract.write_text(json.dumps({'schema_version': 1, 'write_paths': ['src/**'],
            'checks': [{'id': stage, 'kind': 'test', 'stage': stage,
                        'argv': ['{python}', '-c', 'import time; time.sleep(0.06)']}
                       for stage in ('before_commit', 'after_commit')]}), encoding='utf-8')
        self.fixture.git(repo, 'add', '.opencode/worker.json')
        self.fixture.git(repo, 'commit', '-qm', 'declare timed checks')
        code, output, errors = self.fixture.call_main(
            ['run', '--dir', str(repo), 'change source'],
            behavior='sleep_then_success', FAKE_SLEEP_SECONDS='0.08')
        self.assertEqual(code, 0, errors)
        result = json.loads(output)
        report = json.loads(Path(result['report']).read_text(encoding='utf-8'))
        timing = report['timing']
        self.assertEqual(result['timing'], timing)
        self.assertIsNone(timing['active_phase'])
        phases = timing['phases_seconds']
        self.assertGreaterEqual(phases['model'], 0.08)
        for phase in ('before_commit', 'after_commit'):
            self.assertGreaterEqual(phases[phase], 0.06)
        self.assertGreater(phases['commit'], 0)
        self.assertAlmostEqual(sum(phases.values()), timing['elapsed_seconds'], delta=0.01)
        self.assertEqual(timing['events']['model_steps'], 1)
        committed = json.loads((repo / '.opencode' / 'runs' / (result['run_id'] + '.json')).read_text())
        self.assertIsNotNone(committed['timing']['active_phase'])
        self.assertEqual(worker_runtime.verify_commit(repo, 'HEAD'), result['commit'])
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            worker_runtime.export_stats(self.fixture.base, 'csv')
        row = next(csv.DictReader(io.StringIO(stream.getvalue())))
        self.assertEqual(float(row['time_model_seconds']), phases['model'])
        self.assertAlmostEqual(float(row['time_checks_seconds']),
                               phases['before_commit'] + phases['after_commit'], delta=0.001)

    def test_failed_child_exposes_timing_and_preserves_head(self):
        repo = self.fixture.make_repo()
        before = self.fixture.run_head(repo)
        code, output, errors = self.fixture.call_main(
            ['run', '--dir', str(repo), 'change source'], behavior='failure')
        self.assertEqual(code, 1)
        self.assertEqual(output, '')
        result = json.loads(errors)
        report = json.loads(Path(result['report']).read_text(encoding='utf-8'))
        self.assertEqual(result['timing'], report['timing'])
        self.assertIsNone(result['timing']['active_phase'])
        self.assertGreater(result['timing']['phases_seconds']['model'], 0)
        self.assertNotIn('commit', result['timing']['phases_seconds'])
        self.assertEqual(self.fixture.run_head(repo), before)

    def test_preflight_is_visible_to_the_installer_before_project_discovery(self):
        from worker_wait import active_runs
        from install import InstallError, install
        repo = self.fixture.make_repo()
        discover = worker_runtime.load_project
        observed = []

        def inspect_preflight(path):
            running = active_runs(self.fixture.base)
            self.assertEqual(len(running), 1)
            report_path = self.fixture.base / 'runs' / running[0] / 'report.json'
            report = json.loads(report_path.read_text())
            self.assertEqual(report['status'], 'preflight')
            self.assertEqual(report['timing']['active_phase'], 'preflight')
            with self.assertRaisesRegex(InstallError, 'worker is active'):
                install(ROOT, self.fixture.base, self.fixture.base / 'codex', check=True)
            observed.append(running[0])
            return discover(path)

        with mock.patch.object(worker_job, 'load_project', side_effect=inspect_preflight):
            code, output, errors = self.fixture.call_main(
                ['run', '--dir', str(repo), 'change source'])
        self.assertEqual(code, 0, errors)
        self.assertEqual(observed, [json.loads(output)['run_id']])

    def test_final_storage_failure_still_returns_failure_after_timer_is_finished(self):
        repo = self.fixture.make_repo()
        save = worker_runtime.save_report

        def fail_final(base, directory, report):
            if report.get('finalized'):
                raise OSError('fixture persistence failure')
            return save(base, directory, report)

        with mock.patch.object(worker_job, 'save_report', side_effect=fail_final):
            code, output, errors = self.fixture.call_main(
                ['run', '--dir', str(repo), 'change source'])
        self.assertEqual(code, 1)
        self.assertEqual(output, '')
        result = json.loads(errors)
        self.assertEqual(result['persistence_error'], 'OSError')
        self.assertIsNone(result['timing']['active_phase'])
        self.assertTrue(Path(result['report']).is_file())

    def test_timing_failure_is_diagnostic_and_preserves_delivery_or_failure_report(self):
        for behavior, expected in (('success', 0), ('failure', 1)):
            with self.subTest(behavior=behavior):
                repo = self.fixture.make_repo('timer-' + behavior)
                broken = mock.Mock()
                broken.snapshot.side_effect = RuntimeError('fixture timer failure')
                with mock.patch.object(worker_job, 'RunTimer', return_value=broken):
                    code, output, errors = self.fixture.call_main(
                        ['run', '--dir', str(repo), 'change source'], behavior=behavior)
                self.assertEqual(code, expected, errors)
                result = json.loads(output if expected == 0 else errors)
                report = json.loads(Path(result['report']).read_text())
                self.assertTrue(report['finalized'])
                self.assertEqual(report['timing']['availability'], 'unavailable')
                self.assertEqual(report['timing']['error'], 'RuntimeError')
                self.assertGreaterEqual(report['elapsed_seconds'], 0)
                if expected == 0:
                    self.assertEqual(worker_runtime.verify_commit(repo, 'HEAD'), result['commit'])

    def test_legacy_csv_keeps_missing_timings_unknown(self):
        base = self.fixture.base
        run = base / 'runs' / 'legacy-fixture'
        report = {'run_id': 'legacy-fixture', 'status': 'failed', 'metrics': {}, 'git': {}}
        worker_runtime.save_report(base, run, report)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            worker_runtime.export_stats(base, 'csv')
        row = next(csv.DictReader(io.StringIO(stream.getvalue())))
        self.assertIn('time_model_seconds', row)
        self.assertEqual(row['time_model_seconds'], '')
        self.assertEqual(row['time_tool_execution_seconds'], '')


if __name__ == '__main__':
    unittest.main()
