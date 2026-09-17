"""Usage and timing aggregation across sequential model attempts."""

def aggregate_metrics(metrics_list):
    """Aggregate complete/partial telemetry once across all model attempts."""

    if not metrics_list:
        return {}
    token_keys = ('total', 'input', 'output', 'reasoning', 'cache_read', 'cache_write')
    tokens = {key: 0 for key in token_keys}
    event_counts, tool_counts = {}, {}
    errors, telemetry_errors, sessions = [], [], []
    completed = True
    model_steps = 0
    cost = 0.0
    for metrics in metrics_list:
        if not isinstance(metrics, dict):
            continue
        session = metrics.get('session_id')
        if isinstance(session, str) and session and session not in sessions:
            sessions.append(session)
        model_steps += int(metrics.get('model_steps') or 0)
        completed = completed and metrics.get('completed') is True
        for key in token_keys:
            value = (metrics.get('tokens') or {}).get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                tokens[key] += value
        value = metrics.get('estimated_cost_usd')
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            cost += value
        for source, target in ((metrics.get('event_counts') or {}, event_counts),
                               (metrics.get('tool_counts') or {}, tool_counts)):
            for key, count in source.items():
                if isinstance(key, str) and isinstance(count, int) and not isinstance(count, bool):
                    target[key] = target.get(key, 0) + count
        for source, target in ((metrics.get('errors') or [], errors),
                               (metrics.get('telemetry_errors') or [], telemetry_errors)):
            for value in source:
                if isinstance(value, str) and value not in target:
                    target.append(value)
    if not sessions:
        return {}
    if isinstance(cost, int):
        cost = float(cost)
    return {
        'session_id': sessions[-1], 'session_ids': sessions,
        'model_steps': model_steps, 'tokens': tokens,
        'estimated_cost_usd': cost, 'event_counts': event_counts,
        'tool_counts': tool_counts, 'errors': errors,
        'completed': completed, 'accounting_scope': ('completed_run' if completed else 'partial_completed_steps'),
        'telemetry_errors': telemetry_errors,
    }


def aggregate_attempt_reports(attempts):
    """Aggregate available telemetry and retain an incomplete-attempt marker."""

    metrics = aggregate_metrics([
        attempt.get('metrics') for attempt in attempts
        if isinstance(attempt, dict) and isinstance(attempt.get('metrics'), dict)
        and attempt.get('metrics')
    ])
    if metrics and any(attempt.get('status') != 'completed'
                       for attempt in attempts if isinstance(attempt, dict)):
        metrics['completed'] = False
        metrics['accounting_scope'] = 'partial_completed_steps'
    return metrics


def aggregate_timing(summaries):
    """Sum disjoint attempt intervals; unknown durations remain unknown."""
    if len(summaries) == 1:
        return summaries[0]
    fields = ('model_steps', 'tool_calls', 'event_span_seconds',
              'tool_execution_seconds', 'non_tool_seconds')
    result = {'schema_version': 1, 'attempt_count': len(summaries),
              'availability': 'available', 'coverage': {}, 'missing': []}
    for field in fields:
        values = [item.get(field) for item in summaries]
        result[field] = sum(values) if values and all(value is not None for value in values) else None
    for field in ('event_timestamps', 'tool_timestamps'):
        values = [(item.get('coverage') or {}).get(field, 'unknown') for item in summaries]
        result['coverage'][field] = 'complete' if all(value == 'complete' for value in values) else 'partial'
    result['missing'] = sorted({key for item in summaries for key in item.get('missing', [])})
    if any(item.get('availability') != 'available' for item in summaries):
        result['availability'] = 'partial' if any(item.get('availability') != 'unavailable' for item in summaries) else 'unavailable'
    return result
