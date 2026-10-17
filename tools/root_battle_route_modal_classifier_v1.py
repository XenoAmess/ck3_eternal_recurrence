"""Pure, narrowly scoped consumers of existing native sentinel modal receipts."""


def require(value, message):
    if not value:
        raise ValueError("battle/route modal: " + message)


def war_summaries(inner, plan, start, end):
    summaries = []
    for field, date in (("war_progress_before", start), ("war_progress_after", end)):
        progress = inner.get(field)
        wars = progress.get("wars") if isinstance(progress, dict) else None
        require(isinstance(progress, dict) and progress.get("date_raw") == date
                and isinstance(wars, list) and 1 <= len(wars) <= 64, "war/date summary")
        by_war = {}
        for war in wars:
            war_id = war.get("war_id") if isinstance(war, dict) else None
            require(type(war_id) is int and war_id > 0 and war_id not in by_war, "war identity")
            by_war[war_id] = war
            for field in ("player_armies", "enemy_armies"):
                armies = war.get(field)
                require(isinstance(armies, list) and len(armies) <= 4096, "complete army summary")
                ids = [army.get("army_id") if isinstance(army, dict) else None for army in armies]
                require(all(type(i) is int and 0 <= i <= 2**31-1 for i in ids) and len(ids) == len(set(ids)), "army identities")
        summaries.append(by_war)
    planned = plan.get("active_wars")
    ids = [war.get("war_id") if isinstance(war, dict) else None for war in planned] if isinstance(planned, list) else []
    require(len(ids) == len(set(ids)) and set(ids) == set(summaries[0]) == set(summaries[1]), "planned/stable war identities")
    return summaries


def committed_scope(plan, before, after, subject, target, deadline, start):
    require(len(before) == len(after) == 1 and plan.get("phase") == "native_war_committed_route_contact_trial"
            and plan.get("risk_assessment_kind") == "observed_three_to_two_margin_not_win_probability", "committed route plan")
    values = [plan.get(k) for k in ("friendly_current_soldiers", "enemy_current_soldiers", "friendly_ai_base_power_raw", "enemy_ai_base_power_raw")]
    require(all(type(v) is int and v > 0 for v in values)
            and values[0]*2 >= values[1]*3 and values[2]*2 >= values[3]*3, "original 1.5 margins")
    proof = plan.get("contact_horizon")
    require(isinstance(proof, dict), "committed contact horizon")
    enemies = proof.get("hostile_army_ids")
    first = plan.get("first_contact_province_id", target)
    route = proof.get("subject_route")
    require(proof.get("status") == "available" and proof.get("one_day_contact_free") is False
            and proof.get("date_raw") == start and proof.get("horizon_start_date_raw") == start
            and proof.get("horizon_end_date_raw") == deadline and proof.get("subject_army_id") == subject
            and proof.get("target_province_id") == target
            and isinstance(enemies, list) and 1 <= len(enemies) <= 2
            and all(type(i) is int and 0 <= i <= 2**31-1 for i in enemies) and len(set(enemies)) == len(enemies)
            and type(first) is int and first > 0 and isinstance(route, dict)
            and route.get("army_id") == subject and route.get("timeline_observable") is True
            and isinstance(route.get("route_province_ids"), list) and bool(route["route_province_ids"])
            and route["route_province_ids"][0] == first
            and isinstance(route.get("arrival_date_raws"), list) and bool(route["arrival_date_raws"])
            and route["arrival_date_raws"][0] == deadline, "committed initial route/target/date")
    old, new = next(iter(before.values())), next(iter(after.values()))
    require(len(old["player_armies"]) == len(new["player_armies"]) == 1
            and old["player_armies"][0]["army_id"] == new["player_armies"][0]["army_id"] == subject
            and {a["army_id"] for a in old["enemy_armies"]} == set(enemies)
            and {a["army_id"] for a in new["enemy_armies"]} == set(enemies), "complete committed hostile scope")
    player = old["player_armies"][0]
    hostile_routes, conflicts = proof.get("hostile_routes"), proof.get("conflicts")
    require(route.get("current_province_id") == player.get("current_province_id")
            and player.get("in_combat") is False and player.get("retreating") is not True
            and player.get("move_target_province_id") == target
            and player.get("route_province_ids") == route["route_province_ids"]
            and all(a.get("current_province_id") == first and a.get("in_combat") is False for a in old["enemy_armies"])
            and isinstance(hostile_routes, list) and len(hostile_routes) == len(enemies)
            and all(isinstance(r, dict) for r in hostile_routes)
            and {r.get("army_id") for r in hostile_routes} == set(enemies)
            and all(r.get("timeline_observable") is True and r.get("current_province_id") == first
                    and r.get("effective_origin_province_id") == first and r.get("route_province_ids") == []
                    and r.get("arrival_date_raws") == [] for r in hostile_routes)
            and isinstance(conflicts, list) and len(conflicts) == len(enemies)
            and all(isinstance(c, dict) for c in conflicts)
            and {c.get("hostile_army_id") for c in conflicts} == set(enemies)
            and all(c.get("kind") == "same_province" and c.get("province_id") == first
                    and c.get("overlap_start_date_raw") == deadline and c.get("overlap_end_date_raw") == deadline for c in conflicts),
            "original committed contact/risk scope")


