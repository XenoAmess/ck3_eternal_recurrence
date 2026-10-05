"""Strict all-vector preflight and actual ranked-PC source inputs for 2920B50."""
from __future__ import annotations

from .battle_context_source_inputs_contract import _availability, _boolean, _dict, _integer, _number, _string
from .battle_person_after_gated_tail_contract import _pc, _pc_ready
from ..simulation.battle_person_following_2920b50_12003 import (
    FAMILIES_FOLLOWING_2920B50_12003, following_rank_selection_12003,
    emit_following_2920b50_attribute_requests_12003,
    emit_following_2920b50_family_requests_12003, emit_following_2920b50_requests_12003,
)

_FIELD = "following_2920b50"
_NUMERIC_WORDS = ("rank_raw_i32", "index_raw_i32", "ranked_count_raw", "ranked_default_init_guard_raw")
_NUMERIC_STRINGS = ("ranked_header_identity", "selection", "selected_row_identity")
_ATTRIBUTE_FIELDS = {"native_index", "definition_present", "definition_identity", "definition_magic_u32",
    "preflight_valid", *_NUMERIC_WORDS, *_NUMERIC_STRINGS, "ranked_array_present", "pc", "ready", "reason"}


def _start(value, field, fields):
    raw = _dict(value, field, {"status", "ready", "reason", *fields})
    status, ready, reason = _availability(raw, field)
    return raw, {"status": status, "ready": ready, "reason": reason}


def _words(raw, out, field, keys, unsigned=False):
    for key in keys:
        out[key] = _number(raw[key], field + "." + key, 32, unsigned=unsigned)


def _strings(raw, out, field, keys):
    for key in keys:
        out[key] = _string(raw[key], field + "." + key, optional=True)


def _bools(raw, out, field, keys, optional=True):
    for key in keys:
        out[key] = _boolean(raw[key], field + "." + key, optional=optional)


def _preflight_valid(raw, field):
    present = _boolean(raw["definition_present"], field + ".definition_present", optional=True)
    magic = _number(raw["definition_magic_u32"], field + ".definition_magic_u32", 32, unsigned=True)
    return False if present is False else None if present is None or magic is None else magic == 0x4744624F


def _attribute(value, field, index, numeric):
    raw = _dict(value, field, _ATTRIBUTE_FIELDS)
    out = {"native_index": _integer(raw["native_index"], field + ".native_index", 32)}
    _words(raw, out, field, _NUMERIC_WORDS)
    _words(raw, out, field, ("definition_magic_u32",), True)
    _strings(raw, out, field, (*_NUMERIC_STRINGS, "definition_identity", "reason"))
    _bools(raw, out, field, ("definition_present", "preflight_valid", "ranked_array_present"))
    _bools(raw, out, field, ("ready",), False)
    out["pc"] = _pc(raw["pc"], field + ".pc")
    if out["native_index"] != index or out["preflight_valid"] != _preflight_valid(raw, field):
        raise ValueError(field + " attribute index/Definition preflight disagrees")
    if out["definition_present"] is not True and any(out[key] is not None for key in ("definition_identity", "definition_magic_u32")):
        raise ValueError(field + " absent Definition contains undemanded magic/identity")
    if numeric is not True:
        if (any(out[key] is not None for key in (*_NUMERIC_WORDS, *_NUMERIC_STRINGS, "ranked_array_present"))
            or any(out["pc"][key] is not None for key in ("property_identity", "property_block")) or out["ready"]):
            raise ValueError(field + " entire preflight blocks all rank/PC operands")
        return out
    index_raw, selection = following_rank_selection_12003(out)
    if (out["index_raw_i32"], out["selection"]) != (index_raw, selection):
        raise ValueError(field + " wrapped rank/default selection disagrees")
    if index_raw is not None and index_raw < 0:
        if any(out[key] is not None for key in ("ranked_count_raw", "ranked_array_present")):
            raise ValueError(field + " negative index contains undemanded ranked header")
    if selection == "indexed_ranked_row":
        if out["ranked_default_init_guard_raw"] is not None:
            raise ValueError(field + " indexed row contains undemanded default guard")
        selected = out["ranked_header_identity"] is not None and out["ranked_array_present"] is True
    else:
        selected = selection == "initialized_default_5d68fb0"
        if out["ranked_array_present"] is not None:
            raise ValueError(field + " default row contains undemanded ranked data")
    if selection == "uninitialized_default_5d68fb0":
        if out["reason"] != "ranked_default_initialization_result":
            raise ValueError(field + " cold ranked default must retain precise missing result")
        if any(out["pc"][key] is not None for key in ("property_identity", "property_block")):
            raise ValueError(field + " cold ranked default cannot publish uninitialized PC bytes")
    complete = (out["definition_identity"] is not None and selected and out["selected_row_identity"] is not None
                and _pc_ready(out["pc"]) and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " ranked attribute readiness disagrees")
    return out


