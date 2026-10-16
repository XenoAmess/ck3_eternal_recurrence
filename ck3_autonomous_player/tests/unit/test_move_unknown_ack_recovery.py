"""Real Service -> Driver -> primitive wire for uncertain move ACKs.

Native transport/snapshot inputs and the preselected planner input are fake.
The real constructor, dispatch, public/native mapping, history and Service run.
These tests do not attest ordinary planner selection or actual Native execution.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_native_bridge_driver import FakeEndpoint
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge.service import GameplayBridgeService

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "move_unknown_ack_outcome", ROOT / "tools/g2_saved_campaign/move_unknown_ack_outcome.py")
outcome_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outcome_module)
FIXTURE = json.loads((Path(__file__).parent / "fixtures/move_unknown_ack_actual_projection.json").read_text(encoding="utf-8"))


def scenario(*, change=None, native_error="CK3 move-army state is unavailable", army_id=402653503):
    before, after = deepcopy(FIXTURE["before"]), deepcopy(FIXTURE["after"])
    for frame in (before, after):
        frame["player_armies"][0]["army_id"] = army_id
    if change:
        change(before, after)
    endpoint = FakeEndpoint()
    driver = native.NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
    driver.state_dir = None
    sent = []
    step = f"move-army-{army_id}-to-5980"
    driver.capabilities = lambda: {"action_steps": [step], "bridge_capabilities": [
        native.MOVE_ARMY_CAPABILITY, native.ARMY_ROUTES_CAPABILITY]}
    driver.take_snapshot = lambda: deepcopy(after if sent else before)

    def answer(request):
        # Production _execute_primitive_step creates and sends this packet.
        sent.append(deepcopy(request))
        endpoint.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": False,
                          "error": native_error})

    endpoint.send_hook = answer
    service = object.__new__(GameplayBridgeService)
    service.driver = driver
    service._auto_camera_worker = SimpleNamespace(schedule=lambda _: {"status": "test_no_camera"})
    frame = service._observed_planning_source_frame(before)

    def run(phase="native_war_pursuit"):
        plan = {"policy": "one-life-turn-v1", "phase": phase, "selected_step": step}
        service.plan_turn = lambda: {"plan": deepcopy(plan), "snapshot_id": before["snapshot_id"],
                                    "revision": before["revision"], "planning_source_frame": deepcopy(frame)}
        submitted = []
        result = service.auto_turn(before_submit=lambda row: submitted.append(deepcopy(row)))
        assert submitted[0]["revision"] == 256
        return result

    return driver, sent, frame, run


def binding(body, *, initial_frame=None, game_pid=None):
    actual = body["planning_source_frame"]
    assert actual == initial_frame and actual["bridge_pid"] == game_pid
    return deepcopy(actual)


def classify(body, frame):
    return outcome_module.classify_move_native_error_route_observed_v1(
        body, bind_gameplay_frame=binding, initial_frame=frame, game_pid=frame["bridge_pid"])


@pytest.mark.parametrize("phase", ["native_war_pursuit", "native_war_defensive_reposition",
                                  "native_war_siege_uncertain_first_hop_move"])
def test_real_primitive_uses_native_revision_and_retains_unknown_ack(phase):
    driver, sent, frame, run = scenario()
    try:
        body = run(phase)
        assert type(driver).execute_step is native.NativeHeadlessGameplayDriver.execute_step
        assert driver._execute_primitive_step.__func__ is native.NativeHeadlessGameplayDriver._execute_primitive_step
        assert len(sent) == 1 and sent[0]["expected_revision"] == 3207
        inner = body["result"]
        assert inner["source_frame"]["revision"] == 256
        assert inner["source_frame"]["native_revision"] == 3207
        assert inner["observed_frame"]["revision"] == 257
        assert inner["observed_frame"]["native_revision"] == 3208
        assert inner["observed_army_route"] == [5983, 5981, 5980]
        assert inner["native_error_evidence"]["native_request"] == sent[0]
        assert inner["native_ack_status"] == "unknown_after_error"
        assert inner["business_submission_may_have_applied"] is True
        assert len(driver._command_history) == 1 and driver._command_history[0]["ok"] is False
        credit = classify(body, frame)
        for key in ("primitive_accepted", "date_advance_observed", "business_success_inferred", "replay_allowed"):
            assert credit[key] is False
        assert credit["typed_nonmaterial_observation"] is True
    finally:
        driver.close()


@pytest.mark.parametrize("change,error", [
    (lambda old,new: new["player_armies"][0].update(route_province_ids=[5983,5999]), None),
    (lambda old,new: new["diagnostics"].update(bridge_pid=777), None),
    (lambda old,new: old["player_armies"][0].update(move_target_province_id=5980), None),
    (lambda old,new: new.update(date_raw=new["date_raw"]+24), None),
    (lambda old,new: None, "CK3 unrelated move failure"),
])
def test_unmatched_readback_preserves_error_without_replay(change, error):
    driver, sent, _, run = scenario(change=change, native_error=error or "CK3 move-army state is unavailable")
    try:
        with pytest.raises(native._NativeCommandRejectedError):
            run()
        assert len(sent) == 1
        assert len(driver._command_history) == 1 and driver._command_history[0]["ok"] is False
    finally:
        driver.close()


def test_portable_classifier_does_not_upgrade_ack_and_accepts_public_army_zero():
    driver, sent, frame, run = scenario(army_id=0)
    try:
        body = run()
        assert classify(body, frame)["army_id"] == 0
        for change in (
            lambda row: row["result"].update(accepted=True),
            lambda row: row["result"].update(native_ack_status="accepted"),
            lambda row: row["result"]["native_error_evidence"]["native_request"].update(expected_revision=256),
            lambda row: row["result"]["source_frame"].update(revision=3207),
            lambda row: row["plan"].update(phase=""),
        ):
            changed = deepcopy(body); change(changed)
            with pytest.raises(ValueError):
                classify(changed, frame)
        assert len(sent) == 1
    finally:
        driver.close()
