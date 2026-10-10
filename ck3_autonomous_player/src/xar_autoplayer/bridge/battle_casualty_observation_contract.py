"""Owned native casualty applications with separately captured physical debit."""

from __future__ import annotations


_LEAF = "battle_casualty_observations_v1"
_CAPACITY = 256
_FAMILY_KEYS = {
    "status", "source", "membership_basis", "observer_installed",
    "oldest_available_sequence", "latest_sequence", "overwritten_events",
    "event_count", "events",
}
_OWNER_KEYS = {
    "reference_demanded", "requested_full_id", "resolved_full_id",
    "used_fallback", "read_complete",
}
_EVENT_KEYS = {
    "sequence", "entry_identity", "entry_army_regiment_id",
    "soft_request_raw", "hard_request_raw", "raw_scale", "soldiers_scale",
    "observed_date_raw", "before_fighting_raw", "before_soft_raw",
    "after_fighting_raw", "after_soft_raw", "same_entry_after",
    "nested_writer_event_count", "writer_sequence", "writer_army_regiment_id",
    "writer_request_raw", "entry_writer_association_proven",
    "physical_capture_complete", "actual_physical_soldier_debit", "owner_army",
    "owner_unit", "owner_character_id", "original_return_identity",
    "owner_hard_ledger_after_raw",
}


def _object(value: object, keys: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native {name} schema is malformed")
    return value


def _integer(value: object, name: str, *, bits: int = 32,
             unsigned: bool = False, optional: bool = False) -> int | None:
    if optional and value is None:
        return None
    low = 0 if unsigned else -(2 ** (bits - 1))
    high = 2**bits - 1 if unsigned else 2 ** (bits - 1) - 1
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native {name} must be {'unsigned' if unsigned else 'signed'} int{bits}")
    return value


def _boolean(value: object, name: str, *, optional: bool = False) -> bool | None:
    if optional and value is None:
        return None
    if type(value) is not bool:
        raise ValueError(f"native {name} must be bool{' or null' if optional else ''}")
    return value


def _owner(value: object, name: str) -> dict[str, object]:
    raw = _object(value, _OWNER_KEYS, name)
    return {
        "reference_demanded": _boolean(raw["reference_demanded"], name + ".reference_demanded"),
        "requested_full_id": _integer(raw["requested_full_id"], name + ".requested_full_id", optional=True),
        "resolved_full_id": _integer(raw["resolved_full_id"], name + ".resolved_full_id", optional=True),
        "used_fallback": _boolean(raw["used_fallback"], name + ".used_fallback", optional=True),
        "read_complete": _boolean(raw["read_complete"], name + ".read_complete"),
    }


def _event(value: object, name: str) -> dict[str, object]:
    raw = _object(value, _EVENT_KEYS, name)
    result: dict[str, object] = {}
    for key in ("sequence", "entry_identity", "original_return_identity"):
        result[key] = _integer(raw[key], name + "." + key, bits=64, unsigned=True)
    result["writer_sequence"] = _integer(
        raw["writer_sequence"], name + ".writer_sequence", bits=64, unsigned=True, optional=True)
    result["nested_writer_event_count"] = _integer(
        raw["nested_writer_event_count"], name + ".nested_writer_event_count", unsigned=True)
    for key in ("entry_army_regiment_id", "observed_date_raw",
                "writer_army_regiment_id", "owner_character_id"):
        result[key] = _integer(raw[key], name + "." + key, optional=True)
    for key in ("soft_request_raw", "hard_request_raw"):
        result[key] = _integer(raw[key], name + "." + key, bits=64)
    for key in ("before_fighting_raw", "before_soft_raw", "after_fighting_raw",
                "after_soft_raw", "writer_request_raw", "actual_physical_soldier_debit",
                "owner_hard_ledger_after_raw"):
        result[key] = _integer(raw[key], name + "." + key, bits=64, optional=True)
    for key, scale in (("raw_scale", 100_000), ("soldiers_scale", 1)):
        if type(raw[key]) is not int or raw[key] != scale:
            raise ValueError(f"native {name}.{key} must be {scale}")
        result[key] = scale
    for key in ("same_entry_after", "entry_writer_association_proven",
                "physical_capture_complete"):
        result[key] = _boolean(raw[key], name + "." + key)
    for key in ("owner_army", "owner_unit"):
        result[key] = _owner(raw[key], name + "." + key)
    return result


def normalize_battle_casualty_observations_v1(value: object) -> dict[str, object] | None:
    """Preserve zero, failed reads, raw owner IDs and the native association flags."""
    if value is None:
        return None
    family = _object(value, _FAMILY_KEYS, _LEAF)
    if (family["status"] != "available"
            or family["source"] != "native_battle_casualty_application_entry_return"
            or family["membership_basis"] != "membership_at_query"):
        raise ValueError("native battle casualty observation provenance is malformed")
    result: dict[str, object] = {
        "status": family["status"], "source": family["source"],
        "membership_basis": family["membership_basis"],
        "observer_installed": _boolean(family["observer_installed"], _LEAF + ".observer_installed"),
    }
    for key in ("oldest_available_sequence", "latest_sequence", "overwritten_events", "event_count"):
        result[key] = _integer(family[key], _LEAF + "." + key, bits=64, unsigned=True)
    events = family["events"]
    if (not isinstance(events, list) or len(events) != result["event_count"]
            or len(events) > _CAPACITY):
        raise ValueError("native battle casualty event_count is malformed")
    result["events"] = [_event(event, f"{_LEAF}.events[{index}]")
                        for index, event in enumerate(events)]
    oldest, latest = result["oldest_available_sequence"], result["latest_sequence"]
    if oldest > latest:
        raise ValueError("native battle casualty retained sequence bounds disagree")
    previous = None
    for event in result["events"]:
        sequence = event["sequence"]
        if (sequence < oldest or sequence > latest
                or previous is not None and sequence <= previous):
            raise ValueError("native battle casualty events disagree with retained sequence order/bounds")
        previous = sequence
    return result
