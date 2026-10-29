"""Compose one bounded Raiktor continue/white-peace/surrender decision.

This provider joins the production-capable immediate-exit evaluator with the
same-frame measured strategic-power and opponent-terminal-control certificates.
Continuing the war is a strategy baseline minus the versioned power-relation
tail penalty.  A losing war beyond the configured long-war horizon scales the
opponent-stronger penalty by the already measured exact power ratio; this is
still a strategy input, not a campaign win forecast.  A production action
literal is emitted only when all inputs are production-live, frame-bound, and
one option wins by the configured minimum margin.
"""

from __future__ import annotations

from xar_autoplayer.bridge.war_contract import (
    offer_white_peace_step,
    surrender_war_step,
)
from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (
    normalize_raiktor_campaign_dominance_certificate,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_exit_utility_evaluator import (
    evaluate_raiktor_immediate_exit_utilities,
)


CONTRACT = "raiktor-three-way-exit-recommendation-v7"
PROVIDER_SCHEMA = "xar.ck3.raiktor_three_way_exit_recommendation.v6"
PROVIDER_ID = "raiktor-three-way-exit-recommendation-provider-v6"
OPPONENT_TERMINAL_CONTROL_CONTRACT = "raiktor-opponent-terminal-control-v2"
UTILITY_UNIT = "strategy_utility_q100000"

TERMINATION_POSTCONDITIONS = (
    "old_full_generation_war_id_absent",
    "gold_matches_frozen_terms",
    "attacker_prestige_matches_frozen_terms",
    "directional_truce_days_and_expiry_observed",
    "source_specific_war_bound_regiments_absent",
    "postwar_checkpoint_cold_restore_rebinds_identity",
)
CONTINUE_POSTCONDITIONS = (
    "same_full_generation_war_id_remains_active",
    "same_played_character_and_episode_remain_bound",
    "map_resume_is_observed_on_a_successor_revision",
)


class ThreeWayExitRecommendationError(ValueError):
    """The recommendation inputs are malformed or cross-bound."""


def provide_raiktor_three_way_exit_recommendation(
    white_peace_projection_value: object | None,
    surrender_session_value: object | None,
    power_dominance_certificate_value: object | None,
    budget_provider_value: object | None,
    model_provider_value: object | None,
    opponent_terminal_control_value: object | None = None,
) -> dict[str, object]:
    """Return one three-way recommendation and, when live, one action plan."""

    immediate = evaluate_raiktor_immediate_exit_utilities(
        white_peace_projection_value,
        surrender_session_value,
        budget_provider_value,
        model_provider_value,
    )
    blockers = list(immediate["blockers"])
    if power_dominance_certificate_value is None:
        blockers.append("measured_power_dominance_unavailable")
    if opponent_terminal_control_value is None:
        blockers.append("opponent_terminal_control_unavailable")
    if blockers:
        return _result(immediate=immediate, blockers=blockers)

    certificate_value = immediate.get("evaluation_certificate")
    if not isinstance(certificate_value, dict):
        raise ThreeWayExitRecommendationError(
            "immediate-exit evaluation certificate is unavailable"
        )
    certificate = certificate_value
    if (
        certificate.get("schema_version") != 4
        or certificate.get("utility_unit") != UTILITY_UNIT
        or certificate.get("status") not in {
            "pairwise_preference_available",
            "pairwise_underdetermined",
        }
    ):
        raise ThreeWayExitRecommendationError(
            "immediate-exit evaluation identity drifted"
        )

    try:
        dominance = normalize_raiktor_campaign_dominance_certificate(
            power_dominance_certificate_value
        )
    except ValueError as error:
        raise ThreeWayExitRecommendationError(str(error)) from error
    _require_same_frame(certificate["frame"], dominance["frame"])
    terminal_control = _opponent_terminal_control(
        opponent_terminal_control_value
    )
    _require_terminal_control_same_frame(
        certificate["frame"], terminal_control["frame"]
    )

    model = _model_from_provider(model_provider_value)
    relation = dominance["power"]["relation"]
    tail_risk = _continue_penalty(
        model,
        power=dominance["power"],
        terminal_control=terminal_control,
    )
    penalty = tail_risk["applied_penalty_raw"]
    continue_execution_blockers = (
        ["opponent_has_enforceable_terminal_war_score"]
        if terminal_control["opponent_terminal_control"] is True
        else []
    )
    continue_option = {
        "measured_power_relation": relation,
        "base_utility_raw": 0,
        "tail_risk_penalty_raw": penalty,
        "tail_risk_base_penalty_raw": tail_risk["base_penalty_raw"],
        "tail_risk_power_scale_applied": tail_risk["power_scale_applied"],
        "tail_risk_long_war_scale_start_days": tail_risk[
            "long_war_scale_start_days"
        ],
        "observed_war_duration_days": terminal_control["war_duration_days"],
        "observed_player_relative_war_score": terminal_control[
            "player_relative_war_score"
        ],
        "measured_power_ratio_raw": tail_risk["actual_power_ratio_raw"],
        "measured_power_ratio_scale": tail_risk["fixed_point_scale"],
        "utility_raw": -penalty,
        "hard_budget_breaches": [],
        "execution_blockers": continue_execution_blockers,
        "eligible": not continue_execution_blockers,
        "campaign_outcome_forecast_ready": False,
    }

    immediate_options = certificate.get("options")
    if not isinstance(immediate_options, dict) or set(immediate_options) != {
        "white_peace",
        "surrender",
    }:
        raise ThreeWayExitRecommendationError(
            "immediate-exit option set drifted"
        )
    options = {
        "continue": continue_option,
        "white_peace": _option(immediate_options["white_peace"], "white_peace"),
        "surrender": _option(immediate_options["surrender"], "surrender"),
    }
    comparison_value = certificate.get("comparison")
    if not isinstance(comparison_value, dict):
        raise ThreeWayExitRecommendationError(
            "immediate-exit comparison is unavailable"
        )
    minimum_margin = _nonnegative_int(
        comparison_value.get("minimum_switch_margin_raw"),
        "minimum_switch_margin_raw",
    )
    comparison = _compare(options, minimum_margin=minimum_margin)
    recommendation = comparison["recommended_outcome"]
    production_inputs = (
        immediate.get("production_live_inputs") is True
        and dominance["producer"]["production_live_input"] is True
        and terminal_control["producer"]["production_live_input"] is True
    )
    production_recommendation = bool(
        production_inputs and recommendation is not None
    )
    action_literal = (
        _action_literal(recommendation, war_id=dominance["frame"]["war_id"])
        if production_recommendation
        else None
    )
    requirements = (
        list(CONTINUE_POSTCONDITIONS)
        if recommendation == "continue"
        else list(TERMINATION_POSTCONDITIONS)
        if recommendation in {"white_peace", "surrender"}
        else []
    )
    postcondition_plan = _postcondition_plan(
        outcome=recommendation,
        frame=certificate["frame"],
        options=options,
        surrender_session_value=surrender_session_value,
        requirements=requirements,
    )
    recommendation_certificate = {
        "schema_version": 1,
        "contract": CONTRACT,
        "status": (
            "production_recommendation_available"
            if production_recommendation
            else comparison["status"]
        ),
        "frame": dict(certificate["frame"]),
        "utility_unit": UTILITY_UNIT,
        "input_sha256": {
            "immediate_exit_evaluation_sha256": canonical_policy_input_sha256(
                certificate
            ),
            "power_dominance_sha256": canonical_policy_input_sha256(dominance),
            "utility_model_sha256": canonical_policy_input_sha256(model),
            "opponent_terminal_control_sha256": canonical_policy_input_sha256(
                terminal_control
            ),
        },
        "opponent_terminal_control": {
            "active": terminal_control["opponent_terminal_control"],
            "player_relative_war_score": terminal_control[
                "player_relative_war_score"
            ],
            "attacker_war_score": terminal_control["attacker_war_score"],
            "defender_war_score": terminal_control["defender_war_score"],
            "war_duration_days": terminal_control["war_duration_days"],
        },
        "options": options,
        "comparison": comparison,
        "production_live_inputs": production_inputs,
        "production_recommendation_ready": production_recommendation,
        "recommended_outcome": recommendation,
        "action_plan": {
            "ready": production_recommendation,
            "semantic_action": recommendation if production_recommendation else None,
            "literal": action_literal,
            "war_id": dominance["frame"]["war_id"],
            "single_action_only": True,
        },
        "postcondition_plan": postcondition_plan,
        "boundaries": {
            "measured_power_is_not_campaign_forecast": True,
            "continue_is_strategy_baseline_minus_tail_penalty": True,
            "long_losing_war_may_scale_tail_penalty_by_power_ratio": True,
            "native_execution_availability_excludes_immediate_options": True,
            "opponent_terminal_control_excludes_continue": True,
            "checkpoint_replay_power_input": dominance["schema_version"] == 3,
            "action_submitted": False,
            "postcondition_verified": False,
            "gen034_closed": False,
        },
    }
    recommendation_certificate["certificate_sha256"] = (
        canonical_policy_input_sha256(recommendation_certificate)
    )
    return _result(
        immediate=immediate,
        blockers=[],
        certificate=recommendation_certificate,
    )


def _compare(
    options: dict[str, dict[str, object]], *, minimum_margin: int
) -> dict[str, object]:
    eligible = [
        name for name, option in options.items() if option["eligible"] is True
    ]
    recommendation: str | None = None
    margin: int | None = None
    if eligible:
        ranked = sorted(
            eligible,
            key=lambda name: (-int(options[name]["utility_raw"]), name),
        )
        if len(ranked) == 1:
            recommendation = ranked[0]
        else:
            margin = (
                int(options[ranked[0]]["utility_raw"])
                - int(options[ranked[1]]["utility_raw"])
            )
            if margin >= minimum_margin:
                recommendation = ranked[0]
    return {
        "status": (
            "static_recommendation_available"
            if recommendation is not None
            else "three_way_underdetermined"
        ),
        "eligible_options": eligible,
        "recommended_outcome": recommendation,
        "winning_margin_raw": margin,
        "minimum_switch_margin_raw": minimum_margin,
    }


def _option(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitRecommendationError(f"{name} option is malformed")
    utility = _signed_int(value.get("utility_raw"), f"{name}.utility_raw")
    eligible = value.get("eligible")
    if not isinstance(eligible, bool):
        raise ThreeWayExitRecommendationError(f"{name}.eligible is malformed")
    breaches = value.get("hard_budget_breaches")
    if not isinstance(breaches, list) or not all(
        isinstance(item, str) and item for item in breaches
    ):
        raise ThreeWayExitRecommendationError(
            f"{name}.hard_budget_breaches is malformed"
        )
    return {**value, "utility_raw": utility, "eligible": eligible}


def _model_from_provider(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitRecommendationError("strategy model is unavailable")
    model = value.get("exit_utility_model")
    if (
        value.get("status") != "available"
        or value.get("model_production_eligible") is not True
        or not isinstance(model, dict)
        or model.get("model_production_eligible") is not True
    ):
        raise ThreeWayExitRecommendationError("strategy model is unavailable")
    return model


def _continue_penalty(
    model: dict[str, object],
    *,
    power: dict[str, object],
    terminal_control: dict[str, object],
) -> dict[str, object]:
    policy = model.get("tail_risk_policy")
    if not isinstance(policy, dict) or policy.get("rule_id") != (
        "measured-power-relation-long-war-penalty-v2"
    ):
        raise ThreeWayExitRecommendationError("tail-risk policy is unsupported")
    parameters = policy.get("parameters_raw")
    expected = {
        "long_war_scale_start_days",
        "opponent_stronger_continue_penalty_raw",
        "parity_continue_penalty_raw",
        "player_stronger_continue_penalty_raw",
    }
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ThreeWayExitRecommendationError("tail-risk parameters drifted")
    key_by_relation = {
        "opponent_stronger": "opponent_stronger_continue_penalty_raw",
        "equal": "parity_continue_penalty_raw",
        "actor_stronger": "player_stronger_continue_penalty_raw",
    }
    relation = power.get("relation")
    if relation not in key_by_relation:
        raise ThreeWayExitRecommendationError("power relation is unsupported")
    for key in expected:
        _nonnegative_int(parameters[key], f"tail_risk_policy.{key}")
    ratio = _nonnegative_int(
        power.get("actual_power_ratio_raw"), "actual_power_ratio_raw"
    )
    scale = _nonnegative_int(
        power.get("fixed_point_scale"), "fixed_point_scale"
    )
    if scale == 0:
        raise ThreeWayExitRecommendationError("fixed_point_scale must be positive")
    duration = _nonnegative_int(
        terminal_control.get("war_duration_days"), "war_duration_days"
    )
    score = _signed_int(
        terminal_control.get("player_relative_war_score"),
        "player_relative_war_score",
    )
    start_days = int(parameters["long_war_scale_start_days"])
    base = int(parameters[key_by_relation[relation]])
    power_scale_applied = (
        relation == "opponent_stronger"
        and score < 0
        and duration >= start_days
    )
    applied = base * ratio // scale if power_scale_applied else base
    if applied > 2**63 - 1:
        raise ThreeWayExitRecommendationError("tail-risk penalty overflows int64")
    if power_scale_applied and applied < base:
        raise ThreeWayExitRecommendationError(
            "opponent-stronger power ratio reduced the tail-risk penalty"
        )
    return {
        "base_penalty_raw": base,
        "applied_penalty_raw": applied,
        "power_scale_applied": power_scale_applied,
        "long_war_scale_start_days": start_days,
        "actual_power_ratio_raw": ratio,
        "fixed_point_scale": scale,
    }


def _require_same_frame(
    immediate_frame: object, dominance_frame: object
) -> None:
    if not isinstance(immediate_frame, dict) or not isinstance(
        dominance_frame, dict
    ):
        raise ThreeWayExitRecommendationError("same-frame identity is absent")
    connection = immediate_frame.get("connection_id")
    expected = {
        "snapshot_id": immediate_frame.get("snapshot_id"),
        "snapshot_revision": immediate_frame.get("snapshot_revision"),
        "native_revision": immediate_frame.get("native_revision"),
        "date_raw": immediate_frame.get("date_raw"),
        "connection_generation": (
            int(connection.removeprefix("connection-generation:"))
            if isinstance(connection, str)
            and connection.startswith("connection-generation:")
            and connection.removeprefix("connection-generation:").isdigit()
            else None
        ),
        "episode_run_id": immediate_frame.get("episode_id"),
        "ck3_pid": immediate_frame.get("ck3_pid"),
        "war_id": immediate_frame.get("war_id"),
        "actor_character_id": immediate_frame.get(
            "primary_attacker_character_id"
        ),
        "opponent_character_id": immediate_frame.get(
            "primary_defender_character_id"
        ),
    }
    actual = {key: dominance_frame.get(key) for key in expected}
    if actual != expected or None in expected.values():
        raise ThreeWayExitRecommendationError(
            "immediate-exit and power certificates crossed paused frames"
        )


def _opponent_terminal_control(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control input is malformed"
        )
    if (
        value.get("schema_version") != 2
        or value.get("contract") != OPPONENT_TERMINAL_CONTROL_CONTRACT
        or value.get("status") != "complete"
    ):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control identity drifted"
        )
    frame = value.get("frame")
    if not isinstance(frame, dict):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control frame is malformed"
        )
    if (
        value.get("player_side") != "attacker"
        or value.get("player_is_primary_war_leader") is not True
        or value.get("absolute_war_scores_observable") is not True
    ):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control primary-attacker evidence is incomplete"
        )
    player_score = _signed_int(
        value.get("player_relative_war_score"),
        "opponent_terminal_control.player_relative_war_score",
    )
    attacker_score = _signed_int(
        value.get("attacker_war_score"),
        "opponent_terminal_control.attacker_war_score",
    )
    defender_score = _signed_int(
        value.get("defender_war_score"),
        "opponent_terminal_control.defender_war_score",
    )
    if player_score != attacker_score or defender_score != -attacker_score:
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control war scores disagree"
        )
    war_duration_days = _nonnegative_int(
        value.get("war_duration_days"),
        "opponent_terminal_control.war_duration_days",
    )
    active = value.get("opponent_terminal_control")
    if not isinstance(active, bool) or active is not (player_score <= -100):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control classification drifted"
        )
    source_sha = value.get("source_options_query_sha256")
    if not (
        isinstance(source_sha, str)
        and len(source_sha) == 64
        and all(
            character in "0123456789abcdefABCDEF"
            for character in source_sha
        )
    ):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control source hash is malformed"
        )
    producer = value.get("producer")
    if not isinstance(producer, dict) or not isinstance(
        producer.get("production_live_input"), bool
    ):
        raise ThreeWayExitRecommendationError(
            "opponent terminal-control producer is malformed"
        )
    return {
        **value,
        "frame": dict(frame),
        "player_relative_war_score": player_score,
        "attacker_war_score": attacker_score,
        "defender_war_score": defender_score,
        "war_duration_days": war_duration_days,
        "opponent_terminal_control": active,
        "producer": dict(producer),
    }


