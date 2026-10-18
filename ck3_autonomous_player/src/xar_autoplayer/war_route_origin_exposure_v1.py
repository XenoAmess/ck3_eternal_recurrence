"""Do not extend a contact-free day to a longer committed movement leg.

Uses existing Native timelines, defensive objectives, route queries and risk
admission. No new command, battle model, or attack permission is introduced.
"""

def assess_origin_exposure_v1(horizon, *, subject_army_id, origin_province_id,
        target_province_id, hostile_army_ids, date_raw, native_revision):
    from xar_autoplayer.bridge.war_contract import normalize_route_contact_horizon
    try:
        h = normalize_route_contact_horizon(horizon,
            expected_subject_army_id=subject_army_id,
            expected_target_province_id=target_province_id,
            expected_hostile_army_ids=hostile_army_ids,
            expected_date_raw=date_raw,expected_snapshot_revision=native_revision)
    except ValueError:
        return {'status':'unavailable','veto':False,'reason':'fresh_native_timeline_unavailable'}
    subject = h['subject_route']
    route, arrivals = subject['route_province_ids'],subject['arrival_date_raws']
    if (subject.get('current_province_id') != origin_province_id or not route
            or len(route) != len(arrivals) or not subject.get('timeline_observable')
            or type(arrivals[0]) is not int or arrivals[0] <= date_raw):
        return {'status':'unavailable','veto':False,'reason':'subject_first_arrival_not_observable'}
    first_arrival = arrivals[0]
    exposures = []
    for hostile in h['hostile_routes']:
        if hostile.get('timeline_observable') is not True:
            continue
        for province,arrival in zip(hostile['route_province_ids'],hostile['arrival_date_raws']):
            if (province == origin_province_id and type(arrival) is int
                    and date_raw <= arrival <= first_arrival):
                exposures.append({'hostile_army_id':hostile['army_id'],
                    'province_id':origin_province_id,'hostile_arrival_date_raw':arrival,
                    'subject_first_arrival_date_raw':first_arrival,
                    'origin_exposure_hours':first_arrival-arrival})
                break
    return {'schema':'xar.ck3.pre-move-origin-exposure/v1','status':'available',
        'veto':bool(exposures),'reason':('hostile_enters_origin_before_subject_first_arrival'
            if exposures else 'no_observed_origin_entry_before_subject_first_arrival'),
        'subject_army_id':subject_army_id,'origin_province_id':origin_province_id,
        'target_province_id':target_province_id,'first_arrival_date_raw':first_arrival,
        'native_timeline_exposures':exposures,'complete_hostile_army_ids':list(hostile_army_ids),
        'source_native_revision':native_revision,'source_date_raw':date_raw,
        'first_day_contact_free':h['one_day_contact_free'],
        'movement_abortability':'not_observed; native halt can reject a committed leg',
        'full_route_safety_or_battle_win_proven':False}


