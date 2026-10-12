"""Explicit sampling controls through the real Driver, Service and MCP.

Transport replies and preflight observations are synthetic; control execution,
cache publication and the Service/MCP route remain real. These cases establish
control contracts, not successful CK3 capture or military readiness.
"""
from __future__ import annotations

import asyncio
import copy
from contextlib import nullcontext
from dataclasses import dataclass, field
from unittest import mock

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from test_army_profile_cache_regression import CORE, FULL, OBSERVED_PHASE_KEYS, make_scenario
from test_native_bridge_driver import _army, _hello, _snapshot, _war
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    PreSubmissionRevisionMismatchError, UnsupportedStepError,
)
from xar_autoplayer.bridge.version_identity import CK3_12004


ENABLE = "enable-army-gathering-research-sampling-v1"
DISABLE = "disable-army-gathering-research-sampling-v1"
QUERY = "query-army-gathering-research-sampling-v1"
STATE = "army_gathering_research_sampling_v1"
ARMY_CAPABILITY = "game.command.query-army-strengths-v1"
CONTROL_STEPS = {ENABLE, DISABLE, QUERY}
DUE = "native_gathering_due_natural_stage_12004"


def _qualified_hello(*capabilities):
    return {
        **_hello(*capabilities),
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }


def _receipt(step, status, *, accepted):
    # Fixed valid Native examples, not a replacement state machine.
    examples = {
        "enabled": {
            "capture_enabled": True, "busy": False, "clear_completed": False,
            "epoch": 9, "active_captures": 0, "retained_records": 0,
            "qualified_records": 0, "readiness": "awaiting_sample",
        },
        "disabled": {
            "capture_enabled": False, "busy": False, "clear_completed": True,
            "epoch": 10, "active_captures": 0, "retained_records": 0,
            "qualified_records": 0, "readiness": "off",
        },
        "busy": {
            "capture_enabled": False, "busy": True, "clear_completed": False,
            "epoch": 10, "active_captures": 1, "retained_records": 8,
            "qualified_records": 2, "readiness": "off",
        },
        "clear_pending": {
            "capture_enabled": False, "busy": False, "clear_completed": False,
            "epoch": 10, "active_captures": 0, "retained_records": 8,
            "qualified_records": 2, "readiness": "off",
        },
    }
    return {
        "step": step, "accepted": accepted, "status": status,
        STATE: copy.deepcopy(examples[status]), "backend_id": "native-headless",
    }


@dataclass
class SamplingCase:
    army: object
    replies: list[object] = field(default_factory=list)
    requests: list[dict[str, object]] = field(default_factory=list)

    @property
    def driver(self):
        return self.army.driver

    def call(self, method, *, revision=None):
        revision = self.army.before["revision"] if revision is None else revision
        if method == "set":
            return self.driver.set_army_gathering_research_sampling_v1(
                True, expected_revision=revision,
            )
        return self.driver.query_army_gathering_research_sampling_v1(
            expected_revision=revision,
        )


@pytest.fixture
def control(tmp_path):
    army = make_scenario(tmp_path / "driver", projection="native_campaign")
    try:
        # A fresh hello invalidates prior semantic frames, so publish its own
        # fresh snapshot before any Driver query rather than reusing the old one.
        army.endpoint.publish(_qualified_hello("game.state.snapshot", ARMY_CAPABILITY))
        first, second = _army(82), _army(81)
        army.endpoint.publish(_snapshot(
            40, played_character={"character_id": 707, "alive": True},
            player_armies=[first, second],
            active_wars=[_war(45, allied_armies=[second]), _war(46, allied_armies=[second])],
        ))
        army.before = army.driver.take_internal_semantic_snapshot()
        value = SamplingCase(army)
        army_answer = army.endpoint.send_hook

        def answer(frame):
            if frame.get("type") != "execute_step" or frame.get("step") not in CONTROL_STEPS:
                army_answer(frame)
                return
            value.requests.append(copy.deepcopy(frame))
            assert value.replies, "unexpected retry or implicit sampling control"
            reply = value.replies.pop(0)
            army.endpoint.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": copy.deepcopy(reply),
            })

        army.endpoint.send_hook = answer
        army.query()  # Establish a real, formally validated nonempty core cache.
        assert army.cached()["army_strengths"]
        yield value
    finally:
        army.driver.close()


