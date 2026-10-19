"""C6 same-Game bootstrap and once-only original MET286 supply; inherit settlement."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
SCHEMA='xar.sameGame-completed-MET286-C6/v1'
BUSINESS='13eb02ce80249921b1ac1313507793c382e08448'


def require(ok,why):
    if not ok:raise ValueError('completedMET286 warm resume denied: '+why)


def checked(ref,limit=262144):
    path=Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)<=limit and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],
        'exact input differs: '+str(path))
    return json.loads(raw)


def validate_inputs(admission):
    require(admission['schema']==SCHEMA and admission['machine_id']==MACHINE,'finite C6/MET286 admission')
    require(admission['failure_packet']['sha256']=='2a4d013976ff6b6657261b8ad45a45960c8f2a9cefaaf2f434aac5b773fc1ae3'
        and admission['publication_failure']['sha256']=='5d127ca01b9bd0ed1b1fd00a725d91b7e78be30a99d363da8b5505584ed688c6',
        'exact actual metadata interruption required')
    packet=checked(admission['failure_packet']);checked(admission['publication_failure'])
    refs={Path(ref['source']).name:ref for ref in packet['refs']}
    state=checked(refs['ROOT-CUMULATIVE-LOOP-STATE.json']);gov=checked(refs['ROOT-GOVERNANCE-RESULT-STATE.json'])
    require(refs['ROOT-CUMULATIVE-LOOP-STATE.json']['sha256']=='3633579bfa355e9e62caebe4fc5ad7cbcdf13b1b3fccfe28a9608ea99a0f70f9'
        and refs['ROOT-GOVERNANCE-RESULT-STATE.json']['sha256']=='d4705c860e91078cb251ca35d3297e2dc0e253b00b1c3c519cb8dae3106908ee',
        'actual retained111/pending112 state/governance differs')
    require(admission['original_AUTO']['sha256']=='487e865c297abe24b4f375017c65ba44e963b8d1b19e890292b69d819a49303f'
        and admission['original_MET']['sha256']=='3ac0c68febd1b4ddb4f4de3541d1c970201e287f2b96a74fb566c6ab68a2ea07',
        'exact285/286 closed inputs required')
    auto=checked(admission['original_AUTO']);met=checked(admission['original_MET']);body=met['result']['structured_content']
    pending=state['pending_cycle'];halt=checked(refs['ROOT-CURRENT-HALT-P37.json'])
    require(state['completed_cycles']==111 and pending['global_turn']==112 and pending['auto_sequence']==285
        and pending['stage']=='auto_verified' and pending['auto_response']==admission['original_AUTO']['path']
        and pending['before']==state['before'] and pending['before_metrics_response']==state['before_metrics_response']
        and pending['selected_step']=='select-event-option-3' and pending['observation']['primitive_accepted'] is True
        and pending['observation']['business_success_inferred'] is False and pending['observation']['replay_allowed'] is False
        and gov['completed_cycles']==111 and gov['pending_cycle']==pending and gov['new_business_credit']==0
        and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and state['start_date_raw']==53144328 and state['actual_saved_checkpoint']['date_raw']==53145792
        and state['checkpoint_dirty_since_save'] is True,'original111/pending112 observation/counts differs')
    for row,seq,tool in ((auto,285,'ck3_auto_turn'),(met,286,'root_current_runtime_metrics')):
        require(row.get('client_error') is None and row['request']['sequence']==seq and row['request']['tool']==tool
            and row['request']['arguments']=={} and row['result']['is_error'] is False
            and row['result']['result_type']=='complete','original complete successful AUTO/MET required')
    require(halt['error_type']=='TimeoutError'
        and halt['message']=='Exact text publication not observed; no OBS drawn or business-submitted claim'
        and halt['original_request']==met['request'] and halt['original_response']==admission['original_MET']['path']
        and halt['next_sequence']==287 and halt['replay_allowed'] is False
        and body['paused'] is True and body['map_ready'] is True and body['actor_alive'] is True
        and body['native_revision']==68 and body['revision']==9 and body['date_raw']==53146968
        and body['bridge_pid']==153556 and body['connection_generation']==2
        and all(body[key]==state['before'][key] for key in ('date_raw','actor_character_id','episode_run_id')),
        'completed MET286 original identity/public9 domain differs')
    closed=checked(admission['old_closed']);pair=checked(admission['old_pair'])
    require(closed['status']=='ACTUAL_BOTH_SDK_EXITS_OBSERVED' and closed['normal'] is False
        and closed['launcher_exit_code']==1 and closed['machine_id']==MACHINE
        and closed['Game_stopped'] is False and closed['recording_stopped'] is False
        and len(closed['processes'])==2 and len(pair['processes'])==2,'honest original Queue1/App0 closure required')
    expected={'sdk_queue':(180816,134368631379315926,1),'sdk_application':(238840,134368631390076810,0)}
    for row in closed['processes']:
        require((row['pid'],row['creation_filetime'],row['exit_code'])==expected.get(row['role'])
            and row['kernel_exit_observed'] is True and row['wait_result']==0 and row['observation_error'] is None
            and any(original['role']==row['role'] and all(original[key]==row[key]
                for key in ('pid','creation_filetime','executable')) for original in pair['processes']),
            'original retained SDK generation differs')
    require(admission['post_close']['sha256']=='ccc49c3dd4352ec729b019ec3393df53270853bfe9afb7dffec78499cca7f95f',
        'actual post-C5-close Driver provenance required')
    post=checked(admission['post_close'])
    retained={Path(ref['source']).name:ref for ref in post['retained_small_sources']}
    require(post['machine_id']==MACHINE and post['actual_sdk_closed']==admission['old_closed']
        and post['Queue_exit_code']==1 and post['App_exit_code']==0 and post['normal_dual0_claimed'] is False
        and post['old_pair_signaled'] is True and post['Game_pid']==153556
        and post['Game_creation_filetime']==134368602545256920
        and post['closed_Driver']['bytes']==1555495
        and post['closed_Driver']['sha256']=='03bf6e561ed0132ceffbdd3830432c20f45d4b2b4ebcb1244d3b4459e8563a1d'
        and post['before_frame']==state['before'] and post['retained_pending_cycle']==pending
        and post['completed_cycles']==111 and post['T0_date_raw']==53144328 and post['endpoint_date_raw']==53407128
        and post['actual_last_saved_checkpoint']==state['actual_saved_checkpoint']
        and checked(retained['ROOT-CUMULATIVE-LOOP-STATE.json'])==state
        and checked(retained['ROOT-GOVERNANCE-RESULT-STATE.json'])==gov
        and all(retained[name]['sha256']==refs[name]['sha256'] and checked(retained[name])==checked(refs[name])
            for name in ('active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json')),
        'closed Driver/retained111 pending112 lineage differs')
    ack=checked(admission['completed_MET_publication_ACK']);projection=checked(ack['source_observation'])
    require(ack['schema']=='xar.ck3.decision-text-published/v1' and ack['status']=='TEXT_PUBLISHED'
        and ack['machine_id']==MACHINE and ack['OBS_draw_ack'] is False
        and ack['business_submission_or_outcome_inferred'] is False
        and projection['source_ref']==admission['original_MET']['path'] and projection['request']==met['request']
        and ack['source_observation']['sha256']=='75c43f5340a9bfeee5dea461d0e26ddada620cf584484e9b7c7a1e457d373fe3',
        'actual new-publisher same-source286 text ACK required; no fabricated old ACK')
    return state,gov,body,ack


def make_completed_met286_queue_v1(base,env,*,admission_path):
    class CompletedMet286Queue(base):
        def preflight(self):
            from root_continuous_segment_auto_c6 import verify_segment
            from root_decision_text_api_c6 import load_api,started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission=env['read'](Path(admission_path),65536);state,gov,body,ack=validate_inputs(admission)
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir()))
                and not (env['N']/'ROOT-COMPLETED-MET-286-CONSUME-INTENT.json').exists(),
                'new normal queue/recording and unconsumed286 required')
            for key,name in (('queue_source','root_p37c6_sdk_queue.py'),('entry_source','root_p37c6_mcp_entry.py'),
                    ('native_binding_source','root_native_build_binding_p37c6.py')):
                ref=admission[key];path=Path(ref['path']).resolve(strict=True);raw=path.read_bytes()
                require(path==(env['N']/name).resolve() and len(raw)<=1024**2 and len(raw)==ref['bytes']
                    and hashlib.sha256(raw).hexdigest()==ref['sha256'],'current C6 source differs: '+name)
            require(Path(env['__file__']).resolve()==Path(admission['queue_source']['path']).resolve()
                and self.launch['pid']==153556 and self.launch['creation_filetime']==134368602545256920
                and admission['next_sequence']==287,'actual same Game/C6/next287 required')
            self.job,self.record_started,self.first=verify_segment(env['N'],env['R'],self.launch,self.record_job,
                self.args.first_frame_admission,env['read'],env['aware'],env['now'])
            api=load_api(env['N'])
            require(started_reference(env['N'],api)==ack['publisher_started']
                and api.process_identity(153556)['creation_filetime']==134368602545256920,
                'actual new C6 publisher or retained Game differs')
            absence=checked(admission['mod_absence'])
            require(absence['machine_id']==MACHINE and absence['game_pid']==153556
                and absence['game_creation_filetime']==134368602545256920,'physical Game mod-absence proof differs')
            self.expected_lifecycle_binding=bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest),'verified_mod_absence':absence},
                lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding==state['actual_saved_checkpoint']['succession_lifecycle'],
                'same-Game lifecycle differs')
            freeze=checked(admission['sdk_freeze'],2*1024**2)
            require(Path(admission['sdk_freeze']['path']).name=='ROOT-FINAL-SDK-FREEZE-P37C6.json'
                and freeze['business_source_commit']==BUSINESS
                and Path(admission['current_map_admission']).resolve()==(env['N']/'ROOT-CAMPAIGN-MAP-ADMITTED-C6.json').resolve(),
                'C6 exact M3 warm-domain business source/current-map required')
            self.frozen_head=freeze['git_head'];self.frontend_done=len(env['FRONTEND']);self.checkpoint_mode=True
            self.next_sequence=287;self.initial_frame=self.initial_save=None
            self._completed_met286={'phase':'semantic','admission':admission,'state':state,'gov':gov,'body':body,'ack':ack}
            self.guard(reserve=False)

        async def call(self,session,request,path):
            if self._completed_met286['phase']=='semantic' and request.get('tool')==env['SEMANTIC']:
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c6_overlay_relay import relay_compact
                return await startup_readiness_call(self,session,request,path,env,relay_compact=relay_compact)
            return await super().call(session,request,path)

        def check_before(self,tool,arguments):
            resume=self._completed_met286
            if resume['phase']!='ready':
                expected=env['SEMANTIC'] if resume['phase']=='semantic' else env['CAPABILITIES']
                require(tool==expected and arguments=={},'one new same-Game SEM287 then CAP288 required')
                return
            return super().check_before(tool,arguments)

        def check_after(self,tool,arguments,body):
            resume=self._completed_met286
            if resume['phase']=='semantic' and tool==env['SEMANTIC']:
                attempt=self.current_attempt;row=attempt['row'];request=attempt['request']
                require(request=={'sequence':287,'tool':env['SEMANTIC'],'arguments':{}}
                    and row['request']==request and row.get('client_error') is None and row['result']['is_error'] is False
                    and row['result']['result_type']=='complete' and env['decoded'](row)==body and self.next_sequence==287,
                    'actual successful first SEM287 context required')
                actual=env['frame'](body,semantic=True,expected_lifecycle=self.expected_lifecycle_binding)
                diag=body.get('diagnostics') or {};hello=diag.get('hello') or {};original=resume['body']
                require(all(actual[key]==original[key] for key in ('date_raw','actor_character_id','episode_run_id'))
                    and actual['native_revision']>=original['native_revision']
                    and diag.get('bridge_pid')==hello.get('pid')==153556 and diag.get('pipe_name')==self.launch['pipe']
                    and type(diag.get('connection_generation')) is int and diag['connection_generation']>0
                    and diag['connection_generation']==hello.get('connection_generation')
                    and hello.get('ck3_build_match') is True and hello.get('game_adapter_id')=='ck3-1.20.0.4-msvc-x64'
                    and hello.get('game_adapter_status')=='ready' and body.get('campaign_goal')==resume['state']['campaign_goal_anchor'],
                    'fresh same-Game day110/actor/episode/Native/goal differs from original286')
                source=Path(attempt['response']).resolve(strict=True)
                require(source.is_relative_to(env['N'].resolve()) and env['read'](source,env['REPLY_RESERVE'])==row,
                    'actual readiness observer source differs')
                from root_score_month_samples_c4 import observe_semantic
                observe_semantic(env['N'],body,self.launch,source)
                self.semantic=body;self.initial_frame=copy.deepcopy(actual)
                self.cold_semantic_response_path=str(env['OUTBOX']/'0287-1-result.json')
                resume.update(phase='capabilities',opening=actual)
                return
            if resume['phase']=='capabilities' and tool==env['CAPABILITIES']:
                control=body.get('native_session_control') or {};original=resume['body']
                require(body.get('episode_run_id')==original['episode_run_id'] and body.get('episode_character_id')==original['actor_character_id']
                    and body.get('episode_identity_pending') is False and body.get('one_life_terminal') is False
                    and control.get('driver_state_restored') is True and control.get('driver_state_restore_kind')=='same_pid_hot'
                    and control.get('episode_binding_state')=='active_resumed' and control.get('driver_state_error') is None
                    and control.get('cold_candidate_rejection') is None,'actual same_pid_hot restore required')
                self.full_loop_state=copy.deepcopy(resume['state']);self.governance_result_state=copy.deepcopy(resume['gov']['state'])
                self.lifestyle_pending_focus=copy.deepcopy(resume['gov']['pending_focus']);self.initial_save=copy.deepcopy(self.full_loop_state['actual_saved_checkpoint'])
                pin=checked(resume['admission']['classifier_pin'],16384);self.result_classifier=env['load_cold_result_classifier']()
                path=Path(self.result_classifier.__code__.co_filename).resolve(strict=True);raw=path.read_bytes()
                require(path==Path(pin['source']).resolve() and len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                    'current classifier source differs')
                self.result_classifier_pin={key:pin[key] for key in ('source','sha256')}
                self.capabilities_verified=self.cold_readiness_verified=self.checkpoint_bootstrap_verified=True
                self.halted=self.halt_cause=self.current_attempt=self.held_control=None;resume['phase']='ready';self.persist_loop_state()
                env['atomic'](env['Q']/'ROOT-COMPLETED-MET286-WARM-BOUND.json',{'schema':SCHEMA,'machine_id':MACHINE,
                    'fresh_opening':resume['opening'],'original_MET':resume['admission']['original_MET'],
                    'fresh_semantic_response':self.cold_semantic_response_path,'original_MET_once_consumed':False,
                    'completed_cycles':111,'pending112_preserved':True,'ordinary_cycle_credit':0,'new_RPC_replay':False,
                    'original_MET_public_revision_preserved':9,'T0_date_raw':self.full_loop_state['start_date_raw']},limit=16384)
                return
            return super().check_after(tool,arguments,body)

        def persist_loop_state(self):
            # Let the original full_loop persist its actual completed286 settlement
            # first. The independent App-opening publication belongs to SEM287;
            # it never changes the old286 event, receipt, observation or credit.
            result=super().persist_loop_state()
            resume=getattr(self,'_completed_met286',None);state=getattr(self,'full_loop_state',None)
            if (not isinstance(resume,dict) or not resume.get('consumed') or resume.get('rebound')
                    or not isinstance(state,dict) or state.get('completed_cycles')!=112
                    or state.get('pending_cycle') is not None):
                return result
            source=resume['admission']['original_MET'];old_frame=env['frame'](resume['body'])
            event=env['read'](env['Q']/'CUMULATIVE-TURN-000112.json',16384)
            require(state['before']==old_frame and state['before_metrics_response']==source['path']
                and event['after']==old_frame and event['after_metrics_response']==source['path']
                and all(event[key]==value for key,value in resume['state']['pending_cycle'].items())
                and all(resume['opening'][key]==old_frame[key]
                    for key in ('date_raw','actor_character_id','episode_run_id'))
                and resume['opening']['native_revision']>=old_frame['native_revision'],
                'original112 settlement required before source-domain rebind')
            marker=env['Q']/'ROOT-MET286-SETTLED-AND-WARM-REBOUND.json'
            env['atomic'](marker,{'schema':SCHEMA,'machine_id':MACHINE,'settled_metrics_frame':old_frame,
                'settled_metrics_response':source,'fresh_opening':resume['opening'],
                'fresh_semantic_response':self.cold_semantic_response_path,'fresh_source_tool':env['SEMANTIC'],
                'completed_cycles':112,'pending_cycle':None,'new_ordinary_credit_from_rebind':0,
                'old_MET_body_or_public_revision_rewritten':False,'T0_date_raw':state['start_date_raw'],
                'original_settlement_event':str(env['Q']/'CUMULATIVE-TURN-000112.json')},limit=16384)
            state['before']=copy.deepcopy(resume['opening'])
            state['before_metrics_response']=self.cold_semantic_response_path
            state['current_source_kind']='semantic_snapshot_after_completed_MET286_settlement'
            state['completed_MET286_warm_rebind']=str(marker)
            resume['rebound']=True
            return super().persist_loop_state()

        async def generated(self,session,tool,arguments=None):
            resume=self._completed_met286
            if resume['phase']=='ready' and not resume.get('consumed'):
                require(tool==env['METRICS'] and arguments in (None,{}),'pending112 first consumes original286 only')
                require(self.full_loop_state==resume['state'] and self.full_loop_state['pending_cycle']['stage']=='auto_verified',
                    'retained pending112 changed before original286 consumption')
                self.guard();source=resume['admission']['original_MET'];original=checked(source)['result']['structured_content']
                require(original==resume['body'],'original286 body changed')
                intent=env['N']/'ROOT-COMPLETED-MET-286-CONSUME-INTENT.json'
                env['atomic'](intent,{'schema':SCHEMA,'source':source,'global_turn':112,'MCP_calls':0,
                    'sequence_reissued':False,'public_revision_rewritten':False},limit=16384)
                super().check_after(env['METRICS'],{},original)
                resume['consumed']=True
                return original,Path(source['path'])
            return await super().generated(session,tool,arguments)

    return CompletedMet286Queue
