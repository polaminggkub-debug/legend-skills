import json
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from worker_control import configure
from worker_runtime import child_environment, main
from worker_provider import ProviderError


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
