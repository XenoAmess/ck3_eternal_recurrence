"""Strict, optional transport for each standalone current 2633FF0 DATA seed."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import _boolean, _integer, _object, _text

_STATE = {"status", "ready", "unavailable_reason"}
_TOP = _STATE | {"schema_version", "source", "stage", "selection_ready", "roster_ready",
    "current_date_storage_raw64", "primary_receiver_identity", "canonical_pending_vtable_identity",
    "ready_pending_callback_identity", "candidate_occurrences", "incoming"}
_CANDIDATE = _STATE | {"native_index", "raw_full_id_u32", "resolution", "magic_14_raw_u32",
    "incoming_valid", "incoming_index"}
_INCOMING = _STATE | {"native_index", "arrg_identity", "arrg_full_id_u32", "army_full_id_140_u32",
    "unit_full_id_124_u32", "army_resolution", "unit_resolution", "passed_province_identity",
    "data_pointer_identity", "data_count_raw_i32", "captured_cursor_identity", "captured_end_identity",
    "data_ready", "character_full_id_148_u32", "character_resolution", "character_pointer_1b8_present",
    "character_pointer_1b8_identity", "data_occurrences", "physical_chunks", "association_inputs",
    "owner_inputs", "date_inputs", "pending"}
_DATA = _STATE | {"native_index", "record_identity", "raw_regi_full_id_u32", "data_ordinal_raw_i32",
    "held_fallback_regi_identity", "resolution", "magic_14_raw_u32", "identity_valid",
    "physical_chunk_present", "physical_chunk_index"}
_CHUNK = _STATE | {"native_index", "chunk_identity", "maximum_00_raw_i32", "current_04_raw_i32",
    "owner_08_raw_u32", "ordinal_0c_raw_i32", "association_10_raw_u32", "flag_14_raw_u8", "date_1c_raw64"}
_ASSOCIATION = _STATE | {"requested_full_id_u32", "arrg_resolution", "army_full_id_140_u32",
    "army_resolution", "unit_full_id_124_u32", "unit_resolution", "character_full_id_174_u32",
    "character_resolution", "context_pointer_identity", "context_count_0c_raw_u32"}
_OWNER = _STATE | {"requested_full_id_u32", "resolution", "state_138_raw_i32", "definition_identity",
    "definition_magic_38_raw_u32", "origin_identity", "origin_magic_85c_raw_u32"}
_DATE = _STATE | {"association_full_id_u32", "owner_full_id_u32", "unit_identity", "source_origin_identity",
    "source_origin_magic_85c_raw_u32", "capital_origin_identity", "capital_origin_magic_85c_raw_u32",
    "output_date_raw64", "basis"}
_PENDING = _STATE | {"header_identity", "buffer_identity", "capacity_08_raw_i32", "count_0c_raw_i32",
    "allocator_identity", "records"}
_RECORD = _STATE | {"native_index", "record_identity", "vtable_identity", "slot0_target_identity",
    "owner_08_raw_u32", "ordinal_0c_raw_i32"}
_RESOLUTION = _STATE | {"requested_full_id_u32", "registry_loaded", "registry_capacity_u32",
    "registry_index_u32", "indexed_identity", "indexed_full_id_u32", "selection", "used_fallback",
    "object_identity", "selected_full_id_u32"}


def _state(row: dict, name: str) -> None:
    if row["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(f"{name}.status is malformed")
    _boolean(row["ready"], name + ".ready", nullable=False)
    if row["unavailable_reason"] is not None and type(row["unavailable_reason"]) is not str:
        raise ValueError(f"{name}.unavailable_reason must be text or null")


def _resolution(value: object, requested: int | None, name: str) -> None:
    row = _object(value, _RESOLUTION, name)
    _state(row, name)
    _numbers(row, ("requested_full_id_u32", "registry_capacity_u32", "registry_index_u32",
                  "indexed_full_id_u32", "selected_full_id_u32"), name, unsigned=True)
    for field in ("registry_loaded", "used_fallback"):
        _boolean(row[field], name + "." + field)
    _identities(row, ("indexed_identity", "object_identity"), name)
    if row["selection"] not in {None, "registry_full_id", "native_fallback"}:
        raise ValueError(f"{name}.selection is malformed")


def _rows(value: object, name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an ordered array")
    return value


def _row(value: object, fields: set[str], name: str) -> dict:
    row = _object(value, fields, name)
    _state(row, name)
    return row


def _identities(row: dict, fields: tuple[str, ...], name: str) -> None:
    for field in fields:
        value = row[field]
        _text(value, name + "." + field)
        if value is not None and (not value.startswith("native:")
                                  or not value[7:].isascii() or not value[7:].isdigit()
                                  or not 0 <= int(value[7:]) < 1 << 64):
            raise ValueError(f"{name}.{field} native identity is malformed")


def _numbers(row: dict, fields: tuple[str, ...], name: str, *, unsigned: bool = False,
             bits: int = 32) -> None:
    for field in fields:
        _integer(row[field], name + "." + field, bits=bits, unsigned=unsigned)


def _ordinal(row: dict, index: int, name: str) -> None:
    if _integer(row["native_index"], name + ".native_index", nullable=False) != index:
        raise ValueError(f"{name} native occurrence order is malformed")


def normalize_current_detachment_data_inputs_v1(value: object) -> dict | None:
    """Validate raw shape without demanding operands from unselected branches.

    Absence is compatible with an older wire. Signed negative DATA counts and
    unavailable selected inputs remain explicit raw operands, never empty data.
    """
    if value is None:
        return None
    top = _row(value, _TOP, "current detachment DATA")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("current detachment DATA schema_version must equal 1")
    if (top["source"] != "native_current_detachment_data_inputs"
            or top["stage"] != "observed_current_incoming_2633ff0_seed"):
        raise ValueError("current detachment DATA source/stage is malformed")
    for field in ("selection_ready", "roster_ready"):
        _boolean(top[field], field, nullable=False)
    _numbers(top, ("current_date_storage_raw64",), "DATA", bits=64)
    _identities(top, ("primary_receiver_identity", "canonical_pending_vtable_identity",
                      "ready_pending_callback_identity"), "DATA")
    for index, raw in enumerate(_rows(top["candidate_occurrences"], "candidate occurrences")):
        row = _row(raw, _CANDIDATE, "candidate occurrence")
        _ordinal(row, index, "candidate occurrence")
        _numbers(row, ("raw_full_id_u32", "magic_14_raw_u32"), "candidate", unsigned=True)
        _resolution(row["resolution"], row["raw_full_id_u32"], "candidate resolution")
        _boolean(row["incoming_valid"], "candidate.incoming_valid")
        _numbers(row, ("incoming_index",), "candidate")
    for index, raw in enumerate(_rows(top["incoming"], "incoming")):
        incoming = _row(raw, _INCOMING, "incoming DATA seed")
        _ordinal(incoming, index, "incoming DATA seed")
        _identities(incoming, ("arrg_identity", "passed_province_identity", "data_pointer_identity",
            "captured_cursor_identity", "captured_end_identity", "character_pointer_1b8_identity"), "incoming")
        _numbers(incoming, ("arrg_full_id_u32", "army_full_id_140_u32", "unit_full_id_124_u32",
            "character_full_id_148_u32"), "incoming", unsigned=True)
        _resolution(incoming["army_resolution"], incoming["army_full_id_140_u32"], "incoming Army resolution")
        _resolution(incoming["unit_resolution"], incoming["unit_full_id_124_u32"], "incoming Unit resolution")
        _numbers(incoming, ("data_count_raw_i32",), "incoming")
        _boolean(incoming["data_ready"], "incoming.data_ready", nullable=False)
        _boolean(incoming["character_pointer_1b8_present"], "incoming.character_pointer_1b8_present")
        if incoming["character_resolution"] is not None:
            resolution = incoming["character_resolution"]
            requested = (incoming["character_full_id_148_u32"] if incoming["character_full_id_148_u32"] != 0xFFFFFFFF
                         else resolution.get("requested_full_id_u32"))
            _resolution(resolution, requested, "suffix Character resolution")
        for position, raw_data in enumerate(_rows(incoming["data_occurrences"], "DATA occurrences")):
            row = _row(raw_data, _DATA, "DATA occurrence")
            _ordinal(row, position, "DATA occurrence")
            _identities(row, ("record_identity", "held_fallback_regi_identity"), "DATA occurrence")
            _numbers(row, ("raw_regi_full_id_u32", "magic_14_raw_u32"), "DATA occurrence", unsigned=True)
            _numbers(row, ("data_ordinal_raw_i32", "physical_chunk_index"), "DATA occurrence")
            _boolean(row["identity_valid"], "DATA occurrence.identity_valid")
            _boolean(row["physical_chunk_present"], "DATA occurrence.physical_chunk_present")
            _resolution(row["resolution"], row["raw_regi_full_id_u32"], "DATA Regi resolution")
        for position, raw_chunk in enumerate(_rows(incoming["physical_chunks"], "physical chunks")):
            row = _row(raw_chunk, _CHUNK, "physical chunk")
            _ordinal(row, position, "physical chunk")
            _identities(row, ("chunk_identity",), "physical chunk")
            _numbers(row, ("maximum_00_raw_i32", "current_04_raw_i32", "ordinal_0c_raw_i32"), "chunk")
            _numbers(row, ("owner_08_raw_u32", "association_10_raw_u32"), "chunk", unsigned=True)
            _numbers(row, ("flag_14_raw_u8",), "chunk", unsigned=True, bits=8)
            _numbers(row, ("date_1c_raw64",), "chunk", bits=64)
        for raw_association in _rows(incoming["association_inputs"], "association inputs"):
            row = _row(raw_association, _ASSOCIATION, "association source")
            _numbers(row, ("requested_full_id_u32", "army_full_id_140_u32", "unit_full_id_124_u32",
                "character_full_id_174_u32", "context_count_0c_raw_u32"), "association", unsigned=True)
            _identities(row, ("context_pointer_identity",), "association")
            for field, requested in (("arrg_resolution", "requested_full_id_u32"),
                ("army_resolution", "army_full_id_140_u32"), ("unit_resolution", "unit_full_id_124_u32"),
                ("character_resolution", "character_full_id_174_u32")):
                _resolution(row[field], row[requested], "association." + field)
        for raw_owner in _rows(incoming["owner_inputs"], "owner inputs"):
            row = _row(raw_owner, _OWNER, "owner source")
            _numbers(row, ("requested_full_id_u32", "definition_magic_38_raw_u32", "origin_magic_85c_raw_u32"), "owner", unsigned=True)
            _numbers(row, ("state_138_raw_i32",), "owner")
            _identities(row, ("definition_identity", "origin_identity"), "owner")
            _resolution(row["resolution"], row["requested_full_id_u32"], "owner Regi resolution")
        for raw_date in _rows(incoming["date_inputs"], "date inputs"):
            row = _row(raw_date, _DATE, "date source")
            _numbers(row, ("association_full_id_u32", "owner_full_id_u32", "source_origin_magic_85c_raw_u32",
                "capital_origin_magic_85c_raw_u32"), "date", unsigned=True)
            _numbers(row, ("output_date_raw64",), "date", bits=64)
            _identities(row, ("unit_identity", "source_origin_identity", "capital_origin_identity"), "date")
            if row["basis"] is not None and type(row["basis"]) is not str:
                raise ValueError("date.basis must be text or null")
        pending = _row(incoming["pending"], _PENDING, "pending header")
        _identities(pending, ("header_identity", "buffer_identity", "allocator_identity"), "pending")
        _numbers(pending, ("capacity_08_raw_i32", "count_0c_raw_i32"), "pending")
        for position, raw_record in enumerate(_rows(pending["records"], "pending records")):
            row = _row(raw_record, _RECORD, "pending record")
            _ordinal(row, position, "pending record")
            _identities(row, ("record_identity", "vtable_identity", "slot0_target_identity"), "pending record")
            _numbers(row, ("owner_08_raw_u32",), "pending record", unsigned=True)
            _numbers(row, ("ordinal_0c_raw_i32",), "pending record")
    return deepcopy(top)
