"""Bounded ordinary retreat proposal and once-only typed submission candidate.

Normal-turn policy supplies an explicit loss budget and retains battle/war
priorities. Native retains legality/token/membership checks. Current one-hop
friendly-rally screening is an observed local condition, not a future-safety or
pursuit-loss forecast. No default retreat risk budget is invented here.
"""
from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os

from xar_autoplayer.bridge.active_combat_retreat_contract import (
    normalize_active_combat_retreat_v1_preview, preview_active_combat_retreat_v1_step,
)
from xar_autoplayer.bridge.native_driver import _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES
from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
from xar_autoplayer.bridge.battle_transition_contract import normalize_battle_transition_v1
from xar_autoplayer.bridge.battle_terminal_transition_contract import normalize_battle_terminal_transition_v1
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick
from xar_autoplayer.simulation.battle_current_retreat_policy import assess_current_battle_retreat
from xar_autoplayer.simulation.combat_core import DrawState

STATE_FILE = 'ordinary-retreat-once-v1'


def normal_retreat_loss_budget(snapshot, control):
    """Our 5% one-frozen-tick preservation policy for a losing territorial defence.

    This is deliberately not a native AI threshold or a predicted battle loss.
    The war score, target exposure and current Combat entries remain separate.
    Greater campaign stakes are reported; retreat never settles those stakes.
    """
    actor = (snapshot.get('played_character') or {}).get('character_id')
    wars = [war for war in snapshot.get('active_wars', [])
            if isinstance(war, Mapping) and war.get('player_is_primary_war_leader') is True
            and war.get('player_side') == 'defender'
            and type(war.get('player_relative_war_score')) is int
            and war['player_relative_war_score'] < 0
            and isinstance(war.get('targeted_title_ids'), list)
            and any(type(value) is int and value >= 0 for value in war['targeted_title_ids'])]
    unavailable = {'status': 'unavailable', 'maximum_next_tick_hard_loss_raw': None,
                   'policy': 'own-losing-territorial-defence-owner-hard-loss-5pct-v1',
                   'battle_win_probability': None, 'retreat_pursuit_losses_raw': None,
                   'defeat_title_transfer_verified': False}
    if not wars or control.get('side_index') not in (0, 1):
        return {**unavailable, 'reason': 'no_current_losing_own_territorial_defence'}
    own = control.get('attacker' if control['side_index'] == 0 else 'defender')
    enemy = control.get('defender' if control['side_index'] == 0 else 'attacker')
    if not isinstance(own, Mapping) or not isinstance(enemy, Mapping):
        return {**unavailable, 'reason': 'current_combat_entries_unavailable'}
    opposing_ids = {row.get('public_cunit_id') for row in enemy.get('ordered_armies', [])
                    if isinstance(row, Mapping) and type(row.get('public_cunit_id')) is int}
    wars = [war for war in wars if isinstance(war.get('enemy_armies'), list)
            and any(isinstance(army, Mapping) and army.get('army_id') in opposing_ids
                    for army in war['enemy_armies'])]
    if not opposing_ids or not wars:
        return {**unavailable, 'reason': 'current_opposing_cunits_not_related_to_losing_territorial_defence'}
    own_current, enemy_current = own.get('derived_current_fighting_raw'), enemy.get('derived_current_fighting_raw')
    if not (type(own_current) is int and type(enemy_current) is int
            and 0 < own_current <= enemy_current):
        return {**unavailable, 'reason': 'current_combat_headcount_disadvantage_not_observed'}
    entries = [*own.get('levy_entries', []), *own.get('men_at_arms_entries', [])]
    owner_entries = [row for row in entries if isinstance(row, Mapping) and row.get('owner_character_id') == actor]
    if (not owner_entries or any(type(row.get('current_fighting_raw')) is not int
                                or row['current_fighting_raw'] < 0 for row in owner_entries)):
        return {**unavailable, 'reason': 'selected_owner_current_entries_unavailable'}
    remaining = sum(row['current_fighting_raw'] for row in owner_entries)
    if remaining <= 0:
        return {**unavailable, 'reason': 'selected_owner_current_entries_empty'}
    return {**unavailable, 'status': 'observed', 'reason': 'preserve_army_for_continued_defence',
            'maximum_next_tick_hard_loss_raw': remaining * 5 // 100,
            'maximum_next_tick_fraction_percent': 5, 'owner_current_fighting_raw': remaining,
            'current_own_side_fighting_raw': own_current, 'current_enemy_side_fighting_raw': enemy_current,
            'observed_opposing_public_cunit_ids': sorted(opposing_ids),
            'battle_warscore_attribution_verified': False,
            'comparison_scope': 'current fighting headcount, not effective combat power or victory probability',
            'losing_defensive_wars': [{key: war.get(key) for key in
                ('war_id', 'player_relative_war_score', 'targeted_title_ids')} for war in wars],
            'budget_source': 'explicit_ordinary_counter_policy_not_native_AI_threshold'}