@pytest.mark.parametrize("enabled", [0, 1, None, "true"])
def test_sampling_set_requires_strict_boolean_before_snapshot_or_dispatch(control, enabled):
    before = copy.deepcopy(control.driver._army_strength_query)
    count = len(control.army.endpoint.frames)
    with mock.patch.object(
        control.driver, "take_internal_semantic_snapshot",
        side_effect=AssertionError("invalid input must be rejected before snapshot"),
    ):
        with pytest.raises(ValueError, match="explicit boolean"):
            control.driver.set_army_gathering_research_sampling_v1(
                enabled, expected_revision=control.army.before["revision"],
            )
    assert len(control.army.endpoint.frames) == count
    assert control.requests == []
    assert control.driver._army_strength_query == before


@pytest.mark.parametrize("method", ["set", "query"])
@pytest.mark.parametrize("revision", [True, -1, None, "2", 2.5])
def test_sampling_revision_is_strict_before_snapshot_or_dispatch(control, method, revision):
    before = copy.deepcopy(control.driver._army_strength_query)
    count = len(control.army.endpoint.frames)
    with mock.patch.object(
        control.driver, "take_internal_semantic_snapshot",
        side_effect=AssertionError("invalid revision must precede snapshot"),
    ):
        with pytest.raises(ValueError, match="non-negative integer"):
            if method == "set":
                control.driver.set_army_gathering_research_sampling_v1(
                    True, expected_revision=revision,
                )
            else:
                control.driver.query_army_gathering_research_sampling_v1(
                    expected_revision=revision,
                )
    assert len(control.army.endpoint.frames) == count
    assert control.requests == []
    assert control.driver._army_strength_query == before


@pytest.mark.parametrize("method", ["set", "query"])
@pytest.mark.parametrize("gate", ["paused", "revision", "capability", "version", "sha256"])
def test_sampling_preflight_preserves_core_cache_and_never_dispatches(control, method, gate):
    before = copy.deepcopy(control.driver._army_strength_query)
    snapshot = copy.deepcopy(control.army.before)
    revision = snapshot["revision"]
    capability_observation = nullcontext()
    if gate == "paused":
        snapshot["paused"] = False
        error, message = BridgeUnavailableError, "requires pause"
    elif gate == "revision":
        revision += 1
        error, message = PreSubmissionRevisionMismatchError, "source revision is stale"
    elif gate == "capability":
        # A new hello would itself invalidate the cache before this control.
        # Isolate this local gate by changing only the observed capabilities.
        capabilities = copy.deepcopy(control.driver.state.capabilities())
        capabilities["bridge_capabilities"].remove(ARMY_CAPABILITY)
        capability_observation = mock.patch.object(
            control.driver.state, "capabilities", return_value=capabilities,
        )
        error, message = UnsupportedStepError, "Army query capability"
    else:
        key = "expected_ck3_version" if gate == "version" else "expected_ck3_sha256"
        snapshot["diagnostics"]["hello"][key] = "1.20.0.99" if gate == "version" else "0" * 64
        error, message = BridgeUnavailableError, "frozen exact"
    count = len(control.army.endpoint.frames)
    with capability_observation, mock.patch.object(
        control.driver, "take_internal_semantic_snapshot", return_value=snapshot,
    ):
        with pytest.raises(error, match=message):
            control.call(method, revision=revision)
    assert len(control.army.endpoint.frames) == count
    assert control.requests == []
    assert control.driver._army_strength_query == before


@pytest.mark.parametrize("enabled,step,status", [(True, ENABLE, "enabled"), (False, DISABLE, "disabled")])
def test_explicit_terminal_control_invalidates_previous_army_cache(control, enabled, step, status):
    payload = _receipt(step, status, accepted=True)
    control.replies.append(payload)
    result = control.driver.set_army_gathering_research_sampling_v1(
        enabled, expected_revision=control.army.before["revision"],
    )
    assert [request["step"] for request in control.requests] == [step]
    assert result["accepted"] is True and result["status"] == status
    assert result[STATE] == payload[STATE]
    assert result["queried_revision"] == control.army.before["revision"]
    assert result["queried_native_revision"] == control.army.before["native_revision"]
    assert control.driver._army_strength_query is None
    assert control.driver.take_snapshot()["army_strengths"] == []
    assert control.driver._command_history[-1]["ok"] is True


def test_enabled_busy_repeat_enable_preserves_native_epoch(control):
    payload = _receipt(ENABLE, "enabled", accepted=True)
    payload[STATE].update(busy=True, active_captures=1, readiness="inflight")
    observed = copy.deepcopy(payload)
    observed["step"] = QUERY
    control.replies.extend([observed, payload])
    assert control.call("query")[STATE] == payload[STATE]
    result = control.call("set")
    assert result["accepted"] is True and result["status"] == "enabled"
    assert result[STATE] == payload[STATE]
    assert [r["step"] for r in control.requests] == [QUERY, ENABLE]
    assert control.driver._army_strength_query is None


