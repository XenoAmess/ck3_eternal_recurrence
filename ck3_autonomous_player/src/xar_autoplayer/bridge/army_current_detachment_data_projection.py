"""Pure source-ordered 2633FF0 DATA prefix, independent for every incoming seed."""
from __future__ import annotations

from copy import deepcopy
import math
import struct
from typing import Mapping

_U64 = (1 << 64) - 1
_INVALID = 0xFFFFFFFF
_REGI = 0x52656769
_PROV = 0x50726F76
_CHUNK_FIELDS = {
    "maximum_00_raw_i32": (0, 4, True), "current_04_raw_i32": (4, 4, True),
    "owner_08_raw_u32": (8, 4, False), "ordinal_0c_raw_i32": (12, 4, True),
    "association_10_raw_u32": (16, 4, False), "flag_14_raw_u8": (20, 1, False),
    "date_1c_raw64": (28, 8, True),
}
_FALSE = {"actual_effects": False, "actual_detachment": False, "actual_post_stage": None,
    "future_drain": False, "lifecycle": False, "fullmonthly": False,
    "future_drain_ready": False, "full_army_lifecycle_ready": False, "full_monthly_ready": False,
    "full_calendar_ready": False, "live": False, "native_writes_executed": 0,
    "native_mutator_invocations": 0}


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


_SENTINEL = _signed(0xFFFFFFFF029C77F8, 64)


def _address(identity: object) -> int | None:
    if type(identity) is str and identity.startswith("native:"):
        digits = identity[7:]
        if digits.isascii() and digits.isdigit() and int(digits) <= _U64:
            return int(digits)
    return None


def _identity(address: int) -> str:
    return "native:" + str(address & _U64)


def _int(value: object) -> bool:
    return type(value) is int


def _f32(value: float | int) -> float:
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except OverflowError:
        return math.copysign(math.inf, value)


def _capacity(count: int, capacity: int) -> tuple[int, int]:
    new_count = _signed(count + 1, 32)
    scaled = _f32(_f32(capacity) * _f32(1.5))
    converted = (math.trunc(scaled) if math.isfinite(scaled)
                 and -(1 << 31) <= scaled < 1 << 31 else -(1 << 31))
    return new_count, max(new_count, converted)


class _Memory:
    """Overlay only supplied semantic addresses; source stores feed later loads."""

    def __init__(self) -> None:
        self.bytes: dict[int, int] = {}
        self.unknown_bytes: set[int] = set()
        self.effects: list[dict] = []

    def seed(self, address: int | None, size: int, value: object) -> None:
        if address is not None and _int(value):
            for index in range(size):
                self.bytes.setdefault((address + index) & _U64, (value >> (index * 8)) & 255)

    def read(self, address: int | None, size: int, *, signed: bool = False,
             fallback: object = None) -> int | None:
        if address is not None and any((address + index) & _U64 in self.unknown_bytes for index in range(size)):
            return None
        if address is None or any((address + index) & _U64 not in self.bytes for index in range(size)):
            return fallback if _int(fallback) else None
        raw = sum(self.bytes[(address + index) & _U64] << (index * 8) for index in range(size))
        return _signed(raw, size * 8) if signed else raw

    def write(self, address: int, size: int, value: int, kind: str) -> None:
        self.effects.append({"kind": kind, "address_identity": _identity(address), "size": size,
            "before_raw": self.read(address, size), "after_raw": value & ((1 << (size * 8)) - 1)})
        for index in range(size):
            byte_address = (address + index) & _U64
            self.bytes[byte_address] = (value >> (index * 8)) & 255
            self.unknown_bytes.discard(byte_address)

    def write_unknown(self, address: int, size: int, kind: str) -> None:
        self.effects.append({"kind": kind, "address_identity": _identity(address), "size": size,
            "before_raw": self.read(address, size), "after_raw": None})
        for index in range(size):
            byte_address = (address + index) & _U64
            self.bytes.pop(byte_address, None)
            self.unknown_bytes.add(byte_address)


