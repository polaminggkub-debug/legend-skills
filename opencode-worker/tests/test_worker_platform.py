"""Offline tests for the cross-platform worker platform seam."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
import uuid
import ctypes
from unittest import mock
from types import SimpleNamespace
NativePath = type(Path())


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import worker_platform  # noqa: E402


class PlatformDirectoryTests(unittest.TestCase):
    def test_explicit_worker_home_wins_on_every_platform(self):
        platform = SimpleNamespace(name="nt", environ={"OPENROUTER_WORKER_HOME": "/tmp/explicit-worker"})
        with mock.patch.object(worker_platform, "os", platform):
            self.assertEqual(worker_platform.default_base_dir(), NativePath("/tmp/explicit-worker"))

    def test_windows_uses_local_appdata_when_no_explicit_home(self):
        platform = SimpleNamespace(name="nt", environ={"LOCALAPPDATA": "/tmp/local-app-data"})
        with mock.patch.object(worker_platform, "os", platform):
            self.assertEqual(worker_platform.default_base_dir(),
                             NativePath("/tmp/local-app-data") / "OpenRouterWorker")

    def test_posix_uses_private_local_share_directory(self):
        with mock.patch.object(worker_platform, "os", SimpleNamespace(name="posix", environ={})):
            with mock.patch.object(worker_platform.Path, "home", return_value=NativePath("/tmp/user")):
                self.assertEqual(worker_platform.default_base_dir(),
                                 NativePath("/tmp/user/.local/share/codex-openrouter"))


class CredentialTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Native Windows Credential Manager integration')
    def test_native_windows_roundtrip_uses_only_an_ephemeral_fixture_target(self):
        target = 'opencode-worker-test-' + uuid.uuid4().hex
        value = 'fixture-not-a-provider-key-ทดสอบ'
        with mock.patch.object(worker_platform, '_WINDOWS_CREDENTIAL_TARGET', target):
            try:
                worker_platform._write_windows_credential(value)
                self.assertEqual(worker_platform._read_windows_credential(), value)
            finally:
                library = worker_platform._advapi32()
                library.CredDeleteW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
                library.CredDeleteW.restype = ctypes.c_int
                library.CredDeleteW(target, 1, 0)

    def test_environment_key_takes_precedence_without_backend_access(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-secret"}, clear=True):
            with mock.patch.object(worker_platform, "_read_macos_keychain") as mac:
                with mock.patch.object(worker_platform, "_read_windows_credential") as windows:
                    self.assertEqual(worker_platform.read_key(), "env-secret")
                    mac.assert_not_called()
                    windows.assert_not_called()

    def test_macos_keychain_read_and_write_use_fixed_service_and_account(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(worker_platform.os, "name", "posix"):
                with mock.patch.object(worker_platform.sys, "platform", "darwin"):
                    with mock.patch.object(worker_platform.getpass, "getuser", return_value="fixture-user"):
                        with mock.patch.object(worker_platform, "_read_macos_keychain", return_value="keychain-secret") as read:
                            self.assertEqual(worker_platform.read_key(), "keychain-secret")
                            read.assert_called_once_with("fixture-user")
                        with mock.patch.object(worker_platform, "_write_macos_keychain") as write:
                            worker_platform.store_key("new-secret")
                            write.assert_called_once_with("fixture-user", "new-secret")

    def test_unavailable_credential_store_is_actionable_and_secret_free(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(worker_platform.os, "name", "posix"):
                with mock.patch.object(worker_platform.sys, "platform", "linux"):
                    with self.assertRaises(worker_platform.CredentialStoreUnavailable) as raised:
                        worker_platform.read_key()
                    self.assertIn("OPENROUTER_API_KEY", str(raised.exception))
                    self.assertNotIn("secret", str(raised.exception).lower())
                    with self.assertRaises(worker_platform.CredentialStoreUnavailable):
                        worker_platform.store_key("secret")

    def test_windows_credential_dispatch_is_separate_from_posix_backend(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(worker_platform.os, "name", "nt"):
                with mock.patch.object(worker_platform, "_read_windows_credential", return_value="windows-secret") as read:
                    self.assertEqual(worker_platform.read_key(), "windows-secret")
                    read.assert_called_once_with()
                with mock.patch.object(worker_platform, "_write_windows_credential") as write:
                    worker_platform.store_key("new-secret")
                    write.assert_called_once_with("new-secret")


class LockTests(unittest.TestCase):
    def test_posix_lock_is_nonblocking_and_releases_on_close(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "worker.lock"
            first = worker_platform.RepositoryLock(path)
            first.acquire()
            second = worker_platform.RepositoryLock(path)
            try:
                with self.assertRaises(BlockingIOError):
                    second.acquire()
            finally:
                second.close()
            first.close()

            third = worker_platform.RepositoryLock(path)
            try:
                third.acquire()
            finally:
                third.close()

    def test_lock_context_manager_closes_handle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "worker.lock"
            with worker_platform.RepositoryLock(path) as lock:
                self.assertIs(lock, lock)
                self.assertFalse(lock.closed)
            self.assertTrue(lock.closed)


class ProcessTests(unittest.TestCase):
    def test_process_options_selects_process_group_isolation(self):
        with mock.patch.object(worker_platform.os, "name", "posix"):
            self.assertEqual(worker_platform.process_options(), {"start_new_session": True})
        with mock.patch.object(worker_platform.os, "name", "nt"):
            with mock.patch.object(worker_platform.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200, create=True):
                self.assertEqual(
                    worker_platform.process_options(),
                    {"creationflags": 0x200},
                )

    def test_windows_stop_uses_taskkill_tree_without_shell(self):
        process = mock.Mock(pid=4242)
        process.poll.return_value = None
        with mock.patch.object(worker_platform.os, "name", "nt"):
            with mock.patch.object(worker_platform.subprocess, "run") as run:
                worker_platform.stop_process(process)
                run.assert_called_once_with(
                    ["taskkill", "/PID", "4242", "/T", "/F"],
                    check=False,
                    stdout=worker_platform.subprocess.DEVNULL,
                    stderr=worker_platform.subprocess.DEVNULL,
                )

    def test_posix_stop_terminates_then_kills_process_group(self):
        process = mock.Mock(pid=4242)
        process.poll.side_effect = [None, None, 9]
        process.wait.side_effect = [subprocess.TimeoutExpired("fixture", 1), 9]
        with mock.patch.object(worker_platform.os, "name", "posix"), mock.patch.object(signal, "SIGKILL", 9, create=True):
            with mock.patch.object(worker_platform.os, "getpgid", return_value=4242, create=True):
                with mock.patch.object(worker_platform.os, "killpg", create=True) as killpg:
                    worker_platform.stop_process(process)
                    self.assertEqual(
                        killpg.call_args_list,
                        [mock.call(4242, signal.SIGTERM), mock.call(4242, signal.SIGKILL)],
                    )


class CommandTests(unittest.TestCase):
    def test_python_fixture_is_invoked_without_a_shell(self):
        command = worker_platform.cli_command(Path("fixture script.py"))
        self.assertEqual(command, [sys.executable, "fixture script.py"])

    def test_native_path_is_a_single_argv_entry(self):
        executable = Path("/opt/OpenCode/opencode")
        self.assertEqual(worker_platform.cli_command(executable), [str(executable)])

    def test_verified_npm_cmd_prefers_node_and_adjacent_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shim = root / "node_modules" / ".bin" / "opencode.cmd"
            launcher = root / "node_modules" / "opencode-ai" / "bin" / "opencode"
            shim.parent.mkdir(parents=True)
            launcher.parent.mkdir(parents=True)
            shim.write_text(
                '@echo off\nnode "%~dp0\\..\\opencode-ai\\bin\\opencode" %*\n',
                encoding="utf-8",
            )
            launcher.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            with mock.patch.object(worker_platform.shutil, "which", return_value="/usr/local/bin/node"):
                self.assertEqual(
                    worker_platform.cli_command(shim),
                    ["/usr/local/bin/node", str(launcher)],
                )

    def test_unverified_cmd_does_not_get_interpreted_as_a_script(self):
        with tempfile.TemporaryDirectory() as directory:
            shim = Path(directory) / "opencode.cmd"
            shim.write_text("@echo off\necho unrelated\n", encoding="utf-8")
            with mock.patch.object(worker_platform.shutil, "which", return_value="/usr/local/bin/node"):
                with self.assertRaises(ValueError):
                    worker_platform.cli_command(shim)

    def test_bat_does_not_get_interpreted_as_a_script(self):
        with tempfile.TemporaryDirectory() as directory:
            shim = Path(directory) / "check.bat"
            shim.write_text("@echo off\necho unrelated\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                worker_platform.cli_command(shim)

    def test_npm_cmd_prefers_nearby_npm_cli_js_and_node(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shim = root / "nodejs" / "npm.cmd"
            npm_cli = root / "nodejs" / "node_modules" / "npm" / "bin" / "npm-cli.js"
            shim.parent.mkdir(parents=True)
            npm_cli.parent.mkdir(parents=True)
            shim.write_text(
                '@echo off\nnode "%~dp0\\node_modules\\npm\\bin\\npm-cli.js" %*\n',
                encoding="utf-8",
            )
            npm_cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            with mock.patch.object(worker_platform.shutil, "which", return_value="/usr/local/bin/node"):
                self.assertEqual(
                    worker_platform.cli_command(shim),
                    ["/usr/local/bin/node", str(npm_cli)],
                )


if __name__ == "__main__":
    unittest.main()