def _budget_assessment(control, budget, preview=None):
    tick = run_frozen_main_tick(adapt_current_battle_condition(control), draw_state=DrawState(0, 0))
    return assess_current_battle_retreat(control, maximum_next_tick_hard_loss_raw=budget,
                                        frozen_main_tick=tick, retreat_preview=preview)


def _rallies(snapshot, combat_province):
    armies=snapshot.get('player_armies')
    if not isinstance(armies,list):return []
    threats=set()
    wars=snapshot.get('active_wars')
    if not isinstance(wars,list) or not wars:return []
    for war in wars:
        if not isinstance(war,Mapping) or not isinstance(war.get('enemy_armies'),list):return []
        for enemy in war['enemy_armies']:
            if not isinstance(enemy,Mapping):return []
            status=enemy.get('route_read_status')
            route=enemy.get('route_province_ids')
            target=enemy.get('move_target_province_id')
            if not ((status=='complete_empty' and route==[] and target is None)
                    or (status=='complete_nonempty' and isinstance(route,list) and route
                        and type(target) is int and target>0 and route[-1]==target)):
                return []
            if (type(enemy.get('current_province_id')) is not int or enemy['current_province_id']<=0
                    or not isinstance(enemy.get('route_province_ids'),list)
                    or any(type(value) is not int or value<=0 for value in enemy['route_province_ids'])):
                return []
            for province in (enemy.get('current_province_id'),enemy.get('move_target_province_id'),
                             *(enemy.get('route_province_ids') or [])):
                if type(province) is int and province>0:threats.add(province)
    result=[]
    for army in armies:
        if not isinstance(army,Mapping):continue
        province=army.get('current_province_id')
        if (army.get('controllable') is True and army.get('in_combat') is False
                and army.get('owner_character_id')==snapshot.get('played_character',{}).get('character_id')
                and army.get('retreating') is False and not army.get('route_province_ids')
                and army.get('move_target_province_id') is None
                and army.get('army_state') in {'idle','regular'} and type(province) is int and province>0
                and type(army.get('soldiers')) is int and army['soldiers']>0
                and province!=combat_province and province not in threats and province not in result):
            result.append(province)
    return result


