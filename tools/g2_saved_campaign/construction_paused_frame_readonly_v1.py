def classify_construction_paused_frame_readonly_v1(row):
    """A matched rejection of the construction read before its executor entry."""
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
            or body.get("error_type") != "BridgeUnavailableError"):
        return None
    diagnostics = body.get("diagnostics")
    if not isinstance(diagnostics, dict) or set(diagnostics) != {"construction_transport_v1"}:
        return None
    d = diagnostics["construction_transport_v1"]
    if (not isinstance(d, dict) or type(d.get("schema_version")) is not int
            or d["schema_version"] != 1 or d.get("source") != "construction_transport_v1"
            or d.get("diagnostic_only") is not True
            or d.get("classification") != "matched_native_rejected"
            or d.get("step") != "g2_player_construction_view_probe_v1"
            or d.get("native_error") != "private construction probe paused frame unavailable"
            or type(d.get("expected_native_revision")) is not int
            or not 0 < d["expected_native_revision"] <= 2**63 - 1
            or not isinstance(d.get("request_id"), str)
            or re.fullmatch(r"construction-read-[0-9a-f]{32}", d["request_id"]) is None
            or d.get("received_request_id") != d["request_id"]
            or d.get("frame_python_type") != "dict"
            or d.get("received_type") != "command_result"
            or type(d.get("received_protocol_version")) is not int
            or d["received_protocol_version"] != 1
            or d.get("received_ok") is not False
            or d.get("result_python_type") != "NoneType"):
        return None
    if (any(d.get(key) is not True for key in
            ("gate_mapping", "gate_type", "gate_protocol", "gate_request_id"))
            or d.get("gate_ok") is not False or d.get("gate_result_mapping") is not False):
        return None
    absent = ("probe_status", "probe_failure", "probe_schema_version", "probe_advertised",
              "probe_snapshot_revision", "probe_date_raw", "probe_proof_epoch",
              "model_status", "model_failure", "model_snapshot_revision", "model_date_raw",
              "model_actor_character_id", "world_status", "world_failure",
              "definition_identity_stage", "definition_identity_failed_index")
    if any(key not in d or d[key] is not None for key in absent):
        return None
    content = result.get("content")
    expected = ("Error executing tool ck3_auto_turn: g2_player_construction_view_probe_v1 "
                "native result missing/rejected; keep action pending if submitted")
    if (not isinstance(content, list) or len(content) != 1
            or not isinstance(content[0], dict) or content[0].get("type") != "text"
            or content[0].get("text") != expected):
        return None
    return {"classification": "construction_probe_paused_frame_rejected_before_read",
            "read_only_precondition": True, "business_submission": False,
            "native_request_id": d["request_id"], "native_step": d["step"],
            "source_native_revision": d["expected_native_revision"],
            "native_stage": "construction_paused_frame_admission_before_query_executor",
            "construction_query_executor_submitted": False,
            "original_action_replay_allowed": False}
