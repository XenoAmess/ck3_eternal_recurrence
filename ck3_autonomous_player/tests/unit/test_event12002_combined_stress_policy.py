"""Use the migrated native primary stress direction in narrow event consumers."""

from copy import deepcopy
import importlib.util
from pathlib import Path

from xar_autoplayer.vanilla_events.outcome import (
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


def _fixture_module(filename):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


JAPAN = _fixture_module("test_tgp_japan_yearly_1190_policy.py")
EPIDEMIC = _fixture_module("test_vanilla_event_registry_policy.py")
PLAYER = 36403


def _current(context):
    context = deepcopy(context)
    context["provenance"] = {
        "backend_id": "ck3-1.20.0.2-native-event-window-v1",
    }
    for option in context["options"]:
        if "effect_indicators" in option:
            option["effect_indicators"]["coverage"] = (
                "played-character-event-icon-indicators-1.20.0.2-v1"
            )
    return context


def _combined(row):
    row["kind"] = "stress_and_fulfillment"
    # The secondary direction is independent of the primary stress direction.
    row["secondary_direction"] = "increase"


def _recommend(context):
    return recommend_registered_vanilla_event_option_v1(
        context, played_character_id=PLAYER, snapshot_option_count=3,
    )


def test_current_1190_combined_primary_loss_keeps_native_one_and_prestige_receipt():
    context = _current(JAPAN._context())
    _combined(context["options"][1]["effect_indicators"]["rows"][0])
    decision = _recommend(context)
    assert decision["status"] == "recommended"
    assert decision["selected_native_option_index"] == 1
    assert decision["failed_checks"] == []
    expectation = plan_registered_event_material_postcondition_v1(
        decision, {"character_id": PLAYER, "stress_points": 0},
        played_character_prestige={"raw": 10_000_000, "scale": 100_000},
        snapshot_id="native:22", revision=23,
    )
    assert expectation["status"] == "ready"
    assert expectation["metric"] == "played_character_prestige.raw"
    assert expectation["expected_relation"] == "strictly_decreasing"


def test_current_1190_combined_primary_gain_does_not_use_secondary_direction():
    context = _current(JAPAN._context())
    row = context["options"][1]["effect_indicators"]["rows"][0]
    _combined(row)
    row["direction"] = "increase"
    row["secondary_direction"] = "decrease"
    decision = _recommend(context)
    assert decision["status"] == "blocked"
    assert "r0100_selected_stress_decrease_indicator" in decision["failed_checks"]


def test_legacy_1190_combined_shape_is_not_accepted_as_legacy_stress():
    context = JAPAN._context()
    _combined(context["options"][1]["effect_indicators"]["rows"][0])
    decision = _recommend(context)
    assert decision["status"] == "blocked"
    assert "r0100_selected_stress_decrease_indicator" in decision["failed_checks"]


def _5007_with_indicator(kind):
    context = _current(EPIDEMIC._epidemic_5007_context((1, 2)))
    context["options"][1]["effect_indicators"] = {
        "status": "available",
        "coverage": "played-character-event-icon-indicators-1.20.0.2-v1",
        "complete_effect_set": False,
        "rows": [{
            "kind": kind, "direction": "increase",
            "secondary_direction": "decrease",
            "magnitude": {"status": "unavailable"},
            "affected_by_trait": True, "critical": False,
        }],
    }
    return context


def test_current_5007_combined_keeps_only_stress_material_profile():
    decision = _recommend(_5007_with_indicator("stress_and_fulfillment"))
    assert decision["status"] == "recommended"
    assert decision["selected_native_option_index"] == 2
    profile = decision["choice_effect_profile"]
    assert profile["completeness"] == "selected-option-stress-facet-only"
    assert profile["complete_effect_set"] is False
    assert profile["selected_option_effects"] == [{
        "domain": "player_stress", "source": "stress_and_fulfillment_impact",
        "direction": "increase", "binding": "selected_option_same_frame_native_indicator",
    }]
    assert profile["unobserved_effect_domains"] == [
        "spiritual_fulfillment", "opinion", "relationship",
    ]


def test_current_fulfillment_only_row_does_not_supply_stress_direction():
    context = _current(JAPAN._context())
    context["options"][1]["effect_indicators"]["rows"][0]["kind"] = "fulfillment"
    assert _recommend(context)["status"] == "blocked"
    assert _recommend(_5007_with_indicator("fulfillment"))["choice_effect_profile"] is None
