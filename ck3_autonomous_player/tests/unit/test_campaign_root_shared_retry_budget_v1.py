"""Real outer Service wrapper plus guarded inner reads; synthetic backend only."""
from copy import deepcopy
from pathlib import Path
import sys
from unittest import mock

import pytest
import test_campaign_root_terminal_retry_v1 as base
from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge import readonly_planning_retry_v1 as retry


def planned(frame):
    return {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
            "plan": {"selected_step": "life-advance"}}


def setup(kind, mode):
    if kind == "initial":
        driver = base.legacy._InternalRejectedSuccessionRootDriver(
            drift="date" if mode == "decline" else None)
        base.prepare_internal_fixture(driver)
    else:
        driver = base.legacy._RejectedRootDriver(drift="date" if mode == "decline" else None)
        driver.allow_private_current_first_heir_betrothal_fulfillment = True
    driver.first_error = base.error_for()
    service = GameplayBridgeService(driver)
    errors, plans = [], []
    if mode in {"second", "outer", "action"}:
        def reject(step, *, expected_revision=None):
            driver.calls.append((step, expected_revision))
            error = base.error_for(driver.current["native_revision"])
            if mode == "action":
                error.native_request_frame["step"] = "move-army-1-to-2"
            driver.current["native_command_history"].append({
                "index": len(driver.current["native_command_history"]) + 1,
                "command": step, "ok": False, "error": f"_NativeCommandRejectedError: {error}"})
            errors.append(error)
            raise error
        driver.execute_step = reject

    def once(**_kwargs):
        plans.append(True)
        if mode == "outer" and len(plans) == 1:
            driver.execute_step(base.STEP, expected_revision=500)
        frame = driver.take_snapshot()
        if kind == "initial":
            current = service._prepare_succession_transition_v1(
                driver.take_internal_semantic_snapshot(), {base.STEP, "life-advance"})
            return planned(current)
        return service._plan_private_family_opportunity_v1(planned(frame), frame)
    service._plan_turn_internal_without_readonly_retry_v1 = once

    def root_only(_driver, current, _snapshot, **_kwargs):
        _driver.execute_step(base.STEP, expected_revision=current["revision"])
        return {**current, "plan": {**current["plan"], "current_betrothal_fulfillment": True}}
    return service, driver, errors, plans, root_only


def run(service, root_only):
    with mock.patch("xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private",
                    side_effect=root_only), mock.patch.object(service, "_plan_private_family_education_v1",
                    side_effect=lambda current, *_a, **_k: current):
        # The actual production outer wrapper owns the ContextVar lifetime.
        return service._plan_turn_internal()


@pytest.mark.parametrize("kind", ["initial", "family"])
@pytest.mark.parametrize("mode", ["second", "outer", "decline", "action"])
def test_real_outer_and_inner_share_one_budget(kind, mode):
    service, driver, errors, plans, root_only = setup(kind, mode)
    assert retry._RETRY_BUDGET.get() is None
    with pytest.raises(_NativeCommandRejectedError) as caught:
        run(service, root_only)
    expected_reads = 2 if mode in {"second", "outer"} else 1
    assert len(driver.calls) == expected_reads
    assert len(plans) == (2 if mode == "outer" else 1)
    assert driver.wait_count == (1 if mode in {"second", "decline"} else 0)
    if mode == "second":
        assert caught.value is errors[0] and "second_error" in caught.value.read_only_query_retry
    elif mode == "outer":
        assert caught.value.read_only_query_retry_decline["reason"] == "shared_readonly_retry_budget_exhausted"
    assert retry._RETRY_BUDGET.get() is None


@pytest.mark.parametrize("kind", ["initial", "family"])
def test_inner_success_does_not_claim_a_whole_planner_replan(kind):
    service, driver, _errors, plans, root_only = setup(kind, "success")
    result = run(service, root_only)
    assert len(driver.calls) == 2 and len(plans) == 1 and driver.wait_count == 1
    assert "readonly_planning_replan_v1" not in result
    assert retry._RETRY_BUDGET.get() is None


def test_true_outer_replan_keeps_its_existing_audit():
    calls = []
    service = GameplayBridgeService(base.legacy._RejectedRootDriver())
    def once(**_kwargs):
        calls.append(True)
        if len(calls) == 1:
            raise base.legacy.BridgeUnavailableError(retry._HEIR_PRECONDITION)
        return planned(service.driver.take_snapshot())
    service._plan_turn_internal_without_readonly_retry_v1 = once
    result = service._plan_turn_internal()
    assert len(calls) == 2 and result["readonly_planning_replan_v1"]["fresh_replans"] == 1
    assert retry._RETRY_BUDGET.get() is None


def test_selected_root_outside_planning_retains_only_its_existing_once_read():
    driver = base.legacy._RejectedRootDriver(second_reject=True)
    driver.first_error = base.error_for()
    with pytest.raises(_NativeCommandRejectedError):
        base.selected_service(driver).auto_turn()
    assert len(driver.calls) == 2 and driver.wait_count == 1
    assert retry._RETRY_BUDGET.get() is None
