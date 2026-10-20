"""R04 direct county-owner observation on the original public CaseClient.

No host, SDK, game launch, fixture, camera or alternate runtime is constructed.
The public Selection owns normal game closure, including failed observations.
"""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import copy
import hashlib
import json
import math
import os
import subprocess
import time

from .r10_prepare_adapter import need, pin, small_json
from . import r04_county_entry_window as window
from ck3_mod_acceptance_camera import camera_paths

def inventory(row):
    from xar_autoplayer.bridge.army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
    records = normalize_regiment_replenishment_records_v1(row.get('regiment_replenishment_records_v1'))
    need(len(records) == row['regiment_count'] and all((r['ready'] for r in records)), 'complete ordered DATA roster unavailable')
    ids = [r['army_regiment_id'] for r in records]
    need(len(ids) == len(set(ids)), 'duplicate full ArRg ID')
    slots = {}
    aliases = []
    for r in records:
        for d in r['records']:
            key = (d['persistent_regiment_id'], d['chunk_index'])
            value = (d['current_soldiers'], d['maximum_soldiers'], d['state_raw'])
            need(0 <= value[0] <= value[1] and (key not in slots or slots[key] == value), 'conflicting or nonordinary physical DATA')
            slots[key] = value
            aliases.append([r['army_regiment_id'], d['record_index'], *key])
    need(slots, 'actual physical slot inventory empty')
    return dict(ordered_regiment_ids=ids, data_aliases=aliases, physical_slots=[dict(persistent_regiment_id=k[0], chunk_index=k[1], current_soldiers=v[0], maximum_soldiers=v[1], state_raw=v[2]) for k, v in sorted(slots.items())])

def unique_physical_endpoints(before, after):
    """Compare real unique physical slots, allowing a movement state change."""

    def keyshape(value):
        return (value['ordered_regiment_ids'], value['data_aliases'], [(r['persistent_regiment_id'], r['chunk_index'], r['maximum_soldiers']) for r in value['physical_slots']])
    same = keyshape(before) == keyshape(after)
    prior = sum((r['current_soldiers'] for r in before['physical_slots']))
    later = sum((r['current_soldiers'] for r in after['physical_slots']))
    return dict(same_physical_identity_and_maximum=same, before_current=prior, after_current=later, unique_net_current=later - prior if same else None, county_causal_attribution=False)

def bound_saved_campaign_source(report, frozen, prepared, binding, *, sha, date_raw, actor, state_dir):
    """Live launch proof; entry-run-result.json exists only after normal close."""
    saved = prepared.get('startup', {}).get('saved_campaign', {})
    actual = report.get('saved_campaign_input') or {}
    launch = report.get('saved_campaign_launch') or {}
    argv = frozen.get('argv') or []
    need(prepared.get('startup', {}).get('mode') == 'saved_campaign', 'prepared source is not a saved campaign')
    need(frozen.get('run_id') == binding['run_id'], 'frozen host run ID differs')
    need(Path(frozen.get('state_dir', '')).resolve() == Path(state_dir).resolve(), 'frozen host state differs')
    need(saved.get('sha256') == actual.get('sha256') == sha and type(saved.get('bytes')) is int and (saved['bytes'] == actual.get('bytes')) and (saved.get('player_id') == actual.get('actor_character_id') == actor) and (saved.get('date_raw') == actual.get('date_raw') == date_raw) and (Path(saved.get('save', '')).resolve() == Path(actual.get('source_path', '')).resolve()), 'prepared source versus original native saved-campaign input differs')
    need(actual.get('status') == 'IMMUTABLE_SAVE_COPIED_TO_FRESH_VANILLA_PROFILE' and Path(actual.get('copied_save_path', '')).resolve().is_relative_to(Path(state_dir).resolve()), 'original native saved campaign was not copied into this state')
    flags = {'--saved-campaign-save-sha256': sha, '--saved-campaign-player-id': str(actor), '--saved-campaign-date-raw': str(date_raw), '--saved-campaign-save': str(Path(saved['save']))}
    for key, value in flags.items():
        need(argv.count(key) == 1 and argv[argv.index(key) + 1] == value, 'frozen host saved campaign flag differs: ' + key)
    need(launch.get('status') == 'ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED' and launch.get('argv_admitted') is True and (launch.get('ck3_pid') == binding['pid']) and (launch.get('load_save_name') == actual.get('load_save_name')) and ('-loadsave=' + actual['load_save_name'] in (launch.get('command') or [])), 'actual saved-campaign launch/ready PID or load-save command differs')
    return dict(source_sha256=sha, source_bytes=saved['bytes'], actor_character_id=actor, date_raw=date_raw, source_path=str(Path(saved['save']).resolve()), native_saved_campaign_status=actual['status'], actual_launch_status=launch['status'], actual_ck3_pid=launch['ck3_pid'], run_id=binding['run_id'])

def selected_unit(frame, army_id):
    rows = [u for u in frame.get('player_armies', []) if u.get('army_id') == army_id]
    need(len(rows) == 1, 'selected public CUnit missing/ambiguous')
    return rows[0]

