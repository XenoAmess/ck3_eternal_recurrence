"""Exact .4 populist demand: source-bound refusal and event receipt continuity.

The captured window/frame is projected from actual AUTO518. The refusal ACK
is counterfactual and deliberately does not claim an observed CK3 victory.
"""
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


FIXTURE = Path(__file__).parent / "fixtures/event72_populist_actual518_source_reviewed.json"


def case():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def selected(fixture, *, action_steps=("select-event-option-3", "select-event-option-4")):
    return choose_source_reviewed_populist_refusal_v1(
        fixture["plan"], snapshot=fixture["snapshot"], action_steps=action_steps)


def test_portable_actual518_strategy_hook_selects_bound_refusal(monkeypatch):
    fixture = case()
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core",
                        lambda *a, **k: copy.deepcopy(fixture["plan"]))
    monkeypatch.setattr(event_offline_analysis, "annotate_source_reviewed_event_plan_v1",
                        lambda plan, state_dir: copy.deepcopy(fixture["plan"]))
    plan = strategy.choose_one_life_turn(
        [], snapshot=fixture["snapshot"],
        action_steps=("select-event-option-3", "select-event-option-4"),
        pending_interaction_registry_state_dir="synthetic-managed-source-registry",
    )
    assert plan["phase"] == "active_event_source_reviewed_populist_refusal"
    assert plan["selected_step"] == "select-event-option-4"
    assert plan["active_event"]["selected_native_option_index"] == 3
    assert plan["active_event"]["selected_rendered_index"] == 1
    assert plan["event_decision"]["selected_native_option_index"] == 3
    assert plan["event_decision"]["selected_option_number"] == 4
    assert plan["event_decision"]["material_effects_verified"] is False
    capture = plan["unhandled_event_fallback"]
    assert capture["selection"]["selected_step"] == plan["selected_step"]
    assert capture["selection"]["native_option_index"] == 3
    assert capture["selection"]["rendered_index"] == 1
    assert plan["faction_demand_source_outcome"]["war_started_verified"] is False
    assert plan["faction_demand_source_outcome"]["victory_verified"] is False
    assert fixture["plan"]["selected_step"] == "select-event-option-3"


@pytest.mark.parametrize("change", (
    "fingerprint", "source_mode", "backend", "date", "pid", "actor",
    "scope", "layout", "disabled", "advertisement", "conversion_first",
))
def test_other_source_frame_or_option_remains_first_enabled(change):
    fixture = case()
    capture = fixture["plan"]["unhandled_event_fallback"]
    context = capture["window_context"]
    steps = ("select-event-option-3", "select-event-option-4")
    if change == "fingerprint":
        capture["source_knowledge"]["fingerprint"] = "0" * 64
    elif change == "source_mode":
        capture["source_knowledge"]["binding_mode"] = "source_rebound"
    elif change == "backend":
        context["provenance"]["backend_id"] = "ck3-1.20.0.3-native-event-window-v1"
    elif change == "date":
        fixture["snapshot"]["date_raw"] += 24
    elif change == "pid":
        fixture["snapshot"]["diagnostics"]["bridge_pid"] += 1
    elif change == "actor":
        fixture["snapshot"]["played_character"]["character_id"] += 1
    elif change == "scope":
        for row in context["saved_scopes"]:
            if row["name"] == "faction_target":
                row["scope"]["typed_identity"]["character_id"] += 1
    elif change == "layout":
        context["options"][1]["rendered_index"] = 2
    elif change == "disabled":
        context["options"][1]["enabled"] = False
    elif change == "advertisement":
        steps = ("select-event-option-3",)
    else:
        context["options"][0]["native_option_index"] = 0
    assert selected(fixture, action_steps=steps) is fixture["plan"]


class _ReceiptService(GameplayBridgeService):
    def _strategy_state_dir(self):
        return self.test_state_dir

    def _execute_planned_turn_without_unhandled_capture(self, planned, *, before_submit=None):
        self.calls += 1
        return {**copy.deepcopy(self.test_receipt), "plan": planned["plan"]}


def execute_counterfactual(tmp_path, fixture, *, native_option_index=3):
    plan = selected(fixture)
    receipt = copy.deepcopy(fixture["counterfactual_refusal_receipt"])
    receipt["result"]["option_index"] = native_option_index
    receipt["result"]["event_selection"]["selected_native_option_index"] = native_option_index
    service = object.__new__(_ReceiptService)
    service.test_state_dir = tmp_path
    service.test_receipt = receipt
    service.calls = 0
    planned = {"plan": plan, "snapshot_id": fixture["snapshot"]["snapshot_id"],
               "revision": fixture["snapshot"]["revision"]}
    return service, planned


def test_service_capture_and_queue_record_bind_counterfactual_native3(tmp_path):
    fixture = case()
    service, planned = execute_counterfactual(tmp_path, fixture)
    body = service._execute_planned_turn(planned)
    assert service.calls == 1
    evidence = body["unhandled_event_fallback_evidence"]
    before = json.loads(Path(evidence["before"]["path"]).read_text(encoding="utf-8"))
    after = json.loads(Path(evidence["after"]["path"]).read_text(encoding="utf-8"))
    assert before["selection"]["native_option_index"] == 3
    assert before["selection"]["selected_step"] == "select-event-option-4"
    assert after["event_selection"]["selected_native_option_index"] == 3
    assert after["event_instance_advanced_verified"] is True
    record = verify_source_reviewed_populist_refusal_result_v1(body)
    assert record["primitive_accepted"] is True
    assert record["business_success_inferred"] is False
    assert record["war_started_verified"] is False
    assert record["victory_verified"] is False
    assert record["replay_allowed"] is False


def test_wrong_native2_ack_is_retained_without_replay_or_credit(tmp_path):
    service, planned = execute_counterfactual(tmp_path, case(), native_option_index=2)
    with pytest.raises(ValueError, match="receipt/selection differs") as caught:
        service._execute_planned_turn(planned)
    assert service.calls == 1
    evidence = caught.value.unhandled_event_fallback_evidence
    assert evidence["event_instance_advanced_verified"] is False
    assert evidence["replay_allowed"] is False


@pytest.mark.parametrize("field", ("accepted", "postcondition", "old_instance", "index", "capture_index"))
def test_queue_record_rejects_unverified_or_stale_counterfactual(tmp_path, field):
    service, planned = execute_counterfactual(tmp_path, case())
    body = service._execute_planned_turn(planned)
    changed = copy.deepcopy(body)
    if field == "accepted":
        changed["result"]["accepted"] = False
    elif field == "postcondition":
        changed["result"]["event_selection"]["postcondition_verified"] = False
    elif field == "old_instance":
        changed["result"]["event_selection"]["old_event_instance_id"] += 1
    elif field == "index":
        changed["result"]["event_selection"]["selected_native_option_index"] = 2
    else:
        changed["plan"]["unhandled_event_fallback"]["selection"]["native_option_index"] = 2
    with pytest.raises(ValueError, match="receipt/selection differs"):
        verify_source_reviewed_populist_refusal_result_v1(changed)
