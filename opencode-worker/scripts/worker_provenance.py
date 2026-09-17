"""Local, audited OpenCode execution. Python 3.9+, standard library only."""
import hashlib
import json
import uuid

from worker_metrics import (
    validate_report,
    requires_provider_accounting
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

from worker_common import (
    GuardrailError,
    git,
    git_text,
    diff_stats
)


def provider_trailers(report):
    if not requires_provider_accounting(report):
        return {}
    return {'Provider-ID': report['provider_id'], 'Billing-Source': report['billing_source'],
            'Cost-Basis': report['cost_basis']}

def commit_message(report, relative_path, digest, title):
    tokens = report['metrics']['tokens']
    return '\n'.join([
        'chore(opencode): ' + title,
        '',
        'Generated-By: OpenCode',
        'Via: ' + report['provider'],
        *[key + ': ' + value for key, value in provider_trailers(report).items()],
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
    expected.update(provider_trailers(report))
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
    expected.update(provider_trailers(source))
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
