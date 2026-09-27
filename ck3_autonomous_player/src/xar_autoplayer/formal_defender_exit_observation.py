"""Read-only, same-frame exit observation for a losing de-jure defender.

The ordinary tactical planner remains responsible for the next legal move.
This observer preserves the distinction between an executable native option
and its still-unobserved material consequences.  It never emits an exit action.
"""

from __future__ import annotations

from .bridge.war_contract import (
    normalize_war_termination_options,
    query_war_termination_options_step,
)


POLICY = "formal-primary-defender-de-jure-exit-observation-v1"
_CB_KEY = "individual_county_de_jure_cb"
_CB_INDEX = 17
_CACHE_KEYS = {
    "query_sequence", "queried_snapshot_id", "queried_revision",
    "queried_native_revision", "episode_run_id",
    "queried_connection_generation",
}


def observe_primary_defender_de_jure_exit(
    snapshot: dict[str, object] | None,
) -> dict[str, object] | None:
    """Return a typed observation, never a surrender/peace recommendation."""

    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return None
    if snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None:
        return None
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    candidates = [
        war for war in wars
        if isinstance(war, dict)
        and war.get("player_side") == "defender"
        and war.get("player_is_primary_war_leader") is True
        and _positive_id(war.get("war_id")) is not None
        and _negative_score(war.get("player_relative_war_score"))
    ]
    if len(candidates) != 1:
        return None
    war = candidates[0]
    war_id = war["war_id"]
    frame = _frame(snapshot, war)
    if frame is None:
        return None
    rows = snapshot.get("war_termination_options")
    matching = [
        row for row in (rows if isinstance(rows, list) else [])
        if isinstance(row, dict) and row.get("war_id") == war_id
    ]
    if not matching:
        return {
            "policy": POLICY,
            "status": "current_native_options_required",
            "frame": frame,
            "required_observation_step": query_war_termination_options_step(war_id),
            "options": None,
            "material_terms": None,
            "recommended_outcome": None,
            "action_literal": None,
        }
    if len(matching) != 1 or not _same_frame(snapshot, matching[0]):
        return _red(frame, "native_options_frame_or_cardinality_mismatch")
    row = matching[0]
    try:
        options = normalize_war_termination_options(
            {key: value for key, value in row.items() if key not in _CACHE_KEYS},
            expected_war_id=war_id,
        )
    except ValueError:
        return _red(frame, "native_options_schema_invalid")
    cb = options.get("active_casus_belli_identity")
    if not (
        options.get("source") == "native"
        and options.get("player_side") == "defender"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score")
        == war.get("player_relative_war_score")
    ):
        return _red(frame, "native_options_war_identity_mismatch")
    if not (
        options.get("active_casus_belli_present") is True
        and isinstance(cb, dict)
        and cb.get("canonical_key") == _CB_KEY
        and cb.get("database_index") == _CB_INDEX
    ):
        return None
    results = {}
    for name in ("victory", "white_peace", "surrender"):
        option = options["options"][name]
        response = option["recipient_response"]
        terms = option["terms"]
        legal = bool(
            option["context_constructed"] is True
            and option["native_validator_passed"] is True
            and option["available"] is True
        )
        accepted = (
            response["would_accept_now"] is True
            if response["status"] == "available"
            else None
        )
        results[name] = {
            "native_legal_now": legal,
            "recipient_accepts_now": accepted,
            "material_terms_observable": option["terms_observable"],
            "material_terms_status": terms["status"],
            "material_terms_reason": terms.get("reason"),
            "outcome": option["outcome"],
        }
    return {
        "policy": POLICY,
        "status": "native_legality_observed_material_comparison_open",
        "frame": frame,
        "casus_belli": dict(cb),
        "war_duration_days": options["war_duration_days"],
        "options": results,
        "material_terms": {
            "title_holder_and_vassal_effects": None,
            "signed_actor_and_opponent_resources": None,
            "directed_truce": None,
            "continue_war_risk": None,
        },
        "recommended_outcome": None,
        "action_literal": None,
    }


def _frame(snapshot: dict[str, object], war: dict[str, object]) -> dict[str, object] | None:
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    result = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "connection_generation": (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict) else None
        ),
        "played_character_id": (
            played.get("character_id") if isinstance(played, dict) else None
        ),
        "war_id": war["war_id"],
        "player_relative_war_score": war["player_relative_war_score"],
    }
    if (
        not isinstance(result["snapshot_id"], str)
        or not isinstance(result["episode_run_id"], str)
        or not all(
            isinstance(result[key], int) and not isinstance(result[key], bool)
            for key in ("revision", "native_revision", "date_raw", "connection_generation")
        )
        or _positive_id(result["played_character_id"]) is None
    ):
        return None
    return result


def _same_frame(snapshot: dict[str, object], row: dict[str, object]) -> bool:
    diagnostics = snapshot.get("diagnostics")
    connection = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict) else None
    )
    return bool(
        row.get("queried_snapshot_id") == snapshot.get("snapshot_id")
        and row.get("queried_revision") == snapshot.get("revision")
        and row.get("queried_native_revision") == snapshot.get("native_revision")
        and row.get("queried_connection_generation") == connection
        and row.get("episode_run_id") == snapshot.get("episode_run_id")
    )


def _positive_id(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _negative_score(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value < 0


def _red(frame: dict[str, object], reason: str) -> dict[str, object]:
    return {
        "policy": POLICY,
        "status": "observation_red",
        "reason": reason,
        "frame": frame,
        "options": None,
        "material_terms": None,
        "recommended_outcome": None,
        "action_literal": None,
    }


__all__ = ["observe_primary_defender_de_jure_exit"]
