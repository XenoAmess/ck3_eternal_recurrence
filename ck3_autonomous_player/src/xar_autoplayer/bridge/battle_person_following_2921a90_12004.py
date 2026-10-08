"""Source-closed actual4 2921A90 operands, independent of its conditional gap.

Physical list items each contribute one unit request, including empty PCs.
This contract invokes no classifier, evaluator, initializer or numerical merger;
the selected Model destination is provenance, not a fresh stage baseline.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)
from .battle_person_carrier_direct_12004 import _values_q64
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_2921a90"
SCHEMA = "xar.ck3.person-following-2921a90-12004-v1"
CONDITIONAL_GAP = "conditional_modifier_2a38030_2872300_unobserved"
_MAGIC = 0x446F6D69
_SENTINEL = 0xFFFFFFFF
_POINTER_FIELDS = (
    "selected_model_identity", "character_identity", "destination_pc_identity",
    "carrier_identity", "registry_identity", "registry_slots_identity",
    "selected_object_identity", "direct_array_identity", "conditional_definition_identity",
)
_UNSIGNED_FIELDS = (
    "character_id", "requested_full_id_u32", "registry_count_u32",
    "selected_full_id_u32", "selected_magic_u32", "conditional_occurrence_count",
)
_SIGNED_FIELDS = ("direct_count_i32", "conditional_b8c_count_i32", "conditional_bbc_count_i32")
_FIELDS = {
    "schema", "build_version", "executable_sha256", "ready", "reason",
    "carrier_present", "resolution_selection", "admitted", "direct_ready",
    "direct_reason", "direct_rows", "conditional_ready", "conditional_reason",
    *_POINTER_FIELDS, *_UNSIGNED_FIELDS, *_SIGNED_FIELDS,
}
_ROW_FIELDS = {
    "native_index", "ready", "reason", "object_identity", "source_pc_identity",
    "pc_count_i32", "properties", "weight_q100000",
}


def _availability(ready: bool, reason: str | None, field: str) -> None:
    if (ready and reason is not None) or (not ready and not reason):
        raise ValueError(field + " readiness and reason disagree")


def _normalize_row(value: object, field: str) -> dict:
    raw = _dict(value, field, _ROW_FIELDS)
    row = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "object_identity": _string(raw["object_identity"], field + ".object_identity", optional=True),
        "source_pc_identity": _string(raw["source_pc_identity"], field + ".source_pc_identity", optional=True),
        "pc_count_i32": _number(raw["pc_count_i32"], field + ".pc_count_i32", 32),
        "weight_q100000": _integer(raw["weight_q100000"], field + ".weight_q100000", 64),
    }
    if row["weight_q100000"] != 100000:
        raise ValueError(field + " weight disagrees with the native unit call")
    block = raw["properties"]
    if block is not None:
        block = _dict(block, field + ".properties", {"keys_u16", "values_q64"})
        block = {
            "keys_u16": _numbers(block["keys_u16"], field + ".properties.keys_u16", 16, unsigned=True),
            "values_q64": _values_q64(block["values_q64"], field + ".properties.values_q64"),
        }
    row["properties"] = block
    _availability(row["ready"], row["reason"], field)
    if row["ready"]:
        count = row["pc_count_i32"]
        if (count is None or count < 0 or row["object_identity"] is None
                or row["source_pc_identity"] is None or block is None
                or block["keys_u16"] is None or block["values_q64"] is None
                or len(block["keys_u16"]) != count or len(block["values_q64"]) != count):
            raise ValueError(field + " complete row lacks its copied PC operands")
    return row


def normalize_person_following_2921a90_12004(value: object) -> dict | None:
    """Validate the optional whole leaf while retaining independently read rows."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, _FIELDS)
    if raw["schema"] != SCHEMA:
        raise ValueError(FIELD_NAME + " schema mismatch")
    build = require_exact_native_build(raw["build_version"], raw["executable_sha256"])
    if build != CK3_12004:
        raise ValueError(FIELD_NAME + " requires the actual4 source")
    result = {
        "schema": SCHEMA, "build_version": build.game_version,
        "executable_sha256": build.executable_sha256,
        "resolution_selection": _string(raw["resolution_selection"], FIELD_NAME + ".resolution_selection"),
    }
    for key in ("ready", "direct_ready", "conditional_ready"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    for key in ("carrier_present", "admitted"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in ("reason", "direct_reason", "conditional_reason", *_POINTER_FIELDS):
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in _UNSIGNED_FIELDS:
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32, unsigned=True)
    for key in _SIGNED_FIELDS:
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32)
    if result["resolution_selection"] not in ("mapped_id", "fallback", "unavailable"):
        raise ValueError(FIELD_NAME + " unknown registry selection")
    if not isinstance(raw["direct_rows"], list):
        raise ValueError(FIELD_NAME + ".direct_rows must be an ordered list")
    rows = [_normalize_row(row, f"{FIELD_NAME}.direct_rows[{index}]")
            for index, row in enumerate(raw["direct_rows"])]
    result["direct_rows"] = rows
    if [row["native_index"] for row in rows] != list(range(len(rows))):
        raise ValueError(FIELD_NAME + " rows changed their physical native order")
    for ready_key, reason_key in (("ready", "reason"), ("direct_ready", "direct_reason"),
                                  ("conditional_ready", "conditional_reason")):
        _availability(result[ready_key], result[reason_key], FIELD_NAME + "." + ready_key)
    if result["ready"] != (result["direct_ready"] and result["conditional_ready"]):
        raise ValueError(FIELD_NAME + " whole readiness disagrees with its two families")
    if result["conditional_occurrence_count"] not in (None, 0):
        raise ValueError(FIELD_NAME + " conditional occurrences are not observed in this packet")
    if result["conditional_ready"] != (result["conditional_occurrence_count"] == 0):
        raise ValueError(FIELD_NAME + " conditional readiness lacks its known empty family")

    admitted = result["admitted"]
    magic, full_id = result["selected_magic_u32"], result["selected_full_id_u32"]
    if admitted is False:
        gate_failed = (magic is not None and magic != _MAGIC) or (magic == _MAGIC and full_id == _SENTINEL)
        if not gate_failed or not result["ready"] or rows:
            raise ValueError(FIELD_NAME + " known-zero helper lacks an observed failed native gate")
    elif admitted is True:
        if magic != _MAGIC or full_id is None or full_id == _SENTINEL:
            raise ValueError(FIELD_NAME + " admitted object disagrees with native magic/full ID")
        count = result["direct_count_i32"]
        if result["direct_ready"] and (
                count is None or count < 0 or len(rows) != count
                or any(not row["ready"] for row in rows)):
            raise ValueError(FIELD_NAME + " complete direct family lacks its complete physical rows")
        if count is not None and (count < 0 and rows or count >= 0 and len(rows) > count):
            raise ValueError(FIELD_NAME + " observed rows disagree with the direct count")
        b8c, bbc = result["conditional_b8c_count_i32"], result["conditional_bbc_count_i32"]
        if b8c is not None and b8c != 0 and bbc is not None:
            raise ValueError(FIELD_NAME + " BBC was undemanded after a nonzero B8C")
        if result["conditional_ready"] and (b8c != 0 or bbc != 0):
            raise ValueError(FIELD_NAME + " known empty conditional family lacks both observed zero counts")
        demanded = b8c is not None and (b8c != 0 or bbc is not None and bbc != 0)
        if demanded and (result["conditional_ready"] or result["conditional_reason"] != CONDITIONAL_GAP):
            raise ValueError(FIELD_NAME + " demanded conditional family lost its named source gap")
    elif result["direct_ready"] or result["conditional_ready"]:
        raise ValueError(FIELD_NAME + " unread native admission cannot release a complete family")
    return result


