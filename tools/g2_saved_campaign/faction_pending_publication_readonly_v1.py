def classify_faction_pending_publication_readonly_v1(row):
    """A planning snapshot wait failed; retain the previously submitted gift."""
    if not isinstance(row, dict):
        return None
    request, result = row.get("request"), row.get("result")
    if (not isinstance(request, dict) or request.get("tool") != "ck3_auto_turn"
            or request.get("arguments") != {} or type(request.get("sequence")) is not int
            or request["sequence"] <= 0 or row.get("client_error") is not None
            or not isinstance(result, dict) or result.get("is_error") is not True
            or result.get("result_type") != "complete"
            or result.get("structured_content") is not None):
        return None
    content = result.get("content")
    if (not isinstance(content, list) or len(content) != 1
            or not isinstance(content[0], dict) or content[0].get("type") != "text"):
        return None
    errors = {
        "Error executing tool ck3_auto_turn: private faction pending frame changed before receipt":
            "faction_pending_frame_changed_before_receipt_query",
        "Error executing tool ck3_auto_turn: private faction pending same-date paused revision did not arrive":
            "faction_pending_paused_revision_publication_wait",
    }
    stage = errors.get(content[0].get("text"))
    if stage is None:
        return None
    return {"classification": "faction_pending_planning_publication_wait_before_receipt",
            "read_only_precondition": True, "business_submission": False,
            "native_stage": stage, "current_auto_new_business_submission": False,
            "prior_faction_business_may_be_pending": True,
            "faction_pending_ledger_must_be_preserved": True,
            "prior_gift_result_verified": False,
            "receipt_query_submitted_by_failed_auto": False,
            "original_action_replay_allowed": False}
