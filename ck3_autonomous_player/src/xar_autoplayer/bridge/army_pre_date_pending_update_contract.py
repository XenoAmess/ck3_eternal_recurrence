"""Strict raw transport for the current pre-date pending-list update inputs.

This family publishes operands; the native2A92320 mutator is never called.
Generic full-generation resolution/reference validation reuses the same-query
roster family without modifying its shapes or earlier readiness.
"""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import (
    _ordered,
    _primitive,
    _references,
    _resolution,
    _typed as _roster_typed,
)

_STATUS = {"status": "string", "ready": "bool", "unavailable_reason": "string"}
_SHAPES = {
    "PendingArRg": {
        **_STATUS, "native_index": "i32", "raw_full_id_u32": "u32?",
        "arrg_resolution": "OperandResolution", "current_38_raw_i32": "i32?",
        "contract_id_144_raw_u32": "u32?", "contract_resolution": "OperandResolution",
        "contract_flag_b9_raw_u8": "u8?", "state_14c_raw_i32": "i32?",
        "original_data_identity": "identity?", "original_data_present": "bool?",
        "first_persistent_id_raw_u32": "u32?", "persistent_resolution": "OperandResolution",
        "persistent_war_id_13c_raw_u32": "u32?", "war_resolution": "OperandResolution",
        "war_magic_0c_raw_u32": "u32?", "append_to_pending": "bool?", "append_full_id_u32": "u32?",
    },
    "PendingSetup": {
        **_STATUS, "entries_identity": "identity?", "entries_present": "bool?",
        "mask_raw_i32": "i32?", "target_army_full_id_u32": "u32?", "hash_raw_u32": "u32?",
        "home_slot_i64": "i64?", "terminal_physical_slot_i64": "i64?", "probes": "PendingProbe[]",
        "existing_key": "bool?", "existing_references": "RawReferences", "map_count_raw_i32": "i32?",
        "insertion_tail_raw_u8": "u8?", "insertion_threshold_bits_u32": "u32?",
    },
    "PendingOccurrence": {
        **_STATUS, "native_index": "i32", "raw_full_id_u32": "u32?",
        "original_army_resolution": "OperandResolution", "combat_id_128_raw_u32": "u32?",
        "combat_resolution": "OperandResolution", "combat_magic_0c_raw_u32": "u32?",
        "army_counter_5c_raw_i32": "i32?", "pending_mutator_selected": "bool?",
        "pending_setup": "PendingSetup", "original_arrg_references": "RawReferences",
        "arrg_occurrences": "PendingArRg[]",
    },
    "Inputs": {
        **_STATUS, "schema_version": "i32=1", "source": "string=native_current_pre_date_pending_update_inputs",
        "stage": "string=observed_current_pre_date_pending_update_inputs", "manager_loaded": "bool?",
        "manager_identity": "identity?", "original_roster": "RawReferences", "removal_queue": "RawReferences",
        "occurrences": "PendingOccurrence[]", "raw_roster_references_ready": "bool", "source_operands_ready": "bool",
        "actual_pre_date_callback_ready": "bool=false", "actual_tomorrow_roster_ready": "bool=false",
        "full_daily_assault_ready": "bool=false", "full_monthly_ready": "bool=false",
    },
}
_REUSED = {"OperandResolution", "RawReferences", "PendingProbe"}


def _typed(value: object, kind: str, name: str) -> None:
    if kind.endswith("?"):
        if value is None:
            return
        kind = kind[:-1]
    if kind.endswith("[]"):
        if type(value) is not list:
            raise ValueError(f"{name} must retain its native array")
        for index, item in enumerate(value):
            _typed(item, kind[:-2], f"{name}[{index}]")
        return
    if kind in _REUSED:
        _roster_typed(value, kind, name)
        return
    if "=" in kind:
        base, literal = kind.split("=", 1)
        _typed(value, base, name)
        expected = literal if base == "string" else literal == "true" if base == "bool" else int(literal)
        if value != expected:
            raise ValueError(f"{name} exact source value is malformed")
        return
    if kind in _SHAPES:
        fields = _SHAPES[kind]
        if type(value) is not dict or set(value) != set(fields):
            raise ValueError(f"{name} schema is malformed")
        for key, field_type in fields.items():
            _typed(value[key], field_type, name + "." + key)
        if value["status"] not in {"available", "partial", "unavailable"}:
            raise ValueError(f"{name}.status is malformed")
        if value["ready"] != (value["status"] == "available") or value["ready"] == bool(value["unavailable_reason"]):
            raise ValueError(f"{name} status disagrees with readiness/reason")
        return
    _primitive(value, kind, name)


def normalize_current_pre_date_pending_update_inputs_v1(value: object) -> dict | None:
    """Normalize an optional leaf, preserving legal zero, missing inputs and repeats."""
    if value is None:
        return None
    name = "current_pre_date_pending_update_inputs_v1"
    _typed(value, "Inputs", name)
    _references(value["original_roster"], name + ".original_roster")
    _references(value["removal_queue"], name + ".removal_queue")
    raw_rows = value["original_roster"]["occurrences"]
    rows = value["occurrences"]
    if [(r["native_index"], r["raw_full_id_u32"]) for r in rows] != [
        (r["native_index"], r["raw_full_id_u32"]) for r in raw_rows
    ]:
        raise ValueError("pre-date pending inputs filtered or relabeled the original roster")
    for row in rows:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row["original_army_resolution"], row["raw_full_id_u32"], prefix + ".original_army_resolution")
        _resolution(row["combat_resolution"], row["combat_id_128_raw_u32"], prefix + ".combat_resolution")
        setup = row["pending_setup"]
        _ordered(setup["probes"], prefix + ".pending_setup.probes")
        _references(setup["existing_references"], prefix + ".pending_setup.existing_references")
        refs = row["original_arrg_references"]
        _references(refs, prefix + ".original_arrg_references")
        _ordered(row["arrg_occurrences"], prefix + ".arrg_occurrences", refs["count_raw_i32"])
        if [(r["native_index"], r["raw_full_id_u32"]) for r in row["arrg_occurrences"]] != [
            (r["native_index"], r["raw_full_id_u32"]) for r in refs["occurrences"]
        ]:
            raise ValueError("pre-date pending inputs filtered or relabeled original ArRg occurrences")
        for arrg in row["arrg_occurrences"]:
            where = prefix + f'.arrg_occurrences[{arrg["native_index"]}]'
            for field, requested in (
                ("arrg_resolution", "raw_full_id_u32"),
                ("contract_resolution", "contract_id_144_raw_u32"),
                ("persistent_resolution", "first_persistent_id_raw_u32"),
                ("war_resolution", "persistent_war_id_13c_raw_u32"),
            ):
                _resolution(arrg[field], arrg[requested], where + "." + field)
    return deepcopy(value)
