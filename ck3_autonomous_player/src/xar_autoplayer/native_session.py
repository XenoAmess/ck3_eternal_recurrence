"""Lifecycle supervisor for a pure native-headless CK3 MCP session.

This module deliberately depends only on the process runtime.  It does not
import the visual driver, OCR, screenshots, or desktop input modules.
"""

from __future__ import annotations

import json
import math
from queue import Empty, SimpleQueue
import sys
import threading
import time
from typing import TextIO

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


def native_session(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    poll_interval_seconds: float = 0.05,
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
            )


def _native_session_locked(
    spec: EnvironmentSpec,
    config: NativeBridgeLaunchConfig,
    timeout_seconds: float,
    *,
    input_stream: TextIO | None,
    output_stream: TextIO | None,
    poll_interval_seconds: float,
) -> dict[str, object]:
    started_wall = utc_now()
    started = time.monotonic()
    deadline = started + timeout_seconds
    handle = None
    exit_reason = "launch_error"
    process_exit_code: int | None = None
    primary_error: BaseException | None = None
    shutdown: dict[str, object] | None = None

    try:
        # Passing the validated config explicitly prevents environment changes
        # from selecting hybrid fallback between command parsing and launch.
        handle = launch(
            spec,
            native_bridge=config,
            continue_last_save=True,
        )
        pid = int(handle.process.pid)
        _emit(
            output_stream,
            {
                "type": "native_session_ready",
                "pid": pid,
                "mode": PURE_NATIVE_MODE,
                "pipe": config.pipe_name,
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
        "pid": int(handle.process.pid) if handle is not None else None,
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": elapsed,
        "exit_reason": exit_reason,
        "process_exit_code": process_exit_code,
        "shutdown": shutdown,
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


def run_from_cli(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
) -> dict[str, object]:
    """CLI adapter kept here so the generic CLI never imports visual code."""
    return native_session(
        spec,
        timeout_seconds=timeout_seconds,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
    )
