"""Decode the private actual4 selected-perk source packet from one query.

These copied inputs describe child288B1B0. Earlier288AE00 SIL conditions and
the original native can_select observations remain separate. Pointer values
are identities only; this module performs no reads, queries or native calls.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping

WIRE_KEY = "lifestyle_perk_predicate_source_12004"
FACTS_KEY = "lifestyle_perk_predicate_source_facts_12004"
SCHEMA = "lifestyle_perk_predicate_source_12004_v1"
EXECUTABLE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
TARGETS = frozenset({
    "cutting_corners_perk", "professional_workforce_perk", "centralization_perk",
    "tax_man_perk", "thoughtful_perk", "serve_the_crown_perk",
})
_ERASED_SOURCE_REASONS = frozenset({
    "stock_perk_predicate_source_frame_changed", "stock_perk_predicate_source_changed",
})
_MAILBOX_REJECTION = "formal_mailbox_after_guard_rejected"

_FRAME_FIELDS = {
    "executable_sha256": "string", "module_base": "uint64",
    "snapshot_identity": "string", "frame_identity": "nullable_uint64",
    "query_sequence": "nullable_uint64", "mailbox_before_accepted": "nullable_bool",
    "mailbox_after_accepted": "nullable_bool", "module_image_size": "nullable_uint32",
    "module_time_date_stamp": "nullable_uint32", "public_revision": "uint64",
    "native_revision": "uint64", "proof_epoch": "uint64", "date_raw": "int32",
    "played_character_id": "uint32", "caller_domain": "string",
    "caller_snapshot_confirmed": "bool",
}
_INPUT_FIELDS = {
    "command_identity": "uint64", "registry_identity": "nullable_uint64",
    "requested_full_character_id_u32": "nullable_uint32",
    "registry_capacity_u32": "nullable_uint32", "indexed_character_identity": "nullable_uint64",
    "indexed_character_full_id_u32": "nullable_uint32", "used_fallback": "nullable_bool",
    "selected_character_identity": "nullable_uint64", "selected_character_magic_u32": "nullable_uint32",
    "selected_character_full_id_u32": "nullable_uint32", "selected_character_field_1d0_u64": "nullable_uint64",
    "selected_perk_identity": "nullable_uint64", "selected_perk_magic_u32": "nullable_uint32",
    "prefix_admitted": "nullable_bool", "unavailable_reason": "string",
}
_TAIL_FIELDS = {"value": "nullable_bool", "unavailable_reason": "string"}
_TRACE_FIELDS = {
    "selected_perk_identity": "uint64", "compiled_trigger_receiver_identity": "nullable_uint64",
    "context_root_word": "nullable_uint16", "context_full_id_payload": "nullable_uint64",
    "evaluation_flag_raw_u8": "nullable_uint8", "trigger_vtable_raw": "nullable_uint64",
    "root_kind_getter_slot58_raw": "nullable_uint64", "root_mask_getter_slot60_raw": "nullable_uint64",
    "final_evaluator_slotc8_raw": "nullable_uint64", "source_projected_returned_raw_u8": "nullable_uint8",
    "value": "nullable_bool", "context_projection_available": "bool", "copied_frame_ready": "bool",
    "input_leaf_ready": "bool", "child_source_value_ready": "bool", "native_callback_executed": "bool",
    "actual_trigger_evaluation_observed": "bool", "unavailable_reason": "string",
}
_PACKET_FIELDS = {
    "schema": "string", "read_only": "bool", "target_key": "string", "read_frame": "object",
    "current_thread_tls_array_identity": "nullable_uint64", "inputs": "object",
    "tail": "nullable_object", "truth_trace": "nullable_object", "value": "nullable_bool",
    "unavailable_reason": "string", "native_can_select_before": "nullable_bool",
    "native_can_select_after": "nullable_bool", "repeated_source_match": "bool",
}


class _InvalidSource(ValueError):
    pass


def _require(condition: bool, issue: str) -> None:
    if not condition:
        raise _InvalidSource(issue)


def _typed(value: object, kind: str) -> bool:
    if kind.startswith("nullable_"):
        if value is None:
            return True
        kind = kind.removeprefix("nullable_")
    if kind == "string":
        return isinstance(value, str)
    if kind == "bool":
        return type(value) is bool
    if kind == "object":
        return isinstance(value, Mapping)
    if kind.startswith("uint"):
        return type(value) is int and 0 <= value < (1 << int(kind[4:]))
    if kind == "int32":
        return type(value) is int and -(1 << 31) <= value < (1 << 31)
    return False


def _object(value: object, fields: Mapping[str, str], path: str) -> Mapping[str, object]:
    _require(isinstance(value, Mapping), f"{path}:object_required")
    _require(set(value) == set(fields), f"{path}:fields_mismatch")
    for name, kind in fields.items():
        _require(_typed(value[name], kind), f"{path}.{name}:{kind}_required")
    return value


class _PrefixStop(Exception):
    def __init__(self, value: bool | None, reason: str) -> None:
        self.value = value
        self.reason = reason


def _validate_prefix(inputs: Mapping[str, object], frame: Mapping[str, object]) -> None:
    seen = {"command_identity", "prefix_admitted", "unavailable_reason"}

    def read(name: str, reason: str) -> object:
        seen.add(name)
        value = inputs[name]
        if value is None:
            raise _PrefixStop(None, reason)
        return value

    outcome: bool | None = True
    reason = ""
    try:
        registry = read("registry_identity", "lifestyle_perk_character_registry_unavailable")
        fallback = registry == 0
        if not fallback:
            _require(inputs["command_identity"] != 0 or inputs["requested_full_character_id_u32"] is None,
                     "inputs:requested_id_after_null_command")
            requested = read("requested_full_character_id_u32", "lifestyle_perk_requested_character_full_id_unavailable")
            _require(requested == frame["played_character_id"], "inputs:requested_full_id_frame_mismatch")
            capacity = read("registry_capacity_u32", "lifestyle_perk_character_registry_capacity_unavailable")
            index = requested & 0xFFFFFF
            fallback = index >= capacity
            if not fallback:
                indexed = read("indexed_character_identity", "lifestyle_perk_character_registry_row_unavailable")
                fallback = indexed == 0
                if not fallback:
                    indexed_id = read("indexed_character_full_id_u32", "lifestyle_perk_indexed_character_full_id_unavailable")
                    fallback = indexed_id != requested
        seen.add("used_fallback")
        _require(inputs["used_fallback"] is fallback, "inputs:full_generation_fallback_mismatch")
        if fallback:
            selected = read("selected_character_identity", "lifestyle_perk_character_fallback_unavailable")
        else:
            seen.add("selected_character_identity")
            selected = inputs["selected_character_identity"]
            _require(selected == inputs["indexed_character_identity"], "inputs:indexed_selection_mismatch")
        _require(selected != 0 or inputs["selected_character_magic_u32"] is None,
                 "inputs:character_magic_after_null_selection")
        magic = read("selected_character_magic_u32", "lifestyle_perk_character_magic_unavailable")
        if magic != 0x43686172:
            raise _PrefixStop(False, "")
        full_id = read("selected_character_full_id_u32", "lifestyle_perk_selected_character_full_id_unavailable")
        if full_id == 0xFFFFFFFF:
            raise _PrefixStop(False, "")
        field_1d0 = read("selected_character_field_1d0_u64", "lifestyle_perk_character_field_1d0_unavailable")
        if field_1d0 != 0:
            raise _PrefixStop(False, "")
        _require(inputs["command_identity"] != 0 or inputs["selected_perk_identity"] is None,
                 "inputs:perk_after_null_command")
        perk = read("selected_perk_identity", "lifestyle_perk_selected_definition_magic_unavailable")
        _require(perk != 0 or inputs["selected_perk_magic_u32"] is None, "inputs:perk_magic_after_null_definition")
        perk_magic = read("selected_perk_magic_u32", "lifestyle_perk_selected_definition_magic_unavailable")
        outcome = perk_magic == 0x4744624F
    except _PrefixStop as stop:
        outcome, reason = stop.value, stop.reason
    _require(inputs["prefix_admitted"] is outcome, "inputs:prefix_result_mismatch")
    _require(inputs["unavailable_reason"] == reason, "inputs:prefix_reason_mismatch")
    _require(all(inputs[name] is None for name in set(inputs) - seen), "inputs:unread_field_filled")


def _validate_trace(trace: Mapping[str, object], packet: Mapping[str, object]) -> None:
    inputs = packet["inputs"]
    _require(trace["selected_perk_identity"] == inputs["selected_perk_identity"], "truth_trace:perk_identity_mismatch")
    _require(trace["context_projection_available"] is True, "truth_trace:undemanded_context")
    _require(trace["native_callback_executed"] is False and trace["actual_trigger_evaluation_observed"] is False,
             "truth_trace:source_projection_promoted_to_native_evaluation")
    receiver = trace["compiled_trigger_receiver_identity"]
    perk = trace["selected_perk_identity"]
    if receiver is not None:
        _require(perk <= (1 << 64) - 1 - 0x80 and receiver == perk + 0x80, "truth_trace:receiver_binding_mismatch")
    erased = packet["unavailable_reason"] in _ERASED_SOURCE_REASONS
    virtual_fields = ("evaluation_flag_raw_u8", "trigger_vtable_raw", "root_kind_getter_slot58_raw",
                      "root_mask_getter_slot60_raw", "final_evaluator_slotc8_raw", "source_projected_returned_raw_u8", "value")
    context_matches = trace["context_root_word"] == 4 and trace["context_full_id_payload"] == inputs["selected_character_full_id_u32"]
    if not context_matches or receiver is None:
        _require(receiver is None and trace["copied_frame_ready"] is False,
                 "truth_trace:receiver_after_unavailable_context")
        _require(all(trace[name] is None for name in virtual_fields), "truth_trace:undemanded_virtual_field_filled")
    if trace["copied_frame_ready"] is False and not erased:
        _require(all(trace[name] is None for name in virtual_fields), "truth_trace:unread_frame_fields_filled")
    returned = trace["source_projected_returned_raw_u8"]
    if returned is None:
        _require(trace["value"] is None, "truth_trace:value_without_returned_byte")
        _require(trace["child_source_value_ready"] is False or erased, "truth_trace:ready_without_returned_byte")
        _require(bool(trace["unavailable_reason"]) or erased, "truth_trace:unknown_reason_missing")
    else:
        _require(trace["value"] is (returned != 0), "truth_trace:returned_byte_bool_mismatch")
        _require(all(trace[name] is True for name in ("copied_frame_ready", "child_source_value_ready")),
                 "truth_trace:returned_byte_not_qualified")
        _require(context_matches and receiver is not None and trace["evaluation_flag_raw_u8"] is not None,
                 "truth_trace:returned_byte_binding_unavailable")
        # A qualified false can stop before later virtual operands are demanded.
        # A true needs the qualified returned byte and the complete reached path;
        # raw slot addresses alone never satisfy either returned-value check.
        if returned != 0:
            _require(trace["input_leaf_ready"] is True and all(trace[name] not in (None, 0) for name in
                     ("trigger_vtable_raw", "root_kind_getter_slot58_raw", "root_mask_getter_slot60_raw",
                      "final_evaluator_slotc8_raw")), "truth_trace:raw_slots_not_outputs")


def decode_lifestyle_perk_predicate_source_12004(
    packet: object, *, expected_snapshot_identity: str | None = None,
    expected_native_revision: int | None = None, expected_date_raw: int | None = None,
    expected_played_character_id: int | None = None, expected_target_key: str | None = None,
) -> dict[str, object]:
    """Validate optional copied facts without changing original can_select.

    Binding arguments are existing caller values used only for comparison.
    Missing numeric frame/TLS metadata is retained; no field is filled from a
    snapshot string, query counter, proof epoch or a later observation.
    """
    if packet is None:
        return {"status": "absent"}
    try:
        packet = _object(packet, _PACKET_FIELDS, "packet")
        _require(packet["schema"] == SCHEMA and packet["read_only"] is True, "packet:source_schema_invalid")
        _require(packet["target_key"] in TARGETS, "packet:target_not_admitted")
        frame = _object(packet["read_frame"], _FRAME_FIELDS, "read_frame")
        _require(frame["executable_sha256"] == EXECUTABLE_SHA256 and frame["caller_domain"] == "stock_perk_legality_12004",
                 "read_frame:actual4_admission_invalid")
        comparisons = ((expected_snapshot_identity, "snapshot_identity", "string"),
                       (expected_native_revision, "native_revision", "uint64"),
                       (expected_date_raw, "date_raw", "int32"),
                       (expected_played_character_id, "played_character_id", "uint32"))
        for expected, name, kind in comparisons:
            if expected is not None:
                _require(_typed(expected, kind) and frame[name] == expected, f"read_frame:{name}_binding_mismatch")
        if expected_target_key is not None:
            _require(isinstance(expected_target_key, str) and packet["target_key"] == expected_target_key,
                     "packet:target_binding_mismatch")
        inputs = _object(packet["inputs"], _INPUT_FIELDS, "inputs")
        _validate_prefix(inputs, frame)
        tail = packet["tail"]
        trace = packet["truth_trace"]
        if tail is not None:
            tail = _object(tail, _TAIL_FIELDS, "tail")
        if trace is not None:
            trace = _object(trace, _TRACE_FIELDS, "truth_trace")
        reason = packet["unavailable_reason"]
        erased = reason in _ERASED_SOURCE_REASONS
        after_rejected = reason == _MAILBOX_REJECTION
        invalidated = erased or after_rejected
        if invalidated:
            _require(packet["value"] is None and frame["caller_snapshot_confirmed"] is False,
                     "packet:source_invalidation_promoted")
            if after_rejected:
                _require(frame["mailbox_after_accepted"] is False, "read_frame:mailbox_rejection_flag_missing")
            elif tail is not None:
                _require(tail["value"] is None, "tail:source_drift_value_retained")
        prefix = inputs["prefix_admitted"]
        if prefix is not True:
            _require(tail is None and trace is None, "packet:tail_after_unadmitted_prefix")
            if not invalidated:
                _require(packet["value"] is prefix, "packet:prefix_value_mismatch")
                _require(reason == inputs["unavailable_reason"], "packet:prefix_reason_mismatch")
        else:
            _require(tail is not None, "packet:admitted_prefix_tail_missing")
            if not invalidated:
                _require(packet["value"] is tail["value"] and reason == tail["unavailable_reason"],
                         "packet:tail_result_mismatch")
            if tail["value"] is None and not erased:
                _require(bool(tail["unavailable_reason"]), "tail:unknown_reason_missing")
            if trace is not None:
                _validate_trace(trace, packet)
                _require(tail["value"] is trace["value"] or erased, "tail:truth_trace_result_mismatch")
            if tail["value"] is True:
                _require(trace is not None and trace["value"] is True, "tail:true_without_qualified_truth_trace")
        if packet["value"] is None:
            _require(bool(reason), "packet:unknown_reason_missing")
        if packet["value"] is True:
            _require(frame["caller_snapshot_confirmed"] is True and frame["module_base"] != 0
                     and (frame["frame_identity"] not in (None, 0) or bool(frame["snapshot_identity"])),
                     "packet:true_without_copied_frame_binding")
        return {**deepcopy(dict(packet)), "status": "decoded", "whole_parent_legality_decoded": False,
                "source_value_status": "unknown" if packet["value"] is None else
                ("known_true" if packet["value"] else "known_false")}
    except _InvalidSource as error:
        return {"status": "invalid", "value": None, "unavailable_reason": str(error),
                "whole_parent_legality_decoded": False}
