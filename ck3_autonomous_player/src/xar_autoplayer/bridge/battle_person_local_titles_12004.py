"""Ordered actual4 local Title inputs in the current Person query.

Composer constituents form one local PC per eligible Title occurrence. They
are never published as separate outer Model requests or a fresh Entry model.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _string,
)
from .battle_person_following_2922680_12004 import _pc, _resolution, _rows
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_291e3a0_local_titles"
SCHEMA = "xar.ck3.person-local-titles-12004-v1"
_POINTERS = (
    "character_identity", "selected_model_identity", "destination_pc_identity",
    "character_context_1c0_identity", "header_identity", "array_identity",
)
_READY_FIELDS = (
    "family_input_ready", "composer_ready", "primary_ready", "supplemental_ready",
)


def _family(value, field):
    raw = _dict(value, field, {
        "ready", "reason", "array_identity", "count_i32", "source_pcs", "known_empty",
    })
    result = {
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "array_identity": _string(raw["array_identity"], field + ".array_identity", optional=True),
        "count_i32": _number(raw["count_i32"], field + ".count_i32", 32),
        "known_empty": _boolean(raw["known_empty"], field + ".known_empty", optional=True),
    }
    if not isinstance(raw["source_pcs"], list):
        raise ValueError(field + ".source_pcs must retain constituent occurrence order")
    result["source_pcs"] = [
        _pc(pc, f"{field}.source_pcs[{index}]")
        for index, pc in enumerate(raw["source_pcs"])
    ]
    if result["ready"] and (result["reason"] is not None
                            or any(not pc["ready"] for pc in result["source_pcs"])):
        raise ValueError(field + " ready family lacks a demanded constituent")
    return result


def _supplemental_source(value, field):
    raw = _dict(value, field, {
        "native_index", "ready", "reason", "requested_full_id_u32", "resolution",
        "definition_identity", "definition_gate_224_i32", "object_gate_18_u8",
        "rite_id_demanded", "character_rite_full_id_u32", "rite_resolution",
        "membership_array_identity", "membership_count_i32", "rite_membership_key_u32",
        "membership_full_ids_u32", "first_match_index", "match_identity", "admitted", "source_pc",
    })
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "resolution": _resolution(raw["resolution"], field + ".resolution"),
        "rite_resolution": _resolution(raw["rite_resolution"], field + ".rite_resolution"),
        "source_pc": _pc(raw["source_pc"], field + ".source_pc"),
    }
    for key in ("definition_identity", "membership_array_identity", "match_identity"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in ("requested_full_id_u32", "character_rite_full_id_u32",
                "rite_membership_key_u32", "first_match_index"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    for key in ("definition_gate_224_i32", "membership_count_i32"):
        result[key] = _number(raw[key], field + "." + key, 32)
    result["object_gate_18_u8"] = _number(raw["object_gate_18_u8"], field + ".object_gate_18_u8", 8, unsigned=True)
    for key in ("rite_id_demanded", "admitted"):
        result[key] = _boolean(raw[key], field + "." + key, optional=True)
    values = raw["membership_full_ids_u32"]
    if not isinstance(values, list):
        raise ValueError(field + ".membership_full_ids_u32 must retain the observed native prefix")
    result["membership_full_ids_u32"] = [
        _number(value, f"{field}.membership_full_ids_u32[{index}]", 32, unsigned=True)
        for index, value in enumerate(values)
    ]
    if result["requested_full_id_u32"] != result["resolution"]["requested_full_id_u32"]:
        raise ValueError(field + " changed the supplemental full-ID lookup input")
    if result["ready"] and (result["reason"] is not None or not result["source_pc"]["ready"]):
        raise ValueError(field + " ready supplemental source lacks its demanded operand")
    return result


def _supplemental(value, field):
    raw = _dict(value, field, {
        "ready", "reason", "array_identity", "count_i32", "known_empty", "rows",
    })
    result = {
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "array_identity": _string(raw["array_identity"], field + ".array_identity", optional=True),
        "count_i32": _number(raw["count_i32"], field + ".count_i32", 32),
        "known_empty": _boolean(raw["known_empty"], field + ".known_empty", optional=True),
        "rows": _rows(raw["rows"], field + ".rows", _supplemental_source),
    }
    if result["ready"] and (result["reason"] is not None
                            or any(not row["ready"] for row in result["rows"])):
        raise ValueError(field + " ready supplemental family lacks a demanded source")
    return result


def _row(value, field):
    fields = {
        "native_index", "input_ready", "ready", "reason", "requested_title_full_id_u32",
        "resolution", "selected_title_full_id_u32", "exclusion_byte_130_u8",
        "exclusion_dword_12c_i32", "native_contribution_eligible", "exclusion",
        "template_identity", "template_tier_i32", "composer", "primary",
        "supplemental_array_identity", "supplemental_count_i32",
        "supplemental_ready", "supplemental_reason",
    }
    # Frozen Native55 rows predate this optional domain observation.
    if isinstance(value, Mapping) and "supplemental" in value:
        fields.add("supplemental")
    raw = _dict(value, field, fields)
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "input_ready": _boolean(raw["input_ready"], field + ".input_ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "resolution": _resolution(raw["resolution"], field + ".resolution"),
        "native_contribution_eligible": _boolean(
            raw["native_contribution_eligible"], field + ".native_contribution_eligible", optional=True),
        "exclusion": _string(raw["exclusion"], field + ".exclusion"),
        "template_identity": _string(raw["template_identity"], field + ".template_identity", optional=True),
        "composer": _family(raw["composer"], field + ".composer"),
        "primary": _family(raw["primary"], field + ".primary"),
        "supplemental_array_identity": _string(
            raw["supplemental_array_identity"], field + ".supplemental_array_identity", optional=True),
        "supplemental_ready": _boolean(raw["supplemental_ready"], field + ".supplemental_ready"),
        "supplemental_reason": _string(raw["supplemental_reason"], field + ".supplemental_reason", optional=True),
    }
    for key in ("requested_title_full_id_u32", "selected_title_full_id_u32"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    result["exclusion_byte_130_u8"] = _number(
        raw["exclusion_byte_130_u8"], field + ".exclusion_byte_130_u8", 8, unsigned=True)
    for key in ("exclusion_dword_12c_i32", "template_tier_i32", "supplemental_count_i32"):
        result[key] = _number(raw[key], field + "." + key, 32)
    if "supplemental" in raw:
        result["supplemental"] = _supplemental(raw["supplemental"], field + ".supplemental")
    if (result["requested_title_full_id_u32"] !=
            result["resolution"]["requested_full_id_u32"]):
        raise ValueError(field + " changed the full-ID lookup input")
    if result["ready"] and (result["reason"] is not None or not result["input_ready"]):
        raise ValueError(field + " ready row lacks its actual input selection")
    return result


def normalize_person_local_titles_12004(value: object) -> dict | None:
    """Keep partial sources and native row/PC order, including duplicates."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, {
        "schema", "build_version", "executable_sha256", "ready", "reason",
        "character_id", "header_selection", "count_i32", "rows", "family_known_zero",
        "full_helper_ready", "full_helper_reason", *_POINTERS, *_READY_FIELDS,
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
        "header_selection": _string(raw["header_selection"], FIELD_NAME + ".header_selection"),
        "count_i32": _number(raw["count_i32"], FIELD_NAME + ".count_i32", 32),
        "family_known_zero": _boolean(raw["family_known_zero"], FIELD_NAME + ".family_known_zero", optional=True),
        "rows": _rows(raw["rows"], FIELD_NAME + ".rows", _row),
        "full_helper_ready": _boolean(raw["full_helper_ready"], FIELD_NAME + ".full_helper_ready"),
        "full_helper_reason": _string(raw["full_helper_reason"], FIELD_NAME + ".full_helper_reason", optional=True),
    }
    for key in _POINTERS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in _READY_FIELDS:
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    if result["ready"] and (result["reason"] is not None
                            or not all(result[key] for key in _READY_FIELDS)):
        raise ValueError(FIELD_NAME + " ready local family lacks demanded inputs")
    return result


