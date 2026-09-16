"""The Hello acceptance check exercises the CLI boundary, not a raw API."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from worker_probe import run_hello


class ProbeTests(unittest.TestCase):
    def probe(self, source, timeout=2):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            script = base / 'cli.py'
            script.write_text(source)
            result = run_hello(base, {'provider_id': 'opencode-go', 'provider_label': 'OpenCode Go',
                                    'model': 'opencode-go/deepseek-v4.1-flash',
                                    'cost_basis': 'fixture estimate'},
                               [sys.executable, str(script)], lambda folder: os.environ.copy(), timeout)
            return result, json.loads(Path(result['report']).read_text())

    def test_completed_hello_uses_cli_and_private_probe_directory(self):
        source = '''import json, sys
assert sys.argv[1] == 'run'
assert sys.argv[sys.argv.index('--model')+1] == 'opencode-go/deepseek-v4.1-flash'
assert sys.argv[-1] == 'Hello'
print(json.dumps({'type':'text','sessionID':'s','part':{'type':'text','text':'Hello'}}))
'''
        result, report = self.probe(source)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(report['response'], 'Hello')
        self.assertLess(report['elapsed_seconds'], 2)
        self.assertFalse(report['application_workflow_executed'])
        self.assertEqual(report['cost_basis'], 'fixture estimate')

    def test_no_reply_within_deadline_is_failure(self):
        result, report = self.probe('import time; time.sleep(60)', timeout=0.05)
        self.assertEqual(result['status'], 'timed_out')
        self.assertIsNone(report['response'])

    def test_ignored_term_timeout_is_prompt_and_cannot_pass_late(self):
        source = '''import json, signal, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
time.sleep(0.2)
print(json.dumps({'type':'text','part':{'type':'text','text':'Hello'}}), flush=True)
time.sleep(60)
'''
        started = time.monotonic()
        result, report = self.probe(source, timeout=0.05)
        self.assertLess(time.monotonic() - started, 1)
        self.assertEqual(result['status'], 'timed_out')
        self.assertIsNone(report['response'])

    def test_wrong_reply_does_not_pass_connectivity_criterion(self):
        result, _ = self.probe("import json; print(json.dumps({'type':'text','part':{'text':'Goodbye'}}))")
        self.assertEqual(result['status'], 'failed')

    def test_finished_hello_cannot_pass_when_observed_after_deadline(self):
        # Simulate scheduling delay after a successful child exit, without
        # changing subprocess's own monotonic clock or waiting in real time.
        with mock.patch('worker_probe.time') as clock:
            clock.monotonic.side_effect = [0, 0, 0, 3, 3]
            result, report = self.probe("import json; print(json.dumps({'type':'text','part':{'text':'Hello'}}))")
        self.assertEqual(result['status'], 'timed_out')
        self.assertIsNone(report['response'])

    def test_provider_region_consent_is_reported_without_private_payload(self):
        event = {'type': 'error', 'error': {'name': 'APIError', 'data': {'statusCode': 403,
            'responseBody': json.dumps({'error': {'type': 'RegionError', 'message': 'private account URL'}})}}}
        result, report = self.probe('import json; print(' + repr(json.dumps(event)) + ')')
        self.assertEqual(result['status'], 'requires_action')
        self.assertEqual(report['action_required'], 'provider_region_opt_in')
        self.assertNotIn('private account URL', json.dumps(report))
