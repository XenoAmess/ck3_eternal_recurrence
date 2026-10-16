"""Explicit post-arrival B clock composition; no SDK or military commands.

Root supplies an exact actual arrived arm and a reviewed existing BStages.
Linked day receipts retain original claims, first arrival and every raw pin.
This is an execution adapter, never an R10 result or causal ledger qualifier.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
POLICY = 'hold-arrival-position-until-day90'
LIMIT = 1024 * 1024
def need(ok, why):
	if not ok:
		raise ValueError(why)
def signature(view):
	"""Identity/max/order only; current soldiers, stock and wallet may change."""
	rows = []
	for aid, row in sorted(view['rows'].items()):
		cached = [(r['army_regiment_id'], r['maximum_soldiers']) for r in row['regiment_strengths']]
		groups = []
		for g in row['regiment_replenishment_records_v1']:
			records = []
			for r in g['records']:
				pid = r['persistent_regiment_id']
				need(type(pid) is int and -(2**31) <= pid < 2**31, 'typed signed persistent FullID required')
				vals = [r[k] for k in ('record_index', 'chunk_index', 'maximum_soldiers', 'chunk_army_regiment_id')]
				need(all(type(x) is int and 0 <= x < 2**31 for x in vals[:3])
					and type(vals[3]) is int and -(2**31) <= vals[3] < 2**31, 'typed DATA index/slot/max and signed association required')
				records.append([vals[0], pid, *vals[1:]])
			groups.append([g['army_regiment_id'], g['native_data_record_count'], records])
		rows.append([aid, row['native_carmy_id'], cached, groups])
	ep = view['endpoint']
	return hashlib.sha256(json.dumps([rows, ep['commander_id'], ep['player_character_id'],
		ep['cohort_maximum'], ep['loaded_features'], ep['war_state']], sort_keys=True,
		separators=(',', ':')).encode()).hexdigest()
def relative(st, ref):
	p = Path(ref['path']).resolve()
	need(p.is_relative_to(st.evidence.root), 'actual source must be within explicit evidence root')
	value = {'path': p.relative_to(st.evidence.root).as_posix(), 'bytes': ref['bytes'], 'sha256': ref['sha256']}
	st.evidence.raw(value)
	return value
def load(st, ref):
	st.r.verify_pin(ref)
	return st.r.load(ref['path'])
def store(st, name, value):
	value = {'machine_id': st.live.meta['machine_id'], 'source_head': st.live.meta['source_head'],
			 'binding': st.live.binding, 'plan': st.plan_pin,
			 'observed_at_utc': datetime.now(timezone.utc).isoformat(), **value}
	raw = (json.dumps(value, ensure_ascii=False) + '\n').encode()
	used = sum(p.stat().st_size for p in st.dir.iterdir() if p.is_file())
	need(used + len(raw) + 32768 <= LIMIT, 'B existing 1MiB ledger cannot admit more linked evidence')
	return st.r.write_new(st.dir / name, value)
def endpoint(st, current, features):
	aid = st.state['surviving_army_id']; refs = current['packet']['refs']
	elapsed = current['frame']['date_raw'] - st.plan['t0_raw']
	need(type(elapsed) is int and 0 <= elapsed <= 2160 and elapsed % 24 == 0, 'actual common horizon date required')
	ep = {'day': elapsed // 24, 'snapshot': relative(st, refs['snapshot']['response']),
		  'army_result': relative(st, refs['strength_raw']), 'strategy_army_ids': [aid],
		  'commander': {'source': relative(st, refs['commanders'][str(aid)]['response']),
						'pointer': '/body/army_commander_candidates/current_commander/character_id'},
		  'loaded_features': features}
	view = st.next._view(ep, st.plan, st.evidence, st.runtime)
	need(st.next.b.c.arrived(view['endpoint'], st.plan), 'actual B left frozen goal/state/empty route')
	p = view['positions'][aid]
	need(p.get('controllable') is True and p.get('in_combat') is False and p.get('retreating') is False,
		 'combat/retreat/control interruption; preserve actual day without qualification')
	return ep, view
def admission(st, arm_ref):
	c = st.next.b.c; arm = load(st, arm_ref); plan = st.plan
	need(plan.get('status') == 'frozen' and plan.get('follow_after_arrival_to_day90') is True
		 and plan.get('post_arrival_policy') == POLICY, 'explicit frozen common-horizon policy required')
	c.schema_check(arm, 'arm'); rt = arm['runtime']; c.schema_check(rt, 'runtime')
	frozen = datetime.fromisoformat(plan['frozen_at_utc'].replace('Z', '+00:00'))
	started = datetime.fromisoformat(rt['started_at_utc'].replace('Z', '+00:00'))
	need(frozen.tzinfo is not None and started.tzinfo is not None and frozen < started, 'policy must predate runtime')
	need(arm['label'] == 'B' and arm['loaded_save_sha256'] == plan['normal_save']['sha256']
		 and rt['source_head'] == plan['build']['source_head'] == st.live.meta['source_head']
		 and rt['native_dll_sha256'] == plan['build']['native_dll_sha256']
		 and rt['machine_id'] == st.live.meta['machine_id'], 'B common T0/source/DLL/machine differs')
	for name, key in (('pid','pid'), ('process_create_time_100ns','process_create_time_100ns'),
					  ('connection_generation','generation'), ('player_character_id','actor'), ('episode','episode')):
		need(rt[name] == st.live.binding[key], 'B current runtime differs: ' + name)
	st.runtime = rt
	need(st.state['phase'] == 'merged', 'only actual merged B may continue arrival hold')
	need(c.endpoint(arm['cold_start'], plan, st.evidence, rt) == c.check_plan(plan, st.evidence), 'independent common cold T0 differs')
	days = c.clock_days(arm, plan, st.evidence); dis = arm['disposition']
	need(dis['kind'] == 'arrived' and days['count'] == dis['day'] == days['first_arrival'], 'actual original first arrival with exact daily chain required')
	obs = {x['day']: x for x in [arm['cold_start'], *arm['observations']]}
	lower = dis['last_not_arrived_day']; first = obs[dis['day']]
	need(type(lower) is int and 0 <= lower < dis['day'] and dis['day'] - lower <= 1
		 and lower in obs and not c.arrived(c.endpoint(obs[lower], plan, st.evidence, rt), plan), 'actual <=1 day arrival bracket required')
	need(first['strategy_army_ids'] == [st.state['surviving_army_id']], 'actual survivor scope differs')
	view = st.next._view(first, plan, st.evidence, rt)
	need(c.arrived(view['endpoint'], plan), 'original endpoint is not an actual arrival')
	old = st.state.get('common_horizon')
	common = deepcopy(old) if old else {'arrival_arm': arm_ref, 'first_arrival_day': dis['day'],
		'first_arrival_endpoint': first, 'last_day': dis['day'], 'last_endpoint': first,
		'last_complete': None, 'fingerprint': signature(view), 'helper': st.common_horizon_pin}
	need(common['arrival_arm'] == arm_ref and common['first_arrival_day'] == dis['day']
		 and common['first_arrival_endpoint'] == first and common['fingerprint'] == signature(view)
		 and common['helper'] == st.common_horizon_pin,
		 'original first arrival or common cohort changed')
	extra = []; ref = common['last_complete']; seen = set()
	while ref:
		need(ref['path'] not in seen and len(extra) < 90, 'common day link duplicate/overflow')
		seen.add(ref['path']); item = load(st, ref)
		need(item.get('qualified') is True and item['binding'] == st.live.binding
			 and item['plan'] == st.plan_pin and item['arrival_arm'] == arm_ref, 'common day link is not qualified/bound')
		extra.append(item['day']); ref = item['previous_complete']
	arm = deepcopy(arm); arm['days'].extend(reversed(extra))
	checked = c.clock_days(arm, plan, st.evidence)
	need(checked['count'] == common['last_day'] and checked['first_arrival'] == dis['day'], 'linked exact-day history differs')
	return arm, common
def advance(st, arm_ref, days=1, *, recovery_start=None):
	need(type(days) is int and 1 <= days <= 30, 'bounded common-horizon stage1..30 required')
	arm, common = admission(st, arm_ref)
	need(common['last_day'] < 90, 'actual D90 reached; no further request')
	for _ in range(min(days, 90 - common['last_day'])):
		start = st.plan['t0_raw'] + 24 * common['last_day']; target = start + 24
		name = 'common-day-' + str(start); claim_path = st.dir / (name + '.once.claim.json')
		if recovery_start is not None:
			need(recovery_start == start and days == 1, 'recovery binds exactly original next day')
			claim_ref = st.r.pin(claim_path); claim = load(st, claim_ref)
			need(claim['before_common'] == common and claim['binding'] == st.live.binding
				 and claim['plan'] == st.plan_pin, 'original day claim differs')
			for action in ('arm', 'resume'):
				req = st.r.load(claim[action]['request_path']); res = st.r.load(claim[action]['response_path'])
				need(req.get('request_id') == claim[action]['request_id'] and req.get('arguments') == claim[action]['arguments']
					 and req.get('tool') == 'ck3_execute_step' and res.get('is_error') is False
					 and res.get('request', {}).get('request_id') == req['request_id'], 'original action missing/rejected; never replay')
			armed = st.r.load(claim['arm']['response_path'])['body'].get('tactical_daily_sentinel', {})
			resume = st.r.load(claim['resume']['response_path'])['body']
			need(armed.get('state') == 'armed' and resume.get('accepted') is True
				 and resume.get('step') == 'resume-map', 'original Arm/Resume unconfirmed; never replay')
		else:
			need(not claim_path.exists(), 'one-day claim already exists; read original only, never rearm/resume')
			current = st.observe('common-horizon-before'); before, view = endpoint(st, current, common['last_endpoint']['loaded_features'])
			need(before['day'] == common['last_day'] and signature(view) == common['fingerprint'], 'current same-cohort/date/commander gate failed')
			need(current['frame'].get('speed') == 5, 'actual speed5 required before claim; Root may explicitly set and observe')
			step = f'research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-5-mode-terminal-a-0'
			claim = {'arrival_arm': arm_ref, 'before_common': common, 'before': before}
			for offset, action, suffix, args in ((1,'arm','B-common-arm',{'step':step,'expected_revision':current['frame']['revision']}),
					(2,'resume','B-common-resume',{'step':'resume-map','expected_revision':None})):
				rid = st.live.a.attempt + '-' + str(st.live.serial + offset).zfill(3) + '-' + suffix
				claim[action] = {'request_id':rid,'request_path':str(st.live.run/'requests'/(rid+'.json')),
					'response_path':str(st.live.run/'responses'/(rid+'.json')),'arguments':args}
			claim_ref = store(st, claim_path.name, claim)
			row, _ = st.live.request('B-common-arm', 'ck3_execute_step', claim['arm']['arguments'])
			armed = row['body'].get('tactical_daily_sentinel', {})
			need(armed.get('state') == 'armed', 'Arm unknown; retain claim, no retry')
			st.live.request('B-common-resume', 'ck3_execute_step', claim['resume']['arguments'])
		record = {'arrival_arm': arm_ref, 'previous_complete': common['last_complete'], 'claim': claim_ref,
				  'qualified': False, 'day': None, 'after': None}
		try:
			for _poll in range(60):
				time.sleep(.15)
				value, _ = st.live.request('B-common-wait', 'ck3_take_snapshot', {'include_native_command_history':False})
				frame = value['body']; fence = dict(frame, paused=True)
				st.r.validate_frame(fence, st.live.binding)
				need(type(frame.get('paused')) is bool and start <= frame['date_raw'] <= target, 'unpaused clock date/runtime fence failed')
				if frame['paused'] and frame['date_raw'] > start:
					break
			need(frame['paused'] is True and frame['date_raw'] == target, 'exact +24 independent pause not observed')
			status, refs = st.live.request('B-common-status', 'ck3_execute_step', {'step':'research-query-tactical-daily-sentinel-v1','expected_revision':None})
			clock = status['body'].get('tactical_daily_sentinel', {})
			need(type(armed.get('generation')) is int and clock.get('generation') == armed['generation'], 'original Arm/Status generation differs')
			current = st.observe('common-horizon-after'); after, view = endpoint(st, current, common['last_endpoint']['loaded_features'])
			day = {'day':after['day'],'clock_source':relative(st, refs['response']),
				   'paused_snapshot':after['snapshot'],'strategy_army_ids':after['strategy_army_ids']}
			record.update(day=day, after=after)
			candidate = deepcopy(arm); candidate['days'].append(day)
			result = st.next.b.c.clock_days(candidate, st.plan, st.evidence)
			need(after['day'] == common['last_day'] + 1 and result['count'] == after['day']
				 and result['first_arrival'] == common['first_arrival_day'] and signature(view) == common['fingerprint'],
				 'actual day/cohort/native Army/commander fence failed')
			record['qualified'] = True
		except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
			record['error'] = str(error)[:2000]
			store(st, name + '.interrupted.actual.json', record)
			raise
		link = store(st, name + '.complete.actual.json', record)
		arm = candidate; common.update(last_day=after['day'], last_endpoint=after, last_complete=link)
		st.state['common_horizon'] = deepcopy(common)
	return st.write('ACTUAL_COMMON_HORIZON_DAY90_OBSERVED' if common['last_day'] == 90 else 'ACTUAL_COMMON_HORIZON_CONTINUATION_OBSERVED',
		first_arrival_unchanged=True, common_horizon=common, time_advanced=True,
		full_ABC_qualification=False, military_command_submitted=False)