def select_safe_reposition_v1(observed, *, original_general, strategy,
        baseline, commands, snapshot, action_steps, bridge_capabilities):
    if not isinstance(observed, dict) or not isinstance(snapshot, dict):
        return observed
    admission = observed.get('contact_admission')
    known_rejection = (observed.get('phase') == 'native_war_general_battle_model_rejected'
        or isinstance(observed.get('stationary_model_rejection_continuation_v1'), dict))
    origin_exposure = (observed.get('phase') == 'native_war_pre_move_origin_exposure_rejected'
        and isinstance(observed.get('pre_move_origin_exposure_v1'),dict)
        and observed['pre_move_origin_exposure_v1'].get('veto') is True)
    if not ((known_rejection or origin_exposure) and isinstance(admission, dict)
            and admission.get('admitted') is False
            and admission.get('reason') == ('native_origin_entry_before_subject_first_arrival'
                if origin_exposure else 'bounded_model_risk_budget_exceeded')):
        return observed
    hint = snapshot.get('top_exclusive_modal_choice_hint')
    actor = snapshot.get('played_character')
    if not (snapshot.get('paused') is True and snapshot.get('map_ready') is True
            and 'active_event' in snapshot and snapshot['active_event'] is None
            and 'pending_character_interaction' in snapshot and snapshot['pending_character_interaction'] is None
            and 'top_exclusive_modal_choice_hint' in snapshot
            and not (isinstance(hint, dict) and hint.get('status') == 'present')
            and isinstance(actor, dict) and actor.get('alive') is True):
        return observed
    from xar_autoplayer.bridge.native_driver import (
        _army_is_known_stationary, _army_in_combat_or_retreat,
        _route_contact_hostile_ids, _action_steps,
    )
    from xar_autoplayer.bridge.war_contract import (
        enemy_armies_from_wars, preview_move_army_step,
        query_route_contact_horizon_step, move_army_step,
    )
    armies = snapshot.get('player_armies')
    own = [a for a in armies if isinstance(a, dict) and a.get('controllable') is True] if isinstance(armies, list) else []
    if len(own) != 1:
        return observed
    army = own[0];army_id = army.get('army_id');origin = army.get('current_province_id')
    if not (type(army_id) is int and type(origin) is int and origin > 0
            and army.get('owner_character_id') == actor.get('character_id')
            and army.get('route_province_ids') == [] and 'move_target_province_id' in army
            and army['move_target_province_id'] is None and army.get('in_combat') is False
            and army.get('retreating') is False and _army_is_known_stationary(army)
            and not _army_in_combat_or_retreat(army)):
        return observed
    wars = snapshot.get('active_wars')
    if not isinstance(wars, list):
        return observed
    enemies = enemy_armies_from_wars([w for w in wars if isinstance(w, dict)])
    hostiles = _route_contact_hostile_ids(snapshot)
    if not 0 < len(hostiles) <= 64:
        return observed
    active_enemies = [e for e in enemies if e.get('army_id') in hostiles]
    # This leaf is specifically an escape from observed approaching hostile
    # movement. It does not replace active combat or infer arrival times.
    incoming = [e for e in active_enemies if e.get('current_province_id') != origin
        and (e.get('move_target_province_id') == origin
             or origin in (e.get('route_province_ids') if isinstance(e.get('route_province_ids'), list) else []))]
    if not incoming:
        return observed
    rows = list(commands)
    advertised = set(_action_steps(sorted(bridge_capabilities), snapshot['active_event'],
        snapshot['pending_character_interaction'], wars, armies, paused=True))
    root = strategy._same_frame_campaign_root_context(rows, snapshot)
    held = strategy._complete_player_held_county_capital_province_ids(root) if isinstance(root, dict) else None
    seeds = {}
    for war in wars:
        if not (isinstance(war, dict) and war.get('player_side') == 'defender'):
            continue
        objectives = war.get('war_objective_province_ids')
        states = war.get('objective_province_states')
        if not isinstance(objectives, list) or not isinstance(states, list):
            continue
        by_id = {s.get('province_id'):s for s in states if isinstance(s, dict)}
        for province in objectives:
            state = by_id.get(province)
            if (type(province) is int and province > 0 and isinstance(state, dict)
                    and state.get('occupation_observable') is True and state.get('is_occupied') is False):
                seeds.setdefault(province, {'source':'observed_unoccupied_defensive_objective', 'war_id':war.get('war_id')})
    for province in held if isinstance(held, list) else []:
        if type(province) is int and province > 0:
            seeds.setdefault(province, {'source':'complete_same_frame_directly_held_county_capital','war_id':None})
    danger = set()
    for e in active_enemies:
        for value in (e.get('current_province_id'), e.get('move_target_province_id'),
                *(e.get('route_province_ids') if isinstance(e.get('route_province_ids'), list) else [])):
            if type(value) is int and value > 0:
                danger.add(value)
    rejected = []
    def decorate(plan, target, source, stage):
        return {**plan, 'active_wars':wars, 'safe_reposition_after_model_rejection_v1':{
            'schema':'xar.ck3.safe-reposition-after-model-rejection/v1',
            'stage':stage,'subject_army_id':army_id,'origin_province_id':origin,
            'candidate_province_id':target,'candidate_source':source,
            'incoming_hostile_army_ids':sorted({e['army_id'] for e in incoming}),
            'all_hostile_army_ids':list(hostiles),'candidate_rejections':rejected,
            'original_model_rejection':admission,'original_phase':observed.get('phase'),
            'original_selected_step':observed.get('selected_step'),
             'rejected_battle_forecast':observed.get('battle_forecast'),
             'origin_exposure':observed.get('pre_move_origin_exposure_v1'),
            'arrival_guaranteed':False,'safe_retreat_achieved':False,
            'new_attack_authorization':False,'unknown_modal_is_absence_proof':False}}
    for target, source in sorted(seeds.items()):
        if target == origin or target in danger:
            rejected.append({'province_id':target,'status':'current_or_observed_hostile_path'});continue
        preview_step = preview_move_army_step(army_id,target)
        move_step = move_army_step(army_id,target)
        if preview_step not in action_steps or preview_step not in advertised:
            rejected.append({'province_id':target,'status':'preview_not_advertised'});continue
        preview = strategy._fresh_move_route_preview(rows, army_id=army_id,
            origin_province_id=origin,target_province_id=target,date_raw=snapshot.get('date_raw'),snapshot=snapshot)
        if preview is None:
            return decorate({'policy':'one-life-turn-v1','phase':'native_war_route_preview',
                'selected_step':preview_step,'active_attack_allowed':False,
                'reason':'the proposed attack was rejected and a hostile is approaching; preview a real alternate defensive objective or held capital before choosing an escape'},target,source,'preview')
        if preview.get('status') != 'available':
            rejected.append({'province_id':target,'status':'native_preview_unavailable','native_preview':preview});continue
        audit = strategy._audit_war_route(preview.get('route_province_ids'),
            origin_province_id=origin,target_province_id=target,enemies=active_enemies)
        # No one-day override of an unsafe whole-route geometry here.
        if audit.get('status') != 'safe':
            rejected.append({'province_id':target,'status':'route_geometry_rejected','route_audit':audit});continue
        query = query_route_contact_horizon_step(army_id,target,hostiles)
        contact = strategy._fresh_route_contact_horizon(rows,snapshot,army_id=army_id,
            origin_province_id=origin,target_province_id=target,hostile_army_ids=hostiles,
            route_province_ids=preview.get('route_province_ids'))
        if contact is None:
            failed = strategy._current_frame_route_contact_query_failure(rows,snapshot,query)
            if failed is None and query in action_steps and query in advertised:
                return decorate({'policy':'one-life-turn-v1','phase':'native_war_candidate_contact_horizon',
                    'selected_step':query,'active_attack_allowed':False,'route_preview':preview,'route_audit':audit,
                    'reason':'test the alternate escape route against every observed hostile native timeline; no movement is authorized by this query'},target,source,'contact_query')
            rejected.append({'province_id':target,'status':'fresh_full_hostile_horizon_unavailable'});continue
        if contact.get('one_day_contact_free') is not True:
            rejected.append({'province_id':target,'status':'contact_not_free','contact_horizon':contact});continue
        exposure = assess_origin_exposure_v1(contact,subject_army_id=army_id,
            origin_province_id=origin,target_province_id=target,hostile_army_ids=hostiles,
            date_raw=snapshot.get('date_raw'),native_revision=snapshot.get('native_revision'))
        if exposure.get('veto') is True:
            rejected.append({'province_id':target,'status':'origin_exposed_before_first_arrival',
                'origin_exposure':exposure});continue
        if move_step not in action_steps or move_step not in advertised:
            rejected.append({'province_id':target,'status':'native_move_not_advertised'});continue
        if strategy._active_native_move_intent(rows,snapshot,army_id=army_id,target_province_id=target) is not None:
            rejected.append({'province_id':target,'status':'existing_move_intent_no_resubmit'});continue
        backoff = strategy._deferred_move_backoff(rows,snapshot,move_step)
        if isinstance(backoff,dict) and backoff.get('retry_due') is not True:
            rejected.append({'province_id':target,'status':'native_move_backoff_no_resubmit'});continue
        replacement = {'policy':'one-life-turn-v1','phase':'native_war_pursuit','selected_step':move_step,
            'active_attack_allowed':False,'active_wars':wars,'route_preview':preview,
            'route_audit':{**audit,'contact_horizon':contact},
            'pursuit':{'army_id':army_id,'target_province_id':target,'target_source':source['source']},
            'reason':'avoid the rejected battle by a separately previewed, full-hostile checked route to an observed alternate; actual arrival remains unverified'}
        guarded = original_general(replacement,commands=rows,snapshot=snapshot,
            action_steps=action_steps,bridge_capabilities=bridge_capabilities)
        if guarded.get('active_attack_allowed') is True:
            rejected.append({'province_id':target,'status':'alternate_would_authorize_attack'});continue
        # The original ingress may require a read-only actual/projected contact
        # query first. It retains that exact step and all its Native guards.
        return decorate(guarded,target,source,'original_general_review')
    if held is None and 'query-campaign-root-context-v1' in action_steps:
        return decorate({'policy':'one-life-turn-v1','phase':'native_war_safe_objective_context',
            'selected_step':'query-campaign-root-context-v1','active_attack_allowed':False,
            'reason':'the known defensive objectives did not yield a safe escape; read current complete directly held county capitals before declaring alternatives exhausted'},None,{'source':'same_frame_root_required'},'root_query')
    return decorate(observed,None,{'source':'no_qualified_alternate'},'not_selected')



