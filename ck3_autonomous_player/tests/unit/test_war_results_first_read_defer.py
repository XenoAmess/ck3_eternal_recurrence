"""Synthetic Native I/O through the real ordinary AUTO, dedicated query and wire.

The Service owns the real NativeHeadless Driver: no facade, preselected plan,
precomputed DTO or overridden business entry point. No actual Game is accessed.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_results_window_contract import QUERY_STEP, QUERY_CAPABILITY, CLOSE_CAPABILITY
from xar_autoplayer.bridge.war_results_window_transport import get_current_war_results_window_v1
from xar_autoplayer.ordinary_war_results_window_v1 import plan_ordinary_war_results_window_v1

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "war_results_first_read_outcome", ROOT / "tools/g2_saved_campaign/war_results_first_read_outcome.py")
classifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)


@pytest.fixture
def scene():
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
    hello = _hello("game.state.snapshot", QUERY_CAPABILITY, CLOSE_CAPABILITY,
                   *("game.command." + step for step in
                     ("pause-map", "resume-map", "set-speed-1", "set-speed-3", "set-speed-5")))
    hello.update(bridge_version="0.1.0.4", expected_ck3_version=CK3_12004.game_version,
                 expected_ck3_sha256=CK3_12004.executable_sha256, connection_generation=17)
    endpoint.publish(hello)
    endpoint.publish(_snapshot(40, played_character={"character_id": 707, "alive": True}))
    before = driver.take_internal_semantic_snapshot()
    endpoint.frames.clear()  # Initial handshake is outside the tested query.
    endpoint.send_hook = lambda request: endpoint.publish({
        "type": "command_result", "protocol_version": 1, "request_id": request["request_id"],
        "ok": False, "error": "state_changed"})
    service = GameplayBridgeService(driver)
    service._auto_camera_worker = SimpleNamespace(schedule=lambda _: {"status": "synthetic_no_camera"})
    try:
        yield service, driver, endpoint, before
    finally:
        driver.close()


def run(scene):
    service, driver, endpoint, before = scene
    submitted = []
    frame = service._observed_planning_source_frame(before)
    body = service.auto_turn(before_submit=lambda plan: submitted.append(deepcopy(plan)))
    assert len(submitted) == 1
    assert service.driver is driver and type(driver) is NativeHeadlessGameplayDriver
    assert submitted[0]["revision"] == before["revision"] == 2
    assert len(endpoint.frames) == 1
    assert endpoint.frames[0]["expected_revision"] == before["native_revision"] == 40
    return body, frame


def classify(body, frame):
    return classifier.classify_war_results_first_read_state_changed_v1(
        body, initial_frame=frame, game_pid=frame["bridge_pid"])


def test_first_query_state_changed_is_a_readonly_observation_without_replay(scene):
    service, driver, endpoint, before = scene
    body, frame = run(scene)
    assert body["status"] == "observed" and body["selected_step"] == QUERY_STEP
    assert body["ui_action_credit"] is False
    result = body["result"]
    assert result["native_error_evidence"]["native_request"] == endpoint.frames[0]
    assert result["native_error_evidence"]["native_command_result"]["error"] == "state_changed"
    assert result["failed_attempt"]["native_request_id"] == endpoint.frames[0]["request_id"]
    assert result["window_presence"] == "unknown"
    assert result["close_dispatched"] is False
    assert driver._command_history[-1]["command"] == QUERY_STEP
    assert driver._command_history[-1]["ok"] is False
    credit = classify(body, frame)
    assert credit["typed_nonmaterial_observation"] is True
    for flag in ("primitive_accepted", "ui_action_credit", "date_advance_observed",
                 "war_results_window_closed_verified", "business_success_inferred", "replay_allowed"):
        assert credit[flag] is False
    assert get_current_war_results_window_v1(driver, before) is None
    current = driver.take_internal_semantic_snapshot()
    assert current["war_results_window_v1_query_attempt"]["status"] == "failed"
    assert plan_ordinary_war_results_window_v1(
        current, action_steps=(QUERY_STEP,), bridge_capabilities=(QUERY_CAPABILITY,)) is None
    next_plan = service.plan_turn()
    assert next_plan["plan"]["selected_step"] in ("life-advance", "life-advance-one-day")
    assert len(endpoint.frames) == 1


@pytest.mark.parametrize("mutate", [
    lambda x: x["result"]["native_error_evidence"]["native_command_result"].update(error="other"),
    lambda x: x["result"]["native_error_evidence"]["native_request"].update(request_id="other"),
    lambda x: x["result"]["source_frame"].update(bridge_pid=999),
    lambda x: x["result"].update(accepted=True),
    lambda x: x["result"].update(close_dispatched=True),
    lambda x: x["plan"].update(phase="other"),
    lambda x: x["result"]["native_error_evidence"]["native_request"].update(expected_revision=2),
])
def test_classifier_rejects_unbound_packets_and_false_credit(scene, mutate):
    body, frame = run(scene)
    mutate(body)
    with pytest.raises(ValueError): classify(body, frame)


@pytest.mark.parametrize("error", ["arbitrary_error", "war_declared_owner_submission_or_completion_failed"])
def test_other_query_failures_remain_errors(scene, error):
    service, _, endpoint, _ = scene
    endpoint.send_hook = lambda request: endpoint.publish({
        "type": "command_result", "protocol_version": 1, "request_id": request["request_id"],
        "ok": False, "error": error})
    with pytest.raises(BridgeUnavailableError, match=error): service.auto_turn()
    assert len(endpoint.frames) == 1


def test_close_state_changed_is_never_softened(scene):
    _, driver, endpoint, before = scene
    with pytest.raises(BridgeUnavailableError, match="state_changed"):
        driver.close_war_results_window_v1(expected_revision=before["revision"])
    assert len(endpoint.frames) == 1 and endpoint.frames[0]["step"] == "close-war-results-window-v1"


def test_a_new_native_frame_may_read_once_with_a_new_request_id(scene):
    service, _, endpoint, _ = scene
    body, _ = run(scene)
    first_id = body["result"]["native_request_id"]
    endpoint.publish(_snapshot(41, played_character={"character_id": 707, "alive": True}))
    second = service.auto_turn()
    assert second["status"] == "observed"
    assert len(endpoint.frames) == 2 and endpoint.frames[1]["expected_revision"] == 41
    assert endpoint.frames[1]["request_id"] != first_id
