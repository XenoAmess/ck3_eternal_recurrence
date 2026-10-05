from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_terminal_transition_contract import _normalize_raw_numeric_inputs
from xar_autoplayer.simulation.battle_person_auxiliary_scratch_12003 import (
    compute_auxiliary_scratch_from_native_inputs_12003,
)


def _raw():
    return {
        "status": "available", "raw_numeric_inputs_ready": True,
        "character_id": 29829, "scratch_present": True,
        "context_source": "model_inline", "base_points": [0] * 6,
        "caps": [100] * 6, "prowess_adjustment": 0, "category_counts": [0] * 4,
        "scratch_factor_numerator": 0, "scratch_factor_denominator": 100,
        "context": {
            "aggregate_properties": {"count": 5, "keys_u16": [0x3A, 0x3B, 0x3C, 0x3D, 0x3E],
                                     "values_q64": [7, 11, 13, 20, 30]},
            "weighted_count": 2,
            "weighted_rows": [
                {"native_index": 0, "weight_q64": 100000,
                 "properties": {"count": 2, "keys_u16": [0x38, 0x39], "values_q64": [300, 40]}},
                {"native_index": 1, "weight_q64": 100000,
                 "properties": {"count": 2, "keys_u16": [0x38, 0x39], "values_q64": [-100, -70]}},
            ],
        },
        "auxiliary_scratch_inputs": {
            "status": "available", "ready": True, "base430_q64": 50, "base438_q64": -20,
            "selector_flag_raw": 0, "selector_metric_raw": 9,
            "selected_low_threshold_raw": 10, "selected_high_threshold_raw": None,
            "prepared430_q64": 999, "prepared438_q64": -888,
            "copied430_q64": 777, "copied438_q64": -666, "ready440_raw": 0,
            "unavailable_reason": None,
        },
        "unavailable_reason": None,
    }


def test_current_normalizer_to_source_auxiliary_kernel():
    raw = _raw()
    frozen = deepcopy(raw)
    normalized = _normalize_raw_numeric_inputs(raw, "raw")
    result = compute_auxiliary_scratch_from_native_inputs_12003(normalized)
    assert (result.scratch430_q64, result.scratch438_q64, result.selected_property_key_u16) == (270, -13, 0x3A)
    assert result.calculation_ready and result.missing_inputs == ()
    assert result.ledger["observed_prepared_q64"] == (999, -888)
    assert result.ledger["observed_copied_q64"] == (777, -666)
    assert result.ledger["selector"]["demanded_high_raw"] is None
    assert not result.native_write_performed and not result.full_native_callback_ready
    assert not result.entry_refresh_ready and result.actual_game_days_advanced == 0
    assert raw == frozen

    for metric, high, key, answer in ((10, 20, 0x3B, -9), (20, 20, 0x3C, -7),
                                    (-32768, -32767, 0x3B, -9)):
        sample = _raw()
        aux = sample["auxiliary_scratch_inputs"]
        aux.update(selector_metric_raw=metric, selected_high_threshold_raw=high)
        if metric < 0:
            aux.update(selector_flag_raw=255, selected_low_threshold_raw=-32768)
        result = compute_auxiliary_scratch_from_native_inputs_12003(
            _normalize_raw_numeric_inputs(sample, "raw"))
        assert result.calculation_ready and result.selected_property_key_u16 == key
        assert result.scratch438_q64 == answer

    # Wrap before signed min, base outside the negative-tail choice, no 438 cap.
    sample = _raw()
    sample["context"]["weighted_rows"] = []
    sample["context"]["weighted_count"] = 0
    sample["context"]["aggregate_properties"] = {"count": 1, "keys_u16": [0x3D],
                                                   "values_q64": [-(2**63)]}
    sample["auxiliary_scratch_inputs"].update(base430_q64=-1, base438_q64=2**63 - 1)
    result = compute_auxiliary_scratch_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert result.calculation_ready and result.scratch430_q64 == 100000
    assert result.scratch438_q64 == 2**63 - 1

    # Empty/native-absent keys produce zero; missing demanded values are partial.
    sample = _raw()
    sample["context"]["aggregate_properties"]["values_q64"] = None
    sample.update(status="partial", raw_numeric_inputs_ready=False, unavailable_reason="values_unread")
    result = compute_auxiliary_scratch_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert not result.calculation_ready and result.scratch430_q64 is None
    assert result.scratch438_q64 is None and result.missing_inputs
    sample = _raw()
    sample["auxiliary_scratch_inputs"].update(status="partial", ready=False,
        selector_metric_raw=10, unavailable_reason="high_unread")
    result = compute_auxiliary_scratch_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert result.scratch430_q64 == 270 and result.scratch438_q64 is None
    assert "auxiliary_scratch_inputs.selected_high_threshold_raw" in result.missing_inputs

    sample = _raw()
    del sample["auxiliary_scratch_inputs"]
    assert "auxiliary_scratch_inputs" not in _normalize_raw_numeric_inputs(sample, "raw")
    assert not compute_auxiliary_scratch_from_native_inputs_12003(sample).calculation_ready
    sample["auxiliary_scratch_inputs"] = None
    assert _normalize_raw_numeric_inputs(sample, "raw")["auxiliary_scratch_inputs"] is None
    sample = _raw()
    sample.update(scratch_present=False, context_source="not_required_no_scratch", context=None)
    aux = sample["auxiliary_scratch_inputs"]
    for key in tuple(aux):
        if key not in {"status", "ready", "unavailable_reason"}:
            aux[key] = None
    result = compute_auxiliary_scratch_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert result.status == "native_noop" and result.calculation_ready
    assert result.scratch430_q64 is None and result.scratch438_q64 is None
    for key, value in (("selector_metric_raw", 32768), ("selector_flag_raw", True),
                       ("base430_q64", 2**63), ("selected_low_threshold_raw", 2**31)):
        sample = _raw()
        sample["auxiliary_scratch_inputs"][key] = value
        with pytest.raises(ValueError):
            _normalize_raw_numeric_inputs(sample, "raw")
