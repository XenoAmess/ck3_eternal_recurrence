"""Authorize exactly one frame-bound Raiktor three-way action plan.

The gate consumes a production recommendation, the current paused snapshot and
the bridge's advertised capabilities.  It never executes the action.  Its
output is the narrow handoff consumed by a managed runner immediately before a
single semantic command.
"""

from __future__ import annotations

from copy import deepcopy

from xar_autoplayer.bridge.war_contract import (
    OFFER_WHITE_PEACE_CAPABILITY,
    SURRENDER_WAR_CAPABILITY,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_recommendation import (
    CONTRACT as RECOMMENDATION_CONTRACT,
    PROVIDER_ID as RECOMMENDATION_PROVIDER_ID,
    PROVIDER_SCHEMA as RECOMMENDATION_PROVIDER_SCHEMA,
)


CONTRACT = "raiktor-three-way-exit-action-gate-v1"
PROVIDER_SCHEMA = "xar.ck3.raiktor_three_way_exit_action_gate.v1"
PROVIDER_ID = "raiktor-three-way-exit-action-gate-provider-v1"

_CAPABILITY_BY_OUTCOME = {
    "continue": None,
    "white_peace": OFFER_WHITE_PEACE_CAPABILITY,
    "surrender": SURRENDER_WAR_CAPABILITY,
}


class ThreeWayExitActionGateError(ValueError):
    """One supplied recommendation, snapshot or capability shape drifted."""


def provide_raiktor_three_way_exit_action_gate(
    recommendation_value: object | None,
    snapshot_value: object | None,
    capabilities_value: object | None,
) -> dict[str, object]:
    """Return one authorization only for the exact current paused frame."""

    missing = [
        reason
        for value, reason in (
            (recommendation_value, "production_recommendation_unavailable"),
            (snapshot_value, "current_snapshot_unavailable"),
            (capabilities_value, "current_capabilities_unavailable"),
        )
        if value is None
    ]
    if missing:
        return _result(blockers=missing)

    recommendation, certificate = _recommendation(recommendation_value)
    blockers: list[str] = []
    if recommendation["production_recommendation_ready"] is not True:
        blockers.append("production_recommendation_not_ready")
    if recommendation["action_ready"] is not True:
        blockers.append("recommendation_action_not_ready")
    if recommendation["blockers"] != []:
        blockers.append("recommendation_has_blockers")

    action_plan = certificate["action_plan"]
    outcome = certificate["recommended_outcome"]
    literal = action_plan["literal"]
    action_plan_ready = action_plan.get("ready") is True
    if outcome not in _CAPABILITY_BY_OUTCOME:
        raise ThreeWayExitActionGateError("recommendation outcome drifted")
    if action_plan_ready and (
        action_plan["semantic_action"] != outcome
        or action_plan["single_action_only"] is not True
        or recommendation["recommended_outcome"] != outcome
        or recommendation["action_literal"] != literal
    ):
        raise ThreeWayExitActionGateError("recommendation action plan drifted")
    if not action_plan_ready and (
        action_plan.get("semantic_action") is not None
        or literal is not None
        or recommendation["action_literal"] is not None
    ):
        raise ThreeWayExitActionGateError("blocked action plan carries a literal")

    snapshot = _snapshot(snapshot_value)
    snapshot_blockers = _snapshot_blockers(
        snapshot, certificate["frame"], outcome=outcome
    )
    blockers.extend(snapshot_blockers)
    capabilities = _capabilities(capabilities_value)
    action_steps = capabilities["action_steps"]
    advertised = capabilities["bridge_capabilities"]
    required_capability = _CAPABILITY_BY_OUTCOME[outcome]
    if literal not in action_steps:
        blockers.append("recommended_action_step_not_advertised")
    if required_capability is not None and required_capability not in advertised:
        blockers.append("recommended_action_capability_not_advertised")
    blockers = _ordered_unique(blockers)
    if blockers:
        return _result(
            blockers=blockers,
            recommendation=recommendation,
            frame=certificate["frame"],
        )

    authorization = {
        "schema_version": 1,
        "contract": CONTRACT,
        "status": "authorized",
        "recommendation_certificate_sha256": certificate[
            "certificate_sha256"
        ],
        "frame": deepcopy(certificate["frame"]),
        "action": {
            "semantic_action": outcome,
            "literal": literal,
            "required_capability": required_capability,
            "expected_revision": snapshot["revision"],
            "war_id": action_plan["war_id"],
            "single_action_only": True,
        },
        "postcondition_plan": deepcopy(certificate["postcondition_plan"]),
        "boundaries": {
            "action_submitted": False,
            "ack_is_postcondition": False,
            "postcondition_verified": False,
            "checkpoint_cold_restore_verified": False,
            "gen034_closed": False,
        },
    }
    authorization["authorization_sha256"] = canonical_policy_input_sha256(
        authorization
    )
    return _result(
        blockers=[],
        recommendation=recommendation,
        frame=certificate["frame"],
        authorization=authorization,
    )


def _recommendation(
    value: object,
) -> tuple[dict[str, object], dict[str, object]]:
    if not isinstance(value, dict) or (
        value.get("schema") != RECOMMENDATION_PROVIDER_SCHEMA
        or value.get("provider") != RECOMMENDATION_PROVIDER_ID
    ):
        raise ThreeWayExitActionGateError("recommendation provider drifted")
    certificate = value.get("recommendation_certificate")
    if not isinstance(certificate, dict) or (
        certificate.get("schema_version") != 1
        or certificate.get("contract") != RECOMMENDATION_CONTRACT
    ):
        raise ThreeWayExitActionGateError("recommendation certificate drifted")
    expected_hash = certificate.get("certificate_sha256")
    unhashed = {key: item for key, item in certificate.items() if key != "certificate_sha256"}
    if expected_hash != canonical_policy_input_sha256(unhashed):
        raise ThreeWayExitActionGateError("recommendation certificate hash drifted")
    for key in (
        "production_recommendation_ready",
        "action_ready",
    ):
        if not isinstance(value.get(key), bool):
            raise ThreeWayExitActionGateError(f"recommendation {key} drifted")
    blockers = value.get("blockers")
    if not isinstance(blockers, list) or not all(
        isinstance(item, str) and item for item in blockers
    ):
        raise ThreeWayExitActionGateError("recommendation blockers drifted")
    return value, certificate


def _snapshot(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitActionGateError("snapshot is malformed")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ThreeWayExitActionGateError("snapshot revision is malformed")
    return value


def _snapshot_blockers(
    snapshot: dict[str, object],
    frame_value: object,
    *,
    outcome: str,
) -> list[str]:
    if not isinstance(frame_value, dict):
        raise ThreeWayExitActionGateError("recommendation frame is malformed")
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    if not isinstance(diagnostics, dict) or not isinstance(played, dict):
        raise ThreeWayExitActionGateError("snapshot identity is malformed")
    connection = frame_value.get("connection_id")
    prefix = "connection-generation:"
    generation = (
        int(connection.removeprefix(prefix))
        if isinstance(connection, str)
        and connection.startswith(prefix)
        and connection.removeprefix(prefix).isdigit()
        else None
    )
    checks = {
        "snapshot_id": snapshot.get("snapshot_id") == frame_value.get("snapshot_id"),
        "revision": snapshot.get("revision") == frame_value.get("snapshot_revision"),
        "native_revision": snapshot.get("native_revision")
        == frame_value.get("native_revision"),
        "date": snapshot.get("date_raw") == frame_value.get("date_raw"),
        "connection": diagnostics.get("connection_generation") == generation,
        "pid": diagnostics.get("bridge_pid") == frame_value.get("ck3_pid"),
        "episode": snapshot.get("episode_run_id") == frame_value.get("episode_id"),
        "player": played.get("character_id")
        == frame_value.get("primary_attacker_character_id"),
        "paused": snapshot.get("paused") is True,
        "event_clear": snapshot.get("active_event") is None,
    }
    wars = snapshot.get("active_wars")
    war_values = wars if isinstance(wars, list) else []
    rows = [
        row
        for row in war_values
        if isinstance(row, dict)
        and row.get("war_id") == frame_value.get("war_id")
        and row.get("primary_opponent_character_id")
        == frame_value.get("primary_defender_character_id")
    ]
    checks["active_war"] = len(rows) == 1
    if outcome in {"white_peace", "surrender"}:
        checks["primary_war_leader"] = bool(
            rows and rows[0].get("player_is_primary_war_leader") is True
        )
    return [f"action_frame_{name}_mismatch" for name, ok in checks.items() if not ok]


def _capabilities(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ThreeWayExitActionGateError("capabilities are malformed")
    result: dict[str, list[str]] = {}
    for key in ("action_steps", "bridge_capabilities"):
        rows = value.get(key)
        if not isinstance(rows, list) or not all(
            isinstance(item, str) and item for item in rows
        ):
            raise ThreeWayExitActionGateError(f"capabilities {key} drifted")
        result[key] = rows
    return result


def _result(
    *,
    blockers: list[str],
    recommendation: dict[str, object] | None = None,
    frame: object | None = None,
    authorization: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": "authorized" if authorization is not None else "blocked",
        "action_ready": authorization is not None,
        "action_literal": (
            authorization["action"]["literal"]
            if authorization is not None
            else None
        ),
        "frame": deepcopy(frame),
        "recommendation_certificate_sha256": (
            authorization["recommendation_certificate_sha256"]
            if authorization is not None
            else None
        ),
        "authorization": authorization,
        "blockers": blockers,
        "recommendation": deepcopy(recommendation),
        "postcondition_verified": False,
        "gen034_closed": False,
    }


def _ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


__all__ = [
    "CONTRACT",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "ThreeWayExitActionGateError",
    "provide_raiktor_three_way_exit_action_gate",
]
