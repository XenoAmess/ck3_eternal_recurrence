"""One declared natural writer opportunity on the existing public CaseClient.

The existing prepare/observer/consumer controller owns the four-slot watch.
The shared entry owns normal closure; this actor withholds it until restore and
payment OFF/clear are independently proved. No load, host or SDK is constructed.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import re
import subprocess
import sys
import time

from .r10_prepare_adapter import need, pin, small_json
from . import r04_county_entry as common
from . import r08_writer_common_adapter as bridge
from .ordinary_save_contract import (Call, Snapshot, Payment, JsonObject,
    begin_save, verify_save, retained_client, unconfirmed, cleanup_result)

MODE = 'native_campaign_owned_no_load_v2'
RESEARCH = Path('ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004')
AUTH_SCHEMA = 'xar.e04.r206-cd-writer-explicit-root-admission.v1'
AUTH_STATUS = 'ROOT_ADOPTED_R206_INDEPENDENT_CD_WRITER_WINDOW'


def settings(value):
    required = {'scene_root', 'source_head', 'native_build_source_head', 'build_dir',
                'machine_execution_gate', 'actor_id', 'expected_start_date_raw',
                'expected_source_save_sha256', 'profile_limit_bytes', 'driver_limit_bytes',
                'deadline_utc', 'prefix', 'payment_enable_once_authorized'}
    defaults = dict(admission_timeout_seconds=600, normal_close_reserve=900,
                    cleanup_save_reserve=120, poll_seconds=.25,
                    natural_phase_enable_once_authorized=False)
    need(type(value) is dict and required <= set(value) and set(value) <= required | set(defaults),
         'Explicit complete R08 one-opportunity settings required')
    a = SimpleNamespace(**{**defaults, **value})
    for name in ('actor_id', 'expected_start_date_raw', 'profile_limit_bytes', 'driver_limit_bytes'):
        need(type(getattr(a, name)) is int and getattr(a, name) > 0, 'Positive R08 ' + name + ' required')
    for name, size in (('source_head', 40), ('native_build_source_head', 40), ('expected_source_save_sha256', 64)):
        need(re.fullmatch('[0-9a-f]{'+str(size)+'}', getattr(a, name) or '') is not None,
             'Exact R08 source identity required: ' + name)
    need(re.fullmatch('r08-[a-z0-9-]{1,55}', a.prefix or '') is not None, 'Unique bounded R08 prefix required')
    need(type(a.payment_enable_once_authorized) is bool, 'Explicit payment enable decision required')
    need(type(a.natural_phase_enable_once_authorized) is bool, 'Explicit natural-phase enable decision required')
    need(type(a.admission_timeout_seconds) in (int, float) and 0 < a.admission_timeout_seconds <= 900
         and type(a.poll_seconds) in (int, float) and .05 <= a.poll_seconds <= 1,
         'Finite R08 admission wait required')
    need(a.normal_close_reserve >= 900 and a.cleanup_save_reserve >= 120, 'Original normal-close/cleanup reserves required')
    need(datetime.fromisoformat(a.deadline_utc.replace('Z', '+00:00')).tzinfo is not None,
         'Timezone-aware R08 deadline required')
    need(type(a.machine_execution_gate) is dict, 'Exact qualified machine gate pin required')
    return a


def validate_contract(context):
    a = settings(context['case_inputs']['r08_writer_one_day'])
    seed = context.get('saved_campaign') or {}
    if seed:
        need(seed.get('sha256') == a.expected_source_save_sha256 and seed.get('player_id') == a.actor_id
             and seed.get('date_raw') == a.expected_start_date_raw, 'R08 normal source/date/actor differs')
    return a


class CloseGate:
    """Guard only this instance's original shared close; retain errors as errors."""
    def __init__(self, client: object) -> None:
        self.client = client
        self.restored = True
        self.off_clear = False
        self.save_verified = False
        original = getattr(client, 'normal_close', None)
        if not callable(original):
            raise ValueError('Original shared normal_close unavailable')
        def guarded(disposition: str) -> object:
            need(self.restored and self.off_clear and self.save_verified, 'R08 restore/OFF-clear/Save unproved; normal Quit withheld')
            return original(disposition)
        setattr(client, 'normal_close', guarded)