def require_preview(body, frame, *, army_id, carmy_id, actor, origin, target):
    from xar_autoplayer.bridge.army_county_entry_preview_condition_contract import normalize_county_entry_condition_in_route_preview
    need(body.get('accepted') is True and body.get('status') == 'available', 'fresh native movement preview was not admitted')
    for key, fkey in (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'), ('queried_native_revision', 'native_revision')):
        need(body.get(key) == frame[fkey], 'movement preview crossed its actual source frame: ' + key)
    route = normalize_county_entry_condition_in_route_preview(body.get('route_preview') or {})
    need(route.get('status') == 'available' and route.get('army_id') == army_id and (route.get('origin_province_id') == origin) and (route.get('target_province_id') == target) and (route.get('previewed_date_raw') == frame['date_raw']), 'actual native route identity/date unavailable')
    ids = route.get('route_province_ids')
    need(type(ids) is list and ids and all((type(i) is int and i > 0 for i in ids)), 'actual native route absent/malformed')
    remaining = ids[1:] if ids[0] == origin else ids
    need(remaining and remaining[-1] == target, 'actual native path does not reach the requested Bayeux target')
    leaf = route.get('county_entry_condition_v1')
    need(isinstance(leaf, dict) and leaf.get('status') == 'available' and (leaf.get('inputs_observation_ready') is True) and (leaf.get('identity_before_after_match') is True), 'actual first-edge child unavailable; do not guess sea/Embark or substitute1513')
    need(leaf.get('subject_army_id') == army_id and leaf.get('native_carmy_id') == carmy_id and (leaf.get('actor_character_id') == actor) and (leaf.get('source_province_id') == origin) and (leaf.get('target_province_id') == remaining[0]), 'actual first-edge child identity mismatch')
    need(type(leaf.get('source_definition_1b_u8')) is int and type(leaf.get('target_definition_1b_u8')) is int, 'actual first-edge definition bytes unavailable')
    need(remaining == [target] and leaf.get('native_condition_passes') is True, 'County observation requires one actual native-condition-positive land hop')
    return dict(native_preview_available=True, native_route=list(ids), remaining_route=list(remaining), firsthop=remaining[0], county_first_edge=leaf, county_condition_true=leaf.get('native_condition_passes') is True, aggregate_native_move_permission_source='ck3_12002_military.cpp:406-423 plus build_route:459-498; actual4 bindings in ck3_12004_military.cpp:50-79', independent_boarding_quote_observed=False, actual_arrival_observed=False)

def unique_move(io, frame, after_snapshot, *, army_id, target, origin, preview):
    """Exactly one original MCP Move, including an unknown ACK with side effect."""
    io.claim('move-once', dict(expected_revision=frame['revision'], army_id=army_id, target_province_id=target, native_preview=preview))
    ack = None
    error = None
    try:
        ack = io.call('MOVE-ONCE', 'ck3_move_army', dict(army_id=army_id, target_province_id=target, expected_revision=frame['revision']))
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc))
    post = after_snapshot()
    u = selected_unit(post, army_id)
    route = u.get('route_province_ids')
    stored = type(route) is list and bool(route) and (route[-1] == target) and (u.get('move_target_province_id') == target)
    arrived = u.get('current_province_id') == target and route == [] and (u.get('move_target_province_id') is None)
    proof = dict(original_ack=ack, original_error=error, independent_post=post, actual_stored_route=route, stored_target_route_verified=stored, actual_arrived=arrived, route_equal_preview=route == preview['remaining_route'], Move_replayed=False)
    io.client.checkpoint('R04-MOVE-POST', proof)
    need((stored or arrived) and u.get('owner_character_id') == io.actor, 'unique Move postcondition unavailable; NEVER replay Move')
    return (post, proof)

def after_camera_frame(before, after, *, army_id, actor, origin):
    need(after.get('paused') is True, 'camera Start readback is not paused')
    need(before['date_raw'] == after['date_raw'], 'date changed while awaiting camera; do not re-preview or Move')
    need(before['episode_run_id'] == after['episode_run_id'], 'held campaign episode changed while awaiting camera')
    need(before['native_revision'] == after['native_revision'], 'native frame changed after sole preview; no stale P or second preview')
    for field in ('bridge_pid', 'connection_generation'):
        need(before['diagnostics'][field] == after['diagnostics'][field], 'held native identity changed while awaiting camera: ' + field)
    need(before['played_character']['character_id'] == after['played_character']['character_id'] == actor, 'actual camera actor changed')
    unit = selected_unit(after, army_id)
    need(unit['owner_character_id'] == actor and unit['current_province_id'] == origin and (unit['route_province_ids'] == []) and (unit.get('move_target_province_id') is None) and (unit['in_combat'] is False) and (unit['retreating'] is False), 'actual Army owner/origin/empty route/combat/retreat changed while awaiting camera; no Move')
    return after

def actual_arrival_frame(frame, *, army_id, target):
    unit = selected_unit(frame, army_id)
    return frame.get('paused') is True and unit.get('current_province_id') == target and (unit.get('route_province_ids') == []) and (unit.get('move_target_province_id') is None) and (unit.get('in_combat') is False) and (unit.get('retreating') is False)

def settings(value):
    need(type(value) is dict, 'Explicit r04_county_entry settings required')
    required = {'scene_root', 'capacity_admission', 'expected_source_save_sha256',
                'expected_start_date_raw', 'origin_province', 'target_province',
                'actor_id', 'army_id', 'native_carmy_id', 'capture_after_days',
                'max_days', 'driver_limit_bytes', 'profile_limit_bytes', 'deadline_utc',
                'camera_timeout_seconds', 'prefix'}
    need(required <= set(value), 'Incomplete public R04 settings: ' + ','.join(sorted(required-set(value))))
    allowed = required | {'next_full_reserve_bytes', 'normal_close_reserve', 'cleanup_save_reserve',
                         'one_day_timeout', 'max_packet_bytes', 'mirror_limit_bytes',
                         'cleanup_mirror_reserve_bytes', 'poll_seconds', 'speed', 'max_modal_choices', 'before_move_frame_required'}
    need(set(value) <= allowed, 'Unknown public R04 settings')
    defaults = dict(next_full_reserve_bytes=64*1024*1024, normal_close_reserve=900,
                    cleanup_save_reserve=120, one_day_timeout=120, max_packet_bytes=32*1024*1024,
                    mirror_limit_bytes=67*1024*1024, cleanup_mirror_reserve_bytes=3*1024*1024,
                    poll_seconds=.25, speed=5, max_modal_choices=64, before_move_frame_required=False)
    a = SimpleNamespace(**{**defaults, **value})
    need(type(a.before_move_frame_required) is bool, 'before_move_frame_required must be boolean')
    for key in ('expected_start_date_raw', 'origin_province', 'target_province', 'actor_id'):
        need(type(getattr(a, key)) is int and getattr(a, key)>0, 'Actual R04 '+key+' required')
    need(type(a.army_id) is int and 0<=a.army_id<2**31 and
         type(a.native_carmy_id) is int and -(2**31)<=a.native_carmy_id<2**31 and a.native_carmy_id!=-1,
         'Actual public Army and signed full CArmy IDs required')
    need(a.origin_province!=a.target_province, 'County Move must have a different target')
    need(type(a.capture_after_days) is int and 0<=a.capture_after_days<7 and
         type(a.max_days) is int and a.max_days==a.capture_after_days+1,
         'Exactly one late observation day required')
    for key in ('driver_limit_bytes', 'profile_limit_bytes', 'next_full_reserve_bytes'):
        need(type(getattr(a,key)) is int and getattr(a,key)>0, 'Explicit positive '+key+' required')
    need(type(a.camera_timeout_seconds) in (int,float) and math.isfinite(a.camera_timeout_seconds)
         and 0<a.camera_timeout_seconds<=900, 'Camera wait must be bounded to 1..900 seconds')
    need(a.normal_close_reserve>=900 and a.cleanup_save_reserve>=120,
         'R04 original normal-close and cleanup reserve required')
    need(type(a.expected_source_save_sha256) is str and len(a.expected_source_save_sha256)==64
         and all(c in '0123456789abcdef' for c in a.expected_source_save_sha256), 'Exact normal source SHA required')
    import re
    need(type(a.prefix) is str and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,47}',a.prefix),
         'Unique bounded public R04 query prefix required')
    deadline=datetime.fromisoformat(a.deadline_utc.replace('Z','+00:00'))
    need(deadline.tzinfo is not None, 'Timezone-aware R04 deadline required')
    # Reuse the shared finite observation validator before any launch.
    from xar_autoplayer.bridge.r05_supply_observation_case import observation_settings
    observation_settings(observation_options(a, deadline))
    return a


