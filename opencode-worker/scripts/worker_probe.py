"""Bounded Hello probe through the real OpenCode CLI, outside any project."""
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from worker_metrics import MetricsError, parse_events
from worker_platform import process_options, stop_process


def _reply(path):
    parts = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') == 'text':
            value = event.get('part', {}).get('text')
            if isinstance(value, str):
                parts.append(value)
    return ''.join(parts).strip() or None


def _requires_region_consent(path):
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
            data = event.get('error', {}).get('data', {})
            body = json.loads(data.get('responseBody', '{}'))
            if event.get('type') == 'error' and data.get('statusCode') == 403 and body.get('error', {}).get('type') == 'RegionError':
                return True
        except (ValueError, TypeError, AttributeError):
            continue
    return False


def run_hello(base, selection, cli, environment_factory, timeout=10):
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Hello timeout must be a positive finite number')
    probe = Path(base) / 'probes' / str(uuid.uuid4())
    probe.mkdir(parents=True, mode=0o700)
    events, errors = probe / 'events.jsonl', probe / 'stderr.log'
    report = {'status': 'failed', 'provider': selection['provider_label'],
              'provider_id': selection['provider_id'], 'requested_model': selection['model'],
              'timeout_seconds': timeout, 'response': None, 'metrics': None,
              'application_workflow_executed': False, 'billing_source': 'provider_managed_unobserved',
              'report': str(probe / 'report.json')}
    env = environment_factory(probe)
    config = json.loads(env.get('OPENCODE_CONFIG_CONTENT', '{}'))
    config['agent'] = {'worker-hello': {'mode': 'primary', 'prompt': 'Reply with exactly Hello. Use no tools.',
                                       'permission': {'*': 'deny'}}}
    env['OPENCODE_CONFIG_CONTENT'] = json.dumps(config)
    process = None
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='opencode-hello-') as directory:
        command = list(cli) + ['run', '--pure', '--model', selection['model'], '--agent', 'worker-hello',
                               '--dir', directory, '--format', 'json', 'Hello']
        try:
            with events.open('wb') as out, errors.open('wb') as err:
                os.chmod(events, 0o600)
                os.chmod(errors, 0o600)
                started = time.monotonic()
                process = subprocess.Popen(command, cwd=directory, env=env, stdout=out, stderr=err,
                                           **process_options())
                process.wait(timeout=timeout)
                report['elapsed_seconds'] = round(time.monotonic() - started, 3)
            reply = _reply(events)
            report['response'] = reply
            if process.returncode == 0 and reply and reply.lower().rstrip('!.') == 'hello':
                report['status'] = 'passed'
            else:
                report['error'] = 'OpenCode did not complete the expected Hello response'
                if _requires_region_consent(events):
                    report.update(status='requires_action', action_required='provider_region_opt_in',
                                  error=selection['provider_label'] + ' requires explicit hosting-region consent in its console')
        except subprocess.TimeoutExpired:
            report.update(status='timed_out', error='OpenCode Hello exceeded the response deadline')
        except OSError:
            report['error'] = 'OpenCode could not be started'
        finally:
            if process is not None and process.poll() is None:
                stop_process(process)
            report.setdefault('elapsed_seconds', round(time.monotonic() - started, 3))
            report['exit_code'] = process.returncode if process is not None else None
    try:
        report['metrics'] = parse_events(events, allow_partial=True)
    except MetricsError:
        pass  # Missing accounting is unknown, never an invented zero.
    target = Path(report['report'])
    with target.open('w', encoding='utf-8') as stream:
        os.chmod(target, 0o600)
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return report
