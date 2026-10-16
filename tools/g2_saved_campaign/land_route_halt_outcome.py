"""Classify a guarded land-route Halt ACK or its exact pre-submit veto.

The caller supplies its reviewed gameplay-frame binding validator. A returned
pending ACK does not prove that movement stopped. A typed validator veto is a
nonmaterial observation and grants no action, business, or date credit.

This portable extraction accepts the public CUnit ID zero. The deployed P30
classifier's original SHA remains unchanged and is archived separately.
"""

def classify_land_route_halt_result_v1(body, *, bind_gameplay_frame, initial_frame=None, game_pid=None):
    if not isinstance(body,dict):return None
    plan=body.get('plan')
    if not isinstance(plan,dict) or plan.get('phase')!='native_war_land_route_timeline_unavailable_halt_submit':return None
    def require(ok,message):
        if not ok:raise ValueError('land route Halt result rejected: '+message)
    step=body.get('selected_step');inner=body.get('result')
    require(isinstance(step,str) and step.startswith('halt-army-'),'canonical Halt step required')
    token=step.removeprefix('halt-army-')
    require(token.isdecimal() and str(int(token))==token and 0<=int(token)<=2**31-1,'canonical full CUnitID required')
    army=int(token);binding=bind_gameplay_frame(body,initial_frame=initial_frame,game_pid=game_pid)
    intent=plan.get('halt_intent');attempt=plan.get('contact_query_attempt')
    require(body.get('status')=='executed' and plan.get('policy')=='one-life-turn-v1'
        and plan.get('selected_step')==step and isinstance(inner,dict) and inner.get('step')==step
        and isinstance(intent,dict) and intent.get('army_id')==army
        and intent.get('postcondition_required')=='fresh_route_empty_or_verified_retained_first_edge'
        and intent.get('contact_free_proven') is False,'actual plan/intent unavailable')
    route=intent.get('original_route_province_ids');current=intent.get('current_province_id');target=intent.get('original_move_target_province_id')
    require(isinstance(route,list) and 2<=len(route)<=4096
        and all(type(x) is int and 0<x<=2**31-1 for x in route)
        and type(current) is int and current>0 and type(target) is int and target==route[-1], 'actual committed route tuple absent')
    require(isinstance(attempt,dict) and attempt.get('scope_status')=='current_frame'
        and attempt.get('status')=='unavailable' and attempt.get('ok') is False,'same-frame unavailable route query absent')
    action=inner.get('war_action')
    require(isinstance(action,dict) and action.get('army_id')==army,'actual army result differs')
    if inner.get('schema')=='xar.halt-army-validator-deferred/v1':
        require(inner.get('accepted') is False and inner.get('status')=='deferred'
            and inner.get('business_submission') is False and inner.get('replay_allowed') is False
            and inner.get('backend_id')=='native-headless'
            and action.get('status')=='halt_validator_rejected_current_route_retained'
            and action.get('reason')=='native_halt_validator_rejected'
            and action.get('current_province_id')==current and action.get('move_target_province_id')==target
            and action.get('route_province_ids')==route and action.get('contact_free_proven') is False,
            'deferred veto must never become an accepted Halt')
        evidence=inner.get('halt_rejection_evidence')
        require(isinstance(evidence,dict),'original native veto evidence absent')
        request,result,observed=evidence.get('native_request'),evidence.get('native_command_result'),evidence.get('observed_frame')
        rid=evidence.get('native_request_id')
        require(isinstance(rid,str) and 0<len(rid)<=256 and isinstance(request,dict) and isinstance(result,dict)
            and request.get('type')=='execute_step' and type(request.get('protocol_version')) is int and request['protocol_version']==1
            and request.get('request_id')==rid and request.get('step')==step and request.get('expected_revision')==binding['native_revision']
            and result.get('type')=='command_result' and type(result.get('protocol_version')) is int and result['protocol_version']==1
            and result.get('request_id')==rid and result.get('ok') is False
            and result.get('error')=='CK3 halt-army command validation failed' and not isinstance(result.get('result'),dict)
            and ('step' not in result or result['step']==step),'exact original pre-submit native validator veto differs')
        require(isinstance(observed,dict)
            and all(observed.get(k)==binding.get(k) for k in ('date_raw','actor_character_id','episode_run_id','bridge_pid','connection_generation'))
            and type(observed.get('native_revision')) is int and observed['native_revision']>=binding['native_revision']
            and type(observed.get('revision')) is int and observed['revision']>=binding['revision']
            and observed.get('snapshot_id')=='native:'+str(observed['native_revision'])
            and all(inner.get(k)==observed[k] for k in ('snapshot_id','revision','native_revision')),
            'independent current same-Game owner/date/route readback differs')
        return {'schema':'g2.queue.ordinary-result-credit/v1','selected_step':step,'service_status':'executed','result_status':'deferred',
            'category':'halt_validator_rejected_route_retained_observed','source_gameplay_frame':binding,
            'halt_rejection_evidence':evidence,'accepted':False,'business_submission':False,'submitted_pending':False,
            'primitive_accepted':False,'typed_nonmaterial_observation':True,'fresh_snapshot_verified':True,
            'date_advance_observed':False,'actual_date_delta_raw':0,'actual_elapsed_days':0,
            'material_verified':False,'ui_action_credit':False,'action_credit':False,'business_success_inferred':False,
            'halt_postcondition_verified':False,'stopped_army_inferred':False,'contact_free_proven':False,
            'paired_after_metrics_still_required':True,'replay_allowed':False}
    require(inner.get('accepted') is True and inner.get('status') in ('submitted','completed','halt_submitted')
        and action.get('status')=='halt_submitted' and action.get('postcondition_verified') is False
        and action.get('submitted_date_raw')==binding['date_raw']
        and action.get('original_current_province_id')==current and action.get('original_move_target_province_id')==target
        and action.get('original_route_province_ids')==route and action.get('owner_character_id')==binding['actor_character_id']
        and action.get('submitted_native_revision')==binding['native_revision']
        and action.get('submitted_connection_generation')==binding['connection_generation']
        and action.get('submitted_episode_run_id')==binding['episode_run_id'],'native accepted Halt must retain its full original pending tuple')
    starting={'route_province_ids':list(route),'current_province_id':current,'move_target_province_id':target,
        'owner_character_id':binding['actor_character_id'],'native_revision':binding['native_revision'],'revision':binding['revision'],
        'connection_generation':binding['connection_generation'],'episode_run_id':binding['episode_run_id'],'game_pid':binding['bridge_pid']}
    return {'schema':'g2.queue.ordinary-result-credit/v1','selected_step':step,'service_status':'executed','result_status':inner['status'],
        'category':'unsafe_route_halt_submitted_pending','submitted_pending':True,'primitive_accepted':True,
        'halt_army_id':army,'halt_date_raw':binding['date_raw'],'halt_actor_character_id':binding['actor_character_id'],
        'halt_episode_run_id':binding['episode_run_id'],'halt_connection_generation':binding['connection_generation'],
        'halt_game_pid':binding['bridge_pid'],'halt_source_native_revision':binding['native_revision'],
        'halt_source_revision':binding['revision'],'halt_source_snapshot_id':binding['snapshot_id'],
        'halt_current_province_id':current,'halt_unsafe_move_target_province_id':target,'halt_starting_tuple':starting,
        'halt_postcondition_verified':False,'stopped_army_inferred':False,'business_success_inferred':False,
        'contact_free_proven':False,'replay_allowed':False}
