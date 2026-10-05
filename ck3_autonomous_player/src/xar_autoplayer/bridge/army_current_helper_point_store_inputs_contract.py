"""Optional exact-memory inputs for the current helper's point stores."""
from __future__ import annotations

_TOP = {"status", "ready", "unavailable_reason", "entry_army_id", "helper_resolved_army_id",
        "helper_used_fallback", "helper_same_current_army_pointer", "group_count_5c_raw", "groups"}
_GROUP = {"group_index", "record_count_14_raw", "character_count_2c_raw", "record_rows", "character_rows"}
_REQUIRED = {"stored_index", "record_regiment_reference_id", "chunk_index"}
_RECORD_I32 = {"record_regiment_resolved_id", "data_alias_ordinal", "data_state_18_raw",
               "data_owner_regiment_reference_id", "receiver_regiment_resolved_id",
               "receiver_title_reference_130_raw", "receiver_character_reference_12c_raw",
               "owner_title_resolved_id", "owner_title_holder_character_id_128_raw",
               "selected_character_reference_id", "selected_character_resolved_id",
               "membership_alias_ordinal", "membership_count_2b4_raw"}
_RECORD_BOOL = {"record_regiment_used_fallback", "data_record_present", "receiver_regiment_used_fallback",
                "owner_title_used_fallback", "selected_character_used_fallback", "character_child_1c0_present"}
_RECORD = _REQUIRED | _RECORD_I32 | _RECORD_BOOL | {
    "record_regiment_magic_14_raw", "data_byte_14_raw", "ordered_persistent_regiment_ids_2a8"}
_CHAR_I32 = {"character_resolved_id", "child_1b8_alias_ordinal", "child_character_reference_fc_raw"}
_CHAR_BOOL = {"character_used_fallback", "character_child_1b8_present",
              "character_child_1c8_present", "character_child_1c0_present"}
_CHAR = {"stored_index", "character_reference_id", "child_byte_108_raw"} | _CHAR_I32 | _CHAR_BOOL


def _int(value: object, bits: int = 32, signed: bool = True, nullable: bool = True) -> None:
    if value is None and nullable:
        return
    lower = -(1 << (bits - 1)) if signed else 0
    upper = 1 << (bits - 1) if signed else 1 << bits
    if type(value) is not int or not lower <= value < upper:
        raise ValueError("native current helper point-store integer width is malformed")


def _bool(value: object) -> None:
    if value is not None and type(value) is not bool:
        raise ValueError("native current helper point-store predicate must be bool or null")


def _alias(value: object) -> None:
    if value is not None and value < 0:
        raise ValueError("native current helper point-store alias is negative")


def normalize_monthly_current_helper_point_store_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _TOP:
        raise ValueError("native current helper point-store schema is malformed")
    ready = value["status"] == "available"
    if value["status"] not in {"available", "unavailable"} or type(value["ready"]) is not bool or value["ready"] != ready:
        raise ValueError("native current helper point-store status/readiness is malformed")
    reason = value["unavailable_reason"]
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native current helper point-store reason disagrees with readiness")
    for key in ("entry_army_id", "helper_resolved_army_id", "group_count_5c_raw"):
        _int(value[key])
    for key in ("helper_used_fallback", "helper_same_current_army_pointer"):
        _bool(value[key])
    result = dict(value)
    groups = value["groups"]
    if groups is not None:
        if not isinstance(groups, list):
            raise ValueError("native point-store groups must be ordered or null")
        copied = []
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict) or set(group) != _GROUP:
                raise ValueError("native point-store group schema is malformed")
            _int(group["group_index"], nullable=False)
            if group["group_index"] != group_index:
                raise ValueError("native point-store group order is malformed")
            for key in ("record_count_14_raw", "character_count_2c_raw"):
                _int(group[key])
            copy = dict(group)
            records = group["record_rows"]
            if records is not None:
                if not isinstance(records, list):
                    raise ValueError("native point-store record rows must be ordered or null")
                record_copies = []
                for index, row in enumerate(records):
                    if not isinstance(row, dict) or set(row) != _RECORD:
                        raise ValueError("native point-store record schema is malformed")
                    for key in _REQUIRED:
                        _int(row[key], nullable=False)
                    if row["stored_index"] != index:
                        raise ValueError("native point-store record order is malformed")
                    for key in _RECORD_I32:
                        _int(row[key])
                    for key in _RECORD_BOOL:
                        _bool(row[key])
                    _int(row["record_regiment_magic_14_raw"], signed=False)
                    _int(row["data_byte_14_raw"], bits=8, signed=False)
                    for key in ("data_alias_ordinal", "membership_alias_ordinal"):
                        _alias(row[key])
                    item = dict(row)
                    ids = row["ordered_persistent_regiment_ids_2a8"]
                    if ids is not None:
                        if not isinstance(ids, list):
                            raise ValueError("native point-store membership IDs must be ordered or null")
                        for raw_id in ids:
                            _int(raw_id, nullable=False)
                        item["ordered_persistent_regiment_ids_2a8"] = list(ids)
                    record_copies.append(item)
                copy["record_rows"] = record_copies
            characters = group["character_rows"]
            if characters is not None:
                if not isinstance(characters, list):
                    raise ValueError("native point-store Character rows must be ordered or null")
                char_copies = []
                for index, row in enumerate(characters):
                    if not isinstance(row, dict) or set(row) != _CHAR:
                        raise ValueError("native point-store Character schema is malformed")
                    _int(row["stored_index"], nullable=False)
                    _int(row["character_reference_id"], nullable=False)
                    if row["stored_index"] != index:
                        raise ValueError("native point-store Character order is malformed")
                    for key in _CHAR_I32:
                        _int(row[key])
                    for key in _CHAR_BOOL:
                        _bool(row[key])
                    _alias(row["child_1b8_alias_ordinal"])
                    _int(row["child_byte_108_raw"], bits=8, signed=False)
                    char_copies.append(dict(row))
                copy["character_rows"] = char_copies
            char_count = group["character_count_2c_raw"]
            if char_count is not None and char_count < 0 and characters is not None:
                raise ValueError("native negative Character pointer-bound traversal cannot be an empty list")
            copied.append(copy)
        result["groups"] = copied
    if ready and any(value[key] is None for key in ("entry_army_id", "group_count_5c_raw", "groups")):
        raise ValueError("native ready point-store group traversal is incomplete")
    return result
