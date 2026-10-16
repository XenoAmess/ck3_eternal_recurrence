"""One fresh planning retry for proven read-only frame precondition races."""
from contextvars import ContextVar
import json
import re

from .driver import (
    BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError,
)

_RETRY_BUDGET = ContextVar("readonly_planning_retry_budget_v1", default=None)
_HEIR_PRECONDITION = "current heir relationship needs a paused living-player map frame"
_CAMPAIGN_ROOT_TYPED_ERROR = "application-main typed query failed or its snapshot changed"


def _campaign_root_executor_not_entered(error):
    """A failed read whose application-main executor never entered Game code."""
    request = error.native_request_frame
    result = error.native_command_result_frame
    request_id = error.native_request_id
    if (not isinstance(request, dict) or not isinstance(result, dict)
            or not isinstance(request_id, str) or not request_id
            or request.get("type") != "execute_step" or request.get("protocol_version") != 1
            or request.get("request_id") != request_id
            or request.get("step") != "query-campaign-root-context-v1"
            or type(request.get("expected_revision")) is not int
            or request["expected_revision"] <= 0
            or result.get("type") != "command_result" or result.get("protocol_version") != 1
            or result.get("request_id") != request_id or result.get("ok") is not False
            or result.get("error") != _CAMPAIGN_ROOT_TYPED_ERROR
            or result.get("result") is not None
            or error.native_raw_return_receipt is not None):
        return None
    failure = result.get("typed_query_failure_v1")
    required = {"executor_enter", "executor_exception", "executor_finish",
                "executor_typed_result", "final_equal", "final_read", "frame_stable",
                "query_type", "stage", "typed_result", "wait_completed", "wait_result"}
    if (not isinstance(failure, dict) or set(failure) != required
            or failure.get("query_type") != "campaign"
            or failure.get("stage") != "wait"
            or failure.get("wait_result") != "executor_failed"
            or failure.get("wait_completed") is not False
            or failure.get("executor_enter") is not False
            or failure.get("executor_exception") != {"code": 0, "image": "none", "rva": None}
            or any(failure.get(key) is not None for key in
                   ("executor_finish", "executor_typed_result", "final_equal",
                    "final_read", "frame_stable", "typed_result"))):
        return None
    diagnostic = json.dumps(failure, sort_keys=True, separators=(",", ":"))
    if error.native_error != _CAMPAIGN_ROOT_TYPED_ERROR + "; typed_query_failure_v1=" + diagnostic:
        return None
    return {"class": "campaign_root_executor_not_entered", "business_submission": False,
            "native_request_id": request_id,
            "source_native_revision": request["expected_revision"],
            "typed_query_failure_v1": failure}


def classify_readonly_planning_error_v1(error):
    if str(error) == _HEIR_PRECONDITION:
        return {"class": "heir_readonly_frame_precondition", "business_submission": False}
    if isinstance(error, PreSubmissionRevisionMismatchError):
        match = re.fullmatch(
            r"campaign-root revision mismatch: expected ([0-9]{1,19}), current ([0-9]{1,19})",
            str(error),
        )
        if match is not None:
            expected, current = map(int, match.groups())
            if (str(expected) == match[1] and str(current) == match[2]
                    and 0 <= expected < current < 2**63):
                return {"class": "campaign_root_local_revision_changed_before_send",
                        "business_submission": False,
                        "expected_public_revision": expected,
                        "current_public_revision": current,
                        "failed_root_query_native_request_sent": False}
    from .native_driver import _NativeCommandRejectedError
    if isinstance(error, _NativeCommandRejectedError):
        not_entered = _campaign_root_executor_not_entered(error)
        if not_entered is not None:
            return not_entered
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
    if isinstance(failure, dict) and failure.get("stage") == "preflight_revision_changed":
        required = {"query_type", "stage", "request_native_revision", "worker_native_revision",
                    "predicates", "read_attempted", "cached_scalars", "observed_scalars",
                    "differing_fields", "truncated"}
        expected_predicates = {"revision_matches": False, "worker_ready": True,
                               "previous_present": True, "observed_read": False,
                               "observed_equal": False}
        if (set(failure) != required or failure.get("query_type") != "campaign"
                or failure.get("read_attempted") is not False
                or failure.get("truncated") is not False
                or type(failure.get("request_native_revision")) is not int
                or type(failure.get("worker_native_revision")) is not int
                or not 0 < failure["request_native_revision"] < failure["worker_native_revision"]
                or failure["request_native_revision"] != request.get("expected_revision")
                or not isinstance(failure.get("cached_scalars"), str)
                or not failure["cached_scalars"]
                or failure.get("observed_scalars") is not None
                or failure.get("differing_fields") is not None
                or not isinstance(predicates, dict) or set(predicates) != set(expected_predicates)
                or any(predicates[k] is not value for k, value in expected_predicates.items())):
            return None
        return {"class": "campaign_root_preflight_revision_changed_before_read",
                "business_submission": False, "native_request_id": request_id,
                "source_native_revision": failure["request_native_revision"],
                "worker_native_revision": failure["worker_native_revision"],
                "read_attempted": False}
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
