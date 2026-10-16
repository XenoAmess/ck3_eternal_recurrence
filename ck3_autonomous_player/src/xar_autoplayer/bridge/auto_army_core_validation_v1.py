"""Prospective private auto-turn Army view over the existing ordinary wire.

The explicit/public Army query keeps its complete normalized result. This
validator is for the ordinary auto-turn branch whose MCP result exposes only
the scalar summary and whose same-frame cache consumes eleven core fields.
"""

from __future__ import annotations

from .public_unit_contract import public_cunit_id
from .war_contract import (
    CK3_FIXED_POINT_SCALE,
    _ARMY_STRENGTH_ROW_KEYS,
    _ARMY_STRENGTH_SCOPE_ROLES,
    _ARMY_STRENGTH_SUPPLY_ROW_KEYS,
    _optional_native_carmy_full_id,
    _optional_non_negative_int32,
    _strict_positive_int32_id_list,
)


_SUMMARY_OPTIONAL_PAIRS = (
    ("current_supply_raw", "current_supply_scale"),
    ("current_attrition_fraction_raw", "current_attrition_fraction_scale"),
)


def normalize_auto_army_core_v1(
    value: object,
    *,
    expected_scope: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Validate and detach every auto-visible/strategy field, in scope order.

    The native ordinary wire is validated for profile coverage before this
    projection. Explicit queries retain their complete manager normalization.
    A future native lean profile can emit this same scalar row contract.
    """
    if not isinstance(value, list) or not isinstance(expected_scope, list):
        raise ValueError("auto Army rows/scope must be arrays")
    if any(not isinstance(item, dict) for item in expected_scope):
        raise ValueError("auto Army expected scope contains a malformed row")
    rows: list[dict[str, object]] = []
    for index, raw in enumerate(value):
        name = f"army_strengths[{index}]"
        if (
            not isinstance(raw, dict)
            or not _ARMY_STRENGTH_ROW_KEYS <= raw.keys()
            or not raw.keys() <= _ARMY_STRENGTH_SUPPLY_ROW_KEYS
        ):
            raise ValueError(f"native {name} schema is malformed")
        status = raw["status"]
        if status not in {"available", "unavailable"}:
            raise ValueError(f"native {name}.status is malformed")
        scope_role = raw["scope_role"]
        if scope_role not in _ARMY_STRENGTH_SCOPE_ROLES:
            raise ValueError(f"native {name}.scope_role is malformed")
        army_id = public_cunit_id(raw["army_id"], f"{name}.army_id")
        war_ids = _strict_positive_int32_id_list(raw["war_ids"], f"{name}.war_ids")
        native_carmy_id = _optional_native_carmy_full_id(raw["native_carmy_id"], f"{name}.native_carmy_id")
        aggregates = {
            key: _optional_non_negative_int32(raw[key], f"{name}.{key}")
            for key in ("regiment_count", "current_soldiers", "maximum_soldiers")
        }
        power = raw["ai_base_power_raw"]
        if power is not None and (type(power) is not int or not -(2**63) <= power <= 2**63 - 1):
            raise ValueError(f"native {name}.ai_base_power_raw must be signed int64 or null")
        if raw["ai_base_power_scale"] != CK3_FIXED_POINT_SCALE:
            raise ValueError(f"native {name}.ai_base_power_scale is malformed")
        reason = raw["unavailable_reason"]
        if status == "available":
            if native_carmy_id is None or power is None or any(x is None for x in aggregates.values()) or reason is not None:
                raise ValueError(f"native available {name} is incomplete")
        elif any(x is not None for x in aggregates.values()) or power is not None or not isinstance(reason, str) or not reason:
            raise ValueError(f"native unavailable {name} must null aggregates and give a reason")
        row: dict[str, object] = {
            "status": status, "army_id": army_id, "native_carmy_id": native_carmy_id,
            "scope_role": scope_role, "war_ids": war_ids,
            **aggregates, "ai_base_power_raw": power,
            "ai_base_power_scale": CK3_FIXED_POINT_SCALE,
            "unavailable_reason": reason,
        }
        for raw_key, scale_key in _SUMMARY_OPTIONAL_PAIRS:
            if (raw_key in raw) != (scale_key in raw):
                raise ValueError(f"native {name}.{raw_key} requires its scale")
            if raw_key not in raw:
                continue
            scalar = raw[raw_key]
            if scalar is not None and (type(scalar) is not int or not -(2**63) <= scalar <= 2**63 - 1):
                raise ValueError(f"native {name}.{raw_key} must be signed int64 or null")
            if raw[scale_key] != CK3_FIXED_POINT_SCALE or (status != "available" and scalar is not None):
                raise ValueError(f"native {name}.{raw_key} scale/status is malformed")
            row[raw_key], row[scale_key] = scalar, CK3_FIXED_POINT_SCALE
        rows.append(row)
    ids = [row["army_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("native army_strengths contains duplicate ArmyIDs")
    expected = [
        {
            "army_id": public_cunit_id(raw.get("army_id"), "expected army-strength scope army_id"),
            "scope_role": raw.get("scope_role"), "war_ids": raw.get("war_ids"),
        }
        for raw in expected_scope
    ]
    observed = [{key: row[key] for key in ("army_id", "scope_role", "war_ids")} for row in rows]
    if observed != expected:
        raise ValueError("native army_strengths does not match the paused snapshot scope")
    return rows
