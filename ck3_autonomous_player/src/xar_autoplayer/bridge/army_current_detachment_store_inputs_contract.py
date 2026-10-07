"""Strict optional current actual4 ArRg registry-admission operands."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import _boolean, _integer, _object, _text

_STATE = {"status", "ready", "unavailable_reason"}
_LIMITS = {"actual_callback_observed", "actual_resource_return_observed",
    "actual_after_state_observed", "full_detachment_transition_ready",
    "full_daily_ready", "full_monthly_ready"}
_TOP = _STATE | _LIMITS | {"schema_version", "source", "stage",
    "seed_selection_ready", "seed_roster_ready", "current_date_storage_raw64",
    "source_parent_identity", "source_parent_wrapper_mode_i32", "registry_identity",
    "store_48_raw_u8", "slot_count_2c_raw_u32", "slot_table_identity",
    "active_count_3c_raw_u32", "registry_mark_4a_raw_u8", "high_water_38_raw_u32",
    "free_head_40_raw_u32", "requests"}
_REQUEST = _STATE | {"seed_incoming_native_indices", "incoming_arrg_identity",
    "requested_full_id_u32", "index_low24_u32", "slot_identity",
    "selected_pointer_present", "selected_object_identity", "selected_full_id_10_raw_u32",
    "selected_primary_vtable_identity", "selected_slot0_target_identity", "trailing_slot_scan"}
_SCAN = _STATE | {"slot_index_u32", "slot_identity", "object_pointer_present", "object_identity"}


def _state(row: dict, name: str) -> None:
    if row["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(f"{name}.status is malformed")
    _boolean(row["ready"], name + ".ready", nullable=False)
    _text(row["unavailable_reason"], name + ".unavailable_reason")
    if row["ready"] != (row["status"] == "available"):
        raise ValueError(f"{name} availability disagrees with readiness")
    if row["ready"] and row["unavailable_reason"] is not None:
        raise ValueError(f"{name} ready value has an unavailable reason")
    if not row["ready"] and row["unavailable_reason"] is None:
        raise ValueError(f"{name} partial value lacks its actual reason")


def _row(value: object, fields: set[str], name: str) -> dict:
    row = _object(value, fields, name)
    _state(row, name)
    return row


def _identity(value: object, name: str) -> None:
    _text(value, name)
    if value is not None and (not value.startswith("native:")
            or not value[7:].isascii() or not value[7:].isdigit()
            or not 0 <= int(value[7:]) < 1 << 64):
        raise ValueError(f"{name} native identity is malformed")


def _rows(value: object, name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an ordered array")
    return value


def normalize_current_detachment_store_inputs_v1(value: object) -> dict | None:
    """Validate observed shape without demanding unselected source operands.

    The full family may be absent or null on older wires. Later registry,
    callback and trailing-scan context stays nullable and does not qualify or
    invalidate the separately observed current admission branch.
    """
    if value is None:
        return None
    top = _row(value, _TOP, "current detachment store")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("current detachment store schema_version must equal 1")
    if (top["source"] != "native_current_detachment_store_inputs_12004"
            or top["stage"] != "observed_current_detachment_store_seed"):
        raise ValueError("current detachment store source/stage is malformed")
    for field in ("seed_selection_ready", "seed_roster_ready"):
        _boolean(top[field], field, nullable=False)
    _integer(top["current_date_storage_raw64"], "store.current_date_storage_raw64", bits=64)
    mode = _integer(top["source_parent_wrapper_mode_i32"], "store.source_parent_wrapper_mode_i32")
    if mode is not None and mode != 0:
        raise ValueError("store.source_parent_wrapper_mode_i32 lacks the actual4 source witness")
    for field in ("source_parent_identity", "registry_identity", "slot_table_identity"):
        _identity(top[field], "store." + field)
    for field in ("store_48_raw_u8", "registry_mark_4a_raw_u8"):
        _integer(top[field], "store." + field, bits=8, unsigned=True)
    for field in ("slot_count_2c_raw_u32", "active_count_3c_raw_u32",
            "high_water_38_raw_u32", "free_head_40_raw_u32"):
        _integer(top[field], "store." + field, unsigned=True)
    for field in _LIMITS:
        if top[field] is not False:
            raise ValueError(f"store.{field} must remain false")
    for index, value_request in enumerate(_rows(top["requests"], "store.requests")):
        name = f"store.requests[{index}]"
        request = _row(value_request, _REQUEST, name)
        for alias_index in _rows(request["seed_incoming_native_indices"], name + ".seed_indices"):
            _integer(alias_index, name + ".seed_index", nullable=False, nonnegative=True)
        for field in ("incoming_arrg_identity", "slot_identity", "selected_object_identity",
                "selected_primary_vtable_identity", "selected_slot0_target_identity"):
            _identity(request[field], name + "." + field)
        for field in ("requested_full_id_u32", "index_low24_u32", "selected_full_id_10_raw_u32"):
            _integer(request[field], name + "." + field, unsigned=True)
        _boolean(request["selected_pointer_present"], name + ".selected_pointer_present")
        for position, value_scan in enumerate(_rows(request["trailing_slot_scan"], name + ".trailing_scan")):
            scan_name = f"{name}.trailing_scan[{position}]"
            scan = _row(value_scan, _SCAN, scan_name)
            _integer(scan["slot_index_u32"], scan_name + ".slot_index_u32", unsigned=True, nullable=False)
            _boolean(scan["object_pointer_present"], scan_name + ".object_pointer_present")
            for field in ("slot_identity", "object_identity"):
                _identity(scan[field], scan_name + "." + field)
    return deepcopy(top)
