"""New no-main cases consuming the sole native query's serializer artifact.

The unchanged packet is the native producer/serializer baseline. All mutated
packets below are explicitly software-derived rejection or partial/guard cases.
The transport harness sends one software request and never enters CK3.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from xar_autoplayer.bridge.lifestyle_perk_predicate_inputs_12004 import (
    FACTS_KEY, WIRE_KEY, decode_lifestyle_perk_predicate_source_12004,
)
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    QUERY_STEP, _with_lifestyle_perk_source_facts_12004,
    query_player_lifestyle_private_v1,
)


def RunLifestylePerkSource12004NewCases(native_wire_path: str | Path) -> dict[str, object]:
    """Run once after native GREEN; read existing bytes without another query."""
    wire_path = Path(native_wire_path)
    wire_bytes = wire_path.read_bytes()
    packet = json.loads(wire_bytes)
    original = deepcopy(packet)
    source_frame = packet["read_frame"]
    names: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        names.append(name)

    def decode(value: object, **binding: object) -> dict[str, object]:
        return decode_lifestyle_perk_predicate_source_12004(value, **binding)

    facts = decode(packet, expected_snapshot_identity=source_frame["snapshot_identity"],
                   expected_native_revision=source_frame["native_revision"],
                   expected_date_raw=source_frame["date_raw"],
                   expected_played_character_id=source_frame["played_character_id"],
                   expected_target_key=packet["target_key"])
    check("production_oncewire_early_false", facts["status"] == "decoded"
          and facts["value"] is False and facts["source_value_status"] == "known_false"
          and facts["inputs"]["selected_character_field_1d0_u64"] == 1
          and facts["tail"] is None and facts["truth_trace"] is None
          and facts["inputs"]["selected_perk_identity"] is None
          and facts["inputs"]["selected_perk_magic_u32"] is None)
    check("opaque_frame_and_nullable_carriers", facts["read_frame"]["snapshot_identity"]
          == "opaque:owned-memory:query" and facts["read_frame"]["frame_identity"] is None
          and facts["read_frame"]["query_sequence"] == 71
          and facts["current_thread_tls_array_identity"] is None
          and facts["read_frame"]["public_revision"] == 11
          and facts["read_frame"]["native_revision"] == 23
          and facts["read_frame"]["proof_epoch"] == 37)
    check("original_parent_false_remains_independent", facts["native_can_select_before"] is False
          and facts["native_can_select_after"] is False
          and facts["whole_parent_legality_decoded"] is False)

    for name, plane, field, value in (
        ("bool_is_not_u64", "read_frame", "query_sequence", True),
        ("bool_is_not_signed_date", "read_frame", "date_raw", False),
        ("negative_unsigned", "inputs", "command_identity", -1),
        ("unsigned32_overflow", "inputs", "requested_full_character_id_u32", 1 << 32),
        ("unsigned64_overflow", "read_frame", "module_base", 1 << 64),
        ("signed32_overflow", "read_frame", "date_raw", 1 << 31),
    ):
        mutated = deepcopy(packet)
        mutated[plane][field] = value
        check(name, decode(mutated)["status"] == "invalid")

    mutated = deepcopy(packet)
    del mutated["inputs"]["selected_perk_magic_u32"]
    check("required_nullable_field_missing", decode(mutated)["status"] == "invalid")
    mutated = deepcopy(packet)
    mutated["invented_frame_counter"] = 1
    check("unknown_packet_field_rejected", decode(mutated)["status"] == "invalid")
    mutated = deepcopy(packet)
    mutated["inputs"]["indexed_character_full_id_u32"] ^= 0x01000000
    check("generation_mismatch_requires_fallback", decode(mutated)["status"] == "invalid")
    mutated = deepcopy(packet)
    mutated["inputs"]["requested_full_character_id_u32"] ^= 0x01000000
    check("requested_full_id_frame_binding", decode(mutated)["status"] == "invalid")
    mutated = deepcopy(packet)
    mutated["inputs"]["selected_perk_identity"] = 1
    check("early_false_does_not_read_perk", decode(mutated)["status"] == "invalid")
    mutated = deepcopy(packet)
    mutated["tail"] = {"value": False, "unavailable_reason": ""}
    check("unadmitted_prefix_does_not_read_tail", decode(mutated)["status"] == "invalid")

    # Explicitly synthetic negative admission. No positive tail or native truth
    # qualification is derived from the early-false baseline.
    admitted_negative = deepcopy(packet)
    admitted_negative["inputs"].update({"selected_character_field_1d0_u64": 0,
        "selected_perk_identity": 1, "selected_perk_magic_u32": 0x4744624F,
        "prefix_admitted": True})
    admitted_negative["value"] = True
    admitted_negative["tail"] = {"value": True, "unavailable_reason": ""}
    check("child_true_requires_qualified_truth_trace", decode(admitted_negative)["status"] == "invalid")
    admitted_negative["tail"] = None
    check("admitted_prefix_requires_tail", decode(admitted_negative)["status"] == "invalid")

    # Explicit partial source: failed first registry read means all later raw
    # operands are unread, distinct from observed numeric zero.
    partial = deepcopy(packet)
    for field in partial["inputs"]:
        if field not in {"command_identity", "unavailable_reason"}:
            partial["inputs"][field] = None
    partial["inputs"]["unavailable_reason"] = "lifestyle_perk_character_registry_unavailable"
    partial["value"] = None
    partial["unavailable_reason"] = partial["inputs"]["unavailable_reason"]
    partial_facts = decode(partial)
    check("explicit_partial_registry_unread", partial_facts["status"] == "decoded"
          and partial_facts["value"] is None and partial_facts["tail"] is None)
    partial["inputs"]["selected_character_full_id_u32"] = source_frame["played_character_id"]
    check("partial_cannot_late_fill_from_frame", decode(partial)["status"] == "invalid")

    # Apply precisely the documented 13f Finish(false) transformation to the
    # same copied packet. Earlier false facts and parent observations survive.
    rejected = deepcopy(packet)
    rejected["read_frame"]["mailbox_after_accepted"] = False
    rejected["read_frame"]["caller_snapshot_confirmed"] = False
    rejected["value"] = None
    rejected["unavailable_reason"] = "formal_mailbox_after_guard_rejected"
    rejected_facts = decode(rejected)
    check("mailbox_after_reject_preserves_raw_planes", rejected_facts["status"] == "decoded"
          and rejected_facts["value"] is None
          and rejected_facts["inputs"] == packet["inputs"]
          and rejected_facts["tail"] == packet["tail"]
          and rejected_facts["truth_trace"] == packet["truth_trace"]
          and rejected_facts["native_can_select_before"] is False
          and rejected_facts["native_can_select_after"] is False)
    check("snapshot_binding_compares_without_rewriting",
          decode(packet, expected_snapshot_identity="native:23")["status"] == "invalid")

    # Absent/null sibling preserves the exact preexisting return object.
    legacy = {"status": "available", "snapshot": {"can_select": False}}
    bindings = {"snapshot_identity": "native:23", "native_revision": 23,
                "date_raw": source_frame["date_raw"],
                "played_character_id": source_frame["played_character_id"]}
    check("optional_absent_keeps_legacy_shape",
          _with_lifestyle_perk_source_facts_12004(legacy, {}, **bindings) is legacy
          and _with_lifestyle_perk_source_facts_12004(legacy, {WIRE_KEY: None}, **bindings) is legacy)

    # One SOFTWARE transport wrapper. Its legacy canonical binding is native:23;
    # the native artifact's opaque identity remains unchanged and is diagnosed.
    # The wrapper is not an actual formal query response or a game observation.
    full_id = source_frame["played_character_id"]
    episode = f"native-{full_id}-source-transport-software"
    snapshot = {"paused": True, "map_ready": True, "revision": 11,
        "native_revision": 23, "date_raw": source_frame["date_raw"],
        "played_character": {"character_id": full_id},
        "episode_run_id": episode, "snapshot_id": "native:23"}
    life_snapshot = {"status": "available", "snapshot_id": "native:23",
        "public_revision": 23, "native_revision": 23, "proof_epoch": 23,
        "date_raw": source_frame["date_raw"], "player_character_id": full_id,
        "can_select": packet["native_can_select_before"]}
    sent: list[dict[str, object]] = []
    counts = {"snapshots": 0, "waits": 0}

    def read_snapshot() -> dict[str, object]:
        counts["snapshots"] += 1
        return deepcopy(snapshot)

    def wait(request_id: str, timeout: float) -> dict[str, object]:
        counts["waits"] += 1
        return {"request_id": request_id, "ok": True, "result": {
            "step": QUERY_STEP, "private_build": True, "advertised": False,
            "status": "available", "episode_run_id": episode,
            "formal_precondition_status": "ready", "snapshot": deepcopy(life_snapshot),
            WIRE_KEY: packet}}

    driver = SimpleNamespace(allow_private_lifestyle_formal_trial=True,
        take_snapshot=read_snapshot, endpoint=SimpleNamespace(send=sent.append),
        state=SimpleNamespace(wait_for_command_result=wait), command_timeout_seconds=1.0)
    response = query_player_lifestyle_private_v1(driver, expected_revision=11)
    check("same_once_transport_keeps_parent_and_diagnoses_optional_binding",
          response["status"] == "available" and response["snapshot"]["can_select"] is False
          and response[FACTS_KEY]["status"] == "invalid"
          and response[FACTS_KEY]["unavailable_reason"] == "read_frame:snapshot_identity_binding_mismatch"
          and len(sent) == 1 and counts == {"snapshots": 2, "waits": 1})
    check("raw_wire_packet_unchanged", packet == original)
    return {"status": "GREEN", "cases": len(names), "case_names": names,
        "wire_path": str(wire_path), "wire_bytes": len(wire_bytes),
        "wire_sha256": hashlib.sha256(wire_bytes).hexdigest(),
        "native_accessor_demands_from_python": 0, "software_transport_requests": len(sent),
        "qualification": "Unchanged production serializer packet plus labeled derived software cases; no live game, callback or whole-parent source qualification"}
