"""Strict optional current actual4 Character detachment suffix operands."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_active_table_contract import _boolean, _integer, _object, _text

_STATE = {"status", "ready", "unavailable_reason"}
_LIMITS = {"actual_callback_observed", "actual_resource_return_observed",
    "actual_after_state_observed", "full_detachment_transition_ready",
    "full_daily_ready", "full_monthly_ready",
    "full_character_detachment_suffix_ready", "future_date_ready"}
_TOP = _STATE | _LIMITS | {"schema_version", "source", "stage",
    "seed_selection_ready", "seed_roster_ready", "current_date_storage_raw64",
    "source_parent_identity", "requests"}
_REQUEST = _STATE | {"seed_incoming_native_index", "arrg_identity",
    "character_full_id_148_u32", "character_resolution", "passed_province_identity",
    "current_extension_1b8_present", "current_extension_1b8_identity",
    "extension_f8_raw_u32", "extension_100_raw64", "extension_reset_inputs_ready",
    "source_chain_ready", "arrg_resolution", "army_full_id_140_u32",
    "army_resolution", "unit_full_id_124_u32", "unit_resolution"}
_RESOLUTION = _STATE | {"requested_full_id_u32", "registry_loaded",
    "registry_capacity_u32", "registry_index_u32", "indexed_identity",
    "indexed_full_id_u32", "selection", "used_fallback", "object_identity",
    "selected_full_id_u32"}


def _state(row: dict, name: str) -> None:
    if row["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(f"{name}.status is malformed")
    _boolean(row["ready"], name + ".ready", nullable=False)
    _text(row["unavailable_reason"], name + ".unavailable_reason")


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


def _resolution(value: object, name: str) -> None:
    row = _row(value, _RESOLUTION, name)
    for field in ("requested_full_id_u32", "registry_capacity_u32",
            "registry_index_u32", "indexed_full_id_u32", "selected_full_id_u32"):
        _integer(row[field], name + "." + field, unsigned=True)
    for field in ("registry_loaded", "used_fallback"):
        _boolean(row[field], name + "." + field)
    for field in ("indexed_identity", "object_identity"):
        _identity(row[field], name + "." + field)
    if row["selection"] not in {None, "registry_full_id", "native_fallback"}:
        raise ValueError(f"{name}.selection is malformed")


def normalize_current_character_detachment_inputs_v1(value: object) -> dict | None:
    """Validate the observed family without gating independent current inputs.

    Absence/null is compatible with older wires. Unselected resolutions retain
    their full nullable object shape. A fallback's selected full ID and current
    extension before-values are optional context, not reset prerequisites.
    """
    if value is None:
        return None
    top = _row(value, _TOP, "current Character detachment")
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise ValueError("current Character detachment schema_version must equal 1")
    if (top["source"] != "native_current_character_detachment_inputs_12004"
            or top["stage"] != "observed_current_character_detachment_seed"):
        raise ValueError("current Character detachment source/stage is malformed")
    for field in ("seed_selection_ready", "seed_roster_ready"):
        _boolean(top[field], field, nullable=False)
    _integer(top["current_date_storage_raw64"], "Character.current_date_storage_raw64", bits=64)
    _identity(top["source_parent_identity"], "Character.source_parent_identity")
    for field in _LIMITS:
        if top[field] is not False:
            raise ValueError(f"Character.{field} must remain false")
    if not isinstance(top["requests"], list):
        raise ValueError("Character.requests must be an ordered array")
    for index, raw_request in enumerate(top["requests"]):
        name = f"Character.requests[{index}]"
        row = _row(raw_request, _REQUEST, name)
        _integer(row["seed_incoming_native_index"], name + ".seed_incoming_native_index",
                 nullable=False, nonnegative=True)
        for field in ("arrg_identity", "passed_province_identity", "current_extension_1b8_identity"):
            _identity(row[field], name + "." + field)
        for field in ("character_full_id_148_u32", "extension_f8_raw_u32",
                "army_full_id_140_u32", "unit_full_id_124_u32"):
            _integer(row[field], name + "." + field, unsigned=True)
        _integer(row["extension_100_raw64"], name + ".extension_100_raw64", bits=64)
        _boolean(row["current_extension_1b8_present"], name + ".current_extension_1b8_present")
        for field in ("extension_reset_inputs_ready", "source_chain_ready"):
            _boolean(row[field], name + "." + field, nullable=False)
        for field in ("character_resolution", "arrg_resolution", "army_resolution", "unit_resolution"):
            _resolution(row[field], name + "." + field)
    return deepcopy(top)
