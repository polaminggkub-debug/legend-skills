"""Bounded local accounting for one OpenCode model run; reads only."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import time
from collections.abc import Mapping
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

DEFAULT_LIMITS: Dict[str, Any] = {
    "max_model_steps": 100,
    "max_wall_seconds": 3600,
    "max_repair_attempts": 2,
    "check_timeout_seconds": 600,
    "max_repeated_tool_failures": 3,
    "max_tokens": None,
    "max_cost_usd": None,
}
_LIMIT_NAMES = frozenset(DEFAULT_LIMITS)
_TOKEN_FIELDS = ("total", "input", "output", "reasoning", "cache_read", "cache_write")
_IDENTITY_FIELDS = frozenset(("sessionID", "session_id", "sessionId", "messageID", "message_id", "messageId", "stepID", "step_id", "id", "callID", "call_id", "toolID", "tool_id"))
_MAX_EVENT_BYTES = 16 * 1024 * 1024
_HASH_CHUNK_BYTES = 1024 * 1024

def _finite(value: Any, field: str, positive: bool) -> Any:
    adjective = "positive" if positive else "non-negative"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be a finite %s number" % (field, adjective))
    try:
        valid = math.isfinite(float(value)) and (value > 0 if positive else value >= 0)
    except (OverflowError, ValueError):
        valid = False
    if not valid:
        raise ValueError("%s must be a finite %s number" % (field, adjective))
    return value
def _integer(value: Any, field: str, positive: bool) -> int:
    adjective = "positive" if positive else "non-negative"
    if isinstance(value, bool) or not isinstance(value, int) or (value <= 0 if positive else value < 0):
        raise ValueError("%s must be a finite %s integer" % (field, adjective))
    return value
def _validated(values: Mapping[str, Any]) -> Dict[str, Any]:
    unknown = sorted(set(values) - _LIMIT_NAMES)
    if unknown:
        raise ValueError("unknown execution limit: %s" % unknown[0])
    result = dict(DEFAULT_LIMITS)
    result.update(values)
    result["max_model_steps"] = _integer(result["max_model_steps"], "max_model_steps", True)
    result["max_wall_seconds"] = _finite(result["max_wall_seconds"], "max_wall_seconds", True)
    result["max_repair_attempts"] = _integer(result["max_repair_attempts"], "max_repair_attempts", False)
    result["check_timeout_seconds"] = _finite(result["check_timeout_seconds"], "check_timeout_seconds", True)
    result["max_repeated_tool_failures"] = _integer(result["max_repeated_tool_failures"], "max_repeated_tool_failures", True)
    if result["max_tokens"] is not None:
        result["max_tokens"] = _integer(result["max_tokens"], "max_tokens", True)
    if result["max_cost_usd"] is not None:
        result["max_cost_usd"] = _finite(result["max_cost_usd"], "max_cost_usd", True)
    return result
def _nested_limits(settings: Any) -> Mapping[str, Any]:
    if settings is None:
        return {}
    if isinstance(settings, Mapping):
        if "execution_limits" in settings:
            raw = settings.get("execution_limits")
        elif any(key in settings for key in _LIMIT_NAMES):
            raw = settings
        else:
            raw = {}
    else:
        raw = getattr(settings, "execution_limits", {})
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError("execution_limits must be an object")
    return raw
def load_limits(settings: Any, overrides: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Merge and validate ``settings.execution_limits`` and overrides."""
    values = dict(_nested_limits(settings))
    if overrides is not None:
        if not isinstance(overrides, Mapping):
            raise ValueError("overrides must be an object")
        raw = overrides.get("execution_limits") if "execution_limits" in overrides else overrides
        if not isinstance(raw, Mapping):
            raise ValueError("overrides.execution_limits must be an object")
        values.update(raw)
    return _validated(values)
class BudgetExceeded(RuntimeError):
    """A stable, machine-readable reason stopped a run."""
    def __init__(self, reason: str, detail: Optional[str] = None):
        self.reason, self.code = str(reason), str(reason)
        self.detail = None if detail is None else str(detail)
        super().__init__(self.reason if self.detail is None else "%s: %s" % (self.reason, self.detail))
