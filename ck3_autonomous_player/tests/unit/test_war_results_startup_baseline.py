"""Actual six-field queue frame contract with a real Service/Driver DTO.

Native I/O is synthetic. The full queue settlement replay is separately pinned
in the research receipt; this portable test does not impersonate that runner.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_war_results_first_read_defer import scene, run, classifier

_spec = importlib.util.spec_from_file_location(
    "queue_frame_contract", Path(__file__).parent / "fixtures/queue_startup_frame_contract.py")
contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contract)


def baseline(current, *, earlier=True):
    metrics = dict(current, paused=True, map_ready=True, actor_alive=True)
    if earlier:
        metrics.update(snapshot_id="native:39", revision=1, native_revision=39,
                       date_raw=current["date_raw"] - 24)
    result = contract.frame(metrics)
    assert set(result) == {"snapshot_id", "revision", "native_revision",
                           "date_raw", "actor_character_id", "episode_run_id"}
    return result


def classify(body, startup, current):
    return classifier.classify_war_results_first_read_state_changed_v1(
        body, initial_frame=startup, game_pid=current["bridge_pid"])


def test_real_six_field_startup_accepts_later_current_query(scene):
    body, current = run(scene)
    startup = baseline(current)
    assert (startup["revision"], startup["native_revision"]) == (1, 39)
    assert (current["revision"], current["native_revision"]) == (2, 40)
    assert startup["date_raw"] < current["date_raw"]
    credit = classify(body, startup, current)
    assert credit["typed_nonmaterial_observation"] is True
    for flag in ("primitive_accepted", "submitted_pending", "ui_action_credit",
                 "date_advance_observed", "war_results_window_closed_verified",
                 "business_success_inferred", "replay_allowed"):
        assert credit[flag] is False


@pytest.mark.parametrize("case", [
    "wire_public_not_native", "raw_request_id", "current_source_public_native_swap",
    "current_query_lease", "wrong_Game", "false_acceptance", "false_window_close",
    "initial_actor_character_id", "initial_episode_run_id", "initial_date_raw",
])
def test_formal_review_negative_contracts_remain_rejected(scene, case):
    body, current = run(scene)
    startup = baseline(current)
    result = body["result"]
    if case == "wire_public_not_native":
        result["native_error_evidence"]["native_request"]["expected_revision"] = current["revision"]
    elif case == "raw_request_id":
        result["native_error_evidence"]["native_command_result"]["request_id"] = "other"
    elif case == "current_source_public_native_swap":
        result["source_frame"]["revision"] = current["native_revision"]
    elif case == "current_query_lease":
        result["failed_attempt"]["queried_revision"] += 1
    elif case == "wrong_Game":
        result["source_frame"]["bridge_pid"] += 1
        body["planning_source_frame"]["bridge_pid"] += 1
    elif case == "false_acceptance":
        result["accepted"] = True
    elif case == "false_window_close":
        result["close_dispatched"] = True
    elif case == "initial_actor_character_id":
        startup["actor_character_id"] += 1
    elif case == "initial_episode_run_id":
        startup["episode_run_id"] = "other_episode"
    else:
        startup["date_raw"] = current["date_raw"] + 24
    with pytest.raises(ValueError):
        classify(body, startup, current)


def test_handoff_must_replace_the_actor_episode_baseline(scene):
    body, current = run(scene)
    # Synthetic predecessor identity, not evidence of a new in-game death.
    inherited = baseline(current, earlier=False)
    predecessor = deepcopy(inherited)
    predecessor.update(actor_character_id=current["actor_character_id"] + 1,
                       episode_run_id="synthetic_predecessor_episode")
    with pytest.raises(ValueError):
        classify(body, predecessor, current)
    assert classify(body, inherited, current)["typed_nonmaterial_observation"] is True
