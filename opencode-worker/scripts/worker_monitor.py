"""Local process observation; no model requests or automatic retries."""
import datetime
import ctypes
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from collections.abc import Mapping
from typing import Any, Iterable, List, Optional, Tuple


def process_alive(pid):
    """Return whether the recorded process ID currently exists.

    This is deliberately a small OS observation seam.  It does not inspect
    output age or infer progress from a quiet event stream.  A permission
    error means that the process exists but is not inspectable by this user;
    other lookup failures are treated as a dead/unknown process so callers do
    not retain a false busy lock forever.
    """

    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == 'nt':
        # ``os.kill(pid, 0)`` is not a probe on Windows: Python maps several
        # signals to TerminateProcess.  Ask the kernel for a query/sync handle
        # instead and always close it without mutating the target process.
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
            kernel32.OpenProcess.restype = ctypes.c_void_p
            kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            kernel32.GetExitCodeProcess.restype = ctypes.c_int
            kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel32.CloseHandle.restype = ctypes.c_int
            # PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE
            handle = kernel32.OpenProcess(0x1000 | 0x00100000, 0, pid)
        except (AttributeError, OSError, TypeError, ValueError):
            return False
        if not handle:
            # Access denied is evidence that a process exists, while an
            # invalid PID is not.  Do not turn arbitrary API failures into a
            # false active-run lock.
            return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED
        try:
            code = ctypes.c_uint32()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True  # a valid handle still proves the process exists
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except (ProcessLookupError, OSError, ValueError):
        return False
    return True


class WaitError(RuntimeError):
    """Base class for errors found while observing a worker process/run."""


class TerminalOpenCodeError(WaitError):
    """OpenCode supplied explicit non-retryable terminal error evidence."""

    def __init__(self, name, run_id=None):
        self.name = name
        self.run_id = run_id
        message = 'OpenCode reported terminal error: ' + str(name)
        if run_id is not None:
            message += ' for run ' + str(run_id)
        super().__init__(message)


_MAX_EVENT_BYTES = 16 * 1024 * 1024


def _reject_json_constant(value):
    raise ValueError('non-finite JSON number')


def _reject_duplicate_keys(pairs: Iterable[Tuple[str, Any]]) -> dict:
    result = {}
    for key, item in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = item
    return result


def _safe_error_name(value):
    text = str(value).strip()
    text = re.sub(r'[^A-Za-z0-9_.-]', '_', text)
    return (text[:80] or 'OpenCodeError')


def terminal_error_name(path) -> Optional[str]:
    """Return a short name only for explicit terminal error evidence.

    OpenCode can emit ordinary error events while retrying.  A generic event
    type or error payload is therefore insufficient to stop a run.  The
    caller must see a terminal/fatal marker or an explicit ``retryable`` false
    marker before this helper reports a terminal error.
    """

    event_path = Path(path)
    try:
        if (event_path.is_symlink() or not event_path.is_file()
                or event_path.stat().st_size > _MAX_EVENT_BYTES):
            return None
        lines = event_path.read_bytes().decode('utf-8').splitlines()
    except (OSError, UnicodeError):
        return None

    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line, object_pairs_hook=_reject_duplicate_keys,
                               parse_constant=_reject_json_constant)
        except (TypeError, UnicodeError, ValueError):
            # A concurrently written final line is not terminal evidence.
            continue
        if not isinstance(event, Mapping):
            continue
        containers: List[Mapping[str, Any]] = [event]
        for key in ('part', 'properties'):
            nested = event.get(key)
            if isinstance(nested, Mapping):
                containers.append(nested)
                nested_error = nested.get('error')
                if isinstance(nested_error, Mapping):
                    containers.append(nested_error)
                    for data_key in ('data', 'details'):
                        data = nested_error.get(data_key)
                        if isinstance(data, Mapping):
                            containers.append(data)
        event_error = event.get('error')
        if isinstance(event_error, Mapping):
            containers.append(event_error)
            for data_key in ('data', 'details'):
                data = event_error.get(data_key)
                if isinstance(data, Mapping):
                    containers.append(data)

        has_error = False
        explicit_terminal = False
        explicitly_nonretryable = False
        specific_name = None
        fallback_name = None
        for container in containers:
            event_type = container.get('type')
            if isinstance(event_type, str) and 'error' in event_type.lower():
                has_error = True
            if 'error' in container:
                has_error = True
            if container.get('terminal') is True or container.get('isTerminal') is True:
                explicit_terminal = True
            if container.get('fatal') is True or container.get('isFatal') is True:
                explicit_terminal = True
            if (container.get('retryable') is False
                    or container.get('isRetryable') is False
                    or container.get('is_retryable') is False):
                explicitly_nonretryable = True
            # Error names/codes are more useful than the enclosing generic
            # event type (usually simply ``error``).  Keep the two classes
            # separate so the event's type cannot mask ``APIError`` below it.
            for key in ('name', 'code'):
                candidate = container.get(key)
                if specific_name is None and isinstance(candidate, str) and candidate.strip():
                    specific_name = _safe_error_name(candidate)
            candidate = container.get('type')
            if fallback_name is None and isinstance(candidate, str) and candidate.strip():
                fallback_name = _safe_error_name(candidate)
        if has_error and (explicit_terminal or explicitly_nonretryable):
            return specific_name or fallback_name or 'OpenCodeError'
    return None