@pytest.mark.parametrize("status", ["busy", "clear_pending"])
@pytest.mark.parametrize("enabled", [True, False])
def test_native_pending_set_is_not_success_or_retry_but_invalidates_old_cache(control, status, enabled):
    step = ENABLE if enabled else DISABLE
    payload = _receipt(step, status, accepted=False)
    control.replies.append(payload)
    result = control.driver.set_army_gathering_research_sampling_v1(
        enabled, expected_revision=control.army.before["revision"],
    )
    assert [request["step"] for request in control.requests] == [step]
    assert result["accepted"] is False and result["status"] == status
    assert result[STATE] == payload[STATE]
    assert result[STATE]["clear_completed"] is False
    assert result[STATE]["retained_records"] == 8
    assert control.driver._army_strength_query is None
    assert control.driver._command_history[-1]["ok"] is False
    assert control.driver._command_history[-1]["result"][STATE] == payload[STATE]


@pytest.mark.parametrize("status", ["enabled", "disabled", "busy", "clear_pending"])
def test_sampling_query_preserves_actual_state_and_formal_core_cache(control, status):
    before = copy.deepcopy(control.driver._army_strength_query)
    payload = _receipt(QUERY, status, accepted=True)
    control.replies.append(payload)
    result = control.call("query")
    assert [request["step"] for request in control.requests] == [QUERY]
    assert result["accepted"] is True and result["status"] == status
    assert result[STATE] == payload[STATE]
    assert control.driver._army_strength_query == before
    assert control.army.cached()["army_strengths"] == before["army_strengths"]
    assert control.driver._command_history[-1]["ok"] is True


def test_retained_observation_query_reports_sampling_state_without_replacing_army_data(control):
    before = copy.deepcopy(control.driver._army_strength_query)
    payload = _receipt(QUERY, "enabled", accepted=True)
    payload[STATE].update(retained_records=3, qualified_records=2, readiness="retained_observation")
    control.replies.append(payload)
    result = control.call("query")
    assert result[STATE] == payload[STATE]
    assert control.driver._army_strength_query == before
    assert [request["step"] for request in control.requests] == [QUERY]


@pytest.mark.parametrize("method", ["set", "query"])
def test_control_crossing_public_revision_is_failed_once_without_retry(control, method):
    step = ENABLE if method == "set" else QUERY
    control.replies.append(_receipt(step, "enabled", accepted=True))
    original_answer = control.army.endpoint.send_hook
    original_snapshot = control.driver.take_internal_semantic_snapshot
    sent = False

    def answer(frame):
        nonlocal sent
        original_answer(frame)
        if frame.get("type") == "execute_step" and frame.get("step") == step:
            sent = True

    def changed_after():
        snapshot = original_snapshot()
        if sent:
            snapshot = copy.deepcopy(snapshot)
            snapshot["revision"] += 1
        return snapshot

    control.army.endpoint.send_hook = answer
    with mock.patch.object(control.driver, "take_internal_semantic_snapshot", side_effect=changed_after):
        with pytest.raises(BridgeUnavailableError, match="crossed its paused frame"):
            control.call(method)
    assert [request["step"] for request in control.requests] == [step]
    assert control.driver._command_history[-1]["ok"] is False
    if method == "set":
        assert control.driver._army_strength_query is None


@pytest.mark.parametrize("mutation", [
    "scalar", "state_null", "accepted", "counter_bool", "busy",
    "count_limit", "qualified", "clear", "status", "readiness",
])
def test_malformed_native_receipt_is_rejected_once_without_replacement_cache(control, mutation):
    assert control.driver._army_strength_query is not None
    payload = _receipt(ENABLE, "enabled", accepted=True)
    if mutation == "scalar":
        payload = None
    elif mutation == "state_null":
        payload[STATE] = None
    elif mutation == "accepted":
        payload["accepted"] = False
    elif mutation == "counter_bool":
        payload[STATE]["epoch"] = True
    elif mutation == "busy":
        payload[STATE]["active_captures"] = 1
    elif mutation == "count_limit":
        payload[STATE]["retained_records"] = 65
    elif mutation == "qualified":
        payload[STATE].update(retained_records=1, qualified_records=2)
    elif mutation == "clear":
        payload[STATE]["clear_completed"] = True
    elif mutation == "status":
        payload["status"] = "disabled"
    else:
        payload[STATE]["readiness"] = "retained_observation"
    control.replies.append(payload)
    with pytest.raises(BridgeUnavailableError):
        control.call("set")
    assert [request["step"] for request in control.requests] == [ENABLE]
    assert control.driver._army_strength_query is None
    assert control.driver._command_history[-1]["ok"] is False


