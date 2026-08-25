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
from .combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    QUERY_COMBAT_SIMULATION_INPUTS_STEP_PREFIX,
    combat_simulation_encounter_scope,
    combat_simulation_inputs_status,
    normalize_combat_simulation_inputs,
    parse_query_combat_simulation_inputs_step,
)
from .combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX,
    combat_simulation_inputs_v3_status,
    normalize_combat_simulation_inputs_v3,
    parse_query_combat_simulation_inputs_v3_step,
)
from .war_exit_terms_contract import (
    QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY,
    QUERY_WAR_TERMINATION_EXIT_TERMS_STEP_PREFIX,
    WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED,
    normalize_war_termination_exit_terms,
    parse_query_war_termination_exit_terms_step,
    query_war_termination_exit_terms_step,
)
from .war_entry_contract import (
    QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
    QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX,
    normalize_war_entry_assessments,
    parse_query_war_entry_assessments_step,
    query_war_entry_assessments_step,
    require_declarable_war_targets,
)
from .actual_contact_contract import (
    QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY,
    QUERY_ACTUAL_CONTACT_SCOPE_STEP_PREFIX,
    normalize_actual_contact_scope,
    parse_query_actual_contact_scope_step,
    query_actual_contact_scope_step,
)
from .war_contract import (
    ARMY_ROUTES_CAPABILITY,
    DISBAND_ARMY_CAPABILITY,
    ENFORCE_DEMANDS_CAPABILITY,
    MERGE_ARMIES_CAPABILITY,
    MOVE_ARMY_CAPABILITY,
    OFFER_WHITE_PEACE_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
    QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
    QUERY_ARMY_STRENGTHS_CAPABILITY,
    QUERY_ARMY_STRENGTHS_STEP,
    QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
    QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
    RAISE_TROOPS_STEP,
    SPLIT_ARMY_HALF_CAPABILITY,
    START_ASSAULT_CAPABILITY,
    STOP_ASSAULT_CAPABILITY,
    SURRENDER_WAR_CAPABILITY,
    WAR_OBJECTIVES_CAPABILITY,
    WAR_OBJECTIVE_ASSAULT_CAPABILITY,
    WAR_OBJECTIVE_FORT_LEVEL_CAPABILITY,
    WAR_OBJECTIVE_GARRISON_CAPABILITY,
    WAR_OBJECTIVE_OCCUPATION_CAPABILITY,
    WAR_OBJECTIVE_SIEGE_PROGRESS_CAPABILITY,
    WAR_PRIMARY_OPPONENT_CAPABILITY,
    ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX,
    advance_route_contact_horizon_step,
    army_strength_query_status,
    army_strength_scope,
    controllable_armies,
    disband_army_step,
    enemy_primary_default_raise_province_ids,
    enforce_demands_step,
    enemy_armies_from_wars,
    is_native_war_step,
    is_life_advance_step,
    merge_armies_step,
    move_army_step,
    normalize_active_wars,
    normalize_army_strengths,
    normalize_route_contact_horizon,
    normalize_war_termination_options,
    normalize_war_termination_terms,
    parse_disband_army_step,
    parse_enforce_demands_step,
    parse_merge_armies_step,
    parse_move_army_step,
    parse_offer_white_peace_step,
    parse_preview_move_army_step,
    parse_advance_route_contact_horizon_step,
    parse_query_route_contact_horizon_step,
    parse_query_war_termination_options_step,
    parse_query_war_termination_terms_step,
    parse_split_army_half_step,
    parse_start_assault_step,
    parse_stop_assault_step,
    parse_surrender_war_step,
    preview_move_army_step,
    query_route_contact_horizon_step,
    player_armies_from_state,
    query_war_termination_options_step,
    query_war_termination_terms_step,
    split_army_half_step,
    start_assault_step,
    stop_assault_step,
    war_objective_province_ids,
)


