#!/usr/bin/env python3
"""Run isolated CK3 1.19.0.6 live acceptance for ZhongGuo 361 Style."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import ctypes
from ctypes import wintypes
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path

import run_acceptance as acceptance
import build_mod_zhongguo_style_release as release
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated
import kaishek_preflight
import paradox_legal_consent as legal_consent
from zg361_phase2_product_projection import (
    ProductProjectionError,
    materialize_projection,
)


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "mod_zhongguo_style"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
PHASE2_WORKFORCE_ACTION_FIXTURE_SOURCE = (
    ROOT / "tools" / "fixtures" / "zg361_phase2_workforce_action"
)
AUTOPLAYER_SOURCE = ROOT / "ck3_autonomous_player" / "src"
TITLE_NAVIGATION_RESEARCH = (
    ROOT / "ck3_autonomous_player" / "native_bridge" / "research"
)
for import_root in (AUTOPLAYER_SOURCE, TITLE_NAVIGATION_RESEARCH):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.loaded_feature_manifest_contract import (
    QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
    QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
)
from xar_autoplayer.bridge.zhongguo_b2_pip_snapshot_contract import (
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_B2_PIP_CASE_KIND_V1,
    ZhongguoB2PipQueryV1,
    normalize_zhongguo_b2_pip_snapshot_v1_response,
)
from xar_autoplayer.bridge.zhongguo_ai_owned_case_snapshot_contract import (
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1,
    ZHONGGUO_AI_OWNED_CASE_KIND_V1,
    ZhongguoAiOwnedCaseQueryV1,
    normalize_zhongguo_ai_owned_case_snapshot_v1_response,
)
from xar_autoplayer.bridge.zhongguo_ai_owned_case_action import (
    run_zhongguo_ai_owned_case_background_action,
)
from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_incident_snapshot_contract import (
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_INCIDENT_KIND_V1,
    ZhongguoIncidentQueryV1,
    normalize_zhongguo_incident_snapshot_v1_response,
)
from xar_autoplayer.bridge.zhongguo_incident_action_cell import (
    IncidentActionCellError,
    run_incident_xyz_gameplay_action_cell,
)
from zg361_phase2_b2_action_cell import (
    B2_PIP_EVENT_DEFINITION_KEY,
    B2PipActionCellError,
    run_b2_pip_gameplay_action_cell,
)
from zg361_phase2_b2_checkpoint_matrix import (
    B2PrechoiceInspectionError,
    B2SameCheckpointMatrixError,
    inspect_b2_pip_prechoice,
    run_b2_same_checkpoint_matrix,
)
from zg361_phase2_b3_manager_governance_action_cell import (
    B3ManagerGovernanceActionCellError,
    run_b3_manager_governance_gameplay_action_cell,
)
from zg361_phase2_loader_stage import (
    LoaderStageError,
    wait_for_phase2_seed_loader_stage,
)
from zhongguo_phase2_workforce_action import (
    M360_EVENT_DEFINITION_KEY,
    run_m360_action_and_postcondition,
    select_typed_fixture_player_transition,
)
from xar_autoplayer.bridge.zhongguo_workforce_collective_snapshot_contract import (
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_WORKFORCE_COLLECTIVE_CASE_KIND_V1,
    ZhongguoWorkforceCollectiveQueryV1,
    normalize_zhongguo_workforce_collective_snapshot_v1_response,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_state_contract import (
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_action_batch import (
    run_zhongguo_scoreboard_action_batch,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_action_cell import (
    run_zhongguo_scoreboard_action_cell,
)
from xar_autoplayer.bridge.zhongguo_result_case_snapshot_contract import (
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_RESULT_CASE_KIND_V1,
)
from xar_autoplayer.environment import (
    EnvironmentSpec,
    ck3_process_inventory,
    make_spec,
)
from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
from xar_autoplayer.native_session import (
    NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS,
    native_session,
)
from xar_autoplayer.runtime import (
    NativeBridgeLaunchConfig,
    launch as launch_native_ck3,
    native_bridge_launch_config_from_environment,
    stop_tracked,
    validate_native_bridge_launch_config,
)

import run_title_map_navigation_v1_live_acceptance as title_navigation_live

PROMO_TOOLS_DIRECTORY = SOURCE / "tools"
if str(PROMO_TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(PROMO_TOOLS_DIRECTORY))
TOOLS_DIRECTORY = ROOT / "tools"
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

from zhongguo_phase2_promo_producer import (
    Phase2PromoCaptureContext,
    Phase2PromoProducerUnavailable,
    Phase2PromoVisualPrimitive,
    make_managed_phase2_promo_capture_producer,
    phase2_promo_producer_typed_error_payload,
)
import zg361_phase2_loaded_seed_live as loaded_seed_live
from zhongguo_phase2_visual_handlers import (
    CompositePhase2SpanDriver,
    ENDGAME_HANDLER,
    PROJECTS_HANDLER,
    PROMOTION_HANDLER,
    Phase2VisualHandlerAdapter,
    Phase2VisualHandlerError,
)
from zhongguo_phase2_capture_choreography import PHASE2_CAPTURE_SCENARIOS
from zhongguo_phase2_event_choreography import (
    Phase2EventChoreographer,
    Phase2EventChoreographyError,
    Phase2EventSequencePlan,
    SequencedPhase2SpanDriver,
    phase2_event_sequence_plan,
)
from zhongguo_phase2_source_checkpoint_provider import (
    CHECKPOINT_REQUIRED_HANDLERS,
    Phase2SourceCheckpoint,
    Phase2SourceCheckpointError,
    Phase2SourceCheckpointProvider,
)

import promo_real_character_contract as real_characters

# CK3 writes into its -userdir. Keep both the evidence bundle and complete
# writable profile durable but outside the repository/protected real profile.
RUNS_ROOT = ROOT.parent / f"{ROOT.name}_process_assets" / "zg361" / "runs"
PHASE2_SEED_CONTRACT_PATH = ROOT / "tools" / "zg361_phase2_seed_contract.json"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXE_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
NATIVE_BRIDGE_MODE = "native-headless"
NATIVE_TITLE_COMMAND_TIMEOUT_S = 30.0
NATIVE_TITLE_READINESS_TIMEOUT_S = 60.0
NATIVE_LOADER_READINESS_TIMEOUT_S = 300.0
NATIVE_LOADER_STABLE_OBSERVATIONS = 3
PHASE2_PAUSED_READINESS_TIMEOUT_S = 300.0
PHASE2_B2_PROMPT_TIMEOUT_S = 120.0
# Native ``date_raw`` is measured in hours.  The focused B2 route permits at
# most seven game days while waiting for the exact result/PIP event identity.
CK3_DATE_RAW_HOURS_PER_DAY = 24
PHASE2_B2_EVENT_WAIT_MAX_DAYS = 7
PHASE2_SUPERVISOR_READINESS_TIMEOUT_S = 300.0
PHASE2_SUPERVISOR_RUNTIME_TIMEOUT_S = 21600.0
# The native bridge can bind before the CK3 window has a capturable desktop
# surface.  Keep the legal-consent inspection bounded, but give the window a
# short settle period before treating a transient ImageGrab failure as RED.
PHASE2_LEGAL_CONSENT_SCREEN_READY_TIMEOUT_S = 15.0
PHASE2_LEGAL_CONSENT_SCREEN_RETRY_INTERVAL_S = 0.25
LOADER_ERROR_LOG_MINIMUM_QUIET_S = 16.0
LOADER_ERROR_LOG_TIMEOUT_S = 45.0
NATIVE_TITLE_PIPE_PREFIX = r"\\.\pipe\xar_ck3_bridge_zg361_"
PHASE2_B3_MANAGER_SELECTOR_KIND = (
    "zg361-bounded-ai-direct-manager-selection-v1"
)
EXPECTED_PLAYER_HISTORY_ID = real_characters.MANAGER_HISTORY_ID
# The phase-two bootstrap resumes the real historical official selected by the
# phase-one personal-result flow, not the Song emperor used by the clean promo.
# Keep the two identities separate: conflating the saved event root with its
# saved reviewing-superior scope previously bound CharacterID 32904 to the
# wrong history character.
PHASE2_SEED_PLAYER_HISTORY_ID = "han_6875"
EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS = tuple(
    real_characters.REVIEWED_OFFICIAL_CONTRACT
)
EXPECTED_HISTORICAL_COHORT_HISTORY_IDS = tuple(
    real_characters.HISTORICAL_COHORT_CONTRACT
)
HISTORICAL_TARGET_DATA_MARKER_PREFIX = real_characters.TARGET_DATA_MARKER_PREFIX
HISTORICAL_TARGET_PASS_MARKER = real_characters.TARGET_PASS_MARKER
PROMO_CLEAN_SPANS = (
    "calibration",
    "managed_scoreboard",
    "policy_cockpit",
    "jingcha_mandate",
    "free_jingcha_planner",
    "superior_assigned_325",
    "received_scoreboard_with_325",
    "policy_card_001",
    "policy_card_007",
    "policy_card_020",
    "policy_card_022",
    "policy_card_026",
    "policy_card_361",
)
# Phase two has a separate visual producer contract.  These IDs intentionally
# do not alias the phase-one spans above: a phase-one take must never be
# relabelled as sequel footage.  The future producer is required to call
# ``PromoRecorder.clean_hold`` with these exact chapter IDs after each real
# phase-two gameplay surface is visible and clean.
PHASE2_PROMO_CAPTURE_MODE = "zhongguo-361-phase2"
PHASE2_PROMO_CAPTURE_CONTRACT_VERSION = 1
PHASE2_PROMO_CAPTURE_PRODUCER_ID = "zhongguo-361-phase2-visual-producer-v1"
PHASE2_PROMO_CLEAN_SPANS = (
    "phase2_fact_quota_calibration",
    "phase2_receipt_appeal_pip",
    "phase2_manager_governance",
    "phase2_promotion_compensation",
    "phase2_hc_workforce",
    "phase2_projects_metrics",
    "phase2_incidents_operations",
    "phase2_cross_cycle_endgame",
)
# Keep a semantic producer key beside each chapter ID.  The keys are an
# explicit interface for the eventual gameplay choreography; they are not
# aliases for any old visual span.
PHASE2_PROMO_CAPTURE_SPAN_MAP = (
    ("phase2_fact_quota_calibration", "facts-quota-calibration"),
    ("phase2_receipt_appeal_pip", "receipts-appeals-pip"),
    ("phase2_manager_governance", "manager-governance"),
    ("phase2_promotion_compensation", "promotion-compensation"),
    ("phase2_hc_workforce", "hc-workforce"),
    ("phase2_projects_metrics", "projects-metrics"),
    ("phase2_incidents_operations", "incidents-operations"),
    ("phase2_cross_cycle_endgame", "cross-cycle-endgame"),
)


def _strict_contract_equal(expected: object, actual: object) -> bool:
    """Compare phase-two contract JSON with exact scalar/container types.

    Python's ordinary equality treats ``True == 1`` and ``1.0 == 1`` as
    equal.  That is not sufficient for a versioned capture hand-off: a
    producer returning a boolean or float must be rejected before any
    timeline evidence is accepted.
    """

    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():  # type: ignore[union-attr]
            return False
        return all(
            _strict_contract_equal(expected[key], actual[key])  # type: ignore[index]
            for key in expected
        )
    if isinstance(expected, list):
        if len(expected) != len(actual):  # type: ignore[arg-type]
            return False
        return all(
            _strict_contract_equal(left, right)
            for left, right in zip(expected, actual)  # type: ignore[arg-type]
        )
    return expected == actual


if set(PHASE2_PROMO_CLEAN_SPANS).intersection(PROMO_CLEAN_SPANS):
    raise RuntimeError("phase-two promo spans must be disjoint from phase-one spans")
if tuple(item[0] for item in PHASE2_PROMO_CAPTURE_SPAN_MAP) != PHASE2_PROMO_CLEAN_SPANS:
    raise RuntimeError("phase-two promo span map must follow the canonical chapter order")


@dataclass(frozen=True, slots=True)
class PromoCaptureContract:
    """Mode-specific producer contract projected into a capture timeline."""

    mode: str
    version: int
    producer_id: str
    clean_span_ids: tuple[str, ...]
    span_map: tuple[tuple[str, str], ...]

    @property
    def mark_labels(self) -> tuple[str, ...]:
        return tuple(
            label
            for span_id in self.clean_span_ids
            for label in (f"{span_id}_clean_begin", f"{span_id}_clean_end")
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "version": self.version,
            "producer_id": self.producer_id,
            "span_ids": list(self.clean_span_ids),
            "span_map": [
                {"chapter_id": chapter_id, "producer_key": producer_key}
                for chapter_id, producer_key in self.span_map
            ],
        }


LEGACY_PROMO_CAPTURE_CONTRACT = PromoCaptureContract(
    mode="zhongguo-361-phase1",
    version=1,
    producer_id="zhongguo-361-legacy-visual-producer-v1",
    clean_span_ids=PROMO_CLEAN_SPANS,
    span_map=tuple((span_id, span_id) for span_id in PROMO_CLEAN_SPANS),
)
PHASE2_PROMO_CAPTURE_CONTRACT = PromoCaptureContract(
    mode=PHASE2_PROMO_CAPTURE_MODE,
    version=PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    producer_id=PHASE2_PROMO_CAPTURE_PRODUCER_ID,
    clean_span_ids=PHASE2_PROMO_CLEAN_SPANS,
    span_map=PHASE2_PROMO_CAPTURE_SPAN_MAP,
)
PROMO_FORBIDDEN_VISIBLE_TEXT = (
    "决议和大型工程",
    "361制实机验收",
    "开始361制实机验收",
    "验收上司给我的绩效",
    "验收免费京察规划器",
    "演示政策卡",
    "演示触发器",
    "切换至宋帝并开考",
    "切换受考",
    "发出京察召集令",
    "打开此卡",
    "ZhongGuo 361 live acceptance",
    "Verify My Superior's Rating",
    "Verify the Free Jingcha Planner",
    "Promo Policy Card",
    "Switch to Song and begin review",
    "Open this card",
    "ZGA",
    "zga_",
    "zga.",
)
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_S = 300
PRODUCT_OUTER = "zg361_acceptance.mod"
FIXTURE_OUTER = "zga_acceptance_fixture.mod"
PHASE2_WORKFORCE_ACTION_FIXTURE_OUTER = (
    "zga_phase2_workforce_action_fixture.mod"
)
PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT = "zga_phase2_workforce.1"
PHASE2_WORKFORCE_SWITCH_BACK_EVENT = "zga_phase2_workforce.3"
PHASE2_WORKFORCE_OWNER_SCOPE = "zga_phase2_workforce_owner"
PHASE2_WORKFORCE_SUBJECT_SCOPE = "zga_phase2_workforce_subject"
PROJECT_TOKENS = ("zg361", "zga_acceptance", "zga_", "zga.")
DUPLICATE_PATTERNS = (
    "there is more than one",
    "using most recent",
    "duplicate definition",
    "duplicate key",
    "already defined",
    "already registered",
)
LOADER_ERROR_SIGNATURES = {
    "parser_or_script": (
        "parse error",
        "parser error",
        "failed to parse",
        "could not parse",
        "unexpected token",
        "unexpected keyword",
        "script system error",
        "expected opening bracket",
        "invalid syntax",
        "unknown trigger",
        "unknown effect",
        "error in trigger",
        "error in effect",
        "invalid scope",
    ),
    "database_or_duplicate": DUPLICATE_PATTERNS
    + (
        "invalid database object",
        "database error",
    ),
    "localization": (
        "localization error",
        "localisation error",
        "missing localization",
        "missing localisation",
    ),
    "gui": (
        "gui error",
        "widget error",
        "failed to load gui",
        "failed to load widget",
    ),
    "loader": (
        "failed to load",
        "could not load",
        "error loading",
    ),
}
REQUIRED_FIXTURE_MARKERS = (
    "ZGA: TEST BEGIN zg361",
    "ZGA: TEST PASS exact_build_song_emperor",
    "ZGA: TEST PASS song_independent_sample",
    "ZGA: TEST PASS song_direct_governors_at_least_three",
    "ZGA: TEST PASS non_independent_celestial_liege_entry",
    "ZGA: TEST PASS switched_to_song_emperor",
    "ZGA: TEST PASS player_song_review_entry",
    "ZGA: TEST PASS bootstrap_snapshot_prepared_by_product",
    "ZGA: TEST PASS bootstrap_first_review_strict_7_14_2",
    "ZGA: TEST PASS player_calibration_pending",
    "ZGA: TEST PASS calibration_c_all_newcomer_noop",
    "ZGA: TEST PASS calibration_c_mixed_newcomer_atomic_swap",
    "ZGA: TEST PASS pending_review_idempotent",
    "ZGA: TEST PASS grade_325_fourfold_penalty",
    "ZGA: TEST PASS phase2_case_facts_and_quota_reason_frozen",
    "ZGA: TEST PASS phase2_delivery_and_receipt_idempotent",
    "ZGA: TEST PASS appeal_exact_fixed_refund_and_salary_stop",
    "ZGA: TEST PASS appeal_refund_idempotent",
    "ZGA: MECHANISM BATCH BEGIN 361",
    "ZGA: MECHANISM LEDGER PASS",
    "ZGA: MECHANISM IDEMPOTENCE PASS",
    "ZGA: MECHANISM BATCH DONE 361",
    "ZGA: TEST PASS scoreboard_header_and_rows",
    "ZGA: TEST PASS three_grade_counts",
    "ZGA: TEST PASS bootstrap_first_review_result_7_14_2",
    "ZGA: TEST DONE zg361",
    "ZGA: TEST PASS historical_song_direct_whitelist_complete",
    "ZGA: TEST PASS generated_city_officials_excluded_from_provenance",
    "ZGA: TEST PASS recording_health_guard_applied",
)
REQUIRED_LATE_FIXTURE_MARKERS = (
    "ZGA: TEST PASS personal_result_target_selected_from_prior_historical_assessor_tail",
    "ZGA: TEST PASS personal_result_target_can_assess_others",
    HISTORICAL_TARGET_PASS_MARKER,
    "ZGA: TEST PASS personal_result_target_projected_bottom_two",
    "ZGA: TEST PASS post_baseline_newcomer_prepared",
    "ZGA: TEST PASS post_baseline_newcomer_protected_from_325",
    "ZGA: TEST PASS recording_health_guard_removed_before_switch",
    "ZGA: TEST PASS phase2_player_325_prepared_without_early_penalty",
    "ZGA: TEST PASS phase2_refused_notice_witnessed_and_settled",
    "ZGA: TEST PASS phase2_refused_delivery_receipt_idempotent",
)
REQUIRED_PRODUCT_MARKERS = {
    "ZG361: annual review tick": 2,
    "ZG361: scoreboard published": 1,
    "ZG361M: REFERENCE CHARTER COMPLETE 361": 2,
}
REQUIRED_LATE_PRODUCT_MARKERS = {
    # The real post-baseline newcomer is created only after the first review,
    # GUI audit, Jingcha mandate, and personal-result handoff.  Requiring this
    # during the first stream.validate() aborts a correct run before the marker
    # can exist.
    "ZG361: newcomer enters first review with 3.25 protection": 1,
}
SOURCE_ONLY_RUNTIME_ROOTS = {
    "artifacts",
    "docs",
    "fixtures",
    "images",
    "promo",
    "tools",
    "workshop",
}
PROMO_POLICY_CARDS = (
    (1, "演示政策卡 #001", "KPI 分项证据单", "建立分项证据单"),
    (7, "演示政策卡 #007", "背靠背 360 邀评", "只邀请有真实协作"),
    (20, "演示政策卡 #020", "晋升包与跨部门答辩", "用冻结治理成果"),
    (22, "演示政策卡 #022", "软 HC / 编制预算", "按团队成果"),
    (26, "演示政策卡 #026", "真实贡献 / 上司可见度双账", "分别冻结真实贡献"),
    (361, "演示政策卡 #361", "三六一绩效宪章", "锁定证据公平"),
)
PROMO_INTERRUPTION_MAX_DISMISSALS = 3
PROMO_INTERRUPTION_DEFAULT_OBSERVE_S = 1.0
PROMO_PREFERRED_PRODUCT_EVENT_OPTIONS = (
    # The punitive alternative forces every "little white rabbit" to step
    # down, mutating the real 23-person cohort before historical target
    # selection.  The retention option closes the ordinary product event
    # without manufacturing or removing a promo subject.
    ("野狗与小白兔", "宽严相济"),
    # A second consecutive 3.25 opens the real subordinate elimination event
    # after policy card 001.  Appeal can randomly purge the historical subject
    # and retirement always removes their title; the revolt branch preserves
    # the real character/title continuity while still exercising a real,
    # consequential product response.
    ("你被列入末位淘汰名单", "掀桌起兵"),
)
# CK3 character-event titles occupy this left-half lane.  The bottom-right
# pause reason may repeat the title of an event hidden behind another modal;
# it must never satisfy a "target event is visibly on top" assertion.
PROMO_EVENT_TITLE_REGION = (0.18, 0.16, 0.48, 0.32)
# The subordinate-result summary line lives inside this fixed event-body lane.
# Keep grade validation out of the top resource bar (which legitimately shows
# unrelated values such as "+3.5") and the bottom-right pause reason.
PROMO_PERSONAL_RESULT_FIELD_REGION = (0.20, 0.34, 0.42, 0.40)
PROMO_PROTECTED_EVENT_TITLES = (
    "绩效校准会议",
    "你主持的考核",
    "京察之期",
    "上司考定",
    *(event_title for _, _, event_title, _ in PROMO_POLICY_CARDS),
)
# The generated 180x44 toggle is anchored immediately left of CK3's 50-unit
# right HUD rail.  Constrain positive OCR to this normalized lane so the old
# detached {-205,165} placement cannot accidentally satisfy live acceptance.
SCOREBOARD_BUTTON_REGION = (0.86, 0.05, 0.985, 0.16)
DECISIONS_HEADER_REGION = (0.55, 0.00, 0.90, 0.13)
# CK3 acceptance is pinned to 2560x1440 and the isolated profile's UI scale.
# This normalized point is the native Decisions drawer's title-bar X.  The
# drawer is flush with the right HUD rail, so its close glyph sits near the
# screen's right edge (2460, 92 in the pinned 2560x1440 acceptance profile).
DECISIONS_CLOSE_BUTTON = (0.961, 0.064)
# The generated 1220x820 modal is centered.  Its inherited header close glyph
# is centered at (1991, 240) in the same pinned acceptance profile.  The
# backdrop probe deliberately stays far outside the panel's left edge.
SCOREBOARD_TITLE_CLOSE_BUTTON = (0.778, 0.167)
SCOREBOARD_BACKDROP_POINT = (0.050, 0.500)
SCOREBOARD_ROW_NAME_REGION = (0.30, 0.33, 0.45, 0.76)
CHARACTER_WINDOW_NAME_REGION = (0.00, 0.05, 0.38, 0.80)
# CK3's native character sidebar is 610 GUI units wide and the isolated
# profile uses 1.30 GUI scale.  Pixel inspection of the unscaled 2560x1440
# evidence frame places its inherited 30x30 close glyph at (740, 26).
# Escape does not close this sidebar reliably, so the row-link audit uses the
# product-native title-bar control directly.
CHARACTER_WINDOW_CLOSE_BUTTON = (0.2891, 0.0181)
SCOREBOARD_GENERATED_ROW_LINKS = 160
JINGCHA_PERSONAL_SWITCH_DELAY_DAYS = 90
PERSONAL_SWITCH_WAIT_TIMEOUT_S = 240.0
PERSONAL_SWITCH_SCHEDULED_MARKER = (
    "ZGA: TEST PASS personal_result_switch_scheduled"
)
WINDOWS_ENGLISH_US_KLID = "00000409"
WINDOWS_ENGLISH_US_LANGID = 0x0409
WINDOWS_ENGLISH_US_HKL = 0x04090409
WM_INPUTLANGCHANGEREQUEST = 0x0050

# Full phase-two acceptance is deliberately fail-closed.  Existing providers
# may be exercised by focused fixture-live work, but --phase2-live-batch is the
# formal all-domain batch and must not silently degrade to the old visual
# phase-one scenario while one of these requirements is absent.
PHASE2_REQUIRED_BRIDGE_CAPABILITIES = {
    "paused_snapshot": "game.state.snapshot",
    "map_ready_state": "game.state.map-ready",
    "played_character_state": "game.state.played-character",
    "active_event_state": "game.state.active-event",
    "pause_timeline": "game.command.pause-map",
    "resume_timeline": "game.command.resume-map",
    "bounded_timeline_speed": "game.command.set-speed-1",
    "event_option_action_ack": "game.command.select-event-option-N",
    "save_checkpoint": "game.command.save-checkpoint",
    "current_event_context": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    "loaded_feature_manifest": QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
    "b2_pip_snapshot": QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
    "incident_snapshot": QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    "workforce_collective_snapshot": (
        QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
    ),
    "ai_owned_case_snapshot": (
        QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
    ),
    "manager_governance_snapshot": (
        QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
    ),
    "scoreboard_state_acl": QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
    "result_case_snapshot": QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
}
PHASE2_REQUIRED_QUERY_FLAGS = {
    "b2_pip_snapshot": "zhongguo_b2_pip_snapshot_v1_query_supported",
    "incident_snapshot": "zhongguo_incident_snapshot_v1_query_supported",
    "workforce_collective_snapshot": (
        "zhongguo_workforce_collective_snapshot_v1_query_supported"
    ),
    "ai_owned_case_snapshot": (
        "zhongguo_ai_owned_case_snapshot_v1_query_supported"
    ),
    "manager_governance_snapshot": (
        "zhongguo_manager_governance_snapshot_v1_query_supported"
    ),
    "scoreboard_state_acl": (
        "zhongguo_scoreboard_state_v1_query_supported"
    ),
    "loaded_feature_manifest": "loaded_feature_manifest_v1_query_supported",
    "current_event_context": "current_event_window_context_v1_query_supported",
    "result_case_snapshot": "zhongguo_result_case_snapshot_v1_query_supported",
}
PHASE2_REQUIRED_ACTION_STEPS = {
    "pause_timeline": "pause-map",
    "resume_timeline": "resume-map",
    "bounded_timeline_speed": "set-speed-1",
    "bounded_life_advance": "life-advance",
    "save_checkpoint": "save-checkpoint",
    "loaded_feature_manifest": QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
    "result_case_snapshot": QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
}
PHASE2_B2_REQUIRED_BRIDGE_CAPABILITY_LABELS = (
    "paused_snapshot",
    "map_ready_state",
    "played_character_state",
    "active_event_state",
    "pause_timeline",
    "resume_timeline",
    "bounded_timeline_speed",
    "event_option_action_ack",
    "save_checkpoint",
    "current_event_context",
    "loaded_feature_manifest",
    "b2_pip_snapshot",
    "incident_snapshot",
)
PHASE2_B2_REQUIRED_QUERY_FLAG_LABELS = (
    "b2_pip_snapshot",
    "incident_snapshot",
    "loaded_feature_manifest",
    "current_event_context",
)
PHASE2_B2_REQUIRED_ACTION_STEP_LABELS = (
    "pause_timeline",
    "resume_timeline",
    "bounded_timeline_speed",
    "bounded_life_advance",
    "save_checkpoint",
    "loaded_feature_manifest",
)
# Provider readiness and gameplay completion are separate gates.  Every frozen
# read-only provider belongs to the capability preflight below; the missing
# named-widget action and product mutations stay explicit in
# ``PHASE2_MISSING_GAMEPLAY_ACTION_CELLS`` so they cannot make an observation
# cell GREEN claim that the whole phase-two batch is complete.
PHASE2_UNFROZEN_REQUIREMENTS: dict[str, str] = {}
# The runner-side map-entry path is now wired through a strict seed contract.
# Immutable source/provenance drift remains a pre-launch RED.  A source-tree
# hash differing from the current same-mod-ID projection is provenance, not a
# failure; the new runtime is verified by mount/manifest/snapshot after load.
PHASE2_PENDING_RUNNER_REQUIREMENTS: dict[str, str] = {}

# The registry is deliberately data-only.  Read-only cells marked ``wired``
# run in ``run_phase2_domain_query_stage``.  Action cells may have a wired
# handler while remaining ``provider_pending`` on a missing typed selector;
# the batch report therefore distinguishes runner wiring from true gameplay
# readiness.  Read-only observation is never treated as a gameplay action.
PHASE2_DOMAIN_CELL_REGISTRY: dict[str, dict[str, object]] = {
    "b2_pip_snapshot_query_matrix": {
        "implementation": "wired",
        "required_capability": QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
        "required_query_flag": (
            "zhongguo_b2_pip_snapshot_v1_query_supported"
        ),
        "observation_only": True,
        "gameplay_action_complete": True,
    },
    "incident_xyz_snapshot_query_matrix": {
        "implementation": "wired",
        "required_capability": QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
        "required_query_flag": (
            "zhongguo_incident_snapshot_v1_query_supported"
        ),
        "observation_only": True,
        "gameplay_action_complete": True,
    },
    "workforce_collective_and_three_cycle_matrix": {
        "implementation": "wired",
        "required_capability": (
            QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
        ),
        "required_query_flag": (
            "zhongguo_workforce_collective_snapshot_v1_query_supported"
        ),
        "observation_only": True,
        "gameplay_action_complete": True,
    },
    "ai_owned_case_matrix": {
        "implementation": "wired",
        "required_capability": (
            QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
        ),
        "required_query_flag": (
            "zhongguo_ai_owned_case_snapshot_v1_query_supported"
        ),
        "observation_only": True,
        "gameplay_action_complete": True,
    },
    "manager_governance_gameplay_action_and_postcondition_matrix": {
        "implementation": "provider_pending",
        "handler_implementation": "wired",
        "readiness": "static-ready",
        "required_capability": (
            QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
        ),
        "required_query_flag": (
            "zhongguo_manager_governance_snapshot_v1_query_supported"
        ),
        "required_typed_selector": PHASE2_B3_MANAGER_SELECTOR_KIND,
        "observation_only": False,
        "gameplay_action_complete": False,
    },
    "scoreboard_named_widget_and_acl_matrix": {
        "implementation": "provider_pending",
        "required_capability": QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
        "required_query_flag": (
            "zhongguo_scoreboard_state_v1_query_supported"
        ),
        "observation_only": False,
        "gameplay_action_complete": False,
    },
}
PHASE2_MISSING_GAMEPLAY_ACTION_CELLS = (
    "manager_governance_gameplay_action_and_postcondition_matrix",
    "scoreboard_named_widget_action_and_postcondition_matrix",
)


def log(message: str) -> None:
    acceptance.log(f"zg361: {message}")


class PromoRecorder:
    """Append-only desktop recorder started only after CK3 gameplay is visible."""

    def __init__(
        self,
        artifact_dir: Path,
        *,
        contract: PromoCaptureContract = LEGACY_PROMO_CAPTURE_CONTRACT,
    ):
        self.artifact_dir = artifact_dir
        self.contract = contract
        self.raw_dir = artifact_dir / "raw"
        self.raw_path = self.raw_dir / "zg361-promo-live-full-take-01.mkv"
        self.log_path = self.raw_dir / "ffmpeg-take-01.log"
        self.timeline_path = artifact_dir / "capture-timeline.json"
        self.process: subprocess.Popen[bytes] | None = None
        self.log_handle = None
        self.started_monotonic: float | None = None
        self.started_at_utc: str | None = None
        self.marks: list[dict[str, object]] = []
        self.clean_frame_gates: dict[str, dict[str, object]] = {}
        self.reviewed_official_history_id: str | None = None
        self.real_character_provenance: dict[str, object] | None = None
        self.phase2_capture_lineage: dict[str, object] | None = None
        self.phase2_span_receipt_provider: Callable[..., Mapping[str, object]] | None = None
        self.phase2_seed_chain_provider: Callable[..., Mapping[str, object]] | None = None

    def bind_phase2_receipt_sources(
        self,
        *,
        capture_lineage: Mapping[str, object],
        span_receipt_provider: Callable[..., Mapping[str, object]],
        seed_chain_provider: Callable[..., Mapping[str, object]],
    ) -> None:
        """Bind real runner evidence providers before a phase-two recording.

        These callbacks archive materialized save-checkpoints and project
        already-observed seed/session identities.  They are deliberately
        absent from the legacy recorder path.
        """

        if self.contract != PHASE2_PROMO_CAPTURE_CONTRACT:
            raise acceptance.RunnerError(
                "phase-two receipt sources require the phase-two recorder contract"
            )
        if self.process is not None or self.phase2_capture_lineage is not None:
            raise acceptance.RunnerError(
                "phase-two receipt sources must be bound exactly once before recording"
            )
        if not callable(span_receipt_provider) or not callable(seed_chain_provider):
            raise acceptance.RunnerError(
                "phase-two receipt providers must be callable"
            )
        self.phase2_capture_lineage = dict(capture_lineage)
        self.phase2_span_receipt_provider = span_receipt_provider
        self.phase2_seed_chain_provider = seed_chain_provider

    def resolve_reviewed_subject(self, history_id: str) -> None:
        """Freeze the one runtime-selected historical subject for this take."""

        if (
            self.reviewed_official_history_id is not None
            and self.reviewed_official_history_id != history_id
        ):
            raise acceptance.RunnerError(
                "promo recorder received conflicting reviewed subjects: "
                f"{self.reviewed_official_history_id} and {history_id}"
            )
        self.real_character_provenance = promo_real_character_provenance(history_id)
        self.reviewed_official_history_id = history_id

    def start(self) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise acceptance.RunnerError("ffmpeg is required for --promo-capture")
        self.raw_dir.mkdir(parents=True)
        if self.raw_path.exists() or self.log_path.exists() or self.timeline_path.exists():
            raise acceptance.RunnerError(
                f"promo capture output already exists: {self.artifact_dir}"
            )
        self.log_handle = self.log_path.open("wb")
        command = [
            ffmpeg,
            "-hide_banner",
            "-f",
            "gdigrab",
            "-framerate",
            "30",
            "-draw_mouse",
            "1",
            "-i",
            "desktop",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(self.raw_path),
        ]
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=self.log_handle,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.started_monotonic = time.monotonic()
        self.started_at_utc = datetime.now(timezone.utc).isoformat()
        time.sleep(1.5)
        if self.process.poll() is not None:
            raise acceptance.RunnerError(
                f"promo recorder exited during startup; inspect {self.log_path}"
            )
        self.mark("recording_started_after_gameplay_hud")

    def mark(self, label: str) -> None:
        if self.started_monotonic is None:
            return
        self.marks.append(
            {
                "label": label,
                "seconds": round(time.monotonic() - self.started_monotonic, 3),
            }
        )

    def hold(self, seconds: float = 2.5) -> None:
        if self.process is not None:
            time.sleep(seconds)

    def clean_hold(self, label: str, artifacts: Path, seconds: float = 2.5) -> None:
        """Record one exact promo-safe span with full-screen begin/end proof."""

        if self.process is None:
            return
        if label not in self.contract.clean_span_ids:
            raise acceptance.RunnerError(f"unknown promo clean span: {label}")
        if label in self.clean_frame_gates:
            raise acceptance.RunnerError(f"duplicate promo clean span: {label}")
        begin_mark = f"{label}_clean_begin"
        end_mark = f"{label}_clean_end"
        begin = assert_promo_frame_clean(
            artifacts, f"promo_clean_{label}_begin", label=label, phase="begin"
        )
        self.mark(begin_mark)
        self.hold(seconds)
        end = assert_promo_frame_clean(
            artifacts, f"promo_clean_{label}_end", label=label, phase="end"
        )
        self.mark(end_mark)
        self.clean_frame_gates[label] = {
            "span_id": label,
            "result": "GREEN",
            "begin_mark": begin_mark,
            "end_mark": end_mark,
            "full_screen": True,
            "fixture_test_ui_absent": True,
            "native_decisions_drawer_absent": True,
            "frames": [begin, end],
        }

    def stop(self) -> dict[str, object]:
        if self.process is None:
            return {}
        self.mark("recording_stop_requested")
        if self.process.stdin:
            try:
                self.process.stdin.write(b"q\n")
                self.process.stdin.flush()
            except OSError:
                pass
        try:
            returncode = self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            returncode = self.process.wait(timeout=10)
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None
        if returncode != 0 or not self.raw_path.is_file() or self.raw_path.stat().st_size == 0:
            raise acceptance.RunnerError(
                f"promo recorder failed with exit {returncode}; inspect {self.log_path}"
            )
        missing_clean_spans = [
            label
            for label in self.contract.clean_span_ids
            if label not in self.clean_frame_gates
        ]
        payload = {
            "schema": 2,
            "started_at_utc": self.started_at_utc,
            "exclude_ck3_loading": True,
            "source_kind": "real CK3 1.19.0.6 desktop capture after gameplay HUD",
            "raw_path": str(self.raw_path),
            "raw_bytes": self.raw_path.stat().st_size,
            "raw_sha256": isolated.sha256_file(self.raw_path),
            "ffmpeg_log": str(self.log_path),
            "marks": self.marks,
            "clean_frame_gates": [
                self.clean_frame_gates[label]
                for label in self.contract.clean_span_ids
                if label in self.clean_frame_gates
            ],
            "clean_capture_complete": not missing_clean_spans,
            "missing_clean_spans": missing_clean_spans,
            "real_character_provenance": self.real_character_provenance,
        }
        # Keep the established phase-one timeline byte/schema surface intact.
        # The dedicated contract metadata is required only for the new phase-
        # two producer, so existing --promo-capture consumers do not acquire a
        # hidden dependency on sequel vocabulary.
        if self.contract != LEGACY_PROMO_CAPTURE_CONTRACT:
            payload.update(
                {
                    "capture_mode": self.contract.mode,
                    "capture_contract_version": self.contract.version,
                    "capture_contract": self.contract.to_mapping(),
                }
            )
            if self.phase2_capture_lineage is not None:
                source = self.phase2_capture_lineage.get("source")
                source = source if isinstance(source, Mapping) else {}
                payload.update(
                    {
                        "capture_lineage": self.phase2_capture_lineage,
                        "source_git_commit": source.get("git_commit"),
                        "source_clean_tree_sha256": source.get("tree_sha256"),
                    }
                )
        write_json(self.timeline_path, payload)
        self.process = None
        if missing_clean_spans:
            raise acceptance.RunnerError(
                "promo capture is missing clean spans: " + ", ".join(missing_clean_spans)
            )
        if self.real_character_provenance is None:
            raise acceptance.RunnerError(
                "promo capture completed without resolving its historical reviewed subject"
            )
        return payload


Phase2PromoCaptureProducer = Callable[..., dict[str, object]]
_PHASE2_PROMO_CAPTURE_PRODUCER: Phase2PromoCaptureProducer | None = None
_PHASE2_PROMO_VISUAL_PRIMITIVES: dict[str, Phase2PromoVisualPrimitive] = {}


def _phase2_scoreboard_modal_visible(
    service: GameplayBridgeService,
    *,
    nonce: str,
    expected_revision: int,
) -> tuple[bool, dict[str, object]]:
    """Read the contracted scoreboard modal visibility from its provider."""

    response = service.query_zhongguo_scoreboard_state_v1(
        nonce, expected_revision=expected_revision
    )
    widgets = response.get("widgets") if isinstance(response, dict) else None
    modal = next(
        (
            row
            for row in widgets
            if isinstance(row, dict)
            and row.get("stable_identity") == "zg361_scoreboard_modal"
        ),
        None,
    ) if isinstance(widgets, list) else None
    visible = modal.get("effective_visible") if isinstance(modal, dict) else None
    if not (
        isinstance(response, dict)
        and response.get("status") == "available"
        and isinstance(visible, dict)
        and visible.get("status") == "available"
        and isinstance(visible.get("value"), bool)
    ):
        raise Phase2EventChoreographyError(
            "scoreboard_visibility_provider_unavailable",
            {"nonce": nonce, "response": response},
        )
    return bool(visible["value"]), response


class _Phase2RealEventChoreographyService:
    """Bind cross-span choreography to real native MCP primitives only."""

    def __init__(self, service: GameplayBridgeService) -> None:
        self.service = service

    def _source_checkpoint_restore_available(self) -> bool:
        restore = getattr(
            self.service, "restore_phase2_span_source_checkpoint_v1", None
        )
        readiness = getattr(
            self.service,
            "phase2_span_source_checkpoint_restore_available_v1",
            None,
        )
        return bool(
            callable(restore)
            and (not callable(readiness) or readiness() is True)
        )

    @staticmethod
    def _common(plan: Phase2EventSequencePlan) -> dict[str, object]:
        return {
            "result": "GREEN",
            "span_id": plan.span_id,
            "provider_observed": True,
            "ui_state_verified": True,
            "console_used": False,
            "test_fixture_used": False,
        }

    def preflight_source_checkpoints(
        self,
        context: Phase2PromoCaptureContext,
        _runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        capture_lineage = getattr(
            context.recorder, "phase2_capture_lineage", None
        )
        expected_seed_lineage_id = (
            capture_lineage.get("seed_lineage_id")
            if isinstance(capture_lineage, Mapping)
            else None
        )
        restore_available = self._source_checkpoint_restore_available()
        provider = Phase2SourceCheckpointProvider(
            (
                context.source_checkpoint_registry
                if isinstance(context.source_checkpoint_registry, Mapping)
                else None
            ),
            restore_registered_checkpoint=(
                (lambda _entry: {}) if restore_available else None
            ),
            expected_seed_lineage_id=(
                str(expected_seed_lineage_id)
                if isinstance(expected_seed_lineage_id, str)
                else None
            ),
        )
        try:
            preflight = provider.preflight()
        except Phase2SourceCheckpointError as error:
            raise Phase2EventChoreographyError(
                "source_checkpoint_preflight_red",
                {
                    "upstream_reason_code": error.reason_code,
                    "source_checkpoint_evidence": error.evidence,
                },
            ) from error
        if preflight.get("restore_interface_available") is not True:
            raise Phase2EventChoreographyError(
                "source_checkpoint_preflight_red",
                {
                    "upstream_reason_code": (
                        "registered_checkpoint_restore_provider_missing"
                    ),
                    "source_checkpoint_preflight": preflight,
                },
            )
        return preflight

    def _restore_registered_source(
        self,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
    ) -> dict[str, object]:
        registry = context.source_checkpoint_registry
        capture_lineage = getattr(
            context.recorder, "phase2_capture_lineage", None
        )
        expected_seed_lineage_id = (
            capture_lineage.get("seed_lineage_id")
            if isinstance(capture_lineage, Mapping)
            else None
        )
        restore_method = getattr(
            self.service, "restore_phase2_span_source_checkpoint_v1", None
        )
        restore_available = self._source_checkpoint_restore_available()

        def restore(entry: Phase2SourceCheckpoint) -> Mapping[str, object]:
            if not (restore_available and callable(restore_method)):
                raise Phase2SourceCheckpointError(
                    "registered_checkpoint_restore_provider_missing",
                    {"handler": plan.handler},
                )
            return restore_method(
                checkpoint_path=str(entry.path),
                expected_checkpoint_bytes=entry.bytes,
                expected_checkpoint_sha256=entry.sha256,
                expected_save_lineage_id=entry.save_lineage_id,
                expected_event_definition_key=(
                    entry.source_event_definition_key
                ),
                expected_owner_character_id=entry.owner_character_id,
                expected_player_character_id=entry.player_character_id,
                expected_date_raw=entry.date_raw,
                allow_generic_character_rebind=False,
                allow_fixture=False,
                allow_console=False,
            )

        provider = Phase2SourceCheckpointProvider(
            registry if isinstance(registry, Mapping) else None,
            restore_registered_checkpoint=(
                restore if restore_available else None
            ),
            expected_seed_lineage_id=(
                str(expected_seed_lineage_id)
                if isinstance(expected_seed_lineage_id, str)
                else None
            ),
        )
        try:
            restored = provider.restore(plan)
        except Phase2SourceCheckpointError as error:
            raise Phase2EventChoreographyError(
                "source_checkpoint_provider_red",
                {
                    "upstream_reason_code": error.reason_code,
                    "source_checkpoint_evidence": error.evidence,
                },
            ) from error
        expected = restored["expected"]
        assert isinstance(expected, Mapping)
        observed = self._wait_event(
            str(expected["event_definition_key"]),
            plan,
            context,
            operation="registered_source_restore",
        )
        binding = observed.get("binding")
        if not (
            isinstance(binding, Mapping)
            and binding.get("player_character_id")
            == expected.get("player_character_id")
            and binding.get("date_raw") == expected.get("date_raw")
        ):
            raise Phase2EventChoreographyError(
                "restored_source_live_binding_mismatch",
                {
                    "plan": asdict(plan),
                    "expected": dict(expected),
                    "observed_binding": binding,
                },
            )
        return {
            **self._common(plan),
            "event_definition_key": expected["event_definition_key"],
            "surface_visible": True,
            "registered_checkpoint_restore": restored,
            "live_event_observation": observed,
        }

    def stage_span_source(
        self,
        plan: Phase2EventSequencePlan,
        _scenario: object,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        if plan.handler in CHECKPOINT_REQUIRED_HANDLERS:
            return self._restore_registered_source(plan, context)
        if plan.source_kind == "event_free_map":
            snapshot = self.service.snapshot()
            binding = _phase2_paused_binding(
                snapshot, label=f"phase-two {plan.span_id} source staging"
            )
            if isinstance(snapshot.get("active_event"), dict):
                identity = query_event_definition_identity(self.service, snapshot)
                raise Phase2EventChoreographyError(
                    "event_free_source_blocked",
                    {"plan": asdict(plan), "event_identity": identity},
                )
            modal_visible, scoreboard = _phase2_scoreboard_modal_visible(
                self.service,
                nonce=f"zg361.phase2.promo.{plan.span_id}.source",
                expected_revision=int(binding["revision"]),
            )
            if modal_visible:
                raise Phase2EventChoreographyError(
                    "event_free_source_blocked",
                    {"plan": asdict(plan), "scoreboard": scoreboard},
                )
            return {
                **self._common(plan),
                "no_active_event": True,
                "binding": binding,
                "scoreboard_modal_visible": False,
            }

        if not isinstance(plan.source_event, str):
            raise Phase2EventChoreographyError(
                "product_source_event_missing", {"plan": asdict(plan)}
            )
        return self._wait_event(
            plan.source_event,
            plan,
            context,
            operation="source",
        )

    def _wait_event(
        self,
        event_definition_key: str,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        *,
        operation: str,
    ) -> dict[str, object]:
        gate = wait_for_native_event_definition(
            self.service,
            context.artifacts,
            stem=f"phase2_promo_{plan.span_id}_{operation}_{event_definition_key.replace('.', '_')}",
            expected_event_definition_key=event_definition_key,
            timeout_s=45.0,
            clear_unexpected_single_option_events=False,
        )
        identity = gate.get("identity") if isinstance(gate, dict) else None
        if not (
            isinstance(identity, dict)
            and identity.get("event_definition_key") == event_definition_key
        ):
            raise Phase2EventChoreographyError(
                "exact_product_event_not_observed",
                {
                    "plan": asdict(plan),
                    "expected_event": event_definition_key,
                    "gate": gate,
                },
            )
        return {
            **self._common(plan),
            "event_definition_key": event_definition_key,
            "surface_visible": True,
            "identity": identity,
            "binding": _phase2_paused_binding(
                gate["snapshot"],
                label=(
                    f"phase-two {plan.span_id} {operation} exact event"
                ),
            ),
            "wait_gate": gate.get("evidence"),
        }

    def wait_for_product_event(
        self,
        event_definition_key: str,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        _runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        return self._wait_event(
            event_definition_key, plan, context, operation="post_action"
        )

    def close_capture_surface(
        self,
        surface_kind: str,
        surface_id: str,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        _runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        if surface_kind == "product_event":
            snapshot = self.service.snapshot()
            binding = _phase2_paused_binding(
                snapshot, label=f"phase-two {plan.span_id} event close"
            )
            identity = query_event_definition_identity(self.service, snapshot)
            if identity.get("event_definition_key") != surface_id:
                raise Phase2EventChoreographyError(
                    "capture_event_identity_changed_before_close",
                    {
                        "plan": asdict(plan),
                        "expected_event": surface_id,
                        "identity": identity,
                    },
                )
            close = select_single_option_interruption_native(
                self.service,
                context.artifacts,
                f"phase2_promo_{plan.span_id}_{surface_id.replace('.', '_')}_close",
                expected_event_instance_id=int(identity["event_instance_id"]),
            )
            if close.get("result") != "GREEN":
                raise Phase2EventChoreographyError(
                    "capture_event_close_not_green",
                    {"plan": asdict(plan), "close": close},
                )
            return {
                **self._common(plan),
                "surface_kind": surface_kind,
                "surface_id": surface_id,
                "transition_materialized": True,
                "binding_before": binding,
                "close": close,
            }

        if surface_kind == "named_widget" and surface_id == "zg361_scoreboard_modal":
            close = run_zhongguo_scoreboard_action_cell(
                self.service,
                nonce_prefix=f"zg361.phase2.promo.{plan.span_id}.close",
            )
            request = close.get("action_request") if isinstance(close, dict) else None
            later = close.get("later_query") if isinstance(close, dict) else None
            widgets = later.get("widgets") if isinstance(later, dict) else None
            modal = next(
                (
                    row
                    for row in widgets
                    if isinstance(row, dict)
                    and row.get("stable_identity") == surface_id
                ),
                None,
            ) if isinstance(widgets, list) else None
            visible = modal.get("effective_visible") if isinstance(modal, dict) else None
            if not (
                isinstance(close, dict)
                and close.get("result") == "GREEN"
                and isinstance(request, dict)
                and request.get("action") == "close"
                and isinstance(visible, dict)
                and visible.get("status") == "available"
                and visible.get("value") is False
            ):
                raise Phase2EventChoreographyError(
                    "scoreboard_close_not_green",
                    {"plan": asdict(plan), "close": close},
                )
            return {
                **self._common(plan),
                "surface_kind": surface_kind,
                "surface_id": surface_id,
                "transition_materialized": True,
                "close": close,
            }

        raise Phase2EventChoreographyError(
            "capture_surface_close_provider_missing",
            {
                "plan": asdict(plan),
                "surface_kind": surface_kind,
                "surface_id": surface_id,
            },
        )

    def drain_after_span(
        self,
        plan: Phase2EventSequencePlan,
        _context: Phase2PromoCaptureContext,
        _runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        snapshot = self.service.snapshot()
        binding = _phase2_paused_binding(
            snapshot, label=f"phase-two {plan.span_id} drain"
        )
        active_event = snapshot.get("active_event")
        modal_visible, scoreboard = _phase2_scoreboard_modal_visible(
            self.service,
            nonce=f"zg361.phase2.promo.{plan.span_id}.drain",
            expected_revision=int(binding["revision"]),
        )
        no_active_event = active_event is None
        no_blocking_surface = no_active_event and not modal_visible
        if not no_blocking_surface:
            identity = (
                query_event_definition_identity(self.service, snapshot)
                if isinstance(active_event, dict)
                else None
            )
            raise Phase2EventChoreographyError(
                "span_drain_not_empty",
                {
                    "plan": asdict(plan),
                    "active_event_identity": identity,
                    "scoreboard_modal_visible": modal_visible,
                },
            )
        return {
            **self._common(plan),
            "no_active_event": True,
            "no_blocking_surface": True,
            "binding": binding,
            "scoreboard": scoreboard,
        }


class _Phase2AcceptanceActionSpanDriver:
    """Expose the four already-wired acceptance action cells as promo spans."""

    _HANDLERS = (
        "capture_receipt_appeal_pip",
        "capture_manager_governance",
        "capture_hc_workforce",
        "capture_incidents_operations",
    )

    def __init__(
        self,
        service: GameplayBridgeService,
        *,
        event_choreographer: Phase2EventChoreographer,
    ) -> None:
        self.service = service
        self.event_choreographer = event_choreographer

    def available_handlers(self) -> tuple[str, ...]:
        return self._HANDLERS

    def run_span(
        self,
        scenario: object,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        handler = str(getattr(scenario, "handler"))
        if handler not in self._HANDLERS:
            raise Phase2VisualHandlerError(
                "handler_not_owned", {"handler": handler}
            )
        snapshot = self.service.snapshot()
        if not isinstance(snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two promo action baseline is not an object"
            )
        binding = _phase2_paused_binding(
            snapshot, label=f"phase-two promo {handler} baseline"
        )
        if not isinstance(context.seed_contract, Mapping):
            raise acceptance.RunnerError(
                "phase-two promo action lacks its seed contract"
            )
        owners = _phase2_domain_query_contract(
            dict(context.seed_contract),
            player_character_id=int(binding["player_character_id"]),
        )
        if handler == "capture_receipt_appeal_pip":
            evidence = run_phase2_b2_pip_gameplay_action_cell(
                self.service,
                context.artifacts,
                owner_character_id=owners["b2_pip_owner_character_id"],
            )
        elif handler == "capture_manager_governance":
            evidence = run_phase2_ai_owned_case_gameplay_action_cell(
                self.service,
                context.artifacts,
                owner_character_id=owners["ai_owned_case_owner_character_id"],
                subject_character_id=owners["ai_owned_case_subject_character_id"],
            )
        elif handler == "capture_incidents_operations":
            evidence = run_phase2_incident_gameplay_action_cell(
                self.service,
                context.artifacts,
                owner_character_id=owners["incident_owner_character_id"],
            )
        else:
            # The production-only seed must already contain the route.  This
            # preflight never installs or activates the acceptance fixture.
            evidence = preflight_phase2_workforce_m360_gameplay_action_cell(
                self.service,
                context.artifacts,
                owner_character_id=owners["workforce_owner_character_id"],
                subject_character_id=int(binding["player_character_id"]),
                seed_contract=dict(context.seed_contract),
                prior_lineage={"scope": "phase2_promo_production_seed"},
            )
        if not isinstance(evidence, Mapping) or evidence.get("result") != "GREEN":
            raise Phase2VisualHandlerError(
                "acceptance_action_cell_not_green",
                {"handler": handler, "action_cell": evidence},
            )
        plan = phase2_event_sequence_plan(handler)
        post_action = (
            self.event_choreographer.present_post_action_events(
                scenario, context, runtime
            )
            if plan.post_action_events
            else None
        )
        visible = _phase2_promo_visible_scenario_surface(self.service, scenario)
        return {
            "result": "GREEN",
            "surface_visible": True,
            "postcondition_green": True,
            "handler": handler,
            "action_cell": dict(evidence),
            "post_action_event_sequence": post_action,
            "visible_surface": visible,
        }


def _phase2_promo_visible_scenario_surface(
    service: GameplayBridgeService, scenario: object
) -> dict[str, object]:
    snapshot = service.snapshot()
    if not isinstance(snapshot, dict) or not isinstance(
        snapshot.get("active_event"), dict
    ):
        raise Phase2VisualHandlerError(
            "scenario_surface_not_visible",
            {"handler": getattr(scenario, "handler", None)},
        )
    identity = query_event_definition_identity(service, snapshot)
    expected = tuple(getattr(scenario, "event_definition_keys"))
    if identity.get("event_definition_key") not in expected:
        raise Phase2VisualHandlerError(
            "scenario_surface_not_visible",
            {"expected_events": list(expected), "event_identity": identity},
        )
    return identity


def _phase2_promo_advance_to_result(
    service: GameplayBridgeService,
    plan: object,
    context: Phase2PromoCaptureContext,
    _runtime: Mapping[str, object],
) -> Mapping[str, object]:
    saved_state = (
        context.seed_contract.get("saved_state")
        if isinstance(context.seed_contract, Mapping)
        else None
    )
    player_character_id = (
        saved_state.get("played_character_id")
        if isinstance(saved_state, Mapping)
        else None
    )
    if isinstance(player_character_id, bool) or not isinstance(
        player_character_id, int
    ):
        raise Phase2VisualHandlerError("seed_player_identity_unavailable")
    result = wait_for_phase2_exact_event(
        service,
        expected_definition_key=str(getattr(plan, "result_event")),
        expected_player_character_id=player_character_id,
    )
    return {"result": "GREEN", "provider_observed": True, **result}


def _phase2_promo_event_postcondition(
    _service: GameplayBridgeService,
    plan: object,
    before: Mapping[str, object],
    after: Mapping[str, object],
    _context: Phase2PromoCaptureContext,
    _runtime: Mapping[str, object],
) -> Mapping[str, object]:
    checks = {
        "snapshot_advanced": before.get("snapshot_id") != after.get("snapshot_id"),
        "revision_advanced": isinstance(before.get("revision"), int)
        and isinstance(after.get("revision"), int)
        and int(after["revision"]) > int(before["revision"]),
        "native_revision_advanced": isinstance(before.get("native_revision"), int)
        and isinstance(after.get("native_revision"), int)
        and int(after["native_revision"]) > int(before["native_revision"]),
        "same_player": before.get("player_character_id")
        == after.get("player_character_id"),
    }
    green = all(checks.values())
    return {
        "result": "GREEN" if green else "RED",
        "provider_observed": True,
        "postcondition_green": green,
        "handler": getattr(plan, "handler", None),
        "checks": checks,
    }


def _make_default_phase2_promo_span_driver(
    context: Phase2PromoCaptureContext,
) -> SequencedPhase2SpanDriver:
    service = context.title_navigation_service
    event_choreographer = Phase2EventChoreographer(
        _Phase2RealEventChoreographyService(service)
    )
    visual = Phase2VisualHandlerAdapter(
        service,
        scoreboard_action_cell=run_phase2_scoreboard_gameplay_action_cell,
        advance_to_result={
            handler: _phase2_promo_advance_to_result
            for handler in (PROMOTION_HANDLER, PROJECTS_HANDLER, ENDGAME_HANDLER)
        },
        postcondition_verifiers={
            handler: _phase2_promo_event_postcondition
            for handler in (PROMOTION_HANDLER, PROJECTS_HANDLER, ENDGAME_HANDLER)
        },
    )
    composite = CompositePhase2SpanDriver(
        _Phase2AcceptanceActionSpanDriver(
            service, event_choreographer=event_choreographer
        ),
        visual,
    )
    return SequencedPhase2SpanDriver(composite, event_choreographer)


def register_phase2_promo_capture_producer(
    producer: Phase2PromoCaptureProducer,
) -> None:
    """Register the future real-game phase-two visual choreography.

    The registration point is deliberately explicit.  Until a producer is
    registered, ``--phase2-promo-capture`` fails before preflight/CK3/FFmpeg;
    this prevents the existing phase-one scenario from being reused under a
    sequel label.  A producer must start the recorder only after the gameplay
    HUD is visible and call ``clean_hold`` once for every canonical span.
    """

    global _PHASE2_PROMO_CAPTURE_PRODUCER
    if not callable(producer):
        raise TypeError("phase-two promo capture producer must be callable")
    _PHASE2_PROMO_CAPTURE_PRODUCER = producer


def register_phase2_promo_visual_primitive(
    producer_key: str,
    primitive: Phase2PromoVisualPrimitive,
) -> None:
    """Register one real gameplay surface for the built-in eight-span adapter.

    This registry is intentionally separate from the producer hook.  The
    runner can install its concrete managed-runtime producer before every
    visual feature has landed, while that producer still returns a typed RED
    before FFmpeg starts until all eight canonical keys are present.
    """

    expected_keys = tuple(key for _, key in PHASE2_PROMO_CAPTURE_SPAN_MAP)
    if producer_key not in expected_keys:
        raise ValueError(
            f"unknown phase-two promo producer key: {producer_key!r}"
        )
    if not callable(primitive):
        raise TypeError("phase-two promo visual primitive must be callable")
    if producer_key in _PHASE2_PROMO_VISUAL_PRIMITIVES:
        raise ValueError(
            f"duplicate phase-two promo producer key: {producer_key!r}"
        )
    _PHASE2_PROMO_VISUAL_PRIMITIVES[producer_key] = primitive


def _phase2_promo_paused_snapshot_probe(
    context: Phase2PromoCaptureContext,
) -> Mapping[str, object]:
    """Reuse the exact phase-two paused-map acceptance primitive."""

    return wait_for_phase2_paused_snapshot(
        context.title_navigation_service,
        context.artifacts,
        tracked_ck3_pid=context.tracked_ck3_pid,
    )


def _phase2_promo_seed_proof_probe(
    context: Phase2PromoCaptureContext,
    snapshot: Mapping[str, object],
) -> Mapping[str, object]:
    """Reuse the installed-seed proof before any visual recording starts."""

    if not isinstance(context.seed_contract, Mapping):
        raise acceptance.RunnerError(
            "phase-two promo seed contract is unavailable"
        )
    native_binding = context.native_session_binding
    expected_generation = (
        native_binding.get("connection_generation")
        if isinstance(native_binding, Mapping)
        else None
    )
    try:
        handoff = loaded_seed_live.run_existing_session_loaded_seed_v2(
            context.title_navigation_service,
            seed_contract=dict(context.seed_contract),
            artifacts=context.artifacts,
            tracked_ck3_pid=context.tracked_ck3_pid,
            expected_connection_generation=expected_generation,  # type: ignore[arg-type]
            first_snapshot=snapshot,
        )
    except loaded_seed_live.LoadedSeedLiveError as error:
        raise Phase2PromoProducerUnavailable(
            error.reason_code,
            "phase-two loaded-seed inline handoff blocked before recording",
            evidence=error.evidence,
        ) from error
    proof = handoff.get("loaded_seed_proof")
    if not isinstance(proof, Mapping):
        raise Phase2PromoProducerUnavailable(
            "loaded_seed_v2_proof_missing",
            "phase-two loaded-seed inline handoff returned no proof",
            evidence={"handoff": handoff},
        )
    return dict(proof)


def _ensure_phase2_promo_capture_producer() -> Phase2PromoCaptureProducer:
    """Install the real managed-runtime adapter when no override is supplied."""

    if _PHASE2_PROMO_CAPTURE_PRODUCER is None:
        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=_phase2_promo_paused_snapshot_probe,
            seed_proof_probe=_phase2_promo_seed_proof_probe,
            visual_primitives=_PHASE2_PROMO_VISUAL_PRIMITIVES,
            span_driver_factory=_make_default_phase2_promo_span_driver,
            reviewed_history_id=PHASE2_SEED_PLAYER_HISTORY_ID,
            error_factory=acceptance.RunnerError,
        )
        register_phase2_promo_capture_producer(producer)
    return _require_phase2_promo_capture_producer()


def _require_phase2_promo_capture_producer() -> Phase2PromoCaptureProducer:
    producer = _PHASE2_PROMO_CAPTURE_PRODUCER
    if producer is None:
        raise acceptance.RunnerError(
            "phase-two promo capture producer hook is unavailable; "
            "no CK3 launch or FFmpeg recording was attempted"
        )
    return producer


def run_phase2_promo_capture_scenario(
    stream: "MarkerStream",
    artifacts: Path,
    recorder: PromoRecorder,
    *,
    title_navigation_service: GameplayBridgeService,
    tracked_ck3_pid: int,
    native_bridge: NativeBridgeLaunchConfig,
    preflight_bridge_identity: dict[str, object],
    seed_contract: Mapping[str, object] | None = None,
    seed_install: Mapping[str, object] | None = None,
    native_session_binding: Mapping[str, object] | None = None,
    loader_gate: Mapping[str, object] | None = None,
    source_checkpoint_registry: Mapping[str, object] | None = None,
    capture_receipt_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Invoke only the explicitly registered sequel visual producer.

    This function is the stable hand-off between the acceptance runner and
    future phase-two gameplay choreography.  It intentionally has no fallback
    to ``run_scenario`` or ``run_phase2_live_scenario``: those paths either
    capture phase-one spans or are MCP-only and must not become video footage.
    """

    if recorder.contract != PHASE2_PROMO_CAPTURE_CONTRACT:
        raise acceptance.RunnerError(
            "phase-two promo scenario requires the canonical phase-two recorder contract"
        )
    producer = _require_phase2_promo_capture_producer()
    if (
        getattr(producer, "span_session_contract_version", None) == 2
        and capture_receipt_context is not None
    ):
        if not isinstance(seed_install, Mapping):
            raise acceptance.RunnerError(
                "phase-two span-session-v2 producer requires seed install evidence"
            )
        bootstrap = capture_receipt_context.get("bootstrap")
        runtime_identity = capture_receipt_context.get("runtime_identity")
        game_version = capture_receipt_context.get("game_version")
        executable_sha256 = capture_receipt_context.get("executable_sha256")
        if not (
            isinstance(bootstrap, Mapping)
            and isinstance(runtime_identity, Mapping)
            and isinstance(game_version, str)
            and isinstance(executable_sha256, str)
        ):
            raise acceptance.RunnerError(
                "phase-two span-session-v2 receipt context is incomplete"
            )
        lineage, span_receipts, seed_chain = _phase2_promo_receipt_sources(
            title_navigation_service,
            artifacts,
            seed_install=seed_install,
            bootstrap=bootstrap,
            runtime_identity=runtime_identity,
            game_version=game_version,
            executable_sha256=executable_sha256,
        )
        recorder.bind_phase2_receipt_sources(
            capture_lineage=lineage,
            span_receipt_provider=span_receipts,
            seed_chain_provider=seed_chain,
        )
    producer_kwargs: dict[str, object] = {
        "title_navigation_service": title_navigation_service,
        "tracked_ck3_pid": tracked_ck3_pid,
        "native_bridge": native_bridge,
        "preflight_bridge_identity": preflight_bridge_identity,
    }
    # Optional phase-two runtime snapshots are appended only when the managed
    # lifecycle supplied them.  Keeping the old keyword set intact for direct
    # callers preserves producers written against the original hand-off ABI.
    for name, value in (
        ("seed_contract", seed_contract),
        ("seed_install", seed_install),
        ("native_session_binding", native_session_binding),
        ("loader_gate", loader_gate),
        ("source_checkpoint_registry", source_checkpoint_registry),
    ):
        if value is not None:
            producer_kwargs[name] = value
    result = producer(
        stream,
        artifacts,
        recorder,
        **producer_kwargs,
    )
    if not isinstance(result, dict):
        raise acceptance.RunnerError(
            "phase-two promo capture producer must return an evidence object"
        )
    expected_contract = PHASE2_PROMO_CAPTURE_CONTRACT.to_mapping()
    required_contract_fields = (
        "capture_mode",
        "capture_contract_version",
        "capture_contract",
    )
    missing_contract_fields = tuple(
        field for field in required_contract_fields if field not in result
    )
    if missing_contract_fields:
        raise acceptance.RunnerError(
            "phase-two promo producer must explicitly return canonical "
            "capture contract fields: "
            + ", ".join(missing_contract_fields)
        )
    if "result" in result:
        producer_result = result["result"]
        if (
            type(producer_result) is not str
            or producer_result != "GREEN"
        ):
            raise acceptance.RunnerError(
                "phase-two promo producer returned an explicit result that is not GREEN"
            )
    result_mode = result["capture_mode"]
    if (
        type(result_mode) is not str
        or result_mode != PHASE2_PROMO_CAPTURE_MODE
    ):
        raise acceptance.RunnerError(
            "phase-two promo producer returned a non-canonical capture mode"
        )
    result_version = result["capture_contract_version"]
    if (
        type(result_version) is not int
        or isinstance(result_version, bool)
        or result_version != PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
    ):
        raise acceptance.RunnerError(
            "phase-two promo producer returned an unsupported capture contract version"
        )
    result_contract = result["capture_contract"]
    if (
        not isinstance(result_contract, dict)
        or not _strict_contract_equal(result_contract, expected_contract)
    ):
        raise acceptance.RunnerError(
            "phase-two promo producer returned a non-canonical capture contract"
        )
    return result


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


class Phase2LegalConsentBlocked(acceptance.RunnerError):
    """A managed Phase2 run stopped before an unauthorized consent click."""

    def __init__(self, reason_code: str, evidence: dict[str, object]) -> None:
        super().__init__(
            f"phase-two legal consent RED [{reason_code}]: "
            + str(evidence.get("failure_reason") or reason_code)
        )
        self.reason_code = reason_code
        self.evidence = evidence


def handle_phase2_optional_legal_consent(
    userdir: Path,
    artifacts: Path,
    *,
    maximum_agreements: int = 4,
) -> dict[str, object]:
    """Accept only necessary Paradox agreements inside the isolated profile.

    A normal screen with no legal modal returns GREEN without a click.  Every
    recognized agreement must expose a title/version, an allowlisted accept
    control and a new allowlisted marker written below this run's ``-userdir``.
    """

    profile = Path(userdir).resolve()
    evidence_path = Path(artifacts).resolve() / "01_phase2_legal_consent.json"
    ui_dir = evidence_path.parent / "legal-consent"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "reason_code": None,
        "scope": "phase2_managed_isolated_userdir_legal_consent",
        "authorization": legal_consent.LEGAL_AUTHORIZATION_TEXT,
        "authorization_version": legal_consent.LEGAL_AUTHORIZATION_VERSION,
        "commerce_classifier_version": (
            legal_consent.LEGAL_COMMERCE_CLASSIFIER_VERSION
        ),
        "explicitly_not_authorized": [
            "external real-money purchase",
            "external payment or paid order",
            "external checkout or cart action",
            "Steam or Paradox Store purchase action",
        ],
        "isolated_userdir": str(profile),
        "marker_relative_path": (
            legal_consent.LEGAL_CONSENT_PROFILE_SUFFIX.as_posix()
        ),
        "real_profile_read": False,
        "real_profile_modified": False,
        "ocr_used": True,
        "image_used": True,
        "authorized_click_count": 0,
        "acceptances": [],
        "classification_attempts": [],
        "classification_diagnostics": None,
        "screen_capture_attempts": [],
        "screen_capture_retry_count": 0,
        "state": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        if maximum_agreements <= 0:
            raise ValueError("maximum_agreements must be positive")
        acceptances: list[dict[str, object]] = []
        classification_attempts: list[dict[str, object]] = []
        stage_artifacts: list[dict[str, object]] = []
        screen_capture_attempts: list[dict[str, object]] = []

        def observe(index: int) -> tuple[object, list[str]]:
            deadline = (
                time.monotonic()
                + PHASE2_LEGAL_CONSENT_SCREEN_READY_TIMEOUT_S
            )
            image: object | None = None
            capture_attempt_number = 0
            while image is None:
                try:
                    capture_attempt_number += 1
                    focused = acceptance.focus_ck3()
                    if focused is False:
                        raise acceptance.RunnerError(
                            "CK3 window is not ready for legal-consent inspection"
                        )
                    captured = acceptance.ImageGrab.grab()
                    if captured is None:
                        raise acceptance.RunnerError(
                            "screen capture returned no image"
                        )
                    image = captured
                except (OSError, acceptance.RunnerError) as error:
                    now = time.monotonic()
                    retry = now < deadline
                    screen_capture_attempts.append(
                        {
                            "index": index,
                            "attempt": capture_attempt_number,
                            "error_type": type(error).__name__,
                            "error": str(error),
                            "retry": retry,
                        }
                    )
                    evidence.update(
                        {
                            "screen_capture_attempts": screen_capture_attempts,
                            "screen_capture_retry_count": len(
                                screen_capture_attempts
                            ),
                        }
                    )
                    # Preserve a typed, replayable failure even when the
                    # desktop never becomes capturable.  The commerce
                    # classifier is still reached only after a successful
                    # frame and remains the hard stop for purchase actions.
                    write_json(evidence_path, evidence)
                    if not retry:
                        raise
                    time.sleep(
                        min(
                            PHASE2_LEGAL_CONSENT_SCREEN_RETRY_INTERVAL_S,
                            max(0.0, deadline - now),
                        )
                    )
            assert image is not None
            rows = [
                str(row[0])
                for row in acceptance.ocr_results(
                    image, acceptance.FULL_SCREEN_REGION
                )
            ]
            attempt = legal_consent.persist_preclassification_evidence(
                image,
                rows,
                ui_dir,
                index,
                ck3_context_confirmed=True,
            )
            if attempt["evidence_required"]:
                classification_attempts.append(attempt)
                screenshot = attempt["preclassification_screenshot"]
                assert isinstance(screenshot, str)
                stage_artifacts.append(
                    {
                        "stage": "legal_consent_preclassification",
                        "path": Path(screenshot).name,
                    }
                )
                evidence.update(
                    {
                        "classification_attempts": classification_attempts,
                        "stage_artifacts": stage_artifacts,
                    }
                )
                # This write deliberately precedes classification: even a typed
                # stop must leave the exact OCR input and source frame behind.
                write_json(evidence_path, evidence)
            return image, rows

        for index in range(1, maximum_agreements + 1):
            image, rows = observe(index)
            classification = legal_consent.classify_authorized_legal_modal(
                rows, ck3_context_confirmed=True
            )
            if classification is None:
                break
            acceptances.append(
                legal_consent.accept_authorized_legal_modal(
                    acceptance,
                    acceptance.ImageGrab,
                    profile,
                    ui_dir,
                    image,
                    rows,
                    index,
                    stage_artifacts,
                    ck3_context_confirmed=True,
                )
            )
        else:
            _image, rows = observe(maximum_agreements + 1)
            if legal_consent.classify_authorized_legal_modal(
                rows, ck3_context_confirmed=True
            ) is not None:
                raise legal_consent.TypedTerminalError(
                    "LegalConsentSequenceLimit",
                    "legal_consent",
                    "more legal agreements are visible than the bounded handler allows",
                )
        evidence.update(
            {
                "result": "GREEN",
                "state": "accepted" if acceptances else "no_modal",
                "authorized_click_count": len(acceptances),
                "acceptances": acceptances,
                "classification_attempts": classification_attempts,
                "stage_artifacts": stage_artifacts,
                "failure_reason": None,
            }
        )
        write_json(evidence_path, evidence)
        return evidence
    except legal_consent.TypedTerminalError as error:
        diagnostics = error.diagnostics
        if classification_attempts:
            classification_attempts[-1].update(
                {
                    "classification_result": "typed_stop",
                    "typed_terminal": error.terminal,
                }
            )
            if diagnostics is None:
                diagnostics = {
                    key: classification_attempts[-1][key]
                    for key in (
                        "normalized_rows",
                        "normalized_text",
                        "ck3_context_confirmed",
                        "origin_terms",
                        "game_context_recognized",
                        "allowed_terms",
                        "denied_terms",
                        "purchase_terms",
                        "action_labels",
                        "purchase_action_labels",
                        "commerce_confirm_labels",
                        "dismiss_only_labels",
                        "external_commerce_terms",
                        "real_currency_matches",
                        "internal_resource_terms",
                        "commerce_mention_terms",
                        "external_commerce_context",
                        "internal_resource_context",
                        "actionable_commerce",
                        "commerce_context_conflict",
                        "legal_document_hints",
                        "protocol_category_terms",
                        "notification_hints",
                        "safe_action_terms",
                        "classification_state",
                        "evidence_required",
                        "authorization_text",
                        "authorization_version",
                    )
                }
        evidence.update(
            {
                "result": "RED",
                "reason_code": error.terminal,
                "state": "typed_stop",
                "failure_stage": error.stage,
                "failure_reason": str(error),
                "classification_attempts": classification_attempts,
                "classification_diagnostics": diagnostics,
            }
        )
        write_json(evidence_path, evidence)
        raise Phase2LegalConsentBlocked(error.terminal, evidence) from error
    except BaseException as error:
        evidence.update(
            {
                "result": "RED",
                "reason_code": "LegalConsentInspectionFailed",
                "state": "typed_stop",
                "failure_stage": "legal_consent",
                "failure_reason": f"{type(error).__name__}: {error}",
            }
        )
        write_json(evidence_path, evidence)
        raise Phase2LegalConsentBlocked(
            "LegalConsentInspectionFailed", evidence
        ) from error


def _format_keyboard_layout(value: int) -> str:
    return f"0x{value:08x}"


def force_ck3_english_keyboard_layout(
    artifacts: Path, stem: str = "04_ck3_keyboard_layout"
) -> dict[str, object]:
    """Put CK3's own UI thread on US English and deliberately leave it there."""

    output = artifacts / f"{stem}.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "policy": "keep_us_english_for_desktop_automation",
        "requested_klid": WINDOWS_ENGLISH_US_KLID,
        "requested_langid": f"{WINDOWS_ENGLISH_US_LANGID:04x}",
        "restore_requested": False,
        "restore_performed": False,
        "poll_observations": [],
    }
    try:
        if os.name != "nt":
            raise acceptance.RunnerError(
                "CK3 keyboard-layout attestation requires Windows"
            )
        if not acceptance.focus_ck3():
            raise acceptance.RunnerError(
                "CK3 could not be focused for keyboard-layout attestation"
            )
        hwnd = acceptance.win32gui.GetForegroundWindow()
        thread_id, pid = acceptance.win32process.GetWindowThreadProcessId(hwnd)
        title = acceptance.win32gui.GetWindowText(hwnd)
        evidence.update(
            {
                "window_handle": int(hwnd),
                "window_title": title,
                "target_thread_id": int(thread_id),
                "target_pid": int(pid),
                "tracked_ck3_pid": acceptance.ACTIVE_CK3_PID,
            }
        )
        if "Crusader Kings" not in title:
            raise acceptance.RunnerError(
                f"keyboard-layout target is not CK3: {title!r}"
            )
        if acceptance.ACTIVE_CK3_PID is not None and pid != acceptance.ACTIVE_CK3_PID:
            raise acceptance.RunnerError(
                "keyboard-layout target PID does not match the tracked CK3 process"
            )

        class GuiThreadInfo(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("hwndActive", wintypes.HWND),
                ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND),
                ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND),
                ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT),
            ]

        user32 = ctypes.windll.user32
        user32.GetGUIThreadInfo.argtypes = [
            wintypes.DWORD,
            ctypes.POINTER(GuiThreadInfo),
        ]
        user32.GetGUIThreadInfo.restype = wintypes.BOOL
        user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        user32.GetKeyboardLayout.restype = ctypes.c_void_p
        user32.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.PostMessageW.restype = wintypes.BOOL

        gui_info = GuiThreadInfo()
        gui_info.cbSize = ctypes.sizeof(GuiThreadInfo)
        input_hwnd = hwnd
        input_thread_id = thread_id
        input_pid = pid
        if user32.GetGUIThreadInfo(thread_id, ctypes.byref(gui_info)):
            focus_hwnd = int(gui_info.hwndFocus or 0)
            if focus_hwnd:
                focus_thread_id, focus_pid = (
                    acceptance.win32process.GetWindowThreadProcessId(focus_hwnd)
                )
                if focus_pid == pid:
                    input_hwnd = focus_hwnd
                    input_thread_id = focus_thread_id
                    input_pid = focus_pid
        evidence.update(
            {
                "input_window_handle": int(input_hwnd),
                "input_thread_id": int(input_thread_id),
                "input_pid": int(input_pid),
            }
        )

        before_hkl = int(user32.GetKeyboardLayout(input_thread_id) or 0)
        evidence.update(
            {
                "before_hkl": _format_keyboard_layout(before_hkl),
                "before_langid": f"{before_hkl & 0xFFFF:04x}",
            }
        )
        installed_hkls = [
            int(value) for value in acceptance.win32api.GetKeyboardLayoutList()
        ]
        evidence["installed_hkls"] = [
            _format_keyboard_layout(value) for value in installed_hkls
        ]
        if WINDOWS_ENGLISH_US_HKL not in installed_hkls:
            raise acceptance.RunnerError(
                "US English HKL 0x04090409 is not installed"
            )
        message_posted: bool | None = None
        requested_hkl = WINDOWS_ENGLISH_US_HKL
        if before_hkl != WINDOWS_ENGLISH_US_HKL:
            # The layout is already installed. Address CK3's window directly;
            # activating the runner's own thread would not prove that the game
            # receives subsequent shortcuts under the same layout.
            message_posted = bool(
                user32.PostMessageW(
                    input_hwnd,
                    WM_INPUTLANGCHANGEREQUEST,
                    0,
                    requested_hkl,
                )
            )
        evidence.update(
            {
                "requested_hkl": _format_keyboard_layout(requested_hkl),
                "message_posted": message_posted,
                "message_delivery_claimed": False,
            }
        )

        deadline = time.monotonic() + 2.0
        after_hkl = before_hkl
        observations: list[dict[str, object]] = []
        while True:
            after_hkl = int(user32.GetKeyboardLayout(input_thread_id) or 0)
            observations.append(
                {
                    "elapsed_ms": round(max(0.0, 2.0 - (deadline - time.monotonic())) * 1000),
                    "hkl": _format_keyboard_layout(after_hkl),
                    "langid": f"{after_hkl & 0xFFFF:04x}",
                }
            )
            if after_hkl == WINDOWS_ENGLISH_US_HKL:
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        evidence["poll_observations"] = observations
        evidence.update(
            {
                "after_hkl": _format_keyboard_layout(after_hkl),
                "after_langid": f"{after_hkl & 0xFFFF:04x}",
                "left_in_english": after_hkl == WINDOWS_ENGLISH_US_HKL,
            }
        )
        if not evidence["left_in_english"]:
            raise acceptance.RunnerError(
                "CK3 window thread did not attest US English layout 0409"
            )
        if acceptance.win32gui.GetForegroundWindow() != hwnd:
            raise acceptance.RunnerError(
                "CK3 lost foreground while changing its keyboard layout"
            )
        evidence["result"] = "GREEN"
        write_json(output, evidence)
        log(
            "left CK3 keyboard layout on US English "
            f"({_format_keyboard_layout(after_hkl)})"
        )
        return evidence
    except BaseException as error:
        evidence["error"] = str(error) or type(error).__name__
        write_json(output, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"CK3 keyboard-layout attestation failed: {error}"
        ) from error


def _paradox_top_level_block(text: str, key: str) -> str:
    """Return one exact top-level Paradox block for provenance checks."""

    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*\{{", text)
    if match is None:
        raise acceptance.RunnerError(f"vanilla history block is missing: {key}")
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise acceptance.RunnerError(f"vanilla history block is unterminated: {key}")


def fixture_constructor_counts() -> dict[str, int]:
    """Derive, rather than assert, fixture construction-command counts."""

    fixture_files = (
        tuple(FIXTURE_SOURCE.rglob("*.txt"))
        + tuple(FIXTURE_SOURCE.rglob("*.gui"))
        + tuple(FIXTURE_SOURCE.rglob("*.yml"))
    )
    text = "\n".join(path.read_text(encoding="utf-8-sig") for path in fixture_files)
    return {
        token: len(re.findall(rf"\b{re.escape(token)}\b", text))
        for token in (
            "create_character",
            "create_title",
            "grant_title",
            "set_father",
            "set_mother",
            "set_spouse",
            "add_relation",
            "set_relation",
        )
    }


def promo_real_character_provenance(
    reviewed_history_id: str,
) -> dict[str, object]:
    """Bind a take to Zhao Shu and one resolved, hard-allowed real official."""

    history_path = ROOT / "Crusader Kings III" / "game" / "history" / "characters" / "han.txt"
    title_history_path = (
        ROOT / "Crusader Kings III" / "game" / "history" / "titles" / "e_china.txt"
    )
    history_text = history_path.read_text(encoding="utf-8-sig")
    title_history_text = title_history_path.read_text(encoding="utf-8-sig")
    try:
        manager = real_characters.manager()
        reviewed = real_characters.reviewed_official(reviewed_history_id)
    except ValueError as exc:
        raise acceptance.RunnerError(str(exc)) from exc
    manager.update(
        {
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "expected_runtime_contract": {
                "is_player": True,
                "is_ai": False,
                "has_h_china": True,
                "independent": True,
            },
        }
    )
    reviewed.update(
        {
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "historical_title": reviewed["title_id"],
            "historical_liege_title": reviewed["liege_title_id"],
            "selection": "runtime_lowest_ranked_historical_duke_plus_from_hard_allowlist",
            "expected_runtime_contract": {
                "pre_switch_ai": True,
                "post_switch_player": True,
                "direct_liege_runtime": True,
                "current_review_record_runtime": True,
                "lowest_prior_rank_within_historical_duke_plus_allowlist": True,
            },
        }
    )
    records = []
    for subject in (manager, reviewed):
        history_id = str(subject["history_id"])
        _paradox_top_level_block(history_text, history_id)
        records.append(
            {
                **subject,
                "history_source": {
                    "path": str(history_path.resolve()),
                    "bytes": history_path.stat().st_size,
                    "sha256": isolated.sha256_file(history_path),
                },
            }
        )

    china_block = _paradox_top_level_block(title_history_text, "h_china")
    if re.search(
        r"1063\.4\.30\s*=\s*\{[^}]*holder\s*=\s*han_8052",
        china_block,
        re.S,
    ) is None:
        raise acceptance.RunnerError(
            "vanilla h_china history does not bind han_8052 at the 1066 start"
        )
    reviewed_title = str(reviewed["title_id"])
    reviewed_holder_date = str(reviewed["holder_date"])
    reviewed_liege_title = str(reviewed["liege_title_id"])
    reviewed_liege_holder_id = str(reviewed["liege_holder_id"])
    reviewed_liege_holder_date = str(reviewed["liege_holder_date"])
    reviewed_title_block = _paradox_top_level_block(
        title_history_text, reviewed_title
    )
    if re.search(
        rf"{re.escape(reviewed_holder_date)}\s*=\s*\{{"
        rf"[^}}]*holder\s*=\s*{re.escape(reviewed_history_id)}",
        reviewed_title_block,
        re.S,
    ) is None:
        raise acceptance.RunnerError(
            f"vanilla {reviewed_title} history does not bind "
            f"{reviewed_history_id} on {reviewed_holder_date}"
        )
    if re.search(
        rf"\bliege\s*=\s*{re.escape(reviewed_liege_title)}\b",
        reviewed_title_block,
    ) is None:
        raise acceptance.RunnerError(
            f"vanilla {reviewed_title} history does not bind its holder under "
            f"{reviewed_liege_title}"
        )
    reviewed_liege_block = _paradox_top_level_block(
        title_history_text, reviewed_liege_title
    )
    if re.search(
        rf"{re.escape(reviewed_liege_holder_date)}\s*=\s*\{{"
        rf"[^}}]*holder\s*=\s*{re.escape(reviewed_liege_holder_id)}",
        reviewed_liege_block,
        re.S,
    ) is None:
        raise acceptance.RunnerError(
            f"vanilla {reviewed_liege_title} history does not bind direct liege "
            f"holder {reviewed_liege_holder_id} on {reviewed_liege_holder_date}"
        )
    constructor_counts = fixture_constructor_counts()
    if any(constructor_counts.values()):
        raise acceptance.RunnerError(
            f"promo fixture manufactures historical subjects: {constructor_counts}"
        )
    return {
        "schema_version": 1,
        "bookmark": dict(real_characters.BOOKMARK),
        "subjects": records,
        "title_history_source": {
            "path": str(title_history_path.resolve()),
            "bytes": title_history_path.stat().st_size,
            "sha256": isolated.sha256_file(title_history_path),
        },
        "title_history_assertions": {
            "h_china_holder_at_start": "han_8052",
            "reviewed_official_title_at_start": reviewed_title,
            "reviewed_official_holder_at_start": reviewed_history_id,
            "reviewed_official_holder_date": reviewed_holder_date,
            "reviewed_official_title_liege_at_start": reviewed_liege_title,
            "reviewed_official_direct_liege_holder_at_start": reviewed_liege_holder_id,
            "reviewed_official_direct_liege_holder_date": reviewed_liege_holder_date,
        },
        "fixture_constructor_counts": constructor_counts,
        "fixture_state_kind": "fixture_preconditioned_real_characters",
        "performance_and_refusal_evidence_preconditioned": True,
        "test_decision_visibility_contract": {
            "initialization_decision_before_recording_only": True,
            "all_other_fixture_decisions_permanently_hidden": True,
        },
        "native_drawer_close_required_before_first_clean_span": True,
        "selection_contract": (
            "han_8052 is the historical Song emperor; the fixture selected exactly "
            f"{reviewed_history_id} as the lowest-prior-ranked eligible official "
            "inside the frozen 18-person historical duke+ allowlist; three "
            "historical counts are assessed-only, and two generated city officials "
            "in the 23-person runtime cohort are never eligible for promo identity"
        ),
    }


def _normalize_promo_visible_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum() or character == "_")


def _promo_decisions_header_hits(
    items: list[dict[str, object]], width: int, height: int
) -> tuple[list[str], str]:
    left, top, right, bottom = DECISIONS_HEADER_REGION
    header_text: list[str] = []
    for item in items:
        center = item.get("center")
        if (
            not isinstance(center, (list, tuple))
            or len(center) != 2
            or not all(isinstance(value, (int, float)) for value in center)
        ):
            continue
        x, y = float(center[0]), float(center[1])
        if left * width <= x <= right * width and top * height <= y <= bottom * height:
            header_text.append(str(item.get("text", "")))
    normalized = _normalize_promo_visible_text("".join(header_text))
    hits = [
        token
        for token in ("决议", "Decisions")
        if _normalize_promo_visible_text(token) in normalized
    ]
    return hits, normalized


def assert_promo_frame_clean(
    artifacts: Path, stem: str, *, label: str, phase: str
) -> dict[str, object]:
    """Save two consecutive full-screen proofs and reject fixture UI/drawer text."""

    width, height = acceptance.pyautogui.size()
    samples: list[dict[str, object]] = []
    for sample_index, sample_stem in enumerate(
        (stem, f"{stem}_drawer_confirmation"), start=1
    ):
        if sample_index > 1:
            time.sleep(acceptance.POLL_INTERVAL_S)
        items = acceptance.capture_ocr_bundle(
            artifacts, sample_stem, acceptance.FULL_SCREEN_REGION
        )
        if not items:
            raise acceptance.RunnerError(
                f"promo clean frame has no OCR evidence: {sample_stem}"
            )
        joined = "".join(str(item.get("text", "")) for item in items)
        normalized = _normalize_promo_visible_text(joined)
        forbidden_hits = [
            token
            for token in PROMO_FORBIDDEN_VISIBLE_TEXT
            if _normalize_promo_visible_text(token) in normalized
        ]
        drawer_hits, header_ocr = _promo_decisions_header_hits(items, width, height)
        product_event_overlay = promo_product_event_overlay_evidence(
            label, items, width, height
        )
        if forbidden_hits or drawer_hits or product_event_overlay:
            write_json(
                artifacts / f"red_{sample_stem}.json",
                {
                    "schema_version": 1,
                    "result": "RED",
                    "span": label,
                    "phase": phase,
                    "sample_index": sample_index,
                    "forbidden_hits": forbidden_hits,
                    "decisions_header_hits": drawer_hits,
                    "product_event_overlay": product_event_overlay,
                    "normalized_ocr": normalized,
                    "normalized_decisions_header_ocr": header_ocr,
                },
            )
            raise acceptance.RunnerError(
                f"promo clean frame {label}/{phase} contains fixture/test UI or "
                "the Decisions drawer, or overlays the free Jingcha planner with "
                "a product event: "
                f"forbidden={forbidden_hits}, drawer={drawer_hits}, "
                f"product_event_overlay={product_event_overlay}"
            )
        image_path = artifacts / f"{sample_stem}.png"
        ocr_path = artifacts / f"{sample_stem}_ocr.json"
        samples.append(
            {
                "sample_index": sample_index,
                "normalized_decisions_header_ocr": header_ocr,
                "image": {
                    "path": str(image_path.resolve()),
                    "bytes": image_path.stat().st_size,
                    "sha256": isolated.sha256_file(image_path),
                },
                "ocr": {
                    "path": str(ocr_path.resolve()),
                    "bytes": ocr_path.stat().st_size,
                    "sha256": isolated.sha256_file(ocr_path),
                },
            }
        )
    gate_path = artifacts / f"{stem}_gate.json"
    payload = {
        "schema_version": 1,
        "result": "GREEN",
        "span": label,
        "phase": phase,
        "full_screen": True,
        "fixture_test_ui_absent": True,
        "native_decisions_drawer_absent": True,
        "forbidden_hits": [],
        "drawer_absence_consecutive_samples": 2,
        "drawer_absence_samples": samples,
        "image": samples[0]["image"],
        "ocr": samples[0]["ocr"],
    }
    write_json(gate_path, payload)
    payload["gate"] = {
        "path": str(gate_path.resolve()),
        "bytes": gate_path.stat().st_size,
        "sha256": isolated.sha256_file(gate_path),
    }
    return payload


def git_text(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def write_evidence_index(artifacts: Path, matrix: dict[str, object]) -> None:
    files: list[dict[str, object]] = []
    for path in sorted(item for item in artifacts.rglob("*") if item.is_file()):
        if path.name == "evidence-index.json":
            continue
        files.append(
            {
                "path": path.relative_to(artifacts).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": isolated.sha256_file(path),
            }
        )
    try:
        git_head = git_text("rev-parse", "HEAD")
        git_status = git_text(
            "status",
            "--short",
            "--",
            "mod_zhongguo_style",
            "tools/run_zhongguo_acceptance.py",
            "tools/fixtures/zg361_acceptance",
        ).splitlines()
    except (OSError, subprocess.SubprocessError) as error:
        git_head = f"unavailable: {error}"
        git_status = []
    write_json(
        artifacts / "evidence-index.json",
        {
            "schema_version": 1,
            "result": matrix.get("result"),
            "artifact_root": str(artifacts),
            "git_head": git_head,
            "scoped_git_status": git_status,
            "files": files,
        },
    )


def script_tree_errors(root: Path, label: str) -> list[str]:
    if not root.is_dir():
        return [f"{label} missing: {root}"]
    errors: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"{label} text lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        runtime_product_file = not (
            root == SOURCE
            and (
                relative == "README.md"
                or relative.split("/", 1)[0] in SOURCE_ONLY_RUNTIME_ROOTS
            )
        )
        if runtime_product_file and "remote_file_id" in text:
            errors.append(f"{label} contains Workshop identity: {relative}")
        if root in {
            FIXTURE_SOURCE,
            PHASE2_WORKFORCE_ACTION_FIXTURE_SOURCE,
        } and path.suffix.lower() in {".txt", ".gui"}:
            depth = 0
            for line_number, line in enumerate(text.splitlines(), 1):
                body = line.split("#", 1)[0]
                depth += body.count("{") - body.count("}")
                if depth < 0:
                    errors.append(
                        f"fixture has unexpected closing brace: {relative}:{line_number}"
                    )
                    break
            if depth > 0:
                errors.append(f"fixture has {depth} unclosed brace(s): {relative}")
    return errors


def product_source_errors() -> list[str]:
    errors = script_tree_errors(SOURCE, "product")
    descriptor = SOURCE / "descriptor.mod"
    if not descriptor.is_file():
        errors.append("product descriptor.mod is missing")
    else:
        text = descriptor.read_text(encoding="utf-8-sig")
        if f'supported_version="{EXPECTED_GAME_VERSION}"' not in text:
            errors.append(f"product descriptor must support {EXPECTED_GAME_VERSION}")

    triggers = SOURCE / "common" / "scripted_triggers" / "zg361_triggers.txt"
    if not triggers.is_file():
        errors.append("production 361 entry trigger is missing")
    else:
        text = triggers.read_text(encoding="utf-8-sig")
        match = re.search(
            r"zg361_is_celestial_liege_trigger\s*=\s*\{(?P<body>.*?)^\}",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if match is None:
            errors.append("cannot isolate zg361_is_celestial_liege_trigger")
        else:
            body = match.group("body")
            for token in (
                "government_has_flag = government_is_celestial",
                "highest_held_title_tier >= tier_duchy",
                "is_landed = yes",
                "is_alive = yes",
            ):
                if token not in body:
                    errors.append(f"duchy-plus celestial entry missing {token}")
            if "is_independent" in body:
                errors.append(
                    "361 entry must include non-independent celestial dukes and kings"
                )

    effects = SOURCE / "common" / "scripted_effects" / "zg361_effects.txt"
    effects_text = effects.read_text(encoding="utf-8-sig") if effects.is_file() else ""
    snapshot_effects = (
        SOURCE
        / "common"
        / "scripted_effects"
        / "zg361_generated_scoreboard_snapshots.txt"
    )
    scoreboard_effects_text = effects_text + (
        snapshot_effects.read_text(encoding="utf-8-sig")
        if snapshot_effects.is_file()
        else ""
    )
    for token in (
        "zg361_run_review_effect = {",
        'debug_log = "ZG361: annual review tick"',
        "limit = { var:zg361_cohort_n >= 1 }",
        "name = zg361_pending_35_n value = var:zg361_cohort_n",
        "name = zg361_pending_grade value = 2",
        'debug_log = "ZG361: small cohort bypassed forced distribution and settled at 3.5"',
        "zg361_publish_scoreboard_effect = yes",
        "zg361_clear_scoreboard_m_slots_effect = yes",
        "zg361_write_managed_scoreboard_slot_effect = yes",
        "zg361_sb_m_01_char",
        "zg361_scoreboard_managed_375_n",
        "zg361_scoreboard_managed_35_n",
        "zg361_scoreboard_managed_325_n",
        "zg361_scoreboard_managed_shown_n",
        "zg361_sb_m_01_title",
        "zg361_sb_m_01_promotion",
        "zg361_sb_m_01_pip",
        "zg361_copy_received_scoreboard_slots_effect = yes",
    ):
        if token not in scoreboard_effects_text:
            errors.append(f"production review/scoreboard contract missing {token}")

    events = SOURCE / "events" / "zg361_events.txt"
    event_text = events.read_text(encoding="utf-8-sig") if events.is_file() else ""
    for token in ("zg361.10 = {", "name = zg361.10.a", "zg361_apply_pending_grades_effect"):
        if token not in event_text:
            errors.append(f"direct-publication calibration contract missing {token}")
    for token in (
        "zg361_snapshot_player_result_effect = {",
        "save_scope_as = zg361_reviewing_superior",
        "name = zg361_result_kpi",
        "name = zg361_result_rank",
        "name = zg361_result_cohort_n",
    ):
        if token not in effects_text:
            errors.append(f"personal result snapshot contract missing {token}")
    if effects_text.count("zg361_snapshot_player_result_effect = yes") != 3:
        errors.append("all three player grades must freeze their result payload")
    # Only the legacy delayed result trio (.2/.3/.4) is forbidden from
    # rebuilding its payload from live review variables.  Phase two events
    # deliberately bind the already-frozen result case to saved event scopes;
    # scanning the whole file would reject that immutable read model.
    legacy_result_event_text = event_text.split(
        "# 玩家封臣：3.25 正式送达、见证送达、申诉时钟与个人清算单",
        1,
    )[0]
    if any(
        token in legacy_result_event_text
        for token in (
            "save_scope_as = zg361_reviewing_superior",
            "name = zg361_result_kpi",
            "name = zg361_result_rank",
            "name = zg361_result_cohort_n",
        )
    ):
        errors.append("delayed result events must not re-read live review data")

    phase_icon = (
        SOURCE
        / "gfx"
        / "interface"
        / "icons"
        / "activity_phases"
        / "zg361_jingcha_phase.dds"
    )
    if not phase_icon.is_file() or phase_icon.stat().st_size == 0:
        errors.append("production jingcha phase icon is missing")

    chinese_loc = SOURCE / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml"
    chinese_text = (
        chinese_loc.read_text(encoding="utf-8-sig") if chinese_loc.is_file() else ""
    )
    for token in (
        'zg361.1.t:0 "你主持的考核：名册已定"',
        'zg361.2.t:0 "上司考定：3.75',
        'zg361.3.t:0 "上司考定：3.5',
        'zg361.4.t:0 "上司考定：3.25',
        "TopScope.GetValue('zg361_result_kpi')",
        "TopScope.GetValue('zg361_result_rank')",
    ):
        if token not in chinese_text:
            errors.append(f"personal result localization contract missing {token}")

    gui = SOURCE / "gui" / "zg361_scoreboard.gui"
    gui_text = gui.read_text(encoding="utf-8-sig") if gui.is_file() else ""
    for token in (
        'name = "zg361_scoreboard_toggle"',
        'position = { -60 90 }',
        "Not(IsRightWindowOpen)",
        "Not(IsGameViewOpen('outliner'))",
        "Not(IsPauseMenuShown)",
        "IsDefaultGUIMode",
        'name = "zg361_scoreboard_panel"',
        "zg361_sb_m_01_kpi",
        "zg361_scoreboard_tab_managed",
        "zg361_scoreboard_tab_received",
        "zg361_scoreboard_tab_system",
        "shortcut = close_window",
    ):
        if token not in gui_text:
            errors.append(f"production managed scoreboard GUI missing {token}")
    registration = SOURCE / "gui" / "scripted_widgets" / "zg361_scripted_widgets.txt"
    if not registration.is_file() or (
        "gui/zg361_scoreboard.gui = zg361_scoreboard_window"
        not in registration.read_text(encoding="utf-8-sig")
    ):
        errors.append("production scoreboard widget registration is missing")
    return errors


def fixture_source_errors() -> list[str]:
    errors = script_tree_errors(FIXTURE_SOURCE, "fixture")
    required = (
        "descriptor.mod",
        "common/decisions/zga_decisions.txt",
        "common/modifiers/zga_modifiers.txt",
        "common/scripted_effects/zga_effects.txt",
        "common/scripted_effects/zga_generated_361_cases.txt",
        "common/scripted_guis/zga_guis.txt",
        "events/zga_events.txt",
        "gui/zga_bridge.gui",
        "gui/scripted_widgets/zga_scripted_widgets.txt",
        "localization/simp_chinese/zga_l_simp_chinese.yml",
        "localization/english/zga_l_english.yml",
    )
    for relative in required:
        if not (FIXTURE_SOURCE / relative).is_file():
            errors.append(f"fixture file missing: {relative}")
    effects = FIXTURE_SOURCE / "common" / "scripted_effects" / "zga_effects.txt"
    text = effects.read_text(encoding="utf-8-sig") if effects.is_file() else ""
    generated_cases = (
        FIXTURE_SOURCE
        / "common"
        / "scripted_effects"
        / "zga_generated_361_cases.txt"
    )
    fixture_events = FIXTURE_SOURCE / "events" / "zga_events.txt"
    fixture_decisions = FIXTURE_SOURCE / "common" / "decisions" / "zga_decisions.txt"
    fixture_modifiers = FIXTURE_SOURCE / "common" / "modifiers" / "zga_modifiers.txt"
    scenario_text = text + (
        generated_cases.read_text(encoding="utf-8-sig")
        if generated_cases.is_file()
        else ""
    ) + (
        fixture_events.read_text(encoding="utf-8-sig")
        if fixture_events.is_file()
        else ""
    ) + (
        fixture_decisions.read_text(encoding="utf-8-sig")
        if fixture_decisions.is_file()
        else ""
    ) + (
        fixture_modifiers.read_text(encoding="utf-8-sig")
        if fixture_modifiers.is_file()
        else ""
    )
    for token in (
        "character:han_8052",
        "title:h_china",
        "zg361_run_review_effect = yes",
        "zg361_scoreboard_managed",
        "highest_held_title_tier >= tier_duchy",
        "non_independent_celestial_liege_entry",
        "set_player_character = scope:zga_personal_result_target",
        "superior_assigned_player_grade",
        "personal_result_switch_scheduled",
        "zga_verify_361_mechanism_batch_effect = yes",
        "ZGA: MECHANISM CASE PASS 001",
        "ZGA: MECHANISM CASE PASS 361",
        "zga_verify_fixed_scoreboard_slots_effect = yes",
        "zg361_sb_m_01_char",
        "zga_jingcha_planner_decision",
        "set_variable = { name = zg361_jingcha_pending value = 1 }",
        "trigger_event = zg361.40",
        "jingcha_mandate_issued",
        "grade_325_fourfold_penalty",
        "phase2_case_facts_and_quota_reason_frozen",
        "phase2_delivery_and_receipt_idempotent",
        "zg361_compute_kpi_effect = yes",
        "zg361_apply_grade_effect = yes",
        "phase2_player_325_prepared_without_early_penalty",
        "trigger_event = { id = zga_acceptance.13 days = 8 }",
        "phase2_refused_notice_witnessed_and_settled",
        "phase2_refused_delivery_receipt_idempotent",
        "appeal_exact_fixed_refund_and_salary_stop",
        "appeal_refund_idempotent",
        "bootstrap_first_review_strict_7_14_2",
        "pending_review_idempotent",
        "bootstrap_first_review_result_7_14_2",
        "post_baseline_newcomer_prepared",
        "post_baseline_newcomer_protected_from_325",
        "calibration_c_all_newcomer_noop",
        "calibration_c_mixed_newcomer_atomic_swap",
        "var:zga_all_new_protected_actual = var:zg361_cohort_n",
        "zga_original_pending_grade",
        "var:zga_mixed_35_actual = var:zga_mixed_35_actual_before",
        "var:zga_mixed_325_actual = var:zga_mixed_325_actual_before",
        "zga_mark_historical_song_direct_candidate_effect",
        "historical_song_direct_whitelist_complete",
        "generated_city_officials_excluded_from_provenance",
        "personal_result_target_selected_from_prior_historical_assessor_tail",
        "personal_result_target_can_assess_others",
        "personal_result_target_projected_bottom_two",
        HISTORICAL_TARGET_DATA_MARKER_PREFIX,
        HISTORICAL_TARGET_PASS_MARKER,
        "clean_jingcha_dispatch_scheduled",
        "clean_jingcha_dispatched",
        "clean_policy_chain_scheduled",
        "clean_policy_001_dispatched",
        "clean_policy_007_dispatched",
        "clean_policy_020_dispatched",
        "clean_policy_022_dispatched",
        "clean_policy_026_dispatched",
        "clean_policy_361_dispatched",
        "clean_policy_chain_completed",
        "zg361_init_org_ledger_effect = yes",
        "trigger_event = { id = zga_acceptance.5 days = 10 }",
        "trigger_event = { id = zga_acceptance.3 days = 90 }",
        "trigger_event = { id = zga_acceptance.12 days = 1 }",
        "settled_review_same_year_idempotent",
        "jingcha_refusal_superior_opinion_and_kpi_minus_50",
        "refusal_reason_consumed_once_by_original_superior",
        "ai_small_cohort_review_scheduled",
        "ai_small_cohort_candidate_unavailable",
        "ai_small_cohort_neutral_settlement",
        "ai_small_cohort_same_year_idempotent",
        "zga_acceptance_recording_health_guard",
        "recording_health_guard_applied",
        "recording_health_guard_removed_before_switch",
        "days = 120",
    ):
        if token not in scenario_text:
            errors.append(f"fixture scenario contract missing {token}")
    expected_historical_ids = set(EXPECTED_HISTORICAL_COHORT_HISTORY_IDS)
    expected_target_ids = set(EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS)
    marked_historical_id_rows = re.findall(
        r"character:(han_\d+)\s*=\s*\{\s*"
        r"zga_mark_historical_song_direct_candidate_effect\s*=\s*yes\s*\}",
        text,
    )
    marked_historical_ids = set(marked_historical_id_rows)
    data_marker_id_rows = re.findall(
        re.escape(HISTORICAL_TARGET_DATA_MARKER_PREFIX) + r"(han_\d+)\b",
        text,
    )
    data_marker_ids = set(data_marker_id_rows)
    if (
        marked_historical_ids != expected_historical_ids
        or len(marked_historical_id_rows) != len(expected_historical_ids)
    ):
        errors.append(
            "fixture historical candidate marks drifted from the frozen 21-person "
            f"allowlist: missing={sorted(expected_historical_ids - marked_historical_ids)}, "
            f"extra={sorted(marked_historical_ids - expected_historical_ids)}"
        )
    if (
        data_marker_ids != expected_target_ids
        or len(data_marker_id_rows) != len(expected_target_ids)
    ):
        errors.append(
            "fixture historical target DATA branches drifted from the frozen "
            f"18-person duke+ allowlist: missing={sorted(expected_target_ids - data_marker_ids)}, "
            f"extra={sorted(data_marker_ids - expected_target_ids)}"
        )
    if text.count(f'debug_log = "{HISTORICAL_TARGET_PASS_MARKER}"') != 1:
        errors.append(
            "fixture must emit exactly one generic historical target PASS branch"
        )
    for token in (
        "create_character",
        "create_title",
        "grant_title",
        "set_father",
        "set_mother",
        "set_spouse",
        "add_relation",
        "set_relation",
    ):
        if re.search(rf"\b{re.escape(token)}\b", scenario_text):
            errors.append(
                f"fixture must use vanilla history subjects, found constructor {token}"
            )
    return errors


def verified_workshop_runtime(
    runtime_source: Path, workshop_manifest: Path
) -> dict[str, object]:
    """Verify a real Workshop cache leaf against the tagged release sidecar."""

    runtime_source = Path(runtime_source).expanduser().resolve()
    workshop_manifest = Path(workshop_manifest).expanduser().resolve()
    if not runtime_source.is_dir():
        raise acceptance.RunnerError(
            f"Workshop runtime source directory missing: {runtime_source}"
        )
    if not workshop_manifest.is_file():
        raise acceptance.RunnerError(
            f"Workshop verification manifest missing: {workshop_manifest}"
        )
    try:
        count = release.verify_manifest(
            runtime_source, workshop_manifest, workshop_cache=True
        )
        payload = json.loads(workshop_manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise acceptance.RunnerError(
            f"Workshop runtime manifest verification failed: {error}"
        ) from error
    item_id = str(payload["workshop_item_id"])
    if runtime_source.name != item_id:
        raise acceptance.RunnerError(
            "Workshop runtime source must be the numeric cache leaf matching "
            f"the manifest item ID: {runtime_source.name!r} != {item_id!r}"
        )
    steam_root = terminal.steam_userdata_root()
    app_roots = [
        path.resolve() for path in isolated.steam_workshop_app_roots(steam_root)
    ]
    isolated.validate_workshop_target(runtime_source, app_roots)
    try:
        head = git_text("rev-parse", "HEAD")
    except (OSError, subprocess.SubprocessError) as error:
        raise acceptance.RunnerError(
            f"cannot bind Workshop cache to Git HEAD: {error}"
        ) from error
    if payload["git_sha"] != head:
        raise acceptance.RunnerError(
            f"Workshop manifest Git SHA {payload['git_sha']} does not match HEAD {head}"
        )
    if payload["git_tag"] != release.product_tag(str(payload["mod_version"])):
        raise acceptance.RunnerError(
            "Workshop manifest is not bound to the formal product tag"
        )
    return {
        "verified_workshop_cache": True,
        "runtime_source_kind": "verified_workshop_cache",
        "runtime_source_path": str(runtime_source),
        "workshop_item_id": item_id,
        "workshop_manifest_path": str(workshop_manifest),
        "workshop_manifest_sha256": isolated.sha256_file(workshop_manifest),
        "workshop_manifest_git_sha": payload["git_sha"],
        "workshop_manifest_git_tag": payload["git_tag"],
        "verified_file_count": count,
    }


def resolve_native_bridge_config(
    bridge_dll: str | Path | None,
    bridge_injector: str | Path | None,
    bridge_pipe: str | None,
) -> NativeBridgeLaunchConfig:
    """Select one explicit pure-native bridge and one run-unique pipe."""

    selected_pipe = bridge_pipe or f"{NATIVE_TITLE_PIPE_PREFIX}{uuid.uuid4().hex}"
    if re.fullmatch(
        re.escape(NATIVE_TITLE_PIPE_PREFIX) + r"[0-9a-f]{32}", selected_pipe
    ) is None:
        raise acceptance.RunnerError(
            "--bridge-pipe must be a run-unique "
            r"\\.\pipe\xar_ck3_bridge_zg361_<32 lowercase hex> name"
        )
    if bool(bridge_dll) != bool(bridge_injector):
        raise acceptance.RunnerError(
            "--bridge-dll and --bridge-injector must be supplied together"
        )
    if bridge_dll and bridge_injector:
        candidate = NativeBridgeLaunchConfig(
            mode=NATIVE_BRIDGE_MODE,
            pipe_name=selected_pipe,
            dll_path=Path(bridge_dll).expanduser().resolve(),
            injector_path=Path(bridge_injector).expanduser().resolve(),
        )
    else:
        try:
            inherited = native_bridge_launch_config_from_environment()
        except Exception as error:
            raise acceptance.RunnerError(
                f"native bridge environment is invalid: {error}"
            ) from error
        if inherited is None:
            raise acceptance.RunnerError(
                "native title navigation requires --bridge-dll and "
                "--bridge-injector (or the existing XAR native-bridge environment)"
            )
        candidate = NativeBridgeLaunchConfig(
            mode=inherited.mode,
            pipe_name=selected_pipe,
            dll_path=inherited.dll_path,
            injector_path=inherited.injector_path,
        )
    try:
        selected = validate_native_bridge_launch_config(candidate)
    except Exception as error:
        raise acceptance.RunnerError(
            f"native bridge launch configuration is invalid: {error}"
        ) from error
    if selected.mode != NATIVE_BRIDGE_MODE:
        raise acceptance.RunnerError(
            "ZhongGuo acceptance requires native-headless mode with no visual fallback"
        )
    return selected


def native_bridge_preflight_identity(
    config: NativeBridgeLaunchConfig,
) -> dict[str, object]:
    """Freeze the exact injection artifacts selected before CK3 starts."""

    if not config.dll_path.is_file():
        raise acceptance.RunnerError(
            f"native bridge DLL is missing: {config.dll_path}"
        )
    if not config.injector_path.is_file():
        raise acceptance.RunnerError(
            f"native bridge injector is missing: {config.injector_path}"
        )
    return {
        "mode": config.mode,
        "pipe_name": config.pipe_name,
        "pipe_unique_to_run": True,
        "dll_path": str(config.dll_path),
        "dll_sha256": isolated.sha256_file(config.dll_path),
        "injector_path": str(config.injector_path),
        "injector_sha256": isolated.sha256_file(config.injector_path),
        "command_timeout_seconds": NATIVE_TITLE_COMMAND_TIMEOUT_S,
        "visual_fallback": False,
    }


def preflight(
    runtime_source: Path = SOURCE,
    workshop_manifest: Path | None = None,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    *,
    require_visual_tools: bool = True,
) -> dict[str, object]:
    # Run the optional open_kaishek gate before any CK3/desktop work.  The
    # adapter is deliberately advisory when the external checkout or jar is
    # absent, so existing acceptance environments keep their prior behaviour;
    # a real GREEN is never inferred from an UNSUPPORTED/schema-only result.
    try:
        kaishek_root_override = (
            os.environ.get("XAR_KAISHEK_PREFLIGHT_ROOT")
            or os.environ.get("OPEN_KAISHEK_PREFLIGHT_ROOT")
            or os.environ.get("KAISHEK_PREFLIGHT_ROOT")
        )
        open_kaishek_preflight = kaishek_preflight.run_preflight(
            root=kaishek_root_override or runtime_source,
            ck3_build=EXPECTED_GAME_VERSION,
            ck3_exe_sha256=EXPECTED_EXE_SHA256,
        )
    except BaseException as error:
        # Keep a malformed optional integration from obscuring the runner's
        # own preflight result.  The failure remains machine-readable and is
        # not converted to a false GREEN.
        open_kaishek_preflight = {
            "schema": kaishek_preflight.ADAPTER_SCHEMA,
            "status": "failed",
            "result": "FAILED",
            "ok": False,
            "reason": "adapter-exception",
            "error": f"{type(error).__name__}: {error}",
            "provenance": {
                "cli_contract_commit": kaishek_preflight.CLI_CONTRACT_COMMIT,
                "open_kaishek_release": os.environ.get(
                    "XAR_OPEN_KAISHEK_RELEASE", "unreleased"
                ),
                "open_kaishek_commit": os.environ.get(
                    "XAR_OPEN_KAISHEK_COMMIT"
                ),
            },
        }
    errors = fixture_source_errors()
    errors.extend(product_source_errors())
    errors.extend(
        script_tree_errors(
            PHASE2_WORKFORCE_ACTION_FIXTURE_SOURCE,
            "phase-two Workforce action fixture",
        )
    )
    runtime_source = Path(runtime_source).expanduser().resolve()
    runtime_identity: dict[str, object] = {
        "verified_workshop_cache": False,
        "runtime_source_kind": "canonical_development_projection",
        "runtime_source_path": str(SOURCE.resolve()),
        "workshop_item_id": None,
        "workshop_manifest_path": None,
        "workshop_manifest_sha256": None,
        "workshop_manifest_git_sha": None,
        "workshop_manifest_git_tag": None,
        "verified_file_count": None,
        "native_bridge_runtime": None,
        "open_kaishek_preflight": open_kaishek_preflight,
    }
    if native_bridge is None:
        errors.append("native title-navigation bridge configuration is missing")
    else:
        try:
            runtime_identity["native_bridge_runtime"] = (
                native_bridge_preflight_identity(native_bridge)
            )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    if runtime_source == SOURCE.resolve():
        if workshop_manifest is not None:
            errors.append(
                "--workshop-manifest requires --workshop-cache-source"
            )
    elif workshop_manifest is None:
        errors.append(
            "a non-canonical runtime source requires --workshop-manifest"
        )
    else:
        try:
            runtime_identity.update(
                verified_workshop_runtime(runtime_source, workshop_manifest)
            )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    fixture_generation = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "gen_zhongguo_acceptance_cases.py"), "--check"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if fixture_generation.returncode != 0:
        errors.append(
            "361 live fixture generator is RED:\n"
            + (fixture_generation.stdout + fixture_generation.stderr).strip()
        )
    clean_fixture_contract = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "test_zg361_clean_promo_fixture.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if clean_fixture_contract.returncode != 0:
        errors.append(
            "clean historical promo fixture contract is RED:\n"
            + (
                clean_fixture_contract.stdout + clean_fixture_contract.stderr
            ).strip()
        )
    workforce_action_fixture_contract = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "tools"
                / "test_zg361_phase2_workforce_action_fixture.py"
            ),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if workforce_action_fixture_contract.returncode != 0:
        errors.append(
            "phase-two Workforce action fixture contract is RED:\n"
            + (
                workforce_action_fixture_contract.stdout
                + workforce_action_fixture_contract.stderr
            ).strip()
        )
    validation = subprocess.run(
        [sys.executable, str(SOURCE / "tools" / "validate_local.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if validation.returncode != 0:
        errors.append(
            "product static validator is RED:\n"
            + (validation.stdout + validation.stderr).strip()
        )
    if os.name != "nt":
        errors.append("ZhongGuo 361 acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("CK3 live acceptance is forbidden on official GitHub runners")
    if acceptance.ck3_is_running():
        errors.append("ck3.exe is already running")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        try:
            version = isolated.installed_game_version()
            if version != EXPECTED_GAME_VERSION:
                errors.append(f"CK3 version is {version}, expected {EXPECTED_GAME_VERSION}")
            executable_sha256 = isolated.sha256_file(acceptance.CK3_EXE)
            if executable_sha256 != EXPECTED_EXE_SHA256:
                errors.append(
                    "CK3 executable SHA-256 is "
                    f"{executable_sha256}, expected {EXPECTED_EXE_SHA256}"
                )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    desktop = "not_queried_mcp_only"
    if require_visual_tools:
        if acceptance._ocr is None:
            errors.append("RapidOCR is unavailable; use tools/.venv")
        width, height = acceptance.pyautogui.size()
        desktop = f"{width}x{height}"
        if width < 1920 or height < 1080:
            errors.append(f"interactive desktop is too small: {width}x{height}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(
        f"preflight passed: CK3={EXPECTED_GAME_VERSION}, "
        f"exe_sha256={EXPECTED_EXE_SHA256}, desktop={desktop}"
    )
    return runtime_identity


def render_presets() -> str:
    settings = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    settings.extend(("zg361_on", "zg361_freq_yearly", "zg361_ratio_strict"))
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate game-rule setting in acceptance preset")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def canonical_workshop_descriptor(
    descriptor: Path, workshop_manifest: Path
) -> bytes:
    """Recover the exact ID-free descriptor recorded by a formal manifest."""

    descriptor = Path(descriptor).resolve()
    workshop_manifest = Path(workshop_manifest).resolve()
    try:
        manifest = release._load_manifest(workshop_manifest, descriptor.parent)
        item_id = str(manifest["workshop_item_id"])
        entries = [
            entry for entry in manifest["files"] if entry["path"] == "descriptor.mod"
        ]
        if len(entries) != 1 or not release.workshop_descriptor_matches(
            descriptor, entries[0], item_id
        ):
            raise ValueError(
                "Workshop descriptor is not the exact permitted launcher injection"
            )
        data = descriptor.read_bytes()
    except (OSError, UnicodeError, ValueError) as error:
        raise acceptance.RunnerError(
            f"cannot project canonical Workshop descriptor: {error}"
        ) from error

    lines = data.splitlines()
    candidates: set[bytes] = set()
    for separator in (b"\n", b"\r\n"):
        body = separator.join(lines[:-1])
        for candidate in (body, body + separator):
            if (
                len(candidate) == entries[0]["size"]
                and release.sha256_bytes(candidate) == entries[0]["sha256"]
            ):
                candidates.add(candidate)
    if len(candidates) != 1:
        raise acceptance.RunnerError(
            "cannot uniquely recover canonical descriptor from Workshop cache"
        )
    return candidates.pop()


def bootstrap_userdir(
    userdir: Path,
    product_source: Path = SOURCE,
    workshop_manifest: Path | None = None,
    *,
    include_acceptance_fixture: bool = True,
    product_projection: str = "broad",
    product_projection_manifest: Path | None = None,
) -> dict[str, object]:
    product_source = Path(product_source).resolve()
    canonical_descriptor = (
        canonical_workshop_descriptor(
            product_source / "descriptor.mod", Path(workshop_manifest)
        )
        if workshop_manifest is not None
        else None
    )
    for path in (
        userdir / "mod",
        userdir / "mod-content",
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)

    product = userdir / "mod-content" / "zhongguo_361"
    product.mkdir(parents=True)
    try:
        projection = materialize_projection(
            product_source,
            product,
            projection_name=product_projection,
            manifest_path=product_projection_manifest,
            descriptor_override=canonical_descriptor,
        )
    except ProductProjectionError as error:
        raise acceptance.RunnerError(f"product projection failed: {error}") from error
    # Workshop upload/acceptance can require the launcher-canonical descriptor
    # bytes.  Apply that transformation only after the selected projection has
    # been verified and copied; the resulting tree hash is recomputed below.
    if canonical_descriptor is not None:
        (product / "descriptor.mod").write_bytes(canonical_descriptor)
        projection["tree_sha256"] = isolated.snapshot_digest(
            isolated.tree_snapshot(product)
        )
        projection["files"] = [
            {
                "path": path.relative_to(product).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": isolated.sha256_file(path),
            }
            for path in sorted(
                item for item in product.rglob("*") if item.is_file()
            )
        ]
        projection["bytes"] = sum(int(row["bytes"]) for row in projection["files"])
    product_files = [
        str(row["path"])
        for row in projection.get("files", [])
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    ]

    isolated.write_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    targets = {"product": product}
    enabled_mods = [f"mod/{PRODUCT_OUTER}"]
    if include_acceptance_fixture:
        fixture = userdir / "mod-content" / "fixture"
        shutil.copytree(FIXTURE_SOURCE, fixture)
        isolated.write_outer_descriptor(
            fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture
        )
        targets["fixture"] = fixture
        enabled_mods.append(f"mod/{FIXTURE_OUTER}")
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "player" / "game_rules" / "presets.txt").write_text(
        render_presets(), encoding="utf-8", newline="\n"
    )
    (userdir / "dlc_load.json").write_text(
        json.dumps(
            {"enabled_mods": enabled_mods, "disabled_dlcs": []},
            separators=(",", ":"),
        ),
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "pdx_settings.txt").write_text(
        terminal.render_settings(), encoding="utf-8", newline="\n"
    )
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    manifest = {
        "projection": projection,
        "files": product_files,
        "tree_sha256": isolated.snapshot_digest(snapshots["product"]),
    }
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(snapshot) for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "manifest": manifest,
    }


def load_phase2_seed_contract(
    contract_path: Path = PHASE2_SEED_CONTRACT_PATH,
) -> dict[str, object]:
    """Load the one hash-bound real-character seed without inferring fields."""

    contract_path = Path(contract_path).resolve()
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise acceptance.RunnerError(
            f"phase-two seed contract cannot be read: {error}"
        ) from error

    def exact_object(
        value: object, fields: set[str], label: str
    ) -> dict[str, object]:
        if not isinstance(value, dict) or set(value) != fields:
            raise acceptance.RunnerError(
                f"phase-two seed contract {label} fields are invalid"
            )
        return value

    exact_object(
        contract,
        {
            "schema_version",
            "kind",
            "status",
            "ready",
            "blocker",
            "source",
            "provenance",
            "runtime",
            "saved_state",
            "install",
            "domain_query_matrix",
        },
        "root",
    )
    source = exact_object(
        contract.get("source"),
        {
            "profile",
            "relative_save",
            "absolute_save",
            "bytes",
            "sha256",
            "last_write_time_utc",
            "last_write_time_ns",
        },
        "source",
    )
    provenance = exact_object(
        contract.get("provenance"),
        {
            "source_run",
            "source_report_sha256",
            "source_evidence_index_sha256",
            "source_git_commit",
            "real_character_proof",
            "limitations",
        },
        "provenance",
    )
    runtime = exact_object(
        contract.get("runtime"),
        {
            "game_version",
            "executable_sha256",
            "enabled_mods",
            "source_product_tree_sha256",
            "source_fixture_tree_sha256",
        },
        "runtime",
    )
    saved_state = exact_object(
        contract.get("saved_state"),
        {
            "date_raw",
            "played_character_id",
            "player_history_id",
            "played_character_alive",
            "paused_on_load",
            "map_ready",
        },
        "saved_state",
    )
    install = exact_object(
        contract.get("install"),
        {
            "continue_save_relative_path",
            "last_save_relative_path",
            "launch_mode",
        },
        "install",
    )
    domain_query_matrix = exact_object(
        contract.get("domain_query_matrix"),
        {
            "schema_version",
            "b2_pip_owner_character_id",
            "incident_owner_character_id",
            "workforce_owner_character_id",
            "ai_owned_case_owner_character_id",
            "ai_owned_case_subject_character_id",
        },
        "domain_query_matrix",
    )
    status = contract.get("status")
    ready = contract.get("ready")
    if (
        contract.get("schema_version") != 1
        or isinstance(contract.get("schema_version"), bool)
        or contract.get("kind") != "zg361_phase2_paused_seed"
        or status
        not in {
            "ready",
            "blocked_runtime_tree_mismatch",
            "blocked_seed_generation_required",
        }
        or not isinstance(ready, bool)
        or (status == "ready") is not ready
        or not isinstance(contract.get("blocker"), str)
    ):
        raise acceptance.RunnerError(
            "phase-two seed contract header/readiness is invalid"
        )
    if status != "ready" and not contract["blocker"]:
        raise acceptance.RunnerError(
            "phase-two blocked seed contract lacks a blocker explanation"
        )
    if status == "ready" and contract["blocker"]:
        raise acceptance.RunnerError(
            "phase-two ready seed contract must not retain a blocker"
        )

    sha_fields = (
        source.get("sha256"),
        provenance.get("source_report_sha256"),
        provenance.get("source_evidence_index_sha256"),
        runtime.get("executable_sha256"),
        runtime.get("source_product_tree_sha256"),
        runtime.get("source_fixture_tree_sha256"),
    )
    if any(
        not isinstance(value, str)
        or re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in sha_fields
    ):
        raise acceptance.RunnerError(
            "phase-two seed contract contains a non-canonical SHA-256"
        )
    if (
        not isinstance(source.get("bytes"), int)
        or isinstance(source.get("bytes"), bool)
        or source["bytes"] <= 0
        or not isinstance(source.get("last_write_time_ns"), int)
        or isinstance(source.get("last_write_time_ns"), bool)
        or source["last_write_time_ns"] <= 0
        or not isinstance(source.get("last_write_time_utc"), str)
        or not source["last_write_time_utc"]
    ):
        raise acceptance.RunnerError(
            "phase-two seed contract source size/time is invalid"
        )
    string_fields = (
        source.get("profile"),
        source.get("relative_save"),
        source.get("absolute_save"),
        provenance.get("source_run"),
        provenance.get("source_git_commit"),
        provenance.get("real_character_proof"),
    )
    if any(not isinstance(value, str) or not value for value in string_fields):
        raise acceptance.RunnerError(
            "phase-two seed contract source/provenance identity is invalid"
        )
    limitations = provenance.get("limitations")
    if (
        not isinstance(limitations, list)
        or any(not isinstance(value, str) or not value for value in limitations)
    ):
        raise acceptance.RunnerError(
            "phase-two seed contract provenance limitations are invalid"
        )
    if (
        runtime.get("game_version") != EXPECTED_GAME_VERSION
        or runtime.get("executable_sha256") != EXPECTED_EXE_SHA256
        or runtime.get("enabled_mods")
        != [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    ):
        raise acceptance.RunnerError(
            "phase-two seed contract runtime identity is not the frozen profile"
        )
    date_raw = saved_state.get("date_raw")
    character_id = saved_state.get("played_character_id")
    if (
        not isinstance(date_raw, int)
        or isinstance(date_raw, bool)
        or date_raw <= 0
        or not isinstance(character_id, int)
        or isinstance(character_id, bool)
        or character_id <= 0
        or saved_state.get("player_history_id")
        != PHASE2_SEED_PLAYER_HISTORY_ID
        or saved_state.get("played_character_alive") is not True
        or saved_state.get("paused_on_load") is not True
        or saved_state.get("map_ready") is not True
    ):
        raise acceptance.RunnerError(
            "phase-two seed contract saved-state identity is invalid"
        )
    if install != {
        "continue_save_relative_path": "save games/autosave.ck3",
        "last_save_relative_path": "last_save.ck3",
        "launch_mode": "native_session_continue_last_save",
    }:
        raise acceptance.RunnerError(
            "phase-two seed contract install slots/launch mode are invalid"
        )
    if domain_query_matrix.get("schema_version") != 1:
        raise acceptance.RunnerError(
            "phase-two seed contract domain_query_matrix schema is invalid"
        )
    selector_keys = (
        "b2_pip_owner_character_id",
        "incident_owner_character_id",
        "workforce_owner_character_id",
        "ai_owned_case_owner_character_id",
        "ai_owned_case_subject_character_id",
    )
    for key in selector_keys:
        selector = domain_query_matrix.get(key)
        if selector is None and ready is False:
            continue
        if (
            isinstance(selector, bool)
            or not isinstance(selector, int)
            or not 1 <= selector <= 2**31 - 1
        ):
            raise acceptance.RunnerError(
                f"phase-two seed contract {key} is not a captured "
                "CharacterID"
            )
    if ready is True and any(
        domain_query_matrix.get(key) is None for key in selector_keys
    ):
        raise acceptance.RunnerError(
            "phase-two ready seed contract has an uncaptured domain selector"
        )
    for key in selector_keys[:-1]:
        selector = domain_query_matrix.get(key)
        if selector is not None and selector == character_id:
            raise acceptance.RunnerError(
                f"phase-two seed contract {key} is the played CharacterID"
            )
    ai_owner = domain_query_matrix.get("ai_owned_case_owner_character_id")
    ai_subject = domain_query_matrix.get("ai_owned_case_subject_character_id")
    if ai_owner is not None and ai_owner == ai_subject:
        raise acceptance.RunnerError(
            "phase-two seed contract AI-owned owner and subject are identical"
        )
    return contract


def install_phase2_seed(
    userdir: Path,
    bootstrap: dict[str, object],
    artifacts: Path,
    *,
    observed_game_version: str,
    observed_executable_sha256: str,
    contract_path: Path = PHASE2_SEED_CONTRACT_PATH,
    product_only_runtime: bool = False,
) -> dict[str, object]:
    """Install an immutable compatible seed; verify current runtime after load."""

    evidence_path = artifacts / "00_phase2_seed_install.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_hash_bound_paused_seed_install",
        "mcp_only_launch": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "lobby_used": False,
        "test_decision_used": False,
        "contract_path": str(Path(contract_path).resolve()),
        "contract": None,
        "source": None,
        "source_provenance": None,
        "runtime_tree_policy": None,
        "targets": None,
        "checks": {},
        "failed_checks": [],
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        contract = load_phase2_seed_contract(contract_path)
        evidence["contract"] = contract
        source_contract = contract["source"]
        provenance_contract = contract["provenance"]
        runtime_contract = contract["runtime"]
        if not (
            isinstance(source_contract, dict)
            and isinstance(provenance_contract, dict)
            and isinstance(runtime_contract, dict)
        ):
            raise acceptance.RunnerError(
                "phase-two seed contract lost a validated object"
            )
        source_profile = Path(str(source_contract["profile"])).resolve()
        source_save = (source_profile / str(source_contract["relative_save"])).resolve()
        absolute_source = Path(str(source_contract["absolute_save"])).resolve()
        source_exists = source_save.is_file()
        source_stat = source_save.stat() if source_exists else None
        source_hash = isolated.sha256_file(source_save) if source_exists else None
        if source_exists:
            with source_save.open("rb") as source_stream:
                source_header = source_stream.read(96)
        else:
            source_header = b""
        source_run = Path(str(provenance_contract["source_run"])).resolve()
        source_report_path = source_run / "report.json"
        source_index_path = source_run / "evidence-index.json"
        source_report_exists = source_report_path.is_file()
        source_index_exists = source_index_path.is_file()
        source_report_hash = (
            isolated.sha256_file(source_report_path)
            if source_report_exists
            else None
        )
        source_index_hash = (
            isolated.sha256_file(source_index_path)
            if source_index_exists
            else None
        )
        source_report: dict[str, object] = {}
        source_report_error: str | None = None
        if source_report_exists:
            try:
                source_report_value = json.loads(
                    source_report_path.read_text(encoding="utf-8")
                )
                if not isinstance(source_report_value, dict):
                    raise TypeError("source report root is not an object")
                source_report = source_report_value
            except (OSError, UnicodeError, ValueError, TypeError) as error:
                source_report_error = f"{type(error).__name__}: {error}"
        source_cell_value = source_report.get("cell")
        source_cell = (
            source_cell_value if isinstance(source_cell_value, dict) else {}
        )
        source_scenario_value = source_cell.get("scenario_evidence")
        source_scenario = (
            source_scenario_value
            if isinstance(source_scenario_value, dict)
            else {}
        )
        source_snapshot_value = source_scenario.get("phase2_seed_snapshot")
        if not isinstance(source_snapshot_value, dict):
            # Read-only compatibility for the superseded phase-one source
            # report. A ready replacement must use phase2_seed_snapshot.
            source_matrix_value = source_scenario.get(
                "title_navigation_mcp_matrix"
            )
            source_matrix = (
                source_matrix_value
                if isinstance(source_matrix_value, dict)
                else {}
            )
            source_readiness_value = source_matrix.get("readiness")
            source_readiness = (
                source_readiness_value
                if isinstance(source_readiness_value, dict)
                else {}
            )
            source_snapshot_value = source_readiness.get("snapshot")
        source_snapshot = (
            source_snapshot_value
            if isinstance(source_snapshot_value, dict)
            else {}
        )
        source_player_value = source_snapshot.get("played_character")
        source_player = (
            source_player_value
            if isinstance(source_player_value, dict)
            else {}
        )
        source_attestation_value = source_scenario.get(
            "phase2_seed_bootstrap_attestation"
        )
        source_attestation = (
            source_attestation_value
            if isinstance(source_attestation_value, dict)
            else {}
        )
        source_event_close_value = source_attestation.get("event_close")
        source_event_close = (
            source_event_close_value
            if isinstance(source_event_close_value, dict)
            else {}
        )
        source_checkpoint_value = source_attestation.get("checkpoint")
        source_checkpoint = (
            source_checkpoint_value
            if isinstance(source_checkpoint_value, dict)
            else {}
        )
        source_tree_before_value = source_cell.get(
            "runtime_tree_before_sha256"
        )
        source_tree_before = (
            source_tree_before_value
            if isinstance(source_tree_before_value, dict)
            else {}
        )
        source_tree_after_value = source_cell.get(
            "runtime_tree_after_sha256"
        )
        source_tree_after = (
            source_tree_after_value
            if isinstance(source_tree_after_value, dict)
            else {}
        )
        tree_value = bootstrap.get("tree_sha256")
        tree = tree_value if isinstance(tree_value, dict) else {}
        enabled_mods = bootstrap.get("enabled_mods")
        install_contract = contract["install"]
        if not isinstance(install_contract, dict):
            raise acceptance.RunnerError(
                "phase-two seed install contract lost its validated object"
            )
        continue_save = userdir / str(
            install_contract["continue_save_relative_path"]
        )
        last_save = userdir / str(install_contract["last_save_relative_path"])
        checks = {
            "contract_status_ready": contract.get("status") == "ready",
            "contract_ready": contract.get("ready") is True,
            "source_profile_exists": source_profile.is_dir(),
            "source_save_exists": source_exists,
            "source_path_matches_contract": source_save == absolute_source,
            "source_save_inside_profile": isolated.is_relative_to(
                source_save, source_profile
            ),
            "source_size_matches": source_stat is not None
            and source_stat.st_size == source_contract.get("bytes"),
            "source_mtime_matches": source_stat is not None
            and source_stat.st_mtime_ns
            == source_contract.get("last_write_time_ns"),
            "source_sha256_matches": source_hash == source_contract.get("sha256"),
            "source_ck3_header": source_header.startswith(b"SAV0101"),
            "source_header_game_version": EXPECTED_GAME_VERSION.encode("ascii")
            in source_header,
            "source_run_exists": source_run.is_dir(),
            "source_report_exists": source_report_exists,
            "source_evidence_index_exists": source_index_exists,
            "source_report_sha256_matches": source_report_hash
            == provenance_contract.get("source_report_sha256"),
            "source_evidence_index_sha256_matches": source_index_hash
            == provenance_contract.get("source_evidence_index_sha256"),
            "source_report_parsed": source_report_error is None
            and bool(source_report),
            "source_report_green": source_report.get("result") == "GREEN"
            and source_cell.get("result") == "GREEN",
            "source_profile_matches_report": (
                isinstance(source_cell.get("isolated_userdir_path"), str)
                and Path(str(source_cell["isolated_userdir_path"])).resolve()
                == source_profile
            ),
            "source_report_game_version_matches": source_cell.get(
                "game_version"
            )
            == runtime_contract.get("game_version"),
            "source_report_executable_matches": source_cell.get(
                "ck3_executable_before_sha256"
            )
            == runtime_contract.get("executable_sha256")
            and source_cell.get("ck3_executable_after_sha256")
            == runtime_contract.get("executable_sha256"),
            "source_report_enabled_mod_ids_match": source_cell.get(
                "enabled_mods"
            )
            == runtime_contract.get("enabled_mods"),
            "source_product_tree_provenance_matches": source_tree_before.get(
                "product"
            )
            == runtime_contract.get("source_product_tree_sha256")
            and source_tree_after.get("product")
            == runtime_contract.get("source_product_tree_sha256"),
            "source_fixture_tree_provenance_matches": source_tree_before.get(
                "fixture"
            )
            == runtime_contract.get("source_fixture_tree_sha256")
            and source_tree_after.get("fixture")
            == runtime_contract.get("source_fixture_tree_sha256"),
            "source_runtime_trees_were_stable": source_cell.get(
                "runtime_trees_unchanged"
            )
            is True,
            "source_real_history_id_matches": source_scenario.get(
                "player_history_id"
            )
            == contract["saved_state"].get("player_history_id"),
            "source_real_character_id_matches": source_player.get(
                "character_id"
            )
            == contract["saved_state"].get("played_character_id"),
            "source_real_character_was_alive": source_player.get("alive")
            is True,
            "source_native_snapshot_was_paused_map": source_snapshot.get(
                "paused"
            )
            is True
            and source_snapshot.get("map_ready") is True,
            "source_native_snapshot_date_matches": source_snapshot.get(
                "date_raw"
            )
            == contract["saved_state"].get("date_raw"),
            "source_real_character_bootstrap_attested": source_attestation.get(
                "event_definition_key"
            )
            == "zga_phase2_seed.1"
            and source_attestation.get("player_history_id")
            == contract["saved_state"].get("player_history_id")
            and source_attestation.get("played_character_id")
            == contract["saved_state"].get("played_character_id")
            and source_attestation.get("domain_query_matrix")
            == contract.get("domain_query_matrix")
            and source_attestation.get("mcp_only") is True
            and source_event_close.get("step") == "select-event-option-1"
            and source_event_close.get("postcondition_verified") is True
            and source_checkpoint.get("status") == "saved"
            and source_checkpoint.get("path") == str(source_save)
            and source_checkpoint.get("size") == source_contract.get("bytes")
            and source_checkpoint.get("sha256") == source_contract.get("sha256")
            and source_checkpoint.get("date_raw")
            == contract["saved_state"].get("date_raw")
            and source_checkpoint.get("episode_character_id")
            == contract["saved_state"].get("played_character_id")
            and source_scenario.get(
                "historical_subjects_manufactured_by_fixture"
            )
            is False
            and source_scenario.get("ocr_used") is False
            and source_scenario.get("test_decision_used") is False,
            "observed_game_version_matches": observed_game_version
            == runtime_contract.get("game_version"),
            "observed_executable_matches": observed_executable_sha256
            == runtime_contract.get("executable_sha256"),
            "enabled_mods_match": (
                enabled_mods == [f"mod/{PRODUCT_OUTER}"]
                if product_only_runtime
                else enabled_mods == runtime_contract.get("enabled_mods")
            ),
            "current_product_runtime_tree_available": isinstance(
                tree.get("product"), str
            )
            and re.fullmatch(r"[0-9a-f]{64}", str(tree.get("product")))
            is not None,
            "current_fixture_runtime_tree_policy": (
                tree.get("fixture") is None
                if product_only_runtime
                else isinstance(tree.get("fixture"), str)
                and re.fullmatch(r"[0-9a-f]{64}", str(tree.get("fixture")))
                is not None
            ),
            "current_product_tree_matches_seed_source": (
                tree.get("product")
                == runtime_contract.get("source_product_tree_sha256")
                if product_only_runtime
                else True
            ),
            "continue_slot_absent": not continue_save.exists(),
            "last_save_slot_absent": not last_save.exists(),
        }
        evidence["source"] = {
            "profile": str(source_profile),
            "path": str(source_save),
            "bytes": source_stat.st_size if source_stat is not None else None,
            "last_write_time_ns": (
                source_stat.st_mtime_ns if source_stat is not None else None
            ),
            "sha256": source_hash,
        }
        evidence["source_provenance"] = {
            "run": str(source_run),
            "report": {
                "path": str(source_report_path),
                "sha256": source_report_hash,
                "parse_error": source_report_error,
            },
            "evidence_index": {
                "path": str(source_index_path),
                "sha256": source_index_hash,
            },
            "limitations": list(provenance_contract["limitations"]),
        }
        evidence["runtime_tree_policy"] = {
            "source_trees_are_provenance_only": True,
            "source": {
                "product": runtime_contract.get(
                    "source_product_tree_sha256"
                ),
                "fixture": runtime_contract.get(
                    "source_fixture_tree_sha256"
                ),
            },
            "current": {
                "product": tree.get("product"),
                "fixture": tree.get("fixture"),
            },
            "source_current_equality_required_for_install": False,
            "product_only_capture": product_only_runtime,
            "product_source_equality_required_for_capture": product_only_runtime,
            "post_load_current_runtime_gates": [
                "runtime_mount_inventory",
                "loaded_feature_manifest_v1",
                "paused_date_and_player_binding",
            ],
        }
        evidence["targets"] = {
            "continue_save": str(continue_save),
            "last_save": str(last_save),
        }
        evidence["checks"] = checks
        failed = [label for label, passed in checks.items() if passed is not True]
        evidence["failed_checks"] = failed
        if failed:
            raise acceptance.RunnerError(
                "phase-two seed install RED: " + ", ".join(failed)
            )

        continue_save.parent.mkdir(parents=True, exist_ok=True)
        last_save.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_save, continue_save)
        shutil.copy2(source_save, last_save)
        installed_checks = {
            "continue_save_size_matches": continue_save.stat().st_size
            == source_contract["bytes"],
            "last_save_size_matches": last_save.stat().st_size
            == source_contract["bytes"],
            "continue_save_sha256_matches": isolated.sha256_file(continue_save)
            == source_contract["sha256"],
            "last_save_sha256_matches": isolated.sha256_file(last_save)
            == source_contract["sha256"],
        }
        checks.update(installed_checks)
        failed = [label for label, passed in checks.items() if passed is not True]
        evidence["checks"] = checks
        evidence["failed_checks"] = failed
        if failed:
            raise acceptance.RunnerError(
                "phase-two seed materialization RED: " + ", ".join(failed)
            )
        evidence["result"] = "GREEN"
        evidence["failure_reason"] = None
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two seed install failed: {error}"
        ) from error


def preflight_phase2_seed_contract(
    contract_path: Path = PHASE2_SEED_CONTRACT_PATH,
    *,
    runtime_source: Path | None = None,
    workshop_manifest: Path | None = None,
    product_only_runtime: bool = False,
    product_source: Path | None = None,
    product_projection: str = "broad",
    product_projection_manifest: Path | None = None,
) -> dict[str, object]:
    """Validate the contract and optionally dry-install it without CK3."""

    contract = load_phase2_seed_contract(contract_path)
    if contract.get("ready") is not True:
        blocker = str(contract.get("blocker") or "unspecified seed blocker")
        raise acceptance.RunnerError(
            "phase-two seed preflight RED: " + blocker
        )
    if runtime_source is not None:
        selected_product_source = (
            Path(product_source)
            if product_source is not None
            else Path(runtime_source)
        )
        with tempfile.TemporaryDirectory(
            prefix="zg361-phase2-seed-preflight-"
        ) as temporary:
            temporary_root = Path(temporary)
            userdir = temporary_root / "profile"
            artifacts = temporary_root / "artifacts"
            artifacts.mkdir()
            bootstrap = bootstrap_userdir(
                userdir,
                selected_product_source,
                workshop_manifest=workshop_manifest,
                include_acceptance_fixture=not product_only_runtime,
                product_projection=product_projection,
                product_projection_manifest=product_projection_manifest,
            )
            install_phase2_seed(
                userdir,
                bootstrap,
                artifacts,
                observed_game_version=isolated.installed_game_version(),
                observed_executable_sha256=isolated.sha256_file(
                    acceptance.CK3_EXE
                ),
                contract_path=contract_path,
                product_only_runtime=product_only_runtime,
            )
    return contract


def prove_phase2_loaded_seed(
    snapshot: dict[str, object],
    seed_contract: dict[str, object],
    artifacts: Path,
    *,
    loaded_feature_manifest: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Bind the paused seed and its eight-span feature surface to one frame.

    Event definitions and GUI names in the returned matrix are requirements,
    not invented live observations.  Their real visibility and business
    postconditions remain the responsibility of each registered visual
    provider during choreography.  This gate proves only what the paused
    snapshot and the strict loaded-feature query can prove before gameplay.
    """

    evidence_path = artifacts / "04_phase2_seed_loaded.json"
    saved_state_value = seed_contract.get("saved_state")
    saved_state = (
        saved_state_value if isinstance(saved_state_value, dict) else {}
    )
    binding = _phase2_paused_binding(
        snapshot, label="phase-two installed seed"
    )
    source_value = seed_contract.get("source")
    source = source_value if isinstance(source_value, Mapping) else {}
    binding["save_sha256"] = source.get("sha256")
    played_character_value = snapshot.get("played_character")
    played_character = (
        played_character_value
        if isinstance(played_character_value, dict)
        else {}
    )
    manifest = (
        loaded_feature_manifest
        if isinstance(loaded_feature_manifest, Mapping)
        else {}
    )
    manifest_binding_value = manifest.get("binding")
    manifest_binding = (
        manifest_binding_value
        if isinstance(manifest_binding_value, Mapping)
        else {}
    )
    feature_flags_value = manifest.get("effective_feature_flags")
    feature_flags = (
        feature_flags_value
        if isinstance(feature_flags_value, Mapping)
        else {}
    )
    feature_items_value = feature_flags.get("items")
    feature_items = (
        feature_items_value if isinstance(feature_items_value, list) else []
    )
    enabled_features = {
        str(item["key"]): item.get("enabled") is True
        for item in feature_items
        if isinstance(item, Mapping)
        and isinstance(item.get("key"), str)
    }
    script_dlc_value = manifest.get("script_dlc_keys")
    script_dlc = (
        script_dlc_value if isinstance(script_dlc_value, Mapping) else {}
    )
    script_keys_value = script_dlc.get("keys")
    script_keys = {
        item for item in script_keys_value if isinstance(item, str)
    } if isinstance(script_keys_value, list) else set()
    manifest_checks = {
        "loaded_feature_manifest_ready": manifest.get(
            "loaded_feature_manifest_ready"
        )
        is True,
        "loaded_feature_manifest_available": manifest.get("status")
        == "available",
        "manifest_snapshot_id_matches": manifest_binding.get("snapshot_id")
        == binding["snapshot_id"],
        "manifest_revision_matches": manifest_binding.get("revision")
        == binding["revision"],
        "manifest_native_revision_matches": manifest_binding.get(
            "native_revision"
        )
        == binding["native_revision"],
        "manifest_date_matches": manifest_binding.get("date_raw")
        == binding["date_raw"],
        "feature_flags_available": feature_flags.get("status")
        == "available",
        "script_dlc_keys_available": script_dlc.get("status")
        == "available",
    }
    manifest_bound = all(manifest_checks.values())
    span_requirements: list[dict[str, object]] = []
    for scenario in PHASE2_CAPTURE_SCENARIOS:
        feature_observations = {
            key: enabled_features.get(key)
            for key in scenario.loaded_feature_flags
        }
        script_key_observations = {
            key: key in script_keys for key in scenario.script_dlc_keys
        }
        feature_ready = (
            manifest_bound
            and all(value is True for value in feature_observations.values())
            and all(
                value is True for value in script_key_observations.values()
            )
        )
        span_requirements.append(
            {
                "span_id": scenario.span_id,
                "producer_key": scenario.producer_key,
                "handler": scenario.handler,
                "requirements": {
                    "loaded_feature_flags": list(
                        scenario.loaded_feature_flags
                    ),
                    "script_dlc_keys": list(scenario.script_dlc_keys),
                    "event_definition_keys": list(
                        scenario.event_definition_keys
                    ),
                    "gui_surfaces": list(scenario.gui_surfaces),
                    "mcp_queries": list(scenario.mcp_queries),
                    "mcp_actions": list(scenario.mcp_actions),
                },
                "observed_loaded_feature_flags": feature_observations,
                "observed_script_dlc_keys": script_key_observations,
                "loaded_feature_seed_ready": feature_ready,
                "event_gui_provider_live_proof": "required_at_span_execution",
                "mcp_provider_live_proof": "required_at_span_execution",
                "provider_ready_claimed": False,
            }
        )
    checks = {
        "contract_ready": seed_contract.get("ready") is True,
        "contract_status_ready": seed_contract.get("status") == "ready",
        "date_raw_matches_seed": binding["date_raw"]
        == saved_state.get("date_raw"),
        "played_character_matches_seed": binding["player_character_id"]
        == saved_state.get("played_character_id"),
        "played_character_alive_matches_seed": played_character.get("alive")
        is True
        and saved_state.get("played_character_alive") is True,
        "paused_on_load_expected": saved_state.get("paused_on_load") is True,
        "map_ready_expected": saved_state.get("map_ready") is True,
        **manifest_checks,
        "all_eight_span_requirements_present": len(span_requirements) == 8
        and len({row["span_id"] for row in span_requirements}) == 8,
        "all_span_loaded_features_ready": all(
            row["loaded_feature_seed_ready"] is True
            for row in span_requirements
        ),
    }
    failed = [label for label, passed in checks.items() if passed is not True]
    evidence: dict[str, object] = {
        "schema_version": 2,
        "result": "GREEN" if not failed else "RED",
        "scope": "phase2_installed_seed_paused_snapshot_binding",
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "expected": {
            "date_raw": saved_state.get("date_raw"),
            "played_character_id": saved_state.get("played_character_id"),
        },
        "observed": binding,
        "loaded_feature_manifest_binding": dict(manifest_binding),
        "span_requirements": span_requirements,
        "provider_boundary": (
            "event, GUI and MCP provider availability is proven only by each "
            "span's registered live handler; this seed proof makes no such claim"
        ),
        "checks": checks,
        "failed_checks": failed,
        "failure_reason": (
            None
            if not failed
            else "phase-two loaded seed RED: " + ", ".join(failed)
        ),
    }
    write_json(evidence_path, evidence)
    if failed:
        raise acceptance.RunnerError(str(evidence["failure_reason"]))
    return evidence


def verify_runtime_load_order(
    userdir: Path, bootstrap: dict[str, object]
) -> list[str]:
    debug_log = userdir / "logs" / "debug.log"
    try:
        text = debug_log.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        raise acceptance.RunnerError(f"cannot read runtime mod inventory: {error}") from error
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", text)
    expected_enabled = list(bootstrap["enabled_mods"])
    if len(enabled) != len(expected_enabled) or set(enabled) != set(expected_enabled):
        raise acceptance.RunnerError(
            f"isolated enabled-mod inventory drifted: {enabled} != {expected_enabled}"
        )
    content_root = (userdir / "mod-content").resolve()
    mounted: list[Path] = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", text):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    targets_value = bootstrap.get("targets")
    targets = targets_value if isinstance(targets_value, dict) else {}
    target_keys = list(targets)
    if target_keys not in (["product"], ["product", "fixture"]):
        raise acceptance.RunnerError(
            f"isolated runtime target inventory is malformed: {target_keys}"
        )
    expected = [Path(targets[key]).resolve() for key in target_keys]
    if mounted != expected:
        raise acceptance.RunnerError(
            "isolated mount order drifted: "
            f"{[path.as_posix() for path in mounted]} != "
            f"{[path.as_posix() for path in expected]}"
        )
    return [path.as_posix() for path in mounted]


class MarkerStream:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = b""
        self.lines: list[str] = []

    def pump(self, final: bool = False) -> None:
        try:
            with self.path.open("rb") as source:
                source.seek(0, 2)
                size = source.tell()
                if size < self.offset:
                    self.offset = 0
                    self.pending = b""
                source.seek(self.offset)
                data = source.read()
                self.offset = source.tell()
        except OSError as error:
            if final:
                raise acceptance.RunnerError(f"cannot finalize fixture log: {error}") from error
            data = b""
        payload = self.pending + data
        if final:
            complete, self.pending = payload, b""
        else:
            boundary = max(payload.rfind(b"\n"), payload.rfind(b"\r"))
            if boundary < 0:
                self.pending = payload
                return
            complete, self.pending = payload[: boundary + 1], payload[boundary + 1 :]
        for line in complete.decode("utf-8", errors="ignore").splitlines():
            if "ZGA:" in line or "ZG361:" in line or "ZG361M:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                if not (
                    "ZGA: MECHANISM CASE PASS" in stripped
                    or "ZG361M: CASE" in stripped
                    or "ZGA: DATA player_scoreboard" in stripped
                    or "ZGA: DATA player_grade" in stripped
                ):
                    log(stripped)
        failures = [
            line
            for line in self.lines
            if "ZGA: TEST FAIL" in line or "ZGA: MECHANISM CASE FAIL" in line
            or "ZGA: MECHANISM LEDGER FAIL" in line
            or "ZGA: MECHANISM IDEMPOTENCE FAIL" in line
        ]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def count(self, marker: str) -> int:
        return sum(marker in line for line in self.lines)

    def wait(self, marker: str, timeout_s: float = 20) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self.pump()
            if self.count(marker):
                return
            time.sleep(acceptance.POLL_INTERVAL_S)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def counts(self) -> dict[str, int]:
        return {
            "rows": self.count("ZGA: DATA player_scoreboard_row"),
            "grade_375": self.count("ZGA: DATA player_grade_375"),
            "grade_35": self.count("ZGA: DATA player_grade_35"),
            "grade_325": self.count("ZGA: DATA player_grade_325"),
            "ai_non_independent_rows": self.count(
                "ZGA: DATA ai_non_independent_scoreboard_row"
            ),
        }

    def validate(self, final: bool = False) -> None:
        self.pump(final=final)
        required_markers = REQUIRED_FIXTURE_MARKERS
        if final:
            required_markers += REQUIRED_LATE_FIXTURE_MARKERS
        for marker in required_markers:
            count = self.count(marker)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )
        required_product_markers = dict(REQUIRED_PRODUCT_MARKERS)
        if final:
            required_product_markers.update(REQUIRED_LATE_PRODUCT_MARKERS)
        for marker, minimum in required_product_markers.items():
            count = self.count(marker)
            if count < minimum:
                raise acceptance.RunnerError(
                    f"product marker count for {marker!r} is {count}, expected >= {minimum}"
                )
        case_pass_ids = [
            int(match.group(1))
            for line in self.lines
            if (match := re.search(r"ZGA: MECHANISM CASE PASS (\d{3})", line))
        ]
        if case_pass_ids != list(range(1, 362)):
            raise acceptance.RunnerError(
                "361 fixture case coverage drifted: "
                f"count={len(case_pass_ids)}, unique={len(set(case_pass_ids))}"
            )
        batch_begin = next(
            index
            for index, line in enumerate(self.lines)
            if "ZGA: MECHANISM BATCH BEGIN 361" in line
        )
        batch_done = next(
            index
            for index, line in enumerate(self.lines[batch_begin:], batch_begin)
            if "ZGA: MECHANISM BATCH DONE 361" in line
        )
        batch_lines = self.lines[batch_begin : batch_done + 1]
        applied = [
            (int(match.group(1)), match.group(2).lower())
            for line in batch_lines
            if (
                match := re.search(
                    r"ZG361M: CASE (\d{3}) CHOICE ([ABC]) APPLIED", line
                )
            )
        ]
        manifest = json.loads(
            (SOURCE / "docs" / "361-mechanism-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        expected_applied = [
            (int(item["id"]), str(item["reference_choice"]))
            for item in manifest["items"]
        ]
        if applied != expected_applied:
            raise acceptance.RunnerError(
                "product mechanism markers do not match the 361 reference portfolio: "
                f"count={len(applied)}, unique={len(set(applied))}"
            )
        failures = [
            line
            for line in self.lines
            if "ZGA: TEST FAIL" in line or "ZGA: MECHANISM CASE FAIL" in line
            or "ZGA: MECHANISM LEDGER FAIL" in line
            or "ZGA: MECHANISM IDEMPOTENCE FAIL" in line
        ]
        if failures:
            raise acceptance.RunnerError(
                f"fixture emitted {len(failures)} failure marker(s)"
            )
        counts = self.counts()
        if counts["rows"] < 3:
            raise acceptance.RunnerError(
                f"managed scoreboard emitted only {counts['rows']} row marker(s)"
            )
        if (
            counts["grade_375"] + counts["grade_35"] + counts["grade_325"]
            != counts["rows"]
        ):
            raise acceptance.RunnerError(f"grade marker totals do not match rows: {counts}")
        scheduled = self.count("ZGA: TEST INFO ai_non_independent_review_scheduled")
        unavailable = self.count(
            "ZGA: TEST INFO ai_non_independent_review_candidate_unavailable"
        )
        if scheduled + unavailable != 1:
            raise acceptance.RunnerError(
                "AI non-independent probe must be either scheduled or explicitly unavailable"
            )
        if scheduled:
            for marker in (
                "ZGA: TEST PASS ai_non_independent_baseline_snapshot",
                "ZGA: TEST PASS ai_non_independent_full_review",
                "ZGA: TEST PASS settled_review_same_year_idempotent",
            ):
                if self.count(marker) != 1:
                    raise acceptance.RunnerError(
                        f"scheduled AI non-independent probe missing {marker}"
                    )
            if counts["ai_non_independent_rows"] < 3:
                raise acceptance.RunnerError(
                    "scheduled AI non-independent probe emitted fewer than 3 rows"
                )
        # The natural 1–2-person probe is deliberately scheduled only after the
        # manager board and the player's superior-assigned result are frozen.
        # The mid-run validation immediately after direct publication therefore
        # cannot demand its terminal marker; final validation remains strict.
        if final:
            self.validate_small_cohort_probe()

    def validate_small_cohort_probe(self) -> None:
        small_scheduled = self.count("ZGA: TEST INFO ai_small_cohort_review_scheduled")
        small_unavailable = self.count(
            "ZGA: TEST INFO ai_small_cohort_candidate_unavailable"
        )
        if small_scheduled + small_unavailable != 1:
            raise acceptance.RunnerError(
                "AI small-cohort probe must be either scheduled or explicitly unavailable"
            )
        if small_scheduled:
            for marker in (
                "ZGA: TEST PASS ai_small_cohort_neutral_settlement",
                "ZGA: TEST PASS ai_small_cohort_same_year_idempotent",
            ):
                if self.count(marker) != 1:
                    raise acceptance.RunnerError(
                        f"scheduled AI small-cohort probe missing {marker}"
                    )


def resolved_historical_personal_result_target(stream: MarkerStream) -> str:
    """Parse one exact target marker and enforce the frozen historical set."""

    stream.pump()
    pattern = re.compile(
        re.escape(HISTORICAL_TARGET_DATA_MARKER_PREFIX) + r"(han_\d+)\b"
    )
    matches = [
        match.group(1)
        for line in stream.lines
        if (match := pattern.search(line)) is not None
    ]
    if len(matches) != 1:
        raise acceptance.RunnerError(
            "historical personal-result target marker must resolve exactly once; "
            f"found={matches!r}"
        )
    history_id = matches[0]
    if history_id not in real_characters.REVIEWED_OFFICIAL_CONTRACT:
        raise acceptance.RunnerError(
            "historical personal-result target is outside the frozen 1066 Song "
            f"allowlist: {history_id}"
        )
    return history_id


def _is_phase2_static_liveness_warning(line: str) -> bool:
    """Recognize CK3 loader liveness diagnostics that do not reject Phase 2.

    These messages describe the engine's static reachability accounting, not
    a parse failure or a runtime effect failure.  The focused B2 r21 artifact
    proved the distinction: the same messages were present before the loader
    gate went GREEN, and all three product actions plus their postconditions
    completed before the generic diagnostic pass reclassified them as fatal.
    Keep the match deliberately exact so other project-attributed errors stay
    blocking.
    """

    lowered = line.lower()
    return (
        (
            "jomini_effect.cpp:1145" in lowered
            and " is set but is never used." in lowered
        )
        or (
            "jomini_effect.cpp:1161" in lowered
            and " is used but is never set." in lowered
            and (
                "setting it in an unused scripted trigger or effect "
                "does not count"
            )
            in lowered
        )
        or (
            "jomini_eventmanager.cpp:372" in lowered
            and "event " in lowered
            and " is orphaned" in lowered
        )
    )


def project_diagnostics(
    userdir: Path,
    artifacts: Path,
    stem: str,
    *,
    allow_phase2_static_liveness_warnings: bool = False,
) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    observed_engine_warnings: list[str] = []
    for name in ("error.log", "game.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        if not path.is_file():
            continue
        shutil.copy2(path, artifacts / f"{stem}_{name}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            context = " ".join(lines[max(0, index - 2) : index + 3]).lower()
            attributed = any(token in lowered for token in PROJECT_TOKENS)
            duplicate = any(pattern in lowered for pattern in DUPLICATE_PATTERNS)
            dynastic_cycle_stepdown_warning = (
                name == "game.log"
                and "situation.cpp:1314" in lowered
                and "attempted to remove" in lowered
                and "dynastic_cycle" in lowered
            )
            if dynastic_cycle_stepdown_warning:
                observed_engine_warnings.append(f"{name}: {line.strip()}")
            elif (
                allow_phase2_static_liveness_warnings
                and attributed
                and _is_phase2_static_liveness_warning(line)
            ):
                observed_engine_warnings.append(f"{name}: {line.strip()}")
            elif attributed or (
                duplicate and any(token in context for token in PROJECT_TOKENS)
            ):
                blocking.append(f"{name}: {line.strip()}")
    return (
        list(dict.fromkeys(line for line in blocking if line.strip())),
        list(
            dict.fromkeys(
                line for line in observed_engine_warnings if line.strip()
            )
        ),
    )


def native_loader_smoke_readiness(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    timeout_s: float = NATIVE_LOADER_READINESS_TIMEOUT_S,
    stable_observations: int = NATIVE_LOADER_STABLE_OBSERVATIONS,
    poll_interval_s: float = 0.1,
) -> dict[str, object]:
    """Prove a stable exact-build application-main loader boundary.

    This intentionally does not require ``map_ready`` or a played character.
    It proves only that the injected native bridge has reached a paused,
    application-main-owned semantic prefix after CK3's data loader.  The
    caller may then inspect loader diagnostics, but must not claim gameplay
    acceptance from this boundary.
    """

    evidence_path = artifacts / "01_loader_native_readiness.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "exact_build_application_main_loader_smoke_only",
        "tracked_ck3_pid": tracked_ck3_pid,
        "required_stable_observations": stable_observations,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "log_character_id_used": False,
        "gameplay_acceptance_executed": False,
        "gameplay_green_claimed": False,
        "map_ready_required": False,
        "played_character_required": False,
        "observations": [],
        "last_capabilities": None,
        "last_snapshot": None,
        "checks": {},
        "stable_binding": None,
        "failure_reason": None,
    }
    if timeout_s <= 0 or stable_observations < 2 or poll_interval_s < 0:
        raise ValueError("loader readiness timing parameters are invalid")

    deadline = time.monotonic() + timeout_s
    stable_key: tuple[object, ...] | None = None
    stable_rows: list[dict[str, object]] = []
    last_sequence: int | None = None
    last_pump_epochs: int | None = None
    last_failed_checks: list[str] = ["native bridge did not publish readiness"]
    observations = evidence["observations"]
    if not isinstance(observations, list):
        raise RuntimeError("loader readiness evidence schema is invalid")

    try:
        while time.monotonic() < deadline:
            capabilities: dict[str, object] | None = None
            snapshot: dict[str, object] | None = None
            try:
                candidate_capabilities = service.capabilities()
                if isinstance(candidate_capabilities, dict):
                    capabilities = candidate_capabilities
                    evidence["last_capabilities"] = capabilities
                else:
                    raise TypeError("capabilities response is not an object")
                candidate_snapshot = service.snapshot()
                if isinstance(candidate_snapshot, dict):
                    snapshot = candidate_snapshot
                    evidence["last_snapshot"] = snapshot
                else:
                    raise TypeError("snapshot response is not an object")
            except Exception as error:
                last_failed_checks = [
                    f"{type(error).__name__}: {error}"
                ]
                if poll_interval_s:
                    time.sleep(poll_interval_s)
                continue

            diagnostics_value = capabilities.get("diagnostics")
            diagnostics = (
                diagnostics_value
                if isinstance(diagnostics_value, dict)
                else {}
            )
            snapshot_diagnostics_value = snapshot.get("diagnostics")
            snapshot_diagnostics = (
                snapshot_diagnostics_value
                if isinstance(snapshot_diagnostics_value, dict)
                else {}
            )
            hello_value = diagnostics.get("hello")
            hello = hello_value if isinstance(hello_value, dict) else {}
            heartbeat_value = diagnostics.get("last_heartbeat")
            heartbeat = (
                heartbeat_value
                if isinstance(heartbeat_value, dict)
                else {}
            )
            mailbox_value = heartbeat.get("main_thread_query_mailbox_v1")
            mailbox = (
                mailbox_value if isinstance(mailbox_value, dict) else {}
            )
            connection_generation = diagnostics.get(
                "connection_generation"
            )
            heartbeat_sequence = heartbeat.get("sequence")
            pump_epochs = mailbox.get("pump_epochs")
            owner_tid = mailbox.get("owner_tid")
            current_tid = mailbox.get("current_tid")

            checks = {
                "native_headless_mode": capabilities.get("mode")
                == NATIVE_BRIDGE_MODE,
                "native_headless_backend": capabilities.get("backend_id")
                == NATIVE_BRIDGE_MODE,
                "headless": capabilities.get("headless") is True,
                "visual_fallback_disabled": capabilities.get(
                    "visual_fallback"
                )
                is False,
                "transport_ready": capabilities.get("transport_ready")
                is True,
                "snapshot_available": capabilities.get("snapshot") is True,
                "connected": diagnostics.get("connected") is True,
                "semantic_state_available": diagnostics.get(
                    "semantic_state_available"
                )
                is True,
                "tracked_ck3_pid_matches_bridge": diagnostics.get(
                    "bridge_pid"
                )
                == tracked_ck3_pid,
                "positive_connection_generation": isinstance(
                    connection_generation, int
                )
                and not isinstance(connection_generation, bool)
                and connection_generation > 0,
                "snapshot_transport_binding_matches": (
                    snapshot_diagnostics.get("bridge_pid")
                    == tracked_ck3_pid
                    and snapshot_diagnostics.get("connection_generation")
                    == connection_generation
                ),
                "exact_game_version": hello.get("expected_ck3_version")
                == EXPECTED_GAME_VERSION,
                "exact_executable_sha256": str(
                    hello.get("expected_ck3_sha256", "")
                ).lower()
                == EXPECTED_EXE_SHA256,
                "exact_build_adapter_ready": hello.get("ck3_build_match")
                is True
                and hello.get("game_adapter_status") == "ready",
                "heartbeat_bound_to_process": heartbeat.get("pid")
                == tracked_ck3_pid,
                "positive_heartbeat_sequence": isinstance(
                    heartbeat_sequence, int
                )
                and not isinstance(heartbeat_sequence, bool)
                and heartbeat_sequence > 0,
                "main_thread_mailbox_installed": mailbox.get("installed")
                is True,
                "main_thread_mailbox_not_stopping": mailbox.get("stop")
                is False,
                "main_thread_mailbox_failure_free": mailbox.get("failure")
                == 0,
                "main_thread_mailbox_ready": mailbox.get("ready") is True,
                "main_thread_executor_enabled": mailbox.get(
                    "executor_submission_enabled"
                )
                is True,
                "main_thread_stamp_read": mailbox.get(
                    "stamp_read_success"
                )
                is True,
                "positive_pump_epoch": isinstance(pump_epochs, int)
                and not isinstance(pump_epochs, bool)
                and pump_epochs > 0,
                "consecutive_main_thread_proof": isinstance(
                    mailbox.get("consecutive_verified"), int
                )
                and not isinstance(
                    mailbox.get("consecutive_verified"), bool
                )
                and mailbox.get("consecutive_verified", 0) >= 2,
                "main_thread_identity_consistent": isinstance(
                    owner_tid, int
                )
                and not isinstance(owner_tid, bool)
                and owner_tid > 0
                and owner_tid == current_tid,
                "application_state_pointers_available": isinstance(
                    mailbox.get("jomini_state"), int
                )
                and not isinstance(mailbox.get("jomini_state"), bool)
                and mailbox.get("jomini_state", 0) > 0
                and isinstance(mailbox.get("game_state"), int)
                and not isinstance(mailbox.get("game_state"), bool)
                and mailbox.get("game_state", 0) > 0,
                "semantic_snapshot_identity_available": isinstance(
                    snapshot.get("snapshot_id"), str
                )
                and bool(snapshot.get("snapshot_id"))
                and isinstance(snapshot.get("revision"), int)
                and not isinstance(snapshot.get("revision"), bool)
                and snapshot.get("revision", -1) >= 0
                and isinstance(snapshot.get("native_revision"), int)
                and not isinstance(snapshot.get("native_revision"), bool)
                and snapshot.get("native_revision", 0) > 0,
                "semantic_prefix_available": isinstance(
                    snapshot.get("date_raw"), int
                )
                and not isinstance(snapshot.get("date_raw"), bool)
                and isinstance(snapshot.get("map_ready"), bool),
                "paused_application_main": snapshot.get("paused") is True
                and mailbox.get("paused") is True,
                "mailbox_snapshot_date_matches": mailbox.get("date_raw")
                == snapshot.get("date_raw"),
            }
            evidence["checks"] = checks
            last_failed_checks = [
                key for key, value in checks.items() if value is not True
            ]
            if last_failed_checks:
                stable_key = None
                stable_rows = []
                last_sequence = None
                last_pump_epochs = None
                if poll_interval_s:
                    time.sleep(poll_interval_s)
                continue

            candidate_key = (
                tracked_ck3_pid,
                connection_generation,
                snapshot.get("date_raw"),
                snapshot.get("paused"),
                snapshot.get("map_ready"),
                snapshot.get("local_player_id"),
                owner_tid,
                mailbox.get("jomini_state"),
                mailbox.get("game_state"),
            )
            if candidate_key != stable_key:
                stable_key = candidate_key
                stable_rows = []
                last_sequence = None
                last_pump_epochs = None
            if (
                last_sequence is None
                or (
                    isinstance(heartbeat_sequence, int)
                    and isinstance(pump_epochs, int)
                    and heartbeat_sequence > last_sequence
                    and pump_epochs > (
                        last_pump_epochs
                        if isinstance(last_pump_epochs, int)
                        else -1
                    )
                )
            ):
                row = {
                    "heartbeat_sequence": heartbeat_sequence,
                    "pump_epochs": pump_epochs,
                    "consecutive_verified": mailbox.get(
                        "consecutive_verified"
                    ),
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "revision": snapshot.get("revision"),
                    "native_revision": snapshot.get("native_revision"),
                    "date_raw": snapshot.get("date_raw"),
                    "paused": snapshot.get("paused"),
                    "map_ready": snapshot.get("map_ready"),
                    "connection_generation": connection_generation,
                }
                stable_rows.append(row)
                observations.append(row)
                if len(observations) > 64:
                    del observations[:-64]
                last_sequence = int(heartbeat_sequence)
                last_pump_epochs = int(pump_epochs)
            if len(stable_rows) >= stable_observations:
                evidence["result"] = "GREEN"
                evidence["stable_binding"] = {
                    "bridge_pid": tracked_ck3_pid,
                    "connection_generation": connection_generation,
                    "date_raw": snapshot.get("date_raw"),
                    "paused": snapshot.get("paused"),
                    "map_ready": snapshot.get("map_ready"),
                    "local_player_id": snapshot.get("local_player_id"),
                    "owner_thread_id": owner_tid,
                    "jomini_state": mailbox.get("jomini_state"),
                    "game_state": mailbox.get("game_state"),
                    "first_heartbeat_sequence": stable_rows[0][
                        "heartbeat_sequence"
                    ],
                    "last_heartbeat_sequence": stable_rows[-1][
                        "heartbeat_sequence"
                    ],
                    "first_pump_epoch": stable_rows[0]["pump_epochs"],
                    "last_pump_epoch": stable_rows[-1]["pump_epochs"],
                    "stable_observation_count": len(stable_rows),
                }
                evidence["failure_reason"] = None
                write_json(evidence_path, evidence)
                return evidence
            if poll_interval_s:
                time.sleep(poll_interval_s)

        reason = ", ".join(last_failed_checks)
        if not last_failed_checks:
            reason = (
                "native heartbeat/pump epochs did not advance across "
                f"{stable_observations} stable observations"
            )
        raise acceptance.RunnerError(
            "native loader-smoke readiness timed out: " + reason
        )
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"native loader-smoke readiness failed: {error}"
        ) from error


def start_phase2_native_session_supervisor(
    spec: EnvironmentSpec,
    native_bridge: NativeBridgeLaunchConfig,
    *,
    frontend_first_load_save_name: str | None = None,
    frontend_first_timeout_seconds: float = (
        NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS
    ),
) -> dict[str, object]:
    """Start the production pure-native lifecycle owner for phase two only."""

    _validate_phase2_frontend_first_options(
        frontend_first_load_save_name,
        frontend_first_timeout_seconds,
        phase2_runtime_mode=True,
    )

    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}

    def supervise() -> None:
        try:
            native_session_options: dict[str, object] = {}
            if frontend_first_load_save_name is not None:
                native_session_options = {
                    "frontend_first_load_save_name": frontend_first_load_save_name,
                    "frontend_first_timeout_seconds": float(
                        frontend_first_timeout_seconds
                    ),
                }
            session_state["report"] = native_session(
                spec,
                timeout_seconds=PHASE2_SUPERVISOR_RUNTIME_TIMEOUT_S,
                native_bridge=native_bridge,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                stop_event=stop_event,
                # ZhongGuo owns an independent bootstrap/runtime identity/mount
                # gate.  The generic verifier is intentionally bound to the
                # Eternal Recurrence singleton profile; restore relaunches were
                # already unconditionally verified-prepared-profile=False.
                verify_prepared_profile=False,
                **native_session_options,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    session_thread = threading.Thread(
        target=supervise,
        name="zg361-phase2-native-session",
        daemon=False,
    )
    session_thread.start()
    return {
        "stop_event": stop_event,
        "session_done": session_done,
        "session_state": session_state,
        "session_thread": session_thread,
        "frontend_first_load_save_name": frontend_first_load_save_name,
        "frontend_first_timeout_seconds": (
            float(frontend_first_timeout_seconds)
            if frontend_first_load_save_name is not None
            else None
        ),
        "frontend_first_enabled": frontend_first_load_save_name is not None,
        "frontend_first_evidence_path": (
            str(
                (
                    spec.state_dir
                    / "native-session"
                    / "frontend-first-warmup.json"
                ).resolve()
            )
            if frontend_first_load_save_name is not None
            else None
        ),
    }


def _validate_phase2_frontend_first_options(
    load_save_name: str | None,
    timeout_seconds: float,
    *,
    phase2_runtime_mode: bool,
) -> None:
    """Validate the opt-in startup choreography before creating any outputs."""

    if load_save_name is None:
        return
    if not phase2_runtime_mode:
        raise acceptance.RunnerError(
            "frontend-first warm-up is only available for phase-two runtime modes"
        )
    if (
        not isinstance(load_save_name, str)
        or not load_save_name
        or Path(load_save_name).name != load_save_name
        or Path(load_save_name).suffix
        or any(character in load_save_name for character in ("/", "\\", "\0"))
    ):
        raise acceptance.RunnerError(
            "phase-two frontend-first load save name must be one basename "
            "without a path or extension"
        )
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise acceptance.RunnerError(
            "phase-two frontend-first timeout must be finite and positive"
        )


def wait_for_phase2_native_session_binding(
    service: GameplayBridgeService,
    supervisor: dict[str, object],
    artifacts: Path,
    *,
    timeout_s: float = PHASE2_SUPERVISOR_READINESS_TIMEOUT_S,
    poll_interval_s: float = 0.05,
) -> dict[str, object]:
    """Discover the first managed PID through MCP without visual navigation."""

    evidence_path = artifacts / "00_phase2_native_session_start.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_managed_native_session_start",
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "binding": None,
        "last_capabilities": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    if timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("phase-two supervisor readiness timing is invalid")
    frontend_first_enabled = supervisor.get("frontend_first_enabled") is True
    frontend_first_evidence_path: Path | None = None
    if frontend_first_enabled:
        raw_evidence_path = supervisor.get("frontend_first_evidence_path")
        if not isinstance(raw_evidence_path, str) or not raw_evidence_path:
            raise ValueError(
                "phase-two frontend-first supervisor lacks its evidence path"
            )
        frontend_first_evidence_path = Path(raw_evidence_path).resolve()
        evidence["frontend_first"] = {
            "enabled": True,
            "load_save_name": supervisor.get("frontend_first_load_save_name"),
            "evidence_path": str(frontend_first_evidence_path),
            "warmup": None,
        }
    else:
        evidence["frontend_first"] = {"enabled": False}
    session_done = supervisor.get("session_done")
    session_state = supervisor.get("session_state")
    session_thread = supervisor.get("session_thread")
    if not (
        isinstance(session_done, threading.Event)
        and isinstance(session_state, dict)
        and isinstance(session_thread, threading.Thread)
    ):
        raise ValueError("phase-two supervisor handle is malformed")
    deadline = time.monotonic() + timeout_s
    last_error = "native bridge has not published a connected PID"
    try:
        while time.monotonic() < deadline:
            if session_done.is_set():
                raise acceptance.RunnerError(
                    "phase-two native_session exited before MCP binding: "
                    + str(
                        session_state.get("error")
                        or session_state.get("report")
                        or "no session report"
                    )
                )
            try:
                frontend_warmup: dict[str, object] | None = None
                if frontend_first_enabled:
                    try:
                        assert frontend_first_evidence_path is not None
                        loaded_warmup = json.loads(
                            frontend_first_evidence_path.read_text(
                                encoding="utf-8"
                            )
                        )
                        if not isinstance(loaded_warmup, dict):
                            raise TypeError("warm-up evidence is not an object")
                        frontend_warmup = loaded_warmup
                        evidence["frontend_first"]["warmup"] = loaded_warmup
                        warmup_status = loaded_warmup.get("status")
                        if warmup_status == "failed":
                            raise acceptance.RunnerError(
                                "frontend-first warm-up failed: "
                                + str(loaded_warmup.get("failure_reason"))
                            )
                        if warmup_status != "ready":
                            last_error = (
                                "frontend-first warm-up status is "
                                f"{warmup_status!r}"
                            )
                            if poll_interval_s:
                                time.sleep(poll_interval_s)
                            continue
                    except FileNotFoundError:
                        last_error = "frontend-first warm-up evidence is pending"
                        if poll_interval_s:
                            time.sleep(poll_interval_s)
                        continue
                capabilities = service.capabilities()
                if not isinstance(capabilities, dict):
                    raise TypeError("capabilities response is not an object")
                evidence["last_capabilities"] = capabilities
                diagnostics_value = capabilities.get("diagnostics")
                diagnostics = (
                    diagnostics_value
                    if isinstance(diagnostics_value, dict)
                    else {}
                )
                bridge_pid = diagnostics.get("bridge_pid")
                connection_generation = diagnostics.get(
                    "connection_generation"
                )
                checks = {
                    "supervisor_thread_alive": session_thread.is_alive(),
                    "native_headless_mode": capabilities.get("mode")
                    == NATIVE_BRIDGE_MODE,
                    "native_headless_backend": capabilities.get("backend_id")
                    == NATIVE_BRIDGE_MODE,
                    "visual_fallback_disabled": capabilities.get(
                        "visual_fallback"
                    )
                    is False,
                    "connected": diagnostics.get("connected") is True,
                    "positive_bridge_pid": isinstance(bridge_pid, int)
                    and not isinstance(bridge_pid, bool)
                    and bridge_pid > 0,
                    "initial_connection_generation_one": isinstance(
                        connection_generation, int
                    )
                    and not isinstance(connection_generation, bool)
                    and connection_generation == 1,
                }
                if frontend_first_enabled:
                    expected_final_pid = (
                        frontend_warmup.get("final_pid")
                        if isinstance(frontend_warmup, dict)
                        else None
                    )
                    checks.update(
                        {
                            "frontend_first_warmup_ready": isinstance(
                                frontend_warmup, dict
                            )
                            and frontend_warmup.get("status") == "ready",
                            "frontend_first_final_pid_matches": isinstance(
                                expected_final_pid, int
                            )
                            and not isinstance(expected_final_pid, bool)
                            and bridge_pid == expected_final_pid,
                        }
                    )
                if all(checks.values()):
                    binding = {
                        "bridge_pid": bridge_pid,
                        "connection_generation": connection_generation,
                        "checks": checks,
                    }
                    evidence["result"] = "GREEN"
                    evidence["binding"] = binding
                    write_json(evidence_path, evidence)
                    return binding
                last_error = ", ".join(
                    label for label, passed in checks.items() if not passed
                )
            except acceptance.RunnerError:
                # A typed warm-up failure is terminal.  Do not convert it to
                # a generic binding timeout while the supervisor is already
                # known to have failed.
                raise
            except Exception as error:
                last_error = f"{type(error).__name__}: {error}"
            if poll_interval_s:
                time.sleep(poll_interval_s)
        raise acceptance.RunnerError(
            "phase-two native_session MCP binding timed out: " + last_error
        )
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two native_session binding failed: {error}"
        ) from error


class Phase2B2MatrixLifecycle:
    """Transfer one managed Phase2 session to the focused B2 matrix.

    Restore requests remain owned by ``native_session``.  This adapter only
    supplies the matrix with an independent process-inventory observation and
    one final supervisor stop.  The full four-restart shutdown receipts stay
    available for the focused outer cleanup verifier below.
    """

    def __init__(
        self,
        service: GameplayBridgeService,
        supervisor: dict[str, object],
    ) -> None:
        self.service = service
        self.supervisor = supervisor
        self.session_stopped = False
        self.stop_requested_pid: int | None = None
        self.pre_stop_capabilities: dict[str, object] | None = None
        self.session_report: dict[str, object] | None = None
        self.death_proofs: list[dict[str, object]] = []

    def _components(
        self,
    ) -> tuple[
        threading.Event,
        threading.Event,
        dict[str, object],
        threading.Thread,
    ]:
        stop_event = self.supervisor.get("stop_event")
        session_done = self.supervisor.get("session_done")
        session_state = self.supervisor.get("session_state")
        session_thread = self.supervisor.get("session_thread")
        if not (
            isinstance(stop_event, threading.Event)
            and isinstance(session_done, threading.Event)
            and isinstance(session_state, dict)
            and isinstance(session_thread, threading.Thread)
        ):
            raise ValueError("phase-two B2 supervisor handle is malformed")
        return stop_event, session_done, session_state, session_thread

    def prove_pid_dead(
        self,
        pid: int,
        *,
        reason: str,
        timeout_s: float = 30.0,
        poll_interval_s: float = 0.10,
    ) -> dict[str, object]:
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise ValueError("phase-two B2 cleanup PID must be positive")
        if timeout_s <= 0 or poll_interval_s <= 0:
            raise ValueError("phase-two B2 process-proof timing is invalid")
        started = time.monotonic()
        deadline = started + timeout_s
        observations: list[dict[str, object]] = []
        while True:
            if self.session_stopped and isinstance(self.session_report, dict):
                restart_value = self.session_report.get("restart_shutdowns")
                restarts = restart_value if isinstance(restart_value, list) else []
                receipts = [
                    row for row in restarts if isinstance(row, dict)
                ]
                final_shutdown = self.session_report.get("shutdown")
                if isinstance(final_shutdown, dict):
                    receipts.append(final_shutdown)
                matching = [row for row in receipts if row.get("ck3_pid") == pid]
                receipt = matching[0] if len(matching) == 1 else None
                checks = _phase2_shutdown_checks(
                    receipt,
                    expected_pid=pid,
                    prefix="retired_pid",
                )
                dead = len(matching) == 1 and all(checks.values())
                proof = {
                    "schema_version": 1,
                    "pid": pid,
                    "dead": dead,
                    "reason": reason,
                    "observation_source": "native_stop_tracked_tree_receipt",
                    "shutdown_receipt": receipt,
                    "checks": checks,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
                self.death_proofs.append(proof)
                return proof

            capabilities = self.service.capabilities()
            diagnostics = (
                capabilities.get("diagnostics")
                if isinstance(capabilities, dict)
                else None
            )
            current_pid = (
                diagnostics.get("bridge_pid")
                if isinstance(diagnostics, dict)
                and diagnostics.get("connected") is True
                else None
            )
            inventory = ck3_process_inventory()
            raw_pids = inventory.get("wmi_pids")
            observed_pids = (
                [
                    value
                    for value in raw_pids
                    if isinstance(value, int) and not isinstance(value, bool)
                ]
                if isinstance(raw_pids, list)
                else []
            )
            tasklist_pids = inventory.get("tasklist_pids")
            inventories_agree = (
                isinstance(tasklist_pids, list)
                and sorted(tasklist_pids) == sorted(observed_pids)
            )
            exact_managed_replacement = (
                isinstance(current_pid, int)
                and not isinstance(current_pid, bool)
                and current_pid > 0
                and observed_pids == [current_pid]
                and current_pid != pid
            )
            dead = inventories_agree and exact_managed_replacement
            observation = {
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "observed_ck3_pids": observed_pids,
                "current_bridge_pid": current_pid,
                "inventories_agree": inventories_agree,
                "target_absent": pid not in observed_pids,
                "exact_managed_replacement": exact_managed_replacement,
            }
            observations.append(observation)
            if dead or time.monotonic() >= deadline:
                proof = {
                    "schema_version": 1,
                    "pid": pid,
                    "dead": dead,
                    "reason": reason,
                    "observation_source": (
                        "retired_pid_absent_with_exact_managed_replacement"
                    ),
                    "observations": observations,
                    "final_inventory": inventory,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
                self.death_proofs.append(proof)
                return proof
            time.sleep(poll_interval_s)

    def stop_session(
        self,
        pid: int,
        *,
        reason: str,
    ) -> dict[str, object]:
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise ValueError("phase-two B2 final PID must be positive")
        if self.session_stopped:
            if self.stop_requested_pid != pid or self.session_report is None:
                raise acceptance.RunnerError(
                    "phase-two B2 matrix attempted a second mismatched stop"
                )
            shutdown = self.session_report.get("shutdown")
            if not isinstance(shutdown, dict):
                raise acceptance.RunnerError(
                    "phase-two B2 stopped session lacks its shutdown receipt"
                )
            return shutdown

        capabilities = self.service.capabilities()
        diagnostics = (
            capabilities.get("diagnostics")
            if isinstance(capabilities, dict)
            else None
        )
        if not (
            isinstance(capabilities, dict)
            and isinstance(diagnostics, dict)
            and diagnostics.get("connected") is True
            and diagnostics.get("bridge_pid") == pid
        ):
            raise acceptance.RunnerError(
                "phase-two B2 final stop is not bound to the requested PID"
            )
        self.pre_stop_capabilities = capabilities
        self.stop_requested_pid = pid
        stop_event, session_done, session_state, session_thread = (
            self._components()
        )
        stop_event.set()
        session_thread.join()
        if session_thread.is_alive() or not session_done.is_set():
            raise acceptance.RunnerError(
                "phase-two B2 native_session did not finish its final stop"
            )
        if session_state.get("error") is not None:
            raise acceptance.RunnerError(
                "phase-two B2 native_session final stop failed: "
                + str(session_state["error"])
            )
        report = session_state.get("report")
        if not isinstance(report, dict):
            raise acceptance.RunnerError(
                "phase-two B2 native_session final stop lacks a report"
            )
        self.session_report = report
        self.session_stopped = True
        shutdown = report.get("shutdown")
        if not isinstance(shutdown, dict):
            raise acceptance.RunnerError(
                "phase-two B2 native_session final stop lacks shutdown proof"
            )
        return shutdown

    def ensure_stopped(self, *, reason: str) -> dict[str, object]:
        """Finish exactly one supervisor stop, including an early RED path."""

        if self.session_stopped:
            if self.session_report is None:
                raise acceptance.RunnerError(
                    "phase-two B2 stopped session lost its report"
                )
            return self.session_report
        stop_event, session_done, session_state, session_thread = (
            self._components()
        )
        if session_done.is_set() and not session_thread.is_alive():
            if session_state.get("error") is not None:
                raise acceptance.RunnerError(
                    "phase-two B2 native_session exited with an error: "
                    + str(session_state["error"])
                )
            report = session_state.get("report")
            if not isinstance(report, dict):
                raise acceptance.RunnerError(
                    "phase-two B2 completed supervisor lacks its report"
                )
            self.session_report = report
            self.stop_requested_pid = (
                int(report["pid"])
                if isinstance(report.get("pid"), int)
                and not isinstance(report.get("pid"), bool)
                else None
            )
            self.session_stopped = True
            return report

        try:
            capabilities = self.service.capabilities()
            diagnostics = (
                capabilities.get("diagnostics")
                if isinstance(capabilities, dict)
                else None
            )
            current_pid = (
                diagnostics.get("bridge_pid")
                if isinstance(diagnostics, dict)
                and diagnostics.get("connected") is True
                else None
            )
            if (
                isinstance(current_pid, int)
                and not isinstance(current_pid, bool)
                and current_pid > 0
            ):
                self.stop_session(current_pid, reason=reason)
                assert self.session_report is not None
                return self.session_report
        except BaseException:
            # The bridge may disappear immediately after a typed RED.  The
            # supervisor remains the process owner and can still produce its
            # canonical stop_tracked report below.
            pass

        stop_event.set()
        session_thread.join()
        if session_thread.is_alive() or not session_done.is_set():
            raise acceptance.RunnerError(
                "phase-two B2 fallback supervisor stop did not finish"
            )
        if session_state.get("error") is not None:
            raise acceptance.RunnerError(
                "phase-two B2 fallback supervisor stop failed: "
                + str(session_state["error"])
            )
        report = session_state.get("report")
        if not isinstance(report, dict):
            raise acceptance.RunnerError(
                "phase-two B2 fallback supervisor stop lacks its report"
            )
        self.session_report = report
        self.stop_requested_pid = (
            int(report["pid"])
            if isinstance(report.get("pid"), int)
            and not isinstance(report.get("pid"), bool)
            else None
        )
        self.session_stopped = True
        return report


def _phase2_shutdown_checks(
    value: object,
    *,
    expected_pid: int | None,
    prefix: str,
) -> dict[str, bool]:
    shutdown = value if isinstance(value, dict) else {}
    inventory_value = shutdown.get("final_ck3_inventory")
    inventory = inventory_value if isinstance(inventory_value, dict) else {}
    processes = inventory.get("processes")
    control_value = shutdown.get("control_files_absent")
    control_files = control_value if isinstance(control_value, dict) else {}
    contract_errors = shutdown.get("contract_errors")
    return {
        f"{prefix}_object": isinstance(value, dict),
        f"{prefix}_pid_matches": expected_pid is not None
        and shutdown.get("ck3_pid") == expected_pid,
        f"{prefix}_ok": shutdown.get("ok") is True,
        f"{prefix}_cleanup_proven": shutdown.get("cleanup_proven") is True,
        f"{prefix}_tree_gone": shutdown.get("tree_gone") is True,
        f"{prefix}_job_empty": shutdown.get("job_active_processes_final") == 0,
        f"{prefix}_global_inventory_empty": isinstance(processes, list)
        and not processes,
        f"{prefix}_watchdog_absent": shutdown.get("watchdog_state_after")
        == "absent",
        f"{prefix}_control_files_absent": bool(control_files)
        and all(item is True for item in control_files.values()),
        f"{prefix}_contract_errors_empty": isinstance(contract_errors, list)
        and not contract_errors,
    }


def phase2_restore_queue_required(scenario_evidence: object) -> bool:
    """Return true only after a durable save ACK makes restore mandatory."""

    scenario = scenario_evidence if isinstance(scenario_evidence, dict) else {}
    lineage_value = scenario.get("save_restore_lineage")
    lineage = lineage_value if isinstance(lineage_value, dict) else {}
    save_value = lineage.get("save_result")
    save_result = save_value if isinstance(save_value, dict) else {}
    checkpoint_value = save_result.get("checkpoint")
    checkpoint = checkpoint_value if isinstance(checkpoint_value, dict) else {}
    return (
        save_result.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and isinstance(checkpoint.get("size"), int)
        and not isinstance(checkpoint.get("size"), bool)
        and checkpoint.get("size", 0) > 0
        and isinstance(checkpoint.get("sha256"), str)
        and re.fullmatch(r"[0-9A-Fa-f]{64}", checkpoint["sha256"])
        is not None
    )


def _phase2_expected_session_lineage(
    scenario_evidence: object,
) -> dict[str, object]:
    """Project the base restore plus every recorded Workforce restart.

    The original phase-two transaction owns the first two PID/generation
    entries.  The optional Workforce fixture starts on that second binding
    and records its activation, A/B/C, final, or failure-recovery restores.
    Keeping the duplicate join binding explicit in the source evidence makes
    the concatenation auditable while the returned full lineage contains it
    only once.
    """

    scenario = scenario_evidence if isinstance(scenario_evidence, dict) else {}
    base_value = scenario.get("save_restore_lineage")
    base = base_value if isinstance(base_value, dict) else {}
    base_pid_value = base.get("pid_lineage")
    base_generation_value = base.get("connection_generation_lineage")
    base_pids = list(base_pid_value) if isinstance(base_pid_value, list) else []
    base_generations = (
        list(base_generation_value)
        if isinstance(base_generation_value, list)
        else []
    )

    workforce_value = scenario.get(
        "workforce_collective_gameplay_action_cell"
    )
    workforce = workforce_value if isinstance(workforce_value, dict) else {}
    workforce_lineage_value = workforce.get("session_lineage")
    workforce_lineage = (
        workforce_lineage_value
        if isinstance(workforce_lineage_value, dict)
        else {}
    )
    workforce_pid_value = workforce_lineage.get("pid_lineage")
    workforce_generation_value = workforce_lineage.get(
        "connection_generation_lineage"
    )
    workforce_pids = (
        list(workforce_pid_value)
        if isinstance(workforce_pid_value, list)
        else []
    )
    workforce_generations = (
        list(workforce_generation_value)
        if isinstance(workforce_generation_value, list)
        else []
    )
    workforce_recorded = bool(workforce_pids or workforce_generations)
    join_matches = bool(
        base_pids
        and base_generations
        and workforce_pids
        and workforce_generations
        and workforce_pids[0] == base_pids[-1]
        and workforce_generations[0] == base_generations[-1]
    )
    full_pids = list(base_pids)
    full_generations = list(base_generations)
    if workforce_recorded:
        # Append even when the join is malformed.  The explicit join check
        # below will make cleanup/liveness RED, while retaining every claimed
        # retired process in the diagnostic projection.
        full_pids.extend(workforce_pids[1:])
        full_generations.extend(workforce_generations[1:])
    return {
        "base": base,
        "workforce_cell": workforce,
        "workforce_lineage": workforce_lineage,
        "base_pid_lineage": base_pids,
        "base_connection_generation_lineage": base_generations,
        "workforce_pid_lineage": workforce_pids,
        "workforce_connection_generation_lineage": workforce_generations,
        "workforce_recorded": workforce_recorded,
        "workforce_join_matches_base_final": (
            join_matches if workforce_recorded else True
        ),
        "pid_lineage": full_pids,
        "connection_generation_lineage": full_generations,
    }


def prove_phase2_native_session_cleanup(
    session_report: object,
    artifacts: Path,
    *,
    initial_pid: int | None,
    initial_generation: int | None,
    expected_pipe: str,
    scenario_evidence: object,
    final_capabilities: object,
    session_error: object = None,
    supervisor_stopped: bool,
) -> dict[str, object]:
    """Prove every managed PID from the base and optional Workforce restores."""

    evidence_path = artifacts / "09_phase2_native_session_cleanup.json"
    report = session_report if isinstance(session_report, dict) else {}
    scenario = scenario_evidence if isinstance(scenario_evidence, dict) else {}
    restore_expected = phase2_restore_queue_required(scenario)
    lineage_projection = _phase2_expected_session_lineage(scenario)
    lineage = lineage_projection["base"]
    if not isinstance(lineage, dict):
        lineage = {}
    restore_value = lineage.get("restore_result")
    restore_result = restore_value if isinstance(restore_value, dict) else {}
    lifecycle_value = restore_result.get("lifecycle")
    lifecycle = lifecycle_value if isinstance(lifecycle_value, dict) else {}
    restart_value = report.get("restart_shutdowns")
    restart_shutdowns = restart_value if isinstance(restart_value, list) else []
    second_pid_value = lineage.get("second_pid")
    second_pid = (
        second_pid_value
        if isinstance(second_pid_value, int)
        and not isinstance(second_pid_value, bool)
        and second_pid_value > 0
        else None
    )
    second_generation_value = lineage.get("second_connection_generation")
    second_generation = (
        second_generation_value
        if isinstance(second_generation_value, int)
        and not isinstance(second_generation_value, bool)
        and second_generation_value > 0
        else None
    )
    final_capabilities_value = (
        final_capabilities if isinstance(final_capabilities, dict) else {}
    )
    final_diagnostics_value = final_capabilities_value.get("diagnostics")
    final_diagnostics = (
        final_diagnostics_value
        if isinstance(final_diagnostics_value, dict)
        else {}
    )
    pid_lineage_value = lineage_projection.get("pid_lineage")
    pid_lineage = (
        pid_lineage_value if isinstance(pid_lineage_value, list) else []
    )
    generation_lineage_value = lineage_projection.get(
        "connection_generation_lineage"
    )
    generation_lineage = (
        generation_lineage_value
        if isinstance(generation_lineage_value, list)
        else []
    )
    expected_final_pid = (
        pid_lineage[-1]
        if restore_expected and pid_lineage
        else initial_pid
    )
    expected_final_generation = (
        generation_lineage[-1]
        if restore_expected and generation_lineage
        else initial_generation
    )
    checks: dict[str, bool] = {
        "supervisor_stopped": supervisor_stopped is True,
        "session_error_absent": session_error is None,
        "session_report_object": isinstance(session_report, dict),
        "session_kind": report.get("kind") == "ck3_native_headless_session",
        "session_mode": report.get("mode") == NATIVE_BRIDGE_MODE,
        "session_pipe": report.get("pipe") == expected_pipe,
        "session_report_ok": report.get("ok") is True,
        "session_exit_reason_stop": report.get("exit_reason") == "stop",
        "session_process_exit_code_clean": report.get("process_exit_code")
        in (None, 0),
        "initial_pid_positive": isinstance(initial_pid, int)
        and not isinstance(initial_pid, bool)
        and initial_pid > 0,
        "initial_generation_positive": isinstance(initial_generation, int)
        and not isinstance(initial_generation, bool)
        and initial_generation > 0,
        "final_capabilities_object": isinstance(final_capabilities, dict),
        "final_capabilities_connected": final_diagnostics.get("connected")
        is True,
        "final_capabilities_pid_matches": final_diagnostics.get("bridge_pid")
        == expected_final_pid,
        "final_capabilities_generation_matches": final_diagnostics.get(
            "connection_generation"
        )
        == expected_final_generation,
    }
    restart_count = report.get("restart_count")
    if restore_expected:
        checks.update(
            {
                "lineage_green": lineage.get("result") == "GREEN",
                "lineage_two_pid_proven": lineage.get(
                    "two_pid_lineage_proven"
                )
                is True,
                "lineage_first_pid_matches": lineage.get("first_pid")
                == initial_pid,
                "lineage_pid_pair_exact": lineage.get("pid_lineage")
                == [initial_pid, second_pid]
                and len({initial_pid, second_pid}) == 2,
                "lineage_second_pid_distinct": second_pid is not None
                and second_pid != initial_pid,
                "lineage_first_generation_matches": lineage.get(
                    "first_connection_generation"
                )
                == initial_generation,
                "lineage_generation_advanced_once": second_generation
                == initial_generation + 1
                if isinstance(initial_generation, int)
                else False,
                "lineage_generation_pair_exact": lineage.get(
                    "connection_generation_lineage"
                )
                == [initial_generation, second_generation],
                "restore_acknowledged": restore_result.get("accepted") is True
                and restore_result.get("status") == "restored"
                and restore_result.get("source")
                == "native-session-lifecycle-queue",
                "restore_lifecycle_pid_pair_matches": lifecycle.get(
                    "previous_pid"
                )
                == initial_pid
                and lifecycle.get("pid") == second_pid,
                "restore_lifecycle_intent": lifecycle.get(
                    "lifecycle_intent"
                )
                == "restore",
                "restore_request_id_present": isinstance(
                    lifecycle.get("request_id"), str
                )
                and bool(lifecycle.get("request_id")),
                "final_capabilities_bound_second_pid": isinstance(
                    lineage.get("checks"), dict
                )
                and lineage["checks"].get(
                    "final_capabilities_bind_second_pid"
                )
                is True,
            }
        )
        if len(pid_lineage) <= 2:
            checks.update(
                {
                    "restore_queue_consumed_once": restart_count == 1
                    and len(restart_shutdowns) == 1,
                    "restart_count_exactly_one": restart_count == 1,
                    "one_old_pid_shutdown": len(restart_shutdowns) == 1,
                    "session_last_pid_matches_second": report.get("pid")
                    == second_pid,
                }
            )
            old_shutdown = (
                restart_shutdowns[0]
                if len(restart_shutdowns) == 1
                else None
            )
            checks.update(
                _phase2_shutdown_checks(
                    old_shutdown,
                    expected_pid=initial_pid,
                    prefix="old_pid_shutdown",
                )
            )
            checks.update(
                _phase2_shutdown_checks(
                    report.get("shutdown"),
                    expected_pid=second_pid,
                    prefix="new_pid_shutdown",
                )
            )
        else:
            workforce_lineage_value = lineage_projection.get(
                "workforce_lineage"
            )
            workforce_lineage = (
                workforce_lineage_value
                if isinstance(workforce_lineage_value, dict)
                else {}
            )
            restore_records_value = workforce_lineage.get("restore_records")
            restore_records = (
                restore_records_value
                if isinstance(restore_records_value, list)
                else []
            )
            expected_restart_count = len(pid_lineage) - 1
            positive_pid_lineage = all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
                for value in pid_lineage
            )
            positive_generation_lineage = bool(generation_lineage) and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
                for value in generation_lineage
            )
            base_pid_value = lineage_projection.get("base_pid_lineage")
            base_pids = (
                base_pid_value if isinstance(base_pid_value, list) else []
            )
            base_count = len(base_pids)
            lifecycle_chain = (
                base_count == 2
                and len(pid_lineage) == len(generation_lineage)
                and len(restore_records)
                == len(pid_lineage) - base_count
                and all(
                    isinstance(row, dict)
                    and isinstance(row.get("before"), dict)
                    and isinstance(row.get("after"), dict)
                    and isinstance(row.get("lifecycle"), dict)
                    and row["before"].get("bridge_pid")
                    == pid_lineage[index + base_count - 1]
                    and row["after"].get("bridge_pid")
                    == pid_lineage[index + base_count]
                    and row["before"].get("connection_generation")
                    == generation_lineage[index + base_count - 1]
                    and row["after"].get("connection_generation")
                    == generation_lineage[index + base_count]
                    and row["lifecycle"].get("previous_pid")
                    == pid_lineage[index + base_count - 1]
                    and row["lifecycle"].get("pid")
                    == pid_lineage[index + base_count]
                    for index, row in enumerate(restore_records)
                )
            )
            checks.update(
                {
                    "workforce_restart_lineage_recorded": (
                        lineage_projection.get("workforce_recorded") is True
                    ),
                    "workforce_join_matches_base_final": (
                        lineage_projection.get(
                            "workforce_join_matches_base_final"
                        )
                        is True
                    ),
                    "full_pid_lineage_positive": positive_pid_lineage,
                    "full_pid_lineage_unique": positive_pid_lineage
                    and len(set(pid_lineage)) == len(pid_lineage),
                    "full_generation_lineage_positive": (
                        positive_generation_lineage
                    ),
                    "full_generation_lineage_consecutive": (
                        positive_generation_lineage
                        and generation_lineage
                        == list(
                            range(
                                generation_lineage[0],
                                generation_lineage[0]
                                + len(generation_lineage),
                            )
                        )
                    ),
                    "full_lineage_lengths_match": len(pid_lineage)
                    == len(generation_lineage),
                    "full_lineage_starts_at_initial": bool(pid_lineage)
                    and bool(generation_lineage)
                    and pid_lineage[0] == initial_pid
                    and generation_lineage[0] == initial_generation,
                    "restart_count_matches_full_lineage": restart_count
                    == expected_restart_count,
                    "retired_shutdown_count_matches_full_lineage": len(
                        restart_shutdowns
                    )
                    == expected_restart_count,
                    "session_last_pid_matches_full_lineage": report.get(
                        "pid"
                    )
                    == expected_final_pid,
                    "workforce_restore_lifecycle_chain_exact": lifecycle_chain,
                }
            )
            for index, retired_pid in enumerate(pid_lineage[:-1]):
                shutdown = (
                    restart_shutdowns[index]
                    if index < len(restart_shutdowns)
                    else None
                )
                checks.update(
                    _phase2_shutdown_checks(
                        shutdown,
                        expected_pid=(
                            retired_pid
                            if isinstance(retired_pid, int)
                            and not isinstance(retired_pid, bool)
                            else None
                        ),
                        prefix=f"retired_pid_{index + 1}_shutdown",
                    )
                )
            checks.update(
                _phase2_shutdown_checks(
                    report.get("shutdown"),
                    expected_pid=(
                        expected_final_pid
                        if isinstance(expected_final_pid, int)
                        and not isinstance(expected_final_pid, bool)
                        else None
                    ),
                    prefix="final_pid_shutdown",
                )
            )
    else:
        checks.update(
            {
                "prestart_restart_count_zero": restart_count == 0,
                "prestart_restart_shutdowns_empty": not restart_shutdowns,
                "session_last_pid_matches_initial": report.get("pid")
                == initial_pid,
            }
        )
        checks.update(
            _phase2_shutdown_checks(
                report.get("shutdown"),
                expected_pid=initial_pid,
                prefix="initial_pid_shutdown",
            )
        )
    failed = [label for label, passed in checks.items() if passed is not True]
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "GREEN" if not failed else "RED",
        "scope": "phase2_managed_native_session_cleanup",
        "mcp_only": True,
        "restore_expected": restore_expected,
        "initial_pid": initial_pid,
        "initial_generation": initial_generation,
        "second_pid": second_pid,
        "second_generation": second_generation,
        "pid_lineage": pid_lineage if restore_expected else [initial_pid],
        "connection_generation_lineage": (
            generation_lineage if restore_expected else [initial_generation]
        ),
        "expected_final_pid": expected_final_pid,
        "expected_final_generation": expected_final_generation,
        "lineage_projection": lineage_projection,
        "expected_pipe": expected_pipe,
        "final_capabilities": (
            final_capabilities if isinstance(final_capabilities, dict) else None
        ),
        "checks": checks,
        "failed_checks": failed,
        "session_error": session_error,
        "session_report": report if isinstance(session_report, dict) else None,
        "failure_reason": (
            None
            if not failed
            else "phase-two native_session cleanup RED: " + ", ".join(failed)
        ),
    }
    write_json(evidence_path, evidence)
    if failed:
        raise acceptance.RunnerError(str(evidence["failure_reason"]))
    return evidence


def stop_phase2_native_session_supervisor(
    supervisor: dict[str, object],
    artifacts: Path,
    *,
    initial_pid: int | None,
    initial_generation: int | None,
    expected_pipe: str,
    scenario_evidence: object,
    final_capabilities: object,
) -> dict[str, object]:
    """Stop the managed owner and turn its session report into cleanup proof."""

    stop_event = supervisor.get("stop_event")
    session_done = supervisor.get("session_done")
    session_state = supervisor.get("session_state")
    session_thread = supervisor.get("session_thread")
    if not (
        isinstance(stop_event, threading.Event)
        and isinstance(session_done, threading.Event)
        and isinstance(session_state, dict)
        and isinstance(session_thread, threading.Thread)
    ):
        raise ValueError("phase-two supervisor handle is malformed")
    stop_event.set()
    # native_session owns bounded stop_tracked calls for both the retired PID
    # and the final PID.  Do not close the shared driver or return while that
    # non-daemon lifecycle owner still holds its process/lock cleanup proof.
    session_thread.join()
    supervisor_stopped = not session_thread.is_alive() and session_done.is_set()
    return prove_phase2_native_session_cleanup(
        session_state.get("report"),
        artifacts,
        initial_pid=initial_pid,
        initial_generation=initial_generation,
        expected_pipe=expected_pipe,
        scenario_evidence=scenario_evidence,
        final_capabilities=final_capabilities,
        session_error=session_state.get("error"),
        supervisor_stopped=supervisor_stopped,
    )


def prove_phase2_b2_matrix_native_session_cleanup(
    lifecycle: Phase2B2MatrixLifecycle,
    artifacts: Path,
    *,
    initial_pid: int | None,
    initial_generation: int | None,
    expected_pipe: str,
    scenario_evidence: object,
) -> dict[str, object]:
    """Close the focused matrix's five-PID lifecycle without legacy gates."""

    evidence_path = artifacts / "09_phase2_native_session_cleanup.json"
    report = lifecycle.ensure_stopped(
        reason="focused B2 same-checkpoint outer cleanup"
    )
    scenario = scenario_evidence if isinstance(scenario_evidence, dict) else {}
    matrix_value = scenario.get("b2_same_checkpoint_matrix")
    matrix = matrix_value if isinstance(matrix_value, dict) else {}
    matrix_pids_value = matrix.get("pid_lineage")
    matrix_pids = (
        list(matrix_pids_value)
        if isinstance(matrix_pids_value, list)
        else []
    )
    matrix_generations_value = matrix.get("connection_generation_lineage")
    matrix_generations = (
        list(matrix_generations_value)
        if isinstance(matrix_generations_value, list)
        else []
    )
    restart_value = report.get("restart_shutdowns")
    restart_shutdowns = restart_value if isinstance(restart_value, list) else []
    final_shutdown = report.get("shutdown")
    shutdown_rows = [
        row for row in restart_shutdowns if isinstance(row, dict)
    ]
    if isinstance(final_shutdown, dict):
        shutdown_rows.append(final_shutdown)
    native_pid_lineage = [row.get("ck3_pid") for row in shutdown_rows]
    valid_native_pids = bool(native_pid_lineage) and all(
        isinstance(pid, int) and not isinstance(pid, bool) and pid > 0
        for pid in native_pid_lineage
    )
    receipt_checks: dict[str, dict[str, bool]] = {}
    for index, row in enumerate(shutdown_rows):
        label = (
            f"restart_{index + 1:02d}"
            if index < len(restart_shutdowns)
            else "final"
        )
        expected_pid = (
            int(row["ck3_pid"])
            if isinstance(row.get("ck3_pid"), int)
            and not isinstance(row.get("ck3_pid"), bool)
            else None
        )
        receipt_checks[label] = _phase2_shutdown_checks(
            row,
            expected_pid=expected_pid,
            prefix=label,
        )
    all_receipts_green = bool(receipt_checks) and all(
        all(checks.values()) for checks in receipt_checks.values()
    )
    pid_proofs = (
        [
            lifecycle.prove_pid_dead(
                int(pid), reason="focused B2 final native lineage audit"
            )
            for pid in native_pid_lineage
        ]
        if valid_native_pids
        else []
    )
    all_pid_proofs_green = (
        valid_native_pids
        and len(pid_proofs) == len(native_pid_lineage)
        and all(
            proof.get("pid") == pid and proof.get("dead") is True
            for pid, proof in zip(native_pid_lineage, pid_proofs)
        )
    )
    focused_green = (
        scenario.get("result") == "GREEN"
        and scenario.get("phase2_b2_same_checkpoint_complete") is True
        and matrix.get("result") == "GREEN"
    )
    final_capabilities = lifecycle.pre_stop_capabilities
    final_diagnostics = (
        final_capabilities.get("diagnostics")
        if isinstance(final_capabilities, dict)
        else None
    )
    checks: dict[str, bool] = {
        "session_report_object": isinstance(report, dict),
        "session_kind": report.get("kind") == "ck3_native_headless_session",
        "session_mode": report.get("mode") == NATIVE_BRIDGE_MODE,
        "session_pipe": report.get("pipe") == expected_pipe,
        "session_report_ok": report.get("ok") is True,
        "session_exit_reason_stop": report.get("exit_reason") == "stop",
        "session_process_exit_code_clean": report.get("process_exit_code")
        in (None, 0),
        "restart_count_matches_receipts": report.get("restart_count")
        == len(restart_shutdowns),
        "all_shutdown_receipts_present": len(shutdown_rows)
        == len(restart_shutdowns) + 1,
        "native_pid_lineage_positive": valid_native_pids,
        "native_pid_lineage_unique": valid_native_pids
        and len(set(native_pid_lineage)) == len(native_pid_lineage),
        "native_pid_lineage_starts_initial": bool(native_pid_lineage)
        and native_pid_lineage[0] == initial_pid,
        "session_report_pid_matches_final": bool(native_pid_lineage)
        and report.get("pid") == native_pid_lineage[-1],
        "all_native_shutdown_receipts_green": all_receipts_green,
        "all_native_pids_dead": all_pid_proofs_green,
        "matrix_pid_lineage_matches_native": not matrix_pids
        or matrix_pids == native_pid_lineage,
        "final_capabilities_bound_final_pid": isinstance(final_diagnostics, dict)
        and final_diagnostics.get("connected") is True
        and bool(native_pid_lineage)
        and final_diagnostics.get("bridge_pid") == native_pid_lineage[-1],
    }
    if focused_green:
        expected_generations = (
            list(
                range(
                    int(initial_generation),
                    int(initial_generation) + 5,
                )
            )
            if isinstance(initial_generation, int)
            and not isinstance(initial_generation, bool)
            and initial_generation > 0
            else []
        )
        checks.update(
            {
                "focused_matrix_result_green": True,
                "four_native_restores": report.get("restart_count") == 4
                and len(restart_shutdowns) == 4,
                "five_native_pids": len(native_pid_lineage) == 5,
                "five_matrix_pids": len(matrix_pids) == 5,
                "five_matrix_generations": len(matrix_generations) == 5,
                "matrix_generations_consecutive": matrix_generations
                == expected_generations,
                "final_capabilities_bound_final_generation": isinstance(
                    final_diagnostics, dict
                )
                and bool(matrix_generations)
                and final_diagnostics.get("connection_generation")
                == matrix_generations[-1],
                "matrix_cleanup_green": isinstance(matrix.get("cleanup"), dict)
                and matrix["cleanup"].get("result") == "GREEN",
                "matrix_all_managed_pids_dead": isinstance(
                    matrix.get("checks"), dict
                )
                and matrix["checks"].get("all_managed_pids_dead") is True,
            }
        )
    failed = [label for label, passed in checks.items() if passed is not True]
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "GREEN" if not failed else "RED",
        "scope": "phase2_focused_b2_same_checkpoint_native_session_cleanup",
        "mcp_only": True,
        "initial_pid": initial_pid,
        "initial_generation": initial_generation,
        "expected_pipe": expected_pipe,
        "focused_matrix_green": focused_green,
        "pid_lineage": native_pid_lineage,
        "connection_generation_lineage": matrix_generations,
        "matrix_pid_lineage": matrix_pids,
        "restart_shutdowns": restart_shutdowns,
        "final_shutdown": final_shutdown,
        "receipt_checks": receipt_checks,
        "pid_proofs": pid_proofs,
        "final_capabilities": final_capabilities,
        "checks": checks,
        "failed_checks": failed,
        "session_report": report,
        "failure_reason": (
            None
            if not failed
            else "focused B2 native_session cleanup RED: "
            + ", ".join(failed)
        ),
    }
    write_json(evidence_path, evidence)
    if failed:
        raise acceptance.RunnerError(str(evidence["failure_reason"]))
    return evidence


def finalize_phase2_promo_span_session_receipts(
    scenario_evidence: object,
    native_cleanup: object,
    artifacts: Path,
    *,
    driver_closed: bool,
    locks_released: bool,
) -> None:
    """Attach only the runner's completed cleanup proof to v2 span receipts."""

    if not isinstance(scenario_evidence, dict) or scenario_evidence.get(
        "span_session_contract_version"
    ) != 2:
        return
    cleanup = native_cleanup if isinstance(native_cleanup, Mapping) else {}
    checks = cleanup.get("checks")
    checks = checks if isinstance(checks, Mapping) else {}
    tree_checks = [
        value
        for key, value in checks.items()
        if str(key).endswith("_tree_gone")
    ]
    process_tree_gone = bool(tree_checks) and all(value is True for value in tree_checks)
    cleanup_path = Path(artifacts).resolve() / "09_phase2_native_session_cleanup.json"
    cleanup_record = None
    if cleanup_path.is_file():
        cleanup_record = {
            "path": str(cleanup_path),
            "bytes": cleanup_path.stat().st_size,
            "sha256": isolated.sha256_file(cleanup_path).upper(),
        }
    cleanup_green = (
        cleanup.get("result") == "GREEN"
        and not cleanup.get("failed_checks")
        and process_tree_gone
        and driver_closed is True
        and locks_released is True
        and cleanup_record is not None
    )
    rows = scenario_evidence.get("completed_spans")
    completed = rows if isinstance(rows, list) else []
    cleanup_pids = cleanup.get("pid_lineage")
    cleanup_generations = cleanup.get("connection_generation_lineage")
    cleanup_pids = cleanup_pids if isinstance(cleanup_pids, list) else []
    cleanup_generations = (
        cleanup_generations if isinstance(cleanup_generations, list) else []
    )
    for row in completed:
        if not isinstance(row, dict):
            continue
        session = row.get("session_evidence")
        if not isinstance(session, dict):
            continue
        session_cleanup_green = (
            cleanup_green
            and session.get("bridge_pid") in cleanup_pids
            and session.get("connection_generation") in cleanup_generations
        )
        session["cleanup"] = {
            "result": "GREEN" if session_cleanup_green else "RED",
            "session_id": session.get("session_id"),
            "bridge_pid": session.get("bridge_pid"),
            "connection_generation": session.get("connection_generation"),
            "process_tree_gone": process_tree_gone,
            "driver_closed": driver_closed is True,
            "locks_released": locks_released is True,
            "native_cleanup": cleanup_record,
        }
        session["result"] = "GREEN" if session_cleanup_green else "RED"
    if not (
        len(completed) == len(PHASE2_CAPTURE_SCENARIOS)
        and all(
            isinstance(row, Mapping)
            and isinstance(row.get("session_evidence"), Mapping)
            and row["session_evidence"].get("result") == "GREEN"
            for row in completed
        )
    ):
        raise acceptance.RunnerError(
            "phase-two span-session-v2 cleanup receipts are incomplete or RED"
        )


def phase2_runtime_capability_preflight(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    managed_restore_supervisor: bool = False,
    focused_b2_same_checkpoint: bool = False,
) -> dict[str, object]:
    """Fail before navigation unless the selected Phase2 MCP surface exists."""

    evidence_path = artifacts / "02_phase2_mcp_capabilities.json"
    required_bridge_capabilities = (
        {
            label: PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
            for label in PHASE2_B2_REQUIRED_BRIDGE_CAPABILITY_LABELS
        }
        if focused_b2_same_checkpoint
        else dict(PHASE2_REQUIRED_BRIDGE_CAPABILITIES)
    )
    required_query_flags = (
        {
            label: PHASE2_REQUIRED_QUERY_FLAGS[label]
            for label in PHASE2_B2_REQUIRED_QUERY_FLAG_LABELS
        }
        if focused_b2_same_checkpoint
        else dict(PHASE2_REQUIRED_QUERY_FLAGS)
    )
    required_action_steps = (
        {
            label: PHASE2_REQUIRED_ACTION_STEPS[label]
            for label in PHASE2_B2_REQUIRED_ACTION_STEP_LABELS
        }
        if focused_b2_same_checkpoint
        else dict(PHASE2_REQUIRED_ACTION_STEPS)
    )
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": (
            "focused_b2_same_checkpoint_mcp_capability_profile"
            if focused_b2_same_checkpoint
            else "complete_phase2_mcp_capability_profile"
        ),
        "focused_b2_same_checkpoint": focused_b2_same_checkpoint,
        "tracked_ck3_pid": tracked_ck3_pid,
        "managed_restore_supervisor": managed_restore_supervisor,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "legacy_scenario_used": False,
        "required_bridge_capabilities": required_bridge_capabilities,
        "required_query_flags": required_query_flags,
        "required_action_steps": required_action_steps,
        "unfrozen_requirements": dict(PHASE2_UNFROZEN_REQUIREMENTS),
        "pending_runner_requirements": dict(
            PHASE2_PENDING_RUNNER_REQUIREMENTS
        ),
        "checks": {},
        "missing_requirements": [],
        "capabilities": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        capabilities = service.capabilities()
        if not isinstance(capabilities, dict):
            raise acceptance.RunnerError(
                "MCP capability RED: ck3_get_capabilities returned a non-object"
            )
        evidence["capabilities"] = capabilities
        raw_bridge_capabilities = capabilities.get("bridge_capabilities")
        bridge_capabilities = (
            {
                item
                for item in raw_bridge_capabilities
                if isinstance(item, str) and item
            }
            if isinstance(raw_bridge_capabilities, list)
            else set()
        )
        raw_action_steps = capabilities.get("action_steps")
        action_steps = (
            {
                item
                for item in raw_action_steps
                if isinstance(item, str) and item
            }
            if isinstance(raw_action_steps, list)
            else set()
        )
        diagnostics_value = capabilities.get("diagnostics")
        diagnostics = (
            diagnostics_value
            if isinstance(diagnostics_value, dict)
            else {}
        )
        checkpoint_value = capabilities.get("checkpoint_materialization")
        checkpoint = (
            checkpoint_value if isinstance(checkpoint_value, dict) else {}
        )
        native_session_value = capabilities.get("native_session_control")
        native_session = (
            native_session_value
            if isinstance(native_session_value, dict)
            else {}
        )

        missing: list[dict[str, str]] = []
        for label, capability in required_bridge_capabilities.items():
            if capability not in bridge_capabilities:
                missing.append(
                    {
                        "kind": "bridge_capability",
                        "label": label,
                        "value": capability,
                    }
                )
        for label, flag in required_query_flags.items():
            if capabilities.get(flag) is not True:
                missing.append(
                    {
                        "kind": "query_support_flag",
                        "label": label,
                        "value": flag,
                    }
                )

        for label, step in required_action_steps.items():
            if step not in action_steps:
                missing.append(
                    {
                        "kind": "materialized_action_step",
                        "label": label,
                        "value": step,
                    }
                )

        checks = {
            "native_headless_mode": capabilities.get("mode")
            == NATIVE_BRIDGE_MODE,
            "native_headless_backend": capabilities.get("backend_id")
            == NATIVE_BRIDGE_MODE,
            "visual_fallback_disabled": capabilities.get("visual_fallback")
            is False,
            "snapshot_available": capabilities.get("snapshot") is True,
            "wait_for_change_available": capabilities.get("wait_for_change")
            is True,
            "connected": diagnostics.get("connected") is True,
            "tracked_ck3_pid_matches_bridge": diagnostics.get("bridge_pid")
            == tracked_ck3_pid,
            "positive_connection_generation": isinstance(
                diagnostics.get("connection_generation"), int
            )
            and not isinstance(diagnostics.get("connection_generation"), bool)
            and diagnostics.get("connection_generation", 0) > 0,
            "checkpoint_materialization_configured": checkpoint.get(
                "configured"
            )
            is True,
            # restore-checkpoint is a managed composite and becomes an action
            # only after the first checkpoint exists.  Pre-start readiness is
            # therefore the configured lifecycle queue plus save materialization;
            # the post-save gate below must require the concrete restore step.
            "restore_lifecycle_configured": native_session.get("configured")
            is True,
            "restore_lifecycle_supervisor_running": (
                managed_restore_supervisor is True
            ),
        }
        evidence["checks"] = checks
        for label, passed in checks.items():
            if passed is not True:
                missing.append(
                    {
                        "kind": "runtime_check",
                        "label": label,
                        "value": label,
                    }
                )

        for label, reason in PHASE2_UNFROZEN_REQUIREMENTS.items():
            missing.append(
                {
                    "kind": "abi_not_frozen",
                    "label": label,
                    "value": reason,
                }
            )
        for label, reason in PHASE2_PENDING_RUNNER_REQUIREMENTS.items():
            missing.append(
                {
                    "kind": "runner_not_wired",
                    "label": label,
                    "value": reason,
                }
            )
        evidence["missing_requirements"] = missing
        if missing:
            summary = ", ".join(
                f"{row['label']}={row['value']}" for row in missing
            )
            raise acceptance.RunnerError("MCP capability RED: " + summary)

        evidence["result"] = "GREEN"
        evidence["failure_reason"] = None
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"MCP capability RED: phase-two preflight failed: {error}"
        ) from error


def _phase2_paused_binding(
    snapshot: dict[str, object], *, label: str
) -> dict[str, int | str]:
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise acceptance.RunnerError(
            f"{label} is not a paused map-ready CK3 snapshot"
        )
    snapshot_id = snapshot.get("snapshot_id")
    revision = snapshot.get("revision")
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    played_character = snapshot.get("played_character")
    player_character_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    diagnostics_value = snapshot.get("diagnostics")
    diagnostics = (
        diagnostics_value if isinstance(diagnostics_value, dict) else {}
    )
    bridge_pid = diagnostics.get("bridge_pid")
    connection_generation = diagnostics.get("connection_generation")
    if (
        not isinstance(snapshot_id, str)
        or not snapshot_id
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
        or isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or native_revision <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or isinstance(player_character_id, bool)
        or not isinstance(player_character_id, int)
        or player_character_id <= 0
        or isinstance(bridge_pid, bool)
        or not isinstance(bridge_pid, int)
        or bridge_pid <= 0
        or isinstance(connection_generation, bool)
        or not isinstance(connection_generation, int)
        or connection_generation <= 0
    ):
        raise acceptance.RunnerError(
            f"{label} lacks a complete snapshot/player/PID/generation binding"
        )
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "player_character_id": player_character_id,
        "bridge_pid": bridge_pid,
        "connection_generation": connection_generation,
    }


def _phase2_unimplemented_domain_cells() -> list[str]:
    return [
        cell_id
        for cell_id, registration in PHASE2_DOMAIN_CELL_REGISTRY.items()
        if registration.get("implementation") != "wired"
    ]


def _phase2_domain_query_contract(
    seed_contract: dict[str, object], *, player_character_id: int
) -> dict[str, int]:
    """Read only the frozen selectors required by all wired domain cells."""

    value = seed_contract.get("domain_query_matrix")
    expected_keys = {
        "schema_version",
        "b2_pip_owner_character_id",
        "incident_owner_character_id",
        "workforce_owner_character_id",
        "ai_owned_case_owner_character_id",
        "ai_owned_case_subject_character_id",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise acceptance.RunnerError(
            "phase-two domain matrix RED: contract is absent or malformed; expected "
            "schema_version plus B2, Incident, Workforce and AI-owned-case "
            "selectors"
        )
    if value.get("schema_version") != 1:
        raise acceptance.RunnerError(
            "phase-two domain matrix RED: contract schema_version must be 1"
        )
    result: dict[str, int] = {}
    for key in (
        "b2_pip_owner_character_id",
        "incident_owner_character_id",
        "workforce_owner_character_id",
        "ai_owned_case_owner_character_id",
        "ai_owned_case_subject_character_id",
    ):
        character_id = value.get(key)
        if (
            isinstance(character_id, bool)
            or not isinstance(character_id, int)
            or not 1 <= character_id <= 2**31 - 1
        ):
            raise acceptance.RunnerError(
                f"phase-two domain matrix RED: {key} is not a positive "
                "CharacterID"
            )
        result[key] = character_id
    for key in (
        "b2_pip_owner_character_id",
        "incident_owner_character_id",
        "workforce_owner_character_id",
        "ai_owned_case_owner_character_id",
    ):
        if result[key] == player_character_id:
            raise acceptance.RunnerError(
                f"phase-two domain matrix RED: {key} must not be the played "
                "CharacterID"
            )
    if (
        result["ai_owned_case_owner_character_id"]
        == result["ai_owned_case_subject_character_id"]
    ):
        raise acceptance.RunnerError(
            "phase-two domain matrix RED: AI-owned owner and subject must differ"
        )
    return result


def _phase2_wrong_owner_character_id(
    owner_character_id: int,
    player_character_id: int,
    *excluded_character_ids: int,
) -> int:
    excluded = {
        owner_character_id,
        player_character_id,
        *excluded_character_ids,
    }
    for candidate in (
        owner_character_id + 1,
        owner_character_id - 1,
        player_character_id + 1,
        player_character_id - 1,
        1,
    ):
        if (
            1 <= candidate <= 2**31 - 1
            and candidate not in excluded
        ):
            return candidate
    raise acceptance.RunnerError(
        "phase-two domain matrix could not construct a distinct ACL owner filter"
    )


def _phase2_semantic_query_projection(
    response: dict[str, object],
) -> dict[str, object]:
    """Remove only request/transport identity before restore comparison."""

    return {
        key: value
        for key, value in response.items()
        if key not in {"request_nonce", "snapshot_revision", "source", "binding"}
    }


def _phase2_normalize_b2_query(
    response: object,
    *,
    nonce: str,
    owner_character_id: int,
    binding: dict[str, int | str],
) -> dict[str, object]:
    try:
        return normalize_zhongguo_b2_pip_snapshot_v1_response(
            response,
            expected_query=ZhongguoB2PipQueryV1(owner_character_id, nonce),
            expected_snapshot_id=str(binding["snapshot_id"]),
            expected_revision=int(binding["revision"]),
            expected_native_revision=int(binding["native_revision"]),
            expected_connection_generation=int(binding["connection_generation"]),
            expected_date_raw=int(binding["date_raw"]),
            expected_player_character_id=int(binding["player_character_id"]),
        )
    except (TypeError, ValueError, KeyError) as error:
        raise acceptance.RunnerError(
            "phase-two B2 PIP query returned a partial or malformed tuple: "
            f"{error}"
        ) from error


def _phase2_normalize_incident_query(
    response: object,
    *,
    nonce: str,
    owner_character_id: int,
    profile: str,
    binding: dict[str, int | str],
) -> dict[str, object]:
    try:
        return normalize_zhongguo_incident_snapshot_v1_response(
            response,
            expected_query=ZhongguoIncidentQueryV1(
                owner_character_id, profile, nonce
            ),
            expected_snapshot_id=str(binding["snapshot_id"]),
            expected_revision=int(binding["revision"]),
            expected_native_revision=int(binding["native_revision"]),
            expected_connection_generation=int(binding["connection_generation"]),
            expected_date_raw=int(binding["date_raw"]),
            expected_player_character_id=int(binding["player_character_id"]),
        )
    except (TypeError, ValueError, KeyError) as error:
        raise acceptance.RunnerError(
            "phase-two Incident query returned a partial or malformed tuple: "
            f"{error}"
        ) from error


def _phase2_normalize_workforce_query(
    response: object,
    *,
    nonce: str,
    owner_character_id: int,
    binding: dict[str, int | str],
) -> dict[str, object]:
    try:
        return normalize_zhongguo_workforce_collective_snapshot_v1_response(
            response,
            expected_query=ZhongguoWorkforceCollectiveQueryV1(
                owner_character_id, nonce
            ),
            expected_snapshot_id=str(binding["snapshot_id"]),
            expected_revision=int(binding["revision"]),
            expected_native_revision=int(binding["native_revision"]),
            expected_connection_generation=int(binding["connection_generation"]),
            expected_date_raw=int(binding["date_raw"]),
            expected_player_character_id=int(binding["player_character_id"]),
        )
    except (TypeError, ValueError, KeyError) as error:
        raise acceptance.RunnerError(
            "phase-two Workforce collective query returned a partial or "
            f"malformed tuple: {error}"
        ) from error


def _phase2_normalize_ai_owned_case_query(
    response: object,
    *,
    nonce: str,
    owner_character_id: int,
    subject_character_id: int,
    binding: dict[str, int | str],
) -> dict[str, object]:
    try:
        return normalize_zhongguo_ai_owned_case_snapshot_v1_response(
            response,
            expected_query=ZhongguoAiOwnedCaseQueryV1(
                owner_character_id,
                subject_character_id,
                nonce,
            ),
            expected_snapshot_id=str(binding["snapshot_id"]),
            expected_revision=int(binding["revision"]),
            expected_native_revision=int(binding["native_revision"]),
            expected_connection_generation=int(binding["connection_generation"]),
            expected_date_raw=int(binding["date_raw"]),
            expected_player_character_id=int(binding["player_character_id"]),
        )
    except (TypeError, ValueError, KeyError) as error:
        raise acceptance.RunnerError(
            "phase-two AI-owned case query returned a partial or malformed "
            f"tuple: {error}"
        ) from error


def _phase2_typed_unavailable(
    value: object, *, reason: str | None = None
) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"status", "value", "unavailable_reason"}
        and value.get("status") == "unavailable"
        and value.get("value") is None
        and (
            reason is None
            or value.get("unavailable_reason") == reason
        )
    )


def _phase2_typed_available(value: object, expected: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"status", "value", "unavailable_reason"}
        and value.get("status") == "available"
        and value.get("value") == expected
        and value.get("unavailable_reason") is None
    )


def _phase2_query_b2_pip_cell(
    service: GameplayBridgeService,
    *,
    stage: str,
    binding: dict[str, int | str],
    owner_character_id: int,
) -> dict[str, object]:
    player_character_id = int(binding["player_character_id"])
    wrong_owner = _phase2_wrong_owner_character_id(
        owner_character_id, player_character_id
    )
    positive_nonce = f"zg361.phase2.{stage}.b2.positive"
    acl_nonce = f"zg361.phase2.{stage}.b2.acl"
    positive = _phase2_normalize_b2_query(
        service.query_zhongguo_b2_pip_snapshot_v1(
            positive_nonce,
            expected_revision=int(binding["revision"]),
            owner_character_id=owner_character_id,
        ),
        nonce=positive_nonce,
        owner_character_id=owner_character_id,
        binding=binding,
    )
    readiness = positive.get("readiness")
    if not (
        positive.get("status") == "available"
        and positive.get("case_kind") == ZHONGGUO_B2_PIP_CASE_KIND_V1
        and positive.get("unavailable_reason") is None
        and isinstance(readiness, dict)
        and readiness.get("player_subject_binding_ready") is True
        and readiness.get("owner_binding_ready") is True
        and readiness.get("gate_ready") is True
        and readiness.get("gate_evidence_ready") is True
        and readiness.get("pip_identity_ready") is True
        and readiness.get("same_frame_ready") is True
        and readiness.get("ready") is True
    ):
        raise acceptance.RunnerError(
            "phase-two B2 PIP positive cell is not a ready received-self case"
        )
    typed_unavailable_count = 0
    for ticket_name in ("d180_ticket", "d365_ticket"):
        ticket = positive.get(ticket_name)
        if not isinstance(ticket, dict) or not ticket:
            raise acceptance.RunnerError(
                f"phase-two B2 PIP {ticket_name} is a partial tuple"
            )
        for field_name, field in ticket.items():
            expected_reason = (
                "product_not_persisted"
                if field_name == "due_date_raw"
                else "native_observation_unavailable"
            )
            if not _phase2_typed_unavailable(field, reason=expected_reason):
                raise acceptance.RunnerError(
                    f"phase-two B2 PIP {ticket_name}.{field_name} fabricated "
                    "an unimplemented observation"
                )
            typed_unavailable_count += 1
    if not _phase2_typed_unavailable(
        positive.get("pip_modifier_present"),
        reason="native_observation_unavailable",
    ):
        raise acceptance.RunnerError(
            "phase-two B2 PIP modifier observation is not typed unavailable"
        )
    typed_unavailable_count += 1

    acl = _phase2_normalize_b2_query(
        service.query_zhongguo_b2_pip_snapshot_v1(
            acl_nonce,
            expected_revision=int(binding["revision"]),
            owner_character_id=wrong_owner,
        ),
        nonce=acl_nonce,
        owner_character_id=wrong_owner,
        binding=binding,
    )
    acl_binding = acl.get("binding")
    acl_readiness = acl.get("readiness")
    if not (
        acl.get("status") == "unavailable"
        and acl.get("unavailable_reason") == "owner_filter_mismatch"
        and isinstance(acl_binding, dict)
        and acl_binding.get("owner_character_id") is None
        and isinstance(acl_readiness, dict)
        and acl_readiness.get("same_frame_ready") is True
        and acl_readiness.get("ready") is False
    ):
        raise acceptance.RunnerError(
            "phase-two B2 PIP wrong-owner ACL did not return a wiped typed RED"
        )
    return {
        "result": "GREEN",
        "observation_only": True,
        "gameplay_action_executed": False,
        "gameplay_action_complete": False,
        "owner_character_id": owner_character_id,
        "wrong_owner_character_id": wrong_owner,
        "positive_response": positive,
        "acl_response": acl,
        "typed_unavailable_leaf_count": typed_unavailable_count,
        "semantic_projection": {
            "positive": _phase2_semantic_query_projection(positive),
            "acl": _phase2_semantic_query_projection(acl),
        },
    }


def _phase2_query_incident_cell(
    service: GameplayBridgeService,
    *,
    stage: str,
    binding: dict[str, int | str],
    owner_character_id: int,
) -> dict[str, object]:
    player_character_id = int(binding["player_character_id"])
    wrong_owner = _phase2_wrong_owner_character_id(
        owner_character_id, player_character_id
    )
    profiles: dict[str, dict[str, object]] = {}
    acl_profiles: dict[str, dict[str, object]] = {}
    terminal_kinds: list[str] = []
    typed_unavailable_count = 0
    for profile in ("x", "y", "z"):
        positive_nonce = f"zg361.phase2.{stage}.incident.{profile}.positive"
        response = _phase2_normalize_incident_query(
            service.query_zhongguo_incident_snapshot_v1(
                positive_nonce,
                expected_revision=int(binding["revision"]),
                owner_character_id=owner_character_id,
                profile=profile,
            ),
            nonce=positive_nonce,
            owner_character_id=owner_character_id,
            profile=profile,
            binding=binding,
        )
        readiness = response.get("readiness")
        terminal = response.get("terminal")
        terminal_kind = (
            terminal.get("kind") if isinstance(terminal, dict) else None
        )
        if not (
            response.get("status") == "available"
            and response.get("case_kind") == ZHONGGUO_INCIDENT_KIND_V1
            and response.get("profile") == profile
            and response.get("unavailable_reason") is None
            and isinstance(readiness, dict)
            and readiness.get("ready") is True
            and terminal_kind in {"na", "incident"}
        ):
            raise acceptance.RunnerError(
                f"phase-two Incident {profile} is not a complete N/A/positive tuple"
            )
        terminal_kinds.append(str(terminal_kind))
        for group_name in ("probe", "resources", "kpi"):
            group = response.get(group_name)
            if not isinstance(group, dict):
                raise acceptance.RunnerError(
                    f"phase-two Incident {profile} {group_name} is partial"
                )
            typed_unavailable_count += sum(
                1 for field in group.values() if _phase2_typed_unavailable(field)
            )
        profiles[profile] = response

        acl_nonce = f"zg361.phase2.{stage}.incident.{profile}.acl"
        acl = _phase2_normalize_incident_query(
            service.query_zhongguo_incident_snapshot_v1(
                acl_nonce,
                expected_revision=int(binding["revision"]),
                owner_character_id=wrong_owner,
                profile=profile,
            ),
            nonce=acl_nonce,
            owner_character_id=wrong_owner,
            profile=profile,
            binding=binding,
        )
        acl_binding = acl.get("binding")
        acl_readiness = acl.get("readiness")
        if not (
            acl.get("status") == "unavailable"
            and acl.get("unavailable_reason") == "owner_filter_mismatch"
            and isinstance(acl_binding, dict)
            and acl_binding.get("owner_character_id") is None
            and isinstance(acl_readiness, dict)
            and acl_readiness.get("ready") is False
        ):
            raise acceptance.RunnerError(
                f"phase-two Incident {profile} wrong-owner ACL leaked a tuple"
            )
        acl_profiles[profile] = acl

    if set(terminal_kinds) != {"na", "incident"}:
        raise acceptance.RunnerError(
            "phase-two Incident X/Y/Z matrix must contain both an exact N/A "
            "receipt and a positive incident"
        )
    if typed_unavailable_count <= 0:
        raise acceptance.RunnerError(
            "phase-two Incident X/Y/Z matrix did not preserve any typed "
            "unavailable leaf"
        )
    return {
        "result": "GREEN",
        "observation_only": True,
        "gameplay_action_executed": False,
        "gameplay_action_complete": False,
        "owner_character_id": owner_character_id,
        "wrong_owner_character_id": wrong_owner,
        "profiles": profiles,
        "acl_profiles": acl_profiles,
        "terminal_kind_counts": {
            "na": terminal_kinds.count("na"),
            "incident": terminal_kinds.count("incident"),
        },
        "typed_unavailable_leaf_count": typed_unavailable_count,
        "semantic_projection": {
            "profiles": {
                profile: _phase2_semantic_query_projection(response)
                for profile, response in profiles.items()
            },
            "acl_profiles": {
                profile: _phase2_semantic_query_projection(response)
                for profile, response in acl_profiles.items()
            },
        },
    }


def _phase2_query_workforce_collective_cell(
    service: GameplayBridgeService,
    *,
    stage: str,
    binding: dict[str, int | str],
    owner_character_id: int,
) -> dict[str, object]:
    player_character_id = int(binding["player_character_id"])
    wrong_owner = _phase2_wrong_owner_character_id(
        owner_character_id, player_character_id
    )
    positive_nonce = f"zg361.phase2.{stage}.workforce.positive"
    acl_nonce = f"zg361.phase2.{stage}.workforce.acl"
    positive = _phase2_normalize_workforce_query(
        service.query_zhongguo_workforce_collective_snapshot_v1(
            positive_nonce,
            expected_revision=int(binding["revision"]),
            owner_character_id=owner_character_id,
        ),
        nonce=positive_nonce,
        owner_character_id=owner_character_id,
        binding=binding,
    )
    readiness = positive.get("readiness")
    history = positive.get("history")
    al_case = positive.get("al_case")
    receipt = positive.get("m360_receipt")
    if not (
        positive.get("status") == "available"
        and positive.get("case_kind")
        == ZHONGGUO_WORKFORCE_COLLECTIVE_CASE_KIND_V1
        and positive.get("unavailable_reason") is None
        and positive.get("subject_character_id") == player_character_id
        and positive.get("requested_owner_character_id")
        == owner_character_id
        and isinstance(readiness, dict)
        and readiness.get("same_frame_ready") is True
        and readiness.get("collective_lifecycle_ready") is True
        and readiness.get("history_ledger_ready") is True
        and readiness.get("history_order_ready") is True
        and readiness.get("three_cycle_ready") is True
        and readiness.get("charter_gate_lifecycle_ready") is True
        and readiness.get("ready") is True
        and isinstance(history, dict)
        and history.get("status") == "three_cycle"
        and history.get("effective_count") == 3
        and _phase2_typed_available(history.get("count"), 3)
        and isinstance(history.get("slots"), list)
        and len(history["slots"]) == 3
        and isinstance(al_case, dict)
        and _phase2_typed_available(
            al_case.get("owner_character_id"), owner_character_id
        )
        and _phase2_typed_available(
            al_case.get("subject_character_id"), player_character_id
        )
        and isinstance(receipt, dict)
        and _phase2_typed_available(
            receipt.get("owner_character_id"), owner_character_id
        )
        and _phase2_typed_available(
            receipt.get("subject_character_id"), player_character_id
        )
    ):
        raise acceptance.RunnerError(
            "phase-two Workforce collective positive cell lacks its received-self "
            "three-cycle proof"
        )

    acl = _phase2_normalize_workforce_query(
        service.query_zhongguo_workforce_collective_snapshot_v1(
            acl_nonce,
            expected_revision=int(binding["revision"]),
            owner_character_id=wrong_owner,
        ),
        nonce=acl_nonce,
        owner_character_id=wrong_owner,
        binding=binding,
    )
    acl_binding = acl.get("binding")
    acl_readiness = acl.get("readiness")
    if not (
        acl.get("status") == "unavailable"
        and acl.get("unavailable_reason") == "owner_filter_mismatch"
        and isinstance(acl_binding, dict)
        and acl_binding.get("owner_character_id") is None
        and isinstance(acl_readiness, dict)
        and not any(acl_readiness.values())
    ):
        raise acceptance.RunnerError(
            "phase-two Workforce wrong-owner ACL leaked a collective tuple"
        )
    return {
        "result": "GREEN",
        "observation_only": True,
        "gameplay_action_executed": False,
        "gameplay_action_complete": False,
        "owner_character_id": owner_character_id,
        "wrong_owner_character_id": wrong_owner,
        "positive_response": positive,
        "acl_response": acl,
        "three_cycle_receipt_count": 3,
        "semantic_projection": {
            "positive": _phase2_semantic_query_projection(positive),
            "acl": _phase2_semantic_query_projection(acl),
        },
    }


def _phase2_query_ai_owned_case_cell(
    service: GameplayBridgeService,
    *,
    stage: str,
    binding: dict[str, int | str],
    owner_character_id: int,
    subject_character_id: int,
) -> dict[str, object]:
    player_character_id = int(binding["player_character_id"])
    wrong_owner = _phase2_wrong_owner_character_id(
        owner_character_id,
        player_character_id,
        subject_character_id,
    )
    positive_nonce = f"zg361.phase2.{stage}.ai-owned.positive"
    acl_nonce = f"zg361.phase2.{stage}.ai-owned.acl"
    positive = _phase2_normalize_ai_owned_case_query(
        service.query_zhongguo_ai_owned_case_snapshot_v1(
            owner_character_id,
            subject_character_id,
            positive_nonce,
            expected_revision=int(binding["revision"]),
        ),
        nonce=positive_nonce,
        owner_character_id=owner_character_id,
        subject_character_id=subject_character_id,
        binding=binding,
    )
    readiness = positive.get("readiness")
    eligibility = positive.get("owner_eligibility")
    case = positive.get("case")
    route = positive.get("route")
    if not (
        positive.get("status") == "available"
        and positive.get("case_kind") == ZHONGGUO_AI_OWNED_CASE_KIND_V1
        and positive.get("unavailable_reason") is None
        and positive.get("requested_owner_character_id")
        == owner_character_id
        and positive.get("subject_character_id") == subject_character_id
        and isinstance(readiness, dict)
        and readiness.get("owner_eligibility_ready") is True
        and readiness.get("case_identity_ready") is True
        and readiness.get("route_ready") is True
        and readiness.get("same_frame_ready") is True
        and readiness.get("ready") is True
        and isinstance(eligibility, dict)
        and _phase2_typed_available(
            eligibility.get("owner_character_id"), owner_character_id
        )
        and _phase2_typed_available(eligibility.get("owner_alive"), True)
        and _phase2_typed_available(eligibility.get("owner_is_ai"), True)
        and _phase2_typed_available(
            eligibility.get("government_key"), "celestial_government"
        )
        and _phase2_typed_available(
            eligibility.get("subject_immediate_liege_character_id"),
            owner_character_id,
        )
        and _phase2_typed_available(
            eligibility.get("subject_is_direct_subject"), True
        )
        and _phase2_typed_available(eligibility.get("authorized"), True)
        and isinstance(case, dict)
        and _phase2_typed_available(
            case.get("owner_character_id"), owner_character_id
        )
        and _phase2_typed_available(
            case.get("subject_character_id"), subject_character_id
        )
        and isinstance(route, dict)
        and _phase2_typed_available(
            route.get("kind"), ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1
        )
        and _phase2_typed_available(
            route.get("visible_event_allowed"), False
        )
        and _phase2_typed_available(route.get("owner_is_ai"), True)
        and _phase2_typed_available(route.get("manager_eligible"), True)
        and _phase2_typed_available(
            route.get("direct_subject_eligible"), True
        )
    ):
        raise acceptance.RunnerError(
            "phase-two AI-owned case positive cell lacks an authorized AI "
            "background route"
        )

    acl = _phase2_normalize_ai_owned_case_query(
        service.query_zhongguo_ai_owned_case_snapshot_v1(
            wrong_owner,
            subject_character_id,
            acl_nonce,
            expected_revision=int(binding["revision"]),
        ),
        nonce=acl_nonce,
        owner_character_id=wrong_owner,
        subject_character_id=subject_character_id,
        binding=binding,
    )
    acl_readiness = acl.get("readiness")
    if not (
        acl.get("status") == "unavailable"
        and acl.get("unavailable_reason") == "owner_filter_mismatch"
        and isinstance(acl_readiness, dict)
        and acl_readiness.get("same_frame_ready") is True
        and acl_readiness.get("ready") is False
    ):
        raise acceptance.RunnerError(
            "phase-two AI-owned wrong-owner ACL leaked a case tuple"
        )
    return {
        "result": "GREEN",
        "observation_only": True,
        "gameplay_action_executed": False,
        "gameplay_action_complete": False,
        "owner_character_id": owner_character_id,
        "subject_character_id": subject_character_id,
        "wrong_owner_character_id": wrong_owner,
        "positive_response": positive,
        "acl_response": acl,
        "semantic_projection": {
            "positive": _phase2_semantic_query_projection(positive),
            "acl": _phase2_semantic_query_projection(acl),
        },
    }


def run_phase2_domain_query_stage(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    stage: str,
    binding: dict[str, int | str],
    owner_contract: dict[str, int],
) -> dict[str, object]:
    """Run all currently wired read-only domain cells on one paused frame."""

    if stage not in {"pre_restore", "post_restore"}:
        raise ValueError("phase-two domain query stage must be pre/post_restore")
    evidence_path = artifacts / (
        "05a_phase2_domain_queries_pre_restore.json"
        if stage == "pre_restore"
        else "07_phase2_domain_queries_post_restore.json"
    )
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "stage": stage,
        "scope": "phase2_available_mcp_read_only_domain_cells",
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "gameplay_action_executed": False,
        "gameplay_green_claimed": False,
        "binding": binding,
        "owner_contract": owner_contract,
        "cell_registry": PHASE2_DOMAIN_CELL_REGISTRY,
        "implemented_cells": [],
        "unimplemented_domain_cells": _phase2_unimplemented_domain_cells(),
        "cells": {},
        "capabilities": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        capabilities = service.capabilities()
        if not isinstance(capabilities, dict):
            raise acceptance.RunnerError(
                "phase-two domain query capabilities are not an object"
            )
        evidence["capabilities"] = capabilities
        advertised = capabilities.get("bridge_capabilities")
        advertised_set = (
            {item for item in advertised if isinstance(item, str)}
            if isinstance(advertised, list)
            else set()
        )
        implemented = [
            cell_id
            for cell_id, registration in PHASE2_DOMAIN_CELL_REGISTRY.items()
            if registration.get("implementation") == "wired"
        ]
        for cell_id in implemented:
            registration = PHASE2_DOMAIN_CELL_REGISTRY[cell_id]
            capability = registration.get("required_capability")
            query_flag = registration.get("required_query_flag")
            if (
                not isinstance(capability, str)
                or capability not in advertised_set
                or not isinstance(query_flag, str)
                or capabilities.get(query_flag) is not True
            ):
                raise acceptance.RunnerError(
                    f"phase-two domain cell {cell_id} lacks its runtime "
                    "capability/query flag"
                )

        handlers = {
            "b2_pip_snapshot_query_matrix": lambda: _phase2_query_b2_pip_cell(
                service,
                stage=stage,
                binding=binding,
                owner_character_id=owner_contract[
                    "b2_pip_owner_character_id"
                ],
            ),
            "incident_xyz_snapshot_query_matrix": (
                lambda: _phase2_query_incident_cell(
                    service,
                    stage=stage,
                    binding=binding,
                    owner_character_id=owner_contract[
                        "incident_owner_character_id"
                    ],
                )
            ),
            "workforce_collective_and_three_cycle_matrix": (
                lambda: _phase2_query_workforce_collective_cell(
                    service,
                    stage=stage,
                    binding=binding,
                    owner_character_id=owner_contract[
                        "workforce_owner_character_id"
                    ],
                )
            ),
            "ai_owned_case_matrix": lambda: _phase2_query_ai_owned_case_cell(
                service,
                stage=stage,
                binding=binding,
                owner_character_id=owner_contract[
                    "ai_owned_case_owner_character_id"
                ],
                subject_character_id=owner_contract[
                    "ai_owned_case_subject_character_id"
                ],
            ),
        }
        cells = evidence["cells"]
        assert isinstance(cells, dict)
        for cell_id in implemented:
            handler = handlers.get(cell_id)
            if handler is None:
                raise acceptance.RunnerError(
                    f"phase-two wired cell {cell_id} has no runner handler"
                )
            cells[cell_id] = handler()
            implemented_cells = evidence["implemented_cells"]
            if not isinstance(implemented_cells, list):
                raise acceptance.RunnerError(
                    "phase-two implemented-cell evidence changed type"
                )
            implemented_cells.append(cell_id)
            write_json(evidence_path, evidence)
        evidence["result"] = "GREEN"
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two {stage} domain query matrix failed: {error}"
        ) from error


def compare_phase2_domain_query_stages(
    before: dict[str, object],
    after: dict[str, object],
    artifacts: Path,
) -> dict[str, object]:
    """Require every observation-only domain payload to survive restore."""

    evidence_path = artifacts / "07b_phase2_domain_restore_consistency.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_read_only_domain_payload_restore_consistency",
        "mcp_only": True,
        "gameplay_action_executed": False,
        "gameplay_green_claimed": False,
        "checks": {},
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        before_binding = before.get("binding")
        after_binding = after.get("binding")
        before_cells = before.get("cells")
        after_cells = after.get("cells")
        checks = {
            "both_query_stages_green": before.get("result") == "GREEN"
            and after.get("result") == "GREEN",
            "same_player": isinstance(before_binding, dict)
            and isinstance(after_binding, dict)
            and before_binding.get("player_character_id")
            == after_binding.get("player_character_id"),
            "same_date": isinstance(before_binding, dict)
            and isinstance(after_binding, dict)
            and before_binding.get("date_raw") == after_binding.get("date_raw"),
            "same_implemented_cells": before.get("implemented_cells")
            == after.get("implemented_cells"),
            "same_unimplemented_cells": before.get("unimplemented_domain_cells")
            == after.get("unimplemented_domain_cells"),
            "domain_payloads_restored": isinstance(before_cells, dict)
            and isinstance(after_cells, dict)
            and {
                cell_id: cell.get("semantic_projection")
                for cell_id, cell in before_cells.items()
                if isinstance(cell, dict)
            }
            == {
                cell_id: cell.get("semantic_projection")
                for cell_id, cell in after_cells.items()
                if isinstance(cell, dict)
            },
        }
        evidence["checks"] = checks
        failed = [name for name, passed in checks.items() if passed is not True]
        if failed:
            raise acceptance.RunnerError(
                "phase-two domain restore consistency RED: "
                + ", ".join(failed)
            )
        evidence["result"] = "GREEN"
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two domain restore consistency failed: {error}"
        ) from error


def run_phase2_scoreboard_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    prepare_surface: Callable[[str], dict[str, object]] | None = None,
) -> dict[str, object]:
    """Preserve the two-surface named-widget action ledger fail-closed.

    Surface staging is deliberately a narrow provider seam.  Until the real
    managed provider exists, the production runner records an explicit RED
    without dispatching a partial matrix.  A false capability advertisement
    still allows every accepted action's independent verifier to be retained,
    but can never produce GREEN or promotion eligibility.
    """

    evidence_path = artifacts / (
        "07c_phase2_scoreboard_named_widget_action_cell.json"
    )
    if prepare_surface is None:
        provider = getattr(
            service, "prepare_zhongguo_scoreboard_surface_v1", None
        )

        def prepare_surface(surface_id: str) -> dict[str, object]:
            if not callable(provider):
                return {
                    "surface_id": surface_id,
                    "status": "unavailable",
                    "failure_reason": (
                        "scoreboard_surface_preparation_provider_missing"
                    ),
                }
            receipt = provider(surface_id)
            if not isinstance(receipt, dict):
                raise acceptance.RunnerError(
                    "scoreboard surface preparation returned a non-object"
                )
            return receipt

    evidence = run_zhongguo_scoreboard_action_batch(
        service,
        prepare_surface=prepare_surface,
        nonce_prefix="zg361.scoreboard.phase2-live-batch",
    )
    if not isinstance(evidence, dict):
        raise acceptance.RunnerError(
            "phase-two scoreboard action cell returned a non-object"
        )
    write_json(evidence_path, evidence)
    result = evidence.get("result")
    if result == "GREEN":
        if not (
            evidence.get("candidate_batch_complete") is True
            and evidence.get("all_postconditions_verified") is True
            and evidence.get("all_expected_acl_denials_verified") is True
            and evidence.get(
                "per_surface_single_session_binding_verified"
            )
            is True
            and evidence.get("cross_surface_clean_restart_verified") is True
            and evidence.get("production_capability_advertised") is True
            and evidence.get("promotion_eligible") is True
        ):
            raise acceptance.RunnerError(
                "phase-two scoreboard batch forged GREEN without its full "
                "two-surface proof and advertised production capability"
            )
    elif result == "RED":
        if evidence.get("promotion_eligible") is not False:
            raise acceptance.RunnerError(
                "phase-two scoreboard RED ledger claimed promotion eligibility"
            )
    else:
        raise acceptance.RunnerError(
            "phase-two scoreboard action cell returned an invalid result"
        )
    return evidence


def run_phase2_incident_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    owner_character_id: int,
) -> dict[str, object]:
    """Run the reusable Incident action cell and preserve its exact evidence."""

    evidence_path = artifacts / (
        "05_phase2_incident_xyz_gameplay_action_cell.json"
    )
    try:
        evidence = run_incident_xyz_gameplay_action_cell(
            service,
            owner_character_id=owner_character_id,
        )
    except IncidentActionCellError as error:
        write_json(evidence_path, error.evidence)
        raise acceptance.RunnerError(
            "phase-two Incident X/Y/Z gameplay action cell RED: "
            f"{error.reason}"
        ) from error
    if not isinstance(evidence, dict) or evidence.get("result") != "GREEN":
        raise acceptance.RunnerError(
            "phase-two Incident X/Y/Z gameplay action cell returned a "
            "non-GREEN result"
        )
    write_json(evidence_path, evidence)
    return evidence


def run_phase2_b2_pip_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    owner_character_id: int,
) -> dict[str, object]:
    """Accept the real B2 prompt and preserve the provider postcondition."""

    evidence_path = artifacts / "05_phase2_b2_pip_gameplay_action_cell.json"
    try:
        evidence = run_b2_pip_gameplay_action_cell(
            service,
            owner_character_id=owner_character_id,
            action="accept",
        )
    except B2PipActionCellError as error:
        write_json(evidence_path, error.evidence)
        raise acceptance.RunnerError(
            "phase-two B2 PIP accept gameplay action cell RED: "
            f"{error}"
        ) from error
    if not isinstance(evidence, dict) or evidence.get("result") != "GREEN":
        if isinstance(evidence, dict):
            write_json(evidence_path, evidence)
        raise acceptance.RunnerError(
            "phase-two B2 PIP accept gameplay action cell returned a "
            "non-GREEN result"
        )
    write_json(evidence_path, evidence)
    return evidence


def run_phase2_ai_owned_case_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    owner_character_id: int,
    subject_character_id: int,
) -> dict[str, object]:
    """Advance a real bounded timeline until the AI manager posts a receipt."""

    evidence_path = artifacts / (
        "05_phase2_ai_owned_case_gameplay_action_cell.json"
    )
    try:
        evidence = run_zhongguo_ai_owned_case_background_action(
            service,
            owner_character_id=owner_character_id,
            subject_character_id=subject_character_id,
            require_transition=True,
        )
    except BaseException as error:
        failure = {
            "schema_version": 1,
            "kind": "zg361_ai_owned_case_background_action",
            "result": "RED",
            "mcp_only": True,
            "ocr_used": False,
            "coordinates_used": False,
            "test_ui_used": False,
            "owner_character_id": owner_character_id,
            "subject_character_id": subject_character_id,
            "failure_reason": f"{type(error).__name__}: {error}",
        }
        write_json(evidence_path, failure)
        raise acceptance.RunnerError(
            "phase-two AI-owned case gameplay action cell failed before a "
            f"typed result: {error}"
        ) from error

    if not isinstance(evidence, dict):
        raise acceptance.RunnerError(
            "phase-two AI-owned case gameplay action returned a non-object"
        )
    write_json(evidence_path, evidence)
    timeline_actions = evidence.get("timeline_actions")
    provider_observations = evidence.get("provider_observations")
    checks = {
        "result_green": evidence.get("result") == "GREEN",
        "gameplay_action_executed": evidence.get(
            "gameplay_action_executed"
        )
        is True,
        "gameplay_action_complete": evidence.get(
            "gameplay_action_complete"
        )
        is True,
        "background_business_complete": evidence.get(
            "background_business_complete"
        )
        is True,
        "ack_not_business_postcondition": evidence.get(
            "action_ack_is_business_postcondition"
        )
        is False,
        "new_roster_lock_receipt": evidence.get("terminal_condition")
        == "new_allowlisted_roster_lock_receipt",
        "bounded_life_advance_executed": isinstance(timeline_actions, list)
        and bool(timeline_actions)
        and all(
            isinstance(row, dict) and row.get("step") == "life-advance"
            for row in timeline_actions
        ),
        "provider_postcondition_observed": isinstance(
            provider_observations, list
        )
        and bool(provider_observations)
        and isinstance(provider_observations[-1], dict)
        and provider_observations[-1].get("classification") == "postcondition",
    }
    failed = [label for label, passed in checks.items() if passed is not True]
    if failed:
        raise acceptance.RunnerError(
            "phase-two AI-owned case gameplay action cell RED: "
            + ", ".join(failed)
            + f"; terminal={evidence.get('terminal_condition')!r}; "
            f"reason={evidence.get('failure_reason')!r}"
        )
    return evidence


def run_phase2_manager_governance_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    typed_selector_provider: (
        Callable[[GameplayBridgeService], Mapping[str, object]] | None
    ) = None,
) -> dict[str, object]:
    """Run B3 only after a typed AI-manager/subordinate selector is bound.

    The read-only manager provider and joined action/postcondition cell are
    already production-wired.  The native selector that chooses one bounded
    AI direct manager and one of that manager's direct subordinates is not.
    Preserve that boundary as provider-pending evidence; never substitute a
    timeline ACK, seed guess, or player identity for the missing selector.
    """

    evidence_path = artifacts / (
        "07e_phase2_manager_governance_gameplay_action_cell.json"
    )
    cell_id = "manager_governance_gameplay_action_and_postcondition_matrix"
    if typed_selector_provider is None:
        pending = {
            "schema_version": 1,
            "kind": "zg361_b3_manager_governance_runner_handler",
            "cell_id": cell_id,
            "result": "RED",
            "readiness": "static-ready",
            "implementation": "provider_pending",
            "provider_status": "provider_pending",
            "mcp_only": True,
            "ocr_used": False,
            "coordinates_used": False,
            "test_ui_used": False,
            "gameplay_action_executed": False,
            "gameplay_action_complete": False,
            "action_cell_invoked": False,
            "action_ack_is_business_postcondition": False,
            "provider_observed_postcondition_required": True,
            "provider_observed_postcondition": None,
            "required_typed_selector": PHASE2_B3_MANAGER_SELECTOR_KIND,
            "typed_selector": None,
            "missing_requirements": [
                {
                    "id": "bounded_ai_manager_native_typed_selector",
                    "status": "provider_pending",
                    "readiness": "static-ready",
                    "reason": (
                        "the native typed selector for one bounded AI direct "
                        "manager and its direct subordinate is not yet bound "
                        "to the formal Phase2 runner"
                    ),
                }
            ],
            "failure_reason": (
                "provider_pending: bounded AI manager typed selector is not "
                "bound; no gameplay action was attempted"
            ),
        }
        write_json(evidence_path, pending)
        return pending

    try:
        selected = typed_selector_provider(service)
    except BaseException as error:
        failure = {
            "schema_version": 1,
            "kind": "zg361_b3_manager_governance_runner_handler",
            "cell_id": cell_id,
            "result": "RED",
            "readiness": "static-ready",
            "implementation": "selector_provider_error",
            "provider_status": "RED",
            "mcp_only": True,
            "gameplay_action_executed": False,
            "gameplay_action_complete": False,
            "action_cell_invoked": False,
            "action_ack_is_business_postcondition": False,
            "provider_observed_postcondition_required": True,
            "provider_observed_postcondition": None,
            "required_typed_selector": PHASE2_B3_MANAGER_SELECTOR_KIND,
            "typed_selector": None,
            "failure_reason": f"{type(error).__name__}: {error}",
        }
        write_json(evidence_path, failure)
        raise acceptance.RunnerError(
            "phase-two B3 manager typed selector provider failed: "
            f"{error}"
        ) from error

    manager_character_id = (
        selected.get("manager_character_id")
        if isinstance(selected, Mapping)
        else None
    )
    subordinate_character_id = (
        selected.get("subordinate_character_id")
        if isinstance(selected, Mapping)
        else None
    )
    selector_checks = {
        "selector_is_object": isinstance(selected, Mapping),
        "selector_status_available": isinstance(selected, Mapping)
        and selected.get("status") == "available",
        "selector_kind_exact": isinstance(selected, Mapping)
        and selected.get("selector_kind") == PHASE2_B3_MANAGER_SELECTOR_KIND,
        "selector_provider_observed": isinstance(selected, Mapping)
        and selected.get("provider_observed") is True,
        "manager_character_id_positive": not isinstance(
            manager_character_id, bool
        )
        and isinstance(manager_character_id, int)
        and manager_character_id > 0,
        "subordinate_character_id_positive": not isinstance(
            subordinate_character_id, bool
        )
        and isinstance(subordinate_character_id, int)
        and subordinate_character_id > 0,
        "characters_distinct": isinstance(manager_character_id, int)
        and not isinstance(manager_character_id, bool)
        and isinstance(subordinate_character_id, int)
        and not isinstance(subordinate_character_id, bool)
        and manager_character_id != subordinate_character_id,
    }
    failed_selector_checks = [
        label for label, passed in selector_checks.items() if passed is not True
    ]
    if failed_selector_checks:
        failure = {
            "schema_version": 1,
            "kind": "zg361_b3_manager_governance_runner_handler",
            "cell_id": cell_id,
            "result": "RED",
            "readiness": "static-ready",
            "implementation": "selector_provider_invalid",
            "provider_status": "RED",
            "mcp_only": True,
            "gameplay_action_executed": False,
            "gameplay_action_complete": False,
            "action_cell_invoked": False,
            "action_ack_is_business_postcondition": False,
            "provider_observed_postcondition_required": True,
            "provider_observed_postcondition": None,
            "required_typed_selector": PHASE2_B3_MANAGER_SELECTOR_KIND,
            "typed_selector": (
                dict(selected) if isinstance(selected, Mapping) else selected
            ),
            "selector_checks": selector_checks,
            "failed_selector_checks": failed_selector_checks,
            "failure_reason": (
                "typed selector returned a partial, unobserved, or invalid "
                "manager/subordinate binding"
            ),
        }
        write_json(evidence_path, failure)
        raise acceptance.RunnerError(
            "phase-two B3 manager typed selector RED: "
            + ", ".join(failed_selector_checks)
        )

    manager_id = int(manager_character_id)
    subordinate_id = int(subordinate_character_id)
    try:
        action = run_b3_manager_governance_gameplay_action_cell(
            service,
            manager_character_id=manager_id,
            subordinate_character_id=subordinate_id,
        )
    except B3ManagerGovernanceActionCellError as error:
        failure = {
            **error.evidence,
            "kind": "zg361_b3_manager_governance_runner_handler",
            "cell_id": cell_id,
            "readiness": "static-ready",
            "implementation": "wired",
            "provider_status": "RED",
            "typed_selector": dict(selected),
            "provider_observed_postcondition_required": True,
            "action_ack_is_business_postcondition": False,
        }
        write_json(evidence_path, failure)
        raise acceptance.RunnerError(
            "phase-two B3 manager-governance gameplay action cell RED: "
            f"{error.reason_code}"
        ) from error

    transition = action.get("transition") if isinstance(action, dict) else None
    checks = action.get("checks") if isinstance(action, dict) else None
    postcondition = (
        action.get("postcondition") if isinstance(action, dict) else None
    )
    action_checks = {
        "result_green": isinstance(action, dict)
        and action.get("result") == "GREEN",
        "transition_business_complete": isinstance(transition, Mapping)
        and transition.get("gameplay_action_executed") is True
        and transition.get("gameplay_action_complete") is True
        and transition.get("background_business_complete") is True,
        "ack_not_business_postcondition": isinstance(action, dict)
        and action.get("action_ack_is_business_postcondition") is False,
        "provider_postcondition_present": isinstance(postcondition, Mapping),
        "transition_ack_not_business_postcondition": isinstance(
            transition, Mapping
        )
        and transition.get("action_ack_is_business_postcondition") is False,
        "provider_checks_green": isinstance(checks, Mapping)
        and bool(checks)
        and all(value is True for value in checks.values()),
    }
    failed_action_checks = [
        label for label, passed in action_checks.items() if passed is not True
    ]
    if failed_action_checks:
        failure = {
            "schema_version": 1,
            "kind": "zg361_b3_manager_governance_runner_handler",
            "cell_id": cell_id,
            "result": "RED",
            "readiness": "static-ready",
            "implementation": "wired",
            "provider_status": "RED",
            "mcp_only": True,
            "gameplay_action_executed": isinstance(transition, Mapping)
            and transition.get("gameplay_action_executed") is True,
            "gameplay_action_complete": False,
            "action_cell_invoked": True,
            "action_ack_is_business_postcondition": False,
            "provider_observed_postcondition_required": True,
            "provider_observed_postcondition": postcondition,
            "typed_selector": dict(selected),
            "action": action,
            "checks": action_checks,
            "failed_checks": failed_action_checks,
            "failure_reason": (
                "joined B3 action did not provide its provider-observed "
                "business postcondition"
            ),
        }
        write_json(evidence_path, failure)
        raise acceptance.RunnerError(
            "phase-two B3 manager-governance action handler RED: "
            + ", ".join(failed_action_checks)
        )

    evidence = {
        **action,
        "cell_id": cell_id,
        "implementation": "wired",
        "provider_status": "available",
        "gameplay_action_executed": True,
        "gameplay_action_complete": True,
        "action_cell_invoked": True,
        "provider_observed_postcondition_required": True,
        "provider_observed_postcondition": postcondition,
        "typed_selector": dict(selected),
        "runner_checks": action_checks,
    }
    write_json(evidence_path, evidence)
    return evidence


def preflight_phase2_workforce_m360_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    owner_character_id: int,
    subject_character_id: int,
    seed_contract: dict[str, object],
    prior_lineage: dict[str, object],
) -> dict[str, object]:
    """Prove the narrow Workforce runner can execute both former blockers.

    This is a non-mutating preflight, not a gameplay receipt.  Exact player
    rebinding remains mediated by the dedicated typed-event fixture and must be
    confirmed by a later paused native snapshot.  The A/B/C lineage remains a
    managed save/restore operation and must prove three independent restores
    of one byte-identical checkpoint in the live action artifact.
    """

    evidence_path = artifacts / (
        "07d_phase2_workforce_m360_gameplay_action_preflight.json"
    )
    evidence: dict[str, object] = {
        "schema_version": 2,
        "evidence_class": "static_execution_preflight",
        "cell_id": (
            "workforce_collective_gameplay_action_and_postcondition_matrix"
        ),
        "result": "RED",
        "stage": "pre_mutation_runner_contract",
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "console_used": False,
        "test_decision_used": False,
        "gameplay_action_executed": False,
        "gameplay_business_postcondition_claimed": False,
        "live_proof_claimed": False,
        "checkpoint_created_for_workforce": False,
        "helper_invoked": False,
        "helper_entrypoint": (
            f"{run_m360_action_and_postcondition.__module__}."
            f"{run_m360_action_and_postcondition.__name__}"
        ),
        "expected_event_definition_key": M360_EVENT_DEFINITION_KEY,
        "owner_character_id": owner_character_id,
        "subject_character_id": subject_character_id,
        "required_routes": ["A", "B", "C"],
        "runtime_enabled_mods": None,
        "observed_public_surface": None,
        "fixture_contract": None,
        "prior_lineage": prior_lineage,
        "checks": {},
        "requirements": {},
        "missing_requirements": [],
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        for value, label in (
            (owner_character_id, "owner_character_id"),
            (subject_character_id, "subject_character_id"),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= 2**31 - 1
            ):
                raise acceptance.RunnerError(
                    f"phase-two Workforce #360 {label} is not a positive "
                    "CharacterID"
                )
        if owner_character_id == subject_character_id:
            raise acceptance.RunnerError(
                "phase-two Workforce #360 owner and received-self subject "
                "must differ"
            )

        capabilities = service.capabilities()
        if not isinstance(capabilities, dict):
            raise acceptance.RunnerError(
                "phase-two Workforce #360 capability surface is not an object"
            )
        bridge_capabilities = capabilities.get("bridge_capabilities")
        action_steps = capabilities.get("action_steps")
        public_capabilities = (
            {
                value
                for value in bridge_capabilities
                if isinstance(value, str)
            }
            if isinstance(bridge_capabilities, list)
            else set()
        )
        public_steps = (
            {value for value in action_steps if isinstance(value, str)}
            if isinstance(action_steps, list)
            else set()
        )
        required_fixture_files = (
            "descriptor.mod",
            "common/scripted_guis/zga_phase2_workforce_guis.txt",
            "events/zga_phase2_workforce_events.txt",
            "gui/zga_phase2_workforce_bridge.gui",
            (
                "gui/scripted_widgets/"
                "zga_phase2_workforce_scripted_widgets.txt"
            ),
            (
                "localization/english/"
                "zga_phase2_workforce_l_english.yml"
            ),
            (
                "localization/simp_chinese/"
                "zga_phase2_workforce_l_simp_chinese.yml"
            ),
        )
        fixture_source = PHASE2_WORKFORCE_ACTION_FIXTURE_SOURCE.resolve()
        fixture_snapshot = (
            isolated.tree_snapshot(fixture_source)
            if fixture_source.is_dir()
            else {}
        )
        expected_fixture_paths = set(required_fixture_files)
        observed_fixture_paths = {
            str(value).replace("\\", "/") for value in fixture_snapshot
        }
        fixture_file_set_exact = (
            observed_fixture_paths == expected_fixture_paths
        )
        fixture_bom_exact = fixture_file_set_exact and all(
            (fixture_source / relative).read_bytes().startswith(b"\xef\xbb\xbf")
            for relative in required_fixture_files
        )
        event_text = (
            (
                fixture_source
                / "events"
                / "zga_phase2_workforce_events.txt"
            ).read_text(encoding="utf-8-sig")
            if fixture_bom_exact
            else ""
        )
        gui_text = (
            (
                fixture_source
                / "common"
                / "scripted_guis"
                / "zga_phase2_workforce_guis.txt"
            ).read_text(encoding="utf-8-sig")
            if fixture_bom_exact
            else ""
        )
        exact_fixture_transition_contract = all(
            token in event_text
            for token in (
                "zga_phase2_workforce.1 = {",
                "zga_phase2_workforce.3 = {",
                (
                    "set_player_character = "
                    "scope:zga_phase2_workforce_owner"
                ),
                (
                    "set_player_character = "
                    "scope:zga_phase2_workforce_subject"
                ),
                "save_scope_as = zga_phase2_workforce_owner",
                "save_scope_as = zga_phase2_workforce_subject",
                "zg361_we_resume_m360_from_central_source_effect = {",
                "has_variable = zg361_we_m360_receipt_choice",
            )
        ) and event_text.count("set_player_character =") == 2
        fixture_summon_contract = all(
            token in gui_text
            for token in (
                "zga_phase2_workforce_summon_gui = {",
                "var:zg361_case_al_state = 4",
                "var:zg361_p2c_m360_source_status = 1",
                "trigger_event = zga_phase2_workforce.1",
            )
        )
        runtime = seed_contract.get("runtime")
        enabled_mods = (
            runtime.get("enabled_mods")
            if isinstance(runtime, dict)
            else None
        )
        evidence["runtime_enabled_mods"] = enabled_mods
        evidence["observed_public_surface"] = {
            "bridge_capabilities": sorted(public_capabilities),
            "action_steps": sorted(public_steps),
            "has_exact_character_player_rebind_method": callable(
                getattr(service, "set_player_character_v1", None)
            ),
            "has_dedicated_workforce_action_fixture_contract": (
                fixture_file_set_exact
                and fixture_bom_exact
                and exact_fixture_transition_contract
                and fixture_summon_contract
            ),
            "legacy_fixture_switch_accepted": False,
        }
        evidence["fixture_contract"] = {
            "source": str(fixture_source),
            "tree_sha256": (
                isolated.snapshot_digest(fixture_snapshot)
                if fixture_snapshot
                else None
            ),
            "expected_files": list(required_fixture_files),
            "observed_files": sorted(observed_fixture_paths),
            "player_transition_count": event_text.count(
                "set_player_character ="
            ),
            "fixture_file_set_exact": fixture_file_set_exact,
            "fixture_bom_exact": fixture_bom_exact,
            "exact_fixture_transition_contract": (
                exact_fixture_transition_contract
            ),
            "fixture_summon_contract": fixture_summon_contract,
            "acceptance_only": True,
            "release_included": False,
            "promo_included": False,
        }
        prior_scope = prior_lineage.get("scope")
        prior_pid_lineage = prior_lineage.get("pid_lineage")
        checks = {
            "helper_entrypoint_available": callable(
                run_m360_action_and_postcondition
            ),
            "owner_subject_distinct": owner_character_id
            != subject_character_id,
            "current_event_context_available": (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
                in public_capabilities
            ),
            "exact_event_option_ack_available": (
                "game.command.select-event-option-N" in public_capabilities
            ),
            "save_checkpoint_available": "save-checkpoint" in public_steps,
            "restore_checkpoint_available": (
                "restore-checkpoint" in public_steps
            ),
            "snapshot_method_available": callable(
                getattr(service, "snapshot", None)
            ),
            "save_checkpoint_method_available": callable(
                getattr(service, "save_checkpoint", None)
            ),
            "restore_checkpoint_method_available": callable(
                getattr(service, "restore_checkpoint", None)
            ),
            "event_context_method_available": callable(
                getattr(
                    service,
                    "query_current_event_window_context_v1",
                    None,
                )
            ),
            "select_event_option_method_available": callable(
                getattr(service, "select_event_option", None)
            ),
            "public_generic_character_rebind_remains_unavailable": not callable(
                getattr(service, "set_player_character_v1", None)
            ),
            "dedicated_action_fixture_exact_scope_switch_available": (
                fixture_file_set_exact
                and fixture_bom_exact
                and exact_fixture_transition_contract
                and fixture_summon_contract
                and callable(select_typed_fixture_player_transition)
            ),
            "same_pre_m360_checkpoint_three_route_restore_available": (
                "save-checkpoint" in public_steps
                and "restore-checkpoint" in public_steps
                and callable(getattr(service, "save_checkpoint", None))
                and callable(getattr(service, "restore_checkpoint", None))
                and callable(run_phase2_workforce_m360_gameplay_action_cell)
            ),
            "prior_lineage_can_extend_into_workforce_lineage": (
                prior_scope == "phase2_one_save_one_restore_two_pid_lineage"
                and isinstance(prior_pid_lineage, list)
                and len(prior_pid_lineage) == 2
            ),
        }
        evidence["checks"] = checks
        exact_transition_checks = (
            "helper_entrypoint_available",
            "owner_subject_distinct",
            "current_event_context_available",
            "exact_event_option_ack_available",
            "snapshot_method_available",
            "event_context_method_available",
            "select_event_option_method_available",
            "dedicated_action_fixture_exact_scope_switch_available",
        )
        restore_lineage_checks = (
            "save_checkpoint_available",
            "restore_checkpoint_available",
            "save_checkpoint_method_available",
            "restore_checkpoint_method_available",
            "same_pre_m360_checkpoint_three_route_restore_available",
            "prior_lineage_can_extend_into_workforce_lineage",
        )
        exact_transition_ready = all(
            checks[name] is True for name in exact_transition_checks
        )
        restore_lineage_ready = all(
            checks[name] is True for name in restore_lineage_checks
        )
        evidence["requirements"] = {
            "exact_owner_subject_player_transition": {
                "result": "RUNNER_READY" if exact_transition_ready else "RED",
                "revision_bound_by": (
                    "current-event query and select-event-option expected_revision"
                ),
                "identity_postcondition": (
                    "later paused native played CharacterID equals exact target"
                ),
            },
            "same_checkpoint_three_route_restore_lineage": {
                "result": "RUNNER_READY" if restore_lineage_ready else "RED",
                "shared_checkpoint": "one saved pre-zg361we.360 size/SHA-256",
                "independent_route_restores": ["A", "B", "C"],
                "additional_restores": [
                    "fixture activation",
                    "final frozen baseline",
                ],
            },
        }
        missing: list[dict[str, str]] = []
        if not exact_transition_ready:
            missing.append(
                {
                    "id": "exact_owner_subject_player_transition",
                    "reason": "one or more typed fixture/revision/identity checks failed",
                }
            )
        if not restore_lineage_ready:
            missing.append(
                {
                    "id": "same_checkpoint_three_route_restore_lineage",
                    "reason": "one or more shared-checkpoint restore lineage checks failed",
                }
            )
        evidence["missing_requirements"] = missing
        if missing:
            reason = "; ".join(
                f"{row['id']}: {row['reason']}" for row in missing
            )
            raise acceptance.RunnerError(
                "phase-two Workforce #360 static preflight RED before "
                f"mutation: {reason}"
            )
        evidence["result"] = "GREEN"
        evidence["stage"] = "static_runner_ready_live_proof_pending"
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["gameplay_action_executed"] = False
        evidence["helper_invoked"] = False
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            "phase-two Workforce #360 pre-mutation gate failed: "
            f"{error}"
        ) from error


def install_phase2_workforce_action_fixture(
    userdir: Path,
    bootstrap: dict[str, object],
    artifacts: Path,
) -> dict[str, object]:
    """Install one dormant external fixture for the next managed reload only."""

    evidence_path = artifacts / (
        "08a_phase2_workforce_action_fixture_install.json"
    )
    source = PHASE2_WORKFORCE_ACTION_FIXTURE_SOURCE.resolve()
    target = (
        userdir
        / "mod-content"
        / "phase2_workforce_action_fixture"
    ).resolve()
    outer = (userdir / "mod" / PHASE2_WORKFORCE_ACTION_FIXTURE_OUTER).resolve()
    dlc_load = (userdir / "dlc_load.json").resolve()
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_workforce_action_fixture_dynamic_install",
        "acceptance_only": True,
        "release_included": False,
        "promo_included": False,
        "seed_fixture_modified": False,
        "mcp_gameplay_path": True,
        "source": str(source),
        "target": str(target),
        "outer_descriptor": str(outer),
        "source_tree_sha256": None,
        "target_tree_sha256": None,
        "enabled_mods_before": None,
        "enabled_mods_after": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        required = (
            "descriptor.mod",
            "common/scripted_guis/zga_phase2_workforce_guis.txt",
            "events/zga_phase2_workforce_events.txt",
            "gui/zga_phase2_workforce_bridge.gui",
            (
                "gui/scripted_widgets/"
                "zga_phase2_workforce_scripted_widgets.txt"
            ),
            (
                "localization/english/"
                "zga_phase2_workforce_l_english.yml"
            ),
            (
                "localization/simp_chinese/"
                "zga_phase2_workforce_l_simp_chinese.yml"
            ),
        )
        if not source.is_dir() or any(
            not (source / relative).is_file() for relative in required
        ):
            raise acceptance.RunnerError(
                "phase-two Workforce action fixture source is incomplete"
            )
        source_snapshot = isolated.tree_snapshot(source)
        if len(source_snapshot) != len(required):
            raise acceptance.RunnerError(
                "phase-two Workforce action fixture has an unexpected file set"
            )
        for relative in required:
            payload = (source / relative).read_bytes()
            if not payload.startswith(b"\xef\xbb\xbf"):
                raise acceptance.RunnerError(
                    "phase-two Workforce action fixture lacks UTF-8 BOM: "
                    + relative
                )
        if target.exists() or outer.exists():
            raise acceptance.RunnerError(
                "phase-two Workforce action fixture target already exists"
            )
        if not isolated.is_relative_to(target, userdir.resolve()) or not (
            isolated.is_relative_to(outer, userdir.resolve())
        ):
            raise acceptance.RunnerError(
                "phase-two Workforce fixture target escaped the isolated userdir"
            )
        shutil.copytree(source, target)
        isolated.write_outer_descriptor(
            target / "descriptor.mod", outer, target
        )
        try:
            load_value = json.loads(dlc_load.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise acceptance.RunnerError(
                f"cannot read isolated dlc_load.json: {error}"
            ) from error
        if not isinstance(load_value, dict):
            raise acceptance.RunnerError(
                "isolated dlc_load.json root is not an object"
            )
        enabled_value = load_value.get("enabled_mods")
        enabled = enabled_value if isinstance(enabled_value, list) else None
        expected_before = bootstrap.get("enabled_mods")
        if (
            enabled is None
            or any(not isinstance(value, str) for value in enabled)
            or enabled != expected_before
        ):
            raise acceptance.RunnerError(
                "isolated enabled-mod baseline drifted before Workforce fixture"
            )
        fixture_mod = f"mod/{PHASE2_WORKFORCE_ACTION_FIXTURE_OUTER}"
        if fixture_mod in enabled:
            raise acceptance.RunnerError(
                "phase-two Workforce action fixture was enabled before its gate"
            )
        enabled_after = [*enabled, fixture_mod]
        load_value["enabled_mods"] = enabled_after
        write_json(dlc_load, load_value)
        target_snapshot = isolated.tree_snapshot(target)
        if target_snapshot != source_snapshot:
            raise acceptance.RunnerError(
                "phase-two Workforce action fixture copy changed bytes"
            )
        evidence.update(
            {
                "result": "GREEN",
                "source_tree_sha256": isolated.snapshot_digest(
                    source_snapshot
                ),
                "target_tree_sha256": isolated.snapshot_digest(
                    target_snapshot
                ),
                "enabled_mods_before": list(enabled),
                "enabled_mods_after": enabled_after,
                "failure_reason": None,
            }
        )
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two Workforce action fixture install failed: {error}"
        ) from error


def _phase2_checkpoint_payload(
    result: object,
    *,
    status: str,
    label: str,
) -> dict[str, object]:
    if not isinstance(result, dict) or result.get("accepted") is not True:
        raise acceptance.RunnerError(
            f"{label} checkpoint command was not acknowledged"
        )
    checkpoint_value = result.get("checkpoint")
    checkpoint = (
        checkpoint_value if isinstance(checkpoint_value, dict) else {}
    )
    size = checkpoint.get("size")
    sha256 = checkpoint.get("sha256")
    if not (
        checkpoint.get("status") == status
        and isinstance(size, int)
        and not isinstance(size, bool)
        and size > 0
        and isinstance(sha256, str)
        and re.fullmatch(r"[0-9A-Fa-f]{64}", sha256) is not None
    ):
        raise acceptance.RunnerError(
            f"{label} checkpoint lacks typed {status} size/hash proof"
        )
    return checkpoint


def _phase2_archive_checkpoint(
    checkpoint: Mapping[str, object],
    destination: Path,
    *,
    save_lineage_id: str,
) -> dict[str, object]:
    """Archive one materialized CK3 save without inventing checkpoint proof."""

    raw_path = checkpoint.get("path")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise acceptance.RunnerError(
            "phase-two checkpoint does not expose an absolute materialized path"
        )
    source = Path(raw_path).resolve()
    if not source.is_file():
        raise acceptance.RunnerError(
            f"phase-two checkpoint file is absent: {source}"
        )
    expected_size = checkpoint.get("size")
    expected_sha = str(checkpoint.get("sha256", "")).lower()
    if (
        source.stat().st_size != expected_size
        or isolated.sha256_file(source).lower() != expected_sha
    ):
        raise acceptance.RunnerError(
            "phase-two checkpoint bytes drifted from the native save receipt"
        )
    destination = Path(destination).resolve()
    if destination.exists():
        raise acceptance.RunnerError(
            f"phase-two checkpoint archive already exists: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    archived_sha = isolated.sha256_file(destination).upper()
    if destination.stat().st_size != expected_size or archived_sha.lower() != expected_sha:
        raise acceptance.RunnerError(
            "phase-two archived checkpoint differs from the native save receipt"
        )
    return {
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": archived_sha,
        "save_lineage_id": save_lineage_id,
    }


def _phase2_promo_receipt_sources(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    seed_install: Mapping[str, object],
    bootstrap: Mapping[str, object],
    runtime_identity: Mapping[str, object],
    game_version: str,
    executable_sha256: str,
) -> tuple[
    dict[str, object],
    Callable[..., Mapping[str, object]],
    Callable[..., Mapping[str, object]],
]:
    """Bind v2 receipt providers only to already-proven runner state."""

    contract = seed_install.get("contract")
    source_install = seed_install.get("source")
    if not isinstance(contract, Mapping) or not isinstance(source_install, Mapping):
        raise acceptance.RunnerError(
            "phase-two span receipts require the GREEN seed install contract/source"
        )
    provenance = contract.get("provenance")
    seed_runtime = contract.get("runtime")
    seed_source = contract.get("source")
    trees = bootstrap.get("tree_sha256")
    if not all(
        isinstance(value, Mapping)
        for value in (provenance, seed_runtime, seed_source, trees)
    ):
        raise acceptance.RunnerError(
            "phase-two span receipts lack seed/runtime tree provenance"
        )
    assert isinstance(provenance, Mapping)
    assert isinstance(seed_runtime, Mapping)
    assert isinstance(seed_source, Mapping)
    assert isinstance(trees, Mapping)
    current_product_tree = trees.get("product")
    enabled_mods = bootstrap.get("enabled_mods")
    if (
        seed_install.get("result") != "GREEN"
        or enabled_mods != [f"mod/{PRODUCT_OUTER}"]
        or trees.get("fixture") is not None
        or current_product_tree != seed_runtime.get("source_product_tree_sha256")
        or game_version != seed_runtime.get("game_version")
        or executable_sha256 != seed_runtime.get("executable_sha256")
    ):
        raise acceptance.RunnerError(
            "phase-two span receipts require exact seed product tree, game/EXE, "
            "and a product-only runtime mount"
        )
    source_git_commit = provenance.get("source_git_commit")
    if not isinstance(source_git_commit, str) or re.fullmatch(
        r"[0-9A-Fa-f]{40}", source_git_commit
    ) is None:
        raise acceptance.RunnerError(
            "phase-two seed provenance lacks its exact source commit"
        )
    raw_seed_path = source_install.get("path")
    if not isinstance(raw_seed_path, str):
        raise acceptance.RunnerError(
            "phase-two seed install lacks its materialized source path"
        )
    seed_path = Path(raw_seed_path).resolve()
    seed_sha = str(seed_source.get("sha256", "")).upper()
    if (
        not seed_path.is_file()
        or seed_path.stat().st_size != seed_source.get("bytes")
        or isolated.sha256_file(seed_path).upper() != seed_sha
    ):
        raise acceptance.RunnerError(
            "phase-two canonical seed bytes drifted before receipt binding"
        )
    save_lineage_id = f"zg361-phase2-seed-{seed_sha.lower()}"
    canonical_save = artifacts / "promo" / "checkpoints" / "canonical-seed.ck3"
    if canonical_save.exists():
        raise acceptance.RunnerError(
            f"phase-two canonical seed archive already exists: {canonical_save}"
        )
    canonical_save.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seed_path, canonical_save)
    if isolated.sha256_file(canonical_save).upper() != seed_sha:
        raise acceptance.RunnerError(
            "phase-two canonical seed archive hash mismatch"
        )
    canonical_record = {
        "path": str(canonical_save.resolve()),
        "bytes": canonical_save.stat().st_size,
        "sha256": seed_sha,
        "save_lineage_id": save_lineage_id,
    }
    harness_commit = git_text("rev-parse", "HEAD")
    lineage: dict[str, object] = {
        "schema_version": 1,
        "phase": "zhongguo_phase2",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "prior_phase_footage_used": False,
        "seed_lineage_id": save_lineage_id,
        "canonical_seed_save_sha256": seed_sha,
        "source": {
            "git_commit": source_git_commit,
            "tree_sha256": str(current_product_tree).upper(),
        },
        "capture_harness": {
            "git_commit": harness_commit,
            "runtime_source_kind": runtime_identity.get("runtime_source_kind"),
            "runtime_source_path": runtime_identity.get("runtime_source_path"),
        },
        "game": {
            "version": game_version,
            "exe_sha256": executable_sha256.upper(),
        },
        "mod_mount": {
            "kind": "product-only",
            "tree_sha256": str(current_product_tree).upper(),
            "enabled_mods": list(enabled_mods),
        },
    }

    def span_receipt_provider(
        scenario: object, phase: str
    ) -> Mapping[str, object]:
        if phase not in {"pre", "post"}:
            raise acceptance.RunnerError(
                f"phase-two span receipt phase is invalid: {phase}"
            )
        span_id = str(getattr(scenario, "span_id"))
        snapshot = service.snapshot()
        if not isinstance(snapshot, dict):
            raise acceptance.RunnerError(
                f"phase-two {span_id} {phase} snapshot is not an object"
            )
        before = _phase2_paused_binding(
            snapshot, label=f"phase-two {span_id} {phase} checkpoint"
        )
        result = service.save_checkpoint(expected_revision=int(before["revision"]))
        checkpoint = _phase2_checkpoint_payload(
            result, status="saved", label=f"phase-two {span_id} {phase}"
        )
        after_snapshot = service.snapshot()
        if not isinstance(after_snapshot, dict):
            raise acceptance.RunnerError(
                f"phase-two {span_id} {phase} post-save snapshot is not an object"
            )
        after = _phase2_paused_binding(
            after_snapshot, label=f"phase-two {span_id} {phase} post-save"
        )
        for key in (
            "bridge_pid",
            "connection_generation",
            "player_character_id",
            "date_raw",
        ):
            if after.get(key) != before.get(key):
                raise acceptance.RunnerError(
                    f"phase-two {span_id} {phase} save escaped its managed binding"
                )
        archived = _phase2_archive_checkpoint(
            checkpoint,
            artifacts / "promo" / "checkpoints" / span_id / f"{phase}.ck3",
            save_lineage_id=save_lineage_id,
        )
        pid = after["bridge_pid"]
        generation = after["connection_generation"]
        return {
            "schema_version": 1,
            "result": "GREEN",
            "span_id": span_id,
            "phase": phase,
            "session_id": f"managed-pid-{pid}-generation-{generation}",
            "bridge_pid": pid,
            "connection_generation": generation,
            "snapshot_id": after["snapshot_id"],
            "revision": after["revision"],
            "native_revision": after["native_revision"],
            "checkpoint": archived,
            "native_save_receipt": dict(checkpoint),
        }

    def seed_chain_provider(
        loaded_seed_proof: Mapping[str, object],
    ) -> Mapping[str, object]:
        observed = loaded_seed_proof.get("observed")
        if not isinstance(observed, Mapping):
            raise acceptance.RunnerError(
                "phase-two loaded-seed proof lacks observed binding"
            )
        loaded_save_sha = str(observed.get("save_sha256", "")).upper()
        if loaded_seed_proof.get("result") != "GREEN" or loaded_save_sha != seed_sha:
            raise acceptance.RunnerError(
                "phase-two loaded-seed proof is not continuous with canonical seed bytes"
            )
        pid = observed.get("bridge_pid")
        generation = observed.get("connection_generation")
        return {
            "schema_version": 1,
            "result": "GREEN",
            "seed_lineage_id": save_lineage_id,
            "canonical_save": canonical_record,
            "generated": {
                "save_sha256": seed_sha,
                "source_git_commit": source_git_commit,
                "source_product_tree_sha256": str(current_product_tree).upper(),
                "source_report_sha256": str(
                    provenance.get("source_report_sha256", "")
                ).upper(),
                "source_evidence_index_sha256": str(
                    provenance.get("source_evidence_index_sha256", "")
                ).upper(),
                "game_version": seed_runtime.get("game_version"),
                "game_exe_sha256": str(
                    seed_runtime.get("executable_sha256", "")
                ).upper(),
            },
            "loaded": {
                "session_id": f"managed-pid-{pid}-generation-{generation}",
                "bridge_pid": pid,
                "connection_generation": generation,
                "revision": observed.get("revision"),
                "native_revision": observed.get("native_revision"),
                "save_sha256": loaded_save_sha,
                "source_product_tree_sha256": str(current_product_tree).upper(),
                "game_version": game_version,
                "game_exe_sha256": executable_sha256.upper(),
                "mod_mount_tree_sha256": str(current_product_tree).upper(),
            },
        }

    return lineage, span_receipt_provider, seed_chain_provider


def _save_phase2_workforce_checkpoint(
    service: GameplayBridgeService,
    *,
    label: str,
) -> dict[str, object]:
    snapshot = service.snapshot()
    if not isinstance(snapshot, dict):
        raise acceptance.RunnerError(f"{label} save baseline is not an object")
    before = _phase2_paused_binding(snapshot, label=f"{label} save baseline")
    result = service.save_checkpoint(
        expected_revision=int(before["revision"])
    )
    checkpoint = _phase2_checkpoint_payload(
        result, status="saved", label=label
    )
    after_snapshot = service.snapshot()
    if not isinstance(after_snapshot, dict):
        raise acceptance.RunnerError(f"{label} post-save snapshot is not an object")
    after = _phase2_paused_binding(
        after_snapshot, label=f"{label} post-save snapshot"
    )
    if any(
        after[key] != before[key]
        for key in (
            "bridge_pid",
            "connection_generation",
            "player_character_id",
            "date_raw",
        )
    ):
        raise acceptance.RunnerError(
            f"{label} save escaped its paused binding"
        )
    return {
        "label": label,
        "before": before,
        "after": after,
        "result": result,
        "checkpoint": checkpoint,
    }


def _restore_phase2_workforce_checkpoint(
    service: GameplayBridgeService,
    *,
    checkpoint: dict[str, object],
    expected_player_character_id: int,
    label: str,
) -> dict[str, object]:
    before_snapshot = service.snapshot()
    if not isinstance(before_snapshot, dict):
        raise acceptance.RunnerError(
            f"{label} pre-restore snapshot is not an object"
        )
    before = _phase2_paused_binding(
        before_snapshot, label=f"{label} pre-restore"
    )
    result = service.restore_checkpoint(
        expected_revision=int(before["revision"])
    )
    restored = _phase2_checkpoint_payload(
        result, status="restored", label=label
    )
    lifecycle_value = result.get("lifecycle")
    lifecycle = lifecycle_value if isinstance(lifecycle_value, dict) else {}
    after_snapshot = service.snapshot()
    if not isinstance(after_snapshot, dict):
        raise acceptance.RunnerError(
            f"{label} post-restore snapshot is not an object"
        )
    after = _phase2_paused_binding(
        after_snapshot, label=f"{label} post-restore"
    )
    checks = {
        "pid_changed": after["bridge_pid"] != before["bridge_pid"],
        "generation_advanced_once": after["connection_generation"]
        == before["connection_generation"] + 1,
        "lifecycle_previous_pid_matches": lifecycle.get("previous_pid")
        == before["bridge_pid"],
        "lifecycle_pid_matches": lifecycle.get("pid")
        == after["bridge_pid"],
        "lifecycle_intent_restore": lifecycle.get("lifecycle_intent")
        == "restore",
        "player_restored": after["player_character_id"]
        == expected_player_character_id,
        "date_restored": after["date_raw"] == checkpoint.get("date_raw"),
        "size_preserved": restored.get("size") == checkpoint.get("size"),
        "sha256_preserved": str(restored.get("sha256", "")).lower()
        == str(checkpoint.get("sha256", "")).lower(),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise acceptance.RunnerError(
            f"{label} restore lineage RED: " + ", ".join(failed)
        )
    return {
        "label": label,
        "before": before,
        "after": after,
        "result": result,
        "restored_checkpoint": restored,
        "lifecycle": lifecycle,
        "checks": checks,
    }


def wait_for_phase2_exact_event(
    service: GameplayBridgeService,
    *,
    expected_definition_key: str,
    expected_player_character_id: int,
    timeout_s: float = 30.0,
    poll_interval_s: float = 0.05,
) -> dict[str, object]:
    """Wait for one exact current-event identity without timeline input."""

    if timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("phase-two exact-event wait timing is invalid")
    deadline = time.monotonic() + timeout_s
    last = "no active event"
    while time.monotonic() < deadline:
        snapshot = service.snapshot()
        if not isinstance(snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two exact-event snapshot is not an object"
            )
        binding = _phase2_paused_binding(
            snapshot, label="phase-two exact-event wait"
        )
        if binding["player_character_id"] != expected_player_character_id:
            raise acceptance.RunnerError(
                "phase-two exact-event wait changed played CharacterID"
            )
        if isinstance(snapshot.get("active_event"), dict):
            identity = query_event_definition_identity(service, snapshot)
            observed = identity.get("event_definition_key")
            if observed == expected_definition_key:
                return {"binding": binding, "identity": identity}
            raise acceptance.RunnerError(
                "phase-two exact-event wait encountered unexpected event "
                f"{observed!r}; expected {expected_definition_key!r}"
            )
        last = f"revision={binding['revision']} has no active event"
        if poll_interval_s:
            time.sleep(poll_interval_s)
    raise acceptance.RunnerError(
        "phase-two exact-event wait timed out: " + last
    )


def run_phase2_workforce_m360_gameplay_action_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    userdir: Path,
    bootstrap: dict[str, object],
    owner_character_id: int,
    subject_character_id: int,
    b2_owner_character_id: int,
    prior_lineage: dict[str, object],
) -> dict[str, object]:
    """Run A/B/C from one hash-identical checkpoint through typed MCP cards."""

    evidence_path = artifacts / (
        "08_phase2_workforce_m360_gameplay_action_cell.json"
    )
    owner = owner_character_id
    subject = subject_character_id
    evidence: dict[str, object] = {
        "schema_version": 2,
        "cell_id": (
            "workforce_collective_gameplay_action_and_postcondition_matrix"
        ),
        "result": "RED",
        "stage": "dynamic_fixture_activation",
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "console_used": False,
        "test_decision_used": False,
        "legacy_fixture_switch_accepted": False,
        "gameplay_action_executed": False,
        "checkpoint_created_for_workforce": False,
        "helper_invoked": False,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "prior_lineage": prior_lineage,
        "preflight": None,
        "fixture_install": None,
        "activation_checkpoint": None,
        "activation_restore": None,
        "activation_b2_clear": None,
        "shared_pre_m360_checkpoint": None,
        "routes": {
            route: {
                "result": "NOT_RUN",
                "restore_from_shared_pre_m360_checkpoint": False,
                "restore": None,
                "subject_to_owner_transition": None,
                "m360_event_identity": None,
                "action_and_postcondition": None,
                "owner_to_subject_transition": None,
            }
            for route in ("A", "B", "C")
        },
        "final_baseline_restore": None,
        "session_lineage": None,
        "checks": {},
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    shared_checkpoint: dict[str, object] | None = None
    final_restore_completed = False
    recovery_restore_completed = False
    restore_records: list[dict[str, object]] = []
    starting_binding: dict[str, object] | None = None

    def record_session_lineage(
        *, result: str, baseline_restored: bool
    ) -> dict[str, object] | None:
        if starting_binding is None:
            return None
        pid_lineage = [starting_binding["bridge_pid"]] + [
            row["after"]["bridge_pid"]
            for row in restore_records
            if isinstance(row, dict) and isinstance(row.get("after"), dict)
        ]
        generation_lineage = [
            starting_binding["connection_generation"]
        ] + [
            row["after"]["connection_generation"]
            for row in restore_records
            if isinstance(row, dict) and isinstance(row.get("after"), dict)
        ]
        return {
            "scope": (
                "phase2_workforce_activation_three_route_final_restore"
            ),
            "result": result,
            "baseline_restored": baseline_restored,
            "starting_binding": starting_binding,
            "restore_count": len(restore_records),
            "pid_lineage": pid_lineage,
            "connection_generation_lineage": generation_lineage,
            "restore_records": restore_records,
            "final_binding": (
                restore_records[-1]["after"]
                if restore_records
                else starting_binding
            ),
        }

    try:
        character_ids = (owner, subject, b2_owner_character_id)
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            for value in character_ids
        ) or owner == subject:
            raise acceptance.RunnerError(
                "phase-two Workforce action cell received invalid identities"
            )
        evidence["preflight"] = (
            preflight_phase2_workforce_m360_gameplay_action_cell(
                service,
                artifacts,
                owner_character_id=owner,
                subject_character_id=subject,
                seed_contract={
                    "runtime": {
                        "enabled_mods": bootstrap.get("enabled_mods")
                    }
                },
                prior_lineage=prior_lineage,
            )
        )
        initial_snapshot = service.snapshot()
        if not isinstance(initial_snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two Workforce initial snapshot is not an object"
            )
        starting_binding = _phase2_paused_binding(
            initial_snapshot, label="phase-two Workforce action baseline"
        )
        if starting_binding["player_character_id"] != subject:
            raise acceptance.RunnerError(
                "phase-two Workforce action baseline is not the received-self subject"
            )

        fixture_install = install_phase2_workforce_action_fixture(
            userdir, bootstrap, artifacts
        )
        evidence["fixture_install"] = fixture_install
        activation_save = _save_phase2_workforce_checkpoint(
            service, label="Workforce fixture activation"
        )
        evidence["activation_checkpoint"] = activation_save
        activation_restore = _restore_phase2_workforce_checkpoint(
            service,
            checkpoint=activation_save["checkpoint"],
            expected_player_character_id=subject,
            label="Workforce fixture activation",
        )
        restore_records.append(activation_restore)
        evidence["activation_restore"] = activation_restore

        activation_snapshot = service.snapshot()
        if not isinstance(activation_snapshot, dict):
            raise acceptance.RunnerError(
                "Workforce fixture activation snapshot is not an object"
            )
        if isinstance(activation_snapshot.get("active_event"), dict):
            activation_identity = query_event_definition_identity(
                service, activation_snapshot
            )
            activation_key = activation_identity.get("event_definition_key")
        else:
            activation_key = None
        if activation_key == B2_PIP_EVENT_DEFINITION_KEY:
            activation_dir = artifacts / "workforce_fixture_activation"
            activation_dir.mkdir(parents=True, exist_ok=True)
            evidence["activation_b2_clear"] = (
                run_phase2_b2_pip_gameplay_action_cell(
                    service,
                    activation_dir,
                    owner_character_id=b2_owner_character_id,
                )
            )
        elif activation_key not in {
            None,
            PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT,
        }:
            raise acceptance.RunnerError(
                "Workforce fixture activation encountered unexpected event "
                f"{activation_key!r}"
            )
        handoff_ready = wait_for_phase2_exact_event(
            service,
            expected_definition_key=PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT,
            expected_player_character_id=subject,
        )
        evidence["activation_handoff_ready"] = handoff_ready
        shared_save = _save_phase2_workforce_checkpoint(
            service, label="shared pre-M360 A/B/C"
        )
        shared_checkpoint = dict(shared_save["checkpoint"])
        evidence["shared_pre_m360_checkpoint"] = shared_save
        evidence["checkpoint_created_for_workforce"] = True
        evidence["stage"] = "three_independent_route_restores"
        write_json(evidence_path, evidence)

        for route in ("A", "B", "C"):
            route_row = evidence["routes"][route]
            if not isinstance(route_row, dict):
                raise acceptance.RunnerError(
                    f"Workforce route {route} evidence row is malformed"
                )
            route_directory = artifacts / "workforce_m360_routes" / route
            route_directory.mkdir(parents=True, exist_ok=True)
            restored = _restore_phase2_workforce_checkpoint(
                service,
                checkpoint=shared_checkpoint,
                expected_player_character_id=subject,
                label=f"Workforce route {route}",
            )
            restore_records.append(restored)
            route_row["restore"] = restored
            route_row["restore_from_shared_pre_m360_checkpoint"] = True
            route_row["handoff_event"] = wait_for_phase2_exact_event(
                service,
                expected_definition_key=(
                    PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT
                ),
                expected_player_character_id=subject,
            )
            to_owner = select_typed_fixture_player_transition(
                service,
                expected_event_definition_key=(
                    PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT
                ),
                expected_player_before=subject,
                expected_player_after=owner,
                owner_character_id=owner,
                subject_character_id=subject,
                owner_scope_name=PHASE2_WORKFORCE_OWNER_SCOPE,
                subject_scope_name=PHASE2_WORKFORCE_SUBJECT_SCOPE,
                evidence_path=(
                    route_directory / "subject_to_owner_transition.json"
                ),
            )
            route_row["subject_to_owner_transition"] = to_owner
            m360_ready = wait_for_phase2_exact_event(
                service,
                expected_definition_key=M360_EVENT_DEFINITION_KEY,
                expected_player_character_id=owner,
            )
            route_row["m360_event_identity"] = m360_ready
            switch_back_capture: dict[str, object] = {}

            def subject_service_factory(binding: object) -> GameplayBridgeService:
                binding_owner = getattr(binding, "owner_character_id", None)
                binding_subject = getattr(binding, "subject_character_id", None)
                if binding_owner != owner or binding_subject != subject:
                    raise acceptance.RunnerError(
                        "M360 helper binding disagrees with fixture owner/subject"
                    )
                transition = select_typed_fixture_player_transition(
                    service,
                    expected_event_definition_key=(
                        PHASE2_WORKFORCE_SWITCH_BACK_EVENT
                    ),
                    expected_player_before=owner,
                    expected_player_after=subject,
                    owner_character_id=owner,
                    subject_character_id=subject,
                    owner_scope_name=PHASE2_WORKFORCE_OWNER_SCOPE,
                    subject_scope_name=PHASE2_WORKFORCE_SUBJECT_SCOPE,
                    evidence_path=(
                        route_directory / "owner_to_subject_transition.json"
                    ),
                )
                switch_back_capture.update(transition)
                return service

            evidence["helper_invoked"] = True
            matrix = run_m360_action_and_postcondition(
                service,
                route=route,
                subject_service_factory=subject_service_factory,
                evidence_directory=route_directory,
                max_timeline_steps=0,
                post_ack_event_definition_allowlist=(
                    PHASE2_WORKFORCE_SWITCH_BACK_EVENT,
                ),
            )
            evidence["gameplay_action_executed"] = True
            route_row["action_and_postcondition"] = matrix
            route_row["owner_to_subject_transition"] = switch_back_capture
            if not (
                matrix.get("result") == "GREEN"
                and switch_back_capture.get("result") == "GREEN"
            ):
                raise acceptance.RunnerError(
                    f"Workforce route {route} returned a non-GREEN matrix"
                )
            route_row["result"] = "GREEN"
            write_json(evidence_path, evidence)

        final_restore = _restore_phase2_workforce_checkpoint(
            service,
            checkpoint=shared_checkpoint,
            expected_player_character_id=subject,
            label="Workforce final frozen baseline",
        )
        restore_records.append(final_restore)
        evidence["final_baseline_restore"] = final_restore
        final_restore_completed = True
        final_handoff = wait_for_phase2_exact_event(
            service,
            expected_definition_key=PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT,
            expected_player_character_id=subject,
        )
        evidence["final_handoff_event"] = final_handoff
        pid_lineage = [starting_binding["bridge_pid"]] + [
            row["after"]["bridge_pid"] for row in restore_records
        ]
        generation_lineage = [starting_binding["connection_generation"]] + [
            row["after"]["connection_generation"] for row in restore_records
        ]
        checkpoint_hash = str(shared_checkpoint["sha256"]).lower()
        checks = {
            "fixture_installed_only_for_phase2": fixture_install.get("result")
            == "GREEN"
            and fixture_install.get("acceptance_only") is True
            and fixture_install.get("release_included") is False
            and fixture_install.get("promo_included") is False,
            "shared_checkpoint_hashed": re.fullmatch(
                r"[0-9a-f]{64}", checkpoint_hash
            )
            is not None,
            "three_routes_green": all(
                isinstance(evidence["routes"].get(route), dict)
                and evidence["routes"][route].get("result") == "GREEN"
                for route in ("A", "B", "C")
            ),
            "three_independent_route_restores": len(restore_records) == 5
            and all(
                row["restored_checkpoint"].get("sha256", "").lower()
                == checkpoint_hash
                for row in restore_records[1:]
            ),
            "final_baseline_restored": final_restore_completed,
            "pid_lineage_unique": len(set(pid_lineage)) == len(pid_lineage),
            "generation_lineage_consecutive": generation_lineage
            == list(
                range(
                    int(generation_lineage[0]),
                    int(generation_lineage[0]) + len(generation_lineage),
                )
            ),
            "native_subject_restored": final_restore["after"][
                "player_character_id"
            ]
            == subject,
        }
        evidence["checks"] = checks
        failed = [name for name, passed in checks.items() if passed is not True]
        if failed:
            raise acceptance.RunnerError(
                "Workforce #360 A/B/C matrix RED: " + ", ".join(failed)
            )
        evidence["session_lineage"] = record_session_lineage(
            result="GREEN", baseline_restored=True
        )
        evidence["result"] = "GREEN"
        evidence["stage"] = "complete_and_baseline_restored"
        evidence["failure_reason"] = None
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        if shared_checkpoint is not None and not final_restore_completed:
            try:
                recovery = _restore_phase2_workforce_checkpoint(
                    service,
                    checkpoint=shared_checkpoint,
                    expected_player_character_id=subject,
                    label="Workforce failure recovery baseline",
                )
                restore_records.append(recovery)
                evidence["failure_recovery_restore"] = recovery
                recovery_restore_completed = True
            except BaseException as recovery_error:
                evidence["failure_recovery_restore"] = {
                    "result": "RED",
                    "failure_reason": (
                        f"{type(recovery_error).__name__}: {recovery_error}"
                    ),
                }
        evidence["session_lineage"] = record_session_lineage(
            result=(
                "RED_RECOVERED"
                if final_restore_completed or recovery_restore_completed
                else "RED_UNRECOVERED"
            ),
            baseline_restored=(
                final_restore_completed or recovery_restore_completed
            ),
        )
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two Workforce #360 action matrix failed: {error}"
        ) from error


def wait_for_phase2_paused_snapshot(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    timeout_s: float = PHASE2_PAUSED_READINESS_TIMEOUT_S,
    poll_interval_s: float = 0.1,
) -> dict[str, object]:
    """Wait only through MCP for a paused map; never navigate by pixels."""

    evidence_path = artifacts / "04_phase2_paused_readiness.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_mcp_only_paused_map",
        "tracked_ck3_pid": tracked_ck3_pid,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "last_snapshot": None,
        "binding": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    if timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("phase-two paused readiness timing is invalid")
    deadline = time.monotonic() + timeout_s
    last_error = "no semantic snapshot was published"
    try:
        while time.monotonic() < deadline:
            try:
                snapshot = service.snapshot()
                if not isinstance(snapshot, dict):
                    raise TypeError("snapshot response is not an object")
                evidence["last_snapshot"] = snapshot
                binding = _phase2_paused_binding(
                    snapshot, label="phase-two paused readiness"
                )
                if binding["bridge_pid"] != tracked_ck3_pid:
                    raise acceptance.RunnerError(
                        "phase-two paused snapshot moved to an unexpected PID "
                        f"before restore: {binding['bridge_pid']}"
                    )
                evidence["result"] = "GREEN"
                evidence["binding"] = binding
                write_json(evidence_path, evidence)
                return snapshot
            except acceptance.RunnerError:
                raise
            except Exception as error:
                last_error = f"{type(error).__name__}: {error}"
            if poll_interval_s:
                time.sleep(poll_interval_s)
        raise acceptance.RunnerError(
            "phase-two MCP paused readiness timed out: " + last_error
        )
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two MCP paused readiness failed: {error}"
        ) from error


def wait_for_phase2_b2_pip_prompt(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    baseline_binding: dict[str, int | str],
    timeout_s: float = PHASE2_B2_PROMPT_TIMEOUT_S,
    poll_interval_s: float = 0.1,
) -> dict[str, object]:
    """Advance only an event-free map until the exact B2 prompt is paused."""

    evidence_path = artifacts / "05_phase2_b2_pip_prompt_readiness.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_b2_prompt_mcp_only_readiness",
        "expected_event_definition_key": B2_PIP_EVENT_DEFINITION_KEY,
        "baseline_binding": baseline_binding,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "observations": [],
        "submissions": [],
        "event_identity": None,
        "binding": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    if timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("phase-two B2 prompt readiness timing is invalid")

    expected_pid = int(baseline_binding["bridge_pid"])
    expected_generation = int(baseline_binding["connection_generation"])
    expected_player = int(baseline_binding["player_character_id"])
    starting_date = int(baseline_binding["date_raw"])
    deadline = time.monotonic() + timeout_s

    def fail(reason: str) -> None:
        raise acceptance.RunnerError(reason)

    def accepted_submission(value: object, step: str) -> None:
        status = value.get("status") if isinstance(value, dict) else None
        if not (
            isinstance(value, dict)
            and value.get("accepted") is True
            and (
                status == "submitted"
                or (step == "pause-map" and status == "already_paused")
            )
        ):
            fail(f"phase-two B2 prompt {step} ACK was not accepted")

    try:
        while time.monotonic() < deadline:
            snapshot = service.snapshot()
            if not isinstance(snapshot, dict):
                fail("phase-two B2 prompt snapshot is not an object")
            revision = snapshot.get("revision")
            date_raw = snapshot.get("date_raw")
            played_character = snapshot.get("played_character")
            player = (
                played_character.get("character_id")
                if isinstance(played_character, dict)
                else None
            )
            diagnostics = snapshot.get("diagnostics")
            pid = (
                diagnostics.get("bridge_pid")
                if isinstance(diagnostics, dict)
                else None
            )
            generation = (
                diagnostics.get("connection_generation")
                if isinstance(diagnostics, dict)
                else None
            )
            active_event = snapshot.get("active_event")
            event_instance_id = (
                active_event.get("instance_id")
                if isinstance(active_event, dict)
                else None
            )
            observation = {
                "snapshot_id": snapshot.get("snapshot_id"),
                "revision": revision,
                "native_revision": snapshot.get("native_revision"),
                "date_raw": date_raw,
                "paused": snapshot.get("paused"),
                "speed": snapshot.get("speed"),
                "player_character_id": player,
                "bridge_pid": pid,
                "connection_generation": generation,
                "active_event_instance_id": event_instance_id,
                "active_event_option_count": (
                    active_event.get("option_count")
                    if isinstance(active_event, dict)
                    else None
                ),
            }
            observations = evidence["observations"]
            assert isinstance(observations, list)
            observations.append(observation)
            if (
                isinstance(revision, bool)
                or not isinstance(revision, int)
                or revision < 0
                or isinstance(date_raw, bool)
                or not isinstance(date_raw, int)
                or date_raw < starting_date
                or date_raw
                > starting_date
                + PHASE2_B2_EVENT_WAIT_MAX_DAYS * CK3_DATE_RAW_HOURS_PER_DAY
                or player != expected_player
                or pid != expected_pid
                or generation != expected_generation
                or snapshot.get("map_ready") is not True
            ):
                fail(
                    "phase-two B2 prompt escaped its frozen date/player/PID binding"
                )

            if isinstance(active_event, dict):
                if snapshot.get("paused") is not True:
                    submission = service.execute_step(
                        "pause-map", expected_revision=revision
                    )
                    accepted_submission(submission, "pause-map")
                    submissions = evidence["submissions"]
                    assert isinstance(submissions, list)
                    submissions.append(submission)
                    if poll_interval_s:
                        time.sleep(poll_interval_s)
                    continue
                identity = query_event_definition_identity(service, snapshot)
                evidence["event_identity"] = identity
                if (
                    identity.get("event_definition_key")
                    != B2_PIP_EVENT_DEFINITION_KEY
                ):
                    fail(
                        "phase-two B2 readiness encountered an unexpected real "
                        f"event: {identity.get('event_definition_key')!r}"
                    )
                binding = _phase2_paused_binding(
                    snapshot, label="phase-two B2 prompt readiness"
                )
                evidence["binding"] = binding
                evidence["result"] = "GREEN"
                evidence["failure_reason"] = None
                write_json(evidence_path, evidence)
                return snapshot

            if snapshot.get("speed") != 1:
                submission = service.execute_step(
                    "set-speed-1", expected_revision=revision
                )
                accepted_submission(submission, "set-speed-1")
                submissions = evidence["submissions"]
                assert isinstance(submissions, list)
                submissions.append(submission)
            elif snapshot.get("paused") is True:
                submission = service.execute_step(
                    "resume-map", expected_revision=revision
                )
                accepted_submission(submission, "resume-map")
                submissions = evidence["submissions"]
                assert isinstance(submissions, list)
                submissions.append(submission)
            if poll_interval_s:
                time.sleep(poll_interval_s)
        fail("phase-two MCP timed out before the exact zg361b2.40 prompt")
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two B2 prompt readiness failed: {error}"
        ) from error
    raise AssertionError("unreachable")


def run_phase2_save_restore_lineage(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    checkpointed_gameplay_action: Callable[[], dict[str, object]] | None = None,
) -> dict[str, object]:
    """Prove one frozen checkpoint/action/restore topology without visual input."""

    evidence_path = artifacts / "06_phase2_save_restore_lineage.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_one_save_one_restore_two_pid_lineage",
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "before": None,
        "after_save": None,
        "checkpointed_gameplay_action": None,
        "checkpointed_gameplay_action_green": None,
        "checkpointed_gameplay_action_failure": None,
        "restore_completed_after_action_failure": False,
        "before_restore": None,
        "after_restore": None,
        "save_result": None,
        "restore_result": None,
        "checks": {},
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        before_snapshot = service.snapshot()
        if not isinstance(before_snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two save baseline is not a snapshot object"
            )
        before = _phase2_paused_binding(
            before_snapshot, label="phase-two save baseline"
        )
        evidence["before"] = before
        if before["bridge_pid"] != tracked_ck3_pid:
            raise acceptance.RunnerError(
                "phase-two save baseline is not bound to the first tracked PID"
            )

        save_result = service.save_checkpoint(
            expected_revision=int(before["revision"])
        )
        evidence["save_result"] = save_result
        if not isinstance(save_result, dict):
            raise acceptance.RunnerError("save-checkpoint returned a non-object")
        saved_checkpoint = save_result.get("checkpoint")
        if not (
            save_result.get("accepted") is True
            and isinstance(saved_checkpoint, dict)
            and saved_checkpoint.get("status") == "saved"
            and isinstance(saved_checkpoint.get("size"), int)
            and not isinstance(saved_checkpoint.get("size"), bool)
            and saved_checkpoint.get("size", 0) > 0
            and isinstance(saved_checkpoint.get("sha256"), str)
            and re.fullmatch(r"[0-9A-Fa-f]{64}", saved_checkpoint["sha256"])
        ):
            raise acceptance.RunnerError(
                "save-checkpoint did not materialize an acknowledged hashed save"
            )

        after_save_snapshot = service.snapshot()
        if not isinstance(after_save_snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two post-save snapshot is not an object"
            )
        after_save = _phase2_paused_binding(
            after_save_snapshot, label="phase-two post-save snapshot"
        )
        evidence["after_save"] = after_save
        after_save_capabilities = service.capabilities()
        restore_steps = (
            {
                item
                for item in after_save_capabilities.get("action_steps", [])
                if isinstance(item, str)
            }
            if isinstance(after_save_capabilities, dict)
            else set()
        )
        if "restore-checkpoint" not in restore_steps:
            raise acceptance.RunnerError(
                "MCP capability RED: restore-checkpoint did not materialize after save"
            )

        before_restore = after_save
        action_failure: BaseException | None = None
        if checkpointed_gameplay_action is not None:
            try:
                action_evidence = checkpointed_gameplay_action()
                evidence["checkpointed_gameplay_action"] = action_evidence
                if not (
                    isinstance(action_evidence, dict)
                    and action_evidence.get("result") == "GREEN"
                ):
                    action_failure = acceptance.RunnerError(
                        "checkpointed gameplay action returned a non-GREEN result"
                    )
                    evidence["checkpointed_gameplay_action_failure"] = {
                        "error_type": type(action_failure).__name__,
                        "error": str(action_failure),
                    }
            except BaseException as error:
                action_failure = error
                evidence["checkpointed_gameplay_action_failure"] = {
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            # The action helper proves its own product postcondition.  Take a
            # new paused binding even after a typed action RED, so restore is
            # revision-bound to the state that actually follows the attempt,
            # never to a pre-action ACK.  This keeps a failed mutation from
            # escaping its frozen checkpoint transaction.
            before_restore_snapshot = service.snapshot()
            if not isinstance(before_restore_snapshot, dict):
                raise acceptance.RunnerError(
                    "phase-two pre-restore snapshot is not an object"
                )
            before_restore = _phase2_paused_binding(
                before_restore_snapshot,
                label="phase-two checkpointed-action postcondition",
            )
        evidence["before_restore"] = before_restore
        write_json(evidence_path, evidence)

        restore_result = service.restore_checkpoint(
            expected_revision=int(before_restore["revision"])
        )
        evidence["restore_result"] = restore_result
        if not isinstance(restore_result, dict):
            raise acceptance.RunnerError(
                "restore-checkpoint returned a non-object"
            )
        restored_checkpoint = restore_result.get("checkpoint")
        lifecycle = restore_result.get("lifecycle")
        restored_date = restore_result.get("restored_date")
        if not (
            restore_result.get("accepted") is True
            and restore_result.get("status") == "restored"
            and isinstance(restored_checkpoint, dict)
            and restored_checkpoint.get("status") == "restored"
            and isinstance(lifecycle, dict)
            and isinstance(restored_date, dict)
        ):
            raise acceptance.RunnerError(
                "restore-checkpoint did not return its lifecycle/checkpoint proof"
            )

        after_restore_snapshot = service.snapshot()
        if not isinstance(after_restore_snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two restored snapshot is not an object"
            )
        after_restore = _phase2_paused_binding(
            after_restore_snapshot, label="phase-two restored snapshot"
        )
        evidence["after_restore"] = after_restore
        final_capabilities = service.capabilities()
        final_diagnostics = (
            final_capabilities.get("diagnostics")
            if isinstance(final_capabilities, dict)
            else None
        )
        checkpointed_action_value = evidence.get(
            "checkpointed_gameplay_action"
        )
        timeline_advance_expected = (
            isinstance(checkpointed_action_value, dict)
            and checkpointed_action_value.get("timeline_advance_expected")
            is True
        )
        evidence["checkpointed_gameplay_action_green"] = (
            checkpointed_gameplay_action is None
            or (
                isinstance(checkpointed_action_value, dict)
                and checkpointed_action_value.get("result") == "GREEN"
            )
        )
        checks = {
            "first_pid_matches_tracked": before["bridge_pid"]
            == tracked_ck3_pid,
            "save_stayed_on_first_pid": after_save["bridge_pid"]
            == before["bridge_pid"],
            "save_stayed_on_first_generation": after_save[
                "connection_generation"
            ]
            == before["connection_generation"],
            "action_stayed_on_first_pid": before_restore["bridge_pid"]
            == before["bridge_pid"],
            "action_stayed_on_first_generation": before_restore[
                "connection_generation"
            ]
            == before["connection_generation"],
            "action_stayed_on_player": before_restore[
                "player_character_id"
            ]
            == before["player_character_id"],
            "action_date_not_before_checkpoint": before_restore["date_raw"]
            >= before["date_raw"],
            "action_date_contract_matches": (
                before_restore["date_raw"] >= before["date_raw"]
                if action_failure is not None
                else (
                    before_restore["date_raw"] > before["date_raw"]
                    if timeline_advance_expected
                    else before_restore["date_raw"] == before["date_raw"]
                )
            ),
            "second_pid_is_distinct": after_restore["bridge_pid"]
            != before["bridge_pid"],
            "lifecycle_previous_pid_matches": lifecycle.get("previous_pid")
            == before["bridge_pid"],
            "lifecycle_second_pid_matches": lifecycle.get("pid")
            == after_restore["bridge_pid"],
            "connection_generation_advanced": after_restore[
                "connection_generation"
            ]
            == before["connection_generation"] + 1,
            "final_capabilities_bind_second_pid": isinstance(
                final_diagnostics, dict
            )
            and final_diagnostics.get("bridge_pid")
            == after_restore["bridge_pid"]
            and final_diagnostics.get("connection_generation")
            == after_restore["connection_generation"],
            "player_identity_restored": after_restore["player_character_id"]
            == before["player_character_id"],
            "save_date_did_not_advance": after_save["date_raw"]
            == before["date_raw"],
            "snapshot_date_restored": after_restore["date_raw"]
            == before["date_raw"],
            "restore_result_date_matches_snapshot": restored_date.get(
                "date_raw"
            )
            == after_restore["date_raw"],
            "checkpoint_size_preserved": restored_checkpoint.get("size")
            == saved_checkpoint.get("size"),
            "checkpoint_sha256_preserved": str(
                restored_checkpoint.get("sha256", "")
            ).lower()
            == str(saved_checkpoint.get("sha256", "")).lower(),
            "lifecycle_previous_generation_matches": lifecycle.get(
                "previous_connection_generation"
            )
            == before["connection_generation"],
            "lifecycle_new_generation_matches": lifecycle.get(
                "connection_generation"
            )
            == after_restore["connection_generation"],
        }
        evidence["checks"] = checks
        topology_failed = [
            label for label, passed in checks.items() if passed is not True
        ]
        if topology_failed:
            raise acceptance.RunnerError(
                "phase-two save/restore lineage RED: "
                + ", ".join(topology_failed)
            )
        evidence["first_pid"] = before["bridge_pid"]
        evidence["second_pid"] = after_restore["bridge_pid"]
        evidence["pid_lineage"] = [
            before["bridge_pid"],
            after_restore["bridge_pid"],
        ]
        evidence["first_connection_generation"] = before[
            "connection_generation"
        ]
        evidence["second_connection_generation"] = after_restore[
            "connection_generation"
        ]
        evidence["connection_generation_lineage"] = [
            before["connection_generation"],
            after_restore["connection_generation"],
        ]
        evidence["two_pid_lineage_proven"] = True
        evidence["result"] = "GREEN"
        evidence["failure_reason"] = None
        if action_failure is not None:
            evidence["restore_completed_after_action_failure"] = True
            write_json(evidence_path, evidence)
            if isinstance(action_failure, acceptance.RunnerError):
                raise action_failure
            raise acceptance.RunnerError(
                "checkpointed gameplay action failed after its baseline was "
                f"restored: {action_failure}"
            ) from action_failure
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        if evidence.get("restore_completed_after_action_failure") is True:
            if isinstance(error, acceptance.RunnerError):
                raise
            raise acceptance.RunnerError(
                f"checkpointed gameplay action failed: {error}"
            ) from error
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two save/restore lineage failed: {error}"
        ) from error


def phase2_native_session_liveness_gate(
    service: GameplayBridgeService,
    supervisor: dict[str, object],
    artifacts: Path,
    *,
    scenario_evidence: object,
) -> dict[str, object]:
    """Bind the supervisor and driver to the final recorded restore PID."""

    evidence_path = artifacts / "08_phase2_native_session_liveness.json"
    scenario = scenario_evidence if isinstance(scenario_evidence, dict) else {}
    lineage_projection = _phase2_expected_session_lineage(scenario)
    lineage_value = lineage_projection.get("base")
    lineage = lineage_value if isinstance(lineage_value, dict) else {}
    pid_lineage_value = lineage_projection.get("pid_lineage")
    pid_lineage = (
        pid_lineage_value if isinstance(pid_lineage_value, list) else []
    )
    generation_lineage_value = lineage_projection.get(
        "connection_generation_lineage"
    )
    generation_lineage = (
        generation_lineage_value
        if isinstance(generation_lineage_value, list)
        else []
    )
    expected_pid = pid_lineage[-1] if pid_lineage else None
    expected_generation = (
        generation_lineage[-1] if generation_lineage else None
    )
    session_done = supervisor.get("session_done")
    session_thread = supervisor.get("session_thread")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_post_restore_supervisor_liveness",
        "mcp_only": True,
        "expected_pid": expected_pid,
        "expected_connection_generation": expected_generation,
        "lineage_projection": lineage_projection,
        "capabilities": None,
        "snapshot": None,
        "binding": None,
        "checks": {},
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        capabilities = service.capabilities()
        snapshot = service.snapshot()
        if not isinstance(capabilities, dict) or not isinstance(snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two liveness queries returned a non-object"
            )
        binding = _phase2_paused_binding(
            snapshot, label="phase-two post-restore liveness"
        )
        diagnostics_value = capabilities.get("diagnostics")
        diagnostics = (
            diagnostics_value if isinstance(diagnostics_value, dict) else {}
        )
        checks = {
            "supervisor_handle_valid": isinstance(session_done, threading.Event)
            and isinstance(session_thread, threading.Thread),
            "supervisor_not_done": isinstance(session_done, threading.Event)
            and not session_done.is_set(),
            "supervisor_thread_alive": isinstance(
                session_thread, threading.Thread
            )
            and session_thread.is_alive(),
            "lineage_green": lineage.get("result") == "GREEN",
            "lineage_two_pid_proven": lineage.get(
                "two_pid_lineage_proven"
            )
            is True,
            "full_lineage_lengths_match": bool(pid_lineage)
            and len(pid_lineage) == len(generation_lineage),
            "full_pid_lineage_unique": bool(pid_lineage)
            and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
                for value in pid_lineage
            )
            and len(set(pid_lineage)) == len(pid_lineage),
            "full_generation_lineage_consecutive": bool(
                generation_lineage
            )
            and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
                for value in generation_lineage
            )
            and generation_lineage
            == list(
                range(
                    generation_lineage[0],
                    generation_lineage[0] + len(generation_lineage),
                )
            ),
            "workforce_join_matches_base_final": (
                lineage_projection.get(
                    "workforce_join_matches_base_final"
                )
                is True
            ),
            "capabilities_connected": diagnostics.get("connected") is True,
            "capabilities_pid_matches_second": diagnostics.get("bridge_pid")
            == expected_pid,
            "capabilities_generation_matches_second": diagnostics.get(
                "connection_generation"
            )
            == expected_generation,
            "snapshot_pid_matches_second": binding["bridge_pid"]
            == expected_pid,
            "snapshot_generation_matches_second": binding[
                "connection_generation"
            ]
            == expected_generation,
        }
        evidence["capabilities"] = capabilities
        evidence["snapshot"] = snapshot
        evidence["binding"] = binding
        evidence["checks"] = checks
        failed = [label for label, passed in checks.items() if passed is not True]
        if failed:
            raise acceptance.RunnerError(
                "phase-two supervisor liveness RED: " + ", ".join(failed)
            )
        evidence["result"] = "GREEN"
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two supervisor liveness failed: {error}"
        ) from error


def _loader_error_matches(payload: bytes) -> list[dict[str, object]]:
    """Return explicit project-attributed loader signatures in one log image.

    CK3 writes non-fatal script-usage diagnostics to ``error.log`` too.  Those
    lines remain in the frozen full-log artifact and its attributed-line count,
    but only the bounded signature catalog below is a loader failure gate.
    """

    lines = payload.decode("utf-8", errors="replace").splitlines()
    matches: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        # A ``Script system error!`` line is a record header: its error detail
        # and script stack follow it.  Looking backward lets the preceding,
        # unrelated record lend a project token to a vanilla error when the two
        # records are adjacent (observed in the r8 seed live artifact).
        context_start = index if "script system error" in lowered else max(0, index - 2)
        context_lines = lines[context_start : index + 3]
        context = " ".join(context_lines).lower()
        attributed_line = any(
            token in lowered for token in PROJECT_TOKENS
        )
        attributed_context = any(
            token in context for token in PROJECT_TOKENS
        )
        categories = [
            category
            for category, patterns in LOADER_ERROR_SIGNATURES.items()
            if any(pattern in lowered for pattern in patterns)
        ]
        if categories and not attributed_context:
            categories = []
        for category in categories:
            matches.append(
                {
                    "category": category,
                    "line_number": index + 1,
                    "line": line,
                    "context_start_line": context_start + 1,
                    "context": context_lines,
                    "project_attributed_line": attributed_line,
                    "project_attributed_context": attributed_context,
                }
            )
    return matches


def scan_loader_error_log(
    userdir: Path,
    artifacts: Path,
    *,
    timeout_s: float = LOADER_ERROR_LOG_TIMEOUT_S,
    stable_samples: int = 3,
    poll_interval_s: float = 0.25,
    minimum_quiet_s: float = LOADER_ERROR_LOG_MINIMUM_QUIET_S,
) -> dict[str, object]:
    """Freeze and batch-scan ``error.log`` for product loader failures."""

    if (
        timeout_s <= 0
        or stable_samples < 1
        or poll_interval_s < 0
        or minimum_quiet_s < 0
        or timeout_s <= minimum_quiet_s
    ):
        raise ValueError("loader error-log timing parameters are invalid")
    source = userdir / "logs" / "error.log"
    frozen = artifacts / "02_loader_error.log"
    evidence_path = artifacts / "02_loader_error_scan.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "zhongguo_loader_error_log_batch_scan",
        "source": str(source),
        "full_log_artifact": frozen.name,
        "full_log_size": None,
        "full_log_sha256": None,
        "project_attributed_line_count": None,
        "stable_samples_required": stable_samples,
        "minimum_quiet_seconds_required": minimum_quiet_s,
        "quiet_seconds_observed": 0.0,
        "loader_error_detected_before_quiet_window": False,
        "stable_observations": [],
        "project_tokens": list(PROJECT_TOKENS),
        "signature_catalog": {
            key: list(patterns)
            for key, patterns in LOADER_ERROR_SIGNATURES.items()
        },
        "matches": [],
        "counts_by_category": {},
        "failure_reason": None,
    }
    deadline = time.monotonic() + timeout_s
    previous_identity: tuple[int, str] | None = None
    identity_since: float | None = None
    consecutive = 0
    payload: bytes | None = None
    matches: list[dict[str, object]] = []

    try:
        while time.monotonic() < deadline:
            observed_at = time.monotonic()
            try:
                candidate = source.read_bytes()
            except OSError:
                candidate = None
            if candidate is not None:
                identity = (len(candidate), release.sha256_bytes(candidate))
                if identity == previous_identity:
                    consecutive += 1
                else:
                    previous_identity = identity
                    identity_since = observed_at
                    consecutive = 1
                payload = candidate
                quiet_seconds = (
                    max(0.0, observed_at - identity_since)
                    if identity_since is not None
                    else 0.0
                )
                matches = _loader_error_matches(candidate)
                observations = evidence["stable_observations"]
                if not isinstance(observations, list):
                    raise RuntimeError(
                        "loader error-log evidence schema is invalid"
                    )
                observations.append(
                    {
                        "size": identity[0],
                        "sha256": identity[1],
                        "consecutive": consecutive,
                        "quiet_seconds": round(quiet_seconds, 3),
                    }
                )
                if len(observations) > 64:
                    del observations[:-64]
                if matches:
                    evidence[
                        "loader_error_detected_before_quiet_window"
                    ] = quiet_seconds < minimum_quiet_s
                    break
                if (
                    consecutive >= stable_samples
                    and quiet_seconds >= minimum_quiet_s
                ):
                    break
            else:
                previous_identity = None
                identity_since = None
                consecutive = 0
            if poll_interval_s:
                time.sleep(poll_interval_s)
        else:
            raise acceptance.RunnerError(
                "loader error.log did not appear and become quiescent"
            )
        if payload is None:
            raise acceptance.RunnerError(
                "loader error.log was unavailable after native readiness"
            )

        frozen.write_bytes(payload)
        evidence["full_log_size"] = len(payload)
        evidence["full_log_sha256"] = release.sha256_bytes(payload)
        evidence["project_attributed_line_count"] = sum(
            1
            for line in payload.decode("utf-8", errors="replace").splitlines()
            if any(token in line.lower() for token in PROJECT_TOKENS)
        )
        quiet_seconds = (
            max(0.0, time.monotonic() - identity_since)
            if identity_since is not None
            else 0.0
        )
        evidence["quiet_seconds_observed"] = round(quiet_seconds, 3)
        matches = _loader_error_matches(payload)
        counts: dict[str, int] = {}
        for match in matches:
            category = str(match["category"])
            counts[category] = counts.get(category, 0) + 1
        evidence["matches"] = matches
        evidence["counts_by_category"] = counts
        if matches:
            evidence["failure_reason"] = (
                f"{len(matches)} ZhongGuo-attributed loader error "
                "signature(s) found"
            )
            write_json(evidence_path, evidence)
            raise acceptance.RunnerError(str(evidence["failure_reason"]))
        evidence["result"] = "GREEN"
        evidence["failure_reason"] = None
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        if payload is not None and not frozen.exists():
            frozen.write_bytes(payload)
            evidence["full_log_size"] = len(payload)
            evidence["full_log_sha256"] = release.sha256_bytes(payload)
        evidence["result"] = "RED"
        if evidence.get("failure_reason") is None:
            evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"loader error.log scan failed: {error}"
        ) from error


def run_loader_gate(
    service: GameplayBridgeService,
    artifacts: Path,
    userdir: Path,
    bootstrap: dict[str, object],
    *,
    tracked_ck3_pid: int,
    phase2_live_batch: bool,
    managed_restore_supervisor: bool = False,
    phase2_promo_capture: bool = False,
    phase2_b2_same_checkpoint: bool = False,
) -> dict[str, object]:
    """Run the native/log/mount loader gate and persist every RED boundary."""

    managed_phase2 = (
        phase2_live_batch
        or phase2_promo_capture
        or phase2_b2_same_checkpoint
    )
    evidence_path = artifacts / "03_loader_gate.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "exact_build_loader_gate_before_gameplay",
        "mode": (
            "phase2_promo_capture"
            if phase2_promo_capture
            else (
                "phase2_b2_same_checkpoint"
                if phase2_b2_same_checkpoint
                else (
                    "phase2_live_batch"
                    if phase2_live_batch
                    else "loader_smoke_only"
                )
            )
        ),
        "tracked_ck3_pid": tracked_ck3_pid,
        "append_only_loader_stage": None,
        "native_readiness": None,
        "phase2_capability_preflight": None,
        "loader_error_log_scan": None,
        "runtime_mount_inventory": None,
        "same_pid_gameplay_continuation_authorized": False,
        "gameplay_acceptance_executed": False,
        "gameplay_green_claimed": False,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)

    try:
        if managed_phase2:
            try:
                loader_stage = wait_for_phase2_seed_loader_stage(
                    userdir / "logs",
                    artifacts / "01_phase2_loader_stage_progress.jsonl",
                    timeout_seconds=NATIVE_LOADER_READINESS_TIMEOUT_S,
                )
            except LoaderStageError as error:
                evidence["append_only_loader_stage"] = error.evidence
                write_json(evidence_path, evidence)
                state = error.evidence.get("state", "loader_stage_red")
                raise acceptance.RunnerError(f"{state}: {error}") from error
            evidence["append_only_loader_stage"] = loader_stage
            write_json(evidence_path, evidence)
            if loader_stage.get("result") != "GREEN":
                raise acceptance.RunnerError(
                    "phase-two append-only loader stage returned non-GREEN"
                )

        native_readiness = native_loader_smoke_readiness(
            service,
            artifacts,
            tracked_ck3_pid=tracked_ck3_pid,
        )
        evidence["native_readiness"] = native_readiness
        write_json(evidence_path, evidence)
        if native_readiness.get("result") != "GREEN":
            raise acceptance.RunnerError(
                "native loader readiness returned a non-GREEN result"
            )

        if managed_phase2:
            phase2_capabilities = phase2_runtime_capability_preflight(
                service,
                artifacts,
                tracked_ck3_pid=tracked_ck3_pid,
                managed_restore_supervisor=managed_restore_supervisor,
                focused_b2_same_checkpoint=phase2_b2_same_checkpoint,
            )
            evidence["phase2_capability_preflight"] = phase2_capabilities
            write_json(evidence_path, evidence)
            if phase2_capabilities.get("result") != "GREEN":
                raise acceptance.RunnerError(
                    "phase-two MCP capability preflight returned non-GREEN"
                )

        error_scan = scan_loader_error_log(userdir, artifacts)
        evidence["loader_error_log_scan"] = error_scan
        write_json(evidence_path, evidence)
        if error_scan.get("result") != "GREEN":
            raise acceptance.RunnerError(
                "loader error.log scan returned a non-GREEN result"
            )

        mount_order = verify_runtime_load_order(userdir, bootstrap)
        evidence["runtime_mount_inventory"] = mount_order
        evidence["result"] = "GREEN"
        evidence["same_pid_gameplay_continuation_authorized"] = (
            managed_phase2
        )
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["same_pid_gameplay_continuation_authorized"] = False
        evidence["failure_reason"] = (
            f"{type(error).__name__}: {error}"
        )
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"exact-build loader gate failed: {error}"
        ) from error


def initialize_fixture(stream: MarkerStream, artifacts: Path) -> None:
    confirm = isolated.open_decision_detail(
        "开始361制实机验收",
        "切换至宋帝并开考",
        artifacts,
        "05_fixture_initialize",
    )
    acceptance.click_until_text_disappears(
        confirm,
        "切换至宋帝并开考",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    for marker in REQUIRED_FIXTURE_MARKERS[:13]:
        stream.wait(marker, 30)
    isolated.wait_for_gameplay_hud(artifacts)
    acceptance.ensure_game_paused(artifacts, "05_song_emperor")


def native_title_navigation_readiness(
    service: GameplayBridgeService,
    *,
    tracked_ck3_pid: int,
    timeout_s: float = NATIVE_TITLE_READINESS_TIMEOUT_S,
) -> dict[str, object]:
    """Wait for one exact-build, paused, map-ready native bridge binding."""

    deadline = time.monotonic() + timeout_s
    last_error = "native bridge did not publish readiness"
    while time.monotonic() < deadline:
        try:
            capabilities = service.capabilities()
            snapshot = service.snapshot()
            diagnostics_value = capabilities.get("diagnostics")
            diagnostics = (
                diagnostics_value if isinstance(diagnostics_value, dict) else {}
            )
            snapshot_diagnostics_value = snapshot.get("diagnostics")
            snapshot_diagnostics = (
                snapshot_diagnostics_value
                if isinstance(snapshot_diagnostics_value, dict)
                else {}
            )
            hello_value = diagnostics.get("hello")
            hello = hello_value if isinstance(hello_value, dict) else {}
            connection_generation = diagnostics.get("connection_generation")
            capability = title_navigation_live._capability_proof(capabilities)
            binding = title_navigation_live._snapshot_binding(snapshot)
            checks = {
                "native_headless_mode": capabilities.get("mode")
                == NATIVE_BRIDGE_MODE,
                "native_headless_backend": capabilities.get("backend_id")
                == NATIVE_BRIDGE_MODE,
                "visual_fallback_disabled": capabilities.get("visual_fallback")
                is False,
                "transport_ready": capabilities.get("transport_ready") is True,
                "snapshot_available": capabilities.get("snapshot") is True,
                "connected": diagnostics.get("connected") is True,
                "semantic_state_available": diagnostics.get(
                    "semantic_state_available"
                )
                is True,
                "tracked_ck3_pid_matches_bridge": diagnostics.get("bridge_pid")
                == tracked_ck3_pid,
                "positive_connection_generation": isinstance(
                    connection_generation, int
                )
                and not isinstance(connection_generation, bool)
                and connection_generation > 0,
                "snapshot_transport_binding_matches": (
                    snapshot_diagnostics.get("bridge_pid")
                    == diagnostics.get("bridge_pid")
                    and snapshot_diagnostics.get("connection_generation")
                    == connection_generation
                ),
                "exact_game_version": hello.get("expected_ck3_version")
                == EXPECTED_GAME_VERSION,
                "exact_executable_sha256": str(
                    hello.get("expected_ck3_sha256", "")
                ).lower()
                == EXPECTED_EXE_SHA256,
                "exact_build_adapter_ready": hello.get("ck3_build_match") is True
                and hello.get("game_adapter_status") == "ready",
                "title_navigation_capability": capability.get("ok") is True,
                "paused": snapshot.get("paused") is True,
                "map_ready": snapshot.get("map_ready") is True,
                "played_character_present": isinstance(
                    snapshot.get("played_character"), dict
                ),
            }
            if all(checks.values()):
                return {
                    "checks": checks,
                    "ok": True,
                    "capability_proof": capability,
                    "binding": binding,
                    "snapshot": title_navigation_live._snapshot_evidence(snapshot),
                }
            last_error = ", ".join(
                key for key, value in checks.items() if not value
            )
        except Exception as error:
            last_error = f"{type(error).__name__}: {error}"
        time.sleep(0.1)
    raise acceptance.RunnerError(
        "native title-navigation readiness timed out: " + last_error
    )


def run_native_title_navigation_matrix(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    native_bridge: NativeBridgeLaunchConfig,
    preflight_bridge_identity: dict[str, object],
) -> dict[str, object]:
    """Run the shared typed title matrix before FFmpeg starts."""

    evidence_path = artifacts / "05_title_navigation_mcp_matrix.json"
    interaction_audit = title_navigation_live._interaction_audit()
    inhibit_report = title_navigation_live._inhibit_negative_report()
    partial: dict[str, object] = {}
    try:
        readiness = native_title_navigation_readiness(
            service, tracked_ck3_pid=tracked_ck3_pid
        )
        capabilities_before = service.capabilities()
        observed_bridge_identity = native_bridge_preflight_identity(native_bridge)
        exact_binary = title_navigation_live._exact_binary_proof(
            capabilities_before,
            managed_executable_sha256=isolated.sha256_file(acceptance.CK3_EXE),
            production_dll_sha256=str(
                observed_bridge_identity["dll_sha256"]
            ),
            expected_production_dll_sha256=str(
                preflight_bridge_identity["dll_sha256"]
            ),
            injector_sha256=str(
                observed_bridge_identity["injector_sha256"]
            ),
            expected_injector_sha256=str(
                preflight_bridge_identity["injector_sha256"]
            ),
        )
        bridge_identity_checks = {
            "mode_stable": observed_bridge_identity["mode"]
            == preflight_bridge_identity.get("mode")
            == NATIVE_BRIDGE_MODE,
            "pipe_stable": observed_bridge_identity["pipe_name"]
            == preflight_bridge_identity.get("pipe_name")
            == native_bridge.pipe_name,
            "dll_path_stable": observed_bridge_identity["dll_path"]
            == preflight_bridge_identity.get("dll_path"),
            "dll_hash_stable": observed_bridge_identity["dll_sha256"]
            == preflight_bridge_identity.get("dll_sha256"),
            "injector_path_stable": observed_bridge_identity["injector_path"]
            == preflight_bridge_identity.get("injector_path"),
            "injector_hash_stable": observed_bridge_identity["injector_sha256"]
            == preflight_bridge_identity.get("injector_sha256"),
            "visual_fallback_disabled": observed_bridge_identity[
                "visual_fallback"
            ]
            is False,
        }
        if not all(bridge_identity_checks.values()):
            raise acceptance.RunnerError(
                "native bridge DLL/injector/pipe identity drifted after preflight"
            )
        if exact_binary.get("ok") is not True:
            raise acceptance.RunnerError(
                "exact EXE/DLL/injector proof failed before title navigation"
            )

        sequence = title_navigation_live._run_navigation_sequence(service)
        partial["shared_sequence"] = sequence
        if sequence.get("ok") is not True:
            raise acceptance.RunnerError(
                "shared native title-navigation matrix returned RED"
            )
        session_binding = sequence.get("session_binding")
        if not isinstance(session_binding, dict):
            raise acceptance.RunnerError(
                "shared title-navigation matrix omitted its full binding"
            )
        unknown_step = sequence.get("unknown_step")
        if not isinstance(unknown_step, dict):
            raise acceptance.RunnerError(
                "shared title-navigation matrix omitted its typed unknown-title step"
            )
        integrity_probe = unknown_step.get("integrity_probe")
        if not isinstance(integrity_probe, dict):
            raise acceptance.RunnerError(
                "shared title-navigation matrix omitted its integrity probe"
            )
        stable_camera = (
            integrity_probe.get("camera_transition", {}).get("after")
            if isinstance(integrity_probe.get("camera_transition"), dict)
            else None
        )
        if not isinstance(stable_camera, dict):
            raise acceptance.RunnerError(
                "post-unknown integrity probe omitted typed camera state"
            )

        final_bianzhou = title_navigation_live._known_call(
            service,
            label="final_bianzhou_before_ffmpeg",
            title_key=title_navigation_live.COUNTY_TITLE_KEY,
            session_binding=session_binding,
            allowed_statuses={"centered", "already_centered"},
            camera_before=stable_camera,
            camera_before_source=(
                "shared_sequence.unknown_step.integrity_probe."
                "camera_transition.after"
            ),
        )
        partial["final_bianzhou"] = final_bianzhou
        if final_bianzhou.get("ok") is not True:
            raise acceptance.RunnerError(
                "final c_bianzhou native camera postcondition returned RED"
            )

        capabilities_after = service.capabilities()
        same_process = title_navigation_live._same_process_proof(
            capabilities_before, capabilities_after
        )
        same_process_checks = dict(same_process.get("checks", {}))
        same_process_checks["bridge_pid_matches_full_acceptance_pid"] = (
            same_process.get("bridge_pid") == tracked_ck3_pid
        )
        same_process["checks"] = same_process_checks
        same_process["ok"] = all(same_process_checks.values())

        known_results = [
            row
            for row in sequence.get("known_steps", [])
            if isinstance(row, dict)
        ]
        known_results.append(integrity_probe)
        known_results.append(final_bianzhou)
        camera_write_states = [
            row.get("typed_service_payload", {})
            .get("camera_center", {})
            .get("target_write_blocked")
            for row in known_results
        ]
        typed_payload_hashes = [
            row.get("typed_service_payload_sha256") for row in known_results
        ]
        typed_error_hash = unknown_step.get("typed_error_sha256")
        checks = {
            "readiness": readiness.get("ok") is True,
            "exact_binary": exact_binary.get("ok") is True,
            "bridge_identity_stable": all(bridge_identity_checks.values()),
            "shared_matrix": sequence.get("ok") is True,
            "final_bianzhou": final_bianzhou.get("ok") is True
            and final_bianzhou.get("title_key")
            == title_navigation_live.COUNTY_TITLE_KEY,
            "same_tracked_process": same_process.get("ok") is True,
            "all_successful_target_writes_unblocked": bool(camera_write_states)
            and all(value is False for value in camera_write_states),
            "all_successful_payload_hashes_present": bool(typed_payload_hashes)
            and all(isinstance(value, str) for value in typed_payload_hashes),
            "typed_unknown_error_hash_present": isinstance(
                typed_error_hash, str
            ),
            "zero_visual_or_input_fallback": interaction_audit.get("all_zero")
            is True
            and interaction_audit.get("fallbacks_enabled") is False,
            "inhibit_positive_explicitly_skipped": (
                inhibit_report.get("status") == "skipped"
                and inhibit_report.get("executed") is False
                and inhibit_report.get("live_claim") is False
                and inhibit_report.get("process_memory_modified") is False
            ),
            "ffmpeg_not_started": True,
        }
        evidence: dict[str, object] = {
            "schema_version": 1,
            "result": "GREEN" if all(checks.values()) else "RED",
            "navigation_path_status": "native_mcp_fixture_live",
            "mcp_tool": "ck3_center_map_on_landed_title_v1",
            "mcp_capability_implemented": True,
            "formal_mcp_contract": (
                "docs/ck3-native-title-map-navigation-contract.md"
            ),
            "tracked_full_acceptance_pid": tracked_ck3_pid,
            "native_bridge_runtime": observed_bridge_identity,
            "readiness": readiness,
            "exact_binary_proof": exact_binary,
            "bridge_identity_checks": bridge_identity_checks,
            "shared_sequence": sequence,
            "final_bianzhou": final_bianzhou,
            "same_process_proof": same_process,
            "capabilities_before": capabilities_before,
            "capabilities_after": capabilities_after,
            "successful_typed_payload_hashes": typed_payload_hashes,
            "typed_unknown_error_hash": typed_error_hash,
            "successful_target_write_blocked_values": camera_write_states,
            "successful_typed_call_count": len(known_results),
            "interaction_audit": interaction_audit,
            "inhibit_positive": inhibit_report,
            "ffmpeg_started": False,
            "hkl_scope": "other_existing_gui_operations_only",
            "checks": checks,
        }
        evidence["typed_matrix_payload_sha256"] = (
            title_navigation_live._canonical_json_sha256(evidence)
        )
        write_json(evidence_path, evidence)
        if evidence["result"] != "GREEN":
            raise acceptance.RunnerError(
                "native MCP title-navigation evidence gate returned RED"
            )
        return evidence
    except BaseException as error:
        failed: dict[str, object] = {
            "schema_version": 1,
            "result": "RED",
            "error": f"{type(error).__name__}: {error}",
            "navigation_path_status": "native_mcp_fixture_live",
            "mcp_tool": "ck3_center_map_on_landed_title_v1",
            "mcp_capability_implemented": True,
            "tracked_full_acceptance_pid": tracked_ck3_pid,
            "native_bridge_runtime": preflight_bridge_identity,
            "partial": partial,
            "interaction_audit": interaction_audit,
            "inhibit_positive": inhibit_report,
            "ffmpeg_started": False,
        }
        failed["typed_matrix_payload_sha256"] = (
            title_navigation_live._canonical_json_sha256(failed)
        )
        write_json(evidence_path, failed)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"native MCP title-navigation matrix failed: {error}"
        ) from error


def choose_direct_publication(
    stream: MarkerStream, artifacts: Path, recorder: PromoRecorder | None = None
) -> None:
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "决议", (0.52, 0.00, 0.99, 0.30), contains=True
    ) is not None:
        image.save(artifacts / "06_decisions_drawer_before_calibration.png")
        acceptance.pyautogui.press("escape")
        time.sleep(0.8)
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_calibration", require_progress=True
    )
    log("advanced the live date for the one-day production calibration event")
    settle_promo_interruptions(
        artifacts,
        "06_calibration_preemption",
        observation_s=20.0,
        stop_event_title="绩效校准会议",
    )
    acceptance.wait_for_ocr_text(
        "绩效校准会议",
        PROMO_EVENT_TITLE_REGION,
        60,
        artifacts,
        "06_calibration_event.png",
        contains=True,
        stable_hits=1,
    )
    if recorder:
        recorder.mark("calibration_event_visible")
        recorder.clean_hold("calibration", artifacts)
    option = acceptance.wait_for_ocr_text(
        "名单无误",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "06_calibration_direct_publication.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(option, "production calibration direct publication")
    stream.wait("ZG361: scoreboard published", 30)
    stream.wait("ZGA: TEST PASS scoreboard_header_and_rows", 30)
    stream.wait("ZGA: TEST PASS three_grade_counts", 30)
    stream.wait("ZGA: TEST DONE zg361", 30)
    stream.validate()


def close_native_decisions_panel(artifacts: Path, stem: str) -> str:
    """Close the native drawer and prove it is gone before seeking our HUD button."""

    width, height = acceptance.pyautogui.size()

    def park_pointer_away_from_right_rail() -> None:
        # The title-bar X becomes ordinary map terrain as soon as the drawer
        # closes.  Leaving the pointer there raises a terrain tooltip over the
        # adjacent performance-board toggle and can hide its OCR label.
        acceptance.pyautogui.moveTo(
            int(width * 0.50), int(height * 0.50), duration=0.2
        )
        time.sleep(0.5)

    def wait_until_closed(
        timeout_s: float, success_artifact: str, failure_artifact: str
    ) -> bool:
        deadline = time.monotonic() + timeout_s
        absent_hits = 0
        last_image = None
        while time.monotonic() < deadline:
            acceptance.focus_ck3()
            last_image = acceptance.ImageGrab.grab()
            visible = acceptance.find_ocr_text(
                last_image, "决议", DECISIONS_HEADER_REGION, contains=True
            )
            absent_hits = absent_hits + 1 if visible is None else 0
            if absent_hits >= 2:
                last_image.save(artifacts / success_artifact)
                return True
            time.sleep(acceptance.POLL_INTERVAL_S)
        if last_image is not None:
            last_image.save(artifacts / failure_artifact)
        return False

    acceptance.focus_ck3()
    # An open decision-row tooltip can consume the first Escape while leaving
    # the right drawer untouched. Move away before exercising that close path.
    park_pointer_away_from_right_rail()
    acceptance.pyautogui.press("escape")
    if wait_until_closed(
        2.5,
        f"{stem}_closed_by_escape.png",
        f"{stem}_escape_left_drawer_open.png",
    ):
        park_pointer_away_from_right_rail()
        return "escape"

    close_point = (
        int(width * DECISIONS_CLOSE_BUTTON[0]),
        int(height * DECISIONS_CLOSE_BUTTON[1]),
    )
    acceptance.deliberate_click(close_point, "native Decisions title-bar close button")
    if wait_until_closed(
        5.0,
        f"{stem}_closed_by_title_button.png",
        f"red_{stem}_drawer_still_open.png",
    ):
        park_pointer_away_from_right_rail()
        return "title_bar_close"
    raise acceptance.RunnerError(
        "native Decisions drawer remained open after Escape and its title-bar close button"
    )


def wait_for_scoreboard_closed_with_toggle(
    artifacts: Path, stem: str, timeout_s: float = 8.0
) -> tuple[int, int]:
    """Prove the modal closed and its safe-lane HUD toggle became clickable again."""

    deadline = time.monotonic() + timeout_s
    stable_hits = 0
    last_image = None
    last_button = None
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        last_image = acceptance.ImageGrab.grab()
        title = acceptance.find_ocr_text(
            last_image,
            "天朝官员考核榜",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        )
        last_button = acceptance.find_ocr_text(
            last_image,
            "考核榜",
            SCOREBOARD_BUTTON_REGION,
            contains=True,
        )
        stable_hits = stable_hits + 1 if title is None and last_button else 0
        if stable_hits >= 2:
            last_image.save(artifacts / f"{stem}_closed.png")
            return last_button
        time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / f"timeout_{stem}_close.png")
    raise acceptance.RunnerError(
        f"{stem} did not close the scoreboard and restore its safe-lane toggle"
    )


def reopen_managed_scoreboard_for_audit(
    artifacts: Path, stem: str, button: tuple[int, int]
) -> None:
    """Reopen the board after one close probe and prove managed content returned."""

    acceptance.deliberate_click(button, f"reopen performance board after {stem}")
    acceptance.wait_for_ocr_text(
        "天朝官员考核榜",
        acceptance.FULL_SCREEN_REGION,
        12,
        artifacts,
        f"{stem}_title.png",
        contains=True,
        stable_hits=2,
    )
    acceptance.wait_for_ocr_tokens(
        ("所辖官员", "官员 / 官职", "点击任一官员"),
        ("zg361_scoreboard", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        stem,
    )


def select_representative_scoreboard_row(
    items: list[dict[str, object]], width: int, height: int
) -> tuple[dict[str, object], str] | None:
    """Select one visible real-character row, never a header or event option."""

    left, top, right, bottom = SCOREBOARD_ROW_NAME_REGION
    candidates: list[tuple[int, dict[str, object], str]] = []
    for item in items:
        text = re.sub(r"\s+", "", str(item.get("text", "")))
        center = item.get("center")
        bbox = item.get("bbox")
        if not isinstance(center, (list, tuple)) or len(center) != 2:
            continue
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        x_ratio = float(center[0]) / width
        y_ratio = float(center[1]) / height
        if not (left <= x_ratio <= right and top <= y_ratio <= bottom):
            continue
        if (float(bbox[2]) - float(bbox[0])) / width < 0.06:
            continue
        parts = re.split(r"[，,、]", text)
        if len(parts) < 2:
            continue
        personal_name = "".join(re.findall(r"[\u3400-\u9fff]", parts[-1]))
        if len(personal_name) < 2:
            continue
        candidates.append((int(center[1]), item, personal_name))
    if not candidates:
        return None
    _, item, personal_name = min(candidates, key=lambda candidate: candidate[0])
    return item, personal_name


def wait_for_representative_character_view(
    artifacts: Path,
    stem: str,
    source_row: dict[str, object],
    name_probe: str,
    timeout_s: float = 12.0,
) -> tuple[int, int]:
    """Prove a row click closed the board and opened that character's native view."""

    deadline = time.monotonic() + timeout_s
    stable_hits = 0
    last_image = None
    last_name = None
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        last_image = acceptance.ImageGrab.grab()
        board_title = acceptance.find_ocr_text(
            last_image,
            "天朝官员考核榜",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        )
        last_name = acceptance.find_ocr_text(
            last_image,
            name_probe,
            CHARACTER_WINDOW_NAME_REGION,
            contains=True,
        )
        stable_hits = stable_hits + 1 if board_title is None and last_name else 0
        if stable_hits >= 2:
            last_image.save(artifacts / f"{stem}_character_open.png")
            write_json(
                artifacts / f"{stem}_character_open.json",
                {
                    "schema_version": 1,
                    "source_row_text": source_row["text"],
                    "source_row_center": source_row["center"],
                    "verification_name_probe": name_probe,
                    "character_name_center": list(last_name),
                    "scoreboard_closed": True,
                    "native_character_view_open": True,
                },
            )
            return last_name
        time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / f"timeout_{stem}_character_open.png")
    raise acceptance.RunnerError(
        "representative scoreboard row did not close the board and open its character"
    )


def close_representative_character_view(
    artifacts: Path, stem: str, name_probe: str
) -> dict[str, object]:
    """Restore a clean map through the native character title-bar close control."""

    width, height = acceptance.pyautogui.size()
    close_point = (
        int(width * CHARACTER_WINDOW_CLOSE_BUTTON[0]),
        int(height * CHARACTER_WINDOW_CLOSE_BUTTON[1]),
    )
    for attempt in range(1, 3):
        acceptance.focus_ck3()
        acceptance.deliberate_click(
            close_point, "native character title-bar close button"
        )
        deadline = time.monotonic() + 3.0
        absent_hits = 0
        last_image = None
        while time.monotonic() < deadline:
            last_image = acceptance.ImageGrab.grab()
            visible = acceptance.find_ocr_text(
                last_image,
                name_probe,
                CHARACTER_WINDOW_NAME_REGION,
                contains=True,
            )
            absent_hits = absent_hits + 1 if visible is None else 0
            if absent_hits >= 2:
                last_image.save(artifacts / f"{stem}_character_closed.png")
                return {
                    "method": "title_bar_close",
                    "attempts": attempt,
                    "point_px": list(close_point),
                    "point_normalized": list(CHARACTER_WINDOW_CLOSE_BUTTON),
                }
            time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / f"red_{stem}_character_still_open.png")
    raise acceptance.RunnerError(
        "representative row opened a character view that could not be closed"
    )


def audit_scoreboard_controls(artifacts: Path) -> dict[str, object]:
    """Live-click representative custom controls without claiming 160 row clicks."""

    # A queued product event can cover the modal even while its title and tabs
    # remain OCR-visible underneath.  The recovery classifier is deliberately
    # conservative and leaves a clean board untouched.
    settle_promo_interruptions(
        artifacts, "08_gui_audit_preflight", observation_s=1.0
    )
    acceptance.wait_for_ocr_tokens(
        ("天朝官员考核榜", "所辖官员", "点击任一官员"),
        ("zg361_scoreboard", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "08_gui_audit_ready",
    )
    width, height = acceptance.pyautogui.size()

    title_close_point = (
        int(width * SCOREBOARD_TITLE_CLOSE_BUTTON[0]),
        int(height * SCOREBOARD_TITLE_CLOSE_BUTTON[1]),
    )
    acceptance.deliberate_click(
        title_close_point, "performance-board title-bar close button"
    )
    title_toggle = wait_for_scoreboard_closed_with_toggle(
        artifacts, "08_gui_audit_title_button"
    )
    reopen_managed_scoreboard_for_audit(
        artifacts, "08_gui_audit_title_button_reopen", title_toggle
    )

    backdrop_point = (
        int(width * SCOREBOARD_BACKDROP_POINT[0]),
        int(height * SCOREBOARD_BACKDROP_POINT[1]),
    )
    acceptance.deliberate_click(backdrop_point, "performance-board modal backdrop")
    backdrop_toggle = wait_for_scoreboard_closed_with_toggle(
        artifacts, "08_gui_audit_backdrop"
    )
    reopen_managed_scoreboard_for_audit(
        artifacts, "08_gui_audit_backdrop_reopen", backdrop_toggle
    )

    row_items = acceptance.capture_ocr_bundle(
        artifacts, "08_gui_audit_row_source", acceptance.FULL_SCREEN_REGION
    )
    selected = select_representative_scoreboard_row(row_items, width, height)
    if selected is None:
        raise acceptance.RunnerError(
            "no visible real-character scoreboard row satisfied the representative audit"
        )
    source_row, personal_name = selected
    # Use the final two CJK characters as the cross-font OCR probe.  The row
    # and native character header render the same UI name at different sizes;
    # the leading glyph is the one most often recognized differently.
    name_probe = personal_name[-2:]
    row_center = tuple(int(value) for value in source_row["center"])
    acceptance.deliberate_click(
        row_center, f"representative generated scoreboard row: {source_row['text']!r}"
    )
    character_name_center = wait_for_representative_character_view(
        artifacts,
        "08_gui_audit_row_link",
        source_row,
        name_probe,
    )
    cleanup = close_representative_character_view(
        artifacts, "08_gui_audit_row_link", name_probe
    )
    row_reopen_button = acceptance.wait_for_ocr_text(
        "考核榜",
        SCOREBOARD_BUTTON_REGION,
        10,
        artifacts,
        "08_gui_audit_row_link_toggle_restored.png",
        contains=True,
        stable_hits=2,
    )
    reopen_managed_scoreboard_for_audit(
        artifacts, "08_gui_audit_row_link_reopen", row_reopen_button
    )

    return {
        "scope": "representative_generated_controls",
        "title_bar_close": {
            "clicked": True,
            "scoreboard_closed": True,
            "scoreboard_reopened": True,
            "point_px": list(title_close_point),
            "point_normalized": list(SCOREBOARD_TITLE_CLOSE_BUTTON),
            "closed_artifact": "08_gui_audit_title_button_closed.png",
            "reopened_artifact": "08_gui_audit_title_button_reopen.png",
        },
        "modal_backdrop": {
            "clicked": True,
            "scoreboard_closed": True,
            "scoreboard_reopened": True,
            "point_px": list(backdrop_point),
            "point_normalized": list(SCOREBOARD_BACKDROP_POINT),
            "closed_artifact": "08_gui_audit_backdrop_closed.png",
            "reopened_artifact": "08_gui_audit_backdrop_reopen.png",
        },
        "row_link": {
            "clicked": True,
            "scoreboard_closed": True,
            "native_character_view_opened": True,
            "scoreboard_reopened_after_character_cleanup": True,
            "source_text": source_row["text"],
            "source_center_px": list(row_center),
            "source_personal_name_ocr": personal_name,
            "verification_name_probe": name_probe,
            "character_name_center_px": list(character_name_center),
            "artifact": "08_gui_audit_row_link_character_open.png",
            "reopened_artifact": "08_gui_audit_row_link_reopen.png",
            "cleanup": cleanup,
        },
        "row_link_coverage": {
            "generated_total": SCOREBOARD_GENERATED_ROW_LINKS,
            "live_clicked": 1,
            "not_individually_clicked": SCOREBOARD_GENERATED_ROW_LINKS - 1,
            "claim": "one representative click over a shared generated row structure",
        },
    }


def capture_scoreboard_gui(
    artifacts: Path, recorder: PromoRecorder | None = None
) -> dict[str, object]:
    # Settlement schedules the summary one game-day after calibration. Dismiss it
    # before opening the board so a late event cannot cover the GUI evidence.
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    result_title = acceptance.find_ocr_text(
        image, "你主持的考核", PROMO_EVENT_TITLE_REGION, contains=True
    )
    if result_title is None:
        acceptance.set_speed_five_and_unpause(
            artifacts, "zg361_result_summary", require_progress=False
        )
        settle_promo_interruptions(
            artifacts,
            "07_result_summary_preemption",
            observation_s=30.0,
            stop_event_title="你主持的考核",
        )
    acceptance.wait_for_ocr_text(
        "你主持的考核",
        PROMO_EVENT_TITLE_REGION,
        15,
        artifacts,
        "07_result_summary.png",
        contains=True,
        stable_hits=1,
    )
    result_option = acceptance.wait_for_ocr_text(
        "知道了",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "07_result_summary_option.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(result_option, "production review result summary")
    # The summary interrupted a speed-five timeline. Stop that restored clock
    # before the Decisions drawer and scoreboard audit spend wall time on OCR;
    # otherwise the already-scheduled Jingcha mandate can cover the cockpit.
    acceptance.pyautogui.press("space")
    ensure_hud_date_frozen(artifacts, "07_result_summary_closed")
    result_close_interruptions = settle_promo_interruptions(
        artifacts, "07_result_summary_closed_preemption", observation_s=0.5
    )

    # Deliberately hold the native Decisions drawer open and prove that the
    # additive HUD toggle is suppressed.  The old layout rendered the 180x44
    # button on top of this drawer, hiding decision content and stealing input.
    isolated.ensure_decisions_panel(artifacts, "07_scoreboard_overlay_gate")
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "决议", DECISIONS_HEADER_REGION, contains=True
    ) is None:
        image.save(artifacts / "timeout_07_scoreboard_right_panel_gate.png")
        raise acceptance.RunnerError(
            "native Decisions drawer was not open for scoreboard overlay gate"
        )
    if acceptance.find_ocr_text(
        image, "考核榜", acceptance.FULL_SCREEN_REGION, contains=False
    ) is not None:
        image.save(artifacts / "red_07_scoreboard_overlays_right_panel.png")
        raise acceptance.RunnerError(
            "performance-board HUD toggle overlaps a native right-side panel"
        )
    image.save(artifacts / "07_scoreboard_hidden_by_right_panel.png")
    right_panel_close_method = close_native_decisions_panel(
        artifacts, "07_scoreboard_right_panel"
    )
    button = acceptance.wait_for_ocr_text(
        "考核榜",
        SCOREBOARD_BUTTON_REGION,
        20,
        artifacts,
        "07_scoreboard_button.png",
        contains=True,
        stable_hits=1,
    )
    screen_width, screen_height = acceptance.pyautogui.size()
    button_center_normalized = [
        round(button[0] / screen_width, 4),
        round(button[1] / screen_height, 4),
    ]
    acceptance.deliberate_click(button, "production performance-board button")
    acceptance.wait_for_ocr_text(
        "天朝官员考核榜",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "08_scoreboard_title.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.ImageGrab.grab().save(artifacts / "08_scoreboard_panel_raw.png")
    rendered_text = acceptance.wait_for_ocr_tokens(
        (
            "天朝官员考核榜",
            "所辖官员",
            "制度驾驶舱",
            "点击任一官员",
        ),
        ("zg361_scoreboard", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "08_scoreboard_panel",
    )
    cockpit_artifact = None
    if recorder:
        recorder.mark("managed_scoreboard_visible")
        recorder.clean_hold("managed_scoreboard", artifacts)
        cockpit = acceptance.wait_for_ocr_text(
            "制度驾驶舱",
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            "08_scoreboard_cockpit_tab.png",
            stable_hits=1,
        )
        acceptance.deliberate_click(cockpit, "production policy-cockpit tab")
        # The 361 reference batch can schedule ordinary product events on the
        # next game day. One may surface over the board between the tab click
        # and OCR (for example "野狗与小白兔"). First prove the clean cockpit;
        # only if that fails do we invoke the conservative event recovery and
        # retry. This prevents cockpit prose from being mistaken for an event.
        cockpit_tokens = ("361 制度账本", "证据质量", "组织信任", "预算压力")
        try:
            acceptance.wait_for_ocr_tokens(
                cockpit_tokens,
                ("zg361_", "localize", "error"),
                acceptance.FULL_SCREEN_REGION,
                6,
                artifacts,
                "08_scoreboard_cockpit",
            )
            cockpit_artifact = "08_scoreboard_cockpit.png"
        except acceptance.RunnerError:
            settle_promo_interruptions(
                artifacts,
                "08_scoreboard_cockpit_recovery",
                observation_s=1.5,
            )
            acceptance.wait_for_ocr_tokens(
                cockpit_tokens,
                ("zg361_", "localize", "error"),
                acceptance.FULL_SCREEN_REGION,
                20,
                artifacts,
                "08_scoreboard_cockpit_recovered",
            )
            cockpit_artifact = "08_scoreboard_cockpit_recovered.png"
        recorder.mark("policy_cockpit_visible")
        recorder.clean_hold("policy_cockpit", artifacts, 3.0)
        managed = acceptance.wait_for_ocr_text(
            "所辖官员",
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            "08_scoreboard_managed_tab_return.png",
            stable_hits=1,
        )
        acceptance.deliberate_click(managed, "return to managed scoreboard tab")
        recorder.hold(1.0)
    representative_control_audit = audit_scoreboard_controls(artifacts)
    if recorder:
        recorder.mark("representative_scoreboard_controls_audited")
    return {
        "button_ocr": True,
        "right_panel_suppression_ocr": True,
        "managed_panel_ocr": True,
        "right_panel_suppression_artifact": "07_scoreboard_hidden_by_right_panel.png",
        "right_panel_close_method": right_panel_close_method,
        "button_artifact": "07_scoreboard_button.png",
        "button_center_px": list(button),
        "button_center_normalized": button_center_normalized,
        "button_expected_region": list(SCOREBOARD_BUTTON_REGION),
        "panel_artifact": "08_scoreboard_panel.png",
        "panel_ocr_artifact": "08_scoreboard_panel_ocr.json",
        "normalized_ocr": rendered_text,
        "cockpit_artifact": cockpit_artifact,
        "post_result_interruptions_dismissed": result_close_interruptions,
        "representative_control_audit": representative_control_audit,
    }


def close_scoreboard_panel(artifacts: Path, stem: str) -> None:
    acceptance.focus_ck3()
    acceptance.pyautogui.press("escape")
    time.sleep(0.8)
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "天朝官员考核榜", acceptance.FULL_SCREEN_REGION, contains=True
    ) is None:
        return
    image.save(artifacts / f"{stem}_scoreboard_after_escape.png")
    width, height = acceptance.pyautogui.size()
    acceptance.deliberate_click(
        (int(width * 0.05), int(height * 0.50)),
        "scoreboard modal backdrop close",
    )
    deadline = time.time() + 6
    while time.time() < deadline:
        image = acceptance.ImageGrab.grab()
        if acceptance.find_ocr_text(
            image,
            "天朝官员考核榜",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        ) is None:
            image.save(artifacts / f"{stem}_scoreboard_closed.png")
            return
        time.sleep(acceptance.POLL_INTERVAL_S)
    raise acceptance.RunnerError("scoreboard modal did not close")


def ensure_hud_date_frozen(
    artifacts: Path,
    stem: str,
    *,
    probe_interval_s: float = 0.8,
) -> dict[str, object]:
    """Prove a pause from the HUD date when modal UI hides the pause label."""

    acceptance.focus_ck3()

    def probe(label: str) -> tuple[bool, list[int], object]:
        observations: list[int] = []
        last_image = None
        for index in range(4):
            last_image = acceptance.ImageGrab.grab()
            date = acceptance.read_hud_game_date(last_image)
            if date is None:
                last_image.save(artifacts / f"{stem}_{label}_date_unreadable.png")
                raise acceptance.RunnerError(
                    f"HUD date became unreadable during pause proof: {stem}"
                )
            observations.append(date[0])
            if index < 3:
                time.sleep(probe_interval_s)
        return len(set(observations[-3:])) == 1, observations, last_image

    frozen, observations, last_image = probe("initial")
    pause_method = "already_frozen"
    if not frozen:
        width, height = acceptance.pyautogui.size()
        acceptance.deliberate_click(
            (
                int(width * (2315 / 2560)),
                int(height * (1410 / 1440)),
            ),
            f"timeline pause by HUD date ({stem})",
        )
        frozen, click_observations, last_image = probe("timeline_click")
        observations.extend(click_observations)
        pause_method = "timeline_click"
    evidence = {
        "schema_version": 1,
        "result": "GREEN" if frozen else "RED",
        "pause_method": pause_method,
        "date_observations": observations,
        "last_three_dates_identical": frozen,
        "paused_day_ordinal": observations[-1],
    }
    write_json(artifacts / f"{stem}_date_freeze_gate.json", evidence)
    if not frozen:
        last_image.save(artifacts / f"red_{stem}_date_not_frozen.png")
        raise acceptance.RunnerError(
            f"HUD date did not freeze after pause attempts ({stem}): {observations}"
        )
    last_image.save(artifacts / f"{stem}_date_frozen.png")
    return evidence


def pause_after_jingcha_host_click(
    service: GameplayBridgeService,
    stream: MarkerStream,
    artifacts: Path,
    mandate_day: int,
    pre_click_snapshot: dict[str, object],
) -> dict[str, object]:
    """Use the already-connected native MCP to stop the restored game clock."""

    def event_instance_id(snapshot: dict[str, object]) -> int | None:
        active_event = snapshot.get("active_event")
        instance_id = (
            active_event.get("instance_id")
            if isinstance(active_event, dict)
            else None
        )
        return (
            instance_id
            if isinstance(instance_id, int) and not isinstance(instance_id, bool)
            else None
        )

    def played_character(snapshot: dict[str, object]) -> tuple[int | None, bool | None]:
        character = snapshot.get("played_character")
        if not isinstance(character, dict):
            return None, None
        character_id = character.get("character_id")
        return (
            character_id
            if isinstance(character_id, int) and not isinstance(character_id, bool)
            else None,
            character.get("alive") if isinstance(character.get("alive"), bool) else None,
        )

    pre_event_id = event_instance_id(pre_click_snapshot)
    pre_character_id, pre_character_alive = played_character(pre_click_snapshot)
    transition_observations: list[dict[str, object]] = []
    transition_deadline = time.monotonic() + 2.0
    while True:
        snapshot = service.snapshot()
        transition_observations.append(
            {
                "revision": snapshot.get("revision"),
                "native_revision": snapshot.get("native_revision"),
                "date_raw": snapshot.get("date_raw"),
                "paused": snapshot.get("paused"),
                "active_event_instance_id": event_instance_id(snapshot),
            }
        )
        if (
            snapshot.get("paused") is False
            or event_instance_id(snapshot) != pre_event_id
            or time.monotonic() >= transition_deadline
        ):
            break
        time.sleep(0.05)

    pause_submission = service.execute_step("pause-map")
    pause_observations: list[dict[str, object]] = []
    pause_deadline = time.monotonic() + 5.0
    frozen = False
    paused_snapshot: dict[str, object] = {}
    while time.monotonic() < pause_deadline:
        paused_snapshot = service.snapshot()
        character_id, character_alive = played_character(paused_snapshot)
        pause_observations.append(
            {
                "revision": paused_snapshot.get("revision"),
                "native_revision": paused_snapshot.get("native_revision"),
                "date_raw": paused_snapshot.get("date_raw"),
                "paused": paused_snapshot.get("paused"),
                "played_character_id": character_id,
                "played_character_alive": character_alive,
            }
        )
        tail = pause_observations[-3:]
        frozen = (
            len(tail) == 3
            and all(item["paused"] is True for item in tail)
            and len({item["date_raw"] for item in tail}) == 1
        )
        if frozen:
            break
        time.sleep(0.1)

    paused_image = acceptance.ImageGrab.grab()
    post_character_id, post_character_alive = played_character(paused_snapshot)
    played_character_stable = (
        pre_character_alive is True
        and post_character_alive is True
        and pre_character_id is not None
        and post_character_id == pre_character_id
    )
    if not frozen or not played_character_stable:
        paused_image.save(artifacts / "red_09_jingcha_host_native_pause.png")
        evidence = {
            "schema_version": 2,
            "result": "RED",
            "pause_method": "native_mcp_pause_map",
            "native_transition_observations": transition_observations,
            "native_pause_submission": pause_submission,
            "native_pause_observations": pause_observations,
            "last_three_dates_identical": frozen,
            "played_character_stable": played_character_stable,
        }
        write_json(artifacts / "09_jingcha_host_immediate_pause_gate.json", evidence)
        raise acceptance.RunnerError(
            "native MCP did not freeze Jingcha safely on the same living player"
        )

    paused_date = acceptance.read_hud_game_date(paused_image)
    if paused_date is None:
        paused_image.save(artifacts / "09_jingcha_host_native_date_unreadable.png")
        raise acceptance.RunnerError(
            "Jingcha host HUD date is unreadable after native MCP pause"
        )
    paused_image.save(artifacts / "09_jingcha_host_immediate_pause_verified.png")
    paused_day = paused_date[0]
    due_day = mandate_day + JINGCHA_PERSONAL_SWITCH_DELAY_DAYS
    pause_delta_days = paused_day - mandate_day
    stream.pump()
    personal_switch_marker_count = stream.count(PERSONAL_SWITCH_SCHEDULED_MARKER)
    evidence = {
        "schema_version": 2,
        "result": "GREEN",
        "mandate_day_ordinal": mandate_day,
        "personal_switch_due_day_ordinal": due_day,
        "paused_day_ordinal": paused_day,
        "pause_delta_days": pause_delta_days,
        "paused_within_two_days": 0 <= pause_delta_days <= 2,
        "pause_completed_before_personal_switch_due": paused_day < due_day,
        "pause_method": "native_mcp_pause_map",
        "date_observations": [paused_day],
        "native_transition_observations": transition_observations,
        "native_pause_submission": pause_submission,
        "native_pause_observations": pause_observations,
        "last_three_dates_identical": frozen,
        "played_character_stable": played_character_stable,
        "date_before_due": paused_day < due_day,
        "personal_switch_marker_count": personal_switch_marker_count,
    }
    if (
        personal_switch_marker_count != 0
        or paused_day >= due_day
    ):
        evidence["result"] = "RED"
    write_json(artifacts / "09_jingcha_host_immediate_pause_gate.json", evidence)
    if personal_switch_marker_count != 0:
        raise acceptance.RunnerError(
            "personal-result switch raced the immediate Jingcha host pause"
        )
    if paused_day >= due_day:
        raise acceptance.RunnerError(
            "Jingcha host pause reached or crossed the delayed personal-switch due date: "
            f"paused={paused_day}, due={due_day}"
        )
    return evidence


def advance_to_jingcha_mandate(
    stream: MarkerStream,
    artifacts: Path,
    timeout_s: float = 60.0,
) -> list[dict[str, object]]:
    """Advance the delayed mandate while safely clearing earlier product events."""

    marker = "ZGA: TEST PASS jingcha_mandate_issued"
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_clean_jingcha_dispatch", require_progress=True
    )
    deadline = time.monotonic() + timeout_s
    interruptions: list[dict[str, object]] = []
    recovery_round = 0
    while time.monotonic() < deadline:
        stream.pump()
        if stream.count(marker):
            return interruptions
        recovery_round += 1
        recovered = settle_promo_interruptions(
            artifacts,
            f"09_jingcha_wait_{recovery_round:02d}",
            observation_s=0.5,
            stop_event_title="京察之期",
        )
        if recovered:
            interruptions.extend(recovered)
        stream.pump()
        if stream.count(marker):
            return interruptions
        if recovered:
            acceptance.set_speed_five_and_unpause(
                artifacts,
                f"zg361_clean_jingcha_resume_{recovery_round:02d}",
                require_progress=True,
            )
        else:
            time.sleep(0.2)
    raise acceptance.RunnerError(
        "fixture Jingcha mandate did not arrive after the delayed timeline advance"
    )


def capture_jingcha_planner(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
    *,
    pause_service: GameplayBridgeService,
) -> dict[str, object]:
    close_scoreboard_panel(artifacts, "09_jingcha")
    stream.wait("ZGA: TEST PASS clean_jingcha_dispatch_scheduled", 30)
    jingcha_interruptions = advance_to_jingcha_mandate(stream, artifacts)
    stream.wait("ZGA: TEST PASS clean_jingcha_dispatched", 30)
    if stream.count("ZGA: TEST PASS jingcha_mandate_issued") != 1:
        raise acceptance.RunnerError(
            "Jingcha mandate marker must occur exactly once"
        )
    jingcha_interruptions.extend(
        settle_promo_interruptions(
            artifacts,
            "09_jingcha_mandate_preemption",
            observation_s=20.0,
            stop_event_title="京察之期",
        )
    )
    acceptance.wait_for_ocr_text(
        "京察之期",
        PROMO_EVENT_TITLE_REGION,
        20,
        artifacts,
        "09_jingcha_mandate_event.png",
        contains=True,
        stable_hits=1,
    )
    if recorder:
        recorder.mark("jingcha_mandate_visible")
        recorder.clean_hold("jingcha_mandate", artifacts)
    host_option = acceptance.wait_for_ocr_text(
        "依例举办京察",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "09_jingcha_host_option.png",
        stable_hits=1,
    )
    mandate_date = acceptance.read_hud_game_date()
    if mandate_date is None:
        raise acceptance.RunnerError(
            "Jingcha mandate HUD date is unreadable before accepting the host option"
        )
    mandate_day = mandate_date[0]
    # Arm speed one through the same exact-build native bridge used by the MCP
    # title matrix.  Keyboard and OCR latency must not advance weeks of game
    # time or expose the real historical player to an unrelated death roll.
    speed_one_submission = pause_service.execute_step("set-speed-1")
    pre_click_snapshot = pause_service.snapshot()
    acceptance.deliberate_click(host_option, "production host Jingcha option")
    host_pause_evidence = pause_after_jingcha_host_click(
        pause_service,
        stream,
        artifacts,
        mandate_day,
        pre_click_snapshot,
    )
    host_pause_evidence["native_speed_one_submission"] = speed_one_submission
    write_json(artifacts / "09_jingcha_host_immediate_pause_gate.json", host_pause_evidence)
    plan_button = acceptance.wait_for_ocr_text(
        "规划京察大计",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "09_jingcha_activity_detail.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(plan_button, "production plan Jingcha activity button")
    rendered_text = acceptance.wait_for_ocr_tokens(
        ("京察大计", "选择京察举办地"),
        ("activity_zg361", "zg361_jingcha_phase", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "09_jingcha_planner",
    )
    if recorder:
        recorder.mark("free_jingcha_planner_visible")
        recorder.clean_hold("free_jingcha_planner", artifacts, 3.0)
    exit_planner = acceptance.wait_for_ocr_text(
        "退出活动规划",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "09_jingcha_exit_planner.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(exit_planner, "native exit activity planning button")
    acceptance.wait_for_ocr_text(
        "放弃京察大计规划",
        acceptance.FULL_SCREEN_REGION,
        10,
        artifacts,
        "09_jingcha_exit_confirmation.png",
        stable_hits=1,
    )
    exit_confirmation = acceptance.wait_for_ocr_text(
        "确认",
        acceptance.FULL_SCREEN_REGION,
        10,
        artifacts,
        "09_jingcha_exit_confirm_button.png",
        stable_hits=1,
    )
    acceptance.click_until_text_disappears(
        exit_confirmation,
        "放弃京察大计规划",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    isolated.wait_for_gameplay_hud(artifacts)
    return {
        "real_mandate_event_path": True,
        "clean_dispatch_scheduled_marker_count": stream.count(
            "ZGA: TEST PASS clean_jingcha_dispatch_scheduled"
        ),
        "clean_dispatch_marker_count": stream.count(
            "ZGA: TEST PASS clean_jingcha_dispatched"
        ),
        "mandate_marker_count": stream.count("ZGA: TEST PASS jingcha_mandate_issued"),
        "planner_opened": True,
        "custom_activity_title_ocr": True,
        "custom_destination_prompt_ocr": True,
        "unrelated_vanilla_activity_catalog_allowed": True,
        "planner_artifact": "09_jingcha_planner.png",
        "planner_ocr_artifact": "09_jingcha_planner_ocr.json",
        "host_pause_gate": host_pause_evidence,
        "preempting_product_events_dismissed": jingcha_interruptions,
        "normalized_ocr": rendered_text,
    }


def _personal_switch_native_snapshot(
    snapshot: dict[str, object],
) -> dict[str, object]:
    active_event = snapshot.get("active_event")
    active_event_id = (
        active_event.get("instance_id") if isinstance(active_event, dict) else None
    )
    active_event_option_count = (
        active_event.get("option_count") if isinstance(active_event, dict) else None
    )
    return {
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "speed": snapshot.get("speed"),
        "active_event_instance_id": active_event_id,
        "active_event_option_count": active_event_option_count,
    }


def query_event_definition_identity(
    service: GameplayBridgeService,
    snapshot: dict[str, object],
) -> dict[str, object]:
    """Resolve one snapshot-bound canonical event definition through MCP."""

    observation = _personal_switch_native_snapshot(snapshot)
    event_instance_id = observation["active_event_instance_id"]
    revision = snapshot.get("revision")
    if isinstance(event_instance_id, bool) or not isinstance(
        event_instance_id, int
    ):
        raise acceptance.RunnerError(
            "native event-definition query lacks an active event instance"
        )
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise acceptance.RunnerError(
            "native event-definition query lacks a public revision"
        )
    query = service.query_current_event_window_context_v1(
        event_instance_id,
        expected_revision=revision,
    )
    context = query.get("current_event_window_context")
    readiness = context.get("readiness") if isinstance(context, dict) else None
    event_definition_key = (
        context.get("event_definition_key") if isinstance(context, dict) else None
    )
    if not (
        query.get("status") == "available"
        and isinstance(readiness, dict)
        and readiness.get("event_definition_identity_ready") is True
        and isinstance(event_definition_key, str)
        and event_definition_key
    ):
        raise acceptance.RunnerError(
            "event-window MCP did not publish canonical definition identity"
        )
    return {
        "event_instance_id": event_instance_id,
        "snapshot_revision": revision,
        "event_definition_key": event_definition_key,
        "query": query,
    }


def accept_zhongguo_result_case_snapshot_v1_live_cell(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    notice_identity: dict[str, object],
    paused_snapshot: dict[str, object],
    stem: str = "10_phase2_325_notice_result_case_snapshot_v1",
) -> dict[str, object]:
    """Prove the received-self result case on the paused zg361.50 frame.

    The played character and the event root independently bind the subject.
    The expected owner comes from the event's zg361_notice_prompt_owner saved
    scope.  When the visible zg361_reviewing_superior scope is published, it
    must resolve to that same owner.  No fixture character ID, OCR text, log
    marker, coordinate, caller-selected subject, case-kind input, or variable
    name participates in this cell.
    """

    tool_name = "ck3_query_zhongguo_result_case_snapshot_v1"
    capability_path = artifacts / f"{stem}_capabilities.json"
    requests_path = artifacts / f"{stem}_requests.json"
    responses_path = artifacts / f"{stem}_responses.json"
    gate_path = artifacts / f"{stem}_gate.json"
    requests: list[dict[str, object]] = []
    responses: list[dict[str, object]] = []
    capability_sidecar: dict[str, object] = {
        "schema_version": 1,
        "tool_name": tool_name,
        "required_bridge_capability": (
            QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
        ),
        "capabilities": None,
    }
    request_sidecar: dict[str, object] = {
        "schema_version": 1,
        "tool_name": tool_name,
        "requests": requests,
    }
    response_sidecar: dict[str, object] = {
        "schema_version": 1,
        "tool_name": tool_name,
        "responses": responses,
    }
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "tool_name": tool_name,
        "case_kind": ZHONGGUO_RESULT_CASE_KIND_V1,
        "frame": "paused_zg361.50_received_self_notice_before_refusal",
        "subject_source": (
            "paused_snapshot.played_character + "
            "current_event_window_context.root_scope.typed_identity"
        ),
        "owner_source": (
            "current_event_window_context.saved_scopes"
            "[zg361_notice_prompt_owner].scope.typed_identity"
        ),
        "visible_owner_cross_check_source": (
            "current_event_window_context.saved_scopes"
            "[zg361_reviewing_superior].scope.typed_identity"
        ),
        "ocr_used": False,
        "log_character_id_fallback_used": False,
        "fixture_character_id_used": False,
        "capability_sidecar": capability_path.name,
        "requests_sidecar": requests_path.name,
        "responses_sidecar": responses_path.name,
        "binding": None,
        "owner_scope_observation": None,
        "positive_nonces": [],
        "negative_cases": [],
        "observed_result_case": None,
        "checks": {},
        "failure_reason": None,
    }

    def flush() -> None:
        write_json(capability_path, capability_sidecar)
        write_json(requests_path, request_sidecar)
        write_json(responses_path, response_sidecar)
        write_json(gate_path, evidence)

    def require(condition: bool, reason: str) -> None:
        if not condition:
            raise ValueError(reason)

    def integer(
        value: object,
        label: str,
        *,
        minimum: int,
        maximum: int,
    ) -> int:
        require(
            isinstance(value, int)
            and not isinstance(value, bool)
            and minimum <= value <= maximum,
            f"{label} must be an integer in range",
        )
        assert isinstance(value, int)
        return value

    def positive_int32(value: object, label: str) -> int:
        return integer(value, label, minimum=1, maximum=2**31 - 1)

    def public_revision(value: object) -> int:
        return integer(
            value,
            "paused snapshot revision",
            minimum=0,
            maximum=2**64 - 1,
        )

    def typed_value(
        group: object, field_name: str, group_name: str
    ) -> object:
        require(isinstance(group, dict), f"{group_name} is not an object")
        assert isinstance(group, dict)
        field = group.get(field_name)
        require(
            isinstance(field, dict)
            and set(field)
            == {"status", "value", "unavailable_reason"}
            and field.get("status") == "available"
            and field.get("unavailable_reason") is None,
            f"{group_name}.{field_name} is not typed available",
        )
        assert isinstance(field, dict)
        return field.get("value")

    def has_fields(value: object, expected: dict[str, object]) -> bool:
        return isinstance(value, dict) and all(
            value.get(key) == expected_value
            for key, expected_value in expected.items()
        )

    def all_typed_leaves_unavailable(
        group: object, field_names: tuple[str, ...]
    ) -> bool:
        if not isinstance(group, dict) or set(group) != set(field_names):
            return False
        return all(
            has_fields(
                group.get(field_name),
                {
                    "status": "unavailable",
                    "value": None,
                    "unavailable_reason": "case_unavailable",
                },
            )
            for field_name in field_names
        )

    def has_frame_binding(
        response: dict[str, object], nonce: str, actual_owner: int | None
    ) -> bool:
        return has_fields(
            response.get("binding"),
            {
                "request_nonce": nonce,
                "snapshot_id": paused_snapshot.get("snapshot_id"),
                "revision": paused_snapshot.get("revision"),
                "native_revision": paused_snapshot.get("native_revision"),
                "connection_generation": connection_generation,
                "date_raw": paused_snapshot.get("date_raw"),
                "paused": True,
                "player_character_id": subject_character_id,
                "subject_character_id": subject_character_id,
                "owner_character_id": actual_owner,
                "expected_revision": paused_snapshot.get("revision"),
            },
        )

    def binding_without_nonce(response: dict[str, object]) -> dict[str, object]:
        detached = {
            key: value
            for key, value in response.items()
            if key != "request_nonce"
        }
        binding = detached.get("binding")
        require(
            isinstance(binding, dict),
            "result-case response lacks a binding",
        )
        assert isinstance(binding, dict)
        detached["binding"] = {
            key: value
            for key, value in binding.items()
            if key != "request_nonce"
        }
        return detached

    def saved_character_id(row: object, label: str) -> int:
        require(isinstance(row, dict), f"{label} row is not an object")
        assert isinstance(row, dict)
        scope = row.get("scope")
        require(
            isinstance(scope, dict)
            and scope.get("status") == "available"
            and scope.get("raw_type_index") == 4
            and scope.get("type_key") == "character",
            f"{label} scope is not a typed character",
        )
        assert isinstance(scope, dict)
        identity = scope.get("typed_identity")
        require(
            isinstance(identity, dict)
            and identity.get("status") == "available"
            and identity.get("kind") == "character",
            f"{label} scope lacks an available character identity",
        )
        assert isinstance(identity, dict)
        return positive_int32(
            identity.get("character_id"),
            f"{label} character_id",
        )

    def query(
        label: str,
        *,
        nonce: str,
        owner_character_id: int,
        expected_revision: int,
        expected_outcome: str,
    ) -> dict[str, object]:
        arguments: dict[str, object] = {
            "request_nonce": nonce,
            "expected_revision": expected_revision,
            "owner_character_id": owner_character_id,
        }
        requests.append(
            {
                "label": label,
                "expected_outcome": expected_outcome,
                "arguments": arguments,
            }
        )
        write_json(requests_path, request_sidecar)
        response = service.query_zhongguo_result_case_snapshot_v1(
            nonce,
            expected_revision=expected_revision,
            owner_character_id=owner_character_id,
        )
        require(
            isinstance(response, dict),
            f"{label} response is not an object",
        )
        responses.append({"label": label, "response": response})
        write_json(responses_path, response_sidecar)
        return response

    try:
        require(
            notice_identity.get("event_definition_key") == "zg361.50",
            "result-case live cell was not attached to the zg361.50 notice",
        )
        revision = public_revision(paused_snapshot.get("revision"))
        require(
            paused_snapshot.get("paused") is True,
            "result-case live cell requires the paused notice frame",
        )
        require(
            notice_identity.get("snapshot_revision") == revision,
            "notice identity and paused snapshot revision differ",
        )
        played_character = paused_snapshot.get("played_character")
        require(
            isinstance(played_character, dict),
            "paused notice snapshot lacks the played reviewed subject",
        )
        assert isinstance(played_character, dict)
        played_character_id = positive_int32(
            played_character.get("character_id"),
            "played subject character_id",
        )
        diagnostics = paused_snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        integer(
            connection_generation,
            "paused notice connection generation",
            minimum=1,
            maximum=2**64 - 1,
        )

        identity_query = notice_identity.get("query")
        context = (
            identity_query.get("current_event_window_context")
            if isinstance(identity_query, dict)
            else None
        )
        readiness = (
            context.get("readiness") if isinstance(context, dict) else None
        )
        root_scope = (
            context.get("root_scope") if isinstance(context, dict) else None
        )
        require(
            isinstance(readiness, dict)
            and readiness.get("root_scope_ready") is True,
            "zg361.50 notice did not publish a ready typed root scope",
        )
        require(
            isinstance(root_scope, dict)
            and root_scope.get("status") == "available"
            and root_scope.get("raw_type_index") == 4
            and root_scope.get("type_key") == "character",
            "zg361.50 root scope is not a typed character",
        )
        assert isinstance(root_scope, dict)
        typed_identity = root_scope.get("typed_identity")
        require(
            isinstance(typed_identity, dict)
            and typed_identity.get("status") == "available"
            and typed_identity.get("kind") == "character",
            "zg361.50 root scope lacks an available character identity",
        )
        assert isinstance(typed_identity, dict)
        subject_character_id = positive_int32(
            typed_identity.get("character_id"),
            "notice root subject character_id",
        )
        require(
            subject_character_id == played_character_id,
            "zg361.50 notice root is not the played reviewed subject",
        )

        saved_scopes = (
            context.get("saved_scopes") if isinstance(context, dict) else None
        )
        require(
            isinstance(readiness, dict)
            and readiness.get("saved_scopes_ready") is True
            and isinstance(saved_scopes, list),
            "zg361.50 notice did not publish ready typed saved scopes",
        )
        assert isinstance(saved_scopes, list)
        notice_owner_rows = [
            row
            for row in saved_scopes
            if isinstance(row, dict)
            and row.get("name") == "zg361_notice_prompt_owner"
        ]
        reviewing_superior_rows = [
            row
            for row in saved_scopes
            if isinstance(row, dict)
            and row.get("name") == "zg361_reviewing_superior"
        ]
        require(
            len(notice_owner_rows) == 1,
            "zg361.50 notice lacks one canonical notice-prompt-owner scope",
        )
        require(
            len(reviewing_superior_rows) <= 1,
            "zg361.50 notice published duplicate reviewing-superior scopes",
        )
        owner_character_id = saved_character_id(
            notice_owner_rows[0],
            "notice prompt owner",
        )
        visible_owner_character_id: int | None = None
        if reviewing_superior_rows:
            visible_owner_character_id = saved_character_id(
                reviewing_superior_rows[0],
                "visible reviewing superior",
            )
            require(
                visible_owner_character_id == owner_character_id,
                "zg361.50 visible reviewing superior does not match "
                "the notice prompt owner",
            )
        require(
            owner_character_id != subject_character_id,
            "zg361.50 result owner must differ from the received-self subject",
        )

        capabilities = service.capabilities()
        require(
            isinstance(capabilities, dict),
            "bridge capabilities are unavailable",
        )
        assert isinstance(capabilities, dict)
        capability_sidecar["capabilities"] = capabilities
        bridge_capabilities = capabilities.get("bridge_capabilities")
        require(
            capabilities.get(
                "zhongguo_result_case_snapshot_v1_query_supported"
            )
            is True
            and isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities,
            "native bridge did not advertise the ZhongGuo result-case tool",
        )

        checks = evidence["checks"]
        assert isinstance(checks, dict)
        checks["capability_advertised"] = True
        checks["subject_from_typed_notice_root"] = True
        checks["played_character_is_received_self_subject"] = True
        checks["owner_from_notice_prompt_saved_scope"] = True
        checks["visible_reviewing_superior_cross_check"] = (
            "matched"
            if visible_owner_character_id is not None
            else "not_published"
        )
        evidence["owner_scope_observation"] = {
            "zg361_notice_prompt_owner_count": len(notice_owner_rows),
            "zg361_reviewing_superior_count": len(reviewing_superior_rows),
            "selected_owner_scope": "zg361_notice_prompt_owner",
            "visible_cross_check": (
                "matched"
                if visible_owner_character_id is not None
                else "not_published"
            ),
        }
        evidence["binding"] = {
            "snapshot_id": paused_snapshot.get("snapshot_id"),
            "revision": revision,
            "native_revision": paused_snapshot.get("native_revision"),
            "connection_generation": connection_generation,
            "date_raw": paused_snapshot.get("date_raw"),
            "paused": True,
            "player_character_id": subject_character_id,
            "subject_character_id": subject_character_id,
            "owner_character_id": owner_character_id,
            "active_event_instance_id": _personal_switch_native_snapshot(
                paused_snapshot
            )["active_event_instance_id"],
            "event_definition_key": notice_identity["event_definition_key"],
        }

        positive_nonces = (
            "zg361.phase2.result_case.01",
            "zg361.phase2.result_case.02",
        )
        first = query(
            "same_frame_positive_01",
            nonce=positive_nonces[0],
            owner_character_id=owner_character_id,
            expected_revision=revision,
            expected_outcome="available_received_self_open_result_case",
        )
        second = query(
            "same_frame_positive_02",
            nonce=positive_nonces[1],
            owner_character_id=owner_character_id,
            expected_revision=revision,
            expected_outcome="available_received_self_open_result_case",
        )
        evidence["positive_nonces"] = list(positive_nonces)

        observed_projection: dict[str, object] | None = None
        for index, (nonce, response) in enumerate(
            zip(positive_nonces, (first, second), strict=True),
            start=1,
        ):
            require(
                response.get("status") == "available"
                and response.get("unavailable_reason") is None,
                f"positive query {index} did not return an available result case",
            )
            require(
                has_fields(
                    response,
                    {
                        "case_kind": ZHONGGUO_RESULT_CASE_KIND_V1,
                        "request_nonce": nonce,
                        "snapshot_revision": paused_snapshot.get(
                            "native_revision"
                        ),
                        "date_raw": paused_snapshot.get("date_raw"),
                        "paused": True,
                        "player_character_id": subject_character_id,
                        "subject_character_id": subject_character_id,
                        "requested_owner_character_id": owner_character_id,
                    },
                ),
                f"positive query {index} top-level binding drifted",
            )
            require(
                has_frame_binding(response, nonce, owner_character_id),
                f"positive query {index} response binding drifted",
            )

            case = response.get("case")
            case_cycle = integer(
                typed_value(case, "cycle_serial", "case"),
                "case.cycle_serial",
                minimum=1,
                maximum=2**63 - 1,
            )
            case_serial = integer(
                typed_value(case, "case_serial", "case"),
                "case.case_serial",
                minimum=1,
                maximum=999_999,
            )
            require(
                typed_value(case, "owner_character_id", "case")
                == owner_character_id
                and typed_value(case, "subject_character_id", "case")
                == subject_character_id
                and typed_value(case, "state", "case") == 1
                and typed_value(case, "grade", "case") == 1,
                f"positive query {index} open result-case identity drifted",
            )

            notice = response.get("notice")
            absolute_grade = integer(
                typed_value(notice, "absolute_grade", "notice"),
                "notice.absolute_grade",
                minimum=1,
                maximum=3,
            )
            kpi_frozen_q100000 = integer(
                typed_value(
                    notice,
                    "kpi_frozen_q100000",
                    "notice",
                ),
                "notice.kpi_frozen_q100000",
                minimum=-(2**63),
                maximum=2**63 - 1,
            )
            rank_frozen = integer(
                typed_value(notice, "rank_frozen", "notice"),
                "notice.rank_frozen",
                minimum=1,
                maximum=2**63 - 1,
            )
            cohort_n_frozen = integer(
                typed_value(notice, "cohort_n_frozen", "notice"),
                "notice.cohort_n_frozen",
                minimum=1,
                maximum=2**63 - 1,
            )
            require(
                rank_frozen <= cohort_n_frozen,
                f"positive query {index} notice rank exceeds its cohort",
            )

            delivery = response.get("delivery")
            require(
                typed_value(delivery, "method", "delivery") == 0
                and typed_value(
                    delivery,
                    "objection_recorded",
                    "delivery",
                )
                is False
                and typed_value(
                    delivery,
                    "settlement_posted_serial",
                    "delivery",
                )
                == 0
                and typed_value(delivery, "appeal_open", "delivery")
                is False,
                f"positive query {index} is not the open delivery matrix",
            )
            response_readiness = response.get("readiness")
            require(
                response_readiness
                == {
                    "player_subject_binding_ready": True,
                    "owner_binding_ready": True,
                    "case_identity_ready": True,
                    "notice_facts_ready": True,
                    "delivery_state_ready": True,
                    "same_frame_ready": True,
                    "ready": True,
                },
                f"positive query {index} readiness is not fully GREEN",
            )

            projection = {
                "case": {
                    "owner_character_id": owner_character_id,
                    "subject_character_id": subject_character_id,
                    "cycle_serial": case_cycle,
                    "case_serial": case_serial,
                    "state": 1,
                    "grade": 1,
                },
                "notice": {
                    "absolute_grade": absolute_grade,
                    "kpi_frozen_q100000": kpi_frozen_q100000,
                    "rank_frozen": rank_frozen,
                    "cohort_n_frozen": cohort_n_frozen,
                },
                "delivery": {
                    "method": 0,
                    "objection_recorded": False,
                    "settlement_posted_serial": 0,
                    "appeal_open": False,
                },
                "readiness": {"ready": True},
            }
            if observed_projection is None:
                observed_projection = projection
            else:
                require(
                    projection == observed_projection,
                    "consecutive result-case projections differ",
                )

        require(
            binding_without_nonce(first) == binding_without_nonce(second),
            "consecutive result-case queries did not return one semantic frame",
        )
        require(
            observed_projection is not None,
            "positive result-case projection was not recorded",
        )
        evidence["observed_result_case"] = observed_projection
        checks["consecutive_queries_same_semantic_frame"] = True
        checks["result_case_owner_subject_cycle_case_bound"] = True
        checks["open_state_and_grade_one"] = True
        checks["notice_facts_include_q100000"] = True
        checks["open_delivery_matrix_projected"] = True
        checks["aggregate_readiness_ready"] = True

        wrong_owner = (
            owner_character_id + 1
            if owner_character_id < 2**31 - 1
            else owner_character_id - 1
        )
        wrong_nonce = "zg361.phase2.result_case.wrong_owner"
        wrong_owner_response = query(
            "wrong_owner_typed_red",
            nonce=wrong_nonce,
            owner_character_id=wrong_owner,
            expected_revision=revision,
            expected_outcome="typed_red_owner_filter_mismatch_fully_wiped",
        )
        wrong_group_fields = {
            "case": (
                "owner_character_id",
                "subject_character_id",
                "cycle_serial",
                "case_serial",
                "state",
                "grade",
            ),
            "notice": (
                "absolute_grade",
                "kpi_frozen_q100000",
                "rank_frozen",
                "cohort_n_frozen",
            ),
            "delivery": (
                "method",
                "objection_recorded",
                "settlement_posted_serial",
                "appeal_open",
            ),
        }
        wrong_readiness = wrong_owner_response.get("readiness")
        require(
            has_fields(
                wrong_owner_response,
                {
                    "status": "unavailable",
                    "unavailable_reason": "owner_filter_mismatch",
                    "case_kind": ZHONGGUO_RESULT_CASE_KIND_V1,
                    "request_nonce": wrong_nonce,
                    "snapshot_revision": paused_snapshot.get(
                        "native_revision"
                    ),
                    "date_raw": paused_snapshot.get("date_raw"),
                    "paused": True,
                    "player_character_id": subject_character_id,
                    "subject_character_id": subject_character_id,
                    "requested_owner_character_id": wrong_owner,
                },
            )
            and has_frame_binding(wrong_owner_response, wrong_nonce, None)
            and all(
                all_typed_leaves_unavailable(
                    wrong_owner_response.get(group_name),
                    field_names,
                )
                for group_name, field_names in wrong_group_fields.items()
            )
            and wrong_readiness
            == {
                "player_subject_binding_ready": False,
                "owner_binding_ready": False,
                "case_identity_ready": False,
                "notice_facts_ready": False,
                "delivery_state_ready": False,
                "same_frame_ready": True,
                "ready": False,
            },
            "wrong-owner query did not return a fully wiped "
            "owner_filter_mismatch RED",
        )
        checks["wrong_owner_typed_red"] = True
        checks["wrong_owner_all_typed_leaves_unavailable"] = {
            group_name: len(field_names)
            for group_name, field_names in wrong_group_fields.items()
        }

        final_snapshot = service.snapshot()
        initial_frame = {
            **_personal_switch_native_snapshot(paused_snapshot),
            "snapshot_id": paused_snapshot.get("snapshot_id"),
            "connection_generation": connection_generation,
            "played_character_id": subject_character_id,
        }
        final_character = final_snapshot.get("played_character")
        final_diagnostics = final_snapshot.get("diagnostics")
        final_frame = {
            **_personal_switch_native_snapshot(final_snapshot),
            "snapshot_id": final_snapshot.get("snapshot_id"),
            "connection_generation": (
                final_diagnostics.get("connection_generation")
                if isinstance(final_diagnostics, dict)
                else None
            ),
            "played_character_id": (
                final_character.get("character_id")
                if isinstance(final_character, dict)
                else None
            ),
        }
        require(
            final_frame == initial_frame,
            "read-only result-case cell changed the paused notice frame",
        )
        checks["read_only_notice_frame_unchanged"] = True
        evidence["negative_cases"] = [
            {
                "label": "wrong_owner_typed_red",
                "status": "unavailable",
                "reason": "owner_filter_mismatch",
                "semantic_groups_wiped": ["case", "notice", "delivery"],
            }
        ]
        evidence["result"] = "GREEN"
        flush()
        return evidence
    except Exception as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        flush()
        raise acceptance.RunnerError(
            "ZhongGuo result-case snapshot v1 live cell failed: "
            f"{type(error).__name__}: {error}"
        ) from error


def select_resolved_event_option_native(
    service: GameplayBridgeService,
    artifacts: Path,
    snapshot: dict[str, object],
    *,
    stem: str,
    expected_event_definition_key: str,
    expected_option_text: str,
) -> dict[str, object]:
    """Select one configured choice from the typed event-window frame."""

    observation = _personal_switch_native_snapshot(snapshot)
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "selection_method": "native_mcp_resolved_option",
        "expected_event_definition_key": expected_event_definition_key,
        "expected_option_text": expected_option_text,
        "preselection_observation": observation,
        "identity": None,
        "matched_options": [],
        "selected_native_option_index": None,
        "selected_option_number": None,
        "selection_submission": None,
        "failure_reason": None,
    }
    evidence_path = artifacts / f"{stem}_native_option_selection_gate.json"

    def fail(reason: str) -> None:
        evidence["failure_reason"] = reason
        write_json(evidence_path, evidence)
        raise acceptance.RunnerError(reason)

    if snapshot.get("paused") is not True:
        fail("policy option selection requires a paused native snapshot")
    event_instance_id = observation["active_event_instance_id"]
    revision = snapshot.get("revision")
    if isinstance(event_instance_id, bool) or not isinstance(
        event_instance_id, int
    ):
        fail("policy option selection lacks an active event instance")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        fail("policy option selection lacks a valid public revision")

    try:
        identity = query_event_definition_identity(service, snapshot)
    except Exception as error:
        fail(
            "policy option identity query failed: "
            f"{type(error).__name__}: {error}"
        )
    evidence["identity"] = identity
    observed_key = identity["event_definition_key"]
    if observed_key != expected_event_definition_key:
        fail(
            "policy option event identity mismatch: "
            f"expected {expected_event_definition_key}, observed {observed_key}"
        )

    query = identity["query"]
    context = query.get("current_event_window_context")
    readiness = context.get("readiness") if isinstance(context, dict) else None
    options = context.get("options") if isinstance(context, dict) else None
    if not (
        isinstance(readiness, dict)
        and readiness.get("option_presentation_ready") is True
        and isinstance(options, list)
    ):
        fail("policy event-window MCP did not publish option presentation")

    expected = _normalize_promo_visible_text(expected_option_text)
    if not expected:
        fail("configured policy option text normalizes to an empty value")
    matches = [
        option
        for option in options
        if isinstance(option, dict)
        and option.get("shown") is True
        and option.get("enabled") is True
        and isinstance(option.get("resolved_name"), str)
        and expected
        in _normalize_promo_visible_text(str(option["resolved_name"]))
    ]
    evidence["matched_options"] = matches
    if len(matches) != 1:
        fail(
            "policy event-window MCP did not resolve exactly one configured "
            f"option: matches={len(matches)}"
        )

    native_option_index = matches[0].get("native_option_index")
    option_count = observation["active_event_option_count"]
    if (
        isinstance(native_option_index, bool)
        or not isinstance(native_option_index, int)
        or native_option_index < 0
        or isinstance(option_count, bool)
        or not isinstance(option_count, int)
        or native_option_index >= option_count
    ):
        fail("resolved policy option has an invalid native option index")
    option_number = native_option_index + 1
    evidence["selected_native_option_index"] = native_option_index
    evidence["selected_option_number"] = option_number

    try:
        submission = service.select_event_option(
            option_number,
            event_instance_id=event_instance_id,
            expected_revision=revision,
        )
    except Exception as error:
        fail(
            "native policy option selection failed: "
            f"{type(error).__name__}: {error}"
        )
    evidence["selection_submission"] = submission
    if not (
        isinstance(submission, dict)
        and submission.get("accepted") is True
        and submission.get("status") == "submitted"
    ):
        fail("native policy option selection was not accepted")

    evidence["result"] = "GREEN"
    evidence["failure_reason"] = None
    write_json(evidence_path, evidence)
    return evidence


def pause_bound_native_event_for_definition_query(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    stem: str,
) -> dict[str, object]:
    """Freeze one visible event before issuing a paused-only identity query."""

    starting = service.snapshot()
    starting_observation = _personal_switch_native_snapshot(starting)
    starting_event = starting_observation["active_event_instance_id"]
    starting_date = starting_observation["date_raw"]
    starting_revision = starting.get("revision")
    starting_character = starting.get("played_character")
    starting_character_id = (
        starting_character.get("character_id")
        if isinstance(starting_character, dict)
        else None
    )
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "starting_observation": starting_observation,
        "starting_character_id": starting_character_id,
        "pause_submission": None,
        "pause_observations": [],
        "paused_revision": None,
        "event_instance_stable": False,
        "date_stable": False,
        "played_character_stable": False,
        "failure_reason": None,
    }
    evidence_path = artifacts / f"{stem}_prequery_pause_gate.json"

    def fail(reason: str) -> None:
        evidence["failure_reason"] = reason
        write_json(evidence_path, evidence)
        raise acceptance.RunnerError(reason)

    if isinstance(starting_event, bool) or not isinstance(starting_event, int):
        fail("native event-definition pause gate lacks an active event instance")
    if isinstance(starting_date, bool) or not isinstance(starting_date, int):
        fail("native event-definition pause gate lacks date_raw")
    if (
        isinstance(starting_character_id, bool)
        or not isinstance(starting_character_id, int)
    ):
        fail("native event-definition pause gate lacks a played character")
    if (
        isinstance(starting_revision, bool)
        or not isinstance(starting_revision, int)
        or starting_revision < 0
    ):
        fail("native event-definition pause gate lacks a public revision")
    if (
        starting.get("paused") is not True
        and starting.get("paused") is not False
    ):
        fail("native event-definition pause gate lacks paused state")

    paused = starting
    if starting.get("paused") is not True:
        try:
            pause_submission = service.execute_step(
                "pause-map", expected_revision=starting_revision
            )
        except Exception as error:
            fail(
                "native pause-map submission failed before event-definition query: "
                f"{type(error).__name__}: {error}"
            )
        evidence["pause_submission"] = pause_submission
        if not (
            isinstance(pause_submission, dict)
            and pause_submission.get("accepted") is True
            and pause_submission.get("status") == "submitted"
        ):
            fail("native pause-map was not accepted before event-definition query")

        pause_deadline = time.monotonic() + 5.0
        while time.monotonic() < pause_deadline:
            paused = service.snapshot()
            observed = _personal_switch_native_snapshot(paused)
            character = paused.get("played_character")
            character_id = (
                character.get("character_id")
                if isinstance(character, dict)
                else None
            )
            observation = {
                **observed,
                "played_character_id": character_id,
            }
            evidence["pause_observations"].append(observation)
            if observed["active_event_instance_id"] != starting_event:
                fail("active event changed before event-definition query pause")
            if observed["date_raw"] != starting_date:
                fail("game date changed before event-definition query pause")
            if character_id != starting_character_id:
                fail("played character changed before event-definition query pause")
            if paused.get("paused") is True:
                break
            time.sleep(0.05)
        if paused.get("paused") is not True:
            fail("native MCP did not pause the visible event before identity query")
    else:
        evidence["pause_submission"] = {
            "step": "pause-map",
            "accepted": True,
            "status": "not_needed_already_paused",
        }
        evidence["pause_observations"].append(
            {
                **starting_observation,
                "played_character_id": starting_character_id,
            }
        )

    paused_observation = _personal_switch_native_snapshot(paused)
    paused_character = paused.get("played_character")
    paused_character_id = (
        paused_character.get("character_id")
        if isinstance(paused_character, dict)
        else None
    )
    paused_revision = paused.get("revision")
    evidence["paused_revision"] = paused_revision
    evidence["event_instance_stable"] = (
        paused_observation["active_event_instance_id"] == starting_event
    )
    evidence["date_stable"] = paused_observation["date_raw"] == starting_date
    evidence["played_character_stable"] = (
        paused_character_id == starting_character_id
    )
    if paused.get("paused") is not True:
        fail("event-definition query snapshot is not paused")
    if not evidence["event_instance_stable"]:
        fail("active event changed before the paused identity query")
    if not evidence["date_stable"]:
        fail("game date changed before the paused identity query")
    if not evidence["played_character_stable"]:
        fail("played character changed before the paused identity query")
    if (
        isinstance(paused_revision, bool)
        or not isinstance(paused_revision, int)
        or paused_revision < 0
    ):
        fail("paused event-definition query snapshot lacks a public revision")

    evidence["result"] = "GREEN"
    evidence["failure_reason"] = None
    write_json(evidence_path, evidence)
    return {
        "snapshot": paused,
        "evidence": evidence,
    }


def select_single_option_interruption_native(
    service: GameplayBridgeService,
    artifacts: Path,
    stem: str,
    *,
    expected_event_instance_id: int,
) -> dict[str, object]:
    """Bind, pause and clear one forced-choice event through the native MCP."""

    before = service.snapshot()
    before_observation = _personal_switch_native_snapshot(before)
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "selection_method": "native_mcp_single_option",
        "expected_event_instance_id": expected_event_instance_id,
        "before": before_observation,
        "pause_submission": None,
        "pause_observations": [],
        "selection_submission": None,
        "after": None,
        "failure_reason": None,
    }
    evidence_path = artifacts / f"{stem}_native_single_option_gate.json"

    def fail(reason: str) -> None:
        evidence["failure_reason"] = reason
        write_json(evidence_path, evidence)
        raise acceptance.RunnerError(reason)

    event_id = before_observation["active_event_instance_id"]
    option_count = before_observation["active_event_option_count"]
    before_revision = before.get("revision")
    before_date = before.get("date_raw")
    if event_id != expected_event_instance_id:
        fail("native interruption event changed before single-option selection")
    if option_count != 1:
        fail("native interruption is not an exactly-one-option event")
    if (
        isinstance(before_revision, bool)
        or not isinstance(before_revision, int)
        or before_revision < 0
    ):
        fail("native interruption snapshot lacks a valid revision")
    if isinstance(before_date, bool) or not isinstance(before_date, int):
        fail("native interruption snapshot lacks a valid date_raw")

    paused = before
    if before.get("paused") is not True:
        evidence["pause_submission"] = service.execute_step(
            "pause-map", expected_revision=before_revision
        )
        pause_deadline = time.monotonic() + 5.0
        while time.monotonic() < pause_deadline:
            paused = service.snapshot()
            observed = _personal_switch_native_snapshot(paused)
            evidence["pause_observations"].append(observed)
            if observed["active_event_instance_id"] != expected_event_instance_id:
                fail("native interruption changed while waiting for pause-map")
            if observed["date_raw"] != before_date:
                fail("game date changed while pausing native interruption")
            if paused.get("paused") is True:
                break
            time.sleep(0.05)
        if paused.get("paused") is not True:
            fail("native MCP did not pause the single-option interruption")
    else:
        evidence["pause_submission"] = {
            "step": "pause-map",
            "accepted": True,
            "status": "not_needed_already_paused",
        }
        evidence["pause_observations"].append(before_observation)

    paused_observation = _personal_switch_native_snapshot(paused)
    paused_revision = paused.get("revision")
    if paused_observation["active_event_instance_id"] != expected_event_instance_id:
        fail("native interruption changed before bound option submission")
    if paused_observation["active_event_option_count"] != 1:
        fail("native interruption option count changed before submission")
    if (
        isinstance(paused_revision, bool)
        or not isinstance(paused_revision, int)
        or paused_revision < 0
    ):
        fail("paused native interruption lacks a valid revision")

    try:
        evidence["selection_submission"] = service.select_event_option(
            1,
            event_instance_id=expected_event_instance_id,
            expected_revision=paused_revision,
        )
    except Exception as error:
        evidence["failure_reason"] = (
            f"native single-option selection failed: {type(error).__name__}: {error}"
        )
        write_json(evidence_path, evidence)
        raise

    after = service.snapshot()
    after_observation = _personal_switch_native_snapshot(after)
    evidence["after"] = after_observation
    if after_observation["active_event_instance_id"] == expected_event_instance_id:
        fail("native option ACK did not advance the interruption instance")
    if after_observation["date_raw"] != before_date:
        fail("game date advanced while clearing native interruption")
    if after.get("paused") is not True:
        fail("native interruption selection did not leave CK3 paused")

    evidence["result"] = "GREEN"
    evidence["failure_reason"] = None
    write_json(evidence_path, evidence)
    return evidence


def resume_personal_switch_timeline_native(
    service: GameplayBridgeService,
    *,
    reason: str,
    timeout_s: float = 10.0,
) -> dict[str, object]:
    """Use the connected native MCP to resume speed five and prove one tick."""

    starting = service.snapshot()
    starting_raw = starting.get("date_raw")
    if not isinstance(starting_raw, int) or isinstance(starting_raw, bool):
        raise acceptance.RunnerError(
            "native personal-switch timeline snapshot lacks date_raw"
        )
    observations = [_personal_switch_native_snapshot(starting)]
    submissions: list[dict[str, object]] = []
    current = starting

    if current.get("speed") != 5:
        submissions.append(
            {"step": "set-speed-5", "result": service.execute_step("set-speed-5")}
        )
        speed_deadline = time.monotonic() + 5.0
        while time.monotonic() < speed_deadline:
            current = service.snapshot()
            observations.append(_personal_switch_native_snapshot(current))
            if current.get("speed") == 5:
                break
            time.sleep(0.05)
        if current.get("speed") != 5:
            raise acceptance.RunnerError(
                "native MCP did not observe speed five for personal-switch wait"
            )

    if current.get("paused") is True:
        submissions.append(
            {"step": "resume-map", "result": service.execute_step("resume-map")}
        )
    elif current.get("paused") is not False:
        raise acceptance.RunnerError(
            "native personal-switch timeline snapshot lacks paused state"
        )

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        current = service.snapshot()
        observations.append(_personal_switch_native_snapshot(current))
        current_raw = current.get("date_raw")
        if (
            current.get("paused") is False
            and current.get("speed") == 5
            and isinstance(current_raw, int)
            and not isinstance(current_raw, bool)
            and current_raw != starting_raw
        ):
            return {
                "reason": reason,
                "result": "GREEN",
                "terminal_condition": (
                    "date_advanced_to_active_event"
                    if _personal_switch_native_snapshot(current)[
                        "active_event_instance_id"
                    ]
                    is not None
                    else "date_advanced"
                ),
                "starting_date_raw": starting_raw,
                "resumed_date_raw": current_raw,
                "submissions": submissions,
                "observations": observations,
            }
        time.sleep(0.05)
    raise acceptance.RunnerError(
        "native MCP did not resume and advance the personal-switch timeline"
    )


def wait_for_native_event_definition(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    stem: str,
    expected_event_definition_key: str,
    timeout_s: float = 45.0,
    clear_unexpected_single_option_events: bool = True,
) -> dict[str, object]:
    """Reach one product event using native state, identity and ACK only.

    No OCR or geometry participates in navigation or the GREEN decision. An
    unrelated exactly-one-option event may be cleared through its bound native
    instance; a multi-option interruption is an explicit MCP/policy blocker.
    """

    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "navigation_method": "native_mcp_event_identity_and_ack",
        "expected_event_definition_key": expected_event_definition_key,
        "timeout_seconds": timeout_s,
        "observations": [],
        "identity_queries": [],
        "native_resumes": [],
        "cleared_single_option_interruptions": [],
        "terminal_identity": None,
        "failure_reason": None,
        "ocr_used_for_navigation": False,
        "visual_fallback_used": False,
    }
    evidence_path = artifacts / f"{stem}_native_event_wait_gate.json"

    def finish_red(reason: str) -> None:
        evidence["failure_reason"] = reason
        write_json(evidence_path, evidence)
        raise acceptance.RunnerError(reason)

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        snapshot = service.snapshot()
        observation = _personal_switch_native_snapshot(snapshot)
        observations = evidence["observations"]
        assert isinstance(observations, list)
        if not observations or observation != observations[-1]:
            observations.append(observation)

        active_event_id = observation["active_event_instance_id"]
        option_count = observation["active_event_option_count"]
        if isinstance(active_event_id, int) and not isinstance(
            active_event_id, bool
        ):
            try:
                pause_gate = pause_bound_native_event_for_definition_query(
                    service,
                    artifacts,
                    stem=f"{stem}_identity_{len(evidence['identity_queries']) + 1:02d}",
                )
                identity = query_event_definition_identity(
                    service, pause_gate["snapshot"]
                )
            except Exception as error:
                finish_red(
                    "native MCP event identity unavailable: "
                    f"{type(error).__name__}: {error}"
                )
            identity_queries = evidence["identity_queries"]
            assert isinstance(identity_queries, list)
            identity_queries.append(identity)
            if identity["event_definition_key"] == expected_event_definition_key:
                evidence["result"] = "GREEN"
                evidence["terminal_identity"] = identity
                evidence["failure_reason"] = None
                write_json(evidence_path, evidence)
                return {
                    "snapshot": pause_gate["snapshot"],
                    "identity": identity,
                    "evidence": evidence,
                }

            if option_count == 1 and clear_unexpected_single_option_events:
                cleared = select_single_option_interruption_native(
                    service,
                    artifacts,
                    f"{stem}_unexpected_{len(evidence['cleared_single_option_interruptions']) + 1:02d}",
                    expected_event_instance_id=active_event_id,
                )
                cleared["event_definition_key"] = identity[
                    "event_definition_key"
                ]
                cleared_rows = evidence["cleared_single_option_interruptions"]
                assert isinstance(cleared_rows, list)
                cleared_rows.append(cleared)
                continue

            finish_red(
                "unexpected event blocks native phase-two path: "
                f"{identity['event_definition_key']} options={option_count}; "
                "single-option auto-clear="
                f"{clear_unexpected_single_option_events}"
            )

        if snapshot.get("paused") is True or snapshot.get("speed") != 5:
            try:
                resume = resume_personal_switch_timeline_native(
                    service,
                    reason=f"{stem}_resume_to_{expected_event_definition_key}",
                    timeout_s=min(10.0, max(1.0, deadline - time.monotonic())),
                )
            except Exception as error:
                finish_red(
                    "native MCP timeline resume failed: "
                    f"{type(error).__name__}: {error}"
                )
            resumes = evidence["native_resumes"]
            assert isinstance(resumes, list)
            resumes.append(resume)
        else:
            time.sleep(0.05)

    finish_red(
        "native MCP timed out waiting for product event "
        f"{expected_event_definition_key}"
    )
    raise AssertionError("unreachable")


def wait_for_fixture_marker_native(
    stream: MarkerStream,
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    stem: str,
    marker: str,
    timeout_s: float = 20.0,
) -> dict[str, object]:
    """Advance natively until one fixture read-oracle marker is observed."""

    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "navigation_method": "native_mcp_timeline_and_fixture_read_oracle",
        "marker": marker,
        "marker_count": 0,
        "native_resumes": [],
        "pause_submission": None,
        "terminal_snapshot": None,
        "failure_reason": None,
        "ocr_used_for_navigation": False,
        "visual_fallback_used": False,
    }
    evidence_path = artifacts / f"{stem}_native_marker_wait_gate.json"
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        stream.pump()
        count = stream.count(marker)
        if count:
            snapshot = service.snapshot()
            if snapshot.get("paused") is not True:
                revision = snapshot.get("revision")
                try:
                    submission = service.execute_step(
                        "pause-map",
                        expected_revision=(
                            revision
                            if isinstance(revision, int)
                            and not isinstance(revision, bool)
                            else None
                        ),
                    )
                except Exception as error:
                    evidence["failure_reason"] = (
                        "native pause after fixture marker failed: "
                        f"{type(error).__name__}: {error}"
                    )
                    write_json(evidence_path, evidence)
                    raise acceptance.RunnerError(
                        str(evidence["failure_reason"])
                    ) from error
                evidence["pause_submission"] = submission
                pause_deadline = time.monotonic() + 5.0
                while time.monotonic() < pause_deadline:
                    snapshot = service.snapshot()
                    if snapshot.get("paused") is True:
                        break
                    time.sleep(0.05)
            if snapshot.get("paused") is not True:
                evidence["failure_reason"] = (
                    "native MCP did not freeze timeline after fixture marker"
                )
                write_json(evidence_path, evidence)
                raise acceptance.RunnerError(str(evidence["failure_reason"]))
            evidence["result"] = "GREEN" if count == 1 else "RED"
            evidence["marker_count"] = count
            evidence["terminal_snapshot"] = _personal_switch_native_snapshot(
                snapshot
            )
            evidence["failure_reason"] = (
                None if count == 1 else f"fixture marker count is {count}, expected 1"
            )
            write_json(evidence_path, evidence)
            if count != 1:
                raise acceptance.RunnerError(str(evidence["failure_reason"]))
            return evidence

        snapshot = service.snapshot()
        observation = _personal_switch_native_snapshot(snapshot)
        active_event_id = observation["active_event_instance_id"]
        if isinstance(active_event_id, int) and not isinstance(
            active_event_id, bool
        ):
            evidence["failure_reason"] = (
                "unexpected visible event blocked fixture marker wait; "
                "query it through the native event path before continuing"
            )
            evidence["terminal_snapshot"] = observation
            write_json(evidence_path, evidence)
            raise acceptance.RunnerError(str(evidence["failure_reason"]))
        if snapshot.get("paused") is True or snapshot.get("speed") != 5:
            try:
                resume = resume_personal_switch_timeline_native(
                    service,
                    reason=f"{stem}_resume_to_fixture_marker",
                    timeout_s=min(10.0, max(1.0, deadline - time.monotonic())),
                )
            except Exception as error:
                evidence["failure_reason"] = (
                    "native timeline resume before fixture marker failed: "
                    f"{type(error).__name__}: {error}"
                )
                write_json(evidence_path, evidence)
                raise acceptance.RunnerError(str(evidence["failure_reason"])) from error
            resumes = evidence["native_resumes"]
            assert isinstance(resumes, list)
            resumes.append(resume)
        else:
            time.sleep(0.05)

    evidence["marker_count"] = stream.count(marker)
    evidence["failure_reason"] = f"fixture marker timeout: {marker}"
    write_json(evidence_path, evidence)
    raise acceptance.RunnerError(str(evidence["failure_reason"]))


def advance_to_personal_switch(
    stream: MarkerStream,
    artifacts: Path,
    *,
    timeline_service: GameplayBridgeService,
    due_day_ordinal: int,
    timeout_s: float = PERSONAL_SWITCH_WAIT_TIMEOUT_S,
) -> list[dict[str, object]]:
    """Advance the D+90 carrier and recover modal or silent native pauses."""

    native_resumes = [
        resume_personal_switch_timeline_native(
            timeline_service, reason="initial_post_jingcha_resume"
        )
    ]
    native_observations: list[dict[str, object]] = []
    deadline = time.monotonic() + timeout_s
    interruptions: list[dict[str, object]] = []
    recovery_round = 0

    def write_timeline_evidence(result: str) -> None:
        write_json(
            artifacts / "10_personal_switch_timeline_gate.json",
            {
                "schema_version": 1,
                "result": result,
                "due_day_ordinal": due_day_ordinal,
                "timeout_seconds": timeout_s,
                "marker_count": stream.count(PERSONAL_SWITCH_SCHEDULED_MARKER),
                "interruption_count": len(interruptions),
                "native_resumes": native_resumes,
                "native_observations": native_observations,
            },
        )

    while time.monotonic() < deadline:
        stream.pump()
        if stream.count(PERSONAL_SWITCH_SCHEDULED_MARKER):
            write_timeline_evidence("GREEN")
            return interruptions

        # Keep the complete native event identity. A one-option event is a
        # forced presentation choice and can be cleared by the exact-build MCP
        # without inferring its option number from OCR geometry.
        snapshot = timeline_service.snapshot()
        observed = _personal_switch_native_snapshot(snapshot)
        if not native_observations or observed != native_observations[-1]:
            native_observations.append(observed)
        active_event_id = observed["active_event_instance_id"]
        active_event_option_count = observed["active_event_option_count"]

        recovery_round += 1
        recovered = settle_promo_interruptions(
            artifacts,
            f"10_personal_switch_wait_{recovery_round:02d}",
            observation_s=0.5,
            native_event_service=timeline_service,
            native_active_event_instance_id=active_event_id,
            native_active_event_option_count=active_event_option_count,
            stop_event_title="上司考定",
        )
        if recovered:
            interruptions.extend(recovered)

        # A hidden carrier can publish the target while the interruption OCR is
        # observing the screen. Never resume through that newly-arrived event.
        stream.pump()
        if stream.count(PERSONAL_SWITCH_SCHEDULED_MARKER):
            write_timeline_evidence("GREEN")
            return interruptions

        snapshot = timeline_service.snapshot()
        observed = _personal_switch_native_snapshot(snapshot)
        if not native_observations or observed != native_observations[-1]:
            native_observations.append(observed)
        active_event_id = observed["active_event_instance_id"]
        if (
            (snapshot.get("paused") is True or snapshot.get("speed") != 5)
            and active_event_id is None
        ):
            native_resumes.append(
                resume_personal_switch_timeline_native(
                    timeline_service,
                    reason=(
                        "dismissed_interruption" if recovered else "silent_pause"
                    ),
                )
            )
        else:
            time.sleep(0.2)
    write_timeline_evidence("RED")
    raise acceptance.RunnerError(
        "fixture personal-result switch did not arrive after the delayed "
        "post-Jingcha timeline advance"
    )


def capture_superior_assigned_result(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
    *,
    timeline_service: GameplayBridgeService,
    personal_switch_due_day_ordinal: int,
) -> dict[str, object]:
    # The external fixture schedules only the player-character switch. The
    # former player then becomes the real AI superior and invokes the product
    # review, grade, snapshot and result-event chain.
    switch_interruptions = advance_to_personal_switch(
        stream,
        artifacts,
        timeline_service=timeline_service,
        due_day_ordinal=personal_switch_due_day_ordinal,
    )
    stream.wait(HISTORICAL_TARGET_DATA_MARKER_PREFIX, 30)
    stream.wait(HISTORICAL_TARGET_PASS_MARKER, 30)
    reviewed_history_id = resolved_historical_personal_result_target(stream)
    if stream.count(HISTORICAL_TARGET_PASS_MARKER) != 1:
        raise acceptance.RunnerError(
            "historical personal-result target PASS marker must occur exactly once"
        )
    if recorder:
        recorder.resolve_reviewed_subject(reviewed_history_id)
    stream.wait(
        "ZGA: TEST PASS personal_result_target_projected_bottom_two", 30
    )
    stream.wait(
        "ZGA: TEST PASS jingcha_refusal_superior_opinion_and_kpi_minus_50", 30
    )
    stream.wait("ZGA: TEST PASS superior_assigned_player_grade", 30)
    stream.wait(
        "ZGA: TEST PASS phase2_player_325_prepared_without_early_penalty", 30
    )
    stream.wait(
        "ZGA: TEST PASS refusal_reason_consumed_once_by_original_superior", 30
    )
    if stream.count("ZGA: TEST PASS superior_assigned_player_grade") != 1:
        raise acceptance.RunnerError(
            "superior-assigned player grade marker must occur exactly once"
        )

    # Phase-two delivery is navigated exclusively through the exact-build
    # event-window MCP. First bind the prepared notice, then choose refusal by
    # resolved option text and independent typed ACK. OCR is not consulted.
    notice_gate = wait_for_native_event_definition(
        timeline_service,
        artifacts,
        stem="10_phase2_325_notice",
        expected_event_definition_key="zg361.50",
        timeout_s=30.0,
    )
    result_case_snapshot_live_cell = (
        accept_zhongguo_result_case_snapshot_v1_live_cell(
            timeline_service,
            artifacts,
            notice_identity=notice_gate["identity"],
            paused_snapshot=notice_gate["snapshot"],
        )
    )
    notice_speed_gate = arm_native_speed_one(
        timeline_service,
        artifacts,
        stem="10_phase2_325_notice_refusal",
        require_settled_revision=True,
    )
    notice_selection = select_resolved_event_option_native(
        timeline_service,
        artifacts,
        notice_speed_gate["snapshot"],
        stem="10_phase2_325_notice_refusal",
        expected_event_definition_key="zg361.50",
        expected_option_text="拒绝签收",
    )
    notice_transition = pause_after_promo_event_click(
        timeline_service,
        artifacts,
        notice_speed_gate["snapshot"],
        stem="10_phase2_325_notice_refusal",
        expected_predecessor_event_key="zg361.50",
    )

    # Seven days later the hidden witness effect settles the same receipt; the
    # visible personal result is the next canonical product event. This event
    # identity, not its pixels, is the L1 navigation/state boundary.
    result_gate = wait_for_native_event_definition(
        timeline_service,
        artifacts,
        stem="10_phase2_witnessed_result",
        expected_event_definition_key="zg361.4",
        timeout_s=30.0,
    )

    # OCR below is final visual evidence only, after MCP has already proved the
    # canonical event and completed the refusal action/ACK path.
    acceptance.wait_for_ocr_text(
        "上司考定",
        PROMO_EVENT_TITLE_REGION,
        30,
        artifacts,
        "10_superior_result_title.png",
        contains=True,
        stable_hits=1,
    )
    rendered_text = acceptance.wait_for_ocr_tokens(
        ("上司考定", "你的绩效", "KPI", "同组位次"),
        ("zg361_", "topscope", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "10_superior_result",
    )
    performance_field_text = acceptance.wait_for_ocr_tokens(
        ("你的绩效", "3.25"),
        ("3.75", "3.5", "zg361_", "topscope", "localize", "error"),
        PROMO_PERSONAL_RESULT_FIELD_REGION,
        15,
        artifacts,
        "10_superior_result_performance_field",
    )
    if recorder:
        recorder.mark("superior_assigned_325_visible")
        recorder.clean_hold("superior_assigned_325", artifacts, 3.5)

    # Close the result through the same typed event MCP, then advance only far
    # enough for the D+8 fixture read-oracle to verify witnessed settlement and
    # retry idempotence. Freeze before the existing policy chain can dispatch.
    result_speed_gate = arm_native_speed_one(
        timeline_service,
        artifacts,
        stem="10_phase2_result_accept",
        require_settled_revision=True,
    )
    result_selection = select_resolved_event_option_native(
        timeline_service,
        artifacts,
        result_speed_gate["snapshot"],
        stem="10_phase2_result_accept",
        expected_event_definition_key="zg361.4",
        expected_option_text="认命",
    )
    result_transition = pause_after_promo_event_click(
        timeline_service,
        artifacts,
        result_speed_gate["snapshot"],
        stem="10_phase2_result_accept",
        expected_predecessor_event_key="zg361.4",
    )
    refused_settlement_gate = wait_for_fixture_marker_native(
        stream,
        timeline_service,
        artifacts,
        stem="10_phase2_refused_settlement",
        marker="ZGA: TEST PASS phase2_refused_notice_witnessed_and_settled",
        timeout_s=20.0,
    )
    stream.wait(
        "ZGA: TEST PASS phase2_refused_delivery_receipt_idempotent", 5
    )
    stream.wait("ZGA: TEST PASS clean_policy_chain_scheduled", 5)
    return {
        "real_superior_review_path": True,
        "reviewed_official_history_id": reviewed_history_id,
        "historical_target_data_marker_count": stream.count(
            HISTORICAL_TARGET_DATA_MARKER_PREFIX
        ),
        "historical_target_pass_marker_count": stream.count(
            HISTORICAL_TARGET_PASS_MARKER
        ),
        "projected_bottom_two_marker_count": stream.count(
            "ZGA: TEST PASS personal_result_target_projected_bottom_two"
        ),
        "clean_policy_chain_scheduled_marker_count": stream.count(
            "ZGA: TEST PASS clean_policy_chain_scheduled"
        ),
        "preempting_product_events_dismissed": (
            notice_gate["evidence"]["cleared_single_option_interruptions"]
            + result_gate["evidence"]["cleared_single_option_interruptions"]
        ),
        "timeline_interruptions_before_switch": switch_interruptions,
        "phase2_mcp_first_delivery": {
            "prepared_without_early_penalty_marker_count": stream.count(
                "ZGA: TEST PASS phase2_player_325_prepared_without_early_penalty"
            ),
            "notice_identity": notice_gate["identity"],
            "result_case_snapshot_v1_live_cell": (
                result_case_snapshot_live_cell
            ),
            "refusal_option_selection": notice_selection,
            "refusal_transition": notice_transition,
            "witnessed_result_identity": result_gate["identity"],
            "result_option_selection": result_selection,
            "result_transition": result_transition,
            "witnessed_settlement_marker_gate": refused_settlement_gate,
            "witnessed_settlement_marker_count": stream.count(
                "ZGA: TEST PASS phase2_refused_notice_witnessed_and_settled"
            ),
            "refused_receipt_idempotence_marker_count": stream.count(
                "ZGA: TEST PASS phase2_refused_delivery_receipt_idempotent"
            ),
            "ocr_used_for_navigation_or_green": False,
            "visual_evidence_captured_after_native_identity": True,
        },
        "rendered_grade": "3.25",
        "performance_field_ocr_artifact": (
            "10_superior_result_performance_field_ocr.json"
        ),
        "normalized_performance_field_ocr": performance_field_text,
        "title_artifact": "10_superior_result_title.png",
        "panel_artifact": "10_superior_result.png",
        "panel_ocr_artifact": "10_superior_result_ocr.json",
        "normalized_ocr": rendered_text,
    }


def arm_native_speed_one(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    stem: str,
    require_settled_revision: bool = False,
) -> dict[str, object]:
    """Queue speed one while binding the click to the same native modal."""

    starting = service.snapshot()
    starting_observation = _personal_switch_native_snapshot(starting)
    starting_event = starting_observation["active_event_instance_id"]
    starting_date = starting_observation["date_raw"]
    starting_character = starting.get("played_character")
    starting_character_id = (
        starting_character.get("character_id")
        if isinstance(starting_character, dict)
        else None
    )
    precondition_valid = (
        isinstance(starting_event, int)
        and not isinstance(starting_event, bool)
        and isinstance(starting_date, int)
        and not isinstance(starting_date, bool)
        and isinstance(starting_character_id, int)
        and not isinstance(starting_character_id, bool)
    )
    if not precondition_valid:
        evidence = {
            "schema_version": 1,
            "result": "RED",
            "failure_reason": "native modal identity/date/character is incomplete",
            "starting_observation": starting_observation,
            "starting_character_id": starting_character_id,
        }
        write_json(artifacts / f"{stem}_speed_one_gate.json", evidence)
        acceptance.ImageGrab.grab().save(
            artifacts / f"red_{stem}_speed_one_precondition.png"
        )
        raise acceptance.RunnerError(
            "native MCP cannot bind speed one to the visible promo event"
        )
    submission = service.execute_step("set-speed-1")
    submission_confirmed = (
        isinstance(submission, dict)
        and submission.get("accepted") is True
        and submission.get("status") == "submitted"
    )
    observations: list[dict[str, object]] = []
    context_failure = ""
    settled_revision_observed = False
    settle_deadline = time.monotonic() + (1.5 if require_settled_revision else 0.0)
    while True:
        snapshot = service.snapshot()
        observed = _personal_switch_native_snapshot(snapshot)
        observations.append(observed)
        character = snapshot.get("played_character")
        character_id = (
            character.get("character_id") if isinstance(character, dict) else None
        )
        if observed["date_raw"] != starting_date:
            context_failure = "game date changed while arming speed one"
        elif observed["active_event_instance_id"] != starting_event:
            context_failure = "active event changed while arming speed one"
        elif character_id != starting_character_id:
            context_failure = "played character changed while arming speed one"
        if context_failure:
            break
        settled_revision_observed = (
            snapshot.get("revision") != starting.get("revision")
            and snapshot.get("paused") is True
        )
        if not require_settled_revision or settled_revision_observed:
            break
        if time.monotonic() >= settle_deadline:
            context_failure = (
                "speed one submission did not reach a new paused revision"
            )
            break
        time.sleep(0.05)

    # A CK3 character event can stop map progression without projecting that
    # modal stop through Jomini's ordinary paused/speed fields.  The command
    # ACK plus the unchanged event/date/character bind the subsequent click;
    # the post-click same-date freeze is the authoritative safety gate.
    armed = (
        submission_confirmed
        and not context_failure
        and (not require_settled_revision or settled_revision_observed)
    )
    evidence = {
        "schema_version": 1,
        "result": "GREEN" if armed else "RED",
        "starting_observation": starting_observation,
        "starting_character_id": starting_character_id,
        "submission": submission,
        "submission_confirmed": submission_confirmed,
        "observations": observations,
        "settled_revision_required": require_settled_revision,
        "settled_revision_observed": settled_revision_observed,
        "speed_one_observed_pre_click": snapshot.get("speed") == 1,
        "paused_observed_pre_click": snapshot.get("paused"),
        "modal_context_stable": not context_failure,
        "failure_reason": (
            context_failure
            or (None if submission_confirmed else "speed one submission was not accepted")
        ),
    }
    write_json(artifacts / f"{stem}_speed_one_gate.json", evidence)
    if evidence["result"] != "GREEN":
        acceptance.ImageGrab.grab().save(
            artifacts / f"red_{stem}_speed_one_gate.png"
        )
        raise acceptance.RunnerError(
            "native MCP could not bind speed one to the same promo event/date"
        )
    return {
        **evidence,
        "snapshot": snapshot,
    }


def pause_after_promo_event_click(
    service: GameplayBridgeService,
    artifacts: Path,
    pre_click_snapshot: dict[str, object],
    *,
    stem: str,
    expected_predecessor_event_key: str,
) -> dict[str, object]:
    """Freeze an event-restored clock before its next clean carrier wins."""

    if not isinstance(expected_predecessor_event_key, str) or not (
        expected_predecessor_event_key.strip()
    ):
        raise ValueError("expected_predecessor_event_key must be non-empty")

    pre_observation = _personal_switch_native_snapshot(pre_click_snapshot)
    pre_event = pre_observation["active_event_instance_id"]
    pre_date = pre_observation["date_raw"]
    pre_character = pre_click_snapshot.get("played_character")
    pre_character_id = (
        pre_character.get("character_id")
        if isinstance(pre_character, dict)
        else None
    )
    transition_observations: list[dict[str, object]] = []
    transition_deadline = time.monotonic() + 0.75
    running_transition_seen = False
    event_transition_seen = False
    transition_failure = ""
    transition_snapshot = pre_click_snapshot
    while time.monotonic() < transition_deadline:
        transition_snapshot = service.snapshot()
        observed = _personal_switch_native_snapshot(transition_snapshot)
        transition_observations.append(observed)
        if observed["date_raw"] != pre_date:
            transition_failure = "game date advanced before native pause submission"
            break
        if observed["active_event_instance_id"] != pre_event:
            event_transition_seen = True
            running_transition_seen = transition_snapshot.get("paused") is False
            break
        time.sleep(0.01)
    if not event_transition_seen and not transition_failure:
        transition_failure = (
            "event close did not change the native event instance within 0.75s"
        )

    # Only a same-date, changed-event running frame authorizes pause-map.  A
    # failed transition may still receive a best-effort containment pause when
    # the underlying map is running, but it can never turn the gate GREEN.
    should_submit_pause = transition_snapshot.get("paused") is False
    pause_submission = (
        service.execute_step("pause-map")
        if should_submit_pause
        else {
            "step": "pause-map",
            "accepted": True,
            "status": "not_needed_already_paused",
        }
    )
    pause_submitted = (
        isinstance(pause_submission, dict)
        and pause_submission.get("accepted") is True
        and pause_submission.get("status") == "submitted"
    )
    already_paused_after_instance_transition = (
        event_transition_seen
        and transition_snapshot.get("paused") is True
        and pause_submission.get("status") == "not_needed_already_paused"
    )
    pause_observations: list[dict[str, object]] = []
    pause_deadline = time.monotonic() + 5.0
    paused_snapshot: dict[str, object] = {}
    frozen = False
    while time.monotonic() < pause_deadline:
        paused_snapshot = service.snapshot()
        pause_observations.append(_personal_switch_native_snapshot(paused_snapshot))
        tail = pause_observations[-3:]
        frozen = (
            len(tail) == 3
            and all(item["paused"] is True for item in tail)
            and all(item["date_raw"] == pre_date for item in tail)
        )
        if frozen:
            break
        time.sleep(0.1)

    post_character = paused_snapshot.get("played_character")
    post_character_id = (
        post_character.get("character_id")
        if isinstance(post_character, dict)
        else None
    )
    played_character_stable = (
        isinstance(pre_character_id, int)
        and not isinstance(pre_character_id, bool)
        and post_character_id == pre_character_id
    )
    instance_transitioned = (
        bool(pause_observations)
        and pause_observations[-1]["active_event_instance_id"] != pre_event
    )
    definition_query: dict[str, object] | None = None
    definition_query_error: str | None = None
    observed_successor_event_key: str | None = None
    definition_transitioned = False
    post_event_id = (
        pause_observations[-1]["active_event_instance_id"]
        if pause_observations
        else None
    )
    # CK3 can replace one event definition with the next while retaining the
    # same published window instance ID (zg361m.1 -> zg361.6 does this in the
    # exact 1.19.0.6 build).  Only the existing typed event-window MCP may
    # prove that same-ID transition; generic revision, option count, OCR, or a
    # successful pause alone are not event identity.
    if frozen and post_event_id == pre_event and isinstance(post_event_id, int):
        try:
            definition_identity = query_event_definition_identity(
                service, paused_snapshot
            )
            definition_query = definition_identity["query"]
            observed_key = definition_identity["event_definition_key"]
            observed_successor_event_key = observed_key
            definition_transitioned = (
                observed_key != expected_predecessor_event_key
            )
        except Exception as error:
            definition_query_error = f"{type(error).__name__}: {error}"
    event_transitioned = instance_transitioned or definition_transitioned
    if definition_transitioned:
        transition_failure = ""
        running_transition_seen = any(
            item.get("paused") is False for item in transition_observations
        )
    already_paused_after_transition = (
        event_transitioned
        and paused_snapshot.get("paused") is True
        and pause_submission.get("status") == "not_needed_already_paused"
    )
    green = (
        event_transitioned
        and (pause_submitted or already_paused_after_transition)
        and frozen
        and played_character_stable
    )
    evidence = {
        "schema_version": 1,
        "result": "GREEN" if green else "RED",
        "pause_method": (
            "native_mcp_speed_one_then_pause_map"
            if pause_submitted
            else "native_mcp_already_paused_after_event"
        ),
        "pre_click_observation": pre_observation,
        "expected_predecessor_event_key": expected_predecessor_event_key,
        "transition_observations": transition_observations,
        "event_transition_seen_same_date": event_transitioned,
        "instance_transition_seen_same_date": event_transition_seen,
        "definition_transition_seen_same_date": definition_transitioned,
        "event_transition_identity_method": (
            "instance_id"
            if instance_transitioned
            else ("event_definition_key" if definition_transitioned else None)
        ),
        "observed_successor_event_key": observed_successor_event_key,
        "post_event_window_context_query": definition_query,
        "post_event_window_context_error": definition_query_error,
        "running_transition_seen_same_date": running_transition_seen,
        "transition_failure": transition_failure or None,
        "pause_submission": pause_submission,
        "pause_submission_confirmed": pause_submitted,
        "already_paused_after_instance_transition": (
            already_paused_after_instance_transition
        ),
        "already_paused_after_event_transition": already_paused_after_transition,
        "post_close_speed_one_observed": (
            transition_snapshot.get("speed") == 1 if event_transitioned else None
        ),
        "pause_observations": pause_observations,
        "last_three_dates_identical": frozen,
        "last_three_paused_at_pre_click_date": frozen,
        "event_transitioned": event_transitioned,
        "played_character_stable": played_character_stable,
    }
    evidence_path = artifacts / f"{stem}_immediate_pause_gate.json"
    write_json(evidence_path, evidence)
    if evidence["result"] != "GREEN":
        acceptance.ImageGrab.grab().save(
            artifacts / f"red_{stem}_native_pause.png"
        )
        raise acceptance.RunnerError(
            f"native MCP did not freeze the promo-event clock safely ({stem})"
        )
    return evidence


def capture_received_scoreboard(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder,
    *,
    timeline_service: GameplayBridgeService,
) -> dict[str, object]:
    # capture_superior_assigned_result already closed zg361.4 through the typed
    # event MCP and froze the timeline after the D+8 refusal verifier. This step
    # is now display-only and must never navigate phase-two state through OCR.
    pause_evidence = {
        "result": "GREEN",
        "selection_method": "native_mcp_completed_before_received_board",
        "ocr_used_for_navigation_or_green": False,
    }
    stream.pump()
    early_policy_count = stream.count("ZGA: TEST PASS clean_policy_001_dispatched")
    pause_evidence["early_policy_001_marker_count"] = early_policy_count
    if early_policy_count != 0:
        pause_evidence["result"] = "RED"
        pause_evidence["failure_reason"] = (
            "policy card 001 dispatched before received-scoreboard capture"
        )
    write_json(
        artifacts / "11_received_result_immediate_pause_gate.json", pause_evidence
    )
    if early_policy_count != 0:
        raise acceptance.RunnerError(
            "policy card 001 preempted the received-scoreboard capture"
        )
    isolated.wait_for_gameplay_hud(artifacts)
    settle_promo_interruptions(artifacts, "11_received_before_board")
    button = acceptance.wait_for_ocr_text(
        "考核榜",
        SCOREBOARD_BUTTON_REGION,
        20,
        artifacts,
        "11_received_scoreboard_button.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(button, "open received performance board")
    # A native event can already be queued while the result event is closing.
    # Observe again after the board opens so a late event is dismissed while
    # the intended board remains underneath it.
    settle_promo_interruptions(
        artifacts,
        "11_received_after_board_open",
        observation_s=2.5,
    )
    rendered_text = acceptance.wait_for_ocr_tokens(
        ("天朝官员考核榜", "本人所属考核单元", "3.25"),
        ("zg361_", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "11_received_scoreboard",
    )
    recorder.mark("received_scoreboard_with_325_visible")
    recorder.clean_hold("received_scoreboard_with_325", artifacts, 3.0)
    # This historical official has a received scoreboard but does not inherit
    # the emperor's mechanism ledger. Exercise the distinct received-tab button
    # in-place (an intentional idempotent click) without assuming the system tab
    # is available on this character.
    received_tab = acceptance.wait_for_ocr_text(
        "本人所属考核单元",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "11_received_tab_button.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(
        received_tab, "received performance-board tab blocker audit"
    )
    acceptance.wait_for_ocr_tokens(
        ("天朝官员考核榜", "本人所属考核单元", "3.25"),
        ("zg361_", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "11_received_tab_reopened",
    )
    settle_promo_interruptions(artifacts, "11_received_before_close")
    close_scoreboard_panel(artifacts, "11_received")
    settle_promo_interruptions(artifacts, "11_received_after_close")
    acceptance.ensure_game_paused(artifacts, "11_received_policy_setup")
    return {
        "received_panel_artifact": "11_received_scoreboard.png",
        "received_tab_clicked_live": True,
        "received_tab_idempotent_reopen_live": True,
        "received_tab_reopened_artifact": "11_received_tab_reopened.png",
        "result_close_pause_gate": pause_evidence,
        "normalized_ocr": rendered_text,
    }


def promo_event_modal_evidence(
    items: list[dict[str, object]], width: int, height: int
) -> bool:
    """Require both a title and narrative body before treating UI as an event.

    The performance board itself has lower rows in the same lane as classic
    event options.  Requiring a wide narrative line in the event body keeps the
    generic option ranker from ever clicking an ordinary board row.
    """
    title = any(
        # CK3 character-event titles occupy the left half of the classic
        # modal. The centered performance-board and cockpit headings must not
        # satisfy this test even though they also have long explanatory text.
        PROMO_EVENT_TITLE_REGION[0]
        <= item["center"][0] / width
        < PROMO_EVENT_TITLE_REGION[2]
        and PROMO_EVENT_TITLE_REGION[1]
        <= item["center"][1] / height
        <= PROMO_EVENT_TITLE_REGION[3]
        and (item["bbox"][2] - item["bbox"][0]) / width >= 0.055
        for item in items
    )
    narrative = any(
        0.20 <= item["center"][0] / width <= 0.76
        and 0.27 <= item["center"][1] / height <= 0.58
        and (item["bbox"][2] - item["bbox"][0]) / width >= 0.10
        for item in items
    )
    return title and narrative


def promo_event_title_evidence(
    items: list[dict[str, object]],
    width: int,
    height: int,
    expected_title: str,
) -> bool:
    """Prove the expected event title is visibly on top, not in pause text."""

    expected = _normalize_promo_visible_text(expected_title)
    return bool(expected) and any(
        PROMO_EVENT_TITLE_REGION[0]
        <= item["center"][0] / width
        <= PROMO_EVENT_TITLE_REGION[2]
        and PROMO_EVENT_TITLE_REGION[1]
        <= item["center"][1] / height
        <= PROMO_EVENT_TITLE_REGION[3]
        and expected
        in _normalize_promo_visible_text(str(item.get("text", "")))
        for item in items
    )


def promo_preferred_product_event_option(
    items: list[dict[str, object]],
    width: int,
    height: int,
) -> tuple[str | None, dict[str, object] | None]:
    """Select an explicit continuity-preserving option for a known event."""

    for event_title, option_text in PROMO_PREFERRED_PRODUCT_EVENT_OPTIONS:
        if not promo_event_title_evidence(items, width, height, event_title):
            continue
        expected = _normalize_promo_visible_text(option_text)
        matches = [
            item
            for item in items
            if 0.18 <= item["center"][0] / width <= 0.75
            and 0.55 <= item["center"][1] / height <= 0.85
            and expected
            in _normalize_promo_visible_text(str(item.get("text", "")))
        ]
        if len(matches) != 1:
            return event_title, None
        return event_title, matches[0]
    return None, None


def promo_product_event_overlay_evidence(
    label: str,
    items: list[dict[str, object]],
    width: int,
    height: int,
) -> bool:
    """Reject event-shaped UI over the otherwise clean native planner span."""

    return label == "free_jingcha_planner" and promo_event_modal_evidence(
        items, width, height
    )


def _write_promo_interruption_decision(
    artifacts: Path,
    stem: str,
    *,
    status: str,
    kind: str | None,
    selected: dict[str, object] | None,
    native_active_event_instance_id: int | None = None,
    native_event_definition_key: str | None = None,
    selection_method: str | None = None,
) -> None:
    write_json(
        artifacts / f"{stem}_decision.json",
        {
            "schema_version": 1,
            "scope": "promo_fixture_only",
            "status": status,
            "recovery_kind": kind,
            "selected_text": selected.get("text") if selected else None,
            "selected_center": selected.get("center") if selected else None,
            "allow_succession": False,
            "native_active_event_instance_id": native_active_event_instance_id,
            "native_event_definition_key": native_event_definition_key,
            "selection_method": selection_method,
        },
    )


def settle_promo_interruptions(
    artifacts: Path,
    stem: str,
    *,
    observation_s: float = PROMO_INTERRUPTION_DEFAULT_OBSERVE_S,
    max_dismissals: int = PROMO_INTERRUPTION_MAX_DISMISSALS,
    stop_event_title: str | None = None,
    stop_event_definition_key: str | None = None,
    native_event_service: GameplayBridgeService | None = None,
    native_active_event_instance_id: int | None = None,
    native_active_event_option_count: int | None = None,
) -> list[dict[str, object]]:
    """Conservatively settle bounded native events in the promo fixture only.

    Every actual or rejected recovery gets a full screenshot, OCR JSON,
    annotated candidate image, and decision sidecar.  Succession is always
    blocked.  Event-like UI without a strongly classified option is an
    immediate RED; non-event UI is merely observed and never clicked.
    """
    if max_dismissals < 1:
        raise ValueError("max_dismissals must be positive")
    if stop_event_definition_key is not None:
        if not stop_event_definition_key.strip():
            raise ValueError("stop_event_definition_key must be non-empty")
        if native_event_service is None:
            raise ValueError(
                "stop_event_definition_key requires native_event_service"
            )
    deadline = time.monotonic() + max(0.0, observation_s)
    dismissed: list[dict[str, object]] = []
    while True:
        acceptance.focus_ck3()
        image = acceptance.ImageGrab.grab()
        items = acceptance.ocr_box_results(
            image, acceptance.FULL_SCREEN_REGION
        )
        width, height = image.size
        event_modal_visible = promo_event_modal_evidence(items, width, height)
        visual_stop_match = bool(
            stop_event_title
            and promo_event_title_evidence(items, width, height, stop_event_title)
        )
        native_identity: dict[str, object] | None = None
        native_identity_error: str | None = None
        if native_event_service is not None and (
            event_modal_visible or visual_stop_match
        ):
            try:
                pause_gate = pause_bound_native_event_for_definition_query(
                    native_event_service,
                    artifacts,
                    stem=f"{stem}_event_definition_identity",
                )
                native_identity = query_event_definition_identity(
                    native_event_service,
                    pause_gate["snapshot"],
                )
            except Exception as error:
                native_identity_error = f"{type(error).__name__}: {error}"
                if stop_event_definition_key is not None:
                    diagnostic = f"{stem}_event_definition_identity_unavailable"
                    acceptance.mark_recovery_items(items, [], None)
                    acceptance.write_recovery_bundle(
                        image, items, artifacts, diagnostic
                    )
                    _write_promo_interruption_decision(
                        artifacts,
                        diagnostic,
                        status="blocked_event_definition_identity_unavailable",
                        kind=None,
                        selected=None,
                        selection_method="native_mcp_event_definition",
                    )
                    write_json(
                        artifacts / f"{diagnostic}_gate.json",
                        {
                            "schema_version": 1,
                            "result": "RED",
                            "expected_event_definition_key": (
                                stop_event_definition_key
                            ),
                            "error": native_identity_error,
                        },
                    )
                    raise acceptance.RunnerError(
                        "native MCP could not identify the expected promo event"
                    ) from error

        observed_definition_key = (
            native_identity.get("event_definition_key")
            if native_identity is not None
            else None
        )
        native_stop_match = (
            event_modal_visible
            and stop_event_definition_key is not None
            and observed_definition_key == stop_event_definition_key
        )
        if stop_event_definition_key is not None and visual_stop_match and not (
            native_stop_match
        ):
            diagnostic = f"{stem}_event_definition_identity_mismatch"
            acceptance.mark_recovery_items(items, [], None)
            acceptance.write_recovery_bundle(image, items, artifacts, diagnostic)
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_event_definition_identity_mismatch",
                kind=stop_event_title,
                selected=None,
                native_active_event_instance_id=(
                    native_identity.get("event_instance_id")
                    if native_identity is not None
                    else None
                ),
                native_event_definition_key=(
                    observed_definition_key
                    if isinstance(observed_definition_key, str)
                    else None
                ),
                selection_method="native_mcp_event_definition",
            )
            raise acceptance.RunnerError(
                "visible promo target did not match its canonical event definition"
            )
        if native_stop_match or (
            stop_event_definition_key is None and visual_stop_match
        ):
            image.save(artifacts / f"{stem}_target_event_visible.png")
            if native_stop_match:
                write_json(
                    artifacts / f"{stem}_target_event_identity_gate.json",
                    {
                        "schema_version": 1,
                        "result": "GREEN",
                        "identity_method": "event_definition_key",
                        "visual_title_match": visual_stop_match,
                        "expected_event_definition_key": (
                            stop_event_definition_key
                        ),
                        "observed_event_definition_key": observed_definition_key,
                        "identity": native_identity,
                    },
                )
            return dismissed
        protected_title = next(
            (
                title
                for title in PROMO_PROTECTED_EVENT_TITLES
                if title != stop_event_title
                and promo_event_title_evidence(items, width, height, title)
            ),
            None,
        )
        protected_definition_key = (
            observed_definition_key
            if observed_definition_key
            in {f"zg361m.{mechanism_id}" for mechanism_id, *_ in PROMO_POLICY_CARDS}
            and observed_definition_key != stop_event_definition_key
            else None
        )
        if protected_title is not None or protected_definition_key is not None:
            diagnostic = f"{stem}_protected_target_event"
            acceptance.mark_recovery_items(items, [], None)
            acceptance.write_recovery_bundle(image, items, artifacts, diagnostic)
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_protected_target_event",
                kind=(
                    protected_title
                    if protected_title is not None
                    else str(protected_definition_key)
                ),
                selected=None,
                native_active_event_instance_id=(
                    native_identity.get("event_instance_id")
                    if native_identity is not None
                    else None
                ),
                native_event_definition_key=(
                    protected_definition_key
                    if isinstance(protected_definition_key, str)
                    else None
                ),
                selection_method=(
                    "native_mcp_event_definition"
                    if protected_definition_key is not None
                    else None
                ),
            )
            raise acceptance.RunnerError(
                "protected promo target surfaced outside its capture step: "
                f"{protected_title or protected_definition_key}"
            )

        preferred_event, preferred_selected = promo_preferred_product_event_option(
            items, width, height
        )
        preferred_option_text = next(
            (
                configured_option
                for configured_title, configured_option
                in PROMO_PREFERRED_PRODUCT_EVENT_OPTIONS
                if configured_title == preferred_event
            ),
            None,
        )
        lower, selected = acceptance.select_stall_recovery(
            items, image, allow_succession=False
        )
        if preferred_event is not None:
            if preferred_selected is None:
                diagnostic = f"{stem}_known_event_safe_option_missing"
                acceptance.mark_recovery_items(items, lower, None)
                acceptance.write_recovery_bundle(
                    image, items, artifacts, diagnostic
                )
                _write_promo_interruption_decision(
                    artifacts,
                    diagnostic,
                    status="blocked_known_event_safe_option_missing",
                    kind=preferred_event,
                    selected=None,
                )
                raise acceptance.RunnerError(
                    "known promo product event lacks its non-destructive option: "
                    f"{preferred_event}"
                )
            selected = preferred_selected
        succession_lower: list[dict[str, object]] = []
        succession = None
        if selected is None:
            succession_lower, succession = acceptance.select_stall_recovery(
                items, image, allow_succession=True
            )
        if (
            succession is not None
            and succession.get("layout_fallback") == "succession_continue"
        ):
            diagnostic = f"{stem}_interruption_blocked_succession"
            acceptance.mark_recovery_items(
                items, succession_lower, None
            )
            acceptance.write_recovery_bundle(
                image, items, artifacts, diagnostic
            )
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_succession",
                kind="succession_continue",
                selected=None,
            )
            raise acceptance.RunnerError(
                "promo interruption is succession; automatic continuation is forbidden"
            )

        kind = (
            "promo_preferred_product_option"
            if preferred_event is not None and selected is not None
            else (
                acceptance.quick_recovery_kind(items, selected, width, height)
                if selected is not None
                else None
            )
        )
        native_single_option_candidate = (
            native_event_service is not None
            and isinstance(native_active_event_instance_id, int)
            and not isinstance(native_active_event_instance_id, bool)
            and native_active_event_option_count == 1
            and kind is not None
        )
        native_visual_identity_candidate = (
            native_event_service is not None
            and event_modal_visible
            and native_identity is not None
            and not native_single_option_candidate
            and kind is not None
        )
        if (
            not event_modal_visible
            and not native_single_option_candidate
        ):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return dismissed
            time.sleep(min(acceptance.POLL_INTERVAL_S, remaining))
            continue
        ordinal = len(dismissed) + 1
        diagnostic = f"{stem}_interruption_{ordinal:02d}"
        acceptance.mark_recovery_items(items, lower, selected)
        acceptance.write_recovery_bundle(image, items, artifacts, diagnostic)
        if selected is None or kind is None:
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_unknown_modal",
                kind=kind,
                selected=selected,
            )
            raise acceptance.RunnerError(
                "promo interruption looks like an event but has no safe option; "
                f"inspect {diagnostic}.png"
            )
        if len(dismissed) >= max_dismissals:
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_dismissal_limit",
                kind=kind,
                selected=selected,
            )
            raise acceptance.RunnerError(
                f"promo interruption exceeded {max_dismissals} bounded dismissals"
            )

        native_visual_speed_gate: dict[str, object] | None = None
        if native_visual_identity_candidate:
            native_visual_speed_gate = arm_native_speed_one(
                native_event_service,
                artifacts,
                stem=f"{diagnostic}_native_visual",
                # set-speed-1 itself advances the public native revision.  The
                # paused event query below must bind the post-command frame for
                # every multi-option interruption, including vanilla events
                # that have no configured preferred text.
                require_settled_revision=True,
            )
            refreshed_identity = query_event_definition_identity(
                native_event_service,
                native_visual_speed_gate["snapshot"],
            )
            if (
                refreshed_identity["event_instance_id"]
                != native_identity["event_instance_id"]
                or refreshed_identity["event_definition_key"]
                != native_identity["event_definition_key"]
            ):
                write_json(
                    artifacts / f"{diagnostic}_native_visual_identity_gate.json",
                    {
                        "schema_version": 1,
                        "result": "RED",
                        "failure_reason": (
                            "event identity changed while arming speed one"
                        ),
                        "initial_identity": native_identity,
                        "refreshed_identity": refreshed_identity,
                    },
                )
                raise acceptance.RunnerError(
                    "promo interruption changed while binding its native identity"
                )
            native_identity = refreshed_identity

        selection_method = (
            "native_mcp_single_option"
            if native_single_option_candidate
            else (
                "native_mcp_resolved_product_option"
                if native_visual_identity_candidate
                and preferred_option_text is not None
                else (
                    "native_mcp_definition_identity_visual_click"
                    if native_visual_identity_candidate
                    else "visual_click"
                )
            )
        )
        _write_promo_interruption_decision(
            artifacts,
            diagnostic,
            status="selected_safe_event_option",
            kind=kind,
            selected=selected,
            native_active_event_instance_id=(
                native_active_event_instance_id
                if native_single_option_candidate
                else (
                    native_identity.get("event_instance_id")
                    if native_visual_identity_candidate
                    and native_identity is not None
                    else None
                )
            ),
            native_event_definition_key=(
                native_identity.get("event_definition_key")
                if native_visual_identity_candidate
                and native_identity is not None
                else None
            ),
            selection_method=selection_method,
        )
        native_selection_evidence = None
        if native_single_option_candidate:
            native_selection_evidence = select_single_option_interruption_native(
                native_event_service,
                artifacts,
                diagnostic,
                expected_event_instance_id=native_active_event_instance_id,
            )
        elif (
            native_visual_identity_candidate
            and preferred_option_text is not None
            and native_visual_speed_gate is not None
            and native_identity is not None
        ):
            native_selection_evidence = select_resolved_event_option_native(
                native_event_service,
                artifacts,
                native_visual_speed_gate["snapshot"],
                stem=f"{diagnostic}_native_resolved",
                expected_event_definition_key=str(
                    native_identity["event_definition_key"]
                ),
                expected_option_text=preferred_option_text,
            )
        else:
            acceptance.deliberate_click(
                tuple(selected["center"]),
                f"promo fixture interruption {kind}: {selected['text']!r}",
            )
        selected_text = selected["text"]
        selected_center = selected["center"]
        if native_visual_identity_candidate:
            option_selection_evidence = native_selection_evidence
            native_selection_evidence = pause_after_promo_event_click(
                native_event_service,
                artifacts,
                native_visual_speed_gate["snapshot"],
                stem=f"{diagnostic}_native_visual",
                expected_predecessor_event_key=str(
                    native_identity["event_definition_key"]
                ),
            )
            if option_selection_evidence is not None:
                native_selection_evidence["native_option_selection"] = (
                    option_selection_evidence
                )
            native_selection_evidence["speed_one_submission"] = (
                native_visual_speed_gate["submission"]
            )
            native_selection_evidence["speed_one_observations"] = (
                native_visual_speed_gate["observations"]
            )
            after = acceptance.ImageGrab.grab()
            after_items = acceptance.ocr_box_results(
                after, acceptance.FULL_SCREEN_REGION
            )
            repeated_visual_option = any(
                item["text"] == selected_text
                and abs(item["center"][0] - selected_center[0]) <= 30
                and abs(item["center"][1] - selected_center[1]) <= 20
                for item in after_items
            )
            after.save(artifacts / f"{diagnostic}_dismissed.png")
            dismissed.append(
                {
                    "kind": kind,
                    "selected_text": selected_text,
                    "selected_center": selected_center,
                    "diagnostic_stem": diagnostic,
                    "selection_method": selection_method,
                    "native_active_event_instance_id": native_identity.get(
                        "event_instance_id"
                    ),
                    "native_event_definition_key": native_identity.get(
                        "event_definition_key"
                    ),
                    "repeated_visual_option_after_definition_transition": (
                        repeated_visual_option
                    ),
                    "native_selection_evidence": native_selection_evidence,
                }
            )
            deadline = time.monotonic() + max(0.0, observation_s)
            continue
        close_deadline = time.monotonic() + 8
        while time.monotonic() < close_deadline:
            time.sleep(acceptance.POLL_INTERVAL_S)
            after = acceptance.ImageGrab.grab()
            after_items = acceptance.ocr_box_results(
                after, acceptance.FULL_SCREEN_REGION
            )
            still_visible = any(
                item["text"] == selected_text
                and abs(item["center"][0] - selected_center[0]) <= 30
                and abs(item["center"][1] - selected_center[1]) <= 20
                for item in after_items
            )
            if not still_visible:
                after.save(artifacts / f"{diagnostic}_dismissed.png")
                dismissed.append(
                    {
                        "kind": kind,
                        "selected_text": selected_text,
                        "selected_center": selected_center,
                        "diagnostic_stem": diagnostic,
                        "selection_method": selection_method,
                        "native_active_event_instance_id": (
                            native_active_event_instance_id
                            if native_single_option_candidate
                            else None
                        ),
                        "native_selection_evidence": native_selection_evidence,
                    }
                )
                # A second queued event can already be visible here. Its modal
                # hides CK3's top-center pause label, so prove the pause from
                # the HUD date and then let the outer loop classify that event.
                ensure_hud_date_frozen(
                    artifacts, f"{diagnostic}_dismissed"
                )
                # The caller supplied a snapshot-bound event identity. Return
                # after one native selection so the outer timeline loop pumps
                # target markers and takes a fresh instance before any further
                # event can be considered.
                if native_single_option_candidate:
                    return dismissed
                deadline = time.monotonic() + max(0.0, observation_s)
                break
        else:
            after.save(artifacts / f"timeout_{diagnostic}.png")
            raise acceptance.RunnerError(
                f"promo interruption option did not disappear: {diagnostic}"
            )


def advance_to_policy_dispatch(
    stream: MarkerStream,
    artifacts: Path,
    *,
    timeline_service: GameplayBridgeService,
    stem: str,
    dispatch_marker: str,
    target_event_title: str,
    target_event_definition_key: str,
    timeout_s: float = 60.0,
) -> list[dict[str, object]]:
    """Advance one policy carrier while clearing earlier real product events."""

    interruptions: list[dict[str, object]] = []
    native_resumes: list[dict[str, object]] = []
    native_observations: list[dict[str, object]] = []
    recovery_round = 0
    deadline = time.monotonic() + timeout_s

    def observe() -> tuple[dict[str, object], dict[str, object]]:
        snapshot = timeline_service.snapshot()
        observation = _personal_switch_native_snapshot(snapshot)
        if not native_observations or observation != native_observations[-1]:
            native_observations.append(observation)
        return snapshot, observation

    def resume_if_clear(reason: str) -> None:
        snapshot, observation = observe()
        if observation["active_event_instance_id"] is not None:
            return
        if snapshot.get("paused") is True or snapshot.get("speed") != 5:
            native_resumes.append(
                resume_personal_switch_timeline_native(
                    timeline_service,
                    reason=reason,
                )
            )

    def write_evidence(result: str) -> None:
        write_json(
            artifacts / f"{stem}_dispatch_timeline_gate.json",
            {
                "schema_version": 1,
                "result": result,
                "dispatch_marker": dispatch_marker,
                "dispatch_marker_count": stream.count(dispatch_marker),
                "target_event_definition_key": target_event_definition_key,
                "interruption_count": len(interruptions),
                "interruptions": interruptions,
                "native_resumes": native_resumes,
                "native_observations": native_observations,
            },
        )

    resume_if_clear(f"{stem}_initial_resume")
    while time.monotonic() < deadline:
        stream.pump()
        if stream.count(dispatch_marker):
            write_evidence("GREEN")
            return interruptions

        snapshot, observation = observe()
        recovery_round += 1
        recovered = settle_promo_interruptions(
            artifacts,
            f"{stem}_dispatch_wait_{recovery_round:02d}",
            observation_s=0.5,
            stop_event_title=target_event_title,
            stop_event_definition_key=target_event_definition_key,
            native_event_service=timeline_service,
            native_active_event_instance_id=observation[
                "active_event_instance_id"
            ],
            native_active_event_option_count=observation[
                "active_event_option_count"
            ],
        )
        if recovered:
            interruptions.extend(recovered)

        stream.pump()
        if stream.count(dispatch_marker):
            write_evidence("GREEN")
            return interruptions
        resume_if_clear(f"{stem}_resume_after_{recovery_round:02d}")
        time.sleep(0.1)

    write_evidence("RED")
    raise acceptance.RunnerError(
        f"policy dispatch marker did not arrive: {dispatch_marker}"
    )


def capture_policy_cards(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder,
    *,
    timeline_service: GameplayBridgeService,
) -> list[dict[str, object]]:
    captured: list[dict[str, object]] = []
    for card_index, (
        mechanism_id,
        _decision_title,
        event_title,
        option_text,
    ) in enumerate(PROMO_POLICY_CARDS):
        stem = f"12_policy_{mechanism_id:03d}"
        settle_promo_interruptions(artifacts, f"{stem}_preflight")
        acceptance.ensure_game_paused(artifacts, f"{stem}_preflight")
        dispatch_marker = (
            f"ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched"
        )
        advance_to_policy_dispatch(
            stream,
            artifacts,
            timeline_service=timeline_service,
            stem=stem,
            dispatch_marker=dispatch_marker,
            target_event_title=event_title,
            target_event_definition_key=f"zg361m.{mechanism_id}",
        )
        settle_promo_interruptions(
            artifacts,
            f"{stem}_preemption",
            observation_s=20.0,
            stop_event_title=event_title,
            stop_event_definition_key=f"zg361m.{mechanism_id}",
            native_event_service=timeline_service,
        )
        # settle_promo_interruptions has already bound this visible modal to the
        # expected canonical zg361m.N definition through the native MCP. Reuse
        # that validated frame instead of performing a weaker OCR-only wait
        # that can turn a visible card into a RED (for example 晋升 -> 普升).
        validated_event_artifact = (
            artifacts / f"{stem}_preemption_target_event_visible.png"
        )
        event_artifact = artifacts / f"{stem}_event.png"
        if not validated_event_artifact.is_file():
            raise acceptance.RunnerError(
                "normalized policy-title gate did not save its validated frame: "
                f"{validated_event_artifact}"
            )
        shutil.copy2(validated_event_artifact, event_artifact)
        screen_width, screen_height = acceptance.pyautogui.size()
        # The preceding card leaves the pointer over the same first-option
        # lane. Park it on inert narrative space so CK3 closes that tooltip
        # before the clean still and video hold.
        acceptance.pyautogui.moveTo(
            int(screen_width * 0.50), int(screen_height * 0.50), duration=0.2
        )
        time.sleep(0.5)
        acceptance.ImageGrab.grab().save(event_artifact)
        recorder.mark(f"policy_card_{mechanism_id:03d}_visible")
        recorder.clean_hold(
            f"policy_card_{mechanism_id:03d}", artifacts, 2.5
        )
        acceptance.ImageGrab.grab().save(artifacts / f"{stem}_option.png")
        speed_one_gate = arm_native_speed_one(
            timeline_service,
            artifacts,
            stem=f"{stem}_close",
            require_settled_revision=True,
        )
        pre_click_snapshot = speed_one_gate["snapshot"]
        option_selection_evidence = select_resolved_event_option_native(
            timeline_service,
            artifacts,
            pre_click_snapshot,
            stem=f"{stem}_close",
            expected_event_definition_key=f"zg361m.{mechanism_id}",
            expected_option_text=option_text,
        )
        pause_evidence = pause_after_promo_event_click(
            timeline_service,
            artifacts,
            pre_click_snapshot,
            stem=f"{stem}_close",
            expected_predecessor_event_key=f"zg361m.{mechanism_id}",
        )
        pause_evidence["native_option_selection"] = option_selection_evidence
        pause_evidence["speed_one_submission"] = speed_one_gate["submission"]
        pause_evidence["speed_one_observations"] = speed_one_gate["observations"]
        if card_index + 1 < len(PROMO_POLICY_CARDS):
            successor_id = PROMO_POLICY_CARDS[card_index + 1][0]
            successor_marker = (
                f"ZGA: TEST PASS clean_policy_{successor_id:03d}_dispatched"
            )
        else:
            successor_marker = "ZGA: TEST PASS clean_policy_chain_completed"
        stream.pump()
        successor_marker_count = stream.count(successor_marker)
        pause_evidence["premature_successor_marker"] = successor_marker
        pause_evidence["premature_successor_marker_count"] = (
            successor_marker_count
        )
        if successor_marker_count != 0:
            pause_evidence["result"] = "RED"
            pause_evidence["failure_reason"] = (
                "policy successor dispatched before predecessor capture"
            )
        write_json(
            artifacts / f"{stem}_close_immediate_pause_gate.json",
            pause_evidence,
        )
        if successor_marker_count != 0:
            raise acceptance.RunnerError(
                "policy successor preempted its predecessor capture: "
                f"{successor_marker} count={successor_marker_count}"
            )
        isolated.wait_for_gameplay_hud(artifacts)
        captured.append(
            {
                "mechanism_id": mechanism_id,
                "event_artifact": f"{stem}_event.png",
                "dispatch_marker": dispatch_marker,
                "clean_span_id": f"policy_card_{mechanism_id:03d}",
                "close_pause_gate": pause_evidence,
            }
        )
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_clean_policy_chain_completion", require_progress=True
    )
    stream.wait("ZGA: TEST PASS clean_policy_chain_completed", 30)
    acceptance.ensure_game_paused(artifacts, "12_policy_chain_completed")
    policy_markers = {
        f"{mechanism_id:03d}": stream.count(
            f"ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched"
        )
        for mechanism_id, *_ in PROMO_POLICY_CARDS
    }
    all_six_count = stream.count(
        "ZGA: TEST PASS clean_policy_chain_all_six_dispatched"
    )
    completion_count = stream.count("ZGA: TEST PASS clean_policy_chain_completed")
    if any(count != 1 for count in policy_markers.values()):
        raise acceptance.RunnerError(
            f"clean policy dispatch markers must each occur once: {policy_markers}"
        )
    if all_six_count != 1 or completion_count != 1:
        raise acceptance.RunnerError(
            "clean policy persistence markers must each occur once: "
            f"all_six={all_six_count}, completion={completion_count}"
        )
    return captured


def run_phase2_b2_result_continuation_prelude(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    baseline_binding: dict[str, int | str],
    timeout_s: float = 45.0,
    poll_interval_s: float = 0.1,
) -> dict[str, object]:
    """Reach the B2 PIP card, selecting a pending ``zg361.4`` when needed."""

    evidence_path = artifacts / "05_phase2_b2_result_continuation_prelude.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "product_only_pending_witnessed_result_continuation",
        "accepted_event_definition_keys": ["zg361.4", B2_PIP_EVENT_DEFINITION_KEY],
        "continuation_mode": None,
        "selected_option_number": 1,
        "baseline_binding": baseline_binding,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "observations": [],
        "submissions": [],
        "event_identity": None,
        "selection_submission": None,
        "selection_materialization": None,
        "post_binding": None,
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    if timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("phase-two B2 result-continuation timing is invalid")

    expected_pid = int(baseline_binding["bridge_pid"])
    expected_generation = int(baseline_binding["connection_generation"])
    expected_player = int(baseline_binding["player_character_id"])
    starting_date = int(baseline_binding["date_raw"])
    deadline = time.monotonic() + timeout_s

    def fail(reason: str) -> None:
        raise acceptance.RunnerError(reason)

    def accepted_submission(value: object, step: str) -> None:
        status = value.get("status") if isinstance(value, dict) else None
        if not (
            isinstance(value, dict)
            and value.get("accepted") is True
            and (
                status == "submitted"
                or (step == "resume-map" and status == "already_running")
                or (step == "pause-map" and status == "already_paused")
            )
        ):
            fail(f"phase-two B2 result-continuation {step} ACK was not accepted")

    def observe(snapshot: dict[str, object]) -> tuple[int, int | None]:
        revision = snapshot.get("revision")
        date_raw = snapshot.get("date_raw")
        played_character = snapshot.get("played_character")
        player = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        diagnostics = snapshot.get("diagnostics")
        pid = (
            diagnostics.get("bridge_pid")
            if isinstance(diagnostics, dict)
            else None
        )
        generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        active_event = snapshot.get("active_event")
        event_instance_id = (
            active_event.get("instance_id")
            if isinstance(active_event, dict)
            else None
        )
        observation = {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": revision,
            "native_revision": snapshot.get("native_revision"),
            "date_raw": date_raw,
            "paused": snapshot.get("paused"),
            "speed": snapshot.get("speed"),
            "player_character_id": player,
            "bridge_pid": pid,
            "connection_generation": generation,
            "active_event_instance_id": event_instance_id,
            "active_event_option_count": (
                active_event.get("option_count")
                if isinstance(active_event, dict)
                else None
            ),
        }
        observations = evidence["observations"]
        assert isinstance(observations, list)
        if not observations or observations[-1] != observation:
            observations.append(observation)
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or date_raw < starting_date
            or date_raw
            > starting_date
            + PHASE2_B2_EVENT_WAIT_MAX_DAYS * CK3_DATE_RAW_HOURS_PER_DAY
            or player != expected_player
            or pid != expected_pid
            or generation != expected_generation
            or snapshot.get("map_ready") is not True
        ):
            fail(
                "phase-two B2 result-continuation escaped its "
                "date/player/PID binding"
            )
        return revision, event_instance_id

    try:
        while time.monotonic() < deadline:
            snapshot = service.snapshot()
            if not isinstance(snapshot, dict):
                fail("phase-two B2 result-continuation snapshot is not an object")
            revision, event_instance_id = observe(snapshot)
            active_event = snapshot.get("active_event")
            if isinstance(active_event, dict):
                if snapshot.get("paused") is not True:
                    submission = service.execute_step(
                        "pause-map", expected_revision=revision
                    )
                    accepted_submission(submission, "pause-map")
                    submissions = evidence["submissions"]
                    assert isinstance(submissions, list)
                    submissions.append(submission)
                    if poll_interval_s:
                        time.sleep(poll_interval_s)
                    continue

                identity = query_event_definition_identity(service, snapshot)
                evidence["event_identity"] = identity
                observed_key = identity.get("event_definition_key")
                if observed_key == B2_PIP_EVENT_DEFINITION_KEY:
                    if active_event.get("option_count") != 3:
                        fail(
                            "phase-two B2 prompt already visible but does not "
                            "have the exact three-option product shape"
                        )
                    evidence["continuation_mode"] = "b2_prompt_already_visible"
                    evidence["post_binding"] = _phase2_paused_binding(
                        snapshot,
                        label="phase-two B2 already-visible prompt",
                    )
                    evidence["result"] = "GREEN"
                    evidence["failure_reason"] = None
                    write_json(evidence_path, evidence)
                    return evidence
                if observed_key != "zg361.4":
                    fail(
                        "phase-two B2 result-continuation encountered an "
                        f"unexpected visible event: {observed_key!r}"
                    )
                query = identity.get("query")
                context = (
                    query.get("current_event_window_context")
                    if isinstance(query, dict)
                    else None
                )
                options = context.get("options") if isinstance(context, dict) else None
                matches = [
                    row
                    for row in options or []
                    if isinstance(row, dict)
                    and row.get("native_option_index") == 0
                    and row.get("shown") is True
                    and row.get("enabled") is True
                ]
                if len(matches) != 1 or active_event.get("option_count") != 4:
                    fail(
                        "phase-two B2 result-continuation option 1 is not "
                        "uniquely available on the exact four-option card"
                    )
                if isinstance(event_instance_id, bool) or not isinstance(
                    event_instance_id, int
                ):
                    fail("phase-two B2 result-continuation lacks an event instance")
                selection = service.select_event_option(
                    1,
                    event_instance_id=event_instance_id,
                    expected_revision=revision,
                )
                accepted_submission(selection, "select-event-option-1")
                evidence["selection_submission"] = selection

                transition_deadline = min(deadline, time.monotonic() + 5.0)
                while time.monotonic() < transition_deadline:
                    after = service.snapshot()
                    if not isinstance(after, dict):
                        fail(
                            "phase-two B2 result-continuation transition snapshot "
                            "is not an object"
                        )
                    after_revision, after_event_instance = observe(after)
                    if after_event_instance != event_instance_id:
                        if after.get("paused") is not True:
                            pause = service.execute_step(
                                "pause-map", expected_revision=after_revision
                            )
                            accepted_submission(pause, "post-selection pause-map")
                            submissions = evidence["submissions"]
                            assert isinstance(submissions, list)
                            submissions.append(pause)
                            if poll_interval_s:
                                time.sleep(poll_interval_s)
                            continue
                        post_binding = _phase2_paused_binding(
                            after,
                            label="phase-two B2 result-continuation post-selection",
                        )
                        evidence["selection_materialization"] = {
                            "old_event_instance_id": event_instance_id,
                            "new_event_instance_id": after_event_instance,
                            "revision_before": revision,
                            "revision_after": after_revision,
                            "date_raw_after": after.get("date_raw"),
                        }
                        evidence["post_binding"] = post_binding
                        evidence["continuation_mode"] = "zg361_4_option_1_selected"
                        evidence["result"] = "GREEN"
                        evidence["failure_reason"] = None
                        write_json(evidence_path, evidence)
                        return evidence
                    if poll_interval_s:
                        time.sleep(poll_interval_s)
                fail("zg361.4 option 1 ACK did not materialize as an event transition")

            if snapshot.get("speed") != 1:
                submission = service.execute_step(
                    "set-speed-1", expected_revision=revision
                )
                accepted_submission(submission, "set-speed-1")
                submissions = evidence["submissions"]
                assert isinstance(submissions, list)
                submissions.append(submission)
            elif snapshot.get("paused") is True:
                submission = service.execute_step(
                    "resume-map", expected_revision=revision
                )
                accepted_submission(submission, "resume-map")
                submissions = evidence["submissions"]
                assert isinstance(submissions, list)
                submissions.append(submission)
            if poll_interval_s:
                time.sleep(poll_interval_s)
        fail("phase-two MCP timed out before the exact zg361.4 continuation")
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two B2 result-continuation failed: {error}"
        ) from error
    raise AssertionError("unreachable")


def run_phase2_b2_same_checkpoint_scenario(
    service: GameplayBridgeService,
    lifecycle: Phase2B2MatrixLifecycle,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    seed_contract: dict[str, object],
) -> dict[str, object]:
    """Prove the real B2 PIP A/B/C routes from one product-only checkpoint."""

    evidence_path = artifacts / "05_phase2_b2_same_checkpoint_scenario.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "phase2_focused_b2_same_checkpoint_product_only",
        "live_readiness": "not_proven",
        "phase2_b2_same_checkpoint_complete": False,
        "phase2_acceptance_complete": False,
        "full_phase2_acceptance_claimed": False,
        "gameplay_acceptance_executed": False,
        "focused_gameplay_green_claimed": False,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "legacy_run_scenario_used": False,
        "platform_legal_consent_gate_outside_gameplay_scenario": True,
        "paused_readiness": None,
        "seed_load_proof": None,
        "loaded_feature_manifest": None,
        "domain_owner_contract": None,
        "incident_gameplay_action_cell": None,
        "b2_result_continuation_prelude": None,
        "post_prelude_paused_binding": None,
        "b2_pip_prompt_readiness": None,
        "b2_pip_provider_prechoice": None,
        "b2_same_checkpoint_matrix": None,
        "forbidden_full_batch_cells_executed": [],
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        paused_snapshot = wait_for_phase2_paused_snapshot(
            service,
            artifacts,
            tracked_ck3_pid=tracked_ck3_pid,
        )
        paused_binding = _phase2_paused_binding(
            paused_snapshot,
            label="focused phase-two B2 seed baseline",
        )
        evidence["paused_readiness"] = {
            "result": "GREEN",
            "artifact": "04_phase2_paused_readiness.json",
            "binding": paused_binding,
        }
        manifest = service.query_loaded_feature_manifest_v1(
            expected_revision=int(paused_binding["revision"])
        )
        evidence["loaded_feature_manifest"] = manifest
        if not (
            isinstance(manifest, dict)
            and manifest.get("loaded_feature_manifest_ready") is True
        ):
            raise acceptance.RunnerError(
                "focused B2 loaded-feature manifest is not actionable"
            )
        evidence["seed_load_proof"] = prove_phase2_loaded_seed(
            paused_snapshot,
            seed_contract,
            artifacts,
            loaded_feature_manifest=manifest,
        )
        owner_contract = _phase2_domain_query_contract(
            seed_contract,
            player_character_id=int(paused_binding["player_character_id"]),
        )
        evidence["domain_owner_contract"] = owner_contract

        # Depending on the exact save boundary, the product-only seed either owns
        # the genuine zg361.4 result card or has already advanced to the exact B2
        # prompt. Both identities are native-query bound; no unrelated visible
        # event is guessed or auto-cleared.
        result_continuation = run_phase2_b2_result_continuation_prelude(
            service,
            artifacts,
            baseline_binding=paused_binding,
        )
        evidence["b2_result_continuation_prelude"] = result_continuation
        evidence["gameplay_acceptance_executed"] = True
        write_json(evidence_path, evidence)

        post_prelude_snapshot = service.snapshot()
        if not isinstance(post_prelude_snapshot, dict):
            raise acceptance.RunnerError(
                "focused B2 post-prelude baseline is not a snapshot"
            )
        post_prelude_binding = _phase2_paused_binding(
            post_prelude_snapshot,
            label="focused B2 post-prelude baseline",
        )
        if (
            post_prelude_binding["bridge_pid"] != tracked_ck3_pid
            or post_prelude_binding["connection_generation"]
            != paused_binding["connection_generation"]
            or post_prelude_binding["player_character_id"]
            != paused_binding["player_character_id"]
        ):
            raise acceptance.RunnerError(
                "focused B2 prelude escaped its initial PID/generation/player"
            )
        evidence["post_prelude_paused_binding"] = post_prelude_binding

        b2_prompt_snapshot = wait_for_phase2_b2_pip_prompt(
            service,
            artifacts,
            baseline_binding=post_prelude_binding,
        )
        b2_prompt_binding = _phase2_paused_binding(
            b2_prompt_snapshot,
            label="focused B2 prompt baseline",
        )
        evidence["b2_pip_prompt_readiness"] = {
            "result": "GREEN",
            "artifact": "05_phase2_b2_pip_prompt_readiness.json",
            "binding": b2_prompt_binding,
        }
        try:
            prechoice = inspect_b2_pip_prechoice(
                service,
                owner_character_id=owner_contract[
                    "b2_pip_owner_character_id"
                ],
                request_nonce="zg361.phase2.b2.focused.pre-matrix",
            )
        except B2PrechoiceInspectionError as error:
            evidence["b2_pip_provider_prechoice"] = error.evidence
            write_json(
                artifacts / "06_phase2_b2_pip_prechoice.json",
                error.evidence,
            )
            raise
        evidence["b2_pip_provider_prechoice"] = prechoice
        write_json(
            artifacts / "06_phase2_b2_pip_prechoice.json",
            prechoice,
        )
        write_json(evidence_path, evidence)

        matrix_artifacts = artifacts / "07_phase2_b2_same_checkpoint_matrix"
        try:
            matrix = run_b2_same_checkpoint_matrix(
                service,
                lifecycle,
                owner_character_id=owner_contract[
                    "b2_pip_owner_character_id"
                ],
                artifacts_directory=matrix_artifacts,
            )
        except B2SameCheckpointMatrixError as error:
            evidence["b2_same_checkpoint_matrix"] = error.evidence
            raise
        evidence["b2_same_checkpoint_matrix"] = matrix
        if not (
            matrix.get("result") == "GREEN"
            and isinstance(matrix.get("checks"), dict)
            and matrix["checks"].get("four_exact_restores") is True
            and matrix["checks"].get("all_managed_pids_dead") is True
        ):
            raise acceptance.RunnerError(
                "focused B2 same-checkpoint matrix returned without full A/B/C proof"
            )
        evidence.update(
            {
                "result": "GREEN",
                "live_readiness": "production-live primitive",
                "phase2_b2_same_checkpoint_complete": True,
                "focused_gameplay_green_claimed": True,
                "failure_reason": None,
            }
        )
        write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["result"] = "RED"
        evidence["phase2_b2_same_checkpoint_complete"] = False
        evidence["focused_gameplay_green_claimed"] = False
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"focused B2 same-checkpoint scenario failed: {error}"
        ) from error


def run_phase2_live_scenario(
    service: GameplayBridgeService,
    artifacts: Path,
    *,
    tracked_ck3_pid: int,
    seed_contract: dict[str, object],
    userdir: Path | None = None,
    bootstrap: dict[str, object] | None = None,
    b3_manager_typed_selector_provider: (
        Callable[[GameplayBridgeService], Mapping[str, object]] | None
    ) = None,
) -> dict[str, object]:
    """Run only MCP phase-two primitives; never fall back to phase-one UI."""

    evidence_path = artifacts / "05_phase2_live_scenario.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "scope": "complete_phase2_mcp_only_live_batch",
        "phase2_acceptance_complete": False,
        "gameplay_acceptance_executed": False,
        "gameplay_green_claimed": False,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "legacy_run_scenario_used": False,
        "paused_readiness": None,
        "seed_load_proof": None,
        "loaded_feature_manifest": None,
        "domain_cell_registry": PHASE2_DOMAIN_CELL_REGISTRY,
        "domain_owner_contract": None,
        "incident_gameplay_action_cell": None,
        "b2_pip_gameplay_action_cell": None,
        "ai_owned_case_gameplay_action_cell": None,
        "manager_governance_gameplay_action_cell": None,
        "workforce_collective_gameplay_action_cell": None,
        "scoreboard_gameplay_action_cell": None,
        "post_incident_paused_binding": None,
        "b2_pip_prompt_readiness": None,
        "completed_gameplay_action_cells": [],
        "pre_restore_domain_queries": None,
        "save_restore_lineage": None,
        "post_restore_domain_queries": None,
        "domain_restore_consistency": None,
        "completed_observation_only_cells": [],
        "missing_gameplay_action_cells": list(
            PHASE2_MISSING_GAMEPLAY_ACTION_CELLS
        ),
        "unimplemented_domain_cells": _phase2_unimplemented_domain_cells(),
        "failure_reason": None,
    }
    write_json(evidence_path, evidence)
    try:
        paused_snapshot = wait_for_phase2_paused_snapshot(
            service,
            artifacts,
            tracked_ck3_pid=tracked_ck3_pid,
        )
        paused_binding = _phase2_paused_binding(
            paused_snapshot, label="phase-two scenario baseline"
        )
        evidence["paused_readiness"] = {
            "result": "GREEN",
            "artifact": "04_phase2_paused_readiness.json",
            "binding": paused_binding,
        }
        manifest = service.query_loaded_feature_manifest_v1(
            expected_revision=int(paused_binding["revision"])
        )
        evidence["loaded_feature_manifest"] = manifest
        if not (
            isinstance(manifest, dict)
            and manifest.get("loaded_feature_manifest_ready") is True
        ):
            raise acceptance.RunnerError(
                "phase-two loaded-feature manifest is not actionable"
            )
        seed_load_proof = prove_phase2_loaded_seed(
            paused_snapshot,
            seed_contract,
            artifacts,
            loaded_feature_manifest=manifest,
        )
        evidence["seed_load_proof"] = seed_load_proof

        owner_contract = _phase2_domain_query_contract(
            seed_contract,
            player_character_id=int(paused_binding["player_character_id"]),
        )
        evidence["domain_owner_contract"] = owner_contract
        incident_action = run_phase2_incident_gameplay_action_cell(
            service,
            artifacts,
            owner_character_id=owner_contract[
                "incident_owner_character_id"
            ],
        )
        evidence["incident_gameplay_action_cell"] = incident_action
        evidence["completed_gameplay_action_cells"] = [
            "incident_xyz_gameplay_action_and_postcondition_matrix"
        ]
        evidence["gameplay_acceptance_executed"] = True
        write_json(evidence_path, evidence)

        # Incident advances the game through real events.  Never reuse the
        # seed-load revision for later provider queries or the B2 checkpoint.
        post_incident_snapshot = service.snapshot()
        if not isinstance(post_incident_snapshot, dict):
            raise acceptance.RunnerError(
                "phase-two post-Incident checkpoint baseline is not an object"
            )
        post_incident_binding = _phase2_paused_binding(
            post_incident_snapshot,
            label="phase-two post-Incident checkpoint baseline",
        )
        if (
            post_incident_binding["bridge_pid"] != tracked_ck3_pid
            or post_incident_binding["connection_generation"]
            != paused_binding["connection_generation"]
            or post_incident_binding["player_character_id"]
            != paused_binding["player_character_id"]
        ):
            raise acceptance.RunnerError(
                "phase-two post-Incident baseline escaped its first-PID/player binding"
            )
        evidence["post_incident_paused_binding"] = post_incident_binding
        b2_prompt_snapshot = wait_for_phase2_b2_pip_prompt(
            service,
            artifacts,
            baseline_binding=post_incident_binding,
        )
        b2_prompt_binding = _phase2_paused_binding(
            b2_prompt_snapshot,
            label="phase-two B2 prompt checkpoint baseline",
        )
        evidence["b2_pip_prompt_readiness"] = {
            "result": "GREEN",
            "artifact": "05_phase2_b2_pip_prompt_readiness.json",
            "binding": b2_prompt_binding,
        }
        pre_restore_queries = run_phase2_domain_query_stage(
            service,
            artifacts,
            stage="pre_restore",
            binding=b2_prompt_binding,
            owner_contract=owner_contract,
        )
        evidence["pre_restore_domain_queries"] = pre_restore_queries

        def run_checkpointed_phase2_actions() -> dict[str, object]:
            b2_action = run_phase2_b2_pip_gameplay_action_cell(
                service,
                artifacts,
                owner_character_id=owner_contract[
                    "b2_pip_owner_character_id"
                ],
            )
            # The frozen baseline contains the real player B2 prompt.  Only
            # its already-proven product selection clears that window; the
            # AI-owned helper itself never selects player events.  The
            # following life-advance and receipt therefore remain inside the
            # same restorable checkpoint transaction.
            ai_owned_action = run_phase2_ai_owned_case_gameplay_action_cell(
                service,
                artifacts,
                owner_character_id=owner_contract[
                    "ai_owned_case_owner_character_id"
                ],
                subject_character_id=owner_contract[
                    "ai_owned_case_subject_character_id"
                ],
            )
            return {
                "schema_version": 1,
                "result": "GREEN",
                "scope": "phase2_checkpointed_gameplay_action_batch",
                "mcp_only": True,
                "timeline_advance_expected": True,
                "b2_pip_gameplay_action_cell": b2_action,
                "ai_owned_case_gameplay_action_cell": ai_owned_action,
            }

        lineage = run_phase2_save_restore_lineage(
            service,
            artifacts,
            tracked_ck3_pid=tracked_ck3_pid,
            checkpointed_gameplay_action=run_checkpointed_phase2_actions,
        )
        evidence["save_restore_lineage"] = lineage
        checkpointed_actions = lineage.get("checkpointed_gameplay_action")
        b2_action = (
            checkpointed_actions.get("b2_pip_gameplay_action_cell")
            if isinstance(checkpointed_actions, dict)
            else None
        )
        ai_owned_action = (
            checkpointed_actions.get("ai_owned_case_gameplay_action_cell")
            if isinstance(checkpointed_actions, dict)
            else None
        )
        if not (
            isinstance(b2_action, dict)
            and b2_action.get("result") == "GREEN"
        ):
            raise acceptance.RunnerError(
                "phase-two save/restore lineage lacks its GREEN B2 action"
            )
        if not (
            isinstance(ai_owned_action, dict)
            and ai_owned_action.get("result") == "GREEN"
            and ai_owned_action.get("background_business_complete") is True
        ):
            raise acceptance.RunnerError(
                "phase-two save/restore lineage lacks its GREEN AI-owned "
                "business postcondition"
            )
        evidence["b2_pip_gameplay_action_cell"] = b2_action
        evidence["ai_owned_case_gameplay_action_cell"] = ai_owned_action
        evidence["completed_gameplay_action_cells"].append(
            "b2_pip_gameplay_action_and_postcondition_matrix"
        )
        evidence["completed_gameplay_action_cells"].append(
            "ai_owned_case_gameplay_action_and_postcondition_matrix"
        )
        restored_binding = lineage.get("after_restore")
        if not isinstance(restored_binding, dict):
            raise acceptance.RunnerError(
                "phase-two save/restore lineage lacks its restored paused binding"
            )
        post_restore_queries = run_phase2_domain_query_stage(
            service,
            artifacts,
            stage="post_restore",
            binding=restored_binding,
            owner_contract=owner_contract,
        )
        evidence["post_restore_domain_queries"] = post_restore_queries
        evidence["domain_restore_consistency"] = (
            compare_phase2_domain_query_stages(
                pre_restore_queries,
                post_restore_queries,
                artifacts,
            )
        )
        evidence["completed_observation_only_cells"] = list(
            pre_restore_queries.get("implemented_cells", [])
        )
        write_json(evidence_path, evidence)

        manager_action = run_phase2_manager_governance_gameplay_action_cell(
            service,
            artifacts,
            typed_selector_provider=b3_manager_typed_selector_provider,
        )
        evidence["manager_governance_gameplay_action_cell"] = manager_action
        if manager_action.get("result") == "GREEN":
            evidence["completed_gameplay_action_cells"].append(
                "manager_governance_gameplay_action_and_postcondition_matrix"
            )
            evidence["missing_gameplay_action_cells"] = [
                value
                for value in evidence["missing_gameplay_action_cells"]
                if value
                != "manager_governance_gameplay_action_and_postcondition_matrix"
            ]
        write_json(evidence_path, evidence)

        scoreboard_action = run_phase2_scoreboard_gameplay_action_cell(
            service,
            artifacts,
        )
        evidence["scoreboard_gameplay_action_cell"] = scoreboard_action
        if scoreboard_action.get("result") == "GREEN":
            evidence["completed_gameplay_action_cells"].append(
                "scoreboard_named_widget_action_and_postcondition_matrix"
            )
            evidence["missing_gameplay_action_cells"] = [
                value
                for value in evidence["missing_gameplay_action_cells"]
                if value
                != "scoreboard_named_widget_action_and_postcondition_matrix"
            ]
        write_json(evidence_path, evidence)

        # The dedicated third fixture is installed only now, after all prior
        # cells and their read-only restore comparison are complete.  A
        # managed reload activates its invisible scripted-widget summon.  The
        # real #360 product action and typed subject/owner cards then run A/B/C
        # from one hash-identical checkpoint, followed by a final baseline
        # restore.  Tests that call this function without an isolated userdir
        # may prove the non-mutating runner preflight, but still fail before
        # claiming that a gameplay action or business postcondition occurred.
        if userdir is None or bootstrap is None:
            workforce_preflight = (
                preflight_phase2_workforce_m360_gameplay_action_cell(
                    service,
                    artifacts,
                    owner_character_id=owner_contract[
                        "workforce_owner_character_id"
                    ],
                    subject_character_id=int(
                        restored_binding["player_character_id"]
                    ),
                    seed_contract=seed_contract,
                    prior_lineage=lineage,
                )
            )
            workforce_action = {
                "schema_version": 2,
                "cell_id": (
                    "workforce_collective_gameplay_action_and_postcondition_matrix"
                ),
                "result": "RED",
                "stage": "isolated_runtime_context_gate",
                "mcp_only": True,
                "gameplay_action_executed": False,
                "gameplay_business_postcondition_claimed": False,
                "helper_invoked": False,
                "owner_character_id": owner_contract[
                    "workforce_owner_character_id"
                ],
                "subject_character_id": int(
                    restored_binding["player_character_id"]
                ),
                "preflight": workforce_preflight,
                "missing_requirements": [
                    {
                        "id": "isolated_workforce_runtime_context",
                        "reason": (
                            "the action runner requires the managed isolated "
                            "userdir and bootstrap to activate its non-release fixture"
                        ),
                    }
                ],
                "failure_reason": (
                    "runner preflight passed, but no isolated userdir/bootstrap "
                    "was supplied for live execution"
                ),
            }
            write_json(
                artifacts
                / "08_phase2_workforce_m360_gameplay_action_cell.json",
                workforce_action,
            )
            raise acceptance.RunnerError(
                "phase-two Workforce #360 runner preflight GREEN, but live "
                "execution lacks its isolated userdir/bootstrap context"
            )
        else:
            workforce_action = run_phase2_workforce_m360_gameplay_action_cell(
                service,
                artifacts,
                userdir=userdir,
                bootstrap=bootstrap,
                owner_character_id=owner_contract[
                    "workforce_owner_character_id"
                ],
                subject_character_id=int(
                    restored_binding["player_character_id"]
                ),
                b2_owner_character_id=owner_contract[
                    "b2_pip_owner_character_id"
                ],
                prior_lineage=lineage,
            )
        evidence["workforce_collective_gameplay_action_cell"] = (
            workforce_action
        )
        if workforce_action.get("result") == "GREEN":
            evidence["completed_gameplay_action_cells"].append(
                "workforce_collective_gameplay_action_and_postcondition_matrix"
            )
            evidence["missing_gameplay_action_cells"] = [
                value
                for value in evidence["missing_gameplay_action_cells"]
                if value
                != "workforce_collective_gameplay_action_and_postcondition_matrix"
            ]
            write_json(evidence_path, evidence)

        # The scoreboard runner ledger is wired too.  The exact dispatcher and
        # provider-observed revision are static-ready, but no paused-game
        # source/ACK/later-query artifact has promoted the production
        # capability yet.  Preserve the typed RED evidence instead of
        # manufacturing a gameplay PASS from static or fixture proof.
        raise acceptance.RunnerError(
            "phase-two MCP matrix RED: Incident, B2, and AI-owned gameplay "
            "actions and B2/Incident/Workforce/AI-owned observations passed, "
            "but B3 manager governance remains provider-pending until its "
            "typed AI manager selector is bound, and the scoreboard "
            "named-widget action/postcondition cell remains fail-closed"
        )
    except BaseException as error:
        incident_path = artifacts / (
            "05_phase2_incident_xyz_gameplay_action_cell.json"
        )
        if incident_path.is_file():
            try:
                incident_value = json.loads(
                    incident_path.read_text(encoding="utf-8")
                )
                if isinstance(incident_value, dict):
                    evidence["incident_gameplay_action_cell"] = incident_value
                    submissions = incident_value.get("selection_submissions")
                    evidence["gameplay_acceptance_executed"] = bool(
                        isinstance(submissions, list) and submissions
                    )
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        b2_path = artifacts / "05_phase2_b2_pip_gameplay_action_cell.json"
        if b2_path.is_file():
            try:
                b2_value = json.loads(b2_path.read_text(encoding="utf-8"))
                if isinstance(b2_value, dict):
                    evidence["b2_pip_gameplay_action_cell"] = b2_value
                    submission = b2_value.get("selection_submission")
                    evidence["gameplay_acceptance_executed"] = bool(
                        evidence["gameplay_acceptance_executed"]
                        or isinstance(submission, dict)
                    )
                    completed = evidence["completed_gameplay_action_cells"]
                    if (
                        b2_value.get("result") == "GREEN"
                        and isinstance(completed, list)
                        and "b2_pip_gameplay_action_and_postcondition_matrix"
                        not in completed
                    ):
                        completed.append(
                            "b2_pip_gameplay_action_and_postcondition_matrix"
                        )
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        ai_owned_path = artifacts / (
            "05_phase2_ai_owned_case_gameplay_action_cell.json"
        )
        if ai_owned_path.is_file():
            try:
                ai_owned_value = json.loads(
                    ai_owned_path.read_text(encoding="utf-8")
                )
                if isinstance(ai_owned_value, dict):
                    evidence["ai_owned_case_gameplay_action_cell"] = (
                        ai_owned_value
                    )
                    evidence["gameplay_acceptance_executed"] = bool(
                        evidence["gameplay_acceptance_executed"]
                        or ai_owned_value.get("gameplay_action_executed")
                        is True
                    )
                    completed = evidence["completed_gameplay_action_cells"]
                    if (
                        ai_owned_value.get("result") == "GREEN"
                        and ai_owned_value.get("background_business_complete")
                        is True
                        and isinstance(completed, list)
                        and "ai_owned_case_gameplay_action_and_postcondition_matrix"
                        not in completed
                    ):
                        completed.append(
                            "ai_owned_case_gameplay_action_and_postcondition_matrix"
                        )
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        manager_path = artifacts / (
            "07e_phase2_manager_governance_gameplay_action_cell.json"
        )
        if manager_path.is_file():
            try:
                manager_value = json.loads(
                    manager_path.read_text(encoding="utf-8")
                )
                if isinstance(manager_value, dict):
                    evidence["manager_governance_gameplay_action_cell"] = (
                        manager_value
                    )
                    evidence["gameplay_acceptance_executed"] = bool(
                        evidence["gameplay_acceptance_executed"]
                        or manager_value.get("gameplay_action_executed") is True
                    )
                    completed = evidence["completed_gameplay_action_cells"]
                    if (
                        manager_value.get("result") == "GREEN"
                        and manager_value.get("gameplay_action_complete") is True
                        and isinstance(completed, list)
                        and (
                            "manager_governance_gameplay_action_and_postcondition_matrix"
                            not in completed
                        )
                    ):
                        completed.append(
                            "manager_governance_gameplay_action_and_postcondition_matrix"
                        )
                        evidence["missing_gameplay_action_cells"] = [
                            value
                            for value in evidence["missing_gameplay_action_cells"]
                            if value
                            != "manager_governance_gameplay_action_and_postcondition_matrix"
                        ]
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        workforce_path = artifacts / (
            "08_phase2_workforce_m360_gameplay_action_cell.json"
        )
        if workforce_path.is_file():
            try:
                workforce_value = json.loads(
                    workforce_path.read_text(encoding="utf-8")
                )
                if isinstance(workforce_value, dict):
                    evidence["workforce_collective_gameplay_action_cell"] = (
                        workforce_value
                    )
                    completed = evidence["completed_gameplay_action_cells"]
                    if (
                        workforce_value.get("result") == "GREEN"
                        and isinstance(completed, list)
                        and (
                            "workforce_collective_gameplay_action_and_postcondition_matrix"
                            not in completed
                        )
                    ):
                        completed.append(
                            "workforce_collective_gameplay_action_and_postcondition_matrix"
                        )
                        evidence["missing_gameplay_action_cells"] = [
                            value
                            for value in evidence[
                                "missing_gameplay_action_cells"
                            ]
                            if value
                            != "workforce_collective_gameplay_action_and_postcondition_matrix"
                        ]
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        scoreboard_path = artifacts / (
            "07c_phase2_scoreboard_named_widget_action_cell.json"
        )
        if scoreboard_path.is_file():
            try:
                scoreboard_value = json.loads(
                    scoreboard_path.read_text(encoding="utf-8")
                )
                if isinstance(scoreboard_value, dict):
                    evidence["scoreboard_gameplay_action_cell"] = (
                        scoreboard_value
                    )
                    action_matrix = scoreboard_value.get("action_matrix")
                    scoreboard_action_accepted = bool(
                        isinstance(action_matrix, dict)
                        and any(
                            isinstance(row, dict)
                            and isinstance(row.get("action_result"), dict)
                            and row["action_result"].get("accepted") is True
                            for rows in action_matrix.values()
                            if isinstance(rows, list)
                            for row in rows
                        )
                    )
                    evidence["gameplay_acceptance_executed"] = bool(
                        evidence["gameplay_acceptance_executed"]
                        or scoreboard_action_accepted
                    )
                    completed = evidence["completed_gameplay_action_cells"]
                    if (
                        scoreboard_value.get("result") == "GREEN"
                        and scoreboard_value.get("candidate_batch_complete")
                        is True
                        and scoreboard_value.get(
                            "all_postconditions_verified"
                        )
                        is True
                        and scoreboard_value.get(
                            "all_expected_acl_denials_verified"
                        )
                        is True
                        and scoreboard_value.get(
                            "per_surface_single_session_binding_verified"
                        )
                        is True
                        and scoreboard_value.get(
                            "cross_surface_clean_restart_verified"
                        )
                        is True
                        and scoreboard_value.get(
                            "production_capability_advertised"
                        )
                        is True
                        and scoreboard_value.get("promotion_eligible") is True
                        and isinstance(completed, list)
                        and (
                            "scoreboard_named_widget_action_and_postcondition_matrix"
                            not in completed
                        )
                    ):
                        completed.append(
                            "scoreboard_named_widget_action_and_postcondition_matrix"
                        )
                        evidence["missing_gameplay_action_cells"] = [
                            value
                            for value in evidence[
                                "missing_gameplay_action_cells"
                            ]
                            if value
                            != "scoreboard_named_widget_action_and_postcondition_matrix"
                        ]
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        lineage_path = artifacts / "06_phase2_save_restore_lineage.json"
        if lineage_path.is_file():
            try:
                lineage_value = json.loads(
                    lineage_path.read_text(encoding="utf-8")
                )
                if isinstance(lineage_value, dict):
                    evidence["save_restore_lineage"] = lineage_value
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        evidence["result"] = "RED"
        evidence["phase2_acceptance_complete"] = False
        evidence["gameplay_green_claimed"] = False
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        write_json(evidence_path, evidence)
        if isinstance(error, acceptance.RunnerError):
            raise
        raise acceptance.RunnerError(
            f"phase-two MCP-only live scenario failed: {error}"
        ) from error


def run_scenario(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
    *,
    title_navigation_service: GameplayBridgeService,
    tracked_ck3_pid: int,
    native_bridge: NativeBridgeLaunchConfig,
    preflight_bridge_identity: dict[str, object],
) -> dict[str, object]:
    initialize_fixture(stream, artifacts)
    # The fixture decision belongs only to setup.  Close it before the shared
    # native matrix so every full acceptance proves title navigation in the
    # same tracked CK3 PID; promo capture cannot start FFmpeg before this gate.
    close_native_decisions_panel(artifacts, "05_title_navigation_preflight")
    title_navigation_evidence = run_native_title_navigation_matrix(
        title_navigation_service,
        artifacts,
        tracked_ck3_pid=tracked_ck3_pid,
        native_bridge=native_bridge,
        preflight_bridge_identity=preflight_bridge_identity,
    )
    if recorder:
        assert_promo_frame_clean(
            artifacts,
            "05_promo_pre_record_clean_hud",
            label="pre_record_hud",
            phase="pre_record",
        )
        recorder.start()
        recorder.hold(2.0)
    choose_direct_publication(stream, artifacts, recorder)
    gui_evidence = capture_scoreboard_gui(artifacts, recorder)
    jingcha_evidence = capture_jingcha_planner(
        stream,
        artifacts,
        recorder,
        pause_service=title_navigation_service,
    )
    personal_result_evidence = capture_superior_assigned_result(
        stream,
        artifacts,
        recorder,
        timeline_service=title_navigation_service,
        personal_switch_due_day_ordinal=int(
            jingcha_evidence["host_pause_gate"]["personal_switch_due_day_ordinal"]
        ),
    )
    received_evidence = None
    policy_cards: list[dict[str, object]] = []
    if recorder:
        received_evidence = capture_received_scoreboard(
            stream,
            artifacts,
            recorder,
            timeline_service=title_navigation_service,
        )
        policy_cards = capture_policy_cards(
            stream,
            artifacts,
            recorder,
            timeline_service=title_navigation_service,
        )
        recorder.mark("all_requested_product_screens_captured")
        recorder.hold(2.0)
    counts = stream.counts()
    constructor_counts = fixture_constructor_counts()
    policy_dispatch_counts = {
        f"{mechanism_id:03d}": stream.count(
            f"ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched"
        )
        for mechanism_id, *_ in PROMO_POLICY_CARDS
    }
    reviewed_history_id = str(
        personal_result_evidence["reviewed_official_history_id"]
    )
    return {
        "standard_lobby_start": True,
        "title_navigation_mcp_matrix": title_navigation_evidence,
        "player_history_id": EXPECTED_PLAYER_HISTORY_ID,
        "reviewed_official_history_id": reviewed_history_id,
        "real_character_provenance": (
            recorder.real_character_provenance
            if recorder
            else promo_real_character_provenance(reviewed_history_id)
        ),
        "fixture_constructor_counts": constructor_counts,
        "historical_subjects_manufactured_by_fixture": bool(
            any(constructor_counts.values())
        ),
        "test_decisions_visible_inside_clean_spans": 0 if recorder else None,
        "native_decisions_drawer_visible_inside_clean_spans": 0 if recorder else None,
        "real_character_runtime_attestation": {
            "song_emperor_exact_build_marker_count": stream.count(
                "ZGA: TEST PASS exact_build_song_emperor"
            ),
            "song_emperor_player_switch_marker_count": stream.count(
                "ZGA: TEST PASS switched_to_song_emperor"
            ),
            "reviewed_official_history_id": reviewed_history_id,
            "historical_target_data_marker_count": stream.count(
                HISTORICAL_TARGET_DATA_MARKER_PREFIX
            ),
            "historical_target_pass_marker_count": stream.count(
                HISTORICAL_TARGET_PASS_MARKER
            ),
            "projected_bottom_two_marker_count": stream.count(
                "ZGA: TEST PASS personal_result_target_projected_bottom_two"
            ),
            "resolved_subject_superior_grade_marker_count": stream.count(
                "ZGA: TEST PASS superior_assigned_player_grade"
            ),
        },
        "song_emperor_celestial": True,
        "song_emperor_independent_sample": True,
        "review_liege_minimum_tier": "duchy",
        "independence_required_for_review_entry": False,
        "non_independent_celestial_liege_entry": True,
        "direct_governor_cohort_at_least_three": True,
        "bootstrap_first_review_strict_distribution": "23 => 7 / 14 / 2",
        "post_baseline_newcomer_ranked_and_protected_from_325": True,
        "calibration_c_all_newcomer_noop": True,
        "calibration_c_mixed_newcomer_atomic_swap": True,
        "pending_and_settled_review_idempotence": True,
        "grade_325_fixed_penalty_receipts_and_appeal_refund": True,
        "salary_penalty_contract": "one-year -25%; appeal stops future reduction; elapsed salary is not backdated",
        "real_review_effect_invocations_minimum": 2,
        "mechanism_batch": {
            "fixture_cases_passed": sum(
                "ZGA: MECHANISM CASE PASS" in line for line in stream.lines
            ),
            "product_choice_effects_applied": sum(
                "ZG361M: CASE" in line and "APPLIED" in line
                for line in stream.lines
            ),
            "portfolio_ledger_verified": bool(
                stream.count("ZGA: MECHANISM LEDGER PASS")
            ),
            "portfolio_idempotence_verified": bool(
                stream.count("ZGA: MECHANISM IDEMPOTENCE PASS")
            ),
        },
        "calibration_choice": "zg361.10.a direct publication",
        "managed_scoreboard_counts_from_row_markers": counts,
        "ai_non_independent_full_review": bool(
            stream.count("ZGA: TEST PASS ai_non_independent_full_review")
        ),
        "ai_non_independent_probe_unavailable": bool(
            stream.count("ZGA: TEST INFO ai_non_independent_review_candidate_unavailable")
        ),
        "ai_small_cohort_neutral_settlement": bool(
            stream.count("ZGA: TEST PASS ai_small_cohort_neutral_settlement")
        ),
        "ai_small_cohort_probe_unavailable": bool(
            stream.count("ZGA: TEST INFO ai_small_cohort_candidate_unavailable")
        ),
        "scoreboard_gui": gui_evidence,
        "jingcha_planner": jingcha_evidence,
        "jingcha_refusal": {
            "superior_opinion_modifier": True,
            "next_review_kpi_malus": -50,
            "consumed_by_original_superior_once": True,
        },
        "superior_assigned_player_result": personal_result_evidence,
        "promo_received_scoreboard": received_evidence,
        "promo_policy_cards": policy_cards,
        "promo_policy_chain": {
            "dispatch_marker_counts": policy_dispatch_counts,
            "all_six_dispatched_marker_count": stream.count(
                "ZGA: TEST PASS clean_policy_chain_all_six_dispatched"
            ),
            "completion_marker_count": stream.count(
                "ZGA: TEST PASS clean_policy_chain_completed"
            ),
            "persisted_choices_verified": bool(
                recorder
                and stream.count("ZGA: TEST PASS clean_policy_chain_completed") == 1
            ),
        },
    }


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if not logs.is_dir():
        return
    for path in sorted(item for item in logs.iterdir() if item.is_file()):
        shutil.copy2(path, artifacts / f"final_{path.name}")


def run_cell(
    artifacts: Path,
    userdir: Path,
    keep_userdir: bool,
    *,
    state_dir: Path,
    native_bridge: NativeBridgeLaunchConfig,
    promo_capture: bool = False,
    phase2_promo_capture: bool = False,
    promo_camera_probe: bool = False,
    loader_smoke: bool = False,
    phase2_live_batch: bool = False,
    phase2_b2_same_checkpoint: bool = False,
    phase2_frontend_first_load_save_name: str | None = None,
    phase2_frontend_first_timeout_seconds: float = (
        NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS
    ),
    runtime_source: Path = SOURCE,
    phase2_product_source: Path | None = None,
    phase2_product_projection: str = "broad",
    phase2_product_projection_manifest: Path | None = None,
    runtime_identity: dict[str, object] | None = None,
    phase2_seed_install: dict[str, object] | None = None,
    phase2_seed_contract_path: Path | None = None,
    phase2_source_checkpoint_registry: Mapping[str, object] | None = None,
) -> dict[str, object]:
    phase2_runtime_mode = (
        phase2_live_batch
        or phase2_promo_capture
        or phase2_b2_same_checkpoint
    )
    _validate_phase2_frontend_first_options(
        phase2_frontend_first_load_save_name,
        phase2_frontend_first_timeout_seconds,
        phase2_runtime_mode=phase2_runtime_mode,
    )
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    artifacts.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    userdir.mkdir(parents=True)
    runtime_source = Path(runtime_source).resolve()
    selected_product_source = (
        Path(phase2_product_source).resolve()
        if phase2_product_source is not None
        else runtime_source
    )
    state_dir = Path(state_dir).resolve()
    userdir = Path(userdir).resolve()
    runtime_identity = dict(runtime_identity or {})
    bridge_identity = runtime_identity.get("native_bridge_runtime")
    source_before = isolated.tree_snapshot(SOURCE)
    runtime_source_before = isolated.tree_snapshot(runtime_source)
    selected_product_source_before = isolated.tree_snapshot(
        selected_product_source
    )
    acceptance.configure_runtime_userdir(userdir)
    verified_manifest_path = runtime_identity.get("workshop_manifest_path")
    bootstrap = bootstrap_userdir(
        userdir,
        selected_product_source,
        workshop_manifest=(
            Path(str(verified_manifest_path))
            if runtime_identity.get("verified_workshop_cache") is True
            and verified_manifest_path
            else None
        ),
        include_acceptance_fixture=not (
            phase2_promo_capture or phase2_b2_same_checkpoint
        ),
        product_projection=phase2_product_projection,
        product_projection_manifest=phase2_product_projection_manifest,
    )
    spec = make_spec(state_dir, acceptance.CK3_EXE.parent.parent)
    if spec.profile_dir.resolve() != userdir:
        raise acceptance.RunnerError(
            "canonical native runtime profile differs from the bootstrapped userdir"
        )
    if not isinstance(bridge_identity, dict):
        raise acceptance.RunnerError(
            "preflight native bridge identity is missing from runtime evidence"
        )

    process = None
    session_handle = None
    native_driver: NativeHeadlessGameplayDriver | None = None
    lock_stack = ExitStack()
    result = "RED"
    error_reason = None
    evidence: dict[str, object] = {}
    diagnostics: list[str] = []
    observed_engine_warnings: list[str] = []
    mount_order: list[str] = []
    game_version = isolated.installed_game_version()
    executable_before = isolated.sha256_file(acceptance.CK3_EXE)
    executable_after = None
    runtime_after: dict[str, str] = {}
    runtime_unchanged = False
    source_unchanged = False
    runtime_source_unchanged = False
    selected_product_source_unchanged = False
    stream = MarkerStream(userdir / "logs" / "debug.log")
    watchdog_pid = None
    tracked_ck3_pid = None
    native_cleanup: dict[str, object] = {}
    driver_closed = False
    locks_released = False
    recorder = (
        PromoRecorder(
            artifacts / "promo",
            contract=(
                PHASE2_PROMO_CAPTURE_CONTRACT
                if phase2_promo_capture
                else LEGACY_PROMO_CAPTURE_CONTRACT
            ),
        )
        if (promo_capture or phase2_promo_capture)
        else None
    )
    recorder_evidence: dict[str, object] = {}
    keyboard_layout_evidence: dict[str, object] = {}
    # The sequel visual producer uses the same managed seed/session/loader
    # boundary as the phase-two MCP batch.  Keep the legacy promo path on its
    # suspended/inject/resume lifecycle.
    loader_gate_enabled = (
        loader_smoke
        or phase2_live_batch or phase2_promo_capture
        or phase2_b2_same_checkpoint
    )
    loader_gate_evidence: dict[str, object] | None = None
    gameplay_acceptance_executed = False
    phase2_supervisor: dict[str, object] | None = None
    phase2_initial_binding: dict[str, object] | None = None
    phase2_final_capabilities: dict[str, object] | None = None
    phase2_native_session_liveness: dict[str, object] | None = None
    phase2_legal_consent: dict[str, object] | None = None
    phase2_seed_install_evidence: dict[str, object] | None = phase2_seed_install
    phase2_promo_producer_error: dict[str, object] | None = None
    phase2_b2_lifecycle: Phase2B2MatrixLifecycle | None = None
    try:
        if executable_before != EXPECTED_EXE_SHA256:
            raise acceptance.RunnerError(
                f"CK3 executable SHA-256 drifted before launch: {executable_before}"
            )
        if phase2_runtime_mode:
            if phase2_seed_install_evidence is None:
                install_kwargs: dict[str, object] = {
                    "observed_game_version": game_version,
                    "observed_executable_sha256": executable_before,
                }
                if phase2_seed_contract_path is not None:
                    install_kwargs["contract_path"] = Path(
                        phase2_seed_contract_path
                    ).resolve()
                phase2_seed_install_evidence = install_phase2_seed(
                    userdir,
                    bootstrap,
                    artifacts,
                    product_only_runtime=(
                        phase2_promo_capture or phase2_b2_same_checkpoint
                    ),
                    **install_kwargs,
                )
            else:
                # This optional injection is for CK3-free lifecycle tests.  It
                # may not turn a blocked seed into a runnable phase-two mode.
                if (
                    not isinstance(phase2_seed_install_evidence, dict)
                    or phase2_seed_install_evidence.get("result") != "GREEN"
                    or not isinstance(
                        phase2_seed_install_evidence.get("contract"), dict
                    )
                    or phase2_seed_install_evidence["contract"].get("ready")
                    is not True
                    or phase2_seed_install_evidence["contract"].get("status")
                    != "ready"
                ):
                    raise acceptance.RunnerError(
                        "phase-two runtime requires a GREEN ready seed install evidence"
                    )
        native_driver = NativeHeadlessGameplayDriver(
            native_bridge.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            command_timeout_seconds=NATIVE_TITLE_COMMAND_TIMEOUT_S,
        )
        title_navigation_service = GameplayBridgeService(native_driver)
        if phase2_runtime_mode:
            phase2_supervisor_options: dict[str, object] = {}
            if phase2_frontend_first_load_save_name is not None:
                phase2_supervisor_options = {
                    "frontend_first_load_save_name": (
                        phase2_frontend_first_load_save_name
                    ),
                    "frontend_first_timeout_seconds": (
                        phase2_frontend_first_timeout_seconds
                    ),
                }
            phase2_supervisor = start_phase2_native_session_supervisor(
                spec, native_bridge, **phase2_supervisor_options
            )
            phase2_initial_binding = wait_for_phase2_native_session_binding(
                title_navigation_service,
                phase2_supervisor,
                artifacts,
            )
            tracked_ck3_pid = int(phase2_initial_binding["bridge_pid"])
            acceptance.ACTIVE_CK3_PID = tracked_ck3_pid
            log(
                "started managed phase-two native_session supervisor on CK3 "
                f"PID {tracked_ck3_pid} and {native_bridge.pipe_name}"
            )
            try:
                phase2_legal_consent = handle_phase2_optional_legal_consent(
                    userdir, artifacts
                )
            except Phase2LegalConsentBlocked as error:
                phase2_legal_consent = dict(error.evidence)
                raise
        else:
            lock_stack.enter_context(exclusive_launch_lock(spec.game_exe))
            lock_stack.enter_context(
                exclusive_state_lock(spec.state_dir, "zhongguo-361-acceptance")
            )
            session_handle = launch_native_ck3(
                spec,
                native_bridge=native_bridge,
                verify_prepared_profile=False,
            )
            process = session_handle.process
            watchdog_pid = session_handle.watchdog_pid
            tracked_ck3_pid = process.pid
            acceptance.ACTIVE_CK3_PID = process.pid
            log(
                "launched suspended/injected/resumed tracked CK3 "
                f"PID {process.pid} on {native_bridge.pipe_name}"
            )
        if loader_gate_enabled:
            loader_gate_evidence = run_loader_gate(
                title_navigation_service,
                artifacts,
                userdir,
                bootstrap,
                tracked_ck3_pid=tracked_ck3_pid,
                phase2_live_batch=phase2_live_batch,
                managed_restore_supervisor=phase2_supervisor is not None,
                phase2_promo_capture=phase2_promo_capture,
                phase2_b2_same_checkpoint=phase2_b2_same_checkpoint,
            )
            native_readiness = loader_gate_evidence["native_readiness"]
            error_scan = loader_gate_evidence["loader_error_log_scan"]
            mount_inventory = loader_gate_evidence[
                "runtime_mount_inventory"
            ]
            if not isinstance(mount_inventory, list):
                raise acceptance.RunnerError(
                    "loader gate returned an invalid mount inventory"
                )
            mount_order = [str(item) for item in mount_inventory]
        if not loader_smoke and not phase2_runtime_mode:
            acceptance.wait_for_ocr_text(
            "新游戏",
            acceptance.MAIN_MENU_REGION,
            BOOT_TIMEOUT_S,
            artifacts,
            "01_main_menu_parser_ready.png",
            stable_hits=1,
        )
        if not loader_gate_enabled:
            mount_order = verify_runtime_load_order(userdir, bootstrap)
        if not loader_smoke and not phase2_runtime_mode:
            new_diagnostics, new_warnings = project_diagnostics(
                userdir, artifacts, "02_main_menu"
            )
            diagnostics.extend(new_diagnostics)
            observed_engine_warnings.extend(new_warnings)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
        if not loader_smoke and not phase2_runtime_mode:
            isolated.dismiss_external_main_menu_popup(artifacts)
            acceptance.navigate_lobby(artifacts)
            isolated.wait_for_gameplay_hud(artifacts)
            acceptance.ensure_game_paused(artifacts, "04_standard_1066_start")
            keyboard_layout_evidence = force_ck3_english_keyboard_layout(artifacts)
        if loader_smoke:
            evidence = {
                "loader_smoke_only": True,
                "scope": "mcp_assisted_frontend_loader_smoke",
                "native_readiness": native_readiness,
                "runtime_mount_inventory": mount_order,
                "loader_error_log_scan": error_scan,
                "gameplay_acceptance_executed": False,
                "gameplay_green_claimed": False,
                "zg361_50_case_cell_executed": False,
                "result_provider_exercised": False,
                "ocr_used": False,
                "image_used": False,
                "coordinates_used": False,
                "navigation_used": False,
                "ffmpeg_started": False,
            }
        elif phase2_promo_capture:
            gameplay_acceptance_executed = True
            if recorder is None:
                raise acceptance.RunnerError(
                    "phase-two promo capture recorder was not initialized"
                )
            if not isinstance(phase2_seed_install_evidence, dict):
                raise acceptance.RunnerError(
                    "phase-two promo capture has no seed install evidence"
                )
            seed_contract_value = phase2_seed_install_evidence.get("contract")
            if not isinstance(seed_contract_value, dict):
                raise acceptance.RunnerError(
                    "phase-two promo capture seed install lacks its contract"
                )
            try:
                evidence = run_phase2_promo_capture_scenario(
                    stream,
                    artifacts,
                    recorder,
                    title_navigation_service=title_navigation_service,
                    tracked_ck3_pid=tracked_ck3_pid,
                    native_bridge=native_bridge,
                    preflight_bridge_identity=bridge_identity,
                    seed_contract=dict(seed_contract_value),
                    seed_install=phase2_seed_install_evidence,
                    native_session_binding=phase2_initial_binding,
                    loader_gate=loader_gate_evidence,
                    source_checkpoint_registry=(
                        phase2_source_checkpoint_registry
                    ),
                    capture_receipt_context={
                        "bootstrap": bootstrap,
                        "runtime_identity": runtime_identity,
                        "game_version": game_version,
                        "executable_sha256": executable_before,
                    },
                )
            except BaseException as error:
                # Keep a producer's typed RED envelope in the durable report
                # while preserving the existing outer error/cleanup flow.
                phase2_promo_producer_error = (
                    phase2_promo_producer_typed_error_payload(error)
                )
                raise
        elif phase2_b2_same_checkpoint:
            if not (
                isinstance(phase2_seed_install_evidence, dict)
                and isinstance(
                    phase2_seed_install_evidence.get("contract"), dict
                )
                and phase2_supervisor is not None
            ):
                raise acceptance.RunnerError(
                    "focused B2 runtime lacks its seed contract or supervisor"
                )
            phase2_b2_lifecycle = Phase2B2MatrixLifecycle(
                title_navigation_service,
                phase2_supervisor,
            )
            evidence = run_phase2_b2_same_checkpoint_scenario(
                title_navigation_service,
                phase2_b2_lifecycle,
                artifacts,
                tracked_ck3_pid=tracked_ck3_pid,
                seed_contract=dict(
                    phase2_seed_install_evidence["contract"]
                ),
            )
            gameplay_acceptance_executed = (
                evidence.get("gameplay_acceptance_executed") is True
            )
            phase2_final_capabilities = (
                phase2_b2_lifecycle.pre_stop_capabilities
            )
            if evidence.get("phase2_b2_same_checkpoint_complete") is not True:
                raise acceptance.RunnerError(
                    "focused B2 scenario returned without complete A/B/C proof"
                )
        elif phase2_live_batch:
            evidence = run_phase2_live_scenario(
                title_navigation_service,
                artifacts,
                tracked_ck3_pid=tracked_ck3_pid,
                seed_contract=dict(
                    phase2_seed_install_evidence["contract"]
                ),
                userdir=userdir,
                bootstrap=bootstrap,
            )
            gameplay_acceptance_executed = (
                evidence.get("phase2_acceptance_complete") is True
            )
            if not gameplay_acceptance_executed:
                raise acceptance.RunnerError(
                    "phase-two MCP scenario returned without complete acceptance"
                )
        elif promo_camera_probe:
            initialize_fixture(stream, artifacts)
            close_native_decisions_panel(
                artifacts, "05_title_navigation_probe_preflight"
            )
            title_navigation_evidence = run_native_title_navigation_matrix(
                title_navigation_service,
                artifacts,
                tracked_ck3_pid=tracked_ck3_pid,
                native_bridge=native_bridge,
                preflight_bridge_identity=bridge_identity,
            )
            clean_evidence = assert_promo_frame_clean(
                artifacts,
                "05_promo_pre_record_clean_hud",
                label="pre_record_hud",
                phase="pre_record",
            )
            evidence = {
                "probe_only": True,
                "player_history_id": EXPECTED_PLAYER_HISTORY_ID,
                "expected_realm_title": "h_china",
                "keyboard_layout": keyboard_layout_evidence,
                "title_navigation_mcp_matrix": title_navigation_evidence,
                "post_navigation_frame_clean": clean_evidence,
                "ffmpeg_started": False,
            }
        else:
            gameplay_acceptance_executed = True
            evidence = run_scenario(
                stream,
                artifacts,
                recorder,
                title_navigation_service=title_navigation_service,
                tracked_ck3_pid=tracked_ck3_pid,
                native_bridge=native_bridge,
                preflight_bridge_identity=bridge_identity,
            )
            evidence["keyboard_layout"] = keyboard_layout_evidence
        # The post-restore liveness gate is intentionally scoped to the MCP
        # batch.  It proves the two-PID save/restore lineage that that
        # scenario owns; the visual promo producer has a separate eight-span
        # contract and must not be forced to manufacture restore evidence.
        if phase2_live_batch:
            liveness = phase2_native_session_liveness_gate(
                title_navigation_service,
                phase2_supervisor,
                artifacts,
                scenario_evidence=evidence,
            )
            phase2_native_session_liveness = liveness
            evidence["native_session_liveness"] = liveness
            capabilities_value = liveness.get("capabilities")
            if isinstance(capabilities_value, dict):
                phase2_final_capabilities = capabilities_value
        new_diagnostics, new_warnings = project_diagnostics(
            userdir,
            artifacts,
            "10_runtime",
            allow_phase2_static_liveness_warnings=phase2_runtime_mode,
        )
        diagnostics.extend(new_diagnostics)
        observed_engine_warnings.extend(new_warnings)
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        if not phase2_runtime_mode and process is not None and process.poll() is not None:
            raise acceptance.RunnerError(
                f"CK3 PID {process.pid} exited before controlled shutdown"
            )
        result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"FATAL {error}")
        if isinstance(error, Exception) and not isinstance(
            error, acceptance.RunnerError
        ):
            traceback.print_exc()
        if not loader_smoke and not phase2_runtime_mode:
            try:
                acceptance.focus_ck3()
                acceptance.ImageGrab.grab().save(artifacts / "fatal_state.png")
            except Exception:
                pass
    finally:
        if recorder is not None and recorder.process is not None:
            try:
                recorder_evidence = recorder.stop()
            except Exception as error:
                result = "RED"
                reason = f"promo recorder stop failed: {error}"
                error_reason = (
                    f"{error_reason}; {reason}" if error_reason else reason
                )
        if phase2_supervisor is not None:
            try:
                scenario_path = artifacts / (
                    "05_phase2_b2_same_checkpoint_scenario.json"
                    if phase2_b2_same_checkpoint
                    else "05_phase2_live_scenario.json"
                )
                if scenario_path.is_file():
                    scenario_value = json.loads(
                        scenario_path.read_text(encoding="utf-8")
                    )
                    if isinstance(scenario_value, dict):
                        evidence = scenario_value
                if phase2_b2_lifecycle is not None:
                    native_cleanup = (
                        prove_phase2_b2_matrix_native_session_cleanup(
                            phase2_b2_lifecycle,
                            artifacts,
                            initial_pid=tracked_ck3_pid,
                            initial_generation=(
                                int(
                                    phase2_initial_binding[
                                        "connection_generation"
                                    ]
                                )
                                if isinstance(phase2_initial_binding, dict)
                                else None
                            ),
                            expected_pipe=native_bridge.pipe_name,
                            scenario_evidence=evidence,
                        )
                    )
                    phase2_final_capabilities = (
                        phase2_b2_lifecycle.pre_stop_capabilities
                    )
                elif phase2_final_capabilities is None:
                    try:
                        final_capabilities_value = (
                            title_navigation_service.capabilities()
                        )
                        if isinstance(final_capabilities_value, dict):
                            phase2_final_capabilities = final_capabilities_value
                    except Exception:
                        phase2_final_capabilities = None
                if phase2_b2_lifecycle is None:
                    native_cleanup = stop_phase2_native_session_supervisor(
                        phase2_supervisor,
                        artifacts,
                        initial_pid=tracked_ck3_pid,
                        initial_generation=(
                            int(
                                phase2_initial_binding[
                                    "connection_generation"
                                ]
                            )
                            if isinstance(phase2_initial_binding, dict)
                            else None
                        ),
                        expected_pipe=native_bridge.pipe_name,
                        scenario_evidence=evidence,
                        final_capabilities=phase2_final_capabilities,
                    )
            except Exception as error:
                cleanup_path = (
                    artifacts / "09_phase2_native_session_cleanup.json"
                )
                if cleanup_path.is_file():
                    try:
                        cleanup_value = json.loads(
                            cleanup_path.read_text(encoding="utf-8")
                        )
                        if isinstance(cleanup_value, dict):
                            native_cleanup = cleanup_value
                    except (OSError, ValueError, json.JSONDecodeError):
                        pass
                result = "RED"
                reason = f"managed phase-two native_session stop failed: {error}"
                error_reason = (
                    f"{error_reason}; {reason}" if error_reason else reason
                )
        elif session_handle is not None:
            try:
                native_cleanup = stop_tracked(
                    session_handle,
                    require_running=result == "GREEN" and not phase2_live_batch,
                )
                if (
                    native_cleanup.get("cleanup_proven") is not True
                    or native_cleanup.get("contract_errors")
                ):
                    raise acceptance.RunnerError(
                        "canonical native cleanup proof returned RED"
                    )
            except Exception as error:
                result = "RED"
                reason = f"controlled native stop failed: {error}"
                error_reason = (
                    f"{error_reason}; {reason}" if error_reason else reason
                )
        acceptance.ACTIVE_CK3_PID = None
        if native_driver is not None:
            try:
                native_driver.close()
                driver_closed = True
            except Exception as error:
                result = "RED"
                reason = f"native driver close failed: {error}"
                error_reason = (
                    f"{error_reason}; {reason}" if error_reason else reason
                )
        try:
            lock_stack.close()
            locks_released = True
        except Exception as error:
            result = "RED"
            reason = f"native runtime lock release failed: {error}"
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )
        try:
            if (
                result == "GREEN"
                and not promo_camera_probe
                and not loader_smoke
                and not phase2_live_batch
                and not phase2_promo_capture
                and not phase2_b2_same_checkpoint
            ):
                stream.validate(final=True)
            else:
                stream.pump(final=True)
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )
        try:
            version_after = isolated.installed_game_version()
            executable_after = isolated.sha256_file(acceptance.CK3_EXE)
            if (
                game_version != EXPECTED_GAME_VERSION
                or version_after != EXPECTED_GAME_VERSION
                or executable_before != EXPECTED_EXE_SHA256
                or executable_after != EXPECTED_EXE_SHA256
            ):
                raise acceptance.RunnerError(
                    "fixed CK3 1.19.0.6 executable contract changed during acceptance"
                )
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )
        try:
            new_diagnostics, new_warnings = project_diagnostics(
                userdir,
                artifacts,
                "11_shutdown",
                allow_phase2_static_liveness_warnings=phase2_runtime_mode,
            )
            diagnostics.extend(new_diagnostics)
            observed_engine_warnings.extend(new_warnings)
            copy_logs(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )
        try:
            runtime_unchanged = True
            for key, target in bootstrap["targets"].items():
                snapshot = isolated.tree_snapshot(target)
                runtime_after[key] = isolated.snapshot_digest(snapshot)
                if snapshot != bootstrap["tree_snapshots"][key]:
                    runtime_unchanged = False
            source_unchanged = isolated.tree_snapshot(SOURCE) == source_before
            runtime_source_unchanged = (
                isolated.tree_snapshot(runtime_source) == runtime_source_before
            )
            selected_product_source_unchanged = (
                isolated.tree_snapshot(selected_product_source)
                == selected_product_source_before
            )
            if (
                not runtime_unchanged
                or not source_unchanged
                or not runtime_source_unchanged
                or not selected_product_source_unchanged
            ):
                raise acceptance.RunnerError("CK3 rewrote a runtime or source tree")
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )

    state_dir_removed = False
    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        try:
            shutil.rmtree(state_dir)
            state_dir_removed = not state_dir.exists()
            userdir_removed = not userdir.exists()
            if not state_dir_removed or not userdir_removed:
                raise OSError(f"native state directory still exists: {state_dir}")
        except Exception as error:
            result = "RED"
            reason = f"native state cleanup failed: {error}"
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )
    elif state_dir.exists():
        log(f"retained native state and userdir at {state_dir}")

    if phase2_promo_capture:
        try:
            finalize_phase2_promo_span_session_receipts(
                evidence,
                native_cleanup,
                artifacts,
                driver_closed=driver_closed,
                locks_released=locks_released,
            )
        except Exception as error:
            result = "RED"
            reason = f"phase-two span receipt finalization failed: {error}"
            error_reason = (
                f"{error_reason}; {reason}" if error_reason else reason
            )

    phase2_promo_capture_complete = (
        not phase2_promo_capture
        or (
            recorder_evidence.get("capture_mode") == PHASE2_PROMO_CAPTURE_MODE
            and recorder_evidence.get("capture_contract_version")
            == PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
            and recorder_evidence.get("clean_capture_complete") is True
            and recorder_evidence.get("missing_clean_spans") == []
        )
    )
    phase2_b2_same_checkpoint_complete = (
        phase2_b2_same_checkpoint
        and result == "GREEN"
        and evidence.get("result") == "GREEN"
        and evidence.get("phase2_b2_same_checkpoint_complete") is True
        and evidence.get("phase2_acceptance_complete") is False
        and evidence.get("full_phase2_acceptance_claimed") is False
    )
    gameplay_green_claimed = (
        result == "GREEN"
        and gameplay_acceptance_executed
        and (
            (phase2_promo_capture and phase2_promo_capture_complete)
            or (
                phase2_b2_same_checkpoint
                and phase2_b2_same_checkpoint_complete
            )
            or (
                phase2_live_batch
                and evidence.get("phase2_acceptance_complete") is True
            )
            or not phase2_runtime_mode
        )
    )
    if loader_gate_evidence is not None:
        loader_gate_evidence["gameplay_acceptance_executed"] = (
            gameplay_acceptance_executed
        )
        loader_gate_evidence["gameplay_green_claimed"] = gameplay_green_claimed
        write_json(artifacts / "03_loader_gate.json", loader_gate_evidence)
    report = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "game_version": game_version,
        "expected_ck3_executable_sha256": EXPECTED_EXE_SHA256,
        "ck3_executable_before_sha256": executable_before,
        "ck3_executable_after_sha256": executable_after,
        "debug_mode": False,
        "isolated_userdir": True,
        "canonical_native_runtime": True,
        "native_launch_sequence": (
            (
                "managed_native_session_supervisor"
                if phase2_supervisor is not None
                else "not_launched_seed_red"
            )
            if phase2_runtime_mode
            else "suspended_inject_resume"
        ),
        "native_bridge_pipe": native_bridge.pipe_name,
        "native_title_command_timeout_seconds": (
            NATIVE_TITLE_COMMAND_TIMEOUT_S
        ),
        "tracked_full_acceptance_pid": tracked_ck3_pid,
        "promo_camera_probe_only": promo_camera_probe,
        "loader_smoke_only": loader_smoke,
        "phase2_live_batch": phase2_live_batch,
        "phase2_promo_capture": phase2_promo_capture,
        "phase2_b2_same_checkpoint": phase2_b2_same_checkpoint,
        "phase2_frontend_first": {
            "enabled": phase2_frontend_first_load_save_name is not None,
            "load_save_name": phase2_frontend_first_load_save_name,
            "timeout_seconds": (
                phase2_frontend_first_timeout_seconds
                if phase2_frontend_first_load_save_name is not None
                else None
            ),
        },
        "phase2_promo_capture_complete": phase2_promo_capture_complete,
        "phase2_b2_same_checkpoint_complete": (
            phase2_b2_same_checkpoint_complete
        ),
        "promo_capture_mode": (
            recorder.contract.mode
            if recorder is not None
            else None
        ),
        "loader_gate_executed": loader_gate_evidence is not None,
        "phase2_seed_install": phase2_seed_install_evidence,
        "phase2_promo_producer_error": phase2_promo_producer_error,
        "phase2_legal_consent": phase2_legal_consent,
        "loader_gate_evidence": loader_gate_evidence,
        "gameplay_acceptance_executed": gameplay_acceptance_executed,
        "gameplay_green_claimed": gameplay_green_claimed,
        "native_session_liveness": phase2_native_session_liveness,
        "native_session_liveness_scope": (
            "phase2_post_restore_supervisor_liveness"
            if phase2_live_batch
            else (
                "not_applicable_phase2_promo_capture"
                if phase2_promo_capture
                else (
                    "matrix_owns_final_shutdown_no_post_stop_liveness_gate"
                    if phase2_b2_same_checkpoint
                    else None
                )
            )
        ),
        "zg361_50_case_cell_executed": (
            isinstance(evidence.get("incident_gameplay_action_cell"), dict)
            and evidence["incident_gameplay_action_cell"].get("result")
            == "GREEN"
            if phase2_b2_same_checkpoint
            else (
                False
                if loader_smoke or phase2_live_batch or phase2_promo_capture
                else None
            )
        ),
        "enabled_mods": bootstrap["enabled_mods"],
        "verified_mount_order": mount_order,
        "product_runtime_manifest": bootstrap["manifest"],
        "runtime_tree_before_sha256": bootstrap["tree_sha256"],
        "runtime_tree_after_sha256": runtime_after,
        "runtime_trees_unchanged": runtime_unchanged,
        "source_tree_unchanged": source_unchanged,
        "runtime_source_tree_unchanged": runtime_source_unchanged,
        "phase2_product_source_path": str(selected_product_source),
        "phase2_product_projection": phase2_product_projection,
        "phase2_product_projection_manifest": (
            str(Path(phase2_product_projection_manifest).resolve())
            if phase2_product_projection_manifest is not None
            else None
        ),
        "phase2_product_source_tree_unchanged": (
            selected_product_source_unchanged
        ),
        **runtime_identity,
        "fixture_markers": stream.lines,
        "project_diagnostics": list(dict.fromkeys(diagnostics)),
        "observed_nonblocking_engine_warnings": list(
            dict.fromkeys(observed_engine_warnings)
        ),
        "scenario_evidence": evidence,
        "seed_generation_loaded_chain": (
            evidence.get("seed_generation_loaded_chain")
            if phase2_promo_capture
            else None
        ),
        "promo_capture": recorder_evidence,
        "isolated_state_dir_path": str(state_dir),
        "isolated_userdir_path": str(userdir),
        "state_dir_profile_matches_userdir": spec.profile_dir.resolve() == userdir,
        "state_dir_removed_after_run": state_dir_removed,
        "userdir_removed_after_run": userdir_removed,
        "process_watchdog_pid": watchdog_pid,
        "native_cleanup": native_cleanup,
        "phase2_native_session": (
            {
                "startup": phase2_initial_binding,
                "final_binding": (
                    phase2_final_capabilities.get("diagnostics")
                    if isinstance(phase2_final_capabilities, dict)
                    else None
                ),
                "pid_lineage": native_cleanup.get("pid_lineage"),
                "connection_generation_lineage": native_cleanup.get(
                    "connection_generation_lineage"
                ),
                "restart_count": (
                    native_cleanup.get("session_report", {}).get(
                        "restart_count"
                    )
                    if isinstance(native_cleanup.get("session_report"), dict)
                    else None
                ),
                "frontend_first_warmup": (
                    native_cleanup.get("session_report", {}).get(
                        "frontend_first_warmup"
                    )
                    if isinstance(native_cleanup.get("session_report"), dict)
                    else None
                ),
                "cleanup": native_cleanup,
            }
            if phase2_runtime_mode
            else None
        ),
        "native_driver_closed": driver_closed,
        "native_runtime_locks_released": locks_released,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "desktop": (
                "not_queried_mcp_only"
                if loader_smoke or phase2_live_batch or phase2_b2_same_checkpoint
                else (
                    "producer_owned_visual_capture"
                    if phase2_promo_capture
                    else (
                        f"{acceptance.pyautogui.size().width}x"
                        f"{acceptance.pyautogui.size().height}"
                    )
                )
            ),
        },
    }
    write_json(artifacts / "report.json", report)
    return report


def main(
    artifacts_dir: str | None = None,
    keep_userdir: bool = True,
    preflight_only: bool = False,
    promo_capture: bool = False,
    phase2_promo_capture: bool = False,
    promo_camera_probe: bool = False,
    loader_smoke: bool = False,
    phase2_live_batch: bool = False,
    phase2_b2_same_checkpoint: bool = False,
    phase2_frontend_first_load_save_name: str | None = None,
    phase2_frontend_first_timeout_seconds: float = (
        NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS
    ),
    workshop_cache_source: str | None = None,
    workshop_manifest: str | None = None,
    bridge_dll: str | None = None,
    bridge_injector: str | None = None,
    bridge_pipe: str | None = None,
    phase2_seed_contract: str | None = None,
    phase2_source_checkpoint_registry: str | None = None,
    phase2_product_source: str | None = None,
    phase2_product_projection: str = "broad",
    phase2_product_projection_manifest: str | None = None,
) -> int:
    selected_runtime_modes = sum(
        bool(value)
        for value in (
            promo_capture,
            phase2_promo_capture,
            promo_camera_probe,
            loader_smoke,
            phase2_live_batch,
            phase2_b2_same_checkpoint,
        )
    )
    if selected_runtime_modes > 1:
        raise acceptance.RunnerError(
            "--promo-capture, --phase2-promo-capture, --promo-camera-probe, "
            "--loader-smoke, --phase2-live-batch and "
            "--phase2-b2-same-checkpoint are mutually exclusive"
        )
    phase2_runtime_mode = (
        phase2_live_batch
        or phase2_promo_capture
        or phase2_b2_same_checkpoint
    )
    if not isinstance(phase2_product_projection, str):
        raise acceptance.RunnerError(
            "phase-two product projection must be a string"
        )
    phase2_product_projection = phase2_product_projection.strip()
    if (
        not phase2_product_projection
        or any(
            character in phase2_product_projection
            for character in ("/", "\\", "\x00")
        )
    ):
        raise acceptance.RunnerError(
            "phase-two product projection must be a path-free identifier"
        )
    if (
        phase2_product_projection != "broad"
        and phase2_product_projection_manifest is None
    ):
        raise acceptance.RunnerError(
            "a named phase-two product projection requires its manifest"
        )
    if (
        phase2_product_source is not None
        or phase2_product_projection != "broad"
        or phase2_product_projection_manifest is not None
    ) and not phase2_runtime_mode:
        raise acceptance.RunnerError(
            "phase-two product projection options require a Phase2 runtime mode"
        )
    if phase2_product_source is not None and workshop_cache_source is not None:
        raise acceptance.RunnerError(
            "--phase2-product-source and --workshop-cache-source are mutually exclusive"
        )
    _validate_phase2_frontend_first_options(
        phase2_frontend_first_load_save_name,
        phase2_frontend_first_timeout_seconds,
        phase2_runtime_mode=(
            phase2_runtime_mode
        ),
    )
    # Do not let the sequel mode fall through to the legacy visual scenario.
    # A real phase-two choreography must be registered explicitly before any
    # preflight, profile write, CK3 launch, or FFmpeg process is attempted.
    if phase2_promo_capture:
        _ensure_phase2_promo_capture_producer()
    runtime_source = (
        Path(workshop_cache_source).expanduser().resolve()
        if workshop_cache_source
        else SOURCE.resolve()
    )
    manifest_path = (
        Path(workshop_manifest).expanduser().resolve()
        if workshop_manifest
        else None
    )
    phase2_seed_contract_path = (
        Path(phase2_seed_contract).expanduser().resolve()
        if phase2_seed_contract
        else None
    )
    phase2_product_source_path = (
        Path(phase2_product_source).expanduser().resolve()
        if phase2_product_source
        else None
    )
    phase2_product_projection_manifest_path = (
        Path(phase2_product_projection_manifest).expanduser().resolve()
        if phase2_product_projection_manifest
        else None
    )
    source_checkpoint_registry_value: Mapping[str, object] | None = None
    if phase2_source_checkpoint_registry:
        registry_path = Path(
            phase2_source_checkpoint_registry
        ).expanduser().resolve()
        try:
            loaded_registry = json.loads(
                registry_path.read_text(encoding="utf-8-sig")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise acceptance.RunnerError(
                "cannot load phase-two source checkpoint registry: "
                f"{type(error).__name__}: {error}"
            ) from error
        if not isinstance(loaded_registry, dict):
            raise acceptance.RunnerError(
                "phase-two source checkpoint registry must be a JSON object"
            )
        source_checkpoint_registry_value = loaded_registry
    native_bridge = resolve_native_bridge_config(
        bridge_dll, bridge_injector, bridge_pipe
    )
    # Every managed Phase2 gameplay mode now performs the owner-authorized
    # legal-modal OCR gate after binding.  Only loader-smoke stops before that
    # boundary, so every other runtime mode must prove the desktop stack before
    # launch instead of discovering a missing OCR dependency inside CK3.
    require_visual_tools = not loader_smoke
    runtime_identity = preflight(
        runtime_source,
        manifest_path,
        native_bridge=native_bridge,
        require_visual_tools=require_visual_tools,
    )
    if preflight_only:
        if (
            phase2_live_batch
            or phase2_promo_capture
            or phase2_b2_same_checkpoint
        ):
            preflight_phase2_seed_contract(
                contract_path=(
                    phase2_seed_contract_path
                    if phase2_seed_contract_path is not None
                    else PHASE2_SEED_CONTRACT_PATH
                ),
                runtime_source=runtime_source,
                workshop_manifest=manifest_path,
                product_only_runtime=(
                    phase2_promo_capture or phase2_b2_same_checkpoint
                ),
                product_source=phase2_product_source_path,
                product_projection=phase2_product_projection,
                product_projection_manifest=(
                    phase2_product_projection_manifest_path
                ),
            )
        print("ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
        if not artifacts.parent.is_dir():
            raise acceptance.RunnerError(
                f"artifact parent does not exist: {artifacts.parent}"
            )
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        artifacts = RUNS_ROOT / f"zga_{stamp}_{uuid.uuid4().hex[:8]}"
    state_dir = artifacts.with_name(artifacts.name + "_native_state")
    userdir = state_dir / "profile"
    steam_root = terminal.steam_userdata_root()
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe(
        (artifacts, state_dir, userdir), steam_root, workshop_roots
    )
    protected_before = isolated.protected_snapshot(steam_root)
    artifacts.mkdir()
    # Bind the optional offline result to this acceptance attempt after the
    # fresh artifact directory exists.  ``preflight`` runs before this point
    # by design, so this copy is the only write performed by the runner; it
    # does not re-invoke the CLI or cross the CK3 launch boundary.
    open_kaishek_row = runtime_identity.get("open_kaishek_preflight")
    if isinstance(open_kaishek_row, dict):
        open_kaishek_path = artifacts / "open_kaishek-preflight.json"
        try:
            open_kaishek_row["artifact_path"] = str(open_kaishek_path.resolve())
            write_json(open_kaishek_path, open_kaishek_row)
        except BaseException as error:
            # Evidence loss is retained in the run identity, but an optional
            # accelerator must not change the existing CK3 acceptance policy.
            open_kaishek_row["artifact_error"] = (
                f"{type(error).__name__}: {error}"
            )
    report = run_cell(
        artifacts / "cell",
        userdir,
        keep_userdir,
        state_dir=state_dir,
        native_bridge=native_bridge,
        promo_capture=promo_capture,
        phase2_promo_capture=phase2_promo_capture,
        promo_camera_probe=promo_camera_probe,
        loader_smoke=loader_smoke,
        phase2_live_batch=phase2_live_batch,
        phase2_b2_same_checkpoint=phase2_b2_same_checkpoint,
        phase2_frontend_first_load_save_name=(
            phase2_frontend_first_load_save_name
        ),
        phase2_frontend_first_timeout_seconds=(
            phase2_frontend_first_timeout_seconds
        ),
        runtime_source=runtime_source,
        phase2_product_source=phase2_product_source_path,
        phase2_product_projection=phase2_product_projection,
        phase2_product_projection_manifest=(
            phase2_product_projection_manifest_path
        ),
        runtime_identity=runtime_identity,
        phase2_seed_contract_path=phase2_seed_contract_path,
        phase2_source_checkpoint_registry=(
            source_checkpoint_registry_value
        ),
    )
    result = report["result"]
    error_reason = report["error_reason"]
    phase2_scenario_value = report.get("scenario_evidence")
    phase2_scenario = (
        phase2_scenario_value
        if isinstance(phase2_scenario_value, dict)
        else {}
    )
    phase2_complete_claim = (
        report.get("gameplay_acceptance_executed") is True
        and report.get("gameplay_green_claimed") is True
        and phase2_scenario.get("result") == "GREEN"
        and phase2_scenario.get("phase2_acceptance_complete") is True
        and phase2_scenario.get("mcp_only") is True
        and phase2_scenario.get("ocr_used") is False
        and phase2_scenario.get("image_used") is False
        and phase2_scenario.get("coordinates_used") is False
        and phase2_scenario.get("test_decision_used") is False
        and phase2_scenario.get("legacy_run_scenario_used") is False
    )
    if phase2_live_batch and phase2_complete_claim is not True:
        result = "RED"
        reason = "phase-two report lacks a complete MCP-only scenario proof"
        error_reason = f"{error_reason}; {reason}" if error_reason else reason
    phase2_promo_capture_complete_claim = (
        phase2_promo_capture
        and report.get("result") == "GREEN"
        and report.get("phase2_promo_capture") is True
        and isinstance(report.get("promo_capture"), dict)
        and report["promo_capture"].get("capture_mode")
        == PHASE2_PROMO_CAPTURE_MODE
        and report["promo_capture"].get("capture_contract_version")
        == PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
        and report["promo_capture"].get("clean_capture_complete") is True
        and report["promo_capture"].get("missing_clean_spans") == []
    )
    if phase2_promo_capture and phase2_promo_capture_complete_claim is not True:
        result = "RED"
        reason = "phase-two promo capture lacks a complete canonical eight-span proof"
        error_reason = f"{error_reason}; {reason}" if error_reason else reason
    b2_matrix_value = phase2_scenario.get("b2_same_checkpoint_matrix")
    b2_matrix = b2_matrix_value if isinstance(b2_matrix_value, dict) else {}
    phase2_b2_same_checkpoint_complete_claim = (
        phase2_b2_same_checkpoint
        and report.get("result") == "GREEN"
        and report.get("phase2_b2_same_checkpoint") is True
        and report.get("phase2_b2_same_checkpoint_complete") is True
        and report.get("gameplay_acceptance_executed") is True
        and report.get("gameplay_green_claimed") is True
        and phase2_scenario.get("result") == "GREEN"
        and phase2_scenario.get("phase2_b2_same_checkpoint_complete") is True
        and phase2_scenario.get("phase2_acceptance_complete") is False
        and phase2_scenario.get("full_phase2_acceptance_claimed") is False
        and phase2_scenario.get("mcp_only") is True
        and phase2_scenario.get("ocr_used") is False
        and phase2_scenario.get("image_used") is False
        and phase2_scenario.get("coordinates_used") is False
        and phase2_scenario.get("test_decision_used") is False
        and phase2_scenario.get("legacy_run_scenario_used") is False
        and b2_matrix.get("result") == "GREEN"
        and isinstance(b2_matrix.get("checks"), dict)
        and b2_matrix["checks"].get("four_exact_restores") is True
        and b2_matrix["checks"].get("all_managed_pids_dead") is True
    )
    if (
        phase2_b2_same_checkpoint
        and phase2_b2_same_checkpoint_complete_claim is not True
    ):
        result = "RED"
        reason = (
            "focused B2 report lacks a complete product-only same-checkpoint "
            "A/B/C proof"
        )
        error_reason = f"{error_reason}; {reason}" if error_reason else reason
    protected_unchanged = False
    try:
        isolated.verify_protected_storage(
            protected_before,
            steam_root,
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
        )
        protected_unchanged = True
    except BaseException as error:
        result = "RED"
        reason = str(error) or type(error).__name__
        error_reason = f"{error_reason}; {reason}" if error_reason else reason
    if result != "GREEN":
        # The outer protected-storage postflight is part of the run result.
        # Never retain or print a focused completion claim after that gate
        # turns the overall attempt RED.
        phase2_b2_same_checkpoint_complete_claim = False
    matrix = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "loader_smoke_only": loader_smoke,
        "phase2_live_batch": phase2_live_batch,
        "phase2_promo_capture": phase2_promo_capture,
        "phase2_b2_same_checkpoint": phase2_b2_same_checkpoint,
        "phase2_promo_capture_complete": phase2_promo_capture_complete_claim,
        "phase2_b2_same_checkpoint_complete": (
            phase2_b2_same_checkpoint_complete_claim
        ),
        "loader_gate_executed": (
            loader_smoke
            or phase2_live_batch or phase2_promo_capture
            or phase2_b2_same_checkpoint
        ),
        "native_session_liveness": report.get("native_session_liveness"),
        "native_session_liveness_scope": report.get(
            "native_session_liveness_scope"
        ),
        "phase2_promo_producer_error": report.get(
            "phase2_promo_producer_error"
        ),
        "gameplay_acceptance_executed": report.get(
            "gameplay_acceptance_executed", False
        ),
        "gameplay_green_claimed": (
            result == "GREEN"
            and (
                (
                    phase2_complete_claim
                    if phase2_live_batch
                    else (
                        phase2_promo_capture_complete_claim
                        if phase2_promo_capture
                        else (
                            phase2_b2_same_checkpoint_complete_claim
                            if phase2_b2_same_checkpoint
                            else report.get("gameplay_green_claimed") is True
                        )
                    )
                )
            )
        ),
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
        "postflight_quiet_seconds": (
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" and protected_unchanged else 0
        ),
    }
    write_json(artifacts / "report.json", matrix)
    write_evidence_index(artifacts, matrix)
    heading = (
        "ZHONGGUO 361 MCP-ASSISTED LOADER SMOKE"
        if loader_smoke
        else (
            "ZHONGGUO 361 PHASE-TWO LIVE BATCH"
            if phase2_live_batch
            else (
                "ZHONGGUO 361 PHASE-TWO PROMO CAPTURE"
                if phase2_promo_capture
                else (
                    "ZHONGGUO 361 PHASE-TWO B2 SAME-CHECKPOINT"
                    if phase2_b2_same_checkpoint
                    else "ZHONGGUO 361 ACCEPTANCE"
                )
            )
        )
    )
    print(f"\n===== {heading} =====")
    print(f"cell                    {report['result']}")
    print(
        "protected storage       "
        + ("UNCHANGED" if protected_unchanged else "UNPROVEN")
    )
    print(f"artifacts               {artifacts}")
    if loader_smoke:
        print("gameplay acceptance     NOT RUN")
        print("gameplay GREEN claim    NONE")
    elif phase2_live_batch and matrix["gameplay_green_claimed"] is not True:
        print("phase-two acceptance    INCOMPLETE / RED")
        print("gameplay GREEN claim    NONE")
    elif phase2_b2_same_checkpoint:
        print(
            "focused B2 A/B/C        "
            + (
                "GREEN"
                if matrix["phase2_b2_same_checkpoint_complete"] is True
                else "INCOMPLETE / RED"
            )
        )
        print("full phase-two claim    NONE")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument(
        "--discard-userdir",
        action="store_true",
        help="delete the isolated userdir after GREEN; default preserves all process material",
    )
    parser.add_argument("--preflight", action="store_true", help="do not launch CK3")
    parser.add_argument(
        "--promo-capture",
        action="store_true",
        help="record an append-only post-loading gameplay take and extra product UI",
    )
    parser.add_argument(
        "--phase2-promo-capture",
        action="store_true",
        help=(
            "run the explicitly registered phase-two visual producer with the "
            "canonical eight-span capture contract; never falls back to --promo-capture"
        ),
    )
    parser.add_argument(
        "--promo-camera-probe",
        action="store_true",
        help="stop after the historical Bianzhou camera and clean-HUD preflight",
    )
    parser.add_argument(
        "--loader-smoke",
        action="store_true",
        help=(
            "run a zero-visual native/MCP frontend loader smoke and error.log "
            "scan; does not enter or claim gameplay acceptance"
        ),
    )
    parser.add_argument(
        "--phase2-live-batch",
        action="store_true",
        help=(
            "run the strict MCP-only phase-two capability gate and independent "
            "scenario; four frozen read-only domain providers run before the "
            "still-missing named-widget/gameplay actions force RED"
        ),
    )
    parser.add_argument(
        "--phase2-b2-same-checkpoint",
        action="store_true",
        help=(
            "run the product-only focused B2 route: real Incident prelude, "
            "one frozen PIP checkpoint, accept/negotiate/refuse, four "
            "restores and five-PID cleanup; does not claim full Phase2"
        ),
    )
    parser.add_argument(
        "--phase2-frontend-first-load-save-name",
        help=(
            "opt-in Phase2 startup: launch without a save argument, wait for "
            "Frontend, stop, then load this save basename on the same pipe"
        ),
    )
    parser.add_argument(
        "--phase2-frontend-first-timeout-seconds",
        type=float,
        default=NATIVE_SESSION_FRONTEND_FIRST_DEFAULT_TIMEOUT_SECONDS,
        help="bounded Frontend marker wait for the Phase2 opt-in startup",
    )
    parser.add_argument(
        "--workshop-cache-source",
        help="verified fresh CK3 Workshop cache leaf used instead of the development source",
    )
    parser.add_argument(
        "--workshop-manifest",
        help="formal ID-bearing release manifest used to verify --workshop-cache-source",
    )
    parser.add_argument(
        "--bridge-dll",
        help="exact-build production native bridge DLL (or use XAR bridge env)",
    )
    parser.add_argument(
        "--bridge-injector",
        help="exact-build suspended-process injector (paired with --bridge-dll)",
    )
    parser.add_argument(
        "--bridge-pipe",
        help=(
            r"optional run-unique \\.\pipe\xar_ck3_bridge_zg361_<32 hex> name; "
            "a fresh nonce is generated by default"
        ),
    )
    parser.add_argument(
        "--phase2-seed-contract",
        help=(
            "explicit canonical ready seed contract for phase-two live or "
            "promo mode; keeps a generated candidate out of the source tree"
        ),
    )
    parser.add_argument(
        "--phase2-source-checkpoint-registry",
        help=(
            "real-CK3 canonical per-span source checkpoint registry; "
            "required by the Phase2 promo source preflight"
        ),
    )
    parser.add_argument(
        "--phase2-product-source",
        help=(
            "optional exact historical Phase2 product tree; it is mounted "
            "independently from the canonical development/preflight source"
        ),
    )
    parser.add_argument(
        "--phase2-product-projection",
        default="broad",
        help=(
            "named hash-bound product projection (default: broad); non-broad "
            "names require --phase2-product-projection-manifest"
        ),
    )
    parser.add_argument(
        "--phase2-product-projection-manifest",
        help="manifest for --phase2-product-projection",
    )
    arguments = parser.parse_args()
    try:
        raise SystemExit(
            main(
                artifacts_dir=arguments.artifacts_dir,
                keep_userdir=not arguments.discard_userdir,
                preflight_only=arguments.preflight,
                promo_capture=arguments.promo_capture,
                phase2_promo_capture=arguments.phase2_promo_capture,
                promo_camera_probe=arguments.promo_camera_probe,
                loader_smoke=arguments.loader_smoke,
                phase2_live_batch=arguments.phase2_live_batch,
                phase2_b2_same_checkpoint=(
                    arguments.phase2_b2_same_checkpoint
                ),
                phase2_frontend_first_load_save_name=(
                    arguments.phase2_frontend_first_load_save_name
                ),
                phase2_frontend_first_timeout_seconds=(
                    arguments.phase2_frontend_first_timeout_seconds
                ),
                workshop_cache_source=arguments.workshop_cache_source,
                workshop_manifest=arguments.workshop_manifest,
                bridge_dll=arguments.bridge_dll,
                bridge_injector=arguments.bridge_injector,
                bridge_pipe=arguments.bridge_pipe,
                phase2_seed_contract=arguments.phase2_seed_contract,
                phase2_source_checkpoint_registry=(
                    arguments.phase2_source_checkpoint_registry
                ),
                phase2_product_source=arguments.phase2_product_source,
                phase2_product_projection=(
                    arguments.phase2_product_projection
                ),
                phase2_product_projection_manifest=(
                    arguments.phase2_product_projection_manifest
                ),
            )
        )
    except acceptance.RunnerError as error:
        print(f"ZHONGGUO 361 ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
