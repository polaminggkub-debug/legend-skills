"""Offline tests for the bounded OpenCode run budget."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker_budget import (  # noqa: E402
    BudgetExceeded,
    DEFAULT_LIMITS,
    RunBudget,
    load_limits,
)


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _event(kind, event_id=None, *, session="session-1", message_id=None, part=None, **fields):
    payload = {"type": kind, "sessionID": session}
    if event_id is not None:
        payload["id"] = event_id
    payload.update(fields)
    nested = {"type": kind}
    if event_id is not None:
        nested["id"] = event_id
    if message_id is not None:
        nested["messageID"] = message_id
    if part:
        nested.update(part)
    payload["part"] = nested
    return payload


def _finish(
    event_id,
    *,
    session="session-1",
    message_id=None,
    total=10,
    cost=0.25,
    reason="stop",
    include_tokens=True,
    include_cost=True,
):
    part = {}
    if include_tokens:
        input_tokens = min(2, total)
        output_tokens = min(3, max(0, total - input_tokens))
        reasoning_tokens = min(1, max(0, total - input_tokens - output_tokens))
        part["tokens"] = {
            "total": total,
            "input": input_tokens,
            "output": output_tokens,
            "reasoning": reasoning_tokens,
            "cache": {"read": max(0, total - input_tokens - output_tokens - reasoning_tokens), "write": 0},
        }
    if include_cost:
        part["cost"] = cost
    part["reason"] = reason
    return _event(
        "step-finish",
        event_id,
        session=session,
        message_id=message_id,
        part=part,
    )


def _tool(
    tool_id,
    *,
    input_value="same input",
    error="same error",
    output=None,
    session="session-1",
    status="error",
    exit_code=None,
):
    state = {"status": status, "input": input_value}
    if error is not None:
        state["error"] = error
    if output is not None:
        state["output"] = output
    if exit_code is not None:
        state["metadata"] = {"exit": exit_code}
    return _event("tool", tool_id, session=session, part={"state": state})


def _write(path: Path, events) -> None:
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


class LimitLoadingTests(unittest.TestCase):
    def test_defaults_and_nested_overrides_are_detached(self):
        settings = {"execution_limits": {"max_model_steps": 4, "max_tokens": 50}}
        limits = load_limits(settings, {"max_wall_seconds": 12})

        self.assertEqual(limits["max_model_steps"], 4)
        self.assertEqual(limits["max_tokens"], 50)
        self.assertEqual(limits["max_wall_seconds"], 12)
        self.assertEqual(limits["max_cost_usd"], DEFAULT_LIMITS["max_cost_usd"])
        limits["max_model_steps"] = 99
        self.assertEqual(settings["execution_limits"]["max_model_steps"], 4)

    def test_rejects_invalid_required_and_optional_limits(self):
        invalid = (
            ("max_model_steps", 0),
            ("max_model_steps", 1.5),
            ("max_wall_seconds", 0),
            ("max_wall_seconds", float("inf")),
            ("check_timeout_seconds", float("nan")),
            ("max_repair_attempts", -1),
            ("max_repair_attempts", 1.0),
            ("max_tokens", -1),
            ("max_tokens", 0),
            ("max_cost_usd", 0),
            ("max_cost_usd", float("inf")),
        )
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    load_limits({"execution_limits": {field: value}})

        self.assertIsNone(load_limits({"execution_limits": {"max_tokens": None}})["max_tokens"])
        self.assertIsNone(load_limits({"execution_limits": {"max_cost_usd": None}})["max_cost_usd"])


class RunBudgetTests(unittest.TestCase):
    def test_wall_clock_deadline_is_total_and_stable(self):
        clock = FakeClock()
        budget = RunBudget(
            {"max_wall_seconds": 5, "max_model_steps": 1000},
            clock=clock,
        )
        self.assertEqual(budget.remaining_seconds(), 5)
        clock.advance(4.99)
        budget.check()
        clock.advance(0.01)
        with self.assertRaises(BudgetExceeded) as raised:
            budget.check()
        self.assertEqual(raised.exception.reason, "max_wall_seconds")
        self.assertEqual(budget.snapshot()["stop_reason"], "max_wall_seconds")
        with self.assertRaises(BudgetExceeded) as again:
            budget.check()
        self.assertEqual(again.exception.reason, "max_wall_seconds")

    def test_shared_caps_across_paths_pair_message_ids_and_dedup_records(self):
        clock = FakeClock()
        limits = {
            "max_wall_seconds": 100,
            "max_model_steps": 2,
            "max_tokens": 100,
            "max_cost_usd": 10,
        }
        budget = RunBudget(limits, clock=clock)
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "attempt-1" / "events.jsonl"
            second = Path(directory) / "attempt-2" / "events.jsonl"
            first.parent.mkdir()
            second.parent.mkdir()
            start = _event("step-start", "different-start-id", message_id="message-1")
            finish = _finish("different-finish-id", message_id="message-1", total=10, cost=1)
            _write(first, [start, finish, json.loads(json.dumps(finish))])
            budget.observe(first)
            self.assertEqual(budget.snapshot()["counts"]["model_steps"], 1)
            self.assertEqual(budget.snapshot()["counts"]["tokens"]["total"], 10)

            # This invocation has no start record.  Its finish is counted once
            # as the documented fallback, and the shared step cap then stops.
            _write(second, [_finish("finish-only", session="session-2", total=5, cost=2, reason="tool-calls")])
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(second)
            self.assertEqual(raised.exception.reason, "max_model_steps")
            snapshot = budget.snapshot()
            self.assertEqual(snapshot["counts"]["model_steps"], 2)
            self.assertEqual(snapshot["counts"]["tokens"]["total"], 15)
            self.assertEqual(snapshot["counts"]["cost_usd"], 3.0)

    def test_exact_replay_is_ignored_but_conflicting_finish_is_unavailable(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 10})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            first = _finish("finish-1", message_id="message-1", total=10, cost=0.1)
            replay = json.loads(json.dumps(first))
            replay["timestamp"] = 999
            conflicting = _finish("finish-2", message_id="message-1", total=1000, cost=9)
            _write(path, [first, replay, conflicting])
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "accounting_unavailable")
            self.assertEqual(raised.exception.detail, "conflicting_step_finish")
            self.assertEqual(budget.snapshot()["counts"]["tokens"]["total"], 10)
            self.assertEqual(budget.snapshot()["counts"]["cost_usd"], 0.1)

    def test_repeated_start_identity_is_safe_even_when_record_id_changes(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 10})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            first = _event("step-start", "start-1", message_id="message-1")
            second = _event("step-start", "start-2", message_id="message-1")
            second["timestamp"] = 999
            _write(path, [first, second, _finish("finish-1", message_id="message-1")])
            budget.observe(path)
            self.assertEqual(budget.snapshot()["counts"]["model_steps"], 1)

    def test_empty_present_identity_is_rejected_even_with_message_id(self):
        for mutate in ("part_id", "session"):
            with self.subTest(mutate=mutate):
                budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 10})
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "events.jsonl"
                    event = _finish("finish-1", message_id="message-1")
                    if mutate == "part_id":
                        event["part"]["id"] = ""
                    else:
                        event["sessionID"] = ""
                    _write(path, [event])
                    with self.assertRaises(BudgetExceeded) as raised:
                        budget.observe(path)
                self.assertEqual(raised.exception.reason, "accounting_unavailable")
                self.assertEqual(raised.exception.detail, "step_finish_id")

    def test_partial_json_tail_is_deferred_without_zero_accounting(self):
        budget = RunBudget(
            {
                "max_wall_seconds": 100,
                "max_model_steps": 10,
                "max_tokens": 20,
                "max_cost_usd": 2,
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            serialized_finish = json.dumps(_finish("s1", total=8, cost=0.5))
            split_at = len(serialized_finish) // 2
            path.write_text(
                json.dumps(_event("step-start", "s1")) + "\n" + serialized_finish[:split_at],
                encoding="utf-8",
            )
            budget.observe(path)
            self.assertEqual(budget.snapshot()["counts"]["model_steps"], 1)
            self.assertIsNone(budget.snapshot()["counts"]["tokens"]["total"])
            with path.open("a", encoding="utf-8") as stream:
                stream.write(
                    serialized_finish[split_at:] + "\n"
                )
            budget.observe(path)
            self.assertEqual(budget.snapshot()["counts"]["tokens"]["total"], 8)
            self.assertEqual(budget.snapshot()["counts"]["cost_usd"], 0.5)

    def test_requested_accounting_cap_fails_explicitly_when_evidence_missing(self):
        for field, reason, kwargs in (
            ("max_tokens", "tokens_unavailable", {"include_tokens": False}),
            ("max_cost_usd", "cost_unavailable", {"include_cost": False}),
        ):
            with self.subTest(field=field):
                budget = RunBudget(
                    {"max_wall_seconds": 100, "max_model_steps": 10, field: 20},
                )
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "events.jsonl"
                    _write(path, [_finish("missing", **kwargs)])
                    with self.assertRaises(BudgetExceeded) as raised:
                        budget.observe(path)
                self.assertEqual(raised.exception.reason, reason)
                self.assertIn(field.split("_")[1], raised.exception.detail)

    def test_inconsistent_or_incomplete_token_components_are_unavailable(self):
        for mutate in ("mismatch", "missing_cache"):
            with self.subTest(mutate=mutate):
                budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 10, "max_tokens": 50})
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "events.jsonl"
                    event = _finish("bad-token")
                    if mutate == "mismatch":
                        event["part"]["tokens"]["input"] = 100
                    else:
                        del event["part"]["tokens"]["cache"]["read"]
                    _write(path, [event])
                    with self.assertRaises(BudgetExceeded) as raised:
                        budget.observe(path)
                self.assertEqual(raised.exception.reason, "tokens_unavailable")

    def test_token_and_cache_components_are_accumulated_before_cap(self):
        budget = RunBudget(
            {
                "max_wall_seconds": 100,
                "max_model_steps": 10,
                "max_tokens": 15,
                "max_cost_usd": 10,
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write(
                path,
                [
                    _finish("s1", total=10, cost=0.2),
                    _finish("s2", session="session-2", total=5, cost=0.3),
                ],
            )
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "max_tokens")
            self.assertEqual(
                budget.snapshot()["counts"]["tokens"],
                {"total": 15, "input": 4, "output": 6, "reasoning": 1, "cache_read": 4, "cache_write": 0},
            )

    def test_repair_attempts_are_monotonic_and_bounded(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 100, "max_repair_attempts": 2})
        budget.record_repair_attempt()
        budget.record_repair_attempt()
        with self.assertRaises(BudgetExceeded) as raised:
            budget.check_before_repair()
        self.assertEqual(raised.exception.reason, "max_repair_attempts")
        self.assertEqual(budget.snapshot()["counts"]["repair_attempts"], 2)

    def test_zero_repair_allowance_blocks_before_start_without_checking_completed_count(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 100, "max_repair_attempts": 0})
        budget.check()
        with self.assertRaises(BudgetExceeded) as raised:
            budget.check_before_repair()
        self.assertEqual(raised.exception.reason, "max_repair_attempts")
        self.assertEqual(budget.snapshot()["counts"]["repair_attempts"], 0)

    def test_only_consecutive_identical_failed_tools_trigger(self):
        budget = RunBudget(
            {
                "max_wall_seconds": 100,
                "max_model_steps": 100,
                "max_repeated_tool_failures": 3,
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            first = _tool("tool-1")
            duplicate = json.loads(json.dumps(first))
            _write(path, [first, duplicate, _tool("tool-2"), _tool("tool-3")])
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "max_repeated_tool_failures")
            self.assertEqual(budget.snapshot()["counts"]["repeated_tool_failures"], 3)

    def test_changed_failure_and_successful_repeats_reset_streak(self):
        limits = {"max_wall_seconds": 100, "max_model_steps": 100, "max_repeated_tool_failures": 3}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            budget = RunBudget(limits)
            _write(path, [_tool("a"), _tool("b"), _tool("c", error="changed")])
            budget.observe(path)
            self.assertEqual(budget.snapshot()["counts"]["repeated_tool_failures"], 1)

            # Repeated successful reads carry no failure fingerprint and must
            # never become a false stall signal.
            with path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(_tool("d", status="completed", error=None)) + "\n")
                stream.write(json.dumps(_tool("e", status="completed", error=None)) + "\n")
            budget.observe(path)
            self.assertEqual(budget.snapshot()["counts"]["repeated_tool_failures"], 0)

            # A nonzero metadata exit is a failed tool even with a non-error
            # status, and three identical failures trigger the guard.
            with path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(_tool("f", status="completed", error=None, exit_code=1)) + "\n")
            budget.observe(path)
            with path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(_tool("g", status="completed", error=None, exit_code=1)) + "\n")
                stream.write(json.dumps(_tool("h", status="completed", error=None, exit_code=1)) + "\n")
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "max_repeated_tool_failures")

    def test_terminal_step_at_cap_is_available_for_final_checks_but_blocks_next_call(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 1})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write(path, [_finish("s1", reason="stop")])
            budget.observe(path)
            budget.check()
            with self.assertRaises(BudgetExceeded) as raised:
                budget.check_before_invocation()
            self.assertEqual(raised.exception.reason, "max_model_steps")

    def test_batch_over_cap_stops_even_when_last_finish_is_terminal(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 100})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write(path, [_finish("step-%d" % index, reason="stop") for index in range(101)])
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "max_model_steps")
            self.assertEqual(budget.snapshot()["counts"]["model_steps"], 101)

    def test_observed_stream_truncation_is_an_accounting_gap(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 100})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write(path, [_finish("step-1")])
            budget.observe(path)
            path.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "accounting_unavailable")

    def test_same_inode_rewrite_cannot_skip_changed_consumed_prefix(self):
        budget = RunBudget({"max_wall_seconds": 100, "max_model_steps": 100})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            _write(path, [_finish("old", total=10)])
            inode = path.stat().st_ino
            budget.observe(path)
            _write(path, [_finish("new-1", total=20), _finish("new-2", total=20)])
            self.assertEqual(path.stat().st_ino, inode)
            with self.assertRaises(BudgetExceeded) as raised:
                budget.observe(path)
            self.assertEqual(raised.exception.reason, "accounting_unavailable")
            self.assertEqual(raised.exception.detail, "event_stream_changed")


if __name__ == "__main__":
    unittest.main()
