"""Offline acceptance tests for the managed worker installer."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import install  # noqa: E402


class WorkerInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="worker-install-tests-")
        self.tmp = Path(self.temp_dir.name).resolve()
        self.package = self.tmp / "package"
        self.base = self.tmp / "worker-state"
        self.codex_home = self.tmp / "codex-home"
        self.skill_root = self.tmp / "skills"
        self.package_scripts = self.package / "scripts"
        self.package_scripts.mkdir(parents=True)
        self.base.mkdir()
        self.codex_home.mkdir()

        (self.package / "README.md").write_text("worker README v1\n", encoding="utf-8")
        (self.package / "SKILL.md").write_text(
            "worker={{WORKER_PYTHON}}\nentry={{WORKER_ENTRYPOINT}}\nreadme={{WORKER_README}}\n",
            encoding="utf-8",
        )
        (self.package_scripts / "worker_fixture.py").write_text(
            "VERSION = 'v1'\n", encoding="utf-8"
        )
        entrypoint = self.package_scripts / "openrouter-worker"
        entrypoint.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        entrypoint.chmod(0o755)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _install(self, *, check=False):
        return install.install(
            self.package,
            self.base,
            self.codex_home,
            self.skill_root,
            check=check,
        )

    def _managed_paths(self):
        return [
            self.base / "worker_fixture.py",
            self.base / "openrouter-worker",
            self.base / "README.md",
            self.skill_root / "opencode-worker" / "SKILL.md",
            self.base / "installation.json",
            self.codex_home / "AGENTS.md",
        ]

    def _snapshot(self, paths):
        snapshot = {}
        for path in paths:
            if path.exists():
                snapshot[path] = (True, path.read_bytes())
            else:
                snapshot[path] = (False, None)
        return snapshot

    def test_fresh_install_renders_package_and_records_managed_hashes(self):
        summary = self._install()

        self.assertEqual(summary["status"], "installed")
        self.assertEqual((self.base / "worker_fixture.py").read_text(encoding="utf-8"), "VERSION = 'v1'\n")
        self.assertEqual((self.base / "README.md").read_text(encoding="utf-8"), "worker README v1\n")
        skill = (self.skill_root / "opencode-worker" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(str(self.base / "openrouter-worker"), skill)
        self.assertIn(str(self.base / "README.md"), skill)
        self.assertIn(sys.executable, skill)
        if os.name != 'nt':
            self.assertEqual((self.base / "openrouter-worker").stat().st_mode & 0o777, 0o700)

        settings = json.loads((self.base / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("default_model", settings)
        self.assertEqual(settings["execution_limits"]["max_model_steps"], 100)
        self.assertEqual(settings["execution_limits"]["max_wall_seconds"], 3600)
        self.assertEqual(settings["execution_limits"]["max_repair_attempts"], 2)
        self.assertTrue((self.base / "installation.json").is_file())
        manifest = json.loads((self.base / "installation.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], install.VERSION)
        for path in self._managed_paths()[:-2]:
            self.assertEqual(
                manifest["files_sha256"][str(path.resolve())],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        agents = (self.codex_home / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(install.START, agents)
        self.assertIn(install.END, agents)

    def test_repeat_update_uses_managed_hash_and_preserves_user_state(self):
        self._install()
        settings_path = self.base / "settings.json"
        settings_path.write_text(
            json.dumps({"default_model": "user/model", "custom": "keep"}) + "\n",
            encoding="utf-8",
        )
        history_path = self.base / "runs.sqlite3"
        history_path.write_bytes(b"history-bytes")
        private_path = self.base / "runs" / "old-run" / "report.json"
        private_path.parent.mkdir(parents=True)
        private_path.write_bytes(b"private-run-report")
        agents_path = self.codex_home / "AGENTS.md"
        agents_path.write_text(
            "# Personal instructions\nKeep this line.\n" + agents_path.read_text(encoding="utf-8") + "\n# Tail\nKeep tail.\n",
            encoding="utf-8",
        )
        user_snapshot = self._snapshot([settings_path, history_path, private_path])

        (self.package_scripts / "worker_fixture.py").write_text(
            "VERSION = 'v2'\n", encoding="utf-8"
        )
        (self.package / "README.md").write_text("worker README v2\n", encoding="utf-8")
        summary = self._install()

        self.assertEqual(summary["status"], "installed")
        self.assertEqual((self.base / "worker_fixture.py").read_text(encoding="utf-8"), "VERSION = 'v2'\n")
        self.assertEqual((self.base / "README.md").read_text(encoding="utf-8"), "worker README v2\n")
        self.assertEqual(self._snapshot([settings_path, history_path, private_path]), user_snapshot)
        agents = agents_path.read_text(encoding="utf-8")
        self.assertIn("# Personal instructions\nKeep this line.", agents)
        self.assertIn("# Tail\nKeep tail.", agents)
        self.assertEqual(agents.count(install.START), 1)
        self.assertEqual(agents.count(install.END), 1)
        backups = list((self.base / "backups").iterdir())
        self.assertTrue(backups)

    def test_exact_legacy_openrouter_section_is_migrated_and_other_content_survives(self):
        agents_path = self.codex_home / "AGENTS.md"
        agents_path.write_text(
            "# Before\nKeep before.\n\n"
            "# OpenRouter coding delegation\n"
            "Use codex-openrouter/README.md for delegated coding.\n"
            "Old managed instructions.\n\n"
            "# After\nKeep after.\n",
            encoding="utf-8",
        )
        self._install()

        agents = agents_path.read_text(encoding="utf-8")
        self.assertIn("# Before\nKeep before.", agents)
        self.assertIn("# After\nKeep after.", agents)
        self.assertNotIn("# OpenRouter coding delegation", agents)
        self.assertNotIn("codex-openrouter/README.md", agents)
        self.assertIn(install.START, agents)
        self.assertIn(str(self.base / "README.md"), agents)
        self.assertEqual(agents.count(install.START), 1)
        self.assertEqual(agents.count(install.END), 1)

    def test_edited_managed_file_is_rejected_before_any_write(self):
        self._install()
        managed = self.base / "worker_fixture.py"
        managed.write_text("LOCAL EDIT\n", encoding="utf-8")
        settings_path = self.base / "settings.json"
        history_path = self.base / "runs.sqlite3"
        history_path.write_bytes(b"history")
        agents_path = self.codex_home / "AGENTS.md"
        snapshot_paths = self._managed_paths() + [settings_path, history_path]
        before = self._snapshot(snapshot_paths)
        backup_root = self.base / "backups"
        backup_before = sorted(path.name for path in backup_root.iterdir()) if backup_root.exists() else []

        with self.assertRaises(install.InstallError):
            self._install()

        self.assertEqual(self._snapshot(snapshot_paths), before)
        backup_after = sorted(path.name for path in backup_root.iterdir()) if backup_root.exists() else []
        self.assertEqual(backup_after, backup_before)
        self.assertEqual(agents_path.read_bytes(), before[agents_path][1])

    def test_check_mode_validates_without_writing_or_creating_settings(self):
        summary = self._install(check=True)

        self.assertEqual(summary["status"], "checked")
        self.assertFalse((self.base / "installation.json").exists())
        self.assertFalse((self.base / "settings.json").exists())
        self.assertFalse((self.base / "worker_fixture.py").exists())
        self.assertFalse((self.codex_home / "AGENTS.md").exists())

    def test_neutral_entrypoint_and_go_defaults_are_installed_with_legacy_alias(self):
        (self.package_scripts / 'opencode-worker').write_text('#!/bin/sh\nexit 0\n')
        summary = self._install()
        self.assertEqual(summary['entrypoint'], str(self.base / 'opencode-worker'))
        self.assertTrue((self.base / 'openrouter-worker').is_file())
        settings = json.loads((self.base / 'settings.json').read_text())
        self.assertEqual(settings['default_provider'], 'opencode-go')
        self.assertEqual(settings['allowed_providers'], ['opencode-go'])
        self.assertEqual(settings['default_model'], 'opencode-go/deepseek-v4.1-flash')

    def test_active_worker_prevents_install_before_any_managed_write(self):
        run = self.base / 'runs' / '11111111-1111-4111-8111-111111111111'
        run.mkdir(parents=True)
        (run / 'report.json').write_text(json.dumps({'run_id': run.name, 'status': 'running', 'finalized': False,
                                                   'launcher_pid': os.getpid()}))
        with self.assertRaises(install.InstallError):
            self._install()
        self.assertFalse((self.base / 'installation.json').exists())


if __name__ == "__main__":
    unittest.main()
