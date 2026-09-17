"""Install/update the worker and its Codex entrypoint without copying user data."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

from worker_platform import default_base_dir

VERSION = '4.2.0'
START = '<!-- BEGIN OPENCODE-WORKER -->'
END = '<!-- END OPENCODE-WORKER -->'


class InstallError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.install-tmp')
    temp.write_bytes(data)
    temp.replace(path)


def register(text, block, expected=None):
    if START in text or END in text:
        pattern = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
        matches = list(pattern.finditer(text))
        if len(matches) != 1 or text.count(START) != 1 or text.count(END) != 1:
            raise InstallError('Codex registration markers are malformed; existing instructions were preserved')
        previous = matches[0].group()
        if expected and digest(previous.encode('utf-8')) != expected:
            raise InstallError('The worker registration was edited locally; reconcile it before updating')
        return text[:matches[0].start()] + block + text[matches[0].end():]
    # Migrate this worker's original, narrowly named registration only.
    legacy = re.compile(r'^# OpenRouter coding delegation\n.*?(?=^# |\Z)', re.M | re.S)
    match = legacy.search(text)
    if match and 'codex-openrouter/README.md' in match.group():
        return text[:match.start()] + block + '\n\n' + text[match.end():]
    return text.rstrip() + ('\n\n' if text.strip() else '') + block + '\n'


def install(package, base, codex_home, skill_root=None, check=False):
    package, base, codex_home = map(lambda p: Path(p).expanduser().resolve(), (package, base, codex_home))
    skill_root = Path(skill_root).expanduser().resolve() if skill_root else codex_home / 'skills'
    skill_path = skill_root / 'opencode-worker' / 'SKILL.md'
    manifest_path = base / 'installation.json'
    from worker_wait import active_runs
    if active_runs(base):
        raise InstallError('An OpenCode worker is active; install after it finishes')
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    known = previous.get('files_sha256', {})
    legacy_path = base / 'guardrail-verification.json'
    legacy = json.loads(legacy_path.read_text(encoding='utf-8')).get('files_sha256', {}) if legacy_path.exists() else {}
    sources = list((package / 'scripts').glob('worker_*.py')) + [package / 'scripts' / 'openrouter-worker', package / 'README.md']
    entry_name = 'opencode-worker' if (package / 'scripts' / 'opencode-worker').is_file() else 'openrouter-worker'
    if entry_name != 'openrouter-worker':
        sources.append(package / 'scripts' / entry_name)
    if (package / 'INSTALL_FOR_AI.md').is_file():
        sources.append(package / 'INSTALL_FOR_AI.md')
    for folder in ('references', 'examples'):
        if (package / folder).is_dir():
            sources.extend(path for path in (package / folder).rglob('*') if path.is_file() and path.suffix in ('.md', '.json', '.py'))
    files = {}
    for source in sources:
        if source.is_symlink() or not source.is_file():
            raise InstallError('Package source file is missing or is a symlink: ' + source.name)
        relative = source.name if source.parent == package / 'scripts' else source.relative_to(package).as_posix()
        files[base / relative] = source.read_bytes()
    skill = (package / 'SKILL.md').read_text(encoding='utf-8')
    skill = skill.replace('{{WORKER_PYTHON}}', sys.executable).replace('{{WORKER_ENTRYPOINT}}', str(base / entry_name)).replace('{{WORKER_README}}', str(base / 'README.md'))
    files[skill_path] = skill.encode('utf-8')
    for target, data in files.items():
        if target.is_symlink():
            raise InstallError('Managed target is a symlink; existing target was preserved: ' + str(target))
        if not target.exists() or target.read_bytes() == data:
            continue
        key = str(target)
        expected = known.get(key) or (legacy.get(target.name) if target.parent == base else None)
        if not expected or digest(target.read_bytes()) != expected:
            raise InstallError('Existing file is not an unchanged managed copy: ' + str(target))
    agents = codex_home / 'AGENTS.md'
    if agents.is_symlink():
        raise InstallError('Global AGENTS.md is a symlink; install to its explicitly selected home instead')
    original_agents = agents.read_text(encoding='utf-8') if agents.exists() else ''
    block = '\n'.join([START, '# OpenCode delegation',
        'For explicit coding delegation to OpenCode, OpenRouter, DeepSeek, or GLM, follow `' + str(base / 'README.md') + '`. Invoke the installed worker directly from the coordinating agent; handle commands and saved credentials for the user.', END])
    updated_agents = register(original_agents, block, previous.get('registration_sha256'))
    settings_path = base / 'settings.json'
    settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {
        'default_provider': 'opencode-go', 'allowed_providers': ['opencode-go'],
        'default_model': 'opencode-go/deepseek-v4.1-flash',
        'cli_binary': shutil.which('opencode') or 'opencode',
        'default_job_timeout_seconds': None, 'heartbeat_interval_seconds': 5,
        'hello_timeout_seconds': 10,
        'execution_limits': {
            'max_model_steps': 100, 'max_wall_seconds': 3600,
            'max_repair_attempts': 2, 'check_timeout_seconds': 600,
            'max_repeated_tool_failures': 3,
        },
    }
    if not isinstance(settings, dict):
        raise InstallError('Existing settings must be a JSON object')
    summary = {'status': 'checked' if check else 'installed', 'version': VERSION,
               'entrypoint': str(base / entry_name), 'skill': str(skill_path),
               'codex_instructions': str(agents), 'files': len(files),
               'credentials': 'preserved; each user supplies their own key',
               'prerequisites': ['Python 3.9+', 'Git', 'official OpenCode CLI']}
    if check:
        return summary
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup = base / 'backups' / ('install-' + stamp)
    for target in list(files) + [agents, manifest_path]:
        if target.exists():
            key = hashlib.sha256(str(target).encode()).hexdigest()[:12] + '-' + target.name
            (backup / key).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup / key)
    for target, data in files.items():
        write(target, data)
    (base / 'openrouter-worker').chmod(0o700)
    (base / entry_name).chmod(0o700)
    write(agents, updated_agents.encode('utf-8'))
    if not settings_path.exists():
        write(settings_path, (json.dumps(settings, indent=2) + '\n').encode())
    manifest = {'version': VERSION, 'source': 'https://github.com/polaminggkub-debug/legend-skills/tree/main/opencode-worker',
                'installed_at': stamp, 'files_sha256': {str(path): digest(data) for path, data in files.items()},
                'registration_sha256': digest(block.encode()), 'backup': str(backup)}
    write(manifest_path, (json.dumps(manifest, indent=2) + '\n').encode())
    summary['backup'] = str(backup)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=default_base_dir())
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
    parser.add_argument('--skill-root', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = install(Path(__file__).resolve().parents[1], args.base, args.codex_home, args.skill_root, args.check)
        print(json.dumps(result))
        return 0
    except (InstallError, OSError, ValueError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
