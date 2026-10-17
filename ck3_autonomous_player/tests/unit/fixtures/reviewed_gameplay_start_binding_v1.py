"""Reviewed production binder excerpt; SHA pinned in publication source index."""

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
