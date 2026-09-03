"""Lifecycle supervisor for a pure native-headless CK3 MCP session.

This module deliberately depends only on the process runtime.  It does not
import the visual driver, OCR, screenshots, or desktop input modules.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
from queue import Empty, SimpleQueue
import sys
import threading
import time
from typing import Iterator, TextIO

from .bridge.session_queue import PersistentSessionQueue, SessionQueueRequest
from .environment import EnvironmentSpec, ensure_state_path_safe, write_json_atomic
from .errors import AgentError
from .locking import exclusive_launch_lock, exclusive_state_lock
from .runtime import (
    NativeBridgeLaunchConfig,
    NATIVE_BRIDGE_DISABLED,
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
    launch,
    native_bridge_launch_config_from_environment,
    _process_identity,
    _same_executable,
    stop_tracked,
    utc_now,
    validate_native_bridge_launch_config,
)


PURE_NATIVE_MODE = "native-headless"
NATIVE_SESSION_QUEUE_DIRNAME = "native-session"
NATIVE_SESSION_RESTORE_COMMAND = "restore-checkpoint"
NATIVE_SESSION_START_NEXT_EPISODE_COMMAND = "start-next-episode"
NATIVE_SESSION_CHECKPOINT_FILENAME = "xar_checkpoint.ck3"
NATIVE_SESSION_CHECKPOINT_LOAD_NAME = "xar_checkpoint"
NATIVE_SESSION_EPISODE_SEED_FILENAME = "xar_episode_seed.ck3"
NATIVE_SESSION_EPISODE_SEED_LOAD_NAME = "xar_episode_seed"
NATIVE_SESSION_EPISODE_SEED_METADATA_FILENAME = "episode-seed.json"
NATIVE_DRIVER_STATE_FILENAME = "driver-state.json"
# The frontend-first path is deliberately opt-in.  It is used by the
# ZhongGuo phase-two runner when a prepared save must be opened through the
# same lifecycle that historically reached Frontend before Load Save.  The
# generic native-session and all existing callers keep their original
# ``-continuelastsave``/checkpoint behavior when this is unset.
NATIVE_SESSION_FRONTEND_MARKER = "Setting idler 'Frontend'"
NATIVE_SESSION_FRONTEND_HISTORY_MARKER = "End loading of history"
NATIVE_SESSION_FRONTEND_GUI_MARKER = (
    'Loading of "gui/frontend_main.gui" is complete'
)
NATIVE_SESSION_FRONTEND_WINDOW_TITLE = "Crusader Kings III"
NATIVE_SESSION_FRONTEND_WM_NULL_TIMEOUT_MILLISECONDS = 100
NATIVE_SESSION_FRONTEND_FIRST_EVIDENCE_FILENAME = "frontend-first-warmup.json"
NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS = 180.0
_BRIDGE_ENVIRONMENT_KEYS = (
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
)


class _StdinMonitor:
    """Read optional lifecycle commands without blocking process supervision."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lines: SimpleQueue[str] = SimpleQueue()
        self._error: BaseException | None = None
        self._thread = threading.Thread(
            target=self._read,
            name="xar-native-session-stdin",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def _read(self) -> None:
        try:
            for line in self._stream:
                self._lines.put(line)
        except BaseException as error:  # surfaced by the supervising thread
            self._error = error

    def poll(self) -> list[str]:
        if self._error is not None:
            raise AgentError(f"native-session stdin failed: {self._error}")
        lines: list[str] = []
        while True:
            try:
                lines.append(self._lines.get_nowait())
            except Empty:
                return lines


def _emit(stream: TextIO | None, payload: dict[str, object]) -> None:
    if stream is None:
        return
    print(json.dumps(payload, ensure_ascii=False), file=stream, flush=True)


def _status(
    *,
    pid: int,
    pipe_name: str,
    started: float,
    running: bool,
) -> dict[str, object]:
    return {
        "type": "native_session_status",
        "pid": pid,
        "mode": PURE_NATIVE_MODE,
        "pipe": pipe_name,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "running": running,
    }


def _visible_process_windows(pid: int) -> list[int]:
    """Return visible top-level windows owned by one exact process."""
    import win32gui
    import win32process

    windows: list[int] = []

    def collect(hwnd: int, _extra: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        _thread_id, window_pid = win32process.GetWindowThreadProcessId(hwnd)
        if int(window_pid) == pid:
            windows.append(int(hwnd))
        return True

    win32gui.EnumWindows(collect, None)
    return windows


def _process_windows_minimized(pid: int) -> bool | None:
    """Return the visible-window state, or None during a window transition."""
    import win32gui

    windows = _visible_process_windows(pid)
    if not windows:
        return None
    return all(bool(win32gui.IsIconic(hwnd)) for hwnd in windows)


def _minimize_process_windows(
    pid: int,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> bool:
    """Wait for a relaunched CK3 window and restore its prior minimized state."""
    import win32con
    import win32gui

    deadline = time.monotonic() + timeout_seconds
    while True:
        windows = _visible_process_windows(pid)
        if windows:
            for hwnd in windows:
                if not win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            if all(bool(win32gui.IsIconic(hwnd)) for hwnd in windows):
                return True
        now = time.monotonic()
        if now >= deadline:
            return False
        time.sleep(min(poll_interval_seconds, deadline - now))


def _frontend_log_signals(payload: bytes | str) -> dict[str, bool]:
    """Extract the append-only signals used by the frontend-first warm-up.

    The idler line is the historical success marker.  Some no-bridge starts
    reach the menu without emitting that line, however, so the fallback uses
    two independent log milestones and then authenticates the live window.
    Keeping this parser pure makes the fallback easy to test without a game
    process and avoids treating a partial/malformed log as ready.
    """

    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    else:
        text = str(payload)
    idler_seen = NATIVE_SESSION_FRONTEND_MARKER in text
    history_end_seen = NATIVE_SESSION_FRONTEND_HISTORY_MARKER in text
    frontend_gui_complete = NATIVE_SESSION_FRONTEND_GUI_MARKER in text
    return {
        "idler_marker": idler_seen,
        "history_end": history_end_seen,
        "frontend_gui_complete": frontend_gui_complete,
        "fallback_ready": history_end_seen and frontend_gui_complete,
    }


def _probe_frontend_window_responsiveness(
    hwnd: int,
    *,
    timeout_milliseconds: int = NATIVE_SESSION_FRONTEND_WM_NULL_TIMEOUT_MILLISECONDS,
) -> tuple[bool, int, bool]:
    """Read-only ``WM_NULL`` responsiveness probe for one exact HWND.

    This intentionally duplicates the tiny Win32 probe instead of importing
    the visual driver.  A native session must stay independent of screenshots,
    OCR and input modules; ``WM_NULL`` only asks whether the target window's
    message loop is servicing a no-op message.
    """

    import ctypes
    from ctypes import wintypes

    if (
        isinstance(timeout_milliseconds, bool)
        or not isinstance(timeout_milliseconds, int)
        or timeout_milliseconds <= 0
    ):
        raise AgentError("frontend window probe timeout must be positive")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_message_timeout = user32.SendMessageTimeoutW
    send_message_timeout.argtypes = (
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_size_t),
    )
    send_message_timeout.restype = ctypes.c_ssize_t
    is_hung_app_window = user32.IsHungAppWindow
    is_hung_app_window.argtypes = (wintypes.HWND,)
    is_hung_app_window.restype = wintypes.BOOL
    result = ctypes.c_size_t()
    # WM_NULL = 0; SMTO_BLOCK | SMTO_ABORTIFHUNG | SMTO_ERRORONEXIT = 35.
    ctypes.set_last_error(0)
    responded = bool(
        send_message_timeout(
            hwnd,
            0,
            0,
            0,
            35,
            timeout_milliseconds,
            ctypes.byref(result),
        )
    )
    last_error = int(ctypes.get_last_error())
    hung = bool(is_hung_app_window(hwnd))
    return responded, last_error, hung


def _authenticated_frontend_window(
    handle: object, spec: EnvironmentSpec
) -> dict[str, object]:
    """Return authenticated, responsive CK3 frontend-window evidence.

    Every check is read-only.  The process identity is tied to the exact
    ``SessionHandle`` creation timestamp and executable, then the HWND is
    rechecked for visibility, ownership and the canonical CK3 title before a
    ``WM_NULL`` probe.  Transient startup races return ``ready=False`` so the
    caller can keep polling rather than accepting an unrelated window.
    """

    process = getattr(handle, "process", None)
    raw_pid = getattr(process, "pid", None)
    try:
        pid = int(raw_pid)
    except (TypeError, ValueError):
        return {"ready": False, "reason": "missing_process_pid"}
    if pid <= 0:
        return {"ready": False, "reason": "invalid_process_pid", "pid": pid}

    poll = getattr(process, "poll", None)
    if callable(poll):
        try:
            exit_code = poll()
        except Exception as error:
            return {
                "ready": False,
                "pid": pid,
                "reason": "process_poll_failed",
                "error": f"{type(error).__name__}: {error}",
            }
        if exit_code is not None:
            return {
                "ready": False,
                "pid": pid,
                "reason": "process_exited",
                "process_exit_code": exit_code,
            }

    expected_executable = Path(spec.game_exe).resolve()
    expected_creation = getattr(handle, "ck3_creation_date", None)
    if not isinstance(expected_creation, str) or not expected_creation:
        return {
            "ready": False,
            "pid": pid,
            "reason": "missing_handle_creation_date",
        }
    try:
        identity = _process_identity(pid)
    except Exception as error:
        return {
            "ready": False,
            "pid": pid,
            "reason": "process_identity_unavailable",
            "error": f"{type(error).__name__}: {error}",
        }
    if identity is None:
        return {
            "ready": False,
            "pid": pid,
            "reason": "process_identity_missing",
        }

    identity_pid = identity.get("pid")
    identity_parent_pid = identity.get("parent_pid")
    identity_name = str(identity.get("name") or "")
    identity_executable = str(identity.get("executable") or "")
    identity_creation = identity.get("creation_date")
    identity_ok = (
        identity_pid == pid
        and identity_parent_pid == os.getpid()
        and identity_name.casefold() == "ck3.exe"
        and bool(identity_executable)
        and _same_executable(identity_executable, expected_executable)
        and identity_creation == expected_creation
    )
    evidence: dict[str, object] = {
        "ready": False,
        "pid": pid,
        "expected_executable": str(expected_executable),
        "expected_creation_date": expected_creation,
        "identity": identity,
        "identity_authenticated": identity_ok,
    }
    if not identity_ok:
        evidence["reason"] = "process_identity_mismatch"
        return evidence

    image_path = getattr(process, "image_path", None)
    if not callable(image_path):
        evidence["reason"] = "process_handle_image_unavailable"
        return evidence
    try:
        handle_executable = Path(image_path()).resolve()
    except Exception as error:
        evidence["reason"] = "process_handle_image_unavailable"
        evidence["error"] = f"{type(error).__name__}: {error}"
        return evidence
    if not _same_executable(handle_executable, expected_executable):
        evidence["reason"] = "process_handle_image_mismatch"
        evidence["handle_executable"] = str(handle_executable)
        return evidence
    evidence["handle_executable"] = str(handle_executable)

    try:
        import win32gui
        import win32process

        windows = _visible_process_windows(pid)
    except Exception as error:
        evidence["reason"] = "window_enumeration_unavailable"
        evidence["error"] = f"{type(error).__name__}: {error}"
        return evidence

    expected_title = " ".join(NATIVE_SESSION_FRONTEND_WINDOW_TITLE.split())
    candidates: list[dict[str, object]] = []
    for raw_hwnd in windows:
        try:
            hwnd = int(raw_hwnd)
            if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                continue
            _thread_id, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(window_pid) != pid:
                continue
            title = str(win32gui.GetWindowText(hwnd) or "")
            normalized_title = " ".join(title.split())
            if normalized_title != expected_title:
                continue
            try:
                responded, last_error, hung = _probe_frontend_window_responsiveness(
                    hwnd
                )
            except Exception as error:
                candidate = {
                    "hwnd": hwnd,
                    "pid": pid,
                    "title": title,
                    "wm_null_responded": False,
                    "is_hung_app_window": None,
                    "reason": "responsiveness_probe_unavailable",
                    "error": f"{type(error).__name__}: {error}",
                }
                candidates.append(candidate)
                continue
            candidate = {
                "hwnd": hwnd,
                "pid": pid,
                "title": title,
                "wm_null_responded": responded,
                "wm_null_last_error": last_error,
                "is_hung_app_window": hung,
                "responsive": responded and not hung,
            }
            candidates.append(candidate)
            if responded and not hung:
                evidence.update(
                    {
                        "ready": True,
                        "reason": "authenticated_responsive_frontend",
                        "window": candidate,
                    }
                )
                return evidence
        except Exception as error:
            candidates.append(
                {
                    "hwnd": raw_hwnd,
                    "pid": pid,
                    "reason": "window_identity_check_failed",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
    evidence["reason"] = (
        "frontend_window_not_found"
        if not candidates
        else "frontend_window_not_responsive"
    )
    evidence["windows"] = candidates
    return evidence


def _validate_frontend_first_load_save_name(value: object) -> str:
    """Validate the save basename used by the opt-in frontend-first path.

    ``runtime._ck3_launch_command`` applies the same restriction to
    ``-loadsave``.  Keep a local copy here so the opt-in can be rejected before
    the warm-up process is launched and so callers cannot smuggle a path or a
    filename extension into the isolated profile.
    """

    if (
        not isinstance(value, str)
        or not value
        or Path(value).name != value
        or Path(value).suffix
        or any(character in value for character in ("/", "\\", "\0"))
    ):
        raise AgentError(
            "frontend-first load save name requires one save basename "
            "without a path or extension"
        )
    return value


def _frontend_first_target(
    spec: EnvironmentSpec, load_save_name: str
) -> dict[str, object]:
    """Bind the opt-in second launch to one immutable profile save file."""

    name = _validate_frontend_first_load_save_name(load_save_name)
    save_root = (spec.profile_dir / "save games").resolve()
    path = (save_root / f"{name}.ck3").resolve()
    try:
        path.relative_to(save_root)
    except ValueError as error:
        raise AgentError(
            "frontend-first load save escaped the isolated profile"
        ) from error
    try:
        size = path.stat().st_size
    except OSError as error:
        raise AgentError(
            f"frontend-first load save is unavailable: {path}: {error}"
        ) from error
    if not path.is_file() or size <= 0:
        raise AgentError(
            "frontend-first load save must be a non-empty regular file: "
            f"{path}"
        )
    return {
        "name": name,
        "load_save_name": name,
        "path": str(path),
        "size": size,
        "sha256": _sha256_file(path),
    }


def _frontend_first_evidence_path(spec: EnvironmentSpec) -> Path:
    return (
        spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_SESSION_FRONTEND_FIRST_EVIDENCE_FILENAME
    )


def _write_frontend_first_evidence(
    spec: EnvironmentSpec, evidence: dict[str, object]
) -> None:
    """Persist warm-up state so a Phase2 binding can wait for the final PID."""

    write_json_atomic(_frontend_first_evidence_path(spec), evidence)


@contextmanager
def _bridge_injection_disabled() -> Iterator[None]:
    """Temporarily make the frontend warm-up a no-bridge launch.

    The final Phase2 process still receives the explicit native bridge config.
    Keeping this scope local prevents a warm-up's environment mutation from
    leaking into the save-loading relaunch or into another caller in the
    supervising process.
    """

    missing = object()
    previous: dict[str, str | object] = {
        key: os.environ.get(key, missing) for key in _BRIDGE_ENVIRONMENT_KEYS
    }
    os.environ[NATIVE_BRIDGE_MODE_ENV] = NATIVE_BRIDGE_DISABLED
    for key in (
        NATIVE_BRIDGE_PIPE_ENV,
        NATIVE_BRIDGE_DLL_ENV,
        NATIVE_BRIDGE_INJECTOR_ENV,
    ):
        os.environ.pop(key, None)
    try:
        if native_bridge_launch_config_from_environment() is not None:
            raise AgentError(
                "frontend-first warm-up could not disable bridge injection"
            )
        yield
    finally:
        for key, value in previous.items():
            if value is missing:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)


def _wait_for_frontend_marker(
    handle: object,
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
    stop_event: threading.Event | None,
) -> dict[str, object]:
    """Wait for CK3's first clean frontend evidence.

    ``launch`` clears the isolated ``debug.log`` before creating CK3, so a
    marker observed here belongs to this warm-up process.  The historical
    ``Setting idler 'Frontend'`` marker remains the fast path.  On no-bridge
    starts that reach the menu without that line, the fallback requires both
    the history and frontend-GUI completion lines plus an authenticated,
    responsive CK3 window.  The helper never sends gameplay input.
    """

    started = time.monotonic()
    deadline = started + timeout_seconds
    log_path = (spec.profile_dir / "logs" / "debug.log").resolve()
    polls = 0
    last_log_size = 0
    last_read_error: str | None = None
    last_signals: dict[str, bool] = {
        "idler_marker": False,
        "history_end": False,
        "frontend_gui_complete": False,
        "fallback_ready": False,
    }
    last_window_evidence: dict[str, object] | None = None
    while True:
        polls += 1
        try:
            payload = log_path.read_bytes()
            last_log_size = len(payload)
            last_read_error = None
            last_signals = _frontend_log_signals(payload)
            if last_signals["idler_marker"]:
                elapsed = round(max(0.0, time.monotonic() - started), 3)
                return {
                    "marker": NATIVE_SESSION_FRONTEND_MARKER,
                    "mode": "idler-marker",
                    "path": str(log_path),
                    "seen": True,
                    "polls": polls,
                    "log_bytes": last_log_size,
                    "elapsed_seconds": elapsed,
                    "observed_at": utc_now(),
                    "signals": last_signals,
                }
            if last_signals["fallback_ready"]:
                last_window_evidence = _authenticated_frontend_window(
                    handle, spec
                )
                if last_window_evidence.get("ready") is True:
                    elapsed = round(max(0.0, time.monotonic() - started), 3)
                    return {
                        "marker": NATIVE_SESSION_FRONTEND_MARKER,
                        "mode": "log-and-authenticated-window",
                        "fallback": True,
                        "path": str(log_path),
                        "seen": True,
                        "polls": polls,
                        "log_bytes": last_log_size,
                        "elapsed_seconds": elapsed,
                        "observed_at": utc_now(),
                        "signals": last_signals,
                        "window": last_window_evidence,
                    }
        except FileNotFoundError:
            # CK3 may create the log a little after resume.  Keep polling
            # within the explicit warm-up bound instead of treating that
            # normal transition as a launch failure.
            last_log_size = 0
            last_read_error = "log_not_created"
        except OSError as error:
            last_read_error = f"{type(error).__name__}: {error}"

        process = getattr(handle, "process", None)
        poll = getattr(process, "poll", None)
        process_exit_code = poll() if callable(poll) else None
        if process_exit_code is not None:
            detail = {
                "marker": NATIVE_SESSION_FRONTEND_MARKER,
                "path": str(log_path),
                "seen": False,
                "polls": polls,
                "log_bytes": last_log_size,
                "process_exit_code": process_exit_code,
                "last_read_error": last_read_error,
                "signals": last_signals,
                "window": last_window_evidence,
                "elapsed_seconds": round(
                    max(0.0, time.monotonic() - started), 3
                ),
            }
            raise AgentError(
                "frontend-first warm-up CK3 exited before frontend evidence: "
                f"{detail}"
            )
        if stop_event is not None and stop_event.is_set():
            raise AgentError(
                "frontend-first warm-up cancelled before frontend evidence"
            )
        now = time.monotonic()
        if now >= deadline:
            detail = {
                "marker": NATIVE_SESSION_FRONTEND_MARKER,
                "path": str(log_path),
                "seen": False,
                "polls": polls,
                "log_bytes": last_log_size,
                "last_read_error": last_read_error,
                "signals": last_signals,
                "window": last_window_evidence,
                "elapsed_seconds": round(max(0.0, now - started), 3),
            }
            raise AgentError(
                "frontend-first warm-up timed out before frontend evidence: "
                f"{detail}"
            )
        time.sleep(min(poll_interval_seconds, max(0.0, deadline - now)))


def native_session(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    poll_interval_seconds: float = 0.05,
    cold_start_checkpoint: bool = False,
    stop_event: threading.Event | None = None,
    verify_prepared_profile: bool = True,
    frontend_first_load_save_name: str | None = None,
    frontend_first_timeout_seconds: float = (
        NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS
    ),
) -> dict[str, object]:
    """Launch/inject CK3 and supervise it without any visual fallback path."""
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise AgentError("native-session timeout must be finite and positive")
    if poll_interval_seconds <= 0:
        raise AgentError("native-session poll interval must be positive")
    if not isinstance(verify_prepared_profile, bool):
        raise AgentError("native-session verify_prepared_profile must be boolean")
    if frontend_first_load_save_name is not None:
        _validate_frontend_first_load_save_name(frontend_first_load_save_name)
        if cold_start_checkpoint:
            raise AgentError(
                "frontend-first warm-up cannot combine with a cold checkpoint"
            )
        if (
            isinstance(frontend_first_timeout_seconds, bool)
            or not isinstance(frontend_first_timeout_seconds, (int, float))
            or not math.isfinite(float(frontend_first_timeout_seconds))
            or frontend_first_timeout_seconds <= 0
        ):
            raise AgentError(
                "frontend-first warm-up timeout must be finite and positive"
            )

    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != PURE_NATIVE_MODE:
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "native-session requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )

    ensure_state_path_safe(spec.state_dir)
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "native-session"):
            return _native_session_locked(
                spec,
                config,
                float(timeout_seconds),
                input_stream=input_stream,
                output_stream=output_stream,
                poll_interval_seconds=float(poll_interval_seconds),
                cold_start_checkpoint=cold_start_checkpoint,
                stop_event=stop_event,
                verify_prepared_profile=verify_prepared_profile,
                frontend_first_load_save_name=frontend_first_load_save_name,
                frontend_first_timeout_seconds=float(
                    frontend_first_timeout_seconds
                ),
            )


def _native_session_locked(
    spec: EnvironmentSpec,
    config: NativeBridgeLaunchConfig,
    timeout_seconds: float,
    *,
    input_stream: TextIO | None,
    output_stream: TextIO | None,
    poll_interval_seconds: float,
    cold_start_checkpoint: bool = False,
    stop_event: threading.Event | None = None,
    verify_prepared_profile: bool = True,
    frontend_first_load_save_name: str | None = None,
    frontend_first_timeout_seconds: float = (
        NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS
    ),
) -> dict[str, object]:
    started_wall = utc_now()
    started = time.monotonic()
    deadline = started + timeout_seconds
    handle = None
    exit_reason = "launch_error"
    process_exit_code: int | None = None
    primary_error: BaseException | None = None
    shutdown: dict[str, object] | None = None
    restart_shutdowns: list[dict[str, object]] = []
    restart_count = 0
    last_pid: int | None = None
    last_known_window_minimized: bool | None = None
    next_window_state_sample = started
    queue = PersistentSessionQueue(
        spec.state_dir / NATIVE_SESSION_QUEUE_DIRNAME,
        supported_commands=(
            "status",
            "stop",
            NATIVE_SESSION_RESTORE_COMMAND,
            NATIVE_SESSION_START_NEXT_EPISODE_COMMAND,
        ),
        action_steps=(
            NATIVE_SESSION_RESTORE_COMMAND,
            NATIVE_SESSION_START_NEXT_EPISODE_COMMAND,
        ),
    )
    initial_checkpoint = (
        _validate_cold_start_checkpoint(spec, config)
        if cold_start_checkpoint
        else None
    )
    frontend_first_target = (
        _frontend_first_target(spec, frontend_first_load_save_name)
        if frontend_first_load_save_name is not None
        else None
    )
    if frontend_first_target is not None and initial_checkpoint is not None:
        raise AgentError(
            "frontend-first warm-up cannot combine with a cold checkpoint"
        )
    if frontend_first_target is not None and (
        isinstance(frontend_first_timeout_seconds, bool)
        or not isinstance(frontend_first_timeout_seconds, (int, float))
        or not math.isfinite(float(frontend_first_timeout_seconds))
        or frontend_first_timeout_seconds <= 0
    ):
        raise AgentError(
            "frontend-first warm-up timeout must be finite and positive"
        )
    frontend_first_warmup: dict[str, object] | None = None
    if frontend_first_target is not None:
        frontend_first_warmup = {
            "enabled": True,
            "status": "starting",
            "pipe": config.pipe_name,
            "load_save_name": frontend_first_target["load_save_name"],
            "target": frontend_first_target,
            "marker": NATIVE_SESSION_FRONTEND_MARKER,
            "timeout_seconds": float(frontend_first_timeout_seconds),
            "evidence_path": str(_frontend_first_evidence_path(spec).resolve()),
            "warmup_bridge": {
                "mode": NATIVE_BRIDGE_DISABLED,
                "dll_injection": False,
                "mcp": False,
            },
            "initial_launch": {
                "continue_last_save": False,
                "load_save_name": None,
                "native_bridge_mode": NATIVE_BRIDGE_DISABLED,
                "dll_injection": False,
            },
        }
        _write_frontend_first_evidence(spec, frontend_first_warmup)

    try:
        # Passing the validated config explicitly prevents environment changes
        # from selecting hybrid fallback between command parsing and launch.
        initial_launch_options: dict[str, object] = {"native_bridge": config}
        if initial_checkpoint is None and frontend_first_target is None:
            initial_launch_options["continue_last_save"] = True
        elif initial_checkpoint is not None:
            initial_launch_options["load_save_name"] = (
                NATIVE_SESSION_CHECKPOINT_LOAD_NAME
            )
        # Default callers retain the production environment-manifest gate and
        # the historical launch call shape.  ZhongGuo phase-two is the sole
        # opt-out: its runner already freezes its own isolated bootstrap,
        # runtime identity and mount inventory, while this generic verifier is
        # hard-bound to the Eternal Recurrence singleton profile.
        if not verify_prepared_profile:
            initial_launch_options["verify_prepared_profile"] = False
        if frontend_first_warmup is None:
            handle = launch(spec, **initial_launch_options)
        else:
            # The clean Frontend warm-up is intentionally a no-bridge control:
            # current evidence shows that bridge injection is not needed to
            # establish the marker and must not contaminate this diagnostic
            # phase.  The final save-loading process below receives ``config``
            # on the same pipe.
            with _bridge_injection_disabled():
                handle = launch(
                    spec,
                    native_bridge=None,
                    **{
                        key: value
                        for key, value in initial_launch_options.items()
                        if key != "native_bridge"
                    },
                )
        pid = int(handle.process.pid)
        last_pid = pid
        if frontend_first_warmup is None:
            _emit(
                output_stream,
                {
                    "type": "native_session_ready",
                    "pid": pid,
                    "mode": PURE_NATIVE_MODE,
                    "pipe": config.pipe_name,
                    "lifecycle_queue": queue.descriptor(),
                    "cold_start_checkpoint": initial_checkpoint,
                },
            )
        else:
            frontend_first_warmup["status"] = "frontend_launch_started"
            frontend_first_warmup["warmup_pid"] = pid
            frontend_first_warmup["warmup_started_at"] = utc_now()
            _write_frontend_first_evidence(spec, frontend_first_warmup)
            _emit(
                output_stream,
                {
                    "type": "native_session_frontend_first_warmup_started",
                    "pid": pid,
                    "mode": PURE_NATIVE_MODE,
                    "pipe": config.pipe_name,
                    "load_save_name": frontend_first_target[
                        "load_save_name"
                    ],
                },
            )
            frontend_timeout = min(
                float(frontend_first_timeout_seconds),
                max(0.001, deadline - time.monotonic()),
            )
            marker_evidence = _wait_for_frontend_marker(
                handle,
                spec,
                timeout_seconds=frontend_timeout,
                poll_interval_seconds=poll_interval_seconds,
                stop_event=stop_event,
            )
            frontend_first_warmup["status"] = "frontend_marker_seen"
            frontend_first_warmup["frontend_marker"] = marker_evidence
            frontend_first_warmup["frontend_seen_at"] = utc_now()
            _write_frontend_first_evidence(spec, frontend_first_warmup)

            # Stop the clean Frontend process before selecting the save.  This
            # is a distinct warm-up, not a gameplay restore, so it must not
            # increment the managed save/restore restart_count.
            warmup_shutdown = stop_tracked(handle, require_running=False)
            handle = None
            frontend_first_warmup["warmup_shutdown"] = warmup_shutdown
            if warmup_shutdown.get("ok") is not True:
                frontend_first_warmup["status"] = "warmup_shutdown_failed"
                _write_frontend_first_evidence(spec, frontend_first_warmup)
                raise AgentError(
                    "frontend-first warm-up shutdown was not proven: "
                    + "; ".join(
                        str(item)
                        for item in warmup_shutdown.get("contract_errors", [])
                    )
                )

            # Re-bind the exact save immediately before the second launch.
            # The seed runner copies its immutable source before this point;
            # a changed byte must not silently select a different campaign.
            final_target = _frontend_first_target(
                spec, str(frontend_first_target["load_save_name"])
            )
            if (
                final_target["size"] != frontend_first_target["size"]
                or final_target["sha256"] != frontend_first_target["sha256"]
            ):
                frontend_first_warmup["status"] = "target_changed"
                frontend_first_warmup["target_before_final_launch"] = final_target
                _write_frontend_first_evidence(spec, frontend_first_warmup)
                raise AgentError(
                    "frontend-first load save changed between warm-up and "
                    "the final launch"
                )
            frontend_first_warmup["target_before_final_launch"] = final_target
            frontend_first_warmup["status"] = "final_launch_starting"
            _write_frontend_first_evidence(spec, frontend_first_warmup)
            final_launch_options: dict[str, object] = {
                "native_bridge": config,
                "load_save_name": str(final_target["load_save_name"]),
                # The first launch already owns the Phase2 profile gate; do
                # not repeat a repository-wide fingerprint during relaunch.
                "verify_prepared_profile": False,
            }
            handle = launch(spec, **final_launch_options)
            pid = int(handle.process.pid)
            last_pid = pid
            frontend_first_warmup["status"] = "ready"
            frontend_first_warmup["final_pid"] = pid
            frontend_first_warmup["final_launch_started_at"] = utc_now()
            frontend_first_warmup["final_launch"] = {
                "continue_last_save": False,
                "load_save_name": str(final_target["load_save_name"]),
                "pipe": config.pipe_name,
                "native_bridge_mode": config.mode,
                "dll_injection": True,
            }
            _write_frontend_first_evidence(spec, frontend_first_warmup)
            _emit(
                output_stream,
                {
                    "type": "native_session_ready",
                    "pid": pid,
                    "mode": PURE_NATIVE_MODE,
                    "pipe": config.pipe_name,
                    "lifecycle_queue": queue.descriptor(),
                    "cold_start_checkpoint": None,
                    "frontend_first_warmup": frontend_first_warmup,
                },
            )
        stdin = _StdinMonitor(input_stream) if input_stream is not None else None
        if stdin is not None:
            stdin.start()

        while True:
            process_exit_code = handle.process.poll()
            if process_exit_code is not None:
                exit_reason = "process_exit"
                break
            now = time.monotonic()
            if now >= deadline:
                exit_reason = "timeout"
                break
            stop_requested = bool(
                stop_event is not None and stop_event.is_set()
            )
            if not stop_requested and now >= next_window_state_sample:
                sampled_window_state = _process_windows_minimized(pid)
                if sampled_window_state is not None:
                    last_known_window_minimized = sampled_window_state
                next_window_state_sample = now + 0.5
            if not stop_requested and stdin is not None:
                for line in stdin.poll():
                    command = line.strip().casefold()
                    if not command:
                        continue
                    if command == "status":
                        _emit(
                            output_stream,
                            _status(
                                pid=pid,
                                pipe_name=config.pipe_name,
                                started=started,
                                running=handle.process.poll() is None,
                            ),
                        )
                    elif command == "stop":
                        stop_requested = True
                        break
                    else:
                        _emit(
                            output_stream,
                            {
                                "type": "native_session_command_error",
                                "command": command,
                                "error": "only status and stop are supported",
                            },
                        )
            if not stop_requested:
                for request in queue.poll():
                    if request.error is not None:
                        queue.respond(request, ok=False, error=request.error)
                        continue
                    if request.command == "status":
                        queue.respond(
                            request,
                            ok=True,
                            result=_status(
                                pid=pid,
                                pipe_name=config.pipe_name,
                                started=started,
                                running=handle.process.poll() is None,
                            ),
                        )
                        continue
                    if request.command == "stop":
                        queue.respond(
                            request,
                            ok=True,
                            result={"status": "stopping", "pid": pid},
                        )
                        stop_requested = True
                        break
                    if request.command not in {
                        NATIVE_SESSION_RESTORE_COMMAND,
                        NATIVE_SESSION_START_NEXT_EPISODE_COMMAND,
                    }:
                        queue.respond(
                            request,
                            ok=False,
                            error=(
                                "native-session supports status, stop, "
                                f"{NATIVE_SESSION_RESTORE_COMMAND}, and "
                                f"{NATIVE_SESSION_START_NEXT_EPISODE_COMMAND}"
                            ),
                        )
                        continue
                    try:
                        starting_next_episode = (
                            request.command
                            == NATIVE_SESSION_START_NEXT_EPISODE_COMMAND
                        )
                        selected_save = (
                            _validate_start_next_episode_request(
                                request, config, spec
                            )
                            if starting_next_episode
                            else _validate_restore_request(request, config, spec)
                        )
                        previous_pid = int(handle.process.pid)
                        sampled_window_state = _process_windows_minimized(
                            previous_pid
                        )
                        if sampled_window_state is not None:
                            last_known_window_minimized = sampled_window_state
                        preserve_minimized = last_known_window_minimized is True
                        restart_shutdown = stop_tracked(
                            handle, require_running=False
                        )
                        handle = None
                        if restart_shutdown.get("ok") is not True:
                            raise AgentError(
                                "restore-checkpoint could not stop the current "
                                "CK3 process: "
                                + "; ".join(
                                    str(item)
                                    for item in restart_shutdown.get(
                                        "contract_errors", []
                                    )
                                )
                            )
                        # The managed CK3 process is now stopped.  Recheck the
                        # exact bytes immediately before asking Jomini to load
                        # this filename so the lifecycle response describes the
                        # file actually selected for the replacement process.
                        selected_save = (
                            _validate_start_next_episode_request(
                                request, config, spec
                            )
                            if starting_next_episode
                            else _validate_restore_request(request, config, spec)
                        )
                        handle = launch(
                            spec,
                            native_bridge=config,
                            load_save_name=str(selected_save["load_save_name"]),
                            # The session owns both global launch and state
                            # locks.  Its first launch already verified the
                            # committed profile; repeating the full Git/runtime
                            # fingerprint here can block a hot restore without
                            # adding any new gameplay information.
                            verify_prepared_profile=False,
                        )
                        pid = int(handle.process.pid)
                        minimized_preserved = False
                        if preserve_minimized:
                            minimized_preserved = _minimize_process_windows(
                                pid,
                                timeout_seconds=min(
                                    30.0,
                                    max(0.001, deadline - time.monotonic()),
                                ),
                                poll_interval_seconds=poll_interval_seconds,
                            )
                            if not minimized_preserved:
                                raise AgentError(
                                    "restore-checkpoint relaunched CK3 but "
                                    "could not preserve its minimized window state"
                                )
                        last_known_window_minimized = (
                            True if minimized_preserved else None
                        )
                        next_window_state_sample = time.monotonic() + 0.5
                        result = {
                            "status": "relaunched",
                            "previous_pid": previous_pid,
                            "pid": pid,
                            "mode": PURE_NATIVE_MODE,
                            "pipe": config.pipe_name,
                            "continue_last_save": False,
                            "load_save_name": selected_save["load_save_name"],
                            "lifecycle_intent": (
                                "new_episode"
                                if starting_next_episode
                                else "restore"
                            ),
                            "previous_window_minimized": preserve_minimized,
                            "minimized_state_preserved": minimized_preserved,
                        }
                        if starting_next_episode:
                            result["episode_seed"] = selected_save
                        else:
                            result["checkpoint"] = selected_save
                        queue.respond(request, ok=True, result=result)
                        _emit(
                            output_stream,
                            {
                                "type": (
                                    "native_session_episode_started"
                                    if starting_next_episode
                                    else "native_session_restored"
                                ),
                                "request_id": request.request_id,
                                **result,
                            },
                        )
                    except BaseException as error:
                        queue.respond(
                            request,
                            ok=False,
                            error=f"{type(error).__name__}: {error}",
                        )
                        raise
                    last_pid = pid
                    restart_shutdowns.append(restart_shutdown)
                    restart_count += 1
                    process_exit_code = None
            if stop_requested:
                exit_reason = "stop"
                break
            time.sleep(min(poll_interval_seconds, max(0.0, deadline - now)))
    except KeyboardInterrupt:
        exit_reason = "keyboard_interrupt"
    except BaseException as error:
        primary_error = error
        if frontend_first_warmup is not None:
            frontend_first_warmup["status"] = "failed"
            frontend_first_warmup["failure_reason"] = (
                f"{type(error).__name__}: {error}"
            )
            try:
                _write_frontend_first_evidence(
                    spec, frontend_first_warmup
                )
            except BaseException as evidence_error:
                # Preserve the launch failure while making evidence-write
                # loss visible to the caller and the retained state tree.
                frontend_first_warmup["evidence_write_error"] = (
                    f"{type(evidence_error).__name__}: {evidence_error}"
                )
    finally:
        if handle is not None:
            try:
                shutdown = stop_tracked(handle, require_running=False)
                if shutdown.get("ok") is not True and primary_error is None:
                    primary_error = AgentError(
                        "native-session shutdown failed: "
                        + "; ".join(
                            str(item)
                            for item in shutdown.get("contract_errors", [])
                        )
                    )
            except BaseException as error:
                if primary_error is None:
                    primary_error = error

    elapsed = round(max(0.0, time.monotonic() - started), 3)
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_native_headless_session",
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "pid": last_pid,
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": elapsed,
        "exit_reason": exit_reason,
        "process_exit_code": process_exit_code,
        "shutdown": shutdown,
        "restart_count": restart_count,
        "restart_shutdowns": restart_shutdowns,
        "cold_start_checkpoint": initial_checkpoint,
        "frontend_first_warmup": frontend_first_warmup,
        "ok": (
            primary_error is None
            and (shutdown is None or shutdown.get("ok") is True)
            and not (
                exit_reason == "process_exit"
                and process_exit_code not in (None, 0)
            )
        ),
    }
    if primary_error is not None:
        raise AgentError(
            "native-session failed after "
            f"{elapsed:.3f}s ({exit_reason}): {primary_error}"
        ) from primary_error
    return report


def _validate_restore_request(
    request: SessionQueueRequest,
    config: NativeBridgeLaunchConfig,
    spec: EnvironmentSpec,
) -> dict[str, object]:
    """Bind a lifecycle request to one exact checkpoint in this profile."""
    payload = request.payload or {}
    requested_pipe = payload.get("pipe")
    if requested_pipe != config.pipe_name:
        raise AgentError(
            "restore-checkpoint pipe differs from the native-session pipe: "
            f"{requested_pipe!r} != {config.pipe_name!r}"
        )
    checkpoint_name = payload.get("checkpoint_name")
    if checkpoint_name != NATIVE_SESSION_CHECKPOINT_FILENAME:
        raise AgentError(
            "restore-checkpoint requires the managed checkpoint filename "
            f"{NATIVE_SESSION_CHECKPOINT_FILENAME!r}"
        )
    expected_size = payload.get("checkpoint_size")
    expected_sha256 = payload.get("checkpoint_sha256")
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size <= 0
        or not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in expected_sha256
        )
    ):
        raise AgentError(
            "restore-checkpoint requires exact checkpoint_size and sha256"
        )
    checkpoint_path = (
        spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
    )
    try:
        size = checkpoint_path.stat().st_size
    except OSError as error:
        raise AgentError(
            f"restore checkpoint is unavailable: {checkpoint_path}: {error}"
        ) from error
    if size != expected_size:
        raise AgentError(
            "restore checkpoint size changed before launch: "
            f"{size} != {expected_size}"
        )
    digest = _sha256_file(checkpoint_path)
    if digest != expected_sha256:
        raise AgentError(
            "restore checkpoint bytes changed before launch: "
            f"{digest} != {expected_sha256}"
        )
    saved_date_raw = payload.get("checkpoint_saved_date_raw")
    if saved_date_raw is not None and (
        isinstance(saved_date_raw, bool) or not isinstance(saved_date_raw, int)
    ):
        raise AgentError("checkpoint_saved_date_raw must be an integer or null")
    return {
        "name": NATIVE_SESSION_CHECKPOINT_FILENAME,
        "load_save_name": NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
        "path": str(checkpoint_path.resolve()),
        "size": size,
        "sha256": digest,
        "saved_date_raw": saved_date_raw,
    }


