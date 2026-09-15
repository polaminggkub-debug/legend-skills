"""Strict, local parsing of OpenCode JSONL run telemetry.

The worker uses this module at the attribution boundary.  It deliberately
accepts only the fields needed for usage accounting and keeps error values to
names, so a report cannot accidentally include a tool payload or prompt text.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class MetricsError(ValueError):
    """Raised when an event stream cannot support trustworthy accounting."""


_TOKEN_KEYS = ("total", "input", "output", "reasoning", "cache_read", "cache_write")
_REPORT_METRIC_KEYS = (
    "session_id",
    "model_steps",
    "tokens",
    "estimated_cost_usd",
    "event_counts",
    "tool_counts",
    "errors",
    "completed",
    "telemetry_errors",
)
_REPORT_KEYS = (
    "schema_version",
    "run_id",
    "status",
    "started_at",
    "finished_at",
    "elapsed_seconds",
    "engine",
    "provider",
    "opencode_version",
    "requested_model",
    "observed_models",
    "model_evidence",
    "reason_effort",
    "metrics",
    "git",
    "changes",
    "checks",
    "error",
)


def _reject_json_constant(value: str) -> None:
    raise MetricsError("non-finite JSON number: %s" % value)


def _no_duplicate_object_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MetricsError("duplicate JSON object key: %s" % key)
        result[key] = value
    return result


def _normalise_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MetricsError("event type must be a non-empty string")
    normalised = value.strip().lower().replace("-", "_")
    if normalised in ("tool", "tooluse", "tool_use"):
        return "tool_use"
    return normalised


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MetricsError("%s must be a non-empty string" % field)
    return value


def _number(value: Any, field: str, *, nonnegative: bool = True) -> Any:
    """Validate a JSON number while preserving integer values in aggregates."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MetricsError("%s must be numeric" % field)
    if isinstance(value, float) and not math.isfinite(value):
        raise MetricsError("%s must be finite" % field)
    if nonnegative and value < 0:
        raise MetricsError("%s must be non-negative" % field)
    return value


def _sum_numbers(values: Iterable[Any], field: str) -> Any:
    numbers = list(values)
    if not numbers:
        return 0
    try:
        if all(isinstance(value, int) and not isinstance(value, bool) for value in numbers):
            result: Any = sum(numbers)
        else:
            result = math.fsum(float(value) for value in numbers)
    except (OverflowError, ValueError):
        raise MetricsError("%s aggregate must be finite" % field)
    if isinstance(result, float) and not math.isfinite(result):
        raise MetricsError("%s aggregate must be finite" % field)
    return result


def _numbers_equal(left: Any, right: Any) -> bool:
    if isinstance(left, int) and not isinstance(left, bool) and isinstance(right, int) and not isinstance(right, bool):
        return left == right
    try:
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-9)
    except (OverflowError, ValueError):
        return False


def _session_id(event: Mapping[str, Any], part: Mapping[str, Any]) -> str:
    top = event.get("sessionID", event.get("session_id"))
    nested = part.get("sessionID", part.get("session_id"))
    if top is None and nested is None:
        raise MetricsError("event is missing session ID")
    if top is not None and nested is not None and top != nested:
        raise MetricsError("event session IDs conflict")
    value = top if top is not None else nested
    return _require_nonempty_string(value, "session ID")


def _part_type(event: Mapping[str, Any], part: Mapping[str, Any]) -> str:
    top_value = event.get("type")
    nested_value = part.get("type")
    if top_value is None and nested_value is None:
        raise MetricsError("event is missing type")
    if top_value is not None and nested_value is not None:
        top_type = _normalise_type(top_value)
        nested_type = _normalise_type(nested_value)
        if top_type != nested_type:
            raise MetricsError("event and part types conflict")
        return nested_type
    return _normalise_type(nested_value if nested_value is not None else top_value)


def _step_id(part: Mapping[str, Any], event: Mapping[str, Any], event_type: str) -> str:
    value = part.get("id", event.get("id"))
    return _require_nonempty_string(value, "%s step ID" % event_type)


