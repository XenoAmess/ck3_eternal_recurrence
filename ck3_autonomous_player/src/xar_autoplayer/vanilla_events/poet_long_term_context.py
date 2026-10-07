"""Source-reviewed .9001 comparison using the current player's existing stress."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


EVENT_KEY = "trait_specific.9001"
_SOURCE = "events/trait_specific_events/trait_specific_events.txt"
_SOURCE_SHA = "A4882239AB219EFB2BB082C983403E6E24B8C9DD481E5643ADFE3321ACAC43F7"


def _stress_decrease(option: Mapping[str, object]) -> bool:
    indicators = option.get("effect_indicators")
    if not isinstance(indicators, Mapping) or not (
        indicators.get("status") == "available"
        and indicators.get("coverage")
            == "played-character-event-icon-indicators-1.20.0.4-v1"
        and indicators.get("complete_effect_set") is False
    ):
        return False
    rows = indicators.get("rows")
    facets = [row for row in rows if isinstance(row, Mapping)
        and row.get("kind") in {"stress", "stress_and_fulfillment"}] \
        if isinstance(rows, list) else []
    return bool(len(facets) == 1 and facets[0].get("direction") == "decrease"
        and facets[0].get("critical") is False)


def _journaller_gain(option: Mapping[str, object]) -> bool:
    indicators = option.get("effect_indicators")
    rows = indicators.get("rows") if isinstance(indicators, Mapping) else None
    return bool(isinstance(rows, list) and any(
        isinstance(row, Mapping) and row.get("kind") == "trait"
        and row.get("operation") == "add"
        and isinstance(row.get("trait"), Mapping)
        and row["trait"].get("status") == "available"
        and row["trait"].get("key") == "journaller"
        for row in rows))


def compare_poet_long_term_choices_v1(
    event_context: Mapping[str, object], knowledge: Mapping[str, object], *,
    played_character: object,
) -> dict[str, object] | None:
    """Called only after the existing registry projection checks pass."""
    analysis = knowledge.get("analysis")
    sources = analysis.get("source_sha256") if isinstance(analysis, Mapping) else None
    if not (
        event_context.get("event_definition_key") == EVENT_KEY
        and knowledge.get("ck3_build") == "1.20.0.4"
        and isinstance(sources, Mapping) and sources.get(_SOURCE) == _SOURCE_SHA
    ):
        return None
    options = event_context.get("options")
    by_index = {row.get("native_option_index"): row for row in options
        if isinstance(row, Mapping) and row.get("shown") is True
        and row.get("enabled") is True} if isinstance(options, list) else {}
    if set(by_index) != {0, 1, 2}:
        return None
    character = played_character if isinstance(played_character, Mapping) else {}
    stress = character.get("stress_points")
    root = event_context.get("root_scope")
    identity = root.get("typed_identity") if isinstance(root, Mapping) else None
    stress_available = bool(
        isinstance(identity, Mapping)
        and character.get("character_id") == identity.get("character_id")
        and isinstance(stress, int) and not isinstance(stress, bool) and stress >= 0
    )
    relief = {index: _stress_decrease(row) for index, row in by_index.items()}
    selected = 0
    reason = "retain_one_time_permanent_poet_benefit"
    if stress_available and stress >= 100 and not relief[0]:
        if relief[1] and _journaller_gain(by_index[1]):
            selected = 1
            reason = "permanent_journaller_and_observed_current_stress_relief"
        elif relief[2]:
            selected = 2
            reason = "observed_relief_at_first_break_threshold"
    objective = (
        "acquire_long_term_poet_trait_from_one_time_event" if selected == 0
        else "acquire_long_term_journaller_while_reducing_current_stress" if selected == 1
        else "reduce_current_break_threshold_stress"
    )
    order = [selected] + [index for index in (0, 1, 2) if index != selected]
    utility = {
        "schema": "xar.ck3.vanilla-event-campaign-utility",
        "schema_version": 1, "selected_native_option_index": selected,
        "objective_id": objective, "comparison_kind": "source_reviewed_ordinal",
        "selected_rank": 1, "rank_count": 3,
        "selected_utility": {
            "material_direction": "benefit",
            "outcome_variance": "deterministic_source_effect_with_current_stress_facet",
            "persistent_state_risk": "none_authored", "resource_cost": "none_authored",
            "timeline_value": "permanent_positive_trait" if selected != 2 else "immediate_stress_relief",
        },
        "alternatives": [{"native_option_index": index, "rank": rank,
            "reason": "lower_priority_under_current_source_and_stress_objective"}
            for rank, index in enumerate(order[1:], start=2)],
        "cross_event_numeric_score": None, "calibration_status": "not_calibrated",
        "decision_scope": "bounded_timeline_continuation",
    }
    return {
        "selected_native_option_index": selected,
        "selected_option_number": selected + 1,
        "selected_rendered_index": by_index[selected]["rendered_index"],
        "selected_option": dict(by_index[selected]),
        "campaign_utility_profile": utility,
        "decision_context": {
            "schema": "xar.ck3.poet-long-term-decision-context/v1",
            "policy": "permanent_trait_or_observed_break_threshold_relief_v1",
            "stress_input_available": stress_available,
            "stress_points": stress if stress_available else None,
            "at_or_above_first_break_threshold": stress >= 100 if stress_available else None,
            "stress_decrease_by_native_index": {str(key): value for key, value in relief.items()},
            "selected_reason": reason, "stress_magnitude_used": False,
            "secondary_fulfillment_direction_used": False,
            "generic_semantic_decision_ready": False,
        },
    }


def poet_selected_effect_profile_v1(
    knowledge: Mapping[str, object], comparison: Mapping[str, object],
) -> dict[str, object]:
    index = comparison["selected_native_option_index"]
    analysis = knowledge["analysis"]
    profile = deepcopy(analysis["selected_choice_effect_profile"])
    profile["selected_native_option_index"] = index
    if index == 1:
        profile["selected_option_effects"] = [
            {"domain": "trait", "subject": "root", "operation": "add_trait",
             "trait": "journaller", "permanent": True, "authored_resource_cost": "none"},
            {"domain": "stress", "subject": "root", "operation": "conditional_stress_impact",
             "loss_condition_trait": "content", "gain_condition_trait": "ambitious",
             "runtime_delta_exact": False},
        ]
        profile["source_anchors"][0] = f"{_SOURCE}:1336-1364"
    elif index == 2:
        profile["selected_option_effects"] = [{
            "domain": "stress", "subject": "root", "operation": "authored_stress_and_trait_impact",
            "base_value_key": "minor_stress_loss", "loss_condition_traits": ["lazy", "fickle"],
            "gain_condition_trait": "diligent", "runtime_delta_exact": False,
        }]
        profile["source_anchors"][0] = f"{_SOURCE}:1367-1397"
    trait_key = "lifestyle_poet" if index == 0 else "journaller"
    profile["observable_postcondition"] = {
        "metric": "played_character.stress_points" if index == 2
            else f"played_character.event_traits.{trait_key}",
        "expected_relation": "strictly_decreasing" if index == 2 else "false_to_true",
        "material_change_required_for_evidence": True,
    }
    return profile
