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
import secrets
import shutil
import struct
import threading
import time
from typing import Protocol
import uuid

from ..environment import write_bytes_atomic, write_json_atomic
from .driver import (
    BridgeUnavailableError,
    GameplayBridgeDriver,
    HybridGameplayDriver,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
    UnsupportedStepError,
)
from .session_queue import SESSION_QUEUE_PROTOCOL_VERSION
from .event_contract import (
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
    parse_event_option_step,
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
from .battle_control_contract import (
    BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC,
    BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX,
    normalize_battle_control_snapshot_v1,
    parse_query_battle_control_snapshot_v1_step,
    query_battle_control_snapshot_v1_step,
)
from .battle_transition_contract import (
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
    QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX,
    normalize_battle_transition_v1,
    parse_query_battle_transition_v1_step,
)
from .battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX,
    normalize_battle_terminal_transition_v1,
    parse_query_battle_terminal_transition_v1_step,
)
from .battle_reinforcement_assignment_contract import (
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX,
    normalize_battle_reinforcement_assignment_v1,
    parse_query_battle_reinforcement_assignment_v1_step,
    query_battle_reinforcement_assignment_v1_step,
)
from .campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
    normalize_campaign_root_context_v1,
)
from .zhongguo_case_snapshot_contract import (
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoCaseQueryV1,
    normalize_native_zhongguo_case_snapshot_v1,
    parse_query_zhongguo_case_snapshot_v1_step,
)
from .zhongguo_ai_owned_case_snapshot_contract import (
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoAiOwnedCaseQueryV1,
    normalize_native_zhongguo_ai_owned_case_snapshot_v1,
    parse_query_zhongguo_ai_owned_case_snapshot_v1_step,
)
from .zhongguo_result_case_snapshot_contract import (
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoResultCaseQueryV1,
    normalize_native_zhongguo_result_case_snapshot_v1,
    parse_query_zhongguo_result_case_snapshot_v1_step,
)
from .zhongguo_b2_pip_snapshot_contract import (
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoB2PipQueryV1,
    normalize_native_zhongguo_b2_pip_snapshot_v1,
    parse_query_zhongguo_b2_pip_snapshot_v1_step,
)
from .zhongguo_promotion_compensation_postcondition_contract import (
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP,
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX,
    ZhongguoPromotionCompensationQueryV1,
    normalize_native_zhongguo_promotion_compensation_v1,
    parse_query_zhongguo_promotion_compensation_v1_step,
)
from .zhongguo_projects_metrics_postcondition_contract import (
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP,
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX,
    ZhongguoProjectsMetricsQueryV1,
    normalize_native_zhongguo_projects_metrics_v1,
    parse_query_zhongguo_projects_metrics_v1_step,
)
from .zhongguo_workforce_collective_snapshot_contract import (
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoWorkforceCollectiveQueryV1,
    normalize_native_zhongguo_workforce_collective_snapshot_v1,
    parse_query_zhongguo_workforce_collective_snapshot_v1_step,
)
from .zhongguo_workforce_normal_exit_snapshot_contract import (
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoWorkforceNormalExitQueryV1,
    normalize_native_zhongguo_workforce_normal_exit_snapshot_v1,
    parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step,
)
from .zhongguo_incident_snapshot_contract import (
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoIncidentQueryV1,
    normalize_native_zhongguo_incident_snapshot_v1,
    parse_query_zhongguo_incident_snapshot_v1_step,
)
from .zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP,
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX,
    ZhongguoManagerGovernanceQueryV1,
    normalize_native_zhongguo_manager_governance_snapshot_v1,
    parse_query_zhongguo_manager_governance_snapshot_v1_step,
)
from .zhongguo_scoreboard_state_contract import (
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX,
    ZhongguoScoreboardStateQueryV1,
    normalize_native_zhongguo_scoreboard_state_v1,
    parse_query_zhongguo_scoreboard_state_v1_step,
)
from .zhongguo_scoreboard_action_contract import (
    ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY,
    ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
    ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY,
    ZhongguoScoreboardActionRequestV1,
    normalize_native_zhongguo_scoreboard_action_v1_result,
)
from .title_map_navigation_contract import (
    CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY,
    CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
    TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
    TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
    TITLE_MAP_NAVIGATION_V1_REJECTION_CODES,
    normalize_native_title_map_navigation_v1_result,
    normalize_title_map_navigation_v1_binding,
    normalize_title_map_navigation_v1_result,
    validate_landed_title_key,
)
from .loaded_feature_manifest_contract import (
    QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
    QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
    normalize_loaded_feature_manifest_v1,
)
from .event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from .pending_character_interaction_context_contract import (
    ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    normalize_pending_interaction_id,
    normalize_pending_character_interaction_context_v1,
)
from .active_combat_retreat_contract import (
    ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE,
    ORDER_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX,
    PREVIEW_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX,
    normalize_active_combat_retreat_v1_order_ack,
    normalize_active_combat_retreat_v1_preview,
    order_active_combat_retreat_v1_step,
    parse_order_active_combat_retreat_v1_step,
    parse_preview_active_combat_retreat_v1_step,
    preview_active_combat_retreat_v1_step,
)
from .war_contract import (
    ARMY_ROUTES_CAPABILITY,
    BATTLE_DECISION_EPOCH_ADVANCE_STEP,
    BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX,
    BATTLE_SENTINEL_ADVANCE_STEPS,
    BATTLE_TERMINAL_CRUISE_STEP,
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX,
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX,
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
    offer_white_peace_step,
    parse_disband_army_step,
    parse_battle_decision_epoch_advance_step,
    parse_committed_route_sentinel_advance_speed,
    parse_committed_route_sentinel_advance_step,
    parse_war_objective_hold_sentinel_advance_speed,
    parse_war_objective_hold_sentinel_advance_step,
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
    stationary_province_contact_free_in_horizon,
    split_army_half_step,
    start_assault_step,
    stop_assault_step,
    unavoidable_current_province_contact_in_horizon,
    war_objective_province_ids,
    war_termination_active_war_signature,
    war_termination_negative_query_signature,
)
from .raiktor_surrender_public_aggregate import (
    project_raiktor_surrender_six_domain,
)
from .raiktor_war_bound_regiment_contract import (
    bind_raiktor_war_bound_regiment_public_frame,
)
from .raiktor_surrender_session_binding_contract import (
    bind_raiktor_surrender_aggregate_session,
)


PROTOCOL_VERSION = 1
MAXIMUM_FRAME_BYTES = 1024 * 1024
DEFAULT_PIPE_NAME = r"\\.\pipe\xar_ck3_bridge_mcp"
_ACTION_CAPABILITY_PREFIX = "game.command."
_NATIVE_LIFE_ADVANCE_PRIMITIVES = frozenset(
    {
        "set-speed-1",
        "set-speed-3",
        "set-speed-5",
        "resume-map",
        "pause-map",
    }
)
_NATIVE_EXACT_DAY_ADVANCE_PRIMITIVES = frozenset(
    {"set-speed-1", "resume-map", "pause-map"}
)
DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED = 3
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
_PHASE2_SOURCE_CHECKPOINT_STAGE_STEP = (
    "restore-phase2-span-source-checkpoint-v1"
)
_CHECKPOINT_ANCHOR_STEPS = frozenset(
    {"save-checkpoint", _PHASE2_SOURCE_CHECKPOINT_STAGE_STEP}
)
_MANAGED_RESTORE_TRANSACTION_STATUS = "awaiting_checkpoint_rebind"
_START_NEXT_EPISODE_STEP = "start-next-episode"
_WHITE_PEACE_PROPOSAL_COOLDOWN_RAW = 30 * 24
_COLD_RESTORE_SOURCE = "native-session-cold-start"
_RESTORE_MAP_STABLE_SECONDS = 0.5
_NATIVE_WAR_ADVANCE_MAX_DAYS = 30
_NATIVE_SIEGE_ADVANCE_MAX_DAYS = 7
_NATIVE_ASSAULT_ADVANCE_MAX_DAYS = 1
_NATIVE_ACTIVE_ROUTE_ADVANCE_MAX_DAYS = 1
_NATIVE_COMBAT_RETREAT_ADVANCE_MAX_DAYS = 1
_LIFE_ADVANCE_TIMELINE_RETRY_SECONDS = 1.0
_TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY = (
    "game.command.research-arm-tactical-daily-sentinel-v1-N"
)
_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY = (
    "game.command.research-query-tactical-daily-sentinel-v1"
)
_TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY = (
    "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N"
)
_TACTICAL_DAILY_SENTINEL_STATUS_STEP = (
    "research-query-tactical-daily-sentinel-v1"
)
_TACTICAL_DAILY_SENTINEL_ARM_PREFIX = (
    "research-arm-tactical-daily-sentinel-v1-"
)
_TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX = (
    "research-cancel-tactical-daily-sentinel-v1-generation-"
)
_TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES = frozenset(
    {
        _TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY,
        _TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY,
    }
)
_BATTLE_SENTINEL_FALLBACK_DAYS = 45
_BATTLE_SENTINEL_MAXIMUM_ARMIES = 64
_BATTLE_SPEED_READINESS = {
    "decision_sentinel_live_ready": True,
    "committed_route_sentinel_live_ready": True,
    "stationary_objective_hold_sentinel_live_ready": True,
    # Deprecated compatibility alias. Production readiness no longer depends
    # on the old CLI canary flag.
    "stationary_objective_hold_sentinel_canary_ready": True,
    "committed_route_sentinel_speed_4_live_ready": False,
    "committed_route_sentinel_speed_5_live_ready": False,
    "stationary_objective_hold_sentinel_speed_4_live_ready": False,
    "stationary_objective_hold_sentinel_speed_5_live_ready": False,
    "terminal_sentinel_live_ready": True,
    # The native stop envelope is live, but no overwhelming active-battle
    # checkpoint has yet passed the required balanced speed matrix.  Strategy
    # therefore keeps the speed-five crush selector closed.
    "overwhelming_matrix_live_ready": False,
}


def _noncombat_sentinel_scope_speed_live_ready(
    sentinel_scope: str,
    speed: int,
) -> bool:
    if speed <= 3:
        return True
    prefix = {
        "committed_route": "committed_route_sentinel",
        "stationary_objective_hold": "stationary_objective_hold_sentinel",
    }.get(sentinel_scope)
    return bool(
        prefix is not None
        and _BATTLE_SPEED_READINESS.get(
            f"{prefix}_speed_{speed}_live_ready"
        )
        is True
    )
