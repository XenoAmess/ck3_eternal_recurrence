#!/usr/bin/env python3
"""Return an extracted owner subset to native AI and prove its rejoin.

The immutable input is the production pre-retreat canonical checkpoint.  Four
fresh stages are used: production retreat/save, seed-only same-day player
switch back to Character 29829, production-only AI-control reload/save, and a
final one-PID daily assignment/ETA/same-CombatID rejoin observation.  The
production stages mutate gameplay only through ordinary retreat, one-day
advance and checkpoint actions; the player switch is confined to the seed
fixture stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from typing import Any, Callable
import uuid


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_active_combat_retreat_live_acceptance as retreat_live  # noqa: E402
import run_owner_subset_reinforcement_rejoin_live_acceptance as rejoin_live  # noqa: E402
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
from xar_autoplayer.bridge.mod_driver import DataModGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
ONE_GAME_DAY_RAW = 24
ORIGINAL_CHARACTER_ID = owner_live.ORIGINAL_CHARACTER_ID
OWNER_SUBSET_CHARACTER_ID = owner_live.OWNER_SUBSET_CHARACTER_ID
REJOIN_CUNIT_ID = owner_live.OWNER_SUBSET_CUNIT_ID
ANCHOR_CUNIT_ID = owner_live.UNCONTROLLED_ALLY_CUNIT_ID
OPPOSITE_CUNIT_ID = owner_live.ORIGINAL_ATTACKER_CUNIT_ID
COMBAT_ID = owner_live.COMBAT_ID
RETREAT_TARGET_PROVINCE_ID = owner_live.TARGET_PROVINCE_ID
RETURN_CHARACTER_ANCHOR_PROVINCE_ID = 2_619
RETURN_SWITCH_MARKER = "XAR_FIXTURE:OWNER_SUBSET_RETURN|target=29829"
RETURN_CLEAR_MARKER = "XAR_FIXTURE:OWNER_SUBSET_RETURN_GUARD_CLEARED"
RETURN_GUARD_VARIABLE = "xar_fixture_owner_subset_return_consumed"
ASSIGNED_ARCHIVE_NAME = "xar_ai_reassignment_assigned.ck3"
JOINED_ARCHIVE_NAME = "xar_ai_reassignment_joined.ck3"
_ROOT_MARKER_NAME = ".xar-owner-subset-ai-reassignment.json"
FORBIDDEN_NATIVE_CALLS = rejoin_live.FORBIDDEN_NATIVE_CALLS


def _parser() -> argparse.ArgumentParser:
    parser = owner_live._parser()
    parser.description = __doc__
    parser.add_argument("--max-assignment-days", type=int, default=30)
    parser.add_argument("--max-eta-days", type=int, default=30)
    return parser


def _return_switch_effect() -> str:
    return (
        f"province:{RETURN_CHARACTER_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        "\t\tsave_temporary_scope_as = xar_fixture_owner_subset_return_target\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        "\t\texists = scope:xar_fixture_owner_subset_return_target\n"
        f"\t\tNOT = {{ global_var:{RETURN_GUARD_VARIABLE} = 1 }}\n"
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {RETURN_GUARD_VARIABLE}\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        "\tset_player_character = scope:xar_fixture_owner_subset_return_target\n"
        f'\tdebug_log = "{RETURN_SWITCH_MARKER}"\n'
        "}\n"
    )


def _return_clear_effect() -> str:
    return (
        "if = {\n"
        f"\tlimit = {{ exists = global_var:{RETURN_GUARD_VARIABLE} }}\n"
        f"\tremove_global_variable = {RETURN_GUARD_VARIABLE}\n"
        f'\tdebug_log = "{RETURN_CLEAR_MARKER}"\n'
        "}\n"
    )


def _active_side_ids(
    battle: dict[str, object], side_index: int = 1
) -> tuple[list[int], list[int]]:
    return rejoin_live._side_ids(battle, side_index)


def _retreating_membership_transient_proof(
    snapshot: dict[str, object], pair: dict[str, object]
) -> dict[str, object]:
    try:
        army = rejoin_live._subject_army(snapshot, REJOIN_CUNIT_ID)
    except RuntimeError:
        army = {}
    rejoin = pair.get("rejoin_frame")
    anchor = pair.get("anchor_frame")
    rejoin = rejoin if isinstance(rejoin, dict) else {}
    anchor = anchor if isinstance(anchor, dict) else {}
    route = army.get("route_province_ids")
    checks = {
        "same_paused_pair_binding": pair.get("binding_ok") is True,
        "withdrawn_query_typed_mismatch": rejoin.get("status") == "unavailable"
        and rejoin.get("unavailable_reason") == "subunit_backlink_mismatch"
        and rejoin.get("battle_reinforcement_assignment_ready") is False
        and rejoin.get("selected_public_cunit_id") == REJOIN_CUNIT_ID,
        "anchor_query_remains_available": anchor.get("status") == "available"
        and anchor.get("battle_reinforcement_assignment_ready") is True
        and anchor.get("selected_public_cunit_id") == ANCHOR_CUNIT_ID,
        "native_ai_control": army.get("controllable") is False,
        "withdrawn_while_retreating": army.get("in_combat") is False
        and army.get("retreating") is True
        and army.get("army_state_code") == 6,
        "retreat_route_preserved": army.get("move_target_province_id")
        == RETREAT_TARGET_PROVINCE_ID
        and isinstance(route, list)
        and bool(route)
        and route[-1] == RETREAT_TARGET_PROVINCE_ID,
    }
    return {
        "classification": "retreating_subunit_backlink_mismatch",
        "subject_army": army,
        "rejoin_frame": rejoin,
        "anchor_frame": anchor,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _typed_native_membership_proof(
    frame: dict[str, object], selected_public_cunit_id: int
) -> dict[str, object]:
    rows = rejoin_live._native_rows(frame)
    native_order = frame.get("native_order")
    native_order = native_order if isinstance(native_order, dict) else {}
    support_search = native_order.get(
        "support_search_province_ids_in_stored_order"
    )
    flattened: list[int] = []
    locations: list[tuple[int, int]] = []
    rows_typed = bool(rows)
    for row_index, row in enumerate(rows):
        ids = row.get("public_cunit_ids_in_stored_order")
        if not isinstance(ids, list) or not all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            for value in ids
        ):
            rows_typed = False
            continue
        for column_index, value in enumerate(ids):
            flattened.append(value)
            if value == selected_public_cunit_id:
                locations.append((row_index, column_index))
    native_carmy_id = frame.get("selected_native_carmy_id")
    coordinator_id = frame.get("coordinator_id")
    unit_stack_index = frame.get("unit_stack_stored_index")
    subunit_index = frame.get("subunit_stored_index")
    checks = {
        "typed_available_frame": frame.get("status") == "available"
        and frame.get("unavailable_reason") is None
        and frame.get("battle_reinforcement_assignment_ready") is True,
        "selected_identity": frame.get("selected_public_cunit_id")
        == selected_public_cunit_id,
        "positive_native_carmy_id": isinstance(native_carmy_id, int)
        and not isinstance(native_carmy_id, bool)
        and native_carmy_id > 0,
        "positive_coordinator_id": isinstance(coordinator_id, int)
        and not isinstance(coordinator_id, bool)
        and coordinator_id > 0,
        "typed_parent_indices": isinstance(unit_stack_index, int)
        and not isinstance(unit_stack_index, bool)
        and unit_stack_index >= 0
        and isinstance(subunit_index, int)
        and not isinstance(subunit_index, bool)
        and subunit_index >= 0,
        "typed_parent_rows": rows_typed
        and len(flattened) == len(set(flattened)),
        "selected_occurs_once_at_subunit_index": len(locations) == 1
        and locations[0][0] == subunit_index,
        "typed_support_search_vector": isinstance(support_search, list)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            for value in support_search
        ),
    }
    return {
        "selected_public_cunit_id": selected_public_cunit_id,
        "selected_native_carmy_id": native_carmy_id,
        "coordinator_id": coordinator_id,
        "unit_stack_stored_index": unit_stack_index,
        "subunit_stored_index": subunit_index,
        "native_rows": rows,
        "flattened_public_cunit_order": flattened,
        "selected_locations": locations,
        "support_search_province_ids_in_stored_order": support_search,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _independent_native_pair_available_proof(
    pair: dict[str, object],
) -> dict[str, object]:
    rejoin = pair.get("rejoin_frame")
    anchor = pair.get("anchor_frame")
    rejoin = rejoin if isinstance(rejoin, dict) else {}
    anchor = anchor if isinstance(anchor, dict) else {}
    rejoin_membership = _typed_native_membership_proof(
        rejoin, REJOIN_CUNIT_ID
    )
    anchor_membership = _typed_native_membership_proof(
        anchor, ANCHOR_CUNIT_ID
    )
    same_coordinator = bool(
        rejoin_membership.get("coordinator_id")
        == anchor_membership.get("coordinator_id")
        and isinstance(rejoin_membership.get("coordinator_id"), int)
        and rejoin_membership.get("coordinator_id", 0) > 0
    )
    same_parent = bool(
        rejoin_membership.get("selected_native_carmy_id")
        == anchor_membership.get("selected_native_carmy_id")
        and rejoin_membership.get("unit_stack_stored_index")
        == anchor_membership.get("unit_stack_stored_index")
    )
    relationship = (
        "same_parent"
        if same_parent
        else "cross_stack_same_coordinator"
        if same_coordinator
        else "different_coordinator"
    )
    checks = {
        "same_paused_pair_binding": pair.get("binding_ok") is True,
        "withdrawn_membership_typed": rejoin_membership.get("ok") is True,
        "anchor_membership_typed": anchor_membership.get("ok") is True,
        "same_coordinator": same_coordinator,
    }
    return {
        "classification": "independent_native_memberships_available",
        "parent_relationship": relationship,
        "same_parent": same_parent,
        "rejoin_membership": rejoin_membership,
        "anchor_membership": anchor_membership,
        "legacy_same_parent_order_ready": pair.get("available_order_ready"),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _daily_ai_context_proof(
    snapshot: dict[str, object],
    *,
    expected_date_raw: int,
    expected_episode_run_id: str,
) -> dict[str, object]:
    try:
        army = rejoin_live._subject_army(snapshot, REJOIN_CUNIT_ID)
    except RuntimeError:
        army = {}
    checks = {
        "paused": snapshot.get("paused") is True,
        "exact_date": snapshot.get("date_raw") == expected_date_raw,
        "same_episode": snapshot.get("episode_run_id")
        == expected_episode_run_id,
        "player_returned": owner_live._played_character_id(snapshot)
        == ORIGINAL_CHARACTER_ID,
        "withdrawn_unit_not_controllable": army.get("controllable") is False,
    }
    return {
        "expected_date_raw": expected_date_raw,
        "expected_episode_run_id": expected_episode_run_id,
        "subject_army": army,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _native_pair_reopened_proof(
    initial_transient: dict[str, object],
    pair: dict[str, object],
    context: dict[str, object],
    *,
    day_index: int,
) -> dict[str, object]:
    available = _independent_native_pair_available_proof(pair)
    checks = {
        "initial_typed_retreating_mismatch": initial_transient.get("ok")
        is True,
        "observed_after_daily_advance": day_index >= 1,
        "paused_date_episode_ai_control": context.get("ok") is True,
        "independent_native_memberships_available": available.get("ok")
        is True,
    }
    return {
        "from_classification": initial_transient.get("classification"),
        "to_classification": "native_pair_available",
        "available_day_index": day_index,
        "available_date_raw": context.get("expected_date_raw"),
        "native_membership_pair": available,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _independent_assignment_reopened_proof(
    pair: dict[str, object],
    snapshot: dict[str, object],
    battle: dict[str, object],
    *,
    combat_id: int,
    combat_province_id: int,
) -> dict[str, object]:
    base = rejoin_live._assignment_reopened_proof(
        pair,
        snapshot,
        battle,
        combat_id=combat_id,
        combat_province_id=combat_province_id,
    )
    membership = _independent_native_pair_available_proof(pair)
    base_checks = base.get("checks")
    checks = dict(base_checks) if isinstance(base_checks, dict) else {}
    legacy_same_parent_order = checks.pop("native_parent_order", False)
    checks["independent_native_memberships"] = membership.get("ok") is True
    checks["cross_stack_same_coordinator"] = (
        membership.get("parent_relationship")
        == "cross_stack_same_coordinator"
    )
    return base | {
        "native_membership_pair": membership,
        "legacy_same_parent_order_observed": legacy_same_parent_order,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _singleton_requester_parent_cannot_ask_proof(
    observations: list[dict[str, object]],
    membership_transition: dict[str, object],
    *,
    max_assignment_days: int,
) -> dict[str, object]:
    available_day = membership_transition.get("available_day_index")
    typed_available_day = bool(
        isinstance(available_day, int)
        and not isinstance(available_day, bool)
        and 1 <= available_day <= max_assignment_days
    )
    bounded = [
        row
        for row in observations
        if isinstance(row, dict)
        and isinstance(row.get("day_index"), int)
        and not isinstance(row.get("day_index"), bool)
        and typed_available_day
        and row["day_index"] >= available_day
    ]
    evidence: list[dict[str, object]] = []
    all_typed_memberships = bool(bounded)
    all_singleton_parents = bool(bounded)
    all_asking_cleared = bool(bounded)
    all_unassigned = bool(bounded)
    all_anchor_bound_to_old_combat = bool(bounded)
    all_old_combat_active = bool(bounded)
    for row in bounded:
        pair = row.get("pair")
        pair = pair if isinstance(pair, dict) else {}
        rejoin = pair.get("rejoin_frame")
        anchor = pair.get("anchor_frame")
        rejoin = rejoin if isinstance(rejoin, dict) else {}
        anchor = anchor if isinstance(anchor, dict) else {}
        rejoin_rows = rejoin_live._native_rows(rejoin)
        anchor_rows = rejoin_live._native_rows(anchor)
        rejoin_signal = rejoin.get("signal")
        anchor_signal = anchor.get("signal")
        rejoin_signal = (
            rejoin_signal if isinstance(rejoin_signal, dict) else {}
        )
        anchor_signal = (
            anchor_signal if isinstance(anchor_signal, dict) else {}
        )
        rejoin_assignment = rejoin.get("assignment")
        anchor_assignment = anchor.get("assignment")
        rejoin_assignment = (
            rejoin_assignment
            if isinstance(rejoin_assignment, dict)
            else {}
        )
        anchor_assignment = (
            anchor_assignment
            if isinstance(anchor_assignment, dict)
            else {}
        )
        membership = _independent_native_pair_available_proof(pair)
        singleton = len(rejoin_rows) == 1 and len(anchor_rows) == 1
        asking_cleared = (
            rejoin_signal.get("asking_for_help") is False
            and anchor_signal.get("asking_for_help") is False
        )
        unassigned = (
            rejoin_signal.get("assigned_to_help") is False
            and rejoin_assignment.get("assignment_target_province_id") is None
            and rejoin_assignment.get("target_provenance") == "none"
        )
        anchor_bound = (
            anchor_assignment.get("combat_binding_status")
            == "already_in_active_combat"
            and anchor_assignment.get("active_combat_id") == COMBAT_ID
        )
        boundary = row.get("boundary")
        roster = row.get("roster")
        boundary = boundary if isinstance(boundary, dict) else {}
        roster = roster if isinstance(roster, dict) else {}
        old_combat_active = (
            boundary.get("active") is True and roster.get("ok") is True
        )
        all_typed_memberships = (
            all_typed_memberships and membership.get("ok") is True
        )
        all_singleton_parents = all_singleton_parents and singleton
        all_asking_cleared = all_asking_cleared and asking_cleared
        all_unassigned = all_unassigned and unassigned
        all_anchor_bound_to_old_combat = (
            all_anchor_bound_to_old_combat and anchor_bound
        )
        all_old_combat_active = all_old_combat_active and old_combat_active
        evidence.append(
            {
                "day_index": row.get("day_index"),
                "date_raw": (
                    row.get("snapshot", {}).get("date_raw")
                    if isinstance(row.get("snapshot"), dict)
                    else None
                ),
                "rejoin_native_carmy_id": rejoin.get(
                    "selected_native_carmy_id"
                ),
                "rejoin_unit_stack_stored_index": rejoin.get(
                    "unit_stack_stored_index"
                ),
                "rejoin_parent_subunit_count": len(rejoin_rows),
                "rejoin_parent_rows": rejoin_rows,
                "anchor_native_carmy_id": anchor.get(
                    "selected_native_carmy_id"
                ),
                "anchor_unit_stack_stored_index": anchor.get(
                    "unit_stack_stored_index"
                ),
                "anchor_parent_subunit_count": len(anchor_rows),
                "anchor_parent_rows": anchor_rows,
                "rejoin_asking_for_help": rejoin_signal.get(
                    "asking_for_help"
                ),
                "anchor_asking_for_help": anchor_signal.get(
                    "asking_for_help"
                ),
                "rejoin_assigned_to_help": rejoin_signal.get(
                    "assigned_to_help"
                ),
                "rejoin_assignment_target_province_id": (
                    rejoin_assignment.get("assignment_target_province_id")
                ),
                "old_combat_phase_raw": (
                    row.get("battle", {}).get("phase_raw")
                    if isinstance(row.get("battle"), dict)
                    else None
                ),
                "old_combat_phase_day": (
                    row.get("battle", {}).get("phase_day")
                    if isinstance(row.get("battle"), dict)
                    else None
                ),
            }
        )
    expected_count = (
        max_assignment_days - available_day + 1
        if typed_available_day
        else 0
    )
    indices = [row.get("day_index") for row in bounded]
    expected_indices = (
        list(range(available_day, max_assignment_days + 1))
        if typed_available_day
        else []
    )
    checks = {
        "membership_reopened": membership_transition.get("ok") is True,
        "full_post_reopen_bound_observed": bool(bounded)
        and len(bounded) == expected_count
        and indices == expected_indices,
        "every_frame_has_typed_native_memberships": all_typed_memberships,
        "every_candidate_parent_has_one_native_subunit": (
            all_singleton_parents
        ),
        "asking_cleared_for_both_candidates": all_asking_cleared,
        "withdrawn_unit_never_assigned": all_unassigned,
        "anchor_remained_bound_to_old_combat": (
            all_anchor_bound_to_old_combat
        ),
        "old_combat_remained_active_through_bound": all_old_combat_active,
    }
    return {
        "classification": "singleton_requester_parent_cannot_ask",
        "requester_identity_claimed": False,
        "evidence_boundary": (
            "both same-coordinator candidate parents have exactly one native "
            "subunit; no requester identity is stored by the assignment"
        ),
        "static_rule": {
            "exact_build_address": "0x1848310",
            "proven_effect": "parent_subunit_count_le_1_clears_asking",
        },
        "available_day_index": available_day,
        "post_reopen_observation_count": len(bounded),
        "expected_post_reopen_observation_count": expected_count,
        "first_date_raw": evidence[0].get("date_raw") if evidence else None,
        "last_date_raw": evidence[-1].get("date_raw") if evidence else None,
        "daily_evidence": evidence,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _post_retreat_proof(
    snapshot: dict[str, object],
    battle: dict[str, object],
    *,
    expected_date_raw: int,
) -> dict[str, object]:
    try:
        army = rejoin_live._subject_army(snapshot, REJOIN_CUNIT_ID)
        same_side, opposite_side = _active_side_ids(battle)
    except RuntimeError:
        army, same_side, opposite_side = {}, [], []
    checks = {
        "same_date": snapshot.get("date_raw") == expected_date_raw,
        "played_owner_subset": owner_live._played_character_id(snapshot)
        == OWNER_SUBSET_CHARACTER_ID,
        "retreat_semantics": army.get("retreating") is True
        and army.get("move_target_province_id") == RETREAT_TARGET_PROVINCE_ID
        and isinstance(army.get("route_province_ids"), list)
        and army["route_province_ids"]
        and army["route_province_ids"][-1] == RETREAT_TARGET_PROVINCE_ID,
        "old_combat_identity": battle.get("status") == "available"
        and battle.get("battle_transition_ready") is True
        and battle.get("combat_id") == COMBAT_ID
        and battle.get("finalized") is False,
        "owner_subset_removed": same_side == [ANCHOR_CUNIT_ID],
        "opposite_unchanged": opposite_side == [OPPOSITE_CUNIT_ID],
    }
    return {
        "subject_army": army,
        "same_side": same_side,
        "opposite_side": opposite_side,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _ai_control_proof(
    snapshot: dict[str, object],
    pair: dict[str, object],
    battle: dict[str, object],
    terminal: dict[str, object],
    *,
    expected_date_raw: int,
    requested_cursor: int | None,
    expected_episode_run_id: str | None = None,
) -> dict[str, object]:
    try:
        army = rejoin_live._subject_army(snapshot, REJOIN_CUNIT_ID)
    except RuntimeError:
        army = {}
    roster = _waiting_old_combat_proof(battle)
    boundary = rejoin_live._terminal_boundary_proof(
        terminal,
        battle,
        combat_id=COMBAT_ID,
        requested_cursor=requested_cursor,
    )
    episode = snapshot.get("episode_run_id")
    episode = episode if isinstance(episode, str) and episode else ""
    expected_episode = expected_episode_run_id or episode
    context = _daily_ai_context_proof(
        snapshot,
        expected_date_raw=expected_date_raw,
        expected_episode_run_id=expected_episode,
    )
    transient = _retreating_membership_transient_proof(snapshot, pair)
    independent_membership = _independent_native_pair_available_proof(pair)
    pair_available = independent_membership.get("ok") is True
    membership_classification = (
        "native_pair_available"
        if pair_available
        else transient["classification"]
        if transient.get("ok") is True
        else "invalid"
    )
    checks = {
        "paused_date_episode_ai_control": context.get("ok") is True,
        "native_membership_state_typed": pair_available
        or transient.get("ok") is True,
        "old_combat_waiting": roster.get("ok") is True,
        "terminal_active": boundary.get("active") is True,
    }
    return {
        "subject_army": army,
        "pair": pair,
        "daily_context": context,
        "membership_classification": membership_classification,
        "native_pair_available": pair_available,
        "independent_native_membership_pair": independent_membership,
        "retreating_membership_transient": transient,
        "roster": roster,
        "terminal_boundary": boundary,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _waiting_old_combat_proof(battle: dict[str, object]) -> dict[str, object]:
    try:
        same_side, opposite_side = _active_side_ids(battle)
    except RuntimeError:
        same_side, opposite_side = [], []
    phase = battle.get("phase_raw")
    winner = battle.get("winner_raw")
    phase_winner_valid = bool(
        (phase in {0, 1} and winner == -1)
        or (phase == 2 and winner in {0, 1})
    )
    checks = {
        "active_identity": battle.get("status") == "available"
        and battle.get("battle_transition_ready") is True
        and battle.get("combat_id") == COMBAT_ID
        and battle.get("finalized") is False,
        "phase_winner_valid": phase_winner_valid,
        "withdrawn_absent": same_side == [ANCHOR_CUNIT_ID],
        "opposite_unchanged": opposite_side == [OPPOSITE_CUNIT_ID],
    }
    return {
        "same_side": same_side,
        "opposite_side": opposite_side,
        "phase_raw": phase,
        "winner_raw": winner,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_managed_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    name: str,
    fixture: bool,
    body: Callable[
        [GameplayBridgeService, NativeHeadlessGameplayDriver, threading.Event, dict[str, object]],
        dict[str, object],
    ],
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    driver_closed = False
    readiness: dict[str, object] | None = None
    body_result: dict[str, object] | None = None
    primary_error: str | None = None

    def supervise() -> None:
        try:
            if fixture:
                session_state["report"] = owner_live._fixture_native_session(
                    spec=spec,
                    config=config,
                    timeout=timeout + 90.0,
                    stop_event=stop_event,
                )
            else:
                session_state["report"] = native_session(
                    spec,
                    timeout_seconds=timeout + 90.0,
                    native_bridge=config,
                    input_stream=None,
                    output_stream=None,
                    poll_interval_seconds=0.05,
                    cold_start_checkpoint=False,
                    stop_event=stop_event,
                )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        if not fixture:
            owner_live.verify_profile(spec)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(target=supervise, name=name, daemon=False)
        thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=True,
        )
        body_result = body(service, driver, session_done, session_state)
        if body_result.get("ok") is not True:
            raise RuntimeError(
                str(body_result.get("error") or "managed stage body failed")
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_event.set()
        if thread is not None:
            thread.join()
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = detail if primary_error is None else (
                    f"{primary_error}; driver close failed: {detail}"
                )
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=0.0,
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "managed cleanup was not proven"
        )
    return {
        "ok": bool(
            primary_error is None
            and body_result
            and body_result.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "fixture_profile": fixture,
        "readiness": readiness,
        "body": body_result,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _run_retreat_checkpoint_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    postcondition_timeout: float,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        _session_done: threading.Event,
        _session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        rejoin_live._assert_paused(initial)
        initial_date = rejoin_live._snapshot_date(initial)
        capabilities = driver.capabilities()
        exact_build = rejoin_live._exact_build_proof(
            capabilities, owner_live._sha256_file(spec.game_exe)
        )
        capability = rejoin_live._capability_proof(capabilities)
        if not (exact_build.get("ok") is True and capability.get("ok") is True):
            raise RuntimeError("retreat stage exact-build/capability proof failed")
        if owner_live._played_character_id(initial) != OWNER_SUBSET_CHARACTER_ID:
            raise RuntimeError("retreat stage did not bind Character 36108")
        control = service.query_battle_control_snapshot_v1(
            REJOIN_CUNIT_ID,
            expected_revision=rejoin_live._snapshot_revision(initial),
        )
        if not owner_live._validate_owner_subset_frame(control):
            raise RuntimeError("retreat stage lost owner-subset control frame")
        pre_battle = rejoin_live._battle_frame(
            service.query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=rejoin_live._snapshot_revision(initial),
            )
        )
        preview = service.preview_active_combat_retreat_v1(
            REJOIN_CUNIT_ID,
            RETREAT_TARGET_PROVINCE_ID,
            expected_revision=rejoin_live._snapshot_revision(initial),
        )
        target_preview = preview.get("target_preview")
        target_preview = (
            target_preview if isinstance(target_preview, dict) else {}
        )
        token = target_preview.get("candidate_token")
        if not (
            preview.get("status") == "available"
            and preview.get("action_ready") is True
            and isinstance(token, str)
            and bool(token)
        ):
            raise RuntimeError("retreat stage preview was not action-ready")
        order = service.order_active_combat_retreat_v1(
            REJOIN_CUNIT_ID,
            expected_revision=int(preview["source_binding"]["revision"]),
            expected_combat_id=COMBAT_ID,
            expected_side_index=owner_live.EXPECTED_SIDE_INDEX,
            expected_scope="owner_subset",
            target_province_id=RETREAT_TARGET_PROVINCE_ID,
            candidate_token=token,
        )
        if not (
            order.get("accepted") is True
            and order.get("status") == "accepted_verification_pending"
        ):
            raise RuntimeError("retreat stage order was not accepted")
        deadline = time.monotonic() + postcondition_timeout
        snapshots: list[dict[str, object]] = []
        post_snapshot: dict[str, object] | None = None
        post_battle: dict[str, object] | None = None
        proof: dict[str, object] | None = None
        while time.monotonic() < deadline:
            candidate_snapshot = service.snapshot()
            snapshots.append(
                retreat_live._compact_snapshot(
                    candidate_snapshot, REJOIN_CUNIT_ID
                )
            )
            if retreat_live._retreat_semantic_ready(
                candidate_snapshot,
                REJOIN_CUNIT_ID,
                RETREAT_TARGET_PROVINCE_ID,
            ):
                candidate_battle = rejoin_live._battle_frame(
                    service.query_battle_transition_v1(
                        COMBAT_ID,
                        expected_revision=rejoin_live._snapshot_revision(
                            candidate_snapshot
                        ),
                    )
                )
                candidate_proof = _post_retreat_proof(
                    candidate_snapshot,
                    candidate_battle,
                    expected_date_raw=initial_date,
                )
                if candidate_proof.get("ok") is True:
                    post_snapshot = candidate_snapshot
                    post_battle = candidate_battle
                    proof = candidate_proof
                    break
            time.sleep(0.05)
        if post_snapshot is None or post_battle is None or proof is None:
            raise RuntimeError("retreat stage postcondition timed out")
        save_result = service.save_checkpoint(
            expected_revision=rejoin_live._snapshot_revision(post_snapshot)
        )
        checkpoint = owner_live._checkpoint_identity(
            owner_live._checkpoint_path(spec)
        )
        return {
            "ok": True,
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "initial_snapshot": initial,
            "initial_battle_control": control,
            "pre_lifecycle": pre_battle,
            "preview": preview,
            "order": order,
            "post_snapshots": snapshots,
            "post_snapshot": post_snapshot,
            "post_battle": post_battle,
            "post_retreat_proof": proof,
            "save_result": save_result,
            "checkpoint": checkpoint,
            "date_raw": initial_date,
        }

    return _run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-owner-subset-return-retreat-stage",
        fixture=False,
        body=body,
    )


def _validate_return_anchor(snapshot: object) -> bool:
    if not isinstance(snapshot, dict):
        return False
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return False
    matches = [
        war
        for war in wars
        if isinstance(war, dict) and war.get("war_id") == 16_777_290
    ]
    return bool(
        len(matches) == 1
        and matches[0].get("player_side") == "defender"
        and matches[0].get("primary_opponent_character_id")
        == ORIGINAL_CHARACTER_ID
        and matches[0].get("enemy_primary_default_raise_province_id")
        == RETURN_CHARACTER_ANCHOR_PROVINCE_ID
    )


def _run_return_seed_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    seed_timeout: float,
    expected_date_raw: int,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        _driver: NativeHeadlessGameplayDriver,
        session_done: threading.Event,
        session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        if not (
            owner_live._played_character_id(initial)
            == OWNER_SUBSET_CHARACTER_ID
            and initial.get("date_raw") == expected_date_raw
            and _validate_return_anchor(initial)
        ):
            raise RuntimeError("return seed initial identity/anchor differs")
        initial_battle = rejoin_live._battle_frame(
            service.query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=rejoin_live._snapshot_revision(initial),
            )
        )
        initial_proof = _post_retreat_proof(
            initial,
            initial_battle,
            expected_date_raw=expected_date_raw,
        )
        if initial_proof.get("ok") is not True:
            raise RuntimeError("return seed lost post-retreat state")

        debug_log = spec.profile_dir / "logs" / "debug.log"
        switch_offset = owner_live._debug_log_offset(debug_log)
        switch_effect = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _return_switch_effect()
        )
        deadline = time.monotonic() + seed_timeout
        switched: dict[str, object] | None = None
        switch_marker_observed = False
        while time.monotonic() < deadline:
            switch_marker_observed = owner_live._debug_marker_observed(
                debug_log, RETURN_SWITCH_MARKER, offset=switch_offset
            )
            candidate = service.snapshot()
            if (
                switch_marker_observed
                and owner_live._played_character_id(candidate)
                == ORIGINAL_CHARACTER_ID
            ):
                switched = candidate
                break
            if session_done.is_set():
                raise RuntimeError(
                    str(
                        session_state.get("error")
                        or "return seed session ended before switch"
                    )
                )
            time.sleep(0.05)
        if switched is None or switched.get("date_raw") != expected_date_raw:
            raise RuntimeError("return switch marker/player/date was not observed")
        noop_after_switch = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), owner_live.SEED_NOOP_INBOX
        )
        poll_driver = DataModGameplayDriver(
            spec.profile_dir,
            request_timeout_seconds=seed_timeout,
            poll_interval_seconds=0.05,
        )
        switch_polls = [poll_driver.take_snapshot(), poll_driver.take_snapshot()]
        if not (
            len({row.get("request_id") for row in switch_polls}) == 2
            and all(
                row.get("player_id") == ORIGINAL_CHARACTER_ID
                for row in switch_polls
            )
            and switch_polls[0].get("total_days")
            == switch_polls[1].get("total_days")
        ):
            raise RuntimeError("return switch two-poll proof was not stable")

        clear_offset = owner_live._debug_log_offset(debug_log)
        clear_effect = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _return_clear_effect()
        )
        clear_deadline = time.monotonic() + seed_timeout
        clear_marker_observed = False
        while time.monotonic() < clear_deadline:
            clear_marker_observed = owner_live._debug_marker_observed(
                debug_log, RETURN_CLEAR_MARKER, offset=clear_offset
            )
            if clear_marker_observed:
                break
            if session_done.is_set():
                raise RuntimeError(
                    str(
                        session_state.get("error")
                        or "return seed session ended before guard clear"
                    )
                )
            time.sleep(0.05)
        if not clear_marker_observed:
            raise RuntimeError("return seed guard clear marker was not observed")
        clear_polls = [poll_driver.take_snapshot(), poll_driver.take_snapshot()]
        if not (
            len({row.get("request_id") for row in clear_polls}) == 2
            and all(
                row.get("player_id") == ORIGINAL_CHARACTER_ID
                for row in clear_polls
            )
            and clear_polls[0].get("total_days")
            == clear_polls[1].get("total_days")
        ):
            raise RuntimeError("return clear two-poll proof was not stable")
        final_noop = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), owner_live.SEED_NOOP_INBOX
        )
        final = service.snapshot()
        if not (
            owner_live._played_character_id(final) == ORIGINAL_CHARACTER_ID
            and final.get("date_raw") == expected_date_raw
        ):
            raise RuntimeError("return seed identity/date drifted before save")
        final_battle = rejoin_live._battle_frame(
            service.query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=rejoin_live._snapshot_revision(final),
            )
        )
        final_roster = _waiting_old_combat_proof(final_battle)
        final_army = rejoin_live._subject_army(final, REJOIN_CUNIT_ID)
        ai_control_visible = final_army.get("controllable") is False
        if not (final_roster.get("ok") is True and ai_control_visible):
            raise RuntimeError("return seed did not release player army control")
        save_result = service.save_checkpoint(
            expected_revision=rejoin_live._snapshot_revision(final)
        )
        checkpoint = owner_live._checkpoint_identity(
            owner_live._checkpoint_path(spec)
        )
        return {
            "ok": True,
            "initial_snapshot": initial,
            "initial_battle": initial_battle,
            "initial_post_retreat_proof": initial_proof,
            "switched_snapshot": switched,
            "final_snapshot": final,
            "final_battle": final_battle,
            "final_roster": final_roster,
            "ai_control_visible": ai_control_visible,
            "inbox_protocol": {
                "switch_marker": RETURN_SWITCH_MARKER,
                "switch_marker_observed": switch_marker_observed,
                "clear_marker": RETURN_CLEAR_MARKER,
                "clear_marker_observed": clear_marker_observed,
                "switch_effect": switch_effect,
                "noop_after_switch": noop_after_switch,
                "clear_effect": clear_effect,
                "final_noop": final_noop,
                "switch_polls": switch_polls,
                "clear_polls": clear_polls,
            },
            "save_result": save_result,
            "checkpoint": checkpoint,
            "date_raw": expected_date_raw,
        }

    try:
        return _run_managed_session(
            spec=spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            name="xar-owner-subset-return-seed-stage",
            fixture=True,
            body=body,
        )
    finally:
        owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), owner_live.SEED_NOOP_INBOX
        )


def _run_ai_canonical_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    expected_date_raw: int,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        _session_done: threading.Event,
        _session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        exact_build = rejoin_live._exact_build_proof(
            driver.capabilities(), owner_live._sha256_file(spec.game_exe)
        )
        capability = rejoin_live._capability_proof(driver.capabilities())
        if not (exact_build.get("ok") is True and capability.get("ok") is True):
            raise RuntimeError("AI canonical exact-build/capability proof failed")
        snapshot, pair, battle, terminal, retries = (
            rejoin_live._query_paused_observation_bundle(
                service,
                initial,
                combat_id=COMBAT_ID,
                terminal_cursor=None,
            )
        )
        control = _ai_control_proof(
            snapshot,
            pair,
            battle,
            terminal,
            expected_date_raw=expected_date_raw,
            requested_cursor=None,
        )
        if control.get("ok") is not True:
            return {
                "ok": False,
                "error": "production reload did not restore native AI control",
                "initial_snapshot": initial,
                "snapshot": snapshot,
                "pair": pair,
                "battle": battle,
                "terminal": terminal,
                "observation_retries": retries,
                "ai_control_proof": control,
                "exact_build_proof": exact_build,
                "capability_proof": capability,
            }
        save_result = service.save_checkpoint(
            expected_revision=rejoin_live._snapshot_revision(snapshot)
        )
        checkpoint = owner_live._checkpoint_identity(
            owner_live._checkpoint_path(spec)
        )
        return {
            "ok": True,
            "initial_snapshot": initial,
            "snapshot": snapshot,
            "pair": pair,
            "battle": battle,
            "terminal": terminal,
            "observation_retries": retries,
            "ai_control_proof": control,
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "save_result": save_result,
            "checkpoint": checkpoint,
            "date_raw": expected_date_raw,
        }

    return _run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-owner-subset-ai-canonical-stage",
        fixture=False,
        body=body,
    )


def _final_mutation_boundary(commands: list[str]) -> dict[str, object]:
    checks = {
        "only_daily_advance_and_save": all(
            command in {"life-advance", "save-checkpoint"}
            for command in commands
        ),
        "at_least_one_daily_advance": commands.count("life-advance") >= 1,
        "two_checkpoint_saves": commands.count("save-checkpoint") == 2,
    }
    return {
        "commands": list(commands),
        "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        "forbidden_native_calls_invoked": [],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_ai_assignment_sequence(
    service: GameplayBridgeService,
    *,
    wait_after_advance: Callable[[], dict[str, object]],
    max_assignment_days: int,
    max_eta_days: int,
    expected_date_raw: int,
) -> dict[str, object]:
    commands: list[str] = []
    advances: list[dict[str, object]] = []
    observations: list[dict[str, object]] = []
    terminal_boundaries: list[dict[str, object]] = []
    initial = service.snapshot()
    snapshot, pair, battle, terminal, retries = (
        rejoin_live._query_paused_observation_bundle(
            service,
            initial,
            combat_id=COMBAT_ID,
            terminal_cursor=None,
        )
    )
    initial_control = _ai_control_proof(
        snapshot,
        pair,
        battle,
        terminal,
        expected_date_raw=expected_date_raw,
        requested_cursor=None,
    )
    initial_episode = snapshot.get("episode_run_id")
    initial_transient = initial_control.get(
        "retreating_membership_transient"
    )
    initial_transient = (
        initial_transient if isinstance(initial_transient, dict) else {}
    )
    if not (
        initial_control.get("ok") is True
        and isinstance(initial_episode, str)
        and bool(initial_episode)
        and initial_transient.get("ok") is True
    ):
        return {
            "ok": False,
            "outcome": "final_reload_retreating_ai_transient_unavailable",
            "initial_snapshot": initial,
            "diagnostic_frame": {
                "snapshot": snapshot,
                "pair": pair,
                "battle": battle,
                "terminal": terminal,
                "observation_retries": retries,
                "ai_control_proof": initial_control,
                "required_membership_classification": (
                    "retreating_subunit_backlink_mismatch"
                ),
            },
            "commands": commands,
            "advances": advances,
            "readiness_gates": {
                "ai_control_live_ready": initial_control.get("ok") is True,
                "retreating_membership_transient_live_ready": False,
                "native_pair_reopened_live_ready": False,
                "assignment_reopened_aligned_eta_live_ready": False,
                "same_combat_rejoin_live_ready": False,
            },
        }
    combat_province_id = battle.get("province_id")
    if (
        isinstance(combat_province_id, bool)
        or not isinstance(combat_province_id, int)
        or combat_province_id <= 0
    ):
        raise RuntimeError("final stage old combat lacks Province identity")
    baseline_battle = battle
    cursor = initial_control["terminal_boundary"].get("next_cursor")
    membership_observations: list[dict[str, object]] = []
    membership_transition: dict[str, object] | None = None

    def diagnostic(
        outcome: str,
        *,
        stage: str,
        day_index: int,
        frame_snapshot: dict[str, object],
        frame_pair: dict[str, object],
        frame_battle: dict[str, object],
        frame_terminal: dict[str, object],
        boundary: dict[str, object],
        roster: dict[str, object] | None,
        context: dict[str, object] | None,
        frame_retries: list[dict[str, object]],
        assignment: dict[str, object] | None = None,
        assigned_checkpoint: dict[str, object] | None = None,
        structural_classification: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return {
            "ok": False,
            "outcome": outcome,
            "initial_snapshot": initial,
            "initial_ai_control_proof": initial_control,
            "initial_retreating_membership_transient": initial_transient,
            "baseline_battle": baseline_battle,
            "native_pair_reopened_proof": membership_transition,
            "structural_assignment_blocker": structural_classification,
            "assignment_proof": assignment,
            "assigned_checkpoint": assigned_checkpoint,
            "diagnostic_frame": {
                "stage": stage,
                "day_index": day_index,
                "snapshot": frame_snapshot,
                "pair": frame_pair,
                "battle": frame_battle,
                "terminal": frame_terminal,
                "boundary": boundary,
                "roster": roster,
                "daily_context": context,
                "observation_retries": frame_retries,
            },
            "membership_observations": membership_observations,
            "observations": observations,
            "terminal_boundaries": terminal_boundaries,
            "commands": list(commands),
            "advances": advances,
            "readiness_gates": {
                "ai_control_live_ready": True,
                "retreating_membership_transient_live_ready": True,
                "native_pair_reopened_live_ready": bool(
                    membership_transition
                    and membership_transition.get("ok") is True
                ),
                "assignment_reopened_aligned_eta_live_ready": False,
                "same_combat_rejoin_live_ready": False,
            },
        }

    assignment: dict[str, object] | None = None
    assigned_battle: dict[str, object] | None = None
    for day_index in range(max_assignment_days + 1):
        if day_index > 0:
            snapshot, pair, battle, terminal, retries = (
                rejoin_live._query_paused_observation_bundle(
                    service,
                    snapshot,
                    combat_id=COMBAT_ID,
                    terminal_cursor=cursor,
                )
            )
        context = _daily_ai_context_proof(
            snapshot,
            expected_date_raw=(
                expected_date_raw + len(advances) * ONE_GAME_DAY_RAW
            ),
            expected_episode_run_id=initial_episode,
        )
        roster = _waiting_old_combat_proof(battle)
        boundary = rejoin_live._terminal_boundary_proof(
            terminal,
            battle,
            combat_id=COMBAT_ID,
            requested_cursor=(None if day_index == 0 else cursor),
        )
        transient = _retreating_membership_transient_proof(snapshot, pair)
        independent_membership = _independent_native_pair_available_proof(pair)
        pair_available = independent_membership.get("ok") is True
        membership_classification = (
            "native_pair_available"
            if pair_available
            else transient.get("classification")
            if transient.get("ok") is True
            else "invalid"
        )
        membership_observations.append(
            {
                "day_index": day_index,
                "date_raw": snapshot.get("date_raw"),
                "classification": membership_classification,
                "daily_context": context,
                "retreating_transient": transient,
                "independent_native_memberships_available": pair_available,
                "legacy_same_parent_order_ready": pair.get(
                    "available_order_ready"
                ),
                "independent_native_membership_pair": independent_membership,
                "pair": pair,
            }
        )
        observations.append(
            {
                "stage": (
                    "membership_reopen"
                    if membership_transition is None
                    else "assignment"
                ),
                "day_index": day_index,
                "snapshot": snapshot,
                "pair": pair,
                "battle": battle,
                "terminal": terminal,
                "boundary": boundary,
                "roster": roster,
                "daily_context": context,
                "membership_classification": membership_classification,
                "retreating_transient": transient,
                "independent_native_membership_pair": independent_membership,
                "observation_retries": retries,
            }
        )
        terminal_boundaries.append(
            {
                "stage": (
                    "membership_reopen"
                    if membership_transition is None
                    else "assignment"
                ),
                "day_index": day_index,
                **boundary,
            }
        )
        if boundary.get("terminal_event") is True:
            return diagnostic(
                (
                    "terminal_before_native_pair_available"
                    if membership_transition is None
                    else "terminal_before_assignment"
                ),
                stage=(
                    "membership_reopen"
                    if membership_transition is None
                    else "assignment"
                ),
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
            )
        if context.get("ok") is not True:
            return diagnostic(
                "daily_context_drift_before_assignment",
                stage=(
                    "membership_reopen"
                    if membership_transition is None
                    else "assignment"
                ),
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
            )
        if boundary.get("active") is not True or roster.get("ok") is not True:
            return diagnostic(
                "old_combat_drift_before_assignment",
                stage=(
                    "membership_reopen"
                    if membership_transition is None
                    else "assignment"
                ),
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
            )
        cursor = boundary.get("next_cursor")
        if membership_transition is None:
            if pair_available:
                membership_transition = _native_pair_reopened_proof(
                    initial_transient,
                    pair,
                    context,
                    day_index=day_index,
                )
                if membership_transition.get("ok") is not True:
                    return diagnostic(
                        "native_pair_reopen_postcondition_drift",
                        stage="membership_reopen",
                        day_index=day_index,
                        frame_snapshot=snapshot,
                        frame_pair=pair,
                        frame_battle=battle,
                        frame_terminal=terminal,
                        boundary=boundary,
                        roster=roster,
                        context=context,
                        frame_retries=retries,
                    )
            elif transient.get("ok") is not True:
                return diagnostic(
                    "ai_membership_transition_drift",
                    stage="membership_reopen",
                    day_index=day_index,
                    frame_snapshot=snapshot,
                    frame_pair=pair,
                    frame_battle=battle,
                    frame_terminal=terminal,
                    boundary=boundary,
                    roster=roster,
                    context=context,
                    frame_retries=retries,
                )
        elif not pair_available:
            return diagnostic(
                "native_pair_regressed_before_assignment",
                stage="assignment",
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
            )
        candidate: dict[str, object] = {"ok": False}
        if membership_transition is not None:
            candidate = _independent_assignment_reopened_proof(
                pair,
                snapshot,
                battle,
                combat_id=COMBAT_ID,
                combat_province_id=combat_province_id,
            )
        if candidate.get("ok") is True:
            assignment = candidate
            assigned_battle = battle
            break
        if day_index == max_assignment_days:
            structural = (
                _singleton_requester_parent_cannot_ask_proof(
                    observations,
                    membership_transition,
                    max_assignment_days=max_assignment_days,
                )
                if membership_transition is not None
                else None
            )
            return diagnostic(
                (
                    "native_pair_not_available_within_bound"
                    if membership_transition is None
                    else "singleton_requester_parent_cannot_ask"
                    if structural is not None
                    and structural.get("ok") is True
                    else "assignment_not_observed_within_bound"
                ),
                stage=(
                    "membership_reopen"
                    if membership_transition is None
                    else "assignment"
                ),
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
                structural_classification=structural,
            )
        snapshot, advance = rejoin_live._advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
    if assignment is None or assigned_battle is None:
        raise RuntimeError("assignment loop ended without typed proof")
    assigned_date = rejoin_live._snapshot_date(snapshot)
    eta = assignment.get("assignment_eta_date_raw")
    if (
        isinstance(eta, bool)
        or not isinstance(eta, int)
        or not assigned_date < eta
        or eta > assigned_date + max_eta_days * ONE_GAME_DAY_RAW
    ):
        raise RuntimeError("assignment ETA is outside final stage bound")
    assigned_checkpoint = rejoin_live._archive_checkpoint(
        service.save_checkpoint(
            expected_revision=rejoin_live._snapshot_revision(snapshot)
        ),
        archive_name=ASSIGNED_ARCHIVE_NAME,
        expected_date_raw=assigned_date,
    )
    commands.append("save-checkpoint")
    snapshot = service.snapshot()
    immediately_before = assigned_battle

    joined_battle: dict[str, object] | None = None
    join_proof: dict[str, object] | None = None
    for day_index in range(1, max_eta_days + 1):
        pre_eta_context = _daily_ai_context_proof(
            snapshot,
            expected_date_raw=(
                expected_date_raw + len(advances) * ONE_GAME_DAY_RAW
            ),
            expected_episode_run_id=initial_episode,
        )
        if pre_eta_context.get("ok") is not True:
            return diagnostic(
                "daily_context_drift_before_eta_advance",
                stage="eta",
                day_index=day_index - 1,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=immediately_before,
                frame_terminal=terminal,
                boundary=boundary,
                roster=_waiting_old_combat_proof(immediately_before),
                context=pre_eta_context,
                frame_retries=[],
                assignment=assignment,
                assigned_checkpoint=assigned_checkpoint,
            )
        if rejoin_live._snapshot_date(snapshot) >= eta:
            return diagnostic(
                "rejoin_not_observed_by_eta",
                stage="eta",
                day_index=day_index - 1,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=immediately_before,
                frame_terminal=terminal,
                boundary=boundary,
                roster=_waiting_old_combat_proof(immediately_before),
                context=pre_eta_context,
                frame_retries=[],
                assignment=assignment,
                assigned_checkpoint=assigned_checkpoint,
            )
        snapshot, advance = rejoin_live._advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
        snapshot, pair, battle, terminal, retries = (
            rejoin_live._query_paused_observation_bundle(
                service,
                snapshot,
                combat_id=COMBAT_ID,
                terminal_cursor=cursor,
            )
        )
        boundary = rejoin_live._terminal_boundary_proof(
            terminal,
            battle,
            combat_id=COMBAT_ID,
            requested_cursor=cursor,
        )
        context = _daily_ai_context_proof(
            snapshot,
            expected_date_raw=(
                expected_date_raw + len(advances) * ONE_GAME_DAY_RAW
            ),
            expected_episode_run_id=initial_episode,
        )
        roster = _waiting_old_combat_proof(battle)
        observations.append(
            {
                "stage": "eta",
                "day_index": day_index,
                "snapshot": snapshot,
                "pair": pair,
                "battle": battle,
                "terminal": terminal,
                "boundary": boundary,
                "roster": roster,
                "daily_context": context,
                "observation_retries": retries,
            }
        )
        terminal_boundaries.append(
            {"stage": "eta", "day_index": day_index, **boundary}
        )
        if boundary.get("terminal_event") is True:
            return diagnostic(
                "terminal_before_rejoin",
                stage="eta",
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
                assignment=assignment,
                assigned_checkpoint=assigned_checkpoint,
            )
        if context.get("ok") is not True:
            return diagnostic(
                "daily_context_drift_before_rejoin",
                stage="eta",
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
                assignment=assignment,
                assigned_checkpoint=assigned_checkpoint,
            )
        if boundary.get("active") is not True:
            return diagnostic(
                "terminal_boundary_drift_before_rejoin",
                stage="eta",
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
                assignment=assignment,
                assigned_checkpoint=assigned_checkpoint,
            )
        cursor = boundary.get("next_cursor")
        participants = [
            *(battle.get("attacker_public_cunit_ids_in_stored_order") or []),
            *(battle.get("defender_public_cunit_ids_in_stored_order") or []),
        ]
        if REJOIN_CUNIT_ID in participants:
            candidate_join = rejoin_live._same_combat_rejoin_proof(
                baseline_battle,
                immediately_before,
                battle,
                pair,
                snapshot,
                combat_id=COMBAT_ID,
                combat_province_id=combat_province_id,
                side_index=owner_live.EXPECTED_SIDE_INDEX,
            )
            if candidate_join.get("ok") is not True:
                return diagnostic(
                    "same_combat_join_postcondition_drift",
                    stage="eta",
                    day_index=day_index,
                    frame_snapshot=snapshot,
                    frame_pair=pair,
                    frame_battle=battle,
                    frame_terminal=terminal,
                    boundary=boundary,
                    roster=roster,
                    context=context,
                    frame_retries=retries,
                    assignment=assignment,
                    assigned_checkpoint=assigned_checkpoint,
                )
            joined_battle = battle
            join_proof = candidate_join
            break
        if roster.get("ok") is not True:
            return diagnostic(
                "old_combat_roster_drift_before_rejoin",
                stage="eta",
                day_index=day_index,
                frame_snapshot=snapshot,
                frame_pair=pair,
                frame_battle=battle,
                frame_terminal=terminal,
                boundary=boundary,
                roster=roster,
                context=context,
                frame_retries=retries,
                assignment=assignment,
                assigned_checkpoint=assigned_checkpoint,
            )
        immediately_before = battle
    if joined_battle is None or join_proof is None:
        raise RuntimeError("ETA loop ended without rejoin proof")
    joined_date = rejoin_live._snapshot_date(snapshot)
    joined_checkpoint = rejoin_live._archive_checkpoint(
        service.save_checkpoint(
            expected_revision=rejoin_live._snapshot_revision(snapshot)
        ),
        archive_name=JOINED_ARCHIVE_NAME,
        expected_date_raw=joined_date,
    )
    commands.append("save-checkpoint")
    boundary_proof = _final_mutation_boundary(commands)
    assertions = {
        "ai_control_at_final_reload": initial_control.get("ok") is True,
        "initial_retreating_membership_transient": initial_transient.get("ok")
        is True,
        "native_pair_reopened_after_retreat": bool(
            membership_transition
            and membership_transition.get("ok") is True
        ),
        "native_assignment_aligned_eta": assignment.get("ok") is True,
        "same_combat_tail_rejoin": join_proof.get("ok") is True,
        "joined_by_eta": joined_date <= eta,
        "all_advances_exactly_one_day": bool(advances)
        and all(row.get("ok") is True for row in advances),
        "assigned_checkpoint_saved": assigned_checkpoint.get("ok") is True,
        "joined_checkpoint_saved": joined_checkpoint.get("ok") is True,
        "production_mutation_boundary": boundary_proof.get("ok") is True,
    }
    return {
        "ok": all(assertions.values()),
        "outcome": "ai_assignment_same_combat_rejoin",
        "initial_snapshot": initial,
        "initial_ai_control_proof": initial_control,
        "initial_retreating_membership_transient": initial_transient,
        "baseline_battle": baseline_battle,
        "native_pair_reopened_proof": membership_transition,
        "assignment_proof": assignment,
        "assigned_date_raw": assigned_date,
        "assignment_eta_date_raw": eta,
        "assigned_checkpoint": assigned_checkpoint,
        "joined_date_raw": joined_date,
        "joined_battle": joined_battle,
        "join_proof": join_proof,
        "joined_checkpoint": joined_checkpoint,
        "membership_observations": membership_observations,
        "observations": observations,
        "terminal_boundaries": terminal_boundaries,
        "commands": commands,
        "advances": advances,
        "mutation_boundary_proof": boundary_proof,
        "assertions": assertions,
        "readiness_gates": {
            "ai_control_live_ready": initial_control.get("ok") is True,
            "retreating_membership_transient_live_ready": initial_transient.get(
                "ok"
            )
            is True,
            "native_pair_reopened_live_ready": bool(
                membership_transition
                and membership_transition.get("ok") is True
            ),
            "assignment_reopened_aligned_eta_live_ready": assignment.get("ok")
            is True,
            "same_combat_rejoin_live_ready": join_proof.get("ok") is True,
        },
    }


def _run_final_assignment_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    expected_date_raw: int,
    max_assignment_days: int,
    max_eta_days: int,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        session_done: threading.Event,
        session_state: dict[str, object],
    ) -> dict[str, object]:
        before_capabilities = driver.capabilities()
        exact_build = rejoin_live._exact_build_proof(
            before_capabilities, owner_live._sha256_file(spec.game_exe)
        )
        capability = rejoin_live._capability_proof(before_capabilities)
        if not (exact_build.get("ok") is True and capability.get("ok") is True):
            raise RuntimeError("final exact-build/capability proof failed")

        def wait_after_advance() -> dict[str, object]:
            _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=readiness_timeout,
                stable_seconds=0.0,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                allow_terminal=True,
            )
            return service.snapshot()

        sequence = _run_ai_assignment_sequence(
            service,
            wait_after_advance=wait_after_advance,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
            expected_date_raw=expected_date_raw,
        )
        same_process = rejoin_live._same_process_proof(
            before_capabilities, driver.capabilities()
        )
        return {
            "ok": bool(
                sequence.get("ok") is True
                and same_process.get("ok") is True
            ),
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "same_process_proof": same_process,
            "sequence": sequence,
            "error": (
                None
                if sequence.get("ok") is True
                else str(sequence.get("outcome") or "final sequence failed")
            ),
        }

    return _run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-owner-subset-ai-assignment-final-stage",
        fixture=False,
        body=body,
    )


def _target_root(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-owner-subset-ai-reassignment-" + uuid.uuid4().hex
    )


def _cleanup_root(
    root: Path,
    *,
    nonce: str,
    retain: bool,
    all_sessions_clean: bool,
) -> dict[str, object]:
    target = root.resolve()
    if retain:
        return {
            "attempted": False,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": "--retain-state prevents cleanup qualification",
        }
    if not all_sessions_clean:
        return {
            "attempted": False,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": "a managed stage cleanup was not proven",
        }
    marker = target / _ROOT_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == "xar_owner_subset_ai_reassignment"
            and payload.get("nonce") == nonce
        ):
            raise AgentError("AI reassignment root marker differs")
        owner_live.ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "ok": removed,
            "path": str(target),
            "reason": None if removed else "fixture root still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": f"{type(error).__name__}: {error}",
        }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    timeout = owner_live._positive_seconds(args.timeout, "timeout")
    readiness_timeout = owner_live._positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    seed_timeout = owner_live._positive_seconds(args.seed_timeout, "seed_timeout")
    postcondition_timeout = owner_live._positive_seconds(
        args.postcondition_timeout, "postcondition_timeout"
    )
    max_assignment_days = rejoin_live._positive_int(
        args.max_assignment_days, "max_assignment_days"
    )
    max_eta_days = rejoin_live._positive_int(args.max_eta_days, "max_eta_days")
    expected_sha = owner_live._expected_sha256(
        args.expected_battle_save_sha256
    )
    source_state = args.source_state_dir.expanduser().resolve()
    source_profile = source_state / "profile"
    game_dir = args.game_dir.expanduser().resolve()
    root = _target_root(args.state_dir)
    output = args.output.expanduser().resolve()
    if root.exists():
        raise AgentError(f"fixture root already exists: {root}")
    owner_live.ensure_state_path_safe(root)
    if owner_live.paths_overlap(source_state, root):
        raise AgentError("source and fixture roots overlap")
    if owner_live.is_relative_to(output, root):
        raise AgentError("artifact output must be outside disposable root")
    if owner_live.is_relative_to(output, source_state):
        raise AgentError("artifact output must be outside immutable source")
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    source_save, source_identity = owner_live._resolve_source_save(
        source_profile, args.battle_save, expected_sha
    )
    source_before = owner_live._sha256_file(source_save)
    nonce = uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    owner_live.write_json_atomic(
        root / _ROOT_MARKER_NAME,
        {
            "kind": "xar_owner_subset_ai_reassignment",
            "nonce": nonce,
            "source_state_dir": str(source_state),
        },
    )
    dll = args.bridge_dll.expanduser().resolve()
    injector = args.bridge_injector.expanduser().resolve()
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=dll,
        injector_path=injector,
    )
    stages: dict[str, object] = {}
    retreat_stage: dict[str, object] | None = None
    seed_stage: dict[str, object] | None = None
    canonical_stage: dict[str, object] | None = None
    final_stage: dict[str, object] | None = None
    cleanup_flags: list[bool] = []
    primary_error: str | None = None
    expected_date_raw: int | None = None
    try:
        retreat_spec, retreat_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "retreat",
            game_dir=game_dir,
            save_source=source_save,
            save_name=owner_live.CONTINUE_SAVE_NAME,
        )
        stages["retreat"] = retreat_materialization
        retreat_stage = _run_retreat_checkpoint_stage(
            spec=retreat_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            postcondition_timeout=postcondition_timeout,
        )
        cleanup_flags.append(
            isinstance(retreat_stage.get("cleanup"), dict)
            and retreat_stage["cleanup"].get("ok") is True
        )
        if retreat_stage.get("ok") is not True:
            raise AgentError(
                str(retreat_stage.get("error") or "retreat stage failed")
            )
        retreat_body = retreat_stage.get("body")
        retreat_body = retreat_body if isinstance(retreat_body, dict) else {}
        expected_date_raw = retreat_body.get("date_raw")
        if isinstance(expected_date_raw, bool) or not isinstance(
            expected_date_raw, int
        ):
            raise AgentError("retreat stage lacks date")
        retreat_checkpoint = owner_live._checkpoint_path(retreat_spec)

        seed_spec, seed_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "return-seed",
            game_dir=game_dir,
            save_source=retreat_checkpoint,
            save_name=owner_live.CONTINUE_SAVE_NAME,
        )
        seed_materialization["fixture_bridge"] = owner_live._install_seed_bridge(
            seed_spec
        )
        stages["return_seed"] = seed_materialization
        seed_stage = _run_return_seed_stage(
            spec=seed_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
            expected_date_raw=expected_date_raw,
        )
        cleanup_flags.append(
            isinstance(seed_stage.get("cleanup"), dict)
            and seed_stage["cleanup"].get("ok") is True
        )
        if seed_stage.get("ok") is not True:
            raise AgentError(
                str(seed_stage.get("error") or "return seed stage failed")
            )
        seed_checkpoint = owner_live._checkpoint_path(seed_spec)

        canonical_spec, canonical_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "ai-canonical",
            game_dir=game_dir,
            save_source=seed_checkpoint,
            save_name=owner_live.CONTINUE_SAVE_NAME,
        )
        stages["ai_canonical"] = canonical_materialization
        canonical_stage = _run_ai_canonical_stage(
            spec=canonical_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            expected_date_raw=expected_date_raw,
        )
        cleanup_flags.append(
            isinstance(canonical_stage.get("cleanup"), dict)
            and canonical_stage["cleanup"].get("ok") is True
        )
        if canonical_stage.get("ok") is not True:
            raise AgentError(
                str(
                    canonical_stage.get("error")
                    or "AI canonical stage failed"
                )
            )
        canonical_checkpoint = owner_live._checkpoint_path(canonical_spec)

        final_spec, final_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "final",
            game_dir=game_dir,
            save_source=canonical_checkpoint,
            save_name=owner_live.CONTINUE_SAVE_NAME,
        )
        stages["final"] = final_materialization
        final_stage = _run_final_assignment_stage(
            spec=final_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            expected_date_raw=expected_date_raw,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
        )
        cleanup_flags.append(
            isinstance(final_stage.get("cleanup"), dict)
            and final_stage["cleanup"].get("ok") is True
        )
        if final_stage.get("ok") is not True:
            raise AgentError(
                str(final_stage.get("error") or "final assignment stage failed")
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    source_after = owner_live._sha256_file(source_save)
    source_unchanged = source_before == source_after
    all_sessions_clean = bool(
        cleanup_flags
        and all(cleanup_flags)
        and not owner_live.ck3_processes()
    )
    cleanup = _cleanup_root(
        root,
        nonce=nonce,
        retain=bool(args.retain_state),
        all_sessions_clean=all_sessions_clean,
    )
    if not source_unchanged and primary_error is None:
        primary_error = "immutable source changed"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(cleanup.get("reason") or "root cleanup failed")
    canonical_body = (
        canonical_stage.get("body") if isinstance(canonical_stage, dict) else None
    )
    canonical_body = canonical_body if isinstance(canonical_body, dict) else {}
    final_body = final_stage.get("body") if isinstance(final_stage, dict) else None
    final_body = final_body if isinstance(final_body, dict) else {}
    sequence = final_body.get("sequence")
    sequence = sequence if isinstance(sequence, dict) else {}
    canonical_control = canonical_body.get("ai_control_proof")
    canonical_control = (
        canonical_control if isinstance(canonical_control, dict) else {}
    )
    canonical_transient = canonical_control.get(
        "retreating_membership_transient"
    )
    canonical_transient = (
        canonical_transient if isinstance(canonical_transient, dict) else {}
    )
    gates = {
        "production_retreat_checkpoint_ready": bool(
            retreat_stage and retreat_stage.get("ok") is True
        ),
        "same_day_player_return_seed_ready": bool(
            seed_stage and seed_stage.get("ok") is True
        ),
        "production_ai_control_reload_ready": bool(
            canonical_control.get("ok") is True
        ),
        "production_ai_retreating_transient_reload_ready": bool(
            canonical_transient.get("ok") is True
        ),
        "native_pair_reopened_after_retreat_live_ready": bool(
            sequence.get("native_pair_reopened_proof")
            and sequence["native_pair_reopened_proof"].get("ok") is True
        ),
        "assignment_reopened_aligned_eta_live_ready": bool(
            sequence.get("assignment_proof")
            and sequence["assignment_proof"].get("ok") is True
        ),
        "same_combat_rejoin_live_ready": bool(
            sequence.get("join_proof")
            and sequence["join_proof"].get("ok") is True
        ),
        "source_save_unchanged": source_unchanged,
        "managed_cleanup_ready": all_sessions_clean,
        "disposable_state_cleanup_ready": cleanup.get("ok") is True,
    }
    ok = bool(
        primary_error is None
        and all(gates.values())
        and final_stage
        and final_stage.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_owner_subset_ai_reassignment_rejoin_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_scenario": {
            "original_character_id": ORIGINAL_CHARACTER_ID,
            "temporary_player_character_id": OWNER_SUBSET_CHARACTER_ID,
            "withdrawn_public_cunit_id": REJOIN_CUNIT_ID,
            "anchor_public_cunit_id": ANCHOR_CUNIT_ID,
            "opposite_public_cunit_id": OPPOSITE_CUNIT_ID,
            "combat_id": COMBAT_ID,
            "retreat_target_province_id": RETREAT_TARGET_PROVINCE_ID,
            "return_character_anchor_province_id": (
                RETURN_CHARACTER_ANCHOR_PROVINCE_ID
            ),
            "requester_identity_claimed": False,
            "initial_ai_membership_transient": (
                "subunit_backlink_mismatch_while_retreating"
            ),
        },
        "bounds": {
            "max_assignment_days": max_assignment_days,
            "max_eta_days": max_eta_days,
            "one_game_day_raw": ONE_GAME_DAY_RAW,
        },
        "policy": {
            "production_final_stage": True,
            "seed_stage_only_uses_repository_mod_bridge": True,
            "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        },
        "source_save": source_identity
        | {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "stages": stages,
        "retreat_production": retreat_stage,
        "return_seed": seed_stage,
        "ai_canonical_production": canonical_stage,
        "final_assignment_production": final_stage,
        "readiness_gates": gates,
        "state_cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "output": str(output),
                "artifact_sha256": owner_live._sha256_file(output),
                "readiness_gates": payload.get("readiness_gates"),
                "state_cleanup": payload.get("state_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
