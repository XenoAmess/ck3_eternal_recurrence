"""Current ordered IDs and initial generation resolution for the daily queue."""
from __future__ import annotations

_KEYS = {"status", "ready", "unavailable_reason", "manager_army_id_list_2a5a8",
         "initial_army_resolution_rows"}
_ROW_KEYS = {"status", "unavailable_reason", "stored_index", "raw_army_reference_id",
             "resolved_army_id", "used_fallback", "army_magic_14_raw", "native_army_identity_valid"}


def normalize_monthly_daily_queue_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native daily queue inputs schema is malformed")

    def readiness(item: dict[str, object]) -> bool:
        status, reason = item["status"], item["unavailable_reason"]
        if status not in {"available", "unavailable"}:
            raise ValueError("native daily queue status is malformed")
        ready = status == "available"
        if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
            raise ValueError("native daily queue reason disagrees with readiness")
        return ready

    def integer(item: object, bits: int, signed: bool = True, nullable: bool = True) -> None:
        if item is None and nullable:
            return
        lower, upper = (-(1 << (bits - 1)), 1 << (bits - 1)) if signed else (0, 1 << bits)
        if type(item) is not int or not lower <= item < upper:
            raise ValueError("native daily queue operand has invalid integer width")

    ready = readiness(value)
    if type(value["ready"]) is not bool or value["ready"] != ready:
        raise ValueError("native daily queue readiness is malformed")
    result = dict(value)
    ids = value["manager_army_id_list_2a5a8"]
    if ids is not None:
        if not isinstance(ids, list):
            raise ValueError("native daily queue IDs must be an ordered array or null")
        for item in ids:
            integer(item, 32, nullable=False)
        result["manager_army_id_list_2a5a8"] = list(ids)
    rows = value["initial_army_resolution_rows"]
    if rows is not None:
        if not isinstance(rows, list) or (ids is not None and len(rows) != len(ids)):
            raise ValueError("native daily queue resolution rows disagree with ordered IDs")
        normalized = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != _ROW_KEYS:
                raise ValueError("native daily queue resolution row is malformed")
            row_ready = readiness(row)
            integer(row["stored_index"], 32, nullable=False)
            integer(row["raw_army_reference_id"], 32, nullable=False)
            integer(row["resolved_army_id"], 32)
            integer(row["army_magic_14_raw"], 32, False)
            if row["stored_index"] != index or (ids is not None and row["raw_army_reference_id"] != ids[index]):
                raise ValueError("native daily queue occurrence order disagrees with IDs")
            for key in ("used_fallback", "native_army_identity_valid"):
                if row[key] is not None and type(row[key]) is not bool:
                    raise ValueError("native daily queue predicate must be bool or null")
            if row_ready and any(row[key] is None for key in (
                    "resolved_army_id", "used_fallback", "army_magic_14_raw", "native_army_identity_valid")):
                raise ValueError("native available daily queue row is incomplete")
            normalized.append(dict(row))
        result["initial_army_resolution_rows"] = normalized
    if ready and (ids is None or rows is None or any(row["status"] != "available" for row in rows)):
        raise ValueError("native ready daily queue inputs are incomplete")
    return result
