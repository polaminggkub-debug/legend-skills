"""Small setup/probe/wait commands; none dispatch a coding task."""
import argparse
import getpass
import json
from pathlib import Path

from worker_platform import cli_command, read_key, store_key
from worker_provider import ProviderError, SUPPORTED_PROVIDERS, resolve_selection


def load_settings(base):
    value = json.loads((Path(base) / 'settings.json').read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ProviderError('Worker settings must be a JSON object')
    return value


def configure(base, provider=None, model=None):
    from worker_runtime import write_json
    from worker_wait import active_runs
    if active_runs(base):
        raise ProviderError('An OpenCode worker is still active; configure after it finishes')
    settings = load_settings(base)
    current = resolve_selection(settings)
    target = provider or current['provider_id']
    candidate = dict(settings, default_provider=target, allowed_providers=[target])
    if provider and provider != current['provider_id'] and model is None:
        candidate.pop('default_model', None)
    selection = resolve_selection(candidate, model)
    candidate['default_model'] = selection['model']
    write_json(Path(base) / 'settings.json', candidate)
    return {'status': 'configured', 'provider': selection['provider_label'],
            'model': selection['model'], 'automatic_provider_fallback': False}


def execute_control(argv, base, credential_reader):
    if not argv or argv[0] not in ('auth', 'configure', 'hello', 'wait'):
        return None
    from worker_runtime import child_environment, observed_models, write_json
    command = argv[0]
    parser = argparse.ArgumentParser(prog='opencode-worker ' + command)
    if command == 'wait':
        from worker_wait import wait_for_run
        parser.add_argument('--run', required=True)
        args = parser.parse_args(argv[1:])
        result = wait_for_run(base, args.run)
        print(json.dumps(result))
        return 0 if result.get('status') in ('committed', 'no_changes') else 1
    if command == 'configure':
        parser.add_argument('--provider', choices=SUPPORTED_PROVIDERS)
        parser.add_argument('--model')
        args = parser.parse_args(argv[1:])
        print(json.dumps(configure(base, args.provider, args.model)))
        return 0
    settings = load_settings(base)
    if command == 'auth':
        parser.add_argument('action', choices=['login', 'status'])
        parser.add_argument('--provider', choices=SUPPORTED_PROVIDERS)
        args = parser.parse_args(argv[1:])
        selection = resolve_selection({'default_provider': args.provider}) if args.provider else resolve_selection(settings)
        if args.action == 'login':
            key = getpass.getpass(selection['provider_label'] + ' API key (hidden): ').strip()
            store_key(key, selection['provider_id'])
            print(json.dumps({'status': 'stored', 'provider': selection['provider_label'], 'storage': 'OS credential store'}))
            return 0
        try:
            present = bool(read_key(selection['provider_id']) if credential_reader is read_key else credential_reader())
        except Exception:
            present = False
        print(json.dumps({'configured': present, 'provider': selection['provider_label']}))
        return 0 if present else 1
    from worker_wait import active_runs
    from worker_probe import run_hello
    parser.add_argument('--model')
    parser.add_argument('--timeout', type=float, default=settings.get('hello_timeout_seconds', 10))
    args = parser.parse_args(argv[1:])
    if active_runs(base):
        raise ProviderError('An OpenCode worker is still active; run hello after it finishes')
    selection = resolve_selection(settings, args.model)
    key = read_key(selection['provider_id']) if credential_reader is read_key else credential_reader()
    result = run_hello(base, selection, cli_command(settings['cli_binary']),
                       lambda directory: child_environment(base, selection['model'], key, directory), args.timeout)
    session = (result.get('metrics') or {}).get('session_id')
    result['observed_models'] = observed_models(base, session)
    if result['status'] == 'passed' and result['observed_models'] != [selection['model']]:
        result.update(status='failed', error='Hello returned without matching actual model evidence')
    write_json(Path(result['report']), result)
    print(json.dumps(result))
    return 0 if result['status'] == 'passed' else 1
