"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
import uuid
import getpass
import shutil
from contextlib import closing

from worker_metrics import MetricsError, parse_events, validate_report
from worker_monitor import ProcessMonitor, TerminalOpenCodeError as MonitorTerminalError
from worker_provider import resolve_selection, ProviderError
from worker_wait import WaitError
from worker_platform import (CredentialStoreUnavailable, RepositoryLock, cli_command, default_base_dir,
                             process_options, read_key, stop_process, store_key)
from worker_project import (ProjectError, assert_unchanged, command_argv,
                            inspect_project, load_project, path_allowed)
from worker_delivery import DeliveryError, run_steps

BASE = default_base_dir()


class GuardrailError(Exception):
    pass


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def interrupt_run(signum, frame):
    raise KeyboardInterrupt()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as stream:
        os.chmod(temp, 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    temp.replace(path)


def git(repo, *args, check=True, env=None):
    git_env = {k: v for k, v in (os.environ if env is None else env).items()
               if not k.upper().startswith('GIT_')}
    result = subprocess.run(['git', '-C', str(repo)] + list(args),
                            capture_output=True, env=git_env, timeout=60)
    if check and result.returncode:
        # Details remain local; never serialize an arbitrary hook's output.
        label = 'Git command failed: ' + ' '.join(args[:2])
        if args and args[0] == 'commit':
            label = 'Git commit failed; check repository hooks and local Git diagnostics'
        error = GuardrailError(label)
        error.local_diagnostics = result.stderr
        raise error
    return result


def git_text(repo, *args):
    return git(repo, *args).stdout.decode('utf-8', 'surrogateescape').strip()


def safe_report_directory(repo):
    for path in (repo / '.opencode', repo / '.opencode' / 'runs'):
        if path.is_symlink():
            raise GuardrailError('Audit report directories must not be symlinks')
        if path.exists() and not path.is_dir():
            raise GuardrailError('Audit report directory is occupied by a file')


def save_report(base, run_dir, report):
    write_json(run_dir / 'report.json', report)
    database = base / 'runs.sqlite3'
    with closing(sqlite3.connect(str(database), timeout=20)) as conn, conn:
        conn.execute('CREATE TABLE IF NOT EXISTS runs '
                     '(run_id TEXT PRIMARY KEY, status TEXT NOT NULL, report_json TEXT NOT NULL)')
        conn.execute('INSERT OR REPLACE INTO runs VALUES (?, ?, ?)',
                     (report['run_id'], report['status'], json.dumps(report, allow_nan=False)))
    os.chmod(database, 0o600)


def observed_models(base, session_id):
    database = base / 'data' / 'opencode' / 'opencode.db'
    if not database.is_file() or not session_id:
        return []
    try:
        with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
            rows = conn.execute('SELECT data FROM message WHERE session_id=?', (session_id,))
            models = set()
            for row in rows:
                value = json.loads(row[0])
                if value.get('role') != 'assistant':
                    continue
                provider, model = value.get('providerID'), value.get('modelID')
                if isinstance(provider, str) and isinstance(model, str):
                    models.add(provider + '/' + model)
            return sorted(models)
    except (sqlite3.Error, ValueError):
        return []


def prepare_instructions(repo, directory, run_dir):
    """Snapshot applicable project guidance without enabling project config."""
    directory = Path(directory).resolve()
    relative = directory.relative_to(repo)
    folders = [repo]
    for part in relative.parts:
        folders.append(folders[-1] / part)
    sections, sources, size = [], [], 0
    for folder in folders:
        for name in ('AGENTS.md', 'CLAUDE.md', 'CONTEXT.md'):
            path = folder / name
            if not path.exists():
                continue
            try:
                path.resolve().relative_to(repo)
                raw = path.read_bytes()
                content = raw.decode('utf-8')
            except (ValueError, OSError) as exc:
                raise GuardrailError('Project guidance must be a readable UTF-8 file inside the repository') from exc
            size += len(raw)
            if size > 131072:
                raise GuardrailError('Applicable project guidance exceeds 128 KiB; prepare bounded project guidance before delegation')
            source = path.relative_to(repo).as_posix()
            sources.append({'path': source, 'sha256': hashlib.sha256(raw).hexdigest()})
            scope = folder.relative_to(repo).as_posix()
            sections.append('## Project guidance: ' + source + '\nApplies within: ' + scope + '\n\n' + content)
            break  # AGENTS wins over the Claude/deprecated fallback in a folder.
    if not sections:
        return None, {'source': 'none', 'files': []}
    snapshot = run_dir / 'instructions.md'
    snapshot.write_bytes(('Project guidance snapshot. More specific directory guidance applies within its own scope.\n\n'
                          + '\n\n'.join(sections) + '\n').encode('utf-8'))
    snapshot.chmod(0o600)
    return snapshot, {'source': 'explicit_absolute_instructions', 'files': sources,
                      'snapshot_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest()}


def child_environment(base, model, key, run_dir, instructions=None):
    env = os.environ.copy()
    for name in list(env):
        if name.upper().startswith(('OPENCODE_', 'GIT_')):
            env.pop(name)
    provider_id = model.split('/', 1)[0]
    selection = resolve_selection({'default_provider': provider_id, 'default_model': model})
    config = {'model': model, 'small_model': model, 'enabled_providers': [provider_id],
              'provider': {provider_id: {'options': {'apiKey': key}}}}
    for name in ('OPENROUTER_API_KEY', 'OPENCODE_API_KEY', 'OPENCODE_GO_API_KEY'):
        env.pop(name, None)
    if instructions is not None:
        config['instructions'] = [Path(instructions).resolve().as_posix()]
    env.update({
        selection['credential_env']: key,
        'XDG_CONFIG_HOME': str(base / 'config'),
        'XDG_DATA_HOME': str(base / 'data'),
        'XDG_STATE_HOME': str(base / 'state'),
        'XDG_CACHE_HOME': str(base / 'cache'),
        'OPENCODE_CONFIG_DIR': str(base / 'config' / 'opencode'),
        'OPENCODE_CONFIG_CONTENT': json.dumps(config),
        'OPENCODE_DISABLE_PROJECT_CONFIG': 'true',
        'OPENCODE_DISABLE_EXTERNAL_SKILLS': 'true',
        'OPENCODE_DISABLE_CLAUDE_CODE': 'true',
    })
    # Only the worker inherits these hooks. Final commits use the repository's
    # real hooks. HEAD is checked independently in case a worker bypasses hooks.
    hooks = run_dir / 'worker-hooks'
    hooks.mkdir()
    for name in ('pre-commit', 'pre-push'):
        path = hooks / name
        path.write_bytes(b'#!/bin/sh\necho "The audited wrapper owns Git commits and publishing is disabled." >&2\nexit 1\n')
        path.chmod(0o700)
    env['GIT_CONFIG_KEY_0'] = 'core.hooksPath'
    env['GIT_CONFIG_VALUE_0'] = str(hooks)
    env['GIT_CONFIG_COUNT'] = '1'
    return env


def reason_effort(base, model, variant):
    if variant:
        return variant
    try:
        config = json.loads((base / 'config' / 'opencode' / 'opencode.json').read_text(encoding='utf-8'))
        provider, model_id = model.split('/', 1)
        return config['provider'][provider]['models'][model_id]['options']['reasoning']['effort']
    except (OSError, ValueError, KeyError):
        return None


def diff_stats(repo, base_commit, target=None):
    args = ['diff', '--numstat', '-z', '--no-renames', base_commit]
    args += [target] if target else ['--cached']
    args += ['--', '.', ':(exclude).opencode/runs/**']
    files, additions, deletions, binary = [], 0, 0, 0
    for row in git(repo, *args).stdout.split(b'\0'):
        if not row:
            continue
        added, removed, path = row.split(b'\t', 2)
        is_binary = added == b'-' or removed == b'-'
        files.append({'path': os.fsdecode(path),
                      'insertions': None if is_binary else int(added),
                      'deletions': None if is_binary else int(removed)})
        binary += int(is_binary)
        if not is_binary:
            additions += int(added)
            deletions += int(removed)
    return {'files': files, 'insertions': additions, 'deletions': deletions, 'binary_files': binary}


def changed_paths(repo):
    paths = set(git(repo, 'diff', '--name-only', '-z', 'HEAD', '--').stdout.split(b'\0'))
    paths.update(git(repo, 'ls-files', '--others', '--exclude-standard', '-z').stdout.split(b'\0'))
    return sorted(os.fsdecode(path) for path in paths if path)


def enforce_scope(repo, patterns):
    for path in changed_paths(repo):
        if path == '.opencode/worker.json' or path.startswith('.opencode/runs/'):
            raise GuardrailError('A worker or command modified an immutable workflow/audit file')
        if not path_allowed(path, patterns):
            raise GuardrailError('Changed file is outside the declared write scope: ' + path)


def check_cancel(run_dir):
    if (run_dir / 'cancel.request').exists():
        raise KeyboardInterrupt()


def execute_checks(repo, run_dir, report, plan, stage):
    check_cancel(run_dir)
    steps = [step for step in plan['checks'] if step['stage'] == stage]
    report['phase'] = stage
    save_report(run_dir.parent.parent, run_dir, report)
    try:
        results = run_steps(steps, repo=repo, run_dir=run_dir, stage=stage)
    except BaseException as exc:
        report['checks']['results'].extend(getattr(exc, 'results', []))
        report['checks']['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        raise
    report['checks']['results'].extend(results)
    completed = {result['id'] for result in report['checks']['results']}
    if not plan['checks']:
        report['checks']['status'] = 'not_declared'
    elif any(step['id'] not in completed for step in plan['checks']):
        report['checks']['status'] = 'pending'
    elif any(result['status'] != 'passed' for result in report['checks']['results']):
        report['checks']['status'] = 'passed_with_warnings'
    else:
        report['checks']['status'] = 'passed'


def finalize_metadata(repo, run_dir, report, plan):
    check_cancel(run_dir)
    source_commit = report['git']['source_commit']
    if not report['git']['commit']:
        raise GuardrailError('Metadata handoff requires an attributed source change; worker made no changes')
    report['phase'] = 'metadata'
    report['delivery'] = {'status': 'pending', 'source_commit': source_commit, 'metadata_commit': None, 'results': []}
    save_report(run_dir.parent.parent, run_dir, report)
    try:
        results = run_steps(plan['handoff']['metadata'], repo=repo, run_dir=run_dir, stage='metadata',
                            env={'WORKER_SOURCE_COMMIT': source_commit,
                                 'WORKER_RUN_ID': report['run_id'], 'WORKER_REPO_ROOT': str(repo)})
        report['delivery']['results'] = results
    except BaseException as exc:
        report['delivery']['results'] = getattr(exc, 'results', [])
        report['delivery']['status'] = 'failed'
        raise
    assert_unchanged(repo, plan)
    if git_text(repo, 'rev-parse', 'HEAD') != source_commit:
        raise GuardrailError('Metadata command changed HEAD')
    enforce_scope(repo, plan['handoff']['write_paths'])
    if not changed_paths(repo):
        report['delivery']['status'] = 'no_metadata_changes'
        return
    git(repo, 'add', '-A', '--', '.')
    source_report_path = '.opencode/runs/' + report['run_id'] + '.json'
    source_report_bytes = git(repo, 'show', source_commit + ':' + source_report_path).stdout
    metadata = {
        'schema_version': 1, 'phase': 'metadata', 'run_id': report['run_id'],
        'source_commit': source_commit, 'source_report_sha256': hashlib.sha256(source_report_bytes).hexdigest(),
        'contract_sha256': plan.get('contract_committed_sha256', plan['contract_sha256']),
        'source_models': report['observed_models'],
        'changes': diff_stats(repo, source_commit), 'steps': results,
        'model_calls': 0, 'tokens_total': 0, 'estimated_cost_usd': 0,
    }
    relative = '.opencode/runs/' + report['run_id'] + '-metadata.json'
    safe_report_directory(repo)
    write_json(repo / relative, metadata)
    digest = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
    git(repo, 'add', '--', relative)
    expected_tree = git_text(repo, 'write-tree')
    message = run_dir / 'metadata-commit-message.txt'
    message.write_text('\n'.join([
        'chore(opencode): finalize declared metadata', '',
        'Deterministic delivery; model usage is recorded in the source run.', '',
        'Generated-By: OpenCode workflow', 'Via: ' + report['provider'],
        'Model-Observed: ' + ', '.join(report['observed_models']),
        'OpenCode-Run: ' + report['run_id'], 'Run-Phase: metadata',
        'OpenCode-Source-Commit: ' + source_commit,
        'Tokens-Total: 0', 'Model-Calls: 0', 'Cost-Estimate-USD: 0',
        'Run-Report: ' + relative, 'Run-Report-SHA256: ' + digest, '',
    ]), encoding='utf-8')
    check_cancel(run_dir)
    git(repo, 'commit', '--file', str(message))
    commit = git_text(repo, 'rev-parse', 'HEAD')
    report['git']['commit'] = commit
    report['delivery']['metadata_commit'] = commit
    report['commit_verified'] = False
    if git_text(repo, 'show', '-s', '--format=%T', commit) != expected_tree:
        raise GuardrailError('A Git hook changed metadata during commit')
    verify_commit(repo, commit)
    if git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
        raise GuardrailError('Working tree changed during metadata commit')
    report['commit_verified'] = True
    report['delivery']['status'] = 'metadata_committed'


def commit_message(report, relative_path, digest, title):
    tokens = report['metrics']['tokens']
    return '\n'.join([
        'chore(opencode): ' + title,
        '',
        'Generated-By: OpenCode',
        'Via: ' + report['provider'],
        'Model-Requested: ' + report['requested_model'],
        'Model-Observed: ' + ', '.join(report['observed_models']),
        'OpenCode-Version: ' + report['opencode_version'],
        'OpenCode-Run: ' + report['run_id'],
        'Tokens-Total: ' + str(tokens['total']),
        'Cost-Estimate-USD: ' + str(report['metrics']['estimated_cost_usd']),
        'Duration-Seconds: ' + str(report['elapsed_seconds']),
        'Run-Report: ' + relative_path,
        'Run-Report-SHA256: ' + digest,
        '',
    ])


def verify_commit(repo, revision):
    commit = git_text(repo, 'rev-parse', '--verify', revision + '^{commit}')
    body = git_text(repo, 'show', '-s', '--format=%B', commit)
    trailers = {}
    for line in body.splitlines():
        if ': ' in line:
            key, value = line.split(': ', 1)
            if key in trailers:
                raise GuardrailError('Duplicate attribution field: ' + key)
            trailers[key] = value
    run_id = trailers.get('OpenCode-Run', '')
    try:
        if str(uuid.UUID(run_id)) != run_id:
            raise ValueError()
    except ValueError:
        raise GuardrailError('Missing or invalid OpenCode run ID')
    if trailers.get('Run-Phase') == 'metadata':
        return verify_metadata_commit(repo, commit, run_id, trailers)
    relative = '.opencode/runs/' + run_id + '.json'
    if trailers.get('Run-Report') != relative:
        raise GuardrailError('Missing or invalid committed run report')
    raw = git(repo, 'show', commit + ':' + relative).stdout
    if hashlib.sha256(raw).hexdigest() != trailers.get('Run-Report-SHA256'):
        raise GuardrailError('Committed report digest does not match')
    report = json.loads(raw)
    if report.get('status') != 'ready_to_commit':
        raise GuardrailError('Committed report is not a completed pre-commit record')
    errors = validate_report(report)
    if errors:
        raise GuardrailError('Invalid committed report: ' + '; '.join(errors))
    expected = {
        'Generated-By': 'OpenCode', 'Via': report['provider'],
        'Model-Requested': report['requested_model'],
        'Model-Observed': ', '.join(report['observed_models']),
        'OpenCode-Version': report['opencode_version'],
        'OpenCode-Run': report['run_id'],
        'Tokens-Total': str(report['metrics']['tokens']['total']),
        'Cost-Estimate-USD': str(report['metrics']['estimated_cost_usd']),
        'Duration-Seconds': str(report['elapsed_seconds']),
    }
    if any(trailers.get(k) != v for k, v in expected.items()):
        raise GuardrailError('Commit attribution does not match the recorded evidence')
    parents = git_text(repo, 'show', '-s', '--format=%P', commit).split()
    if parents != [report['git']['base_commit']]:
        raise GuardrailError('Commit parent does not match run base')
    if diff_stats(repo, parents[0], commit) != report['changes']:
        raise GuardrailError('Committed changes differ from run statistics')
    return commit


def verify_metadata_commit(repo, commit, run_id, trailers):
    relative = '.opencode/runs/' + run_id + '-metadata.json'
    if trailers.get('Run-Report') != relative:
        raise GuardrailError('Invalid metadata report path')
    raw = git(repo, 'show', commit + ':' + relative).stdout
    if hashlib.sha256(raw).hexdigest() != trailers.get('Run-Report-SHA256'):
        raise GuardrailError('Metadata report digest does not match')
    metadata = json.loads(raw)
    source_commit = metadata.get('source_commit')
    if git_text(repo, 'show', '-s', '--format=%P', commit).split() != [source_commit]:
        raise GuardrailError('Metadata commit must directly follow its source commit')
    source_body = git_text(repo, 'show', '-s', '--format=%B', source_commit)
    if 'Run-Phase: metadata' in source_body:
        raise GuardrailError('Metadata cannot attribute another metadata commit as its source')
    verify_commit(repo, source_commit)
    source_raw = git(repo, 'show', source_commit + ':.opencode/runs/' + run_id + '.json').stdout
    source = json.loads(source_raw)
    plan = source.get('project', {})
    if metadata.get('source_report_sha256') != hashlib.sha256(source_raw).hexdigest():
        raise GuardrailError('Metadata source report digest does not match')
    contract_digest = plan.get('contract_committed_sha256', plan.get('contract_sha256'))
    if not plan.get('handoff') or metadata.get('contract_sha256') != contract_digest:
        raise GuardrailError('Metadata has no matching declared handoff')
    contract = git(repo, 'show', source_commit + ':.opencode/worker.json').stdout
    if hashlib.sha256(contract).hexdigest() != contract_digest:
        raise GuardrailError('Committed workflow contract digest does not match')
    if git(repo, 'show', commit + ':.opencode/worker.json').stdout != contract:
        raise GuardrailError('Metadata changed its workflow contract')
    expected = {'Generated-By': 'OpenCode workflow', 'Via': source['provider'],
                'Model-Observed': ', '.join(source['observed_models']),
                'OpenCode-Source-Commit': source_commit, 'Tokens-Total': '0',
                'Model-Calls': '0', 'Cost-Estimate-USD': '0'}
    if any(trailers.get(key) != value for key, value in expected.items()):
        raise GuardrailError('Metadata attribution does not match its source')
    if (metadata.get('schema_version') != 1 or metadata.get('phase') != 'metadata'
            or metadata.get('run_id') != run_id or metadata.get('source_models') != source['observed_models']
            or any(metadata.get(key) != 0 for key in ('model_calls', 'tokens_total', 'estimated_cost_usd'))):
        raise GuardrailError('Invalid deterministic metadata accounting')
    changes = diff_stats(repo, source_commit, commit)
    if changes != metadata.get('changes') or any(
            not path_allowed(item['path'], plan['handoff']['write_paths']) for item in changes['files']):
        raise GuardrailError('Metadata changes do not match the declared scope')
    return commit


def export_stats(base, output_format):
    database = base / 'runs.sqlite3'
    reports = []
    if database.is_file():
        with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
            reports = [json.loads(row[0]) for row in conn.execute('SELECT report_json FROM runs ORDER BY rowid')]
    if output_format == 'json':
        print(json.dumps(reports))
        return
    columns = ['run_id', 'started_at', 'finished_at', 'status', 'phase', 'launcher_version', 'engine', 'provider', 'requested_model',
               'observed_models', 'opencode_version', 'reason_effort', 'elapsed_seconds',
               'tokens_total', 'tokens_input', 'tokens_output', 'tokens_reasoning',
               'tokens_cache_read', 'tokens_cache_write', 'estimated_cost_usd',
               'files_changed', 'insertions', 'deletions', 'commit', 'source_commit',
               'metadata_commit', 'checks_status', 'model_steps', 'metrics_complete',
               'accounting_scope', 'error']
    writer = csv.DictWriter(sys.stdout, fieldnames=columns)
    writer.writeheader()
    for report in reports:
        metrics, changes = report.get('metrics') or {}, report.get('changes') or {}
        row = {k: report.get(k) for k in columns if k in report}
        row['observed_models'] = ', '.join(report.get('observed_models', []))
        row.update({'tokens_' + k: v for k, v in metrics.get('tokens', {}).items()})
        row.update({'estimated_cost_usd': metrics.get('estimated_cost_usd'),
                    'files_changed': len(changes.get('files', [])),
                    'insertions': changes.get('insertions'), 'deletions': changes.get('deletions'),
                    'commit': report.get('git', {}).get('commit'),
                    'source_commit': report.get('git', {}).get('source_commit'),
                    'metadata_commit': (report.get('delivery') or {}).get('metadata_commit'),
                    'checks_status': (report.get('checks') or {}).get('status'),
                    'model_steps': metrics.get('model_steps'),
                    'metrics_complete': metrics.get('completed'),
                    'accounting_scope': metrics.get('accounting_scope')})
        # Prevent task titles/errors or unusual model IDs becoming spreadsheet formulas.
        row = {k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v)
               for k, v in row.items()}
        writer.writerow(row)


def run_job(args, base, credential_reader):
    settings = json.loads((base / 'settings.json').read_text(encoding='utf-8'))
    selection = resolve_selection(settings, args.model)
    model = selection['model']
    repo = Path(git_text(Path(args.dir).resolve(), 'rev-parse', '--show-toplevel'))
    common = Path(git_text(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    run_id = str(uuid.uuid4())
    run_dir = base / 'runs' / run_id
    run_dir.mkdir(parents=True, mode=0o700)
    report = {
        'schema_version': 1, 'run_id': run_id, 'status': 'preflight',
        'launcher_version': '4.0.0', 'execution_started': False, 'exit_code': None,
        'commit_verified': False, 'finalized': False, 'phase': 'preflight',
        'started_at': utc_now(), 'finished_at': None, 'elapsed_seconds': 0,
        'engine': 'OpenCode', 'provider': selection['provider_label'],
        'provider_id': selection['provider_id'], 'launcher_pid': os.getpid(),
        'billing_source': 'provider_managed_unobserved',
        'opencode_version': '', 'requested_model': model, 'observed_models': [],
        'model_evidence': 'unavailable', 'reason_effort': reason_effort(base, model, args.variant),
        'metrics': {}, 'git': {'base_commit': None, 'commit': None, 'parent_repo': str(repo)},
        'changes': {'files': [], 'insertions': 0, 'deletions': 0, 'binary_files': 0},
        'checks': {'status': 'not_verified'}, 'error': None,
        'prompt_sha256': hashlib.sha256(' '.join(args.prompt).encode()).hexdigest(),
        'cost_basis': selection['cost_basis'],
    }
    lock = RepositoryLock(common / 'opencode-worker.lock')
    started = time.monotonic()
    process = None
    monitor = None
    previous_sigterm = None
    try:
        try:
            monitor = ProcessMonitor(
                run_dir, interval_seconds=settings.get('heartbeat_interval_seconds', 5),
                timeout_seconds=settings.get('default_job_timeout_seconds'))
        except ValueError as exc:
            raise GuardrailError(str(exc))
        report['monitoring'] = {
            'kind': 'local_process', 'heartbeat_interval_seconds': monitor.interval_seconds,
            'job_timeout_seconds': monitor.timeout_seconds,
        }
        try:
            previous_sigterm = signal.signal(signal.SIGTERM, interrupt_run)
        except ValueError:
            pass  # Embedded callers outside Python's main thread cannot set signals.
        try:
            lock.acquire()
        except BlockingIOError:
            raise GuardrailError('Another audited OpenCode worker is using this repository')
        if git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
            raise GuardrailError('Repository must be clean; existing work will not be staged or committed')
        base_commit = git_text(repo, 'rev-parse', '--verify', 'HEAD')
        report['git']['base_commit'] = base_commit
        plan = load_project(repo)
        report['project'] = plan
        report['checks'] = {'status': 'not_declared' if not plan['checks'] else 'pending',
                            'source': plan['source'], 'results': []}
        if plan['source'] == 'contract':
            git(repo, 'ls-files', '--error-unmatch', '--', '.opencode/worker.json')
            # A Windows checkout can use CRLF while Git stores LF. Keep the
            # working-file hash for immutability and Git's bytes for provenance.
            contract_bytes = git(repo, 'show', base_commit + ':.opencode/worker.json').stdout
            plan['contract_committed_sha256'] = hashlib.sha256(contract_bytes).hexdigest()
        instructions, report['instructions'] = prepare_instructions(repo, args.dir, run_dir)
        for step in plan['checks'] + ((plan.get('handoff') or {}).get('metadata') or []):
            command_argv(step, repo)
        safe_report_directory(repo)
        git(repo, 'var', 'GIT_AUTHOR_IDENT')
        git(repo, 'var', 'GIT_COMMITTER_IDENT')
        # Check Git ignore policy before paying for a job whose report cannot be committed.
        relative = '.opencode/runs/' + run_id + '.json'
        ignored = git(repo, 'check-ignore', '-q', relative, check=False).returncode
        if ignored == 0:
            raise GuardrailError('Repository ignore rules exclude .opencode/runs; adjust policy before running')
        if ignored != 1:
            raise GuardrailError('Could not verify repository ignore policy')
        try:
            cli = cli_command(settings['cli_binary'])
            version = subprocess.run(cli + ['--version'], capture_output=True,
                                     text=True, check=True, timeout=15).stdout.strip()
        except ValueError as exc:
            raise GuardrailError(str(exc)) from exc
        except (OSError, subprocess.SubprocessError):
            raise GuardrailError('OpenCode version probe failed')
        if not version or '\n' in version:
            raise GuardrailError('Could not verify the OpenCode version')
        report['opencode_version'] = version
        report['status'] = 'running'
        report['phase'] = 'model'
        save_report(base, run_dir, report)
        assert_unchanged(repo, plan)
        check_cancel(run_dir)
        key = (read_key(selection['provider_id']) if credential_reader is read_key else credential_reader())
        if not key:
            raise GuardrailError('Saved provider credential is empty')
        env = child_environment(base, model, key, run_dir, instructions)
        title = ' '.join((args.title or 'delegated coding task').split())[:120]
        prompt = ' '.join(args.prompt) + '\n\nThe local audited launcher owns commits and usage reports. Leave your changes in the working tree; do not commit, push, edit .git, .opencode/runs, or .opencode/worker.json. Applicable project guidance is supplied through explicit instructions. Read any more specific AGENTS.md or CLAUDE.md in directories you edit and follow its scope. Implement the requested task. The launcher will run these declared checks and delivery stages after you finish; do not duplicate them or attempt stages requiring a future commit:\n' + json.dumps({'checks': plan['checks'], 'handoff': plan.get('handoff'), 'write_paths': plan['write_paths']}, ensure_ascii=False) + '\nPrepare any task-specific semantic review needed by the declared metadata commands. If required project steps are missing from this plan, report the conflict instead of inventing success. Summarize the result.'
        command = cli + ['run', '--pure', '--auto', '--model', model,
                   '--dir', str(Path(args.dir).resolve()), '--format', 'json', '--title', title, '--agent', args.agent]
        if args.variant:
            command += ['--variant', args.variant]
        command.append(prompt)
        with (run_dir / 'events.jsonl').open('wb') as out, (run_dir / 'stderr.log').open('wb') as err:
            os.chmod(run_dir / 'events.jsonl', 0o600)
            os.chmod(run_dir / 'stderr.log', 0o600)
            check_cancel(run_dir)
            process = subprocess.Popen(command, stdout=out, stderr=err, env=env,
                                       cwd=str(repo), **process_options())
            report['execution_started'] = True
            try:
                monitor.wait(process)
            except subprocess.TimeoutExpired:
                report['status'] = 'timed_out'
                raise GuardrailError('OpenCode exceeded the job timeout')
        report['exit_code'] = process.returncode
        if process.returncode:
            raise GuardrailError('OpenCode exited with status ' + str(process.returncode))
        if git_text(repo, 'rev-parse', 'HEAD') != base_commit:
            raise GuardrailError('Repository HEAD changed during the worker run; automatic commit refused')
        assert_unchanged(repo, plan)
        enforce_scope(repo, plan['write_paths'])
        report['metrics'] = parse_events(run_dir / 'events.jsonl')
        report['observed_models'] = observed_models(base, report['metrics'].get('session_id'))
        if report['observed_models']:
            report['model_evidence'] = 'opencode_message_db'
        if git(repo, 'status', '--porcelain', '--', '.opencode/runs').stdout:
            raise GuardrailError('Worker modified the reserved audit report directory')
        execute_checks(repo, run_dir, report, plan, 'before_commit')
        assert_unchanged(repo, plan)
        enforce_scope(repo, plan['write_paths'])
        if git_text(repo, 'rev-parse', 'HEAD') != base_commit:
            raise GuardrailError('A check changed HEAD; automatic commit refused')
        report['finished_at'] = utc_now()
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report['status'] = 'ready_to_commit'
        errors = validate_report(report)
        if errors:
            raise GuardrailError('Incomplete run evidence: ' + '; '.join(errors))
        if not git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
            report['status'] = 'no_changes'
        else:
            git(repo, 'add', '-A', '--', '.')
            report['changes'] = diff_stats(repo, base_commit)
            errors = validate_report(report)
            if errors:
                raise GuardrailError('Invalid change evidence: ' + '; '.join(errors))
            manifest = repo / relative
            safe_report_directory(repo)
            manifest.parent.mkdir(parents=True, exist_ok=True)
            # A committed document cannot contain its own commit hash. The central
            # record receives that hash after Git commits; run_id binds both records.
            write_json(manifest, report)
            digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            git(repo, 'add', '--', relative)
            expected_tree = git_text(repo, 'write-tree')
            message = run_dir / 'commit-message.txt'
            message.write_text(commit_message(report, relative, digest, title), encoding='utf-8')
            if git_text(repo, 'rev-parse', 'HEAD') != base_commit:
                raise GuardrailError('Repository HEAD changed before commit')
            check_cancel(run_dir)
            git(repo, 'commit', '--file', str(message))
            commit = git_text(repo, 'rev-parse', 'HEAD')
            report['git']['commit'] = commit
            if git_text(repo, 'show', '-s', '--format=%T', commit) != expected_tree:
                raise GuardrailError('A Git hook changed the committed files; evidence verification failed')
            verify_commit(repo, commit)
            if git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
                raise GuardrailError('Working tree changed during finalization; inspect remaining changes')
            report['status'] = 'committed'
            report['commit_verified'] = True
        report['git']['source_commit'] = report['git']['commit'] or base_commit
        if plan.get('handoff'):
            finalize_metadata(repo, run_dir, report, plan)
        final_revision = git_text(repo, 'rev-parse', 'HEAD')
        execute_checks(repo, run_dir, report, plan, 'after_commit')
        assert_unchanged(repo, plan)
        if git_text(repo, 'rev-parse', 'HEAD') != final_revision or git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
            raise GuardrailError('Final checks changed the committed revision or files; delivery is not verified')
        report['checks']['revision'] = final_revision
        report['phase'] = 'finished'
        report['finalized'] = True
        report['finished_at'] = utc_now()
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report['changes'] = diff_stats(repo, base_commit, final_revision)
        save_report(base, run_dir, report)
        print(json.dumps({'status': report['status'], 'run_id': run_id,
                          'commit': report['git']['commit'], 'report': str(run_dir / 'report.json'),
                          'provider': report['provider'], 'model': report['observed_models'],
                          'elapsed_seconds': report['elapsed_seconds'], 'metrics': report['metrics'],
                          'checks': report['checks'], 'delivery': report.get('delivery')},
                         ensure_ascii=True))
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        report['finalized'] = True
        if report['status'] != 'timed_out':
            report['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        report['error'] = str(exc) if isinstance(exc, (GuardrailError, MetricsError, ProjectError, DeliveryError, CredentialStoreUnavailable, ProviderError, WaitError, MonitorTerminalError)) else type(exc).__name__
        if getattr(exc, 'local_diagnostics', None):
            diagnostic_path = run_dir / 'git-error.log'
            diagnostic_path.write_bytes(exc.local_diagnostics)
            diagnostic_path.chmod(0o600)
        report['finished_at'] = utc_now()
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        if process is not None and process.poll() is None:
            stop_process(process)
        if process is not None:
            report['exit_code'] = process.returncode
            try:
                monitor.record(process, state=report['status'])
            except Exception as heartbeat_error:
                report['heartbeat_error'] = type(heartbeat_error).__name__
        if (run_dir / 'events.jsonl').is_file() and not report['metrics']:
            try:
                report['metrics'] = parse_events(run_dir / 'events.jsonl', allow_partial=True)
                report['observed_models'] = observed_models(base, report['metrics'].get('session_id'))
                if report['observed_models']:
                    report['model_evidence'] = 'opencode_message_db'
            except Exception:
                pass
        try:
            save_report(base, run_dir, report)
        except Exception as storage_error:
            report['persistence_error'] = type(storage_error).__name__
            try:
                write_json(run_dir / 'report.json', report)
            except Exception:
                pass
        print(json.dumps({'status': report['status'], 'run_id': run_id,
                          'persistence_error': report.get('persistence_error'),
                          'error': report['error'], 'commit': report['git']['commit'],
                          'report': str(run_dir / 'report.json')}, ensure_ascii=True), file=sys.stderr)
        return 1
    finally:
        if process is not None and process.poll() is None:
            stop_process(process)
        lock.close()
        if previous_sigterm is not None:
            signal.signal(signal.SIGTERM, previous_sigterm)


def diagnose(base, directory):
    problems = []
    settings_path = base / 'settings.json'
    settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
    if not settings:
        problems.append('Worker is not installed: run the package installer first')
    for executable in ('git',):
        if not shutil.which(executable):
            problems.append('Required executable is missing: ' + executable)
    try:
        cli = cli_command(settings.get('cli_binary') or shutil.which('opencode') or 'opencode')
        version = subprocess.run(cli + ['--version'], capture_output=True, text=True, timeout=15, check=True).stdout.strip()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        version = None
        problems.append('OpenCode is unavailable: install the official OpenCode CLI and rerun doctor')
    project = None
    try:
        repo = Path(git_text(Path(directory).resolve(), 'rev-parse', '--show-toplevel'))
        project = load_project(repo)
        for step in project['checks'] + ((project.get('handoff') or {}).get('metadata') or []):
            command_argv(step, repo)
    except (GuardrailError, ProjectError) as exc:
        problems.append(str(exc))
    return {'status': 'needs_setup' if problems else 'ready', 'problems': problems,
            'opencode_version': version, 'project': project, 'state_directory': str(base),
            'scope': 'Dependency and workflow preflight; no model call or application checks executed'}


def main(argv=None, base=None, credential_reader=read_key):
    argv = list(sys.argv[1:] if argv is None else argv)
    base = Path(base) if base is not None else default_base_dir()
    try:
        from worker_control import execute_control
        result = execute_control(argv, base, credential_reader)
        if result is not None:
            return result
        if argv and argv[0] in ('doctor', 'inspect'):
            parser = argparse.ArgumentParser(prog='openrouter-worker ' + argv[0])
            parser.add_argument('--dir', default=os.getcwd())
            args = parser.parse_args(argv[1:])
            result = diagnose(base, args.dir) if argv[0] == 'doctor' else inspect_project(Path(args.dir).resolve())
            print(json.dumps(result))
            return 1 if result.get('status') == 'needs_setup' else 0
        if argv and argv[0] == 'cancel':
            parser = argparse.ArgumentParser(prog='openrouter-worker cancel')
            parser.add_argument('--run', required=True)
            args = parser.parse_args(argv[1:])
            run_id = str(uuid.UUID(args.run))
            run_dir = base / 'runs' / run_id
            report = json.loads((run_dir / 'report.json').read_text(encoding='utf-8'))
            if report.get('finalized') or report.get('status') in ('failed', 'interrupted', 'timed_out', 'no_changes'):
                raise GuardrailError('This run has already finished')
            write_json(run_dir / 'cancel.request', {'requested_at': utc_now()})
            print(json.dumps({'status': 'cancellation_requested', 'run_id': run_id}))
            return 0
        if argv and argv[0] == 'stats':
            parser = argparse.ArgumentParser(prog='openrouter-worker stats')
            parser.add_argument('--format', choices=['json', 'csv'], default='json')
            args = parser.parse_args(argv[1:])
            export_stats(base, args.format)
            return 0
        if argv and argv[0] == 'verify':
            parser = argparse.ArgumentParser(prog='openrouter-worker verify')
            parser.add_argument('--dir', default=os.getcwd())
            parser.add_argument('--commit', default='HEAD')
            args = parser.parse_args(argv[1:])
            commit = verify_commit(Path(args.dir), args.commit)
            print(json.dumps({'status': 'verified', 'commit': commit}))
            return 0
        parser = argparse.ArgumentParser(description='Run OpenCode with mandatory usage evidence and an attributed local Git commit.')
        if argv and argv[0] == 'run':
            argv.pop(0)
        parser.add_argument('--dir', default=os.getcwd())
        parser.add_argument('--model', '-m')
        parser.add_argument('--title')
        parser.add_argument('--agent', default='build')
        parser.add_argument('--variant')
        parser.add_argument('--format', choices=['json', 'default'], default='json', help='Compatibility flag; raw events are always saved privately.')
        parser.add_argument('prompt', nargs='+')
        args = parser.parse_args(argv)
        return run_job(args, base, credential_reader)
    except (Exception, KeyboardInterrupt) as exc:
        error = str(exc) if isinstance(exc, (GuardrailError, ProjectError, DeliveryError, CredentialStoreUnavailable, ProviderError, WaitError, MonitorTerminalError)) else type(exc).__name__
        print(json.dumps({'status': 'failed', 'error': error}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
