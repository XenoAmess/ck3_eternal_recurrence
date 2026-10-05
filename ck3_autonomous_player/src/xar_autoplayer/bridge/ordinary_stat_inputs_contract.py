"""Strict typed wire for exact .3 ordinary selected-Character getter sources."""
from __future__ import annotations


def _object(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"native {name} has unexpected fields")
    return value


def _integer(value, bits, name):
    if value is None:
        return None
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"native {name} must be signed int{bits} or null")
    return value


def normalize_ordinary_stat_inputs_v1(value, *, name):
    row = _object(value, {"status", "selected_character_full_id", "character_resolution",
                         "aggregate_properties", "loaded_bases", "scale", "unavailable_reason"}, name)
    status = row["status"]
    if status not in {"available", "unavailable"}:
        raise ValueError(f"native {name}.status differs")
    character = _integer(row["selected_character_full_id"], 32, name + ".selected_character_full_id")
    resolution = row["character_resolution"]
    if resolution not in {None, "generation_resolved", "native_fallback"}:
        raise ValueError(f"native {name}.character_resolution differs")
    pc = _object(row["aggregate_properties"], {"count", "keys_u16", "values_q64"}, name + ".aggregate_properties")
    count = _integer(pc["count"], 32, name + ".aggregate_properties.count")
    keys, values = pc["keys_u16"], pc["values_q64"]
    if keys is not None and (not isinstance(keys, list) or any(type(key) is not int or not 0 <= key <= 0xFFFF for key in keys)):
        raise ValueError(f"native {name}.aggregate_properties.keys_u16 differs")
    if values is not None:
        if not isinstance(values, list):
            raise ValueError(f"native {name}.aggregate_properties.values_q64 differs")
        values = [_integer(item, 64, name + ".aggregate_properties.values_q64") for item in values]
    names = {"siege_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw"}
    bases = _object(row["loaded_bases"], names, name + ".loaded_bases")
    bases = {key: _integer(bases[key], 64, name + ".loaded_bases." + key) for key in bases}
    if row["scale"] != 100000:
        raise ValueError(f"native {name}.scale differs")
    reason = row["unavailable_reason"]
    if status == "available":
        if (character is None or resolution is None or count is None or count < 0 or
                keys is None or values is None or len(keys) != count or len(values) != count or
                any(value is None for value in values) or any(value is None for value in bases.values()) or reason is not None):
            raise ValueError(f"native available {name} lacks demanded source operands")
    elif not isinstance(reason, str) or not reason:
        raise ValueError(f"native unavailable {name} lacks reason")
    return {"status": status, "selected_character_full_id": character,
            "character_resolution": resolution,
            "aggregate_properties": {"count": count, "keys_u16": keys, "values_q64": values},
            "loaded_bases": bases, "scale": 100000, "unavailable_reason": reason}
