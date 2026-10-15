"""Pure next-step adapter over the existing R10 B evidence consumer.

No SDK calls, time advance, command dispatch, file writes or cause attribution.
Callers must obtain a new decision after every attempted command; native IsValid
remains authoritative even when a literal is advertised in a fresh scope.
"""
from __future__ import annotations

from copy import deepcopy

import r10_compare as c
import strategy_b as b
from xar_autoplayer.bridge.army_split_merge_observation_12004 import (
    compare_split_merge_cohorts,
    identify_split_sibling,
    read_bound_current_commander,
)
from xar_autoplayer.bridge.war_contract import (
    merge_armies_step,
    preview_move_army_step,
    split_army_half_step,
)


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _view(ep, plan, evidence, runtime):
    c.schema_check(ep, 'endpoint')
    view = b.observe(ep, plan, evidence, runtime)
    query = c.body(evidence.json(ep['army_result']))
    scope = query.get('army_strengths_query_scope')
    _need(isinstance(scope, dict) and scope.get('published_scope_status') == 'available'
          and set(scope.get('army_ids', [])) == set(view['rows']),
          'complete actual Army query scope is required')
    for row in view['rows'].values():
        resolution = row['native_army_resolution_v1']
        _need(resolution.get('branch') == 'resolved'
              and resolution.get('raw_reference') == resolution.get('entry_full_id') == row['native_carmy_id'],
              'full CArmy generation is not resolved from the actual raw reference')
        index, capacity = resolution.get('reference_index'), resolution.get('storage_capacity')
        _need(c.integer(index) and c.integer(capacity) and 0 <= index < capacity,
              'native CArmy storage/index witness is unavailable')
        strengths = row['regiment_strengths']
        groups = row['regiment_replenishment_records_v1']
        _need([r['army_regiment_id'] for r in strengths] == [g['army_regiment_id'] for g in groups],
              'DATA group order differs from the observed native ArRg order')
        for group in groups:
            _need([r['record_index'] for r in group['records']] == list(range(group['native_data_record_count'])),
                  'DATA record order/index is incomplete; never sort it into apparent validity')
    return view


def _scope_steps(scope, current, evidence, runtime):
    _need(isinstance(scope, dict), 'fresh bracketed ck3_get_capabilities scope is required')
    _need(scope['before_snapshot']['path'] != scope['after_snapshot']['path'],
          'capabilities need two independently saved bracket snapshots')
    before = c.frame(evidence.json(scope['before_snapshot']), runtime)
    after = c.frame(evidence.json(scope['after_snapshot']), runtime)
    actual = current['snapshot']
    # The capabilities DTO has no queried frame. Preserve original packets and
    # require a stable independent snapshot on each side instead of adding one.
    fields = ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id',
              'played_character', 'player_armies', 'active_event', 'pending_character_interaction')
    for field in fields:
        _need(field in actual and before.get(field) == after.get(field) == actual[field],
              'capabilities bracket/current frame differs: ' + field)
    capabilities = c.body(evidence.json(scope['capabilities']))
    d = capabilities.get('diagnostics') or {}
    _need(capabilities.get('backend_id') == 'native-headless' and capabilities.get('snapshot') is True
          and d.get('connected') is True and d.get('bridge_pid') == runtime['pid']
          and d.get('connection_generation') == runtime['connection_generation'],
          'capabilities backend/process/generation is not the current native scope')
    hello = d.get('hello') or {}
    _need(hello.get('expected_ck3_version') == '1.20.0.4'
          and str(hello.get('expected_ck3_sha256', '')).lower() == c.EXE,
          'capabilities exact build differs')
    steps = capabilities.get('action_steps')
    _need(isinstance(steps, list) and all(isinstance(s, str) for s in steps),
          'actual action_steps collection is missing')
    return set(steps)


def _last_endpoint(arm, trace):
    if not trace['events']:
        return arm['cold_start']
    event = trace['events'][-1]
    return event.get('endpoint') or event.get('after') or event['before']


def _at(view, aid, target):
    p = view['positions'][aid]
    return (p['current_province_id'] == target and p.get('army_state') == 'regular'
            and p.get('route_read_status') == 'complete_empty'
            and p.get('route_province_ids') == [] and p.get('move_target_province_id') is None)


