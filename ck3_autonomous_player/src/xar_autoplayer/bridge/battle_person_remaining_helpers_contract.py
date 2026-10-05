"""Current-person 291F550/291F940 source receipts and ordered unit requests.

The two helpers append to the same actor's model+10 recipient. These receipts
provide no preceding baseline, remaining caller stages or current-final replay.
"""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)


FAMILIES_291F550 = ("government_indexed", "culture_direct", "culture_mapped")
FAMILIES_291F940 = ("direct", "mapped")
_FIELD = "later_helpers_291f550_291f940"
_MAGIC = 0x4744624F
_MAP = "first_full_id_10_mapping"
_DEFAULT_550 = "inline_culture_mapped_default_5dc2380"
_DEFAULT_940 = "inline_nested_mapped_default_5dc21b0"
_RITE_I32 = ("first_key_b4_raw", "second_key_4b8_raw", "third_key_98_raw")
_RITE_SELECTIONS = ("first_selection", "second_selection", "third_selection")


def _pc_ready(block: dict | None) -> bool:
    return _properties_ready(block) and block["reason"] is None


def _selection(value: object, field: str, allowed: set[str]) -> str | None:
    result = _string(value, field, optional=True)
    if result is not None and result not in allowed:
        raise ValueError(field + " is invalid")
    return result


