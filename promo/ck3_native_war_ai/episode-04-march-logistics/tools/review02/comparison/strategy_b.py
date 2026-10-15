"""Read-only B-arm action/state audit for the E04 R10 frozen comparison.

Consumes only small, pinned JSON evidence; never imports the SDK or controls CK3.
The comparison consumer remains responsible for daily clocks, arrival and fees.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import r10_compare as c


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def input_bytes(path):
    need(path.suffix.lower() == '.json' and path.is_file() and 0 < path.stat().st_size <= c.MAX_FILE,
         'input must be a bounded small JSON file; raw saves/binaries are never opened')
    return path.read_bytes()


def recipe(plan, evidence):
    """Return a concrete, non-executing B recipe from the frozen R10 plan."""
    base = c.check_plan(plan, evidence)
    bp = plan['strategies']['B']
    need(bp['merge_destination_policy'] in ('destination-main', 'destination-child'),
         'B recipe needs a concrete destination-main/destination-child policy')
    return {'schema': 'xar.e04.r10.strategy-b-recipe.v1', 'plan_consistent': True,
            'baseline_date_raw': base['date_raw'], 'absolute_deadline_raw': plan['t0_raw'] + 2160,
            'role_assignment': {'main': bp['rest_province_ids'][0], 'child': bp['rest_province_ids'][1]},
            'rest_exit': {'minimum_stock_raw': bp['minimum_stock_raw'], 'scale': 100000,
                          'maximum_deficit': bp['maximum_deficit'],
                          'maximum_rest_days': bp['maximum_rest_days'],
                          'rule': 'actual threshold OR actual maximum-stay; retain failed recovery outcome'},
            'sequence': ['independent normal cold load and actual T0 equality',
                         'split actual whole Army once; identify new resolved CArmy by post-state',
                         'move main/child to their frozen distinct sites; observe actual stationary arrival',
                         'observe and record each rest exit; do not infer growth from a monthly getter',
                         'move each to the frozen meeting province; observe both stationary',
                         'merge once in frozen direction; verify source absent, destination retained and complete DATA',
                         'retain all extra rows and current commander; move merged Army to the frozen goal',
                         'daily existing exact-clock observations; preserve first actual arrival interval'],
            'merge_province_id': bp['merge_province_id'],
            'merge_destination_policy': bp['merge_destination_policy'],
            'commander_policy': bp['commander_policy'], 'goal_province_id': plan['goal_province_id'],
            'failed_or_unknown_action_policy': 'preserve receipt and stop trace; never resubmit',
            'site_stock_growth_semantically_qualified': False, 'R09_mechanism_qualified': False,
            'live_execution_performed': False, 'research_card_closed': False,
            'scope': 'Recipe and supplied pinned plan consistency. Existing R09/site evidence must '
                     'be independently qualified; this output is not execution readiness or a result.'}


def observe(ep, plan, evidence, runtime):
    """Use R10's native integer/DATA projection, adding actual CArmy identity.

    Public roster shadows are retained separately. They cannot identify a child:
    every strategy row must have an available exact native resolution witness.
    """
    metrics = c.endpoint(ep, plan, evidence, runtime)
    snapshot = c.frame(evidence.json(ep['snapshot']), runtime)
    query = c.body(evidence.json(ep['army_result']))
    need(query.get('status') == 'available', 'complete available Army result required')
    wanted = set(ep['strategy_army_ids'])
    rows = {a['army_id']: a for a in query['army_strengths'] if a['army_id'] in wanted}
    native = {}
    for aid, row in rows.items():
        resolution = row.get('native_army_resolution_v1') or {}
        actual = row.get('native_carmy_id')
        need(c.integer(actual) and actual >= 0 and resolution.get('status') == 'available'
             and resolution.get('ready') is True and resolution.get('entry_full_id') == actual,
             'strategy Army lacks actual CArmy resolution')
        need(actual not in native.values(), 'strategy IDs alias one actual CArmy')
        native[aid] = actual
    positions = {p['army_id']: p for p in snapshot['player_armies']}
    need(len(positions) == len(snapshot['player_armies']), 'duplicate public roster row')
    regs = {}
    for row in rows.values():
        for regiment in row['regiment_strengths']:
            rid = regiment['army_regiment_id']
            regs[rid] = regiment
        for group in row['regiment_replenishment_records_v1']:
            need(group.get('ready') is True and group.get('source') == 'native_all_data_records',
                 'DATA must be the complete native collection')
            keys = [(r.get('record_index'), r.get('persistent_regiment_id'), r.get('chunk_index'))
                    for r in group['records']]
            need(len(keys) == len(set(keys)) and all(r.get('status') == 'available'
                 for r in group['records']), 'DATA identities unavailable/duplicate')
            need(all(all(c.integer(value) and value >= 0 for value in key) for key in keys),
                 'DATA identity fields must be complete native integers')
    return {'endpoint': metrics, 'snapshot': snapshot, 'rows': rows,
            'positions': positions, 'native': native, 'regiments': regs,
            'unqueried_public_roster_ids': sorted(set(positions) - wanted)}


def _frame_order(before, after, same_day=False):
    a, b = before['snapshot'], after['snapshot']
    need(a['episode_run_id'] == b['episode_run_id'] and
         a['diagnostics']['connection_generation'] == b['diagnostics']['connection_generation'],
         'action crossed episode/generation')
    need(b['date_raw'] >= a['date_raw'] and b['native_revision'] >= a['native_revision']
         and b['revision'] >= a['revision'], 'action evidence goes backwards')
    if same_day:
        need(a['date_raw'] == b['date_raw'], 'command post-state must have no intervening date tick')


def _stationary(view, ids, province):
    for aid in ids:
        p = view['positions'].get(aid) or {}
        need(p.get('owner_character_id') == view['snapshot']['played_character']['character_id']
             and p.get('controllable') is True and p.get('in_combat') is False
             and p.get('retreating') is False and p.get('current_province_id') == province
             and p.get('army_state') == 'regular' and p.get('route_read_status') == 'complete_empty'
             and p.get('route_province_ids') == [] and p.get('move_target_province_id') is None,
             'actual stationary owner/control/location/route gate failed')


def _integer_rows(view):
    return {k: (r['current_soldiers'], r['maximum_soldiers'], r['scale'])
            for k, r in view['regiments'].items()}


def _passive_observation(previous, view):
    _frame_order(previous, view)
    need(previous['native'] == view['native'], 'strategy Army identity changed without a recorded action')
    for aid in previous['native']:
        old, new = previous['positions'][aid], view['positions'][aid]
        if old['current_province_id'] != new['current_province_id']:
            need(old.get('route_province_ids') and old.get('move_target_province_id') is not None,
                 'location changed without a previously observed movement order')


def _action(event, before, after, evidence, seen):
    request = evidence.json(event['request'])
    response = evidence.json(event['response'])
    need(isinstance(request, dict), 'action request object required')
    request_id = request.get('request_id')
    need(isinstance(request_id, str) and request_id and request_id not in seen,
         'duplicate/missing action request_id; never resend a failed or unknown action')
    seen.add(request_id)
    args = request.get('arguments') or {}
    need(request.get('tool') == 'ck3_execute_step' and
         args.get('expected_revision') == before['snapshot']['revision'],
         'action did not bind fresh public revision')
    if 'request' in response:
        need(response['request'] == request, 'response request witness differs')
    need(event['outcome'] in ('applied', 'rejected', 'unknown'), 'invalid action outcome')
    if event['outcome'] != 'applied':
        # Rejection and timeout stay terminal for this trace. A future observation
        # can diagnose them; it cannot authorize a replay of this request.
        return args['step'], None
    body = c.body(response)
    need(body.get('step') == args.get('step'), 'response step differs from frozen request')
    need(response.get('is_error') is not True and body.get('accepted') is True,
         'applied action is only an error/rejection')
    need(after is not None, 'ACK without independent complete post-state')
    _frame_order(before, after, same_day=True)
    return args['step'], body.get('war_action') or {}


def _summary(view, plan):
    m = view['endpoint']
    extra = sorted(set(view['regiments']) - set(plan['original_regiment_ids']))
    return {'day': m['day'], 'date_raw': m['date_raw'],
            'original_cohort_current': m['cohort_current'],
            'original_cohort_maximum': m['cohort_maximum'],
            'all_strategy_current': m['all_strategy_current'],
            'all_strategy_maximum': m['all_strategy_maximum'],
            'extra_regiment_rows': [view['regiments'][k] for k in extra],
            'extra_regiment_DATA': [r for r in m['DATA'] if r['army_regiment_id'] in extra],
            'commander_id': m['commander_id'],
            'per_army_supply': m['units'], 'actual_carmy_by_public_id': view['native'],
            'unqueried_public_roster_ids': view['unqueried_public_roster_ids']}


def audit(plan, arm, trace, evidence, *, plan_sha256):
    """Check the B event state machine without granting R10/live completion.

    trace = {schema, plan_sha256, events}. Applied events have kind, before,
    after, request, response, outcome; rest-enter/exit have endpoint/unit/site.
    An action's no-retry rule applies to its logical operation as well as ID.
    """
    base = c.check_plan(plan, evidence)
    c.schema_check(arm, 'arm')
    need(arm['label'] == 'B', 'only the B arm is accepted')
    need(isinstance(trace, dict) and trace.get('schema') == 'xar.e04.r10.strategy-b-events.v1',
         'wrong B trace schema')
    need(isinstance(trace.get('events'), list), 'B trace needs an ordered events array')
    need(trace.get('plan_sha256') == plan_sha256, 'B trace does not bind frozen plan bytes')
    evidence.all_pins(trace)
    rt = arm['runtime']
    bp = plan['strategies']['B']
    need(bp['merge_destination_policy'] in ('destination-main', 'destination-child'),
         'B audit needs a concrete destination-main/destination-child policy')
    need(arm['loaded_save_sha256'] == plan['normal_save']['sha256'], 'cold normal save SHA differs')
    need(rt['source_head'] == plan['build']['source_head'] and
         rt['native_dll_sha256'] == plan['build']['native_dll_sha256'], 'runtime source/DLL differs')
    frozen = datetime.fromisoformat(plan['frozen_at_utc'].replace('Z', '+00:00'))
    started = datetime.fromisoformat(rt['started_at_utc'].replace('Z', '+00:00'))
    need(started.tzinfo is not None and frozen < started, 'plan must precede cold session')
    cold = observe(arm['cold_start'], plan, evidence, rt)
    need(cold['endpoint'] == base and arm['cold_start']['day'] == 0,
         'cold T0 observable baseline differs')
    need(len(cold['rows']) == 1, 'B starts from one frozen actual whole Army')
    main = next(iter(cold['rows']))
    child = None
    phase = 'whole'
    seen, logical = set(), set()
    rests, exits, summaries = {}, {}, []
    current = cold
    stop = None
    for index, event in enumerate(trace.get('events', [])):
        need(isinstance(event, dict), 'B event must be an object')
        need(stop is None, 'action/event after failed or unknown action; diagnosis requires a new trace')
        kind = event.get('kind')
        need(kind in ('split', 'move', 'rest-enter', 'rest-exit', 'merge'), 'unknown B event kind')
        if kind in ('rest-enter', 'rest-exit'):
            view = observe(event['endpoint'], plan, evidence, rt)
            _passive_observation(current, view)
            aid, site = event['unit_id'], event['province_id']
            need(c.integer(aid) and c.integer(site), 'rest unit/site must be native integer IDs')
            need(phase == 'split' and aid in (main, child) and site in bp['rest_province_ids'],
                 'rest is outside the split unit/site plan')
            need(site == bp['rest_province_ids'][0 if aid == main else 1],
                 'rest site differs from frozen main/child assignment')
            _stationary(view, [aid], site)
            if kind == 'rest-enter':
                need(aid not in rests and site not in [v['site'] for v in rests.values()],
                     'rest unit/site duplicated')
                rests[aid] = {'site': site, 'day': view['endpoint']['day']}
            else:
                need(aid in rests and aid not in exits and rests[aid]['site'] == site,
                     'rest exit has no matching actual arrival')
                elapsed = view['endpoint']['day'] - rests[aid]['day']
                unit = next(u for u in view['endpoint']['units'] if u['army_id'] == aid)
                threshold = (unit['stock_raw'] >= bp['minimum_stock_raw'] and
                             unit['maximum_soldiers'] - unit['current_soldiers'] <= bp['maximum_deficit'])
                reason = event.get('reason')
                need(0 <= elapsed <= bp['maximum_rest_days'], 'rest exceeded frozen maximum')
                need((reason == 'threshold' and threshold) or
                     (reason == 'maximum_rest_days' and elapsed == bp['maximum_rest_days']),
                     'rest exit threshold/max-stay was not actually observed')
                exits[aid] = {'province_id': site, 'unit_id': aid, 'start_day': rests[aid]['day'],
                              'end_day': view['endpoint']['day'], 'reason': reason,
                              'endpoint_day': view['endpoint']['day']}
            current = view
            summaries.append({'kind': kind, 'state': _summary(view, plan)})
            continue
        before = observe(event['before'], plan, evidence, rt)
        _passive_observation(current, before)
        after = observe(event['after'], plan, evidence, rt) if event.get('after') else None
        if kind == 'split':
            need(phase == 'whole', 'split may be submitted once from the whole state')
            key = ('split', main)
        elif kind == 'merge':
            need(phase == 'split' and set(exits) == {main, child}, 'merge before both actual rest exits')
            key = ('merge', main, child)
        else:
            need(phase in ('split', 'merged'), 'B move before split')
            aid, target = event['unit_id'], event['target_province_id']
            need(c.integer(aid) and c.integer(target), 'move unit/target must be native integer IDs')
            if phase == 'split':
                need(aid in (main, child), 'move outside the actual split cohort')
                need(aid not in rests or aid in exits, 'move leaves rest before actual exit')
                expected = bp['merge_province_id'] if aid in exits else bp['rest_province_ids'][0 if aid == main else 1]
                need(target == expected, 'move target differs from frozen rest/meeting policy')
            else:
                need(target == plan['goal_province_id'], 'postmerge move must use frozen goal')
            key = ('move', event['unit_id'], event['target_province_id'])
        need(key not in logical, 'logical action was already attempted; no automatic retry')
        logical.add(key)
        step, action = _action(event, before, after, evidence, seen)
        if event['outcome'] != 'applied':
            stop = {'event_index': index, 'kind': kind, 'outcome': event['outcome'],
                    'retry_allowed': False, 'independent_post_state_present': after is not None}
            if after:
                current = after
            continue
        if kind == 'split':
            need(step == 'split-army-half-' + str(main), 'split request differs from actual main')
            need(set(before['rows']) == {main} and main in after['rows'] and len(after['rows']) == 2,
                 'split requires retained main plus one actual child')
            child = next(iter(set(after['rows']) - {main}))
            need(after['native'][main] == before['native'][main] and
                 after['native'][child] not in before['native'].values() and child not in before['positions'],
                 'child is not a new actual CArmy/public unit')
            need(set(after['positions']) == set(before['positions']) | {child},
                 'split roster has unexplained additional/removal rows')
            need(_integer_rows(before) == _integer_rows(after),
                 'split changed original regiment identities/current/max')
            _stationary(before, [main], before['positions'][main]['current_province_id'])
            _stationary(after, [main, child], before['positions'][main]['current_province_id'])
            phase = 'split'
        elif kind == 'merge':
            destination = event['destination_army_id']
            source = event['source_army_id']
            need(c.integer(destination) and c.integer(source), 'merge needs integer Army IDs')
            need({source, destination} == {main, child} and source != destination,
                 'merge participants differ from actual split')
            expected_destination = main if bp['merge_destination_policy'] == 'destination-main' else child
            need(destination == expected_destination, 'merge direction violates frozen destination policy')
            need(event.get('merge_destination_policy') == bp['merge_destination_policy'] and
                 event.get('commander_policy') == bp['commander_policy'], 'frozen merge/commander policy changed')
            need(step == 'merge-armies-' + str(destination) + '-with-' + str(source),
                 'merge command direction differs')
            _stationary(before, [main, child], bp['merge_province_id'])
            _stationary(after, [destination], bp['merge_province_id'])
            need(action.get('status') == 'merge_applied' and action.get('postcondition_verified') is True
                 and action.get('source_army_id_absent') is True, 'merge ACK lacks native postcondition')
            need(action.get('destination_army_id') == destination and action.get('source_army_id') == source,
                 'merge response participants differ')
            for field in ('date_raw', 'snapshot_id', 'native_revision', 'episode_run_id'):
                need(action.get('submitted_' + field) == before['snapshot'][field],
                     'merge receipt submitted frame differs: ' + field)
            need(action.get('submitted_public_revision') == before['snapshot']['revision'],
                 'merge receipt submitted public revision differs')
            need(action.get('observed_date_raw') == after['snapshot']['date_raw'] and
                 action.get('observed_episode_run_id') == after['snapshot']['episode_run_id'] and
                 c.integer(action.get('observed_native_revision')) and
                 before['snapshot']['native_revision'] < action['observed_native_revision'] <= after['snapshot']['native_revision'],
                 'merge receipt observed frame not bracketed by independent post-state')
            need(set(after['rows']) == {destination} and source not in after['positions'] and
                 after['native'][destination] == before['native'][destination],
                 'merge incomplete: source present or destination identity replaced')
            old, new = _integer_rows(before), _integer_rows(after)
            need(set(old) <= set(new) and all(new[k] == v for k, v in old.items()),
                 'no-tick merge lost/changed premerge integer regiment rows')
            # Extra actual records are strategy consequences, never deleted to
            # make the B arm resemble A/C. Their producer belongs to R09.
            phase = 'merged'
            main = destination
        else:
            aid, target = event['unit_id'], event['target_province_id']
            need(aid in before['rows'] and after['native'] == before['native'],
                 'move changed actual strategy Army identities')
            need(step == 'move-army-' + str(aid) + '-to-' + str(target), 'move request target differs')
            p = after['positions'][aid]
            pending = (p.get('move_target_province_id') == target and target in p.get('route_province_ids', []))
            complete = (p.get('current_province_id') == target and p.get('army_state') == 'regular'
                        and p.get('route_province_ids') == [] and p.get('move_target_province_id') is None)
            need(pending or complete, 'move ACK has no actual route/target/arrival post-state')
        current = after
        summaries.append({'kind': kind, 'state': _summary(current, plan)})
    complete = phase == 'merged' and stop is None
    return {'schema': 'xar.e04.r10.strategy-b-audit.v1', 'state': phase,
            'strategy_b_split_rest_merge_verified': complete, 'stop': stop,
            'B_rest_exit_records': sorted(exits.values(), key=lambda r: r['province_id']),
            'event_states': summaries, 'final_observation': _summary(current, plan),
            'next_operation': 'observe-final-route-and-daily-arrival' if complete else
                              'diagnose-without-resubmitting' if stop else 'continue-frozen-B-policy',
            'live_execution_performed': False, 'research_card_closed': False,
            'R09_mechanism_qualified': False, 'R10_comparison_qualified': False,
            'scope': 'Pinned supplied action/state consistency only. Does not grant causal mechanism, '
                     'complete daily clocks, first arrival, expense ledger, footage or live qualification.'}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', nargs='?', type=Path)
    p.add_argument('--plan', required=True, type=Path)
    p.add_argument('--arm', type=Path)
    p.add_argument('--plan-only', action='store_true')
    p.add_argument('--evidence-root', required=True, type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args(argv)
    try:
        plan_raw = input_bytes(a.plan)
        if a.plan_only:
            need(a.trace is None and a.arm is None, '--plan-only must not silently ignore trace/arm')
            out = recipe(c.parse(plan_raw), c.Evidence(a.evidence_root))
            code = 0
        else:
            need(a.trace is not None and a.arm is not None, 'event audit requires trace and --arm')
            trace = c.parse(input_bytes(a.trace))
            need(trace.get('plan_sha256') == c.digest(plan_raw), 'trace does not bind exact frozen plan bytes')
            out = audit(c.parse(plan_raw), c.parse(input_bytes(a.arm)), trace,
                        c.Evidence(a.evidence_root), plan_sha256=c.digest(plan_raw))
            code = 0 if out['strategy_b_split_rest_merge_verified'] else 2
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        out = {'accepted': False, 'reason': str(error), 'live_execution_performed': False}
        code = 2
    out['checked_at_utc'] = datetime.now(timezone.utc).isoformat()
    raw = json.dumps(out, ensure_ascii=False, indent=2) + '\n'
    if a.output:
        with a.output.open('x', encoding='utf-8', newline='\n') as f:
            f.write(raw)
    else:
        sys.stdout.write(raw)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