def _movement_dependency(view, aid, target, role):
    p = view['positions'][aid]
    if p.get('move_target_province_id') == target and p.get('route_read_status') == 'complete_nonempty':
        return {'status': 'await_actual_arrival', 'army_id': aid, 'target_province_id': target, 'role': role}
    return {'status': 'need_fresh_route_preview', 'army_id': aid, 'target_province_id': target,
            'role': role, 'required_preview_step': preview_move_army_step(aid, target),
            'move_command': None}


def next_decision(plan, arm, trace, current_endpoint, evidence, *, plan_sha256,
                  capability_scope=None, commander_queries=None):
    """Return one candidate command, bookkeeping event, or precise dependency.

    All endpoint/arm/trace/pin shapes are the existing B/R10 inputs. Optional
    capability_scope contains three pins: before_snapshot, capabilities,
    after_snapshot. commander_queries maps current public Army IDs to typed
    commander-query pins. No separately persisted policy state is introduced.
    """
    out = {'schema': 'xar.e04.r10.strategy-b-next.v1', 'command': None,
           'bookkeeping_event': None, 'dependencies': [], 'native_validation_pending': False,
           'actual_physical_refill': None, 'birth_producer_observed': False,
           'live_execution_performed': False, 'research_card_closed': False,
           'R10_comparison_qualified': False}
    try:
        audit = b.audit(plan, arm, trace, evidence, plan_sha256=plan_sha256)
        out['verified_phase'] = audit['state']
        if audit['stop'] is not None:
            out.update(status='diagnose_without_resubmitting', previous_attempt=deepcopy(audit['stop']))
            return out
        rt = arm['runtime']
        current = _view(current_endpoint, plan, evidence, rt)
        previous = _view(_last_endpoint(arm, trace), plan, evidence, rt)
        b._passive_observation(previous, current)
        cold = _view(arm['cold_start'], plan, evidence, rt)
        main = next(iter(cold['rows']))
        child = None
        rests, exits = {}, {}
        for event in trace['events']:
            if event['kind'] == 'split':
                before = _view(event['before'], plan, evidence, rt)
                after = _view(event['after'], plan, evidence, rt)
                split = identify_split_sibling(before['snapshot'], after['snapshot'], source_army_id=main,
                    pre_strengths=c.body(evidence.json(event['before']['army_result'])),
                    post_strengths=c.body(evidence.json(event['after']['army_result'])))
                child = split['sibling_army_id']
                out['actual_split_identity'] = split
            elif event['kind'] == 'rest-enter':
                rests[event['unit_id']] = event['endpoint']['day']
            elif event['kind'] == 'rest-exit':
                exits[event['unit_id']] = event['reason']
        out['quantities'] = compare_split_merge_cohorts(list(cold['rows'].values()), list(current['rows'].values()))
        out['per_army_supply'] = deepcopy(current['endpoint']['units'])
        out['actual_native_ids'] = dict(current['native'])
        if current_endpoint['day'] == 90:
            out['status'] = 'absolute_horizon_observed_use_comparison_consumer'
            return out
        frame = current['snapshot']
        _need('active_event' in frame and 'pending_character_interaction' in frame,
              'actual current event/interaction state is missing')
        if frame['active_event'] is not None or frame['pending_character_interaction'] is not None:
            out['status'] = 'handle_actual_event_then_reobserve'
            return out
        for aid, p in current['positions'].items():
            if aid not in current['rows']:
                continue
            _need(p.get('controllable') is True and p.get('in_combat') is False
                  and p.get('retreating') is False, 'actual strategy Army is uncontrolled/in combat/retreating')
        assigned = {}
        commander_queries = commander_queries or {}
        for aid, native in current['native'].items():
            pin = commander_queries.get(aid)
            if pin is None:
                out['dependencies'].append({'status': 'need_typed_current_commander', 'tool': 'ck3_query_army_commander_candidates_v1',
                    'arguments': {'army_id': aid, 'expected_revision': frame['revision']}})
            else:
                assigned[aid] = read_bound_current_commander(c.body(evidence.json(pin)), frame,
                                                            army_id=aid, native_carmy_id=native)
        out['assigned_commanders'] = assigned
        if out['dependencies']:
            out['status'] = 'needs_actual_observation'
            return out
        bp = plan['strategies']['B']
        candidate = None
        if audit['state'] == 'whole':
            _need(current['endpoint'] == cold['endpoint'], 'fresh whole state drifted from frozen T0 before split')
            b._stationary(current, [main], current['positions'][main]['current_province_id'])
            candidate = split_army_half_step(main)
        elif audit['state'] == 'split':
            _need(child is not None and set(current['rows']) == {main, child}, 'actual split pair is incomplete')
            roles = list(zip((main, child), bp['rest_province_ids']))
            # Record every actual entry before waiting for one army's recovery.
            # Otherwise a stationary child's rest clock would start artificially
            # late merely because main was inspected first.
            for aid, site in roles:
                if aid not in rests and _at(current, aid, site):
                    out.update(status='record_actual_rest_entry', bookkeeping_event={
                        'kind': 'rest-enter', 'endpoint': deepcopy(current_endpoint),
                        'unit_id': aid, 'province_id': site})
                    return out
            absent_entries = [(aid, site) for aid, site in roles if aid not in rests]
            if absent_entries:
                out['status'] = 'movement_dependency'
                out['dependencies'] = [_movement_dependency(current, aid, site, 'rest') for aid, site in absent_entries]
                return out
            waiting = []
            for aid, site in roles:
                if aid not in exits:
                    _need(_at(current, aid, site), 'unexited rest Army left its frozen site')
                    elapsed = current_endpoint['day'] - rests[aid]
                    _need(0 <= elapsed <= bp['maximum_rest_days'], 'actual rest exceeded frozen maximum')
                    row = current['rows'][aid]
                    threshold = (row['current_supply_raw'] >= bp['minimum_stock_raw'] and
                                 row['maximum_soldiers'] - row['current_soldiers'] <= bp['maximum_deficit'])
                    reason = 'threshold' if threshold else 'maximum_rest_days' if elapsed == bp['maximum_rest_days'] else None
                    if reason:
                        out.update(status='record_actual_rest_exit', bookkeeping_event={
                            'kind': 'rest-exit', 'endpoint': deepcopy(current_endpoint), 'unit_id': aid,
                            'province_id': site, 'reason': reason})
                        return out
                    else:
                        waiting.append({'army_id': aid, 'days_until_maximum': bp['maximum_rest_days'] - elapsed})
            for aid, site in roles:
                if aid not in exits:
                    continue
                if not _at(current, aid, bp['merge_province_id']):
                    out['status'] = 'movement_dependency'
                    out['dependencies'].append(_movement_dependency(current, aid, bp['merge_province_id'], 'meeting'))
                    return out
            if waiting:
                out.update(status='await_rest_daily_observation', waiting_armies=waiting)
                return out
            b._stationary(current, [main, child], bp['merge_province_id'])
            destination, source = ((main, child) if bp['merge_destination_policy'] == 'destination-main' else (child, main))
            candidate = merge_armies_step(destination, source)
        else:
            # A merged trace may end in a later move. Use its surviving actual
            # scope rather than relying on the last event's type or an old ID.
            _need(len(current['rows']) == 1, 'merged actual strategy scope is incomplete')
            destination = next(iter(current['rows']))
            if _at(current, destination, plan['goal_province_id']):
                out['status'] = 'actual_goal_state_use_daily_first_arrival_consumer'
            else:
                out['status'] = 'movement_dependency'
                out['dependencies'].append(_movement_dependency(current, destination, plan['goal_province_id'], 'goal'))
            return out
        steps = _scope_steps(capability_scope, current, evidence, rt)
        if candidate not in steps:
            out.update(status='not_in_actual_advertised_scope', required_step=candidate)
            return out
        attempted = [e for e in trace['events'] if 'request' in e
                     and evidence.json(e['request']).get('arguments', {}).get('step') == candidate]
        _need(not attempted, 'candidate was already attempted; never resend it')
        out.update(status='candidate_requires_native_validation', native_validation_pending=True,
                   command={'tool': 'ck3_execute_step', 'arguments': {
                       'step': candidate, 'expected_revision': frame['revision']}})
    except (ValueError, KeyError, TypeError, OSError) as error:
        out.update(status='blocked_missing_or_inconsistent_input', reason=str(error), command=None,
                   native_validation_pending=False)
    return out
