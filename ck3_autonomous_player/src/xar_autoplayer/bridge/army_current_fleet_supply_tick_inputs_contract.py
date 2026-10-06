"""Candidate exact .3 current fleet operands; not yet executed or qualified."""
from __future__ import annotations

_I32 = (
    "subject_army_id", "subject_carmy_id", "province_id", "current_native_date_low32",
    "fleet_raw_full_id", "fleet_resolved_full_id", "fleet_day_raw",
    "loaded_fleet_day_sentinel_raw", "commander_raw_full_id", "commander_resolved_full_id",
)
_I64 = (
    "terrain_modifier_772_raw", "loaded_fleet_loss_raw", "commander_modifier_1a9_raw",
    "loaded_divisor_floor_raw", "loaded_max_loss_raw",
)
_BOOL = (
    "native_fleet_branch_applicable", "fleet_used_native_fallback",
    "commander_used_native_fallback",
)
_KEYS = {
    "source", "status", "ready", "unavailable_reason", "scale", *_I32, *_I64, *_BOOL,
    "terrain_magic_38_raw", "terrain_modifier_772_id",
}


def normalize_current_fleet_supply_tick_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native current_fleet_supply_tick_inputs_v1 schema is malformed")
    if value["source"] != "native_current_fleet_supply_tick_inputs" or value["scale"] != 100000:
        raise ValueError("native fleet supply tick source/scale is malformed")
    if type(value["scale"]) is not int:
        raise ValueError("native fleet supply tick scale must be integer")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if status not in {"available", "unavailable", "not_fleet"} or type(ready) is not bool:
        raise ValueError("native fleet supply tick readiness is malformed")
    if ready != (status != "unavailable") or (ready and reason is not None) or (
            not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native fleet supply tick reason disagrees with readiness")
    for keys, bits, signed in ((_I32, 32, True), (_I64, 64, True),
                              (("terrain_magic_38_raw",), 32, False),
                              (("terrain_modifier_772_id",), 16, False)):
        lower, upper = (-(1 << (bits - 1)), 1 << (bits - 1)) if signed else (0, 1 << bits)
        for key in keys:
            item = value[key]
            if item is not None and (type(item) is not int or not lower <= item < upper):
                raise ValueError(f"native fleet supply tick {key} has invalid integer width")
    for key in _BOOL:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native fleet supply tick {key} must be bool or null")
    if not ready:
        return dict(value)
    required = ["subject_army_id", "subject_carmy_id", "province_id", "native_fleet_branch_applicable"]
    if status == "not_fleet":
        if value["native_fleet_branch_applicable"] is not False:
            raise ValueError("not_fleet requires actual false native branch")
    else:
        if value["native_fleet_branch_applicable"] is not True:
            raise ValueError("available fleet inputs require actual true native branch")
        required += ["current_native_date_low32", "fleet_raw_full_id", "fleet_resolved_full_id",
                     "fleet_used_native_fallback", "fleet_day_raw", "loaded_fleet_day_sentinel_raw",
                     "terrain_magic_38_raw"]
        if value["terrain_magic_38_raw"] == 0x4744624F:
            required += ["terrain_modifier_772_id", "terrain_modifier_772_raw", "commander_raw_full_id",
                         "commander_resolved_full_id", "commander_used_native_fallback"]
            modifier = value["terrain_modifier_772_raw"]
            if modifier is not None and modifier <= 0:
                required += ["loaded_fleet_loss_raw"]
                loss = value["loaded_fleet_loss_raw"]
                if loss is not None and (loss > 0 or loss == -(1 << 63)):
                    required += ["commander_modifier_1a9_raw", "loaded_divisor_floor_raw", "loaded_max_loss_raw"]
    if any(value[key] is None for key in required):
        raise ValueError("native ready fleet supply tick inputs are incomplete")
    return dict(value)
