"""Literal actual4 Government bit19 input after the ordered Person helper.

A ready positive bit only demands the later conditional branch. Its numerical
contribution and complete Person/Entry remain outside this observation.
"""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _string,
)
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_291ce01_government_gate"
SCHEMA = "xar.ck3.person-government-gate-12004-v1"
_POINTERS = {
    "character_identity", "selected_model_identity", "registry_identity",
    "character_fallback_identity", "government_identity",
}
_STEP_POINTERS = {
    "character_identity", "death_context_identity", "living_context_identity",
    "related_context_identity", "registry_slots_identity", "candidate_identity",
    "selected_character_identity",
}
_STEP_NUMBERS = {
    "magic_u32", "full_id_u32", "related_full_id_u32",
    "registry_count_u32", "candidate_full_id_u32",
}
_BOOLEANS = {"model_owner_matches", "bit19_set", "branch_admitted", "known_no_contribution"}


def _step(value, index):
    field = f"{FIELD_NAME}.steps[{index}]"
    raw = _dict(value, field, {
        "native_index", "resolution_selection", *_STEP_POINTERS, *_STEP_NUMBERS,
    })
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
              "resolution_selection": _string(raw["resolution_selection"], field + ".resolution_selection")}
    for key in _STEP_POINTERS:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in _STEP_NUMBERS:
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    if result["native_index"] != index:
        raise ValueError(field + " changed native resolution order")
    if result["resolution_selection"] not in {"unavailable", "mapped", "fallback"}:
        raise ValueError(field + " unknown Character resolution selection")
    return result


def normalize_person_government_gate_12004(value: object) -> dict | None:
    """Preserve raw flags and every partial resolution step in original order."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, {
        "schema", "build_version", "executable_sha256", "ready", "reason",
        "character_id", "selection", "flags_40_u32", "steps", *_POINTERS, *_BOOLEANS,
    })
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {
        "schema": SCHEMA, "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "ready": _boolean(raw["ready"], FIELD_NAME + ".ready"),
        "reason": _string(raw["reason"], FIELD_NAME + ".reason", optional=True),
        "character_id": _number(raw["character_id"], FIELD_NAME + ".character_id", 32, unsigned=True),
        "selection": _string(raw["selection"], FIELD_NAME + ".selection"),
        "flags_40_u32": _number(raw["flags_40_u32"], FIELD_NAME + ".flags_40_u32", 32, unsigned=True),
    }
    for key in _POINTERS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in _BOOLEANS:
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key, optional=True)
    if result["selection"] not in {
        "unavailable", "living_context", "death_context",
        "invalid_character_fallback", "selected_null_fallback",
    }:
        raise ValueError(FIELD_NAME + " unknown Government selection")
    if not isinstance(raw["steps"], list):
        raise ValueError(FIELD_NAME + ".steps must retain native resolution order")
    result["steps"] = [_step(step, index) for index, step in enumerate(raw["steps"])]
    if result["ready"]:
        flags = result["flags_40_u32"]
        if flags is None or result["government_identity"] is None or result["reason"] is not None:
            raise ValueError(FIELD_NAME + " ready gate lacks its literal returned flags")
        admitted = bool((flags >> 19) & 1)
        if (result["bit19_set"] is not admitted or result["branch_admitted"] is not admitted
                or result["known_no_contribution"] is not (not admitted)):
            raise ValueError(FIELD_NAME + " gate differs from actual DWORD40 bit19")
    return result
