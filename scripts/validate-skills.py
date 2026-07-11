#!/usr/bin/env python3
"""Portable, dependency-free checks for the maintained personal skills."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("chris", "margaret", "ship", "steve", "update-all")
FORBIDDEN = ("~/.claude/skills/", "python3 ~/.", "How many audit passes?")


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


def main() -> None:
    for skill in SKILLS:
        path = ROOT / skill / "SKILL.md"
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if lines[0:1] != ["---"] or "---" not in lines[1:]:
            fail(f"{skill}/SKILL.md lacks YAML front matter")
        frontmatter = text.split("---", 2)[1]
        if not re.search(r"description:\s*>\s*\n\s+Use when\b", frontmatter):
            fail(f"{skill}/SKILL.md description must start with 'Use when'")
        if len(lines) > 150:
            fail(f"{skill}/SKILL.md is {len(lines)} lines; maximum is 150")
        for token in FORBIDDEN:
            if token in text:
                fail(f"{skill}/SKILL.md contains forbidden legacy token: {token}")
        if "Markdown" not in text:
            fail(f"{skill}/SKILL.md does not declare Markdown output")
        metadata = ROOT / skill / "agents" / "openai.yaml"
        if not metadata.is_file():
            fail(f"missing {skill}/agents/openai.yaml")
        metadata_text = metadata.read_text(encoding="utf-8")
        for key in ("display_name:", "short_description:", "default_prompt:"):
            if key not in metadata_text:
                fail(f"{skill}/agents/openai.yaml lacks {key}")
        if f"${skill}" not in metadata_text:
            fail(f"{skill}/agents/openai.yaml default prompt does not mention ${skill}")

    chris = (ROOT / "chris" / "SKILL.md").read_text(encoding="utf-8")
    if "only testing gateway" not in chris.lower():
        fail("Chris does not declare itself as the only testing gateway")

    ship = (ROOT / "ship" / "SKILL.md").read_text(encoding="utf-8")
    if "production only" not in ship.lower():
        fail("Ship does not declare production-only scope")

    suite = ROOT / "steve-design-suite"
    for relative in (
        ".codex-plugin/plugin.json",
        ".claude-plugin/plugin.json",
        "dependency-lock.json",
        "skills/steve/SKILL.md",
        "skills/ui-ux-pro-max/SKILL.md",
    ):
        if not (suite / relative).is_file():
            fail(f"missing suite file steve-design-suite/{relative}")
    bundled_steve = (suite / "skills" / "steve" / "SKILL.md").read_text(encoding="utf-8")
    if bundled_steve != (ROOT / "steve" / "SKILL.md").read_text(encoding="utf-8"):
        fail("bundled Steve differs from canonical steve/SKILL.md")
    bundled_metadata = (suite / "skills" / "steve" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    root_metadata = (ROOT / "steve" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if bundled_metadata != root_metadata:
        fail("bundled Steve metadata differs from canonical Steve metadata")
    bundled_audit = (suite / "skills" / "steve" / "references" / "design-audit.md").read_text(encoding="utf-8")
    root_audit = (ROOT / "steve" / "references" / "design-audit.md").read_text(encoding="utf-8")
    if bundled_audit != root_audit:
        fail("bundled Steve audit reference differs from canonical Steve reference")
    uiux = suite / "skills" / "ui-ux-pro-max"
    if not (uiux / "agents" / "openai.yaml").is_file():
        fail("missing UIUX Pro Max agents/openai.yaml")
    uiux_text = (uiux / "SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"description:\s*>\s*\n\s+Use when\b", uiux_text.split("---", 2)[1]):
        fail("UIUX Pro Max description must start with 'Use when'")
    for relative in ("scripts/search.py", "scripts/core.py", "data/styles.csv", "data/stacks/vue.csv"):
        if not (uiux / relative).is_file():
            fail(f"missing UIUX Pro Max resource: {relative}")

    print("PASS skill validation")


if __name__ == "__main__":
    main()