def load_controller():
    # A fresh module keeps its Popen sessions local to this one public run.
    path = Path(__file__).with_name('r08_writer_controller.py')
    name = '_r08_public_writer_controller_' + str(time.monotonic_ns())
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def root_window_guard(context, client, cfg, a, identity):
    """Consume the existing explicit Root DR grant against fresh public facts."""
    client.guard()
    auth = small_json(cfg['observer_admission'])
    small_json(a.machine_execution_gate)
    cap = small_json(cfg['scene_capacity'])
    common.capacity_binding(cap, selection=client.selection, scene=a.scene_root,
        machine_id=cfg['watch']['expected']['machine'], source_head=a.source_head, a=a)
    need(auth.get('schema') == AUTH_SCHEMA and auth.get('status') == AUTH_STATUS
         and auth.get('admitted') is True and auth.get('external_debugger_allowed') is True
         and auth.get('scope') == 'independent-unfilmed-cd-writer-window'
         and auth.get('r06_probe_concurrent') is False, 'Independent finite Root DR grant required')
    for key, expected in (('scene_capacity', cfg['scene_capacity']), ('runtime_identity', identity),
        ('machine_id', cfg['watch']['expected']['machine']), ('source_head', a.source_head),
        ('runtime_source_head', a.source_head), ('native_build_source_head', a.native_build_source_head),
        ('run_id', context['run_id']), ('expected_root_identity', cfg['root_identity']),
        ('overrides_observer_policy_of_sha256', cfg['scene_capacity']['sha256'])):
        need(auth.get(key) == expected, 'Root writer grant differs: ' + key)
    need(all(type(auth['expected_root_identity'][k]) is type(v) for k,v in cfg['root_identity'].items()),
         'Typed Root writer identity differs')
    need(Path(auth['scene_root']).resolve() == Path(a.scene_root).resolve()
         and Path(auth['watch_output_root']).resolve() == Path(cfg['watch']['watch_output_root']).resolve(),
         'Root writer grant crossed actual roots')
    end = datetime.fromisoformat(auth['quota_review_at_utc'].replace('Z', '+00:00')).timestamp()
    need(time.time() < end <= min(datetime.fromisoformat(cap['quota_review_at_utc'].replace('Z','+00:00')).timestamp(),
         datetime.fromisoformat(a.deadline_utc.replace('Z','+00:00')).timestamp()), 'Root writer grant expired/exceeds scope')
    need(auth.get('maximum_watch_ms') == cfg['watch']['timeout_ms'] == 30000
         and auth.get('maximum_aggregate_slot_hits') == cfg['watch']['max_slot_hits'] == 128
         and auth.get('payment_window_policy') == 'preserve_existing_owned_window_no_enable_clear',
         'Only existing four-slot 30s/128 preserved-window contract admitted')
    need(min(client.remaining(), end-time.time()) >= a.normal_close_reserve+a.cleanup_save_reserve+70,
         'R08 original deadline lacks finite watch and close reserves')
    return auth


