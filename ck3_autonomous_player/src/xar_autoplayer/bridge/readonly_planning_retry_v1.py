"""One fresh planning retry for proven read-only frame precondition races."""
from contextvars import ContextVar

from .driver import BridgeUnavailableError, UnsupportedStepError

_RETRY_BUDGET = ContextVar("readonly_planning_retry_budget_v1", default=None)
_HEIR_PRECONDITION = "current heir relationship needs a paused living-player map frame"


def classify_readonly_planning_error_v1(error):
    if str(error) == _HEIR_PRECONDITION:
        return {"class": "heir_readonly_frame_precondition", "business_submission": False}
    from .native_driver import _NativeCommandRejectedError
    if not isinstance(error, _NativeCommandRejectedError) or error.native_error != "state_changed":
        return None
    request = error.native_request_frame
    result = error.native_command_result_frame
    request_id = error.native_request_id
    if (not isinstance(request, dict) or not isinstance(result, dict)
            or not isinstance(request_id, str) or not request_id
            or request.get("type") != "execute_step" or request.get("protocol_version") != 1
            or request.get("request_id") != request_id
            or request.get("step") != "query-campaign-root-context-v1"
            or result.get("type") != "command_result" or result.get("protocol_version") != 1
            or result.get("request_id") != request_id or result.get("ok") is not False
            or result.get("error") != "state_changed"):
        return None
    failure = result.get("campaign_root_preflight_failure_v1")
    predicates = failure.get("predicates") if isinstance(failure, dict) else None
    if (not isinstance(failure, dict) or failure.get("query_type") != "campaign"
            or failure.get("stage") != "preflight_native_snapshot_changed"
            or failure.get("read_attempted") is not True or failure.get("truncated") is not False
            or not isinstance(predicates, dict) or predicates.get("observed_equal") is not False
            or any(predicates.get(key) is not True for key in
                   ("revision_matches", "worker_ready", "previous_present", "observed_read"))
            or type(failure.get("request_native_revision")) is not int
            or failure["request_native_revision"] <= 0
            or failure["request_native_revision"] != failure.get("worker_native_revision")
            or failure["request_native_revision"] != request.get("expected_revision")):
        return None
    return {"class": "campaign_root_preflight_state_changed", "business_submission": False,
            "native_request_id": request_id, "source_native_revision": failure["request_native_revision"],
            "differing_fields": failure.get("differing_fields")}


def retry_readonly_planning_once_v1(plan_once):
    """The callback starts planning from a new snapshot and never executes a plan."""
    budget = _RETRY_BUDGET.get()
    token = None
    if budget is None:
        budget = {"remaining": 1, "rejections": []}
        token = _RETRY_BUDGET.set(budget)
    try:
        while True:
            try:
                planned = plan_once()
                if token is not None and budget["rejections"] and isinstance(planned, dict):
                    planned = {**planned, "readonly_planning_replan_v1": {
                        "schema": "xar.readonly-planning-replan/v1", "fresh_replans": 1,
                        "original_rejections": list(budget["rejections"]),
                        "fresh_snapshot_id": planned.get("snapshot_id"),
                        "fresh_revision": planned.get("revision"), "business_actions_replayed": 0}}
                return planned
            except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
                qualified = classify_readonly_planning_error_v1(error)
                if qualified is None or budget["remaining"] == 0:
                    raise
                budget["remaining"] = 0
                budget["rejections"].append(qualified)
                # Call the whole planner again. Never retain the failed planning
                # view, replay auto_turn, or invoke any execute hook here.
    finally:
        if token is not None:
            _RETRY_BUDGET.reset(token)
