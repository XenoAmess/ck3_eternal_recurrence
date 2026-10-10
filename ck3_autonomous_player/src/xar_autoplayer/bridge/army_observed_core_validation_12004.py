"""Source-bound regular-core semantics after the unified transport type check.

The actual producer is the natural 2A98AC0 original-once seam at return
2A9A8E2. Entry and return are independent guarded copies. Object maps use
physical identities; occurrence arrays retain order, duplicates and full IDs.
No later query value supplies a historical field.
"""
from __future__ import annotations

from .army_scoped_ordered_refill_contract import (
    _RAW, _CONTEXT, _MAGIC, _BOOL, _int, _reason,
)


def _require(condition: bool, path: str, detail: str) -> None:
    if not condition:
        raise ValueError(f"{path}: {detail}")


def _ordered(first: dict, second: dict) -> bool:
    return (first["clock_identity"] != 0
            and first["clock_identity"] == second["clock_identity"]
            and first["thread_id"] is not None
            and first["thread_id"] == second["thread_id"]
            and 0 < first["sequence"] < second["sequence"])


def _occurrences(rows: list, count: int | None, complete: bool, path: str) -> None:
    _require([row["stored_index"] for row in rows] == list(range(len(rows))),
             path, "native occurrence positions must remain dense and ordered")
    _require(len(rows) <= max(0, count or 0), path, "copied occurrences exceed native extent")
    if complete:
        _require(count is not None and count >= 0 and len(rows) == count,
                 path, "complete capture lacks the full native occurrence extent")
    for row in rows:
        if row["used_fallback"] is False:
            _require(row["raw_full_id"] is not None
                     and row["resolved_full_id"] == row["raw_full_id"]
                     and row["physical_token"] != 0,
                     path, "nonfallback resolution loses the complete generation")


def _physical(value: dict, identity: int | None, path: str) -> None:
    _require(type(value) is dict and set(value) == {
        "persistent_regiment_id", "prepared_fraction_raw", "unavailable_reason", "chunks"},
        path, "physical persistent copy shape differs from the literal serializer")
    _int(value["persistent_regiment_id"], nullable=False)
    _int(value["prepared_fraction_raw"], 64)
    _reason(value["unavailable_reason"])
    _require(value["persistent_regiment_id"] == (-1 if identity is None else identity),
             path, "physical copy belongs to another resolved generation")
    _require(type(value["chunks"]) is list and len(value["chunks"]) <= 7,
             path, "physical copy exceeds the seven native slots")
    fields = set(_RAW + _CONTEXT + _MAGIC + _BOOL) | {"context_unavailable_reason"}
    for index, chunk in enumerate(value["chunks"]):
        _require(type(chunk) is dict and set(chunk) == fields,
                 path, "physical chunk shape differs from the literal serializer")
        for field in _RAW:
            _int(chunk[field], nullable=False)
        for field in _CONTEXT:
            _int(chunk[field])
        for field in _MAGIC:
            _int(chunk[field], unsigned=True)
        for field in _BOOL:
            _require(chunk[field] is None or type(chunk[field]) is bool,
                     path, "native predicate must retain bool or null")
        _reason(chunk["context_unavailable_reason"])
        _require(chunk["physical_index"] == index, path, "physical slot order changed")
        for field in ("exclusion_byte_14_raw", "army_byte_1d4_raw", "army_byte_1ec_raw"):
            _require(chunk[field] is None or 0 <= chunk[field] <= 255,
                     path, "copied native byte is outside its physical width")


def _object_map(rows: list, path: str) -> dict:
    keys = [row["physical_token"] for row in rows]
    _require(all(keys) and len(set(keys)) == len(keys),
             path, "physical object keys must be nonzero and unique")
    return dict(zip(keys, rows))


