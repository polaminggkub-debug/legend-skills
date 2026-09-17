"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import hashlib
import json
from pathlib import (
    Path
)
import time

from worker_metrics import (
    validate_report
)
from worker_project import (
    assert_unchanged
)
from worker_delivery import (
    run_steps
)
from worker_timing import (
    summarize_events
)
from worker_attempt_stats import (
    aggregate_metrics as _aggregate_metrics,
    aggregate_timing
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
    write_json,
    git,
    git_text,
    safe_report_directory,
    save_report,
    diff_stats,
    changed_paths,
    enforce_scope,
    check_cancel
)
from worker_provenance import (
    provider_trailers,
    commit_message,
    verify_commit
)


def record_timing(report, timer, run_dir, *, final=False, events=False):
    """Add diagnostic timing without changing success or billing evidence."""
    event_summary = (report.get('timing') or {}).get('events')
    if events or (final and event_summary is None):
        try:
            paths = [Path(a['events_path']) for a in report.get('attempts', [])]
            event_summary = aggregate_timing([summarize_events(path) for path in paths]) if paths else summarize_events(run_dir / 'events.jsonl')
        except Exception as exc:
            event_summary = {'availability': 'unavailable', 'error': type(exc).__name__}
    report['timing'] = timer.finish() if final else timer.snapshot()
    if event_summary is not None:
        report['timing']['events'] = event_summary

def _budget_error(exc):
    """Return whether *exc* is the shared run-budget stop signal."""

    return BudgetExceeded is not None and isinstance(exc, BudgetExceeded)

def _budget_snapshot(budget):
    if budget is None:
        return None
    try:
        return budget.snapshot()
    except Exception as exc:
        return {'availability': 'unavailable', 'error': type(exc).__name__}

def _budget_remaining(budget):
    if budget is None:
        return None
    try:
        value = budget.remaining_seconds()
    except Exception as exc:
        raise GuardrailError('Shared execution budget could not be read') from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise GuardrailError('Shared execution budget returned an invalid remaining time')
    return value

def _budget_check(budget):
    if budget is None:
        return
    budget.check()

def _budget_check_before_model(budget):
    if budget is None:
        return
    method = getattr(budget, 'check_before_invocation', None)
    if not callable(method):
        raise GuardrailError('Shared execution budget lacks invocation guard')
    method()

def _run_steps_compat(steps, *, repo, run_dir, stage, env=None, budget=None,
                      check_timeout_seconds=None):
    """Run delivery with the shared guard and whole-job timeout seam."""

    if budget is None:
        raise GuardrailError('A shared execution budget is required for delivery checks')
    return run_steps(
        steps, repo=repo, run_dir=run_dir, stage=stage, env=env,
        guard=lambda: _budget_check(budget),
        default_timeout_seconds=check_timeout_seconds,
        remaining_seconds=lambda: _budget_remaining(budget),
    )

def _latest_check_results(results):
    latest = {}
    for result in results:
        if isinstance(result, dict) and result.get('id') is not None:
            latest[result['id']] = result
    return latest

def _check_status(report, plan):
    """Compute status from the latest result per declared check.

    Historical failed attempts remain in the report for auditability, while a
    later passing rerun is allowed to make the current workflow pass.
    """

    if not plan['checks']:
        return 'not_declared'
    latest = _latest_check_results(report['checks']['results'])
    if any(step['id'] not in latest for step in plan['checks']):
        return 'pending'
    if any(result.get('status') != 'passed' for result in latest.values()):
        return 'passed_with_warnings'
    return 'passed'

def execute_checks(repo, run_dir, report, plan, stage, timer=None, *,
                   budget=None, attempt=None, report_base=None,
                   check_timeout_seconds=None):
    check_cancel(run_dir)
    steps = [step for step in plan['checks'] if step['stage'] == stage]
    report['phase'] = stage
    if timer is not None:
        timer.start(stage)
        record_timing(report, timer, run_dir)
    report_dir = run_dir
    if report_base is not None:
        report_dir = Path(report_base) / 'runs' / report['run_id']
    save_report(report_base or run_dir.parent.parent, report_dir, report)
    try:
        results = _run_steps_compat(
            steps, repo=repo, run_dir=run_dir, stage=stage, budget=budget,
            check_timeout_seconds=check_timeout_seconds,
        )
    except BaseException as exc:
        failed_results = (getattr(exc, 'results', []) or
                          getattr(exc, 'delivery_results', []) or [])
        for result in failed_results:
            if attempt is not None and isinstance(result, dict):
                result.setdefault('attempt', attempt)
        report['checks']['results'].extend(failed_results)
        report['checks']['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        raise
    for result in results:
        if attempt is not None and isinstance(result, dict):
            result.setdefault('attempt', attempt)
    report['checks']['results'].extend(results)
    report['checks']['status'] = _check_status(report, plan)
    if attempt is not None:
        report['checks'].setdefault('attempts', []).append({
            'attempt': attempt, 'stage': stage, 'results': results,
            'status': ('failed' if any(item.get('status') != 'passed' for item in results)
                       else ('not_declared' if not results else 'passed')),
        })
    return results

def finalize_metadata(repo, run_dir, report, plan, timer=None, *, budget=None,
                      check_timeout_seconds=None):
    check_cancel(run_dir)
    source_commit = report['git']['source_commit']
    if not report['git']['commit']:
        raise GuardrailError('Metadata handoff requires an attributed source change; worker made no changes')
    report['phase'] = 'metadata'
    if timer is not None:
        timer.start('metadata')
        record_timing(report, timer, run_dir)
    report['delivery'] = {'status': 'pending', 'source_commit': source_commit, 'metadata_commit': None, 'results': []}
    save_report(run_dir.parent.parent, run_dir, report)
    try:
        results = _run_steps_compat(
            plan['handoff']['metadata'], repo=repo, run_dir=run_dir, stage='metadata',
            env={'WORKER_SOURCE_COMMIT': source_commit,
                 'WORKER_RUN_ID': report['run_id'], 'WORKER_REPO_ROOT': str(repo)},
            budget=budget, check_timeout_seconds=check_timeout_seconds,
        )
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
        *[key + ': ' + value for key, value in provider_trailers(report).items()],
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

def _commit_source(repo, run_dir, report, *, base_commit, relative, title, timer, budget,
                   started_clock, cycle_metrics=None, cycle_observed_models=None):
    """Commit the current source cycle while preserving report invariants."""

    _budget_check(budget)
    timer.start('commit')
    assert_unchanged(repo, report['project'])
    enforce_scope(repo, report['project']['write_paths'])
    if git_text(repo, 'rev-parse', 'HEAD') != base_commit:
        raise GuardrailError('A check changed HEAD; automatic commit refused')
    if not git(repo, 'status', '--porcelain', '--untracked-files=all').stdout:
        report['status'] = 'committed' if report['git'].get('commit') else 'no_changes'
        report['git']['source_commit'] = base_commit
        return base_commit
    report.pop('_started_clock', None)
    report['git']['base_commit'] = base_commit
    report['git']['commit'] = None
    git(repo, 'add', '-A', '--', '.')
    report['changes'] = diff_stats(repo, base_commit)
    report['finished_at'] = utc_now()
    report['elapsed_seconds'] = round(time.monotonic() - started_clock, 3)
    report['status'] = 'ready_to_commit'
    record_timing(report, timer, run_dir)
    manifest_report = json.loads(json.dumps(report))
    manifest_report['git']['base_commit'] = base_commit
    manifest_report['git']['commit'] = None
    manifest_report['git']['source_commit'] = None  # This commit does not exist yet.
    manifest_report['git']['previous_source_commits'] = manifest_report['git'].pop('source_commits', [])
    if manifest_report.get('delivery'):
        manifest_report['previous_delivery'] = manifest_report.pop('delivery')
    if cycle_metrics:
        manifest_report['metrics'] = _aggregate_metrics(cycle_metrics)
    if cycle_observed_models:
        manifest_report['observed_models'] = sorted(set(cycle_observed_models))
        manifest_report['model_evidence'] = 'opencode_message_db'
    errors = validate_report(manifest_report)
    if errors:
        raise GuardrailError('Invalid change evidence: ' + '; '.join(errors))
    safe_report_directory(repo)
    manifest = repo / relative
    manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(manifest, manifest_report)
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    git(repo, 'add', '--', relative)
    expected_tree = git_text(repo, 'write-tree')
    message = run_dir / ('commit-message-' + base_commit[:12] + '.txt')
    message.write_text(commit_message(manifest_report, relative, digest, title), encoding='utf-8')
    check_cancel(run_dir)
    git(repo, 'commit', '--file', str(message))
    commit = git_text(repo, 'rev-parse', 'HEAD')
    report['git']['commit'] = commit
    if git_text(repo, 'show', '-s', '--format=%T', commit) != expected_tree:
        raise GuardrailError('A Git hook changed the committed files; evidence verification failed')
    verify_commit(repo, commit)
    report['commit_verified'] = True
    report['git'].setdefault('source_commits', []).append(commit)
    report['git']['source_commit'] = commit
    report['status'] = 'committed'
    return commit
