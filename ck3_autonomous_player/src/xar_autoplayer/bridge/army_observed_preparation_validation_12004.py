"""Actual 35b preparation facts after the owned 59d strict shape check.

This validates copied associations only. It performs no native reads, gate or
political replay, normalization, inferred occurrence selection, or backfill.
"""
from __future__ import annotations

from copy import deepcopy

_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
_CALLSITE = 0x2A9A081
_RETURN = 0x2A9A086
_PREFIX_RETURN = 0x2A99E76
_PRE_DATE = 0x2A99DA0
_BOUND = 4096


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("preparation " + reason)


def _same_ordered(start: dict, end: dict) -> bool:
    return (start["clock_identity"] != 0
            and start["clock_identity"] == end["clock_identity"]
            and 0 < start["sequence"] < end["sequence"]
            and start["thread_id"] is not None
            and start["thread_id"] == end["thread_id"])


def _known_return_order(start: dict, end: dict) -> None:
    # Missing token components stay unknown; every known contradiction is kept.
    if start["clock_identity"] and end["clock_identity"]:
        _require(start["clock_identity"] == end["clock_identity"],
                 "return clock differs from child entry")
    if start["thread_id"] is not None and end["thread_id"] is not None:
        _require(start["thread_id"] == end["thread_id"],
                 "return thread differs from child entry")
    if start["sequence"] and end["sequence"]:
        _require(start["sequence"] < end["sequence"],
                 "return does not follow child entry")


def _identity(value: str | None) -> int | None:
    if value is None:
        return None
    _require(value.startswith("native:") and value[7:].isdigit(),
             "copied pointer identity is malformed")
    pointer = int(value[7:])
    _require(0 <= pointer < (1 << 64) and value == f"native:{pointer}",
             "copied pointer identity is malformed")
    return pointer


def _references(value: dict) -> None:
    rows, count = value["occurrences"], value["count_raw_i32"]
    _require(len(rows) <= _BOUND and value["observed_occurrence_count"] == len(rows),
             "raw vector observed count differs from physical copy")
    _require([row["native_index"] for row in rows] == list(range(len(rows))),
             "raw vector lost physical occurrence order")
    if count is not None:
        _require(not rows or count >= len(rows), "raw vector exceeds copied count")
    for row in rows:
        _require(row["ready"] == (row["raw_full_id_u32"] is not None),
                 "raw reference readiness invents a full ID")
    complete = (count is not None and count >= 0 and count == len(rows)
                and all(row["raw_full_id_u32"] is not None for row in rows))
    _require(value["ready"] == value["references_ready"] == complete,
             "raw vector completeness differs from copied occurrences")
    pointer = _identity(value["data_identity"])
    if pointer is not None and value["data_present"] is not None:
        _require(value["data_present"] == (pointer != 0),
                 "raw vector pointer presence differs")
    if complete and count > 0:
        _require(pointer is not None and pointer != 0 and value["data_present"] is True,
                 "complete nonempty vector lacks its physical data")


def _contains(value: dict, full_id: int) -> bool | None:
    for row in value["occurrences"]:
        raw = row["raw_full_id_u32"]
        if raw is None:
            return None
        if raw == full_id:
            return True
    return False if value["references_ready"] else None


def _signed32(value: int) -> int:
    raw = value & 0xFFFFFFFF
    return raw if raw < (1 << 31) else raw - (1 << 32)


def _full_id_hash(value: int) -> int:
    # Existing pinned copied-input binder: four low-to-high DWORD bytes.
    result = 0x811C9DC5
    for shift in range(0, 32, 8):
        result = ((result ^ ((value >> shift) & 0xFF)) * 0x1000193) & 0xFFFFFFFF
    return result


