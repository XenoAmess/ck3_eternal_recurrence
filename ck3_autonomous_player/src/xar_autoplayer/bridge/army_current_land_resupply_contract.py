"""Current native land gain admission and its distinct conditional component."""
from __future__ import annotations

_KEYS = {
    "source", "status", "unavailable_reason", "current_observation_ready",
    "province_id", "owner_character_id", "native_land_branch_applicable",
    "native_resupply_eligible", "loaded_gain_raw", "scale",
}


def _integer(value: object, bits: int, name: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not -(1 << (bits - 1)) <= value < 1 << (bits - 1):
        raise ValueError(f"native current land resupply {name} must be signed int{bits} or null")
    return value


def normalize_current_land_resupply_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native current land resupply schema is malformed")
    if value["source"] != "native_current_province_land_resupply":
        raise ValueError("native current land resupply source is malformed")
    status = value["status"]
    if not isinstance(status, str) or status not in {"available", "not_land", "unavailable"}:
        raise ValueError("native current land resupply status is malformed")
    reason = value["unavailable_reason"]
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError("native current land resupply reason must be text or null")
    if type(value["current_observation_ready"]) is not bool:
        raise ValueError("native current land resupply readiness must be bool")
    for field in ("native_land_branch_applicable", "native_resupply_eligible"):
        if value[field] is not None and type(value[field]) is not bool:
            raise ValueError(f"native current land resupply {field} must be bool or null")
    for field in ("province_id", "owner_character_id"):
        _integer(value[field], 32, field)
    _integer(value["loaded_gain_raw"], 64, "loaded_gain_raw")
    if type(value["scale"]) is not int or value["scale"] != 100000:
        raise ValueError("native current land resupply scale must be100000")
    if status == "available":
        if (reason is not None or not value["current_observation_ready"]
                or value["native_land_branch_applicable"] is not True
                or any(value[field] is None for field in (
                    "province_id", "owner_character_id", "native_resupply_eligible", "loaded_gain_raw"))):
            raise ValueError("native available current land resupply is incomplete")
    elif value["current_observation_ready"] or value["native_resupply_eligible"] is not None:
        raise ValueError("native nonavailable current land resupply cannot publish admission")
    if status == "not_land" and (
            value["native_land_branch_applicable"] is not False or reason is not None):
        raise ValueError("native not-land supply branch is malformed")
    return dict(value)


def project_land_resupply_gain_component_v1(
    observation: object, *, usage_soldiers: int, limit_soldiers: int,
) -> dict[str, object]:
    """Compute only gain for explicit same-context usage/limit, never full rate.

    An explicit projected usage may come from selected contributor refill.
    This does not observe the after stage or calendar dispatch. Province,
    owner and relationship context remain the supplied current observation.
    """
    for field, scalar in (("usage_soldiers", usage_soldiers), ("limit_soldiers", limit_soldiers)):
        if _integer(scalar, 32, field) is None:
            raise ValueError(f"land resupply gain component requires {field}")
    inputs = normalize_current_land_resupply_v1(observation)
    ready = inputs is not None and inputs["current_observation_ready"]
    under_limit = usage_soldiers <= limit_soldiers
    gain = None
    if ready:
        gain = inputs["loaded_gain_raw"] if under_limit and inputs["native_resupply_eligible"] else 0
    return {
        "source": "conditional_same_context_land_gain_component",
        "gain_component_ready": bool(ready),
        "usage_soldiers": usage_soldiers, "limit_soldiers": limit_soldiers,
        "under_limit": under_limit, "gain_component_raw": gain, "scale": 100000,
        "full_monthly_supply_change_ready": False, "actual_post_stage_observed": False,
    }
