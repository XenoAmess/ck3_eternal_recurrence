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
from ..simulation.battle_person_pc_merger_12004 import (
    _divide_q_from_instructions, _signed64, native_fixed_mul_q_12004,
)

FIELD_NAME = "following_six_attribute_captured_stages"
SCHEMA = "xar.ck3.person-native-six-stage-capture-12004-v1"
SOURCE_STAGE = "ordered_six_attribute_native_calls"
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


def _aggregate(value: object, field: str, source_stage: str) -> dict:
    raw = _dict(value, field, {"observed", "source_stage", "context_pc_offset", "pc"})
    result = {
        "observed": _boolean(raw["observed"], field + ".observed"),
        "source_stage": _string(raw["source_stage"], field + ".source_stage"),
        "context_pc_offset": _integer(raw["context_pc_offset"], field + ".context_pc_offset", 32, unsigned=True),
        "pc": _pc(raw["pc"], field + ".pc"),
    }
    if result["source_stage"] != source_stage or result["context_pc_offset"] != 0x68:
        raise ValueError(field + " changed its actual inline PC source")
    pc = result["pc"]
    if pc["weight_q100000"] is not None:
        raise ValueError(field + " aggregate state cannot claim a native append weight")
    if result["observed"]:
        if pc["admitted"] is not True or pc["identity"] is None:
            raise ValueError(field + " observed aggregate lacks its actual PC source")
    elif pc["ready"] or pc["admitted"] is not None or pc["identity"] is not None:
        raise ValueError(field + " unobserved aggregate cannot claim PC operands")
    return result


def _preparation_model(value: object, leaf: dict) -> dict:
    field = FIELD_NAME + ".preparation_model"
    raw = _dict(value, field, {
        "observed", "ready", "reason", "model_identity",
        "owner_character_identity", "owner_character_id", "owner_matches_capture",
        "context_offset", "owner_offset", "source_stage",
    })
    result = {
        "observed": _boolean(raw["observed"], field + ".observed"),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "model_identity": _string(raw["model_identity"], field + ".model_identity", optional=True),
        "owner_character_identity": _string(raw["owner_character_identity"], field + ".owner_character_identity", optional=True),
        "owner_character_id": _number(raw["owner_character_id"], field + ".owner_character_id", 32, unsigned=True),
        "owner_matches_capture": _boolean(raw["owner_matches_capture"], field + ".owner_matches_capture", optional=True),
        "context_offset": _integer(raw["context_offset"], field + ".context_offset", 32, unsigned=True),
        "owner_offset": _integer(raw["owner_offset"], field + ".owner_offset", 32, unsigned=True),
        "source_stage": _string(raw["source_stage"], field + ".source_stage"),
    }
    if (result["context_offset"] != 0x10 or result["owner_offset"] != 8
            or result["source_stage"] != "before_first_count_callback"):
        raise ValueError(field + " changed its actual preparation source")
    if result["observed"]:
        if (not leaf["capture_observed"] or not leaf["stages"][0]["observed"]
                or result["model_identity"] is None
                or int(result["model_identity"], 16) != int(leaf["context_identity"], 16) - 0x10):
            raise ValueError(field + " lacks its captured context-minus-10 Model")
    elif (result["ready"] or any(result[key] is not None for key in (
            "model_identity", "owner_character_identity", "owner_character_id",
            "owner_matches_capture"))):
        raise ValueError(field + " unobserved preparation cannot claim Model operands")
    if result["ready"]:
        if (not result["observed"] or result["reason"] is not None
                or result["owner_character_identity"] is None
                or int(result["owner_character_identity"], 16) == 0
                or result["owner_character_id"] is None):
            raise ValueError(field + " ready preparation lacks its copied owner operands")
        matches = (int(result["owner_character_identity"], 16) == int(leaf["character_identity"], 16)
                   and result["owner_character_id"] == leaf["character_id"])
        if result["owner_matches_capture"] is not matches:
            raise ValueError(field + " owner comparison differs from its copied operands")
    elif result["owner_matches_capture"] is not None:
        raise ValueError(field + " unread preparation cannot claim an owner comparison")
    return result


