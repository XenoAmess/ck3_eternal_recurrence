"""Preserve the source-backed current holy-order quote branch observation."""

from __future__ import annotations

from collections.abc import Mapping


def validate_holy_order_hire_cost_context(value: object) -> None:
    if (not isinstance(value, Mapping) or type(value.get("available")) is not bool
            or type(value.get("order_title_resolved")) is not bool
            or value.get("resource_scale") != 100000):
        raise ValueError("native holy-order hire cost context is malformed")
    for key in ("order_title_id", "order_title_holder_id"):
        reference = value.get(key)
        if reference is not None and (type(reference) is not int or not 0 <= reference <= 0xFFFFFFFF):
            raise ValueError(f"native holy-order cost title reference is malformed: {key}")
    for key in ("title_holder_is_player", "patron_is_player", "employed_by_other"):
        if value.get(key) is not None and type(value[key]) is not bool:
            raise ValueError(f"native holy-order cost branch predicate is malformed: {key}")
    factor = value.get("selected_patron_multiplier_raw")
    if factor is not None and (type(factor) is not int or not -(1 << 63) <= factor < (1 << 63)):
        raise ValueError("native holy-order selected patron multiplier is malformed")
    branch = value.get("cost_branch")
    branches = ("title_holder_zero", "ordinary", "patron_hire", "patron_recall")
    if branch is not None and branch not in branches:
        raise ValueError("native holy-order hire cost branch is malformed")
    if not value["available"]:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("unavailable native holy-order cost context lost its reason")
        return
    if (value.get("unavailable_reason") is not None or value.get("order_title_id") is None
            or type(value.get("title_holder_is_player")) is not bool or branch not in branches):
        raise ValueError("available native holy-order cost context is incomplete")
    if branch == "title_holder_zero":
        if (value["title_holder_is_player"] is not True
                or any(value.get(key) is not None for key in (
                    "patron_is_player", "employed_by_other", "selected_patron_multiplier_raw"))):
            raise ValueError("native holy-order early holder exemption sampled later branches")
    elif value["title_holder_is_player"] is not False:
        raise ValueError("native holy-order later quote branch conflicts with holder exemption")
    elif branch == "ordinary":
        if (value.get("patron_is_player") is not False or value.get("employed_by_other") is not None
                or factor is not None):
            raise ValueError("native holy-order ordinary branch contains patron inputs")
    elif (value.get("patron_is_player") is not True or type(value.get("employed_by_other")) is not bool
          or value["employed_by_other"] != (branch == "patron_recall") or factor is None):
        raise ValueError("native holy-order selected patron cost branch is incomplete")
