"""Compose action-bound Raiktor loss and truce postwar evidence.

The provider joins an exact source-creation capture to the same full-generation
regiment identities observed before an authorized exit.  It then validates the
native cleanup and two stable persisted-truce reads on the successor paused
frame.  It is pure and performs no CK3 or filesystem operation.
"""

from __future__ import annotations

from copy import deepcopy

from xar_autoplayer.bridge.raiktor_actual_truce_expiry_contract import (
    QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX,
    normalize_raiktor_actual_truce_expiry_v1,
)
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (
    normalize_raiktor_source_specific_capture,
)
from xar_autoplayer.bridge.raiktor_war_bound_loss_cleanup_contract import (
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX,
    normalize_raiktor_war_bound_loss_cleanup_v1,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (
    normalize_raiktor_war_bound_regiment,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_postcondition import (
    POSTWAR_EVIDENCE_SCHEMA,
    normalize_raiktor_three_way_exit_authorization,
)


PROVIDER_SCHEMA = "xar.ck3.raiktor_three_way_exit_postwar_evidence_provider.v1"
PROVIDER_ID = "raiktor-three-way-exit-postwar-evidence-provider-v1"


class ThreeWayExitPostwarEvidenceError(ValueError):
    """A source, frame or native observation crossed its frozen identity."""


def normalize_raiktor_three_way_exit_source_binding(
    action_gate_value: object,
    source_capture_value: object,
    *,
    source_capture_sha256: str,
    active_war_bound_value: object,
) -> dict[str, object]:
    """Bind frozen source generations to the authorized pre-action frame."""

    try:
        authorization = normalize_raiktor_three_way_exit_authorization(
            action_gate_value
        )
    except ValueError as error:
        raise ThreeWayExitPostwarEvidenceError(str(error)) from error
    action = _object(authorization["action"], "authorization action")
    route = action.get("semantic_action")
    if route not in {"white_peace", "surrender"}:
        raise ThreeWayExitPostwarEvidenceError(
            "source binding requires a termination authorization"
        )
    frame = _object(authorization["frame"], "authorization frame")
    plan = _object(
        authorization["postcondition_plan"], "authorization postcondition plan"
    )
    expectations = _object(plan.get("expectations"), "postcondition expectations")
    war_id = _integer(expectations.get("war_id"), "expected WarID", minimum=1)
    attacker_id = _integer(
        expectations.get("played_character_id"),
        "expected player CharacterID",
        minimum=1,
    )
    defender_id = _integer(
        expectations.get("opponent_character_id"),
        "expected opponent CharacterID",
        minimum=1,
    )
    try:
        source = normalize_raiktor_source_specific_capture(
            source_capture_value,
            capture_sha256=source_capture_sha256,
        )
        active = normalize_raiktor_war_bound_regiment(
            active_war_bound_value,
            expected_war_id=war_id,
            expected_attacker_character_id=attacker_id,
            expected_defender_character_id=defender_id,
            expected_snapshot_revision=_integer(
                frame.get("snapshot_revision"), "active revision", minimum=1
            ),
            expected_native_revision=_integer(
                frame.get("native_revision"), "active native revision", minimum=1
            ),
            expected_date_raw=_integer(frame.get("date_raw"), "active date"),
        )
    except ValueError as error:
        raise ThreeWayExitPostwarEvidenceError(str(error)) from error
    source_sets = _source_sets(source)
    active_sets = _observation_sets(active)
    if not _same_source_regiment_identity(source_sets, active_sets):
        raise ThreeWayExitPostwarEvidenceError(
            "active war-bound regiment generations do not match the source capture"
        )
    return {
        "authorization": deepcopy(authorization),
        "route": route,
        "frame": deepcopy(frame),
        "expectations": deepcopy(expectations),
        "war_id": war_id,
        "attacker_id": attacker_id,
        "defender_id": defender_id,
        "source": source,
        "active": active,
        "source_sets": source_sets,
        "active_sets": active_sets,
    }


def provide_raiktor_three_way_exit_postwar_evidence(
    action_gate_value: object,
    source_capture_value: object,
    *,
    source_capture_sha256: str,
    active_war_bound_value: object,
    post_snapshot_value: object,
    cleanup_result_value: object,
    truce_result_values: object,
) -> dict[str, object]:
    """Return one strict postwar evidence packet or typed observed blockers."""

    binding = normalize_raiktor_three_way_exit_source_binding(
        action_gate_value,
        source_capture_value,
        source_capture_sha256=source_capture_sha256,
        active_war_bound_value=active_war_bound_value,
    )
    authorization = binding["authorization"]
    frame = binding["frame"]
    expectations = binding["expectations"]
    war_id = binding["war_id"]
    attacker_id = binding["attacker_id"]
    defender_id = binding["defender_id"]
    source = binding["source"]
    active = binding["active"]
    source_sets = binding["source_sets"]
    active_sets = binding["active_sets"]

    post = _snapshot(post_snapshot_value)
    post_checks = {
        "successor_public_revision": post["revision"] > frame["snapshot_revision"],
        "successor_native_revision": post["native_revision"]
        > frame["native_revision"],
        "nondecreasing_date": post["date_raw"] >= frame["date_raw"],
        "paused": post.get("paused") is True,
        "event_clear": post.get("active_event") is None,
        "old_war_absent": not _war_present(post, war_id),
        "hot_identity": _hot_identity(post, frame=frame, attacker_id=attacker_id),
    }
    if not all(post_checks.values()):
        raise ThreeWayExitPostwarEvidenceError(
            f"postwar frame binding failed: {post_checks}"
        )

    cleanup_step = QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX + str(
        war_id
    )
    try:
        cleanup = normalize_raiktor_war_bound_loss_cleanup_v1(
            cleanup_result_value,
            expected_step=cleanup_step,
            expected_war_id=war_id,
            expected_attacker_character_id=attacker_id,
            expected_defender_character_id=defender_id,
            expected_active_public_revision=frame["snapshot_revision"],
            expected_active_native_revision=frame["native_revision"],
            expected_active_date_raw=frame["date_raw"],
            expected_post_public_revision=post["revision"],
            expected_post_native_revision=post["native_revision"],
            expected_post_date_raw=post["date_raw"],
        )
    except ValueError as error:
        raise ThreeWayExitPostwarEvidenceError(str(error)) from error
    cleanup_observation = _object(
        cleanup.get("observation"), "cleanup observation"
    )
    if _observation_sets(cleanup_observation) != active_sets:
        raise ThreeWayExitPostwarEvidenceError(
            "cleanup generations differ from the source-bound active set"
        )

    truce_expected = _object(expectations.get("truce"), "truce expectations")
    expected_truce_days = _integer(
        truce_expected.get("evaluated_days"),
        "expected truce days",
        minimum=0,
    )
    truce_step = QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX + str(
        defender_id
    )
    truce_values = truce_result_values if isinstance(truce_result_values, list) else []
    if len(truce_values) != 2:
        raise ThreeWayExitPostwarEvidenceError(
            "truce_result_values must contain exactly two reads"
        )
    try:
        first = _normalize_truce_read(
            truce_values[0],
            expected_step=truce_step,
            expected_snapshot_revision=post["native_revision"],
        )
        second = _normalize_truce_read(
            truce_values[1],
            expected_step=truce_step,
            expected_snapshot_revision=post["native_revision"],
        )
    except ValueError as error:
        raise ThreeWayExitPostwarEvidenceError(str(error)) from error
    sequences = [value.get("query_sequence") for value in truce_values]
    if first != second or not (
        _integer(sequences[1], "second truce sequence", minimum=1)
        == _integer(sequences[0], "first truce sequence", minimum=1) + 1
    ):
        raise ThreeWayExitPostwarEvidenceError(
            "persisted truce double-read is not stable and consecutive"
        )

    cleanup_status = _object(
        cleanup_observation.get("cleanup"), "cleanup status"
    ).get("status")
    truce_ready = bool(
        first.get("status") == "available"
        and first.get("readiness") is True
        and first.get("owner_character_id")
        == truce_expected.get("owner_character_id")
        and first.get("toward_character_id")
        == truce_expected.get("toward_character_id")
        and first.get("current_date_raw") == post["date_raw"]
        and first.get("expiry_date_raw")
        == post["date_raw"] + expected_truce_days * 24
    )
    checks = {
        "source_generations_bound": _same_source_regiment_identity(
            source_sets, active_sets
        ),
        "old_war_absent": post_checks["old_war_absent"],
        "source_specific_cleanup_destroyed": cleanup_status == "destroyed",
        "directional_persisted_truce_stable": truce_ready,
    }
    blockers = [name for name, ready in checks.items() if not ready]
    evidence = None
    if not blockers:
        evidence = {
            "schema": POSTWAR_EVIDENCE_SCHEMA,
            "authorization_sha256": authorization["authorization_sha256"],
            "war_id": war_id,
            "post_snapshot_id": post["snapshot_id"],
            "source_specific_loss": {
                "war_id": war_id,
                "status": "destroyed",
                "source_specific_attribution_ready": True,
                "frozen_generation_count": len(active_sets["persistent"]),
                "post_termination_soldiers": 0,
                "source_set_sha256": source["source_set_sha256"],
                "evidence_sha256": canonical_policy_input_sha256(
                    {
                        "source": source,
                        "active": active,
                        "cleanup": cleanup,
                    }
                ),
            },
            "truce": {
                "source": "persisted_native_truce_row",
                "formula_derived": False,
                "from_character_id": first["owner_character_id"],
                "to_character_id": first["toward_character_id"],
                "evaluated_days": expected_truce_days,
                "queried_at_date_raw": first["current_date_raw"],
                "expiry_date_raw": first["expiry_date_raw"],
                "evidence_sha256": canonical_policy_input_sha256(
                    {"first": truce_values[0], "second": truce_values[1]}
                ),
            },
        }
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": "available" if evidence is not None else "red",
        "evidence_ready": evidence is not None,
        "postwar_evidence": deepcopy(evidence),
        "checks": checks,
        "blockers": blockers,
        "boundaries": [
            "source_capture_is_read_only_origin_evidence",
            "war_and_regiment_generations_must_match_the_source_capture",
            "active_army_containers_are_cleanup_context_not_source_identity",
            "command_acknowledgement_is_not_consumed_as_postwar_state",
            "this_provider_performs_no_ck3_or_filesystem_operation",
        ],
    }


def _source_sets(source: dict[str, object]) -> dict[str, object]:
    source_set = _object(source.get("source_set"), "source set")
    return {
        "war_id": source_set.get("war_id"),
        "persistent": tuple(source_set.get("persistent_generation_ids", [])),
        "current": tuple(source_set.get("current_generation_ids", [])),
        "armies": tuple(source_set.get("army_generation_ids", [])),
    }


def _same_source_regiment_identity(
    source_sets: dict[str, object], active_sets: dict[str, object]
) -> bool:
    """Compare stable war/regiment identity, excluding mutable army containers."""

    return all(
        source_sets.get(field) == active_sets.get(field)
        for field in ("war_id", "persistent", "current")
    )


def _normalize_truce_read(
    value: object,
    *,
    expected_step: str,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    result = _object(value, "actual truce-expiry read")
    wire_keys = {
        "step",
        "accepted",
        "query_sequence",
        "snapshot_revision",
        "raiktor_actual_truce_expiry",
        "backend_id",
    }
    if not wire_keys <= set(result) or set(result) - wire_keys not in (
        set(),
        {"actual_truce_expiry_proof"},
    ):
        raise ThreeWayExitPostwarEvidenceError(
            "actual truce-expiry envelope fields changed"
        )
    normalized = normalize_raiktor_actual_truce_expiry_v1(
        {key: deepcopy(result[key]) for key in wire_keys},
        expected_step=expected_step,
        expected_snapshot_revision=expected_snapshot_revision,
    )
    proof = result.get("actual_truce_expiry_proof")
    if proof is not None and proof != normalized:
        raise ThreeWayExitPostwarEvidenceError(
            "driver truce proof differs from the native wire"
        )
    return normalized


def _observation_sets(observation: dict[str, object]) -> dict[str, object]:
    regiments = observation.get("regiments")
    if not isinstance(regiments, list):
        raise ThreeWayExitPostwarEvidenceError(
            "war-bound observation regiments are malformed"
        )
    persistent: set[int] = set()
    current: set[int] = set()
    armies: set[int] = set()
    for value in regiments:
        regiment = _object(value, "war-bound regiment")
        persistent.add(
            _integer(
                regiment.get("persistent_regiment_id"),
                "persistent regiment ID",
            )
        )
        rows = regiment.get("composition_rows")
        if not isinstance(rows, list):
            raise ThreeWayExitPostwarEvidenceError(
                "war-bound composition rows are malformed"
            )
        for row_value in rows:
            row = _object(row_value, "war-bound composition row")
            current_id = row.get("current_army_regiment_id")
            army_id = row.get("raised_carmy_id")
            if current_id is None:
                continue
            current.add(_integer(current_id, "current regiment ID"))
            armies.add(_integer(army_id, "raised army ID"))
    return {
        "war_id": observation.get("war_id"),
        "persistent": tuple(sorted(persistent)),
        "current": tuple(sorted(current)),
        "armies": tuple(sorted(armies)),
    }


def _snapshot(value: object) -> dict[str, object]:
    result = _object(value, "post snapshot")
    for field in ("revision", "native_revision", "date_raw"):
        _integer(result.get(field), f"post snapshot {field}")
    if not isinstance(result.get("snapshot_id"), str) or not result["snapshot_id"]:
        raise ThreeWayExitPostwarEvidenceError(
            "post snapshot ID is malformed"
        )
    if not isinstance(result.get("active_wars"), list):
        raise ThreeWayExitPostwarEvidenceError(
            "post snapshot active_wars is malformed"
        )
    return result


def _hot_identity(
    post: dict[str, object],
    *,
    frame: dict[str, object],
    attacker_id: int,
) -> bool:
    diagnostics = post.get("diagnostics")
    played = post.get("played_character")
    connection = frame.get("connection_id")
    prefix = "connection-generation:"
    expected_connection = (
        int(connection.removeprefix(prefix))
        if isinstance(connection, str)
        and connection.startswith(prefix)
        and connection.removeprefix(prefix).isdigit()
        else None
    )
    return bool(
        isinstance(diagnostics, dict)
        and isinstance(played, dict)
        and expected_connection is not None
        and diagnostics.get("bridge_pid") == frame.get("ck3_pid")
        and diagnostics.get("connection_generation") == expected_connection
        and post.get("episode_run_id") == frame.get("episode_id")
        and played.get("character_id") == attacker_id
    )


def _war_present(snapshot: dict[str, object], war_id: int) -> bool:
    return any(
        isinstance(row, dict) and row.get("war_id") == war_id
        for row in snapshot["active_wars"]
    )


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ThreeWayExitPostwarEvidenceError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ThreeWayExitPostwarEvidenceError(f"{name} must be >= {minimum}")
    return value


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitPostwarEvidenceError(f"{name} must be an object")
    return value


__all__ = [
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "ThreeWayExitPostwarEvidenceError",
    "normalize_raiktor_three_way_exit_source_binding",
    "provide_raiktor_three_way_exit_postwar_evidence",
]
