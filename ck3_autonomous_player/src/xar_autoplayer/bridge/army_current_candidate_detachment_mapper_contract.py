"""Typed current candidate roster and source-defined persistent mapper operands."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import _boolean, _integer, _object, _resolution

_STATE = {"status", "ready", "unavailable_reason"}
_TOP = _STATE | {"schema_version", "source", "stage", "selection_ready", "selection_branch",
    "candidate_reference_native_index", "candidate_pending_native_index", "candidate_raw_full_id_u32",
    "candidate_actual_full_id_u32", "candidate_army_identity", "roster_count_raw_i32",
    "roster_data_present", "roster_data_identity", "roster_ready", "occurrences", "mappers", "count_inputs"}
_OCCURRENCE = _STATE | {"native_index", "raw_full_id_u32", "resolution", "mapper_index"}
_MAPPER = _STATE | {"native_index", "arrg_identity", "kind_14c_raw_i32", "data_count_raw_i32",
    "first_data_record_identity", "first_regi_full_id_u32", "selected_regi_resolution",
    "selected_regi_magic_14_raw_u32", "selected_regi_identity_valid", "count_input_index",
    "return_selection_ready", "return_selection", "fallback_regi_identity", "returned_regi_identity", "returned_regi_full_id_u32",
    "returned_regi_magic_14_raw_u32", "returned_state_138_raw_i32", "return_basis"}
_COUNT = _STATE | {"native_index", "regi_identity", "count_base_128_raw_i32", "chunks"}
_CHUNK = {"physical_index", "maximum_00_raw_i32", "current_04_raw_i32", "state_18_raw_i32"}


def _string(value: object, name: str, *, nullable: bool = True) -> None:
    if value is None and nullable:
        return
    if type(value) is not str:
        raise ValueError(f"{name} must be text or null")


def _state(row: dict, name: str) -> None:
    if row["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(f"{name}.status is malformed")
    _boolean(row["ready"], name + ".ready", nullable=False)
    _string(row["unavailable_reason"], name + ".unavailable_reason")


def _array(value: object, name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return value


def _ordinal(row: dict, index: int, name: str) -> None:
    if _integer(row["native_index"], name + ".native_index", nullable=False) != index:
        raise ValueError(f"{name} native order is malformed")


def normalize_current_candidate_detachment_mapper_inputs_v1(value: object) -> dict | None:
    """Preserve typed partial operands, unsigned references, repeats, and optional absence."""
    if value is None:
        return None
    top = _object(value, _TOP, "current candidate detachment mapper root")
    _state(top, "current candidate detachment mapper root")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("current candidate detachment mapper schema_version must equal 1")
    if (top["source"] != "native_current_candidate_detachment_mapper_inputs"
            or top["stage"] != "observed_current_first_candidate_mapper_seed"):
        raise ValueError("current candidate detachment mapper source/stage is malformed")
    for field in ("selection_ready", "roster_ready"):
        _boolean(top[field], field, nullable=False)
    if top["selection_branch"] not in {None, "first_valid_current_receiver", "not_called"}:
        raise ValueError("current candidate detachment mapper selection branch is malformed")
    for field in ("candidate_reference_native_index", "candidate_pending_native_index", "roster_count_raw_i32"):
        _integer(top[field], field)
    for field in ("candidate_raw_full_id_u32", "candidate_actual_full_id_u32"):
        _integer(top[field], field, unsigned=True)
    _boolean(top["roster_data_present"], "roster_data_present")
    for field in ("candidate_army_identity", "roster_data_identity"):
        _string(top[field], field)
    for index, raw in enumerate(_array(top["occurrences"], "occurrences")):
        row = _object(raw, _OCCURRENCE, "candidate ArRg occurrence")
        _state(row, "candidate ArRg occurrence")
        _ordinal(row, index, "candidate ArRg occurrence")
        requested = _integer(row["raw_full_id_u32"], "occurrence.raw_full_id_u32", unsigned=True)
        _resolution(row["resolution"], requested, "candidate ArRg resolution")
        _integer(row["mapper_index"], "occurrence.mapper_index")
    for index, raw in enumerate(_array(top["mappers"], "mappers")):
        row = _object(raw, _MAPPER, "physical ArRg mapper")
        _state(row, "physical ArRg mapper")
        _ordinal(row, index, "physical ArRg mapper")
        _string(row["arrg_identity"], "mapper.arrg_identity", nullable=False)
        for field in ("kind_14c_raw_i32", "data_count_raw_i32", "count_input_index", "returned_state_138_raw_i32"):
            _integer(row[field], "mapper." + field)
        for field in ("first_data_record_identity", "fallback_regi_identity", "returned_regi_identity"):
            _string(row[field], "mapper." + field)
        for field in ("first_regi_full_id_u32", "selected_regi_magic_14_raw_u32",
                      "returned_regi_full_id_u32", "returned_regi_magic_14_raw_u32"):
            _integer(row[field], "mapper." + field, unsigned=True)
        for field in ("selected_regi_identity_valid", "return_selection_ready"):
            _boolean(row[field], "mapper." + field, nullable=field != "return_selection_ready")
        if row["return_selection"] not in {None, "selected_regi", "native_fallback"}:
            raise ValueError("mapper.return_selection is malformed")
        if row["return_basis"] != "source2A977A0_from_same_capture_raw_operands":
            raise ValueError("mapper return basis is malformed")
        if row["selected_regi_resolution"] is not None:
            requested = 0xFFFFFFFF if row["data_count_raw_i32"] == 0 else row["first_regi_full_id_u32"]
            _resolution(row["selected_regi_resolution"], requested, "selected persistent Regi resolution")
    for index, raw in enumerate(_array(top["count_inputs"], "count_inputs")):
        row = _object(raw, _COUNT, "physical persistent Regi count")
        _state(row, "physical persistent Regi count")
        _ordinal(row, index, "physical persistent Regi count")
        _string(row["regi_identity"], "count.regi_identity", nullable=False)
        _integer(row["count_base_128_raw_i32"], "count.count_base_128_raw_i32")
        seen = set()
        for raw_chunk in _array(row["chunks"], "count.chunks"):
            chunk = _object(raw_chunk, _CHUNK, "physical count chunk")
            physical = _integer(chunk["physical_index"], "chunk.physical_index", nullable=False)
            if physical not in range(7) or physical in seen:
                raise ValueError("count physical chunk indices are malformed")
            seen.add(physical)
            for field in ("maximum_00_raw_i32", "current_04_raw_i32", "state_18_raw_i32"):
                _integer(chunk[field], "chunk." + field)
    return deepcopy(top)
