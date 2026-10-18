"""Concentrate separated idle armies before reconsidering a local engagement.

The current count comparison selects an observation purpose, never a battle
permission. Existing route, origin-exposure, Native move and merge contracts
remain authoritative. No split, combat, retained move, or other war is replaced.
"""


def assess_rendezvous_locked_route_v1(horizon):
    """Veto known contact during committed legs, beyond the H1 flag.

    This is a conservative inference from published full current-order ETAs,
    not a new Native contact-free proof. A province remains exposed until its
    next arrival; reversed edges with overlapping traversal windows conflict.
    """
    if not isinstance(horizon, dict):
        return {'status':'unavailable','veto':True}
    subject=horizon.get('subject_route');start=horizon.get('date_raw')
    if not (isinstance(subject,dict) and type(start)is int
            and subject.get('route_province_ids') and subject.get('arrival_date_raws')):
        return {'status':'unavailable','veto':True}
    end=subject['arrival_date_raws'][-1]

    def windows(route):
        points=[(route['current_province_id'],start),*zip(route['route_province_ids'],route['arrival_date_raws'])]
        visits=[];edges=[]
        for index,(province,date) in enumerate(points):
            next_date=points[index+1][1] if index+1<len(points) else end
            if date<=end:
                visits.append((province,date,min(next_date,end)))
            if index and points[index-1][1]<=end:
                edges.append((points[index-1][0],province,points[index-1][1],min(date,end)))
        return visits,edges

    own_visits,own_edges=windows(subject);conflicts=[]
    for enemy in horizon['hostile_routes']:
        visits,edges=windows(enemy)
        for p,a,b in own_visits:
            for q,c,d in visits:
                if p==q and max(a,c)<=min(b,d):
                    conflicts.append({'kind':'projected_locked_province_overlap','hostile_army_id':enemy['army_id'],
                        'province_id':p,'overlap_start_date_raw':max(a,c),'overlap_end_date_raw':min(b,d)})
        for p,q,a,b in own_edges:
            for r,t,c,d in edges:
                if p==t and q==r and max(a,c)<=min(b,d):
                    conflicts.append({'kind':'projected_locked_opposing_edge','hostile_army_id':enemy['army_id'],
                        'from_province_id':p,'to_province_id':q,
                        'overlap_start_date_raw':max(a,c),'overlap_end_date_raw':min(b,d)})
    return {'schema':'xar.ck3.rendezvous-locked-route-exposure/v1','status':'available',
        'veto':bool(conflicts),'known_route_conflicts':conflicts,
        'evaluated_until_date_raw':end,'native_h1_end_date_raw':horizon['horizon_end_date_raw'],
        'source':'conservative inference from full Native current-order route/arrival arrays',
        'future_orders_or_safe_arrival_proven':False}