def _pending(value: dict, selected_full_id: int | None) -> None:
    target = value["target_army_full_id_u32"]
    if target is not None:
        _require(selected_full_id is not None and target == selected_full_id,
                 "pending lookup loses selected full generation")
    if value["hash_raw_u32"] is not None:
        _require(target is not None and value["hash_raw_u32"] == _full_id_hash(target),
                 "pending hash loses the copied full generation")
    probes = value["probes"]
    _require(len(probes) <= 65536
             and [row["native_index"] for row in probes] == list(range(len(probes))),
             "pending probes lost source order")
    home = value["home_slot_i64"]
    if home is not None:
        _require(value["hash_raw_u32"] is not None and value["mask_raw_i32"] is not None
                 and home == (_signed32(value["hash_raw_u32"]) & value["mask_raw_i32"]),
                 "pending home is not its copied hash/mask physical slot")
    for index, row in enumerate(probes):
        _require(home is not None and row["physical_slot_i64"] == home + index
                 and row["distance_raw_u8"] == ((index + 1) & 0xFF),
                 "pending physical probe progression differs")
        control, key = row["control_raw_u8"], row["key_raw_full_id_u32"]
        stops = control is None or control < row["distance_raw_u8"] or key is None or key == target
        if stops:
            _require(index == len(probes) - 1, "pending probes continue after source exit")
    end = value["end_slot_raw_i32"]
    if end is not None:
        _require(value["mask_raw_i32"] is not None and value["tail_distance_raw_u8"] is not None
                 and end == _signed32(value["mask_raw_i32"] + value["tail_distance_raw_u8"] + 1),
                 "pending end slot differs from copied extent")
    slot = value["selected_physical_slot_i64"]
    if value["selected_is_end_marker"] is True:
        _require(slot is not None and end is not None and slot == end,
                 "pending end selection loses its physical slot")
    elif value["selected_is_end_marker"] is False:
        _require(bool(probes) and slot == probes[-1]["physical_slot_i64"]
                 and target is not None and probes[-1]["key_raw_full_id_u32"] == target,
                 "pending key selection loses its actual probe/full ID")
    if value["ready"]:
        _require(slot is not None and value["selected_control_raw_u8"] is not None
                 and value["selected_is_end_marker"] is not None,
                 "ready pending selection lacks physical facts")
    _references(value["suppression_references"])


def _active(value: dict) -> None:
    parent, roster = value["parent"], value["parent"]["original_army_roster"]
    child = value["entry_event"]
    _require(value["observed"] and value["callsite_rva"] == _CALLSITE
             and value["caller_return_rva"] == _RETURN,
             "actual call route differs")
    if value["parent_bound"]:
        _require(parent["observed"] and parent["phase"] == "pre_date"
                 and parent["actual_entry_rva"] == _PRE_DATE
                 and parent["primary_manager_identity"] == value["incoming_primary_manager"]
                 and _same_ordered(parent["entry_event"], child),
                 "parent binding lacks source clock/thread/order")
    if roster["complete"]:
        _require(roster["count"] is not None and roster["count"] >= 0
                 and roster["count"] == len(roster["ordered_full_ids"]),
                 "complete parent roster loses ordered occurrences")
    index = value["native_occurrence_index"]
    if not value["original_occurrence_bound"]:
        _require(index is None and value["local_start_index"] is None
                 and value["requested_army_full_id_u32"] is None,
                 "unbound occurrence invents an index/requested ID")
        return
    _require(value["parent_bound"] and roster["boundary"] == "pre_date_prefix_return"
             and roster["capture_rva"] == _PREFIX_RETURN and roster["complete"]
             and _same_ordered(parent["entry_event"], roster["capture_event"])
             and _same_ordered(roster["capture_event"], child),
             "occurrence does not use the real ordered prefix-return roster")
    begin, end, count = roster["begin_identity"], roster["end_identity"], roster["count"]
    iterator = value["actual_caller_iterator"]
    _require(begin is not None and end is not None and count is not None
             and 0 <= count <= _BOUND and end - begin == count * 4
             and value["actual_caller_end"] == end and begin <= iterator < end
             and (iterator - begin) % 4 == 0,
             "R15/R12 do not bind a physical original-roster occurrence")
    actual_index = (iterator - begin) // 4
    _require(index == actual_index and value["local_start_index"] == actual_index,
             "occurrence index is not derived from the actual iterator")
    raw = roster["ordered_full_ids"][actual_index]
    _require(value["iterator_entry_full_id_u32"] == raw
             and value["requested_army_full_id_u32"] == raw,
             "iterator/requested ID differs from the exact physical roster row")