PROTOCOL_VERSION = 1
MAXIMUM_FRAME_BYTES = 1024 * 1024
DEFAULT_PIPE_NAME = r"\\.\pipe\xar_ck3_bridge_mcp"
_ACTION_CAPABILITY_PREFIX = "game.command."
_NATIVE_LIFE_ADVANCE_PRIMITIVES = frozenset(
    {"set-speed-5", "resume-map", "pause-map"}
)
_NATIVE_EXACT_DAY_ADVANCE_PRIMITIVES = frozenset(
    {"set-speed-1", "resume-map", "pause-map"}
)
_CHECKPOINT_FILENAME = "xar_checkpoint.ck3"
_EPISODE_SEED_FILENAME = "xar_episode_seed.ck3"
_EPISODE_SEED_METADATA_FILENAME = "episode-seed.json"
_EPISODE_TRANSITION_FILENAME = "episode-transition.json"
_NATIVE_DEATH_TERMINAL_STEP = "death-terminal"
_NATIVE_SESSION_QUEUE_DIRNAME = "native-session"
_NATIVE_DRIVER_STATE_FILENAME = "driver-state.json"
_NATIVE_DRIVER_STATE_VERSION = 2
_MAX_ROLLBACK_WAR_FAILURES = 2
_ROLLBACK_WAR_FAILURE_COMPLETED_EPOCH_LIMIT = 2
_RESTORE_CHECKPOINT_STEP = "restore-checkpoint"
_MANAGED_RESTORE_TRANSACTION_STATUS = "awaiting_checkpoint_rebind"
_START_NEXT_EPISODE_STEP = "start-next-episode"
_COLD_RESTORE_SOURCE = "native-session-cold-start"
_RESTORE_MAP_STABLE_SECONDS = 0.5
_NATIVE_WAR_ADVANCE_MAX_DAYS = 30
_NATIVE_SIEGE_ADVANCE_MAX_DAYS = 7
_NATIVE_ASSAULT_ADVANCE_MAX_DAYS = 1
_NATIVE_ACTIVE_ROUTE_ADVANCE_MAX_DAYS = 1
_NATIVE_COMBAT_RETREAT_ADVANCE_MAX_DAYS = 1
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
                        paused=(
                            self._semantic_snapshot.get("paused")
                            if self._semantic_snapshot is not None
                            else None
                        ),
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
        self._rollback_war_failures: list[dict[str, object]] = []
        self._rollback_war_failures_migration_required = False
        self._managed_restore_transaction: dict[str, object] | None = None
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
        self._army_strength_query: dict[str, object] | None = None
        self._combat_simulation_inputs_query: dict[str, object] | None = None
        self._combat_simulation_inputs_v3_query: dict[str, object] | None = None
        self._war_entry_assessments_query: dict[str, object] | None = None
        self._war_termination_options: dict[int, dict[str, object]] = {}
        self._war_termination_terms: dict[int, dict[str, object]] = {}
        self._war_termination_exit_terms: dict[
            int, dict[str, object]
        ] = {}
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
        if (
            QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY in bridge_capabilities
            and _NATIVE_EXACT_DAY_ADVANCE_PRIMITIVES <= action_steps
            and isinstance(current_snapshot, dict)
        ):
            proof_steps = _fresh_route_contact_advance_steps(
                current_snapshot, self._history_snapshot()
            )
            action_steps.update(proof_steps)
            composite_action_steps.extend(sorted(proof_steps))
        if (
            QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY in bridge_capabilities
            and isinstance(current_snapshot, dict)
            and current_snapshot.get("paused") is True
        ):
            distinct_targets = list(
                dict.fromkeys(
                    int(row["target_character_id"])
                    for row in declarations
                    if isinstance(row.get("target_character_id"), int)
                    and not isinstance(row.get("target_character_id"), bool)
                    and 0 < int(row["target_character_id"]) <= 2**31 - 1
                )
            )
            action_steps.update(
                query_war_entry_assessments_step([target])
                for target in distinct_targets
            )
        # Native surrender and white-peace ABIs are intentionally not Python
        # actions yet. claim-disposition v1 is necessary but not sufficient:
        # dynamic exit terms and campaign-decision readiness remain required.
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
            "route_contact_horizon_supported": (
                QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY
                in bridge_capabilities
            ),
            "actual_contact_scope_query_supported": (
                QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY
                in bridge_capabilities
            ),
            "army_strength_query_supported": (
                QUERY_ARMY_STRENGTHS_CAPABILITY in bridge_capabilities
            ),
            "combat_simulation_inputs_query_supported": (
                QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
                in bridge_capabilities
            ),
            "combat_simulation_inputs_v3_query_supported": (
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
                in bridge_capabilities
            ),
            "war_entry_assessments_query_supported": (
                QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
                in bridge_capabilities
            ),
            "war_termination_query_supported": (
                QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY
                in bridge_capabilities
            ),
            "war_termination_terms_query_supported": (
                QUERY_WAR_TERMINATION_TERMS_CAPABILITY
                in bridge_capabilities
            ),
            "war_termination_exit_terms_query_supported": (
                WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED
                and QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY
                in bridge_capabilities
            ),
            "surrender_war_supported": (
                SURRENDER_WAR_CAPABILITY in bridge_capabilities
            ),
            "offer_white_peace_supported": (
                OFFER_WHITE_PEACE_CAPABILITY in bridge_capabilities
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
        with self._driver_state_lock:
            rollback_war_failures = copy.deepcopy(self._rollback_war_failures)
            rollback_war_failure = (
                copy.deepcopy(rollback_war_failures[0])
                if rollback_war_failures
                else None
            )
        return {
            **snapshot,
            "native_command_history": self._history_snapshot(),
            "native_rollback_war_failure": rollback_war_failure,
            "native_rollback_war_failures": rollback_war_failures,
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
        war_termination_options = self._war_termination_cache_for_snapshot(
            snapshot,
            episode_run_id=episode_run_id,
        )
        war_termination_terms = (
            self._war_termination_terms_cache_for_snapshot(
                snapshot,
                episode_run_id=episode_run_id,
            )
        )
        war_termination_exit_terms = (
            self._war_termination_exit_terms_cache_for_snapshot(
                snapshot,
                episode_run_id=episode_run_id,
            )
        )
        army_strength_query = self._army_strength_cache_for_snapshot(
            snapshot,
            episode_run_id=episode_run_id,
        )
        combat_simulation_inputs_query = (
            self._combat_simulation_inputs_cache_for_snapshot(
                snapshot,
                episode_run_id=episode_run_id,
            )
        )
        combat_simulation_inputs_v3_query = (
            self._combat_simulation_inputs_v3_cache_for_snapshot(
                snapshot,
                episode_run_id=episode_run_id,
            )
        )
        war_entry_assessments_query = (
            self._war_entry_assessments_cache_for_snapshot(
                {**snapshot, "declarable_wars": declarable_wars},
                episode_run_id=episode_run_id,
            )
        )
        if identity_changed:
            self._persist_driver_state()
        self._migrate_legacy_rollback_war_failures(snapshot)

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
            "route_contact_horizon_supported": (
                QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY
                in bridge_capabilities
            ),
            "actual_contact_scope_query_supported": (
                QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY
                in bridge_capabilities
            ),
            "combat_simulation_inputs_query_supported": (
                QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
                in bridge_capabilities
            ),
            "combat_simulation_inputs_v3_query_supported": (
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
                in bridge_capabilities
            ),
            "war_entry_assessments_query_supported": (
                QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
                in bridge_capabilities
            ),
            **_war_objective_capability_flags(bridge_capabilities),
            "declarable_wars": declarable_wars,
            "declaration_query_sequence": declaration_query_sequence,
            "arrange_marriage_choices": arrange_marriage_choices,
            "arrange_marriage_query_sequence": arrange_marriage_query_sequence,
            "army_strengths": (
                copy.deepcopy(army_strength_query["army_strengths"])
                if isinstance(army_strength_query, dict)
                else []
            ),
            "army_strengths_status": (
                army_strength_query.get("status")
                if isinstance(army_strength_query, dict)
                else None
            ),
            "army_strengths_query_sequence": (
                army_strength_query.get("query_sequence")
                if isinstance(army_strength_query, dict)
                else None
            ),
            "army_strengths_queried_snapshot_id": (
                army_strength_query.get("queried_snapshot_id")
                if isinstance(army_strength_query, dict)
                else None
            ),
            "army_strengths_queried_revision": (
                army_strength_query.get("queried_revision")
                if isinstance(army_strength_query, dict)
                else None
            ),
            "combat_simulation_inputs": (
                copy.deepcopy(
                    combat_simulation_inputs_query[
                        "combat_simulation_inputs"
                    ]
                )
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_status": (
                combat_simulation_inputs_query.get("status")
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_query_sequence": (
                combat_simulation_inputs_query.get("query_sequence")
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_target_province_id": (
                combat_simulation_inputs_query.get("target_province_id")
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_attacker_entry_province_id": (
                combat_simulation_inputs_query.get(
                    "attacker_entry_province_id"
                )
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_attacker_army_ids": (
                copy.deepcopy(
                    combat_simulation_inputs_query.get("attacker_army_ids")
                )
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_defender_army_ids": (
                copy.deepcopy(
                    combat_simulation_inputs_query.get("defender_army_ids")
                )
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_queried_snapshot_id": (
                combat_simulation_inputs_query.get("queried_snapshot_id")
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_queried_revision": (
                combat_simulation_inputs_query.get("queried_revision")
                if isinstance(combat_simulation_inputs_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3": (
                copy.deepcopy(
                    combat_simulation_inputs_v3_query[
                        "combat_simulation_inputs"
                    ]
                )
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_status": (
                combat_simulation_inputs_v3_query.get("status")
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_query_sequence": (
                combat_simulation_inputs_v3_query.get("query_sequence")
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_target_province_id": (
                combat_simulation_inputs_v3_query.get("target_province_id")
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_attacker_entry_province_id": (
                combat_simulation_inputs_v3_query.get(
                    "attacker_entry_province_id"
                )
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_attacker_army_ids": (
                copy.deepcopy(
                    combat_simulation_inputs_v3_query.get("attacker_army_ids")
                )
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_defender_army_ids": (
                copy.deepcopy(
                    combat_simulation_inputs_v3_query.get("defender_army_ids")
                )
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_queried_snapshot_id": (
                combat_simulation_inputs_v3_query.get("queried_snapshot_id")
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "combat_simulation_inputs_v3_queried_revision": (
                combat_simulation_inputs_v3_query.get("queried_revision")
                if isinstance(combat_simulation_inputs_v3_query, dict)
                else None
            ),
            "war_entry_assessments": (
                copy.deepcopy(
                    war_entry_assessments_query["war_entry_assessments"]
                )
                if isinstance(war_entry_assessments_query, dict)
                else None
            ),
            "war_entry_assessments_status": (
                war_entry_assessments_query.get("status")
                if isinstance(war_entry_assessments_query, dict)
                else None
            ),
            "war_entry_assessments_query_sequence": (
                war_entry_assessments_query.get("query_sequence")
                if isinstance(war_entry_assessments_query, dict)
                else None
            ),
            "war_entry_assessments_queried_snapshot_id": (
                war_entry_assessments_query.get("queried_snapshot_id")
                if isinstance(war_entry_assessments_query, dict)
                else None
            ),
            "war_entry_assessments_queried_revision": (
                war_entry_assessments_query.get("queried_revision")
                if isinstance(war_entry_assessments_query, dict)
                else None
            ),
            "war_termination_options": war_termination_options,
            "war_termination_terms": war_termination_terms,
            "war_termination_exit_terms": war_termination_exit_terms,
        }

    def _war_entry_assessments_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> dict[str, object] | None:
        """Project only a complete assessment bound to this paused frame."""
        if snapshot.get("paused") is not True:
            return None
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        played_character = snapshot.get("played_character")
        actor_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(actor_id, bool)
            or not isinstance(actor_id, int)
            or not 1 <= actor_id <= 2**31 - 1
        ):
            return None
        with self._driver_state_lock:
            cached = self._war_entry_assessments_query
            if not isinstance(cached, dict):
                return None
            binding = cached.get("cache_binding")
            query_sequence = cached.get("query_sequence")
            if not (
                set(cached)
                == {
                    "status",
                    "war_entry_assessments",
                    "query_sequence",
                    "cache_binding",
                }
                and isinstance(binding, dict)
                and set(binding)
                == {
                    "native_revision",
                    "snapshot_id",
                    "revision",
                    "connection_generation",
                    "episode_run_id",
                    "target_character_ids",
                }
                and binding.get("native_revision")
                == snapshot.get("native_revision")
                and binding.get("snapshot_id") == snapshot.get("snapshot_id")
                and binding.get("revision") == snapshot.get("revision")
                and binding.get("connection_generation")
                == connection_generation
                and binding.get("episode_run_id") == episode_run_id
                and cached.get("status") == "available"
                and isinstance(query_sequence, int)
                and not isinstance(query_sequence, bool)
                and 1 <= query_sequence <= 2**64 - 1
            ):
                self._war_entry_assessments_query = None
                return None
            targets = binding.get("target_character_ids")
            try:
                targets = require_declarable_war_targets(snapshot, targets)
                normalized = normalize_war_entry_assessments(
                    cached.get("war_entry_assessments"),
                    expected_target_character_ids=targets,
                    expected_actor_character_id=actor_id,
                    expected_snapshot_revision=snapshot.get("native_revision"),
                )
            except ValueError:
                self._war_entry_assessments_query = None
                return None
            return {
                "status": "available",
                "war_entry_assessments": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "queried_snapshot_id": snapshot.get("snapshot_id"),
                "queried_revision": snapshot.get("revision"),
                "queried_native_revision": snapshot.get("native_revision"),
                "episode_run_id": episode_run_id,
                "target_character_ids": list(targets),
            }

    def _army_strength_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> dict[str, object] | None:
        """Project only the complete query bound to this paused native frame."""
        if snapshot.get("paused") is not True:
            return None
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        with self._driver_state_lock:
            cached = self._army_strength_query
            if not isinstance(cached, dict):
                return None
            binding = cached.get("cache_binding")
            rows = cached.get("army_strengths")
            try:
                expected_scope = army_strength_scope(snapshot)
                normalized = normalize_army_strengths(
                    rows, expected_scope=expected_scope
                )
            except ValueError:
                self._army_strength_query = None
                return None
            if not (
                isinstance(binding, dict)
                and binding.get("native_revision")
                == snapshot.get("native_revision")
                and binding.get("snapshot_id") == snapshot.get("snapshot_id")
                and binding.get("connection_generation")
                == connection_generation
                and binding.get("episode_run_id") == episode_run_id
                and cached.get("status")
                == army_strength_query_status(normalized)
            ):
                self._army_strength_query = None
                return None
            return {
                "status": cached["status"],
                "army_strengths": copy.deepcopy(normalized),
                "query_sequence": cached["query_sequence"],
                "queried_snapshot_id": snapshot.get("snapshot_id"),
                "queried_revision": snapshot.get("revision"),
                "queried_native_revision": snapshot.get("native_revision"),
                "episode_run_id": episode_run_id,
            }

    def _war_termination_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> list[dict[str, object]]:
        """Project only queries bound to this exact paused native frame."""
        if snapshot.get("paused") is not True:
            return []
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        native_revision = snapshot.get("native_revision")
        snapshot_id = snapshot.get("snapshot_id")
        wars = snapshot.get("active_wars")
        wars_by_id = {
            int(war["war_id"]): war
            for war in (wars if isinstance(wars, list) else [])
            if isinstance(war, dict)
            and _positive_native_id(war.get("war_id"))
        }
        result: list[dict[str, object]] = []
        stale_ids: list[int] = []
        with self._driver_state_lock:
            for war_id, cached in self._war_termination_options.items():
                binding = cached.get("cache_binding")
                options = cached.get("options")
                war = wars_by_id.get(war_id)
                if not (
                    isinstance(binding, dict)
                    and isinstance(options, dict)
                    and isinstance(war, dict)
                    and binding.get("native_revision") == native_revision
                    and binding.get("snapshot_id") == snapshot_id
                    and binding.get("connection_generation")
                    == connection_generation
                    and binding.get("episode_run_id") == episode_run_id
                    and options.get("player_side") == war.get("player_side")
                    and options.get("player_is_primary_war_leader")
                    == war.get("player_is_primary_war_leader")
                    and options.get("player_relative_war_score")
                    == war.get("player_relative_war_score")
                ):
                    stale_ids.append(war_id)
                    continue
                result.append(
                    {
                        **copy.deepcopy(options),
                        "query_sequence": cached["query_sequence"],
                        "queried_snapshot_id": snapshot_id,
                        "queried_revision": snapshot.get("revision"),
                        "queried_native_revision": native_revision,
                        "episode_run_id": episode_run_id,
                    }
                )
            for war_id in stale_ids:
                self._war_termination_options.pop(war_id, None)
        return sorted(result, key=lambda row: int(row["war_id"]))

    def _war_termination_terms_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> list[dict[str, object]]:
        """Project claim terms only on their exact paused native frame."""
        if snapshot.get("paused") is not True:
            return []
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        native_revision = snapshot.get("native_revision")
        snapshot_id = snapshot.get("snapshot_id")
        wars = snapshot.get("active_wars")
        active_war_ids = {
            int(war["war_id"])
            for war in (wars if isinstance(wars, list) else [])
            if isinstance(war, dict)
            and _positive_native_id(war.get("war_id"))
        }
        result: list[dict[str, object]] = []
        stale_ids: list[int] = []
        with self._driver_state_lock:
            for war_id, cached in self._war_termination_terms.items():
                binding = cached.get("cache_binding")
                terms = cached.get("terms")
                if not (
                    isinstance(binding, dict)
                    and isinstance(terms, dict)
                    and war_id in active_war_ids
                    and binding.get("native_revision") == native_revision
                    and binding.get("snapshot_id") == snapshot_id
                    and binding.get("connection_generation")
                    == connection_generation
                    and binding.get("episode_run_id") == episode_run_id
                    and terms.get("war_id") == war_id
                ):
                    stale_ids.append(war_id)
                    continue
                result.append(
                    {
                        **copy.deepcopy(terms),
                        "query_sequence": cached["query_sequence"],
                        "queried_snapshot_id": snapshot_id,
                        "queried_revision": snapshot.get("revision"),
                        "queried_native_revision": native_revision,
                        "episode_run_id": episode_run_id,
                    }
                )
            for war_id in stale_ids:
                self._war_termination_terms.pop(war_id, None)
        return sorted(result, key=lambda row: int(row["war_id"]))

    def _war_termination_exit_terms_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> list[dict[str, object]]:
        """Project complete v2 exit terms only on their exact paused frame."""
        if snapshot.get("paused") is not True:
            return []
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        binding_values = {
            "native_revision": snapshot.get("native_revision"),
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "connection_generation": connection_generation,
            "episode_run_id": episode_run_id,
        }
        wars = snapshot.get("active_wars")
        active_war_ids = {
            int(war["war_id"])
            for war in (wars if isinstance(wars, list) else [])
            if isinstance(war, dict)
            and _positive_native_id(war.get("war_id"))
        }
        result: list[dict[str, object]] = []
        stale_ids: list[int] = []
        with self._driver_state_lock:
            for war_id, cached in self._war_termination_exit_terms.items():
                binding = cached.get("cache_binding")
                terms = cached.get("terms")
                if not (
                    isinstance(binding, dict)
                    and binding == binding_values
                    and isinstance(terms, dict)
                    and war_id in active_war_ids
                    and terms.get("war_id") == war_id
                ):
                    stale_ids.append(war_id)
                    continue
                result.append(
                    {
                        **copy.deepcopy(terms),
                        "query_sequence": cached["query_sequence"],
                        "queried_snapshot_id": binding_values["snapshot_id"],
                        "queried_revision": binding_values["revision"],
                        "queried_native_revision": binding_values[
                            "native_revision"
                        ],
                        "episode_run_id": episode_run_id,
                    }
                )
            for war_id in stale_ids:
                self._war_termination_exit_terms.pop(war_id, None)
        return sorted(result, key=lambda row: int(row["war_id"]))

    def _combat_simulation_inputs_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> dict[str, object] | None:
        """Project one hypothetical-contact query bound to this paused frame."""
        if snapshot.get("paused") is not True:
            return None
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        with self._driver_state_lock:
            cached = self._combat_simulation_inputs_query
            if not isinstance(cached, dict):
                return None
            binding = cached.get("cache_binding")
            query_sequence = cached.get("query_sequence")
            if not (
                set(cached)
                == {
                    "status",
                    "combat_simulation_inputs",
                    "query_sequence",
                    "cache_binding",
                }
                and isinstance(binding, dict)
                and set(binding)
                == {
                    "native_revision",
                    "snapshot_id",
                    "revision",
                    "connection_generation",
                    "episode_run_id",
                    "target_province_id",
                    "attacker_entry_province_id",
                    "attacker_army_ids",
                    "defender_army_ids",
                }
                and isinstance(query_sequence, int)
                and not isinstance(query_sequence, bool)
                and 1 <= query_sequence <= 2**64 - 1
            ):
                self._combat_simulation_inputs_query = None
                return None
            target_province_id = binding.get("target_province_id")
            attacker_entry_province_id = binding.get(
                "attacker_entry_province_id"
            )
            attacker_army_ids = binding.get("attacker_army_ids")
            defender_army_ids = binding.get("defender_army_ids")
            try:
                encounter_scope = combat_simulation_encounter_scope(
                    snapshot, attacker_army_ids, defender_army_ids
                )
                normalized = normalize_combat_simulation_inputs(
                    cached.get("combat_simulation_inputs"),
                    expected_target_province_id=int(target_province_id),
                    expected_attacker_entry_province_id=int(
                        attacker_entry_province_id
                    ),
                    expected_encounter_scope=encounter_scope,
                )
                status = combat_simulation_inputs_status(normalized)
            except (TypeError, ValueError):
                self._combat_simulation_inputs_query = None
                return None
            if not (
                binding.get("native_revision")
                == snapshot.get("native_revision")
                and binding.get("snapshot_id") == snapshot.get("snapshot_id")
                and binding.get("revision") == snapshot.get("revision")
                and binding.get("connection_generation")
                == connection_generation
                and binding.get("episode_run_id") == episode_run_id
                and binding.get("target_province_id")
                == normalized.get("target_province_id")
                and binding.get("attacker_army_ids")
                == encounter_scope.get("attacker_army_ids")
                and binding.get("defender_army_ids")
                == encounter_scope.get("defender_army_ids")
                and cached.get("status") == status
            ):
                self._combat_simulation_inputs_query = None
                return None
            return {
                "status": status,
                "combat_simulation_inputs": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "target_province_id": target_province_id,
                "attacker_entry_province_id": (
                    attacker_entry_province_id
                ),
                "attacker_army_ids": copy.deepcopy(attacker_army_ids),
                "defender_army_ids": copy.deepcopy(defender_army_ids),
                "queried_snapshot_id": snapshot.get("snapshot_id"),
                "queried_revision": snapshot.get("revision"),
                "queried_native_revision": snapshot.get("native_revision"),
                "episode_run_id": episode_run_id,
            }

    def _combat_simulation_inputs_v3_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> dict[str, object] | None:
        """Project only an atomic production-v3 slice from this paused frame."""
        if snapshot.get("paused") is not True:
            return None
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        with self._driver_state_lock:
            cached = self._combat_simulation_inputs_v3_query
            if not isinstance(cached, dict):
                return None
            binding = cached.get("cache_binding")
            query_sequence = cached.get("query_sequence")
            if not (
                set(cached)
                == {
                    "status",
                    "combat_simulation_inputs",
                    "query_sequence",
                    "cache_binding",
                }
                and isinstance(binding, dict)
                and set(binding)
                == {
                    "native_revision",
                    "snapshot_id",
                    "revision",
                    "connection_generation",
                    "episode_run_id",
                    "target_province_id",
                    "attacker_entry_province_id",
                    "attacker_army_ids",
                    "defender_army_ids",
                }
                and isinstance(query_sequence, int)
                and not isinstance(query_sequence, bool)
                and 1 <= query_sequence <= 2**64 - 1
            ):
                self._combat_simulation_inputs_v3_query = None
                return None
            target_province_id = binding.get("target_province_id")
            attacker_entry_province_id = binding.get(
                "attacker_entry_province_id"
            )
            attacker_army_ids = binding.get("attacker_army_ids")
            defender_army_ids = binding.get("defender_army_ids")
            try:
                encounter_scope = combat_simulation_encounter_scope(
                    snapshot, attacker_army_ids, defender_army_ids
                )
                normalized = normalize_combat_simulation_inputs_v3(
                    cached.get("combat_simulation_inputs"),
                    expected_target_province_id=int(target_province_id),
                    expected_attacker_entry_province_id=int(
                        attacker_entry_province_id
                    ),
                    expected_encounter_scope=encounter_scope,
                )
                status = combat_simulation_inputs_v3_status(normalized)
            except (TypeError, ValueError):
                self._combat_simulation_inputs_v3_query = None
                return None
            if not (
                binding.get("native_revision")
                == snapshot.get("native_revision")
                and binding.get("snapshot_id") == snapshot.get("snapshot_id")
                and binding.get("revision") == snapshot.get("revision")
                and binding.get("connection_generation")
                == connection_generation
                and binding.get("episode_run_id") == episode_run_id
                and binding.get("target_province_id")
                == normalized["base_inputs"].get("target_province_id")
                and binding.get("attacker_army_ids")
                == encounter_scope.get("attacker_army_ids")
                and binding.get("defender_army_ids")
                == encounter_scope.get("defender_army_ids")
                and cached.get("status") == status
            ):
                self._combat_simulation_inputs_v3_query = None
                return None
            return {
                "status": status,
                "combat_simulation_inputs": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "target_province_id": target_province_id,
                "attacker_entry_province_id": attacker_entry_province_id,
                "attacker_army_ids": copy.deepcopy(attacker_army_ids),
                "defender_army_ids": copy.deepcopy(defender_army_ids),
                "queried_snapshot_id": snapshot.get("snapshot_id"),
                "queried_revision": snapshot.get("revision"),
                "queried_native_revision": snapshot.get("native_revision"),
                "episode_run_id": episode_run_id,
            }

    def _migrate_legacy_rollback_war_failures(
        self, snapshot: dict[str, object]
    ) -> None:
        """Finish a missing-plural v2 migration at the first exact frame."""
        with self._driver_state_lock:
            if (
                not self._rollback_war_failures_migration_required
                or self._pending_cold_candidate is not None
                or snapshot.get("map_ready") is not True
            ):
                return
            completed = _derive_completed_rollback_war_failures(
                self._command_history,
                checkpoint=self._last_checkpoint,
                restored_snapshot=snapshot,
                episode_run_id=self._episode_run_id,
                completed_restore_epoch_limit=(
                    _ROLLBACK_WAR_FAILURE_COMPLETED_EPOCH_LIMIT
                ),
            )
            self._rollback_war_failures = _bounded_rollback_war_failures(
                self._rollback_war_failures, completed
            )
            self._rollback_war_failures_migration_required = False
        self._persist_driver_state()

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
        life_advance_starting: dict[str, object] | None = None
        if step == "life-advance":
            # Bind the caller's revision before capability projection.  A
            # loading -> map_ready snapshot can arrive while capabilities()
            # is being assembled; that is an internal readiness transition,
            # not permission to accept an already-stale paused-map request.
            try:
                life_advance_starting = self.take_snapshot()
            except UnsupportedStepError:
                # Preserve the ordinary unsupported-composite result below
                # when this bridge never advertised snapshot state.
                life_advance_starting = None
            if (
                life_advance_starting is not None
                and expected_revision is not None
            ):
                _validate_revision(expected_revision, "expected_revision")
                current_revision = int(life_advance_starting["revision"])
                if expected_revision != current_revision:
                    raise BridgeUnavailableError(
                        "native life-advance revision mismatch: "
                        f"expected {expected_revision}, current "
                        f"{current_revision}"
                    )
        actual_contact_query = parse_query_actual_contact_scope_step(step)
        if (
            isinstance(step, str)
            and step.startswith(QUERY_ACTUAL_CONTACT_SCOPE_STEP_PREFIX)
            and actual_contact_query is None
        ):
            raise UnsupportedStepError(
                "malformed actual-contact scope query step"
            )
        route_contact_query = parse_query_route_contact_horizon_step(step)
        route_contact_advance = parse_advance_route_contact_horizon_step(step)
        if (
            isinstance(step, str)
            and step.startswith("query-route-contact-horizon-v1-")
            and route_contact_query is None
        ):
            raise UnsupportedStepError(
                "malformed or incomplete route-contact horizon step"
            )
        if (
            isinstance(step, str)
            and step.startswith(ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX)
            and route_contact_advance is None
        ):
            raise UnsupportedStepError(
                "malformed or incomplete route-contact horizon advance step"
            )
        war_entry_targets = parse_query_war_entry_assessments_step(step)
        if (
            isinstance(step, str)
            and step.startswith(QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX)
            and war_entry_targets is None
        ):
            raise UnsupportedStepError(
                "malformed or non-production-bounded war-entry assessment "
                "step"
            )
        capabilities = self.capabilities()
        if actual_contact_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the actual contact scope"
                )
            return self._execute_native_war_step(
                step, expected_revision=expected_revision
            )
        if war_entry_targets is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query strategic war-entry assessments"
                )
            return self._execute_war_entry_assessments_query(
                step,
                expected_revision=expected_revision,
            )
        combat_v3_query = parse_query_combat_simulation_inputs_v3_step(step)
        if combat_v3_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query production combat phase inputs"
                )
            return self._execute_combat_simulation_inputs_v3_query(
                step,
                expected_revision=expected_revision,
            )
        combat_query = parse_query_combat_simulation_inputs_step(step)
        if combat_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query combat simulation inputs"
                )
            return self._execute_combat_simulation_inputs_query(
                step,
                expected_revision=expected_revision,
            )
        exit_terms_query_war_id = (
            parse_query_war_termination_exit_terms_step(step)
        )
        if exit_terms_query_war_id is not None:
            if not WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED:
                raise UnsupportedStepError(
                    "native exit-terms v2 is disabled after the reproducible "
                    "loaded-effect preview crash at CK3 RVA 0x334C668"
                )
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query structured termination exit terms"
                )
            return self._execute_native_war_step(
                step, expected_revision=expected_revision
            )
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
        if parse_offer_white_peace_step(step) is not None:
            raise BridgeUnavailableError(
                "native white_peace submission requires "
                "structured_terms_v2 and campaign decision readiness"
            )
        if parse_surrender_war_step(step) is not None:
            raise BridgeUnavailableError(
                "native surrender submission requires structured_terms_v2 "
                "and campaign decision readiness"
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
        if route_contact_advance is not None:
            if step not in capabilities.get("composite_action_steps", []):
                raise UnsupportedStepError(
                    "route-contact one-day advance lacks a fresh native proof"
                )
            return self._execute_route_contact_horizon_advance(
                step, expected_revision=expected_revision
            )
        if step in capabilities.get("composite_action_steps", []):
            if step == "life-advance":
                return self._execute_life_advance(
                    expected_revision=expected_revision,
                    starting_snapshot=life_advance_starting,
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
            if step == _RESTORE_CHECKPOINT_STEP:
                if ok:
                    history_index = _checkpoint_history_index(
                        self._last_checkpoint, self._command_history
                    )
                    if history_index is not None:
                        self._command_history = self._command_history[
                            :history_index
                        ]
                    self._managed_restore_transaction = None
                elif (
                    isinstance(self._managed_restore_transaction, dict)
                    and self._managed_restore_transaction.get(
                        "replacement_bridge_pid"
                    )
                    is None
                    and self._pending_cold_candidate is None
                ):
                    # A pre-relaunch failure leaves the original CK3 process
                    # and factual branch authoritative.  Disarm the marker so
                    # the next ordinary hello is not held for reconciliation.
                    self._managed_restore_transaction = None
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
            self._rollback_war_failures = []
            self._rollback_war_failures_migration_required = False
            self._managed_restore_transaction = None
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
            self._army_strength_query = None
            self._combat_simulation_inputs_query = None
            self._combat_simulation_inputs_v3_query = None
            self._war_entry_assessments_query = None
            self._war_termination_options = {}
            self._war_termination_terms = {}
            self._war_termination_exit_terms = {}
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

    def _driver_state_payload_locked(self) -> dict[str, object]:
        rollback_war_failures = copy.deepcopy(self._rollback_war_failures)
        payload = {
            "format_version": _NATIVE_DRIVER_STATE_VERSION,
            "pipe_name": self.pipe_name,
            "bridge_pid": self._session_bridge_pid,
            "episode_character_id": self._episode_character_id,
            "episode_run_id": self._episode_run_id,
            "last_checkpoint": copy.deepcopy(self._last_checkpoint),
            "command_history": copy.deepcopy(self._command_history),
            # Singular stays as the latest advisory for old readers.
            "rollback_war_failure": (
                copy.deepcopy(rollback_war_failures[0])
                if rollback_war_failures
                else None
            ),
            "managed_restore_transaction": copy.deepcopy(
                self._managed_restore_transaction
            ),
        }
        # Keep an old-state migration recognizable across a crash before the
        # first playable snapshot supplies the restored physical origin.
        if not self._rollback_war_failures_migration_required:
            payload["rollback_war_failures"] = rollback_war_failures
        return payload

    def _managed_restore_request_state(
        self, transaction: dict[str, object]
    ) -> str:
        request_id = transaction.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            return "missing"
        queue_dir = self._native_session_queue_dir()
        inbox_path = queue_dir / "inbox" / f"{request_id}.json"
        outbox_path = queue_dir / "outbox" / f"{request_id}.json"
        if outbox_path.is_file():
            try:
                response = json.loads(
                    outbox_path.read_text(encoding="utf-8-sig")
                )
            except (OSError, UnicodeError, json.JSONDecodeError):
                return "present"
            if (
                isinstance(response, dict)
                and response.get("request_id") == request_id
                and response.get("ok") is False
            ):
                return "failed"
            return "present"
        return "present" if inbox_path.is_file() else "missing"

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
                self._rollback_war_failures = []
                self._rollback_war_failures_migration_required = False
                self._managed_restore_transaction = None
                self._driver_state_restored = False
                self._driver_state_restore_kind = None
                self._episode_binding_state = "unbound"
                self._pending_cold_candidate = None
                self._cold_candidate_rejection = None
                restored_transaction = (
                    restored.get("managed_restore_transaction")
                    if isinstance(restored, dict)
                    else None
                )
                transaction_crossed_process = bool(
                    isinstance(restored_transaction, dict)
                    and (
                        restored_transaction.get("replacement_bridge_pid")
                        == bridge_pid
                        or restored_transaction.get("source_bridge_pid")
                        != bridge_pid
                    )
                )
                if (
                    restored is not None
                    and restored.get("bridge_pid") == bridge_pid
                    and not transaction_crossed_process
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
                    self._rollback_war_failures = copy.deepcopy(
                        restored.get("rollback_war_failures", [])
                    )
                    self._rollback_war_failures_migration_required = bool(
                        restored.get(
                            "rollback_war_failures_migration_required"
                        )
                    )
                    self._managed_restore_transaction = copy.deepcopy(
                        restored_transaction
                    )
                    if (
                        isinstance(self._managed_restore_transaction, dict)
                        and self._managed_restore_transaction.get(
                            "replacement_bridge_pid"
                        )
                        is None
                        and self._managed_restore_request_state(
                            self._managed_restore_transaction
                        )
                        in {"missing", "failed"}
                    ):
                        # The daemon may have died after persisting the marker
                        # but before publishing the lifecycle request.  With
                        # the original PID still authoritative, a missing (or
                        # terminally failed) request disarms that orphan.
                        self._managed_restore_transaction = None
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
                    self._managed_restore_transaction = copy.deepcopy(
                        restored_transaction
                    )
                    self._episode_binding_state = "pending_cold_candidate"
                elif restored is not None:
                    self._cold_candidate_rejection = "no_complete_checkpoint_anchor"
            # A managed restore transaction turns the replacement hello into
            # the same cold checkpoint rebind used after a daemon restart.
            # Persist the marker with the new PID before the first playable
            # snapshot so a crash here cannot revive the discarded branch as
            # same-PID factual history.
            if (
                not first_connection
                and self._episode_transition is None
                and isinstance(self._managed_restore_transaction, dict)
                and self._managed_restore_transaction.get(
                    "source_bridge_pid"
                )
                != bridge_pid
            ):
                self._managed_restore_transaction[
                    "replacement_bridge_pid"
                ] = bridge_pid
                candidate = self._driver_state_payload_locked()
                if self._cold_candidate_ready(candidate):
                    self._pending_cold_candidate = candidate
                    self._episode_binding_state = "pending_cold_candidate"
                    self._driver_state_restore_kind = (
                        "managed_restore_checkpoint_rebind"
                    )
                else:
                    self._cold_candidate_rejection = (
                        "no_complete_checkpoint_anchor"
                    )
                should_persist = True

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
            self._army_strength_query = None
            self._combat_simulation_inputs_query = None
            self._combat_simulation_inputs_v3_query = None
            self._war_entry_assessments_query = None
            self._war_termination_options = {}
            self._war_termination_terms = {}
            self._war_termination_exit_terms = {}
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
                rollback_war_failure = _derive_rollback_war_failure(
                    candidate["command_history"],
                    checkpoint=checkpoint,
                    restored_snapshot=snapshot,
                    episode_run_id=str(candidate["episode_run_id"]),
                )
                completed_failures = (
                    _derive_completed_rollback_war_failures(
                        candidate["command_history"],
                        checkpoint=checkpoint,
                        restored_snapshot=snapshot,
                        episode_run_id=str(candidate["episode_run_id"]),
                        completed_restore_epoch_limit=(
                            _ROLLBACK_WAR_FAILURE_COMPLETED_EPOCH_LIMIT
                        ),
                    )
                    if candidate.get(
                        "rollback_war_failures_migration_required"
                    )
                    else []
                )
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
                self._rollback_war_failures = _bounded_rollback_war_failures(
                    [rollback_war_failure],
                    candidate.get("rollback_war_failures"),
                    completed_failures,
                )
                self._rollback_war_failures_migration_required = False
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
                self._rollback_war_failures = []
                self._rollback_war_failures_migration_required = False
                self._driver_state_restored = False
                self._driver_state_restore_kind = "new_episode"
                self._episode_binding_state = "active_new"
                self._cold_candidate_rejection = rejection
            self._pending_cold_candidate = None
            self._managed_restore_transaction = None
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
            plural_present = "rollback_war_failures" in payload
            persisted_plural = payload.get("rollback_war_failures")
            if plural_present and not isinstance(persisted_plural, list):
                raise ValueError(
                    "driver state rollback_war_failures is malformed"
                )
            singular_failure = _normalize_rollback_war_failure(
                payload.get("rollback_war_failure")
            )
            rollback_war_failures = _bounded_rollback_war_failures(
                persisted_plural if plural_present else [singular_failure]
            )
            rollback_war_failures = [
                failure
                for failure in rollback_war_failures
                if isinstance(last_checkpoint, dict)
                and failure.get("checkpoint_sha256")
                == last_checkpoint.get("sha256")
                and failure.get("episode_run_id") == run_id
            ]
            migration_required = bool(
                not plural_present
                and isinstance(last_checkpoint, dict)
                and isinstance(run_id, str)
                and run_id
            )
            if migration_required and rollback_war_failures:
                # A valid v2 singular is the newest seed.  Its exact scope is
                # enough to inspect any completed restore epochs that still
                # survive in this compatible state.  Once old factual rows
                # have already been truncated, this scan cannot reconstruct
                # them.  It never reaches an arbitrary third-or-older epoch.
                scope_snapshot = _rollback_war_failure_scope_snapshot(
                    rollback_war_failures[0]
                )
                completed = _derive_completed_rollback_war_failures(
                    history,
                    checkpoint=last_checkpoint,
                    restored_snapshot=scope_snapshot,
                    episode_run_id=run_id,
                    completed_restore_epoch_limit=(
                        _ROLLBACK_WAR_FAILURE_COMPLETED_EPOCH_LIMIT
                    ),
                )
                rollback_war_failures = _bounded_rollback_war_failures(
                    rollback_war_failures, completed
                )
                migration_required = False
            managed_restore_transaction = (
                _normalize_managed_restore_transaction(
                    payload.get("managed_restore_transaction"),
                    checkpoint=last_checkpoint,
                    history=history,
                    bridge_pid=persisted_bridge_pid,
                    episode_character_id=character_id,
                    episode_run_id=run_id,
                )
            )
            return {
                "format_version": format_version,
                "bridge_pid": persisted_bridge_pid,
                "episode_character_id": character_id,
                "episode_run_id": run_id,
                "command_history": copy.deepcopy(history),
                "last_checkpoint": copy.deepcopy(last_checkpoint),
                "rollback_war_failure": (
                    copy.deepcopy(rollback_war_failures[0])
                    if rollback_war_failures
                    else None
                ),
                "rollback_war_failures": copy.deepcopy(
                    rollback_war_failures
                ),
                "rollback_war_failures_migration_required": (
                    migration_required
                ),
                "managed_restore_transaction": managed_restore_transaction,
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
            payload = self._driver_state_payload_locked()
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
        self,
        step: str,
        *,
        expected_revision: int | None = None,
        required_capability: str | None = None,
    ) -> dict[str, object]:
        if not isinstance(step, str) or not step:
            raise ValueError("step must be a non-empty string")
        capabilities = self.capabilities()
        if required_capability is None:
            if step not in capabilities["action_steps"]:
                raise UnsupportedStepError(
                    f"native DLL does not implement gameplay step {step}"
                )
        elif required_capability not in set(
            _string_list(capabilities.get("bridge_capabilities"))
        ):
            raise UnsupportedStepError(
                "native DLL does not advertise required capability "
                f"{required_capability}"
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
            # A new save anchor starts a new rollback scope even if CK3 emits
            # byte-identical checkpoint contents at the same date.
            self._rollback_war_failures = []
            self._rollback_war_failures_migration_required = False
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
        if step == QUERY_ARMY_STRENGTHS_STEP:
            return self._execute_army_strength_query(
                starting=starting,
                selected_revision=selected_revision,
            )
        actual_contact_query = parse_query_actual_contact_scope_step(step)
        if actual_contact_query is not None:
            subject_army_id, target_province_id = actual_contact_query
            if starting.get("paused") is not True:
                raise BridgeUnavailableError(
                    "native actual-contact query requires a paused map"
                )
            subject = _army_by_id(starting, subject_army_id)
            if not (
                isinstance(subject, dict)
                and subject.get("controllable") is True
                and subject.get("current_province_id") == target_province_id
            ):
                raise BridgeUnavailableError(
                    "native actual-contact subject is not a controllable "
                    "army at the requested Province"
                )
            date_raw = _date_raw(starting, "actual-contact starting snapshot")
            native_revision = starting.get("native_revision")
            if (
                isinstance(native_revision, bool)
                or not isinstance(native_revision, int)
                or not 1 <= native_revision <= 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "native actual-contact query lacks a native revision"
                )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            if (
                set(result)
                != {
                    "step",
                    "accepted",
                    "status",
                    "query_sequence",
                    "snapshot_revision",
                    "actual_contact_scope",
                    "backend_id",
                }
                or result.get("step") != step
                or result.get("accepted") is not True
                or result.get("status") != "available"
                or result.get("snapshot_revision") != native_revision
            ):
                raise BridgeUnavailableError(
                    "native actual-contact query returned malformed status"
                )
            query_sequence = result.get("query_sequence")
            if (
                isinstance(query_sequence, bool)
                or not isinstance(query_sequence, int)
                or not 1 <= query_sequence <= 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "native actual-contact query lacks query_sequence"
                )
            try:
                scope = normalize_actual_contact_scope(
                    result.get("actual_contact_scope"),
                    expected_subject_army_id=subject_army_id,
                    expected_target_province_id=target_province_id,
                    expected_date_raw=date_raw,
                    expected_snapshot_revision=native_revision,
                )
            except ValueError as error:
                raise BridgeUnavailableError(str(error)) from error
            current = self.take_snapshot()
            if not _same_paused_native_frame(starting, current):
                raise BridgeUnavailableError(
                    "native actual-contact query crossed a snapshot revision"
                )
            return {
                **result,
                "actual_contact_scope": scope,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": native_revision,
                "queried_connection_generation": (
                    starting.get("diagnostics", {}).get(
                        "connection_generation"
                    )
                    if isinstance(starting.get("diagnostics"), dict)
                    else None
                ),
                "queried_episode_run_id": starting.get("episode_run_id"),
            }
        termination_query_war_id = (
            parse_query_war_termination_options_step(step)
        )
        termination_terms_query_war_id = (
            parse_query_war_termination_terms_step(step)
        )
        exit_terms_query_war_id = (
            parse_query_war_termination_exit_terms_step(step)
        )
        if exit_terms_query_war_id is not None:
            if not WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED:
                raise UnsupportedStepError(
                    "native exit-terms v2 production dispatch is disabled"
                )
            return self._execute_war_termination_exit_terms_query(
                step,
                starting=starting,
                selected_revision=selected_revision,
                war_id=exit_terms_query_war_id,
            )
        if termination_terms_query_war_id is not None:
            return self._execute_war_termination_terms_query(
                step,
                starting=starting,
                selected_revision=selected_revision,
                war_id=termination_terms_query_war_id,
            )
        surrender_war_id = parse_surrender_war_step(step)
        white_peace_war_id = parse_offer_white_peace_step(step)
        if (
            termination_query_war_id is not None
            or surrender_war_id is not None
            or white_peace_war_id is not None
        ):
            return self._execute_war_termination_step(
                step,
                starting=starting,
                selected_revision=selected_revision,
                query_war_id=termination_query_war_id,
                surrender_war_id=surrender_war_id,
                white_peace_war_id=white_peace_war_id,
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

        start_siege_id = parse_start_assault_step(step)
        stop_siege_id = parse_stop_assault_step(step)
        if start_siege_id is not None or stop_siege_id is not None:
            starting_siege_id = (
                start_siege_id
                if start_siege_id is not None
                else stop_siege_id
            )
            assert starting_siege_id is not None
            if starting.get("paused") is not True:
                raise BridgeUnavailableError(
                    "native assault command requires a paused snapshot"
                )
            if starting.get("war_objective_assault_supported") is not True:
                raise BridgeUnavailableError(
                    "native assault command requires the exact assault state "
                    "capability"
                )
            observation = _assault_siege_observation(
                starting, siege_id=starting_siege_id
            )
            if observation is None:
                raise BridgeUnavailableError(
                    f"native assault command requires observable SiegeID "
                    f"{starting_siege_id}"
                )
            active_siege = observation["active_siege"]
            starting_active = active_siege.get("assault_in_progress")
            is_start = start_siege_id is not None
            if is_start and not (
                starting_active is False
                and active_siege.get("can_start_assault") is True
            ):
                raise BridgeUnavailableError(
                    f"native start-assault-{starting_siege_id} is not "
                    "eligible in the paused snapshot"
                )
            if not is_start and not (
                starting_active is True
                and active_siege.get("can_stop_assault") is True
            ):
                raise BridgeUnavailableError(
                    f"native stop-assault-{starting_siege_id} is not "
                    "eligible in the paused snapshot"
                )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            expected_submission_status = (
                "start_submitted" if is_start else "stop_submitted"
            )
            if result.get("status") != expected_submission_status:
                raise BridgeUnavailableError(
                    f"native {step} returned malformed submission status"
                )
            expected_active = is_start
            war_id = int(observation["war_id"])
            province_id = int(observation["province_id"])
            changed = self._wait_for_snapshot(
                self.take_snapshot(),
                lambda snapshot: (
                    snapshot.get("paused") is True
                    and (
                        observed := _assault_siege_observation(
                            snapshot,
                            siege_id=starting_siege_id,
                            war_id=war_id,
                            province_id=province_id,
                        )
                    )
                    is not None
                    and observed["active_siege"].get(
                        "assault_in_progress"
                    )
                    is expected_active
                ),
                timeout_seconds=self.command_timeout_seconds,
            )
            applied = _assault_siege_observation(
                changed,
                siege_id=starting_siege_id,
                war_id=war_id,
                province_id=province_id,
            )
            if not (
                changed.get("paused") is True
                and isinstance(applied, dict)
                and applied["active_siege"].get("assault_in_progress")
                is expected_active
            ):
                raise BridgeUnavailableError(
                    f"native {step} did not expose its same-SiegeID paused "
                    "postcondition"
                )
            action_status = "assault_started" if is_start else "assault_stopped"
            assault_action = {
                "status": action_status,
                "submission_status": expected_submission_status,
                "siege_id": starting_siege_id,
                "war_id": war_id,
                "province_id": province_id,
                "assault_in_progress": expected_active,
            }
            return {
                **result,
                "war_action": assault_action,
                "assault_action": assault_action,
                "active_siege": copy.deepcopy(applied["active_siege"]),
                "snapshot_id": changed["snapshot_id"],
                "revision": changed["revision"],
            }

        source_army_id = parse_split_army_half_step(step)
        if source_army_id is not None:
            starting_army = _army_by_id(starting, source_army_id)
            if (
                not isinstance(starting_army, dict)
                or starting_army.get("controllable") is not True
            ):
                raise BridgeUnavailableError(
                    f"native split-army-half-{source_army_id} requires a "
                    "controllable player army"
                )
            submitted_date_raw = _date_raw(
                starting, "split-army-half starting snapshot"
            )
            player_army_ids_before = sorted(
                _controllable_army_ids(starting)
            )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            immediate = self.take_snapshot()
            player_army_ids_immediate = _controllable_army_ids(immediate)
            new_army_ids = sorted(
                player_army_ids_immediate - set(player_army_ids_before)
            )
            split_applied = (
                source_army_id in player_army_ids_immediate
                and len(new_army_ids) == 1
            )
            war_action: dict[str, object] = {
                "status": (
                    "split_applied" if split_applied else "split_submitted"
                ),
                "source_army_id": source_army_id,
                "submitted_date_raw": submitted_date_raw,
                "player_army_ids_before": player_army_ids_before,
            }
            if split_applied:
                war_action["sibling_army_id"] = new_army_ids[0]
            return {
                **result,
                "war_action": war_action,
            }

        merge = parse_merge_armies_step(step)
        if merge is not None:
            destination_army_id, source_army_id = merge
            destination_before = _army_by_id(starting, destination_army_id)
            source_before = _army_by_id(starting, source_army_id)
            if not (
                isinstance(destination_before, dict)
                and destination_before.get("controllable") is True
                and isinstance(source_before, dict)
                and source_before.get("controllable") is True
            ):
                raise BridgeUnavailableError(
                    "native merge-armies requires two controllable player "
                    "armies"
                )
            destination_province_id = destination_before.get(
                "current_province_id"
            )
            if not (
                _positive_native_id(destination_province_id)
                and source_before.get("current_province_id")
                == destination_province_id
                and not _army_known_merge_blocked(destination_before)
                and not _army_known_merge_blocked(source_before)
            ):
                raise BridgeUnavailableError(
                    "native merge-armies requires an advertised same-province "
                    "non-combat pair"
                )
            submitted_date_raw = _date_raw(
                starting, "merge-armies starting snapshot"
            )
            player_army_ids_before = sorted(
                _controllable_army_ids(starting)
            )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            immediate = self.take_snapshot()
            player_army_ids_immediate = _controllable_army_ids(immediate)
            destination_immediate = _army_by_id(
                immediate, destination_army_id
            )
            merge_applied = bool(
                isinstance(destination_immediate, dict)
                and destination_immediate.get("owner_character_id")
                == destination_before.get("owner_character_id")
                and destination_immediate.get("current_province_id")
                == destination_province_id
                and _army_by_id(immediate, source_army_id) is None
                and player_army_ids_immediate
                == set(player_army_ids_before) - {source_army_id}
            )
            return {
                **result,
                "war_action": {
                    "status": (
                        "merge_applied"
                        if merge_applied
                        else "merge_submitted"
                    ),
                    "destination_army_id": destination_army_id,
                    "source_army_id": source_army_id,
                    "submitted_date_raw": submitted_date_raw,
                    "player_army_ids_before": player_army_ids_before,
                },
            }

        route_contact_query = parse_query_route_contact_horizon_step(step)
        if route_contact_query is not None:
            subject_army_id, target_province_id, hostile_army_ids = (
                route_contact_query
            )
            if starting.get("paused") is not True:
                raise BridgeUnavailableError(
                    "native route-contact horizon query requires a paused map"
                )
            subject = _army_by_id(starting, subject_army_id)
            if (
                not isinstance(subject, dict)
                or subject.get("controllable") is not True
            ):
                raise BridgeUnavailableError(
                    "native route-contact horizon subject is not controllable"
                )
            expected_hostiles = _route_contact_hostile_ids(starting)
            if hostile_army_ids != expected_hostiles:
                raise BridgeUnavailableError(
                    "native route-contact horizon hostile scope is incomplete"
                )
            date_raw = _date_raw(starting, "route-contact starting snapshot")
            native_revision = starting.get("native_revision")
            if (
                isinstance(native_revision, bool)
                or not isinstance(native_revision, int)
                or not 1 <= native_revision <= 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "native route-contact horizon lacks a native revision"
                )
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            if (
                set(result)
                != {
                    "step",
                    "accepted",
                    "status",
                    "query_sequence",
                    "snapshot_revision",
                    "route_contact_horizon",
                    "backend_id",
                }
                or result.get("step") != step
                or result.get("accepted") is not True
                or result.get("status") != "available"
                or result.get("snapshot_revision") != native_revision
            ):
                raise BridgeUnavailableError(
                    "native route-contact horizon returned malformed status"
                )
            query_sequence = result.get("query_sequence")
            if (
                isinstance(query_sequence, bool)
                or not isinstance(query_sequence, int)
                or not 1 <= query_sequence <= 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "native route-contact horizon lacks query_sequence"
                )
            try:
                horizon = normalize_route_contact_horizon(
                    result.get("route_contact_horizon"),
                    expected_subject_army_id=subject_army_id,
                    expected_target_province_id=target_province_id,
                    expected_hostile_army_ids=hostile_army_ids,
                    expected_date_raw=date_raw,
                    expected_snapshot_revision=native_revision,
                )
            except ValueError as error:
                raise BridgeUnavailableError(str(error)) from error
            current = self.take_snapshot()
            if not _same_paused_native_frame(starting, current):
                raise BridgeUnavailableError(
                    "native route-contact horizon crossed a snapshot revision"
                )
            return {
                **result,
                "route_contact_horizon": horizon,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": native_revision,
                "queried_connection_generation": (
                    starting.get("diagnostics", {}).get(
                        "connection_generation"
                    )
                    if isinstance(starting.get("diagnostics"), dict)
                    else None
                ),
                "queried_episode_run_id": starting.get("episode_run_id"),
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

    def _execute_army_strength_query(
        self,
        *,
        starting: dict[str, object],
        selected_revision: int,
    ) -> dict[str, object]:
        """Read the full published army scope without advancing CK3 state."""
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native army-strength query requires a paused snapshot"
            )
        try:
            expected_scope = army_strength_scope(starting)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native army-strength scope is malformed: {error}"
            ) from error
        result = self._execute_primitive_step(
            QUERY_ARMY_STRENGTHS_STEP,
            expected_revision=selected_revision,
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "army_strengths",
                "backend_id",
            }
            or result.get("step") != QUERY_ARMY_STRENGTHS_STEP
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "partial"}
        ):
            raise BridgeUnavailableError(
                "native army-strength query returned a malformed status"
            )
        try:
            rows = normalize_army_strengths(
                result.get("army_strengths"),
                expected_scope=expected_scope,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native army-strength query returned malformed rows: {error}"
            ) from error
        status = army_strength_query_status(rows)
        if result.get("status") != status:
            raise BridgeUnavailableError(
                "native army-strength query status disagrees with its rows"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or query_sequence < 1
            or query_sequence > 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native army-strength query lacks query_sequence"
            )
        current = self.take_snapshot()
        if not _same_paused_native_frame(starting, current):
            raise BridgeUnavailableError(
                "native army-strength query crossed a snapshot revision"
            )
        try:
            if army_strength_scope(current) != expected_scope:
                raise BridgeUnavailableError(
                    "native army-strength scope changed during the query"
                )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native army-strength scope became malformed: {error}"
            ) from error
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": starting.get("native_revision"),
            "snapshot_id": starting.get("snapshot_id"),
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
        }
        with self._driver_state_lock:
            self._army_strength_query = {
                "status": status,
                "army_strengths": copy.deepcopy(rows),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "status": status,
            "army_strengths": rows,
            "query_sequence": query_sequence,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def _execute_combat_simulation_inputs_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one explicit encounter without advancing CK3 state."""
        parsed = parse_query_combat_simulation_inputs_step(step)
        if parsed is None:
            raise UnsupportedStepError(
                f"malformed combat simulation input step {step}"
            )
        (
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
        ) = parsed
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native combat simulation input query requires a paused snapshot"
            )
        try:
            encounter_scope = combat_simulation_encounter_scope(
                starting, attacker_army_ids, defender_army_ids
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native combat encounter scope is malformed: {error}"
            ) from error
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
            ),
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "combat_simulation_inputs",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "partial"}
        ):
            raise BridgeUnavailableError(
                "native combat simulation input query returned a malformed status"
            )
        try:
            normalized = normalize_combat_simulation_inputs(
                result.get("combat_simulation_inputs"),
                expected_target_province_id=target_province_id,
                expected_attacker_entry_province_id=(
                    attacker_entry_province_id
                ),
                expected_encounter_scope=encounter_scope,
            )
            status = combat_simulation_inputs_status(normalized)
        except ValueError as error:
            raise BridgeUnavailableError(
                "native combat simulation input query returned malformed "
                f"inputs: {error}"
            ) from error
        if result.get("status") != status:
            raise BridgeUnavailableError(
                "native combat simulation input status disagrees with "
                "input_observation_ready"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native combat simulation input query lacks query_sequence"
            )
        current = self.take_snapshot()
        if not _same_paused_native_frame(starting, current) or (
            starting.get("revision") != current.get("revision")
        ):
            raise BridgeUnavailableError(
                "native combat simulation input query crossed a snapshot revision"
            )
        try:
            current_scope = combat_simulation_encounter_scope(
                current, attacker_army_ids, defender_army_ids
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native combat encounter scope became malformed: {error}"
            ) from error
        if current_scope != encounter_scope:
            raise BridgeUnavailableError(
                "native combat encounter scope changed during the query"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": starting.get("native_revision"),
            "snapshot_id": starting.get("snapshot_id"),
            "revision": starting.get("revision"),
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
            "target_province_id": target_province_id,
            "attacker_entry_province_id": attacker_entry_province_id,
            "attacker_army_ids": list(attacker_army_ids),
            "defender_army_ids": list(defender_army_ids),
        }
        with self._driver_state_lock:
            self._combat_simulation_inputs_query = {
                "status": status,
                "combat_simulation_inputs": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "status": status,
            "combat_simulation_inputs": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def _execute_war_entry_assessments_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read exact native strategic-power assessments on one paused frame."""
        targets = parse_query_war_entry_assessments_step(step)
        if targets is None:
            raise UnsupportedStepError(
                f"malformed war-entry assessment step {step}"
            )
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native war-entry assessment query requires a paused snapshot"
            )
        try:
            require_declarable_war_targets(starting, targets)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native war-entry target scope is malformed: {error}"
            ) from error
        played_character = starting.get("played_character")
        actor_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(actor_id, bool)
            or not isinstance(actor_id, int)
            or not 1 <= actor_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native war-entry assessment lacks a played CharacterID"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "war_entry_assessments",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") != "available"
        ):
            raise BridgeUnavailableError(
                "native war-entry assessment query returned malformed status"
            )
        try:
            normalized = normalize_war_entry_assessments(
                result.get("war_entry_assessments"),
                expected_target_character_ids=targets,
                expected_actor_character_id=actor_id,
                expected_snapshot_revision=starting.get("native_revision"),
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native war-entry assessment query is malformed: {error}"
            ) from error
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native war-entry assessment query lacks query_sequence"
            )
        current = self.take_snapshot()
        if not _same_paused_native_frame(starting, current):
            raise BridgeUnavailableError(
                "native war-entry assessment query crossed a snapshot revision"
            )
        try:
            require_declarable_war_targets(current, targets)
        except ValueError as error:
            raise BridgeUnavailableError(
                "native war-entry declarations changed during query: "
                f"{error}"
            ) from error
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": starting.get("native_revision"),
            "snapshot_id": starting.get("snapshot_id"),
            "revision": starting.get("revision"),
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
            "target_character_ids": list(targets),
        }
        with self._driver_state_lock:
            self._war_entry_assessments_query = {
                "status": "available",
                "war_entry_assessments": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "status": "available",
            "war_entry_assessments": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def _execute_combat_simulation_inputs_v3_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one atomic 81-native/51-offline phase slice on one frame."""
        parsed = parse_query_combat_simulation_inputs_v3_step(step)
        if parsed is None:
            raise UnsupportedStepError(
                f"malformed production combat phase input step {step}"
            )
        (
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
        ) = parsed
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native production combat phase query requires a paused snapshot"
            )
        try:
            encounter_scope = combat_simulation_encounter_scope(
                starting, attacker_army_ids, defender_army_ids
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native production combat encounter scope is malformed: {error}"
            ) from error
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
            ),
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "combat_simulation_inputs",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "unavailable"}
        ):
            raise BridgeUnavailableError(
                "native production combat phase query returned a malformed status"
            )
        try:
            normalized = normalize_combat_simulation_inputs_v3(
                result.get("combat_simulation_inputs"),
                expected_target_province_id=target_province_id,
                expected_attacker_entry_province_id=(
                    attacker_entry_province_id
                ),
                expected_encounter_scope=encounter_scope,
            )
            status = combat_simulation_inputs_v3_status(normalized)
        except ValueError as error:
            raise BridgeUnavailableError(
                "native production combat phase query returned malformed "
                f"inputs: {error}"
            ) from error
        if result.get("status") != status:
            raise BridgeUnavailableError(
                "native production combat phase status disagrees with "
                "phase_event_inputs_ready"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native production combat phase query lacks query_sequence"
            )
        current = self.take_snapshot()
        if not _same_paused_native_frame(starting, current) or (
            starting.get("revision") != current.get("revision")
        ):
            raise BridgeUnavailableError(
                "native production combat phase query crossed a snapshot revision"
            )
        try:
            current_scope = combat_simulation_encounter_scope(
                current, attacker_army_ids, defender_army_ids
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native production combat scope became malformed: {error}"
            ) from error
        if current_scope != encounter_scope:
            raise BridgeUnavailableError(
                "native production combat scope changed during the query"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": starting.get("native_revision"),
            "snapshot_id": starting.get("snapshot_id"),
            "revision": starting.get("revision"),
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
            "target_province_id": target_province_id,
            "attacker_entry_province_id": attacker_entry_province_id,
            "attacker_army_ids": list(attacker_army_ids),
            "defender_army_ids": list(defender_army_ids),
        }
        with self._driver_state_lock:
            self._combat_simulation_inputs_v3_query = {
                "status": status,
                "combat_simulation_inputs": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "status": status,
            "combat_simulation_inputs": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def _execute_war_termination_terms_query(
        self,
        step: str,
        *,
        starting: dict[str, object],
        selected_revision: int,
        war_id: int,
    ) -> dict[str, object]:
        """Read the narrow claim-CB terms union on one paused frame."""
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native war-termination terms query requires a paused snapshot"
            )
        if _war_by_id(starting, war_id) is None:
            raise BridgeUnavailableError(
                "native war-termination terms query requires active WarID "
                f"{war_id}"
            )
        result = self._execute_primitive_step(
            step, expected_revision=selected_revision
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "war_termination_terms",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "unsupported"}
        ):
            raise BridgeUnavailableError(
                "native war-termination terms query returned malformed status"
            )
        terms = normalize_war_termination_terms(
            result.get("war_termination_terms"),
            expected_war_id=war_id,
        )
        if result.get("status") != terms.get("status"):
            raise BridgeUnavailableError(
                "native war-termination terms union status disagrees with frame"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or query_sequence < 1
            or query_sequence > 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native war-termination terms query lacks query_sequence"
            )
        current = self.take_snapshot()
        if not _same_paused_native_frame(starting, current):
            raise BridgeUnavailableError(
                "native war-termination terms query crossed a snapshot revision"
            )
        if _war_by_id(current, war_id) is None:
            raise BridgeUnavailableError(
                "native war-termination terms query returned after war ended"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": starting.get("native_revision"),
            "snapshot_id": starting.get("snapshot_id"),
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
        }
        with self._driver_state_lock:
            self._war_termination_terms[war_id] = {
                "terms": copy.deepcopy(terms),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "war_termination_terms": terms,
            "query_sequence": query_sequence,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def _execute_war_termination_exit_terms_query(
        self,
        step: str,
        *,
        starting: dict[str, object],
        selected_revision: int,
        war_id: int,
    ) -> dict[str, object]:
        """Read one all-or-nothing claim-CB exit preview on a paused frame."""
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native war-termination exit-terms query requires a paused "
                "snapshot"
            )
        if _war_by_id(starting, war_id) is None:
            raise BridgeUnavailableError(
                "native war-termination exit-terms query requires active "
                f"WarID {war_id}"
            )
        result = self._execute_primitive_step(
            step, expected_revision=selected_revision
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "war_termination_exit_terms",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") != "available"
        ):
            raise BridgeUnavailableError(
                "native war-termination exit-terms query returned malformed "
                "status"
            )
        try:
            terms = normalize_war_termination_exit_terms(
                result.get("war_termination_exit_terms"),
                expected_war_id=war_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native war-termination exit-terms query is malformed: {error}"
            ) from error
        war = _war_by_id(starting, war_id)
        played_character = starting.get("played_character")
        played_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        targeted_title_ids = (
            war.get("targeted_title_ids")
            if isinstance(war, dict)
            else None
        )
        if not (
            isinstance(war, dict)
            and war.get("player_side") == "attacker"
            and war.get("player_is_primary_war_leader") is True
            and terms.get("primary_attacker_character_id")
            == played_character_id
            and terms.get("primary_defender_character_id")
            == war.get("primary_opponent_character_id")
            and isinstance(targeted_title_ids, list)
            and terms.get("target_title_ids") == targeted_title_ids
        ):
            raise BridgeUnavailableError(
                "native war-termination exit-terms identity disagrees with "
                "the paused war snapshot"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native war-termination exit-terms query lacks query_sequence"
            )
        current = self.take_snapshot()
        if not _same_paused_native_frame(starting, current):
            raise BridgeUnavailableError(
                "native war-termination exit-terms query crossed a snapshot "
                "revision"
            )
        if _war_by_id(current, war_id) is None:
            raise BridgeUnavailableError(
                "native war-termination exit-terms query returned after war "
                "ended"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": starting.get("native_revision"),
            "snapshot_id": starting.get("snapshot_id"),
            "revision": starting.get("revision"),
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
        }
        with self._driver_state_lock:
            self._war_termination_exit_terms[war_id] = {
                "terms": copy.deepcopy(terms),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "war_termination_exit_terms": terms,
            "query_sequence": query_sequence,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def _execute_war_termination_step(
        self,
        step: str,
        *,
        starting: dict[str, object],
        selected_revision: int,
        query_war_id: int | None,
        surrender_war_id: int | None,
        white_peace_war_id: int | None,
    ) -> dict[str, object]:
        """Execute one query or query-proven termination submission."""
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native war-termination steps require a paused snapshot"
            )
        war_id = next(
            war_id
            for war_id in (
                query_war_id,
                surrender_war_id,
                white_peace_war_id,
            )
            if war_id is not None
        )
        war = _war_by_id(starting, war_id)
        if war is None:
            raise BridgeUnavailableError(
                f"native war-termination step requires active WarID {war_id}"
            )

        if query_war_id is not None:
            result = self._execute_primitive_step(
                step, expected_revision=selected_revision
            )
            if (
                set(result)
                != {
                    "step",
                    "accepted",
                    "status",
                    "query_sequence",
                    "war_termination_options",
                    "backend_id",
                }
                or result.get("step") != step
                or result.get("accepted") is not True
                or result.get("status") != "available"
            ):
                raise BridgeUnavailableError(
                    "native war-termination query returned a malformed status"
                )
            options = normalize_war_termination_options(
                result.get("war_termination_options"),
                expected_war_id=war_id,
            )
            _require_termination_options_match_war(options, war)
            query_sequence = result.get("query_sequence")
            if (
                isinstance(query_sequence, bool)
                or not isinstance(query_sequence, int)
                or query_sequence < 1
                or query_sequence > 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "native war-termination query lacks query_sequence"
                )
            current = self.take_snapshot()
            if not _same_paused_native_frame(starting, current):
                raise BridgeUnavailableError(
                    "native war-termination query crossed a snapshot revision"
                )
            current_war = _war_by_id(current, war_id)
            if current_war is None:
                raise BridgeUnavailableError(
                    "native war-termination query returned after the war ended"
                )
            _require_termination_options_match_war(options, current_war)
            diagnostics = starting.get("diagnostics")
            connection_generation = (
                diagnostics.get("connection_generation")
                if isinstance(diagnostics, dict)
                else None
            )
            cache_binding = {
                "native_revision": starting.get("native_revision"),
                "snapshot_id": starting.get("snapshot_id"),
                "connection_generation": connection_generation,
                "episode_run_id": starting.get("episode_run_id"),
            }
            with self._driver_state_lock:
                self._war_termination_options[war_id] = {
                    "options": copy.deepcopy(options),
                    "query_sequence": query_sequence,
                    "cache_binding": cache_binding,
                }
            return {
                **result,
                "war_termination_options": options,
                "query_sequence": query_sequence,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }

        option_name = (
            "surrender" if surrender_war_id is not None else "white_peace"
        )
        raise BridgeUnavailableError(
            f"native {option_name} submission requires structured_terms_v2 "
            "and campaign decision readiness"
        )

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
        with self._driver_state_lock:
            self._managed_restore_transaction = {
                "status": _MANAGED_RESTORE_TRANSACTION_STATUS,
                "request_id": request_id,
                "source_bridge_pid": self._session_bridge_pid,
                "checkpoint_sha256": checkpoint_sha256,
                "checkpoint_size": checkpoint_size,
                "checkpoint_date_raw": checkpoint_saved_date_raw,
                "history_index": previous_checkpoint.get("history_index"),
                "episode_character_id": self._episode_character_id,
                "episode_run_id": self._episode_run_id,
            }
        # This marker must reach disk before native-session can replace CK3.
        # The replacement hello may otherwise persist a new PID alongside the
        # still-untrimmed factual branch and make a daemon restart look hot.
        self._persist_driver_state()
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
        with self._driver_state_lock:
            rollback_war_failure = _derive_rollback_war_failure(
                self._command_history,
                checkpoint=previous_checkpoint,
                restored_snapshot=restored,
                episode_run_id=self._episode_run_id,
                abandoned_snapshot=starting,
            )
            if rollback_war_failure is not None:
                self._rollback_war_failures = _bounded_rollback_war_failures(
                    [rollback_war_failure], self._rollback_war_failures
                )
                self._rollback_war_failures_migration_required = False
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

    def _execute_route_contact_horizon_advance(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        starting = self.take_snapshot()
        starting_revision = int(starting["revision"])
        if expected_revision is None:
            raise BridgeUnavailableError(
                "route-contact one-day advance requires expected_revision"
            )
        _validate_revision(expected_revision, "expected_revision")
        if expected_revision != starting_revision:
            raise BridgeUnavailableError(
                "route-contact one-day advance revision mismatch: "
                f"expected {expected_revision}, current {starting_revision}"
            )
        if step not in _fresh_route_contact_advance_steps(
            starting, self._history_snapshot()
        ):
            raise BridgeUnavailableError(
                "route-contact one-day advance proof is stale or incomplete"
            )
        return self._execute_life_advance(
            expected_revision=expected_revision,
            exact_one_day=True,
            result_step=step,
        )

    def _execute_life_advance(
        self,
        *,
        expected_revision: int | None,
        exact_one_day: bool = False,
        result_step: str = "life-advance",
        starting_snapshot: dict[str, object] | None = None,
    ) -> dict[str, object]:
        revision_validated_at_entry = starting_snapshot is not None
        starting = (
            copy.deepcopy(starting_snapshot)
            if starting_snapshot is not None
            else self.take_snapshot()
        )
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
            if (
                not revision_validated_at_entry
                and expected_revision != starting_revision
            ):
                if exact_one_day or starting.get("paused") is True:
                    raise BridgeUnavailableError(
                        "native life-advance revision mismatch: "
                        f"expected {expected_revision}, current "
                        f"{starting_revision}"
                    )
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
        if exact_one_day and starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "route-contact one-day advance requires a paused map"
            )
        assault_history = self._history_snapshot()
        open_assaults = _native_open_assault_lifecycles(assault_history)
        if open_assaults and starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native life-advance requires a paused rich snapshot while "
                "an assault_started lifecycle remains open"
            )
        if starting.get("paused") is True:
            unresolved_assaults = _native_unobservable_started_assaults(
                starting, assault_history
            )
            if unresolved_assaults:
                raise BridgeUnavailableError(
                    "native life-advance refused an unresolved assault_started "
                    "lifecycle without observable same-SiegeID rich state"
                )
        starting_date_raw = _date_raw(starting, "starting snapshot")
        horizon_days = 1 if exact_one_day else _life_advance_horizon_days(starting)
        timeline_speed = 1 if horizon_days == 1 else 5
        speed_step = f"set-speed-{timeline_speed}"
        if speed_step not in self.capabilities()["action_steps"]:
            raise BridgeUnavailableError(
                "native life-advance requires "
                f"{speed_step} for its {horizon_days}-day paused timeline "
                "slice; the map was not resumed"
            )
        actions: list[dict[str, object]] = []

        speed_result = self._execute_composite_primitive(
            speed_step, starting
        )
        actions.append({"step": speed_step, "result": speed_result})
        current = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: snapshot.get("speed") == timeline_speed,
            timeout_seconds=self.command_timeout_seconds,
        )
        if current.get("speed") != timeline_speed:
            raise BridgeUnavailableError(
                "native life-advance did not observe "
                f"speed {timeline_speed}"
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
        while not _life_advance_progressed(
            current,
            starting,
            horizon_days_override=(1 if exact_one_day else None),
        ):
            remaining = progress_deadline - time.monotonic()
            if remaining <= 0:
                break
            current = self.wait_for_change(
                int(current["revision"]),
                timeout_seconds=remaining,
            )

        current = self._pause_life_advance(current, actions)
        reached_progress_postcondition = _life_advance_progressed(
            current,
            starting,
            horizon_days_override=(1 if exact_one_day else None),
        )
        if not reached_progress_postcondition:
            current_date_raw = _date_raw(
                current, "active-war bounded ending snapshot"
            )
            if current_date_raw > starting_date_raw:
                progress_status = "wall_timeout_with_date_progress"
            elif starting.get("active_wars"):
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
        if exact_one_day and ending_date_raw > starting_date_raw + 24:
            raise BridgeUnavailableError(
                "route-contact one-day advance exceeded its 24-hour native "
                f"horizon: {starting_date_raw} -> {ending_date_raw}"
            )
        return {
            "step": result_step,
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
        if isinstance(step, str) and step.startswith(
            QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX
        ):
            if parse_query_war_entry_assessments_step(step) is None:
                raise UnsupportedStepError(
                    "malformed war-entry assessment step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "war-entry assessment queries are pure native and will "
                    "not use fallback"
                )
            starting = self.take_snapshot()
            native_revision = None
            if expected_revision is not None:
                _validate_revision(expected_revision, "expected_revision")
                if expected_revision != starting.get("revision"):
                    raise BridgeUnavailableError(
                        "hybrid gameplay revision mismatch: expected "
                        f"{expected_revision}, current "
                        f"{starting.get('revision')}"
                    )
            backend_revisions = starting.get("backend_revisions")
            if isinstance(backend_revisions, dict) and isinstance(
                backend_revisions.get("fast"), int
            ):
                native_revision = int(backend_revisions["fast"])
            result = self.native.execute_step(
                step, expected_revision=native_revision
            )
            ending = self.take_snapshot()
            if (
                ending.get("snapshot_id") != starting.get("snapshot_id")
                or ending.get("revision") != starting.get("revision")
                or ending.get("native_revision")
                != starting.get("native_revision")
            ):
                raise BridgeUnavailableError(
                    "hybrid war-entry assessment query crossed a snapshot "
                    "revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
        if isinstance(step, str) and step.startswith(
            QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX
        ):
            if parse_query_combat_simulation_inputs_v3_step(step) is None:
                raise UnsupportedStepError(
                    "malformed production combat phase input step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "production combat phase queries are pure native and "
                    "will not use fallback"
                )
            starting = self.take_snapshot()
            native_revision = None
            if expected_revision is not None:
                _validate_revision(expected_revision, "expected_revision")
                if expected_revision != starting.get("revision"):
                    raise BridgeUnavailableError(
                        "hybrid gameplay revision mismatch: expected "
                        f"{expected_revision}, current "
                        f"{starting.get('revision')}"
                    )
            backend_revisions = starting.get("backend_revisions")
            if isinstance(backend_revisions, dict) and isinstance(
                backend_revisions.get("fast"), int
            ):
                native_revision = int(backend_revisions["fast"])
            result = self.native.execute_step(
                step, expected_revision=native_revision
            )
            ending = self.take_snapshot()
            if (
                ending.get("snapshot_id") != starting.get("snapshot_id")
                or ending.get("revision") != starting.get("revision")
                or ending.get("native_revision")
                != starting.get("native_revision")
            ):
                raise BridgeUnavailableError(
                    "hybrid production combat phase query crossed a "
                    "snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get(
                    "native_revision"
                ),
            }
        if isinstance(step, str) and step.startswith(
            QUERY_COMBAT_SIMULATION_INPUTS_STEP_PREFIX
        ):
            if parse_query_combat_simulation_inputs_step(step) is None:
                raise UnsupportedStepError(
                    "malformed hypothetical-contact combat input step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "combat simulation input queries are pure native and "
                    "will not use fallback"
                )
            starting = self.take_snapshot()
            native_revision = None
            if expected_revision is not None:
                _validate_revision(expected_revision, "expected_revision")
                if expected_revision != starting.get("revision"):
                    raise BridgeUnavailableError(
                        "hybrid gameplay revision mismatch: expected "
                        f"{expected_revision}, current "
                        f"{starting.get('revision')}"
                    )
            backend_revisions = starting.get("backend_revisions")
            if isinstance(backend_revisions, dict) and isinstance(
                backend_revisions.get("fast"), int
            ):
                native_revision = int(backend_revisions["fast"])
            result = self.native.execute_step(
                step, expected_revision=native_revision
            )
            ending = self.take_snapshot()
            if (
                ending.get("snapshot_id") != starting.get("snapshot_id")
                or ending.get("revision") != starting.get("revision")
                or ending.get("native_revision")
                != starting.get("native_revision")
            ):
                raise BridgeUnavailableError(
                    "hybrid combat simulation input query crossed a "
                    "snapshot revision"
                )
            # The native driver proves the underlying fast frame.  Rebind its
            # result metadata to the paired public frame checked by the MCP
            # service; native_revision remains the exact CK3 frame identity.
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get(
                    "native_revision"
                ),
            }
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
    snapshot: dict[str, object],
    starting_snapshot: dict[str, object],
    *,
    horizon_days_override: int | None = None,
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
    horizon_days = (
        horizon_days_override
        if horizon_days_override is not None
        else _life_advance_horizon_days(starting_snapshot)
    )
    return current_date_raw >= starting_date_raw + horizon_days * 24


def _native_history_after_latest_restore(
    history: list[dict[str, object]],
) -> list[dict[str, object]]:
    for position in range(len(history) - 1, -1, -1):
        row = history[position]
        if row.get("command") == _RESTORE_CHECKPOINT_STEP and row.get("ok") is True:
            return history[position + 1 :]
    return history


def _native_open_assault_lifecycles(
    history: list[dict[str, object]],
) -> list[dict[str, int]]:
    """Recover exact, postcondition-proven Assault lifecycles from history."""
    scoped = _native_history_after_latest_restore(history)
    opened: dict[tuple[int, int, int], dict[str, int]] = {}
    for position, row in enumerate(scoped, start=1):
        if row.get("ok") is not True:
            continue
        command, result = _effective_native_history_entry(row)
        if not isinstance(result, dict):
            continue
        action = result.get("assault_action")
        if not isinstance(action, dict):
            candidate = result.get("war_action")
            action = candidate if isinstance(candidate, dict) else None
        if not isinstance(action, dict):
            continue
        siege_id = action.get("siege_id")
        war_id = action.get("war_id")
        province_id = action.get("province_id")
        if not all(
            _positive_native_id(value)
            for value in (siege_id, war_id, province_id)
        ):
            continue
        key = (int(war_id), int(province_id), int(siege_id))
        if (
            action.get("status") == "assault_started"
            and parse_start_assault_step(command) == siege_id
        ):
            opened[key] = {
                "war_id": int(war_id),
                "province_id": int(province_id),
                "siege_id": int(siege_id),
                "started_history_position": position,
            }
        elif (
            action.get("status") == "assault_stopped"
            and parse_stop_assault_step(command) == siege_id
        ):
            opened.pop(key, None)
    return sorted(
        opened.values(),
        key=lambda row: (
            row["started_history_position"],
            row["war_id"],
            row["province_id"],
            row["siege_id"],
        ),
    )


def _native_latest_assault_life_advance_failed(
    history: list[dict[str, object]],
    *,
    started_history_position: int,
) -> bool:
    scoped = _native_history_after_latest_restore(history)
    for position in range(len(scoped), started_history_position, -1):
        row = scoped[position - 1]
        command, _result = _effective_native_history_entry(row)
        if is_life_advance_step(command):
            return row.get("ok") is not True
    return False


def _native_unobservable_started_assaults(
    snapshot: dict[str, object],
    history: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Find proven Starts whose current paused rich state is unknown."""
    wars = snapshot.get("active_wars")
    wars_by_id = {
        int(war["war_id"]): war
        for war in (wars if isinstance(wars, list) else [])
        if isinstance(war, dict) and _positive_native_id(war.get("war_id"))
    }
    pending: list[dict[str, object]] = []
    for lifecycle in _native_open_assault_lifecycles(history):
        war = wars_by_id.get(lifecycle["war_id"])
        if not isinstance(war, dict):
            continue
        states = war.get("objective_province_states")
        state = next(
            (
                row
                for row in (states if isinstance(states, list) else [])
                if isinstance(row, dict)
                and row.get("province_id") == lifecycle["province_id"]
            ),
            None,
        )
        reason: str | None = None
        if snapshot.get("war_objective_assault_supported") is not True:
            reason = "assault_capability_unavailable_after_start"
        elif not isinstance(state, dict):
            reason = "objective_row_unavailable_after_start"
        elif state.get("siege_observable") is not True:
            reason = "siege_unobservable_after_start"
        else:
            active_siege = state.get("active_siege")
            if "active_siege" in state and active_siege is None:
                continue
            if not isinstance(active_siege, dict):
                reason = "active_siege_unavailable_after_start"
            else:
                observed_siege_id = active_siege.get("siege_id")
                if observed_siege_id != lifecycle["siege_id"]:
                    if _positive_native_id(observed_siege_id):
                        continue
                    reason = "siege_generation_unavailable_after_start"
                elif active_siege.get("assault_observable") is not True:
                    reason = "assault_subdomain_unobservable_after_start"
                elif active_siege.get("assault_in_progress") is False:
                    continue
                elif (
                    active_siege.get("assault_in_progress") is True
                    and active_siege.get("player_army_besieging") is True
                ):
                    if _native_latest_assault_life_advance_failed(
                        history,
                        started_history_position=lifecycle[
                            "started_history_position"
                        ],
                    ):
                        reason = "previous_assault_slice_failed_unknown"
                    else:
                        continue
                else:
                    reason = "assault_flag_unavailable_after_start"
        pending.append(
            {
                **lifecycle,
                "reason": reason or "assault_state_unavailable_after_start",
            }
        )
    return pending


def _life_advance_horizon_days(snapshot: dict[str, object]) -> int:
    """Use bounded paused-to-paused slices while the player owns a siege.

    Rich CSiege state is intentionally unavailable in running snapshots.  We
    therefore only classify the starting paused frame and stop by date; a
    running ``active_siege=null`` can never masquerade as siege completion.
    Because running frames also suppress full routes, any active controlled or
    hostile route takes a one-day horizon. Any controllable combat/retreat or
    active assault has the same one-day bound. An ordinary stationary siege
    and an otherwise route-free active war retain a seven-day ceiling so a
    direct MCP advance cannot skip the first enemy-target cadence milestone.
    """
    player_armies = snapshot.get("player_armies")
    for army in player_armies if isinstance(player_armies, list) else []:
        if (
            isinstance(army, dict)
            and army.get("controllable") is True
            and _army_in_combat_or_retreat(army)
        ):
            # Combat and retreat can resolve or redirect another stack between
            # ticks.  Re-observe the whole M x N matrix after one day even if
            # this snapshot started while the map was already running.
            return _NATIVE_COMBAT_RETREAT_ADVANCE_MAX_DAYS
    for army in player_armies if isinstance(player_armies, list) else []:
        if not isinstance(army, dict) or army.get("controllable") is not True:
            continue
        move_target = army.get("move_target_province_id")
        route = army.get("route_province_ids")
        state = army.get("army_state")
        state_code = army.get("army_state_code")
        if (
            _positive_native_id(move_target)
            or isinstance(route, list)
            and bool(route)
            or isinstance(state, str)
            and state.casefold() == "moving"
            or state_code == 7
        ):
            # Running snapshots do not publish a complete route. Stop by date
            # before CK3 can retarget enemies for several unseen game days.
            return _NATIVE_ACTIVE_ROUTE_ADVANCE_MAX_DAYS
    wars = snapshot.get("active_wars")
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        enemies = war.get("enemy_armies")
        for enemy in enemies if isinstance(enemies, list) else []:
            if not isinstance(enemy, dict):
                continue
            state = enemy.get("army_state")
            state_code = enemy.get("army_state_code")
            if (
                enemy.get("retreating") is True
                or isinstance(state, str)
                and state.casefold() == "retreating"
                or state_code == 6
            ):
                continue
            target = enemy.get("move_target_province_id")
            route = enemy.get("route_province_ids")
            if (
                _positive_native_id(target)
                or isinstance(route, list)
                and bool(route)
                or isinstance(state, str)
                and state.casefold() == "moving"
                or state_code == 7
            ):
                # The enemy endpoint epoch is re-evaluated after every
                # tactical day.  Seven/fourteen days are observations, not a
                # license to run blind through them.
                return _NATIVE_ACTIVE_ROUTE_ADVANCE_MAX_DAYS
    if snapshot.get("paused") is not True:
        return (
            _NATIVE_SIEGE_ADVANCE_MAX_DAYS
            if isinstance(wars, list) and bool(wars)
            else _NATIVE_WAR_ADVANCE_MAX_DAYS
        )
    player_siege_observed = False
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
                player_siege_observed = True
                if (
                    snapshot.get("war_objective_assault_supported") is True
                    and active_siege.get("assault_observable") is True
                    and active_siege.get("assault_in_progress") is True
                ):
                    return _NATIVE_ASSAULT_ADVANCE_MAX_DAYS
    if (
        player_siege_observed
        and snapshot.get("war_objective_siege_progress_supported") is True
    ):
        return _NATIVE_SIEGE_ADVANCE_MAX_DAYS
    return (
        _NATIVE_SIEGE_ADVANCE_MAX_DAYS
        if isinstance(wars, list) and bool(wars)
        else _NATIVE_WAR_ADVANCE_MAX_DAYS
    )


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
        "war_objective_assault_supported": (
            WAR_OBJECTIVE_ASSAULT_CAPABILITY in capabilities
        ),
    }


