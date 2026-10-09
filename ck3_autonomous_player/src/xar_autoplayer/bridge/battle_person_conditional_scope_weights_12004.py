"""Actual4 row weights observed with an owned caller-equivalent scope.

Original literal/raw partial inputs retain their old contract. Native weights
are independently parsed without replacing the expression guards or treating
a missing shared scope prefix as a zero. No live Model merge is performed.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)
from .battle_person_carrier_direct_12004 import _values_q64
from .battle_person_conditional_2921a90_12004 import (
    _ROW_FIELDS, _ROW_I32, _ROW_POINTERS, _metadata, _q64, _request, _row, _state,
)
from .battle_person_conditional_opinion_12004 import normalize_person_conditional_opinion_12004
from .version_identity import CK3_12004, require_exact_native_build

FIELD_NAME = "following_2921a90_scope_weights"
SCHEMA = "xar.ck3.person-following-2921a90-scope-weights-12004-v1"
_FIELDS = {
    "schema", "build_version", "executable_sha256", "character_id", "selected_object_identity",
    "classifier_ready", "classifier_result_i32", "selected_family", "selected_array_identity",
    "selected_count_i32", "scope_initialized", "scope_kind_u16", "scope_payload_u32",
    "ready", "reason", "rows", "occurrence_count",
}
_FIELDS_ROW = {"native_index", "evaluation_selection", "weight_call_ordinal",
               "scope_prefix_ready", "source_inputs", "evaluated_inputs"}
_SELECTIONS = {"same_sample_source", "native_row_2872300", "unavailable"}


def _evaluated(value, field):
    """Native weight has its own proof; preserve every copied expression field."""
    if value is None:
        return None
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
    result["metadata"] = [_metadata(row, f"{field}.metadata[{i}]") for i, row in enumerate(raw["metadata"])]
    _state(result["ready"], result["reason"], field)
    if result["ready"]:
        weight = result["weight_q64"]
        if result["object_identity"] is None or weight is None:
            raise ValueError(field + " known native row lacks identity or observed weight")
        if weight == 0:
            if (block is not None or result["metadata"] or result["keys_count_i32"] is not None
                    or result["values_count_i32"] is not None):
                raise ValueError(field + " zero native weight demanded skipped PC inputs")
        else:
            keys, values = result["keys_count_i32"], result["values_count_i32"]
            if (keys is None or values is None or keys < 0 or values < keys or block is None
                    or block["keys_u16"] is None or block["values_q64"] is None
                    or len(block["keys_u16"]) != keys or len(block["values_q64"]) != values
                    or len(result["metadata"]) != keys or any(not row["ready"] for row in result["metadata"])
                    or [row["native_index"] for row in result["metadata"]] != list(range(keys))
                    or [row["key_u16"] for row in result["metadata"]] != block["keys_u16"]):
                raise ValueError(field + " known native row lacks independent PC counts or metadata")
    return result


def _scope_row(value, field, initialized):
    raw = _dict(value, field, _FIELDS_ROW)
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
        "evaluation_selection": _string(raw["evaluation_selection"], field + ".evaluation_selection"),
        "weight_call_ordinal": _number(raw["weight_call_ordinal"], field + ".weight_call_ordinal", 32, unsigned=True),
        "scope_prefix_ready": _boolean(raw["scope_prefix_ready"], field + ".scope_prefix_ready"),
        "source_inputs": _row(raw["source_inputs"], field + ".source_inputs"),
        "evaluated_inputs": _evaluated(raw["evaluated_inputs"], field + ".evaluated_inputs"),
    }
    selection, source, evaluated = (result[key] for key in
                                    ("evaluation_selection", "source_inputs", "evaluated_inputs"))
    if selection not in _SELECTIONS or result["native_index"] != source["native_index"]:
        raise ValueError(field + " native selection or original physical row index disagrees")
    if evaluated is not None and (evaluated["native_index"] != source["native_index"] or
            evaluated["object_identity"] is not None and evaluated["object_identity"] != source["object_identity"]):
        raise ValueError(field + " evaluated row changed the observed physical identity")
    if result["weight_call_ordinal"] is not None and not initialized:
        raise ValueError(field + " native call has no initialized caller scope")
    if selection == "same_sample_source":
        if result["weight_call_ordinal"] is not None or evaluated != source:
            raise ValueError(field + " reused source row must remain unchanged and uncalled")
    elif selection == "native_row_2872300":
        if (not initialized or not result["scope_prefix_ready"]
                or result["weight_call_ordinal"] is None or evaluated is None):
            raise ValueError(field + " native weight lacks the actual scope prefix or call observation")
    elif evaluated is not None and (evaluated["ready"] or evaluated["weight_q64"] is not None):
        raise ValueError(field + " unavailable native call cannot release a weight or ready PC")
    return result


def normalize_person_conditional_scope_weights_12004(value):
    if value is None:
        return None
    raw = _dict(value, FIELD_NAME, _FIELDS)
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {"schema": SCHEMA, "build_version": CK3_12004.game_version,
              "executable_sha256": CK3_12004.executable_sha256}
    for key in ("character_id", "scope_payload_u32", "occurrence_count"):
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32, unsigned=True)
    for key in ("selected_object_identity", "selected_array_identity", "reason"):
        result[key] = _string(raw[key], FIELD_NAME + "." + key, optional=True)
    result["selected_family"] = _string(raw["selected_family"], FIELD_NAME + ".selected_family")
    for key in ("classifier_result_i32", "selected_count_i32"):
        result[key] = _number(raw[key], FIELD_NAME + "." + key, 32)
    result["scope_kind_u16"] = _number(raw["scope_kind_u16"], FIELD_NAME + ".scope_kind_u16", 16, unsigned=True)
    for key in ("classifier_ready", "scope_initialized", "ready"):
        result[key] = _boolean(raw[key], FIELD_NAME + "." + key)
    if result["scope_initialized"] and (result["scope_kind_u16"] != 4 or result["scope_payload_u32"] is None):
        raise ValueError(FIELD_NAME + " initialized scope lacks its actual kind4 and observed payload")
    if result["scope_kind_u16"] not in (None, 4):
        raise ValueError(FIELD_NAME + " scope kind differs from the native caller")
    if not isinstance(raw["rows"], list):
        raise ValueError(FIELD_NAME + " rows must retain physical order")
    rows = [_scope_row(row, f"{FIELD_NAME}.rows[{i}]", result["scope_initialized"])
            for i, row in enumerate(raw["rows"])]
    result["rows"] = rows
    if [row["native_index"] for row in rows] != list(range(len(rows))):
        raise ValueError(FIELD_NAME + " physical source occurrence order changed")
    calls = [row["weight_call_ordinal"] for row in rows if row["weight_call_ordinal"] is not None]
    if calls != list(range(len(calls))):
        raise ValueError(FIELD_NAME + " native call attempt order changed")
    _state(result["ready"], result["reason"], FIELD_NAME)
    classifier = result["classifier_result_i32"]
    if result["classifier_ready"]:
        if classifier not in (0, 1, 2):
            raise ValueError(FIELD_NAME + " known classifier lacks its actual result")
    elif classifier is not None:
        raise ValueError(FIELD_NAME + " unread classifier cannot supply a result")
    count = result["selected_count_i32"]
    if count is not None and (count < 0 and rows or count >= 0 and len(rows) > count):
        raise ValueError(FIELD_NAME + " selected rows disagree with its raw count")
    if result["ready"]:
        family = result["selected_family"]
        if family in ("not_demanded", "classifier_other_empty"):
            if rows or result["scope_initialized"] or family == "classifier_other_empty" and classifier != 1:
                raise ValueError(FIELD_NAME + " known empty family demanded a scope or rows")
        elif family in ("bb0_bbc", "b80_b8c"):
            expected = "bb0_bbc" if classifier == 0 else "b80_b8c"
            if (not result["classifier_ready"] or classifier not in (0, 2) or family != expected
                    or count is None or count < 0 or len(rows) != count
                    or any(row["evaluated_inputs"] is None or not row["evaluated_inputs"]["ready"] for row in rows)):
                raise ValueError(FIELD_NAME + " complete family lacks independently observed row inputs")
        else:
            raise ValueError(FIELD_NAME + " unknown selected family")
        if result["occurrence_count"] != sum(row["evaluated_inputs"]["weight_q64"] != 0 for row in rows):
            raise ValueError(FIELD_NAME + " downstream append occurrence count differs")
    elif result["occurrence_count"] is not None:
        raise ValueError(FIELD_NAME + " partial family cannot supply a full occurrence count")
    return result


def _joined(section):
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_conditional_scope_weights_12004(section.get(FIELD_NAME))
    opinion = normalize_person_conditional_opinion_12004(section.get("following_2921a90_opinion"))
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if leaf is None or opinion is None or leaf["character_id"] != character or opinion["character_id"] != character:
        raise ValueError("Required same-Character input unavailable: " + FIELD_NAME)
    if (leaf["selected_object_identity"] != opinion["source_inputs"]["selected_object_identity"]
            or any(leaf[key] != opinion[key] for key in ("classifier_ready", "classifier_result_i32",
                       "selected_family", "selected_array_identity", "selected_count_i32"))
            or [row["source_inputs"] for row in leaf["rows"]] != opinion["rows"]):
        raise ValueError("Required same-selection Native45 source inputs unavailable: " + FIELD_NAME)
    return leaf, opinion


def _request_row(row):
    return tuple(replace(request, source_name=FIELD_NAME + "_12004")
                 for request in _request(row["evaluated_inputs"]))


def emit_scope_2921a90_requests_from_current_source_inputs_12004(section):
    leaf, _ = _joined(section)
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + leaf["reason"])
    return tuple(request for row in leaf["rows"] for request in _request_row(row))


def emit_scope_2921a90_row_requests_from_current_source_inputs_12004(section, native_index):
    leaf, _ = _joined(section)
    index = _integer(native_index, FIELD_NAME + ".native_index", 32, unsigned=True)
    row = next((row for row in leaf["rows"] if row["native_index"] == index), None)
    evaluated = row["evaluated_inputs"] if row is not None else None
    if evaluated is None or not evaluated["ready"]:
        reason = (evaluated["reason"] if evaluated is not None else leaf["reason"] or
                  (row["source_inputs"]["reason"] if row is not None else None) or FIELD_NAME + " row unobserved")
        raise ValueError("Required native input unavailable: " + reason)
    return _request_row(row)


def emit_complete_scope_2921a90_requests_from_current_source_inputs_12004(section):
    from .battle_person_following_2921a90_12004 import (
        normalize_person_following_2921a90_12004,
        emit_following_2921a90_direct_requests_from_current_source_inputs_12004,
    )
    leaf, opinion = _joined(section)
    direct = normalize_person_following_2921a90_12004(section.get("following_2921a90"))
    if direct is None or any(direct[key] != opinion["source_inputs"][key] for key in (
            "character_identity", "selected_model_identity", "selected_object_identity")):
        raise ValueError("Required same-receiver direct family unavailable: " + FIELD_NAME)
    first = emit_following_2921a90_direct_requests_from_current_source_inputs_12004(section)
    following = emit_scope_2921a90_requests_from_current_source_inputs_12004(section)
    return first + tuple(replace(request, source_ordinal=len(direct["direct_rows"]) + request.source_ordinal)
                         for request in following)
