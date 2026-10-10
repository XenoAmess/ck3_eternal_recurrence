"""Strict copied frontier facts from the same private lifestyle response.

Raw targets, four returned source planes and native can_select are independent.
This decoder performs no query, memory read, clock allocation or native call.
"""

from copy import deepcopy
from typing import Mapping

from .lifestyle_perk_predicate_inputs_12004 import EXECUTABLE_SHA256, TARGETS

WIRE_KEY = "lifestyle_perk_trigger_frontier_12004"
FACTS_KEY = "lifestyle_perk_trigger_frontier_facts_12004"
SCHEMA = "lifestyle-perk-trigger-frontier-12004-v1"
_U64_MAX = (1 << 64) - 1
_OUTPUT_FIELDS = ("returned_raw_u8", "returned_raw_u16", "returned_qword0", "returned_qword1")
_FRAME = {
    "executable_sha256": "string", "module_base": "u64", "frame_identity": "nullable_u64",
    "snapshot_identity": "string", "native_revision": "u64", "query_sequence": "nullable_u64",
    "proof_epoch": "u64", "date_raw": "nullable_i32", "caller_domain": "string",
    "caller_snapshot_confirmed": "bool",
}
_TARGET = {"slot_identity": "nullable_u64", "target_identity": "nullable_u64",
           "target_rva": "nullable_u64", "copied": "bool", "unavailable_reason": "string"}
_INPUT = {
    "read_frame": "object", "module_image_size": "nullable_u32", "module_time_date_stamp": "nullable_u32",
    "public_revision": "u64", "mailbox_before_accepted": "nullable_bool", "mailbox_after_accepted": "nullable_bool",
    "target_key": "string", "capture_scope": "string", "command_identity": "u64", "selected_perk_identity": "u64",
    "requested_full_character_id": "u32", "selected_character_identity": "nullable_u64",
    "selected_character_full_id": "nullable_u32", "receiver_identity": "nullable_u64",
    "vtable_identity": "nullable_u64", "vtable_rva": "nullable_u64", "slots": "object",
    "source_context_root_word": "nullable_u16", "source_context_full_id_payload": "nullable_u64",
    "context_is_source_projection": "bool", "descriptor_provider": "nullable_object",
    "caller_before_after_confirmed": "bool", "repeated_raw_match": "bool",
    "native_before": "nullable_bool", "native_after": "nullable_bool", "unavailable_reason": "string",
}
_DESCRIPTOR = {
    "read_frame": "object", "caller_root_kind_raw_u16": "nullable_u16", "table_identity": "nullable_u64",
    "initialization_guard_raw_i32": "nullable_i32", "table_data_identity": "nullable_u64",
    "capacity_raw_i32": "nullable_i32", "count_raw_i32": "nullable_i32", "selected_source_fallback": "nullable_bool",
    "selected_descriptor_identity": "nullable_u64", "descriptor_validator_pointer10": "nullable_u64",
    "descriptor_selection_inputs_copied": "bool", "descriptor_validator_pointer_copied": "bool",
    "initializer_semantics_source_closed": "bool", "native_provider_return_observed": "bool", "unavailable_reason": "string",
}
_LANE = {
    "lane": "string", "call_rva": "u64", "return_rva": "u64", "target": "object",
    "raw_target_ready": "bool", "source_value_ready": "bool", "returned_raw_u8": "nullable_u8",
    "returned_raw_u16": "nullable_u16", "returned_qword0": "nullable_u64", "returned_qword1": "nullable_u64",
    "result_source": "string", "closed_target_proof": "nullable_object", "natural_witness": "nullable_object",
    "unavailable_reason": "string",
}
_PROOF = {"target_rva": "u64", "exact_source_sha256": "string", "producer_key": "string",
          "complete_pure_readonly_body": "bool"}
