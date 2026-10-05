"""Strict raw cached absent-1C8 leaf; computation remains in the pure kernel."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)

_FIELD = "absent_recipient_inputs"


def _word64(value: object, field: str) -> int | None:
    if isinstance(value, str):
        digits = value[2:] if value[:2].lower() == "0x" else ""
        if not digits or len(digits) > 16 or any(
                char not in "0123456789abcdefABCDEF" for char in digits):
            raise ValueError(field + " must be a native unsigned64 or hexadecimal pointer")
        value = int(digits, 16)
    return _number(value, field, 64, unsigned=True)


def _mapping(value: object, field: str, *, linked: bool) -> dict:
    raw = _dict(value, field, {"count", "mask", "max_probe_u8", "entries"})
    entries = raw["entries"]
    if entries is not None and not isinstance(entries, list):
        raise ValueError(field + ".entries must be a list or null")
    rows = None
    if entries is not None:
        rows = []
        prior_bucket = -1
        for index, entry in enumerate(entries):
            path = f"{field}.entries[{index}]"
            keys = {"bucket_index", "hash_u32", "probe_u8", "key_object"}
            keys |= {"value_u64"} if linked else {"trait_id_u32", "value_q64"}
            row = _dict(entry, path, keys)
            bucket = _integer(row["bucket_index"], path + ".bucket_index", 32, unsigned=True)
            if bucket <= prior_bucket:
                raise ValueError(path + ".bucket_index must retain increasing native bucket order")
            prior_bucket = bucket
            result = {
                "bucket_index": bucket,
                "hash_u32": _number(row["hash_u32"], path + ".hash_u32", 32, unsigned=True),
                "probe_u8": _number(row["probe_u8"], path + ".probe_u8", 8, unsigned=True),
                "key_object": _word64(row["key_object"], path + ".key_object"),
            }
            if result["probe_u8"] in (0, 0xFF):
                raise ValueError(path + ".probe_u8 cannot describe an empty bucket or end sentinel")
            if linked:
                result["value_u64"] = _word64(row["value_u64"], path + ".value_u64")
            else:
                result["trait_id_u32"] = _number(row["trait_id_u32"], path + ".trait_id_u32", 32, unsigned=True)
                result["value_q64"] = _number(row["value_q64"], path + ".value_q64", 64)
            rows.append(result)
    count = _number(raw["count"], field + ".count", 32)
    if count is not None and rows is not None and len(rows) > max(count, 0):
        raise ValueError(field + ".entries exceeds the native occupied count")
    return {
        "count": count,
        "mask": _number(raw["mask"], field + ".mask", 32),
        "max_probe_u8": _number(raw["max_probe_u8"], field + ".max_probe_u8", 8, unsigned=True),
        "entries": rows,
    }


def _ids(value: object, field: str, bits: int) -> dict:
    name = "values_u32" if bits == 32 else "values_u64"
    raw = _dict(value, field, {"count", name})
    return {
        "count": _number(raw["count"], field + ".count", 32),
        name: _numbers(raw[name], field + "." + name, bits, unsigned=True),
    }


def normalize_absent_recipient_inputs(value: object, field: str = _FIELD) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", "carrier_present",
        "associated_full_id", "associated_resolved_full_id", "associated_used_fallback",
        "associated_cache_440", "cached_map_430", "cached_map_458", "trait_ids",
        "membership_ids", "membership_header_guard_raw", "aggregate_properties",
        "aggregate_context_selection", "aggregate_context_guard_raw", "member_multiplier_q64",
        "clamp_lower_q64", "clamp_upper_q64", "calculated_recipient_q64", "reason",
    })
    status = _string(raw["status"], field + ".status")
    if status not in {"available", "partial", "not_applicable"}:
        raise ValueError(field + ".status is unsupported")
    result = {
        "status": status,
        "ready": _boolean(raw["ready"], field + ".ready"),
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "carrier_present": _boolean(raw["carrier_present"], field + ".carrier_present", optional=True),
        "associated_used_fallback": _boolean(raw["associated_used_fallback"], field + ".associated_used_fallback", optional=True),
        "cached_map_430": _mapping(raw["cached_map_430"], field + ".cached_map_430", linked=False),
        "cached_map_458": _mapping(raw["cached_map_458"], field + ".cached_map_458", linked=True),
        "trait_ids": _ids(raw["trait_ids"], field + ".trait_ids", 32),
        "membership_ids": _ids(raw["membership_ids"], field + ".membership_ids", 64),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    for key in ("associated_full_id", "associated_resolved_full_id", "associated_cache_440"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    for key in ("membership_header_guard_raw", "aggregate_context_guard_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("member_multiplier_q64", "clamp_lower_q64", "clamp_upper_q64", "calculated_recipient_q64"):
        result[key] = _number(raw[key], field + "." + key, 64)
    selection = _string(raw["aggregate_context_selection"], field + ".aggregate_context_selection", optional=True)
    if selection not in {None, "owned_model_10", "inline_context_5d67b90"}:
        raise ValueError(field + ".aggregate_context_selection is unsupported")
    result["aggregate_context_selection"] = selection
    aggregate = _dict(raw["aggregate_properties"], field + ".aggregate_properties", {
        "count", "keys_u16", "values_q64",
    })
    result["aggregate_properties"] = {
        "count": _number(aggregate["count"], field + ".aggregate_properties.count", 32),
        "keys_u16": _numbers(aggregate["keys_u16"], field + ".aggregate_properties.keys_u16", 16, unsigned=True),
        "values_q64": _numbers(aggregate["values_q64"], field + ".aggregate_properties.values_q64", 64),
    }
    from ..simulation.battle_person_absent_recipient_12003 import (
        compute_absent_recipient_from_native_inputs_12003,
    )
    calculated = compute_absent_recipient_from_native_inputs_12003(result)
    if status == "not_applicable":
        if (result["ready"] is not True or result["carrier_present"] is not True
                or result["calculated_recipient_q64"] is not None or result["reason"] is not None):
            raise ValueError(field + " has inconsistent present1C8 skip")
    elif status == "available":
        if (result["ready"] is not True or result["reason"] is not None
                or not calculated.calculation_ready
                or result["calculated_recipient_q64"] != calculated.value_q64):
            raise ValueError(field + " available scalar differs from actual native inputs")
    elif (result["ready"] is not False or result["calculated_recipient_q64"] is not None
          or result["reason"] is None):
        raise ValueError(field + " has inconsistent partial observation")
    return result
