"""Synthetic portable source-review tests; no CK3 installation or MCP calls."""
import copy
import json
from pathlib import Path

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.vanilla_events import event_offline_analysis as offline
from xar_autoplayer.vanilla_events.unhandled_fallback import (
    plan_unhandled_event_fallback_v1, capture_unhandled_event_before_v1,
    capture_unhandled_event_after_v1,
)


@pytest.fixture
def reviewed_case(tmp_path, monkeypatch):
    # Entire Native-like context, frame, source and ACK are SYNTHETIC.
    context = {"schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "event_definition_key": "synthetic.1", "calculated_event_id": 10001,
        "runtime_stats_ordinal": 9, "current_event_instance_id": 17, "snapshot_revision": 7,
        "date_raw": 1000, "root_scope": {}, "saved_scopes": [], "readiness": {},
        "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1", "fixture": "SYNTHETIC"},
        "options": [{"rendered_index": 0, "native_option_index": 1, "shown": True, "enabled": True,
                     "resolved_name": "Synthetic first displayed"},
                    {"rendered_index": 1, "native_option_index": 0, "shown": True, "enabled": True,
                     "resolved_name": "Synthetic second displayed"}]}
    snapshot = {"snapshot_id": "synthetic:7", "revision": 3, "native_revision": 7,
        "date_raw": 1000, "paused": True, "map_ready": True, "episode_run_id": "synthetic-episode",
        "played_character": {"character_id": 101}, "active_event": {"instance_id": 17, "option_count": 2}}
    actions = {"select-event-option-1", "select-event-option-2"}
    plan = plan_unhandled_event_fallback_v1(snapshot=snapshot, event_context=context,
        event_summary=snapshot["active_event"], registry_decision={"status": "blocked", "unavailable_reason": "SYNTHETIC unsupported contract"},
        action_steps=actions)
    state, game = tmp_path / "state", tmp_path / "synthetic-game"
    source = game / "events/synthetic.txt"
    source.parent.mkdir(parents=True)
    source.write_text('synthetic.1 = {\n type = character_event\n'
        ' option = {\n name = synthetic.1.a\n add_piety = -5\n }\n'
        ' option = {\n name = {\n trigger = { always = yes }\n text = synthetic.1.b\n }\n'
        ' if = {\n limit = { exists = scope:doctor }\n scripted_treatment_effect = yes\n }\n }\n}\n', encoding="utf-8")
    monkeypatch.setattr(offline, "_index", lambda build: {"events": {}})
    ticket = capture_unhandled_event_before_v1(state, {"plan": plan, "snapshot_id": "synthetic:7", "revision": 3})
    after = capture_unhandled_event_after_v1(ticket, outcome={"result": {"accepted": True,
        "event_selection": {"status": "event_instance_advanced", "postcondition_verified": True,
            "old_event_instance_id": 17, "new_event_instance_id": None, "selected_native_option_index": 1}}})
    manifest = tmp_path / "batch.json"
    manifest.write_text(json.dumps({"completed_control_sequence": 100,
        "new_incidents": [{"incident_id": ticket["incident_id"], "event_definition_key": "synthetic.1",
            "before": ticket["before"]["path"], "before_sha256": ticket["before"]["sha256"],
            "after": after["after"]["path"], "after_sha256": after["after"]["sha256"]}]}), encoding="utf-8")
    return {"plan": plan, "context": context, "snapshot": snapshot, "actions": actions,
            "state": state, "game": game, "source": source, "manifest": manifest, "output": tmp_path / "review"}


def publish(case):
    return offline.analyze_event_batch(case["manifest"], case["game"], case["output"],
                                       publish_state_dir=case["state"])


def choose(case, monkeypatch):
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **k: copy.deepcopy(case["plan"]))
    return strategy.choose_one_life_turn([], snapshot=case["snapshot"], action_steps=case["actions"],
                                         pending_interaction_registry_state_dir=case["state"])


def test_first_unknown_then_same_process_ordinary_boundary_is_known(reviewed_case, monkeypatch):
    case = reviewed_case
    first = choose(case, monkeypatch)
    assert first["unhandled_event_fallback"]["offline_followup_required"] is True
    report = publish(case)
    second = choose(case, monkeypatch)
    assert second["selected_step"] == first["selected_step"] == "select-event-option-2"
    assert second["event_decision"]["status"] == "source_reviewed_known"
    assert second["event_decision"]["classification"] == "offline-source-reviewed-user-first-rendered-policy"
    assert second["active_event"]["source_knowledge_status"] == "source_reviewed_known"
    assert second["phase"] == "active_event_source_reviewed_first_rendered_option"
    assert "Source-reviewed" in second["reason"] and "Uncovered" not in second["reason"]
    capture = second["unhandled_event_fallback"]
    assert capture["registry_known"] is True and capture["offline_followup_required"] is False
    assert capture["original_registry_decision"]["status"] == "blocked"
    assert second["event_decision"]["registry_contract_accepted"] is False
    assert second["event_decision"]["material_effects_verified"] is False
    facts = json.loads(Path(report["entries"][0]["canonical_source_facts"]["path"]).read_bytes())
    assert len(facts["options"]) == 2 and "exists = scope:doctor" in facts["options"][1]["source_option"]
    assert facts["options"][1]["source_name_keys"] == ["synthetic.1.b"]
    assert facts["options"][1]["direct_effect_statements"][0]["effect"] == "scripted_treatment_effect"


