"""Normalize the current Rite's fixed native confession status."""
from __future__ import annotations

from typing import Mapping


def normalize_player_confession_rite_permission_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    if value is None:
        return None
    keys = {"schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "date_raw", "played_character_id", "rite_id", "tenet_key",
            "current_rite_status", "has_at_least_permitted"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_confession_rite_permission_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or value["tenet_key"] != "tenet_confession"):
        raise ValueError("native confession Rite permission schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native confession Rite permission differs from the current context")
    if value["rite_id"] != current_context["rite_id"]:
        raise ValueError("native confession permission belongs to another Rite")
    if value["rite_id"] is not None and (type(value["rite_id"]) is not int or not 0 <= value["rite_id"] <= 0xFFFFFFFF):
        raise ValueError("native confession Rite identity is malformed")
    if value["available"]:
        state = value["current_rite_status"]
        if (value["unavailable_reason"] is not None or value["rite_id"] is None
                or type(state) is not int or not 0 <= state <= 4
                or type(value["has_at_least_permitted"]) is not bool
                or value["has_at_least_permitted"] != (state in (3, 4))):
            raise ValueError("available native confession permission lost actual state")
    elif (not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]
            or value["current_rite_status"] is not None or value["has_at_least_permitted"] is not None):
        raise ValueError("unavailable native confession permission lost its failure distinction")
    return dict(value)