def _field(memory: _Memory, chunk: Mapping, name: str) -> int | None:
    address = _address(chunk.get("chunk_identity"))
    offset, size, signed = _CHUNK_FIELDS[name]
    return memory.read(None if address is None else address + offset, size,
                       signed=signed, fallback=chunk.get(name))


def _seed_memory(incoming: Mapping, pending: Mapping) -> _Memory:
    memory = _Memory()
    for chunk in incoming.get("physical_chunks", []):
        address = _address(chunk.get("chunk_identity"))
        for field, (offset, size, _) in _CHUNK_FIELDS.items():
            memory.seed(None if address is None else address + offset, size, chunk.get(field))
    for row in incoming.get("data_occurrences", []):
        address = _address(row.get("record_identity"))
        memory.seed(None if address is None else address + 8, 4, row.get("raw_regi_full_id_u32"))
        memory.seed(None if address is None else address + 12, 4, row.get("data_ordinal_raw_i32"))
    header = _address(pending.get("header_identity"))
    for field, offset, size in (("buffer_identity", 0, 8), ("capacity_08_raw_i32", 8, 4),
                              ("count_0c_raw_i32", 12, 4), ("allocator_identity", 16, 8)):
        value = _address(pending.get(field)) if field.endswith("identity") else pending.get(field)
        memory.seed(None if header is None else header + offset, size, value)
    for row in pending.get("records", []):
        address = _address(row.get("record_identity"))
        for value, offset, size in ((_address(row.get("vtable_identity")), 0, 8),
            (row.get("owner_08_raw_u32"), 8, 4), (row.get("ordinal_0c_raw_i32"), 12, 4)):
            memory.seed(None if address is None else address + offset, size, value)
    return memory


def _resolved(row: object) -> bool:
    return (isinstance(row, Mapping) and row.get("ready") is True
            and _address(row.get("object_identity")) is not None)


def _association(incoming: Mapping, requested: int) -> Mapping | None:
    return next((row for row in incoming.get("association_inputs", [])
                 if row.get("requested_full_id_u32") == requested), None)


def _owner(incoming: Mapping, requested: int) -> Mapping | None:
    return next((row for row in incoming.get("owner_inputs", [])
                 if row.get("requested_full_id_u32") == requested), None)


def _suffix(incoming: Mapping) -> dict:
    result = {"ready": False, "branch": None, "character_full_id_148_u32": incoming.get("character_full_id_148_u32"),
        "actual_selected_character_identity": None, "missing_inputs": []}
    character_id = incoming.get("character_full_id_148_u32")
    if character_id == _INVALID:
        result.update(ready=True, branch="invalid_character_id_return")
    elif not _int(character_id):
        result["missing_inputs"].append("character_full_id_148_u32")
    elif not _resolved(incoming.get("character_resolution")):
        result["missing_inputs"].append("actual_character_resolution")
    else:
        result["actual_selected_character_identity"] = incoming["character_resolution"]["object_identity"]
        present = incoming.get("character_pointer_1b8_present")
        if present is False:
            result.update(ready=True, branch="null_character1b8_return")
        elif present is True:
            result["branch"] = "selected_character_inner_effects_partial"
            result["missing_inputs"].append("actually_selected28CBE70_inner_effects")
        else:
            result["missing_inputs"].append("character_pointer_1b8_present")
    return result


