"""Actual ordered first Title-pointer vector and its numerical Person inputs.

Primary/supplemental inputs form a shared helper-local PC. Composer inputs
form one separate block per emitted occurrence. No outer weight is inferred.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _string,
)
from .battle_person_following_2922680_12004 import _resolution, _rows
from .battle_person_local_titles_12004 import _family, _supplemental
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_291e3a0_first_title_vector"
SCHEMA = "xar.ck3.person-first-title-vector-12004-v1"
_READY_FIELDS = (
    "source_inputs_ready", "producer_ready", "family_input_ready",
    "primary_ready", "composer_ready", "supplemental_ready",
)
_POINTERS = (
    "character_identity", "selected_model_identity", "destination_pc_identity",
    "receiver_context_1c0_identity",
)


def _receiver(value, field):
    pointers = (
        "input_context_1c0_identity", "input_link_1b8_identity",
        "context_link_1c0_identity", "context_candidate_28_identity",
        "selected_identity",
    )
    numbers = ("candidate_magic_1c_u32", "candidate_full_id_18_u32",
               "requested_full_id_u32")
    raw = _dict(value, field, {
        "ready", "reason", "selection", "resolution", *pointers, *numbers,
    })
    result = {
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "selection": _string(raw["selection"], field + ".selection"),
        "resolution": _resolution(raw["resolution"], field + ".resolution"),
    }
    for key in pointers:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in numbers:
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    if result["ready"] and (result["reason"] is not None
                            or result["selected_identity"] is None):
        raise ValueError(field + " ready receiver lacks its actual selected pointer")
    return result


def _element(value, field):
    if value is None:
        return None
    raw = _dict(value, field, {
        "input_ready", "ready", "reason", "identity", "template_identity",
        "template_tier_i32", "primary", "composer", "supplemental",
    })
    result = {
        "input_ready": _boolean(raw["input_ready"], field + ".input_ready"),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "identity": _string(raw["identity"], field + ".identity", optional=True),
        "template_identity": _string(raw["template_identity"], field + ".template_identity", optional=True),
        "template_tier_i32": _number(raw["template_tier_i32"], field + ".template_tier_i32", 32),
        "primary": _family(raw["primary"], field + ".primary"),
        "composer": _family(raw["composer"], field + ".composer"),
        "supplemental": _supplemental(raw["supplemental"], field + ".supplemental"),
    }
    if result["ready"] and (result["reason"] is not None
                            or not result["input_ready"]
                            or not all(result[key]["ready"] for key in (
                                "primary", "composer", "supplemental"))):
        raise ValueError(field + " ready element lacks a demanded numerical family")
    return result


def _candidate(value, field):
    raw = _dict(value, field, {
        "native_index", "ready", "reason", "id_demanded", "requested_full_id_u32",
        "resolution", "filter_byte_130_u8", "emitted", "element",
    })
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "id_demanded": _boolean(raw["id_demanded"], field + ".id_demanded", optional=True),
        "requested_full_id_u32": _number(raw["requested_full_id_u32"], field + ".requested_full_id_u32", 32, unsigned=True),
        "resolution": _resolution(raw["resolution"], field + ".resolution"),
        "filter_byte_130_u8": _number(raw["filter_byte_130_u8"], field + ".filter_byte_130_u8", 8, unsigned=True),
        "emitted": _boolean(raw["emitted"], field + ".emitted", optional=True),
        "element": _element(raw["element"], field + ".element"),
    }
    if (result["id_demanded"] is True and result["requested_full_id_u32"]
            != result["resolution"]["requested_full_id_u32"]):
        raise ValueError(field + " changed the demanded full Title-ID input")
    if result["ready"] and (result["reason"] is not None or result["emitted"] is None):
        raise ValueError(field + " ready source lacks its emission decision")
    return result


def _phase(value, field):
    raw = _dict(value, field, {
        "ready", "reason", "admitted", "header_identity", "array_identity",
        "count_i32", "rows", "title_registry_identity", "title_fallback_identity",
    })
    result = {
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "header_identity": _string(raw["header_identity"], field + ".header_identity", optional=True),
        "array_identity": _string(raw["array_identity"], field + ".array_identity", optional=True),
        "title_registry_identity": _string(raw["title_registry_identity"], field + ".title_registry_identity", optional=True),
        "title_fallback_identity": _string(raw["title_fallback_identity"], field + ".title_fallback_identity", optional=True),
        "count_i32": _number(raw["count_i32"], field + ".count_i32", 32),
        "rows": _rows(raw["rows"], field + ".rows", _candidate),
    }
    if result["ready"] and (result["reason"] is not None
                            or any(not row["ready"] for row in result["rows"])):
        raise ValueError(field + " ready phase lacks a demanded source")
    return result


def _phase_b_inputs(value, field):
    pointers = (
        "subject_context_1c0_identity", "context_array_1e0_identity",
        "alternate_root_1d0_identity", "alternate_array_68_identity",
    )
    counts = ("context_count_1ec_i32", "alternate_count_74_i32")
    full_ids = ("initial_title_full_id_u32", "second_requested_full_id_330_u32")
    raw = _dict(value, field, {
        "ready", "reason", "selection", "initial_title_resolution",
        "second_resolution", *pointers, *counts, *full_ids,
    })
    result = {
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "selection": _string(raw["selection"], field + ".selection"),
        "initial_title_resolution": _resolution(raw["initial_title_resolution"], field + ".initial_title_resolution"),
        "second_resolution": _resolution(raw["second_resolution"], field + ".second_resolution"),
    }
    for key in pointers:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in counts:
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in full_ids:
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    if result["ready"] and result["reason"] is not None:
        raise ValueError(field + " ready phase input retains an unavailable reason")
    return result


def normalize_person_first_title_vector_12004(value: object) -> dict | None:
    """Preserve source demand, phase order, duplicate emissions and partial PCs."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, {
        "schema", "build_version", "executable_sha256", "ready", "reason",
        "character_id", "receiver", "receiver_context_1b8_full_id_u32",
        "phase_a", "phase_b_inputs", "phase_b", "emitted_element_identities",
        "family_known_zero", "full_helper_ready", "full_helper_reason",
        *_POINTERS, *_READY_FIELDS,
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
        "receiver": _receiver(raw["receiver"], FIELD_NAME + ".receiver"),
        "receiver_context_1b8_full_id_u32": _number(raw["receiver_context_1b8_full_id_u32"], FIELD_NAME + ".receiver_context_1b8_full_id_u32", 32, unsigned=True),
        "phase_a": _phase(raw["phase_a"], FIELD_NAME + ".phase_a"),
        "phase_b_inputs": _phase_b_inputs(raw["phase_b_inputs"], FIELD_NAME + ".phase_b_inputs"),
        "phase_b": _phase(raw["phase_b"], FIELD_NAME + ".phase_b"),
        "family_known_zero": _boolean(raw["family_known_zero"], FIELD_NAME + ".family_known_zero", optional=True),
        "full_helper_ready": _boolean(raw["full_helper_ready"], FIELD_NAME + ".full_helper_ready"),
        "full_helper_reason": _string(raw["full_helper_reason"], FIELD_NAME + ".full_helper_reason", optional=True),
    }
    for key in _POINTERS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in _READY_FIELDS:
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    emitted = raw["emitted_element_identities"]
    if emitted is not None and not isinstance(emitted, list):
        raise ValueError(FIELD_NAME + ".emitted_element_identities must retain native order")
    result["emitted_element_identities"] = (None if emitted is None else [
        _string(pointer, f"{FIELD_NAME}.emitted_element_identities[{index}]")
        for index, pointer in enumerate(emitted)
    ])
    if result["producer_ready"] and result["emitted_element_identities"] is None:
        raise ValueError(FIELD_NAME + " ready producer lacks its emitted pointer sequence")
    if result["ready"] and (result["reason"] is not None
                            or not all(result[key] for key in _READY_FIELDS)):
        raise ValueError(FIELD_NAME + " ready vector lacks demanded source inputs")
    return result


