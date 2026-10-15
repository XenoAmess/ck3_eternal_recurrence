"""Only declarable reads omit transcript copies; declaration stays unchanged."""

import copy
from unittest import mock

import pytest

from test_war_entry_assessments_bridge import (
    _FakeEndpoint, _declaration, _semantic_snapshot,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.declaration_contract import DECLARE_WAR_CAPABILITY
from xar_autoplayer.bridge.war_entry_contract import EXECUTABLE_SHA256


def new_driver(timeout=120.0):
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint,
        declarable_wars_timeout_seconds=timeout)
    endpoint.publish({
        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
        "pid": 4545, "session_generation": 0, "game_version": "1.19.0.6",
        "executable_sha256": EXECUTABLE_SHA256,
        "capabilities": ["game.state.snapshot", "game.state.declarable-wars",
                         "game.command.query-declarable-wars",
                         DECLARE_WAR_CAPABILITY],
    })
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def result_frame(request_id):
    return {
        "type": "command_result", "protocol_version": 1,
        "request_id": request_id, "ok": True,
        "result": {"step": "query-declarable-wars", "accepted": True,
                   "status": "available", "query_sequence": 1,
                   "declarable_wars": [_declaration(808)]},
    }


def test_declarable_read_omits_history_and_retains_public_history():
    driver, endpoint = new_driver()
    try:
        endpoint.send_hook = lambda frame: endpoint.publish(result_frame(frame["request_id"]))
        driver._command_history.append({"index": 9, "command": "synthetic-prior", "ok": True})
        revision = driver.take_snapshot()["revision"]
        with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError(
            "declarable read exported command history")):
            result = driver.execute_step("query-declarable-wars", expected_revision=revision)
        assert result["status"] == "available"
        assert result["declarable_wars"][0]["declaration_id"] == "808-17-0"
        public = driver.take_snapshot()
        assert public["declarable_wars"] == result["declarable_wars"]
        assert any(row.get("command") == "synthetic-prior"
                   for row in public["native_command_history"])
    finally:
        driver.close()


def test_declarable_late_result_collect_omits_history_and_keeps_binding():
    driver, endpoint = new_driver(timeout=0.001)
    try:
        revision = driver.take_snapshot()["revision"]
        with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError(
            "declarable query exported command history")):
            with pytest.raises(BridgeUnavailableError, match="retained_declaration_query="):
                driver.execute_step("query-declarable-wars", expected_revision=revision)
        pending = driver.diagnostics()["pending_declaration_query"]
        request_id = pending["request_id"]
        endpoint.publish(result_frame(request_id))
        with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError(
            "declarable collection exported command history")):
            collected = driver.collect_declarable_wars_result_v1(
                request_id, expected_revision=revision)
        assert collected["status"] == "available"
        assert collected["cache_restored"] is True
        assert collected["native_resubmitted"] is False
    finally:
        driver.close()


def test_declarable_collect_rejects_changed_binding_without_full_history():
    driver, endpoint = new_driver(timeout=0.001)
    try:
        starting = driver.take_snapshot()
        with pytest.raises(BridgeUnavailableError, match="retained_declaration_query="):
            driver.execute_step("query-declarable-wars", expected_revision=starting["revision"])
        request_id = driver.diagnostics()["pending_declaration_query"]["request_id"]
        endpoint.publish(result_frame(request_id))
        changed = copy.deepcopy(starting)
        changed["diagnostics"]["connection_generation"] += 1
        with mock.patch.object(driver, "take_snapshot_without_native_command_history",
                               return_value=changed):
            result = driver.collect_declarable_wars_result_v1(
                request_id, expected_revision=changed["revision"])
        assert result["status"] == "stale"
        assert result["cache_restored"] is False
    finally:
        driver.close()


def test_declare_business_branch_still_requests_full_history():
    driver, endpoint = new_driver()
    try:
        endpoint.send_hook = lambda frame: endpoint.publish(result_frame(frame["request_id"]))
        revision = driver.take_snapshot()["revision"]
        driver.execute_step("query-declarable-wars", expected_revision=revision)
        with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError(
            "declare business branch retained full history")):
            with pytest.raises(AssertionError, match="declare business branch"):
                driver.execute_step("declare-war-808-17-0", expected_revision=revision)
    finally:
        driver.close()
