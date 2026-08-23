"""Headless gameplay driver for the injected CK3 named-pipe bridge.

The native DLL is the pipe client.  This module owns the Windows named-pipe
server and translates its small length-prefixed JSON protocol into the same
semantic driver interface used by the visual and data-Mod backends.
"""

from __future__ import annotations

from collections.abc import Callable
import copy
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import threading
import time
from typing import Protocol
import uuid

from ..environment import write_json_atomic
from .driver import (
    BridgeUnavailableError,
    GameplayBridgeDriver,
    HybridGameplayDriver,
    UnsupportedStepError,
)
from .session_queue import SESSION_QUEUE_PROTOCOL_VERSION
from .event_contract import (
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
)
from .war_contract import (
    DISBAND_ARMY_CAPABILITY,
    MOVE_ARMY_CAPABILITY,
    RAISE_TROOPS_STEP,
    controllable_armies,
    disband_army_step,
    enemy_armies_from_wars,
    is_native_war_step,
    move_army_step,
    normalize_active_wars,
    parse_disband_army_step,
    parse_move_army_step,
    player_armies_from_state,
)


PROTOCOL_VERSION = 1
MAXIMUM_FRAME_BYTES = 1024 * 1024
DEFAULT_PIPE_NAME = r"\\.\pipe\xar_ck3_bridge_mcp"
_ACTION_CAPABILITY_PREFIX = "game.command."
_NATIVE_LIFE_ADVANCE_PRIMITIVES = frozenset(
    {"set-speed-5", "resume-map", "pause-map"}
)
_CHECKPOINT_FILENAME = "xar_checkpoint.ck3"
_NATIVE_DEATH_TERMINAL_STEP = "death-terminal"
_NATIVE_SESSION_QUEUE_DIRNAME = "native-session"
_RESTORE_CHECKPOINT_STEP = "restore-checkpoint"


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
                    _action_steps(
                        raw_capabilities,
                        self._semantic_snapshot.get("active_event")
                        if self._semantic_snapshot is not None
                        else None,
                        self._semantic_snapshot.get(
                            "pending_character_interaction"
                        )
                        if self._semantic_snapshot is not None
                        else None,
                        self._semantic_snapshot.get("active_wars")
                        if self._semantic_snapshot is not None
                        else None,
                        self._semantic_snapshot.get("player_armies")
                        if self._semantic_snapshot is not None
                        else None,
                    )
                    if self._connected
                    else []
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
        life_advance_timeout_seconds: float = 30.0,
        state_dir: str | os.PathLike[str] | None = None,
        save_dir: str | os.PathLike[str] | None = None,
        checkpoint_timeout_seconds: float = 30.0,
        checkpoint_poll_interval_seconds: float = 0.1,
        restore_timeout_seconds: float = 180.0,
        restore_poll_interval_seconds: float = 0.05,
    ) -> None:
        self.pipe_name = _validate_pipe_name(pipe_name)
        self.command_timeout_seconds = _positive_seconds(
            command_timeout_seconds, "command_timeout_seconds"
        )
        self.life_advance_timeout_seconds = _positive_seconds(
            life_advance_timeout_seconds, "life_advance_timeout_seconds"
        )
        self.state_dir = Path(state_dir) if state_dir is not None else None
        self.save_dir = Path(save_dir) if save_dir is not None else None
        self.checkpoint_timeout_seconds = _positive_seconds(
            checkpoint_timeout_seconds, "checkpoint_timeout_seconds"
        )
        self.checkpoint_poll_interval_seconds = _positive_seconds(
            checkpoint_poll_interval_seconds,
            "checkpoint_poll_interval_seconds",
        )
        self.restore_timeout_seconds = _positive_seconds(
            restore_timeout_seconds, "restore_timeout_seconds"
        )
        self.restore_poll_interval_seconds = _positive_seconds(
            restore_poll_interval_seconds,
            "restore_poll_interval_seconds",
        )
        self._last_checkpoint: dict[str, object] | None = None
        self._history_lock = threading.Lock()
        self._command_history: list[dict[str, object]] = []
        self._episode_identity_lock = threading.Lock()
        self._episode_character_id: int | None = None
        self._episode_run_id: str | None = None
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
        action_steps = set(_string_list(result.get("action_steps")))
        bridge_capabilities = set(
            _string_list(result.get("bridge_capabilities"))
        )
        composite_action_steps: list[str] = []
        if (
            result.get("snapshot") is True
            and result.get("wait_for_change") is True
            and _NATIVE_LIFE_ADVANCE_PRIMITIVES <= action_steps
            and "game.command.life-advance" not in bridge_capabilities
        ):
            action_steps.add("life-advance")
            composite_action_steps.append("life-advance")
        checkpoint_path = self._checkpoint_path()
        if (
            result.get("snapshot") is True
            and self.state_dir is not None
            and checkpoint_path is not None
            and _checkpoint_signature(checkpoint_path) is not None
        ):
            action_steps.add(_RESTORE_CHECKPOINT_STEP)
            composite_action_steps.append(_RESTORE_CHECKPOINT_STEP)
        current_snapshot = (
            self._with_one_life_episode(self.state.semantic_snapshot())
            if result.get("snapshot") is True
            else None
        )
        terminal_reason = (
            current_snapshot.get("one_life_terminal_reason")
            if isinstance(current_snapshot, dict)
            else None
        )
        if isinstance(terminal_reason, str):
            action_steps.add(_NATIVE_DEATH_TERMINAL_STEP)
            composite_action_steps.append(_NATIVE_DEATH_TERMINAL_STEP)
        with self._episode_identity_lock:
            episode_character_id = self._episode_character_id
            episode_run_id = self._episode_run_id
        return {
            **result,
            "action_steps": sorted(action_steps),
            "composite_action_steps": composite_action_steps,
            "checkpoint_materialization": {
                "configured": self.save_dir is not None,
                "save_dir": str(self.save_dir) if self.save_dir is not None else None,
                "filename": _CHECKPOINT_FILENAME,
            },
            "native_session_control": {
                "configured": self.state_dir is not None,
                "queue_dir": (
                    str(self._native_session_queue_dir())
                    if self.state_dir is not None
                    else None
                ),
                "restore_checkpoint": (
                    _RESTORE_CHECKPOINT_STEP in action_steps
                ),
            },
            "episode_character_id": episode_character_id,
            "episode_run_id": episode_run_id,
            "one_life_terminal": isinstance(terminal_reason, str),
            "one_life_terminal_reason": terminal_reason,
            "continue_as_heir_after_death": False,
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
        return {
            **self._with_one_life_episode(self.state.semantic_snapshot()),
            "native_command_history": self._history_snapshot(),
        }

    def _with_one_life_episode(
        self, snapshot: dict[str, object]
    ) -> dict[str, object]:
        """Project the immutable character identity of this one-life episode."""
        played_character = snapshot.get("played_character")
        current_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        with self._episode_identity_lock:
            if (
                self._episode_character_id is None
                and snapshot.get("map_ready") is True
                and isinstance(current_character_id, int)
            ):
                self._episode_character_id = current_character_id
                self._episode_run_id = (
                    f"native-{current_character_id}-{uuid.uuid4().hex[:12]}"
                )
            episode_character_id = self._episode_character_id
            episode_run_id = self._episode_run_id

        terminal_reason: str | None = None
        if (
            episode_character_id is not None
            and isinstance(current_character_id, int)
            and current_character_id != episode_character_id
        ):
            terminal_reason = "played_character_changed"
        elif (
            episode_character_id is not None
            and isinstance(played_character, dict)
            and played_character.get("alive") is False
        ):
            terminal_reason = "played_character_dead"

        return {
            **snapshot,
            "episode_character_id": episode_character_id,
            "episode_run_id": episode_run_id,
            "one_life_terminal": terminal_reason is not None,
            "one_life_terminal_reason": terminal_reason,
            "continue_as_heir_after_death": False,
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        try:
            result = self._execute_step_unrecorded(
                step, expected_revision=expected_revision
            )
        except Exception as error:
            self._record_command(
                step,
                ok=False,
                error=f"{type(error).__name__}: {error}",
            )
            raise
        self._record_command(step, ok=True, result=result)
        return result

    def _execute_step_unrecorded(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        capabilities = self.capabilities()
        if step == "save-checkpoint" and step in capabilities["action_steps"]:
            return self._execute_save_checkpoint(
                expected_revision=expected_revision
            )
        if step in {
            "accept-pending-character-interaction",
            "reject-pending-character-interaction",
        } and step in capabilities["action_steps"]:
            return self._execute_pending_character_interaction_reply(
                step, expected_revision=expected_revision
            )
        if is_native_war_step(step) and step in capabilities["action_steps"]:
            return self._execute_native_war_step(
                step, expected_revision=expected_revision
            )
        if (
            step == _RESTORE_CHECKPOINT_STEP
            and step in capabilities.get("composite_action_steps", [])
        ):
            return self._execute_restore_checkpoint(
                expected_revision=expected_revision
            )
        if (
            step == _NATIVE_DEATH_TERMINAL_STEP
            and step in capabilities.get("composite_action_steps", [])
        ):
            return self._execute_native_death_terminal(
                expected_revision=expected_revision
            )
        if step in capabilities.get("composite_action_steps", []):
            if step == "life-advance":
                return self._execute_life_advance(
                    expected_revision=expected_revision
                )
            raise UnsupportedStepError(
                f"native Python bridge does not implement composite step {step}"
            )
        return self._execute_primitive_step(
            step,
            expected_revision=expected_revision,
        )

    def _record_command(
        self,
        step: str,
        *,
        ok: bool,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> None:
        with self._history_lock:
            row: dict[str, object] = {
                "index": len(self._command_history) + 1,
                "command": step,
                "ok": ok,
            }
            if result is not None:
                row["result"] = copy.deepcopy(result)
            if error is not None:
                row["error"] = error
            self._command_history.append(row)

    def _history_snapshot(self) -> list[dict[str, object]]:
        with self._history_lock:
            return copy.deepcopy(self._command_history)

    def _execute_primitive_step(
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

    def _execute_save_checkpoint(
        self, *, expected_revision: int | None
    ) -> dict[str, object]:
        checkpoint_path = (
            self.save_dir / _CHECKPOINT_FILENAME
            if self.save_dir is not None
            else None
        )
        before = (
            _checkpoint_signature(checkpoint_path)
            if checkpoint_path is not None
            else None
        )
        submission_result = self._execute_primitive_step(
            "save-checkpoint", expected_revision=expected_revision
        )
        submission = submission_result.get("submission")
        submitted_date_raw = (
            submission.get("date_raw")
            if isinstance(submission, dict)
            and not isinstance(submission.get("date_raw"), bool)
            and isinstance(submission.get("date_raw"), int)
            else _date_raw(self.take_snapshot(), "checkpoint submission")
        )
        if checkpoint_path is None:
            return {
                **submission_result,
                "checkpoint": {
                    "status": "materialization_unavailable",
                    "path": None,
                    "name": _CHECKPOINT_FILENAME,
                    "size": None,
                    "sha256": None,
                    "date_raw": submitted_date_raw,
                    "strategy": "native-autosave-command-v1",
                },
                "materialization": {
                    "available": False,
                    "reason": "save_dir_not_configured",
                },
            }

        signature = self._wait_for_checkpoint_materialization(
            checkpoint_path, before
        )
        size, mtime_ns = signature
        checkpoint = {
            "status": "saved",
            "path": str(checkpoint_path.resolve()),
            "name": checkpoint_path.name,
            "size": size,
            "sha256": _sha256_file(checkpoint_path),
            "date_raw": submitted_date_raw,
            "overwrite_confirmed": before is not None,
            "strategy": "native-autosave-command-v1",
        }
        self._last_checkpoint = dict(checkpoint)
        return {
            **submission_result,
            "checkpoint": checkpoint,
            "materialization": {
                "available": True,
                "save_dir": str(self.save_dir.resolve()),
                "mtime_ns": mtime_ns,
            },
        }

    def _execute_pending_character_interaction_reply(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        starting = self.take_snapshot()
        pending = starting.get("pending_character_interaction")
        if not isinstance(pending, dict):
            raise BridgeUnavailableError(
                "CK3 has no pending character interaction"
            )
        instance_id = pending.get("instance_id")
        result = self._execute_primitive_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(starting["revision"])
            ),
        )
        changed = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: (
                not isinstance(
                    snapshot.get("pending_character_interaction"), dict
                )
                or snapshot["pending_character_interaction"].get("instance_id")
                != instance_id
            ),
            timeout_seconds=self.command_timeout_seconds,
        )
        remaining = changed.get("pending_character_interaction")
        if isinstance(remaining, dict) and remaining.get("instance_id") == instance_id:
            raise BridgeUnavailableError(
                "native character interaction reply did not advance the pending request"
            )
        return {
            **result,
            "interaction_result": {
                "status": "accepted" if step.startswith("accept-") else "rejected",
                "instance_id": instance_id,
                "sender_character_id": pending.get("sender_character_id"),
            },
            "remaining_pending_character_interaction": remaining,
            "snapshot_id": changed["snapshot_id"],
            "revision": changed["revision"],
        }

    def _execute_native_war_step(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        starting = self.take_snapshot()
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        if step == RAISE_TROOPS_STEP:
            starting_army_ids = _controllable_army_ids(starting)
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            changed = self._wait_for_snapshot(
                self.take_snapshot(),
                lambda snapshot: bool(
                    _controllable_army_ids(snapshot) - starting_army_ids
                ),
                timeout_seconds=self.command_timeout_seconds,
            )
            raised_ids = sorted(
                _controllable_army_ids(changed) - starting_army_ids
            )
            if not raised_ids:
                raise BridgeUnavailableError(
                    "native raise-troops-default did not expose a new "
                    "controllable army"
                )
            return {
                **result,
                "war_action": {
                    "status": "raised",
                    "raised_army_ids": raised_ids,
                },
                "player_armies": changed.get("player_armies", []),
                "snapshot_id": changed["snapshot_id"],
                "revision": changed["revision"],
            }

        move = parse_move_army_step(step)
        if move is not None:
            army_id, province_id = move
            starting_army = _army_by_id(starting, army_id)
            if (
                not isinstance(starting_army, dict)
                or starting_army.get("controllable") is not True
            ):
                raise BridgeUnavailableError(
                    f"native move-army-{army_id} requires a controllable "
                    "player army"
                )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            if (
                isinstance(starting_army, dict)
                and starting_army.get("move_target_observable") is False
                and (
                    result.get("accepted") is True
                    or result.get("status") in {"accepted", "submitted"}
                )
            ):
                current = self.take_snapshot()
                return {
                    **result,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": army_id,
                        "target_province_id": province_id,
                        "move_target_observable": False,
                    },
                    "player_armies": current.get("player_armies", []),
                    "snapshot_id": current["snapshot_id"],
                    "revision": current["revision"],
                }
            changed = self._wait_for_snapshot(
                self.take_snapshot(),
                lambda snapshot: _army_move_postcondition(
                    snapshot, army_id, province_id
                ) is not None,
                timeout_seconds=self.command_timeout_seconds,
            )
            status = _army_move_postcondition(changed, army_id, province_id)
            if status is None:
                raise BridgeUnavailableError(
                    f"native move-army-{army_id} did not target province "
                    f"{province_id}"
                )
            return {
                **result,
                "war_action": {
                    "status": status,
                    "army_id": army_id,
                    "target_province_id": province_id,
                },
                "player_armies": changed.get("player_armies", []),
                "snapshot_id": changed["snapshot_id"],
                "revision": changed["revision"],
            }

        army_id = parse_disband_army_step(step)
        if army_id is None:
            raise UnsupportedStepError(
                f"native Python bridge does not implement war step {step}"
            )
        result = self._execute_primitive_step(
            step, expected_revision=selected_revision
        )
        changed = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: _army_by_id(snapshot, army_id) is None,
            timeout_seconds=self.command_timeout_seconds,
        )
        if _army_by_id(changed, army_id) is not None:
            raise BridgeUnavailableError(
                f"native disband-army-{army_id} did not remove the army"
            )
        return {
            **result,
            "war_action": {
                "status": "disbanded",
                "army_id": army_id,
            },
            "player_armies": changed.get("player_armies", []),
            "snapshot_id": changed["snapshot_id"],
            "revision": changed["revision"],
        }

    def _execute_restore_checkpoint(
        self, *, expected_revision: int | None
    ) -> dict[str, object]:
        if self.state_dir is None:
            raise UnsupportedStepError(
                "native restore-checkpoint requires a configured state_dir"
            )
        checkpoint_path = self._checkpoint_path()
        signature = (
            _checkpoint_signature(checkpoint_path)
            if checkpoint_path is not None
            else None
        )
        if checkpoint_path is None or signature is None or signature[0] <= 0:
            raise BridgeUnavailableError(
                "native restore-checkpoint requires xar_checkpoint.ck3"
            )

        starting = self.take_snapshot()
        starting_revision = int(starting["revision"])
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != starting_revision:
                raise BridgeUnavailableError(
                    "native gameplay revision mismatch: "
                    f"expected {expected_revision}, current {starting_revision}"
                )
        diagnostics = self.state.diagnostics()
        starting_generation = diagnostics.get("connection_generation")
        if (
            isinstance(starting_generation, bool)
            or not isinstance(starting_generation, int)
            or starting_generation < 1
        ):
            raise BridgeUnavailableError(
                "native restore-checkpoint requires a connected DLL generation"
            )

        request_id = f"restore-{uuid.uuid4().hex}"
        queue_dir = self._native_session_queue_dir()
        inbox_dir = queue_dir / "inbox"
        outbox_dir = queue_dir / "outbox"
        response_path = outbox_dir / f"{request_id}.json"
        write_json_atomic(
            inbox_dir / f"{request_id}.json",
            {
                "protocol_version": SESSION_QUEUE_PROTOCOL_VERSION,
                "request_id": request_id,
                "command": _RESTORE_CHECKPOINT_STEP,
                "pipe": self.pipe_name,
                "checkpoint_name": _CHECKPOINT_FILENAME,
            },
        )

        deadline = time.monotonic() + self.restore_timeout_seconds
        response = self._wait_for_restore_response(
            response_path, request_id, deadline
        )
        restored = self._wait_for_restored_map(starting_generation, deadline)
        restored_date_raw = _date_raw(restored, "restored snapshot")
        restored_signature = _checkpoint_signature(checkpoint_path)
        if restored_signature is None or restored_signature[0] <= 0:
            raise BridgeUnavailableError(
                "native-session restored CK3 but its checkpoint file is missing"
            )
        size, mtime_ns = restored_signature
        previous_checkpoint = self._last_checkpoint or {}
        lifecycle_result = response.get("result")
        lifecycle = (
            dict(lifecycle_result)
            if isinstance(lifecycle_result, dict)
            else {}
        )
        restored_checkpoint = {
            "status": "restored",
            "path": str(checkpoint_path.resolve()),
            "name": checkpoint_path.name,
            "size": size,
            "sha256": _sha256_file(checkpoint_path),
            "date_raw": restored_date_raw,
            "saved_date_raw": previous_checkpoint.get("date_raw"),
            "mtime_ns": mtime_ns,
            "strategy": "native-session-continuelastsave-v1",
        }
        return {
            "step": _RESTORE_CHECKPOINT_STEP,
            "accepted": True,
            "status": "restored",
            "backend_id": "native-headless",
            "source": "native-session-lifecycle-queue",
            "starting_date": {"date_raw": _date_raw(starting, "starting snapshot")},
            "restored_date": {"date_raw": restored_date_raw},
            "starting_date_raw": _date_raw(starting, "starting snapshot"),
            "restored_date_raw": restored_date_raw,
            "checkpoint": restored_checkpoint,
            "lifecycle": {
                **lifecycle,
                "request_id": request_id,
                "previous_connection_generation": starting_generation,
                "connection_generation": restored["diagnostics"][
                    "connection_generation"
                ],
            },
            "map_ready": True,
            "paused": restored.get("paused"),
            "snapshot_id": restored["snapshot_id"],
            "revision": restored["revision"],
        }

    def _execute_native_death_terminal(
        self, *, expected_revision: int | None
    ) -> dict[str, object]:
        snapshot = self.take_snapshot()
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != snapshot["revision"]:
                raise BridgeUnavailableError(
                    "native gameplay revision mismatch: "
                    f"expected {expected_revision}, current {snapshot['revision']}"
                )
        played_character = snapshot.get("played_character")
        terminal_reason = snapshot.get("one_life_terminal_reason")
        if not isinstance(terminal_reason, str):
            raise BridgeUnavailableError(
                "native one-life episode has not reached a death terminal"
            )
        terminal_kind = (
            "native_played_character_changed"
            if terminal_reason == "played_character_changed"
            else "native_played_character_dead"
        )
        result: dict[str, object] = {
            "step": _NATIVE_DEATH_TERMINAL_STEP,
            "backend_id": "native-headless",
            "terminal": True,
            "terminal_kind": terminal_kind,
            "terminal_reason": terminal_reason,
            "episode_character_id": snapshot.get("episode_character_id"),
            "technical_settlement_handoff": False,
            "continue_as_heir_after_death": False,
            "score": None,
            "played_character": copy.deepcopy(played_character),
            "date_raw": snapshot.get("date_raw"),
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
        }
        if self.state_dir is not None:
            from ..strategy import record_one_life_episode

            episode_run_id = snapshot.get("episode_run_id")
            if not isinstance(episode_run_id, str) or not episode_run_id:
                raise BridgeUnavailableError(
                    "native one-life episode lacks a stable run identity"
                )
            commands = self._history_snapshot()
            commands.append(
                {
                    "index": len(commands) + 1,
                    "command": _NATIVE_DEATH_TERMINAL_STEP,
                    "ok": True,
                    "result": copy.deepcopy(result),
                }
            )
            result["cross_run_strategy"] = record_one_life_episode(
                self.state_dir,
                run_id=episode_run_id,
                commands=commands,
                terminal=result,
            )
        return result

    def _wait_for_restore_response(
        self,
        response_path: Path,
        request_id: str,
        deadline: float,
    ) -> dict[str, object]:
        while True:
            if response_path.is_file():
                try:
                    payload = json.loads(
                        response_path.read_text(encoding="utf-8-sig")
                    )
                except (OSError, UnicodeError, json.JSONDecodeError) as error:
                    raise BridgeUnavailableError(
                        f"native-session restore response is malformed: {error}"
                    ) from error
                if (
                    not isinstance(payload, dict)
                    or payload.get("protocol_version")
                    != SESSION_QUEUE_PROTOCOL_VERSION
                    or payload.get("request_id") != request_id
                ):
                    raise BridgeUnavailableError(
                        "native-session restore response does not match the request"
                    )
                if payload.get("ok") is not True:
                    raise BridgeUnavailableError(
                        "native-session restore failed: "
                        f"{payload.get('error') or 'unknown error'}"
                    )
                return payload
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeUnavailableError(
                    "native-session did not acknowledge restore-checkpoint"
                )
            time.sleep(min(self.restore_poll_interval_seconds, remaining))

    def _wait_for_restored_map(
        self, starting_generation: int, deadline: float
    ) -> dict[str, object]:
        observed_revision = self.state.public_revision()
        while True:
            diagnostics = self.state.diagnostics()
            generation = diagnostics.get("connection_generation")
            if isinstance(generation, int) and generation > starting_generation:
                try:
                    snapshot = self.state.semantic_snapshot()
                except BridgeUnavailableError:
                    snapshot = None
                if isinstance(snapshot, dict) and snapshot.get("map_ready") is True:
                    return snapshot
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeUnavailableError(
                    "native-session relaunched CK3 but no newer DLL generation "
                    "published a map_ready snapshot"
                )
            self.state.wait_for_public_change(observed_revision, remaining)
            observed_revision = self.state.public_revision()

    def _native_session_queue_dir(self) -> Path:
        if self.state_dir is None:
            raise UnsupportedStepError(
                "native-session lifecycle queue requires state_dir"
            )
        return self.state_dir / _NATIVE_SESSION_QUEUE_DIRNAME / "bridge"

    def _checkpoint_path(self) -> Path | None:
        return (
            self.save_dir / _CHECKPOINT_FILENAME
            if self.save_dir is not None
            else None
        )

    def _wait_for_checkpoint_materialization(
        self,
        checkpoint_path: Path,
        before: tuple[int, int] | None,
    ) -> tuple[int, int]:
        deadline = time.monotonic() + self.checkpoint_timeout_seconds
        prior_changed: tuple[int, int] | None = None
        while True:
            current = _checkpoint_signature(checkpoint_path)
            if current is not None and current[0] > 0 and current != before:
                if current == prior_changed:
                    return current
                prior_changed = current
            else:
                prior_changed = None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeUnavailableError(
                    "native save-checkpoint was submitted but "
                    f"{checkpoint_path} did not materialize"
                )
            time.sleep(min(self.checkpoint_poll_interval_seconds, remaining))

    def _execute_life_advance(
        self, *, expected_revision: int | None
    ) -> dict[str, object]:
        starting = self.take_snapshot()
        if starting.get("map_ready") is not True:
            starting = self._wait_for_snapshot(
                starting,
                lambda snapshot: snapshot.get("map_ready") is True,
                timeout_seconds=self.life_advance_timeout_seconds,
            )
        if starting.get("map_ready") is not True:
            raise BridgeUnavailableError(
                "native life-advance timed out waiting for map_ready"
            )
        starting_revision = int(starting["revision"])
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != starting_revision:
                # life-advance is a bounded timeline transaction and always
                # starts from a fresh native snapshot.  A date tick can race
                # the caller's prior observation, so refresh once rather than
                # rejecting the whole composite before it begins.
                starting = self.take_snapshot()
                starting_revision = int(starting["revision"])
                if starting.get("active_event") is not None:
                    raise BridgeUnavailableError(
                        "native life-advance revision changed onto an active event"
                    )
        starting_date_raw = _date_raw(starting, "starting snapshot")
        actions: list[dict[str, object]] = []

        speed_result = self._execute_composite_primitive(
            "set-speed-5", starting
        )
        actions.append({"step": "set-speed-5", "result": speed_result})
        current = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: snapshot.get("speed") == 5,
            timeout_seconds=self.command_timeout_seconds,
        )
        if current.get("speed") != 5:
            raise BridgeUnavailableError(
                "native life-advance did not observe speed 5"
            )

        resume_result = self._execute_composite_primitive(
            "resume-map", current
        )
        actions.append({"step": "resume-map", "result": resume_result})
        current = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: snapshot.get("paused") is False,
            timeout_seconds=self.command_timeout_seconds,
        )
        if current.get("paused") is not False:
            raise BridgeUnavailableError(
                "native life-advance did not observe the running map"
            )

        progress_deadline = time.monotonic() + self.life_advance_timeout_seconds
        while not _life_advance_progressed(current, starting_date_raw):
            remaining = progress_deadline - time.monotonic()
            if remaining <= 0:
                break
            current = self.wait_for_change(
                int(current["revision"]),
                timeout_seconds=remaining,
            )

        current = self._pause_life_advance(current, actions)
        if not _life_advance_progressed(current, starting_date_raw):
            raise BridgeUnavailableError(
                "native life-advance observed neither a date change nor an active event"
            )

        ordinary_events: list[dict[str, object]] = []
        event_resolution = "none"
        active_event = current.get("active_event")
        if isinstance(active_event, dict):
            option_number = choose_event_option_number(active_event)
            selection_step = (
                event_option_step(option_number)
                if option_number is not None
                else None
            )
            if (
                selection_step is not None
                and selection_step in self.capabilities()["action_steps"]
            ):
                event_instance_id = active_event.get("instance_id")
                selection_result = self._execute_composite_primitive(
                    selection_step, current
                )
                actions.append(
                    {"step": selection_step, "result": selection_result}
                )
                ordinary_events.append(
                    _native_ordinary_event(active_event, option_number)
                )
                current = self._wait_for_snapshot(
                    self.take_snapshot(),
                    lambda snapshot: _event_instance_id(snapshot)
                    != event_instance_id,
                    timeout_seconds=self.command_timeout_seconds,
                )
                if _event_instance_id(current) == event_instance_id:
                    raise BridgeUnavailableError(
                        "native event selection did not advance the active event"
                    )
                current = self._pause_life_advance(current, actions)
                event_resolution = "selected"
            else:
                event_resolution = "unsupported"

        ending_date_raw = _date_raw(current, "ending snapshot")
        return {
            "step": "life-advance",
            "backend_id": "native-headless",
            "source": "native-composite",
            "starting_date": {"date_raw": starting_date_raw},
            "ending_date": {"date_raw": ending_date_raw},
            "starting_date_raw": starting_date_raw,
            "ending_date_raw": ending_date_raw,
            "elapsed_days": max(0, (ending_date_raw - starting_date_raw) // 24),
            "ordinary_events": ordinary_events,
            "event_resolution": event_resolution,
            "actions": actions,
            "paused": current.get("paused") is True,
            "active_event": current.get("active_event"),
            "final_screen": "map_hud" if current.get("paused") is True else None,
            "snapshot_id": current["snapshot_id"],
            "revision": current["revision"],
        }

    def _pause_life_advance(
        self,
        snapshot: dict[str, object],
        actions: list[dict[str, object]],
    ) -> dict[str, object]:
        if snapshot.get("paused") is True:
            return snapshot
        result = self._execute_composite_primitive("pause-map", snapshot)
        actions.append({"step": "pause-map", "result": result})
        paused = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda candidate: candidate.get("paused") is True,
            timeout_seconds=self.command_timeout_seconds,
        )
        if paused.get("paused") is not True:
            raise BridgeUnavailableError(
                "native life-advance did not observe the paused map"
            )
        return paused

    def _execute_composite_primitive(
        self,
        step: str,
        observed_snapshot: dict[str, object],
    ) -> dict[str, object]:
        """Submit from a fresh revision, retrying one harmless state race."""
        try:
            return self._execute_primitive_step(
                step,
                expected_revision=int(observed_snapshot["revision"]),
            )
        except BridgeUnavailableError as error:
            if "native gameplay revision mismatch" not in str(error):
                raise
            refreshed = self.take_snapshot()
            if not _retryable_life_advance_change(observed_snapshot, refreshed):
                raise
            return self._execute_primitive_step(
                step,
                expected_revision=int(refreshed["revision"]),
            )

    def _wait_for_snapshot(
        self,
        snapshot: dict[str, object],
        predicate: Callable[[dict[str, object]], bool],
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        deadline = time.monotonic() + timeout_seconds
        current = snapshot
        while not predicate(current):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return current
            current = self.wait_for_change(
                int(current["revision"]), timeout_seconds=remaining
            )
        return current

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
        native_steps = set(
            _string_list(self.native.capabilities().get("action_steps"))
        )
        action_steps = set(_string_list(base.get("action_steps")))
        if _RESTORE_CHECKPOINT_STEP not in native_steps:
            action_steps.discard(_RESTORE_CHECKPOINT_STEP)
        action_steps = {
            step
            for step in action_steps
            if not is_native_war_step(step) or step in native_steps
        }
        return {
            **base,
            "action_steps": sorted(action_steps),
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
        if (
            step == _RESTORE_CHECKPOINT_STEP
            and step
            not in _string_list(self.native.capabilities().get("action_steps"))
        ):
            raise UnsupportedStepError(
                "restore-checkpoint is pure native and will not use fallback"
            )
        if (
            is_native_war_step(step)
            and step
            not in _string_list(self.native.capabilities().get("action_steps"))
        ):
            raise UnsupportedStepError(
                "native war steps are pure native and will not use fallback"
            )
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
    active_wars = normalize_active_wars(state.get("active_wars"))
    player_armies = player_armies_from_state(
        active_wars, state.get("player_armies")
    )
    return {
        **state,
        "format_version": 1,
        "snapshot_id": snapshot_id,
        "revision": revision,
        "history": history if isinstance(history, list) else [],
        "active_event": normalize_active_event(
            state.get("active_event"), default_source="native"
        ),
        "played_character": _played_character(state.get("played_character")),
        "pending_character_interaction": (
            _pending_character_interaction(
                state.get("pending_character_interaction")
            )
        ),
        "active_wars": active_wars,
        "player_armies": player_armies,
    }


def _date_raw(snapshot: dict[str, object], name: str) -> int:
    value = snapshot.get("date_raw")
    if isinstance(value, bool) or not isinstance(value, int):
        raise BridgeUnavailableError(f"native {name} lacks date_raw")
    return value


def _life_advance_progressed(
    snapshot: dict[str, object], starting_date_raw: int
) -> bool:
    active_event = snapshot.get("active_event")
    if isinstance(active_event, dict):
        return True
    value = snapshot.get("date_raw")
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and value > starting_date_raw
    )


def _retryable_life_advance_change(
    previous: dict[str, object], refreshed: dict[str, object]
) -> bool:
    """Allow one retry when only the controlled timeline naturally moved."""
    try:
        previous_date = _date_raw(previous, "previous composite snapshot")
        refreshed_date = _date_raw(refreshed, "refreshed composite snapshot")
    except BridgeUnavailableError:
        return False
    return (
        refreshed_date >= previous_date
        and refreshed.get("active_event") == previous.get("active_event")
        and refreshed.get("paused") == previous.get("paused")
        and refreshed.get("speed") == previous.get("speed")
    )


def _event_instance_id(snapshot: dict[str, object]) -> object:
    active_event = snapshot.get("active_event")
    return active_event.get("instance_id") if isinstance(active_event, dict) else None


def _native_ordinary_event(
    active_event: dict[str, object], option_number: int
) -> dict[str, object]:
    options = active_event.get("options")
    visible_options = options if isinstance(options, list) else []
    selected = next(
        (
            option
            for option in visible_options
            if isinstance(option, dict)
            and option.get("option_number") == option_number
        ),
        {},
    )
    return {
        "event_index": 1,
        "event_instance_id": active_event.get("instance_id"),
        "title": active_event.get("title"),
        "visible_options": visible_options,
        "selected_option_number": option_number,
        "selected_option_index": option_number - 1,
        "selected_visible_text": selected.get("label"),
        "strategy": "backend-neutral-event-v1",
        "source": active_event.get("source"),
    }


def _checkpoint_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    if not path.is_file():
        return None
    return stat.st_size, stat.st_mtime_ns


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(item for item in value if isinstance(item, str) and item))


