"""Focused policy tests for bounded build/check repair feedback."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker_repairs import (  # noqa: E402
    failure_signature,
    feedback_text,
    no_progress,
    repair_prompt,
    repair_targets,
)


class RepairPolicyTests(unittest.TestCase):
    def test_only_required_nonzero_command_exit_is_eligible(self):
        results = [
            {"id": "build", "kind": "build", "stage": "before_commit", "required": True,
             "status": "failed", "exit_code": 2, "error": "command exited with status 2"},
            {"id": "optional", "required": False, "status": "failed", "exit_code": 2},
            {"id": "timeout", "required": True, "status": "timed_out", "exit_code": None},
            {"id": "launch", "required": True, "status": "failed", "exit_code": 1,
             "error_type": "FileNotFoundError"},
            {"id": "guard", "required": True, "status": "budget_exceeded", "exit_code": 1},
        ]
        targets = repair_targets(results)
        self.assertEqual([target.identifier for target in targets], ["build"])
        self.assertEqual(targets[0].argv, ())

    def test_same_failure_and_same_source_tree_is_no_progress(self):
        result = {"id": "test", "kind": "test", "stage": "after_commit", "required": True,
                  "status": "failed", "exit_code": 7}
        signature = failure_signature(repair_targets([result]))
        self.assertTrue(no_progress(signature, "tree-a", signature, "tree-a"))
        self.assertFalse(no_progress(signature, "tree-a", signature, "tree-b"))
        self.assertFalse(no_progress(signature, "tree-a", "different", "tree-a"))

    def test_feedback_is_bounded_and_prompt_keeps_task_instructions(self):
        with tempfile.TemporaryDirectory() as directory:
            stderr = Path(directory) / "stderr.log"
            stderr.write_text("ข้อมูลวินิจฉัย\n" * 2000, encoding="utf-8")
            result = {"id": "build", "kind": "build", "stage": "before_commit", "required": True,
                      "status": "failed", "exit_code": 2, "argv": ["make", "build"],
                      "stderr_path": str(stderr)}
            targets = repair_targets([result])
            feedback = feedback_text(targets, max_bytes=2048)
            self.assertLessEqual(len(feedback.encode("utf-8")), 2048)
            prompt = repair_prompt("make the game", targets, attempt=1, remaining_attempts=1,
                                   max_feedback_bytes=2048)
            self.assertIn("make the game", prompt)
            self.assertIn("bounded repair attempt 1", prompt)
            self.assertIn("make build", prompt)


if __name__ == "__main__":
    unittest.main()
