"""Observe an existing route window; callers inject reviewed pure validators.

A date result grants no business, war, move or material success. This module
has no SDK imports and cannot submit or repeat any Native request.
"""
import json

def classify_route_contact_window_advance_v1(body, *, bind_gameplay_frame, parse_advance_step, validate_sentinel_stop, initial_frame=None, game_pid=None):
    plan = body.get("plan") if isinstance(body, dict) and isinstance(body.get("plan"), dict) else {}
    step = body.get("selected_step", plan.get("selected_step")) if isinstance(body, dict) else None
    if not isinstance(step, str) or not step.startswith("advance-route-contact-window-v1-"):
        return None
    parsed = parse_advance_step(step)
    if parsed is None:
        raise ValueError("route-window step is not canonical")
    subject, target, hostiles, horizon = parsed
    inner = body.get("result")
    if (len(json.dumps(body, ensure_ascii=False).encode("utf-8")) > 1024**2
            or not isinstance(inner, dict) or body.get("status") != "executed"
            or plan.get("selected_step") != step or plan.get("route_contact_window_days") != horizon
            or inner.get("step") != step or inner.get("backend_id") != "native-headless"
            or inner.get("source") != "native-tactical-daily-sentinel-composite"
            or inner.get("sentinel_scope") != "route_contact_window"
            or inner.get("progress_status") != "postcondition" or inner.get("stop_kind") != "decision_epoch"
            or inner.get("paused") is not True or inner.get("final_screen") != "map_hud"
            or inner.get("terminal_reached") is not False or inner.get("one_life_terminal") is not False
            or inner.get("played_character_alive") is not True
            or inner.get("player_decision_boundary") is not None
            or inner.get("player_decision_boundary_cancel") is not None):
        raise ValueError("route-window typed postcondition unavailable")
    start, end, deadline = (inner.get(k) for k in ("starting_date_raw", "ending_date_raw", "target_date_raw"))
    elapsed, speed = inner.get("elapsed_days"), inner.get("timeline_speed")
    if (not all(type(v) is int for v in (start, end, deadline, elapsed, speed))
            or not 1 <= elapsed <= horizon or end-start != elapsed*24 or deadline-start != horizon*24
            or not start < end <= deadline or not 1 <= speed <= 5
            or inner.get("starting_date") != {"date_raw": start}
            or inner.get("ending_date") != {"date_raw": end}
            or inner.get("requested_horizon_days") != horizon
            or inner.get("completed_daily_ticks") != elapsed or inner.get("overshoot_days") != 0
            or inner.get("timeline_policy") != "terminal_or_sentinel"
            or inner.get("sentinel_mode") != "terminal_or_sentinel"
            or inner.get("route_contact_window_context_basis") != "frozen_current_routes"):
        raise ValueError("route-window date/tick contract differs")
    binding = bind_gameplay_frame(body, initial_frame=initial_frame, game_pid=game_pid)
    if (not isinstance(initial_frame, dict)
            or type(initial_frame.get("actor_character_id")) is not int
            or inner.get("played_character_id") != initial_frame["actor_character_id"]
            or inner.get("episode_character_id") != initial_frame["actor_character_id"]
            or inner.get("episode_run_id") != initial_frame.get("episode_run_id")
            or inner.get("bridge_pid") != game_pid
            or binding.get("episode_run_id") != inner["episode_run_id"] or binding.get("date_raw") != start
            or type(inner.get("connection_generation")) is not int or inner["connection_generation"] <= 0
            or binding.get("connection_generation") != inner["connection_generation"]
            or type(binding.get("native_revision")) is not int or type(inner.get("native_revision")) is not int
            or inner["native_revision"] <= binding["native_revision"]
            or type(binding.get("revision")) is not int or type(inner.get("revision")) is not int
            or inner["revision"] <= binding["revision"]):
        raise ValueError("route-window actor/episode/frame binding differs")
    proof = inner.get("route_contact_window")
    before_progress = inner.get("war_progress_before")
    before_wars = before_progress.get("wars") if isinstance(before_progress, dict) else None
    if not isinstance(before_wars, list) or not before_wars:
        raise ValueError("route-window actual war watch source absent")
    own_army_ids, eligible_hostile_ids = set(), set()
    for watched_war in before_wars:
        if not isinstance(watched_war, dict):
            raise ValueError("route-window actual war watch row invalid")
        for side in ("player_armies", "enemy_armies"):
            watched_rows = watched_war.get(side)
            if not isinstance(watched_rows, list):
                raise ValueError("route-window actual war watch armies absent")
            for watched in watched_rows:
                watched_id = watched.get("army_id") if isinstance(watched, dict) else None
                if type(watched_id) is not int or not 0 <= watched_id < 2**31:
                    raise ValueError("route-window actual war watch army invalid")
                if side == "player_armies":
                    own_army_ids.add(watched_id)
                elif watched.get("retreating") is not True:
                    # Match the existing exact-day reader: a missing retreat
                    # bit remains hostile; only an explicit True is excluded.
                    eligible_hostile_ids.add(watched_id)
    if subject not in own_army_ids or tuple(sorted(eligible_hostile_ids)) != tuple(hostiles):
        raise ValueError("route-window selected complete nonretreating hostile scope differs")
    # Native arms all owned armies plus the qualified hostile query scope.
    # A retreating enemy remains in the war roster but is not a contact watch.
    watches = tuple(sorted(own_army_ids | eligible_hostile_ids))
    if (not isinstance(proof, dict) or proof.get("status") != "available"
            or proof.get("context_basis") != "frozen_current_routes" or proof.get("horizon_days") != horizon
            or proof.get("window_start_date_raw") != start or proof.get("window_end_date_raw") != deadline
            or proof.get("contact_free") is not True or proof.get("missing") != [] or proof.get("conflicts") != []
            or proof.get("contact_free_whole_days") != horizon
            or inner.get("watch_army_ids") != list(watches)):
        raise ValueError("route-window frozen route proof differs")
    war_sets = []
    for key, date in (("war_progress_before", start), ("war_progress_after", end)):
        progress = inner.get(key)
        wars = progress.get("wars") if isinstance(progress, dict) else None
        if (not isinstance(wars, list) or len(wars) > 64
                or key == "war_progress_before" and not wars
                or progress.get("date_raw") != date):
            raise ValueError("route-window war/date proof missing")
        ids, friendly, enemy = set(), set(), set()
        for war in wars:
            if not isinstance(war, dict) or type(war.get("war_id")) is not int or war["war_id"] <= 0 or war["war_id"] in ids:
                raise ValueError("route-window war identity invalid")
            ids.add(war["war_id"])
            for field, result_ids in (("player_armies", friendly), ("enemy_armies", enemy)):
                armies = war.get(field)
                if not isinstance(armies, list) or len(armies) > 4096:
                    raise ValueError("route-window army summary missing")
                for army in armies:
                    if not isinstance(army, dict) or type(army.get("army_id")) is not int:
                        raise ValueError("route-window army identity invalid")
                    result_ids.add(army["army_id"])
        if key == "war_progress_before" and (subject not in friendly or not set(hostiles) <= enemy):
            raise ValueError("route-window subject/hostile war scope differs")
        war_sets.append(ids)
    if (not isinstance(plan.get("active_wars"), list)
            or {war.get("war_id") for war in plan["active_wars"] if isinstance(war, dict)} != war_sets[0]):
        raise ValueError("route-window selected active war scope differs")
    arm, stop, actions = (inner.get(k) for k in ("armed_tactical_daily_sentinel", "tactical_daily_sentinel", "actions"))
    expected_arm = (f"research-arm-tactical-daily-sentinel-v1-{start}-to-{deadline}-speed-{speed}-"
                    f"mode-terminal-a-{len(watches)}-" + "-".join(map(str, watches)))
    expected_steps = [f"set-speed-{speed}", expected_arm, "resume-map", "research-query-tactical-daily-sentinel-v1"]
    if (not isinstance(arm, dict) or arm.get("state") != "armed" or type(arm.get("generation")) is not int
            or arm["generation"] <= 0 or not isinstance(stop, dict) or not isinstance(actions, list)
            or [a.get("step") if isinstance(a, dict) else None for a in actions] != expected_steps
            or any(not isinstance(a.get("result"), dict) or a["result"].get("accepted") is not True
                   or a["result"].get("step") != a["step"] for a in actions[1:])
            or not isinstance(actions[0].get("result"), dict)
            or not (actions[0]["result"].get("accepted") is True
                    and actions[0]["result"].get("step") == actions[0]["step"]
                    or actions[0]["result"].get("status") == "already_observed"
                    and actions[0]["result"].get("submitted") is False
                    and actions[0]["result"].get("accepted") is None
                    and actions[0]["result"].get("observed_speed") == speed
                    and actions[0]["result"].get("source_snapshot_id") == binding["snapshot_id"]
                    and actions[0]["result"].get("source_native_revision") == binding["native_revision"]
                    and actions[0]["result"].get("source_date_raw") == start)
            or actions[1]["result"].get("tactical_daily_sentinel") != arm
            or actions[3]["result"].get("tactical_daily_sentinel") != stop
            or inner.get("sentinel_generation") != arm["generation"]
            or inner.get("trigger_reasons") != stop.get("trigger_reasons")
            or inner.get("intermediate_pause_count") != stop.get("intermediate_pause_count")
            or inner.get("managed_failure_cleanup") != {"attempted": False, "error": None}):
        raise ValueError("route-window original sentinel/action postconditions differ")
    validate_sentinel_stop(stop, arm_status=arm, starting_date_raw=start,
        target_date_raw=deadline, ending_date_raw=end, elapsed_days=elapsed,
        speed=speed, mode="terminal_or_sentinel", watch_army_ids=watches)
    return {"schema": "g2.queue.ordinary-result-credit/v1", "selected_step": step,
        "service_status": "executed", "result_status": "postcondition",
        "category": "existing_route_contact_window_date_advance_observed",
        "actual_date_delta_raw": end-start, "actual_elapsed_days": elapsed,
        "paired_after_metrics_still_required": True, "date_advance_observed": True,
        "submitted_pending": False, "primitive_accepted": False, "typed_nonmaterial_observation": False,
        "lifestyle_material_verified": False, "council_material_verified": False,
        "construction_material_verified": False, "construction_start_verified": False,
        "construction_completion_verified": False, "crown_material_verified": False,
        "existing_typed_material_verified": False, "business_success_inferred": False, "replay_allowed": False}
