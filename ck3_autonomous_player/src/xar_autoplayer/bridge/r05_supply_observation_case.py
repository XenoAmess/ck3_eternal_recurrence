"""Bounded R05 observation in the already owned public common-runtime process.

Only existing MCP primitives are used. A completed callback observation is not
an observed updater AL. Actual periodic writer provenance and physical DATA
debits remain the positive predicate; initialization never earns that credit.
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

from . import r05_low_supply_fixture as fixture
from .army_actual_supply_callback_observations_contract import normalize_actual_supply_callback_observations_v1
from .army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1
from .army_actual_supply_callback_observation_summary import summarize_actual_supply_callback_observations_v1
from .army_actual_supply_parent_join_summary import join_actual_supply_parent_writer_observations_v1
from .army_periodic_loss_component_12004 import classify_actual_loss_component_12004
from .episode04_starvation_loss_12004 import _physical_debit
from .army_observer_research_sampling_control import normalize_result as normalize_sampling

SCHEMA = 'xar.r05-initialize-and-observe.v1'
FAMILY = 'natural_phase'
CLOCK_CAPABILITIES = frozenset({
    'game.command.research-arm-tactical-daily-sentinel-v1-N',
    'game.command.research-query-tactical-daily-sentinel-v1',
    'game.command.research-cancel-tactical-daily-sentinel-v1-generation-N',
    'game.command.pause-map', 'game.command.resume-map',
})
SAMPLING_FIELDS = ('step','accepted','status','army_observer_research_sampling_v1','backend_id')
CALLBACK = 'actual_supply_callback_observations_v1'
WRITER = 'actual_loss_writer_observations_v1'
DISPATCH_RETURN = 0x2A9AB4B
STRENGTH_REVISION_DRIFT = 'native army-strength query crossed a snapshot revision'

def is_strength_revision_drift(row):
    # Only a completed explicit error is recoverable. A lost result, another
    # validation error or an action error never authorizes a second request.
    error=row.get('error')
    if row.get('ok') is True or not isinstance(error,str):return False
    message=error.split(': ',1)[-1] if ': ' in error else error
    return message in (STRENGTH_REVISION_DRIFT,
        'Error executing tool ck3_query_army_strengths: '+STRENGTH_REVISION_DRIFT)

class StrengthRevisionDrift(ValueError):
    def __init__(self,proof):
        super().__init__(STRENGTH_REVISION_DRIFT);self.proof=proof

def classify_strength_pre_snapshot_not_started(row):
    """Only the completed R209 diagnostic proves this native query never began."""
    if row.get('ok') is not False or not isinstance(row.get('finished_at'),str) or not row['finished_at']:
        return None
    plan=row.get('plan');args=plan.get('args') if isinstance(plan,dict) else None
    if not (isinstance(args,dict) and plan.get('tool')=='ck3_query_army_strengths'
            and plan.get('continue_on_error') is True and args.get('profile')=='observed_history_full_v1'):
        return None
    prefix=('RuntimeError: MCP tool ck3_query_army_strengths returned an error: '
        'Error executing tool ck3_query_army_strengths: native gameplay step failed: '
        'CK3 army-strength query is unavailable ')
    diagnostic={'worker':'pre_snapshot','native':'not_started','reader':'not_started',
        'army_id':-1,'scope_rows':-1,'baseline_result':-1,'pre_snapshot':0,'paused':0,'map_ready':0,
        'submit':-1,'wait':-1,'reclaim':-1,'enter_result':-1,'entered':-1,
        'native_snapshot':-1,'native_returned':-1,'finish_result':-1,'frame_stable':-1,'run_success':-1}
    suffix='['+';'.join(k+'='+str(v) for k,v in diagnostic.items())+']'
    return diagnostic if row.get('error')==prefix+suffix else None

class StrengthQueryNotStarted(StrengthRevisionDrift):
    def __init__(self,proof):
        ValueError.__init__(self,'native army-strength query not started at pre_snapshot')
        self.proof=proof

def require(ok, why):
    if not ok: raise ValueError(why)

def observation_settings(value):
    require(type(value) is dict, 'explicit observation settings required')
    out = dict(value)
    for key,low,high in (('maximum_actual_days',1,30),('maximum_modal_choices',1,64),
                         ('max_packet_bytes',1024,64*1024*1024),
                         ('max_retained_capture_bytes',4096,1024*1024*1024)):
        require(type(out.get(key)) is int and low <= out[key] <= high, key+' outside finite case bound')
    for key,low,high in (('one_day_timeout_seconds',1,600),('normal_close_reserve_seconds',90,1800),
                         ('cleanup_save_reserve_seconds',30,900),('poll_interval_seconds',0.1,5)):
        v=out.get(key);require(type(v) in (int,float) and math.isfinite(v) and low<=v<=high,key+' invalid')
    require(type(out.get('speed')) is int and 1<=out['speed']<=5, 'native speed1..5 required')
    reserve=out.get('cleanup_capture_reserve_bytes')
    require(type(reserve) is int and 1024<=reserve<out['max_retained_capture_bytes'],
        'explicit cleanup capture reserve required inside original allocation')
    deadline=dt.datetime.fromisoformat(out['deadline_utc'].replace('Z','+00:00'))
    require(deadline.tzinfo is not None, 'explicit UTC-aware original deadline required')
    out['deadline_unix_seconds']=deadline.timestamp()
    return out

def frame_identity(frame):
    d=frame.get('diagnostics',{});p=frame.get('played_character',{})
    return (p.get('character_id'),d.get('bridge_pid'),d.get('connection_generation'),frame.get('episode_run_id'))

def normalized_army(frame,query,*,actor_id,army_id,carmy_id,province_id):
    witness=fixture.target_witness(frame,query,actor_id=actor_id,army_id=army_id,carmy_id=carmy_id,
        province_id=province_id,minimum_physical_current=0)
    army=next(row for row in query['army_strengths'] if row['army_id']==army_id)
    army=dict(army)
    army[CALLBACK]=normalize_actual_supply_callback_observations_v1(army.get(CALLBACK),
        current_army_id=army_id,current_native_carmy_id=carmy_id)
    army[WRITER]=normalize_actual_loss_writer_observations_v1(army.get(WRITER),
        current_regiment_ids=witness['ordered_regiment_ids'])
    for family in (CALLBACK,WRITER):
        row=army[family]
        require(row is not None and row['observer_installed'] is True, family+' actual observer unavailable')
    return {'frame':frame,'query':query,'army':army,'witness':witness}

def history_complete(family,fence):
    oldest,latest=family['oldest_available_sequence'],family['latest_sequence']
    seq=[e['sequence'] for e in family['events']]
    return (latest>=fence and not (latest>fence and oldest>fence+1)
        and family['unattributed_capture_failures']==0 and seq==sorted(set(seq)))

def same_target(before,after):
    a,b=before['witness'],after['witness']
    keys=('actor_id','army_id','carmy_id','province_id','pid','generation',
          'ordered_regiment_ids','data_aliases','raw138_by_persistent')
    require(all(a[k]==b[k] for k in keys), 'target identity/roster/classification changed during observation')
    shape=lambda w:[{k:r[k] for k in ('persistent_regiment_id','chunk_index','maximum_soldiers','state_raw')}
                    for r in w['physical_slots']]
    require(shape(a)==shape(b), 'physical identity/max/state changed; do not treat a replacement as loss')
    require(frame_identity(before['frame'])==frame_identity(after['frame']), 'owned process/episode changed')

def assess_supply_window(before,after,*,exact_day_verified,modal_actions=0):
    """Reuse production normalizers, parent join, physical debit and classifier."""
    same_target(before,after)
    a,b=before['army'],after['army'];start,end=before['frame']['date_raw'],after['frame']['date_raw']
    fences={'callback':a[CALLBACK]['latest_sequence'],'writer':a[WRITER]['latest_sequence']}
    continuity=history_complete(b[CALLBACK],fences['callback']) and history_complete(b[WRITER],fences['writer'])
    summary=summarize_actual_supply_callback_observations_v1(b,after_sequence=fences['callback'])
    joined=join_actual_supply_parent_writer_observations_v1(b,game_version='1.20.0.4',
        executable_sha256=fixture.EXE_SHA,callback_after_sequence=fences['callback'],loss_after_sequence=fences['writer'])
    complete=[]
    for event in b[CALLBACK]['events']:
        passed=event['passed_date_raw64'];prior,later=event['before'],event['after']
        if (event['sequence']>fences['callback'] and event['same_instance_after'] is True and
            event['capture_failure_flags']==0 and event['caller_return_rva']==DISPATCH_RETURN and
            type(passed) is int and start < (passed & 0xffffffff) <= end and
            all(type(v['supply_raw']) is int for v in (prior,later)) and
            all(v.get('province_id')==before['witness']['province_id'] for v in (prior,later))):
            complete.append(event['sequence'])
    by_sequence={e['writer_sequence']:e for e in joined['events']}
    rows=[];qualified=0
    for writer in b[WRITER]['events']:
        if writer['sequence']<=fences['writer']:continue
        component=classify_actual_loss_component_12004(writer)
        join=by_sequence.get(writer['sequence'],{});physical=_physical_debit(writer)
        positive=(continuity and not joined['unknown_reasons'] and exact_day_verified is True and end-start==24 and
            join.get('status')=='joined' and join.get('callback_sequence') in complete and
            component['source_ready'] is True and component['component']=='supply' and
            join.get('strict_below_ten') is True and type(physical) is int and physical>0)
        if positive:qualified+=physical
        rows.append({'writer_sequence':writer['sequence'],'component':component,'parent_join':join,
            'unique_physical_debit_soldiers':physical,'strict_supply_positive':positive})
    physical_values=[r['unique_physical_debit_soldiers'] for r in rows]
    no_writer=not rows
    all_zero=bool(rows) and all(type(v) is int and v==0 for v in physical_values)
    return {'schema':'xar.r05-supply-window.v1','start_date_raw':start,'end_date_raw':end,
        'exact_day_verified':exact_day_verified is True,'fences':fences,'history_continuity_verified':continuity,
        'callback_summary':summary,'parent_join':joined,'classified_writers':rows,
        'complete_natural_callback_sequences':complete,'complete_natural_callback_observed':bool(complete),
        'updater_AL_observed':False,'updater_admission_inferred_from_stock_or_byte':False,
        'no_retained_matching_writer':no_writer,'complete_writer_physical_debit_zero':all_zero,
        'qualified_supply_physical_debit_soldiers':qualified if qualified>0 else None,
        'R05_positive':qualified>0,'whole_army_net_loss_attributed':False,'modal_actions_in_window':modal_actions}

class ObservationIO:
    """One existing public client and its original hold; no second SDK owner."""
    def __init__(self,client,settings,*,context,initialization,clock=time.monotonic,sleep=time.sleep):
        self.client=client;self.settings=observation_settings(settings);self.context=context
        self.initialization=initialization;self.identity=(initialization['independent_after']['actor_id'],
            initialization['pid'],initialization['independent_after']['generation'],initialization['episode'])
        self.actor,self.pid,self.generation,self.episode=self.identity
        self.army=initialization['army_id'];self.carmy=initialization['carmy_id']
        self.province=initialization['independent_after']['province_id']
        self.clock,self.sleep=clock,sleep;self.serial=0;self.capture_bytes=0;self.refs=[];self.active_clock=None
        self.unknown_clock_claim=None
        self.readonly_strength_recoveries=[];self.strength_recovery_failed=False
        self.root=Path(context['output'])/'r05-observe-originals';self.root.mkdir()
        self.modals=[];self.sampling_owned=False;self.sampling_enable_attempted=False
        require(type(getattr(client,'_hold',None)) in (int,float), 'actual common hold must be numeric')
    def room(self,extra=0,*,cleanup=False):
        reserve=self.settings['normal_close_reserve_seconds']+(0 if cleanup else self.settings['cleanup_save_reserve_seconds'])
        require(min(self.client.remaining(),self.settings['deadline_unix_seconds']-time.time())>reserve+extra,
            'original deadline room/normal-close reserve exhausted')
        self.client.guard(reserve=reserve+extra)
    def store(self,label,payload,*,cleanup=False):
        raw=(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n').encode()
        compressed=gzip.compress(raw,mtime=0)
        limit=self.settings['max_retained_capture_bytes']-(0 if cleanup else self.settings['cleanup_capture_reserve_bytes'])
        if len(raw)>self.settings['max_packet_bytes'] or self.capture_bytes+len(compressed)>limit:
            # execute_plan already persists the complete original control rows.
            # A bounded local mirror must never prevent OFF/Save cleanup.
            ref={'label':label,'mirrored':False,'public_original':str(self.client.output/(label+'.actual-results.json')),
                'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),
                'reason':'declared_mirror_allocation_or_packet_bound','cleanup':cleanup}
            self.refs.append(ref)
            require(cleanup,'R05 mirror allocation exhausted; public original retained')
            return ref
        path=self.root/(label+'.json.gz')
        with path.open('xb') as stream:stream.write(compressed)
        self.capture_bytes+=len(compressed)
        ref={'path':str(path),'bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),
            'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),
            'representation':'full structured common SDK control row; transport bytes are not fabricated'}
        self.refs.append(ref);return ref
    def call(self,label,tool,args,*,cleanup=False,readonly_strength=False):
        self.room(cleanup=cleanup);self.serial+=1;name='r05obs-'+str(self.serial).zfill(4)+'-'+label
        reserve=self.settings['normal_close_reserve_seconds']+(0 if cleanup else self.settings['cleanup_save_reserve_seconds'])
        timeout=min(self.context['command_timeout'],self.client.remaining()-reserve)
        step={'id':name,'tool':tool,'args':args,'fresh_revision':False}
        if readonly_strength:
            require(tool=='ck3_query_army_strengths' and args.get('profile')=='observed_history_full_v1'
                and args.get('army_ids')==[self.army], 'readonly error continuation is scoped to this full strength query')
            # Existing public queue and host both honor this flag. It keeps a
            # terminal readonly RED from killing the owned host before cleanup.
            step['continue_on_error']=True
        rows=self.client.execute_plan([step],name,timeout=timeout)
        ref=self.store(name,{'machine_id':self.context['machine_id'],'tool':tool,'arguments':args,'rows':rows},cleanup=cleanup)
        require(len(rows)==1 and rows[0].get('id')==name,'actual common control returned an ambiguous request identity')
        if readonly_strength and is_strength_revision_drift(rows[0]):
            raise StrengthRevisionDrift({'request_id':name,'arguments':args,'original':ref,'terminal_row':rows[0]})
        if readonly_strength and rows[0].get('full_query_not_started_v1') is not None:
            diagnostic=classify_strength_pre_snapshot_not_started(rows[0])
            require(diagnostic is not None and rows[0]['full_query_not_started_v1']['diagnostic']==diagnostic,
                'readonly not-started proof differs from completed original diagnostic')
            raise StrengthQueryNotStarted({'request_id':name,'arguments':args,'original':ref,'terminal_row':rows[0],
                'reason':'pre_snapshot_failed_native_not_started','diagnostic':diagnostic})
        require(rows[0].get('ok') is True and not rows[0].get('error'),
            'actual common control failed; original request is never replayed')
        return rows[0]['result']
    def snapshot(self,label,*,paused=None,cleanup=False):
        frame=self.call(label,'ck3_take_snapshot',{'include_native_command_history':False},cleanup=cleanup)
        self.client.validate_frame(frame,require_event_free=False,require_paused=paused is True)
        require(frame_identity(frame)==self.identity,'current actor/PID/generation/episode differs')
        require(type(frame.get('date_raw')) is int and frame.get('map_ready') is True and
            frame.get('played_character',{}).get('alive') is True,'current living ready map unavailable')
        if paused is not None:require(frame.get('paused') is paused,'actual paused state differs')
        hello=frame.get('diagnostics',{}).get('hello',{})
        require(hello.get('expected_ck3_version',hello.get('game_version'))=='1.20.0.4' and
            str(hello.get('expected_ck3_sha256',hello.get('executable_sha256',''))).lower()==fixture.EXE_SHA,
            'actual exact4 hello binding differs')
        return frame
    def sample(self,label,*,frame=None):
        f=frame or self.snapshot(label+'-snapshot',paused=True)
        def query(current,suffix):
            return self.call(label+suffix,'ck3_query_army_strengths',{
                'army_ids':[self.army],'expected_revision':current['revision'],
                'profile':'observed_history_full_v1'},readonly_strength=True)
        try:
            try:q=query(f,'-full-history')
            except StrengthRevisionDrift as first:
                proof={'first_RED':first.proof,'initial_frame':f,'retry_limit':1,
                    'recovery_reason':first.proof.get('reason','snapshot_revision_drift'),
                    'date_advance_replayed':False,'action_replayed':False,'status':'fresh_frame_pending'}
                self.readonly_strength_recoveries.append(proof)
                # First RED is already durable. Persist both actual frames even
                # if the fresh one fails the same-date/identity admission.
                fresh=self.snapshot(label+'-readonly-fresh-snapshot',paused=True)
                proof['fresh_frame']=fresh
                proof['frame_original']=self.store(label+'-readonly-rebound-frames',proof)
                require(f.get('paused') is True and fresh.get('date_raw')==f.get('date_raw') and
                    frame_identity(f)==frame_identity(fresh)==self.identity,
                    'readonly strength rebound changed date/paused/owned identity')
                require(all(x.get('active_event') is None and x.get('pending_character_interaction') is None
                    for x in (f,fresh)), 'readonly strength rebound found an unresolved modal')
                def target(current):
                    rows=[a for a in current.get('player_armies',[]) if a.get('army_id')==self.army]
                    require(len(rows)==1,'readonly strength rebound target missing/ambiguous')
                    return {k:rows[0].get(k) for k in ('army_id','owner_character_id','current_province_id')}
                require(target(f)==target(fresh)=={'army_id':self.army,'owner_character_id':self.actor,
                    'current_province_id':self.province}, 'readonly strength rebound owner/location changed')
                proof['status']='second_readonly_query_pending'
                q=query(fresh,'-full-history-rebound-once');f=fresh
                proof['status']='second_readonly_query_completed'
            value=normalized_army(f,q,actor_id=self.actor,army_id=self.army,carmy_id=self.carmy,province_id=self.province)
            return value
        except BaseException:
            # The outer unknown-day convergence must not create a third full
            # request after a second drift, changed frame or lost query result.
            self.strength_recovery_failed=True
            raise
    def sampling(self,mode,*,cleanup=False):
        frame=self.snapshot('sampling-'+mode+'-frame',paused=True,cleanup=cleanup)
        args={'observer_family':FAMILY,'expected_revision':frame['revision']}
        if mode!='query':args['enabled']=mode=='enable'
        tool='ck3_query_army_observer_research_sampling_v1' if mode=='query' else 'ck3_set_army_observer_research_sampling_v1'
        result=self.call('sampling-'+mode,tool,args,cleanup=cleanup)
        step=('query' if mode=='query' else 'enable' if mode=='enable' else 'disable')+'-army-observer-research-sampling-v1'
        normalized=normalize_sampling({k:result[k] for k in SAMPLING_FIELDS},expected_step=step,observer_family=FAMILY)
        require(result.get('queried_revision')==frame['revision'] and result.get('queried_native_revision')==frame['native_revision']
            and result.get('queried_date_raw')==frame['date_raw'],'sampling control did not bind the actual paused frame')
        return normalized['army_observer_research_sampling_v1'][FAMILY]
    def clock_status(self,*,cleanup=False):
        from .native_driver import _normalize_tactical_daily_sentinel_status
        result=self.call('clock-query','ck3_execute_step',{'step':'research-query-tactical-daily-sentinel-v1','expected_revision':None},cleanup=cleanup)
        return _normalize_tactical_daily_sentinel_status(result['tactical_daily_sentinel'])
    def claim(self,label,value):
        path=self.root/(label+'.once-claim.json')
        with path.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump({'machine_id':self.context['machine_id'],'episode':self.episode,'pid':self.pid,
                'status':'claimed_result_unknown_no_replay',**value},stream,ensure_ascii=False,indent=2)
            stream.write('\n');stream.flush()
            import os;os.fsync(stream.fileno())
        return path
    def exact_day(self,before):
        from .native_driver import _normalize_tactical_daily_sentinel_status,_validate_tactical_daily_sentinel_arm,_validate_tactical_daily_sentinel_stop
        self.room(self.settings['one_day_timeout_seconds'])
        start=before['frame']['date_raw'];target=start+24;speed=self.settings['speed'];self.active_clock=None
        claim=self.claim('day-'+str(start),{'starting_date_raw':start,'target_date_raw':target})
        self.unknown_clock_claim={'start':start,'target':target,'claim':str(claim)}
        step=f'research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-{speed}-mode-terminal-a-0'
        result=self.call('arm-day','ck3_execute_step',{'step':step,'expected_revision':before['frame']['revision']})
        armed=_normalize_tactical_daily_sentinel_status(result['tactical_daily_sentinel'])
        _validate_tactical_daily_sentinel_arm(result,armed,arm_step=step,starting_date_raw=start,target_date_raw=target,
            speed=speed,mode='terminal_or_sentinel',watch_army_ids=(),sentinel_scope='exact_one_day')
        self.active_clock={'armed':armed,'start':start,'target':target,'claim':str(claim)}
        self.unknown_clock_claim=None
        self.claim('day-'+str(start)+'-initial-resume',{'generation':armed['generation']})
        self.call('resume-day','ck3_execute_step',{'step':'resume-map','expected_revision':None})
        limit=self.clock()+self.settings['one_day_timeout_seconds'];modal_count_before=len(self.modals)
        while self.clock()<limit:
            self.room();frame=self.snapshot('wait-day')
            require(start<=frame['date_raw']<=target,'actual day overshot/reversed; no replay or extra day')
            modal=frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None
            if modal and frame.get('paused') is not True:
                self.call('known-modal-pause-once','ck3_execute_step',{'step':'pause-map','expected_revision':None})
                frame=self.snapshot('known-modal-paused',paused=True)
                require(start<=frame['date_raw']<=target,'modal pause crossed original clock window')
            if frame.get('paused') is True:
                if frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
                    modal_date=frame['date_raw']
                    frame=self.handle_modals(frame)
                    require(frame['date_raw']==modal_date,'modal handling advanced game date')
                    if frame['date_raw']<target:
                        status=self.clock_status()
                        require(status['generation']==armed['generation'] and status['state']=='armed' and
                            status['starting_date_raw']==start and status['target_date_raw']==target,
                            'early modal did not retain the original armed clock')
                        self.claim('day-'+str(start)+'-known-modal-resume-'+str(len(self.modals)),
                            {'generation':armed['generation'],'resolved_modal_count':len(self.modals),
                             'known_early_pause':True,'new_Arm':False})
                        self.call('continue-original-clock','ck3_execute_step',{'step':'resume-map','expected_revision':None})
                if frame['date_raw']==target:
                    status=self.clock_status()
                    _validate_tactical_daily_sentinel_stop(status,arm_status=armed,starting_date_raw=start,
                        target_date_raw=target,ending_date_raw=frame['date_raw'],elapsed_days=1,speed=speed,
                        mode='terminal_or_sentinel',watch_army_ids=())
                    self.active_clock=None
                    return frame,{'armed':armed,'stopped':status,'exact_day_verified':True,
                        'modal_actions':len(self.modals)-modal_count_before,'Arm_reissued':False}
            self.sleep(self.settings['poll_interval_seconds'])
        raise TimeoutError('original exact-day wait unresolved; preserve Arm/Resume, never replay')

    def handle_modals(self,frame):
        """Known registry first; otherwise existing first-rendered/left policy."""
        from .event_window_context_contract import normalize_current_event_window_context_v1
        from ..vanilla_events.policy import recommend_registered_vanilla_event_option_v1
        from ..vanilla_events.unhandled_fallback import plan_unhandled_event_fallback_v1,capture_unhandled_event_before_v1,capture_unhandled_event_after_v1
        from ..pending_interaction_fallback import plan_pending_interaction_left_reply_v1,capture_pending_interaction_before_v1,capture_pending_interaction_after_v1
        from .pending_character_interaction_context_contract import normalize_pending_character_interaction_context_v1
        from ..strategy import _degraded_pending_interaction_decision,_degraded_pending_interaction_plan
        while frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
            require(len(self.modals)<self.settings['maximum_modal_choices'],'finite modal budget exhausted')
            self.room();active=frame.get('active_event');pending=frame.get('pending_character_interaction');ticket=None
            # Native action strings expand from the current modal, not from
            # the event-free capability snapshot taken before day one.
            current_caps=self.call('modal-current-capabilities','ck3_get_capabilities',{})
            steps=set(current_caps.get('action_steps',[]))
            if active is not None:
                instance=active['instance_id'];kind='event'
                result=self.call('event-context','ck3_query_current_event_window_context_v1',{
                    'event_instance_id':instance,'expected_revision':frame['revision']})
                require(result.get('accepted') is True and result.get('queried_revision')==frame['revision'] and
                    result.get('queried_native_revision')==frame['native_revision'] and result.get('queried_snapshot_id')==frame['snapshot_id'],
                    'event context crossed actual frame')
                typed=normalize_current_event_window_context_v1(result['current_event_window_context'],
                    expected_event_instance_id=instance,expected_date_raw=frame['date_raw'],expected_snapshot_revision=frame['native_revision'])
                decision=recommend_registered_vanilla_event_option_v1(typed,played_character_id=self.actor,
                    snapshot_option_count=active['option_count'],ck3_build='1.20.0.4',played_character=frame['played_character'])
                if decision.get('status')=='recommended':
                    plan={'selected_step':'select-event-option-'+str(decision['selected_option_number']),'event_decision':decision}
                else:
                    plan=plan_unhandled_event_fallback_v1(snapshot=frame,event_context=typed,
                        event_summary={'instance_id':instance,'option_count':active['option_count']},registry_decision=decision,action_steps=steps)
                    require(plan is not None and plan.get('selected_step') is not None,'first rendered event option unavailable')
                    ticket=capture_unhandled_event_before_v1(self.context['state_dir'],{'plan':plan,'snapshot_id':frame['snapshot_id'],'revision':frame['revision']})
                    decision=plan['event_decision']
                number=decision['selected_option_number']
                require('select-event-option-'+str(number) in steps,'actual native option action not advertised')
                tool='ck3_select_event_option';args={'event_instance_id':instance,'option_number':number,'expected_revision':frame['revision']}
            else:
                instance=pending['instance_id'];kind='interaction'
                result=self.call('interaction-context','ck3_query_pending_character_interaction_context_v1',{
                    'pending_interaction_id':instance,'expected_revision':frame['revision']})
                require(result.get('accepted') is True and result.get('queried_revision')==frame['revision'] and
                    result.get('queried_native_revision')==frame['native_revision'] and
                    result.get('queried_snapshot_id')==frame['snapshot_id'],'interaction context crossed actual frame')
                typed=normalize_pending_character_interaction_context_v1(result['pending_character_interaction_context'],
                    expected_pending_interaction_id=instance,expected_date_raw=frame['date_raw'],expected_snapshot_revision=frame['native_revision'])
                known=_degraded_pending_interaction_decision(pending,typed,snapshot=frame,
                    active_wars=frame.get('active_wars',[]),available_steps=steps)
                decision=known['decision'];known_ready=(str(decision.get('classification','')).startswith('known_') and decision.get('selected_step') is not None)
                if known_ready:plan=_degraded_pending_interaction_plan(known)
                else:
                    plan=plan_pending_interaction_left_reply_v1(snapshot=frame,context=typed,
                        original_plan=_degraded_pending_interaction_plan(known),action_steps=steps,registry_state_dir=self.context['state_dir'])
                    require(plan is not None and plan.get('selected_step') is not None,'native left reply unavailable')
                    selected=plan['unhandled_interaction_fallback']['selection']
                    require(selected['position'] in ('left','only'),'ordinary left is disabled; do not substitute right accept')
                    ticket=capture_pending_interaction_before_v1(self.context['state_dir'],{'plan':plan,'snapshot_id':frame['snapshot_id'],'revision':frame['revision']})
                    decision=plan['decision']
                step=plan['selected_step']
                require(step in steps,'interaction action not advertised')
                tool='ck3_acknowledge_pending_character_interaction' if step=='acknowledge-pending-character-interaction' else 'ck3_reply_pending_character_interaction'
                args={'interaction_instance_id':instance,'expected_revision':frame['revision']}
                if tool=='ck3_reply_pending_character_interaction':
                    require(step in ('accept-pending-character-interaction','reject-pending-character-interaction'),'unhandled dedicated interaction action')
                    args['accept']=step=='accept-pending-character-interaction'
            name='modal-'+str(len(self.modals)+1).zfill(3)
            self.client.checkpoint(name+'-decision',{'machine_id':self.context['machine_id'],'typed_context':typed,
                'plan':plan,'actor':self.actor,'date_raw':frame['date_raw'],'native_instance':instance,'dispatch_attempted':False})
            self.claim(name,{'kind':kind,'instance_id':instance,'tool':tool,'arguments':args})
            ack=None
            try:
                ack=self.call(name+'-select-once',tool,args)
                after=self.snapshot(name+'-independent-after',paused=True)
                require(frame_identity(frame)==frame_identity(after) and after['date_raw']==frame['date_raw'],'modal action crossed original owner/date')
                field='active_event' if kind=='event' else 'pending_character_interaction'
                gone=(after.get(field) or {}).get('instance_id')!=instance
                require(gone,'original native modal remains after once action; never resubmit')
                # Event ACK accepted and interaction accept:false have distinct meanings.
                # Common control row ok=True proves transport execution only.
                # In reply receipts accepted=False can encode accept=False.
                acked=ack.get('accepted') is True if kind=='event' else None
                entry={'kind':kind,'instance_id':instance,'typed_context':typed,'plan':plan,'ack':ack,
                    'control_row_ok':True,'command_acknowledged':acked,
                    'interaction_accept_argument':args.get('accept') if kind=='interaction' else None,
                    'interaction_accepted_field_is_not_dispatch_success':kind=='interaction',
                    'old_window_gone_independent':gone,'after_frame':after,
                    'replay_permitted':False,'offline_followup_required':ticket is not None}
                self.modals.append(entry)
                if kind=='event':capture_unhandled_event_after_v1(ticket,outcome={'result':ack})
                else:capture_pending_interaction_after_v1(ticket,outcome={'result':ack})
                frame=after
            except BaseException as error:
                if kind=='event':capture_unhandled_event_after_v1(ticket,outcome={'result':ack},error=error)
                else:capture_pending_interaction_after_v1(ticket,outcome={'result':ack},error=error)
                raise
        return frame

    def cleanup(self):
        result={'sampling_OFF_clear_verified':False,'sampling_owned':self.sampling_owned,
            'save_submitted':False,'save_verified':False,'errors':[]}
        try:
            frame=self.snapshot('cleanup-current',cleanup=True)
            if frame.get('paused') is not True:
                self.call('cleanup-pause-once','ck3_execute_step',{'step':'pause-map','expected_revision':None},cleanup=True)
                frame=self.snapshot('cleanup-paused',paused=True,cleanup=True)
            if self.active_clock is not None:
                status=self.clock_status(cleanup=True);armed=self.active_clock['armed']
                require(status['generation']==armed['generation'],'cleanup clock generation differs')
                if status['state']=='armed':
                    step='research-cancel-tactical-daily-sentinel-v1-generation-'+str(armed['generation'])
                    receipt=self.call('cleanup-cancel-original-clock','ck3_execute_step',{'step':step,'expected_revision':None},cleanup=True)
                    require(receipt.get('accepted') is True and receipt.get('status')=='canceled','original clock cancel not verified')
                result['original_clock_status']=status
            elif self.unknown_clock_claim is not None:
                # Read-only convergence after unknown Arm; no invented arm
                # receipt, generation claim, Resume or cancel of another clock.
                result['unknown_arm_readonly_clock']=self.clock_status(cleanup=True)
                result['unresolved_arm_claim']=self.unknown_clock_claim
        except BaseException as error:result['errors'].append('clock/pause: '+type(error).__name__+': '+str(error))
        disable_known=False
        if self.sampling_enable_attempted:
            try:
                self.sampling('disable',cleanup=True);disable_known=True
            except BaseException as error:
                result['disable_request_result_unknown']=True
                result['errors'].append('sampling disable: '+type(error).__name__+': '+str(error))
        # Fresh readback is mandatory even if admission failed before enable.
        # Never disable a family we did not attempt to acquire.
        try:
                query=self.sampling('query',cleanup=True)
                # A known clear_pending after a completed disable is distinct
                # from an unknown request: clear once more only after busy=0.
                if disable_known and query['capture_enabled'] is False and query['busy'] is False and query['clear_completed'] is False:
                    self.sampling('disable',cleanup=True);query=self.sampling('query',cleanup=True)
                result['sampling_final']=query
                result['sampling_OFF_clear_verified']=(query['installed'] and query['available'] and
                    not query['capture_enabled'] and not query['busy'] and query['clear_completed'] and query['retained_records']==0)
        except BaseException as error:result['errors'].append('sampling readback: '+type(error).__name__+': '+str(error))
        try:
            frame=self.snapshot('final-save-frame',paused=True,cleanup=True)
            self.claim('final-normal-save',{'date_raw':frame['date_raw'],'sampling_OFF_clear_verified':result['sampling_OFF_clear_verified']})
            result['save_submitted']=True
            saved=self.call('final-normal-save-once','ck3_save_checkpoint',{'expected_revision':frame['revision']},cleanup=True)
            result['normal_save_receipt']=saved
            result['save_verified']=(saved.get('accepted') is True and saved.get('step')=='save-checkpoint'
                and saved.get('checkpoint',{}).get('status')=='saved')
        except BaseException as error:result['errors'].append('Save: '+type(error).__name__+': '+str(error))
        return result

def observe_initialized_supply(client,settings,*,context,initialization,clock=time.monotonic,sleep=time.sleep):
    require(initialization.get('assessment',{}).get('status')=='prepared_low_stock' and
        initialization['assessment']['physical_soldiers_unchanged'] is True,'strictly qualified initializer required before natural observation')
    io=ObservationIO(client,settings,context=context,initialization=initialization,clock=clock,sleep=sleep)
    result={'schema':SCHEMA,'machine_id':context['machine_id'],'episode':io.episode,'pid':io.pid,'army_id':io.army,
        'carmy_id':io.carmy,'initializer_at_zero':initialization['assessment']['initialization_at_zero'],
        'initialized_stock_raw':initialization['assessment']['actual_after_stock_raw'],
        'status':'not_started','verified_actual_days':0,'windows':[],'R05_positive':False,'new_updater_AL_witness':False}
    before=None
    try:
        io.room(io.settings['one_day_timeout_seconds'])
        capabilities=io.call('capabilities','ck3_get_capabilities',{})
        require(CLOCK_CAPABILITIES<=set(capabilities.get('bridge_capabilities',[])),'actual native exact-clock capabilities missing')
        context['action_steps']=capabilities.get('action_steps',[])
        initial=io.sampling('query')
        require(initial['installed'] and initial['available'] and not initial['capture_enabled'] and
            not initial['busy'] and initial['clear_completed'],'natural-phase sampler not exclusively available OFF/clear')
        io.sampling_enable_attempted=True
        enabled=io.sampling('enable');require(enabled['capture_enabled'] and not enabled['busy'],'sampling enable not independently available')
        readback=io.sampling('query');require(readback['capture_enabled'] and readback['epoch']==enabled['epoch'],'sampling enable readback differs')
        io.sampling_owned=True;result['status']='observing'
        for day in range(1,io.settings['maximum_actual_days']+1):
            io.room(io.settings['one_day_timeout_seconds'])
            before=io.sample('day-'+str(day).zfill(2)+'-before')
            frame,clock_receipt=io.exact_day(before)
            after=io.sample('day-'+str(day).zfill(2)+'-after',frame=frame)
            sampling=io.sampling('query')
            require(sampling['capture_enabled'] and sampling['epoch']==enabled['epoch'],
                'owned sampler epoch/enabled state changed during day')
            window=assess_supply_window(before,after,exact_day_verified=True,modal_actions=clock_receipt['modal_actions'])
            window['clock']=clock_receipt;window['actual_day']=day
            result['windows'].append(window);result['verified_actual_days']=day
            if not window['history_continuity_verified']:
                result['status']='history_gap_or_capture_failure';break
            if window['complete_natural_callback_observed']:
                result['R05_positive']=window['R05_positive'];result['status']=('strict_supply_physical_positive' if window['R05_positive'] else
                    'first_complete_callback_no_matching_writer' if window['no_retained_matching_writer'] else
                    'first_complete_callback_physical_debit_zero' if window['complete_writer_physical_debit_zero'] else
                    'first_complete_callback_no_qualified_supply_debit')
                break
        else:result['status']='actual_day_cap_without_complete_matching_callback'
    except BaseException as error:
        result['status']='unknown_or_incomplete_observation_no_replay'
        result['error']={'type':type(error).__name__,'message':str(error)}
        if before is not None and not io.strength_recovery_failed:
            try:
                f=io.snapshot('unresolved-day-readonly-after')
                if f.get('paused') is True and f.get('active_event') is None and f.get('pending_character_interaction') is None:
                    after=io.sample('unresolved-day-full-history-after',frame=f)
                    result['unverified_day_readonly_assessment']=assess_supply_window(before,after,exact_day_verified=False)
            except BaseException as recovery_error:
                result['readonly_recovery_error']={'type':type(recovery_error).__name__,'message':str(recovery_error)}
    finally:
        result['cleanup']=io.cleanup();result['originals']=io.refs;result['modals']=io.modals
        result['readonly_strength_recoveries']=io.readonly_strength_recoveries
        result['capture_compressed_bytes']=io.capture_bytes;result['normal_close_pending']=True
        result['replay_permitted']=False
        client.checkpoint('r05-initialize-and-observe-result',result)
    return result
