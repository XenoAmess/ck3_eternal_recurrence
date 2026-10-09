"""Owned natural-call observations of the final actual291E3A0 Title request.

The captured PC is the native-prepared input at return291EBEF, before the
original outer append. Its capture date/sequence are historical attribution;
the current query frame never relabels it as the current Model or a baseline.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _string,
)
from .battle_person_following_2922680_12004 import _pc
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_291e3a0_captured_tail"
SCHEMA = "xar.ck3.person-native-title-tail-capture-12004-v1"
SOURCE_STAGE = "post_composer_pre_final_outer_append"
SOURCE_RETURN_RVA = 0x291EBEF
_POINTERS = (
    "character_identity", "model_identity", "source_return_rva",
    "inline_destination_identity",
)


def normalize_person_title_tail_capture_12004(value: object) -> dict | None:
    """Preserve copied operands and their original capture attribution."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, {
        "schema", "build_version", "executable_sha256", "configured",
        "capture_observed", "ready", "reason", "capture_sequence",
        "capture_date_raw", "character_id", *_POINTERS, "prepared_pc",
        "model_aggregate_pc", "weight_q100000", "source_stage",
        "historical_capture", "actual_model_write_performed", "full_helper_ready",
    })
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {
        "schema": SCHEMA, "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "reason": _string(raw["reason"], FIELD_NAME + ".reason", optional=True),
        "capture_sequence": _integer(raw["capture_sequence"], FIELD_NAME + ".capture_sequence", 64, unsigned=True),
        "capture_date_raw": _number(raw["capture_date_raw"], FIELD_NAME + ".capture_date_raw", 32),
        "character_id": _number(raw["character_id"], FIELD_NAME + ".character_id", 32, unsigned=True),
        "weight_q100000": _integer(raw["weight_q100000"], FIELD_NAME + ".weight_q100000", 64),
        "source_stage": _string(raw["source_stage"], FIELD_NAME + ".source_stage"),
        "prepared_pc": _pc(raw["prepared_pc"], FIELD_NAME + ".prepared_pc"),
        "model_aggregate_pc": _pc(raw["model_aggregate_pc"], FIELD_NAME + ".model_aggregate_pc"),
    }
    for key in ("configured", "capture_observed", "ready", "historical_capture",
                "actual_model_write_performed", "full_helper_ready"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    for key in _POINTERS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    if (result["source_stage"] != SOURCE_STAGE or result["historical_capture"] is not True
            or result["weight_q100000"] != 100000
            or result["actual_model_write_performed"] is not False
            or result["full_helper_ready"] is not False):
        raise ValueError(FIELD_NAME + " changed its captured-stage scope")
    if result["capture_observed"]:
        if (not result["configured"] or result["capture_sequence"] == 0
                or result["character_id"] is None
                or result["character_identity"] is None
                or result["model_identity"] is None):
            raise ValueError(FIELD_NAME + " observed record lacks its native owner or sequence")
        try:
            return_rva = int(result["source_return_rva"], 16)
            destination = int(result["inline_destination_identity"], 16)
            model = int(result["model_identity"], 16)
        except (TypeError, ValueError) as error:
            raise ValueError(FIELD_NAME + " lacks its actual caller/destination") from error
        if return_rva != SOURCE_RETURN_RVA or destination != model + 0x10:
            raise ValueError(FIELD_NAME + " differs from the actual final outer caller")
    elif result["capture_sequence"] != 0 or result["ready"]:
        raise ValueError(FIELD_NAME + " unobserved record cannot be ready or sequenced")
    if result["ready"]:
        if (not result["capture_observed"] or result["reason"] is not None
                or not result["prepared_pc"]["ready"]
                or result["prepared_pc"]["admitted"] is not True):
            raise ValueError(FIELD_NAME + " ready capture lacks its native-prepared PC")
    return result


def emit_captured_person_title_tail_request_12004(section: object) -> dict:
    """Publish one actual prepared request, preserving historical attribution.

    Diagnostic aggregate-copy failure does not block this independently ready
    request. This function neither replays the helper nor mutates a Model.
    """
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    leaf = normalize_person_title_tail_capture_12004(section.get(FIELD_NAME))
    if leaf is None or leaf["character_id"] != character or not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + (
            leaf["reason"] if leaf and leaf["reason"] else FIELD_NAME))
    pc = leaf["prepared_pc"]
    return {
        "source_family": "captured_final_title_tail",
        "source_stage": SOURCE_STAGE,
        "historical_capture": True,
        "capture_sequence": leaf["capture_sequence"],
        "capture_date_raw": leaf["capture_date_raw"],
        "character_id": character,
        "character_identity": leaf["character_identity"],
        "selected_model_identity": leaf["model_identity"],
        "inline_destination_identity": leaf["inline_destination_identity"],
        "source_return_rva": leaf["source_return_rva"],
        "property_block": {
            "keys_count": pc["count_i32"],
            "keys_u16": pc["properties"]["keys_u16"],
            "values_q64": pc["properties"]["values_q64"],
        },
        "weight_q100000": 100000,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }
