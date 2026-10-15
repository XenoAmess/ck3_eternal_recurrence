"""Only pure player-siege/readonly-army checkpoint cadence changes, 5 -> 10."""
import re


def checkpoint_step_is_readonly(step):
    if not isinstance(step, str):
        return False
    if step.startswith(('query-', 'private-query-')):
        return True
    match = re.fullmatch(r'preview-move-army-(0|[1-9][0-9]{0,9})-to-([1-9][0-9]{0,9})', step)
    return match is not None and int(match[1]) <= 2**31 - 1 and int(match[2]) <= 2**31 - 1


def checkpoint_cycle_may_change_game(pending, after):
    before = pending['before']
    if any(after.get(key) != before.get(key) for key in ('date_raw', 'actor_character_id', 'episode_run_id')):
        return True
    observation = pending.get('observation') or {}
    if observation.get('submitted_pending') is True:
        return True
    if any(observation.get(key) is True for key in (
        'lifestyle_material_verified', 'council_material_verified',
        'construction_start_verified', 'construction_completion_verified',
        'crown_material_verified', 'existing_typed_material_verified',
    )):
        return True
    return not checkpoint_step_is_readonly(pending.get('selected_step'))


def _siege_scope(progress):
    wars = progress.get('wars')
    if not isinstance(wars, list) or not wars:
        raise ValueError('war scope unavailable')
    result, sieges = [], []
    for war in wars:
        wid = war['war_id']
        if type(wid) is not int or wid <= 0:
            raise ValueError('war identity unavailable')
        armies = []
        for side in ('player_armies', 'enemy_armies'):
            for army in war[side]:
                if army['in_combat'] is not False or army['retreating'] is not False:
                    raise ValueError('combat or retreat is outside routine siege')
                armies.append([side, army['army_id'], army['current_province_id'],
                               army['move_target_province_id'], army['route_province_ids'],
                               army['army_state']])
        for province in war['objective_province_states']:
            siege = province.get('active_siege')
            if isinstance(siege, dict) and siege.get('player_army_besieging') is True:
                sieges.append([wid, province['province_id'], siege['siege_id'], siege['besieging_army_id']])
        result.append([wid, war['war_objective_province_ids'], armies,
                       [[p['province_id'], p.get('occupation_observable'), p.get('is_occupied'),
                         p.get('occupying_character_id')] for p in war['objective_province_states']]])
    if not sieges:
        raise ValueError('no active player siege')
    return result, sieges


def checkpoint_context_from_auto(body):
    """Small projection of the already verified AUTO; never reads Game again."""
    try:
        plan, inner, source = body['plan'], body['result'], body['planning_source_frame']
        start, end = inner['starting_date_raw'], inner['ending_date_raw']
        if (body['status'] != 'executed' or body['selected_step'] != 'life-advance'
                or plan['phase'] != 'native_war_siege_progress' or plan['selected_step'] != 'life-advance'
                or inner['step'] != 'life-advance' or inner['backend_id'] != 'native-headless'
                or inner['source'] != 'native-composite' or inner['timeline_policy'] != 'player_siege'
                or inner['progress_status'] != 'postcondition' or inner['paused'] is not True
                or inner['final_screen'] != 'map_hud' or inner['ordinary_events'] != []
                or inner.get('active_event') is not None or inner['elapsed_days'] != 1
                or inner['requested_horizon_days'] != 1 or type(start) is not int
                or type(end) is not int or end-start != 24 or source['status'] != 'complete'
                or source['date_raw'] != start):
            return None
        before, after = inner['war_progress_before'], inner['war_progress_after']
        first, last = _siege_scope(before), _siege_scope(after)
        if (before['date_raw'] != start or after['date_raw'] != end or first != last
                or [w['war_id'] for w in plan['active_wars']] != [w[0] for w in first[0]]):
            return None
        snap, revision = inner['snapshot_id'], inner['revision']
        if (not re.fullmatch(r'native:[1-9][0-9]*', snap) or type(revision) is not int
                or any(type(source[k]) is not int or source[k] <= 0 for k in
                       ('revision', 'native_revision', 'actor_character_id', 'connection_generation', 'bridge_pid'))
                or source['snapshot_id'] != 'native:' + str(source['native_revision'])
                or not isinstance(source['episode_run_id'], str) or not source['episode_run_id']):
            return None
        native = int(snap.split(':')[1])
        if native <= source['native_revision'] or revision <= source['revision']:
            return None
        return {'schema': 'g2.queue.routine-siege-checkpoint-context/v1', 'source_frame': dict(source),
                'after_frame': {'snapshot_id': snap, 'revision': revision, 'native_revision': native,
                                'date_raw': end, 'actor_character_id': source['actor_character_id'],
                                'episode_run_id': source['episode_run_id']}}
    except (KeyError, TypeError, ValueError):
        return None  # Unknown/new phases or scope changes retain the five-cycle policy.


