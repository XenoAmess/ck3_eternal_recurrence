from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import (
    normalize_current_context_source_inputs,
)
from xar_autoplayer.bridge.battle_person_later_direct_contract import (
    emit_later_direct_requests_from_current_source_inputs_12003,
)


def empty_pc():
    return {"keys_count": 0, "values_count": None, "keys_u16": [],
            "values_q64": [], "reason": None}


def source():
    row = {"native_index": 0, "requested_full_id_raw": -1426063359,
           "selection": "registry_full_id", "selected_identity": "later0",
           "selected_field_24c_raw": -7, "admitted": True,
           "property_block": empty_pc(), "reason": None}
    duplicate = deepcopy(row)
    duplicate["native_index"] = 1
    skipped = {"native_index": 2, "requested_full_id_raw": 0,
               "selection": "native_fallback", "selected_identity": "later1",
               "selected_field_24c_raw": 0, "admitted": False,
               "property_block": None, "reason": None}
    return {"status": "partial", "ready": False, "character_id": 29829,
            "branch_291e210": None, "reason": "other_source_families_unobserved",
            "later_direct_291c3fb_44c": {
                "status": "available", "ready": True, "character_id": 29829,
                "ordered_header_selection": "character_1b0_inline_98",
                "ordered_count": 3, "ordered_array_present": True,
                "ordered_rows": [row, duplicate, skipped],
                "guarded_selection": "character_1c0_pointer_388",
                "guarded_magic_raw": 0x4744624F, "guarded_admitted": True,
                "guarded_property_block": empty_pc(), "reason": None,
            }}


def test_stored_duplicate_requests_then_aa0_preserve_actual_blocks():
    normalized = normalize_current_context_source_inputs(source())
    leaf = normalized["later_direct_291c3fb_44c"]
    requests = emit_later_direct_requests_from_current_source_inputs_12003(normalized)
    assert [(r.source_name, r.first_row_index, r.row_count) for r in requests] == [
        ("ordered_291c3fb_80", 0, 1), ("ordered_291c3fb_80", 1, 1),
        ("guarded_291c44c_aa0", 0, 1)]
    assert requests[0].definition_identity == requests[1].definition_identity == "later0"
    assert requests[0].base_property_block is leaf["ordered_rows"][0]["property_block"]
    assert requests[1].base_property_block is leaf["ordered_rows"][1]["property_block"]
    assert requests[2].base_property_block is leaf["guarded_property_block"]
    assert all(r.weight_q64 == 100000 for r in requests)
    assert normalized["ready"] is False


def test_native_zero_count_and_false_magic_are_complete_empty_direct_family():
    raw = source()
    leaf = raw["later_direct_291c3fb_44c"]
    leaf.update(ordered_header_selection="inline_static_545a3e8", ordered_count=0,
                ordered_array_present=False, ordered_rows=[],
                guarded_selection="native_fallback", guarded_magic_raw=0,
                guarded_admitted=False, guarded_property_block=None)
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["later_direct_291c3fb_44c"]["ready"] is True
    assert emit_later_direct_requests_from_current_source_inputs_12003(normalized) == ()


def test_observation_failure_stays_nullable_instead_of_false_or_fallback():
    raw = source()
    leaf = raw["later_direct_291c3fb_44c"]
    row = leaf["ordered_rows"][0]
    row.update(selection=None, selected_identity=None, selected_field_24c_raw=None,
               admitted=None, property_block=None, reason="registry_read_unavailable")
    leaf.update(status="partial", ready=False, reason="registry_read_unavailable")
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["later_direct_291c3fb_44c"]["ordered_rows"][0]["admitted"] is None
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_later_direct_requests_from_current_source_inputs_12003(normalized)


def test_admitted_property_failure_preserves_true_admission_and_unavailable_data():
    raw = source()
    leaf = raw["later_direct_291c3fb_44c"]
    row = leaf["ordered_rows"][0]
    row["property_block"].update(keys_count=1, keys_u16=None, values_q64=None,
                                 reason="consumed_read_unavailable")
    row["reason"] = "consumed_read_unavailable"
    leaf.update(status="partial", ready=False, reason="consumed_read_unavailable")
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["later_direct_291c3fb_44c"]["ordered_rows"][0]["admitted"] is True
    with pytest.raises(ValueError):
        emit_later_direct_requests_from_current_source_inputs_12003(normalized)


def test_negative_count_does_not_become_real_zero_and_no_vector_is_manufactured():
    raw = source()
    leaf = raw["later_direct_291c3fb_44c"]
    leaf.update(ordered_count=-1, ordered_rows=None, status="partial", ready=False,
                reason="negative_count_unrepresentable")
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["later_direct_291c3fb_44c"]["ordered_count"] == -1
    assert normalized["later_direct_291c3fb_44c"]["ordered_rows"] is None


def test_actor_join_and_old_producer_compatibility():
    raw = source()
    raw["later_direct_291c3fb_44c"]["character_id"] = 29830
    with pytest.raises(ValueError, match="source actor"):
        normalize_current_context_source_inputs(raw)
    del raw["later_direct_291c3fb_44c"]
    normalized = normalize_current_context_source_inputs(raw)
    assert "later_direct_291c3fb_44c" not in normalized
    with pytest.raises(ValueError, match="unavailable"):
        emit_later_direct_requests_from_current_source_inputs_12003(normalized)


@pytest.mark.parametrize("key,value", [
    ("selected_field_24c_raw", True), ("requested_full_id_raw", 2**31),
    ("admitted", False), ("native_index", 1),
])
def test_native_word_types_predicate_and_occurrence_order(key, value):
    raw = source()
    raw["later_direct_291c3fb_44c"]["ordered_rows"][0][key] = value
    with pytest.raises(ValueError):
        normalize_current_context_source_inputs(raw)


def test_zero_and_false_branches_reject_undemanded_property_values():
    raw = source()
    raw["later_direct_291c3fb_44c"]["ordered_rows"][2]["property_block"] = empty_pc()
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(raw)
    raw = source()
    leaf = raw["later_direct_291c3fb_44c"]
    leaf.update(guarded_magic_raw=0, guarded_admitted=False)
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(raw)
