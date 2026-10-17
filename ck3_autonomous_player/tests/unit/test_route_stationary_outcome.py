"""Completed stationary clock replay and public Native proof producer.

The actual queue reconsume/persistence replay is archived separately. These
portable tests make no Game calls and do not impersonate a public queue.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from tools.g2_saved_campaign.route_contact_exact_day_outcome import (
    classify_route_contact_horizon_one_day_v1,
)
from xar_autoplayer.bridge.native_driver import _fresh_route_contact_advance_proofs


FIXTURES = Path(__file__).with_name("fixtures")


def load(name):
    spec = importlib.util.spec_from_file_location(name, FIXTURES / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BINDER = load("reviewed_gameplay_start_binding_v1")
MUTATIONS = load("route_stationary_mutations").mutations


def actual():
    return json.loads((FIXTURES / "route_stationary_actual22.json").read_text(encoding="utf-8"))


def classify(body, fixture):
    return classify_route_contact_horizon_one_day_v1(
        body, bind_gameplay_frame=BINDER.classify_gameplay_start_binding_v1,
        initial_frame=fixture["initial_frame"], game_pid=fixture["game_pid"],
    )


def test_actual_stationary_clock_is_date_only_and_does_not_mutate_input():
    fixture = actual()
    body = fixture["body"]
    unchanged = copy.deepcopy(body)
    assert len(fixture["initial_frame"]) == 6
    credit = classify(body, fixture)
    assert body == unchanged
    assert credit["actual_date_delta_raw"] == 24
    assert credit["actual_elapsed_days"] == 1
    assert credit["paired_after_metrics_still_required"] is True
    for key in ("primitive_accepted", "material_verified", "ui_action_credit",
                "action_credit", "business_success_inferred", "replay_allowed"):
        assert credit[key] is False
    body["result"].update(active_event={"instance_id": 111, "option_count": 3},
                          final_screen=None, event_resolution="typed_query_required")
    assert classify(body, fixture) == credit


@pytest.mark.parametrize("state,code", [("regular", 1), ("sieging", 3), (None, 1), (None, 3)])
def test_known_stationary_native_postures(state, code):
    fixture = actual()
    body = fixture["body"]
    body["result"]["war_progress_before"]["wars"][0]["player_armies"][0].update(
        army_state=state, army_state_code=code)
    assert classify(body, fixture)["actual_date_delta_raw"] == 24


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_clock_scope_and_stationary_negatives(name):
    fixture = actual()
    MUTATIONS[name](fixture["body"])
    with pytest.raises(ValueError):
        classify(fixture["body"], fixture)


def test_actual_readonly_lease_advertises_stationary_step_through_public_producer():
    fixture = actual()
    semantic, query, body = fixture["semantic"], fixture["query"], fixture["body"]
    proofs = _fresh_route_contact_advance_proofs(semantic, [query])
    assert body["selected_step"] in proofs
    proof = proofs[body["selected_step"]]
    assert proof["proof_kind"] == "contact_free"
    assert proof["contact_horizon"]["subject_route"]["route_province_ids"] == []
    assert query["result"]["queried_revision"] != query["result"]["queried_native_revision"]
    for key in ("queried_revision", "queried_native_revision", "queried_connection_generation"):
        bad = copy.deepcopy(query)
        bad["result"][key] = 999
        assert body["selected_step"] not in _fresh_route_contact_advance_proofs(semantic, [bad])
