from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_terminal_transition_contract import _normalize_raw_numeric_inputs
from xar_autoplayer.simulation.battle_person_nine_cache_bytes_12003 import (
    BASE_KEYS_12003, compute_nine_cache_bytes_from_native_inputs_12003,
)


def _raw():
    return {
        "status": "available", "raw_numeric_inputs_ready": True,
        "character_id": 29829, "scratch_present": True,
        "context_source": "fallback_static", "base_points": [0] * 6,
        "caps": [100] * 6, "prowess_adjustment": 0, "category_counts": [0] * 4,
        "scratch_factor_numerator": 0, "scratch_factor_denominator": 100,
        "context": {"aggregate_properties": {"count": 0, "keys_u16": [], "values_q64": []},
                    "weighted_count": 0, "weighted_rows": []},
        "unavailable_reason": None,
        "nine_cache_byte_inputs": {
            "status": "available", "ready": True, "model_present": True,
            "aggregate_properties": {
                "count": 10, "keys_u16": [0x50, *range(0x225, 0x22E)],
                "values_q64": [200000, -99999, -250000, 10050000, -300000,
                               (2**31 - 1) * 100000 + 99999, 300000,
                               2**31 * 100000, 10100000, -10100000],
            },
            "carrier278_present": True, "carrier278_magic_raw": 0x41495374,
            "linked20_present": True, "used_native_definition_fallback": False,
            "selected_definition_present": True, "selected_definition_magic_raw": 0x4744624F,
            "selected_definition_keys_u16": [0x50, 0xFFFF, 0x225, 0x228, 0x50, 0x22D, 0x22C, 0x50, 0xFFFF],
            "current_cache_present": True,
            "current_cache_bytes": [127, -128, 0, 1, -1, 100, -100, 2, -2],
            "unavailable_reason": None,
        },
    }


def test_actual_model_normalizer_to_nine_cache_byte_kernel():
    sample = _raw()
    prior = deepcopy(sample)
    result = compute_nine_cache_bytes_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert result.calculation_ready and result.optional_family_admitted is True
    assert result.cache_bytes == (5, -3, 100, 100, 1, -100, 100, 0, 100)
    assert result.ledger["base_keys_in_native_order"] == BASE_KEYS_12003
    assert result.ledger["observed_current_cache_bytes"] == (127, -128, 0, 1, -1, 100, -100, 2, -2)
    assert result.points_low32[2] == 2**31 - 1
    assert result.sums_q64[5] == -20200000
    assert sample == prior and not result.native_write_performed and not result.entry_refresh_ready
    assert not result.full_native_callback_ready and result.actual_game_days_advanced == 0

    for use_fallback in (False, True):
        sample = _raw()
        nine = sample["nine_cache_byte_inputs"]
        nine.update(linked20_present=not use_fallback, used_native_definition_fallback=use_fallback,
                    selected_definition_keys_u16=[0xFFFF] * 9)
        result = compute_nine_cache_bytes_from_native_inputs_12003(
            _normalize_raw_numeric_inputs(sample, "raw"))
        assert result.calculation_ready and result.cache_bytes == (3, -3, -100, 100, 0, -100, 100, -2, 100)
        assert result.points_low32[2] == -(2**31)

    # Wrong first guard does not demand linked/definition fields; wrong second
    # guard does not demand nine keys. Native key absence and zero count are0.
    for guard in (1, 2):
        sample = _raw()
        nine = sample["nine_cache_byte_inputs"]
        nine["selected_definition_keys_u16"] = None
        if guard == 1:
            nine.update(carrier278_magic_raw=0, linked20_present=None,
                        used_native_definition_fallback=None, selected_definition_present=None,
                        selected_definition_magic_raw=None)
        else:
            nine["selected_definition_magic_raw"] = 0
        nine["aggregate_properties"] = {"count": 0, "keys_u16": [], "values_q64": []}
        nine.update(current_cache_present=False, current_cache_bytes=None)
        result = compute_nine_cache_bytes_from_native_inputs_12003(
            _normalize_raw_numeric_inputs(sample, "raw"))
        assert result.calculation_ready and result.optional_family_admitted is False
        assert result.cache_bytes == (0,) * 9

    # Addition wraps64 before division; lower clamp uses signedlow32.
    sample = _raw()
    nine = sample["nine_cache_byte_inputs"]
    nine["aggregate_properties"] = {"count": 1, "keys_u16": [0x225], "values_q64": [2**63 - 1]}
    nine["selected_definition_keys_u16"] = [0xFFFF] * 9
    nine["selected_definition_keys_u16"][4] = 0x225
    result = compute_nine_cache_bytes_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert result.calculation_ready and result.sums_q64[4] == -2
    assert result.points_low32[4] == 0 and result.cache_bytes[4] == 0
    for missing in ("model", "carrier", "definition", "values", "keys"):
        sample = _raw()
        nine = sample["nine_cache_byte_inputs"]
        nine.update(status="partial", ready=False, unavailable_reason="demanded_input_unread")
        if missing == "model":
            nine.update(model_present=False, aggregate_properties=None)
        elif missing == "carrier":
            nine.update(carrier278_present=False, carrier278_magic_raw=None)
        elif missing == "definition":
            nine.update(selected_definition_present=False, selected_definition_magic_raw=None,
                        selected_definition_keys_u16=None)
        elif missing == "values":
            nine["aggregate_properties"]["values_q64"] = None
        else:
            nine["selected_definition_keys_u16"] = None
        result = compute_nine_cache_bytes_from_native_inputs_12003(
            _normalize_raw_numeric_inputs(sample, "raw"))
        assert not result.calculation_ready and result.missing_inputs

    sample = _raw()
    del sample["nine_cache_byte_inputs"]
    assert "nine_cache_byte_inputs" not in _normalize_raw_numeric_inputs(sample, "raw")
    assert not compute_nine_cache_bytes_from_native_inputs_12003(sample).calculation_ready
    sample["nine_cache_byte_inputs"] = None
    assert _normalize_raw_numeric_inputs(sample, "raw")["nine_cache_byte_inputs"] is None
    sample = _raw()
    sample.update(scratch_present=False, context=None, context_source="not_required_no_scratch")
    for key in tuple(sample["nine_cache_byte_inputs"]):
        if key not in {"status", "ready", "unavailable_reason"}:
            sample["nine_cache_byte_inputs"][key] = None
    result = compute_nine_cache_bytes_from_native_inputs_12003(
        _normalize_raw_numeric_inputs(sample, "raw"))
    assert result.status == "native_noop" and result.calculation_ready and result.cache_bytes == (None,) * 9
    for key, bad in (("selected_definition_keys_u16", [0xFFFF] * 8),
                     ("current_cache_bytes", [128] * 9), ("carrier278_magic_raw", True)):
        sample = _raw()
        sample["nine_cache_byte_inputs"][key] = bad
        with pytest.raises(ValueError):
            _normalize_raw_numeric_inputs(sample, "raw")
