"""Portable Native-choice policy tests; actual715 fixture is clearly labeled.

All generic windows and interaction replies are synthetic, with no Native
transport, game installation, desktop or external run-path dependency.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from xar_autoplayer.mandatory_choice_policy_v1 import (
    select_existing_native_choice_v1, select_unknown_mandatory_choice_v1,
)
from xar_autoplayer import pending_interaction_fallback as interactions
from xar_autoplayer.vanilla_events import unhandled_fallback as events
from test_pending_interaction_left_fallback import fixture as interaction_case


def _choice(identity, top=10, left=20, **extra):
    return {"choice_id": identity, "visible": True, "enabled": True, "is_choice": True,
            "label": "Synthetic unfamiliar wording", "action_token": "synthetic-token-" + str(identity),
            "bounds": {"top": top, "left": left, "width": 80, "height": 24}, **extra}


def _window(choices):
    return {"window_id": "synthetic-native-window", "window_type": "generic",
            "blocking_proof": {"kind": "exclusive_modal_blocks_input", "verified": True,
                               "source": "SYNTHETIC-NATIVE-EXCLUSIVE-RECEIVER"},
            "choices_complete": True,
            "frame_binding": {"game_pid": 1, "native_revision": 8, "epoch": 9},
            "choices": choices}


@pytest.mark.parametrize("choices,expected", [
    ([_choice("right", 10, 100), _choice("left", 10, 20)], "left"),
    ([_choice("bottom", 60, 20), _choice("top", 10, 20)], "top"),
    ([_choice("bottom-left", 60, 0), _choice("top-right", 10, 100), _choice("top-left", 10, 20)], "top-left"),
    ([_choice("disabled", 0, 0, enabled=False), _choice("enabled", 10, 20)], "enabled"),
    ([_choice("close-x", 0, 0, role="close_x"), _choice("hidden", 0, 0, visible=False),
      _choice("decoration", 0, 0, is_choice=False), _choice("button", 20, 20)], "button"),
])
def test_native_geometry_order_filters_disabled_invisible_and_nonchoices_without_mutation(choices, expected):
    window = _window(choices)
    original = deepcopy(window)
    result = select_unknown_mandatory_choice_v1(window, expected_frame=window["frame_binding"])
    assert result["status"] == "recommended"
    assert result["selected_choice_id"] == expected
    assert result["evidence"]["choices"] == choices
    assert window == original
    assert result["material_effects_verified"] is False


def test_single_enabled_unknown_label_requires_no_geometry():
    choice = _choice("only")
    choice.pop("bounds")
    result = select_unknown_mandatory_choice_v1(_window([choice]))
    assert result["selected_choice_id"] == "only"
    assert result["evidence"]["sort_order"] == "single_visible_enabled_native_choice_no_geometry_needed"


def test_native_identity_exact_duplicates_removed_conflicts_rejected():
    choice = _choice("same")
    result = select_unknown_mandatory_choice_v1(_window([choice, deepcopy(choice)]))
    assert result["selected_choice_id"] == "same"
    assert len(result["evidence"]["duplicates_removed"]) == 1
    conflict = {**choice, "action_token": "different-synthetic-token"}
    assert select_unknown_mandatory_choice_v1(_window([choice, conflict]))["status"] == "mechanism_unavailable"


@pytest.mark.parametrize("change,expected_status", [
    ({"blocking_proof": None}, "not_mandatory"),
    ({"choices_complete": False}, "mechanism_unavailable"),
    ({"choices": [{**_choice("a"), "action_token": None}]}, "mechanism_unavailable"),
    ({"choices": [{**_choice("a"), "bounds": None}, {**_choice("b"), "bounds": None}]}, "mechanism_unavailable"),
])
def test_missing_native_mechanism_is_explicit_and_never_invents_choice(change, expected_status):
    result = select_unknown_mandatory_choice_v1({**_window([_choice("a")]), **change})
    assert result["status"] == expected_status
    assert result["selected_choice_id"] is None


def test_stale_native_frame_cannot_be_consumed():
    window = _window([_choice("a")])
    frame = {**window["frame_binding"], "native_revision": 9}
    assert select_unknown_mandatory_choice_v1(window, expected_frame=frame)["status"] == "stale_frame"


def test_existing_event_native_presentation_order_maps_native6_to_public7_without_geometry():
    choices = [{**_choice(6), "bounds": None, "rendered_index": 0, "native_index": 6},
               {**_choice(0), "bounds": None, "rendered_index": 1, "native_index": 0}]
    window = {**_window(choices), "window_type": "event", "blocking_proof": None,
              "presentation_order_proof": {"kind": "native_event_rendered_order"}}
    result = select_existing_native_choice_v1(window)
    assert result["native_index"] == 6 and result["public_option_number"] == 7
    assert result["evidence"]["blocking_proof"] is None
    assert select_unknown_mandatory_choice_v1(_window(choices))["status"] == "mechanism_unavailable"


def _actual715():
    path = Path(__file__).parent / "fixtures/unhandled_event_actual715.json"
    return json.loads(path.read_bytes())


def _event_plan(fixture):
    return events.plan_unhandled_event_fallback_v1(snapshot=fixture["snapshot"], event_context=fixture["event_context"],
        event_summary=fixture["event_summary"], registry_decision=fixture["registry_decision"],
        action_steps={"select-event-option-" + str(i) for i in range(1, 8)})


def test_actual715_disabled_first_two_selects_native2_public3_and_keeps_all_source_options():
    fixture = _actual715()
    assert fixture["source_response_sha256"] == "7df4f3dcd6d9bd48347546f6c97ca3c7610822ca86e8c418391f8c1412758710"
    original = deepcopy(fixture)
    result = _event_plan(fixture)
    assert result["selected_step"] == "select-event-option-3"
    assert result["event_decision"]["selected_native_option_index"] == 2
    assert result["event_decision"]["selected_option_number"] == 3
    capture = result["unhandled_event_fallback"]
    assert capture["window_context"] == fixture["event_context"]
    assert capture["selection"]["excluded_disabled_rendered_indices"] == [0, 1]
    assert fixture == original


def test_event_single_native6_all_disabled_and_stale_original_guards():
    fixture = _actual715()
    fixture["snapshot"]["active_event"]["option_count"] = 7
    fixture["event_context"]["options"] = [{"native_option_index": 6, "rendered_index": 0,
                                              "shown": True, "enabled": True}]
    assert _event_plan(fixture)["selected_step"] == "select-event-option-7"
    fixture["event_context"]["options"][0]["enabled"] = False
    assert _event_plan(fixture)["selected_step"] is None
    fixture["event_context"]["snapshot_revision"] += 1
    assert _event_plan(fixture) is None


def _unknown_interaction(case):
    snapshot, context, _ = case
    context["definition"].update(canonical_key="synthetic_unknown_interaction", deterministic_key_hash=12)
    return snapshot, context


def _interaction_plan(snapshot, context):
    return interactions.plan_pending_interaction_left_reply_v1(snapshot=snapshot, context=context,
        original_plan={"phase": "synthetic_unknown"}, action_steps={
            "reject-pending-character-interaction", "accept-pending-character-interaction"})


def test_unknown_interaction_disabled_left_uses_enabled_right_with_full_native_legality(interaction_case):
    snapshot, context = _unknown_interaction(interaction_case)
    context["legality"]["reject"]["allowed"] = False
    result = _interaction_plan(snapshot, context)
    assert result["selected_step"] == "accept-pending-character-interaction"
    assert result["decision"]["display_position"] == "right"
    capture = result["unhandled_interaction_fallback"]
    assert capture["context"] == context
    assert capture["presented_choice_policy"]["evidence"]["blocking_proof"] is None
    assert capture["offline_followup_required"] is True


@pytest.mark.parametrize("mutation,verified", [(None, True), ("ACK_only", False), ("wrong_status", False),
                                                ("wrong_ID", False), ("same_pending", False), ("unpaused", False)])
def test_accept_receipt_requires_actual_original_pending_advance_not_ACK_or_material_claim(interaction_case, tmp_path, mutation, verified):
    snapshot, context = _unknown_interaction(interaction_case)
    context["legality"]["reject"]["allowed"] = False
    plan = _interaction_plan(snapshot, context)
    ticket = interactions.capture_pending_interaction_before_v1(tmp_path, {
        "plan": plan, "snapshot_id": snapshot["snapshot_id"], "revision": snapshot["revision"]})
    before = json.loads(Path(ticket["before"]["path"]).read_bytes())
    assert before["dispatch_attempted"] is False and before["selection"]["action"] == "accept"
    result = {"accepted": True, "paused": True, "interaction_result": {
        "status": "accepted", "instance_id": ticket["pending_interaction_id"]},
        "remaining_pending_character_interaction": None}
    if mutation == "ACK_only":
        result = {"accepted": True}
    elif mutation == "wrong_status":
        result["interaction_result"]["status"] = "rejected"
    elif mutation == "wrong_ID":
        result["interaction_result"]["instance_id"] += 1
    elif mutation == "same_pending":
        result["remaining_pending_character_interaction"] = snapshot["pending_character_interaction"]
    elif mutation == "unpaused":
        result["paused"] = False
    receipt = interactions.capture_pending_interaction_after_v1(ticket, outcome={"result": result})
    assert receipt["original_pending_advanced_verified"] is verified
    assert receipt["material_effects_verified"] is False and receipt["replay_allowed"] is False