def observation_options(a, deadline):
    return dict(maximum_actual_days=a.max_days, maximum_modal_choices=a.max_modal_choices,
                max_packet_bytes=a.max_packet_bytes, max_retained_capture_bytes=a.mirror_limit_bytes,
                cleanup_capture_reserve_bytes=a.cleanup_mirror_reserve_bytes,
                one_day_timeout_seconds=a.one_day_timeout, normal_close_reserve_seconds=a.normal_close_reserve,
                cleanup_save_reserve_seconds=a.cleanup_save_reserve, poll_interval_seconds=a.poll_seconds,
                speed=a.speed, deadline_utc=deadline.isoformat())


def capacity_binding(cap, *, selection, scene, machine_id, source_head, a):
    """Only exact admitted roots grant scope; drive letters grant no authority."""
    scene=Path(scene).resolve(); profile=selection.state_dir.resolve(); driver=selection.run_dir.resolve()
    need(cap.get('machine_id')==machine_id and cap.get('admitted') is True and
         cap.get('budget_status')=='GREEN' and cap.get('run_id')==driver.name and
         cap.get('source_head')==source_head and Path(cap['scene_root']).resolve()==scene,
         'Actual same-machine/run/source Root capacity required')
    need(Path(cap['component_roots']['profile']).resolve()==profile and
         Path(cap['component_roots']['driver']).resolve()==driver,
         'Capacity does not exactly bind selected profile and Driver')
    need(cap['component_ceiling_bytes']['profile']==a.profile_limit_bytes and
         cap['component_ceiling_bytes']['driver']==a.driver_limit_bytes,
         'Selected profile/Driver limits differ from actual admission')
    now=datetime.now(timezone.utc)
    need(now<datetime.fromisoformat(cap['quota_review_at_utc'].replace('Z','+00:00')),
         'Root capacity quota expired')
    need(datetime.fromisoformat(a.deadline_utc.replace('Z','+00:00'))<=
         datetime.fromisoformat(cap['run_hard_deadline_utc'].replace('Z','+00:00')),
         'R04 deadline exceeds actual Root run hard deadline')
    return cap


def unique_roots(roots):
    roots=set(Path(p).resolve() for p in roots)
    return sorted((p for p in roots if not any(p!=q and p.is_relative_to(q) for q in roots)),key=str)


def metadata_bytes(roots):
    """Bounded stat-only accounting; nested roots and repeated files count once."""
    seen=set();total=0;files=0;roots=unique_roots(roots)
    for root in roots:
        need(root.is_dir() and not root.is_symlink() and not os.path.isjunction(root),
             'Actual admitted regular directory required: '+str(root))
        for directory, dirs, names in os.walk(root, followlinks=False):
            dirs[:]=[n for n in dirs if not (Path(directory)/n).is_symlink() and
                     not os.path.isjunction(Path(directory)/n)]
            for name in names:
                path=Path(directory)/name
                if path.is_symlink(): continue
                resolved=path.resolve(); key=os.path.normcase(str(resolved))
                need(resolved.is_relative_to(root), 'Meter file escaped admitted root')
                if key in seen: continue
                seen.add(key);files+=1
                need(files<=100000, 'Bounded same-run metadata meter exhausted')
                try: total+=path.stat().st_size
                except FileNotFoundError: pass
    return dict(bytes=total,files=files,roots=list(map(str,roots)),body_reads=0)


def runtime_bytes(selection, cap, *, limit, reserve, profile_limit, extra_roots=()):
    profile=unique_roots([selection.state_dir,*cap.get('component_additional_roots',{}).get('profile',[])])
    driver=selection.run_dir.resolve()
    need(all(not p.is_relative_to(driver) and not driver.is_relative_to(p) for p in profile),
         'Admitted profile and Driver roots overlap')
    need(all(Path(p).resolve().is_relative_to(driver) for p in extra_roots),
         'Actor output outside actual Driver run')
    p=metadata_bytes(profile);d=metadata_bytes([driver])
    need(p['bytes']<=profile_limit, 'Actual state plus additional profile roots exceeds profile ceiling')
    need(d['bytes']+reserve<=limit, 'Actual Driver lacks next-full/cleanup headroom')
    return dict(profile={**p,'limit_bytes':profile_limit},driver={**d,'limit_bytes':limit,'reserve_bytes':reserve},
                each_file_counted_once=True,global_shared_parent_walk=False)