def wait_admission(context, client, a, collected, identity, *, clock=time.monotonic, sleep=time.sleep):
    signal = Path(client.output)/'r08-root-observer-admission.json'
    need(not signal.exists(), 'R08 Root grant predates fresh awaiting; never reuse')
    client.checkpoint('r08-before-observer-awaiting', dict(machine_id=collected['expected']['machine'],
        run_id=context['run_id'], actual_inputs=collected['receipt'], runtime_identity=identity,
        expected_root_identity={k:collected['expected'][v] for k,v in (
            ('pid','pid'),('process_create_time_100ns','created'),('connection_generation','generation'),
            ('episode_run_id','episode'),('player_character_full_id','character_id'),
            ('controlled_window_id','window'),('payment_epoch','epoch'),('date_raw','date'))},
        signal_path=str(signal), start_date_raw=a.expected_start_date_raw,
        target_date_raw=a.expected_start_date_raw+24, maximum_observer_launches=1,
        maximum_actual_days=1, observer_started=False, watch_ms=30000, aggregate_slot_hits=128))
    end = clock()+a.admission_timeout_seconds
    while clock() < end:
        client.guard()
        need(client.remaining() > a.normal_close_reserve+a.cleanup_save_reserve+70,
             'R08 admission wait exhausted original close reserves')
        if signal.exists():
            ref=pin(signal)
            return ref, small_json(ref)
        sleep(a.poll_seconds)
    raise TimeoutError('R08 Root admission absent; no observer/day submitted')



def normalize_cleanup_clock(raw, *, observer_claimed):
    """Accept native's literal never-armed zero state only before our claim."""
    from xar_autoplayer.bridge.native_driver import _normalize_tactical_daily_sentinel_status
    idle = dict(state='idle', generation=0, starting_date_raw=0, target_date_raw=0,
        last_observed_date_raw=0, trigger_date_raw=0, speed=0, mode='decision_epoch',
        army_count=0, combat_count=0, completed_daily_ticks=0, intermediate_pause_count=0,
        trigger_flags=0, trigger_reasons=[], signed_date_delta_from_target_raw=0,
        overshoot_days=-1, pause_wrapper_called=False, pause_observed=False,
        terminal_observed=False, abnormal=False)
    if observer_claimed is False and type(raw) is dict and set(raw)==set(idle) and all(
        type(raw[k]) is type(v) and raw[k]==v for k,v in idle.items()):
        return dict(raw)
    return _normalize_tactical_daily_sentinel_status(raw)


def cleanup_clock(call, *, observer_claimed):
    status=normalize_cleanup_clock(call('cleanup-clock','ck3_execute_step',
        dict(step='research-query-tactical-daily-sentinel-v1',expected_revision=None))['tactical_daily_sentinel'],
        observer_claimed=observer_claimed)
    if status['state']=='armed':
        call('cleanup-cancel-clock','ck3_execute_step',dict(
            step='research-cancel-tactical-daily-sentinel-v1-generation-'+str(status['generation']),expected_revision=None))
        status=normalize_cleanup_clock(call('cleanup-clock-independent','ck3_execute_step',
            dict(step='research-query-tactical-daily-sentinel-v1',expected_revision=None))['tactical_daily_sentinel'],
            observer_claimed=True)
    need(status['state'] in ('idle','triggered','failed'), 'Clock quiescence unknown; Save withheld')
    return status


def sampling_control(call, snapshot, label, family, enabled=None):
    from xar_autoplayer.bridge.army_observer_research_sampling_control import normalize_result, STATE_KEY
    frame=snapshot(label+'-frame')
    args=dict(observer_family=family,expected_revision=frame['revision'])
    if enabled is None:
        tool='ck3_query_army_observer_research_sampling_v1'
        step='query-army-observer-research-sampling-v1'
    else:
        args['enabled']=enabled
        tool='ck3_set_army_observer_research_sampling_v1'
        step=('enable' if enabled else 'disable')+'-army-observer-research-sampling-v1'
    body=call(label,tool,args)
    raw={k:body[k] for k in ('step','accepted','status',STATE_KEY,'backend_id')}
    return normalize_result(raw,expected_step=step,observer_family=family)[STATE_KEY]


