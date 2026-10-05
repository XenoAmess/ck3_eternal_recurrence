"""Strict source-shaped provider192 and 2920850 unit-request receipts."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties_ready, _string,
)
from .battle_person_after_gated_tail_contract import _pc, _pc_ready
from .battle_person_remaining_helpers_contract import _family, _membership_ready, _rite
from ..simulation.battle_person_provider192_and2920850_12003 import (
    FAMILIES_PROVIDER192_AND2920850_12003,
    emit_provider192_and2920850_descriptor_requests_12003,
    emit_provider192_and2920850_family_requests_12003,
    emit_provider192_and2920850_requests_12003,
    emit_provider192_and2920850_slot_requests_12003,
)

_FIELD = "provider192_and2920850"
_DEFAULT = "inline_nested_mapped_default_5dc21b0"


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


def _bools(raw, out, field, keys, optional=True):
    for key in keys:
        out[key] = _boolean(raw[key], field + "." + key, optional=optional)


def _provider(value, field):
    raw, out = _start(value, field, {"provider_loaded", "provider_identity", "character_192_i16",
        "upper_i32", "lower_i32", "selection", "selected_identity", "magic_u32", "admitted", "pc"})
    _bools(raw, out, field, ("provider_loaded", "admitted"))
    _strings(raw, out, field, ("provider_identity", "selection", "selected_identity"))
    _words(raw, out, field, ("character_192_i16",), 16)
    _words(raw, out, field, ("upper_i32", "lower_i32"))
    _words(raw, out, field, ("magic_u32",), 32, True)
    out["pc"] = _pc(raw["pc"], field + ".pc")
    selection = None
    value, upper, lower = out["character_192_i16"], out["upper_i32"], out["lower_i32"]
    if out["provider_loaded"] is True and value is not None and upper is not None:
        if value >= upper:
            selection = "provider_16a0"
            if lower is not None:
                raise ValueError(field + " upper success contains undemanded lower threshold")
        elif lower is not None:
            selection = "provider_16b0" if value <= lower else "native_fallback_5d1e0b0"
    if out["selection"] != selection:
        raise ValueError(field + " upper-first signed provider selection disagrees")
    magic = out["magic_u32"]
    admitted = magic == 0x4744624F if selection is not None and magic is not None else None
    if out["admitted"] != admitted:
        raise ValueError(field + " selected magic admission disagrees")
    if admitted is not True and any(out["pc"][key] is not None for key in ("property_identity", "property_block")):
        raise ValueError(field + " rejected provider contains undemanded PC")
    complete = (out["provider_loaded"] is True and out["provider_identity"] is not None
        and selection is not None and out["selected_identity"] is not None and admitted is not None
        and (not admitted or _pc_ready(out["pc"])) and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " provider readiness disagrees")
    return out


def _slots(value, field, nested, rite, guard):
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(field + " resolved table must have four physical slots")
    rows = []
    for i, item in enumerate(value):
        name = f"{field}[{i}]"
        key = "mapped_family" if nested else "pc"
        raw = _dict(item, name, {"native_index", key})
        index = _integer(raw["native_index"], name + ".native_index", 32)
        if index != i:
            raise ValueError(name + " slot index disagrees with physical order")
        payload = (_family(raw[key], name + "." + key, "mapped", rite=rite, default=_DEFAULT, guard=guard)
                   if nested else _pc(raw[key], name + ".pc"))
        rows.append({"native_index": index, key: payload})
    return rows


def _occurrence(value, field, index, rite, guard):
    raw = _dict(value, field, {"native_index", "requested_full_id_raw", "resolution_selection",
        "selected_full_id_raw", "object_identity", "table_identity", "direct_rows", "nested_rows",
        "direct_ready", "mapped_ready", "ready", "reason"})
    out = {"native_index": _integer(raw["native_index"], field + ".native_index", 32)}
    _words(raw, out, field, ("requested_full_id_raw", "selected_full_id_raw"))
    _strings(raw, out, field, ("resolution_selection", "object_identity", "table_identity", "reason"))
    _bools(raw, out, field, ("direct_ready", "mapped_ready", "ready"), False)
    selection = out["resolution_selection"]
    if out["native_index"] != index or selection not in {None, "registry_full_id_8", "native_fallback"}:
        raise ValueError(field + " occurrence order/resolution selection invalid")
    if selection == "registry_full_id_8" and (
        out["requested_full_id_raw"] is None or out["selected_full_id_raw"] != out["requested_full_id_raw"]
    ):
        raise ValueError(field + " full-generation resolution disagrees")
    for key, nested in (("direct_rows", False), ("nested_rows", True)):
        out[key] = _slots(raw[key], field + "." + key, nested, rite, guard)
    resolved = selection is not None and out["object_identity"] is not None and out["table_identity"] is not None
    direct = resolved and out["direct_rows"] is not None and all(_pc_ready(row["pc"]) for row in out["direct_rows"])
    mapped = resolved and out["nested_rows"] is not None and all(row["mapped_family"]["ready"] for row in out["nested_rows"])
    if (out["direct_ready"], out["mapped_ready"], out["ready"]) != (direct, mapped, direct and mapped and out["reason"] is None):
        raise ValueError(field + " independent occurrence readiness disagrees")
    return out


def _list(value, field, name, land, death, rite, guard):
    raw, out = _start(value, field, {"direct_ready", "mapped_ready", "header_selection",
        "default_init_guard_raw", "count_raw", "numeric_count", "array_present", "rows"})
    _bools(raw, out, field, ("direct_ready", "mapped_ready"), False)
    _bools(raw, out, field, ("array_present",))
    _strings(raw, out, field, ("header_selection",))
    _words(raw, out, field, ("default_init_guard_raw", "count_raw", "numeric_count"))
    selection = out["header_selection"]
    current = "current_1c0_" + name[-3:]
    expected = current if land is True and death is False else (
        "default" if land is False or death is True else None)
    if selection not in {None, current, "inline_default_5d67e60", "modeled_empty_default_5d67e60"}:
        raise ValueError(field + " list header selection invalid")
    if selection is not None and (selection == current) != (expected == current):
        raise ValueError(field + " header selection disagrees with current1C0/1D0")
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        rows = [_occurrence(row, f"{field}.rows[{i}]", i, rite, guard) for i, row in enumerate(rows)]
    out["rows"] = rows
    count, numeric, default_guard = out["count_raw"], out["numeric_count"], out["default_init_guard_raw"]
    if selection == "modeled_empty_default_5d67e60":
        if default_guard not in {0, -1} or count is not None or numeric != 0 or out["array_present"] is not None or rows != []:
            raise ValueError(field + " modeled default contains physical operands or lacks observed guard")
        complete = True
    else:
        if count != numeric:
            raise ValueError(field + " numeric count disagrees with observed header")
        complete = selection is not None and count is not None and count >= 0 and rows is not None and len(rows) == count
        if count is not None and count > 0:
            complete = complete and out["array_present"] is True
        if selection == "inline_default_5d67e60":
            complete = complete and default_guard not in {None, 0, -1}
        if selection == current and default_guard is not None:
            raise ValueError(field + " current header contains undemanded default guard")
    direct = complete and all(row["direct_ready"] for row in rows)
    mapped = complete and all(row["mapped_ready"] for row in rows)
    if (out["direct_ready"], out["mapped_ready"], out["ready"]) != (direct, mapped, direct and mapped and out["reason"] is None):
        raise ValueError(field + " independent list readiness disagrees")
    return out


def normalize_provider192_and2920850(value, field=_FIELD):
    if value is None:
        return None
    raw, out = _start(value, field, {"character_id", "current_land_present", "current_death_present",
        "rite", "mapped_default_guard_raw", *FAMILIES_PROVIDER192_AND2920850_12003})
    out["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    _bools(raw, out, field, ("current_land_present", "current_death_present"))
    _words(raw, out, field, ("mapped_default_guard_raw",))
    out["rite"] = _rite(raw["rite"], field + ".rite")
    out["provider_192"] = _provider(raw["provider_192"], field + ".provider_192")
    for name in FAMILIES_PROVIDER192_AND2920850_12003[1:]:
        out[name] = _list(raw[name], field + "." + name, name, out["current_land_present"],
                          out["current_death_present"], out["rite"], out["mapped_default_guard_raw"])
    if out["ready"] != all(out[name]["ready"] for name in FAMILIES_PROVIDER192_AND2920850_12003):
        raise ValueError(field + " readiness disagrees with independent families")
    return out


def _current(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_provider192_and2920850(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return leaf, raw


def _indexed_occurrence(leaf, family, occurrence_index):
    if family not in FAMILIES_PROVIDER192_AND2920850_12003[1:]:
        raise ValueError("Slot/descriptor family must be list_168 or list_180")
    index = _integer(occurrence_index, "occurrence_index", 32)
    rows = leaf[family]["rows"]
    if rows is None or not 0 <= index < len(rows):
        raise ValueError("Required native input unavailable: occurrence")
    row = rows[index]
    if row["resolution_selection"] is None or row["object_identity"] is None or row["table_identity"] is None:
        raise ValueError("Required native input unavailable: occurrence table")
    return row


def emit_provider192_and2920850_requests_from_current_source_inputs_12003(section):
    leaf, raw = _current(section)
    return emit_provider192_and2920850_requests_12003(leaf, actual_leaf=raw)


def emit_provider192_and2920850_family_requests_from_current_source_inputs_12003(section, family):
    leaf, raw = _current(section)
    return emit_provider192_and2920850_family_requests_12003(leaf, family, actual_leaf=raw)


def emit_provider192_and2920850_slot_requests_from_current_source_inputs_12003(section, family, occurrence_index, slot_index):
    leaf, raw = _current(section)
    row = _indexed_occurrence(leaf, family, occurrence_index)
    slot = _integer(slot_index, "slot_index", 32)
    if not 0 <= slot < 8:
        raise ValueError("slot_index must be0..7")
    slots = row["direct_rows" if slot < 4 else "nested_rows"]
    item = None if slots is None else slots[slot if slot < 4 else slot - 4]
    complete = item is not None and (_pc_ready(item["pc"]) if slot < 4 else item["mapped_family"]["ready"])
    if not complete:
        raise ValueError("Required native input unavailable: slot")
    return emit_provider192_and2920850_slot_requests_12003(leaf, family, occurrence_index, slot, actual_leaf=raw)


def emit_provider192_and2920850_descriptor_requests_from_current_source_inputs_12003(
    section, family, occurrence_index, nested_index, descriptor_index,
):
    leaf, raw = _current(section)
    occurrence = _indexed_occurrence(leaf, family, occurrence_index)
    nested = _integer(nested_index, "nested_index", 32)
    index = _integer(descriptor_index, "descriptor_index", 32)
    slots = occurrence["nested_rows"]
    if not 0 <= nested < 4 or slots is None:
        raise ValueError("Required native input unavailable: nested slot")
    header = slots[nested]["mapped_family"]
    rows = header["rows"]
    if rows is None or not 0 <= index < len(rows):
        raise ValueError("Required native input unavailable: descriptor")
    row = rows[index]
    complete = (_membership_ready(leaf["rite"]) and row["source_identity"] is not None
        and row["key_identity"] is not None and row["admitted"] is not None and row["reason"] is None)
    if row["admitted"]:
        guard = leaf["mapped_default_guard_raw"]
        complete = (complete and row["key_magic_raw"] is not None and guard is not None
            and row["property_selection"] is not None and row["property_identity"] is not None
            and _properties_ready(row["property_block"]) and row["property_block"]["reason"] is None
            and (row["property_selection"] != _DEFAULT or guard not in {0, -1}))
    if not complete:
        raise ValueError("Required native input unavailable: descriptor")
    return emit_provider192_and2920850_descriptor_requests_12003(
        leaf, family, occurrence_index, nested, index, actual_leaf=raw)
