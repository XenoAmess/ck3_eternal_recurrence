"""Use current native reads for one Raiktor three-way war-exit decision.

Continue hands the choice to the existing bounded tactical planner.  It does
not execute direct resume-map, which failed to yield a successor in R661.
"""

from __future__ import annotations

from typing import Iterable

from .bridge.war_contract import (
    normalize_war_termination_options,
    offer_white_peace_step,
    query_war_termination_options_step,
    query_war_termination_terms_step,
    surrender_war_step,
)
from .bridge.war_entry_contract import query_war_entry_assessments_step
from .simulation.raiktor_campaign_dominance_provider import provide_raiktor_campaign_dominance
from .simulation.raiktor_continue_vs_surrender_policy import canonical_policy_input_sha256
from .simulation.raiktor_exit_utility_model_provider import provide_raiktor_exit_utility_model
from .simulation.raiktor_owner_budget_profile_provider import provide_raiktor_owner_budget_profile
from .simulation.raiktor_three_way_exit_action_gate import provide_raiktor_three_way_exit_action_gate
from .simulation.raiktor_three_way_exit_recommendation import (
    OPPONENT_TERMINAL_CONTROL_CONTRACT,
    provide_raiktor_three_way_exit_recommendation,
)
from .simulation.raiktor_white_peace_narrow_projection_provider import provide_raiktor_white_peace_narrow_projection

POLICY = "raiktor-formal-three-way-exit-v1"
TRACE_FIELD = "war_entry_assessments_two_read_trace_v1"


