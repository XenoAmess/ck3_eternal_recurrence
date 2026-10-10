"""Project independent copied natural-conception facts without a future draw."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

from ..bridge.conception_natural_observation_contract_12004 import JOURNAL_SCHEMA, SOURCE_PIN
from ..bridge.conception_incoming_caller_sourcebinding_12004 import (
    CallerSourceResolver, ExactImage, bind_owned_journal,
)

CHARACTER_MAGIC = 0x43686172
PROVIDER_RETURN = 0x2929C30
SAMPLE_RETURN = 0x2929D99


def _clock_matches(value: dict[str, Any], parent: dict[str, Any]) -> bool:
    return (value["clock_identity"] == parent["clock_identity"]
            and value["thread_id"] == parent["thread_id"] and value["sequence"] > 0)


def _key(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "clock_identity": event["before_event"]["clock_identity"],
        "parent_scope_id": event["before_event"]["sequence"],
        "process_clock": event["before_event"]["sequence"],
        "thread_id": event["thread_id"],
        "first_character": event["first_character"],
        "second_character": event["second_character"],
        "first_full_id": event["first_before"]["full_id"],
        "second_full_id": event["second_before"]["full_id"],
        "sample_receiver": event["sample_receiver"],
    }


def _same_key(child: dict[str, Any], parent: dict[str, Any]) -> bool:
    return all(child.get(name) == value for name, value in parent.items())


def _within_extent(child: dict[str, Any], event: dict[str, Any], parent: dict[str, Any]) -> bool:
    before, returned = child["before_event"], child["returned_event"]
    return (_clock_matches(before, parent) and _clock_matches(returned, parent)
            and event["before_event"]["sequence"] < before["sequence"]
            < returned["sequence"] < event["completed_event"]["sequence"])


def _parent_ready(event: dict[str, Any], journal: dict[str, Any], parent: dict[str, Any]) -> bool:
    if not (parent["clock_identity"] > 0 and parent["parent_scope_id"] > 0
            and parent["thread_id"] > 0 and event["process_id"] > 0
            and parent["first_character"] > 0 and parent["second_character"] > 0
            and parent["sample_receiver"] > 0 and parent["clock_identity"] == journal["clock_identity"]
            and event["event_clock_and_thread_match"] is True
            and event["generation_unchanged"] is True
            and event["original_called_once"] is True and event["original_returned"] is True
            and _clock_matches(event["before_event"], parent)
            and _clock_matches(event["completed_event"], parent)
            and event["completed_event"]["sequence"] > parent["process_clock"]):
        return False
    for role in ("first", "second"):
        before, after = event[role + "_before"], event[role + "_after"]
        if (before["full_id"] is None or before["full_id"] == (1 << 32) - 1
                or after["full_id"] != before["full_id"] or before["magic"] != CHARACTER_MAGIC
                or after["magic"] != CHARACTER_MAGIC):
            return False
    return True


def _provider(event: dict[str, Any], journal: dict[str, Any], parent: dict[str, Any], ready: bool) -> dict[str, Any]:
    child = event["provider"]
    result: dict[str, Any] = {"status": "unknown", "reason": "provider_child_unavailable", "first_qword_raw": None}
    if child is None:
        return result
    result["copied_output_before"] = child["output_before"]
    result["copied_output_after"] = child["output_after"]
    # Returned RAX/outptr equality is diagnostic only; the caller loads out[0].
    result["native_return_matches_output"] = child["native_return_matches_output"]
    ids = (child["first_full_id_before"], child["second_full_id_before"],
           child["first_full_id_after"], child["second_full_id_after"])
    expected_ids = (parent["first_full_id"], parent["second_full_id"]) * 2
    if not (ready and _same_key(child["parent"], parent) and child["parent"]["active"] is True
            and _within_extent(child, event, parent)
            and child["caller_return_rva"] == PROVIDER_RETURN
            and child["caller_return_pc"] == journal["image_base"] + PROVIDER_RETURN
            and child["process_id"] == event["process_id"] and child["thread_id"] == parent["thread_id"]
            and child["first_character"] == parent["first_character"]
            and child["second_character"] == parent["second_character"]
            and child["output_pointer"] > 0 and child["mode"] == 3 and child["fifth_argument"] == 0
            and child["original_returned"] is True and child["parent_extent_unchanged"] is True
            and child["event_clock_and_thread_match"] is True and child["actual_caller_input_ready"] is True
            and child["capture_failure_flags"] == 0 and event["duplicate_provider_returns"] == 0
            and ids == expected_ids and child["output_after"] is not None):
        result["reason"] = "provider_source_or_parent_not_qualified"
        return result
    result.update(status="source_bound_copied", reason=None, first_qword_raw=child["output_after"])
    return result


def _comparison(event: dict[str, Any], parent: dict[str, Any], ready: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "original_compare_available": False, "threshold_at_sample_signed64": None,
        "returned_sample_signed64": None, "original_sample_below_threshold": None,
        "copied_original_compare_causal": None, "reason": "sample_child_unavailable",
    }
    samples = event["sample"]
    if samples is None:
        return result
    child = samples["events"][0]
    threshold, sample = child["threshold_at_sample_signed64"], child["returned_rax_signed64"]
    result["threshold_at_sample_signed64"] = threshold
    result["returned_sample_signed64"] = sample
    before, after = child["state_before_2dword"], child["state_after_2dword"]
    state_matches = (before is not None and after is not None
                     and after[0] == ((before[0] + 2) & ((1 << 32) - 1)) and after[1] == before[1])
    if not (ready and _same_key(child["parent"], parent) and _within_extent(child, event, parent)
            and child["caller_return_rva"] == SAMPLE_RETURN
            and child["receiver"] == parent["sample_receiver"]
            and child["original_lower"] == 0 and child["original_upper"] == 10000000
            and child["original_returned"] is True
            and child["parent_extent_and_generation_unchanged"] is True
            and child["event_clock_and_thread_match"] is True
            and child["causal_sample_ready"] is True and child["sample_within_source_range"] is True
            and 0 <= sample <= 10000000 and child["state_transition_matches_source"] is True
            and state_matches and event["duplicate_sample_returns"] == 0):
        result["reason"] = "sample_source_state_or_parent_not_qualified"
        return result
    if not (child["threshold_capture_ready"] is True and threshold is not None and threshold > 0
            and child["capture_failure_flags"] == 0):
        result["reason"] = "original_comparison_threshold_unavailable"
        return result
    below = sample < threshold
    if child["comparison_at_sample_passed"] is not below:
        result["reason"] = "captured_comparison_disagrees_with_raw_sample_and_threshold"
        return result
    result.update(original_compare_available=True, original_sample_below_threshold=below,
                  copied_original_compare_causal=False, reason="source_comparison_did_not_accept")
    if not below:
        return result
    if event["original_al"] != 1 or event["original_rax_bits"] is None:
        result["copied_original_compare_causal"] = None
        result["reason"] = "independent_original_AL1_unavailable"
        return result
    first_before, first_after = event["first_before"], event["first_after"]
    if (first_before["extended_pointer"] is None or first_before["extended_pointer"] == 0
            or first_after["extended_pointer"] != first_before["extended_pointer"]
            or first_after["pending_3e8_raw"] is None or first_after["pending_3f0_raw"] is None):
        result["copied_original_compare_causal"] = None
        result["reason"] = "independent_stable_extended_write_copies_unavailable"
        return result
    write_matches = (first_after["pending_3e8_raw"] == 1
                     and first_after["pending_3f0_raw"] == event["second_character"])
    result.update(copied_original_compare_causal=write_matches,
                  reason=None if write_matches else "independent_pending_byte_or_target_did_not_match")
    return result


def project_conception_natural_observations_12004(
    journal: dict[str, Any] | None, *, caller_source_resolver: CallerSourceResolver | None = None,
) -> dict[str, Any]:
    """Consume the strict normalized owned journal; never fill another time plane.

    Copied comparison evidence is separate from current natural availability.
    Internal scalar/clamp MOVs are unsampled in this wire, so accepted_causal
    remains unknown. An AL observation is not pregnancy, birth or eligibility.
    """
    result: dict[str, Any] = {
        "source": "native_natural_conception_observation", "schema": "xar.conception-natural-observation-12004.v1",
        "status": "unavailable", "reason": "owned_journal_unavailable", "records": [],
        "monthly_or_stage_role": "unknown", "incoming_caller_literal_call_status": "unknown",
        "current_pair_actual_stack50": None, "historical_reconstruction_available": False,
        "conditional_software_provider_plane": "separate", "pregnancy_or_birth_status": "unknown",
    }
    if journal is None:
        return result
    if journal.get("schema") != JOURNAL_SCHEMA or journal.get("source_pin", "").upper() != SOURCE_PIN:
        raise ValueError("projector requires the exact normalized owned journal")
    result["journal_guards"] = {name: deepcopy(journal[name]) for name in (
        "observer_installed", "current_session_guard", "clock_identity", "oldest_available_sequence",
        "latest_sequence", "overwritten_events", "unattributed_identity_events")}
    current_guard = journal["observer_installed"] is True and journal["current_session_guard"] is True
    result["status"] = "retained_current_session" if current_guard else "unknown_current_observation"
    result["reason"] = None if current_guard else "owned_journal_current_guard_unavailable"
    #53's guard check returns before consulting the resolver for false guards.
    # A supplied resolver is constructed once outside this pure consumer.
    if caller_source_resolver is not None or not current_guard:
        result["incoming_caller_source_binding"] = bind_owned_journal(
            journal, image=ExactImage(journal["build_version"], journal["source_pin"], journal["image_base"]),
            resolver=cast(CallerSourceResolver, caller_source_resolver))
    else:
        result["incoming_caller_source_binding"] = {
            "status": "unavailable", "reason": "held_source_resolver_unavailable",
            "monthly_or_stage_role": "unknown", "records": [],
        }
    for event in journal["events"]:
        parent = _key(event)
        ready = _parent_ready(event, journal, parent)
        comparison = _comparison(event, parent, ready)
        natural = current_guard and event["fixture_origin"] is False
        original_compare = comparison["copied_original_compare_causal"] if natural else None
        original_compare_reason = (comparison["reason"] if natural else
                                   "current_journal_guard_unavailable" if not current_guard else
                                   "fixture_original_provenance")
        row: dict[str, Any] = {
            "journal_sequence": event["journal_sequence"], "original_parent_key": parent,
            "caller_return_pc": event["caller_return_pc"], "caller_return_rva": event["caller_return_rva"],
            "process_id": event["process_id"], "fixture_origin": event["fixture_origin"],
            "original_r9_modifier": event["original_r9_modifier"],
            "original_rax_bits": event["original_rax_bits"], "original_al": event["original_al"],
            "native_parent_accepted": None if not ready or event["original_al"] not in (0, 1) else event["original_al"] == 1,
            "native_parent_return_plane": "copied_original_once",
            "sample_comparison": comparison,
            "provider_first_qword": _provider(event, journal, parent, ready),
            "copied_original_compare_causal": comparison["copied_original_compare_causal"],
            "copied_original_compare_reason": comparison["reason"],
            "original_compare_causal": original_compare, "original_compare_reason": original_compare_reason,
            "accepted_causal": None, "accepted_causal_reason": "required_internal_scalar_and_clamp_consumed_values_unavailable",
            "source_before": deepcopy(event["source_before"]), "source_after": deepcopy(event["source_after"]),
            "parent_sample_state_before_2dword": deepcopy(event["sample_state_before_2dword"]),
            "parent_sample_state_after_2dword": deepcopy(event["sample_state_after_2dword"]),
            "current_natural_observation_available": natural and ready,
            "monthly_or_stage_role": "unknown", "incoming_caller_literal_call_status": "unknown",
        }
        result["records"].append(row)
    return result
