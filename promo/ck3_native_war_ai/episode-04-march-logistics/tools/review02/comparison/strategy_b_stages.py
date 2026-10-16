"""Root-only staged B composition over the existing admitted file Relay.

Import/--help perform no relay requests. Ordinary stages never advance time, create a
session, run SDK, dispatch movement or infer native legality from capability ACK.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
LIMIT = 1024 * 1024


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def reviewed_module(path, name, sha256):
    path = Path(path)
    need(path.suffix == '.py' and path.stat().st_size <= 256 * 1024, 'reviewed bounded Python dependency required')
    need(hashlib.sha256(path.read_bytes()).hexdigest() == sha256, 'reviewed Python dependency SHA differs')
    return module(path, name)


class BStages:
    """Compose existing Relay primitives; every continuation supplies a state pin.

    root_module is the reviewed split_merge/root_relay.py module; relay is its
    admitted Relay instance. next_adapter is the reviewed strategy_b_next.py.
    State snapshots contain only small projections and exact original pins.
    """
    def __init__(self, root_module, relay, next_adapter, plan, *, plan_pin,
                 evidence, previous=None, previous_pin=None, s0_arm=None):
        self.r, self.live, self.next = root_module, relay, next_adapter
        self.plan, self.bp, self.evidence = plan, plan['strategies']['B'], evidence
        self.plan_pin = plan_pin
        self.s0_arm = s0_arm
        self.pending_packet = None
        self.code_pins = {'B_helper': self.r.pin(Path(__file__)),
            'root_helper': relay.meta.get('helper'),
            'next_adapter': self.r.pin(Path(next_adapter.__file__)) if getattr(next_adapter, '__file__', None) else None}
        self.dir = relay.case / 'B-stages'
        self.dir.mkdir(exist_ok=True)
        self.state = deepcopy(previous) if previous else {
            'schema': 'xar.e04.B.staged-relay-state.v1', 'phase': 'uninitialized',
            'machine_id': relay.meta['machine_id'], 'source_head': relay.meta['source_head'],
            'binding': deepcopy(relay.binding), 'plan': plan_pin, 'code_pins': self.code_pins,
            'main_id': None, 'child_id': None, 'rest_entries': {}, 'rest_exits': {},
            'latest_packet_refs': None, 'physical_refill': None,
            'live_B_comparison_qualified': False, 'research_card_closed': False}
        if previous:
            need(previous_pin is not None, 'continuation requires exact previous state pin')
            self.r.verify_pin(previous_pin)
            need(previous['machine_id'] == relay.meta['machine_id'] and previous['binding'] == relay.binding
                 and previous['source_head'] == relay.meta['source_head'] and previous['plan'] == plan_pin
                 and previous.get('code_pins') == self.code_pins,
                 'B continuation crossed machine/runtime/source/frozen policy')
            self.state['previous'] = previous_pin
        self.r.verify_pin(plan_pin)
        self.next.b.recipe(plan, evidence)
        need(plan['build']['source_head'] == relay.meta['source_head'], 'B frozen source differs from admitted actual Relay')
        # The original plan prerequisite pins and compare_fees scope remain in
        # force; no local relaxed policy, invented T0 or waived R07/R08 is made.
        need(self.bp['merge_destination_policy'] in ('destination-main', 'destination-child'),
             'concrete frozen merge direction required')

    def write(self, status, *, packet=None, **extra):
        if packet is not None:
            self.state['latest_packet_refs'] = packet['refs']
            self.state['latest_strategy_army_ids'] = packet.get('strategy_army_ids')
        value = {**deepcopy(self.state), 'status': status, 'observed_at_utc': self.r.utc(),
                 'stage': self.live.a.stage, 'time_advanced': False,
                 'SDK_connection_created': False, **extra}
        size = len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
        used = sum(p.stat().st_size for p in self.dir.iterdir() if p.is_file())
        need(used + size + 4096 <= LIMIT, 'B small stage ledger 1MiB limit reached; Root must retain exact state and stop expansion')
        return self.r.write_new(self.dir / (self.live.a.attempt + '.state.actual.json'), value)

    def full_packet(self, packet):
        """Hydrate source raw, not the small R09 DTO which omits stock/cap."""
        refs = packet['refs']
        raw_limit = self.evidence.file_limit(Path(refs['strength_raw']['path']))
        need(type(refs['strength_raw'].get('bytes')) is int and refs['strength_raw']['bytes'] <= raw_limit
             and Path(refs['strength_raw']['path']).stat().st_size == refs['strength_raw']['bytes'] <= raw_limit,
             'B Driver reference exceeds admitted input limit; stop before hash/read')
        for key in ('snapshot', 'strength_raw', 'same_frame_readback'):
            ref = refs[key]
            if key == 'strength_raw':
                self.r.verify_pin(ref)
            else:
                self.r.verify_pin(ref['response'])
        frame = self.r.load(refs['snapshot']['response']['path'])['body']
        self.r.validate_frame(frame, self.live.binding)
        self.r.same_frame(packet['frame'], frame)
        check = self.r.load(refs['same_frame_readback']['response']['path'])['body']
        self.r.same_frame(frame, check)
        query = self.r.load(refs['strength_raw']['path'], raw_limit)
        need(query.get('accepted') is True and query.get('status') == 'available', 'complete ordinary query unavailable')
        for qkey, skey in (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'),
                           ('queried_native_revision', 'native_revision'), ('queried_date_raw', 'date_raw'),
                           ('queried_episode_run_id', 'episode_run_id')):
            need(query.get(qkey) == frame.get(skey), 'B full query frame differs: ' + qkey)
        need(query.get('queried_connection_generation') == self.live.binding['generation'], 'query generation differs')
        scope = query.get('army_strengths_query_scope') or {}
        rows = query.get('army_strengths')
        selected = packet.get('strategy_army_ids') or self.strategy_ids()
        need(type(selected) is list and selected and len(set(selected)) == len(selected)
             and set(selected) <= set(self.r.roster(frame)), 'B selected scope is not in complete snapshot roster')
        need(type(rows) is list and scope.get('published_scope_status') == 'available'
             and set(scope.get('army_ids', [])) == set(selected), 'complete actual selected query scope missing')
        self.live.observation.compare_split_merge_cohorts(rows, rows)
        mapping = {r['army_id']: r for r in rows}
        need(len(mapping) == len(rows) and set(mapping) == set(selected), 'actual selected Army map incomplete')
        supply = {}
        for aid, row in mapping.items():
            resolution = row.get('native_army_resolution_v1') or {}
            need(resolution.get('status') == 'available' and resolution.get('ready') is True
                 and resolution.get('branch') == 'resolved'
                 and resolution.get('entry_full_id') == row.get('native_carmy_id'), 'actual CArmy generation unresolved')
            supply[aid] = {key: row.get(key) for key in ('current_supply_raw', 'current_supply_scale',
                'current_supply_capacity_raw', 'current_supply_capacity_scale')}
        assigned = {}
        for aid, row in mapping.items():
            response_pin = refs['commanders'][str(aid)]['response']
            self.r.verify_pin(response_pin)
            commander = self.r.load(response_pin['path'])['body']
            assigned[aid] = self.live.observation.read_bound_current_commander(commander, frame,
                army_id=aid, native_carmy_id=row['native_carmy_id'])
        return {'frame': frame, 'query': query, 'rows': mapping,
                'view': {'positions': self.r.roster(frame)}, 'supply': supply,
                'assigned_commanders': assigned, 'packet': packet}

    def strategy_ids(self):
        if self.state['phase'] == 'merged':
            return [self.state['surviving_army_id']]
        return sorted({i for i in (self.state.get('main_id') or self.live.a.army_id, self.state.get('child_id')) if i is not None})

    def observe(self, name, *, army_ids=None):
        packet = self.live.packet('B-' + name, army_ids=self.strategy_ids() if army_ids is None else army_ids,
                                  raw_file_limit=self.evidence.file_limit)
        self.pending_packet = packet
        return self.full_packet(packet)

    def prior_packet(self):
        refs = self.state['latest_packet_refs']
        need(refs is not None, 'B previous packet missing')
        # No directory latest/glob: read only the explicitly pinned original.
        frame = self.r.load(refs['snapshot']['response']['path'])['body']
        return self.full_packet({'frame': frame, 'refs': refs,
                                 'strategy_army_ids': self.state.get('latest_strategy_army_ids')})

    def horizon(self, frame):
        elapsed = frame['date_raw'] - self.plan['t0_raw']
        need(type(elapsed) is int and 0 <= elapsed <= 90 * 24, 'B actual date outside frozen absolute horizon')
        return elapsed == 90 * 24

    def baseline(self):
        need(self.state['phase'] == 'uninitialized', 'B baseline cannot reset a continuation')
        need(self.s0_arm is not None, 'same-S0 admission needs existing actual R10 B arm: runtime, loaded_save_sha256 and cold_start evidence; do not infer it from date alone')
        c = self.next.b.c
        self.next.b.audit(self.plan, self.s0_arm, {'schema': 'xar.e04.r10.strategy-b-events.v1',
            'plan_sha256': self.plan_pin['sha256'], 'events': []}, self.evidence,
            plan_sha256=self.plan_pin['sha256'])
        c.schema_check(self.s0_arm, 'arm')
        need(self.s0_arm['label'] == 'B' and self.s0_arm['loaded_save_sha256'] == self.plan['normal_save']['sha256'], 'actual B normal cold-load SHA differs from common S0')
        runtime = self.s0_arm['runtime']
        for field, key in (('pid', 'pid'), ('process_create_time_100ns', 'process_create_time_100ns'),
                           ('connection_generation', 'generation'), ('player_character_id', 'actor'), ('episode', 'episode')):
            need(runtime[field] == self.live.binding[key], 'B cold-load runtime differs: ' + field)
        need(runtime['machine_id'] == self.live.meta['machine_id'], 'B cold-load machine differs')
        expected = c.check_plan(self.plan, self.evidence)
        cold = c.endpoint(self.s0_arm['cold_start'], self.plan, self.evidence, runtime)
        need(cold == expected, 'actual independent cold S0 observables differ from frozen baseline')
        ref = self.live.baseline(strategy_scope=True, raw_file_limit=self.evidence.file_limit)
        saved = self.live.saved('baseline')
        current = self.full_packet(saved['packet'])
        need(current['frame']['date_raw'] == self.plan['t0_raw'], 'B did not cold-load the frozen common S0 date')
        main = saved['source_army_id']
        actual = current['rows'].get(main)
        need(actual is not None, 'frozen main not actually available')
        ids = {v['army_regiment_id'] for v in actual['regiment_strengths']}
        need(ids == set(self.plan['original_regiment_ids']) and actual['current_soldiers'] == expected['cohort_current']
             and actual['maximum_soldiers'] == expected['cohort_maximum'], 'B S0 original cohort differs')
        integers = sorted((v['army_regiment_id'], v['current_soldiers'], v['maximum_soldiers']) for v in actual['regiment_strengths'])
        frozen_integers = sorted((v['army_regiment_id'], v['current_soldiers'], v['maximum_soldiers']) for v in expected['cohort_regiments'])
        need(integers == frozen_integers, 'fresh S0 individual cached regiment rows differ')
        expected_unit = next((u for u in expected['units'] if u['army_id'] == main), None)
        need(expected_unit is not None, 'actual selected main is not the frozen S0 main')
        p = current['view']['positions'][main]
        for observed, frozen in ((p['current_province_id'], expected_unit['current_province_id']),
            (p['army_state'], expected_unit['state']), (p['route_province_ids'], expected_unit['route']),
            (p['move_target_province_id'], expected_unit['target']),
            (actual.get('current_supply_raw'), expected_unit['stock_raw']),
            (actual.get('current_supply_capacity_raw'), expected_unit['capacity_raw'])):
            need(observed == frozen, 'fresh baseline location/route/supply/capacity drifted from S0')
        need(current['frame'].get('active_wars') == expected['war_state']
             and current['frame'].get('played_character_gold', {}).get('raw') == expected['treasury_raw']
             and current['frame'].get('played_character_gold', {}).get('scale') == 100000, 'fresh baseline war/wallet differs from S0')
        need(sorted(actual['regiment_replenishment_records_v1'], key=lambda g: g['army_regiment_id']) == expected['DATA'], 'fresh baseline complete DATA differs from S0')
        assigned = self.live.observation.read_bound_current_commander(saved['packet']['commanders'][str(main)],
            current['frame'], army_id=main, native_carmy_id=actual['native_carmy_id'])
        need(assigned == expected['commander_id'], 'fresh baseline actual assigned commander differs from S0')
        self.state.update(phase='baseline', main_id=main)
        return self.write('BASELINE_READ_ONLY_OBSERVED', packet=saved['packet'], root_baseline=ref)

    def split_once(self):
        need(self.state['phase'] == 'baseline', 'B split requires frozen baseline stage')
        result = self.live.submit_once('split')
        self.state['phase'] = 'split-submitted'
        return self.write('SPLIT_SUBMITTED_NOT_POSTCONDITION', submission=result, native_legality_inferred_from_capability=False)

    def post_split(self):
        need(self.state['phase'] in ('baseline', 'split-submitted'), 'B split post-state requires original one-shot submission')
        result = self.live.post_split(strategy_scope=True, raw_file_limit=self.evidence.file_limit)
        saved = self.live.saved('post-split')
        need(saved['split_assertion']['accepted'] is True, 'fresh split transfer not accepted')
        self.full_packet(saved['packet'])
        self.state.update(phase='rest', child_id=saved['split_assertion']['identity']['sibling_army_id'])
        return self.write('FRESH_SPLIT_OBSERVED_REST_ROUTE_REQUIRED', packet=saved['packet'], root_post_split=result)

    def rest(self):
        need(self.state['phase'] in ('rest', 'meeting'), 'B rest observation requires actual split pair')
        current = self.observe('rest')
        if self.horizon(current['frame']):
            return self.write('HOLD_ABSOLUTE_DAY90_USE_COMPARISON_CONSUMER', packet=current['packet'])
        roles = list(zip((self.state['main_id'], self.state['child_id']), self.bp['rest_province_ids']))
        needs, waiting = [], []
        for aid, site in roles:
            key = str(aid)
            if key in self.state['rest_exits']:
                continue
            if not self.next._at(current['view'], aid, site):
                need(key not in self.state['rest_entries'], 'unexited rest Army left its frozen site; preserve policy deviation')
                needs.append(self.next._movement_dependency(current['view'], aid, site, 'rest'))
                continue
            entry = self.state['rest_entries'].setdefault(key, {
                'province_id': site, 'date_raw': current['frame']['date_raw'],
                'snapshot': current['packet']['refs']['snapshot']['response']})
            elapsed = current['frame']['date_raw'] - entry['date_raw']
            need(elapsed % 24 == 0 and elapsed >= 0, 'actual rest natural-day interval missing')
            days = elapsed // 24
            need(days <= self.bp['maximum_rest_days'], 'actual rest exceeded frozen maximum; preserve deviation')
            supply = current['supply'][aid]
            required = ['current_supply_raw', 'current_supply_scale', 'current_supply_capacity_raw', 'current_supply_capacity_scale']
            missing = [k for k in required if type(supply[k]) is not int]
            if missing or supply['current_supply_scale'] != 100000 or supply['current_supply_capacity_scale'] != 100000:
                needs.append({'status': 'HOLD_ACTUAL_SUPPLY_UNAVAILABLE', 'army_id': aid,
                    'required_fields': missing or required, 'tool': 'ck3_query_army_strengths',
                    'arguments': {'army_ids': [aid], 'expected_revision': current['frame']['revision'], 'profile': 'ordinary_core_v1'}})
                continue
            row = current['rows'][aid]
            threshold = (supply['current_supply_raw'] >= self.bp['minimum_stock_raw'] and
                         row['maximum_soldiers'] - row['current_soldiers'] <= self.bp['maximum_deficit'])
            reason = 'threshold' if threshold else 'maximum_rest_days' if days == self.bp['maximum_rest_days'] else None
            if reason:
                self.state['rest_exits'][key] = {'unit_id': aid, 'province_id': site,
                    'start_day': (entry['date_raw'] - self.plan['t0_raw']) // 24,
                    'end_day': (current['frame']['date_raw'] - self.plan['t0_raw']) // 24,
                    'endpoint_day': (current['frame']['date_raw'] - self.plan['t0_raw']) // 24,
                    'reason': reason, 'recovery_threshold_observed': threshold,
                    'stock_raw': supply['current_supply_raw'], 'capacity_raw': supply['current_supply_capacity_raw'],
                    'deficit': row['maximum_soldiers'] - row['current_soldiers'], 'proof': current['packet']['refs']}
            else:
                waiting.append({'army_id': aid, 'days_until_maximum': self.bp['maximum_rest_days'] - days,
                                'stock_raw': supply['current_supply_raw'], 'future_stock_change': None})
        if len(self.state['rest_exits']) == 2:
            self.state['phase'] = 'meeting'
            for aid, _ in roles:
                if not self.next._at(current['view'], aid, self.bp['merge_province_id']):
                    needs.append(self.next._movement_dependency(current['view'], aid, self.bp['merge_province_id'], 'meeting'))
        status = 'HOLD_ROUTE_OR_OBSERVATION_DEPENDENCY' if needs else 'HOLD_REST_UNTIL_ACTUAL_EXIT' if waiting else 'ACTUAL_MEETING_READY'
        return self.write(status, packet=current['packet'], dependencies=needs, waiting_armies=waiting,
                          B_rest_exit_records=list(self.state['rest_exits'].values()), time_advance_request=None)

    def merge_once(self):
        need(self.state['phase'] == 'meeting' and len(self.state['rest_exits']) == 2, 'B merge requires both actual rest exits')
        current = self.observe('meeting')
        need(not self.horizon(current['frame']), 'absolute horizon reached before B merge')
        ids = [self.state['main_id'], self.state['child_id']]
        if self.bp['merge_destination_policy'] == 'destination-child':
            ids.reverse()
        need(all(self.next._at(current['view'], aid, self.bp['merge_province_id']) for aid in ids), 'both armies must actually be stationary at frozen meeting site')
        step = 'merge-armies-' + str(ids[0]) + '-with-' + str(ids[1])
        gate = self.r.action_gate(current['frame'], current['packet']['capabilities'], step, 'merge', ids, self.live.binding['actor'])
        check, checkref = self.live.snapshot('B-merge-submit-frame')
        self.r.same_frame(current['frame'], check)
        claim_path = self.dir / 'merge.once.claim.json'
        arguments = {'step': step, 'expected_revision': check['revision']}
        identifier = self.live.a.attempt + '-' + str(self.live.serial + 1).zfill(3) + '-B-merge-once'
        claim = {'machine_id': self.live.meta['machine_id'], 'binding': self.live.binding, 'plan': self.plan_pin,
            'ids': ids, 'arguments': arguments, 'before_packet_refs': current['packet']['refs'], 'gate': gate,
            'pre_submit_readback': checkref, 'request_id': identifier,
            'request_path': str(self.live.run / 'requests' / (identifier + '.json')),
            'response_path': str(self.live.run / 'responses' / (identifier + '.json')),
            'retry_allowed': False, 'legality_from_capability': False}
        claim_pin = self.r.write_new(claim_path, claim)  # exclusive before any action
        row, refs = self.live.request('B-merge-once', 'ck3_execute_step', arguments)
        self.state.update(phase='merge-submitted', merge_claim=claim_pin)
        accepted = row.get('body', {}).get('accepted') is True and row.get('body', {}).get('step') == step
        receipt = self.write('MERGE_SUBMITTED_AWAIT_INDEPENDENT_POST' if accepted else 'HOLD_NATIVE_REJECTION_NO_RETRY',
                             packet=current['packet'], submission=refs, action_retry_allowed=False)
        return receipt

    def post_merge(self):
        need(self.state['phase'] in ('meeting', 'merge-submitted'), 'B merge post-state needs premerge state')
        claim_pin = self.state.get('merge_claim') or self.r.pin(self.dir / 'merge.once.claim.json')
        self.r.verify_pin(claim_pin)
        claim = self.r.load(claim_pin['path'])
        need(claim['binding'] == self.live.binding and claim['plan'] == self.plan_pin, 'B merge claim runtime/policy differs')
        request = self.r.load(claim['request_path'])
        need(request.get('request_id') == claim['request_id'] and request.get('arguments') == claim['arguments'], 'B original merge request differs')
        response = self.r.load(claim['response_path'])
        need(response.get('is_error') is False and response.get('body', {}).get('accepted') is True
             and response.get('body', {}).get('step') == claim['arguments']['step']
             and response.get('request', {}).get('request_id') == claim['request_id'], 'B original result unknown/rejected; read original only')
        before = self.full_packet({'frame': self.r.load(claim['before_packet_refs']['snapshot']['response']['path'])['body'],
                                   'refs': claim['before_packet_refs']})
        current = self.observe('post-merge', army_ids=[claim['ids'][0]])
        self.live.observation._fresh_pair(before['frame'], current['frame'])
        destination, source = claim['ids']
        need(set(self.r.roster(current['frame'])) == set(self.r.roster(before['frame'])) - {source}
             and set(current['rows']) == set(before['rows']) - {source} and destination in current['rows'],
             'actual B source removal is incomplete in selected query or complete snapshot roster')
        need(before['rows'][destination]['native_carmy_id'] == current['rows'][destination]['native_carmy_id'], 'B destination generation changed')
        old_position, new_position = before['view']['positions'][destination], current['view']['positions'][destination]
        need(new_position.get('owner_character_id') == self.live.binding['actor']
             and new_position.get('controllable') is True
             and new_position.get('current_province_id') == old_position.get('current_province_id'), 'merged B destination owner/control/site changed')
        unchanged = {'coverage': 'not_requested', 'only_strategy_cohort_audited': True,
                     'complete_snapshot_roster_retained': True}
        roles = self.r.compare_data_roles(self.live.consumer, [before['rows'][i] for i in claim['ids']], [current['rows'][destination]])
        need(roles['accepted'], 'actual B ordered/physical DATA changed or unexplained role transition; preserve original packet')
        self.state.update(phase='merged', surviving_army_id=destination)
        return self.write('ACTUAL_MERGE_POSTSTATE_OBSERVED_ROUTE_HANDOFF', packet=current['packet'], DATA_roles=roles,
                           unrelated_cohorts=unchanged,
                          assigned_commanders_before=before['assigned_commanders'], assigned_commanders_after=current['assigned_commanders'],
                          physical_refill=None, dynamic_video_qualified=False)

    def route(self):
        need(self.state['phase'] == 'merged', 'B final route needs verified actual merged state')
        current = self.observe('route')
        aid = self.state['surviving_army_id']
        supply = current['supply'][aid]
        if any(type(v) is not int for v in supply.values()):
            return self.write('HOLD_ACTUAL_SUPPLY_UNAVAILABLE', packet=current['packet'],
                              army_id=aid, required_fields=[k for k, v in supply.items() if type(v) is not int])
        dependency = None if self.next._at(current['view'], aid, self.plan['goal_province_id']) else self.next._movement_dependency(
            current['view'], aid, self.plan['goal_province_id'], 'goal')
        return self.write('ACTUAL_GOAL_STATE_USE_DAILY_COMPARISON' if dependency is None else 'HOLD_ROUTE_HANDOFF_REQUIRED',
                          packet=current['packet'], route_handoff=dependency, move_command=None,
                          absolute_deadline_raw=self.plan['t0_raw'] + 90 * 24, fees=None, loss_or_refill_cause=None)

    def common_horizon_stage(self, *, recovery=False):
        a = self.live.a
        need(a.common_horizon is not None and a.common_horizon_sha256
             and a.arrival_arm is not None and a.arrival_arm_sha256,
             'explicit reviewed common-horizon helper and actual arrival arm required')
        helper = reviewed_module(a.common_horizon, 'B_reviewed_common_horizon', a.common_horizon_sha256)
        self.common_horizon_pin = self.r.pin(a.common_horizon)
        arrival = self.r.pin(a.arrival_arm)
        need(arrival['sha256'] == a.arrival_arm_sha256, 'actual first-arrival arm pin differs')
        return helper.advance(self, arrival, a.days,
            recovery_start=a.day_start_raw if recovery else None)

    def run(self, stage):
        methods = {'baseline': self.baseline, 'split-once': self.split_once, 'post-split': self.post_split,
                   'rest': self.rest, 'merge-once': self.merge_once, 'post-merge': self.post_merge, 'route': self.route,
                   'advance-common-horizon': self.common_horizon_stage,
                   'recover-common-horizon-day': lambda: self.common_horizon_stage(recovery=True)}
        try:
            return methods[stage]()
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as error:
            return self.write('HOLD_STAGE_PREREQUISITE_OR_ORIGINAL_PENDING', packet=self.pending_packet,
                error_type=type(error).__name__, reason=str(error)[:3000], action_retry_allowed=False,
                instruction='Read original exact request/response and actual state; never remove one-shot claim or retry unknown action.')


def relay_arguments(args):
    """Keep the historical Relay defaults or forward one complete reviewed binding."""
    fields = ('source_head', 'run_sequence', 'module_pins', 'module_pins_sha256')
    present = [hasattr(args, name) for name in fields]
    if any(present):
        need(all(present), 'explicit Relay binding requires source-head, run-sequence, module-pins and module-pins-sha256 together')
        need(isinstance(args.source_head, str) and len(args.source_head) == 40
             and all(c in '0123456789abcdef' for c in args.source_head), 'exact lowercase source-head SHA required')
        need(type(args.run_sequence) is int and args.run_sequence >= 176, 'explicit allocated run sequence required')
        need(isinstance(args.module_pins_sha256, str) and len(args.module_pins_sha256) == 64
             and all(c in '0123456789abcdef' for c in args.module_pins_sha256), 'exact reviewed module-pins SHA required')
    result = deepcopy(args)
    result.self_sha256 = args.root_relay_sha256
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=('baseline', 'split-once', 'post-split', 'rest', 'merge-once', 'post-merge', 'route', 'advance-common-horizon', 'recover-common-horizon-day'))
    for name in ('repo', 'context', 'runtime-proof', 'request-helper', 'root-relay', 'next-adapter', 'plan', 'evidence-root'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('self-sha256', 'context-sha256', 'runtime-proof-sha256', 'request-helper-sha256',
                 'root-relay-sha256', 'next-adapter-sha256', 'plan-sha256', 'run-id', 'case-id', 'attempt'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--army-id', type=int, required=True)
    p.add_argument('--previous-state', type=Path)
    p.add_argument('--previous-state-sha256')
    p.add_argument('--s0-arm', type=Path)
    p.add_argument('--s0-arm-sha256')
    # Suppressed defaults preserve the historical R0176/dcda Relay scope. A new
    # source/run must supply the complete reviewed binding; never infer HEAD.
    p.add_argument('--source-head', default=argparse.SUPPRESS)
    p.add_argument('--run-sequence', type=int, default=argparse.SUPPRESS)
    p.add_argument('--module-pins', type=Path, default=argparse.SUPPRESS)
    p.add_argument('--module-pins-sha256', default=argparse.SUPPRESS)
    p.add_argument('--max-evidence-file-bytes', type=int, default=16 * 1024 * 1024)
    p.add_argument('--max-runtime-total-bytes', type=int, default=512 * 1024 * 1024)
    p.add_argument('--runtime-capacity-admission', nargs=2, metavar=('PATH', 'SHA256'))
    p.add_argument('--evidence-capacity-admission', nargs=2, metavar=('PATH', 'SHA256'), action='append', default=[])
    p.add_argument('--common-horizon', type=Path)
    p.add_argument('--common-horizon-sha256')
    p.add_argument('--arrival-arm', type=Path)
    p.add_argument('--arrival-arm-sha256')
    p.add_argument('--days', type=int, default=1)
    p.add_argument('--day-start-raw', type=int)
    a = p.parse_args(argv)
    base_args = relay_arguments(a)
    root = reviewed_module(a.root_relay, 'reviewed_r09_root_relay_for_B', a.root_relay_sha256)
    need(root.pin(Path(__file__))['sha256'] == a.self_sha256, 'reviewed B composer SHA differs')
    for path, expected in ((a.root_relay, a.root_relay_sha256), (a.next_adapter, a.next_adapter_sha256), (a.plan, a.plan_sha256)):
        need(root.pin(path)['sha256'] == expected, 'reviewed B dependency SHA differs: ' + str(path))
    sys.path[:0] = [str(a.repo / 'ck3_autonomous_player/src'), str(a.repo / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison')]
    next_adapter = reviewed_module(a.next_adapter, 'reviewed_B_next', a.next_adapter_sha256)
    # Policy/schema/evidence checks happen before constructing a live Relay.
    plan = root.load(a.plan)
    evidence = next_adapter.b.c.Evidence(a.evidence_root, max_file_bytes=a.max_evidence_file_bytes,
        capacity_admissions=[{'path': path, 'sha256': sha} for path, sha in a.evidence_capacity_admission],
        expected_source_head=plan['build']['source_head'], expected_machine_ids={root.MACHINE})
    next_adapter.b.recipe(plan, evidence)
    previous_pin = root.pin(a.previous_state) if a.previous_state else None
    if previous_pin:
        need(previous_pin['sha256'] == a.previous_state_sha256, 'previous B state SHA differs')
    previous = root.load(a.previous_state) if previous_pin else None
    if a.s0_arm:
        need(root.pin(a.s0_arm)['sha256'] == a.s0_arm_sha256, 'actual S0 B arm SHA differs')
    s0_arm = root.load(a.s0_arm) if a.s0_arm else None
    budget = next_adapter.b.c.runtime_total_budget(vars(a), scene_root=a.context.resolve().parent,
        source_head=plan['build']['source_head'], machine_id=root.MACHINE, deadline_utc=root.DEADLINE)
    live = root.Relay(base_args)
    budget.bind_live(live, raw_file_max=a.max_evidence_file_bytes)
    stages = BStages(root, live, next_adapter, plan, plan_pin=root.pin(a.plan), evidence=evidence,
                     previous=previous, previous_pin=previous_pin, s0_arm=s0_arm)
    result = stages.run(a.stage)
    print(json.dumps(result, ensure_ascii=False))
    return 2 if root.load(result['path'])['status'].startswith('HOLD_') else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'status': 'HOLD_MISSING_OR_INCONSISTENT_STAGE_INPUT',
            'error_type': type(error).__name__, 'reason': str(error)[:3000],
            'action_retry_allowed': False, 'instruction': 'Inspect exact originals; do not delete claims or infer action outcome.'}))
        raise SystemExit(2)
