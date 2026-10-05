"""Strict literal-source input contract for current-person C7A7..C9D8."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _numbers, _properties,
    _properties_ready, _string,
)
from ..simulation.battle_person_gated_temporary_tail_12003 import (
    FAMILIES_291C7A7, emit_gated_temporary_tail_family_requests_12003,
    emit_gated_temporary_tail_requests_12003, fresh_temporary_rank_12003,
    literal_named_source_value_12003, selected_temporary_operand_12003, temporary_delta_12003,
)
from ..simulation.battle_trait_numeric_inputs_12003 import native_wrap32_12003

_FIELD = "gated_temporary_tail_291c7a7"


def _pc_ready(block):
    return _properties_ready(block) and block["reason"] is None


def _start(value, field, fields):
    raw = _dict(value, field, {"status", "ready", "reason", *fields})
    status, ready, reason = _availability(raw, field)
    return raw, {"status": status, "ready": ready, "reason": reason}


def _words(raw, result, field, keys, bits=32, unsigned=False):
    for key in keys:
        result[key] = _number(raw[key], field + "." + key, bits, unsigned=unsigned)


def _strings(raw, result, field, keys):
    for key in keys:
        result[key] = _string(raw[key], field + "." + key, optional=True)


def _bools(raw, result, field, keys):
    for key in keys:
        result[key] = _boolean(raw[key], field + "." + key, optional=True)


def _named(value, field, slot):
    raw, result = _start(value, field, {
        "slot_offset", "entry_identity", "tree_present", "tree_identity", "fixed_flag_u8",
        "raw_fixed_q64", "value_q64", "kind",
    })
    result["slot_offset"] = _integer(raw["slot_offset"], field + ".slot_offset", 32)
    _strings(raw, result, field, ("entry_identity", "tree_identity"))
    _bools(raw, result, field, ("tree_present",))
    _words(raw, result, field, ("fixed_flag_u8",), 8, True)
    _words(raw, result, field, ("raw_fixed_q64", "value_q64"), 64)
    result["kind"] = _string(raw["kind"], field + ".kind")
    if result["slot_offset"] != slot or result["kind"] not in {
        "unconsumed", "missing", "dynamic_tree_requires_current_result", "known_zero", "literal",
    }:
        raise ValueError(field + " source slot/kind disagrees")
    tree, flag = result["tree_present"], result["fixed_flag_u8"]
    if tree is not False and any(result[key] is not None for key in ("fixed_flag_u8", "raw_fixed_q64")):
        raise ValueError(field + " tree takes precedence over fixed flag/value")
    if flag in {None, 0} and result["raw_fixed_q64"] is not None:
        raise ValueError(field + " raw68 was not demanded")
    expected_value = literal_named_source_value_12003(result)
    if result["value_q64"] != expected_value:
        raise ValueError(field + " numeric value disagrees with tree/flag/raw68")
    if tree is True:
        if result["kind"] != "dynamic_tree_requires_current_result" or result["entry_identity"] is None or result["tree_identity"] is None:
            raise ValueError(field + " dynamic source provenance disagrees")
    elif expected_value is not None:
        expected_kind = "known_zero" if flag == 0 else "literal"
        if result["kind"] != expected_kind:
            raise ValueError(field + " literal source kind disagrees")
    elif result["kind"] not in {"missing", "unconsumed"}:
        raise ValueError(field + " incomplete source cannot claim a value kind")
    if result["kind"] == "unconsumed" and any(result[key] is not None for key in (
        "entry_identity", "tree_present", "tree_identity", "fixed_flag_u8", "raw_fixed_q64", "value_q64")):
        raise ValueError(field + " unconsumed source contains numeric operands")
    complete = expected_value is not None and result["entry_identity"] is not None and result["reason"] is None
    if result["ready"] != complete:
        raise ValueError(field + " literal availability disagrees")
    return result


def _refresh(value, field, gate):
    raw, result = _start(value, field, {
        "source", "minimum_q64", "maximum_q64", "clamped_q64", "threshold_count",
        "threshold_array_present", "thresholds_consumed_q64", "fresh_rank_raw",
    })
    result["source"] = _named(raw["source"], field + ".source", 0x168)
    _words(raw, result, field, ("minimum_q64", "maximum_q64", "clamped_q64"), 64)
    _words(raw, result, field, ("threshold_count", "fresh_rank_raw"))
    _bools(raw, result, field, ("threshold_array_present",))
    result["thresholds_consumed_q64"] = _numbers(raw["thresholds_consumed_q64"], field + ".thresholds_consumed_q64", 64)
    clamp, rank = fresh_temporary_rank_12003(result)
    if result["clamped_q64"] != clamp or result["fresh_rank_raw"] != rank:
        raise ValueError(field + " fresh clamp/rank disagrees with literal source")
    count, thresholds = result["threshold_count"], result["thresholds_consumed_q64"]
    if count is not None and thresholds is not None:
        if count <= 0:
            if thresholds or result["threshold_array_present"] is not None:
                raise ValueError(field + " nonpositive count contains undemanded thresholds")
        else:
            if len(thresholds) > count:
                raise ValueError(field + " threshold prefix exceeds count")
            if clamp is not None:
                hit = next((i for i, item in enumerate(thresholds) if clamp <= item), None)
                if hit is not None and hit != len(thresholds) - 1:
                    raise ValueError(field + " thresholds continue past first signed rank")
    if gate is False:
        if any(result[key] is not None for key in (
            "minimum_q64", "maximum_q64", "clamped_q64", "threshold_count", "threshold_array_present",
            "thresholds_consumed_q64", "fresh_rank_raw")) or result["source"]["kind"] != "unconsumed":
            raise ValueError(field + " skipped refresh contains undemanded operands")
        complete = True
    else:
        complete = (gate is True and result["source"]["ready"] and clamp is not None and rank is not None
                    and count is not None and (count <= 0 or result["threshold_array_present"] is True)
                    and thresholds is not None and result["reason"] is None)
    if result["ready"] != complete:
        raise ValueError(field + " refresh availability disagrees")
    return result


def _prefix_row(value, field, index):
    raw = _dict(value, field, {"native_index", "definition_identity", "magic_raw", "admitted", "property_identity", "property_block", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    _words(raw, result, field, ("magic_raw",), 32, True)
    _strings(raw, result, field, ("definition_identity", "property_identity", "reason"))
    _bools(raw, result, field, ("admitted",))
    expected = None if result["magic_raw"] is None else result["magic_raw"] == 0x4744624F
    if result["native_index"] != index or result["admitted"] != expected:
        raise ValueError(field + " prefix occurrence/magic admission disagrees")
    if expected is not True and any(result[key] is not None for key in ("property_identity", "property_block")):
        raise ValueError(field + " unadmitted definition contains undemanded PC")
    return result


def _prefix(value, field, selector, gate):
    raw, result = _start(value, field, {"selector_raw", "native_prefix_count", "header_count", "array_present", "rows"})
    _words(raw, result, field, ("selector_raw", "native_prefix_count", "header_count"))
    _bools(raw, result, field, ("array_present",))
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        rows = [_prefix_row(row, f"{field}.rows[{i}]", i) for i, row in enumerate(rows)]
    result["rows"] = rows
    expected_selector = selector if gate is True else None
    expected_count = None if expected_selector is None else native_wrap32_12003(expected_selector + 1)
    if result["selector_raw"] != expected_selector or result["native_prefix_count"] != expected_count:
        raise ValueError(field + " selector/prefix count disagrees with wrapped native operands")
    count, header = expected_count, result["header_count"]
    if gate is False:
        if header is not None or result["array_present"] is not None or rows != []:
            raise ValueError(field + " skipped prefix contains source operands")
        complete = True
    elif gate is not True or count is None:
        complete = False
    elif count <= 0:
        if header is not None or rows != [] or result["array_present"] is not None:
            raise ValueError(field + " nonpositive prefix contains undemanded header/rows")
        complete = result["reason"] is None
    elif header is None:
        complete = False
    elif count > header:
        if rows != [] or result["array_present"] is not None:
            raise ValueError(field + " rejected prefix contains undemanded rows")
        complete = result["reason"] is None
    else:
        if rows is not None and len(rows) > count:
            raise ValueError(field + " rows exceed admitted prefix")
        complete = (result["array_present"] is True and rows is not None and len(rows) == count
                    and all(row["definition_identity"] is not None and row["admitted"] is not None and row["reason"] is None
                            and (not row["admitted"] or (row["property_identity"] is not None and _pc_ready(row["property_block"]))) for row in rows)
                    and result["reason"] is None)
    if result["ready"] != complete:
        raise ValueError(field + " independent prefix readiness disagrees")
    return result


def _delta(value, field, leaf, selected):
    raw, result = _start(value, field, {"delta_raw", "absolute_delta_raw", "header_selection", "weight_source", "prefix"})
    _words(raw, result, field, ("delta_raw", "absolute_delta_raw"))
    _strings(raw, result, field, ("header_selection",))
    result["weight_source"] = _named(raw["weight_source"], field + ".weight_source", 0x170)
    gate, rank = leaf["temporary_admitted"], leaf["refresh_168"]["fresh_rank_raw"]
    delta = absolute = None
    if gate is True and selected is not None and rank is not None:
        delta, absolute = temporary_delta_12003(selected, rank)
        if delta == 0:
            absolute = None  # Native zero fast path does not demand absolute.
    if result["delta_raw"] != delta or result["absolute_delta_raw"] != absolute:
        raise ValueError(field + " delta disagrees with fresh rank, not cached FC")
    expected_header = None if delta is None else "zero_delta" if delta == 0 else "provider_1420" if delta > 0 else "provider_14a8"
    if result["header_selection"] != expected_header:
        raise ValueError(field + " delta header disagrees")
    prefix_gate = False if gate is False or delta == 0 else True if delta is not None else None
    result["prefix"] = _prefix(raw["prefix"], field + ".prefix", absolute, prefix_gate)
    prefix = result["prefix"]
    needs_weight = bool(prefix["ready"] and any(row["admitted"] and row["property_block"]["keys_count"] > 0 for row in (prefix["rows"] or [])))
    complete = (gate is False or (gate is True and leaf["refresh_168"]["ready"] and delta is not None
                and prefix["ready"] and (not needs_weight or result["weight_source"]["ready"]))) and result["reason"] is None
    if result["ready"] != complete:
        raise ValueError(field + " delta numeric readiness disagrees")
    return result


def _resolution(value, field, index, helper):
    raw = _dict(value, field, {"native_index", "requested_full_id_raw", "registry_present", "capacity_u32",
        "indexed_pointer_present", "indexed_full_id_raw", "selection", "object_identity", "magic_raw", "full_id_raw", "admitted", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32)}
    _words(raw, result, field, ("requested_full_id_raw", "indexed_full_id_raw", "full_id_raw"))
    _words(raw, result, field, ("capacity_u32", "magic_raw"), 32, True)
    _bools(raw, result, field, ("registry_present", "indexed_pointer_present", "admitted"))
    _strings(raw, result, field, ("selection", "object_identity", "reason"))
    if result["native_index"] != index or result["selection"] not in {
        None, "registry_absent", "out_of_capacity", "indexed_full_id", "native_fallback",
    }:
        raise ValueError(field + " resolution order/selection disagrees")
    key, capacity, store = result["requested_full_id_raw"], result["capacity_u32"], result["registry_present"]
    expected_selection = None
    if store is False:
        expected_selection = "registry_absent" if helper else "native_fallback"
    elif store is True and key is not None and capacity is not None:
        if (key & 0xFFFFFF) >= capacity:
            expected_selection = "out_of_capacity" if helper else "native_fallback"
        elif result["indexed_pointer_present"] is False:
            expected_selection = "native_fallback"
        elif result["indexed_pointer_present"] is True and result["indexed_full_id_raw"] is not None:
            expected_selection = "indexed_full_id" if result["indexed_full_id_raw"] == key else "native_fallback"
    if result["selection"] is not None and result["selection"] != expected_selection:
        raise ValueError(field + " resolution disagrees with full-generation lookup")
    selection, magic, full_id = result["selection"], result["magic_raw"], result["full_id_raw"]
    expected_admission = (False if selection in {"registry_absent", "out_of_capacity"} else
                          None if magic is None else False if magic != 0x43686172 else None if full_id is None else full_id != -1)
    if result["admitted"] != expected_admission:
        raise ValueError(field + " Character magic/full ID admission disagrees")
    if selection in {"registry_absent", "out_of_capacity"} and any(result[key] is not None for key in ("object_identity", "magic_raw", "full_id_raw")):
        raise ValueError(field + " helper miss contains undemanded fallback/gate operands")
    return result


def _related(value, field, current_land):
    raw = _dict(value, field, {"carrier_present", "attempts", "self_full_id_raw", "helper_return_full_id_raw", "caller", "land_present", "selected_present", "reason"})
    result = {}
    _bools(raw, result, field, ("carrier_present", "land_present", "selected_present"))
    _words(raw, result, field, ("self_full_id_raw", "helper_return_full_id_raw"))
    _strings(raw, result, field, ("reason",))
    if not isinstance(raw["attempts"], list) or len(raw["attempts"]) > 2:
        raise ValueError(field + ".attempts must be the CC then C8 prefix")
    result["attempts"] = [_resolution(row, f"{field}.attempts[{i}]", i, True) for i, row in enumerate(raw["attempts"])]
    attempts = result["attempts"]
    expected_return = None
    if result["carrier_present"] is False:
        if attempts or result["self_full_id_raw"] is not None:
            raise ValueError(field + " missing1B8 contains undemanded candidate/self operands")
        expected_return = -1
    elif result["carrier_present"] is True:
        for i, row in enumerate(attempts):
            if row["admitted"] is True:
                if i != len(attempts) - 1:
                    raise ValueError(field + " continues after an admitted candidate")
                expected_return = row["requested_full_id_raw"]
                break
            if row["admitted"] is None or row["reason"] is not None:
                break
        else:
            if len(attempts) == 2:
                expected_return = result["self_full_id_raw"] if current_land else -1 if current_land is False else None
    if result["helper_return_full_id_raw"] != expected_return:
        raise ValueError(field + " helper returned ID disagrees with CC/C8/self demand")
    result["caller"] = _resolution(raw["caller"], field + ".caller", 0, False)
    caller = result["caller"]
    if caller["requested_full_id_raw"] != expected_return:
        raise ValueError(field + " caller did not resolve the actual returned full ID")
    if caller["admitted"] is not True and (result["land_present"] is not None or result["selected_present"] is not None):
        raise ValueError(field + " inadmissible related Character contains selected operands")
    if result["land_present"] is False and result["selected_present"] not in {None, False}:
        raise ValueError(field + " absent related land cannot have selected458")
    return result


def _list(value, field, leaf):
    raw, result = _start(value, field, {"selection", "related", "count_raw", "array_present", "rows"})
    _strings(raw, result, field, ("selection",))
    _words(raw, result, field, ("count_raw",))
    _bools(raw, result, field, ("array_present",))
    result["related"] = _related(raw["related"], field + ".related", leaf["current_land_present"])
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        copied = []
        for i, item in enumerate(rows):
            name = f"{field}.rows[{i}]"
            row = _dict(item, name, {"native_index", "property_identity", "property_block", "reason"})
            row = {"native_index": _integer(row["native_index"], name + ".native_index", 32),
                   "property_identity": _string(row["property_identity"], name + ".property_identity", optional=True),
                   "property_block": _properties(row["property_block"], name + ".property_block"),
                   "reason": _string(row["reason"], name + ".reason", optional=True)}
            if row["native_index"] != i:
                raise ValueError(name + " native occurrence order disagrees")
            copied.append(row)
        rows = copied
    result["rows"] = rows
    bit, current = leaf["global_bit20"], leaf["current_selected_present"]
    related, expected = result["related"], None
    if bit is False:
        expected = "skipped_bit20"
    elif bit is True and current is True:
        expected = "current_A20"
    elif bit is True and current is False:
        caller = related["caller"]
        if caller["admitted"] is False or related["land_present"] is False or related["selected_present"] is False:
            expected = "related_skip"
        elif caller["admitted"] is True and related["land_present"] is True and related["selected_present"] is True:
            expected = "related_BE0"
    if result["selection"] != expected:
        raise ValueError(field + " list source disagrees with bit/current/related gates")
    count = result["count_raw"]
    if expected in {"skipped_bit20", "related_skip"}:
        if count is not None or result["array_present"] is not None or rows != []:
            raise ValueError(field + " skipped list contains undemanded rows")
        complete = True
    elif expected is None or count is None:
        complete = False
    elif count == 0 or (expected == "related_BE0" and count < 0):
        if rows != []:
            raise ValueError(field + " empty list contains rows")
        complete = True
    elif count < 0:
        complete = False
    else:
        if rows is not None and len(rows) > count:
            raise ValueError(field + " list rows exceed count")
        complete = (result["array_present"] is True and rows is not None and len(rows) == count
                    and all(row["property_identity"] is not None and _pc_ready(row["property_block"]) and row["reason"] is None for row in rows))
    complete = complete and result["reason"] is None
    if result["ready"] != complete:
        raise ValueError(field + " independent list availability disagrees")
    return result


def normalize_gated_temporary_tail_291c7a7(value: object, field: str = _FIELD) -> dict | None:
    if value is None:
        return None
    bools = ("global_bit20", "current_land_present", "current_selected_present", "temporary_admitted")
    words = ("selected_ec_raw", "selector_global_raw", "selected_e8_raw", "selected_f8_raw")
    raw, result = _start(value, field, {"character_id", "global_flag_u8", *bools, *words,
        "refresh_168", "prefix_1398", "delta_prefix_1420_14a8", "list"})
    result["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    _words(raw, result, field, words)
    _words(raw, result, field, ("global_flag_u8",), 8, True)
    _bools(raw, result, field, bools)
    bit = None if result["global_flag_u8"] is None else bool(result["global_flag_u8"] & 0x20)
    if result["global_bit20"] != bit:
        raise ValueError(field + " global bit20 disagrees with actual flag byte")
    land, selected = result["current_land_present"], result["current_selected_present"]
    if bit is False and (land is not None or selected is not None):
        raise ValueError(field + " disabled bit demanded current selection")
    if land is False and selected not in {None, False}:
        raise ValueError(field + " absent current land cannot have selected458")
    gate = False if bit is False or land is False or selected is False else True if bit is True and land is True and selected is True else None
    if result["temporary_admitted"] != gate:
        raise ValueError(field + " temporary gate disagrees")
    operand = selected_temporary_operand_12003(result)
    if gate is not True and any(result[key] is not None for key in words):
        raise ValueError(field + " skipped temporary gate contains selected operands")
    if result["selected_ec_raw"] is not None and result["selector_global_raw"] is not None:
        unused = "selected_e8_raw" if result["selected_ec_raw"] == result["selector_global_raw"] else "selected_f8_raw"
        if result[unused] is not None:
            raise ValueError(field + " contains an undemanded alternate selection operand")
    result["refresh_168"] = _refresh(raw["refresh_168"], field + ".refresh_168", gate)
    result["prefix_1398"] = _prefix(raw["prefix_1398"], field + ".prefix_1398", operand, gate)
    result["delta_prefix_1420_14a8"] = _delta(raw["delta_prefix_1420_14a8"], field + ".delta_prefix_1420_14a8", result, operand)
    result["list"] = _list(raw["list"], field + ".list", result)
    if result["ready"] != all(result[family]["ready"] for family in FAMILIES_291C7A7):
        raise ValueError(field + " availability disagrees with three independent families")
    return result


def _current(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_gated_temporary_tail_291c7a7(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return leaf, raw


def emit_gated_temporary_tail_family_requests_from_current_source_inputs_12003(section, family):
    leaf, raw = _current(section)
    return emit_gated_temporary_tail_family_requests_12003(leaf, family, actual_leaf=raw)


def emit_gated_temporary_tail_requests_from_current_source_inputs_12003(section):
    leaf, raw = _current(section)
    return emit_gated_temporary_tail_requests_12003(leaf, actual_leaf=raw)
