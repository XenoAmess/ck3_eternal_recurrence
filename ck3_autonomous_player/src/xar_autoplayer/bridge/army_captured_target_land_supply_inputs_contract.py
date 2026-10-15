"""Current target numerical operands, independently of actual landfall."""
from __future__ import annotations

_I32 = ("subject_army_id", "subject_carmy_id", "owner_character_id", "province_id")
_I64 = ("province_component_raw", "loaded_gain_raw")
_BOOL = ("native_province_component_applicable", "native_resupply_eligible")
_READY = (
    "current_inputs_ready", "province_component_observation_ready",
    "resupply_observation_ready",
)
_REASONS = (
    "unavailable_reason", "province_component_unavailable_reason",
    "resupply_unavailable_reason",
)
_KEYS = {"source", "input_basis", "scale", "status", *_I32, *_I64,
         *_BOOL, *_READY, *_REASONS}


def normalize_captured_target_land_supply_inputs_v1(
    value: object,
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) not in (_KEYS, _KEYS | {"loss_adjustment_operands_v1"}):
        raise ValueError("captured target land supply input schema is malformed")
    if (value["source"] != "native_captured_target_land_supply_inputs"
            or value["input_basis"] != "captured_owner_and_target_province"
            or type(value["scale"]) is not int or value["scale"] != 100000):
        raise ValueError("captured target land supply input source/basis/scale is malformed")
    for keys, bits in ((_I32, 32), (_I64, 64)):
        for key in keys:
            item = value[key]
            if item is not None and (type(item) is not int
                    or not -(1 << (bits - 1)) <= item < 1 << (bits - 1)):
                raise ValueError(f"captured target land supply {key} has invalid integer width")
    for key in _BOOL:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"captured target land supply {key} must be bool or null")
    for key in _READY:
        if type(value[key]) is not bool:
            raise ValueError(f"captured target land supply {key} must be bool")
    for key in _REASONS:
        reason = value[key]
        if reason is not None and (not isinstance(reason, str) or not reason):
            raise ValueError(f"captured target land supply {key} must be nonempty text or null")
    component_ready = value["province_component_observation_ready"]
    resupply_ready = value["resupply_observation_ready"]
    ready = component_ready and resupply_ready
    status = "available" if ready else "partial" if component_ready or resupply_ready else "unavailable"
    if value["status"] != status or value["current_inputs_ready"] != ready:
        raise ValueError("captured target land supply status disagrees with readiness")
    for flag, reason_key, operands in (
        (component_ready, "province_component_unavailable_reason",
         ("native_province_component_applicable", "province_component_raw")),
        (resupply_ready, "resupply_unavailable_reason",
         ("native_resupply_eligible",)),
    ):
        if flag:
            if value[reason_key] is not None or any(value[key] is None for key in operands):
                raise ValueError("ready captured target branch has missing operands or a reason")
        elif value[reason_key] is None:
            raise ValueError("unavailable captured target branch requires a reason")
    if component_ready and value["native_province_component_applicable"] is False:
        if value["province_component_raw"] != 0:
            raise ValueError("false target component predicate requires native0")
    expected_reason = None if ready else (
        value["province_component_unavailable_reason"] or value["resupply_unavailable_reason"]
    )
    if value["unavailable_reason"] != expected_reason:
        raise ValueError("captured target land supply reason disagrees with branch reasons")
    if component_ready or resupply_ready:
        if any(value[key] is None for key in _I32):
            raise ValueError("ready captured target branch requires actual subject/owner/Province IDs")
    result=dict(value)
    if "loss_adjustment_operands_v1" in value:
        result["loss_adjustment_operands_v1"]=normalize_target_loss_operands_v1(value["loss_adjustment_operands_v1"])
    return result


def normalize_target_land_supply_in_route_preview(
    preview: dict[str, object],
) -> dict[str, object]:
    """Normalize only the optional new sibling; preserve the legacy preview."""
    supply = preview.get("province_supply")
    target = supply.get("target") if isinstance(supply, dict) else None
    if not isinstance(target, dict) or "captured_target_land_supply_inputs_v1" not in target:
        return preview
    family = normalize_captured_target_land_supply_inputs_v1(
        target["captured_target_land_supply_inputs_v1"]
    )
    if family is not None:
        for actual, expected in (
            (family["subject_army_id"], preview.get("army_id")),
            (family["subject_carmy_id"], supply.get("native_carmy_id")),
            (family["owner_character_id"], supply.get("owner_character_id")),
            (family["province_id"], target.get("province_id")),
        ):
            if actual is not None and (type(expected) is not int or actual != expected):
                raise ValueError("captured target land inputs disagree with preview context")
        if (target.get("role") != "target"
                or target.get("province_id") != preview.get("target_province_id")):
            raise ValueError("captured target land input Province disagrees with requested target")
    return {
        **preview,
        "province_supply": {**supply, "target": {
            **target, "captured_target_land_supply_inputs_v1": family,
        }},
    }


def normalize_target_loss_operands_v1(value):
    if value is None:return None
    i32=("commander_raw_full_id","commander_resolved_full_id")
    i64=("commander_modifier_1a9_raw","loaded_excess_slope_raw","loaded_min_loss_raw",
         "loaded_max_loss_raw","loaded_divisor_floor_raw")
    keys={"source","scale","status","observation_ready","unavailable_reason",
          "commander_used_native_fallback",*i32,*i64}
    if not isinstance(value,dict) or set(value)!=keys:
        raise ValueError("target loss operand schema is malformed")
    if value["source"]!="native_captured_target_loss_operands" or type(value["scale"]) is not int or value["scale"]!=100000:
        raise ValueError("target loss operand source/scale is malformed")
    for fields,bits in ((i32,32),(i64,64)):
        for field in fields:
            x=value[field]
            if x is not None and (type(x) is not int or not -(1<<(bits-1))<=x<(1<<(bits-1))):
                raise ValueError("target loss operand integer width is malformed")
    ready=value["observation_ready"]
    fallback=value["commander_used_native_fallback"]
    if type(ready) is not bool or (fallback is not None and type(fallback) is not bool):
        raise ValueError("target loss operand readiness/fallback is malformed")
    reason=value["unavailable_reason"]
    if ready:
        if value["status"]!="available" or reason is not None or fallback is None or any(value[k] is None for k in (*i32,*i64)):
            raise ValueError("ready target loss operands incomplete")
    elif value["status"]!="unavailable" or not isinstance(reason,str) or not reason:
        raise ValueError("unavailable target loss operands require reason")
    if value["commander_modifier_1a9_raw"] is not None and (fallback is None or any(value[k] is None for k in i32)):
        raise ValueError("observed target modifier requires resolved commander witness")
    if fallback is False and value["commander_resolved_full_id"] is not None and value["commander_raw_full_id"]!=value["commander_resolved_full_id"]:
        raise ValueError("target commander raw/resolved FullID differs without fallback")
    return dict(value)
