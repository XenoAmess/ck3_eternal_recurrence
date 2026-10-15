"""Construction readback keeps one Game identity across DMTF offsets and SDK rotations."""

import copy

import pytest

from construction_cold_readback_classifier_v1 import (
    classify_construction_cold_requery_v1,
    classify_dmtf_creation_instant_v1,
)
from test_construction_cold_readback_classifier_v1 import _case, _next


def _rotated_monthly():
    first, state, initial, pid = _case()
    _, state = classify_construction_cold_requery_v1(
        first, state=state, initial_frame=initial, game_pid=pid)
    prior = _next(first, date=53234016, native=100, public=99, proof=104000)
    _, state = classify_construction_cold_requery_v1(
        prior, state=state, initial_frame=initial, game_pid=pid)
    current = _next(prior, date=53234736, native=200, public=3, proof=105000)
    current["planning_source_frame"]["connection_generation"] = 3
    current["result"]["post_bridge_creation_date"] = "20261015123736.520398+480"
    return current, state, initial, pid


def test_dmtf_same_instant_has_exact_microsecond_precision():
    parse = classify_dmtf_creation_instant_v1
    assert parse("20261015043736.520398+000") == parse("20261015123736.520398+480")
    assert parse("20261015043736.520399+000") != parse("20261015123736.520398+480")
    assert parse("20261015123736.520398+999") is None
    assert parse("20261315123736.520398+480") is None


def test_offset_equivalent_birth_and_new_sdk_public_counter_are_readonly():
    current, state, initial, pid = _rotated_monthly()
    before = copy.deepcopy(state)
    observation, next_state = classify_construction_cold_requery_v1(
        current, state=state, initial_frame=initial, game_pid=pid)
    action = current["result"]["action_request_id"]
    assert observation["typed_nonmaterial_observation"] is True
    assert observation["construction_start_verified"] is False
    assert observation["construction_completion_verified"] is False
    assert observation["business_success_inferred"] is False
    assert observation["replay_allowed"] is False
    assert next_state["construction_actions"][action]["binding"] == before["construction_actions"][action]["binding"]
    assert next_state["construction_actions"][action]["cold_readback_generation_v1"]["last_connection_generation"] == 3


def test_legacy_tracker_without_connection_uses_fresh_native_date_and_proof():
    current, state, initial, pid = _rotated_monthly()
    action = current["result"]["action_request_id"]
    state["construction_actions"][action]["cold_readback_generation_v1"].pop("last_connection_generation")
    observation, after = classify_construction_cold_requery_v1(
        current, state=state, initial_frame=initial, game_pid=pid)
    assert observation["construction_start_verified"] is False
    assert after["construction_actions"][action]["cold_readback_generation_v1"]["last_connection_generation"] == 3


@pytest.mark.parametrize("change", [
    lambda b, s: b["result"].__setitem__("post_bridge_pid", 226541),
    lambda b, s: b["result"].__setitem__("post_bridge_creation_date", "20261015123736.520399+480"),
    lambda b, s: b["result"].__setitem__("post_bridge_creation_date", "20261015123736.520398+999"),
    lambda b, s: b["result"].__setitem__("post_public_revision", 4),
    lambda b, s: b["result"].__setitem__("post_proof_epoch", 104000),
    lambda b, s: b["result"].__setitem__("post_native_revision", 199),
    lambda b, s: s["construction_actions"][b["result"]["action_request_id"]]["cold_readback_generation_v1"].__setitem__("last_connection_generation", 3),
])
def test_wrong_pid_birth_frame_proof_or_same_connection_reset_rejected(change):
    current, state, initial, pid = _rotated_monthly()
    change(current, state)
    with pytest.raises(ValueError, match="construction cold readonly requery rejected"):
        classify_construction_cold_requery_v1(
            current, state=state, initial_frame=initial, game_pid=pid)