def _paired_context(pending, after):
    context = pending.get('checkpoint_context')
    if not isinstance(context, dict) or context.get('schema') != 'g2.queue.routine-siege-checkpoint-context/v1':
        return False
    source, end, before = context['source_frame'], context['after_frame'], pending['before']
    return (all(source.get(k) == before.get(k) for k in ('date_raw', 'actor_character_id', 'episode_run_id'))
            and all(end.get(k) == after.get(k) for k in
                    ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'actor_character_id', 'episode_run_id'))
            and all(type(before.get(k)) is int and source.get(k, 0) >= before[k]
                    for k in ('revision', 'native_revision')))


def checkpoint_after_settled_cycle(state, pending, after):
    was_dirty = state.get('checkpoint_dirty_since_save', False)
    policy = state.get('checkpoint_policy_v1')
    if not was_dirty:
        policy = {'routine_only': True, 'last_siege_after': None}
    elif not isinstance(policy, dict):
        policy = {'routine_only': False, 'last_siege_after': None}
    paired_siege = _paired_context(pending, after)
    army_read = (pending.get('phase') == 'native_war_army_strength_query'
                 and pending.get('selected_step') == 'query-army-strengths-v1'
                 and not checkpoint_cycle_may_change_game(pending, after))
    if paired_siege:
        policy['last_siege_after'] = dict(after)
    elif not army_read:
        policy['routine_only'] = False
    dirty = was_dirty or checkpoint_cycle_may_change_game(pending, after)
    state['checkpoint_dirty_since_save'] = dirty
    state['checkpoint_policy_v1'] = policy
    last = policy.get('last_siege_after') or {}
    routine = policy['routine_only'] and bool(last) and all(
        last.get(k) == after.get(k) for k in ('date_raw', 'actor_character_id', 'episode_run_id'))
    interval = 10 if routine else 5
    boundary_due = dirty and state['completed_cycles'] % interval == 0
    carried_due = was_dirty and state.get('checkpoint_due_after_readonly_chain', False)
    due_pending = bool(boundary_due or carried_due)
    state['checkpoint_due_after_readonly_chain'] = due_pending
    readonly_chain = (checkpoint_step_is_readonly(pending.get('selected_step'))
                      and not checkpoint_cycle_may_change_game(pending, after))
    due = bool(due_pending and not state['terminal'] and not readonly_chain)
    reason = ('scheduled_dirty_checkpoint' if due else
              'dirty_checkpoint_due_deferred_readonly_chain' if due_pending and readonly_chain else
              'unchanged_readonly_evidence_chain' if not dirty else
              'stable_player_siege_checkpoint_deferred_to_cycle_10' if routine else
              'ordinary_checkpoint_not_due')
    state['checkpoint_last_decision'] = {'reason': reason, 'interval_settled_cycles': interval,
                                         'dirty': bool(dirty), 'due': due}
    return due
