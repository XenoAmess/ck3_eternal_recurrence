"""Small policy adapter over an admitted strategy_a state and real preview shape.

No new MCP API/schema, move/split dispatch, hypothetical Army or route simulator.
Native current aggregate usage is never replaced by Army size or future usage.
"""
from __future__ import annotations

from copy import deepcopy

import r10_compare as c
import strategy_a as a


def _latest(state):
    return (state['observations'][-1] if state['days'] else
            state['move_postcondition'] or state['cold_start'])


def _signed(value, label, bits):
    c.need(type(value) is int and -(1 << (bits-1)) <= value < (1 << (bits-1)),
           label + ' must be a signed native integer')
    return value


def _province_row(row, role, province_id):
    if row is None:
        return None
    c.need(isinstance(row, dict) and row.get('role') == role
           and type(row.get('province_id')) is int and row['province_id'] == province_id,
           'preview supply role/Province differs')
    if row.get('status') == 'unavailable':
        c.need(isinstance(row.get('unavailable_reason'), str) and bool(row['unavailable_reason']),
               'unavailable province supply requires original reason')
        return None
    c.need(row.get('status') == 'available' and row.get('unavailable_reason') is None
           and type(row.get('scale')) is int and row['scale'] == 1,
           'preview supply availability/scale differs')
    limit = _signed(row.get('native_supply_limit_soldiers'), 'native limit', 32)
    usage = _signed(row.get('native_supply_usage_soldiers'), 'native usage', 32)
    return {'province_id': province_id, 'native_supply_limit_soldiers': limit,
            'native_supply_usage_soldiers': usage, 'scale': 1,
            'signed_usage_exceeds_limit': usage > limit,
            'usage_minus_limit_soldiers': usage-limit}


def _supply(preview, actual, snapshot):
    supply = preview.get('province_supply')
    if supply is None:
        return {'current': None, 'target': None, 'context': None,
                'unavailable_reason': 'province_supply_absent'}
    c.need(isinstance(supply, dict), 'preview province_supply is malformed')
    unit = actual['units'][0]
    c.need(type(supply.get('army_id')) is int and supply['army_id'] == unit['army_id'],
           'preview supply subject differs')
    owner = supply.get('owner_character_id')
    c.need(owner is None or (type(owner) is int and owner == snapshot['played_character']['character_id']),
           'preview supply owner differs')
    current = _province_row(supply.get('current'), 'current', unit['current_province_id'])
    target = _province_row(supply.get('target'), 'target', preview['target_province_id'])
    expected = 'available' if current is not None and target is not None else (
        'partial' if current is not None or target is not None else 'unavailable')
    c.need(supply.get('status') == expected, 'preview supply status contradicts rows')
    if current is not None or target is not None:
        c.need(owner is not None and type(supply.get('native_carmy_id')) is int,
               'available province supply lacks captured owner/CArmy')
    return {'current': current, 'target': target,
            'context': {key: deepcopy(supply.get(key)) for key in
                        ('army_id', 'native_carmy_id', 'owner_character_id', 'commander_character_id')},
            'unavailable_reason': deepcopy(supply.get('unavailable_reason'))}


def _current_rate(query, army_id):
    row = next(x for x in query['army_strengths'] if x['army_id'] == army_id)
    out = {}
    for name in ('current_supply_change_monthly', 'current_attrition_fraction'):
        raw, scale = row.get(name+'_raw'), row.get(name+'_scale')
        if raw is None:
            c.need(scale is None or (type(scale) is int and scale == 100000), name + ' scale differs')
            out[name] = None
        else:
            _signed(raw, name, 64)
            c.need(type(scale) is int and scale == 100000, name + ' scale differs')
            out[name] = {'raw': raw, 'scale': scale}
    return out


