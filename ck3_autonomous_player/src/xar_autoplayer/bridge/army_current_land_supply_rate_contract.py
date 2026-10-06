"""Actual current operands for the exact.3 current Province land numeric kernel."""
from __future__ import annotations

_I32 = (
    "province_id", "subject_army_id", "subject_carmy_id", "owner_character_id",
    "commander_raw_full_id", "commander_resolved_full_id",
)
_BOOL = (
    "native_land_branch_applicable", "commander_used_native_fallback",
    "native_province_component_applicable",
)
_I64 = (
    "province_component_raw", "commander_modifier_1a9_raw",
    "loaded_excess_slope_raw", "loaded_min_loss_raw", "loaded_max_loss_raw",
    "loaded_divisor_floor_raw",
)
_KEYS = set(_I32 + _BOOL + _I64) | {
    "source", "status", "unavailable_reason", "current_observation_ready", "scale",
}


def _integer(value: object, bits: int, name: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"native land supply rate {name} must be signed int{bits} or null")
    return value


def normalize_current_land_supply_rate_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native land supply rate input schema is malformed")
    if value["source"] != "native_current_province_land_supply_rate_inputs":
        raise ValueError("native land supply rate input source is malformed")
    status, reason = value["status"], value["unavailable_reason"]
    if type(status) is not str or status not in {"available", "unavailable", "not_land"}:
        raise ValueError("native land supply rate status is malformed")
    if reason is not None and (type(reason) is not str or not reason):
        raise ValueError("native land supply rate reason must be text or null")
    if type(value["current_observation_ready"]) is not bool:
        raise ValueError("native land supply rate readiness must be bool")
    for field in _I32:
        _integer(value[field], 32, field)
    for field in _I64:
        _integer(value[field], 64, field)
    for field in _BOOL:
        if value[field] is not None and type(value[field]) is not bool:
            raise ValueError(f"native land supply rate {field} must be bool or null")
    if type(value["scale"]) is not int or value["scale"] != 100000:
        raise ValueError("native land supply rate scale must be100000")
    if status == "available":
        if (reason is not None or not value["current_observation_ready"]
                or value["native_land_branch_applicable"] is not True
                or any(value[field] is None for field in _I32 + _BOOL + _I64)):
            raise ValueError("native available land supply rate inputs are incomplete")
        if (value["native_province_component_applicable"] is False
                and value["province_component_raw"] != 0):
            raise ValueError("native absent Province component must be zero")
        if (value["commander_used_native_fallback"] is False
                and value["commander_raw_full_id"] != value["commander_resolved_full_id"]):
            raise ValueError("native resolved commander FullID differs")
    elif value["current_observation_ready"]:
        raise ValueError("native nonavailable land supply rate inputs cannot be ready")
    if status == "not_land" and (
            value["native_land_branch_applicable"] is not False or reason is not None
            or any(value[field] is not None for field in (
                "native_province_component_applicable", "province_component_raw",
                "commander_modifier_1a9_raw"))):
        raise ValueError("native not-land supply rate branch is malformed")
    if status == "unavailable" and reason is None:
        raise ValueError("native unavailable land supply rate inputs require a reason")
    return dict(value)