def propose_retreat(snapshot, control, native_caps, *, maximum_next_tick_hard_loss_raw,
                    preview=None, prior_intent=None):
    """Return a typed proposal only; the normal planner still owns execution."""
    if isinstance(prior_intent,Mapping):
        return {'stage':'observe_original_only','reason':'original_retreat_intent_retained','submit_allowed':False}
    if not _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES <= set(native_caps):
        return {'stage':'unavailable','reason':'underlying_Native_capability_missing','submit_allowed':False}
    if (snapshot.get('paused') is not True or snapshot.get('map_ready') is not True
            or control.get('snapshot_revision')!=snapshot.get('native_revision')
            or control.get('observed_date_raw')!=snapshot.get('date_raw')):
        return {'stage':'query_current_control','reason':'current_control_binding_required','submit_allowed':False}
    actor=snapshot.get('played_character') or {}
    subject=control.get('selected_public_cunit_id')
    selected=[row for row in snapshot.get('player_armies',[]) if row.get('army_id')==subject]
    if (actor.get('alive') is not True or actor.get('character_id')!=control.get('selected_owner_character_id')
            or snapshot.get('active_event') is not None or snapshot.get('pending_character_interaction') is not None
            or snapshot.get('one_life_settlement') is not None or len(selected)!=1
            or selected[0].get('controllable') is not True or selected[0].get('in_combat') is not True
            or selected[0].get('retreating') is not False
            or selected[0].get('current_province_id')!=control.get('combat_province_id')):
        return {'stage':'retain_ordinary_battle_policy','reason':'ordinary_current_subject_or_modal_guard','submit_allowed':False}
    try:
        control=normalize_battle_control_snapshot_v1(control,expected_subject_public_cunit_id=subject,
            expected_observed_date_raw=snapshot['date_raw'],expected_snapshot_revision=snapshot['native_revision'])
        assessment=_budget_assessment(control,maximum_next_tick_hard_loss_raw)
    except (ValueError,KeyError,TypeError) as error:
        return {'stage':'current_loss_unavailable','reason':str(error),'submit_allowed':False}
    if assessment.get('recommendation')!='query_retreat_preview':
        return {'stage':'retain_ordinary_battle_policy','assessment':assessment,'submit_allowed':False}
    targets=_rallies(snapshot,control.get('combat_province_id'))
    if not targets:
        return {'stage':'no_observed_rally','assessment':assessment,'submit_allowed':False,
                'missing':'No alternative stationary controllable rally outside observed hostile positions/routes.'}
    if preview is None:
        return {'stage':'preview','selected_step':preview_active_combat_retreat_v1_step(subject,targets[0]),
                'target_province_id':targets[0],'assessment':assessment,'submit_allowed':False}
    try:
        target=preview.get('target_province_id')
        normalized=normalize_active_combat_retreat_v1_preview(preview,
            expected_selected_public_cunit_id=subject,expected_target_province_id=target,
            expected_snapshot_revision=snapshot['revision'])
        route=normalized['target_preview']['route_province_ids']
        if (target not in targets or route not in ([target],[control['combat_province_id'],target])
                or normalized['source_binding']['snapshot_id']!=snapshot.get('snapshot_id')
                or normalized['source_binding']['episode_run_id']!=snapshot.get('episode_run_id')
                or normalized['source_binding']['native_revision']!=snapshot.get('native_revision')
                or normalized['source_binding']['date_raw']!=snapshot.get('date_raw')
                or normalized['source_binding']['connection_generation']!=snapshot.get('diagnostics',{}).get('connection_generation')):
            return {'stage':'preview_rejected','reason':'one_hop_rally_or_source_changed','submit_allowed':False}
        assessment=_budget_assessment(normalized['battle_control_snapshot'],maximum_next_tick_hard_loss_raw,normalized)
    except (ValueError,KeyError,TypeError) as error:
        return {'stage':'preview_rejected','reason':str(error),'submit_allowed':False}
    if assessment.get('recommendation')!='order_active_combat_retreat':
        return {'stage':'retain_ordinary_battle_policy','assessment':assessment,'submit_allowed':False}
    return {'stage':'order','assessment':assessment,'arguments':assessment['retreat_order_arguments'],
            'submit_allowed':True,'destination_screen':'current_one_hop_friendly_rally_no_known_hostile_route',
            'future_target_safety_proven':False,'pursuit_losses_known':False,
            'source_binding':normalized['source_binding'],
            'selected_owner_character_id':control['selected_owner_character_id'],
            'affected_public_cunit_ids_in_stored_order':normalized['affected_public_cunit_ids_in_stored_order'],
            'unaffected_same_side_public_cunit_ids_in_stored_order':normalized['unaffected_same_side_public_cunit_ids_in_stored_order'],
            'route_province_ids':route}


def intent_path(state_dir, episode_run_id, arguments):
    # Target/token are deliberately excluded: changing either cannot resend an
    # unresolved retreat for this episode/subject/full CombatID.
    key=json.dumps([episode_run_id,arguments['selected_public_cunit_id'],arguments['expected_combat_id']],
                   separators=(',',':')).encode('utf-8')
    return Path(state_dir)/(STATE_FILE+'-'+hashlib.sha256(key).hexdigest()[:24]+'.json')