def _snapshot(value: dict, active: dict) -> None:
    row = value["selected_occurrence"]
    _require(value["source_inputs_ready"] == row["ready"],
             "source readiness is not the selected occurrence readiness")
    _require(row["ready"] == (row["army_append_ready"] and row["arrg_append_ready"]),
             "selected occurrence readiness differs from copied append inputs")
    if row["army_append_ready"]:
        _require(row["army_append"] is not None,
                 "ready Army append lacks its nullable decision")
    if row["arrg_append_ready"]:
        _require(row["arrg_append_full_ids_u32"] is not None,
                 "ready ArRg append lacks its nullable ordered list")
    _references(value["removal_queue"])
    _references(row["original_arrg_references"])
    resolution = row["original_army_resolution"]
    if resolution["selection"] is not None:
        _require(resolution["selection"] == "actual_original_rdx"
                 and resolution["object_identity"] == f'native:{active["incoming_selected_army"]}',
                 "selected operand was re-resolved or replaced")
        _require(all(resolution[field] is None for field in (
            "registry_loaded", "registry_capacity_u32", "registry_index_u32",
            "indexed_identity", "indexed_full_id_u32", "used_fallback")),
            "direct RDX observation invents earlier lookup/fallback facts")
        expected_index = active["native_occurrence_index"]
        _require(row["native_index"] == (-1 if expected_index is None else expected_index)
                 and row["raw_full_id_u32"] == active["requested_army_full_id_u32"]
                 and resolution["requested_full_id_u32"] == active["requested_army_full_id_u32"],
                 "selected occurrence loses its explicit requested association")
        selected = resolution["selected_full_id_u32"]
        _require(resolution["selected_object_ready"] == (active["incoming_selected_army"] != 0)
                 and resolution["selected_full_id_read_ready"] == (selected is not None)
                 and resolution["ready"] == (resolution["selected_object_ready"] and selected is not None),
                 "direct RDX resolution readiness differs")
        for known in (value["selected_army_full_id_raw_u32"], row["selected_army_full_id_raw_u32"]):
            if known is not None and selected is not None:
                _require(known == selected, "copied selected generation differs within a snapshot")
    else:
        _require(not row["ready"] and not resolution["ready"],
                 "missing direct RDX copy promoted to ready")
    state = value["game_state_identity_raw"]
    match = value["game_state_matches_parent"]
    if match is not None:
        _require(state is not None and active["parent"]["game_state_identity"] != 0
                 and match == (state == active["parent"]["game_state_identity"]),
                 "GameState parent comparison backfills an unknown identity")
    selected = row["selected_army_full_id_raw_u32"]
    if row["removal_contains_selected_army"] is not None:
        _require(selected is not None
                 and row["removal_contains_selected_army"] == _contains(value["removal_queue"], selected),
                 "removal membership skips missing or full-generation references")
    _pending(row["pending_selection"], selected)
    originals = row["original_arrg_references"]["occurrences"]
    arrgs = row["arrg_occurrences"]
    _require([(r["native_index"], r["raw_full_id_u32"]) for r in arrgs]
             == [(r["native_index"], r["raw_full_id_u32"]) for r in originals],
             "ArRg evaluation filters or relabels original occurrences")
    for arrg in arrgs:
        membership = arrg["pending_contains"]
        if membership is not None:
            _require(arrg["raw_full_id_u32"] is not None
                     and membership == _contains(row["pending_selection"]["suppression_references"],
                                                  arrg["raw_full_id_u32"])
                     and arrg["append"] == (not membership),
                     "ArRg suppression/append differs from physical references")
        else:
            _require(arrg["append"] is None and not arrg["ready"],
                     "unknown ArRg membership promoted to an append")
    if arrgs and row["arrg_append_ready"]:
        _require(all(r["ready"] and r["append"] is not None for r in arrgs)
                 and row["arrg_append_full_ids_u32"] == [r["raw_full_id_u32"] for r in arrgs if r["append"]],
                 "ArRg append list loses order or duplicate occurrences")
    if row["pending_selection"]["selected_control_raw_u8"] == 0xFF and row["arrg_append_ready"]:
        _require(not arrgs and row["arrg_append_full_ids_u32"] == [],
                 "end-control branch invents an ArRg append")