def actual_binding(selection, scene, retained, report, cap, *, machine_id, source_head, a):
    capacity_binding(cap, selection=selection, scene=scene, machine_id=machine_id,source_head=source_head,a=a)
    control_path=(selection.state_dir/'control/ck3.json').resolve(strict=True)
    need(control_path==(Path(cap['component_roots']['profile'])/'control/ck3.json').resolve(strict=True),
         'Selected control outside exact Root-admitted profile')
    control=read(control_path);pid=retained.get('pid');creation=retained.get('create_time')
    hold=report.get('hold_until_utc_estimated')
    need(type(pid) is int and pid>0 and type(creation) in (int,float) and math.isfinite(creation)
         and creation>0 and retained.get('retained_synchronize_query_handle_acquired') is True,
         'Original retained OS PID/create-time unavailable')
    need(control.get('ck3_pid')==pid, 'Original retained identity/control disagree')
    need(type(hold) in (int,float) and math.isfinite(hold) and hold>time.time(), 'Original host hold unavailable')
    need(Path(report['state_dir']).resolve()==selection.state_dir.resolve(), 'Actual report state differs')
    return dict(machine_id=machine_id,observed_at_utc=datetime.now(timezone.utc).isoformat(),
                pid=pid,create_time=creation,hold=hold,run_id=selection.run_dir.name,control_path=str(control_path),
                capacity_admission=a.capacity_admission,original_retained_process=retained)


def read(path):
    return json.loads(Path(path).read_bytes())


class PreservedCaseQueue:
    """Same public queue; completed control errors leave room for OFF and Save."""
    def __init__(self, client): self.client=client
    def __getattr__(self,key): return getattr(self.client,key)
    def execute_plan(self,steps,*args,**kwargs):
        steps=copy.deepcopy(steps)
        for step in steps: step['continue_on_error']=True
        return self.client.execute_plan(steps,*args,**kwargs)


def held_day_frame(before, after, *, army_id, actor_id):
    need(after.get('paused') is True and before['date_raw']==after['date_raw'],
         'Date/paused changed during late camera wait; no day')
    need(before.get('episode_run_id')==after.get('episode_run_id'), 'Held campaign identity changed')
    need(all(before['diagnostics'][k]==after['diagnostics'][k] for k in ('bridge_pid','connection_generation')),
         'Held native lifetime changed')
    need(before['played_character']['character_id']==after['played_character']['character_id']==actor_id and
         after['played_character'].get('alive') is True,'Held player changed')
    old,new=selected_unit(before,army_id),selected_unit(after,army_id)
    fields=('army_id','owner_character_id','current_province_id','route_province_ids','move_target_province_id',
            'in_combat','retreating')
    need(all(old.get(k)==new.get(k) for k in fields) and new['owner_character_id']==actor_id and
         new['in_combat'] is False and new['retreating'] is False, 'Army route/owner changed during camera wait')
    return after


def await_day_camera(io,frame,result,a,*,_time=time.time,_monotonic=time.monotonic,_sleep=time.sleep):
    awaiting,signal=camera_paths(io.client.output)
    need(not awaiting.exists() and not signal.exists(),'Unique camera coordination already consumed')
    baseline=Path(io.client.output)/'R04-ENTRY-WINDOW-BASELINE.json'
    need(baseline.is_file() and result['Move_attempts']==1, 'Actual baseline and one claimed Move required')
    expected=dict(machine_id=io.context['machine_id'],run_id=io.client.selection.run_dir.name,
                  bridge_pid=frame['diagnostics']['bridge_pid'],date_raw=frame['date_raw'])
    payload=dict(**expected,observed_at_utc=datetime.now(timezone.utc).isoformat(),signal_path=str(signal.resolve()),
                 coordination_only=True,action_kind='exact-day',army_id=a.army_id,target_province_id=a.target_province,
                 pre_action_baseline=pin(baseline),terminal_result_path=str((Path(io.client.output)/'R04-BAYEUX-TERMINAL.json').resolve()),
                 maximum_wait_seconds=a.camera_timeout_seconds,Move_already_submitted_once=True,
                 clock_action_submitted=False,preparatory_days_unfilmed=a.capture_after_days,
                 planned_observation_day=a.max_days,actual_arrival_observed=False)
    io.client.checkpoint('before-action-camera-awaiting',payload)
    until=_monotonic()+a.camera_timeout_seconds
    reserve=a.normal_close_reserve+a.cleanup_save_reserve+a.one_day_timeout
    while _monotonic()<until:
        io.client.guard(reserve=reserve)
        need(_time()+reserve<io.settings['deadline_unix_seconds'], 'Original deadline reached before camera Start')
        if signal.is_file():
            row=read(signal)
            need(all(type(row.get(k)) is type(v) and row.get(k)==v for k,v in expected.items()) and
                 row.get('camera_started') is True, 'Actual Start signal identity/status differs')
            ref=row.get('start_receipt')
            need(type(ref) is dict, 'Actual canonical Start receipt absent')
            started=small_json(ref)
            need(started.get('machine_id')==expected['machine_id'] and started.get('run_id')==expected['run_id'] and
                 started.get('one_ffmpeg_job') is True, 'Actual one-job Start receipt differs')
            ready=started.get('canonical_process_ready')
            need(type(ready) is dict and pin(ready['path'])==ready, 'Canonical process-ready exact pin differs')
            proof=dict(status='ACTUAL_CAMERA_STARTED_FOR_OBSERVATION_DAY',awaiting=pin(awaiting),signal=pin(signal),
                       start_receipt=ref,canonical_process_ready=ready,Move_was_unfilmed=True,
                       preparatory_days_unfilmed=a.capture_after_days,business_or_video_approved=False)
            io.client.checkpoint('before-action-camera-Start-consumed',proof)
            return proof
        _sleep(min(.25,max(0,until-_monotonic())))
    raise TimeoutError('Late camera Start absent; completed days preserved, no day or Move replay')