def submit_once(service, state_dir: Path, proposal, *, machine_id, episode_run_id):
    """One persisted intent before typed Service order; unknown is never resent.

    This stores intent/ACK only. Independent Core plus prior-Combat transition
    remains owned by the normal runner before the intent may be resolved.
    """
    if proposal.get('stage')!='order' or proposal.get('submit_allowed') is not True:
        return {'status':'not_submitted','submit_attempted':False}
    arguments=proposal.get('arguments')
    if not isinstance(arguments,dict):raise ValueError('exact typed order arguments required')
    if (not machine_id or not episode_run_id or
            proposal.get('source_binding',{}).get('episode_run_id')!=episode_run_id):
        raise ValueError('machine and exact episode binding required')
    state_dir=Path(state_dir)
    state_dir.mkdir(parents=True,exist_ok=True)
    path=intent_path(state_dir,episode_run_id,arguments)
    identity=json.dumps(arguments,sort_keys=True).encode('utf-8')
    intent={'schema':'ordinary-retreat-once-candidate/v1','machine_id':machine_id,
            'episode_run_id':episode_run_id,'order_sha256':hashlib.sha256(identity).hexdigest(),
            'arguments':arguments,'status':'submitting','replay_allowed':False,
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'source_binding':proposal['source_binding'],
            'selected_owner_character_id':proposal['selected_owner_character_id'],
            'affected_public_cunit_ids_in_stored_order':proposal['affected_public_cunit_ids_in_stored_order'],
            'unaffected_same_side_public_cunit_ids_in_stored_order':proposal['unaffected_same_side_public_cunit_ids_in_stored_order'],
            'route_province_ids':proposal['route_province_ids']}
    try:
        descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    except FileExistsError:
        # Even an interrupted/partial intent file is an unresolved attempt.
        return {'status':'observe_original_only','submit_attempted':False,'replay_allowed':False}
    with os.fdopen(descriptor,'w',encoding='utf-8') as output:
        output.write(json.dumps(intent,ensure_ascii=False,sort_keys=True)+'\n')
        output.flush()
        os.fsync(output.fileno())
    try:
        result=service.order_active_combat_retreat_v1(**arguments)
    except Exception as error:
        intent.update(status='unknown',error=f'{type(error).__name__}: {error}')
        write_json_atomic(path,intent)
        return {'status':'unknown','submit_attempted':True,'replay_allowed':False}
    rejected = result.get('accepted') is False and result.get('status') == 'rejected'
    intent.update(status='native_rejected' if rejected else 'ack_retained_independent_post_required',ack=result)
    write_json_atomic(path,intent)
    return {'status':intent['status'],'submit_attempted':True,'ack':result,
            'operational_retreat_verified':False,'replay_allowed':False}


def verify_independent_post(intent, snapshot, transition):
    """Read-only result projection; never replay or infer full war success.

    A disappearing CombatID needs the existing terminal reader; this small
    candidate leaves that branch pending instead of inventing a terminal DTO.
    Join/reopen likewise stays pending for ordinary battle lifecycle handling.
    """
    pending={'status':'independent_post_pending','operational_retreat_verified':False,
             'command_causation_verified':False,
             'replay_allowed':False,'war_outcome_verified':False}
    source=intent['source_binding']
    if (snapshot.get('episode_run_id')!=intent['episode_run_id']
            or snapshot.get('diagnostics',{}).get('connection_generation')!=source['connection_generation']
            or snapshot.get('revision',-1)<=source['revision']
            or snapshot.get('snapshot_id')==source['snapshot_id']
            or snapshot.get('native_revision',-1)<source['native_revision']
            or snapshot.get('date_raw',-1)<source['date_raw']
            or snapshot.get('paused') is not True or snapshot.get('map_ready') is not True
            or snapshot.get('played_character',{}).get('character_id')!=intent['selected_owner_character_id']):
        return {**pending,'reason':'independent_same_episode_current_post_required'}
    arguments=intent['arguments']
    try:
        transition=normalize_battle_transition_v1(transition,
            expected_combat_id=arguments['expected_combat_id'],
            expected_observed_date_raw=snapshot['date_raw'],expected_snapshot_revision=snapshot['native_revision'])
    except (ValueError,TypeError,KeyError) as error:
        return {**pending,'reason':str(error)}
    if transition['status']!='available':
        return {**pending,'reason':'original_combat_not_available_requires_existing_terminal_query'}
    armies=snapshot.get('player_armies',[])
    rows=[]
    for unit in intent['affected_public_cunit_ids_in_stored_order']:
        matches=[row for row in armies if row.get('army_id')==unit]
        valid=(len(matches)==1 and matches[0].get('retreating') is True
               and matches[0].get('in_combat') is False
               and matches[0].get('owner_character_id')==intent['selected_owner_character_id']
               and matches[0].get('move_target_province_id')==arguments['target_province_id']
               and matches[0].get('route_province_ids')==intent['route_province_ids'])
        rows.append({'public_cunit_id':unit,'retreat_target_route_observed':valid})
    if not all(row['retreat_target_route_observed'] for row in rows):
        return {**pending,'reason':'affected_retreat_target_route_not_independently_complete','affected':rows}
    own_side='attacker' if arguments['expected_side_index']==0 else 'defender'
    members=transition[own_side+'_public_cunit_ids_in_stored_order']
    if arguments['expected_scope']=='owner_subset':
        lifecycle=(not set(intent['affected_public_cunit_ids_in_stored_order']) & set(members)
                   and set(intent['unaffected_same_side_public_cunit_ids_in_stored_order'])<=set(members))
    else:
        lifecycle=(transition['winner_raw']==1-arguments['expected_side_index']
                   and transition['phase'] in ('pursuit','done'))
    if not lifecycle:
        return {**pending,'reason':'scope_lifecycle_or_real_reinforcement_reopen_requires_observation','affected':rows}
    return {**pending,'status':'operational_retreat_observed','operational_retreat_verified':True,
            'affected':rows,'scope':arguments['expected_scope'],
            'post_public_revision':snapshot['revision'],'post_native_revision':snapshot['native_revision']}


