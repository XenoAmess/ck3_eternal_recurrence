"""Portable offline tests; every frame, context and reply below is SYNTHETIC.

Run with the repository's normal xar_autoplayer import path. No game installation,
local D: paths, Native transport, desktop, or MCP server is used.
"""

import copy
import json
from pathlib import Path

import pytest

from xar_autoplayer import pending_interaction_fallback as fallback
from xar_autoplayer import strategy
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService


@pytest.fixture
def fixture():
    pending_id, actor, sender, native, public, date = 301989889, 101, 102, 7, 3, 1000
    context = {
        "schema": "pending-character-interaction-context-v1", "schema_version": 1,
        "status": "available", "snapshot_revision": native, "date_raw": date,
        "pending_interaction_id": pending_id, "reason": None,
        "build": {"version": "1.20.0.4", "exe_sha256": "SYNTHETIC-NOT-A-BUILD"},
        "definition": {"canonical_key": "request_clerical_chastity_interaction",
                       "deterministic_key_hash": 1409884230, "runtime_ordinal": 9},
        "roles": {"actor_character_id": sender, "recipient_character_id": actor,
                  "secondary_actor_character_id": -1, "secondary_recipient_character_id": -1,
                  "intermediary_character_id": -1},
        "target": {"present": False, "raw_type_index": 0,
                   "raw_16_bytes_hex": "00000000ffffffff0000000000000000",
                   "type_key_status": "absent", "type_key": None, "type_key_reason": None,
                   "typed_identity_status": "absent", "typed_identity": None,
                   "typed_identity_reason": None},
        "send_options": {"exclusive": False, "definition_count": 2, "context_count": 2,
            "rows": [{"native_index": i, "numeric_flag_identifier": flag,
                      "selected": bool(i), "is_shown": bool(i), "is_valid": True,
                      "canonical_flag_status": "unavailable", "canonical_flag_key": None,
                      "canonical_flag_reason": "synthetic_unmapped_flag"}
                     for i, flag in enumerate((49, 35850))]},
        "routing": {"kind": 0, "played_character_id": actor,
                    "current_responder_role": "recipient", "reply_execution_channel": "recipient",
                    "local_route": True, "auto_accept_notification": False},
        "deadline": {"age_days": 0, "expiration_days": 60, "remaining_days": 60,
                     "expiry_boundary_status": "not_reached"},
        "auto_accept": {"status": "available", "value": False, "reason": None},
        # Deliberately accept-first: dictionary order is NOT rendered GUI order.
        "legality": {name: {"status": "available", "allowed": name != "acknowledge",
                            "reason": None if name != "acknowledge" else "normal_reply_channel"}
                     for name in ("accept", "reject", "block", "acknowledge")},
        "terms": {"special_data_present": False,
            "structured_costs": {"status": "available", "reason": None, "value": {
                "raw_scale": 100000, "payer_role": "actor", "application_timing": "on_send",
                "pending_payment_state": "already_applied",
                "entries": [{"resource_key": key, "raw": 15000000 if key == "piety" else 0}
                            for key in ("gold", "prestige", "piety", "renown", "influence", "herd",
                                        "treasury", "treasury_or_gold", "merit", "barter_goods")]}}},
        "readiness": {"same_frame_ready": True, "stable_definition_ready": True,
                      "roles_ready": True, "reply_legality_ready": True,
                      "interaction_semantic_decision_ready": False},
        "provenance": {"backend_id": "SYNTHETIC-OFFLINE-FIXTURE-NO-NATIVE-CALL"},
    }
    for name in ("special_war_binding", "structured_exchanges", "structured_effect_preview",
                 "recipient_ai_acceptance_score", "recipient_ai_final_decision"):
        context["terms"][name] = {"status": "unavailable", "value": None,
                                 "reason": "synthetic_not_applicable_or_unavailable"}
    snapshot = {"snapshot_id": "synthetic:7", "revision": public, "native_revision": native,
                "date_raw": date, "episode_run_id": "synthetic-episode", "paused": True,
                "map_ready": True, "backend_id": "native-headless", "bridge_pid": 999,
                "connection_generation": 2, "played_character": {"character_id": actor, "alive": True},
                "pending_character_interaction": {"instance_id": pending_id,
                    "sender_character_id": sender, "auto_accept_notification": False},
                "active_event": None, "active_wars": [], "player_armies": []}
    result = {"step": "query-pending-character-interaction-context-v1", "accepted": True,
              "status": "available", "snapshot_revision": native,
              "pending_character_interaction_context": context,
              "queried_snapshot_id": snapshot["snapshot_id"], "queried_revision": public,
              "queried_native_revision": native}
    return snapshot, context, [{"index": 1, "command": result["step"], "ok": True, "result": result}]


ACTIONS = {"query-pending-character-interaction-context-v1", "reject-pending-character-interaction",
           "accept-pending-character-interaction"}


def choose(fixture, actions=ACTIONS):
    snapshot, _, rows = fixture
    return strategy.choose_one_life_turn(rows, snapshot=snapshot, action_steps=actions)


def planned(fixture):
    snapshot, _, _ = fixture
    return {"plan": choose(fixture), "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"]}


def reply(fixture):
    snapshot, _, _ = fixture
    pending = snapshot["pending_character_interaction"]
    return {"accepted": True, "step": "reject-pending-character-interaction",
            "interaction_result": {"status": "rejected", "instance_id": pending["instance_id"],
                                   "sender_character_id": pending["sender_character_id"]},
            "remaining_pending_character_interaction": None, "paused": True,
            "snapshot_id": "synthetic:8", "revision": 4}


