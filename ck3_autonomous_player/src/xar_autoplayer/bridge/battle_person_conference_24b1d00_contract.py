from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)

_FIELD = "conference_24b1d00"
FAMILIES_24B1D00 = ("classified_owner", "classified_common", "owner_common", "unconditional")
_CATEGORY_OFFSETS = {
    "same_id": (0x30, 0x1F0, 0x3B0),
    "same_identity": (0xAB0, 0xC70, 0xE30),
    "different": (0xFF0, 0x11B0, 0x1370),
}


def _object(value: object, field: str, id_offset: int) -> dict:
    raw = _dict(value, field, {
        "requested_full_id_raw", "selection", "identity", "full_id_raw", "reason",
    })
    result = {key: _number(raw[key], field + "." + key, 32)
              for key in ("requested_full_id_raw", "full_id_raw")}
    result.update({key: _string(raw[key], field + "." + key, optional=True)
                   for key in ("selection", "identity", "reason")})
    if result["selection"] not in {None, "native_fallback", f"registry_full_id_{id_offset:x}"}:
        raise ValueError(field + ".selection is invalid")
    if result["selection"] is not None and result["identity"] is None:
        raise ValueError(field + " selected object lacks its actual identity")
    if result["selection"] == f"registry_full_id_{id_offset:x}" and (
        result["requested_full_id_raw"] is None or result["full_id_raw"] != result["requested_full_id_raw"]
    ):
        raise ValueError(field + " registry selection disagrees with exact full ID")
    return result


