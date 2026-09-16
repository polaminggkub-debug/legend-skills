import json
import math
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from worker_metrics import parse_events, validate_report
from worker_provider import resolve_selection


def _record(kind, *, session="session-1", part=None, timestamp=1):
    payload = {"type": kind, "timestamp": timestamp, "sessionID": session}
    payload["part"] = {"type": kind, **(part or {})}
    return payload


def _finish(step_id, *, reason="tool-calls", cost=0.25, tokens=None, session="session-1"):
    token_values = tokens or {
        "total": 10,
        "input": 2,
        "output": 3,
        "reasoning": 1,
        "cache": {"read": 4, "write": 0},
    }
    return _record(
        "step-finish",
        session=session,
        part={"id": step_id, "reason": reason, "tokens": token_values, "cost": cost},
    )


def _write_events(path, events):
    path.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")


class ParseEventsTests(unittest.TestCase):
    def test_partial_accounting_retains_completed_steps_but_cannot_pass_success_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            _write_events(path, [_finish('step-1')])
            with self.assertRaises(ValueError):
                parse_events(path)
            result = parse_events(path, allow_partial=True)
            self.assertEqual(result['tokens']['total'], 10)
            self.assertEqual(result['estimated_cost_usd'], 0.25)
            self.assertFalse(result['completed'])
            self.assertEqual(result['accounting_scope'], 'partial_completed_steps')
            with path.open('ab') as stream:
                stream.write(b'{"unfinished":')
            self.assertEqual(parse_events(path, allow_partial=True)['tokens']['total'], 10)

    def test_strict_rejects_step_started_after_terminal_but_partial_keeps_prior_usage(self):
        terminal = _finish('step-1', reason='stop')
        duplicate_terminal = json.loads(json.dumps(terminal))
        duplicate_terminal['timestamp'] = 999
        events = [
            terminal,
            duplicate_terminal,
            _record('step-start', part={'id': 'step-2'}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            _write_events(path, events)
            with self.assertRaises(ValueError):
                parse_events(path)
            result = parse_events(path, allow_partial=True)

        self.assertEqual(result['model_steps'], 1)
        self.assertEqual(result['tokens']['total'], 10)
        self.assertEqual(result['estimated_cost_usd'], 0.25)
        self.assertFalse(result['completed'])
        self.assertEqual(result['event_counts']['step_finish'], 1)
        self.assertEqual(result['event_counts']['step_start'], 1)

    def test_partial_accounting_does_not_ignore_corrupt_completed_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            _write_events(path, [_finish('step-1')])
            with path.open('ab') as stream:
                stream.write(b'broken\n')
            with self.assertRaises(ValueError):
                parse_events(path, allow_partial=True)

    def test_aggregates_steps_and_tools_and_deduplicates_step_records(self):
        first = _finish("step-1")
        duplicate = json.loads(json.dumps(first))
        duplicate["timestamp"] = 999
        events = [
            _record("step-start", part={"id": "step-1"}),
            _record("tool", part={"id": "tool-1", "tool": "edit"}),
            first,
            duplicate,
            _record("step-start", part={"id": "step-2"}),
            _record("text", part={"id": "text-1", "text": "done"}),
            _finish(
                "step-2",
                reason="stop",
                cost=0.5,
                tokens={
                    "total": 5,
                    "input": 1,
                    "output": 1,
                    "reasoning": 1,
                    "cache": {"read": 2, "write": 0},
                },
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = parse_events(path)

        self.assertEqual(result["session_id"], "session-1")
        self.assertEqual(result["model_steps"], 2)
        self.assertEqual(
            result["tokens"],
            {
                "total": 15,
                "input": 3,
                "output": 4,
                "reasoning": 2,
                "cache_read": 6,
                "cache_write": 0,
            },
        )
        self.assertTrue(math.isclose(result["estimated_cost_usd"], 0.75))
        self.assertEqual(
            result["event_counts"],
            {"step_start": 2, "tool_use": 1, "step_finish": 2, "text": 1},
        )
        self.assertEqual(result["tool_counts"], {"edit": 1})
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["telemetry_errors"], [])
        self.assertTrue(result["completed"])

    def test_collects_error_names_without_error_payloads(self):
        events = [
            _record(
                "error",
                part={"error": {"name": "TimeoutError", "message": "secret detail"}},
            ),
            _record(
                "telemetry-error",
                part={"error": {"name": "UsageUnavailable", "message": "secret detail"}},
            ),
            _finish("step-1", reason="stop"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, events)
            result = parse_events(path)

        self.assertEqual(result["errors"], ["TimeoutError"])
        self.assertEqual(result["telemetry_errors"], ["UsageUnavailable"])

    def test_rejects_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text('{"type":"step-finish"}\nnot-json\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_events(path)

    def test_rejects_missing_token_component_and_cost(self):
        event = _finish("step-1", reason="stop")
        del event["part"]["tokens"]["cache"]["read"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [event])
            with self.assertRaises(ValueError):
                parse_events(path)

        event = _finish("step-1", reason="stop")
        del event["part"]["cost"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [event])
            with self.assertRaises(ValueError):
                parse_events(path)

    def test_rejects_nonfinite_values_and_inconsistent_total(self):
        event = _finish("step-1", reason="stop", cost=float("nan"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [event])
            with self.assertRaises(ValueError):
                parse_events(path)

        event = _finish("step-1", reason="stop")
        event["part"]["tokens"]["total"] = 11
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [event])
            with self.assertRaises(ValueError):
                parse_events(path)

    def test_rejects_conflicting_duplicate_steps(self):
        first = _finish("step-1", reason="stop")
        second = _finish("step-1", reason="stop", cost=0.5)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [first, second])
            with self.assertRaises(ValueError):
                parse_events(path)

    def test_rejects_multiple_sessions_and_missing_terminal_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [_finish("step-1", reason="stop"), _finish("step-2", session="session-2")])
            with self.assertRaises(ValueError):
                parse_events(path)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write_events(path, [_finish("step-1", reason="tool-calls")])
            with self.assertRaises(ValueError):
                parse_events(path)


def _valid_report():
    metrics = {
        "session_id": "session-1",
        "model_steps": 1,
        "tokens": {
            "total": 10,
            "input": 2,
            "output": 3,
            "reasoning": 1,
            "cache_read": 4,
            "cache_write": 0,
        },
        "estimated_cost_usd": 0.25,
        "event_counts": {"step_finish": 1},
        "tool_counts": {"edit": 1},
        "errors": [],
        "completed": True,
        "telemetry_errors": [],
    }
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "status": "ready_to_commit",
        "started_at": "2026-09-15T00:00:00Z",
        "finished_at": "2026-09-15T00:00:01Z",
        "elapsed_seconds": 1.0,
        "engine": "OpenCode",
        "provider": "OpenRouter",
        "opencode_version": "1.0.0",
        "requested_model": "openrouter/deepseek/deepseek-chat-v3-0324:free",
        "observed_models": ["openrouter/deepseek/deepseek-chat-v3-0324:free"],
        "model_evidence": "opencode_message_db",
        "reason_effort": None,
        "metrics": metrics,
        "git": {"base_commit": "abc", "commit": None, "parent_repo": "/repo"},
        "changes": {
            "files": [{"path": "game.js", "insertions": 1, "deletions": 0}],
            "insertions": 1,
            "deletions": 0,
            "binary_files": 0,
        },
        "checks": {"status": "not_verified"},
        "error": None,
    }


class ValidateReportTests(unittest.TestCase):
    def test_accepts_ready_to_commit_report_with_null_commit(self):
        self.assertEqual(validate_report(_valid_report()), [])

    def test_current_reports_require_provider_and_estimate_evidence(self):
        report = _valid_report()
        report.update(launcher_version="4.0.0", provider_id="openrouter",
                      billing_source="provider_managed_unobserved",
                      cost_basis=resolve_selection({"default_provider": "openrouter"})["cost_basis"])
        self.assertEqual(validate_report(report), [])
        for field in ("provider_id", "billing_source", "cost_basis"):
            with self.subTest(field=field):
                damaged = dict(report)
                damaged.pop(field)
                self.assertTrue(any(field in error for error in validate_report(damaged)))
        report["billing_source"] = "zen_balance"
        self.assertTrue(any("billing_source" in error for error in validate_report(report)))

    def test_legacy_reports_without_new_accounting_fields_remain_valid(self):
        report = _valid_report()
        report["launcher_version"] = "3.0.0"
        self.assertEqual(validate_report(report), [])

    def test_rejects_unverifiable_model_attribution(self):
        report = _valid_report()
        report["observed_models"] = []
        report["model_evidence"] = "config_only"
        errors = validate_report(report)
        self.assertTrue(any("observed_models" in error for error in errors))
        self.assertTrue(any("model_evidence" in error for error in errors))

    def test_rejects_invalid_metric_totals(self):
        report = _valid_report()
        report["metrics"]["tokens"]["total"] = 99
        errors = validate_report(report)
        self.assertTrue(any("tokens.total" in error for error in errors))

    def test_rejects_unexpected_observed_model_and_success_errors(self):
        report = _valid_report()
        report["observed_models"].append("openrouter/other/model")
        report["metrics"]["errors"] = ["ProviderError"]
        report["metrics"]["telemetry_errors"] = ["UsageUnavailable"]
        errors = validate_report(report)
        self.assertTrue(any("match requested_model" in error for error in errors))
        self.assertTrue(any("metrics.errors" in error for error in errors))
        self.assertTrue(any("metrics.telemetry_errors" in error for error in errors))

    def test_invalid_token_component_does_not_raise_validator(self):
        report = _valid_report()
        report["metrics"]["tokens"]["input"] = "unknown"
        errors = validate_report(report)
        self.assertTrue(any("metrics.tokens.input" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
