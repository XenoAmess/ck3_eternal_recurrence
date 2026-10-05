from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import (
    normalize_current_context_source_inputs,
)
from xar_autoplayer.bridge.battle_person_helper_291f0a0_contract import (
    emit_helper_291f0a0_family_requests_from_current_source_inputs_12003,
    emit_helper_291f0a0_requests_from_current_source_inputs_12003,
)


def pc():
    return {"keys_count": 1, "values_count": 1, "keys_u16": [5],
            "values_q64": [-9], "reason": None}


def row(index, identity="h0", gate=None, admitted=True):
    return {"native_index": index, "source_identity": identity, "gate_raw": gate,
            "admitted": admitted, "property_block": pc() if admitted else None,
            "reason": None}


def family(rows, count, array, selected="fixture_source"):
    return {"status": "available", "ready": True, "selected_source": selected,
            "admitted": True, "count": count, "array_present": array,
            "rows": rows, "reason": None}


def source():
    helper = {
        "status": "available", "ready": True, "character_id": 29829,
        "first_selection": "registry_full_id_8", "first_key_b4_raw": -1426063359,
        "manager_present": True, "manager_definition_selection": "manager_ef0",
        "manager_definition_identity": "h1", "recipient_source": "character_1c8_a0",
        "recipient_q64": 0, "range_count_raw": 0,
        "range_selection": "inline_default_5d70fc0", "range_native_index": None,
        "range_lower_q64": None, "range_upper_q64": None,
        "default_pc_guard_raw": -2, "pointer_list_guard_raw": None,
        "predicate_character_15c_raw": 0, "predicate_first_key_b4_raw": -1426063359,
        "predicate_second_key_4b8_raw": None, "predicate_second_a0_raw": 0,
        "predicate_admitted": True,
        "primary_direct": family([row(0), row(1)], 2, True),
        "manager_range": family([row(0, "h2", gate=0, admitted=False)], 0, None),
        "source_a18": family([row(0, "h3", gate=1), row(1, "h3", gate=1)], 2, True),
        "conditional_direct": family([row(0), row(1)], 2, True),
        "reason": None,
    }
    return {"status": "partial", "ready": False, "character_id": 29829,
            "branch_291e210": None, "reason": "other_source_families_unobserved",
            "helper_291f0a0": helper}


def unavailable_manager(raw, reason):
    h = raw["helper_291f0a0"]
    h.update(status="partial", ready=False, reason="helper_current_families_partial")
    h["manager_range"].update(status="partial", ready=False, reason=reason,
                              rows=None, count=None)
    h.update(range_count_raw=None, range_selection=None, default_pc_guard_raw=None)
    return h


def test_four_family_order_occurrences_identity_and_actual_block_references():
    normalized = normalize_current_context_source_inputs(source())
    h = normalized["helper_291f0a0"]
    requests = emit_helper_291f0a0_requests_from_current_source_inputs_12003(normalized)
    assert [r.source_ordinal for r in requests] == [0, 0, 2, 2, 3, 3]
    assert [r.first_row_index for r in requests] == [0, 1, 0, 1, 0, 1]
    assert requests[0].definition_identity == requests[1].definition_identity
    assert requests[0].base_property_block is h["primary_direct"]["rows"][0]["property_block"]
    assert requests[2].base_property_block is h["source_a18"]["rows"][0]["property_block"]
    assert all(r.weight_q64 == 100000 and r.row_count == 1 for r in requests)
    assert normalized["ready"] is False


def test_admitted_manager_pc_is_between_primary_and_a18():
    raw = source()
    h = raw["helper_291f0a0"]
    h["manager_range"] = family([row(0, "range1", gate=1)], 1, None)
    h.update(range_count_raw=2, range_selection="first_matching_stored_interval",
             range_native_index=1, range_lower_q64=10, range_upper_q64=20,
             recipient_q64=10, default_pc_guard_raw=None)
    normalized = normalize_current_context_source_inputs(raw)
    requests = emit_helper_291f0a0_requests_from_current_source_inputs_12003(normalized)
    assert [r.source_ordinal for r in requests] == [0, 0, 1, 2, 2, 3, 3]
    assert requests[2].definition_identity == "range1"
    assert requests[2].base_property_block is normalized["helper_291f0a0"]["manager_range"]["rows"][0]["property_block"]


