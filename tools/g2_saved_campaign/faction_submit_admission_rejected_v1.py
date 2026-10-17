def classify_faction_submit_admission_rejected_v1(row):
    """Completed Native pre-mailbox rejection; retain the Python business ledger."""
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
            or not isinstance(content[0], dict) or content[0].get("type") != "text"
            or content[0].get("text") != "Error executing tool ck3_auto_turn: private-submit-faction-gift-member-v1 failed: private_faction_action_or_pending_binding_invalid"):
        return None
    return {"classification": "faction_submit_native_admission_rejected_before_mailbox",
            "read_only_precondition": True, "business_submission": False,
            "original_operation_kind": "business_submit_attempt",
            "native_business_executor_entered": False,
            "native_mailbox_submission_occurred": False,
            "native_failure_stage": "ReadAction_before_TrySubmitMainThreadQueryV1",
            "python_submission_started_ledger_may_exist": True,
            "faction_pending_ledger_must_be_preserved": True,
            "gift_success_claimed": False, "gift_receipt_verified": False,
            "current_auto_new_business_submission": False,
            "original_action_replay_allowed": False,
            "recovery_scope": "fresh_semantic_and_queue_failure_reset_only"}