def _pack(value: object, field: str) -> dict:
    strings = ("configuration_identity", "selection", "pack_identity")
    raw = _dict(value, field, {
        "status", "ready", *strings, "target_q64", "enabled_u8", "count_raw",
        "array_present", "probes", "selected_native_index", "default_guard_raw", "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason}
    result.update({key: _string(raw[key], field + "." + key, optional=True) for key in strings})
    for key in ("count_raw", "selected_native_index", "default_guard_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    result["target_q64"] = _number(raw["target_q64"], field + ".target_q64", 64)
    result["enabled_u8"] = _number(raw["enabled_u8"], field + ".enabled_u8", 8, unsigned=True)
    result["array_present"] = _boolean(raw["array_present"], field + ".array_present", optional=True)
    probes = raw["probes"]
    if probes is not None:
        if not isinstance(probes, list):
            raise ValueError(field + ".probes must be a list or null")
        copied = []
        for i, item in enumerate(probes):
            name = f"{field}.probes[{i}]"
            probe = _dict(item, name, {"native_index", "timestamp_q64"})
            copied.append({"native_index": _integer(probe["native_index"], name + ".native_index", 32),
                           "timestamp_q64": _integer(probe["timestamp_q64"], name + ".timestamp_q64", 64)})
        probes = copied
    result["probes"] = probes
    flag, count, target = result["enabled_u8"], result["count_raw"], result["target_q64"]
    selected = result["selected_native_index"]
    selection = result["selection"]
    if selection not in {None, "last_native_row_at_or_before_target", "inline_default_54ebab0"}:
        raise ValueError(field + ".selection is invalid")
    known_selection = None
    if flag == 0:
        if any(result[key] is not None for key in ("count_raw", "array_present", "probes", "selected_native_index")):
            raise ValueError(field + " disabled pack contains undemanded row operands")
        known_selection = "inline_default_54ebab0"
    elif flag is not None and count is not None and count >= 0 and probes is not None and target is not None:
        if len(probes) > count:
            raise ValueError(field + " probes exceed native row count")
        match = None
        for i, probe in enumerate(probes):
            if probe["native_index"] != count - 1 - i:
                raise ValueError(field + " probes disagree with backward native order")
            if probe["timestamp_q64"] <= target:
                if i != len(probes) - 1:
                    raise ValueError(field + " probes continue after the last qualifying row")
                match = probe["native_index"]
        if match is not None:
            known_selection = "last_native_row_at_or_before_target"
            if selected != match:
                raise ValueError(field + " selection is not the last qualifying native row")
        elif len(probes) == count:
            known_selection = "inline_default_54ebab0"
    if selection is not None and selection != known_selection:
        raise ValueError(field + " selected pack disagrees with consumed probes")
    if selection != "last_native_row_at_or_before_target" and selected is not None:
        raise ValueError(field + " default or unavailable pack contains an index")
    if selection == "last_native_row_at_or_before_target" and result["default_guard_raw"] is not None:
        raise ValueError(field + " mapped pack contains an unused inline guard")
    complete = (result["configuration_identity"] is not None and target is not None and flag is not None
                and selection is not None and result["pack_identity"] is not None
                and (selection != "last_native_row_at_or_before_target" or result["array_present"] is True)
                and (selection != "inline_default_54ebab0" or result["default_guard_raw"] not in {None, 0, -1})
                and reason is None)
    if ready != complete:
        raise ValueError(field + " availability disagrees with selected pack operands")
    return result


def _gate(magic: int | None, full_id: int | None, expected: int) -> bool | None:
    if magic is None:
        return None
    if magic != expected:
        return False
    return None if full_id is None else full_id != -1


def _family(value: object, field: str, index: int, helper: dict, offset: int | None) -> dict:
    raw = _dict(value, field, {
        "status", "ready", "native_index", "admitted", "pc_offset", "property_identity", "property_block", "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
              "pc_offset": _number(raw["pc_offset"], field + ".pc_offset", 32, unsigned=True),
              "property_identity": _string(raw["property_identity"], field + ".property_identity", optional=True),
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    if result["native_index"] != index or result["admitted"] != helper["admitted"]:
        raise ValueError(field + " native order or admission disagrees")
    if helper["admitted"] is not True:
        if any(result[key] is not None for key in ("pc_offset", "property_identity", "property_block")):
            raise ValueError(field + " skipped family contains undemanded properties")
        complete = helper["admitted"] is False
    else:
        if result["pc_offset"] != offset:
            raise ValueError(field + " PC offset disagrees with raw family predicate")
        pc = result["property_block"]
        complete = (helper["pack"]["ready"] and offset is not None and result["property_identity"] is not None
                    and _properties_ready(pc) and pc["reason"] is None and reason is None)
    if ready != complete:
        raise ValueError(field + " availability disagrees with independent family operands")
    return result


def normalize_conference_24b1d00(value: object, field: str = _FIELD) -> dict | None:
    if value is None:
        return None
    bools = ("carrier_present", "conference_admitted", "character_admitted", "admitted",
             "relation_registry_present", "owner_matches")
    strings = ("first_group_identity", "second_group_identity", "category")
    raw = _dict(value, field, {
        "status", "ready", "character_id", *bools, *strings, "conference", "conference_magic_raw",
        "character_magic_raw", "character_full_id_raw", "pack", "first", "second", "owner_full_id_raw", "families", "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "character_id": _integer(raw["character_id"], field + ".character_id", 32),
              "conference": _object(raw["conference"], field + ".conference", 8),
              "first": _object(raw["first"], field + ".first", 0x10),
              "second": _object(raw["second"], field + ".second", 0x10),
              "pack": _pack(raw["pack"], field + ".pack")}
    result.update({key: _boolean(raw[key], field + "." + key, optional=True) for key in bools})
    result.update({key: _string(raw[key], field + "." + key, optional=True) for key in strings})
    for key in ("conference_magic_raw", "character_magic_raw"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    for key in ("character_full_id_raw", "owner_full_id_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    conf_gate = _gate(result["conference_magic_raw"], result["conference"]["full_id_raw"], 0x436F6E66)
    char_gate = _gate(result["character_magic_raw"], result["character_full_id_raw"], 0x43686172)
    if result["conference_admitted"] != conf_gate or result["character_admitted"] != char_gate:
        raise ValueError(field + " admission disagrees with native magic/full ID gates")
    if conf_gate is not True and any(result[key] is not None for key in (
        "character_magic_raw", "character_full_id_raw", "character_admitted")):
        raise ValueError(field + " skipped helper contains undemanded Character gate operands")
    if result["character_magic_raw"] not in {None, 0x43686172} and result["character_full_id_raw"] is not None:
        raise ValueError(field + " wrong Character magic contains an undemanded ID")
    admission = False if conf_gate is False else char_gate if conf_gate is True else None
    if result["admitted"] != admission:
        raise ValueError(field + " helper admission disagrees")
    first, second = result["first"]["full_id_raw"], result["second"]["full_id_raw"]
    category = None
    if first is not None and second is not None:
        if first == second:
            category = "same_id"
            if any(result[key] is not None for key in strings[:2]):
                raise ValueError(field + " equal IDs contain undemanded group identities")
        elif all(result[key] is not None for key in strings[:2]):
            category = "same_identity" if result["first_group_identity"] == result["second_group_identity"] else "different"
    if result["category"] != category:
        raise ValueError(field + " category disagrees with full ID/QWORD equality")
    owner, character = result["owner_full_id_raw"], result["character_full_id_raw"]
    owner_matches = owner == character if owner is not None and character is not None else None
    if result["owner_matches"] != owner_matches:
        raise ValueError(field + " owner predicate disagrees with raw full DWORDs")
    if admission is not True and (category is not None or owner is not None or result["pack"]["selection"] is not None):
        raise ValueError(field + " unadmitted helper contains consumed pack/relation operands")
    if result["relation_registry_present"] is False and any(result[key]["requested_full_id_raw"] is not None for key in ("first", "second")):
        raise ValueError(field + " null relation registry contains undemanded keys")
    offsets = [None, None, None, None]
    if admission is True:
        offsets[3] = 0x8F0
        if owner_matches is not None:
            offsets[2] = 0x570 if owner_matches else 0x730
        if category is not None:
            owned, other, common = _CATEGORY_OFFSETS[category]
            offsets[1] = common
            if owner_matches is not None:
                offsets[0] = owned if owner_matches else other
    families = raw["families"]
    if not isinstance(families, list) or len(families) != 4:
        raise ValueError(field + ".families must contain four native request families")
    result["families"] = [_family(row, f"{field}.families[{i}]", i, result, offsets[i]) for i, row in enumerate(families)]
    if ready != all(row["ready"] for row in result["families"]):
        raise ValueError(field + " availability disagrees with four independent families")
    return result


def _current(section: dict | None) -> tuple[dict, dict]:
    raw = None if section is None else section.get(_FIELD)
    helper = normalize_conference_24b1d00(raw)
    if helper is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if helper["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return helper, raw


def emit_conference_24b1d00_family_requests_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    if family not in FAMILIES_24B1D00:
        raise ValueError("Unknown conference24B1D00 family")
    helper, raw = _current(section)
    index = FAMILIES_24B1D00.index(family)
    row = helper["families"][index]
    if not row["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD + "." + family)
    if not row["admitted"]:
        return ()
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return (NativeWeightedContributionRequest12003(
        source_ordinal=index, source_name="24b1d00_" + family, first_row_index=0, row_count=1,
        definition_identity=row["property_identity"],
        base_property_block=raw["families"][index]["property_block"], weight_q64=100000),)


def emit_conference_24b1d00_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    helper, _ = _current(section)
    if not helper["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    return tuple(request for family in FAMILIES_24B1D00
                 for request in emit_conference_24b1d00_family_requests_from_current_source_inputs_12003(section, family))