def prepare_natural_phase(call, snapshot, *, enable_once_authorized):
    state=sampling_control(call,snapshot,'natural-phase-initial','natural_phase')['natural_phase']
    if state['capture_enabled'] is not True:
        need(enable_once_authorized is True, 'Natural-phase OFF: no explicit once-enable authorization')
        sampling_control(call,snapshot,'natural-phase-enable-once','natural_phase',True)
        state=sampling_control(call,snapshot,'natural-phase-independent-on','natural_phase')['natural_phase']
    need(state['installed'] is True and state['available'] is True and state['capture_enabled'] is True
        and state['busy'] is False and state['active_captures']==0,
        'Payment enable requires independent available idle natural-phase ON')
    return state


def _cleanup_writer_window_impl(call, snapshot, payment, gate, *, observer_claimed, expected_start_date_raw):
    """Converge independent OFFs even after an error; never replay an unknown action."""
    cleanup=dict(OFFclear=False,Save=False,native_restore_verified=gate.restored,
        payment_OFFclear=False,army_families_OFFclear=False,clock_quiescent=False)
    errors=[];actual_days=None
    def attempt(label, action):
        try:return True,action()
        except BaseException as error:
            errors.append(label+': '+type(error).__name__+': '+str(error))
            return False,None
    if not gate.restored:
        errors.append('cleanup: Observer restore/detach unproved; OFF/Save/Quit withheld; retain original controller session')
        return cleanup,errors,actual_days
    paused,_=attempt('cleanup-pause',lambda:call('cleanup-pause','ck3_execute_step',dict(step='pause-map',expected_revision=None)))
    clock_ok,status=attempt('cleanup-clock',lambda:cleanup_clock(call,observer_claimed=observer_claimed))
    cleanup['clock_quiescent']=clock_ok
    if status is not None:cleanup['clock_status']=status
    attempt('payment-disable-once',lambda:payment('payment-disable-once','disable'))
    def payment_off():
        off=payment('payment-independent-off','query')['sampling']
        need(off['available'] is True and off['capture_enabled'] is False and off['busy'] is False and off['clear_completed'] is True
            and off['active_captures']==0 and off['retained_records']==0,'Independent payment OFF/clear unavailable')
        cleanup['payment_OFFclear']=True
    attempt('payment-independent-off',payment_off)
    attempt('army-families-disable-once',lambda:sampling_control(call,snapshot,'army-families-disable-once','all',False))
    def army_off():
        rows=sampling_control(call,snapshot,'army-families-independent-off','all')
        need(len(rows)==9 and all(v['installed'] is True and v['available'] is True
            and v['capture_enabled'] is False and v['busy'] is False
            and v['clear_completed'] is True and v['active_captures']==0 and v['retained_records']==0
            for v in rows.values()),'Independent all-family OFF/clear unavailable')
        cleanup['army_families_OFFclear']=True
    attempt('army-families-independent-off',army_off)
    cleanup['OFFclear']=cleanup['payment_OFFclear'] and cleanup['army_families_OFFclear']
    gate.off_clear=cleanup['OFFclear'] and paused and clock_ok
    if gate.off_clear:
        def save_once():
            nonlocal actual_days
            gate.save_verified=False
            try:
                before=snapshot('Save-before')
                start=begin_save(before,retained_client(gate.client))
                saved=call('Save-once','ck3_save_checkpoint',dict(expected_revision=before['revision']))
                # Preserve the actual response before a later request can fail.
                cleanup['Save_result']=saved
                after=snapshot('Save-independent-after')
                cleanup['independent_after']=after
                proof=verify_save(start,saved,after,retained_client(gate.client))
                cleanup.update(ordinary_save_proof=proof,Save=True)
                gate.save_verified=True
                delta=after['date_raw']-expected_start_date_raw
                if delta in (0,24):actual_days=delta//24
            except BaseException as error:
                cleanup['ordinary_save_proof']=unconfirmed(error)
                raise
        attempt('Save-once',save_once)
    return cleanup,errors,actual_days


def cleanup_writer_window(call: Call, snapshot: Snapshot, payment: Payment,
        gate: CloseGate, *, observer_claimed: bool,
        expected_start_date_raw: int) -> tuple[JsonObject,list[str],int|None]:
    """Return finite evidence; Save uses one producer call and native bracketing."""
    return cleanup_result(_cleanup_writer_window_impl(call,snapshot,payment,gate,
        observer_claimed=observer_claimed,expected_start_date_raw=expected_start_date_raw))


