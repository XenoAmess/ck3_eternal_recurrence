"""Semantic checks for 43b's typed, owned cleanup boundary copies."""
from __future__ import annotations

_U64 = (1 << 64) - 1
_ENTRY = 0x2A98C90
_RETURN = 0x2A9A672
_PARENT = 0x2A9A570
_REGI = 0x52656769
_SELECTION_FIELDS = (
    "selection", "indexed_regi_full_id", "selected_regi_full_id",
    "selected_magic_14", "selected_regi_identity", "selected_regi_valid",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"cleanup {message}")


def _present(token: dict) -> bool:
    return bool(token["clock_identity"] and token["sequence"]
                and token["thread_id"] is not None and token["thread_id"] != 0)


def _lineage(parent: dict, children: list[dict]) -> bool | None:
    if not all(_present(token) for token in [parent, *children]):
        return None
    last = parent["sequence"]
    same = True
    for token in children:
        same = same and token["clock_identity"] == parent["clock_identity"]
        same = same and token["thread_id"] == parent["thread_id"]
        same = same and token["sequence"] > last
        last = token["sequence"]
    return same


def _slots(frame: dict) -> None:
    slots = frame["physical_slots"]
    extent = frame["copied_physical_extent"]
    _require(extent <= 256 and len(slots) <= extent, "physical extent exceeds source bound")
    _require(not frame["physical_copy_complete"] or len(slots) == extent,
             "complete backing copy lost physical occurrences")
    selections: dict[int, tuple] = {}
    dates: dict[int, int | None] = {}
    for index, slot in enumerate(slots):
        _require(slot["physical_index"] == index, "physical slots were reordered or deduplicated")
        _require(frame["buffer_identity"] is not None, "physical slot has no backing address")
        _require(slot["record_identity"] == (frame["buffer_identity"] + 16 * index) & _U64,
                 "record address differs from the fixed 16-byte backing slot")
        _require(slot["selection"] in {"unavailable", "registry_full_generation", "native_fallback"},
                 "Regi selection source is unknown")
        target = slot["slot0_target_identity"]
        _require((slot["slot0_matches_known_mode0_source"] is None) == (target is None),
                 "callback source classification was filled without its raw target")
        if target is not None:
            _require(slot["vtable_identity"] not in (None, 0), "callback target lacks its raw vtable")
        requested, ordinal = slot["requested_regi_full_id"], slot["ordinal"]
        if requested is None or ordinal is None:
            _require(slot["selection"] == "unavailable"
                     and all(slot[field] is None for field in _SELECTION_FIELDS[1:])
                     and slot["computed_chunk_identity"] is None
                     and slot["date_1c_raw64"] is None,
                     "missing raw Regi pair received selected/current-query fields")
        if slot["selection"] == "registry_full_generation":
            _require(requested is not None and slot["indexed_regi_full_id"] == requested,
                     "Regi registry match loses the full generation")
        if slot["selected_regi_valid"] is True:
            _require(slot["selected_magic_14"] == _REGI
                     and slot["selected_regi_full_id"] not in (None, 0xFFFFFFFF)
                     and slot["selected_regi_identity"] not in (None, 0),
                     "valid Regi lacks the actual magic/full ID/object operands")
        if slot["selected_regi_valid"] is False:
            _require(slot["computed_chunk_identity"] is None and slot["date_1c_raw64"] is None,
                     "invalid Regi received a computed chunk/date")
        if slot["selected_magic_14"] is not None and slot["selected_magic_14"] != _REGI:
            _require(slot["selected_regi_valid"] is False, "invalid Regi magic was promoted")
        if requested is not None and ordinal is not None:
            selection = tuple(slot[field] for field in _SELECTION_FIELDS)
            if requested in selections:
                _require(selections[requested] == selection,
                         "cached Regi selection differs within one raw frame")
            else:
                selections[requested] = selection
        if slot["selected_regi_valid"] is True and ordinal is not None:
            expected = (slot["selected_regi_identity"] + 0x18 + ordinal * 36) & _U64
            _require(slot["computed_chunk_identity"] == expected,
                     "chunk address loses the signed raw ordinal")
        chunk = slot["computed_chunk_identity"]
        if chunk not in (None, 0):
            if chunk in dates:
                _require(dates[chunk] == slot["date_1c_raw64"],
                         "same physical chunk has different cached raw date aliases")
            else:
                dates[chunk] = slot["date_1c_raw64"]
        if slot["complete"]:
            _require(all(slot[field] is not None for field in (
                "vtable_identity", "slot0_target_identity", "requested_regi_full_id", "ordinal")),
                "complete slot lost its raw pair or callback prefix")
            _require(slot["selected_regi_valid"] is not None, "complete slot has an unknown Regi selection")
            if slot["selected_regi_valid"] and chunk != 0:
                _require(chunk is not None and slot["date_1c_raw64"] is not None,
                         "complete valid slot lost its raw chunk date")
            # A false known-source classification is valid for an actual copy.


