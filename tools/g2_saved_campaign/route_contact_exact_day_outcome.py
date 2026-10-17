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
    phase = plan.get("phase")
    safe_stationary = {"native_war_stationary_contact_horizon_progress",
        "native_war_defender_capital_contact_horizon_progress",
        "native_war_defender_native_rally_contact_horizon_progress"}
    unavoidable_phases = {"native_war_unavoidable_contact_transition",
        "native_war_defender_capital_contact_transition",
        "native_war_defender_native_rally_contact_transition"}
    unavoidable = phase in unavoidable_phases
    stationary = phase in safe_stationary or unavoidable
    speed_value = 1 if unavoidable else 3
    inner = body.get("result")
    require(isinstance(inner, dict) and body.get("status") == "executed"
            and plan.get("selected_step") == step
            and (stationary or phase in {"native_war_moving_contact_before_strength_progress", "native_war_route_contact_horizon_progress"})
            and inner.get("step") == step and inner.get("backend_id") == "native-headless"
            and inner.get("source") == "native-composite"
            and inner.get("progress_status") == "postcondition"
            and inner.get("requested_horizon_days") == 1
            and inner.get("timeline_policy") == ("exact_one_day_unavoidable_contact" if unavoidable else "exact_one_day_contact_free_speed_3")
            and inner.get("timeline_speed") == speed_value
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
            and inner.get("final_screen") == ("map_hud" if unavoidable and isinstance(inner.get("contact_refresh"), dict) else None if popup else "map_hud")
            and (inner.get("event_resolution") in {"none", "typed_query_required"} if unavoidable and isinstance(inner.get("contact_refresh"), dict) and event_valid else inner.get("event_resolution") == ("typed_query_required" if event_valid else "none")),
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
    if phase == "native_war_route_contact_horizon_progress":
        require(plan.get("route_contact_window_days") == 1, "one-day route-window fallback source")
    audit = plan.get("route_audit")
    if phase in {"native_war_defender_capital_contact_horizon_progress",
                 "native_war_defender_native_rally_contact_horizon_progress",
                 "native_war_defender_capital_contact_transition",
                 "native_war_defender_native_rally_contact_transition"}:
        hold = plan.get("defensive_hold")
        require(isinstance(hold, dict) and hold.get("army_id") == subject,
                "exact defensive hold subject")
        audit = {"status": "stationary_current_province_contact" if unavoidable
                 else "safe_one_day_stationary_contact_horizon",
                 "target_province_id": target, "contact_horizon": plan.get("contact_horizon")}
    horizon = audit.get("contact_horizon") if isinstance(audit, dict) else None
    require(isinstance(audit, dict) and audit.get("target_province_id") == target
            and isinstance(horizon, dict)
            and horizon.get("status") == "available"
            and horizon.get("date_raw") == start
            and horizon.get("snapshot_revision") == binding["native_revision"]
            and horizon.get("subject_army_id") == subject
            and horizon.get("target_province_id") == target
            and horizon.get("hostile_army_ids") == list(hostile_ids)
            and horizon.get("one_day_contact_free") is (not unavoidable)
            and horizon.get("horizon_start_date_raw") == start
            and horizon.get("horizon_end_date_raw") == end
            and (bool(horizon.get("conflicts")) if unavoidable else horizon.get("conflicts") == []), "complete same-frame native horizon proof")
    if stationary:
        require(audit.get("status") == ("stationary_current_province_contact" if unavoidable else "safe_one_day_stationary_contact_horizon"),
                "exact stationary plan audit")
        from xar_autoplayer.bridge.war_contract import normalize_route_contact_horizon
        normalize_route_contact_horizon(horizon, expected_subject_army_id=subject,
            expected_target_province_id=target, expected_hostile_army_ids=hostile_ids,
            expected_date_raw=start, expected_snapshot_revision=binding["native_revision"])
        if unavoidable:
            from xar_autoplayer.bridge.war_contract import unavoidable_current_province_contact_in_horizon
            require(unavoidable_current_province_contact_in_horizon(horizon),
                    "native unavoidable current province conflict")
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
                f"-speed-{speed_value}-mode-terminal-a-0")
    steps = [f"set-speed-{speed_value}", arm_step, "resume-map",
             "research-query-tactical-daily-sentinel-v1"]
    refresh = inner.get("contact_refresh")
    if unavoidable and isinstance(refresh, dict):
        steps.append("pause-map")
    require(isinstance(actions, list) and len(actions) == len(steps)
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
        (speed.get("accepted") is True and speed.get("step") == f"set-speed-{speed_value}")
        or (speed.get("status") == "already_observed" and speed.get("submitted") is False
            and speed.get("accepted") is None and type(speed.get("observed_speed")) is int
            and speed["observed_speed"] == speed_value
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
                    and row.get("speed") == speed_value
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
    if unavoidable:
        verify_unavoidable(inner, before, after, horizon, binding, subject, target, start, end)
    credit = {"schema": "g2.queue.ordinary-result-credit/v1", "selected_step": step,
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

    if unavoidable:
        credit["category"] = "unavoidable_contact_exact_one_day_observed"
        credit["unavoidable_contact_transition"] = dict(inner["contact_transition"])
        credit["contact_free_claimed"] = False
    return credit

def verify_unavoidable(inner, before, after, horizon, binding, subject, target, start, end):
    """Check the existing producer's nonmaterial contact transition evidence."""
    def need(ok, reason):
        if not ok:
            raise ValueError("unavoidable exact day rejected: " + reason)
    def army_map(progress, key):
        out = {}
        for war in progress["wars"]:
            for row in war[key]:
                ident = row["army_id"]
                if ident in out:
                    need(out[ident] == row, "inconsistent cross-war army row")
                out[ident] = row
        return out
    def combat(row):
        return isinstance(row, dict) and (row.get("in_combat") is True
            or row.get("army_state") == "combat" or row.get("army_state_code") == 2)
    def retreat(row):
        return isinstance(row, dict) and (row.get("retreating") is True
            or row.get("army_state") == "retreating" or row.get("army_state_code") == 6)
    def native(snapshot):
        if not isinstance(snapshot, str) or not snapshot.startswith("native:"):
            return None
        token = snapshot[7:]
        return int(token) if token.isdecimal() and str(int(token)) == token else None
    transition = inner.get("contact_transition")
    need(isinstance(transition, dict) and transition.get("proof_kind") == "unavoidable_current_province_contact"
         and transition.get("subject_army_id") == subject
         and transition.get("starting_date_raw") == start and transition.get("ending_date_raw") == end
         and inner.get("contact_followup") is None, "retained completed transition and no failed strict followup")
    final_native = native(inner.get("snapshot_id"))
    need(type(final_native) is int and final_native > binding["native_revision"]
         and ("native_revision" not in inner or inner["native_revision"] == final_native), "later Native frame")
    refresh = inner.get("contact_refresh")
    if refresh is not None:
        need(isinstance(refresh, dict) and refresh.get("attempted") is True
             and refresh.get("ack_status") == "already_paused" and refresh.get("date_raw") == end
             and all(type(refresh.get(k)) is int for k in ("from_revision","to_revision","from_native_revision","to_native_revision"))
             and refresh["from_revision"] > binding["revision"]
             and refresh["to_revision"] > refresh["from_revision"]
             and refresh["from_native_revision"] > binding["native_revision"]
             and refresh["to_native_revision"] > refresh["from_native_revision"]
             and refresh["from_snapshot_id"] == "native:" + str(refresh["from_native_revision"])
             and refresh["to_snapshot_id"] == inner["snapshot_id"]
             and refresh["to_revision"] == inner["revision"] and refresh["to_native_revision"] == final_native,
             "one same-date independent paused refresh")
        pause = inner["actions"][-1]
        need(pause["step"] == "pause-map" and pause["result"].get("status") == "already_paused",
             "refresh actual already-paused ACK")
    old_players,new_players = army_map(before,"player_armies"),army_map(after,"player_armies")
    old_enemies,new_enemies = army_map(before,"enemy_armies"),army_map(after,"enemy_armies")
    old_subject,new_subject = old_players.get(subject),new_players.get(subject)
    conflicts = horizon["conflicts"]
    conflict_ids = sorted({row["hostile_army_id"] for row in conflicts})
    status, post = transition.get("status"),transition.get("postcondition")
    if status == "predicted_only":
        need(post == "predicted_contact_boundary_reached" and transition.get("contact_observed") is False
             and transition.get("episode_run_id") == binding["episode_run_id"]
             and transition.get("contact_province_id") == target
             and transition.get("conflict_hostile_army_ids") == conflict_ids
             and isinstance(refresh, dict)
             and all(c.get("kind") == "same_province" and c.get("province_id") == target
                     and c.get("overlap_start_date_raw") == end and c.get("overlap_end_date_raw") == end for c in conflicts)
             and {w["war_id"] for w in before["wars"]} == {w["war_id"] for w in after["wars"]}
             and isinstance(new_subject, dict) and new_subject.get("current_province_id") == target
             and new_subject.get("move_target_province_id") is None and new_subject.get("route_province_ids") == []
             and not combat(new_subject) and not retreat(new_subject), "prediction only at exact closed endpoint")
        return
    need(status == "observed" and post in {"active_war_set_changed","subject_army_removed",
         "active_combat_observed","retreat_observed","hostile_entered_contact_province","hostile_intent_changed"},
         "source-supported observed transition")
    old_wars,new_wars = sorted(w["war_id"] for w in before["wars"]),sorted(w["war_id"] for w in after["wars"])
    if post == "active_war_set_changed":
        need(old_wars != new_wars and transition.get("starting_war_ids") == old_wars
             and transition.get("ending_war_ids") == new_wars, "actual changed war set without victory credit")
    elif post == "subject_army_removed":
        need(subject not in new_players, "actual subject absence")
    elif post == "active_combat_observed":
        need(combat(new_subject), "actual active combat row")
    elif post == "retreat_observed":
        need(retreat(new_subject), "actual retreat row")
    elif post == "hostile_entered_contact_province":
        changed = [ident for ident in conflict_ids if isinstance(old_enemies.get(ident),dict)
                   and isinstance(new_enemies.get(ident),dict)
                   and old_enemies[ident].get("current_province_id") != target
                   and new_enemies[ident].get("current_province_id") == target]
        need(isinstance(old_subject,dict) and isinstance(new_subject,dict)
             and old_subject.get("current_province_id") == new_subject.get("current_province_id") == target
             and transition.get("contact_province_id") == target
             and bool(changed) and transition.get("changed_hostile_army_ids") == changed,
             "actual hostile province entry without battle inference")
    else:
        def intent(row):
            if not isinstance(row,dict):return None
            return (row.get("move_target_province_id"),row.get("route_province_ids"),row.get("army_state"),
                    row.get("army_state_code"),row.get("in_combat"),row.get("retreating"))
        changed = [ident for ident in conflict_ids if intent(old_enemies.get(ident)) != intent(new_enemies.get(ident))]
        need(bool(changed) and transition.get("changed_hostile_army_ids") == changed,
             "actual hostile intent change without contact inference")
