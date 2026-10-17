"""Completed AUTO50 through the public consumer, with actual startup frame shape.

The original formal queue replay is preserved separately. These tests exercise
the portable consumer and reviewed binder; they do not impersonate a live queue.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from tools.g2_saved_campaign.route_contact_exact_day_outcome import (
    classify_route_contact_horizon_one_day_v1,
)


FIXTURES = Path(__file__).with_name("fixtures")


def load_fixture_module(name):
    spec = importlib.util.spec_from_file_location(name, FIXTURES / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BINDER = load_fixture_module("reviewed_gameplay_start_binding_v1")
MUTATIONS = load_fixture_module("route_clock_popup_mutations").mutations


def actual():
    return json.loads((FIXTURES / "route_clock_popup_actual50.json").read_text(encoding="utf-8"))


def classify(body, fixture):
    return classify_route_contact_horizon_one_day_v1(
        body,
        bind_gameplay_frame=BINDER.classify_gameplay_start_binding_v1,
        initial_frame=fixture["initial_frame"],
        game_pid=fixture["game_pid"],
    )


def test_actual_popup_keeps_only_the_observed_clock_credit():
    fixture = actual()
    body = fixture["body"]
    before = copy.deepcopy(body)
    assert len(fixture["initial_frame"]) == 6
    assert fixture["initial_frame"]["date_raw"] < body["planning_source_frame"]["date_raw"]
    credit = classify(body, fixture)
    assert body == before
    assert credit["actual_date_delta_raw"] == 24
    assert credit["actual_elapsed_days"] == 1
    assert credit["date_advance_observed"] is True
    assert credit["paired_after_metrics_still_required"] is True
    for key in (
        "primitive_accepted", "material_verified", "ui_action_credit", "action_credit",
        "business_success_inferred", "replay_allowed",
    ):
        assert credit[key] is False


def test_map_and_unresolved_interaction_keep_the_same_clock_contract():
    fixture = actual()
    body = fixture["body"]
    expected = classify(body, fixture)
    body["result"].update(active_event=None, pending_character_interaction=None,
                          final_screen="map_hud", event_resolution="none")
    assert classify(body, fixture) == expected
    body["result"].update(pending_character_interaction={"source": "synthetic_unresolved"},
                          final_screen=None)
    assert classify(body, fixture) == expected


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_clock_scope_and_popup_negatives_remain_rejected(name):
    fixture = actual()
    body = fixture["body"]
    MUTATIONS[name](body)
    with pytest.raises(ValueError):
        classify(body, fixture)


def test_unrelated_step_does_not_claim_clock_or_ui_credit():
    fixture = actual()
    fixture["body"]["selected_step"] = "select-event-option-1"
    assert classify(fixture["body"], fixture) is None