def _frame(frame: dict, primary: int, before: dict | None) -> None:
    captured = frame["primary_manager_identity"] != 0
    if captured:
        _require(frame["primary_manager_identity"] == primary
                 and frame["header_identity"] == (primary + 0x468) & _U64,
                 "raw frame is bound to a different manager/header")
    else:
        _require(frame["header_identity"] == 0 and frame["passed_date_pointer_identity"] == 0
                 and frame["passed_date_raw64"] is None and frame["buffer_identity"] is None
                 and frame["live_count_raw_i32"] is None and frame["copied_physical_extent"] == 0
                 and not frame["header_complete"] and not frame["physical_copy_complete"]
                 and not frame["complete"] and not frame["truncated"]
                 and frame["original_backing_address_preserved"] is None
                 and not frame["physical_slots"],
                 "uncaptured frame was promoted or backfilled")
    _require(frame["header_complete"] == (
        frame["buffer_identity"] is not None and frame["live_count_raw_i32"] is not None),
        "header completeness differs from raw operands")
    _slots(frame)
    count = frame["live_count_raw_i32"]
    extent = count
    if frame["header_complete"] and count >= 0:
        if before is not None and before["buffer_identity"] is not None:
            same = frame["buffer_identity"] == before["buffer_identity"]
            _require(frame["original_backing_address_preserved"] is same,
                     "returned backing continuity does not match the two raw addresses")
            if same and before["physical_copy_complete"]:
                extent = max(count, before["copied_physical_extent"])
        else:
            _require(frame["original_backing_address_preserved"] is None,
                     "backing continuity was invented without an entry address")
        if extent > 256:
            _require(frame["truncated"] and not frame["complete"]
                     and frame["copied_physical_extent"] == 0 and not frame["physical_slots"],
                     "oversized backing was materialized as a ready or fake empty frame")
        elif extent and frame["buffer_identity"] == 0:
            _require(not frame["complete"] and not frame["physical_slots"],
                     "nonempty null backing was materialized")
        elif frame["physical_copy_complete"]:
            _require(frame["copied_physical_extent"] == extent,
                     "fixed backing extent was replaced by the current live count")
    if frame["truncated"]:
        _require(not frame["complete"] and not frame["physical_copy_complete"],
                 "truncated raw frame was marked complete")
    if frame["complete"]:
        _require(frame["header_complete"] and frame["physical_copy_complete"]
                 and frame["passed_date_raw64"] is not None
                 and all(slot["complete"] for slot in frame["physical_slots"]),
                 "complete frame contains unavailable boundary operands")