_EVENT = {"clock_identity": "u64", "sequence": "u64", "thread_id": "nullable_u32"}
_WITNESS = {
    "read_frame": "object", "query_cursor": "object", "call_event": "object", "return_event": "object",
    "call_rva": "u64", "return_rva": "u64", "selected_perk_identity": "u64", "receiver_identity": "u64",
    "target_identity": "u64", "original_rcx": "u64", "original_rdx": "u64",
    "original_root_word": "nullable_u16", "original_full_id_payload": "nullable_u64",
    "returned_raw_u8": "nullable_u8", "returned_raw_u16": "nullable_u16", "returned_qword0": "nullable_u64",
    "returned_qword1": "nullable_u64", "original_matching_call_count": "u32",
    "original_call_observed": "bool", "original_return_observed": "bool",
}
_LANES = {
    "descriptor_al": (0x372E0AE, 0x372E0B0, ("returned_raw_u8",), None),
    "root_kind_ax": (0x372B4D3, 0x372B4D6, ("returned_raw_u16",), "slot58"),
    "root_mask_qwords": (0x372B4EE, 0x372B4F1, ("returned_qword0", "returned_qword1"), "slot60"),
    "final_c8_al": (0x372E34D, 0x372E353, ("returned_raw_u8",), "slotc8"),
}
_PACKET = {"schema": "string", "read_only": "bool", "copied_input_binding_ready": "bool",
           "inputs": "object", "lanes": "object"}


