"""Normalize the independent current-player native spiritual-fulfillment type."""
from __future__ import annotations

from .religion_context_addon_schema import religion_context_addon_schema

from typing import Mapping


def normalize_player_spiritual_fulfillment_type_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    if value is None:
        return None
    keys = {"schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "date_raw", "played_character_id", "spiritual_fulfillment_type_key",
            "has_christian_fulfillment_type"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != religion_context_addon_schema("ck3_12003_spiritual_fulfillment_type_v1", current_context)
            or value["read_only"] is not True or type(value["available"]) is not bool):
        raise ValueError("native spiritual-fulfillment type schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native spiritual-fulfillment type differs from the current context")
    if value["spiritual_fulfillment_type_key"] is not None and not isinstance(value["spiritual_fulfillment_type_key"], str):
        raise ValueError("native spiritual-fulfillment type key is malformed")
    if value["has_christian_fulfillment_type"] is not None and type(value["has_christian_fulfillment_type"]) is not bool:
        raise ValueError("native Christian spiritual-fulfillment predicate is malformed")
    if value["available"]:
        if (value["unavailable_reason"] is not None or value["spiritual_fulfillment_type_key"] is None
                or value["has_christian_fulfillment_type"] is None):
            raise ValueError("available native spiritual-fulfillment type lost actual values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native spiritual-fulfillment type lost its reason")
    return dict(value)