def _action_steps(
    capabilities: list[str],
    active_event: object = None,
    pending_character_interaction: object = None,
    active_wars: object = None,
    player_armies: object = None,
) -> list[str]:
    steps: set[str] = set()
    expand_event_options = False
    pending_interaction_steps: set[str] = set()
    expand_move_armies = False
    expand_disband_armies = False
    advertise_raise_troops = False
    for capability in capabilities:
        if not capability.startswith(_ACTION_CAPABILITY_PREFIX):
            continue
        step = capability.removeprefix(_ACTION_CAPABILITY_PREFIX)
        if step == "select-event-option-N":
            expand_event_options = True
        elif step in {
            "accept-pending-character-interaction",
            "reject-pending-character-interaction",
        }:
            pending_interaction_steps.add(step)
        elif capability == MOVE_ARMY_CAPABILITY:
            expand_move_armies = True
        elif capability == DISBAND_ARMY_CAPABILITY:
            expand_disband_armies = True
        elif step == RAISE_TROOPS_STEP:
            advertise_raise_troops = True
        elif step:
            steps.add(step)
    if expand_event_options and isinstance(active_event, dict):
        option_count = active_event.get("option_count")
        if (
            not isinstance(option_count, bool)
            and isinstance(option_count, int)
            and option_count > 0
        ):
            steps.update(
                f"select-event-option-{option_number}"
                for option_number in range(1, option_count + 1)
            )
    if (
        isinstance(pending_character_interaction, dict)
        and pending_character_interaction.get("auto_accept_notification") is False
    ):
        steps.update(pending_interaction_steps)
    wars = (
        [war for war in active_wars if isinstance(war, dict)]
        if isinstance(active_wars, list)
        else []
    )
    armies = (
        [army for army in player_armies if isinstance(army, dict)]
        if isinstance(player_armies, list)
        else []
    )
    controllable = controllable_armies(armies)
    if advertise_raise_troops and wars and not controllable:
        steps.add(RAISE_TROOPS_STEP)
    if expand_disband_armies:
        steps.update(
            disband_army_step(int(army["army_id"]))
            for army in controllable
            if isinstance(army.get("army_id"), int)
        )
    if expand_move_armies and wars:
        target_provinces = {
            int(army["current_province_id"])
            for army in enemy_armies_from_wars(wars)
            if isinstance(army.get("current_province_id"), int)
        }
        for army in controllable:
            army_id = army.get("army_id")
            if not isinstance(army_id, int):
                continue
            for province_id in target_provinces:
                if province_id in {
                    army.get("current_province_id"),
                    army.get("move_target_province_id"),
                }:
                    continue
                steps.add(move_army_step(army_id, province_id))
    return sorted(steps)


