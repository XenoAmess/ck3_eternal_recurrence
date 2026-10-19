"""Finite same-Game C5 SDK rotation after source-proven251 pre-submit blockage."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'


def require(ok,reason):
    if not ok:raise ValueError('publisher251 warm bootstrap denied: '+reason)


def checked(ref,limit=65536):
    path=Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)<=limit and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],
        'exact retained input differs: '+str(path))
    return json.loads(raw)


def warm_inputs(admission):
    require(admission['schema']=='xar.publisher251-sameGame-C5/v1' and admission['machine_id']==MACHINE,
        'explicit same-Game C5 admission')
    require(admission['post_close']['sha256']=='fd2a83b0fffbdf8c98551306a91463a9ab76ea08db202448f89cb87c94a4a4f7'
        and admission['source_proof']['sha256']=='dfe9834d06efecba05681f18746108b8de8891c535db2702a3f7c7736774de33',
        'actual post-close and251 dispatch proof required')
    close=checked(admission['post_close']);proof=checked(admission['source_proof'])
    require(close['machine_id']==MACHINE and close['Game_pid']==153556
        and close['Game_creation_filetime']==134368602545256920 and close['old_pair_signaled'] is True
        and close['Queue_exit_code']==1 and close['App_exit_code']==0 and close['normal_dual0_claimed'] is False
        and close['closed_Driver']['bytes']==1308498
        and close['closed_Driver']['sha256']=='1413f3c7f8c799a01be9e55d3b2aea805092cf8d7bc6f0981366d2007961579e',
        'exact honest C4 closure/closed Driver provenance differs')
    old=checked(close['actual_sdk_closed'])
    expected={'sdk_queue':(42800,134368610358548563,1),'sdk_application':(150132,134368610381151161,0)}
    require(old['normal'] is False and old['launcher_exit_code']==1 and old['Game_stopped'] is False
        and old['recording_stopped'] is False and len(old['processes'])==2 and all(
            (row['pid'],row['creation_filetime'],row['exit_code'])==expected.get(row['role'])
            and row['kernel_exit_observed'] is True and row['wait_result']==0 and row['observation_error'] is None
            for row in old['processes']), 'retained exact SDK process births/exits differ')
    refs={Path(ref['source']).name:ref for ref in close['retained_small_sources']}
    require(refs['ROOT-CUMULATIVE-LOOP-STATE.json']['sha256']=='994f364260b6ea53e290e9439e55220d0c0d5a85046cca3d8ba70cbbc529b69c'
        and refs['ROOT-GOVERNANCE-RESULT-STATE.json']['sha256']=='a820c674cc1f88dd5bad89c29be2a61ae0bd055c6d88bc4e127a74069bf5b4f8',
        'actual98 state/governance pins differ')
    state=checked(refs['ROOT-CUMULATIVE-LOOP-STATE.json']);gov=checked(refs['ROOT-GOVERNANCE-RESULT-STATE.json'])
    require(state['completed_cycles']==98 and state['start_date_raw']==53144328
        and state['before']['date_raw']==53146896 and state['before']['native_revision']==60
        and state['before']['actor_character_id']==31254 and state['before']['episode_run_id']=='native-31254-6271ac8cd441'
        and state['pending_cycle']==close['retained_pending_cycle'] and state['pending_cycle']['auto_sequence']==251
        and state['pending_cycle']['global_turn']==99 and state['pending_cycle']['stage']=='auto_unsettled'
        and state['pending_cycle']['before']==state['before'] and state['checkpoint_dirty_since_save'] is True
        and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and state['actual_saved_checkpoint']==close['actual_last_saved_checkpoint']
        and state['actual_saved_checkpoint']['date_raw']==53145792
        and state['actual_saved_checkpoint']['sha256']=='cb385a8fd4be62b6e553a4d0a5575d50886e8d894dc8ed83173d9ae851d4075d',
        'exact98/day107/pending99/dirty/lastSaved61 state differs')
    boundary=proof['boundary']
    require(proof['machine_id']==MACHINE and boundary['parent_sequence']==251 and boundary['callback_index']==1
        and boundary['selected_step']=='query-war-results-window-v1'
        and boundary['plan_sha256']=='0532a95440118d7d9c8bd47b2d9901b85310621310a793bd26b114ebf062508b'
        and boundary['text_publication_ack_present'] is False and boundary['selected_driver_dispatch_occurred'] is False
        and boundary['full_AUTO_or_query_completion_credit'] is False,'selected251 dispatch exclusion not proven')
    for ref in close['retained_small_sources']:
        if Path(ref['path']).name in ('active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json'):
            checked(ref,16384)
    return state,gov,close


def bind_warm_opening(body,*,state,launch,lifecycle,frame):
    actual=frame(body,semantic=True,expected_lifecycle=lifecycle)
    before=state['before'];diag=body.get('diagnostics') or {};hello=diag.get('hello') or {}
    require(all(actual[key]==before[key] for key in ('date_raw','actor_character_id','episode_run_id'))
        and actual['native_revision']>=before['native_revision']
        and actual['snapshot_id']=='native:'+str(actual['native_revision'])
        and diag.get('bridge_pid')==hello.get('pid')==launch['pid']==153556
        and diag.get('pipe_name')==launch['pipe'] and diag.get('connected') is True
        and type(diag.get('connection_generation')) is int and diag['connection_generation']>0
        and diag['connection_generation']==hello.get('connection_generation')
        and hello.get('ck3_build_match') is True and hello.get('game_adapter_id')=='ck3-1.20.0.4-msvc-x64'
        and hello.get('game_adapter_status')=='ready' and body.get('campaign_goal')==state['campaign_goal_anchor']
        and body.get('active_event') is None and body.get('pending_character_interaction') is None,
        'actual same-Game day107 warm frame/Native/goal differs')
    return actual


def project_warm_state(state,opening,source,proof):
    changed=copy.deepcopy(state)
    changed.update(before=copy.deepcopy(opening),before_metrics_response=str(source),pending_cycle=None,
        before_source_kind='actual_sameGame_warm_semantic_snapshot')
    changed['publisher251_warm_opening']={'frame':copy.deepcopy(opening),'semantic_response':str(source),
        'source_proof':proof,'ordinary_cycle_credit':0,'game_day_credit':0,'query_completion_credit':0,
        'original251_AUTO_replayed':False,'selected251_dispatch_occurred':False}
    return changed


def make_publisher251_warm_queue_v1(base,env,*,admission_path):
    class Publisher251WarmQueue(base):
        def preflight(self):
            from root_continuous_segment_auto_c5 import verify_segment
            from root_decision_text_api_c5 import load_api,started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission=env['read'](Path(admission_path),65536);state,gov,close=warm_inputs(admission)
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir())),
                'new empty normal recorded C5 Queue required')
            for key,name in (('queue_source','root_p37c5_sdk_queue.py'),('entry_source','root_p37c5_mcp_entry.py'),
                    ('native_binding_source','root_native_build_binding_p37c4.py')):
                ref=admission[key];source=Path(ref['path']).resolve(strict=True);raw=source.read_bytes()
                require(source==(env['N']/name).resolve() and len(raw)<=1024**2 and len(raw)==ref['bytes']
                    and hashlib.sha256(raw).hexdigest()==ref['sha256'],'current C5 source differs: '+name)
            require(Path(env['__file__']).resolve()==Path(admission['queue_source']['path']).resolve()
                and self.launch['pid']==153556 and self.launch['creation_filetime']==134368602545256920
                and admission['next_sequence']==252,'actual same-Game C5/next252 source views required')
            self.job,self.record_started,self.first=verify_segment(env['N'],env['R'],self.launch,
                self.record_job,self.args.first_frame_admission,env['read'],env['aware'],env['now'])
            api=load_api(env['N']);checked(admission['publisher_started'],16384)
            require(api.process_identity(153556)['creation_filetime']==134368602545256920
                and started_reference(env['N'],api)==admission['publisher_started'],'actual paired C5 publisher/Game differs')
            absence=checked(admission['mod_absence'])
            require(absence['machine_id']==MACHINE and absence['game_pid']==153556
                and absence['game_creation_filetime']==134368602545256920,'physical same-Game mod absence differs')
            self.expected_lifecycle_binding=bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest),'verified_mod_absence':absence},
                lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding==state['actual_saved_checkpoint']['succession_lifecycle'],
                'same-Game environment lifecycle differs')
            freeze=checked(admission['sdk_freeze'],2*1024**2)
            require(Path(admission['sdk_freeze']['path']).name=='ROOT-FINAL-SDK-FREEZE-P37C5.json'
                and freeze['business_source_commit']=='6ebbffcdebe3e30353513e0984572ebc701daa2e'
                and Path(admission['current_map_admission']).resolve()==(env['N']/'ROOT-CAMPAIGN-MAP-ADMITTED-C5.json').resolve(),
                'C5 freeze/map must reference current publisher session')
            self.frozen_head=freeze['git_head'];self.frontend_done=len(env['FRONTEND']);self.checkpoint_mode=True
            self.next_sequence=252;self.initial_frame=self.initial_save=None
            self._publisher251_warm={'phase':'semantic','admission':admission,'state':state,'gov':gov,'close':close}
            self.guard(reserve=False)

        async def call(self,session,request,path):
            if self._publisher251_warm['phase']=='semantic' and request.get('tool')==env['SEMANTIC']:
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c5_overlay_relay import relay_compact
                return await startup_readiness_call(self,session,request,path,env,relay_compact=relay_compact)
            return await super().call(session,request,path)

        def check_before(self,tool,arguments):
            warm=self._publisher251_warm
            if warm['phase']!='ready':
                expected=env['SEMANTIC'] if warm['phase']=='semantic' else env['CAPABILITIES']
                require(tool==expected and arguments=={},'one new SEM252 then CAP253 required')
                return
            return super().check_before(tool,arguments)

        def check_after(self,tool,arguments,body):
            warm=self._publisher251_warm
            if warm['phase']=='semantic' and tool==env['SEMANTIC']:
                attempt=self.current_attempt;row=attempt['row'];request=attempt['request']
                require(request=={'sequence':252,'tool':env['SEMANTIC'],'arguments':{}}
                    and row['request']==request and row.get('client_error') is None
                    and row['result']['is_error'] is False and row['result']['result_type']=='complete'
                    and env['decoded'](row)==body and self.next_sequence==252,'actual readiness252 context required')
                opening=bind_warm_opening(body,state=warm['state'],launch=self.launch,
                    lifecycle=self.expected_lifecycle_binding,frame=env['frame'])
                source=Path(attempt['response']).resolve(strict=True)
                require(source.is_relative_to(env['N'].resolve()) and env['read'](source,env['REPLY_RESERVE'])==row,
                    'actual252 observer attempt source differs')
                from root_score_month_samples_c4 import observe_semantic
                observe_semantic(env['N'],body,self.launch,source)
                self.initial_frame=copy.deepcopy(opening);self.semantic=body
                self.cold_semantic_response_path=str(env['OUTBOX']/'0252-1-result.json')
                warm.update(phase='capabilities',opening=opening,semantic_response=self.cold_semantic_response_path)
                return
            if warm['phase']=='capabilities' and tool==env['CAPABILITIES']:
                control=body.get('native_session_control') or {};before=warm['state']['before']
                require(body.get('episode_run_id')==before['episode_run_id'] and body.get('episode_character_id')==before['actor_character_id']
                    and body.get('episode_identity_pending') is False and body.get('one_life_terminal') is False
                    and control.get('driver_state_restored') is True and control.get('driver_state_restore_kind')=='same_pid_hot'
                    and control.get('episode_binding_state')=='active_resumed' and control.get('driver_state_error') is None
                    and control.get('cold_candidate_rejection') is None,'actual same_pid_hot original-Game CAP required')
                self.full_loop_state=project_warm_state(warm['state'],warm['opening'],warm['semantic_response'],warm['admission']['source_proof'])
                self.initial_save=copy.deepcopy(warm['state']['actual_saved_checkpoint'])
                self.governance_result_state=copy.deepcopy(warm['gov']['state']);self.lifestyle_pending_focus=copy.deepcopy(warm['gov']['pending_focus'])
                pin=checked(warm['admission']['classifier_pin'],16384);self.result_classifier=env['load_cold_result_classifier']()
                path=Path(self.result_classifier.__code__.co_filename).resolve(strict=True);raw=path.read_bytes()
                require(path==Path(pin['source']).resolve() and len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                    'actual C5 classifier source differs')
                self.result_classifier_pin={key:pin[key] for key in ('source','sha256')}
                self.capabilities_verified=self.cold_readiness_verified=self.checkpoint_bootstrap_verified=True
                self.halted=self.halt_cause=self.current_attempt=self.held_control=None;warm['phase']='ready'
                self.persist_loop_state()
                env['atomic'](env['Q']/'ROOT-PUBLISHER251-WARM-BOUND.json',{'schema':'xar.publisher251-warm-bound/v1',
                    'machine_id':MACHINE,'opening_frame':warm['opening'],'semantic_response':warm['semantic_response'],
                    'completed_cycles':98,'game_days':107,'ordinary_cycle_credit':0,'query_completion_credit':0,
                    'original251_replayed':False,'selected251_dispatch_occurred':False,'old_sdk_normal':False,
                    'last_saved_date_raw':self.initial_save['date_raw'],'checkpoint_dirty_since_save':True,
                    'source_proof':warm['admission']['source_proof'],'post_close':warm['admission']['post_close']},limit=16384)
                return
            return super().check_after(tool,arguments,body)

    return Publisher251WarmQueue