class _Pending:
    def __init__(self, raw: Mapping, memory: _Memory, canonical: object, callback: object,
                 incoming_index: object) -> None:
        self.raw, self.memory = raw, memory
        self.header = _address(raw.get("header_identity"))
        self.buffer = raw.get("buffer_identity")
        self.canonical, self.callback = canonical, callback
        self.count = raw.get("count_0c_raw_i32")
        self.capacity = raw.get("capacity_08_raw_i32")
        self.records = deepcopy(raw.get("records", []))
        self.fresh = False
        self.events: list[dict] = []
        self.growths = 0
        self.incoming_index = incoming_index

    def number(self, field: str) -> int | None:
        value = self.count if field == "count" else self.capacity
        offset = 12 if field == "count" else 8
        return self.memory.read(None if self.header is None else self.header + offset,
                                4, signed=True, fallback=value)

    def buffer_identity(self) -> str | None:
        if self.fresh:
            return self.buffer
        pointer = self.memory.read(self.header, 8, fallback=_address(self.buffer))
        return _identity(pointer) if pointer is not None else None

    def record(self, index: int) -> dict | None:
        base = _address(self.buffer_identity())
        address = None if base is None else (base + index * 16) & _U64
        raw = next((row for row in self.records if row.get("native_index") == index), None)
        if self.fresh:
            return deepcopy(raw) if raw is not None else None
        vtable = self.memory.read(address, 8, fallback=_address(raw.get("vtable_identity")) if raw else None)
        owner = self.memory.read(None if address is None else address + 8, 4,
                                 fallback=raw.get("owner_08_raw_u32") if raw else None)
        ordinal = self.memory.read(None if address is None else address + 12, 4, signed=True,
                                   fallback=raw.get("ordinal_0c_raw_i32") if raw else None)
        if vtable is None or owner is None or ordinal is None:
            return None
        identity = _identity(vtable)
        target = (raw.get("slot0_target_identity") if raw is not None and raw.get("vtable_identity") == identity
            else next((item.get("slot0_target_identity") for item in self.records
                       if item.get("vtable_identity") == identity), None))
        return {"native_index": index, "record_identity": _identity(address) if address is not None else None,
            "vtable_identity": identity, "slot0_target_identity": target,
            "owner_08_raw_u32": owner, "ordinal_0c_raw_i32": ordinal}

    def append(self, chunk: Mapping) -> tuple[bool, str | None, dict]:
        count, capacity = self.number("count"), self.number("capacity")
        event = {"count_before": count, "capacity_before": capacity, "branch": None,
                 "ready": False, "missing_inputs": []}
        def missing(reason: str) -> tuple[bool, str, dict]:
            event["missing_inputs"].append(reason)
            self.events.append(event)
            return False, reason, event
        if count is None or capacity is None or self.header is None:
            return missing("selected_pending_header_count_capacity")
        if _address(self.canonical) is None:
            return missing("canonical_pending_vtable_identity")
        if count != capacity:
            event["branch"] = "typed_no_growth"
            base = _address(self.buffer_identity())
            if base is None and not self.fresh:
                return missing("selected_pending_buffer_identity")
            destination = None if base is None else (base + count * 16) & _U64
            if destination is not None:
                self.memory.write(destination, 8, _address(self.canonical), "pending_record_init_vtable")
                self.memory.write(destination + 8, 4, _INVALID, "pending_record_init_owner")
                self.memory.write(destination + 12, 4, 0, "pending_record_init_ordinal")
            ordinal = _field(self.memory, chunk, "ordinal_0c_raw_i32")
            owner = _field(self.memory, chunk, "owner_08_raw_u32")
            if owner is None or ordinal is None:
                return missing("pending_reload_chunk_owner8_rawordinalC")
            record = {"native_index": count, "record_identity": (_identity(destination) if destination is not None
                else f"{self.buffer}:record:{count}"), "vtable_identity": self.canonical,
                "slot0_target_identity": self.callback, "owner_08_raw_u32": owner, "ordinal_0c_raw_i32": ordinal}
            if destination is not None:
                self.memory.write(destination + 12, 4, ordinal, "pending_record_raw_ordinal")
                self.memory.write(destination + 8, 4, owner, "pending_record_raw_owner")
            reloaded_count = self.number("count")
            if reloaded_count is None:
                return missing("pending_count_after_record_stores")
            self.count = _signed(reloaded_count + 1, 32)
            self.capacity = self.number("capacity")
            self.records = [row for row in self.records if row.get("native_index") != count] + [record]
            self.memory.write(self.header + 12, 4, self.count, "pending_count_increment")
            event.update(ready=True, count_after=self.count, appended_record=deepcopy(record))
        else:
            event["branch"] = "typed_growth"
            allocator = (_identity(self.memory.read(self.header + 16, 8))
                if self.memory.read(self.header + 16, 8) is not None else self.raw.get("allocator_identity"))
            if _address(allocator) is None:
                return missing("selected_pending_allocator_identity")
            new_count, new_capacity = _capacity(count, capacity)
            event.update(new_count=new_count, new_capacity=new_capacity,
                allocation_bytes=(new_capacity & _INVALID) * 16, allocation_alignment=8)
            owner, ordinal = _field(self.memory, chunk, "owner_08_raw_u32"), _field(self.memory, chunk, "ordinal_0c_raw_i32")
            if owner is None or ordinal is None:
                return missing("pending_reload_chunk_owner8_rawordinalC")
            # New storage is a conditional fresh resource token, never an observed pointer.
            token = f"conditional:incoming:{self.incoming_index}:pending-buffer:{self.growths + 1}"
            old_count = self.number("count")
            if old_count is None:
                return missing("growth_reloaded_old_count")
            old_records = []
            for index in range(max(old_count, 0)):
                record = self.record(index)
                if record is None:
                    return missing(f"growth_existing_typed_record[{index}]")
                old_records.append(record)
            prepared = [{**row, "record_identity": f"{token}:record:{index}",
                "vtable_identity": self.canonical, "slot0_target_identity": self.callback}
                for index, row in enumerate(old_records)]
            appended = {"native_index": old_count, "record_identity": f"{token}:record:{old_count}",
                "vtable_identity": self.canonical, "slot0_target_identity": self.callback,
                "owner_08_raw_u32": owner, "ordinal_0c_raw_i32": ordinal}
            prepared.append(appended)
            event.update(prepared_records=deepcopy(prepared), captured_old_count=old_count,
                         old_record_callbacks=[])
            for index, record in enumerate(old_records):
                target = record.get("slot0_target_identity")
                event["old_record_callbacks"].append({"native_index": index,
                    "target_identity": target, "edx": 0, "source_noop_ready": target == self.callback and target is not None})
                if target != self.callback or target is None:
                    return missing(f"selected_old_pending_record_slot0[{index}]_source")
            self.growths += 1
            self.count, self.capacity, self.buffer = new_count, new_capacity, token
            self.records, self.fresh = prepared, True
            self.memory.write(self.header + 8, 4, new_capacity, "pending_commit_capacity")
            # Header bytes now contain an unobserved new pointer. Actual aliases
            # cannot fall back to the captured old pointer after this source store.
            self.memory.write_unknown(self.header, 8, "pending_commit_buffer")
            self.memory.effects[-1].update(conditional_buffer_identity=token, actual_buffer_after_identity=None)
            self.memory.write(self.header + 12, 4, new_count, "pending_commit_count")
            event.update(ready=True, count_after=new_count, conditional_buffer_identity=token,
                         header_write_order=["capacity8", "buffer0", "countC"])
        self.events.append(event)
        return True, None, event

    def result(self) -> dict:
        count = self.number("count")
        records = []
        for index in range(max(count or 0, 0)):
            row = self.record(index)
            if row is None:
                break
            records.append(row)
        return {"observed_header_identity": self.raw.get("header_identity"),
            "observed_buffer_identity": self.raw.get("buffer_identity"),
            "conditional_buffer_identity": self.buffer,
            "actual_buffer_after_identity": None, "conditional_count_0c_raw_i32": count,
            "conditional_capacity_08_raw_i32": self.number("capacity"),
            "conditional_records": records, "events": deepcopy(self.events)}


