"""Run deterministic project delivery steps for an audited worker run.

The model process is deliberately outside this module.  A delivery step is
an already selected command represented by an argument vector; this module
only starts it, captures its output, and records what happened.  In
particular, it never invokes a shell, retries a command, talks to a model, or
changes Git state.
"""

from __future__ import annotations

import os
from collections.abc import (
    Mapping
)
from pathlib import (
    Path
)
import subprocess
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


from worker_delivery_support import (
    sanitize_step_id,
    DEFAULT_STEP_TIMEOUT_SECONDS,
    HEARTBEAT_INTERVAL_SECONDS,
    DeliveryError,
    DeliveryInterrupted,
    _mark_guard_failure,
    _is_guard_failure,
    _attach_delivery_results,
    _invoke_guard,
    _validate_optional_seconds,
    _remaining_value,
    _step_directory_name,
    _display_step_id,
    _required_value,
    _timeout_value,
    _prepare_paths,
    _initial_result,
    _finish,
    _child_environment,
    _resolve_cwd,
    _resolve_argv,
    _record_monitor,
    _cancel_requested,
    _stop_quietly,
    _new_monitor
)


def _run_step(
    step: Any,
    *,
    repo: Path,
    run_dir: Path,
    stage: Any,
    env: Optional[Mapping[str, Any]],
    result: dict[str, Any],
    started_clock: float,
    guard: Any = None,
    default_timeout_seconds: Optional[float | int] = None,
    remaining_seconds: Any = None,
) -> None:
    process = None
    monitor: Optional[ProcessMonitor] = None
    streams: list[Any] = []
    try:
        if not isinstance(step, Mapping):
            raise ValueError("each delivery step must be an object")
        if worker_platform is None:
            raise RuntimeError("worker_platform process seam is unavailable")
        # A request that predates this step must not even resolve or prepare a
        # command.  The caller still receives a structured interrupted result.
        if _cancel_requested(run_dir):
            raise KeyboardInterrupt()
        required = _required_value(step)
        result["required"] = required
        explicit_timeout = _timeout_value(step)
        timeout = explicit_timeout if explicit_timeout is not None else default_timeout_seconds
        remaining = _remaining_value(remaining_seconds)
        if remaining is not None:
            if remaining <= 0:
                # Normally the shared guard raises the owner's
                # BudgetExceeded exception before this point.  Keep a
                # deterministic fallback for direct callers that provide a
                # depleted remaining-time seam without a guard.
                raise DeliveryError("whole-job delivery deadline exhausted", [])
            timeout = remaining if timeout is None else min(timeout, remaining)
        result["timeout_seconds"] = timeout
        argv = _resolve_argv(step, repo)
        cwd = _resolve_cwd(step, repo)
        result["argv"] = list(argv)
        result["cwd"] = str(cwd)
        child_env = _child_environment(env)
        # Constructing the monitor validates the per-step timeout before any
        # child starts.  ``None`` deliberately means no total deadline.
        check_dir = Path(result["heartbeat_path"]).parent
        monitor = _new_monitor(check_dir, timeout, run_dir, guard=guard)
        # Avoid launching a new check after the local cancellation request is
        # already visible.  The monitor performs the same check while a child
        # is running to close the race between this check and ``Popen``.
        if _cancel_requested(run_dir):
            raise KeyboardInterrupt()
        stdout_stream = open(result["stdout_path"], "wb")
        stderr_stream = open(result["stderr_path"], "wb")
        streams.extend((stdout_stream, stderr_stream))
        options = worker_platform.process_options()
        if options is None:
            options = {}
        # Recheck after all setup so a request arriving during resolution or
        # log opening cannot race directly into a child launch.
        if _cancel_requested(run_dir):
            raise KeyboardInterrupt()
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=child_env,
            stdout=stdout_stream,
            stderr=stderr_stream,
            shell=False,
            **dict(options),
        )
        result["pid"] = process.pid
        waited_code = monitor.wait(process)
        # A process-like test double, or a platform-specific monitor, may
        # return the code before updating ``returncode``.  Prefer the actual
        # process attribute when available and use the wait result otherwise.
        result["exit_code"] = process.returncode
        if result["exit_code"] is None:
            result["exit_code"] = waited_code
        result["status"] = "passed" if result["exit_code"] == 0 else "failed"
        if result["status"] == "failed":
            result["error"] = "command exited with status " + str(result["exit_code"])
        _record_monitor(monitor, process, result["status"])
    except subprocess.TimeoutExpired:
        _stop_quietly(process, result)
        result["status"] = "timed_out"
        result["error"] = "command exceeded timeout"
        try:
            _record_monitor(monitor, process, "timed_out")
        except Exception as heartbeat_error:
            result["heartbeat_error"] = type(heartbeat_error).__name__
    except KeyboardInterrupt:
        _stop_quietly(process, result)
        result["status"] = "interrupted"
        try:
            _record_monitor(monitor, process, "interrupted")
        except Exception as heartbeat_error:
            result["heartbeat_error"] = type(heartbeat_error).__name__
        _finish(result, started_clock)
        raise
    except Exception as exc:
        _stop_quietly(process, result)
        guard_failed = _is_guard_failure(exc) or (
            monitor is not None and getattr(monitor, "guard_exception", None) is exc
        )
        if monitor is not None and getattr(monitor, "guard_exception", None) is exc:
            _mark_guard_failure(exc)
        result["status"] = "budget_exceeded" if guard_failed else "failed"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        try:
            _record_monitor(monitor, process, "failed")
        except Exception as heartbeat_error:
            result["heartbeat_error"] = type(heartbeat_error).__name__
        if guard_failed:
            raise
    finally:
        for stream in streams:
            try:
                stream.close()
            except Exception as close_error:
                result.setdefault("log_close_error", type(close_error).__name__)
        _finish(result, started_clock)


