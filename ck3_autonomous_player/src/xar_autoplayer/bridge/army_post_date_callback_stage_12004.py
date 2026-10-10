"""Source-bound stage join over the existing actual4 callback records.

The caller supplies the existing strictly normalized optional family. This
module does not read a query roster, native memory, a bucket or a game clock.
It records the source route of an already retained invocation; it does not
simulate the preceding manager mutators or call the original callback.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


_DISPATCHER_RETURN = 0x2A9AB4B
_VALUE_KEYS = ("supply_raw", "last_supply_update_date_raw64", "supply_updated_byte_raw")
_PRIOR_STAGES = (
    "saved_month_bit2_cleanup_then_daily_gathering_and_queue_transitions",
    "saved_month_bit2_regular_refill",
    "unconditional_daily_assault_table_consumer",
    "fixed_end_ordered_late_army_roster",
    "stored_day_unsigned_modulo30_pointer_bucket",
)


def _integer(value: object, bits: int, unsigned: bool = False) -> bool:
    low = 0 if unsigned else -(1 << (bits - 1))
    high = (1 << bits) - 1 if unsigned else (1 << (bits - 1)) - 1
    return type(value) is int and low <= value <= high


def project_army_post_date_callback_stage_12004(
    observations: Mapping | None,
) -> dict:
    """Keep each retained invocation independent and bind only its known route.

    A source-matched return address establishes a position in the dispatcher,
    while the before fields establish that record's callback initial state.
    Neither result proves that this subject occurred in the earlier Army
    roster, nor supplies its historical storedD, bucket or physical ordinal.
    A partial before capture keeps every independently recorded scalar.
    """
    result = {
        "projection_kind": "army_post_date_callback_stage_12004",
        "status": "unavailable",
        "input_basis": "existing_normalized_actual_supply_callback_observations_v1",
        "dispatcher_rva": "0x2A9A570",
        "source_callsite_rva": "0x2A9AB46",
        "source_caller_return_rva": "0x2A9AB4B",
        "source_prior_stage_order": list(_PRIOR_STAGES),
        "events": [],
        "retained_event_count": 0,
        "source_matched_event_count": 0,
        "complete_source_matched_entry_count": 0,
        "journal_counters": None,
        "observer_installed": None,
        "missing_inputs": [],
        "unavailable_reason": "actual_supply_callback_observation_family_absent",
        "current_query_membership_used": False,
        "late_callee_effects_modeled": False,
        "actual_stored_bucket_ordinal_observed": False,
        "complete_prior_manager_transition_ready": False,
        "full_daily_ready": False,
        "full_monthly_ready": False,
        "new_live_evidence": False,
        "native_calls_executed": 0,
        "native_writes_executed": 0,
    }
    if observations is None:
        return result
    if (not isinstance(observations, Mapping)
            or observations.get("status") != "available"
            or observations.get("source") != "native_natural_supply_callback_entry_return"
            or observations.get("identity_basis")
            != "public_unit_and_native_carmy_full_ids_at_invocation"):
        result["unavailable_reason"] = "normalized_actual4_callback_provenance_unavailable"
        return result
    events = observations.get("events")
    if (not isinstance(events, list)
            or not _integer(observations.get("event_count"), 64, True)
            or observations["event_count"] != len(events)):
        result["unavailable_reason"] = "normalized_actual4_callback_event_list_unavailable"
        return result
    result["observer_installed"] = observations.get("observer_installed")
    result["journal_counters"] = {
        key: observations.get(key) for key in (
            "oldest_available_sequence", "latest_sequence", "overwritten_events",
            "unattributed_capture_failures",
        )
    }
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            result["missing_inputs"].append(f"events[{index}].normalized_event")
            continue
        before = event.get("before")
        before = before if isinstance(before, Mapping) else {}
        raw_fields = {key: deepcopy(before.get(key)) for key in _VALUE_KEYS}
        missing = []
        widths = (("supply_raw", 64, False),
                  ("last_supply_update_date_raw64", 64, True),
                  ("supply_updated_byte_raw", 8, True))
        for key, bits, unsigned in widths:
            if not _integer(raw_fields[key], bits, unsigned):
                missing.append("before." + key)
        date = event.get("passed_date_raw64")
        if not _integer(date, 64, True):
            missing.append("passed_date_raw64")
        route_matches = event.get("caller_return_rva") == _DISPATCHER_RETURN
        row = {
            "retained_event_index": index,
            "sequence": event.get("sequence"),
            "army_id": event.get("army_id"),
            "native_carmy_id": event.get("native_carmy_id"),
            "caller_return_rva": event.get("caller_return_rva"),
            "source_dispatcher_route_matches": route_matches,
            "source_stage": (
                "after_late_army_roster_at_stored_bucket_callback_entry"
                if route_matches else None
            ),
            "passed_date_raw64": deepcopy(date),
            "callback_entry_fields": raw_fields,
            "callback_entry_fields_complete": not missing,
            "source_matched_callback_entry_ready": route_matches and not missing,
            "same_instance_after": event.get("same_instance_after"),
            "capture_failure_flags": event.get("capture_failure_flags"),
            "subject_was_processed_in_late_roster": None,
            "subject_late_reset_executed": None,
            "stored_day_index_at_dispatch_u32": None,
            "selected_bucket_at_dispatch_i32": None,
            "actual_bucket_occurrence_index_i32": None,
            "prior_callee_outputs_observed": False,
            "missing_inputs": missing,
        }
        result["events"].append(row)
        result["source_matched_event_count"] += int(route_matches)
        result["complete_source_matched_entry_count"] += int(
            row["source_matched_callback_entry_ready"]
        )
        result["missing_inputs"].extend(
            f"events[{index}].{key}" for key in missing
        )
    result["retained_event_count"] = len(events)
    result["status"] = "partial" if result["missing_inputs"] else "available"
    result["unavailable_reason"] = (
        "callback_entry_capture_partial" if result["missing_inputs"] else None
    )
    result["empty_matching_events_meaning"] = (
        "no retained matching completed invocation; no no-callback or no-change claim"
    )
    return result
