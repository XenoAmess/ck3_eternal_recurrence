"""War-entry reads retain their checks without exporting command history."""

import copy
from unittest import mock

import pytest

from test_war_entry_assessments_bridge import (
    STEP,
    _ServiceDriver,
    _answer,
    _native_driver,
    _result,
    _semantic_snapshot,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService


class FiniteServiceDriver(_ServiceDriver):
    def take_snapshot(self):
        raise AssertionError("service requested the full command history")

    def take_snapshot_without_native_command_history(self):
        return _ServiceDriver.take_snapshot(self)


def test_service_uses_two_finite_snapshots_with_identical_result_and_scope():
    finite = FiniteServiceDriver()
    ordinary = _ServiceDriver()
    actual = GameplayBridgeService(finite).query_war_entry_assessments(
        [808], expected_revision=17)
    expected = GameplayBridgeService(ordinary).query_war_entry_assessments(
        [808], expected_revision=17)
    assert actual == expected
    assert finite.snapshot_count == ordinary.snapshot_count == 2
    assert finite.execute_count == ordinary.execute_count == 1


def test_native_query_uses_no_history_snapshot_and_preserves_public_history():
    driver, endpoint = _native_driver()
    _answer(endpoint)
    driver._command_history.append({"index": 9, "command": "synthetic-prior", "ok": True})
    revision = driver.take_snapshot()["revision"]
    with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError(
        "native query exported command history")):
        actual = driver.execute_step(STEP, expected_revision=revision)
    assert actual["status"] == "available"
    assert actual["war_entry_assessments"] == _result()["war_entry_assessments"]
    public = driver.take_snapshot()
    assert any(row.get("command") == "synthetic-prior"
               for row in public["native_command_history"])
    assert public["war_entry_assessments"] == actual["war_entry_assessments"]


def test_end_to_end_service_and_native_query_never_export_history():
    driver, endpoint = _native_driver()
    _answer(endpoint)
    revision = driver.take_snapshot()["revision"]
    with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError(
        "war-entry query exported command history")):
        actual = GameplayBridgeService(driver).query_war_entry_assessments(
            [808], expected_revision=revision)
    assert actual["status"] == "available"
    assert actual["war_entry_assessments"] == _result()["war_entry_assessments"]
    assert actual["target_scopes"] == [
        {"target_character_id": 808, "sources": ["declarable_war"]}]


@pytest.mark.parametrize("mutation", ["target", "native_revision", "ending_frame"])
def test_native_query_still_rejects_scope_or_frame_drift(mutation):
    driver, endpoint = _native_driver()
    revision = driver.take_snapshot()["revision"]

    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        result = copy.deepcopy(_result())
        if mutation == "target":
            result["war_entry_assessments"]["assessments"][0]["target_character_id"] = 42
        elif mutation == "native_revision":
            result["war_entry_assessments"]["snapshot_revision"] = 6
        else:
            endpoint.publish(_semantic_snapshot(6))
        endpoint.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": frame["request_id"], "ok": True,
                          "result": result})

    endpoint.send_hook = answer
    with pytest.raises(BridgeUnavailableError):
        driver.execute_step(STEP, expected_revision=revision)