def _army_in_combat_or_retreat(army: dict[str, object]) -> bool:
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    return bool(
        army.get("in_combat") is True
        or army.get("retreating") is True
        or (
            isinstance(state, str)
            and state.casefold() in {"combat", "retreating"}
        )
        or (
            isinstance(state_code, int)
            and not isinstance(state_code, bool)
            and state_code in {2, 6}
        )
    )


def _army_retreating(army: dict[str, object]) -> bool:
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    return bool(
        army.get("retreating") is True
        or (
            isinstance(state, str)
            and state.casefold() == "retreating"
        )
        or (
            isinstance(state_code, int)
            and not isinstance(state_code, bool)
            and state_code == 6
        )
    )


def _army_known_merge_blocked(army: dict[str, object]) -> bool:
    return _army_in_combat_or_retreat(army)


def _action_steps(
    capabilities: list[str],
    active_event: object = None,
    pending_character_interaction: object = None,
    active_wars: object = None,
    player_armies: object = None,
    declarable_wars: object = None,
    arrange_marriage_choices: object = None,
    paused: object = None,
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
    expand_route_contact_horizons = False
    expand_actual_contact_scopes = False
    expand_disband_armies = False
    expand_split_armies = False
    expand_merge_armies = False
    expand_start_assaults = False
    expand_stop_assaults = False
    expand_enforce_demands = False
    advertise_army_strength_query = False
    expand_termination_queries = False
    expand_termination_terms_queries = False
    expand_termination_exit_terms_queries = False
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
        elif capability == QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY:
            expand_route_contact_horizons = True
        elif capability == QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY:
            expand_actual_contact_scopes = True
        elif capability == DISBAND_ARMY_CAPABILITY:
            expand_disband_armies = True
        elif capability == SPLIT_ARMY_HALF_CAPABILITY:
            expand_split_armies = True
        elif step.startswith("split-army-half-"):
            # Split Half is generation-bound and may only be expanded from the
            # exact adapter template above. Never expose an unknown adapter's
            # literal or placeholder spelling as an executable step.
            continue
        elif capability == MERGE_ARMIES_CAPABILITY:
            expand_merge_armies = True
        elif step.startswith("merge-armies-"):
            # Merge is a generation-bound ordered pair and must only be
            # expanded from the exact adapter template above.
            continue
        elif capability == START_ASSAULT_CAPABILITY:
            expand_start_assaults = True
        elif step.startswith("start-assault-"):
            # Siege IDs carry a generation. Expand only the frozen exact-build
            # template against the current observable siege state.
            continue
        elif capability == STOP_ASSAULT_CAPABILITY:
            expand_stop_assaults = True
        elif step.startswith("stop-assault-"):
            continue
        elif capability == ENFORCE_DEMANDS_CAPABILITY:
            expand_enforce_demands = True
        elif capability == QUERY_ARMY_STRENGTHS_CAPABILITY:
            advertise_army_strength_query = True
        elif capability in {
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
            QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
        }:
            # The target, entry edge and ordered side partitions are supplied.
            # Never leak the N placeholder as an executable action or try to
            # enumerate candidate Provinces from a snapshot.
            continue
        elif capability == QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY:
            # This query needs the current paused declarable-target set. The
            # concrete literal is added below from that snapshot; never expose
            # the adapter's `-N` capability template as an executable action.
            continue
        elif capability == QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY:
            expand_termination_queries = True
        elif capability == QUERY_WAR_TERMINATION_TERMS_CAPABILITY:
            expand_termination_terms_queries = True
        elif (
            WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED
            and capability == QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY
        ):
            expand_termination_exit_terms_queries = True
        elif capability in {
            SURRENDER_WAR_CAPABILITY,
            OFFER_WHITE_PEACE_CAPABILITY,
        }:
            # Termination commands are generation-bound and irreversible.
            # The driver advertises literals only from a same-revision native
            # query cache; never leak an adapter placeholder as an action.
            continue
        elif step.startswith(
            (
                QUERY_COMBAT_SIMULATION_INPUTS_STEP_PREFIX,
                QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX,
                "query-war-termination-options-",
                "query-war-termination-terms-v1-",
                QUERY_WAR_TERMINATION_EXIT_TERMS_STEP_PREFIX,
                "surrender-war-",
                "offer-white-peace-",
            )
        ):
            continue
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
    if expand_termination_queries and paused is True:
        steps.update(
            query_war_termination_options_step(int(war["war_id"]))
            for war in wars
            if _positive_native_id(war.get("war_id"))
            and int(war["war_id"]) <= 2**31 - 1
        )
    if expand_termination_terms_queries and paused is True:
        steps.update(
            query_war_termination_terms_step(int(war["war_id"]))
            for war in wars
            if _positive_native_id(war.get("war_id"))
            and int(war["war_id"]) <= 2**31 - 1
        )
    if expand_termination_exit_terms_queries and paused is True:
        steps.update(
            query_war_termination_exit_terms_step(int(war["war_id"]))
            for war in wars
            if _positive_native_id(war.get("war_id"))
            and int(war["war_id"]) <= 2**31 - 1
        )
    if advertise_army_strength_query and paused is True:
        steps.add(QUERY_ARMY_STRENGTHS_STEP)
    if expand_actual_contact_scopes and paused is True:
        steps.update(
            query_actual_contact_scope_step(
                int(army["army_id"]), int(army["current_province_id"])
            )
            for army in controllable
            if _positive_native_id(army.get("army_id"))
            and _positive_native_id(army.get("current_province_id"))
            and not _army_retreating(army)
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
    if expand_split_armies:
        steps.update(
            split_army_half_step(int(army["army_id"]))
            for army in controllable
            if isinstance(army.get("army_id"), int)
            and not isinstance(army.get("army_id"), bool)
            and 0 < int(army["army_id"]) <= 2**31 - 1
        )
    if expand_merge_armies:
        merge_candidates = [
            army
            for army in controllable
            if _positive_native_id(army.get("army_id"))
            and _positive_native_id(army.get("current_province_id"))
            and not _army_known_merge_blocked(army)
        ]
        for destination in merge_candidates:
            for source in merge_candidates:
                destination_army_id = int(destination["army_id"])
                source_army_id = int(source["army_id"])
                if (
                    destination_army_id != source_army_id
                    and destination.get("current_province_id")
                    == source.get("current_province_id")
                ):
                    steps.add(
                        merge_armies_step(
                            destination_army_id, source_army_id
                        )
                    )
    if WAR_OBJECTIVE_ASSAULT_CAPABILITY in capabilities:
        # Start opens a time-sensitive lifecycle and therefore requires a
        # complete recovery bundle.  A partial adapter that cannot later Stop
        # must never advertise Start.  Stop remains independently available
        # for recovering an assault that was already active/restored.
        expand_start_assaults = bool(
            expand_start_assaults and expand_stop_assaults
        )
        for war in wars:
            states = war.get("objective_province_states")
            for state in states if isinstance(states, list) else []:
                active_siege = (
                    state.get("active_siege")
                    if isinstance(state, dict)
                    and state.get("siege_observable") is True
                    else None
                )
                if not (
                    isinstance(active_siege, dict)
                    and active_siege.get("assault_observable") is True
                    and _positive_native_id(active_siege.get("siege_id"))
                    and active_siege.get("player_army_besieging") is True
                ):
                    continue
                siege_id = int(active_siege["siege_id"])
                if (
                    expand_start_assaults
                    and active_siege.get("assault_in_progress") is False
                    and active_siege.get("can_start_assault") is True
                ):
                    steps.add(start_assault_step(siege_id))
                if (
                    expand_stop_assaults
                    and active_siege.get("assault_in_progress") is True
                    and active_siege.get("can_stop_assault") is True
                ):
                    steps.add(stop_assault_step(siege_id))
    if (
        expand_move_armies
        or expand_preview_move_armies
        or expand_route_contact_horizons
    ) and wars:
        target_provinces = {
            int(army["current_province_id"])
            for army in enemy_armies_from_wars(wars)
            if isinstance(army.get("current_province_id"), int)
        }
        target_provinces.update(
            int(army["move_target_province_id"])
            for army in controllable
            if _positive_native_id(army.get("move_target_province_id"))
        )
        if war_primary_opponent_supported:
            target_provinces.update(
                enemy_primary_default_raise_province_ids(wars)
            )
        if war_objectives_supported:
            target_provinces.update(war_objective_province_ids(wars))
        hostile_ids = sorted(
            {
                int(enemy["army_id"])
                for enemy in enemy_armies_from_wars(wars)
                if _positive_native_id(enemy.get("army_id"))
                and enemy.get("retreating") is not True
                and enemy.get("army_state") != "retreating"
                and enemy.get("army_state_code") != 6
            }
        )
        for army in controllable:
            army_id = army.get("army_id")
            if not isinstance(army_id, int):
                continue
            for province_id in target_provinces:
                if province_id == army.get("current_province_id"):
                    continue
                if (
                    expand_move_armies
                    and province_id != army.get("move_target_province_id")
                ):
                    steps.add(move_army_step(army_id, province_id))
                if expand_preview_move_armies:
                    steps.add(preview_move_army_step(army_id, province_id))
                if (
                    expand_route_contact_horizons
                    and paused is True
                    and 0 < len(hostile_ids) <= 64
                ):
                    steps.add(
                        query_route_contact_horizon_step(
                            army_id, province_id, hostile_ids
                        )
                    )
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


def _route_contact_hostile_ids(
    snapshot: dict[str, object],
) -> tuple[int, ...]:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return ()
    return tuple(
        sorted(
            {
                int(enemy["army_id"])
                for enemy in enemy_armies_from_wars(
                    [war for war in wars if isinstance(war, dict)]
                )
                if _positive_native_id(enemy.get("army_id"))
                and enemy.get("retreating") is not True
                and enemy.get("army_state") != "retreating"
                and enemy.get("army_state_code") != 6
            }
        )
    )


def _fresh_route_contact_advance_steps(
    snapshot: dict[str, object],
    history: list[dict[str, object]],
) -> set[str]:
    """Return one-shot advances backed by a true proof on this exact frame."""
    if snapshot.get("paused") is not True:
        return set()
    hostiles = _route_contact_hostile_ids(snapshot)
    if not 0 < len(hostiles) <= 64:
        return set()
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    date_raw = snapshot.get("date_raw")
    native_revision = snapshot.get("native_revision")
    if (
        isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or native_revision <= 0
    ):
        return set()

    advances: set[str] = set()
    seen_queries: set[tuple[int, int, tuple[int, ...]]] = set()
    scoped_history = _native_history_after_latest_restore(history)
    for row in reversed(scoped_history):
        command, result = _effective_native_history_entry(row)
        query = parse_query_route_contact_horizon_step(command)
        if query is None or query in seen_queries:
            continue
        seen_queries.add(query)
        subject_army_id, target_province_id, requested_hostiles = query
        if row.get("ok") is not True or requested_hostiles != hostiles:
            continue
        subject = _army_by_id(snapshot, subject_army_id)
        horizon = (
            result.get("route_contact_horizon")
            if isinstance(result, dict)
            else None
        )
        subject_route = (
            horizon.get("subject_route")
            if isinstance(horizon, dict)
            else None
        )
        snapshot_route = _canonical_remaining_route(subject)
        proof_route = _canonical_timed_route(subject_route)
        if not (
            isinstance(subject, dict)
            and subject.get("controllable") is True
            and subject.get("move_target_province_id") == target_province_id
            and snapshot_route
            and snapshot_route[-1] == target_province_id
            and proof_route == snapshot_route
            and isinstance(subject_route, dict)
            and subject_route.get("army_id") == subject_army_id
            and subject_route.get("current_province_id")
            == subject.get("current_province_id")
            and isinstance(horizon, dict)
            and horizon.get("status") == "available"
            and horizon.get("one_day_contact_free") is True
            and horizon.get("date_raw") == date_raw
            and horizon.get("snapshot_revision") == native_revision
            and horizon.get("subject_army_id") == subject_army_id
            and horizon.get("target_province_id") == target_province_id
            and tuple(horizon.get("hostile_army_ids", ())) == hostiles
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == native_revision
            and result.get("queried_connection_generation")
            == connection_generation
            and result.get("queried_episode_run_id")
            == snapshot.get("episode_run_id")
            and _route_contact_advance_scope_isolated(
                snapshot, subject_army_id=subject_army_id
            )
        ):
            continue
        advances.add(
            advance_route_contact_horizon_step(
                subject_army_id, target_province_id, hostiles
            )
        )
    return advances


def _canonical_remaining_route(army: object) -> list[int] | None:
    if not isinstance(army, dict):
        return None
    route = army.get("route_province_ids")
    if not isinstance(route, list) or any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in route
    ):
        return None
    normalized = list(route)
    current = army.get("current_province_id")
    if normalized and normalized[0] == current:
        normalized = normalized[1:]
    return normalized


def _canonical_timed_route(route: object) -> list[int] | None:
    if not isinstance(route, dict) or route.get("timeline_observable") is not True:
        return None
    values = route.get("route_province_ids")
    if not isinstance(values, list) or any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in values
    ):
        return None
    normalized = list(values)
    if normalized and normalized[0] == route.get("current_province_id"):
        normalized = normalized[1:]
    return normalized


