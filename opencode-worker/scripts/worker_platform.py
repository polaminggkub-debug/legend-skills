"""Small operating-system seams used by the audited OpenCode worker.

The worker deliberately keeps credentials in the platform credential store and
uses argument-vector process execution.  This module contains no network code
and never writes an API key to a file.
"""

from __future__ import annotations

import ctypes
import errno
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
from typing import Any, List, Optional

try:  # ``fcntl`` is unavailable on Windows.
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised by Windows CI
    _fcntl = None

try:  # ``msvcrt`` is unavailable on POSIX.
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - exercised by POSIX CI
    _msvcrt = None


_KEYCHAIN_SERVICE = "codex-openrouter-cli"
_WINDOWS_CREDENTIAL_TARGET = "codex-openrouter-cli"
_OPENCODE_GO_KEYCHAIN_SERVICE = "codex-opencode-go-cli"
_OPENCODE_GO_WINDOWS_CREDENTIAL_TARGET = "codex-opencode-go-cli"


def _credential_spec(provider: str) -> tuple[str, str, str]:
    """Return the environment variable and native-store names for a provider."""

    if provider == "openrouter":
        # Read these constants at call time so platform tests and migrations
        # can replace the legacy target without changing the Go target.
        return "OPENROUTER_API_KEY", _KEYCHAIN_SERVICE, _WINDOWS_CREDENTIAL_TARGET
    if provider == "opencode-go":
        return (
            "OPENCODE_API_KEY",
            _OPENCODE_GO_KEYCHAIN_SERVICE,
            _OPENCODE_GO_WINDOWS_CREDENTIAL_TARGET,
        )
    raise ValueError("Unsupported credential provider")


class CredentialStoreUnavailable(RuntimeError):
    """Raised when the platform credential store cannot be reached."""


def default_base_dir() -> Path:
    """Return the worker state directory for the current operating system."""

    explicit = os.environ.get("OPENROUTER_WORKER_HOME")
    if explicit and explicit.strip():
        return Path(explicit).expanduser()
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data and local_app_data.strip():
            return Path(local_app_data) / "OpenRouterWorker"
        # LOCALAPPDATA is normally set by Windows.  The fallback keeps the
        # seam usable for service accounts and minimal CI environments.
        return Path.home() / "AppData" / "Local" / "OpenRouterWorker"
    return Path.home() / ".local" / "share" / "codex-openrouter"


def _require_key(value: Any, label: str = "API key") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be a non-empty string")
    return value


def read_key(provider: str = "openrouter") -> str:
    """Read one provider's API key from its environment or native storage."""

    environment_name, service, target = _credential_spec(provider)
    environment_key = os.environ.get(environment_name)
    if environment_key and environment_key.strip():
        return environment_key
    if os.name == "nt":
        if provider == "openrouter":
            return _read_windows_credential()
        return _read_windows_credential(target)
    if sys.platform == "darwin":
        account = getpass.getuser()
        if provider == "openrouter":
            return _read_macos_keychain(account)
        return _read_macos_keychain(account, service)
    raise CredentialStoreUnavailable(
        "No " + environment_name + " is set and this OS has no configured credential backend; "
        "set " + environment_name + " or run on macOS/Windows with its credential store enabled"
    )


def store_key(key: str, provider: str = "openrouter") -> None:
    """Store one provider's API key in native storage, never in worker files."""

    environment_name, service, target = _credential_spec(provider)
    value = _require_key(key, environment_name + " value")
    if os.name == "nt":
        if provider == "openrouter":
            _write_windows_credential(value)
        else:
            _write_windows_credential(value, target)
        return
    if sys.platform == "darwin":
        account = getpass.getuser()
        if provider == "openrouter":
            _write_macos_keychain(account, value)
        else:
            _write_macos_keychain(account, value, service)
        return
    raise CredentialStoreUnavailable(
        "Native credential storage is unavailable on this OS; keep the key in "
        + environment_name + " or use a supported macOS/Windows credential store"
    )


def _security_command() -> str:
    # Keep the system path explicit so a repository-local executable cannot be
    # selected accidentally.  subprocess errors below become actionable
    # CredentialStoreUnavailable exceptions.
    return "/usr/bin/security"


