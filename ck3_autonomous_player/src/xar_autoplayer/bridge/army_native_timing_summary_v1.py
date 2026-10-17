"""Retain existing Native timing scalars without adding queries or timers."""

from __future__ import annotations

_FIELDS = ("read_total_ns", "owner_query_ns", "baseline_read_ns", "rich_attach_ns", "serialize_ns")


def retained_native_timing(payload: dict[str, object]) -> dict[str, object]:
    """Omit missing/malformed diagnostics while preserving the business result."""
    value = payload.get("army_native_timing_v1")
    if not isinstance(value, dict) or set(value) != set(_FIELDS):
        return {}
    if any(type(value[key]) is not int or value[key] < 0 for key in _FIELDS):
        return {}
    if (
        max(value["baseline_read_ns"], value["rich_attach_ns"]) > value["owner_query_ns"]
        or value["owner_query_ns"] > value["read_total_ns"]
    ):
        return {}
    return {"army_native_timing_v1": {key: value[key] for key in _FIELDS}}
