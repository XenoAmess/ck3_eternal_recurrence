"""Cross-process ownership for one autonomous-player state directory."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Iterator

from .errors import AgentError


def _lock_name(state_dir: Path) -> str:
    identity = str(state_dir.resolve()).casefold().encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:24]
    return f"Local\\XarAutoplayer-{digest}"


def _launch_lock_name(game_exe: Path) -> str:
    identity = str(game_exe.resolve()).casefold().encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:24]
    return f"Local\\XarAutoplayer-Launch-{digest}"


@contextmanager
def exclusive_launch_lock(game_exe: Path) -> Iterator[None]:
    """Allow at most one agent launch for a CK3 installation across state dirs."""
    if os.name == "nt":
        import win32api
        import win32event

        handle = win32event.CreateMutex(None, False, _launch_lock_name(game_exe))
        outcome = win32event.WaitForSingleObject(handle, 0)
        if outcome not in (win32event.WAIT_OBJECT_0, win32event.WAIT_ABANDONED):
            win32api.CloseHandle(handle)
            raise AgentError("another autonomous-player launch owns this CK3 install")
        try:
            yield
        finally:
            win32event.ReleaseMutex(handle)
            win32api.CloseHandle(handle)
        return

    # Non-Windows support exists for tests only; the desktop runtime refuses it.
    import fcntl
    import tempfile

    digest = hashlib.sha256(str(game_exe.resolve()).encode("utf-8")).hexdigest()[:24]
    path = Path(tempfile.gettempdir()) / f"xar-autoplayer-launch-{digest}.lock"
    with path.open("a+b") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise AgentError(
                "another autonomous-player launch owns this CK3 install"
            ) from error
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextmanager
def exclusive_state_lock(state_dir: Path, purpose: str) -> Iterator[None]:
    """Fail closed when another process/thread owns the same runtime profile."""
    control = state_dir.resolve() / "control"
    control.mkdir(parents=True, exist_ok=True)
    owner_path = control / "owner.json"
    owner = {
        "pid": os.getpid(),
        "thread_id": threading.get_ident(),
        "purpose": purpose,
        "state_dir": str(state_dir.resolve()),
    }

    if os.name == "nt":
        import win32api
        import win32event

        handle = win32event.CreateMutex(None, False, _lock_name(state_dir))
        outcome = win32event.WaitForSingleObject(handle, 0)
        if outcome not in (win32event.WAIT_OBJECT_0, win32event.WAIT_ABANDONED):
            win32api.CloseHandle(handle)
            detail = ""
            try:
                detail = f": {owner_path.read_text(encoding='utf-8').strip()}"
            except OSError:
                pass
            raise AgentError(f"autoplayer state is already locked{detail}")
        try:
            owner_path.write_text(
                json.dumps(owner, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            yield
        finally:
            owner_path.unlink(missing_ok=True)
            win32event.ReleaseMutex(handle)
            win32api.CloseHandle(handle)
        return

    # The package's desktop runtime is Windows-only, but a non-blocking flock
    # keeps unit tests and read-only tooling honest on other hosts.
    import fcntl

    lock_path = control / "agent.lock"
    with lock_path.open("a+b") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise AgentError("autoplayer state is already locked") from error
        try:
            owner_path.write_text(
                json.dumps(owner, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            yield
        finally:
            owner_path.unlink(missing_ok=True)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
