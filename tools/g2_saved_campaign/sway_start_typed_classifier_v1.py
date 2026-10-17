def classify_ordinary_sway_start_applied_v1(body, *, initial_frame=None, game_pid=None):
    """Credit a joined Start primitive; no terminal, benefit, or day credit."""
    if not isinstance(body, dict):
        return None
    step = "ordinary-sway-opportunity-v1"
    plan = body.get("plan")
    plan = plan if isinstance(plan, dict) else {}
    if body.get("selected_step") != step and plan.get("selected_step") != step:
        return None

    def require(ok, reason):
        if not ok:
            raise ValueError("ordinary Sway Start: " + reason + "; retain original action, no replay")

    def positive(value):
        return type(value) is int and value > 0

    def mapping(value, name):
        require(isinstance(value, dict), name + " missing")
        return value

    require(body.get("status") == "executed" and body.get("selected_step") == step
            and plan.get("selected_step") == step, "executed step mismatch")
    result = mapping(body.get("result"), "formal resolved result")
    job = mapping(plan.get("ordinary_sway_job_v1"), "ordinary nomination")
    source = mapping(body.get("planning_source_frame"), "planning source")
    actor, target, action = (result.get(key) for key in
                             ("actor_character_id", "target_character_id", "action_id"))
    require(positive(actor) and actor <= 0xFFFFFFFF and positive(target)
            and target <= 0xFFFFFFFF and actor != target, "full actor/target invalid")
    require(isinstance(action, str) and len(action) == 37 and action.startswith("sway-")
            and all(ch in "0123456789abcdef" for ch in action[5:]), "original action invalid")
    require(result.get("status") == "applied" and result.get("postcondition_verified") is True
            and result.get("next_turn_consumed") is False, "Start not newly postverified")
    require(job.get("job") == "query_selected_target" and job.get("submit_allowed") is False
            and job.get("target_character_id") == target
            and mapping(job.get("state"), "nomination state").get("actor_character_id") == actor,
            "nomination is not this actor/target")
    require(source.get("schema") == "xar.ck3.planning-source-frame/v1"
            and source.get("status") == "complete"
            and all(positive(source.get(key)) for key in
                    ("revision", "native_revision", "date_raw", "bridge_pid", "connection_generation"))
            and source.get("actor_character_id") == actor
            and source.get("snapshot_id") == "native:" + str(source["native_revision"])
            and isinstance(source.get("episode_run_id"), str) and source["episode_run_id"],
            "source frame incomplete")
    admitted = mapping(initial_frame, "admitted campaign")
    require(positive(game_pid) and source["bridge_pid"] == game_pid
            and admitted.get("actor_character_id") == actor
            and admitted.get("episode_run_id") == source["episode_run_id"],
            "admitted actor/episode/PID mismatch")
    receipt = mapping(result.get("native_receipt"), "Native applied receipt")
    exe = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
    require(receipt.get("schema") == "active-scheme-sway-formal-private-v1"
            and receipt.get("stage") == "applied" and receipt.get("action_id") == action
            and receipt.get("postcondition_verified") is True
            and receipt.get("exact_ck3_build") == "1.20.0.4"
            and isinstance(receipt.get("exe_sha256"), str)
            and receipt["exe_sha256"].upper() == exe, "Native receipt identity/build invalid")
    for key, identity in (("actor_character_id", actor), ("target_character_id", target)):
        require(key not in receipt or (type(receipt[key]) is int and receipt[key] == identity),
                "optional Native identity differs")
    instance, generation = receipt.get("scheme_instance_id"), receipt.get("scheme_instance_generation")
    require(positive(instance) and instance < 0xFFFFFFFF and type(generation) is int
            and generation == instance >> 24, "full instance generation invalid")
    require(all(positive(result.get(key)) for key in
                ("pre_capture_epoch", "post_capture_epoch", "post_native_revision", "post_date_raw"))
            and positive(receipt.get("post_capture_epoch"))
            and positive(receipt.get("post_container_generation"))
            and type(receipt.get("post_date_raw")) is int
            and result["pre_capture_epoch"] < receipt["post_capture_epoch"] < result["post_capture_epoch"]
            and receipt["post_date_raw"] == result["post_date_raw"] == source["date_raw"]
            and result["post_native_revision"] >= source["native_revision"], "postcondition frame invalid")
    observation = mapping(result.get("applied_instance_observation"), "independent instance observation")
    require(observation.get("schema") == "xar.ck3.sway-applied-instance-observation.v1"
            and observation.get("source_kind") == "independent_active_read_after_native_receipt"
            and all(observation.get(key) == value for key, value in (
                ("action_id", action), ("actor_character_id", actor), ("target_character_id", target),
                ("scheme_instance_id", instance), ("scheme_instance_generation", generation))),
            "independent observation identity differs")
    row = mapping(observation.get("active_instance"), "independent active row")
    require(all(type(row.get(key)) is int and row[key] == value for key, value in (
                ("scheme_instance_id", instance), ("scheme_instance_generation", generation),
                ("target_character_id", target)))
            and type(row.get("progress")) is int and type(row.get("progress_goal")) is int
            and 0 <= row["progress"] <= row["progress_goal"] <= 0x7FFFFFFF
            and row["progress_goal"] > 0 and type(row.get("is_exposed")) is bool
            and type(row.get("is_frozen")) is bool, "independent active row invalid")
    read = mapping(observation.get("source_read"), "independent source read")
    require(read.get("schema") == "active-scheme-sway-private-read-v1"
            and read.get("exact_ck3_build") == "1.20.0.4"
            and isinstance(read.get("exe_sha256"), str) and read["exe_sha256"].upper() == exe
            and positive(read.get("queried_revision")) and read["queried_revision"] >= source["revision"]
            and all(type(read.get(key)) is int and read[key] == value for key, value in (
                ("queried_native_revision", result["post_native_revision"]),
                ("snapshot_revision", result["post_native_revision"]), ("date_raw", source["date_raw"]),
                ("capture_epoch", result["post_capture_epoch"]),
                ("container_generation", receipt["post_container_generation"])))
            and read.get("queried_snapshot_id") == "native:" + str(result["post_native_revision"])
            and read.get("post_snapshot_id") == read["queried_snapshot_id"], "independent read source differs")
    optional = mapping(body.get("ordinary_sway_optional"), "ordinary completion")
    require(optional.get("job") == "query_selected_target"
            and optional.get("target_character_id") == target and optional.get("outcome") == "applied"
            and optional.get("result") == result, "ordinary completion differs")
    cadence = mapping(optional.get("scheduler_state"), "completed cadence")
    require(all(type(cadence.get(key)) is int and cadence[key] == value for key, value in (
                ("actor_character_id", actor), ("last_target_character_id", target), ("no_operation_count", 0),
                ("last_check_date_raw", source["date_raw"]),
                ("next_check_date_raw", source["date_raw"] + 720)))
            and cadence.get("last_job_kind") == "query_selected_target", "cadence completion differs")
    return {"schema": "g2.queue.ordinary-result-credit/v1", "category": "sway_start_applied_primitive",
        "selected_step": step, "service_status": "executed", "result_status": "applied",
        "primitive_accepted": True, "submitted_pending": False,
        "sway_start_postcondition_verified": True, "original_action_id": action,
        "actor_character_id": actor, "target_character_id": target,
        "scheme_instance_id": instance, "scheme_instance_generation": generation,
        "sway_terminal_observed": False, "sway_material_benefit_verified": False,
        "material_verified": False, "business_success_inferred": False,
        "date_advance_observed": False, "replay_allowed": False}
