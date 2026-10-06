"""Typed current Province flags0 besieging contributors and assault context."""
from __future__ import annotations

from .army_replenishment_records_contract import (
    normalize_regiment_replenishment_records_v1,
)

_TOP = {
    "status", "unavailable_reason", "province_id", "native_province_unit_count",
    "native_besieging_strength", "contributors_ready", "native_assault_expected_loss",
    "assault_context", "occurrences",
}
_CONTEXT = {
    "status", "unavailable_reason", "has_active_siege", "siege_id",
    "breach_level_raw", "casualty_percentage_count", "casualty_percentage_raw",
}
_OCCURRENCE = {
    "stored_index", "public_unit_id", "resolved_unit_id", "unit_used_fallback",
    "current_province_id", "current_province_used_fallback", "raw_unit18",
    "raw_unit170", "raw_unit44", "native_carmy_id", "army_used_fallback",
    "eligible", "available", "unavailable_reason", "native_whole_current_soldiers",
    "regiments",
}
_REGIMENT = {
    "stored_index", "army_regiment_id", "available", "unavailable_reason",
    "current_soldiers", "maximum_soldiers", "replenishment_records_v1",
}
_NULLABLE_OCCURRENCE_I32 = (
    "resolved_unit_id", "current_province_id", "raw_unit18", "raw_unit170",
    "raw_unit44", "native_carmy_id", "native_whole_current_soldiers",
)
_NULLABLE_OCCURRENCE_BOOL = (
    "unit_used_fallback", "current_province_used_fallback", "army_used_fallback",
    "eligible",
)


def _integer(value: object, bits: int, name: str, *, nullable: bool = True):
    if value is None and nullable:
        return None
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"native besieging {name} must be signed int{bits}"
                         + (" or null" if nullable else ""))
    return value


def _boolean(value: object, name: str, *, nullable: bool = True):
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise ValueError(f"native besieging {name} must be bool"
                         + (" or null" if nullable else ""))
    return value


def _object(value: object, keys: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native besieging {name} schema is malformed")
    return value


def _reason(value: object) -> None:
    if not isinstance(value, str):
        raise ValueError("native besieging unavailable_reason must be a string")


def normalize_current_province_besieging_contributors_v1(
    value: object,
) -> dict[str, object] | None:
    """Copy native typed operands, preserving zero IDs, signed counts and repeats.

    Current native B and assault loss can exist independently of complete
    contributor DATA. Availability flags are retained rather than inferred
    from a fallback ID, signed aggregate, or optional percentage value.
    """
    if value is None:
        return None
    top = _object(value, _TOP, "root")
    if not isinstance(top["status"], str) or top["status"] not in {
            "available", "partial", "unavailable"}:
        raise ValueError("native besieging status is malformed")
    _reason(top["unavailable_reason"])
    _integer(top["province_id"], 32, "province_id", nullable=False)
    _integer(top["native_province_unit_count"], 32, "native_province_unit_count")
    for field in ("native_besieging_strength", "native_assault_expected_loss"):
        _integer(top[field], 32, field)
    _boolean(top["contributors_ready"], "contributors_ready", nullable=False)

    context = _object(top["assault_context"], _CONTEXT, "assault context")
    if not isinstance(context["status"], str):
        raise ValueError("native besieging assault status must be a string")
    _reason(context["unavailable_reason"])
    _boolean(context["has_active_siege"], "has_active_siege")
    for field in ("siege_id", "breach_level_raw", "casualty_percentage_count"):
        _integer(context[field], 32, field)
    _integer(context["casualty_percentage_raw"], 64, "casualty_percentage_raw")

    if not isinstance(top["occurrences"], list):
        raise ValueError("native besieging occurrences must be an array")
    occurrences = []
    for raw in top["occurrences"]:
        occurrence = _object(raw, _OCCURRENCE, "occurrence")
        _reason(occurrence["unavailable_reason"])
        for field in ("stored_index", "public_unit_id"):
            _integer(occurrence[field], 32, field, nullable=False)
        for field in _NULLABLE_OCCURRENCE_I32:
            _integer(occurrence[field], 32, field)
        for field in _NULLABLE_OCCURRENCE_BOOL:
            _boolean(occurrence[field], field)
        _boolean(occurrence["available"], "available", nullable=False)
        if not isinstance(occurrence["regiments"], list):
            raise ValueError("native besieging regiments must be an array")
        regiments = []
        for raw_regiment in occurrence["regiments"]:
            regiment = _object(raw_regiment, _REGIMENT, "regiment")
            for field in ("stored_index", "army_regiment_id"):
                _integer(regiment[field], 32, field, nullable=False)
            for field in ("current_soldiers", "maximum_soldiers"):
                _integer(regiment[field], 32, field)
            _boolean(regiment["available"], "available", nullable=False)
            _reason(regiment["unavailable_reason"])
            data = regiment["replenishment_records_v1"]
            if data is not None:
                data = normalize_regiment_replenishment_records_v1([data])[0]
            regiments.append({**regiment, "replenishment_records_v1": data})
        occurrences.append({**occurrence, "regiments": regiments})
    return {**top, "assault_context": dict(context), "occurrences": occurrences}
