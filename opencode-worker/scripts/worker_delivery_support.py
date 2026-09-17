"""Run deterministic project delivery steps for an audited worker run.

The model process is deliberately outside this module.  A delivery step is
an already selected command represented by an argument vector; this module
only starts it, captures its output, and records what happened.  In
particular, it never invokes a shell, retries a command, talks to a model, or
changes Git state.
"""

from __future__ import annotations

import datetime
import hashlib
import math
import os
from collections.abc import (
    Mapping
)
from pathlib import (
    Path
)
import re
import time
from typing import (
    Any,
    Iterable,
    Optional
)

try:
    import worker_platform
except ImportError:  # The companion seam may be installed after this module.
    worker_platform = None  # type: ignore[assignment]

try:
    import worker_project
except ImportError:  # The companion seam may be installed after this module.
    worker_project = None  # type: ignore[assignment]

from worker_monitor import (
    ProcessMonitor
)


HEARTBEAT_INTERVAL_SECONDS = 5
DEFAULT_STEP_TIMEOUT_SECONDS = 600
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]")
_WINDOWS_RESERVED_NAMES = {
    "aux",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "con",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
    "nul",
    "prn",
}


class DeliveryError(RuntimeError):
    """A required delivery step failed.

    ``results`` includes the failed step and all earlier steps.  The caller
    can therefore persist the partial evidence before reporting the error.
    """

    def __init__(self, message: str, results: Iterable[dict[str, Any]]) -> None:
        super().__init__(message)
        self.results = list(results)


class DeliveryInterrupted(KeyboardInterrupt):
    """Cancellation while a delivery step was running or being prepared."""

    def __init__(self, results: Iterable[dict[str, Any]]) -> None:
        super().__init__("delivery interrupted")
        self.results = list(results)


_GUARD_FAILURE_ATTR = "_worker_delivery_guard_failure"


def _mark_guard_failure(exc: BaseException) -> BaseException:
    """Mark a guard exception while preserving its original type and cause."""

    try:
        setattr(exc, _GUARD_FAILURE_ATTR, True)
    except Exception:
        # Built-in exceptions normally have a dictionary.  If a caller uses a
        # slotted exception, the original exception still propagates; the
        # monitor path below remains able to identify it by its monitor flag.
        pass
    return exc


def _is_guard_failure(exc: BaseException) -> bool:
    return getattr(exc, _GUARD_FAILURE_ATTR, False) is True


def _attach_delivery_results(exc: BaseException, results: Iterable[dict[str, Any]]) -> None:
    """Make partial results available without wrapping a budget exception."""

    try:
        setattr(exc, "delivery_results", list(results))
    except Exception:
        pass


def _invoke_guard(guard: Any) -> None:
    if guard is None:
        return
    if not callable(guard):
        raise ValueError("guard must be callable or null")
    try:
        guard()
    except BaseException as exc:
        raise _mark_guard_failure(exc)


