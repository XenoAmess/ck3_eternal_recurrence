"""Strict optional direct-memory operands for the current Domain subsystem."""
from __future__ import annotations

_KEYS = {"status", "ready", "unavailable_reason", "entry_army_id", "group_count_5c_raw", "rows"}
_REQUIRED_I32 = {"group_index", "stored_index", "record_regiment_reference_id", "chunk_index"}
_OPTIONAL_I32 = {
    "record_regiment_resolved_id", "data_state_18_raw", "data_owner_regiment_reference_id",
    "receiver_regiment_resolved_id", "receiver_state_138_raw", "receiver_title_reference_130_raw",
    "receiver_character_reference_12c_raw", "owner_title_resolved_id",
    "owner_title_holder_character_id_128_raw", "selected_character_reference_id",
    "selected_character_resolved_id", "domain_reference_id", "domain_resolved_id",
    "count_base_128_raw", "domain_owner_character_reference_id",
    "domain_owner_character_resolved_id", "domain_alias_ordinal",
}
_OPTIONAL_U32 = {"record_regiment_magic_14_raw", "domain_magic_0c_raw", "domain_owner_character_magic_1c_raw"}
_OPTIONAL_BOOL = {
    "record_regiment_used_fallback", "data_record_present", "receiver_regiment_used_fallback",
    "owner_title_used_fallback", "selected_character_used_fallback", "character_domain_child_present",
    "domain_used_fallback", "domain_data_30_present", "domain_owner_character_used_fallback",
}
_ROW_KEYS = (_REQUIRED_I32 | _OPTIONAL_I32 | _OPTIONAL_U32 | _OPTIONAL_BOOL
             | {"domain_flag_17e_raw", "domain_value_48_raw64", "count_records"})
_COUNT_KEYS = {"stored_index", "count_00_raw", "count_04_raw", "state_18_raw"}


def _integer(value: object, bits: int, signed: bool, nullable: bool = True) -> None:
    if value is None and nullable:
        return
    lower = -(1 << (bits - 1)) if signed else 0
    upper = 1 << (bits - 1) if signed else 1 << bits
    if type(value) is not int or not lower <= value < upper:
        raise ValueError("native current helper Domain integer width is malformed")


def normalize_monthly_current_helper_domain_inputs_v1(value: object) -> dict[str, object] | None:
    """Validate captured traversal, preserving lawful branch-dependent nulls."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native current helper Domain schema is malformed")
    status = value["status"]
    if status not in {"available", "unavailable"}:
        raise ValueError("native current helper Domain status is malformed")
    ready = status == "available"
    if type(value["ready"]) is not bool or value["ready"] != ready:
        raise ValueError("native current helper Domain readiness is malformed")
    reason = value["unavailable_reason"]
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native current helper Domain reason disagrees with readiness")
    _integer(value["entry_army_id"], 32, True)
    _integer(value["group_count_5c_raw"], 32, True)
    result = dict(value)
    rows = value["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError("native current helper Domain rows must be ordered or null")
        copied = []
        previous = None
        for row in rows:
            if not isinstance(row, dict) or set(row) != _ROW_KEYS:
                raise ValueError("native current helper Domain row schema is malformed")
            for key in _REQUIRED_I32:
                _integer(row[key], 32, True, False)
            for key in _OPTIONAL_I32:
                _integer(row[key], 32, True)
            for key in _OPTIONAL_U32:
                _integer(row[key], 32, False)
            for key in _OPTIONAL_BOOL:
                if row[key] is not None and type(row[key]) is not bool:
                    raise ValueError("native current helper Domain predicate must be bool or null")
            _integer(row["domain_flag_17e_raw"], 8, False)
            _integer(row["domain_value_48_raw64"], 64, True)
            ordinal = (row["group_index"], row["stored_index"])
            if min(ordinal) < 0 or (previous is not None and ordinal <= previous):
                raise ValueError("native current helper Domain stored order is malformed")
            previous = ordinal
            alias = row["domain_alias_ordinal"]
            if alias is not None and alias < 0:
                raise ValueError("native current helper Domain alias ordinal is negative")
            copy = dict(row)
            records = row["count_records"]
            if records is not None:
                if not isinstance(records, list) or len(records) != 7:
                    raise ValueError("native current helper Domain count must have exactly seven records")
                record_copies = []
                for index, record in enumerate(records):
                    if not isinstance(record, dict) or set(record) != _COUNT_KEYS:
                        raise ValueError("native current helper Domain count record schema is malformed")
                    _integer(record["stored_index"], 32, True, False)
                    if record["stored_index"] != index:
                        raise ValueError("native current helper Domain count record order is malformed")
                    for key in ("count_00_raw", "count_04_raw", "state_18_raw"):
                        _integer(record[key], 32, True)
                    record_copies.append(dict(record))
                copy["count_records"] = record_copies
            copied.append(copy)
        result["rows"] = copied
    # Available means the traversal was captured. Individual row operands
    # remain nullable, including ordinary skipped-record branches.
    if ready and any(value[key] is None for key in ("entry_army_id", "group_count_5c_raw", "rows")):
        raise ValueError("native ready current helper Domain traversal is incomplete")
    return result
