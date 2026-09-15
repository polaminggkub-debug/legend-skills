"""Opt-in installed CLI compatibility probe. No prompt or provider request."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import tempfile
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from worker_platform import cli_command
from worker_runtime import child_environment


@unittest.skipUnless(os.environ.get('OPENCODE_WORKER_TEST_CLI') == '1',
                     'Opt-in official OpenCode CLI probe')
class OfficialCliTests(unittest.TestCase):
    def test_explicit_instructions_survive_isolated_project_config(self):
        with tempfile.TemporaryDirectory(prefix='opencode-config-probe-') as directory:
            base = Path(directory).resolve()
            run_dir = base / 'run'
            run_dir.mkdir()
            instructions = run_dir / 'instructions.md'
            instructions.write_text('Use the provided project checks.\n', encoding='utf-8')
            env = child_environment(base, 'openrouter/deepseek/deepseek-v4.1-flash',
                                    'synthetic-unused-key', run_dir, instructions)
            output = base / 'resolved-config.json'
            with output.open('wb') as stream:
                subprocess.run(cli_command(shutil.which('opencode')) + ['--pure', 'debug', 'config'],
                               cwd=base, env=env, stdout=stream, stderr=subprocess.PIPE,
                               check=True, timeout=30)
            config = json.loads(output.read_text(encoding='utf-8'))
            self.assertIn(instructions.as_posix(), config['instructions'])
            self.assertEqual(config['model'], 'openrouter/deepseek/deepseek-v4.1-flash')

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
