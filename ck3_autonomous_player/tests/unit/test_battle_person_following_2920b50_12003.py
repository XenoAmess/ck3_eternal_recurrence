from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_following_2920b50_contract import (
    emit_following_2920b50_requests_from_current_source_inputs_12003 as emit_all,
    emit_following_2920b50_family_requests_from_current_source_inputs_12003 as emit_family,
    emit_following_2920b50_attribute_requests_from_current_source_inputs_12003 as emit_attribute,
)

FIELD = "following_2920b50"
Q = 100000
NUMERIC = ("rank_raw_i32", "index_raw_i32", "ranked_header_identity", "ranked_count_raw",
           "ranked_array_present", "selection", "selected_row_identity", "ranked_default_init_guard_raw")


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def pc(*rows):
    return {"keys_count": len(rows), "values_count": len(rows), "keys_u16": [key for key, _ in rows],
            "values_q64": [value for _, value in rows], "reason": None}


def operand(identity=None, *rows):
    return {"property_identity": identity, "property_block": pc(*rows) if identity else None, "reason": None}


def attribute(index, rank, key, value):
    return {"native_index": index, "definition_present": True, "definition_identity": "definition:" + str(key),
        "definition_magic_u32": 0x4744624F, "preflight_valid": True, "rank_raw_i32": rank, "index_raw_i32": rank - 1,
        "ranked_header_identity": "ranked_header:" + str(key), "ranked_count_raw": 2, "ranked_array_present": True,
        "selection": "indexed_ranked_row", "selected_row_identity": "ranked_row:" + str(key),
        "ranked_default_init_guard_raw": None, "pc": operand("pc:" + str(key), (key, value)),
        "ready": True, "reason": None}


def occurrence(index, *, own=False):
    full_id = 0xAA000001 - 2**32
    attrs = [attribute(0, 2, 22, 2200), attribute(1, 1, 23, 2300)] if own else [
        attribute(0, 1, 11, 1100), attribute(1, 2, 14, 1400), attribute(2, 1, 11, 1100)]
    return {**availability(), "native_index": index, "requested_full_id_raw": full_id if not own else None,
        "resolution_selection": "native_fallback" if own else "registry_full_id_8",
        "selected_full_id_raw": None if own else full_id, "object_identity": "own:AccB" if own else "list:AccA",
        "accolade_magic_u32": 0x4163636F if own else None, "accolade_full_id_raw": 42 if own else None,
        "admitted": True, "attribute_count_raw": len(attrs), "attribute_array_present": True,
        "preflight_ready": True, "preflight_all_valid": True, "attributes": attrs}


def following2920b50_source():
    """Reusable genuine source input; import does not execute the producer case."""
    leaf = {**availability(), "character_id": 29829,
        "list_1c8_50": {**availability(), "component_present": True, "header_selection": "current_1c8_50",
            "default_init_guard_raw": None, "count_raw": 2, "numeric_count": 2, "array_present": True,
            "rows": [occurrence(i) for i in range(2)]},
        "own_1b0_570": {**availability(), "component_present": False, "occurrence": occurrence(0, own=True)}}
    return {"status": "partial", "ready": False, "character_id": 29829, "branch_291e210": None,
            "reason": "other_person_stages_unobserved", FIELD: leaf}


def preflight_only(row):
    row.update({key: None for key in NUMERIC})
    row.update(pc=operand(), ready=False, reason=None)


def zero_list(raw):
    raw[FIELD]["list_1c8_50"].update(count_raw=0, numeric_count=0, array_present=None, rows=[])