def validate_cleanup_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Validate semantics after 59d's exact Cleanup _typed shape check.

    No field is filled or reordered. Nullable clocks/session/dates and partial
    reads remain source facts; pending Regi IDs never establish Army membership.
    """
    _require(type(expected_carmy_id) is int and -(1 << 31) <= expected_carmy_id < (1 << 32),
             "expected full CArmy ID is malformed")
    full = expected_carmy_id & 0xFFFFFFFF
    _require(value["membership_basis"] == "parent_entry_roster_membership",
             "membership basis does not describe the earlier Army frame")
    journal = value["journal"]
    _require(journal["source"] == "native_natural_monthfirst_cleanup_entry_return"
             and journal["snapshot_basis"] == "actual_readonly_boundary_copies"
             and journal["actual_entry_rva"] == _ENTRY
             and journal["literal_caller_return_rva"] == _RETURN
             and not journal["conditional_predictor_executed"], "actual source/boundary claim differs")
    _require(journal["status"] in {"available", "partial"}, "journal status is unknown")
    _require(journal["dropped_record_copies"] == 0 or journal["status"] == "partial",
             "dropped owned records were promoted as available")
    events = journal["events"]
    _require(journal["event_count"] == len(events) and len(events) <= 32,
             "owned journal event count differs")
    last = 0
    for event in events:
        ordinal = event["journal_ordinal"]
        _require(last < ordinal <= journal["latest_ordinal"]
                 and ordinal >= journal["oldest_available_ordinal"],
                 "filtered journal order/range differs")
        last = ordinal
        _require(event["actual_entry_rva"] == _ENTRY and event["caller_return_rva"] == _RETURN
                 and event["source_call_admitted"]
                 and event["saved_mask02_admitted_by_literal_call"] is True,
                 "literal arrival/saved mask02 source fact differs")
        phase = event["phase"]
        primary = phase["primary_manager_identity"]
        _require(phase["observed"] and phase["phase"] == "post_date"
                 and phase["actual_entry_rva"] == _PARENT and primary != 0
                 and phase["secondary_manager_identity"] == (primary + 8) & _U64,
                 "post-date parent manager relation differs")
        roster = phase["original_army_roster"]
        ids = roster["ordered_full_ids"]
        _require(roster["boundary"] == "parent_entry" and roster["capture_rva"] == _PARENT
                 and roster["complete"] and roster["count"] == len(ids)
                 and roster["copied_occurrence_count"] == len(ids)
                 and full in ids, "full-generation CArmy parent roster join is absent")
        _require(roster["capture_event"] == phase["entry_event"], "roster capture token differs from parent entry")
        begin, end = roster["begin_identity"], roster["end_identity"]
        _require(begin is not None and end == begin + 4 * len(ids)
                 and (not ids or begin != 0), "parent50/5C roster extent differs")
        # Reaching the CALL proves mask2, without filling savedC0/entryC0.
        _require(phase["saved_mask02_admitted"] is not False, "known parent saved mask contradicts arrival")
        if phase["saved_c0_raw"] is not None:
            _require(bool(phase["saved_c0_raw"] & 2), "known savedC0 contradicts literal mask2 arrival")
        before, after = event["before"], event["after"]
        _frame(before, primary, None)
        _frame(after, primary, before)
        for frame in (before, after):
            if frame["primary_manager_identity"] and phase["game_state_identity"]:
                _require(frame["passed_date_pointer_identity"] == (phase["game_state_identity"] + 8) & _U64,
                         "passed CDate pointer differs from the literal GameState+8 operand")
        if before["primary_manager_identity"] and after["primary_manager_identity"]:
            _require(before["passed_date_pointer_identity"] == after["passed_date_pointer_identity"],
                     "return date argument was replaced by a current query")
        dates_known = phase["date_raw"] is not None and before["passed_date_raw64"] is not None
        expected_date_match = phase["date_raw"] == before["passed_date_raw64"] if dates_known else None
        _require(event["phase_date_matches_passed_date"] is expected_date_match,
                 "date match fact was changed or backfilled")
        if event["original_returned"]:
            _require(event["original_called"] and event["raw_return_bits"] is not None,
                     "returned original lost its opaque raw RAX")
        else:
            _require(event["raw_return_bits"] is None, "unreturned original acquired raw RAX")
        children = [event[name] for name in (
            "before_event", "before_copied_event", "returned_event", "after_copied_event")]
        _require(event["same_clock_thread_order"] is _lineage(phase["entry_event"], children),
                 "nullable shared-clock lineage was changed")
