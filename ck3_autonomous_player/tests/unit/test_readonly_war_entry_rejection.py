"""Exact typed war-entry read failures replan without action credit or replay."""

import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.readonly_war_entry_rejection import (
    _ERROR, _TYPED_FAILURE,
    observe_readonly_war_entry_rejection_v1,
    returned_readonly_war_entry_typed_rejection_v1,
    suppressed_war_entry_read_steps_v1,
)
from xar_autoplayer.strategy import choose_one_life_turn
from test_war_entry_assessments_bridge import (
    _claim_snapshot_and_history, _player_claim,
)


STEP = "query-war-entry-assessments-v1-1-30380"
SOURCE = {
    "schema": "xar.ck3.planning-source-frame/v1", "status": "complete",
    "snapshot_id": "native:1370", "revision": 1285, "native_revision": 1370,
    "date_raw": 53195616, "actor_character_id": 31254,
    "episode_run_id": "native-31254-96253c58fd68",
    "connection_generation": 4, "bridge_pid": 202692,
}
REQUEST = {"type": "execute_step", "protocol_version": 1,
           "request_id": "step-1921-9dbdd609dc8a", "step": STEP,
           "expected_revision": 1370}
RESPONSE = {"type": "command_result", "protocol_version": 1,
            "request_id": REQUEST["request_id"], "ok": False,
            "error": _ERROR, "typed_query_failure_v1": _TYPED_FAILURE}
PLANNED = {"snapshot_id": SOURCE["snapshot_id"], "revision": SOURCE["revision"],
           "planning_source_frame": SOURCE, "plan": {"selected_step": STEP}}


def rejection(request=None, response=None):
    req = copy.deepcopy(request if request is not None else REQUEST)
    resp = copy.deepcopy(response if response is not None else RESPONSE)
    return _NativeCommandRejectedError(
        _ERROR + "; typed_query_failure_v1="
        + json.dumps(resp["typed_query_failure_v1"], sort_keys=True, separators=(",", ":")),
        native_request_id=req["request_id"], native_request_frame=req,
        native_command_result_frame=resp,
    )


def frame():
    return {"snapshot_id": SOURCE["snapshot_id"], "revision": SOURCE["revision"],
            "native_revision": SOURCE["native_revision"], "date_raw": SOURCE["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 31254, "alive": True},
            "episode_run_id": SOURCE["episode_run_id"],
            "diagnostics": {"bridge_pid": 202692, "connection_generation": 4}}


class _Driver:
    def __init__(self, fresh):
        self.fresh = fresh
        self.reads = 0

    def take_internal_semantic_snapshot(self):
        self.reads += 1
        return copy.deepcopy(self.fresh)


class _Service:
    def __init__(self, fresh):
        self.driver = _Driver(fresh)


def test_exact_typed_read_failure_is_zero_action_and_cools_only_its_target():
    result = returned_readonly_war_entry_typed_rejection_v1(
        rejection(), STEP, PLANNED)
    assert result["status"] == "readonly_rejected"
    assert result["result"]["business_submission"] is False
    assert result["result"]["replay_allowed"] is False
    service = _Service(frame())
    observed = observe_readonly_war_entry_rejection_v1(service, result)
    assert observed["result"]["fresh_snapshot_verified"] is True
    assert service.driver.reads == 1
    assert suppressed_war_entry_read_steps_v1(frame(), service._readonly_war_entry_failures) == {STEP}
    assert suppressed_war_entry_read_steps_v1(
        {**frame(), "date_raw": SOURCE["date_raw"] + 168},
        service._readonly_war_entry_failures) == set()
    other_game = frame()
    other_game["diagnostics"]["bridge_pid"] += 1
    assert suppressed_war_entry_read_steps_v1(
        other_game, service._readonly_war_entry_failures) == set()


@pytest.mark.parametrize("mutation", ["wrong_step", "wrong_revision", "accepted", "wrong_type"])
def test_unknown_or_unbound_native_failure_is_not_normalized(mutation):
    request, response = copy.deepcopy(REQUEST), copy.deepcopy(RESPONSE)
    if mutation == "wrong_step":
        request["step"] = "pause-map"
    elif mutation == "wrong_revision":
        request["expected_revision"] -= 1
    elif mutation == "accepted":
        response["ok"] = True
    else:
        response["typed_query_failure_v1"]["query_type"] = "other"
    assert returned_readonly_war_entry_typed_rejection_v1(
        rejection(request, response), STEP, PLANNED) is None


def test_unverified_fresh_frame_does_not_replan_or_cool_target():
    result = returned_readonly_war_entry_typed_rejection_v1(
        rejection(), STEP, PLANNED)
    service = _Service({**frame(), "paused": False})
    observed = observe_readonly_war_entry_rejection_v1(service, result)
    assert observed["result"]["replan_deferred"] is True
    assert service._readonly_war_entry_rejection_refresh == result
    assert not hasattr(service, "_readonly_war_entry_failures")


def test_suppressed_first_claim_target_allows_another_real_read_only():
    first, second = (_player_claim(808, title=91),
                     _player_claim(909, title=92))
    snapshot, history = _claim_snapshot_and_history(
        [first, second], [], target_contexts=[
            (808, 91, "county"), (909, 92, "county")])
    plan = choose_one_life_turn(
        history, snapshot=snapshot,
        action_steps={"query-war-entry-assessments-v1-1-909",
                      "declare-war-808-11-0", "declare-war-909-11-0",
                      "life-advance"})
    assert plan["selected_step"] == "query-war-entry-assessments-v1-1-909"
    assert plan["phase"] == "native_player_claim_power_assessment"
    no_read = choose_one_life_turn(
        history, snapshot=snapshot,
        action_steps={"declare-war-808-11-0", "declare-war-909-11-0",
                      "life-advance"})
    assert no_read["selected_step"] == "life-advance"
    assert no_read["decision"]["outcome"] == "NO_DECLARE"
