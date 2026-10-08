"""Actual4 conditional admission and local numerical operands for 2921A90.

All-self classification and literal weights are source closed. Other-person
opinions and dynamic expressions remain specific missing inputs. The native
observer copies fields only; this module scales/quantizes the physical PC and
releases the real downstream unit occurrences, including nonzero empty PCs.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import struct

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)
from .battle_person_carrier_direct_12004 import _values_q64
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_2921a90_conditional"
SCHEMA = "xar.ck3.person-following-2921a90-conditional-12004-v1"
_POINTERS = (
    "character_identity", "selected_model_identity", "selected_object_identity",
    "conditional_definition_identity", "classifier_land_identity",
    "classifier_header_identity", "classifier_array_identity", "selected_array_identity",
)
_U32 = ("character_id", "classifier_magic_u32", "classifier_full_id_u32", "occurrence_count")
_I32 = (
    "gate_b8c_count_i32", "gate_bbc_count_i32", "classifier_default_guard_i32",
    "classifier_count_i32", "classifier_result_i32", "selected_count_i32",
)
_FIELDS = {
    "schema", "build_version", "executable_sha256", "ready", "reason", "admitted",
    "classifier_ready", "classifier_reason", "classifier_header_selection",
    "classifier_rows", "selected_family", "rows", *_POINTERS, *_U32, *_I32,
}
_VOTE_POINTERS = (
    "registry_identity", "registry_slots_identity", "candidate_character_identity",
    "selected_character_identity", "selected_scratch_identity",
)
_VOTE_U32 = (
    "requested_full_id_u32", "registry_count_u32", "candidate_full_id_u32",
    "high_threshold_bits_u32", "low_threshold_bits_u32",
)
_VOTE_I32 = ("base_opinion_i32", "additional_opinion_i32", "minimum_i32", "maximum_i32", "clamped_i32")
_VOTE_FIELDS = {"native_index", "ready", "reason", "resolution_selection", "vote",
                *_VOTE_POINTERS, *_VOTE_U32, *_VOTE_I32}
_ROW_POINTERS = (
    "object_identity", "expression_tree_278_identity", "expression_scoped_268_identity",
    "metadata_registry_identity", "metadata_table_identity",
)
_ROW_I32 = ("expression_flag_280_i32", "expression_count_1d4_i32", "keys_count_i32", "values_count_i32")
_ROW_FIELDS = {"native_index", "ready", "reason", "raw_value_258_q64", "weight_q64",
               "properties", "metadata", *_ROW_POINTERS, *_ROW_I32}
_METADATA_FIELDS = {"native_index", "ready", "reason", "key_u16", "definition_identity", "flag_ba_u8", "flag_b8_u8"}


def _q64(value, field):
    if value is None:
        return None
    return _values_q64([value], field)[0]


def _state(ready, reason, field):
    if ready and reason is not None or not ready and not reason:
        raise ValueError(field + " readiness and reason disagree")


def _float(bits):
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def _float_i32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _vote(value, field, character):
    raw = _dict(value, field, _VOTE_FIELDS)
    ready = _boolean(raw["ready"], field + ".ready")
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
              "ready": ready,
              "reason": _string(raw["reason"], field + ".reason", optional=True),
              "vote": "" if not ready and raw["vote"] == "" else _string(raw["vote"], field + ".vote"),
              "resolution_selection": _string(raw["resolution_selection"], field + ".resolution_selection")}
    for key in _VOTE_POINTERS:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in _VOTE_U32:
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    for key in _VOTE_I32:
        result[key] = _number(raw[key], field + "." + key, 32)
    _state(result["ready"], result["reason"], field)
    if result["ready"]:
        if (result["selected_character_identity"] != character
                or result["selected_scratch_identity"] is None
                or result["base_opinion_i32"] != 100 or result["additional_opinion_i32"] != 0
                or result["minimum_i32"] is None or result["high_threshold_bits_u32"] is None):
            raise ValueError(field + " known vote lacks actual self-only source operands")
        minimum = result["minimum_i32"]
        if 100 < minimum:
            clamped = minimum
            if result["maximum_i32"] is not None:
                raise ValueError(field + " maximum was undemanded below the minimum")
        else:
            if result["maximum_i32"] is None:
                raise ValueError(field + " maximum is demanded")
            clamped = min(100, result["maximum_i32"])
        if result["clamped_i32"] != clamped:
            raise ValueError(field + " native clamp disagrees with its actual globals")
        number = _float_i32(clamped)
        if number >= _float(result["high_threshold_bits_u32"]):
            vote = "high"
            if result["low_threshold_bits_u32"] is not None:
                raise ValueError(field + " low threshold was undemanded after high match")
        else:
            if result["low_threshold_bits_u32"] is None:
                raise ValueError(field + " low threshold is demanded")
            vote = "low" if _float(result["low_threshold_bits_u32"]) >= number else "middle"
        if result["vote"] != vote:
            raise ValueError(field + " vote disagrees with actual float32 comparisons")
    return result


def _metadata(value, field):
    raw = _dict(value, field, _METADATA_FIELDS)
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
              "ready": _boolean(raw["ready"], field + ".ready"),
              "reason": _string(raw["reason"], field + ".reason", optional=True),
              "key_u16": _number(raw["key_u16"], field + ".key_u16", 16, unsigned=True),
              "definition_identity": _string(raw["definition_identity"], field + ".definition_identity", optional=True),
              "flag_ba_u8": _number(raw["flag_ba_u8"], field + ".flag_ba_u8", 8, unsigned=True),
              "flag_b8_u8": _number(raw["flag_b8_u8"], field + ".flag_b8_u8", 8, unsigned=True)}
    _state(result["ready"], result["reason"], field)
    if result["ready"]:
        if result["key_u16"] is None or result["definition_identity"] is None or result["flag_ba_u8"] is None:
            raise ValueError(field + " known metadata lacks its demanded fields")
        if result["flag_ba_u8"] != 0:
            if result["flag_b8_u8"] is not None:
                raise ValueError(field + " B8 was undemanded after nonzero BA")
        elif result["flag_b8_u8"] is None:
            raise ValueError(field + " B8 is demanded")
    return result


def _row(value, field):
    raw = _dict(value, field, _ROW_FIELDS)
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
              "ready": _boolean(raw["ready"], field + ".ready"),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    for key in _ROW_POINTERS:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in _ROW_I32:
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("raw_value_258_q64", "weight_q64"):
        result[key] = _q64(raw[key], field + "." + key)
    block = raw["properties"]
    if block is not None:
        block = _dict(block, field + ".properties", {"keys_u16", "values_q64"})
        block = {"keys_u16": _numbers(block["keys_u16"], field + ".properties.keys_u16", 16, unsigned=True),
                 "values_q64": _values_q64(block["values_q64"], field + ".properties.values_q64")}
    result["properties"] = block
    if not isinstance(raw["metadata"], list):
        raise ValueError(field + " metadata must retain physical key order")
    result["metadata"] = [_metadata(m, f"{field}.metadata[{i}]") for i, m in enumerate(raw["metadata"])]
    _state(result["ready"], result["reason"], field)
    weight = result["weight_q64"]
    if weight is not None:
        flag = result["expression_flag_280_i32"]
        if flag == 0:
            if weight != 100000 or any(result[k] is not None for k in (
                    "expression_tree_278_identity", "expression_scoped_268_identity",
                    "expression_count_1d4_i32", "raw_value_258_q64")):
                raise ValueError(field + " default weight disagrees with demanded source")
        elif (flag is None or result["expression_tree_278_identity"] != "0x0"
              or result["expression_scoped_268_identity"] != "0x0"
              or result["expression_count_1d4_i32"] != 0 or weight != result["raw_value_258_q64"]):
            raise ValueError(field + " raw weight lacks its three actual zero expression guards")
    if result["ready"]:
        if result["object_identity"] is None or weight is None:
            raise ValueError(field + " known row lacks physical identity or evaluated scalar")
        if weight == 0:
            if (block is not None or result["metadata"] or result["keys_count_i32"] is not None
                    or result["values_count_i32"] is not None):
                raise ValueError(field + " zero scalar demanded skipped PC operands")
        else:
            keys, values = result["keys_count_i32"], result["values_count_i32"]
            if (keys is None or values is None or keys < 0 or values < keys or block is None
                    or block["keys_u16"] is None or block["values_q64"] is None
                    or len(block["keys_u16"]) != keys or len(block["values_q64"]) != values
                    or len(result["metadata"]) != keys or any(not m["ready"] for m in result["metadata"])
                    or [m["native_index"] for m in result["metadata"]] != list(range(keys))
                    or [m["key_u16"] for m in result["metadata"]] != block["keys_u16"]):
                raise ValueError(field + " known row lacks actual independent PC counts or metadata")
    return result


def normalize_person_conditional_2921a90_12004(value):
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, _FIELDS)
    if raw["schema"] != SCHEMA or require_exact_native_build(raw["build_version"], raw["executable_sha256"]) != CK3_12004:
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {"schema": SCHEMA, "build_version": CK3_12004.game_version,
              "executable_sha256": CK3_12004.executable_sha256}
    for key in _POINTERS:
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in _U32:
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32, unsigned=True)
    for key in _I32:
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32)
    for key in ("ready", "classifier_ready"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    result["admitted"] = _boolean(raw["admitted"], FIELD_NAME + ".admitted", optional=True)
    for key in ("reason", "classifier_reason"):
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in ("classifier_header_selection", "selected_family"):
        result[key] = _string(raw[key], FIELD_NAME + "." + key)
    for key in ("rows", "classifier_rows"):
        if not isinstance(raw[key], list):
            raise ValueError(FIELD_NAME + "." + key + " must preserve physical order")
    votes = [_vote(v, f"{FIELD_NAME}.classifier_rows[{i}]", result["character_identity"])
             for i, v in enumerate(raw["classifier_rows"])]
    rows = [_row(r, f"{FIELD_NAME}.rows[{i}]") for i, r in enumerate(raw["rows"])]
    result["classifier_rows"], result["rows"] = votes, rows
    for sequence in (votes, rows):
        if [r["native_index"] for r in sequence] != list(range(len(sequence))):
            raise ValueError(FIELD_NAME + " source occurrence order changed")
    _state(result["ready"], result["reason"], FIELD_NAME)
    classifier = result["classifier_result_i32"]
    if result["classifier_ready"]:
        if result["classifier_reason"] is not None or classifier not in (0, 1, 2):
            raise ValueError(FIELD_NAME + " classifier readiness lacks actual result")
        invalid = (result["classifier_magic_u32"] is not None and result["classifier_magic_u32"] != 0x43686172
                   or result["classifier_full_id_u32"] == 0xFFFFFFFF)
        empty = result["classifier_count_i32"] == 0
        if invalid or empty:
            if classifier != 1 or votes:
                raise ValueError(FIELD_NAME + " actual classifier early return disagrees")
        else:
            if (result["classifier_count_i32"] is None or result["classifier_count_i32"] <= 0
                    or len(votes) != result["classifier_count_i32"] or any(not r["ready"] for r in votes)):
                raise ValueError(FIELD_NAME + " classifier lacks its complete physical votes")
            high = sum(v["vote"] == "high" for v in votes)
            low = sum(v["vote"] == "low" for v in votes)
            middle = len(votes) - high - low
            expected = 0 if high > low and high > middle else 2 if low > high and low > middle else 1
            if classifier != expected:
                raise ValueError(FIELD_NAME + " classifier majority disagrees")
        if result["classifier_header_selection"] == "static_default_5d21338" and result["classifier_default_guard_i32"] in (None, 0, -1):
            raise ValueError(FIELD_NAME + " default classifier header is uninitialized")
    elif classifier is not None:
        raise ValueError(FIELD_NAME + " unknown classifier cannot publish a supplied result")
    family = result["selected_family"]
    if result["ready"]:
        if family == "not_demanded":
            if not (result["admitted"] is False or result["admitted"] is True
                    and result["gate_b8c_count_i32"] == 0 and result["gate_bbc_count_i32"] == 0):
                raise ValueError(FIELD_NAME + " bypass lacks its actual admission or zero counts")
        elif family == "classifier_other_empty":
            if not result["classifier_ready"] or classifier != 1:
                raise ValueError(FIELD_NAME + " empty classifier branch lacks actual admission")
        elif family in ("bb0_bbc", "b80_b8c"):
            expected = "bb0_bbc" if classifier == 0 else "b80_b8c"
            count = result["selected_count_i32"]
            if (not result["classifier_ready"] or classifier not in (0, 2) or family != expected
                    or count is None or count < 0 or len(rows) != count or any(not r["ready"] for r in rows)):
                raise ValueError(FIELD_NAME + " selected family lacks actual classifier or rows")
        else:
            raise ValueError(FIELD_NAME + " unknown selected family")
        occurrences = sum(r["weight_q64"] != 0 for r in rows)
        if result["occurrence_count"] != occurrences:
            raise ValueError(FIELD_NAME + " downstream append occurrence count differs")
    elif result["occurrence_count"] is not None:
        raise ValueError(FIELD_NAME + " incomplete selected family cannot claim a full occurrence count")
    return result


def _i64(value):
    return (value + (1 << 63)) % (1 << 64) - (1 << 63)


def _div(value, divisor):
    return abs(value) // divisor * (-1 if value < 0 else 1)


def _scale(value, weight):
    """Actual2303380 identity/fast path and signed-maximum slow decomposition."""
    if weight == 100000:
        return value
    bias, span = 0xB504F333, 0x16A09E666
    if (value + bias) % (1 << 64) <= span and (weight + bias) % (1 << 64) <= span:
        return _div(_i64(value * weight), 100000)
    greater, lesser = max(value, weight), min(value, weight)
    quotient = _div(greater, 100000)
    remainder = _i64(greater - _i64(quotient * 100000))
    return _i64(_i64(quotient * lesser) + _div(_i64(remainder * lesser), 100000))


def _request(row):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    if row["weight_q64"] == 0:
        return ()
    values = [_scale(v, row["weight_q64"]) for v in row["properties"]["values_q64"]]
    for index, m in enumerate(row["metadata"]):
        if m["flag_ba_u8"] == 0 and not m["flag_b8_u8"] & 1:
            quotient = _div(values[index], 100000)
            narrowed = (quotient + (1 << 31)) % (1 << 32) - (1 << 31)
            values[index] = narrowed * 100000
    count = row["keys_count_i32"]
    return (NativeWeightedContributionRequest12003(
        source_ordinal=row["native_index"], source_name=FIELD_NAME + "_12004",
        first_row_index=0, row_count=1, definition_identity=row["object_identity"],
        base_property_block={"keys_count": count, "keys_u16": row["properties"]["keys_u16"],
                             "values_q64": values[:count]}, weight_q64=100000),)


def _joined(section):
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_conditional_2921a90_12004(section.get(FIELD_NAME))
    if leaf is None or leaf["character_id"] != _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True):
        raise ValueError("Required same-Character input unavailable: " + FIELD_NAME)
    return leaf


def emit_conditional_2921a90_requests_from_current_source_inputs_12004(section):
    leaf = _joined(section)
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + leaf["reason"])
    return tuple(request for row in leaf["rows"] for request in _request(row))


def emit_conditional_2921a90_row_requests_from_current_source_inputs_12004(section, native_index):
    leaf = _joined(section)
    selected = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
    row = next((r for r in leaf["rows"] if r["native_index"] == selected), None)
    if row is None or not row["ready"]:
        raise ValueError("Required native input unavailable: " + (row["reason"] if row else FIELD_NAME + " row unobserved"))
    return _request(row)


def emit_complete_2921a90_requests_from_current_source_inputs_12004(section):
    """Direct calls then selected conditional slot calls; no duplicate weighting."""
    from .battle_person_following_2921a90_12004 import (
        normalize_person_following_2921a90_12004,
        emit_following_2921a90_direct_requests_from_current_source_inputs_12004,
    )
    conditional = _joined(section)
    direct = normalize_person_following_2921a90_12004(section.get("following_2921a90"))
    if direct is None or any(direct[key] != conditional[key] for key in
                             ("character_identity", "selected_model_identity", "selected_object_identity")):
        raise ValueError("Required same-receiver direct family unavailable: " + FIELD_NAME)
    first = emit_following_2921a90_direct_requests_from_current_source_inputs_12004(section)
    following = emit_conditional_2921a90_requests_from_current_source_inputs_12004(section)
    return first + tuple(replace(r, source_ordinal=len(direct["direct_rows"]) + r.source_ordinal) for r in following)
