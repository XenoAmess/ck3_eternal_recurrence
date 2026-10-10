"""Typed same-query operands for the current daily assault numerical caller."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import (
    _boolean, _integer, _object, _resolution, _state,
)
from .army_province_besieging_contributors_contract import (
    normalize_current_province_besieging_contributors_v1,
)
from .army_ordered_besieging_refill_contract import (
    normalize_ordered_besieging_refill_inputs_v1,
)
from .army_replenishment_records_contract import (
    normalize_regiment_replenishment_records_v1,
)

_STATE = {"status", "ready", "unavailable_reason"}
_TOP = _STATE | {"schema_version", "source", "stage", "groups", "target_regiments"}
_GROUP = _STATE | {"native_index", "physical_slot_i64", "native_current_expected_loss",
                   "province_magic_raw_u32", "besieging_inputs_v1", "army_counts"}
_GROUP_OPTIONAL = {"ordered_besieging_refill_inputs_v1"}
_ARMY = _STATE | {"native_index", "raw_full_id_u32", "resolution",
                  "native_whole_current_soldiers", "regiments"}
_REGIMENT = {"native_index", "raw_full_id_u32", "resolution", "identity_valid",
             "current_soldiers", "maximum_soldiers"}
_TARGET = _STATE | {"resolution", "identity_valid", "current_soldiers",
                    "maximum_soldiers", "native_loss_writer_skipped",
                    "replenishment_records_v1"}


def _array(value: object, name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"daily assault loss {name} must be an array")
    return value


def _resolved(value: object, requested: int | None, name: str) -> None:
    _resolution(value, requested, name)


def normalize_current_daily_assault_loss_inputs_v1(value: object) -> dict | None:
    """Preserve independent nullable operands and every native occurrence.

    Availability describes the captured family, rather than requiring DATA
    for an unused zero-budget or character-skip branch of the projection.
    """
    if value is None:
        return None
    top = _object(value, _TOP, "daily assault loss root")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("daily assault loss schema_version must equal 1")
    if top["source"] != "native_current_daily_assault_loss_inputs":
        raise ValueError("daily assault loss source is malformed")
    if top["stage"] != "observed_current_daily_assault_table":
        raise ValueError("daily assault loss stage is malformed")
    _state(top, "daily assault loss root")
    groups = []
    for raw in _array(top["groups"], "groups"):
        # Older producers omit the additive scope; preserve that absence.
        if not isinstance(raw, dict) or set(raw) not in (_GROUP, _GROUP | _GROUP_OPTIONAL):
            raise ValueError("daily assault loss group schema is malformed")
        group = raw
        _state(group, "daily assault loss group")
        _integer(group["native_index"], "native_index", nullable=False, nonnegative=True)
        _integer(group["physical_slot_i64"], "physical_slot_i64", bits=64, nullable=False)
        _integer(group["native_current_expected_loss"], "native_current_expected_loss")
        _integer(group["province_magic_raw_u32"], "province_magic_raw_u32", unsigned=True)
        family = normalize_current_province_besieging_contributors_v1(group["besieging_inputs_v1"])
        armies = []
        for raw_army in _array(group["army_counts"], "army_counts"):
            army = _object(raw_army, _ARMY, "daily assault Army count")
            _state(army, "daily assault Army count")
            _integer(army["native_index"], "native_index", nullable=False, nonnegative=True)
            raw_id = _integer(army["raw_full_id_u32"], "raw_full_id_u32", unsigned=True)
            _resolved(army["resolution"], raw_id, "daily assault Army resolution")
            _integer(army["native_whole_current_soldiers"], "native_whole_current_soldiers")
            for regiment in _array(army["regiments"], "Army regiments"):
                regiment = _object(regiment, _REGIMENT, "daily assault Army regiment")
                _integer(regiment["native_index"], "native_index", nullable=False, nonnegative=True)
                requested = _integer(regiment["raw_full_id_u32"], "raw_full_id_u32", unsigned=True)
                _resolved(regiment["resolution"], requested, "daily assault Army ArRg resolution")
                _boolean(regiment["identity_valid"], "identity_valid")
                for field in ("current_soldiers", "maximum_soldiers"):
                    _integer(regiment[field], field)
            armies.append(deepcopy(army))
        normalized = {**deepcopy(group), "besieging_inputs_v1": family,
                      "army_counts": armies}
        if "ordered_besieging_refill_inputs_v1" in group:
            scope = normalize_ordered_besieging_refill_inputs_v1(
                group["ordered_besieging_refill_inputs_v1"])
            if scope is not None and (family is None or scope["province_id"] != family["province_id"]):
                raise ValueError("daily assault group ordered scope must match its actual Province")
            normalized["ordered_besieging_refill_inputs_v1"] = scope
        groups.append(normalized)
    targets = []
    for raw in _array(top["target_regiments"], "target_regiments"):
        target = _object(raw, _TARGET, "daily assault writer target")
        _state(target, "daily assault writer target")
        resolution = target["resolution"]
        requested = resolution.get("requested_full_id_u32") if isinstance(resolution, dict) else None
        _resolved(resolution, requested, "daily assault writer target resolution")
        _boolean(target["identity_valid"], "identity_valid")
        _boolean(target["native_loss_writer_skipped"], "native_loss_writer_skipped")
        for field in ("current_soldiers", "maximum_soldiers"):
            _integer(target[field], field)
        data = target["replenishment_records_v1"]
        if data is not None:
            data = normalize_regiment_replenishment_records_v1([data])[0]
        targets.append({**deepcopy(target), "replenishment_records_v1": data})
    return {**deepcopy(top), "groups": groups, "target_regiments": targets}