@pytest.mark.parametrize("failure", ["timeout", "native_error"])
def test_postdispatch_set_failure_has_unknown_outcome_and_discards_previous_cache(control, failure):
    assert control.driver._army_strength_query is not None

    def fail(frame):
        assert frame["type"] == "execute_step" and frame["step"] == ENABLE
        control.requests.append(copy.deepcopy(frame))
        if failure == "native_error":
            control.army.endpoint.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": False,
                "error": "synthetic capture-control failure after dispatch",
            })
        # The timeout case deliberately delivers no reply after the real send.

    control.army.endpoint.send_hook = fail
    with pytest.raises(BridgeUnavailableError):
        control.call("set")
    assert [request["step"] for request in control.requests] == [ENABLE]
    assert control.driver._army_strength_query is None
    assert control.driver._command_history[-1]["ok"] is False
    assert "result" not in control.driver._command_history[-1]


def test_ordinary_and_full_queries_do_not_implicitly_enable_or_disable_sampling(control):
    full = control.army.query(FULL)
    assert all(key in row for row in full["army_strengths"] for key in OBSERVED_PHASE_KEYS)
    assert all(row[DUE] is None for row in full["army_strengths"])
    ordinary = control.army.query(CORE)
    assert not any(key in row for row in ordinary["army_strengths"] for key in OBSERVED_PHASE_KEYS)
    assert control.requests == []
    assert all(
        frame["step"] == "query-army-strengths-v1"
        for frame in control.army.endpoint.frames if frame.get("type") == "execute_step"
    )


def test_disabled_capture_with_full_null_observations_remains_unknown(control):
    control.replies.append(_receipt(QUERY, "disabled", accepted=True))
    state = control.call("query")[STATE]
    full = control.army.query(FULL)
    assert state["capture_enabled"] is False and state["readiness"] == "off"
    assert state["qualified_records"] == 0
    assert all(key in row for row in full["army_strengths"] for key in OBSERVED_PHASE_KEYS)
    assert all(row[DUE] is None for row in full["army_strengths"])
    assert [request["step"] for request in control.requests] == [QUERY]


def test_enable_ack_does_not_prove_a_later_sample_or_army_readiness(control):
    control.replies.append(_receipt(ENABLE, "enabled", accepted=True))
    receipt = control.call("set")
    assert receipt["accepted"] is True
    assert receipt[STATE]["readiness"] == "awaiting_sample"
    assert receipt[STATE]["qualified_records"] == 0
    full = control.army.query(FULL)
    assert all(row[DUE] is None for row in full["army_strengths"])
    assert [request["step"] for request in control.requests] == [ENABLE]


def test_registered_control_tools_route_native_pending_state_without_retry(control):
    server = create_server(control.driver)
    names = {tool.name for tool in asyncio.run(server.list_tools())}
    setter = "ck3_set_army_gathering_research_sampling_v1"
    query = "ck3_query_army_gathering_research_sampling_v1"
    assert {setter, query} <= names
    before = copy.deepcopy(control.driver._army_strength_query)
    with pytest.raises(ToolError):
        asyncio.run(server.call_tool(setter, {
            "enabled": 1, "expected_revision": control.army.before["revision"],
        }))
    assert control.requests == []
    assert control.driver._army_strength_query == before

    pending = _receipt(DISABLE, "clear_pending", accepted=False)
    control.replies.append(pending)
    response = asyncio.run(server.call_tool(setter, {
        "enabled": False, "expected_revision": control.army.before["revision"],
    }))
    assert response.is_error is False
    assert response.structured_content["accepted"] is False
    assert response.structured_content["status"] == "clear_pending"
    assert response.structured_content[STATE] == pending[STATE]
    assert [request["step"] for request in control.requests] == [DISABLE]
    assert control.driver._army_strength_query is None

    # A fresh ordinary query is explicit and creates a formal cache again.
    control.army.query()
    before_query = copy.deepcopy(control.driver._army_strength_query)
    observed = _receipt(QUERY, "clear_pending", accepted=True)
    control.replies.append(observed)
    queried = asyncio.run(server.call_tool(query, {
        "expected_revision": control.army.before["revision"],
    }))
    assert queried.is_error is False and queried.structured_content["accepted"] is True
    assert queried.structured_content[STATE] == observed[STATE]
    assert [request["step"] for request in control.requests] == [DISABLE, QUERY]
    assert control.driver._army_strength_query == before_query