def positive_seconds(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + ' must be a finite positive number')
    try:
        valid = math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(name + ' must be a finite positive number')
    return value


class ProcessMonitor:
    def __init__(self, run_dir, *, interval_seconds=5, timeout_seconds=None, cancel_path=None,
                 launcher_pid=None, detect_terminal_errors=True):
        self.run_dir = Path(run_dir)
        self.cancel_path = Path(cancel_path) if cancel_path else self.run_dir / 'cancel.request'
        self.interval_seconds = positive_seconds(interval_seconds, 'heartbeat_interval_seconds')
        self.timeout_seconds = (None if timeout_seconds is None else
                                positive_seconds(timeout_seconds, 'default_job_timeout_seconds'))
        if launcher_pid is None:
            launcher_pid = os.getpid()
        if isinstance(launcher_pid, bool) or not isinstance(launcher_pid, int) or launcher_pid <= 0:
            raise ValueError('launcher_pid must be a positive integer')
        self.launcher_pid = launcher_pid
        if not isinstance(detect_terminal_errors, bool):
            raise ValueError('detect_terminal_errors must be a boolean')
        self.detect_terminal_errors = detect_terminal_errors
        self.started = None
        self.heartbeat_count = 0
        self.output_sizes = (0, 0)
        self.last_output_time = None
        self.last_output_at = None

    def record(self, process, state=None):
        now = time.monotonic()
        checked_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if self.started is None:
            self.started = now
        code = process.poll()
        sizes = []
        stdout_name = 'events.jsonl' if (self.run_dir / 'events.jsonl').exists() else 'stdout.log'
        for name in (stdout_name, 'stderr.log'):
            try:
                sizes.append((self.run_dir / name).stat().st_size)
            except FileNotFoundError:
                sizes.append(0)
        if tuple(sizes) != self.output_sizes:
            self.last_output_time, self.last_output_at = now, checked_at
            self.output_sizes = tuple(sizes)
        self.heartbeat_count += 1
        snapshot = {
            'schema_version': 1, 'pid': process.pid,
            # ``launcher_pid`` identifies the Python wrapper that owns the
            # run.  The child PID above is retained for compatibility and for
            # legacy run inspection; neither field is a progress heuristic.
            'launcher_pid': self.launcher_pid,
            'state': state or ('running' if code is None else 'exited'),
            'process_running': code is None, 'exit_code': code,
            'checked_at': checked_at, 'elapsed_seconds': round(now - self.started, 3),
            'interval_seconds': self.interval_seconds, 'timeout_seconds': self.timeout_seconds,
            'heartbeat_count': self.heartbeat_count,
            'events_bytes': sizes[0], 'stderr_bytes': sizes[1],
            'last_output_observed_at': self.last_output_at,
            'seconds_since_output': (None if self.last_output_time is None else
                                     round(now - self.last_output_time, 3)),
        }
        # A single private snapshot is replaced atomically; nothing is emitted
        # to the coordinating model or appended to the model's event stream.
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / 'heartbeat.json'
        temp = path.with_name(path.name + '.tmp')
        with temp.open('w', encoding='utf-8', newline='\n') as stream:
            os.chmod(temp, 0o600)
            json.dump(snapshot, stream, allow_nan=False)
            stream.write('\n')
        temp.replace(path)
        return snapshot

    def wait(self, process):
        self.started = time.monotonic()
        while True:
            if self.cancel_path.exists():
                raise KeyboardInterrupt()
            snapshot = self.record(process)
            if self.detect_terminal_errors:
                terminal_name = terminal_error_name(self.run_dir / 'events.jsonl')
                if terminal_name is not None:
                    raise TerminalOpenCodeError(terminal_name)
            if not snapshot['process_running']:
                return snapshot['exit_code']
            delay = self.interval_seconds
            if self.timeout_seconds is not None:
                remaining = self.timeout_seconds - (time.monotonic() - self.started)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(process.args, self.timeout_seconds)
                delay = min(delay, remaining)
            try:
                # Timeout here means another local check, not a failed job.
                # A real worker exit wakes this wait without waiting five seconds.
                process.wait(timeout=delay)
            except subprocess.TimeoutExpired:
                pass


__all__ = [
    'ProcessMonitor', 'TerminalOpenCodeError', 'WaitError', 'positive_seconds', 'process_alive',
    'terminal_error_name',
]