@pytest.mark.parametrize("mutation", ["build", "calculated", "count", "option", "source", "facts"])
def test_changed_source_event_option_or_build_never_becomes_known(reviewed_case, mutation):
    case = reviewed_case
    report = publish(case)
    capture = copy.deepcopy(case["plan"]["unhandled_event_fallback"])
    assert offline.load_source_reviewed_event_v1(case["state"], capture)[0] is not None
    if mutation == "build":
        capture["window_context"]["provenance"]["backend_id"] = "ck3-1.20.0.3-native-event-window-v1"
    elif mutation == "calculated":
        capture["window_context"]["calculated_event_id"] += 1
    elif mutation == "count":
        capture["snapshot_option_count"] += 1
    elif mutation == "option":
        capture["window_context"]["options"][0]["native_option_index"] = 99
    elif mutation == "source":
        case["source"].write_bytes(case["source"].read_bytes() + b'\n# modified\n')
    else:
        Path(report["entries"][0]["canonical_source_facts"]["path"]).write_bytes(b'{}')
    known, audit = offline.load_source_reviewed_event_v1(case["state"], capture)
    assert known is None and audit["status"] == "unknown"


@pytest.mark.parametrize("failure", ["missing", "count", "non_event_ui"])
def test_unparseable_or_unbound_event_retains_unknown_and_no_registry_entry(reviewed_case, failure):
    case = reviewed_case
    if failure == "missing":
        case["source"].unlink()
    elif failure == "count":
        case["source"].write_text('synthetic.1 = {\n option = {\n name = synthetic.1.a\n }\n}\n', encoding="utf-8")
    else:
        batch = json.loads(case["manifest"].read_bytes())
        before = Path(batch["new_incidents"][0]["before"])
        data = json.loads(before.read_bytes())
        data["window_context"]["schema"] = "unidentified-ui-window"
        before.write_text(json.dumps(data), encoding="utf-8")
        import hashlib
        batch["new_incidents"][0]["before_sha256"] = hashlib.sha256(before.read_bytes()).hexdigest()
        case["manifest"].write_text(json.dumps(batch), encoding="utf-8")
    report = publish(case)
    assert report["entries"] == []
    assert report["unresolved"][0]["status"] == "unknown_unable_to_source_review"
    assert not list((case["state"] / "evidence/event-source-registry").glob("*.json"))


def test_source_known_disabled_first_never_chooses_second(reviewed_case):
    case = reviewed_case
    publish(case)
    context = copy.deepcopy(case["context"])
    context["options"][0]["enabled"] = False
    disabled = plan_unhandled_event_fallback_v1(snapshot=case["snapshot"], event_context=context,
        event_summary=case["snapshot"]["active_event"], registry_decision={"status": "unavailable"}, action_steps=case["actions"])
    result = offline.annotate_source_reviewed_event_plan_v1(disabled, case["state"])
    assert result["selected_step"] is None and result["event_decision"]["registry_known"] is True
    assert result["phase"] == "active_event_source_reviewed_first_rendered_disabled"
    assert "Source-reviewed" in result["reason"] and "disabled" in result["reason"]


def test_different_batch_output_reuses_immutable_canonical_facts(reviewed_case, tmp_path):
    case = reviewed_case
    first = publish(case)
    path = Path(first["entries"][0]["published"]["path"])
    original, stamp = path.read_bytes(), path.stat().st_mtime_ns
    second = offline.analyze_event_batch(case["manifest"], case["game"], tmp_path / "second-review",
                                         publish_state_dir=case["state"])
    assert second["entries"][0]["canonical_source_facts"] == first["entries"][0]["canonical_source_facts"]
    assert path.read_bytes() == original and path.stat().st_mtime_ns == stamp


def test_source_known_repeat_does_not_generate_another_analysis_todo(reviewed_case, tmp_path, monkeypatch):
    case = reviewed_case
    publish(case)
    known = choose(case, monkeypatch)
    ticket = capture_unhandled_event_before_v1(case["state"], {
        "plan": known, "snapshot_id": "synthetic:7", "revision": 3})
    after = capture_unhandled_event_after_v1(ticket, outcome={"result": {"accepted": True}})
    manifest = tmp_path / "known-next-batch.json"
    manifest.write_text(json.dumps({"completed_control_sequence": 101, "new_incidents": [{
        "incident_id": ticket["incident_id"], "event_definition_key": "synthetic.1",
        "before": ticket["before"]["path"], "before_sha256": ticket["before"]["sha256"],
        "after": after["after"]["path"], "after_sha256": after["after"]["sha256"],
        "registry_known": True, "offline_followup_required": False}]}), encoding="utf-8")
    def unnecessary_source_parse(*args, **kwargs):
        raise AssertionError("already source-known event must not be reanalysed")
    monkeypatch.setattr(offline, "_source", unnecessary_source_parse)
    result = offline.analyze_event_batch(manifest, case["game"], tmp_path / "known-next-review",
                                        publish_state_dir=case["state"])
    assert result["entries"] == [] and result["unresolved"] == []
    assert len(result["already_known"]) == 1
    assert result["already_known"][0]["offline_followup_required"] is False


def test_existing_dedicated_selection_unchanged(reviewed_case, monkeypatch):
    case = reviewed_case
    dedicated = {"policy": "one-life-turn-v1", "phase": "active_event_known_specialized",
                 "selected_step": "select-event-option-1", "reason": "Synthetic dedicated policy"}
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **k: dedicated)
    result = strategy.choose_one_life_turn([], snapshot=case["snapshot"], action_steps=case["actions"],
                                          pending_interaction_registry_state_dir=case["state"])
    assert result["selected_step"] == "select-event-option-1"
    assert "unhandled_event_fallback" not in result
