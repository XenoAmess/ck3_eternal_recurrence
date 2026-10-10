"""Map one owned release record to its exact numerical predecessor.

The captured record remains visible when that predecessor is unavailable.
This module maps facts and conditional inputs; it runs no release arithmetic.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

_EXE_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
_CONSUMER = 0x2A97EB0
_CONSUMER_RETURN = 0x2A9A8EA
_RELEASE_CALL = 0x2A981A9
_RELEASE_RETURN = 0x2A981AE
_POST_STAGE = "after_record_return_before_caller_bookkeeping"
_EXPECTED = {"arrgs": 0x54DEB68, "armies": 0x54E0570}


def _token(value):
    if not isinstance(value, Mapping):
        return None
    clock, sequence, thread = (value.get(key) for key in
                               ("clock_identity", "sequence", "thread_id"))
    if (type(clock) is int and 0 < clock < 1 << 64 and
            type(sequence) is int and 0 < sequence < 1 << 64 and
            type(thread) is int and 0 <= thread < 1 << 32):
        return clock, sequence, thread
    return None


def _ordered(*events):
    tokens = [_token(event) for event in events]
    return (all(token is not None for token in tokens) and
            all(token[0] == tokens[0][0] and token[2] == tokens[0][2]
                for token in tokens) and
            all(left[1] < right[1] for left, right in zip(tokens, tokens[1:])))


def _identity(value):
    return hex(value) if type(value) is int and 0 < value < 1 << 64 else None


def _full_id(value):
    if type(value) is int and -(1 << 31) <= value < 1 << 32:
        return value & 0xFFFFFFFF
    return None


def _vector(raw, role):
    pointer = raw.get("data_address")
    count, capacity = raw.get("count_raw_i32"), raw.get("capacity_raw_i32")
    ids = deepcopy(raw.get("raw_full_ids_u32", []))
    complete = (raw.get("payload_complete") is True and type(count) is int and
                count >= 0 and count == len(ids))
    header_ready = pointer is not None and count is not None and capacity is not None
    header = {"status": "available" if header_ready else "partial",
              "ready": header_ready,
              "unavailable_reason": None if header_ready else "captured_release_header_partial",
              "data_present": None if pointer is None else pointer != 0,
              "data_identity": _identity(pointer), "count_raw_i32": count,
              "capacity_raw_i32": capacity}
    # The owned producer already compared the actual receiver with the exact
    # image singleton. It did not transport an independently readable expected
    # runtime address; keep that address unknown rather than constructing one.
    witness = {"actual_read_ready": raw.get("allocator_address") is not None,
               "actual_identity": _identity(raw.get("allocator_address")),
               "expected_rva_u32": raw.get("expected_allocator_rva_u32"),
               "matches_expected": raw.get("allocator_matches_expected")}
    return {"status": "available" if complete else "partial", "ready": complete,
            "unavailable_reason": None if complete else "captured_release_payload_prefix",
            "references_ready": complete, "count_raw_i32": count,
            "data_present": header["data_present"], "data_identity": header["data_identity"],
            "occurrences": [{"native_index": index, "raw_full_id_u32": value}
                            for index, value in enumerate(ids)],
            "observed_occurrence_count": len(ids), "release_header_v1": header,
            "allocator_witness": witness, "captured_raw_vector": deepcopy(dict(raw)),
            "source_expected_allocator_rva_u32": _EXPECTED[role]}


def _observed(event):
    slot, control = event.get("physical_slot"), event.get("control_before")
    manager = _identity(event.get("primary_manager_address"))
    controls = ([] if slot is None else
                [{"physical_slot_i64": slot, "control_raw_u8": control,
                  "unavailable_reason": None if control is not None else "captured_control_unread"}])
    group = {"native_index": None, "physical_slot_i64": slot,
             "control_raw_u8": control,
             "arrgs": _vector(event["arrgs_before"], "arrgs"),
             "armies": _vector(event["armies_before"], "armies")}
    return {"army_id": None,
            "actual_assault_release_record_12004": deepcopy(dict(event)),
            "actual_assault_release_post_record_12004": {
                "stage": event.get("post_stage"),
                "arrgs": deepcopy(event["arrgs_after"]),
                "armies": deepcopy(event["armies_after"]),
                "control_raw_u8": event.get("control_at_record_return"),
                "occupied_count_raw_i32": event.get("occupied_count_at_record_return")},
            "current_daily_assault_table_v1": {
                "status": "partial", "ready": False,
                "source": "captured_natural_assault_record_entry",
                "manager_identity": manager,
                "header": {"entries_identity": _identity(event.get("entries_address")),
                           "occupied_count_raw_i32": event.get("occupied_count_before"),
                           "mask_raw_i32": None, "tail_distance_raw_u8": None,
                           "load_factor_f32_bits_u32": None,
                           "end_slot_raw_i32": None, "end_marker_control_raw_u8": None},
                "physical_controls": controls, "groups": [group],
                "physical_scan_ready": False, "raw_groups_ready": False}}


def map_actual_assault_release_stage_12004(event, consumer_stage) -> dict:
    """Return copied facts, a qualified conditional stage, and exact gaps.

    ``consumer_stage`` is the 59d wrapper containing native_event, phase_record,
    mapped={army,stage,missing}, and projection from the retained37 leaf. IDs
    are supplied by its complete shared-clock token, never a journal ordinal.
    Missing numerical prefix, captures or predecessor IDs produce no stage.
    """
    if not isinstance(event, Mapping) or not all(
            isinstance(event.get(name), Mapping) for name in
            ("arrgs_before", "armies_before", "arrgs_after", "armies_after")):
        return {"observed": None, "stage": None,
                "missing": ["owned_actual_assault_release_record"]}
    observed = _observed(event)
    if not isinstance(consumer_stage, Mapping):
        return {"observed": observed, "stage": None,
                "missing": ["exact_assault_consumer_stage_wrapper"]}
    missing = []
    native = consumer_stage.get("native_event")
    phase_record = consumer_stage.get("phase_record")
    mapped = consumer_stage.get("mapped")
    native = native if isinstance(native, Mapping) else {}
    parent = native.get("parent")
    parent = parent if isinstance(parent, Mapping) else {}
    phase_record = phase_record if isinstance(phase_record, Mapping) else {}
    phase = phase_record.get("scope")
    phase = phase if isinstance(phase, Mapping) else {}
    mapped = mapped if isinstance(mapped, Mapping) else {}
    army, preceding = mapped.get("army"), mapped.get("stage")
    army = army if isinstance(army, Mapping) else {}
    preceding = preceding if isinstance(preceding, Mapping) else {}
    subject = _full_id(army.get("army_id"))
    observed["army_id"] = army.get("army_id")
    if army.get("actual_assault_consumer_copied_input_12004") != dict(native):
        missing.append("owned_consumer_mapped_input_origin")

    if not (event.get("actual") is True and event.get("original_returned") is True and
            event.get("same_parent_at_return") is True and
            event.get("same_clock_thread_order") is True and
            event.get("exact_post_date_parent") is True and
            event.get("callsite_rva") == _RELEASE_CALL and
            event.get("caller_return_rva") == _RELEASE_RETURN and
            event.get("post_stage") == _POST_STAGE):
        missing.append("exact_natural_record_release_entry_return")
    if not (native.get("actual") is True and native.get("current_session_guard") is True and
            native.get("original_called") is True and native.get("original_returned") is True and
            parent.get("exact_post_date_parent") is True and
            parent.get("actual_entry_rva") == _CONSUMER and
            parent.get("caller_return_rva") == _CONSUMER_RETURN and
            event.get("source_consumer_rva") == _CONSUMER and
            event.get("consumer_caller_return_rva") == _CONSUMER_RETURN):
        missing.append("exact_natural_consumer_source_parent")
    if (_token(event.get("consumer_entry_event")) is None or
            event.get("consumer_entry_event") != parent.get("entry_event") or
            event.get("natural_parent_entry_event") != parent.get("phase_entry_event") or
            phase.get("entry_event") != parent.get("phase_entry_event")):
        missing.append("exact_consumer_and_phase_occurrence_tokens")
    if not (phase.get("observed") is True and phase.get("phase") == "post_date" and
            phase.get("actual_entry_rva") == 0x2A9A570 and
            phase_record.get("original_called") is True and
            phase_record.get("original_returned") is True and
            _ordered(phase.get("entry_event"), parent.get("entry_event"),
                     event.get("entry_event"), event.get("returned_event"),
                     native.get("returned_event"), phase_record.get("returned_event"))):
        missing.append("same_clock_thread_strict_nested_order")
    release_token = _token(event.get("entry_event"))
    if release_token is None or event.get("thread_id") != release_token[2]:
        missing.append("release_native_thread_identity")
    manager = event.get("primary_manager_address")
    if (_identity(manager) is None or manager != parent.get("manager_identity") or
            manager != phase.get("primary_manager_identity")):
        missing.append("same_actual_primary_manager")
    if (event.get("passed_date_raw64") is None or
            event.get("passed_date_raw64") != parent.get("date_raw") or
            event.get("passed_date_raw64") != phase.get("date_raw") or
            event.get("absolute_day_raw") is None or
            event.get("absolute_day_raw") != parent.get("absolute_day_raw") or
            event.get("absolute_day_raw") != phase.get("absolute_day_raw")):
        missing.append("same_actual_parent_date_and_absolute_day")

    raw_table = native.get("entry_table")
    raw_table = raw_table if isinstance(raw_table, Mapping) else {}
    slot = event.get("physical_slot")
    matching = [group for group in raw_table.get("groups", [])
                if isinstance(group, Mapping) and group.get("physical_slot_i64") == slot]
    group = matching[0] if len(matching) == 1 else {}
    entries = event.get("entries_address")
    if (type(slot) is not int or slot < 0 or _identity(entries) is None or
            entries != raw_table.get("entries_identity") or
            event.get("record_plus10_address") != entries + slot * 0x40 + 0x10 or
            len(matching) != 1 or type(group.get("native_index")) is not int):
        missing.append("exact_captured_record_slot_and_consumer_group")
    armies_before = event["armies_before"].get("raw_full_ids_u32", [])
    source_armies = group.get("armies")
    source_armies = source_armies if isinstance(source_armies, Mapping) else {}
    roster = phase.get("original_army_roster")
    roster = roster if isinstance(roster, Mapping) else {}
    if (subject is None or subject not in armies_before or
            subject not in source_armies.get("ordered_full_ids_u32", []) or
            subject not in roster.get("ordered_full_ids", [])):
        missing.append("same_full_generation_CArmy_membership")
    control, occupied = event.get("control_before"), event.get("occupied_count_before")
    if (type(control) is not int or control == 0 or control != group.get("control_raw_u8") or
            control != event.get("control_at_record_return") or
            type(occupied) is not int or occupied <= 0 or
            occupied != raw_table.get("occupied_count_raw_i32") or
            occupied != event.get("occupied_count_at_record_return")):
        missing.append("same_pre_bookkeeping_table_control_and_count_frame")
    for role in ("arrgs", "armies"):
        before = event[role + "_before"]
        entry = group.get(role)
        entry = entry if isinstance(entry, Mapping) else {}
        for child, older in (("data_address", "data_identity"),
                             ("count_raw_i32", "count_raw_i32"),
                             ("capacity_raw_i32", "capacity_raw_i32"),
                             ("allocator_address", "allocator_identity")):
            if before.get(child) is not None and entry.get(older) is not None and before[child] != entry[older]:
                missing.append("same_record_" + role + "_" + child)
        if before.get("expected_allocator_rva_u32") != _EXPECTED[role]:
            missing.append("source_expected_" + role + "_allocator_RVA")
        previous_ids = entry.get("ordered_full_ids_u32", [])
        for index, full_id in enumerate(before.get("raw_full_ids_u32", [])):
            if index < len(previous_ids) and previous_ids[index] is not None and previous_ids[index] != full_id:
                missing.append("same_record_" + role + "_raw_full_ID_prefix")
                break
    lineage_ready = not missing
    if lineage_ready:
        # These are copies from the joined original consumer, not current query
        # families. Other group release witnesses remain unobserved and partial.
        prior_table = army.get("current_daily_assault_table_v1")
        if isinstance(prior_table, Mapping):
            copied_table = deepcopy(dict(prior_table))
            captured_group = deepcopy(observed["current_daily_assault_table_v1"]["groups"][0])
            captured_group["native_index"] = group["native_index"]
            copied_groups = copied_table.get("groups", [])
            copied_table["groups"] = [
                {**row, "arrgs": captured_group["arrgs"], "armies": captured_group["armies"]}
                if row.get("physical_slot_i64") == slot else row for row in copied_groups]
            copied_table["source"] = "same_consumer_entry_frame_with_actual_record_release_headers"
            observed["current_daily_assault_table_v1"] = copied_table
        queue = native.get("entry_pending_queue")
        if isinstance(queue, Mapping):
            ids = queue.get("ordered_full_ids_u32")
            count = queue.get("count_raw_i32")
            complete = (queue.get("references_complete") is True and type(count) is int and
                        count >= 0 and isinstance(ids, list) and count == len(ids) and
                        all(type(value) is int and 0 <= value < 1 << 32 for value in ids))
            observed["native_consumer_entry_pending_queue"] = deepcopy(dict(queue))
            observed["monthly_daily_queue_inputs_v1"] = {
                "manager_army_id_list_2a5a8": [value - (1 << 32) if value & (1 << 31) else value
                                             for value in ids] if complete else None}

    token = _token(parent.get("entry_event"))
    if token is None:
        missing.append("actual_consumer_capture_identity")
    else:
        identity = f"{hex(token[0])}:{token[1]}:{token[2]}"
        if preceding.get("capture_id") != "army_phase_clock:" + identity:
            missing.append("actual_consumer_capture_identity")
        if preceding.get("stage_id") != "actual_assault_consumer_entry_12004:" + identity:
            missing.append("actual_numerical_predecessor_identity")
    if (preceding.get("entry_event") != parent.get("entry_event") or
            preceding.get("phase_entry_event") != parent.get("phase_entry_event")):
        missing.append("exact_supplied_predecessor_occurrence_tokens")
    projection = consumer_stage.get("projection")
    if not isinstance(projection, Mapping):
        missing.append("supplied_numerical_predecessor_projection")
    else:
        if (not preceding.get("stage_id") or projection.get("stage_id") != preceding.get("stage_id") or
                not preceding.get("capture_id") or projection.get("capture_id") != preceding.get("capture_id")):
            missing.append("exact_numerical_predecessor_stage_and_capture")
        if (preceding.get("manager_identity") != _identity(manager) or
                projection.get("manager_identity") != preceding.get("manager_identity")):
            missing.append("exact_numerical_predecessor_manager")
        if (projection.get("source_contract_game_version") != "1.20.0.4" or
                projection.get("source_consumer_rva") != "0x2A97EB0"):
            missing.append("actual4_numerical_source_binding")
        if not preceding.get("basis") or projection.get("input_basis") != preceding.get("basis"):
            missing.append("exact_supplied_numerical_stage_basis")
        if (projection.get("stage_input_ready") is not True or
                not isinstance(projection.get("numerical_prefix"), Mapping)):
            missing.append("numerical_stage_known_prefix")
    if missing:
        return {"observed": observed, "stage": None, "missing": list(dict.fromkeys(missing))}
    clock, sequence, thread = release_token
    stage = {"stage_id": f"actual_assault_record_release_entry_12004:{hex(clock)}:{sequence}:{thread}",
             "capture_id": preceding["capture_id"], "observed_input_capture_id": preceding["capture_id"],
             "manager_identity": preceding["manager_identity"], "prior_stage_id": preceding["stage_id"],
             "basis": "captured_record_entry_headers; exact_same_consumer_numerical_predecessor; conditional_release_only",
             "executable_sha256": _EXE_SHA,
             "table_headers_and_controls_fixed_through_numerical_prefix": True,
             "consumer_entry_event": deepcopy(parent["entry_event"]),
             "natural_parent_entry_event": deepcopy(parent["phase_entry_event"]),
             "record_entry_event": deepcopy(event["entry_event"]),
             "record_returned_event": deepcopy(event["returned_event"]),
             "actual_post_stage": _POST_STAGE, "actual_effects": False}
    return {"observed": observed, "stage": stage, "missing": []}