def test_absent_recipient_keeps_other_three_families_independently_useful():
    raw = source()
    h = unavailable_manager(raw, "absent_carrier_contribution_inputs_unobserved")
    h.update(recipient_source="absent_1c8_2bfac30_unobserved", recipient_q64=None)
    normalized = normalize_current_context_source_inputs(raw)
    for f in ("primary_direct", "source_a18", "conditional_direct"):
        assert len(emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(normalized, f)) == 2
    with pytest.raises(ValueError, match="unavailable"):
        emit_helper_291f0a0_requests_from_current_source_inputs_12003(normalized)
    with pytest.raises(ValueError, match="unavailable"):
        emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(normalized, "manager_range")


def test_actual_lazy_null_manager_cannot_be_converted_to_initialized_empty_pc():
    raw = source()
    h = unavailable_manager(raw, "helper_native_manager_not_initialized")
    h.update(manager_present=False, manager_definition_selection=None,
             manager_definition_identity=None, recipient_source=None, recipient_q64=None)
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["helper_291f0a0"]["manager_present"] is False
    assert normalized["helper_291f0a0"]["manager_range"]["count"] is None
    assert len(emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(normalized, "primary_direct")) == 2


def test_lazy_default_zero_bytes_stay_partial_with_actual_guard():
    raw = source()
    h = raw["helper_291f0a0"]
    h.update(status="partial", ready=False, reason="helper_current_families_partial",
             default_pc_guard_raw=0)
    m = h["manager_range"]
    m.update(status="partial", ready=False, reason="helper_default_pc_not_initialized")
    m["rows"][0]["reason"] = "helper_default_pc_not_initialized"
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["helper_291f0a0"]["manager_range"]["count"] == 0
    assert normalized["helper_291f0a0"]["default_pc_guard_raw"] == 0


def test_early_minus_one_predicate_false_skips_all_conditional_operands():
    raw = source()
    h = raw["helper_291f0a0"]
    h.update(predicate_character_15c_raw=-1, predicate_first_key_b4_raw=None,
             predicate_second_key_4b8_raw=None, predicate_second_a0_raw=None,
             predicate_admitted=False)
    h["conditional_direct"].update(admitted=False, count=None, array_present=None, rows=[])
    normalized = normalize_current_context_source_inputs(raw)
    assert emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(normalized, "conditional_direct") == ()
    h["predicate_second_a0_raw"] = 0
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(raw)


def test_partial_nonzero_source_property_keeps_admission_and_native_failure():
    raw = source()
    h = raw["helper_291f0a0"]
    h.update(status="partial", ready=False, reason="helper_current_families_partial")
    f = h["source_a18"]
    f.update(status="partial", ready=False, reason="properties_unavailable")
    f["rows"][0]["reason"] = "properties_unavailable"
    f["rows"][0]["property_block"].update(keys_u16=None, values_q64=None)
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["helper_291f0a0"]["source_a18"]["rows"][0]["admitted"] is True
    assert len(emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(normalized, "primary_direct")) == 2


def test_source_actor_join_and_legacy_field_omission():
    raw = source()
    raw["helper_291f0a0"]["character_id"] += 1
    with pytest.raises(ValueError, match="source actor"):
        normalize_current_context_source_inputs(raw)
    del raw["helper_291f0a0"]
    old = normalize_current_context_source_inputs(raw)
    assert "helper_291f0a0" not in old
    with pytest.raises(ValueError, match="unavailable"):
        emit_helper_291f0a0_requests_from_current_source_inputs_12003(old)


@pytest.mark.parametrize("key,value", [
    ("recipient_q64", True), ("predicate_character_15c_raw", 2**31),
    ("predicate_admitted", False),
])
def test_native_types_and_exact_predicate(key, value):
    raw = source()
    raw["helper_291f0a0"][key] = value
    with pytest.raises(ValueError):
        normalize_current_context_source_inputs(raw)
