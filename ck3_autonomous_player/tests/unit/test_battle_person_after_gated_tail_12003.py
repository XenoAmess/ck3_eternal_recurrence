from copy import deepcopy
import hashlib

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_after_gated_tail_contract import (
    emit_after_gated_tail_family_requests_from_current_source_inputs_12003 as emit_family,
    emit_after_gated_tail_requests_from_current_source_inputs_12003 as emit_all,
)
from xar_autoplayer.simulation.battle_person_after_gated_tail_12003 import (
    _DAY_TABLE, _MONTH_TABLE, completed_after_gated_months_12003,
)

FIELD = "after_gated_tail_326a8e0_2920310"
FAMILIES = ("composition_326a8e0", "current_1b8_court_positions", "current_1c0_court_positions", "related_court_positions")
Q = 100000


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def pc(*rows):
    return {"keys_count": len(rows), "values_count": len(rows), "keys_u16": [key for key, _ in rows],
            "values_q64": [value for _, value in rows], "reason": None}


def operand(identity=None, *rows):
    return {"property_identity": identity, "property_block": pc(*rows) if identity else None, "reason": None}


def date(raw=None, day=None, month=None, year=None):
    return {"raw_i32": raw, "day_cache_i8": day, "month_cache_i8": month, "year_cache_i16": year}


def named(kind="unconsumed", value=None):
    known = kind in {"literal", "known_zero"}
    return {**availability(known, None if known else "not_consumed" if kind == "unconsumed" else "dynamic_tree_requires_current_result"),
        "slot_offset": 0, "entry_identity": "nested_named" if kind != "unconsumed" else None,
        "tree_present": None if kind == "unconsumed" else kind == "dynamic_tree_requires_current_result",
        "tree_identity": "nested_tree" if kind == "dynamic_tree_requires_current_result" else None,
        "fixed_flag_u8": 3 if kind == "literal" else 0 if kind == "known_zero" else None,
        "raw_fixed_q64": value if kind == "literal" else None, "value_q64": value if kind == "literal" else 0 if kind == "known_zero" else None,
        "kind": kind}


def rule(value=None, *, mode=None):
    return {**availability(mode == 0, None if mode == 0 else "not_consumed"), "mode_raw": mode,
        "tree_present": None, "tree_identity": None, "named_present": None, "named": named(),
        "target_count_raw": None, "raw_98_q64": value, "value_q64": value, "selection": "mode_zero_raw98" if mode == 0 else None}


def kind(ready=True):
    return {**availability(ready, None if ready else "not_consumed"), "position_120_raw": None, "position_124_raw": None,
        "owner_selection": "native_fallback" if ready else None, "owner_identity": "character:29829" if ready else None,
        "owner_full_id_raw": 29829 if ready else None, "played_count_raw": 1 if ready else None,
        "played_full_ids": [29829] if ready else None, "owner_played": True if ready else None, "raw_a0_u8": None,
        "threshold_count_raw": 4 if ready else None, "thresholds_i32": [0, 1, 3, 5] if ready else None,
        "rule": rule(2 * Q, mode=0) if ready else rule(), "kind_raw": 2 if ready else None}


def resolution():
    return {"native_index": 0, "requested_full_id_raw": None, "registry_present": None, "capacity_u32": None,
        "indexed_pointer_present": None, "indexed_full_id_raw": None, "selection": None, "object_identity": None,
        "magic_raw": None, "full_id_raw": None, "admitted": None, "reason": None}


def related(active=False):
    result = {"carrier_present": None, "attempts": [], "self_full_id_raw": None, "helper_return_full_id_raw": None,
        "caller_selection": None, "caller_identity": None, "caller_requested_full_id_raw": None, "caller_full_id_raw": None,
        "caller_magic_raw": None, "caller_admitted": None, "land_present": None, "selected_present": None, "reason": None}
    if active:
        full_id = 0xAA000001 - 2**32
        row = {**resolution(), "requested_full_id_raw": full_id, "registry_present": True, "capacity_u32": 2,
               "indexed_pointer_present": True, "indexed_full_id_raw": full_id, "selection": "indexed_full_id",
               "object_identity": "related_character", "magic_raw": 0x43686172, "full_id_raw": full_id, "admitted": True}
        result.update(carrier_present=True, attempts=[row], helper_return_full_id_raw=full_id,
            caller_selection="indexed_full_id", caller_identity="related_character", caller_requested_full_id_raw=full_id,
            caller_full_id_raw=full_id, caller_magic_raw=0x43686172, caller_admitted=True, land_present=True)
    return result