def compose_local_title_composer_blocks_from_current_source_inputs_12004(
        section, native_index=None):
    """Fold each selected Title's constituents once; do not infer outer weight.

    A selected ready occurrence remains useful when a sibling has an unread
    operand. Without an index, every native Title occurrence must be observed.
    """
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_local_titles_12004(section.get(FIELD_NAME))
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if leaf is None or leaf["character_id"] != character:
        raise ValueError(FIELD_NAME + " full CharacterID join unavailable or mismatched")
    rows = leaf["rows"]
    if native_index is not None:
        index = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
        if index >= len(rows):
            raise ValueError("Required native input unavailable: " + FIELD_NAME + " occurrence")
        rows = [rows[index]]
    elif not leaf["family_input_ready"] or not leaf["composer_ready"]:
        raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIELD_NAME))
    from ..simulation.battle_person_after_gated_tail_12003 import fold_after_gated_blocks_12003
    result = []
    for row in rows:
        if not row["input_ready"]:
            raise ValueError("Required native input unavailable: " + (row["reason"] or FIELD_NAME))
        if row["native_contribution_eligible"] is False:
            continue
        composer = row["composer"]
        if row["native_contribution_eligible"] is not True or not composer["ready"]:
            raise ValueError("Required native input unavailable: " + (composer["reason"] or FIELD_NAME))
        blocks = [{"keys_count": pc["count_i32"],
                   "keys_u16": pc["properties"]["keys_u16"],
                   "values_q64": pc["properties"]["values_q64"]}
                  for pc in composer["source_pcs"]]
        block = fold_after_gated_blocks_12003(blocks)
        result.append({"native_index": row["native_index"],
                       "selected_title_full_id_u32": row["selected_title_full_id_u32"],
                       "property_block": block,
                       "outer_append_demanded": block["keys_count"] != 0})
    return tuple(result)