def test_following2920b50_entire_preflight_rank_demand_independent_attributes_empty_defaults_and_actor():
    raw = following2920b50_source()
    before = deepcopy(raw)
    source = normalize_current_context_source_inputs(raw)
    requests = emit_all(source)
    assert raw == before and len(requests) == 8 and all(item.weight_q64 == Q for item in requests)
    assert [item.source_ordinal for item in requests] == [0] * 6 + [1] * 2
    assert [item.first_row_index for item in requests[:6]] == [0, 0, 0, 1, 1, 1]
    assert [item.base_property_block["keys_u16"] for item in requests] == [[11], [14], [11], [11], [14], [11], [22], [23]]
    assert requests[0].base_property_block is source[FIELD]["list_1c8_50"]["rows"][0]["attributes"][0]["pc"]["property_block"]
    assert requests[-1].base_property_block is source[FIELD]["own_1b0_570"]["occurrence"]["attributes"][1]["pc"]["property_block"]
    assert source[FIELD]["own_1b0_570"]["component_present"] is False and len(emit_family(source, "own_1b0_570")) == 2

    invalid = following2920b50_source()
    for occurrence_row in invalid[FIELD]["list_1c8_50"]["rows"]:
        occurrence_row.update(preflight_all_valid=False)
        occurrence_row["attributes"] = occurrence_row["attributes"][:2]
        for row in occurrence_row["attributes"]:
            preflight_only(row)
        occurrence_row["attributes"][1].update(definition_magic_u32=0, preflight_valid=False)
    normalized = normalize_current_context_source_inputs(invalid)
    assert len(emit_all(normalized)) == 2 and emit_family(normalized, "list_1c8_50") == ()
    assert emit_attribute(normalized, "list_1c8_50", 0, 0) == ()
    assert emit_attribute(normalized, "list_1c8_50", 0, 2) == ()
    premature = deepcopy(invalid)
    premature[FIELD]["list_1c8_50"]["rows"][0]["attributes"][0]["rank_raw_i32"] = 1
    with pytest.raises(ValueError, match="entire preflight blocks"):
        normalize_current_context_source_inputs(premature)

    unknown = following2920b50_source()
    unknown[FIELD].update(availability(False, "preflight_unread"))
    unknown[FIELD]["list_1c8_50"].update(availability(False, "preflight_unread"))
    for occurrence_row in unknown[FIELD]["list_1c8_50"]["rows"]:
        occurrence_row.update(availability(False, "preflight_unread"))
        occurrence_row.update(preflight_ready=False, preflight_all_valid=None)
        occurrence_row["attributes"] = occurrence_row["attributes"][:2]
        for row in occurrence_row["attributes"]:
            preflight_only(row)
        occurrence_row["attributes"][1].update(definition_magic_u32=None, preflight_valid=None, reason="preflight_unread")
    normalized = normalize_current_context_source_inputs(unknown)
    assert len(emit_family(normalized, "own_1b0_570")) == 2
    with pytest.raises(ValueError, match="entire attribute preflight"):
        emit_attribute(normalized, "list_1c8_50", 0, 0)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_all(normalized)

    for guard in (0, -1):
        cold = following2920b50_source()
        cold[FIELD].update(availability(False, "ranked_default_initialization_result"))
        cold[FIELD]["list_1c8_50"].update(availability(False, "ranked_default_initialization_result"))
        for occurrence_row in cold[FIELD]["list_1c8_50"]["rows"]:
            occurrence_row.update(availability(False, "ranked_default_initialization_result"))
            row = occurrence_row["attributes"][0]
            row.update(rank_raw_i32=0, index_raw_i32=-1, ranked_count_raw=None, ranked_array_present=None,
                selection="uninitialized_default_5d68fb0", selected_row_identity="ranked_default:5d68fb0",
                ranked_default_init_guard_raw=guard, pc=operand(), ready=False, reason="ranked_default_initialization_result")
        normalized = normalize_current_context_source_inputs(cold)
        assert len(emit_family(normalized, "own_1b0_570")) == 2
        assert emit_attribute(normalized, "list_1c8_50", 0, 1)[0].base_property_block == pc((14, 1400))
        assert emit_attribute(normalized, "list_1c8_50", 1, 2)[0].base_property_block == pc((11, 1100))
        with pytest.raises(ValueError, match="ranked attribute PC"):
            emit_attribute(normalized, "list_1c8_50", 0, 0)
        with pytest.raises(ValueError, match="Required native input unavailable"):
            emit_family(normalized, "list_1c8_50")

    initialized = following2920b50_source()
    branch = initialized[FIELD]["list_1c8_50"]
    branch.update(count_raw=1, numeric_count=1, rows=branch["rows"][:1])
    attrs = branch["rows"][0]["attributes"]
    attrs[0].update(rank_raw_i32=-(2**31), index_raw_i32=2**31 - 1, ranked_count_raw=-3,
        ranked_array_present=None, selection="initialized_default_5d68fb0", selected_row_identity="ranked_default",
        ranked_default_init_guard_raw=9, pc=operand("actual:default_owner"))
    attrs[2].update(rank_raw_i32=0, index_raw_i32=-1, ranked_count_raw=None, ranked_array_present=None,
        selection="initialized_default_5d68fb0", selected_row_identity="ranked_default",
        ranked_default_init_guard_raw=9, pc=operand("actual:default_owner"))
    normalized = normalize_current_context_source_inputs(initialized)
    assert len(emit_all(normalized)) == 5
    assert [item.base_property_block for item in emit_family(normalized, "list_1c8_50")] == [pc(), pc((14, 1400)), pc()]
    undemanded_header = deepcopy(initialized)
    undemanded_header[FIELD]["list_1c8_50"]["rows"][0]["attributes"][2]["ranked_count_raw"] = 0
    with pytest.raises(ValueError, match="negative index contains undemanded"):
        normalize_current_context_source_inputs(undemanded_header)
    undemanded_guard = following2920b50_source()
    undemanded_guard[FIELD]["list_1c8_50"]["rows"][0]["attributes"][0]["ranked_default_init_guard_raw"] = 0
    with pytest.raises(ValueError, match="indexed row contains undemanded"):
        normalize_current_context_source_inputs(undemanded_guard)

    for guard in (0, -1, 9):
        modeled = following2920b50_source()
        branch = modeled[FIELD]["list_1c8_50"]
        branch.update(component_present=False, header_selection="inline_default_5d67e80" if guard == 9 else "modeled_empty_default_5d67e80",
            default_init_guard_raw=guard, count_raw=0 if guard == 9 else None, numeric_count=0, array_present=None, rows=[])
        own = modeled[FIELD]["own_1b0_570"]["occurrence"]
        own.update(accolade_magic_u32=0, accolade_full_id_raw=None, admitted=False, attribute_count_raw=None,
                   attribute_array_present=None, preflight_ready=True, preflight_all_valid=False, attributes=[])
        assert emit_all(normalize_current_context_source_inputs(modeled)) == ()
    own_bad_id = following2920b50_source()
    zero_list(own_bad_id)
    own = own_bad_id[FIELD]["own_1b0_570"]["occurrence"]
    own.update(accolade_full_id_raw=-1, admitted=False, attribute_count_raw=None, attribute_array_present=None,
               preflight_ready=True, preflight_all_valid=False, attributes=[])
    assert emit_all(normalize_current_context_source_inputs(own_bad_id)) == ()

    null_registry = following2920b50_source()
    for row in null_registry[FIELD]["list_1c8_50"]["rows"]:
        row.update(requested_full_id_raw=None, resolution_selection="native_fallback", selected_full_id_raw=None)
    assert len(emit_all(normalize_current_context_source_inputs(null_registry))) == 8
    zero_attributes = following2920b50_source()
    zero_list(zero_attributes)
    own = zero_attributes[FIELD]["own_1b0_570"]["occurrence"]
    own.update(attribute_count_raw=0, attribute_array_present=None, attributes=[])
    assert emit_all(normalize_current_context_source_inputs(zero_attributes)) == ()
    negative = following2920b50_source()
    negative[FIELD].update(availability(False, "negative_list_count"))
    negative[FIELD]["list_1c8_50"].update(availability(False, "negative_list_count"), count_raw=-1,
                                       numeric_count=-1, array_present=None, rows=[])
    normalized = normalize_current_context_source_inputs(negative)
    assert len(emit_family(normalized, "own_1b0_570")) == 2
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_family(normalized, "list_1c8_50")
    wrong_actor = following2920b50_source()
    wrong_actor[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="character"):
        normalize_current_context_source_inputs(wrong_actor)
