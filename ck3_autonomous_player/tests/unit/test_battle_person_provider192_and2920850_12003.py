from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_provider192_and2920850_contract import (
    emit_provider192_and2920850_requests_from_current_source_inputs_12003 as emit_all,
    emit_provider192_and2920850_family_requests_from_current_source_inputs_12003 as emit_family,
    emit_provider192_and2920850_slot_requests_from_current_source_inputs_12003 as emit_slot,
    emit_provider192_and2920850_descriptor_requests_from_current_source_inputs_12003 as emit_descriptor,
)

FIELD = "provider192_and2920850"
Q = 100000
FAMILIES = ("provider_192", "list_168", "list_180")


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def pc(*rows):
    return {"keys_count": len(rows), "values_count": len(rows), "keys_u16": [key for key, _ in rows],
            "values_q64": [value for _, value in rows], "reason": None}


def operand(identity=None, *rows):
    return {"property_identity": identity, "property_block": pc(*rows) if identity else None, "reason": None}


def rite(consumed=True):
    return {"first_key_b4_raw": 1 if consumed else None, "second_key_4b8_raw": 2 if consumed else None,
        "third_key_98_raw": 3 if consumed else None, "first_selection": "registry_full_id_8" if consumed else None,
        "second_selection": "native_fallback" if consumed else None, "third_selection": "registry_full_id_8" if consumed else None,
        "selected_identity": "rite:750" if consumed else None, "membership_count": 2 if consumed else None,
        "membership_array_present": True if consumed else None,
        "membership_identities": ["key:A", "key:B"] if consumed else None, "reason": None}


def mapped_row(index, key, *, admitted=True, shared=None):
    return {"native_index": index, "source_identity": "descriptor:" + str(index), "key_identity": key,
        "key_magic_raw": 0x4744624F if admitted else None, "key_full_id_raw": 123 if admitted else None,
        "admitted": admitted, "property_selection": "first_full_id_10_mapping" if admitted else None,
        "mapping_native_index": 0 if admitted else None, "property_identity": "mapped:first" if admitted else None,
        "property_block": shared if admitted else None, "reason": None}


def mapped_family(slot, *, empty=False):
    if empty:
        rows = []
    else:
        block = pc((51 + slot, 501 + slot))
        rows = ([mapped_row(0, "key:A", shared=block), mapped_row(1, "key:B", shared=block),
                 mapped_row(2, "key:A", shared=block), mapped_row(3, "key:C", admitted=False)]
                if slot == 0 else [mapped_row(0, "key:A", shared=block)])
    return {**availability(), "admitted": True, "count": len(rows), "array_present": bool(rows), "rows": rows}


def occurrence(index, *, second=False):
    return {"native_index": index, "requested_full_id_raw": 0xAA000001 - 2**32,
        "resolution_selection": "registry_full_id_8", "selected_full_id_raw": 0xAA000001 - 2**32,
        "object_identity": "table_owner:B" if second else "table_owner:A", "table_identity": "table:B" if second else "table:A",
        "direct_rows": [{"native_index": i, "pc": operand("direct:" + str(i), *((21 + i, 201 + i),) if second and i < 3 else ()
                        if second else ((11 + i, 101 + i),))} for i in range(4)],
        "nested_rows": [{"native_index": i, "mapped_family": mapped_family(i, empty=second)} for i in range(4)],
        "direct_ready": True, "mapped_ready": True, "ready": True, "reason": None}


def provider192_and2920850_source():
    """Reusable genuine main-normalizer input; importing this file runs no case."""
    lists = {}
    for name, count in (("list_168", 2), ("list_180", 1)):
        lists[name] = {**availability(), "direct_ready": True, "mapped_ready": True,
            "header_selection": "current_1c0_" + name[-3:], "default_init_guard_raw": None,
            "count_raw": count, "numeric_count": count, "array_present": True,
            "rows": [occurrence(i, second=name == "list_180") for i in range(count)]}
    leaf = {**availability(), "character_id": 29829, "current_land_present": True, "current_death_present": False,
        "rite": rite(), "mapped_default_guard_raw": 0,
        "provider_192": {**availability(), "provider_loaded": True, "provider_identity": "provider",
            "character_192_i16": 32767, "upper_i32": 10, "lower_i32": None, "selection": "provider_16a0",
            "selected_identity": "provider:upper", "magic_u32": 0x4744624F, "admitted": True,
            "pc": operand("provider:inline40", (10, Q))}, **lists}
    return {"status": "partial", "ready": False, "character_id": 29829, "branch_291e210": None,
            "reason": "other_person_stages_unobserved", FIELD: leaf}


