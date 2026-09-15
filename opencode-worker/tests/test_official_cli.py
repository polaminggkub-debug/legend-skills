"""Opt-in installed CLI compatibility probe. No prompt or provider request."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from worker_platform import cli_command


@unittest.skipUnless(os.environ.get('OPENCODE_WORKER_TEST_CLI') == '1',
                     'Opt-in official OpenCode CLI probe')
class OfficialCliTests(unittest.TestCase):
    def test_official_cli_version_and_required_run_flags(self):
        executable = shutil.which('opencode')
        self.assertIsNotNone(executable, 'Install official opencode-ai@1.18.31 first')
        command = cli_command(executable)
        version = subprocess.run(command + ['--version'], capture_output=True,
                                 text=True, check=True, timeout=30)
        self.assertIn('1.18.31', version.stdout + version.stderr)
        help_result = subprocess.run(command + ['run', '--help'], capture_output=True,
                                     text=True, check=True, timeout=30)
        output = help_result.stdout + help_result.stderr
        for flag in ('--pure', '--auto', '--format', '--model', '--dir'):
            self.assertIn(flag, output)


if __name__ == '__main__':
    unittest.main()
