#!/usr/bin/env python3
"""Capture one managed paused BattleReinforcementAssignmentV1 frame.

The runner owns exactly one CK3 process tree and performs observation only. It
never advances time, submits a command, previews a command, saves, or invokes
the native contact resolver. Two immediate reinforcement queries must agree on
the complete frame. The paused semantic army, committed route, current battle
binding, exact-build identity, and application-main mailbox generation are
then checked before managed cleanup produces the final artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.battle_reinforcement_assignment_contract import (  # noqa: E402
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.battle_transition_contract import (  # noqa: E402
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import make_spec  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
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
EXPECTED_QUERY_SCOPE = (
    "typed_war_entry_route_actual_contact_combat_v3_battle_control_"
    "battle_transition_reinforcement_assignment"
)
FORBIDDEN_NATIVE_CALLS = ("0x2208320", "0x27FB7C0")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--subject-public-cunit-id", type=int, required=True
    )
    parser.add_argument("--expected-target-province-id", type=int)
    parser.add_argument("--require-assigned", action="store_true")
    parser.add_argument("--timeout", type=float, default=420.0)
    parser.add_argument("--readiness-timeout", type=float, default=180.0)
    parser.add_argument(
        "--mailbox-observation-timeout", type=float, default=5.0
    )
    parser.add_argument("--cold-start-checkpoint", action="store_true")
    return parser


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _positive_integer(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def _positive_int32(value: object) -> bool:
    return (
        _positive_integer(value)
        and 1 <= value <= 2**31 - 1
    )


def _same_paused_frame(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return before.get("paused") is True and after.get("paused") is True and all(
        before.get(key) == after.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "episode_run_id",
        )
    )


def _subject_observations(
    snapshot: dict[str, object], subject_public_cunit_id: int
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []

    def collect(
        value: object, source: str, war_id: object = None
    ) -> None:
        for row in value if isinstance(value, list) else []:
            if (
                isinstance(row, dict)
                and row.get("army_id") == subject_public_cunit_id
            ):
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
        tuple(route) if isinstance(route, list) else None,
        army.get("in_combat"),
        army.get("retreating"),
        army.get("army_state_code"),
    )


def _compact_snapshot(
    snapshot: dict[str, object], subject_public_cunit_id: int
) -> dict[str, object]:
    return {
        key: snapshot.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "map_ready",
            "paused",
            "episode_character_id",
            "episode_run_id",
        )
    } | {
        "subject_observations": _subject_observations(
            snapshot, subject_public_cunit_id
        )
    }


def _compact_session_report(report: object) -> object:
    if not isinstance(report, dict):
        return report
    return {
        key: report.get(key)
        for key in (
            "pid",
            "pipe",
            "started_at",
            "finished_at",
            "elapsed_seconds",
            "exit_reason",
            "process_exit_code",
            "restart_count",
            "restart_shutdowns",
            "shutdown",
            "cold_start_checkpoint",
            "ok",
        )
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _heartbeat(capabilities: object) -> dict[str, object]:
    value = _diagnostics(capabilities).get("last_heartbeat")
    return value if isinstance(value, dict) else {}


def _mailbox(capabilities: object) -> dict[str, object]:
    value = _heartbeat(capabilities).get("main_thread_query_mailbox_v1")
    return value if isinstance(value, dict) else {}


def _compact_capability_binding(capabilities: object) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    diagnostics = _diagnostics(raw)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    heartbeat = _heartbeat(raw)
    mailbox = _mailbox(raw)
    return {
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "connected": diagnostics.get("connected"),
        "semantic_state_available": diagnostics.get(
            "semantic_state_available"
        ),
        "hello": {
            key: hello.get(key)
            for key in (
                "pid",
                "expected_ck3_version",
                "expected_ck3_sha256",
                "game_version",
                "executable_sha256",
                "game_adapter_id",
                "game_adapter_status",
                "ck3_build_match",
            )
        },
        "bridge_capabilities": raw.get("bridge_capabilities"),
        "query_supported": raw.get(
            "battle_reinforcement_assignment_v1_query_supported"
        ),
        "heartbeat_sequence": heartbeat.get("sequence"),
        "mailbox": {
            key: mailbox.get(key)
            for key in (
                "query_scope",
                "installed",
                "stop",
                "failure",
                "pump_epochs",
                "consecutive_verified",
                "owner_tid",
                "current_tid",
                "tls_global",
                "tls_context",
                "tls_marker",
                "jomini_state",
                "game_state",
                "date_raw",
                "paused",
                "stamp_read_success",
                "executed_requests",
                "executor_submission_enabled",
                "ready",
            )
        },
    }


def _exact_build_proof(
    capabilities: object, game_executable_sha256: object
) -> dict[str, object]:
    diagnostics = _diagnostics(capabilities)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    version = hello.get("expected_ck3_version", hello.get("game_version"))
    executable_sha = hello.get(
        "expected_ck3_sha256", hello.get("executable_sha256")
    )
    executable_sha = (
        executable_sha.upper() if isinstance(executable_sha, str) else None
    )
    local_sha = (
        game_executable_sha256.upper()
        if isinstance(game_executable_sha256, str)
        else None
    )
    checks = {
        "game_version": version == EXPECTED_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": executable_sha
        == EXPECTED_EXECUTABLE_SHA256,
        "managed_executable_sha256": local_sha
        == EXPECTED_EXECUTABLE_SHA256,
    }
    return {
        "expected_game_version": EXPECTED_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "observed_game_version": version,
        "observed_adapter_id": hello.get("game_adapter_id"),
        "observed_hello_executable_sha256": executable_sha,
        "observed_managed_executable_sha256": local_sha,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _capability_proof(capabilities: object) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    bridge_capabilities = raw.get("bridge_capabilities")
    advertised = (
        isinstance(bridge_capabilities, list)
        and QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
        in bridge_capabilities
    )
    diagnostics = _diagnostics(raw)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_capabilities = hello.get("capabilities")
    hello_advertised = (
        isinstance(hello_capabilities, list)
        and QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
        in hello_capabilities
    )
    checks = {
        "bridge_capability_advertised": advertised,
        "hello_capability_advertised": hello_advertised,
        "driver_query_supported": raw.get(
            "battle_reinforcement_assignment_v1_query_supported"
        )
        is True,
    }
    return {
        "capability": QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _query_pair(
    service: GameplayBridgeService,
    subject_public_cunit_id: int,
    snapshot: dict[str, object],
) -> dict[str, object]:
    revision = snapshot.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise RuntimeError("paused snapshot lacks a valid public revision")
    first = service.query_battle_reinforcement_assignment_v1(
        subject_public_cunit_id,
        expected_revision=revision,
    )
    second = service.query_battle_reinforcement_assignment_v1(
        subject_public_cunit_id,
        expected_revision=revision,
    )
    first_frame = first.get("battle_reinforcement_assignment")
    second_frame = second.get("battle_reinforcement_assignment")
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    frame_equal = isinstance(first_frame, dict) and first_frame == second_frame
    sequence_increased = bool(
        isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence > first_sequence
    )
    binding_equal = all(
        first.get(key) == second.get(key)
        for key in (
            "status",
            "snapshot_revision",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
        )
    )
    return {
        "first": first,
        "second": second,
        "frame_sha256": (
            _canonical_sha256(first_frame)
            if isinstance(first_frame, dict)
            else None
        ),
        "immediate_frame_equal": frame_equal,
        "query_sequence_increased": sequence_increased,
        "binding_equal": binding_equal,
        "ok": frame_equal and sequence_increased and binding_equal,
    }


def _battle_probe_requests(frame: object) -> list[dict[str, object]]:
    if not isinstance(frame, dict) or frame.get("status") != "available":
        return []
    result: list[dict[str, object]] = []
    assignment = frame.get("assignment")
    active_id = (
        assignment.get("active_combat_id")
        if isinstance(assignment, dict)
        else None
    )
    if _positive_int32(active_id):
        result.append({"kind": "active_combat", "combat_id": active_id})
    contact = frame.get("contact_projection")
    contact_id = (
        contact.get("contact_if_now_selected_combat_id")
        if isinstance(contact, dict)
        else None
    )
    if _positive_int32(contact_id) and not any(
        row["combat_id"] == contact_id for row in result
    ):
        result.append({"kind": "contact_if_now", "combat_id": contact_id})
    return result


def _probe_by_id(
    probes: object, combat_id: object
) -> dict[str, object] | None:
    for row in probes if isinstance(probes, list) else []:
        if (
            isinstance(row, dict)
            and row.get("combat_id") == combat_id
            and isinstance(row.get("result"), dict)
        ):
            return row["result"]
    return None


def _battle_transition_matches(
    transition: object,
    *,
    combat_id: int,
    province_id: int,
    subject_public_cunit_id: int,
    subject_must_be_present: bool,
) -> bool:
    if not isinstance(transition, dict):
        return False
    attackers = transition.get(
        "attacker_public_cunit_ids_in_stored_order"
    )
    defenders = transition.get(
        "defender_public_cunit_ids_in_stored_order"
    )
    if not isinstance(attackers, list) or not isinstance(defenders, list):
        return False
    occurrences = [*attackers, *defenders].count(subject_public_cunit_id)
    return bool(
        transition.get("status") == "available"
        and transition.get("battle_transition_ready") is True
        and transition.get("combat_id") == combat_id
        and transition.get("province_id") == province_id
        and occurrences == (1 if subject_must_be_present else 0)
    )


def _consistency_proof(
    snapshot: dict[str, object],
    subject_public_cunit_id: int,
    frame: object,
    battle_probes: object,
    *,
    require_assigned: bool,
    expected_target_province_id: int | None,
) -> dict[str, object]:
    observations = _subject_observations(
        snapshot, subject_public_cunit_id
    )
    armies = [
        row["army"]
        for row in observations
        if isinstance(row.get("army"), dict)
    ]
    signatures = [_army_signature(army) for army in armies]
    semantic_army = armies[0] if armies else {}
    available = bool(
        isinstance(frame, dict)
        and frame.get("status") == "available"
        and frame.get("battle_reinforcement_assignment_ready") is True
    )
    route = frame.get("route") if isinstance(frame, dict) else None
    signal = frame.get("signal") if isinstance(frame, dict) else None
    assignment = (
        frame.get("assignment") if isinstance(frame, dict) else None
    )
    native_order = (
        frame.get("native_order") if isinstance(frame, dict) else None
    )
    route = route if isinstance(route, dict) else {}
    signal = signal if isinstance(signal, dict) else {}
    assignment = assignment if isinstance(assignment, dict) else {}
    native_order = native_order if isinstance(native_order, dict) else {}

    native_rows_value = native_order.get("parent_subunits_in_stored_order")
    native_rows = native_rows_value if isinstance(native_rows_value, list) else []
    subunit_index = frame.get("subunit_stored_index") if isinstance(frame, dict) else None
    selected_row = (
        native_rows[subunit_index]
        if isinstance(subunit_index, int)
        and not isinstance(subunit_index, bool)
        and 0 <= subunit_index < len(native_rows)
        and isinstance(native_rows[subunit_index], dict)
        else {}
    )
    selected_ids = selected_row.get("public_cunit_ids_in_stored_order")
    selected_membership_ok = bool(
        isinstance(selected_ids, list)
        and selected_ids.count(subject_public_cunit_id) == 1
    )

    route_ids = route.get("route_province_ids")
    semantic_route_ids = semantic_army.get("route_province_ids")
    semantic_route_endpoint = (
        semantic_route_ids[-1]
        if isinstance(semantic_route_ids, list) and semantic_route_ids
        else None
    )
    semantic_endpoint_consistent = bool(
        isinstance(semantic_route_ids, list)
        and semantic_army.get("move_target_province_id")
        == semantic_route_endpoint
        and semantic_army.get("move_target_observable")
        is bool(semantic_route_ids)
    )
    native_move_target = route.get("move_target_province_id")
    native_move_target_typed = bool(
        native_move_target is None or _positive_int32(native_move_target)
    )
    route_consistent = bool(
        armies
        and route.get("current_province_id")
        == semantic_army.get("current_province_id")
        and isinstance(route_ids, list)
        and route_ids == semantic_route_ids
        and semantic_endpoint_consistent
        and native_move_target_typed
    )

    assigned = signal.get("assigned_to_help") is True
    target_id = assignment.get("assignment_target_province_id")
    assignment_observed = bool(assigned and _positive_int32(target_id))
    aligned_eta_ready = bool(
        assignment_observed
        and route.get("route_alignment") == "aligned_to_assignment"
        and route.get("move_target_province_id") == target_id
        and (
            isinstance(route_ids, list)
            and (
                bool(route_ids)
                and route_ids[-1] == target_id
                or not route_ids
                and route.get("current_province_id") == target_id
            )
        )
        and isinstance(route.get("arrival_date_raws"), list)
        and len(route["arrival_date_raws"]) == len(route_ids)
        and route.get("assignment_eta_date_raw")
        == (
            route["arrival_date_raws"][-1]
            if route["arrival_date_raws"]
            else frame.get("observed_date_raw")
        )
    )

    in_combat = semantic_army.get("in_combat")
    active_combat_id = assignment.get("active_combat_id")
    active_binding = assignment.get("combat_binding_status")
    battle_binding_consistent = bool(
        (
            in_combat is True
            and _positive_int32(active_combat_id)
            and active_binding == "already_in_active_combat"
        )
        or (
            in_combat is False
            and active_combat_id is None
            and active_binding == "unbound_until_contact"
        )
    )
    active_transition_consistent = True
    if _positive_int32(active_combat_id):
        active_transition_consistent = _battle_transition_matches(
            _probe_by_id(battle_probes, active_combat_id),
            combat_id=active_combat_id,
            province_id=int(route.get("current_province_id", -1)),
            subject_public_cunit_id=subject_public_cunit_id,
            subject_must_be_present=True,
        )

    contact = frame.get("contact_projection") if isinstance(frame, dict) else None
    contact = contact if isinstance(contact, dict) else {}
    contact_id = contact.get("contact_if_now_selected_combat_id")
    contact_consistent = True
    if _positive_int32(contact_id) and contact_id != active_combat_id:
        contact_consistent = bool(
            _positive_int32(target_id)
            and _battle_transition_matches(
                _probe_by_id(battle_probes, contact_id),
                combat_id=contact_id,
                province_id=target_id,
                subject_public_cunit_id=subject_public_cunit_id,
                subject_must_be_present=False,
            )
        )

    expected_target_ok = (
        expected_target_province_id is None
        or target_id == expected_target_province_id
    )
    checks = {
        "available": available,
        "selected_public_cunit_id": isinstance(frame, dict)
        and frame.get("selected_public_cunit_id")
        == subject_public_cunit_id,
        "snapshot_revision": isinstance(frame, dict)
        and frame.get("snapshot_revision") == snapshot.get("native_revision"),
        "observed_date": isinstance(frame, dict)
        and frame.get("observed_date_raw") == snapshot.get("date_raw"),
        "semantic_subject_present": bool(armies),
        "semantic_subject_observations_agree": bool(signatures)
        and len(set(signatures)) == 1,
        "native_selected_subunit_membership": selected_membership_ok,
        "route_matches_semantic_army": route_consistent,
        "battle_binding_matches_semantic_army": battle_binding_consistent,
        "active_battle_transition_matches": active_transition_consistent,
        "contact_if_now_transition_matches": contact_consistent,
        "expected_target_matches": expected_target_ok,
        "required_assignment_observed": not require_assigned
        or assignment_observed,
        "required_aligned_eta_observed": not require_assigned
        or aligned_eta_ready,
    }
    return {
        "checks": checks,
        "subject_observations": observations,
        "route_semantics": {
            "semantic_route_endpoint_province_id": semantic_route_endpoint,
            "native_cunit_0x30_province_id": native_move_target,
            "native_slot_matches_semantic_route_endpoint": (
                native_move_target == semantic_route_endpoint
            ),
            "contract": (
                "CUnit+0x30 is an independent native movement-target slot; "
                "ArmySnapshot move_target_province_id is the remaining-route "
                "endpoint and may differ during active combat"
            ),
        },
        "assignment_observed": assignment_observed,
        "aligned_assignment_eta_ready": aligned_eta_ready,
        "battle_probe_count": len(
            battle_probes if isinstance(battle_probes, list) else []
        ),
        "ok": all(checks.values()),
    }


def _main_thread_generation_proof(
    before_capabilities: object,
    after_capabilities: object,
    snapshot: dict[str, object],
    query_pair: object,
    *,
    expected_executions: int,
) -> dict[str, object]:
    before_diagnostics = _diagnostics(before_capabilities)
    after_diagnostics = _diagnostics(after_capabilities)
    before_mailbox = _mailbox(before_capabilities)
    after_mailbox = _mailbox(after_capabilities)
    before_executed = before_mailbox.get("executed_requests")
    after_executed = after_mailbox.get("executed_requests")
    checks = {
        "same_positive_bridge_pid": _positive_integer(
            before_diagnostics.get("bridge_pid")
        )
        and before_diagnostics.get("bridge_pid")
        == after_diagnostics.get("bridge_pid"),
        "same_positive_connection_generation": _positive_integer(
            before_diagnostics.get("connection_generation")
        )
        and before_diagnostics.get("connection_generation")
        == after_diagnostics.get("connection_generation"),
        "mailbox_installed_ready": after_mailbox.get("installed") is True
        and after_mailbox.get("stop") is False
        and after_mailbox.get("failure") == 0
        and after_mailbox.get("ready") is True
        and after_mailbox.get("executor_submission_enabled") is True,
        "mailbox_scope": after_mailbox.get("query_scope")
        == EXPECTED_QUERY_SCOPE,
        "paused_owner_generation": _positive_integer(
            after_mailbox.get("owner_tid")
        )
        and after_mailbox.get("owner_tid")
        == after_mailbox.get("current_tid")
        and isinstance(after_mailbox.get("consecutive_verified"), int)
        and not isinstance(after_mailbox.get("consecutive_verified"), bool)
        and after_mailbox.get("consecutive_verified", 0) >= 2,
        "tls_main_thread_generation": after_mailbox.get("tls_global") == 1
        and _positive_integer(after_mailbox.get("tls_context"))
        and after_mailbox.get("tls_marker") == 1
        and _positive_integer(after_mailbox.get("jomini_state"))
        and _positive_integer(after_mailbox.get("game_state"))
        and after_mailbox.get("stamp_read_success") is True,
        "paused_date_binding": after_mailbox.get("paused") is True
        and after_mailbox.get("date_raw") == snapshot.get("date_raw"),
        "executed_request_delta": isinstance(before_executed, int)
        and not isinstance(before_executed, bool)
        and isinstance(after_executed, int)
        and not isinstance(after_executed, bool)
        and after_executed >= before_executed + expected_executions,
        "immediate_query_pair": isinstance(query_pair, dict)
        and query_pair.get("ok") is True,
    }
    return {
        "before": _compact_capability_binding(before_capabilities),
        "after": _compact_capability_binding(after_capabilities),
        "expected_executions": expected_executions,
        "observed_execution_delta": (
            after_executed - before_executed
            if isinstance(before_executed, int)
            and not isinstance(before_executed, bool)
            and isinstance(after_executed, int)
            and not isinstance(after_executed, bool)
            else None
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _wait_for_mailbox_generation(
    driver: NativeHeadlessGameplayDriver,
    *,
    before_capabilities: dict[str, object],
    expected_snapshot: dict[str, object],
    expected_executions: int,
    timeout_seconds: float,
    session_done: threading.Event,
    session_state: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    before_executed = _mailbox(before_capabilities).get("executed_requests")
    if (
        isinstance(before_executed, bool)
        or not isinstance(before_executed, int)
        or before_executed < 0
    ):
        raise RuntimeError("initial mailbox execution generation is unavailable")
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, object] | None = None
    while True:
        if session_done.is_set():
            raise RuntimeError(
                "managed CK3 session exited before mailbox observation: "
                f"{session_state!r}"
            )
        capabilities = driver.capabilities()
        snapshot = driver.take_snapshot()
        executed = _mailbox(capabilities).get("executed_requests")
        last = {
            "executed_requests": executed,
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
        }
        if (
            isinstance(executed, int)
            and not isinstance(executed, bool)
            and executed >= before_executed + expected_executions
            and _same_paused_frame(expected_snapshot, snapshot)
        ):
            return capabilities, snapshot
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "mailbox execution generation did not publish in time; "
                f"last={last!r}"
            )
        time.sleep(0.05)


def _read_only_runner_proof() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    run_start = source.index("\ndef _run(") + 1
    run_end = source.index("\ndef main()", run_start)
    run_source = source[run_start:run_end]
    forbidden_runner_calls = (
        "service." + "execute_step(",
        "service." + "save_checkpoint(",
        "service." + "preview_active_combat_retreat_v1(",
        "service." + "order_active_combat_retreat_v1(",
    )
    checks = {
        "no_generic_or_mutating_service_call": not any(
            token in run_source for token in forbidden_runner_calls
        ),
        "reinforcement_query_present": (
            "service.query_battle_reinforcement_assignment_v1(" in source
        ),
        "transition_query_is_read_only": (
            "service.query_battle_transition_v1(" in source
        ),
    }
    return {
        "mode": "managed_paused_read_only",
        "allowed_native_read_helpers": [
            "0x22475E0",
            "0x2247320",
            "0x2900470",
        ],
        "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        "forbidden_native_calls_invoked": [],
        "mutation_commands_executed": [],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    spec = make_spec(args.state_dir, args.game_dir)
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.resolve(),
        injector_path=args.bridge_injector.resolve(),
    )
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    primary_error: str | None = None
    readiness: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    initial_snapshot: dict[str, object] | None = None
    ending_snapshot: dict[str, object] | None = None
    query_pair: dict[str, object] | None = None
    battle_probes: list[dict[str, object]] = []
    exact_build: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    main_thread_generation: dict[str, object] | None = None
    consistency: dict[str, object] | None = None
    driver_closed = False
    game_executable_sha256: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=float(args.timeout) + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=bool(args.cold_start_checkpoint),
                stop_event=stop_event,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        game_executable_sha256 = _sha256_file(spec.game_exe)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-battle-reinforcement-live-session",
            daemon=False,
        )
        session_thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=float(args.readiness_timeout),
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=bool(args.cold_start_checkpoint),
            allow_terminal=False,
        )
        capabilities_before = driver.capabilities()
        initial_snapshot = service.snapshot()
        exact_build = _exact_build_proof(
            capabilities_before, game_executable_sha256
        )
        capability = _capability_proof(capabilities_before)
        if exact_build.get("ok") is not True:
            raise RuntimeError("exact-build identity proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("reinforcement query capability is unavailable")
        if not _subject_observations(
            initial_snapshot, args.subject_public_cunit_id
        ):
            raise RuntimeError("subject public CUnit is absent from snapshot")

        query_pair = _query_pair(
            service, args.subject_public_cunit_id, initial_snapshot
        )
        if query_pair.get("ok") is not True:
            raise RuntimeError("immediate reinforcement query frames differ")
        first = query_pair.get("first")
        frame = (
            first.get("battle_reinforcement_assignment")
            if isinstance(first, dict)
            else None
        )
        for request in _battle_probe_requests(frame):
            combat_id = int(request["combat_id"])
            bridge_capabilities = capabilities_before.get(
                "bridge_capabilities"
            )
            if not (
                isinstance(bridge_capabilities, list)
                and QUERY_BATTLE_TRANSITION_V1_CAPABILITY
                in bridge_capabilities
            ):
                raise RuntimeError(
                    "battle consistency requires the read-only transition query"
                )
            result = service.query_battle_transition_v1(
                combat_id,
                expected_revision=int(initial_snapshot["revision"]),
            )
            battle_probes.append({**request, "result": result})

        expected_executions = 2 + len(battle_probes)
        capabilities_after, ending_snapshot = _wait_for_mailbox_generation(
            driver,
            before_capabilities=capabilities_before,
            expected_snapshot=initial_snapshot,
            expected_executions=expected_executions,
            timeout_seconds=float(args.mailbox_observation_timeout),
            session_done=session_done,
            session_state=session_state,
        )
        main_thread_generation = _main_thread_generation_proof(
            capabilities_before,
            capabilities_after,
            initial_snapshot,
            query_pair,
            expected_executions=expected_executions,
        )
        consistency = _consistency_proof(
            initial_snapshot,
            args.subject_public_cunit_id,
            frame,
            battle_probes,
            require_assigned=bool(args.require_assigned),
            expected_target_province_id=args.expected_target_province_id,
        )
        failed = [
            name
            for name, proof in (
                ("main_thread_generation", main_thread_generation),
                ("army_battle_route_consistency", consistency),
                ("read_only_runner", _read_only_runner_proof()),
            )
            if proof.get("ok") is not True
        ]
        if failed:
            raise RuntimeError(
                "reinforcement live acceptance gates failed: "
                + ", ".join(failed)
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None:
            session_thread.join()
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
    read_only = _read_only_runner_proof()
    ok = bool(
        primary_error is None
        and exact_build is not None
        and exact_build.get("ok") is True
        and capability is not None
        and capability.get("ok") is True
        and query_pair is not None
        and query_pair.get("ok") is True
        and main_thread_generation is not None
        and main_thread_generation.get("ok") is True
        and consistency is not None
        and consistency.get("ok") is True
        and ending_snapshot is not None
        and initial_snapshot is not None
        and _same_paused_frame(initial_snapshot, ending_snapshot)
        and read_only.get("ok") is True
        and cleanup.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_battle_reinforcement_assignment_v1_live_acceptance",
        "started_at": started_wall,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "load_kind": (
            "cold_checkpoint"
            if args.cold_start_checkpoint
            else "continue_last_save"
        ),
        "subject_public_cunit_id": args.subject_public_cunit_id,
        "require_assigned": bool(args.require_assigned),
        "expected_target_province_id": args.expected_target_province_id,
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": game_executable_sha256,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": _sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": _sha256_file(config.injector_path),
        },
        "readiness": readiness,
        "exact_build_proof": exact_build,
        "capability_proof": capability,
        "main_thread_generation_proof": main_thread_generation,
        "initial_snapshot": (
            _compact_snapshot(
                initial_snapshot, args.subject_public_cunit_id
            )
            if initial_snapshot is not None
            else None
        ),
        "ending_snapshot": (
            _compact_snapshot(
                ending_snapshot, args.subject_public_cunit_id
            )
            if ending_snapshot is not None
            else None
        ),
        "query_pair": query_pair,
        "battle_probes": battle_probes,
        "consistency_proof": consistency,
        "read_only_proof": read_only,
        "readiness_gates": {
            "exact_build_ready": bool(
                exact_build and exact_build.get("ok") is True
            ),
            "capability_advertised": bool(
                capability and capability.get("ok") is True
            ),
            "main_thread_generation_ready": bool(
                main_thread_generation
                and main_thread_generation.get("ok") is True
            ),
            "immediate_pair_stable": bool(
                query_pair and query_pair.get("ok") is True
            ),
            "army_battle_route_consistent": bool(
                consistency and consistency.get("ok") is True
            ),
            "native_assignment_observed": bool(
                consistency
                and consistency.get("assignment_observed") is True
            ),
            "aligned_assignment_eta_live_ready": bool(
                consistency
                and consistency.get("aligned_assignment_eta_ready") is True
            ),
            "read_only_boundary": read_only.get("ok") is True,
            "managed_cleanup": cleanup.get("ok") is True,
        },
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    if not _positive_int32(args.subject_public_cunit_id):
        raise SystemExit("--subject-public-cunit-id must be a positive int32")
    if (
        args.expected_target_province_id is not None
        and not _positive_int32(args.expected_target_province_id)
    ):
        raise SystemExit(
            "--expected-target-province-id must be a positive int32"
        )
    if args.timeout <= 0 or args.readiness_timeout <= 0:
        raise SystemExit("session/readiness timeouts must be positive")
    if args.mailbox_observation_timeout <= 0:
        raise SystemExit("--mailbox-observation-timeout must be positive")
    payload, exit_code = _run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "output": str(args.output.resolve()),
                "frame_sha256": (
                    payload.get("query_pair", {}).get("frame_sha256")
                    if isinstance(payload.get("query_pair"), dict)
                    else None
                ),
                "readiness_gates": payload["readiness_gates"],
                "cleanup": payload["cleanup"],
                "error": payload["error"],
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
