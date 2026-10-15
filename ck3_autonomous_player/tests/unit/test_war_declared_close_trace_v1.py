"""Fixed Close callback traces preserve owner proof and business postconditions."""

from copy import deepcopy

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from test_war_declared_overview_transport import _harness, _reply


@pytest.mark.parametrize("operation,presence", [("query", "visible"), ("close", "hidden")])
def test_non_dispatch_observations_have_no_close_callback(operation, presence):
    driver, endpoint, before, _, _ = _harness()

    def answer(request):
        frame = _reply(request, before, operation=operation, presence=presence)
        frame["result"].update(close_stage="not_attempted", close_exception_code=0)
        endpoint.publish(frame)

    endpoint.send_hook = answer
    try:
        method = driver.query_war_declared_overview_v1 if operation == "query" else driver.close_war_declared_overview_v1
        result = method(expected_revision=before["revision"])
        assert result["available"] and result["close_stage"] == "not_attempted"
        assert not result["dispatch_attempted"] and not result["closure_verified"]
    finally:
        driver.close()


@pytest.mark.parametrize("stage,code,invoked", [
    ("preflight_rejected", 0, False),
    ("callback_exception", 0xC0000005, False),
    ("callback_returned", 0, True),
])
def test_real_driver_accepts_close_trace_without_crediting_visible_window(stage, code, invoked):
    driver, endpoint, before, _, _ = _harness()

    def answer(request):
        frame = _reply(request, before, operation="close", pending=True)
        frame["result"].update(close_stage=stage, close_exception_code=code,
            dispatch_invoked=invoked, native_handled=invoked,
            post_observed=True, scope_unchanged=True,
            post_observation_source="guarded_registered_top_level")
        endpoint.publish(frame)

    endpoint.send_hook = answer
    try:
        result = driver.close_war_declared_overview_v1(expected_revision=before["revision"])
        assert result["close_stage"] == stage
        assert result["status"] == "verification_pending"
        assert not result["accepted"] and not result["closure_verified"]
        assert len(endpoint.frames) == 1
    finally:
        driver.close()


def test_close_callback_requires_independent_hidden_post_readback():
    driver, endpoint, before, _, _ = _harness()

    def answer(request):
        frame = _reply(request, before, operation="close")
        frame["result"].update(close_stage="callback_returned", close_exception_code=0,
            native_handled=True)
        endpoint.publish(frame)

    endpoint.send_hook = answer
    try:
        result = driver.close_war_declared_overview_v1(expected_revision=before["revision"])
        assert result["closure_verified"] and result["status"] == "closed_verified"
        assert result["post_effective_visible"] is False
    finally:
        driver.close()


@pytest.mark.parametrize("mutation", [
    {"close_exception_code": 0xC0000005},
    {"close_stage": "callback_exception"},
    {"dispatch_invoked": False, "native_handled": False},
    {"post_effective_visible": True},
    {"close_exception_code": True},
    {"close_stage": "guessed"},
    {"extra": True},
])
def test_forged_close_trace_never_publishes_verified_closure(mutation):
    driver, endpoint, before, _, _ = _harness()

    def answer(request):
        frame = _reply(request, before, operation="close")
        frame["result"].update(close_stage="callback_returned", close_exception_code=0,
            native_handled=True)
        frame["result"].update(deepcopy(mutation))
        endpoint.publish(frame)

    endpoint.send_hook = answer
    try:
        with pytest.raises(BridgeUnavailableError):
            driver.close_war_declared_overview_v1(expected_revision=before["revision"])
        assert driver.get_current_war_declared_overview_v1() is None
        assert len(endpoint.frames) == 1
    finally:
        driver.close()
