"""Owned observations of natural native loss-writer calls, never a forecast."""

from __future__ import annotations


_FAMILY_KEYS = {
    "status", "source", "membership_basis", "observer_installed",
    "oldest_available_sequence", "latest_sequence", "overwritten_events",
    "unattributed_capture_failures", "event_count", "events",
}
_EVENT_KEYS = {
    "sequence", "army_regiment_id", "request_raw", "request_scale",
    "caller_return_rva", "caller_kind", "observed_date_raw",
    "before_current_soldiers", "before_maximum_soldiers",
    "after_current_soldiers", "after_maximum_soldiers", "same_instance_after",
    "cached_current_delta", "cached_maximum_delta", "capture_failure_flags",
    "native_data_record_count", "captured_data_record_count",
    "physical_capture_complete", "physical_debit_observed",
    "actual_physical_soldier_debit", "physical_slot_count", "data_aliases",
    "physical_slots",
}
_CALLERS = {
    "supply_preferred", "siege_or_raid_preferred", "residual_allocator",
    "other_writer_caller",
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


def _physical_values(value: object, name: str) -> dict[str, int | None]:
    row = _object(value, {"current_soldiers", "maximum_soldiers", "state_raw"}, name)
    return {key: _integer(raw, f"{name}.{key}", optional=True)
            for key, raw in row.items()}


def normalize_actual_loss_writer_observations_v1(
    value: object, *, current_regiment_ids: list[int],
) -> dict[str, object] | None:
    """Keep physical before/after and cache movement separate; allow empty history."""
    if value is None:
        return None
    family = _object(value, _FAMILY_KEYS, "actual_loss_writer_observations_v1")
    if (family["status"] != "available"
            or family["source"] != "native_natural_writer_entry_return"
            or family["membership_basis"] != "membership_at_query"):
        raise ValueError("native actual loss observation provenance is malformed")
    result: dict[str, object] = {
        "status": family["status"], "source": family["source"],
        "membership_basis": family["membership_basis"],
        "observer_installed": _boolean(family["observer_installed"], "observer_installed"),
    }
    for key in ("oldest_available_sequence", "latest_sequence", "overwritten_events",
                "unattributed_capture_failures", "event_count"):
        result[key] = _integer(family[key], key, bits=64, unsigned=True)
    events = family["events"]
    if not isinstance(events, list) or len(events) != result["event_count"]:
        raise ValueError("native actual loss event_count is malformed")
    normalized = []
    for index, raw_event in enumerate(events):
        name = f"actual_loss_writer_observations_v1.events[{index}]"
        event = _object(raw_event, _EVENT_KEYS, name)
        row: dict[str, object] = {}
        for key in ("sequence", "capture_failure_flags", "captured_data_record_count",
                    "physical_slot_count"):
            row[key] = _integer(event[key], f"{name}.{key}", bits=64, unsigned=True)
        row["army_regiment_id"] = _integer(event["army_regiment_id"], f"{name}.army_regiment_id")
        if row["army_regiment_id"] not in current_regiment_ids:
            raise ValueError(f"native {name} is outside current full regiment IDs")
        row["request_raw"] = _integer(event["request_raw"], f"{name}.request_raw", bits=64)
        if type(event["request_scale"]) is not int or event["request_scale"] != 100_000:
            raise ValueError(f"native {name}.request_scale is malformed")
        row["request_scale"] = 100_000
        row["caller_return_rva"] = _integer(event["caller_return_rva"],
            f"{name}.caller_return_rva", bits=64, unsigned=True, optional=True)
        if event["caller_kind"] not in _CALLERS:
            raise ValueError(f"native {name}.caller_kind is malformed")
        row["caller_kind"] = event["caller_kind"]
        for key in ("observed_date_raw", "before_current_soldiers", "before_maximum_soldiers",
                    "after_current_soldiers", "after_maximum_soldiers", "native_data_record_count"):
            row[key] = _integer(event[key], f"{name}.{key}", optional=True)
        for key in ("cached_current_delta", "cached_maximum_delta", "actual_physical_soldier_debit"):
            row[key] = _integer(event[key], f"{name}.{key}", bits=64, optional=True)
        for key in ("same_instance_after", "physical_capture_complete", "physical_debit_observed"):
            row[key] = _boolean(event[key], f"{name}.{key}")
        aliases, slots = event["data_aliases"], event["physical_slots"]
        if (not isinstance(aliases, list) or len(aliases) != row["captured_data_record_count"]
                or not isinstance(slots, list) or len(slots) != row["physical_slot_count"]):
            raise ValueError(f"native {name} physical coverage counts are malformed")
        row["data_aliases"] = []
        for alias_index, raw_alias in enumerate(aliases):
            alias_name = f"{name}.data_aliases[{alias_index}]"
            alias = _object(raw_alias, {"data_record_index", "persistent_regiment_id",
                                      "data_chunk_ordinal", "physical_slot_index"}, alias_name)
            parsed = {key: _integer(raw, f"{alias_name}.{key}",
                                   optional=key != "data_record_index")
                      for key, raw in alias.items()}
            if (parsed["physical_slot_index"] is not None
                    and not 0 <= parsed["physical_slot_index"] < len(slots)):
                raise ValueError(f"native {alias_name}.physical_slot_index is malformed")
            row["data_aliases"].append(parsed)
        row["physical_slots"] = []
        for slot_index, raw_slot in enumerate(slots):
            slot_name = f"{name}.physical_slots[{slot_index}]"
            slot = _object(raw_slot, {"physical_slot_index", "before", "after",
                                     "same_instance_after"}, slot_name)
            if type(slot["physical_slot_index"]) is not int or slot["physical_slot_index"] != slot_index:
                raise ValueError(f"native {slot_name}.physical_slot_index is malformed")
            row["physical_slots"].append({
                "physical_slot_index": slot_index,
                "before": _physical_values(slot["before"], f"{slot_name}.before"),
                "after": _physical_values(slot["after"], f"{slot_name}.after"),
                "same_instance_after": _boolean(slot["same_instance_after"],
                                                  f"{slot_name}.same_instance_after"),
            })
        if row["physical_debit_observed"] != (row["actual_physical_soldier_debit"] is not None):
            raise ValueError(f"native {name} physical observation availability is malformed")
        if row["physical_debit_observed"] and not row["physical_capture_complete"]:
            raise ValueError(f"native {name} cannot publish a complete physical debit from partial reads")
        normalized.append(row)
    result["events"] = normalized
    return result
