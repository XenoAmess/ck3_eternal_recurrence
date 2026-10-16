"""Failed optional UI reads retain unknown visibility and their Native request ID."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from xar_autoplayer import ordinary_war_declared_overview_v1 as overview
from xar_autoplayer import ordinary_war_results_window_v1 as results
from xar_autoplayer.bridge.war_declared_overview_contract import QUERY_STEP
from test_war_declared_overview_priority import _service

ACTUAL = json.loads((Path(__file__).parent / "fixtures/optional_war_ui_read_failure_actual_projection.json").read_text(encoding="utf-8"))["snapshot"]


def settings(module, prefix):
    return {"action_steps": (getattr(module, "QUERY_" + prefix + "_STEP"), getattr(module, "CLOSE_" + prefix + "_STEP")),
            "bridge_capabilities": (getattr(module, "QUERY_" + prefix + "_CAPABILITY"), getattr(module, "CLOSE_" + prefix + "_CAPABILITY"))}


@pytest.mark.parametrize("module,prefix,schema", [
    (overview, "WAR_DECLARED_OVERVIEW_V1", "war-declared-overview"),
    (results, "WAR_RESULTS_WINDOW_V1", "war-results-window"),
])
def test_failed_lease_defers_but_visible_pending_and_new_frame_stay_strict(module, prefix, schema):
    snapshot = deepcopy(ACTUAL)
    keys = getattr(module, prefix + "_PUBLIC_KEYS")
    planner = getattr(module, "plan_ordinary_" + schema.replace("-", "_") + "_v1")
    snapshot["war_results_window_v1_check_due"] = True
    snapshot[keys[1]] = {"validation_schema": schema + "-query-attempt-v1",
                         "status": "failed", **module._binding(snapshot)}
    # The overview positive's source values are the real SEM105 lease.
    if module is overview: snapshot[keys[1]] = deepcopy(ACTUAL[keys[1]])
    assert planner(snapshot, **settings(module, prefix)) is None
    assert module.__dict__[schema.replace("-", "_") + "_presence_v1"](snapshot.get(keys[0])) == "unknown"
    changed = deepcopy(snapshot); changed["revision"] += 1
    assert planner(changed, **settings(module, prefix))["selected_step"] == getattr(module, "QUERY_" + prefix + "_STEP")
    snapshot[keys[0]] = {"sdk_validation_schema": schema + "-source-v1", **module._binding(snapshot),
                         "available": True, "post_observed": True, "scope_unchanged": True,
                         "post_window_present": True, "post_effective_visible": True}
    assert planner(snapshot, **settings(module, prefix))["selected_step"] == getattr(module, "CLOSE_" + prefix + "_STEP")
    snapshot[keys[2]] = {"native_request_id": "synthetic-prior-close"}
    assert planner(snapshot, **settings(module, prefix))["status"] == "pending"
    del snapshot[keys[0]]
    assert planner(snapshot, **settings(module, prefix)) is not None


def test_real_service_plan_and_native_query_replan_once_on_state_changed():
    service, facade, driver, endpoint, before = _service()
    try:
        assert before["revision"] != before["native_revision"]
        answer = facade.answer
        def fail(request):
            if request["step"] == QUERY_STEP:
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": request["request_id"], "ok": False, "error": "state_changed"})
            else: answer(request)
        endpoint.send_hook = fail
        planned = service.plan_turn()
        assert planned["revision"] == before["revision"]
        assert endpoint.frames[0]["expected_revision"] == before["native_revision"]
        assert sum(row["step"] == QUERY_STEP for row in endpoint.frames) == 1
        assert planned["plan"]["selected_step"] not in (None, QUERY_STEP)
        deferred = planned["plan"]["war_declared_overview_query"]
        assert deferred["status"] == "technical_read_deferred" and deferred["request_retried"] is False
        assert deferred["failed_attempt"]["native_request_id"] == endpoint.frames[0]["request_id"]
        assert deferred["failed_attempt"]["queried_native_revision"] == before["native_revision"]
        assert driver.get_current_war_declared_overview_v1(before) is None
        assert not any("close-war" in row["step"] for row in endpoint.frames)
    finally: driver.close()


def test_unqualified_first_read_error_is_not_reported_as_absent_or_success():
    service, facade, driver, endpoint, _ = _service()
    try:
        answer = facade.answer
        def fail(request):
            if request["step"] == QUERY_STEP:
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": request["request_id"], "ok": False,
                                  "error": "war_declared_owner_submission_or_completion_failed"})
            else: answer(request)
        endpoint.send_hook = fail
        plan = service.plan_turn()["plan"]
        assert plan["selected_step"] is None
        assert plan["war_declared_overview_query"]["status"] == "failed"
        assert sum(row["step"] == QUERY_STEP for row in endpoint.frames) == 1
    finally: driver.close()