def compose_first_title_vector_inputs_from_current_source_inputs_12004(
        section, phase=None, native_index=None):
    """Fold observed inputs while retaining separate per-occurrence composers.

    Selecting phase and index uses one independently ready emitted occurrence.
    Its main block is partial in scope, not a complete helper or final Model.
    """
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_first_title_vector_12004(section.get(FIELD_NAME))
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if leaf is None or leaf["character_id"] != character:
        raise ValueError(FIELD_NAME + " full CharacterID join unavailable or mismatched")
    selected = phase is not None or native_index is not None
    if selected:
        if phase not in ("phase_a", "phase_b") or native_index is None:
            raise ValueError("A selected Title occurrence requires phase and native_index")
        index = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
        rows = leaf[phase]["rows"]
        if index >= len(rows):
            raise ValueError("Required native input unavailable: selected Title occurrence")
        occurrences = [(phase, rows[index])]
    else:
        if not leaf["ready"]:
            raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIELD_NAME))
        occurrences = [(name, row) for name in ("phase_a", "phase_b")
                       for row in leaf[name]["rows"]]
    from ..simulation.battle_person_after_gated_tail_12003 import fold_after_gated_blocks_12003

    def block(pc):
        return {"keys_count": pc["count_i32"],
                "keys_u16": pc["properties"]["keys_u16"],
                "values_q64": pc["properties"]["values_q64"]}

    main_blocks, composers = [], []
    for name, row in occurrences:
        if not row["ready"]:
            raise ValueError("Required native input unavailable: " + (row["reason"] or FIELD_NAME))
        if row["emitted"] is False:
            continue
        element = row["element"]
        if row["emitted"] is not True or element is None or not element["ready"]:
            raise ValueError("Required native input unavailable: emitted Title numerical inputs")
        main_blocks.extend(block(pc) for pc in element["primary"]["source_pcs"])
        composed = fold_after_gated_blocks_12003([
            block(pc) for pc in element["composer"]["source_pcs"]])
        composers.append({"phase": name, "native_index": row["native_index"],
                          "element_identity": element["identity"],
                          "property_block": composed,
                          "outer_append_demanded": composed["keys_count"] != 0})
        main_blocks.extend(block(source["source_pc"])
                           for source in element["supplemental"]["rows"]
                           if source["admitted"] is True)
    return {"complete_vector_input": not selected,
            "main_property_block": fold_after_gated_blocks_12003(main_blocks),
            "composer_blocks": tuple(composers), "full_helper_ready": False}
