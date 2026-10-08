"""Strict current committed first-route target contributor observation.

The nested roster keeps the existing native_current_province_mode0 wire
lineage.  The outer family identifies its target Province context.  Neither
subject absence nor duplicate subject positions predicts arrival usage.
"""
from __future__ import annotations

from .army_current_province_supply_contributors_contract import (
    normalize_current_province_supply_contributors_v1,
)

FAMILY_KEY = "current_first_route_target_supply_contributors_v1"
SOURCE = "native_current_first_route_target_supply_contributors_12004"
INPUT_BASIS = "captured_committed_first_route_target"
KEYS = frozenset({
    "source", "status", "unavailable_reason", "current_target_inputs_ready",
    "subject_army_id", "subject_carmy_id", "current_province_id",
    "first_route_target_province_id", "route_source_count", "target_contributors_v1",
    "subject_matching_occurrence_indices", "subject_included_occurrence_count",
    "input_basis", "actual_arrival_observed", "actual_after_arrival_usage_observed",
    "full_arrival_supply_transition_ready",
})
STATUSES = frozenset({"available", "no_committed_target", "partial", "unavailable"})


def _i32(value, name, *, nullable=True):
    if value is None and nullable:
        return None
    if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
        raise ValueError(f"{name} must be a signed int32" + (" or null" if nullable else ""))
    return value


def _check_army_context(value, family):
    if not isinstance(value, dict):
        raise ValueError("first-route target armycontext must be an object")
    army_id = _i32(value.get("army_id"), "armycontext.army_id", nullable=False)
    if army_id != family["subject_army_id"]:
        raise ValueError("first-route target subject disagrees with same-frame armycontext")
    if value.get("current_province_id") is not None:
        province = _i32(value["current_province_id"], "armycontext.current_province_id", nullable=False)
        if family["current_province_id"] is not None and province != family["current_province_id"]:
            raise ValueError("first-route target current Province disagrees with same-frame armycontext")
    route = value.get("route_province_ids")
    if route is not None:
        if not isinstance(route, list):
            raise ValueError("armycontext.route_province_ids must be an array")
        for province in route:
            _i32(province, "armycontext.route_province_ids item", nullable=False)
        if family["first_route_target_province_id"] is not None:
            if not route or route[0] != family["first_route_target_province_id"]:
                raise ValueError("first-route target disagrees with same-frame route_province_ids[0]")
        elif family["status"] == "no_committed_target" and route:
            raise ValueError("no committed target disagrees with same-frame route")
    count = value.get("route_source_count")
    if count is not None:
        _i32(count, "armycontext.route_source_count", nullable=False)
        if family["route_source_count"] is not None and count != family["route_source_count"]:
            raise ValueError("first-route target count disagrees with same-frame armycontext")


def normalize_current_first_route_target_supply_contributors_v1(
    value, expected_army_id=None, expected_carmy_id=None, army_context=None,
):
    """Preserve all 16 native fields, including partial scalar/roster separation."""
    if not isinstance(value, dict) or set(value) != KEYS:
        raise ValueError("current first-route target contributors must have exactly 16 keys")
    result = dict(value)
    if result["source"] != SOURCE or result["input_basis"] != INPUT_BASIS:
        raise ValueError("current first-route target contributors have an unknown source or input basis")
    status = result["status"]
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("current first-route target contributors status is malformed")
    reason = result["unavailable_reason"]
    if status in {"available", "no_committed_target"}:
        if reason is not None:
            raise ValueError("available/no-target first-route observation requires a null reason")
    elif not isinstance(reason, str) or not reason:
        raise ValueError("partial/unavailable first-route observation requires a nonempty reason")
    if type(result["current_target_inputs_ready"]) is not bool:
        raise ValueError("current_target_inputs_ready must be boolean")
    for key in ("actual_arrival_observed", "actual_after_arrival_usage_observed",
                "full_arrival_supply_transition_ready"):
        if result[key] is not False:
            raise ValueError(f"{key} must remain false for a current target observation")
    for key in ("subject_army_id", "subject_carmy_id", "current_province_id",
                "first_route_target_province_id", "route_source_count",
                "subject_included_occurrence_count"):
        _i32(result[key], FAMILY_KEY + "." + key)
    for key, expected in (("subject_army_id", expected_army_id),
                          ("subject_carmy_id", expected_carmy_id)):
        if expected is not None:
            _i32(expected, "expected_" + key, nullable=False)
            if result[key] != expected:
                raise ValueError(f"first-route target {key} disagrees with its ArmyStrength row")
    indices = result["subject_matching_occurrence_indices"]
    if not isinstance(indices, list):
        raise ValueError("subject_matching_occurrence_indices must be an array")
    last = -1
    for index in indices:
        _i32(index, "subject_matching_occurrence_indices item", nullable=False)
        if index <= last:
            raise ValueError("subject matching indices must preserve increasing stored positions")
        last = index
    result["subject_matching_occurrence_indices"] = list(indices)
    nested = result["target_contributors_v1"]
    if nested is not None:
        nested = normalize_current_province_supply_contributors_v1(nested)
        result["target_contributors_v1"] = nested
        for nested_key, outer_key in (("province_id", "first_route_target_province_id"),
                                      ("subject_army_id", "subject_army_id"),
                                      ("subject_carmy_id", "subject_carmy_id")):
            if nested[nested_key] != result[outer_key]:
                raise ValueError(f"nested target contributors {nested_key} disagrees with its context")
        occurrences = nested["occurrences"]
        for index in indices:
            if index >= len(occurrences):
                raise ValueError("subject matching index is outside the captured target roster")
            occurrence = occurrences[index]
            if (occurrence["army_id"] != result["subject_army_id"]
                    or occurrence["native_carmy_id"] is not None
                    and occurrence["native_carmy_id"] != result["subject_carmy_id"]):
                raise ValueError("subject matching index does not identify the resolved subject")
        if nested["contributors_ready"]:
            matching = [index for index, occurrence in enumerate(occurrences)
                        if occurrence["army_id"] == result["subject_army_id"]
                        and occurrence["native_carmy_id"] == result["subject_carmy_id"]]
            if indices != matching:
                raise ValueError("complete target roster disagrees with subject matching positions")
            included = sum(occurrences[index]["included"] is True for index in matching)
            if result["subject_included_occurrence_count"] != included:
                raise ValueError("complete target roster disagrees with included subject count")
        elif result["subject_included_occurrence_count"] is not None:
            raise ValueError("partial target roster cannot claim a complete included subject count")
    elif indices or result["subject_included_occurrence_count"] is not None:
        raise ValueError("missing target roster cannot supply subject occurrence witnesses")
    if status == "available":
        if (result["current_target_inputs_ready"] is not True or nested is None
                or nested["status"] != "available" or nested["contributors_ready"] is not True
                or nested["current_usage_ready"] is not True):
            raise ValueError("available first-route target requires complete native target inputs")
        for key in ("subject_army_id", "subject_carmy_id",
                    "first_route_target_province_id", "route_source_count"):
            if result[key] is None:
                raise ValueError("available first-route target has a missing context identity")
        if result["route_source_count"] <= 0:
            raise ValueError("available first-route target requires a committed route entry")
    elif result["current_target_inputs_ready"]:
        raise ValueError("incomplete/no-target observation cannot be current-target ready")
    if status == "no_committed_target":
        if (result["route_source_count"] != 0 or result["first_route_target_province_id"] is not None
                or nested is not None or indices or result["subject_included_occurrence_count"] is not None):
            raise ValueError("no committed target must preserve an empty route and absent target observation")
    if army_context is not None:
        _check_army_context(army_context, result)
    return result
