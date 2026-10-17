def classify_war_results_first_read_state_changed_v1(body, *, initial_frame=None, game_pid=None):
    """Credit only the paired readonly failure, never window absence or closure."""
    if not isinstance(body, dict) or body.get("selected_step") != "query-war-results-window-v1":
        return None
    result = body.get("result")
    if not isinstance(result, dict) or result.get("schema") != "xar.war-results-readonly-state-changed/v1":
        return None
    plan = body.get("plan")
    source = result.get("source_frame")
    binding = body.get("planning_source_frame")
    raw = result.get("native_error_evidence")
    attempt = result.get("failed_attempt")
    if (body.get("status") != "observed" or body.get("ui_action_credit") is not False
            or not isinstance(plan, dict) or plan.get("policy") != "ordinary-war-results-window-v1"
            or plan.get("phase") != "war_results_window"
            or plan.get("selected_step") != "query-war-results-window-v1"
            or not isinstance(source, dict) or not isinstance(binding, dict)
            or not isinstance(initial_frame, dict) or not isinstance(raw, dict)
            or not isinstance(attempt, dict)):
        raise ValueError("war results readonly failure lacks its ordinary source")
    keys = ("snapshot_id", "revision", "native_revision", "date_raw",
            "actor_character_id", "episode_run_id", "connection_generation", "bridge_pid")
    if (source.get("status") is not None or binding.get("status") != "complete"
            or any(key not in source or source[key] != binding.get(key)
                   or type(source[key]) is not type(binding.get(key)) for key in keys)
            or any(type(source[key]) is not int or source[key] <= 0 for key in
                   ("revision", "native_revision", "actor_character_id", "bridge_pid"))
            or type(source["connection_generation"]) is not int
            or source["connection_generation"] < 0
            or type(source["date_raw"]) is not int
            # The queue supplies its real six-key startup baseline, which is
            # also replaced after an actual natural succession handoff.
            # Current snapshot/public/native counters belong to binding/raw
            # and the query lease, not to that earlier baseline.
            or type(initial_frame.get("actor_character_id")) is not int
            or initial_frame["actor_character_id"] != source["actor_character_id"]
            or not isinstance(initial_frame.get("episode_run_id"), str)
            or initial_frame["episode_run_id"] != source["episode_run_id"]
            or type(initial_frame.get("date_raw")) is not int
            or source["date_raw"] < initial_frame["date_raw"]
            or not isinstance(source["snapshot_id"], str) or not source["snapshot_id"]
            or not isinstance(source["episode_run_id"], str) or not source["episode_run_id"]
            or game_pid is not None and source["bridge_pid"] != game_pid):
        raise ValueError("war results readonly failure source Game/frame differs")
    request = raw.get("native_request")
    response = raw.get("native_command_result")
    request_id = result.get("native_request_id")
    if (result.get("step") != "query-war-results-window-v1"
            or result.get("status") != "technical_read_deferred"
            or result.get("accepted") is not False or result.get("available") is not False
            or result.get("read_only") is not True
            or result.get("business_submission") is not False
            or result.get("native_ack_verified") is not False
            or result.get("request_retried") is not False
            or result.get("ui_action_credit") is not False
            or result.get("date_advance_observed") is not False
            or result.get("window_presence") != "unknown"
            or result.get("close_dispatched") is not False
            or not isinstance(request_id, str) or not request_id
            or not isinstance(request, dict) or not isinstance(response, dict)
            or set(request) != {"type", "protocol_version", "request_id", "step", "expected_revision"}
            or request.get("type") != "execute_step"
            or type(request.get("protocol_version")) is not int or request["protocol_version"] != 1
            or request.get("request_id") != request_id
            or request.get("step") != "query-war-results-window-v1"
            or type(request.get("expected_revision")) is not int
            or request["expected_revision"] != source["native_revision"]
            or set(response) != {"type", "protocol_version", "request_id", "ok", "error"}
            or response.get("type") != "command_result"
            or type(response.get("protocol_version")) is not int or response["protocol_version"] != 1
            or response.get("request_id") != request_id
            or response.get("ok") is not False or response.get("error") != "state_changed"):
        raise ValueError("war results readonly failure raw Native rejection differs")
    lease = {
        "queried_snapshot_id": "snapshot_id", "queried_revision": "revision",
        "queried_native_revision": "native_revision", "queried_date_raw": "date_raw",
        "queried_actor_character_id": "actor_character_id",
        "queried_episode_run_id": "episode_run_id",
        "queried_connection_generation": "connection_generation",
    }
    if (attempt.get("validation_schema") != "war-results-window-query-attempt-v1"
            or attempt.get("step") != "query-war-results-window-v1"
            or attempt.get("native_request_id") != request_id
            or attempt.get("status") != "failed"
            or attempt.get("error") != "Native war results refused: state_changed"
            or any(result.get(key) != source[value] or attempt.get(key) != source[value]
                   for key, value in lease.items())):
        raise ValueError("war results readonly failure cache lease differs")
    return {
        "schema": "g2.queue.ordinary-result-credit/v1",
        "selected_step": "query-war-results-window-v1",
        "service_status": "observed", "result_status": "technical_read_deferred",
        "category": "war_results_readonly_state_changed_deferred",
        "source_gameplay_frame": dict(source),
        "source_native_request_id": request_id,
        "window_presence": "unknown", "war_results_window_closed_verified": False,
        "submitted_pending": False, "primitive_accepted": False,
        "typed_nonmaterial_observation": True,
        "existing_typed_material_verified": False,
        "ui_action_credit": False, "date_advance_observed": False,
        "business_success_inferred": False, "replay_allowed": False,
    }
