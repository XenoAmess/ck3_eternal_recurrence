"""Exact DWORD admission, demanded-PC readiness and prefix request contract."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import (
    emit_pre_291e210_1640_requests_from_current_source_inputs_12003,
    normalize_current_context_source_inputs,
)


def block(count=0):
    return {
        "keys_count": count, "values_count": None if count == 0 else count,
        "keys_u16": [] if count == 0 else [65535, 7],
        "values_q64": [] if count == 0 else [0, -(1 << 63)], "reason": None,
    }


def section(first=0, second=0):
    early_false = first == -1
    admitted = False if early_false else first == second
    return {
        "status": "partial", "ready": False, "character_id": 29829,
        "branch_291e210": None, "reason": "independent_A_inputs_unavailable",
        "pre_291e210_1640": {
            "status": "available", "ready": True, "character_id": 29829,
            "army_selection": "registry_full_id", "army_key_f4_raw": -1426063359,
            "army_field_120_raw": first,
            "army_field_124_raw": None if early_false else -855638015,
            "second_selection": None if early_false else "registry_full_id",
            "second_field_174_raw": None if early_false else second,
            "admitted": admitted, "property_block": block() if admitted else None,
            "unavailable_reason": None,
        },
    }


@pytest.mark.parametrize("first,second,expected", [
    (-1, None, False), (0, 0, True), (-2147483641, -2147483641, True),
    (0, 1, False), (123, -123, False),
])
def test_exact_predicate_and_unit_request(first, second, expected):
    raw = section(first, second)
    before = deepcopy(raw)
    normalized = normalize_current_context_source_inputs(raw)
    leaf = normalized["pre_291e210_1640"]
    assert leaf["admitted"] is expected
    requests = emit_pre_291e210_1640_requests_from_current_source_inputs_12003(normalized)
    assert len(requests) == int(expected)
    if expected:
        request = requests[0]
        assert request.source_name == "pre_291e210_1640"
        assert request.source_ordinal == 0 and request.weight_q64 == 100000
        assert request.base_property_block is leaf["property_block"]
        assert request.base_property_block["keys_count"] == 0
    assert raw == before


def test_signed_bits_paired_values_and_native_fallback_zero():
    raw = section()
    leaf = raw["pre_291e210_1640"]
    leaf.update(army_selection="native_fallback", second_selection="native_fallback",
                army_key_f4_raw=None, army_field_124_raw=None, property_block=block(2))
    normalized = normalize_current_context_source_inputs(raw)
    request, = emit_pre_291e210_1640_requests_from_current_source_inputs_12003(normalized)
    assert request.base_property_block["keys_u16"] == [65535, 7]
    assert request.base_property_block["values_q64"] == [0, -(1 << 63)]
    assert normalized["pre_291e210_1640"]["army_field_124_raw"] is None


def test_unread_operand_and_missing_property_remain_partial():
    raw = section()
    leaf = raw["pre_291e210_1640"]
    leaf.update(status="partial", ready=False, second_field_174_raw=None,
                admitted=None, property_block=None,
                unavailable_reason="second_field_174_read_unavailable")
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["pre_291e210_1640"]["admitted"] is None
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_pre_291e210_1640_requests_from_current_source_inputs_12003(normalized)
    leaf.update(second_field_174_raw=0, admitted=True,
                unavailable_reason="provider_1640_consumed_properties_unavailable")
    assert normalize_current_context_source_inputs(raw)["pre_291e210_1640"]["admitted"] is True


@pytest.mark.parametrize("key,value", [
    ("army_field_120_raw", True), ("army_field_120_raw", 1.0),
    ("army_field_120_raw", 1 << 31), ("second_field_174_raw", -(1 << 31) - 1),
    ("admitted", 1), ("ready", 1), ("army_selection", "commander"),
])
def test_closed_native_wire_types(key, value):
    raw = section()
    raw["pre_291e210_1640"][key] = value
    with pytest.raises(ValueError):
        normalize_current_context_source_inputs(raw)


def test_admission_and_short_circuit_follow_actual_operands():
    raw = section(0, 1)
    raw["pre_291e210_1640"]["admitted"] = True
    with pytest.raises(ValueError, match="DWORD predicate"):
        normalize_current_context_source_inputs(raw)
    raw = section(-1, None)
    raw["pre_291e210_1640"]["army_field_124_raw"] = 0
    with pytest.raises(ValueError, match="undemanded second"):
        normalize_current_context_source_inputs(raw)


def test_actor_join_and_unavailable_older_producer():
    raw = section()
    raw["pre_291e210_1640"]["character_id"] = 29830
    with pytest.raises(ValueError, match="source actor"):
        normalize_current_context_source_inputs(raw)
    del raw["pre_291e210_1640"]
    old = normalize_current_context_source_inputs(raw)
    assert "pre_291e210_1640" not in old
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_pre_291e210_1640_requests_from_current_source_inputs_12003(old)