def _rite(value: object, field: str) -> dict:
    raw = _dict(value, field, {
        *_RITE_I32, *_RITE_SELECTIONS, "selected_identity", "membership_count",
        "membership_array_present", "membership_identities", "reason",
    })
    result = {
        "selected_identity": _string(raw["selected_identity"], field + ".selected_identity", optional=True),
        "membership_count": _number(raw["membership_count"], field + ".membership_count", 32),
        "membership_array_present": _boolean(raw["membership_array_present"], field + ".membership_array_present", optional=True),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    for key in _RITE_I32:
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in _RITE_SELECTIONS:
        result[key] = _selection(raw[key], field + "." + key,
                                 {"registry_full_id_8", "native_fallback"})
    identities = raw["membership_identities"]
    if identities is not None:
        if not isinstance(identities, list):
            raise ValueError(field + ".membership_identities must be a list or null")
        identities = [_string(item, f"{field}.membership_identities[{i}]")
                      for i, item in enumerate(identities)]
    result["membership_identities"] = identities
    return result


def _membership_ready(rite: dict) -> bool:
    count, identities = rite["membership_count"], rite["membership_identities"]
    return (rite["reason"] is None and rite["selected_identity"] is not None
            and all(rite[key] is not None for key in _RITE_SELECTIONS)
            and count is not None and count >= 0
            and rite["membership_array_present"] is not None
            and identities is not None and len(identities) == count
            and (count == 0 or rite["membership_array_present"]))


def _row(value: object, field: str, kind: str, default: str | None) -> dict:
    raw = _dict(value, field, {
        "native_index", "source_identity", "key_identity", "key_magic_raw",
        "key_full_id_raw", "admitted", "property_selection",
        "mapping_native_index", "property_identity", "property_block", "reason",
    })
    allowed = ({_MAP, default} if kind == "mapped" else
               {"government_indexed_1c0", "inline_government_default_5d65890"}
               if kind == "government" else {"direct_pc_pointer"})
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "key_magic_raw": _number(raw["key_magic_raw"], field + ".key_magic_raw", 32, unsigned=True),
        "key_full_id_raw": _number(raw["key_full_id_raw"], field + ".key_full_id_raw", 32),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "property_selection": _selection(raw["property_selection"], field + ".property_selection", allowed),
        "mapping_native_index": _number(raw["mapping_native_index"], field + ".mapping_native_index", 32),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
    }
    for key in ("source_identity", "key_identity", "property_identity", "reason"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    mapper_fields = ("key_magic_raw", "key_full_id_raw", "mapping_native_index")
    property_fields = ("property_selection", "property_identity", "property_block")
    if kind != "mapped":
        if result["key_identity"] is not None or any(result[key] is not None for key in mapper_fields):
            raise ValueError(field + " direct PC has no key or mapper operands")
        if result["admitted"] is False:
            raise ValueError(field + " direct PC has no additional admission gate")
    elif result["admitted"] is not True:
        if any(result[key] is not None for key in (*mapper_fields, *property_fields)):
            raise ValueError(field + " contains undemanded mapper or PC operands")
    elif result["property_selection"] == _MAP:
        if result["key_magic_raw"] != _MAGIC or result["key_full_id_raw"] is None:
            raise ValueError(field + " mapping selection lacks consumed full-ID operands")
        if result["mapping_native_index"] is None:
            raise ValueError(field + " mapping selection lacks native index")
    if result["admitted"] is not True and result["property_block"] is not None:
        raise ValueError(field + " contains an undemanded PC")
    return result


def _family(value: object, field: str, kind: str, *, rite: dict | None = None,
            default: str | None = None, guard: int | None = None) -> dict:
    raw = _dict(value, field, {
        "status", "ready", "admitted", "count", "array_present", "rows", "reason",
    })
    status, ready, reason = _availability(raw, field)
    admitted = _boolean(raw["admitted"], field + ".admitted", optional=True)
    count = _number(raw["count"], field + ".count", 32)
    array = _boolean(raw["array_present"], field + ".array_present", optional=True)
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        rows = [_row(item, f"{field}.rows[{i}]", kind, default)
                for i, item in enumerate(rows)]
        for i, row in enumerate(rows):
            if row["native_index"] != i:
                raise ValueError(field + ".rows native_index disagrees with stored order")
            mapped_index = row["mapping_native_index"]
            if mapped_index is not None:
                if count is None or not 0 <= mapped_index < count:
                    raise ValueError(field + ".rows mapping_native_index is outside native count")
                if mapped_index < len(rows):
                    selected_id = rows[mapped_index]["key_full_id_raw"]
                    if selected_id is not None and selected_id != row["key_full_id_raw"]:
                        raise ValueError(field + ".rows mapped full-ID disagrees")
            if kind == "mapped" and _membership_ready(rite) and row["key_identity"] is not None:
                if row["admitted"] != (row["key_identity"] in rite["membership_identities"]):
                    raise ValueError(field + ".rows admission disagrees with whole QWORD membership")
    if admitted is False:
        complete = count is None and array is None and rows == []
    elif kind == "government":
        complete = admitted is True and count == 1 and array is None and rows is not None and len(rows) == 1
    else:
        complete = (admitted is True and count is not None and count >= 0
                    and array is not None and rows is not None and len(rows) == count
                    and (count == 0 or array))
    if complete and admitted is True:
        complete = all(
            row["source_identity"] is not None and row["admitted"] is not None
            and row["reason"] is None
            and (kind != "mapped" or row["key_identity"] is not None)
            and (not row["admitted"] or (
                row["property_selection"] is not None and row["property_identity"] is not None
                and _pc_ready(row["property_block"])
                and (kind != "mapped" or (row["key_magic_raw"] is not None and guard is not None))
                and (row["property_selection"] not in {
                    default, "inline_government_default_5d65890"
                } or guard not in {None, 0, -1})
            )) for row in rows
        )
        if kind == "mapped" and count > 0:
            complete = complete and _membership_ready(rite)
    complete = complete and reason is None
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed family operands")
    return {"status": status, "ready": ready, "admitted": admitted,
            "count": count, "array_present": array, "rows": rows, "reason": reason}


def _helper_550(value: object, field: str) -> dict:
    strings = ("culture_selection", "culture_identity", "government_selection", "government_identity")
    words = ("culture_key_b0_raw", "culture_full_id_raw", "government_full_id_raw",
             "government_default_guard_raw", "mapped_default_guard_raw")
    raw = _dict(value, field, {
        "status", "ready", *strings, *words, "culture_magic_raw",
        "government_magic_raw", "admitted", "rite", *FAMILIES_291F550, "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True)}
    for key in strings:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in words:
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("culture_magic_raw", "government_magic_raw"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    magic, culture_id = result["culture_magic_raw"], result["culture_full_id_raw"]
    actual = (None if magic is None else False if magic != 0x43756C74
              else culture_id != -1 if culture_id is not None else None)
    if result["admitted"] != actual:
        raise ValueError(field + ".admitted disagrees with native Culture gate")
    result["rite"] = _rite(raw["rite"], field + ".rite")
    for family, kind in (("government_indexed", "government"), ("culture_direct", "direct"),
                         ("culture_mapped", "mapped")):
        guard = result["government_default_guard_raw" if kind == "government" else "mapped_default_guard_raw"]
        result[family] = _family(raw[family], field + "." + family, kind,
                                 rite=result["rite"], default=_DEFAULT_550, guard=guard)
        if result[family]["admitted"] != actual:
            raise ValueError(field + "." + family + " disagrees with Culture admission")
    if actual is False:
        if any(result[key] is not None for key in (
            "government_selection", "government_identity", "government_magic_raw",
            "government_full_id_raw", "government_default_guard_raw", "mapped_default_guard_raw",
        )) or any(value is not None for value in result["rite"].values()):
            raise ValueError(field + " skipped Culture contains undemanded helper operands")
    complete = (result["culture_selection"] is not None and result["culture_identity"] is not None
                and actual is not None and all(result[key]["ready"] for key in FAMILIES_291F550))
    if ready != complete:
        raise ValueError(field + " availability disagrees with three current families")
    return result


def _helper_940(value: object, field: str) -> dict:
    raw = _dict(value, field, {
        "status", "ready", "direct_ready", "mapped_ready", "first_key_158_raw",
        "first_selection", "second_key_2c_raw", "second_selection", "selected_identity",
        "outer_count", "outer_array_present", "outer_rows", "mapped_default_guard_raw",
        "rite", "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "direct_ready": _boolean(raw["direct_ready"], field + ".direct_ready"),
              "mapped_ready": _boolean(raw["mapped_ready"], field + ".mapped_ready"),
              "outer_array_present": _boolean(raw["outer_array_present"], field + ".outer_array_present", optional=True),
              "rite": _rite(raw["rite"], field + ".rite")}
    for key in ("first_key_158_raw", "second_key_2c_raw", "outer_count", "mapped_default_guard_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("first_selection", "second_selection", "selected_identity"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    rows = raw["outer_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".outer_rows must be a list or null")
        copied = []
        for i, value in enumerate(rows):
            name = f"{field}.outer_rows[{i}]"
            row = _dict(value, name, {
                "native_index", "source_identity", "direct_gate_raw", "direct_admitted",
                "direct_property_identity", "direct_property_block", "direct_reason", "inner_mapped",
            })
            gate = _number(row["direct_gate_raw"], name + ".direct_gate_raw", 32)
            admission = _boolean(row["direct_admitted"], name + ".direct_admitted", optional=True)
            if admission != (gate != 0 if gate is not None else None):
                raise ValueError(name + ".direct_admitted disagrees with signed32 nonzero")
            index = _integer(row["native_index"], name + ".native_index", 32)
            if index != i:
                raise ValueError(name + ".native_index disagrees with stored order")
            block = _properties(row["direct_property_block"], name + ".direct_property_block")
            identity = _string(row["direct_property_identity"], name + ".direct_property_identity", optional=True)
            if admission is not True and (block is not None or identity is not None):
                raise ValueError(name + " contains an undemanded direct PC")
            copied.append({
                "native_index": index, "source_identity": _string(row["source_identity"], name + ".source_identity", optional=True),
                "direct_gate_raw": gate, "direct_admitted": admission,
                "direct_property_identity": identity, "direct_property_block": block,
                "direct_reason": _string(row["direct_reason"], name + ".direct_reason", optional=True),
                "inner_mapped": _family(row["inner_mapped"], name + ".inner_mapped", "mapped",
                                         rite=result["rite"], default=_DEFAULT_940,
                                         guard=result["mapped_default_guard_raw"]),
            })
        rows = copied
    result["outer_rows"] = rows
    count, array = result["outer_count"], result["outer_array_present"]
    header_ready = (all(result[key] is not None for key in ("first_selection", "second_selection", "selected_identity"))
                    and count is not None and count >= 0 and array is not None
                    and rows is not None and len(rows) == count and (count == 0 or array))
    direct_ready = header_ready and all(
        row["source_identity"] is not None and row["direct_admitted"] is not None
        and row["direct_reason"] is None and (not row["direct_admitted"] or (
            row["direct_property_identity"] is not None and _pc_ready(row["direct_property_block"])
        )) for row in rows
    )
    mapped_ready = header_ready and all(row["source_identity"] is not None
                                       and row["inner_mapped"]["ready"] for row in rows)
    if result["direct_ready"] != direct_ready or result["mapped_ready"] != mapped_ready:
        raise ValueError(field + " independent availability disagrees with outer/inner operands")
    if ready != (direct_ready and mapped_ready):
        raise ValueError(field + " availability disagrees with direct and mapped families")
    return result


def normalize_later_helpers_291f550_291f940(value: object, field: str = _FIELD) -> dict | None:
    """Retain exact native words, pointer identities and independent readiness."""
    if value is None:
        return None
    raw = _dict(value, field, {"status", "ready", "character_id", "helper_291f550", "helper_291f940", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "character_id": _integer(raw["character_id"], field + ".character_id", 32),
              "helper_291f550": _helper_550(raw["helper_291f550"], field + ".helper_291f550"),
              "helper_291f940": _helper_940(raw["helper_291f940"], field + ".helper_291f940")}
    if ready != (result["helper_291f550"]["ready"] and result["helper_291f940"]["ready"]):
        raise ValueError(field + " availability disagrees with the two helpers")
    return result


def _current(section: dict | None) -> tuple[dict, dict]:
    value = None if section is None else section.get(_FIELD)
    helper = normalize_later_helpers_291f550_291f940(value)
    if helper is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    actor = _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32)
    if helper["character_id"] != actor:
        raise ValueError(_FIELD + " character disagrees with source actor")
    return helper, value


def _request(ordinal: int, name: str, row: dict, block: object):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return NativeWeightedContributionRequest12003(
        source_ordinal=ordinal, source_name=name, first_row_index=row["native_index"],
        row_count=1, definition_identity=row["property_identity"],
        base_property_block=block, weight_q64=100000,
    )


def emit_helper_291f550_family_requests_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    """Emit one independently available 550 family, keeping each occurrence."""
    if family not in FAMILIES_291F550:
        raise ValueError("Unknown helper291F550 family")
    helper, raw = _current(section)
    current = helper["helper_291f550"][family]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: helper_291f550." + family)
    return tuple(_request(FAMILIES_291F550.index(family), "291f550_" + family, row,
                          raw["helper_291f550"][family]["rows"][row["native_index"]]["property_block"])
                 for row in current["rows"] if row["admitted"])


def emit_helper_291f550_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Emit government indexed, culture direct, then culture mapped."""
    helper, _ = _current(section)
    if not helper["helper_291f550"]["ready"]:
        raise ValueError("Required native input unavailable: helper_291f550")
    return tuple(request for family in FAMILIES_291F550
                 for request in emit_helper_291f550_family_requests_from_current_source_inputs_12003(section, family))


def _requests_940(helper: dict, raw: dict, families: tuple[str, ...]) -> tuple:
    requests = []
    for outer in helper["outer_rows"]:
        index = outer["native_index"]
        actual = raw["outer_rows"][index]
        if "direct" in families and outer["direct_admitted"]:
            requests.append(_request(index, "291f940_direct160", {
                "native_index": 0, "property_identity": outer["direct_property_identity"],
            }, actual["direct_property_block"]))
        if "mapped" in families:
            requests.extend(_request(index, "291f940_inner450", row,
                                     actual["inner_mapped"]["rows"][row["native_index"]]["property_block"])
                            for row in outer["inner_mapped"]["rows"] if row["admitted"])
    return tuple(requests)


def emit_helper_291f940_family_requests_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    """Emit direct or mapped independently; ordinal retains the outer index."""
    if family not in FAMILIES_291F940:
        raise ValueError("Unknown helper291F940 family")
    helper, raw = _current(section)
    current = helper["helper_291f940"]
    if not current[family + "_ready"]:
        raise ValueError("Required native input unavailable: helper_291f940." + family)
    return _requests_940(current, raw["helper_291f940"], (family,))


def emit_helper_291f940_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Interleave each outer direct160 request and that outer's inner450 rows."""
    helper, raw = _current(section)
    current = helper["helper_291f940"]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: helper_291f940")
    return _requests_940(current, raw["helper_291f940"], FAMILIES_291F940)


def emit_later_helpers_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Emit 550 then interleaved 940; preceding/following stages remain separate."""
    helper, _ = _current(section)
    if not helper["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    return (emit_helper_291f550_requests_from_current_source_inputs_12003(section)
            + emit_helper_291f940_requests_from_current_source_inputs_12003(section))
