"""Offline whole-direct A decision input/state consumer; never calls the game.

Uses the existing R10 small-text Evidence and complete native endpoint readers.
Only A inputs are required here. Full ABC/fees eligibility belongs to r10_compare.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re

import r10_compare as c


def _ids(value, label, minimum=0, maximum=2**31-1):
    c.need(isinstance(value, list) and value and all(
        type(x) is int and minimum <= x and (maximum is None or x <= maximum) for x in value
    ) and len(value) == len(set(value)), label + ' must contain unique native IDs')
    return set(value)


def _whole(ep, plan, evidence, runtime=None, army_id=None):
    c.schema_check(ep, 'endpoint')
    ids = _ids(ep['strategy_army_ids'], 'A Army scope')
    c.need(len(ids) == 1 and (army_id is None or ids == {army_id}),
           'A whole-direct Army scope changed; do not hide split/merge as loss')
    snap = c.frame(evidence.json(ep['snapshot']), runtime)
    positions = snap.get('player_armies', [])
    c.need(len({p.get('army_id') for p in positions}) == len(positions),
           'duplicate Army map row')
    query = c.body(evidence.json(ep['army_result']))
    scope = query.get('army_strengths_query_scope') or {}
    c.need(scope.get('published_scope_status') == 'available'
           and scope.get('army_ids') == ep['strategy_army_ids'],
           'A requires explicit complete query scope')
    c.need({r.get('army_id') for r in query.get('army_strengths', [])} == ids,
           'A query rows differ from whole Army scope')
    value = c.endpoint(ep, plan, evidence, runtime)
    for p in positions:
        if p.get('army_id') not in ids:
            continue
        route = p.get('route_province_ids')
        c.need(isinstance(route, list) and all(type(x) is int and x > 0 for x in route),
               'A route contains unknown Province IDs')
        c.need(p['route_read_status'] == ('complete_nonempty' if route else 'complete_empty'),
               'A route status contradicts actual vector')
        c.need(type(p.get('current_province_id')) is int and p['current_province_id'] > 0,
               'A current province is unknown')
    return value, snap


def _preview(pin, ep, plan, evidence, runtime=None):
    actual, snap = _whole(ep, plan, evidence, runtime)
    unit = actual['units'][0]
    aid = unit['army_id']; target = plan['goal_province_id']
    row = next(x for x in snap['player_armies'] if x['army_id'] == aid)
    c.need(row.get('controllable') is True, 'A requires a currently controllable Army')
    receipt = c.body(evidence.json(pin)); preview = receipt.get('route_preview') or {}
    c.need(receipt.get('accepted') is True and preview.get('status') == 'available',
           'A native route preview is unavailable/deferred')
    for q, s in [('snapshot_id', 'snapshot_id'), ('revision', 'revision'),
                 ('native_revision', 'native_revision'), ('episode_run_id', 'episode_run_id')]:
        c.need(receipt.get('queried_' + q) == snap[s], 'A preview frame differs: ' + q)
    c.need(receipt.get('queried_connection_generation') == snap['diagnostics']['connection_generation'],
           'A preview generation differs')
    c.need(receipt.get('step') == f'preview-move-army-{aid}-to-{target}'
           and preview.get('army_id') == aid
           and preview.get('origin_province_id') == unit['current_province_id']
           and preview.get('target_province_id') == target
           and preview.get('previewed_date_raw') == snap['date_raw'],
           'A preview subject/origin/target/date differs')
    route = preview.get('route_province_ids')
    c.need(isinstance(route, list) and route and all(type(x) is int and x > 0 for x in route),
           'A preview lacks a complete native route')
    remaining = route[1:] if route[0] == unit['current_province_id'] else route
    c.need(remaining and remaining[-1] == target, 'A preview does not reach frozen goal')
    return list(remaining)


def admit(plan, runtime, loaded_save_sha256, cold_start, fresh_preview, evidence):
    """Validate A only and return one proposed existing typed Move, not an ACK.

    Frozen preview belongs to the baseline session; fresh_preview belongs to this
    independent cold session. Unknown B/C/fee prerequisites do not block A action.
    No output from this function grants full controlled-comparison eligibility.
    """
    c.need(plan.get('schema') == 'xar.e04.r10.plan.v1' and plan.get('status') == 'frozen',
           'A plan is UNBOUND or not frozen')
    c.schema_check(runtime, 'runtime'); evidence.all_pins(runtime)
    build = plan['build']
    c.need(build.get('version') == '1.20.0.4' and build.get('steam_build') == 25734779
           and build.get('exe_sha256') == c.EXE, 'A exact build differs')
    for key, pattern in [('source_head', r'[0-9a-f]{40}'), ('native_dll_sha256', r'[0-9a-f]{64}')]:
        c.need(isinstance(build.get(key), str) and re.fullmatch(pattern, build[key])
               and runtime[key] == build[key], 'A runtime source/DLL differs')
    frozen = datetime.fromisoformat(plan['frozen_at_utc'].replace('Z', '+00:00'))
    started = datetime.fromisoformat(runtime['started_at_utc'].replace('Z', '+00:00'))
    c.need(frozen.tzinfo is not None and started.tzinfo is not None and frozen < started,
           'A plan was not frozen before cold session')
    save = plan['normal_save']
    c.need(save.get('kind') == 'normal-native-checkpoint' and type(save.get('bytes')) is int
           and save['bytes'] > 0 and isinstance(save.get('sha256'), str)
           and re.fullmatch(r'[0-9a-f]{64}', save['sha256'])
           and loaded_save_sha256 == save['sha256'], 'A normal checkpoint binding differs')
    evidence.raw(save['save_receipt']); evidence.raw(save['normal_origin_proof'])
    c.need(type(plan.get('t0_raw')) is int and plan.get('raw_per_day') == 24
           and plan.get('max_natural_days') == 90, 'A absolute natural-day budget is unbound')
    c.need(type(plan.get('goal_province_id')) is int and plan['goal_province_id'] > 0,
           'A goal Province is unknown')
    c.need(isinstance(plan.get('arrival_states'), list) and plan['arrival_states']
           and all(isinstance(x, str) and x for x in plan['arrival_states']),
           'A arrival state definition is unbound')
    original = _ids(plan.get('original_regiment_ids'), 'A original cohort', maximum=None)
    reports = plan.get('report_days')
    c.need(isinstance(reports, list) and reports == sorted(set(reports))
           and all(type(x) is int and 1 <= x <= 90 for x in reports), 'A report dates unbound')
    c.need(type(plan.get('follow_after_arrival_to_day90')) is bool
           and plan['follow_after_arrival_to_day90'] == (plan.get('post_arrival_policy') is not None),
           'A D90 needs a policy frozen before results')
    c.need(isinstance(plan.get('event_policy'), str) and bool(plan['event_policy'])
           and type(plan.get('wall_budget_seconds_per_arm')) is int
           and plan['wall_budget_seconds_per_arm'] > 0, 'A event/wall budget policy unbound')
    c.need(plan['strategies']['A'].get('mode') == 'whole-direct', 'A is not whole-direct')
    c.need(plan['baseline']['day'] == cold_start['day'] == 0, 'A cold session must be T0')
    base, _ = _whole(plan['baseline'], plan, evidence)
    c.need({r['army_regiment_id'] for r in base['DATA']} == original,
           'A original cohort does not cover the entire T0 Army')
    cold, snap = _whole(cold_start, plan, evidence, runtime)
    c.need(cold == base, 'A cold T0 observable baseline differs')
    c.need(not c.arrived(cold, plan), 'A starts already arrived; freeze another T0')
    frozen_route = _preview(plan['strategies']['A']['route_preview'], plan['baseline'], plan, evidence)
    route = _preview(fresh_preview, cold_start, plan, evidence, runtime)
    c.need(route == frozen_route, 'A fresh native route differs from frozen direct preview')
    aid = cold['units'][0]['army_id']
    return {'schema': 'xar.e04.strategy-a.state.v1', 'plan': deepcopy(plan), 'runtime': deepcopy(runtime),
            'cold_start': deepcopy(cold_start), 'fresh_preview': deepcopy(fresh_preview),
            'army_id': aid, 'route': route, 'move_postcondition': None, 'days': [],
            'observations': [deepcopy(cold_start)], 'actual': cold, 'first_arrival_day': None,
            'arrival_actual': None,
            'last_not_arrived_day': 0,
            'proposed_call': {'tool': 'ck3_move_army', 'arguments': {
                'army_id': aid, 'target_province_id': plan['goal_province_id'],
                'expected_revision': snap['revision']}},
            'calls_executed': False, 'live_execution_performed': False, 'research_card_closed': False}


def observe_move(state, after, evidence):
    """Consume independent same-day post-state; no Move ACK is accepted here."""
    c.need(state['move_postcondition'] is None and not state['days'], 'A Move already observed')
    plan = state['plan']; runtime = state['runtime']
    actual, snap = _whole(after, plan, evidence, runtime, state['army_id'])
    before = c.frame(evidence.json(state['cold_start']['snapshot']), runtime)
    c.need(after['day'] == 0 and snap['date_raw'] == before['date_raw']
           and snap['native_revision'] > before['native_revision']
           and after['snapshot'] != state['cold_start']['snapshot'], 'A needs independent Move post-state')
    unit = actual['units'][0]
    c.need(unit['target'] == plan['goal_province_id'] and unit['route'] == state['route'],
           'A Move postcondition target/complete route differs')
    c.need(actual['cohort_regiments'] == state['actual']['cohort_regiments'],
           'A Move postcondition changed original cohort')
    out = deepcopy(state); out['move_postcondition'] = deepcopy(after); out['actual'] = actual
    out['proposed_call'] = None
    return out


def update(state, clock_day, observation, evidence):
    """Add one actual exact day with full cohort; raises on measurement mismatch.

    A world interruption is retained as needs_current_state_decision. This reader
    neither retries a Move nor erases contact, an early STOP or a missing cohort.
    """
    c.need(state['move_postcondition'] is not None, 'A Move ACK is not an observed route')
    plan = state['plan']; next_day = len(state['days']) + 1
    c.need(next_day <= 90 and clock_day['day'] == observation['day'] == next_day,
           'A days missing/duplicate/reset or beyond absolute D90')
    c.need(state['first_arrival_day'] is None or plan['follow_after_arrival_to_day90'],
           'A unregistered post-arrival continuation')
    c.need(clock_day['paused_snapshot'] == observation['snapshot']
           and clock_day['strategy_army_ids'] == observation['strategy_army_ids'],
           'A clock/endpoint frame or scope differs')
    days = state['days'] + [deepcopy(clock_day)]
    actual, _ = _whole(observation, plan, evidence, state['runtime'], state['army_id'])
    clock = c.clock_days({'runtime': state['runtime'], 'days': days}, plan, evidence)
    is_arrived = c.arrived(actual, plan)
    out = deepcopy(state); out['days'] = days; out['actual'] = actual
    out['observations'].append(deepcopy(observation))
    if out['first_arrival_day'] is None:
        if is_arrived:
            c.need(clock['first_arrival'] == next_day, 'A first arrival differs from daily scan')
            out['first_arrival_day'] = next_day
            out['arrival_actual'] = deepcopy(actual)
        else:
            out['last_not_arrived_day'] = next_day
    return out


def report(state):
    """A-only observations. Joint common-date and fee qualification stays external."""
    plan = state['plan']; actual = state['actual']; day = len(state['days'])
    first = state['first_arrival_day']
    unit = actual['units'][0]
    following = unit['target'] == plan['goal_province_id'] and bool(unit['route'])
    kind = 'arrived' if first is not None else 'budget-censored' if day == 90 else None
    return {'arm': 'A', 'machine_id': state['runtime']['machine_id'],
            'observed_day': day, 'observed_date_raw': actual['date_raw'],
            'absolute_deadline_raw': plan['t0_raw'] + 90*24,
            'disposition': kind, 'first_arrival_day': first,
            'arrival_interval_days': [state['last_not_arrived_day'], first] if first is not None else None,
            'current_actual': deepcopy(actual), 'arrival_actual': deepcopy(state['arrival_actual']),
            'actual_fees': None, 'winner': None,
            'action_status': 'terminal' if kind else 'observe_move_postcondition' if state['move_postcondition'] is None
            else 'continue_exact_day' if following else 'needs_current_state_decision',
            'report_date_endpoints': [deepcopy(x) for x in state['observations'] if x['day'] in plan['report_days']],
            'joint_common_date_rows': None,
            'D90_endpoint': deepcopy(state['observations'][-1]) if day == 90 and plan['follow_after_arrival_to_day90'] else None,
            'full_ABC_eligibility_assessed': False, 'live_execution_performed': False, 'research_card_closed': False}