def _validate_start_next_episode_request(
    request: SessionQueueRequest,
    config: NativeBridgeLaunchConfig,
    spec: EnvironmentSpec,
) -> dict[str, object]:
    """Bind a new-episode relaunch to the immutable campaign seed."""
    payload = request.payload or {}
    if payload.get("pipe") != config.pipe_name:
        raise AgentError("start-next-episode pipe differs from native-session")
    if payload.get("seed_name") != NATIVE_SESSION_EPISODE_SEED_FILENAME:
        raise AgentError(
            "start-next-episode requires xar_episode_seed.ck3"
        )
    expected_size = payload.get("seed_size")
    expected_sha256 = payload.get("seed_sha256")
    seed_date_raw = payload.get("seed_date_raw")
    seed_character_id = payload.get("seed_character_id")
    source_run_id = payload.get("source_run_id")
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size <= 0
        or not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
        or isinstance(seed_date_raw, bool)
        or not isinstance(seed_date_raw, int)
        or isinstance(seed_character_id, bool)
        or not isinstance(seed_character_id, int)
        or not isinstance(source_run_id, str)
        or not source_run_id
    ):
        raise AgentError("start-next-episode seed metadata is incomplete")
    seed_path = (
        spec.profile_dir
        / "save games"
        / NATIVE_SESSION_EPISODE_SEED_FILENAME
    )
    try:
        size = seed_path.stat().st_size
    except OSError as error:
        raise AgentError(f"episode seed is unavailable: {seed_path}: {error}") from error
    digest = _sha256_file(seed_path)
    if size != expected_size or digest != expected_sha256:
        raise AgentError("episode seed bytes differ from the lifecycle request")
    return {
        "name": NATIVE_SESSION_EPISODE_SEED_FILENAME,
        "load_save_name": NATIVE_SESSION_EPISODE_SEED_LOAD_NAME,
        "path": str(seed_path.resolve()),
        "size": size,
        "sha256": digest,
        "date_raw": seed_date_raw,
        "character_id": seed_character_id,
        "source_run_id": source_run_id,
        "immutable": True,
    }


