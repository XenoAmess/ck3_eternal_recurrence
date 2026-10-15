"""Synthetic complete battle frames; real Driver and owned fake endpoint."""
from contextlib import ExitStack
from unittest.mock import patch

import pytest

import xar_autoplayer.bridge.native_driver as native_module
import test_battle_control_snapshot_v1_bridge as fixture


@pytest.mark.parametrize("kind", ["success", "fresh_pump", "retry", "retry_drift"])
def test_battle_control_never_copies_unused_history_and_keeps_retry_lease(kind):
    driver, endpoint = fixture._native_driver()
    before = driver.take_snapshot()
    retained = {"command": "synthetic-large-readonly-result", "ok": True,
                "result": {"original_payload": True}}
    driver._command_history.append(retained)
    snapshot_flags = []
    original_snapshot = driver.take_snapshot

    def history_copy_forbidden():
        raise AssertionError("battle-control query copied native command history")

    def read(*args, **kwargs):
        snapshot_flags.append(kwargs.get("include_native_command_history"))
        assert kwargs.get("include_native_command_history") is False
        return original_snapshot(*args, **kwargs)

    driver._history_snapshot = history_copy_forbidden
    driver.take_snapshot = read
    requests = []

    def answer(request):
        if request.get("type") != "execute_step":
            return
        requests.append(request)
        if kind in {"retry", "retry_drift"} and len(requests) == 1:
            if kind == "retry_drift":
                endpoint.publish(fixture._semantic_snapshot(fixture.NATIVE_REVISION + 1))
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": False,
                "error": fixture.TRANSIENT_QUERY_ERROR})
        else:
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": fixture._native_result()})

    endpoint.send_hook = answer
    try:
        with ExitStack() as stack:
            if kind == "fresh_pump":
                capabilities = fixture._r0211_exact_capabilities(driver, advance_after=3)
                elapsed = [0.0]

                def synthetic_wait(provider, baseline, date, *, timeout_seconds):
                    def sleep(_seconds):
                        elapsed[0] += 1.0
                    return fixture.wait_for_verified_pump(provider, baseline, date,
                        timeout_seconds=timeout_seconds, clock=lambda: elapsed[0], sleep=sleep)

                stack.enter_context(patch.object(driver, "capabilities", side_effect=capabilities))
                stack.enter_context(patch.object(native_module, "wait_for_verified_pump", side_effect=synthetic_wait))
            if kind == "retry_drift":
                with pytest.raises(native_module.BridgeUnavailableError, match=fixture.TRANSIENT_QUERY_ERROR):
                    driver.execute_step(fixture.STEP, expected_revision=before["revision"])
            else:
                result = driver.execute_step(fixture.STEP, expected_revision=before["revision"])
                assert result["accepted"] is True and result["status"] == "available"
                assert result["query_sequence"] == 41
                assert driver._battle_control_snapshot_v1_query["status"] == "available"
                recorded = driver._command_history[-1]
                assert recorded["command"] == fixture.STEP and recorded["ok"] is True
                assert recorded["result"]["battle_control_snapshot"] == result["battle_control_snapshot"]
        assert len(requests) == (2 if kind == "retry" else 1)
        assert driver._command_history[0] is retained
        assert retained["result"] == {"original_payload": True}
        assert snapshot_flags and all(flag is False for flag in snapshot_flags)
    finally:
        driver.close()
