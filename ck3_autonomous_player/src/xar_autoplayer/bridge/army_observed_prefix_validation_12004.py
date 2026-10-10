"""Check the actual 1.20.0.4 prefix DTO after the shared strict shape check.

This validates retained observations only. Nullable reads remain nullable, queue
occurrences retain their order and duplicates, and a positive D4 does not prove
that the physical transition has been captured.
"""

_U64_MAX = (1 << 64) - 1
_RETURN_RVA = 0x2A99E76
_PRE_DATE_RVA = 0x2A99DA0
_JOURNAL_CAPACITY = 64
_MEMBERSHIP = "complete_literal_prefix_return_roster_full_ID"


def _fail(name: str, reason: str) -> None:
    raise ValueError(f"{name}: {reason}")


def _integer(value, bits: int, name: str, *, signed=False, nullable=False):
    if value is None and nullable:
        return None
    lower = -(1 << (bits - 1)) if signed else 0
    upper = (1 << (bits - (1 if signed else 0))) - 1
    if type(value) is not int or not lower <= value <= upper:
        _fail(name, f"raw {'i' if signed else 'u'}{bits} width differs")
    return value


def _boolean(value, name: str, *, nullable=False):
    if value is None and nullable:
        return None
    if type(value) is not bool:
        _fail(name, "boolean or observation availability differs")
    return value


def _ids(values, name: str) -> None:
    if type(values) is not list or len(values) > 65536:
        _fail(name, "ordered occurrence extent differs")
    for value in values:
        _integer(value, 32, name)


def _token(value: dict, name: str) -> bool:
    _integer(value["clock_identity"], 64, name)
    _integer(value["sequence"], 64, name)
    _integer(value["thread_id"], 32, name, nullable=True)
    return (value["clock_identity"] != 0 and value["sequence"] != 0
            and value["thread_id"] is not None)


def _ordered(start: dict, end: dict, name: str, *, required=False) -> None:
    start_available = _token(start, name)
    end_available = _token(end, name)
    available = start_available and end_available
    if not available:
        if required:
            _fail(name, "claimed binding has no complete clock/thread tokens")
        return
    if (start["clock_identity"] != end["clock_identity"]
            or start["thread_id"] != end["thread_id"]
            or start["sequence"] >= end["sequence"]):
        _fail(name, "observed clock/thread causal order differs")


def _queue(value: dict, name: str) -> None:
    data = _integer(value["data_identity"], 64, name, nullable=True)
    end = _integer(value["end_identity"], 64, name, nullable=True)
    capacity = _integer(value["capacity_raw_i32"], 32, name, signed=True, nullable=True)
    count = _integer(value["count_raw_i32"], 32, name, signed=True, nullable=True)
    bounds = _boolean(value["bounds_valid"], name, nullable=True)
    admitted = _boolean(value["copy_bound_admitted"], name, nullable=True)
    copied = _boolean(value["copied_complete"], name)
    ids = value["ordered_full_ids"]
    _ids(ids, name)

    # C8/D0/D4 and 158/160/164 are independent raw reads. A missing
    # header field cannot be replaced by its counterpart in another snapshot.
    if data is None or capacity is None or count is None:
        if bounds is not None or admitted is not None or end is not None or copied or ids:
            _fail(name, "partial header promoted to a copied extent")
        return
    valid = (count >= 0 and capacity >= 0 and count <= capacity
             and data <= _U64_MAX - max(count, 0) * 4
             and (count == 0 or data != 0))
    if bounds is not valid:
        _fail(name, "bounds claim differs from this snapshot's raw header")
    if not valid:
        if admitted is not None or end is not None or copied or ids:
            _fail(name, "invalid raw bounds promoted to a copied extent")
        return
    if admitted is None:
        _fail(name, "valid raw bounds lack the observer copy-bound decision")
    if not admitted:
        if end is not None or copied or ids:
            _fail(name, "unadmitted copy has a payload or derived end")
        return
    if end != data + count * 4:
        _fail(name, "end does not preserve the raw uint32 occurrence extent")
    if copied:
        if len(ids) != count:
            _fail(name, "complete copy loses raw occurrences")
    elif ids or count == 0:
        _fail(name, "failed copy differs from the observer's empty payload")


def _snapshot(value: dict, name: str) -> None:
    _queue(value["source_c8"], name + ".source_c8")
    _queue(value["destination_158"], name + ".destination_158")
    for field, bits in (("supplied_date_raw_u64", 64), ("game_date_raw_u64", 64),
                        ("absolute_day_raw_u32", 32), ("calendar_c0_raw_u8", 8)):
        _integer(value[field], bits, name + "." + field, nullable=True)
    no_work = _boolean(value["conditional_no_work_arm"], name, nullable=True)
    count = value["source_c8"]["count_raw_i32"]
    expected = None if count is None else count <= 0
    if no_work is not expected:
        _fail(name, "no-work arm differs from this snapshot's signed D4")
    if _boolean(value["positive_physical_transition_complete"], name):
        _fail(name, "positive physical transition has no captured completion proof")


