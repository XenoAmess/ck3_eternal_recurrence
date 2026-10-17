"""Synthetic Native I/O; real public Driver.execute_step; no runtime connection.

The ordinary plan/Service envelope is a test fixture, not Service.auto_turn output.
The startup baseline is six fields observed before the current planning frame.
"""
import ast
import copy
import importlib
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def configure(source_root):
    global NativeHeadlessGameplayDriver, native, fixtures
    global battle_decision_epoch_advance_step, committed_route_sentinel_advance_step
    source_root = Path(source_root).resolve()
    sdk = source_root / "ck3_autonomous_player/src"
    sys.path.insert(0, str(sdk))
    native = importlib.import_module("xar_autoplayer.bridge.native_driver")
    require(Path(native.__file__).resolve() == sdk / "xar_autoplayer/bridge/native_driver.py", "wrong Driver import")
    NativeHeadlessGameplayDriver = native.NativeHeadlessGameplayDriver
    war = importlib.import_module("xar_autoplayer.bridge.war_contract")
    battle_decision_epoch_advance_step = war.battle_decision_epoch_advance_step
    committed_route_sentinel_advance_step = war.committed_route_sentinel_advance_step
    path = source_root / "ck3_autonomous_player/tests/unit/test_native_bridge_driver.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"FakeEndpoint", "_hello", "_snapshot", "_army", "_war", "_tactical_sentinel_status"}
    nodes = [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.ClassDef)) and x.name in names]
    require(len(nodes) == len(names), "public Native I/O fixture is incomplete")
    fixtures = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), fixtures)


def producer(scope, kind, state, *, elapsed=1, already_paused=None, army_id=501):
    endpoint = fixtures["FakeEndpoint"]()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        command_timeout_seconds=.1, life_advance_timeout_seconds=.1)
    endpoint.publish(fixtures["_hello"]("game.state.snapshot", "game.command.set-speed-3",
        "game.command.resume-map", "game.command.pause-map",
        "game.command.research-arm-tactical-daily-sentinel-v1-N",
        "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
        "game.command.research-query-tactical-daily-sentinel-v1"))
    start = 53400000
    deadline = start + (4 if scope == "active_battle" else 1)*24
    end = start + elapsed*24
    player = fixtures["_army"](army_id, in_combat=scope == "active_battle", retreating=False,
        move_target_province_id=None if scope == "active_battle" else 11,
        army_state="regular" if scope == "active_battle" else "moving",
        army_state_code=1 if scope == "active_battle" else 7,
        route_province_ids=[] if scope == "active_battle" else [11])
    enemy = fixtures["_army"](601, controllable=False, province_id=11, in_combat=scope == "active_battle",
        route_province_ids=[])
    war = fixtures["_war"](allied_armies=[player], enemy_armies=[enemy])
    played = {"character_id":707,"alive":True}
    def snapshot(rev, date, *, paused=True, modal=False):
        event = {"source":"native","instance_id":47,"option_count":1,
                 "options":[{"index":0,"option_number":1,"enabled":True}]} if modal and kind == "active_event" else None
        pending = {"instance_id":-2130706341,"sender_character_id":808,"auto_accept_notification":False} if modal and kind == "pending_character_interaction" else None
        return fixtures["_snapshot"](rev,date_raw=date,speed=3,paused=paused,active_event=event,
            pending_character_interaction=pending,played_character=played,active_wars=[war],player_armies=[player])
    endpoint.publish(snapshot(10,start-24))
    startup_snapshot = driver.take_internal_semantic_snapshot()
    endpoint.publish(snapshot(11,start))
    before = driver.take_internal_semantic_snapshot()
    combat_count = 1 if scope == "active_battle" else 0
    arm = fixtures["_tactical_sentinel_status"](state="armed",generation=42,starting_date_raw=start,
        target_date_raw=deadline,observed_date_raw=start,speed=3,mode="decision_epoch",army_count=1,combat_count=combat_count)
    if state == "idle":
        stop = dict(arm,state="idle")
        statuses = [arm, stop]
    else:
        reasons = [r for r in native._TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS
                   if r == "native_pause" or r == "date_deadline" and end == deadline]
        flags = sum(1 << native._TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS.index(r) for r in reasons)
        stop = fixtures["_tactical_sentinel_status"](state="triggered",generation=42,starting_date_raw=start,
            target_date_raw=deadline,observed_date_raw=end,speed=3,mode="decision_epoch",army_count=1,
            combat_count=combat_count,completed_daily_ticks=elapsed,intermediate_pause_count=1,
            trigger_flags=flags,trigger_reasons=reasons,overshoot_days=0,pause_wrapper_called=False,pause_observed=True)
        statuses = [stop]
    paused_on_resume = state == "triggered" if already_paused is None else already_paused
    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        step = frame["step"]
        result = {"step":step,"accepted":True,"status":"submitted"}
        if step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            result.update(status="available",tactical_daily_sentinel=arm)
        elif step == "research-query-tactical-daily-sentinel-v1":
            result.update(status="available",tactical_daily_sentinel=statuses.pop(0))
        elif step.startswith("research-cancel-tactical-daily-sentinel-v1-generation-"):
            result["status"] = "canceled"
        endpoint.publish({"type":"command_result","protocol_version":1,"request_id":frame["request_id"],"ok":True,"result":result})
        if step == "set-speed-3":
            endpoint.publish(snapshot(12,start))
        elif step == "resume-map":
            endpoint.publish(snapshot(13,end,paused=paused_on_resume,modal=True))
        elif step == "pause-map":
            endpoint.publish(snapshot(14,end,modal=True))
    endpoint.send_hook = answer
    step = battle_decision_epoch_advance_step(deadline) if scope == "active_battle" else committed_route_sentinel_advance_step(army_id,11,deadline)
    result = driver.execute_step(step,expected_revision=before["revision"])
    require(result["progress_status"] == "postcondition" and result["stop_kind"] == "player_decision", "real producer postcondition")
    require(result["revision"] != result["native_revision"] and before["revision"] != before["native_revision"], "separate public/native fixture")
    frame_source = {k:before[k] for k in ("snapshot_id","revision","native_revision","date_raw","episode_run_id")}
    frame_source.update(status="complete",actor_character_id=707,bridge_pid=4242,
        connection_generation=before["diagnostics"]["connection_generation"])
    plan = {"selected_step":step,"absolute_target_date_raw":deadline,"active_wars":[{"war_id":61}]}
    if scope == "active_battle":
        plan.update(phase="native_war_global_battle_decision_epoch",timeline_policy="battle_decision_epoch_speed_3",timeline_speed=3,watch_army_ids=[army_id])
    else:
        plan.update(phase="native_war_committed_route_contact_trial",risk_assessment_kind="observed_three_to_two_margin_not_win_probability",
            friendly_current_soldiers=1500,enemy_current_soldiers=1000,friendly_ai_base_power_raw=1500,enemy_ai_base_power_raw=1000,
            first_contact_province_id=11,contact_horizon={"status":"available","one_day_contact_free":False,
            "date_raw":start,"horizon_start_date_raw":start,"horizon_end_date_raw":deadline,"subject_army_id":army_id,
            "target_province_id":11,"hostile_army_ids":[601],"subject_route":{"army_id":army_id,"timeline_observable":True,
                "current_province_id":10,"route_province_ids":[11],"arrival_date_raws":[deadline]},
            "hostile_routes":[{"army_id":601,"timeline_observable":True,"current_province_id":11,"effective_origin_province_id":11,"route_province_ids":[],"arrival_date_raws":[]}],
            "conflicts":[{"hostile_army_id":601,"kind":"same_province","province_id":11,"overlap_start_date_raw":deadline,"overlap_end_date_raw":deadline}]})
    body = {"status":"executed","selected_step":step,"plan":plan,"planning_source_frame":frame_source,"result":result}
    after = driver.take_internal_semantic_snapshot()
    def metrics(s):
        return {**{k:s[k] for k in ("snapshot_id","revision","native_revision","date_raw","episode_run_id","paused","map_ready")},
                "actor_character_id":707,"actor_alive":True}
    return body, metrics(startup_snapshot), metrics(before), metrics(after), copy.deepcopy(endpoint.frames)