def _base_point_inputs(value: object, leaf: dict) -> dict:
    field = FIELD_NAME + ".base_point_inputs"
    raw = _dict(value, field, {
        "source_stage", "character_offset", "stride_bytes", "observed",
        "values_i32", "ready", "reason",
    })
    result = {
        "source_stage": _string(raw["source_stage"], field + ".source_stage"),
        "character_offset": _integer(raw["character_offset"], field + ".character_offset", 32, unsigned=True),
        "stride_bytes": _integer(raw["stride_bytes"], field + ".stride_bytes", 32, unsigned=True),
        "values_i32": [
            _number(point, f"{field}.values_i32[{index}]", 32)
            for index, point in enumerate(raw["values_i32"])
        ] if isinstance(raw["values_i32"], list) else None,
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    if (result["source_stage"] != "before_each_original_count"
            or result["character_offset"] != 0xC0 or result["stride_bytes"] != 4):
        raise ValueError(field + " changed its actual per-stage Character source")
    if (not isinstance(raw["observed"], list) or len(raw["observed"]) != STAGE_COUNT
            or result["values_i32"] is None or len(result["values_i32"]) != STAGE_COUNT):
        raise ValueError(field + " must retain the six native stage input slots")
    result["observed"] = [
        _boolean(observed, f"{field}.observed[{index}]")
        for index, observed in enumerate(raw["observed"])
    ]
    for index, observed in enumerate(result["observed"]):
        if observed and not leaf["stages"][index]["observed"]:
            raise ValueError(field + " observed input lacks its actual stage callback")
        if not observed and result["values_i32"][index] is not None:
            raise ValueError(field + " unobserved input cannot claim a base value")
    all_observed = leaf["raw_counts_ready"] and all(result["observed"])
    ready = all_observed and all(value is not None for value in result["values_i32"])
    reason = None if ready else "base_point_unread" if all_observed else "base_point_unobserved"
    if result["ready"] is not ready or result["reason"] != reason:
        raise ValueError(field + " readiness differs from its owned per-call inputs")
    return result


_PIETY_SOURCE = {
    "source_stage": "before_each_original_count", "getter_rva": 0x28BE0B0,
    "key_table_rva": 0x4807608, "key_stride_bytes": 8,
    "character_extension_offset": 0x1B0, "score_offset": 0x118, "cap_offset": 0x120,
    "threshold_pointer_rva": 0x54582D8, "threshold_count_rva": 0x54582E4,
}


def _piety_category_inputs(value: object, leaf: dict) -> dict:
    field = FIELD_NAME + ".piety_category_inputs"
    raw = _dict(value, field, {*_PIETY_SOURCE, "stages"})
    if any(raw[key] != expected for key, expected in _PIETY_SOURCE.items()):
        raise ValueError(field + " changed its actual category source")
    if not isinstance(raw["stages"], list) or len(raw["stages"]) != STAGE_COUNT:
        raise ValueError(field + " must retain six historical input slots")
    stages = []
    for index, value in enumerate(raw["stages"]):
        slot = f"{field}.stages[{index}]"
        row = _dict(value, slot, {
            "index", "observed", "ready", "reason", "property_key_u16",
            "extension_identity", "score_q64", "cap_i32", "threshold_count_i32",
            "thresholds_used_q64", "category_i32",
        })
        result = {
            "index": _integer(row["index"], slot + ".index", 32, unsigned=True),
            "observed": _boolean(row["observed"], slot + ".observed"),
            "ready": _boolean(row["ready"], slot + ".ready"),
            "reason": _string(row["reason"], slot + ".reason", optional=True),
            "property_key_u16": _number(row["property_key_u16"], slot + ".property_key_u16", 16, unsigned=True),
            "extension_identity": _string(row["extension_identity"], slot + ".extension_identity", optional=True),
            "score_q64": None if row["score_q64"] is None else _values_q64([row["score_q64"]], slot + ".score_q64")[0],
            "cap_i32": _number(row["cap_i32"], slot + ".cap_i32", 32),
            "threshold_count_i32": _number(row["threshold_count_i32"], slot + ".threshold_count_i32", 32),
            "thresholds_used_q64": _values_q64(row["thresholds_used_q64"], slot + ".thresholds_used_q64"),
            "category_i32": _number(row["category_i32"], slot + ".category_i32", 32),
        }
        if result["index"] != index or result["thresholds_used_q64"] is None:
            raise ValueError(slot + " lost its physical input slot or consumed threshold prefix")
        if result["observed"] and not leaf["stages"][index]["observed"]:
            raise ValueError(slot + " lacks its natural count callback")
        if not result["observed"]:
            if (result["ready"] or result["reason"] != "piety_category_unobserved"
                    or result["thresholds_used_q64"]
                    or any(result[key] is not None for key in (
                        "property_key_u16", "extension_identity", "score_q64",
                        "cap_i32", "threshold_count_i32", "category_i32"))):
                raise ValueError(slot + " unobserved source cannot supply a category")
        if result["category_i32"] is not None:
            extension = result["extension_identity"]
            if extension is None:
                raise ValueError(slot + " category lacks its copied extension decision")
            if int(extension, 16) == 0:
                expected = 0
            else:
                score, cap, count = (result[key] for key in (
                    "score_q64", "cap_i32", "threshold_count_i32"))
                if score is None or cap is None or count is None:
                    raise ValueError(slot + " category lacks its signed resource operands")
                used = result["thresholds_used_q64"]
                rank = 0
                for threshold in used:
                    if score < threshold:
                        break
                    rank += 1
                if (len(used) > max(count, 0) or rank < len(used) - 1
                        or rank < max(count, 0) and rank == len(used)):
                    raise ValueError(slot + " category lacks its consumed threshold boundary")
                expected = rank if cap < 0 else min(rank, cap)
            if result["category_i32"] != expected:
                raise ValueError(slot + " category differs from its actual getter operands")
        ready = (result["observed"] and result["property_key_u16"] is not None
                 and result["category_i32"] is not None)
        if result["ready"] is not ready or ready and result["reason"] is not None:
            raise ValueError(slot + " readiness differs from its historical key/category")
        stages.append(result)
    return {**_PIETY_SOURCE, "stages": stages}


_CLASSIFIED_PIETY_SOURCE = {
    "source_stage": "before_each_original_count",
    "context_rows_offset": 0, "context_count_offset": 12,
    "row_stride_bytes": 16, "row_pc_offset": 0, "row_scale_offset": 8,
    "classified_reader_rva": 0x2438980, "key_lookup_rva": 0x23036E0,
}
_CLASSIFIED_LOOKUPS = {"sentinel", "empty", "absent", "mapped", "unavailable"}


def _classified_q64(value: object, field: str) -> int | None:
    return None if value is None else _values_q64([value], field)[0]


def _classified_pointer(value: object, field: str) -> str | None:
    pointer = _string(value, field, optional=True)
    if pointer is not None:
        try:
            address = int(pointer, 16)
        except ValueError as error:
            raise ValueError(field + " must retain a native pointer identity") from error
        if not 0 <= address < 2**64:
            raise ValueError(field + " must retain a native pointer identity")
    return pointer


def _classified_piety_row(value: object, field: str, index: int, key: int | None) -> dict:
    raw = _dict(value, field, {
        "native_index", "ready", "reason", "pc_identity", "pc_count_i32",
        "lookup_selection", "selected_index_u32", "raw_value_q64", "scale_q64",
    })
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "pc_identity": _classified_pointer(raw["pc_identity"], field + ".pc_identity"),
        "pc_count_i32": _number(raw["pc_count_i32"], field + ".pc_count_i32", 32),
        "lookup_selection": _string(raw["lookup_selection"], field + ".lookup_selection"),
        "selected_index_u32": _number(raw["selected_index_u32"], field + ".selected_index_u32", 32, unsigned=True),
        "raw_value_q64": _classified_q64(raw["raw_value_q64"], field + ".raw_value_q64"),
        "scale_q64": _classified_q64(raw["scale_q64"], field + ".scale_q64"),
    }
    selection = result["lookup_selection"]
    if result["native_index"] != index or selection not in _CLASSIFIED_LOOKUPS:
        raise ValueError(field + " changed its physical row order or native lookup selection")
    count, selected = result["pc_count_i32"], result["selected_index_u32"]
    if selection == "sentinel":
        if key != 0xFFFF or selected is not None or result["raw_value_q64"] != 0:
            raise ValueError(field + " sentinel lookup lacks its original FFFF early zero")
    elif selection != "unavailable":
        if (key is None or key == 0xFFFF or result["pc_identity"] is None
                or int(result["pc_identity"], 16) == 0):
            raise ValueError(field + " keyed lookup lacks its original key/PC operands")
        if selection == "mapped":
            # The selected physical index survives an unread value QWORD.
            if count is None or count <= 0 or selected is None or selected >= count:
                raise ValueError(field + " mapped lookup lost its physical count/index")
        elif (count is None or count < 0 or selected is not None
              or result["raw_value_q64"] != 0 or selection == "empty" and count != 0):
            raise ValueError(field + " zero lookup disagrees with its native selection")
    ready = (selection != "unavailable" and result["raw_value_q64"] is not None
             and result["scale_q64"] is not None)
    if result["ready"] is not ready or (result["reason"] is None) != ready:
        raise ValueError(field + " readiness differs from independently copied row operands")
    return result


