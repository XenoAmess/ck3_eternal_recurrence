"""Exact .3 current operands for the finite monthly caller effects."""
from __future__ import annotations

_KEYS = {"status", "ready", "unavailable_reason", "army_byte_22_raw",
         "current_date_storage_raw64", "unit_actor_character_id",
         "war_counter_rows", "manager_army_id_list_2a5a8"}
_ROW_KEYS = {"status", "unavailable_reason", "stored_index", "war_reference_id",
             "resolved_war_id", "used_fallback", "native_selected_side", "native_counter_30_raw"}


def normalize_monthly_caller_effect_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native monthly_caller_effect_inputs_v1 schema is malformed")

    def readiness(item: dict[str, object]) -> bool:
        status, reason = item["status"], item["unavailable_reason"]
        if status not in {"available", "unavailable"}:
            raise ValueError("native monthly caller status is malformed")
        ready = status == "available"
        if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
            raise ValueError("native monthly caller reason disagrees with readiness")
        return ready

    def integer(item: object, bits: int, signed: bool = True, nullable: bool = True) -> None:
        if item is None and nullable:
            return
        lower, upper = (-(1 << (bits - 1)), 1 << (bits - 1)) if signed else (0, 1 << bits)
        if type(item) is not int or not lower <= item < upper:
            raise ValueError("native monthly caller operand has invalid integer width")

    ready = readiness(value)
    if type(value["ready"]) is not bool or value["ready"] != ready:
        raise ValueError("native monthly caller readiness is malformed")
    integer(value["army_byte_22_raw"], 8, False)
    integer(value["current_date_storage_raw64"], 64)
    integer(value["unit_actor_character_id"], 32)
    result = dict(value)
    rows = value["war_counter_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError("native monthly caller rows must be an ordered array or null")
        normalized = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != _ROW_KEYS:
                raise ValueError("native monthly caller war row is malformed")
            row_ready = readiness(row)
            integer(row["stored_index"], 32, nullable=False)
            if row["stored_index"] != index:
                raise ValueError("native monthly caller row order is malformed")
            integer(row["war_reference_id"], 32, nullable=False)
            for key in ("resolved_war_id", "native_counter_30_raw"):
                integer(row[key], 32)
            if row["used_fallback"] is not None and type(row["used_fallback"]) is not bool:
                raise ValueError("native monthly caller fallback must be bool or null")
            if row["native_selected_side"] is not None and (
                    type(row["native_selected_side"]) is not int or row["native_selected_side"] not in {-1, 0, 1}):
                raise ValueError("native monthly caller side is malformed")
            if row_ready and (any(row[key] is None for key in (
                    "resolved_war_id", "used_fallback", "native_selected_side"))
                    or (row["native_selected_side"] != -1 and row["native_counter_30_raw"] is None)):
                raise ValueError("native available monthly caller war row is incomplete")
            if row["native_selected_side"] == -1 and row["native_counter_30_raw"] is not None:
                raise ValueError("native monthly caller no-side counter must be null")
            normalized.append(dict(row))
        result["war_counter_rows"] = normalized
    ids = value["manager_army_id_list_2a5a8"]
    if ids is not None:
        if not isinstance(ids, list):
            raise ValueError("native monthly caller ArmyID list must be an ordered array or null")
        for item in ids:
            integer(item, 32, nullable=False)
        result["manager_army_id_list_2a5a8"] = list(ids)
    if ready and (any(value[key] is None for key in _KEYS - {"status", "ready", "unavailable_reason"})
                  or any(row["status"] != "available" for row in rows)):
        raise ValueError("native ready monthly caller operands are incomplete")
    return result
