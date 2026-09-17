"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import hashlib
import json
import os
from pathlib import (
    Path
)
import signal
import subprocess
import sys
import time
import uuid

from worker_metrics import (
    MetricsError
)
from worker_monitor import (
    TerminalOpenCodeError as MonitorTerminalError
)
from worker_provider import (
    resolve_selection,
    ProviderError
)
from worker_wait import (
    WaitError
)
from worker_platform import (
    CredentialStoreUnavailable,
    RepositoryLock,
    cli_command,
    read_key,
    stop_process
)
from worker_project import (
    ProjectError,
    assert_unchanged,
    command_argv,
    load_project
)
from worker_delivery import (
    DeliveryError
)
from worker_timing import (
    DiagnosticTimer,
    RunTimer
)
from worker_attempt_stats import (
    aggregate_metrics as _aggregate_metrics,
    aggregate_attempt_reports as _aggregate_attempt_reports
)
from worker_repairs import (
    failure_signature,
    no_progress,
    repair_prompt,
    repair_targets
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
    interrupt_run,
    write_json,
    git,
    git_text,
    safe_report_directory,
    save_report,
    prepare_instructions,
    reason_effort,
    diff_stats,
    enforce_scope,
    check_cancel
)
from worker_workflow import (
    record_timing,
    _budget_snapshot,
    _budget_check,
    _budget_check_before_model,
    execute_checks,
    finalize_metadata,
    _commit_source
)
from worker_model import (
    _fingerprint_worktree,
    _monitor_for_job,
    _run_model_attempt,
    _ensure_model_evidence
)


def _repair_failure(report, *, stage, results, repo, budget, max_repairs,
                    original_prompt, previous_signature, previous_tree):
    """Record an eligible check failure and return the next model prompt."""

    targets = repair_targets(results)
    if not targets:
        raise DeliveryError('required delivery check failed', results)
    signature = failure_signature(targets)
    tree = _fingerprint_worktree(repo)
    if no_progress(previous_signature, previous_tree, signature, tree):
        report.setdefault('repairs', {})['stop_reason'] = 'no_progress'
        report['stop_reason'] = 'no_progress'
        raise GuardrailError('Automatic repair stopped: no progress after the same failed check')
    repairs = report.setdefault('repairs', {})
    used = int(repairs.get('attempts', 0))
    if used >= max_repairs:
        repairs['stop_reason'] = 'max_repair_attempts'
        report['stop_reason'] = 'max_repair_attempts'
        raise GuardrailError('Automatic repair limit reached')
    try:
        _budget_check_before_model(budget)
        budget.record_repair_attempt()
    except Exception as exc:
        reason = getattr(exc, 'reason', 'max_repair_attempts')
        repairs['stop_reason'] = reason
        report['stop_reason'] = reason
        raise
    used += 1
    repairs['attempts'] = used
    entry = {
        'attempt': used, 'stage': stage,
        'checks': [target.identifier for target in targets],
        'failure_signature': signature, 'tree_fingerprint': tree,
        'action': 'model_feedback',
    }
    repairs.setdefault('history', []).append(entry)
    return repair_prompt(
        original_prompt, targets, attempt=used,
        remaining_attempts=max(0, max_repairs - used),
    ), signature, tree

