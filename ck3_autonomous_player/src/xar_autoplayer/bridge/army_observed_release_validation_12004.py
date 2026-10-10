"""Validate copied natural record-release facts after the unified typed check.

This validator reads no native state and changes no payload.  Vector payload
completeness is independent of header completeness and the record return is
before caller bookkeeping.  No later query can fill a missing observation.
"""
from __future__ import annotations


_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
_POST_STAGE = "after_record_return_before_caller_bookkeeping"
_PAYLOAD_LIMIT = 64
_JOURNAL_CAPACITY = 256


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("Army release " + message)


def _valid_token(token: dict, thread: int) -> bool:
    return (token["clock_identity"] != 0 and token["sequence"] != 0
            and token["thread_id"] == thread)


def _vector(vector: dict, *, allocator_rva: int, before: bool) -> tuple[bool, bool, bool]:
    """Return independent header failure, payload failure and truncation facts."""
    _require(vector["expected_allocator_rva_u32"] == allocator_rva,
             "vector receiver source differs")
    data = vector["data_address"]
    count = vector["count_raw_i32"]
    allocator = vector["allocator_address"]
    match = vector["allocator_matches_expected"]
    _require((match is None) == (allocator is None),
             "allocator observation is backfilled or lost")
    # This is the producer's selected source, not a claim about allocator safety.
    if before and data is not None and data != 0:
        _require(match is True, "nonnull entry receiver lacks canonical source")

    payload = vector["raw_full_ids_u32"]
    size = vector["payload_count"]
    _require(size == len(payload) and 0 <= size <= _PAYLOAD_LIMIT,
             "copied raw DWORD payload extent differs")
    complete = vector["payload_complete"]
    header_failed = any(vector[key] is None for key in (
        "data_address", "count_raw_i32", "capacity_raw_i32", "allocator_address"))
    if data is None or count is None:
        _require(size == 0 and complete is False,
                 "unread data/count invents a payload")
        return header_failed, False, False
    if count <= 0:
        # The capture source does not compare capacity or normalize a negative count.
        _require(size == 0 and complete is True,
                 "nonpositive raw count loses complete empty payload")
        return header_failed, False, False
    if data == 0:
        _require(size == 0 and complete is False,
                 "null positive-count payload is invented")
        return header_failed, True, False

    _require(size <= min(count, _PAYLOAD_LIMIT), "payload exceeds observed count")
    _require(complete == (size == count), "payload complete flag contradicts raw count")
    return header_failed, size < min(count, _PAYLOAD_LIMIT), count > _PAYLOAD_LIMIT


