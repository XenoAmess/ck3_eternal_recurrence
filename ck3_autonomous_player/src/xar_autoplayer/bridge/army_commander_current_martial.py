"""Optional current total martial of the actual assigned Army commander.

The parent current-role identity is authoritative. Candidate quality and
contextual selected-side martial are independent observations.
"""

from __future__ import annotations


CURRENT_COMMANDER_TOTAL_MARTIAL_SOURCE = (
    "native_current_assigned_commander_total_skill_cache"
)


def normalize_current_commander_total_martial(
    value: object,
    *,
    expected_current_commander: dict[str, object],
) -> dict[str, object] | None:
    """Retain legacy null and the native signed32 total-cache getter value."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("native current_total_martial must be an object or null")
    required = (
        "status", "source", "source_character_id", "skill_index", "value",
        "unavailable_reason",
    )
    if any(name not in value for name in required):
        raise ValueError("native current_total_martial is missing an observation field")
    status = value["status"]
    if (
        status not in ("available", "unavailable")
        or value["source"] != CURRENT_COMMANDER_TOTAL_MARTIAL_SOURCE
        or type(value["skill_index"]) is not int
        or value["skill_index"] != 1
    ):
        raise ValueError("native current_total_martial status/source/skill index is malformed")
    parent_id = expected_current_commander.get("character_id")
    source_id = value["source_character_id"]
    if source_id is not None and (
        type(source_id) is not int or not 0 <= source_id <= 2**31 - 1
    ):
        raise ValueError("native current_total_martial source_character_id must be a full native int32 ID or null")
    if type(source_id) is not type(parent_id) or source_id != parent_id:
        raise ValueError("native current_total_martial source disagrees with the actual current commander")
    amount = value["value"]
    if status == "available":
        if expected_current_commander.get("status") != "available" or source_id is None:
            raise ValueError("available current_total_martial requires the actual available current commander")
        if type(amount) is not int or not -(2**31) <= amount <= 2**31 - 1:
            raise ValueError("native current_total_martial value must be a signed32 getter value")
        if value["unavailable_reason"] is not None:
            raise ValueError("available current_total_martial must have a null reason")
    else:
        if amount is not None:
            raise ValueError("unavailable current_total_martial must retain a null value")
        reason = value["unavailable_reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("unavailable current_total_martial requires a concrete reason")
    return dict(value)