def _validate_cold_start_checkpoint(
    spec: EnvironmentSpec, config: NativeBridgeLaunchConfig
) -> dict[str, object]:
    """Resolve the exact v2 checkpoint selected by an explicit cold start."""
    return validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)


def validate_cold_start_checkpoint_for_pipe(
    spec: EnvironmentSpec, pipe_name: str
) -> dict[str, object]:
    """Resolve a v2 checkpoint without requiring a bridge binary.

    The driver-state pipe remains part of the immutable checkpoint anchor.  A
    no-injection startup control therefore supplies the pipe whose prior
    native session created the checkpoint, but never constructs or injects a
    native bridge configuration.
    """
    if not isinstance(pipe_name, str) or not pipe_name:
        raise AgentError("cold checkpoint pipe name must be nonempty")
    state_path = (
        spec.state_dir / NATIVE_SESSION_QUEUE_DIRNAME / NATIVE_DRIVER_STATE_FILENAME
    )
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(
            f"cold checkpoint state is unavailable: {state_path}: {error}"
        ) from error
    checkpoint = payload.get("last_checkpoint") if isinstance(payload, dict) else None
    if (
        not isinstance(payload, dict)
        or payload.get("format_version") != 2
        or payload.get("pipe_name") != pipe_name
        or not isinstance(checkpoint, dict)
        or checkpoint.get("name") != NATIVE_SESSION_CHECKPOINT_FILENAME
    ):
        raise AgentError(
            "cold checkpoint start requires a v2 driver state for this pipe"
        )
    expected_size = checkpoint.get("size")
    expected_sha256 = checkpoint.get("sha256")
    saved_date_raw = checkpoint.get("date_raw")
    history_index = checkpoint.get("history_index")
    character_id = payload.get("episode_character_id")
    run_id = payload.get("episode_run_id")
    history = payload.get("command_history")
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size <= 0
        or not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
        or isinstance(saved_date_raw, bool)
        or not isinstance(saved_date_raw, int)
        or isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or history_index < 1
        or isinstance(character_id, bool)
        or not isinstance(character_id, int)
        or not isinstance(run_id, str)
        or not run_id
        or not isinstance(history, list)
        or history_index > len(history)
        or checkpoint.get("episode_character_id") != character_id
        or checkpoint.get("episode_run_id") != run_id
    ):
        raise AgentError("cold checkpoint state has an incomplete checkpoint anchor")
    anchor = history[history_index - 1]
    result = anchor.get("result") if isinstance(anchor, dict) else None
    saved = result.get("checkpoint") if isinstance(result, dict) else None
    if (
        not isinstance(anchor, dict)
        or anchor.get("index") != history_index
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or not isinstance(saved, dict)
        or saved.get("size") != expected_size
        or saved.get("sha256") != expected_sha256
        or saved.get("date_raw") != saved_date_raw
    ):
        raise AgentError("cold checkpoint history anchor does not match the save")
    checkpoint_path = (
        spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
    )
    try:
        size = checkpoint_path.stat().st_size
    except OSError as error:
        raise AgentError(
            f"cold checkpoint is unavailable: {checkpoint_path}: {error}"
        ) from error
    digest = _sha256_file(checkpoint_path)
    if size != expected_size or digest != expected_sha256:
        raise AgentError("cold checkpoint bytes differ from the v2 driver state")
    return {
        "name": NATIVE_SESSION_CHECKPOINT_FILENAME,
        "load_save_name": NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
        "path": str(checkpoint_path.resolve()),
        "size": size,
        "sha256": digest,
        "saved_date_raw": saved_date_raw,
        "history_index": history_index,
    }