def _qualified_origin_contact(plan, exposure, snapshot):
    """Preserve existing same-frame risk admission for this origin encounter.

    A destination forecast cannot certify the exposed origin. This function
    never creates permission; it checks an already-selected general admission.
    """
    from .simulation.general_battle_forecast import contact_admission
    encounter = plan.get('encounter')
    forecast = plan.get('general_battle_forecast')
    admission = plan.get('general_battle_contact_admission')
    if not (plan.get('general_battle_forecast_used_for_decision') is True
            and isinstance(encounter, dict) and isinstance(forecast, dict)
            and isinstance(admission, dict) and admission.get('admitted') is True
            and encounter.get('target_province_id') == exposure['origin_province_id']
            and forecast.get('capture') == {key: snapshot.get(key) for key in (
                'snapshot_id', 'revision', 'native_revision', 'date_raw')}
            and contact_admission(forecast).get('admitted') is True):
        return False
    attackers, defenders = encounter.get('attacker_army_ids'), encounter.get('defender_army_ids')
    if not (isinstance(attackers, list) and isinstance(defenders, list)
            and all(type(ident) is int for ident in attackers + defenders)):
        return False
    subject = exposure['subject_army_id']
    if (subject in attackers) == (subject in defenders):
        return False
    opponents = set(defenders if subject in attackers else attackers)
    incoming = {row['hostile_army_id'] for row in exposure['native_timeline_exposures']}
    return bool(incoming) and incoming <= opponents