def plan_raiktor_formal_exit(
    snapshot: dict[str, object] | None,
    commands: Iterable[dict[str, object]],
    *,
    action_steps: Iterable[str],
    bridge_capabilities: Iterable[str],
) -> dict[str, object] | None:
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return None
    if snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None:
        return None
    options_rows = snapshot.get("war_termination_options")
    if not isinstance(options_rows, list):
        return None
    rows = [
        row for row in options_rows
        if isinstance(row, dict)
        and isinstance(row.get("active_casus_belli_identity"), dict)
        and row["active_casus_belli_identity"].get("canonical_key") == "raiktor_claim_cb"
    ]
    if not rows:
        return None
    if len(rows) != 1:
        return _blocked("multiple_current_raiktor_wars")
    war_id = _positive_id(rows[0].get("war_id"))
    if war_id is None:
        return _blocked("raiktor_war_id_unavailable")
    wars = snapshot.get("active_wars")
    matches = [
        war for war in (wars if isinstance(wars, list) else [])
        if isinstance(war, dict) and war.get("war_id") == war_id
    ]
    if len(matches) != 1:
        return _blocked("current_raiktor_war_identity_unavailable", war_id)
    war = matches[0]
    opponent = _positive_id(war.get("primary_opponent_character_id"))
    if not (
        opponent is not None
        and war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
    ):
        return _blocked("raiktor_primary_attacker_binding_unavailable", war_id)
    if isinstance(war.get("player_relative_war_score"), int) and war["player_relative_war_score"] >= 100:
        return None  # existing native enforce-demands branch has priority
    steps = set(action_steps)
    capabilities = set(bridge_capabilities)
    history = _history_since_latest_restore(commands)
    if any(
        row.get("ok") is not False
        and row.get("command") in {offer_white_peace_step(war_id), surrender_war_step(war_id)}
        for row in history
    ):
        return _blocked("previous_terminal_submission_requires_fresh_status", war_id)
    options_query = _current_query(
        history, snapshot, query_war_termination_options_step(war_id),
        episode_field="queried_episode_run_id",
    )
    if options_query is None:
        return _query_or_block(
            query_war_termination_options_step(war_id), steps,
            "native_war_raiktor_threeway_options_query", war_id,
        )
    trace = snapshot.get(TRACE_FIELD)
    trace_rows = [
        entry for entry in (trace if isinstance(trace, list) else [])
        if isinstance(entry, dict) and entry.get("target_character_id") == opponent
    ]
    if len(trace_rows) < 2:
        return _query_or_block(
            query_war_entry_assessments_step([opponent]), steps,
            "native_war_raiktor_threeway_power_query", war_id,
        )
    if len(trace_rows) != 2:
        return _blocked("power_double_read_trace_drifted", war_id)
    terms_query = _current_query(
        history, snapshot, query_war_termination_terms_step(war_id),
        episode_field="episode_run_id",
    )
    if terms_query is None:
        return _query_or_block(
            query_war_termination_terms_step(war_id), steps,
            "native_war_raiktor_threeway_terms_query", war_id,
        )
    try:
        first, second = trace_rows
        dominance_input = {
            "before": first["before_snapshot"], "first": first["query"],
            "between": first["after_snapshot"], "second": second["query"],
            "after": second["after_snapshot"],
        }
        dominance = provide_raiktor_campaign_dominance(
            dominance_input["before"], dominance_input["first"],
            dominance_input["between"], dominance_input["second"],
            dominance_input["after"], war_id=war_id,
            opponent_character_id=opponent,
            source_artifact_sha256=canonical_policy_input_sha256(dominance_input),
        )
        white = provide_raiktor_white_peace_narrow_projection(
            snapshot, options_query, terms_query, production_live=True,
        )
        terminal_control = _opponent_terminal_control_input(
            war=war,
            war_id=war_id,
            opponent_character_id=opponent,
            options_query=options_query,
            white_peace_projection=white,
        )
        recommendation = provide_raiktor_three_way_exit_recommendation(
            white, terms_query.get("raiktor_surrender_aggregate_session"),
            dominance["campaign_dominance_certificate"],
            provide_raiktor_owner_budget_profile(None),
            provide_raiktor_exit_utility_model(),
            terminal_control,
        )
        gate = provide_raiktor_three_way_exit_action_gate(
            recommendation, snapshot,
            {"action_steps": sorted(steps), "bridge_capabilities": sorted(capabilities)},
        )
    except (KeyError, TypeError, ValueError) as error:
        return _blocked(f"same_frame_provider_red:{type(error).__name__}:{error}", war_id)
    if recommendation.get("production_recommendation_ready") is not True or gate.get("action_ready") is not True:
        return _blocked(
            "threeway_recommendation_or_action_gate_unready", war_id,
            blockers=[*recommendation.get("blockers", []), *gate.get("blockers", [])],
        )
    try:
        utility_comparison = _utility_comparison_trace(
            recommendation["recommendation_certificate"]
        )
    except (KeyError, TypeError, ValueError) as error:
        return _blocked(f"same_frame_utility_trace_red:{type(error).__name__}:{error}", war_id)
    outcome = recommendation.get("recommended_outcome")
    decision = {
        "policy": POLICY,
        "war_id": war_id,
        "opponent_character_id": opponent,
        "frame": recommendation["recommendation_certificate"]["frame"],
        "recommended_outcome": outcome,
        "recommendation_certificate_sha256": recommendation["recommendation_certificate"]["certificate_sha256"],
        "utility_comparison": utility_comparison,
        "outcome_gate_authorization_sha256": gate["authorization"]["authorization_sha256"],
        "outcome_gate_authorized_literal": gate["authorization"]["action"]["literal"],
        "same_frame_power_double_read": True,
        "action_submitted": False,
        "independent_postcondition_verified": False,
        "cold_restore_verified": False,
        "gen034_closed": False,
    }
    if outcome == "continue":
        decision["bounded_action_authorization"] = "separate-core-step-legality"
        return {"status": "continue_ready", "decision": decision}
    literal = recommendation.get("action_literal")
    if outcome not in {"white_peace", "surrender"} or not isinstance(literal, str):
        return _blocked("threeway_outcome_literal_drifted", war_id)
    if literal not in steps:
        return _blocked("terminal_action_unregistered", war_id, blockers=[literal])
    return {
        "policy": POLICY,
        "phase": "native_war_raiktor_threeway_terminal",
        "selected_step": literal,
        "war_exit_decision": decision,
        "reason": "one same-frame legal terminal wins the versioned three-way utility comparison",
    }


def _utility_comparison_trace(certificate: dict[str, object]) -> dict[str, object]:
    """Copy the versioned three-way ranking inputs without changing the choice."""
    options = certificate["options"]
    comparison = certificate["comparison"]
    rows = {}
    for name in ("continue", "white_peace", "surrender"):
        option = options[name]
        rows[name] = {
            "eligible": option["eligible"],
            "utility_raw": option["utility_raw"],
            "hard_budget_breaches": list(option["hard_budget_breaches"]),
            "execution_blockers": list(option.get("execution_blockers", [])),
        }
        if name == "continue":
            rows[name]["measured_power_relation"] = option["measured_power_relation"]
            rows[name]["tail_risk_penalty_raw"] = option["tail_risk_penalty_raw"]
            rows[name]["tail_risk_base_penalty_raw"] = option[
                "tail_risk_base_penalty_raw"
            ]
            rows[name]["tail_risk_power_scale_applied"] = option[
                "tail_risk_power_scale_applied"
            ]
            rows[name]["observed_war_duration_days"] = option[
                "observed_war_duration_days"
            ]
            rows[name]["observed_player_relative_war_score"] = option[
                "observed_player_relative_war_score"
            ]
            rows[name]["measured_power_ratio_raw"] = option[
                "measured_power_ratio_raw"
            ]
            rows[name]["measured_power_ratio_scale"] = option[
                "measured_power_ratio_scale"
            ]
        else:
            rows[name]["uncertainty_penalty_raw"] = option["uncertainty_penalty_raw"]
    return {
        "schema_version": 1,
        "utility_unit": certificate["utility_unit"],
        "options": rows,
        "comparison": {
            "status": comparison["status"],
            "eligible_options": list(comparison["eligible_options"]),
            "winning_margin_raw": comparison["winning_margin_raw"],
            "minimum_switch_margin_raw": comparison["minimum_switch_margin_raw"],
        },
    }


