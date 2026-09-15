"""Project-local execution contracts for the audited OpenCode worker.

The module only reads project metadata and validates an optional, committed
``.opencode/worker.json`` contract.  It never invokes a discovered command.
The runtime owns Git operations and supplies the metadata environment when it
does execute a validated contract step.

This file intentionally uses only the Python 3.9 standard library.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import worker_platform


CONTRACT_RELATIVE = ".opencode/worker.json"
CONTRACT_SCHEMA_VERSION = 1
DEFAULT_WRITE_PATHS = ["**"]
DEFAULT_CWD = "."
DEFAULT_STAGE = "before_commit"
DEFAULT_REQUIRED = True
MAX_DISCOVERY_BYTES = 1024 * 1024
MAX_DISCOVERY_FILES = 512
MAX_DISCOVERY_DEPTH = 4

_CHECK_KINDS = {"test", "lint", "build", "check"}
_STAGES = {"before_commit", "after_commit"}
_CONTRACT_KEYS = {"schema_version", "write_paths", "checks", "handoff"}
_CHECK_KEYS = {
    "id",
    "kind",
    "argv",
    "cwd",
    "stage",
    "required",
    "timeout_seconds",
}
_METADATA_KEYS = {"id", "argv", "cwd", "required", "timeout_seconds"}
_HANDOFF_KEYS = {"metadata", "write_paths"}
_SHELL_EXECUTABLES = {
    "ash",
    "bash",
    "cmd",
    "cmd.exe",
    "csh",
    "dash",
    "fish",
    "ksh",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
    "sh",
    "tcsh",
    "zsh",
}


class ProjectError(ValueError):
    """Raised when project metadata cannot support a safe worker plan."""


def _is_within(root: Path, candidate: Path) -> bool:
    """Return whether *candidate* is inside *root* without Path.is_relative_to."""

    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _repo_root(repo: Path) -> Path:
    try:
        root = Path(repo).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as exc:
        raise ProjectError("repository path is unavailable") from exc
    if not root.is_dir():
        raise ProjectError("repository path is not a directory")
    return root


def _reject_json_constant(value: str) -> None:
    raise ProjectError("contract contains a non-finite JSON number")


def _no_duplicate_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectError("contract contains a duplicate object key")
        result[key] = value
    return result


def _finite_positive(value: Any, field: str) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectError("%s must be a finite positive number" % field)
    try:
        valid = math.isfinite(float(value)) and value > 0
    except (OverflowError, ValueError):
        valid = False
    if not valid:
        raise ProjectError("%s must be a finite positive number" % field)
    return value


def _secret_literal(value: str) -> bool:
    """Detect common literal credentials without retaining or reporting them."""

    patterns = (
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----",
        r"\b(?:sk|ghp|github_pat|xox[baprs])-[A-Za-z0-9_-]{16,}\b",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|authorization)\s*[:=]\s*[A-Za-z0-9_./+=:-]{16,}",
    )
    return any(re.search(pattern, value) for pattern in patterns)


def _safe_string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ProjectError("%s must be a non-empty string" % field)
    if "\x00" in value:
        raise ProjectError("%s contains a NUL character" % field)
    if _secret_literal(value):
        raise ProjectError("contract contains a secret literal")
    return value


def _normalise_relative(value: Any, field: str, *, allow_glob: bool = False) -> str:
    text = _safe_string(value, field).strip()
    normalized = text.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise ProjectError("%s must be a relative path" % field)
    parts = normalized.split("/")
    if any(part == ".." for part in parts):
        raise ProjectError("%s may not contain parent traversal" % field)
    if not allow_glob and any(char in normalized for char in "*?[]"):
        raise ProjectError("%s may not contain glob characters" % field)
    normalized = "/".join(part for part in parts if part not in ("", "."))
    return normalized or "."


def _validate_scope_pattern(value: Any, field: str) -> str:
    pattern = _normalise_relative(value, field, allow_glob=True)
    if pattern == ".":
        raise ProjectError("%s must name a non-empty relative glob" % field)
    return pattern


def _path_segments(value: Any) -> Optional[List[str]]:
    if isinstance(value, Path):
        if value.is_absolute():
            return None
        text = value.as_posix()
    elif isinstance(value, str):
        text = value.replace("\\", "/")
    else:
        return None
    if not text or text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
        return None
    segments = [part for part in text.split("/") if part not in ("", ".")]
    if any(part == ".." for part in segments):
        return None
    return segments


def _glob_matches(path_segments: Sequence[str], pattern_segments: Sequence[str]) -> bool:
    """Match slash-separated globs where ``**`` also matches zero directories."""

    memo: Dict[Tuple[int, int], bool] = {}

    def match(path_index: int, pattern_index: int) -> bool:
        key = (path_index, pattern_index)
        if key in memo:
            return memo[key]
        if pattern_index == len(pattern_segments):
            result = path_index == len(path_segments)
        elif pattern_segments[pattern_index] == "**":
            result = match(path_index, pattern_index + 1) or (
                path_index < len(path_segments) and match(path_index + 1, pattern_index)
            )
        else:
            result = path_index < len(path_segments) and fnmatch.fnmatchcase(
                path_segments[path_index], pattern_segments[pattern_index]
            ) and match(path_index + 1, pattern_index + 1)
        memo[key] = result
        return result

    return match(0, 0)


def path_allowed(path: Any, patterns: Iterable[str]) -> bool:
    """Return whether a relative path matches one of the explicit globs.

    ``**`` matches zero or more path components, so ``**/*.py`` includes a
    Python file at the repository root as well as files in nested directories.
    Invalid or absolute paths never match.
    """

    path_parts = _path_segments(path)
    if not path_parts:
        return False
    try:
        pattern_values = list(patterns)
    except TypeError:
        return False
    for pattern in pattern_values:
        pattern_parts = _path_segments(pattern)
        if pattern_parts and _glob_matches(path_parts, pattern_parts):
            return True
    return False


def _contained_path(root: Path, relative: str, field: str, *, must_exist: bool = False,
                    directory: bool = False) -> Path:
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ProjectError("%s cannot be resolved" % field) from exc
    if not _is_within(root, resolved):
        raise ProjectError("%s escapes the repository" % field)
    if must_exist and not candidate.exists():
        raise ProjectError("%s does not exist" % field)
    if directory and candidate.exists() and not candidate.is_dir():
        raise ProjectError("%s is not a directory" % field)
    return candidate


def _validate_symlink_scopes(root: Path, patterns: Sequence[str], field: str) -> None:
    """Reject an existing outside-repository symlink selected by a scope glob."""

    for current, directories, files in os.walk(str(root), topdown=True, followlinks=False):
        current_path = Path(current)
        filtered_directories: List[str] = []
        for name in directories:
            path = current_path / name
            if path.is_symlink():
                relative = path.relative_to(root).as_posix()
                try:
                    target = path.resolve(strict=False)
                except (OSError, RuntimeError) as exc:
                    raise ProjectError("%s contains an unresolved symlink" % field) from exc
                if not _is_within(root, target) and any(path_allowed(relative, [pattern]) for pattern in patterns):
                    raise ProjectError("%s selects a symlink outside the repository" % field)
                continue
            if name not in (".git", "node_modules"):
                filtered_directories.append(name)
        directories[:] = filtered_directories
        for name in files:
            path = current_path / name
            if not path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            try:
                target = path.resolve(strict=False)
            except (OSError, RuntimeError) as exc:
                raise ProjectError("%s contains an unresolved symlink" % field) from exc
            if not _is_within(root, target) and any(path_allowed(relative, [pattern]) for pattern in patterns):
                raise ProjectError("%s selects a symlink outside the repository" % field)


def _validate_write_paths(root: Path, values: Any, field: str, *, require_nonempty: bool = False) -> List[str]:
    if not isinstance(values, list) or (require_nonempty and not values):
        qualifier = "non-empty " if require_nonempty else ""
        raise ProjectError("%s must be a %slist" % (field, qualifier))
    patterns = [_validate_scope_pattern(value, "%s[%d]" % (field, index))
                for index, value in enumerate(values)]
    _validate_symlink_scopes(root, patterns, field)
    return patterns


def _validate_argv(value: Any, field: str) -> List[str]:
    if not isinstance(value, list) or not value:
        raise ProjectError("%s must be a non-empty list of strings" % field)
    result: List[str] = []
    for index, item in enumerate(value):
        token = _safe_string(item, "%s[%d]" % (field, index))
        if not token.strip():
            raise ProjectError("%s[%d] must be non-empty" % (field, index))
        # Commands are passed as argv directly.  Shell interpolation makes a
        # contract ambiguous and is rejected before any model spend.
        if "`" in token or "$(" in token or "${" in token:
            raise ProjectError("%s contains shell interpolation" % field)
        result.append(token)
    executable_name = result[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if executable_name in _SHELL_EXECUTABLES:
        raise ProjectError("%s may not invoke a shell" % field)
    return result


def _validate_step(raw: Any, field: str, *, metadata: bool = False) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ProjectError("%s must be an object" % field)
    allowed = _METADATA_KEYS if metadata else _CHECK_KEYS
    unknown = set(raw) - allowed
    if unknown:
        raise ProjectError("%s contains unknown fields" % field)
    step_id = _safe_string(raw.get("id"), "%s.id" % field).strip()
    argv = _validate_argv(raw.get("argv"), "%s.argv" % field)
    cwd = _normalise_relative(raw.get("cwd", DEFAULT_CWD), "%s.cwd" % field)
    required = raw.get("required", DEFAULT_REQUIRED)
    if not isinstance(required, bool):
        raise ProjectError("%s.required must be boolean" % field)
    timeout = raw.get("timeout_seconds")
    if timeout is not None:
        timeout = _finite_positive(timeout, "%s.timeout_seconds" % field)

    result: Dict[str, Any] = {
        "id": step_id,
        "argv": argv,
        "cwd": cwd,
        "required": required,
        "timeout_seconds": timeout,
    }
    if not metadata:
        kind = _safe_string(raw.get("kind"), "%s.kind" % field).strip().lower()
        if kind not in _CHECK_KINDS:
            raise ProjectError("%s.kind is invalid" % field)
        stage = _safe_string(raw.get("stage", DEFAULT_STAGE), "%s.stage" % field).strip().lower()
        if stage not in _STAGES:
            raise ProjectError("%s.stage is invalid" % field)
        result["kind"] = kind
        result["stage"] = stage
    return result


def _validate_handoff(root: Path, raw: Any, used_ids: set) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ProjectError("handoff must be an object")
    unknown = set(raw) - _HANDOFF_KEYS
    if unknown:
        raise ProjectError("handoff contains unknown fields")
    if "write_paths" not in raw:
        raise ProjectError("handoff.write_paths is required")
    write_paths = _validate_write_paths(root, raw["write_paths"], "handoff.write_paths", require_nonempty=True)
    metadata_raw = raw.get("metadata", [])
    if not isinstance(metadata_raw, list):
        raise ProjectError("handoff.metadata must be a list")
    metadata: List[Dict[str, Any]] = []
    for index, item in enumerate(metadata_raw):
        step = _validate_step(item, "handoff.metadata[%d]" % index, metadata=True)
        if step["id"] in used_ids:
            raise ProjectError("contract contains repeated step IDs")
        used_ids.add(step["id"])
        metadata.append(step)
    return {"metadata": metadata, "write_paths": write_paths}


def _validate_contract(root: Path, raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ProjectError("worker contract must be an object")
    unknown = set(raw) - _CONTRACT_KEYS
    if unknown:
        raise ProjectError("worker contract contains unknown fields")
    version = raw.get("schema_version")
    if isinstance(version, bool) or version != CONTRACT_SCHEMA_VERSION:
        raise ProjectError("worker contract schema_version must be 1")

    write_paths = _validate_write_paths(root, raw.get("write_paths", DEFAULT_WRITE_PATHS), "write_paths")
    checks_raw = raw.get("checks", [])
    if not isinstance(checks_raw, list):
        raise ProjectError("checks must be a list")
    checks: List[Dict[str, Any]] = []
    used_ids = set()
    for index, item in enumerate(checks_raw):
        step = _validate_step(item, "checks[%d]" % index)
        if step["id"] in used_ids:
            raise ProjectError("contract contains repeated step IDs")
        used_ids.add(step["id"])
        checks.append(step)
    handoff = _validate_handoff(root, raw.get("handoff"), used_ids)
    return {"write_paths": write_paths, "checks": checks, "handoff": handoff}


def _read_contract(root: Path) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    path = root / CONTRACT_RELATIVE
    if not os.path.lexists(str(path)):
        return None, None
    if path.is_symlink():
        raise ProjectError("worker contract may not be a symlink")
    _contained_path(root, CONTRACT_RELATIVE, "worker contract", must_exist=True)
    try:
        raw_bytes = path.read_bytes()
    except (OSError, UnicodeError) as exc:
        raise ProjectError("worker contract cannot be read") from exc
    digest = hashlib.sha256(raw_bytes).hexdigest()
    try:
        decoded = raw_bytes.decode("utf-8")
        parsed = json.loads(
            decoded,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except ProjectError:
        raise
    except (UnicodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProjectError("worker contract contains malformed JSON") from exc
    return digest, parsed


def _read_text_if_small(path: Path) -> Optional[str]:
    try:
        if not path.is_file() or path.stat().st_size > MAX_DISCOVERY_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _bounded_files(root: Path, filename: str) -> List[Path]:
    found: List[Path] = []
    for current, directories, files in os.walk(str(root), topdown=True, followlinks=False):
        current_path = Path(current)
        try:
            depth = len(current_path.relative_to(root).parts)
        except ValueError:
            continue
        if depth >= MAX_DISCOVERY_DEPTH:
            directories[:] = []
        else:
            directories[:] = [
                name for name in directories
                if name not in (".git", "node_modules") and not (current_path / name).is_symlink()
            ]
        if filename in files:
            candidate = current_path / filename
            if not candidate.is_symlink():
                found.append(candidate)
                if len(found) >= MAX_DISCOVERY_FILES:
                    break
    return found


def _package_candidates(root: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    candidates: List[Dict[str, Any]] = []
    projects: List[str] = []
    package_paths = _bounded_files(root, "package.json")
    for path in package_paths:
        text = _read_text_if_small(path)
        if text is None:
            continue
        try:
            data = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(data, Mapping):
            continue
        relative = _relative(root, path)
        projects.append(relative)
        scripts = data.get("scripts")
        if not isinstance(scripts, Mapping):
            continue
        for name in sorted(scripts):
            if not isinstance(name, str) or not name.strip() or not isinstance(scripts[name], str):
                continue
            script_name = name.strip()
            candidates.append({
                "source": "package.json",
                "path": relative,
                "name": script_name,
                "command": "npm run " + script_name,
                "argv": ["npm", "run", script_name],
                "evidence": "package_script",
            })
    return candidates, sorted(set(projects))


def _python_candidates(root: Path) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    config_names = ("pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini", ".flake8", "mypy.ini")
    for name in config_names:
        path = root / name
        if not path.is_file() or path.is_symlink():
            continue
        text = _read_text_if_small(path) or ""
        lower = text.lower()
        relative = _relative(root, path)
        detected: List[Tuple[str, List[str], str]] = []
        if name == "pyproject.toml":
            section_names = (
                ("pytest", ["{python}", "-m", "pytest"]),
                ("ruff", ["ruff"]),
                ("mypy", ["mypy"]),
                ("black", ["black"]),
                ("coverage", ["coverage"]),
            )
            for tool_name, argv in section_names:
                if re.search(r"(?m)^\s*\[tool\." + re.escape(tool_name) + r"(?:[.\]])", lower):
                    detected.append((tool_name, argv, "tool." + tool_name))
            if re.search(r"(?m)^\s*\[build-system\]", lower) or "build-backend" in lower:
                detected.append(("build", ["{python}", "-m", "build"], "build-system"))
        elif name in ("setup.cfg", "tox.ini"):
            for tool_name, argv, marker in (
                ("pytest", ["{python}", "-m", "pytest"], "pytest"),
                ("flake8", ["flake8"], "flake8"),
                ("mypy", ["mypy"], "mypy"),
            ):
                if re.search(r"(?m)^\s*\[(?:tool:)?" + re.escape(tool_name) + r"\s*\]", lower):
                    detected.append((tool_name, argv, marker))
            if name == "tox.ini" and re.search(r"(?m)^\s*\[tox\]", lower):
                detected.append(("tox", ["tox"], "tox"))
        elif name == "pytest.ini":
            detected.append(("pytest", ["{python}", "-m", "pytest"], "pytest.ini"))
        elif name == ".flake8":
            detected.append(("flake8", ["flake8"], ".flake8"))
        elif name == "mypy.ini":
            detected.append(("mypy", ["mypy"], "mypy.ini"))
        seen = set()
        for candidate_name, argv, evidence in detected:
            if candidate_name in seen:
                continue
            seen.add(candidate_name)
            candidates.append({
                "source": "python_config",
                "path": relative,
                "name": candidate_name,
                "command": " ".join(argv),
                "argv": argv,
                "evidence": evidence,
            })
    return candidates


def _make_candidates(root: Path) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    path = next((root / name for name in ("Makefile", "makefile", "GNUmakefile") if (root / name).is_file()), None)
    if path is None:
        return candidates
    text = _read_text_if_small(path)
    if text is None:
        return candidates
    targets = set()
    for line in text.splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        target_text = line.split(":", 1)[0].strip()
        for target in target_text.split():
            if target and not target.startswith(".") and re.match(r"^[A-Za-z0-9_.@%+/-]+$", target):
                targets.add(target)
    relative = _relative(root, path)
    for target in sorted(targets):
        candidates.append({
            "source": "Makefile",
            "path": relative,
            "name": target,
            "command": "make " + target,
            "argv": ["make", target],
            "evidence": "make_target",
        })
    return candidates


def _ci_files(root: Path) -> List[Path]:
    result: List[Path] = []
    exact = (
        ".gitlab-ci.yml",
        ".gitlab-ci.yaml",
        ".circleci/config.yml",
        "azure-pipelines.yml",
        "Jenkinsfile",
    )
    for name in exact:
        path = root / name
        if not path.is_file() or path.is_symlink():
            continue
        try:
            if _is_within(root, path.resolve(strict=True)):
                result.append(path)
        except (OSError, RuntimeError):
            continue
    workflows = root / ".github" / "workflows"
    try:
        workflows_inside = _is_within(root, workflows.resolve(strict=True))
    except (OSError, RuntimeError):
        workflows_inside = False
    if workflows.is_dir() and not workflows.is_symlink() and workflows_inside:
        try:
            for path in sorted(workflows.iterdir()):
                try:
                    inside = _is_within(root, path.resolve(strict=True))
                except (OSError, RuntimeError):
                    inside = False
                if path.is_file() and not path.is_symlink() and inside and path.suffix.lower() in (".yml", ".yaml"):
                    result.append(path)
        except OSError:
            pass
    return result[:MAX_DISCOVERY_FILES]


def inspect_project(repo: Path) -> Dict[str, Any]:
    """Inspect bounded project metadata without running any candidate command."""

    root = _repo_root(repo)
    package_candidates, projects = _package_candidates(root)
    candidates = package_candidates + _python_candidates(root) + _make_candidates(root)
    ci_paths = _ci_files(root)
    for path in ci_paths:
        candidates.append({
            "source": "ci",
            "path": _relative(root, path),
            "name": path.name,
            "command": None,
            "argv": None,
            "evidence": "ci_file",
        })
    instruction_paths: List[str] = []
    claude_paths: List[str] = []
    for current, directories, files in os.walk(str(root), topdown=True, followlinks=False):
        current_path = Path(current)
        try:
            depth = len(current_path.relative_to(root).parts)
        except ValueError:
            continue
        if depth >= MAX_DISCOVERY_DEPTH:
            directories[:] = []
        else:
            directories[:] = [
                name for name in directories
                if name not in (".git", "node_modules") and not (current_path / name).is_symlink()
            ]
        for name in files:
            upper = name.upper()
            relative = _relative(root, current_path / name)
            if upper == "AGENTS.MD" or upper.startswith("AGENTS."):
                instruction_paths.append(relative)
            if upper == "CLAUDE.MD" or upper.startswith("CLAUDE."):
                claude_paths.append(relative)

    candidates.sort(key=lambda item: (str(item.get("path", "")), str(item.get("name", "")), str(item.get("source", ""))))
    return {
        "root": str(root),
        "projects": sorted(set(projects)),
        "candidates": candidates,
        "presence": {
            "agents": sorted(instruction_paths),
            "claude": sorted(claude_paths),
            "ci": sorted(_relative(root, path) for path in ci_paths),
        },
    }


def _preflight_steps(root: Path, steps: Iterable[Mapping[str, Any]]) -> None:
    for step in steps:
        command_argv(step, root)


def load_project(repo: Path) -> Dict[str, Any]:
    """Load a validated contract or a discovery-only, no-check plan."""

    root = _repo_root(repo)
    digest, raw = _read_contract(root)
    if raw is None:
        discovery = inspect_project(root)
        presence = discovery.get("presence") or {}
        has_guidance = any(bool(values) for values in presence.values() if isinstance(values, list))
        if discovery.get("candidates") or has_guidance:
            raise ProjectError("project workflow needs a committed .opencode/worker.json contract")
        return {
            **discovery,
            "source": "discovery",
            "contract_sha256": None,
            "contract_path": CONTRACT_RELATIVE,
            "write_paths": list(DEFAULT_WRITE_PATHS),
            "checks": [],
            "handoff": None,
        }

    normalized = _validate_contract(root, raw)
    metadata_steps = []
    if normalized["handoff"] is not None:
        metadata_steps = normalized["handoff"]["metadata"]
    # This is a read-only executable preflight.  It resolves commands and
    # validates cwd containment; it never starts a subprocess.
    _preflight_steps(root, list(normalized["checks"]) + list(metadata_steps))
    discovery = inspect_project(root)
    return {
        **discovery,
        "source": "contract",
        "contract_sha256": digest,
        "contract_path": CONTRACT_RELATIVE,
        "write_paths": normalized["write_paths"],
        "checks": normalized["checks"],
        "handoff": normalized["handoff"],
    }


def _resolve_cwd(root: Path, step: Mapping[str, Any]) -> Path:
    cwd = _normalise_relative(step.get("cwd", DEFAULT_CWD), "step.cwd")
    return _contained_path(root, cwd, "step.cwd", must_exist=True, directory=True).resolve(strict=True)


def cli_command(path: os.PathLike[str] | str) -> List[str]:
    """Delegate platform-specific executable handling without a shell."""

    return worker_platform.cli_command(path)


platform_cli_command = cli_command


def _executable(token: str, root: Path, cwd: Path) -> str:
    if token == "{python}":
        executable = Path(sys.executable)
        if not executable.is_file():
            raise ProjectError("{python} executable is unavailable")
        return str(executable)

    path_like = token.startswith((".", "/", "\\")) or "/" in token or "\\" in token
    if path_like:
        candidate = Path(token)
        if candidate.is_absolute():
            resolved = candidate.resolve(strict=False)
        else:
            resolved = (cwd / candidate).resolve(strict=False)
        if not _is_within(root, resolved):
            raise ProjectError("explicit executable escapes the repository")
        if not resolved.is_file() or not os.access(str(resolved), os.X_OK):
            raise ProjectError("explicit executable is unavailable")
        return str(resolved)

    resolved_name = shutil.which(token)
    if not resolved_name:
        raise ProjectError("executable is unavailable")
    resolved = Path(resolved_name)
    if not resolved.is_file():
        raise ProjectError("executable is unavailable")
    return str(resolved)


def command_argv(step: Mapping[str, Any], repo: Path) -> List[str]:
    """Resolve a validated step to an argv list without executing it."""

    root = _repo_root(repo)
    metadata = "kind" not in step and "stage" not in step
    normalized = _validate_step(step, "step", metadata=metadata)
    cwd = _resolve_cwd(root, normalized)
    executable = _executable(normalized["argv"][0], root, cwd)
    return cli_command(executable) + normalized["argv"][1:]


def metadata_environment(repo: Path, source_commit: Optional[str] = None,
                         run_id: Optional[str] = None) -> Dict[str, str]:
    """Build the fixed metadata environment for handoff commands.

    Values are passed as environment entries.  No command token is expanded or
    interpolated by this module.
    """

    root = _repo_root(repo)
    environment = {"WORKER_REPO_ROOT": str(root)}
    if source_commit is not None:
        environment["WORKER_SOURCE_COMMIT"] = _safe_string(source_commit, "source_commit")
    if run_id is not None:
        environment["WORKER_RUN_ID"] = _safe_string(run_id, "run_id")
    return environment


metadata_env = metadata_environment


def assert_unchanged(repo: Path, plan: Mapping[str, Any]) -> bool:
    """Verify that the contract's presence and bytes still match a loaded plan."""

    root = _repo_root(repo)
    path = root / CONTRACT_RELATIVE
    expected = plan.get("contract_sha256") if isinstance(plan, Mapping) else None
    present = os.path.lexists(str(path))
    if expected is None:
        if present:
            raise ProjectError("worker contract appeared after planning")
        return True
    if not present or path.is_symlink() or not path.is_file():
        raise ProjectError("worker contract disappeared after planning")
    try:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise ProjectError("worker contract cannot be reread") from exc
    if actual != expected:
        raise ProjectError("worker contract changed after planning")
    return True


__all__ = [
    "CONTRACT_RELATIVE",
    "CONTRACT_SCHEMA_VERSION",
    "ProjectError",
    "assert_unchanged",
    "cli_command",
    "command_argv",
    "inspect_project",
    "load_project",
    "metadata_env",
    "metadata_environment",
    "path_allowed",
    "platform_cli_command",
]