def compose_local_title_supplemental_blocks_from_current_source_inputs_12004(
        section, native_index=None):
    """Fold the observed supplemental PCs once per Title, in source order.

    No outer Model append or weight is inferred. A selected complete Title
    remains usable when another Title has an unread supplemental constituent.
    """
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_local_titles_12004(section.get(FIELD_NAME))
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if leaf is None or leaf["character_id"] != character:
        raise ValueError(FIELD_NAME + " full CharacterID join unavailable or mismatched")
    rows = leaf["rows"]
    if native_index is not None:
        index = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
        if index >= len(rows):
            raise ValueError("Required native input unavailable: " + FIELD_NAME + " occurrence")
        rows = [rows[index]]
    elif not leaf["family_input_ready"] or not leaf["supplemental_ready"]:
        raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIELD_NAME))
    from ..simulation.battle_person_after_gated_tail_12003 import fold_after_gated_blocks_12003
    result = []
    for row in rows:
        if not row["input_ready"]:
            raise ValueError("Required native input unavailable: " + (row["reason"] or FIELD_NAME))
        if row["native_contribution_eligible"] is False:
            continue
        family = row.get("supplemental")
        if family is None or not family["ready"]:
            raise ValueError("Required native input unavailable: " + (
                family["reason"] if family is not None and family["reason"] else "supplemental"))
        pcs = [source["source_pc"] for source in family["rows"] if source["admitted"] is True]
        blocks = [{"keys_count": pc["count_i32"],
                   "keys_u16": pc["properties"]["keys_u16"],
                   "values_q64": pc["properties"]["values_q64"]} for pc in pcs]
        result.append({"native_index": row["native_index"],
                       "selected_title_full_id_u32": row["selected_title_full_id_u32"],
                       "property_block": fold_after_gated_blocks_12003(blocks)})
    return tuple(result)
