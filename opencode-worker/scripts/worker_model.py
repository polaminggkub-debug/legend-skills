"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import hashlib
import inspect
import json
import os
from pathlib import (
    Path
)
import subprocess

from worker_metrics import (
    MetricsError,
    parse_events
)
from worker_monitor import (
    ProcessMonitor,
    TerminalOpenCodeError as MonitorTerminalError
)
from worker_platform import (
    cli_command,
    process_options,
    stop_process
)

try:
    from worker_budget import BudgetExceeded, RunBudget, load_limits
except ImportError:  # pragma: no cover - kept for staged installation upgrades.
    BudgetExceeded = None
    RunBudget = None
    load_limits = None

from worker_common import (
    GuardrailError,
    utc_now,
    git,
    observed_models,
    child_environment,
    check_cancel
)
from worker_workflow import (
    _budget_remaining,
    _budget_check,
    _budget_check_before_model
)


def _fingerprint_worktree(repo):
    """Hash all visible source files, including a clean committed tree.

    ``git status`` alone cannot distinguish two clean revisions, so a repair
    attempt compares the full tracked/untracked source snapshot.  Ignored
    build products are omitted by Git's ``--exclude-standard`` rule; audit
    records are always omitted explicitly.
    """

    paths = set()
    for command in (('ls-files', '-z'), ('ls-files', '--others', '--exclude-standard', '-z')):
        raw = git(repo, *command).stdout
        paths.update(os.fsdecode(item) for item in raw.split(b'\0') if item)
    digest = hashlib.sha256()
    for relative in sorted(paths):
        if relative == '.opencode/worker.json' or relative.startswith('.opencode/runs/'):
            continue
        path = repo / relative
        digest.update(relative.encode('utf-8', 'surrogateescape'))
        digest.update(b'\0')
        try:
            if path.is_symlink():
                digest.update(b'link\0' + os.readlink(str(path)).encode('utf-8', 'surrogateescape'))
            elif path.is_file():
                digest.update(b'file\0')
                with path.open('rb') as stream:
                    while True:
                        chunk = stream.read(1024 * 1024)
                        if not chunk:
                            break
                        digest.update(chunk)
            else:
                digest.update(b'missing-or-other')
        except (OSError, UnicodeError):
            digest.update(b'unavailable')
        digest.update(b'\0')
    return digest.hexdigest()

def _prepare_model_logs(run_dir, attempt_dir):
    """Keep each invocation's telemetry separate without filesystem hard links."""
    attempt_dir.mkdir(parents=True, exist_ok=True)
    for name in ('events.jsonl', 'stderr.log'):
        path = attempt_dir / name
        with path.open('wb'):
            pass
        path.chmod(0o600)

def _budget_poll(state, budget):
    path = state.get('events_path') if isinstance(state, dict) else None
    if path is not None:
        budget.observe(path)
    else:
        _budget_check(budget)

def _monitor_for_job(run_dir, settings, budget, budget_state):
    kwargs = {
        'interval_seconds': settings.get('heartbeat_interval_seconds', 5),
        'timeout_seconds': settings.get('default_job_timeout_seconds'),
    }
    try:
        parameters = inspect.signature(ProcessMonitor).parameters
    except (TypeError, ValueError):
        raise GuardrailError('ProcessMonitor signature could not be verified')
    if 'guard' not in parameters:
        raise GuardrailError('ProcessMonitor does not support the shared budget guard')
    kwargs['cancel_path'] = run_dir / 'cancel.request'
    kwargs['launcher_pid'] = os.getpid()
    kwargs['guard'] = lambda: _budget_poll(budget_state, budget)
    return ProcessMonitor(run_dir, **kwargs)

class _ModelAttemptFailure(GuardrailError):
    """Failure from the model process; never treated as a check repair."""

    def __init__(self, message, *, reason='model_failure'):
        super().__init__(message)
        self.reason = reason