def _step_tokens(part: Mapping[str, Any], step_id: str) -> Dict[str, Any]:
    raw = part.get("tokens")
    if not isinstance(raw, Mapping):
        raise MetricsError("step %s is missing tokens" % step_id)

    values: Dict[str, Any] = {}
    for key in ("total", "input", "output", "reasoning"):
        if key not in raw:
            raise MetricsError("step %s is missing tokens.%s" % (step_id, key))
        values[key] = _number(raw[key], "step %s tokens.%s" % (step_id, key))

    cache = raw.get("cache")
    if not isinstance(cache, Mapping):
        raise MetricsError("step %s is missing tokens.cache" % step_id)
    for cache_key, output_key in (("read", "cache_read"), ("write", "cache_write")):
        if cache_key not in cache:
            raise MetricsError("step %s is missing tokens.cache.%s" % (step_id, cache_key))
        values[output_key] = _number(
            cache[cache_key], "step %s tokens.cache.%s" % (step_id, cache_key)
        )

    expected_total = _sum_numbers((values[key] for key in _TOKEN_KEYS if key != "total"), "step tokens")
    if not _numbers_equal(values["total"], expected_total):
        raise MetricsError("step %s tokens.total does not equal component sum" % step_id)
    return values


def _error_name(part: Mapping[str, Any], event: Mapping[str, Any], event_type: str) -> str:
    """Return a stable error name without retaining arbitrary error payloads."""

    candidates: List[Any] = []
    for container in (part, event):
        if "name" in container:
            candidates.append(container.get("name"))
        value = container.get("error")
        if isinstance(value, Mapping):
            candidates.extend((value.get("name"), value.get("type"), value.get("code")))
        elif isinstance(value, str):
            # A string under ``error`` may be a message; keep only a generic
            # event name in that case.
            candidates.append(None)
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return event_type


def _telemetry_name(part: Mapping[str, Any], event: Mapping[str, Any], event_type: str) -> Optional[str]:
    for container in (part, event):
        for key in ("telemetry_error", "telemetryError"):
            if key not in container:
                continue
            value = container[key]
            if isinstance(value, Mapping):
                for name_key in ("name", "type", "code"):
                    name = value.get(name_key)
                    if isinstance(name, str) and name.strip():
                        return name.strip()
            elif isinstance(value, str) and value.strip():
                return value.strip()
            return event_type
    return None


def _canonical_part(part: Mapping[str, Any]) -> str:
    try:
        return json.dumps(part, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError):
        raise MetricsError("step payload is not JSON serialisable")