def _read_macos_keychain(account: str, service: Optional[str] = None) -> str:
    account = _require_key(account, "Keychain account")
    service = service or _KEYCHAIN_SERVICE
    command = _security_command()
    try:
        result = subprocess.run(
            [command, "find-generic-password", "-a", account, "-s", service, "-w"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise CredentialStoreUnavailable(
            "macOS Keychain helper is unavailable; set the selected provider API key"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CredentialStoreUnavailable(
            "macOS Keychain lookup timed out; set the selected provider API key or repair Keychain access"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise CredentialStoreUnavailable(
            "Selected provider API key was not available in macOS Keychain; set it or store it"
        ) from exc
    value = result.stdout.strip()
    if not value:
        raise CredentialStoreUnavailable(
            "macOS Keychain returned an empty provider API key; set it or store it"
        )
    return value


def _write_macos_keychain(account: str, key: str, service: Optional[str] = None) -> None:
    account = _require_key(account, "Keychain account")
    key = _require_key(key)
    service = service or _KEYCHAIN_SERVICE
    command = _security_command()
    try:
        subprocess.run(
            [
                command,
                "add-generic-password",
                "-U",
                "-a",
                account,
                "-s",
                service,
                "-w",
                key,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise CredentialStoreUnavailable(
            "macOS Keychain helper is unavailable; set the selected provider API key"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CredentialStoreUnavailable(
            "macOS Keychain update timed out; set the selected provider API key or repair Keychain access"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise CredentialStoreUnavailable(
            "Could not store the provider API key in macOS Keychain; check Keychain access"
        ) from exc


class _CredentialW(ctypes.Structure):  # pragma: no cover - layout is exercised on Windows
    _fields_ = [
        ("Flags", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("TargetName", ctypes.c_wchar_p),
        ("Comment", ctypes.c_wchar_p),
        ("LastWritten", ctypes.c_byte * 8),
        ("CredentialBlobSize", ctypes.c_uint32),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", ctypes.c_uint32),
        ("AttributeCount", ctypes.c_uint32),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.c_wchar_p),
        ("UserName", ctypes.c_wchar_p),
    ]


_CREDENTIAL_TYPE_GENERIC = 1
_CREDENTIAL_PERSIST_LOCAL_MACHINE = 2


def _advapi32() -> Any:  # pragma: no cover - exercised on Windows CI
    if not hasattr(ctypes, "WinDLL"):
        raise CredentialStoreUnavailable(
            "Windows Credential Manager is unavailable in this Python build; set the selected provider API key"
        )
    try:
        library = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    except OSError as exc:
        raise CredentialStoreUnavailable(
            "Windows Credential Manager could not be loaded; set the selected provider API key"
        ) from exc
    # Explicit prototypes are required on 64-bit Windows so ctypes does not
    # truncate the CREDENTIALW pointer returned to CredReadW.
    try:
        library.CredReadW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.POINTER(_CredentialW)),
        ]
        library.CredReadW.restype = ctypes.c_int
        library.CredWriteW.argtypes = [ctypes.POINTER(_CredentialW), ctypes.c_uint32]
        library.CredWriteW.restype = ctypes.c_int
        library.CredFree.argtypes = [ctypes.c_void_p]
        library.CredFree.restype = ctypes.c_uint32
    except AttributeError as exc:
        raise CredentialStoreUnavailable(
            "Windows Credential Manager API is incomplete; set the selected provider API key"
        ) from exc
    return library


def _read_windows_credential(target: Optional[str] = None) -> str:  # pragma: no cover - exercised on Windows CI
    target = target or _WINDOWS_CREDENTIAL_TARGET
    library = _advapi32()
    credential_pointer = ctypes.POINTER(_CredentialW)()
    try:
        success = library.CredReadW(
            target,
            _CREDENTIAL_TYPE_GENERIC,
            0,
            ctypes.byref(credential_pointer),
        )
        if not success or not credential_pointer:
            raise CredentialStoreUnavailable(
                "Selected provider API key was not available in Windows Credential Manager; "
                "set it or store it"
            )
        credential = credential_pointer.contents
        if not credential.CredentialBlob or credential.CredentialBlobSize <= 0:
            raise CredentialStoreUnavailable(
                "Windows Credential Manager returned an empty provider API key; set it"
            )
        try:
            raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
            value = raw.decode("utf-16-le")
        except (UnicodeDecodeError, ValueError) as exc:
            raise CredentialStoreUnavailable(
                "Windows Credential Manager returned an invalid provider API key; set it"
            ) from exc
        if not value.strip():
            raise CredentialStoreUnavailable(
                "Windows Credential Manager returned an empty provider API key; set it"
            )
        return value
    finally:
        if credential_pointer:
            try:
                library.CredFree(credential_pointer)
            except Exception:
                pass


def _write_windows_credential(key: str, target: Optional[str] = None) -> None:  # pragma: no cover - exercised on Windows CI
    key = _require_key(key)
    target = target or _WINDOWS_CREDENTIAL_TARGET
    library = _advapi32()
    encoded = key.encode("utf-16-le")
    blob = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
    credential = _CredentialW()
    credential.Type = _CREDENTIAL_TYPE_GENERIC
    credential.TargetName = target
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = _CREDENTIAL_PERSIST_LOCAL_MACHINE
    credential.UserName = getpass.getuser()
    try:
        success = library.CredWriteW(ctypes.byref(credential), 0)
        if not success:
            raise CredentialStoreUnavailable(
                "Could not store the provider API key in Windows Credential Manager; "
                "check Credential Manager access"
            )
    finally:
        # Remove the key material from this temporary ctypes buffer as soon as
        # the platform call returns.  No file or process argument contains it.
        for index in range(len(blob)):
            blob[index] = 0


class RepositoryLock:
    """A nonblocking inter-process lock backed by a repository-local file."""

    def __init__(self, path: os.PathLike[str] | str) -> None:
        self.path = Path(path)
        self._stream: Optional[Any] = None
        self._locked = False

    @property
    def closed(self) -> bool:
        return self._stream is None or self._stream.closed

    def acquire(self) -> "RepositoryLock":
        if self._stream is not None:
            raise RuntimeError("repository lock is already open")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = self.path.open("a+")
        try:
            if os.name == "nt":
                self._acquire_windows(stream)
            else:
                self._acquire_posix(stream)
        except Exception:
            stream.close()
            raise
        self._stream = stream
        self._locked = True
        return self

    def _acquire_posix(self, stream: Any) -> None:
        if _fcntl is None:
            raise RuntimeError("POSIX file locking is unavailable in this Python build")
        try:
            _fcntl.flock(stream.fileno(), _fcntl.LOCK_EX | _fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                raise BlockingIOError(errno.EAGAIN, "repository lock is held", str(self.path)) from exc
            raise

    def _acquire_windows(self, stream: Any) -> None:  # pragma: no cover - exercised on Windows CI
        if _msvcrt is None:
            raise RuntimeError("Windows file locking is unavailable in this Python build")
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write("0")
            stream.flush()
        stream.seek(0)
        try:
            _msvcrt.locking(stream.fileno(), _msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise BlockingIOError(errno.EAGAIN, "repository lock is held", str(self.path)) from exc

    def close(self) -> None:
        stream = self._stream
        if stream is None:
            return
        try:
            if self._locked:
                if os.name == "nt":
                    if _msvcrt is not None:
                        stream.seek(0)
                        try:
                            _msvcrt.locking(stream.fileno(), _msvcrt.LK_UNLCK, 1)
                        except OSError:
                            pass
                elif _fcntl is not None:
                    try:
                        _fcntl.flock(stream.fileno(), _fcntl.LOCK_UN)
                    except OSError:
                        pass
        finally:
            self._locked = False
            self._stream = None
            stream.close()

    def __enter__(self) -> "RepositoryLock":
        return self.acquire()

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()


def process_options() -> dict:
    """Return safe Popen options that isolate the child process group."""

    if os.name == "nt":
        return {
            "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200),
        }
    return {"start_new_session": True}


def stop_process(process: Any) -> None:
    """Stop a child and its descendants without invoking a shell."""

    if process is None:
        return
    try:
        if process.poll() is not None:
            return
    except Exception:
        # Continue with the platform termination primitive when a process-like
        # object cannot report its state.
        pass

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, ValueError):
            pass
        try:
            process.wait(timeout=5)
        except (AttributeError, subprocess.TimeoutExpired, OSError):
            pass
        return

    try:
        process_group = os.getpgid(process.pid)
        os.killpg(process_group, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        return
    try:
        process.wait(timeout=5)
        return
    except (subprocess.TimeoutExpired, OSError, AttributeError):
        pass
    try:
        os.killpg(process_group, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        return
    try:
        process.wait(timeout=5)
    except (subprocess.TimeoutExpired, OSError, AttributeError):
        pass


def _verified_opencode_binary(shim: Path) -> Optional[Path]:
    """Resolve the native executable shipped by official opencode-ai 1.18.31."""
    try:
        source = shim.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not re.search(r"opencode-ai[\\/]+bin[\\/]+opencode\.exe", source, re.I):
        return None
    for parent in (shim.parent,) + tuple(shim.parents):
        for package in (parent / "node_modules" / "opencode-ai", parent / "opencode-ai"):
            binary = package / "bin" / "opencode.exe"
            try:
                manifest = json.loads((package / "package.json").read_text(encoding="utf-8"))
                if manifest.get("name") != "opencode-ai":
                    continue
                entry = manifest.get("bin", {})
                entry = entry.get("opencode") if isinstance(entry, dict) else entry
                if entry not in ("./bin/opencode.exe", "bin/opencode.exe"):
                    continue
                with binary.open("rb") as stream:
                    if stream.read(2) != b"MZ":
                        continue
                return binary
            except (OSError, ValueError, AttributeError):
                continue
    return None


def _verified_npm_launcher(shim: Path) -> Optional[Path]:
    """Resolve a known npm shim only after checking its source and target."""

    try:
        shim_source = shim.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError):
        return None
    source_lower = shim_source.lower()
    if "node" not in source_lower or not re.search(
        r"opencode-ai[\\/]+bin[\\/]+\s*opencode",
        source_lower,
    ):
        return None

    candidates: List[Path] = []
    for parent in (shim.parent,) + tuple(shim.parents):
        candidates.append(parent / "node_modules" / "opencode-ai" / "bin" / "opencode")
        candidates.append(parent / "opencode-ai" / "bin" / "opencode")
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        key = str(resolved)
        if key in seen or not resolved.is_file():
            continue
        seen.add(key)
        # Reading the launcher verifies that the target is a real file before
        # handing it to Node; the source is never executed or shell-expanded.
        try:
            launcher_source = resolved.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError):
            continue
        if launcher_source.strip():
            # Preserve the path as derived from the shim.  ``Path.resolve``
            # may rewrite legitimate Windows junctions or macOS /var aliases;
            # it was used above only to verify the source before returning.
            return candidate
    return None


def _verified_npm_cli(shim: Path) -> Optional[Path]:
    """Resolve an npm.cmd shim to its nearby npm-cli.js entry point."""

    try:
        shim_source = shim.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError):
        return None
    source_lower = shim_source.lower()
    if "node" not in source_lower or not re.search(
        r"node_modules[\\/]+npm[\\/]+bin[\\/]+npm-cli\.js",
        source_lower,
    ):
        return None

    candidates: List[Path] = []
    for parent in (shim.parent,) + tuple(shim.parents):
        candidates.append(parent / "node_modules" / "npm" / "bin" / "npm-cli.js")
        candidates.append(parent / "npm" / "bin" / "npm-cli.js")
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        key = str(resolved)
        if key in seen or not resolved.is_file():
            continue
        seen.add(key)
        try:
            npm_source = resolved.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError):
            continue
        if npm_source.strip():
            return candidate
    return None


def _node_for_shim(shim: Path) -> Optional[str]:
    """Prefer a node executable adjacent to a shim, then PATH lookup."""

    for candidate in (shim.parent / "node.exe", shim.parent / "node"):
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            pass
    return shutil.which("node")


def cli_command(path: os.PathLike[str] | str) -> List[str]:
    """Build a shell-free argv prefix for a worker CLI executable."""

    value = str(path)
    if Path(value).name == value:
        value = shutil.which(value) or value
    suffix = Path(value).suffix.lower()
    if suffix == ".py":
        return [sys.executable, value]
    if suffix == ".cmd":
        shim = Path(value)
        native = _verified_opencode_binary(shim)
        if native is not None:
            return [str(native)]
        if shim.name.lower() == "npm.cmd":
            launcher = _verified_npm_cli(shim)
        else:
            launcher = _verified_npm_launcher(shim)
        node = _node_for_shim(shim)
        if launcher is not None and node:
            return [node, str(launcher)]
        raise ValueError("unsupported or unverified .cmd executable")
    if suffix == ".bat":
        raise ValueError(".bat executables are unsupported")
    return [value]


__all__ = [
    "CredentialStoreUnavailable",
    "RepositoryLock",
    "cli_command",
    "default_base_dir",
    "process_options",
    "read_key",
    "stop_process",
    "store_key",
]