def _occurrence(value, field, index, own):
    raw, out = _start(value, field, {"native_index", "requested_full_id_raw", "resolution_selection",
        "selected_full_id_raw", "object_identity", "accolade_magic_u32", "accolade_full_id_raw", "admitted",
        "attribute_count_raw", "attribute_array_present", "preflight_ready", "preflight_all_valid", "attributes"})
    out["native_index"] = _integer(raw["native_index"], field + ".native_index", 32)
    _words(raw, out, field, ("requested_full_id_raw", "selected_full_id_raw", "accolade_full_id_raw", "attribute_count_raw"))
    _words(raw, out, field, ("accolade_magic_u32",), True)
    _strings(raw, out, field, ("resolution_selection", "object_identity"))
    _bools(raw, out, field, ("admitted", "attribute_array_present", "preflight_all_valid"))
    _bools(raw, out, field, ("preflight_ready",), False)
    selection = out["resolution_selection"]
    if out["native_index"] != index or selection not in {None, "registry_full_id_8", "native_fallback"}:
        raise ValueError(field + " source occurrence index/resolution invalid")
    if selection == "registry_full_id_8" and (
        out["requested_full_id_raw"] is None or out["selected_full_id_raw"] != out["requested_full_id_raw"]
    ):
        raise ValueError(field + " full-generation resolution disagrees")
    resolved = selection is not None and out["object_identity"] is not None
    if own:
        magic, full_id = out["accolade_magic_u32"], out["accolade_full_id_raw"]
        admission = None if not resolved or magic is None else False if magic != 0x4163636F else None if full_id is None else full_id != -1
    else:
        admission = True if resolved else None
        if out["accolade_magic_u32"] is not None or out["accolade_full_id_raw"] is not None:
            raise ValueError(field + " list occurrence has no Acco magic/fullID gate")
    if out["admitted"] != admission:
        raise ValueError(field + " actual Accolade admission disagrees")
    count, attrs = out["attribute_count_raw"], raw["attributes"]
    if attrs is not None and not isinstance(attrs, list):
        raise ValueError(field + ".attributes must be a list or null")
    preflight, all_valid = False, None
    if admission is False:
        if count is not None or out["attribute_array_present"] is not None or attrs != []:
            raise ValueError(field + " rejected own Accolade contains attribute operands")
        preflight, all_valid = True, False
    elif admission is True and count == 0:
        if attrs != []:
            raise ValueError(field + " zero attribute vector contains rows")
        preflight, all_valid = True, True
    elif admission is True and count is not None and count > 0 and attrs is not None and out["attribute_array_present"] is True:
        if len(attrs) > count:
            raise ValueError(field + " attributes exceed actual count")
        for i, item in enumerate(attrs):
            row = _dict(item, f"{field}.attributes[{i}]", _ATTRIBUTE_FIELDS)
            valid = _preflight_valid(row, f"{field}.attributes[{i}]")
            if valid is not True:
                if i != len(attrs) - 1:
                    raise ValueError(field + " preflight prefix continues after invalid/unknown row")
                preflight, all_valid = valid is False, False if valid is False else None
                break
        else:
            if len(attrs) == count:
                preflight, all_valid = True, True
    if (out["preflight_ready"], out["preflight_all_valid"]) != (preflight, all_valid):
        raise ValueError(field + " entire-vector preflight availability disagrees")
    out["attributes"] = None if attrs is None else [
        _attribute(row, f"{field}.attributes[{i}]", i, preflight and all_valid) for i, row in enumerate(attrs)]
    complete = resolved and preflight and (all_valid is False or all(row["ready"] for row in out["attributes"]))
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " occurrence readiness disagrees with all-vector preflight")
    return out