def _stage(value: dict, before: dict, active: dict) -> None:
    _require(active["original_occurrence_bound"] and before["game_state_matches_parent"] is True,
             "copied conditional stage lacks its entry binding")
    _require(value["source"] == "actual4_daily_assault_preparation_copied_readonly_input_binding",
             "copied conditional source differs")
    _require(not any(value[field] for field in (
        "actual_callback_execution_observed", "full_future_table_placement_ready",
        "full_daily_assault_ready", "full_monthly_execution_ready",
        "current_group_frame_matches", "current_group_records_ready"))
        and value["current_group_records"] is None,
        "copied conditional stage promoted an absent physical/future boundary")
    boundary, roster = value["boundary"], active["parent"]["original_army_roster"]
    child = active["entry_event"]
    _require(boundary["executable_sha256"] == _SHA and boundary["stage"] == "pre_date_assault_call"
             and boundary["callsite_rva"] == _CALLSITE
             and boundary["query_sequence"] == child["sequence"]
             and boundary["frame_identity"] == f'actual-army:{child["clock_identity"]}:{child["sequence"]}'
             and boundary["native_occurrence_index"] == active["native_occurrence_index"]
             and boundary["primary_manager_identity"] == f'native:{active["incoming_primary_manager"]}'
             and boundary["selected_army_identity"] == f'native:{active["incoming_selected_army"]}'
             and boundary["original_roster_capture_identity"] == f'native:{roster["begin_identity"]}',
             "copied conditional boundary loses its exact entry/physical identities")
    for boundary_field, snapshot_field in (
        ("game_date_raw_i32", "game_date_raw_u64"),
        ("absolute_day_raw_i32", "absolute_day_raw_u32"),
        ("calendar_flags_raw_u8", "calendar_flags_raw_u8"),
    ):
        raw = before[snapshot_field]
        expected = None if raw is None else raw if snapshot_field == "calendar_flags_raw_u8" else _signed32(raw)
        _require(boundary[boundary_field] == expected,
                 "conditional boundary backfills or changes a copied scalar")
    _references(value["original_roster"])
    _require(value["removal_queue"] == before["removal_queue"],
             "conditional stage substitutes a later removal queue")
    refs = value["original_roster"]
    _require(refs["references_ready"] and refs["count_raw_i32"] == roster["count"]
             and refs["data_identity"] == boundary["original_roster_capture_identity"]
             and [r["raw_full_id_u32"] for r in refs["occurrences"]] == roster["ordered_full_ids"],
             "conditional stage loses the complete original physical roster")
    if not value["boundary_binding_ready"]:
        _require(not value["occurrence_inputs"] and not value["ordered_append_inputs"]
                 and not value["ordered_append_inputs_ready"],
                 "unbound conditional stage invents evaluated occurrences")
        return
    _require(all(boundary[field] is not None for field in (
        "game_date_raw_i32", "absolute_day_raw_i32", "calendar_flags_raw_u8")),
        "ready conditional boundary defaults missing scalar inputs")
    _require(value["occurrence_inputs"] == [before["selected_occurrence"]]
             and len(value["ordered_append_inputs"]) == 1,
             "conditional stage evaluates another original occurrence")
    row, append = before["selected_occurrence"], value["ordered_append_inputs"][0]
    army_ready = row["army_append_ready"] and row["army_append"] is not None
    selected_siege = row["army_append_siege_full_id_u32"] if row["army_append"] is True else None
    selected_army = row["army_append_full_id_u32"] if row["army_append"] is True else None
    if row["army_append"] is True:
        army_ready = army_ready and selected_siege is not None and selected_army is not None
    arrg_ready = row["arrg_append_ready"] and row["arrg_append_full_ids_u32"] is not None
    _require(append["native_occurrence_index"] == active["native_occurrence_index"]
             and append["requested_army_full_id_u32"] == row["raw_full_id_u32"]
             and append["army_append_input_ready"] == army_ready
             and append["army_append"] == row["army_append"]
             and append["selected_siege_full_id_u32"] == selected_siege
             and append["selected_army_full_id_u32"] == selected_army
             and append["arrg_append_inputs_ready"] == arrg_ready
             and append["ordered_arrg_full_ids_u32"] == row["arrg_append_full_ids_u32"]
             and value["ordered_append_inputs_ready"] == (army_ready and arrg_ready),
             "conditional append changes its one copied occurrence")
    if selected_siege is None:
        _require(append["selected_siege_fnv1a_u32"] is None,
                 "conditional hash backfills a missing Siege key")
    else:
        _require(append["selected_siege_fnv1a_u32"] == _full_id_hash(selected_siege),
                 "conditional hash loses the copied full Siege generation")