def run_steps(
    steps: Iterable[Mapping[str, Any]],
    *,
    repo: os.PathLike[str] | str,
    run_dir: os.PathLike[str] | str,
    stage: Any,
    env: Optional[Mapping[str, Any]] = None,
    guard: Any = None,
    default_timeout_seconds: Optional[float | int] = None,
    remaining_seconds: Any = None,
) -> list[dict[str, Any]]:
    """Run each declared delivery step once and return structured results.

    A nonzero exit, timeout, launch error, or invalid required step raises
    :class:`DeliveryError` after its result is appended.  Optional failures
    remain in the returned list.  ``guard`` is a local callback invoked before
    each step and by :class:`ProcessMonitor` during each running step; its
    original exception propagates unchanged so a shared ``BudgetExceeded``
    can be handled by the job owner.  A ``KeyboardInterrupt`` is converted to
    :class:`DeliveryInterrupted`, which is still a ``KeyboardInterrupt`` and
    carries the partial result list for persistence by the caller.
    """

    if guard is not None and not callable(guard):
        raise ValueError("guard must be callable or null")
    default_timeout_seconds = _validate_optional_seconds(
        default_timeout_seconds, "default_timeout_seconds"
    )
    if remaining_seconds is not None and not callable(remaining_seconds):
        _validate_optional_seconds(remaining_seconds, "remaining_seconds", allow_zero=True)

    results: list[dict[str, Any]] = []
    try:
        iterator = iter(steps)
    except TypeError as exc:
        raise DeliveryError("steps must be iterable", results) from exc

    repo_path = Path(repo)
    run_path = Path(run_dir)
    used_directories: set[str] = set()
    try:
        for index, step in enumerate(iterator):
            _invoke_guard(guard)
            step_id = _display_step_id(step, index)
            directory_name = _step_directory_name(step_id, stage, used_directories)
            result, started_clock = _initial_result(
                step,
                index=index,
                stage=stage,
                run_dir=run_path,
                directory_name=directory_name,
            )
            try:
                _prepare_paths(run_path, directory_name)
                _run_step(
                    step,
                    repo=repo_path,
                    run_dir=run_path,
                    stage=stage,
                    env=env,
                    result=result,
                    started_clock=started_clock,
                    guard=guard,
                    default_timeout_seconds=default_timeout_seconds,
                    remaining_seconds=remaining_seconds,
                )
            except DeliveryInterrupted:
                raise
            except KeyboardInterrupt:
                result["status"] = "interrupted"
                _finish(result, started_clock)
                results.append(result)
                raise DeliveryInterrupted(results) from None
            except Exception as exc:
                guard_failed = _is_guard_failure(exc)
                if not guard_failed:
                    result["status"] = "failed"
                    result["error_type"] = type(exc).__name__
                    result["error"] = str(exc)
                    _finish(result, started_clock)
                else:
                    result.setdefault("error_type", type(exc).__name__)
                    result.setdefault("error", str(exc))
                    if result.get("finished_at") is None:
                        _finish(result, started_clock)
                results.append(result)
                if guard_failed:
                    _attach_delivery_results(exc, results)
                    raise
                if result["required"]:
                    raise DeliveryError(
                        "required delivery step " + repr(result["id"]) + " failed",
                        results,
                    )
                continue

            results.append(result)
            if result["required"] and result["status"] != "passed":
                raise DeliveryError(
                    "required delivery step " + repr(result["id"]) + " " + result["status"],
                    results,
                )
    except DeliveryInterrupted:
        raise
    except KeyboardInterrupt:
        raise DeliveryInterrupted(results) from None
    except Exception as exc:
        if _is_guard_failure(exc):
            _attach_delivery_results(exc, results)
        raise
    return results


__all__ = [
    "DeliveryError",
    "DeliveryInterrupted",
    "DEFAULT_STEP_TIMEOUT_SECONDS",
    "HEARTBEAT_INTERVAL_SECONDS",
    "run_steps",
    "sanitize_step_id",
]