def parse_events(path: Path, *, allow_partial: bool = False) -> Dict[str, Any]:
    """Parse and aggregate a strict OpenCode JSONL event stream.

    Duplicate ``step-start`` or ``step-finish`` records with the same ID are
    ignored only when their nested payloads are identical.  A second payload
    with different accounting data is rejected as a conflicting duplicate.
    """

    event_path = Path(path)
    try:
        raw = event_path.read_bytes()
        if allow_partial and raw and not raw.endswith(b'\n'):
            prefix, separator, last = raw.rpartition(b'\n')
            try:
                json.loads(last)
            except (ValueError, UnicodeError):
                raw = prefix if separator else b''
        lines = raw.decode('utf-8').splitlines()
    except (OSError, UnicodeError) as exc:
        raise MetricsError("unable to read events file: %s" % event_path) from exc

    session: Optional[str] = None
    event_counts: Dict[str, int] = {}
    tool_counts: Dict[str, int] = {}
    errors: List[str] = []
    telemetry_errors: List[str] = []
    seen_errors = set()
    seen_telemetry_errors = set()
    step_payloads: Dict[Tuple[str, str], str] = {}
    finished_steps: List[Tuple[str, str, Dict[str, Any], Any]] = []

    if not lines:
        raise MetricsError("events file is empty")

    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            raise MetricsError("malformed JSON at line %d" % line_number)
        try:
            event = json.loads(
                line,
                object_pairs_hook=_no_duplicate_object_keys,
                parse_constant=_reject_json_constant,
            )
        except MetricsError:
            raise
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MetricsError("malformed JSON at line %d" % line_number) from exc
        if not isinstance(event, Mapping):
            raise MetricsError("event at line %d must be a JSON object" % line_number)

        part = event.get("part")
        if not isinstance(part, Mapping):
            raise MetricsError("event at line %d is missing part object" % line_number)
        current_session = _session_id(event, part)
        if session is None:
            session = current_session
        elif current_session != session:
            raise MetricsError("multiple session IDs in events file")
        event_type = _part_type(event, part)

        is_step = event_type in ("step_start", "step_finish")
        step_key: Optional[Tuple[str, str]] = None
        if is_step:
            step_key = (event_type, _step_id(part, event, event_type))
            signature = _canonical_part(part)
            previous = step_payloads.get(step_key)
            if previous is not None:
                if previous != signature:
                    raise MetricsError("conflicting duplicate %s" % step_key[1])
                # Duplicate records do not contribute to accounting or counts.
                continue
            step_payloads[step_key] = signature

        event_counts[event_type] = event_counts.get(event_type, 0) + 1

        if event_type == "step_finish":
            reason = part.get("reason")
            reason = _require_nonempty_string(reason, "step finish reason")
            tokens = _step_tokens(part, step_key[1] if step_key is not None else "")
            if "cost" not in part:
                raise MetricsError("step %s is missing cost" % (step_key[1] if step_key else ""))
            cost = _number(part["cost"], "step cost")
            finished_steps.append((step_key[1] if step_key else "", reason, tokens, cost))
        elif event_type == "tool_use":
            tool = part.get("tool")
            if isinstance(tool, str) and tool.strip():
                tool_name = tool.strip()
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            else:
                telemetry_name = "tool_name_missing"
                if telemetry_name not in seen_telemetry_errors:
                    telemetry_errors.append(telemetry_name)
                    seen_telemetry_errors.add(telemetry_name)

        if "error" in part or "error" in event or "error" in event_type:
            if event_type not in ("telemetry_error", "telemetryerror") and "telemetry" not in event_type:
                name = _error_name(part, event, event_type)
                if name not in seen_errors:
                    errors.append(name)
                    seen_errors.add(name)
        if "telemetry" in event_type:
            name = _error_name(part, event, event_type)
            if name not in seen_telemetry_errors:
                telemetry_errors.append(name)
                seen_telemetry_errors.add(name)
        explicit_telemetry_name = _telemetry_name(part, event, event_type)
        if explicit_telemetry_name is not None and explicit_telemetry_name not in seen_telemetry_errors:
            telemetry_errors.append(explicit_telemetry_name)
            seen_telemetry_errors.add(explicit_telemetry_name)

    if session is None:
        raise MetricsError("events file contains no session")
    if not finished_steps:
        raise MetricsError("events file is missing step-finish terminal step")
    if not allow_partial and finished_steps[-1][1].strip().lower() != "stop":
        raise MetricsError("events file is missing terminal step-finish reason stop")

    totals: Dict[str, Any] = {}
    for key in _TOKEN_KEYS:
        totals[key] = _sum_numbers((step[2][key] for step in finished_steps), "tokens.%s" % key)
    total_cost = _sum_numbers((step[3] for step in finished_steps), "estimated_cost_usd")
    if isinstance(total_cost, int):
        total_cost = float(total_cost)

    return {
        "session_id": session,
        "model_steps": len(finished_steps),
        "tokens": totals,
        "estimated_cost_usd": total_cost,
        "event_counts": event_counts,
        "tool_counts": tool_counts,
        "errors": errors,
        "completed": not allow_partial,
        "accounting_scope": "partial_completed_steps" if allow_partial else "completed_run",
        "telemetry_errors": telemetry_errors,
    }


def _record_error(errors: List[str], message: str) -> None:
    errors.append(message)


def _check_mapping(report: Any, field: str, errors: List[str]) -> Optional[Mapping[str, Any]]:
    value = report.get(field) if isinstance(report, Mapping) else None
    if not isinstance(value, Mapping):
        _record_error(errors, "missing or invalid report field: %s" % field)
        return None
    return value


def _check_string(report: Mapping[str, Any], field: str, errors: List[str], *, allow_empty: bool = False) -> None:
    value = report.get(field)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        _record_error(errors, "missing or invalid report field: %s" % field)