def zero_lists(raw):
    raw[FIELD]["rite"] = rite(False)
    raw[FIELD]["mapped_default_guard_raw"] = None
    for family in FAMILIES[1:]:
        raw[FIELD][family].update(count_raw=0, numeric_count=0, array_present=None, rows=[])


def test_provider192_signed_order_physical_occurrences_mapping_independence_defaults_and_actor():
    raw = provider192_and2920850_source()
    before = deepcopy(raw)
    source = normalize_current_context_source_inputs(raw)
    requests = emit_all(source)
    assert raw == before and len(requests) == 25 and all(item.weight_q64 == Q for item in requests)
    assert [item.source_ordinal for item in requests] == [0] + [1] * 20 + [2] * 4
    assert [item.base_property_block["keys_u16"] for item in requests[1:11]] == [
        [11], [12], [13], [14], [51], [51], [51], [52], [53], [54]]
    assert [item.first_row_index for item in requests[1:21]] == [0] * 10 + [1] * 10
    assert requests[-1].base_property_block == pc()
    assert requests[1].base_property_block is source[FIELD]["list_168"]["rows"][0]["direct_rows"][0]["pc"]["property_block"]
    assert requests[6].base_property_block is source[FIELD]["list_168"]["rows"][0]["nested_rows"][0]["mapped_family"]["rows"][1]["property_block"]
    assert emit_descriptor(source, "list_168", 0, 0, 3) == ()
    assert source[FIELD]["list_168"]["rows"][0]["nested_rows"][0]["mapped_family"]["rows"][1]["mapping_native_index"] == 0

    for value, upper, lower, selection in (
        (-32768, 10, -5, "provider_16b0"),
        (0, 10, -5, "native_fallback_5d1e0b0"),
        (0, -10, None, "provider_16a0"),
    ):
        selected = provider192_and2920850_source()
        zero_lists(selected)
        selected[FIELD]["provider_192"].update(character_192_i16=value, upper_i32=upper, lower_i32=lower,
                                             selection=selection, pc=operand("provider:empty"))
        normalized = normalize_current_context_source_inputs(selected)
        assert emit_all(normalized)[0].base_property_block == pc()
    rejected = provider192_and2920850_source()
    rejected[FIELD]["provider_192"].update(magic_u32=0, admitted=False, pc=operand())
    assert len(emit_all(normalize_current_context_source_inputs(rejected))) == 24
    bad_lower = provider192_and2920850_source()
    bad_lower[FIELD]["provider_192"]["lower_i32"] = -5
    with pytest.raises(ValueError, match="undemanded lower"):
        normalize_current_context_source_inputs(bad_lower)

    partial = provider192_and2920850_source()
    leaf = partial[FIELD]
    leaf.update(availability(False, "independent_inputs_missing"))
    leaf["provider_192"].update(availability(False, "loaded_provider_null"))
    leaf["provider_192"].update(provider_loaded=False, provider_identity=None, character_192_i16=None,
        upper_i32=None, lower_i32=None, selection=None, selected_identity=None, magic_u32=None, admitted=None, pc=operand())
    branch = leaf["list_168"]
    branch.update(availability(False, "occurrence_partial"), direct_ready=False, mapped_ready=False)
    row = branch["rows"][0]
    row.update(direct_ready=False, mapped_ready=False, ready=False, reason="slots_partial")
    row["direct_rows"][2]["pc"].update(property_block=None, reason="direct_pc_unread")
    header = row["nested_rows"][0]["mapped_family"]
    header.update(availability(False, "selected_pc_pointer_null"))
    header["rows"][1].update(property_identity=None, property_block=None, reason="selected_pc_pointer_null")
    independent = normalize_current_context_source_inputs(partial)
    assert len(emit_family(independent, "list_180")) == 4
    assert emit_slot(independent, "list_168", 0, 0)[0].base_property_block == pc((11, 101))
    assert emit_slot(independent, "list_168", 0, 5)[0].base_property_block == pc((52, 502))
    assert emit_descriptor(independent, "list_168", 0, 0, 0)[0].base_property_block == pc((51, 501))
    assert emit_descriptor(independent, "list_168", 0, 0, 2)[0].base_property_block == pc((51, 501))
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_descriptor(independent, "list_168", 0, 0, 1)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_slot(independent, "list_168", 0, 2)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_all(independent)

    for guard in (None, 0, -1, 1):
        default = provider192_and2920850_source()
        zero_lists(default)
        leaf = default[FIELD]
        leaf.update(current_land_present=False, current_death_present=None)
        for family in FAMILIES[1:]:
            branch = leaf[family]
            modeled = guard in {0, -1}
            branch.update(header_selection="modeled_empty_default_5d67e60" if modeled else "inline_default_5d67e60",
                default_init_guard_raw=guard, count_raw=None if modeled or guard is None else 0,
                numeric_count=0 if modeled or guard == 1 else None, array_present=None, rows=[])
            if guard is None:
                branch.update(availability(False, "default_init_guard_unread"), direct_ready=False, mapped_ready=False)
        if guard is None:
            leaf.update(availability(False, "default_init_guard_unread"))
        normalized = normalize_current_context_source_inputs(default)
        assert len(emit_family(normalized, "provider_192")) == 1
        if guard is not None:
            assert len(emit_all(normalized)) == 1
        else:
            with pytest.raises(ValueError, match="Required native input unavailable"):
                emit_all(normalized)

    mapped_default = provider192_and2920850_source()
    leaf = mapped_default[FIELD]
    leaf.update(availability(False, "consumed_default_uninitialized"))
    branch = leaf["list_168"]
    branch.update(availability(False, "consumed_default_uninitialized"), mapped_ready=False)
    row = branch["rows"][0]
    row.update(mapped_ready=False, ready=False, reason="consumed_default_uninitialized")
    header = row["nested_rows"][0]["mapped_family"]
    header.update(availability(False, "consumed_default_uninitialized"))
    header["rows"][1].update(key_magic_raw=0, key_full_id_raw=None,
        property_selection="inline_nested_mapped_default_5dc21b0", mapping_native_index=None,
        property_identity="uninitialized:inline", property_block=None, reason="consumed_default_uninitialized")
    normalized = normalize_current_context_source_inputs(mapped_default)
    assert len(emit_slot(normalized, "list_168", 0, 0)) == 1
    assert len(emit_descriptor(normalized, "list_168", 0, 0, 0)) == 1
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_descriptor(normalized, "list_168", 0, 0, 1)

    missing_guard = provider192_and2920850_source()
    leaf = missing_guard[FIELD]
    leaf.update(availability(False, "mapped_guard_unread"), mapped_default_guard_raw=None)
    branch = leaf["list_168"]
    branch.update(availability(False, "mapped_guard_unread"), mapped_ready=False)
    for row in branch["rows"]:
        row.update(mapped_ready=False, ready=False, reason="mapped_guard_unread")
        for nested in row["nested_rows"]:
            nested["mapped_family"].update(availability(False, "mapped_guard_unread"))
    normalized = normalize_current_context_source_inputs(missing_guard)
    assert len(emit_slot(normalized, "list_168", 0, 3)) == 1 and len(emit_family(normalized, "list_180")) == 4
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_descriptor(normalized, "list_168", 0, 0, 0)

    negative = provider192_and2920850_source()
    zero_lists(negative)
    negative[FIELD].update(availability(False, "negative_list_count"))
    negative[FIELD]["list_168"].update(availability(False, "negative_list_count"), count_raw=-1,
                                      numeric_count=-1, direct_ready=False, mapped_ready=False)
    normalized = normalize_current_context_source_inputs(negative)
    assert emit_family(normalized, "list_180") == ()
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_family(normalized, "list_168")
    null_registry = provider192_and2920850_source()
    for family in FAMILIES[1:]:
        for row in null_registry[FIELD][family]["rows"]:
            row.update(requested_full_id_raw=None, resolution_selection="native_fallback", selected_full_id_raw=None)
    assert len(emit_all(normalize_current_context_source_inputs(null_registry))) == 25
    wrong_actor = provider192_and2920850_source()
    wrong_actor[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="character"):
        normalize_current_context_source_inputs(wrong_actor)
