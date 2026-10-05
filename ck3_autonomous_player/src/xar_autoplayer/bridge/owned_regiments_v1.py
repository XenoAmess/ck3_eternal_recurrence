"""Normalize the optional owned-Regi object carried by army strengths.

Direct owned inventory and raw chunk inputs are preserved independently of
raising eligibility and of the raised ArRg strength aggregate.
"""

from __future__ import annotations


_TOP_KEYS = {
    "schema", "scope", "status", "actor_character_id", "source_count",
    "collection_complete", "regiments", "unavailable_reason",
}
_ROW_KEYS = {
    "persistent_regiment_id", "available", "owner_character_id",
    "native_capacity_raw", "maa_type_status", "maa_type_key",
    "siege_tier_observable", "siege_tier", "composition_unavailable_reason",
    "chunks", "unavailable_reason",
}
_CHUNK_KEYS = {
    "chunk_index", "maximum_soldiers", "current_soldiers",
    "persistent_regiment_id", "native_chunk_index", "army_regiment_id",
    "pending_raw", "pending", "state_raw",
}


def _object(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native {name} schema is malformed")
    return value


def _int32(value: object, name: str) -> int:
    if type(value) is not int or not -(2**31) <= value <= 2**31 - 1:
        raise ValueError(f"native {name} must be a signed int32")
    return value


def _optional_int32(value: object, name: str) -> int | None:
    return None if value is None else _int32(value, name)


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"native {name} must be a boolean")
    return value


def _reason(value: object, name: str) -> str | None:
    if value is not None and (not isinstance(value, str) or not value):
        raise ValueError(f"native {name} must be null or a nonempty string")
    return value


def _normalize_chunk(value: object, name: str) -> dict[str, object]:
    row = _object(value, _CHUNK_KEYS, name)
    output: dict[str, object] = {
        key: _int32(row[key], f"{name}.{key}")
        for key in _CHUNK_KEYS - {"pending_raw", "pending"}
    }
    pending_raw = row["pending_raw"]
    if type(pending_raw) is not int or not 0 <= pending_raw <= 255:
        raise ValueError(f"native {name}.pending_raw must be a byte")
    pending = _boolean(row["pending"], f"{name}.pending")
    if pending is not (pending_raw != 0):
        raise ValueError(f"native {name}.pending disagrees with pending_raw")
    output.update(pending_raw=pending_raw, pending=pending)
    return output


def _normalize_record(value: object, name: str) -> dict[str, object]:
    row = _object(value, _ROW_KEYS, name)
    available = _boolean(row["available"], f"{name}.available")
    type_status = row["maa_type_status"]
    if not isinstance(type_status, str) or type_status not in {
        "available", "absent", "unavailable"
    }:
        raise ValueError(f"native {name}.maa_type_status is malformed")
    key = row["maa_type_key"]
    if type_status == "available":
        if not isinstance(key, str) or not key:
            raise ValueError(f"native {name}.maa_type_key must be observed")
    elif key is not None:
        raise ValueError(f"native {name}.maa_type_key must be null")
    tier = _optional_int32(row["siege_tier"], f"{name}.siege_tier")
    tier_observable = _boolean(
        row["siege_tier_observable"], f"{name}.siege_tier_observable"
    )
    if tier_observable is not (tier is not None):
        raise ValueError(f"native {name}.siege_tier_observable disagrees with tier")
    chunks_value = row["chunks"]
    if available:
        if not isinstance(chunks_value, list) or len(chunks_value) != 7:
            raise ValueError(f"native {name}.chunks must contain all seven chunks")
        chunks = [
            _normalize_chunk(chunk, f"{name}.chunks[{index}]")
            for index, chunk in enumerate(chunks_value)
        ]
    else:
        if chunks_value is not None:
            raise ValueError(f"native {name}.chunks must be null when unread")
        chunks = None
    return {
        "persistent_regiment_id": _int32(row["persistent_regiment_id"], f"{name}.persistent_regiment_id"),
        "available": available,
        "owner_character_id": _optional_int32(row["owner_character_id"], f"{name}.owner_character_id"),
        "native_capacity_raw": _optional_int32(row["native_capacity_raw"], f"{name}.native_capacity_raw"),
        "maa_type_status": type_status,
        "maa_type_key": key,
        "siege_tier_observable": tier_observable,
        "siege_tier": tier,
        "composition_unavailable_reason": _reason(row["composition_unavailable_reason"], f"{name}.composition_unavailable_reason"),
        "chunks": chunks,
        "unavailable_reason": _reason(row["unavailable_reason"], f"{name}.unavailable_reason"),
    }


def normalize_owned_regiments_v1(
    value: object, *, name: str = "owned_regiments_v1"
) -> dict[str, object] | None:
    """Preserve explicit null; callers preserve legacy field omission."""
    if value is None:
        return None
    payload = _object(value, _TOP_KEYS, name)
    if payload["schema"] != "ck3_12003_owned_regiments_v1":
        raise ValueError(f"native {name}.schema is malformed")
    if payload["scope"] != "current-player-direct-owned-regiments":
        raise ValueError(f"native {name}.scope is malformed")
    status = payload["status"]
    if not isinstance(status, str) or status not in {
        "available", "partial", "unavailable"
    }:
        raise ValueError(f"native {name}.status is malformed")
    count = _optional_int32(payload["source_count"], f"{name}.source_count")
    complete = _boolean(payload["collection_complete"], f"{name}.collection_complete")
    values = payload["regiments"]
    if status == "unavailable":
        if values is not None:
            raise ValueError(f"native {name}.regiments must be null when unread")
        regiments = None
    else:
        if not isinstance(values, list):
            raise ValueError(f"native {name}.regiments must be a list")
        regiments = [
            _normalize_record(row, f"{name}.regiments[{index}]")
            for index, row in enumerate(values)
        ]
        if complete and count is not None and len(regiments) != count:
            raise ValueError(f"native {name}.regiments must retain the complete source vector")
    return {
        "schema": payload["schema"], "scope": payload["scope"], "status": status,
        "actor_character_id": _int32(payload["actor_character_id"], f"{name}.actor_character_id"),
        "source_count": count, "collection_complete": complete,
        "regiments": regiments,
        "unavailable_reason": _reason(payload["unavailable_reason"], f"{name}.unavailable_reason"),
    }