def _validate_metrics(metrics: Mapping[str, Any], errors: List[str]) -> None:
    for field in _REPORT_METRIC_KEYS:
        if field not in metrics:
            _record_error(errors, "missing metrics field: %s" % field)

    session_id = metrics.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        _record_error(errors, "metrics.session_id must be a non-empty string")

    model_steps = metrics.get("model_steps")
    if isinstance(model_steps, bool) or not isinstance(model_steps, int) or model_steps < 1:
        _record_error(errors, "metrics.model_steps must be a positive integer")

    tokens = metrics.get("tokens")
    if not isinstance(tokens, Mapping):
        _record_error(errors, "missing or invalid metrics field: tokens")
    else:
        valid_token_values = True
        for key in _TOKEN_KEYS:
            if key not in tokens:
                _record_error(errors, "missing metrics.tokens field: %s" % key)
                valid_token_values = False
            else:
                try:
                    _number(tokens[key], "metrics.tokens.%s" % key)
                except MetricsError as exc:
                    _record_error(errors, str(exc))
                    valid_token_values = False
        if valid_token_values:
            expected = _sum_numbers((tokens[key] for key in _TOKEN_KEYS if key != "total"), "metrics.tokens")
            if not _numbers_equal(tokens["total"], expected):
                _record_error(errors, "metrics.tokens.total does not equal component sum")

    if "estimated_cost_usd" not in metrics:
        _record_error(errors, "missing metrics field: estimated_cost_usd")
    else:
        try:
            _number(metrics["estimated_cost_usd"], "metrics.estimated_cost_usd")
        except MetricsError as exc:
            _record_error(errors, str(exc))

    event_counts = metrics.get("event_counts")
    if not isinstance(event_counts, Mapping):
        _record_error(errors, "metrics.event_counts must be an object")
    else:
        _validate_count_map(event_counts, "metrics.event_counts", errors)

    tool_counts = metrics.get("tool_counts")
    if not isinstance(tool_counts, Mapping):
        _record_error(errors, "metrics.tool_counts must be an object")
    else:
        _validate_count_map(tool_counts, "metrics.tool_counts", errors)

    for field in ("errors", "telemetry_errors"):
        values = metrics.get(field)
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
            _record_error(errors, "metrics.%s must be a list of names" % field)

    if not isinstance(metrics.get("completed"), bool):
        _record_error(errors, "metrics.completed must be boolean")


def _validate_count_map(value: Mapping[str, Any], field: str, errors: List[str]) -> None:
    for key, count in value.items():
        if not isinstance(key, str) or not key.strip():
            _record_error(errors, "%s keys must be non-empty strings" % field)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            _record_error(errors, "%s values must be non-negative integers" % field)


