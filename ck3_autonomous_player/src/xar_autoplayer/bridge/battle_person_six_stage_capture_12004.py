"""Owned observations of the six natural actual4 Person attribute stages.

Raw callback results belong to their intermediate native context. They are not
final skills. Append operands and weights are copied from calls that actually
occurred; this module does not reconstruct a gate, replay a helper, or fold PCs.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)
from .battle_person_carrier_direct_12004 import _values_q64
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_six_attribute_captured_stages"
SCHEMA = "xar.ck3.person-native-six-stage-capture-12004-v1"
QUERY_FIELD_NAME = "person_six_stage_captures"
QUERY_SCHEMA = "xar.ck3.person-native-six-stage-query-12004-v1"
SOURCE_RETURN_RVA = 0x291CEA9
STAGE_COUNT = 6
_POINTERS = ("character_identity", "context_identity", "source_return_rva")
_APPEND_KINDS = ("first", "second")


def _pc(value: object, field: str) -> dict:
    """Copy the existing Person PC shape, retaining its actual signed weight."""
    raw = _dict(value, field, {
        "ready", "reason", "admitted", "identity", "count_i32",
        "properties", "weight_q100000",
    })
    result = {
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "identity": _string(raw["identity"], field + ".identity", optional=True),
        "count_i32": _number(raw["count_i32"], field + ".count_i32", 32),
        "weight_q100000": _number(raw["weight_q100000"], field + ".weight_q100000", 64),
    }
    block = raw["properties"]
    if block is not None:
        block = _dict(block, field + ".properties", {"keys_u16", "values_q64"})
        block = {
            "keys_u16": _numbers(block["keys_u16"], field + ".properties.keys_u16", 16, unsigned=True),
            "values_q64": _values_q64(block["values_q64"], field + ".properties.values_q64"),
        }
    result["properties"] = block
    if result["ready"]:
        if result["reason"] is not None or result["admitted"] is None:
            raise ValueError(field + " ready observation lacks its native call decision")
        if result["admitted"]:
            count = result["count_i32"]
            if (result["identity"] is None or count is None or count < 0
                    or block is None or block["keys_u16"] is None
                    or block["values_q64"] is None
                    or len(block["keys_u16"]) != count
                    or len(block["values_q64"]) != count):
                raise ValueError(field + " ready append lacks its actual PC operands")
    return result


def _stage(value: object, field: str, index: int, capture_complete: bool) -> dict:
    raw = _dict(value, field, {
        "index", "observed", "raw_count_i32", "first_append_observed",
        "second_append_observed", "first_pc", "second_pc",
    })
    result = {
        "index": _integer(raw["index"], field + ".index", 32, unsigned=True),
        "observed": _boolean(raw["observed"], field + ".observed"),
        "raw_count_i32": _number(raw["raw_count_i32"], field + ".raw_count_i32", 32),
    }
    if result["index"] != index:
        raise ValueError(field + " changed its physical six-stage order")
    if result["observed"] != (result["raw_count_i32"] is not None):
        raise ValueError(field + " raw callback observation disagrees with its signed result")
    for kind in _APPEND_KINDS:
        observed_name, pc_name = kind + "_append_observed", kind + "_pc"
        observed = _boolean(raw[observed_name], field + "." + observed_name)
        pc = _pc(raw[pc_name], field + "." + pc_name)
        result[observed_name], result[pc_name] = observed, pc
        if observed:
            if (not result["observed"] or pc["admitted"] is not True
                    or pc["weight_q100000"] is None):
                raise ValueError(field + " append lacks its observed native stage/call")
        elif pc["weight_q100000"] is not None:
            raise ValueError(field + " absent append cannot claim a captured weight")
        elif pc["admitted"] is True:
            raise ValueError(field + " absent append cannot contain admitted operands")
        elif not capture_complete and (pc["ready"] or pc["admitted"] is not None):
            raise ValueError(field + " incomplete capture cannot turn an absent call into a skip")
        elif capture_complete and (not pc["ready"] or pc["admitted"] is not False):
            raise ValueError(field + " completed absent call lacks its native skip decision")
    return result


def normalize_person_six_stage_capture_12004(value: object) -> dict | None:
    """Retain six owned stages, including incomplete and unread observations."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, {
        "schema", "build_version", "executable_sha256", "configured",
        "capture_observed", "capture_complete", "ready", "raw_counts_ready",
        "reason", "capture_sequence", "capture_date_raw", "character_id",
        "capture_thread_id", "query_thread_id",
        *_POINTERS, "stages", "historical_capture",
        "actual_model_write_performed", "full_helper_ready",
    })
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {
        "schema": SCHEMA,
        "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "reason": _string(raw["reason"], FIELD_NAME + ".reason", optional=True),
        "capture_sequence": _integer(raw["capture_sequence"], FIELD_NAME + ".capture_sequence", 64, unsigned=True),
        "capture_date_raw": _number(raw["capture_date_raw"], FIELD_NAME + ".capture_date_raw", 32),
        "character_id": _number(raw["character_id"], FIELD_NAME + ".character_id", 32, unsigned=True),
        "capture_thread_id": _number(raw["capture_thread_id"], FIELD_NAME + ".capture_thread_id", 32, unsigned=True),
        "query_thread_id": _number(raw["query_thread_id"], FIELD_NAME + ".query_thread_id", 32, unsigned=True),
    }
    for key in ("configured", "capture_observed", "capture_complete", "ready",
                "raw_counts_ready", "historical_capture",
                "actual_model_write_performed", "full_helper_ready"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    for key in _POINTERS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    if (result["historical_capture"] is not True
            or result["actual_model_write_performed"] is not False
            or result["full_helper_ready"] is not False):
        raise ValueError(FIELD_NAME + " changed its historical observation scope")
    if not isinstance(raw["stages"], list) or len(raw["stages"]) != STAGE_COUNT:
        raise ValueError(FIELD_NAME + " must retain all six physical stage slots")
    result["stages"] = [
        _stage(stage, f"{FIELD_NAME}.stages[{index}]", index, result["capture_complete"])
        for index, stage in enumerate(raw["stages"])
    ]
    if result["capture_observed"]:
        if (not result["configured"] or result["capture_sequence"] == 0
                or result["character_id"] is None
                or result["capture_thread_id"] is None
                or result["character_identity"] is None
                or result["context_identity"] is None):
            raise ValueError(FIELD_NAME + " observed record lacks its native owner or sequence")
        try:
            return_rva = int(result["source_return_rva"], 16)
        except (TypeError, ValueError) as error:
            raise ValueError(FIELD_NAME + " lacks its actual callback caller") from error
        if return_rva != SOURCE_RETURN_RVA:
            raise ValueError(FIELD_NAME + " differs from the actual six-stage callback caller")
    elif (result["capture_sequence"] != 0 or result["capture_complete"]
            or result["raw_counts_ready"] or result["ready"]
            or result["capture_thread_id"] is not None or result["query_thread_id"] is not None
            or any(stage["observed"] for stage in result["stages"])):
        raise ValueError(FIELD_NAME + " unobserved record cannot contain captured stages")
    if result["capture_complete"]:
        if (result["query_thread_id"] is None
                or result["query_thread_id"] != result["capture_thread_id"]):
            raise ValueError(FIELD_NAME + " completed capture lacks its same-thread query proof")
    elif result["query_thread_id"] is not None:
        raise ValueError(FIELD_NAME + " incomplete capture cannot claim a query completion thread")
    if result["raw_counts_ready"] and not all(stage["observed"] for stage in result["stages"]):
        raise ValueError(FIELD_NAME + " complete raw counts lack a natural callback result")
    if result["ready"]:
        if (not result["capture_observed"] or not result["capture_complete"]
                or not result["raw_counts_ready"] or result["reason"] is not None
                or any(not stage[kind + "_pc"]["ready"]
                       for stage in result["stages"] for kind in _APPEND_KINDS)):
            raise ValueError(FIELD_NAME + " ready capture retains an unavailable stage")
    return result


def normalize_person_six_stage_query_12004(
        value: object, *, expected_snapshot_revision: object,
        expected_observed_date_raw: object, expected_character_ids: object) -> dict:
    """Join the separate whole-query envelope to its requested frame and IDs."""
    raw = _dict(value, QUERY_FIELD_NAME, {
        "schema", "snapshot_revision", "observed_date_raw", "character_captures",
    })
    if raw["schema"] != QUERY_SCHEMA:
        raise ValueError(QUERY_FIELD_NAME + " schema mismatch")
    revision = _integer(raw["snapshot_revision"], QUERY_FIELD_NAME + ".snapshot_revision", 64, unsigned=True)
    date = _integer(raw["observed_date_raw"], QUERY_FIELD_NAME + ".observed_date_raw", 32)
    expected_revision = _integer(expected_snapshot_revision, "expected_snapshot_revision", 64, unsigned=True)
    expected_date = _integer(expected_observed_date_raw, "expected_observed_date_raw", 32)
    if revision != expected_revision or date != expected_date:
        raise ValueError(QUERY_FIELD_NAME + " differs from the requested snapshot frame")
    if not isinstance(expected_character_ids, (list, tuple)):
        raise ValueError("expected_character_ids must retain the requested full-ID order")
    requested = [
        _integer(character, f"expected_character_ids[{index}]", 32, unsigned=True)
        for index, character in enumerate(expected_character_ids)
    ]
    if not isinstance(raw["character_captures"], list):
        raise ValueError(QUERY_FIELD_NAME + ".character_captures must retain requested character order")
    captures = [normalize_person_six_stage_capture_12004(leaf)
                for leaf in raw["character_captures"]]
    if (any(leaf is None for leaf in captures)
            or [leaf["character_id"] for leaf in captures] != requested):
        raise ValueError(QUERY_FIELD_NAME + " full CharacterID order differs from its request")
    return {
        "schema": QUERY_SCHEMA,
        "snapshot_revision": revision,
        "observed_date_raw": date,
        "character_captures": captures,
    }


def select_person_six_stage_capture_12004(sidecar: object, character_id: object) -> dict:
    """Select one full-ID capture from a query envelope for the existing emitters.

    The caller receives the same section shape accepted before the capture was
    placed in its separate query sibling. External frame binding belongs to
    normalize_person_six_stage_query_12004 at the query boundary.
    """
    character = _integer(character_id, QUERY_FIELD_NAME + ".character_id", 32, unsigned=True)
    raw = _dict(sidecar, QUERY_FIELD_NAME, {
        "schema", "snapshot_revision", "observed_date_raw", "character_captures",
    })
    captures = raw["character_captures"]
    if not isinstance(captures, list) or any(not isinstance(leaf, dict) for leaf in captures):
        raise ValueError(QUERY_FIELD_NAME + ".character_captures must retain requested character order")
    normalized = normalize_person_six_stage_query_12004(
        raw, expected_snapshot_revision=raw["snapshot_revision"],
        expected_observed_date_raw=raw["observed_date_raw"],
        expected_character_ids=[leaf.get("character_id") for leaf in captures],
    )
    matches = [leaf for leaf in normalized["character_captures"]
               if leaf["character_id"] == character]
    if len(matches) != 1:
        raise ValueError("Required native input unavailable: " + QUERY_FIELD_NAME + " full CharacterID selection")
    return {"character_id": character, FIELD_NAME: matches[0]}


def _joined_leaf(section: object) -> tuple[int, dict]:
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    leaf = normalize_person_six_stage_capture_12004(section.get(FIELD_NAME))
    if leaf is None or leaf["character_id"] != character:
        raise ValueError("Required native input unavailable: " + FIELD_NAME + " full CharacterID join")
    return character, leaf


def _stage_requests(character: int, leaf: dict, stage: dict) -> tuple[dict, ...]:
    if (not leaf["capture_complete"] or not stage["observed"]
            or any(not stage[kind + "_pc"]["ready"] for kind in _APPEND_KINDS)):
        raise ValueError("Required native input unavailable: " + FIELD_NAME + " stage " + str(stage["index"]))
    requests = []
    for slot, kind in enumerate(_APPEND_KINDS):
        if not stage[kind + "_append_observed"]:
            continue
        pc = stage[kind + "_pc"]
        block = pc["properties"]
        requests.append({
            "source_family": "captured_six_attribute_stages",
            "source_ordinal": 2 * stage["index"] + slot,
            "stage_index": stage["index"],
            "append_kind": kind,
            "native_append_observed": True,
            "historical_capture": True,
            "capture_sequence": leaf["capture_sequence"],
            "capture_date_raw": leaf["capture_date_raw"],
            "capture_thread_id": leaf["capture_thread_id"],
            "query_thread_id": leaf["query_thread_id"],
            "character_id": character,
            "character_identity": leaf["character_identity"],
            "context_identity": leaf["context_identity"],
            "source_return_rva": leaf["source_return_rva"],
            "raw_count_i32": stage["raw_count_i32"],
            "source_pc_identity": pc["identity"],
            "property_block": {
                "keys_count": pc["count_i32"],
                "keys_u16": list(block["keys_u16"]),
                "values_q64": list(block["values_q64"]),
            },
            "weight_q100000": pc["weight_q100000"],
            "actual_model_write_performed": False,
            "full_helper_ready": False,
        })
    return tuple(requests)


def emit_captured_person_six_stage_requests_12004(section: object) -> tuple[dict, ...]:
    """Publish actual append inputs in stage/first/second order; never fold them."""
    character, leaf = _joined_leaf(section)
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIELD_NAME))
    return tuple(request for stage in leaf["stages"]
                 for request in _stage_requests(character, leaf, stage))


def emit_captured_person_six_stage_occurrence_requests_12004(
        section: object, native_index: object) -> tuple[dict, ...]:
    """Publish one ready stage of a completed capture despite other PC failures."""
    character, leaf = _joined_leaf(section)
    index = _integer(native_index, FIELD_NAME + ".stages.index", 32, unsigned=True)
    if index >= STAGE_COUNT:
        raise ValueError("Required native input unavailable: " + FIELD_NAME + " stage")
    return _stage_requests(character, leaf, leaf["stages"][index])
