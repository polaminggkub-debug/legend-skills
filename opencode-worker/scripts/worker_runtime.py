"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import argparse
import csv
import datetime
import hashlib
import inspect
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

from worker_metrics import MetricsError, parse_events, validate_report, requires_provider_accounting
from worker_monitor import ProcessMonitor, TerminalOpenCodeError as MonitorTerminalError
from worker_provider import resolve_selection, ProviderError
from worker_wait import WaitError
from worker_platform import (CredentialStoreUnavailable, RepositoryLock, cli_command, default_base_dir,
                             process_options, read_key, stop_process, store_key)
from worker_project import (ProjectError, assert_unchanged, command_argv,
                            inspect_project, load_project, path_allowed)
from worker_delivery import DeliveryError, run_steps
from worker_timing import DiagnosticTimer, RunTimer, summarize_events
from worker_attempt_stats import (aggregate_metrics as _aggregate_metrics,
                                  aggregate_attempt_reports as _aggregate_attempt_reports,
                                  aggregate_timing)
from worker_repairs import (failure_signature, no_progress, repair_prompt,
                            repair_targets)

try:
    from worker_budget import BudgetExceeded, RunBudget, load_limits
except ImportError:  # pragma: no cover - kept for staged installation upgrades.
    BudgetExceeded = None
    RunBudget = None
    load_limits = None

from worker_common import (GuardrailError, utc_now, interrupt_run, write_json, git, git_text, safe_report_directory, save_report, observed_models, prepare_instructions, child_environment, reason_effort, diff_stats, changed_paths, enforce_scope, check_cancel)
from worker_provenance import (provider_trailers, commit_message, verify_commit, verify_metadata_commit)
from worker_workflow import (record_timing, _budget_error, _budget_snapshot, _budget_remaining, _budget_check, _budget_check_before_model, _run_steps_compat, _latest_check_results, _check_status, execute_checks, finalize_metadata, _commit_source)
from worker_job import (_repair_failure, run_job, _check_mutation_guard)


def timing_columns(report):
    timing = report.get('timing') or {}
    phases = timing.get('phases_seconds') or {}
    events = timing.get('events') or {}
    checks = [phases[key] for key in ('before_commit', 'after_commit') if key in phases]
    return {
        'time_preflight_seconds': phases.get('preflight'),
        'time_model_seconds': phases.get('model'),
        'time_checks_seconds': round(sum(checks), 3) if checks else None,
        'time_commit_seconds': phases.get('commit'),
        'time_metadata_seconds': phases.get('metadata'),
        'time_finalize_seconds': phases.get('finalize'),
        'time_tool_execution_seconds': events.get('tool_execution_seconds'),
        'time_non_tool_seconds': events.get('non_tool_seconds'),
        'time_event_coverage': events.get('availability'),
    }

def export_stats(base, output_format):
    database = base / 'runs.sqlite3'
    reports = []
    if database.is_file():
        with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
            reports = [json.loads(row[0]) for row in conn.execute('SELECT report_json FROM runs ORDER BY rowid')]
    if output_format == 'json':
        print(json.dumps(reports))
        return
    columns = ['run_id', 'started_at', 'finished_at', 'status', 'phase', 'launcher_version', 'engine', 'provider',
               'provider_id', 'billing_source', 'cost_basis', 'requested_model',
               'observed_models', 'opencode_version', 'reason_effort', 'elapsed_seconds',
               'tokens_total', 'tokens_input', 'tokens_output', 'tokens_reasoning',
               'tokens_cache_read', 'tokens_cache_write', 'estimated_cost_usd',
               'files_changed', 'insertions', 'deletions', 'commit', 'source_commit',
               'metadata_commit', 'checks_status', 'model_steps', 'metrics_complete',
               'accounting_scope', 'repair_attempts', 'max_repair_attempts',
               'max_model_steps', 'max_wall_seconds', 'stop_reason', 'error'] + list(timing_columns({}))
    writer = csv.DictWriter(sys.stdout, fieldnames=columns)
    writer.writeheader()
    for report in reports:
        metrics, changes = report.get('metrics') or {}, report.get('changes') or {}
        row = {k: report.get(k) for k in columns if k in report}
        row['observed_models'] = ', '.join(report.get('observed_models', []))
        row.update(timing_columns(report))
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
                    'accounting_scope': metrics.get('accounting_scope'),
                    'repair_attempts': (report.get('repairs') or {}).get('attempts'),
                    'max_repair_attempts': (report.get('repairs') or {}).get('max_attempts'),
                    'max_model_steps': (report.get('budget') or {}).get('limits', {}).get('max_model_steps'),
                    'max_wall_seconds': (report.get('budget') or {}).get('limits', {}).get('max_wall_seconds'),
                    'stop_reason': report.get('stop_reason') or (report.get('budget') or {}).get('stop_reason')})
        # Prevent task titles/errors or unusual model IDs becoming spreadsheet formulas.
        row = {k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v)
               for k, v in row.items()}
        writer.writerow(row)

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
        parser.add_argument('--max-model-steps', type=int)
        parser.add_argument('--max-job-seconds', type=float)
        parser.add_argument('--max-repairs', type=int)
        parser.add_argument('--max-tokens', type=int)
        parser.add_argument('--max-cost-usd', type=float)
        parser.add_argument('--check-timeout-seconds', type=float)
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
