"""Cold-ID migration with synthetic source bytes; no stock/live execution credit."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from xar_autoplayer.vanilla_events import event_offline_analysis as offline
from xar_autoplayer.vanilla_events import populist1001_known_refusal_v1 as policy


FIXTURE = Path(__file__).parent / "fixtures/p43_populist_actual193_projection.json"


def prepare(tmp_path, monkeypatch, event_key="faction_demand.1001"):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    plan = fixture["plan"]
    capture = plan["unhandled_event_fallback"]
    plan["phase"] = "active_event_unhandled_first_rendered_option"
    capture.update(event_definition_key=event_key, registry_known=False,
                   source_knowledge={"status": "unknown"})
    capture["window_context"]["event_definition_key"] = event_key
    plan["event_decision"]["status"] = "unhandled"
    source = tmp_path / "game/events/synthetic.txt"
    source.parent.mkdir(parents=True)
    source.write_text(event_key + " = {\n type = letter_event\n" + "".join(
        f" option = {{\n name = synthetic.{index}\n }}\n" for index in range(4)) + "}\n",
        encoding="utf-8")
    monkeypatch.setattr(offline, "_index", lambda build: {"events": {event_key: {
        "definition": {"relative_path": "events/synthetic.txt",
                       "file_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}}}})
    before = tmp_path / "before.json"
    before.write_text(json.dumps({**capture, "incident_id": "synthetic-cold-populist",
                                 "dispatch_attempted": False}), encoding="utf-8")
    batch = tmp_path / "batch.json"
    batch.write_text(json.dumps({"completed_control_sequence": 1, "new_incidents": [{
        "event_definition_key": event_key, "incident_id": "synthetic-cold-populist",
        "before": str(before), "before_sha256": hashlib.sha256(before.read_bytes()).hexdigest()}]}), encoding="utf-8")
    state = tmp_path / "state"
    report = offline.analyze_event_batch(batch, tmp_path / "game", tmp_path / "review",
                                         publish_state_dir=state)
    assert not report["unresolved"]
    entry_path = Path(report["entries"][0]["published"]["path"])
    original_entry = entry_path.read_bytes()
    entry = json.loads(original_entry)
    # The synthetic source has its own explicit approved hashes. Production
    # anchors remain the reviewed stock hashes; the live-free external replay
    # separately checks those actual stock bytes and retained facts.
    monkeypatch.setattr(policy, "SOURCE_SHA256", entry["binding"]["source_sha256"])
    monkeypatch.setattr(policy, "OPTION_CATALOGUE_SHA256", entry["binding"]["option_catalogue_sha256"])
    old_id = capture["window_context"]["calculated_event_id"]
    capture["window_context"]["calculated_event_id"] = old_id + 10000
    return fixture, state, source, entry_path, original_entry


def recommend(fixture, state):
    plan = offline.annotate_source_reviewed_event_plan_v1(fixture["plan"], state)
    return policy.choose_source_reviewed_populist_refusal_v1(
        plan, snapshot=fixture["snapshot"],
        action_steps=("select-event-option-3", "select-event-option-4"))


def test_production_loader_binds_changed_cold_id_then_policy_refuses(tmp_path, monkeypatch):
    fixture, state, _, entry_path, original_entry = prepare(tmp_path, monkeypatch)
    result = recommend(fixture, state)
    audit = result["unhandled_event_fallback"]["source_knowledge"]
    assert result["selected_step"] == "select-event-option-4"
    assert audit["binding_mode"] == policy.SOURCE_REBIND_MODE
    assert audit["fresh_binding"]["calculated_event_id"] == 3581001
    assert audit["adapted_from"]["calculated_event_id"] == 3571001
    assert audit["fresh_binding_fingerprint"] != audit["fingerprint"]
    assert result["event_decision"]["status"] == "source_reviewed_known"
    assert result["faction_demand_source_outcome"]["title_retention_verified"] is False
    assert entry_path.read_bytes() == original_entry


@pytest.mark.parametrize("mutation", ["source", "catalogue", "layout", "roles", "scope_payload"])
def test_changed_source_layout_or_roles_do_not_gain_known(tmp_path, monkeypatch, mutation):
    fixture, state, source, _, _ = prepare(tmp_path, monkeypatch)
    capture = fixture["plan"]["unhandled_event_fallback"]
    context = capture["window_context"]
    if mutation == "source":
        source.write_bytes(source.read_bytes() + b"\n# changed\n")
    elif mutation == "catalogue":
        monkeypatch.setattr(policy, "OPTION_CATALOGUE_SHA256", "0" * 64)
    elif mutation == "layout":
        context["options"][0]["rendered_index"] = 1
        context["options"][1]["rendered_index"] = 0
        capture["selection"].update(native_option_index=3, option_number=4,
                                    selected_step="select-event-option-4")
        fixture["plan"]["selected_step"] = "select-event-option-4"
    else:
        name = "faction_target" if mutation == "roles" else "peasant_county"
        row = next(row for row in context["saved_scopes"] if row["name"] == name)
        if mutation == "roles":
            row["scope"]["typed_identity"]["character_id"] += 1
        else:
            row["scope"]["typed_identity"] = {"status": "unavailable", "reason": "SYNTHETIC"}
    known, audit = offline.load_source_reviewed_event_v1(state, capture)
    assert known is None and audit["status"] == "unknown"
    result = recommend(fixture, state)
    assert result["phase"] != "active_event_source_reviewed_populist_refusal"


def test_other_reviewed_letter_still_cannot_rebind(tmp_path, monkeypatch):
    fixture, state, _, _, _ = prepare(tmp_path, monkeypatch, event_key="synthetic_letter.1")
    known, audit = offline.load_source_reviewed_event_v1(
        state, fixture["plan"]["unhandled_event_fallback"])
    assert known is None and audit["status"] == "unknown"


def test_enabled_restore_hook_intercepts_unresolved_target_before_native(tmp_path, monkeypatch):
    from xar_autoplayer.bridge.service import GameplayBridgeService

    fixture, state, source, _, _ = prepare(tmp_path, monkeypatch)
    source.write_bytes(source.read_bytes() + b"\n# changed\n")
    plan = recommend(fixture, state)
    planned = {"plan": plan, "snapshot_id": fixture["snapshot"]["snapshot_id"],
               "revision": fixture["snapshot"]["revision"]}
    service = object.__new__(GameplayBridgeService)
    result = service._execute_planned_turn_without_unhandled_capture(
        planned, before_submit=lambda value: policy.intercept_unresolved_populist_restore_target_v1(
            value, enabled=True))
    assert result["status"] == "intercepted"
    assert result["interception"]["native_dispatch_allowed"] is False
    assert result["interception"]["offline_followup_required"] is True
    # There is no driver on this service. Reaching a native dispatcher would fail.
    assert not hasattr(service, "driver")


def test_restore_hook_allows_reviewed_refusal_and_is_opt_in(tmp_path, monkeypatch):
    fixture, state, _, _, _ = prepare(tmp_path, monkeypatch)
    plan = recommend(fixture, state)
    planned = {"plan": plan, "selected_step": plan["selected_step"]}
    assert policy.intercept_unresolved_populist_restore_target_v1(planned, enabled=True) is None
    unknown = {"plan": fixture["plan"], "selected_step": "select-event-option-3"}
    assert policy.intercept_unresolved_populist_restore_target_v1(unknown) is None
    unrelated = deepcopy(unknown)
    unrelated["plan"]["unhandled_event_fallback"]["event_definition_key"] = "synthetic_letter.1"
    assert policy.intercept_unresolved_populist_restore_target_v1(unrelated, enabled=True) is None
