"""Real fixed-popup Driver/cache/MCP path; only native endpoint replies are synthetic."""
import asyncio
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_declared_overview_contract import (
    QUERY_STEP, CLOSE_STEP, QUERY_CAPABILITY, CLOSE_CAPABILITY, OWNER_RECEIPT_KEY,
)
from xar_autoplayer.ordinary_war_declared_overview_v1 import war_declared_overview_presence_v1
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from test_ordinary_prewar_force_admission_v2 import _evidence

NATIVE_GENERATION = 17


def _harness():
    template, declaration, _, _ = _evidence()
    template = deepcopy(template)
    template.pop("prewar_force_coalition_coverage_v2_query")
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        command_timeout_seconds=.1)
    hello = _hello("game.state.snapshot", "game.state.declarable-wars",
        "game.command.query-declarable-wars", "game.command.declare-war-N",
        "game.command.query-prewar-force-coalition-coverage-v2-N", QUERY_CAPABILITY, CLOSE_CAPABILITY)
    hello.update(bridge_version="0.1.0.4", expected_ck3_version=CK3_12004.game_version,
        expected_ck3_sha256=CK3_12004.executable_sha256, connection_generation=NATIVE_GENERATION)
    endpoint.publish(hello)
    endpoint.publish(_snapshot(40, played_character=deepcopy(template["played_character"]),
        date_raw=template["date_raw"]))
    def catalogue(request):
        assert request["step"] == "query-declarable-wars"
        endpoint.publish({"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": {
                "step": request["step"], "accepted": True, "status": "available",
                "query_sequence": 3, "declarable_wars": [deepcopy(declaration)]}})
    endpoint.send_hook = catalogue
    driver.execute_step("query-declarable-wars", expected_revision=driver.take_snapshot()["revision"])
    before = driver.take_internal_semantic_snapshot()
    rows, sequence = driver._declarable_wars_cache_for_snapshot(before,
        episode_run_id=before["episode_run_id"])
    assert sequence == 3 and len(rows) == 1
    endpoint.frames.clear()
    endpoint.send_hook = None
    return driver, endpoint, before, rows[0], template


