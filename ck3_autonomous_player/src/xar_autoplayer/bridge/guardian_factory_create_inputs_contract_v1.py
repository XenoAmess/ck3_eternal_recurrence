"""Validate copied factory creation inputs from the same private paused job.

The DWORD and QWORD stay raw. This decoder neither calls a factory nor assigns
the QWORD a pointer role, relation kind, membership or outcome.
"""
from __future__ import annotations

from copy import deepcopy

LEAF = "factory_create_inputs_v1"
DISCOVERY = "xar.ck3.guardian-factory-discovery.v1"
EXACT_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
KEYS = ("has_relation_guardian", "has_relation_ward")


def _uint(value: object, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < 2**bits:
        raise ValueError(f"{name}: unsigned {bits}-bit value required")
    return value


def _flag(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name}: boolean required")
    return value


def _optional_u32(value: object, name: str) -> int | None:
    return None if value is None else _uint(value, 32, name)


def _raw_field(value: object, bits: int, name: str) -> int | None:
    if not isinstance(value, dict) or set(value) != {"available", "raw_value"}:
        raise ValueError(f"{name}: malformed availability/value pair")
    available = _flag(value["available"], name + ".available")
    if available:
        return _uint(value["raw_value"], bits, name + ".raw_value")
    if value["raw_value"] is not None:
        raise ValueError(f"{name}: unavailable read must retain null")
    return None


def validate_guardian_factory_create_inputs_v1(
    value: object, *, command_result: object, snapshot: dict[str, object],
    family_result: dict[str, object],
) -> dict[str, object] | None:
    """Return an owned native sidecar, or None for the legacy absent sibling.

    A malformed new sibling raises ValueError. The ordinary family result has
    already been retained by the capture wrapper and is independent of it.
    """
    if not isinstance(value, dict):
        raise ValueError("guardian discovery must be an object")
    rows = value.get("factories")
    if not isinstance(rows, list) or len(rows) != 2 or any(
        not isinstance(row, dict) for row in rows
    ) or tuple(row.get("key") for row in rows) != KEYS:
        raise ValueError("guardian discovery requires two fixed ordered keys")
    present = [LEAF in row for row in rows]
    if not any(present):
        return None
    if not all(present):
        raise ValueError("guardian discovery has mixed factory input versions")
    if (value.get("schema") != DISCOVERY
            or type(value.get("schema_version")) is not int
            or value["schema_version"] != 1):
        raise ValueError("guardian discovery schema changed")
    for key, expected in (("read_only", True), ("advertised", False),
                          ("source_discovery_only", True),
                          ("guardian_membership_observed", False), ("paused", True)):
        if value.get(key) is not expected:
            raise ValueError(f"guardian discovery {key} changed")
    if snapshot.get("paused") is not True:
        raise ValueError("guardian inputs lack the original paused snapshot")
    qualified = _flag(value.get("qualified"), "qualified")
    if (value.get("status") != ("captured" if qualified else "unavailable")
            or not isinstance(value.get("unavailable_reason"), str)
            or (value["unavailable_reason"] != "" if qualified
                else value["unavailable_reason"] == "")):
        raise ValueError("guardian discovery qualification is inconsistent")
    if not isinstance(command_result, dict) or (
        command_result.get("type") != "command_result"
        or type(command_result.get("protocol_version")) is not int
        or command_result["protocol_version"] != 1
        or command_result.get("ok") is not True
    ):
        raise ValueError("guardian inputs lack the retained original command result")
    request = command_result.get("request_id")
    if not isinstance(request, str) or not request or value.get("request_id") != request:
        raise ValueError("guardian input request differs from the actual family job")
    result = command_result.get("result")
    if not isinstance(result, dict) or (
        result.get("step") != "query-current-first-heir-relationship-v1-private"
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
    ):
        raise ValueError("guardian inputs lack the original private family result")
    revision = _uint(snapshot.get("native_revision"), 64, "snapshot.native_revision")
    if revision == 0 or any(type(container.get("native_revision")) is not int
        or container["native_revision"] != revision
        for container in (value, result, family_result)):
        raise ValueError("guardian input native revision changed")
    date = snapshot.get("date_raw")
    if type(date) is not int or type(value.get("date_raw")) is not int or value["date_raw"] != date:
        raise ValueError("guardian input date changed")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, dict) else snapshot.get("played_character_id")
    if type(actor) is not int or not 0 < actor < 2**31 or value.get("played_character_id") != actor:
        raise ValueError("guardian input played character changed")
    if type(value.get("played_character_id")) is not int:
        raise ValueError("guardian input played character must be an integer")
    sha = value.get("executable_sha256")
    family_sha = family_result.get("exe_sha256")
    if (not isinstance(sha, str) or sha.upper() != EXACT_SHA
            or not isinstance(family_sha, str) or family_sha.upper() != EXACT_SHA
            or family_result.get("exact_ck3_build") != "1.20.0.4"):
        raise ValueError("guardian inputs lack the same exact native build")
    heir = family_result.get("heir_character_id")
    native_heir = heir if heir is not None else -1
    if type(native_heir) is not int or any(
        type(container.get("heir_character_id")) is not int
        or container["heir_character_id"] != native_heir for container in (value, result)
    ):
        raise ValueError("guardian input heir binding changed")
    base = _uint(value.get("module_base"), 64, "module_base")
    image_size = _uint(value.get("image_size"), 64, "image_size")
    _uint(value.get("pump_epoch"), 64, "pump_epoch")
    _uint(value.get("thread_id"), 32, "thread_id")
    for row in rows:
        child = row[LEAF]
        if not isinstance(child, dict) or set(child) != {
            "schema_version", "field_10_dword", "field_18_qword"
        } or type(child.get("schema_version")) is not int or child["schema_version"] != 1:
            raise ValueError("factory creation input schema changed")
        dword = _raw_field(child["field_10_dword"], 32, "field_10_dword")
        qword = _raw_field(child["field_18_qword"], 64, "field_18_qword")
        record = _optional_u32(row.get("record_name_id"), "record_name_id")
        if dword != record:
            raise ValueError("factory DWORD differs from its original record_name_id")
        name_id = _optional_u32(row.get("name_id"), "name_id")
        map_id = _optional_u32(row.get("map_name_id"), "map_name_id")
        factory = _uint(row.get("factory_address"), 64, "factory_address")
        _uint(row.get("vtable_address"), 64, "vtable_address")
        _uint(row.get("opaque_descriptor_address"), 64, "opaque_descriptor_address")
        status = row.get("status")
        if status not in {"found", "name_missing", "factory_missing", "unavailable"}:
            raise ValueError("factory lookup status changed")
        if not isinstance(row.get("unavailable_reason"), str):
            raise ValueError("factory lookup reason missing")
        if status == "found":
            stored = row.get("stored_name")
            folded = "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in stored) if isinstance(stored, str) else None
            if (not qualified or factory == 0 or name_id is None or map_id != name_id
                    or record is None or folded != row["key"]
                    or row["unavailable_reason"] != ""):
                raise ValueError("factory input row lost its actual key/name/factory association")
        elif qword is not None:
            raise ValueError("factory QWORD is present without a found source factory")
        if not qualified and (dword is not None or qword is not None):
            raise ValueError("unqualified completion cannot retain available factory inputs")
        slots = row.get("virtual_slots")
        if not isinstance(slots, list) or len(slots) != 4:
            raise ValueError("factory input row lost its original virtual slots")
        for index, slot in enumerate(slots):
            if not isinstance(slot, dict) or type(slot.get("slot_index")) is not int or slot["slot_index"] != index:
                raise ValueError("factory virtual-slot order changed")
            available = _flag(slot.get("available"), "virtual_slot.available")
            address, rva = slot.get("address"), slot.get("rva")
            if not available:
                if address is not None or rva is not None:
                    raise ValueError("unavailable virtual slot must retain null")
                continue
            address = _uint(address, 64, "virtual_slot.address")
            in_image = base != 0 and base <= address and address - base < image_size
            if rva is not None:
                _uint(rva, 64, "virtual_slot.rva")
                if not in_image or rva != address - base:
                    raise ValueError("factory virtual-slot RVA/address association changed")
            elif in_image:
                raise ValueError("in-image factory virtual slot lost its native RVA")
    return deepcopy(value)
