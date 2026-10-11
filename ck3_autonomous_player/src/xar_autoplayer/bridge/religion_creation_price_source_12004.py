"""Decode the independent source price carried by one existing cost response.

Copied source inputs and partial diagnostics retain their native widths and
order. This projection never replaces the separately observed native quote.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re

from .version_identity import CK3_12004, require_exact_native_build


WIRE_KEY = "religion_creation_price_source_12004"
FACTS_KEY = "religion_creation_price_source_facts_12004"
SCHEMA = "religion-creation-price-source-12004-v1"
_U64 = (1 << 64) - 1
_I64_LOW, _I64_HIGH = -(1 << 63), (1 << 63) - 1
_I32_LOW, _I32_HIGH = -(1 << 31), (1 << 31) - 1
_POINTER = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]{0,15})\Z")
_TOP = {
    "schema", "game_version", "executable_sha256", "capture_scope", "source_kind",
    "actual_original_consumed_values", "source_ready", "reason", "frame",
    "editing_owned_current_rite", "before", "after", "copied_spans_still_current",
    "input_mappings_still_current", "copied_read_count", "copied_bytes",
    "source_model", "final_piety_price_raw_q64",
}
_FRAME = {
    "snapshot_revision", "query_sequence", "capture_epoch", "date_raw",
    "played_character_id", "owning_thread_id", "stamp_date_raw", "stamp_paused",
    "mailbox_before_accepted", "mailbox_after_accepted",
}
_INPUTS = {
    "complete", "reason", "window_identity", "price_payload_identity",
    "window_source_rite_carrier", "character_storage_identity",
    "character_fallback_identity", "rite_storage_identity", "rite_fallback_identity",
    "first_actor", "current_rite", "second_actor",
}
_RESOLVED = {"ready", "reason", "requested_full_id", "selected_identity",
             "resolved_full_id", "used_fallback"}
_MODEL = {
    "source_ready", "actual_original_consumed_values", "reason", "stopped_stage",
    "price_payload", "current_rite", "actor", "actor_full_id_raw_u32",
    "rite_full_id_carrier_u32", "unchanged_snapshot_revision",
    "source_qualified_actor_fallback", "create_base", "actor_property_223",
    "entered_base_with223_raw_q64", "rite_term", "actor_property_224",
    "final_piety_price_raw_q64",
}
_BASE = {
    "complete", "reason", "composition_source_ready", "reached_numeric_sources_ready",
    "first_data", "first_count_raw", "second_data", "second_count_raw",
    "stopped_collection", "stopped_ordinal", "base_price_raw_q64", "ordered_contributions",
}
_ROW = {"collection", "ordinal", "full_element_pointer", "native_eax_raw",
        "scaled_raw", "contribution_applied", "child"}
_CHILD = {"source_ready", "reason", "selected_expression_identity", "native_eax_raw",
          "dynamic_input_copy_reason", "dynamic_callback_attempted"}
_ACTOR_TERM = {
    "source_ready", "reason", "requested_key_raw_u32", "collection_still_current",
    "collection_identity", "collection_source_ready", "collection_reason",
    "term_source_ready", "term_reason", "scaled_term_raw_q64",
}
_RITE_TERM = {
    "source_ready", "reason", "route", "native_term_raw_q64", "provider",
    "definition_table", "definition", "definition_enabled_byte_7c",
    "literal_flag_byte_7b", "expression", "expression_receiver", "expression_vtable",
    "expression_virtual_30", "dynamic_context_operands_copied",
}


def _require(condition: bool, field: str) -> None:
    if not condition:
        raise ValueError(field)


def _shape(value: object, keys: set[str], field: str) -> dict[str, object]:
    _require(isinstance(value, dict) and set(value) == keys, field + ":keyset")
    return value


def _integer(value: object, low: int, high: int, field: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    _require(type(value) is int and low <= value <= high, field + ":integer_width")


def _boolean(value: object, field: str, *, nullable: bool = False) -> None:
    _require((nullable and value is None) or type(value) is bool, field + ":boolean")


def _text(value: object, field: str, *, nullable: bool = False) -> None:
    _require((nullable and value is None) or isinstance(value, str), field + ":text")


def _pointer(value: object, field: str, *, nullable: bool = False) -> int | None:
    if nullable and value is None:
        return None
    _require(isinstance(value, str) and _POINTER.fullmatch(value) is not None,
             field + ":pointer_width")
    return int(value, 16)


def _signed_bits(value: int) -> int:
    bits = value & _U64
    return bits if bits <= _I64_HIGH else bits - (1 << 64)


def _resolved(value: object, field: str) -> dict[str, object]:
    out = _shape(value, _RESOLVED, field)
    _boolean(out["ready"], field + ".ready")
    _text(out["reason"], field + ".reason")
    for key in ("requested_full_id", "resolved_full_id"):
        _integer(out[key], 0, 0xFFFFFFFF, field + "." + key, nullable=True)
    selected = _pointer(out["selected_identity"], field + ".selected_identity", nullable=True)
    _boolean(out["used_fallback"], field + ".used_fallback", nullable=True)
    if out["ready"]:
        _require(selected is not None and selected != 0 and out["resolved_full_id"] is not None
                 and out["used_fallback"] is not None, field + ":ready_without_identity")
        if out["used_fallback"] is False:
            _require(out["requested_full_id"] is not None
                     and out["requested_full_id"] == out["resolved_full_id"],
                     field + ":full_generation_mismatch")
    return out


def _inputs(value: object, field: str) -> dict[str, object]:
    out = _shape(value, _INPUTS, field)
    _boolean(out["complete"], field + ".complete")
    _text(out["reason"], field + ".reason")
    window = _pointer(out["window_identity"], field + ".window_identity")
    payload = _pointer(out["price_payload_identity"], field + ".price_payload_identity", nullable=True)
    _integer(out["window_source_rite_carrier"], 0, 0xFFFFFFFF,
             field + ".window_source_rite_carrier", nullable=True)
    pointers = {}
    for key in ("character_storage_identity", "character_fallback_identity",
                "rite_storage_identity", "rite_fallback_identity"):
        pointers[key] = _pointer(out[key], field + "." + key, nullable=True)
    first = _resolved(out["first_actor"], field + ".first_actor")
    rite = _resolved(out["current_rite"], field + ".current_rite")
    second = _resolved(out["second_actor"], field + ".second_actor")
    if payload is not None:
        _require(window != 0 and window <= _U64 - 0xB28 and payload == window + 0xB28,
                 field + ":price_payload_relation")
    for name, resolved, storage_key, fallback_key in (
        ("first_actor", first, "character_storage_identity", "character_fallback_identity"),
        ("current_rite", rite, "rite_storage_identity", "rite_fallback_identity"),
        ("second_actor", second, "character_storage_identity", "character_fallback_identity"),
    ):
        if resolved["ready"]:
            _require(pointers[storage_key] is not None, field + "." + name + ":storage_unread")
            if pointers[storage_key] == 0:
                _require(resolved["requested_full_id"] is None and resolved["used_fallback"] is True,
                         field + "." + name + ":undemanded_request_filled")
            if resolved["used_fallback"]:
                _require(pointers[fallback_key] is not None and pointers[fallback_key] != 0
                         and out[fallback_key] == resolved["selected_identity"],
                         field + "." + name + ":literal_fallback_binding")
    if rite["ready"] and rite["used_fallback"] is False:
        _require(out["rite_fallback_identity"] is None, field + ":unreached_rite_fallback_filled")
    if out["complete"]:
        _require(window != 0 and payload is not None and out["window_source_rite_carrier"] is not None
                 and pointers["character_storage_identity"] is not None
                 and pointers["character_fallback_identity"] is not None
                 and pointers["rite_storage_identity"] is not None
                 and first["ready"] and rite["ready"] and second["ready"],
                 field + ":complete_without_reached_inputs")
    return out


def _child(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    out = _shape(value, _CHILD, field)
    _boolean(out["source_ready"], field + ".source_ready")
    _text(out["reason"], field + ".reason")
    _pointer(out["selected_expression_identity"], field + ".selected_expression_identity", nullable=True)
    _integer(out["native_eax_raw"], _I32_LOW, _I32_HIGH, field + ".native_eax_raw", nullable=True)
    _text(out["dynamic_input_copy_reason"], field + ".dynamic_input_copy_reason")
    _boolean(out["dynamic_callback_attempted"], field + ".dynamic_callback_attempted")
    _require(out["dynamic_callback_attempted"] is False, field + ":unavailable_callback_attempted")
    if out["source_ready"]:
        _require(out["native_eax_raw"] is not None, field + ":ready_without_eax")
    return out


def _base(value: object, field: str) -> dict[str, object]:
    out = _shape(value, _BASE, field)
    for key in ("complete", "composition_source_ready", "reached_numeric_sources_ready"):
        _boolean(out[key], field + "." + key)
    _text(out["reason"], field + ".reason")
    for key in ("first_data", "second_data"):
        _pointer(out[key], field + "." + key, nullable=True)
    for key in ("first_count_raw", "second_count_raw"):
        _integer(out[key], _I32_LOW, _I32_HIGH, field + "." + key, nullable=True)
    _integer(out["stopped_collection"], 0, 1, field + ".stopped_collection", nullable=True)
    _integer(out["stopped_ordinal"], 0, 4096, field + ".stopped_ordinal", nullable=True)
    _integer(out["base_price_raw_q64"], _I64_LOW, _I64_HIGH,
             field + ".base_price_raw_q64", nullable=True)
    rows = out["ordered_contributions"]
    _require(isinstance(rows, list) and len(rows) <= 4096, field + ":occurrence_budget")
    ordinals = [0, 0]
    collection_before = 0
    total = 0
    for index, value_row in enumerate(rows):
        row_field = f"{field}.ordered_contributions[{index}]"
        row = _shape(value_row, _ROW, row_field)
        _integer(row["collection"], 0, 1, row_field + ".collection")
        _integer(row["ordinal"], 0, 4095, row_field + ".ordinal")
        collection = row["collection"]
        _require(collection >= collection_before and row["ordinal"] == ordinals[collection],
                 row_field + ":ordered_occurrence")
        collection_before = collection
        ordinals[collection] += 1
        count = out["first_count_raw" if collection == 0 else "second_count_raw"]
        _require(count is not None and count >= 0 and row["ordinal"] < count,
                 row_field + ":occurrence_outside_copied_count")
        _pointer(row["full_element_pointer"], row_field + ".full_element_pointer")
        _integer(row["native_eax_raw"], _I32_LOW, _I32_HIGH,
                 row_field + ".native_eax_raw", nullable=True)
        _integer(row["scaled_raw"], _I64_LOW, _I64_HIGH, row_field + ".scaled_raw", nullable=True)
        _boolean(row["contribution_applied"], row_field + ".contribution_applied")
        child = _child(row["child"], row_field + ".child")
        if row["contribution_applied"]:
            _require(child is not None and child["source_ready"]
                     and row["native_eax_raw"] is not None
                     and row["native_eax_raw"] == child["native_eax_raw"]
                     and row["scaled_raw"] == row["native_eax_raw"] * 100000,
                     row_field + ":unqualified_contribution")
            total += row["scaled_raw"]
        else:
            _require(row["native_eax_raw"] is None and row["scaled_raw"] is None
                     and index == len(rows) - 1, row_field + ":unreached_contribution")
    if out["complete"]:
        _require(out["composition_source_ready"] and out["reached_numeric_sources_ready"]
                 and out["first_count_raw"] is not None and out["first_count_raw"] >= 0
                 and out["second_count_raw"] is not None and out["second_count_raw"] >= 0
                 and ordinals == [out["first_count_raw"], out["second_count_raw"]]
                 and all(row["contribution_applied"] for row in rows)
                 and out["stopped_collection"] is None and out["stopped_ordinal"] is None
                 and out["base_price_raw_q64"] == _signed_bits(total),
                 field + ":complete_prefix_mismatch")
    else:
        _require(out["base_price_raw_q64"] is None, field + ":partial_price_filled")
    return out


def _actor_term(value: object, key: int, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    out = _shape(value, _ACTOR_TERM, field)
    for name in ("source_ready", "collection_still_current"):
        _boolean(out[name], field + "." + name)
    for name in ("collection_source_ready", "term_source_ready"):
        _boolean(out[name], field + "." + name, nullable=True)
    _text(out["reason"], field + ".reason")
    for name in ("collection_reason", "term_reason"):
        _text(out[name], field + "." + name, nullable=True)
    _integer(out["requested_key_raw_u32"], 0, 0xFFFFFFFF, field + ".requested_key_raw_u32")
    _require(out["requested_key_raw_u32"] == key, field + ":wrong_property_occurrence")
    collection = _pointer(out["collection_identity"], field + ".collection_identity", nullable=True)
    _integer(out["scaled_term_raw_q64"], _I64_LOW, _I64_HIGH,
             field + ".scaled_term_raw_q64", nullable=True)
    if out["source_ready"]:
        _require(out["collection_source_ready"] is True and out["term_source_ready"] is True
                 and out["collection_still_current"] is True and collection is not None
                 and collection != 0 and out["scaled_term_raw_q64"] is not None,
                 field + ":ready_without_source_term")
    else:
        _require(out["scaled_term_raw_q64"] is None, field + ":unqualified_scaled_term")
    return out


def _rite_term(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    out = _shape(value, _RITE_TERM, field)
    _boolean(out["source_ready"], field + ".source_ready")
    _boolean(out["dynamic_context_operands_copied"], field + ".dynamic_context_operands_copied")
    _text(out["reason"], field + ".reason")
    _integer(out["route"], 0, 4, field + ".route")
    _integer(out["native_term_raw_q64"], _I64_LOW, _I64_HIGH,
             field + ".native_term_raw_q64", nullable=True)
    for name in ("definition_enabled_byte_7c", "literal_flag_byte_7b"):
        _integer(out[name], 0, 255, field + "." + name, nullable=True)
    pointers = {}
    for name in ("provider", "definition_table", "definition", "expression",
                 "expression_receiver", "expression_vtable", "expression_virtual_30"):
        pointers[name] = _pointer(out[name], field + "." + name)
    if out["source_ready"]:
        _require(out["route"] in (1, 2, 3) and out["native_term_raw_q64"] is not None
                 and pointers["provider"] != 0 and pointers["definition"] != 0
                 and out["dynamic_context_operands_copied"] is False,
                 field + ":ready_without_closed_route")
        if out["route"] == 1:
            _require(out["definition_enabled_byte_7c"] == 0 and out["native_term_raw_q64"] == 0,
                     field + ":disabled_zero_mismatch")
        else:
            _require(out["definition_enabled_byte_7c"] not in (None, 0)
                     and pointers["expression"] == 0 and out["literal_flag_byte_7b"] is not None,
                     field + ":literal_route_mismatch")
            if out["route"] == 2:
                _require(out["literal_flag_byte_7b"] == 0 and out["native_term_raw_q64"] == 0,
                         field + ":flag_zero_mismatch")
            else:
                _require(out["literal_flag_byte_7b"] != 0, field + ":literal_flag_missing")
    else:
        _require(out["native_term_raw_q64"] is None, field + ":unqualified_rite_value")
    return out


def _model(value: object, before: dict[str, object], revision: int) -> dict[str, object] | None:
    if value is None:
        return None
    field = "source_model"
    out = _shape(value, _MODEL, field)
    _boolean(out["source_ready"], field + ".source_ready")
    _boolean(out["actual_original_consumed_values"], field + ".actual_original_consumed_values")
    _require(out["actual_original_consumed_values"] is False, field + ":original_values_claimed")
    _boolean(out["source_qualified_actor_fallback"], field + ".source_qualified_actor_fallback")
    _text(out["reason"], field + ".reason")
    _integer(out["stopped_stage"], 0, 4, field + ".stopped_stage")
    for name in ("price_payload", "current_rite", "actor"):
        _pointer(out[name], field + "." + name)
    for name in ("actor_full_id_raw_u32", "rite_full_id_carrier_u32"):
        _integer(out[name], 0, 0xFFFFFFFF, field + "." + name)
    _integer(out["unchanged_snapshot_revision"], 0, _U64, field + ".unchanged_snapshot_revision")
    _require(before["complete"] and out["price_payload"] == before["price_payload_identity"]
             and out["current_rite"] == before["current_rite"]["selected_identity"]
             and out["actor"] == before["second_actor"]["selected_identity"]
             and out["actor_full_id_raw_u32"] == before["second_actor"]["resolved_full_id"]
             and out["rite_full_id_carrier_u32"] == before["current_rite"]["resolved_full_id"]
             and out["source_qualified_actor_fallback"] == before["second_actor"]["used_fallback"]
             and out["unchanged_snapshot_revision"] == revision, field + ":input_binding")
    base = _base(out["create_base"], field + ".create_base")
    term223 = _actor_term(out["actor_property_223"], 0x223, field + ".actor_property_223")
    term224 = _actor_term(out["actor_property_224"], 0x224, field + ".actor_property_224")
    rite = _rite_term(out["rite_term"], field + ".rite_term")
    _integer(out["entered_base_with223_raw_q64"], _I64_LOW, _I64_HIGH,
             field + ".entered_base_with223_raw_q64", nullable=True)
    _integer(out["final_piety_price_raw_q64"], _I64_LOW, _I64_HIGH,
             field + ".final_piety_price_raw_q64", nullable=True)
    stage = out["stopped_stage"]
    _require(out["source_ready"] is (stage == 4), field + ":stage_readiness")
    if stage == 0:
        _require(not base["complete"] and term223 is None and rite is None and term224 is None
                 and out["entered_base_with223_raw_q64"] is None, field + ":late_child_filled")
    else:
        _require(base["complete"] and term223 is not None, field + ":base_source_missing")
        if stage == 1:
            _require(not term223["source_ready"] and rite is None and term224 is None
                     and out["entered_base_with223_raw_q64"] is None, field + ":late_child_filled")
        else:
            _require(term223["source_ready"] and rite is not None
                     and out["entered_base_with223_raw_q64"] == _signed_bits(
                         base["base_price_raw_q64"] + term223["scaled_term_raw_q64"]),
                     field + ":entered_source_sum")
            if stage == 2:
                _require(not rite["source_ready"] and term224 is None, field + ":late_child_filled")
            else:
                _require(rite["source_ready"] and term224 is not None, field + ":rite_source_missing")
                if stage == 3:
                    _require(not term224["source_ready"], field + ":stopped_after_ready_term")
                else:
                    _require(term224["source_ready"] and out["final_piety_price_raw_q64"] is not None
                             and out["final_piety_price_raw_q64"] >= 0,
                             field + ":complete_price_missing")
    if stage != 4:
        _require(out["final_piety_price_raw_q64"] is None, field + ":partial_final_filled")
    return out


def decode_religion_creation_price_source_12004(
    packet: object, *, snapshot: Mapping[str, object], resource_costs: Mapping[str, object],
    snapshot_revision: object, query_date_raw: object,
) -> dict[str, object]:
    """Qualify only this optional companion against its existing response."""
    unavailable: dict[str, object] = {
        "status": "absent" if packet is None else "invalid", "source_ready": False,
        "final_piety_price_raw_q64": None, "actual_original_consumed_values": False,
        "reason": "source_packet_absent" if packet is None else "source_packet_invalid",
    }
    if packet is None:
        return unavailable
    try:
        value = _shape(packet, _TOP, "packet")
        _require(value["schema"] == SCHEMA, "packet:schema")
        _require(require_exact_native_build(value["game_version"], value["executable_sha256"]) == CK3_12004,
                 "packet:exact_build")
        _require(value["capture_scope"] in ("actual_application_query", "owned_memory_fixture"),
                 "packet:capture_scope")
        _require(value["source_kind"] == "readonly_source_projection"
                 and value["actual_original_consumed_values"] is False, "packet:source_kind")
        _boolean(value["source_ready"], "packet.source_ready")
        _text(value["reason"], "packet.reason")
        _boolean(value["editing_owned_current_rite"], "packet.editing_owned_current_rite", nullable=True)
        for name in ("copied_spans_still_current", "input_mappings_still_current"):
            _boolean(value[name], "packet." + name, nullable=True)
        _integer(value["copied_read_count"], 0, 16384, "packet.copied_read_count")
        _integer(value["copied_bytes"], 0, 262144, "packet.copied_bytes")
        _require(value["copied_bytes"] >= value["copied_read_count"], "packet:copy_counter_relation")
        _integer(value["final_piety_price_raw_q64"], _I64_LOW, _I64_HIGH,
                 "packet.final_piety_price_raw_q64", nullable=True)
        frame = _shape(value["frame"], _FRAME, "frame")
        for name in ("snapshot_revision", "query_sequence", "capture_epoch"):
            _integer(frame[name], 0, _U64, "frame." + name)
        for name in ("played_character_id", "owning_thread_id"):
            _integer(frame[name], 0, 0xFFFFFFFF, "frame." + name)
        for name in ("date_raw", "stamp_date_raw"):
            _integer(frame[name], _I32_LOW, _I32_HIGH, "frame." + name)
        for name in ("stamp_paused", "mailbox_before_accepted"):
            _boolean(frame[name], "frame." + name)
        _boolean(frame["mailbox_after_accepted"], "frame.mailbox_after_accepted", nullable=True)
        before = _inputs(value["before"], "before")
        after = None if value["after"] is None else _inputs(value["after"], "after")
        if not before["complete"]:
            _require(after is None and value["source_model"] is None
                     and value["input_mappings_still_current"] is None
                     and value["copied_spans_still_current"] is None, "packet:unreached_bookends")
        if value["input_mappings_still_current"] is True:
            _require(after is not None and before == after, "packet:mapping_bookend_mismatch")
        model = _model(value["source_model"], before, frame["snapshot_revision"])
        if model is not None:
            _require(value["editing_owned_current_rite"] is False, "packet:model_without_false_selector")
        if value["source_ready"]:
            _require(frame["mailbox_before_accepted"] is True
                     and frame["mailbox_after_accepted"] is True and frame["stamp_paused"] is True
                     and frame["owning_thread_id"] != 0 and frame["date_raw"] == frame["stamp_date_raw"]
                     and before["complete"] and after is not None and after["complete"]
                     and value["input_mappings_still_current"] is True
                     and value["copied_spans_still_current"] is True
                     and model is not None and model["source_ready"]
                     and value["final_piety_price_raw_q64"] == model["final_piety_price_raw_q64"]
                     and value["reason"] == "same_query_create_source_price_ready",
                     "packet:ready_without_finished_source")
        else:
            _require(value["final_piety_price_raw_q64"] is None, "packet:unqualified_final_filled")

        # All comparisons use copied existing-response carriers. No identity,
        # counter or missing source input is constructed from them.
        actor = snapshot.get("played_character")
        _require(isinstance(actor, Mapping), "binding:caller_player_missing")
        _integer(actor.get("character_id"), 0, 0xFFFFFFFF, "binding.caller_player_full_id")
        _integer(snapshot.get("native_revision"), 1, _U64, "binding.caller_native_revision")
        _integer(snapshot.get("date_raw"), _I32_LOW, _I32_HIGH, "binding.caller_date_raw")
        _integer(snapshot_revision, 1, _U64, "binding.response_snapshot_revision")
        _integer(query_date_raw, _I32_LOW, _I32_HIGH, "binding.response_date_raw")
        _require(frame["snapshot_revision"] == snapshot_revision == snapshot["native_revision"],
                 "binding:snapshot_revision_mismatch")
        _require(frame["date_raw"] == query_date_raw == snapshot["date_raw"] == resource_costs.get("date_raw"),
                 "binding:date_raw_mismatch")
        _require(frame["capture_epoch"] == resource_costs.get("capture_epoch")
                 and frame["played_character_id"] == actor["character_id"] == resource_costs.get("played_character_id"),
                 "binding:owner_epoch_or_full_id_mismatch")
        quote = resource_costs.get("base_resource_cost_quote")
        quote = quote.get("draft_quote") if isinstance(quote, Mapping) else None
        if value["editing_owned_current_rite"] is not None:
            _require(isinstance(quote, Mapping) and quote.get("available") is True
                     and type(quote.get("editing_owned_current_rite")) is bool
                     and value["editing_owned_current_rite"] == quote["editing_owned_current_rite"],
                     "binding:existing_selector_mismatch")
        # currentRite is the first actor+B4 lookup; the old quote source_rite_id
        # and windowC8 remain separate roles and are never substituted for it.
        ready = value["source_ready"] and value["capture_scope"] == "actual_application_query"
        return {
            "status": "available" if ready else "unavailable", "source_ready": ready,
            "final_piety_price_raw_q64": value["final_piety_price_raw_q64"] if ready else None,
            "actual_original_consumed_values": False, "source_kind": value["source_kind"],
            "capture_scope": value["capture_scope"],
            "source_model_value_ready": model is not None and model["source_ready"] is True,
            "reason": value["reason"] if value["capture_scope"] == "actual_application_query"
                else "source_scope_not_actual_application_query",
            "source_packet": deepcopy(value),
        }
    except ValueError as error:
        return {**unavailable, "reason": str(error)}