def _route_contact_advance_scope_isolated(
    snapshot: dict[str, object], *, subject_army_id: int
) -> bool:
    """Fail closed when one subject proof would advance another risky army."""
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return False
    wars = snapshot.get("active_wars")
    enemies = enemy_armies_from_wars(
        [war for war in wars if isinstance(war, dict)]
        if isinstance(wars, list)
        else []
    )
    for army in controllable_armies(
        [row for row in armies if isinstance(row, dict)]
    ):
        army_id = army.get("army_id")
        if army_id == subject_army_id:
            continue
        if _army_in_combat_or_retreat(army):
            return False
        route = _canonical_remaining_route(army)
        if _positive_native_id(army.get("move_target_province_id")) or route:
            return False
        province_id = army.get("current_province_id")
        if not _positive_native_id(province_id):
            return False
        for enemy in enemies:
            if (
                enemy.get("retreating") is True
                or enemy.get("army_state") == "retreating"
                or enemy.get("army_state_code") == 6
            ):
                continue
            enemy_route = enemy.get("route_province_ids")
            if province_id in {
                enemy.get("current_province_id"),
                enemy.get("move_target_province_id"),
            } or (
                isinstance(enemy_route, list) and province_id in enemy_route
            ):
                return False
    return True


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


def _assault_siege_observation(
    snapshot: dict[str, object],
    *,
    siege_id: int,
    war_id: int | None = None,
    province_id: int | None = None,
) -> dict[str, object] | None:
    """Locate one generation-stable assault row in a paused rich snapshot."""
    if snapshot.get("paused") is not True:
        return None
    wars = snapshot.get("active_wars")
    matches: list[dict[str, object]] = []
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        candidate_war_id = war.get("war_id")
        if not _positive_native_id(candidate_war_id) or (
            war_id is not None and candidate_war_id != war_id
        ):
            continue
        states = war.get("objective_province_states")
        for state in states if isinstance(states, list) else []:
            if not isinstance(state, dict):
                continue
            candidate_province_id = state.get("province_id")
            if not _positive_native_id(candidate_province_id) or (
                province_id is not None
                and candidate_province_id != province_id
            ):
                continue
            active_siege = (
                state.get("active_siege")
                if state.get("siege_observable") is True
                else None
            )
            if not (
                isinstance(active_siege, dict)
                and active_siege.get("siege_id") == siege_id
                and active_siege.get("assault_observable") is True
            ):
                continue
            matches.append(
                {
                    "war_id": int(candidate_war_id),
                    "province_id": int(candidate_province_id),
                    "active_siege": active_siege,
                }
            )
    return matches[0] if len(matches) == 1 else None


