"""Synthetic frames/IDs/ACKs only; stock source review is not live qualification."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.vanilla_events import independence0001_known_refusal_v1 as policy
from xar_autoplayer.vanilla_events.event_offline_analysis import _blocks, _fingerprint, _native_binding
from xar_autoplayer.vanilla_events.unhandled_fallback import plan_unhandled_event_fallback_v1


def scope(kind, field, value):
    return {"status": "available", "type_key": kind,
            "typed_identity": {"status": "available", "kind": kind, field: value}}


def case(*, co_emperor=False):
    # These invented values model the production DTO; none is a CK3 observation.
    snapshot = {"snapshot_id": "native:7", "revision": 3, "native_revision": 7,
        "date_raw": 1000, "paused": True, "map_ready": True, "episode_run_id": "SYNTHETIC",
        "diagnostics": {"bridge_pid": 123, "connection_generation": 2},
        "played_character": {"character_id": 101, "alive": True},
        "active_event": {"instance_id": 17, "option_count": 3}}
    options = [{"rendered_index": 0, "native_option_index": 0, "shown": True,
                "enabled": True, "resolved_name": "SYNTHETIC accept"}]
    if co_emperor:
        options.append({"rendered_index": 1, "native_option_index": 1, "shown": True,
                        "enabled": False, "resolved_name": "SYNTHETIC counteroffer"})
    options.append({"rendered_index": len(options), "native_option_index": 2, "shown": True,
                    "enabled": True, "resolved_name": "SYNTHETIC refuse"})
    context = {"schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "window_match_count": 1,
        "event_definition_key": policy.EVENT_KEY, "calculated_event_id": 10001,
        "current_event_instance_id": 17, "snapshot_revision": 7, "date_raw": 1000,
        "root_scope": scope("character", "character_id", 101),
        "saved_scopes": [
            {"name": "faction", "scope": scope("faction", "faction_id", 201)},
            {"name": "faction_target", "scope": scope("character", "character_id", 101)},
            {"name": "faction_leader", "scope": scope("character", "character_id", 301)}],
        "readiness": {"event_definition_identity_ready": True, "root_scope_ready": True,
            "saved_scopes_ready": True, "option_presentation_ready": True},
        "provenance": {"backend_id": policy.BACKEND, "fixture": "SYNTHETIC"}, "options": options}
    steps = {"select-event-option-1", "select-event-option-2", "select-event-option-3"}
    plan = plan_unhandled_event_fallback_v1(snapshot=snapshot, event_context=context,
        event_summary=snapshot["active_event"], registry_decision={"status": "blocked",
        "unavailable_reason": "SYNTHETIC no live timeline contract"}, action_steps=steps)
    plan["unhandled_event_fallback"]["source_knowledge"] = {"status": "unknown", "rejected_entries": []}
    return {"snapshot": snapshot, "plan": plan, "steps": steps}


def choose(c):
    return policy.choose_source_reviewed_independence_refusal_v1(
        c["plan"], snapshot=c["snapshot"], action_steps=c["steps"])


def test_review_retains_complete_source_options_and_transitive_war_release_effects():
    root = Path(__file__).resolve().parents[3]
    proof = json.loads((root / policy.REVIEW["complete_source_options_and_effects"]).read_text(encoding="utf-8"))
    assert proof["source_pins"][0]["sha256"] == policy.SOURCE_SHA256
    assert _fingerprint(proof["source_option_catalogue"]) == policy.OPTION_CATALOGUE_SHA256
    definitions = {d["definition_key"]: d for d in proof["definitions"]}
    definition = definitions[policy.EVENT_KEY]
    assert definition["sha256"] == policy.REVIEW["definition_block_sha256"]
    options = _blocks(definition["complete_body"], "option")
    assert options == [d["source_option"] for d in proof["source_option_catalogue"]]
    assert [d["source_name_keys"] for d in proof["source_option_catalogue"]] == [
        ["FACTION_DEMAND_ACCEPT"], ["FACTION_DEMAND_BRIBE_CO_EMPEROR"], ["FACTION_DEMAND_REFUSE"]]
    assert "add_claim_on_loss = no" in options[0]
    assert "every_faction_member" in options[0] and "change_liege_or_become_independent" in options[0]
    assert "trigger_event = faction_demand.0003" in options[2]
    assert "faction_start_war = {}" in definitions["faction_demand.0003"]["complete_body"]
    helper = definitions["change_liege_or_become_independent"]["complete_body"]
    assert "becomes_independent" in helper and "liege.liege" in helper
    assert "calculated_event_id" not in policy.REVIEW
    assert policy.REVIEW["new_live_evidence"] is False and policy.REVIEW["observations"] == []


@pytest.mark.parametrize("co_emperor", [False, True])
def test_public_ordinary_hook_prelearns_source_before_any_accept_incident(monkeypatch, co_emperor):
    c = case(co_emperor=co_emperor)
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **k: deepcopy(c["plan"]))
    result = strategy.choose_one_life_turn([], snapshot=c["snapshot"], action_steps=c["steps"])
    assert result["phase"] == "active_event_source_reviewed_independence_refusal"
    assert result["selected_step"] == "select-event-option-3"
    capture = result["unhandled_event_fallback"]
    assert capture["selection"]["native_option_index"] == 2
    assert capture["selection"]["rendered_index"] == (2 if co_emperor else 1)
    assert capture["source_knowledge"]["status"] == "independence0001_source_reviewed_current_binding"
    assert capture["source_knowledge"]["binding"]["calculated_event_id"] == 10001
    assert capture["source_knowledge"]["loaded_definition_bytes_verified"] is False
    assert result["event_decision"]["material_effects_verified"] is False
    assert result["faction_demand_source_outcome"]["exact_lost_titles"] is None
    assert all(result["faction_demand_source_outcome"][key] is False for key in (
        "war_started_verified", "victory_verified", "title_retention_verified"))
    assert c["plan"]["selected_step"] == "select-event-option-1"


def test_already_validated_exact_source_entry_uses_its_observed_definition():
    c = case()
    capture = c["plan"]["unhandled_event_fallback"]
    current = _native_binding(capture)
    current.update(source_sha256=policy.SOURCE_SHA256, option_catalogue_sha256=policy.OPTION_CATALOGUE_SHA256)
    capture.update(registry_known=True, source_knowledge={"status": "offline-source-reviewed",
        "binding_mode": "exact", "fingerprint": _fingerprint(current)})
    c["plan"]["phase"] = "active_event_source_reviewed_first_rendered_option"
    c["plan"]["event_decision"]["status"] = "source_reviewed_known"
    assert choose(c)["selected_step"] == "select-event-option-3"


@pytest.mark.parametrize("change", ["unknown_key", "unreviewed", "source", "catalogue",
    "rejected_exact", "missing_refuse", "disabled_refuse", "unadvertised", "date", "pid", "target"])
def test_unknown_changed_source_or_illegal_current_refusal_keeps_first_displayed(monkeypatch, change):
    c = case()
    capture = c["plan"]["unhandled_event_fallback"]
    context = capture["window_context"]
    if change == "unknown_key":
        capture["event_definition_key"] = context["event_definition_key"] = "synthetic.1"
    elif change == "unreviewed":
        monkeypatch.setitem(policy.REVIEW, "readiness", "unreviewed")
    elif change == "source":
        capture["source_knowledge"] = {"status": "offline-source-reviewed", "binding_mode": "exact",
            "fingerprint": "0" * 64}
    elif change == "catalogue":
        monkeypatch.setitem(policy.REVIEW, "option_catalogue_sha256", "0" * 64)
    elif change == "rejected_exact":
        capture["source_knowledge"]["rejected_entries"] = [{"reason": "source changed"}]
    elif change == "missing_refuse":
        context["options"].pop()
    elif change == "disabled_refuse":
        context["options"][-1]["enabled"] = False
    elif change == "unadvertised":
        c["steps"].remove("select-event-option-3")
    elif change == "date":
        c["snapshot"]["date_raw"] += 1
    elif change == "pid":
        c["snapshot"]["diagnostics"]["bridge_pid"] += 1
    else:
        context["saved_scopes"][1]["scope"]["typed_identity"]["character_id"] += 1
    result = choose(c)
    assert result is c["plan"]
    assert result["phase"] == "active_event_unhandled_first_rendered_option"
    assert result["selected_step"] == "select-event-option-1"


class _SyntheticReceiptService(GameplayBridgeService):
    def _strategy_state_dir(self):
        return self.test_state_dir

    def _execute_planned_turn_without_unhandled_capture(self, planned, *, before_submit=None):
        self.calls += 1
        return {"status": "executed", "plan": planned["plan"],
            "selected_step": planned["plan"]["selected_step"],
            "result": {"accepted": True, "event_selection": {
                "status": "event_instance_advanced", "postcondition_verified": True,
                "old_event_instance_id": 17, "new_event_instance_id": None,
                "selected_native_option_index": self.selected_native}}}


@pytest.mark.parametrize("selected_native,advanced", [(2, True), (0, False)])
def test_existing_generic_capture_binds_refusal_and_never_replays_ack(tmp_path, selected_native, advanced):
    c = case()
    result = choose(c)
    service = object.__new__(_SyntheticReceiptService)
    service.test_state_dir, service.calls, service.selected_native = tmp_path, 0, selected_native
    body = service._execute_planned_turn({"plan": result,
        "snapshot_id": c["snapshot"]["snapshot_id"], "revision": c["snapshot"]["revision"]})
    assert service.calls == 1
    evidence = body["unhandled_event_fallback_evidence"]
    before = json.loads(Path(evidence["before"]["path"]).read_text(encoding="utf-8"))
    assert before["selection"]["native_option_index"] == 2
    assert before["selection"]["rendered_index"] == 1
    assert evidence["command_acknowledged"] is True
    assert evidence["event_instance_advanced_verified"] is advanced
    assert evidence["replay_allowed"] is False
    assert result["event_decision"]["material_effects_verified"] is False
