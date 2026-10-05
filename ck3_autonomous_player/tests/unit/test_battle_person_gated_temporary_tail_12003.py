from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_gated_temporary_tail_contract import (
    emit_gated_temporary_tail_family_requests_from_current_source_inputs_12003 as emit_family,
    emit_gated_temporary_tail_requests_from_current_source_inputs_12003 as emit_all,
)

FIELD = "gated_temporary_tail_291c7a7"
Q = 100000


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def pc(*pairs):
    return {"keys_count": len(pairs), "values_count": len(pairs),
            "keys_u16": [key for key, _ in pairs], "values_q64": [value for _, value in pairs], "reason": None}


def named(slot, *, value=None, kind="unconsumed", flag=3):
    ready = kind in {"literal", "known_zero"}
    return {**availability(ready, None if ready else "not_consumed" if kind == "unconsumed" else kind),
            "slot_offset": slot, "entry_identity": "named:" + str(slot) if kind != "unconsumed" else None,
            "tree_present": None if kind == "unconsumed" else kind != "literal" and kind != "known_zero",
            "tree_identity": "tree:dynamic" if kind == "dynamic_tree_requires_current_result" else None,
            "fixed_flag_u8": flag if kind == "literal" else 0 if kind == "known_zero" else None,
            "raw_fixed_q64": value if kind == "literal" else None,
            "value_q64": value if kind == "literal" else 0 if kind == "known_zero" else None, "kind": kind}


def blank_resolution():
    return {"native_index": 0, "requested_full_id_raw": None, "registry_present": None, "capacity_u32": None,
            "indexed_pointer_present": None, "indexed_full_id_raw": None, "selection": None, "object_identity": None,
            "magic_raw": None, "full_id_raw": None, "admitted": None, "reason": None}


def unused_related():
    return {"carrier_present": None, "attempts": [], "self_full_id_raw": None, "helper_return_full_id_raw": None,
            "caller": blank_resolution(), "land_present": None, "selected_present": None, "reason": None}


def prefix(selector=None, *, rows=None, header=None, ready=True, reason=None):
    return {**availability(ready, reason), "selector_raw": selector,
            "native_prefix_count": None if selector is None else (selector + 1 + 2**31) % 2**32 - 2**31,
            "header_count": header, "array_present": True if rows else None, "rows": [] if rows is None else rows}


def prefix_rows(block, identity):
    return [{"native_index": i, "definition_identity": identity, "magic_raw": 0x4744624F, "admitted": True,
             "property_identity": identity + ":40", "property_block": block, "reason": None} for i in range(2)]


def gated_temporary_source():
    """Source-shaped current frame, usable by the separate stage-joining lane."""
    a = prefix_rows(pc((1, Q), (65535, -2 * Q)), "definition:A")
    b = prefix_rows(pc((2, -Q), (65535, 0)), "definition:B")
    leaf = {**availability(), "character_id": 29829, "global_flag_u8": 0x20, "global_bit20": True,
            "current_land_present": True, "current_selected_present": True, "temporary_admitted": True,
            "selected_ec_raw": 7, "selector_global_raw": 7, "selected_e8_raw": None, "selected_f8_raw": 1,
            "refresh_168": {**availability(), "source": named(0x168, value=-50000, kind="literal"),
                "minimum_q64": 0, "maximum_q64": None, "clamped_q64": 0, "threshold_count": 3,
                "threshold_array_present": True, "thresholds_consumed_q64": [0], "fresh_rank_raw": 0},
            "prefix_1398": prefix(1, rows=a, header=2),
            "delta_prefix_1420_14a8": {**availability(), "delta_raw": 1, "absolute_delta_raw": 1,
                "header_selection": "provider_1420", "weight_source": named(0x170, value=-250000, kind="literal"),
                "prefix": prefix(1, rows=b, header=2)},
            "list": {**availability(), "selection": "current_A20", "related": unused_related(), "count_raw": 2,
                "array_present": True, "rows": [{"native_index": i, "property_identity": "list:duplicate:a20",
                    "property_block": pc((3, 0)), "reason": None} for i in range(2)]}}
    return {"status": "partial", "ready": False, "character_id": 29829,
            "branch_291e210": None, "reason": "other_person_stages_unobserved", FIELD: leaf}


