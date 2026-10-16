"""Independent route intent after uncertain Native ACK; host supplies frame binding.

No action/date/business credit or command replay follows from the observation.
"""

def classify_move_native_error_route_observed_v1(body, *, bind_gameplay_frame, initial_frame=None, game_pid=None):
    """One true route readback after an uncertain Native ACK; zero ACK/date credit."""
    if not isinstance(body, dict):
        return None
    step = body.get("selected_step")
    inner = body.get("result")
    if not isinstance(inner, dict) or inner.get("status") != "observed_after_native_error":
        return None
    def require(ok, why):
        if not ok:
            raise ValueError("move native-error route observation rejected: " + why)
    bits = step.split("-") if isinstance(step, str) else []
    require(len(bits) == 5 and bits[:2] == ["move", "army"] and bits[3] == "to"
            and bits[2].isdecimal() and bits[4].isdecimal(), "canonical move step absent")
    # Canonical actual grammar has five hyphen-delimited components.
    army_id, target = int(bits[2]), int(bits[4])
    require(step == f"move-army-{army_id}-to-{target}" and 0 <= army_id < 2**31
            and 0 < target < 2**31, "canonical IDs differ")
    plan = body.get("plan")
    require(body.get("status") == "executed" and isinstance(plan, dict)
            and plan.get("policy") == "one-life-turn-v1"
            and isinstance(plan.get("phase"), str) and bool(plan["phase"])
            and plan.get("selected_step") == step
            and inner.get("step") == step and inner.get("backend_id") == "native-headless"
            and inner.get("accepted") is False and inner.get("native_ack_verified") is False
            and inner.get("native_ack_status") == "unknown_after_error"
            and inner.get("native_error") == "CK3 move-army state is unavailable"
            and inner.get("business_submission_may_have_applied") is True,
            "actual plan and uncertain ACK differ")
    raw = inner.get("native_error_evidence")
    request = raw.get("native_request") if isinstance(raw, dict) else None
    result = raw.get("native_command_result") if isinstance(raw, dict) else None
    require(isinstance(raw, dict) and isinstance(request, dict) and isinstance(result, dict)
            and isinstance(raw.get("native_request_id"), str) and raw["native_request_id"]
            and request.get("type") == "execute_step" and request.get("protocol_version") == 1
            and request.get("request_id") == raw["native_request_id"]
            and request.get("step") == step
            and result.get("type") == "command_result" and result.get("protocol_version") == 1
            and result.get("request_id") == raw["native_request_id"]
            and result.get("ok") is False
            and result.get("error") == "CK3 move-army state is unavailable",
            "original native error packet absent")
    binding = bind_gameplay_frame(
        body, initial_frame=initial_frame, game_pid=game_pid)
    source, observed, action = (inner.get(k) for k in ("source_frame", "observed_frame", "war_action"))
    keys = ("snapshot_id", "revision", "native_revision", "date_raw",
            "actor_character_id", "episode_run_id", "connection_generation", "bridge_pid")
    require(request.get("expected_revision") == binding.get("native_revision")
            and isinstance(source, dict)
            and source.get("revision") == binding.get("revision")
            and all(source.get(k) == binding.get(k) for k in keys if k != "revision")
            and isinstance(observed, dict)
            and all(observed.get(k) == source.get(k) for k in
                    ("date_raw", "actor_character_id", "episode_run_id", "connection_generation", "bridge_pid"))
            and type(observed.get("native_revision")) is int
            and observed["native_revision"] > source["native_revision"]
            and observed.get("snapshot_id") == f"native:{observed['native_revision']}"
            and type(observed.get("revision")) is int
            and observed["revision"] >= source["revision"]
            and inner.get("snapshot_id") == observed["snapshot_id"]
            and inner.get("revision") == observed["revision"],
            "independent newer same-Game route frame differs")
    old, route = inner.get("starting_army_route"), inner.get("observed_army_route")
    armies = inner.get("player_armies")
    matched = ([a for a in armies if isinstance(a, dict) and a.get("army_id") == army_id]
               if isinstance(armies, list) else [])
    require(isinstance(route, list) and route and len(route) <= 4096
            and all(type(p) is int and 0 < p < 2**31 for p in route)
            and route[-1] == target and route != old
            and inner.get("starting_army_target") != target
            and len(matched) == 1
            and matched[0].get("owner_character_id") == source["actor_character_id"]
            and matched[0].get("controllable") is True
            and matched[0].get("move_target_observable") is True
            and matched[0].get("move_target_province_id") == target
            and matched[0].get("route_read_status") == "complete_nonempty"
            and matched[0].get("route_province_ids") == route
            and matched[0].get("in_combat") is False
            and matched[0].get("retreating") is False
            and isinstance(action, dict)
            and action.get("status") == "route_intent_observed"
            and action.get("army_id") == army_id
            and action.get("target_province_id") == target
            and action.get("submitted_date_raw") == source["date_raw"]
            and action.get("postcondition_verified") is True
            and action.get("original_native_ack_verified") is False,
            "fresh route and action identity differ")
    return {"schema": "g2.queue.ordinary-result-credit/v1",
            "selected_step": step, "service_status": "executed",
            "result_status": "observed_after_native_error",
            "category": "move_native_error_route_intent_observed",
            "source_gameplay_frame": dict(binding), "observed_frame": dict(observed),
            "army_id": army_id, "target_province_id": target,
            "route_province_ids": list(route),
            "original_native_ack": "rejected_or_unknown",
            "original_native_request_id": raw["native_request_id"],
            "original_submission_may_have_applied": True,
            "observed_route_intent": True,
            "submitted_pending": False, "primitive_accepted": False,
            "typed_nonmaterial_observation": True,
            "date_advance_observed": False,
            "business_success_inferred": False,
            "paired_after_metrics_still_required": True,
            "replay_allowed": False}