def verify_terminal_post(intent, snapshot, terminal):
    """Consume the existing journal DTO after removal; only full-side closure.

    No journal event, suppressed outcome, missing subject or real reentry stays
    pending. The normal battle reader continues handling those lifecycle cases.
    """
    pending = {'status': 'independent_post_pending', 'operational_retreat_verified': False,
               'command_causation_verified': False,
               'replay_allowed': False, 'war_outcome_verified': False}
    # Reuse the independent Core source guard; the deliberately malformed
    # transition cannot grant success but distinguishes a stale Core.
    check = verify_independent_post(intent, snapshot, {})
    if check.get('reason') == 'independent_same_episode_current_post_required':
        return check
    args = intent['arguments']
    if args['expected_scope'] != 'full_side':
        return {**pending, 'reason': 'removed_owner_subset_retains_existing_lifecycle_reader'}
    try:
        frame = normalize_battle_terminal_transition_v1(terminal,
            expected_prior_combat_id=args['expected_combat_id'],
            expected_subject_public_cunit_id=args['selected_public_cunit_id'],
            expected_after_terminal_sequence=None, expected_observed_date_raw=snapshot['date_raw'],
            expected_snapshot_revision=snapshot['native_revision'])
    except (ValueError, TypeError, KeyError) as error:
        return {**pending, 'reason': str(error)}
    if frame['status'] != 'available':
        return {**pending, 'reason': 'original_terminal_journal_unavailable'}
    prior, removal, subject, successor = (frame[key] for key in ('prior', 'removal', 'subject', 'successor'))
    side_key = 'attacker' if args['expected_side_index'] == 0 else 'defender'
    if not (frame['terminal_journal']['event_status'] == 'observed'
            and prior['terminal_kind'] == 'normal_result'
            and prior['winner_raw'] == 1 - args['expected_side_index']
            and removal['prior_combat_strictly_resolves'] is False
            and prior[side_key + '_public_cunit_ids_in_stored_order'] == intent['affected_public_cunit_ids_in_stored_order']
            and successor['state'] == 'subject_retreating'
            and subject['move_target_province_id'] == args['target_province_id']
            and subject['route_province_ids_in_stored_order'] == intent['route_province_ids']):
        return {**pending, 'reason': 'terminal_kind_original_scope_or_retreat_state_incomplete'}
    for unit in intent['affected_public_cunit_ids_in_stored_order']:
        rows = [army for army in snapshot.get('player_armies', []) if army.get('army_id') == unit]
        if not (len(rows) == 1 and rows[0].get('retreating') is True and rows[0].get('in_combat') is False
                and rows[0].get('owner_character_id') == intent['selected_owner_character_id']
                and rows[0].get('move_target_province_id') == args['target_province_id']
                and rows[0].get('route_province_ids') == intent['route_province_ids']):
            return {**pending, 'reason': 'affected_army_terminal_core_post_incomplete'}
    return {**pending, 'status': 'operational_retreat_observed', 'operational_retreat_verified': True,
            'scope': 'full_side', 'terminal_event_sequence': frame['terminal_journal']['event_sequence'],
            'post_public_revision': snapshot['revision'], 'post_native_revision': snapshot['native_revision']}