def skip_temporaries(leaf):
    leaf.update(temporary_admitted=False, selected_ec_raw=None, selector_global_raw=None,
                selected_e8_raw=None, selected_f8_raw=None)
    leaf["refresh_168"] = {**availability(), "source": named(0x168), "minimum_q64": None, "maximum_q64": None,
        "clamped_q64": None, "threshold_count": None, "threshold_array_present": None,
        "thresholds_consumed_q64": None, "fresh_rank_raw": None}
    leaf["prefix_1398"] = prefix()
    leaf["delta_prefix_1420_14a8"] = {**availability(), "delta_raw": None, "absolute_delta_raw": None,
        "header_selection": None, "weight_source": named(0x170), "prefix": prefix()}


def set_partial(branch, reason):
    branch.update(availability(False, reason))


def test_gated_temporary_tail_literal_fold_outer_empty_independent_sources_and_real_actor_join():
    raw = gated_temporary_source()
    before = deepcopy(raw)
    source = normalize_current_context_source_inputs(raw)
    requests = emit_all(source)
    assert raw == before and source["ready"] is False and source[FIELD]["ready"] is True
    assert [r.source_ordinal for r in requests] == [0, 1, 2, 2]
    assert [r.weight_q64 for r in requests] == [Q] * 4
    assert requests[0].base_property_block == pc((1, 2 * Q), (65535, -2 * Q))
    assert requests[1].base_property_block == pc((2, 5 * Q), (65535, 0))
    assert [r.definition_identity for r in requests[2:]] == ["list:duplicate:a20"] * 2
    assert requests[2].base_property_block is source[FIELD]["list"]["rows"][0]["property_block"]
    assert requests[3].base_property_block is source[FIELD]["list"]["rows"][1]["property_block"]

    zero = gated_temporary_source()
    refresh = zero[FIELD]["refresh_168"]
    refresh["source"] = named(0x168, kind="known_zero")
    refresh["maximum_q64"] = 100000
    zero[FIELD]["delta_prefix_1420_14a8"]["weight_source"] = named(0x170, kind="known_zero")
    zero_requests = emit_all(normalize_current_context_source_inputs(zero))
    assert zero_requests[1].base_property_block == pc((2, 0), (65535, 0))
    assert zero_requests[1].base_property_block["keys_count"] == 2

    delta_zero = gated_temporary_source()
    leaf = delta_zero[FIELD]
    leaf["selected_f8_raw"] = 0
    leaf["prefix_1398"] = prefix(0, rows=leaf["prefix_1398"]["rows"][:1], header=2)
    leaf["delta_prefix_1420_14a8"] = {**availability(), "delta_raw": 0, "absolute_delta_raw": None,
        "header_selection": "zero_delta", "weight_source": named(0x170), "prefix": prefix()}
    delta_zero_requests = emit_all(normalize_current_context_source_inputs(delta_zero))
    assert len(delta_zero_requests) == 4 and delta_zero_requests[1].base_property_block == pc()

    for selected, expected_header in ((2**31 - 1, "provider_1420"), (-2**31, "provider_14a8")):
        bounds = gated_temporary_source()
        leaf = bounds[FIELD]
        leaf["selected_f8_raw"] = selected
        leaf["prefix_1398"] = prefix(selected)
        leaf["delta_prefix_1420_14a8"] = {**availability(), "delta_raw": selected, "absolute_delta_raw": selected,
            "header_selection": expected_header, "weight_source": named(0x170), "prefix": prefix(selected)}
        leaf["list"].update(count_raw=0, array_present=None, rows=[])
        empty_requests = emit_all(normalize_current_context_source_inputs(bounds))
        assert len(empty_requests) == 2 and [r.base_property_block for r in empty_requests] == [pc(), pc()]

    empty_keys = gated_temporary_source()
    leaf = empty_keys[FIELD]
    for row in leaf["delta_prefix_1420_14a8"]["prefix"]["rows"]:
        row["property_block"] = pc()
    leaf["delta_prefix_1420_14a8"]["weight_source"] = named(0x170)
    assert emit_all(normalize_current_context_source_inputs(empty_keys))[1].base_property_block == pc()

    dynamic = gated_temporary_source()
    leaf = dynamic[FIELD]
    set_partial(leaf, "temporary_delta_missing")
    leaf["refresh_168"] = {**availability(False, "dynamic_tree_requires_current_result"),
        "source": named(0x168, kind="dynamic_tree_requires_current_result"),
        "minimum_q64": None, "maximum_q64": None, "clamped_q64": None, "threshold_count": None,
        "threshold_array_present": None, "thresholds_consumed_q64": None, "fresh_rank_raw": None}
    leaf["delta_prefix_1420_14a8"] = {**availability(False, "fresh_rank_missing"), "delta_raw": None,
        "absolute_delta_raw": None, "header_selection": None, "weight_source": named(0x170),
        "prefix": prefix(ready=False, reason="fresh_rank_missing")}
    normalized_dynamic = normalize_current_context_source_inputs(dynamic)
    assert len(emit_family(normalized_dynamic, "prefix_1398")) == 1
    assert len(emit_family(normalized_dynamic, "list")) == 2
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_all(normalized_dynamic)
    bad_tree = deepcopy(dynamic)
    bad_tree[FIELD]["refresh_168"]["source"]["fixed_flag_u8"] = 3
    with pytest.raises(ValueError, match="tree takes precedence"):
        normalize_current_context_source_inputs(bad_tree)

    missing_weight = gated_temporary_source()
    leaf = missing_weight[FIELD]
    set_partial(leaf, "temporary_weight_missing")
    branch = leaf["delta_prefix_1420_14a8"]
    set_partial(branch, "dynamic_tree_requires_current_result")
    branch["weight_source"] = named(0x170, kind="dynamic_tree_requires_current_result")
    normalized_weight = normalize_current_context_source_inputs(missing_weight)
    assert len(emit_family(normalized_weight, "prefix_1398")) == 1
    assert len(emit_family(normalized_weight, "list")) == 2
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_family(normalized_weight, "delta_prefix_1420_14a8")

    disabled = gated_temporary_source()
    leaf = disabled[FIELD]
    leaf.update(global_flag_u8=0, global_bit20=False, current_land_present=None, current_selected_present=None)
    skip_temporaries(leaf)
    leaf["list"] = {**availability(), "selection": "skipped_bit20", "related": unused_related(),
                    "count_raw": None, "array_present": None, "rows": []}
    assert emit_all(normalize_current_context_source_inputs(disabled)) == ()

    related_frame = gated_temporary_source()
    leaf = related_frame[FIELD]
    leaf.update(current_land_present=False, current_selected_present=False)
    skip_temporaries(leaf)
    identity = 0xAA000001 - 2**32
    first = {**blank_resolution(), "native_index": 0, "requested_full_id_raw": 5, "registry_present": True,
             "capacity_u32": 2, "selection": "out_of_capacity", "admitted": False}
    second = {**blank_resolution(), "native_index": 1, "requested_full_id_raw": identity, "registry_present": True,
              "capacity_u32": 2, "indexed_pointer_present": True, "indexed_full_id_raw": identity,
              "selection": "indexed_full_id", "object_identity": "related:character",
              "magic_raw": 0x43686172, "full_id_raw": identity, "admitted": True}
    related = {"carrier_present": True, "attempts": [first, second], "self_full_id_raw": None,
               "helper_return_full_id_raw": identity, "caller": {**second, "native_index": 0},
               "land_present": True, "selected_present": True, "reason": None}
    leaf["list"] = {**availability(), "selection": "related_BE0", "related": related, "count_raw": 2,
        "array_present": True, "rows": [{"native_index": i, "property_identity": "related:be0",
                                       "property_block": pc((4, -7 * Q)), "reason": None} for i in range(2)]}
    related_requests = emit_all(normalize_current_context_source_inputs(related_frame))
    assert len(related_requests) == 2 and [r.source_ordinal for r in related_requests] == [2, 2]
    assert [r.source_name for r in related_requests] == ["291c9c3_related_be0"] * 2
    assert [r.base_property_block["values_q64"] for r in related_requests] == [[-7 * Q]] * 2

    wrong_actor = gated_temporary_source()
    wrong_actor[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="character"):
        normalize_current_context_source_inputs(wrong_actor)
