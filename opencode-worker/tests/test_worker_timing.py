"""Focused tests for local phase and OpenCode event timing."""

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker_timing import RunTimer, summarize_events  # noqa: E402


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def _event(kind, timestamp, part):
    return {"type": kind, "timestamp": timestamp, "part": part}


def _write_events(path, lines):
    path.write_text("\n".join(json.dumps(item) for item in lines) + "\n", encoding="utf-8")


class RunTimerTests(unittest.TestCase):
    def test_starts_preflight_accumulates_repeated_phases_and_freezes_on_finish(self):
        clock = FakeClock()
        timer = RunTimer(clock=clock)
        clock.advance(2)
        timer.start("model")
        clock.advance(3)
        timer.start("before_commit")
        clock.advance(1)
        timer.start("model")
        clock.advance(4)

        snapshot = timer.snapshot()
        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["active_phase"], "model")
        self.assertEqual(snapshot["phases_seconds"], {
            "preflight": 2.0,
            "model": 7.0,
            "before_commit": 1.0,
        })
        self.assertEqual(snapshot["elapsed_seconds"], 10.0)

        finished = timer.finish()
        self.assertIsNone(finished["active_phase"])
        self.assertEqual(finished["elapsed_seconds"], 10.0)
        clock.advance(50)
        self.assertEqual(timer.snapshot(), finished)
        self.assertEqual(timer.finish(), finished)

    def test_rejects_invalid_phase_and_start_after_finish(self):
        clock = FakeClock()
        timer = RunTimer(clock=clock)
        with self.assertRaises((TypeError, ValueError)):
            timer.start("")
        timer.finish()
        with self.assertRaises(RuntimeError):
            timer.start("model")


class SummarizeEventsTests(unittest.TestCase):
    def test_reports_distinct_steps_tools_and_union_of_overlapping_tool_intervals(self):
        events = [
            _event("step-start", 1000, {"type": "step-start", "id": "started"}),
            _event("tool", 2000, {
                "type": "tool", "id": "tool-1", "state": {
                    "status": "completed", "time": {"start": 2000, "end": 4000}
                }
            }),
            _event("tool", 2500, {
                "type": "tool", "id": "tool-1", "state": {
                    "status": "completed", "time": {"start": 2000, "end": 4000}
                }
            }),
            _event("tool", 3500, {
                "type": "tool", "id": "tool-2", "state": {
                    "status": "completed", "time": {"start": 3500, "end": 6000}
                }
            }),
            _event("step-finish", 7000, {"type": "step-finish", "id": "finished"}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = summarize_events(path)

        self.assertEqual(result["availability"], "available")
        self.assertEqual(result["coverage"], {
            "event_timestamps": "complete",
            "tool_timestamps": "complete",
        })
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["model_steps"], 1)
        self.assertEqual(result["tool_calls"], 2)
        self.assertEqual(result["event_span_seconds"], 6.0)
        self.assertEqual(result["tool_execution_seconds"], 4.0)
        self.assertEqual(result["non_tool_seconds"], 2.0)
        self.assertNotIn("text", result)

    def test_missing_and_malformed_timestamps_are_partial_and_never_zero_filled(self):
        events = [
            _event("step-finish", 1000, {"type": "step-finish", "id": "step-1"}),
            _event("tool", None, {
                "type": "tool", "id": "tool-1", "state": {"status": "completed"}
            }),
        ]
        events[1].pop("timestamp")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            with path.open("a", encoding="utf-8") as stream:
                stream.write('{"type":"tool"')
            result = summarize_events(path)

        self.assertEqual(result["availability"], "partial")
        self.assertEqual(result["coverage"]["event_timestamps"], "partial")
        self.assertEqual(result["coverage"]["tool_timestamps"], "unknown")
        self.assertIn("event_timestamps", result["missing"])
        self.assertIn("tool_timestamps", result["missing"])
        self.assertEqual(result["event_span_seconds"], 0.0)
        self.assertIsNone(result["tool_execution_seconds"])
        self.assertIsNone(result["non_tool_seconds"])

    def test_legacy_stream_without_timestamps_is_unavailable_and_does_not_leak_text(self):
        events = [{
            "type": "error",
            "error": {"message": "secret prompt or tool output"},
            "part": {"type": "text", "id": "text-1", "text": "secret"},
        }]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = summarize_events(path)

        self.assertEqual(result["availability"], "unavailable")
        self.assertIsNone(result["event_span_seconds"])
        self.assertIsNone(result["tool_execution_seconds"])
        self.assertIsNone(result["non_tool_seconds"])
        self.assertIn("event_timestamps", result["missing"])
        rendered = json.dumps(result)
        self.assertNotIn("secret", rendered)

    def test_missing_file_and_nonfinite_timestamp_are_safe_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.jsonl"
            missing_result = summarize_events(missing)
            self.assertEqual(missing_result["availability"], "unavailable")
            self.assertIsNone(missing_result["model_steps"])
            self.assertIsNone(missing_result["tool_calls"])
            path = Path(directory) / "events.jsonl"
            path.write_text('{"type":"step-finish","timestamp":NaN,"part":{"type":"step-finish","id":"s"}}\n', encoding="utf-8")
            result = summarize_events(path)

        self.assertEqual(result["availability"], "unavailable")
        self.assertIsNone(result["model_steps"])
        self.assertIsNone(result["event_span_seconds"])

    def test_error_event_without_part_does_not_create_a_false_timestamp_gap(self):
        events = [
            {"type": "error", "timestamp": 1000, "error": {"name": "Retryable"}},
            _event("step-finish", 3000, {"type": "step-finish", "id": "step"}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = summarize_events(path)

        self.assertEqual(result["availability"], "available")
        self.assertEqual(result["coverage"]["event_timestamps"], "complete")
        self.assertEqual(result["event_span_seconds"], 2.0)

    def test_failed_tool_with_a_finite_terminal_interval_keeps_measured_union(self):
        events = [
            _event("step-start", 1000, {"type": "step-start", "id": "step"}),
            _event("tool", 2000, {
                "type": "tool", "id": "tool", "state": {
                    "status": "error", "time": {"start": 2000, "end": 5000}
                }
            }),
            _event("step-finish", 6000, {"type": "step-finish", "id": "step"}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = summarize_events(path)

        self.assertEqual(result["availability"], "available")
        self.assertEqual(result["coverage"]["tool_timestamps"], "complete")
        self.assertEqual(result["tool_execution_seconds"], 3.0)
        self.assertEqual(result["non_tool_seconds"], 2.0)

    def test_running_tool_update_is_completed_by_a_later_record_with_the_same_id(self):
        events = [
            _event("step-start", 1000, {"type": "step-start", "id": "step"}),
            _event("tool", 2000, {"type": "tool", "id": "tool", "state": {"status": "running"}}),
            _event("tool", 3000, {
                "type": "tool", "id": "tool", "state": {
                    "status": "completed", "time": {"start": 2000, "end": 5000}
                }
            }),
            _event("step-finish", 6000, {"type": "step-finish", "id": "step"}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = summarize_events(path)

        self.assertEqual(result["availability"], "available")
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["tool_execution_seconds"], 3.0)


if __name__ == "__main__":
    unittest.main()