def _event(value: dict, full_id: int, name: str) -> None:
    for field in ("primary_manager_identity", "date_argument_identity",
                  "caller_return_rva", "incoming_rax_raw_u64", "original_rax_raw_u64"):
        _integer(value[field], 64, name + "." + field)
    _integer(value["capture_failure_flags"], 32, name)
    if value["caller_return_rva"] != _RETURN_RVA:
        _fail(name, "literal original callback return differs")
    if (not _boolean(value["original_called"], name)
            or not _boolean(value["original_returned"], name)):
        _fail(name, "published return packet has no naturally returned original")

    parent = value["parent"]
    for field in ("actual_entry_rva", "caller_return_rva", "primary_manager_identity",
                  "secondary_manager_identity", "game_state_identity"):
        _integer(parent[field], 64, name + ".parent." + field)
    _integer(parent["phase_raw"], 32, name)
    _integer(parent["date_raw_u64"], 64, name, nullable=True)
    _integer(parent["absolute_day_raw_u32"], 32, name, nullable=True)
    observed = _boolean(parent["observed"], name)
    bound = _boolean(value["parent_bound"], name)
    if parent["phase_raw"] not in (0, 1, 2):
        _fail(name, "raw parent phase differs from the observed enum")
    if observed:
        source_entry = {1: _PRE_DATE_RVA, 2: 0x2A9A570}.get(parent["phase_raw"])
        if (parent["actual_entry_rva"] != source_entry
                or parent["primary_manager_identity"] > _U64_MAX - 8
                or parent["secondary_manager_identity"] != parent["primary_manager_identity"] + 8):
            _fail(name, "observed parent entry or manager adjustment differs")
    _token(value["parent_entry_event"], name)
    _token(value["entry_event"], name)
    _token(value["returned_event"], name)
    if bound:
        if (not observed or parent["phase_raw"] != 1
                or parent["actual_entry_rva"] != _PRE_DATE_RVA
                or parent["primary_manager_identity"] != value["primary_manager_identity"]):
            _fail(name, "claimed pre-date parent differs from the actual scope")
        _ordered(value["parent_entry_event"], value["entry_event"], name, required=True)

    _snapshot(value["before"], name + ".before")
    _snapshot(value["after"], name + ".after")
    # A copied D4 does not record the count consumed by native MOVSXD.
    # Actual returned RAX and incoming RAX remain independent raw facts.

    roster = value["captured_original_roster"]
    count = _integer(roster["count_raw_i32"], 32, name, signed=True, nullable=True)
    begin = _integer(roster["begin_identity"], 64, name, nullable=True)
    end = _integer(roster["end_identity"], 64, name, nullable=True)
    _integer(roster["boundary_raw"], 32, name)
    _integer(roster["capture_rva"], 64, name)
    _ids(roster["ordered_full_ids"], name)
    if (not _boolean(value["original_roster_capture_complete"], name)
            or not _boolean(roster["complete"], name)
            or roster["boundary_raw"] != 2 or roster["capture_rva"] != _RETURN_RVA):
        _fail(name, "query membership lacks the complete literal return roster")
    if (count is None or count < 0 or count != len(roster["ordered_full_ids"])
            or begin is None or end is None or (count != 0 and begin == 0)
            or begin > _U64_MAX - count * 4 or end != begin + count * 4):
        _fail(name, "complete original roster loses its raw occurrence extent")
    if full_id not in roster["ordered_full_ids"]:
        _fail(name, "query loses full-generation CArmy membership")
    if not _token(roster["capture_event"], name):
        _fail(name, "literal roster lacks its source clock/thread token")
    _ordered(value["entry_event"], roster["capture_event"], name)
    _ordered(roster["capture_event"], value["returned_event"], name)


def validate_prefix_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Validate a strict-typed query family without modifying its raw packet.

    The unified family normalizer owns exact DTO keys/types. These checks add
    source semantics. Unknown parent or individual reads are preserved; current
    load/session qualification is independent of historical roster membership.
    """
    if type(value) is not dict or type(expected_carmy_id) is not int:
        _fail("prefix", "family or exact CArmy ID type differs")
    if not -(1 << 31) <= expected_carmy_id <= (1 << 32) - 1:
        _fail("prefix", "exact CArmy ID raw width differs")
    full_id = expected_carmy_id & 0xFFFFFFFF
    try:
        if value["membership_basis"] != _MEMBERSHIP or type(value["journals"]) is not list:
            _fail("prefix", "literal return roster membership basis differs")
        for index, journal in enumerate(value["journals"]):
            name = f"prefix.journals[{index}]"
            _boolean(journal["observer_installed"], name)
            _boolean(journal["current_session_guard"], name)
            oldest = _integer(journal["oldest_available_sequence"], 64, name)
            latest = _integer(journal["latest_sequence"], 64, name)
            overwritten = _integer(journal["overwritten_events"], 64, name)
            _integer(journal["unattributed_capture_failures"], 64, name)
            if (oldest != (max(1, latest - _JOURNAL_CAPACITY + 1) if latest else 0)
                    or overwritten != max(latest - _JOURNAL_CAPACITY, 0)):
                _fail(name, "retained 64-slot journal extent differs")
            events = journal["events"]
            if type(events) is not list or len(events) > _JOURNAL_CAPACITY:
                _fail(name, "retained event bound differs")
            previous = 0
            manager = None
            for event_index, event in enumerate(events):
                event_name = f"{name}.events[{event_index}]"
                sequence = _integer(event["sequence"], 64, event_name)
                if not sequence or not oldest <= sequence <= latest or sequence <= previous:
                    _fail(event_name, "filtered journal loses retained sequence order")
                previous = sequence
                _event(event, full_id, event_name)
                if manager is not None and manager != event["primary_manager_identity"]:
                    _fail(event_name, "journal mixes independently selected managers")
                manager = event["primary_manager_identity"]
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("prefix: strict DTO shape required before semantic validation") from error