def run_job(args, base, credential_reader):
    """Run OpenCode with one shared budget and bounded check repair cycles."""

    settings = json.loads((base / 'settings.json').read_text(encoding='utf-8'))
    selection = resolve_selection(settings, args.model)
    model = selection['model']
    repo = Path(git_text(Path(args.dir).resolve(), 'rev-parse', '--show-toplevel'))
    common = Path(git_text(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    run_id = str(uuid.uuid4())
    run_dir = base / 'runs' / run_id
    run_dir.mkdir(parents=True, mode=0o700)
    limits_override = {}
    for argument, field in (
        ('max_model_steps', 'max_model_steps'), ('max_job_seconds', 'max_wall_seconds'),
        ('max_repairs', 'max_repair_attempts'), ('max_tokens', 'max_tokens'),
        ('max_cost_usd', 'max_cost_usd'), ('check_timeout_seconds', 'check_timeout_seconds'),
    ):
        value = getattr(args, argument, None)
        if value is not None:
            limits_override[field] = value
    if load_limits is None or RunBudget is None:
        raise GuardrailError('Shared execution budget is unavailable; reinstall the worker')
    limits = load_limits(settings, limits_override)
    budget = RunBudget(limits)
    report = {
        'schema_version': 1, 'run_id': run_id, 'status': 'preflight',
        'launcher_version': '4.2.0', 'execution_started': False, 'exit_code': None,
        'commit_verified': False, 'finalized': False, 'phase': 'preflight',
        'started_at': utc_now(), 'finished_at': None, 'elapsed_seconds': 0,
        'engine': 'OpenCode', 'provider': selection['provider_label'],
        'provider_id': selection['provider_id'], 'launcher_pid': os.getpid(),
        'billing_source': 'provider_managed_unobserved', 'opencode_version': '',
        'requested_model': model, 'observed_models': [], 'model_evidence': 'unavailable',
        'reason_effort': reason_effort(base, model, args.variant), 'metrics': {},
        'git': {'base_commit': None, 'commit': None, 'parent_repo': str(repo),
                'job_base_commit': None, 'source_commit': None, 'source_commits': []},
        'changes': {'files': [], 'insertions': 0, 'deletions': 0, 'binary_files': 0},
        'checks': {'status': 'not_verified', 'results': [], 'attempts': []},
        'repairs': {'attempts': 0, 'max_attempts': limits['max_repair_attempts'],
                    'history': [], 'stop_reason': None},
        'budget': _budget_snapshot(budget), 'error': None,
        'prompt_sha256': hashlib.sha256(' '.join(args.prompt).encode()).hexdigest(),
        'cost_basis': selection['cost_basis'], 'attempts': [],
    }
    lock = RepositoryLock(common / 'opencode-worker.lock')
    started = time.monotonic()
    timer = DiagnosticTimer(factory=RunTimer)
    process = None
    monitor = None
    budget_state = {'events_path': None}
    previous_sigterm = None
    model_metrics = []
    cycle_model_metrics = []
    cycle_observed_models = []
    previous_failure_signature = None
    previous_failure_tree = None
    title = ' '.join((args.title or 'delegated coding task').split())[:120]
    try:
        record_timing(report, timer, run_dir)
        save_report(base, run_dir, report)
        try:
            monitor = _monitor_for_job(run_dir, settings, budget, budget_state)
        except (TypeError, ValueError) as exc:
            raise GuardrailError(str(exc)) from exc
        report['monitoring'] = {
            'kind': 'local_process', 'heartbeat_interval_seconds': monitor.interval_seconds,
            'job_timeout_seconds': monitor.timeout_seconds,
            'total_budget_seconds': limits['max_wall_seconds'],
        }
        try:
            previous_sigterm = signal.signal(signal.SIGTERM, interrupt_run)
        except ValueError:
            pass
        try:
            lock.acquire()
        except BlockingIOError:
            raise GuardrailError('Another audited OpenCode worker is using this repository')
        if git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
            raise GuardrailError('Repository must be clean; existing work will not be staged or committed')
        base_commit = git_text(repo, 'rev-parse', '--verify', 'HEAD')
        report['git']['base_commit'] = base_commit
        report['git']['job_base_commit'] = base_commit
        plan = load_project(repo)
        report['project'] = plan
        report['checks'] = {'status': 'not_declared' if not plan['checks'] else 'pending',
                            'source': plan['source'], 'results': [], 'attempts': []}
        if plan['source'] == 'contract':
            git(repo, 'ls-files', '--error-unmatch', '--', '.opencode/worker.json')
            contract_bytes = git(repo, 'show', base_commit + ':.opencode/worker.json').stdout
            plan['contract_committed_sha256'] = hashlib.sha256(contract_bytes).hexdigest()
        instructions, report['instructions'] = prepare_instructions(repo, args.dir, run_dir)
        for step in plan['checks'] + ((plan.get('handoff') or {}).get('metadata') or []):
            command_argv(step, repo)
        safe_report_directory(repo)
        git(repo, 'var', 'GIT_AUTHOR_IDENT')
        git(repo, 'var', 'GIT_COMMITTER_IDENT')
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
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            raise GuardrailError('OpenCode version probe failed') from exc
        if not version or '\n' in version:
            raise GuardrailError('Could not verify the OpenCode version')
        report['opencode_version'] = version
        report['status'] = 'running'
        report['phase'] = 'model'
        record_timing(report, timer, run_dir)
        save_report(base, run_dir, report)
        assert_unchanged(repo, plan)
        check_cancel(run_dir)
        key = (read_key(selection['provider_id']) if credential_reader is read_key else credential_reader())
        if not key:
            raise GuardrailError('Saved provider credential is empty')
        original_prompt = ' '.join(args.prompt)
        base_prompt = original_prompt + (
            '\n\nThe local audited launcher owns commits and usage reports. Leave your changes in the '
            'working tree; do not commit, push, edit .git, .opencode/runs, or .opencode/worker.json. '
            'Applicable project guidance is supplied through explicit instructions. Read any more '
            'specific AGENTS.md or CLAUDE.md in directories you edit and follow its scope. '
            'Implement the requested task. The launcher will run these declared checks and delivery '
            'stages after you finish; do not duplicate them or attempt stages requiring a future commit:\n' +
            json.dumps({'checks': plan['checks'], 'handoff': plan.get('handoff'),
                        'write_paths': plan['write_paths']}, ensure_ascii=False) +
            '\nPrepare any task-specific semantic review needed by the declared metadata commands. '
            'If required project steps are missing from this plan, report the conflict instead of '
            'inventing success. Summarize the result.'
        )
        cycle_base = base_commit
        prompt = base_prompt
        metadata_done = False
        while True:
            report['phase'] = 'model'
            _budget_check_before_model(budget)
            attempt_dir = run_dir / 'attempts' / ('attempt-%03d' % (len(report['attempts']) + 1))
            metrics = _run_model_attempt(
                args, base=base, repo=repo, run_dir=run_dir, attempt_dir=attempt_dir,
                report=report, model=model, key=key, instructions=instructions,
                prompt=prompt, title=title, monitor=monitor, budget=budget, timer=timer,
                budget_state=budget_state,
            )
            model_metrics.append(metrics)
            cycle_model_metrics.append(metrics)
            cycle_observed_models.extend(report['attempts'][-1].get('observed_models', []))
            report['metrics'] = _aggregate_metrics(model_metrics)
            report['observed_models'] = sorted({item for attempt in report['attempts']
                                                for item in attempt.get('observed_models', [])})
            if report['observed_models']:
                report['model_evidence'] = 'opencode_message_db'
            _ensure_model_evidence(report)
            report['budget'] = _budget_snapshot(budget)
            if git_text(repo, 'rev-parse', 'HEAD') != cycle_base:
                raise GuardrailError('Repository HEAD changed during the worker run; automatic commit refused')
            assert_unchanged(repo, plan)
            enforce_scope(repo, plan['write_paths'])
            tree_before_checks = _fingerprint_worktree(repo)
            try:
                execute_checks(repo, run_dir,
                               report, plan, 'before_commit', timer, budget=budget,
                               attempt=len(report['attempts']), report_base=base,
                               check_timeout_seconds=limits['check_timeout_seconds'])
            except DeliveryError as exc:
                results = getattr(exc, 'results', []) or getattr(exc, 'delivery_results', [])
                _check_mutation_guard(repo, plan, cycle_base, tree_before_checks)
                prompt, previous_failure_signature, previous_failure_tree = _repair_failure(
                    report, stage='before_commit', results=results, repo=repo, budget=budget,
                    max_repairs=limits['max_repair_attempts'], original_prompt=base_prompt,
                    previous_signature=previous_failure_signature, previous_tree=previous_failure_tree,
                )
                continue
            _check_mutation_guard(repo, plan, cycle_base, tree_before_checks)
            report['git']['base_commit'] = cycle_base
            source_commit_before = git_text(repo, 'rev-parse', 'HEAD')
            source_commit = _commit_source(
                repo, run_dir, report, base_commit=cycle_base, relative=relative,
                title=title, timer=timer, budget=budget, started_clock=started,
                cycle_metrics=cycle_model_metrics,
                cycle_observed_models=cycle_observed_models,
            )
            if source_commit != source_commit_before:
                cycle_base = source_commit
                cycle_model_metrics = []
                cycle_observed_models = []
            report['git']['source_commit'] = source_commit
            if plan.get('handoff') and (source_commit != source_commit_before or not metadata_done):
                finalize_metadata(repo, run_dir, report, plan, timer, budget=budget,
                                  check_timeout_seconds=limits['check_timeout_seconds'])
                metadata_done = True
                cycle_base = git_text(repo, 'rev-parse', 'HEAD')
            final_revision = git_text(repo, 'rev-parse', 'HEAD')
            tree_before_after = _fingerprint_worktree(repo)
            try:
                execute_checks(repo, run_dir,
                               report, plan, 'after_commit', timer, budget=budget,
                               attempt=len(report['attempts']), report_base=base,
                               check_timeout_seconds=limits['check_timeout_seconds'])
            except DeliveryError as exc:
                results = getattr(exc, 'results', []) or getattr(exc, 'delivery_results', [])
                _check_mutation_guard(repo, plan, final_revision, tree_before_after)
                cycle_base = final_revision
                prompt, previous_failure_signature, previous_failure_tree = _repair_failure(
                    report, stage='after_commit', results=results, repo=repo, budget=budget,
                    max_repairs=limits['max_repair_attempts'], original_prompt=base_prompt,
                    previous_signature=previous_failure_signature, previous_tree=previous_failure_tree,
                )
                continue
            _check_mutation_guard(repo, plan, final_revision, tree_before_after)
            _budget_check(budget)
            timer.start('finalize')
            report['checks']['revision'] = final_revision
            report['phase'] = 'finished'
            report['finalized'] = True
            report['finished_at'] = utc_now()
            report['elapsed_seconds'] = round(time.monotonic() - started, 3)
            report['changes'] = diff_stats(repo, report['git']['job_base_commit'], final_revision)
            record_timing(report, timer, run_dir, final=True)
            if report['timing']['elapsed_seconds'] is not None:
                report['elapsed_seconds'] = report['timing']['elapsed_seconds']
            report['finished_at'] = utc_now()
            report['budget'] = _budget_snapshot(budget)
            report.pop('_started_clock', None)
            save_report(base, run_dir, report)
            print(json.dumps({'status': report['status'], 'run_id': run_id,
                              'commit': report['git']['commit'], 'report': str(run_dir / 'report.json'),
                              'provider': report['provider'], 'model': report['observed_models'],
                              'elapsed_seconds': report['elapsed_seconds'], 'metrics': report['metrics'],
                              'checks': report['checks'], 'delivery': report.get('delivery'),
                              'repairs': report['repairs'], 'budget': report['budget'],
                              'timing': report['timing']}, ensure_ascii=True))
            return 0
    except (Exception, KeyboardInterrupt) as exc:
        report['finalized'] = True
        if report['status'] != 'timed_out':
            report['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        reason = getattr(exc, 'reason', None)
        if reason:
            report['stop_reason'] = reason
            report.setdefault('repairs', {})['stop_reason'] = reason
        report['error'] = str(exc) if isinstance(exc, (GuardrailError, MetricsError, ProjectError, DeliveryError,
                                                        CredentialStoreUnavailable, ProviderError, WaitError,
                                                        MonitorTerminalError, BudgetExceeded)) else type(exc).__name__
        if getattr(exc, 'local_diagnostics', None):
            diagnostic_path = run_dir / 'git-error.log'
            diagnostic_path.write_bytes(exc.local_diagnostics)
            diagnostic_path.chmod(0o600)
        if process is not None and process.poll() is None:
            stop_process(process)
        if timer.snapshot()['active_phase'] is not None:
            timer.start('finalize')
        available_metrics = _aggregate_attempt_reports(report.get('attempts') or [])
        if available_metrics:
            report['metrics'] = available_metrics
            report['observed_models'] = sorted({item for attempt in report['attempts']
                                                for item in attempt.get('observed_models', [])})
            if report['observed_models']:
                report['model_evidence'] = 'opencode_message_db'
        report['budget'] = _budget_snapshot(budget)
        report['finished_at'] = utc_now()
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report.pop('_started_clock', None)
        record_timing(report, timer, run_dir, final=True, events=True)
        if report['timing']['elapsed_seconds'] is not None:
            report['elapsed_seconds'] = report['timing']['elapsed_seconds']
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
                          'repairs': report.get('repairs'), 'budget': report.get('budget'),
                          'stop_reason': report.get('stop_reason'),
                          'report': str(run_dir / 'report.json'), 'timing': report['timing']}, ensure_ascii=True), file=sys.stderr)
        return 1
    finally:
        if process is not None and process.poll() is None:
            stop_process(process)
        lock.close()
        if previous_sigterm is not None:
            signal.signal(signal.SIGTERM, previous_sigterm)

def _check_mutation_guard(repo, plan, expected_head, expected_tree):
    """A declared check must observe the source, not alter it."""

    assert_unchanged(repo, plan)
    enforce_scope(repo, plan['write_paths'])
    if git_text(repo, 'rev-parse', 'HEAD') != expected_head:
        raise GuardrailError('Declared check changed HEAD; automatic repair refused')
    if _fingerprint_worktree(repo) != expected_tree:
        raise GuardrailError('Declared check modified the worktree; automatic repair refused')