def _project_incoming(incoming: Mapping, top: Mapping, date: object) -> dict:
    pending_raw = incoming.get("pending") if isinstance(incoming.get("pending"), Mapping) else {}
    memory = _seed_memory(incoming, pending_raw)
    pending = _Pending(pending_raw, memory, top.get("canonical_pending_vtable_identity"),
                       top.get("ready_pending_callback_identity"), incoming.get("native_index"))
    result = {"native_index": incoming.get("native_index"), "arrg_identity": incoming.get("arrg_identity"),
        "input_basis": "standalone_current2633FF0_seed_no_between_ArRg_replay",
        "ready": False, "data_prefix_ready": False, "status": "partial", "unavailable_reason": None,
        "data_count_raw_i32": incoming.get("data_count_raw_i32"),
        "captured_cursor_identity": incoming.get("captured_cursor_identity"),
        "captured_end_identity": incoming.get("captured_end_identity"),
        "terminal_cursor_identity": incoming.get("captured_cursor_identity"),
        "conditional_entry_date_raw64": date, "actual_caller_date_raw64": None,
        "completed_data_occurrence_count": 0, "begun_data_occurrence_count": 0,
        "occurrences": [], "physical_chunks": [], "effects": [], "missing_inputs": [],
        "Character_suffix": _suffix(incoming), "whole_conditional_caller_ready": False, **_FALSE}
    def stop(reason: str) -> None:
        result["missing_inputs"].append(reason)
        if result["unavailable_reason"] is None:
            result["unavailable_reason"] = reason
    cursor = _address(incoming.get("captured_cursor_identity"))
    end = _address(incoming.get("captured_end_identity"))
    if cursor is None or end is None or not _int(incoming.get("data_count_raw_i32")):
        stop("captured_DATA_signed_count_cursor_end")
    rows = incoming.get("data_occurrences", [])
    held_fallback = rows[0].get("held_fallback_regi_identity") if rows else None
    chunks = incoming.get("physical_chunks", [])
    for row in rows if cursor is not None and end is not None and not result["missing_inputs"] else []:
        if cursor == end:
            break
        item = {"native_index": row.get("native_index"), "record_identity": row.get("record_identity"),
            "raw_regi_full_id_u32": None, "data_ordinal_raw_i32": None, "physical_chunk_identity": None,
            "ready": False, "branch": None, "setter_pair_cleared": False, "predicate": None,
            "date_branch": None, "output_date_raw64": None, "date_greater": None,
            "pending_event": None, "missing_inputs": []}
        result["occurrences"].append(item)
        result["begun_data_occurrence_count"] += 1
        def missing(reason: str) -> None:
            item["missing_inputs"].append(reason)
            stop(reason)
        if _address(row.get("record_identity")) != cursor:
            missing("next_source_visited_DATA_cursor")
            break
        requested = memory.read(cursor + 8, 4, fallback=row.get("raw_regi_full_id_u32"))
        ordinal = memory.read(cursor + 12, 4, signed=True, fallback=row.get("data_ordinal_raw_i32"))
        item.update(raw_regi_full_id_u32=requested, data_ordinal_raw_i32=ordinal)
        source_row = next((candidate for candidate in rows if candidate.get("raw_regi_full_id_u32") == requested
            and candidate.get("held_fallback_regi_identity") == held_fallback), None)
        if source_row is None or not _resolved(source_row.get("resolution")) or ordinal is None:
            missing("fresh_selected_Regi_resolution_for_current_DATA_request")
            break
        resolution = source_row["resolution"]
        magic, full_id = source_row.get("magic_14_raw_u32"), resolution.get("selected_full_id_u32")
        item["selected_regi_identity"] = resolution.get("object_identity")
        item["held_fallback_regi_identity"] = held_fallback
        if magic is None or full_id is None:
            missing("selected_Regi_magic14_fullID10")
            break
        if magic != _REGI or full_id == _INVALID:
            item.update(ready=True, branch="invalid_selected_Regi_skip")
            cursor = (cursor + 16) & _U64
            result["completed_data_occurrence_count"] += 1
            continue
        physical = (_address(resolution["object_identity"]) + 0x18 + 0x24 * ordinal) & _U64
        item["physical_chunk_identity"] = _identity(physical)
        if physical == 0:
            item.update(ready=True, branch="null_physical_pointer_skip")
            cursor = (cursor + 16) & _U64
            result["completed_data_occurrence_count"] += 1
            continue
        chunk = next((raw for raw in chunks if _address(raw.get("chunk_identity")) == physical), None)
        if chunk is None:
            missing("selected_physical_chunk_snapshot")
            break
        maximum, current = _field(memory, chunk, "maximum_00_raw_i32"), _field(memory, chunk, "current_04_raw_i32")
        if maximum is None or current is None:
            missing("physical_maximum0_current4")
            break
        if current >= maximum:
            memory.write(physical + 4, 4, maximum, "setter_exact_current_store")
            association = _field(memory, chunk, "association_10_raw_u32")
            if association is None:
                missing("setter_association10")
                break
            flag = _field(memory, chunk, "flag_14_raw_u8") if association == _INVALID else None
            if association == _INVALID and flag is None:
                missing("setter_flag14_for_cleared_association")
                break
            if association == _INVALID and flag == 0:
                owner = _owner(incoming, _field(memory, chunk, "owner_08_raw_u32"))
                if owner is None or not _resolved(owner.get("resolution")) or owner.get("state_138_raw_i32") is None:
                    missing("setter_actual_owner_Regi138")
                    break
                if owner["state_138_raw_i32"] == 0:
                    if owner.get("definition_magic_38_raw_u32") is None:
                        missing("setter_actual_owner_definition_magic38")
                        break
                    if owner["definition_magic_38_raw_u32"] != 0x4744624F:
                        memory.write(physical, 8, 0, "setter_special_pair_clear")
                        item["setter_pair_cleared"] = True
        association_id = _field(memory, chunk, "association_10_raw_u32")
        association = _association(incoming, association_id)
        if (association is None or not _int(association.get("context_count_0c_raw_u32"))
                or any(not _resolved(association.get(field)) for field in
                       ("arrg_resolution", "army_resolution", "unit_resolution", "character_resolution"))):
            missing("evolved_association2658050_chain_raw_context_count")
            break
        predicate = association["context_count_0c_raw_u32"] != 0
        item["predicate"] = predicate
        if predicate:
            memory.write(physical + 28, 8, _SENTINEL, "caller_date_sentinel")
            if not _int(date):
                missing("current_date_storage_raw64_conditional_entry")
                break
            if _address(incoming.get("passed_province_identity")) is None:
                missing("actual_passed_Province_identity")
                break
            owner_id = _field(memory, chunk, "owner_08_raw_u32")
            owner = _owner(incoming, owner_id)
            if owner is None or not _resolved(owner.get("resolution")) or owner.get("origin_magic_85c_raw_u32") is None:
                missing("date_actual_owner_Regi120_origin")
                break
            date_row = next((raw for raw in incoming.get("date_inputs", [])
                if raw.get("association_full_id_u32") == association_id and raw.get("owner_full_id_u32") == owner_id), None)
            if owner["origin_magic_85c_raw_u32"] != _PROV:
                if date_row is None or date_row.get("capital_origin_magic_85c_raw_u32") is None:
                    missing("actual_native_capital_origin_tag")
                    break
                if date_row["capital_origin_magic_85c_raw_u32"] != _PROV:
                    output = date
                    item["date_branch"] = "both_origins_nonProv_copy_entry_qword"
                else:
                    output = date_row.get("output_date_raw64")
                    item["date_branch"] = "native_computed_capital_origin"
            else:
                output = date_row.get("output_date_raw64") if date_row else None
                item["date_branch"] = "native_computed_Regi120_origin"
            unit_identity = association["unit_resolution"].get("object_identity")
            if item["date_branch"] != "both_origins_nonProv_copy_entry_qword" and (
                    not _int(output) or date_row.get("unit_identity") != unit_identity
                    or date != top.get("current_date_storage_raw64")
                    or (owner["origin_magic_85c_raw_u32"] == _PROV
                        and date_row.get("source_origin_identity") != owner.get("origin_identity"))):
                missing("actual_selected_current_input2C54340_full_date")
                break
            item["output_date_raw64"] = output
            greater = _signed(output, 32) > _signed(date, 32)
            item["date_greater"] = greater
            if greater:
                memory.write(physical + 28, 8, output, "caller_full_computed_date_store")
                if _address(top.get("primary_receiver_identity")) is None:
                    missing("actual_primary_receiver_identity")
                    break
                ready, reason, event = pending.append(chunk)
                item["pending_event"] = deepcopy(event)
                if not ready:
                    missing(reason)
                    break
        memory.write(physical + 16, 4, _INVALID, "caller_association_clear")
        memory.write(physical + 20, 1, 0, "caller_flag_clear")
        # Captures expose the actual fallback binding, not a final mapper return.
        next_index = row.get("native_index", 0) + 1
        held_fallback = (rows[next_index].get("held_fallback_regi_identity") if next_index < len(rows)
                         else row.get("held_fallback_regi_identity"))
        item.update(ready=True, branch="processed_valid_chunk")
        cursor = (cursor + 16) & _U64
        result["completed_data_occurrence_count"] += 1
    if cursor is not None and end is not None and cursor != end and not result["missing_inputs"]:
        stop("remaining_source_visited_DATA_occurrences")
    ready = cursor is not None and end is not None and cursor == end and not result["missing_inputs"]
    result.update(ready=ready, data_prefix_ready=ready, status="available" if ready else "partial",
        terminal_cursor_identity=_identity(cursor) if cursor is not None else None,
        whole_conditional_caller_ready=ready and result["Character_suffix"]["ready"],
        conditional_pending=pending.result(), effects=memory.effects,
        physical_chunks=[{**deepcopy(chunk), **{name: _field(memory, chunk, name) for name in _CHUNK_FIELDS}}
                         for chunk in chunks])
    return result


