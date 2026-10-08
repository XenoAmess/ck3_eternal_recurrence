"""Actual4 carrier source PC inputs; no complete person/context rebuild claim.

The reader's current physical PC is a numerical source, not a logical stage
baseline. See battle-person-next-direct-carrier-12004.md for the actual field
uses and initialized-default boundary. This module invokes no engine callback.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "carrier_1c8_b70_direct"
SCHEMA = "xar.ck3.person-carrier-direct-12004-v1"
_POINTER_FIELDS = (
    "selected_model_identity", "destination_pc_identity", "character_identity",
    "carrier_identity", "definition_identity", "table_identity",
    "selected_pc_identity",
)
_SIGNED_FIELDS = (
    "rank_i32", "row_count_i32", "default_guard_raw", "selected_pc_count_i32",
)
_FIELDS = {
    "schema", "build_version", "executable_sha256", "ready", "reason",
    "character_id", "carrier_present", "definition_magic_u32", "selection",
    "properties", "source_occurrence_count", "weight_q100000",
    *_POINTER_FIELDS, *_SIGNED_FIELDS,
}


def _values_q64(value: object, field: str) -> list[int] | None:
    """Decode native decimal strings and retain normalized signed64 integers."""
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list or null")
    result = []
    for index, item in enumerate(value):
        item_field = f"{field}[{index}]"
        if type(item) is str:
            digits = item[1:] if item.startswith("-") else item
            if not digits or not digits.isascii() or not digits.isdecimal():
                raise ValueError(f"{item_field} must be a native signed64 decimal string or integer")
            item = int(item, 10)
        result.append(_integer(item, item_field, 64))
    return result


def normalize_carrier_direct_12004(value: object) -> dict | None:
    """Normalize the optional raw numerical leaf, retaining partial observations."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, _FIELDS)
    if raw["schema"] != SCHEMA:
        raise ValueError(FIELD_NAME + " schema mismatch")
    build = require_exact_native_build(raw["build_version"], raw["executable_sha256"])
    if build != CK3_12004:
        raise ValueError(FIELD_NAME + " requires the actual4 source")
    result = {
        "schema": SCHEMA,
        "build_version": build.game_version,
        "executable_sha256": build.executable_sha256,
        "ready": _boolean(raw["ready"], FIELD_NAME + ".ready"),
        "reason": _string(raw["reason"], FIELD_NAME + ".reason", optional=True),
        "character_id": _number(raw["character_id"], FIELD_NAME + ".character_id", 32, unsigned=True),
        "carrier_present": _boolean(raw["carrier_present"], FIELD_NAME + ".carrier_present", optional=True),
        "definition_magic_u32": _number(raw["definition_magic_u32"], FIELD_NAME + ".definition_magic_u32", 32, unsigned=True),
        "selection": _string(raw["selection"], FIELD_NAME + ".selection"),
        "source_occurrence_count": _number(raw["source_occurrence_count"], FIELD_NAME + ".source_occurrence_count", 32, unsigned=True),
        "weight_q100000": _integer(raw["weight_q100000"], FIELD_NAME + ".weight_q100000", 64),
    }
    for key in _POINTER_FIELDS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in _SIGNED_FIELDS:
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32)
    if result["selection"] not in ("none", "mapped_row", "static_default_5d71200", "unavailable"):
        raise ValueError(FIELD_NAME + " unknown source selection")
    if result["source_occurrence_count"] not in (None, 0, 1):
        raise ValueError(FIELD_NAME + " source occurrence count must be 0, 1 or null")
    if result["weight_q100000"] != 100000:
        raise ValueError(FIELD_NAME + " weight disagrees with the actual unit append")
    block = raw["properties"]
    if block is not None:
        block = _dict(block, FIELD_NAME + ".properties", {"keys_u16", "values_q64"})
        block = {
            "keys_u16": _numbers(block["keys_u16"], FIELD_NAME + ".properties.keys_u16", 16, unsigned=True),
            "values_q64": _values_q64(block["values_q64"], FIELD_NAME + ".properties.values_q64"),
        }
    result["properties"] = block
    if result["ready"]:
        occurrence = result["source_occurrence_count"]
        if occurrence is None:
            raise ValueError(FIELD_NAME + " ready source lacks occurrence admission")
        if occurrence == 1:
            count = result["selected_pc_count_i32"]
            if (count is None or count <= 0 or block is None
                    or block["keys_u16"] is None or block["values_q64"] is None
                    or len(block["keys_u16"]) != count or len(block["values_q64"]) != count
                    or result["selected_pc_identity"] is None):
                raise ValueError(FIELD_NAME + " nonempty source lacks copied numerical inputs")
    return result


def emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004(
    section: Mapping | None,
) -> tuple:
    """Return the single bounded source request after the same-query Character join.

    The existing request dataclass has a historical 12003 name and contains
    only ordered raw source-PC/weight operands. Reusing that data type does not
    qualify its numerical merger or the historical whole stage chain as .4.
    """
    leaf = normalize_carrier_direct_12004(None if section is None else section.get(FIELD_NAME))
    if leaf is None or not leaf["ready"]:
        reason = FIELD_NAME if leaf is None else leaf["reason"] or FIELD_NAME
        raise ValueError("Required native input unavailable: " + reason)
    character = _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32, unsigned=True)
    if character != leaf["character_id"]:
        raise ValueError(FIELD_NAME + " Character join unavailable or mismatched")
    if leaf["source_occurrence_count"] == 0:
        return ()
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    block = leaf["properties"]
    return (NativeWeightedContributionRequest12003(
        source_ordinal=0,
        source_name=FIELD_NAME + "_12004",
        first_row_index=0,
        row_count=1,
        definition_identity=leaf["selected_pc_identity"],
        base_property_block={
            "keys_count": leaf["selected_pc_count_i32"],
            "keys_u16": block["keys_u16"],
            "values_q64": block["values_q64"],
        },
        weight_q64=100000,
    ),)
