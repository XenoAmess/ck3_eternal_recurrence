"""Observed pair-opinion inputs for the actual4 2921A90 classifier.

The bound native pair getter returns the post-clamp signed32 total. Nonself
base/additional values remain unobserved. The preceding self-only contract
stays unchanged; selected PC rows reuse its numerical source semantics.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _string,
)
from .battle_person_conditional_2921a90_12004 import (
    _float, _float_i32, _request, _row, _state,
    normalize_person_conditional_2921a90_12004,
)
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_2921a90_opinion"
SCHEMA = "xar.ck3.person-following-2921a90-opinion-12004-v1"
_FIELDS = {
    "schema", "build_version", "executable_sha256", "character_id", "ready", "reason",
    "source_inputs", "opinion_rows", "classifier_ready", "classifier_reason",
    "classifier_result_i32", "selected_family", "selected_array_identity",
    "selected_count_i32", "rows", "occurrence_count",
}
_OPINION_FIELDS = {
    "source_index", "ready", "reason", "selected_full_character_id",
    "selected_character_identity", "toward_full_character_id", "toward_character_identity",
    "source_selection", "base_value", "additional_value", "total_opinion_i32",
    "high_threshold_bits_u32", "low_threshold_bits_u32", "vote",
}
_SELECTIONS = {"self_source_inputs", "native_pair_postclamp_28bc470", "unavailable"}


def _opinion(value, field, source, character_id, character_identity):
    raw = _dict(value, field, _OPINION_FIELDS)
    result = {
        "source_index": _integer(raw["source_index"], field + ".source_index", 32, unsigned=True),
        "ready": _boolean(raw["ready"], field + ".ready"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
        "source_selection": _string(raw["source_selection"], field + ".source_selection"),
    }
    for key in ("selected_character_identity", "toward_character_identity"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in ("selected_full_character_id", "toward_full_character_id",
                "high_threshold_bits_u32", "low_threshold_bits_u32"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    for key in ("base_value", "additional_value", "total_opinion_i32"):
        result[key] = _number(raw[key], field + "." + key, 32)
    result["vote"] = "" if raw["vote"] == "" else _string(raw["vote"], field + ".vote")
    _state(result["ready"], result["reason"], field)
    selection = result["source_selection"]
    if selection not in _SELECTIONS:
        raise ValueError(field + " unknown opinion source selection")
    if result["source_index"] != source["native_index"]:
        raise ValueError(field + " opinion occurrence changed its physical source index")
    if result["selected_character_identity"] != source["selected_character_identity"]:
        raise ValueError(field + " opinion owner differs from the selected source Character")
    if (result["toward_full_character_id"] != character_id
            or result["toward_character_identity"] != character_identity):
        raise ValueError(field + " opinion toward receiver differs from the original Character")
    if selection == "native_pair_postclamp_28bc470":
        if result["base_value"] is not None or result["additional_value"] is not None:
            raise ValueError(field + " pair total cannot fabricate base or additional opinion")
        if (result["selected_character_identity"] == character_identity
                or result["selected_full_character_id"] == character_id):
            raise ValueError(field + " nonself provider source selected the original Character")
    elif selection == "self_source_inputs":
        if (result["selected_character_identity"] != character_identity
                or result["selected_full_character_id"] != character_id
                or result["ready"] != source["ready"]
                or result["base_value"] != source["base_opinion_i32"]
                or result["additional_value"] != source["additional_opinion_i32"]
                or result["total_opinion_i32"] != source["clamped_i32"]
                or result["high_threshold_bits_u32"] != source["high_threshold_bits_u32"]
                or result["low_threshold_bits_u32"] != source["low_threshold_bits_u32"]):
            raise ValueError(field + " self vote differs from its unchanged source proof")
    if not result["ready"]:
        if result["vote"] != "":
            raise ValueError(field + " unread opinion cannot supply a high, low or middle vote")
        return result
    if (selection == "unavailable" or result["selected_full_character_id"] in (None, 0, 0xFFFFFFFF)
            or result["selected_character_identity"] is None
            or result["total_opinion_i32"] is None
            or result["high_threshold_bits_u32"] is None):
        raise ValueError(field + " known opinion lacks the actual pair total or threshold")
    number = _float_i32(result["total_opinion_i32"])
    if number >= _float(result["high_threshold_bits_u32"]):
        vote = "high"
        if result["low_threshold_bits_u32"] is not None:
            raise ValueError(field + " low threshold was undemanded after a high match")
    else:
        if result["low_threshold_bits_u32"] is None:
            raise ValueError(field + " low threshold is demanded")
        vote = "low" if _float(result["low_threshold_bits_u32"]) >= number else "middle"
    if result["vote"] != vote:
        raise ValueError(field + " vote disagrees with the observed postclamp float32 comparison")
    return result


def normalize_person_conditional_opinion_12004(value):
    """Retain the unchanged prior inputs and validate new pair observations."""
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, _FIELDS)
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    source = normalize_person_conditional_2921a90_12004(raw["source_inputs"])
    if source is None:
        raise ValueError(FIELD_NAME + " unchanged conditional source inputs are required")
    result = {"schema": SCHEMA, "build_version": CK3_12004.game_version,
              "executable_sha256": CK3_12004.executable_sha256, "source_inputs": source}
    result["character_id"] = _number(raw["character_id"], FIELD_NAME + ".character_id", 32, unsigned=True)
    if result["character_id"] != source["character_id"]:
        raise ValueError(FIELD_NAME + " source inputs have a different full CharacterID")
    for key in ("ready", "classifier_ready"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    for key in ("reason", "classifier_reason", "selected_array_identity"):
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    for key in ("classifier_result_i32", "selected_count_i32"):
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32)
    result["occurrence_count"] = _number(raw["occurrence_count"], FIELD_NAME + ".occurrence_count", 32, unsigned=True)
    result["selected_family"] = _string(raw["selected_family"], FIELD_NAME + ".selected_family")
    for key in ("opinion_rows", "rows"):
        if not isinstance(raw[key], list):
            raise ValueError(FIELD_NAME + "." + key + " must preserve physical order")
    if len(raw["opinion_rows"]) > len(source["classifier_rows"]):
        raise ValueError(FIELD_NAME + " opinion rows lack original source occurrences")
    opinions = [_opinion(row, f"{FIELD_NAME}.opinion_rows[{i}]", source["classifier_rows"][i],
                         result["character_id"], source["character_identity"])
                for i, row in enumerate(raw["opinion_rows"])]
    rows = [_row(row, f"{FIELD_NAME}.rows[{i}]") for i, row in enumerate(raw["rows"])]
    result["opinion_rows"], result["rows"] = opinions, rows
    if ([row["source_index"] for row in opinions] != list(range(len(opinions)))
            or [row["native_index"] for row in rows] != list(range(len(rows)))):
        raise ValueError(FIELD_NAME + " physical source occurrence order changed")
    _state(result["ready"], result["reason"], FIELD_NAME)
    if result["classifier_ready"] or result["selected_family"] != "not_demanded":
        _state(result["classifier_ready"], result["classifier_reason"], FIELD_NAME + ".classifier")
    classifier = result["classifier_result_i32"]
    if result["classifier_ready"]:
        if classifier not in (0, 1, 2):
            raise ValueError(FIELD_NAME + " known classifier lacks its actual result")
        count = source["classifier_count_i32"]
        if source["classifier_ready"]:
            if classifier != source["classifier_result_i32"]:
                raise ValueError(FIELD_NAME + " known preceding classifier changed")
        if count is not None and count > 0:
            if len(opinions) != count or any(not row["ready"] for row in opinions):
                raise ValueError(FIELD_NAME + " classifier lacks complete observed opinion occurrences")
            high = sum(row["vote"] == "high" for row in opinions)
            low = sum(row["vote"] == "low" for row in opinions)
            middle = len(opinions) - high - low
            expected = 0 if high > low and high > middle else 2 if low > high and low > middle else 1
            if classifier != expected:
                raise ValueError(FIELD_NAME + " classifier differs from the physical opinion majority")
        elif not source["classifier_ready"] or opinions:
            raise ValueError(FIELD_NAME + " empty classifier lacks its preceding source proof")
    elif classifier is not None:
        raise ValueError(FIELD_NAME + " unread opinion classifier cannot supply a result")
    family, count = result["selected_family"], result["selected_count_i32"]
    if count is not None and (count < 0 and rows or count >= 0 and len(rows) > count):
        raise ValueError(FIELD_NAME + " selected rows disagree with the observed count")
    if result["ready"]:
        if family == "not_demanded":
            if not source["ready"] or source["selected_family"] != family or opinions or rows:
                raise ValueError(FIELD_NAME + " bypass lacks unchanged preceding admission inputs")
        elif family == "classifier_other_empty":
            if not result["classifier_ready"] or classifier != 1 or rows:
                raise ValueError(FIELD_NAME + " empty selected branch lacks an observed classifier")
        elif family in ("bb0_bbc", "b80_b8c"):
            expected = "bb0_bbc" if classifier == 0 else "b80_b8c"
            if (not result["classifier_ready"] or classifier not in (0, 2) or family != expected
                    or count is None or count < 0 or len(rows) != count
                    or result["selected_array_identity"] is None or any(not row["ready"] for row in rows)):
                raise ValueError(FIELD_NAME + " selected family lacks actual classifier or PC operands")
        else:
            raise ValueError(FIELD_NAME + " unknown selected family")
        if result["occurrence_count"] != sum(row["weight_q64"] != 0 for row in rows):
            raise ValueError(FIELD_NAME + " downstream append occurrence count differs")
    elif result["occurrence_count"] is not None:
        raise ValueError(FIELD_NAME + " incomplete selected family cannot claim a full occurrence count")
    return result


def _joined(section):
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_conditional_opinion_12004(section.get(FIELD_NAME))
    if leaf is None or leaf["character_id"] != _integer(
            section.get("character_id"), "current_person_state.character_id", 32, unsigned=True):
        raise ValueError("Required same-Character input unavailable: " + FIELD_NAME)
    return leaf


def _opinion_request(row):
    return tuple(replace(request, source_name=FIELD_NAME + "_12004") for request in _request(row))


def emit_opinion_conditional_2921a90_requests_from_current_source_inputs_12004(section):
    leaf = _joined(section)
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + leaf["reason"])
    return tuple(request for row in leaf["rows"] for request in _opinion_request(row))


def emit_opinion_conditional_2921a90_row_requests_from_current_source_inputs_12004(section, native_index):
    leaf = _joined(section)
    index = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
    row = next((row for row in leaf["rows"] if row["native_index"] == index), None)
    if row is None or not row["ready"]:
        raise ValueError("Required native input unavailable: " + (
            row["reason"] if row else FIELD_NAME + " row unobserved"))
    return _opinion_request(row)


def emit_complete_opinion_2921a90_requests_from_current_source_inputs_12004(section):
    """Same receiver: preceding direct calls, then new conditional occurrences."""
    from .battle_person_following_2921a90_12004 import (
        normalize_person_following_2921a90_12004,
        emit_following_2921a90_direct_requests_from_current_source_inputs_12004,
    )
    leaf = _joined(section)
    direct = normalize_person_following_2921a90_12004(section.get("following_2921a90"))
    if direct is None or any(direct[key] != leaf["source_inputs"][key] for key in (
            "character_identity", "selected_model_identity", "selected_object_identity")):
        raise ValueError("Required same-receiver direct family unavailable: " + FIELD_NAME)
    first = emit_following_2921a90_direct_requests_from_current_source_inputs_12004(section)
    following = emit_opinion_conditional_2921a90_requests_from_current_source_inputs_12004(section)
    return first + tuple(replace(request, source_ordinal=len(direct["direct_rows"]) + request.source_ordinal)
                         for request in following)
