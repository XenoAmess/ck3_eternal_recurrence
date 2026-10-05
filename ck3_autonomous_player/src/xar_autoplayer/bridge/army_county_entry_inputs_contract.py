"""Exact .3 current county-entry inputs; never an applied-loss event ledger."""

from __future__ import annotations


_BUDGET_FIELDS = (
    "whole_soldiers", "current_loss_budget", "effective_fraction_raw",
    "minimum_multiplier_raw", "loaded_minimum_soldiers",
)
_CONDITION_FIELDS = (
    "actor_character_id", "source_province_id", "target_province_id", "mode", "passes",
)


def _integer(value: object, name: str, bits: int = 32) -> int:
    if type(value) is not int or not -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
        raise ValueError(f"native {name} must be signed int{bits}")
    return value


def _status(value: dict[str, object], fields: tuple[str, ...], name: str) -> bool:
    status, reason = value["status"], value["unavailable_reason"]
    if type(status) is not str or status not in {"available", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    if status == "unavailable":
        if type(reason) is not str or not reason or any(value[k] is not None for k in fields):
            raise ValueError(f"native unavailable {name} requires a reason and null observations")
        return False
    if reason is not None:
        raise ValueError(f"native available {name} cannot have unavailable_reason")
    return True


def normalize_army_county_entry_inputs_v1(
    value: object, *, current_soldiers: int, name: str = "county_entry_inputs_v1"
) -> dict[str, object]:
    """Validate native current outputs and independently unavailable route condition."""
    if not isinstance(value, dict) or set(value) != {
        "status", "source", "unavailable_reason", "fraction_scale", "soldier_scale",
        "condition", *_BUDGET_FIELDS,
    }:
        raise ValueError(f"native {name} schema is malformed")
    if value["source"] != "native_current_county_entry_inputs":
        raise ValueError(f"native {name}.source is malformed")
    if type(value["fraction_scale"]) is not int or value["fraction_scale"] != 100_000:
        raise ValueError(f"native {name}.fraction_scale must be 100000")
    if type(value["soldier_scale"]) is not int or value["soldier_scale"] != 1:
        raise ValueError(f"native {name}.soldier_scale must be whole soldiers (1)")
    available = _status(value, _BUDGET_FIELDS, name)
    result = dict(value)
    if available:
        for field in _BUDGET_FIELDS:
            bits = 64 if field in {"effective_fraction_raw", "minimum_multiplier_raw"} else 32
            result[field] = _integer(value[field], f"{name}.{field}", bits)
        if value["whole_soldiers"] != current_soldiers or not 0 <= value["current_loss_budget"] <= current_soldiers:
            raise ValueError(f"native {name} must match the same-frame whole strength and bounded budget")
    condition = value["condition"]
    if not isinstance(condition, dict) or set(condition) != {
        "status", "source", "unavailable_reason", *_CONDITION_FIELDS,
    } or condition["source"] != "current_stored_route_first_province":
        raise ValueError(f"native {name}.condition schema is malformed")
    condition_available = _status(condition, _CONDITION_FIELDS, f"{name}.condition")
    if condition_available:
        if not available:
            raise ValueError(f"native unavailable {name} cannot publish an available condition")
        for field in _CONDITION_FIELDS[:-1]:
            _integer(condition[field], f"{name}.condition.{field}")
        if condition["actor_character_id"] < 0 or condition["source_province_id"] < 1 or condition["target_province_id"] < 1:
            raise ValueError(f"native {name}.condition requires resolved actor and province identities")
        if condition["mode"] not in {0, 1} or type(condition["passes"]) is not bool:
            raise ValueError(f"native {name}.condition requires native mode0/1 and an observed boolean")
    result["condition"] = dict(condition)
    return result
