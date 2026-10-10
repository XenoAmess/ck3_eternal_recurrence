"""Owned actual CArmy supply callback snapshots from the exact native observer."""

from __future__ import annotations


_FAMILY_KEYS = {
    "status", "source", "identity_basis", "observer_installed",
    "oldest_available_sequence", "latest_sequence", "overwritten_events",
    "unattributed_capture_failures", "event_count", "events",
}
_EVENT_KEYS = {
    "sequence", "army_id", "native_carmy_id", "passed_date_raw64",
    "caller_return_rva", "before", "after", "same_instance_after",
    "capture_failure_flags",
}
_VALUE_KEYS = {
    "supply_raw", "last_supply_update_date_raw64", "supply_updated_byte_raw",
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


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"native {name} must be bool")
    return value


def _values(value: object, name: str) -> dict[str, int | None]:
    row = _object(value, _VALUE_KEYS, name)
    return {
        "supply_raw": _integer(row["supply_raw"], name + ".supply_raw",
                               bits=64, optional=True),
        "last_supply_update_date_raw64": _integer(
            row["last_supply_update_date_raw64"],
            name + ".last_supply_update_date_raw64",
            bits=64, unsigned=True, optional=True),
        "supply_updated_byte_raw": _integer(
            row["supply_updated_byte_raw"], name + ".supply_updated_byte_raw",
            bits=8, unsigned=True, optional=True),
    }


def normalize_actual_supply_callback_observations_v1(
    value: object, *, current_army_id: int, current_native_carmy_id: int,
) -> dict[str, object] | None:
    """Preserve measured zero and partial reads; legacy absent leaf stays absent."""
    if value is None:
        return None
    family = _object(value, _FAMILY_KEYS, "actual_supply_callback_observations_v1")
    if (family["status"] != "available"
            or family["source"] != "native_natural_supply_callback_entry_return"
            or family["identity_basis"] != "public_unit_and_native_carmy_full_ids_at_invocation"):
        raise ValueError("native actual supply callback provenance is malformed")
    result: dict[str, object] = {
        "status": family["status"], "source": family["source"],
        "identity_basis": family["identity_basis"],
        "observer_installed": _boolean(family["observer_installed"], "observer_installed"),
    }
    for key in ("oldest_available_sequence", "latest_sequence", "overwritten_events",
                "unattributed_capture_failures", "event_count"):
        result[key] = _integer(family[key], key, bits=64, unsigned=True)
    events = family["events"]
    if not isinstance(events, list) or len(events) != result["event_count"]:
        raise ValueError("native actual supply callback event_count is malformed")
    normalized = []
    for index, raw_event in enumerate(events):
        name = f"actual_supply_callback_observations_v1.events[{index}]"
        event = _object(raw_event, _EVENT_KEYS, name)
        row: dict[str, object] = {
            "sequence": _integer(event["sequence"], name + ".sequence", bits=64, unsigned=True),
            "army_id": _integer(event["army_id"], name + ".army_id"),
            "native_carmy_id": _integer(event["native_carmy_id"], name + ".native_carmy_id"),
            "passed_date_raw64": _integer(event["passed_date_raw64"],
                name + ".passed_date_raw64", bits=64, unsigned=True, optional=True),
            "caller_return_rva": _integer(event["caller_return_rva"],
                name + ".caller_return_rva", bits=64, unsigned=True, optional=True),
            "before": _values(event["before"], name + ".before"),
            "after": _values(event["after"], name + ".after"),
            "same_instance_after": _boolean(event["same_instance_after"],
                name + ".same_instance_after"),
            "capture_failure_flags": _integer(event["capture_failure_flags"],
                name + ".capture_failure_flags", unsigned=True),
        }
        if (row["army_id"] != current_army_id
                or row["native_carmy_id"] != current_native_carmy_id):
            raise ValueError(f"native {name} does not match both current full Army identities")
        normalized.append(row)
    result["events"] = normalized
    return result
