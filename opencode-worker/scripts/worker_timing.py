"""Local phase timing and event-derived diagnostics, without raw event text.

RunTimer is strict; DiagnosticTimer isolates its errors from delivery. Event
durations are supported by timestamps, independently of model/tool success.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple


PHASE_NAMES = (
    "preflight",
    "model",
    "before_commit",
    "commit",
    "metadata",
    "after_commit",
    "finalize",
)

_MAX_EVENT_LINE_BYTES = 16 * 1024 * 1024
_MISSING_EVENT_TIMESTAMPS = "event_timestamps"
_MISSING_TOOL_TIMESTAMPS = "tool_timestamps"


def _clock_value(clock: Any) -> float:
    """Read and validate a clock value without allowing non-finite output."""

    value = clock()
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("clock must return a finite number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("clock must return a finite number") from exc
    if not math.isfinite(result):
        raise ValueError("clock must return a finite number")
    return result


class RunTimer:
    """Accumulate phases starting with preflight; finish freezes idempotently.

    Repeated phases accumulate. Invalid input or a backwards clock raises;
    DiagnosticTimer makes this optional report metadata for the runtime.
    """

    def __init__(self, clock=time.monotonic):
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._clock = clock
        started = _clock_value(clock)
        self._started_at = started
        self._phase_started_at = started
        self._finished_at: Optional[float] = None
        self._active_phase: Optional[str] = "preflight"
        self._phases: Dict[str, float] = {}
        self._frozen: Optional[Dict[str, Any]] = None

    def _duration(self, now: float, earlier: float) -> float:
        duration = now - earlier
        if not math.isfinite(duration) or duration < 0:
            raise RuntimeError("monotonic clock moved backwards")
        return duration

    @staticmethod
    def _phase_name(phase: Any) -> str:
        if not isinstance(phase, str) or not phase.strip():
            raise ValueError("phase must be a non-empty string")
        return phase.strip()

    def _accrue(self, now: float) -> None:
        if self._active_phase is None:
            return
        duration = self._duration(now, self._phase_started_at)
        current = self._phases.get(self._active_phase, 0.0) + duration
        if not math.isfinite(current):
            raise RuntimeError("phase duration is not finite")
        self._phases[self._active_phase] = current

    def _snapshot_at(self, now: float) -> Dict[str, Any]:
        elapsed = self._duration(now, self._started_at)
        phases = dict(self._phases)
        if self._active_phase is not None:
            active_duration = self._duration(now, self._phase_started_at)
            value = phases.get(self._active_phase, 0.0) + active_duration
            if not math.isfinite(value):
                raise RuntimeError("phase duration is not finite")
            phases[self._active_phase] = value
        return {
            "schema_version": 1,
            "elapsed_seconds": elapsed,
            "phases_seconds": phases,
            "active_phase": self._active_phase,
        }

    def start(self, phase: str) -> None:
        """Close the active phase and begin ``phase``."""

        name = self._phase_name(phase)
        if self._frozen is not None:
            raise RuntimeError("timer is already finished")
        now = _clock_value(self._clock)
        self._accrue(now)
        self._active_phase = name
        self._phase_started_at = now

    def snapshot(self) -> Dict[str, Any]:
        """Return a detached current or frozen timing snapshot."""

        if self._frozen is not None:
            return {
                "schema_version": self._frozen["schema_version"],
                "elapsed_seconds": self._frozen["elapsed_seconds"],
                "phases_seconds": dict(self._frozen["phases_seconds"]),
                "active_phase": self._frozen["active_phase"],
            }
        return self._snapshot_at(_clock_value(self._clock))

    def finish(self) -> Dict[str, Any]:
        """Close and freeze the timer; repeated calls are idempotent."""

        if self._frozen is not None:
            return self.snapshot()
        now = _clock_value(self._clock)
        self._accrue(now)
        self._finished_at = now
        self._active_phase = None
        self._phase_started_at = now
        self._frozen = self._snapshot_at(now)
        return self.snapshot()


class DiagnosticTimer:
    """Keep timer failures from changing delivery or hiding failure reports."""

    def __init__(self, factory=RunTimer):
        self._timer, self._error = None, None
        try:
            self._timer = factory()
        except Exception as exc:
            self._error = type(exc).__name__

    def _call(self, method, *args):
        if self._timer is not None:
            try:
                return getattr(self._timer, method)(*args)
            except Exception as exc:
                self._error, self._timer = type(exc).__name__, None
        return {'schema_version': 1, 'availability': 'unavailable',
                'error': self._error, 'elapsed_seconds': None,
                'phases_seconds': {}, 'active_phase': None}

    def start(self, phase):
        self._call('start', phase)

    def snapshot(self):
        return self._call('snapshot')

    def finish(self):
        return self._call('finish')


class _MalformedRecord(ValueError):
    """Internal marker for a record that cannot support timing evidence."""


def _reject_json_constant(value: str) -> None:
    raise _MalformedRecord("non-finite JSON number")


def _reject_duplicate_keys(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _MalformedRecord("duplicate JSON object key")
        result[key] = value
    return result


def _identity(value: str) -> bytes:
    """Return a non-reversible key so IDs are never present in output."""

    return hashlib.sha256(value.encode("utf-8")).digest()


def _number_ms(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        value = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    value /= 1000.0
    return value if math.isfinite(value) else None


def _normalise_kind(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip().lower().replace("-", "_")
    if value in ("tool", "tooluse", "tool_use"):
        return "tool"
    if value in ("step_start", "stepstart"):
        return "step_start"
    if value in ("step_finish", "stepfinish"):
        return "step_finish"
    return value


def _event_part(event: Mapping[str, Any]) -> Mapping[str, Any]:
    part = event.get("part")
    return part if isinstance(part, Mapping) else {}


def _event_kind(event: Mapping[str, Any], part: Mapping[str, Any]) -> str:
    nested = _normalise_kind(part.get("type"))
    if nested in ("tool", "step_start", "step_finish"):
        return nested
    outer = _normalise_kind(event.get("type"))
    if outer in ("tool", "step_start", "step_finish"):
        return outer
    return nested or outer


def _string_id(part: Mapping[str, Any], event: Mapping[str, Any], keys: Iterable[str]) -> Optional[str]:
    for container in (part, event):
        for key in keys:
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


class _IntervalUnion:
    """Maintain sorted, disjoint finite intervals without raw event data."""

    def __init__(self) -> None:
        self._intervals: List[Tuple[float, float]] = []

    def add(self, interval: Tuple[float, float]) -> None:
        start, end = interval
        if end < start:
            raise ValueError("interval end precedes start")
        index = bisect.bisect_left(self._intervals, (start, float("-inf")))
        if index and self._intervals[index - 1][1] >= start:
            index -= 1
        merged_start, merged_end = start, end
        stop = index
        while stop < len(self._intervals) and self._intervals[stop][0] <= merged_end:
            current_start, current_end = self._intervals[stop]
            merged_start = min(merged_start, current_start)
            merged_end = max(merged_end, current_end)
            stop += 1
        self._intervals[index:stop] = [(merged_start, merged_end)]

    def seconds(self) -> float:
        total = math.fsum(end - start for start, end in self._intervals)
        if not math.isfinite(total):
            raise ValueError("interval union is not finite")
        return total


class _EventAccumulator:
    def __init__(self) -> None:
        self.event_count = 0
        self.valid_event_timestamps = 0
        self.missing_event_timestamps = 0
        self.malformed_records = 0
        self.truncated_records = 0
        self.file_error = False
        self.step_starts: Set[bytes] = set()
        self.step_finishes: Set[bytes] = set()
        self.tool_ids: Set[bytes] = set()
        self.tool_intervals: Dict[bytes, Optional[Tuple[float, float]]] = {}
        self.unidentified_tools = 0
        self.event_min: Optional[float] = None
        self.event_max: Optional[float] = None

    def malformed(self, *, truncated: bool = False) -> None:
        self.malformed_records += 1
        if truncated:
            self.truncated_records += 1
        self.missing_event_timestamps += 1

    def _record_timestamp(self, event: Mapping[str, Any], part: Mapping[str, Any]) -> None:
        raw = event.get("timestamp")
        if raw is None and "timestamp" in part:
            raw = part.get("timestamp")
        timestamp = _number_ms(raw)
        if timestamp is None:
            self.missing_event_timestamps += 1
            return
        self.valid_event_timestamps += 1
        self.event_min = timestamp if self.event_min is None else min(self.event_min, timestamp)
        self.event_max = timestamp if self.event_max is None else max(self.event_max, timestamp)

    def _record_tool(self, event: Mapping[str, Any], part: Mapping[str, Any]) -> None:
        tool_id = _string_id(part, event, ("id", "callID", "call_id"))
        if tool_id is None:
            self.unidentified_tools += 1
            return
        key = _identity(tool_id)
        self.tool_ids.add(key)
        if key not in self.tool_intervals:
            self.tool_intervals[key] = None
        state = part.get("state")
        if not isinstance(state, Mapping):
            return
        status = state.get("status")
        if not isinstance(status, str):
            return
        status = status.strip().lower()
        if status not in ("completed", "error", "failed", "cancelled"):
            return
        timing = state.get("time")
        if not isinstance(timing, Mapping):
            return
        start = _number_ms(timing.get("start"))
        end = _number_ms(timing.get("end"))
        if start is None or end is None or end < start:
            return
        if self.tool_intervals[key] is None:
            self.tool_intervals[key] = (start, end)

    def consume(self, raw_line: bytes) -> None:
        if len(raw_line) > _MAX_EVENT_LINE_BYTES:
            self.malformed(truncated=not raw_line.endswith(b"\n"))
            return
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            self.malformed(truncated=not raw_line.endswith(b"\n"))
            return
        if not line.strip():
            self.malformed(truncated=False)
            return
        try:
            event = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_json_constant,
            )
        except (TypeError, ValueError, UnicodeError, RecursionError):
            self.malformed(truncated=not raw_line.endswith(b"\n"))
            return
        if not isinstance(event, Mapping):
            self.malformed(truncated=False)
            return
        self.event_count += 1
        part = _event_part(event)
        self._record_timestamp(event, part)
        kind = _event_kind(event, part)
        if kind == "step_start":
            step_id = _string_id(part, event, ("id", "stepID", "step_id"))
            if step_id is not None:
                self.step_starts.add(_identity(step_id))
        elif kind == "step_finish":
            step_id = _string_id(part, event, ("id", "stepID", "step_id"))
            if step_id is not None:
                self.step_finishes.add(_identity(step_id))
        elif kind == "tool":
            self._record_tool(event, part)

    def _event_coverage(self) -> str:
        if not self.event_count or not self.valid_event_timestamps:
            return "unknown"
        if self.file_error or self.missing_event_timestamps or self.malformed_records:
            return "partial"
        return "complete"

    def _tool_coverage(self) -> str:
        if not self.tool_ids:
            return "complete" if not self.unidentified_tools else "unknown"
        valid = sum(interval is not None for interval in self.tool_intervals.values())
        if valid == 0:
            return "unknown"
        if valid != len(self.tool_ids) or self.unidentified_tools:
            return "partial"
        return "complete"

    def _event_span(self) -> Optional[float]:
        if self.event_min is None or self.event_max is None:
            return None
        span = self.event_max - self.event_min
        return span if math.isfinite(span) and span >= 0 else None

    def _durations(self, event_span: Optional[float], event_coverage: str,
                   tool_coverage: str) -> Tuple[Optional[float], Optional[float]]:
        if event_span is None or event_coverage != "complete":
            return None, None
        intervals = [interval for interval in self.tool_intervals.values() if interval is not None]
        if self.tool_ids and intervals:
            union = _IntervalUnion()
            for interval in intervals:
                start = max(interval[0], self.event_min)
                end = min(interval[1], self.event_max)
                if end >= start:
                    union.add((start, end))
            execution = union.seconds()
            non_tool = event_span - execution if tool_coverage == "complete" else None
            return execution, non_tool
        if not self.tool_ids and not self.unidentified_tools:
            return 0.0, event_span
        return None, None

    def _missing(self, event_coverage: str, tool_coverage: str) -> List[str]:
        missing: List[str] = []
        if event_coverage != "complete":
            missing.append(_MISSING_EVENT_TIMESTAMPS)
        valid_tools = sum(interval is not None for interval in self.tool_intervals.values())
        if ((self.tool_ids or self.unidentified_tools) and tool_coverage != "complete"
                and (tool_coverage == "unknown" or valid_tools < len(self.tool_ids))):
            missing.append(_MISSING_TOOL_TIMESTAMPS)
        if self.unidentified_tools:
            missing.append("tool_ids")
        if self.malformed_records:
            missing.append("event_records")
        if self.file_error or not self.event_count:
            missing.append("events_file")
        return missing

    def result(self) -> Dict[str, Any]:
        event_coverage = self._event_coverage()
        tool_coverage = self._tool_coverage()
        event_span = self._event_span()
        tool_execution, non_tool = self._durations(event_span, event_coverage, tool_coverage)
        missing = self._missing(event_coverage, tool_coverage)
        if event_coverage == "unknown":
            availability = "unavailable"
        elif event_coverage == "partial" or tool_coverage in ("partial", "unknown"):
            availability = "partial"
        else:
            availability = "available"
        model_steps = len(self.step_finishes) or len(self.step_starts)
        return {
            "schema_version": 1,
            "availability": availability,
            "coverage": {
                "event_timestamps": event_coverage,
                "tool_timestamps": tool_coverage,
            },
            "missing": missing,
            "model_steps": model_steps if self.event_count else None,
            "tool_calls": len(self.tool_ids) if self.event_count else None,
            "event_span_seconds": event_span,
            "tool_execution_seconds": tool_execution,
            "non_tool_seconds": non_tool,
        }


def summarize_events(path: Any) -> Dict[str, Any]:
    """Return compact, conservative timing evidence from an event stream.

    Event and tool ``time`` values are interpreted as milliseconds.  A tool
    with a terminal state (``completed``, ``error``, ``failed``, or
    ``cancelled``) and finite ``time.start`` / ``time.end`` contributes a
    measured interval.  Coverage describes timestamp availability, so a
    terminal tool error can still have complete timing coverage.  Tool
    intervals are unioned and clipped to the observed event span, so overlap
    is counted once.  Missing, malformed, legacy, or truncated records produce
    partial or unavailable diagnostics with ``None`` for unsupported durations.
    File and decoding errors are absorbed into the same diagnostic result;
    unexpected caller errors should still be treated as non-fatal report
    metadata.
    """

    accumulator = _EventAccumulator()
    try:
        event_path = Path(path)
        with event_path.open("rb") as stream:
            for raw_line in stream:
                accumulator.consume(raw_line)
    except (OSError, TypeError, ValueError, UnicodeError):
        accumulator.file_error = True
    return accumulator.result()


__all__ = ["PHASE_NAMES", "RunTimer", "DiagnosticTimer", "summarize_events"]