def _clock_value(clock: Any) -> float:
    if not callable(clock):
        clock = getattr(clock, "monotonic", None)
    if not callable(clock):
        raise TypeError("clock must be callable")
    value = clock()
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("clock must return a finite number")
    try:
        value = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("clock must return a finite number") from exc
    if not math.isfinite(value):
        raise ValueError("clock must return a finite number")
    return value
def _reject_duplicate_keys(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result
def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON number")
def _normal_type(value: Any) -> Optional[str]:
    return value.strip().lower().replace("-", "_") if isinstance(value, str) else None
def _containers(event: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    values: List[Mapping[str, Any]] = [event]
    for name in ("part", "data", "properties"):
        nested = event.get(name)
        if isinstance(nested, Mapping) and nested not in values:
            values.append(nested)
    for container in tuple(values):
        state = container.get("state")
        if isinstance(state, Mapping) and state not in values:
            values.append(state)
    return values
def _first(containers: Iterable[Mapping[str, Any]], names: Iterable[str]) -> Any:
    for container in containers:
        for name in names:
            if name in container and container[name] is not None:
                return container[name]
    return None
def _identity(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return str(value)
def _identities_valid(event: Mapping[str, Any]) -> bool:
    for container in _containers(event):
        for name in _IDENTITY_FIELDS:
            if name in container and (not isinstance(container[name], str) or not container[name].strip()):
                return False
    return True
def _event_type(event: Mapping[str, Any]) -> Optional[str]:
    values = [_normal_type(item.get("type")) for item in _containers(event)]
    values = [item for item in values if item]
    for item in values:
        if item in ("step_start", "step_finish"):
            return item
        if item in ("tool", "tool_use", "tooluse"):
            return "tool"
    return values[0] if values else None
def _session(event: Mapping[str, Any], fallback: str) -> str:
    value = _first(_containers(event), ("sessionID", "session_id", "sessionId"))
    return _identity(value) if value is not None else fallback
def _step_key(event: Mapping[str, Any], path_key: str) -> Optional[Tuple[str, str]]:
    if not _identities_valid(event):
        return None
    containers = _containers(event)
    value = _first(containers, ("messageID", "message_id", "messageId"))
    value = value if value is not None else _first(containers, ("stepID", "step_id", "id"))
    session, identity = _session(event, path_key), _identity(value)
    return None if not session or identity is None else (session, identity)
def _tool_key(event: Mapping[str, Any], path_key: str) -> Optional[str]:
    if not _identities_valid(event):
        return None
    value = _first(_containers(event), ("callID", "call_id", "toolID", "tool_id", "id"))
    identity = _identity(value)
    session = _session(event, path_key)
    return None if not session or identity is None else "%s:%s" % (session, identity)
def _number(value: Any) -> Optional[Any]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(float(value)) and value >= 0 else None
    except (OverflowError, ValueError):
        return None
def _token_number(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
def _any_number(value: Any) -> Optional[Any]:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        try:
            value = float(value.strip())
        except (TypeError, ValueError):
            return None
    if not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(float(value)) else None
    except (OverflowError, ValueError):
        return None
def _token_values(event: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    raw = None
    for container in _containers(event):
        for name in ("tokens", "usage", "token_usage", "tokenUsage"):
            if isinstance(container.get(name), Mapping):
                raw = container[name]
                break
        if raw is not None:
            break
    if raw is None:
        return None
    aliases = {
        "total": ("total", "total_tokens", "totalTokens"),
        "input": ("input", "input_tokens", "inputTokens"),
        "output": ("output", "output_tokens", "outputTokens"),
        "reasoning": ("reasoning", "reasoning_tokens", "reasoningTokens"),
    }
    result: Dict[str, Any] = {}
    for field, names in aliases.items():
        value = _first((raw,), names)
        value = _token_number(value)
        if value is None:
            return None
        result[field] = value
    cache = raw.get("cache") if isinstance(raw.get("cache"), Mapping) else raw
    for field, names in (("cache_read", ("read", "cache_read", "cacheRead")),
                         ("cache_write", ("write", "cache_write", "cacheWrite"))):
        value = _first((cache,), names)
        value = _token_number(value)
        if value is None:
            return None
        result[field] = value
    if result["total"] != sum(result[field] for field in _TOKEN_FIELDS[1:]):
        return None
    return result

def _cost_value(event: Mapping[str, Any]) -> Optional[Any]:
    for container in _containers(event):
        for name in ("cost", "cost_usd", "estimated_cost_usd", "estimatedCostUsd"):
            if name in container:
                return _number(container[name])
    return None

def _exit_value(event: Mapping[str, Any]) -> Optional[Any]:
    for container in _containers(event):
        metadata = container.get("metadata")
        if isinstance(metadata, Mapping):
            for name in ("exit", "exit_code", "exitCode"):
                if name in metadata:
                    return _any_number(metadata[name])
    return None

def _tool_status(event: Mapping[str, Any]) -> Optional[str]:
    return _normal_type(_first(_containers(event), ("status",)))

def _tool_name(event: Mapping[str, Any]) -> Optional[str]:
    value = _first(_containers(event), ("tool", "tool_name", "toolName"))
    return None if value is None else str(value)


def _step_signature(event: Mapping[str, Any]) -> str:
    part = event.get("part")
    if isinstance(part, Mapping):
        payload = {key: value for key, value in part.items() if key not in ("id", "timestamp")}
    else:
        payload = {key: value for key, value in event.items() if key not in ("id", "timestamp")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _prefix_digest(path: Path, length: int) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        remaining = length
        while remaining:
            chunk = stream.read(min(_HASH_CHUNK_BYTES, remaining))
            if not chunk:
                raise OSError("event stream ended before its recorded prefix")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()

class RunBudget:
    """Keep one monotonic budget across all invocations in a run."""

    def __init__(self, limits: Mapping[str, Any], clock=time.monotonic):
        if not isinstance(limits, Mapping):
            raise ValueError("limits must be an object")
        self.limits = _validated(dict(limits))
        self._clock = clock if callable(clock) else getattr(clock, "monotonic", None)
        self._started_at = _clock_value(self._clock)
        self._stop_reason: Optional[str] = None
        self._stop_detail: Optional[str] = None
        self._repair_attempts = 0
        self._step_starts: Set[Tuple[str, str]] = set()
        self._step_finishes: Set[Tuple[str, str]] = set()
        self._finish_signatures: Dict[Tuple[str, str], str] = {}
        self._paths: Dict[str, Tuple[int, bytes, Any, str]] = {}
        self._tokens: Dict[str, Any] = {field: 0 for field in _TOKEN_FIELDS}
        self._token_fields: Set[str] = set()
        self._token_total_evidence = False
        self._cost_usd = 0.0
        self._cost_evidence = False
        self._accounting = {"tokens": "pending", "cost_usd": "pending"}
        self._tool_states: Dict[str, Tuple[str, str]] = {}
        self._failure_streak = 0
        self._failure_fingerprint: Optional[str] = None
        self._terminal_step_seen = False

    @property
    def model_steps(self) -> int:
        return len(self._step_starts | self._step_finishes)

    @property
    def completed_model_steps(self) -> int:
        return len(self._step_finishes)

    @property
    def repair_attempts(self) -> int:
        return self._repair_attempts

    def remaining_seconds(self) -> float:
        return max(0.0, self.limits["max_wall_seconds"] - (_clock_value(self._clock) - self._started_at))

    def _raise(self, reason: str, detail: Optional[str] = None) -> None:
        if self._stop_reason is None:
            self._stop_reason, self._stop_detail = reason, detail
        raise BudgetExceeded(self._stop_reason, self._stop_detail)

    def _accounting_failure(self, kind: str, detail: str) -> None:
        self._accounting[kind] = "unavailable"
        cap = self.limits["max_tokens"] if kind == "tokens" else self.limits["max_cost_usd"]
        if cap is not None:
            self._raise("tokens_unavailable" if kind == "tokens" else "cost_unavailable", detail)

    def _stream_failure(self, detail: str) -> None:
        self._accounting["tokens"] = self._accounting["cost_usd"] = "unavailable"
        self._raise("accounting_unavailable", detail)

    def check(self) -> None:
        """Raise the first stable reason whose limit has been reached."""
        if self._stop_reason is not None:
            raise BudgetExceeded(self._stop_reason, self._stop_detail)
        if _clock_value(self._clock) - self._started_at >= self.limits["max_wall_seconds"]:
            self._raise("max_wall_seconds")
        if self.model_steps > self.limits["max_model_steps"]:
            self._raise("max_model_steps")
        if (self.completed_model_steps >= self.limits["max_model_steps"] and
                not (self._terminal_step_seen and self.completed_model_steps == self.limits["max_model_steps"])):
            self._raise("max_model_steps")
        if self.limits["max_tokens"] is not None:
            if self._accounting["tokens"] == "unavailable":
                self._raise("tokens_unavailable", "tokens")
            if self._token_total_evidence and self._tokens["total"] >= self.limits["max_tokens"]:
                self._raise("max_tokens")
        if self.limits["max_cost_usd"] is not None:
            if self._accounting["cost_usd"] == "unavailable":
                self._raise("cost_unavailable", "cost_usd")
            if self._cost_evidence and self._cost_usd >= self.limits["max_cost_usd"]:
                self._raise("max_cost_usd")
        if self._failure_streak >= self.limits["max_repeated_tool_failures"]:
            self._raise("max_repeated_tool_failures")

    def check_before_invocation(self) -> None:
        """Enforce the step cap before launching another invocation."""
        self._terminal_step_seen = False
        if self.model_steps >= self.limits["max_model_steps"]:
            self._raise("max_model_steps")
        self.check()

    def check_before_repair(self, count: int = 1) -> None:
        """Raise before starting repairs that exceed their allowance."""
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("repair attempt count must be a non-negative integer")
        if self._repair_attempts + count > self.limits["max_repair_attempts"]:
            self._raise("max_repair_attempts")
        self.check()

    def record_repair_attempt(self, count: int = 1) -> Dict[str, Any]:
        self.check_before_repair(count)
        self._repair_attempts += count
        return self.snapshot()

    note_repair_attempt = record_repair_attempt

    def _advance_tool(self, tool_id: str, event: Mapping[str, Any]) -> None:
        status, exit_value = _tool_status(event), _exit_value(event)
        failed = status in ("error", "failed", "failure") or (exit_value is not None and exit_value != 0)
        successful = status in ("completed", "complete", "success", "succeeded", "done", "ok") and not failed
        if not failed and not successful:
            return
        relevant: Dict[str, Any] = {"tool": _tool_name(event)}
        for field in ("input", "error", "output"):
            value = _first(_containers(event), (field,))
            if value is not None:
                relevant[field] = value
        if exit_value is not None:
            relevant["exit"] = exit_value
        fingerprint = hashlib.sha256(json.dumps(
            relevant, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")).hexdigest()
        classification = "failure" if failed else "success"
        if self._tool_states.get(tool_id) == (classification, fingerprint):
            return
        self._tool_states[tool_id] = (classification, fingerprint)
        if successful:
            self._failure_streak, self._failure_fingerprint = 0, None
        elif self._failure_fingerprint == fingerprint:
            self._failure_streak += 1
        else:
            self._failure_streak, self._failure_fingerprint = 1, fingerprint

    def _process(self, event: Mapping[str, Any], path_key: str) -> None:
        kind = _event_type(event)
        if kind == "step_start":
            if self._terminal_step_seen:
                self.check_before_invocation()
            key = _step_key(event, path_key)
            if key is None:
                self._stream_failure("step_start_id")
            else:
                self._step_starts.add(key)
        elif kind == "step_finish":
            key = _step_key(event, path_key)
            if key is None:
                self._stream_failure("step_finish_id")
            else:
                signature_key = key
                signature = _step_signature(event)
                previous = self._finish_signatures.get(signature_key)
                if previous is not None and previous != signature:
                    self._stream_failure("conflicting_step_finish")
                self._finish_signatures[signature_key] = signature
            if key is not None and key not in self._step_finishes:
                reason = _first(_containers(event), ("reason",))
                self._terminal_step_seen = isinstance(reason, str) and reason.strip().lower() == "stop"
                token_values = _token_values(event)
                if token_values is None:
                    self._accounting_failure("tokens", "step_finish_tokens")
                else:
                    for field, value in token_values.items():
                        self._tokens[field] += value
                        self._token_fields.add(field)
                    if "total" in token_values:
                        self._token_total_evidence = True
                        if self._accounting["tokens"] == "pending":
                            self._accounting["tokens"] = "available"
                    elif self.limits["max_tokens"] is not None:
                        self._accounting_failure("tokens", "step_finish_total_tokens")
                cost = _cost_value(event)
                if cost is None:
                    self._accounting_failure("cost_usd", "step_finish_cost")
                else:
                    self._cost_usd += cost
                    self._cost_evidence = True
                    if self._accounting["cost_usd"] == "pending":
                        self._accounting["cost_usd"] = "available"
                self._step_finishes.add(key)
        elif kind == "tool":
            key = _tool_key(event, path_key)
            if key is not None:
                self._advance_tool(key, event)

    def observe(self, path: Union[os.PathLike, str]) -> Dict[str, Any]:
        """Read newly complete JSONL records from ``path`` and return a snapshot."""
        self.check()
        event_path = Path(path)
        path_key = os.path.normcase(os.path.abspath(os.fspath(event_path)))
        previous = self._paths.get(path_key)
        try:
            if not event_path.exists():
                if previous is None:
                    return self.snapshot()
                self._stream_failure("event_stream_unavailable")
            if not event_path.is_file():
                self._stream_failure("event_stream_unavailable")
            stat = event_path.stat()
            inode = (getattr(stat, "st_dev", 0), getattr(stat, "st_ino", 0))
            offset, tail = (previous[0], previous[1]) if previous is not None else (0, b"")
            if previous is not None and (stat.st_size < offset or inode != previous[2]):
                self._stream_failure("event_stream_replaced")
            expected_digest = previous[3] if previous is not None else None
            if expected_digest is not None and _prefix_digest(event_path, offset) != expected_digest:
                self._stream_failure("event_stream_changed")
            with event_path.open("rb") as stream:
                stream.seek(offset)
                chunk = stream.read(_MAX_EVENT_BYTES + 1)
            if len(chunk) > _MAX_EVENT_BYTES:
                self._stream_failure("event_stream_too_large")
        except (OSError, ValueError):
            if previous is None and not event_path.exists():
                return self.snapshot()
            self._stream_failure("event_stream_unavailable")
        data = tail + chunk
        lines = data.split(b"\n")
        tail = lines.pop()
        if len(tail) > _MAX_EVENT_BYTES:
            self._stream_failure("partial_event_too_large")
        new_offset = offset + len(chunk)
        self._paths[path_key] = (new_offset, tail, inode, _prefix_digest(event_path, new_offset))
        for raw_line in lines:
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys,
                                   parse_constant=_reject_constant)
            except (UnicodeError, TypeError, ValueError, json.JSONDecodeError):
                self._stream_failure("malformed_event")
            if not isinstance(event, Mapping):
                self._stream_failure("event_not_object")
            self._process(event, path_key)
        self.check()
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        tokens = {field: self._tokens[field] if field in self._token_fields else None for field in _TOKEN_FIELDS}
        return {
            "counts": {
                "model_steps": self.model_steps,
                "completed_model_steps": self.completed_model_steps,
                "repair_attempts": self._repair_attempts,
                "tokens": tokens,
                "cost_usd": self._cost_usd if self._cost_evidence else None,
                "repeated_tool_failures": self._failure_streak,
            },
            "limits": dict(self.limits),
            "stop_reason": self._stop_reason,
            "stop_detail": self._stop_detail,
            "accounting": dict(self._accounting),
        }


__all__ = ["BudgetExceeded", "DEFAULT_LIMITS", "RunBudget", "load_limits"]
