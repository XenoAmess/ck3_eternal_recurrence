#!/usr/bin/env python3
"""Prove owner-subset retreat -> native assignment -> same-combat rejoin.

The first three stages are the frozen v13 materialization pipeline from
``run_owner_subset_retreat_live_acceptance.py``.  Its fourth production stage
is replaced by one managed session which retreats CUnit 357, keeps CUnit
33554657 in the old CombatID, and then observes native AI assignment and
contact one paused day at a time.  No contact, join, finalizer, or combat
constructor helper is called by this runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import threading
import time
from typing import Any, Callable


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_active_combat_retreat_live_acceptance as retreat_live  # noqa: E402
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
from xar_autoplayer.bridge.battle_control_contract import (  # noqa: E402
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.battle_reinforcement_assignment_contract import (  # noqa: E402
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (  # noqa: E402
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
)
from xar_autoplayer.bridge.battle_transition_contract import (  # noqa: E402
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
EXPECTED_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ONE_GAME_DAY_RAW = 24
REJOIN_CUNIT_ID = owner_live.OWNER_SUBSET_CUNIT_ID
ANCHOR_CUNIT_ID = owner_live.UNCONTROLLED_ALLY_CUNIT_ID
OPPOSITE_CUNIT_ID = owner_live.ORIGINAL_ATTACKER_CUNIT_ID
COMBAT_ID = owner_live.COMBAT_ID
RETREAT_TARGET_PROVINCE_ID = owner_live.TARGET_PROVINCE_ID
ASSIGNED_ARCHIVE_NAME = "xar_owner_subset_reinforcement_assigned.ck3"
JOINED_ARCHIVE_NAME = "xar_owner_subset_reinforcement_joined.ck3"
FORBIDDEN_NATIVE_CALLS = (
    "0x1872BF0",
    "0x1848310",
    "0x1848570",
    "0x18721B0",
    "0x186B190",
    "0x973E00",
    "0x2208320",
    "0x23040A0",
    "0x23043F0",
    "0x23044F0",
    "0x23C9100",
    "0x23CB840",
    "0x2305580",
    "0x27FB7C0",
)
_REINFORCEMENT_HEARTBEAT_TRANSIENT = (
    "battle-reinforcement snapshot changed; retry after heartbeat"
)
_READ_ONLY_REVISION_TRANSIENTS = (
    "battle-reinforcement revision mismatch: expected ",
    "battle-reinforcement query crossed a snapshot revision",
    "battle-transition revision mismatch: expected ",
    "battle-transition query crossed a snapshot revision",
    "battle-terminal transition revision mismatch: expected ",
    "battle-terminal transition query crossed a snapshot revision",
)
_OBSERVATION_RETRY_ATTEMPTS = 6
_OBSERVATION_RETRY_TIMEOUT_SECONDS = 8.0


def _parser() -> argparse.ArgumentParser:
    parser = owner_live._parser()
    parser.description = __doc__
    parser.add_argument(
        "--direct-canonical-source",
        action="store_true",
        help=(
            "source save is already the production canonical pre-retreat "
            "checkpoint; clone it and run only the one-PID action stage"
        ),
    )
    parser.add_argument("--max-assignment-days", type=int, default=30)
    parser.add_argument("--max-eta-days", type=int, default=30)
    return parser


def _positive_int(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _snapshot_revision(snapshot: dict[str, object]) -> int:
    value = snapshot.get("revision")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("paused snapshot lacks a public revision")
    return value


def _snapshot_date(snapshot: dict[str, object]) -> int:
    value = snapshot.get("date_raw")
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("paused snapshot lacks date_raw")
    return value


def _assert_paused(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("reinforcement rejoin acceptance requires pause")


def _reinforcement_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("reinforcement query returned a non-object")
    frame = result.get("battle_reinforcement_assignment")
    if not isinstance(frame, dict):
        raise RuntimeError("reinforcement query omitted its typed frame")
    return frame


def _battle_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("battle query returned a non-object")
    nested = result.get("battle_transition_snapshot")
    if isinstance(nested, dict):
        return nested
    if "battle_transition_ready" in result:
        return result
    raise RuntimeError("battle query omitted its lifecycle frame")


def _terminal_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("terminal query returned a non-object")
    frame = result.get("battle_terminal_transition")
    if not isinstance(frame, dict):
        raise RuntimeError("terminal query omitted its journal frame")
    return frame


def _subject_observations(
    snapshot: dict[str, object], public_cunit_id: int
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []

    def collect(value: object, source: str, war_id: object = None) -> None:
        for row in value if isinstance(value, list) else []:
            if isinstance(row, dict) and row.get("army_id") == public_cunit_id:
                observations.append(
                    {"source": source, "war_id": war_id, "army": dict(row)}
                )

    collect(snapshot.get("player_armies"), "player_armies")
    wars = snapshot.get("active_wars")
    for index, war in enumerate(wars if isinstance(wars, list) else []):
        if not isinstance(war, dict):
            continue
        war_id = war.get("war_id")
        collect(war.get("allied_armies"), f"active_wars[{index}].allied", war_id)
        collect(war.get("enemy_armies"), f"active_wars[{index}].enemy", war_id)
    return observations


def _army_signature(army: dict[str, object]) -> tuple[object, ...]:
    route = army.get("route_province_ids")
    return (
        army.get("army_id"),
        army.get("owner_character_id"),
        army.get("current_province_id"),
        army.get("move_target_province_id"),
        army.get("move_target_observable"),
        tuple(route) if isinstance(route, list) else None,
        army.get("in_combat"),
        army.get("retreating"),
        army.get("army_state_code"),
    )


def _subject_army(
    snapshot: dict[str, object], public_cunit_id: int
) -> dict[str, object]:
    observations = _subject_observations(snapshot, public_cunit_id)
    armies = [
        row["army"]
        for row in observations
        if isinstance(row.get("army"), dict)
    ]
    signatures = [_army_signature(army) for army in armies]
    if not armies or len(set(signatures)) != 1:
        raise RuntimeError(
            f"CUnit {public_cunit_id} semantic observations disagree"
        )
    return dict(armies[0])


def _native_rows(frame: dict[str, object]) -> list[dict[str, object]]:
    native_order = frame.get("native_order")
    rows = (
        native_order.get("parent_subunits_in_stored_order")
        if isinstance(native_order, dict)
        else None
    )
    return [dict(row) for row in rows] if isinstance(rows, list) and all(
        isinstance(row, dict) for row in rows
    ) else []


def _native_pair_proof(
    snapshot: dict[str, object],
    rejoin_result: dict[str, object],
    anchor_result: dict[str, object],
) -> dict[str, object]:
    rejoin = _reinforcement_frame(rejoin_result)
    anchor = _reinforcement_frame(anchor_result)
    first_sequence = rejoin_result.get("query_sequence")
    second_sequence = anchor_result.get("query_sequence")
    binding_checks = {
        "selected_ids": rejoin.get("selected_public_cunit_id")
        == REJOIN_CUNIT_ID
        and anchor.get("selected_public_cunit_id") == ANCHOR_CUNIT_ID,
        "same_paused_native_binding": rejoin.get("snapshot_revision")
        == snapshot.get("native_revision")
        == anchor.get("snapshot_revision")
        and rejoin.get("observed_date_raw")
        == snapshot.get("date_raw")
        == anchor.get("observed_date_raw"),
        "queried_357_then_33554657": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence > first_sequence,
    }
    rows = _native_rows(rejoin)
    anchor_rows = _native_rows(anchor)
    flattened: list[int] = []
    locations: dict[int, tuple[int, int]] = {}
    typed = bool(rows)
    for row_index, row in enumerate(rows):
        ids = row.get("public_cunit_ids_in_stored_order")
        if not isinstance(ids, list):
            typed = False
            continue
        for column, value in enumerate(ids):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
                or value in locations
            ):
                typed = False
                continue
            flattened.append(value)
            locations[value] = (row_index, column)
    rejoin_location = locations.get(REJOIN_CUNIT_ID)
    anchor_location = locations.get(ANCHOR_CUNIT_ID)
    order_checks = {
        "both_available": rejoin.get("status") == "available"
        and anchor.get("status") == "available",
        "same_parent_identity": rejoin.get("coordinator_id")
        == anchor.get("coordinator_id")
        and rejoin.get("unit_stack_stored_index")
        == anchor.get("unit_stack_stored_index"),
        "parent_order_identical": rows == anchor_rows,
        "native_flattened_order": typed
        and flattened == [REJOIN_CUNIT_ID, ANCHOR_CUNIT_ID],
        "selected_indices_match_rows": rejoin_location is not None
        and anchor_location is not None
        and rejoin.get("subunit_stored_index") == rejoin_location[0]
        and anchor.get("subunit_stored_index") == anchor_location[0],
    }
    return {
        "rejoin_result": rejoin_result,
        "anchor_result": anchor_result,
        "rejoin_frame": rejoin,
        "anchor_frame": anchor,
        "native_rows": rows,
        "flattened_public_cunit_order": flattened,
        "binding_checks": binding_checks,
        "order_checks": order_checks,
        "binding_ok": all(binding_checks.values()),
        "available_order_ready": all(binding_checks.values())
        and all(order_checks.values()),
    }


def _query_native_pair(
    service: GameplayBridgeService, snapshot: dict[str, object]
) -> dict[str, object]:
    revision = _snapshot_revision(snapshot)
    rejoin = service.query_battle_reinforcement_assignment_v1(
        REJOIN_CUNIT_ID, expected_revision=revision
    )
    anchor = service.query_battle_reinforcement_assignment_v1(
        ANCHOR_CUNIT_ID, expected_revision=revision
    )
    proof = _native_pair_proof(snapshot, rejoin, anchor)
    if proof.get("binding_ok") is not True:
        raise RuntimeError("daily reinforcement queries crossed their frame")
    return proof


def _is_read_only_heartbeat_transient(error: BaseException) -> bool:
    detail = str(error)
    return bool(
        _REINFORCEMENT_HEARTBEAT_TRANSIENT in detail
        or any(value in detail for value in _READ_ONLY_REVISION_TRANSIENTS)
    )


def _wait_for_fresh_paused_observation(
    service: GameplayBridgeService,
    stale: dict[str, object],
    *,
    deadline: float,
) -> dict[str, object]:
    stale_date = _snapshot_date(stale)
    stale_episode = stale.get("episode_run_id")
    while True:
        candidate = service.snapshot()
        if candidate.get("paused") is not True:
            raise RuntimeError(
                "read-only retry observed CK3 unpaused"
            )
        if _snapshot_date(candidate) != stale_date:
            raise RuntimeError(
                "read-only retry crossed a game day"
            )
        if candidate.get("episode_run_id") != stale_episode:
            raise RuntimeError(
                "read-only retry crossed an episode"
            )
        if (
            candidate.get("snapshot_id") != stale.get("snapshot_id")
            or candidate.get("revision") != stale.get("revision")
            or candidate.get("native_revision") != stale.get("native_revision")
        ):
            return candidate
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "read-only retry timed out waiting for a fresh paused heartbeat"
            )
        time.sleep(0.05)


def _query_paused_observation_bundle(
    service: GameplayBridgeService,
    snapshot: dict[str, object],
    *,
    combat_id: int,
    terminal_cursor: int | None,
    retry_attempts: int = _OBSERVATION_RETRY_ATTEMPTS,
    retry_timeout_seconds: float = _OBSERVATION_RETRY_TIMEOUT_SECONDS,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
]:
    if retry_attempts <= 0 or retry_timeout_seconds <= 0:
        raise ValueError("observation retry bounds must be positive")
    _assert_paused(snapshot)
    fixed_date = _snapshot_date(snapshot)
    fixed_episode = snapshot.get("episode_run_id")
    current = snapshot
    deadline = time.monotonic() + retry_timeout_seconds
    retries: list[dict[str, object]] = []
    for attempt in range(1, retry_attempts + 1):
        try:
            pair = _query_native_pair(service, current)
            battle = _battle_frame(
                service.query_battle_transition_v1(
                    combat_id, expected_revision=_snapshot_revision(current)
                )
            )
            terminal = _terminal_frame(
                service.query_battle_terminal_transition_v1(
                    combat_id,
                    REJOIN_CUNIT_ID,
                    expected_revision=_snapshot_revision(current),
                    after_terminal_sequence=terminal_cursor,
                )
            )
            return current, pair, battle, terminal, retries
        except BaseException as error:
            if not _is_read_only_heartbeat_transient(error):
                raise
            if attempt >= retry_attempts or time.monotonic() >= deadline:
                raise RuntimeError(
                    "read-only paused observation retry bound exhausted"
                ) from error
            fresh = _wait_for_fresh_paused_observation(
                service, current, deadline=deadline
            )
            if (
                _snapshot_date(fresh) != fixed_date
                or fresh.get("episode_run_id") != fixed_episode
            ):
                raise RuntimeError(
                    "read-only paused observation retry changed context"
                ) from error
            retries.append(
                {
                    "attempt": attempt,
                    "transient": str(error),
                    "stale_snapshot_id": current.get("snapshot_id"),
                    "stale_revision": current.get("revision"),
                    "stale_native_revision": current.get("native_revision"),
                    "fresh_snapshot_id": fresh.get("snapshot_id"),
                    "fresh_revision": fresh.get("revision"),
                    "fresh_native_revision": fresh.get("native_revision"),
                    "date_raw": fixed_date,
                    "episode_run_id": fixed_episode,
                    "restart_scope": "reinforcement_pair_then_battle_then_terminal",
                }
            )
            current = fresh
    raise RuntimeError("unreachable paused observation retry state")


def _side_ids(
    battle: dict[str, object], side_index: int
) -> tuple[list[int], list[int]]:
    if side_index not in {0, 1}:
        raise RuntimeError("battle side index is not typed")
    attacker = battle.get("attacker_public_cunit_ids_in_stored_order")
    defender = battle.get("defender_public_cunit_ids_in_stored_order")
    if not isinstance(attacker, list) or not isinstance(defender, list):
        raise RuntimeError("battle lifecycle omitted ordered side identities")
    if not all(
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
        for value in [*attacker, *defender]
    ):
        raise RuntimeError("battle lifecycle side identities are malformed")
    return (
        list(attacker if side_index == 0 else defender),
        list(defender if side_index == 0 else attacker),
    )


def _active_old_combat_proof(
    battle: dict[str, object],
    *,
    combat_id: int,
    combat_province_id: int,
    side_index: int,
    same_side_expected: list[int],
    opposite_side_expected: list[int],
) -> dict[str, object]:
    try:
        same_side, opposite_side = _side_ids(battle, side_index)
    except RuntimeError:
        same_side, opposite_side = [], []
    checks = {
        "available_active_identity": battle.get("status") == "available"
        and battle.get("battle_transition_ready") is True
        and battle.get("combat_id") == combat_id
        and battle.get("province_id") == combat_province_id,
        "active_phase": battle.get("finalized") is False
        and battle.get("phase_raw") in {0, 1, 2}
        and battle.get("winner_raw") == -1,
        "same_side_exact": same_side == same_side_expected,
        "opposite_side_exact": opposite_side == opposite_side_expected,
        "withdrawn_absent": REJOIN_CUNIT_ID not in same_side
        and REJOIN_CUNIT_ID not in opposite_side,
        "anchor_remains": same_side.count(ANCHOR_CUNIT_ID) == 1,
    }
    return {
        "same_side": same_side,
        "opposite_side": opposite_side,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _terminal_boundary_proof(
    terminal: dict[str, object],
    battle: dict[str, object],
    *,
    combat_id: int,
    requested_cursor: int | None,
) -> dict[str, object]:
    journal = terminal.get("terminal_journal")
    prior = terminal.get("prior")
    removal = terminal.get("removal")
    journal = journal if isinstance(journal, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    removal = removal if isinstance(removal, dict) else {}
    latest = journal.get("latest_sequence")
    oldest = journal.get("oldest_available_sequence")
    bounds_typed = bool(
        isinstance(latest, int)
        and not isinstance(latest, bool)
        and latest >= 0
        and isinstance(oldest, int)
        and not isinstance(oldest, bool)
        and oldest >= 0
        and ((oldest == latest == 0) or 1 <= oldest <= latest)
    )
    common = {
        "query_available": terminal.get("status") == "available"
        and terminal.get("battle_terminal_transition_ready") is True,
        "combat_identity": terminal.get("prior_combat_id") == combat_id
        and prior.get("combat_id") == combat_id,
        "cursor_bound": journal.get("requested_after_sequence")
        == requested_cursor,
        "journal_bounds_typed": bounds_typed,
    }
    active = bool(
        all(common.values())
        and prior.get("terminal_kind") == "active_not_terminal"
        and journal.get("event_status") == "not_observed"
        and journal.get("event_sequence") is None
        and removal.get("prior_combat_strictly_resolves") is True
        and prior.get("attacker_public_cunit_ids_in_stored_order")
        == battle.get("attacker_public_cunit_ids_in_stored_order")
        and prior.get("defender_public_cunit_ids_in_stored_order")
        == battle.get("defender_public_cunit_ids_in_stored_order")
    )
    terminal_event = bool(
        all(common.values())
        and prior.get("terminal_kind") in {"normal_result", "no_normal_result"}
        and journal.get("event_status") == "observed"
        and isinstance(journal.get("event_sequence"), int)
        and not isinstance(journal.get("event_sequence"), bool)
    )
    classification = (
        "active" if active else "terminal_event" if terminal_event else "invalid"
    )
    next_cursor = (
        latest
        if bounds_typed and isinstance(latest, int) and latest > 0
        else requested_cursor
    )
    return {
        "classification": classification,
        "requested_cursor": requested_cursor,
        "next_cursor": next_cursor,
        "terminal_kind": prior.get("terminal_kind"),
        "event_sequence": journal.get("event_sequence"),
        "common_checks": common,
        "active": active,
        "terminal_event": terminal_event,
        "boundary_valid": active or terminal_event,
    }


def _assignment_reopened_proof(
    pair: dict[str, object],
    snapshot: dict[str, object],
    battle: dict[str, object],
    *,
    combat_id: int,
    combat_province_id: int,
) -> dict[str, object]:
    rejoin = pair.get("rejoin_frame")
    anchor = pair.get("anchor_frame")
    rejoin = rejoin if isinstance(rejoin, dict) else {}
    anchor = anchor if isinstance(anchor, dict) else {}
    rejoin_signal = rejoin.get("signal")
    anchor_signal = anchor.get("signal")
    rejoin_assignment = rejoin.get("assignment")
    anchor_assignment = anchor.get("assignment")
    route = rejoin.get("route")
    rejoin_signal = rejoin_signal if isinstance(rejoin_signal, dict) else {}
    anchor_signal = anchor_signal if isinstance(anchor_signal, dict) else {}
    rejoin_assignment = (
        rejoin_assignment if isinstance(rejoin_assignment, dict) else {}
    )
    anchor_assignment = (
        anchor_assignment if isinstance(anchor_assignment, dict) else {}
    )
    route = route if isinstance(route, dict) else {}
    route_ids = route.get("route_province_ids")
    arrivals = route.get("arrival_date_raws")
    eta = route.get("assignment_eta_date_raw")
    try:
        semantic = _subject_army(snapshot, REJOIN_CUNIT_ID)
    except RuntimeError:
        semantic = {}
    rows = pair.get("native_rows")
    rows = rows if isinstance(rows, list) else []
    any_same_frame_asking = any(
        row.get("asking_for_help") is True
        for row in rows
        if isinstance(row, dict)
    ) or rejoin_signal.get("asking_for_help") is True or anchor_signal.get(
        "asking_for_help"
    ) is True
    checks = {
        "native_parent_order": pair.get("available_order_ready") is True,
        "same_frame_help_request_exists": any_same_frame_asking,
        "anchor_still_in_old_combat": anchor_assignment.get(
            "combat_binding_status"
        )
        == "already_in_active_combat"
        and anchor_assignment.get("active_combat_id") == combat_id,
        "withdrawn_unit_assigned_to_help": rejoin_signal.get(
            "assigned_to_help"
        )
        is True,
        "native_help_override_target": rejoin_assignment.get(
            "assignment_target_province_id"
        )
        == combat_province_id
        and rejoin_assignment.get("target_provenance")
        == "native_help_override",
        "future_combat_not_fabricated": rejoin_assignment.get(
            "combat_binding_status"
        )
        == "unbound_until_contact"
        and rejoin_assignment.get("active_combat_id") is None,
        "aligned_route": route.get("route_alignment")
        == "aligned_to_assignment"
        and route.get("move_target_province_id") == combat_province_id
        and isinstance(route_ids, list)
        and bool(route_ids)
        and route_ids[-1] == combat_province_id,
        "typed_eta": isinstance(arrivals, list)
        and isinstance(route_ids, list)
        and len(arrivals) == len(route_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in arrivals
        )
        and arrivals == sorted(arrivals)
        and isinstance(eta, int)
        and not isinstance(eta, bool)
        and bool(arrivals)
        and eta == arrivals[-1]
        and eta > _snapshot_date(snapshot),
        "semantic_route_matches": semantic.get("in_combat") is False
        and semantic.get("current_province_id")
        == route.get("current_province_id")
        and semantic.get("move_target_province_id") == combat_province_id
        and semantic.get("route_province_ids") == route_ids,
        "old_combat_roster_still_excludes_withdrawn": (
            REJOIN_CUNIT_ID
            not in (battle.get("attacker_public_cunit_ids_in_stored_order") or [])
            and REJOIN_CUNIT_ID
            not in (battle.get("defender_public_cunit_ids_in_stored_order") or [])
        ),
    }
    return {
        "assignment_eta_date_raw": eta,
        "rejoin_frame": rejoin,
        "anchor_frame": anchor,
        "semantic_rejoin_army": semantic,
        "same_frame_asking_observed": any_same_frame_asking,
        "requester_identity_claimed": False,
        "evidence_boundary": (
            "the assignment stores a target Province, not requester identity; "
            "the asking signal and old-combat anchor are only same-frame facts"
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _same_combat_rejoin_proof(
    post_retreat_battle: dict[str, object],
    immediately_before_battle: dict[str, object],
    joined_battle: dict[str, object],
    pair: dict[str, object],
    snapshot: dict[str, object],
    *,
    combat_id: int,
    combat_province_id: int,
    side_index: int,
) -> dict[str, object]:
    baseline_same, baseline_opposite = _side_ids(
        post_retreat_battle, side_index
    )
    before_same, before_opposite = _side_ids(
        immediately_before_battle, side_index
    )
    joined_same, joined_opposite = _side_ids(joined_battle, side_index)
    rejoin = pair.get("rejoin_frame")
    rejoin = rejoin if isinstance(rejoin, dict) else {}
    assignment = rejoin.get("assignment")
    assignment = assignment if isinstance(assignment, dict) else {}
    semantic = _subject_army(snapshot, REJOIN_CUNIT_ID)
    pursuit_reopened = immediately_before_battle.get("phase_raw") == 2
    phase_checks = (
        joined_battle.get("phase_raw") == 1
        and joined_battle.get("phase_day") == 0
        and joined_battle.get("winner_raw") == -1
        if pursuit_reopened
        else joined_battle.get("phase_raw") in {0, 1}
        and joined_battle.get("winner_raw") == -1
    )
    checks = {
        "same_combat_identity": joined_battle.get("status") == "available"
        and joined_battle.get("battle_transition_ready") is True
        and joined_battle.get("combat_id") == combat_id
        and joined_battle.get("province_id") == combat_province_id,
        "withdrawn_absent_immediately_before": REJOIN_CUNIT_ID
        not in [*before_same, *before_opposite],
        "baseline_roster_unchanged_before_join": before_same == baseline_same
        and before_opposite == baseline_opposite,
        "strict_unique_tail_append": joined_same
        == [*baseline_same, REJOIN_CUNIT_ID]
        and joined_same.count(REJOIN_CUNIT_ID) == 1,
        "opposite_side_unchanged": joined_opposite == baseline_opposite,
        "anchor_retained_once": joined_same.count(ANCHOR_CUNIT_ID) == 1,
        "exact_active_combat_binding": assignment.get(
            "combat_binding_status"
        )
        == "already_in_active_combat"
        and assignment.get("active_combat_id") == combat_id,
        "semantic_rejoin": semantic.get("in_combat") is True
        and semantic.get("current_province_id") == combat_province_id,
        "phase_invariant": joined_battle.get("finalized") is False
        and phase_checks,
    }
    return {
        "combat_id": combat_id,
        "side_index": side_index,
        "pursuit_reopened": pursuit_reopened,
        "baseline_same_side": baseline_same,
        "immediately_before_same_side": before_same,
        "joined_same_side": joined_same,
        "baseline_opposite_side": baseline_opposite,
        "immediately_before_opposite_side": before_opposite,
        "joined_opposite_side": joined_opposite,
        "semantic_rejoin_army": semantic,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _advance_one_day(
    service: GameplayBridgeService,
    before: dict[str, object],
    wait_after_advance: Callable[[], dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    _assert_paused(before)
    before_date = _snapshot_date(before)
    before_revision = _snapshot_revision(before)
    result = service.execute_step(
        "life-advance", expected_revision=before_revision
    )
    after = wait_after_advance()
    _assert_paused(after)
    checks = {
        "step": isinstance(result, dict)
        and result.get("step") == "life-advance",
        "result_dates": result.get("starting_date_raw") == before_date
        and result.get("ending_date_raw") == before_date + ONE_GAME_DAY_RAW,
        "result_elapsed_days": result.get("elapsed_days") == 1,
        "snapshot_exactly_one_day": _snapshot_date(after)
        == before_date + ONE_GAME_DAY_RAW,
        "fresh_revision": _snapshot_revision(after) > before_revision,
        "same_episode": after.get("episode_run_id")
        == before.get("episode_run_id"),
    }
    proof = {
        "before_date_raw": before_date,
        "after_date_raw": _snapshot_date(after),
        "before_revision": before_revision,
        "after_revision": _snapshot_revision(after),
        "result": result,
        "checks": checks,
        "ok": all(checks.values()),
    }
    if proof["ok"] is not True:
        raise RuntimeError("life-advance did not advance exactly one CK3 day")
    return after, proof


def _archive_checkpoint(
    result: object,
    *,
    archive_name: str,
    expected_date_raw: int,
) -> dict[str, object]:
    checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    raw_path = checkpoint.get("path")
    source = Path(raw_path).resolve() if isinstance(raw_path, str) else None
    if (
        checkpoint.get("status") != "saved"
        or source is None
        or not source.is_file()
        or checkpoint.get("date_raw") != expected_date_raw
    ):
        raise RuntimeError("save-checkpoint did not materialize expected date")
    archive = source.with_name(archive_name)
    if archive.exists():
        raise RuntimeError(f"checkpoint archive already exists: {archive}")
    shutil.copy2(source, archive)
    source_sha = owner_live._sha256_file(source)
    archive_sha = owner_live._sha256_file(archive)
    if source_sha != archive_sha:
        raise RuntimeError("checkpoint archive bytes differ")
    return {
        "checkpoint": checkpoint,
        "archive_path": str(archive),
        "archive_size": archive.stat().st_size,
        "archive_sha256": archive_sha,
        "ok": True,
    }


def _mutation_boundary_proof(commands: list[str]) -> dict[str, object]:
    allowed = {
        "preview-active-combat-retreat-v1",
        "order-active-combat-retreat-v1",
        "life-advance",
        "save-checkpoint",
    }
    checks = {
        "only_production_commands": all(command in allowed for command in commands),
        "one_retreat_preview": commands.count(
            "preview-active-combat-retreat-v1"
        )
        == 1,
        "one_retreat_order": commands.count("order-active-combat-retreat-v1")
        == 1,
        "two_checkpoint_saves": commands.count("save-checkpoint") == 2,
        "at_least_one_daily_advance": commands.count("life-advance") >= 1,
    }
    return {
        "commands": list(commands),
        "allowed_commands": sorted(allowed),
        "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        "forbidden_native_calls_invoked": [],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_rejoin_sequence(
    service: GameplayBridgeService,
    *,
    wait_after_advance: Callable[[], dict[str, object]],
    max_assignment_days: int,
    max_eta_days: int,
    postcondition_timeout: float,
) -> dict[str, object]:
    commands: list[str] = []
    advances: list[dict[str, object]] = []
    daily_pairs: list[dict[str, object]] = []
    terminal_boundaries: list[dict[str, object]] = []

    initial = service.snapshot()
    _assert_paused(initial)
    if owner_live._played_character_id(initial) != owner_live.OWNER_SUBSET_CHARACTER_ID:
        raise RuntimeError("canonical source did not bind Character 36108")
    pre_action_battle_control = service.query_battle_control_snapshot_v1(
        REJOIN_CUNIT_ID, expected_revision=_snapshot_revision(initial)
    )
    if not owner_live._validate_owner_subset_frame(pre_action_battle_control):
        raise RuntimeError("canonical source lost exact owner-subset battle frame")
    side_index = pre_action_battle_control.get("side_index")
    if side_index not in {0, 1}:
        raise RuntimeError("owner-subset frame lacks side index")
    combat_id = retreat_live._battle_combat_id(pre_action_battle_control)
    if combat_id != COMBAT_ID:
        raise RuntimeError("canonical source CombatID differs")
    pre_lifecycle = _battle_frame(
        service.query_battle_transition_v1(
            combat_id, expected_revision=_snapshot_revision(initial)
        )
    )
    pre_same, pre_opposite = _side_ids(pre_lifecycle, int(side_index))
    if not (
        pre_same == [REJOIN_CUNIT_ID, ANCHOR_CUNIT_ID]
        and pre_opposite == [OPPOSITE_CUNIT_ID]
    ):
        raise RuntimeError("canonical source stored roster differs")
    combat_province_id = pre_lifecycle.get("province_id")
    if (
        isinstance(combat_province_id, bool)
        or not isinstance(combat_province_id, int)
        or combat_province_id <= 0
    ):
        raise RuntimeError("canonical source lacks combat Province")

    preview = service.preview_active_combat_retreat_v1(
        REJOIN_CUNIT_ID,
        RETREAT_TARGET_PROVINCE_ID,
        expected_revision=_snapshot_revision(initial),
    )
    commands.append("preview-active-combat-retreat-v1")
    target_preview = preview.get("target_preview")
    target_preview = target_preview if isinstance(target_preview, dict) else {}
    token = target_preview.get("candidate_token")
    if not (
        preview.get("status") == "available"
        and preview.get("action_ready") is True
        and isinstance(token, str)
        and bool(token)
    ):
        raise RuntimeError("owner-subset retreat preview is not action-ready")
    order = service.order_active_combat_retreat_v1(
        REJOIN_CUNIT_ID,
        expected_revision=int(preview["source_binding"]["revision"]),
        expected_combat_id=combat_id,
        expected_side_index=int(side_index),
        expected_scope="owner_subset",
        target_province_id=RETREAT_TARGET_PROVINCE_ID,
        candidate_token=token,
    )
    commands.append("order-active-combat-retreat-v1")
    if not (
        order.get("accepted") is True
        and order.get("status") == "accepted_verification_pending"
    ):
        raise RuntimeError("owner-subset retreat order was not accepted")

    post_retreat_snapshots: list[dict[str, object]] = []
    post_retreat_battle: dict[str, object] | None = None
    snapshot: dict[str, object] | None = None
    deadline = time.monotonic() + postcondition_timeout
    while True:
        observed = service.snapshot()
        post_retreat_snapshots.append(
            retreat_live._compact_snapshot(observed, REJOIN_CUNIT_ID)
        )
        if retreat_live._retreat_semantic_ready(
            observed, REJOIN_CUNIT_ID, RETREAT_TARGET_PROVINCE_ID
        ):
            candidate = _battle_frame(
                service.query_battle_transition_v1(
                    combat_id,
                    expected_revision=_snapshot_revision(observed),
                )
            )
            if retreat_live._owner_subset_transition_ready(
                candidate,
                pre_action_battle_control,
                REJOIN_CUNIT_ID,
            ):
                snapshot = observed
                post_retreat_battle = candidate
                break
        if time.monotonic() >= deadline:
            raise RuntimeError("owner-subset retreat postcondition timed out")
        time.sleep(0.05)
    assert snapshot is not None and post_retreat_battle is not None
    if _snapshot_date(snapshot) != _snapshot_date(initial):
        raise RuntimeError("owner-subset extraction crossed a game day")
    post_same, post_opposite = _side_ids(post_retreat_battle, int(side_index))
    if not (
        post_same == [ANCHOR_CUNIT_ID]
        and post_opposite == pre_opposite
    ):
        raise RuntimeError("owner-subset extraction changed the wrong roster")

    def diagnostic_outcome(
        outcome: str,
        *,
        stage: str,
        day_index: int,
        current_snapshot: dict[str, object],
        pair: dict[str, object],
        battle: dict[str, object],
        terminal: dict[str, object],
        boundary: dict[str, object],
        active_roster: dict[str, object] | None,
        observation_retries: list[dict[str, object]],
        assignment_proof: dict[str, object] | None = None,
        assigned_checkpoint: dict[str, object] | None = None,
        persistence: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        return {
            "ok": False,
            "outcome": outcome,
            "initial_snapshot": initial,
            "pre_action_battle_control": pre_action_battle_control,
            "pre_lifecycle": pre_lifecycle,
            "preview": preview,
            "order": order,
            "post_retreat_snapshots": post_retreat_snapshots,
            "post_retreat_battle": post_retreat_battle,
            "assignment_proof": assignment_proof,
            "assigned_checkpoint": assigned_checkpoint,
            "persistence": list(persistence or []),
            "diagnostic_frame": {
                "stage": stage,
                "day_index": day_index,
                "snapshot": current_snapshot,
                "pair": pair,
                "battle": battle,
                "terminal": terminal,
                "boundary": boundary,
                "active_roster": active_roster,
                "observation_retries": observation_retries,
            },
            "daily_pairs": daily_pairs,
            "terminal_boundaries": terminal_boundaries,
            "commands": list(commands),
            "advances": advances,
            "readiness_gates": {
                "assignment_reopened_aligned_eta_live_ready": False,
                "same_combat_rejoin_live_ready": False,
            },
        }

    cursor: int | None = None
    assignment: dict[str, object] | None = None
    assigned_pair: dict[str, object] | None = None
    assigned_battle: dict[str, object] | None = None
    for day_index in range(max_assignment_days + 1):
        snapshot, pair, battle, terminal, observation_retries = (
            _query_paused_observation_bundle(
                service,
                snapshot,
                combat_id=combat_id,
                terminal_cursor=cursor,
            )
        )
        daily_pairs.append(
            {
                "stage": "assignment",
                "day_index": day_index,
                "observation_retries": observation_retries,
                "pair": pair,
            }
        )
        active_roster = _active_old_combat_proof(
            battle,
            combat_id=combat_id,
            combat_province_id=combat_province_id,
            side_index=int(side_index),
            same_side_expected=post_same,
            opposite_side_expected=post_opposite,
        )
        boundary = _terminal_boundary_proof(
            terminal,
            battle,
            combat_id=combat_id,
            requested_cursor=cursor,
        )
        terminal_boundaries.append(
            {"stage": "assignment", "day_index": day_index, **boundary}
        )
        if boundary.get("terminal_event") is True:
            return diagnostic_outcome(
                "terminal_before_assignment",
                stage="assignment",
                day_index=day_index,
                current_snapshot=snapshot,
                pair=pair,
                battle=battle,
                terminal=terminal,
                boundary=boundary,
                active_roster=active_roster,
                observation_retries=observation_retries,
            )
        if boundary.get("active") is not True or active_roster.get("ok") is not True:
            return diagnostic_outcome(
                "assignment_old_combat_lifecycle_drift",
                stage="assignment",
                day_index=day_index,
                current_snapshot=snapshot,
                pair=pair,
                battle=battle,
                terminal=terminal,
                boundary=boundary,
                active_roster=active_roster,
                observation_retries=observation_retries,
            )
        cursor = boundary.get("next_cursor")
        candidate_assignment = _assignment_reopened_proof(
            pair,
            snapshot,
            battle,
            combat_id=combat_id,
            combat_province_id=combat_province_id,
        )
        if candidate_assignment.get("ok") is True:
            assignment = candidate_assignment
            assigned_pair = pair
            assigned_battle = battle
            break
        if day_index == max_assignment_days:
            raise RuntimeError("native help assignment was not observed within bound")
        snapshot, advance = _advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
    if assignment is None or assigned_pair is None or assigned_battle is None:
        raise RuntimeError("assignment loop ended without aligned ETA")

    assigned_date = _snapshot_date(snapshot)
    eta = assignment.get("assignment_eta_date_raw")
    if (
        isinstance(eta, bool)
        or not isinstance(eta, int)
        or not assigned_date < eta
        or eta > assigned_date + max_eta_days * ONE_GAME_DAY_RAW
    ):
        raise RuntimeError("captured ETA is outside the bounded daily loop")
    assigned_checkpoint = _archive_checkpoint(
        service.save_checkpoint(expected_revision=_snapshot_revision(snapshot)),
        archive_name=ASSIGNED_ARCHIVE_NAME,
        expected_date_raw=assigned_date,
    )
    commands.append("save-checkpoint")
    after_save = service.snapshot()
    _assert_paused(after_save)
    if (
        _snapshot_date(after_save) != assigned_date
        or after_save.get("episode_run_id") != snapshot.get("episode_run_id")
    ):
        raise RuntimeError("assigned checkpoint changed gameplay frame")
    snapshot = after_save

    immediately_before_battle = assigned_battle
    rejoin: dict[str, object] | None = None
    joined_pair: dict[str, object] | None = None
    joined_battle: dict[str, object] | None = None
    persistence: list[dict[str, object]] = []
    for day_index in range(1, max_eta_days + 1):
        if _snapshot_date(snapshot) >= eta:
            raise RuntimeError("withdrawn CUnit did not rejoin by native ETA")
        snapshot, advance = _advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
        snapshot, pair, battle, terminal, observation_retries = (
            _query_paused_observation_bundle(
                service,
                snapshot,
                combat_id=combat_id,
                terminal_cursor=cursor,
            )
        )
        daily_pairs.append(
            {
                "stage": "eta",
                "day_index": day_index,
                "observation_retries": observation_retries,
                "pair": pair,
            }
        )
        boundary = _terminal_boundary_proof(
            terminal,
            battle,
            combat_id=combat_id,
            requested_cursor=cursor,
        )
        terminal_boundaries.append(
            {"stage": "eta", "day_index": day_index, **boundary}
        )
        if boundary.get("terminal_event") is True:
            return diagnostic_outcome(
                "terminal_before_rejoin",
                stage="eta",
                day_index=day_index,
                current_snapshot=snapshot,
                pair=pair,
                battle=battle,
                terminal=terminal,
                boundary=boundary,
                active_roster=None,
                observation_retries=observation_retries,
                assignment_proof=assignment,
                assigned_checkpoint=assigned_checkpoint,
                persistence=persistence,
            )
        if boundary.get("active") is not True:
            return diagnostic_outcome(
                "eta_terminal_boundary_drift",
                stage="eta",
                day_index=day_index,
                current_snapshot=snapshot,
                pair=pair,
                battle=battle,
                terminal=terminal,
                boundary=boundary,
                active_roster=None,
                observation_retries=observation_retries,
                assignment_proof=assignment,
                assigned_checkpoint=assigned_checkpoint,
                persistence=persistence,
            )
        cursor = boundary.get("next_cursor")
        participants = [
            *(battle.get("attacker_public_cunit_ids_in_stored_order") or []),
            *(battle.get("defender_public_cunit_ids_in_stored_order") or []),
        ]
        if REJOIN_CUNIT_ID in participants:
            candidate_rejoin = _same_combat_rejoin_proof(
                post_retreat_battle,
                immediately_before_battle,
                battle,
                pair,
                snapshot,
                combat_id=combat_id,
                combat_province_id=combat_province_id,
                side_index=int(side_index),
            )
            if candidate_rejoin.get("ok") is not True:
                raise RuntimeError("contact failed strict same-CombatID tail proof")
            rejoin = candidate_rejoin
            joined_pair = pair
            joined_battle = battle
            break
        active_roster = _active_old_combat_proof(
            battle,
            combat_id=combat_id,
            combat_province_id=combat_province_id,
            side_index=int(side_index),
            same_side_expected=post_same,
            opposite_side_expected=post_opposite,
        )
        if active_roster.get("ok") is not True:
            return diagnostic_outcome(
                "eta_old_combat_roster_drift",
                stage="eta",
                day_index=day_index,
                current_snapshot=snapshot,
                pair=pair,
                battle=battle,
                terminal=terminal,
                boundary=boundary,
                active_roster=active_roster,
                observation_retries=observation_retries,
                assignment_proof=assignment,
                assigned_checkpoint=assigned_checkpoint,
                persistence=persistence,
            )
        persistence.append(
            {
                "day_index": day_index,
                "date_raw": _snapshot_date(snapshot),
                "pair": pair,
                "assignment": _assignment_reopened_proof(
                    pair,
                    snapshot,
                    battle,
                    combat_id=combat_id,
                    combat_province_id=combat_province_id,
                ),
            }
        )
        immediately_before_battle = battle
    if rejoin is None or joined_pair is None or joined_battle is None:
        raise RuntimeError("withdrawn CUnit did not rejoin within ETA bound")
    joined_date = _snapshot_date(snapshot)
    if joined_date > eta:
        raise RuntimeError("withdrawn CUnit joined after captured native ETA")
    joined_checkpoint = _archive_checkpoint(
        service.save_checkpoint(expected_revision=_snapshot_revision(snapshot)),
        archive_name=JOINED_ARCHIVE_NAME,
        expected_date_raw=joined_date,
    )
    commands.append("save-checkpoint")
    ending = service.snapshot()
    _assert_paused(ending)
    if _snapshot_date(ending) != joined_date:
        raise RuntimeError("joined checkpoint changed gameplay date")
    mutation_boundary = _mutation_boundary_proof(commands)
    assertions = {
        "owner_subset_retreat_same_day": _snapshot_date(snapshot)
        >= _snapshot_date(initial)
        and post_same == [ANCHOR_CUNIT_ID]
        and post_opposite == pre_opposite,
        "daily_queries_bound": bool(daily_pairs)
        and all(
            isinstance(row.get("pair"), dict)
            and row["pair"].get("binding_ok") is True
            for row in daily_pairs
        ),
        "native_assignment_reopened": assignment.get("ok") is True,
        "typed_aligned_eta": isinstance(eta, int)
        and assigned_date < eta,
        "old_combat_active_until_join": bool(terminal_boundaries)
        and all(row.get("active") is True for row in terminal_boundaries),
        "same_combat_tail_rejoin": rejoin.get("ok") is True,
        "joined_by_eta": joined_date <= eta,
        "assigned_checkpoint_saved": assigned_checkpoint.get("ok") is True,
        "joined_checkpoint_saved": joined_checkpoint.get("ok") is True,
        "production_mutation_boundary": mutation_boundary.get("ok") is True,
    }
    return {
        "ok": all(assertions.values()),
        "outcome": "same_combat_rejoin",
        "initial_snapshot": initial,
        "pre_action_battle_control": pre_action_battle_control,
        "pre_lifecycle": pre_lifecycle,
        "preview": preview,
        "order": order,
        "post_retreat_snapshots": post_retreat_snapshots,
        "post_retreat_battle": post_retreat_battle,
        "assignment_proof": assignment,
        "assigned_pair": assigned_pair,
        "assigned_battle": assigned_battle,
        "assigned_date_raw": assigned_date,
        "assignment_eta_date_raw": eta,
        "assigned_checkpoint": assigned_checkpoint,
        "persistence": persistence,
        "joined_date_raw": joined_date,
        "joined_pair": joined_pair,
        "joined_battle": joined_battle,
        "rejoin_proof": rejoin,
        "joined_checkpoint": joined_checkpoint,
        "daily_pairs": daily_pairs,
        "terminal_boundaries": terminal_boundaries,
        "terminal_outcome": None,
        "advances": advances,
        "ending_snapshot": ending,
        "mutation_boundary_proof": mutation_boundary,
        "assertions": assertions,
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _exact_build_proof(
    capabilities: object, executable_sha256: str
) -> dict[str, object]:
    diagnostics = _diagnostics(capabilities)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    observed_version = hello.get(
        "expected_ck3_version", hello.get("game_version")
    )
    observed_sha = hello.get(
        "expected_ck3_sha256", hello.get("executable_sha256")
    )
    checks = {
        "game_version": observed_version == EXPECTED_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper() == EXPECTED_EXECUTABLE_SHA256,
        "managed_executable_sha256": executable_sha256.upper()
        == EXPECTED_EXECUTABLE_SHA256,
    }
    return {
        "expected_game_version": EXPECTED_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _capability_proof(capabilities: object) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    hello_value = _diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_value = hello.get("capabilities")
    hello_caps = hello_value if isinstance(hello_value, list) else []
    required = (
        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
        QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
        QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
        QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    )
    checks = {
        "bridge_capabilities": all(value in advertised for value in required),
        "hello_capabilities": all(value in hello_caps for value in required),
        "battle_control_surface": raw.get(
            "battle_control_snapshot_v1_query_supported"
        )
        is True,
        "reinforcement_surface": raw.get(
            "battle_reinforcement_assignment_v1_query_supported"
        )
        is True,
        "battle_transition_surface": raw.get(
            "battle_transition_v1_query_supported"
        )
        is True,
        "terminal_surface": raw.get(
            "battle_terminal_transition_v1_query_supported"
        )
        is True,
        "retreat_composition_surface": raw.get(
            "active_combat_retreat_v1_composition_supported"
        )
        is True,
    }
    return {
        "required_bridge_capabilities": list(required),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _same_process_proof(
    before_capabilities: object, after_capabilities: object
) -> dict[str, object]:
    before = _diagnostics(before_capabilities)
    after = _diagnostics(after_capabilities)
    pid = before.get("bridge_pid")
    generation = before.get("connection_generation")
    checks = {
        "same_positive_bridge_pid": isinstance(pid, int)
        and not isinstance(pid, bool)
        and pid > 0
        and after.get("bridge_pid") == pid,
        "same_positive_connection_generation": isinstance(generation, int)
        and not isinstance(generation, bool)
        and generation > 0
        and after.get("connection_generation") == generation,
        "connection_remained_live": before.get("connected") is True
        and after.get("connected") is True,
    }
    return {"checks": checks, "ok": all(checks.values())}


def _run_action_production_session(
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    postcondition_timeout: float,
    *,
    max_assignment_days: int,
    max_eta_days: int,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    driver_closed = False
    readiness: dict[str, object] | None = None
    exact_build: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    sequence: dict[str, object] | None = None
    primary_error: str | None = None
    executable_sha256: str | None = None

    def supervise() -> None:
        try:
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
        owner_live.verify_profile(spec)
        executable_sha256 = owner_live._sha256_file(spec.game_exe)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-owner-subset-reinforcement-rejoin-session",
            daemon=False,
        )
        thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        before_capabilities = driver.capabilities()
        exact_build = _exact_build_proof(
            before_capabilities, executable_sha256
        )
        capability = _capability_proof(before_capabilities)
        if exact_build.get("ok") is not True:
            raise RuntimeError("exact-build proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("rejoin production capabilities are incomplete")

        def wait_after_advance() -> dict[str, object]:
            _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=readiness_timeout,
                stable_seconds=0.0,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                allow_terminal=False,
            )
            return service.snapshot()

        sequence = _run_rejoin_sequence(
            service,
            wait_after_advance=wait_after_advance,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
            postcondition_timeout=postcondition_timeout,
        )
        if sequence.get("ok") is not True:
            raise RuntimeError(
                "owner-subset reinforcement rejoin sequence did not qualify: "
                + str(sequence.get("outcome"))
            )
        same_process = _same_process_proof(
            before_capabilities, driver.capabilities()
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("rejoin proof crossed bridge PID/generation")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
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
            and exact_build
            and exact_build.get("ok") is True
            and capability
            and capability.get("ok") is True
            and sequence
            and sequence.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "production_profile": True,
        "readiness": readiness,
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": owner_live._sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": owner_live._sha256_file(
                config.injector_path
            ),
        },
        "exact_build_proof": exact_build,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "sequence": sequence,
        "readiness_gates": {
            "owner_subset_postcondition_live_ready": bool(
                sequence
                and isinstance(sequence.get("assertions"), dict)
                and sequence["assertions"].get(
                    "owner_subset_retreat_same_day"
                )
                is True
            ),
            "assignment_reopened_aligned_eta_live_ready": bool(
                sequence
                and isinstance(sequence.get("assignment_proof"), dict)
                and sequence["assignment_proof"].get("ok") is True
            ),
            "same_combat_rejoin_live_ready": bool(
                sequence
                and isinstance(sequence.get("rejoin_proof"), dict)
                and sequence["rejoin_proof"].get("ok") is True
            ),
        },
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _action_callback(args: argparse.Namespace) -> Callable[..., dict[str, object]]:
    def run(
        spec: Any,
        config: NativeBridgeLaunchConfig,
        timeout: float,
        readiness_timeout: float,
        postcondition_timeout: float,
    ) -> dict[str, object]:
        return _run_action_production_session(
            spec,
            config,
            timeout,
            readiness_timeout,
            postcondition_timeout,
            max_assignment_days=_positive_int(
                args.max_assignment_days, "max_assignment_days"
            ),
            max_eta_days=_positive_int(args.max_eta_days, "max_eta_days"),
        )

    return run


def _rejoin_gates(action: object) -> dict[str, bool]:
    action = action if isinstance(action, dict) else {}
    gates = action.get("readiness_gates")
    gates = gates if isinstance(gates, dict) else {}
    sequence = action.get("sequence")
    sequence = sequence if isinstance(sequence, dict) else {}
    return {
        "owner_subset_postcondition_live_ready": gates.get(
            "owner_subset_postcondition_live_ready"
        )
        is True,
        "assignment_reopened_aligned_eta_live_ready": gates.get(
            "assignment_reopened_aligned_eta_live_ready"
        )
        is True,
        "same_combat_rejoin_live_ready": gates.get(
            "same_combat_rejoin_live_ready"
        )
        is True,
        "assigned_checkpoint_saved": isinstance(
            sequence.get("assigned_checkpoint"), dict
        )
        and sequence["assigned_checkpoint"].get("ok") is True,
        "joined_checkpoint_saved": isinstance(
            sequence.get("joined_checkpoint"), dict
        )
        and sequence["joined_checkpoint"].get("ok") is True,
    }


def _run_four_stage(
    args: argparse.Namespace,
) -> tuple[dict[str, object], int]:
    payload, _unused_exit = owner_live._run(
        args, action_runner=_action_callback(args)
    )
    action = payload.get("action_production_reload")
    gates = _rejoin_gates(action)
    payload["kind"] = (
        "ck3_owner_subset_reinforcement_rejoin_v1_live_acceptance"
    )
    payload["materialization_mode"] = "v13_four_stage"
    payload["fixed_rejoin"] = {
        "combat_id": COMBAT_ID,
        "withdrawn_public_cunit_id": REJOIN_CUNIT_ID,
        "anchor_public_cunit_id": ANCHOR_CUNIT_ID,
        "opposite_public_cunit_id": OPPOSITE_CUNIT_ID,
        "retreat_target_province_id": RETREAT_TARGET_PROVINCE_ID,
        "requester_identity_claimed": False,
    }
    readiness = payload.get("readiness_gates")
    readiness = readiness if isinstance(readiness, dict) else {}
    readiness.update(gates)
    payload["readiness_gates"] = readiness
    payload["ok"] = bool(payload.get("ok") is True and all(gates.values()))
    return payload, 0 if payload["ok"] else 1


def _run_direct_canonical(
    args: argparse.Namespace,
) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    timeout = owner_live._positive_seconds(args.timeout, "timeout")
    readiness_timeout = owner_live._positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    postcondition_timeout = owner_live._positive_seconds(
        args.postcondition_timeout, "postcondition_timeout"
    )
    max_assignment_days = _positive_int(
        args.max_assignment_days, "max_assignment_days"
    )
    max_eta_days = _positive_int(args.max_eta_days, "max_eta_days")
    expected_sha = owner_live._expected_sha256(
        args.expected_battle_save_sha256
    )
    source_state = args.source_state_dir.expanduser().resolve()
    source_profile = source_state / "profile"
    game_dir = args.game_dir.expanduser().resolve()
    root = owner_live._target_root(args.state_dir)
    output = args.output.expanduser().resolve()
    if not source_profile.is_dir():
        raise owner_live.AgentError(
            f"canonical source profile is missing: {source_profile}"
        )
    if root.exists():
        raise owner_live.AgentError(f"fixture root already exists: {root}")
    owner_live.ensure_state_path_safe(root)
    if owner_live.paths_overlap(source_state, root):
        raise owner_live.AgentError("source and fixture state roots overlap")
    if owner_live.is_relative_to(output, root):
        raise owner_live.AgentError(
            "artifact output must be outside disposable state"
        )
    if owner_live.is_relative_to(output, source_state):
        raise owner_live.AgentError(
            "artifact output must be outside immutable canonical source"
        )
    if output.exists():
        raise owner_live.AgentError(f"artifact output already exists: {output}")
    source_save, source_identity = owner_live._resolve_source_save(
        source_profile, args.battle_save, expected_sha
    )
    source_before = owner_live._sha256_file(source_save)
    nonce = hashlib.sha256(
        f"{source_save}|{time.time_ns()}".encode("utf-8")
    ).hexdigest()
    root.mkdir(parents=True, exist_ok=False)
    owner_live.write_json_atomic(
        root / owner_live._ROOT_MARKER,
        {
            "kind": "xar_owner_subset_retreat_fixture",
            "nonce": nonce,
            "source_state_dir": str(source_state),
            "direct_canonical_source": True,
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
    stage: dict[str, object] | None = None
    action: dict[str, object] | None = None
    primary_error: str | None = None
    try:
        spec, stage = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "action",
            game_dir=game_dir,
            save_source=source_save,
            save_name=owner_live.CONTINUE_SAVE_NAME,
        )
        action = _run_action_production_session(
            spec,
            config,
            timeout,
            readiness_timeout,
            postcondition_timeout,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
        )
        if action.get("ok") is not True:
            primary_error = str(
                action.get("error") or "direct canonical action session failed"
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    source_after = owner_live._sha256_file(source_save)
    source_unchanged = source_before == source_after
    session_cleanup = bool(
        action
        and isinstance(action.get("cleanup"), dict)
        and action["cleanup"].get("ok") is True
        and not owner_live.ck3_processes()
    )
    cleanup = owner_live._cleanup_root(
        root,
        nonce=nonce,
        retain=bool(args.retain_state),
        all_sessions_clean=session_cleanup,
    )
    if not source_unchanged and primary_error is None:
        primary_error = "immutable canonical source changed"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            cleanup.get("reason") or "disposable root cleanup failed"
        )
    gates = _rejoin_gates(action)
    gates.update(
        {
            "source_save_unchanged": source_unchanged,
            "managed_cleanup_ready": session_cleanup,
            "disposable_state_cleanup_ready": cleanup.get("ok") is True,
        }
    )
    ok = bool(
        primary_error is None
        and action
        and action.get("ok") is True
        and all(gates.values())
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_owner_subset_reinforcement_rejoin_v1_live_acceptance",
        "materialization_mode": "direct_canonical_clone",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_rejoin": {
            "combat_id": COMBAT_ID,
            "withdrawn_public_cunit_id": REJOIN_CUNIT_ID,
            "anchor_public_cunit_id": ANCHOR_CUNIT_ID,
            "opposite_public_cunit_id": OPPOSITE_CUNIT_ID,
            "retreat_target_province_id": RETREAT_TARGET_PROVINCE_ID,
            "requester_identity_claimed": False,
        },
        "bounds": {
            "max_assignment_days": max_assignment_days,
            "max_eta_days": max_eta_days,
            "one_game_day_raw": ONE_GAME_DAY_RAW,
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "postcondition_timeout_seconds": postcondition_timeout,
        },
        "policy": {
            "production_non_debug": True,
            "load_kind": "continue_last_save",
            "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        },
        "source_save": source_identity
        | {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "stage": stage,
        "action_production_reload": action,
        "readiness_gates": gates,
        "state_cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    if bool(args.direct_canonical_source):
        return _run_direct_canonical(args)
    return _run_four_stage(args)


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
                "materialization_mode": payload.get("materialization_mode"),
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