def _validate_optional_seconds(value: Any, name: str, *, allow_zero: bool = False) -> Optional[float | int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        qualifier = "non-negative" if allow_zero else "finite positive"
        raise ValueError(name + " must be a " + qualifier + " number or null")
    try:
        valid = math.isfinite(value) and (value >= 0 if allow_zero else value > 0)
    except (OverflowError, TypeError):
        valid = False
    if not valid:
        qualifier = "non-negative" if allow_zero else "finite positive"
        raise ValueError(name + " must be a " + qualifier + " number or null")
    return value


def _remaining_value(value: Any) -> Optional[float | int]:
    """Read a whole-job remaining-time seam at the point of child launch."""

    if value is None:
        return None
    current = value() if callable(value) else value
    return _validate_optional_seconds(current, "remaining_seconds", allow_zero=True)


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _elapsed(started: float) -> float:
    return round(max(0.0, time.monotonic() - started), 3)


def sanitize_step_id(value: Any) -> str:
    """Return one safe directory component for a step identifier.

    The result contains no path separators, is bounded for Windows paths, and
    avoids special or reserved directory names.  Directory names also include
    a digest in :func:`_step_directory_name` so sanitization cannot merge IDs.
    """

    text = str(value)
    safe = _SAFE_ID.sub("_", text).rstrip(" .")
    if not safe or safe in {".", ".."}:
        safe = "step"
    if safe.casefold().split(".", 1)[0] in _WINDOWS_RESERVED_NAMES:
        safe = "_" + safe
    if len(safe) > 80:
        digest = hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()[:12]
        safe = safe[:67] + "-" + digest
    return safe


def _step_directory_name(value: Any, stage: Any, used: set[str]) -> str:
    """Build a readable, bounded, collision-resistant directory component."""

    original = str(value)
    stage_text = str(stage)
    readable = sanitize_step_id(stage_text + "-" + original)
    digest_source = (stage_text + "\0" + original).encode("utf-8", "surrogatepass")
    digest = hashlib.sha256(digest_source).hexdigest()[:12]
    digest_suffix = "-" + digest

    def bounded(prefix: str, suffix: str) -> str:
        room = max(1, 80 - len(suffix))
        return (prefix[:room].rstrip(" .") or "step") + suffix

    candidate = bounded(readable, digest_suffix)
    folded = candidate.casefold()
    if folded not in used:
        used.add(folded)
        return candidate

    # Exact duplicate IDs are invalid at the project-contract layer, but keep
    # this executor safe when called directly and when a caller reuses a run
    # directory.  Compare case-folded names because Windows does.
    suffix_number = 2
    while True:
        number_suffix = digest_suffix + "-" + str(suffix_number)
        candidate = bounded(readable, number_suffix)
        folded = candidate.casefold()
        if folded not in used:
            used.add(folded)
            return candidate
        suffix_number += 1


def _display_step_id(step: Any, index: int) -> Any:
    if isinstance(step, Mapping) and "id" in step:
        value = step["id"]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
    return f"step-{index}"


def _required_value(step: Any) -> bool:
    if not isinstance(step, Mapping):
        return True
    value = step.get("required", True)
    if not isinstance(value, bool):
        raise ValueError("required must be a boolean")
    return value


def _timeout_value(step: Any) -> Optional[float | int]:
    if not isinstance(step, Mapping):
        return None
    value = step.get("timeout_seconds")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("timeout_seconds must be a finite positive number or null")
    try:
        valid = math.isfinite(value) and value > 0
    except (OverflowError, TypeError):
        valid = False
    if not valid:
        raise ValueError("timeout_seconds must be a finite positive number or null")
    return value


def _safe_path_text(value: Any) -> str:
    if isinstance(value, bytes):
        return os.fsdecode(value)
    if isinstance(value, os.PathLike):
        return os.fsdecode(os.fspath(value))
    return str(value)


def _private_directory(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("delivery log directory must not be a symlink: " + str(path))
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("delivery log directory is not a directory: " + str(path))
    path.chmod(0o700)


def _prepare_log(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("delivery log path is not a regular file: " + str(path))
    with path.open("wb"):
        pass
    path.chmod(0o600)


def _prepare_paths(run_dir: Path, directory_name: str) -> tuple[Path, Path, Path]:
    _private_directory(run_dir)
    checks = run_dir / "checks"
    _private_directory(checks)
    check_dir = checks / directory_name
    _private_directory(check_dir)
    stdout_path = check_dir / "stdout.log"
    stderr_path = check_dir / "stderr.log"
    _prepare_log(stdout_path)
    _prepare_log(stderr_path)
    return check_dir, stdout_path, stderr_path


def _initial_result(
    step: Any,
    *,
    index: int,
    stage: Any,
    run_dir: Path,
    directory_name: str,
) -> tuple[dict[str, Any], float]:
    started_clock = time.monotonic()
    step_id = _display_step_id(step, index)
    required = True
    if isinstance(step, Mapping) and isinstance(step.get("required", True), bool):
        required = step.get("required", True)
    timeout = step.get("timeout_seconds") if isinstance(step, Mapping) else None
    # Keep the result JSON-safe even when the contract is invalid.  The
    # execution path records the validation error below and does not launch a
    # process for such a step.
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        timeout = None
    else:
        try:
            if not math.isfinite(timeout) or timeout <= 0:
                timeout = None
        except (OverflowError, TypeError):
            timeout = None
    check_dir = run_dir / "checks" / directory_name
    stdout_path = check_dir / "stdout.log"
    stderr_path = check_dir / "stderr.log"
    result: dict[str, Any] = {
        "id": step_id,
        "kind": step.get("kind") if isinstance(step, Mapping) else None,
        "stage": stage,
        "required": required,
        "status": "failed",
        "exit_code": None,
        "started_at": _utc_now(),
        "finished_at": None,
        "elapsed_seconds": None,
        "timeout_seconds": timeout,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "heartbeat_path": str(check_dir / "heartbeat.json"),
        "log_paths": {"stdout": str(stdout_path), "stderr": str(stderr_path)},
    }
    return result, started_clock


def _finish(result: dict[str, Any], started_clock: float) -> None:
    result["finished_at"] = _utc_now()
    result["elapsed_seconds"] = _elapsed(started_clock)


def _child_environment(extra: Optional[Mapping[str, Any]]) -> dict[str, str]:
    """Build a child environment without credentials or ambient Git control."""

    child = dict(os.environ)
    for name in list(child):
        upper = name.upper()
        if upper == "OPENROUTER_API_KEY" or upper.startswith("GIT_") or upper.startswith("WORKER_"):
            child.pop(name, None)

    if extra is not None:
        if not isinstance(extra, Mapping):
            raise ValueError("env must be a mapping or null")
        for name, value in extra.items():
            if not isinstance(name, str):
                raise ValueError("environment names must be strings")
            if not name.startswith("WORKER_"):
                continue
            if isinstance(value, bytes):
                child[name] = os.fsdecode(value)
            elif isinstance(value, (str, os.PathLike)):
                child[name] = _safe_path_text(value)
            else:
                raise ValueError("WORKER_* environment values must be strings")

    # Apply the filter again in case a case-variant key was supplied on
    # Windows, where environment names are case-insensitive.
    for name in list(child):
        upper = name.upper()
        if upper == "OPENROUTER_API_KEY" or upper.startswith("GIT_"):
            child.pop(name, None)
    return child


def _resolve_cwd(step: Mapping[str, Any], repo: Path) -> Path:
    value = step.get("cwd", repo)
    if value is None:
        value = repo
    if not isinstance(value, (str, bytes, os.PathLike)):
        raise ValueError("cwd must be a path string")
    cwd = Path(_safe_path_text(value))
    return cwd if cwd.is_absolute() else repo / cwd


def _resolve_argv(step: Mapping[str, Any], repo: Path) -> list[str]:
    if worker_project is None or not hasattr(worker_project, "command_argv"):
        raise RuntimeError("worker_project.command_argv is unavailable")
    argv = worker_project.command_argv(step, repo)
    if isinstance(argv, (str, bytes)) or not isinstance(argv, (list, tuple)):
        raise ValueError("command_argv must return an argument vector")
    if not argv:
        raise ValueError("command_argv returned an empty argument vector")
    normalized: list[str] = []
    for item in argv:
        if not isinstance(item, (str, bytes, os.PathLike)):
            raise ValueError("command arguments must be strings")
        normalized.append(_safe_path_text(item))
    return normalized


def _record_monitor(monitor: Optional[ProcessMonitor], process: Any, state: str) -> None:
    if monitor is None or process is None:
        return
    monitor.record(process, state=state)


def _cancel_requested(run_dir: Path) -> bool:
    return (run_dir / "cancel.request").exists()


def _stop_quietly(process: Any, result: dict[str, Any]) -> None:
    if process is None or worker_platform is None:
        return
    try:
        # The platform seam is idempotent and performs its own liveness check;
        # calling it on every interruption/timeout closes races where a child
        # exits between the monitor exception and cleanup.
        worker_platform.stop_process(process)
    except KeyboardInterrupt:
        # The original cancellation is preserved by the caller.
        result["cleanup_error"] = "KeyboardInterrupt"
    except Exception as exc:
        result["cleanup_error"] = type(exc).__name__
    try:
        result["exit_code"] = process.poll()
    except Exception as exc:
        result["cleanup_error"] = result.get("cleanup_error", type(exc).__name__)


def _new_monitor(
    check_dir: Path,
    timeout: Optional[float | int],
    run_dir: Path,
    guard: Any = None,
) -> ProcessMonitor:
    kwargs = {
        "interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
        "timeout_seconds": timeout,
        "cancel_path": run_dir / "cancel.request",
    }
    if guard is not None:
        kwargs["guard"] = guard
    try:
        return ProcessMonitor(check_dir, **kwargs)
    except TypeError as exc:
        # Keep compatibility with an older installed monitor while the shared
        # cancellation seam is rolled out.  A monitor that accepts the seam
        # always receives it above.
        if guard is not None and "guard" in str(exc):
            raise RuntimeError(
                "ProcessMonitor does not support the shared delivery guard"
            ) from exc
        if "cancel_path" not in str(exc):
            raise
        kwargs.pop("cancel_path")
        try:
            return ProcessMonitor(check_dir, **kwargs)
        except TypeError as retry_error:
            if guard is not None and "guard" in str(retry_error):
                raise RuntimeError(
                    "ProcessMonitor does not support the shared delivery guard"
                ) from retry_error
            raise