def _run_model_attempt(args, *, base, repo, run_dir, attempt_dir, report, model,
                       key, instructions, prompt, title, monitor, budget, timer,
                       budget_state):
    """Run one isolated OpenCode invocation and return strict telemetry."""

    _budget_check_before_model(budget)
    _prepare_model_logs(run_dir, attempt_dir)
    events_path = attempt_dir / 'events.jsonl'
    stderr_path = attempt_dir / 'stderr.log'
    env = child_environment(base, model, key, attempt_dir, instructions)
    env['OPENCODE_WORKER_ATTEMPT'] = str(len(report.get('attempts') or []) + 1)
    cli = cli_command(json.loads((base / 'settings.json').read_text(encoding='utf-8'))['cli_binary'])
    command = cli + ['run', '--pure', '--auto', '--model', model,
                     '--dir', str(Path(args.dir).resolve()), '--format', 'json',
                     '--title', title, '--agent', args.agent]
    if args.variant:
        command += ['--variant', args.variant]
    command.append(prompt)
    attempt_number = len(report.get('attempts') or []) + 1
    attempt_report = {
        'attempt': attempt_number, 'phase': report.get('phase', 'model'),
        'events_path': str(events_path), 'stderr_path': str(stderr_path),
        'status': 'running', 'started_at': utc_now(), 'finished_at': None,
        'metrics': {}, 'observed_models': [],
        'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
    }
    report.setdefault('attempts', []).append(attempt_report)
    process = None
    attempt_exception = None
    old_timeout = getattr(monitor, 'timeout_seconds', None)
    try:
        budget_state['events_path'] = events_path
        monitor.output_dir = attempt_dir
        remaining = _budget_remaining(budget)
        configured = old_timeout
        if remaining is not None and configured is not None:
            configured = min(configured, remaining)
            if hasattr(monitor, 'timeout_seconds'):
                monitor.timeout_seconds = configured
        timer.start('model')
        with events_path.open('wb') as out, stderr_path.open('wb') as err:
            events_path.chmod(0o600)
            stderr_path.chmod(0o600)
            check_cancel(run_dir)
            process = subprocess.Popen(command, stdout=out, stderr=err, env=env,
                                       cwd=str(repo), **process_options())
            report['execution_started'] = True
            try:
                monitor.wait(process)
            except subprocess.TimeoutExpired as exc:
                attempt_report['status'] = 'timed_out'
                attempt_report['error'] = 'OpenCode exceeded the job timeout'
                report['status'] = 'timed_out'
                raise _ModelAttemptFailure(attempt_report['error'], reason='timed_out') from exc
            except MonitorTerminalError as exc:
                attempt_report['status'] = 'failed'
                attempt_report['error'] = str(exc)
                raise _ModelAttemptFailure(str(exc), reason='terminal_model_error') from exc
        code = process.returncode
        try:
            metrics = parse_events(events_path, allow_partial=(code != 0))
        except MetricsError as exc:
            attempt_report['status'] = 'failed'
            attempt_report['error'] = str(exc)
            raise _ModelAttemptFailure('OpenCode telemetry was not usable', reason='metrics_failure') from exc
        attempt_report['metrics'] = metrics
        attempt_report['observed_models'] = observed_models(base, metrics.get('session_id'))
        attempt_report['exit_code'] = code
        if attempt_report['observed_models']:
            attempt_report['model_evidence'] = 'opencode_message_db'
        try:
            budget.observe(events_path)
        except Exception as exc:
            # A completed invocation is still usable when it exactly reaches a
            # model/token/cost ceiling; the guard prevents a subsequent launch.
            reason = getattr(exc, 'reason', None)
            if reason in ('max_model_steps', 'max_tokens', 'max_cost_usd'):
                report.setdefault('budget', {})['stop_reason'] = reason
            else:
                attempt_report['status'] = 'failed'
                attempt_report['error'] = str(exc)
                raise
        if code:
            attempt_report['status'] = 'failed'
            attempt_report['error'] = 'OpenCode exited with status ' + str(code)
            raise _ModelAttemptFailure(attempt_report['error'], reason='model_exit')
        attempt_report['status'] = 'completed'
        return metrics
    except BaseException as exc:
        attempt_exception = exc
        if attempt_report.get('status') == 'running':
            attempt_report['status'] = 'failed'
            attempt_report['error'] = str(exc)
        raise
    finally:
        attempt_report['finished_at'] = utc_now()
        if process is not None and process.poll() is None:
            stop_process(process)
        if not attempt_report['metrics'] and process is not None:
            try:
                attempt_report['metrics'] = parse_events(events_path, allow_partial=True)
                attempt_report['observed_models'] = observed_models(base, attempt_report['metrics'].get('session_id'))
            except (MetricsError, OSError):
                attempt_report['accounting_unavailable'] = True
        if process is not None and attempt_report.get('status') != 'completed':
            try:
                state = 'interrupted' if isinstance(attempt_exception, KeyboardInterrupt) else attempt_report.get('status', 'failed')
                monitor.record(process, state=state)
            except Exception:
                pass
        if hasattr(monitor, 'timeout_seconds'):
            monitor.timeout_seconds = old_timeout
        budget_state['events_path'] = None

def _ensure_model_evidence(report):
    """Reject a successful-looking invocation without exact model evidence."""

    observed = report.get('observed_models')
    if not isinstance(observed, list) or not observed:
        raise GuardrailError('OpenCode model attribution evidence is unavailable')
    if set(observed) != {report.get('requested_model')}:
        raise GuardrailError('OpenCode observed model does not match the requested model')
    metrics = report.get('metrics') or {}
    if metrics.get('completed') is not True or not metrics.get('session_id'):
        raise GuardrailError('OpenCode telemetry did not complete with usable accounting')