def run_case(context, client):
    from ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge.war_payment_observations_v1 import normalize_payment_extras, JOURNAL_KEY
    a = validate_contract(context)
    repo=Path(context['repo_root']).resolve(); output=Path(client.output)
    machine=current_machine_id()
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    need(head==a.source_head,'R08 frozen source differs')
    bridge.write_new(output/'r08-one-opportunity.once.json', dict(machine_id=machine,run_id=context['run_id'],
        source_head=head,start_date_raw=a.expected_start_date_raw,target_date_raw=a.expected_start_date_raw+24,
        unknown_action_never_replayed=True))
    gate=CloseGate(client); legacy=load_controller(); cfg=None; session=None
    packets=bridge.CommonPackets(context,client,output/'r08-common-packets',machine=machine)
    serial=0
    result=dict(machine_id=machine,run_id=context['run_id'],status='ENTERED',actual_days=0,
        exact_day_verified=False,full_R08_qualified=False,business_pass=False,errors=[])
    def call(label,tool,args):
        nonlocal serial
        serial+=1
        return packets.request(a.prefix+'-'+str(serial)+'-'+label,tool,args)[0]
    def snapshot(label):
        frame=call(label,'ck3_take_snapshot',{'include_native_command_history':False})
        need(frame.get('episode_run_id') is None and frame.get('episode_projection')=='native_campaign'
             and frame.get('paused') is True and frame.get('map_ready') is True
             and frame['played_character']['character_id']==a.actor_id, 'R08 fresh ordinary paused owner differs')
        return frame
    def payment(label,mode):
        frame=snapshot(label+'-frame')
        args=dict(expected_revision=frame['revision'],payment_sampling=mode)
        if mode=='enable':args['payment_window_contract']='same_owned_process_no_load_v1'
        body=call(label,bridge.CASH_TOOL,args)
        normalized=normalize_payment_extras(body,snapshot=frame,payment_sampling=mode)
        if mode!='query':need(normalized['war_payment_control_v1']['accepted'] is True,'R08 payment control not accepted')
        return normalized[JOURNAL_KEY]
    try:
        initial=payment('initial-payment','query')
        if initial['sampling']['capture_enabled'] is not True:
            need(a.payment_enable_once_authorized,'Payment OFF: no explicit once-enable authorization')
            prepare_natural_phase(call,snapshot,enable_once_authorized=a.natural_phase_enable_once_authorized)
            payment('payment-enable-once','enable')
        need(payment('payment-independent-on','query')['sampling']['capture_enabled'] is True,
             'Independent payment ON unavailable')
        collected=bridge.collect_current_context(context,client,machine=machine,prefix=a.prefix+'-initial',
            packet_root=output/'r08-initial-inputs',owner_binding_mode=MODE)
        x=collected['expected']
        need(x['date']==a.expected_start_date_raw and x['character_id']==a.actor_id,'R08 predeclared date/actor differs')
        identity=bridge.write_new(output/'R08-COMMON-IDENTITY.actual.json',dict(machine_id=machine,
            run_id=context['run_id'],source_head=head,retained=collected['common_retained_process'],expected=x))
        admission_ref, auth=wait_admission(context,client,a,collected,identity)
        root=output/'r08-writer-control'; watch=root/'watch'
        watch_cfg=dict(repo=str(repo),python=str(client.selection.locations['python']),source_head=head,
            build_dir=a.build_dir,machine_execution_gate=a.machine_execution_gate['path'],
            before_response=collected['before_response']['path'],cash_response=collected['cash_response']['path'],
            owner_binding_mode=MODE,watch_output_root=str(watch),expected=x,timeout_ms=30000,max_slot_hits=128)
        # Gate bytes are checked before the canonical prepare adapter consumes it.
        small_json(a.machine_execution_gate)
        cfg=dict(schema='xar.e04.common-cd-writer-driver-input.v1',run_id=context['run_id'],
            request_prefix=a.prefix,control_root=str(root),common_packet_root=str(output/'r08-observer-packets'),
            watch=watch_cfg,build_card=pin(repo/RESEARCH/'build_card.py'),observer_admission=admission_ref,
            scene_capacity=auth['scene_capacity'])
        cfg['root_identity']=legacy.expected_binding(watch_cfg)
        cap=small_json(cfg['scene_capacity'])
        bound_args=SimpleNamespace(**{**vars(a),'capacity_admission':cfg['scene_capacity']})
        binding=common.actual_binding(client.selection,Path(a.scene_root),client._process,client.read_report(),cap,
            machine_id=machine,source_head=head,a=bound_args)
        binding['saved_campaign_source']=common.bound_saved_campaign_source(client.read_report(),client.frozen,
            client.selection.prepared,binding,sha=a.expected_source_save_sha256,date_raw=a.expected_start_date_raw,
            actor=a.actor_id,state_dir=client.selection.state_dir)
        result['actual_binding']=binding
        guard=lambda c,owner,value:root_window_guard(c,owner,value,a,identity)
        bridge.bind_legacy_driver(legacy,context,client,machine=machine,root_window_guard=guard)
        legacy.SELECTOR=pin(repo/RESEARCH/'select_cd_writers.py')
        cfg_pin=bridge.write_new(output/'R08-DRIVER-INPUT.actual.json',cfg)
        result['driver_input']=cfg_pin
        legacy.prepare(cfg_pin)
        gate.restored=False
        try:
            session,window=legacy.observe_prepared(cfg_pin)
            result['window']=window
        finally:
            # A failed pre-launch guard is safe; an unknown Popen remains unsafe.
            claimed=(root/'observer-start.once.json').exists()
            gate.restored=not claimed or result.get('window',{}).get('safe_to_begin_normal_close') is True
        result['exact_day_verified']=(window.get('day') or {}).get('exact_day_qualified') is True
        result['status']=('NATURAL_OPPORTUNITY_CONSUMED' if not window.get('primary_error')
            and window.get('safe_to_begin_normal_close') is True else 'STOPPED_ERROR_PRESERVED_NO_REPLAY')
    except BaseException as error:
        result.update(status='STOPPED_ERROR_PRESERVED_NO_REPLAY',error=type(error).__name__+': '+str(error))
    finally:
        claimed=(output/'r08-writer-control/observer-start.once.json').exists()
        cleanup,errors,actual_days=cleanup_writer_window(call,snapshot,payment,gate,
            observer_claimed=claimed,expected_start_date_raw=a.expected_start_date_raw)
        result['errors'].extend(errors)
        if actual_days is not None:result['actual_days']=actual_days
        result.update(cleanup=cleanup,native_restore_verified=gate.restored,normal_close_owned_by_shared_entry=True)
        client.checkpoint('R08-WRITER-RESULT',result)
        client.checkpoint('R08-WRITER-TERMINAL',dict(machine_id=machine,run_id=context['run_id'],
            status=result['status'],actual_days=result['actual_days'],exact_day_verified=result['exact_day_verified'],
            OFFclear=cleanup['OFFclear'],Save=cleanup['Save'],native_restore_verified=gate.restored,
            full_R08_qualified=False,business_pass=False,errors=result['errors']))
    return result


def verify_case(context):
    path=Path(context['output'])/'R08-WRITER-TERMINAL.json'
    value=small_json(pin(path)) if path.is_file() else {}
    return dict(actual_days=value.get('actual_days',0),exact_day_verified=value.get('exact_day_verified') is True,
        native_restore_verified=value.get('native_restore_verified') is True,
        full_R08_qualified=False,business_pass=False,normal_close_owned_by_shared_entry=True)
