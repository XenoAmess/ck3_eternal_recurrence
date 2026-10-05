"""Strict current actual 258A470 outputs beside independently stored Combat+710."""

from __future__ import annotations


def _signed(value: object, field: str, bits: int) -> int:
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"{field} must be signed int{bits}")
    return value


def normalize_current_dynamic_advantage_v1(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "scale", "base_advantage_raw", "stored_resolved_advantage_raw", "sides",
    }:
        raise ValueError(f"{field} must contain current dynamic advantage fields")
    if type(value["scale"]) is not int or value["scale"] != 100000:
        raise ValueError(f"{field}.scale must be 100000")
    base = _signed(value["base_advantage_raw"], f"{field}.base_advantage_raw", 64)
    stored = _signed(value["stored_resolved_advantage_raw"], f"{field}.stored_resolved_advantage_raw", 64)
    sides = value["sides"]
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f"{field}.sides requires both native side slots")
    normalized = []
    for index, side in enumerate(sides):
        if not isinstance(side, dict) or set(side) != {
            "side_index", "status", "current_roll_points", "selected_character_id_raw",
            "side_dynamic_total_raw", "unavailable_reason",
        } or type(side["side_index"]) is not int or side["side_index"] != index:
            raise ValueError(f"{field}.sides must retain native side order")
        roll = _signed(side["current_roll_points"], f"{field}.sides.current_roll_points", 32)
        selected = _signed(side["selected_character_id_raw"], f"{field}.sides.selected_character_id_raw", 32)
        status, total, reason = side["status"], side["side_dynamic_total_raw"], side["unavailable_reason"]
        if status == "available":
            total = _signed(total, f"{field}.sides.side_dynamic_total_raw", 64)
            if reason is not None:
                raise ValueError(f"{field}.sides available total must have null reason")
        elif status != "unavailable" or total is not None or not isinstance(reason, str) or not reason:
            raise ValueError(f"{field}.sides unavailable total requires null and reason")
        normalized.append({"side_index": index, "status": status, "current_roll_points": roll,
                           "selected_character_id_raw": selected, "side_dynamic_total_raw": total,
                           "unavailable_reason": reason})
    return {"scale": 100000, "base_advantage_raw": base,
            "stored_resolved_advantage_raw": stored, "sides": normalized}
