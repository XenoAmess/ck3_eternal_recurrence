"""Headless gameplay driver for the injected CK3 named-pipe bridge.

The native DLL is the pipe client.  This module owns the Windows named-pipe
server and translates its small length-prefixed JSON protocol into the same
semantic driver interface used by the visual and data-Mod backends.
"""

from __future__ import annotations

from collections.abc import Callable
import ctypes
from ctypes import wintypes
import json
import math
import os
import struct
import threading
import time
from typing import Protocol
import uuid

from .driver import (
    BridgeUnavailableError,
    GameplayBridgeDriver,
    HybridGameplayDriver,
    UnsupportedStepError,
)


PROTOCOL_VERSION = 1
MAXIMUM_FRAME_BYTES = 1024 * 1024
DEFAULT_PIPE_NAME = r"\\.\pipe\xar_ck3_bridge_mcp"
_ACTION_CAPABILITY_PREFIX = "game.command."


class NativeBridgeEndpoint(Protocol):
    """Transport boundary kept small enough for deterministic offline tests."""

    pipe_name: str

    def start(
        self,
        on_frame: Callable[[dict[str, object]], None],
        on_disconnect: Callable[[], None],
    ) -> None: ...

    def send(self, frame: dict[str, object]) -> None: ...

    def close(self) -> None: ...


