"""Current caller291C3FB/291C44C inputs, after the separate291F0A0 helper.

This emits ordered unit requests only. It supplies neither the preceding helper
nor a prepared baseline, and never rebuilds an observed current final context.
"""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)


def normalize_later_direct_291c3fb_44c(value: object, field: str) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", "ordered_header_selection",
        "ordered_count", "ordered_array_present", "ordered_rows",
        "guarded_selection", "guarded_magic_raw", "guarded_admitted",
        "guarded_property_block", "reason",
    })
    status, ready, reason = _availability(raw, field)
    count = _number(raw["ordered_count"], field + ".ordered_count", 32)
    array_present = _boolean(raw["ordered_array_present"],
                             field + ".ordered_array_present", optional=True)
    header = _string(raw["ordered_header_selection"],
                     field + ".ordered_header_selection", optional=True)
    if header not in {None, "character_1b0_inline_98", "inline_static_545a3e8"}:
        raise ValueError(field + ".ordered_header_selection is invalid")
    rows = raw["ordered_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".ordered_rows must be a list or null")
        copied = []
        for i, value in enumerate(rows):
            name = f"{field}.ordered_rows[{i}]"
            r = _dict(value, name, {
                "native_index", "requested_full_id_raw", "selection",
                "selected_identity", "selected_field_24c_raw", "admitted",
                "property_block", "reason",
            })
            index = _integer(r["native_index"], name + ".native_index", 32)
            if index != i:
                raise ValueError(name + ".native_index disagrees with stored order")
            selection = _string(r["selection"], name + ".selection", optional=True)
            if selection not in {None, "registry_full_id", "native_fallback"}:
                raise ValueError(name + ".selection is invalid")
            word = _number(r["selected_field_24c_raw"], name + ".selected_field_24c_raw", 32)
            admitted = _boolean(r["admitted"], name + ".admitted", optional=True)
            if admitted != (word != 0 if word is not None else None):
                raise ValueError(name + ".admitted disagrees with signed32 nonzero")
            block = _properties(r["property_block"], name + ".property_block")
            if admitted is not True and block is not None:
                raise ValueError(name + " contains an undemanded +80 property")
            copied.append({
                "native_index": index,
                "requested_full_id_raw": _number(r["requested_full_id_raw"], name + ".requested_full_id_raw", 32),
                "selection": selection,
                "selected_identity": _string(r["selected_identity"], name + ".selected_identity", optional=True),
                "selected_field_24c_raw": word, "admitted": admitted,
                "property_block": block,
                "reason": _string(r["reason"], name + ".reason", optional=True),
            })
        rows = copied
    magic = _number(raw["guarded_magic_raw"], field + ".guarded_magic_raw", 32, unsigned=True)
    guarded = _boolean(raw["guarded_admitted"], field + ".guarded_admitted", optional=True)
    if guarded != (magic == 0x4744624F if magic is not None else None):
        raise ValueError(field + ".guarded_admitted disagrees with magic DWORD")
    block = _properties(raw["guarded_property_block"], field + ".guarded_property_block")
    if guarded is not True and block is not None:
        raise ValueError(field + " contains an undemanded +AA0 property")
    selection = _string(raw["guarded_selection"], field + ".guarded_selection", optional=True)
    if selection not in {None, "character_1c0_pointer_388", "native_fallback"}:
        raise ValueError(field + ".guarded_selection is invalid")
    ordered_ready = (header is not None and count is not None and count >= 0
                     and array_present is not None and rows is not None
                     and len(rows) == count and (count == 0 or array_present))
    if ordered_ready:
        ordered_ready = all(
            r["requested_full_id_raw"] is not None and r["selection"] is not None
            and r["selected_identity"] is not None and r["admitted"] is not None
            and r["reason"] is None
            and (not r["admitted"] or _properties_ready(r["property_block"]))
            for r in rows
        )
    complete = (ordered_ready and selection is not None and guarded is not None
                and (not guarded or _properties_ready(block)))
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed direct operands")
    return {
        "status": status, "ready": ready,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "ordered_header_selection": header, "ordered_count": count,
        "ordered_array_present": array_present, "ordered_rows": rows,
        "guarded_selection": selection, "guarded_magic_raw": magic,
        "guarded_admitted": guarded, "guarded_property_block": block,
        "reason": reason,
    }


def emit_later_direct_requests_from_current_source_inputs_12003(
    normalized_section: dict | None,
) -> tuple:
    """Preserve each native occurrence, then AA0; no helper/baseline implied."""
    from ..simulation.battle_context_preparation_branch_291e210_12003 import (
        NativeWeightedContributionRequest12003,
    )
    value = None if normalized_section is None else normalized_section.get("later_direct_291c3fb_44c")
    branch = normalize_later_direct_291c3fb_44c(value, "later_direct_291c3fb_44c")
    if branch is None or not branch["ready"]:
        raise ValueError("Required native input unavailable: later_direct_291c3fb_44c")
    requests = [
        NativeWeightedContributionRequest12003(
            source_ordinal=0, source_name="ordered_291c3fb_80",
            first_row_index=r["native_index"], row_count=1,
            definition_identity=r["selected_identity"],
            base_property_block=value["ordered_rows"][r["native_index"]]["property_block"],
            weight_q64=100000,
        ) for r in branch["ordered_rows"] if r["admitted"]
    ]
    if branch["guarded_admitted"]:
        requests.append(NativeWeightedContributionRequest12003(
            source_ordinal=1, source_name="guarded_291c44c_aa0", first_row_index=0,
            row_count=1, definition_identity="guarded_291c44c",
            base_property_block=value["guarded_property_block"], weight_q64=100000,
        ))
    return tuple(requests)
