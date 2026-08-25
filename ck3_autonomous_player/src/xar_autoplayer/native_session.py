"""Lifecycle supervisor for a pure native-headless CK3 MCP session.

This module deliberately depends only on the process runtime.  It does not
import the visual driver, OCR, screenshots, or desktop input modules.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from queue import Empty, SimpleQueue
import sys
import threading
import time
from typing import TextIO

from .bridge.session_queue import PersistentSessionQueue, SessionQueueRequest
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .locking import exclusive_launch_lock, exclusive_state_lock
from .runtime import (
    NativeBridgeLaunchConfig,
    launch,
    native_bridge_launch_config_from_environment,
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
NATIVE_DRIVER_STATE_FILENAME = "driver-state.json"


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


def native_session(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    poll_interval_seconds: float = 0.05,
    cold_start_checkpoint: bool = False,
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

    try:
        # Passing the validated config explicitly prevents environment changes
        # from selecting hybrid fallback between command parsing and launch.
        if initial_checkpoint is None:
            handle = launch(
                spec,
                native_bridge=config,
                continue_last_save=True,
            )
        else:
            handle = launch(
                spec,
                native_bridge=config,
                load_save_name=NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
            )
        pid = int(handle.process.pid)
        last_pid = pid
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
            if now >= next_window_state_sample:
                sampled_window_state = _process_windows_minimized(pid)
                if sampled_window_state is not None:
                    last_known_window_minimized = sampled_window_state
                next_window_state_sample = now + 0.5
            stop_requested = False
            if stdin is not None:
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
