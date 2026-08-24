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
import shutil
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
from .declaration_contract import (
    DECLARE_WAR_CAPABILITY,
    QUERY_DECLARABLE_WARS_STEP,
    declare_war_step,
    is_native_declaration_step,
    normalize_declarable_wars,
    parse_declare_war_step,
)
from .marriage_contract import (
    ARRANGE_MARRIAGE_CAPABILITY,
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
    arrange_marriage_step,
    is_native_marriage_step,
    normalize_arrange_marriage_choices,
    observed_marriage_status,
    parse_arrange_marriage_step,
)
from .settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
    normalize_one_life_settlement,
    settlement_ready_for_episode,
    tutorial_record_observation,
)
from .war_contract import (
    ARMY_ROUTES_CAPABILITY,
    DISBAND_ARMY_CAPABILITY,
    ENFORCE_DEMANDS_CAPABILITY,
    MOVE_ARMY_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
    RAISE_TROOPS_STEP,
    WAR_OBJECTIVES_CAPABILITY,
    WAR_OBJECTIVE_FORT_LEVEL_CAPABILITY,
    WAR_OBJECTIVE_GARRISON_CAPABILITY,
    WAR_OBJECTIVE_OCCUPATION_CAPABILITY,
    WAR_OBJECTIVE_SIEGE_PROGRESS_CAPABILITY,
    WAR_PRIMARY_OPPONENT_CAPABILITY,
    controllable_armies,
    disband_army_step,
    enemy_primary_default_raise_province_ids,
    enforce_demands_step,
    enemy_armies_from_wars,
    is_native_war_step,
    move_army_step,
    normalize_active_wars,
    parse_disband_army_step,
    parse_enforce_demands_step,
    parse_move_army_step,
    parse_preview_move_army_step,
    preview_move_army_step,
    player_armies_from_state,
    war_objective_province_ids,
)


PROTOCOL_VERSION = 1
MAXIMUM_FRAME_BYTES = 1024 * 1024
DEFAULT_PIPE_NAME = r"\\.\pipe\xar_ck3_bridge_mcp"
_ACTION_CAPABILITY_PREFIX = "game.command."
_NATIVE_LIFE_ADVANCE_PRIMITIVES = frozenset(
    {"set-speed-5", "resume-map", "pause-map"}
)
_CHECKPOINT_FILENAME = "xar_checkpoint.ck3"
_EPISODE_SEED_FILENAME = "xar_episode_seed.ck3"
_EPISODE_SEED_METADATA_FILENAME = "episode-seed.json"
_EPISODE_TRANSITION_FILENAME = "episode-transition.json"
_NATIVE_DEATH_TERMINAL_STEP = "death-terminal"
_NATIVE_SESSION_QUEUE_DIRNAME = "native-session"
_NATIVE_DRIVER_STATE_FILENAME = "driver-state.json"
_NATIVE_DRIVER_STATE_VERSION = 2
_RESTORE_CHECKPOINT_STEP = "restore-checkpoint"
_START_NEXT_EPISODE_STEP = "start-next-episode"
_COLD_RESTORE_SOURCE = "native-session-cold-start"
_RESTORE_MAP_STABLE_SECONDS = 0.5
_NATIVE_WAR_ADVANCE_MAX_DAYS = 30
_NATIVE_SIEGE_ADVANCE_MAX_DAYS = 7
_ARMY_MOVE_DEFERRED_ERRORS = frozenset(
    {
        # Kept for protocol-v1 bridges built before the native rejection
        # stages were split.
        "CK3 army cannot move to the destination",
        "CK3 army has no move mode for the destination",
        "CK3 army state rejects movement",
    }
)


