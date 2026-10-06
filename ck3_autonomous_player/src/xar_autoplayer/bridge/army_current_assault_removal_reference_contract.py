"""Typed current Army-reference union and target-specific first-helper context."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import _boolean, _integer, _object, _resolution

_STATE = {"status", "ready", "unavailable_reason"}
_TOP = _STATE | {"schema_version", "source", "stage", "manager_identity",
    "observed_pending_ids_i32", "manager_id_lists", "records_b0",
    "reference_occurrences", "cleanup_targets"}
_REFERENCE = _STATE | {"native_index", "reference_scope", "pending_native_index",
    "group_native_index", "group_physical_slot_i64", "group_army_native_index",
    "raw_full_id_u32", "resolution", "army_magic_14_raw_u32",
    "native_army_identity_valid", "identity_scalar_basis", "cleanup_target_index"}
_TARGET = _STATE | {"native_index", "argument_full_id_u32", "helper_resolution",
    "selected_bucket_index_u32", "bucket_count_raw_i32", "bucket_data_present", "bucket_rows"}
_BUCKET = {"native_index", "pointer_identity", "native_same_helper_pointer"}
_OFFSETS = ("50", "68", "80", "98", "c8", "158")


def _state(value: dict, name: str) -> None:
    if value["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(f"{name}.status is malformed")
    _boolean(value["ready"], name + ".ready", nullable=False)
    _string(value["unavailable_reason"], name + ".unavailable_reason")


def _string(value: object, name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be text or null")


def _array(value: object, name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return value


def normalize_current_assault_removal_reference_inputs_v1(value: object) -> dict | None:
    """Copy actual typed operands without demanding an unused candidate tail."""
    if value is None:
        return None
    top = _object(value, _TOP, "current assault removal reference root")
    _state(top, "current assault removal reference root")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("current assault removal reference schema_version must equal1")
    if top["source"] != "native_current_assault_removal_references" or top["stage"] != "observed_current_removal_reference_context":
        raise ValueError("current assault removal reference source/stage is malformed")
    _string(top["manager_identity"], "manager_identity")
    pending = top["observed_pending_ids_i32"]
    if pending is not None:
        for identity in _array(pending, "observed_pending_ids_i32"):
            _integer(identity, "observed pending ID", nullable=False)
    lists = _array(top["manager_id_lists"], "manager_id_lists")
    if len(lists) != len(_OFFSETS):
        raise ValueError("current assault removal must retain six manager list components")
    for offset, component in zip(_OFFSETS, lists):
        row = _object(component, {"manager_offset", "ordered_army_ids"}, "manager list")
        if row["manager_offset"] != offset:
            raise ValueError("current assault removal manager component order is malformed")
        if row["ordered_army_ids"] is not None:
            for identity in _array(row["ordered_army_ids"], "manager IDs"):
                _integer(identity, "manager ID", nullable=False)
    records = top["records_b0"]
    if records is not None:
        for words in _array(records, "records_b0"):
            if not isinstance(words, list) or len(words) != 4:
                raise ValueError("current assault removal record must retain four DWORDs")
            for word in words:
                _integer(word, "opaque B0 DWORD", unsigned=True, nullable=False)
    references = _array(top["reference_occurrences"], "reference_occurrences")
    for index, raw in enumerate(references):
        row = _object(raw, _REFERENCE, "current assault Army reference")
        _state(row, "current assault Army reference")
        native_index = _integer(row["native_index"], "reference native_index", nullable=False)
        if native_index != index:
            raise ValueError("current assault removal reference union order is malformed")
        if row["reference_scope"] not in {"current_pending", "current_group_army"}:
            raise ValueError("current assault removal reference scope is malformed")
        if row["identity_scalar_basis"] not in {"copied_current_pending_magic", "native_current_group_magic"}:
            raise ValueError("current assault removal identity scalar basis is malformed")
        for field in ("pending_native_index", "group_native_index", "group_army_native_index", "cleanup_target_index"):
            _integer(row[field], field)
        _integer(row["group_physical_slot_i64"], "group_physical_slot_i64", bits=64)
        requested = _integer(row["raw_full_id_u32"], "raw_full_id_u32", unsigned=True)
        _resolution(row["resolution"], requested, "current assault Army resolution")
        _integer(row["army_magic_14_raw_u32"], "army_magic_14_raw_u32", unsigned=True)
        _boolean(row["native_army_identity_valid"], "native_army_identity_valid")
    for index, raw in enumerate(_array(top["cleanup_targets"], "cleanup_targets")):
        row = _object(raw, _TARGET, "current assault helper target")
        _state(row, "current assault helper target")
        native_index = _integer(row["native_index"], "target native_index", nullable=False)
        if native_index != index:
            raise ValueError("current assault removal target order is malformed")
        argument = _integer(row["argument_full_id_u32"], "argument_full_id_u32", unsigned=True, nullable=False)
        _resolution(row["helper_resolution"], argument, "current assault helper second resolution")
        _integer(row["selected_bucket_index_u32"], "selected_bucket_index_u32", unsigned=True)
        _integer(row["bucket_count_raw_i32"], "bucket_count_raw_i32")
        _boolean(row["bucket_data_present"], "bucket_data_present")
        if row["bucket_rows"] is not None:
            for ordinal, raw_bucket in enumerate(_array(row["bucket_rows"], "bucket_rows")):
                bucket = _object(raw_bucket, _BUCKET, "current assault bucket row")
                if _integer(bucket["native_index"], "bucket native_index", nullable=False) != ordinal:
                    raise ValueError("current assault removal bucket order is malformed")
                _string(bucket["pointer_identity"], "bucket pointer_identity")
                _boolean(bucket["native_same_helper_pointer"], "native_same_helper_pointer")
    return deepcopy(top)
