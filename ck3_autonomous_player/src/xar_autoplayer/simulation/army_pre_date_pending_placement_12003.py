"""Exact record28 pending placement on a private same-capture physical image.

Native allocation/initialization is never called. Growth creates a sparse
logical image, then consumes the old occupied count in physical order.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, Mapping


class PendingPlacementUnavailable(Exception):
    """An actual demanded operand or supported normal-return branch is absent."""


def _i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _require(value, reason: str):
    if value is None:
        raise PendingPlacementUnavailable(reason)
    return value


def _empty_vector() -> dict:
    return {"count": 0, "values": [], "allocator_matches": True}


def create_pending_placement_state(frame: Mapping) -> dict:
    records = {}
    for row in frame["records"]:
        refs = row["references"]
        records[row["physical_slot_i64"]] = {
            "control": row["control_raw_u8"], "hash": row["stored_hash_raw_u32"],
            "key": row["key_raw_full_id_u32"],
            "vector": {"count": refs["count_raw_i32"],
                       "values": [r["raw_full_id_u32"] for r in refs["occurrences"]] if refs["references_ready"] else None,
                       "allocator_matches": row["vector_allocator_matches_expected"]},
        }
    return {"entries_present": frame["entries_present"], "initial_entries_identity": frame["entries_identity"],
            "data_is_empty": frame["data_is_native_empty_buffer"], "mask": frame["mask_raw_i32"],
            "count": frame["map_count_raw_i32"], "tail": frame["tail_raw_u8"],
            "threshold": frame["threshold_bits_u32"], "records": records,
            "generated": False, "terminal": frame["physical_control_extent_last_slot_i64"],
            "events": [], "placement_invocations": 0, "changed_keys": set()}


def _at(state: dict, slot: int) -> dict:
    if slot in state["records"]:
        record = state["records"][slot]
    elif state["generated"] and 0 <= slot <= state["terminal"]:
        record = {"control": 255 if slot == state["terminal"] else 0,
                  "hash": None, "key": None, "vector": {"count": None, "values": None, "allocator_matches": None}}
        state["records"][slot] = record
    else:
        raise PendingPlacementUnavailable("pending_physical_control_unobserved")
    _require(record["control"], "pending_physical_control_unavailable")
    return record


def _movable(record: Mapping) -> dict:
    _require(record["hash"], "pending_carried_stored_hash_unavailable")
    _require(record["key"], "pending_carried_key_unavailable")
    if record["vector"]["allocator_matches"] is not True:
        raise PendingPlacementUnavailable("pending_required_vector_transfer_unmatched_or_unread")
    return deepcopy(record)


def _incoming(hash_raw: int, key: int, vector: Mapping, control: int) -> dict:
    if vector["allocator_matches"] is not True:
        raise PendingPlacementUnavailable("pending_required_vector_transfer_unmatched_or_unread")
    return {"hash": hash_raw, "key": key, "control": control, "vector": deepcopy(vector)}


def _growth_index(mask: int) -> int:
    size = _i32(mask + 1)
    return 3 if size <= 1 else max(3, (size - 1).bit_length() + 1)


def _grow(state: dict, density_exceeds: Callable, trigger: str) -> None:
    mask = _require(state["mask"], "pending_insertion_mask_unavailable")
    count = _require(state["count"], "pending_insertion_count_unavailable")
    index = _growth_index(mask)
    if index >= 31:
        raise PendingPlacementUnavailable("pending_native_growth_index_nonreturn_boundary")
    if count > 0:
        old_is_empty = _require(state["data_is_empty"], "pending_old_data_sentinel_equality_unavailable")
    else:
        old_is_empty = True
    old = deepcopy(state)
    capacity, tail = 1 << index, (index + 2) & 255
    event = {"kind": "growth", "trigger": trigger, "index": index,
             "mask_before": mask, "count_before": count, "capacity": capacity,
             "mask_after": capacity - 1, "tail_after": tail, "allocated_records": capacity + tail + 1,
             "terminal_slot": capacity + tail, "old_rehash_occurrences": []}
    state.update(mask=capacity - 1, count=0, tail=tail, records={}, generated=True,
                 terminal=capacity + tail, data_is_empty=False)
    state["events"].append(event)
    if count <= 0 or old_is_empty:
        return
    remaining, slot = count, 0
    while remaining > 0:
        record = _at(old, slot)
        if record["control"] != 0:
            stored_hash = _require(record["hash"], "pending_rehash_stored_hash_unavailable")
            key = _require(record["key"], "pending_rehash_key_unavailable")
            selected = _insert(state, stored_hash, key, record["vector"], density_exceeds)
            state["changed_keys"].add(key)
            event["old_rehash_occurrences"].append({"physical_slot_i64": slot,
                "stored_hash_raw_u32": stored_hash, "key_raw_full_id_u32": key,
                "selected_slot_i64": selected["slot"], "inserted": selected["inserted"]})
            remaining -= 1
        slot += 1


def _insert(state: dict, hash_raw: int, key: int, vector: Mapping, density_exceeds: Callable) -> dict:
    mask = _require(state["mask"], "pending_insertion_mask_unavailable")
    slot, distance = _i32(hash_raw & (mask & 0xFFFFFFFF)), 1
    while True:
        record = _at(state, slot)
        control = record["control"]
        if control < distance:
            break
        if _require(record["key"], "pending_probe_key_unavailable") == key:
            return {"slot": slot, "record": record, "inserted": False, "branch": "existing_key"}
        slot += 1
        distance = (distance + 1) & 255
    tail = _require(state["tail"], "pending_insertion_tail_unavailable")
    count = _require(state["count"], "pending_insertion_count_unavailable")
    threshold = _require(state["threshold"], "pending_insertion_threshold_unavailable")
    if distance > tail or density_exceeds(count, mask, threshold):
        _grow(state, density_exceeds, "initial_growth")
        selected = _insert(state, hash_raw, key, vector, density_exceeds)
        selected["branch"] = "initial_growth"
        return selected
    if control == 0:
        state["records"][slot] = _incoming(hash_raw, key, vector, distance)
        state["changed_keys"].add(key)
        state["count"] = _i32(count + 1)
        state["events"].append({"kind": "direct_empty", "slot": slot, "key": key})
        return {"slot": slot, "record": state["records"][slot], "inserted": True, "branch": "direct_empty"}
    carried_control = (control + 1) & 255
    next_record = _at(state, slot + 1)
    resident = _movable(record)
    state["changed_keys"].update((key, resident["key"]))
    resident["control"] = carried_control
    if next_record["control"] == 0:
        state["records"][slot + 1] = resident
        state["records"][slot] = _incoming(hash_raw, key, vector, distance)
        state["count"] = _i32(count + 1)
        state["events"].append({"kind": "fast_shift", "slot": slot, "moved_to": slot + 1, "key": key})
        return {"slot": slot, "record": state["records"][slot], "inserted": True, "branch": "fast_shift"}
    first_slot = slot
    state["records"][slot] = _incoming(hash_raw, key, vector, distance)
    carried = resident
    state["events"].append({"kind": "carry_start", "slot": slot, "key": key})
    while True:
        slot += 1
        record = _at(state, slot)
        control = record["control"]
        if control == 0:
            state["records"][slot] = carried
            state["count"] = _i32(state["count"] + 1)
            state["events"].append({"kind": "carry_empty", "slot": slot, "selected_slot": first_slot})
            return {"slot": first_slot, "record": state["records"][first_slot], "inserted": True,
                    "branch": "general_carried_collision"}
        if control < carried["control"]:
            displaced = _movable(record)
            state["changed_keys"].add(displaced["key"])
            state["records"][slot] = carried
            carried = displaced
            carried["control"] = (control + 1) & 255
            state["events"].append({"kind": "lower_distance_swap", "slot": slot,
                "reloaded_control": control, "carried_control_after": carried["control"], "tail_test": False})
            continue
        carried["control"] = (carried["control"] + 1) & 255
        if carried["control"] <= state["tail"]:
            continue
        original = _movable(state["records"][first_slot])
        state["records"][first_slot] = carried
        carried = original
        state["events"].append({"kind": "carried_overflow_first_slot_exchange", "slot": first_slot})
        _grow(state, density_exceeds, "carried_overflow")
        selected = _insert(state, carried["hash"], carried["key"], carried["vector"], density_exceeds)
        selected["branch"] = "carried_growth"
        return selected


def select_or_insert_pending_record28(state: dict, *, full_id_u32: int, hash_raw_u32: int,
                                      density_exceeds: Callable) -> dict:
    """One top-level placement; recursion is actual growth/reinsertion only."""
    if state["entries_present"] is not True:
        raise PendingPlacementUnavailable("pending_map_header_unavailable")
    state["placement_invocations"] += 1
    return _insert(state, hash_raw_u32, full_id_u32, _empty_vector(), density_exceeds)


def project_pending_placement_state(state: dict) -> dict:
    records = [{"physical_slot_i64": slot, "control_raw_u8": record["control"],
                "stored_hash_raw_u32": record["hash"], "key_raw_full_id_u32": record["key"],
                "conditional_count_raw_i32": record["vector"]["count"] if record["control"] else None,
                "conditional_full_ids_u32": record["vector"]["values"] if record["control"] else None,
                "physically_changed": record["key"] in state["changed_keys"]}
               for slot, record in sorted(state["records"].items())]
    return {"source": "same_input_conditional_pending_record28_placement_v1",
            "mask_raw_i32": state["mask"], "conditional_map_count_raw_i32": state["count"],
            "tail_raw_u8": state["tail"], "threshold_bits_u32": state["threshold"],
            "sparse_generated_image": state["generated"], "default_control_raw_u8": 0 if state["generated"] else None,
            "terminal_slot_i64": state["terminal"], "terminal_control_raw_u8": 255 if state["generated"] else None,
            "physical_records": records, "events": deepcopy(state["events"]),
            "placement_invocations": state["placement_invocations"], "native_writes": 0,
            "native_mutator_invocations": 0, "actual_native_after_ready": False}