def _reply(request, before, *, presence="visible", operation="query", pending=False, unavailable=False):
    # This independent expected owner execution record is separate from the DTO.
    receipt = {"request_id": request["request_id"], "ticket_sequence": 13,
        "executor_started_sequence": 13, "completed_sequence": 13,
        "pump_epoch": 23, "thread_id": 31, "date_raw": before["date_raw"],
        "connection_generation": NATIVE_GENERATION}
    present, visible = presence != "absent", presence == "visible"
    source = "guarded_registered_top_level" if present else "guarded_top_level_and_complete_owner_tree"
    closed = operation == "close" and not pending and not unavailable and presence == "visible"
    leaf = {"schema": "ck3-war-declared-overview-v1", "operation": operation,
        "window_name": "war_declared_overview", "available": True,
        "accepted": operation == "query" or closed,
        "root_observed": True, "window_present": present, "effective_visible": visible,
        "dispatch_attempted": closed or pending, "dispatch_invoked": closed or pending,
        "native_handled": False, "post_observed": not pending,
        "post_window_present": False if closed else present,
        "post_effective_visible": False if closed else visible,
        "scope_unchanged": not pending, "closure_verified": closed,
        "application_owner_thread_verified": True,
        "button_name": "button_close" if closed or pending else "",
        "status": "closed_verified" if closed else "verification_pending" if pending else
            presence if operation == "query" else "already_" + presence,
        "unavailable_reason": "war_declared_close_not_post_verified" if pending else "",
        "played_character_id": before["played_character"]["character_id"],
        "date_raw": before["date_raw"], "paused": True, "native_revision": before["native_revision"],
        "connection_generation": NATIVE_GENERATION, "pump_epoch": 23, "thread_id": 31,
        "ticket_sequence": 13, "request_id": request["request_id"],
        "root_observation_source": source,
        "post_observation_source": "guarded_top_level_and_complete_owner_tree" if closed else "" if pending else source,
        "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256}
    if pending:
        leaf.update(available=False, accepted=False)
    if unavailable:
        leaf.update(available=False, accepted=False, root_observed=False, window_present=False,
            effective_visible=False, post_observed=False, post_window_present=False,
            post_effective_visible=False, scope_unchanged=False, root_observation_source="",
            post_observation_source="", status="unavailable", unavailable_reason="war_declared_window_read_failed")
    return {"type": "command_result", "protocol_version": 1, "request_id": request["request_id"],
        "ok": True, OWNER_RECEIPT_KEY: receipt, "result": leaf}


def _query(driver, before):
    return driver.query_war_declared_overview_v1(expected_revision=before["revision"])


def test_actual_outer_five_key_send_matches_independent_owner_receipt_and_detached_cache():
    driver, endpoint, before, _, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_reply(request, before))
    try:
        result = _query(driver, before)
        assert len(endpoint.frames) == 1
        wire = endpoint.frames[0]
        assert set(wire) == {"type", "protocol_version", "request_id", "step", "expected_revision"}
        assert wire["type"] == "execute_step" and wire["protocol_version"] == 1
        assert wire["step"] == QUERY_STEP and wire["expected_revision"] == before["native_revision"]
        assert result["native_request_id"] == wire["request_id"]
        assert result["native_command_result"][OWNER_RECEIPT_KEY]["request_id"] == wire["request_id"]
        cached = driver.get_current_war_declared_overview_v1()
        assert war_declared_overview_presence_v1(cached) == "visible"
        cached["native_command_result"][OWNER_RECEIPT_KEY]["thread_id"] = 999
        result["post_effective_visible"] = False
        public = driver.take_snapshot()
        public["war_declared_overview_v1_observation"]["post_effective_visible"] = False
        actual = driver.get_current_war_declared_overview_v1()
        assert actual["post_effective_visible"] is True
        assert actual["native_command_result"][OWNER_RECEIPT_KEY]["thread_id"] == 31
    finally:
        driver.close()


@pytest.mark.parametrize("corruption", ["missing_receipt", "request", "not_started", "leaf_pump",
    "actor", "owner", "false_absence", "boolean"])
def test_wrong_owner_receipt_or_native_lease_never_publishes_cache(corruption):
    driver, endpoint, before, _, _ = _harness()
    def answer(request):
        reply = _reply(request, before, presence="absent" if corruption == "false_absence" else "visible")
        if corruption == "missing_receipt": reply.pop(OWNER_RECEIPT_KEY)
        elif corruption == "request": reply[OWNER_RECEIPT_KEY]["request_id"] = "wrong-request"
        elif corruption == "not_started": reply[OWNER_RECEIPT_KEY]["executor_started_sequence"] = 14
        elif corruption == "leaf_pump": reply["result"]["pump_epoch"] = 24
        elif corruption == "actor": reply["result"]["played_character_id"] += 1
        elif corruption == "owner": reply["result"]["application_owner_thread_verified"] = False
        elif corruption == "false_absence": reply["result"]["root_observation_source"] = "guarded_registered_top_level"
        else: reply["result"]["post_observed"] = 1
        endpoint.publish(reply)
    endpoint.send_hook = answer
    try:
        with pytest.raises(BridgeUnavailableError): _query(driver, before)
        assert driver.get_current_war_declared_overview_v1() is None
        assert len(endpoint.frames) == 1
        assert driver.get_current_war_declared_overview_v1_query_attempt()["status"] == "failed"
    finally:
        driver.close()


@pytest.mark.parametrize("lease", ["snapshot_id", "revision", "native_revision", "date_raw",
    "actor", "connection_generation", "episode_run_id"])
