"""Same-query current trait composites and classified owner requests, exact .3.

The pure fold reuses the existing source-closed logical PropertyContainer
kernel. No allocator, initializer, getter or native callback is executed.
"""
from __future__ import annotations

from bisect import bisect_left

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _numbers, _properties,
    _properties_ready, _string,
)

_FIELD = "trait_stage_291d460"
_TOP_STRINGS = ("selector_a_selection", "selector_a_identity", "selector_b_selection", "selector_b_identity")
_TOP_WORDS = ("selector_a_key_raw", "selector_b_key_raw", "selector_a_membership_count",
              "selector_b_primary_count", "selector_b_nested_count")
_TOP_ARRAYS = ("selector_a_keys_i32", "selector_b_primary_keys_i32")


def _pc_ready(block: dict | None) -> bool:
    return _properties_ready(block) and block["reason"] is None


def _wrap32(value: int) -> int:
    return (value + 2**31) % 2**32 - 2**31


def _fnv_pointer(value: int) -> int:
    result = 0x811C9DC5
    for byte in value.to_bytes(8, "little"):
        result = ((result ^ byte) * 0x1000193) & 0xFFFFFFFF
    return result


def _contains(keys: list[int], key: int) -> bool:
    index = bisect_left(keys, key)
    return index != len(keys) and keys[index] == key


def _keys_complete(count: int | None, keys: list[int] | None) -> bool:
    return count is not None and keys is not None and len(keys) == max(0, count)


def _membership(stage: dict, key: int, first: bool) -> bool | None:
    if first:
        if not _keys_complete(stage["selector_a_membership_count"], stage["selector_a_keys_i32"]):
            return None
        return _contains(stage["selector_a_keys_i32"], key)
    if not _keys_complete(stage["selector_b_primary_count"], stage["selector_b_primary_keys_i32"]):
        return None
    if _contains(stage["selector_b_primary_keys_i32"], key):
        return True
    count, sets = stage["selector_b_nested_count"], stage["selector_b_nested_keys"]
    if count is None or sets is None:
        return None
    for keys in sets:
        if not _keys_complete(keys["count"], keys["keys_i32"]) or keys["reason"] is not None:
            return None
        if _contains(keys["keys_i32"], key):
            return True
    return False if len(sets) == max(0, count) else None


