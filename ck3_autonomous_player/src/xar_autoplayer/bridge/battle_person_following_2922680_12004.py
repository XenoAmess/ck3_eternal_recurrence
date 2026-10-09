"""Actual4 2922680 observations and independently ready primary operands.

The installed Model is receiver provenance, not a fresh preparation baseline.
Mapped membership observations retain their unclosed mapper reason; primary
requests never manufacture that contribution or merge a native context.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
)
from .battle_person_carrier_direct_12004 import _values_q64
from .version_identity import CK3_12004, require_exact_native_build
from ..simulation.battle_person_after_gated_tail_12003 import _trunc
from ..simulation.battle_trait_numeric_inputs_12003 import native_wrap32_12003

FIELD_NAME = "following_2922680"
SCHEMA = "xar.ck3.person-following-2922680-12004-v1"
MAPPED_GAP = "actual42127e0_input_unobserved"
_PRIMARY_KINDS = {"item_primary", "nested_primary"}
_KINDS = _PRIMARY_KINDS | {"item_mapped", "nested_mapped"}
_PC_FIELDS = {"ready", "reason", "admitted", "identity", "count_i32",
              "properties", "weight_q100000"}


def _record(value, field, *, pointers=(), unsigned=(), signed=(), booleans=(),
            nullable_booleans=(), strings=(), children=None, extra=()):
    children = children or {}
    fields = {"ready", "reason", *pointers, *booleans, *nullable_booleans,
              *strings, *children, *extra,
              *(name for name, _ in unsigned), *(name for name, _ in signed)}
    raw = _dict(value, field, fields)
    result = {"ready": _boolean(raw["ready"], field + ".ready"),
              "reason": _string(raw["reason"], field + ".reason", optional=True)}
    for key in pointers:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key, bits in unsigned:
        result[key] = _number(raw[key], field + "." + key, bits, unsigned=True)
    for key, bits in signed:
        result[key] = _number(raw[key], field + "." + key, bits)
    for key in booleans:
        result[key] = _boolean(raw[key], field + "." + key)
    for key in nullable_booleans:
        result[key] = _boolean(raw[key], field + "." + key, optional=True)
    for key in strings:
        result[key] = _string(raw[key], field + "." + key)
    for key, parser in children.items():
        result[key] = parser(raw[key], field + "." + key)
    if result["ready"] and result["reason"] is not None:
        raise ValueError(field + " ready observation retains an unavailable reason")
    return raw, result


def _rows(value, field, parser):
    if not isinstance(value, list):
        raise ValueError(field + " must retain physical row order")
    rows = [parser(row, f"{field}[{index}]") for index, row in enumerate(value)]
    if [row["native_index"] for row in rows] != list(range(len(rows))):
        raise ValueError(field + " changed physical occurrence order")
    return rows


def _resolution(value, field):
    _, row = _record(value, field,
        pointers=("registry_identity", "registry_slots_identity", "candidate_identity", "selected_identity"),
        unsigned=(("requested_full_id_u32", 32), ("registry_count_u32", 32), ("candidate_full_id_u32", 32)),
        strings=("selection",))
    if row["selection"] not in {"unavailable", "fallback", "mapped"}:
        raise ValueError(field + " unknown native resolution selection")
    return row


def _pc(value, field):
    raw, row = _record(value, field, pointers=("identity",),
        signed=(("count_i32", 32),), nullable_booleans=("admitted",),
        extra=("properties", "weight_q100000"))
    row["weight_q100000"] = _integer(raw["weight_q100000"], field + ".weight_q100000", 64)
    if row["weight_q100000"] != 100000:
        raise ValueError(field + " weight differs from the actual unit append")
    block = raw["properties"]
    if block is not None:
        block = _dict(block, field + ".properties", {"keys_u16", "values_q64"})
        block = {"keys_u16": _numbers(block["keys_u16"], field + ".properties.keys_u16", 16, unsigned=True),
                 "values_q64": _values_q64(block["values_q64"], field + ".properties.values_q64")}
    row["properties"] = block
    if row["ready"] and row["admitted"] is True:
        count = row["count_i32"]
        if (row["identity"] is None or count is None or count < 0 or block is None
                or block["keys_u16"] is None or block["values_q64"] is None
                or len(block["keys_u16"]) != count or len(block["values_q64"]) != count):
            raise ValueError(field + " ready append lacks its actual PC operands")
    return row


def _membership_row(value, field):
    raw, row = _record(value, field, pointers=("key_identity",),
        nullable_booleans=("admitted",), extra=("native_index",))
    row["native_index"] = _integer(raw["native_index"], field + ".native_index", 32, unsigned=True)
    return row


def _membership(value, field):
    raw, row = _record(value, field,
        pointers=("header_identity", "array_identity", "membership_array_identity"),
        signed=(("count_i32", 32), ("membership_count_i32", 32)),
        children={"rows": lambda rows, name: _rows(rows, name, _membership_row)},
        extra=("membership_identities",))
    identities = raw["membership_identities"]
    if identities is not None:
        if not isinstance(identities, list):
            raise ValueError(field + ".membership_identities must be a list or null")
        identities = [_string(identity, f"{field}.membership_identities[{index}]")
                      for index, identity in enumerate(identities)]
    row["membership_identities"] = identities
    return row


def _probe(value, field):
    raw = _dict(value, field, {"native_index", "slot_identity", "control_u8", "key_u32"})
    return {"native_index": _integer(raw["native_index"], field + ".native_index", 32, unsigned=True),
            "slot_identity": _string(raw["slot_identity"], field + ".slot_identity", optional=True),
            "control_u8": _number(raw["control_u8"], field + ".control_u8", 8, unsigned=True),
            "key_u32": _number(raw["key_u32"], field + ".key_u32", 32, unsigned=True)}


def _getter(value, field):
    _, row = _record(value, field,
        pointers=("table_identity", "end_slot_identity", "found_slot_identity", "result_identity"),
        unsigned=(("input_magic_u32", 32), ("input_full_id_u32", 32), ("hash_u32", 32),
                  ("overflow_u8", 8), ("selected_value_u32", 32),
                  ("result_magic_u32", 32), ("result_full_id_u32", 32)),
        signed=(("mask_i32", 32), ("start_index_i64", 64)), nullable_booleans=("admitted",),
        children={"probes": lambda rows, name: _rows(rows, name, _probe),
                  "value_resolution": _resolution})
    return row


def _nested(value, field):
    raw, row = _record(value, field, pointers=("object_identity",),
        unsigned=(("selector_id_u32", 32),), nullable_booleans=("matched",),
        children={"primary_pc": _pc, "membership": _membership}, extra=("native_index",))
    row["native_index"] = _integer(raw["native_index"], field + ".native_index", 32, unsigned=True)
    return row


def _item(value, field):
    raw, row = _record(value, field, pointers=("object_identity", "nested_array_identity"),
        unsigned=(("enabled_3f0_u8", 8),), signed=(("nested_count_i32", 32),),
        children={"primary_pc": _pc, "membership": _membership,
                  "nested": lambda rows, name: _rows(rows, name, _nested)}, extra=("native_index",))
    row["native_index"] = _integer(raw["native_index"], field + ".native_index", 32, unsigned=True)
    return row


def _source(value, field):
    raw, row = _record(value, field,
        pointers=("match_definition_identity", "item_container_identity", "item_array_identity"),
        unsigned=(("list_full_id_u32", 32), ("match_id_u32", 32)), signed=(("item_count_i32", 32),),
        booleans=("direct_ready",), nullable_booleans=("list_id_demanded",),
        children={"resolution": _resolution, "getter": _getter,
                  "items": lambda rows, name: _rows(rows, name, _item)}, extra=("native_index",))
    row["native_index"] = _integer(raw["native_index"], field + ".native_index", 32, unsigned=True)
    if row["list_full_id_u32"] != row["resolution"]["requested_full_id_u32"]:
        raise ValueError(field + " physical full ID differs from the actual lookup input")
    return row


def _outer(value, field):
    raw, row = _record(value, field,
        pointers=("current_game_data_identity", "source_list_array_identity"),
        unsigned=(("list_full_id_u32", 32),),
        signed=(("cached_date_c7ce_i16", 16), ("raw_date_c7c8_i32", 32),
                ("derived_year_i32", 32), ("current_date_i32", 32), ("source_list_count_i32", 32)),
        booleans=("known_no_contribution", "primary_ready"),
        nullable_booleans=("list_id_demanded", "date_admitted"),
        strings=("date_branch",),
        children={"resolution": _resolution, "sources": lambda rows, name: _rows(rows, name, _source)},
        extra=("native_index",))
    row["native_index"] = _integer(raw["native_index"], field + ".native_index", 32, unsigned=True)
    if row["list_full_id_u32"] != row["resolution"]["requested_full_id_u32"]:
        raise ValueError(field + " physical full ID differs from the actual lookup input")
    if row["date_branch"] not in {"unavailable", "expired", "not_expired", "no_current_date_required"}:
        raise ValueError(field + " unknown source date branch")
    cached, date, year = (row[key] for key in
                          ("cached_date_c7ce_i16", "raw_date_c7c8_i32", "derived_year_i32"))
    if year is not None:
        expected = (cached if cached is not None and cached >= 0 else
                    _trunc(native_wrap32_12003(date - 43800000), 8760)
                    if cached is not None and date is not None else None)
        if year != expected:
            raise ValueError(field + " decoded year differs from the reused native calendar primitive")
    return row


def _append(value, field):
    extra = {"kind", "outer_index", "source_index", "item_index", "nested_index", "descriptor_index"}
    raw = _dict(value, field, _PC_FIELDS | extra)
    row = _pc({key: raw[key] for key in _PC_FIELDS}, field)
    row["kind"] = _string(raw["kind"], field + ".kind")
    if row["kind"] not in _KINDS:
        raise ValueError(field + " unknown native append kind")
    for key in ("outer_index", "source_index", "item_index"):
        row[key] = _integer(raw[key], field + "." + key, 32, unsigned=True)
    for key in ("nested_index", "descriptor_index"):
        row[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    if row["admitted"] is not True:
        raise ValueError(field + " flat occurrence is not an actual admitted source call")
    return row


def normalize_person_following_2922680_12004(value: object) -> dict | None:
    """Preserve the whole optional source leaf, including all partial rows."""
    if value is None:
        return None
    raw, result = _record(value, FIELD_NAME,
        pointers=("character_identity", "selected_model_identity", "destination_pc_identity",
                  "character_context_1c0_identity", "character_gate_1d0_identity",
                  "list_header_identity", "list_array_identity", "source_operand_identity"),
        unsigned=(("character_id", 32),), signed=(("list_count_i32", 32),),
        booleans=("source_operand_ready", "primary_ready"), strings=("header_selection",),
        children={"rite_resolution": _resolution, "context_resolution": _resolution,
                  "operand_rite_resolution": _resolution,
                  "rows": lambda rows, name: _rows(rows, name, _outer)},
        extra=("schema", "build_version", "executable_sha256", "source_operand_reason", "append_occurrences"))
    if (raw["schema"] != SCHEMA or require_exact_native_build(
            raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result.update(schema=SCHEMA, build_version=CK3_12004.game_version,
                  executable_sha256=CK3_12004.executable_sha256)
    result["source_operand_reason"] = _string(
        raw["source_operand_reason"], FIELD_NAME + ".source_operand_reason", optional=True)
    if not isinstance(raw["append_occurrences"], list):
        raise ValueError(FIELD_NAME + " append occurrences must retain native order")
    result["append_occurrences"] = [_append(row, f"{FIELD_NAME}.append_occurrences[{index}]")
                                     for index, row in enumerate(raw["append_occurrences"])]
    count, rows = result["list_count_i32"], result["rows"]
    if count is not None and (count < 0 and rows or count >= 0 and len(rows) > count):
        raise ValueError(FIELD_NAME + " observed rows disagree with its raw signed count")
    if result["primary_ready"] or result["ready"]:
        if count is None or count < 0 or len(rows) != count:
            raise ValueError(FIELD_NAME + " complete family lacks its physical outer rows")
    if result["primary_ready"]:
        if any(not row["primary_ready"] for row in rows):
            raise ValueError(FIELD_NAME + " complete primary family retains an unavailable primary row")
        if any(not row["ready"] for row in result["append_occurrences"] if row["kind"] in _PRIMARY_KINDS):
            raise ValueError(FIELD_NAME + " complete primary family retains an unavailable primary PC")
    if result["ready"] and (not result["primary_ready"] or any(not row["ready"] for row in rows)
            or any(not row["ready"] for row in result["append_occurrences"])):
        raise ValueError(FIELD_NAME + " complete helper retains an unavailable source occurrence")
    return result


def _joined_leaf(section):
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    leaf = normalize_person_following_2922680_12004(section.get(FIELD_NAME))
    if leaf is None:
        raise ValueError("Required native input unavailable: " + FIELD_NAME)
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if leaf["character_id"] != character:
        raise ValueError(FIELD_NAME + " full CharacterID join unavailable or mismatched")
    return leaf


def _request(row, ordinal):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    if not row["ready"]:
        raise ValueError("Required native input unavailable: " + (row["reason"] or FIELD_NAME))
    block = row["properties"]
    return NativeWeightedContributionRequest12003(
        source_ordinal=ordinal, source_name=FIELD_NAME + "_12004:" + row["kind"],
        first_row_index=0, row_count=1, definition_identity=row["identity"],
        base_property_block={"keys_count": row["count_i32"],
                             "keys_u16": block["keys_u16"], "values_q64": block["values_q64"]},
        weight_q64=row["weight_q100000"],
    )


def emit_following_2922680_requests_from_current_source_inputs_12004(section):
    """Release the full helper only when every demanded family is available."""
    leaf = _joined_leaf(section)
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIELD_NAME))
    return tuple(_request(row, index) for index, row in enumerate(leaf["append_occurrences"]))


def emit_following_2922680_primary_requests_from_current_source_inputs_12004(section):
    """Release the complete primary family independently of mapper partials."""
    leaf = _joined_leaf(section)
    if not leaf["primary_ready"]:
        raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIELD_NAME + " primary"))
    return tuple(_request(row, index) for index, row in enumerate(leaf["append_occurrences"])
                 if row["kind"] in _PRIMARY_KINDS)


def emit_following_2922680_primary_occurrence_requests_from_current_source_inputs_12004(section, native_index):
    """Release one ready primary PC at its original flat append ordinal."""
    leaf = _joined_leaf(section)
    index = _integer(native_index, FIELD_NAME + ".append_occurrences.native_index", 32, unsigned=True)
    rows = leaf["append_occurrences"]
    if index >= len(rows) or rows[index]["kind"] not in _PRIMARY_KINDS:
        raise ValueError("Required native input unavailable: " + FIELD_NAME + " primary occurrence")
    return (_request(rows[index], index),)