def validate_preparation_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Check typed actual preparation facts without changing any copied value."""
    _require(type(value) is dict and type(expected_carmy_id) is int
             and -(1 << 31) <= expected_carmy_id < (1 << 32),
             "query requires an exact full CArmy ID")
    full = expected_carmy_id & 0xFFFFFFFF
    _require(value["schema_version"] == 1
             and value["source"] == "native_natural_army_daily_assault_preparation_entry_return"
             and value["membership_basis"] == "captured_before_selected_CArmy_full_id",
             "owned source/membership basis differs")
    previous = 0
    for event in value["events"]:
        sequence = event["sequence"]
        _require(previous < sequence and value["oldest_available_sequence"] <= sequence <= value["latest_sequence"],
                 "journal sequence is outside its retained ordered range")
        previous = sequence
        active, before, after = event["active"], event["before"], event["after"]
        _require(before["selected_army_full_id_raw_u32"] == full,
                 "query loses the before-entry selected full generation")
        if active["selected_army_full_id_raw_u32"] is not None:
            _require(active["selected_army_full_id_raw_u32"] == full,
                     "active selected generation differs from before-entry query")
        _require(event["original_called"] and event["original_returned"],
                 "entry/return observation lacks its original call/return")
        _active(active)
        _known_return_order(active["entry_event"], event["returned_event"])
        _snapshot(before, active)
        _snapshot(after, active)
        _require(after["copied_stage_input"] is None, "after frame backfills an entry conditional stage")
        same = event["same_selected_army_generation_after"]
        if same is not None:
            _require(after["selected_army_full_id_raw_u32"] is not None
                     and same == (before["selected_army_full_id_raw_u32"] == after["selected_army_full_id_raw_u32"]),
                     "after-generation comparison invents or changes an unknown value")
        if before["copied_stage_input"] is not None:
            _stage(before["copied_stage_input"], before, active)


def validate_cases_preparation_12004(native_value: dict, *, expected_carmy_id: int) -> list[dict]:
    """Return unexecuted variants of Root's newly captured native Append value.

    Every record has name/value/expected_raise. Root59's sole new Python compound
    runs the real strict family normalizer; this export itself runs no validator.
    """
    cases = [{"name": "actual_preparation_owned_copy", "value": deepcopy(native_value), "expected_raise": False}]

    def add(name: str, mutate, bad: bool = True) -> None:
        copy = deepcopy(native_value)
        mutate(copy)
        cases.append({"name": name, "value": copy, "expected_raise": bad})

    add("wrong_preparation_membership_basis", lambda v: v.update(membership_basis="current_query_roster"))
    if not native_value["events"]:
        return cases
    event = native_value["events"][0]
    add("before_full_generation_mismatch", lambda v: v["events"][0]["before"].update(
        selected_army_full_id_raw_u32=(expected_carmy_id & 0xFFFFFFFF) ^ 0x01000000))
    add("wrong_actual_prepare_callsite", lambda v: v["events"][0]["active"].update(callsite_rva=_CALLSITE + 1))
    add("physical_queue_observed_count_mismatch", lambda v: v["events"][0]["before"]["removal_queue"].update(
        observed_occurrence_count=len(v["events"][0]["before"]["removal_queue"]["occurrences"]) + 1))
    add("return_without_original_call", lambda v: v["events"][0].update(original_called=False))
    add("source_readiness_from_original_return", lambda v: v["events"][0]["before"].update(
        source_inputs_ready=not v["events"][0]["before"]["selected_occurrence"]["ready"]))
    add("RDX_argument_substituted", lambda v: v["events"][0]["before"]["selected_occurrence"]["original_army_resolution"].update(
        selection="registry_full_id", used_fallback=False))
    if event["active"]["parent_bound"]:
        add("parent_child_clock_mismatch", lambda v: v["events"][0]["active"]["entry_event"].update(
            clock_identity=v["events"][0]["active"]["parent"]["entry_event"]["clock_identity"] + 1))
        add("bound_parent_missing_thread", lambda v: v["events"][0]["active"]["entry_event"].update(thread_id=None))
    if event["active"]["original_occurrence_bound"]:
        add("wrong_iterator_derived_index", lambda v: v["events"][0]["active"].update(
            native_occurrence_index=v["events"][0]["active"]["native_occurrence_index"] + 1))
        add("wrong_R12_physical_end", lambda v: v["events"][0]["active"].update(
            actual_caller_end=v["events"][0]["active"]["actual_caller_end"] + 4))
        add("unaligned_R15_physical_iterator", lambda v: v["events"][0]["active"].update(
            actual_caller_iterator=v["events"][0]["active"]["actual_caller_iterator"] + 1))
        add("query_roster_replaces_literal_prefix", lambda v: v["events"][0]["active"]["parent"]["original_army_roster"].update(
            boundary="parent_entry"))
        def missing_iterator_read(v):
            e, a = v["events"][0], v["events"][0]["active"]
            a.update(original_occurrence_bound=False, native_occurrence_index=None,
                     local_start_index=None, requested_army_full_id_u32=None,
                     iterator_entry_full_id_u32=None)
            e["capture_failure_flags"] |= 1 << 3
            e["before"]["copied_stage_input"] = None
            for snapshot in (e["before"], e["after"]):
                row = snapshot["selected_occurrence"]
                if row["original_army_resolution"]["selection"] == "actual_original_rdx":
                    row.update(native_index=-1, raw_full_id_u32=None)
                    row["original_army_resolution"]["requested_full_id_u32"] = None
        add("nullable_iterator_read_does_not_infer_index", missing_iterator_read, False)
    if event["before"]["copied_stage_input"] is not None:
        add("after_backfills_before_conditional", lambda v: v["events"][0]["after"].update(
            copied_stage_input=deepcopy(v["events"][0]["before"]["copied_stage_input"])))
        add("conditional_stage_claims_full_daily", lambda v: v["events"][0]["before"]["copied_stage_input"].update(
            full_daily_assault_ready=True))
        def zero_copied_scalars(v):
            before = v["events"][0]["before"]
            before.update(game_date_raw_u64=0, absolute_day_raw_u32=0, calendar_flags_raw_u8=0)
            before["copied_stage_input"]["boundary"].update(
                game_date_raw_i32=0, absolute_day_raw_i32=0, calendar_flags_raw_u8=0)
        add("zero_scalar_reads_are_present", zero_copied_scalars, False)
    if event["after"]["selected_army_full_id_raw_u32"] is not None:
        def missing_after_id(v):
            e = v["events"][0]
            e["after"]["selected_army_full_id_raw_u32"] = None
            e["same_selected_army_generation_after"] = None
        add("nullable_after_generation_stays_unknown", missing_after_id, False)
    return cases