def validate_episode_seed_for_state(
    spec: EnvironmentSpec,
) -> dict[str, object]:
    """Resolve the immutable next-episode seed without launching CK3."""
    metadata_path = (
        spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_SESSION_EPISODE_SEED_METADATA_FILENAME
    )
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(
            f"episode seed metadata is unavailable: {metadata_path}: {error}"
        ) from error
    expected_path = (
        spec.profile_dir
        / "save games"
        / NATIVE_SESSION_EPISODE_SEED_FILENAME
    ).resolve()
    size = metadata.get("size") if isinstance(metadata, dict) else None
    digest = metadata.get("sha256") if isinstance(metadata, dict) else None
    date_raw = (
        metadata.get("date_raw") if isinstance(metadata, dict) else None
    )
    character_id = (
        metadata.get("character_id") if isinstance(metadata, dict) else None
    )
    source_run_id = (
        metadata.get("source_run_id") if isinstance(metadata, dict) else None
    )
    if (
        not isinstance(metadata, dict)
        or metadata.get("format_version") != 1
        or metadata.get("name") != NATIVE_SESSION_EPISODE_SEED_FILENAME
        or metadata.get("immutable") is not True
        or Path(str(metadata.get("path", ""))).resolve() != expected_path
        or isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or isinstance(character_id, bool)
        or not isinstance(character_id, int)
        or not isinstance(source_run_id, str)
        or not source_run_id
    ):
        raise AgentError("episode seed metadata is incomplete")
    try:
        actual_size = expected_path.stat().st_size
    except OSError as error:
        raise AgentError(
            f"episode seed is unavailable: {expected_path}: {error}"
        ) from error
    actual_digest = _sha256_file(expected_path)
    if actual_size != size or actual_digest != digest:
        raise AgentError("episode seed bytes differ from immutable metadata")
    return {
        **metadata,
        "path": str(expected_path),
        "size": actual_size,
        "sha256": actual_digest,
        "metadata_path": str(metadata_path.resolve()),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_from_cli(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    cold_start_checkpoint: bool = False,
) -> dict[str, object]:
    """CLI adapter kept here so the generic CLI never imports visual code."""
    return native_session(
        spec,
        timeout_seconds=timeout_seconds,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
        cold_start_checkpoint=cold_start_checkpoint,
    )
