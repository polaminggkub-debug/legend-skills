"""Quiet, local waiting for an already launched OpenCode worker run.

The worker process owns the model loop and writes a private report.  This
module is the resume seam for a coordinator: it observes that report and the
recorded process identity until the run is final.  It never invokes a model,
contacts a service, or prints periodic status.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
import uuid
from collections.abc import Mapping
from typing import Any, Callable, Dict, List, Optional, Tuple

from worker_monitor import (
    TerminalOpenCodeError,
    WaitError,
    positive_seconds,
    process_alive,
    terminal_error_name,
)


class InvalidRunIdError(WaitError, ValueError):
    """The requested run ID is not a canonical UUID string."""


class MissingRunError(WaitError, FileNotFoundError):
    """The requested run directory does not exist."""


class MissingReportError(WaitError, FileNotFoundError):
    """A run directory exists but has no readable report."""


class StaleRunError(WaitError):
    """A recorded owner process is gone before a final report was written."""


class RunTimeoutError(WaitError, TimeoutError):
    """An explicitly requested local waiting deadline elapsed."""


TERMINAL_FAILURE_STATUSES = frozenset(
    ("failed", "interrupted", "timed_out", "cancelled", "canceled", "error")
)
TERMINAL_SUCCESS_STATUSES = frozenset(
    ("committed", "no_changes", "completed", "complete", "succeeded", "success", "done")
)
_MAX_REPORT_BYTES = 4 * 1024 * 1024


def validate_run_id(run_id: Any) -> str:
    """Validate and return a canonical UUID run ID.

    A canonical form is required so the ID can safely select exactly one
    directory below the worker state directory.  UUID spellings with braces,
    uppercase characters, or omitted hyphens are rejected.
    """

    if not isinstance(run_id, str):
        raise InvalidRunIdError("run ID must be a canonical UUID")
    try:
        parsed = uuid.UUID(run_id)
    except (AttributeError, TypeError, ValueError):
        raise InvalidRunIdError("run ID must be a canonical UUID") from None
    if str(parsed) != run_id:
        raise InvalidRunIdError("run ID must be a canonical UUID")
    return run_id


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON number")


def _reject_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def _read_json(path: Path, *, label: str, max_bytes: int) -> Any:
    try:
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(str(path))
        size = path.stat().st_size
        if size > max_bytes:
            raise ValueError("JSON file is too large")
        raw = path.read_bytes()
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        # Keep diagnostics bounded and avoid echoing report/event payloads.
        raise WaitError("unable to read %s: %s" % (label, path)) from exc


def _state_paths(base: Any) -> Tuple[Path, Path]:
    try:
        root = Path(base).expanduser()
    except (TypeError, ValueError, OSError) as exc:
        raise WaitError("worker state directory is invalid") from exc
    runs = root / "runs"
    if runs.is_symlink():
        raise WaitError("worker runs directory must not be a symlink")
    return root, runs


def run_directory(base: Any, run_id: Any) -> Path:
    """Resolve one validated run directory below ``base/runs``."""

    canonical = validate_run_id(run_id)
    _, runs = _state_paths(base)
    path = runs / canonical
    if path.is_symlink():
        raise WaitError("worker run directory must not be a symlink")
    if not path.exists() or not path.is_dir():
        raise MissingRunError("worker run was not found: %s" % canonical)
    return path


def _read_report(run_dir: Path, run_id: str) -> Tuple[dict, Path]:
    path = run_dir / "report.json"
    try:
        report = _read_json(path, label="run report", max_bytes=_MAX_REPORT_BYTES)
    except FileNotFoundError:
        raise MissingReportError("run report is missing for run %s" % run_id) from None
    if not isinstance(report, Mapping):
        raise WaitError("run report must be a JSON object for run %s" % run_id)
    report_id = report.get("run_id")
    if report_id != run_id:
        raise WaitError("run report ID does not match requested run %s" % run_id)
    status = report.get("status")
    if not isinstance(status, str) or not status.strip():
        raise WaitError("run report has no valid status for run %s" % run_id)
    # Return a plain dict because the report is JSON-derived and callers may
    # pass the compact projection through a serializer.
    return dict(report), path


def _is_final_report(report: Mapping[str, Any]) -> bool:
    """Return whether the wrapper has supplied a terminal report.

    ``finalized`` is the authoritative marker in current reports.  An explicit
    non-true value therefore remains non-terminal, even when its status looks
    terminal.  Legacy reports without that marker use their status and phase
    as a compatibility fallback while avoiding the transient
    ``status=committed`` report written during metadata/final checks.
    """

    if "finalized" in report:
        return report.get("finalized") is True
    status = report.get("status")
    if not isinstance(status, str):
        return False
    status = status.strip().lower()
    if status in TERMINAL_FAILURE_STATUSES:
        return True
    if status in TERMINAL_SUCCESS_STATUSES:
        phase = report.get("phase")
        return phase in (None, "finished")
    return False


def _valid_pid(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _probe_pid(probe: Callable[[int], Any], pid: int) -> bool:
    try:
        result = probe(pid)
    except (OSError, ValueError, TypeError):
        return False
    return bool(result)


def _heartbeat(run_dir: Path) -> Optional[Mapping[str, Any]]:
    path = run_dir / "heartbeat.json"
    if path.is_symlink() or not path.exists():
        return None
    try:
        value = _read_json(path, label="worker heartbeat", max_bytes=_MAX_REPORT_BYTES)
    except FileNotFoundError:
        return None
    except WaitError:
        # A heartbeat is advisory.  A malformed snapshot must not become an
        # invented liveness or timeout decision.
        return None
    return value if isinstance(value, Mapping) else None


def _recorded_owner_alive(
    run_dir: Path,
    report: Mapping[str, Any],
    process_probe: Callable[[int], Any],
) -> Optional[bool]:
    """Observe a recorded owner process without using output silence.

    Current reports record ``launcher_pid``.  Older reports have no owner
    field, so only their heartbeat's explicit child PID and
    ``process_running=true`` are considered.  Missing or malformed legacy
    evidence remains unknown; it is never treated as a dead process merely
    because no output arrived.
    """

    if "launcher_pid" in report:
        pid = _valid_pid(report.get("launcher_pid"))
        if pid is None:
            return False
        return _probe_pid(process_probe, pid)

    heartbeat = _heartbeat(run_dir)
    if heartbeat is None or heartbeat.get("process_running") is not True:
        return None
    pid = _valid_pid(heartbeat.get("pid"))
    if pid is None:
        return None
    return _probe_pid(process_probe, pid)


def compact_report(report: Mapping[str, Any], report_path: Any) -> Dict[str, Any]:
    """Project the user-facing final fields without returning the full report."""

    git = report.get("git")
    git = git if isinstance(git, Mapping) else {}
    observed = report.get("observed_models")
    observed = list(observed) if isinstance(observed, list) else []
    result: Dict[str, Any] = {
        "status": report.get("status"),
        "run_id": report.get("run_id"),
        "commit": git.get("commit"),
        "report": str(Path(report_path)),
        "provider": report.get("provider"),
        "model": observed,
        "elapsed_seconds": report.get("elapsed_seconds"),
        "metrics": report.get("metrics") if isinstance(report.get("metrics"), Mapping) else {},
        "checks": report.get("checks") if isinstance(report.get("checks"), Mapping) else None,
        "delivery": report.get("delivery") if isinstance(report.get("delivery"), Mapping) else None,
    }
    # These aliases keep the projection usable by callers that need to decide
    # their exit code without loading the private full report again.
    result["finalized"] = _is_final_report(report)
    result["observed_models"] = observed
    result["git"] = dict(git)
    timing = report.get("timing")
    if isinstance(timing, Mapping):
        result["timing"] = dict(timing)
    if report.get("error") is not None:
        result["error"] = report.get("error")
    if report.get("persistence_error") is not None:
        result["persistence_error"] = report.get("persistence_error")
    return result


def active_runs(
    base: Any,
    *,
    process_probe: Optional[Callable[[int], Any]] = None,
) -> List[str]:
    """Return unfinished runs whose recorded owner process is alive.

    The result intentionally excludes stale reports.  For current reports,
    only ``launcher_pid`` is authoritative.  Legacy reports may use the
    heartbeat child PID when that snapshot explicitly says the child is
    running.  This protects setup/configuration without turning old exited
    reports or quiet output into a false active-run lock.
    """

    _, runs = _state_paths(base)
    if not runs.exists() or not runs.is_dir():
        return []
    probe = process_probe or process_alive
    result: List[str] = []
    try:
        entries = sorted(runs.iterdir(), key=lambda item: item.name)
    except OSError:
        return []
    for entry in entries:
        if entry.is_symlink() or not entry.is_dir():
            continue
        try:
            run_id = validate_run_id(entry.name)
            report, _ = _read_report(entry, run_id)
        except (InvalidRunIdError, MissingReportError, WaitError, OSError):
            continue
        if _is_final_report(report):
            continue
        owner_alive = _recorded_owner_alive(entry, report, probe)
        if owner_alive is True:
            result.append(run_id)
    return result


def wait_for_run(
    base: Any,
    run_id: Any,
    *,
    interval_seconds: Any = 5,
    timeout_seconds: Any = None,
    cancel_path: Any = None,
    process_probe: Optional[Callable[[int], Any]] = None,
    sleep_fn: Optional[Callable[[float], Any]] = None,
    clock: Optional[Callable[[], float]] = None,
    detect_terminal_errors: bool = True,
) -> Dict[str, Any]:
    """Block locally until a worker report is finalized and return its summary.

    ``timeout_seconds`` is opt-in.  ``None`` preserves the worker's support
    for jobs that are quiet for longer than twenty minutes.  Cancellation is
    performed by the worker's existing ``cancel`` command; this waiter keeps
    observing until that request produces a final report.
    """

    canonical = validate_run_id(run_id)
    run_dir = run_directory(base, canonical)
    interval = positive_seconds(interval_seconds, "wait_interval_seconds")
    timeout = None if timeout_seconds is None else positive_seconds(
        timeout_seconds, "wait_timeout_seconds"
    )
    if cancel_path is not None:
        # The path is an observation input only.  Do not create, remove, or
        # interpret it as a local timeout; the worker owns cancellation.
        try:
            Path(cancel_path)
        except (TypeError, ValueError, OSError) as exc:
            raise WaitError("cancel path is invalid") from exc
    probe = process_probe or process_alive
    sleeper = sleep_fn or time.sleep
    now = clock or time.monotonic
    started = now()
    events_path = run_dir / "events.jsonl"

    while True:
        report, report_path = _read_report(run_dir, canonical)
        if _is_final_report(report):
            return compact_report(report, report_path)

        if detect_terminal_errors:
            terminal_name = terminal_error_name(events_path)
            if terminal_name is not None:
                raise TerminalOpenCodeError(terminal_name, canonical)

        owner_alive = _recorded_owner_alive(run_dir, report, probe)
        if owner_alive is False:
            # The wrapper may have atomically published its final report
            # between the first report read and this liveness observation.
            report, report_path = _read_report(run_dir, canonical)
            if _is_final_report(report):
                return compact_report(report, report_path)
            raise StaleRunError(
                "worker wrapper for run %s is no longer running and no final report was written"
                % canonical
            )

        elapsed = now() - started
        if timeout is not None and elapsed >= timeout:
            raise RunTimeoutError(
                "waiting for run %s exceeded %.3f seconds" % (canonical, timeout)
            )
        delay = interval
        if timeout is not None:
            delay = min(delay, max(0.0, timeout - elapsed))
        sleeper(delay)


__all__ = [
    "InvalidRunIdError",
    "MissingReportError",
    "MissingRunError",
    "RunTimeoutError",
    "StaleRunError",
    "TerminalOpenCodeError",
    "WaitError",
    "active_runs",
    "compact_report",
    "run_directory",
    "validate_run_id",
    "wait_for_run",
]