def test_cached_observation_cannot_rebind_to_any_changed_public_lease(lease):
    driver, endpoint, before, _, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_reply(request, before))
    try:
        _query(driver, before)
        changed = deepcopy(driver.take_internal_semantic_snapshot())
        if lease == "actor": changed["played_character"]["character_id"] += 1
        elif lease == "connection_generation": changed["diagnostics"]["connection_generation"] += 1
        elif lease in {"snapshot_id", "episode_run_id"}: changed[lease] += "-another"
        else: changed[lease] += 1
        assert driver.get_current_war_declared_overview_v1(changed) is None
        assert war_declared_overview_presence_v1(driver.get_current_war_declared_overview_v1()) == "visible"
    finally:
        driver.close()


def test_native_read_failure_remains_unknown_and_never_becomes_absent():
    driver, endpoint, before, _, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_reply(request, before, unavailable=True))
    try:
        result = _query(driver, before)
        assert result["available"] is False and result["status"] == "unavailable"
        assert war_declared_overview_presence_v1(driver.get_current_war_declared_overview_v1()) == "unknown"
    finally:
        driver.close()


def test_changed_actual_frame_after_query_refuses_publication():
    driver, endpoint, before, _, _ = _harness()
    def answer(request):
        endpoint.publish(_snapshot(41, played_character=deepcopy(before["played_character"]),
            date_raw=before["date_raw"] + 1))
        endpoint.publish(_reply(request, before))
    endpoint.send_hook = answer
    try:
        with pytest.raises(BridgeUnavailableError, match="lease|superseded"):
            _query(driver, before)
        assert driver.get_current_war_declared_overview_v1() is None
        assert len(endpoint.frames) == 1
    finally:
        driver.close()


def test_public_mcp_ack_without_post_close_proof_never_clears_blocker_or_resends_close():
    driver, endpoint, before, _, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_reply(request, before,
        operation="close" if request["step"] == CLOSE_STEP else "query",
        pending=request["step"] == CLOSE_STEP))
    try:
        _query(driver, before)
        server = create_server(driver)
        response = asyncio.run(server.call_tool("ck3_close_war_declared_overview_v1",
            {"expected_revision": before["revision"]}))
        assert response.structured_content["closure_verified"] is False
        assert response.structured_content["accepted"] is False
        snapshot = driver.take_internal_semantic_snapshot()
        assert snapshot["war_declared_overview_v1_close_pending"] is not None
        assert war_declared_overview_presence_v1(snapshot["war_declared_overview_v1_observation"]) == "unknown"
        with pytest.raises(Exception, match="previous close remains unresolved"):
            asyncio.run(server.call_tool("ck3_close_war_declared_overview_v1",
                {"expected_revision": before["revision"]}))
        assert [request["step"] for request in endpoint.frames] == [QUERY_STEP, CLOSE_STEP]
    finally:
        driver.close()


def test_fresh_hidden_query_does_not_consume_unconfirmed_original_close_latch():
    driver, endpoint, before, _, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_reply(request, before,
        operation="close", pending=True))
    try:
        driver.close_war_declared_overview_v1(expected_revision=before["revision"])
        original = driver.take_internal_semantic_snapshot()["war_declared_overview_v1_close_pending"]["native_request_id"]
        endpoint.send_hook = lambda request: endpoint.publish(_reply(request, before, presence="hidden"))
        _query(driver, before)
        current = driver.take_internal_semantic_snapshot()
        assert war_declared_overview_presence_v1(current["war_declared_overview_v1_observation"]) == "hidden"
        assert current["war_declared_overview_v1_close_pending"]["native_request_id"] == original
        with pytest.raises(BridgeUnavailableError, match="previous close remains unresolved"):
            driver.close_war_declared_overview_v1(expected_revision=before["revision"])
        assert [request["step"] for request in endpoint.frames] == [CLOSE_STEP, QUERY_STEP]
    finally:
        driver.close()