class _InvalidFrontier(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise _InvalidFrontier(reason)


def _typed(value: object, kind: str) -> bool:
    if kind.startswith("nullable_"):
        if value is None:
            return True
        kind = kind.removeprefix("nullable_")
    if kind == "bool":
        return type(value) is bool
    if kind == "string":
        return isinstance(value, str)
    if kind == "object":
        return isinstance(value, Mapping)
    if kind.startswith("u"):
        return type(value) is int and 0 <= value < (1 << int(kind[1:]))
    if kind == "i32":
        return type(value) is int and -(1 << 31) <= value < (1 << 31)
    return False


def _object(value: object, fields: Mapping[str, str], path: str) -> Mapping[str, object]:
    _require(isinstance(value, Mapping), f"{path}:object_required")
    _require(set(value) == set(fields), f"{path}:fields_mismatch")
    for key, kind in fields.items():
        _require(_typed(value[key], kind), f"{path}.{key}:{kind}_required")
    return value


def _frame(value: object, path: str) -> Mapping[str, object]:
    frame = _object(value, _FRAME, path)
    _require(frame["executable_sha256"] == EXECUTABLE_SHA256
             and frame["caller_domain"] == "stock_perk_legality_12004", f"{path}:actual4_admission_invalid")
    # Generic zero denotes missing numeric metadata in this frozen serializer.
    _require(frame["frame_identity"] != 0 and frame["query_sequence"] != 0,
             f"{path}:missing_numeric_carrier_must_be_null")
    return frame


def _bounded(inputs: Mapping[str, object], address: object, width: int) -> bool:
    size = inputs["module_image_size"]
    base = inputs["read_frame"]["module_base"]
    return (size is not None and size > 0 and address is not None
            and address >= base and address - base < size
            and width <= size - (address - base))


def _input_bound(inputs: Mapping[str, object]) -> bool:
    frame = inputs["read_frame"]
    perk = inputs["selected_perk_identity"]
    return (frame["module_base"] != 0 and frame["caller_snapshot_confirmed"] is True
            and (frame["frame_identity"] is not None or bool(frame["snapshot_identity"]))
            and frame["query_sequence"] is not None and bool(inputs["target_key"])
            and inputs["command_identity"] != 0 and 0 < perk <= _U64_MAX - 0x80
            and inputs["receiver_identity"] == perk + 0x80
            and _bounded(inputs, inputs["vtable_identity"], 0xD0))


def _target(value: object, inputs: Mapping[str, object], path: str) -> Mapping[str, object]:
    target = _object(value, _TARGET, path)
    _require(not target["copied"] or target["target_identity"] is not None, f"{path}:copied_target_missing")
    if target["target_rva"] is not None:
        _require(_bounded(inputs, target["target_identity"], 1)
                 and target["target_rva"] == target["target_identity"] - inputs["read_frame"]["module_base"],
                 f"{path}:bounded_target_rva_mismatch")
    return target


def _descriptor_target(inputs: Mapping[str, object]) -> dict[str, object]:
    descriptor = inputs["descriptor_provider"]
    empty = {"slot_identity": None, "target_identity": None, "target_rva": None,
             "copied": False, "unavailable_reason": "lifestyle_descriptor_source_kind_association_unavailable"}
    if descriptor is None:
        return empty
    selected = descriptor["selected_descriptor_identity"]
    if (descriptor["read_frame"] != inputs["read_frame"] or inputs["source_context_root_word"] is None
            or descriptor["caller_root_kind_raw_u16"] != inputs["source_context_root_word"]
            or selected is None or selected > _U64_MAX - 0x10):
        return {**empty, "unavailable_reason": "lifestyle_descriptor_same_query_selection_unavailable"}
    target = descriptor["descriptor_validator_pointer10"]
    return {"slot_identity": selected + 0x10, "target_identity": target,
            "target_rva": target - inputs["read_frame"]["module_base"] if _bounded(inputs, target, 1) else None,
            "copied": descriptor["descriptor_validator_pointer_copied"],
            "unavailable_reason": descriptor["unavailable_reason"]}


def _ordered_events(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return (left["clock_identity"] != 0 and left["clock_identity"] == right["clock_identity"]
            and left["thread_id"] not in (None, 0) and left["thread_id"] == right["thread_id"]
            and 0 < left["sequence"] < right["sequence"])


def _lane_facts(name: str, value: object, inputs: Mapping[str, object], binding_ready: bool) -> dict[str, object]:
    unavailable = {"status": "invalid", "raw_target_ready": False, "source_value_ready": False,
                   **{field: None for field in _OUTPUT_FIELDS}}
    try:
        lane = _object(value, _LANE, f"lanes.{name}")
        call, ret, demanded, slot = _LANES[name]
        _require(lane["lane"] == name and lane["call_rva"] == call and lane["return_rva"] == ret,
                 "lane:literal_call_return_mismatch")
        target = _target(lane["target"], inputs, "lane.target")
        expected = (_target(inputs["slots"][slot], inputs, "lane.input_target")
                    if slot else _descriptor_target(inputs))
        if slot and expected["slot_identity"] is not None:
            offset = {"slot58": 0x58, "slot60": 0x60, "slotc8": 0xC8}[slot]
            vtable = inputs["vtable_identity"]
            _require(vtable not in (None, 0) and vtable <= _U64_MAX - offset
                     and expected["slot_identity"] == vtable + offset, "lane:slot_storage_mismatch")
        # Finalize preserves the previously copied descriptor target while its
        # parent frame confirmation is cleared. It removes all readiness credit.
        if binding_ready:
            _require(target == expected, "lane:current_input_target_mismatch")
        elif slot:
            _require(target == expected, "lane:copied_slot_target_mismatch")
        if lane["raw_target_ready"]:
            _require(binding_ready and _input_bound(inputs) and target["copied"]
                     and _bounded(inputs, target["target_identity"], 1)
                     and target["target_rva"] is not None, "lane:raw_target_binding_unavailable")
        proof = lane["closed_target_proof"]
        if proof is not None:
            proof = _object(proof, _PROOF, "lane.closed_target_proof")
        witness = lane["natural_witness"]
        if witness is not None:
            witness = _object(witness, _WITNESS, "lane.natural_witness")
            _frame(witness["read_frame"], "lane.natural_witness.read_frame")
            for event in ("query_cursor", "call_event", "return_event"):
                _object(witness[event], _EVENT, f"lane.natural_witness.{event}")
        _require(lane["result_source"] in {"unavailable", "closed_pure_target_source", "natural_original_once"},
                 "lane:result_source_not_admitted")
        if not lane["source_value_ready"]:
            _require(all(lane[field] is None for field in _OUTPUT_FIELDS)
                     and lane["result_source"] == "unavailable", "lane:unqualified_returned_output")
            return {"status": "decoded", "raw_target_ready": lane["raw_target_ready"],
                    "source_value_ready": False, **{field: None for field in _OUTPUT_FIELDS},
                    "unavailable_reason": lane["unavailable_reason"]}
        _require(lane["raw_target_ready"] and binding_ready, "lane:output_without_current_raw_binding")
        _require(all(lane[field] is not None for field in demanded)
                 and all(lane[field] is None for field in set(_OUTPUT_FIELDS) - set(demanded)),
                 "lane:returned_width_mismatch")
        if lane["result_source"] == "closed_pure_target_source":
            _require(proof is not None and proof["complete_pure_readonly_body"] is True
                     and proof["target_rva"] == target["target_rva"] and bool(proof["producer_key"])
                     and len(proof["exact_source_sha256"]) == 64
                     and all(c in "0123456789abcdef" for c in proof["exact_source_sha256"]),
                     "lane:exact_pure_target_proof_unavailable")
        else:
            _require(lane["result_source"] == "natural_original_once" and witness is not None,
                     "lane:original_once_witness_unavailable")
            _require(witness["read_frame"] == inputs["read_frame"]
                     and witness["selected_perk_identity"] == inputs["selected_perk_identity"]
                     and witness["receiver_identity"] == inputs["receiver_identity"]
                     and witness["target_identity"] == target["target_identity"]
                     and witness["call_rva"] == call and witness["return_rva"] == ret
                     and witness["original_matching_call_count"] == 1
                     and witness["original_call_observed"] is True and witness["original_return_observed"] is True
                     and _ordered_events(witness["query_cursor"], witness["call_event"])
                     and _ordered_events(witness["call_event"], witness["return_event"])
                     and all(witness[field] == lane[field] for field in _OUTPUT_FIELDS),
                     "lane:original_once_frame_target_event_or_return_mismatch")
            if slot:
                _require(witness["original_rcx"] == inputs["receiver_identity"], "lane:original_receiver_mismatch")
            if name == "root_mask_qwords":
                _require(witness["original_rdx"] != 0, "lane:original_mask_buffer_unavailable")
            if name == "descriptor_al":
                provider = inputs["descriptor_provider"]
                _require(provider is not None and witness["original_rcx"] != 0
                         and witness["original_rdx"] == provider["selected_descriptor_identity"]
                         and witness["original_root_word"] == inputs["source_context_root_word"]
                         and witness["original_full_id_payload"] == inputs["source_context_full_id_payload"],
                         "lane:original_descriptor_scope_mismatch")
            if name == "final_c8_al":
                _require(witness["original_rdx"] != 0 and witness["original_root_word"] == 4
                         and witness["original_full_id_payload"] == inputs["selected_character_full_id"],
                         "lane:original_c8_scope_unavailable")
        return {"status": "decoded", "raw_target_ready": True, "source_value_ready": True,
                **{field: lane[field] for field in _OUTPUT_FIELDS}, "result_source": lane["result_source"],
                "unavailable_reason": lane["unavailable_reason"]}
    except _InvalidFrontier as error:
        return {**unavailable, "unavailable_reason": str(error)}


def decode_lifestyle_perk_trigger_frontier_12004(
    packet: object, *, expected_snapshot_identity: str | None = None,
    expected_native_revision: int | None = None, expected_date_raw: int | None = None,
    expected_played_character_id: int | None = None, expected_target_key: str | None = None,
) -> dict[str, object]:
    """Compare existing caller bindings and qualify each source lane separately.

`lane_facts` contains validated output credit. The copied packet remains raw
diagnostic evidence, including rejected proof/witness facts. No lane qualifies
another lane or the complete native parent legality predicate.
"""
    if packet is None:
        return {"status": "absent"}
    try:
        packet = _object(packet, _PACKET, "packet")
        _require(packet["schema"] == SCHEMA and packet["read_only"] is True, "packet:frontier_schema_invalid")
        inputs = _object(packet["inputs"], _INPUT, "inputs")
        frame = _frame(inputs["read_frame"], "inputs.read_frame")
        _require(inputs["target_key"] in TARGETS, "inputs:target_not_admitted")
        _require(inputs["capture_scope"] in {"unavailable", "owned_memory_fixture", "actual_application_query"},
                 "inputs:capture_scope_not_admitted")
        for expected, copied, kind, name in (
            (expected_snapshot_identity, frame["snapshot_identity"], "string", "snapshot_identity"),
            (expected_native_revision, frame["native_revision"], "u64", "native_revision"),
            (expected_date_raw, frame["date_raw"], "i32", "date_raw"),
            (expected_played_character_id, inputs["requested_full_character_id"], "u32", "requested_full_character_id"),
            (expected_target_key, inputs["target_key"], "string", "target_key"),
        ):
            if expected is not None:
                _require(_typed(expected, kind) and copied == expected, f"inputs:{name}_binding_mismatch")
        slots = _object(inputs["slots"], {name: "object" for name in ("slot58", "slot60", "slotc8")}, "inputs.slots")
        # Slot semantics are validated in their own lanes. A failed or
        # mismatching slot/proof does not invalidate another output plane.
        if inputs["vtable_rva"] is not None:
            _require(_bounded(inputs, inputs["vtable_identity"], 1)
                     and inputs["vtable_rva"] == inputs["vtable_identity"] - frame["module_base"],
                     "inputs:bounded_vtable_rva_mismatch")
        provider = inputs["descriptor_provider"]
        if provider is not None:
            provider = _object(provider, _DESCRIPTOR, "inputs.descriptor_provider")
            _frame(provider["read_frame"], "inputs.descriptor_provider.read_frame")
        if not inputs["context_is_source_projection"]:
            _require(inputs["source_context_root_word"] is None and inputs["source_context_full_id_payload"] is None
                     and provider is None, "inputs:undemanded_projected_context_filled")
        binding_ready = packet["copied_input_binding_ready"]
        _require(not binding_ready or _input_bound(inputs), "packet:copied_input_binding_unavailable")
        if inputs["mailbox_after_accepted"] is False:
            _require(not binding_ready and frame["caller_snapshot_confirmed"] is False,
                     "packet:rejected_mailbox_admission_retained")
        lanes = _object(packet["lanes"], {name: "object" for name in _LANES}, "lanes")
        lane_facts = {name: _lane_facts(name, lanes[name], inputs, binding_ready) for name in _LANES}
        actual_response_bound = (inputs["capture_scope"] == "actual_application_query" and binding_ready
                                 and inputs["caller_before_after_confirmed"] is True
                                 and inputs["repeated_raw_match"] is True
                                 and inputs["mailbox_before_accepted"] is True
                                 and inputs["mailbox_after_accepted"] is True
                                 and inputs["requested_full_character_id"] not in (0, 0xFFFFFFFF)
                                 and frame["native_revision"] != 0 and frame["proof_epoch"] != 0
                                 and all(value is not None for value in (expected_snapshot_identity,
                                     expected_native_revision, expected_date_raw, expected_played_character_id)))
        for facts in lane_facts.values():
            facts["actual_target_source_claim_ready"] = actual_response_bound and facts["raw_target_ready"]
            facts["actual_source_value_ready"] = actual_response_bound and facts["source_value_ready"]
        return {**deepcopy(dict(packet)), "status": "decoded", "lane_facts": lane_facts,
                "actual_application_response_bound": actual_response_bound,
                "whole_parent_legality_decoded": False}
    except _InvalidFrontier as error:
        return {"status": "invalid", "unavailable_reason": str(error),
                "actual_application_response_bound": False,
                "lane_facts": {name: {"raw_target_ready": False, "source_value_ready": False,
                                      "actual_target_source_claim_ready": False, "actual_source_value_ready": False,
                                      **{field: None for field in _OUTPUT_FIELDS}}
                               for name in _LANES}, "whole_parent_legality_decoded": False}