def _keyset(value: object, field: str, index: int) -> dict:
    raw = _dict(value, field, {"native_index", "count", "keys_i32", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "count": _number(raw["count"], field + ".count", 32),
              "keys_i32": _numbers(raw["keys_i32"], field + ".keys_i32", 32),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    if result["native_index"] != index:
        raise ValueError(field + " native order disagrees")
    return result


def _condition(value: object, field: str, index: int, stage: dict, first: bool) -> dict:
    raw = _dict(value, field, {"native_index", "key_i32", "admitted", "property_identity", "property_block", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "key_i32": _number(raw["key_i32"], field + ".key_i32", 32),
              "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
              "property_identity": _string(raw["property_identity"], field + ".property_identity", optional=True),
              "property_block": _properties(raw["property_block"], field + ".property_block"),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    if result["native_index"] != index:
        raise ValueError(field + " native order disagrees")
    expected = None if result["key_i32"] is None else _membership(stage, result["key_i32"], first)
    if result["admitted"] != expected:
        raise ValueError(field + " admission disagrees with consumed signed membership")
    if result["admitted"] is not True and (result["property_identity"] is not None or result["property_block"] is not None):
        raise ValueError(field + " contains undemanded conditional PC")
    return result


def _group(value: object, field: str, stage: dict) -> dict:
    raw = _dict(value, field, {"role", "track_index", "level_index", "property_identity", "base_property_block",
                              "conditional_b_count", "conditional_b_rows", "conditional_a_count", "conditional_a_rows",
                              "ready", "reason"})
    result = {"role": _string(raw["role"], field + ".role"),
              "track_index": _number(raw["track_index"], field + ".track_index", 32),
              "level_index": _number(raw["level_index"], field + ".level_index", 32),
              "property_identity": _string(raw["property_identity"], field + ".property_identity", optional=True),
              "base_property_block": _properties(raw["base_property_block"], field + ".base_property_block"),
              "ready": _boolean(raw["ready"], field + ".ready"),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    if result["role"] not in {"base", "growth_level"}:
        raise ValueError(field + " role is invalid")
    if (result["role"] == "base") != (result["track_index"] is None and result["level_index"] is None):
        raise ValueError(field + " growth indices disagree with role")
    complete = result["property_identity"] is not None and _pc_ready(result["base_property_block"])
    for family, first in (("b", False), ("a", True)):
        name = "conditional_" + family
        count = _number(raw[name + "_count"], field + "." + name + "_count", 32)
        rows = raw[name + "_rows"]
        if rows is not None:
            if not isinstance(rows, list):
                raise ValueError(field + "." + name + "_rows must be a list or null")
            rows = [_condition(row, f"{field}.{name}_rows[{i}]", i, stage, first) for i, row in enumerate(rows)]
        result[name + "_count"], result[name + "_rows"] = count, rows
        complete = complete and count is not None and rows is not None and len(rows) == max(0, count)
        if rows is not None:
            complete = complete and all(row["reason"] is None and row["admitted"] is not None
                and (not row["admitted"] or (row["property_identity"] is not None and _pc_ready(row["property_block"])))
                for row in rows)
    complete = complete and result["reason"] is None
    if result["ready"] != complete:
        raise ValueError(field + " group readiness disagrees")
    return result


def _track(value: object, field: str, index: int) -> dict:
    raw = _dict(value, field, {"native_index", "current_value_raw", "level_count", "thresholds_read", "admitted_prefix_count", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "current_value_raw": _number(raw["current_value_raw"], field + ".current_value_raw", 64),
              "level_count": _number(raw["level_count"], field + ".level_count", 32),
              "thresholds_read": _numbers(raw["thresholds_read"], field + ".thresholds_read", 64),
              "admitted_prefix_count": _number(raw["admitted_prefix_count"], field + ".admitted_prefix_count", 32),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    if result["native_index"] != index:
        raise ValueError(field + " native track order disagrees")
    return result


def _side(value: object, field: str, pointer: int | None, stage: dict) -> dict:
    raw = _dict(value, field, {"status", "ready", "map_mask_raw", "map_overflow_raw", "hash_u32", "first_row_index",
                              "probes", "kind_raw", "owner_selection", "property_identity", "property_block", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "map_mask_raw": _number(raw["map_mask_raw"], field + ".map_mask_raw", 32),
              "map_overflow_raw": _number(raw["map_overflow_raw"], field + ".map_overflow_raw", 8, unsigned=True),
              "hash_u32": _number(raw["hash_u32"], field + ".hash_u32", 32, unsigned=True),
              "first_row_index": _number(raw["first_row_index"], field + ".first_row_index", 64),
              "kind_raw": _number(raw["kind_raw"], field + ".kind_raw", 32),
              "owner_selection": _string(raw["owner_selection"], field + ".owner_selection", optional=True),
              "property_identity": _string(raw["property_identity"], field + ".property_identity", optional=True),
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    if not isinstance(raw["probes"], list):
        raise ValueError(field + ".probes must be a list")
    probes = []
    terminal = False
    hit = False
    start, mask, overflow, hash_raw = (result[k] for k in ("first_row_index", "map_mask_raw", "map_overflow_raw", "hash_u32"))
    if hash_raw is not None:
        if pointer is None or hash_raw != _fnv_pointer(pointer) or mask is None or start != (_wrap32(hash_raw) & mask):
            raise ValueError(field + " full pointer hash/index disagrees")
    for i, item in enumerate(raw["probes"]):
        path = f"{field}.probes[{i}]"
        row = _dict(item, path, {"row_index", "distance_u8", "control_u8", "key_pointer_raw", "admitted", "reason"})
        row = {"row_index": _integer(row["row_index"], path + ".row_index", 64),
               "distance_u8": _integer(row["distance_u8"], path + ".distance_u8", 8, unsigned=True),
               "control_u8": _number(row["control_u8"], path + ".control_u8", 8, unsigned=True),
               "key_pointer_raw": _number(row["key_pointer_raw"], path + ".key_pointer_raw", 64, unsigned=True),
               "admitted": _boolean(row["admitted"], path + ".admitted", optional=True),
               "reason": _string(row["reason"], path + ".reason", optional=True)}
        if terminal or start is None or row["row_index"] != start + i or row["distance_u8"] != ((i + 1) & 255):
            raise ValueError(path + " forward native probe order disagrees")
        expected = None if row["control_u8"] is None else row["control_u8"] >= row["distance_u8"]
        if row["admitted"] != expected or (expected is not True and row["key_pointer_raw"] is not None):
            raise ValueError(path + " probe admission disagrees")
        hit = expected is True and row["key_pointer_raw"] == pointer
        terminal = expected is False or hit
        probes.append(row)
    result["probes"] = probes
    complete = (pointer is not None and stage["selector_a_identity"] is not None and hash_raw is not None
                and mask is not None and overflow is not None and terminal and bool(probes)
                and all(row["reason"] is None for row in probes) and result["kind_raw"] is not None)
    end = None if mask is None or overflow is None else _wrap32(mask + overflow + 1)
    native_hit = hit and probes[-1]["row_index"] != end
    if terminal and not native_hit and result["kind_raw"] not in {None, 0}:
        raise ValueError(field + " absent probe must have kind zero")
    if result["kind_raw"] == 0:
        if any(result[k] is not None for k in ("owner_selection", "property_identity", "property_block")):
            raise ValueError(field + " neutral classification contains unused owner PC")
    elif result["kind_raw"] is not None:
        expected_owner = "provider_1620" if result["kind_raw"] == 1 else "provider_1630"
        if result["owner_selection"] not in {None, expected_owner}:
            raise ValueError(field + " owner branch disagrees with signed kind")
        complete = complete and result["owner_selection"] == expected_owner and result["property_identity"] is not None and _pc_ready(result["property_block"])
    complete = complete and reason is None
    if ready != complete:
        raise ValueError(field + " classified-side readiness disagrees")
    return result


def _growth_complete(row: dict, all_ids: list[int]) -> bool:
    flag, tracks, selection = row["growth_flag_raw"], row["track_count_raw"], row["growth_selection"]
    if flag is None:
        return False
    if flag != 0:
        return selection == "empty_character_flag" and row["growth_output_count_raw"] == 0 and not row["growth_tracks"]
    if tracks is None:
        return False
    if tracks <= 0:
        return selection == "empty_track_count" and row["growth_output_count_raw"] == 0 and not row["growth_tracks"]
    definition_id = row["definition_id_raw"]
    if definition_id is None:
        return False
    match = next((i for i, value in enumerate(all_ids) if value == definition_id), None)
    if match is None:
        return selection == "empty_trait_search" and row["growth_output_count_raw"] == 0 and not row["growth_tracks"]
    counts = row["growth_prefix_track_counts"]
    if row["growth_trait_match_index"] != match or counts is None or len(counts) != match:
        return False
    offset = _wrap32(sum(counts))
    aux = row["growth_aux_count_raw"]
    if row["growth_prefix_offset_raw"] != offset or aux is None:
        return False
    if offset >= aux:
        return selection == "empty_aux_range" and row["growth_output_count_raw"] == 0 and not row["growth_tracks"]
    output_count = min(tracks, _wrap32(aux - offset))
    if row["growth_output_count_raw"] != output_count:
        return False
    if output_count == 0:
        return selection == "empty_header_count" and not row["growth_tracks"]
    if selection != "current_consumed_growth" or len(row["growth_tracks"]) != tracks:
        return False
    groups = []
    for track in row["growth_tracks"]:
        value, count, thresholds, prefix = (track[k] for k in ("current_value_raw", "level_count", "thresholds_read", "admitted_prefix_count"))
        if value is None or track["reason"] is not None:
            return False
        if value <= 0:
            if count is not None or thresholds is not None or prefix is not None:
                return False
            continue
        if count is None or count < 0 or thresholds is None or prefix is None or not 0 <= prefix <= count:
            return False
        if len(thresholds) != prefix + (prefix < count) or any(t > value for t in thresholds[:prefix]):
            return False
        if prefix < count and thresholds[-1] <= value:
            return False
        groups.extend((track["native_index"], level) for level in range(prefix))
    return [(group["track_index"], group["level_index"]) for group in row["composite_groups"][1:]] == groups


def _row(value: object, field: str, index: int, stage: dict, all_ids: list[int]) -> dict:
    words = ("definition_id_raw", "track_count_raw", "growth_trait_match_index", "growth_prefix_offset_raw", "growth_aux_count_raw", "growth_output_count_raw")
    raw = _dict(value, field, {"native_index", "trait_id_raw", "definition_selection", "definition_identity", "definition_pointer_raw",
                              "composite_ready", "composite_groups", "growth_flag_raw", *words, "growth_prefix_track_counts",
                              "growth_tracks", "growth_selection", "composite_reason", "side", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "trait_id_raw": _integer(raw["trait_id_raw"], field + ".trait_id_raw", 32),
              "definition_selection": _string(raw["definition_selection"], field + ".definition_selection", optional=True),
              "definition_identity": _string(raw["definition_identity"], field + ".definition_identity", optional=True),
              "definition_pointer_raw": _number(raw["definition_pointer_raw"], field + ".definition_pointer_raw", 64, unsigned=True),
              "composite_ready": _boolean(raw["composite_ready"], field + ".composite_ready"),
              "growth_flag_raw": _number(raw["growth_flag_raw"], field + ".growth_flag_raw", 8, unsigned=True),
              "growth_prefix_track_counts": _numbers(raw["growth_prefix_track_counts"], field + ".growth_prefix_track_counts", 32),
              "growth_selection": raw["growth_selection"],
              "composite_reason": _string(raw["composite_reason"], field + ".composite_reason", optional=True),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    for word in words:
        result[word] = _number(raw[word], field + "." + word, 32)
    if result["native_index"] != index or type(result["growth_selection"]) is not str or result["growth_selection"] not in {
        "", "empty_character_flag", "empty_track_count", "empty_trait_search", "empty_aux_range", "empty_header_count", "current_consumed_growth"
    }:
        raise ValueError(field + " native order or growth selection disagrees")
    if result["definition_selection"] not in {None, "indexed_trait_database", "native_trait_definition_fallback"}:
        raise ValueError(field + " definition source is invalid")
    for key in ("composite_groups", "growth_tracks"):
        if not isinstance(raw[key], list):
            raise ValueError(field + "." + key + " must be a list")
    result["composite_groups"] = [_group(group, f"{field}.composite_groups[{i}]", stage) for i, group in enumerate(raw["composite_groups"])]
    result["growth_tracks"] = [_track(track, f"{field}.growth_tracks[{i}]", i) for i, track in enumerate(raw["growth_tracks"])]
    result["side"] = _side(raw["side"], field + ".side", result["definition_pointer_raw"], stage)
    groups = result["composite_groups"]
    complete = (result["definition_identity"] is not None and result["definition_pointer_raw"] is not None
                and result["definition_selection"] is not None and bool(groups) and groups[0]["role"] == "base"
                and all(group["role"] == "growth_level" for group in groups[1:]) and all(group["ready"] for group in groups)
                and _growth_complete(result, all_ids) and result["composite_reason"] is None)
    if result["composite_ready"] != complete:
        raise ValueError(field + " full composite readiness disagrees")
    if (result["reason"] is None) != (complete and result["side"]["ready"]):
        raise ValueError(field + " trait readiness disagrees")
    return result


def normalize_trait_stage_291d460(value: object, field: str = "current_context_source_inputs.trait_stage_291d460") -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {"status", "ready", "character_id", "trait_count", "trait_array_present", "rows",
                              *_TOP_STRINGS, *_TOP_WORDS, *_TOP_ARRAYS, "selector_b_nested_keys", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "character_id": _integer(raw["character_id"], field + ".character_id", 32),
              "trait_count": _number(raw["trait_count"], field + ".trait_count", 32),
              "trait_array_present": _boolean(raw["trait_array_present"], field + ".trait_array_present", optional=True)}
    for key in _TOP_STRINGS:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in _TOP_WORDS:
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in _TOP_ARRAYS:
        result[key] = _numbers(raw[key], field + "." + key, 32)
    nested = raw["selector_b_nested_keys"]
    if nested is not None:
        if not isinstance(nested, list):
            raise ValueError(field + ".selector_b_nested_keys must be a list or null")
        nested = [_keyset(keys, f"{field}.selector_b_nested_keys[{i}]", i) for i, keys in enumerate(nested)]
        if result["selector_b_nested_count"] is None or len(nested) > max(0, result["selector_b_nested_count"]):
            raise ValueError(field + " nested keyset count disagrees")
    result["selector_b_nested_keys"] = nested
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        all_ids = [_integer(_dict(row, f"{field}.rows[{i}]", set(row))["trait_id_raw"], f"{field}.rows[{i}].trait_id_raw", 32) for i, row in enumerate(rows)]
        rows = [_row(row, f"{field}.rows[{i}]", i, result, all_ids) for i, row in enumerate(rows)]
    result["rows"] = rows
    count = result["trait_count"]
    complete = (count is not None and count >= 0 and rows is not None and len(rows) == count
                and (count == 0 or result["trait_array_present"] is True)
                and all(row["composite_ready"] and row["side"]["ready"] and row["reason"] is None for row in rows)
                and reason is None)
    if ready != complete:
        raise ValueError(field + " full D460 readiness disagrees")
    return result


def _current(section: dict | None) -> dict:
    if not isinstance(section, dict) or _FIELD not in section:
        raise ValueError("Required native input unavailable: " + _FIELD)
    value = normalize_trait_stage_291d460(section[_FIELD])
    if value is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if value["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return value


def _composite_block(row: dict) -> dict:
    from ..simulation.battle_trait_materialized_prefix_12003 import _fold_property_request
    keys, values, updates = [], [], []
    for group in row["composite_groups"]:
        blocks = [group["base_property_block"]]
        blocks.extend(condition["property_block"] for family in ("conditional_b_rows", "conditional_a_rows")
                      for condition in group[family] if condition["admitted"])
        for block in blocks:
            count = block["keys_count"]
            if count:
                _fold_property_request(keys, values, tuple(block["keys_u16"][:count]),
                                       tuple(block["values_q64"][:count]), 100000, {}, updates)
    return {"keys_count": len(keys), "values_count": len(values), "keys_u16": keys, "values_q64": values, "reason": None}


def _request(row: dict, source: str, identity: str, block: dict):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return NativeWeightedContributionRequest12003(source_ordinal=row["native_index"], source_name=source,
        first_row_index=row["native_index"], row_count=1, definition_identity=identity,
        base_property_block=block, weight_q64=100000)


def emit_trait_291d460_family_requests_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    """Retain one independently complete composite/side family in a partial stage."""
    if family not in {"composite", "side"}:
        raise ValueError("Unknown trait291D460 family")
    stage = _current(section)
    if stage["rows"] is None or stage["trait_count"] is None or len(stage["rows"]) != stage["trait_count"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    requests = []
    for row in stage["rows"]:
        if family == "composite":
            if not row["composite_ready"]:
                raise ValueError("Required native input unavailable: trait291D460.composite")
            block = _composite_block(row)
            if block["keys_count"]:
                requests.append(_request(row, "291d460_trait_composite", row["definition_identity"], block))
        else:
            side = row["side"]
            if not side["ready"]:
                raise ValueError("Required native input unavailable: trait291D460.side")
            if side["kind_raw"] != 0 and side["property_block"]["keys_count"]:
                requests.append(_request(row, "291d460_classified_owner", side["property_identity"], side["property_block"]))
    return tuple(requests)


def emit_trait_291d460_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Fold full current composites, then emit each same-trait side occurrence."""
    stage = _current(section)
    if not stage["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    requests = []
    for row in stage["rows"]:
        composite = _composite_block(row)
        if composite["keys_count"]:
            requests.append(_request(row, "291d460_trait_composite", row["definition_identity"], composite))
        side = row["side"]
        if side["kind_raw"] != 0 and side["property_block"]["keys_count"]:
            requests.append(_request(row, "291d460_classified_owner", side["property_identity"], side["property_block"]))
    return tuple(requests)
