"""Portable synthetic event continuation fixtures; no Game, MCP or desktop calls."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.vanilla_events import unhandled_fallback


QUERY = QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP


def _scope(character_id=None):
    return {
        "status": "available",
        "raw_type_index": 4 if character_id is not None else 1,
        "type_key": "character" if character_id is not None else "flag",
        "subtype": 0,
        "typed_identity": (
            {"status": "available", "kind": "character", "character_id": character_id}
            if character_id is not None
            else {"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"}
        ),
    }


def _option(rendered, native):
    return {
        "rendered_index": rendered,
        "native_option_index": native,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "resolved_name": f"Synthetic displayed choice {rendered + 1}",
        "unavailable_reason": "",
        "effect_indicators": {
            "status": "available",
            "coverage": "played-character-event-icon-indicators-1.20.0.4-v1",
            "complete_effect_set": False,
            "rows": [],
        },
        "effect_preview": {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        },
        "resource_deltas": {"status": "unavailable"},
        "relationship_deltas": {"status": "unavailable"},
    }


@pytest.fixture
def event_case():
    """Small invented DTOs with the production exact-build envelope shape."""
    snapshot = {
        "snapshot_id": "synthetic-event-frame",
        "revision": 3,
        "native_revision": 7,
        "date_raw": 53_000_016,
        "episode_run_id": "synthetic-event-episode",
        "diagnostics": {"connection_generation": 2, "bridge_pid": 123},
        "backend_id": "native-headless",
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 99, "alive": True},
        "active_event": {"instance_id": 41, "option_count": 7},
        "active_wars": [],
    }
    context = {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": snapshot["native_revision"],
        "date_raw": snapshot["date_raw"],
        "current_event_instance_id": 41,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "portable_unhandled_fixture.1",
        "calculated_event_id": 123_001,
        "runtime_stats_ordinal": 1,
        "root_scope": _scope(99),
        "saved_scopes": [],
        # Native zero is displayed second; selecting it would violate the policy.
        "options": [_option(0, 6), _option(1, 0)],
        "readiness": {
            "event_definition_identity_ready": True,
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "option_presentation_ready": True,
            "effect_indicators_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        },
        "provenance": {
            "root": "module+0x5C6A520->+0x10",
            "idler_vtable_rva": "0x44BC418",
            "manager_offset": "+0x28",
            "backend_id": "ck3-1.20.0.4-native-event-window-v1",
        },
    }
    actions = {QUERY, *(f"select-event-option-{number}" for number in range(1, 8))}
    return snapshot, context, actions


def _choose(case):
    snapshot, context, actions = case
    history = [{
        "command": QUERY,
        "ok": True,
        "result": {
            "step": QUERY,
            "accepted": True,
            "status": context["status"],
            "snapshot_revision": context["snapshot_revision"],
            "date_raw": context["date_raw"],
            "current_event_instance_id": context["current_event_instance_id"],
            "current_event_window_context": deepcopy(context),
            "queried_snapshot_id": snapshot["snapshot_id"],
            "queried_revision": snapshot["revision"],
            "queried_native_revision": snapshot["native_revision"],
        },
    }]
    return strategy.choose_one_life_turn(history, snapshot=snapshot, action_steps=actions)


def _planned(case):
    snapshot, _, _ = case
    return {
        "plan": _choose(case),
        "snapshot_id": snapshot["snapshot_id"],
        "revision": snapshot["revision"],
    }


def _service(case, state_dir, execute):
    snapshot, _, actions = case
    service = GameplayBridgeService.__new__(GameplayBridgeService)
    service.driver = SimpleNamespace(
        state_dir=state_dir, take_snapshot=lambda: deepcopy(snapshot),
    )
    service.capabilities = lambda: {"action_steps": sorted(actions)}
    # Exercise the real Service capture, dispatch and select_event_option methods.
    # Only the final native transport boundary is synthetic.
    service.execute_step = execute
    return service


def _read_receipt(receipt):
    payload = Path(receipt["path"]).read_bytes()
    assert len(payload) == receipt["bytes"]
    assert hashlib.sha256(payload).hexdigest() == receipt["sha256"]
    return json.loads(payload)


def test_unknown_event_selects_first_displayed_native_index_and_preserves_card(event_case):
    plan = _choose(event_case)

    assert plan["selected_step"] == "select-event-option-7"
    assert plan["phase"] == "active_event_unhandled_first_rendered_option"
    capture = plan["unhandled_event_fallback"]
    assert capture["selection"]["rendered_index"] == 0
    assert capture["selection"]["native_option_index"] == 6
    assert capture["window_context"]["options"] == event_case[1]["options"]
    assert capture["offline_followup_required"] is True
    assert capture["semantic_optimal"] is False


@pytest.mark.parametrize("phase", [
    "active_event_raiktor_contract_blocked",
    "active_event_registry_material_observation_blocked",
    "active_event_unknown_new_consumer_blocked",
])
def test_common_wrapper_continues_blocked_event_consumers(event_case, monkeypatch, phase):
    original = {
        "policy": "one-life-turn-v1", "phase": phase, "selected_step": None,
        "reason": "Synthetic consumer has no decision",
        "active_event": {"instance_id": 41},
    }
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **kw: deepcopy(original))

    plan = _choose(event_case)

    assert plan["selected_step"] == "select-event-option-7"
    assert plan["unhandled_event_fallback"]["original_registry_decision"]["original_phase"] == phase


def test_common_wrapper_preserves_an_existing_selected_strategy(event_case, monkeypatch):
    original = {
        "policy": "one-life-turn-v1", "phase": "active_event_registry_choice",
        "selected_step": "select-event-option-1", "active_event": {"instance_id": 41},
    }
    monkeypatch.setattr(strategy, "_choose_one_life_turn_core", lambda *a, **kw: deepcopy(original))

    plan = _choose(event_case)

    assert plan["selected_step"] == "select-event-option-1"
    assert plan["phase"] == original["phase"]
    assert "unhandled_event_fallback" not in plan


def test_registered_physician_strategy_still_uses_its_dedicated_choice(event_case):
    _, context, _ = event_case
    context["event_definition_key"] = "health.1001"
    context["options"] = [_option(rendered, native) for rendered, native in enumerate((3, 4, 6))]
    context["saved_scopes"] = [
        {"name": "physician", "name_identifier": 1, "scope": _scope(100)},
        {"name": "sick_character", "name_identifier": 2, "scope": _scope(99)},
        {"name": "disease_type", "name_identifier": 3, "scope": _scope()},
    ]

    plan = _choose(event_case)

    assert plan["phase"] == "active_event_registry_choice"
    assert plan["selected_step"] == "select-event-option-4"
    assert "unhandled_event_fallback" not in plan


def test_service_writes_complete_before_evidence_before_dispatch_and_records_postcondition(event_case, tmp_path):
    planned = _planned(event_case)
    directory = tmp_path / "evidence" / "unhandled-events"
    calls = []
    selection = {
        "status": "event_instance_advanced", "postcondition_verified": True,
        "old_event_instance_id": 41, "new_event_instance_id": None,
        "selected_option_number": 7, "selected_native_option_index": 6,
    }

    def execute(step, *, expected_revision):
        before_files = list(directory.glob("*.before.json"))
        assert len(before_files) == 1
        assert not list(directory.glob("*.after.json"))
        before = json.loads(before_files[0].read_bytes())
        assert before["stage"] == "before_submission"
        assert before["dispatch_attempted"] is False
        assert before["window_context"]["options"] == event_case[1]["options"]
        assert before["selection"]["selected_step"] == step
        assert before["binding"]["connection_generation"] == 2
        assert before["binding"]["bridge_pid"] == 123
        calls.append((step, expected_revision))
        return {"step": step, "accepted": True, "progress_status": "postcondition", "event_selection": selection}

    outcome = _service(event_case, tmp_path, execute)._execute_planned_turn(planned)

    assert calls == [("select-event-option-7", 3)]
    receipt = outcome["unhandled_event_fallback_evidence"]
    before, after = _read_receipt(receipt["before"]), _read_receipt(receipt["after"])
    assert before["incident_id"] == after["incident_id"] == receipt["incident_id"]
    assert after["before"] == receipt["before"]
    assert after["event_selection"] == selection
    assert after["command_acknowledged"] is True
    assert after["event_instance_advanced_verified"] is True
    assert after["replay_allowed"] is False


def test_ack_alone_is_retained_without_claiming_event_advancement(event_case, tmp_path):
    ticket = unhandled_fallback.capture_unhandled_event_before_v1(tmp_path, _planned(event_case))

    receipt = unhandled_fallback.capture_unhandled_event_after_v1(
        ticket, outcome={"status": "executed", "result": {"accepted": True}},
    )

    after = _read_receipt(receipt["after"])
    assert after["command_acknowledged"] is True
    assert after["event_instance_advanced_verified"] is False
    assert after["replay_allowed"] is False


def test_unknown_dispatch_outcome_retains_original_error_without_replay(event_case, tmp_path):
    error = BridgeUnavailableError("Synthetic unknown native submission outcome")
    calls = []

    def execute(step, *, expected_revision):
        calls.append((step, expected_revision))
        raise error

    with pytest.raises(BridgeUnavailableError) as caught:
        _service(event_case, tmp_path, execute)._execute_planned_turn(_planned(event_case))

    assert caught.value is error
    assert calls == [("select-event-option-7", 3)]
    evidence = caught.value.unhandled_event_fallback_evidence
    after = _read_receipt(evidence["after"])
    assert after["error"] == {"type": "BridgeUnavailableError", "message": str(error)}
    assert after["command_acknowledged"] is False
    assert after["event_instance_advanced_verified"] is False
    assert evidence["replay_allowed"] is False


def test_after_capture_error_does_not_repeat_an_acknowledged_submission(event_case, tmp_path, monkeypatch):
    calls = []

    def execute(step, *, expected_revision):
        calls.append((step, expected_revision))
        return {"step": step, "accepted": True}

    def fail_after(*args, **kwargs):
        raise OSError("Synthetic after receipt write failure")

    monkeypatch.setattr(unhandled_fallback, "capture_unhandled_event_after_v1", fail_after)
    outcome = _service(event_case, tmp_path, execute)._execute_planned_turn(_planned(event_case))

    assert calls == [("select-event-option-7", 3)]
    assert outcome["result"]["accepted"] is True
    evidence = outcome["unhandled_event_fallback_evidence"]
    assert _read_receipt(evidence["before"])["stage"] == "before_submission"
    assert evidence["after_capture_error"] == "Synthetic after receipt write failure"
    assert evidence["replay_allowed"] is False


def test_before_capture_failure_prevents_dispatch(event_case):
    calls = []

    def execute(step, *, expected_revision):
        calls.append((step, expected_revision))
        raise AssertionError("A submission without durable before evidence must not happen")

    with pytest.raises(ValueError, match="managed state directory"):
        _service(event_case, None, execute)._execute_planned_turn(_planned(event_case))

    assert calls == []