class _NativeCommandRejectedError(BridgeUnavailableError):
    def __init__(self, native_error: str) -> None:
        self.native_error = native_error
        super().__init__(f"native gameplay step failed: {native_error}")


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
        settlement_timeout_seconds: float = 30.0,
        settlement_poll_interval_seconds: float = 0.05,
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
        self.settlement_timeout_seconds = _positive_seconds(
            settlement_timeout_seconds, "settlement_timeout_seconds"
        )
        self.settlement_poll_interval_seconds = _positive_seconds(
            settlement_poll_interval_seconds,
            "settlement_poll_interval_seconds",
        )
        self._driver_state_lock = threading.RLock()
        self._driver_state_write_lock = threading.Lock()
        self._history_lock = self._driver_state_lock
        self._last_checkpoint: dict[str, object] | None = None
        self._command_history: list[dict[str, object]] = []
        self._episode_identity_lock = self._driver_state_lock
        self._episode_character_id: int | None = None
        self._episode_run_id: str | None = None
        self._session_bridge_pid: int | None = None
        self._driver_state_restored = False
        self._driver_state_error: str | None = None
        self._driver_state_restore_kind: str | None = None
        self._episode_binding_state = "unbound"
        self._pending_cold_candidate: dict[str, object] | None = None
        self._cold_candidate_rejection: str | None = None
        self._episode_seed: dict[str, object] | None = self._read_episode_seed()
        self._episode_transition: dict[str, object] | None = (
            self._read_pending_episode_transition()
        )
        self._episode_transition_error: str | None = (
            str(self._episode_transition.get("error"))
            if isinstance(self._episode_transition, dict)
            and self._episode_transition.get("phase") == "blocked"
            and self._episode_transition.get("error")
            else None
        )
        self._declarable_wars: list[dict[str, object]] = []
        self._declaration_query_sequence: int | None = None
        self._arrange_marriage_choices: list[dict[str, object]] = []
        self._arrange_marriage_query_sequence: int | None = None
        self.state = NativeProtocolState(self.pipe_name)
        self.endpoint = endpoint or NativeNamedPipeServer(self.pipe_name)
        self._request_sequence = 0
        self.endpoint.start(self._ingest, self.state.mark_disconnected)

    def _ingest(self, frame: dict[str, object]) -> None:
        frame_type = self.state.ingest(frame)
        if frame_type == "hello":
            bridge_pid = frame.get("pid")
            if isinstance(bridge_pid, int) and not isinstance(bridge_pid, bool):
                self._adopt_bridge_session(bridge_pid)
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
        with self._driver_state_lock:
            declarations = copy.deepcopy(self._declarable_wars)
            marriage_choices = copy.deepcopy(self._arrange_marriage_choices)
        if DECLARE_WAR_CAPABILITY in bridge_capabilities:
            action_steps.update(
                declare_war_step(str(row["declaration_id"]))
                for row in declarations
            )
        if ARRANGE_MARRIAGE_CAPABILITY in bridge_capabilities:
            action_steps.update(
                arrange_marriage_step(str(row["choice_id"]))
                for row in marriage_choices
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
            episode_seed = copy.deepcopy(self._episode_seed)
            completed_terminal = self._completed_terminal_result_locked()
            episode_transition = copy.deepcopy(self._episode_transition)
        if (
            isinstance(terminal_reason, str)
            and completed_terminal is not None
            and self.state_dir is not None
            and self._episode_seed_matches_file(episode_seed)
            and episode_transition is None
        ):
            action_steps.add(_START_NEXT_EPISODE_STEP)
            composite_action_steps.append(_START_NEXT_EPISODE_STEP)
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
                "driver_state_path": (
                    str(self._native_driver_state_path())
                    if self.state_dir is not None
                    else None
                ),
                "driver_state_restored": self._driver_state_restored,
                "driver_state_error": self._driver_state_error,
                "driver_state_restore_kind": self._driver_state_restore_kind,
                "episode_binding_state": self._episode_binding_state,
                "cold_candidate_rejection": self._cold_candidate_rejection,
                "episode_transition": episode_transition,
                "episode_transition_error": self._episode_transition_error,
            },
            "episode_seed": episode_seed,
            "episode_character_id": episode_character_id,
            "episode_run_id": episode_run_id,
            "episode_identity_pending": (
                self._episode_binding_state == "pending_cold_candidate"
            ),
            "one_life_terminal": isinstance(terminal_reason, str),
            "one_life_terminal_reason": terminal_reason,
            "one_life_settlement_supported": (
                ONE_LIFE_SETTLEMENT_CAPABILITY in bridge_capabilities
            ),
            "army_routes_supported": (
                ARMY_ROUTES_CAPABILITY in bridge_capabilities
            ),
            "move_route_preview_supported": (
                PREVIEW_MOVE_ARMY_CAPABILITY in bridge_capabilities
            ),
            **_war_objective_capability_flags(bridge_capabilities),
            "one_life_settlement_status": (
                current_snapshot.get("one_life_settlement_status")
                if isinstance(current_snapshot, dict)
                else None
            ),
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
        snapshot = self._with_one_life_episode(self.state.semantic_snapshot())
        self._observe_arrange_marriage_outcome(snapshot)
        return {
            **snapshot,
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
        self._bind_episode_from_playable_snapshot(
            snapshot, current_character_id=current_character_id
        )
        identity_changed = False
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
                self._episode_binding_state = "active_new"
                self._driver_state_restore_kind = "new_episode"
                identity_changed = True
            episode_character_id = self._episode_character_id
            episode_run_id = self._episode_run_id
            declarable_wars = copy.deepcopy(self._declarable_wars)
            declaration_query_sequence = self._declaration_query_sequence
            arrange_marriage_choices = copy.deepcopy(
                self._arrange_marriage_choices
            )
            arrange_marriage_query_sequence = (
                self._arrange_marriage_query_sequence
            )
        if identity_changed:
            self._persist_driver_state()

        settlement = snapshot.get("one_life_settlement")
        terminal_reason: str | None = None
        if (
            episode_character_id is not None
            and isinstance(current_character_id, int)
            and current_character_id != episode_character_id
        ):
            terminal_reason = "played_character_changed"
        elif (
            episode_character_id is not None
            and played_character is None
            and settlement_ready_for_episode(
                settlement, episode_character_id
            )
        ):
            terminal_reason = "played_character_missing"
        elif (
            episode_character_id is not None
            and isinstance(played_character, dict)
            and played_character.get("alive") is False
        ):
            terminal_reason = "played_character_dead"

        bridge_capabilities = set(
            _string_list(self.state.capabilities().get("bridge_capabilities"))
        )
        if terminal_reason is None:
            settlement_status = "not_terminal"
        elif ONE_LIFE_SETTLEMENT_CAPABILITY not in bridge_capabilities:
            settlement_status = "settlement_unavailable"
        elif settlement_ready_for_episode(settlement, episode_character_id):
            settlement_status = "ready"
        elif isinstance(settlement, dict) and settlement.get("ready") is True:
            settlement_status = "source_mismatch"
        else:
            settlement_status = "pending"

        return {
            **snapshot,
            "episode_character_id": episode_character_id,
            "episode_run_id": episode_run_id,
            "episode_identity_pending": (
                self._episode_binding_state == "pending_cold_candidate"
            ),
            "one_life_terminal": terminal_reason is not None,
            "one_life_terminal_reason": terminal_reason,
            "one_life_settlement_status": settlement_status,
            "continue_as_heir_after_death": False,
            "army_routes_supported": (
                ARMY_ROUTES_CAPABILITY in bridge_capabilities
            ),
            "move_route_preview_supported": (
                PREVIEW_MOVE_ARMY_CAPABILITY in bridge_capabilities
            ),
            **_war_objective_capability_flags(bridge_capabilities),
            "declarable_wars": declarable_wars,
            "declaration_query_sequence": declaration_query_sequence,
            "arrange_marriage_choices": arrange_marriage_choices,
            "arrange_marriage_query_sequence": arrange_marriage_query_sequence,
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
        if (
            is_native_declaration_step(step)
            and step in capabilities["action_steps"]
        ):
            return self._execute_declarable_war_step(
                step, expected_revision=expected_revision
            )
        if is_native_marriage_step(step) and step in capabilities["action_steps"]:
            return self._execute_arrange_marriage_step(
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
        if (
            step == _START_NEXT_EPISODE_STEP
            and step in capabilities.get("composite_action_steps", [])
        ):
            return self._execute_start_next_episode(
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
        self._persist_driver_state()

    def _observe_arrange_marriage_outcome(
        self, snapshot: dict[str, object]
    ) -> None:
        """Persist a proposal outcome only after the exact relationship exists."""
        played_character = snapshot.get("played_character")
        observed_date_raw = snapshot.get("date_raw")
        changed = False
        with self._history_lock:
            for row in reversed(self._command_history):
                choice_id = parse_arrange_marriage_step(row.get("command"))
                if choice_id is None or row.get("ok") is not True:
                    continue
                result = row.get("result")
                action = (
                    result.get("marriage_action")
                    if isinstance(result, dict)
                    else None
                )
                if (
                    not isinstance(result, dict)
                    or not isinstance(action, dict)
                    or action.get("status") != "proposal_submitted"
                ):
                    continue
                played_character_id = action.get("played_character_id")
                candidate_character_id = action.get("candidate_character_id")
                if (
                    isinstance(played_character_id, bool)
                    or not isinstance(played_character_id, int)
                    or isinstance(candidate_character_id, bool)
                    or not isinstance(candidate_character_id, int)
                ):
                    continue
                status = observed_marriage_status(
                    played_character,
                    played_character_id=played_character_id,
                    candidate_character_id=candidate_character_id,
                )
                if status is None:
                    continue
                existing = result.get("marriage_result")
                if (
                    isinstance(existing, dict)
                    and existing.get("status") == status
                    and existing.get("candidate_character_id")
                    == candidate_character_id
                ):
                    return
                result["marriage_result"] = {
                    "status": status,
                    "played_character_id": played_character_id,
                    "candidate_character_id": candidate_character_id,
                    "observed_date_raw": (
                        observed_date_raw
                        if isinstance(observed_date_raw, int)
                        and not isinstance(observed_date_raw, bool)
                        else None
                    ),
                    "source": "native_relationship_snapshot",
                }
                changed = True
                break
        if changed:
            self._persist_driver_state()

    def _bind_new_episode_from_seed_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        current_character_id: int,
    ) -> bool:
        """Bind a seed relaunch as a new run, even when CharacterID is unchanged."""
        with self._driver_state_lock:
            transition = copy.deepcopy(self._episode_transition)
        if transition is None:
            return False
        seed = transition.get("seed")
        snapshot_date_raw = snapshot.get("date_raw")
        rejection: str | None = None
        if not isinstance(seed, dict):
            rejection = "episode_seed_metadata_missing"
        elif current_character_id != seed.get("character_id"):
            rejection = "episode_seed_character_mismatch"
        elif snapshot_date_raw != seed.get("date_raw"):
            rejection = "episode_seed_date_mismatch"
        elif not self._episode_seed_matches_file(seed, verify_sha256=True):
            rejection = "episode_seed_bytes_mismatch"

        with self._driver_state_lock:
            if (
                self._episode_transition is None
                or self._episode_transition.get("request_id")
                != transition.get("request_id")
            ):
                return True
            if rejection is not None:
                self._episode_transition_error = rejection
                self._episode_binding_state = "episode_seed_blocked"
                self._episode_transition["phase"] = "blocked"
                self._episode_transition["error"] = rejection
                self._persist_episode_transition_locked()
                return True
            previous_run_id = self._episode_run_id
            self._command_history = []
            self._last_checkpoint = None
            self._episode_character_id = current_character_id
            self._episode_run_id = (
                f"native-{current_character_id}-{uuid.uuid4().hex[:12]}"
            )
            self._driver_state_restored = False
            self._driver_state_restore_kind = "new_episode_seed"
            self._episode_binding_state = "active_new"
            self._cold_candidate_rejection = None
            self._pending_cold_candidate = None
            self._declarable_wars = []
            self._declaration_query_sequence = None
            self._arrange_marriage_choices = []
            self._arrange_marriage_query_sequence = None
            completed = {
                **self._episode_transition,
                "phase": "active_new",
                "source_run_id": previous_run_id,
                "episode_run_id": self._episode_run_id,
                "episode_character_id": current_character_id,
                "bridge_pid": self._session_bridge_pid,
            }
            self._episode_transition = None
            self._episode_transition_error = None
            self._write_episode_transition(completed)
        self._persist_driver_state()
        return True

    def _completed_terminal_result_locked(self) -> dict[str, object] | None:
        """Return the current run's durable, scored death terminal."""
        for row in reversed(self._command_history):
            if row.get("command") != _NATIVE_DEATH_TERMINAL_STEP:
                continue
            if row.get("ok") is not True:
                return None
            result = row.get("result")
            score = result.get("score") if isinstance(result, dict) else None
            settlement = (
                result.get("one_life_settlement")
                if isinstance(result, dict)
                else None
            )
            strategy = (
                result.get("cross_run_strategy")
                if isinstance(result, dict)
                else None
            )
            recorded = (
                strategy.get("recorded_episode")
                if isinstance(strategy, dict)
                else None
            )
            if (
                isinstance(result, dict)
                and result.get("terminal") is True
                and result.get("settlement_status") == "complete"
                and isinstance(score, (int, float))
                and not isinstance(score, bool)
                and isinstance(settlement, dict)
                and settlement.get("final_score") is not None
                and isinstance(recorded, dict)
                and recorded.get("run_id") == self._episode_run_id
                and recorded.get("score") == score
            ):
                return copy.deepcopy(result)
            return None
        return None

    def _episode_seed_path(self) -> Path | None:
        return (
            self.save_dir / _EPISODE_SEED_FILENAME
            if self.save_dir is not None
            else None
        )

    def _episode_seed_metadata_path(self) -> Path | None:
        return (
            self.state_dir
            / _NATIVE_SESSION_QUEUE_DIRNAME
            / _EPISODE_SEED_METADATA_FILENAME
            if self.state_dir is not None
            else None
        )

    def _episode_transition_path(self) -> Path | None:
        return (
            self.state_dir
            / _NATIVE_SESSION_QUEUE_DIRNAME
            / _EPISODE_TRANSITION_FILENAME
            if self.state_dir is not None
            else None
        )

    def _read_episode_seed(self) -> dict[str, object] | None:
        metadata_path = self._episode_seed_metadata_path()
        if metadata_path is None or not metadata_path.is_file():
            return None
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        return dict(payload) if isinstance(payload, dict) else None

    def _read_pending_episode_transition(self) -> dict[str, object] | None:
        path = self._episode_transition_path()
        if path is None or not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        if (
            isinstance(payload, dict)
            and payload.get("command") == _START_NEXT_EPISODE_STEP
            and payload.get("phase")
            in {"relaunching_episode_seed", "binding", "blocked"}
            and isinstance(payload.get("seed"), dict)
        ):
            return dict(payload)
        return None

    def _episode_seed_matches_file(
        self,
        seed: object,
        *,
        verify_sha256: bool = False,
    ) -> bool:
        path = self._episode_seed_path()
        if not isinstance(seed, dict) or path is None:
            return False
        size = seed.get("size")
        digest = seed.get("sha256")
        if (
            seed.get("name") != _EPISODE_SEED_FILENAME
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
            or not isinstance(digest, str)
            or len(digest) != 64
            or isinstance(seed.get("date_raw"), bool)
            or not isinstance(seed.get("date_raw"), int)
            or isinstance(seed.get("character_id"), bool)
            or not isinstance(seed.get("character_id"), int)
        ):
            return False
        signature = _checkpoint_signature(path)
        if signature is None or signature[0] != size:
            return False
        return not verify_sha256 or _sha256_file(path) == digest

    def _persist_episode_transition_locked(self) -> None:
        if self._episode_transition is not None:
            self._write_episode_transition(self._episode_transition)

    def _write_episode_transition(self, payload: dict[str, object]) -> None:
        path = self._episode_transition_path()
        if path is not None:
            write_json_atomic(path, payload)

    def _history_snapshot(self) -> list[dict[str, object]]:
        with self._history_lock:
            return copy.deepcopy(self._command_history)

    def _adopt_bridge_session(self, bridge_pid: int) -> None:
        """Adopt a bridge now, but delay cross-PID identity until map-ready."""
        first_connection = False
        with self._driver_state_lock:
            first_connection = self._session_bridge_pid is None
        restored: dict[str, object] | None = None
        if first_connection:
            restored = self._read_driver_state()

        should_persist = False
        with self._driver_state_lock:
            if self._session_bridge_pid is None:
                self._command_history = []
                self._episode_character_id = None
                self._episode_run_id = None
                self._last_checkpoint = None
                self._driver_state_restored = False
                self._driver_state_restore_kind = None
                self._episode_binding_state = "unbound"
                self._pending_cold_candidate = None
                self._cold_candidate_rejection = None
                if (
                    restored is not None
                    and restored.get("bridge_pid") == bridge_pid
                ):
                    self._command_history = copy.deepcopy(
                        restored["command_history"]
                    )
                    self._episode_character_id = restored[
                        "episode_character_id"
                    ]
                    self._episode_run_id = restored["episode_run_id"]
                    self._last_checkpoint = copy.deepcopy(
                        restored["last_checkpoint"]
                    )
                    self._upgrade_checkpoint_anchor()
                    self._driver_state_restored = True
                    self._driver_state_restore_kind = "same_pid_hot"
                    self._episode_binding_state = (
                        "active_resumed"
                        if self._episode_character_id is not None
                        else "unbound"
                    )
                    should_persist = True
                elif restored is not None and self._cold_candidate_ready(restored):
                    self._pending_cold_candidate = copy.deepcopy(restored)
                    self._episode_binding_state = "pending_cold_candidate"
                elif restored is not None:
                    self._cold_candidate_rejection = "no_complete_checkpoint_anchor"
            # A PID change inside the same driver is the expected
            # restore-checkpoint lifecycle.  Keep the episode and history,
            # then persist the replacement PID for a later daemon restart.
            self._session_bridge_pid = bridge_pid
            if not first_connection and self._pending_cold_candidate is None:
                if self._episode_transition is not None:
                    self._episode_transition["phase"] = "binding"
                    self._episode_transition["bridge_pid"] = bridge_pid
                    self._episode_binding_state = "binding_episode_seed"
                    self._persist_episode_transition_locked()
                else:
                    self._driver_state_restore_kind = "managed_hot_restore"
                    should_persist = True
            self._declarable_wars = []
            self._declaration_query_sequence = None
            self._arrange_marriage_choices = []
            self._arrange_marriage_query_sequence = None
        if should_persist:
            self._persist_driver_state()

    def _upgrade_checkpoint_anchor(self) -> None:
        """Attach a v2 history/episode anchor to an older hot-restored state."""
        checkpoint = self._last_checkpoint
        if (
            not isinstance(checkpoint, dict)
            or self._episode_character_id is None
            or self._episode_run_id is None
        ):
            return
        history_index = checkpoint.get("history_index")
        if (
            isinstance(history_index, bool)
            or not isinstance(history_index, int)
            or history_index < 1
            or history_index > len(self._command_history)
        ):
            history_index = self._matching_checkpoint_history_index(checkpoint)
            if history_index is None:
                return
            checkpoint["history_index"] = history_index
        checkpoint["episode_character_id"] = self._episode_character_id
        checkpoint["episode_run_id"] = self._episode_run_id

    def _matching_checkpoint_history_index(
        self, checkpoint: dict[str, object]
    ) -> int | None:
        expected_sha256 = checkpoint.get("sha256")
        expected_size = checkpoint.get("size")
        expected_date_raw = checkpoint.get("date_raw")
        if (
            not isinstance(expected_sha256, str)
            or len(expected_sha256) != 64
            or isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size <= 0
            or isinstance(expected_date_raw, bool)
            or not isinstance(expected_date_raw, int)
        ):
            return None
        for row in reversed(self._command_history):
            if row.get("command") != "save-checkpoint" or row.get("ok") is not True:
                continue
            result = row.get("result")
            saved = result.get("checkpoint") if isinstance(result, dict) else None
            if not isinstance(saved, dict):
                continue
            if (
                saved.get("sha256") == expected_sha256
                and saved.get("size") == expected_size
                and saved.get("date_raw") == expected_date_raw
            ):
                index = row.get("index")
                return index if isinstance(index, int) else None
        return None

    def _cold_candidate_ready(self, candidate: dict[str, object]) -> bool:
        if (
            candidate.get("format_version") != _NATIVE_DRIVER_STATE_VERSION
            or self.save_dir is None
        ):
            return False
        character_id = candidate.get("episode_character_id")
        run_id = candidate.get("episode_run_id")
        history = candidate.get("command_history")
        checkpoint = candidate.get("last_checkpoint")
        if (
            isinstance(character_id, bool)
            or not isinstance(character_id, int)
            or not isinstance(run_id, str)
            or not run_id
            or not isinstance(history, list)
            or not isinstance(checkpoint, dict)
        ):
            return False
        history_index = checkpoint.get("history_index")
        sha256 = checkpoint.get("sha256")
        size = checkpoint.get("size")
        date_raw = checkpoint.get("date_raw")
        if (
            isinstance(history_index, bool)
            or not isinstance(history_index, int)
            or history_index < 1
            or history_index > len(history)
            or not isinstance(sha256, str)
            or len(sha256) != 64
            or any(character not in "0123456789abcdef" for character in sha256)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or checkpoint.get("episode_character_id") != character_id
            or checkpoint.get("episode_run_id") != run_id
        ):
            return False
        anchor = history[history_index - 1]
        result = anchor.get("result") if isinstance(anchor, dict) else None
        saved = result.get("checkpoint") if isinstance(result, dict) else None
        return bool(
            isinstance(anchor, dict)
            and anchor.get("index") == history_index
            and anchor.get("command") == "save-checkpoint"
            and anchor.get("ok") is True
            and isinstance(saved, dict)
            and saved.get("sha256") == sha256
            and saved.get("size") == size
            and saved.get("date_raw") == date_raw
        )

    def _bind_episode_from_playable_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        current_character_id: object,
    ) -> None:
        if (
            snapshot.get("map_ready") is not True
            or isinstance(current_character_id, bool)
            or not isinstance(current_character_id, int)
        ):
            return
        if self._bind_new_episode_from_seed_snapshot(
            snapshot, current_character_id=int(current_character_id)
        ):
            return
        with self._driver_state_lock:
            candidate = copy.deepcopy(self._pending_cold_candidate)
        if candidate is None:
            return

        checkpoint = candidate["last_checkpoint"]
        assert isinstance(checkpoint, dict)
        checkpoint_path = self._checkpoint_path()
        rejection: str | None = None
        snapshot_date_raw = snapshot.get("date_raw")
        if current_character_id != candidate.get("episode_character_id"):
            rejection = "played_character_mismatch"
        elif snapshot_date_raw != checkpoint.get("date_raw"):
            rejection = "checkpoint_date_mismatch"
        elif checkpoint_path is None:
            rejection = "checkpoint_path_unavailable"
        else:
            signature = _checkpoint_signature(checkpoint_path)
            if signature is None or signature[0] != checkpoint.get("size"):
                rejection = "checkpoint_size_mismatch"
            elif _sha256_file(checkpoint_path) != checkpoint.get("sha256"):
                rejection = "checkpoint_sha256_mismatch"

        with self._driver_state_lock:
            if self._pending_cold_candidate != candidate:
                return
            if rejection is None:
                history_index = int(checkpoint["history_index"])
                history = copy.deepcopy(candidate["command_history"][:history_index])
                previous_pid = candidate.get("bridge_pid")
                synthetic_result = {
                    "step": _RESTORE_CHECKPOINT_STEP,
                    "accepted": True,
                    "status": "restored",
                    "backend_id": "native-headless",
                    "source": _COLD_RESTORE_SOURCE,
                    "checkpoint": copy.deepcopy(checkpoint),
                    "restored_date_raw": snapshot_date_raw,
                    "map_ready": True,
                    "lifecycle": {
                        "previous_pid": previous_pid,
                        "pid": self._session_bridge_pid,
                    },
                }
                history.append(
                    {
                        "index": len(history) + 1,
                        "command": _RESTORE_CHECKPOINT_STEP,
                        "ok": True,
                        "result": synthetic_result,
                    }
                )
                self._command_history = history
                self._episode_character_id = int(
                    candidate["episode_character_id"]
                )
                self._episode_run_id = str(candidate["episode_run_id"])
                self._last_checkpoint = copy.deepcopy(checkpoint)
                self._driver_state_restored = True
                self._driver_state_restore_kind = "cold_checkpoint"
                self._episode_binding_state = "active_resumed"
                self._cold_candidate_rejection = None
            else:
                self._command_history = []
                self._episode_character_id = current_character_id
                self._episode_run_id = (
                    f"native-{current_character_id}-{uuid.uuid4().hex[:12]}"
                )
                self._last_checkpoint = None
                self._driver_state_restored = False
                self._driver_state_restore_kind = "new_episode"
                self._episode_binding_state = "active_new"
                self._cold_candidate_rejection = rejection
            self._pending_cold_candidate = None
        self._persist_driver_state()

    def _read_driver_state(self) -> dict[str, object] | None:
        if self.state_dir is None:
            return None
        path = self._native_driver_state_path()
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(payload, dict):
                raise ValueError("driver state must be a JSON object")
            format_version = payload.get("format_version")
            if format_version not in (1, _NATIVE_DRIVER_STATE_VERSION):
                return None
            if payload.get("pipe_name") != self.pipe_name:
                return None
            persisted_bridge_pid = payload.get("bridge_pid")
            if (
                isinstance(persisted_bridge_pid, bool)
                or not isinstance(persisted_bridge_pid, int)
                or persisted_bridge_pid <= 0
            ):
                raise ValueError("driver state bridge_pid is malformed")
            character_id = payload.get("episode_character_id")
            run_id = payload.get("episode_run_id")
            if character_id is None:
                if run_id is not None:
                    raise ValueError("driver state has a run without a character")
            elif (
                isinstance(character_id, bool)
                or not isinstance(character_id, int)
                or not isinstance(run_id, str)
                or not run_id
            ):
                raise ValueError("driver state episode identity is malformed")
            history = payload.get("command_history")
            if not isinstance(history, list):
                raise ValueError("driver state command_history is malformed")
            for index, row in enumerate(history, start=1):
                if (
                    not isinstance(row, dict)
                    or row.get("index") != index
                    or not isinstance(row.get("command"), str)
                    or not row.get("command")
                    or not isinstance(row.get("ok"), bool)
                ):
                    raise ValueError("driver state command history is malformed")
            last_checkpoint = payload.get("last_checkpoint")
            if last_checkpoint is not None and not isinstance(
                last_checkpoint, dict
            ):
                raise ValueError("driver state checkpoint is malformed")
            return {
                "format_version": format_version,
                "bridge_pid": persisted_bridge_pid,
                "episode_character_id": character_id,
                "episode_run_id": run_id,
                "command_history": copy.deepcopy(history),
                "last_checkpoint": copy.deepcopy(last_checkpoint),
            }
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            with self._driver_state_lock:
                self._driver_state_error = (
                    f"{type(error).__name__}: {error}"
                )
            return None

    def _persist_driver_state(self) -> None:
        if self.state_dir is None:
            return
        with self._driver_state_lock:
            if self._session_bridge_pid is None:
                return
            payload = {
                "format_version": _NATIVE_DRIVER_STATE_VERSION,
                "pipe_name": self.pipe_name,
                "bridge_pid": self._session_bridge_pid,
                "episode_character_id": self._episode_character_id,
                "episode_run_id": self._episode_run_id,
                "last_checkpoint": copy.deepcopy(self._last_checkpoint),
                "command_history": copy.deepcopy(self._command_history),
            }
        try:
            with self._driver_state_write_lock:
                write_json_atomic(self._native_driver_state_path(), payload)
            with self._driver_state_lock:
                self._driver_state_error = None
        except (OSError, TypeError, ValueError) as error:
            # A gameplay command has already happened by this point.  Keep the
            # live agent usable and surface persistence failure in capabilities
            # instead of falsely reporting that the game command failed.
            with self._driver_state_lock:
                self._driver_state_error = (
                    f"{type(error).__name__}: {error}"
                )

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
            native_error = frame.get("error")
            raise _NativeCommandRejectedError(
                native_error if isinstance(native_error, str) else "unknown error"
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
        with self._driver_state_lock:
            checkpoint["history_index"] = len(self._command_history) + 1
            checkpoint["episode_character_id"] = self._episode_character_id
            checkpoint["episode_run_id"] = self._episode_run_id
            self._last_checkpoint = dict(checkpoint)
        episode_seed = self._establish_episode_seed(checkpoint_path, checkpoint)
        return {
            **submission_result,
            "checkpoint": checkpoint,
            "episode_seed": episode_seed,
            "materialization": {
                "available": True,
                "save_dir": str(self.save_dir.resolve()),
                "mtime_ns": mtime_ns,
            },
        }

    def _establish_episode_seed(
        self,
        checkpoint_path: Path,
        checkpoint: dict[str, object],
    ) -> dict[str, object] | None:
        """Freeze the first baseline save; later recovery saves never replace it."""
        with self._driver_state_lock:
            existing = copy.deepcopy(self._episode_seed)
            character_id = self._episode_character_id
            run_id = self._episode_run_id
        if existing is not None:
            return existing
        if self.state_dir is None or self.save_dir is None:
            return None
        strategy_path = self.state_dir / "strategy" / "one-life-history.json"
        if strategy_path.is_file():
            try:
                strategy = json.loads(strategy_path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                return None
            if isinstance(strategy, dict) and strategy.get("episodes"):
                return None
        if (
            isinstance(character_id, bool)
            or not isinstance(character_id, int)
            or not isinstance(run_id, str)
            or not run_id
        ):
            return None
        seed_path = self._episode_seed_path()
        metadata_path = self._episode_seed_metadata_path()
        if seed_path is None or metadata_path is None:
            return None
        if seed_path.exists():
            # Bytes without their date/character metadata cannot be treated as
            # a seed.  Most importantly, never overwrite them implicitly.
            return None
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = seed_path.with_name(
            f".{seed_path.name}.{uuid.uuid4().hex}.tmp"
        )
        try:
            shutil.copyfile(checkpoint_path, temporary)
            os.link(temporary, seed_path)
        except FileExistsError:
            return self._read_episode_seed()
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        seed = {
            "format_version": 1,
            "name": _EPISODE_SEED_FILENAME,
            "path": str(seed_path.resolve()),
            "size": seed_path.stat().st_size,
            "sha256": _sha256_file(seed_path),
            "date_raw": checkpoint.get("date_raw"),
            "character_id": character_id,
            "source_run_id": run_id,
            "source_checkpoint_name": _CHECKPOINT_FILENAME,
            "immutable": True,
        }
        write_json_atomic(metadata_path, seed)
        with self._driver_state_lock:
            self._episode_seed = dict(seed)
        return seed

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

    def _execute_declarable_war_step(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        if step == QUERY_DECLARABLE_WARS_STEP:
            result = self._execute_primitive_step(
                step, expected_revision=expected_revision
            )
            declarations = normalize_declarable_wars(
                result.get("declarable_wars")
            )
            query_sequence = result.get("query_sequence")
            if (
                isinstance(query_sequence, bool)
                or not isinstance(query_sequence, int)
                or query_sequence < 1
            ):
                raise BridgeUnavailableError(
                    "native declarable-war result lacks query_sequence"
                )
            with self._driver_state_lock:
                self._declarable_wars = copy.deepcopy(declarations)
                self._declaration_query_sequence = query_sequence
            return {
                **result,
                "declarable_wars": declarations,
                "query_sequence": query_sequence,
            }

        declaration_id = parse_declare_war_step(step)
        if declaration_id is None:
            raise UnsupportedStepError(
                f"native Python bridge does not implement declaration step {step}"
            )
        with self._driver_state_lock:
            declaration = next(
                (
                    copy.deepcopy(row)
                    for row in self._declarable_wars
                    if row.get("declaration_id") == declaration_id
                ),
                None,
            )
        if declaration is None:
            raise BridgeUnavailableError(
                "native declare-war choice is not in the latest query"
            )
        starting = self.take_snapshot()
        starting_wars = starting.get("active_wars")
        starting_count = len(starting_wars) if isinstance(starting_wars, list) else 0
        try:
            result = self._execute_primitive_step(
                step, expected_revision=expected_revision
            )
        finally:
            with self._driver_state_lock:
                self._declarable_wars = []
                self._declaration_query_sequence = None
        changed = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: (
                isinstance(snapshot.get("active_wars"), list)
                and len(snapshot["active_wars"]) > starting_count
            ),
            timeout_seconds=self.command_timeout_seconds,
        )
        active_wars = changed.get("active_wars")
        war_started = (
            isinstance(active_wars, list) and len(active_wars) > starting_count
        )
        return {
            **result,
            "declaration": declaration,
            "war_action": {
                "status": "war_started" if war_started else "declaration_submitted",
                "declaration_id": declaration_id,
                "target_character_id": declaration["target_character_id"],
                "casus_belli_key": declaration["casus_belli_key"],
            },
            "active_wars": active_wars if isinstance(active_wars, list) else [],
            "snapshot_id": changed["snapshot_id"],
            "revision": changed["revision"],
        }

    def _execute_arrange_marriage_step(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        if step == QUERY_ARRANGE_MARRIAGE_CHOICES_STEP:
            result = self._execute_primitive_step(
                step, expected_revision=expected_revision
            )
            choices = normalize_arrange_marriage_choices(
                result.get("arrange_marriage_choices")
            )
            query_sequence = result.get("query_sequence")
            if (
                isinstance(query_sequence, bool)
                or not isinstance(query_sequence, int)
                or query_sequence < 1
            ):
                raise BridgeUnavailableError(
                    "native arrange-marriage result lacks query_sequence"
                )
            current_character = self.take_snapshot().get("played_character")
            current_character_id = (
                current_character.get("character_id")
                if isinstance(current_character, dict)
                else None
            )
            if any(
                choice["played_character_id"] != current_character_id
                for choice in choices
            ):
                raise BridgeUnavailableError(
                    "native arrange-marriage query returned another player"
                )
            with self._driver_state_lock:
                self._arrange_marriage_choices = copy.deepcopy(choices)
                self._arrange_marriage_query_sequence = query_sequence
            return {
                **result,
                "arrange_marriage_choices": choices,
                "query_sequence": query_sequence,
            }

        choice_id = parse_arrange_marriage_step(step)
        if choice_id is None:
            raise UnsupportedStepError(
                f"native Python bridge does not implement marriage step {step}"
            )
        with self._driver_state_lock:
            choice = next(
                (
                    copy.deepcopy(row)
                    for row in self._arrange_marriage_choices
                    if row.get("choice_id") == choice_id
                ),
                None,
            )
        if choice is None:
            raise BridgeUnavailableError(
                "native arrange-marriage choice is not in the latest query"
            )
        starting = self.take_snapshot()
        submitted_date_raw = _date_raw(
            starting, "arrange-marriage submission snapshot"
        )
        try:
            result = self._execute_primitive_step(
                step, expected_revision=expected_revision
            )
        finally:
            with self._driver_state_lock:
                self._arrange_marriage_choices = []
                self._arrange_marriage_query_sequence = None
        return {
            **result,
            "marriage_choice": choice,
            "marriage_action": {
                "status": "proposal_submitted",
                "choice_id": choice_id,
                "played_character_id": choice["played_character_id"],
                "candidate_character_id": choice["candidate_character_id"],
                "submitted_date_raw": submitted_date_raw,
            },
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

        preview = parse_preview_move_army_step(step)
        if preview is not None:
            army_id, province_id = preview
            if starting.get("paused") is not True:
                raise BridgeUnavailableError(
                    "native move preview requires the paused map"
                )
            starting_army = _army_by_id(starting, army_id)
            if (
                not isinstance(starting_army, dict)
                or starting_army.get("controllable") is not True
            ):
                raise BridgeUnavailableError(
                    f"native preview-move-army-{army_id} requires a "
                    "controllable player army"
                )
            origin_province_id = starting_army.get("current_province_id")
            if not isinstance(origin_province_id, int) or isinstance(
                origin_province_id, bool
            ):
                raise BridgeUnavailableError(
                    "native move preview requires the army's current province"
                )
            previewed_date_raw = _date_raw(
                starting, "move preview starting snapshot"
            )
            try:
                result = self._execute_primitive_step(
                    step, expected_revision=selected_revision
                )
            except _NativeCommandRejectedError as error:
                if error.native_error not in _ARMY_MOVE_DEFERRED_ERRORS:
                    raise
                current = self.take_snapshot()
                return {
                    "step": step,
                    "accepted": False,
                    "status": "deferred",
                    "backend_id": "native-headless",
                    "route_preview": {
                        "status": "deferred",
                        "reason": "army_not_move_ready",
                        "army_id": army_id,
                        "origin_province_id": origin_province_id,
                        "target_province_id": province_id,
                        "route_province_ids": [],
                        "previewed_date_raw": previewed_date_raw,
                    },
                    "player_armies": current.get("player_armies", []),
                    "snapshot_id": current["snapshot_id"],
                    "revision": current["revision"],
                }
            route_preview = result.get("route_preview")
            route_province_ids = (
                route_preview.get("route_province_ids")
                if isinstance(route_preview, dict)
                else None
            )
            remaining_route = (
                list(route_province_ids)
                if isinstance(route_province_ids, list)
                else []
            )
            if (
                remaining_route
                and remaining_route[0] == origin_province_id
            ):
                remaining_route = remaining_route[1:]
            route_reaches_target = (
                province_id == origin_province_id and not remaining_route
            ) or (
                bool(remaining_route)
                and remaining_route[-1] == province_id
            )
            if (
                not isinstance(route_preview, dict)
                or route_preview.get("status") != "available"
                or route_preview.get("army_id") != army_id
                or route_preview.get("origin_province_id")
                != origin_province_id
                or route_preview.get("target_province_id") != province_id
                or not isinstance(route_province_ids, list)
                or any(
                    isinstance(item, bool)
                    or not isinstance(item, int)
                    or item <= 0
                    for item in route_province_ids
                )
                or not route_reaches_target
            ):
                raise BridgeUnavailableError(
                    "native move preview returned a malformed route_preview"
                )
            return {
                **result,
                "route_preview": {
                    **route_preview,
                    "route_province_ids": list(route_province_ids),
                    "previewed_date_raw": previewed_date_raw,
                },
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
            submitted_date_raw = _date_raw(
                starting, "move starting snapshot"
            )
            try:
                result = self._execute_primitive_step(
                    step, expected_revision=selected_revision
                )
            except _NativeCommandRejectedError as error:
                if error.native_error not in _ARMY_MOVE_DEFERRED_ERRORS:
                    raise
                current = self.take_snapshot()
                return {
                    "step": step,
                    "accepted": False,
                    "status": "deferred",
                    "backend_id": "native-headless",
                    "war_action": {
                        "status": "move_deferred",
                        "reason": "army_not_move_ready",
                        "army_id": army_id,
                        "target_province_id": province_id,
                        "submitted_date_raw": submitted_date_raw,
                    },
                    "player_armies": current.get("player_armies", []),
                    "snapshot_id": current["snapshot_id"],
                    "revision": current["revision"],
                }
            capability_payload = self.capabilities()
            bridge_capabilities = capability_payload.get("bridge_capabilities")
            army_routes_supported = bool(
                isinstance(bridge_capabilities, list)
                and ARMY_ROUTES_CAPABILITY in bridge_capabilities
            )
            if (
                isinstance(starting_army, dict)
                and starting_army.get("move_target_observable") is False
                and not army_routes_supported
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
                        "submitted_date_raw": submitted_date_raw,
                        "move_target_observable": False,
                    },
                    "player_armies": current.get("player_armies", []),
                    "snapshot_id": current["snapshot_id"],
                    "revision": current["revision"],
                }
            changed = self._wait_for_snapshot(
                self.take_snapshot(),
                lambda snapshot: _army_move_postcondition(
                    snapshot,
                    army_id,
                    province_id,
                    require_route=army_routes_supported,
                ) is not None,
                timeout_seconds=self.command_timeout_seconds,
            )
            status = _army_move_postcondition(
                changed,
                army_id,
                province_id,
                require_route=army_routes_supported,
            )
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
                    "submitted_date_raw": submitted_date_raw,
                },
                "player_armies": changed.get("player_armies", []),
                "snapshot_id": changed["snapshot_id"],
                "revision": changed["revision"],
            }

        war_id = parse_enforce_demands_step(step)
        if war_id is not None:
            if _war_by_id(starting, war_id) is None:
                raise BridgeUnavailableError(
                    f"native enforce-demands-{war_id} requires an active war"
                )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            changed = self._wait_for_snapshot(
                self.take_snapshot(),
                lambda snapshot: _war_by_id(snapshot, war_id) is None,
                timeout_seconds=self.command_timeout_seconds,
            )
            if _war_by_id(changed, war_id) is not None:
                raise BridgeUnavailableError(
                    f"native enforce-demands-{war_id} did not end the war"
                )
            return {
                **result,
                "war_action": {
                    "status": "victory_enforced",
                    "war_id": war_id,
                },
                "war_victory": {
                    "status": "victory_enforced",
                    "war_id": war_id,
                },
                "active_wars": changed.get("active_wars", []),
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
        checkpoint_size = signature[0]
        checkpoint_sha256 = _sha256_file(checkpoint_path)
        with self._driver_state_lock:
            previous_checkpoint = copy.deepcopy(self._last_checkpoint) or {}
            expected_episode_character_id = self._episode_character_id
        checkpoint_saved_date_raw = previous_checkpoint.get("date_raw")
        if not isinstance(checkpoint_saved_date_raw, int) or isinstance(
            checkpoint_saved_date_raw, bool
        ):
            checkpoint_saved_date_raw = None

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
                "checkpoint_size": checkpoint_size,
                "checkpoint_sha256": checkpoint_sha256,
                "checkpoint_saved_date_raw": checkpoint_saved_date_raw,
            },
        )

        deadline = time.monotonic() + self.restore_timeout_seconds
        response = self._wait_for_restore_response(
            response_path, request_id, deadline
        )
        restored = self._wait_for_restored_map(starting_generation, deadline)
        restored_date_raw = _date_raw(restored, "restored snapshot")
        if (
            checkpoint_saved_date_raw is not None
            and restored_date_raw != checkpoint_saved_date_raw
        ):
            raise BridgeUnavailableError(
                "native-session loaded a different save date than the requested "
                "checkpoint: "
                f"{restored_date_raw} != {checkpoint_saved_date_raw}"
            )
        restored_character = restored.get("played_character")
        restored_character_id = (
            restored_character.get("character_id")
            if isinstance(restored_character, dict)
            else None
        )
        if (
            expected_episode_character_id is not None
            and restored_character_id != expected_episode_character_id
        ):
            raise BridgeUnavailableError(
                "native-session restored a different played character than the "
                "checkpoint episode: "
                f"{restored_character_id} != {expected_episode_character_id}"
            )
        restored_signature = _checkpoint_signature(checkpoint_path)
        if restored_signature is None or restored_signature[0] <= 0:
            raise BridgeUnavailableError(
                "native-session restored CK3 but its checkpoint file is missing"
            )
        size, mtime_ns = restored_signature
        lifecycle_result = response.get("result")
        lifecycle = (
            dict(lifecycle_result)
            if isinstance(lifecycle_result, dict)
            else {}
        )
        lifecycle_checkpoint = lifecycle.get("checkpoint")
        if not isinstance(lifecycle_checkpoint, dict) or (
            lifecycle_checkpoint.get("name") != _CHECKPOINT_FILENAME
            or lifecycle_checkpoint.get("size") != checkpoint_size
            or lifecycle_checkpoint.get("sha256") != checkpoint_sha256
        ):
            raise BridgeUnavailableError(
                "native-session did not attest the requested checkpoint bytes"
            )
        restored_sha256 = _sha256_file(checkpoint_path)
        if restored_sha256 != checkpoint_sha256:
            raise BridgeUnavailableError(
                "native checkpoint bytes changed during restore"
            )
        restored_checkpoint = {
            "status": "restored",
            "path": str(checkpoint_path.resolve()),
            "name": checkpoint_path.name,
            "size": size,
            "sha256": restored_sha256,
            "date_raw": restored_date_raw,
            "saved_date_raw": checkpoint_saved_date_raw,
            "mtime_ns": mtime_ns,
            "strategy": "native-session-loadsave-exact-v2",
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

    def _execute_start_next_episode(
        self, *, expected_revision: int | None
    ) -> dict[str, object]:
        """Relaunch the immutable campaign seed and bind a fresh one-life run."""
        if self.state_dir is None:
            raise UnsupportedStepError(
                "start-next-episode requires a managed pure-native session"
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
        with self._driver_state_lock:
            terminal = self._completed_terminal_result_locked()
            seed = copy.deepcopy(self._episode_seed)
            source_run_id = self._episode_run_id
        if terminal is None:
            raise BridgeUnavailableError(
                "start-next-episode requires a complete scored death-terminal"
            )
        if not self._episode_seed_matches_file(seed, verify_sha256=True):
            raise BridgeUnavailableError(
                "start-next-episode requires the immutable xar_episode_seed.ck3"
            )
        assert isinstance(seed, dict)
        diagnostics = self.state.diagnostics()
        starting_generation = diagnostics.get("connection_generation")
        if (
            isinstance(starting_generation, bool)
            or not isinstance(starting_generation, int)
            or starting_generation < 1
        ):
            raise BridgeUnavailableError(
                "start-next-episode requires a connected DLL generation"
            )

        request_id = f"next-episode-{uuid.uuid4().hex}"
        transition = {
            "format_version": 1,
            "request_id": request_id,
            "command": _START_NEXT_EPISODE_STEP,
            "phase": "relaunching_episode_seed",
            "source_run_id": source_run_id,
            "seed": copy.deepcopy(seed),
        }
        with self._driver_state_lock:
            self._episode_transition = transition
            self._episode_transition_error = None
            self._episode_binding_state = "relaunching_episode_seed"
            self._persist_episode_transition_locked()

        queue_dir = self._native_session_queue_dir()
        response_path = queue_dir / "outbox" / f"{request_id}.json"
        write_json_atomic(
            queue_dir / "inbox" / f"{request_id}.json",
            {
                "protocol_version": SESSION_QUEUE_PROTOCOL_VERSION,
                "request_id": request_id,
                "command": _START_NEXT_EPISODE_STEP,
                "pipe": self.pipe_name,
                "seed_name": _EPISODE_SEED_FILENAME,
                "seed_size": seed["size"],
                "seed_sha256": seed["sha256"],
                "seed_date_raw": seed["date_raw"],
                "seed_character_id": seed["character_id"],
                "source_run_id": source_run_id,
            },
        )
        deadline = time.monotonic() + self.restore_timeout_seconds
        try:
            response = self._wait_for_restore_response(
                response_path, request_id, deadline
            )
            lifecycle_result = response.get("result")
            lifecycle = (
                dict(lifecycle_result)
                if isinstance(lifecycle_result, dict)
                else {}
            )
            lifecycle_seed = lifecycle.get("episode_seed")
            if not isinstance(lifecycle_seed, dict) or (
                lifecycle_seed.get("name") != _EPISODE_SEED_FILENAME
                or lifecycle_seed.get("size") != seed["size"]
                or lifecycle_seed.get("sha256") != seed["sha256"]
                or lifecycle.get("lifecycle_intent") != "new_episode"
            ):
                raise BridgeUnavailableError(
                    "native-session did not attest the new-episode seed lifecycle"
                )
            resumed = self._wait_for_restored_map(starting_generation, deadline)
            resumed = self._with_one_life_episode(resumed)
            with self._driver_state_lock:
                transition_error = self._episode_transition_error
                new_run_id = self._episode_run_id
                new_character_id = self._episode_character_id
            if transition_error is not None:
                raise BridgeUnavailableError(
                    f"episode seed binding failed: {transition_error}"
                )
            if new_run_id == source_run_id or not isinstance(new_run_id, str):
                raise BridgeUnavailableError(
                    "episode seed relaunch did not create a new run identity"
                )
        except Exception:
            with self._driver_state_lock:
                if self._episode_transition is not None:
                    self._episode_transition["phase"] = "blocked"
                    self._persist_episode_transition_locked()
            raise

        from ..strategy import read_one_life_strategy

        cross_run = read_one_life_strategy(self.state_dir)
        return {
            "step": _START_NEXT_EPISODE_STEP,
            "accepted": True,
            "status": "started",
            "backend_id": "native-headless",
            "source": "native-session-lifecycle-queue",
            "lifecycle_intent": "new_episode",
            "source_run_id": source_run_id,
            "episode_run_id": new_run_id,
            "episode_character_id": new_character_id,
            "same_character_id": new_character_id == seed["character_id"],
            "episode_seed": copy.deepcopy(seed),
            "cross_run_plan_used": copy.deepcopy(cross_run["next_run_plan"]),
            "lifecycle": {
                **lifecycle,
                "request_id": request_id,
                "previous_connection_generation": starting_generation,
                "connection_generation": resumed["diagnostics"][
                    "connection_generation"
                ],
            },
            "map_ready": True,
            "paused": resumed.get("paused"),
            "snapshot_id": resumed["snapshot_id"],
            "revision": resumed["revision"],
        }

    def _execute_native_death_terminal(
        self,
        *,
        expected_revision: int | None,
        projected_settlement: dict[str, object] | None = None,
        settlement_source: str = "native-headless",
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
            else (
                "native_played_character_missing"
                if terminal_reason == "played_character_missing"
                else "native_played_character_dead"
            )
        )
        episode_character_id = snapshot.get("episode_character_id")
        result: dict[str, object] = {
            "step": _NATIVE_DEATH_TERMINAL_STEP,
            "backend_id": "native-headless",
            "terminal": True,
            "terminal_kind": terminal_kind,
            "terminal_reason": terminal_reason,
            "episode_character_id": episode_character_id,
            "technical_settlement_handoff": False,
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": None,
            "played_character": copy.deepcopy(played_character),
            "date_raw": snapshot.get("date_raw"),
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
        }

        bridge_capabilities = set(
            _string_list(self.state.capabilities().get("bridge_capabilities"))
        )
        if projected_settlement is not None:
            settlement = normalize_one_life_settlement(projected_settlement)
            if not settlement_ready_for_episode(
                settlement, episode_character_id
            ):
                raise BridgeUnavailableError(
                    "projected one-life settlement does not match episode "
                    f"CharacterID {episode_character_id}"
                )
            deadline = time.monotonic() + self.settlement_timeout_seconds
            persistence = self._wait_for_settlement_record_persistence(
                settlement, deadline=deadline
            )
            result.update(
                {
                    "settlement_status": "complete",
                    "settlement_unavailable": False,
                    "settlement_source": settlement_source,
                    "one_life_settlement": copy.deepcopy(settlement),
                    "record_persistence": persistence,
                    "score": settlement["final_score"],
                }
            )
        elif ONE_LIFE_SETTLEMENT_CAPABILITY not in bridge_capabilities:
            result.update(
                {
                    "settlement_status": "settlement_unavailable",
                    "settlement_unavailable": True,
                    "one_life_settlement": None,
                    "record_persistence": {
                        "status": "settlement_unavailable",
                        "required": False,
                    },
                }
            )
        else:
            if (
                isinstance(episode_character_id, bool)
                or not isinstance(episode_character_id, int)
            ):
                raise BridgeUnavailableError(
                    "native one-life terminal lacks an episode CharacterID"
                )
            deadline = time.monotonic() + self.settlement_timeout_seconds
            settled_snapshot, settlement = self._wait_for_episode_settlement(
                snapshot,
                episode_character_id=episode_character_id,
                deadline=deadline,
            )
            persistence = self._wait_for_settlement_record_persistence(
                settlement, deadline=deadline
            )
            result.update(
                {
                    "settlement_status": "complete",
                    "settlement_unavailable": False,
                    "settlement_source": "native-headless",
                    "one_life_settlement": copy.deepcopy(settlement),
                    "record_persistence": persistence,
                    "score": settlement["final_score"],
                    "date_raw": settled_snapshot.get("date_raw"),
                    "snapshot_id": settled_snapshot["snapshot_id"],
                    "revision": settled_snapshot["revision"],
                }
            )

        if (
            self.state_dir is not None
            and result.get("settlement_status") == "complete"
            and result.get("score") is not None
        ):
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

    def finalize_projected_one_life_settlement(
        self,
        settlement: dict[str, object],
        *,
        expected_revision: int | None = None,
        source: str,
    ) -> dict[str, object]:
        """Finalize a semantic settlement read by a non-visual fallback."""
        try:
            result = self._execute_native_death_terminal(
                expected_revision=expected_revision,
                projected_settlement=settlement,
                settlement_source=source,
            )
        except Exception as error:
            self._record_command(
                _NATIVE_DEATH_TERMINAL_STEP,
                ok=False,
                error=f"{type(error).__name__}: {error}",
            )
            raise
        self._record_command(
            _NATIVE_DEATH_TERMINAL_STEP,
            ok=True,
            result=result,
        )
        return result

    def _wait_for_episode_settlement(
        self,
        snapshot: dict[str, object],
        *,
        episode_character_id: int,
        deadline: float,
    ) -> tuple[dict[str, object], dict[str, object]]:
        current = snapshot
        while True:
            settlement = current.get("one_life_settlement")
            if settlement_ready_for_episode(settlement, episode_character_id):
                return current, dict(settlement)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                status = current.get("one_life_settlement_status")
                raise BridgeUnavailableError(
                    "native one-life settlement did not become ready for "
                    f"episode CharacterID {episode_character_id}; status={status}"
                )
            self.state.wait_for_public_change(
                int(current["revision"]),
                min(self.settlement_poll_interval_seconds, remaining),
            )
            current = self.take_snapshot()

    def _wait_for_settlement_record_persistence(
        self,
        settlement: dict[str, object],
        *,
        deadline: float,
    ) -> dict[str, object]:
        candidate = settlement["record_candidate"]
        if not isinstance(candidate, int) or isinstance(candidate, bool):
            raise BridgeUnavailableError(
                "native one-life settlement lacks record_candidate"
            )
        if candidate == 0:
            return {
                "status": "not_required_zero_score",
                "required": False,
                "record_candidate": 0,
            }
        if settlement.get("record_written") is not True:
            return {
                "status": "not_required_no_new_record",
                "required": False,
                "record_candidate": candidate,
            }
        if self.state_dir is None:
            raise BridgeUnavailableError(
                "native new-record settlement requires state_dir to verify "
                "tutorial.txt persistence"
            )

        tutorial_path = self.state_dir / "profile" / "tutorial.txt"
        stable_signature: tuple[object, object] | None = None
        stable_observations = 0
        last_observation: dict[str, object] | None = None
        while True:
            try:
                observation = tutorial_record_observation(
                    tutorial_path, candidate
                )
            except (OSError, UnicodeError, ValueError) as error:
                observation = {
                    "path": str(tutorial_path),
                    "lesson_id": f"xar_hs_ge_{candidate}",
                    "present": False,
                    "read_error": f"{type(error).__name__}: {error}",
                }
            last_observation = observation
            if observation.get("present") is True:
                signature = (
                    observation.get("size"),
                    observation.get("sha256"),
                )
                if signature == stable_signature:
                    stable_observations += 1
                else:
                    stable_signature = signature
                    stable_observations = 1
                if stable_observations >= 2:
                    return {
                        **observation,
                        "status": "persisted",
                        "required": True,
                        "record_candidate": candidate,
                        "stable_observations": stable_observations,
                    }
            else:
                stable_signature = None
                stable_observations = 0

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                detail = (
                    last_observation.get("read_error")
                    if isinstance(last_observation, dict)
                    else None
                )
                raise BridgeUnavailableError(
                    "native one-life record lesson did not persist stably to "
                    f"{tutorial_path}: xar_hs_ge_{candidate}"
                    + (f" ({detail})" if isinstance(detail, str) else "")
                )
            time.sleep(min(self.settlement_poll_interval_seconds, remaining))

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
        stable_revision: int | None = None
        stable_since: float | None = None
        while True:
            now = time.monotonic()
            diagnostics = self.state.diagnostics()
            generation = diagnostics.get("connection_generation")
            if isinstance(generation, int) and generation > starting_generation:
                try:
                    snapshot = self.state.semantic_snapshot()
                except BridgeUnavailableError:
                    snapshot = None
                if (
                    isinstance(snapshot, dict)
                    and snapshot.get("map_ready") is True
                    and isinstance(snapshot.get("played_character"), dict)
                ):
                    revision = int(snapshot["revision"])
                    if revision != stable_revision:
                        stable_revision = revision
                        stable_since = now
                    elif (
                        stable_since is not None
                        and now - stable_since >= _RESTORE_MAP_STABLE_SECONDS
                    ):
                        return snapshot
                else:
                    stable_revision = None
                    stable_since = None
            remaining = deadline - now
            if remaining <= 0:
                raise BridgeUnavailableError(
                    "native-session relaunched CK3 but no newer DLL generation "
                    "published a stable map_ready snapshot with played_character"
                )
            wait_seconds = remaining
            if stable_since is not None:
                wait_seconds = min(
                    wait_seconds,
                    max(
                        0.001,
                        _RESTORE_MAP_STABLE_SECONDS - (now - stable_since),
                    ),
                )
            self.state.wait_for_public_change(observed_revision, wait_seconds)
            observed_revision = self.state.public_revision()

    def _native_driver_state_path(self) -> Path:
        if self.state_dir is None:
            raise UnsupportedStepError(
                "native driver state requires state_dir"
            )
        return (
            self.state_dir
            / _NATIVE_SESSION_QUEUE_DIRNAME
            / _NATIVE_DRIVER_STATE_FILENAME
        )

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
        while not _life_advance_progressed(current, starting):
            remaining = progress_deadline - time.monotonic()
            if remaining <= 0:
                break
            current = self.wait_for_change(
                int(current["revision"]),
                timeout_seconds=remaining,
            )

        current = self._pause_life_advance(current, actions)
        reached_progress_postcondition = _life_advance_progressed(
            current, starting
        )
        if not reached_progress_postcondition:
            current_date_raw = _date_raw(
                current, "active-war bounded ending snapshot"
            )
            if current_date_raw > starting_date_raw:
                progress_status = "wall_timeout_with_date_progress"
            elif starting.get("active_wars"):
                horizon_days = _life_advance_horizon_days(starting)
                raise BridgeUnavailableError(
                    "native active-war life-advance observed no event, war "
                    "or army progress, and did not reach its "
                    f"{horizon_days}-day horizon"
                )
            else:
                raise BridgeUnavailableError(
                    "native life-advance observed neither a date change nor an active event"
                )
        else:
            progress_status = "postcondition"

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
            "progress_status": progress_status,
            "war_progress_before": _war_progress_summary(starting),
            "war_progress_after": _war_progress_summary(current),
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
        if _START_NEXT_EPISODE_STEP not in native_steps:
            action_steps.discard(_START_NEXT_EPISODE_STEP)
        action_steps = {
            step
            for step in action_steps
            if (
                not is_native_war_step(step)
                and not is_native_declaration_step(step)
                and not is_native_marriage_step(step)
            )
            or step in native_steps
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
        if step == _NATIVE_DEATH_TERMINAL_STEP:
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            data_bridge_capabilities = set(
                _string_list(
                    self.data_mod.capabilities().get("bridge_capabilities")
                )
            )
            if (
                ONE_LIFE_SETTLEMENT_CAPABILITY
                not in native_bridge_capabilities
                and ONE_LIFE_SETTLEMENT_CAPABILITY
                in data_bridge_capabilities
            ):
                return self._execute_data_mod_death_terminal(
                    expected_revision=expected_revision
                )
        if (
            step in {_RESTORE_CHECKPOINT_STEP, _START_NEXT_EPISODE_STEP}
            and step
            not in _string_list(self.native.capabilities().get("action_steps"))
        ):
            raise UnsupportedStepError(
                f"{step} is pure native and will not use fallback"
            )
        if (
            (
                is_native_war_step(step)
                or is_native_declaration_step(step)
                or is_native_marriage_step(step)
            )
            and step
            not in _string_list(self.native.capabilities().get("action_steps"))
        ):
            raise UnsupportedStepError(
                "native strategic steps are pure native and will not use fallback"
            )
        return self._delegate.execute_step(step, expected_revision=expected_revision)

    def _execute_data_mod_death_terminal(
        self, *, expected_revision: int | None
    ) -> dict[str, object]:
        starting = self.take_snapshot()
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != starting["revision"]:
                raise BridgeUnavailableError(
                    "hybrid gameplay revision mismatch: "
                    f"expected {expected_revision}, current {starting['revision']}"
                )
        terminal_reason = starting.get("one_life_terminal_reason")
        episode_character_id = starting.get("episode_character_id")
        if not isinstance(terminal_reason, str) or (
            isinstance(episode_character_id, bool)
            or not isinstance(episode_character_id, int)
        ):
            raise BridgeUnavailableError(
                "hybrid one-life settlement requires a native terminal identity"
            )

        deadline = time.monotonic() + self.native.settlement_timeout_seconds
        settlement = starting.get("one_life_settlement")
        while not settlement_ready_for_episode(
            settlement, episode_character_id
        ):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeUnavailableError(
                    "data Mod one-life settlement did not become ready for "
                    f"episode CharacterID {episode_character_id}"
                )
            time.sleep(
                min(self.native.settlement_poll_interval_seconds, remaining)
            )
            data_snapshot = self.data_mod.take_snapshot()
            settlement = normalize_one_life_settlement(
                data_snapshot.get("one_life_settlement")
            )

        native_snapshot = self.native.take_snapshot()
        result = self.native.finalize_projected_one_life_settlement(
            dict(settlement),
            expected_revision=int(native_snapshot["revision"]),
            source="data-mod",
        )
        return {
            **result,
            "backend_id": "hybrid-fallback",
            "settlement_projection_backend": "data-mod",
        }

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
        "one_life_settlement": normalize_one_life_settlement(
            state.get("one_life_settlement")
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
    snapshot: dict[str, object], starting_snapshot: dict[str, object]
) -> bool:
    active_event = snapshot.get("active_event")
    if isinstance(active_event, dict):
        return True
    if isinstance(snapshot.get("one_life_terminal_reason"), str):
        return True
    starting_date_raw = _date_raw(
        starting_snapshot, "life-advance starting snapshot"
    )
    current_date_raw = snapshot.get("date_raw")
    if isinstance(current_date_raw, bool) or not isinstance(
        current_date_raw, int
    ):
        return False
    starting_war_progress = _active_war_progress_signature(
        starting_snapshot
    )
    if not starting_war_progress:
        return current_date_raw > starting_date_raw
    if _active_war_progress_signature(snapshot) != starting_war_progress:
        return True
    starting_threats = set(
        _stationary_army_threat_relations(starting_snapshot)
    )
    current_threats = set(_stationary_army_threat_relations(snapshot))
    if current_threats - starting_threats:
        return True
    return current_date_raw >= (
        starting_date_raw + _life_advance_horizon_days(starting_snapshot) * 24
    )


def _life_advance_horizon_days(snapshot: dict[str, object]) -> int:
    """Use short paused-to-paused slices while the player owns a siege.

    Rich CSiege state is intentionally unavailable in running snapshots.  We
    therefore only classify the starting paused frame and stop by date; a
    running ``active_siege=null`` can never masquerade as siege completion.
    """
    if (
        snapshot.get("paused") is not True
        or snapshot.get("war_objective_siege_progress_supported") is not True
    ):
        return _NATIVE_WAR_ADVANCE_MAX_DAYS
    wars = snapshot.get("active_wars")
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        states = war.get("objective_province_states")
        for state in states if isinstance(states, list) else []:
            active_siege = (
                state.get("active_siege")
                if isinstance(state, dict)
                and state.get("siege_observable") is True
                else None
            )
            if (
                isinstance(active_siege, dict)
                and active_siege.get("player_army_besieging") is True
            ):
                return _NATIVE_SIEGE_ADVANCE_MAX_DAYS
    return _NATIVE_WAR_ADVANCE_MAX_DAYS


def _active_war_progress_signature(
    snapshot: dict[str, object],
) -> tuple[tuple[object, ...], ...]:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return ()
    result: list[tuple[object, ...]] = []
    for war in wars:
        if not isinstance(war, dict):
            continue
        war_id = war.get("war_id")
        score = war.get("player_relative_war_score")
        if (
            isinstance(war_id, bool)
            or not isinstance(war_id, int)
            or isinstance(score, bool)
            or not isinstance(score, int)
        ):
            continue
        army_progress: list[tuple[object, ...]] = []
        armies = war.get("allied_armies")
        for army in armies if isinstance(armies, list) else []:
            if not isinstance(army, dict) or army.get("controllable") is not True:
                continue
            army_id = army.get("army_id")
            province_id = army.get("current_province_id")
            if isinstance(army_id, bool) or not isinstance(army_id, int):
                continue
            army_progress.append(
                (
                    army_id,
                    province_id
                    if isinstance(province_id, int)
                    and not isinstance(province_id, bool)
                    else -1,
                    (
                        army.get("move_target_province_id")
                        if isinstance(army.get("move_target_province_id"), int)
                        and not isinstance(
                            army.get("move_target_province_id"), bool
                        )
                        else -1
                    ),
                    (
                        army.get("army_state")
                        if isinstance(army.get("army_state"), str)
                        else ""
                    ),
                    (
                        army.get("army_state_code")
                        if isinstance(army.get("army_state_code"), int)
                        and not isinstance(army.get("army_state_code"), bool)
                        else -1
                    ),
                    1 if army.get("in_combat") is True else 0,
                    1 if army.get("retreating") is True else 0,
                )
            )
        result.append(
            (
                war_id,
                score,
                tuple(sorted(army_progress)),
            )
        )
    return tuple(sorted(result))


def _stationary_army_threat_relations(
    snapshot: dict[str, object],
) -> tuple[tuple[int, int, int, int], ...]:
    wars = snapshot.get("active_wars")
    relations: list[tuple[int, int, int, int]] = []
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        war_id = war.get("war_id")
        if isinstance(war_id, bool) or not isinstance(war_id, int):
            continue
        allied = war.get("allied_armies")
        stationary: list[tuple[int, int]] = []
        for army in allied if isinstance(allied, list) else []:
            if not isinstance(army, dict) or army.get("controllable") is not True:
                continue
            army_id = army.get("army_id")
            province_id = army.get("current_province_id")
            move_target = army.get("move_target_province_id")
            state = army.get("army_state")
            state_code = army.get("army_state_code")
            stationary_state = (
                isinstance(state, str)
                and state.casefold() in {"regular", "sieging"}
            ) or (
                not isinstance(state, str)
                and isinstance(state_code, int)
                and not isinstance(state_code, bool)
                and state_code in {1, 3}
            )
            if (
                isinstance(army_id, bool)
                or not isinstance(army_id, int)
                or isinstance(province_id, bool)
                or not isinstance(province_id, int)
                or not stationary_state
                or (
                    isinstance(move_target, int)
                    and not isinstance(move_target, bool)
                )
                or army.get("in_combat") is True
                or army.get("retreating") is True
            ):
                continue
            stationary.append((army_id, province_id))

        enemy = war.get("enemy_armies")
        for hostile in enemy if isinstance(enemy, list) else []:
            if not isinstance(hostile, dict):
                continue
            hostile_state = hostile.get("army_state")
            if hostile.get("retreating") is True or (
                isinstance(hostile_state, str)
                and hostile_state.casefold() == "retreating"
            ):
                continue
            hostile_id = hostile.get("army_id")
            if isinstance(hostile_id, bool) or not isinstance(hostile_id, int):
                continue
            route = hostile.get("route_province_ids")
            threatened = {
                province_id
                for province_id in (
                    hostile.get("current_province_id"),
                    hostile.get("move_target_province_id"),
                    *(route if isinstance(route, list) else []),
                )
                if isinstance(province_id, int)
                and not isinstance(province_id, bool)
            }
            relations.extend(
                (war_id, army_id, hostile_id, province_id)
                for army_id, province_id in stationary
                if province_id in threatened
            )
    return tuple(sorted(relations))


def _war_progress_summary(snapshot: dict[str, object]) -> dict[str, object]:
    """Persist the small tactical slice needed to bound future war decisions."""
    wars = snapshot.get("active_wars")
    result: list[dict[str, object]] = []
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        result.append(
            {
                "war_id": war.get("war_id"),
                "player_relative_war_score": war.get(
                    "player_relative_war_score"
                ),
                "war_objective_province_ids": list(
                    war.get("war_objective_province_ids", [])
                ),
                "objective_province_states": copy.deepcopy(
                    war.get("objective_province_states", [])
                    if isinstance(
                        war.get("objective_province_states"), list
                    )
                    else []
                ),
                "enemy_primary_default_raise_province_id": war.get(
                    "enemy_primary_default_raise_province_id"
                ),
                "player_armies": _war_progress_armies(
                    war.get("allied_armies"), controllable=True
                ),
                "enemy_armies": _war_progress_armies(
                    war.get("enemy_armies"), controllable=None
                ),
            }
        )
    return {"date_raw": snapshot.get("date_raw"), "wars": result}


def _war_progress_armies(
    value: object, *, controllable: bool | None
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for army in value if isinstance(value, list) else []:
        if not isinstance(army, dict) or (
            controllable is not None
            and army.get("controllable") is not controllable
        ):
            continue
        row = {
            key: army.get(key)
            for key in (
                "army_id",
                "current_province_id",
                "soldiers",
                "move_target_province_id",
            )
        }
        for optional_flag in ("in_combat", "retreating"):
            if isinstance(army.get(optional_flag), bool):
                row[optional_flag] = army[optional_flag]
        for optional_state in ("army_state", "army_state_code"):
            if isinstance(army.get(optional_state), (str, int)) and not isinstance(
                army.get(optional_state), bool
            ):
                row[optional_state] = army[optional_state]
        if isinstance(army.get("route_province_ids"), list):
            row["route_province_ids"] = list(army["route_province_ids"])
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            int(row["army_id"])
            if isinstance(row.get("army_id"), int)
            and not isinstance(row.get("army_id"), bool)
            else 2**31 - 1
        ),
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


def _war_objective_capability_flags(
    capabilities: set[str],
) -> dict[str, bool]:
    return {
        "war_objective_occupation_supported": (
            WAR_OBJECTIVE_OCCUPATION_CAPABILITY in capabilities
        ),
        "war_objective_fort_level_supported": (
            WAR_OBJECTIVE_FORT_LEVEL_CAPABILITY in capabilities
        ),
        "war_objective_garrison_supported": (
            WAR_OBJECTIVE_GARRISON_CAPABILITY in capabilities
        ),
        "war_objective_siege_progress_supported": (
            WAR_OBJECTIVE_SIEGE_PROGRESS_CAPABILITY in capabilities
        ),
    }


def _action_steps(
    capabilities: list[str],
    active_event: object = None,
    pending_character_interaction: object = None,
    active_wars: object = None,
    player_armies: object = None,
    declarable_wars: object = None,
    arrange_marriage_choices: object = None,
) -> list[str]:
    steps: set[str] = set()
    war_primary_opponent_supported = (
        WAR_PRIMARY_OPPONENT_CAPABILITY in capabilities
    )
    war_objectives_supported = WAR_OBJECTIVES_CAPABILITY in capabilities
    expand_event_options = False
    pending_interaction_steps: set[str] = set()
    expand_move_armies = False
    expand_preview_move_armies = False
    expand_disband_armies = False
    expand_enforce_demands = False
    expand_declare_wars = False
    expand_arrange_marriage = False
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
        elif capability == PREVIEW_MOVE_ARMY_CAPABILITY:
            expand_preview_move_armies = True
        elif capability == DISBAND_ARMY_CAPABILITY:
            expand_disband_armies = True
        elif capability == ENFORCE_DEMANDS_CAPABILITY:
            expand_enforce_demands = True
        elif capability == DECLARE_WAR_CAPABILITY:
            expand_declare_wars = True
        elif capability == ARRANGE_MARRIAGE_CAPABILITY:
            expand_arrange_marriage = True
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
    if expand_enforce_demands:
        steps.update(
            enforce_demands_step(int(war["war_id"]))
            for war in wars
            if isinstance(war.get("war_id"), int)
            and (
                not war_primary_opponent_supported
                or (
                    war.get("player_is_primary_war_leader") is True
                    and isinstance(
                        war.get("player_relative_war_score"), int
                    )
                    and int(war["player_relative_war_score"]) >= 100
                )
            )
        )
    if expand_declare_wars and isinstance(declarable_wars, list):
        steps.update(
            declare_war_step(str(row["declaration_id"]))
            for row in declarable_wars
            if isinstance(row, dict)
            and isinstance(row.get("declaration_id"), str)
        )
    if expand_arrange_marriage and isinstance(arrange_marriage_choices, list):
        steps.update(
            arrange_marriage_step(str(row["choice_id"]))
            for row in arrange_marriage_choices
            if isinstance(row, dict) and isinstance(row.get("choice_id"), str)
        )
    if expand_disband_armies:
        steps.update(
            disband_army_step(int(army["army_id"]))
            for army in controllable
            if isinstance(army.get("army_id"), int)
        )
    if (expand_move_armies or expand_preview_move_armies) and wars:
        target_provinces = {
            int(army["current_province_id"])
            for army in enemy_armies_from_wars(wars)
            if isinstance(army.get("current_province_id"), int)
        }
        if war_primary_opponent_supported:
            target_provinces.update(
                enemy_primary_default_raise_province_ids(wars)
            )
        if war_objectives_supported:
            target_provinces.update(war_objective_province_ids(wars))
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
                if expand_move_armies:
                    steps.add(move_army_step(army_id, province_id))
                if expand_preview_move_armies:
                    steps.add(preview_move_army_step(army_id, province_id))
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


def _war_by_id(
    snapshot: dict[str, object], war_id: int
) -> dict[str, object] | None:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    return next(
        (
            war
            for war in wars
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )


def _army_move_postcondition(
    snapshot: dict[str, object],
    army_id: int,
    province_id: int,
    *,
    require_route: bool = False,
) -> str | None:
    army = _army_by_id(snapshot, army_id)
    if army is None:
        return "army_no_longer_present"
    if army.get("current_province_id") == province_id:
        return "arrived"
    if army.get("move_target_province_id") == province_id:
        if require_route:
            route = army.get("route_province_ids")
            if not isinstance(route, list) or not route or route[-1] != province_id:
                return None
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
    relationship_fields = {
        "betrothed_id",
        "primary_spouse_id",
        "spouse_ids",
    }
    if relationship_fields & value.keys():
        if not relationship_fields <= value.keys():
            raise ValueError(
                "native played_character relationship state is incomplete"
            )
        betrothed_id = value.get("betrothed_id")
        primary_spouse_id = value.get("primary_spouse_id")
        spouse_ids = value.get("spouse_ids")
        for name, related_id in (
            ("betrothed_id", betrothed_id),
            ("primary_spouse_id", primary_spouse_id),
        ):
            if related_id is not None and (
                isinstance(related_id, bool)
                or not isinstance(related_id, int)
                or related_id < 0
            ):
                raise ValueError(
                    f"native played_character {name} is malformed"
                )
        if not isinstance(spouse_ids, list) or any(
            isinstance(related_id, bool)
            or not isinstance(related_id, int)
            or related_id < 0
            for related_id in spouse_ids
        ):
            raise ValueError(
                "native played_character spouse_ids is malformed"
            )
        if len(set(spouse_ids)) != len(spouse_ids):
            raise ValueError(
                "native played_character spouse_ids contains duplicates"
            )
        if (
            primary_spouse_id is not None
            and primary_spouse_id not in spouse_ids
        ):
            raise ValueError(
                "native played_character primary_spouse_id is not a spouse"
            )
        result.update(
            {
                "betrothed_id": betrothed_id,
                "primary_spouse_id": primary_spouse_id,
                "spouse_ids": list(spouse_ids),
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
