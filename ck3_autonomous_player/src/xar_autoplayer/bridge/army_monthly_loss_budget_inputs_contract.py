"""Readonly exact .3 admission, state-table and component operands."""
from __future__ import annotations

_I32 = ("unit_native_170_raw", "army_gathering_count_raw")
_BOOL = ("native_unit_in_combat", "native_unit_gathering",
         "native_fleet_supply_loss_suppressed", "commander_valid")
_KEYS = {"status", "ready", "unavailable_reason", "scale", *_I32, *_BOOL,
         "loaded_supply_state_levels", "loaded_supply_state_fractions_raw",
         "commander_supply_modifier_id", "commander_supply_modifier_raw"}


def normalize_monthly_loss_budget_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native monthly_loss_budget_inputs_v1 schema is malformed")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if status not in {"available", "unavailable"} or type(ready) is not bool or ready != (status == "available"):
        raise ValueError("native monthly_loss_budget_inputs_v1 readiness is malformed")
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native monthly_loss_budget_inputs_v1 reason disagrees with readiness")
    if type(value["scale"]) is not int or value["scale"] != 100_000:
        raise ValueError("native monthly_loss_budget_inputs_v1 scale must be 100000")
    result = dict(value)

    def integer(item: object, bits: int, key: str, signed: bool = True) -> None:
        lower, upper = (-(1 << (bits - 1)), 1 << (bits - 1)) if signed else (0, 1 << bits)
        if item is not None and (type(item) is not int or not lower <= item < upper):
            raise ValueError(f"native monthly_loss_budget_inputs_v1 {key} has invalid integer width")

    for key in _I32:
        integer(value[key], 32, key)
    integer(value["commander_supply_modifier_id"], 16, "commander_supply_modifier_id", False)
    integer(value["commander_supply_modifier_raw"], 64, "commander_supply_modifier_raw")
    for key in _BOOL:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native monthly_loss_budget_inputs_v1 {key} must be bool or null")
    for key, bits in (("loaded_supply_state_levels", 32), ("loaded_supply_state_fractions_raw", 64)):
        items = value[key]
        if items is not None:
            if not isinstance(items, list):
                raise ValueError(f"native monthly_loss_budget_inputs_v1 {key} must be an ordered array or null")
            for item in items:
                if item is None:
                    raise ValueError(f"native monthly_loss_budget_inputs_v1 {key} cannot contain null")
                integer(item, bits, key)
            result[key] = list(items)
    if value["commander_valid"] is False and any(value[key] is not None for key in (
            "commander_supply_modifier_id", "commander_supply_modifier_raw")):
        raise ValueError("native invalid commander cannot publish a modifier operand")
    if ready and (any(value[key] is None for key in (*_I32, *_BOOL,
            "loaded_supply_state_levels", "loaded_supply_state_fractions_raw"))
            or (value["commander_valid"] and any(value[key] is None for key in (
                "commander_supply_modifier_id", "commander_supply_modifier_raw")))):
        raise ValueError("native ready monthly_loss_budget_inputs_v1 is incomplete")
    return result
