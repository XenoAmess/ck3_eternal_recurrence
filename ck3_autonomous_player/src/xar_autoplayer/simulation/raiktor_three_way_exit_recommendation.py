"""Compose one bounded Raiktor continue/white-peace/surrender decision.

This provider joins the production-capable immediate-exit evaluator with the
same-frame measured strategic-power certificate.  Continuing the war is a
strategy baseline minus the versioned power-relation tail penalty; it is not a
campaign win forecast.  A production action literal is emitted only when all
inputs are production-live, frame-bound, and one option wins by the configured
minimum margin.
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


CONTRACT = "raiktor-three-way-exit-recommendation-v5"
PROVIDER_SCHEMA = "xar.ck3.raiktor_three_way_exit_recommendation.v4"
PROVIDER_ID = "raiktor-three-way-exit-recommendation-provider-v4"
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

    model = _model_from_provider(model_provider_value)
    relation = dominance["power"]["relation"]
    penalty = _continue_penalty(model, relation=relation)
    continue_option = {
        "measured_power_relation": relation,
        "base_utility_raw": 0,
        "tail_risk_penalty_raw": penalty,
        "utility_raw": -penalty,
        "hard_budget_breaches": [],
        "eligible": True,
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
            "native_execution_availability_excludes_immediate_options": True,
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


def _continue_penalty(model: dict[str, object], *, relation: object) -> int:
    policy = model.get("tail_risk_policy")
    if not isinstance(policy, dict) or policy.get("rule_id") != (
        "measured-power-relation-penalty-v1"
    ):
        raise ThreeWayExitRecommendationError("tail-risk policy is unsupported")
    parameters = policy.get("parameters_raw")
    expected = {
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
    if relation not in key_by_relation:
        raise ThreeWayExitRecommendationError("power relation is unsupported")
    for key in expected:
        _nonnegative_int(parameters[key], f"tail_risk_policy.{key}")
    return int(parameters[key_by_relation[relation]])


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
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "TERMINATION_POSTCONDITIONS",
    "ThreeWayExitRecommendationError",
    "provide_raiktor_three_way_exit_recommendation",
]
