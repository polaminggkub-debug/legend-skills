import json
import contextlib
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from worker_control import configure
from worker_runtime import child_environment, main
from worker_provider import ProviderError
import worker_probe


class ControlTests(unittest.TestCase):
    def test_configure_migrates_provider_without_losing_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / 'settings.json'
            path.write_text(json.dumps({'default_model': 'deepseek/deepseek-v4.1-flash',
                                        'heartbeat_interval_seconds': 5, 'custom': 'keep'}))
            result = configure(base, 'opencode-go', 'deepseek-v4.1-flash')
            value = json.loads(path.read_text())
            self.assertEqual(value['default_model'], 'opencode-go/deepseek-v4.1-flash')
            self.assertEqual(value['allowed_providers'], ['opencode-go'])
            self.assertEqual(value['custom'], 'keep')
            self.assertFalse(result['automatic_provider_fallback'])
            configure(base, model='glm-5.3')
            self.assertEqual(json.loads(path.read_text())['default_model'], 'opencode-go/glm-5.3')

    def test_go_child_environment_has_one_provider_and_no_router_key(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            env = child_environment(base, 'opencode-go/deepseek-v4.1-flash', 'fixture-only-key', base)
            config = json.loads(env['OPENCODE_CONFIG_CONTENT'])
            self.assertEqual(config['enabled_providers'], ['opencode-go'])
            self.assertNotIn('OPENROUTER_API_KEY', env)
            self.assertEqual(config['provider']['opencode-go']['options']['apiKey'], 'fixture-only-key')
            self.assertEqual(config['small_model'], config['model'])
            for path in base.rglob('*'):
                if path.is_file():
                    self.assertNotIn('fixture-only-key', path.read_text())

    def test_wait_cli_returns_one_final_result_and_success_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run_id = '11111111-1111-4111-8111-111111111111'
            run = base / 'runs' / run_id
            run.mkdir(parents=True)
            (run / 'report.json').write_text(json.dumps({'run_id': run_id, 'status': 'committed',
                'phase': 'finished', 'finalized': True, 'provider': 'OpenCode Go', 'git': {'commit': 'abc'}}))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(['wait', '--run', run_id], base=base)
            self.assertEqual(code, 0)
            self.assertEqual(len(output.getvalue().splitlines()), 1)
            self.assertEqual(json.loads(output.getvalue())['commit'], 'abc')

    def test_configure_preserves_settings_while_a_recorded_worker_is_alive(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            settings = base / 'settings.json'
            settings.write_text('{"default_model":"deepseek/deepseek-v4.1-flash"}')
            before = settings.read_bytes()
            run = base / 'runs' / '11111111-1111-4111-8111-111111111111'
            run.mkdir(parents=True)
            (run / 'report.json').write_text(json.dumps({'run_id': run.name, 'status': 'running',
                'finalized': False, 'launcher_pid': os.getpid()}))
            with self.assertRaises(ProviderError):
                configure(base, 'opencode-go')
            self.assertEqual(settings.read_bytes(), before)

    def test_hello_refuses_live_worker_before_credential_or_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            settings = base / 'settings.json'
            settings.write_text(json.dumps({
                'default_provider': 'opencode-go',
                'allowed_providers': ['opencode-go'],
                'default_model': 'opencode-go/deepseek-v4.1-flash',
                'cli_binary': 'opencode',
            }))
            before = settings.read_bytes()
            run_id = '11111111-1111-4111-8111-111111111111'
            run = base / 'runs' / run_id
            run.mkdir(parents=True)
            (run / 'report.json').write_text(json.dumps({
                'run_id': run_id, 'status': 'running', 'finalized': False,
                'launcher_pid': os.getpid(),
            }))
            credential_calls = []

            def credential_reader():
                credential_calls.append(True)
                return 'fixture-key'

            output, errors = io.StringIO(), io.StringIO()
            with mock.patch.object(worker_probe, 'run_hello') as probe:
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    code = main(['hello'], base=base, credential_reader=credential_reader)

            self.assertEqual(code, 1)
            self.assertEqual(credential_calls, [])
            probe.assert_not_called()
            self.assertEqual(settings.read_bytes(), before)
            self.assertIn('still active', errors.getvalue())

    def test_hello_uses_isolated_probe_state_for_environment_and_model_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            settings = base / 'settings.json'
            settings.write_text(json.dumps({
                'default_provider': 'opencode-go',
                'allowed_providers': ['opencode-go'],
                'default_model': 'opencode-go/deepseek-v4.1-flash',
                'cli_binary': sys.executable,
            }))
            before = settings.read_bytes()
            captured = {}
            credential_calls = []

            def credential_reader():
                credential_calls.append(True)
                return 'fixture-key'

            def fake_hello(_base, selection, _cli, environment_factory, _timeout):
                probe = base / 'probes' / 'fixture-probe'
                probe.mkdir(parents=True)
                captured['probe'] = probe
                captured['environment'] = environment_factory(probe)
                database = probe / 'data' / 'opencode' / 'opencode.db'
                database.parent.mkdir(parents=True)
                with sqlite3.connect(database) as connection:
                    connection.execute('CREATE TABLE message (session_id TEXT, data TEXT)')
                    connection.execute(
                        'INSERT INTO message VALUES (?, ?)',
                        ('hello-session', json.dumps({
                            'role': 'assistant', 'providerID': selection['provider_id'],
                            'modelID': 'deepseek-v4.1-flash',
                        })),
                    )
                report = probe / 'report.json'
                return {'status': 'passed', 'metrics': {'session_id': 'hello-session'},
                        'report': str(report)}

            output = io.StringIO()
            with mock.patch.object(worker_probe, 'run_hello', side_effect=fake_hello):
                with contextlib.redirect_stdout(output):
                    code = main(['hello'], base=base, credential_reader=credential_reader)

            result = json.loads(output.getvalue())
            environment = captured['environment']
            probe = captured['probe']
            self.assertEqual(code, 0)
            self.assertEqual(result['observed_models'], ['opencode-go/deepseek-v4.1-flash'])
            self.assertEqual(Path(environment['XDG_DATA_HOME']), probe / 'data')
            self.assertEqual(Path(environment['XDG_CONFIG_HOME']), probe / 'config')
            self.assertEqual(Path(environment['XDG_STATE_HOME']), probe / 'state')
            self.assertEqual(Path(environment['XDG_CACHE_HOME']), probe / 'cache')
            self.assertEqual(Path(environment['OPENCODE_CONFIG_DIR']), probe / 'config' / 'opencode')
            self.assertEqual(credential_calls, [True])
            self.assertEqual(settings.read_bytes(), before)
            for path in base.rglob('*'):
                if path.is_file():
                    self.assertNotIn('fixture-key', path.read_text(encoding='utf-8', errors='replace'))
