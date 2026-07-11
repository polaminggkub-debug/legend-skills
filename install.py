#!/usr/bin/env python3
"""Install maintained skills without requiring Bash, cp, or a fixed OS."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent
CORE_SKILLS = ("chris", "formpress", "margaret", "ship", "update-all")


def target(platform: str) -> Path:
    home = Path.home()
    if platform == "claude":
        return Path(os.environ.get("CLAUDE_CODE_SKILLS_DIR", home / ".claude" / "skills"))
    return Path(os.environ.get("CODEX_HOME", home / ".codex")) / "skills"


def copy_skill(source: Path, destination: Path) -> None:
    staging = destination.with_name(f".{destination.name}.installing")
    backup = destination.with_name(f".{destination.name}.previous")
    for temporary in (staging, backup):
        if temporary.exists():
            shutil.rmtree(temporary)
    shutil.copytree(source, staging, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if destination.exists():
        destination.replace(backup)
    try:
        staging.replace(destination)
    except Exception:
        if backup.exists() and not destination.exists():
            backup.replace(destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)
    print(f"Installed: {destination.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("codex", "claude"), default="codex")
    args = parser.parse_args()
    skills_dir = target(args.platform)
    skills_dir.mkdir(parents=True, exist_ok=True)

    suite = ROOT / "steve-design-suite" / "skills"
    sources = [(ROOT / name, skills_dir / name) for name in CORE_SKILLS]
    sources.extend(
        (
            (suite / "steve", skills_dir / "steve"),
            (suite / "ui-ux-pro-max", skills_dir / "ui-ux-pro-max"),
        )
    )
    for source, _ in sources:
        if not (source / "SKILL.md").is_file():
            raise FileNotFoundError(f"Invalid skill source: {source}")
    for source, destination in sources:
        copy_skill(source, destination)
    print(f"Done. Restart {args.platform} if it does not discover skills immediately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
