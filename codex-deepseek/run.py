"""Run an explicitly delegated task with Codex and the direct DeepSeek API."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--prompt-file', type=Path, required=True)
    parser.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    base = Path.home() / '.local' / 'share' / 'codex-deepseek'
    binary = shutil.which('codex')
    if not binary:
        parser.error('Install the official Codex CLI first')
    if not (base / 'home' / 'config.toml').is_file():
        parser.error('Complete the isolated setup in README.md first')
    env = os.environ.copy()
    key = env.get('DEEPSEEK_API_KEY')
    if not key:
        key = (base / 'api-key').read_text(encoding='utf-8').strip()
    if not key:
        parser.error('A direct DeepSeek API key is required')
    env['DEEPSEEK_API_KEY'] = key
    env['CODEX_HOME'] = str(base / 'home')
    command = [binary, 'exec', '--ephemeral', '--json', '--skip-git-repo-check',
               '-C', str(args.repo.resolve()), '-s',
               'read-only' if args.read_only else 'workspace-write', '-']
    result = subprocess.run(command, env=env,
                            input=args.prompt_file.read_text(encoding='utf-8'), text=True)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