def _list(value, field):
    raw, out = _start(value, field, {"component_present", "header_selection", "default_init_guard_raw",
                                  "count_raw", "numeric_count", "array_present", "rows"})
    _bools(raw, out, field, ("component_present", "array_present"))
    _strings(raw, out, field, ("header_selection",))
    _words(raw, out, field, ("default_init_guard_raw", "count_raw", "numeric_count"))
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        rows = [_occurrence(row, f"{field}.rows[{i}]", i, False) for i, row in enumerate(rows)]
    out["rows"] = rows
    selection, guard = out["header_selection"], out["default_init_guard_raw"]
    if selection not in {None, "current_1c8_50", "inline_default_5d67e80", "modeled_empty_default_5d67e80"}:
        raise ValueError(field + " list header selection invalid")
    if selection is not None and (selection == "current_1c8_50") != (out["component_present"] is True):
        raise ValueError(field + " header selection disagrees with component1C8")
    count, numeric = out["count_raw"], out["numeric_count"]
    if selection == "modeled_empty_default_5d67e80":
        if guard not in {0, -1} or count is not None or numeric != 0 or out["array_present"] is not None or rows != []:
            raise ValueError(field + " modeled empty list contains physical operands or lacks observed guard")
        complete = True
    else:
        if numeric != count:
            raise ValueError(field + " numeric list count disagrees with actual header")
        complete = selection is not None and count is not None and count >= 0 and rows is not None and len(rows) == count
        if count is not None and count > 0:
            complete = complete and out["array_present"] is True and all(row["ready"] for row in rows)
        if selection == "inline_default_5d67e80":
            complete = complete and guard not in {None, 0, -1}
        if selection == "current_1c8_50" and guard is not None:
            raise ValueError(field + " current list contains undemanded default guard")
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " list readiness disagrees")
    return out


def normalize_following_2920b50(value, field=_FIELD):
    if value is None:
        return None
    raw, out = _start(value, field, {"character_id", *FAMILIES_FOLLOWING_2920B50_12003})
    out["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    out["list_1c8_50"] = _list(raw["list_1c8_50"], field + ".list_1c8_50")
    name = field + ".own_1b0_570"
    own, copied = _start(raw["own_1b0_570"], name, {"component_present", "occurrence"})
    _bools(own, copied, name, ("component_present",))
    copied["occurrence"] = _occurrence(own["occurrence"], name + ".occurrence", 0, True)
    if copied["ready"] != (copied["occurrence"]["ready"] and copied["reason"] is None):
        raise ValueError(name + " own-family readiness disagrees")
    out["own_1b0_570"] = copied
    if out["ready"] != all(out[name]["ready"] for name in FAMILIES_FOLLOWING_2920B50_12003):
        raise ValueError(field + " readiness disagrees with two independent families")
    return out


def _current(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_following_2920b50(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return leaf, raw


def emit_following_2920b50_requests_from_current_source_inputs_12003(section):
    leaf, raw = _current(section)
    return emit_following_2920b50_requests_12003(leaf, actual_leaf=raw)


def emit_following_2920b50_family_requests_from_current_source_inputs_12003(section, family):
    leaf, raw = _current(section)
    return emit_following_2920b50_family_requests_12003(leaf, family, actual_leaf=raw)


def emit_following_2920b50_attribute_requests_from_current_source_inputs_12003(
    section, family, occurrence_index, attribute_index,
):
    leaf, raw = _current(section)
    if family not in FAMILIES_FOLLOWING_2920B50_12003:
        raise ValueError("Unknown following2920B50 family")
    index = _integer(occurrence_index, "occurrence_index", 32)
    attr = _integer(attribute_index, "attribute_index", 32)
    rows = leaf[family]["rows"] if family == "list_1c8_50" else [leaf[family]["occurrence"]]
    if rows is None or not 0 <= index < len(rows):
        raise ValueError("Required native input unavailable: occurrence")
    occurrence = rows[index]
    if occurrence["admitted"] is not False:
        count = occurrence["attribute_count_raw"]
        if count is None or not 0 <= attr < count:
            raise ValueError("Required native input unavailable: attribute")
    return emit_following_2920b50_attribute_requests_12003(leaf, family, index, attr, actual_leaf=raw)
