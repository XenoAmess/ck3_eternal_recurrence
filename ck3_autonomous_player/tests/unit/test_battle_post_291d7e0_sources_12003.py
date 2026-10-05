"""Current post-B DTO and unit-request consumer; no native or Entry inference."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import (
    emit_post_291d7e0_requests_from_current_source_inputs_12003,
    normalize_current_context_source_inputs,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    _normalize_current_person_state,
)


def properties(empty=False):
    return {
        "keys_count": 0 if empty else 2,
        "values_count": None if empty else 9,
        "keys_u16": [] if empty else [65535, 7],
        "values_q64": [] if empty else [0, -200000], "reason": None,
    }


def section():
    return {
        "status": "partial", "ready": False, "character_id": 29829,
        "branch_291e210": None, "reason": "independent_A_inputs_unavailable",
        "post_291d7e0_sources": {
            "status": "available", "ready": True, "character_id": 29829,
            "unavailable_reason": None,
            "guarded630": {
                "status": "available", "ready": True, "carrier_1b0_present": True,
                "carrier280_present": True, "selection": "carrier280_qword8",
                "selected_field38_raw": 0x4744624F, "character68_signed": -5,
                "threshold_signed": -5, "admitted": True,
                "property_block": properties(True), "unavailable_reason": None,
            },
            "carrier40": {
                "status": "available", "ready": True, "carrier_1b0_present": True,
                "carrier288_present": True, "admitted": True,
                "property_block": properties(), "unavailable_reason": None,
            },
            "ordered_d8": {
                "status": "available", "ready": True, "carrier_1c0_present": False,
                "header_selection": "inline_static54E7270", "source_array_present": True,
                "source_count_raw": 3,
                "occurrences": [
                    {"source_index": i, "source_identity": identity,
                     "property_block": properties(i == 1), "unavailable_reason": None}
                    for i, identity in enumerate(("post0", "post1", "post0"))
                ], "unavailable_reason": None,
            },
        },
    }


def test_existing_current_person_authority_and_ordered_requests():
    raw = section()
    before = deepcopy(raw)
    person = {
        "scope": "current_character",
        "effective_prowess": {"status": "available", "points": 0, "unavailable_reason": None},
        "injury_traits": {
            "status": "available", "flags": {key: False for key in (
                "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
                "one_eyed", "disfigured", "incapable")},
            "wounded_rank": 0, "unavailable_reason": None,
            "wounded_rank_unavailable_reason": None,
        },
        "current_context_source_inputs": raw,
    }
    normalized = _normalize_current_person_state(person, "current_person_state")["current_context_source_inputs"]
    post = normalized["post_291d7e0_sources"]
    requests = emit_post_291d7e0_requests_from_current_source_inputs_12003(normalized)
    assert [r.source_name for r in requests] == [
        "post_291d7e0_guarded630", "post_291d7e0_carrier40",
        *["post_291d7e0_ordered_d8"] * 3,
    ]
    assert [r.definition_identity for r in requests[2:]] == ["post0", "post1", "post0"]
    assert [r.first_row_index for r in requests[2:]] == [0, 1, 2]
    assert all(r.weight_q64 == 100000 and r.row_count == 1 for r in requests)
    assert requests[0].base_property_block is post["guarded630"]["property_block"]
    assert requests[3].base_property_block is post["ordered_d8"]["occurrences"][1]["property_block"]
    assert requests[0].base_property_block["keys_count"] == 0
    assert requests[1].base_property_block["values_count"] == 9
    assert raw == before


@pytest.mark.parametrize("signed,threshold,admitted", [
    (-5, -5, True), (-5, -4, False), (32767, 32768, False), (-32768, -32769, True),
])
def test_signed16_sign_extension_and_signed32_threshold(signed, threshold, admitted):
    raw = section()
    guard = raw["post_291d7e0_sources"]["guarded630"]
    guard.update(character68_signed=signed, threshold_signed=threshold, admitted=admitted,
                 property_block=properties(True) if admitted else None)
    normalized = normalize_current_context_source_inputs(raw)
    requests = emit_post_291d7e0_requests_from_current_source_inputs_12003(normalized)
    assert (requests[0].source_name == "post_291d7e0_guarded630") is admitted


def test_null_carrier_fallback_and_wrong_magic_short_circuit():
    raw = section()
    post = raw["post_291d7e0_sources"]
    post["guarded630"].update(carrier_1b0_present=False, carrier280_present=None,
                              selection="native_fallback5D1E308", selected_field38_raw=-1,
                              character68_signed=None, threshold_signed=None,
                              admitted=False, property_block=None)
    post["carrier40"].update(carrier_1b0_present=False, carrier288_present=None,
                             admitted=False, property_block=None)
    normalized = normalize_current_context_source_inputs(raw)
    requests = emit_post_291d7e0_requests_from_current_source_inputs_12003(normalized)
    assert len(requests) == 3
    assert all(r.source_name == "post_291d7e0_ordered_d8" for r in requests)


@pytest.mark.parametrize("count", [0, -1])
def test_real_empty_vs_negative_unavailable_count(count):
    raw = section()
    post = raw["post_291d7e0_sources"]
    ordered = post["ordered_d8"]
    ordered.update(source_array_present=False, source_count_raw=count, occurrences=[] if count == 0 else None)
    if count < 0:
        ordered.update(status="partial", ready=False, unavailable_reason="ordered_d8_negative_count")
        post.update(status="partial", ready=False, unavailable_reason="post_291d7e0_sources_partial")
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["post_291d7e0_sources"]["ordered_d8"]["source_count_raw"] == count
    if count == 0:
        assert len(emit_post_291d7e0_requests_from_current_source_inputs_12003(normalized)) == 2
    else:
        with pytest.raises(ValueError, match="Required native input unavailable"):
            emit_post_291d7e0_requests_from_current_source_inputs_12003(normalized)


def test_unread_demanded_pc_keeps_other_current_leaves():
    raw = section()
    post = raw["post_291d7e0_sources"]
    post["carrier40"].update(status="partial", ready=False, property_block=None,
                             unavailable_reason="carrier288_selected_object_read_unavailable")
    post.update(status="partial", ready=False, unavailable_reason="post_291d7e0_sources_partial")
    normalized = normalize_current_context_source_inputs(raw)
    assert normalized["post_291d7e0_sources"]["guarded630"]["ready"]
    assert normalized["post_291d7e0_sources"]["carrier40"]["admitted"] is True
    assert normalized["post_291d7e0_sources"]["ordered_d8"]["occurrences"][2]["source_identity"] == "post0"
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_post_291d7e0_requests_from_current_source_inputs_12003(normalized)


@pytest.mark.parametrize("leaf,key,value", [
    ("guarded630", "character68_signed", 32768),
    ("guarded630", "threshold_signed", True),
    ("guarded630", "selected_field38_raw", 1 << 31),
    ("guarded630", "admitted", 1),
    ("ordered_d8", "source_count_raw", True),
    ("ordered_d8", "header_selection", "static_slot_pointer"),
])
def test_native_wire_types_and_inline_header_selection(leaf, key, value):
    raw = section()
    raw["post_291d7e0_sources"][leaf][key] = value
    with pytest.raises(ValueError):
        normalize_current_context_source_inputs(raw)


def test_actor_and_stored_occurrence_order():
    raw = section()
    raw["post_291d7e0_sources"]["character_id"] = 29830
    with pytest.raises(ValueError, match="source actor"):
        normalize_current_context_source_inputs(raw)
    raw = section()
    raw["post_291d7e0_sources"]["ordered_d8"]["occurrences"][1]["source_index"] = 0
    with pytest.raises(ValueError, match="stored occurrence order"):
        normalize_current_context_source_inputs(raw)
    del raw["post_291d7e0_sources"]
    old = normalize_current_context_source_inputs(raw)
    assert "post_291d7e0_sources" not in old
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_post_291d7e0_requests_from_current_source_inputs_12003(old)
