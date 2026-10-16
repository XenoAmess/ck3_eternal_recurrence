"""Pure AST-installable zero-credit observation for a returned UI callback.

None delegates to existing branches. No SDK import, native call, action replay,
or queue mutation occurs. Pair after-metrics and pause/readback remain required.
"""

def classify_war_results_start_binding_v1(body, *, initial_frame=None, game_pid=None):
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

def classify_war_results_scope_transition_pending_v1(body, *, initial_frame=None, game_pid=None):
    """Retain a real UI close scope transition with zero closure/day credit."""
    import json
    import re

    if not isinstance(body, dict):
        return None
    result, plan = body.get('result'), body.get('plan')
    if not isinstance(result, dict):
        return None
    reason = result.get('unavailable_reason')
    if not isinstance(reason, str) or not reason.startswith('war_results_ui_scope_transition;'):
        return None
    def require(condition, message):
        if not condition:
            raise ValueError('war results scope-transition pending differs: ' + message)
    step = 'close-war-results-window-v1'
    binding = classify_war_results_start_binding_v1(body, initial_frame=initial_frame, game_pid=game_pid)
    require(len(json.dumps(body, ensure_ascii=False).encode('utf-8')) <= 1024**2
        and body.get('status') == 'pending' and body.get('selected_step') == step
        and body.get('ui_action_credit') is False and isinstance(plan, dict)
        and plan.get('policy') == 'ordinary-war-results-window-v1'
        and plan.get('phase') == 'war_results_window' and plan.get('selected_step') == step
        and plan.get('pending_actions') == [step]
        and type(game_pid) is int and game_pid > 0 and binding.get('bridge_pid') == game_pid,
        'ordinary close plan or actual Game source')
    require(result.get('schema') == 'ck3-war-results-window-v1'
        and result.get('sdk_validation_schema') == 'war-results-window-source-v1'
        and result.get('backend_id') == 'native-headless' and result.get('step') == step
        and result.get('operation') == 'close' and result.get('window_name') == 'war_results'
        and result.get('button_name') == 'close_button'
        and result.get('status') == 'verification_pending' and result.get('available') is False
        and result.get('accepted') is False and result.get('closure_verified') is False
        and result.get('scope_unchanged') is False
        and all(result.get(k) is True for k in ('root_observed','window_present','effective_visible',
            'application_owner_thread_verified','paused','dispatch_attempted','dispatch_invoked','native_handled'))
        and result.get('dismiss_stage') == 'callback_returned'
        and type(result.get('dismiss_exception_code')) is int and result['dismiss_exception_code'] == 0
        and result.get('root_observation_source') == 'guarded_top_level_and_complete_owner_tree'
        and result.get('game_version') == '1.20.0.4'
        and result.get('executable_sha256') == '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518',
        'returned fixed callback, qualified owner or zero-credit pending status')
    match = re.fullmatch(
        r'war_results_ui_scope_transition;begin_date_raw=(-?[0-9]+);end_date_raw=(-?[0-9]+);begin_paused=true;end_paused=false;owner_boundary_admitted=true',
        reason)
    require(match is not None, 'actual Native begin/end scope diagnostic')
    begin, end = map(int, match.groups())
    require(str(begin) == match[1] and str(end) == match[2]
            and -(2**31) <= begin <= end <= 2**31-1 and begin == binding.get('date_raw'),
            'forward Native date transition from actual planning frame')
    for wire, key in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),
        ('queried_native_revision','native_revision'),('native_revision','native_revision'),
        ('queried_date_raw','date_raw'),('date_raw','date_raw'),
        ('queried_actor_character_id','actor_character_id'),('played_character_id','actor_character_id'),
        ('queried_episode_run_id','episode_run_id'),('queried_connection_generation','connection_generation'),
        ('connection_generation','connection_generation')):
        require(type(result.get(wire)) is type(binding.get(key)) and result[wire] == binding[key],
                'original request lease '+wire)
    for key in ('post_observed','post_window_present','post_effective_visible'):
        require(type(result.get(key)) is bool, 'actual post flag '+key)
    require(not result['post_effective_visible'] or result['post_window_present'],
            'post visibility requires a window')
    if result['post_observed']:
        require(result.get('post_observation_source') == 'guarded_top_level_and_complete_owner_tree',
                'actual post source')
    else:
        require(result.get('post_observation_source') == '', 'unobserved post source')
    native, rid = result.get('native_command_result'), result.get('request_id')
    owner = native.get('war_results_window_owner_receipt') if isinstance(native, dict) else None
    require(isinstance(rid,str) and rid.startswith('war-overview-close-')
        and len(rid)>len('war-overview-close-') and result.get('native_request_id') == rid
        and isinstance(native,dict) and native.get('type') == 'command_result'
        and type(native.get('protocol_version')) is int and native['protocol_version'] == 1
        and native.get('ok') is True and native.get('request_id') == rid
        and isinstance(owner,dict) and owner.get('request_id') == rid
        and all(type(result.get(k)) is int and result[k]>0 and type(owner.get(k)) is int
                and owner[k] == result[k] for k in ('ticket_sequence','pump_epoch','thread_id','date_raw','connection_generation'))
        and owner.get('executor_started_sequence') == owner.get('completed_sequence') == result['ticket_sequence'],
        'independently completed original owner ticket')
    return {'schema':'g2.queue.ordinary-result-credit/v1','selected_step':step,
        'service_status':'pending','result_status':'verification_pending',
        'category':'war_results_close_scope_transition_pending_observed',
        'ui_verification_pending':True,'war_results_window_closed_verified':False,
        'submitted_pending':True,'primitive_accepted':False,'typed_nonmaterial_observation':True,
        'source_gameplay_frame':dict(binding),'source_native_request_id':rid,
        'source_native_owner_receipt':dict(owner),'original_native_ui_scope_diagnostic':reason,
        'observed_callback_begin_date_raw':begin,'observed_callback_end_date_raw':end,
        'original_close_outcome':'verification_pending','readonly_ui_query_required':True,
        'pause_readback_required':True,'new_close_retry_authorized':False,
        'actual_elapsed_days':0,'actual_date_delta_raw':0,'date_advance_observed':False,
        'ui_action_credit':False,'action_credit':False,'existing_typed_material_verified':False,
        'lifestyle_material_verified':False,'existing_focus_verified':False,'council_material_verified':False,
        'construction_material_verified':False,'construction_start_verified':False,
        'construction_completion_verified':False,'crown_material_verified':False,'crown_receipt_nonmaterial':False,
        'business_success_inferred':False,'paired_after_metrics_still_required':True,'replay_allowed':False}