def _classified_piety_inputs(value: object, leaf: dict) -> dict:
    field = FIELD_NAME + ".classified_piety_inputs"
    raw = _dict(value, field, {*_CLASSIFIED_PIETY_SOURCE, "stages"})
    for key, expected in _CLASSIFIED_PIETY_SOURCE.items():
        actual = (_string(raw[key], field + "." + key) if key == "source_stage" else
                  _integer(raw[key], field + "." + key, 32, unsigned=True))
        if actual != expected:
            raise ValueError(field + " changed its actual historical classified source")
    if not isinstance(raw["stages"], list) or len(raw["stages"]) != STAGE_COUNT:
        raise ValueError(field + " must retain all six historical stage slots")
    stages = []
    for index, value in enumerate(raw["stages"]):
        slot = f"{field}.stages[{index}]"
        stage = _dict(value, slot, {
            "index", "observed", "ready", "reason", "property_key_u16",
            "row_count_i32", "row_array_identity", "rows",
        })
        result = {
            "index": _integer(stage["index"], slot + ".index", 32, unsigned=True),
            "observed": _boolean(stage["observed"], slot + ".observed"),
            "ready": _boolean(stage["ready"], slot + ".ready"),
            "reason": _string(stage["reason"], slot + ".reason", optional=True),
            "property_key_u16": _number(stage["property_key_u16"], slot + ".property_key_u16", 16, unsigned=True),
            "row_count_i32": _number(stage["row_count_i32"], slot + ".row_count_i32", 32),
            "row_array_identity": _classified_pointer(stage["row_array_identity"], slot + ".row_array_identity"),
        }
        if result["index"] != index or not isinstance(stage["rows"], list):
            raise ValueError(slot + " lost its physical stage or ordered row observations")
        result["rows"] = [
            _classified_piety_row(row, f"{slot}.rows[{row_index}]", row_index,
                                  result["property_key_u16"])
            for row_index, row in enumerate(stage["rows"])
        ]
        if result["observed"] and not leaf["stages"][index]["observed"]:
            raise ValueError(slot + " lacks its natural original count callback")
        if not result["observed"]:
            if (result["reason"] != "classified_piety_unobserved" or result["rows"]
                    or any(result[key] is not None for key in (
                        "property_key_u16", "row_count_i32", "row_array_identity"))):
                raise ValueError(slot + " unobserved source cannot supply classified operands")
        count, pointer = result["row_count_i32"], result["row_array_identity"]
        if count is None or count <= 0:
            if result["rows"]:
                raise ValueError(slot + " absent/empty row count cannot supply physical rows")
        elif len(result["rows"]) > count:
            raise ValueError(slot + " supplied more rows than its actual physical count")
        # Count zero is the literal reader's early exit: no row pointer or key
        # is required. Other stages retain their own partial source observations.
        ready = (result["observed"] and count is not None and count >= 0 and (
            count == 0 or (result["property_key_u16"] is not None
                           and pointer is not None and int(pointer, 16) != 0
                           and len(result["rows"]) == count
                           and all(row["ready"] for row in result["rows"]))))
        if result["ready"] is not ready or (result["reason"] is None) != ready:
            raise ValueError(slot + " readiness differs from its own historical row source")
        piety = leaf.get("piety_category_inputs")
        if piety is not None:
            piety_key = piety["stages"][index]["property_key_u16"]
            if (piety_key is not None and result["property_key_u16"] is not None
                    and piety_key != result["property_key_u16"]):
                raise ValueError(slot + " changed its same-call physical piety key")
        stages.append(result)
    return {**_CLASSIFIED_PIETY_SOURCE, "stages": stages}


