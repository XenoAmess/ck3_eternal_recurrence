"""Optional source operands for the first daily manager cleanup stage."""
from __future__ import annotations

_OFFSETS = ("50", "68", "80", "98", "c8", "158")
_KEYS = {"status", "ready", "unavailable_reason", "candidate_found",
         "candidate_stored_index", "argument_army_id", "cleanup_resolved_army_id",
         "cleanup_used_fallback", "selected_bucket_index", "id_lists",
         "selected_bucket_rows", "records_b0"}
_LIST_KEYS = {"manager_offset", "ordered_army_ids"}
_BUCKET_KEYS = {"stored_index", "observed_army_id", "native_same_cleanup_army_pointer"}


def normalize_monthly_first_removal_cleanup_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native first removal cleanup schema is malformed")
    ready = value["status"] == "available"
    reason = value["unavailable_reason"]
    if value["status"] not in {"available", "unavailable"}:
        raise ValueError("native first removal cleanup status is malformed")
    if type(value["ready"]) is not bool or value["ready"] != ready:
        raise ValueError("native first removal cleanup readiness is malformed")
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native first removal cleanup reason disagrees with readiness")

    def integer(item: object, signed: bool = True, nullable: bool = True) -> None:
        if item is None and nullable:
            return
        lower, upper = (-(1 << 31), 1 << 31) if signed else (0, 1 << 32)
        if type(item) is not int or not lower <= item < upper:
            raise ValueError("native first removal cleanup integer width is malformed")

    for key in ("candidate_found", "cleanup_used_fallback"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError("native first removal cleanup predicate must be bool or null")
    for key in ("candidate_stored_index", "argument_army_id", "cleanup_resolved_army_id"):
        integer(value[key])
    index = value["candidate_stored_index"]
    if index is not None and index < 0:
        raise ValueError("native first removal cleanup candidate index is negative")
    bucket_index = value["selected_bucket_index"]
    integer(bucket_index, False)
    if bucket_index is not None and bucket_index >= 30:
        raise ValueError("native first removal cleanup bucket index is outside30 phases")

    result = dict(value)
    lists = value["id_lists"]
    if not isinstance(lists, list) or len(lists) != len(_OFFSETS):
        raise ValueError("native first removal cleanup must publish six ordered ID-list components")
    normalized_lists = []
    for offset, component in zip(_OFFSETS, lists):
        if (not isinstance(component, dict) or set(component) != _LIST_KEYS
                or component["manager_offset"] != offset):
            raise ValueError("native first removal cleanup ID-list component order is malformed")
        ids = component["ordered_army_ids"]
        if ids is not None:
            if not isinstance(ids, list):
                raise ValueError("native first removal cleanup IDs must be an ordered list or null")
            for item in ids:
                integer(item, nullable=False)
        normalized_lists.append({"manager_offset": offset,
                                 "ordered_army_ids": None if ids is None else list(ids)})
    result["id_lists"] = normalized_lists

    rows = value["selected_bucket_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError("native first removal cleanup bucket must be an ordered list or null")
        normalized_rows = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != _BUCKET_KEYS:
                raise ValueError("native first removal cleanup bucket occurrence is malformed")
            integer(row["stored_index"], nullable=False)
            integer(row["observed_army_id"])
            if row["stored_index"] != index or type(row["native_same_cleanup_army_pointer"]) is not bool:
                raise ValueError("native first removal cleanup bucket order or pointer predicate is malformed")
            normalized_rows.append(dict(row))
        result["selected_bucket_rows"] = normalized_rows

    records = value["records_b0"]
    if records is not None:
        if not isinstance(records, list):
            raise ValueError("native first removal cleanup records must be an ordered list or null")
        copied = []
        for words in records:
            if not isinstance(words, list) or len(words) != 4:
                raise ValueError("native first removal cleanup record must preserve four DWORDs")
            for word in words:
                integer(word, False, False)
            copied.append(list(words))
        result["records_b0"] = copied
    if ready:
        if value["candidate_found"] is None:
            raise ValueError("native ready first removal cleanup selection is incomplete")
        if value["candidate_found"]:
            if any(value[key] is None for key in ("candidate_stored_index", "argument_army_id",
                       "cleanup_resolved_army_id", "cleanup_used_fallback", "selected_bucket_index",
                       "selected_bucket_rows", "records_b0")) or any(
                           item["ordered_army_ids"] is None for item in normalized_lists):
                raise ValueError("native ready first removal cleanup operands are incomplete")
    return result