def project_current_detachment_data_prefix(inputs: Mapping | None, *,
                                         current_date_storage_raw64: int | None = None) -> dict:
    """Every incoming result starts from its own captured baseline, including repeats."""
    result = {"projection_kind": "same_input_current_detachment_data_prefix",
        "source_contract_game_version": "1.20.0.3", "native_caller_rva": "0x2633FF0",
        "input_basis": "standalone_current_incoming_seed_not_parent_detach_replay",
        "status": "unavailable", "ready": False, "selection_ready": False, "roster_ready": False,
        "candidate_occurrences": [], "incoming": [], "missing_inputs": [], **_FALSE}
    if not isinstance(inputs, Mapping):
        result["missing_inputs"].append("current_detachment_data_inputs_v1")
        return result
    date = current_date_storage_raw64 if current_date_storage_raw64 is not None else inputs.get("current_date_storage_raw64")
    result["selection_ready"] = inputs.get("selection_ready") is True
    result["roster_ready"] = inputs.get("roster_ready") is True
    result["incoming"] = [_project_incoming(row, inputs, date) for row in inputs.get("incoming", [])]
    by_index = {row["native_index"]: row for row in result["incoming"]}
    for row in inputs.get("candidate_occurrences", []):
        item = {"native_index": row.get("native_index"), "raw_full_id_u32": row.get("raw_full_id_u32"),
            "resolved_arrg_identity": row.get("resolution", {}).get("object_identity"),
            "incoming_index": row.get("incoming_index"), "incoming_valid": row.get("incoming_valid"),
            "ready": False, "missing_inputs": []}
        if row.get("incoming_valid") is False and _resolved(row.get("resolution")):
            item["ready"] = True
        elif row.get("incoming_valid") is True:
            incoming = by_index.get(row.get("incoming_index"))
            if incoming is None:
                item["missing_inputs"].append("independent_incoming_snapshot")
            else:
                item["ready"] = incoming["data_prefix_ready"]
                item["missing_inputs"].extend(incoming["missing_inputs"])
        else:
            item["missing_inputs"].append("current_incoming_ArRg_admission")
        result["candidate_occurrences"].append(item)
        result["missing_inputs"].extend(f"candidate[{item['native_index']}].{field}" for field in item["missing_inputs"])
    if not result["selection_ready"]:
        result["missing_inputs"].append("current_candidate_selection")
    if not result["roster_ready"]:
        result["missing_inputs"].append("whole_current_candidate_roster")
    ready = result["selection_ready"] and result["roster_ready"] and all(
        item["ready"] for item in result["candidate_occurrences"])
    result.update(ready=ready, status="available" if ready else "partial")
    return result