def validate_report(report: Mapping[str, Any]) -> List[str]:
    """Return human-readable validation failures for a worker report.

    The validator is intentionally side-effect free.  It checks the model
    attribution evidence required before a commit and permits a null
    ``git.commit`` for the ``ready_to_commit`` pre-commit state.
    """

    errors: List[str] = []
    if not isinstance(report, Mapping):
        return ["report must be an object"]

    for field in _REPORT_KEYS:
        if field not in report:
            _record_error(errors, "missing report field: %s" % field)

    schema_version = report.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != 1:
        _record_error(errors, "schema_version must be 1")

    for field in ("run_id", "status", "started_at", "opencode_version"):
        _check_string(report, field, errors)
    if report.get("finished_at") is not None and not isinstance(report.get("finished_at"), str):
        _record_error(errors, "finished_at must be a string or null")

    try:
        _number(report.get("elapsed_seconds"), "elapsed_seconds")
    except MetricsError as exc:
        _record_error(errors, str(exc))

    if report.get("engine") != "OpenCode":
        _record_error(errors, "engine must be OpenCode")
    if report.get("provider") != "OpenRouter":
        _record_error(errors, "provider must be OpenRouter")

    requested_model = report.get("requested_model")
    if not isinstance(requested_model, str) or not requested_model.startswith("openrouter/"):
        _record_error(errors, "requested_model must use the openrouter/ prefix")

    observed_models = report.get("observed_models")
    status = report.get("status")
    failure_status = isinstance(status, str) and status.lower() in ("failed", "error", "failure", "timed_out", "interrupted")
    if not isinstance(observed_models, list) or any(not isinstance(item, str) or not item.strip() for item in observed_models):
        _record_error(errors, "observed_models must be a list of names")
    elif not observed_models and not failure_status:
        _record_error(errors, "observed_models must contain actual model evidence")
    elif observed_models:
        if any(not item.startswith("openrouter/") for item in observed_models):
            _record_error(errors, "observed_models must use the openrouter/ prefix")
        if isinstance(requested_model, str) and set(observed_models) != {requested_model}:
            _record_error(errors, "observed_models must match requested_model exactly")
        if len(set(observed_models)) != len(observed_models):
            _record_error(errors, "observed_models must not contain duplicates")

    model_evidence = report.get("model_evidence")
    if not isinstance(model_evidence, str):
        _record_error(errors, "model_evidence must be a string")
    elif model_evidence != "opencode_message_db" and not (failure_status and not model_evidence.strip()):
        _record_error(errors, "model_evidence must be opencode_message_db")

    reason_effort = report.get("reason_effort")
    if reason_effort is not None and (not isinstance(reason_effort, str) or not reason_effort.strip()):
        _record_error(errors, "reason_effort must be a string or null")

    metrics = _check_mapping(report, "metrics", errors)
    if metrics is not None:
        _validate_metrics(metrics, errors)
        if not failure_status and metrics.get("completed") is not True:
            _record_error(errors, "metrics.completed must be true for a successful report")
        if not failure_status:
            for field in ("errors", "telemetry_errors"):
                values = metrics.get(field)
                if isinstance(values, list) and values:
                    _record_error(errors, "metrics.%s must be empty for a successful report" % field)

    git = _check_mapping(report, "git", errors)
    if git is not None:
        for field in ("base_commit", "parent_repo"):
            if not isinstance(git.get(field), str) or not git.get(field, "").strip():
                _record_error(errors, "git.%s must be a non-empty string" % field)
        commit = git.get("commit")
        if commit is not None and (not isinstance(commit, str) or not commit.strip()):
            _record_error(errors, "git.commit must be a string or null")
        if status == "committed" and not isinstance(commit, str):
            _record_error(errors, "git.commit is required for committed report")

    changes = _check_mapping(report, "changes", errors)
    if changes is not None:
        files = changes.get("files")
        if not isinstance(files, list):
            _record_error(errors, "changes.files must be a list")
        else:
            for item in files:
                if isinstance(item, str):
                    if not item.strip():
                        _record_error(errors, "changes.files names must be non-empty strings")
                    continue
                if not isinstance(item, Mapping):
                    _record_error(errors, "changes.files entries must be objects")
                    continue
                if not isinstance(item.get("path"), str) or not item.get("path", "").strip():
                    _record_error(errors, "changes.files.path must be a non-empty string")
                for stat_field in ("insertions", "deletions"):
                    stat_value = item.get(stat_field)
                    if stat_value is not None and (
                        isinstance(stat_value, bool) or not isinstance(stat_value, int) or stat_value < 0
                    ):
                        _record_error(errors, "changes.files.%s must be a non-negative integer or null" % stat_field)
        binary_files = changes.get("binary_files")
        if isinstance(binary_files, bool) or not isinstance(binary_files, (int, list)):
            _record_error(errors, "changes.binary_files must be a non-negative count or list")
        elif isinstance(binary_files, int) and binary_files < 0:
            _record_error(errors, "changes.binary_files must be a non-negative count")
        elif isinstance(binary_files, list) and any(not isinstance(item, str) or not item.strip() for item in binary_files):
            _record_error(errors, "changes.binary_files list must contain names")
        for field in ("insertions", "deletions"):
            value = changes.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                _record_error(errors, "changes.%s must be a non-negative integer" % field)

    checks = _check_mapping(report, "checks", errors)
    if checks is not None and (not isinstance(checks.get("status"), str) or not checks.get("status", "").strip()):
        _record_error(errors, "checks.status must be a non-empty string")

    if "error" in report and report.get("error") is not None and not isinstance(report.get("error"), (str, Mapping)):
        _record_error(errors, "error must be null, a string, or an object")

    return errors


__all__ = ["MetricsError", "parse_events", "validate_report"]
