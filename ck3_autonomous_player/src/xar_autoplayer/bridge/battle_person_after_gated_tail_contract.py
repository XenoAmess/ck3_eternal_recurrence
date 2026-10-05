"""Strict readonly numeric inputs for the source-closed after-gated segment."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _numbers, _properties, _properties_ready, _string,
)
from .battle_person_gated_temporary_tail_contract import _named, _resolution
from .battle_person_trait_stage_291d460_contract import _group, _keyset
from ..simulation.battle_person_after_gated_tail_12003 import (
    FAMILIES_AFTER_GATED_12003, completed_after_gated_months_12003,
    definition_600_literal_value_12003, emit_after_gated_tail_family_requests_12003,
    emit_after_gated_tail_requests_12003, quantized_court_position_kind_12003,
)

_FIELD = "after_gated_tail_326a8e0_2920310"
_SELECTOR_STRINGS = ("selector_a_selection", "selector_a_identity", "selector_b_selection", "selector_b_identity")
_SELECTOR_WORDS = ("selector_a_key_raw", "selector_b_key_raw", "selector_a_membership_count",
                   "selector_b_primary_count", "selector_b_nested_count")


def _start(value, field, fields):
    raw = _dict(value, field, {"status", "ready", "reason", *fields})
    status, ready, reason = _availability(raw, field)
    return raw, {"status": status, "ready": ready, "reason": reason}


def _words(raw, out, field, keys, bits=32, unsigned=False):
    for key in keys:
        out[key] = _number(raw[key], field + "." + key, bits, unsigned=unsigned)


def _strings(raw, out, field, keys):
    for key in keys:
        out[key] = _string(raw[key], field + "." + key, optional=True)


def _bools(raw, out, field, keys):
    for key in keys:
        out[key] = _boolean(raw[key], field + "." + key, optional=True)


def _pc(value, field):
    raw = _dict(value, field, {"property_identity", "property_block", "reason"})
    return {"property_identity": _string(raw["property_identity"], field + ".property_identity", optional=True),
            "property_block": _properties(raw["property_block"], field + ".property_block"),
            "reason": _string(raw["reason"], field + ".reason", optional=True)}


def _pc_ready(value):
    return (value["property_identity"] is not None and value["reason"] is None
            and _properties_ready(value["property_block"]) and value["property_block"]["reason"] is None)


def _date(value, field):
    raw = _dict(value, field, {"raw_i32", "day_cache_i8", "month_cache_i8", "year_cache_i16"})
    return {key: _number(raw[key], field + "." + key, bits) for key, bits in
            (("raw_i32", 32), ("day_cache_i8", 8), ("month_cache_i8", 8), ("year_cache_i16", 16))}


def _selectors(value, field):
    raw = _dict(value, field, {*_SELECTOR_STRINGS, *_SELECTOR_WORDS,
        "selector_a_keys_i32", "selector_b_primary_keys_i32", "selector_b_nested_keys", "reason"})
    out = {}
    _strings(raw, out, field, (*_SELECTOR_STRINGS, "reason"))
    _words(raw, out, field, _SELECTOR_WORDS)
    for key in ("selector_a_keys_i32", "selector_b_primary_keys_i32"):
        out[key] = _numbers(raw[key], field + "." + key, 32)
    if not isinstance(raw["selector_b_nested_keys"], list):
        raise ValueError(field + ".selector_b_nested_keys must be a list")
    out["selector_b_nested_keys"] = [_keyset(row, f"{field}.selector_b_nested_keys[{i}]", i)
                                   for i, row in enumerate(raw["selector_b_nested_keys"])]
    return out


def _related(value, field, current_land, check_magic):
    fields = {"carrier_present", "attempts", "self_full_id_raw", "helper_return_full_id_raw",
        "caller_selection", "caller_identity", "caller_requested_full_id_raw", "caller_full_id_raw",
        "caller_magic_raw", "caller_admitted", "land_present", "selected_present", "reason"}
    raw = _dict(value, field, fields)
    out = {}
    _bools(raw, out, field, ("carrier_present", "caller_admitted", "land_present", "selected_present"))
    _strings(raw, out, field, ("caller_selection", "caller_identity", "reason"))
    _words(raw, out, field, ("self_full_id_raw", "helper_return_full_id_raw", "caller_requested_full_id_raw", "caller_full_id_raw"))
    _words(raw, out, field, ("caller_magic_raw",), 32, True)
    if not isinstance(raw["attempts"], list) or len(raw["attempts"]) > 2:
        raise ValueError(field + " attempts must be CC then C8 prefix")
    out["attempts"] = [_resolution(row, f"{field}.attempts[{i}]", i, True) for i, row in enumerate(raw["attempts"])]
    returned = None
    if out["carrier_present"] is False:
        if out["attempts"] or out["self_full_id_raw"] is not None:
            raise ValueError(field + " absent carrier contains undemanded candidates")
        returned = -1
    elif out["carrier_present"] is True:
        for i, row in enumerate(out["attempts"]):
            if row["admitted"] is True:
                if i != len(out["attempts"]) - 1:
                    raise ValueError(field + " continued after admitted candidate")
                returned = row["requested_full_id_raw"]
                break
            if row["admitted"] is None or row["reason"] is not None:
                break
        else:
            if len(out["attempts"]) == 2:
                returned = out["self_full_id_raw"] if current_land else -1 if current_land is False else None
    if out["helper_return_full_id_raw"] != returned:
        raise ValueError(field + " helper full ID disagrees")
    selection = out["caller_selection"]
    if selection not in {None, "indexed_full_id", "native_fallback"}:
        raise ValueError(field + " caller selection invalid")
    if out["caller_requested_full_id_raw"] not in {None, returned}:
        raise ValueError(field + " caller requested a different full ID")
    if selection == "indexed_full_id" and (returned is None or out["caller_full_id_raw"] != returned):
        raise ValueError(field + " indexed caller full generation disagrees")
    if check_magic:
        magic, full_id = out["caller_magic_raw"], out["caller_full_id_raw"]
        admitted = None if magic is None else False if magic != 0x43686172 else None if full_id is None else full_id != -1
        if out["caller_admitted"] != admitted:
            raise ValueError(field + " caller Character gate disagrees")
    elif out["caller_magic_raw"] is not None:
        raise ValueError(field + " composition caller has no Character magic gate")
    if out["land_present"] is False and out["selected_present"] not in {None, False}:
        raise ValueError(field + " absent land cannot have selected458")
    return out


def _rowset(value, field, selector, gate):
    raw, out = _start(value, field, {"count_raw", "array_present", "rows"})
    _words(raw, out, field, ("count_raw",))
    _bools(raw, out, field, ("array_present",))
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        copied = []
        for i, value in enumerate(rows):
            name = f"{field}.rows[{i}]"
            row = _dict(value, name, {"native_index", "threshold_raw", "admitted", "pc", "reason"})
            item = {"native_index": _integer(row["native_index"], name + ".native_index", 32), "pc": _pc(row["pc"], name + ".pc")}
            _words(row, item, name, ("threshold_raw",))
            _bools(row, item, name, ("admitted",))
            _strings(row, item, name, ("reason",))
            expected = selector >= item["threshold_raw"] if selector is not None and item["threshold_raw"] is not None else None
            if item["native_index"] != i or item["admitted"] != expected:
                raise ValueError(name + " stored row admission disagrees")
            if expected is not True and any(item["pc"][key] is not None for key in ("property_identity", "property_block")):
                raise ValueError(name + " rejected threshold contains undemanded PC")
            copied.append(item)
        rows = copied
    out["rows"] = rows
    count = out["count_raw"]
    if gate is False:
        if count is not None or out["array_present"] is not None or rows != []:
            raise ValueError(field + " skipped rowset contains operands")
        complete = True
    elif gate is not True or count is None or count < 0:
        complete = False
    elif count == 0:
        if rows != []:
            raise ValueError(field + " zero rowset contains rows")
        complete = True
    else:
        complete = (selector is not None and out["array_present"] is True and rows is not None and len(rows) == count
                    and all(row["admitted"] is not None and row["reason"] is None
                            and (not row["admitted"] or _pc_ready(row["pc"])) for row in rows))
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " rowset readiness disagrees")
    return out


def _composition(value, field, current_land):
    raw, out = _start(value, field, {"global_flag_u8", "global_bit20", "current_land_present", "current_selected_present",
        "receiver_selection", "admitted", "related", "owner_mode", "definition_identity", "level_raw", "handle_date",
        "fifth_date", "current_date", "chosen_date_selection", "completed_months_raw", "level_rows", "month_rows"})
    _words(raw, out, field, ("global_flag_u8",), 8, True)
    _words(raw, out, field, ("level_raw", "completed_months_raw"))
    _bools(raw, out, field, ("global_bit20", "current_land_present", "current_selected_present", "admitted", "owner_mode"))
    _strings(raw, out, field, ("receiver_selection", "definition_identity", "chosen_date_selection"))
    out["related"] = _related(raw["related"], field + ".related", current_land, False)
    for key in ("handle_date", "fifth_date", "current_date"):
        out[key] = _date(raw[key], field + "." + key)
    bit = None if out["global_flag_u8"] is None else bool(out["global_flag_u8"] & 0x20)
    if out["global_bit20"] != bit:
        raise ValueError(field + " bit20 disagrees")
    if bit is False:
        gate, selection, owner = False, "skipped", None
    elif bit is True and out["current_land_present"] is True and out["current_selected_present"] is True:
        gate, selection, owner = True, "current_458_178", True
    elif bit is True and (out["current_land_present"] is False or out["current_selected_present"] is False):
        rel = out["related"]
        if rel["helper_return_full_id_raw"] == -1 or rel["land_present"] is False or rel["selected_present"] is False:
            gate, selection, owner = False, "skipped", None
        elif rel["caller_selection"] is not None and rel["land_present"] is True and rel["selected_present"] is True:
            gate, selection, owner = True, "related_458_178", False
        else:
            gate = selection = owner = None
    else:
        gate = selection = owner = None
    if (out["admitted"], out["receiver_selection"], out["owner_mode"]) != (gate, selection, owner):
        raise ValueError(field + " receiver/mode admission disagrees")
    months = choice = None
    # Numeric-empty month rowset releases calendar/source dates entirely.
    if gate is True and raw["month_rows"]["count_raw"] is not None and raw["month_rows"]["count_raw"] > 0:
        handle, fifth = out["handle_date"]["raw_i32"], out["fifth_date"]["raw_i32"]
        if handle is not None and fifth is not None:
            choice = "fifth" if fifth > handle else "handle"
            months = completed_after_gated_months_12003(out["current_date"], out[choice + "_date"])
    if out["chosen_date_selection"] != choice or out["completed_months_raw"] != months:
        raise ValueError(field + " signedMAX/tie-retained calendar difference disagrees")
    out["level_rows"] = _rowset(raw["level_rows"], field + ".level_rows", out["level_raw"], gate)
    out["month_rows"] = _rowset(raw["month_rows"], field + ".month_rows", months, gate)
    complete = gate is False or (gate is True and out["definition_identity"] is not None
                               and out["level_rows"]["ready"] and out["month_rows"]["ready"])
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " composition readiness disagrees")
    return out


def _rule(value, field):
    raw, out = _start(value, field, {"mode_raw", "tree_present", "tree_identity", "named_present", "named",
                                  "target_count_raw", "raw_98_q64", "value_q64", "selection"})
    _words(raw, out, field, ("mode_raw", "target_count_raw"))
    _words(raw, out, field, ("raw_98_q64", "value_q64"), 64)
    _bools(raw, out, field, ("tree_present", "named_present"))
    _strings(raw, out, field, ("tree_identity", "selection"))
    out["named"] = _named(raw["named"], field + ".named", 0)
    mode = out["mode_raw"]
    selection = None
    if mode == 0:
        selection = "mode_zero_raw98"
        if any(out[key] is not None for key in ("tree_present", "tree_identity", "named_present", "target_count_raw")) or out["named"]["kind"] != "unconsumed":
            raise ValueError(field + " mode0 literal has tree/named/target demand")
    elif mode is not None:
        if out["tree_present"] is True:
            selection = "dynamic_tree"
            if out["tree_identity"] is None:
                raise ValueError(field + " dynamic tree lacks source identity")
        elif out["tree_present"] is False:
            if out["named_present"] is True:
                selection = "nested_named"
            elif out["named_present"] is False and out["target_count_raw"] is not None:
                selection = "zero_targets_raw98" if out["target_count_raw"] == 0 else "dynamic_targets"
    if out["selection"] != selection:
        raise ValueError(field + " rule source selection disagrees")
    value = definition_600_literal_value_12003(out)
    if out["value_q64"] != value:
        raise ValueError(field + " rule result disagrees with literal source")
    complete = value is not None and out["reason"] is None and (selection != "nested_named" or out["named"]["ready"])
    if out["ready"] != complete:
        raise ValueError(field + " rule numeric availability disagrees")
    return out


def _kind(value, field):
    raw, out = _start(value, field, {"position_120_raw", "position_124_raw", "owner_selection", "owner_identity",
        "owner_full_id_raw", "played_count_raw", "played_full_ids", "owner_played", "raw_a0_u8",
        "threshold_count_raw", "thresholds_i32", "rule", "kind_raw"})
    _words(raw, out, field, ("position_120_raw", "position_124_raw", "owner_full_id_raw", "played_count_raw", "threshold_count_raw", "kind_raw"))
    _words(raw, out, field, ("raw_a0_u8",), 8, True)
    _strings(raw, out, field, ("owner_selection", "owner_identity"))
    _bools(raw, out, field, ("owner_played",))
    out["played_full_ids"] = _numbers(raw["played_full_ids"], field + ".played_full_ids", 32)
    out["thresholds_i32"] = _numbers(raw["thresholds_i32"], field + ".thresholds_i32", 32)
    out["rule"] = _rule(raw["rule"], field + ".rule")
    count, ids, owner = out["played_count_raw"], out["played_full_ids"], out["owner_full_id_raw"]
    played = owner in ids if owner is not None and count is not None and count >= 0 and ids is not None and len(ids) == count else None
    if out["owner_played"] != played:
        raise ValueError(field + " played membership disagrees with whole DWORD IDs")
    if out["owner_selection"] not in {None, "indexed_full_id", "native_fallback"}:
        raise ValueError(field + " owner selection invalid")
    if out["owner_selection"] == "indexed_full_id" and out["position_120_raw"] != owner:
        raise ValueError(field + " owner indexed full generation disagrees")
    if played is True and out["raw_a0_u8"] is not None:
        raise ValueError(field + " played branch contains undemanded raw A0")
    value = quantized_court_position_kind_12003(out)
    if out["kind_raw"] != value:
        raise ValueError(field + " raw/fixed quantized kind disagrees")
    evaluation = played is True or (played is False and out["raw_a0_u8"] == 5)
    if not evaluation and any(out[key] is not None for key in ("threshold_count_raw", "thresholds_i32")):
        raise ValueError(field + " ordinary kind contains undemanded quantizer")
    if out["threshold_count_raw"] is not None and out["threshold_count_raw"] < 4:
        if out["thresholds_i32"] is not None or out["rule"]["mode_raw"] is not None:
            raise ValueError(field + " short threshold count contains undemanded rule/thresholds")
    complete = (out["owner_selection"] is not None and out["owner_identity"] is not None
                and owner is not None and value is not None and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " kind readiness disagrees")
    return out


def _pair(value, field):
    if not isinstance(value, list) or len(value) > 6:
        raise ValueError(field + " must contain up to six ordered count probes")
    rows, admitted = [], None
    for i, item in enumerate(value):
        raw = _dict(item, f"{field}[{i}]", {"native_index", "count_raw"})
        row = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
               "count_raw": _number(raw["count_raw"], field + ".count_raw", 32)}
        if row["native_index"] != i or admitted is not None:
            raise ValueError(field + " probes continue after known admission")
        rows.append(row)
        if row["count_raw"] is None:
            if i != len(value) - 1:
                raise ValueError(field + " probes continue after missing count")
        elif row["count_raw"] != 0:
            admitted = True
    if len(rows) == 6 and all(row["count_raw"] == 0 for row in rows):
        admitted = False
    return rows, admitted


def _position(value, field, index, family, selectors):
    fields = {"native_index", "requested_full_id_raw", "position_selection", "position_identity", "position_full_id_raw",
        "definition_identity", "other_definition_identity", "other_magic_raw", "other_admitted", "base_pc", "tier_pc",
        "composite_group", "kind", "other_base_pc", "other_tier_pc", "other_kind", "definition_pair_probes",
        "definition_pair_admitted", "other_pair_probes", "other_pair_admitted", "ready", "reason"}
    raw = _dict(value, field, fields)
    out = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
           "ready": _boolean(raw["ready"], field + ".ready")}
    _words(raw, out, field, ("requested_full_id_raw", "position_full_id_raw"))
    _words(raw, out, field, ("other_magic_raw",), 32, True)
    _strings(raw, out, field, ("position_selection", "position_identity", "definition_identity", "other_definition_identity", "reason"))
    _bools(raw, out, field, ("other_admitted", "definition_pair_admitted", "other_pair_admitted"))
    if out["native_index"] != index or out["position_selection"] not in {None, "registry_full_id_8", "native_fallback"}:
        raise ValueError(field + " CourtPosition source order/selection invalid")
    if out["position_selection"] == "registry_full_id_8" and (out["requested_full_id_raw"] is None or out["position_full_id_raw"] != out["requested_full_id_raw"]):
        raise ValueError(field + " CourtPosition full-generation selection disagrees")
    expected_other = None if out["other_magic_raw"] is None else out["other_magic_raw"] == 0x4744624F
    if out["other_admitted"] != expected_other:
        raise ValueError(field + " Other magic admission disagrees")
    for key in ("base_pc", "tier_pc", "other_base_pc", "other_tier_pc"):
        out[key] = _pc(raw[key], field + "." + key)
    for key in ("kind", "other_kind"):
        out[key] = _kind(raw[key], field + "." + key)
    group = raw["composite_group"]
    out["composite_group"] = None if group is None else _group(group, field + ".composite_group", selectors)
    if out["composite_group"] is not None and out["composite_group"]["role"] != "base":
        raise ValueError(field + " B8D0 cannot contain a growth group")
    out["definition_pair_probes"], def_pair = _pair(raw["definition_pair_probes"], field + ".definition_pair_probes")
    out["other_pair_probes"], other_pair = _pair(raw["other_pair_probes"], field + ".other_pair_probes")
    if out["definition_pair_admitted"] != def_pair or out["other_pair_admitted"] != other_pair:
        raise ValueError(field + " related pair admission disagrees with six source counts")
    complete = out["position_selection"] is not None and out["position_identity"] is not None and out["definition_identity"] is not None
    if family == 1:
        complete = (complete and _pc_ready(out["base_pc"]) and out["composite_group"] is not None and out["composite_group"]["ready"]
                    and expected_other is not None and (not expected_other or _pc_ready(out["other_base_pc"])))
    elif family == 2:
        complete = (complete and _pc_ready(out["base_pc"]) and out["kind"]["ready"] and _pc_ready(out["tier_pc"])
                    and out["composite_group"] is not None and out["composite_group"]["ready"] and expected_other is not None
                    and (not expected_other or (_pc_ready(out["other_base_pc"]) and out["other_kind"]["ready"] and _pc_ready(out["other_tier_pc"]))))
    else:
        complete = (complete and def_pair is not None and expected_other is not None
                    and (not def_pair or (_pc_ready(out["base_pc"]) and out["kind"]["ready"] and _pc_ready(out["tier_pc"])))
                    and (not expected_other or (other_pair is not None and (not other_pair or
                        (_pc_ready(out["other_base_pc"]) and out["other_kind"]["ready"] and _pc_ready(out["other_tier_pc"]))))))
        if group is not None:
            raise ValueError(field + " related family has no B8D0 composite")
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " per-position source readiness disagrees")
    return out


def _court_list(value, field, family, current_land, selectors):
    raw, out = _start(value, field, {"owner_present", "header_selection", "count_raw", "numeric_count", "array_present",
                                   "default_init_guard_raw", "related", "rows"})
    _words(raw, out, field, ("count_raw", "numeric_count", "default_init_guard_raw"))
    _bools(raw, out, field, ("owner_present", "array_present"))
    _strings(raw, out, field, ("header_selection",))
    out["related"] = _related(raw["related"], field + ".related", current_land, True)
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        rows = [_position(row, f"{field}.rows[{i}]", i, family, selectors) for i, row in enumerate(rows)]
    out["rows"] = rows
    selection, count, numeric = out["header_selection"], out["count_raw"], out["numeric_count"]
    allowed = ({None, "absent_owner", "current_1b8_d0"} if family == 1 else {None, "absent_owner", "current_1c0_3b8"}
               if family == 2 else {None, "related_1c0_3b8", "inline_default_54e7220", "modeled_empty_default_54e7220", "related_invalid_skip"})
    if selection not in allowed:
        raise ValueError(field + " header selection invalid for source family")
    if selection in {"absent_owner", "related_invalid_skip", "modeled_empty_default_54e7220"}:
        if numeric != 0 or count is not None or out["array_present"] is not None or rows != []:
            raise ValueError(field + " known/modelled empty header contains physical operands")
        complete = True
        if selection == "modeled_empty_default_54e7220" and out["default_init_guard_raw"] not in {0, -1}:
            raise ValueError(field + " modeled default requires actual uninitialized guard")
    else:
        if numeric != count:
            raise ValueError(field + " numeric count disagrees with actual observed header")
        complete = selection is not None and count is not None and count >= 0 and rows is not None and len(rows) == count
        if count and count > 0:
            complete = complete and out["array_present"] is True and all(row["ready"] for row in rows)
        if selection == "inline_default_54e7220":
            complete = complete and out["default_init_guard_raw"] not in {None, 0, -1}
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " independent list readiness disagrees")
    return out


def normalize_after_gated_tail_326a8e0_2920310(value, field=_FIELD):
    if value is None:
        return None
    raw, out = _start(value, field, {"character_id", "current_land_present", "selector_inputs", *FAMILIES_AFTER_GATED_12003})
    out["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    _bools(raw, out, field, ("current_land_present",))
    out["selector_inputs"] = _selectors(raw["selector_inputs"], field + ".selector_inputs")
    out["composition_326a8e0"] = _composition(raw["composition_326a8e0"], field + ".composition_326a8e0", out["current_land_present"])
    for family, name in enumerate(FAMILIES_AFTER_GATED_12003[1:], 1):
        out[name] = _court_list(raw[name], field + "." + name, family, out["current_land_present"], out["selector_inputs"])
    if out["ready"] != all(out[family]["ready"] for family in FAMILIES_AFTER_GATED_12003):
        raise ValueError(field + " readiness disagrees with four independent source families")
    return out


def _current(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_after_gated_tail_326a8e0_2920310(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return leaf, raw


def emit_after_gated_tail_family_requests_from_current_source_inputs_12003(section, family):
    leaf, raw = _current(section)
    return emit_after_gated_tail_family_requests_12003(leaf, family, actual_leaf=raw)


def emit_after_gated_tail_requests_from_current_source_inputs_12003(section):
    leaf, raw = _current(section)
    return emit_after_gated_tail_requests_12003(leaf, actual_leaf=raw)
