"""Recognize one received, terminal campaign read rejection for existing retry.

This does not retry, change the SourceProfile, claim an unread field or permit
another command. The caller still owns every original fresh-frame/history gate.
"""
from __future__ import annotations

import json


def is_campaign_root_terminal_rejection_v1(error: BaseException, starting: object) -> bool:
    """Use the original in-memory exception frames, never an error-text prefix."""
    from .native_driver import _NativeCommandRejectedError

    if not isinstance(error, _NativeCommandRejectedError) or not isinstance(starting, dict):
        return False
    native_revision = starting.get("native_revision")
    if type(native_revision) is not int or native_revision <= 0:
        return False
    request = error.native_request_frame
    response = error.native_command_result_frame
    if not isinstance(request, dict) or not isinstance(response, dict):
        return False
    request_id = request.get("request_id")
    if not (
        request.get("type") == "execute_step"
        and type(request.get("protocol_version")) is int
        and request["protocol_version"] == 1
        and isinstance(request_id, str) and bool(request_id)
        and request_id == error.native_request_id
        and request.get("step") == "query-campaign-root-context-v1"
        and type(request.get("expected_revision")) is int
        and request["expected_revision"] == native_revision
        and response.get("type") == "command_result"
        and type(response.get("protocol_version")) is int
        and response["protocol_version"] == 1
        and response.get("request_id") == request_id
        and response.get("ok") is False
        and response.get("result") is None
        and response.get("error") == "application-main typed query failed or its snapshot changed"
    ):
        return False
    failure = response.get("typed_query_failure_v1")
    if not isinstance(failure, dict):
        return False
    expected = {
        "query_type": "campaign", "stage": "wait",
        "wait_completed": False, "wait_result": "executor_failed",
        "executor_enter": False, "executor_finish": None,
        "executor_typed_result": None, "typed_result": None,
        "frame_stable": None, "final_read": None, "final_equal": None,
    }
    if any(key not in failure or type(failure[key]) is not type(value)
           or failure[key] != value for key, value in expected.items()):
        return False
    exception = failure.get("executor_exception")
    if not (isinstance(exception, dict) and type(exception.get("code")) is int
            and exception["code"] == 0 and exception.get("image") == "none"
            and "rva" in exception and exception["rva"] is None):
        return False
    exact_text = (response["error"] + "; typed_query_failure_v1="
                  + json.dumps(failure, sort_keys=True, separators=(",", ":")))
    return error.native_error == exact_text


def claim_campaign_root_terminal_retry_v1(error: BaseException, starting: object) -> bool:
    """Claim the shared once budget only for the new qualified typed branch."""
    if not is_campaign_root_terminal_rejection_v1(error, starting):
        return False
    from .readonly_planning_retry_v1 import claim_guarded_campaign_root_retry_v1

    if claim_guarded_campaign_root_retry_v1():
        return True
    error.read_only_query_retry_decline = {
        "status": "declined", "reason": "shared_readonly_retry_budget_exhausted",
        "failed_checks": [],
    }
    return False