def _event(event: dict, *, value: dict, full_id: int) -> None:
    _require((event["callsite_rva"], event["caller_return_rva"])
             == (0x2A981A9, 0x2A981AE), "literal release caller differs")
    _require(event["source_consumer_rva"] == 0x2A97EB0
             and event["consumer_caller_return_rva"] == 0x2A9A8EA
             and event["exact_post_date_parent"] is True
             and event["primary_manager_address"] != 0,
             "natural consumer parent differs")
    _require(event["post_stage"] == _POST_STAGE,
             "record return is promoted to caller cleanup")
    _require(event["original_returned"] is True, "published record lacks original return")
    _require(event["actual"] == (value["observer_installed"]
                                  and value["current_session_guard"]),
             "installed/session source credit differs")

    entries, slot = event["entries_address"], event["physical_slot"]
    _require(entries is not None and entries != 0 and slot is not None,
             "captured physical record identity is missing")
    expected_address = entries + slot * 0x40 + 0x10
    _require(expected_address < (1 << 64)
             and event["record_plus10_address"] == expected_address,
             "record+10 differs from captured physical slot")
    _require(event["control_before"] is not None and event["control_before"] != 0
             and event["occupied_count_before"] is not None
             and event["occupied_count_before"] > 0,
             "entry record lacks observed occupied control")
    # Occupied count is not a physical vector extent. Post control/count remain
    # independent readings; they are not computed from expected native effects.

    thread = event["thread_id"]
    natural = event["natural_parent_entry_event"]
    consumer = event["consumer_entry_event"]
    _require(thread != 0 and _valid_token(natural, thread)
             and _valid_token(consumer, thread)
             and natural["clock_identity"] == consumer["clock_identity"]
             and natural["sequence"] < consumer["sequence"],
             "parent clock/thread stage identity differs")
    entry, returned = event["entry_event"], event["returned_event"]
    ordered = (_valid_token(entry, thread) and _valid_token(returned, thread)
               and entry["clock_identity"] == consumer["clock_identity"]
               and returned["clock_identity"] == entry["clock_identity"]
               and consumer["sequence"] < entry["sequence"] < returned["sequence"])
    claimed_order = event["same_clock_thread_order"]
    # Observe assigns the predicate on every published record. Optional DTO
    # storage does not add an unavailable published-record source branch.
    _require(type(claimed_order) is bool and claimed_order == ordered,
             "published child clock order proof contradicts source/tokens")

    flags = event["capture_failure_flags"]
    _require(flags & ~0xFF == 0, "capture failure bits are not source-defined")
    _require(bool(flags & 0x20) == (event["same_parent_at_return"] is not True),
             "return parent partial flag differs")
    _require(bool(flags & 0x80) == (claimed_order is not True),
             "child clock partial flag differs")
    missing_slot_return = (event["control_at_record_return"] is None
                           or event["occupied_count_at_record_return"] is None)
    _require(bool(flags & 0x40) == missing_slot_return,
             "return slot read is backfilled or loses its failure")

    _require(full_id in event["armies_before"]["raw_full_ids_u32"],
             "query full generation lacks captured pre-release membership")
    failures = {}
    for field, allocator in (("arrgs_before", 0x54DEB68), ("armies_before", 0x54E0570),
                             ("arrgs_after", 0x54DEB68), ("armies_after", 0x54E0570)):
        failures[field] = _vector(event[field], allocator_rva=allocator,
                                  before=field.endswith("before"))
    for suffix, header_bit, payload_bit in (("before", 1, 4), ("after", 2, 8)):
        snapshots = [failures[f"{kind}_{suffix}"] for kind in ("arrgs", "armies")]
        _require(bool(flags & header_bit) == any(row[0] for row in snapshots),
                 suffix + " header partial flag differs")
        _require(bool(flags & payload_bit) == any(row[1] for row in snapshots),
                 suffix + " payload partial flag differs")
    _require(bool(flags & 0x10) == any(row[2] for row in failures.values()),
             "bounded payload truncation flag differs")


def validate_release_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Validate an already typed Release family without projection or mutation."""
    _require(type(expected_carmy_id) is int and 0 <= expected_carmy_id <= 0xFFFFFFFF,
             "expected full CArmy ID is not a raw DWORD")
    _require(type(value) is dict, "family is not the typed owned object")
    try:
        _require(value["schema_version"] == 1
                 and value["source_contract_game_version"] == "1.20.0.4"
                 and value["source_executable_sha256"] == _SHA
                 and value["source_release_rva"] == 0x9D11F0
                 and value["source"] == "native_natural_assault_record_entry_return"
                 and value["membership_basis"] == "raw_group_armies_at_release_entry",
                 "source/build contract differs")
        _require(value["observer_installed"] == value["current_session_guard"],
                 "copied installation/session guards differ")
        events = value["events"]
        _require(value["event_count"] == len(events), "copied event count differs")
        latest, oldest = value["latest_sequence"], value["oldest_available_sequence"]
        expected_oldest = max(1, latest - _JOURNAL_CAPACITY + 1) if latest else 0
        _require(oldest == expected_oldest
                 and value["overwritten_events"] == max(0, latest - _JOURNAL_CAPACITY),
                 "journal retained-window metadata differs")
        previous = 0
        for event in events:
            sequence = event["sequence"]
            _require(oldest <= sequence <= latest and previous < sequence,
                     "filtered event order/window differs")
            previous = sequence
            _event(event, value=value, full_id=expected_carmy_id)
    except (KeyError, TypeError) as error:
        raise ValueError("Army release typed owned fields are missing or malformed") from error
