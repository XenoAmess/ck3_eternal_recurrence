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
    if not isinstance(value, dict) or set(value) != _KEYS:
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
    return dict(value)


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
