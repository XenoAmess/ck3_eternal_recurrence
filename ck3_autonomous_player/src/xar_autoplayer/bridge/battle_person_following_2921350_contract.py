"""Strict actual Title/Province/map/tier source inputs for following2921350."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _numbers, _string,
)
from .battle_person_after_gated_tail_contract import _pc, _pc_ready
from ..simulation.battle_person_following_2921350_12003 import (
    emit_following_2921350_requests_12003, emit_following_2921350_group_requests_12003,
    following_2921350_group_results_12003, following_2921350_fnv1a_12003,
    following_2921350_tier_index_12003,
)
from ..simulation.battle_trait_numeric_inputs_12003 import native_wrap32_12003

_FIELD = "following_2921350"


def _record(value, field, fields, *, availability=False):
    raw = _dict(value, field, {*fields, "reason", *(('status', 'ready') if availability else ())})
    out = {"reason": _string(raw["reason"], field + ".reason", optional=True)}
    if availability:
        status, ready, reason = _availability(raw, field)
        out.update(status=status, ready=ready, reason=reason)
    return raw, out


def _words(raw, out, field, keys, bits=32, unsigned=False):
    for key in keys:
        out[key] = _number(raw[key], field + "." + key, bits, unsigned=unsigned)


def _strings(raw, out, field, keys):
    for key in keys:
        out[key] = _string(raw[key], field + "." + key, optional=True)


def _bools(raw, out, field, keys):
    for key in keys:
        out[key] = _boolean(raw[key], field + "." + key, optional=True)


def _list(value, field):
    if not isinstance(value, list):
        raise ValueError(field + " must be a list")
    return value


def _readiness(out, complete, field):
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " actual input readiness disagrees")


def _ids_complete(count, present, ids, field):
    if count is None or count < 0:
        if ids is not None:
            raise ValueError(field + " missing/negative count cannot become an empty stream")
        return False
    if count == 0:
        if present is not None or ids != []:
            raise ValueError(field + " count0 must avoid undemanded array reads")
        return True
    if ids is not None and len(ids) != count:
        raise ValueError(field + " IDs disagree with full signed count")
    return present is True and ids is not None


def _resolution(out, field):
    selection = out["selection"]
    if selection not in {None, "registry_full_id", "native_fallback"}:
        raise ValueError(field + " actual full-ID resolution invalid")
    if selection == "registry_full_id" and (
        out["requested_full_id_u32"] is None
        or out["selected_full_id_u32"] != out["requested_full_id_u32"]
    ):
        raise ValueError(field + " full-generation comparator disagrees")
    if selection != "registry_full_id" and out["selected_full_id_u32"] is not None:
        raise ValueError(field + " fallback contains an indexed selected ID")
    return selection is not None


def _title_source(value, field):
    raw, out = _record(value, field, {"carrier_present", "selection", "header_identity", "count_raw",
                                    "array_present", "full_ids_u32"}, availability=True)
    _strings(raw, out, field, ("selection", "header_identity"))
    _bools(raw, out, field, ("carrier_present", "array_present"))
    _words(raw, out, field, ("count_raw",))
    out["full_ids_u32"] = _numbers(raw["full_ids_u32"], field + ".full_ids_u32", 32, unsigned=True)
    selected = ("current_1c0_1e0" if out["carrier_present"] is True else
                "actual_default_5459c88" if out["carrier_present"] is False else None)
    if out["selection"] != selected:
        raise ValueError(field + " current/default Title header selection disagrees")
    complete = _ids_complete(out["count_raw"], out["array_present"], out["full_ids_u32"], field)
    _readiness(out, complete and out["header_identity"] is not None and selected is not None, field)
    return out


def _title_walk(values, field, source):
    pending = [(i, None, key) for i, key in reversed(list(enumerate(source["full_ids_u32"] or [])))]
    seen, rows, collected = set(), [], []
    complete = source["ready"]
    for i, value in enumerate(_list(values, field)):
        name = f"{field}[{i}]"
        raw, out = _record(value, name, {"native_index", "root_index", "parent_index", "requested_full_id_u32",
            "selection", "selected_full_id_u32", "title_identity", "definition_identity", "tier_raw_i32",
            "children_count_raw", "children_array_present", "child_ids_u32", "collected"})
        for key in ("native_index", "root_index"):
            out[key] = _integer(raw[key], name + "." + key, 32)
        _words(raw, out, name, ("parent_index", "tier_raw_i32", "children_count_raw"))
        _words(raw, out, name, ("requested_full_id_u32", "selected_full_id_u32"), unsigned=True)
        _strings(raw, out, name, ("selection", "title_identity", "definition_identity"))
        _bools(raw, out, name, ("children_array_present", "collected"))
        out["child_ids_u32"] = _numbers(raw["child_ids_u32"], name + ".child_ids_u32", 32, unsigned=True)
        if out["native_index"] != i or not pending or not complete:
            raise ValueError(name + " rows must retain the actual demanded DFS prefix")
        if (out["root_index"], out["parent_index"], out["requested_full_id_u32"]) != pending.pop():
            raise ValueError(name + " DFS occurrence/order disagrees")
        resolved = _resolution(out, name)
        tier, identity = out["tier_raw_i32"], out["title_identity"]
        row_complete = resolved and identity is not None and out["definition_identity"] is not None and tier is not None
        expected = None
        if row_complete:
            if tier > 1:
                row_complete = _ids_complete(out["children_count_raw"], out["children_array_present"], out["child_ids_u32"], name)
                if row_complete:
                    pending.extend((out["root_index"], i, key) for key in reversed(out["child_ids_u32"]))
                expected = False
            else:
                if any(out[key] is not None for key in ("children_count_raw", "children_array_present", "child_ids_u32")):
                    raise ValueError(name + " non-parent Title contains undemanded children")
                expected = tier == 1 and identity not in seen
                if tier == 1:
                    seen.add(identity)
                if expected:
                    collected.append(i)
        if out["collected"] != expected:
            raise ValueError(name + " first full-pointer Title dedup disagrees")
        complete = complete and row_complete and out["reason"] is None
        rows.append(out)
    return rows, collected, complete and not pending


def _map(value, field, province_id):
    raw, out = _record(value, field, {"data_identity", "mask_raw_i32", "overflow_raw_u8", "probes", "found", "operand_q64"}, availability=True)
    _strings(raw, out, field, ("data_identity",))
    _words(raw, out, field, ("mask_raw_i32",))
    _words(raw, out, field, ("overflow_raw_u8",), 8, True)
    _words(raw, out, field, ("operand_q64",), 64)
    _bools(raw, out, field, ("found",))
    mask, overflow = out["mask_raw_i32"], out["overflow_raw_u8"]
    bucket = None if mask is None else native_wrap32_12003(following_2921350_fnv1a_12003(province_id)) & mask
    end = None if mask is None or overflow is None else mask + 1 + overflow
    rows, found, operand = [], None, None
    for i, value in enumerate(_list(raw["probes"], field + ".probes")):
        name = f"{field}.probes[{i}]"
        item, row = _record(value, name, {"native_index", "bucket_index_i64", "distance_raw_u8", "key_raw_u32", "operand_q64"})
        row["native_index"] = _integer(item["native_index"], name + ".native_index", 32)
        _words(item, row, name, ("bucket_index_i64", "operand_q64"), 64)
        _words(item, row, name, ("distance_raw_u8",), 8, True)
        _words(item, row, name, ("key_raw_u32",), 32, True)
        if bucket is None or found is not None or row["native_index"] != i or row["bucket_index_i64"] != bucket + i:
            raise ValueError(name + " physical FNV probe order disagrees")
        distance = row["distance_raw_u8"]
        if distance is not None and distance < ((i + 1) & 0xFF):
            if row["key_raw_u32"] is not None or row["operand_q64"] is not None:
                raise ValueError(name + " terminating distance contains undemanded key/payload")
            found, operand = False, 0
        elif distance is not None and row["key_raw_u32"] == province_id:
            found = row["bucket_index_i64"] != end if end is not None else None
            operand = row["operand_q64"] if found else 0 if found is False else None
            if found is False and row["operand_q64"] is not None:
                raise ValueError(name + " end bucket contains undemanded payload")
        elif row["operand_q64"] is not None:
            raise ValueError(name + " unmatched bucket contains undemanded operand")
        if row["reason"] is not None or distance is None or (distance >= ((i + 1) & 0xFF) and row["key_raw_u32"] is None):
            if i != len(raw["probes"]) - 1:
                raise ValueError(name + " probe continues after unread input")
        rows.append(row)
    out["probes"] = rows
    if (out["found"], out["operand_q64"]) != (found, operand):
        raise ValueError(field + " found/actual absent0 operand disagrees")
    complete = out["data_identity"] is not None and mask is not None and overflow is not None
    complete = complete and found is not None and operand is not None and all(row["reason"] is None for row in rows)
    _readiness(out, complete, field)
    return out


def _tiers(value, field, operand):
    raw, out = _record(value, field, {"count_raw_i32", "data_identity", "thresholds_q64", "selected_index_raw_i32",
        "selection", "default_guard_raw_i32", "pc"}, availability=True)
    _words(raw, out, field, ("count_raw_i32", "selected_index_raw_i32", "default_guard_raw_i32"))
    _strings(raw, out, field, ("data_identity", "selection"))
    out["thresholds_q64"] = _numbers(raw["thresholds_q64"], field + ".thresholds_q64", 64)
    out["pc"] = _pc(raw["pc"], field + ".pc")
    count, thresholds = out["count_raw_i32"], out["thresholds_q64"]
    if count is not None and count <= 0 and (thresholds != [] or out["data_identity"] is not None):
        raise ValueError(field + " nonpositive count contains undemanded tier data")
    if count is not None and count > 0 and thresholds is not None:
        if len(thresholds) > count:
            raise ValueError(field + " thresholds exceed stored count")
        first = next((i for i, threshold in enumerate(thresholds) if operand is not None and operand < threshold), None)
        if first is not None and first != len(thresholds) - 1:
            raise ValueError(field + " threshold scan continues after strict greater")
    index = following_2921350_tier_index_12003(count, thresholds, operand)
    if out["selected_index_raw_i32"] != index:
        raise ValueError(field + " ordinal minus1/equality tier selection disagrees")
    selection = None
    if index is not None:
        if 0 <= index < count:
            selection = "indexed_tier"
            if out["default_guard_raw_i32"] is not None:
                raise ValueError(field + " valid tier contains undemanded fallback guard")
        elif out["default_guard_raw_i32"] is not None:
            selection = ("cold_default_5d65b00" if out["default_guard_raw_i32"] in {0, -1}
                         else "initialized_default_5d65b00")
    if out["selection"] != selection:
        raise ValueError(field + " selected actual tier/default route disagrees")
    if selection == "cold_default_5d65b00":
        if out["reason"] != "tier_default_2560620_result" or any(out["pc"][key] is not None for key in ("property_identity", "property_block")):
            raise ValueError(field + " demanded cold fallback cannot fabricate an empty PC")
    selector_complete = index is not None and (count <= 0 or out["data_identity"] is not None)
    _readiness(out, selector_complete and selection in {"indexed_tier", "initialized_default_5d65b00"} and _pc_ready(out["pc"]), field)
    return out


def _source(value, field, index, requested, province_id):
    raw, out = _record(value, field, {"native_index", "requested_full_id_u32", "selection", "selected_full_id_u32",
        "object_identity", "definition_identity", "group_index_raw_i32", "map", "tiers"})
    out["native_index"] = _integer(raw["native_index"], field + ".native_index", 32)
    _words(raw, out, field, ("requested_full_id_u32", "selected_full_id_u32"), unsigned=True)
    _words(raw, out, field, ("group_index_raw_i32",))
    _strings(raw, out, field, ("selection", "object_identity", "definition_identity"))
    if out["native_index"] != index or out["requested_full_id_u32"] != requested:
        raise ValueError(field + " ordered fullDWORD source occurrence disagrees")
    _resolution(out, field)
    out["map"] = _map(raw["map"], field + ".map", province_id)
    out["tiers"] = _tiers(raw["tiers"], field + ".tiers", out["map"]["operand_q64"] if out["map"]["ready"] else None)
    return out


def _province(value, field, index, title_index, walk):
    raw, out = _record(value, field, {"native_index", "title_walk_index", "steps", "province_identity", "magic_u32",
        "admitted", "full_id_u32", "source_count_raw", "source_array_present", "source_ids_u32", "sources"})
    for key in ("native_index", "title_walk_index"):
        out[key] = _integer(raw[key], field + "." + key, 32)
    if out["native_index"] != index or out["title_walk_index"] != title_index:
        raise ValueError(field + " collected Title/Province occurrence order disagrees")
    _strings(raw, out, field, ("province_identity",))
    _words(raw, out, field, ("magic_u32", "full_id_u32"), unsigned=True)
    _words(raw, out, field, ("source_count_raw",))
    _bools(raw, out, field, ("admitted", "source_array_present"))
    out["source_ids_u32"] = _numbers(raw["source_ids_u32"], field + ".source_ids_u32", 32, unsigned=True)
    steps, done = [], False
    previous_id = None
    for i, value in enumerate(_list(raw["steps"], field + ".steps")):
        name = f"{field}.steps[{i}]"
        item, step = _record(value, name, {"native_index", "title_identity", "definition_identity", "tier_raw_i32",
            "requested_full_id_u32", "selection", "selected_full_id_u32", "first_child_count_raw", "first_child_array_present", "first_child_full_id_u32"})
        step["native_index"] = _integer(item["native_index"], name + ".native_index", 32)
        _strings(item, step, name, ("title_identity", "definition_identity", "selection"))
        _words(item, step, name, ("tier_raw_i32", "first_child_count_raw"))
        _words(item, step, name, ("requested_full_id_u32", "selected_full_id_u32", "first_child_full_id_u32"), unsigned=True)
        _bools(item, step, name, ("first_child_array_present",))
        if step["native_index"] != i or done or step["requested_full_id_u32"] != previous_id:
            raise ValueError(name + "230F900 first-child trace disagrees")
        if i == 0:
            if step["title_identity"] != walk[title_index]["title_identity"] or step["selection"] is not None or step["selected_full_id_u32"] is not None:
                raise ValueError(name + "230F900 starts on a different collected pointer")
        else:
            _resolution(step, name)
        if step["tier_raw_i32"] == 2:
            count = step["first_child_count_raw"]
            if count == 0 and (step["first_child_full_id_u32"] != 0xFFFFFFFF or step["first_child_array_present"] is not None):
                raise ValueError(name + " empty first-child header must resolve fullFFFFFFFF")
            previous_id = step["first_child_full_id_u32"]
        elif step["tier_raw_i32"] is not None:
            done = True
            if any(step[key] is not None for key in ("first_child_count_raw", "first_child_array_present", "first_child_full_id_u32")):
                raise ValueError(name + " non-tier2 contains undemanded first child")
        if step["reason"] is not None and i != len(raw["steps"]) - 1:
            raise ValueError(name + " Province selection continues after unread input")
        steps.append(step)
    out["steps"] = steps
    admitted = None if out["magic_u32"] is None else out["magic_u32"] == 0x50726F76
    if out["admitted"] != admitted:
        raise ValueError(field + " actual Prov magic admission disagrees")
    ids = out["source_ids_u32"]
    if admitted is False:
        if any(out[key] is not None for key in ("full_id_u32", "source_count_raw", "source_array_present", "source_ids_u32")) or raw["sources"]:
            raise ValueError(field + " rejected Province contains undemanded numerical sources")
    elif admitted is True:
        _ids_complete(out["source_count_raw"], out["source_array_present"], ids, field)
    values = _list(raw["sources"], field + ".sources")
    if values and (ids is None or out["full_id_u32"] is None) or ids is not None and len(values) > len(ids):
        raise ValueError(field + " sources lack ordered source IDs/Province full ID")
    out["sources"] = [_source(value, f"{field}.sources[{i}]", i, ids[i], out["full_id_u32"]) for i, value in enumerate(values)]
    return out


def normalize_following_2921350(value, field=_FIELD):
    if value is None:
        return None
    raw, out = _record(value, field, {"character_id", "character_identity", "source_scope", "title_source", "title_walk", "provinces", "manager"}, availability=True)
    out["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    _strings(raw, out, field, ("character_identity", "source_scope"))
    if out["source_scope"] != "held_current_native_inputs":
        raise ValueError(field + " cannot rename held-current inputs as fresh stage observation")
    out["title_source"] = _title_source(raw["title_source"], field + ".title_source")
    walk, collected, stream_complete = _title_walk(raw["title_walk"], field + ".title_walk", out["title_source"])
    out["title_walk"] = walk
    provinces = _list(raw["provinces"], field + ".provinces")
    if len(provinces) > len(collected):
        raise ValueError(field + " Province rows exceed collected Title pointers")
    out["provinces"] = [_province(value, f"{field}.provinces[{i}]", i, collected[i], walk) for i, value in enumerate(provinces)]
    item, manager = _record(raw["manager"], field + ".manager", {"loaded", "identity", "group_count_raw_i32"}, availability=True)
    _strings(item, manager, field, ("identity",))
    _bools(item, manager, field, ("loaded",))
    _words(item, manager, field, ("group_count_raw_i32",))
    group_count = manager["group_count_raw_i32"]
    manager_complete = manager["loaded"] is True and manager["identity"] is not None and group_count is not None and group_count >= 0
    if manager["loaded"] is False and (manager["identity"] is not None or group_count is not None):
        raise ValueError(field + " null manager cannot supply numerical group dimension")
    _readiness(manager, manager_complete, field + ".manager")
    out["manager"] = manager
    complete = stream_complete and len(provinces) == len(collected) and manager["ready"] and out["character_identity"] is not None
    for province in out["provinces"]:
        complete = complete and province["reason"] is None and all(step["reason"] is None for step in province["steps"])
        complete = complete and bool(province["steps"]) and province["steps"][-1]["tier_raw_i32"] is not None and province["steps"][-1]["tier_raw_i32"] != 2
        complete = complete and province["province_identity"] is not None and province["admitted"] is not None
        if province["admitted"] is True:
            n, ids = province["source_count_raw"], province["source_ids_u32"]
            complete = complete and province["full_id_u32"] is not None and n is not None and n >= 0 and ids is not None and len(province["sources"]) == n
            for source in province["sources"]:
                index = source["group_index_raw_i32"]
                complete = complete and source["reason"] is None and source["selection"] is not None and source["object_identity"] is not None and source["definition_identity"] is not None
                complete = complete and index is not None and group_count is not None and 0 <= index < group_count and source["map"]["ready"] and source["tiers"]["ready"]
    _readiness(out, complete, field)
    return out


def emit_following_2921350_requests_from_current_source_inputs_12003(section):
    leaf = normalize_following_2921350(None if section is None else section.get(_FIELD))
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return emit_following_2921350_requests_12003(leaf)


def emit_following_2921350_group_requests_from_current_source_inputs_12003(section, group_index):
    leaf = normalize_following_2921350(None if section is None else section.get(_FIELD))
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    groups = following_2921350_group_results_12003(leaf)
    index = _integer(group_index, _FIELD + ".group_index", 32)
    if not 0 <= index < len(groups):
        raise ValueError(_FIELD + " group index outside actual manager dimension")
    return emit_following_2921350_group_requests_12003(leaf, groups[index])