class NativeProtocolState:
    """Thread-safe cache of the frames published by one injected DLL."""

    def __init__(self, pipe_name: str) -> None:
        self.pipe_name = pipe_name
        self._condition = threading.Condition()
        self._public_revision = 0
        self._connection_generation = 0
        self._connected = False
        self._hello: dict[str, object] | None = None
        self._last_heartbeat: dict[str, object] | None = None
        self._last_pong: dict[str, object] | None = None
        self._last_error: dict[str, object] | None = None
        self._semantic_snapshot: dict[str, object] | None = None
        self._command_results: dict[str, dict[str, object]] = {}

    def ingest(self, frame: dict[str, object]) -> str:
        if not isinstance(frame, dict):
            raise ValueError("native bridge frame must be a JSON object")
        if frame.get("protocol_version") != PROTOCOL_VERSION:
            raise ValueError("native bridge protocol_version must be 1")
        frame_type = frame.get("type")
        if not isinstance(frame_type, str) or not frame_type:
            raise ValueError("native bridge frame lacks type")

        with self._condition:
            if frame_type == "hello":
                pid = frame.get("pid")
                capabilities = frame.get("capabilities")
                if (
                    isinstance(pid, bool)
                    or not isinstance(pid, int)
                    or pid <= 0
                    or not isinstance(capabilities, list)
                ):
                    raise ValueError("native bridge hello is malformed")
                self._connected = True
                self._connection_generation += 1
                self._hello = dict(frame)
                self._last_heartbeat = None
                self._last_pong = None
                self._semantic_snapshot = None
                self._command_results.clear()
                self._public_revision += 1
            elif frame_type == "heartbeat":
                sequence = frame.get("sequence")
                if (
                    isinstance(sequence, bool)
                    or not isinstance(sequence, int)
                    or sequence < 0
                ):
                    raise ValueError("native bridge heartbeat is malformed")
                self._last_heartbeat = dict(frame)
            elif frame_type == "pong":
                if not isinstance(frame.get("request_id"), str):
                    raise ValueError("native bridge pong is malformed")
                self._last_pong = dict(frame)
            elif frame_type == "state_snapshot":
                snapshot = _semantic_snapshot_from_frame(frame)
                # Heartbeat-adjacent publishers may repeat the most recent
                # semantic frame.  Repeated bytes are liveness, not a new game
                # revision, so wait_for_change must keep waiting.
                if snapshot != self._semantic_snapshot:
                    self._semantic_snapshot = snapshot
                    self._public_revision += 1
            elif frame_type == "command_result":
                request_id = frame.get("request_id")
                if not isinstance(request_id, str) or not request_id:
                    raise ValueError("native bridge command_result is malformed")
                self._command_results[request_id] = dict(frame)
            elif frame_type == "error":
                self._last_error = dict(frame)
            else:
                raise ValueError(f"unsupported native bridge frame type: {frame_type}")
            self._condition.notify_all()
        return frame_type

    def mark_disconnected(self) -> None:
        with self._condition:
            if self._connected:
                self._connected = False
                self._semantic_snapshot = None
                self._public_revision += 1
                self._condition.notify_all()

    def capabilities(self) -> dict[str, object]:
        with self._condition:
            raw_capabilities = _string_list(
                self._hello.get("capabilities") if self._hello else None
            )
            snapshot_supported = (
                self._connected
                and self._semantic_snapshot is not None
                and "game.state.snapshot" in raw_capabilities
            )
            return {
                "format_version": 1,
                "backend_id": "native-headless",
                "mode": "native-headless",
                "source": "injected-dll-named-pipe",
                "latency": "realtime",
                "headless": True,
                "minimized_operation": True,
                "visual_fallback": False,
                "fallback_enabled": False,
                "snapshot": snapshot_supported,
                "wait_for_change": snapshot_supported,
                "action_steps": (
                    _action_steps(raw_capabilities) if self._connected else []
                ),
                "bridge_capabilities": raw_capabilities,
                "diagnostics": self._diagnostics_locked(),
            }

    def diagnostics(self) -> dict[str, object]:
        with self._condition:
            return self._diagnostics_locked()

    def semantic_snapshot(self) -> dict[str, object]:
        with self._condition:
            if not self._connected:
                raise BridgeUnavailableError(
                    f"native DLL is not connected to {self.pipe_name}"
                )
            raw_capabilities = _string_list(self._hello.get("capabilities"))
            if self._semantic_snapshot is None:
                if "game.state.snapshot" in raw_capabilities:
                    raise BridgeUnavailableError(
                        "native game state is not available yet; CK3 may still be "
                        "loading or may not have entered a map"
                    )
                raise UnsupportedStepError(
                    "native DLL did not advertise game.state.snapshot"
                )
            if "game.state.snapshot" not in raw_capabilities:
                raise UnsupportedStepError(
                    "native DLL did not advertise game.state.snapshot"
                )
            return {
                **self._semantic_snapshot,
                "revision": self._public_revision,
                "native_revision": self._semantic_snapshot["revision"],
                "backend_id": "native-headless",
                "source": "injected-dll-named-pipe",
                "diagnostics": self._diagnostics_locked(),
            }

    def public_revision(self) -> int:
        with self._condition:
            return self._public_revision

    def wait_for_public_change(
        self, after_revision: int, timeout_seconds: float
    ) -> None:
        with self._condition:
            self._condition.wait_for(
                lambda: self._public_revision > after_revision,
                timeout=timeout_seconds,
            )

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object] | None:
        with self._condition:
            self._condition.wait_for(
                lambda: request_id in self._command_results or not self._connected,
                timeout=timeout_seconds,
            )
            return self._command_results.pop(request_id, None)

    def _diagnostics_locked(self) -> dict[str, object]:
        hello = dict(self._hello) if self._hello else None
        heartbeat = dict(self._last_heartbeat) if self._last_heartbeat else None
        pong = dict(self._last_pong) if self._last_pong else None
        return {
            "protocol_version": PROTOCOL_VERSION,
            "pipe_name": self.pipe_name,
            "connected": self._connected,
            "connection_generation": self._connection_generation,
            "bridge_pid": hello.get("pid") if hello else None,
            "bridge_version": hello.get("bridge_version") if hello else None,
            "hello": hello,
            "last_heartbeat": heartbeat,
            "last_pong": pong,
            "last_error": dict(self._last_error) if self._last_error else None,
            "semantic_state_available": self._semantic_snapshot is not None,
        }


