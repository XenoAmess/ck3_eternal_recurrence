"""P43 actual source/frame projection; all refusal execution here is synthetic."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.vanilla_events import event_offline_analysis
from xar_autoplayer.vanilla_events.populist1001_known_refusal_v1 import (
    choose_source_reviewed_populist_refusal_v1,
    verify_source_reviewed_populist_refusal_result_v1,
)


FIXTURE = Path(__file__).parent / "fixtures/p43_populist_actual193_projection.json"


def case():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def choose(fixture):
    return choose_source_reviewed_populist_refusal_v1(
        fixture["plan"], snapshot=fixture["snapshot"],
        action_steps=("select-event-option-3", "select-event-option-4"))


def test_current_exact_source_fingerprint_binds_new_native_calculated_id():
    fixture = case()
    selected = choose(fixture)
    assert selected["selected_step"] == "select-event-option-4"
    assert selected["active_event"]["selected_native_option_index"] == 3
    assert fixture["plan"]["selected_step"] == "select-event-option-3"
    outcome = selected["faction_demand_source_outcome"]
    assert outcome["saved_target_title_id"] == 2200
    assert outcome["same_frame_faction_strength"] == "not_available_in_bound_event_context"
    assert outcome["counterfactual_optimality_verified"] is False
    assert outcome["war_started_verified"] is False
    assert outcome["title_retention_verified"] is False
    assert outcome["visible_alternatives"] == [
        {"native_option_index": 2, "expected_effect": "grant_populist_independence", "selected": False},
        {"native_option_index": 3, "expected_effect": "start_faction_war", "selected": True}]


@pytest.mark.parametrize("mutation", (
    "fingerprint", "source_hash", "catalogue_hash", "calculated_id", "source_rebound", "unknown",
))
def test_changed_source_binding_or_unreviewed_letter_preserves_fallback(mutation):
    fixture = case()
    capture = fixture["plan"]["unhandled_event_fallback"]
    audit = capture["source_knowledge"]
    if mutation == "fingerprint":
        audit["fingerprint"] = "0" * 64
    elif mutation in ("source_hash", "catalogue_hash"):
        binding = event_offline_analysis._native_binding(capture)
        binding.update(
            source_sha256="eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd",
            option_catalogue_sha256="5c76ae1a7cc44883f5d4af07e6f5c2e59986b9b0c6d6ca9cb379ac7ce298bace")
        binding["source_sha256" if mutation == "source_hash" else "option_catalogue_sha256"] = "0" * 64
        audit["fingerprint"] = event_offline_analysis._fingerprint(binding)
    elif mutation == "calculated_id":
        capture["window_context"]["calculated_event_id"] += 1
    elif mutation == "source_rebound":
        audit["binding_mode"] = "source_rebound"
    else:
        audit["status"] = "unknown"
        capture["registry_known"] = False
    assert choose(fixture) is fixture["plan"]


def test_production_strategy_annotation_then_known_refusal_hook(monkeypatch):
    fixture = case()
    # Only the core native-input acquisition and filesystem source validation
    # are doubled; the production annotation and ordinary return hook execute.
    original = copy.deepcopy(fixture["plan"])
    original["phase"] = "active_event_unhandled_first_rendered_option"
    capture = original["unhandled_event_fallback"]
    capture["registry_known"] = False
    capture["source_knowledge"] = {"status": "unknown", "rejected_entries": []}
    audit = fixture["plan"]["unhandled_event_fallback"]["source_knowledge"]
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **k: copy.deepcopy(original))
    monkeypatch.setattr(event_offline_analysis, "load_source_reviewed_event_v1",
                        lambda *a, **k: ({"classification": "offline-source-reviewed-user-first-rendered-policy"}, copy.deepcopy(audit)))
    selected = strategy.choose_one_life_turn(
        [], snapshot=fixture["snapshot"],
        action_steps=("select-event-option-3", "select-event-option-4"),
        pending_interaction_registry_state_dir="synthetic-source-registry")
    assert selected["phase"] == "active_event_source_reviewed_populist_refusal"
    assert selected["selected_step"] == "select-event-option-4"
    assert selected["unhandled_event_fallback"]["source_knowledge"]["fingerprint"] == audit["fingerprint"]


class ReceiptService(GameplayBridgeService):
    def _strategy_state_dir(self):
        return self.test_state_dir

    def _execute_planned_turn_without_unhandled_capture(self, planned, *, before_submit=None):
        self.calls += 1
        return {**copy.deepcopy(self.test_receipt), "plan": planned["plan"]}


def execute_counterfactual(tmp_path, *, native_index=3):
    fixture = case()
    plan = choose(fixture)
    capture = plan["unhandled_event_fallback"]
    frame = capture["binding"]
    next_snapshot = "native:" + str(frame["native_revision"] + 1)
    post = {
        "status": "event_instance_advanced", "postcondition_verified": True,
        "old_event_instance_id": capture["current_event_instance_id"], "new_event_instance_id": None,
        "selected_option_number": 4, "selected_native_option_index": native_index,
        "starting_snapshot_id": frame["snapshot_id"], "starting_revision": frame["revision"],
        "ending_snapshot_id": next_snapshot, "ending_revision": frame["revision"] + 1,
        **{k: frame[k] for k in ("episode_run_id", "connection_generation", "bridge_pid")}}
    inner = {
        "step": "select-event-option-4", "accepted": True, "status": "submitted",
        "snapshot_id": next_snapshot, "revision": frame["revision"] + 1,
        "event_instance_id": capture["current_event_instance_id"], "option_number": 4,
        "option_index": native_index, "event_selection": post}
    service = object.__new__(ReceiptService)
    service.calls = 0
    service.test_state_dir = tmp_path
    service.test_receipt = {"status": "executed", "selected_step": "select-event-option-4", "result": inner}
    planned = {"plan": plan, "snapshot_id": frame["snapshot_id"], "revision": frame["revision"]}
    return service, planned


def test_current_id_service_capture_and_receipt_chain_zero_business_credit(tmp_path):
    service, planned = execute_counterfactual(tmp_path)
    body = service._execute_planned_turn(planned)
    assert service.calls == 1
    record = verify_source_reviewed_populist_refusal_result_v1(body)
    assert record["primitive_accepted"] is True
    assert record["business_success_inferred"] is False
    assert record["victory_verified"] is False
    assert record["title_retention_verified"] is False
    assert record["replay_allowed"] is False
    before = json.loads(Path(body["unhandled_event_fallback_evidence"]["before"]["path"]).read_text(encoding="utf-8"))
    assert before["selection"]["native_option_index"] == 3
    assert before["window_context"]["calculated_event_id"] == 3571001


def test_wrong_native_acceptance_receipt_is_retained_without_replay(tmp_path):
    service, planned = execute_counterfactual(tmp_path, native_index=2)
    with pytest.raises(ValueError, match="receipt/selection differs") as caught:
        service._execute_planned_turn(planned)
    assert service.calls == 1
    assert caught.value.unhandled_event_fallback_evidence["replay_allowed"] is False
