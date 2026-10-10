"""New no-main cases from the successor's unchanged production once wire.

Only the first new native production packet is the baseline. Mutations are
explicit software rejection/partial/finalizer cases, never actual target,
clock, body or returned-value evidence. No old51d cases are invoked.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from xar_autoplayer.bridge.lifestyle_perk_trigger_frontier_12004 import (
    FACTS_KEY, WIRE_KEY, decode_lifestyle_perk_trigger_frontier_12004,
)
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    STATE_QUERY_STEP, _with_lifestyle_perk_source_facts_12004,
    query_player_lifestyle_private_v1,
)

_OUTPUTS = ("returned_raw_u8", "returned_raw_u16", "returned_qword0", "returned_qword1")
_NAMES = ("descriptor_al", "root_kind_ax", "root_mask_qwords", "final_c8_al")


def RunLifestylePerkTriggerFrontier12004NewCases(native_wire_path: str | Path) -> dict[str, object]:
    """Consume lead16e's new wire once, with no new native accessor demand."""
    path = Path(native_wire_path)
    wire_bytes = path.read_bytes()
    packet = json.loads(wire_bytes)
    original = deepcopy(packet)
    inputs = packet["inputs"]
    frame = inputs["read_frame"]
    names: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        names.append(name)

    binding = {"expected_snapshot_identity": frame["snapshot_identity"],
               "expected_native_revision": frame["native_revision"],
               "expected_date_raw": frame["date_raw"],
               "expected_played_character_id": inputs["requested_full_character_id"],
               "expected_target_key": inputs["target_key"]}

    def decode(value: object, **extra: object) -> dict[str, object]:
        return decode_lifestyle_perk_trigger_frontier_12004(value, **{**binding, **extra})

    def other_lanes_decoded(facts: dict[str, object], rejected: str) -> bool:
        return facts["status"] == "decoded" and facts["lane_facts"][rejected]["status"] == "invalid" \
            and all(facts["lane_facts"][name]["status"] == "decoded" for name in _NAMES if name != rejected)

    facts = decode(packet)
    check("new_production_once_wire_copied_class_and_slots", facts["status"] == "decoded"
          and all(facts["lane_facts"][name]["status"] == "decoded" for name in _NAMES)
          and inputs["receiver_identity"] == inputs["selected_perk_identity"] + 0x80
          and inputs["vtable_rva"] == 0x5000 and packet["copied_input_binding_ready"] is True)
    check("fixture_raw_readiness_does_not_grant_actual_source_claim",
          inputs["capture_scope"] == "owned_memory_fixture"
          and facts["actual_application_response_bound"] is False
          and all(facts["lane_facts"][name]["actual_target_source_claim_ready"] is False
                  and facts["lane_facts"][name]["actual_source_value_ready"] is False for name in _NAMES))
    check("opaque_frame_and_missing_numeric_identity_preserved",
          frame["snapshot_identity"] == "opaque:owned-memory:query" and frame["frame_identity"] is None
          and frame["query_sequence"] == 71 and frame["native_revision"] == 23
          and frame["proof_epoch"] == 37 and inputs["public_revision"] == 11
          and inputs["mailbox_before_accepted"] is True and inputs["mailbox_after_accepted"] is True)
    check("slot_storage_is_distinct_from_copied_target", all(
          inputs["slots"][slot]["slot_identity"] == inputs["vtable_identity"] + offset
          and inputs["slots"][slot]["target_rva"] == rva
          and inputs["slots"][slot]["target_identity"] != inputs["slots"][slot]["slot_identity"]
          for slot, offset, rva in (("slot58", 0x58, 0x1000), ("slot60", 0x60, 0x2000), ("slotc8", 0xC8, 0x3000))))
    check("four_returned_planes_independently_unknown",
          inputs["source_context_root_word"] is None and inputs["descriptor_provider"] is None
          and all(packet["lanes"][name]["natural_witness"] is None
                  and facts["lane_facts"][name]["source_value_ready"] is False
                  and all(facts["lane_facts"][name][field] is None for field in _OUTPUTS) for name in _NAMES))
    check("original_parent_observations_and_boundary_preserved",
          inputs["native_before"] is False and inputs["native_after"] is False
          and facts["whole_parent_legality_decoded"] is False)

    for name, plane, field, value in (
        ("bool_not_signed_date", "frame", "date_raw", False),
        ("bool_not_pointer_identity", "inputs", "command_identity", True),
        ("full_id_unsigned_overflow", "inputs", "requested_full_character_id", 1 << 32),
        ("negative_unsigned_pointer", "inputs", "selected_perk_identity", -1),
        ("signed_date_overflow", "frame", "date_raw", 1 << 31),
    ):
        changed = deepcopy(packet)
        target = changed["inputs"]["read_frame"] if plane == "frame" else changed["inputs"]
        target[field] = value
        check(name, decode(changed)["status"] == "invalid")
    changed = deepcopy(packet)
    del changed["inputs"]["read_frame"]["frame_identity"]
    check("required_nullable_carrier_missing", decode(changed)["status"] == "invalid")
    changed = deepcopy(packet)
    changed["inputs"]["read_frame"]["frame_identity"] = 0
    check("missing_numeric_identity_must_remain_null", decode(changed)["status"] == "invalid")
    changed = deepcopy(packet)
    changed["inputs"]["capture_scope"] = "current_game_from_snapshot_hash"
    check("invented_capture_scope_rejected", decode(changed)["status"] == "invalid")

    changed = deepcopy(packet)
    changed["lanes"]["descriptor_al"]["returned_raw_u8"] = False
    check("bool_not_al_and_other_lanes_preserved", other_lanes_decoded(decode(changed), "descriptor_al"))
    changed = deepcopy(packet)
    changed["lanes"]["root_kind_ax"]["returned_raw_u16"] = 1 << 16
    check("ax_width_failure_is_independent", other_lanes_decoded(decode(changed), "root_kind_ax"))
    changed = deepcopy(packet)
    changed["inputs"]["slots"]["slot60"]["target_rva"] += 1
    check("mask_target_rva_mismatch_is_independent", other_lanes_decoded(decode(changed), "root_mask_qwords"))
    changed = deepcopy(packet)
    changed["lanes"]["root_kind_ax"]["returned_raw_u16"] = 0
    rejected = decode(changed)
    check("unqualified_zero_ax_is_unknown_not_false", other_lanes_decoded(rejected, "root_kind_ax")
          and rejected["lane_facts"]["root_kind_ax"]["returned_raw_u16"] is None)
    for name, basis in (("pure_source_requires_exact_proof", "closed_pure_target_source"),
                        ("natural_return_requires_real_witness", "natural_original_once")):
        changed = deepcopy(packet)
        changed["lanes"]["root_kind_ax"].update({"raw_target_ready": True, "source_value_ready": True,
            "returned_raw_u16": 0, "result_source": basis})
        check(name, other_lanes_decoded(decode(changed), "root_kind_ax"))
    changed = deepcopy(packet)
    changed["lanes"]["root_kind_ax"]["call_rva"] += 1
    check("literal_callsite_mismatch_is_independent", other_lanes_decoded(decode(changed), "root_kind_ax"))
    check("full_generation_compared_to_existing_caller",
          decode(packet, expected_played_character_id=inputs["requested_full_character_id"] ^ 0x01000000)["status"] == "invalid")
    changed = deepcopy(packet)
    changed["inputs"]["source_context_root_word"] = 4
    check("undemanded_context_cannot_be_late_filled", decode(changed)["status"] == "invalid")

    # Explicit software partial-copy shape, using the production collector's
    # per-slot unread transformation. No actual partial-wire credit is claimed.
    changed = deepcopy(packet)
    changed["inputs"]["slots"]["slot60"].update({"target_identity": None, "target_rva": None,
        "copied": False, "unavailable_reason": "trigger_vtable_slot_unreadable"})
    changed["lanes"]["root_mask_qwords"]["target"] = deepcopy(changed["inputs"]["slots"]["slot60"])
    changed["lanes"]["root_mask_qwords"]["raw_target_ready"] = False
    partial = decode(changed)
    check("partial_slot_does_not_erase_other_copies", partial["status"] == "decoded"
          and partial["lane_facts"]["root_mask_qwords"]["source_value_ready"] is False
          and partial["inputs"]["slots"]["slot58"] == inputs["slots"]["slot58"]
          and partial["inputs"]["slots"]["slotc8"] == inputs["slots"]["slotc8"])

    # Precisely the pure finalizer's rejection transform, with the formal
    # owner's copied actual-after Boolean, applied to the same owned packet.
    changed = deepcopy(packet)
    changed["copied_input_binding_ready"] = False
    changed["inputs"]["read_frame"]["caller_snapshot_confirmed"] = False
    changed["inputs"]["mailbox_after_accepted"] = False
    for lane in changed["lanes"].values():
        lane.update({"raw_target_ready": False, "source_value_ready": False, "result_source": "unavailable",
                     "unavailable_reason": "lifestyle_trigger_frontier_current_query_binding_unconfirmed"})
        for field in _OUTPUTS:
            lane[field] = None
    rejected = decode(changed)
    check("mailbox_reject_keeps_raw_targets_without_credit", rejected["status"] == "decoded"
          and rejected["inputs"]["slots"] == inputs["slots"]
          and all(rejected["lane_facts"][name]["raw_target_ready"] is False
                  and rejected["lane_facts"][name]["source_value_ready"] is False for name in _NAMES))
    check("snapshot_binding_compared_without_rewriting", decode(packet, expected_snapshot_identity="native:23")["status"] == "invalid")

    transport_binding = {"snapshot_identity": frame["snapshot_identity"], "native_revision": frame["native_revision"],
        "date_raw": frame["date_raw"], "played_character_id": inputs["requested_full_character_id"]}
    legacy = {"status": "available", "snapshot": {"can_select": False}}
    check("absent_or_null_successor_keeps_legacy_shape",
          _with_lifestyle_perk_source_facts_12004(legacy, {}, **transport_binding) is legacy
          and _with_lifestyle_perk_source_facts_12004(legacy, {WIRE_KEY: None}, **transport_binding) is legacy)
    attached = _with_lifestyle_perk_source_facts_12004(legacy, {WIRE_KEY: packet}, **transport_binding)
    check("same_response_source_facts_append_is_independent", attached["status"] == "available"
          and attached["snapshot"] is legacy["snapshot"] and attached["snapshot"]["can_select"] is False
          and attached[FACTS_KEY]["status"] == "decoded" and attached[FACTS_KEY]["actual_application_response_bound"] is False)

    # Exactly one SOFTWARE current-state transport request. The unchanged
    # production packet has opaque identity; its optional binding diagnostic
    # accompanies the successful legacy native:23 wrapper without changing it.
    full_id = inputs["requested_full_character_id"]
    episode = f"native-{full_id}-frontier-software"
    snapshot = {"paused": True, "map_ready": True, "revision": 11, "native_revision": 23,
        "date_raw": frame["date_raw"], "played_character": {"character_id": full_id},
        "episode_run_id": episode, "snapshot_id": "native:23"}
    life = {"status": "available", "snapshot_id": "native:23", "public_revision": 23,
        "native_revision": 23, "proof_epoch": 23, "date_raw": frame["date_raw"],
        "player_character_id": full_id, "can_select": inputs["native_before"]}
    sent: list[dict[str, object]] = []
    counts = {"snapshots": 0, "waits": 0}

    def read() -> dict[str, object]:
        counts["snapshots"] += 1
        return deepcopy(snapshot)

    def wait(request_id: str, timeout: float) -> dict[str, object]:
        counts["waits"] += 1
        return {"ok": True, "request_id": request_id, "result": {"step": STATE_QUERY_STEP,
            "private_build": True, "advertised": False, "status": "available", "episode_run_id": episode,
            "formal_precondition_status": "ready", "snapshot": deepcopy(life), WIRE_KEY: packet}}

    driver = SimpleNamespace(allow_private_lifestyle_formal_trial=True, take_snapshot=read,
        endpoint=SimpleNamespace(send=sent.append), state=SimpleNamespace(wait_for_command_result=wait),
        command_timeout_seconds=1.0)
    response = query_player_lifestyle_private_v1(driver, expected_revision=11, query_step=STATE_QUERY_STEP)
    check("once_state_response_preserves_legacy_parent_and_diagnoses_binding",
          response["status"] == "available" and response["snapshot"]["can_select"] is False
          and response[FACTS_KEY]["status"] == "invalid"
          and response[FACTS_KEY]["unavailable_reason"] == "inputs:snapshot_identity_binding_mismatch"
          and len(sent) == 1 and counts == {"snapshots": 2, "waits": 1})
    check("unchanged_production_packet_bytes_and_fields", packet == original)
    return {"status": "GREEN", "cases": len(names), "case_names": names,
        "wire_path": str(path), "wire_bytes": len(wire_bytes), "wire_sha256": hashlib.sha256(wire_bytes).hexdigest(),
        "software_transport_requests": len(sent), "new_native_accessor_demands": 0, "old51d_case_invocations": 0,
        "qualification": "New production serializer once-wire, owned_memory_fixture, derived software negatives/partial/finalizer; no actual target/body/clock/returned-value/whole-parent credit"}