def classify_gameplay_start_binding_v1(body, *, initial_frame=None, game_pid=None):
    """Bind gameplay evidence to the observed plan frame, independently of presentation."""
    plan = body.get("plan") if isinstance(body.get("plan"), dict) else {}
    inner = body.get("result") if isinstance(body.get("result"), dict) else {}
    if "planning_source_frame" in body:
        source = body["planning_source_frame"]
        if not isinstance(source, dict) or source.get("status") != "complete":
            raise ValueError("actual planning source frame is partial")
        binding = dict(source)
    elif "starting_frame" in inner:
        source = inner["starting_frame"]
        if not isinstance(source, dict):
            raise ValueError("actual composite starting frame is malformed")
        binding = dict(source)
    elif "query_source" in plan:
        source = plan["query_source"]
        if not isinstance(source, dict):
            raise ValueError("actual plan query source is malformed")
        binding = dict(source)
    else:
        risk = plan.get("player_risk_context")
        goal = plan.get("campaign_goal_plan_used")
        if not isinstance(risk, dict) or not isinstance(goal, dict):
            raise ValueError("independent legacy gameplay frame is absent")
        source = risk.get("binding")
        scope = risk.get("current_scope")
        if not isinstance(source, dict) or not isinstance(scope, dict):
            raise ValueError("independent legacy gameplay frame is malformed")
        binding = dict(source)
        binding["actor_character_id"] = source.get("character_id")
        binding["episode_run_id"] = goal.get("campaign_id")
        binding["connection_generation"] = scope.get("connection_generation")
        if goal.get("current_character_id") != binding["actor_character_id"]:
            raise ValueError("legacy gameplay actor sources differ")
    if (not isinstance(initial_frame, dict)
            or type(initial_frame.get("actor_character_id")) is not int
            or not isinstance(initial_frame.get("episode_run_id"), str)
            or not initial_frame["episode_run_id"]
            or type(binding.get("actor_character_id")) is not int
            or binding["actor_character_id"] != initial_frame["actor_character_id"]
            or binding.get("episode_run_id") != initial_frame["episode_run_id"]
            or any(type(binding.get(k)) is not int or binding[k] <= 0 for k in
                   ("revision", "native_revision", "date_raw", "connection_generation"))
            or binding.get("snapshot_id") != "native:" + str(binding["native_revision"])):
        raise ValueError("gameplay starting actor/episode/frame binding differs")
    pid = binding.get("bridge_pid")
    if pid is not None and (type(pid) is not int or pid <= 0
                            or game_pid is not None and pid != game_pid):
        raise ValueError("gameplay starting process binding differs")
    return binding