def _opponent_terminal_control_input(
    *,
    war: dict[str, object],
    war_id: int,
    opponent_character_id: int,
    options_query: dict[str, object],
    white_peace_projection: dict[str, object],
) -> dict[str, object]:
    normalized = normalize_war_termination_options(
        options_query.get("war_termination_options"),
        expected_war_id=war_id,
    )
    active_score = war.get("player_relative_war_score")
    if isinstance(active_score, bool) or not isinstance(active_score, int):
        raise ValueError("active Raiktor war score is unavailable")
    if (
        normalized["player_side"] != "attacker"
        or normalized["player_is_primary_war_leader"] is not True
        or normalized["absolute_war_scores_observable"] is not True
        or normalized["player_relative_war_score"] != active_score
        or normalized["attacker_war_score"] != active_score
        or normalized["defender_war_score"] != -active_score
    ):
        raise ValueError(
            "same-frame Raiktor terminal-control scores are incomplete or drifted"
        )
    war_duration_days = normalized.get("war_duration_days")
    if (
        isinstance(war_duration_days, bool)
        or not isinstance(war_duration_days, int)
        or war_duration_days < 0
    ):
        raise ValueError("same-frame Raiktor war duration is unavailable")
    active_duration = war.get("war_duration_days")
    if active_duration is not None and active_duration != war_duration_days:
        raise ValueError("same-frame Raiktor war duration drifted")
    observation = white_peace_projection.get("white_peace_observation")
    frame = observation.get("frame") if isinstance(observation, dict) else None
    if not isinstance(frame, dict) or (
        frame.get("war_id") != war_id
        or frame.get("primary_defender_character_id") != opponent_character_id
    ):
        raise ValueError("Raiktor terminal-control frame is unavailable")
    return {
        "schema_version": 2,
        "contract": OPPONENT_TERMINAL_CONTROL_CONTRACT,
        "status": "complete",
        "frame": dict(frame),
        "player_side": "attacker",
        "player_is_primary_war_leader": True,
        "player_relative_war_score": active_score,
        "absolute_war_scores_observable": True,
        "attacker_war_score": active_score,
        "defender_war_score": -active_score,
        "war_duration_days": war_duration_days,
        "opponent_terminal_control": active_score <= -100,
        "source_options_query_sha256": canonical_policy_input_sha256(
            normalized
        ),
        "producer": {
            "producer_id": "raiktor-formal-exit-terminal-control-v1",
            "production_live_input": True,
        },
    }


def _current_query(
    rows: list[dict[str, object]], snapshot: dict[str, object],
    step: str, *, episode_field: str,
) -> dict[str, object] | None:
    diagnostics = snapshot.get("diagnostics")
    connection = diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None
    for row in reversed(rows):
        result = row.get("result")
        if (
            row.get("command") == step and row.get("ok") is True
            and isinstance(result, dict)
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == snapshot.get("native_revision")
            and result.get("queried_connection_generation", connection) == connection
            and result.get(episode_field) == snapshot.get("episode_run_id")
        ):
            return result
    return None


def _history_since_latest_restore(
    commands: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    rows = [row for row in commands if isinstance(row, dict)]
    for index in range(len(rows) - 1, -1, -1):
        if rows[index].get("command") == "restore-checkpoint":
            return rows[index + 1:]
    return rows


def _positive_id(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _query_or_block(step: str, steps: set[str], phase: str, war_id: int) -> dict[str, object]:
    if step not in steps:
        return _blocked(f"{phase}_unregistered", war_id, blockers=[step])
    return {
        "policy": POLICY, "phase": phase, "selected_step": step, "war_id": war_id,
        "reason": "obtain one independent read on the unchanged paused war frame before selecting an outcome",
    }


def _blocked(
    reason: str, war_id: int | None = None, *,
    blockers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "policy": POLICY, "phase": "native_war_raiktor_threeway_blocked",
        "selected_step": None, "war_id": war_id, "reason": reason,
        "blockers": blockers or [], "gen034_closed": False,
    }


__all__ = [
    "POLICY",
    "TRACE_FIELD",
    "plan_raiktor_formal_exit",
]