def normalize_person_six_stage_capture_12004(value: object) -> dict | None:
    """Retain six owned stages, including incomplete and unread observations."""
    if value is None:
        return None
    aggregate_fields = {"pre_six_aggregate", "post_six_aggregate",
                        "aggregate_postimage_inputs_ready", "aggregate_postimage_comparison_ready"}
    has_aggregate = isinstance(value, dict) and "pre_six_aggregate" in value
    has_preparation = isinstance(value, dict) and "preparation_model" in value
    has_base_points = isinstance(value, dict) and "base_point_inputs" in value
    has_piety_category = isinstance(value, dict) and "piety_category_inputs" in value
    has_classified_piety = isinstance(value, dict) and "classified_piety_inputs" in value
    raw = _dict(value, FIELD_NAME, {
        "schema", "build_version", "executable_sha256", "configured",
        "capture_observed", "capture_complete", "ready", "raw_counts_ready",
        "reason", "capture_sequence", "capture_date_raw", "character_id",
        "capture_thread_id", "query_thread_id",
        *_POINTERS, "stages", "source_stage", "historical_capture",
        "actual_model_write_performed", "full_helper_ready",
    } | (aggregate_fields if has_aggregate else set())
      | ({"preparation_model"} if has_preparation else set())
      | ({"base_point_inputs"} if has_base_points else set())
      | ({"piety_category_inputs"} if has_piety_category else set())
      | ({"classified_piety_inputs"} if has_classified_piety else set()))
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {
        "schema": SCHEMA,
        "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "source_stage": _string(raw["source_stage"], FIELD_NAME + ".source_stage"),
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
    if (result["source_stage"] != SOURCE_STAGE
            or result["historical_capture"] is not True
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
    if has_aggregate:
        pre = _aggregate(raw["pre_six_aggregate"], FIELD_NAME + ".pre_six_aggregate",
                         "before_first_count_callback")
        post = _aggregate(raw["post_six_aggregate"], FIELD_NAME + ".post_six_aggregate",
                          "same_thread_capture_completion")
        inputs_ready = _boolean(raw["aggregate_postimage_inputs_ready"], FIELD_NAME + ".aggregate_postimage_inputs_ready")
        comparison_ready = _boolean(raw["aggregate_postimage_comparison_ready"], FIELD_NAME + ".aggregate_postimage_comparison_ready")
        if pre["observed"] and (not result["capture_observed"] or not result["stages"][0]["observed"]):
            raise ValueError(FIELD_NAME + " baseline lacks its actual first callback")
        if post["observed"] != result["capture_complete"]:
            raise ValueError(FIELD_NAME + " completion aggregate lacks its same-thread completion")
        for aggregate in (pre, post):
            if aggregate["observed"] and int(aggregate["pc"]["identity"], 16) != int(result["context_identity"], 16) + 0x68:
                raise ValueError(FIELD_NAME + " aggregate PC differs from captured context+68")
        if inputs_ready != (result["ready"] and pre["observed"] and pre["pc"]["ready"]):
            raise ValueError(FIELD_NAME + " aggregate input readiness differs from owned baseline and requests")
        if comparison_ready != (inputs_ready and post["observed"] and post["pc"]["ready"]):
            raise ValueError(FIELD_NAME + " comparison readiness differs from actual completion PC")
        result.update(pre_six_aggregate=pre, post_six_aggregate=post,
                      aggregate_postimage_inputs_ready=inputs_ready,
                      aggregate_postimage_comparison_ready=comparison_ready)
    if has_preparation:
        result["preparation_model"] = _preparation_model(raw["preparation_model"], result)
    if has_base_points:
        result["base_point_inputs"] = _base_point_inputs(raw["base_point_inputs"], result)
    if has_piety_category:
        result["piety_category_inputs"] = _piety_category_inputs(raw["piety_category_inputs"], result)
    if has_classified_piety:
        result["classified_piety_inputs"] = _classified_piety_inputs(raw["classified_piety_inputs"], result)
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


def emit_captured_person_pre_six_aggregate_12004(section: object) -> dict:
    """Publish the owned actual baseline; an older capture cannot supply empty state."""
    character, leaf = _joined_leaf(section)
    aggregate = leaf.get("pre_six_aggregate")
    if not leaf.get("aggregate_postimage_inputs_ready") or aggregate is None:
        raise ValueError("Required native input unavailable: actual pre-six aggregate baseline")
    pc = aggregate["pc"]
    return {
        "character_id": character,
        "capture_sequence": leaf["capture_sequence"],
        "capture_date_raw": leaf["capture_date_raw"],
        "capture_thread_id": leaf["capture_thread_id"],
        "context_identity": leaf["context_identity"],
        "source_pc_identity": pc["identity"],
        "property_block": {
            "keys_count": pc["count_i32"],
            "keys_u16": list(pc["properties"]["keys_u16"]),
            "values_q64": list(pc["properties"]["values_q64"]),
        },
        "historical_capture": True,
        "source_stage": aggregate["source_stage"],
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


def emit_captured_person_preparation_model_12004(section: object) -> dict:
    """Publish the Model/owner copied before the first original callback."""
    character, leaf = _joined_leaf(section)
    preparation = leaf.get("preparation_model")
    if preparation is None or not preparation["ready"]:
        reason = preparation["reason"] if preparation is not None else "preparation_model_unobserved"
        raise ValueError("Required native input unavailable: " + (reason or "preparation Model"))
    return {
        "character_id": character,
        "capture_sequence": leaf["capture_sequence"],
        "capture_date_raw": leaf["capture_date_raw"],
        "capture_thread_id": leaf["capture_thread_id"],
        "context_identity": leaf["context_identity"],
        "model_identity": preparation["model_identity"],
        "owner_character_identity": preparation["owner_character_identity"],
        "owner_character_id": preparation["owner_character_id"],
        "owner_matches_capture": preparation["owner_matches_capture"],
        "context_offset": preparation["context_offset"],
        "owner_offset": preparation["owner_offset"],
        "source_stage": preparation["source_stage"],
        "historical_capture": True,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


def _base_point_provenance(character: int, leaf: dict) -> dict:
    return {
        "character_id": character,
        "character_identity": leaf["character_identity"],
        "context_identity": leaf["context_identity"],
        "capture_sequence": leaf["capture_sequence"],
        "capture_date_raw": leaf["capture_date_raw"],
        "capture_thread_id": leaf["capture_thread_id"],
        "source_stage": "before_each_original_count",
        "historical_capture": True,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


def emit_captured_person_base_points_12004(section: object) -> dict:
    """Publish six owned pre-call base DWORDs, independently of append readiness."""
    character, leaf = _joined_leaf(section)
    base = leaf.get("base_point_inputs")
    if base is None or not base["ready"]:
        reason = base["reason"] if base is not None else "base_point_unobserved"
        raise ValueError("Required native input unavailable: " + reason)
    return _base_point_provenance(character, leaf) | {
        "character_offset": base["character_offset"],
        "stride_bytes": base["stride_bytes"],
        "values_i32": list(base["values_i32"]),
    }


def emit_captured_person_base_point_12004(section: object, native_index: object) -> dict:
    """Publish one observed stage's base operand despite another unread stage."""
    character, leaf = _joined_leaf(section)
    index = _integer(native_index, FIELD_NAME + ".base_point_inputs.index", 32, unsigned=True)
    if index >= STAGE_COUNT:
        raise ValueError("Required native input unavailable: base point stage")
    base = leaf.get("base_point_inputs")
    if base is None or not base["observed"][index]:
        raise ValueError("Required native input unavailable: base_point_unobserved")
    value = base["values_i32"][index]
    if value is None:
        raise ValueError("Required native input unavailable: base_point_unread")
    return _base_point_provenance(character, leaf) | {
        "stage_index": index,
        "source_offset_bytes": base["character_offset"] + base["stride_bytes"] * index,
        "value_i32": value,
    }


def emit_captured_person_piety_category_12004(section: object, native_index: object) -> dict:
    """Publish one actual per-stage category/key and the inputs explaining it."""
    character, leaf = _joined_leaf(section)
    index = _integer(native_index, FIELD_NAME + ".piety_category_inputs.index", 32, unsigned=True)
    if index >= STAGE_COUNT:
        raise ValueError("Required native input unavailable: piety category stage")
    inputs = leaf.get("piety_category_inputs")
    if inputs is None:
        raise ValueError("Required native input unavailable: piety_category_unobserved")
    stage = inputs["stages"][index]
    if not stage["ready"]:
        raise ValueError("Required native input unavailable: " + stage["reason"])
    return _base_point_provenance(character, leaf) | {
        "stage_index": index, "property_key_u16": stage["property_key_u16"],
        "category_multiplier_i32": stage["category_i32"],
        "extension_identity": stage["extension_identity"],
        "score_q64": stage["score_q64"], "cap_i32": stage["cap_i32"],
        "threshold_count_i32": stage["threshold_count_i32"],
        "thresholds_used_q64": list(stage["thresholds_used_q64"]),
    }


def _classified_piety_stage(section: object, native_index: object, mode: object) -> tuple[int, dict, dict, int]:
    character, leaf = _joined_leaf(section)
    index = _integer(native_index, FIELD_NAME + ".classified_piety_inputs.index", 32, unsigned=True)
    mode = _integer(mode, FIELD_NAME + ".classified_piety_inputs.mode", 32)
    if index >= STAGE_COUNT or mode not in (1, 2):
        raise ValueError("Required native input unavailable: classified piety stage/mode")
    inputs = leaf.get("classified_piety_inputs")
    if inputs is None:
        raise ValueError("Required native input unavailable: classified_piety_unobserved")
    return character, leaf, inputs["stages"][index], mode


def _classified_piety_provenance(character: int, leaf: dict, stage: dict, mode: int) -> dict:
    return _base_point_provenance(character, leaf) | {
        "stage_index": stage["index"], "mode": mode,
        "property_key_u16": stage["property_key_u16"],
        "row_array_identity": stage["row_array_identity"],
        "classified_reader_rva": _CLASSIFIED_PIETY_SOURCE["classified_reader_rva"],
        "key_lookup_rva": _CLASSIFIED_PIETY_SOURCE["key_lookup_rva"],
        "source_evaluated": True, "native_mode_call_observed": False,
    }


def _classified_piety_scaled_row(row: dict, mode: int) -> dict:
    if not row["ready"]:
        raise ValueError("Required native input unavailable: " + row["reason"])
    scaled = native_fixed_mul_q_12004(row["raw_value_q64"], row["scale_q64"])
    included = scaled > 0 if mode == 1 else scaled < 0
    return row | {
        "scaled_value_q64": scaled, "included": included,
        "value_q64": scaled if included else 0,
    }


def emit_captured_person_classified_piety_row_12004(
        section: object, native_index: object, row_index: object, mode: object) -> dict:
    """Evaluate one owned ready row independently of other rows/category reads."""
    character, leaf, stage, mode = _classified_piety_stage(section, native_index, mode)
    index = _integer(row_index, FIELD_NAME + ".classified_piety_inputs.row_index", 32, unsigned=True)
    if not stage["observed"] or index >= len(stage["rows"]):
        raise ValueError("Required native input unavailable: classified piety row")
    return (_classified_piety_provenance(character, leaf, stage, mode)
            | _classified_piety_scaled_row(stage["rows"][index], mode))


def emit_captured_person_classified_piety_value_12004(
        section: object, native_index: object, mode: object) -> dict:
    """Evaluate modes 1/2 from owned rows, then the independently known category."""
    character, leaf, stage, mode = _classified_piety_stage(section, native_index, mode)
    if not stage["ready"]:
        raise ValueError("Required native input unavailable: " + stage["reason"])
    total, included = 0, []
    for row in stage["rows"]:
        term = _classified_piety_scaled_row(row, mode)
        if term["included"]:
            included.append(row["native_index"])
            total = _signed64(total + term["value_q64"])
    piety = leaf.get("piety_category_inputs")
    category_stage = piety["stages"][stage["index"]] if piety is not None else None
    category_ready = category_stage is not None and category_stage["ready"]
    category = category_stage["category_i32"] if category_ready else None
    direct_term = None
    if category_ready:
        quotient = _divide_q_from_instructions(_signed64(category * total))
        direct_term = quotient & 0xFFFFFFFF
        if direct_term & 0x80000000:
            direct_term -= 2**32
    return _classified_piety_provenance(character, leaf, stage, mode) | {
        "row_count_i32": stage["row_count_i32"],
        "value_q64": total, "included_native_indexes": included,
        "category_multiplier_i32": category,
        "direct_term_ready": category_ready, "direct_term_i32": direct_term,
        "direct_term_reason": (None if category_ready else
                               category_stage["reason"] if category_stage is not None else
                               "piety_category_unobserved"),
    }