class NativeNamedPipeServer:
    """One-client byte-mode Windows named-pipe server for protocol v1."""

    def __init__(
        self,
        pipe_name: str = DEFAULT_PIPE_NAME,
        *,
        poll_interval_seconds: float = 0.01,
    ) -> None:
        self.pipe_name = _validate_pipe_name(pipe_name)
        self.poll_interval_seconds = _positive_seconds(
            poll_interval_seconds, "poll_interval_seconds"
        )
        self._on_frame: Callable[[dict[str, object]], None] | None = None
        self._on_disconnect: Callable[[], None] | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._fatal_error: str | None = None
        self._handle_lock = threading.Lock()
        self._handle: int | None = None
        self._write_lock = threading.Lock()

    def start(
        self,
        on_frame: Callable[[dict[str, object]], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        if os.name != "nt":
            raise RuntimeError("native-headless named pipes require Windows")
        if self._thread is not None:
            return
        self._on_frame = on_frame
        self._on_disconnect = on_disconnect
        self._thread = threading.Thread(
            target=self._run,
            name="xar-ck3-native-pipe",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=2.0):
            self.close()
            raise RuntimeError("native named-pipe server did not become ready")
        if self._fatal_error is not None:
            self.close()
            raise RuntimeError(self._fatal_error)

    def transport_error(self) -> str | None:
        return self._fatal_error

    def send(self, frame: dict[str, object]) -> None:
        payload = json.dumps(
            frame, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        if not payload or len(payload) > MAXIMUM_FRAME_BYTES:
            raise ValueError("native bridge frame is empty or too large")
        packet = struct.pack("<I", len(payload)) + payload
        with self._write_lock:
            handle = self._current_handle()
            if handle is None:
                raise BridgeUnavailableError("native DLL is not connected")
            if not _write_all(handle, packet):
                raise BridgeUnavailableError("native bridge pipe write failed")

    def close(self) -> None:
        self._stop.set()
        handle = self._current_handle()
        if handle is not None:
            _cancel_io(handle)
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None

    def _current_handle(self) -> int | None:
        with self._handle_lock:
            return self._handle

    def _set_handle(self, handle: int | None) -> None:
        with self._handle_lock:
            self._handle = handle

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                handle = _create_named_pipe(self.pipe_name)
            except OSError as error:
                self._fatal_error = (
                    f"native named-pipe server failed for {self.pipe_name}: {error}"
                )
                self._ready.set()
                if self._on_disconnect is not None:
                    self._on_disconnect()
                return
            self._set_handle(handle)
            self._ready.set()
            connected = False
            try:
                connected = self._wait_for_connection(handle)
                if connected:
                    self._read_connection(handle)
            finally:
                if connected and self._on_disconnect is not None:
                    self._on_disconnect()
                _disconnect_pipe(handle)
                _close_handle(handle)
                self._set_handle(None)

    def _wait_for_connection(self, handle: int) -> bool:
        while not self._stop.is_set():
            result, error = _connect_named_pipe(handle)
            if result or error == _ERROR_PIPE_CONNECTED:
                return True
            if error not in (_ERROR_PIPE_LISTENING, _ERROR_NO_DATA):
                return False
            time.sleep(self.poll_interval_seconds)
        return False

    def _read_connection(self, handle: int) -> None:
        pending_payload_size: int | None = None
        while not self._stop.is_set():
            available = _peek_available(handle)
            if available is None:
                return
            if pending_payload_size is None:
                if available < 4:
                    time.sleep(self.poll_interval_seconds)
                    continue
                header = _read_exact(handle, 4)
                if header is None:
                    return
                pending_payload_size = struct.unpack("<I", header)[0]
                if not 0 < pending_payload_size <= MAXIMUM_FRAME_BYTES:
                    return
            available = _peek_available(handle)
            if available is None:
                return
            if available < pending_payload_size:
                time.sleep(self.poll_interval_seconds)
                continue
            payload = _read_exact(handle, pending_payload_size)
            pending_payload_size = None
            if payload is None:
                return
            try:
                frame = json.loads(payload.decode("utf-8"))
                if not isinstance(frame, dict):
                    continue
                if self._on_frame is not None:
                    self._on_frame(frame)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                continue


class NativeHeadlessGameplayDriver:
    """Pure native mode: never invokes OCR, keyboard, mouse, or window focus."""

    def __init__(
        self,
        pipe_name: str = DEFAULT_PIPE_NAME,
        *,
        endpoint: NativeBridgeEndpoint | None = None,
        command_timeout_seconds: float = 10.0,
    ) -> None:
        self.pipe_name = _validate_pipe_name(pipe_name)
        self.command_timeout_seconds = _positive_seconds(
            command_timeout_seconds, "command_timeout_seconds"
        )
        self.state = NativeProtocolState(self.pipe_name)
        self.endpoint = endpoint or NativeNamedPipeServer(self.pipe_name)
        self._request_sequence = 0
        self.endpoint.start(self._ingest, self.state.mark_disconnected)

    def _ingest(self, frame: dict[str, object]) -> None:
        frame_type = self.state.ingest(frame)
        if frame_type == "hello":
            self._request_sequence += 1
            request_id = f"python-{self._request_sequence}-{uuid.uuid4().hex[:12]}"
            try:
                self.endpoint.send(
                    {
                        "type": "ping",
                        "protocol_version": PROTOCOL_VERSION,
                        "request_id": request_id,
                    }
                )
            except BridgeUnavailableError:
                self.state.mark_disconnected()

    def capabilities(self) -> dict[str, object]:
        result = self.state.capabilities()
        diagnostics = dict(result["diagnostics"])
        transport_error = self._transport_error()
        diagnostics["transport_fatal_error"] = transport_error
        return {
            **result,
            "transport_ready": transport_error is None,
            "diagnostics": diagnostics,
        }

    def diagnostics(self) -> dict[str, object]:
        result = self.state.diagnostics()
        result["transport_fatal_error"] = self._transport_error()
        return result

    def take_snapshot(self) -> dict[str, object]:
        transport_error = self._transport_error()
        if transport_error is not None:
            raise BridgeUnavailableError(transport_error)
        return self.state.semantic_snapshot()

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if not isinstance(step, str) or not step:
            raise ValueError("step must be a non-empty string")
        capabilities = self.capabilities()
        if step not in capabilities["action_steps"]:
            raise UnsupportedStepError(
                f"native DLL does not implement gameplay step {step}"
            )
        snapshot = self.take_snapshot()
        revision = int(snapshot["revision"])
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != revision:
                raise BridgeUnavailableError(
                    "native gameplay revision mismatch: "
                    f"expected {expected_revision}, current {revision}"
                )
        self._request_sequence += 1
        request_id = f"step-{self._request_sequence}-{uuid.uuid4().hex[:12]}"
        self.endpoint.send(
            {
                "type": "execute_step",
                "protocol_version": PROTOCOL_VERSION,
                "request_id": request_id,
                "step": step,
                "expected_revision": snapshot["native_revision"],
            }
        )
        frame = self.state.wait_for_command_result(
            request_id, self.command_timeout_seconds
        )
        if frame is None:
            raise BridgeUnavailableError(
                f"native command_result timed out for gameplay step {step}"
            )
        if frame.get("ok") is not True:
            raise BridgeUnavailableError(
                f"native gameplay step failed: {frame.get('error') or 'unknown error'}"
            )
        result = frame.get("result")
        if isinstance(result, dict):
            return {**result, "backend_id": "native-headless"}
        return {
            "result": result,
            "backend_id": "native-headless",
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        _validate_revision(after_revision, "after_revision")
        timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
        if not self.capabilities()["snapshot"]:
            return self.take_snapshot()
        self.state.wait_for_public_change(after_revision, timeout)
        return self.take_snapshot()

    def close(self) -> None:
        self.endpoint.close()

    def _transport_error(self) -> str | None:
        getter = getattr(self.endpoint, "transport_error", None)
        if not callable(getter):
            return None
        value = getter()
        return value if isinstance(value, str) and value else None


class MinimizedRejectingVisualDriver:
    """Allow configured visual fallback only while CK3 is not minimized."""

    def __init__(
        self,
        driver: GameplayBridgeDriver,
        *,
        window_minimized: Callable[[], bool | None] | None = None,
    ) -> None:
        self.driver = driver
        self._window_minimized = window_minimized or self._detect_minimized

    def capabilities(self) -> dict[str, object]:
        try:
            base = self.driver.capabilities()
        except (BridgeUnavailableError, UnsupportedStepError) as error:
            base = {
                "format_version": 1,
                "backend_id": "vision-session",
                "source": "ocr-keyboard-mouse-session-queue",
                "latency": "interactive",
                "snapshot": False,
                "wait_for_change": False,
                "connected": False,
                "action_steps": [],
                "unavailable_reason": str(error),
            }
        return {
            **base,
            "backend_id": "vision-session-guarded",
            "visual_fallback": True,
            "visual_fallback_when_minimized": False,
            "window_minimized": self._window_minimized(),
        }

    def take_snapshot(self) -> dict[str, object]:
        # The session snapshot is a cached report read.  It does not capture
        # the screen, restore the window, or send input.
        return self.driver.take_snapshot()

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        minimized = self._window_minimized()
        if minimized is True:
            raise BridgeUnavailableError(
                "CK3 is minimized; configured visual fallback was refused "
                "without restoring or focusing the window"
            )
        if minimized is not False:
            raise BridgeUnavailableError(
                "CK3 window visibility is unknown; configured visual fallback "
                "was refused without restoring or focusing the window"
            )
        return self.driver.execute_step(step, expected_revision=expected_revision)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return self.driver.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )

    def _detect_minimized(self) -> bool | None:
        try:
            snapshot = self.driver.take_snapshot()
            session = snapshot.get("session")
            process = session.get("process") if isinstance(session, dict) else None
            hwnd = process.get("hwnd") if isinstance(process, dict) else None
            pid = process.get("pid") if isinstance(process, dict) else None
            import win32gui

            if isinstance(hwnd, int) and hwnd > 0 and win32gui.IsWindow(hwnd):
                return bool(win32gui.IsIconic(hwnd))
            if isinstance(pid, int) and pid > 0:
                matches: list[int] = []

                def collect(candidate: int, _extra: object) -> None:
                    import win32process

                    _thread_id, candidate_pid = win32process.GetWindowThreadProcessId(
                        candidate
                    )
                    if candidate_pid == pid and win32gui.IsWindowVisible(candidate):
                        matches.append(candidate)

                win32gui.EnumWindows(collect, None)
                if matches:
                    return all(bool(win32gui.IsIconic(item)) for item in matches)
        except (BridgeUnavailableError, OSError, ImportError):
            return None
        return None


class ConfiguredHybridFallbackDriver:
    """Explicit native -> data Mod -> guarded visual fallback mode."""

    def __init__(
        self,
        native: NativeHeadlessGameplayDriver,
        data_mod: GameplayBridgeDriver,
        visual: MinimizedRejectingVisualDriver,
    ) -> None:
        self.native = native
        self.data_mod = data_mod
        self.visual = visual
        self._delegate = HybridGameplayDriver(
            native,
            HybridGameplayDriver(data_mod, visual),
        )

    def capabilities(self) -> dict[str, object]:
        base = self._delegate.capabilities()
        return {
            **base,
            "backend_id": "hybrid-fallback",
            "mode": "hybrid-fallback",
            "headless": False,
            "minimized_operation": "native-and-data-mod-only",
            "visual_fallback": True,
            "visual_fallback_when_minimized": False,
            "fallback_enabled": True,
            "fallback_order": [
                "native-headless",
                "data-mod",
                "vision-session-guarded",
            ],
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            **self._delegate.take_snapshot(),
            "backend_id": "hybrid-fallback",
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        return self._delegate.execute_step(step, expected_revision=expected_revision)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return {
            **self._delegate.wait_for_change(
                after_revision, timeout_seconds=timeout_seconds
            ),
            "backend_id": "hybrid-fallback",
        }

    def diagnostics(self) -> dict[str, object]:
        return self.native.diagnostics()

    def close(self) -> None:
        self.native.close()


def selected_pipe_name(pipe_name: str | None = None) -> str:
    return _validate_pipe_name(
        pipe_name or os.environ.get("XAR_CK3_BRIDGE_PIPE") or DEFAULT_PIPE_NAME
    )


def _semantic_snapshot_from_frame(frame: dict[str, object]) -> dict[str, object]:
    state = frame.get("state")
    if not isinstance(state, dict):
        raise ValueError("native state_snapshot lacks state")
    snapshot_id = frame.get("snapshot_id")
    revision = frame.get("revision")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("native state_snapshot lacks snapshot_id")
    _validate_revision(revision, "state_snapshot revision")
    history = state.get("history")
    return {
        **state,
        "format_version": 1,
        "snapshot_id": snapshot_id,
        "revision": revision,
        "history": history if isinstance(history, list) else [],
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(item for item in value if isinstance(item, str) and item))


def _action_steps(capabilities: list[str]) -> list[str]:
    return sorted(
        capability.removeprefix(_ACTION_CAPABILITY_PREFIX)
        for capability in capabilities
        if capability.startswith(_ACTION_CAPABILITY_PREFIX)
        and capability.removeprefix(_ACTION_CAPABILITY_PREFIX)
    )


def _validate_revision(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _positive_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) <= 0
    ):
        raise ValueError(f"{name} must be finite and positive")
    return float(value)


def _validate_pipe_name(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("\\\\.\\pipe\\")
        or len(value) <= len("\\\\.\\pipe\\")
    ):
        raise ValueError("pipe name must start with \\\\.\\pipe\\")
    return value


_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_PIPE_ACCESS_DUPLEX = 0x00000003
_PIPE_TYPE_BYTE = 0x00000000
_PIPE_READMODE_BYTE = 0x00000000
_PIPE_NOWAIT = 0x00000001
_ERROR_NO_DATA = 232
_ERROR_PIPE_CONNECTED = 535
_ERROR_PIPE_LISTENING = 536


def _kernel32():
    if os.name != "nt":
        raise RuntimeError("native named pipes require Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateNamedPipeW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
    ]
    kernel.CreateNamedPipeW.restype = wintypes.HANDLE
    kernel.ConnectNamedPipe.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
    kernel.ConnectNamedPipe.restype = wintypes.BOOL
    kernel.PeekNamedPipe.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    kernel.PeekNamedPipe.restype = wintypes.BOOL
    kernel.ReadFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    kernel.ReadFile.restype = wintypes.BOOL
    kernel.WriteFile.argtypes = kernel.ReadFile.argtypes
    kernel.WriteFile.restype = wintypes.BOOL
    kernel.DisconnectNamedPipe.argtypes = [wintypes.HANDLE]
    kernel.DisconnectNamedPipe.restype = wintypes.BOOL
    kernel.CancelIoEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
    kernel.CancelIoEx.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def _create_named_pipe(pipe_name: str) -> int:
    handle = _kernel32().CreateNamedPipeW(
        pipe_name,
        _PIPE_ACCESS_DUPLEX,
        _PIPE_TYPE_BYTE | _PIPE_READMODE_BYTE | _PIPE_NOWAIT,
        1,
        MAXIMUM_FRAME_BYTES + 4,
        MAXIMUM_FRAME_BYTES + 4,
        0,
        None,
    )
    raw = int(handle) if handle else 0
    if raw == _INVALID_HANDLE_VALUE or raw == 0:
        raise OSError(ctypes.get_last_error(), "CreateNamedPipeW failed")
    return raw


def _connect_named_pipe(handle: int) -> tuple[bool, int]:
    ctypes.set_last_error(0)
    result = bool(_kernel32().ConnectNamedPipe(handle, None))
    return result, ctypes.get_last_error()


def _peek_available(handle: int) -> int | None:
    available = wintypes.DWORD()
    if not _kernel32().PeekNamedPipe(
        handle, None, 0, None, ctypes.byref(available), None
    ):
        return None
    return int(available.value)


def _read_exact(handle: int, size: int) -> bytes | None:
    buffer = ctypes.create_string_buffer(size)
    read = wintypes.DWORD()
    if not _kernel32().ReadFile(handle, buffer, size, ctypes.byref(read), None):
        return None
    if read.value != size:
        return None
    return buffer.raw


def _write_all(handle: int, data: bytes) -> bool:
    offset = 0
    kernel = _kernel32()
    while offset < len(data):
        chunk = data[offset:]
        buffer = ctypes.create_string_buffer(chunk)
        written = wintypes.DWORD()
        if not kernel.WriteFile(
            handle, buffer, len(chunk), ctypes.byref(written), None
        ):
            return False
        if written.value == 0:
            return False
        offset += int(written.value)
    return True


def _cancel_io(handle: int) -> None:
    try:
        _kernel32().CancelIoEx(handle, None)
    except OSError:
        pass


def _disconnect_pipe(handle: int) -> None:
    try:
        _kernel32().DisconnectNamedPipe(handle)
    except OSError:
        pass


def _close_handle(handle: int) -> None:
    try:
        _kernel32().CloseHandle(handle)
    except OSError:
        pass