_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS = (
    "date_deadline",
    "army_unavailable",
    "route_target_changed",
    "combat_transition",
    "retreat_transition",
    "combat_unavailable",
    "combat_phase_changed",
    "combat_roster_changed",
    "combat_terminal",
    "date_sequence_failure",
    "world_identity_changed",
    "pause_not_observed",
    "original_unavailable",
    "native_pause",
    "combat_winner_changed",
    "evaluation_failure",
)
_BATTLE_CONTROL_TRANSIENT_QUERY_ERROR = (
    "CK3 battle-control state changed during query"
)
_BATTLE_CONTROL_IDENTITY_PENDING_QUERY_ERROR = (
    f"{_BATTLE_CONTROL_TRANSIENT_QUERY_ERROR} "
    f"({BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC})"
)
_BATTLE_CONTROL_QUERY_MAX_ATTEMPTS = 3
_ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES = frozenset(
    {
        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
        PREVIEW_MOVE_ARMY_CAPABILITY,
        MOVE_ARMY_CAPABILITY,
    }
)
_ARMY_MOVE_DEFERRED_ERROR_STAGES = {
    # Kept for protocol-v1 bridges built before the native rejection stages
    # were split.
    "CK3 army cannot move to the destination": "legacy_unclassified",
    "CK3 army has no move mode for the destination": "move_mode_unavailable",
    "CK3 army state rejects movement": "army_state_rejected",
}
_ARMY_MOVE_DEFERRED_ERRORS = frozenset(_ARMY_MOVE_DEFERRED_ERROR_STAGES)
_WAR_TERMINATION_REVISION_RETRY_ERRORS = frozenset(
    {
        "war-termination snapshot revision is stale",
        "war-termination admission snapshot changed; retry after heartbeat",
        "war-termination completion snapshot changed; retry after heartbeat",
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
        self._rejected_state_snapshot_count = 0
        self._last_rejected_state_snapshot: dict[str, object] | None = None
        self._snapshot_publish_diagnostic_count = 0
        self._last_snapshot_publish_diagnostic: dict[str, object] | None = None

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
                try:
                    snapshot = _semantic_snapshot_from_frame(frame)
                except ValueError as error:
                    state = frame.get("state")
                    state_summary = state if isinstance(state, dict) else {}
                    self._rejected_state_snapshot_count += 1
                    self._last_rejected_state_snapshot = {
                        "snapshot_id": frame.get("snapshot_id"),
                        "revision": frame.get("revision"),
                        "date_raw": state_summary.get("date_raw"),
                        "speed": state_summary.get("speed"),
                        "paused": state_summary.get("paused"),
                        "map_ready": state_summary.get("map_ready"),
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                    self._condition.notify_all()
                    return "state_snapshot_rejected"
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
            elif frame_type == "snapshot_publish_diagnostic":
                request_id = frame.get("request_id")
                phase = frame.get("phase")
                status = frame.get("status")
                revision = frame.get("revision")
                payload_bytes = frame.get("payload_bytes")
                if (
                    not isinstance(request_id, str)
                    or not request_id
                    or phase not in {"begin", "end"}
                    or not isinstance(status, str)
                    or not status
                    or isinstance(revision, bool)
                    or not isinstance(revision, int)
                    or revision < 0
                    or isinstance(payload_bytes, bool)
                    or not isinstance(payload_bytes, int)
                    or payload_bytes < 0
                ):
                    raise ValueError(
                        "native snapshot_publish_diagnostic is malformed"
                    )
                self._snapshot_publish_diagnostic_count += 1
                self._last_snapshot_publish_diagnostic = dict(frame)
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
        private_observers: dict[str, object] = {}
        if isinstance(heartbeat, dict):
            preview_observer = heartbeat.get(
                "g2_truce_preview_entry_observer_v1"
            )
            if isinstance(preview_observer, dict):
                # Keep private native evidence available to diagnostics and
                # MCP inspection without adding it to bridge capabilities or
                # making it a routable gameplay step.
                private_observers[
                    "g2_truce_preview_entry_observer_v1"
                ] = dict(preview_observer)
        return {
            "protocol_version": PROTOCOL_VERSION,
            "pipe_name": self.pipe_name,
            "connected": self._connected,
            "connection_generation": self._connection_generation,
            "bridge_pid": hello.get("pid") if hello else None,
            "bridge_version": hello.get("bridge_version") if hello else None,
            "hello": hello,
            "last_heartbeat": heartbeat,
            "private_observers": private_observers,
            "last_pong": pong,
            "last_error": dict(self._last_error) if self._last_error else None,
            "semantic_state_available": self._semantic_snapshot is not None,
            "rejected_state_snapshot_count": (
                self._rejected_state_snapshot_count
            ),
            "last_rejected_state_snapshot": (
                dict(self._last_rejected_state_snapshot)
                if self._last_rejected_state_snapshot
                else None
            ),
            "snapshot_publish_diagnostic_count": (
                self._snapshot_publish_diagnostic_count
            ),
            "last_snapshot_publish_diagnostic": (
                dict(self._last_snapshot_publish_diagnostic)
                if self._last_snapshot_publish_diagnostic
                else None
            ),
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


def load_native_driver_state_for_resume(
    path: Path, pipe_name: str
) -> dict[str, object] | None:
    """Read one driver state through the exact cold-consumer contract."""
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("driver state must be a JSON object")
    format_version = payload.get("format_version")
    if format_version not in (1, _NATIVE_DRIVER_STATE_VERSION):
        return None
    if payload.get("pipe_name") != pipe_name:
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
    # Historical timeline rows only need objective-state detail for an
    # actually active siege.  Normalize the in-memory copy exactly as the
    # live consumer does; this helper never writes the source artifact.
    _compact_war_progress_history_in_place(history)
    last_checkpoint = payload.get("last_checkpoint")
    if last_checkpoint is not None and not isinstance(last_checkpoint, dict):
        raise ValueError("driver state checkpoint is malformed")
    plural_present = "rollback_war_failures" in payload
    persisted_plural = payload.get("rollback_war_failures")
    if plural_present and not isinstance(persisted_plural, list):
        raise ValueError("driver state rollback_war_failures is malformed")
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
        and failure.get("checkpoint_sha256") == last_checkpoint.get("sha256")
        and failure.get("episode_run_id") == run_id
    ]
    migration_required = bool(
        not plural_present
        and isinstance(last_checkpoint, dict)
        and isinstance(run_id, str)
        and run_id
    )
    if migration_required and rollback_war_failures:
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
    managed_restore_transaction = _normalize_managed_restore_transaction(
        payload.get("managed_restore_transaction"),
        checkpoint=last_checkpoint,
        history=history,
        bridge_pid=persisted_bridge_pid,
        episode_character_id=character_id,
        episode_run_id=run_id,
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
        "rollback_war_failures": copy.deepcopy(rollback_war_failures),
        "rollback_war_failures_migration_required": migration_required,
        "managed_restore_transaction": managed_restore_transaction,
    }


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
        route_contact_timeline_speed: int = (
            DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED
        ),
        allow_route_contact_high_speed_ab: bool = False,
        allow_stationary_objective_hold_sentinel_canary: bool = False,
    ) -> None:
        self.pipe_name = _validate_pipe_name(pipe_name)
        self.command_timeout_seconds = _positive_seconds(
            command_timeout_seconds, "command_timeout_seconds"
        )
        self.life_advance_timeout_seconds = _positive_seconds(
            life_advance_timeout_seconds, "life_advance_timeout_seconds"
        )
        self.route_contact_timeline_speed = _timeline_speed(
            route_contact_timeline_speed,
            "route_contact_timeline_speed",
        )
        if (
            self.route_contact_timeline_speed > 3
            and allow_route_contact_high_speed_ab is not True
            and not any(
                _noncombat_sentinel_scope_speed_live_ready(
                    scope,
                    self.route_contact_timeline_speed,
                )
                for scope in (
                    "committed_route",
                    "stationary_objective_hold",
                )
            )
        ):
            raise ValueError(
                "route_contact_timeline_speed 4..5 requires "
                "allow_route_contact_high_speed_ab=True"
            )
        self.allow_route_contact_high_speed_ab = (
            allow_route_contact_high_speed_ab is True
        )
        # Scope-specific sentinel readiness may admit its own requested speed,
        # but it must never leak that admission into the exact route-contact
        # transaction. Route-contact speed 4/5 remains explicit-A/B only.
        self.route_contact_effective_timeline_speed = (
            self.route_contact_timeline_speed
            if (
                self.route_contact_timeline_speed <= 3
                or self.allow_route_contact_high_speed_ab
            )
            else 3
        )
        self.allow_stationary_objective_hold_sentinel_canary = (
            allow_stationary_objective_hold_sentinel_canary is True
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
        self._phase2_source_restore_lock = threading.Lock()
        self._driver_state_dirty = False
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
        self._battle_control_snapshot_v1_query: dict[str, object] | None = None
        self._active_combat_retreat_v1_token: dict[str, object] | None = None
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
        # The native arm capability is a parameterized protocol template,
        # never a directly executable action literal.  Only the bounded
        # Python composites below materialize a concrete arm command.
        action_steps.discard(
            _TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY.removeprefix(
                _ACTION_CAPABILITY_PREFIX
            )
        )
        bridge_capabilities = set(
            _string_list(result.get("bridge_capabilities"))
        )
        with self._driver_state_lock:
            declarations = copy.deepcopy(self._declarable_wars)
            marriage_choices = copy.deepcopy(self._arrange_marriage_choices)
            active_retreat_token = copy.deepcopy(
                self._active_combat_retreat_v1_token
            )
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
        sentinel_watch_army_ids = _battle_sentinel_watch_army_ids(
            current_snapshot
        )
        if (
            result.get("snapshot") is True
            and result.get("wait_for_change") is True
            and _TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES
            <= bridge_capabilities
            and isinstance(current_snapshot, dict)
            and current_snapshot.get("paused") is True
            and current_snapshot.get("map_ready") is True
            and current_snapshot.get("active_event") is None
            and current_snapshot.get("pending_character_interaction") is None
            and sentinel_watch_army_ids is not None
            and {"resume-map", "pause-map"} <= action_steps
        ):
            if "set-speed-3" in action_steps:
                action_steps.add(BATTLE_DECISION_EPOCH_ADVANCE_STEP)
                composite_action_steps.append(
                    BATTLE_DECISION_EPOCH_ADVANCE_STEP
                )
            noncombat_sentinel_speed_step = (
                f"set-speed-{self.route_contact_timeline_speed}"
            )
            high_speed_ab = self.allow_route_contact_high_speed_ab
            committed_route_speed_ready = bool(
                high_speed_ab
                or _noncombat_sentinel_scope_speed_live_ready(
                    "committed_route",
                    self.route_contact_timeline_speed,
                )
            )
            objective_hold_speed_ready = bool(
                high_speed_ab
                or _noncombat_sentinel_scope_speed_live_ready(
                    "stationary_objective_hold",
                    self.route_contact_timeline_speed,
                )
            )
            if (
                noncombat_sentinel_speed_step in action_steps
                and committed_route_speed_ready
            ):
                action_steps.add(COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP)
                composite_action_steps.append(
                    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP
                )
            if (
                noncombat_sentinel_speed_step in action_steps
                and objective_hold_speed_ready
            ):
                action_steps.add(
                    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP
                )
                composite_action_steps.append(
                    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP
                )
            if "set-speed-5" in action_steps:
                action_steps.add(BATTLE_TERMINAL_CRUISE_STEP)
                composite_action_steps.append(BATTLE_TERMINAL_CRUISE_STEP)
        active_retreat_composition_supported = bool(
            _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES
            <= bridge_capabilities
        )
        active_retreat_token_ready = False
        if (
            active_retreat_composition_supported
            and isinstance(current_snapshot, dict)
            and current_snapshot.get("paused") is True
        ):
            preview_steps = _active_combat_retreat_preview_steps(
                current_snapshot, action_steps
            )
            action_steps.update(preview_steps)
            composite_action_steps.extend(sorted(preview_steps))
            if _active_combat_retreat_token_matches_snapshot(
                active_retreat_token, current_snapshot
            ):
                with self._driver_state_lock:
                    token_still_current = (
                        self._active_combat_retreat_v1_token
                        == active_retreat_token
                    )
                order_step = active_retreat_token.get("order_step")
                if token_still_current and isinstance(order_step, str):
                    action_steps.add(order_step)
                    composite_action_steps.append(order_step)
                    active_retreat_token_ready = True
        proof_steps: set[str] = set()
        white_peace_steps: set[str] = set()
        # These helpers only read history.  Evaluate them while holding the
        # owning lock so capability projection neither deep-copies the full
        # transcript nor exposes the internal list outside this critical
        # section.
        with self._history_lock:
            if (
                QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY
                in bridge_capabilities
                and _NATIVE_EXACT_DAY_ADVANCE_PRIMITIVES <= action_steps
                and isinstance(current_snapshot, dict)
            ):
                proof_steps = _fresh_route_contact_advance_steps(
                    current_snapshot, self._command_history
                )
            if (
                isinstance(current_snapshot, dict)
                and {
                    QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
                    QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
                    OFFER_WHITE_PEACE_CAPABILITY,
                }
                <= bridge_capabilities
            ):
                for war in current_snapshot.get("active_wars", []):
                    if not isinstance(war, dict) or not _positive_native_id(
                        war.get("war_id")
                    ):
                        continue
                    war_id = int(war["war_id"])
                    ready, _, _ = _claim_cb_white_peace_readiness(
                        current_snapshot, war_id
                    )
                    cooldown = _white_peace_proposal_cooldown(
                        self._command_history,
                        war_id=war_id,
                        current_date_raw=current_snapshot.get("date_raw"),
                        episode_run_id=current_snapshot.get("episode_run_id"),
                    )
                    if ready and cooldown is None:
                        white_peace_steps.add(offer_white_peace_step(war_id))
        if proof_steps:
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
        # Owner-authorized minimal claim_cb counter-policy.  This is narrower
        # than the frozen native/v2 exit tree: only a same-frame, recipient-
        # accepted, claim-preserving white peace can become a literal action.
        action_steps.update(white_peace_steps)
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
            "battle_speed_readiness": {
                **_BATTLE_SPEED_READINESS,
                "stationary_objective_hold_legacy_canary_flag_requested": (
                    self.allow_stationary_objective_hold_sentinel_canary
                ),
                "noncombat_sentinel_timeline_speed": (
                    self.route_contact_timeline_speed
                ),
                "route_contact_effective_timeline_speed": (
                    self.route_contact_effective_timeline_speed
                ),
                "noncombat_sentinel_high_speed_ab": (
                    self.allow_route_contact_high_speed_ab
                ),
            },
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
            "battle_control_snapshot_v1_query_supported": (
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "battle_transition_v1_query_supported": (
                QUERY_BATTLE_TRANSITION_V1_CAPABILITY
                in bridge_capabilities
            ),
            "battle_terminal_transition_v1_query_supported": (
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
                in bridge_capabilities
            ),
            "battle_reinforcement_assignment_v1_query_supported": (
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "campaign_root_context_v1_query_supported": (
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_case_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_ai_owned_case_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_result_case_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_b2_pip_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_promotion_compensation_v1_query_supported": (
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_projects_metrics_v1_query_supported": (
                QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_workforce_collective_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_workforce_normal_exit_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_incident_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_manager_governance_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_scoreboard_state_v1_query_supported": (
                QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_scoreboard_action_v1_transport_wired": (
                ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_scoreboard_action_v1_supported": (
                ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY
                in bridge_capabilities
            ),
            "loaded_feature_manifest_v1_query_supported": (
                QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
                in bridge_capabilities
            ),
            "pending_character_interaction_context_v1_query_supported": (
                QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "current_event_window_context_v1_query_supported": (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "active_combat_retreat_v1_composition_supported": (
                active_retreat_composition_supported
            ),
            "active_combat_retreat_v1_token_ready": (
                active_retreat_token_ready
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

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        """Read a runner-internal semantic frame without transcript evidence."""
        transport_error = self._transport_error()
        if transport_error is not None:
            raise BridgeUnavailableError(transport_error)
        snapshot = self._with_one_life_episode(self.state.semantic_snapshot())
        self._observe_arrange_marriage_outcome(snapshot)
        return snapshot

    def _with_internal_planning_view(
        self,
        snapshot: dict[str, object],
        planner: Callable[
            [dict[str, object], list[dict[str, object]]],
            dict[str, object],
        ],
    ) -> dict[str, object]:
        """Run the in-process planner against owned history without copying it."""
        with self._history_lock:
            rollback_war_failures = copy.deepcopy(
                self._rollback_war_failures
            )
            planning_snapshot = {
                **snapshot,
                "native_rollback_war_failure": (
                    copy.deepcopy(rollback_war_failures[0])
                    if rollback_war_failures
                    else None
                ),
                "native_rollback_war_failures": rollback_war_failures,
            }
            # The callback is the local one-step planner.  Keeping it inside
            # this lock prevents concurrent history mutation, and the view is
            # never returned through the public snapshot/MCP surface.
            return copy.deepcopy(
                planner(planning_snapshot, self._command_history)
            )

    def take_snapshot(self) -> dict[str, object]:
        snapshot = self.take_internal_semantic_snapshot()
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
        battle_control_snapshot_v1_query = (
            self._battle_control_snapshot_v1_cache_for_snapshot(
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
            "battle_control_snapshot_v1_query_supported": (
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "battle_transition_v1_query_supported": (
                QUERY_BATTLE_TRANSITION_V1_CAPABILITY
                in bridge_capabilities
            ),
            "battle_terminal_transition_v1_query_supported": (
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
                in bridge_capabilities
            ),
            "battle_reinforcement_assignment_v1_query_supported": (
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "campaign_root_context_v1_query_supported": (
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_case_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_ai_owned_case_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_result_case_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_b2_pip_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_promotion_compensation_v1_query_supported": (
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_projects_metrics_v1_query_supported": (
                QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_workforce_collective_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_workforce_normal_exit_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_incident_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_manager_governance_snapshot_v1_query_supported": (
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_scoreboard_state_v1_query_supported": (
                QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_scoreboard_action_v1_transport_wired": (
                ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY
                in bridge_capabilities
            ),
            "zhongguo_scoreboard_action_v1_supported": (
                ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY
                in bridge_capabilities
            ),
            "loaded_feature_manifest_v1_query_supported": (
                QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
                in bridge_capabilities
            ),
            "pending_character_interaction_context_v1_query_supported": (
                QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
                in bridge_capabilities
            ),
            "current_event_window_context_v1_query_supported": (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
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
            "battle_control_snapshot_v1": (
                copy.deepcopy(
                    battle_control_snapshot_v1_query.get(
                        "battle_control_snapshot"
                    )
                )
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_status": (
                battle_control_snapshot_v1_query.get("status")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_query_sequence": (
                battle_control_snapshot_v1_query.get("query_sequence")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_query_attempts": (
                battle_control_snapshot_v1_query.get("query_attempts")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_diagnostic_reason": (
                battle_control_snapshot_v1_query.get("diagnostic_reason")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_native_query_status": (
                battle_control_snapshot_v1_query.get("native_query_status")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_subject_army_id": (
                battle_control_snapshot_v1_query.get(
                    "subject_public_cunit_id"
                )
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_queried_snapshot_id": (
                battle_control_snapshot_v1_query.get("queried_snapshot_id")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_queried_revision": (
                battle_control_snapshot_v1_query.get("queried_revision")
                if isinstance(battle_control_snapshot_v1_query, dict)
                else None
            ),
            "battle_control_snapshot_v1_queried_native_revision": (
                battle_control_snapshot_v1_query.get(
                    "queried_native_revision"
                )
                if isinstance(battle_control_snapshot_v1_query, dict)
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
                        "queried_connection_generation": connection_generation,
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
                        "queried_connection_generation": connection_generation,
                        "raiktor_surrender_aggregate_session": copy.deepcopy(
                            cached["raiktor_surrender_aggregate_session"]
                        ),
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

    def _battle_control_snapshot_v1_cache_for_snapshot(
        self,
        snapshot: dict[str, object],
        *,
        episode_run_id: str | None,
    ) -> dict[str, object] | None:
        """Project only a battle observation bound to this paused revision."""
        if snapshot.get("paused") is not True:
            return None
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        with self._driver_state_lock:
            cached = self._battle_control_snapshot_v1_query
            if not isinstance(cached, dict):
                return None
            binding = cached.get("cache_binding")
            if cached.get("status") == BATTLE_CONTROL_IDENTITY_PENDING_STATUS:
                if not (
                    set(cached)
                    == {
                        "status",
                        "diagnostic_reason",
                        "native_query_status",
                        "query_attempts",
                        "cache_binding",
                    }
                    and cached.get("diagnostic_reason")
                    == BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
                    and cached.get("native_query_status") == "state_changed"
                    and cached.get("query_attempts")
                    == _BATTLE_CONTROL_QUERY_MAX_ATTEMPTS
                    and isinstance(binding, dict)
                    and set(binding)
                    == {
                        "native_revision",
                        "snapshot_id",
                        "revision",
                        "date_raw",
                        "connection_generation",
                        "episode_run_id",
                        "subject_public_cunit_id",
                    }
                ):
                    self._battle_control_snapshot_v1_query = None
                    return None
                subject = binding.get("subject_public_cunit_id")
                native_revision = binding.get("native_revision")
                revision = binding.get("revision")
                date_raw = binding.get("date_raw")
                current_subject = (
                    _army_by_id(snapshot, int(subject))
                    if _positive_native_id(subject)
                    else None
                )
                if not (
                    _positive_native_id(native_revision)
                    and isinstance(revision, int)
                    and not isinstance(revision, bool)
                    and revision >= 0
                    and isinstance(date_raw, int)
                    and not isinstance(date_raw, bool)
                    and binding.get("native_revision")
                    == snapshot.get("native_revision")
                    and binding.get("snapshot_id")
                    == snapshot.get("snapshot_id")
                    and binding.get("revision") == snapshot.get("revision")
                    and binding.get("date_raw") == snapshot.get("date_raw")
                    and binding.get("connection_generation")
                    == connection_generation
                    and binding.get("episode_run_id") == episode_run_id
                    and isinstance(current_subject, dict)
                    and current_subject.get("controllable") is True
                    and current_subject.get("in_combat") is True
                ):
                    self._battle_control_snapshot_v1_query = None
                    return None
                return {
                    "status": BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
                    "diagnostic_reason": (
                        BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
                    ),
                    "native_query_status": "state_changed",
                    "query_attempts": _BATTLE_CONTROL_QUERY_MAX_ATTEMPTS,
                    "subject_public_cunit_id": int(subject),
                    "queried_snapshot_id": snapshot.get("snapshot_id"),
                    "queried_revision": snapshot.get("revision"),
                    "queried_native_revision": snapshot.get(
                        "native_revision"
                    ),
                    "episode_run_id": episode_run_id,
                }
            query_sequence = cached.get("query_sequence")
            if not (
                set(cached)
                == {
                    "status",
                    "battle_control_snapshot",
                    "query_sequence",
                    "cache_binding",
                }
                and isinstance(binding, dict)
                and set(binding)
                == {
                    "native_revision",
                    "snapshot_id",
                    "revision",
                    "date_raw",
                    "connection_generation",
                    "episode_run_id",
                    "subject_public_cunit_id",
                }
                and isinstance(query_sequence, int)
                and not isinstance(query_sequence, bool)
                and 1 <= query_sequence <= 2**64 - 1
            ):
                self._battle_control_snapshot_v1_query = None
                return None
            try:
                subject = int(binding["subject_public_cunit_id"])
                date_raw = int(binding["date_raw"])
                native_revision = int(binding["native_revision"])
                normalized = normalize_battle_control_snapshot_v1(
                    cached.get("battle_control_snapshot"),
                    expected_subject_public_cunit_id=subject,
                    expected_observed_date_raw=date_raw,
                    expected_snapshot_revision=native_revision,
                )
            except (KeyError, TypeError, ValueError):
                self._battle_control_snapshot_v1_query = None
                return None
            if not (
                binding.get("native_revision")
                == snapshot.get("native_revision")
                and binding.get("snapshot_id") == snapshot.get("snapshot_id")
                and binding.get("revision") == snapshot.get("revision")
                and binding.get("date_raw") == snapshot.get("date_raw")
                and binding.get("connection_generation")
                == connection_generation
                and binding.get("episode_run_id") == episode_run_id
                and normalized.get("subject_public_cunit_id") == subject
                and cached.get("status") == "available"
            ):
                self._battle_control_snapshot_v1_query = None
                return None
            return {
                "status": "available",
                "battle_control_snapshot": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "subject_public_cunit_id": subject,
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

    def center_map_on_landed_title_v1(
        self,
        title_key: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Run the explicit-only typed camera command over the native pipe."""
        try:
            result = self._center_map_on_landed_title_v1_unrecorded(
                title_key,
                expected_revision=expected_revision,
            )
        except Exception as error:
            self._record_command(
                CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
                ok=False,
                error=f"{type(error).__name__}: {error}",
            )
            raise
        self._record_command(
            CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
            ok=True,
            result=result,
        )
        return result

    def _center_map_on_landed_title_v1_unrecorded(
        self,
        title_key: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        key = validate_landed_title_key(title_key)
        _validate_revision(expected_revision, "expected_revision")
        bridge_capabilities = set(
            _string_list(self.capabilities().get("bridge_capabilities"))
        )
        if (
            CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
            not in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "capability_not_available: native DLL cannot center the map "
                "on a landed title"
            )
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native title-map navigation requires a paused snapshot"
            )
        if starting.get("map_ready") is not True:
            raise BridgeUnavailableError(
                "native title-map navigation requires a map-ready snapshot"
            )
        try:
            binding = _title_map_navigation_binding_from_snapshot(starting)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native title-map navigation lacks a binding: {error}"
            ) from error
        if binding["revision"] != expected_revision:
            raise BridgeUnavailableError(
                "native title-map navigation revision mismatch: expected "
                f"{expected_revision}, current {binding['revision']}"
            )
        diagnostics = starting.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != TITLE_MAP_NAVIGATION_V1_GAME_VERSION
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
        ):
            raise BridgeUnavailableError(
                "native title-map navigation requires the frozen exact build"
            )
        try:
            raw = self._execute_primitive_step(
                CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
                expected_revision=expected_revision,
                required_capability=(
                    CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
                ),
                request_fields={"title_key": key},
            )
        except _NativeCommandRejectedError as error:
            if error.native_error not in TITLE_MAP_NAVIGATION_V1_REJECTION_CODES:
                raise BridgeUnavailableError(
                    "native title-map navigation returned an unknown rejection "
                    f"code: {error.native_error}"
                ) from error
            raise
        try:
            normalized_native = (
                normalize_native_title_map_navigation_v1_result(
                    raw,
                    expected_title_key=key,
                    expected_snapshot_id=str(binding["snapshot_id"]),
                    expected_native_revision=int(binding["native_revision"]),
                    expected_date_raw=int(binding["date_raw"]),
                )
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native title-map navigation returned malformed data: {error}"
            ) from error
        ending = self.take_snapshot()
        try:
            ending_binding = _title_map_navigation_binding_from_snapshot(
                ending
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native title-map navigation lost its binding: {error}"
            ) from error
        if not (
            ending.get("paused") is True
            and ending.get("map_ready") is True
            and ending_binding == binding
            and ending.get("played_character")
            == starting.get("played_character")
        ):
            raise BridgeUnavailableError(
                "native title-map navigation crossed its paused session binding"
            )
        projected = {
            **normalized_native,
            "binding": binding,
        }
        try:
            return normalize_title_map_navigation_v1_result(
                projected,
                expected_title_key=key,
                expected_binding=binding,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native title-map projection is malformed: {error}"
            ) from error

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
                result=(
                    error.step_result
                    if isinstance(error, StepPostconditionError)
                    else None
                ),
                error=f"{type(error).__name__}: {error}",
            )
            raise
        self._record_command(step, ok=True, result=result)
        return result

    def _execute_step_unrecorded(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step == CENTER_MAP_ON_LANDED_TITLE_V1_STEP:
            raise UnsupportedStepError(
                "title-map navigation requires its typed driver method"
            )
        life_advance_starting: dict[str, object] | None = None
        decision_epoch_target = parse_battle_decision_epoch_advance_step(step)
        committed_route_request = (
            parse_committed_route_sentinel_advance_step(step)
        )
        objective_hold_request = (
            parse_war_objective_hold_sentinel_advance_step(step)
        )
        if (
            step == "life-advance"
            or step in BATTLE_SENTINEL_ADVANCE_STEPS
            or decision_epoch_target is not None
            or committed_route_request is not None
            or objective_hold_request is not None
        ):
            # Bind the caller's revision before capability projection.  A
            # loading -> map_ready snapshot can arrive while capabilities()
            # is being assembled; that is an internal readiness transition,
            # not permission to accept an already-stale paused-map request.
            try:
                life_advance_starting = (
                    self.take_internal_semantic_snapshot()
                )
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
                    raise PreSubmissionRevisionMismatchError(
                        f"native {step} revision mismatch: "
                        f"expected {expected_revision}, current "
                        f"{current_revision}"
                    )
        event_option_number = parse_event_option_step(step)
        if (
            isinstance(step, str)
            and step.startswith("select-event-option-")
            and event_option_number is None
        ):
            raise UnsupportedStepError("malformed event option step")
        zhongguo_case_query = parse_query_zhongguo_case_snapshot_v1_step(
            step
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_case_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo case snapshot v1 query step"
            )
        zhongguo_ai_owned_case_query = (
            parse_query_zhongguo_ai_owned_case_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_ai_owned_case_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo AI-owned case snapshot v1 query step"
            )
        zhongguo_result_case_query = (
            parse_query_zhongguo_result_case_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_result_case_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo result-case snapshot v1 query step"
            )
        zhongguo_b2_pip_query = (
            parse_query_zhongguo_b2_pip_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_b2_pip_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo B2 PIP snapshot v1 query step"
            )
        zhongguo_promotion_compensation_query = (
            parse_query_zhongguo_promotion_compensation_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX
            )
            and zhongguo_promotion_compensation_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo promotion/compensation v1 query step"
            )
        zhongguo_projects_metrics_query = (
            parse_query_zhongguo_projects_metrics_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX)
            and zhongguo_projects_metrics_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo projects/metrics v1 query step"
            )
        zhongguo_workforce_collective_query = (
            parse_query_zhongguo_workforce_collective_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_workforce_collective_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo Workforce collective snapshot v1 query "
                "step"
            )
        zhongguo_workforce_normal_exit_query = (
            parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_workforce_normal_exit_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo Workforce normal-exit snapshot v1 "
                "query step"
            )
        zhongguo_incident_query = (
            parse_query_zhongguo_incident_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_incident_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo incident snapshot v1 query step"
            )
        zhongguo_manager_governance_query = (
            parse_query_zhongguo_manager_governance_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_manager_governance_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo manager-governance snapshot v1 query "
                "step"
            )
        zhongguo_scoreboard_query = (
            parse_query_zhongguo_scoreboard_state_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX
            )
            and zhongguo_scoreboard_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo scoreboard state v1 query step"
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
        battle_control_subject = (
            parse_query_battle_control_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX)
            and battle_control_subject is None
        ):
            raise UnsupportedStepError(
                "malformed battle-control snapshot v1 query step"
            )
        battle_transition_combat_id = parse_query_battle_transition_v1_step(
            step
        )
        if (
            isinstance(step, str)
            and step.startswith(QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX)
            and battle_transition_combat_id is None
        ):
            raise UnsupportedStepError(
                "malformed battle-transition v1 query step"
            )
        battle_terminal_transition_request = (
            parse_query_battle_terminal_transition_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX
            )
            and battle_terminal_transition_request is None
        ):
            raise UnsupportedStepError(
                "malformed battle-terminal transition v1 query step"
            )
        reinforcement_subject = (
            parse_query_battle_reinforcement_assignment_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX
            )
            and reinforcement_subject is None
        ):
            raise UnsupportedStepError(
                "malformed battle-reinforcement assignment v1 query step"
            )
        active_retreat_preview = (
            parse_preview_active_combat_retreat_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX)
            and decision_epoch_target is None
        ):
            raise UnsupportedStepError(
                "malformed battle decision-epoch target step"
            )
        if (
            isinstance(step, str)
            and step.startswith(
                COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX
            )
            and committed_route_request is None
        ):
            raise UnsupportedStepError(
                "malformed committed-route sentinel step"
            )
        if (
            isinstance(step, str)
            and step.startswith(
                WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX
            )
            and objective_hold_request is None
        ):
            raise UnsupportedStepError(
                "malformed war-objective hold sentinel step"
            )
        if (
            isinstance(step, str)
            and step.startswith(PREVIEW_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX)
            and active_retreat_preview is None
        ):
            raise UnsupportedStepError(
                "malformed active-combat retreat preview step"
            )
        active_retreat_order = parse_order_active_combat_retreat_v1_step(step)
        if (
            isinstance(step, str)
            and step.startswith(ORDER_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX)
            and active_retreat_order is None
        ):
            raise UnsupportedStepError(
                "malformed active-combat retreat order step"
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
        if zhongguo_case_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query an allowlisted ZhongGuo case"
                )
            return self._execute_zhongguo_case_snapshot_v1_query(
                zhongguo_case_query,
                expected_revision=expected_revision,
            )
        if zhongguo_ai_owned_case_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query an AI-owned ZhongGuo case"
                )
            return self._execute_zhongguo_ai_owned_case_snapshot_v1_query(
                zhongguo_ai_owned_case_query,
                expected_revision=expected_revision,
            )
        if zhongguo_result_case_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the received-self ZhongGuo "
                    "result case"
                )
            return self._execute_zhongguo_result_case_snapshot_v1_query(
                zhongguo_result_case_query,
                expected_revision=expected_revision,
            )
        if zhongguo_b2_pip_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the received-self ZhongGuo "
                    "B2 PIP case"
                )
            return self._execute_zhongguo_b2_pip_snapshot_v1_query(
                zhongguo_b2_pip_query,
                expected_revision=expected_revision,
            )
        if zhongguo_promotion_compensation_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL does not advertise the ZhongGuo "
                    "promotion/compensation postcondition query"
                )
            return self._execute_zhongguo_promotion_compensation_v1_query(
                zhongguo_promotion_compensation_query,
                expected_revision=expected_revision,
            )
        if zhongguo_projects_metrics_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL does not advertise the ZhongGuo "
                    "projects/metrics postcondition query"
                )
            return self._execute_zhongguo_projects_metrics_v1_query(
                zhongguo_projects_metrics_query,
                expected_revision=expected_revision,
            )
        if zhongguo_workforce_collective_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the received-self ZhongGuo "
                    "Workforce collective state"
                )
            return self._execute_zhongguo_workforce_collective_snapshot_v1_query(
                zhongguo_workforce_collective_query,
                expected_revision=expected_revision,
            )
        if zhongguo_workforce_normal_exit_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the received-self ZhongGuo "
                    "Workforce normal-exit lifecycle"
                )
            return self._execute_zhongguo_workforce_normal_exit_snapshot_v1_query(
                zhongguo_workforce_normal_exit_query,
                expected_revision=expected_revision,
            )
        if zhongguo_incident_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the received-self ZhongGuo "
                    "incident state"
                )
            return self._execute_zhongguo_incident_snapshot_v1_query(
                zhongguo_incident_query,
                expected_revision=expected_revision,
            )
        if zhongguo_manager_governance_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the ZhongGuo manager-governance "
                    "lifecycle"
                )
            return self._execute_zhongguo_manager_governance_snapshot_v1_query(
                zhongguo_manager_governance_query,
                expected_revision=expected_revision,
            )
        if zhongguo_scoreboard_query is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query fixed ZhongGuo scoreboard state"
                )
            return self._execute_zhongguo_scoreboard_state_v1_query(
                zhongguo_scoreboard_query,
                expected_revision=expected_revision,
            )
        if active_retreat_preview is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if not (
                _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES
                <= bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL lacks the battle query, exact move preview, "
                    "or player move capability required for active retreat"
                )
            return self._execute_active_combat_retreat_v1_preview(
                step, expected_revision=expected_revision
            )
        if active_retreat_order is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if not (
                _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES
                <= bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL lacks the battle query, exact move preview, "
                    "or player move capability required for active retreat"
                )
            return self._execute_active_combat_retreat_v1_order(
                step, expected_revision=expected_revision
            )
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
        if battle_control_subject is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query an ongoing battle control frame"
                )
            return self._execute_battle_control_snapshot_v1_query(
                step,
                expected_revision=expected_revision,
            )
        if battle_transition_combat_id is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_BATTLE_TRANSITION_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query a full-CombatID battle transition"
                )
            return self._execute_battle_transition_v1_query(
                step,
                expected_revision=expected_revision,
            )
        if battle_terminal_transition_request is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query journal-backed battle terminal "
                    "transitions"
                )
            return self._execute_battle_terminal_transition_v1_query(
                step,
                expected_revision=expected_revision,
            )
        if reinforcement_subject is not None:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query AI reinforcement assignment state"
                )
            return self._execute_battle_reinforcement_assignment_v1_query(
                step,
                expected_revision=expected_revision,
            )
        if step == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the campaign root context"
                )
            return self._execute_campaign_root_context_v1_query(
                expected_revision=expected_revision,
            )
        if step == QUERY_LOADED_FEATURE_MANIFEST_V1_STEP:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the loaded feature manifest"
                )
            return self._execute_loaded_feature_manifest_v1_query(
                expected_revision=expected_revision,
            )
        if step == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query a pending interaction context"
                )
            pending = self.take_snapshot().get(
                "pending_character_interaction"
            )
            pending_id = (
                pending.get("instance_id")
                if isinstance(pending, dict)
                else None
            )
            try:
                pending_id = normalize_pending_interaction_id(pending_id)
            except ValueError as error:
                raise BridgeUnavailableError(
                    "CK3 has no valid signed full pending interaction ID"
                ) from error
            return self.query_pending_character_interaction_context_v1(
                pending_id,
                expected_revision=expected_revision,
            )
        if step == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP:
            bridge_capabilities = set(
                _string_list(capabilities.get("bridge_capabilities"))
            )
            if (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
                not in bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "native DLL cannot query the current event window"
                )
            active_event = self.take_snapshot().get("active_event")
            event_id = (
                active_event.get("instance_id")
                if isinstance(active_event, dict)
                else None
            )
            if (
                isinstance(event_id, bool)
                or not isinstance(event_id, int)
                or not 1 <= event_id <= 2**31 - 1
            ):
                raise BridgeUnavailableError(
                    "CK3 has no positive full active event ID"
                )
            return self.query_current_event_window_context_v1(
                event_id,
                expected_revision=expected_revision,
            )
        if event_option_number is not None:
            return self._execute_event_option_step(
                step,
                option_number=event_option_number,
                expected_revision=expected_revision,
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
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
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
            if step not in capabilities["action_steps"]:
                raise BridgeUnavailableError(
                    "native white_peace submission lacks fresh same-frame "
                    "claim_cb decision readiness"
                )
            return self._execute_native_war_step(
                step, expected_revision=expected_revision
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
        if (
            step in BATTLE_SENTINEL_ADVANCE_STEPS
            or decision_epoch_target is not None
            or committed_route_request is not None
            or objective_hold_request is not None
        ):
            required_composite = (
                WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP
                if objective_hold_request is not None
                else
                COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP
                if committed_route_request is not None
                else BATTLE_DECISION_EPOCH_ADVANCE_STEP
                if decision_epoch_target is not None
                else step
            )
            if required_composite not in capabilities.get(
                "composite_action_steps", []
            ):
                raise UnsupportedStepError(
                    f"native tactical sentinel cannot execute {step}"
                )
            return self._execute_battle_sentinel_advance(
                step,
                expected_revision=expected_revision,
                starting_snapshot=life_advance_starting,
                requested_scope=(
                    "stationary_objective_hold"
                    if objective_hold_request is not None
                    else "committed_route"
                    if committed_route_request is not None
                    else "active_battle"
                ),
                requested_route=committed_route_request,
                requested_objective_hold=objective_hold_request,
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
            self._driver_state_dirty = True
        if not (ok and _is_deferred_read_only_history_step(step)):
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
            self._battle_control_snapshot_v1_query = None
            self._active_combat_retreat_v1_token = None
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

    def _encode_driver_state_locked(self) -> bytes:
        """Encode the current locked state without cloning its full history."""
        rollback_war_failures = self._rollback_war_failures
        payload = {
            "format_version": _NATIVE_DRIVER_STATE_VERSION,
            "pipe_name": self.pipe_name,
            "bridge_pid": self._session_bridge_pid,
            "episode_character_id": self._episode_character_id,
            "episode_run_id": self._episode_run_id,
            "last_checkpoint": self._last_checkpoint,
            "command_history": self._command_history,
            # Singular stays as the latest advisory for old readers.
            "rollback_war_failure": (
                rollback_war_failures[0]
                if rollback_war_failures
                else None
            ),
            "managed_restore_transaction": self._managed_restore_transaction,
        }
        # Keep an old-state migration recognizable across a crash before the
        # first playable snapshot supplies the restored physical origin.
        if not self._rollback_war_failures_migration_required:
            payload["rollback_war_failures"] = rollback_war_failures
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

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
            self._battle_control_snapshot_v1_query = None
            self._active_combat_retreat_v1_token = None
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
            if (
                row.get("command") not in _CHECKPOINT_ANCHOR_STEPS
                or row.get("ok") is not True
            ):
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
            and anchor.get("command") in _CHECKPOINT_ANCHOR_STEPS
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
            return load_native_driver_state_for_resume(path, self.pipe_name)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            with self._driver_state_lock:
                self._driver_state_error = (
                    f"{type(error).__name__}: {error}"
                )
            return None

    def _persist_driver_state(self) -> None:
        if self.state_dir is None:
            return
        with self._driver_state_write_lock:
            try:
                # Encode one immutable snapshot under the state lock, then
                # keep the write lock through its atomic replacement.  A
                # query appended while those bytes are being written sets
                # dirty again for the next barrier/close.
                with self._driver_state_lock:
                    if self._session_bridge_pid is None:
                        return
                    encoded = self._encode_driver_state_locked()
                    self._driver_state_dirty = False
                write_bytes_atomic(
                    self._native_driver_state_path(), encoded
                )
            except (OSError, TypeError, ValueError) as error:
                # A gameplay command has already happened by this point.  Keep
                # the live agent usable and surface persistence failure in
                # capabilities instead of falsely reporting that the game
                # command failed.
                with self._driver_state_lock:
                    self._driver_state_dirty = True
                    self._driver_state_error = (
                        f"{type(error).__name__}: {error}"
                    )
            else:
                with self._driver_state_lock:
                    self._driver_state_error = None

    def _execute_primitive_step(
        self,
        step: str,
        *,
        expected_revision: int | None = None,
        required_capability: str | None = None,
        request_fields: dict[str, object] | None = None,
        timeout_seconds: float | None = None,
        internal_semantic_snapshot: bool = False,
    ) -> dict[str, object]:
        if not isinstance(step, str) or not step:
            raise ValueError("step must be a non-empty string")
        capabilities = (
            self.state.capabilities()
            if internal_semantic_snapshot
            else self.capabilities()
        )
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
        snapshot = (
            self.take_internal_semantic_snapshot()
            if internal_semantic_snapshot
            else self.take_snapshot()
        )
        revision = int(snapshot["revision"])
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != revision:
                raise PreSubmissionRevisionMismatchError(
                    "native gameplay revision mismatch: "
                    f"expected {expected_revision}, current {revision}"
                )
        self._request_sequence += 1
        request_id = f"step-{self._request_sequence}-{uuid.uuid4().hex[:12]}"
        request = {
            "type": "execute_step",
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "step": step,
            "expected_revision": snapshot["native_revision"],
        }
        if request_fields is not None:
            if not isinstance(request_fields, dict) or any(
                not isinstance(key, str) or not key
                for key in request_fields
            ):
                raise ValueError("native request_fields must use string keys")
            reserved = set(request) & set(request_fields)
            if reserved:
                raise ValueError(
                    "native request_fields attempted to replace protocol fields"
                )
            request.update(request_fields)
        self.endpoint.send(request)
        command_timeout_seconds = (
            self.command_timeout_seconds
            if timeout_seconds is None
            else _positive_seconds(timeout_seconds, "timeout_seconds")
        )
        frame = self.state.wait_for_command_result(
            request_id, command_timeout_seconds
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

    def _execute_event_option_step(
        self,
        step: str,
        *,
        option_number: int,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Submit one event option and require the old full instance to move."""

        starting = self.take_snapshot()
        if starting.get("map_ready") is not True:
            raise BridgeUnavailableError(
                "native event selection requires a map-ready snapshot"
            )
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native event selection requires a paused snapshot"
            )
        active_event = starting.get("active_event")
        event_instance_id = (
            active_event.get("instance_id")
            if isinstance(active_event, dict)
            else None
        )
        option_count = (
            active_event.get("option_count")
            if isinstance(active_event, dict)
            else None
        )
        if (
            isinstance(event_instance_id, bool)
            or not isinstance(event_instance_id, int)
            or not 1 <= event_instance_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "CK3 has no positive full active event ID"
            )
        if (
            isinstance(option_count, bool)
            or not isinstance(option_count, int)
            or option_count < 1
            or not 1 <= option_number <= option_count
        ):
            raise BridgeUnavailableError(
                "selected native event option is outside the active event"
            )
        starting_diagnostics = starting.get("diagnostics")
        starting_connection_generation = (
            starting_diagnostics.get("connection_generation")
            if isinstance(starting_diagnostics, dict)
            else None
        )
        starting_bridge_pid = (
            starting_diagnostics.get("bridge_pid")
            if isinstance(starting_diagnostics, dict)
            else None
        )
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
            lambda snapshot: _event_instance_id(snapshot)
            != event_instance_id,
            timeout_seconds=self.command_timeout_seconds,
        )
        if _event_instance_id(changed) == event_instance_id:
            raise BridgeUnavailableError(
                "native event selection ACK did not advance the old full event instance"
            )
        changed_diagnostics = changed.get("diagnostics")
        if not (
            changed.get("episode_run_id") == starting.get("episode_run_id")
            and isinstance(changed_diagnostics, dict)
            and changed_diagnostics.get("connection_generation")
            == starting_connection_generation
            and changed_diagnostics.get("bridge_pid") == starting_bridge_pid
        ):
            raise BridgeUnavailableError(
                "native event selection crossed its bridge or episode binding"
            )
        if changed.get("paused") is not True:
            raise BridgeUnavailableError(
                "native event selection postcondition is not paused"
            )
        new_event_instance_id = _event_instance_id(changed)
        return {
            **result,
            "progress_status": "postcondition",
            "event_selection": {
                "status": "event_instance_advanced",
                "postcondition_verified": True,
                "old_event_instance_id": event_instance_id,
                "new_event_instance_id": new_event_instance_id,
                "selected_option_number": option_number,
                "selected_native_option_index": option_number - 1,
                "starting_snapshot_id": starting.get("snapshot_id"),
                "starting_revision": starting.get("revision"),
                "ending_snapshot_id": changed.get("snapshot_id"),
                "ending_revision": changed.get("revision"),
                "episode_run_id": changed.get("episode_run_id"),
                "connection_generation": starting_connection_generation,
                "bridge_pid": starting_bridge_pid,
            },
            "active_event": changed.get("active_event"),
            "paused": True,
            "snapshot_id": changed["snapshot_id"],
            "revision": changed["revision"],
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
        try:
            instance_id = normalize_pending_interaction_id(instance_id)
        except ValueError as error:
            raise BridgeUnavailableError(
                "CK3 pending character interaction lacks a valid signed full ID"
            ) from error
        notification = pending.get("auto_accept_notification")
        acknowledging = (
            step == ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP
        )
        if acknowledging and notification is not True:
            raise BridgeUnavailableError(
                "CK3 pending character interaction is not an ACK notification"
            )
        if not acknowledging and notification is not False:
            raise BridgeUnavailableError(
                "CK3 pending character interaction requires acknowledgement"
            )
        result = self._execute_primitive_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(starting["revision"])
            ),
            request_fields=(
                {"pending_interaction_id": int(instance_id)}
                if acknowledging
                else None
            ),
        )
        changed = self._wait_for_snapshot(
            self.take_snapshot(),
            lambda snapshot: (
                snapshot.get("paused") is True
                and (
                    not isinstance(
                        snapshot.get("pending_character_interaction"), dict
                    )
                    or snapshot["pending_character_interaction"].get(
                        "instance_id"
                    )
                    != instance_id
                )
            ),
            timeout_seconds=self.command_timeout_seconds,
        )
        remaining = changed.get("pending_character_interaction")
        if (
            isinstance(remaining, dict)
            and remaining.get("instance_id") == instance_id
        ):
            raise BridgeUnavailableError(
                "native character interaction reply did not advance the pending request"
            )
        if changed.get("paused") is not True:
            raise BridgeUnavailableError(
                "native character interaction reply postcondition is not paused"
            )
        if acknowledging:
            interaction_status = "acknowledged"
        elif step.startswith("accept-"):
            interaction_status = "accepted"
        else:
            interaction_status = "rejected"
        return {
            **result,
            "interaction_result": {
                "status": interaction_status,
                "instance_id": instance_id,
                "sender_character_id": pending.get("sender_character_id"),
            },
            "remaining_pending_character_interaction": remaining,
            "paused": True,
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

    def _execute_active_combat_retreat_v1_preview(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Compose battle legality and exact routing without mutating CK3."""
        parsed = parse_preview_active_combat_retreat_v1_step(step)
        if parsed is None:
            raise UnsupportedStepError(
                f"malformed active-combat retreat preview step {step}"
            )
        selected_public_cunit_id, target_province_id = parsed
        with self._driver_state_lock:
            self._active_combat_retreat_v1_token = None

        starting = self.take_snapshot()
        source_binding = _require_active_combat_retreat_source_binding(starting)
        selected_revision = int(source_binding["revision"])
        if expected_revision is None:
            raise BridgeUnavailableError(
                "active-combat retreat preview requires expected_revision"
            )
        _validate_revision(expected_revision, "expected_revision")
        if expected_revision != selected_revision:
            raise BridgeUnavailableError(
                "active-combat retreat preview revision mismatch: expected "
                f"{expected_revision}, current {selected_revision}"
            )
        selected_army = _army_by_id(starting, selected_public_cunit_id)
        if not (
            isinstance(selected_army, dict)
            and selected_army.get("controllable") is True
            and _army_in_active_combat(selected_army)
        ):
            raise BridgeUnavailableError(
                "active-combat retreat preview requires a controllable "
                "selected CUnit in active combat"
            )

        battle_result = self._execute_battle_control_snapshot_v1_query(
            query_battle_control_snapshot_v1_step(selected_public_cunit_id),
            expected_revision=selected_revision,
        )
        battle = battle_result.get("battle_control_snapshot")
        if not isinstance(battle, dict):
            raise BridgeUnavailableError(
                "active-combat retreat preview lacks a battle-control frame"
            )
        origin_province_id = selected_army.get("current_province_id")
        if not _positive_native_id(origin_province_id):
            raise BridgeUnavailableError(
                "active-combat retreat preview lacks the semantic origin"
            )
        combat_province_id = int(battle["combat_province_id"])
        if int(origin_province_id) != combat_province_id:
            raise BridgeUnavailableError(
                "active-combat retreat semantic origin disagrees with CombatID"
            )
        legality = battle.get("legality")
        if not (
            isinstance(legality, dict)
            and legality.get("status") == "available"
            and legality.get("legal_now") is True
        ):
            reason_codes = (
                legality.get("reason_codes_in_native_order")
                if isinstance(legality, dict)
                else None
            )
            first_reason = (
                reason_codes[0]
                if isinstance(reason_codes, list)
                and reason_codes
                and isinstance(reason_codes[0], str)
                else "native_legality_unavailable"
            )
            return self._active_combat_retreat_v1_unavailable_preview(
                step=step,
                source_binding=source_binding,
                battle=battle,
                target_province_id=target_province_id,
                origin_province_id=int(origin_province_id),
                reason=f"retreat_not_legal:{first_reason}",
            )
        if target_province_id == combat_province_id:
            return self._active_combat_retreat_v1_unavailable_preview(
                step=step,
                source_binding=source_binding,
                battle=battle,
                target_province_id=target_province_id,
                origin_province_id=int(origin_province_id),
                reason="target_does_not_leave_combat_province",
            )

        route_result = self._execute_native_war_step(
            preview_move_army_step(
                selected_public_cunit_id, target_province_id
            ),
            expected_revision=selected_revision,
        )
        route_preview = _canonical_active_combat_retreat_route_preview(
            route_result,
            selected_public_cunit_id=selected_public_cunit_id,
            combat_province_id=combat_province_id,
            target_province_id=target_province_id,
            expected_date_raw=int(source_binding["date_raw"]),
        )
        if route_preview is None:
            return self._active_combat_retreat_v1_unavailable_preview(
                step=step,
                source_binding=source_binding,
                battle=battle,
                target_province_id=target_province_id,
                origin_province_id=int(origin_province_id),
                reason="exact_route_preview_unavailable",
            )
        ending = self.take_snapshot()
        if _active_combat_retreat_source_binding(ending) != source_binding:
            return self._active_combat_retreat_v1_unavailable_preview(
                step=step,
                source_binding=source_binding,
                battle=battle,
                target_province_id=target_province_id,
                origin_province_id=int(origin_province_id),
                reason="snapshot_changed_during_preview",
            )

        candidate_token = secrets.token_urlsafe(24)
        order_step = order_active_combat_retreat_v1_step(
            selected_public_cunit_id,
            expected_snapshot_revision=selected_revision,
            expected_combat_id=int(battle["combat_id"]),
            expected_side_index=int(battle["side_index"]),
            expected_scope=str(battle["side_scope"]),
            target_province_id=target_province_id,
            candidate_token=candidate_token,
        )
        token_binding = {
            "candidate_token": candidate_token,
            "order_step": order_step,
            "source_binding": copy.deepcopy(source_binding),
            "battle_control_snapshot": copy.deepcopy(battle),
            "battle_binding": _active_combat_retreat_battle_binding(battle),
            "target_province_id": target_province_id,
            "route_preview": copy.deepcopy(route_preview),
        }
        with self._driver_state_lock:
            self._active_combat_retreat_v1_token = token_binding
        payload = _active_combat_retreat_preview_payload(
            step=step,
            source_binding=source_binding,
            battle=battle,
            target_province_id=target_province_id,
            target_preview={
                **route_preview,
                "status": "available",
                "unavailable_reason": None,
                "provenance": (
                    "planner_selected_exact_native_route_preview"
                ),
                "candidate_token": candidate_token,
                "order_step": order_step,
            },
            status="available",
            unavailable_reason=None,
            action_ready=True,
        )
        try:
            return normalize_active_combat_retreat_v1_preview(
                payload,
                expected_selected_public_cunit_id=(
                    selected_public_cunit_id
                ),
                expected_target_province_id=target_province_id,
                expected_snapshot_revision=selected_revision,
            )
        except ValueError as error:
            with self._driver_state_lock:
                if (
                    isinstance(self._active_combat_retreat_v1_token, dict)
                    and self._active_combat_retreat_v1_token.get(
                        "candidate_token"
                    )
                    == candidate_token
                ):
                    self._active_combat_retreat_v1_token = None
            raise BridgeUnavailableError(
                f"active-combat retreat preview composition failed: {error}"
            ) from error

    def _active_combat_retreat_v1_unavailable_preview(
        self,
        *,
        step: str,
        source_binding: dict[str, object],
        battle: dict[str, object],
        target_province_id: int,
        origin_province_id: int,
        reason: str,
    ) -> dict[str, object]:
        payload = _active_combat_retreat_preview_payload(
            step=step,
            source_binding=source_binding,
            battle=battle,
            target_province_id=target_province_id,
            target_preview={
                "status": "unavailable",
                "unavailable_reason": reason,
                "provenance": (
                    "planner_selected_exact_native_route_preview"
                ),
                "army_id": battle["selected_public_cunit_id"],
                "origin_province_id": origin_province_id,
                "target_province_id": target_province_id,
                "route_province_ids": [],
                "previewed_date_raw": None,
                "move_mode": None,
                "eta_date_raw": None,
                "movement_days": None,
                "candidate_token": None,
                "order_step": None,
            },
            status="unavailable",
            unavailable_reason=reason,
            action_ready=False,
        )
        try:
            return normalize_active_combat_retreat_v1_preview(
                payload,
                expected_selected_public_cunit_id=int(
                    battle["selected_public_cunit_id"]
                ),
                expected_target_province_id=target_province_id,
                expected_snapshot_revision=int(source_binding["revision"]),
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "active-combat retreat unavailable preview composition "
                f"failed: {error}"
            ) from error

    def _execute_active_combat_retreat_v1_order(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Consume a preview token, re-prove it, and submit player movement."""
        request = parse_order_active_combat_retreat_v1_step(step)
        if request is None:
            raise UnsupportedStepError(
                f"malformed active-combat retreat order step {step}"
            )
        with self._driver_state_lock:
            token_binding = copy.deepcopy(
                self._active_combat_retreat_v1_token
            )
            self._active_combat_retreat_v1_token = None

        def reject(reason: str) -> dict[str, object]:
            return self._active_combat_retreat_v1_rejection(
                step=step,
                request=request,
                token_binding=token_binding,
                reason=reason,
            )

        if expected_revision is None:
            return reject("expected_revision_required")
        try:
            _validate_revision(expected_revision, "expected_revision")
        except ValueError:
            return reject("invalid_expected_revision")
        if expected_revision != request["expected_snapshot_revision"]:
            return reject("revision_argument_mismatch")
        if not isinstance(token_binding, dict) or (
            token_binding.get("candidate_token")
            != request["candidate_token"]
        ):
            return reject("stale_or_unknown_token")

        cached_source = token_binding.get("source_binding")
        cached_battle = token_binding.get("battle_binding")
        field_rejections = (
            (
                "selected_public_cunit_id",
                "selected_public_cunit_id",
                "selected_identity_changed",
            ),
            (
                "expected_snapshot_revision",
                "revision",
                "revision_changed",
            ),
            ("expected_combat_id", "combat_id", "combat_changed"),
            ("expected_side_index", "side_index", "side_changed"),
            ("expected_scope", "side_scope", "scope_changed"),
        )
        if not isinstance(cached_source, dict) or not isinstance(
            cached_battle, dict
        ):
            return reject("stale_or_unknown_token")
        for request_key, binding_key, reason in field_rejections:
            binding = (
                cached_source if binding_key == "revision" else cached_battle
            )
            if request.get(request_key) != binding.get(binding_key):
                return reject(reason)
        if request["target_province_id"] != token_binding.get(
            "target_province_id"
        ):
            return reject("target_changed")

        try:
            current = self.take_snapshot()
        except (BridgeUnavailableError, UnsupportedStepError):
            return reject("snapshot_binding_unavailable")
        mismatch = _active_combat_retreat_source_mismatch_reason(
            cached_source, current
        )
        if mismatch is not None:
            return reject(mismatch)
        selected_public_cunit_id = int(
            request["selected_public_cunit_id"]
        )
        current_army = _army_by_id(current, selected_public_cunit_id)
        if not (
            isinstance(current_army, dict)
            and current_army.get("controllable") is True
            and _army_in_active_combat(current_army)
            and current_army.get("current_province_id")
            == cached_battle.get("combat_province_id")
        ):
            return reject("selected_army_left_active_combat")

        try:
            battle_result = self._execute_battle_control_snapshot_v1_query(
                query_battle_control_snapshot_v1_step(
                    selected_public_cunit_id
                ),
                expected_revision=int(request["expected_snapshot_revision"]),
            )
        except (BridgeUnavailableError, UnsupportedStepError):
            return reject("battle_requery_unavailable")
        battle = battle_result.get("battle_control_snapshot")
        if not isinstance(battle, dict):
            return reject("battle_requery_unavailable")
        current_battle_binding = _active_combat_retreat_battle_binding(battle)
        for key, reason in (
            ("combat_id", "combat_changed"),
            ("selected_public_cunit_id", "selected_identity_changed"),
            ("selected_native_carmy_id", "selected_identity_changed"),
            ("selected_owner_character_id", "selected_identity_changed"),
            ("side_index", "side_changed"),
            ("side_scope", "scope_changed"),
            (
                "affected_public_cunit_ids_in_stored_order",
                "scope_membership_changed",
            ),
            (
                "unaffected_same_side_public_cunit_ids_in_stored_order",
                "scope_membership_changed",
            ),
        ):
            if current_battle_binding.get(key) != cached_battle.get(key):
                return reject(reason)
        legality = battle.get("legality")
        if not (
            isinstance(legality, dict)
            and legality.get("status") == "available"
            and legality.get("legal_now") is True
        ):
            return reject("retreat_no_longer_legal")
        if battle != token_binding.get("battle_control_snapshot"):
            return reject("battle_frame_changed")

        target_province_id = int(request["target_province_id"])
        try:
            route_result = self._execute_native_war_step(
                preview_move_army_step(
                    selected_public_cunit_id, target_province_id
                ),
                expected_revision=int(request["expected_snapshot_revision"]),
            )
        except (BridgeUnavailableError, UnsupportedStepError):
            return reject("exact_route_preview_unavailable")
        route_preview = _canonical_active_combat_retreat_route_preview(
            route_result,
            selected_public_cunit_id=selected_public_cunit_id,
            combat_province_id=int(cached_battle["combat_province_id"]),
            target_province_id=target_province_id,
            expected_date_raw=int(cached_source["date_raw"]),
        )
        if route_preview is None:
            return reject("exact_route_preview_unavailable")
        if route_preview != token_binding.get("route_preview"):
            return reject("route_changed")
        try:
            rechecked = self.take_snapshot()
        except (BridgeUnavailableError, UnsupportedStepError):
            return reject("snapshot_binding_unavailable")
        mismatch = _active_combat_retreat_source_mismatch_reason(
            cached_source, rechecked
        )
        if mismatch is not None:
            return reject(mismatch)

        move_step = move_army_step(
            selected_public_cunit_id, target_province_id
        )
        try:
            move_result = self._execute_primitive_step(
                move_step,
                expected_revision=int(request["expected_snapshot_revision"]),
                required_capability=MOVE_ARMY_CAPABILITY,
            )
        except _NativeCommandRejectedError:
            return reject("move_command_rejected")
        if not (
            move_result.get("step") == move_step
            and move_result.get("accepted") is True
            and move_result.get("status") == "submitted"
        ):
            raise BridgeUnavailableError(
                "active-combat retreat move command returned a malformed ACK"
            )
        try:
            observed = self.take_snapshot()
        except (BridgeUnavailableError, UnsupportedStepError):
            semantic_postcondition = (
                _active_combat_retreat_pending_postcondition()
            )
        else:
            semantic_postcondition = (
                _active_combat_retreat_semantic_postcondition(
                    observed,
                    affected_public_cunit_ids=list(
                        cached_battle[
                            "affected_public_cunit_ids_in_stored_order"
                        ]
                    ),
                    target_province_id=target_province_id,
                )
            )
        payload = {
            "schema_version": 1,
            "contract_stage": ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE,
            "step": step,
            "accepted": True,
            "status": "accepted_verification_pending",
            "rejection_reason": None,
            "verification_pending": True,
            "token_consumed": True,
            "selected_public_cunit_id": selected_public_cunit_id,
            "expected_snapshot_revision": request[
                "expected_snapshot_revision"
            ],
            "expected_combat_id": request["expected_combat_id"],
            "expected_side_index": request["expected_side_index"],
            "expected_scope": request["expected_scope"],
            "target_province_id": target_province_id,
            "affected_public_cunit_ids_in_stored_order": copy.deepcopy(
                cached_battle[
                    "affected_public_cunit_ids_in_stored_order"
                ]
            ),
            "unaffected_same_side_public_cunit_ids_in_stored_order": (
                copy.deepcopy(
                    cached_battle[
                        "unaffected_same_side_public_cunit_ids_in_stored_order"
                    ]
                )
            ),
            "underlying_move_result": copy.deepcopy(move_result),
            "semantic_postcondition": semantic_postcondition,
            "backend_id": "native-headless",
        }
        return _normalize_active_combat_retreat_order_payload(
            payload, request=request
        )

    def _active_combat_retreat_v1_rejection(
        self,
        *,
        step: str,
        request: dict[str, object],
        token_binding: dict[str, object] | None,
        reason: str,
    ) -> dict[str, object]:
        battle_binding = (
            token_binding.get("battle_binding")
            if isinstance(token_binding, dict)
            else None
        )
        affected = (
            copy.deepcopy(
                battle_binding.get(
                    "affected_public_cunit_ids_in_stored_order", []
                )
            )
            if isinstance(battle_binding, dict)
            else []
        )
        unaffected = (
            copy.deepcopy(
                battle_binding.get(
                    "unaffected_same_side_public_cunit_ids_in_stored_order",
                    [],
                )
            )
            if isinstance(battle_binding, dict)
            else []
        )
        payload = {
            "schema_version": 1,
            "contract_stage": ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE,
            "step": step,
            "accepted": False,
            "status": "rejected",
            "rejection_reason": reason,
            "verification_pending": False,
            "token_consumed": True,
            "selected_public_cunit_id": request[
                "selected_public_cunit_id"
            ],
            "expected_snapshot_revision": request[
                "expected_snapshot_revision"
            ],
            "expected_combat_id": request["expected_combat_id"],
            "expected_side_index": request["expected_side_index"],
            "expected_scope": request["expected_scope"],
            "target_province_id": request["target_province_id"],
            "affected_public_cunit_ids_in_stored_order": affected,
            "unaffected_same_side_public_cunit_ids_in_stored_order": (
                unaffected
            ),
            "underlying_move_result": None,
            "semantic_postcondition": (
                _active_combat_retreat_not_observed_postcondition()
            ),
            "backend_id": "native-headless",
        }
        return _normalize_active_combat_retreat_order_payload(
            payload, request=request
        )

    def _execute_native_war_step(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        termination_query_war_id = (
            parse_query_war_termination_options_step(step)
        )
        termination_terms_query_war_id = (
            parse_query_war_termination_terms_step(step)
        )
        internal_read_only_query = bool(
            termination_query_war_id is not None
            or termination_terms_query_war_id is not None
            or parse_preview_move_army_step(step) is not None
            or parse_query_route_contact_horizon_step(step) is not None
        )
        starting = (
            self.take_internal_semantic_snapshot()
            if internal_read_only_query
            else self.take_snapshot()
        )
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
                step,
                expected_revision=selected_revision,
                internal_semantic_snapshot=True,
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
            current = self.take_internal_semantic_snapshot()
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
                    step,
                    expected_revision=selected_revision,
                    internal_semantic_snapshot=True,
                )
            except _NativeCommandRejectedError as error:
                if error.native_error not in _ARMY_MOVE_DEFERRED_ERRORS:
                    raise
                current = self.take_internal_semantic_snapshot()
                return {
                    "step": step,
                    "accepted": False,
                    "status": "deferred",
                    "backend_id": "native-headless",
                    "route_preview": {
                        "status": "deferred",
                        "reason": "army_not_move_ready",
                        "native_rejection_stage": (
                            _ARMY_MOVE_DEFERRED_ERROR_STAGES[
                                error.native_error
                            ]
                        ),
                        "native_error": error.native_error,
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

    def _execute_battle_control_snapshot_v1_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one atomic exact-build ongoing-battle control frame."""
        subject_public_cunit_id = (
            parse_query_battle_control_snapshot_v1_step(step)
        )
        if subject_public_cunit_id is None:
            raise UnsupportedStepError(
                f"malformed battle-control snapshot v1 step {step}"
            )
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native battle-control snapshot requires a paused snapshot"
            )
        subject = _army_by_id(starting, subject_public_cunit_id)
        if not (
            isinstance(subject, dict)
            and subject.get("controllable") is True
            and _army_in_active_combat(subject)
        ):
            raise BridgeUnavailableError(
                "native battle-control subject is not a controllable army "
                "in active combat"
            )
        date_raw = _date_raw(starting, "battle-control starting snapshot")
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-control query lacks a native revision"
            )
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        for attempt in range(_BATTLE_CONTROL_QUERY_MAX_ATTEMPTS):
            try:
                result = self._execute_primitive_step(
                    step,
                    expected_revision=selected_revision,
                    required_capability=(
                        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
                    ),
                )
                break
            except _NativeCommandRejectedError as error:
                if not error.native_error.startswith(
                    _BATTLE_CONTROL_TRANSIENT_QUERY_ERROR
                ):
                    raise
                retry_snapshot = self.take_snapshot()
                retry_subject = _army_by_id(
                    retry_snapshot, subject_public_cunit_id
                )
                if not (
                    _same_paused_native_frame(starting, retry_snapshot)
                    and starting.get("revision")
                    == retry_snapshot.get("revision")
                    and starting.get("date_raw")
                    == retry_snapshot.get("date_raw")
                    and isinstance(retry_subject, dict)
                    and retry_subject.get("controllable") is True
                    and _army_in_active_combat(retry_subject)
                ):
                    raise
                if attempt + 1 >= _BATTLE_CONTROL_QUERY_MAX_ATTEMPTS:
                    if (
                        error.native_error
                        == _BATTLE_CONTROL_IDENTITY_PENDING_QUERY_ERROR
                        and subject.get("in_combat") is True
                        and retry_subject.get("in_combat") is True
                    ):
                        return self._cache_battle_control_identity_pending(
                            step=step,
                            starting=starting,
                            current=retry_snapshot,
                            subject_public_cunit_id=(
                                subject_public_cunit_id
                            ),
                            native_revision=int(native_revision),
                            date_raw=date_raw,
                        )
                    raise
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "battle_control_snapshot",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") != "available"
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native battle-control query returned a malformed status"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-control query lacks query_sequence"
            )
        try:
            normalized = normalize_battle_control_snapshot_v1(
                result.get("battle_control_snapshot"),
                expected_subject_public_cunit_id=(
                    subject_public_cunit_id
                ),
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native battle-control query returned a malformed frame: {error}"
            ) from error
        current = self.take_snapshot()
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native battle-control query crossed a snapshot revision"
            )
        current_subject = _army_by_id(current, subject_public_cunit_id)
        if not (
            isinstance(current_subject, dict)
            and current_subject.get("controllable") is True
            and _army_in_active_combat(current_subject)
        ):
            raise BridgeUnavailableError(
                "native battle-control subject changed during the query"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": native_revision,
            "snapshot_id": starting.get("snapshot_id"),
            "revision": starting.get("revision"),
            "date_raw": date_raw,
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
            "subject_public_cunit_id": subject_public_cunit_id,
        }
        with self._driver_state_lock:
            self._battle_control_snapshot_v1_query = {
                "status": "available",
                "battle_control_snapshot": copy.deepcopy(normalized),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
            }
        return {
            **result,
            "status": "available",
            "battle_control_snapshot": normalized,
            "query_sequence": query_sequence,
            "selected_public_cunit_id": normalized[
                "selected_public_cunit_id"
            ],
            "selected_native_carmy_id": normalized[
                "selected_native_carmy_id"
            ],
            "selected_owner_character_id": normalized[
                "selected_owner_character_id"
            ],
            "combat_province_id": normalized["combat_province_id"],
            "side_index": normalized["side_index"],
            "side_scope": normalized["side_scope"],
            "affected_public_cunit_ids_in_stored_order": copy.deepcopy(
                normalized["affected_public_cunit_ids_in_stored_order"]
            ),
            "unaffected_same_side_public_cunit_ids_in_stored_order": (
                copy.deepcopy(
                    normalized[
                        "unaffected_same_side_public_cunit_ids_in_stored_order"
                    ]
                )
            ),
            "side_flags": copy.deepcopy(normalized["side_flags"]),
            "legality": copy.deepcopy(normalized["legality"]),
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def _cache_battle_control_identity_pending(
        self,
        *,
        step: str,
        starting: dict[str, object],
        current: dict[str, object],
        subject_public_cunit_id: int,
        native_revision: int,
        date_raw: int,
    ) -> dict[str, object]:
        """Expose one exact frozen combat-identity materialization request."""
        starting_subject = _army_by_id(starting, subject_public_cunit_id)
        current_subject = _army_by_id(current, subject_public_cunit_id)
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw") == date_raw
            and isinstance(starting_subject, dict)
            and starting_subject.get("controllable") is True
            and starting_subject.get("in_combat") is True
            and isinstance(current_subject, dict)
            and current_subject.get("controllable") is True
            and current_subject.get("in_combat") is True
        ):
            raise BridgeUnavailableError(
                "native battle-control identity-pending observation crossed "
                "its frozen public combat frame"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        cache_binding = {
            "native_revision": native_revision,
            "snapshot_id": starting.get("snapshot_id"),
            "revision": starting.get("revision"),
            "date_raw": date_raw,
            "connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
            "subject_public_cunit_id": subject_public_cunit_id,
        }
        with self._driver_state_lock:
            self._battle_control_snapshot_v1_query = {
                "status": BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
                "diagnostic_reason": (
                    BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
                ),
                "native_query_status": "state_changed",
                "query_attempts": _BATTLE_CONTROL_QUERY_MAX_ATTEMPTS,
                "cache_binding": cache_binding,
            }
        return {
            "step": step,
            "accepted": True,
            "status": BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
            "native_query_status": "state_changed",
            "diagnostic_reason": BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC,
            "query_attempts": _BATTLE_CONTROL_QUERY_MAX_ATTEMPTS,
            "subject_public_cunit_id": subject_public_cunit_id,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "backend_id": "native-headless",
        }

    def _execute_battle_transition_v1_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one atomic lifecycle projection by full CombatID."""
        combat_id = parse_query_battle_transition_v1_step(step)
        if combat_id is None:
            raise UnsupportedStepError(
                f"malformed battle-transition v1 step {step}"
            )
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native battle-transition query requires a paused snapshot"
            )
        date_raw = _date_raw(starting, "battle-transition starting snapshot")
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-transition query lacks a native revision"
            )
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "battle_transition_snapshot",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native battle-transition query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-transition query lacks query_sequence"
            )
        try:
            normalized = normalize_battle_transition_v1(
                result.get("battle_transition_snapshot"),
                expected_combat_id=combat_id,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native battle-transition query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native battle-transition envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native battle-transition query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "battle_transition_snapshot": normalized,
            "query_sequence": query_sequence,
            "combat_id": normalized["combat_id"],
            "province_id": normalized["province_id"],
            "phase": normalized["phase"],
            "phase_raw": normalized["phase_raw"],
            "phase_day": normalized["phase_day"],
            "winner_side": normalized["winner_side"],
            "winner_raw": normalized["winner_raw"],
            "forced_winner_side": normalized["forced_winner_side"],
            "forced_winner_raw": normalized["forced_winner_raw"],
            "finalized": normalized["finalized"],
            "battle_result_id": normalized["battle_result_id"],
            "attacker_public_cunit_ids_in_stored_order": copy.deepcopy(
                normalized[
                    "attacker_public_cunit_ids_in_stored_order"
                ]
            ),
            "defender_public_cunit_ids_in_stored_order": copy.deepcopy(
                normalized[
                    "defender_public_cunit_ids_in_stored_order"
                ]
            ),
            "battle_transition_ready": normalized[
                "battle_transition_ready"
            ],
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def _execute_battle_terminal_transition_v1_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one journal-backed terminal event and its current successor."""
        request = parse_query_battle_terminal_transition_v1_step(step)
        if request is None:
            raise UnsupportedStepError(
                f"malformed battle-terminal transition v1 step {step}"
            )
        prior_combat_id, subject_public_cunit_id, after_sequence = request
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native battle-terminal transition query requires a paused "
                "snapshot"
            )
        date_raw = _date_raw(
            starting, "battle-terminal transition starting snapshot"
        )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-terminal transition query lacks a native "
                "revision"
            )
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
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
            ),
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "battle_terminal_transition",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native battle-terminal transition query returned a malformed "
                "envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-terminal transition query lacks query_sequence"
            )
        try:
            normalized = normalize_battle_terminal_transition_v1(
                result.get("battle_terminal_transition"),
                expected_prior_combat_id=prior_combat_id,
                expected_subject_public_cunit_id=subject_public_cunit_id,
                expected_after_terminal_sequence=after_sequence,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native battle-terminal transition query returned a "
                f"malformed frame: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native battle-terminal transition envelope status "
                "disagrees with frame"
            )
        current = self.take_snapshot()
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native battle-terminal transition query crossed a snapshot "
                "revision"
            )
        mirror_keys = (
            "prior_combat_id",
            "subject_public_cunit_id",
            "terminal_journal",
            "prior",
            "removal",
            "subject",
            "successor",
            "battle_terminal_transition_ready",
            "unavailable_reason",
        )
        return {
            **result,
            "status": normalized["status"],
            "battle_terminal_transition": normalized,
            "query_sequence": query_sequence,
            **{
                key: copy.deepcopy(normalized[key])
                for key in mirror_keys
            },
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def _execute_battle_reinforcement_assignment_v1_query(
        self,
        step: str,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one paused exact-build native AI help assignment frame."""
        selected_public_cunit_id = (
            parse_query_battle_reinforcement_assignment_v1_step(step)
        )
        if selected_public_cunit_id is None:
            raise UnsupportedStepError(
                f"malformed battle-reinforcement assignment v1 step {step}"
            )
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native battle-reinforcement query requires a paused snapshot"
            )
        date_raw = _date_raw(
            starting, "battle-reinforcement starting snapshot"
        )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-reinforcement query lacks a native revision"
            )
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
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
            ),
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "battle_reinforcement_assignment",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native battle-reinforcement query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native battle-reinforcement query lacks query_sequence"
            )
        try:
            normalized = normalize_battle_reinforcement_assignment_v1(
                result.get("battle_reinforcement_assignment"),
                expected_selected_public_cunit_id=selected_public_cunit_id,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native battle-reinforcement query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native battle-reinforcement envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native battle-reinforcement query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "battle_reinforcement_assignment": normalized,
            "query_sequence": query_sequence,
            "selected_public_cunit_id": normalized[
                "selected_public_cunit_id"
            ],
            "selected_native_carmy_id": normalized[
                "selected_native_carmy_id"
            ],
            "coordinator_id": normalized["coordinator_id"],
            "unit_stack_stored_index": normalized[
                "unit_stack_stored_index"
            ],
            "subunit_stored_index": normalized["subunit_stored_index"],
            "signal": copy.deepcopy(normalized["signal"]),
            "assignment": copy.deepcopy(normalized["assignment"]),
            "route": copy.deepcopy(normalized["route"]),
            "native_order": copy.deepcopy(normalized["native_order"]),
            "contact_projection": copy.deepcopy(
                normalized["contact_projection"]
            ),
            "battle_reinforcement_assignment_ready": normalized[
                "battle_reinforcement_assignment_ready"
            ],
            "unavailable_reason": normalized["unavailable_reason"],
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def _execute_campaign_root_context_v1_query(
        self,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read the atomic local-player campaign root while paused."""
        step = QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native campaign-root query requires a paused snapshot"
            )
        date_raw = _date_raw(starting, "campaign-root starting snapshot")
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native campaign-root query lacks a native revision"
            )
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "campaign_root_context",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native campaign-root query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native campaign-root query lacks query_sequence"
            )
        try:
            normalized = normalize_campaign_root_context_v1(
                result.get("campaign_root_context"),
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native campaign-root query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native campaign-root envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native campaign-root query crossed a snapshot revision"
            )
        mirror_keys = (
            "schema_version",
            "date_raw",
            "local_player_id",
            "player_character_id",
            "player_character_alive",
            "primary_title",
            "capital_province_id",
            "immediate_liege_character_id",
            "top_liege_character_id",
            "independent",
            "government",
            "selected_game_rule_tokens",
            "native_selected_game_rule_token_count",
            "readiness",
            "unavailable_reason",
            "provenance",
        )
        return {
            **result,
            "status": normalized["status"],
            "campaign_root_context": normalized,
            "query_sequence": query_sequence,
            **{
                key: copy.deepcopy(normalized[key])
                for key in mirror_keys
            },
            "campaign_root_context_ready": normalized["readiness"][
                "ready"
            ],
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def _execute_zhongguo_case_snapshot_v1_query(
        self,
        query: ZhongguoCaseQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one allowlisted ZhongGuo product case while paused."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo case query requires a paused snapshot"
            )
        date_raw = _date_raw(starting, "ZhongGuo-case starting snapshot")
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo case query lacks a signed int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo case query lacks a native revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo case query lacks a snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo case query lacks the played character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo case query lacks a connection generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY
            ),
            request_fields={
                "case_kind": query.case_kind,
                "subject_character_id": query.subject_character_id,
                "owner_character_id": query.owner_character_id or 0,
                "request_nonce": query.request_nonce,
            },
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "zhongguo_case_snapshot",
                "backend_id",
            }
            or result.get("step")
            != QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo case query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo case query lacks query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_case_snapshot_v1(
                result.get("zhongguo_case_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo case query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo case envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo case query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_case_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_ai_owned_case_snapshot_v1_query(
        self,
        query: ZhongguoAiOwnedCaseQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one AI manager's B1 case through the fixed native profile."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query requires a paused "
                "snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo AI-owned-case starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query lacks a signed int32 "
                "date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query lacks a native revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query lacks a snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query lacks the played "
                "character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query lacks a connection "
                "generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
            ),
            request_fields={
                "owner_character_id": query.owner_character_id,
                "subject_character_id": query.subject_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_ai_owned_case_snapshot",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query returned a malformed "
                "envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query lacks query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_ai_owned_case_snapshot_v1(
                result.get("zhongguo_ai_owned_case_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query returned a malformed "
                f"frame: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case envelope status disagrees "
                "with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo AI-owned case query crossed a snapshot "
                "revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_ai_owned_case_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_result_case_snapshot_v1_query(
        self,
        query: ZhongguoResultCaseQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read the paused player's received result from one expected owner."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query requires a paused snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo result-case starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query lacks a signed int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query lacks a native revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query lacks a snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query lacks the played character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query lacks a connection "
                "generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
            ),
            request_fields={
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "zhongguo_result_case_snapshot",
                "backend_id",
            }
            or result.get("step")
            != QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query returned a malformed "
                "envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query lacks query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_result_case_snapshot_v1(
                result.get("zhongguo_result_case_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query returned a malformed "
                f"frame: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo result-case envelope status disagrees with "
                "frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo result-case query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_result_case_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_b2_pip_snapshot_v1_query(
        self,
        query: ZhongguoB2PipQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read the paused player's fixed-allowlist B2 PIP projection."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query requires a paused snapshot"
            )
        date_raw = _date_raw(starting, "ZhongGuo B2 PIP starting snapshot")
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query lacks a signed int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query lacks a native revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query lacks a snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query lacks the played character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query lacks a connection generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
            request_fields={
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_b2_pip_snapshot",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step") != QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query lacks query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_b2_pip_snapshot_v1(
                result.get("zhongguo_b2_pip_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo B2 PIP query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_b2_pip_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_promotion_compensation_v1_query(
        self,
        query: ZhongguoPromotionCompensationQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one paused, player-owned promotion/compensation receipt."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation query requires a "
                "paused snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo promotion/compensation starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation query lacks an "
                "int32 date"
            )
        native_revision = starting.get("native_revision")
        snapshot_id = starting.get("snapshot_id")
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
            or isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
            or isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation query lacks its "
                "paused snapshot binding"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
            ),
            request_fields={
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step", "accepted", "status", "query_sequence",
            "snapshot_revision", "zhongguo_promotion_compensation_postcondition",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation query returned a "
                "malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation query lacks "
                "query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_promotion_compensation_v1(
                result.get(
                    "zhongguo_promotion_compensation_postcondition"
                ),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation frame is malformed: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation envelope status "
                "disagrees with frame"
            )
        current = self.take_snapshot()
        current_played = current.get("played_character")
        current_player_id = (
            current_played.get("character_id")
            if isinstance(current_played, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo promotion/compensation query crossed a "
                "snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_promotion_compensation_postcondition": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_projects_metrics_v1_query(
        self,
        query: ZhongguoProjectsMetricsQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one paused, played-subject projects/metrics receipt."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics query requires a "
                "paused snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo projects/metrics starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics query lacks an "
                "int32 date"
            )
        native_revision = starting.get("native_revision")
        snapshot_id = starting.get("snapshot_id")
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
            or isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
            or isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics query lacks its "
                "paused snapshot binding"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
            ),
            request_fields={
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step", "accepted", "status", "query_sequence",
            "snapshot_revision", "zhongguo_projects_metrics_postcondition",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics query returned a "
                "malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics query lacks "
                "query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_projects_metrics_v1(
                result.get(
                    "zhongguo_projects_metrics_postcondition"
                ),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics frame is malformed: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics envelope status "
                "disagrees with frame"
            )
        current = self.take_snapshot()
        current_played = current.get("played_character")
        current_player_id = (
            current_played.get("character_id")
            if isinstance(current_played, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo projects/metrics query crossed a "
                "snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_projects_metrics_postcondition": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }



    def _execute_zhongguo_workforce_collective_snapshot_v1_query(
        self,
        query: ZhongguoWorkforceCollectiveQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read the paused player's Workforce collective and owner ledger."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query requires a "
                "paused snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo Workforce collective starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query lacks a signed "
                "int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query lacks a native "
                "revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query lacks a snapshot "
                "identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query lacks the played "
                "character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query lacks a "
                "connection generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
            ),
            request_fields={
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_workforce_collective_snapshot",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query returned a "
                "malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query lacks "
                "query_sequence"
            )
        try:
            normalized = (
                normalize_native_zhongguo_workforce_collective_snapshot_v1(
                    result.get("zhongguo_workforce_collective_snapshot"),
                    expected_query=query,
                    expected_snapshot_revision=native_revision,
                    expected_date_raw=date_raw,
                    expected_player_character_id=player_character_id,
                )
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query returned a "
                f"malformed frame: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective envelope status "
                "disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce collective query crossed a "
                "snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_workforce_collective_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_workforce_normal_exit_snapshot_v1_query(
        self,
        query: ZhongguoWorkforceNormalExitQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read the paused player's Workforce normal-exit/HC lifecycle."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query requires a "
                "paused snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo Workforce normal-exit starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query lacks a signed "
                "int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query lacks a native "
                "revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query lacks a "
                "snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query lacks the "
                "played character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query lacks a "
                "connection generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
            ),
            request_fields={
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_workforce_normal_exit_snapshot",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query returned a "
                "malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query lacks "
                "query_sequence"
            )
        try:
            normalized = (
                normalize_native_zhongguo_workforce_normal_exit_snapshot_v1(
                    result.get("zhongguo_workforce_normal_exit_snapshot"),
                    expected_query=query,
                    expected_snapshot_revision=native_revision,
                    expected_date_raw=date_raw,
                    expected_player_character_id=player_character_id,
                )
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query returned a "
                f"malformed frame: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit envelope status "
                "disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo Workforce normal-exit query crossed a "
                "snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_workforce_normal_exit_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_incident_snapshot_v1_query(
        self,
        query: ZhongguoIncidentQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one paused fixed-profile incident projection for the player."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo incident query requires a paused snapshot"
            )
        date_raw = _date_raw(starting, "ZhongGuo incident starting snapshot")
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo incident query lacks a signed int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo incident query lacks a native revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo incident query lacks a snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo incident query lacks the played character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo incident query lacks a connection generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
            request_fields={
                "owner_character_id": query.owner_character_id,
                "profile": query.profile,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_incident_snapshot",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo incident query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo incident query lacks query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_incident_snapshot_v1(
                result.get("zhongguo_incident_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo incident query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo incident envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo incident query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_incident_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_manager_governance_snapshot_v1_query(
        self,
        query: ZhongguoManagerGovernanceQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read one paused, fixed-allowlist manager-governance lifecycle."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query requires a paused "
                "snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo manager-governance starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query lacks a signed "
                "int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query lacks a native "
                "revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query lacks a snapshot "
                "identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query lacks the played "
                "character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query lacks a connection "
                "generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
            ),
            request_fields={
                "subject_character_id": query.subject_character_id,
                "owner_character_id": query.owner_character_id,
                "request_nonce": query.request_nonce,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_manager_governance_snapshot",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query returned a malformed "
                "envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query lacks query_sequence"
            )
        try:
            normalized = (
                normalize_native_zhongguo_manager_governance_snapshot_v1(
                    result.get("zhongguo_manager_governance_snapshot"),
                    expected_query=query,
                    expected_snapshot_revision=native_revision,
                    expected_date_raw=date_raw,
                    expected_player_character_id=player_character_id,
                )
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query returned a "
                f"malformed frame: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance envelope status "
                "disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo manager-governance query crossed a snapshot "
                "revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_manager_governance_snapshot": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_zhongguo_scoreboard_state_v1_query(
        self,
        query: ZhongguoScoreboardStateQueryV1,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read fixed scoreboard instances and the played character's ACL."""
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query requires a paused snapshot"
            )
        date_raw = _date_raw(
            starting, "ZhongGuo scoreboard starting snapshot"
        )
        if not -(2**31) <= date_raw <= 2**31 - 1:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query lacks a signed int32 date"
            )
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query lacks a native revision"
            )
        snapshot_id = starting.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query lacks a snapshot identity"
            )
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query lacks the played character"
            )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query lacks a connection generation"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
            expected_revision=selected_revision,
            required_capability=QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
            request_fields={
                "request_nonce": query.request_nonce,
                "expected_connection_generation": connection_generation,
            },
        )
        expected_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_scoreboard_state",
            "backend_id",
        }
        if (
            set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query lacks query_sequence"
            )
        try:
            normalized = normalize_native_zhongguo_scoreboard_state_v1(
                result.get("zhongguo_scoreboard_state"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and current_player_character_id == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard query crossed a snapshot revision"
            )
        return {
            **result,
            "status": normalized["status"],
            "zhongguo_scoreboard_state": normalized,
            "query_sequence": query_sequence,
            "queried_snapshot_id": snapshot_id,
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def activate_zhongguo_scoreboard_v1(
        self,
        request: ZhongguoScoreboardActionRequestV1,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Cross the exact dispatcher transport without promoting its ACK.

        The typed request binds the last provider observation. A native ACK is
        still verification-pending and production capability remains a
        separate advertised gate.
        """

        if not isinstance(request, ZhongguoScoreboardActionRequestV1):
            raise ValueError("request must be a scoreboard action v1 request")
        _validate_revision(expected_revision, "expected_revision")
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard action requires a paused snapshot"
            )
        public_revision = starting.get("revision")
        native_revision = starting.get("native_revision")
        date_raw = starting.get("date_raw")
        played_character = starting.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        diagnostics = starting.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if (
            public_revision != expected_revision
            or request.expected_revision != expected_revision
            or native_revision != request.expected_native_revision
            or connection_generation
            != request.expected_connection_generation
            or player_character_id != request.expected_player_character_id
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
        ):
            raise PreSubmissionRevisionMismatchError(
                "native ZhongGuo scoreboard action source binding is stale"
            )
        bridge_capabilities = set(
            _string_list(self.capabilities().get("bridge_capabilities"))
        )
        if (
            ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY
            not in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "native DLL lacks the fail-closed scoreboard action transport"
            )
        production_advertised = (
            ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY
            in bridge_capabilities
        )
        result = self._execute_primitive_step(
            ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
            expected_revision=expected_revision,
            required_capability=(
                ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY
            ),
            request_fields={
                "request_nonce": request.request_nonce,
                "action": request.action,
                # Wire-only name avoids collision with the native protocol's
                # reserved expected_revision (the native snapshot revision).
                "expected_public_revision": request.expected_revision,
                "expected_native_revision": request.expected_native_revision,
                "expected_connection_generation": (
                    request.expected_connection_generation
                ),
                "expected_player_character_id": (
                    request.expected_player_character_id
                ),
                "expected_provider_session_id": (
                    request.expected_provider_session_id
                ),
                "expected_observation_sequence": (
                    request.expected_observation_sequence
                ),
                "expected_observed_state_revision": (
                    request.expected_observed_state_revision
                ),
                "expected_tree_fingerprint_v1": (
                    request.expected_tree_fingerprint_v1
                ),
                "expected_semantic_fingerprint_v1": (
                    request.expected_semantic_fingerprint_v1
                ),
                "expected_window_instance_pointer": (
                    request.expected_window_instance_pointer
                ),
                "expected_target_instance_pointer": (
                    request.expected_target_instance_pointer
                ),
                "expected_target_vtable_pointer": (
                    request.expected_target_vtable_pointer
                ),
            },
        )
        try:
            normalized = normalize_native_zhongguo_scoreboard_action_v1_result(
                result, expected_request=request
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard action returned a malformed "
                f"result: {error}"
            ) from error
        if (
            normalized["snapshot_revision"] != native_revision
            or normalized["production_capability_advertised"]
            is not production_advertised
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard action capability/revision mirror "
                "drifted"
            )
        ending = self.take_snapshot()
        ending_diagnostics = ending.get("diagnostics")
        ending_played_character = ending.get("played_character")
        if not (
            _same_paused_native_frame(starting, ending)
            and ending.get("revision") == public_revision
            and ending.get("date_raw") == date_raw
            and isinstance(ending_diagnostics, dict)
            and ending_diagnostics.get("connection_generation")
            == connection_generation
            and isinstance(ending_played_character, dict)
            and ending_played_character.get("character_id")
            == player_character_id
        ):
            raise BridgeUnavailableError(
                "native ZhongGuo scoreboard action crossed its paused binding"
            )
        return {
            **normalized,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": public_revision,
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
        }

    def _execute_loaded_feature_manifest_v1_query(
        self,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read effective build flags and script DLC keys while paused."""
        step = QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native loaded-feature query requires a paused snapshot"
            )
        date_raw = _date_raw(starting, "loaded-feature starting snapshot")
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native loaded-feature query lacks a native revision"
            )
        starting_revision = int(starting["revision"])
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else starting_revision
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "loaded_feature_manifest",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native loaded-feature query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native loaded-feature query lacks query_sequence"
            )
        try:
            normalized = normalize_loaded_feature_manifest_v1(
                result.get("loaded_feature_manifest"),
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native loaded-feature query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native loaded-feature envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native loaded-feature query crossed a snapshot revision"
            )
        mirror_keys = (
            "schema",
            "schema_version",
            "date_raw",
            "unavailable_reason",
            "build",
            "effective_feature_flags",
            "script_dlc_keys",
            "entitlements",
            "readiness",
            "provenance",
        )
        return {
            **result,
            "status": normalized["status"],
            "loaded_feature_manifest": normalized,
            "query_sequence": query_sequence,
            **{
                key: copy.deepcopy(normalized[key])
                for key in mirror_keys
            },
            "loaded_feature_manifest_ready": normalized["readiness"][
                "actionable_ready"
            ],
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def query_current_event_window_context_v1(
        self,
        event_instance_id: int,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Copy event identity, options, and lossy indicators while paused."""
        if (
            isinstance(event_instance_id, bool)
            or not isinstance(event_instance_id, int)
            or not 1 <= event_instance_id <= 2**31 - 1
        ):
            raise ValueError("event_instance_id must be a positive full int32")
        step = QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native event-window query requires a paused snapshot"
            )
        active_event = starting.get("active_event")
        if (
            not isinstance(active_event, dict)
            or active_event.get("instance_id") != event_instance_id
        ):
            raise BridgeUnavailableError(
                "active event ID does not match the current snapshot"
            )
        date_raw = _date_raw(starting, "event-window starting snapshot")
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native event-window query lacks a native revision"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(starting["revision"])
        )
        result = self._execute_primitive_step(
            step,
            expected_revision=selected_revision,
            required_capability=(
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            ),
            request_fields={"event_instance_id": event_instance_id},
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "current_event_window_context",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native event-window query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native event-window query lacks query_sequence"
            )
        try:
            normalized = normalize_current_event_window_context_v1(
                result.get("current_event_window_context"),
                expected_event_instance_id=event_instance_id,
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native event-window query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native event-window envelope status disagrees with frame"
            )
        current = self.take_snapshot()
        current_event = current.get("active_event")
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and isinstance(current_event, dict)
            and current_event.get("instance_id") == event_instance_id
        ):
            raise BridgeUnavailableError(
                "native event-window query crossed a snapshot revision"
            )
        mirror_keys = (
            "schema",
            "schema_version",
            "date_raw",
            "current_event_instance_id",
            "window_match_count",
            "unavailable_reason",
            "event_definition_key",
            "calculated_event_id",
            "runtime_stats_ordinal",
            "root_scope",
            "saved_scopes",
            "options",
            "readiness",
            "provenance",
        )
        return {
            **result,
            "status": normalized["status"],
            "current_event_window_context": normalized,
            "query_sequence": query_sequence,
            **{
                key: copy.deepcopy(normalized[key])
                for key in mirror_keys
            },
            "current_event_window_context_ready": normalized["readiness"][
                "option_presentation_ready"
            ],
            "current_event_effect_indicators_ready": normalized["readiness"][
                "effect_indicators_ready"
            ],
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
        }

    def query_pending_character_interaction_context_v1(
        self,
        pending_interaction_id: int,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Read exact routing, paid costs, and typed special-war binding."""
        pending_interaction_id = normalize_pending_interaction_id(
            pending_interaction_id
        )
        step = QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native pending-interaction query requires a paused snapshot"
            )
        pending = starting.get("pending_character_interaction")
        if (
            not isinstance(pending, dict)
            or pending.get("instance_id") != pending_interaction_id
        ):
            raise BridgeUnavailableError(
                "pending interaction ID does not match the current snapshot"
            )
        date_raw = _date_raw(starting, "pending-interaction starting snapshot")
        native_revision = starting.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native pending-interaction query lacks a native revision"
            )
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
                QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
            ),
            request_fields={
                "pending_interaction_id": pending_interaction_id,
            },
        )
        if (
            set(result)
            != {
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "pending_character_interaction_context",
                "backend_id",
            }
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "native pending-interaction query returned a malformed envelope"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "native pending-interaction query lacks query_sequence"
            )
        try:
            normalized = normalize_pending_character_interaction_context_v1(
                result.get("pending_character_interaction_context"),
                expected_pending_interaction_id=pending_interaction_id,
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "native pending-interaction query returned a malformed frame: "
                f"{error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "native pending-interaction envelope status disagrees with frame"
            )
        if normalized["status"] == "available":
            routing = normalized["routing"]
            roles = normalized["roles"]
            assert isinstance(routing, dict)
            assert isinstance(roles, dict)
            if (
                routing.get("auto_accept_notification")
                is not pending.get("auto_accept_notification")
                or roles.get("actor_character_id")
                != pending.get("sender_character_id")
            ):
                raise BridgeUnavailableError(
                    "native pending-interaction frame disagrees with snapshot mirror"
                )
        current = self.take_snapshot()
        current_pending = current.get("pending_character_interaction")
        if not (
            _same_paused_native_frame(starting, current)
            and starting.get("revision") == current.get("revision")
            and starting.get("date_raw") == current.get("date_raw")
            and isinstance(current_pending, dict)
            and current_pending.get("instance_id") == pending_interaction_id
            and current_pending == pending
        ):
            raise BridgeUnavailableError(
                "native pending-interaction query crossed a snapshot revision"
            )
        mirror_keys = (
            "schema",
            "schema_version",
            "date_raw",
            "pending_interaction_id",
            "reason",
            "build",
            "definition",
            "roles",
            "target",
            "send_options",
            "routing",
            "deadline",
            "auto_accept",
            "legality",
            "terms",
            "readiness",
            "provenance",
        )
        readiness = normalized["readiness"]
        assert isinstance(readiness, dict)
        return {
            **result,
            "status": normalized["status"],
            "pending_character_interaction_context": normalized,
            "query_sequence": query_sequence,
            **{
                key: copy.deepcopy(normalized[key])
                for key in mirror_keys
            },
            "pending_character_interaction_context_ready": readiness[
                "interaction_semantic_decision_ready"
            ],
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": native_revision,
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
            step,
            expected_revision=selected_revision,
            internal_semantic_snapshot=True,
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
        current = self.take_internal_semantic_snapshot()
        if not _same_paused_native_frame(starting, current):
            raise BridgeUnavailableError(
                "native war-termination terms query crossed a snapshot revision"
            )
        if _war_by_id(current, war_id) is None:
            raise BridgeUnavailableError(
                "native war-termination terms query returned after war ended"
            )
        generic_war_bound_current = terms.get(
            "generic_war_bound_current"
        )
        if generic_war_bound_current is not None:
            starting_war = _war_by_id(starting, war_id)
            casus_belli = terms.get("casus_belli")
            defender_id = (
                starting_war.get("primary_opponent_character_id")
                if isinstance(starting_war, dict)
                else None
            )
            cb_database_index = (
                casus_belli.get("database_index")
                if isinstance(casus_belli, dict)
                else None
            )
            bound_war_bound = (
                bind_raiktor_war_bound_regiment_public_frame(
                    generic_war_bound_current,
                    expected_snapshot_revision=starting.get("revision"),
                    expected_native_revision=starting.get(
                        "native_revision"
                    ),
                    expected_date_raw=starting.get("date_raw"),
                    expected_war_id=war_id,
                    expected_casus_belli_database_index=cb_database_index,
                    expected_attacker_character_id=starting.get(
                        "episode_character_id"
                    ),
                    expected_defender_character_id=defender_id,
                )
            )
            if bound_war_bound is None:
                raise BridgeUnavailableError(
                    "native generic war-bound payload disagrees with "
                    "the public paused frame"
                )
            terms = copy.deepcopy(terms)
            terms["generic_war_bound_current"] = bound_war_bound
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
        query_receipt = {
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
            "queried_connection_generation": connection_generation,
            "episode_run_id": starting.get("episode_run_id"),
        }
        aggregate = project_raiktor_surrender_six_domain(
            starting,
            terms,
            generic_war_bound_current_value=terms.get(
                "generic_war_bound_current"
            ),
        )
        aggregate_session = bind_raiktor_surrender_aggregate_session(
            starting,
            query_receipt,
            aggregate,
        )
        with self._driver_state_lock:
            self._war_termination_terms[war_id] = {
                "terms": copy.deepcopy(terms),
                "query_sequence": query_sequence,
                "cache_binding": cache_binding,
                "raiktor_surrender_aggregate_session": copy.deepcopy(
                    aggregate_session
                ),
            }
        return {
            **result,
            "war_termination_terms": terms,
            "query_sequence": query_sequence,
            **query_receipt,
            "raiktor_surrender_aggregate_session": aggregate_session,
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
            try:
                result = self._execute_primitive_step(
                    step,
                    expected_revision=selected_revision,
                    internal_semantic_snapshot=True,
                )
            except _NativeCommandRejectedError as error:
                if error.native_error not in (
                    _WAR_TERMINATION_REVISION_RETRY_ERRORS
                ):
                    raise
                refreshed = self.take_internal_semantic_snapshot()
                if _same_paused_native_frame(starting, refreshed):
                    raise
                raise PreSubmissionRevisionMismatchError(
                    "native war-termination query observed a newer native "
                    "snapshot before performing its read-only query"
                ) from error
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
            options = normalize_war_termination_options(
                result.get("war_termination_options"),
                expected_war_id=war_id,
            )
            identity_diff = _termination_options_war_identity_diff(
                options, war
            )
            if identity_diff:
                raise StepPostconditionError(
                    "native war-termination query does not match the active "
                    "war row",
                    step_result=_war_termination_query_mismatch_result(
                        step=step,
                        stage="starting_snapshot",
                        requested_war_id=war_id,
                        query_sequence=query_sequence,
                        snapshot=starting,
                        identity_diff=identity_diff,
                    ),
                    selected_step=step,
                )
            current = self.take_internal_semantic_snapshot()
            if not _same_paused_native_frame(starting, current):
                raise BridgeUnavailableError(
                    "native war-termination query crossed a snapshot revision"
                )
            current_war = _war_by_id(current, war_id)
            if current_war is None:
                raise BridgeUnavailableError(
                    "native war-termination query returned after the war ended"
                )
            identity_diff = _termination_options_war_identity_diff(
                options, current_war
            )
            if identity_diff:
                raise StepPostconditionError(
                    "native war-termination query does not match the active "
                    "war row",
                    step_result=_war_termination_query_mismatch_result(
                        step=step,
                        stage="post_query_snapshot",
                        requested_war_id=war_id,
                        query_sequence=query_sequence,
                        snapshot=current,
                        identity_diff=identity_diff,
                    ),
                    selected_step=step,
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
            active_war_signature = war_termination_active_war_signature(
                starting.get("active_wars")
            )
            negative_decision_signature = (
                war_termination_negative_query_signature(options)
            )
            played_character = starting.get("played_character")
            queried_character_id = (
                played_character.get("character_id")
                if isinstance(played_character, dict)
                else None
            )
            if (
                active_war_signature is None
                or negative_decision_signature is None
            ):
                raise BridgeUnavailableError(
                    "native war-termination query lacks a reusable exact "
                    "decision signature"
                )
            termination_query_context = {
                "schema_version": 1,
                "queried_date_raw": starting.get("date_raw"),
                "queried_connection_generation": connection_generation,
                "queried_episode_run_id": starting.get("episode_run_id"),
                "queried_character_id": queried_character_id,
                "active_war_signature": active_war_signature,
                "negative_decision_signature": (
                    negative_decision_signature
                ),
                # Duration is provenance only.  It must not invalidate a
                # seven-day lease merely because one game day elapsed.
                "queried_war_duration_days": options.get(
                    "war_duration_days"
                ),
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
                "queried_connection_generation": connection_generation,
                "queried_episode_run_id": starting.get("episode_run_id"),
                "termination_query_context": termination_query_context,
            }

        option_name = (
            "surrender" if surrender_war_id is not None else "white_peace"
        )
        if option_name != "white_peace":
            raise BridgeUnavailableError(
                "native surrender submission remains disabled by the "
                "minimal claim_cb counter-policy"
            )
        bridge_capabilities = set(
            _string_list(self.state.capabilities().get("bridge_capabilities"))
        )
        if not {
            QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
            QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
            OFFER_WHITE_PEACE_CAPABILITY,
        } <= bridge_capabilities:
            raise BridgeUnavailableError(
                "native white_peace submission lacks exact raw capabilities"
            )
        ready, reason, evidence = _claim_cb_white_peace_readiness(
            starting, war_id
        )
        if not ready:
            raise BridgeUnavailableError(
                "native white_peace fresh validation failed: " + reason
            )
        cooldown = _white_peace_proposal_cooldown(
            self._history_snapshot(),
            war_id=war_id,
            current_date_raw=starting.get("date_raw"),
            episode_run_id=starting.get("episode_run_id"),
        )
        if cooldown is not None:
            raise BridgeUnavailableError(
                "native white_peace proposal is suppressed by its 30-day "
                "same-WarID cooldown"
            )
        result = self._execute_primitive_step(
            step, expected_revision=selected_revision
        )
        if (
            set(result) != {"step", "accepted", "status", "backend_id"}
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") != "submitted"
        ):
            raise BridgeUnavailableError(
                "native white_peace queue returned a malformed ACK"
            )
        current = self.take_snapshot()
        starting_played = starting.get("played_character")
        current_played = current.get("played_character")
        starting_diagnostics = starting.get("diagnostics")
        current_diagnostics = current.get("diagnostics")
        if not (
            current.get("paused") is True
            and current.get("episode_run_id")
            == starting.get("episode_run_id")
            and isinstance(starting_diagnostics, dict)
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == starting_diagnostics.get("connection_generation")
            and current_diagnostics.get("bridge_pid")
            == starting_diagnostics.get("bridge_pid")
            and isinstance(starting_played, dict)
            and isinstance(current_played, dict)
            and current_played.get("character_id")
            == starting_played.get("character_id")
            and isinstance(starting.get("date_raw"), int)
            and not isinstance(starting.get("date_raw"), bool)
            and isinstance(current.get("date_raw"), int)
            and not isinstance(current.get("date_raw"), bool)
            and current.get("date_raw") == starting.get("date_raw")
        ):
            raise BridgeUnavailableError(
                "native white_peace ACK lacks a fresh paused postcondition"
            )
        remaining_war = _war_by_id(current, war_id)
        status = "applied" if remaining_war is None else "submitted_pending"
        options = evidence["options"]
        terms = evidence["terms"]
        white_peace = evidence["white_peace"]
        response = white_peace["recipient_response"]
        return {
            **result,
            "war_termination_result": {
                "status": status,
                "war_id": war_id,
                "outcome": "white_peace",
                "submitted_date_raw": starting.get("date_raw"),
                "observed_date_raw": current.get("date_raw"),
                "episode_run_id": starting.get("episode_run_id"),
                "starting_snapshot_id": starting.get("snapshot_id"),
                "observed_snapshot_id": current.get("snapshot_id"),
                "command_acknowledged": result.get("accepted") is True,
                "war_id_absent_after_ack": remaining_war is None,
                "recipient_decision_status_raw": response.get(
                    "decision_status_raw"
                ),
                "recipient_would_accept_now": response.get(
                    "would_accept_now"
                ),
                "casus_belli": copy.deepcopy(
                    options.get("active_casus_belli_identity")
                ),
                "claimant_character_id": terms.get(
                    "claimant_character_id"
                ),
                "target_title_ids": copy.deepcopy(
                    terms.get("target_title_ids")
                ),
                "remaining_active_war": (
                    copy.deepcopy(remaining_war)
                    if isinstance(remaining_war, dict)
                    else None
                ),
            },
        }

    def restore_phase2_span_source_checkpoint_v1(
        self,
        *,
        checkpoint_path: str,
        expected_checkpoint_bytes: int,
        expected_checkpoint_sha256: str,
        expected_save_lineage_id: str,
        expected_event_definition_key: str,
        expected_owner_character_id: int,
        expected_player_character_id: int,
        expected_date_raw: int,
        allow_generic_character_rebind: bool,
        allow_fixture: bool,
        allow_console: bool,
    ) -> dict[str, object]:
        """Restore one registry-bound Phase2 source through native lifecycle.

        This is deliberately not an action-step or a general save loader.  It
        accepts the complete identity already authenticated by the Phase2
        source registry, stages only those bytes as the managed checkpoint,
        and then reuses the ordinary restore-checkpoint lifecycle.
        """

        if not (
            allow_generic_character_rebind is False
            and allow_fixture is False
            and allow_console is False
        ):
            raise BridgeUnavailableError(
                "Phase2 source restore forbids generic rebind, fixture, and console"
            )
        if not isinstance(checkpoint_path, str) or not checkpoint_path:
            raise ValueError("checkpoint_path must be a nonempty absolute path")
        source_path = Path(checkpoint_path)
        if not source_path.is_absolute():
            raise ValueError("checkpoint_path must be absolute")
        source_path = source_path.resolve()
        if not source_path.is_file():
            raise BridgeUnavailableError(
                f"Phase2 source checkpoint is absent: {source_path}"
            )
        if (
            isinstance(expected_checkpoint_bytes, bool)
            or not isinstance(expected_checkpoint_bytes, int)
            or expected_checkpoint_bytes <= 0
        ):
            raise ValueError(
                "expected_checkpoint_bytes must be a positive integer"
            )
        normalized_sha256 = (
            expected_checkpoint_sha256.lower()
            if isinstance(expected_checkpoint_sha256, str)
            else ""
        )
        if (
            len(normalized_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in normalized_sha256
            )
        ):
            raise ValueError("expected_checkpoint_sha256 must be a SHA-256 digest")
        if (
            not isinstance(expected_save_lineage_id, str)
            or not expected_save_lineage_id
        ):
            raise ValueError("expected_save_lineage_id must be nonempty")
        if (
            not isinstance(expected_event_definition_key, str)
            or not expected_event_definition_key
        ):
            raise ValueError("expected_event_definition_key must be nonempty")
        for value, name in (
            (expected_owner_character_id, "expected_owner_character_id"),
            (expected_player_character_id, "expected_player_character_id"),
        ):
            if not _positive_native_id(value):
                raise ValueError(f"{name} must be a positive native ID")
        if isinstance(expected_date_raw, bool) or not isinstance(
            expected_date_raw, int
        ):
            raise ValueError("expected_date_raw must be an integer")
        if (
            source_path.stat().st_size != expected_checkpoint_bytes
            or _sha256_file(source_path) != normalized_sha256
        ):
            raise BridgeUnavailableError(
                "Phase2 source checkpoint bytes differ from the registry"
            )

        managed_path = self._checkpoint_path()
        if self.state_dir is None or managed_path is None:
            raise UnsupportedStepError(
                "Phase2 source restore requires managed state_dir and save_dir"
            )

        with self._phase2_source_restore_lock:
            starting = self.take_snapshot()
            diagnostics = starting.get("diagnostics")
            diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
            starting_pid = diagnostics.get("bridge_pid")
            starting_generation = diagnostics.get("connection_generation")
            starting_revision = starting.get("revision")
            if not (
                starting.get("paused") is True
                and starting.get("map_ready") is True
                and _positive_native_id(starting_pid)
                and _positive_native_id(starting_generation)
                and isinstance(starting_revision, int)
                and not isinstance(starting_revision, bool)
                and starting_revision >= 0
            ):
                raise BridgeUnavailableError(
                    "Phase2 source restore requires a paused map-ready "
                    "PID/generation binding"
                )
            with self._driver_state_lock:
                episode_run_id = self._episode_run_id
                session_bridge_pid = self._session_bridge_pid
            if (
                not isinstance(episode_run_id, str)
                or not episode_run_id
                or session_bridge_pid != starting_pid
            ):
                raise BridgeUnavailableError(
                    "Phase2 source restore requires an active managed episode binding"
                )

            managed_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path != managed_path.resolve():
                temporary = managed_path.with_name(
                    f".{managed_path.name}.phase2-{uuid.uuid4().hex}.tmp"
                )
                try:
                    shutil.copyfile(source_path, temporary)
                    if (
                        temporary.stat().st_size != expected_checkpoint_bytes
                        or _sha256_file(temporary) != normalized_sha256
                    ):
                        raise BridgeUnavailableError(
                            "Phase2 staged checkpoint differs from the registry"
                        )
                    os.replace(temporary, managed_path)
                finally:
                    try:
                        temporary.unlink()
                    except FileNotFoundError:
                        pass
            if (
                managed_path.stat().st_size != expected_checkpoint_bytes
                or _sha256_file(managed_path) != normalized_sha256
            ):
                raise BridgeUnavailableError(
                    "Phase2 managed checkpoint differs after staging"
                )

            with self._driver_state_lock:
                history_index = len(self._command_history) + 1
                checkpoint = {
                    "status": "registered_source",
                    "path": str(managed_path.resolve()),
                    "source_path": str(source_path),
                    "name": managed_path.name,
                    "size": expected_checkpoint_bytes,
                    "sha256": normalized_sha256,
                    "date_raw": expected_date_raw,
                    "history_index": history_index,
                    "episode_character_id": expected_player_character_id,
                    "episode_run_id": episode_run_id,
                    "save_lineage_id": expected_save_lineage_id,
                    "event_definition_key": expected_event_definition_key,
                    "owner_character_id": expected_owner_character_id,
                    "player_character_id": expected_player_character_id,
                    "strategy": "phase2-canonical-source-registry-v1",
                }
                stage_result = {
                    "step": _PHASE2_SOURCE_CHECKPOINT_STAGE_STEP,
                    "accepted": True,
                    "status": "registered_source",
                    "checkpoint": copy.deepcopy(checkpoint),
                    "fixture_used": False,
                    "console_used": False,
                    "generic_character_rebind_used": False,
                }
                self._command_history.append(
                    {
                        "index": history_index,
                        "command": _PHASE2_SOURCE_CHECKPOINT_STAGE_STEP,
                        "ok": True,
                        "result": stage_result,
                    }
                )
                self._episode_character_id = expected_player_character_id
                self._last_checkpoint = checkpoint
                self._rollback_war_failures = []
                self._rollback_war_failures_migration_required = False
                self._driver_state_dirty = True
            self._persist_driver_state()

            restored = self.execute_step(
                _RESTORE_CHECKPOINT_STEP,
                expected_revision=int(starting_revision),
            )
            restored_checkpoint = restored.get("checkpoint")
            lifecycle = restored.get("lifecycle")
            ending = self.take_snapshot()
            ending_diagnostics = ending.get("diagnostics")
            ending_diagnostics = (
                ending_diagnostics
                if isinstance(ending_diagnostics, dict)
                else {}
            )
            ending_player = ending.get("played_character")
            ending_player_id = (
                ending_player.get("character_id")
                if isinstance(ending_player, dict)
                else None
            )
            ending_pid = ending_diagnostics.get("bridge_pid")
            ending_generation = ending_diagnostics.get(
                "connection_generation"
            )
            if not (
                isinstance(restored_checkpoint, dict)
                and restored_checkpoint.get("status") == "restored"
                and restored_checkpoint.get("size") == expected_checkpoint_bytes
                and restored_checkpoint.get("sha256") == normalized_sha256
                and restored.get("restored_date_raw") == expected_date_raw
                and isinstance(lifecycle, dict)
                and lifecycle.get("previous_pid") == starting_pid
                and lifecycle.get("pid") == ending_pid
                and lifecycle.get("previous_connection_generation")
                == starting_generation
                and lifecycle.get("connection_generation") == ending_generation
                and ending_pid != starting_pid
                and ending_generation == starting_generation + 1
                and ending.get("paused") is True
                and ending.get("map_ready") is True
                and ending.get("date_raw") == expected_date_raw
                and ending_player_id == expected_player_character_id
            ):
                raise BridgeUnavailableError(
                    "Phase2 source restore lacks exact "
                    "checkpoint/session/player/date proof"
                )
            return {
                "schema_version": 1,
                "result": "GREEN",
                "provider_observed": True,
                "restore_materialized": True,
                "checkpoint_sha256": normalized_sha256.upper(),
                "checkpoint_bytes": expected_checkpoint_bytes,
                "save_lineage_id": expected_save_lineage_id,
                "event_definition_key": expected_event_definition_key,
                "event_identity_validation": "runner_exact_query_required",
                "owner_character_id": expected_owner_character_id,
                "player_character_id": expected_player_character_id,
                "date_raw": expected_date_raw,
                "checkpoint": {
                    "source_path": str(source_path),
                    "managed_path": str(managed_path.resolve()),
                    "bytes": expected_checkpoint_bytes,
                    "sha256": normalized_sha256.upper(),
                },
                "lifecycle": copy.deepcopy(lifecycle),
                "snapshot_id": ending.get("snapshot_id"),
                "revision": ending.get("revision"),
                "native_revision": ending.get("native_revision"),
                "fixture_used": False,
                "console_used": False,
                "generic_character_rebind_used": False,
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
                raise PreSubmissionRevisionMismatchError(
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
                raise PreSubmissionRevisionMismatchError(
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
                raise PreSubmissionRevisionMismatchError(
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
        starting = self.take_internal_semantic_snapshot()
        starting_revision = int(starting["revision"])
        if expected_revision is None:
            raise BridgeUnavailableError(
                "route-contact one-day advance requires expected_revision"
            )
        _validate_revision(expected_revision, "expected_revision")
        if expected_revision != starting_revision:
            raise PreSubmissionRevisionMismatchError(
                "route-contact one-day advance revision mismatch: "
                f"expected {expected_revision}, current {starting_revision}"
            )
        with self._history_lock:
            proof = _fresh_route_contact_advance_proofs(
                starting, self._command_history
            ).get(step)
        if not isinstance(proof, dict):
            raise BridgeUnavailableError(
                "route-contact one-day advance proof is stale or incomplete"
            )
        proof_kind = proof.get("proof_kind")
        preferred_timeline_speed = (
            self.route_contact_effective_timeline_speed
            if proof_kind == "contact_free"
            else 1
        )
        result = self._execute_life_advance(
            expected_revision=expected_revision,
            exact_one_day=True,
            exact_one_day_proof_kind=(
                str(proof_kind) if isinstance(proof_kind, str) else None
            ),
            exact_one_day_preferred_speed=preferred_timeline_speed,
            result_step=step,
        )
        if proof.get("proof_kind") != "unavoidable_current_province_contact":
            return result
        strict_endpoint_followup = proof.get("strict_endpoint_followup") is True
        ending = self.take_internal_semantic_snapshot()
        postcondition = _unavoidable_contact_transition_postcondition(
            starting,
            ending,
            proof=proof,
            strong_only=strict_endpoint_followup,
        )
        if postcondition is None:
            result = _retarget_timeline_step_result(result, ending)
            prior_boundary = proof.get("prior_contact_boundary")
            if strict_endpoint_followup and isinstance(prior_boundary, dict):
                result["contact_followup"] = {
                    "status": "pending_strong_transition",
                    "episode_run_id": starting.get("episode_run_id"),
                    "subject_army_id": proof.get("subject_army_id"),
                    "contact_province_id": prior_boundary.get(
                        "contact_province_id"
                    ),
                    "starting_date_raw": starting.get("date_raw"),
                    "ending_date_raw": ending.get("date_raw"),
                    "prior_boundary_ending_date_raw": prior_boundary.get(
                        "ending_date_raw"
                    ),
                }
            refresh_deadline = time.monotonic() + self.command_timeout_seconds
            refresh_from_revision = ending.get("revision")
            refresh_from_native_revision = ending.get("native_revision")
            refresh: dict[str, object] = {
                "attempted": True,
                "ack_status": None,
                "from_snapshot_id": ending.get("snapshot_id"),
                "from_revision": refresh_from_revision,
                "from_native_revision": refresh_from_native_revision,
                "to_snapshot_id": None,
                "to_revision": None,
                "to_native_revision": None,
                "date_raw": ending.get("date_raw"),
            }
            result["contact_refresh"] = refresh
            if not (
                ending.get("map_ready") is True
                and ending.get("paused") is True
            ):
                raise StepPostconditionError(
                    "the proof-bound unavoidable contact day ended without "
                    "a paused map eligible for one same-date refresh",
                    step_result=result,
                    selected_step=step,
                )
            try:
                remaining = refresh_deadline - time.monotonic()
                if remaining <= 0:
                    raise BridgeUnavailableError(
                        "same-date unavoidable-contact refresh timed out "
                        "before pause-map submission"
                    )
                refresh_result = self._execute_primitive_step(
                    "pause-map",
                    expected_revision=None,
                    timeout_seconds=remaining,
                    internal_semantic_snapshot=True,
                )
                result["actions"] = [
                    *copy.deepcopy(
                        result.get("actions")
                        if isinstance(result.get("actions"), list)
                        else []
                    ),
                    {"step": "pause-map", "result": refresh_result},
                ]
                refresh["ack_status"] = _timeline_ack_status(refresh_result)
                if refresh["ack_status"] != "already_paused":
                    raise BridgeUnavailableError(
                        "same-date unavoidable-contact refresh expected an "
                        "already_paused ACK, got "
                        f"{refresh['ack_status']}"
                    )
                remaining = max(0.0, refresh_deadline - time.monotonic())
                refreshed = self._wait_for_life_advance_snapshot(
                    ending,
                    lambda candidate: _newer_native_contact_refresh_frame(
                        ending, candidate
                    ),
                    timeout_seconds=remaining,
                )
                refresh.update(
                    {
                        "to_snapshot_id": refreshed.get("snapshot_id"),
                        "to_revision": refreshed.get("revision"),
                        "to_native_revision": refreshed.get(
                            "native_revision"
                        ),
                    }
                )
                result = _retarget_timeline_step_result(result, refreshed)
                result["contact_refresh"] = refresh
                if not _same_paused_contact_refresh_owner(ending, refreshed):
                    raise BridgeUnavailableError(
                        "same-date unavoidable-contact refresh did not "
                        "publish a newer frame for the same paused timeline "
                        "owner"
                    )
            except (BridgeUnavailableError, UnsupportedStepError) as error:
                raise StepPostconditionError(
                    str(error),
                    step_result=result,
                    selected_step=step,
                ) from error
            ending = refreshed
            postcondition = _unavoidable_contact_transition_postcondition(
                starting,
                ending,
                proof=proof,
                strong_only=strict_endpoint_followup,
            )
            if postcondition is None:
                postcondition = (
                    None
                    if strict_endpoint_followup
                    else _predicted_contact_boundary_postcondition(
                        starting,
                        ending,
                        proof=proof,
                    )
                )
            if postcondition is None:
                transition_requirement = (
                    "episode, war, subject-army, combat, or retreat transition"
                    if strict_endpoint_followup
                    else "combat, retreat, war/episode transition, or hostile "
                    "state change"
                )
                if strict_endpoint_followup:
                    contact_followup = result.get("contact_followup")
                    if isinstance(contact_followup, dict):
                        contact_followup["status"] = (
                            "exhausted_without_strong_transition"
                        )
                        contact_followup["ending_date_raw"] = ending.get(
                            "date_raw"
                        )
                raise StepPostconditionError(
                    "the proof-bound unavoidable contact day advanced and "
                    "published one same-date refresh, but the required "
                    "transition was not observed; required_transition="
                    f"{transition_requirement}; refreshed_revision="
                    f"{ending.get('revision')}, refreshed_native_revision="
                    f"{ending.get('native_revision')}",
                    step_result=result,
                    selected_step=step,
                )
        if postcondition is not None and strict_endpoint_followup:
            result.pop("contact_followup", None)
        return {**result, "contact_transition": postcondition}

    def _execute_battle_sentinel_advance(
        self,
        step: str,
        *,
        expected_revision: int | None,
        starting_snapshot: dict[str, object] | None = None,
        requested_scope: str = "active_battle",
        requested_route: tuple[int, int, int] | None = None,
        requested_objective_hold: tuple[int, int, int, int] | None = None,
    ) -> dict[str, object]:
        """Run one explicitly scoped tactical tranche without Python polling.

        The application-main sentinel owns every intermediate daily boundary.
        Python submits exactly one resume and observes only ordinary state
        frames until the sentinel has paused CK3.  ``pause-map`` is reserved
        for failed-transaction cleanup.
        """
        requested_decision_target = (
            parse_battle_decision_epoch_advance_step(step)
        )
        parsed_route_request = parse_committed_route_sentinel_advance_step(
            step
        )
        parsed_route_speed = parse_committed_route_sentinel_advance_speed(
            step
        )
        parsed_objective_hold_request = (
            parse_war_objective_hold_sentinel_advance_step(step)
        )
        parsed_objective_hold_speed = (
            parse_war_objective_hold_sentinel_advance_speed(step)
        )
        if parsed_objective_hold_request is not None:
            if (
                requested_scope != "stationary_objective_hold"
                or requested_objective_hold
                != parsed_objective_hold_request
                or requested_route is not None
            ):
                raise UnsupportedStepError(
                    "war-objective hold sentinel request scope is inconsistent"
                )
            if parsed_objective_hold_speed is None:
                raise UnsupportedStepError(
                    "war-objective hold sentinel speed binding is malformed"
                )
            speed = parsed_objective_hold_speed
            wire_mode = "decision"
            status_mode = "decision_epoch"
        elif parsed_route_request is not None:
            if (
                requested_scope != "committed_route"
                or requested_route != parsed_route_request
                or requested_objective_hold is not None
            ):
                raise UnsupportedStepError(
                    "committed-route sentinel request scope is inconsistent"
                )
            if parsed_route_speed is None:
                raise UnsupportedStepError(
                    "committed-route sentinel speed binding is malformed"
                )
            speed = parsed_route_speed
            wire_mode = "decision"
            status_mode = "decision_epoch"
        elif (
            step == BATTLE_DECISION_EPOCH_ADVANCE_STEP
            or requested_decision_target is not None
        ):
            if (
                requested_scope != "active_battle"
                or requested_route is not None
                or requested_objective_hold is not None
            ):
                raise UnsupportedStepError(
                    "battle decision sentinel request scope is inconsistent"
                )
            speed = 3
            wire_mode = "decision"
            status_mode = "decision_epoch"
        elif step == BATTLE_TERMINAL_CRUISE_STEP:
            if (
                requested_scope != "active_battle"
                or requested_route is not None
                or requested_objective_hold is not None
            ):
                raise UnsupportedStepError(
                    "battle terminal sentinel request scope is inconsistent"
                )
            speed = 5
            wire_mode = "terminal"
            status_mode = "terminal_or_sentinel"
        else:
            raise UnsupportedStepError(
                f"unknown battle sentinel composite {step}"
            )

        starting = (
            copy.deepcopy(starting_snapshot)
            if starting_snapshot is not None
            else self.take_internal_semantic_snapshot()
        )
        starting_revision = int(starting["revision"])
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != starting_revision:
                raise PreSubmissionRevisionMismatchError(
                    f"native {step} revision mismatch: expected "
                    f"{expected_revision}, current {starting_revision}"
                )
        if not (
            starting.get("map_ready") is True
            and starting.get("paused") is True
        ):
            raise BridgeUnavailableError(
                f"native {step} requires a paused, map-ready frame"
            )
        if starting.get("active_event") is not None or starting.get(
            "pending_character_interaction"
        ) is not None:
            raise BridgeUnavailableError(
                f"native {step} cannot bypass a pending player decision"
            )
        watch_army_ids = _battle_sentinel_watch_army_ids(starting)
        if watch_army_ids is None:
            raise BridgeUnavailableError(
                f"native {step} requires the complete controllable ArmyID set"
            )
        active_combat_at_start = _battle_sentinel_has_active_combat(
            starting, watch_army_ids
        )
        active_retreat_at_start = _battle_sentinel_has_active_retreat(
            starting, watch_army_ids
        )
        hold_admission: dict[str, object] | None = None
        if requested_scope == "active_battle":
            if not active_combat_at_start:
                raise BridgeUnavailableError(
                    f"native {step} active-battle scope requires active combat"
                )
        elif requested_scope == "committed_route":
            if parsed_route_request is None:
                raise UnsupportedStepError(
                    "committed-route sentinel lacks its typed request"
                )
            if active_combat_at_start or active_retreat_at_start:
                raise BridgeUnavailableError(
                    f"native {step} committed-route scope rejects any watched "
                    "active combat or retreat"
                )
            if not _battle_sentinel_matches_committed_route(
                starting,
                watch_army_ids,
                subject_army_id=parsed_route_request[0],
                target_province_id=parsed_route_request[1],
            ):
                raise BridgeUnavailableError(
                    f"native {step} does not match the requested subject's "
                    "complete nonempty committed route"
                )
        elif requested_scope == "stationary_objective_hold":
            if parsed_objective_hold_request is None:
                raise UnsupportedStepError(
                    "war-objective hold sentinel lacks its typed request"
                )
            hold_admission = _battle_sentinel_stationary_objective_hold_state(
                starting,
                watch_army_ids,
                war_id=parsed_objective_hold_request[0],
                subject_army_id=parsed_objective_hold_request[1],
                objective_province_id=parsed_objective_hold_request[2],
            )
            if hold_admission.get("status") != "matched":
                raise BridgeUnavailableError(
                    f"native {step} stationary-objective admission failed: "
                    f"{hold_admission.get('reason')}"
                )
        else:
            raise UnsupportedStepError(
                f"native {step} has unknown sentinel scope {requested_scope!r}"
            )
        sentinel_scope = requested_scope
        if requested_scope in {
            "committed_route",
            "stationary_objective_hold",
        }:
            if speed != self.route_contact_timeline_speed:
                raise UnsupportedStepError(
                    f"native {step} speed {speed} does not match configured "
                    f"noncombat sentinel speed {self.route_contact_timeline_speed}"
                )
            if not (
                self.allow_route_contact_high_speed_ab
                or _noncombat_sentinel_scope_speed_live_ready(
                    requested_scope,
                    speed,
                )
            ):
                raise UnsupportedStepError(
                    f"native {step} speed {speed} lacks an explicit A/B or "
                    "scope-specific live gate"
                )
        bridge_capabilities = set(
            _string_list(
                self.state.capabilities().get("bridge_capabilities")
            )
        )
        if not (
            _TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES
            <= bridge_capabilities
        ):
            raise UnsupportedStepError(
                "native DLL lacks the exact tactical sentinel arm/status pair"
            )

        starting_date_raw = _date_raw(starting, f"{step} starting snapshot")
        fallback_target_date_raw = (
            starting_date_raw + _BATTLE_SENTINEL_FALLBACK_DAYS * 24
        )
        target_date_raw = (
            parsed_objective_hold_request[3]
            if parsed_objective_hold_request is not None
            else parsed_route_request[2]
            if parsed_route_request is not None
            else requested_decision_target
            if requested_decision_target is not None
            else fallback_target_date_raw
        )
        target_delta_raw = target_date_raw - starting_date_raw
        maximum_horizon_days = (
            7
            if parsed_objective_hold_request is not None
            else _BATTLE_SENTINEL_FALLBACK_DAYS
        )
        if not (
            24 <= target_delta_raw <= maximum_horizon_days * 24
            and target_delta_raw % 24 == 0
        ):
            raise BridgeUnavailableError(
                "native battle decision-epoch target must be 1.."
                f"{maximum_horizon_days} whole days after the bound "
                "starting frame"
            )
        arm_step = (
            f"{_TACTICAL_DAILY_SENTINEL_ARM_PREFIX}"
            f"{starting_date_raw}-to-{target_date_raw}-speed-{speed}-"
            f"mode-{wire_mode}-a-{len(watch_army_ids)}-"
            + "-".join(str(army_id) for army_id in watch_army_ids)
        )
        actions: list[dict[str, object]] = []
        current = starting
        arm_status: dict[str, object] | None = None
        sentinel_status: dict[str, object] | None = None
        player_decision_boundary: dict[str, object] | None = None
        player_decision_boundary_cancel: dict[str, object] | None = None
        cleanup_error: str | None = None
        try:
            speed_step = f"set-speed-{speed}"
            speed_result = self._execute_composite_primitive(
                speed_step, current
            )
            actions.append({"step": speed_step, "result": speed_result})
            current = self._wait_for_life_advance_snapshot(
                self.take_internal_semantic_snapshot(),
                lambda snapshot: snapshot.get("speed") == speed,
                timeout_seconds=self.command_timeout_seconds,
            )
            if current.get("speed") != speed:
                raise BridgeUnavailableError(
                    f"native {step} did not observe speed {speed}"
                )

            arm_result = self._execute_primitive_step(
                arm_step,
                expected_revision=None,
                required_capability=(
                    _TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY
                ),
                internal_semantic_snapshot=True,
            )
            actions.append({"step": arm_step, "result": arm_result})
            arm_status = _normalize_tactical_daily_sentinel_status(
                arm_result.get("tactical_daily_sentinel")
            )
            _validate_tactical_daily_sentinel_arm(
                arm_result,
                arm_status,
                arm_step=arm_step,
                starting_date_raw=starting_date_raw,
                target_date_raw=target_date_raw,
                speed=speed,
                mode=status_mode,
                watch_army_ids=watch_army_ids,
                sentinel_scope=sentinel_scope,
            )

            resume_result = self._execute_primitive_step(
                "resume-map",
                expected_revision=None,
                internal_semantic_snapshot=True,
            )
            actions.append({"step": "resume-map", "result": resume_result})

            def running_or_native_stop(
                snapshot: dict[str, object],
            ) -> bool:
                date_raw = snapshot.get("date_raw")
                return bool(
                    snapshot.get("paused") is False
                    or (
                        snapshot.get("paused") is True
                        and isinstance(date_raw, int)
                        and not isinstance(date_raw, bool)
                        and date_raw > starting_date_raw
                    )
                )

            current = self._wait_for_life_advance_snapshot(
                self.take_internal_semantic_snapshot(),
                running_or_native_stop,
                timeout_seconds=self.command_timeout_seconds,
            )
            if not running_or_native_stop(current):
                raise BridgeUnavailableError(
                    f"native {step} single resume reached neither a running "
                    "frame nor a native sentinel stop"
                )
            if current.get("paused") is not True:
                current = self._wait_for_life_advance_snapshot(
                    current,
                    lambda snapshot: bool(
                        snapshot.get("paused") is True
                        or _battle_sentinel_player_decision_boundary(snapshot)
                        is not None
                    ),
                    timeout_seconds=self.life_advance_timeout_seconds,
                )
            observed_boundary = (
                _battle_sentinel_player_decision_boundary(current)
                or _battle_sentinel_active_war_set_boundary(
                    starting, current
                )
            )
            new_decision_boundary = bool(
                observed_boundary is not None
                and (
                    observed_boundary.get("kind")
                    == "active_war_set_changed"
                    or _battle_sentinel_player_decision_is_new(
                        starting, current
                    )
                )
            )
            running_boundary = (
                observed_boundary
                if new_decision_boundary
                and current.get("paused") is not True
                else None
            )
            if (
                new_decision_boundary
                and current.get("paused") is True
            ):
                player_decision_boundary = observed_boundary
            if current.get("paused") is not True:
                before_pause_inspection = current
                boundary_pause_actions: list[dict[str, object]] = []
                paused_inspection = self._pause_life_advance(
                    current, boundary_pause_actions
                )
                inspected_boundary = (
                    _battle_sentinel_player_decision_boundary(
                        paused_inspection
                    )
                )
                boundary_confirmed = bool(
                    len(boundary_pause_actions) == 1
                    and inspected_boundary is not None
                    and _fresh_battle_sentinel_player_decision_boundary(
                        before_pause_inspection,
                        paused_inspection,
                        expected_boundary=running_boundary,
                    )
                    and _battle_sentinel_player_decision_is_new(
                        starting, paused_inspection
                    )
                )
                purpose = (
                    "player_decision_boundary_stabilization"
                    if boundary_confirmed
                    else "managed_failure_cleanup"
                )
                for action in boundary_pause_actions:
                    actions.append({**action, "purpose": purpose})
                current = paused_inspection
                if boundary_confirmed:
                    player_decision_boundary = inspected_boundary
                elif running_boundary is not None:
                    raise BridgeUnavailableError(
                        "native tactical sentinel player-decision boundary "
                        "did not stabilize on one fresh paused frame"
                    )
                else:
                    raise BridgeUnavailableError(
                        f"native {step} timed out before a native sentinel "
                        "pause"
                    )
            if current.get("paused") is not True:
                raise BridgeUnavailableError(
                    f"native {step} timed out before a native sentinel pause"
                )

            def query_tactical_daily_sentinel() -> dict[str, object]:
                status_result = self._execute_primitive_step(
                    _TACTICAL_DAILY_SENTINEL_STATUS_STEP,
                    expected_revision=None,
                    required_capability=(
                        _TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY
                    ),
                    internal_semantic_snapshot=True,
                )
                actions.append(
                    {
                        "step": _TACTICAL_DAILY_SENTINEL_STATUS_STEP,
                        "result": status_result,
                    }
                )
                return _normalize_tactical_daily_sentinel_status(
                    status_result.get("tactical_daily_sentinel")
                )

            sentinel_status = query_tactical_daily_sentinel()
            if player_decision_boundary is not None:
                generation = arm_status.get("generation")
                if (
                    isinstance(generation, bool)
                    or not isinstance(generation, int)
                    or generation <= 0
                ):
                    raise BridgeUnavailableError(
                        "native tactical sentinel boundary lacks an armed "
                        "generation"
                    )
                sentinel_state = sentinel_status.get("state")
                if sentinel_state == "armed":
                    if sentinel_status.get("generation") != generation:
                        raise BridgeUnavailableError(
                            "native tactical sentinel boundary armed a "
                            "different generation"
                        )
                    cancel_step = (
                        f"{_TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX}"
                        f"{generation}"
                    )
                    cancel_result = self._execute_primitive_step(
                        cancel_step,
                        expected_revision=None,
                        required_capability=(
                            _TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY
                        ),
                        internal_semantic_snapshot=True,
                    )
                    actions.append(
                        {"step": cancel_step, "result": cancel_result}
                    )
                    if not (
                        cancel_result.get("step") == cancel_step
                        and cancel_result.get("accepted") is True
                        and cancel_result.get("status") == "canceled"
                    ):
                        raise BridgeUnavailableError(
                            "native tactical sentinel boundary cancel was "
                            "not accepted"
                        )
                    player_decision_boundary_cancel = {
                        "step": cancel_step,
                        "status": "canceled",
                        "generation": generation,
                    }
                    sentinel_status = query_tactical_daily_sentinel()
                elif sentinel_state != "triggered":
                    raise BridgeUnavailableError(
                        "native tactical sentinel player-decision boundary "
                        "is neither armed nor normally triggered"
                    )
            post_stop_snapshot = self.take_internal_semantic_snapshot()
            if not (
                post_stop_snapshot.get("paused") is True
                and post_stop_snapshot.get("map_ready") is True
                and post_stop_snapshot.get("date_raw")
                == current.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "native tactical sentinel lacks a fresh stable paused "
                    "post-stop snapshot"
                )
            post_stop_decision_boundary = (
                _battle_sentinel_player_decision_boundary(
                    post_stop_snapshot
                )
                or _battle_sentinel_active_war_set_boundary(
                    starting, post_stop_snapshot
                )
            )
            if player_decision_boundary is not None:
                if not _same_battle_sentinel_player_decision_boundary(
                    player_decision_boundary,
                    post_stop_decision_boundary,
                ):
                    raise BridgeUnavailableError(
                        "native tactical sentinel player-decision boundary "
                        "changed before its stable paused snapshot"
                    )
                player_decision_boundary = post_stop_decision_boundary
            objective_hold_post_stop = (
                _battle_sentinel_stationary_objective_hold_state(
                    post_stop_snapshot,
                    watch_army_ids,
                    war_id=parsed_objective_hold_request[0],
                    subject_army_id=parsed_objective_hold_request[1],
                    objective_province_id=(
                        parsed_objective_hold_request[2]
                    ),
                )
                if parsed_objective_hold_request is not None
                else None
            )
            if (
                isinstance(objective_hold_post_stop, dict)
                and objective_hold_post_stop.get("status") == "unavailable"
            ):
                raise BridgeUnavailableError(
                    "native war-objective hold post-stop scope could not be "
                    "revalidated"
                )
            current = post_stop_snapshot
            result = _battle_sentinel_step_result(
                step=step,
                starting=starting,
                ending=current,
                target_date_raw=target_date_raw,
                speed=speed,
                status_mode=status_mode,
                sentinel_scope=sentinel_scope,
                watch_army_ids=watch_army_ids,
                arm_status=arm_status,
                sentinel_status=sentinel_status,
                actions=actions,
                progress_status="postcondition_pending",
                cleanup_error=None,
                objective_hold_request=parsed_objective_hold_request,
                objective_hold_admission=hold_admission,
                objective_hold_post_stop=objective_hold_post_stop,
                player_decision_boundary=player_decision_boundary,
                player_decision_boundary_cancel=(
                    player_decision_boundary_cancel
                ),
            )
            if player_decision_boundary is not None:
                _validate_tactical_daily_sentinel_decision_boundary(
                    sentinel_status,
                    arm_status=arm_status,
                    starting_date_raw=starting_date_raw,
                    target_date_raw=target_date_raw,
                    ending_date_raw=int(result["ending_date_raw"]),
                    elapsed_days=int(result["elapsed_days"]),
                    speed=speed,
                    mode=status_mode,
                    watch_army_ids=watch_army_ids,
                    player_decision_boundary=player_decision_boundary,
                    player_decision_boundary_cancel=(
                        player_decision_boundary_cancel
                    ),
                )
            else:
                _validate_tactical_daily_sentinel_stop(
                    sentinel_status,
                    arm_status=arm_status,
                    starting_date_raw=starting_date_raw,
                    target_date_raw=target_date_raw,
                    ending_date_raw=int(result["ending_date_raw"]),
                    elapsed_days=int(result["elapsed_days"]),
                    speed=speed,
                    mode=status_mode,
                    watch_army_ids=watch_army_ids,
                )
            result["progress_status"] = "postcondition"
            return result
        except Exception as error:
            try:
                current = self.take_internal_semantic_snapshot()
                if current.get("paused") is not True:
                    cleanup_actions: list[dict[str, object]] = []
                    current = self._pause_life_advance(
                        current, cleanup_actions
                    )
                    for action in cleanup_actions:
                        actions.append(
                            {**action, "purpose": "managed_failure_cleanup"}
                        )
            except Exception as cleanup:
                cleanup_error = f"{type(cleanup).__name__}: {cleanup}"
            result = _battle_sentinel_step_result(
                step=step,
                starting=starting,
                ending=current,
                target_date_raw=target_date_raw,
                speed=speed,
                status_mode=status_mode,
                sentinel_scope=sentinel_scope,
                watch_army_ids=watch_army_ids,
                arm_status=arm_status,
                sentinel_status=sentinel_status,
                actions=actions,
                progress_status="postcondition_failed",
                cleanup_error=cleanup_error,
                objective_hold_request=parsed_objective_hold_request,
                objective_hold_admission=hold_admission,
                objective_hold_post_stop=None,
                player_decision_boundary=player_decision_boundary,
                player_decision_boundary_cancel=(
                    player_decision_boundary_cancel
                ),
            )
            message = f"native {step} postcondition failed: {error}"
            if cleanup_error is not None:
                message += f"; managed cleanup failed: {cleanup_error}"
            raise StepPostconditionError(
                message,
                step_result=result,
                selected_step=step,
            ) from error

    def _execute_life_advance(
        self,
        *,
        expected_revision: int | None,
        exact_one_day: bool = False,
        exact_one_day_proof_kind: str | None = None,
        exact_one_day_preferred_speed: int = 1,
        result_step: str = "life-advance",
        starting_snapshot: dict[str, object] | None = None,
    ) -> dict[str, object]:
        revision_validated_at_entry = starting_snapshot is not None
        starting = (
            copy.deepcopy(starting_snapshot)
            if starting_snapshot is not None
            else self.take_internal_semantic_snapshot()
        )
        if starting.get("map_ready") is not True:
            starting = self._wait_for_life_advance_snapshot(
                starting,
                lambda snapshot: snapshot.get("map_ready") is True,
                timeout_seconds=self.life_advance_timeout_seconds,
            )
        if starting.get("map_ready") is not True:
            raise BridgeUnavailableError(
                "native life-advance timed out waiting for map_ready"
            )
        identity_materialization: dict[str, object] | None = None
        if (
            starting.get("battle_control_snapshot_v1_status")
            == BATTLE_CONTROL_IDENTITY_PENDING_STATUS
        ):
            if exact_one_day or result_step != "life-advance":
                raise BridgeUnavailableError(
                    "battle identity materialization requires the explicit "
                    "life-advance composite"
                )
            identity_materialization = (
                _battle_identity_materialization_request(starting)
            )
            if identity_materialization is None:
                raise BridgeUnavailableError(
                    "battle identity materialization lacks an exact frozen "
                    "paused public-combat binding"
                )
            with self._history_lock:
                previous_materialization = (
                    _battle_identity_materialization_for_snapshot(
                        self._command_history,
                        starting,
                        subject_public_cunit_id=int(
                            identity_materialization[
                                "subject_public_cunit_id"
                            ]
                        ),
                    )
                )
            if previous_materialization is not None:
                raise BridgeUnavailableError(
                    "battle identity materialization was already consumed "
                    "for this revision; the next query must expose a "
                    "non-missing full CombatID"
                )
            exact_one_day = True
            exact_one_day_proof_kind = "battle_identity_materialization"
            exact_one_day_preferred_speed = 1
        starting_revision = int(starting["revision"])
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if (
                not revision_validated_at_entry
                and expected_revision != starting_revision
            ):
                if exact_one_day or starting.get("paused") is True:
                    raise PreSubmissionRevisionMismatchError(
                        "native life-advance revision mismatch: "
                        f"expected {expected_revision}, current "
                        f"{starting_revision}"
                    )
                # life-advance is a bounded timeline transaction and always
                # starts from a fresh native snapshot.  A date tick can race
                # the caller's prior observation, so refresh once rather than
                # rejecting the whole composite before it begins.
                starting = self.take_internal_semantic_snapshot()
                starting_revision = int(starting["revision"])
                if starting.get("active_event") is not None:
                    raise BridgeUnavailableError(
                        "native life-advance revision changed onto an active event"
                    )
        if exact_one_day and starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "exact one-day advance requires a paused map"
            )
        # Assault lifecycle checks are read-only.  Scan the owned transcript
        # under its lock so a timeline slice does not deep-copy an ever-growing
        # command history merely to decide whether it may resume the map.
        with self._history_lock:
            open_assaults = _native_open_assault_lifecycles(
                self._command_history
            )
            unresolved_assaults = (
                _native_unobservable_started_assaults(
                    starting, self._command_history
                )
                if starting.get("paused") is True
                else []
            )
        if open_assaults and starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "native life-advance requires a paused rich snapshot while "
                "an assault_started lifecycle remains open"
            )
        if starting.get("paused") is True:
            if unresolved_assaults:
                raise BridgeUnavailableError(
                    "native life-advance refused an unresolved assault_started "
                    "lifecycle without observable same-SiegeID rich state"
                )
        starting_date_raw = _date_raw(starting, "starting snapshot")
        horizon_days = 1 if exact_one_day else _life_advance_horizon_days(starting)
        primitive_steps = set(
            _string_list(self.state.capabilities().get("action_steps"))
        )
        timeline_speed, timeline_policy = _life_advance_timeline_policy(
            starting,
            horizon_days=horizon_days,
            exact_one_day=exact_one_day,
            exact_one_day_proof_kind=exact_one_day_proof_kind,
            exact_one_day_preferred_speed=exact_one_day_preferred_speed,
            available_action_steps=primitive_steps,
        )
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
        current = self._wait_for_life_advance_snapshot(
            self.take_internal_semantic_snapshot(),
            lambda snapshot: snapshot.get("speed") == timeline_speed,
            timeout_seconds=self.command_timeout_seconds,
        )
        if current.get("speed") != timeline_speed:
            raise BridgeUnavailableError(
                "native life-advance did not observe "
                f"speed {timeline_speed}"
            )

        current = self._resume_life_advance(current, actions)

        progress_deadline = time.monotonic() + self.life_advance_timeout_seconds
        horizon_days_override = 1 if exact_one_day else None
        native_pause_observed = current.get("paused") is True
        semantic_progress_observed = _life_advance_progressed(
            current,
            starting,
            horizon_days_override=horizon_days_override,
        )
        while not native_pause_observed and not semantic_progress_observed:
            remaining = progress_deadline - time.monotonic()
            if remaining <= 0:
                break
            current = self._wait_for_life_advance_change(
                int(current["revision"]),
                timeout_seconds=remaining,
            )
            # This observation happens before the composite submits its own
            # cleanup pause.  A paused frame here is therefore CK3's native
            # auto-pause and is a legitimate early timeline boundary.
            native_pause_observed = current.get("paused") is True
            semantic_progress_observed = _life_advance_progressed(
                current,
                starting,
                horizon_days_override=horizon_days_override,
            )

        reached_progress_postcondition = (
            native_pause_observed or semantic_progress_observed
        )
        current = self._pause_life_advance(current, actions)
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
                current = self._wait_for_life_advance_snapshot(
                    self.take_internal_semantic_snapshot(),
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
                "exact one-day advance exceeded its 24-hour native "
                f"horizon: {starting_date_raw} -> {ending_date_raw}"
            )
        materialization_result: dict[str, object] | None = None
        if identity_materialization is not None:
            subject_public_cunit_id = int(
                identity_materialization["subject_public_cunit_id"]
            )
            ending_subject = _army_by_id(current, subject_public_cunit_id)
            starting_native_revision = starting.get("native_revision")
            ending_native_revision = current.get("native_revision")
            starting_played = starting.get("played_character")
            ending_played = current.get("played_character")
            if not (
                ending_date_raw == starting_date_raw + 24
                and current.get("paused") is True
                and isinstance(current.get("revision"), int)
                and not isinstance(current.get("revision"), bool)
                and int(current["revision"]) > starting_revision
                and _positive_native_id(starting_native_revision)
                and _positive_native_id(ending_native_revision)
                and int(ending_native_revision)
                > int(starting_native_revision)
                and starting.get("episode_run_id")
                == current.get("episode_run_id")
                and starting.get("episode_character_id")
                == current.get("episode_character_id")
                and isinstance(starting_played, dict)
                and isinstance(ending_played, dict)
                and starting_played.get("character_id")
                == ending_played.get("character_id")
                and isinstance(ending_subject, dict)
                and ending_subject.get("controllable") is True
                and ending_subject.get("in_combat") is True
            ):
                raise BridgeUnavailableError(
                    "battle identity materialization did not produce one "
                    "exact next paused public-combat revision"
                )
            materialization_result = {
                "schema_version": 1,
                "status": "one_day_advanced",
                "proof_kind": "battle_identity_materialization",
                "diagnostic_reason": (
                    BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
                ),
                "subject_public_cunit_id": subject_public_cunit_id,
                "starting_snapshot_id": starting.get("snapshot_id"),
                "starting_revision": starting_revision,
                "starting_native_revision": int(starting_native_revision),
                "starting_date_raw": starting_date_raw,
                "ending_snapshot_id": current.get("snapshot_id"),
                "ending_revision": int(current["revision"]),
                "ending_native_revision": int(ending_native_revision),
                "ending_date_raw": ending_date_raw,
                "elapsed_days": 1,
                "next_revision_requirement": "full_combat_id",
            }
        result: dict[str, object] = {
            "step": result_step,
            "backend_id": "native-headless",
            "source": "native-composite",
            "starting_date": {"date_raw": starting_date_raw},
            "ending_date": {"date_raw": ending_date_raw},
            "starting_date_raw": starting_date_raw,
            "ending_date_raw": ending_date_raw,
            "elapsed_days": max(0, (ending_date_raw - starting_date_raw) // 24),
            "requested_horizon_days": horizon_days,
            "timeline_speed": timeline_speed,
            "timeline_policy": timeline_policy,
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
        if materialization_result is not None:
            result["battle_identity_materialization"] = (
                materialization_result
            )
        return result

    def _resume_life_advance(
        self,
        snapshot: dict[str, object],
        actions: list[dict[str, object]],
    ) -> dict[str, object]:
        if snapshot.get("paused") is False:
            return snapshot
        deadline = time.monotonic() + self.command_timeout_seconds
        current = self.take_internal_semantic_snapshot()
        if current.get("paused") is False:
            return current
        if not _retryable_life_advance_resume_owner(snapshot, current):
            raise BridgeUnavailableError(
                "native life-advance resume-map owner changed before submission"
            )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeUnavailableError(
                "native life-advance resume-map submission timed out"
            )
        # The exact 1.19.0.6 handler fresh-reads CK3 and treats an already
        # running map as success.  This composite owns the timeline slice, so
        # it can bypass the redundant Python revision comparison while direct
        # resume-map primitives retain their public-revision gate.
        result = self._execute_primitive_step(
            "resume-map",
            expected_revision=None,
            timeout_seconds=remaining,
            internal_semantic_snapshot=True,
        )
        actions.append({"step": "resume-map", "result": result})
        resume_attempt_count = 1
        resume_ack_statuses = [_timeline_ack_status(result)]
        remaining = max(0.0, deadline - time.monotonic())
        current = self._wait_for_life_advance_snapshot(
            self.take_internal_semantic_snapshot(),
            lambda candidate: candidate.get("paused") is False,
            timeout_seconds=min(
                remaining, _LIFE_ADVANCE_TIMELINE_RETRY_SECONDS
            ),
        )
        if current.get("paused") is False:
            return current

        retry_suppressed = None
        if not _retryable_life_advance_resume_owner(snapshot, current):
            retry_suppressed = "owner_changed"
        else:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                resume_attempt_count = 2
                try:
                    result = self._execute_primitive_step(
                        "resume-map",
                        expected_revision=None,
                        timeout_seconds=remaining,
                        internal_semantic_snapshot=True,
                    )
                except (BridgeUnavailableError, UnsupportedStepError) as error:
                    raise BridgeUnavailableError(
                        "native life-advance second resume-map request failed; "
                        f"resume_attempts={resume_attempt_count}, "
                        f"resume_ack_statuses={resume_ack_statuses}, "
                        f"second_error={type(error).__name__}: {error}"
                    ) from error
                actions.append({"step": "resume-map", "result": result})
                resume_ack_statuses.append(_timeline_ack_status(result))
                remaining = max(0.0, deadline - time.monotonic())
                current = self._wait_for_life_advance_snapshot(
                    self.take_internal_semantic_snapshot(),
                    lambda candidate: candidate.get("paused") is False,
                    timeout_seconds=remaining,
                )
        if current.get("paused") is not False:
            raise BridgeUnavailableError(
                "native life-advance did not observe the running map; "
                f"resume_attempts={resume_attempt_count}, "
                f"resume_ack_statuses={resume_ack_statuses}, "
                f"retry_suppressed={retry_suppressed}, "
                f"last_revision={current.get('revision')}, "
                f"last_native_revision={current.get('native_revision')}, "
                f"last_date_raw={current.get('date_raw')}, "
                f"last_speed={current.get('speed')}, "
                f"last_paused={current.get('paused')}, "
                "state_frame_rejections="
                f"{_state_frame_rejection_summary(current)}"
            )
        return current

    def _pause_life_advance(
        self,
        snapshot: dict[str, object],
        actions: list[dict[str, object]],
    ) -> dict[str, object]:
        if snapshot.get("paused") is True:
            return snapshot
        deadline = time.monotonic() + self.command_timeout_seconds
        current = self.take_internal_semantic_snapshot()
        if current.get("paused") is True:
            return current
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeUnavailableError(
                "native life-advance pause-map submission timed out"
            )
        # The exact 1.19.0.6 DLL pause handler does not consume the wire
        # expected_revision.  It fresh-reads CK3, returns already_paused when
        # satisfied, or queues the idempotent paused=1 command.  Requiring a
        # second Python public-revision comparison can starve forever while a
        # speed-five map publishes frames, so only this composite-owned pause
        # bypasses that redundant pre-submit comparison.  Direct primitives
        # and every other action keep their existing revision contract.
        result = self._execute_primitive_step(
            "pause-map",
            expected_revision=None,
            timeout_seconds=remaining,
            internal_semantic_snapshot=True,
        )
        actions.append({"step": "pause-map", "result": result})
        pause_attempt_count = 1
        pause_ack_statuses = [_timeline_ack_status(result)]
        remaining = max(0.0, deadline - time.monotonic())
        current = self._wait_for_life_advance_snapshot(
            self.take_internal_semantic_snapshot(),
            lambda candidate: candidate.get("paused") is True,
            timeout_seconds=min(
                remaining, _LIFE_ADVANCE_TIMELINE_RETRY_SECONDS
            ),
        )
        if current.get("paused") is True:
            return current

        retry_suppressed = None
        if not _retryable_life_advance_pause_owner(snapshot, current):
            retry_suppressed = "owner_changed"
        else:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                pause_attempt_count = 2
                try:
                    result = self._execute_primitive_step(
                        "pause-map",
                        expected_revision=None,
                        timeout_seconds=remaining,
                        internal_semantic_snapshot=True,
                    )
                except (BridgeUnavailableError, UnsupportedStepError) as error:
                    raise BridgeUnavailableError(
                        "native life-advance second pause-map request failed; "
                        f"pause_attempts={pause_attempt_count}, "
                        f"pause_ack_statuses={pause_ack_statuses}, "
                        f"second_error={type(error).__name__}: {error}"
                    ) from error
                actions.append({"step": "pause-map", "result": result})
                pause_ack_statuses.append(_timeline_ack_status(result))
                remaining = max(0.0, deadline - time.monotonic())
                current = self._wait_for_life_advance_snapshot(
                    self.take_internal_semantic_snapshot(),
                    lambda candidate: candidate.get("paused") is True,
                    timeout_seconds=remaining,
                )
        if current.get("paused") is not True:
            raise BridgeUnavailableError(
                "native life-advance did not observe the paused map; "
                f"pause_attempts={pause_attempt_count}, "
                f"pause_ack_statuses={pause_ack_statuses}, "
                f"retry_suppressed={retry_suppressed}, "
                f"last_revision={current.get('revision')}, "
                f"last_native_revision={current.get('native_revision')}, "
                f"last_date_raw={current.get('date_raw')}, "
                f"last_speed={current.get('speed')}, "
                f"last_paused={current.get('paused')}, "
                "state_frame_rejections="
                f"{_state_frame_rejection_summary(current)}"
            )
        return current

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
                internal_semantic_snapshot=True,
            )
        except BridgeUnavailableError as error:
            if "native gameplay revision mismatch" not in str(error):
                raise
            refreshed = self.take_internal_semantic_snapshot()
            if not _retryable_life_advance_change(observed_snapshot, refreshed):
                raise
            return self._execute_primitive_step(
                step,
                expected_revision=int(refreshed["revision"]),
                internal_semantic_snapshot=True,
            )

    def _wait_for_life_advance_snapshot(
        self,
        snapshot: dict[str, object],
        predicate: Callable[[dict[str, object]], bool],
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        """Wait for a semantic frame without materializing transcript evidence."""
        deadline = time.monotonic() + timeout_seconds
        current = snapshot
        while not predicate(current):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return current
            current = self._wait_for_life_advance_change(
                int(current["revision"]), timeout_seconds=remaining
            )
        return current

    def _wait_for_life_advance_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        """Private lean counterpart of wait_for_change for a timeline slice."""
        _validate_revision(after_revision, "after_revision")
        timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
        if not self.state.capabilities()["snapshot"]:
            return self.take_internal_semantic_snapshot()
        self.state.wait_for_public_change(after_revision, timeout)
        return self.take_internal_semantic_snapshot()

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
        while True:
            with self._driver_state_lock:
                flush_driver_state = bool(
                    self.state_dir is not None
                    and self._session_bridge_pid is not None
                    and self._driver_state_dirty
                )
            if not flush_driver_state:
                break
            self._persist_driver_state()
            with self._driver_state_lock:
                if self._driver_state_error is not None:
                    break
        self.endpoint.close()

    def _transport_error(self) -> str | None:
        getter = getattr(self.endpoint, "transport_error", None)
        if not callable(getter):
            return None
        value = getter()
        return value if isinstance(value, str) and value else None


def _is_deferred_read_only_history_step(step: object) -> bool:
    """Return commands whose successful result may wait for a durable barrier."""
    return bool(
        isinstance(step, str)
        and (
            step.startswith("query-")
            or parse_preview_move_army_step(step) is not None
            or parse_preview_active_combat_retreat_v1_step(step) is not None
        )
    )


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
        native_capabilities = self.native.capabilities()
        native_steps = set(_string_list(native_capabilities.get("action_steps")))
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
        native_bridge_capabilities = set(
            _string_list(native_capabilities.get("bridge_capabilities"))
        )
        bridge_capabilities = set(
            _string_list(base.get("bridge_capabilities"))
        )
        for pure_native_capability in (
            QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
            QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
            QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
            ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY,
            ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY,
        ):
            if pure_native_capability not in native_bridge_capabilities:
                bridge_capabilities.discard(pure_native_capability)
        return {
            **base,
            "action_steps": sorted(action_steps),
            "bridge_capabilities": sorted(bridge_capabilities),
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

    def activate_zhongguo_scoreboard_v1(
        self,
        request: ZhongguoScoreboardActionRequestV1,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Route the exact action transport to native only.

        Hybrid public revisions are not the named-pipe public revision.  The
        adapter can rebind an unavailable result safely. ACK rebinding remains
        fail-closed in this hybrid path until it has its own live evidence.
        """

        if not isinstance(request, ZhongguoScoreboardActionRequestV1):
            raise ValueError("request must be a scoreboard action v1 request")
        _validate_revision(expected_revision, "expected_revision")
        starting = self.take_snapshot()
        if (
            starting.get("paused") is not True
            or starting.get("revision") != expected_revision
            or request.expected_revision != expected_revision
        ):
            raise PreSubmissionRevisionMismatchError(
                "hybrid ZhongGuo scoreboard action source binding is stale"
            )
        diagnostics = starting.get("diagnostics")
        played_character = starting.get("played_character")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if not (
            starting.get("native_revision")
            == request.expected_native_revision
            and connection_generation
            == request.expected_connection_generation
            and player_character_id == request.expected_player_character_id
        ):
            raise PreSubmissionRevisionMismatchError(
                "hybrid ZhongGuo scoreboard native binding is stale"
            )
        backend_revisions = starting.get("backend_revisions")
        native_public_revision = (
            backend_revisions.get("fast")
            if isinstance(backend_revisions, dict)
            else None
        )
        if (
            isinstance(native_public_revision, bool)
            or not isinstance(native_public_revision, int)
            or native_public_revision < 0
        ):
            raise BridgeUnavailableError(
                "hybrid ZhongGuo scoreboard action lacks a native public "
                "revision"
            )
        native_request = ZhongguoScoreboardActionRequestV1(
            request_nonce=request.request_nonce,
            action=request.action,
            expected_revision=native_public_revision,
            expected_native_revision=request.expected_native_revision,
            expected_connection_generation=(
                request.expected_connection_generation
            ),
            expected_player_character_id=request.expected_player_character_id,
            expected_provider_session_id=request.expected_provider_session_id,
            expected_observation_sequence=(
                request.expected_observation_sequence
            ),
            expected_observed_state_revision=(
                request.expected_observed_state_revision
            ),
            expected_tree_fingerprint_v1=(
                request.expected_tree_fingerprint_v1
            ),
            expected_semantic_fingerprint_v1=(
                request.expected_semantic_fingerprint_v1
            ),
            expected_window_instance_pointer=(
                request.expected_window_instance_pointer
            ),
            expected_target_instance_pointer=(
                request.expected_target_instance_pointer
            ),
            expected_target_vtable_pointer=(
                request.expected_target_vtable_pointer
            ),
        )
        result = self.native.activate_zhongguo_scoreboard_v1(
            native_request, expected_revision=native_public_revision
        )
        if result.get("accepted") is True:
            raise BridgeUnavailableError(
                "hybrid scoreboard ACK is disabled until its dedicated "
                "public/native binding is proven"
            )
        ending = self.take_snapshot()
        if not (
            ending.get("paused") is True
            and ending.get("snapshot_id") == starting.get("snapshot_id")
            and ending.get("revision") == starting.get("revision")
            and ending.get("native_revision")
            == starting.get("native_revision")
            and ending.get("date_raw") == starting.get("date_raw")
            and ending.get("played_character")
            == starting.get("played_character")
        ):
            raise BridgeUnavailableError(
                "hybrid ZhongGuo scoreboard action crossed its paused binding"
            )
        return {
            **result,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
            "queried_connection_generation": connection_generation,
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            **self._delegate.take_snapshot(),
            "backend_id": "hybrid-fallback",
        }

    def center_map_on_landed_title_v1(
        self,
        title_key: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Keep explicit title navigation on the native backend only."""
        key = validate_landed_title_key(title_key)
        _validate_revision(expected_revision, "expected_revision")
        native_bridge_capabilities = set(
            _string_list(
                self.native.capabilities().get("bridge_capabilities")
            )
        )
        if (
            CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
            not in native_bridge_capabilities
        ):
            raise UnsupportedStepError(
                "capability_not_available: title-map navigation is pure "
                "native and will not use fallback"
            )
        starting = self.take_snapshot()
        if starting.get("paused") is not True:
            raise BridgeUnavailableError(
                "hybrid title-map navigation requires a paused snapshot"
            )
        if starting.get("map_ready") is not True:
            raise BridgeUnavailableError(
                "hybrid title-map navigation requires a map-ready snapshot"
            )
        try:
            binding = _title_map_navigation_binding_from_snapshot(starting)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"hybrid title-map navigation lacks a binding: {error}"
            ) from error
        if binding["revision"] != expected_revision:
            raise BridgeUnavailableError(
                "hybrid title-map navigation revision mismatch: expected "
                f"{expected_revision}, current {binding['revision']}"
            )
        backend_revisions = starting.get("backend_revisions")
        native_revision = (
            backend_revisions.get("fast")
            if isinstance(backend_revisions, dict)
            else None
        )
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or native_revision < 0
        ):
            raise BridgeUnavailableError(
                "hybrid title-map navigation lacks the native public revision"
            )
        result = self.native.center_map_on_landed_title_v1(
            key,
            expected_revision=native_revision,
        )
        ending = self.take_snapshot()
        try:
            ending_binding = _title_map_navigation_binding_from_snapshot(
                ending
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"hybrid title-map navigation lost its binding: {error}"
            ) from error
        if not (
            ending.get("paused") is True
            and ending.get("map_ready") is True
            and ending_binding == binding
            and ending.get("played_character")
            == starting.get("played_character")
        ):
            raise BridgeUnavailableError(
                "hybrid title-map navigation crossed its paused session binding"
            )
        try:
            return normalize_title_map_navigation_v1_result(
                {**result, "binding": binding},
                expected_title_key=key,
                expected_binding=binding,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"hybrid title-map projection is malformed: {error}"
            ) from error

    def query_pending_character_interaction_context_v1(
        self,
        pending_interaction_id: int,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        """Keep the typed parameterized pending query on the native backend."""
        pending_interaction_id = normalize_pending_interaction_id(
            pending_interaction_id
        )
        native_bridge_capabilities = set(
            _string_list(
                self.native.capabilities().get("bridge_capabilities")
            )
        )
        if (
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
            not in native_bridge_capabilities
        ):
            raise UnsupportedStepError(
                "pending-interaction queries are pure native and will not use "
                "fallback"
            )
        starting = self.take_snapshot()
        if expected_revision is not None:
            _validate_revision(expected_revision, "expected_revision")
            if expected_revision != starting.get("revision"):
                raise BridgeUnavailableError(
                    "hybrid gameplay revision mismatch: expected "
                    f"{expected_revision}, current {starting.get('revision')}"
                )
        pending = starting.get("pending_character_interaction")
        if (
            not isinstance(pending, dict)
            or pending.get("instance_id") != pending_interaction_id
        ):
            raise BridgeUnavailableError(
                "pending interaction ID does not match the hybrid snapshot"
            )
        native_revision = None
        backend_revisions = starting.get("backend_revisions")
        if isinstance(backend_revisions, dict) and isinstance(
            backend_revisions.get("fast"), int
        ):
            native_revision = int(backend_revisions["fast"])
        result = self.native.query_pending_character_interaction_context_v1(
            pending_interaction_id,
            expected_revision=native_revision,
        )
        ending = self.take_snapshot()
        if (
            ending.get("snapshot_id") != starting.get("snapshot_id")
            or ending.get("revision") != starting.get("revision")
            or ending.get("native_revision") != starting.get("native_revision")
            or ending.get("date_raw") != starting.get("date_raw")
            or ending.get("pending_character_interaction") != pending
        ):
            raise BridgeUnavailableError(
                "hybrid pending-interaction query crossed a snapshot revision"
            )
        return {
            **result,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        zhongguo_case_query = parse_query_zhongguo_case_snapshot_v1_step(
            step
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_case_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo case snapshot v1 query step"
            )
        zhongguo_ai_owned_case_query = (
            parse_query_zhongguo_ai_owned_case_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_ai_owned_case_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo AI-owned case snapshot v1 query step"
            )
        zhongguo_result_case_query = (
            parse_query_zhongguo_result_case_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_result_case_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo result-case snapshot v1 query step"
            )
        zhongguo_b2_pip_query = (
            parse_query_zhongguo_b2_pip_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_b2_pip_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo B2 PIP snapshot v1 query step"
            )
        zhongguo_workforce_collective_query = (
            parse_query_zhongguo_workforce_collective_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_workforce_collective_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo Workforce collective snapshot v1 query "
                "step"
            )
        zhongguo_workforce_normal_exit_query = (
            parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_workforce_normal_exit_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo Workforce normal-exit snapshot v1 "
                "query step"
            )
        zhongguo_incident_query = (
            parse_query_zhongguo_incident_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_incident_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo incident snapshot v1 query step"
            )
        zhongguo_manager_governance_query = (
            parse_query_zhongguo_manager_governance_snapshot_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX
            )
            and zhongguo_manager_governance_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo manager-governance snapshot v1 query "
                "step"
            )
        zhongguo_scoreboard_query = (
            parse_query_zhongguo_scoreboard_state_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX
            )
            and zhongguo_scoreboard_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo scoreboard state v1 query step"
            )
        if zhongguo_case_query is not None:
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "ZhongGuo case queries are pure native and will not use "
                    "fallback"
                )
            starting = self.take_snapshot()
            if expected_revision is not None:
                _validate_revision(expected_revision, "expected_revision")
                if expected_revision != starting.get("revision"):
                    raise BridgeUnavailableError(
                        "hybrid gameplay revision mismatch: expected "
                        f"{expected_revision}, current "
                        f"{starting.get('revision')}"
                    )
            starting_diagnostics = starting.get("diagnostics")
            connection_generation = (
                starting_diagnostics.get("connection_generation")
                if isinstance(starting_diagnostics, dict)
                else None
            )
            if (
                isinstance(connection_generation, bool)
                or not isinstance(connection_generation, int)
                or not 1 <= connection_generation <= 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "hybrid ZhongGuo case query lacks a connection generation"
                )
            native_public_revision = None
            backend_revisions = starting.get("backend_revisions")
            if isinstance(backend_revisions, dict) and isinstance(
                backend_revisions.get("fast"), int
            ):
                native_public_revision = int(backend_revisions["fast"])
            result = self.native.execute_step(
                step,
                expected_revision=native_public_revision,
            )
            if (
                result.get("queried_connection_generation")
                != connection_generation
            ):
                raise BridgeUnavailableError(
                    "hybrid ZhongGuo case result crossed a connection"
                )
            ending = self.take_snapshot()
            ending_diagnostics = ending.get("diagnostics")
            if not (
                ending.get("paused") is True
                and ending.get("snapshot_id") == starting.get("snapshot_id")
                and ending.get("revision") == starting.get("revision")
                and ending.get("native_revision")
                == starting.get("native_revision")
                and ending.get("date_raw") == starting.get("date_raw")
                and ending.get("played_character")
                == starting.get("played_character")
                and isinstance(ending_diagnostics, dict)
                and ending_diagnostics.get("connection_generation")
                == connection_generation
            ):
                raise BridgeUnavailableError(
                    "hybrid ZhongGuo case query crossed a snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
                "queried_connection_generation": connection_generation,
            }
        zhongguo_promotion_compensation_query = (
            parse_query_zhongguo_promotion_compensation_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX
            )
            and zhongguo_promotion_compensation_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo promotion/compensation v1 query step"
            )
        zhongguo_projects_metrics_query = (
            parse_query_zhongguo_projects_metrics_v1_step(step)
        )
        if (
            isinstance(step, str)
            and step.startswith(QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX)
            and zhongguo_projects_metrics_query is None
        ):
            raise UnsupportedStepError(
                "malformed ZhongGuo projects/metrics v1 query step"
            )
        if (
            zhongguo_ai_owned_case_query is not None
            or zhongguo_result_case_query is not None
            or zhongguo_b2_pip_query is not None
            or zhongguo_promotion_compensation_query is not None
            or zhongguo_projects_metrics_query is not None
            or zhongguo_workforce_collective_query is not None
            or zhongguo_workforce_normal_exit_query is not None
            or zhongguo_incident_query is not None
            or zhongguo_manager_governance_query is not None
            or zhongguo_scoreboard_query is not None
        ):
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            required_capability = (
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
                if zhongguo_ai_owned_case_query is not None
                else (
                    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
                    if zhongguo_workforce_normal_exit_query is not None
                    else (
                        QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
                        if zhongguo_workforce_collective_query is not None
                        else (
                            QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY
                            if zhongguo_scoreboard_query is not None
                            else (
                                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
                                if zhongguo_manager_governance_query is not None
                                else (
                                    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY
                                    if zhongguo_incident_query is not None
                                    else (
                                    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
                                        if zhongguo_projects_metrics_query is not None
                                        else (
                                            QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
                                            if zhongguo_promotion_compensation_query is not None
                                            else (
                                                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY
                                                if zhongguo_b2_pip_query is not None
                                                else (
                                                    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            if (
                required_capability not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "ZhongGuo received-self case queries are pure native "
                    "and will not use fallback"
                )
            starting = self.take_snapshot()
            if expected_revision is not None:
                _validate_revision(expected_revision, "expected_revision")
                if expected_revision != starting.get("revision"):
                    raise BridgeUnavailableError(
                        "hybrid gameplay revision mismatch: expected "
                        f"{expected_revision}, current "
                        f"{starting.get('revision')}"
                    )
            starting_diagnostics = starting.get("diagnostics")
            connection_generation = (
                starting_diagnostics.get("connection_generation")
                if isinstance(starting_diagnostics, dict)
                else None
            )
            if (
                isinstance(connection_generation, bool)
                or not isinstance(connection_generation, int)
                or not 1 <= connection_generation <= 2**64 - 1
            ):
                raise BridgeUnavailableError(
                    "hybrid ZhongGuo result-case query lacks a connection "
                    "generation"
                )
            native_public_revision = None
            backend_revisions = starting.get("backend_revisions")
            if isinstance(backend_revisions, dict) and isinstance(
                backend_revisions.get("fast"), int
            ):
                native_public_revision = int(backend_revisions["fast"])
            result = self.native.execute_step(
                step,
                expected_revision=native_public_revision,
            )
            if (
                result.get("queried_connection_generation")
                != connection_generation
            ):
                raise BridgeUnavailableError(
                    "hybrid ZhongGuo result-case result crossed a connection"
                )
            ending = self.take_snapshot()
            ending_diagnostics = ending.get("diagnostics")
            if not (
                ending.get("paused") is True
                and ending.get("snapshot_id") == starting.get("snapshot_id")
                and ending.get("revision") == starting.get("revision")
                and ending.get("native_revision")
                == starting.get("native_revision")
                and ending.get("date_raw") == starting.get("date_raw")
                and ending.get("played_character")
                == starting.get("played_character")
                and isinstance(ending_diagnostics, dict)
                and ending_diagnostics.get("connection_generation")
                == connection_generation
            ):
                raise BridgeUnavailableError(
                    "hybrid ZhongGuo result-case query crossed a snapshot "
                    "revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
                "queried_connection_generation": connection_generation,
            }
        if step == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP:
            pending = self.take_snapshot().get(
                "pending_character_interaction"
            )
            pending_id = (
                pending.get("instance_id")
                if isinstance(pending, dict)
                else None
            )
            try:
                pending_id = normalize_pending_interaction_id(pending_id)
            except ValueError as error:
                raise BridgeUnavailableError(
                    "CK3 has no valid signed full pending interaction ID"
                ) from error
            return self.query_pending_character_interaction_context_v1(
                pending_id,
                expected_revision=expected_revision,
            )
        if step == QUERY_LOADED_FEATURE_MANIFEST_V1_STEP:
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "loaded-feature queries are pure native and will not use "
                    "fallback"
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
                or ending.get("date_raw") != starting.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "hybrid loaded-feature query crossed a snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
        if step == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP:
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "campaign-root queries are pure native and will not use "
                    "fallback"
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
                or ending.get("date_raw") != starting.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "hybrid campaign-root query crossed a snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
        if isinstance(step, str) and step.startswith(
            QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX
        ):
            if parse_query_battle_terminal_transition_v1_step(step) is None:
                raise UnsupportedStepError(
                    "malformed battle-terminal transition v1 step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "battle-terminal transition queries are pure native and "
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
                or ending.get("date_raw") != starting.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "hybrid battle-terminal transition query crossed a "
                    "snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
        if isinstance(step, str) and step.startswith(
            QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX
        ):
            if (
                parse_query_battle_reinforcement_assignment_v1_step(step)
                is None
            ):
                raise UnsupportedStepError(
                    "malformed battle-reinforcement assignment v1 step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "battle-reinforcement queries are pure native and will "
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
                or ending.get("date_raw") != starting.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "hybrid battle-reinforcement query crossed a snapshot "
                    "revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
        if isinstance(step, str) and step.startswith(
            QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX
        ):
            if parse_query_battle_transition_v1_step(step) is None:
                raise UnsupportedStepError(
                    "malformed battle-transition v1 step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_BATTLE_TRANSITION_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "battle-transition queries are pure native and will not "
                    "use fallback"
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
                or ending.get("date_raw") != starting.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "hybrid battle-transition query crossed a snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
        if isinstance(step, str) and step.startswith(
            QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX
        ):
            if parse_query_battle_control_snapshot_v1_step(step) is None:
                raise UnsupportedStepError(
                    "malformed battle-control snapshot v1 step"
                )
            native_bridge_capabilities = set(
                _string_list(
                    self.native.capabilities().get("bridge_capabilities")
                )
            )
            if (
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
                not in native_bridge_capabilities
            ):
                raise UnsupportedStepError(
                    "battle-control snapshot queries are pure native and "
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
                or ending.get("date_raw") != starting.get("date_raw")
            ):
                raise BridgeUnavailableError(
                    "hybrid battle-control query crossed a snapshot revision"
                )
            return {
                **result,
                "queried_snapshot_id": starting.get("snapshot_id"),
                "queried_revision": starting.get("revision"),
                "queried_native_revision": starting.get("native_revision"),
            }
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


def _battle_sentinel_watch_army_ids(
    snapshot: object,
) -> tuple[int, ...] | None:
    """Return the complete stable controllable public-CUnit watch set."""
    if not isinstance(snapshot, dict):
        return None
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return None
    army_ids: set[int] = set()
    for army in armies:
        if not isinstance(army, dict):
            return None
        if army.get("controllable") is not True:
            continue
        army_id = army.get("army_id")
        if (
            isinstance(army_id, bool)
            or not isinstance(army_id, int)
            or not 0 < army_id <= 2**31 - 1
            or army_id in army_ids
        ):
            return None
        army_ids.add(army_id)
    if not 0 < len(army_ids) <= _BATTLE_SENTINEL_MAXIMUM_ARMIES:
        return None
    return tuple(sorted(army_ids))


def _battle_sentinel_has_active_combat(
    snapshot: object, watch_army_ids: tuple[int, ...]
) -> bool:
    """Return whether the complete watched set contains active combat."""
    if not isinstance(snapshot, dict):
        return False
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return False
    watched = set(watch_army_ids)
    for army in armies:
        if not isinstance(army, dict) or army.get("controllable") is not True:
            continue
        if army.get("army_id") not in watched:
            continue
        named_state = army.get("army_state")
        state_code = army.get("army_state_code")
        combat_id = army.get("combat_id")
        if (
            (
                isinstance(named_state, str)
                and named_state.casefold() == "combat"
            )
            or state_code == 2
            or army.get("in_combat") is True
            or (
                isinstance(combat_id, int)
                and not isinstance(combat_id, bool)
                and combat_id != -1
            )
        ):
            return True
    return False


def _battle_sentinel_matches_committed_route(
    snapshot: object,
    watch_army_ids: tuple[int, ...],
    *,
    subject_army_id: int,
    target_province_id: int,
) -> bool:
    """Match the typed subject/target against that subject's exact route."""
    if not isinstance(snapshot, dict):
        return False
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return False
    watched = set(watch_army_ids)
    matches = 0
    for army in armies:
        if not isinstance(army, dict) or army.get("controllable") is not True:
            continue
        if army.get("army_id") not in watched:
            continue
        if army.get("army_id") != subject_army_id:
            continue
        matches += 1
        target = army.get("move_target_province_id")
        route = army.get("route_province_ids")
        named_state = army.get("army_state")
        state_code = army.get("army_state_code")
        if (
            isinstance(target, int)
            and not isinstance(target, bool)
            and target == target_province_id
            and isinstance(route, list)
            and bool(route)
            and all(
                isinstance(province_id, int)
                and not isinstance(province_id, bool)
                and province_id > 0
                for province_id in route
            )
            and route[-1] == target
            and (
                (
                    isinstance(named_state, str)
                    and named_state.casefold() in {"moving", "embarked"}
                )
                or state_code in {4, 7}
            )
        ):
            continue
        return False
    return matches == 1


def _battle_sentinel_player_decision_boundary(
    snapshot: object,
) -> dict[str, object] | None:
    if not isinstance(snapshot, dict):
        return None
    binding = _battle_sentinel_frame_binding(snapshot)
    active_event = snapshot.get("active_event")
    if isinstance(active_event, dict):
        return {
            **binding,
            "kind": "active_event",
            "instance_id": active_event.get("instance_id"),
            "option_count": active_event.get("option_count"),
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
        }
    pending = snapshot.get("pending_character_interaction")
    if isinstance(pending, dict):
        return {
            **binding,
            "kind": "pending_character_interaction",
            "instance_id": pending.get("instance_id"),
            "sender_character_id": pending.get("sender_character_id"),
            "auto_accept_notification": pending.get(
                "auto_accept_notification"
            ),
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
        }
    played_character = snapshot.get("played_character")
    played_character_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    played_character_alive = (
        played_character.get("alive")
        if isinstance(played_character, dict)
        else None
    )
    episode_character_id = snapshot.get("episode_character_id")
    terminal_reason = snapshot.get("one_life_terminal_reason")
    inferred_terminal = bool(
        isinstance(episode_character_id, int)
        and not isinstance(episode_character_id, bool)
        and episode_character_id > 0
        and (
            played_character_alive is False
            or (
                isinstance(played_character_id, int)
                and not isinstance(played_character_id, bool)
                and played_character_id > 0
                and played_character_id != episode_character_id
            )
        )
    )
    if isinstance(terminal_reason, str) or inferred_terminal:
        return {
            **binding,
            "kind": "one_life_terminal",
            "instance_id": None,
            "terminal_reason": (
                terminal_reason
                if isinstance(terminal_reason, str)
                else "played_character_dead"
                if played_character_alive is False
                else "played_character_changed"
            ),
            "played_character_alive": played_character_alive,
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
        }
    return None


def _battle_sentinel_active_war_ids(
    snapshot: object,
) -> tuple[int, ...] | None:
    """Return the complete, normalized active WarID set for one frame."""

    if not isinstance(snapshot, dict):
        return None
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    war_ids: list[int] = []
    for war in wars:
        war_id = war.get("war_id") if isinstance(war, dict) else None
        if (
            isinstance(war_id, bool)
            or not isinstance(war_id, int)
            or not 0 < war_id <= 2**31 - 1
            or war_id in war_ids
        ):
            return None
        war_ids.append(war_id)
    return tuple(sorted(war_ids))


def _battle_sentinel_active_war_set_instance_id(
    before_war_ids: tuple[int, ...],
    after_war_ids: tuple[int, ...],
) -> str:
    before = ",".join(str(war_id) for war_id in before_war_ids) or "-"
    after = ",".join(str(war_id) for war_id in after_war_ids) or "-"
    return f"active-wars:{before}->{after}"


def _battle_sentinel_active_war_set_boundary(
    starting: object,
    current: object,
) -> dict[str, object] | None:
    """Describe a fresh paused-frame active-war-set replan boundary.

    This is deliberately a Python snapshot delta, not an exact native watch.
    It only consumes a boundary after CK3 has already paused and keeps every
    bridge/episode/player owner pin stable across a whole-day revision step.
    """

    if not isinstance(starting, dict) or not isinstance(current, dict):
        return None
    before_war_ids = _battle_sentinel_active_war_ids(starting)
    after_war_ids = _battle_sentinel_active_war_ids(current)
    if (
        before_war_ids is None
        or after_war_ids is None
        or before_war_ids == after_war_ids
        or current.get("paused") is not True
        or current.get("map_ready") is not True
    ):
        return None
    starting_revision = starting.get("revision")
    current_revision = current.get("revision")
    starting_date_raw = starting.get("date_raw")
    current_date_raw = current.get("date_raw")
    if not (
        isinstance(starting_revision, int)
        and not isinstance(starting_revision, bool)
        and isinstance(current_revision, int)
        and not isinstance(current_revision, bool)
        and current_revision > starting_revision
        and isinstance(starting_date_raw, int)
        and not isinstance(starting_date_raw, bool)
        and isinstance(current_date_raw, int)
        and not isinstance(current_date_raw, bool)
        and current_date_raw >= starting_date_raw
        and (current_date_raw - starting_date_raw) % 24 == 0
    ):
        return None
    starting_binding = _battle_sentinel_frame_binding(starting)
    current_binding = _battle_sentinel_frame_binding(current)
    owner_fields = (
        "bridge_pid",
        "connection_generation",
        "episode_character_id",
        "episode_run_id",
        "played_character_id",
    )
    if not all(
        starting_binding.get(field) == current_binding.get(field)
        for field in owner_fields
    ):
        return None
    before_set = set(before_war_ids)
    after_set = set(after_war_ids)
    return {
        **current_binding,
        "kind": "active_war_set_changed",
        "instance_id": _battle_sentinel_active_war_set_instance_id(
            before_war_ids, after_war_ids
        ),
        "before_war_ids": list(before_war_ids),
        "after_war_ids": list(after_war_ids),
        "added_war_ids": sorted(after_set - before_set),
        "removed_war_ids": sorted(before_set - after_set),
        "snapshot_id": current.get("snapshot_id"),
        "revision": current_revision,
        "native_revision": current.get("native_revision"),
    }


def _battle_sentinel_active_war_set_boundary_identity_valid(
    boundary: object,
) -> bool:
    if not isinstance(boundary, dict):
        return False
    rows: dict[str, tuple[int, ...]] = {}
    for key in (
        "before_war_ids",
        "after_war_ids",
        "added_war_ids",
        "removed_war_ids",
    ):
        value = boundary.get(key)
        if not isinstance(value, list):
            return False
        normalized: list[int] = []
        for war_id in value:
            if (
                isinstance(war_id, bool)
                or not isinstance(war_id, int)
                or not 0 < war_id <= 2**31 - 1
                or war_id in normalized
            ):
                return False
            normalized.append(war_id)
        if normalized != sorted(normalized):
            return False
        rows[key] = tuple(normalized)
    before = rows["before_war_ids"]
    after = rows["after_war_ids"]
    if before == after:
        return False
    before_set = set(before)
    after_set = set(after)
    return bool(
        boundary.get("kind") == "active_war_set_changed"
        and boundary.get("instance_id")
        == _battle_sentinel_active_war_set_instance_id(before, after)
        and rows["added_war_ids"] == tuple(sorted(after_set - before_set))
        and rows["removed_war_ids"]
        == tuple(sorted(before_set - after_set))
        and (rows["added_war_ids"] or rows["removed_war_ids"])
    )


def _battle_sentinel_frame_binding(
    snapshot: dict[str, object],
) -> dict[str, object]:
    diagnostics = snapshot.get("diagnostics")
    played_character = snapshot.get("played_character")
    return {
        "observed_date_raw": snapshot.get("date_raw"),
        "bridge_pid": (
            diagnostics.get("bridge_pid")
            if isinstance(diagnostics, dict)
            else None
        ),
        "connection_generation": (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        ),
        "episode_character_id": snapshot.get("episode_character_id"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "played_character_id": (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        ),
    }


def _same_battle_sentinel_player_decision_boundary(
    before: object,
    after: object,
) -> bool:
    terminal_boundary = bool(
        isinstance(before, dict)
        and isinstance(after, dict)
        and before.get("kind") == "one_life_terminal"
        and after.get("kind") == "one_life_terminal"
    )
    binding_fields = (
        "observed_date_raw",
        "bridge_pid",
        "connection_generation",
        "episode_character_id",
        "episode_run_id",
        "played_character_id",
    )
    if terminal_boundary:
        # A one-life terminal is monotonic for the bound episode.  CK3 may
        # advance one or more daily ticks and finish switching from the dead
        # character to the heir between observing the terminal on a running
        # frame and servicing the explicit pause request.  Keep every
        # episode/connection owner pin, but do not mistake that bounded date
        # and played-character surface evolution for a different terminal
        # boundary.
        binding_fields = tuple(
            field
            for field in binding_fields
            if field not in {"observed_date_raw", "played_character_id"}
        )
    same_kind_identity = bool(
        isinstance(before, dict)
        and isinstance(after, dict)
        and (
            (
                before.get("kind") == "one_life_terminal"
                and after.get("kind") == "one_life_terminal"
                and isinstance(before.get("terminal_reason"), str)
                and isinstance(after.get("terminal_reason"), str)
            )
            or (
                before.get("kind") != "one_life_terminal"
                and before.get("kind") == after.get("kind")
                and before.get("instance_id")
                == after.get("instance_id")
            )
        )
    )
    return bool(
        isinstance(before, dict)
        and isinstance(after, dict)
        and same_kind_identity
        and all(before.get(field) == after.get(field) for field in binding_fields)
    )


def _battle_sentinel_player_decision_is_new(
    starting: dict[str, object],
    current: dict[str, object],
) -> bool:
    starting_boundary = _battle_sentinel_player_decision_boundary(starting)
    current_boundary = _battle_sentinel_player_decision_boundary(current)
    starting_revision = starting.get("revision")
    current_revision = current.get("revision")
    starting_binding = _battle_sentinel_frame_binding(starting)
    current_binding = _battle_sentinel_frame_binding(current)
    owner_fields = (
        "bridge_pid",
        "connection_generation",
        "episode_character_id",
        "episode_run_id",
    )
    if not (
        isinstance(current_boundary, dict)
        and current_boundary.get("kind") == "one_life_terminal"
    ):
        owner_fields += ("played_character_id",)
    return bool(
        current_boundary is not None
        and (
            starting_boundary is None
            or not _same_battle_sentinel_player_decision_boundary(
                starting_boundary, current_boundary
            )
        )
        and isinstance(starting_revision, int)
        and not isinstance(starting_revision, bool)
        and isinstance(current_revision, int)
        and not isinstance(current_revision, bool)
        and current_revision > starting_revision
        and all(
            starting_binding.get(field) == current_binding.get(field)
            for field in owner_fields
        )
    )


def _fresh_battle_sentinel_player_decision_boundary(
    before_pause: dict[str, object],
    after_pause: dict[str, object],
    *,
    expected_boundary: dict[str, object] | None,
) -> bool:
    before_revision = before_pause.get("revision")
    after_revision = after_pause.get("revision")
    before_native_revision = before_pause.get("native_revision")
    after_native_revision = after_pause.get("native_revision")
    boundary = _battle_sentinel_player_decision_boundary(after_pause)
    terminal_boundary = bool(
        isinstance(boundary, dict)
        and boundary.get("kind") == "one_life_terminal"
        and isinstance(expected_boundary, dict)
        and expected_boundary.get("kind") == "one_life_terminal"
    )
    before_binding = _battle_sentinel_frame_binding(before_pause)
    after_binding = _battle_sentinel_frame_binding(after_pause)
    stable_binding_fields = (
        "bridge_pid",
        "connection_generation",
        "episode_character_id",
        "episode_run_id",
        "played_character_id",
    )
    if terminal_boundary:
        stable_binding_fields = tuple(
            field
            for field in stable_binding_fields
            if field != "played_character_id"
        )
    before_date_raw = before_binding.get("observed_date_raw")
    after_date_raw = after_binding.get("observed_date_raw")
    return bool(
        after_pause.get("paused") is True
        and after_pause.get("map_ready") is True
        and isinstance(before_revision, int)
        and not isinstance(before_revision, bool)
        and isinstance(after_revision, int)
        and not isinstance(after_revision, bool)
        and after_revision > before_revision
        and isinstance(before_native_revision, int)
        and not isinstance(before_native_revision, bool)
        and isinstance(after_native_revision, int)
        and not isinstance(after_native_revision, bool)
        and after_native_revision >= before_native_revision
        and (
            before_binding == after_binding
            or (
                terminal_boundary
                and isinstance(before_date_raw, int)
                and not isinstance(before_date_raw, bool)
                and isinstance(after_date_raw, int)
                and not isinstance(after_date_raw, bool)
                and after_date_raw >= before_date_raw
                and all(
                    before_binding.get(field) == after_binding.get(field)
                    for field in stable_binding_fields
                )
            )
        )
        and boundary is not None
        and (
            expected_boundary is None
            or _same_battle_sentinel_player_decision_boundary(
                expected_boundary, boundary
            )
        )
    )


def _battle_sentinel_stationary_objective_hold_state(
    snapshot: object,
    watch_army_ids: tuple[int, ...],
    *,
    war_id: int,
    subject_army_id: int,
    objective_province_id: int,
) -> dict[str, object]:
    """Observe one explicitly bound stationary objective-hold scope.

    Only the CUnit fields in ``watch_army_ids`` are exact native sentinel
    triggers.  War/objective/siege facts are deliberately re-read here at arm
    and after stop; they are not presented as same-day native watches.
    """
    result: dict[str, object] = {
        "status": "unavailable",
        "reason": "snapshot_unavailable",
        "sentinel_scope": "stationary_objective_hold",
        "war_id": war_id,
        "subject_army_id": subject_army_id,
        "objective_province_id": objective_province_id,
        "watch_army_ids": list(watch_army_ids),
        "paused_map_ready": False,
        "player_decision_clear": False,
        "complete_controllable_watch": False,
        "all_player_armies_regular_idle_stationary": False,
        "player_active_siege": None,
        "player_active_assault": None,
        "war_active": False,
        "objective_in_war": False,
        "subject_controllable": False,
        "subject_current_province_id": None,
        "subject_at_objective": False,
        "exact_war_terminal_watch": False,
        "exact_active_war_set_watch": False,
    }
    if not isinstance(snapshot, dict):
        return result
    result["paused_map_ready"] = bool(
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
    )
    result["player_decision_clear"] = bool(
        _battle_sentinel_player_decision_boundary(snapshot) is None
    )
    armies = snapshot.get("player_armies")
    wars = snapshot.get("active_wars")
    if not isinstance(armies, list) or not isinstance(wars, list):
        result["reason"] = "army_or_war_scope_unavailable"
        return result

    army_by_id: dict[int, dict[str, object]] = {}
    controllable_ids: list[int] = []
    all_stationary = bool(armies)
    for army in armies:
        if not isinstance(army, dict):
            result["reason"] = "player_army_row_malformed"
            return result
        army_id = army.get("army_id")
        if (
            isinstance(army_id, bool)
            or not isinstance(army_id, int)
            or not 0 < army_id <= 2**31 - 1
            or army_id in army_by_id
        ):
            result["reason"] = "player_army_identity_unavailable"
            return result
        army_by_id[army_id] = army
        if army.get("controllable") is True:
            controllable_ids.append(army_id)
        named_state = army.get("army_state")
        state_code = army.get("army_state_code")
        regular = bool(
            (
                isinstance(named_state, str)
                and named_state.casefold() == "regular"
            )
            or (named_state is None and state_code == 1)
        )
        route = army.get("route_province_ids")
        current_province = army.get("current_province_id")
        all_stationary = bool(
            all_stationary
            and regular
            and army.get("move_target_province_id") is None
            and isinstance(route, list)
            and not route
            and isinstance(current_province, int)
            and not isinstance(current_province, bool)
            and current_province > 0
            and army.get("in_combat") is not True
            and army.get("retreating") is not True
        )
    result["complete_controllable_watch"] = bool(
        tuple(sorted(controllable_ids)) == watch_army_ids
        and len(controllable_ids) == len(set(controllable_ids))
    )
    result["all_player_armies_regular_idle_stationary"] = all_stationary

    subject = army_by_id.get(subject_army_id)
    if isinstance(subject, dict):
        result["subject_controllable"] = bool(
            subject.get("controllable") is True
            and subject_army_id in watch_army_ids
        )
        subject_province = subject.get("current_province_id")
        result["subject_current_province_id"] = subject_province
        result["subject_at_objective"] = bool(
            isinstance(subject_province, int)
            and not isinstance(subject_province, bool)
            and subject_province == objective_province_id
        )

    matched_wars: list[dict[str, object]] = []
    for war in wars:
        if not isinstance(war, dict):
            result["reason"] = "active_war_row_malformed"
            return result
        if war.get("war_id") == war_id:
            matched_wars.append(war)
    if len(matched_wars) > 1:
        result["reason"] = "duplicate_requested_war"
        return result
    requested_war = matched_wars[0] if matched_wars else None
    result["war_active"] = requested_war is not None
    if isinstance(requested_war, dict):
        objectives = requested_war.get("war_objective_province_ids")
        if not isinstance(objectives, list):
            result["reason"] = "war_objective_scope_unavailable"
            return result
        result["objective_in_war"] = objective_province_id in objectives

    player_active_siege = False
    player_active_assault = False
    for war in wars:
        states = war.get("objective_province_states")
        # Exact objective identities can be published without deep objective
        # states.  Missing rows must not block the canary: the required
        # regular/idle state of every player army already excludes an active
        # player siege or assault.  Treat any published deep row as additional
        # contradictory evidence and reject a known player siege below.
        if not isinstance(states, list):
            continue
        for state in states:
            if not isinstance(state, dict):
                continue
            active_siege = state.get("active_siege")
            if active_siege is None:
                continue
            if not isinstance(active_siege, dict):
                continue
            if active_siege.get("player_army_besieging") is True:
                player_active_siege = True
                if active_siege.get("assault_in_progress") is True:
                    player_active_assault = True
    result["player_active_siege"] = player_active_siege
    result["player_active_assault"] = player_active_assault

    checks = (
        (result["paused_map_ready"], "paused_map_required"),
        (result["player_decision_clear"], "pending_player_decision"),
        (
            result["complete_controllable_watch"],
            "controllable_watch_set_changed",
        ),
        (
            result["all_player_armies_regular_idle_stationary"],
            "player_army_not_regular_idle_stationary",
        ),
        (not player_active_siege, "player_active_siege"),
        (not player_active_assault, "player_active_assault"),
        (result["war_active"], "war_not_active"),
        (result["objective_in_war"], "objective_not_in_requested_war"),
        (result["subject_controllable"], "subject_not_controllable"),
        (result["subject_at_objective"], "subject_not_at_objective"),
    )
    for matched, reason in checks:
        if not matched:
            result["status"] = "invalidated"
            result["reason"] = reason
            return result
    result["status"] = "matched"
    result["reason"] = None
    return result


def _battle_sentinel_has_active_retreat(
    snapshot: object, watch_army_ids: tuple[int, ...]
) -> bool:
    """Return whether any completely watched controllable army retreats."""
    if not isinstance(snapshot, dict):
        return False
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return False
    watched = set(watch_army_ids)
    for army in armies:
        if not isinstance(army, dict) or army.get("controllable") is not True:
            continue
        if army.get("army_id") not in watched:
            continue
        named_state = army.get("army_state")
        if (
            army.get("retreating") is True
            or (
                isinstance(named_state, str)
                and named_state.casefold() == "retreating"
            )
            or army.get("army_state_code") == 6
        ):
            return True
    return False


def _normalize_tactical_daily_sentinel_status(
    value: object,
) -> dict[str, object]:
    keys = {
        "state",
        "generation",
        "starting_date_raw",
        "target_date_raw",
        "last_observed_date_raw",
        "trigger_date_raw",
        "speed",
        "mode",
        "army_count",
        "combat_count",
        "completed_daily_ticks",
        "intermediate_pause_count",
        "trigger_flags",
        "trigger_reasons",
        "signed_date_delta_from_target_raw",
        "overshoot_days",
        "pause_wrapper_called",
        "pause_observed",
        "terminal_observed",
        "abnormal",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("tactical daily sentinel status schema is malformed")
    state = value.get("state")
    if state not in {"idle", "armed", "triggered", "failed", "unavailable"}:
        raise ValueError("tactical daily sentinel state is malformed")
    mode = value.get("mode")
    if mode not in {"decision_epoch", "terminal_or_sentinel"}:
        raise ValueError("tactical daily sentinel mode is malformed")
    nonnegative_fields = (
        "generation",
        "starting_date_raw",
        "target_date_raw",
        "last_observed_date_raw",
        "trigger_date_raw",
        "army_count",
        "combat_count",
        "completed_daily_ticks",
        "intermediate_pause_count",
        "trigger_flags",
    )
    for field in nonnegative_fields:
        field_value = value.get(field)
        if (
            isinstance(field_value, bool)
            or not isinstance(field_value, int)
            or field_value < 0
        ):
            raise ValueError(
                f"tactical daily sentinel {field} is malformed"
            )
    speed = value.get("speed")
    if (
        isinstance(speed, bool)
        or not isinstance(speed, int)
        or speed not in {1, 2, 3, 4, 5}
    ):
        raise ValueError("tactical daily sentinel speed is malformed")
    signed_delta = value.get("signed_date_delta_from_target_raw")
    overshoot_days = value.get("overshoot_days")
    if (
        isinstance(signed_delta, bool)
        or not isinstance(signed_delta, int)
        or isinstance(overshoot_days, bool)
        or not isinstance(overshoot_days, int)
        or overshoot_days < -1
    ):
        raise ValueError("tactical daily sentinel date delta is malformed")
    for field in (
        "pause_wrapper_called",
        "pause_observed",
        "terminal_observed",
        "abnormal",
    ):
        if not isinstance(value.get(field), bool):
            raise ValueError(
                f"tactical daily sentinel {field} is malformed"
            )
    trigger_flags = int(value["trigger_flags"])
    if trigger_flags >= 1 << len(_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS):
        raise ValueError("tactical daily sentinel has unknown trigger flags")
    expected_reasons = [
        reason
        for index, reason in enumerate(
            _TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS
        )
        if trigger_flags & (1 << index)
    ]
    if value.get("trigger_reasons") != expected_reasons:
        raise ValueError(
            "tactical daily sentinel trigger reasons disagree with flags"
        )
    if value.get("terminal_observed") is not (
        "combat_terminal" in expected_reasons
    ):
        raise ValueError(
            "tactical daily sentinel terminal flag disagrees with reasons"
        )
    if value.get("abnormal") is not (state == "failed"):
        raise ValueError(
            "tactical daily sentinel abnormal flag disagrees with state"
        )
    return copy.deepcopy(value)


def _validate_tactical_daily_sentinel_arm(
    result: dict[str, object],
    status: dict[str, object],
    *,
    arm_step: str,
    starting_date_raw: int,
    target_date_raw: int,
    speed: int,
    mode: str,
    watch_army_ids: tuple[int, ...],
    sentinel_scope: str,
) -> None:
    combat_count = status.get("combat_count")
    combat_scope_valid = bool(
        isinstance(combat_count, int)
        and not isinstance(combat_count, bool)
        and (
            (sentinel_scope == "active_battle" and combat_count > 0)
            or (
                sentinel_scope
                in {"committed_route", "stationary_objective_hold"}
                and combat_count == 0
            )
        )
    )
    if not (
        result.get("step") == arm_step
        and result.get("accepted") is True
        and result.get("status") == "available"
        and status.get("state") == "armed"
        and isinstance(status.get("generation"), int)
        and int(status["generation"]) > 0
        and status.get("starting_date_raw") == starting_date_raw
        and status.get("target_date_raw") == target_date_raw
        and status.get("last_observed_date_raw") == starting_date_raw
        and status.get("trigger_date_raw") == 0
        and status.get("speed") == speed
        and status.get("mode") == mode
        and status.get("army_count") == len(watch_army_ids)
        and combat_scope_valid
        and status.get("completed_daily_ticks") == 0
        and status.get("intermediate_pause_count") == 0
        and status.get("trigger_flags") == 0
        and status.get("trigger_reasons") == []
        and status.get("signed_date_delta_from_target_raw") == 0
        and status.get("overshoot_days") == -1
        and status.get("pause_wrapper_called") is False
        and status.get("pause_observed") is False
        and status.get("terminal_observed") is False
        and status.get("abnormal") is False
    ):
        raise BridgeUnavailableError(
            "native tactical sentinel arm acknowledgement is inconsistent"
        )


def _validate_tactical_daily_sentinel_stop(
    status: dict[str, object],
    *,
    arm_status: dict[str, object],
    starting_date_raw: int,
    target_date_raw: int,
    ending_date_raw: int,
    elapsed_days: int,
    speed: int,
    mode: str,
    watch_army_ids: tuple[int, ...],
) -> None:
    trigger_reasons = status.get("trigger_reasons")
    raw_delta = ending_date_raw - starting_date_raw
    expected_signed_delta = ending_date_raw - target_date_raw
    if not (
        status.get("state") == "triggered"
        and status.get("abnormal") is False
        and status.get("generation") == arm_status.get("generation")
        and status.get("starting_date_raw") == starting_date_raw
        and status.get("target_date_raw") == target_date_raw
        and status.get("last_observed_date_raw") == ending_date_raw
        and status.get("trigger_date_raw") == ending_date_raw
        and status.get("speed") == speed
        and status.get("mode") == mode
        and status.get("army_count") == len(watch_army_ids)
        and status.get("combat_count") == arm_status.get("combat_count")
        and isinstance(trigger_reasons, list)
        and bool(trigger_reasons)
        and status.get("trigger_flags") != 0
        and status.get("pause_observed") is True
        and status.get("signed_date_delta_from_target_raw")
        == expected_signed_delta
        and status.get("overshoot_days") == 0
        and raw_delta > 0
        and raw_delta % 24 == 0
        and elapsed_days == raw_delta // 24
        and status.get("completed_daily_ticks") == elapsed_days
    ):
        raise BridgeUnavailableError(
            "native tactical sentinel stop failed its generation/date/tick "
            "postcondition"
        )
    deadline_reason = "date_deadline" in trigger_reasons
    if deadline_reason is not (ending_date_raw == target_date_raw):
        raise BridgeUnavailableError(
            "native tactical sentinel deadline reason disagrees with dates"
        )
    native_pause = "native_pause" in trigger_reasons
    expected_intermediate_pause_count = 1 if native_pause else 0
    expected_pause_wrapper_called = not native_pause
    if not (
        status.get("intermediate_pause_count")
        == expected_intermediate_pause_count
        and status.get("pause_wrapper_called")
        is expected_pause_wrapper_called
    ):
        raise BridgeUnavailableError(
            "native tactical sentinel pause ownership disagrees with its "
            "trigger reasons"
        )


def _validate_tactical_daily_sentinel_decision_boundary(
    status: dict[str, object],
    *,
    arm_status: dict[str, object],
    starting_date_raw: int,
    target_date_raw: int,
    ending_date_raw: int,
    elapsed_days: int,
    speed: int,
    mode: str,
    watch_army_ids: tuple[int, ...],
    player_decision_boundary: dict[str, object],
    player_decision_boundary_cancel: dict[str, object] | None,
) -> None:
    """Validate a real replan boundary during a daily-sentinel arm.

    CK3 can materialize a blocking event before the sentinel's final daily
    callback.  The game date then stops while the public paused bit remains
    false.  That path requires an exact generation-bound cancel proven by an
    idle status.  When the event and the native deadline land on the same
    daily callback, the ordinary native stop is already complete and must be
    retained without attempting to cancel it.  A fresh paused active-war-set
    delta uses the same cancel/idle envelope without claiming a native watch.
    """

    raw_delta = ending_date_raw - starting_date_raw
    completed_ticks = status.get("completed_daily_ticks")
    last_observed_date_raw = status.get("last_observed_date_raw")
    boundary_kind = player_decision_boundary.get("kind")
    boundary_identity_valid = bool(
        (
            boundary_kind
            in {"active_event", "pending_character_interaction"}
            and player_decision_boundary.get("instance_id") is not None
        )
        or (
            boundary_kind == "one_life_terminal"
            and isinstance(
                player_decision_boundary.get("terminal_reason"), str
            )
            and (
                player_decision_boundary.get("played_character_alive")
                is False
                or player_decision_boundary.get("played_character_id")
                != player_decision_boundary.get("episode_character_id")
            )
        )
        or (
            boundary_kind == "active_war_set_changed"
            and _battle_sentinel_active_war_set_boundary_identity_valid(
                player_decision_boundary
            )
        )
    )
    if not (
        boundary_identity_valid
        and player_decision_boundary.get("observed_date_raw")
        == ending_date_raw
        and raw_delta >= 0
        and raw_delta % 24 == 0
        and elapsed_days == raw_delta // 24
        and ending_date_raw <= target_date_raw
    ):
        raise BridgeUnavailableError(
            "native tactical sentinel player-decision boundary failed its "
            "identity/date postcondition"
        )
    if status.get("state") == "triggered":
        if player_decision_boundary_cancel is not None:
            raise BridgeUnavailableError(
                "normally triggered tactical sentinel was unexpectedly "
                "canceled at a player-decision boundary"
            )
        _validate_tactical_daily_sentinel_stop(
            status,
            arm_status=arm_status,
            starting_date_raw=starting_date_raw,
            target_date_raw=target_date_raw,
            ending_date_raw=ending_date_raw,
            elapsed_days=elapsed_days,
            speed=speed,
            mode=mode,
            watch_army_ids=watch_army_ids,
        )
        return
    if not (
        status.get("state") == "idle"
        and status.get("abnormal") is False
        and status.get("generation") == arm_status.get("generation")
        and status.get("starting_date_raw") == starting_date_raw
        and status.get("target_date_raw") == target_date_raw
        and status.get("speed") == speed
        and status.get("mode") == mode
        and status.get("army_count") == len(watch_army_ids)
        and status.get("combat_count") == arm_status.get("combat_count")
        and isinstance(completed_ticks, int)
        and not isinstance(completed_ticks, bool)
        and 0 <= completed_ticks <= elapsed_days
        and last_observed_date_raw
        == starting_date_raw + completed_ticks * 24
        and status.get("trigger_date_raw") == 0
        and status.get("intermediate_pause_count") == 0
        and status.get("trigger_flags") == 0
        and status.get("trigger_reasons") == []
        and status.get("signed_date_delta_from_target_raw") == 0
        and status.get("overshoot_days") == -1
        and status.get("pause_wrapper_called") is False
        and status.get("pause_observed") is False
        and status.get("terminal_observed") is False
        and player_decision_boundary_cancel
        == {
            "step": (
                f"{_TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX}"
                f"{arm_status.get('generation')}"
            ),
            "status": "canceled",
            "generation": arm_status.get("generation"),
        }
    ):
        raise BridgeUnavailableError(
            "native tactical sentinel player-decision boundary failed its "
            "generation/date/status postcondition"
        )


def _battle_sentinel_step_result(
    *,
    step: str,
    starting: dict[str, object],
    ending: dict[str, object],
    target_date_raw: int,
    speed: int,
    status_mode: str,
    sentinel_scope: str,
    watch_army_ids: tuple[int, ...],
    arm_status: dict[str, object] | None,
    sentinel_status: dict[str, object] | None,
    actions: list[dict[str, object]],
    progress_status: str,
    cleanup_error: str | None,
    objective_hold_request: tuple[int, int, int, int] | None,
    objective_hold_admission: dict[str, object] | None,
    objective_hold_post_stop: dict[str, object] | None,
    player_decision_boundary: dict[str, object] | None,
    player_decision_boundary_cancel: dict[str, object] | None,
) -> dict[str, object]:
    starting_date_raw = _date_raw(starting, f"{step} starting snapshot")
    ending_date_raw = _date_raw(ending, f"{step} ending snapshot")
    raw_delta = ending_date_raw - starting_date_raw
    elapsed_days = (
        raw_delta // 24 if raw_delta >= 0 and raw_delta % 24 == 0 else 0
    )
    cleanup_actions = [
        action
        for action in actions
        if action.get("purpose") == "managed_failure_cleanup"
    ]
    decision_boundary_pause_actions = [
        action
        for action in actions
        if action.get("purpose")
        == "player_decision_boundary_stabilization"
    ]
    terminal_observed = bool(
        isinstance(sentinel_status, dict)
        and sentinel_status.get("terminal_observed") is True
    )
    trigger_reasons = (
        copy.deepcopy(sentinel_status.get("trigger_reasons"))
        if isinstance(sentinel_status, dict)
        else []
    )
    diagnostics = ending.get("diagnostics")
    played_character = ending.get("played_character")
    one_life_terminal_reason = ending.get("one_life_terminal_reason")
    result: dict[str, object] = {
        "step": step,
        "backend_id": "native-headless",
        "source": "native-tactical-daily-sentinel-composite",
        "starting_date": {"date_raw": starting_date_raw},
        "ending_date": {"date_raw": ending_date_raw},
        "starting_date_raw": starting_date_raw,
        "target_date_raw": target_date_raw,
        "ending_date_raw": ending_date_raw,
        "elapsed_days": elapsed_days,
        "requested_horizon_days": (
            (target_date_raw - starting_date_raw) // 24
            if target_date_raw > starting_date_raw
            and (target_date_raw - starting_date_raw) % 24 == 0
            else None
        ),
        "timeline_speed": speed,
        "timeline_policy": status_mode,
        "sentinel_mode": status_mode,
        "sentinel_scope": sentinel_scope,
        "watch_army_ids": list(watch_army_ids),
        "progress_status": progress_status,
        "stop_kind": (
            "player_decision"
            if player_decision_boundary is not None
            else "terminal"
            if terminal_observed
            else "decision_epoch"
        ),
        "terminal_reached": terminal_observed,
        "one_life_terminal": bool(
            isinstance(one_life_terminal_reason, str)
        ),
        "one_life_terminal_reason": one_life_terminal_reason,
        "trigger_reasons": trigger_reasons,
        "sentinel_generation": (
            sentinel_status.get("generation")
            if isinstance(sentinel_status, dict)
            else arm_status.get("generation")
            if isinstance(arm_status, dict)
            else None
        ),
        "completed_daily_ticks": (
            sentinel_status.get("completed_daily_ticks")
            if isinstance(sentinel_status, dict)
            else None
        ),
        "intermediate_pause_count": (
            sentinel_status.get("intermediate_pause_count")
            if isinstance(sentinel_status, dict)
            else None
        ),
        "overshoot_days": (
            sentinel_status.get("overshoot_days")
            if isinstance(sentinel_status, dict)
            else None
        ),
        "zero_intermediate_pause": bool(
            isinstance(sentinel_status, dict)
            and sentinel_status.get("intermediate_pause_count") == 0
        ),
        "armed_tactical_daily_sentinel": copy.deepcopy(arm_status),
        "tactical_daily_sentinel": copy.deepcopy(sentinel_status),
        "player_decision_boundary": copy.deepcopy(
            player_decision_boundary
        ),
        "player_decision_boundary_cancel": copy.deepcopy(
            player_decision_boundary_cancel
        ),
        "war_progress_before": _war_progress_summary(starting),
        "war_progress_after": _war_progress_summary(ending),
        "actions": copy.deepcopy(actions),
        "external_pause_count": (
            len(cleanup_actions) + len(decision_boundary_pause_actions)
        ),
        "player_decision_boundary_pause_count": len(
            decision_boundary_pause_actions
        ),
        "external_rich_query_count": 0,
        "managed_failure_cleanup": {
            "attempted": bool(cleanup_actions),
            "error": cleanup_error,
        },
        "paused": ending.get("paused") is True,
        "active_event": copy.deepcopy(ending.get("active_event")),
        "pending_character_interaction": copy.deepcopy(
            ending.get("pending_character_interaction")
        ),
        "final_screen": (
            "map_hud"
            if ending.get("paused") is True
            and ending.get("active_event") is None
            and ending.get("pending_character_interaction") is None
            and not isinstance(one_life_terminal_reason, str)
            else None
        ),
        "snapshot_id": ending.get("snapshot_id"),
        "revision": ending.get("revision"),
        "native_revision": ending.get("native_revision"),
        "bridge_pid": (
            diagnostics.get("bridge_pid")
            if isinstance(diagnostics, dict)
            else None
        ),
        "connection_generation": (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        ),
        "episode_character_id": ending.get("episode_character_id"),
        "episode_run_id": ending.get("episode_run_id"),
        "played_character_id": (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        ),
        "played_character_alive": (
            played_character.get("alive")
            if isinstance(played_character, dict)
            else None
        ),
    }
    if objective_hold_request is not None:
        result["war_objective_hold_request"] = {
            "sentinel_scope": "stationary_objective_hold",
            "war_id": objective_hold_request[0],
            "subject_army_id": objective_hold_request[1],
            "objective_province_id": objective_hold_request[2],
            "target_date_raw": objective_hold_request[3],
        }
        result["war_objective_hold_admission"] = copy.deepcopy(
            objective_hold_admission
        )
        result["war_objective_hold_post_stop"] = copy.deepcopy(
            objective_hold_post_stop
        )
        result["exact_war_terminal_watch"] = False
        result["exact_active_war_set_watch"] = False
        result["maximum_omitted_state_detection_lag_days"] = 7
    return result


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
    if snapshot.get("pending_character_interaction") != starting_snapshot.get(
        "pending_character_interaction"
    ):
        return True
    starting_date_raw = _date_raw(
        starting_snapshot, "life-advance starting snapshot"
    )
    current_date_raw = snapshot.get("date_raw")
    if isinstance(current_date_raw, bool) or not isinstance(
        current_date_raw, int
    ):
        return False
    starting_war_progress = _active_war_progress_signature(starting_snapshot)
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


def _battle_identity_materialization_request(
    snapshot: dict[str, object],
) -> dict[str, object] | None:
    """Validate the sole public condition allowed to materialize CombatID."""
    subject = snapshot.get("battle_control_snapshot_v1_subject_army_id")
    if not _positive_native_id(subject):
        return None
    army = _army_by_id(snapshot, int(subject))
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and snapshot.get("battle_control_snapshot_v1_status")
        == BATTLE_CONTROL_IDENTITY_PENDING_STATUS
        and snapshot.get("battle_control_snapshot_v1_diagnostic_reason")
        == BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
        and snapshot.get("battle_control_snapshot_v1_native_query_status")
        == "state_changed"
        and snapshot.get("battle_control_snapshot_v1_query_attempts")
        == _BATTLE_CONTROL_QUERY_MAX_ATTEMPTS
        and snapshot.get("battle_control_snapshot_v1") is None
        and snapshot.get("battle_control_snapshot_v1_queried_snapshot_id")
        == snapshot.get("snapshot_id")
        and snapshot.get("battle_control_snapshot_v1_queried_revision")
        == snapshot.get("revision")
        and snapshot.get(
            "battle_control_snapshot_v1_queried_native_revision"
        )
        == snapshot.get("native_revision")
        and isinstance(army, dict)
        and army.get("controllable") is True
        and army.get("in_combat") is True
    ):
        return None
    return {
        "status": BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
        "diagnostic_reason": BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC,
        "subject_public_cunit_id": int(subject),
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
    }


def _battle_identity_materialization_for_snapshot(
    history: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    subject_public_cunit_id: int,
) -> dict[str, object] | None:
    """Find a consumed materialization whose ending is this exact frame."""
    for row in reversed(_native_history_after_latest_restore(history)):
        if row.get("ok") is not True:
            continue
        command, result = _effective_native_history_entry(row)
        if command != "life-advance" or not isinstance(result, dict):
            continue
        materialization = result.get("battle_identity_materialization")
        if not isinstance(materialization, dict):
            continue
        start_date_raw = materialization.get("starting_date_raw")
        end_date_raw = materialization.get("ending_date_raw")
        start_revision = materialization.get("starting_revision")
        end_revision = materialization.get("ending_revision")
        start_native_revision = materialization.get(
            "starting_native_revision"
        )
        end_native_revision = materialization.get("ending_native_revision")
        if not (
            materialization.get("schema_version") == 1
            and materialization.get("status") == "one_day_advanced"
            and materialization.get("proof_kind")
            == "battle_identity_materialization"
            and materialization.get("diagnostic_reason")
            == BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
            and materialization.get("subject_public_cunit_id")
            == subject_public_cunit_id
            and materialization.get("next_revision_requirement")
            == "full_combat_id"
            and isinstance(start_date_raw, int)
            and not isinstance(start_date_raw, bool)
            and isinstance(end_date_raw, int)
            and not isinstance(end_date_raw, bool)
            and end_date_raw == start_date_raw + 24
            and materialization.get("elapsed_days") == 1
            and isinstance(start_revision, int)
            and not isinstance(start_revision, bool)
            and isinstance(end_revision, int)
            and not isinstance(end_revision, bool)
            and end_revision > start_revision
            and _positive_native_id(start_native_revision)
            and _positive_native_id(end_native_revision)
            and int(end_native_revision) > int(start_native_revision)
            and materialization.get("ending_snapshot_id")
            == snapshot.get("snapshot_id")
            and end_revision == snapshot.get("revision")
            and end_native_revision == snapshot.get("native_revision")
            and end_date_raw == snapshot.get("date_raw")
        ):
            continue
        return copy.deepcopy(materialization)
    return None


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


def _life_advance_timeline_policy(
    snapshot: dict[str, object],
    *,
    horizon_days: int,
    exact_one_day: bool,
    exact_one_day_proof_kind: str | None = None,
    exact_one_day_preferred_speed: int = 1,
    available_action_steps: set[str] | None = None,
) -> tuple[int, str]:
    """Choose wall-clock speed while retaining paused tactical sampling.

    CK3 still executes the same native daily movement/contact chain at every
    public timeline speed.  A proof-bound contact-free day may therefore use
    the configured speed-1..5 A/B arm while retaining the exact same +24
    postcondition.  A known unavoidable endpoint remains speed one because it
    must observe the contact transition itself.  Complete enemy routes that
    are wholly disjoint from every known-stationary controllable army may use
    speed three while retaining the one-day requested horizon and the same
    paused re-observation.  Route-free bounded slices retain speed five.
    """
    if exact_one_day:
        return _exact_route_contact_timeline_policy(
            proof_kind=exact_one_day_proof_kind,
            preferred_speed=exact_one_day_preferred_speed,
            available_action_steps=available_action_steps,
        )
    if horizon_days != 1:
        return 5, "bounded_non_tactical"

    player_armies = snapshot.get("player_armies")
    players = (
        player_armies if isinstance(player_armies, list) else []
    )
    for army in players:
        if not isinstance(army, dict) or army.get("controllable") is not True:
            continue
        if _army_in_combat_or_retreat(army) or _army_has_active_route(army):
            return 1, "player_tactical"

    if _player_assault_in_progress(snapshot):
        return 1, "player_assault"

    enemy_routes: list[dict[str, object]] = []
    wars = snapshot.get("active_wars")
    for war in wars if isinstance(wars, list) else []:
        if not isinstance(war, dict):
            continue
        enemies = war.get("enemy_armies")
        for enemy in enemies if isinstance(enemies, list) else []:
            if not isinstance(enemy, dict) or _army_is_retreating(enemy):
                continue
            if _army_has_active_route(enemy):
                enemy_routes.append(enemy)

    if _remote_enemy_routes_speed_three_ready(snapshot, enemy_routes):
        return 3, "remote_enemy_route"
    return 1, "enemy_route_imminent_or_unknown"


def _exact_route_contact_timeline_policy(
    *,
    proof_kind: str | None,
    preferred_speed: int,
    available_action_steps: set[str] | None,
) -> tuple[int, str]:
    """Select an exact-day route arm without weakening its +24 contract.

    Speed three is the production candidate.  Speeds four and five are
    only constructible when the driver itself was created with the explicit
    high-speed A/B admission; this pure selector merely consumes that already
    validated preference.  Old bridges that do not advertise the requested
    public speed retain a deterministic speed-one fallback.
    """
    selected_proof_kind = (
        proof_kind if isinstance(proof_kind, str) else "unknown"
    )
    if selected_proof_kind == "battle_identity_materialization":
        return 1, "exact_one_day_battle_identity_materialization"
    if selected_proof_kind != "contact_free":
        return 1, "exact_one_day_unavoidable_contact"
    requested = _timeline_speed(
        preferred_speed, "exact_one_day_preferred_speed"
    )
    steps = (
        available_action_steps
        if isinstance(available_action_steps, set)
        else set()
    )
    if f"set-speed-{requested}" in steps:
        return requested, f"exact_one_day_contact_free_speed_{requested}"
    return (
        1,
        f"exact_one_day_contact_free_speed_{requested}_fallback_speed_1",
    )


def _remote_enemy_routes_speed_three_ready(
    snapshot: dict[str, object],
    enemy_routes: list[dict[str, object]],
) -> bool:
    """Require complete, disjoint player/enemy route state for speed three."""
    if (
        snapshot.get("army_routes_supported") is not True
        or snapshot.get("war_objective_assault_supported") is not True
        or not enemy_routes
        or not all(
            _army_has_auditable_route(army) for army in enemy_routes
        )
    ):
        return False

    player_armies = snapshot.get("player_armies")
    if not isinstance(player_armies, list) or not player_armies:
        return False
    player_by_id: dict[int, dict[str, object]] = {}
    player_provinces: set[int] = set()
    for army in player_armies:
        if not isinstance(army, dict) or army.get("controllable") is not True:
            return False
        army_id = army.get("army_id")
        province_id = army.get("current_province_id")
        if (
            not _positive_native_id(army_id)
            or not _positive_native_id(province_id)
            or not _army_route_projection_complete(army)
            or not _army_is_known_stationary(army)
            or _army_in_combat_or_retreat(army)
            or _army_has_active_route(army)
        ):
            return False
        player_by_id[int(army_id)] = army
        player_provinces.add(int(province_id))
    if len(player_by_id) != len(player_armies):
        return False

    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or not wars:
        return False
    observed_enemy_routes: set[int] = set()
    enemy_projections: dict[int, tuple[object, ...]] = {}
    for war in wars:
        if not isinstance(war, dict):
            return False
        allied = war.get("allied_armies")
        enemies = war.get("enemy_armies")
        if not isinstance(allied, list) or not isinstance(enemies, list):
            return False
        war_player_ids: set[int] = set()
        for ally in allied:
            if not isinstance(ally, dict):
                return False
            if ally.get("controllable") is not True:
                continue
            ally_id = ally.get("army_id")
            ally_province = ally.get("current_province_id")
            if (
                not _positive_native_id(ally_id)
                or not _positive_native_id(ally_province)
                or int(ally_id) not in player_by_id
                or int(ally_id) in war_player_ids
                or _army_tactical_projection(ally)
                != _army_tactical_projection(player_by_id[int(ally_id)])
            ):
                return False
            war_player_ids.add(int(ally_id))
        if war_player_ids != set(player_by_id):
            return False

        war_enemy_ids: set[int] = set()
        for enemy in enemies:
            if not isinstance(enemy, dict):
                return False
            if _army_is_retreating(enemy):
                continue
            enemy_id = enemy.get("army_id")
            enemy_province = enemy.get("current_province_id")
            if (
                not _positive_native_id(enemy_id)
                or not _positive_native_id(enemy_province)
                or not _army_route_projection_complete(enemy)
                or int(enemy_id) in war_enemy_ids
                or int(enemy_province) in player_provinces
            ):
                return False
            war_enemy_ids.add(int(enemy_id))
            projection = _army_tactical_projection(enemy)
            prior_projection = enemy_projections.setdefault(
                int(enemy_id), projection
            )
            if prior_projection != projection:
                return False
            if not _army_has_active_route(enemy):
                continue
            if not _army_has_auditable_route(enemy):
                return False
            route = enemy["route_province_ids"]
            if any(
                int(province_id) in player_provinces
                for province_id in route
            ):
                return False
            observed_enemy_routes.add(int(enemy_id))
    return observed_enemy_routes == {
        int(army["army_id"]) for army in enemy_routes
    }


def _army_has_active_route(army: dict[str, object]) -> bool:
    target = army.get("move_target_province_id")
    route = army.get("route_province_ids")
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    return bool(
        _positive_native_id(target)
        or isinstance(route, list)
        and bool(route)
        or isinstance(state, str)
        and state.casefold() == "moving"
        or state_code == 7
    )


def _army_has_auditable_route(army: dict[str, object]) -> bool:
    target = army.get("move_target_province_id")
    route = army.get("route_province_ids")
    return bool(
        _positive_native_id(target)
        and isinstance(route, list)
        and bool(route)
        and all(_positive_native_id(province_id) for province_id in route)
        and route[-1] == target
    )


def _army_route_projection_complete(army: dict[str, object]) -> bool:
    if "move_target_province_id" not in army:
        return False
    target = army.get("move_target_province_id")
    route = army.get("route_province_ids")
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    known_state = bool(
        isinstance(state, str)
        and state.casefold()
        in {"regular", "combat", "sieging", "gathering", "moving"}
        or not isinstance(state, str)
        and isinstance(state_code, int)
        and not isinstance(state_code, bool)
        and state_code in {1, 2, 3, 5, 7}
    )
    return bool(
        (target is None or _positive_native_id(target))
        and isinstance(route, list)
        and all(_positive_native_id(province_id) for province_id in route)
        and known_state
    )


def _army_tactical_projection(
    army: dict[str, object],
) -> tuple[object, ...]:
    route = army.get("route_province_ids")
    state = army.get("army_state")
    return (
        army.get("army_id"),
        army.get("current_province_id"),
        army.get("move_target_province_id"),
        tuple(route) if isinstance(route, list) else None,
        state.casefold() if isinstance(state, str) else None,
        army.get("army_state_code"),
        army.get("in_combat"),
        army.get("retreating"),
        army.get("controllable"),
    )


def _army_is_known_stationary(army: dict[str, object]) -> bool:
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    return bool(
        isinstance(state, str)
        and state.casefold() in {"regular", "sieging"}
        or not isinstance(state, str)
        and isinstance(state_code, int)
        and not isinstance(state_code, bool)
        and state_code in {1, 3}
    )


def _army_is_retreating(army: dict[str, object]) -> bool:
    state = army.get("army_state")
    return bool(
        army.get("retreating") is True
        or isinstance(state, str)
        and state.casefold() == "retreating"
        or army.get("army_state_code") == 6
    )


def _player_assault_in_progress(snapshot: dict[str, object]) -> bool:
    if snapshot.get("war_objective_assault_supported") is not True:
        return False
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
                and active_siege.get("assault_observable") is True
                and active_siege.get("assault_in_progress") is True
            ):
                return True
    return False


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
                # Historical strategy only reads objective-state detail for
                # active-siege work/loss and stall observations.  Objective
                # identity stays complete in war_objective_province_ids;
                # copying every inactive province here made a 4,563-row
                # production driver state grow to 93.96 MB.
                "objective_province_states": (
                    _active_siege_progress_states(
                        war.get("objective_province_states")
                    )
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


def _active_siege_progress_states(value: object) -> list[dict[str, object]]:
    """Copy only objective rows that can affect historical siege decisions."""
    return [
        copy.deepcopy(state)
        for state in (value if isinstance(value, list) else ())
        if isinstance(state, dict)
        and isinstance(state.get("active_siege"), dict)
    ]


def _compact_war_progress_history_in_place(
    history: list[dict[str, object]],
) -> int:
    """Remove legacy inactive objective rows; return the number removed."""
    removed = 0
    for row in history:
        result = row.get("result") if isinstance(row, dict) else None
        if not isinstance(result, dict):
            continue
        for name in ("war_progress_before", "war_progress_after"):
            summary = result.get(name)
            wars = summary.get("wars") if isinstance(summary, dict) else None
            for war in wars if isinstance(wars, list) else ():
                if not isinstance(war, dict):
                    continue
                states = war.get("objective_province_states")
                if not isinstance(states, list):
                    continue
                active = [
                    state
                    for state in states
                    if isinstance(state, dict)
                    and isinstance(state.get("active_siege"), dict)
                ]
                removed += len(states) - len(active)
                war["objective_province_states"] = active
    return removed


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


def _retarget_timeline_step_result(
    result: dict[str, object], snapshot: dict[str, object]
) -> dict[str, object]:
    """Bind timeline result evidence to the semantic frame it describes."""
    updated = copy.deepcopy(result)
    ending_date_raw = _date_raw(snapshot, "timeline result ending snapshot")
    starting_date_raw = updated.get("starting_date_raw")
    updated.update(
        {
            "ending_date": {"date_raw": ending_date_raw},
            "ending_date_raw": ending_date_raw,
            "elapsed_days": (
                max(0, (ending_date_raw - starting_date_raw) // 24)
                if isinstance(starting_date_raw, int)
                and not isinstance(starting_date_raw, bool)
                else updated.get("elapsed_days")
            ),
            "war_progress_after": _war_progress_summary(snapshot),
            "paused": snapshot.get("paused") is True,
            "active_event": snapshot.get("active_event"),
            "final_screen": (
                "map_hud" if snapshot.get("paused") is True else None
            ),
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
        }
    )
    return updated


def _newer_native_contact_refresh_frame(
    previous: dict[str, object], refreshed: dict[str, object]
) -> bool:
    """Require both endpoint and native snapshot revisions to move forward."""

    def newer(value: object, prior: object) -> bool:
        return bool(
            isinstance(value, int)
            and not isinstance(value, bool)
            and isinstance(prior, int)
            and not isinstance(prior, bool)
            and value > prior
        )

    return newer(refreshed.get("revision"), previous.get("revision")) and newer(
        refreshed.get("native_revision"), previous.get("native_revision")
    )


def _same_paused_contact_refresh_owner(
    previous: dict[str, object], refreshed: dict[str, object]
) -> bool:
    """Keep the forced refresh on the exact same paused gameplay endpoint."""
    previous_diagnostics = previous.get("diagnostics")
    refreshed_diagnostics = refreshed.get("diagnostics")
    if not isinstance(previous_diagnostics, dict) or not isinstance(
        refreshed_diagnostics, dict
    ):
        return False
    return bool(
        _newer_native_contact_refresh_frame(previous, refreshed)
        and refreshed.get("map_ready") is True
        and refreshed.get("paused") is True
        and refreshed.get("date_raw") == previous.get("date_raw")
        and refreshed.get("speed") == previous.get("speed")
        and refreshed.get("active_event") == previous.get("active_event")
        and refreshed.get("episode_character_id")
        == previous.get("episode_character_id")
        and refreshed.get("episode_run_id") == previous.get("episode_run_id")
        and refreshed.get("local_player_id")
        == previous.get("local_player_id")
        and refreshed_diagnostics.get("connection_generation")
        == previous_diagnostics.get("connection_generation")
        and refreshed_diagnostics.get("bridge_pid")
        == previous_diagnostics.get("bridge_pid")
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


def _retryable_life_advance_pause_owner(
    previous: dict[str, object], refreshed: dict[str, object]
) -> bool:
    """Keep one idempotent pause retry bound to the same running episode."""
    return _retryable_life_advance_timeline_owner(
        previous, refreshed, expected_paused=False
    )


def _retryable_life_advance_resume_owner(
    previous: dict[str, object], refreshed: dict[str, object]
) -> bool:
    """Keep one idempotent resume retry bound to the same paused episode."""
    return _retryable_life_advance_timeline_owner(
        previous, refreshed, expected_paused=True
    )


def _retryable_life_advance_timeline_owner(
    previous: dict[str, object],
    refreshed: dict[str, object],
    *,
    expected_paused: bool,
) -> bool:
    previous_diagnostics = previous.get("diagnostics")
    refreshed_diagnostics = refreshed.get("diagnostics")
    if not isinstance(previous_diagnostics, dict) or not isinstance(
        refreshed_diagnostics, dict
    ):
        return False
    return bool(
        refreshed.get("map_ready") is True
        and refreshed.get("paused") is expected_paused
        and refreshed.get("one_life_terminal_reason") is None
        and previous.get("episode_character_id")
        == refreshed.get("episode_character_id")
        and previous.get("episode_run_id") == refreshed.get("episode_run_id")
        and previous_diagnostics.get("connection_generation")
        == refreshed_diagnostics.get("connection_generation")
        and previous_diagnostics.get("bridge_pid")
        == refreshed_diagnostics.get("bridge_pid")
        and _retryable_life_advance_change(previous, refreshed)
    )


def _timeline_ack_status(result: dict[str, object]) -> str:
    status = result.get("status")
    return status if isinstance(status, str) and status else "missing"


def _state_frame_rejection_summary(snapshot: dict[str, object]) -> object:
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return None
    return {
        "rejected_count": diagnostics.get(
            "rejected_state_snapshot_count"
        ),
        "last_rejected": diagnostics.get("last_rejected_state_snapshot"),
        "publish_diagnostic_count": diagnostics.get(
            "snapshot_publish_diagnostic_count"
        ),
        "last_publish": diagnostics.get(
            "last_snapshot_publish_diagnostic"
        ),
    }


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


def _title_map_navigation_binding_from_snapshot(
    snapshot: object,
) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    return normalize_title_map_navigation_v1_binding(
        {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
            "date_raw": snapshot.get("date_raw"),
            "episode_run_id": snapshot.get("episode_run_id"),
            "connection_generation": connection_generation,
        }
    )


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


def _active_combat_retreat_source_binding(
    snapshot: object,
) -> dict[str, object] | None:
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return None
    snapshot_id = snapshot.get("snapshot_id")
    revision = snapshot.get("revision")
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    episode_run_id = snapshot.get("episode_run_id")
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    if not (
        isinstance(snapshot_id, str)
        and snapshot_id
        and isinstance(revision, int)
        and not isinstance(revision, bool)
        and 0 <= revision <= 2**64 - 1
        and isinstance(native_revision, int)
        and not isinstance(native_revision, bool)
        and 1 <= native_revision <= 2**64 - 1
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and -(2**63) <= date_raw <= 2**63 - 1
        and isinstance(episode_run_id, str)
        and episode_run_id
        and isinstance(connection_generation, int)
        and not isinstance(connection_generation, bool)
        and 1 <= connection_generation <= 2**64 - 1
    ):
        return None
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "episode_run_id": episode_run_id,
        "connection_generation": connection_generation,
    }


def _require_active_combat_retreat_source_binding(
    snapshot: object,
) -> dict[str, object]:
    binding = _active_combat_retreat_source_binding(snapshot)
    if binding is None:
        raise BridgeUnavailableError(
            "active-combat retreat requires one complete paused episode frame"
        )
    return binding


def _active_combat_retreat_source_mismatch_reason(
    expected: object,
    snapshot: object,
) -> str | None:
    current = _active_combat_retreat_source_binding(snapshot)
    if current is None:
        return "snapshot_binding_unavailable"
    if not isinstance(expected, dict):
        return "stale_or_unknown_token"
    for key, reason in (
        ("revision", "revision_changed"),
        ("native_revision", "native_revision_changed"),
        ("date_raw", "date_changed"),
        ("episode_run_id", "episode_changed"),
        ("connection_generation", "connection_changed"),
        ("snapshot_id", "snapshot_changed"),
    ):
        if expected.get(key) != current.get(key):
            return reason
    return None


def _active_combat_retreat_battle_binding(
    battle: dict[str, object],
) -> dict[str, object]:
    return {
        "combat_id": battle.get("combat_id"),
        "combat_province_id": battle.get("combat_province_id"),
        "selected_public_cunit_id": battle.get(
            "selected_public_cunit_id"
        ),
        "selected_native_carmy_id": battle.get("selected_native_carmy_id"),
        "selected_owner_character_id": battle.get(
            "selected_owner_character_id"
        ),
        "side_index": battle.get("side_index"),
        "side_scope": battle.get("side_scope"),
        "affected_public_cunit_ids_in_stored_order": copy.deepcopy(
            battle.get("affected_public_cunit_ids_in_stored_order")
        ),
        "unaffected_same_side_public_cunit_ids_in_stored_order": (
            copy.deepcopy(
                battle.get(
                    "unaffected_same_side_public_cunit_ids_in_stored_order"
                )
            )
        ),
    }


def _active_combat_retreat_token_matches_snapshot(
    token_binding: object,
    snapshot: object,
) -> bool:
    if not isinstance(token_binding, dict) or set(token_binding) != {
        "candidate_token",
        "order_step",
        "source_binding",
        "battle_control_snapshot",
        "battle_binding",
        "target_province_id",
        "route_preview",
    }:
        return False
    if token_binding.get("source_binding") != (
        _active_combat_retreat_source_binding(snapshot)
    ):
        return False
    battle = token_binding.get("battle_binding")
    order = parse_order_active_combat_retreat_v1_step(
        token_binding.get("order_step")
    )
    if not isinstance(battle, dict) or order is None:
        return False
    if not (
        order.get("candidate_token") == token_binding.get("candidate_token")
        and order.get("expected_snapshot_revision")
        == token_binding["source_binding"].get("revision")
        and order.get("expected_combat_id") == battle.get("combat_id")
        and order.get("selected_public_cunit_id")
        == battle.get("selected_public_cunit_id")
        and order.get("expected_side_index") == battle.get("side_index")
        and order.get("expected_scope") == battle.get("side_scope")
        and order.get("target_province_id")
        == token_binding.get("target_province_id")
    ):
        return False
    selected = _army_by_id(
        snapshot, int(order["selected_public_cunit_id"])
    )
    return bool(
        isinstance(selected, dict)
        and selected.get("controllable") is True
        and _army_in_active_combat(selected)
        and selected.get("current_province_id")
        == battle.get("combat_province_id")
    )


def _active_combat_retreat_preview_steps(
    snapshot: dict[str, object],
    action_steps: set[str],
) -> set[str]:
    result: set[str] = set()
    if snapshot.get("paused") is not True:
        return result
    for step in tuple(action_steps):
        parsed = parse_preview_move_army_step(step)
        if parsed is None:
            continue
        selected_public_cunit_id, target_province_id = parsed
        army = _army_by_id(snapshot, selected_public_cunit_id)
        if not (
            isinstance(army, dict)
            and army.get("controllable") is True
            and _army_in_active_combat(army)
            and target_province_id != army.get("current_province_id")
        ):
            continue
        result.add(
            preview_active_combat_retreat_v1_step(
                selected_public_cunit_id, target_province_id
            )
        )
    return result


def _canonical_active_combat_retreat_route_preview(
    result: object,
    *,
    selected_public_cunit_id: int,
    combat_province_id: int,
    target_province_id: int,
    expected_date_raw: int,
) -> dict[str, object] | None:
    if not isinstance(result, dict) or result.get("status") != "available":
        return None
    route_preview = result.get("route_preview")
    if not isinstance(route_preview, dict):
        return None
    route = route_preview.get("route_province_ids")
    if not (
        route_preview.get("status") == "available"
        and route_preview.get("army_id") == selected_public_cunit_id
        and route_preview.get("origin_province_id") == combat_province_id
        and route_preview.get("target_province_id") == target_province_id
        and target_province_id != combat_province_id
        and isinstance(route, list)
        and bool(route)
        and all(_positive_native_id(province_id) for province_id in route)
        and route[-1] == target_province_id
        and route_preview.get("previewed_date_raw") == expected_date_raw
    ):
        return None
    move_mode = route_preview.get("move_mode")
    eta_date_raw = route_preview.get("eta_date_raw")
    movement_days = route_preview.get("movement_days")
    if not (
        (
            move_mode is None
            or (
                isinstance(move_mode, int)
                and not isinstance(move_mode, bool)
                and -(2**31) <= move_mode <= 2**31 - 1
            )
        )
        and (
            eta_date_raw is None
            or (
                isinstance(eta_date_raw, int)
                and not isinstance(eta_date_raw, bool)
                and -(2**63) <= eta_date_raw <= 2**63 - 1
            )
        )
        and (
            movement_days is None
            or (
                isinstance(movement_days, int)
                and not isinstance(movement_days, bool)
                and 0 <= movement_days <= 2**31 - 1
            )
        )
    ):
        return None
    return {
        "army_id": selected_public_cunit_id,
        "origin_province_id": combat_province_id,
        "target_province_id": target_province_id,
        "route_province_ids": list(route),
        "previewed_date_raw": expected_date_raw,
        "move_mode": move_mode,
        "eta_date_raw": eta_date_raw,
        "movement_days": movement_days,
    }


def _active_combat_retreat_preview_payload(
    *,
    step: str,
    source_binding: dict[str, object],
    battle: dict[str, object],
    target_province_id: int,
    target_preview: dict[str, object],
    status: str,
    unavailable_reason: str | None,
    action_ready: bool,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE,
        "step": step,
        "status": status,
        "unavailable_reason": unavailable_reason,
        "action_ready": action_ready,
        "source_binding": copy.deepcopy(source_binding),
        "battle_control_snapshot": copy.deepcopy(battle),
        "selected_public_cunit_id": battle["selected_public_cunit_id"],
        "selected_native_carmy_id": battle["selected_native_carmy_id"],
        "selected_owner_character_id": battle[
            "selected_owner_character_id"
        ],
        "combat_id": battle["combat_id"],
        "combat_province_id": battle["combat_province_id"],
        "side_index": battle["side_index"],
        "side_scope": battle["side_scope"],
        "affected_public_cunit_ids_in_stored_order": copy.deepcopy(
            battle["affected_public_cunit_ids_in_stored_order"]
        ),
        "unaffected_same_side_public_cunit_ids_in_stored_order": (
            copy.deepcopy(
                battle[
                    "unaffected_same_side_public_cunit_ids_in_stored_order"
                ]
            )
        ),
        "target_province_id": target_province_id,
        "target_preview": copy.deepcopy(target_preview),
        "backend_id": "native-headless",
    }


def _active_combat_retreat_not_observed_postcondition() -> dict[str, object]:
    return {
        "status": "not_observed",
        "observation_snapshot_id": None,
        "observation_revision": None,
        "observation_native_revision": None,
        "observation_date_raw": None,
        "affected_armies_in_stored_order": [],
        "all_affected_retreating_observed": None,
        "all_affected_target_observed": None,
        "all_affected_route_observed": None,
        "combat_id_post_query_performed": False,
        "winner_verified": False,
        "phase_verified": False,
        "full_postcondition_verified": False,
    }


def _active_combat_retreat_pending_postcondition() -> dict[str, object]:
    return {
        **_active_combat_retreat_not_observed_postcondition(),
        "status": "observation_pending",
    }


def _active_combat_retreat_semantic_postcondition(
    snapshot: dict[str, object],
    *,
    affected_public_cunit_ids: list[int],
    target_province_id: int,
) -> dict[str, object]:
    source = _active_combat_retreat_source_binding(snapshot)
    if source is None:
        return _active_combat_retreat_pending_postcondition()
    observations: list[dict[str, object]] = []
    for public_cunit_id in affected_public_cunit_ids:
        army = _army_by_id(snapshot, public_cunit_id)
        if not isinstance(army, dict):
            observations.append(
                {
                    "public_cunit_id": public_cunit_id,
                    "present": False,
                    "retreating": None,
                    "move_target_province_id": None,
                    "target_matches": None,
                    "route_province_ids": None,
                    "route_reaches_target": None,
                }
            )
            continue
        move_target = army.get("move_target_province_id")
        move_target = (
            int(move_target) if _positive_native_id(move_target) else None
        )
        route = _canonical_remaining_route(army)
        move_target_observable = army.get("move_target_observable") is not False
        retreat_state_observable = any(
            key in army
            for key in (
                "retreating",
                "in_combat",
                "army_state",
                "army_state_code",
            )
        )
        observations.append(
            {
                "public_cunit_id": public_cunit_id,
                "present": True,
                "retreating": (
                    _army_retreating(army)
                    if retreat_state_observable
                    else None
                ),
                "move_target_province_id": (
                    move_target if move_target_observable else None
                ),
                "target_matches": (
                    move_target == target_province_id
                    if move_target_observable
                    else None
                ),
                "route_province_ids": route,
                "route_reaches_target": (
                    bool(route and route[-1] == target_province_id)
                    if isinstance(route, list)
                    else None
                ),
            }
        )
    return {
        "status": "observed_partial",
        "observation_snapshot_id": source["snapshot_id"],
        "observation_revision": source["revision"],
        "observation_native_revision": source["native_revision"],
        "observation_date_raw": source["date_raw"],
        "affected_armies_in_stored_order": observations,
        "all_affected_retreating_observed": bool(observations) and all(
            row["present"] is True and row["retreating"] is True
            for row in observations
        ),
        "all_affected_target_observed": bool(observations) and all(
            row["present"] is True and row["target_matches"] is True
            for row in observations
        ),
        "all_affected_route_observed": bool(observations) and all(
            row["present"] is True
            and row["route_reaches_target"] is True
            for row in observations
        ),
        "combat_id_post_query_performed": False,
        "winner_verified": False,
        "phase_verified": False,
        "full_postcondition_verified": False,
    }


def _normalize_active_combat_retreat_order_payload(
    payload: dict[str, object],
    *,
    request: dict[str, object],
) -> dict[str, object]:
    try:
        return normalize_active_combat_retreat_v1_order_ack(
            payload,
            expected_selected_public_cunit_id=int(
                request["selected_public_cunit_id"]
            ),
            expected_snapshot_revision=int(
                request["expected_snapshot_revision"]
            ),
            expected_combat_id=int(request["expected_combat_id"]),
            expected_side_index=int(request["expected_side_index"]),
            expected_scope=str(request["expected_scope"]),
            expected_target_province_id=int(request["target_province_id"]),
            expected_candidate_token=str(request["candidate_token"]),
        )
    except ValueError as error:
        raise BridgeUnavailableError(
            f"active-combat retreat order composition failed: {error}"
        ) from error


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


def _army_in_active_combat(army: dict[str, object]) -> bool:
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    return bool(
        army.get("in_combat") is True
        or (
            isinstance(state, str)
            and state.casefold() == "combat"
        )
        or (
            isinstance(state_code, int)
            and not isinstance(state_code, bool)
            and state_code == 2
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
    expand_battle_control_snapshots = False
    expand_battle_reinforcement_assignments = False
    advertise_campaign_root_context = False
    advertise_loaded_feature_manifest = False
    advertise_pending_interaction_context = False
    advertise_current_event_window_context = False
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
        if capability == CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY:
            # This parameterized presentation command is explicit-only.  Its
            # fixed semantic step must never enter planner/action-step space.
            continue
        if step == "select-event-option-N":
            expand_event_options = True
        elif step in {
            "accept-pending-character-interaction",
            "reject-pending-character-interaction",
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
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
        elif capability == QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY:
            expand_battle_control_snapshots = True
        elif capability == QUERY_BATTLE_TRANSITION_V1_CAPABILITY:
            # CombatIDs are supplied explicitly (normally from a prior battle
            # frame/token); never advertise the adapter's N placeholder.
            continue
        elif capability == QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY:
            # This journal query requires two exact identities and an explicit
            # cursor.  It is callable through the typed service, not an action.
            continue
        elif (
            capability
            == QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
        ):
            expand_battle_reinforcement_assignments = True
        elif capability == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY:
            advertise_campaign_root_context = True
        elif capability == QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY:
            # The case selector and request nonce are explicit MCP inputs.
            # Never expose the fixed native command as a planner action.
            continue
        elif (
            capability
            == QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
        ):
            # Owner, subject, and nonce are explicit MCP inputs. Native code
            # proves AI-manager eligibility; this is never a planner action.
            continue
        elif (
            capability
            == QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
        ):
            # The expected owner and request nonce are explicit MCP inputs;
            # the paused played character is the only subject.
            continue
        elif capability == QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY:
            # The expected owner and request nonce are explicit MCP inputs;
            # the fixed native command is not a parameterless planner action.
            continue
        elif (
            capability
            == QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
        ):
            # Owner and nonce are explicit MCP inputs. Default descriptors do
            # not advertise this until a paused production artifact exists.
            continue
        elif (
            capability
            == QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
        ):
            # Owner is an equality filter, nonce is explicit, and the paused
            # played character is the provider-owned subject.
            continue
        elif (
            capability
            == QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
        ):
            # Owner is an equality filter and nonce is explicit. The fixed
            # received-self lifecycle query is never a planner action.
            continue
        elif capability == QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY:
            # Owner, profile and nonce are explicit MCP inputs. The paused
            # played character remains the provider-owned subject.
            continue
        elif capability == QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY:
            # The nonce is explicit; all widget and ACL identities are fixed
            # provider allowlists and never become planner actions.
            continue
        elif capability == QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY:
            advertise_loaded_feature_manifest = True
        elif (
            capability
            == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
        ):
            advertise_pending_interaction_context = True
        elif capability == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY:
            advertise_current_event_window_context = True
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
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX,
                QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX,
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX,
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX,
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
                QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
                QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
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
    if isinstance(pending_character_interaction, dict):
        if (
            pending_character_interaction.get("auto_accept_notification")
            is False
        ):
            steps.update(
                step
                for step in pending_interaction_steps
                if step != ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP
            )
        elif (
            paused is True
            and pending_character_interaction.get(
                "auto_accept_notification"
            )
            is True
            and ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP
            in pending_interaction_steps
        ):
            steps.add(ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP)
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
    if advertise_campaign_root_context and paused is True:
        steps.add(QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP)
    if advertise_loaded_feature_manifest and paused is True:
        steps.add(QUERY_LOADED_FEATURE_MANIFEST_V1_STEP)
    if (
        advertise_pending_interaction_context
        and paused is True
        and isinstance(pending_character_interaction, dict)
        and _valid_pending_interaction_id(
            pending_character_interaction.get("instance_id")
        )
    ):
        steps.add(QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP)
    if (
        advertise_current_event_window_context
        and paused is True
        and isinstance(active_event, dict)
        and _positive_native_id(active_event.get("instance_id"))
        and int(active_event["instance_id"]) <= 2**31 - 1
    ):
        steps.add(QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP)
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
    if expand_battle_control_snapshots and paused is True:
        steps.update(
            query_battle_control_snapshot_v1_step(int(army["army_id"]))
            for army in controllable
            if _positive_native_id(army.get("army_id"))
            and int(army["army_id"]) <= 2**31 - 1
            and _army_in_active_combat(army)
        )
    if expand_battle_reinforcement_assignments and paused is True:
        steps.update(
            query_battle_reinforcement_assignment_v1_step(
                int(army["army_id"])
            )
            for army in armies
            if _positive_native_id(army.get("army_id"))
            and int(army["army_id"]) <= 2**31 - 1
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
            army_target_provinces = set(target_provinces)
            current_province_id = army.get("current_province_id")
            current_route = army.get("route_province_ids")
            same_province_route_clear_ready = bool(
                _positive_native_id(current_province_id)
                and isinstance(current_route, list)
                and current_route
            )
            stationary_contact_hold_ready = bool(
                _positive_native_id(current_province_id)
                and isinstance(current_route, list)
                and not current_route
                and "move_target_province_id" in army
                and army.get("move_target_province_id") is None
                and _army_is_known_stationary(army)
                and not _army_in_combat_or_retreat(army)
            )
            if same_province_route_clear_ready:
                army_target_provinces.add(int(current_province_id))
            for province_id in army_target_provinces:
                same_province_route_clear = bool(
                    province_id == current_province_id
                    and same_province_route_clear_ready
                )
                stationary_contact_hold = bool(
                    province_id == current_province_id
                    and stationary_contact_hold_ready
                )
                if (
                    province_id == current_province_id
                    and not same_province_route_clear
                    and not (
                        expand_route_contact_horizons
                        and stationary_contact_hold
                    )
                ):
                    continue
                if (
                    expand_move_armies
                    and (
                        same_province_route_clear
                        or province_id != army.get("move_target_province_id")
                    )
                ):
                    steps.add(move_army_step(army_id, province_id))
                if expand_preview_move_armies and not stationary_contact_hold:
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
    """Return one-shot advances backed by a fresh exact-frame proof."""
    return set(_fresh_route_contact_advance_proofs(snapshot, history))


def _fresh_route_contact_advance_proofs(
    snapshot: dict[str, object],
    history: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Bind each exact-day step to its contact-free or unavoidable proof."""
    if snapshot.get("paused") is not True:
        return {}
    hostiles = _route_contact_hostile_ids(snapshot)
    if not 0 < len(hostiles) <= 64:
        return {}
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
        return {}

    candidate_proofs: dict[str, dict[str, object]] = {}
    proofs_by_subject: dict[int, dict[str, object]] = {}
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
        try:
            normalized_horizon = normalize_route_contact_horizon(
                horizon,
                expected_subject_army_id=subject_army_id,
                expected_target_province_id=target_province_id,
                expected_hostile_army_ids=hostiles,
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError:
            continue
        subject_route = (
            normalized_horizon.get("subject_route")
            if isinstance(normalized_horizon, dict)
            else None
        )
        snapshot_route = _canonical_remaining_route(subject)
        proof_route = _canonical_timed_route(subject_route)
        active_route_matches = bool(
            isinstance(subject, dict)
            and subject.get("move_target_province_id") == target_province_id
            and snapshot_route
            and snapshot_route[-1] == target_province_id
        )
        stationary_hold_matches = bool(
            isinstance(subject, dict)
            and subject.get("current_province_id") == target_province_id
            and "move_target_province_id" in subject
            and subject.get("move_target_province_id") is None
            and snapshot_route == []
            and _army_is_known_stationary(subject)
            and not _army_in_combat_or_retreat(subject)
        )
        proof_kind = (
            "contact_free"
            if normalized_horizon.get("one_day_contact_free") is True
            else "unavoidable_current_province_contact"
            if unavoidable_current_province_contact_in_horizon(
                normalized_horizon
            )
            else None
        )
        if not (
            isinstance(subject, dict)
            and subject.get("controllable") is True
            and (active_route_matches or stationary_hold_matches)
            and proof_route == snapshot_route
            and isinstance(subject_route, dict)
            and subject_route.get("army_id") == subject_army_id
            and subject_route.get("current_province_id")
            == subject.get("current_province_id")
            and normalized_horizon.get("status") == "available"
            and proof_kind is not None
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == native_revision
            and result.get("queried_connection_generation")
            == connection_generation
            and result.get("queried_episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            continue
        step = advance_route_contact_horizon_step(
            subject_army_id, target_province_id, hostiles
        )
        advance_proof: dict[str, object] = {
            "proof_kind": proof_kind,
            "subject_army_id": subject_army_id,
            "target_province_id": target_province_id,
            "hostile_army_ids": list(hostiles),
            "contact_horizon": normalized_horizon,
        }
        candidate_proofs[step] = advance_proof
        proofs_by_subject[subject_army_id] = advance_proof

    advances: dict[str, dict[str, object]] = {}
    for step, advance_proof in candidate_proofs.items():
        subject_army_id = int(advance_proof["subject_army_id"])
        proof_kind = advance_proof.get("proof_kind")
        normalized_horizon = advance_proof["contact_horizon"]
        if not isinstance(normalized_horizon, dict) or not (
            _route_contact_advance_scope_isolated(
                snapshot,
                subject_army_id=subject_army_id,
                contact_horizon=normalized_horizon,
                subject_proofs=proofs_by_subject,
            )
        ):
            continue
        if proof_kind == "unavoidable_current_province_contact":
            subject_route = normalized_horizon.get("subject_route")
            if not isinstance(subject_route, dict):
                continue
            contact_province_id = subject_route.get("current_province_id")
            if _predicted_contact_followup_exhausted(
                snapshot,
                history,
                subject_army_id=subject_army_id,
                contact_province_id=contact_province_id,
            ):
                continue
            prior_boundary = _adjacent_predicted_contact_boundary(
                snapshot,
                history,
                subject_army_id=subject_army_id,
                contact_province_id=contact_province_id,
            )
            if prior_boundary is not None:
                advance_proof.update(
                    {
                        "strict_endpoint_followup": True,
                        "prior_contact_boundary": prior_boundary,
                    }
                )
        advances[step] = advance_proof
    return advances


def _adjacent_predicted_contact_boundary(
    snapshot: dict[str, object],
    history: list[dict[str, object]],
    *,
    subject_army_id: int,
    contact_province_id: object,
) -> dict[str, object] | None:
    """Bind the next exact day to the latest surviving endpoint marker."""
    date_raw = snapshot.get("date_raw")
    episode_run_id = snapshot.get("episode_run_id")
    if (
        isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not isinstance(episode_run_id, str)
        or not episode_run_id
        or not _positive_native_id(contact_province_id)
    ):
        return None

    # Use the complete surviving branch, not the post-restore slice.  A
    # checkpoint taken after the boundary preserves its marker when restore
    # truncates history to the checkpoint history_index; hiding everything
    # before the restore row would incorrectly grant another boundary day.
    for row in reversed(history):
        command, result = _effective_native_history_entry(row)
        if not is_life_advance_step(command):
            continue
        if row.get("ok") is not True or not isinstance(result, dict):
            return None
        parsed = parse_advance_route_contact_horizon_step(command)
        transition = result.get("contact_transition")
        if parsed is None or not isinstance(transition, dict):
            return None
        command_subject_id, _target_province_id, _hostile_army_ids = parsed
        if not (
            command_subject_id == subject_army_id
            and transition.get("status") == "predicted_only"
            and transition.get("postcondition")
            == "predicted_contact_boundary_reached"
            and transition.get("contact_observed") is False
            and transition.get("proof_kind")
            == "unavoidable_current_province_contact"
            and transition.get("episode_run_id") == episode_run_id
            and transition.get("subject_army_id") == subject_army_id
            and transition.get("contact_province_id") == contact_province_id
            and transition.get("ending_date_raw") == date_raw
            and result.get("ending_date_raw") == date_raw
        ):
            return None
        return copy.deepcopy(transition)
    return None


def _predicted_contact_followup_exhausted(
    snapshot: dict[str, object],
    history: list[dict[str, object]],
    *,
    subject_army_id: int,
    contact_province_id: object,
) -> bool:
    """Refuse a third exact day after a strict follow-up ended RED."""
    date_raw = snapshot.get("date_raw")
    episode_run_id = snapshot.get("episode_run_id")
    if (
        isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not isinstance(episode_run_id, str)
        or not episode_run_id
    ):
        return False
    for row in reversed(history):
        command, result = _effective_native_history_entry(row)
        if not is_life_advance_step(command):
            continue
        parsed = parse_advance_route_contact_horizon_step(command)
        followup = (
            result.get("contact_followup")
            if isinstance(result, dict)
            else None
        )
        return bool(
            row.get("ok") is False
            and parsed is not None
            and parsed[0] == subject_army_id
            and isinstance(followup, dict)
            and followup.get("status")
            in {
                "pending_strong_transition",
                "exhausted_without_strong_transition",
            }
            and followup.get("episode_run_id") == episode_run_id
            and followup.get("subject_army_id") == subject_army_id
            and followup.get("ending_date_raw") == date_raw
        )
    return False


def _unavoidable_contact_transition_postcondition(
    starting: dict[str, object],
    ending: dict[str, object],
    *,
    proof: dict[str, object],
    strong_only: bool = False,
) -> dict[str, object] | None:
    """Require an observed game-state transition after the exact contact day."""
    subject_army_id = proof.get("subject_army_id")
    hostile_army_ids = proof.get("hostile_army_ids")
    if (
        isinstance(subject_army_id, bool)
        or not isinstance(subject_army_id, int)
        or subject_army_id <= 0
        or not isinstance(hostile_army_ids, list)
        or any(not _positive_native_id(value) for value in hostile_army_ids)
        or ending.get("paused") is not True
    ):
        return None
    starting_date_raw = starting.get("date_raw")
    ending_date_raw = ending.get("date_raw")
    if (
        isinstance(starting_date_raw, bool)
        or not isinstance(starting_date_raw, int)
        or isinstance(ending_date_raw, bool)
        or not isinstance(ending_date_raw, int)
        or not starting_date_raw <= ending_date_raw <= starting_date_raw + 24
    ):
        return None

    base = {
        "status": "observed",
        "proof_kind": "unavoidable_current_province_contact",
        "subject_army_id": subject_army_id,
        "starting_date_raw": starting_date_raw,
        "ending_date_raw": ending_date_raw,
    }
    if (
        ending.get("one_life_terminal") is True
        or ending.get("played_character_alive") is False
    ):
        return {**base, "postcondition": "episode_terminal"}

    starting_wars = starting.get("active_wars")
    ending_wars = ending.get("active_wars")
    starting_war_ids = {
        int(war["war_id"])
        for war in (starting_wars if isinstance(starting_wars, list) else [])
        if isinstance(war, dict) and _positive_native_id(war.get("war_id"))
    }
    ending_war_ids = {
        int(war["war_id"])
        for war in (ending_wars if isinstance(ending_wars, list) else [])
        if isinstance(war, dict) and _positive_native_id(war.get("war_id"))
    }
    if ending_war_ids != starting_war_ids:
        return {
            **base,
            "postcondition": "active_war_set_changed",
            "starting_war_ids": sorted(starting_war_ids),
            "ending_war_ids": sorted(ending_war_ids),
        }

    subject = _army_by_id(ending, subject_army_id)
    if not isinstance(subject, dict):
        return {**base, "postcondition": "subject_army_removed"}
    if _army_in_active_combat(subject):
        return {**base, "postcondition": "active_combat_observed"}
    if _army_retreating(subject):
        return {**base, "postcondition": "retreat_observed"}
    if strong_only:
        return None

    contact_horizon = proof.get("contact_horizon")
    subject_route = (
        contact_horizon.get("subject_route")
        if isinstance(contact_horizon, dict)
        else None
    )
    conflicts = (
        contact_horizon.get("conflicts")
        if isinstance(contact_horizon, dict)
        else None
    )
    contact_province_id = (
        subject_route.get("current_province_id")
        if isinstance(subject_route, dict)
        else None
    )
    conflict_hostile_ids = {
        int(conflict["hostile_army_id"])
        for conflict in (conflicts if isinstance(conflicts, list) else [])
        if isinstance(conflict, dict)
        and conflict.get("kind") == "same_province"
        and conflict.get("province_id") == contact_province_id
        and _positive_native_id(conflict.get("hostile_army_id"))
    }

    def hostile_rows_by_id(
        snapshot: dict[str, object],
    ) -> dict[int, dict[str, object]]:
        wars = snapshot.get("active_wars")
        rows = enemy_armies_from_wars(
            [war for war in wars if isinstance(war, dict)]
            if isinstance(wars, list)
            else []
        )
        return {
            int(army["army_id"]): army
            for army in rows
            if _positive_native_id(army.get("army_id"))
        }

    starting_hostile_rows = hostile_rows_by_id(starting)
    ending_hostile_rows = hostile_rows_by_id(ending)
    starting_subject = _army_by_id(starting, subject_army_id)
    entered_contact_province_ids = [
        hostile_army_id
        for hostile_army_id in sorted(conflict_hostile_ids)
        if isinstance(starting_subject, dict)
        and _positive_native_id(contact_province_id)
        and starting_subject.get("current_province_id") == contact_province_id
        and subject.get("current_province_id") == contact_province_id
        and isinstance(starting_hostile_rows.get(hostile_army_id), dict)
        and isinstance(ending_hostile_rows.get(hostile_army_id), dict)
        and starting_hostile_rows[hostile_army_id].get("current_province_id")
        != contact_province_id
        and ending_hostile_rows[hostile_army_id].get("current_province_id")
        == contact_province_id
    ]
    if entered_contact_province_ids:
        return {
            **base,
            "postcondition": "hostile_entered_contact_province",
            "contact_province_id": contact_province_id,
            "changed_hostile_army_ids": entered_contact_province_ids,
        }

    def hostile_intent_by_id(
        snapshot: dict[str, object],
    ) -> dict[int, tuple[object, ...]]:
        return {
            int(army["army_id"]): (
                army.get("move_target_province_id"),
                tuple(army["route_province_ids"])
                if isinstance(army.get("route_province_ids"), list)
                else None,
                army.get("army_state"),
                army.get("army_state_code"),
                army.get("in_combat"),
                army.get("retreating"),
            )
            for army in hostile_rows_by_id(snapshot).values()
        }

    starting_hostiles = hostile_intent_by_id(starting)
    ending_hostiles = hostile_intent_by_id(ending)
    changed_hostile_ids = [
        hostile_army_id
        for hostile_army_id in sorted(conflict_hostile_ids)
        if ending_hostiles.get(hostile_army_id)
        != starting_hostiles.get(hostile_army_id)
    ]
    if changed_hostile_ids:
        return {
            **base,
            "postcondition": "hostile_intent_changed",
            "changed_hostile_army_ids": changed_hostile_ids,
        }
    return None


def _predicted_contact_boundary_postcondition(
    starting: dict[str, object],
    ending: dict[str, object],
    *,
    proof: dict[str, object],
) -> dict[str, object] | None:
    """Record one conservative closed-endpoint prediction without claiming contact."""
    if proof.get("strict_endpoint_followup") is True:
        return None
    subject_army_id = proof.get("subject_army_id")
    contact_horizon = proof.get("contact_horizon")
    subject_route = (
        contact_horizon.get("subject_route")
        if isinstance(contact_horizon, dict)
        else None
    )
    conflicts = (
        contact_horizon.get("conflicts")
        if isinstance(contact_horizon, dict)
        else None
    )
    starting_date_raw = starting.get("date_raw")
    ending_date_raw = ending.get("date_raw")
    horizon_start_date_raw = (
        contact_horizon.get("horizon_start_date_raw")
        if isinstance(contact_horizon, dict)
        else None
    )
    horizon_end_date_raw = (
        contact_horizon.get("horizon_end_date_raw")
        if isinstance(contact_horizon, dict)
        else None
    )
    contact_province_id = (
        subject_route.get("current_province_id")
        if isinstance(subject_route, dict)
        else None
    )
    subject_arrival_date_raws = (
        subject_route.get("arrival_date_raws")
        if isinstance(subject_route, dict)
        else None
    )
    episode_run_id = starting.get("episode_run_id")
    starting_diagnostics = starting.get("diagnostics")
    ending_diagnostics = ending.get("diagnostics")
    starting_episode_character_id = starting.get("episode_character_id")
    if (
        not _positive_native_id(subject_army_id)
        or not _positive_native_id(contact_province_id)
        or not isinstance(episode_run_id, str)
        or not episode_run_id
        or ending.get("episode_run_id") != episode_run_id
        or starting.get("map_ready") is not True
        or starting.get("paused") is not True
        or ending.get("map_ready") is not True
        or ending.get("paused") is not True
        or not _positive_native_id(starting_episode_character_id)
        or ending.get("episode_character_id") != starting_episode_character_id
        or starting.get("local_player_id") != ending.get("local_player_id")
        or not isinstance(starting_diagnostics, dict)
        or not isinstance(ending_diagnostics, dict)
        or not _positive_native_id(starting_diagnostics.get("bridge_pid"))
        or isinstance(
            starting_diagnostics.get("connection_generation"), bool
        )
        or not isinstance(
            starting_diagnostics.get("connection_generation"), int
        )
        or starting_diagnostics.get("connection_generation") <= 0
        or starting_diagnostics.get("connection_generation")
        != ending_diagnostics.get("connection_generation")
        or starting_diagnostics.get("bridge_pid")
        != ending_diagnostics.get("bridge_pid")
        or isinstance(starting_date_raw, bool)
        or not isinstance(starting_date_raw, int)
        or ending_date_raw != starting_date_raw + 24
        or horizon_start_date_raw != starting_date_raw
        or horizon_end_date_raw != ending_date_raw
        or not isinstance(conflicts, list)
        or not conflicts
        or not isinstance(subject_arrival_date_raws, list)
    ):
        return None
    starting_subject = _army_by_id(starting, int(subject_army_id))
    ending_subject = _army_by_id(ending, int(subject_army_id))
    starting_remaining_route = _canonical_remaining_route(starting_subject)
    ending_remaining_route = _canonical_remaining_route(ending_subject)
    subject_route_province_ids = (
        subject_route.get("route_province_ids")
        if isinstance(subject_route, dict)
        else None
    )
    moving_route_province_ids = (
        subject_route_province_ids
        if isinstance(subject_route_province_ids, list)
        else starting_remaining_route
    )
    moving_edge_cannot_clear = bool(
        isinstance(starting_subject, dict)
        and isinstance(ending_subject, dict)
        and isinstance(moving_route_province_ids, list)
        and moving_route_province_ids
        and len(subject_arrival_date_raws) == len(moving_route_province_ids)
        and not isinstance(subject_arrival_date_raws[0], bool)
        and isinstance(subject_arrival_date_raws[0], int)
        and subject_arrival_date_raws[0] > horizon_end_date_raw
        and starting_subject.get("move_target_province_id")
        == proof.get("target_province_id")
        and ending_subject.get("move_target_province_id")
        == proof.get("target_province_id")
        and bool(starting_remaining_route)
        and ending_remaining_route == starting_remaining_route
    )
    stationary_hold = bool(
        isinstance(starting_subject, dict)
        and isinstance(ending_subject, dict)
        and subject_route_province_ids == []
        and subject_arrival_date_raws == []
        and proof.get("target_province_id") == contact_province_id
        and starting_subject.get("move_target_province_id") is None
        and ending_subject.get("move_target_province_id") is None
        and starting_remaining_route == []
        and ending_remaining_route == []
    )
    if not (
        isinstance(starting_subject, dict)
        and isinstance(ending_subject, dict)
        and starting_subject.get("controllable") is True
        and ending_subject.get("controllable") is True
        and starting_subject.get("current_province_id") == contact_province_id
        and ending_subject.get("current_province_id") == contact_province_id
        and isinstance(starting_remaining_route, list)
        and (moving_edge_cannot_clear or stationary_hold)
        and not _army_in_active_combat(starting_subject)
        and not _army_retreating(starting_subject)
        and not _army_in_active_combat(ending_subject)
        and not _army_retreating(ending_subject)
    ):
        return None
    if not all(
        isinstance(conflict, dict)
        and conflict.get("kind") == "same_province"
        and conflict.get("province_id") == contact_province_id
        and _positive_native_id(conflict.get("hostile_army_id"))
        and conflict.get("overlap_start_date_raw") == ending_date_raw
        and conflict.get("overlap_end_date_raw") == ending_date_raw
        for conflict in conflicts
    ):
        return None
    conflict_hostile_army_ids = sorted(
        {int(conflict["hostile_army_id"]) for conflict in conflicts}
    )
    return {
        "status": "predicted_only",
        "proof_kind": "unavoidable_current_province_contact",
        "postcondition": "predicted_contact_boundary_reached",
        "contact_observed": False,
        "episode_run_id": episode_run_id,
        "subject_army_id": int(subject_army_id),
        "contact_province_id": int(contact_province_id),
        "conflict_hostile_army_ids": conflict_hostile_army_ids,
        "starting_date_raw": starting_date_raw,
        "ending_date_raw": ending_date_raw,
    }


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
    snapshot: dict[str, object],
    *,
    subject_army_id: int,
    contact_horizon: dict[str, object],
    subject_proofs: dict[int, dict[str, object]] | None = None,
) -> bool:
    """Fail closed when one subject proof would advance another risky army."""
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return False
    for army in controllable_armies(
        [row for row in armies if isinstance(row, dict)]
    ):
        army_id = army.get("army_id")
        if army_id == subject_army_id:
            continue
        if _army_in_combat_or_retreat(army):
            return False
        route = _canonical_remaining_route(army)
        target_province_id = army.get("move_target_province_id")
        if route and _positive_native_id(target_province_id):
            if (
                route[-1] == target_province_id
                and _active_route_is_geometrically_safe_in_horizon(
                    army, contact_horizon
                )
            ):
                continue
            sibling_proof = (
                subject_proofs.get(int(army_id))
                if isinstance(subject_proofs, dict)
                and _positive_native_id(army_id)
                else None
            )
            if _contact_free_sibling_proof_matches_conjunction(
                sibling_proof,
                army=army,
                reference_horizon=contact_horizon,
            ):
                continue
            return False
        if (
            route is None
            or "move_target_province_id" not in army
            or target_province_id is not None
            or route
            or not _army_is_known_stationary(army)
        ):
            return False
        province_id = army.get("current_province_id")
        if not _positive_native_id(province_id):
            return False
        try:
            contact_free = stationary_province_contact_free_in_horizon(
                contact_horizon, int(province_id)
            )
        except ValueError:
            return False
        if not contact_free:
            return False
    return True


def _contact_free_sibling_proof_matches_conjunction(
    proof: object,
    *,
    army: dict[str, object],
    reference_horizon: dict[str, object],
) -> bool:
    if not isinstance(proof, dict) or proof.get("proof_kind") != "contact_free":
        return False
    horizon = proof.get("contact_horizon")
    if not isinstance(horizon, dict):
        return False
    return bool(
        proof.get("subject_army_id") == army.get("army_id")
        and proof.get("target_province_id")
        == army.get("move_target_province_id")
        and horizon.get("one_day_contact_free") is True
        and horizon.get("date_raw") == reference_horizon.get("date_raw")
        and horizon.get("snapshot_revision")
        == reference_horizon.get("snapshot_revision")
        and horizon.get("horizon_start_date_raw")
        == reference_horizon.get("horizon_start_date_raw")
        and horizon.get("horizon_end_date_raw")
        == reference_horizon.get("horizon_end_date_raw")
        and horizon.get("hostile_army_ids")
        == reference_horizon.get("hostile_army_ids")
        and horizon.get("hostile_routes")
        == reference_horizon.get("hostile_routes")
    )


def _active_route_is_geometrically_safe_in_horizon(
    army: dict[str, object],
    contact_horizon: dict[str, object],
) -> bool:
    """Audit a non-subject active route against the proof's hostile scope."""
    route = _canonical_remaining_route(army)
    current_province_id = army.get("current_province_id")
    target_province_id = army.get("move_target_province_id")
    state = army.get("army_state")
    state_code = army.get("army_state_code")
    known_active_state = bool(
        isinstance(state, str)
        and state.casefold() in {"regular", "sieging", "moving", "embarked"}
        or not isinstance(state, str)
        and isinstance(state_code, int)
        and not isinstance(state_code, bool)
        and state_code in {1, 3, 4, 7}
    )
    if not (
        known_active_state
        and route
        and _positive_native_id(current_province_id)
        and _positive_native_id(target_province_id)
        and route[-1] == target_province_id
    ):
        return False
    try:
        current_province_contact_free = (
            stationary_province_contact_free_in_horizon(
                contact_horizon, int(current_province_id)
            )
        )
    except ValueError:
        return False
    if not current_province_contact_free:
        return False
    hostile_routes = contact_horizon.get("hostile_routes")
    hostile_ids = contact_horizon.get("hostile_army_ids")
    if not (
        isinstance(hostile_routes, list)
        and isinstance(hostile_ids, list)
        and len(hostile_routes) == len(hostile_ids)
        and hostile_routes
    ):
        return False

    route_provinces = set(route)
    route_edges = set(zip(route, route[1:]))
    for hostile_route in hostile_routes:
        if not isinstance(hostile_route, dict):
            return False
        hostile_current = hostile_route.get("current_province_id")
        hostile_remaining = _canonical_timed_route(hostile_route)
        if not (
            _positive_native_id(hostile_current)
            and isinstance(hostile_remaining, list)
        ):
            return False
        if hostile_current in route_provinces:
            return False
        if not hostile_remaining:
            continue
        if (
            hostile_remaining[-1] in route_provinces
            or hostile_remaining[0] == route[0]
            or route_provinces.intersection(hostile_remaining)
        ):
            return False
        hostile_edges = set(zip(hostile_remaining, hostile_remaining[1:]))
        if any(
            (destination, origin) in hostile_edges
            for origin, destination in route_edges
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


def _termination_cache_row(
    snapshot: dict[str, object], field: str, war_id: int
) -> dict[str, object] | None:
    rows = snapshot.get(field)
    matches = [
        row
        for row in (rows if isinstance(rows, list) else [])
        if isinstance(row, dict) and row.get("war_id") == war_id
    ]
    return matches[0] if len(matches) == 1 else None


def _claim_cb_white_peace_readiness(
    snapshot: dict[str, object], war_id: int
) -> tuple[bool, str, dict[str, object]]:
    """Validate the owner-authorized narrow claim_cb white-peace slice."""
    if snapshot.get("paused") is not True:
        return False, "snapshot_not_paused", {}
    war = _war_by_id(snapshot, war_id)
    if not isinstance(war, dict):
        return False, "war_not_active", {}
    options = _termination_cache_row(
        snapshot, "war_termination_options", war_id
    )
    terms = _termination_cache_row(
        snapshot, "war_termination_terms", war_id
    )
    if not isinstance(options, dict):
        return False, "termination_options_missing", {}
    if not isinstance(terms, dict):
        return False, "termination_terms_v1_missing", {"options": options}
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    expected_binding = {
        "queried_snapshot_id": snapshot.get("snapshot_id"),
        "queried_revision": snapshot.get("revision"),
        "queried_native_revision": snapshot.get("native_revision"),
        "queried_connection_generation": connection_generation,
        "episode_run_id": snapshot.get("episode_run_id"),
    }
    if any(
        row.get(key) != expected
        for row in (options, terms)
        for key, expected in expected_binding.items()
    ):
        return False, "termination_evidence_not_same_frame", {}
    score = war.get("player_relative_war_score")
    duration = options.get("war_duration_days")
    option_cb = options.get("active_casus_belli_identity")
    terms_cb = terms.get("casus_belli")
    if not (
        war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score") == score
        and isinstance(score, int)
        and not isinstance(score, bool)
        and 0 <= score < 100
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration >= 365
        and options.get("active_casus_belli_present") is True
        and isinstance(option_cb, dict)
        and option_cb.get("canonical_key") == "claim_cb"
        and isinstance(terms_cb, dict)
        and terms_cb.get("canonical_key") == "claim_cb"
        and terms_cb.get("database_index")
        == option_cb.get("database_index")
        and options.get("cb_allows_white_peace") is True
    ):
        return False, "claim_cb_white_peace_base_gate_failed", {}
    raw_options = options.get("options")
    white_peace = (
        raw_options.get("white_peace")
        if isinstance(raw_options, dict)
        else None
    )
    response = (
        white_peace.get("recipient_response")
        if isinstance(white_peace, dict)
        else None
    )
    if not (
        isinstance(white_peace, dict)
        and white_peace.get("outcome") == "white_peace"
        and white_peace.get("hostage_variant") == "none"
        and white_peace.get("context_constructed") is True
        and white_peace.get("native_validator_passed") is True
        and white_peace.get("available") is True
        and isinstance(response, dict)
        and response.get("status") == "available"
        and response.get("would_accept_now") is True
    ):
        return False, "white_peace_recipient_or_validator_gate_failed", {}
    readiness = terms.get("readiness")
    played_character = snapshot.get("played_character")
    played_character_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    target_title_ids = war.get("targeted_title_ids")
    claims = terms.get("claims")
    if not (
        terms.get("status") == "available"
        and isinstance(readiness, dict)
        and readiness.get("ready") is True
        and terms.get("claimant_character_id") == played_character_id
        and isinstance(target_title_ids, list)
        and bool(target_title_ids)
        and terms.get("target_title_ids") == target_title_ids
        and isinstance(claims, list)
        and len(claims) == len(target_title_ids)
        and all(
            isinstance(claim, dict)
            and claim.get("title_id") == title_id
            and claim.get("present") is True
            for claim, title_id in zip(claims, target_title_ids, strict=True)
        )
    ):
        return False, "claim_disposition_v1_gate_failed", {}
    return True, "ready", {
        "war": war,
        "options": options,
        "terms": terms,
        "white_peace": white_peace,
    }


def _white_peace_proposal_cooldown(
    history: list[dict[str, object]],
    *,
    war_id: int,
    current_date_raw: object,
    episode_run_id: object,
) -> dict[str, object] | None:
    if isinstance(current_date_raw, bool) or not isinstance(
        current_date_raw, int
    ):
        return {"status": "invalid_current_date"}
    step = offer_white_peace_step(war_id)
    for row in reversed(history):
        if row.get("command") != step or row.get("ok") is not True:
            continue
        result = row.get("result")
        action = (
            result.get("war_termination_result")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(action, dict)
            and action.get("war_id") == war_id
            and action.get("outcome") == "white_peace"
            and action.get("episode_run_id") == episode_run_id
            and action.get("status") in {"submitted_pending", "applied"}
        ):
            continue
        submitted_date_raw = action.get("submitted_date_raw")
        if isinstance(submitted_date_raw, bool) or not isinstance(
            submitted_date_raw, int
        ):
            return {"status": "malformed_submission_history"}
        elapsed_raw = current_date_raw - submitted_date_raw
        if elapsed_raw < _WHITE_PEACE_PROPOSAL_COOLDOWN_RAW:
            return {
                "status": "cooldown",
                "submitted_date_raw": submitted_date_raw,
                "elapsed_raw": elapsed_raw,
                "remaining_raw": (
                    _WHITE_PEACE_PROPOSAL_COOLDOWN_RAW - elapsed_raw
                ),
                "history_index": row.get("index"),
            }
        return None
    return None


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


def _termination_options_war_identity_diff(
    options: dict[str, object], war: dict[str, object]
) -> dict[str, dict[str, object]]:
    fields = (
        "war_id",
        "player_side",
        "player_is_primary_war_leader",
        "player_relative_war_score",
    )
    return {
        field: {
            "query": options.get(field),
            "active_war": war.get(field),
        }
        for field in fields
        if options.get(field) != war.get(field)
    }


def _war_termination_query_mismatch_result(
    *,
    step: str,
    stage: str,
    requested_war_id: int,
    query_sequence: int,
    snapshot: dict[str, object],
    identity_diff: dict[str, dict[str, object]],
) -> dict[str, object]:
    diagnostics = snapshot.get("diagnostics")
    return {
        "step": step,
        "status": "postcondition_failed",
        "accepted": True,
        "query_sequence": query_sequence,
        "war_termination_query_mismatch": {
            "stage": stage,
            "requested_war_id": requested_war_id,
            "snapshot_binding": {
                "snapshot_id": snapshot.get("snapshot_id"),
                "revision": snapshot.get("revision"),
                "native_revision": snapshot.get("native_revision"),
                "connection_generation": (
                    diagnostics.get("connection_generation")
                    if isinstance(diagnostics, dict)
                    else None
                ),
                "episode_run_id": snapshot.get("episode_run_id"),
            },
            "identity_diff": copy.deepcopy(identity_diff),
        },
    }


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
        and anchor.get("command") in _CHECKPOINT_ANCHOR_STEPS
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


def _valid_pending_interaction_id(value: object) -> bool:
    try:
        normalize_pending_interaction_id(value)
    except ValueError:
        return False
    return True


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
    try:
        instance_id = normalize_pending_interaction_id(instance_id)
    except ValueError as error:
        raise ValueError(
            "native pending_character_interaction is malformed"
        ) from error
    if (
        isinstance(sender_character_id, bool)
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


def _timeline_speed(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > 5
    ):
        raise ValueError(f"{name} must be an integer from 1 through 5")
    return value


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
