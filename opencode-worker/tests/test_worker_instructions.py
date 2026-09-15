"""Offline tests for scoped project guidance and OpenCode isolation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import worker_runtime  # noqa: E402


class WorkerInstructionTests(unittest.TestCase):
    def test_inherits_root_and_nested_guidance_in_scope_order_without_siblings(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            target = repo / "src" / "app"
            sibling = repo / "other"
            target.mkdir(parents=True)
            sibling.mkdir()
            (repo / "AGENTS.md").write_text("root guidance\n", encoding="utf-8")
            (repo / "src" / "CLAUDE.md").write_text("src fallback guidance\n", encoding="utf-8")
            (target / "AGENTS.md").write_text("target guidance\n", encoding="utf-8")
            (sibling / "AGENTS.md").write_text("sibling must not load\n", encoding="utf-8")
            run_dir = Path(directory) / "run"
            run_dir.mkdir()

            snapshot, metadata = worker_runtime.prepare_instructions(repo, target, run_dir)

            self.assertIsNotNone(snapshot)
            self.assertEqual(
                [item["path"] for item in metadata["files"]],
                ["AGENTS.md", "src/CLAUDE.md", "src/app/AGENTS.md"],
            )
            content = snapshot.read_text(encoding="utf-8")
            self.assertLess(content.index("root guidance"), content.index("src fallback guidance"))
            self.assertLess(content.index("src fallback guidance"), content.index("target guidance"))
            self.assertNotIn("sibling must not load", content)
            if os.name != 'nt':
                self.assertEqual(snapshot.stat().st_mode & 0o777, 0o600)

    def test_uses_claude_then_context_fallback_when_agents_is_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            target = repo / "nested"
            target.mkdir(parents=True)
            (repo / "CLAUDE.md").write_text("root Claude guidance\n", encoding="utf-8")
            (repo / "CONTEXT.md").write_text("root context must lose\n", encoding="utf-8")
            (target / "CONTEXT.md").write_text("nested context guidance\n", encoding="utf-8")
            run_dir = Path(directory) / "run"
            run_dir.mkdir()

            snapshot, metadata = worker_runtime.prepare_instructions(repo, target, run_dir)

            self.assertEqual(
                [item["path"] for item in metadata["files"]],
                ["CLAUDE.md", "nested/CONTEXT.md"],
            )
            content = snapshot.read_text(encoding="utf-8")
            self.assertIn("root Claude guidance", content)
            self.assertIn("nested context guidance", content)
            self.assertNotIn("root context must lose", content)

    def test_rejects_oversized_and_outside_repository_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = (root / "repo").resolve()
            repo.mkdir()
            run_dir = root / "run"
            run_dir.mkdir()
            (repo / "AGENTS.md").write_bytes(b"x" * (128 * 1024 + 1))
            with self.assertRaises(worker_runtime.GuardrailError):
                worker_runtime.prepare_instructions(repo, repo, run_dir)

            bounded_repo = (root / "escape-repo").resolve()
            target = bounded_repo / "src"
            target.mkdir(parents=True)
            outside = root / "outside-guidance.md"
            outside.write_text("outside guidance\n", encoding="utf-8")
            link = target / "AGENTS.md"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable on this platform")
            with self.assertRaises(worker_runtime.GuardrailError):
                worker_runtime.prepare_instructions(bounded_repo, target, run_dir)

    def test_child_environment_uses_absolute_snapshot_and_isolates_global_config(self):
        model = "openrouter/deepseek/deepseek-v4.1-flash"
        key = "synthetic-worker-key"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = (root / "repo").resolve()
            repo.mkdir()
            (repo / "AGENTS.md").write_text("follow local rules\n", encoding="utf-8")
            run_dir = root / "run"
            run_dir.mkdir()
            snapshot, metadata = worker_runtime.prepare_instructions(repo, repo, run_dir)
            self.assertIsNotNone(snapshot)

            with mock.patch.dict(
                os.environ,
                {
                    "OPENCODE_CONFIG_CONTENT": "ambient-config",
                    "OPENCODE_UNRELATED": "ambient-setting",
                    "GIT_DIR": "ambient-git",
                    "OPENROUTER_API_KEY": "ambient-key",
                },
                clear=False,
            ):
                env = worker_runtime.child_environment(root / "base", model, key, run_dir, snapshot)

            config = json.loads(env["OPENCODE_CONFIG_CONTENT"])
            self.assertEqual(config["model"], model)
            self.assertEqual(config["small_model"], model)
            self.assertEqual(config["instructions"], [snapshot.resolve().as_posix()])
            self.assertTrue(Path(config["instructions"][0]).is_absolute())
            self.assertEqual(env["OPENCODE_DISABLE_PROJECT_CONFIG"], "true")
            self.assertEqual(env["OPENCODE_DISABLE_EXTERNAL_SKILLS"], "true")
            self.assertEqual(env["OPENCODE_DISABLE_CLAUDE_CODE"], "true")
            self.assertNotIn("OPENCODE_UNRELATED", env)
            self.assertNotIn("GIT_DIR", env)
            self.assertEqual(env["OPENROUTER_API_KEY"], key)
            self.assertNotIn(key, snapshot.read_text(encoding="utf-8"))
            self.assertNotIn(key, json.dumps(metadata))


if __name__ == "__main__":
    unittest.main()