def snapshot_only_to_target(io,snap,*,army_id,actor,target,max_days,before_day,on_day,result):
    """Publish every completed exact day before the next fallible preparation."""
    for day in range(1,max_days+1):
        current=snap('day'+str(day)+'-before');unit=selected_unit(current,army_id)
        need(current.get('paused') is True and unit['owner_character_id']==actor and
             unit['in_combat'] is False and unit['retreating'] is False, 'Day source is not paused/owned/noncombat')
        if actual_arrival_frame(current,army_id=army_id,target=target):
            return dict(arrived=True,actual_days=result['actual_days'],arrival_frame=current)
        route=unit['route_province_ids']
        need(route and route[-1]==target and unit.get('move_target_province_id')==target,
             'Stored route no longer reaches selected target; no re-Move')
        prepared=before_day(day,current)
        if prepared is not None: current=prepared
        end,clock=io.exact_day({'frame':current})
        need(end['date_raw']==current['date_raw']+24 and end.get('paused') is True and
             clock.get('exact_day_verified') is True,'Exact-day postframe/clock unavailable; no extra day')
        need(result['actual_days']==day-1,'Completed exact-day counter is not consecutive')
        unit=selected_unit(end,army_id)
        status=dict(machine_id=io.context['machine_id'],observed_at_utc=datetime.now(timezone.utc).isoformat(),
                    run_id=io.client.selection.run_dir.name,day=day,date_raw=end['date_raw'],
                    province=unit['current_province_id'],route=unit['route_province_ids'],
                    move_target_province_id=unit.get('move_target_province_id'),paused=end['paused'],
                    in_combat=unit['in_combat'],retreating=unit['retreating'],
                    arrived=actual_arrival_frame(end,army_id=army_id,target=target),
                    arrival_independent_full_verified=False,status='EXACT_DAY_SNAPSHOT_ONLY',clock=clock)
        result['days'].append(status);result['actual_days']=day
        on_day(day,end,clock,status)
        if status['arrived']: return dict(arrived=True,actual_days=day,arrival_frame=end)
    return dict(arrived=False,actual_days=result['actual_days'],arrival_frame=None)


def validate_contract(context):
    value=context.get('case_inputs',{}).get('r04_county_entry')
    if value is None: return
    a=settings(value)
    seed=context.get('saved_campaign',{})
    if seed:
        need(seed.get('sha256')==a.expected_source_save_sha256 and seed.get('date_raw')==a.expected_start_date_raw
             and seed.get('player_id')==a.actor_id, 'Prepared R04 normal S0 differs from selected source')
    # After allocation, common preflight checks the actual cap before a game is
    # launched. Preparation has run_id=None and validates only portable inputs.
    if context.get('run_id'):
        from ck3_live_run_id import current_machine_id
        head=subprocess.check_output(['git','-C',str(context['repo_root']),'rev-parse','HEAD'],text=True).strip()
        selection=SimpleNamespace(state_dir=Path(context['state_dir']),run_dir=Path(context['run_dir']))
        capacity_binding(small_json(a.capacity_admission),selection=selection,scene=a.scene_root,
                         machine_id=current_machine_id(),source_head=head,a=a)


def await_before_move_frame(io, frame, result, a, *, _time=time.time,
                           _monotonic=time.monotonic, _sleep=time.sleep):
    """Wait for a pinned canonical frame review; this does not start a camera."""
    if not a.before_move_frame_required:
        return None
    maximum_wait=a.camera_timeout_seconds
    need(0<maximum_wait<=900, 'Before-Move frame wait must be bounded to 900 seconds')
    need(result['Move_attempts']==0, 'Before-Move frame review must precede the sole Move')
    output=Path(io.client.output)
    awaiting=output/'before-move-frame-awaiting.json'
    signal=output/'before-move-frame-reviewed.json'
    need(not awaiting.exists() and not signal.exists(), 'Before-Move frame namespace already consumed')
    expected=dict(machine_id=io.context['machine_id'],run_id=io.client.selection.run_dir.name,
                  bridge_pid=frame['diagnostics']['bridge_pid'],date_raw=frame['date_raw'])
    source=io.client.checkpoint('R04-BEFORE-MOVE-FRAME-SOURCE',frame)
    payload=dict(**expected,observed_at_utc=datetime.now(timezone.utc).isoformat(),
                 signal_path=str(signal.resolve()),source_frame=pin(source),maximum_wait_seconds=maximum_wait,
                 retained_create_time=result['actual_binding']['create_time'],coordination_only=True,
                 action_kind='review-frame-only',Move_attempts=0,camera_started=False,
                 normal_close_reserve_seconds=a.normal_close_reserve,
                 cleanup_save_reserve_seconds=a.cleanup_save_reserve)
    io.client.checkpoint('before-move-frame-awaiting',payload)
    until=_monotonic()+maximum_wait
    reserve=a.normal_close_reserve+a.cleanup_save_reserve+a.one_day_timeout
    while _monotonic()<until:
        io.client.guard(reserve=reserve)
        need(_time()+reserve<io.settings['deadline_unix_seconds'],
             'Original deadline reached before frame review; no Move')
        if signal.is_file():
            row=read(signal)
            need(all(type(row.get(k)) is type(v) and row.get(k)==v for k,v in expected.items()) and
                 row.get('frame_reviewed') is True and row.get('camera_started') is not True,
                 'Before-Move frame signal machine/run/PID/date differs')
            review_ref=row.get('review_receipt')
            need(type(review_ref) is dict, 'Canonical Root frame review receipt required')
            review=small_json(review_ref)
            need(review.get('schema')=='xar.e04.owned-client-root-review.v1' and
                 review.get('machine_id')==expected['machine_id'] and review.get('run_id')==expected['run_id'] and
                 review.get('reviewer')=='/root' and review.get('root_reviewed_window_only') is True and
                 review.get('root_reviewed_no_hover') is True and review.get('content') in ('army-supply','map-context'),
                 'Canonical Root direct frame review identity/status differs')
            now=datetime.now(timezone.utc)
            need(0<=(now-datetime.fromisoformat(review['reviewed_at_utc'].replace('Z','+00:00'))).total_seconds()<=120,
                 'Before-Move Root frame review is stale')
            capture_ref=review.get('capture');need(type(capture_ref) is dict, 'Canonical original capture pin required')
            capture=small_json(capture_ref);source=capture.get('source') or {}
            need(capture.get('schema')=='xar.e04.owned-client-original-frame.v1' and
                 capture.get('machine_id')==expected['machine_id'] and capture.get('run_id')==expected['run_id'] and
                 capture.get('pid')==expected['bridge_pid']==source.get('owned_ck3_pid') and
                 source.get('owned_ck3_create_time')==result['actual_binding']['create_time'] and
                 capture.get('recording_started') is False,
                 'Canonical original frame crossed actual CK3 lifetime')
            need(0<=(now-datetime.fromisoformat(capture['observed_at_utc'].replace('Z','+00:00'))).total_seconds()<=180,
                 'Before-Move original frame is stale')
            for key in ('desktop_original','client_original'):
                ref=capture[key];need(pin(ref['path'])==ref,'Before-Move original image pin changed')
            need(review.get('client_original')==capture['client_original'], 'Root review client original differs')
            proof=dict(status='ACTUAL_BEFORE_MOVE_FRAME_REVIEW_CONSUMED',**expected,
                       awaiting=pin(awaiting),signal=pin(signal),review_receipt=review_ref,capture=capture_ref,
                       camera_started=False,Move_submitted=False,business_or_video_approved=False)
            io.client.checkpoint('before-move-frame-review-consumed',proof)
            return proof
        _sleep(min(.25,max(0,until-_monotonic())))
    raise TimeoutError('Before-Move frame review absent; no Move submitted')


