"""Source semantics for typed, owned CK3 1.20.0.4 natural Army phase records.

The unified transport validates exact shapes and scalar types first. This
validator neither fills unavailable samples nor grants prediction readiness.
Session/load epochs remain independent from source invocation and event order.
"""
from __future__ import annotations

_ENTRIES = {"pre_date": 0x2A99DA0, "post_date": 0x2A9A570}
_PREFIX_RETURN = 0x2A99E76
_FULL_C0_SAVE = 0x2A9A65D
_MASK_RETURNS = {0x2A9A672, 0x2A9A67D, 0x2A9A8E2, 0x2A9A8EA}
_ADMITTED_MASK_RETURNS = {0x2A9A672, 0x2A9A8E2}
_EMPTY_EVENT = {"clock_identity": 0, "sequence": 0, "thread_id": None}


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(f"owned Army phase {reason}")


def _same_thread(start: dict, end: dict) -> bool:
    return (
        start["clock_identity"] != 0
        and start["clock_identity"] == end["clock_identity"]
        and start["sequence"] > 0
        and end["sequence"] > 0
        and start["thread_id"] is not None
        and end["thread_id"] is not None
        and start["thread_id"] > 0
        and end["thread_id"] > 0
        and start["thread_id"] == end["thread_id"]
    )


def _later(start: dict, end: dict) -> bool:
    return _same_thread(start, end) and start["sequence"] < end["sequence"]


def _inside(entry: dict, event: dict, returned: dict, label: str) -> None:
    # Literal observations only replace the parent copy after this entry join.
    _require(_later(entry, event), f"{label} lacks its owning entry clock/thread")
    if _same_thread(event, returned):
        _require(event["sequence"] < returned["sequence"],
                 f"{label} does not precede the independent return")


def _roster(scope: dict, returned: dict, full_id: int) -> None:
    roster = scope["original_army_roster"]
    boundary = roster["boundary"]
    ids = roster["ordered_full_ids"]
    # Preserve order, duplicates, zero and all-one raw DWORDs. Membership is
    # exact full-ID equality even when the overall physical copy is partial.
    _require(full_id in ids, "query loses captured full-generation roster membership")
    if boundary == "parent_entry":
        _require(roster["capture_rva"] == scope["actual_entry_rva"],
                 "parent roster source entry differs")
        _require(roster["capture_event"] == scope["entry_event"],
                 "parent roster replaced its entry token")
        _require(scope["prefix_date_raw"] is None,
                 "parent-entry roster acquired a later prefix date")
    elif boundary == "pre_date_prefix_return":
        _require(scope["phase"] == "pre_date" and
                 roster["capture_rva"] == _PREFIX_RETURN,
                 "prefix roster lacks its literal pre-date return")
        _inside(scope["entry_event"], roster["capture_event"], returned, "prefix roster")
    else:
        _require(False, "observed parent roster has no native capture boundary")

    count = roster["count"]
    begin = roster["begin_identity"]
    end = roster["end_identity"]
    if count is not None:
        _require(count >= 0 and len(ids) <= count,
                 "copied roster occurrences exceed the native extent")
    if begin is not None and end is not None and count is not None:
        _require(begin + count * 4 == end and end < (1 << 64),
                 "roster bounds do not describe native DWORD occurrences")
    if roster["complete"]:
        _require(count is not None and count == len(ids) and count <= 65536 and
                 begin is not None and end is not None and (count == 0 or begin != 0),
                 "complete roster lacks its full native extent")
    # Unknown headers and incomplete copies stay partial; no field is backfilled.


def _saved_c0(scope: dict, returned: dict) -> None:
    full = scope["saved_c0_raw"]
    admitted = scope["saved_mask02_admitted"]
    source_rva = scope["saved_c0_observed_rva"]
    event = scope["saved_c0_event"]
    if scope["phase"] == "pre_date" or admitted is None:
        _require(full is None and admitted is None and source_rva == 0 and
                 event == _EMPTY_EVENT,
                 "unobserved saved C0 acquired literal source evidence")
        return
    _require(source_rva == _FULL_C0_SAVE or source_rva in _MASK_RETURNS,
             "saved C0 has no admitted post-date source boundary")
    _inside(scope["entry_event"], event, returned, "saved C0")
    if source_rva == _FULL_C0_SAVE:
        _require(full is not None, "full C0 save supplies only a masked bit")
    if source_rva in _ADMITTED_MASK_RETURNS:
        _require(admitted is True, "conditional cleanup/core call lost its admitted mask")
    if full is not None:
        _require(admitted == bool(full & 2), "saved full C0 and masked bit disagree")
    # Mask-only child observations never reconstruct a full saved C0 byte.
    # Entry/return C0 and date samples intentionally need not equal this save.


def validate_phase_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Validate natural phase source relationships after unified ``_typed``.

    A signed native full CArmy ID and its unsigned wire representation are
    accepted equivalently. There is no current-session or same-date gate, and
    a None sample stays unknown. The caller handles an absent family before
    this function and returns its own unchanged copy after successful validation.
    """
    _require(type(value) is dict, "family is not an owned object")
    _require(type(expected_carmy_id) is int and
             -(1 << 31) <= expected_carmy_id < (1 << 32),
             "expected full CArmy ID is malformed")
    full_id = expected_carmy_id & 0xFFFFFFFF
    _require(value["schema_version"] == 1 and
             value["source"] == "owned_native_natural_army_phase_records" and
             value["membership_basis"] == "captured_parent_roster_full_CArmy_ID_occurrences",
             "family source or membership basis differs")
    _require(value["subject_full_carmy_id_u32"] == full_id,
             "subject full-generation CArmy ID differs")
    _require(len(value["records"]) <= 64, "records exceed the native retained journal")
    for record in value["records"]:
        scope = record["scope"]
        _require(scope["observed"] and record["original_called"] and record["original_returned"],
                 "journal record lacks its actual original entry/return")
        _require(scope["phase"] in _ENTRIES and
                 scope["actual_entry_rva"] == _ENTRIES[scope["phase"]],
                 "native phase entry differs")
        primary = scope["primary_manager_identity"]
        _require(primary > 0 and scope["secondary_manager_identity"] == primary + 8,
                 "primary/secondary manager source pair differs")
        entry = scope["entry_event"]
        returned = record["returned_event"]
        order_observable = (entry["clock_identity"] != 0 and
                            returned["clock_identity"] != 0 and
                            entry["thread_id"] is not None and
                            returned["thread_id"] is not None)
        actual_order = _later(entry, returned) if order_observable else None
        _require(record["same_clock_thread_order"] is actual_order,
                 "shared process-clock/thread order claim differs from copied tokens")
        if scope["game_state_identity"] == 0:
            _require(all(sample is None for sample in (
                scope["date_raw"], scope["absolute_day_raw"], scope["entry_c0_raw"],
                record["returned_date_raw"], record["returned_absolute_day_raw"],
                record["returned_c0_raw"],
            )), "game-state samples acquired an absent source identity")
        _roster(scope, returned, full_id)
        _saved_c0(scope, returned)
        # session_identity is a separate nullable source-proved load epoch.
        # It is never inferred from manager/state pointers, clock or ordinals.