def _require_terminal_control_same_frame(
    immediate_frame: object, terminal_frame: object
) -> None:
    if (
        not isinstance(immediate_frame, dict)
        or not isinstance(terminal_frame, dict)
        or terminal_frame != immediate_frame
    ):
        raise ThreeWayExitRecommendationError(
            "immediate-exit and terminal-control inputs crossed paused frames"
        )


def _action_literal(outcome: object, *, war_id: int) -> str:
    if outcome == "continue":
        return "resume-map"
    if outcome == "white_peace":
        return offer_white_peace_step(war_id)
    if outcome == "surrender":
        return surrender_war_step(war_id)
    raise ThreeWayExitRecommendationError("recommended outcome is unavailable")


def _postcondition_plan(
    *,
    outcome: object,
    frame: dict[str, object],
    options: dict[str, dict[str, object]],
    surrender_session_value: object,
    requirements: list[str],
) -> dict[str, object]:
    plan: dict[str, object] = {
        "schema_version": 1,
        "route": outcome,
        "requirements": requirements,
        "expectations": None,
        "verified": False,
        "gen034_completion_eligible": outcome in {"white_peace", "surrender"},
    }
    if outcome == "continue":
        plan["expectations"] = {
            "war_id": frame["war_id"],
            "played_character_id": frame["primary_attacker_character_id"],
            "episode_id": frame["episode_id"],
            "successor_revision_required": True,
        }
        return plan
    if outcome not in {"white_peace", "surrender"}:
        return plan

    selected = options[outcome]
    features = _object(selected.get("features"), f"{outcome}.features")
    session = _object(surrender_session_value, "surrender session")
    aggregate = _object(session.get("aggregate"), "surrender aggregate")
    domains = _object(aggregate.get("domains"), "surrender domains")
    gold = _resource_balance(
        domains,
        domain="gold",
        field="attacker_current_gold",
        expected_character_id=frame["primary_attacker_character_id"],
    )
    prestige = _resource_balance(
        domains,
        domain="prestige",
        field="attacker_current_prestige",
        expected_character_id=frame["primary_attacker_character_id"],
    )
    gold_delta = -_nonnegative_int(
        features.get("primary_gold_transfer_raw"),
        f"{outcome}.primary_gold_transfer_raw",
    )
    prestige_delta = _signed_int(
        features.get("attacker_prestige_delta_raw"),
        f"{outcome}.attacker_prestige_delta_raw",
    )
    truce_days = _nonnegative_int(
        features.get("truce_day_count"), f"{outcome}.truce_day_count"
    )
    plan["expectations"] = {
        "war_id": frame["war_id"],
        "played_character_id": frame["primary_attacker_character_id"],
        "opponent_character_id": frame["primary_defender_character_id"],
        "resources": {
            "scale": 100_000,
            "gold": _resource_expectation(gold, delta_raw=gold_delta),
            "prestige": _resource_expectation(
                prestige, delta_raw=prestige_delta
            ),
        },
        "truce": {
            "owner_character_id": frame["primary_attacker_character_id"],
            "toward_character_id": frame["primary_defender_character_id"],
            "evaluated_days": truce_days,
            "persisted_expiry_required": True,
        },
        "source_specific_loss": {
            "war_id": frame["war_id"],
            "required_cleanup_status": "destroyed",
        },
        "checkpoint": {"cold_restore_required": True},
    }
    return plan