def _frame(frame: dict, path: str) -> None:
    complete = frame["capture_complete"]
    _occurrences(frame["persistent_occurrences"], frame["native_persistent_occurrence_count"],
                 complete, path + ".persistent_occurrences")
    _occurrences(frame["army_refresh_occurrences"], frame["native_army_refresh_occurrence_count"],
                 complete, path + ".army_refresh_occurrences")
    persistents = _object_map(frame["persistent_objects"], path + ".persistent_objects")
    armies = _object_map(frame["army_objects"], path + ".army_objects")
    direct_tokens = {row["physical_token"] for row in frame["persistent_occurrences"]}
    if complete:
        _require(not frame["missing_inputs"], path, "complete capture retains missing inputs")
    for token, persistent in persistents.items():
        physical = persistent["physical_values"]
        _physical(physical, persistent["resolved_full_id"], path + ".physical_values")
        _require(physical["unavailable_reason"] == (persistent["unavailable_reason"] or None),
                 path, "physical and owning persistent copy reasons differ")
        if complete:
            _require(persistent["resolved_full_id"] is not None
                     and not persistent["unavailable_reason"] and len(physical["chunks"]) == 7,
                     path, "complete capture lacks an independently copied physical seven")
            if token in direct_tokens:
                _require(physical["prepared_fraction_raw"] is not None,
                         path, "direct manager receiver lacks its observed prepared148")
    # DATA-only physical receivers do not require prepared148. Their operands
    # remain independent of the direct manager prepared-fraction source.
    for rows, objects, label in (
        (frame["persistent_occurrences"], persistents, "persistent"),
        (frame["army_refresh_occurrences"], armies, "army"),
    ):
        for row in rows:
            if complete:
                obj = objects.get(row["physical_token"])
                _require(row["raw_full_id"] is not None and row["resolved_full_id"] is not None
                         and row["used_fallback"] is not None and not row["unavailable_reason"]
                         and obj is not None and obj["resolved_full_id"] == row["resolved_full_id"],
                         path, label + " occurrence lacks its physical full-generation copy")

    data_tokens = []
    for army in frame["army_objects"]:
        arrgs = army["arrg_occurrences"]
        count = army["native_arrg_occurrence_count"]
        _occurrences([row["occurrence"] for row in arrgs], count, complete, path + ".arrg_occurrences")
        if complete:
            _require(army["resolved_full_id"] is not None and not army["unavailable_reason"],
                     path, "complete Army receiver lacks its own full generation")
        for arrg in arrgs:
            occurrence = arrg["occurrence"]
            magic, identity = arrg["resolved_magic_14_raw"], occurrence["resolved_full_id"]
            admitted = arrg["native_refresh_admitted"]
            if admitted is not None:
                _require(magic is not None and identity is not None,
                         path, "known ArRg admission lacks its independent magic/full-ID inputs")
            if magic is not None and identity is not None:
                _require(admitted == (magic == 0x41725267 and identity != -1),
                         path, "ArRg refresh admission differs from the actual magic/full-ID branch")
            records, count = arrg["records"], arrg["native_record_count"]
            _require([row["record_index"] for row in records] == list(range(len(records))),
                     path, "DATA record order changed")
            if admitted is not True:
                _require(not records and count is None and arrg["native_loss_writer_skipped"] is None,
                         path, "unadmitted ArRg manufactured DATA inputs")
                if admitted is False:
                    _require(arrg["records_complete"], path, "known nonrefresh branch lost its complete skip")
                else:
                    _require(not arrg["records_complete"], path, "unknown dispatch promoted DATA completeness")
            elif arrg["native_loss_writer_skipped"] is True:
                _require(not records and arrg["records_complete"],
                         path, "native Character override must not traverse DATA")
            elif arrg["native_loss_writer_skipped"] is None:
                _require(not records and not arrg["records_complete"],
                         path, "unknown Character branch promoted DATA completeness")
            else:
                _require(len(records) <= max(0, count or 0), path, "DATA exceeds its native extent")
                if arrg["records_complete"]:
                    _require(count is not None and count >= 0 and len(records) == count
                             and all(row["native_record_admitted"] for row in records),
                             path, "complete DATA lacks all naturally admitted records")
            if complete:
                _require(admitted is not None and arrg["records_complete"]
                         and not arrg["unavailable_reason"] and not occurrence["unavailable_reason"],
                         path, "complete frame contains an unresolved ArRg/DATA branch")
            for record in records:
                token = record["persistent_physical_token"]
                data_tokens.append(token)
                if not record["native_record_admitted"]:
                    continue
                obj = persistents.get(token)
                chunks = obj["physical_values"]["chunks"] if obj is not None else []
                index = record["chunk_index"]
                _require(record["persistent_regiment_id"] is not None
                         and obj is not None and obj["resolved_full_id"] not in (None, -1)
                         and len(chunks) == 7
                         and index is not None and 0 <= index < 7
                         and record["state_raw"] == chunks[index]["state_raw"]
                         and not record["unavailable_reason"],
                         path, "admitted DATA loses its exact physical chunk/state association")

    def first_known(tokens, objects):
        seen = set()
        ordered = []
        for token in tokens:
            if token in objects and token not in seen:
                seen.add(token)
                ordered.append(token)
        return ordered
    persistent_order = [row["physical_token"] for row in frame["persistent_occurrences"]] + data_tokens
    army_order = [row["physical_token"] for row in frame["army_refresh_occurrences"]]
    for objects, references, label in ((persistents, persistent_order, "persistent"),
                                        (armies, army_order, "Army")):
        copied_order = first_known(references, objects)
        _require(list(objects)[:len(copied_order)] == copied_order
                 and (not complete or len(objects) == len(copied_order)),
                 path, "physical " + label + " first-observation order changed")
    # A partial exception can retain the final materialized object before its
    # referencing occurrence/record is appended. Optional context is separate
    # from completeness of the raw seven-slot copy.


def validate_core_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Validate the already typed owned leaf without filling or rewriting it."""
    path = "actual_army_regular_core_observations_v1"
    _require(value["membership_basis"] == "captured_core_entry_resolved_Army_roster_full_ID",
             path, "query membership must use the captured core entry roster")
    events = value["events"]
    latest = value["latest_journal_sequence"]
    _require(len(events) <= 4 and value["overwritten_events"] == max(0, latest - 4),
             path, "owned journal retention differs from the four-event producer")
    previous = 0
    expected = expected_carmy_id & 0xFFFFFFFF
    for event in events:
        sequence = event["journal_sequence"]
        _require(max(previous, latest - 4) < sequence <= latest,
                 path, "journal retention order differs; it is not the shared event clock")
        previous = sequence
        _require(event["caller_return_rva"] == 0x2A9A8E2,
                 path, "regular core must retain its literal natural caller")
        _require(not event["original_returned"] or event["original_called"],
                 path, "original return lacks its original call")
        _require(not event["entry_provenance_complete"] or event["observed"],
                 path, "complete entry provenance lacks its natural observation")
        scope = event["parent_scope"]
        if event["observed"]:
            _require(scope["observed"] and scope["phase"] == "post_date"
                     and scope["actual_entry_rva"] == 0x2A9A570
                     and scope["primary_manager_identity"] == event["manager_identity"]
                     and scope["secondary_manager_identity"] == event["manager_identity"] + 8
                     and scope["game_state_identity"] != 0 and scope["date_raw"] is not None
                     and _ordered(scope["entry_event"], event["entry_event"])
                     and scope["saved_mask02_admitted"] is True
                     and scope["saved_c0_observed_rva"] == event["caller_return_rva"]
                     and _ordered(event["entry_event"], scope["saved_c0_event"])
                     and event["entry_date_raw"] == scope["date_raw"],
                     path, "complete entry lacks its actual postdate parent/clock/thread/date")
        if event["return_provenance_complete"]:
            _require(event["entry_provenance_complete"] and event["original_returned"]
                     and _ordered(event["entry_event"], event["returned_event"])
                     and _ordered(scope["saved_c0_event"], event["returned_event"])
                     and event["returned_date_raw"] == event["entry_date_raw"],
                     path, "complete return lacks its independent same-parent event/date")
        for label, proof in (("entry", "entry_provenance_complete"),
                             ("returned", "return_provenance_complete")):
            frame = event[label]
            has_copy = (frame["capture_complete"]
                        or frame["native_persistent_occurrence_count"] is not None
                        or frame["native_army_refresh_occurrence_count"] is not None
                        or any(frame[key] for key in ("persistent_occurrences", "army_refresh_occurrences",
                                                     "persistent_objects", "army_objects", "missing_inputs")))
            _require(not frame["capture_complete"] or event[proof],
                     path, label + " complete copy lacks its own natural provenance")
            _require(not has_copy or event["observed"],
                     path, label + " copy lacks its natural entry observation")
            if label == "returned" and has_copy:
                _require(event["entry_provenance_complete"] and event["original_returned"],
                         path, "returned copy lacks its independently observed original return")
            _frame(frame, path + "." + label)
        _require(any(row["resolved_full_id"] is not None
                     and row["resolved_full_id"] & 0xFFFFFFFF == expected
                     for row in event["entry"]["army_refresh_occurrences"]),
                 path, "queried full CArmy generation is absent from the original entry occurrence copy")
