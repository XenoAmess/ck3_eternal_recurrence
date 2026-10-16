"""Small read-only C adapter: fresh via choice, DATA coverage and next proposal.

No SDK/API registrations or commands are executed. A native preview remains
conditional; the existing typed Move validator and independent applied route
are mandatory. Frozen whole-via targets are never replaced by candidate choice.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

_policy_spec = importlib.util.spec_from_file_location(
    '_e04_c_existing_policy', Path(__file__).resolve().with_name('strategy_c.py'))
c = importlib.util.module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(c)


def _reader():
    path = Path(__file__).resolve().parent.parent / 'comparison/r10_compare.py'
    spec = importlib.util.spec_from_file_location('_e04_c_next_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_inputs(plan, runtime, endpoint_record, evidence):
    """Consume the existing complete paired R10 snapshot/Driver files once.

    This leaves actual movement fields and every stored DATA record unchanged.
    The caller must have qualified normal cold-T0/runtime and evidence custody.
    """
    observation = c.read_observation(plan, runtime, endpoint_record, evidence)
    reader = _reader()
    query = reader.body(evidence.json(endpoint_record['army_result']))
    army_id = observation['endpoint']['units'][0]['army_id']
    row = next(a for a in query['army_strengths'] if a['army_id'] == army_id)
    observation['decision_inputs'] = {
        'all_regiment_ids': [r['army_regiment_id'] for r in row['regiment_strengths']],
        'current_movement_progress': deepcopy(row.get('current_movement_progress')),
        'source_pins': {'snapshot': deepcopy(endpoint_record['snapshot']),
                        'army_result': deepcopy(endpoint_record['army_result'])}}
    return observation


def _whole_data(plan, observation):
    """Check every stored DATA row, including extras, without summing aliases.

    Full Driver normalization is upstream. This gate additionally refuses
    'available' containers whose individual records are unavailable, reordered
    or missing. Zero records is accepted only as an explicit native count0.
    Physical current is never replaced with effective/prepared values.
    """
    ep, unit, binding = c._valid_observation(plan, observation)
    inputs = observation.get('decision_inputs')
    c.need(isinstance(inputs, dict), 'decision inputs are missing; re-read full scoped Army')
    ids = inputs.get('all_regiment_ids')
    c.need(isinstance(ids, list) and ids and all(c.integer(x) and x >= 0 for x in ids)
           and len(set(ids)) == len(ids), 'complete all-regiment identity vector missing')
    c.need(set(plan['original_regiment_ids']) <= set(ids), 'original cohort missing from current whole Army')
    rows = ep.get('DATA')
    c.need(isinstance(rows, list) and len(rows) == len(ids)
           and {r.get('army_regiment_id') for r in rows} == set(ids), 'whole Army DATA rows missing or duplicated')
    count = 0
    for row in rows:
        c.need(row.get('source') == 'native_all_data_records' and row.get('status') == 'available'
               and row.get('ready') is True and row.get('unavailable_reason') is None,
               'whole Army DATA container is partial/unavailable')
        records = row.get('records')
        native_count = row.get('native_data_record_count')
        c.need(c.integer(native_count) and native_count >= 0 and isinstance(records, list)
               and len(records) == native_count, 'whole Army stored DATA count differs')
        for index, record in enumerate(records):
            c.need(record.get('status') == 'available' and record.get('unavailable_reason') is None,
                   'whole Army DATA contains an unavailable record')
            c.need(record.get('record_index') == index
                   and c.integer(record.get('record_index')),
                   'stored DATA ordinal/order is incomplete')
            c.need(c.integer(record.get('persistent_regiment_id'))
                   and -(2**31) <= record['persistent_regiment_id'] < 2**31
                   and c.integer(record.get('chunk_index')) and 0 <= record['chunk_index'] < 7,
                   'stored DATA persistent/chunk identity missing')
            c.need(all(c.integer(record.get(k)) for k in ('current_soldiers', 'maximum_soldiers'))
                   and 0 <= record['current_soldiers'] <= record['maximum_soldiers'],
                   'stored DATA physical current/max missing')
            if record.get('chunk_army_regiment_id') is not None:
                c.need(record['chunk_army_regiment_id'] == row['army_regiment_id'],
                       'stored DATA chunk points to another actual regiment')
        count += native_count
    return ep, unit, binding, {'regiment_count': len(ids), 'stored_DATA_count': count,
                              'record_aliases_not_summed': True}


def _base(status, reason, observation):
    ep = observation.get('endpoint') or {}
    return {'schema': 'xar.e04.strategy-c.next-decision.v1', 'status': status,
            'reason': reason, 'observed_day': ep.get('day'), 'observed_date_raw': ep.get('date_raw'),
            'source_frame': deepcopy(observation.get('binding')),
            'source_pins': deepcopy((observation.get('decision_inputs') or {}).get('source_pins')),
            'proposed_call': None, 'next_state': None, 'live_execution_performed': False,
            'research_card_closed': False, 'winner': None, 'exact_arrival_tick': None}


def _query_call(observation):
    binding = observation['binding']
    return {'tool': 'ck3_query_army_strengths', 'arguments': {
        'army_ids': [observation['endpoint']['units'][0]['army_id']],
        'expected_revision': binding['revision'], 'profile': 'ordinary_core_v1'}}


def _preview_call(observation, target):
    return {'tool': 'ck3_execute_step', 'arguments': {
        'step': f"preview-move-army-{observation['endpoint']['units'][0]['army_id']}-to-{target}",
        'expected_revision': observation['binding']['revision']}}


def _fresh_route(observation, target, value):
    c.need(isinstance(value, dict) and value.get('accepted') is True,
           'native preview rejected/deferred/missing')
    p = value.get('route_preview') or {}
    ep, binding = observation['endpoint'], observation['binding']
    unit = ep['units'][0]
    for key, expected in [('queried_snapshot_id', binding['snapshot_id']),
                          ('queried_revision', binding['revision']),
                          ('queried_native_revision', binding['native_revision']),
                          ('queried_connection_generation', binding['connection_generation']),
                          ('queried_episode_run_id', binding['episode'])]:
        c.need(value.get(key) == expected, 'stale/foreign native preview: ' + key)
    c.need(p.get('status') == 'available' and p.get('army_id') == unit['army_id']
           and p.get('origin_province_id') == unit['current_province_id']
           and p.get('target_province_id') == target and p.get('previewed_date_raw') == ep['date_raw'],
           'native preview Army/origin/target/date differs')
    route = deepcopy(p.get('route_province_ids'))
    c.need(isinstance(route, list) and route and all(c.integer(x) and x > 0 for x in route),
           'native preview complete route missing')
    if route[0] == unit['current_province_id']:
        route = route[1:]
    c.need(route and route[-1] == target, 'native preview does not reach desired target')
    return route


def _lock(observation):
    unit = observation['endpoint']['units'][0]
    if not unit['route']:
        return {'state': 'no_current_edge', 'front': None, 'locked': None}
    result = {'state': 'unknown', 'front': unit['route'][0], 'locked': None}
    movement = (observation.get('decision_inputs') or {}).get('current_movement_progress')
    if not isinstance(movement, dict) or movement.get('source') != 'native_current_route_edge':
        return result
    values = []
    for field in ('normalized_edge_progress', 'loaded_movement_lock_cutoff'):
        value = movement.get(field)
        if not (isinstance(value, dict) and set(value) == {'raw', 'scale'}
                and c.integer(value['raw']) and -(2**63) <= value['raw'] < 2**63
                and type(value['scale']) is int and value['scale'] == 100000):
            return result
        values.append(value['raw'])
    progress, cutoff = values
    return {'state': 'locked' if progress > cutoff else 'not_above_cutoff',
            'front': unit['route'][0], 'locked': progress > cutoff,
            'progress_raw': progress, 'loaded_cutoff_raw': cutoff, 'scale': 100000}


def route_change_advice(plan, observation, desired_target, preview=None):
    """Read-only advisory; locked first edge never implies all reroutes illegal.

    No reroute is submitted, even when a preview retains the front. A frozen C
    executor uses only its existing stationary propose_move/observed route flow.
    """
    try:
        _, unit, _, coverage = _whole_data(plan, observation)
        c.need(c.integer(desired_target) and desired_target > 0, 'desired target is unknown')
    except (ValueError, KeyError, TypeError) as error:
        return _base('hold_unknown', str(error), observation)
    lock = _lock(observation)
    out = _base('needs_fresh_preview', 'actual native preview required before any route change', observation)
    out.update(edge_lock=lock, coverage=coverage, immediate_edge_cancellation_legal=None,
               native_preview_route=None, suffix_route_change_ready=None)
    if lock['locked'] is True:
        out.update(status='hold_locked_front', immediate_edge_cancellation_legal=False,
                   reason='current first edge is retained; suffix legality still requires native preview')
    elif unit['route'] and lock['locked'] is None:
        out.update(status='hold_unknown', reason='actual edge progress/cutoff missing; do not guess lock state')
    if preview is None:
        out['proposed_read_only_call'] = (_query_call(observation) if lock['state'] == 'unknown'
                                          else _preview_call(observation, desired_target))
        return out
    try:
        route = _fresh_route(observation, desired_target, preview)
    except (ValueError, KeyError, TypeError) as error:
        out.update(reason=str(error), native_preview_rejected_or_unknown=True)
        return out
    out['native_preview_route'] = route
    if lock['locked'] is None and unit['route']:
        return out
    if lock['locked'] is True and route[0] != lock['front']:
        out.update(reason='preview does not preserve known locked front; retain unknown and re-read',
                   suffix_route_change_ready=None)
        return out
    out.update(status='native_preview_available', suffix_route_change_ready=True,
               reason='fresh native preview is available; final validator and independent applied route remain required')
    return out


def choose_draft_via(plan, observation, ordered_candidate_ids, previews):
    """Choose first fresh available candidate in a caller-declared draft order.

    Candidate IDs are supplied by the caller, never guessed or enumerated here.
    This does not forecast the onward via-to-goal leg or update/freeze the plan.
    """
    try:
        c.need(plan.get('status') != 'frozen', 'frozen C may not replace its waypoint policy')
        _, unit, _, coverage = _whole_data(plan, observation)
        c.need(isinstance(ordered_candidate_ids, list) and ordered_candidate_ids
               and all(c.integer(x) and x > 0 for x in ordered_candidate_ids)
               and len(set(ordered_candidate_ids)) == len(ordered_candidate_ids),
               'declare a nonempty unique candidate order')
        c.need(all(x not in (unit['current_province_id'], plan['goal_province_id']) for x in ordered_candidate_ids),
               'via candidate equals current Province or final goal')
    except (ValueError, KeyError, TypeError) as error:
        return _base('hold_unknown', str(error), observation)
    out = _base('no_fresh_available_candidate', 'no candidate has a qualifying current preview', observation)
    out.update(candidate_order=deepcopy(ordered_candidate_ids), selected_waypoint=None,
               candidate_diagnostics=[], coverage=coverage, onward_leg_qualified=False,
               selection_criterion='first_fresh_available_in_declared_order')
    for target in ordered_candidate_ids:
        advice = route_change_advice(plan, observation, target, previews.get(target))
        out['candidate_diagnostics'].append({'province_id': target, 'status': advice['status'],
                                            'reason': advice['reason']})
        if advice['status'] == 'native_preview_available':
            out.update(status='draft_via_selected', selected_waypoint=target,
                       native_first_leg_route=advice['native_preview_route'],
                       reason='selected only from fresh currently available native previews; freeze before formal C')
            break
    return out


def next_decision(plan, state, observation, preview=None):
    """Produce the next existing call/hold from a current frozen C state.

    This never calls observe automatically or invents an arrival. Newly arrived
    evidence must pass existing c.observe first, preserving its native interval.
    """
    try:
        c.need(plan.get('status') == 'frozen', 'formal C plan is not frozen')
        ep, unit, binding, coverage = _whole_data(plan, observation)
        c._same_subject(state, ep, unit, binding)
        destinations = c.targets(plan)
    except (ValueError, KeyError, TypeError) as error:
        return _base('hold_unknown', str(error), observation)
    out = _base('hold_unknown', 'current state needs classification', observation)
    out['coverage'] = coverage
    out['actual_arrival_intervals'] = deepcopy(state['arrivals'])
    if state['phase'] in ('arrived', 'budget-censored', 'stopped'):
        out.update(status='terminal', reason=state.get('reason') or state['phase'])
        return out
    if ep['day'] != state['last_day'] or binding['snapshot_id'] != state['binding']['snapshot_id']:
        out.update(status='needs_existing_observe', reason='pass this new independent frame through c.observe first')
        return out
    if state['phase'] == 'pending_move':
        out.update(reason='Move result remains unknown; preserve pending state and do not resubmit',
                   proposed_read_only_call=_query_call(observation))
        return out
    target = destinations[state['target_index']]
    out['frozen_next_target'] = target
    if state['phase'] == 'marching':
        if (unit['state'] == 'moving' and unit['route'] and unit['route'][-1] == target
                and unit['target'] == target
                and any(unit['route'] == state['pending_route'][i:] for i in range(len(state['pending_route'])))):
            if ep['day'] >= 90:
                out.update(status='needs_existing_observe', reason='original day90 must be classified by c.observe')
            else:
                out.update(status='continue_exact_day', reason='existing frozen route is still observed',
                    proposed_call={'tool': 'ck3_execute_step', 'arguments': {
                        'step': f"research-arm-tactical-daily-sentinel-v1-{ep['date_raw']}-to-{ep['date_raw'] + 24}-speed-5-mode-terminal-a-0",
                        'expected_revision': binding['revision']}})
            return out
        advice = route_change_advice(plan, observation, target, preview)
        out.update(status=advice['status'], reason=advice['reason'], route_change_advisory=advice)
        return out
    if preview is None:
        out.update(status='needs_fresh_preview', reason='read native preview for the frozen next target',
                   proposed_read_only_call=_preview_call(observation, target))
        return out
    try:
        new_state, call = c.propose_move(plan, state, observation, preview)
    except (ValueError, KeyError, TypeError) as error:
        out.update(reason=str(error))
        return out
    out.update(status='propose_existing_move', reason='persist pending state before one typed Move submission',
               next_state=new_state, proposed_call={'tool': call['tool'], 'arguments': {
                   'army_id': call['army_id'], 'target_province_id': call['target_province_id'],
                   'expected_revision': call['expected_revision']}})
    return out


def _captured_target_now(observation, preview, target):
    """Retain already normalized current .4 target operands, never landfall."""
    supplied = (preview.get('route_preview') or {}).get('province_supply')
    if supplied is None:
        return {'target_inputs': None, 'reason': 'native_target_province_supply_absent'}
    unit = observation['endpoint']['units'][0]
    binding = observation['binding']
    owner = observation['endpoint']['player_character_id']
    row = supplied.get('target') if isinstance(supplied, dict) else None
    c.need(isinstance(row, dict) and row.get('role') == 'target' and row.get('province_id') == target,
           'captured target Province/role differs')
    c.need(supplied.get('army_id') == unit['army_id']
           and supplied.get('native_carmy_id') == binding['native_carmy_id']
           and supplied.get('owner_character_id') == owner,
           'captured target context belongs to another Army/CArmy/owner')
    family = row.get('captured_target_land_supply_inputs_v1')
    if family is not None:
        c.need(isinstance(family, dict)
               and family.get('source') == 'native_captured_target_land_supply_inputs'
               and family.get('input_basis') == 'captured_owner_and_target_province'
               and type(family.get('scale')) is int and family['scale'] == 100000,
               'captured target input source/basis/scale differs')
        for key, expected in [('subject_army_id', unit['army_id']),
                              ('subject_carmy_id', binding['native_carmy_id']),
                              ('owner_character_id', owner), ('province_id', target)]:
            c.need(family.get(key) is None or (type(family[key]) is int and family[key] == expected),
                   'captured target numerical subject differs: ' + key)
    return {'target_inputs': deepcopy(row), 'reason': deepcopy(row.get('unavailable_reason')),
            'input_basis': 'current_captured_target_only', 'future_usage_after_arrival': None,
            'future_monthly_supply_rate': None, 'future_stock': None,
            'positive_supply_recovery_guaranteed': False}


def compare_via_first_leg(plan, observation, via_province_id, direct_preview=None, via_preview=None):
    """Explain whether a fresh via leg differs from the current direct preview.

    This neither selects a shortest route nor changes a frozen C policy. A stop
    on the direct prefix is distinguished from a native first-leg divergence.
    The onward leg must be queried only after an actual stationary via arrival.
    """
    out = _base('needs_current_previews', 'no current direct/via route pair has been supplied', observation)
    out.update(route_relation=None, missing_read_only_calls=[], frozen_policy_changed=False,
               first_leg_geometric_difference=None, shortest_total_route_established=False,
               total_travel_days=None, onward_route=None, onward_target_inputs=None,
               onward_preview_required_after_actual_via_arrival=True)
    try:
        _, unit, _, coverage = _whole_data(plan, observation)
        goal = plan.get('goal_province_id')
        c.need(type(goal) is int and goal > 0, 'freeze an explicit common goal; war objective is not an implicit goal')
        c.need(type(via_province_id) is int and via_province_id > 0
               and via_province_id not in (unit['current_province_id'], goal),
               'declare a distinct via candidate from current actual scope; never borrow an old Army target')
        out['coverage'] = coverage
        for value, target in ((direct_preview, goal), (via_preview, via_province_id)):
            if value is None:
                out['missing_read_only_calls'].append(_preview_call(observation, target))
        if out['missing_read_only_calls']:
            return out
        direct = _fresh_route(observation, goal, direct_preview)
        via = _fresh_route(observation, via_province_id, via_preview)
        out.update(direct_preview_route=direct, via_first_leg_preview_route=via,
                   direct_target_now=_captured_target_now(observation, direct_preview, goal),
                   via_target_now=_captured_target_now(observation, via_preview, via_province_id))
        if via_province_id in direct and via == direct[:direct.index(via_province_id)+1]:
            relation = 'intermediate_stop_on_direct_prefix'
            out.update(first_leg_geometric_difference=False,
                       reason='via is an explicit stop on the same current direct prefix; detour not established')
        elif goal in via[:-1]:
            relation = 'goal_passed_before_via'
            out.update(first_leg_geometric_difference=True,
                       reason='via preview passes the common goal before its stop; retain this design conflict before freeze')
        else:
            relation = 'current_first_leg_diverges'
            out.update(first_leg_geometric_difference=True,
                       reason='fresh current first leg differs; onward reachability/time/supply remain conditional')
        out.update(status='current_route_pair_observed', route_relation=relation,
                   preview_hop_counts={'direct':len(direct),'via_first_leg':len(via)},
                   hop_counts_are_travel_time_or_distance=False,
                   requery_after_arrival=['fresh paused current Army/CArmy and complete whole DATA',
                       'same-frame typed commander and actual current stock/cap/rate',
                       'fresh native preview from actual via to frozen next target',
                       'retain current target contributor/resupply inputs; do not add Army soldiers to target usage'])
        return out
    except (ValueError, KeyError, TypeError) as error:
        out.update(status='hold_unknown', reason=str(error))
        return out