def _resource_balance(
    domains: dict[str, object],
    *,
    domain: str,
    field: str,
    expected_character_id: object,
) -> int:
    domain_value = _object(domains.get(domain), f"{domain} domain")
    payload = _object(domain_value.get("payload"), f"{domain} payload")
    balance = _object(payload.get(field), field)
    value = _object(balance.get("value"), f"{field}.value")
    if balance.get("character_id") != expected_character_id:
        raise ThreeWayExitRecommendationError(
            f"{field} character identity drifted"
        )
    if value.get("scale") != 100_000:
        raise ThreeWayExitRecommendationError(f"{field} scale drifted")
    return _signed_int(value.get("raw"), f"{field}.raw")


def _resource_expectation(pre_raw: int, *, delta_raw: int) -> dict[str, int]:
    post_raw = pre_raw + delta_raw
    if not -(2**63) <= post_raw <= 2**63 - 1:
        raise ThreeWayExitRecommendationError(
            "post-action resource balance overflows int64"
        )
    return {
        "pre_raw": pre_raw,
        "delta_raw": delta_raw,
        "post_raw": post_raw,
    }


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitRecommendationError(f"{name} is malformed")
    return value


def _result(
    *,
    immediate: dict[str, object],
    blockers: list[str],
    certificate: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": (
            certificate["status"] if certificate is not None else "evidence_required"
        ),
        "recommendation_ready": certificate is not None
        and certificate["recommended_outcome"] is not None,
        "production_recommendation_ready": certificate is not None
        and certificate["production_recommendation_ready"] is True,
        "recommended_outcome": (
            certificate["recommended_outcome"] if certificate is not None else None
        ),
        "action_ready": certificate is not None
        and certificate["action_plan"]["ready"] is True,
        "action_literal": (
            certificate["action_plan"]["literal"]
            if certificate is not None
            else None
        ),
        "postcondition_verified": False,
        "gen034_closed": False,
        "recommendation_certificate": certificate,
        "immediate_exit_evaluation": immediate,
        "blockers": blockers,
        "boundaries": [
            "measured_power_relation_is_a_strategy_input_not_a_forecast",
            "repository_tail_penalty_is_versioned_and_replaceable",
            "only_one_margin-winning_action_can_be_emitted",
            "action_ack_does_not_verify_postconditions",
            "gen034_requires_action_postcondition_checkpoint_and_cold_restore",
        ],
    }


def _signed_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ThreeWayExitRecommendationError(f"{name} must be an integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    result = _signed_int(value, name)
    if result < 0:
        raise ThreeWayExitRecommendationError(f"{name} must be nonnegative")
    return result


__all__ = [
    "CONTRACT",
    "CONTINUE_POSTCONDITIONS",
    "OPPONENT_TERMINAL_CONTROL_CONTRACT",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "TERMINATION_POSTCONDITIONS",
    "ThreeWayExitRecommendationError",
    "provide_raiktor_three_way_exit_recommendation",
]
