"""Optional real target-union preparation inputs from one Strength sample."""
from __future__ import annotations

from .army_fixed_chunk0_preparation_contract import (
    _integer, _status, normalize_fixed_chunk0_preparation_persistent_v1,
)

_KEYS = {
    "source", "entry_kind", "scope_kind", "status", "ready", "unavailable_reason",
    "source_scope_status", "subject_army_id", "subject_carmy_id", "province_id",
    "target_persistent_ids_complete", "persistent_regiments",
}


def normalize_ordered_besieging_fixed_chunk0_preparation_inputs_v1(
    value: object, *, expected_army_id: int, expected_carmy_id: int,
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("ordered B fixed chunk0 preparation schema is malformed")
    if (value["source"] != "native_ordered_besieging_fixed_chunk0_preparation_inputs"
            or value["entry_kind"] != "current_frozen_context_preparation"
            or value["scope_kind"] != "actual_ordered_besieging_target_physical_union"):
        raise ValueError("ordered B fixed chunk0 preparation source/scope is malformed")
    _status(value, "ordered B family")
    if value["source_scope_status"] not in ("available", "partial", "unavailable"):
        raise ValueError("ordered B fixed chunk0 source scope status is malformed")
    for key in ("subject_army_id", "subject_carmy_id", "province_id"):
        _integer(value[key], 32, key)
    if (value["subject_army_id"] != expected_army_id
            or value["subject_carmy_id"] != expected_carmy_id):
        raise ValueError("ordered B fixed chunk0 preparation subject differs")
    if type(value["target_persistent_ids_complete"]) is not bool:
        raise ValueError("ordered B fixed chunk0 target scope completeness must be bool")
    if not isinstance(value["persistent_regiments"], list):
        raise ValueError("ordered B fixed chunk0 persistent rows must be a list")
    rows = [normalize_fixed_chunk0_preparation_persistent_v1(row)
            for row in value["persistent_regiments"]]
    if value["ready"] and (not value["target_persistent_ids_complete"]
                           or any(not row["ready"] for row in rows)):
        raise ValueError("available ordered B fixed chunk0 preparation family is incomplete")
    return {**value, "persistent_regiments": rows}