def selectors():
    return {"selector_a_selection": "registry_full_id_8", "selector_a_identity": "selector:A",
        "selector_b_selection": "registry_full_id_10", "selector_b_identity": "selector:B",
        "selector_a_key_raw": 7, "selector_b_key_raw": -1, "selector_a_membership_count": 1,
        "selector_b_primary_count": 1, "selector_b_nested_count": 0,
        "selector_a_keys_i32": [7], "selector_b_primary_keys_i32": [-1], "selector_b_nested_keys": [], "reason": None}


def composite(identity):
    def conditional(key, amount):
        return {"native_index": 0, "key_i32": key, "admitted": True, "property_identity": identity + ":" + str(key),
                "property_block": pc((5, amount)), "reason": None}
    return {"role": "base", "track_index": None, "level_index": None, "property_identity": identity,
        "base_property_block": pc((5, Q), (65535, -Q)), "conditional_b_count": 1, "conditional_b_rows": [conditional(-1, 2 * Q)],
        "conditional_a_count": 1, "conditional_a_rows": [conditional(7, 3 * Q)], "ready": True, "reason": None}


def position(index, family):
    out = {"native_index": index, "requested_full_id_raw": None, "position_selection": "native_fallback",
        "position_identity": "position:" + str(family), "position_full_id_raw": None,
        "definition_identity": "definition:" + str(family), "other_definition_identity": "other:" + str(family),
        "other_magic_raw": 0x4744624F, "other_admitted": True, "base_pc": operand("base:" + str(family)),
        "tier_pc": operand(), "composite_group": composite("composite:" + str(family)) if family < 3 else None,
        "kind": kind(family > 1), "other_base_pc": operand("other_base:" + str(family)), "other_tier_pc": operand(),
        "other_kind": kind(family > 1), "definition_pair_probes": [], "definition_pair_admitted": None,
        "other_pair_probes": [], "other_pair_admitted": None, "ready": True, "reason": None}
    if family == 2:
        out.update(base_pc=operand("base:2", (6, Q)), tier_pc=operand("tier:2", (7, 2 * Q)),
                   other_base_pc=operand("other_base:2", (8, 3 * Q)), other_tier_pc=operand("other_tier:2", (9, 4 * Q)))
    if family == 3:
        out.update(base_pc=operand("base:3", (10, Q)), tier_pc=operand("tier:3"),
                   other_tier_pc=operand("other_tier:3"), definition_pair_probes=[{"native_index": 0, "count_raw": 1}],
                   definition_pair_admitted=True, other_pair_probes=[{"native_index": 0, "count_raw": 0}, {"native_index": 1, "count_raw": 1}],
                   other_pair_admitted=True)
    return out


def court_list(family):
    count = 2 if family == 1 else 1
    return {**availability(), "owner_present": True, "header_selection": ("current_1b8_d0", "current_1c0_3b8", "related_1c0_3b8")[family - 1],
            "count_raw": count, "numeric_count": count, "array_present": True, "default_init_guard_raw": None,
            "related": related(family == 3), "rows": [position(i, family) for i in range(count)]}


def rowset(month=False):
    thresholds = [0, 99, 2 if month else 1]
    return {**availability(), "count_raw": 3, "array_present": True, "rows": [
        {"native_index": i, "threshold_raw": threshold, "admitted": i != 1,
         "pc": operand(("month" if month else "level") + ":" + str(i), (1, Q)) if i != 1 else operand(),
         "reason": None} for i, threshold in enumerate(thresholds)]}


