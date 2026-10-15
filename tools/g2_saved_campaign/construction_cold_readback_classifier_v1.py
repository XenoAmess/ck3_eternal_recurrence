"""Pure cold-restore construction readback credit rule.

The active queue embeds the function body into a reviewed classifier source.
Keep this helper's AST equal to that embedded function before each runtime pin.
"""

CONSTRUCTION_RECEIPT = "private-query-player-construction-receipt-v1"


def classify_construction_cold_requery_v1(body, *, state=None, initial_frame=None, game_pid=None):
    """Track a prior construction across cold and monthly readonly readbacks."""
    if not isinstance(body, dict):
        return None
    plan = body.get("plan")
    step = body.get("selected_step")
    phase = plan.get("phase") if isinstance(plan, dict) else None
    cold = phase == "construction_cold_applied_requery"
    watch = phase in {"construction_completion_watch",
                      "construction_completed_income_receipt",
                      "construction_completed_province_income_watch"}
    if step != CONSTRUCTION_RECEIPT or not (cold or watch):
        return None
    inner = body.get("result")
    source = body.get("planning_source_frame")
    pending = plan.get("construction_pending_action")
    actions = state.get("construction_actions") if isinstance(state, dict) else None
    request_id = inner.get("action_request_id") if isinstance(inner, dict) else None
    known = actions.get(request_id) if isinstance(actions, dict) and isinstance(request_id, str) else None
    binding = known.get("binding") if isinstance(known, dict) else None
    tracker = known.get("cold_readback_generation_v1") if isinstance(known, dict) else None
    if watch and not isinstance(tracker, dict):
        # A same-process action from this Game keeps the original strict
        # governance classifier; only cold-reconciled IDs enter this path.
        return None

    def require(ok, reason):
        if not ok:
            raise ValueError("construction cold readonly requery rejected: " + reason)

    require(body.get("status") == "executed" and plan.get("selected_step") == step
            and isinstance(inner, dict) and isinstance(source, dict)
            and isinstance(initial_frame, dict) and type(game_pid) is int and game_pid > 0,
            "typed result/current source unavailable")
    require(source.get("schema") == "xar.ck3.planning-source-frame/v1"
            and source.get("status") == "complete"
            and type(source.get("native_revision")) is int and source["native_revision"] > 0
            and source.get("snapshot_id") == "native:" + str(source["native_revision"])
            and type(source.get("revision")) is int and source["revision"] >= 0
            and type(source.get("date_raw")) is int
            and type(source.get("connection_generation")) is int
            and source.get("bridge_pid") == game_pid
            and source.get("actor_character_id") == initial_frame.get("actor_character_id")
            and source.get("episode_run_id") == initial_frame.get("episode_run_id"),
            "new Game planning frame differs")
    require(isinstance(known, dict) and isinstance(binding, dict)
            and known.get("pending") is False and type(known.get("completion_verified")) is bool
            and isinstance(pending, dict)
            and isinstance(request_id, str) and request_id.startswith("construction-submit-")
            and request_id == binding.get("action_request_id"),
            "prior tracked applied action unavailable")
    bound_keys = ("action_request_id", "episode_run_id", "actor_character_id",
                  "pre_native_revision", "pre_date_raw", "pre_proof_epoch",
                  "source_bridge_pid", "source_bridge_creation_date", "candidate", "native_ack")
    require(all(inner.get(key) == binding.get(key) and pending.get(key) == binding.get(key)
                for key in bound_keys)
            and binding.get("episode_run_id") == source["episode_run_id"]
            and binding.get("actor_character_id") == source["actor_character_id"]
            and type(binding.get("source_bridge_pid")) is int
            and type(known.get("last_date_raw")) is int
            and source["date_raw"] >= known["last_date_raw"]
            and pending.get("status") == "applied"
            and pending.get("postcondition_verified") is True,
            "old action/old Game binding differs")
    candidate = binding.get("candidate")
    tuple_keys = ("barony_title_id", "province_id", "building_type_id", "slot_index")
    require(isinstance(candidate, dict)
            and all(type(candidate.get(key)) is int and candidate[key] > 0 for key in tuple_keys[:3])
            and type(candidate.get("slot_index")) is int and candidate["slot_index"] >= 0,
            "original construction tuple unavailable")
    import re
    stamp = r"[0-9]{14}\.[0-9]{6}[+-][0-9]{3}"
    current_stamp = inner.get("post_bridge_creation_date")
    require(isinstance(binding.get("source_bridge_creation_date"), str)
            and re.fullmatch(stamp, binding["source_bridge_creation_date"]) is not None
            and isinstance(current_stamp, str) and re.fullmatch(stamp, current_stamp) is not None
            and inner.get("post_bridge_pid") == game_pid,
            "current Game process proof unavailable")
    if cold:
        previous_pid = tracker.get("bridge_pid") if isinstance(tracker, dict) else binding["source_bridge_pid"]
        previous_stamp = tracker.get("bridge_creation_date") if isinstance(tracker, dict) else binding["source_bridge_creation_date"]
        previous_native = tracker.get("last_native_revision") if isinstance(tracker, dict) else known.get("last_native_revision")
        previous_date = tracker.get("last_date_raw") if isinstance(tracker, dict) else known.get("last_date_raw")
        require(previous_pid != game_pid and current_stamp != previous_stamp
                and pending.get("post_bridge_pid") == previous_pid
                and pending.get("post_bridge_creation_date") == previous_stamp
                and pending.get("post_native_revision") == previous_native
                and pending.get("post_date_raw") == previous_date,
                "cold restore is not tied to the prior verified readback")
    else:
        require(isinstance(tracker, dict) and tracker.get("bridge_pid") == game_pid
                and tracker.get("bridge_creation_date") == current_stamp
                and pending.get("post_bridge_pid") == game_pid
                and pending.get("post_bridge_creation_date") == current_stamp
                and pending.get("post_native_revision") == tracker.get("last_native_revision")
                and pending.get("post_public_revision") == tracker.get("last_public_revision")
                and pending.get("post_date_raw") == tracker.get("last_date_raw")
                and pending.get("post_proof_epoch") == tracker.get("last_proof_epoch")
                and source["native_revision"] >= tracker["last_native_revision"]
                and source["revision"] >= tracker["last_public_revision"]
                and source["date_raw"] >= tracker["last_date_raw"],
                "monthly readback did not continue the current Game generation")
        if phase == "construction_completion_watch":
            last_check = pending.get("completion_last_check_date_raw")
            require(type(last_check) is int and source["date_raw"] >= last_check + 30 * 24
                    and source["date_raw"] > tracker["last_date_raw"],
                    "monthly completion watch is not due")
    require(inner.get("status") == "applied" and inner.get("postcondition_verified") is True
            and inner.get("completion_status") in {"in_progress", "completed"}
            and inner.get("post_snapshot_id") == source["snapshot_id"]
            and inner.get("post_public_revision") == source["revision"]
            and inner.get("post_native_revision") == source["native_revision"]
            and inner.get("post_date_raw") == source["date_raw"]
            and type(inner.get("post_proof_epoch")) is int and inner["post_proof_epoch"] > 0
            and (cold or inner["post_proof_epoch"] > tracker["last_proof_epoch"]),
            "fresh readonly receipt is not on the current frame")
    progress = inner.get("construction_progress_observation")
    income = inner.get("construction_province_income_observation")
    require(isinstance(progress, dict)
            and progress.get("snapshot_id") == source["snapshot_id"]
            and progress.get("native_revision") == source["native_revision"]
            and progress.get("date_raw") == source["date_raw"]
            and isinstance(income, dict)
            and income.get("barony_title_id") == candidate["barony_title_id"]
            and income.get("province_id") == candidate["province_id"],
            "fresh native construction/province observation missing")
    completed = inner["completion_status"] == "completed"
    if completed:
        completion_date = inner.get("completion_observed_date_raw")
        require(progress.get("status") == "not_active"
                and type(completion_date) is int
                and binding["pre_date_raw"] <= completion_date <= source["date_raw"]
                and income.get("status") in {"observed", "unavailable"},
                "completed native slot or completion date unavailable")
    else:
        require(progress.get("status") == "observed"
                and type(progress.get("native_remaining_work_raw")) is int
                and progress["native_remaining_work_raw"] >= 0
                and type(progress.get("native_progress_divisor_raw")) is int
                and income.get("status") == "observed"
                and income.get("snapshot_id") == source["snapshot_id"]
                and income.get("native_revision") == source["native_revision"]
                and income.get("date_raw") == source["date_raw"]
                and type(income.get("native_province_monthly_income_raw")) is int,
                "active construction material read missing")
    intent = inner.get("construction_selected_intent")
    expected_identity = {key: candidate[key] for key in tuple_keys}
    expected_action = {"action_request_id": request_id,
                       "episode_run_id": binding["episode_run_id"],
                       "actor_character_id": binding["actor_character_id"],
                       "candidate": expected_identity}
    require(isinstance(intent, dict)
            and intent.get("schema") == "xar.ck3.construction_selected_intent_continuity_v1"
            and intent.get("source_role") == "prior_action_receipt_query"
            and intent.get("selected_step") == step
            and intent.get("original_action") == expected_action
            and intent.get("observed_action") == expected_action
            and intent.get("action_identity_matches") is True
            and intent.get("actor_identity_matches") is True
            and intent.get("candidate_identity_matches") is True
            and intent.get("selected_query_performed_new_submission") is False
            and intent.get("observed_material_candidate") == expected_identity
            and intent.get("intent_outcome") == "requested_construction_observed",
            "prior action identity or readonly intent differs")
    start = inner.get("start_receipt")
    require(isinstance(start, dict)
            and start.get("action_request_id") == request_id
            and start.get("source_bridge_pid") == binding["source_bridge_pid"]
            and start.get("post_bridge_pid") == binding["source_bridge_pid"]
            and start.get("postcondition_verified") is True,
            "original same-process start proof was not preserved")
    first_completion = completed and not known["completion_verified"]
    import copy
    new_state = copy.deepcopy(state)
    new_known = new_state["construction_actions"][request_id]
    new_known["cold_readback_generation_v1"] = {
        "bridge_pid": game_pid, "bridge_creation_date": current_stamp,
        "last_native_revision": source["native_revision"],
        "last_public_revision": source["revision"],
        "last_date_raw": source["date_raw"],
        "last_proof_epoch": inner["post_proof_epoch"],
        "completion_verified": completed or known["completion_verified"],
    }
    if first_completion:
        new_known["completion_verified"] = True
    observation = {"schema": "g2.queue.ordinary-result-credit/v1", "selected_step": step,
        "service_status": "executed", "result_status": inner["status"],
        "category": ("construction_cold_completion_verified" if first_completion
                     else "construction_cold_readonly_reconciliation_observed"),
        "action_request_id": request_id, "old_bridge_pid": binding["source_bridge_pid"],
        "fresh_bridge_pid": game_pid, "fresh_snapshot_id": source["snapshot_id"],
        "fresh_date_raw": source["date_raw"], "completion_status": inner["completion_status"],
        "submitted_pending": False, "primitive_accepted": False,
        "typed_nonmaterial_observation": not first_completion,
        "existing_typed_material_verified": False,
        "lifestyle_material_verified": False, "existing_focus_verified": False,
        "council_material_verified": False, "construction_material_verified": False,
        "construction_start_verified": False,
        "construction_completion_verified": first_completion,
        "crown_material_verified": False, "crown_receipt_nonmaterial": False,
        "date_advance_observed": False, "business_success_inferred": False,
        "replay_allowed": False}
    return observation, new_state
