"""Read-only whole-via C policy; no SDK, process, save, media or command access.

Supply and physical cohort counts are observations, never waiting criteria.
Use a frozen R10 plan and qualified paired endpoints from r10_compare.endpoint.
This pure consumer does not certify supplied evidence authenticity or execute Move.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path


def read_observation(plan, runtime, endpoint_record, evidence):
    """Join existing pinned R10 files; no external absolute module imports.

    `evidence` is the existing r10_compare.Evidence rooted at a caller-supplied
    small package. Run shared check_plan/cold comparison first. No save or media
    is opened by this adapter.
    """
    path = Path(__file__).resolve().parent.parent / 'comparison' / 'r10_compare.py'
    spec = importlib.util.spec_from_file_location('_e04_c_r10_reader', path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    ep = reader.endpoint(endpoint_record, plan, evidence, runtime)
    snapshot = reader.frame(evidence.json(endpoint_record['snapshot']), runtime)
    query = reader.body(evidence.json(endpoint_record['army_result']))
    need(len(ep['units']) == 1, 'C requires one whole strategy Army')
    army_id = ep['units'][0]['army_id']
    row = next(x for x in query['army_strengths'] if x['army_id'] == army_id)
    position = next(x for x in snapshot['player_armies'] if x['army_id'] == army_id)
    diagnostics = snapshot['diagnostics']
    return {'endpoint': ep, 'binding': {
        'machine_id': runtime['machine_id'], 'pid': diagnostics['bridge_pid'],
        'process_create_time_100ns': runtime['process_create_time_100ns'],
        'connection_generation': diagnostics['connection_generation'],
        'episode': snapshot['episode_run_id'], 'snapshot_id': snapshot['snapshot_id'],
        'revision': snapshot['revision'], 'native_revision': snapshot['native_revision'],
        'native_carmy_id': row.get('native_carmy_id'), 'paused': snapshot['paused'],
        'controllable': position.get('controllable'), 'in_combat': position.get('in_combat'),
        'retreating': position.get('retreating'),
        'move_target_observable': position.get('move_target_observable')}}


def need(value, message):
    if not value:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def targets(plan):
    policy = plan['strategies']['C']
    need(policy['mode'] == 'whole-via', 'C must retain frozen whole-via policy')
    # An independent waiting policy cannot be smuggled into the existing C arm.
    need(set(policy) == {'mode', 'waypoint_province_ids', 'route_preview'},
         'C contract contains unregistered policy fields')
    way = policy['waypoint_province_ids']
    goal = plan['goal_province_id']
    need(isinstance(way, list) and way, 'freeze at least one alternate waypoint')
    need(all(integer(x) and x > 0 for x in way + [goal]), 'invalid target ID')
    need(len(set(way + [goal])) == len(way) + 1, 'duplicate waypoint/final goal')
    need(plan['max_natural_days'] == 90 and plan['raw_per_day'] == 24,
         'C shares the absolute T0 plus 90-day budget')
    need(integer(plan['t0_raw']), 'missing absolute T0')
    return way + [goal]


def _valid_observation(plan, obs):
    """Validate a qualified R10 endpoint plus the joined native identity/frame.

    Caller must first invoke r10_compare.endpoint with exact pinned files and
    the arm runtime. `binding` is extracted from that same paused snapshot and
    complete Driver row, not inferred from a UI, camera or another process.
    """
    ep = obs['endpoint']
    day = ep['day']
    need(integer(day) and 0 <= day <= 90 and ep['date_raw'] == plan['t0_raw'] + day * 24,
         'endpoint is outside the original absolute natural-day scope')
    need(len(ep['units']) == 1, 'whole-via C must retain one whole strategy Army')
    unit = ep['units'][0]
    binding = obs['binding']
    for key in ('machine_id', 'episode', 'snapshot_id'):
        need(isinstance(binding.get(key), str) and binding[key], 'missing binding: ' + key)
    for key in ('pid', 'process_create_time_100ns', 'connection_generation',
                'revision', 'native_revision', 'native_carmy_id'):
        need(integer(binding.get(key)) and binding[key] >= 0, 'missing integer binding: ' + key)
    need(binding.get('paused') is True and binding.get('controllable') is True,
         'C needs an actual paused controllable Army')
    need(binding.get('in_combat') is False and binding.get('retreating') is False,
         'combat/retreat is a competing event, not normal march completion')
    observable = binding.get('move_target_observable')
    need(type(observable) is bool and observable == bool(unit['route']),
         'target observability must retain the native complete-route contract')
    if not observable:
        need(unit['target'] is None, 'empty-route null must not become an invented target')
    else:
        need(unit['target'] == unit['route'][-1], 'native target differs from complete route tail')
    need(unit['scale'] == 100000 and integer(unit['stock_raw'])
         and integer(unit['capacity_raw']) and 0 <= unit['stock_raw'] <= unit['capacity_raw'],
         'unknown/malformed supply is not zero')
    rows = ep['cohort_regiments']
    ids = [r['army_regiment_id'] for r in rows]
    need(set(ids) == set(plan['original_regiment_ids']) and len(set(ids)) == len(ids),
         'original physical cohort missing or duplicated')
    need(all(integer(r['current_soldiers']) and integer(r['maximum_soldiers'])
             and 0 <= r['current_soldiers'] <= r['maximum_soldiers'] for r in rows),
         'physical scale1 integers required; effective/prepared values cannot substitute')
    need(ep['cohort_current'] == sum(r['current_soldiers'] for r in rows)
         and ep['cohort_maximum'] == sum(r['maximum_soldiers'] for r in rows),
         'original cohort totals disagree')
    need(ep['all_strategy_current'] == unit['current_soldiers']
         and ep['all_strategy_maximum'] == unit['maximum_soldiers']
         and ep['all_strategy_current'] >= ep['cohort_current']
         and ep['all_strategy_maximum'] >= ep['cohort_maximum'],
         'all-strategy and original-cohort quantities cannot substitute for each other')
    need(isinstance(unit['route'], list) and all(integer(x) and x > 0 for x in unit['route']),
         'route must be the complete native route')
    need(integer(unit['current_province_id']) and unit['current_province_id'] > 0,
         'actual current Province missing')
    return ep, unit, binding


def _stationary_at(unit, target, arrival_states):
    return (unit['current_province_id'] == target and unit['state'] in arrival_states
            and unit['route'] == [] and unit['target'] is None)


def start(plan, observation):
    """Initialize after shared plan/cold-T0 qualification; emits no action."""
    destinations = targets(plan)
    ep, unit, binding = _valid_observation(plan, observation)
    need(ep['day'] == 0, 'start only at the qualified common T0; no clock reset')
    need(unit['state'] in plan['arrival_states'] and unit['route'] == []
         and unit['target'] is None, 'initial C must be stationary before its first Move')
    need(unit['current_province_id'] not in destinations, 'T0 is already a frozen C target')
    return {'phase': 'ready', 'target_index': 0, 'last_day': 0,
            'last_clock_generation': 0, 'binding': deepcopy(binding),
            'army_id': unit['army_id'], 'commander_id': ep['commander_id'],
            'cohort_maxima': sorted([[r['army_regiment_id'], r['maximum_soldiers']] for r in ep['cohort_regiments']]),
            'last_not_arrived_day': 0, 'arrivals': [], 'pending_route': None,
            'pending_origin': None, 'pending_target': None,
            'ready_province': unit['current_province_id'], 'reason': None}


def _same_subject(state, ep, unit, binding):
    for key in ('machine_id', 'pid', 'process_create_time_100ns',
                'connection_generation', 'episode', 'native_carmy_id'):
        need(binding[key] == state['binding'][key], 'C runtime/subject changed: ' + key)
    need(unit['army_id'] == state['army_id'], 'public Army generation changed')
    need(ep['commander_id'] == state['commander_id'], 'frozen commander changed')
    need(sorted([[r['army_regiment_id'], r['maximum_soldiers']] for r in ep['cohort_regiments']])
         == state['cohort_maxima'], 'cohort identity/capacity changed')
    need(binding['native_revision'] >= state['binding']['native_revision'], 'native frame went backwards')


def _clock(state, observation):
    ep = observation['endpoint']
    delta = ep['day'] - state['last_day']
    need(delta in (0, 1), 'missing daily observation: preserve a wider interval, reject exact-day credit')
    if delta == 0:
        return state['last_clock_generation']
    c = observation.get('clock')
    need(isinstance(c, dict), 'day advance lacks actual native sentinel status')
    need(all(integer(c.get(key)) for key in ('starting_date_raw', 'target_date_raw',
         'last_observed_date_raw', 'trigger_date_raw', 'speed', 'completed_daily_ticks',
         'overshoot_days', 'signed_date_delta_from_target_raw', 'army_count',
         'combat_count', 'intermediate_pause_count')), 'clock counts/dates require actual integers')
    need(c.get('state') == 'triggered' and c.get('starting_date_raw') == ep['date_raw'] - 24
         and c.get('target_date_raw') == c.get('last_observed_date_raw') == c.get('trigger_date_raw') == ep['date_raw'],
         'native clock start/target/trigger/end differs')
    need(c.get('speed') == 5 and c.get('completed_daily_ticks') == 1
         and c.get('overshoot_days') == 0 and c.get('signed_date_delta_from_target_raw') == 0
         and c.get('abnormal') is False and c.get('pause_observed') is True,
         'clock is not one actual day with zero overshoot and pause')
    need(c.get('mode') == 'terminal_or_sentinel' and c.get('army_count') == 0
         and c.get('combat_count') == 0, 'R10 uses its existing date-only clock contract')
    reasons = c.get('trigger_reasons')
    if reasons == ['date_deadline']:
        need(c.get('pause_wrapper_called') is True and c.get('intermediate_pause_count') == 0,
             'date pause provenance differs')
    else:
        need(isinstance(reasons, list) and 'native_pause' in reasons
             and c.get('pause_wrapper_called') is False and c.get('intermediate_pause_count') == 1,
             'unexpected native stop provenance')
    generation = c.get('generation')
    need(integer(generation) and generation > state['last_clock_generation'],
         'sentinel generation must increase')
    return generation


def propose_move(plan, state, observation, preview):
    """Return one proposal plus pending state BEFORE submission; never retries.

    `preview` is the actual existing Driver preview result. Its binding must
    name this exact paused source frame. Native final Move validation remains
    necessary; preview availability is not a standalone CanMove verdict.
    """
    destinations = targets(plan)
    ep, unit, binding = _valid_observation(plan, observation)
    _same_subject(state, ep, unit, binding)
    need(state['phase'] == 'ready', 'pending/uncertain Move must not be resubmitted')
    need(ep['day'] == state['last_day'] and ep['day'] < 90,
         'observe the current day first; no action after absolute deadline')
    need(unit['state'] in plan['arrival_states'] and unit['route'] == [] and unit['target'] is None,
         'C departs only from its actual stationary source')
    need(unit['current_province_id'] == state['ready_province'], 'unlogged stationary relocation')
    target = destinations[state['target_index']]
    p = preview.get('route_preview', {})
    need(preview.get('accepted') is True and p.get('status') == 'available',
         'native preview rejected/deferred/unavailable')
    for key, expected in [('queried_snapshot_id', binding['snapshot_id']),
                          ('queried_revision', binding['revision']),
                          ('queried_native_revision', binding['native_revision']),
                          ('queried_connection_generation', binding['connection_generation']),
                          ('queried_episode_run_id', binding['episode'])]:
        need(preview.get(key) == expected, 'stale/foreign preview: ' + key)
    need(p.get('army_id') == unit['army_id'] and p.get('origin_province_id') == unit['current_province_id']
         and p.get('target_province_id') == target and p.get('previewed_date_raw') == ep['date_raw'],
         'preview target/origin/Army/date differs from frozen next target')
    route = deepcopy(p.get('route_province_ids'))
    need(isinstance(route, list) and route and all(integer(x) and x > 0 for x in route),
         'preview route missing or malformed')
    if route[0] == unit['current_province_id']:
        route = route[1:]
    need(route and route[-1] == target, 'preview does not reach next frozen target')
    new = deepcopy(state)
    new.update(phase='pending_move', pending_route=route,
               pending_origin=unit['current_province_id'], pending_target=target,
               binding=deepcopy(binding))
    return new, {'tool': 'ck3_move_army', 'army_id': state['army_id'],
                 'target_province_id': target, 'expected_revision': binding['revision'],
                 'dispatch_performed': False, 'ACK_is_arrival': False}


def observe(plan, state, observation):
    """Accept an independent same-frame/day or next-day poststate, purely.

    Retain every day's call in the caller's log. Unknown execution results stay
    pending; the caller may read again but must not automatically submit again.
    """
    destinations = targets(plan)
    ep, unit, binding = _valid_observation(plan, observation)
    _same_subject(state, ep, unit, binding)
    need(state['phase'] not in ('arrived', 'budget-censored', 'stopped'), 'terminal C cannot restart')
    generation = _clock(state, observation)
    new = deepcopy(state)
    target = destinations[state['target_index']]
    at_target = _stationary_at(unit, target, plan['arrival_states'])
    if state['phase'] == 'pending_move':
        # Move ACKs are deliberately not an input. A later native revision on
        # the original paused date must show the actual complete applied route.
        if ep['day'] != state['last_day']:
            raise ValueError('Move application not independently read before advancing')
        if binding['native_revision'] == state['binding']['native_revision']:
            need(unit['route'] == [] and unit['target'] is None
                 and unit['current_province_id'] == state['pending_origin'],
                 'same-revision Move consequence cannot be independent')
            return new
        need(unit['current_province_id'] == state['pending_origin']
             and unit['state'] == 'moving' and unit['route'] == state['pending_route']
             and unit['target'] == state['pending_target'], 'actual applied route differs from submitted preview')
        new['phase'] = 'marching'
    elif state['phase'] == 'marching':
        if at_target:
            need(ep['day'] > state['last_not_arrived_day'], 'arrival requires a later observation')
            bracket = [state['last_not_arrived_day'], ep['day']]
            need(bracket[1] - bracket[0] <= 1, 'arrival bracket is wider than one day')
            new['arrivals'].append({'province_id': target, 'day': ep['day'],
                                    'observed_interval_days': bracket, 'exact_arrival_tick': None})
            new['target_index'] += 1
            new['phase'] = 'arrived' if new['target_index'] == len(destinations) else 'ready'
            new['pending_route'] = None
            new['ready_province'] = target
            new['last_not_arrived_day'] = ep['day']
        else:
            need(unit['state'] == 'moving' and unit['route'] and unit['route'][-1] == target
                 and unit['target'] == target, 'unexpected route/state is a deviation, not arrival')
            route = state['pending_route']
            need(any(unit['route'] == route[i:] for i in range(len(route))),
                 'unlogged reroute is not a suffix of the independently applied route')
            new['last_not_arrived_day'] = ep['day']
    else:
        need(unit['route'] == [] and unit['target'] is None
             and unit['state'] in plan['arrival_states']
             and unit['current_province_id'] == state['ready_province'],
             'unlogged Move while ready is not C policy compliance')
        new['last_not_arrived_day'] = ep['day']
    if ep['day'] == 90 and new['phase'] != 'arrived':
        new.update(phase='budget-censored', reason='actual original day90 without final arrival')
    new.update(last_day=ep['day'], last_clock_generation=generation, binding=deepcopy(binding))
    return new


def stop(state, reason):
    """Explicit operator/competing/measurement stop never becomes D90 censor."""
    need(isinstance(reason, str) and reason, 'record stop reason')
    new = deepcopy(state)
    new.update(phase='stopped', reason=reason)
    return new


def outcome(state, observation):
    ep = observation['endpoint']
    need(ep['day'] == state['last_day'] and observation['binding']['snapshot_id'] == state['binding']['snapshot_id'],
         'outcome must use the last independently observed state')
    return {'phase': state['phase'], 'observed_day': ep['day'], 'date_raw': ep['date_raw'],
            'waypoint_and_goal_observations': deepcopy(state['arrivals']),
            'original_cohort_physical_current': ep['cohort_current'],
            'original_cohort_maximum': ep['cohort_maximum'],
            'all_strategy_current': ep['all_strategy_current'],
            'all_strategy_maximum': ep['all_strategy_maximum'],
            'per_army_supply': deepcopy(ep['units']), 'treasury_raw': ep['treasury_raw'],
            'move_target_observable': observation['binding']['move_target_observable'],
            'target_null_is_independent_clearance_proof': False,
            'physical_ADD_or_debit_cause': None, 'actual_military_fees': None,
            'common_date_comparison_performed': False, 'winner': None,
            'live_execution_performed': False, 'research_card_closed': False}
