"""Optional current-frame inputs for native persistent physical chunk0 preparation."""
from __future__ import annotations

_SOURCE = "native_scoped_fixed_chunk0_preparation_inputs"
_ENTRY = "current_frozen_context_preparation"
_OPERANDS = (
    "containing_guard_138_raw", "containing_definition_magic_38",
    "native_fixed_chunk0_can_replenish", "fresh_fraction_raw",
)
_ROW_KEYS = set(_OPERANDS) | {
    "persistent_regiment_id", "fixed_chunk_index", "status", "ready",
    "unavailable_reason", "fraction_scale",
}
_KEYS = {
    "source", "entry_kind", "status", "ready", "subject_army_id",
    "subject_carmy_id", "referenced_persistent_ids_complete",
    "unavailable_reason", "persistent_regiments",
}


def _integer(value: object, bits: int, name: str, *, nullable: bool = False,
             signed: bool = True) -> None:
    if value is None and nullable:
        return
    lower = -(1 << (bits - 1)) if signed else 0
    upper = (1 << (bits - 1)) if signed else (1 << bits)
    if type(value) is not int or not lower <= value < upper:
        raise ValueError(f"native fixed chunk0 preparation {name} has invalid int{bits} width")


def _status(value: dict, name: str) -> None:
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if (type(status) is not str or status not in {"available", "partial", "unavailable"}
            or type(ready) is not bool or ready != (status == "available")):
        raise ValueError(f"native fixed chunk0 preparation {name} readiness is malformed")
    if ((ready and reason is not None)
            or (not ready and (type(reason) is not str or not reason))):
        raise ValueError(f"native fixed chunk0 preparation {name} reason disagrees with readiness")


def normalize_fixed_chunk0_preparation_persistent_v1(row: object) -> dict[str, object]:
    """Normalize one actual containing-Regi row, independent of family scope."""
    if not isinstance(row, dict) or set(row) != _ROW_KEYS:
        raise ValueError("native fixed chunk0 preparation persistent row schema is malformed")
    _status(row, "persistent row")
    _integer(row["persistent_regiment_id"], 32, "persistent_regiment_id")
    if type(row["fixed_chunk_index"]) is not int or row["fixed_chunk_index"] != 0:
        raise ValueError("native fixed chunk0 preparation requires physical chunk index0")
    _integer(row["containing_guard_138_raw"], 32, "containing_guard_138_raw", nullable=True)
    _integer(row["containing_definition_magic_38"], 32,
             "containing_definition_magic_38", nullable=True, signed=False)
    _integer(row["fresh_fraction_raw"], 64, "fresh_fraction_raw", nullable=True)
    permission = row["native_fixed_chunk0_can_replenish"]
    if permission is not None and type(permission) is not bool:
        raise ValueError("native fixed chunk0 preparation permission must be bool or null")
    if type(row["fraction_scale"]) is not int or row["fraction_scale"] != 100000:
        raise ValueError("native fixed chunk0 preparation fraction scale must be100000")
    if row["ready"] and any(row[key] is None for key in _OPERANDS):
        raise ValueError("native available fixed chunk0 preparation row is incomplete")
    return dict(row)


def normalize_fixed_chunk0_preparation_inputs_v1(
    value: object, *, expected_army_id: int | None = None,
    expected_carmy_id: int | None = None,
) -> dict[str, object] | None:
    """Copy the optional native family; publication completeness is not a branch verdict."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native fixed chunk0 preparation input schema is malformed")
    if value["source"] != _SOURCE or value["entry_kind"] != _ENTRY:
        raise ValueError("native fixed chunk0 preparation source or entry kind is malformed")
    _status(value, "family")
    for key in ("subject_army_id", "subject_carmy_id"):
        _integer(value[key], 32, key)
    if expected_army_id is not None and value["subject_army_id"] != expected_army_id:
        raise ValueError("native fixed chunk0 preparation subject Army differs")
    if expected_carmy_id is not None and value["subject_carmy_id"] != expected_carmy_id:
        raise ValueError("native fixed chunk0 preparation subject CArmy differs")
    if type(value["referenced_persistent_ids_complete"]) is not bool:
        raise ValueError("native fixed chunk0 preparation referenced-ID completeness is malformed")
    if not isinstance(value["persistent_regiments"], list):
        raise ValueError("native fixed chunk0 preparation persistent rows must be an ordered list")
    rows = [normalize_fixed_chunk0_preparation_persistent_v1(row)
            for row in value["persistent_regiments"]]
    if value["ready"] and (
            not value["referenced_persistent_ids_complete"]
            or any(not row["ready"] for row in rows)):
        raise ValueError("native available fixed chunk0 preparation family is incomplete")
    result = dict(value)
    result["persistent_regiments"] = rows
    return result
