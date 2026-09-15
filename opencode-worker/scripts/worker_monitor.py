"""Local process observation; no model requests or automatic retries."""
import datetime
import json
import math
import os
from pathlib import Path
import subprocess
import time


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
    def __init__(self, run_dir, *, interval_seconds=5, timeout_seconds=None, cancel_path=None):
        self.run_dir = Path(run_dir)
        self.cancel_path = Path(cancel_path) if cancel_path else self.run_dir / 'cancel.request'
        self.interval_seconds = positive_seconds(interval_seconds, 'heartbeat_interval_seconds')
        self.timeout_seconds = (None if timeout_seconds is None else
                                positive_seconds(timeout_seconds, 'default_job_timeout_seconds'))
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