def verify_case(context):
    """Read preserved progress even when the optional observation stopped RED."""
    from ck3_live_run_id import current_machine_id
    path=Path(context['output'])/'R04-BAYEUX-TERMINAL.json'
    if not path.is_file():
        return dict(present=False,actual_days=None,status='ACTUAL_R04_TERMINAL_ABSENT',
                    business_pass=False,R04_entire_card_closed=False)
    actual=pin(path);value=small_json(actual)
    need(value.get('machine_id')==current_machine_id() and value.get('run_id')==context['run_id'],
         'R04 terminal belongs to another machine or allocated run')
    need(type(value.get('actual_days')) is int and 0<=value['actual_days']<=7,
         'Actual R04 completed-day summary absent or malformed')
    return dict(present=True,source=actual,**{k:value.get(k) for k in
                ('machine_id','run_id','status','actual_days','arrived','finaldate','finalprovince','OFFclear','Save','errors')},
                business_pass=False,R04_entire_card_closed=False)


def run_case(context,client):
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_full_army import FullArmyResultClient
    from xar_autoplayer.bridge.r05_supply_observation_case import ObservationIO,StrengthRevisionDrift
    from xar_autoplayer.bridge.army_county_entry_loss_evidence_12004 import EXE_12004
    from xar_autoplayer.bridge.army_observer_research_sampling_control import normalize_result as normalize_sampling
    a=settings(context['case_inputs']['r04_county_entry']);sel=client.selection
    machine_id=current_machine_id();scene=Path(a.scene_root).resolve()
    source_head=subprocess.check_output(['git','-C',str(context['repo_root']),'rev-parse','HEAD'],text=True).strip()
    cap=small_json(a.capacity_admission)
    need(Path(client.output).resolve().is_relative_to(sel.run_dir.resolve()),'R04 output outside selected Driver')
    client.guard(reserve=a.normal_close_reserve+a.cleanup_save_reserve+a.one_day_timeout)
    retained=client.retain_process();report=client.read_report()
    binding=actual_binding(sel,scene,retained,report,cap,machine_id=machine_id,source_head=source_head,a=a)
    binding['saved_campaign_source']=bound_saved_campaign_source(report,client.frozen,sel.prepared,binding,
        sha=a.expected_source_save_sha256,date_raw=a.expected_start_date_raw,actor=a.actor_id,state_dir=sel.state_dir)
    deadline=datetime.fromtimestamp(min(datetime.fromisoformat(a.deadline_utc.replace('Z','+00:00')).timestamp(),binding['hold']),timezone.utc)
    binding.update(requested_Root_deadline_utc=a.deadline_utc,effective_deadline_utc=deadline.isoformat())
    need(all(r.get('finished_at') and r.get('ok') is True and not r.get('error') for r in report.get('steps',[])),
         'Original owner has pending/failed steps; no queue race or replay')
    def usage():
        need(small_json(a.capacity_admission)==cap, 'Actual Root capacity changed')
        return runtime_bytes(sel,cap,limit=a.driver_limit_bytes,reserve=a.next_full_reserve_bytes*2,
                             profile_limit=a.profile_limit_bytes,extra_roots=[client.output])
    initial_usage=usage()
    wrapped=FullArmyResultClient(PreservedCaseQueue(client),prefix=a.prefix)
    actual_context={**context,'machine_id':machine_id,
                    'command_timeout':getattr(sel,'effective_budgets',sel.case['budgets'])['command_timeout']}
    frame=wrapped.snapshot();u=selected_unit(frame,a.army_id)
    need(frame['date_raw']==a.expected_start_date_raw and frame['played_character']['character_id']==a.actor_id and
         u['owner_character_id']==a.actor_id and u['current_province_id']==a.origin_province and
         u['route_province_ids']==[] and u['in_combat'] is False and u['retreating'] is False,
         'Fresh saved date/actor/stationary owned Army origin required')
    identity=dict(independent_after=dict(actor_id=a.actor_id,generation=frame['diagnostics']['connection_generation'],
                                        province_id=a.origin_province),pid=binding['pid'],episode=frame['episode_run_id'],
                  army_id=a.army_id,carmy_id=a.native_carmy_id)
    io=ObservationIO(wrapped,observation_options(a,deadline),context=actual_context,initialization=identity)
    result=dict(machine_id=machine_id,observed_at_utc=datetime.now(timezone.utc).isoformat(),run_id=sel.run_dir.name,
                status='entered',actual_binding=binding,initial_usage=initial_usage,target_province_id=a.target_province,
                initialization_executed=False,Move_attempts=0,actual_days=0,arrived=False,days=[],
                physical_county_positive=None,county_total_debit=None,whole_army_net_attributed=False,
                normalclose_delegated_to_public_entry=True)
    sampling_attempted=False;before=None
    def snap(label,cleanup=False):return io.snapshot(label,paused=True,cleanup=cleanup)
    def sample(label,current=None):
        usage();f=current or snap(label+'-before')
        def query(x,suffix):
            return io.call(label+suffix,'ck3_query_army_strengths',dict(army_ids=[a.army_id],profile='observed_history_full_v1',
                ordered_refill_entry_mode='observed_prepared',ordered_besieging_entry_mode='observed_prepared',
                expected_revision=x['revision']),readonly_strength=True)
        try:q=query(f,'-full')
        except StrengthRevisionDrift as first:
            wrapped.checkpoint(label+'-first-readonly-RED',dict(proof=first.proof,original_frame=f,retry_limit=1,Move_replayed=False,day_replayed=False))
            fresh=snap(label+'-fresh-readonly');old=selected_unit(f,a.army_id);new=selected_unit(fresh,a.army_id)
            need(fresh['date_raw']==f['date_raw'] and all(old.get(k)==new.get(k) for k in
                 ('owner_character_id','current_province_id','army_id')),'Readonly rebound crossed actual date/Army position')
            q=query(fresh,'-fresh-full-once');f=fresh
        rows=[r for r in q['army_strengths'] if r['army_id']==a.army_id]
        need(len(rows)==1 and rows[0]['status']=='available' and rows[0]['native_carmy_id']==a.native_carmy_id,
             'Complete actual CArmy full row unavailable')
        end=snap(label+'-independent-after')
        need(end['paused'] is True and end['date_raw']==f['date_raw'] and end['native_revision']==f['native_revision'],
             'Full query crossed actual date/native frame')
        need(q['queried_revision']==f['revision'] and q['queried_native_revision']==f['native_revision'], 'Full query source differs')
        need(end.get('episode_run_id')==f.get('episode_run_id') and
             end['played_character']['character_id']==f['played_character']['character_id'] and
             all(end['diagnostics'][k]==f['diagnostics'][k] for k in ('bridge_pid','connection_generation')),
             'Full query lifetime/actor differs')
        wrapped.checkpoint(label+'-independent-fences',dict(before=f,after=end,query_sequence=q['query_sequence']))
        return dict(frame=end,before_frame=f,query=q,army=rows[0],physical=inventory(rows[0]))
    def sampling(enabled,family,cleanup=False):
        f=snap('sampling-'+family,cleanup);args=dict(observer_family=family,expected_revision=f['revision'])
        if enabled is not None:args['enabled']=enabled
        tool='ck3_query_army_observer_research_sampling_v1' if enabled is None else 'ck3_set_army_observer_research_sampling_v1'
        b=io.call('sampling-'+family,tool,args,cleanup=cleanup);mode='query' if enabled is None else 'enable' if enabled else 'disable'
        v=normalize_sampling({k:b[k] for k in ('step','accepted','status','army_observer_research_sampling_v1','backend_id')},
            expected_step=mode+'-army-observer-research-sampling-v1',observer_family=family)
        need(b.get('queried_revision')==f['revision'] and b.get('queried_native_revision')==f['native_revision'] and
             b.get('queried_date_raw')==f['date_raw'],'Sampling control crossed actual source frame')
        if enabled is True:need(v['accepted'] is True,'Actual inline observer enable refused')
        return v
    try:
        caps=io.call('county-current-capabilities','ck3_get_capabilities',{})
        from xar_autoplayer.bridge.war_contract import MOVE_ARMY_CAPABILITY,PREVIEW_MOVE_ARMY_CAPABILITY
        required={MOVE_ARMY_CAPABILITY,PREVIEW_MOVE_ARMY_CAPABILITY,'game.command.query-army-strengths-v1'}
        need(caps.get('snapshot') is True and required<=set(caps.get('bridge_capabilities',[])),
             'Public R04 required native capabilities are unavailable')
        off0=sampling(None,'all')
        need(all(not x['capture_enabled'] and not x['busy'] for x in off0['army_observer_research_sampling_v1'].values()),
             'Another observer owner remains active')
        result['entry_window_plan']=dict(snapshot_only_days=a.capture_after_days,single_observation_day=a.max_days,
            full_query_count_planned=2,early_arrival_has_no_owner_claim=True,arrival_on_observation_day_not_assumed=True)
        if a.before_move_frame_required:
            held=snap('before-move-frame-current')
            result['before_move_frame']=await_before_move_frame(io,held,result,a)
            held_day_frame(held,snap('before-move-frame-independent-after'),army_id=a.army_id,actor_id=a.actor_id)
        preview_frame=snap('fresh-target-preview-source')
        unit=selected_unit(preview_frame,a.army_id)
        need(preview_frame['date_raw']==a.expected_start_date_raw and
             preview_frame['played_character']['character_id']==a.actor_id and unit['owner_character_id']==a.actor_id and
             unit['current_province_id']==a.origin_province and unit['route_province_ids']==[] and
             unit['in_combat'] is False and unit['retreating'] is False,
             'Post-sampler preview source changed date/actor/stationary Army')
        fresh=preview_frame
        preview=io.call('fresh-target-preview','ck3_execute_step',dict(step=f'preview-move-army-{a.army_id}-to-{a.target_province}',
                        expected_revision=fresh['revision']))
        admitted=require_preview(preview,fresh,army_id=a.army_id,carmy_id=a.native_carmy_id,actor=a.actor_id,
                                 origin=a.origin_province,target=a.target_province)
        wrapped.checkpoint('R04-FRESH-PREVIEW',dict(native_body=preview,admission=admitted))
        move_frame=after_camera_frame(fresh,snap('Move-before-once'),army_id=a.army_id,actor=a.actor_id,origin=a.origin_province)
        result.update(camera_start=None,Move_attempts=1,recording_placement='observation_day_only; preparatory_Move_and_days_unfilmed')
        post,proof=unique_move(io,move_frame,lambda:snap('Move-independent-after'),army_id=a.army_id,
                               target=a.target_province,origin=a.origin_province,preview=admitted)
        result['Move_postcondition']=proof
        def before_day(day,current):
            nonlocal before,sampling_attempted
            usage()
            if day!=a.max_days:return None
            sampling_attempted=True
            before,on,current=window.arm_window(current,sample=sample,sampling=sampling,snapshot=snap,
                army_id=a.army_id,native_carmy_id=a.native_carmy_id,selected_unit=selected_unit)
            base=before['army']['actual_loss_writer_observations_v1'];result['sampling_ON']=on
            wrapped.checkpoint('R04-ENTRY-WINDOW-BASELINE',dict(frame=before['frame'],physical=before['physical'],
                writer_fences={k:base[k] for k in ('latest_sequence','oldest_available_sequence','overwritten_events','unattributed_capture_failures')},sampling_ON=on))
            result['camera_start']=await_day_camera(io,current,result,a)
            return held_day_frame(current,snap('entry-window-after-camera'),army_id=a.army_id,actor_id=a.actor_id)
        def on_day(day,end,clock,status):
            client.checkpoint('R04-ENTRY-STATUS-DAY-'+str(day).zfill(2),status)
        transit=snapshot_only_to_target(io,snap,army_id=a.army_id,actor=a.actor_id,target=a.target_province,
            max_days=a.max_days,before_day=before_day,on_day=on_day,result=result)
        result['arrival_candidate_observed']=transit['arrived']
        if before is None:
            result['status']='ARRIVED_BEFORE_WINDOW_NO_OWNER_PROOF' if transit['arrived'] else 'NO_ENTRY_WINDOW_EXECUTED'
            result['arrived']=bool(transit['arrived']);result['arrival_full_verified']=False
        else:
            arrival=sample('entry-window-after');post_sampling=sampling(None,'all')
            result['entry_window_evidence']=window.consume_window(before,arrival,exe_sha256=EXE_12004,
                endpoint_compare=unique_physical_endpoints,after_sampling=post_sampling,on_sampling=result['sampling_ON'])
            result['arrived']=actual_arrival_frame(arrival['frame'],army_id=a.army_id,target=a.target_province)
            result['arrival_full_verified']=result['arrived']
            result['status']='ENTRY_WINDOW_ACTUAL_ARRIVAL_CONSUMED' if result['arrived'] else 'ONE_WINDOW_COMPLETED_NO_ACTUAL_ARRIVAL'
            wrapped.checkpoint('R04-ENTRY-WINDOW-EVIDENCE',result['entry_window_evidence'])
    except BaseException as error:
        result.update(status='STOPPED_ERROR_PRESERVED_NO_REPLAY',error=dict(type=type(error).__name__,message=str(error)))
    finally:
        cleanup=dict(errors=[],sampling_OFF_clear_verified=False,normal_Save_verified=False)
        try:
            f=io.snapshot('cleanup-frame',cleanup=True)
            if not f['paused']:io.call('cleanup-pause','ck3_execute_step',dict(step='pause-map',expected_revision=None),cleanup=True)
            if io.active_clock is not None:
                status=io.clock_status(cleanup=True)
                if status['state']=='armed':
                    need(status['generation']==io.active_clock['armed']['generation'],'Original sentinel generation changed')
                    io.call('cancel-original-clock','ck3_execute_step',dict(step='research-cancel-tactical-daily-sentinel-v1-generation-'+str(status['generation']),expected_revision=None),cleanup=True)
            elif io.unknown_clock_claim is not None:cleanup['unknown_clock_readback']=io.clock_status(cleanup=True)
        except BaseException as error:cleanup['errors'].append('clock/pause: '+repr(error))
        try:
            if sampling_attempted:sampling(False,'all',True)
            off=sampling(None,'all',True);cleanup['OFF_readback']=off
            cleanup['sampling_OFF_clear_verified']=all(not r['capture_enabled'] and not r['busy'] and r['clear_completed'] and
                r['retained_records']==0 for r in off['army_observer_research_sampling_v1'].values())
            need(cleanup['sampling_OFF_clear_verified'],'Actual OFF/clear incomplete')
        except BaseException as error:cleanup['errors'].append('OFF: '+repr(error))
        try:
            f=snap('Save-before',True);saved=io.call('Save-once','ck3_save_checkpoint',dict(expected_revision=f['revision']),cleanup=True)
            post=snap('Save-independent-after',True);ck=saved.get('checkpoint') or {}
            cleanup.update(Save_result=saved,Save_after=post)
            cleanup['normal_Save_verified']=ck.get('status')=='saved' and ck.get('date_raw')==f['date_raw']==post['date_raw']
            need(cleanup['normal_Save_verified'],'Actual normal Save not independently verified')
        except BaseException as error:cleanup['errors'].append('Save: '+repr(error))
        result.update(cleanup=cleanup,full_wire_proofs=wrapped.full_proofs,modals=io.modals,
                      readonly_strength_recoveries=io.readonly_strength_recoveries)
        fullpath=client.checkpoint('R04-BAYEUX-RESULT',result)
        terminal=dict(machine_id=machine_id,observed_at_utc=datetime.now(timezone.utc).isoformat(),run_id=sel.run_dir.name,
            status=result['status'],arrived=result['arrived'],actual_days=result['actual_days'],Move_attempts=result['Move_attempts'],
            OFFclear=cleanup['sampling_OFF_clear_verified'],Save=cleanup['normal_Save_verified'],errors=cleanup['errors'],
            full_result_path=str(fullpath),business_pass=False,R04_entire_card_closed=False)
        final=cleanup.get('Save_after')
        if final is not None:terminal.update(finaldate=final['date_raw'],finalprovince=selected_unit(final,a.army_id)['current_province_id'])
        client.checkpoint('R04-BAYEUX-TERMINAL',terminal)
    need(result['status']!='STOPPED_ERROR_PRESERVED_NO_REPLAY' and not cleanup['errors'],
         'R04 stopped with preserved evidence; public normal close still required')
    return terminal
