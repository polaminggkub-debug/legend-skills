"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import datetime
import hashlib
import json
import os
from pathlib import (
    Path
)
import sqlite3
import subprocess
from contextlib import (
    closing
)

from worker_provider import (
    resolve_selection
)
from worker_project import (
    path_allowed
)

try:
    from worker_budget import BudgetExceeded, RunBudget, load_limits
except ImportError:  # pragma: no cover - kept for staged installation upgrades.
    BudgetExceeded = None
    RunBudget = None
    load_limits = None



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
