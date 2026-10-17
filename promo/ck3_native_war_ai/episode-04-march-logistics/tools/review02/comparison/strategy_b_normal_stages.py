"""Root-only frozen B movement and one normal date day; import is offline."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import time


def need(ok, why):
    if not ok:
        raise ValueError(why)


def targets(st):
    phase = st.state['phase']
    if phase == 'rest':
        return {aid: site for aid, site in zip((st.state['main_id'], st.state['child_id']), st.bp['rest_province_ids'])
                if str(aid) not in st.state['rest_exits']}
    if phase == 'meeting':
        need(len(st.state['rest_exits']) == 2, 'both frozen rest exits required')
        return {aid: st.bp['merge_province_id'] for aid in st.strategy_ids()}
    need(phase == 'merged', 'normal movement/day requires actual split pair or verified merge')
    return {st.state['surviving_army_id']: st.plan['goal_province_id']}


def signature(current):
    rows = []
    for aid, row in sorted(current['rows'].items()):
        cached = [(r['army_regiment_id'], r['maximum_soldiers']) for r in row['regiment_strengths']]
        groups = [(g['army_regiment_id'], g['native_data_record_count'],
                   [[r[k] for k in ('record_index', 'persistent_regiment_id', 'chunk_index', 'maximum_soldiers', 'chunk_army_regiment_id')]
                    for r in g['records']]) for g in row['regiment_replenishment_records_v1']]
        rows.append([aid, row['native_carmy_id'], cached, groups])
    return hashlib.sha256(json.dumps([rows, current['assigned_commanders']], sort_keys=True).encode()).hexdigest()


def endpoint(st, current):
    need(st.s0_arm is not None, 'actual pinned B cold-load arm required for normal-day runtime')
    rt = st.s0_arm['runtime']
    need(rt['source_head'] == st.plan['build']['source_head'] == st.live.meta['source_head']
         and rt['machine_id'] == st.live.meta['machine_id'], 'normal-day source/machine differs')
    for name, key in (('pid', 'pid'), ('process_create_time_100ns', 'process_create_time_100ns'),
                      ('connection_generation', 'generation'), ('player_character_id', 'actor'), ('episode', 'episode')):
        need(rt[name] == st.live.binding[key], 'normal-day runtime differs: ' + name)
    def relative(ref):
        path = Path(ref['path']).resolve()
        need(path.is_relative_to(st.evidence.root), 'endpoint original is outside evidence root')
        out = {'path': path.relative_to(st.evidence.root).as_posix(), 'bytes': ref['bytes'], 'sha256': ref['sha256']}
        st.evidence.raw(out)
        return out
    refs = current['packet']['refs']; ids = sorted(current['rows'])
    commander_aid = st.state['surviving_army_id'] if st.state['phase'] == 'merged' else st.state['main_id']
    elapsed = current['frame']['date_raw'] - st.plan['t0_raw']
    need(type(elapsed) is int and 0 <= elapsed <= 2160 and elapsed % 24 == 0, 'actual absolute natural day required')
    ep = {'day': elapsed // 24, 'snapshot': relative(refs['snapshot']['response']),
          'army_result': relative(refs['strength_raw']), 'strategy_army_ids': ids,
          'commander': {'source': relative(refs['commanders'][str(commander_aid)]['response']),
                        'pointer': '/body/army_commander_candidates/current_commander/character_id'},
          'loaded_features': st.s0_arm['cold_start']['loaded_features']}
    st.next._view(ep, st.plan, st.evidence, rt)
    return ep


def store(st, name, value):
    return st.r.write_new(st.dir / name, {'machine_id': st.live.meta['machine_id'],
        'source_head': st.live.meta['source_head'], 'binding': st.live.binding,
        'plan': st.plan_pin, 'helper': st.normal_stages_pin, **value})


def request_claim(st, suffix, arguments, *, tool='ck3_execute_step', offset=1):
    rid = st.live.a.attempt + '-' + str(st.live.serial + offset).zfill(3) + '-' + suffix
    return {'request_id': rid, 'tool': tool, 'arguments': arguments,
            'request_path': str(st.live.run / 'requests' / (rid + '.json')),
            'response_path': str(st.live.run / 'responses' / (rid + '.json'))}


def original(st, action):
    req = st.r.load(action['request_path']); row = st.r.load(action['response_path'])
    need(req.get('request_id') == action['request_id'] and req.get('tool') == action['tool']
         and req.get('arguments') == action['arguments'] and row.get('is_error') is False
         and row.get('request', {}).get('request_id') == action['request_id']
         and row.get('machine_id') == st.live.meta['machine_id'], 'original result pending/foreign; never replay')
    return row['body']


def move(st, aid, *, post=False):
    goal = targets(st); need(aid in goal, 'explicit Army must be a current frozen B role')
    target = goal[aid]; key = f"normal-move-{st.state['phase']}-{aid}"
    path = st.dir / (key + '.once.claim.json')
    if post:
        ref = st.r.pin(path); st.r.verify_pin(ref); claim = st.r.load(path)
        need(claim['binding'] == st.live.binding and claim['plan'] == st.plan_pin and claim['helper'] == st.normal_stages_pin
             and claim['army_id'] == aid and claim['target'] == target, 'original movement binding differs')
        body = original(st, claim['action'])
        need(body.get('accepted') is True, 'native Move rejected/unknown; no replay')
        current = st.observe('normal-move-post')
        p = current['view']['positions'][aid]
        need(current['frame']['date_raw'] == claim['date_raw'] and signature(current) == claim['signature'], 'Move post-state crossed date/cohort/native generation/commander')
        need(st.next._at(current['view'], aid, target) or
             (p.get('route_read_status') == 'complete_nonempty' and p.get('route_province_ids') == claim['route']
              and p.get('move_target_province_id') == target), 'actual stored route does not match original preview')
        st.state.pop('normal_move_pending', None)
        return st.write('ACTUAL_FROZEN_STAGE_ROUTE_OBSERVED', packet=current['packet'], move_claim=ref, move_reissued=False)
    need(not path.exists() and not st.state.get('normal_move_pending'), 'Move already claimed/pending; use original post-state, never replay')
    current = st.observe('normal-move-before'); need(not st.horizon(current['frame']), 'absolute D90 reached')
    if st.next._at(current['view'], aid, target):
        return st.write('ACTUAL_FROZEN_STAGE_LOCATION_ALREADY_OBSERVED', packet=current['packet'], move_submitted=False)
    p = current['view']['positions'][aid]
    need(p.get('owner_character_id') == st.live.binding['actor'] and p.get('controllable') is True
         and p.get('in_combat') is False and p.get('retreating') is False, 'actual B Army cannot move now')
    step = f'preview-move-army-{aid}-to-{target}'
    row, preview_ref = st.live.request('B-normal-preview', 'ck3_execute_step', {'step': step, 'expected_revision': current['frame']['revision']})
    body = row['body']; preview = body.get('route_preview') or {}; frame = current['frame']
    need(body.get('accepted') is True and preview.get('status') == 'available'
         and preview.get('army_id') == aid and preview.get('origin_province_id') == p['current_province_id']
         and preview.get('target_province_id') == target and preview.get('previewed_date_raw') == frame['date_raw'], 'native preview scope/rejection differs')
    for key, actual in (('snapshot_id', frame['snapshot_id']), ('revision', frame['revision']),
                        ('native_revision', frame['native_revision']), ('connection_generation', st.live.binding['generation']),
                        ('episode_run_id', frame['episode_run_id'])):
        need(body.get('queried_' + key) == actual, 'native preview frame differs: ' + key)
    route = deepcopy(preview.get('route_province_ids'))
    need(type(route) is list and route and all(type(x) is int and x > 0 for x in route), 'complete native route required')
    if route[0] == p['current_province_id']: route = route[1:]
    need(route and route[-1] == target, 'native preview misses frozen target')
    check, check_ref = st.live.snapshot('B-normal-move-submit'); st.r.same_frame(frame, check)
    args = {'army_id': aid, 'target_province_id': target, 'expected_revision': check['revision']}
    action = request_claim(st, 'B-normal-move', args, tool='ck3_move_army')
    claim = store(st, path.name, {'army_id': aid, 'target': target, 'date_raw': frame['date_raw'],
        'route': route, 'signature': signature(current), 'preview': preview_ref, 'before': current['packet']['refs'],
        'submit_snapshot': check_ref, 'action': action, 'retry_allowed': False})
    st.state['normal_move_pending'] = claim
    row, refs = st.live.request('B-normal-move', 'ck3_move_army', args)
    return st.write('MOVE_SUBMITTED_AWAIT_INDEPENDENT_STAGE_POST', packet=current['packet'], claim=claim, submission=refs,
                    native_accepted=row.get('body', {}).get('accepted') is True, move_reissued=False)


def day(st, *, recovery=False):
    targets(st); need(not st.state.get('normal_move_pending'), 'observe original Move post-state before a normal day')
    nd = getattr(st, 'normal_clock_adapter', None)
    if nd is None:
        from xar_autoplayer.bridge import native_driver as nd
    start = st.live.a.day_start_raw if recovery else None
    if recovery:
        need(type(start) is int, 'explicit original day start required for read-only recovery')
        claim_ref = st.r.pin(st.dir / f'normal-day-{start}.once.claim.json'); claim = st.r.load(claim_ref['path'])
        need(claim['binding'] == st.live.binding and claim['plan'] == st.plan_pin
             and claim['helper'] == st.normal_stages_pin, 'original normal-day binding differs')
        armed_body = original(st, claim['arm']); resume = original(st, claim['resume'])
        need(resume.get('accepted') is True and resume.get('step') == 'resume-map', 'original Resume unconfirmed; never replay')
    else:
        current = st.observe('normal-day-before'); before = endpoint(st, current)
        need(before['day'] == st.state.get('normal_last_day', 0) and not st.horizon(current['frame']), 'normal-day chain must remain contiguous from common T0')
        goals = targets(st)
        for aid, site in goals.items():
            if not st.next._at(current['view'], aid, site):
                p = current['view']['positions'][aid]
                need(p.get('move_target_province_id') == site and p.get('route_read_status') == 'complete_nonempty', 'submit and observe frozen stage route first')
        if st.state['phase'] == 'merged':
            need(not all(st.next._at(current['view'], aid, site) for aid, site in goals.items()), 'already at goal; use actual arrival arm and common-horizon stage')
        elif st.state['phase'] == 'meeting':
            need(not all(st.next._at(current['view'], aid, site) for aid, site in goals.items()), 'meeting reached; merge before advancing')
        else:
            for aid, site in goals.items():
                if st.next._at(current['view'], aid, site):
                    entry = st.state['rest_entries'].get(str(aid)); supply = current['supply'][aid]; row = current['rows'][aid]
                    need(entry is not None and current['frame']['date_raw'] - entry['date_raw'] < 24 * st.bp['maximum_rest_days']
                         and not (supply['current_supply_raw'] >= st.bp['minimum_stock_raw'] and row['maximum_soldiers'] - row['current_soldiers'] <= st.bp['maximum_deficit']), 'observe frozen rest entry/exit before advancing')
                else:
                    p = current['view']['positions'][aid]
                    need(p.get('move_target_province_id') == site and p.get('route_read_status') == 'complete_nonempty', 'submit and observe frozen rest route first')
        need(current['frame'].get('speed') == 5, 'actual speed5 required; Root may set and independently observe')
        start = current['frame']['date_raw']; target = start + 24
        path = st.dir / f'normal-day-{start}.once.claim.json'
        need(not path.exists(), 'normal day already claimed; recover original only')
        step = f'research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-5-mode-terminal-a-0'
        arm = request_claim(st, 'B-normal-arm', {'step': step, 'expected_revision': current['frame']['revision']})
        resume = request_claim(st, 'B-normal-resume', {'step': 'resume-map', 'expected_revision': None}, offset=2)
        claim = {'arm': arm, 'resume': resume, 'before': before, 'start': start, 'target': target,
                 'signature': signature(current), 'previous_complete': st.state.get('normal_last_complete'), 'retry_allowed': False}
        claim_ref = store(st, path.name, claim)
        st.state['normal_pending_day'] = claim_ref
        row, _ = st.live.request('B-normal-arm', 'ck3_execute_step', arm['arguments']); armed_body = row['body']
    target = start + 24; armed = nd._normalize_tactical_daily_sentinel_status(armed_body['tactical_daily_sentinel'])
    nd._validate_tactical_daily_sentinel_arm(armed_body, armed, arm_step=claim['arm']['arguments']['step'],
        starting_date_raw=start, target_date_raw=target, speed=5, mode='terminal_or_sentinel', watch_army_ids=(), sentinel_scope='exact_one_day')
    if not recovery:
        st.live.request('B-normal-resume', 'ck3_execute_step', claim['resume']['arguments'])
    for _ in range(60):
        time.sleep(.15)
        value, _ = st.live.request('B-normal-wait', 'ck3_take_snapshot', {'include_native_command_history': False})
        frame = value['body']; st.r.validate_frame(dict(frame, paused=True), st.live.binding)
        need(type(frame.get('paused')) is bool and start <= frame['date_raw'] <= target, 'normal-day runtime/date fence failed')
        if frame['paused'] and frame['date_raw'] > start: break
    need(frame['paused'] is True and frame['date_raw'] == target, 'exact normal day not independently paused; preserve original Arm/Resume')
    status, refs = st.live.request('B-normal-clock-status', 'ck3_execute_step', {'step': 'research-query-tactical-daily-sentinel-v1', 'expected_revision': None})
    clock = nd._normalize_tactical_daily_sentinel_status(status['body']['tactical_daily_sentinel'])
    current = st.observe('normal-day-after'); after = endpoint(st, current)
    nd._validate_tactical_daily_sentinel_stop(clock, arm_status=armed, starting_date_raw=start, target_date_raw=target,
        ending_date_raw=current['frame']['date_raw'], elapsed_days=1, speed=5, mode='terminal_or_sentinel', watch_army_ids=())
    need(clock['generation'] > st.state.get('normal_last_generation', 0) and signature(current) == claim['signature'], 'normal-day generation/cohort/native Army/max/order/commander changed')
    def relative(ref):
        path = Path(ref['path']).resolve(); need(path.is_relative_to(st.evidence.root), 'clock original outside evidence root')
        return {'path': path.relative_to(st.evidence.root).as_posix(), 'bytes': ref['bytes'], 'sha256': ref['sha256']}
    record = {'day': after['day'], 'clock_source': relative(refs['response']), 'paused_snapshot': after['snapshot'], 'strategy_army_ids': after['strategy_army_ids']}
    complete = store(st, f'normal-day-{start}.complete.actual.json', {'claim': claim_ref, 'before': claim['before'], 'after': after,
        'day': record, 'previous_complete': claim['previous_complete'], 'qualified': True})
    st.state.update(normal_last_day=after['day'], normal_last_generation=clock['generation'], normal_last_complete=complete)
    st.state.pop('normal_pending_day', None)
    return st.write('ACTUAL_NORMAL_STAGE_DAY_OBSERVED', packet=current['packet'], normal_day=record, normal_day_complete=complete,
                    time_advanced=True, military_command_submitted=False, full_ABC_qualification=False)