def classify(body, initial_frame, game_pid, start_binding, scope):
    if not isinstance(body, dict) or not isinstance(body.get("result"), dict):
        return None
    inner, plan = body["result"], body.get("plan")
    step = body.get("selected_step")
    if inner.get("stop_kind") != "player_decision" or inner.get("sentinel_scope") != scope:
        return None
    prefix = "battle-decision-epoch-advance-to-" if scope == "active_battle" else "committed-route-sentinel-advance-"
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    from xar_autoplayer.bridge.war_contract import parse_battle_decision_epoch_advance_step, parse_committed_route_sentinel_advance_speed, parse_committed_route_sentinel_advance_step
    from xar_autoplayer.bridge.native_driver import _normalize_tactical_daily_sentinel_status, _validate_tactical_daily_sentinel_arm, _validate_tactical_daily_sentinel_decision_boundary
    require(isinstance(plan, dict) and plan.get("selected_step") == step and body.get("status") == "executed", "ordinary plan")
    if scope == "active_battle":
        deadline = parse_battle_decision_epoch_advance_step(step) if isinstance(step, str) else None
        watches = plan.get("watch_army_ids")
        require(deadline is not None and plan.get("phase") == "native_war_global_battle_decision_epoch"
                and plan.get("timeline_policy") == "battle_decision_epoch_speed_3" and plan.get("timeline_speed") == 3
                and isinstance(watches, list) and len(watches) == 1 and type(watches[0]) is int and 0 <= watches[0] <= 2**31-1,
                "active battle epoch plan")
        subject, target = watches[0], None
    elif scope == "committed_route":
        parsed = parse_committed_route_sentinel_advance_step(step) if isinstance(step, str) else None
        require(parsed is not None and parse_committed_route_sentinel_advance_speed(step) == 3, "committed canonical step/speed")
        subject, target, deadline = parsed
        watches = [subject]
    else:
        return None
    binding = start_binding(body, initial_frame=initial_frame, game_pid=game_pid)
    start, end, days, horizon = (inner.get(k) for k in ("starting_date_raw", "ending_date_raw", "elapsed_days", "requested_horizon_days"))
    require(inner.get("step") == step and inner.get("backend_id") == "native-headless"
            and inner.get("source") == "native-tactical-daily-sentinel-composite"
            and inner.get("progress_status") == "postcondition" and inner.get("paused") is True
            and inner.get("final_screen") is None and inner.get("terminal_reached") is False
            and inner.get("one_life_terminal") is False and inner.get("one_life_terminal_reason") is None
            and inner.get("played_character_alive") is True
            and inner.get("sentinel_mode") == inner.get("timeline_policy") == "decision_epoch"
            and inner.get("timeline_speed") == 3 and inner.get("watch_army_ids") == watches
            and all(type(v) is int for v in (start, end, deadline, days, horizon))
            and 0 <= days <= horizon <= 45 and horizon >= 1 and end-start == days*24
            and deadline-start == horizon*24 and start <= end <= deadline
            and inner.get("target_date_raw") == plan.get("absolute_target_date_raw") == deadline
            and inner.get("starting_date") == {"date_raw": start} and inner.get("ending_date") == {"date_raw": end}
            and (scope != "committed_route" or horizon == 1), "native clock/frame envelope")
    require(type(game_pid) is int and binding.get("bridge_pid") == inner.get("bridge_pid") == game_pid
            and binding["date_raw"] == start and initial_frame["date_raw"] <= start
            and inner.get("played_character_id") == inner.get("episode_character_id") == binding["actor_character_id"]
            and inner.get("episode_run_id") == binding["episode_run_id"]
            and inner.get("connection_generation") == binding["connection_generation"]
            and all(type(inner.get(k)) is int and inner[k] > binding[k] for k in ("revision", "native_revision"))
            and inner.get("snapshot_id") == "native:"+str(inner["native_revision"]), "actor/episode/native-public binding")
    boundary, event, interaction = (inner.get(k) for k in ("player_decision_boundary", "active_event", "pending_character_interaction"))
    require(isinstance(boundary, dict) and boundary.get("kind") in {"active_event", "pending_character_interaction"}
            and boundary.get("observed_date_raw") == end
            and all(boundary.get(k) == inner.get(k) for k in ("bridge_pid", "connection_generation", "episode_character_id", "episode_run_id", "played_character_id", "snapshot_id", "revision", "native_revision")),
            "native decision boundary identity")
    if boundary["kind"] == "active_event":
        options = event.get("options") if isinstance(event, dict) else None
        count = event.get("option_count") if isinstance(event, dict) else None
        require(isinstance(event, dict) and event.get("source") == "native" and type(event.get("instance_id")) is int
                and event["instance_id"] > 0 and boundary.get("instance_id") == event["instance_id"]
                and type(count) is int and 1 <= count <= 256 and boundary.get("option_count") == count
                and isinstance(options, list) and len(options) == count
                and all(isinstance(o, dict) and type(o.get("index")) is int and o["index"] == i
                        and type(o.get("option_number")) is int and o["option_number"] == i+1
                        and type(o.get("enabled")) is bool for i,o in enumerate(options))
                and any(o["enabled"] for o in options) and interaction is None, "native event/options")
    else:
        require(event is None and isinstance(interaction, dict) and type(interaction.get("instance_id")) is int
                and all(boundary.get(k) == interaction.get(k) for k in ("instance_id", "sender_character_id", "auto_accept_notification")),
                "native interaction identity")
    before, after = war_summaries(inner, plan, start, end)
    if scope == "committed_route":
        committed_scope(plan, before, after, subject, target, deadline, start)
    else:
        require(any(a["army_id"] == subject and a.get("in_combat") is True for w in before.values() for a in w["player_armies"]), "starting active combat")
    arm, stop, actions = (inner.get(k) for k in ("armed_tactical_daily_sentinel", "tactical_daily_sentinel", "actions"))
    require(isinstance(arm, dict) and isinstance(stop, dict) and isinstance(actions, list), "native sentinel/action receipts")
    arm, stop = _normalize_tactical_daily_sentinel_status(arm), _normalize_tactical_daily_sentinel_status(stop)
    generation = arm["generation"]
    arm_step = f"research-arm-tactical-daily-sentinel-v1-{start}-to-{deadline}-speed-3-mode-decision-a-1-{subject}"
    query = "research-query-tactical-daily-sentinel-v1"
    cancel = f"research-cancel-tactical-daily-sentinel-v1-generation-{generation}"
    steps = [a.get("step") if isinstance(a, dict) else None for a in actions]
    prefix = ["set-speed-3", arm_step, "resume-map"]
    pause_count = 1 if len(steps) > 3 and steps[3] == "pause-map" else 0
    expected = prefix + (["pause-map"] if pause_count else []) + [query]
    if stop["state"] == "idle":
        expected += [cancel, query]
    require(steps == expected and all(isinstance(a.get("result"), dict) and a["result"].get("accepted") is True
            and a["result"].get("step") == a["step"] for a in actions), "original bounded native action sequence")
    require(actions[1]["result"].get("tactical_daily_sentinel") == arm
            and actions[-1]["result"].get("tactical_daily_sentinel") == stop
            and all(a["result"].get("status") == "available" for a in actions if a["step"] in {arm_step, query})
            and (not pause_count or actions[3].get("purpose") == "player_decision_boundary_stabilization")
            and inner.get("sentinel_generation") == generation
            and inner.get("external_pause_count") == inner.get("player_decision_boundary_pause_count") == pause_count
            and inner.get("external_rich_query_count") == 0
            and inner.get("managed_failure_cleanup") == {"attempted":False,"error":None}
            and all(inner.get(k) == stop.get(k) for k in ("completed_daily_ticks", "intermediate_pause_count", "overshoot_days", "trigger_reasons"))
            and inner.get("zero_intermediate_pause") is (stop["intermediate_pause_count"] == 0), "native action/result readback")
    if stop["state"] == "idle":
        pending = _normalize_tactical_daily_sentinel_status(actions[-3]["result"].get("tactical_daily_sentinel"))
        require(pending == dict(stop, state="armed") and actions[-2]["result"].get("status") == "canceled", "generation cancel then idle readback")
    _validate_tactical_daily_sentinel_arm(actions[1]["result"], arm, arm_step=arm_step,
        starting_date_raw=start, target_date_raw=deadline, speed=3, mode="decision_epoch",
        watch_army_ids=tuple(watches), sentinel_scope=scope)
    _validate_tactical_daily_sentinel_decision_boundary(stop, arm_status=arm,
        starting_date_raw=start, target_date_raw=deadline, ending_date_raw=end, elapsed_days=days,
        speed=3, mode="decision_epoch", watch_army_ids=tuple(watches), player_decision_boundary=boundary,
        player_decision_boundary_cancel=inner.get("player_decision_boundary_cancel"))
    return {"schema":"g2.queue.ordinary-result-credit/v1", "selected_step":step,
        "service_status":"executed", "result_status":"postcondition",
        "category":scope+"_player_decision_interrupted_observed", "source_gameplay_frame":dict(binding),
        "player_decision_boundary":dict(boundary), "player_decision_boundary_cancel":inner.get("player_decision_boundary_cancel"),
        "original_action_steps":steps, "sentinel_generation":generation,
        "actual_date_delta_raw":end-start, "actual_elapsed_days":days, "requested_horizon_days":horizon,
        "paired_after_metrics_still_required":True, "date_advance_observed":days>0,
        "typed_nonmaterial_observation":True, "submitted_pending":False, "primitive_accepted":False,
        "material_verified":False, "ui_action_credit":False, "action_credit":False,
        "lifestyle_material_verified":False, "council_material_verified":False,
        "construction_material_verified":False, "construction_start_verified":False,
        "construction_completion_verified":False, "crown_material_verified":False,
        "existing_typed_material_verified":False, "business_success_inferred":False, "replay_allowed":False}