def _controllable_army_ids(snapshot: dict[str, object]) -> set[int]:
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return set()
    return {
        int(army["army_id"])
        for army in controllable_armies(
            [row for row in armies if isinstance(row, dict)]
        )
        if isinstance(army.get("army_id"), int)
    }


def _army_by_id(
    snapshot: dict[str, object], army_id: int
) -> dict[str, object] | None:
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return None
    return next(
        (
            army
            for army in armies
            if isinstance(army, dict) and army.get("army_id") == army_id
        ),
        None,
    )


def _army_move_postcondition(
    snapshot: dict[str, object], army_id: int, province_id: int
) -> str | None:
    army = _army_by_id(snapshot, army_id)
    if army is None:
        return "army_no_longer_present"
    if army.get("current_province_id") == province_id:
        return "arrived"
    if army.get("move_target_province_id") == province_id:
        return "moving"
    return None


def _pending_character_interaction(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("native pending_character_interaction must be an object")
    instance_id = value.get("instance_id")
    sender_character_id = value.get("sender_character_id")
    auto_accept_notification = value.get("auto_accept_notification")
    if (
        isinstance(instance_id, bool)
        or not isinstance(instance_id, int)
        or instance_id < 0
        or isinstance(sender_character_id, bool)
        or not isinstance(sender_character_id, int)
        or not isinstance(auto_accept_notification, bool)
    ):
        raise ValueError("native pending_character_interaction is malformed")
    return {
        "instance_id": instance_id,
        "sender_character_id": sender_character_id,
        "auto_accept_notification": auto_accept_notification,
        "source": "native",
    }


def _played_character(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("native played_character must be an object")
    character_id = value.get("character_id")
    alive = value.get("alive")
    if (
        isinstance(character_id, bool)
        or not isinstance(character_id, int)
        or character_id < 0
        or not isinstance(alive, bool)
    ):
        raise ValueError("native played_character is malformed")
    result: dict[str, object] = {
        "character_id": character_id,
        "alive": alive,
        "source": "native",
    }
    if "primary_heir_id" in value or "has_heir" in value:
        primary_heir_id = value.get("primary_heir_id")
        has_heir = value.get("has_heir")
        if not isinstance(has_heir, bool):
            raise ValueError("native played_character has_heir is malformed")
        if has_heir:
            if (
                isinstance(primary_heir_id, bool)
                or not isinstance(primary_heir_id, int)
                or primary_heir_id < 0
            ):
                raise ValueError(
                    "native played_character primary_heir_id is malformed"
                )
        elif primary_heir_id is not None:
            raise ValueError(
                "native played_character primary_heir_id conflicts with has_heir"
            )
        result.update(
            {
                "primary_heir_id": primary_heir_id,
                "has_heir": has_heir,
            }
        )
    return result


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
