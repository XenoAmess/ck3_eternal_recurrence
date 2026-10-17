"""Pure exact-day consumer: unchanged moving contract plus explicit stationary scope.
No action, native read, queue or credit persistence is performed here.
"""

def classify_route_contact_horizon_one_day_v1(body, *, bind_gameplay_frame, initial_frame=None, game_pid=None):
    """Credit only the exact paused one-day clock with a complete same-frame hostile proof."""
    if not isinstance(body, dict):
        return None
    plan = body.get("plan") if isinstance(body.get("plan"), dict) else {}
    step = body.get("selected_step")
    prefix = "advance-route-contact-horizon-v1-"
    if not isinstance(step, str) or not step.startswith(prefix):
        return None

    def require(ok, reason):
        if not ok:
            raise ValueError("route-contact exact day rejected: " + reason)

    import re
    match = re.fullmatch(r"([0-9]+)-to-([0-9]+)-h-([0-9]+)-([0-9]+(?:-[0-9]+)*)", step[len(prefix):])
    require(match is not None, "noncanonical step")
    subject, target, count = (int(match.group(i)) for i in (1, 2, 3))
    hostile_ids = tuple(int(token) for token in match.group(4).split("-"))
    require(0 <= subject <= 2**31 - 1 and 0 < target <= 2**31 - 1
            and 0 < count <= 64 and len(hostile_ids) == count
            and all(0 <= value <= 2**31 - 1 for value in hostile_ids)
            and tuple(sorted(set(hostile_ids))) == hostile_ids
            and subject not in hostile_ids
            and step == prefix + f"{subject}-to-{target}-h-{count}-" + "-".join(map(str, hostile_ids)),
            "step IDs/order")
    stationary = plan.get("phase") == "native_war_stationary_contact_horizon_progress"
    inner = body.get("result")
    require(isinstance(inner, dict) and body.get("status") == "executed"
            and plan.get("selected_step") == step
            and plan.get("phase") in {"native_war_moving_contact_before_strength_progress",
                                      "native_war_stationary_contact_horizon_progress"}
            and inner.get("step") == step and inner.get("backend_id") == "native-headless"
            and inner.get("source") == "native-composite"
            and inner.get("progress_status") == "postcondition"
            and inner.get("requested_horizon_days") == 1
            and inner.get("timeline_policy") == "exact_one_day_contact_free_speed_3"
            and inner.get("timeline_speed") == 3
            and inner.get("paused") is True
            and inner.get("ordinary_events") == [], "exact one-day composite")
    # Native retains an exclusive popup for the next ordinary typed query.
    # It changes screen projection, never the exact clock or UI action credit.
    event, pending = inner.get("active_event"), inner.get("pending_character_interaction")
    event_valid = (isinstance(event, dict)
                   and type(event.get("instance_id")) is int and event["instance_id"] > 0
                   and type(event.get("option_count")) is int and event["option_count"] > 0)
    pending_valid = isinstance(pending, dict) and bool(pending)
    popup = event_valid or pending_valid
    require((event is None or event_valid) and (pending is None or pending_valid)
            and inner.get("final_screen") == (None if popup else "map_hud")
            and inner.get("event_resolution") == ("typed_query_required" if event_valid else "none"),
            "paused popup retained for ordinary typed query")
    start, end, elapsed = (inner.get(k) for k in
                           ("starting_date_raw", "ending_date_raw", "elapsed_days"))
    require(type(start) is int and type(end) is int and type(elapsed) is int
            and end == start + 24 and elapsed == 1
            and inner.get("starting_date") == {"date_raw": start}
            and inner.get("ending_date") == {"date_raw": end}, "one actual game day")
    binding = bind_gameplay_frame(
        body, initial_frame=initial_frame, game_pid=game_pid)
    require(binding.get("date_raw") == start
            and type(game_pid) is int and game_pid > 0
            and binding.get("bridge_pid") == game_pid
            and type(inner.get("revision")) is int
            and inner["revision"] > binding["revision"]
            and inner.get("snapshot_id") != binding.get("snapshot_id"),
            "same-game source and later readback")
    audit = plan.get("route_audit")
    horizon = audit.get("contact_horizon") if isinstance(audit, dict) else None
    require(isinstance(audit, dict) and audit.get("target_province_id") == target
            and isinstance(horizon, dict)
            and horizon.get("status") == "available"
            and horizon.get("date_raw") == start
            and horizon.get("snapshot_revision") == binding["native_revision"]
            and horizon.get("subject_army_id") == subject
            and horizon.get("target_province_id") == target
            and horizon.get("hostile_army_ids") == list(hostile_ids)
            and horizon.get("one_day_contact_free") is True
            and horizon.get("horizon_start_date_raw") == start
            and horizon.get("horizon_end_date_raw") == end
            and horizon.get("conflicts") == [], "complete same-frame contact-free proof")
    if stationary:
        require(audit.get("status") == "safe_one_day_stationary_contact_horizon",
                "exact stationary plan audit")
        from xar_autoplayer.bridge.war_contract import normalize_route_contact_horizon
        normalize_route_contact_horizon(horizon, expected_subject_army_id=subject,
            expected_target_province_id=target, expected_hostile_army_ids=hostile_ids,
            expected_date_raw=start, expected_snapshot_revision=binding["native_revision"])
    else:
        require(audit.get("army_id") == subject and audit.get("army_state") == "moving",
                "original moving plan audit")
    route = horizon.get("subject_route")
    hostile_routes = horizon.get("hostile_routes")
    require(isinstance(route, dict) and route.get("army_id") == subject
            and route.get("timeline_observable") is True
            and isinstance(hostile_routes, list)
            and len(hostile_routes) == count
            and all(isinstance(row, dict) and type(row.get("army_id")) is int
                    for row in hostile_routes)
            and sorted(row["army_id"] for row in hostile_routes) == list(hostile_ids)
            and all(isinstance(row, dict) and row.get("timeline_observable") is True
                    and isinstance(row.get("route_province_ids"), list)
                    and isinstance(row.get("arrival_date_raws"), list)
                    and len(row["route_province_ids"]) == len(row["arrival_date_raws"])
                    for row in hostile_routes), "actual complete route catalogue")
    if stationary:
        require(route.get("current_province_id") == route.get("effective_origin_province_id") == target
                and route.get("route_province_ids") == [] and route.get("arrival_date_raws") == [],
                "native stationary complete empty timeline")
    else:
        require(route.get("route_province_ids") == audit.get("route_province_ids")
                and route.get("route_province_ids") and route["route_province_ids"][-1] == target,
                "original complete moving route")
    before, after = (inner.get(k) for k in ("war_progress_before", "war_progress_after"))
    def war_scope(progress, date):
        require(isinstance(progress, dict) and progress.get("date_raw") == date
                and isinstance(progress.get("wars"), list)
                and len(progress["wars"]) <= 64
                and (date != start or len(progress["wars"]) > 0), "war watch/date")
        seen = set()
        player = set()
        enemy = set()
        for war in progress["wars"]:
            require(isinstance(war, dict) and type(war.get("war_id")) is int
                    and war["war_id"] > 0 and war["war_id"] not in seen,
                    "war identity")
            seen.add(war["war_id"])
            for key, into in (("player_armies", player), ("enemy_armies", enemy)):
                rows = war.get(key)
                require(isinstance(rows, list) and len(rows) <= 4096,
                        "war side roster")
                for row in rows:
                    require(isinstance(row, dict) and type(row.get("army_id")) is int
                            and 0 <= row["army_id"] <= 2**31 - 1,
                            "war side army ID")
                    # The route-contact reader's full hostile scope excludes
                    # armies already retreating at the *starting* frame.  A
                    # missing retreat bit stays in scope; do not guess it away.
                    if key != "enemy_armies" or (row.get("retreating") is not True
                            and (not stationary or row.get("army_state") != "retreating"
                                 and row.get("army_state_code") != 6)):
                        into.add(row["army_id"])
        if date == start:
            require(subject in player and set(hostile_ids) <= enemy,
                    "subject and full hostile watch")
        return seen, enemy
    old_wars, old_enemies = war_scope(before, start)
    if stationary:
        stationary_rows = [row for war in before.get("wars", [])
                           for row in war.get("player_armies", [])
                           if isinstance(row, dict) and row.get("army_id") == subject]
        require(bool(stationary_rows), "observed stationary subject absent")
        for row in stationary_rows:
            state, code = row.get("army_state"), row.get("army_state_code")
            known = (isinstance(state, str) and state.casefold() in {"regular", "sieging"}
                     or not isinstance(state, str) and type(code) is int and code in {1, 3})
            require(known and row.get("current_province_id") == target
                    and "move_target_province_id" in row and row["move_target_province_id"] is None
                    and row.get("route_province_ids") == [] and row.get("in_combat") is False
                    and row.get("retreating") is not True and code not in {2, 6},
                    "same-frame actual stationary subject/target")
    new_wars, _ = war_scope(after, end)
    require(isinstance(plan.get("active_wars"), list), "selected active wars absent")
    require(set(hostile_ids) == old_enemies
            and {war.get("war_id") for war in plan.get("active_wars", [])
                 if isinstance(war, dict)} == old_wars,
            "selected and observed complete starting war scope")
    # A war can terminate or another can begin during the native-stopped day.
    # Fresh post-stop war rows are still shape-checked above, but date credit
    # never grants a war outcome or reuses the old hostile roster afterward.
    actions = inner.get("actions")
    clock = inner.get("exact_day_native_clock")
    armed = clock.get("armed") if isinstance(clock, dict) else None
    stopped = clock.get("stopped") if isinstance(clock, dict) else None
    arm_step = (f"research-arm-tactical-daily-sentinel-v1-{start}-to-{end}"
                "-speed-3-mode-terminal-a-0")
    steps = ["set-speed-3", arm_step, "resume-map",
             "research-query-tactical-daily-sentinel-v1"]
    require(isinstance(actions, list) and len(actions) == 4
            and [row.get("step") if isinstance(row, dict) else None
                 for row in actions] == steps
            and all(isinstance(row.get("result"), dict)
                    and row["result"].get("accepted") is True
                    and row["result"].get("step") == row["step"]
                    for row in actions[1:])
            and isinstance(armed, dict) and isinstance(stopped, dict)
            and actions[1]["result"].get("tactical_daily_sentinel") == armed
            and actions[3]["result"].get("tactical_daily_sentinel") == stopped,
            "native arm/resume/query receipts")
    speed = actions[0].get("result")
    require(isinstance(speed, dict) and (
        (speed.get("accepted") is True and speed.get("step") == "set-speed-3")
        or (speed.get("status") == "already_observed" and speed.get("submitted") is False
            and speed.get("accepted") is None and type(speed.get("observed_speed")) is int
            and speed["observed_speed"] == 3
            and speed.get("source_snapshot_id") == binding["snapshot_id"]
            and speed.get("source_native_revision") == binding["native_revision"]
            and speed.get("source_date_raw") == start)),
        "native speed ACK or same-frame observed speed required")
    generation = armed.get("generation")
    require(type(generation) is int and generation > 0
            and armed.get("state") == "armed"
            and stopped.get("state") == "triggered"
            and stopped.get("generation") == generation
            and all(row.get("starting_date_raw") == start
                    and row.get("target_date_raw") == end
                    and row.get("speed") == 3
                    and row.get("mode") == "terminal_or_sentinel"
                    and row.get("army_count") == 0
                    and row.get("combat_count") == 0
                    and row.get("abnormal") is False
                    for row in (armed, stopped))
            and armed.get("completed_daily_ticks") == 0
            and armed.get("trigger_flags") == 0
            and armed.get("trigger_reasons") == []
            and stopped.get("completed_daily_ticks") == 1
            and stopped.get("last_observed_date_raw") == end
            and stopped.get("trigger_date_raw") == end
            and stopped.get("trigger_flags") == 1
            and stopped.get("trigger_reasons") == ["date_deadline"]
            and stopped.get("signed_date_delta_from_target_raw") == 0
            and stopped.get("overshoot_days") == 0
            and stopped.get("intermediate_pause_count") == 0
            and stopped.get("pause_wrapper_called") is True
            and stopped.get("pause_observed") is True
            and stopped.get("terminal_observed") is False,
            "native exact-day deadline/paused stop")
    return {"schema": "g2.queue.ordinary-result-credit/v1", "selected_step": step,
            "service_status": "executed", "result_status": "postcondition",
            "category": "route_contact_horizon_exact_one_day_observed",
            "actual_date_delta_raw": 24, "actual_elapsed_days": 1,
            "date_advance_observed": True,
            "paired_after_metrics_still_required": True,
            "submitted_pending": False, "primitive_accepted": False,
            "typed_nonmaterial_observation": False,
            "material_verified": False, "ui_action_credit": False,
            "action_credit": False, "lifestyle_material_verified": False,
            "council_material_verified": False, "construction_material_verified": False,
            "construction_start_verified": False, "construction_completion_verified": False,
            "crown_material_verified": False, "existing_typed_material_verified": False,
            "business_success_inferred": False, "replay_allowed": False}
