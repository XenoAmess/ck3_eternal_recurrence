def classify_campaign_root_paused_boundary_readonly_v1(row):
    """One completed, native-declared campaign read admission rejection."""
    import re
    if not isinstance(row, dict):
        return None
    request, result = row.get("request"), row.get("result")
    if (not isinstance(request, dict) or request.get("tool") != "ck3_auto_turn"
            or request.get("arguments") != {} or type(request.get("sequence")) is not int
            or request["sequence"] <= 0 or row.get("client_error") is not None
            or not isinstance(result, dict) or result.get("is_error") is not True
            or result.get("result_type") != "complete"):
        return None
    body = result.get("structured_content")
    if (not isinstance(body, dict) or set(body) != {"error_type", "diagnostics"}
            or body.get("error_type") != "_NativeCommandRejectedError"):
        return None
    diagnostics = body.get("diagnostics")
    if not isinstance(diagnostics, dict) or set(diagnostics) != {"native_command_rejection"}:
        return None
    rejection = diagnostics["native_command_rejection"]
    if (not isinstance(rejection, dict) or set(rejection) != {
            "diagnostic_only", "native_request_id", "native_step",
            "expected_native_revision", "native_error"}
            or rejection.get("diagnostic_only") is not True
            or rejection.get("native_step") != "query-campaign-root-context-v1"
            or rejection.get("native_error") != "paused application-main boundary is not ready"
            or type(rejection.get("expected_native_revision")) is not int
            or not 0 < rejection["expected_native_revision"] <= 2**64-1
            or not isinstance(rejection.get("native_request_id"), str)
            or re.fullmatch(r"step-[1-9][0-9]*-[0-9a-f]{12}", rejection["native_request_id"]) is None):
        return None
    content = result.get("content")
    expected = "Error executing tool ck3_auto_turn: native gameplay step failed: paused application-main boundary is not ready"
    if (not isinstance(content, list) or len(content) != 1
            or not isinstance(content[0], dict) or content[0].get("type") != "text"
            or content[0].get("text") != expected):
        return None
    return {"classification": "campaign_root_paused_boundary_not_ready_before_query",
            "read_only_precondition": True, "business_submission": False,
            "native_request_id": rejection["native_request_id"],
            "native_step": rejection["native_step"],
            "source_native_revision": rejection["expected_native_revision"],
            "native_stage": "paused_application_main_admission",
            "campaign_query_executor_submitted": False,
            "campaign_root_read_attempted": False,
            "original_action_replay_allowed": False}