def next_decision(state, evidence, fresh_preview=None):
    """Annotate existing A decision; return existing read-only/Move call shapes.

    Supply absence never invalidates a legal Move. Pressure can justify reviewing
    a different split policy, but a frozen whole-direct arm never dispatches split.
    The caller uses ordinary battle/event policies for a world interruption.
    """
    c.need(state.get('schema') == 'xar.e04.strategy-a.state.v1'
           and state['plan']['strategies']['A']['mode'] == 'whole-direct',
           'route adapter requires existing whole-direct A state')
    plan = state['plan']; runtime = state['runtime']; ep = _latest(state)
    actual, snap = a._whole(ep, plan, evidence, runtime, state['army_id'])
    c.need(actual == state['actual'], 'A latest endpoint differs from state actual')
    unit = actual['units'][0]
    route = list(state['route'])
    observed = []
    for observed_ep in state['observations'] + ([state['move_postcondition']] if state['move_postcondition'] else []):
        original = c.frame(evidence.json(observed_ep['snapshot']), runtime)
        rows = [x for x in original.get('player_armies', []) if x.get('army_id') == state['army_id']]
        c.need(len(rows) == 1, 'pass-through observation lacks a unique actual Army')
        province = rows[0].get('current_province_id')
        if province in route:
            observed.append({'province_id': province, 'day': observed_ep['day'],
                             'date_raw': original['date_raw'], 'snapshot': deepcopy(observed_ep['snapshot'])})
    supply = {'current': None, 'target': None, 'context': None,
              'unavailable_reason': 'fresh_preview_not_supplied'}
    fresh_route = None
    terminal = state['first_arrival_day'] is not None or len(state['days']) == 90
    ordinary_status = a.report(state)['action_status']
    if fresh_preview is not None:
        # _preview joins every queried_* field, actual origin, date and legal route.
        fresh_route = a._preview(fresh_preview, ep, plan, evidence, runtime)
        preview = c.body(evidence.json(fresh_preview))['route_preview']
        supply = _supply(preview, actual, snap)
    rates = _current_rate(c.body(evidence.json(ep['army_result'])), state['army_id'])
    pressure = None if supply['current'] is None else supply['current']['signed_usage_exceeds_limit']
    # The only actions prepared here are existing A Move or the existing readonly preview.
    call = None
    if not terminal and ordinary_status != 'needs_current_state_decision':
        if state['proposed_call'] is not None:
            call = deepcopy(state['proposed_call'])
        elif fresh_preview is None:
            call = {'tool': 'ck3_execute_step', 'arguments': {
                'step': f'preview-move-army-{state["army_id"]}-to-{plan["goal_province_id"]}',
                'expected_revision': snap['revision']}}
    return {'proposed_call': call,
            'policy': 'terminal' if terminal else 'preserve_frozen_whole_direct',
            'ordinary_policy_action_status': ordinary_status,
            'current_aggregate_pressure_suggests_review': pressure,
            'source_frame': {'machine_id': runtime['machine_id'], 'episode': runtime['episode'],
                             'snapshot': deepcopy(ep['snapshot']), 'army_result': deepcopy(ep['army_result']),
                             'preview': deepcopy(fresh_preview), 'date_raw': snap['date_raw'],
                             'revision': snap['revision'], 'native_revision': snap['native_revision'],
                             'connection_generation': snap['diagnostics']['connection_generation']},
            'observed_current': {'army_id': state['army_id'], 'current_province_id': unit['current_province_id'],
                                 'original_cohort_current': actual['cohort_current'],
                                 'all_strategy_current': actual['all_strategy_current'],
                                 'stock_raw': unit['stock_raw'], 'capacity_raw': unit['capacity_raw'],
                                 'scale': unit['scale'], **rates},
            'native_province_supply': supply,
            'queued_route': list(unit['route']), 'queued_target': unit['target'],
            'fresh_preview_route': fresh_route, 'initial_preview_route': route,
            'actual_observed_on_initial_route': observed,
            'not_independently_observed_province_ids': [p for p in route if p not in {x['province_id'] for x in observed}],
            'unknown': {'future_target_usage_soldiers': None, 'future_supply_rate_raw': None,
                        'future_army_stock_raw': None, 'route_intermediate_supply': None,
                        'route_terrain_effects': None, 'future_losses_soldiers': None,
                        'future_refills_soldiers': None, 'military_maintenance_paid_raw': None,
                        'split_size_to_avoid_loss': None, 'split_loss_saving_soldiers': None},
            'calls_executed': False, 'research_card_closed': False,
            'full_ABC_eligibility_assessed': False}
