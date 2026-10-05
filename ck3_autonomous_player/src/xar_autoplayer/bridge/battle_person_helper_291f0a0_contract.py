"""Current helper291F0A0 four ordered families; no lazy initializer or baseline."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)

FAMILIES_291F0A0 = (
    "primary_direct", "manager_range", "source_a18", "conditional_direct",
)
_STRINGS = (
    "first_selection", "manager_definition_selection", "manager_definition_identity",
    "recipient_source", "range_selection",
)
_I32 = (
    "first_key_b4_raw", "range_count_raw", "range_native_index",
    "default_pc_guard_raw", "pointer_list_guard_raw",
    "predicate_character_15c_raw", "predicate_first_key_b4_raw",
    "predicate_second_key_4b8_raw", "predicate_second_a0_raw",
)
_I64 = ("recipient_q64", "range_lower_q64", "range_upper_q64")


def _family(value: object, field: str, family: str) -> dict:
    raw = _dict(value, field, {
        "status", "ready", "selected_source", "admitted", "count",
        "array_present", "rows", "reason",
    })
    status, ready, reason = _availability(raw, field)
    admitted = _boolean(raw["admitted"], field + ".admitted", optional=True)
    count = _number(raw["count"], field + ".count", 32)
    array = _boolean(raw["array_present"], field + ".array_present", optional=True)
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        result = []
        for i, value in enumerate(rows):
            name = f"{field}.rows[{i}]"
            r = _dict(value, name, {
                "native_index", "source_identity", "gate_raw", "admitted",
                "property_block", "reason",
            })
            index = _integer(r["native_index"], name + ".native_index", 32)
            if index != i:
                raise ValueError(name + ".native_index disagrees with stored order")
            gate = _number(r["gate_raw"], name + ".gate_raw", 32)
            row_admitted = _boolean(r["admitted"], name + ".admitted", optional=True)
            if family in {"manager_range", "source_a18"}:
                if row_admitted != (gate != 0 if gate is not None else None):
                    raise ValueError(name + ".admitted disagrees with native nonzero gate")
            elif gate is not None or row_admitted not in {None, True}:
                raise ValueError(name + " direct PC occurrence has no additional gate")
            block = _properties(r["property_block"], name + ".property_block")
            if row_admitted is not True and block is not None:
                raise ValueError(name + " contains an undemanded PC")
            result.append({
                "native_index": index, "source_identity": _string(
                    r["source_identity"], name + ".source_identity", optional=True),
                "gate_raw": gate, "admitted": row_admitted, "property_block": block,
                "reason": _string(r["reason"], name + ".reason", optional=True),
            })
        rows = result
    if admitted is False:
        complete = count is None and array is None and rows == []
    elif family == "manager_range":
        complete = (admitted is True and rows is not None and len(rows) == 1
                    and count is not None and rows[0]["gate_raw"] == count
                    and array is None)
    else:
        complete = (admitted is True and count is not None and count >= 0
                    and array is not None and rows is not None and len(rows) == count
                    and (count == 0 or array))
    if complete and admitted is True:
        complete = all(r["source_identity"] is not None and r["admitted"] is not None
                       and r["reason"] is None
                       and (not r["admitted"] or _properties_ready(r["property_block"]))
                       for r in rows)
    # An actually uninitialized lazy static header can have zero counts. The
    # producer retains those current bytes and an initialization reason.
    complete = complete and reason is None
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed family operands")
    return {
        "status": status, "ready": ready,
        "selected_source": _string(raw["selected_source"], field + ".selected_source"),
        "admitted": admitted, "count": count, "array_present": array,
        "rows": rows, "reason": reason,
    }


def normalize_helper_291f0a0(value: object, field: str) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", *_STRINGS, *_I32, *_I64,
        "manager_present", "predicate_admitted", *FAMILIES_291F0A0, "reason",
    })
    status, ready, reason = _availability(raw, field)
    normalized = {
        "status": status, "ready": ready, "reason": reason,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "manager_present": _boolean(raw["manager_present"], field + ".manager_present", optional=True),
        "predicate_admitted": _boolean(raw["predicate_admitted"], field + ".predicate_admitted", optional=True),
    }
    for key in _STRINGS:
        normalized[key] = _string(raw[key], field + "." + key, optional=True)
    for keys, bits in ((_I32, 32), (_I64, 64)):
        for key in keys:
            normalized[key] = _number(raw[key], field + "." + key, bits)
    for family in FAMILIES_291F0A0:
        normalized[family] = _family(raw[family], field + "." + family, family)
    character = normalized["predicate_character_15c_raw"]
    second = normalized["predicate_second_a0_raw"]
    predicate = False if character == -1 else (character == second if character is not None and second is not None else None)
    if normalized["predicate_admitted"] != predicate:
        raise ValueError(field + ".predicate_admitted disagrees with exact DWORD equality")
    if character == -1 and any(normalized[key] is not None for key in (
        "predicate_first_key_b4_raw", "predicate_second_key_4b8_raw",
        "predicate_second_a0_raw",
    )):
        raise ValueError(field + " early predicate false contains undemanded operands")
    if normalized["conditional_direct"]["admitted"] != predicate:
        raise ValueError(field + ".conditional_direct disagrees with native AL gate")
    if ready != all(normalized[f]["ready"] for f in FAMILIES_291F0A0):
        raise ValueError(field + " availability disagrees with four current families")
    if normalized["manager_present"] is False and normalized["manager_range"]["ready"]:
        raise ValueError(field + " actual lazy null manager cannot provide ready range PC")
    if normalized["recipient_source"] == "absent_1c8_2bfac30_unobserved":
        if normalized["recipient_q64"] is not None or normalized["manager_range"]["ready"]:
            raise ValueError(field + " missing absent-carrier contribution inputs cannot establish recipient")
    return normalized


def emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(
    normalized_section: dict | None, family: str,
) -> tuple:
    """Emit one independently available native family; every occurrence remains."""
    from ..simulation.battle_context_preparation_branch_291e210_12003 import (
        NativeWeightedContributionRequest12003,
    )
    if family not in FAMILIES_291F0A0:
        raise ValueError("Unknown helper291F0A0 family")
    value = None if normalized_section is None else normalized_section.get("helper_291f0a0")
    helper = normalize_helper_291f0a0(value, "helper_291f0a0")
    if helper is None or not helper[family]["ready"]:
        raise ValueError("Required native input unavailable: helper_291f0a0." + family)
    return tuple(
        NativeWeightedContributionRequest12003(
            source_ordinal=FAMILIES_291F0A0.index(family), source_name="291f0a0_" + family,
            first_row_index=r["native_index"], row_count=1,
            definition_identity=r["source_identity"],
            base_property_block=value[family]["rows"][r["native_index"]]["property_block"],
            weight_q64=100000,
        ) for r in helper[family]["rows"] if r["admitted"]
    )


def emit_helper_291f0a0_requests_from_current_source_inputs_12003(
    normalized_section: dict | None,
) -> tuple:
    """All four families in native order; no prepared baseline or suffix claim."""
    value = None if normalized_section is None else normalized_section.get("helper_291f0a0")
    helper = normalize_helper_291f0a0(value, "helper_291f0a0")
    if helper is None or not helper["ready"]:
        raise ValueError("Required native input unavailable: helper_291f0a0")
    return tuple(r for family in FAMILIES_291F0A0
                 for r in emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(
                     normalized_section, family))
