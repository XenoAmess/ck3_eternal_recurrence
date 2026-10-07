"""Strict optional actual4 inputs for each current ArRg callback core seed."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import _boolean, _integer, _object, _text

_STATE = {"status", "ready", "unavailable_reason"}
_LIMITS = {"actual_callback_observed", "actual_resource_return_observed",
    "actual_after_state_observed", "full_detachment_transition_ready",
    "full_daily_ready", "full_monthly_ready"}
_KNOWN = {"known_primary_vtable_identity", "known_primary_slot0_target_identity",
    "known_core_identity", "known_mode0_record_callback_identity",
    "known_secondary_base_vtable_identity"}
_TOP = _STATE | _LIMITS | _KNOWN | {"schema_version", "source", "stage",
    "seed_selection_ready", "seed_roster_ready", "current_date_storage_raw64",
    "source_parent_wrapper_mode_i32", "incoming"}
_INCOMING = _STATE | {"seed_incoming_native_indices", "arrg_identity", "arrg_full_id_u32",
    "arrg_primary_vtable_identity", "arrg_primary_slot0_target_identity",
    "data_pointer_present", "data_buffer_identity", "data_count_2c_raw_i32",
    "data_capacity_28_raw_i32", "data_allocator_identity", "data_allocator_vtable_identity",
    "data_allocator_slot10_target_identity", "records"}
_RECORD = _STATE | {"native_index", "record_identity", "vtable_identity", "slot0_target_identity"}


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


def normalize_current_detachment_callback_inputs_v1(value: object) -> dict | None:
    """Keep missing branch operands and raw signed counts separate from zero.

    Older frames may omit this whole family. A null DATA buffer does not demand
    count/capacity or allocator context. Noncanonical selected record callbacks
    are valid observations; the pure consumer decides their source readiness.
    """
    if value is None:
        return None
    top = _row(value, _TOP, "current detachment callback")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("current detachment callback schema_version must equal 1")
    if (top["source"] != "native_current_detachment_callback_inputs_12004"
            or top["stage"] != "observed_current_detachment_callback_seed"):
        raise ValueError("current detachment callback source/stage is malformed")
    for field in ("seed_selection_ready", "seed_roster_ready"):
        _boolean(top[field], field, nullable=False)
    _integer(top["current_date_storage_raw64"], "callback.current_date_storage_raw64", bits=64)
    mode = _integer(top["source_parent_wrapper_mode_i32"], "callback.source_parent_wrapper_mode_i32")
    if mode is not None and mode != 0:
        raise ValueError("callback.source_parent_wrapper_mode_i32 lacks the actual4 source witness")
    for field in _KNOWN:
        _identity(top[field], "callback." + field)
    for field in _LIMITS:
        if top[field] is not False:
            raise ValueError(f"callback.{field} must remain false")
    for index, value_incoming in enumerate(_rows(top["incoming"], "callback.incoming")):
        name = f"callback.incoming[{index}]"
        incoming = _row(value_incoming, _INCOMING, name)
        for alias_index in _rows(incoming["seed_incoming_native_indices"], name + ".seed_indices"):
            _integer(alias_index, name + ".seed_index", nullable=False, nonnegative=True)
        for field in ("arrg_identity", "arrg_primary_vtable_identity",
                "arrg_primary_slot0_target_identity", "data_buffer_identity",
                "data_allocator_identity", "data_allocator_vtable_identity",
                "data_allocator_slot10_target_identity"):
            _identity(incoming[field], name + "." + field)
        _integer(incoming["arrg_full_id_u32"], name + ".arrg_full_id_u32", unsigned=True)
        _boolean(incoming["data_pointer_present"], name + ".data_pointer_present")
        for field in ("data_count_2c_raw_i32", "data_capacity_28_raw_i32"):
            _integer(incoming[field], name + "." + field)
        for position, value_record in enumerate(_rows(incoming["records"], name + ".records")):
            record_name = f"{name}.records[{position}]"
            record = _row(value_record, _RECORD, record_name)
            if _integer(record["native_index"], record_name + ".native_index",
                    nullable=False, nonnegative=True) != position:
                raise ValueError(f"{record_name} original occurrence order is malformed")
            for field in ("record_identity", "vtable_identity", "slot0_target_identity"):
                _identity(record[field], record_name + "." + field)
    return deepcopy(top)