def _require_termination_options_match_war(
    options: dict[str, object], war: dict[str, object]
) -> None:
    fields = (
        "war_id",
        "player_side",
        "player_is_primary_war_leader",
        "player_relative_war_score",
    )
    if any(options.get(field) != war.get(field) for field in fields):
        raise BridgeUnavailableError(
            "native war-termination query does not match the active war row"
        )


def _same_paused_native_frame(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    before_diagnostics = before.get("diagnostics")
    after_diagnostics = after.get("diagnostics")
    return bool(
        before.get("paused") is True
        and after.get("paused") is True
        and before.get("native_revision") == after.get("native_revision")
        and before.get("snapshot_id") == after.get("snapshot_id")
        and isinstance(before_diagnostics, dict)
        and isinstance(after_diagnostics, dict)
        and before_diagnostics.get("connection_generation")
        == after_diagnostics.get("connection_generation")
        and before.get("episode_run_id") == after.get("episode_run_id")
    )


def _checkpoint_history_index(
    checkpoint: object,
    history: list[dict[str, object]],
) -> int | None:
    if not isinstance(checkpoint, dict):
        return None
    index = checkpoint.get("history_index")
    if (
        isinstance(index, bool)
        or not isinstance(index, int)
        or not 1 <= index <= len(history)
    ):
        return None
    anchor = history[index - 1]
    result = anchor.get("result")
    saved = result.get("checkpoint") if isinstance(result, dict) else None
    return index if (
        anchor.get("index") == index
        and anchor.get("command") == "save-checkpoint"
        and anchor.get("ok") is True
        and isinstance(saved, dict)
        and all(
            saved.get(key) == checkpoint.get(key)
            for key in ("sha256", "size", "date_raw")
        )
    ) else None


def _normalize_managed_restore_transaction(
    value: object,
    *,
    checkpoint: object,
    history: list[dict[str, object]],
    bridge_pid: int,
    episode_character_id: object,
    episode_run_id: object,
) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    source_pid = value.get("source_bridge_pid")
    replacement_pid = value.get("replacement_bridge_pid")
    request_id = value.get("request_id")
    digest = value.get("checkpoint_sha256")
    size = value.get("checkpoint_size")
    date_raw = value.get("checkpoint_date_raw")
    history_index = value.get("history_index")
    if (
        value.get("status") != _MANAGED_RESTORE_TRANSACTION_STATUS
        or not isinstance(request_id, str)
        or not request_id.startswith("restore-")
        or isinstance(source_pid, bool)
        or not isinstance(source_pid, int)
        or source_pid <= 0
        or (
            replacement_pid is not None
            and (
                isinstance(replacement_pid, bool)
                or not isinstance(replacement_pid, int)
                or replacement_pid <= 0
            )
        )
        or bridge_pid
        != (replacement_pid if replacement_pid is not None else source_pid)
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or value.get("episode_character_id") != episode_character_id
        or value.get("episode_run_id") != episode_run_id
        or not isinstance(checkpoint, dict)
        or checkpoint.get("sha256") != digest
        or checkpoint.get("size") != size
        or checkpoint.get("date_raw") != date_raw
        or _checkpoint_history_index(checkpoint, history) != history_index
    ):
        return None
    return copy.deepcopy(value)


def _effective_native_history_entry(
    row: dict[str, object],
) -> tuple[str | None, dict[str, object] | None]:
    command = row.get("command")
    result = row.get("result")
    if command == "auto-turn" and isinstance(result, dict):
        auto_turn = result.get("auto_turn")
        selected = (
            auto_turn.get("selected_step")
            if isinstance(auto_turn, dict)
            else None
        )
        command = selected if isinstance(selected, str) else None
        if not set(result).intersection(
            {
                "route_preview",
                "war_action",
                "assault_action",
                "war_progress_before",
                "war_progress_after",
                "player_armies",
            }
        ):
            nested = (
                auto_turn.get("result")
                if isinstance(auto_turn, dict)
                else None
            )
            if isinstance(nested, dict):
                result = nested
    return (
        command if isinstance(command, str) else None,
        result if isinstance(result, dict) else None,
    )


def _result_army_observations(
    result: dict[str, object],
) -> list[dict[str, object]]:
    direct = result.get("player_armies")
    observations = (
        [army for army in direct if isinstance(army, dict)]
        if isinstance(direct, list)
        else []
    )
    progress = result.get("war_progress_after")
    wars = progress.get("wars") if isinstance(progress, dict) else None
    for war in wars if isinstance(wars, list) else []:
        armies = war.get("player_armies") if isinstance(war, dict) else None
        if isinstance(armies, list):
            observations.extend(army for army in armies if isinstance(army, dict))
    return observations


def _war_id_for_army(
    snapshot: dict[str, object], army_id: int
) -> int | None:
    wars = snapshot.get("active_wars")
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        armies = war.get("allied_armies")
        if not any(
            isinstance(army, dict)
            and army.get("army_id") == army_id
            and army.get("controllable") is True
            for army in (armies if isinstance(armies, list) else [])
        ):
            continue
        war_id = war.get("war_id")
        return int(war_id) if _positive_native_id(war_id) else None
    return None


def _positive_native_id(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_native_route(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        _positive_native_id(province_id) for province_id in value
    )


def _derive_rollback_war_failure(
    history: list[dict[str, object]],
    *,
    checkpoint: object,
    restored_snapshot: dict[str, object],
    episode_run_id: object,
    abandoned_snapshot: dict[str, object] | None = None,
    completed_restore_epoch_limit: int = 0,
) -> dict[str, object] | None:
    """Extract one unresolved route from facts discarded by exact restore."""
    history_index = _checkpoint_history_index(checkpoint, history)
    if history_index is None or not isinstance(checkpoint, dict):
        return None
    restore_positions: list[int] = []
    for position in range(history_index, len(history)):
        row = history[position]
        step, _result = _effective_native_history_entry(row)
        if (
            step == _RESTORE_CHECKPOINT_STEP
            and row.get("ok") is True
        ):
            restore_positions.append(position)
    branch_start = (
        restore_positions[-1] + 1 if restore_positions else history_index
    )
    failure = _derive_rollback_war_failure_from_epoch(
        history[branch_start:],
        checkpoint=checkpoint,
        restored_snapshot=restored_snapshot,
        episode_run_id=episode_run_id,
        abandoned_snapshot=abandoned_snapshot,
    )
    if failure is not None or completed_restore_epoch_limit <= 0:
        return failure
    completed = _derive_completed_rollback_war_failures(
        history,
        checkpoint=checkpoint,
        restored_snapshot=restored_snapshot,
        episode_run_id=episode_run_id,
        completed_restore_epoch_limit=completed_restore_epoch_limit,
    )
    return completed[0] if completed else None


def _derive_completed_rollback_war_failures(
    history: list[dict[str, object]],
    *,
    checkpoint: object,
    restored_snapshot: dict[str, object],
    episode_run_id: object,
    completed_restore_epoch_limit: int,
) -> list[dict[str, object]]:
    """Read newest completed restore epochs without crossing the fixed bound."""
    history_index = _checkpoint_history_index(checkpoint, history)
    if (
        history_index is None
        or not isinstance(checkpoint, dict)
        or completed_restore_epoch_limit <= 0
    ):
        return []
    restore_positions: list[int] = []
    for position in range(history_index, len(history)):
        row = history[position]
        step, _result = _effective_native_history_entry(row)
        if step == _RESTORE_CHECKPOINT_STEP and row.get("ok") is True:
            restore_positions.append(position)

    failures: list[dict[str, object]] = []
    for restore_offset in range(
        len(restore_positions) - 1,
        max(-1, len(restore_positions) - 1 - completed_restore_epoch_limit),
        -1,
    ):
        epoch_end = restore_positions[restore_offset]
        epoch_start = (
            restore_positions[restore_offset - 1] + 1
            if restore_offset > 0
            else history_index
        )
        failure = _derive_rollback_war_failure_from_epoch(
            history[epoch_start:epoch_end],
            checkpoint=checkpoint,
            restored_snapshot=restored_snapshot,
            episode_run_id=episode_run_id,
        )
        if failure is not None:
            failures.append(failure)
    return _bounded_rollback_war_failures(failures)


def _derive_rollback_war_failure_from_epoch(
    rows: list[dict[str, object]],
    *,
    checkpoint: dict[str, object],
    restored_snapshot: dict[str, object],
    episode_run_id: object,
    abandoned_snapshot: dict[str, object] | None = None,
) -> dict[str, object] | None:
    previews: dict[tuple[int, int], dict[str, object]] = {}
    successful_moves: list[tuple[int, int, dict[str, object]]] = []
    latest_armies: dict[int, dict[str, object]] = {}
    failed_move: tuple[int, int, dict[str, object]] | None = None
    for row in rows:
        step, result = _effective_native_history_entry(row)
        if row.get("ok") is not True or not isinstance(result, dict):
            continue
        parsed_preview = parse_preview_move_army_step(step)
        preview = result.get("route_preview")
        if (
            parsed_preview is not None
            and isinstance(preview, dict)
            and preview.get("status") == "available"
            and preview.get("army_id") == parsed_preview[0]
            and preview.get("target_province_id") == parsed_preview[1]
            and _positive_native_id(preview.get("origin_province_id"))
            and _valid_native_route(preview.get("route_province_ids"))
        ):
            previews[parsed_preview] = preview
        parsed_move = parse_move_army_step(step)
        action = result.get("war_action")
        if parsed_move is not None and isinstance(action, dict):
            if action.get("status") in {"move_submitted", "moving"}:
                matching_preview = previews.get(parsed_move)
                fresh_preview = bool(
                    matching_preview
                    and action.get("army_id") == parsed_move[0]
                    and action.get("target_province_id") == parsed_move[1]
                    and action.get("submitted_date_raw")
                    == matching_preview.get("previewed_date_raw")
                )
                failed_move = (
                    (*parsed_move, matching_preview)
                    if fresh_preview and matching_preview is not None
                    else None
                )
                if failed_move is not None:
                    successful_moves.append(failed_move)
            elif action.get("status") == "arrived":
                failed_move = None
        for army in _result_army_observations(result):
            army_id = army.get("army_id")
            if _positive_native_id(army_id):
                latest_armies[int(army_id)] = army
    if failed_move is None:
        return None
    move_army_id, move_target_id, preview = failed_move

    active_army = (
        _army_by_id(abandoned_snapshot, move_army_id)
        if isinstance(abandoned_snapshot, dict)
        else latest_armies.get(move_army_id)
    )
    active_route = (
        active_army.get("route_province_ids")
        if isinstance(active_army, dict)
        else None
    )
    if not (
        isinstance(active_army, dict)
        and active_army.get("move_target_province_id") == move_target_id
        and _valid_native_route(active_route)
    ):
        return None

    terminal_route = preview.get("route_province_ids")
    terminal_route_origin = preview.get("origin_province_id")
    if not (
        _valid_native_route(terminal_route)
        and _positive_native_id(terminal_route_origin)
    ):
        return None

    restored_army = _army_by_id(restored_snapshot, move_army_id)
    restored_origin = (
        restored_army.get("current_province_id")
        if isinstance(restored_army, dict)
        else None
    )
    war_id = _war_id_for_army(restored_snapshot, move_army_id)
    checkpoint_sha256 = checkpoint.get("sha256")
    if not (
        isinstance(episode_run_id, str)
        and episode_run_id
        and _positive_native_id(restored_origin)
        and war_id is not None
        and isinstance(checkpoint_sha256, str)
        and len(checkpoint_sha256) == 64
    ):
        return None

    entry_move = next(
        (
            candidate
            for candidate in successful_moves
            if candidate[0] == move_army_id
            and candidate[2].get("origin_province_id") == restored_origin
        ),
        None,
    )
    if entry_move is None:
        return None
    _entry_army_id, entry_target_id, entry_preview = entry_move
    entry_route = entry_preview.get("route_province_ids")
    entry_route_origin = entry_preview.get("origin_province_id")
    if not (
        _valid_native_route(entry_route)
        and entry_route_origin == restored_origin
    ):
        return None
    failure = {
        "status": "rolled_back_active_route",
        "source": "checkpoint_discarded_branch",
        "episode_run_id": episode_run_id,
        "checkpoint_sha256": checkpoint_sha256,
        "checkpoint_date_raw": checkpoint.get("date_raw"),
        "war_id": war_id,
        "army_id": move_army_id,
        "restored_origin_province_id": int(restored_origin),
        "target_province_id": entry_target_id,
        "route_origin_province_id": int(entry_route_origin),
        "route_province_ids": list(entry_route),
        "previewed_date_raw": entry_preview.get("previewed_date_raw"),
        "terminal_failure_target_province_id": move_target_id,
        "terminal_failure_route_origin_province_id": int(
            terminal_route_origin
        ),
        "terminal_failure_route_province_ids": list(terminal_route),
        "abandoned_date_raw": (
            abandoned_snapshot.get("date_raw")
            if isinstance(abandoned_snapshot, dict)
            else None
        ),
        "restored_date_raw": restored_snapshot.get("date_raw"),
    }
    return _normalize_rollback_war_failure(failure)


def _normalize_rollback_war_failure(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict) or value.get("status") != "rolled_back_active_route":
        return None
    required_ids = (
        "war_id",
        "army_id",
        "restored_origin_province_id",
        "target_province_id",
        "route_origin_province_id",
    )
    if any(not _positive_native_id(value.get(name)) for name in required_ids):
        return None
    if value.get("route_origin_province_id") != value.get(
        "restored_origin_province_id"
    ):
        return None
    route = value.get("route_province_ids")
    if not _valid_native_route(route):
        return None
    terminal_target = value.get("terminal_failure_target_province_id")
    terminal_origin = value.get("terminal_failure_route_origin_province_id")
    terminal_route = value.get("terminal_failure_route_province_ids")
    has_terminal_diagnostics = any(
        name in value
        for name in (
            "terminal_failure_target_province_id",
            "terminal_failure_route_origin_province_id",
            "terminal_failure_route_province_ids",
        )
    )
    if has_terminal_diagnostics and not (
        _positive_native_id(terminal_target)
        and _positive_native_id(terminal_origin)
        and _valid_native_route(terminal_route)
    ):
        return None
    run_id = value.get("episode_run_id")
    digest = value.get("checkpoint_sha256")
    if not (
        isinstance(run_id, str)
        and run_id
        and isinstance(digest, str)
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return None
    normalized = copy.deepcopy(value)
    normalized["route_province_ids"] = list(route)
    if has_terminal_diagnostics and isinstance(terminal_route, list):
        normalized["terminal_failure_route_province_ids"] = list(
            terminal_route
        )
    return normalized


def _rollback_war_failure_scope(
    failure: dict[str, object],
) -> tuple[object, object, object, object, object]:
    return (
        failure.get("episode_run_id"),
        failure.get("checkpoint_sha256"),
        failure.get("war_id"),
        failure.get("army_id"),
        failure.get("restored_origin_province_id"),
    )


def _bounded_rollback_war_failures(
    *groups: object,
) -> list[dict[str, object]]:
    """Merge newest-first advisories within one exact restored scope."""
    merged: list[dict[str, object]] = []
    scope: tuple[object, object, object, object, object] | None = None
    seen_routes: set[tuple[object, tuple[object, ...]]] = set()
    for group in groups:
        values = group if isinstance(group, list) else [group]
        for value in values:
            failure = _normalize_rollback_war_failure(value)
            if failure is None:
                continue
            failure_scope = _rollback_war_failure_scope(failure)
            if scope is None:
                scope = failure_scope
            elif failure_scope != scope:
                continue
            route = failure.get("route_province_ids")
            assert isinstance(route, list)
            dedupe_key = (failure.get("target_province_id"), tuple(route))
            if dedupe_key in seen_routes:
                continue
            seen_routes.add(dedupe_key)
            merged.append(failure)
            if len(merged) >= _MAX_ROLLBACK_WAR_FAILURES:
                return merged
    return merged


def _rollback_war_failure_scope_snapshot(
    failure: dict[str, object],
) -> dict[str, object]:
    """Build only the exact public facts needed for legacy epoch extraction."""
    army_id = int(failure["army_id"])
    war_id = int(failure["war_id"])
    origin = int(failure["restored_origin_province_id"])
    army = {
        "army_id": army_id,
        "current_province_id": origin,
        "move_target_province_id": None,
        "route_province_ids": [],
        "army_state": "regular",
        "controllable": True,
    }
    return {
        "date_raw": failure.get(
            "restored_date_raw", failure.get("checkpoint_date_raw")
        ),
        "player_armies": [army],
        "active_wars": [
            {
                "war_id": war_id,
                "allied_armies": [army],
            }
        ],
    }


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
