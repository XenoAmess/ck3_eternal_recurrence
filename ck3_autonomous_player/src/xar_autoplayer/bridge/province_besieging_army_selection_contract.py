"""Fresh native Province CArmy selection; public CUnit joining stays separate."""
from __future__ import annotations

from .public_unit_contract import optional_public_cunit_id


def normalize_province_besieging_army_selection(
    value: object, *, name: str
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a native selection object or null")
    native_id = value.get("native_carmy_id")
    if native_id is not None and (type(native_id) is not int or not 0 <= native_id <= 2**31 - 1):
        raise ValueError(f"{name}.native_carmy_id must be a full native int32 ID or null")
    public_id = optional_public_cunit_id(value.get("public_unit_id"), f"{name}.public_unit_id")
    controllable = value.get("controllable")
    if controllable is not None and type(controllable) is not bool:
        raise ValueError(f"{name}.controllable must be boolean or null")
    return {"native_carmy_id": native_id, "public_unit_id": public_id,
            "controllable": controllable}
