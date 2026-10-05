from copy import deepcopy

from xar_autoplayer.bridge.battle_terminal_transition_contract import _normalize_raw_numeric_inputs
from xar_autoplayer.simulation.battle_person_stage_cache_projection_12003 import (
    ExplicitPersonCacheStage12003, project_person_cache_stage_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, WeightedModifierRow12003,
)


def test_normalized_current_operands_to_two_explicit_stage_cache_families():
    raw = {
        "status": "available", "raw_numeric_inputs_ready": True,
        "character_id": 29829, "scratch_present": True,
        "context_source": "fallback_static", "base_points": [1, 2, 3, 4, 5, 6],
        "caps": [100] * 6, "prowess_adjustment": 0, "category_counts": [0] * 4,
        "scratch_factor_numerator": 0, "scratch_factor_denominator": 100,
        "context": {"aggregate_properties": {"count": 0, "keys_u16": [], "values_q64": []},
                    "weighted_count": 0, "weighted_rows": []},
        "auxiliary_scratch_inputs": {
            "status": "available", "ready": True, "base430_q64": 50, "base438_q64": -20,
            "selector_flag_raw": 0, "selector_metric_raw": 9,
            "selected_low_threshold_raw": 10, "selected_high_threshold_raw": None,
            "prepared430_q64": 999, "prepared438_q64": -888,
            "copied430_q64": 777, "copied438_q64": -666, "ready440_raw": 0,
            "unavailable_reason": None,
        },
        "nine_cache_byte_inputs": {
            "status": "available", "ready": True, "model_present": True,
            "aggregate_properties": {"count": 0, "keys_u16": [], "values_q64": []},
            "carrier278_present": True, "carrier278_magic_raw": 0x41495374,
            "linked20_present": True, "used_native_definition_fallback": False,
            "selected_definition_present": True, "selected_definition_magic_raw": 0x4744624F,
            "selected_definition_keys_u16": [0xFFFF] * 9,
            "current_cache_present": True, "current_cache_bytes": [7] * 9,
            "unavailable_reason": None,
        },
        "unavailable_reason": None,
    }
    frozen = deepcopy(raw)
    normalized = _normalize_raw_numeric_inputs(raw, "raw")
    normalized_frozen = deepcopy(normalized)
    skill_context = NativeModifierContext12003(
        PropertyContainer12003((0x3A, 0x3D, 0x3E), (7, 20, 30), 3),
        (WeightedModifierRow12003(PropertyContainer12003((0x38, 0x39), (300, 40), 2), 100000, 0),
         WeightedModifierRow12003(PropertyContainer12003((0x38, 0x39), (-100, -70), 2), 100000, 1)), 2)
    model_context = NativeModifierContext12003(
        PropertyContainer12003((0x225, 0x228, 0x22A), (1200000, -399999, 250000), 3), (), 0)
    skill = ExplicitPersonCacheStage12003(29829, "post291D1D0_explicit_logical", skill_context)
    model = ExplicitPersonCacheStage12003(29829, "explicit_scratch258_model_stage", model_context)
    result = project_person_cache_stage_12003(normalized, skill_stage=skill, scratch_model_stage=model)
    assert result.ready and result.missing_inputs == ()
    assert result.six_skills.final_cache_points == (1, 2, 3, 4, 5, 6)
    assert (result.auxiliary.scratch430_q64, result.auxiliary.scratch438_q64) == (270, -13)
    assert result.nine_bytes.cache_bytes == (2, -3, 0, 0, 12, 0, 0, 0, 0)
    assert result.auxiliary.ledger["observed_prepared_q64"] == (999, -888)
    assert result.auxiliary.ledger["observed_copied_q64"] == (777, -666)
    assert result.nine_bytes.ledger["observed_current_cache_bytes"] == (7,) * 9
    assert result.nine_bytes.ledger["source_scope"] == "explicit_logical_scratch258_model_stage"
    assert not result.source_ledger["nine_model_defaulted_from_skill_context"]
    assert not result.source_ledger["skill_context_defaulted_from_nine_model"]
    assert raw == frozen and normalized == normalized_frozen

    # No implicit copy of the ready skill context into the missing nine-model stage.
    partial = project_person_cache_stage_12003(normalized, skill_stage=skill)
    assert not partial.ready and partial.six_skills.calculation_ready
    assert partial.auxiliary.calculation_ready and not partial.nine_bytes.calculation_ready
    assert partial.nine_bytes.cache_bytes == (None,) * 9
    independent = project_person_cache_stage_12003(normalized, scratch_model_stage=model)
    assert not independent.ready and independent.nine_bytes.calculation_ready
    assert not independent.six_skills.calculation_ready and not independent.auxiliary.calculation_ready

    wrong_actor = ExplicitPersonCacheStage12003(29830, skill.stage, skill.context)
    mixed = project_person_cache_stage_12003(normalized, skill_stage=wrong_actor, scratch_model_stage=model)
    assert not mixed.ready and mixed.nine_bytes.calculation_ready
    assert "skill_auxiliary_stage.queried_actor_association" in mixed.missing_inputs

    noop_raw = deepcopy(raw)
    noop_raw.update(scratch_present=False, context=None, context_source="not_required_no_scratch")
    noop = project_person_cache_stage_12003(_normalize_raw_numeric_inputs(noop_raw, "raw"))
    assert noop.ready and noop.six_skills.status == "source_noop"
    assert noop.auxiliary.status == "native_noop" and noop.nine_bytes.status == "native_noop"
    assert noop.nine_bytes.cache_bytes == (None,) * 9
    for projection in (result, partial, independent, mixed, noop):
        assert not projection.native_write_performed and not projection.historical_stage_observed
        assert not projection.entry_refresh_ready and not projection.full_native_callback_ready
        assert projection.actual_game_days_advanced == 0