def review_war_route_origin_exposure_v1(observed, *, commands, snapshot,
        action_steps, bridge_capabilities):
    """Review the selected order after the ordinary general ingress."""
    from . import strategy
    original = strategy._general_battle_forecast_ingress
    baseline = observed
    from xar_autoplayer.bridge.native_driver import _route_contact_hostile_ids
    from xar_autoplayer.bridge.war_contract import parse_move_army_step
    parsed = parse_move_army_step(observed.get('selected_step')) if isinstance(observed,dict) else None
    if parsed is not None and isinstance(snapshot,dict):
        army_id,target = parsed
        armies = snapshot.get('player_armies')
        army = next((a for a in armies if isinstance(a,dict) and a.get('army_id')==army_id),None) if isinstance(armies,list) else None
        # Prevention applies before committing an idle army. An already
        # submitted move cannot be undone or called halted by this policy.
        if (isinstance(army,dict) and army.get('route_province_ids')==[]
                and 'move_target_province_id' in army and army['move_target_province_id'] is None):
            origin = army.get('current_province_id');hostiles = _route_contact_hostile_ids(snapshot)
            preview = strategy._fresh_move_route_preview(list(commands),army_id=army_id,
                origin_province_id=origin,target_province_id=target,
                date_raw=snapshot.get('date_raw'),snapshot=snapshot)
            contact = strategy._fresh_route_contact_horizon(list(commands),snapshot,
                army_id=army_id,origin_province_id=origin,target_province_id=target,
                hostile_army_ids=hostiles,route_province_ids=preview.get('route_province_ids')) if isinstance(preview,dict) else None
            exposure = assess_origin_exposure_v1(contact,subject_army_id=army_id,
                origin_province_id=origin,target_province_id=target,hostile_army_ids=hostiles,
                date_raw=snapshot.get('date_raw'),native_revision=snapshot.get('native_revision'))
            if exposure.get('veto') is True and _qualified_origin_contact(observed, exposure, snapshot):
                return observed
            if exposure.get('veto') is True:
                observed = {**observed,'phase':'native_war_pre_move_origin_exposure_rejected',
                    'selected_step':None,'active_attack_allowed':False,
                    'reason':'the fresh native timeline puts a hostile at the origin before this army reaches its first waypoint; one contact-free day cannot justify the longer committed leg',
                    'pre_move_origin_exposure_v1':exposure,
                    'contact_admission':{'admitted':False,'reason':'native_origin_entry_before_subject_first_arrival'},
                    'original_move_plan_v1':observed}
    return select_safe_reposition_v1(observed,original_general=original,strategy=strategy,
        baseline=baseline,commands=commands,snapshot=snapshot,action_steps=action_steps,
        bridge_capabilities=bridge_capabilities)
