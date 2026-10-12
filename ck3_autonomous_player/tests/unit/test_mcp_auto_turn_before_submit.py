"""Registered MCP path: decisions publish before the real selected Driver send."""
import asyncio
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.mcp_server import create_server
from test_prewar_force_transport_v2 import _harness, _response, STEP
from test_service_prewar_prefetch_v2 import NativeFacade
from test_native_bridge_driver import _snapshot, _war


class HookNativeFacade(NativeFacade):
    """Synthetic endpoint responses; all planning and selected Driver dispatch run."""
    def __init__(self, *args, trace, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace = trace
        self.selected_submissions = []
        self.endpoint.send_hook = self.answer

    def answer(self, request):
        if request["step"] == STEP:
            self.trace.append("readonly-prefetch")
            self.endpoint.publish(_response(request, self.before, self.declaration))
            return
        expected_step = "declare-war-" + self.declaration["declaration_id"]
        assert request["step"] == expected_step
        self.trace.append("selected-submit")
        self.selected_submissions.append(deepcopy(request))
        self.endpoint.publish({"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": {
                "step": request["step"], "accepted": True, "status": "submitted"}})
        self.endpoint.publish(_snapshot(41,
            played_character=deepcopy(self.before["played_character"]),
            date_raw=self.before["date_raw"], active_wars=[_war(73)]))

    def execute_step(self, step, *, expected_revision=None):
        return self.native.execute_step(step, expected_revision=expected_revision)


def _registered(trace, callback):
    driver, endpoint, before, declaration, template = _harness(bridge_version="0.1.0.4")
    try:
        facade = HookNativeFacade(driver, endpoint, before, declaration, template, trace=trace)
        server = create_server(facade, before_auto_turn_submit=callback)
    except BaseException:
        driver.close()
        raise
    return server, facade, driver, endpoint, before, declaration


def test_real_mcp_auto_turn_publishes_decision_before_selected_native_submission():
    trace, published = [], []

    def publish(payload):
        trace.append("decision-published")
        published.append(deepcopy(payload))
        # The callback receives a detached plan, not the plan used for submission.
        payload["plan"]["selected_step"] = "synthetic-publisher-mutation"
        return None

    server, facade, driver, endpoint, before, declaration = _registered(trace, publish)
    try:
        response = asyncio.run(server.call_tool("ck3_auto_turn", {}))
        step = "declare-war-" + declaration["declaration_id"]
        assert response.structured_content["status"] == "executed"
        assert response.structured_content["selected_step"] == step
        assert response.structured_content["plan"]["selected_step"] == step
        assert trace == ["readonly-prefetch", "decision-published", "selected-submit"]
        assert len(published) == len(facade.selected_submissions) == 1
        assert set(published[0]) == {"plan", "selected_step", "snapshot_id", "revision"}
        assert published[0]["selected_step"] == step
        assert published[0]["snapshot_id"] == before["snapshot_id"]
        assert published[0]["revision"] == before["revision"]
        assert published[0]["plan"]["decision"]["outcome"] == "DECLARE"
        assert facade.selected_submissions[0]["expected_revision"] == before["native_revision"]
        assert len(facade.query_calls) == 1 and len(endpoint.frames) == 2
    finally:
        driver.close()


def test_real_mcp_auto_turn_publisher_failure_prevents_selected_native_submission():
    trace, published = [], []

    def fail_publish(payload):
        trace.append("decision-publish-failed")
        published.append(deepcopy(payload))
        raise RuntimeError("synthetic decision publisher failed before selected submission")

    server, facade, driver, endpoint, before, declaration = _registered(trace, fail_publish)
    try:
        # MCP may wrap the callback error in its tool exception; its exact message
        # and the selected submission boundary remain observable.
        with pytest.raises(Exception, match="synthetic decision publisher failed before selected submission"):
            asyncio.run(server.call_tool("ck3_auto_turn", {}))
        assert trace == ["readonly-prefetch", "decision-publish-failed"]
        assert len(published) == 1
        assert published[0]["selected_step"] == "declare-war-" + declaration["declaration_id"]
        assert published[0]["revision"] == before["revision"]
        assert facade.selected_submissions == []
        assert len(facade.query_calls) == len(endpoint.frames) == 1
        assert endpoint.frames[0]["step"] == STEP
    finally:
        driver.close()
