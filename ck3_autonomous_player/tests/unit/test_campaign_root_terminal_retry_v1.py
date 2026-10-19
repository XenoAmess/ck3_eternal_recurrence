"""Actual F95/F96 diagnostic values; synthetic wire frames and world fixtures.

The production Service gates, waiter and second read are exercised. These tests
do not claim a native read, a live retry, or the missing Enter sub-gate result.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "tools/g2_saved_campaign"))
import test_r724_campaign_root_read_retry as legacy
from xar_autoplayer.bridge.campaign_root_terminal_retry_v1 import is_campaign_root_terminal_rejection_v1
from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.service import GameplayBridgeService
from transform_campaign_root_terminal_retry_v1 import transform_service_source

DATA = json.loads((ROOT / "tests/fixtures/campaign_root_terminal_f95_f96.json").read_bytes())
STEP = "query-campaign-root-context-v1"


def error_for(native_revision=30, case=None):
    # Full native envelopes were not retained in the small MCP response. Rebuild
    # their exact documented wire shape synthetically, keeping actual typed data.
    case = case or DATA["cases"][1]
    rid = case["diagnostic"]["native_request_id"]
    request = dict(type="execute_step", protocol_version=1, request_id=rid,
                   step=STEP, expected_revision=native_revision)
    response = dict(type="command_result", protocol_version=1, request_id=rid, ok=False,
                    error=case["diagnostic"]["native_error"],
                    typed_query_failure_v1=deepcopy(case["typed_failure"]))
    return _NativeCommandRejectedError(case["native_error"], native_request_id=rid,
        native_request_frame=request, native_command_result_frame=response)


@pytest.mark.parametrize("case", DATA["cases"], ids=["F95", "F96"])
def test_closed_failure_values_qualify_only_complete_synthetic_wire_frames(case):
    native = case["diagnostic"]["expected_native_revision"]
    error = error_for(native, case)
    before = deepcopy(error.native_command_result_frame)
    assert is_campaign_root_terminal_rejection_v1(error, {"native_revision": native})
    assert error.native_command_result_frame == before
    assert not is_campaign_root_terminal_rejection_v1(
        _NativeCommandRejectedError(case["native_error"]), {"native_revision": native})


@pytest.mark.parametrize("change", ["action", "request_id", "response_id", "protocol_bool",
    "revision_bool", "revision_wrong", "query_type", "stage", "running", "entered",
    "finish", "typed", "frame", "exception", "exception_bool", "result", "text"])
def test_foreign_incomplete_or_nonterminal_frames_do_not_qualify(change):
    error = error_for()
    request, response = error.native_request_frame, error.native_command_result_frame
    failure = response["typed_query_failure_v1"]
    if change == "action": request["step"] = "move-army-1-to-2"
    elif change == "request_id": request["request_id"] = "foreign"
    elif change == "response_id": response["request_id"] = "foreign"
    elif change == "protocol_bool": request["protocol_version"] = True
    elif change == "revision_bool": request["expected_revision"] = True
    elif change == "revision_wrong": request["expected_revision"] = 31
    elif change == "query_type": failure["query_type"] = "war_entry"
    elif change == "stage": failure["stage"] = "typed_result"
    elif change == "running": failure["wait_result"] = "timeout_executor_already_running"
    elif change == "entered": failure["executor_enter"] = True
    elif change == "finish": failure["executor_finish"] = False
    elif change == "typed": failure["typed_result"] = False
    elif change == "frame": failure["frame_stable"] = True
    elif change == "exception": failure["executor_exception"]["code"] = 0xC0000005
    elif change == "exception_bool": failure["executor_exception"]["code"] = False
    elif change == "result": response["result"] = {"accepted": True}
    else: error.native_error = "other error"
    assert not is_campaign_root_terminal_rejection_v1(error, {"native_revision": 30})


def test_every_failure_observation_is_required_not_defaulted_from_missing():
    for key in DATA["cases"][1]["typed_failure"]:
        error = error_for()
        del error.native_command_result_frame["typed_query_failure_v1"][key]
        assert not is_campaign_root_terminal_rejection_v1(error, {"native_revision": 30}), key
    assert not is_campaign_root_terminal_rejection_v1(error_for(), {"native_revision": True})


def selected_service(driver, service_type=GameplayBridgeService, step=STEP):
    service = service_type(driver)
    service.plan_turn = mock.Mock(return_value={"snapshot_id": "native:30", "revision": 500,
        "plan": {"phase": "native_campaign_root_context", "selected_step": step}})
    return service


def prepare_internal_fixture(driver):
    # Service consumes this synthetic backend's semantic observation protocol.
    # Driver post-read decorators for unrelated declaration state are outside
    # this test; keep the original fixture frame/history omission unchanged.
    driver.command_timeout_seconds = 120.0
    driver.take_internal_semantic_snapshot = lambda: {
        key: deepcopy(value) for key, value in driver.current.items()
        if key != "native_command_history"}


def exercise_gate(kind, tmp_path, service_type=GameplayBridgeService):
    if kind == "selected":
        driver = legacy._RejectedRootDriver()
        driver.first_error = error_for()
        hooks = []
        result = selected_service(driver, service_type).auto_turn(
            before_submit=lambda payload: hooks.append(payload))
        assert result["status"] == "executed" and len(hooks) == 1
        assert result["read_only_query_retry"]["fresh_native_revision"] == 31
    elif kind == "initial":
        driver = legacy._InternalRejectedSuccessionRootDriver()
        prepare_internal_fixture(driver)
        driver.first_error = error_for()
        service = service_type(driver)
        current = service._prepare_succession_transition_v1(
            driver.take_internal_semantic_snapshot(), {STEP, "life-advance"})
        assert current["revision"] == 501 and driver.retained_revisions == [501]
    else:
        driver = legacy._RejectedRootDriver()
        driver.allow_private_current_first_heir_betrothal_fulfillment = True
        driver.first_error = error_for()
        service = service_type(driver)
        frame = driver.take_snapshot()
        planned = {"snapshot_id": frame["snapshot_id"], "revision": 500,
                   "plan": {"selected_step": "life-advance"}}
        # Isolate this Service catch/retry gate from the unrelated relation DTO
        # contract. The deterministic consumer only requests the native root;
        # the marker returns from the remaining optional family arbitration.
        def root_only(_driver, current, _snapshot, **_kwargs):
            _driver.execute_step(STEP, expected_revision=current["revision"])
            return {**current, "plan": {**current["plan"], "current_betrothal_fulfillment": True}}
        with mock.patch.object(sys.modules[service_type.__module__],
                               "plan_current_first_heir_betrothal_fulfillment_private",
                               side_effect=root_only), mock.patch.object(
                service, "_plan_private_family_education_v1", side_effect=lambda current, *_a, **_k: current):
            result = service._plan_private_family_opportunity_v1(planned, frame)
        assert result["revision"] == 501 and result["plan"]["selected_step"] == "life-advance"
    assert driver.calls == [(STEP, 500), (STEP, 501)] and driver.wait_count == 1


@pytest.mark.parametrize("kind", ["initial", "family", "selected"])
def test_real_service_three_gates_use_existing_once_retry(kind, tmp_path):
    exercise_gate(kind, tmp_path)


@pytest.mark.parametrize("drift", ["date", "event", "typed_action", "no_new_native_frame"])
def test_existing_fresh_frame_guards_still_reject_without_second_read(drift):
    driver = legacy._RejectedRootDriver(drift=drift)
    driver.first_error = error_for()
    with pytest.raises(_NativeCommandRejectedError) as caught:
        selected_service(driver).auto_turn()
    assert caught.value is driver.first_error
    assert driver.calls == [(STEP, 500)] and driver.wait_count == 1
    assert caught.value.read_only_query_retry_decline["status"] == "declined"


def test_second_refusal_retains_original_error_and_never_loops():
    driver = legacy._RejectedRootDriver(second_reject=True)
    driver.first_error = error_for()
    with pytest.raises(_NativeCommandRejectedError) as caught:
        selected_service(driver).auto_turn()
    assert caught.value is driver.first_error and "second_error" in caught.value.read_only_query_retry
    assert driver.calls == [(STEP, 500), (STEP, 501)] and driver.wait_count == 1


def test_selected_action_is_not_replayed_even_with_campaign_shaped_error():
    driver = legacy._RejectedRootDriver()
    driver.first_error = error_for()
    with pytest.raises(_NativeCommandRejectedError):
        selected_service(driver, step="move-army-1-to-2").auto_turn()
    assert driver.calls == [("move-army-1-to-2", 500)] and driver.wait_count == 0


def test_legacy_bare_path_remains_unchanged():
    driver = legacy._RejectedRootDriver()
    assert selected_service(driver).auto_turn()["status"] == "executed"
    assert len(driver.calls) == 2 and driver.wait_count == 1


def test_actual_source15_reversible_splice_and_all_three_gates_in_memory(tmp_path):
    source = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/"
                  "sdk-v20261019-candidate/src15/xar_autoplayer/bridge/service.py")
    if not source.is_file():
        pytest.skip("closed Source15 source is not present on this machine")
    before = source.read_bytes()
    assert hashlib.sha256(before).hexdigest() == "5b49eaf311269230aeb046e9f61ccb829aa4392c627b23f0878e14f42c3883f8"
    after = transform_service_source(before)
    assert transform_service_source(after, reverse=True) == before
    name = "xar_autoplayer.bridge._source20_service_offline_qualification"
    module = ModuleType(name)
    module.__file__ = str(source)
    module.__package__ = "xar_autoplayer.bridge"
    sys.modules[name] = module
    try:
        exec(compile(after, str(source), "exec"), module.__dict__)
        for kind in ("initial", "family", "selected"):
            exercise_gate(kind, tmp_path, module.GameplayBridgeService)
    finally:
        del sys.modules[name]
