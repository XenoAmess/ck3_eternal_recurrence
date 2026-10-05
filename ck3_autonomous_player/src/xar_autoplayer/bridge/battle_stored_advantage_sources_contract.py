"""Actual retained 16-byte effect ledger; row amounts are already scaled."""

from __future__ import annotations

from .battle_stored_effect_flags_contract import normalize_stored_effect_flags_v1


def _i64(value: object, field: str) -> int:
    if type(value) is not int or not -(1 << 63) <= value < (1 << 63):
        raise ValueError(f"{field} must be signed int64")
    return value


def normalize_stored_advantage_sources_v1(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "scale", "base_advantage_raw", "resolved_advantage_raw", "sides",
    }:
        raise ValueError(f"{field} must contain the stored advantage source fields")
    if type(value["scale"]) is not int or value["scale"] != 100000:
        raise ValueError(f"{field}.scale must be 100000")
    base = _i64(value["base_advantage_raw"], f"{field}.base_advantage_raw")
    resolved = _i64(value["resolved_advantage_raw"], f"{field}.resolved_advantage_raw")
    sides = value["sides"]
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f"{field}.sides requires both stored side slots")
    normalized = []
    for index, side in enumerate(sides):
        if not isinstance(side, dict) or set(side) != {
            "side_index", "status", "unavailable_reason", "rows",
        } or type(side["side_index"]) is not int or side["side_index"] != index:
            raise ValueError(f"{field}.sides must retain native side order")
        status, reason, rows = side["status"], side["unavailable_reason"], side["rows"]
        if status == "unavailable":
            if rows is not None or not isinstance(reason, str) or not reason:
                raise ValueError(f"{field}.sides unavailable ledger must be null with reason")
            normalized.append(dict(side))
            continue
        if status != "available" or reason is not None or not isinstance(rows, list) or len(rows) > 65536:
            raise ValueError(f"{field}.sides available ledger is invalid")
        copied_rows = []
        for row in rows:
            required = {"effect_key", "key_unavailable_reason", "contribution_raw"}
            if not isinstance(row, dict) or not required <= set(row) or set(row) - required - {"effect_flags_v1"}:
                raise ValueError(f"{field}.rows has invalid retained source fields")
            key, key_reason = row["effect_key"], row["key_unavailable_reason"]
            if key is None:
                if not isinstance(key_reason, str) or not key_reason:
                    raise ValueError(f"{field}.rows undecoded key requires a reason")
            elif not isinstance(key, str) or not 1 <= len(key) <= 512 or key_reason is not None:
                raise ValueError(f"{field}.rows decoded key is invalid")
            amount = _i64(row["contribution_raw"], f"{field}.rows.contribution_raw")
            copied = {"effect_key": key, "key_unavailable_reason": key_reason, "contribution_raw": amount}
            if "effect_flags_v1" in row:
                copied["effect_flags_v1"] = normalize_stored_effect_flags_v1(
                    row["effect_flags_v1"], field=f"{field}.rows.effect_flags_v1",
                )
            copied_rows.append(copied)
        normalized.append({"side_index": index, "status": status,
                           "unavailable_reason": None, "rows": copied_rows})
    return {"scale": 100000, "base_advantage_raw": base,
            "resolved_advantage_raw": resolved, "sides": normalized}