def test_known_religious_hash_and_source_left_order(fixture):
    value = choose(fixture)
    assert value["selected_step"] == "reject-pending-character-interaction"
    assert value["decision"]["classification"] == "reviewed_religious_clerical_chastity_request"
    assert value["decision"]["registry_known"] is True
    capture = value["unhandled_interaction_fallback"]
    assert capture["context"] == fixture[1]
    assert capture["selection"]["rendered_index"] == 0
    assert capture["selection"]["action"] == "reject"
    fixture[1]["definition"]["deterministic_key_hash"] += 1
    assert choose(fixture)["decision"]["registry_known"] is False


def test_unknown_left_capture_and_completed_batch_dedup(fixture, tmp_path):
    fixture[1]["definition"].update(canonical_key="synthetic_unknown_interaction", deterministic_key_hash=12)
    value = planned(fixture)
    assert value["plan"]["selected_step"] == "reject-pending-character-interaction"
    ticket = fallback.capture_pending_interaction_before_v1(tmp_path, value)
    before = json.loads(Path(ticket["before"]["path"]).read_bytes())
    assert before["context"] == fixture[1] and before["offline_followup_required"] is True
    fallback.capture_pending_interaction_after_v1(ticket, outcome={"result": reply(fixture)})
    batch = fallback.collect_completed_interaction_incidents_v1(tmp_path)
    assert len(batch) == 1 and batch[0]["registry_known"] is False
    assert batch[0]["original_pending_advanced_verified"] is True
    assert fallback.collect_completed_interaction_incidents_v1(tmp_path, [batch[0]["incident_id"]]) == []


@pytest.mark.parametrize("legality", [
    {"status": "available", "allowed": False},
    {"status": "unavailable", "allowed": None},
])
def test_disabled_left_never_selects_right(fixture, legality):
    fixture[1]["legality"]["reject"] = legality
    assert choose(fixture)["selected_step"] is None
    assert choose(fixture)["unhandled_interaction_fallback"]["selection"]["action"] == "reject"


def test_missing_left_primitive_never_selects_right(fixture):
    assert choose(fixture, {"accept-pending-character-interaction"})["selected_step"] is None


@pytest.mark.parametrize("field", ["native_revision", "revision", "date_raw", "instance_id"])
def test_existing_exact_context_frame_and_original_id_guard(fixture, field):
    target = fixture[0]["pending_character_interaction"] if field == "instance_id" else fixture[0]
    target[field] += 1
    assert choose(fixture)["selected_step"] != "reject-pending-character-interaction"


def test_dedicated_selection_keeps_priority(fixture, monkeypatch):
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **k: {
        "policy": "one-life-turn-v1", "phase": "pending_synthetic_known_accept",
        "selected_step": "accept-pending-character-interaction"})
    value = choose(fixture)
    assert value["selected_step"] == "accept-pending-character-interaction"
    assert "unhandled_interaction_fallback" not in value


def test_service_durable_before_precedes_single_dispatch(fixture, tmp_path):
    service = GameplayBridgeService.__new__(GameplayBridgeService)
    service.driver = type("SyntheticDriver", (), {"state_dir": tmp_path})()
    calls = []

    def execute(step, *, expected_revision):
        files = list((tmp_path / "evidence/unhandled-interactions").glob("*.before.json"))
        assert len(files) == 1
        before = json.loads(files[0].read_bytes())
        assert before["context"] == fixture[1] and before["dispatch_attempted"] is False
        calls.append((step, expected_revision))
        return reply(fixture)

    service.execute_step = execute
    outcome = service._execute_planned_turn(planned(fixture))
    assert calls == [("reject-pending-character-interaction", fixture[0]["revision"])]
    proof = outcome["unhandled_event_fallback_evidence"]
    assert proof["command_acknowledged"] is True
    assert proof["original_pending_advanced_verified"] is True
    assert proof["material_effects_verified"] is False and proof["replay_allowed"] is False


@pytest.mark.parametrize("mutation", ["ack_only", "same_pending", "wrong_original", "unpaused"])
def test_ack_is_separate_from_exact_original_pending_advancement(fixture, tmp_path, mutation):
    result = reply(fixture)
    if mutation == "ack_only":
        result = {"accepted": True}
    elif mutation == "same_pending":
        result["remaining_pending_character_interaction"] = fixture[0]["pending_character_interaction"]
    elif mutation == "wrong_original":
        result["interaction_result"]["instance_id"] += 1
    else:
        result["paused"] = False
    ticket = fallback.capture_pending_interaction_before_v1(tmp_path, planned(fixture))
    proof = fallback.capture_pending_interaction_after_v1(ticket, outcome={"result": result})
    assert proof["command_acknowledged"] is True
    assert proof["original_pending_advanced_verified"] is False
    assert proof["material_effects_verified"] is False


def test_original_dispatch_error_is_preserved_without_replay(fixture, tmp_path):
    service = GameplayBridgeService.__new__(GameplayBridgeService)
    service.driver = type("SyntheticDriver", (), {"state_dir": tmp_path})()
    error = BridgeUnavailableError("SYNTHETIC unknown reply outcome")
    calls = []

    def execute(*args, **kwargs):
        calls.append((args, kwargs))
        raise error

    service.execute_step = execute
    with pytest.raises(BridgeUnavailableError) as caught:
        service._execute_planned_turn(planned(fixture))
    assert caught.value is error and len(calls) == 1
    assert caught.value.unhandled_event_fallback_evidence["replay_allowed"] is False
