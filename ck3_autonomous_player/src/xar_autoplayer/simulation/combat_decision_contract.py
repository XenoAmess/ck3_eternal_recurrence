"""Version-bound combat-entry expected utility, with production activation off.

The base v1 contract retains its frozen inventory.  A separate, explicitly
bound action-component record supplies attack, avoid, and wait trial tapes.
Without that record, the evaluator never invents costs.
Even a favorable calculated candidate cannot select a production action while
the explicit activation constant is false.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from .combat_core import wilson_interval_95


COMBAT_ENTRY_EU_SCHEMA_VERSION = 1
COMBAT_ENTRY_EU_CONTRACT_VERSION = "combat-entry-eu-v1"
COMBAT_ENTRY_EU_ACTIVATION_ENABLED = False
COMBAT_ENTRY_ACTION_COMPONENTS_VERSION = "combat-entry-action-components-v1"
_SCALE = 100_000
_SHA256 = re.compile(r"[0-9A-F]{64}")

_IDENTITY_KEYS = (
    "episode_run_id",
    "snapshot_id",
    "revision",
    "native_revision",
)
_FIDELITY_KEYS = (
    "loaded_playset_verified",
    "ast_evaluator_ready",
    "original_trace_ready",
    "transition_fidelity_gate",
    "monte_carlo_ready",
    "planner_usable",
    "active_attack_allowed",
)
_DISTRIBUTION_KEYS = (
    "player_win_probability_raw",
    "player_loss_probability_raw",
    "no_resolution_probability_raw",
)
_CHARACTER_TAIL_KEYS = (
    "commander_wound_probability_raw",
    "commander_maim_probability_raw",
    "commander_death_probability_raw",
    "knight_wound_probability_raw",
    "knight_maim_probability_raw",
    "knight_death_probability_raw",
    "detach_or_capture_probability_raw",
)
_CAMPAIGN_FEEDBACK_KEYS = (
    "battle_warscore_raw",
    "objective_siege_tempo_raw",
    "reinforcement_route_raw",
    "supply_attrition_raw",
    "replacement_gold_time_raw",
    "exit_option_value_raw",
)
_UTILITY_COEFFICIENT_KEYS = (
    "player_win",
    "player_loss",
    "no_resolution",
    "battle_day",
    "player_hard_loss",
    "enemy_hard_loss",
    "player_commander_wound",
    "player_commander_maim",
    "player_commander_death",
    "player_knight_death",
    "player_detach_capture",
    "player_one_life_catastrophic",
    "battle_warscore",
    "objective_siege_tempo",
    "reinforcement_route",
    "supply_attrition",
    "replacement_gold_time",
    "exit_option_value",
)

_REQUIRED_PATHS = (
    *(f"identity.observation.{key}" for key in _IDENTITY_KEYS),
    *(f"identity.forecast.{key}" for key in _IDENTITY_KEYS),
    "identity.target_province_id",
    "identity.entry_province_id",
    "identity.war_id",
    "identity.player_war_side",
    "identity.player_ordered_army_ids",
    "identity.opponent_ordered_army_ids",
    *(f"fidelity.{key}" for key in _FIDELITY_KEYS),
    "experiment.simulator_version",
    "experiment.simulator_sha256",
    "experiment.input_sha256",
    "experiment.per_trial_component_vector_sha256",
    "experiment.seed_u64",
    "experiment.trial_count",
    "experiment.horizon_days",
    "experiment.wins",
    "experiment.losses",
    "experiment.no_resolution",
    *(f"distribution.{key}" for key in _DISTRIBUTION_KEYS),
    "distribution.resolved_win_wilson95.low_raw",
    "distribution.resolved_win_wilson95.high_raw",
    *(f"distribution.battle_days.{key}" for key in ("p10", "p50", "p90")),
    *(
        f"distribution.player_hard_losses_raw.{key}"
        for key in ("p10", "p50", "p90")
    ),
    *(
        f"distribution.enemy_hard_losses_raw.{key}"
        for key in ("p10", "p50", "p90")
    ),
    "distribution.player_stack_wipe_probability_raw",
    *(
        f"character_tails.{side}.{key}"
        for side in ("player", "opponent")
        for key in _CHARACTER_TAIL_KEYS
    ),
    "character_tails.player_one_life_catastrophic_probability_raw",
    *(f"campaign_feedback.{key}" for key in _CAMPAIGN_FEEDBACK_KEYS),
    "utility_policy.policy_version",
    "utility_policy.policy_sha256",
    "utility_policy.action_alternatives",
    *(
        f"utility_policy.coefficients_raw.{key}"
        for key in _UTILITY_COEFFICIENT_KEYS
    ),
    "utility_policy.risk_constraints.max_player_stack_wipe_probability_raw",
    "utility_policy.risk_constraints.max_player_one_life_catastrophic_probability_raw",
    "utility_policy.risk_constraints.min_resolved_win_wilson_low_raw",
    "utility_policy.uncertainty_penalty_raw",
    "utility_policy.opportunity_cost_raw",
    "utility_policy.minimum_attack_margin_raw",
)


def _required_path_tree() -> dict[str, object]:
    root: dict[str, object] = {}
    for path in _REQUIRED_PATHS:
        current = root
        parts = path.split(".")
        for part in parts[:-1]:
            child = current.setdefault(part, {})
            if not isinstance(child, dict):
                raise AssertionError("combat-entry EU required path prefix drifted")
            current = child
        current[parts[-1]] = None
    return root


_REQUIRED_PATH_TREE = _required_path_tree()

_CONTRACT = {
    "schema_version": COMBAT_ENTRY_EU_SCHEMA_VERSION,
    "version": COMBAT_ENTRY_EU_CONTRACT_VERSION,
    "scale": _SCALE,
    "required_paths": list(_REQUIRED_PATHS),
    "same_frame_identity_keys": list(_IDENTITY_KEYS),
    "fidelity_gates": list(_FIDELITY_KEYS),
    "probability_partition": list(_DISTRIBUTION_KEYS),
    "resolved_win_probability_is_not_unconditional": True,
    "trial_accounting": "wins_plus_losses_plus_no_resolution_equals_trial_count",
    "character_tail_keys": list(_CHARACTER_TAIL_KEYS),
    "campaign_feedback_keys": list(_CAMPAIGN_FEEDBACK_KEYS),
    "utility_coefficient_keys": list(_UTILITY_COEFFICIENT_KEYS),
    "alternatives_source_order": ["attack", "avoid", "wait_reinforce"],
    "future_equation": (
        "sum_q100000_probability_times_per_trial_utility_minus_"
        "uncertainty_penalty_minus_opportunity_cost"
    ),
    "rounding": "signed_q100000_truncate_toward_zero_per_component",
    "activation": "explicit_separate_production_gate_false",
}


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest().upper()


COMBAT_ENTRY_EU_CONTRACT_SHA256 = _canonical_digest(_CONTRACT)

_ACTION_COMPONENTS_CONTRACT = {
    "version": COMBAT_ENTRY_ACTION_COMPONENTS_VERSION,
    "base_contract_sha256": COMBAT_ENTRY_EU_CONTRACT_SHA256,
    "actions": ["attack", "avoid", "wait_reinforce"],
    "required_trial_count": "experiment.trial_count_for_each_action",
    "trial_component_keys": list(_UTILITY_COEFFICIENT_KEYS),
    "attack_trial_sha256": "experiment.per_trial_component_vector_sha256",
    "rounding": "signed_q100000_truncate_toward_zero_per_trial_component_then_mean",
    "alternative_costs": "explicit_uncertainty_and_opportunity_per_action",
    "activation": "explicit_separate_production_gate_false",
}
COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256 = _canonical_digest(
    _ACTION_COMPONENTS_CONTRACT
)


class CombatEntryEuContractError(ValueError):
    """The supplied future-policy record violates a typed field contract."""


def combat_entry_eu_contract() -> dict[str, object]:
    """Return the canonical, immutable-by-copy field inventory."""

    return json.loads(json.dumps(_CONTRACT, ensure_ascii=False))


def combat_entry_action_components_contract() -> dict[str, object]:
    """Return the separate trial-tape calculator interface by value."""

    return json.loads(json.dumps(_ACTION_COMPONENTS_CONTRACT, ensure_ascii=False))


def assess_combat_entry_eu_contract(
    value: object, *, action_components: object | None = None
) -> dict[str, object]:
    """Validate the base record, then calculate only from explicit action data."""

    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise CombatEntryEuContractError("combat-entry EU input must be an object")
    missing = [path for path in _REQUIRED_PATHS if not _has_path(value, path)]
    errors = _unexpected_field_errors(value, _REQUIRED_PATH_TREE)
    identity_ready = False
    fidelity_ready = False
    probability_partition_ready = False
    trial_accounting_ready = False
    utility_policy_ready = False

    if not missing:
        observation = _object_path(value, "identity.observation", errors)
        forecast = _object_path(value, "identity.forecast", errors)
        if observation is not None and forecast is not None:
            _validate_identity(observation, "identity.observation", errors)
            _validate_identity(forecast, "identity.forecast", errors)
            identity_ready = not errors and all(
                observation[key] == forecast[key] for key in _IDENTITY_KEYS
            )
            if not identity_ready and not errors:
                errors.append("identity.observation_and_forecast_mismatch")
        _validate_positive_id(value, "identity.target_province_id", errors)
        _validate_positive_id(value, "identity.entry_province_id", errors)
        _validate_positive_id(value, "identity.war_id", errors)
        _validate_side(value, "identity.player_war_side", errors)
        _validate_id_vector(value, "identity.player_ordered_army_ids", errors)
        _validate_id_vector(value, "identity.opponent_ordered_army_ids", errors)

        fidelity = _object_path(value, "fidelity", errors)
        if fidelity is not None:
            for key in _FIDELITY_KEYS:
                if not isinstance(fidelity[key], bool):
                    errors.append(f"fidelity.{key}_not_boolean")
            fidelity_ready = not any(
                error.startswith("fidelity.") for error in errors
            ) and all(fidelity[key] is True for key in _FIDELITY_KEYS)

        experiment = _object_path(value, "experiment", errors)
        if experiment is not None:
            for key in (
                "simulator_sha256",
                "input_sha256",
                "per_trial_component_vector_sha256",
            ):
                _validate_sha(experiment[key], f"experiment.{key}", errors)
            if not isinstance(experiment["simulator_version"], str) or not experiment[
                "simulator_version"
            ]:
                errors.append("experiment.simulator_version_invalid")
            for key in ("seed_u64", "trial_count", "horizon_days", "wins", "losses", "no_resolution"):
                item = experiment[key]
                if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                    errors.append(f"experiment.{key}_invalid")
            if isinstance(experiment["trial_count"], int) and experiment["trial_count"] <= 0:
                errors.append("experiment.trial_count_invalid")
            if isinstance(experiment["horizon_days"], int) and experiment["horizon_days"] <= 0:
                errors.append("experiment.horizon_days_invalid")
            trial_accounting_ready = (
                not any(error.startswith("experiment.") for error in errors)
                and experiment["wins"]
                + experiment["losses"]
                + experiment["no_resolution"]
                == experiment["trial_count"]
            )
            if not trial_accounting_ready and not any(
                error.startswith("experiment.") for error in errors
            ):
                errors.append("experiment.trial_accounting_mismatch")

        distribution = _object_path(value, "distribution", errors)
        if distribution is not None:
            for key in _DISTRIBUTION_KEYS:
                _validate_probability(distribution[key], f"distribution.{key}", errors)
            probability_partition_ready = (
                not any(error.startswith("distribution.") for error in errors)
                and sum(distribution[key] for key in _DISTRIBUTION_KEYS) == _SCALE
            )
            if not probability_partition_ready and not any(
                error.startswith("distribution.") for error in errors
            ):
                errors.append("distribution.probability_partition_not_q100000")
            _validate_distribution_details(distribution, errors)

        _validate_character_tails(value, errors)
        _validate_campaign_feedback(value, errors)
        utility_policy_ready = _validate_utility_policy(value, errors)

    external_inputs_ready = bool(
        not missing
        and not errors
        and identity_ready
        and fidelity_ready
        and probability_partition_ready
        and trial_accounting_ready
        and utility_policy_ready
    )
    blockers: list[str] = []
    if missing:
        blockers.append("required_fields_missing")
    if errors:
        blockers.append("contract_validation_failed")
    if not identity_ready:
        blockers.append("same_frame_identity_not_ready")
    if not fidelity_ready:
        blockers.append("fidelity_gates_not_ready")
    if not probability_partition_ready:
        blockers.append("probability_partition_not_ready")
    if not trial_accounting_ready:
        blockers.append("trial_accounting_not_ready")
    if not utility_policy_ready:
        blockers.append("utility_policy_not_ready")
    blockers.append(
        "combat_entry_eu_activation_not_enabled"
        if not COMBAT_ENTRY_EU_ACTIVATION_ENABLED
        else "action_components_missing"
    )
    result: dict[str, object] = {
        "schema_version": COMBAT_ENTRY_EU_SCHEMA_VERSION,
        "contract_version": COMBAT_ENTRY_EU_CONTRACT_VERSION,
        "contract_sha256": COMBAT_ENTRY_EU_CONTRACT_SHA256,
        "status": (
            (
                "blocked_not_activated"
                if not COMBAT_ENTRY_EU_ACTIVATION_ENABLED
                else "blocked_action_components_missing"
            )
            if external_inputs_ready
            else "blocked_incomplete_or_invalid"
        ),
        "missing_required_paths": missing,
        "validation_errors": errors,
        "same_frame_identity_ready": identity_ready,
        "fidelity_gates_ready": fidelity_ready,
        "probability_partition_ready": probability_partition_ready,
        "trial_accounting_ready": trial_accounting_ready,
        "utility_policy_ready": utility_policy_ready,
        "external_inputs_ready": external_inputs_ready,
        "eu_attack_raw": None,
        "eu_avoid_raw": None,
        "eu_wait_reinforce_raw": None,
        "attack_margin_raw": None,
        "dominant_risk": None,
        "decision_status": "blocked",
        "selected_action": None,
        "automatic_attack_enabled": False,
        "blockers": blockers,
    }
    result["assessment_sha256"] = _canonical_digest(result)
    if action_components is not None:
        return _assess_explicit_action_components(value, action_components, result)
    return result


_ALTERNATIVE_ACTIONS = ("avoid", "wait_reinforce")
_MAX_SIGNED_RAW = (1 << 63) - 1


def _signed_q100000_product(left: int, right: int) -> int:
    product = left * right
    return (1 if product >= 0 else -1) * (abs(product) // _SCALE)


def _is_signed_raw(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and -_MAX_SIGNED_RAW - 1 <= value <= _MAX_SIGNED_RAW
    )


def _component_utility(
    components: Mapping[str, int], coefficients: Mapping[str, int]
) -> int:
    return sum(
        _signed_q100000_product(components[key], coefficients[key])
        for key in _UTILITY_COEFFICIENT_KEYS
    )


def _signed_truncate_divide(value: int, divisor: int) -> int:
    return (1 if value >= 0 else -1) * (abs(value) // divisor)


def _valid_trial_components(rows: object, count: int) -> bool:
    return bool(
        isinstance(rows, list)
        and len(rows) == count
        and all(
            isinstance(row, Mapping)
            and set(row) == set(_UTILITY_COEFFICIENT_KEYS)
            and all(_is_signed_raw(component) for component in row.values())
            for row in rows
        )
    )


def _attack_trial_summary_errors(
    value: Mapping[str, Any], rows: list[Mapping[str, int]]
) -> list[str]:
    """Bind every decision-bearing attack summary to its hashed trial tape."""
    errors: list[str] = []
    count = len(rows)
    distribution = value["distribution"]
    for field, group in (
        ("battle_day", "battle_days"),
        ("player_hard_loss", "player_hard_losses_raw"),
        ("enemy_hard_loss", "enemy_hard_losses_raw"),
    ):
        values = sorted(row[field] for row in rows)
        if any(item < 0 for item in values):
            errors.append(f"attack_trial_{field}_negative")
            continue
        if field == "battle_day":
            if any(
                item % _SCALE != 0
                or item > value["experiment"]["horizon_days"] * _SCALE
                for item in values
            ):
                errors.append("attack_trial_battle_day_invalid")
                continue
            values = [item // _SCALE for item in values]
        for quantile, numerator in (("p10", 1), ("p50", 5), ("p90", 9)):
            rank = max(1, (numerator * count + 9) // 10)
            if distribution[group][quantile] != values[rank - 1]:
                errors.append(f"attack_trial_{group}_{quantile}_mismatch")
    player = value["character_tails"]["player"]
    tail_keys = {
        "player_commander_wound": player["commander_wound_probability_raw"],
        "player_commander_maim": player["commander_maim_probability_raw"],
        "player_commander_death": player["commander_death_probability_raw"],
        "player_knight_death": player["knight_death_probability_raw"],
        "player_detach_capture": player["detach_or_capture_probability_raw"],
        "player_one_life_catastrophic": value["character_tails"][
            "player_one_life_catastrophic_probability_raw"
        ],
    }
    for field, published in tail_keys.items():
        if any(row[field] not in {0, _SCALE} for row in rows):
            errors.append(f"attack_trial_{field}_not_indicator")
        elif abs(sum(row[field] for row in rows) - published * count) > count:
            errors.append(f"attack_trial_{field}_probability_mismatch")
    for key in _CAMPAIGN_FEEDBACK_KEYS:
        field = key.removesuffix("_raw")
        published = value["campaign_feedback"][key]
        if abs(sum(row[field] for row in rows) - published * count) > count:
            errors.append(f"attack_trial_{field}_campaign_mismatch")
    return errors


def _assess_explicit_action_components(
    value: Mapping[str, Any],
    action_components: object,
    base: dict[str, object],
) -> dict[str, object]:
    """Compare three explicit alternatives; retain the production OFF gate."""
    result = dict(base)
    result["action_components_version"] = COMBAT_ENTRY_ACTION_COMPONENTS_VERSION
    result["action_components_contract_sha256"] = (
        COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256
    )
    result["action_components_ready"] = False
    result["candidate_action"] = None
    errors: list[str] = []
    if not base["external_inputs_ready"]:
        errors.append("base_contract_not_ready")
    if not isinstance(action_components, Mapping) or set(action_components) != {
        "version", "identity", "experiment_input_sha256",
        "per_trial_component_vector_sha256", "policy_sha256",
        "attack_trial_components_raw", "alternatives",
    }:
        errors.append("action_components_schema_invalid")
    elif base["external_inputs_ready"]:
        if action_components["version"] != COMBAT_ENTRY_ACTION_COMPONENTS_VERSION:
            errors.append("action_components_version_mismatch")
        if action_components["identity"] != value["identity"]:
            errors.append("action_components_identity_mismatch")
        if (
            action_components["experiment_input_sha256"]
            != value["experiment"]["input_sha256"]
            or action_components["per_trial_component_vector_sha256"]
            != value["experiment"]["per_trial_component_vector_sha256"]
            or action_components["policy_sha256"]
            != value["utility_policy"]["policy_sha256"]
        ):
            errors.append("action_components_versioned_source_mismatch")
        count = value["experiment"]["trial_count"]
        attack_trials = action_components["attack_trial_components_raw"]
        if not _valid_trial_components(attack_trials, count):
            errors.append("attack_trial_components_invalid")
        else:
            if (
                _canonical_digest(attack_trials)
                != value["experiment"]["per_trial_component_vector_sha256"]
            ):
                errors.append("attack_trial_components_sha256_mismatch")
            outcomes = ("player_win", "player_loss", "no_resolution")
            for row in attack_trials:
                if sorted(row[key] for key in outcomes) != [0, 0, _SCALE]:
                    errors.append("attack_trial_outcome_not_one_hot")
                    break
            else:
                observed = (
                    sum(row[key] == _SCALE for row in attack_trials)
                    for key in outcomes
                )
                if tuple(observed) != tuple(
                    value["experiment"][key]
                    for key in ("wins", "losses", "no_resolution")
                ):
                    errors.append("attack_trial_outcome_count_mismatch")
            errors.extend(_attack_trial_summary_errors(value, attack_trials))
        alternatives = action_components["alternatives"]
        if not (
            isinstance(alternatives, Mapping)
            and set(alternatives) == set(_ALTERNATIVE_ACTIONS)
        ):
            errors.append("alternative_actions_invalid")
        else:
            for action in _ALTERNATIVE_ACTIONS:
                row = alternatives[action]
                if not isinstance(row, Mapping) or set(row) != {
                    "trial_components_raw", "uncertainty_penalty_raw",
                    "opportunity_cost_raw",
                }:
                    errors.append(f"{action}_projection_schema_invalid")
                    continue
                if not _valid_trial_components(row["trial_components_raw"], count):
                    errors.append(f"{action}_trial_components_invalid")
                for penalty in ("uncertainty_penalty_raw", "opportunity_cost_raw"):
                    if not _is_signed_raw(row[penalty]) or row[penalty] < 0:
                        errors.append(f"{action}_{penalty}_invalid")
        policy = value["utility_policy"]
        for penalty in (
            "uncertainty_penalty_raw", "opportunity_cost_raw",
            "minimum_attack_margin_raw",
        ):
            if policy[penalty] < 0:
                errors.append(f"attack_{penalty}_negative")
        experiment = value["experiment"]
        distribution = value["distribution"]
        count_keys = ("wins", "losses", "no_resolution")
        for count_key, probability_key in zip(count_keys, _DISTRIBUTION_KEYS):
            if abs(
                distribution[probability_key] * experiment["trial_count"]
                - experiment[count_key] * _SCALE
            ) > experiment["trial_count"]:
                errors.append(f"{probability_key}_trial_count_mismatch")
        resolved = experiment["wins"] + experiment["losses"]
        wilson = wilson_interval_95(experiment["wins"], resolved)
        interval = distribution["resolved_win_wilson95"]
        if wilson is None or any(
            abs(observed - expected * _SCALE) > 1.5
            for observed, expected in (
                (interval["low_raw"], wilson.lower),
                (interval["high_raw"], wilson.upper),
            )
        ):
            errors.append("resolved_win_wilson95_trial_count_mismatch")
    result["action_components_errors"] = errors
    if errors:
        result["status"] = "blocked_incomplete_or_invalid"
        result["blockers"] = [*base["blockers"], "action_components_not_ready"]
        result["assessment_sha256"] = _canonical_digest(
            {key: item for key, item in result.items() if key != "assessment_sha256"}
        )
        return result

    assert isinstance(action_components, Mapping)
    policy = value["utility_policy"]
    distribution = value["distribution"]
    coefficients = policy["coefficients_raw"]
    trial_count = value["experiment"]["trial_count"]
    attack = (
        _signed_truncate_divide(
            sum(
                _component_utility(row, coefficients)
                for row in action_components["attack_trial_components_raw"]
            ),
            trial_count,
        )
        - policy["uncertainty_penalty_raw"]
        - policy["opportunity_cost_raw"]
    )
    alternatives = action_components["alternatives"]
    eu = {"attack": attack}
    for action in _ALTERNATIVE_ACTIONS:
        projection = alternatives[action]
        eu[action] = (
            _signed_truncate_divide(
                sum(
                    _component_utility(row, coefficients)
                    for row in projection["trial_components_raw"]
                ),
                trial_count,
            )
            - projection["uncertainty_penalty_raw"]
            - projection["opportunity_cost_raw"]
        )
    risk = policy["risk_constraints"]
    risk_failures: list[str] = []
    if (
        distribution["resolved_win_wilson95"]["low_raw"]
        < risk["min_resolved_win_wilson_low_raw"]
    ):
        risk_failures.append("resolved_win_wilson_low")
    if (
        distribution["player_stack_wipe_probability_raw"]
        > risk["max_player_stack_wipe_probability_raw"]
    ):
        risk_failures.append("player_stack_wipe")
    if (
        value["character_tails"]["player_one_life_catastrophic_probability_raw"]
        > risk["max_player_one_life_catastrophic_probability_raw"]
    ):
        risk_failures.append("player_one_life_catastrophic")
    nonattack = max(_ALTERNATIVE_ACTIONS, key=lambda action: eu[action])
    margin = attack - eu[nonattack]
    candidate = (
        "attack"
        if not risk_failures and margin > policy["minimum_attack_margin_raw"]
        else nonattack
    )
    activated = COMBAT_ENTRY_EU_ACTIVATION_ENABLED
    result.update(
        status="selected" if activated else "calculated_not_activated",
        action_components_ready=True,
        action_components_sha256=_canonical_digest(action_components),
        eu_attack_raw=attack,
        eu_avoid_raw=eu["avoid"],
        eu_wait_reinforce_raw=eu["wait_reinforce"],
        attack_margin_raw=margin,
        dominant_risk=risk_failures[0] if risk_failures else None,
        candidate_action=candidate,
        decision_status="selected" if activated else "candidate_only",
        selected_action=candidate if activated else None,
        automatic_attack_enabled=activated and candidate == "attack",
        blockers=[] if activated else ["combat_entry_eu_activation_not_enabled"],
    )
    result["assessment_sha256"] = _canonical_digest(
        {key: item for key, item in result.items() if key != "assessment_sha256"}
    )
    return result


def _has_path(value: Mapping[str, Any], path: str) -> bool:
    current: object = value
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False
        current = current[part]
    return True


def _unexpected_field_errors(
    value: Mapping[str, Any],
    allowed: Mapping[str, object],
    *,
    prefix: str = "",
) -> list[str]:
    errors: list[str] = []
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if key not in allowed:
            errors.append(f"{path}_unexpected")
            continue
        nested = allowed[key]
        if isinstance(nested, Mapping) and isinstance(child, Mapping):
            errors.extend(
                _unexpected_field_errors(child, nested, prefix=path)
            )
    return errors


def _lookup(value: Mapping[str, Any], path: str) -> object:
    current: object = value
    for part in path.split("."):
        if not isinstance(current, Mapping):
            raise KeyError(path)
        current = current[part]
    return current


def _object_path(
    value: Mapping[str, Any], path: str, errors: list[str]
) -> Mapping[str, Any] | None:
    item = _lookup(value, path)
    if not isinstance(item, Mapping) or any(not isinstance(key, str) for key in item):
        errors.append(f"{path}_not_object")
        return None
    return item


def _validate_identity(
    value: Mapping[str, Any], path: str, errors: list[str]
) -> None:
    for key in ("episode_run_id", "snapshot_id"):
        if not isinstance(value[key], str) or not value[key]:
            errors.append(f"{path}.{key}_invalid")
    for key in ("revision", "native_revision"):
        item = value[key]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            errors.append(f"{path}.{key}_invalid")


def _validate_positive_id(
    value: Mapping[str, Any], path: str, errors: list[str]
) -> None:
    item = _lookup(value, path)
    if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
        errors.append(f"{path}_invalid")


def _validate_side(value: Mapping[str, Any], path: str, errors: list[str]) -> None:
    item = _lookup(value, path)
    if isinstance(item, bool) or item not in {0, 1}:
        errors.append(f"{path}_invalid")


def _validate_id_vector(
    value: Mapping[str, Any], path: str, errors: list[str]
) -> None:
    rows = _lookup(value, path)
    if (
        not isinstance(rows, list)
        or not rows
        or any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in rows)
        or len(rows) != len(set(rows))
    ):
        errors.append(f"{path}_invalid")


def _validate_sha(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        errors.append(f"{path}_invalid")


def _validate_probability(value: object, path: str, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= _SCALE:
        errors.append(f"{path}_invalid")


def _validate_distribution_details(
    distribution: Mapping[str, Any], errors: list[str]
) -> None:
    wilson = distribution["resolved_win_wilson95"]
    if not isinstance(wilson, Mapping):
        errors.append("distribution.resolved_win_wilson95_not_object")
    else:
        _validate_probability(wilson["low_raw"], "distribution.resolved_win_wilson95.low_raw", errors)
        _validate_probability(wilson["high_raw"], "distribution.resolved_win_wilson95.high_raw", errors)
        if (
            isinstance(wilson["low_raw"], int)
            and isinstance(wilson["high_raw"], int)
            and wilson["low_raw"] > wilson["high_raw"]
        ):
            errors.append("distribution.resolved_win_wilson95_order_invalid")
    for group in ("battle_days", "player_hard_losses_raw", "enemy_hard_losses_raw"):
        row = distribution[group]
        if not isinstance(row, Mapping):
            errors.append(f"distribution.{group}_not_object")
            continue
        values = [row[key] for key in ("p10", "p50", "p90")]
        if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in values):
            errors.append(f"distribution.{group}_invalid")
        elif values != sorted(values):
            errors.append(f"distribution.{group}_quantile_order_invalid")
    _validate_probability(
        distribution["player_stack_wipe_probability_raw"],
        "distribution.player_stack_wipe_probability_raw",
        errors,
    )


def _validate_character_tails(
    value: Mapping[str, Any], errors: list[str]
) -> None:
    tails = _object_path(value, "character_tails", errors)
    if tails is None:
        return
    for side in ("player", "opponent"):
        row = tails[side]
        if not isinstance(row, Mapping):
            errors.append(f"character_tails.{side}_not_object")
            continue
        for key in _CHARACTER_TAIL_KEYS:
            _validate_probability(row[key], f"character_tails.{side}.{key}", errors)
    _validate_probability(
        tails["player_one_life_catastrophic_probability_raw"],
        "character_tails.player_one_life_catastrophic_probability_raw",
        errors,
    )


def _validate_campaign_feedback(
    value: Mapping[str, Any], errors: list[str]
) -> None:
    row = _object_path(value, "campaign_feedback", errors)
    if row is None:
        return
    for key in _CAMPAIGN_FEEDBACK_KEYS:
        item = row[key]
        if isinstance(item, bool) or not isinstance(item, int) or not -(1 << 63) <= item < (1 << 63):
            errors.append(f"campaign_feedback.{key}_invalid")


def _validate_utility_policy(
    value: Mapping[str, Any], errors: list[str]
) -> bool:
    row = _object_path(value, "utility_policy", errors)
    if row is None:
        return False
    if not isinstance(row["policy_version"], str) or not row["policy_version"]:
        errors.append("utility_policy.policy_version_invalid")
    _validate_sha(row["policy_sha256"], "utility_policy.policy_sha256", errors)
    if row["action_alternatives"] != ["attack", "avoid", "wait_reinforce"]:
        errors.append("utility_policy.action_alternatives_invalid")
    coefficients = row["coefficients_raw"]
    if not isinstance(coefficients, Mapping) or set(coefficients) != set(
        _UTILITY_COEFFICIENT_KEYS
    ):
        errors.append("utility_policy.coefficients_raw_schema_invalid")
    else:
        for key in _UTILITY_COEFFICIENT_KEYS:
            item = coefficients[key]
            if isinstance(item, bool) or not isinstance(item, int) or not -(1 << 63) <= item < (1 << 63):
                errors.append(f"utility_policy.coefficients_raw.{key}_invalid")
    risk = row["risk_constraints"]
    if not isinstance(risk, Mapping):
        errors.append("utility_policy.risk_constraints_not_object")
    else:
        for key in (
            "max_player_stack_wipe_probability_raw",
            "max_player_one_life_catastrophic_probability_raw",
            "min_resolved_win_wilson_low_raw",
        ):
            _validate_probability(risk[key], f"utility_policy.risk_constraints.{key}", errors)
    for key in (
        "uncertainty_penalty_raw",
        "opportunity_cost_raw",
        "minimum_attack_margin_raw",
    ):
        item = row[key]
        if isinstance(item, bool) or not isinstance(item, int) or not -(1 << 63) <= item < (1 << 63):
            errors.append(f"utility_policy.{key}_invalid")
    return not any(error.startswith("utility_policy.") for error in errors)


__all__ = [
    "COMBAT_ENTRY_EU_SCHEMA_VERSION",
    "COMBAT_ENTRY_EU_CONTRACT_VERSION",
    "COMBAT_ENTRY_EU_CONTRACT_SHA256",
    "COMBAT_ENTRY_EU_ACTIVATION_ENABLED",
    "COMBAT_ENTRY_ACTION_COMPONENTS_VERSION",
    "COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256",
    "CombatEntryEuContractError",
    "combat_entry_eu_contract",
    "combat_entry_action_components_contract",
    "assess_combat_entry_eu_contract",
]
