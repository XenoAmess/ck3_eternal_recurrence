"""Normalize the native current Province mode0 supply contributor observation."""
from __future__ import annotations

from .army_replenishment_records_contract import (
    normalize_regiment_replenishment_records_v1,
)

_TOP = {
    "source", "status", "unavailable_reason", "current_usage_ready",
    "contributors_ready", "province_id", "subject_army_id", "subject_carmy_id",
    "owner_character_id", "native_province_unit_count",
    "native_supply_limit_soldiers", "native_supply_usage_soldiers",
    "soldiers_scale", "occurrences",
}
_OCCURRENCE = {
    "stored_index", "army_id", "status", "unavailable_reason",
    "owner_character_id", "included", "inclusion_basis", "native_carmy_id",
    "native_eligible_current_soldiers", "regiments",
}
_REGIMENT = {
    "stored_index", "army_regiment_id", "status", "unavailable_reason",
    "current_soldiers", "maximum_soldiers", "native_supply_loss_eligible",
    "replenishment_records_v1",
}
_TOP_I32 = (
    "province_id", "subject_army_id", "subject_carmy_id", "owner_character_id",
    "native_province_unit_count", "native_supply_limit_soldiers",
    "native_supply_usage_soldiers",
)
_BASES = {"same_owner", "native_common_war_side", "native_not_common_war_side"}


def _i32(value: object, name: str, *, nullable: bool = True) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
        raise ValueError(f"native Province supply {name} must be signed int32"
                         + (" or null" if nullable else ""))
    return value


def _bool(value: object, name: str, *, nullable: bool = True) -> bool | None:
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise ValueError(f"native Province supply {name} must be bool"
                         + (" or null" if nullable else ""))
    return value


def _schema(value: object, keys: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native Province supply {name} schema is malformed")
    return value


def _status(row: dict, *, partial: bool = False) -> None:
    choices = {"available", "unavailable", "partial"} if partial else {
        "available", "unavailable"}
    if not isinstance(row["status"], str) or row["status"] not in choices:
        raise ValueError("native Province supply status is malformed")
    reason = row["unavailable_reason"]
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError("native Province supply reason must be a string or null")
    if row["status"] == "available" and reason is not None:
        raise ValueError("native available Province supply cannot have a reason")


def normalize_current_province_supply_contributors_v1(
    value: object,
) -> dict[str, object] | None:
    """Copy ordered native occurrences without deduplicating their contributions.

    Contributor readiness concerns current admission, identity, and roster.
    Complete associated DATA has its own status and is not required for that
    current observation. Native scalar usage remains independently available.
    """
    if value is None:
        return None
    top = _schema(value, _TOP, "root")
    _status(top, partial=True)
    if top["source"] != "native_current_province_mode0":
        raise ValueError("native Province supply source is malformed")
    if type(top["soldiers_scale"]) is not int or top["soldiers_scale"] != 1:
        raise ValueError("native Province supply soldier scale must be 1")
    for field in _TOP_I32:
        _i32(top[field], field)
    for field in ("current_usage_ready", "contributors_ready"):
        _bool(top[field], field, nullable=False)
    if top["current_usage_ready"] and top["native_supply_usage_soldiers"] is None:
        raise ValueError("native ready Province usage requires its scalar")
    if not isinstance(top["occurrences"], list):
        raise ValueError("native Province supply occurrences must be an array")

    occurrences = []
    for index, raw in enumerate(top["occurrences"]):
        occurrence = _schema(raw, _OCCURRENCE, "occurrence")
        _status(occurrence)
        for field in ("stored_index", "army_id"):
            _i32(occurrence[field], field, nullable=False)
        if occurrence["stored_index"] != index:
            raise ValueError("native Province supply occurrence order is malformed")
        for field in ("owner_character_id", "native_carmy_id",
                      "native_eligible_current_soldiers"):
            _i32(occurrence[field], field)
        included = _bool(occurrence["included"], "included")
        basis = occurrence["inclusion_basis"]
        if basis is not None and (not isinstance(basis, str) or basis not in _BASES):
            raise ValueError("native Province supply inclusion basis is malformed")
        if ((included is True and basis not in {"same_owner", "native_common_war_side"})
                or (included is False and basis != "native_not_common_war_side")
                or (included is None and basis is not None)):
            raise ValueError("native Province supply inclusion witness differs")
        raw_regiments = occurrence["regiments"]
        if not isinstance(raw_regiments, list):
            raise ValueError("native Province supply regiments must be an array")
        if included is False and (raw_regiments or
                                 occurrence["native_eligible_current_soldiers"] is not None):
            raise ValueError("native excluded Province occurrence has a contribution")
        regiments = []
        for ordinal, raw_regiment in enumerate(raw_regiments):
            regiment = _schema(raw_regiment, _REGIMENT, "regiment")
            _status(regiment)
            for field in ("stored_index", "army_regiment_id"):
                _i32(regiment[field], field, nullable=False)
            if regiment["stored_index"] != ordinal:
                raise ValueError("native Province supply regiment order is malformed")
            for field in ("current_soldiers", "maximum_soldiers"):
                _i32(regiment[field], field)
            eligible = _bool(regiment["native_supply_loss_eligible"],
                             "native_supply_loss_eligible")
            if regiment["status"] == "available" and (
                    eligible is None or regiment["current_soldiers"] is None
                    or regiment["maximum_soldiers"] is None):
                raise ValueError("native available Province regiment is incomplete")
            snapshot = regiment["replenishment_records_v1"]
            if snapshot is not None:
                snapshot = normalize_regiment_replenishment_records_v1([snapshot])[0]
                if snapshot["army_regiment_id"] != regiment["army_regiment_id"]:
                    raise ValueError("native Province DATA identity differs")
            if eligible is False and snapshot is not None:
                raise ValueError("native ineligible Province regiment has DATA")
            regiments.append({**regiment, "replenishment_records_v1": snapshot})
        if occurrence["status"] == "available" and (
                included is None or (included and (
                    occurrence["native_carmy_id"] is None
                    or occurrence["native_eligible_current_soldiers"] is None
                    or any(row["status"] != "available" for row in regiments)))):
            raise ValueError("native available Province occurrence is incomplete")
        occurrences.append({**occurrence, "regiments": regiments})

    if top["contributors_ready"]:
        count = top["native_province_unit_count"]
        if count is None or count < 0 or len(occurrences) != count or any(
                row["status"] != "available" for row in occurrences):
            raise ValueError("native ready Province contributor roster is incomplete")
    return {**top, "occurrences": occurrences}
