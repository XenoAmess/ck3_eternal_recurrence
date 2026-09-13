"""Evaluate immediate Raiktor exits with the versioned strategy model.

This pure provider compares white peace with surrender.  Continue-war value is
deliberately left to the next integration package because measured strategic
power is not a campaign forecast.  The evaluator consumes only a same-frame
white-peace projection, its bound surrender aggregate, the versioned budget
provider and the versioned utility-model provider.
"""

from __future__ import annotations

from xar_autoplayer.bridge.raiktor_surrender_session_binding_contract import (
    normalize_raiktor_surrender_aggregate_session_binding,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_exit_utility_model_provider import (
    MODEL_CONTRACT,
    PROVIDER_ID as MODEL_PROVIDER_ID,
    PROVIDER_SCHEMA as MODEL_PROVIDER_SCHEMA,
    UTILITY_UNIT,
)
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (
    PROVIDER_SCHEMA as BUDGET_PROVIDER_SCHEMA,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    OWNER_BUDGET_PROVIDER,
    normalize_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_contracts import (
    normalize_white_peace_terms_observation,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (
    PROVIDER_ID as PROJECTION_PROVIDER_ID,
    PROVIDER_SCHEMA as PROJECTION_PROVIDER_SCHEMA,
)


CONTRACT = "raiktor-white-peace-vs-surrender-utility-evaluation-v4"
PROVIDER_SCHEMA = "xar.ck3.raiktor_exit_utility_evaluator.v3"
PROVIDER_ID = "raiktor-immediate-exit-utility-evaluator-v3"
_FIXED_POINT_FEATURES = {
    "primary_gold_transfer_raw",
    "attacker_prestige_delta_raw",
}
_FEATURE_KEYS = {
    "primary_gold_transfer_raw",
    "attacker_prestige_delta_raw",
    "declared_claim_removed_count",
    "favor_hook_applied",
    "truce_day_count",
    "pow_release_count",
    "title_holder_change_count",
    "hostage_transfer_count",
    "war_bound_soldier_loss_count",
}


class ExitUtilityEvaluationError(ValueError):
    """One immediate-exit evaluation input is malformed or cross-bound."""


def evaluate_raiktor_immediate_exit_utilities(
    white_peace_projection_value: object | None,
    surrender_session_value: object | None,
    budget_provider_value: object | None,
    model_provider_value: object | None,
) -> dict[str, object]:
    """Compare white peace and surrender without authorizing an action."""

    missing = [
        reason
        for value, reason in (
            (
                white_peace_projection_value,
                "white_peace_narrow_projection_unavailable",
            ),
            (surrender_session_value, "surrender_session_unavailable"),
            (budget_provider_value, "strategy_budget_profile_unavailable"),
            (model_provider_value, "strategy_utility_model_unavailable"),
        )
        if value is None
    ]
    if missing:
        return _result(blockers=missing)

    projection, observation = _normalize_projection(
        white_peace_projection_value
    )
    frame = observation["frame"]
    session = _normalize_session(surrender_session_value, frame=frame)
    aggregate = session["aggregate"]
    aggregate_sha = canonical_policy_input_sha256(aggregate)
    if observation["evaluated_surrender_terms_sha256"] != aggregate_sha:
        raise ExitUtilityEvaluationError(
            "white-peace projection and surrender aggregate hashes differ"
        )
    budget, budget_version = _normalize_budget_provider(
        budget_provider_value
    )
    model = _normalize_model_provider(model_provider_value)
    _require_model_budget_binding(
        model,
        budget=budget,
        budget_version=budget_version,
    )

    white_features = _white_features(observation)
    surrender_features = _surrender_features(projection)
    white_breaches = _white_budget_breaches(
        white_features, budget["white_peace_limits"]
    )
    surrender_breaches = _surrender_budget_breaches(
        surrender_features, budget["pairwise_limits"]
    )
    execution_blockers = _execution_blockers(observation)
    white = _evaluate_option(
        "white_peace",
        white_features,
        projection["unobserved_dynamic_effects"],
        white_breaches,
        execution_blockers["white_peace"],
        model,
    )
    surrender = _evaluate_option(
        "surrender",
        surrender_features,
        projection["surrender_unobserved_dynamic_effects"],
        surrender_breaches,
        execution_blockers["surrender"],
        model,
    )
    minimum_margin = budget["pairwise_limits"]["minimum_switch_margin_raw"]
    comparison = _compare(white, surrender, minimum_margin=minimum_margin)
    input_hashes = {
        "white_peace_projection_sha256": canonical_policy_input_sha256(
            projection
        ),
        "surrender_session_sha256": canonical_policy_input_sha256(session),
        "budget_profile_sha256": canonical_policy_input_sha256(budget),
        "utility_model_sha256": canonical_policy_input_sha256(model),
    }
    certificate = {
        "schema_version": 4,
        "contract": CONTRACT,
        "status": comparison["status"],
        "frame": dict(frame),
        "utility_unit": UTILITY_UNIT,
        "input_sha256": input_hashes,
        "strategy_identity": {
            "profile_id": budget["profile_id"],
            "profile_version": budget_version,
            "model_id": model["model_id"],
            "model_version": model["model_version"],
        },
        "options": {
            "white_peace": white,
            "surrender": surrender,
        },
        "comparison": comparison,
        "production_live_inputs": (
            projection["production_live"] is True
            and observation["producer"]["production_live"] is True
            and budget["profile_production_eligible"] is True
            and model["model_production_eligible"] is True
        ),
        "boundaries": {
            "immediate_exit_utility_ready": True,
            "execution_availability_gated_separately": True,
            "continue_utility_ready": False,
            "full_three_way_recommendation_ready": False,
            "action_ready": False,
            "action_literal": None,
        },
    }
    certificate["certificate_sha256"] = canonical_policy_input_sha256(
        certificate
    )
    return _result(blockers=[], certificate=certificate)


def _normalize_projection(
    value: object,
) -> tuple[dict[str, object], dict[str, object]]:
    projection = _object(value, "white-peace projection")
    if (
        projection.get("schema") != PROJECTION_PROVIDER_SCHEMA
        or projection.get("provider") != PROJECTION_PROVIDER_ID
        or projection.get("status") != "available"
        or projection.get("observation_ready") is not True
        or projection.get("blockers") != []
    ):
        raise ExitUtilityEvaluationError(
            "white-peace narrow projection is unavailable"
        )
    try:
        observation = normalize_white_peace_terms_observation(
            projection.get("white_peace_observation")
        )
    except ValueError as error:
        raise ExitUtilityEvaluationError(str(error)) from error
    if observation["status"] != "complete" or observation[
        "same_frame_stable"
    ] is not True:
        raise ExitUtilityEvaluationError(
            "white-peace observation is incomplete"
        )
    for key in (
        "unobserved_dynamic_effects",
        "surrender_unobserved_dynamic_effects",
    ):
        _string_list(projection.get(key), f"projection.{key}")
    if not isinstance(projection.get("production_live"), bool):
        raise ExitUtilityEvaluationError(
            "white-peace production_live flag is malformed"
        )
    return projection, observation


def _normalize_session(
    value: object, *, frame: dict[str, object]
) -> dict[str, object]:
    connection = frame.get("connection_id")
    prefix = "connection-generation:"
    if not isinstance(connection, str) or not connection.startswith(prefix):
        raise ExitUtilityEvaluationError(
            "white-peace frame lacks connection generation"
        )
    try:
        generation = int(connection[len(prefix) :])
    except ValueError as error:
        raise ExitUtilityEvaluationError(
            "white-peace connection generation is malformed"
        ) from error
    try:
        return normalize_raiktor_surrender_aggregate_session_binding(
            value,
            expected_snapshot_id=frame["snapshot_id"],
            expected_snapshot_revision=frame["snapshot_revision"],
            expected_native_revision=frame["native_revision"],
            expected_date_raw=frame["date_raw"],
            expected_connection_generation=generation,
            expected_episode_run_id=frame["episode_id"],
            expected_episode_character_id=frame[
                "primary_attacker_character_id"
            ],
            expected_process_id=frame["ck3_pid"],
            expected_war_id=frame["war_id"],
        )
    except (KeyError, ValueError) as error:
        raise ExitUtilityEvaluationError(str(error)) from error


def _normalize_budget_provider(
    value: object,
) -> tuple[dict[str, object], str]:
    provider = _object(value, "budget provider")
    if (
        provider.get("schema") != BUDGET_PROVIDER_SCHEMA
        or provider.get("provider") != OWNER_BUDGET_PROVIDER
        or provider.get("status") != "available"
        or provider.get("profile_available") is not True
        or provider.get("profile_production_eligible") is not True
        or provider.get("blockers") != []
    ):
        raise ExitUtilityEvaluationError("strategy budget is unavailable")
    try:
        budget = normalize_raiktor_owner_budget_profile(
            provider.get("owner_budget_profile")
        )
    except ValueError as error:
        raise ExitUtilityEvaluationError(str(error)) from error
    version = _nonempty_string(
        provider.get("source_profile_version"), "source_profile_version"
    )
    return budget, version


def _normalize_model_provider(value: object) -> dict[str, object]:
    provider = _object(value, "model provider")
    if (
        provider.get("schema") != MODEL_PROVIDER_SCHEMA
        or provider.get("provider") != MODEL_PROVIDER_ID
        or provider.get("status") != "available"
        or provider.get("model_available") is not True
        or provider.get("model_production_eligible") is not True
        or provider.get("provider_blockers") != []
    ):
        raise ExitUtilityEvaluationError("strategy utility model is unavailable")
    model = _object(provider.get("exit_utility_model"), "utility model")
    if (
        model.get("schema_version") != 2
        or model.get("contract") != MODEL_CONTRACT
        or model.get("status") != "complete"
        or model.get("utility_unit") != UTILITY_UNIT
        or model.get("model_production_eligible") is not True
    ):
        raise ExitUtilityEvaluationError("strategy utility model drifted")
    coefficients = _object(
        model.get("domain_coefficients_q100000"), "model coefficients"
    )
    if set(coefficients) != _FEATURE_KEYS:
        raise ExitUtilityEvaluationError("strategy coefficient set drifted")
    for key, item in coefficients.items():
        _int64(item, f"coefficient.{key}")
    uncertainty = _object(
        model.get("uncertainty_policy"), "uncertainty policy"
    )
    if uncertainty.get("rule_id") != "bounded-unobserved-effect-penalty-v1":
        raise ExitUtilityEvaluationError("uncertainty policy is unsupported")
    parameters = _object(
        uncertainty.get("parameters_raw"), "uncertainty parameters"
    )
    if set(parameters) != {
        "per_unobserved_effect_penalty_raw",
        "maximum_total_penalty_raw",
    }:
        raise ExitUtilityEvaluationError("uncertainty parameters drifted")
    for key, item in parameters.items():
        if _int64(item, key) < 0:
            raise ExitUtilityEvaluationError(
                "uncertainty penalties must be nonnegative"
            )
    nonlinear = _object(model.get("nonlinear_policy"), "nonlinear policy")
    if (
        nonlinear.get("rule_id") != "hard-budget-reject-v1"
        or nonlinear.get("parameters_raw") != {}
    ):
        raise ExitUtilityEvaluationError("nonlinear policy is unsupported")
    return model


def _require_model_budget_binding(
    model: dict[str, object],
    *,
    budget: dict[str, object],
    budget_version: str,
) -> None:
    binding = _object(model.get("budget_profile_binding"), "budget binding")
    expected = {
        "profile_id": budget["profile_id"],
        "profile_version": budget_version,
        "profile_source_sha256": budget["profile_source_sha256"],
    }
    if binding != expected:
        raise ExitUtilityEvaluationError(
            "strategy model and budget profile bindings differ"
        )


def _white_features(observation: dict[str, object]) -> dict[str, int]:
    terms = _object(observation["terms"], "white-peace terms")
    pairs = terms.get("prisoner_release_pairs")
    if not isinstance(pairs, list):
        raise ExitUtilityEvaluationError("white-peace release pairs malformed")
    return {
        "primary_gold_transfer_raw": _nonnegative_int(
            terms.get("primary_gold_transfer_raw"), "white gold transfer"
        ),
        "attacker_prestige_delta_raw": _int64(
            terms.get("attacker_prestige_delta_raw"), "white prestige delta"
        ),
        "declared_claim_removed_count": 0,
        "favor_hook_applied": int(
            _boolean(
                terms.get("favor_hook_will_apply"), "white favor hook"
            )
        ),
        "truce_day_count": _nonnegative_int(
            terms.get("truce_evaluated_days"), "white truce days"
        ),
        "pow_release_count": len(pairs),
        "title_holder_change_count": _nonnegative_int(
            terms.get("title_holder_change_count"),
            "white title-holder changes",
        ),
        "hostage_transfer_count": 0,
        "war_bound_soldier_loss_count": 0,
    }


def _surrender_features(projection: dict[str, object]) -> dict[str, int]:
    features = _object(
        projection.get("surrender_feature_observation"),
        "projection.surrender_feature_observation",
    )
    if set(features) != _FEATURE_KEYS:
        raise ExitUtilityEvaluationError(
            "surrender feature observation drifted"
        )
    return {
        key: _int64(features[key], f"surrender.{key}")
        for key in sorted(_FEATURE_KEYS)
    }


def _evaluate_option(
    name: str,
    features: dict[str, int],
    unobserved_effects_value: object,
    budget_breaches: list[str],
    execution_blockers: list[str],
    model: dict[str, object],
) -> dict[str, object]:
    if set(features) != _FEATURE_KEYS:
        raise ExitUtilityEvaluationError(f"{name} feature set drifted")
    effects = _string_list(unobserved_effects_value, f"{name}.unobserved")
    coefficients = model["domain_coefficients_q100000"]
    contributions: dict[str, int] = {}
    for key in sorted(_FEATURE_KEYS):
        feature = _int64(features[key], f"{name}.{key}")
        coefficient = _int64(coefficients[key], f"coefficient.{key}")
        contribution = (
            _truncating_fixed_product(feature, coefficient)
            if key in _FIXED_POINT_FEATURES
            else _checked_multiply(feature, coefficient, f"{name}.{key}")
        )
        contributions[key] = contribution
    base = 0
    for key in sorted(contributions):
        base = _checked_add(base, contributions[key], f"{name}.base")
    parameters = model["uncertainty_policy"]["parameters_raw"]
    penalty = min(
        _checked_multiply(
            len(effects),
            parameters["per_unobserved_effect_penalty_raw"],
            f"{name}.uncertainty_penalty",
        ),
        parameters["maximum_total_penalty_raw"],
    )
    utility = _checked_add(base, -penalty, f"{name}.utility")
    return {
        "features": dict(features),
        "contributions_raw": contributions,
        "base_utility_raw": base,
        "unobserved_dynamic_effects": effects,
        "uncertainty_penalty_raw": penalty,
        "utility_raw": utility,
        "hard_budget_breaches": budget_breaches,
        "execution_blockers": execution_blockers,
        "eligible": not budget_breaches and not execution_blockers,
    }


def _execution_blockers(
    observation: dict[str, object],
) -> dict[str, list[str]]:
    white = _object(observation.get("option"), "observation.option")
    surrender = _object(
        white.get("same_frame_surrender"),
        "observation.option.same_frame_surrender",
    )
    return {
        "white_peace": (
            []
            if _boolean(white.get("available"), "white_peace.available")
            else ["white_peace_native_execution_unavailable"]
        ),
        "surrender": (
            []
            if _boolean(surrender.get("available"), "surrender.available")
            else ["surrender_native_execution_unavailable"]
        ),
    }


def _compare(
    white: dict[str, object],
    surrender: dict[str, object],
    *,
    minimum_margin: int,
) -> dict[str, object]:
    eligible = [
        name
        for name, value in (
            ("white_peace", white),
            ("surrender", surrender),
        )
        if value["eligible"] is True
    ]
    preferred: str | None = None
    margin: int | None = None
    if len(eligible) == 1:
        preferred = eligible[0]
    elif len(eligible) == 2:
        difference = white["utility_raw"] - surrender["utility_raw"]
        if abs(difference) >= minimum_margin:
            preferred = "white_peace" if difference > 0 else "surrender"
            margin = abs(difference)
    return {
        "status": (
            "pairwise_preference_available"
            if preferred is not None
            else "pairwise_underdetermined"
        ),
        "eligible_options": eligible,
        "preferred_immediate_exit": preferred,
        "preference_margin_raw": margin,
        "minimum_switch_margin_raw": minimum_margin,
    }


def _white_budget_breaches(
    features: dict[str, int], limits: dict[str, object]
) -> list[str]:
    breaches: list[str] = []
    if features["primary_gold_transfer_raw"] > limits[
        "maximum_gold_transfer_raw"
    ]:
        breaches.append("white_peace_gold_budget_breached")
    if max(0, -features["attacker_prestige_delta_raw"]) > limits[
        "maximum_prestige_loss_raw"
    ]:
        breaches.append("white_peace_prestige_budget_breached")
    if features["declared_claim_removed_count"] > limits[
        "maximum_claims_removed"
    ]:
        breaches.append("white_peace_claim_budget_breached")
    if features["favor_hook_applied"] and limits["allow_favor_hook"] is not True:
        breaches.append("white_peace_favor_hook_budget_breached")
    if features["truce_day_count"] > limits["maximum_truce_days"]:
        breaches.append("white_peace_truce_budget_breached")
    return breaches


def _surrender_budget_breaches(
    features: dict[str, int], limits: dict[str, object]
) -> list[str]:
    breaches: list[str] = []
    if features["primary_gold_transfer_raw"] > limits[
        "maximum_surrender_gold_transfer_raw"
    ]:
        breaches.append("surrender_gold_budget_breached")
    if max(0, -features["attacker_prestige_delta_raw"]) > limits[
        "maximum_surrender_prestige_loss_raw"
    ]:
        breaches.append("surrender_prestige_budget_breached")
    if features["declared_claim_removed_count"] > limits[
        "maximum_surrender_claims_removed"
    ]:
        breaches.append("surrender_claim_budget_breached")
    if features["favor_hook_applied"] and limits[
        "allow_surrender_favor_hook"
    ] is not True:
        breaches.append("surrender_favor_hook_budget_breached")
    if features["truce_day_count"] > limits[
        "maximum_surrender_truce_days"
    ]:
        breaches.append("surrender_truce_budget_breached")
    return breaches


def _result(
    *,
    blockers: list[str],
    certificate: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": (
            certificate["status"] if certificate is not None else "evidence_required"
        ),
        "utility_evaluation_ready": certificate is not None,
        "immediate_exit_comparison_ready": certificate is not None,
        "production_live_inputs": bool(
            certificate is not None
            and certificate["production_live_inputs"] is True
        ),
        "evaluation_certificate": certificate,
        "blockers": blockers,
        "full_three_way_recommendation_ready": False,
        "action_ready": False,
        "action_literal": None,
        "automatic_surrender_ready": False,
        "boundaries": [
            "white_peace_vs_surrender_only",
            "measured_power_is_not_relabelled_as_campaign_forecast",
            "unobserved_effects_receive_the_versioned_penalty",
            "generic_current_war_bound_soldiers_are_not_proven_loss",
            "hard_budget_rejects_ineligible_options",
            "native_execution_unavailability_rejects_only_that_option",
            "no_recommendation_or_action_submission",
        ],
    }


def _truncating_fixed_product(value: int, coefficient: int) -> int:
    product = _checked_multiply(value, coefficient, "fixed-point product")
    return product // 100_000 if product >= 0 else -((-product) // 100_000)


def _checked_multiply(left: int, right: int, name: str) -> int:
    result = left * right
    if not -(2**63) <= result <= 2**63 - 1:
        raise ExitUtilityEvaluationError(f"{name} overflowed int64")
    return result


def _checked_add(left: int, right: int, name: str) -> int:
    result = left + right
    if not -(2**63) <= result <= 2**63 - 1:
        raise ExitUtilityEvaluationError(f"{name} overflowed int64")
    return result


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ExitUtilityEvaluationError(f"{name} must be an object")
    return value


def _boolean(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ExitUtilityEvaluationError(f"{name} must be a boolean")
    return value


def _int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**63) <= value <= 2**63 - 1
    ):
        raise ExitUtilityEvaluationError(f"{name} must be a signed int64")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    result = _int64(value, name)
    if result < 0:
        raise ExitUtilityEvaluationError(f"{name} must be nonnegative")
    return result


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExitUtilityEvaluationError(f"{name} must be a nonempty string")
    return value


def _string_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ExitUtilityEvaluationError(f"{name} must be a list")
    result = [_nonempty_string(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise ExitUtilityEvaluationError(f"{name} contains duplicates")
    return result


__all__ = [
    "CONTRACT",
    "ExitUtilityEvaluationError",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "evaluate_raiktor_immediate_exit_utilities",
]