def after_gated_source():
    """Real normalizer input shape for the separately owned stage-chain case."""
    composition = {**availability(), "global_flag_u8": 0x20, "global_bit20": True,
        "current_land_present": True, "current_selected_present": True, "receiver_selection": "current_458_178",
        "admitted": True, "related": related(), "owner_mode": True, "definition_identity": "composition_definition",
        "level_raw": 1, "handle_date": date(100, 0, 1, 10), "fifth_date": date(100),
        "current_date": date(200, 0, 3, 10), "chosen_date_selection": "handle", "completed_months_raw": 2,
        "level_rows": rowset(), "month_rows": rowset(True)}
    leaf = {**availability(), "character_id": 29829, "current_land_present": True, "selector_inputs": selectors(),
            FAMILIES[0]: composition, **{FAMILIES[i]: court_list(i) for i in range(1, 4)}}
    return {"status": "partial", "ready": False, "character_id": 29829, "branch_291e210": None,
            "reason": "other_person_stages_unobserved", FIELD: leaf}


def test_after_gated_tail_calendar_literal_precedence_order_empty_pairs_independence_and_actor():
    raw = after_gated_source()
    before = deepcopy(raw)
    source = normalize_current_context_source_inputs(raw)
    requests = emit_all(source)
    assert raw == before and len(requests) == 16 and [r.weight_q64 for r in requests] == [Q] * 16
    assert requests[0].base_property_block == pc((1, 4 * Q))
    assert [r.source_ordinal for r in requests] == [0] + [1] * 6 + [2] * 5 + [3] * 4
    assert requests[1].base_property_block == pc() and requests[3].base_property_block == pc()
    assert requests[2].base_property_block == pc((5, 6 * Q), (65535, -Q))
    assert [r.first_row_index for r in requests[1:7]] == [0, 0, 0, 1, 1, 1]
    assert requests[1].base_property_block is source[FIELD][FAMILIES[1]]["rows"][0]["base_pc"]["property_block"]
    assert [r.base_property_block["keys_count"] for r in requests[-4:]] == [1, 0, 0, 0]

    assert len(_DAY_TABLE) == len(_MONTH_TABLE) == 365
    assert hashlib.sha256(_DAY_TABLE).hexdigest() == "49cfa7734c595821c26db19fac8d0427fa12adc3e8988e04e0d94198d8f35517"
    assert hashlib.sha256(_MONTH_TABLE).hexdigest() == "218539a9f584e576a0912771d97ac39c5042fc9169e2b5d250069a88d1478f0a"
    assert completed_after_gated_months_12003(date(43800000 + 396 * 24, -1, -1, -1), date(43800000, -1, -1, -1)) == 13
    assert completed_after_gated_months_12003(date(43800000 - 24, -1, -1, -1), date(43800000, -1, -1, -1)) == 11
    tie = after_gated_source()
    tie[FIELD][FAMILIES[0]]["fifth_date"] = date(100, 0, 0, 10)
    assert normalize_current_context_source_inputs(tie)[FIELD][FAMILIES[0]]["completed_months_raw"] == 2

    literal = after_gated_source()
    for k in ("kind", "other_kind"):
        item = literal[FIELD][FAMILIES[2]]["rows"][0][k]
        item["rule"] = rule(-Q, mode=0)
        item["kind_raw"] = 0
    assert normalize_current_context_source_inputs(literal)[FIELD][FAMILIES[2]]["rows"][0]["kind"]["kind_raw"] == 0
    bad_precedence = deepcopy(literal)
    bad_precedence[FIELD][FAMILIES[2]]["rows"][0]["kind"]["rule"]["tree_present"] = True
    with pytest.raises(ValueError, match="mode0 literal"):
        normalize_current_context_source_inputs(bad_precedence)

    for nested_kind, value, expected_kind in (("known_zero", None, 1), ("literal", -Q, 0)):
        nested = after_gated_source()
        for key in ("kind", "other_kind"):
            item = nested[FIELD][FAMILIES[2]]["rows"][0][key]
            item["rule"] = {**availability(), "mode_raw": 1, "tree_present": False, "tree_identity": None,
                "named_present": True, "named": named(nested_kind, value), "target_count_raw": None, "raw_98_q64": None,
                "value_q64": 0 if nested_kind == "known_zero" else value, "selection": "nested_named"}
            item["kind_raw"] = expected_kind
        assert len(emit_all(normalize_current_context_source_inputs(nested))) == 16

    ordinary = after_gated_source()
    for key in ("kind", "other_kind"):
        item = ordinary[FIELD][FAMILIES[2]]["rows"][0][key]
        item.update(owner_played=False, played_full_ids=[29830], raw_a0_u8=250, threshold_count_raw=None,
                    thresholds_i32=None, rule=rule(), kind_raw=250)
    assert normalize_current_context_source_inputs(ordinary)[FIELD][FAMILIES[2]]["rows"][0]["kind"]["kind_raw"] == 250
    short = after_gated_source()
    for key in ("kind", "other_kind"):
        item = short[FIELD][FAMILIES[2]]["rows"][0][key]
        item.update(threshold_count_raw=-1, thresholds_i32=None, rule=rule(), kind_raw=4)
    assert len(emit_all(normalize_current_context_source_inputs(short))) == 16

    dynamic = after_gated_source()
    leaf = dynamic[FIELD]
    leaf.update(availability(False, "kind_missing"))
    branch = leaf[FAMILIES[2]]
    branch.update(availability(False, "definition_600_dynamic_fixed_result"))
    row = branch["rows"][0]
    row.update(ready=False, reason="definition_600_dynamic_fixed_result")
    for key in ("kind", "other_kind"):
        item = row[key]
        item.update(availability(False, "definition_600_dynamic_fixed_result"))
        item.update(kind_raw=None, rule={**availability(False, "definition_600_dynamic_fixed_result"),
            "mode_raw": 1, "tree_present": False, "tree_identity": None, "named_present": False, "named": named(),
            "target_count_raw": 1, "raw_98_q64": None, "value_q64": None, "selection": "dynamic_targets"})
    row["tier_pc"] = operand()
    row["other_tier_pc"] = operand()
    normalized_dynamic = normalize_current_context_source_inputs(dynamic)
    assert [len(emit_family(normalized_dynamic, family)) for family in (FAMILIES[0], FAMILIES[1], FAMILIES[3])] == [1, 6, 4]
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_all(normalized_dynamic)

    disabled = after_gated_source()
    comp = disabled[FIELD][FAMILIES[0]]
    comp.update(global_flag_u8=0, global_bit20=False, current_land_present=None, current_selected_present=None,
        receiver_selection="skipped", admitted=False, owner_mode=None, definition_identity=None, level_raw=None,
        handle_date=date(), fifth_date=date(), current_date=date(), chosen_date_selection=None, completed_months_raw=None)
    for key in ("level_rows", "month_rows"):
        comp[key] = {**availability(), "count_raw": None, "array_present": None, "rows": []}
    assert len(emit_all(normalize_current_context_source_inputs(disabled))) == 15

    for guard in (0, -1, 1):
        default = after_gated_source()
        comp = default[FIELD][FAMILIES[0]]
        comp.update(level_raw=None, handle_date=date(), fifth_date=date(), current_date=date(),
                    chosen_date_selection=None, completed_months_raw=None)
        for key in ("level_rows", "month_rows"):
            comp[key] = {**availability(), "count_raw": 0, "array_present": None, "rows": []}
        branch = default[FIELD][FAMILIES[3]]
        branch.update(owner_present=False, header_selection="inline_default_54e7220" if guard == 1 else "modeled_empty_default_54e7220",
            default_init_guard_raw=guard, count_raw=0 if guard == 1 else None, numeric_count=0, array_present=None, rows=[])
        branch["related"].update(land_present=False)
        result = normalize_current_context_source_inputs(default)
        assert emit_family(result, FAMILIES[0])[0].base_property_block == pc()
        assert emit_family(result, FAMILIES[3]) == ()

    all_empty = after_gated_source()
    row = all_empty[FIELD][FAMILIES[3]]["rows"][0]
    row.update(definition_pair_probes=[{"native_index": i, "count_raw": 0} for i in range(6)], definition_pair_admitted=False,
               other_magic_raw=0, other_admitted=False, other_pair_probes=[], other_pair_admitted=None,
               base_pc=operand(), tier_pc=operand(), other_base_pc=operand(), other_tier_pc=operand(),
               kind=kind(False), other_kind=kind(False))
    assert emit_family(normalize_current_context_source_inputs(all_empty), FAMILIES[3]) == ()

    wrong_actor = after_gated_source()
    wrong_actor[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="character"):
        normalize_current_context_source_inputs(wrong_actor)