def _joined_leaf(section: Mapping | None) -> dict:
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_following_2921a90_12004(section.get(FIELD_NAME))
    if leaf is None:
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if character != leaf["character_id"]:
        raise ValueError(FIELD_NAME + " full CharacterID join unavailable or mismatched")
    return leaf


def _request(row: dict):
    # This reused dataclass carries operands only; no historical merger credit.
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    block = row["properties"]
    return NativeWeightedContributionRequest12003(
        source_ordinal=row["native_index"], source_name=FIELD_NAME + "_12004",
        first_row_index=0, row_count=1, definition_identity=row["source_pc_identity"],
        base_property_block={"keys_count": row["pc_count_i32"],
                             "keys_u16": block["keys_u16"], "values_q64": block["values_q64"]},
        weight_q64=row["weight_q100000"],
    )


def emit_following_2921a90_requests_from_current_source_inputs_12004(section: Mapping | None) -> tuple:
    """Release all physical direct calls only when the whole helper is known."""
    leaf = _joined_leaf(section)
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + leaf["reason"])
    return tuple(_request(row) for row in leaf["direct_rows"])


def emit_following_2921a90_direct_requests_from_current_source_inputs_12004(section: Mapping | None) -> tuple:
    """Release the direct family independently of a demanded conditional gap."""
    leaf = _joined_leaf(section)
    if not leaf["direct_ready"]:
        raise ValueError("Required native input unavailable: " + leaf["direct_reason"])
    return tuple(_request(row) for row in leaf["direct_rows"])


def emit_following_2921a90_row_requests_from_current_source_inputs_12004(
    section: Mapping | None, native_index: int,
) -> tuple:
    """Release one independently complete row at its original physical index."""
    leaf = _joined_leaf(section)
    selected = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
    row = next((row for row in leaf["direct_rows"] if row["native_index"] == selected), None)
    if row is None:
        raise ValueError(f"Required native input unavailable: {FIELD_NAME} row {selected} unobserved")
    if not row["ready"]:
        raise ValueError("Required native input unavailable: " + row["reason"])
    return (_request(row),)