def review_safe_war_rendezvous_v1(baseline, *, commands, snapshot,
        action_steps, bridge_capabilities):
    from . import strategy
    from .bridge.native_driver import _route_contact_hostile_ids
    from .bridge.war_contract import (MERGE_ARMIES_CAPABILITY,
        enemy_armies_from_wars, move_army_step, preview_move_army_step,
        query_route_contact_horizon_step, normalize_route_contact_horizon)
    from .war_route_origin_exposure_v1 import assess_origin_exposure_v1

    if not (isinstance(baseline, dict) and isinstance(snapshot, dict)
            and baseline.get('phase') == 'native_war_stationary_objective_hold_sentinel'
            and isinstance(baseline.get('selected_step'), str)
            and baseline['selected_step'].startswith('war-objective-hold-sentinel-advance-')
            and baseline.get('active_attack_allowed') is not True
            and MERGE_ARMIES_CAPABILITY in bridge_capabilities):
        return baseline
    actor = snapshot.get('played_character')
    hint = snapshot.get('top_exclusive_modal_choice_hint')
    if not (snapshot.get('paused') is True and snapshot.get('map_ready') is True
            and 'active_event' in snapshot and snapshot['active_event'] is None
            and 'pending_character_interaction' in snapshot and snapshot['pending_character_interaction'] is None
            and 'top_exclusive_modal_choice_hint' in snapshot
            and not (isinstance(hint, dict) and hint.get('status') == 'present')
            and isinstance(actor, dict) and actor.get('alive') is True
            and type(actor.get('character_id')) is int
            and snapshot.get('army_strengths_queried_snapshot_id') == snapshot.get('snapshot_id')
            and snapshot.get('army_strengths_queried_revision') == snapshot.get('revision')):
        return baseline
    # This first consumer only rearranges one primary defensive war. Moving a
    # shared army away from another active war needs a separate assignment.
    wars = snapshot.get('active_wars')
    if not (isinstance(wars, list) and len(wars) == 1 and isinstance(wars[0], dict)):
        return baseline
    war = wars[0]
    if not (war.get('player_side') == 'defender'
            and war.get('player_is_primary_war_leader') is True
            and type(war.get('player_relative_war_score')) is int
            and war['player_relative_war_score'] < 0):
        return baseline
    armies = snapshot.get('player_armies')
    if not (isinstance(armies, list) and len(armies) > 1 and all(
            isinstance(a, dict) and type(a.get('army_id')) is int
            and a.get('owner_character_id') == actor['character_id']
            and a.get('controllable') is True and a.get('army_state') == 'regular'
            and a.get('in_combat') is False and a.get('retreating') is False
            and a.get('route_read_status') == 'complete_empty'
            and a.get('route_province_ids') == []
            and 'move_target_province_id' in a and a['move_target_province_id'] is None
            and type(a.get('current_province_id')) is int and a['current_province_id'] > 0
            for a in armies)):
        return baseline
    own_ids = {a['army_id'] for a in armies}
    if len(own_ids) != len(armies) or len({a['current_province_id'] for a in armies}) == 1:
        return baseline  # Original co-located CanMerge selection is retained.
    balance = strategy._same_frame_army_strength_balance(snapshot, war.get('war_id'))
    strength_rows = snapshot.get('army_strengths')
    if not isinstance(strength_rows, list):
        return baseline
    strengths = {r['army_id']:r['current_soldiers'] for r in strength_rows
        if isinstance(r, dict) and r.get('status') == 'available'
        and r.get('scope_role') == 'player' and isinstance(r.get('war_ids'), list)
        and war.get('war_id') in r['war_ids']
        and type(r.get('army_id')) is int and type(r.get('current_soldiers')) is int}
    if not isinstance(balance, dict) or set(strengths) != own_ids or any(n <= 0 for n in strengths.values()):
        return baseline
    hostiles = _route_contact_hostile_ids(snapshot)
    enemies = enemy_armies_from_wars(wars)
    if not 0 < len(hostiles) <= 64:
        return baseline
    enemy_strengths = {r['army_id']:r['current_soldiers'] for r in strength_rows
        if isinstance(r, dict) and r.get('status') == 'available'
        and r.get('scope_role') == 'active_war_enemy'
        and type(r.get('army_id')) is int and type(r.get('current_soldiers')) is int}
    if set(enemy_strengths) != set(hostiles):
        return baseline
    local_groups = {}
    for enemy in enemies:
        if (enemy.get('army_id') in hostiles and enemy.get('in_combat') is False
                and enemy.get('retreating') is False and enemy.get('route_province_ids') == []
                and type(enemy.get('current_province_id')) is int):
            local_groups.setdefault(enemy['current_province_id'], set()).add(enemy['army_id'])
    total = sum(strengths.values())
    opportunities = [{'province_id':p, 'enemy_army_ids':sorted(ids),
        'observed_current_soldiers':sum(enemy_strengths[i] for i in ids)}
        for p, ids in sorted(local_groups.items())
        if max(strengths.values()) < sum(enemy_strengths[i] for i in ids) < total]
    if not opportunities:
        return baseline
    state_rows = war.get('objective_province_states')
    objectives = war.get('war_objective_province_ids')
    if not isinstance(state_rows, list) or not isinstance(objectives, list):
        return baseline
    states = {r.get('province_id'):r for r in state_rows if isinstance(r, dict)}
    anchors = [a for a in sorted(armies, key=lambda a:(-strengths[a['army_id']], a['army_id']))
        if a['current_province_id'] in objectives
        and states.get(a['current_province_id'], {}).get('occupation_observable') is True
        and states[a['current_province_id']].get('is_occupied') is False]
    rows = list(commands)
    rejections = []

    def decorate(plan, anchor, mover, stage, **extra):
        return {**plan, 'active_wars':wars, 'active_attack_allowed':False,
            'war_safe_rendezvous_v1':{'schema':'xar.ck3.safe-war-rendezvous/v1',
                'stage':stage, 'war_id':war['war_id'], 'anchor_army_id':anchor['army_id'],
                'moving_army_id':mover['army_id'], 'rendezvous_province_id':anchor['current_province_id'],
                'all_controlled_army_ids':sorted(own_ids), 'all_hostile_army_ids':list(hostiles),
                'local_opportunities':opportunities, 'observed_own_total':total,
                'observed_all_hostile_total':sum(enemy_strengths.values()),
                'other_hostiles_and_future_arrivals_not_ignored':True,
                'battle_win_probability':None, 'attack_authorized':False,
                'arrival_guaranteed':False, 'merge_accepted':False,
                'candidate_rejections':rejections, **extra}}

    def query_plan(step, phase, reason, anchor, mover, **extra):
        if step not in action_steps:
            return None
        return decorate({'policy':'one-life-turn-v1','phase':phase,
            'selected_step':step,'reason':reason}, anchor, mover, 'observe', **extra)

    for anchor in anchors:
        target = anchor['current_province_id']
        for mover in sorted(armies, key=lambda a:(strengths[a['army_id']], a['army_id'])):
            origin = mover['current_province_id']; ident = mover['army_id']
            if origin == target:
                continue
            preview_step = preview_move_army_step(ident, target)
            preview = strategy._fresh_move_route_preview(rows, army_id=ident,
                origin_province_id=origin, target_province_id=target,
                date_raw=snapshot.get('date_raw'), snapshot=snapshot)
            if preview is None:
                candidate = query_plan(preview_step,'native_war_route_preview',
                    'read a route to the existing defensive army before considering concentration; no attack is authorized',anchor,mover)
                if candidate is not None:
                    return candidate
                continue
            audit = strategy._audit_war_route(preview.get('route_province_ids'),
                origin_province_id=origin,target_province_id=target,enemies=enemies)
            if preview.get('status') != 'available' or audit.get('status') != 'safe':
                rejections.append({'army_id':ident,'target':target,'reason':'whole_route_geometry_unavailable_or_unsafe'})
                continue
            horizons = {}
            for own in [mover, *[a for a in armies if a is not mover]]:
                subject = own['army_id']; destination = target if subject == ident else own['current_province_id']
                route = preview['route_province_ids'] if subject == ident else []
                horizon = strategy._fresh_route_contact_horizon(rows,snapshot,army_id=subject,
                    origin_province_id=own['current_province_id'],target_province_id=destination,
                    hostile_army_ids=hostiles,route_province_ids=route)
                step = query_route_contact_horizon_step(subject,destination,hostiles)
                if horizon is None:
                    if strategy._current_frame_route_contact_query_failure(rows,snapshot,step) is None:
                        candidate = query_plan(step,'native_war_candidate_contact_horizon',
                            'check this army and every waiting friendly against all observed hostile timelines before a rendezvous move',anchor,mover)
                        if candidate is not None:
                            return candidate
                    break
                try:
                    horizon=normalize_route_contact_horizon(horizon,expected_subject_army_id=subject,
                        expected_target_province_id=destination,expected_hostile_army_ids=hostiles,
                        expected_date_raw=snapshot.get('date_raw'),expected_snapshot_revision=snapshot.get('native_revision'))
                except ValueError:
                    break
                horizons[subject] = horizon
            if len(horizons) != len(armies) or any(h.get('one_day_contact_free') is not True for h in horizons.values()):
                rejections.append({'army_id':ident,'target':target,'reason':'complete_friendly_full_hostile_h1_not_free'})
                continue
            contact = horizons[ident]
            if any(h['hostile_routes'] != contact['hostile_routes'] for h in horizons.values()):
                rejections.append({'army_id':ident,'target':target,'reason':'friendly_horizons_disagree_on_hostile_timelines'})
                continue
            locked_route=assess_rendezvous_locked_route_v1(contact)
            if locked_route.get('status')!='available' or locked_route.get('veto')is True:
                rejections.append({'army_id':ident,'target':target,'reason':'known_contact_during_committed_route',
                    'locked_route_exposure':locked_route})
                continue
            exposure = assess_origin_exposure_v1(contact,subject_army_id=ident,
                origin_province_id=origin,target_province_id=target,hostile_army_ids=hostiles,
                date_raw=snapshot.get('date_raw'),native_revision=snapshot.get('native_revision'))
            arrivals = contact['subject_route']['arrival_date_raws']
            if exposure.get('status') != 'available' or exposure.get('veto') is True or not arrivals:
                rejections.append({'army_id':ident,'target':target,'reason':'origin_exposed_during_locked_leg'})
                continue
            waiting = {a['current_province_id'] for a in armies if a['army_id'] != ident}
            # H1 publishes complete current route ETAs. Do not extend its
            # contact-free flag; separately reject a known entry into a
            # waiting friendly before the proposed mover's final arrival.
            waiting_exposure = [h['army_id'] for h in contact['hostile_routes']
                if h['current_province_id'] in waiting or any(p in waiting and d <= arrivals[-1]
                    for p,d in zip(h['route_province_ids'],h['arrival_date_raws']))]
            if waiting_exposure:
                rejections.append({'army_id':ident,'target':target,'reason':'waiting_friendly_exposed_before_rendezvous',
                    'hostile_army_ids':waiting_exposure})
                continue
            step = move_army_step(ident,target)
            if (step not in action_steps
                    or strategy._active_native_move_intent(rows,snapshot,army_id=ident,target_province_id=target) is not None):
                continue
            backoff = strategy._deferred_move_backoff(rows,snapshot,step)
            if isinstance(backoff,dict) and backoff.get('retry_due') is not True:
                continue
            return decorate({'policy':'one-life-turn-v1','phase':'native_war_pursuit','selected_step':step,
                'reason':f'两军分驻，先向现有己军所在防御目标{target}集中；己军合计{total}，局部已观测敌军{opportunities[0]["observed_current_soldiers"]}，全部已观测敌军{sum(enemy_strengths.values())}含在途。仅选择经独立核验的会合路线；抵达、原生合并及新战斗评估后再决策，未授接战',
                'pursuit':{'army_id':ident,'target_province_id':target,'target_source':'existing_defensive_friendly_rendezvous'},
                'route_preview':preview,'route_audit':{**audit,'contact_horizon':contact}},
                anchor,mover,'move_candidate', origin_exposure=exposure,
                locked_route_exposure=locked_route,
                predicted_rendezvous_date_raw=arrivals[-1],
                observation_required='native committed-route daily stops and independent arrival; original CanMerge and fresh forecast afterwards')
    if anchors:
        return decorate(baseline,anchors[0],armies[0],'not_selected')
    return baseline
