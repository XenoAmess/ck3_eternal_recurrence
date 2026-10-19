"""Finite C8 same-Game warm boundary and one App-owned LIFE2 diagnostic."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
SCHEMA='xar.C8-LIFE4102-diagnostic-warm/v1'
BUSINESS='8e1e59f073f239d266f5b59f57c65b5645658512'
TOOL='ck3_query_player_lifestyle_current_state_once_diagnostic_v1'
CHILD_TOOL='ck3_query_current_player_education_focus_once_diagnostic_v1'
LIFE2_ERRORS=frozenset(('native_lifestyle_current_state_current_lifestyle_getter_failed',
    'native_lifestyle_current_state_current_lifestyle_key_read_failed'))
POST_SHA='11a0de1e994f597abdce3d7c2a8c5c3b810bcc576a7a872e4a3de7148e32738d'
BLOCKED_SHA='896f6c4aa7658a7bfc9bf1f4c2380c445faf94cd8284ccb5081cde46ced4a484'
SIDECARS=('faction-gift-pending-v1.json','active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json')


def require(ok,why):
    if not ok:raise ValueError('C8 LIFE4102 diagnostic warm denied: '+why)


def checked(ref,limit=262144):
    path=Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)<=limit and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],
        'exact bounded input differs: '+str(path))
    return json.loads(raw)


def warm_inputs(admission):
    require(admission['schema']==SCHEMA and admission['machine_id']==MACHINE,'finite admission required')
    require(admission['post_close']['sha256']==POST_SHA,'actual C7 postclose source required')
    post=checked(admission['post_close']);refs={Path(r['original_source']).name:r for r in post['source_refs']}
    state=checked(refs['ROOT-CUMULATIVE-LOOP-STATE.json']);gov=checked(refs['ROOT-GOVERNANCE-RESULT-STATE.json'])
    row=checked(refs['4102-1-result.json']);rejected=checked(refs['4103-1-result.json'])
    require(refs['4102-1-result.json']['sha256']==BLOCKED_SHA
        and refs['4103-1-result.json']['sha256']=='0154c97b2060a96558161e5cdefbc05c9735f8d85b47eeb62ea1a5993d43a5a4'
        and row['request']['sequence']==4102 and row['request']['tool']=='ck3_auto_turn'
        and row.get('client_error') is None and row['result']['is_error'] is False
        and row['result']['result_type']=='complete'
        and row['result']['structured_content']['status']=='blocked'
        and row['result']['structured_content'].get('selected_step') is None
        and row['result']['structured_content']['plan']['phase']=='lifestyle_native_query_unavailable'
        and row['result']['structured_content']['plan']['selected_step'] is None
        and rejected['request']['sequence']==4103
        and 'only an unexecuted blocked turn with a fresh same-date frame may be discarded' in rejected['client_error'],
        'original blocked4102/no selected dispatch and rejected4103 required')
    pending=state['pending_cycle'];before=state['before']
    require(state['completed_cycles']==1956 and state['start_date_raw']==53144328
        and before['date_raw']==53188032 and before['actor_character_id']==40526
        and before['episode_run_id']=='native-40526-1bec95182886' and before['native_revision']==3134
        and pending['global_turn']==1957 and pending['auto_sequence']==4102 and pending['stage']=='auto_unsettled'
        and pending['before']==before and gov['completed_cycles']==1956
        and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt')),
        'exact1956/day1821 with only blocked pending1957 required')
    closed=checked(admission['old_closed']);pair=checked(admission['old_pair'])
    require(post['actual_sdk_closed']==admission['old_closed'] and closed['status']=='ACTUAL_BOTH_SDK_EXITS_OBSERVED'
        and closed['machine_id']==MACHINE and closed['normal'] is False and closed['launcher_exit_code']==1
        and closed['Game_stopped'] is False and closed['recording_stopped'] is False
        and len(closed['processes'])==len(pair['processes'])==2,'actual known1/0 SDK-only closure required')
    for p in closed['processes']:
        require(p['exit_code']=={'sdk_queue':1,'sdk_application':0}.get(p['role'])
            and p['kernel_exit_observed'] is True and p['wait_result']==0 and p['observation_error'] is None
            and any(q['role']==p['role'] and all(q[k]==p[k] for k in ('pid','creation_filetime','executable'))
                for q in pair['processes']),'exact closed SDK generation required')
    require(post['machine_id']==MACHINE and post['Game_pid']==153556
        and post['Game_creation_filetime']==134368602545256920 and post['completed_cycles']==1956
        and post['next_sequence']==4104 and post['old_normal'] is False
        and post['known_unexecuted_blocked_AUTO4102_preserved'] is True and post['failed_clear4103_preserved'] is True
        and post['closed_Driver']['bytes']==1361402
        and post['closed_Driver']['sha256']=='e14981fa10124cca0d1b66473c58da73e5893ad7febcdb2290133d8f05191384'
        and post['loop_cached_checkpoint']==state['actual_saved_checkpoint'],
        'same-Game postclose/Driver provenance required; Driver body is not reread')
    require(post['unexecuted_proof']['sha256']=='25f8cd84a5d4305d3ed3cd0c41d106d370d334698e67c15e1443a3394bb4a8bd',
        'closed4102 source boundary required')
    checked(post['unexecuted_proof'])
    for name in SIDECARS:checked(refs[name])
    return state,gov,post,refs


def make_life4102_diag_warm_queue_v1(base,env,*,admission_path):
    class Life4102DiagnosticWarmQueue(base):
        def preflight(self):
            from root_continuous_segment_auto_c6 import verify_segment
            from root_decision_text_api_c6 import load_api,started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission=env['read'](Path(admission_path),65536);state,gov,post,refs=warm_inputs(admission)
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir()))
                and admission['next_sequence']==4104 and self.launch['pid']==153556
                and self.launch['creation_filetime']==134368602545256920,'new C8 queue/same Game/next4104 required')
            for key,name in (('queue_source','root_p37c8_sdk_queue.py'),('entry_source','root_p37c8_mcp_entry.py')):
                ref=admission[key];path=Path(ref['path']).resolve(strict=True);raw=path.read_bytes()
                require(path==(env['N']/name).resolve() and len(raw)<=1024**2 and len(raw)==ref['bytes']
                    and hashlib.sha256(raw).hexdigest()==ref['sha256'],'actual C8 source differs: '+name)
            require(Path(env['__file__']).resolve()==Path(admission['queue_source']['path']).resolve(),'executing queue differs')
            self.job,self.record_started,self.first=verify_segment(env['N'],env['R'],self.launch,self.record_job,
                self.args.first_frame_admission,env['read'],env['aware'],env['now'])
            api=load_api(env['N'])
            require(started_reference(env['N'],api)==admission['retained_C6_publisher_started']
                and self.record_job.resolve()==Path(admission['retained_recording_job']).resolve()
                and self.args.first_frame_admission.resolve()==Path(admission['retained_first_frame_admission']).resolve()
                and api.process_identity(153556)['creation_filetime']==134368602545256920,'existing C6 pub/OBS/Game required')
            absence=checked(admission['mod_absence'])
            require(absence['machine_id']==MACHINE and absence['game_pid']==153556
                and absence['game_creation_filetime']==134368602545256920,'physical Game mod absence differs')
            self.expected_lifecycle_binding=bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest),'verified_mod_absence':absence},
                lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding==state['actual_saved_checkpoint']['succession_lifecycle'],'lifecycle differs')
            freeze=checked(admission['sdk_freeze'],2*1024**2)
            require(Path(admission['sdk_freeze']['path']).name=='ROOT-FINAL-SDK-FREEZE-P37C7.json'
                and admission['sdk_freeze']['sha256']=='4c9de700f1572ad81627fe6c92cd5fec4b05cb4e02b0c4e6449bda48b32cb4d9'
                and freeze['business_source_commit']==BUSINESS
                and Path(admission['current_map_admission']).resolve()==(env['N']/'ROOT-CAMPAIGN-MAP-ADMITTED-C8.json').resolve(),
                'unchanged C7 business source and explicit new map required')
            self.frozen_head=freeze['git_head'];self.frontend_done=len(env['FRONTEND']);self.checkpoint_mode=True
            self.next_sequence=4104;self.initial_frame=self.initial_save=None
            self._life4102={'phase':'semantic','admission':admission,'state':state,'gov':gov,'post':post,'refs':refs,'diag_attempted':False}
            self.guard(reserve=False)

        async def call(self,session,request,path):
            if self._life4102['phase']=='semantic' and request.get('tool')==env['SEMANTIC']:
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c6_overlay_relay import relay_compact
                return await startup_readiness_call(self,session,request,path,env,relay_compact=relay_compact)
            return await super().call(session,request,path)

        def check_before(self,tool,arguments):
            resume=self._life4102
            if resume['phase']!='ready':
                require(tool==(env['SEMANTIC'] if resume['phase']=='semantic' else env['CAPABILITIES']) and arguments=={},
                    'one fresh SEM4104 then CAP4105 required')
                return
            if tool==TOOL:
                require(not resume['diag_attempted'] and arguments=={'expected_revision':resume['opening']['revision']},
                    'one diagnostic at exact fresh SEM revision required')
                self.guard()
                env['atomic'](env['Q']/'ROOT-C8-LIFE2-DIAGNOSTIC-ATTEMPT.json',{'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'expected_revision':arguments['expected_revision'],
                    'next_sequence':self.next_sequence,'gameplay_action_credit':0,'replay_allowed':False},limit=16384)
                resume['diag_attempted']=True
                return
            if tool==CHILD_TOOL:
                prior=resume.get('diagnostic_result') or {}
                require(not resume.get('child_diag_attempted') and arguments=={'expected_revision':resume['opening']['revision']}
                    and prior.get('status')=='observed' and prior.get('same_frame') is True and prior.get('query_attempted') is True
                    and prior.get('before')==prior.get('after') and isinstance(prior.get('before'),dict)
                    and prior['before'].get('revision')==resume['opening']['revision']
                    and (prior.get('original_method_return') or {}).get('native_error') in LIFE2_ERRORS,
                    'conditional once child-focus requires exact preceding same-frame LIFE2 getter/key failure')
                self.guard()
                env['atomic'](env['Q']/'ROOT-C8-CHILD-FOCUS-DIAGNOSTIC-ATTEMPT.json',{'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'expected_revision':arguments['expected_revision'],
                    'next_sequence':self.next_sequence,'gameplay_action_credit':0,'replay_allowed':False},limit=16384)
                resume['child_diag_attempted']=True
                return
            return super().check_before(tool,arguments)

        def check_after(self,tool,arguments,body):
            resume=self._life4102
            if resume['phase']=='semantic' and tool==env['SEMANTIC']:
                attempt=self.current_attempt;row=attempt['row'];request=attempt['request']
                require(request=={'sequence':4104,'tool':env['SEMANTIC'],'arguments':{}}
                    and row['request']==request and row.get('client_error') is None and row['result']['is_error'] is False
                    and row['result']['result_type']=='complete' and env['decoded'](row)==body and self.next_sequence==4104,
                    'actual first SEM4104 context required')
                actual=env['frame'](body,semantic=True,expected_lifecycle=self.expected_lifecycle_binding)
                diag=body.get('diagnostics') or {};hello=diag.get('hello') or {}
                require(all(actual[k]==resume['state']['before'][k] for k in ('date_raw','actor_character_id','episode_run_id'))
                    and actual['native_revision']>=resume['state']['before']['native_revision']
                    and diag.get('bridge_pid')==hello.get('pid')==153556 and diag.get('pipe_name')==self.launch['pipe']
                    and type(diag.get('connection_generation')) is int and diag['connection_generation']>0
                    and diag['connection_generation']==hello.get('connection_generation')
                    and hello.get('ck3_build_match') is True and hello.get('game_adapter_id')=='ck3-1.20.0.4-msvc-x64'
                    and hello.get('game_adapter_status')=='ready' and body.get('campaign_goal')==resume['state']['campaign_goal_anchor'],
                    'fresh same-Game actor/episode/date/Native/goal differs')
                source=Path(attempt['response']).resolve(strict=True)
                require(source.is_relative_to(env['N'].resolve()) and env['read'](source,env['REPLY_RESERVE'])==row,
                    'actual readiness row required')
                from root_score_month_samples_c4 import observe_semantic
                observe_semantic(env['N'],body,self.launch,source)
                self.semantic=body;self.initial_frame=copy.deepcopy(actual)
                self.cold_semantic_response_path=str(env['OUTBOX']/'4104-1-result.json')
                resume.update(phase='capabilities',opening=actual)
                return
            if resume['phase']=='capabilities' and tool==env['CAPABILITIES']:
                control=body.get('native_session_control') or {};opening=resume['opening']
                require(body.get('episode_run_id')==opening['episode_run_id'] and body.get('episode_character_id')==opening['actor_character_id']
                    and body.get('episode_identity_pending') is False and body.get('one_life_terminal') is False
                    and control.get('driver_state_restored') is True and control.get('driver_state_restore_kind')=='same_pid_hot'
                    and control.get('episode_binding_state')=='active_resumed' and control.get('driver_state_error') is None
                    and control.get('cold_candidate_rejection') is None,'actual same_pid_hot restore required')
                for name in SIDECARS:
                    ref=resume['refs'][name];raw=Path(ref['original_source']).read_bytes()
                    require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'retained sidecar differs: '+name)
                self.full_loop_state=copy.deepcopy(resume['state']);self.governance_result_state=copy.deepcopy(resume['gov']['state'])
                self.lifestyle_pending_focus=copy.deepcopy(resume['gov']['pending_focus']);self.initial_save=copy.deepcopy(self.full_loop_state['actual_saved_checkpoint'])
                self.full_loop_state.update(pending_cycle=None,before=copy.deepcopy(opening),
                    before_metrics_response=self.cold_semantic_response_path,before_source_kind='actual_sameGame_LIFE4102_warm_semantic_snapshot')
                pin=checked(resume['admission']['classifier_pin'],16384);self.result_classifier=env['load_cold_result_classifier']()
                path=Path(self.result_classifier.__code__.co_filename).resolve(strict=True);raw=path.read_bytes()
                require(path==Path(pin['source']).resolve() and len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                    'current classifier source differs')
                self.result_classifier_pin={k:pin[k] for k in ('source','sha256')}
                self.capabilities_verified=self.cold_readiness_verified=self.checkpoint_bootstrap_verified=True
                self.halted=self.halt_cause=self.current_attempt=self.held_control=None;resume['phase']='ready';self.persist_loop_state()
                env['atomic'](env['Q']/'ROOT-C8-LIFE-DIAG-WARM-BOUND.json',{'schema':SCHEMA,'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'fresh_opening':opening,'fresh_semantic_response':self.cold_semantic_response_path,
                    'completed_cycles':1956,'pending_cycle':None,'source_blocked4102':resume['refs']['4102-1-result.json'],
                    'failed_clear4103':resume['refs']['4103-1-result.json'],'ordinary_cycle_credit':0,'business_action_credit':0,
                    'T0_date_raw':self.full_loop_state['start_date_raw'],'SDK_source_commit':BUSINESS,
                    'original_AUTO_replayed':False,'retained_C6_publisher_started':resume['admission']['retained_C6_publisher_started']},limit=16384)
                return
            if tool==TOOL:
                require(resume['phase']=='ready' and resume['diag_attempted'] is True
                    and body.get('schema')=='xar.app-owned-lifestyle-current-state-once-diagnostic.v1'
                    and body.get('machine_id')==MACHINE and body.get('gameplay_action_submitted') is False
                    and body.get('method')=='NativeDriver.query_player_lifestyle_current_state_private_v1'
                    and body.get('expected_revision')==resume['opening']['revision']
                    and body.get('status') in ('observed','frame_changed','diagnostic_failed')
                    and body.get('expected_owner_frame')=={'bridge_pid':153556,'player_character_id':40526,
                        'date_raw':53188032,'min_native_revision':3134,'episode_run_id':'native-40526-1bec95182886'},
                    'exact App-owned once diagnostic result required')
                env['atomic'](env['Q']/'ROOT-C8-LIFE2-DIAGNOSTIC-OBSERVED.json',{'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'status':body['status'],'source_response':self.current_attempt['response'],
                    'ordinary_cycle_credit':0,'business_action_credit':0,'native_error_retained':True,'replay_allowed':False},limit=16384)
                resume['diagnostic_result']=copy.deepcopy(body)
                return
            if tool==CHILD_TOOL:
                require(resume['phase']=='ready' and resume.get('child_diag_attempted') is True
                    and body.get('schema')=='xar.app-owned-child-focus-once-diagnostic.v1'
                    and body.get('machine_id')==MACHINE and body.get('gameplay_action_submitted') is False
                    and body.get('method')=='NativeDriver.query_child_education_focus_private_v1'
                    and body.get('expected_revision')==resume['opening']['revision']
                    and body.get('status') in ('observed','frame_changed','diagnostic_failed')
                    and Path(body.get('prior_lifestyle_diagnostic_path','')).resolve()==Path(resume['admission']['lifestyle_diagnostic_path']).resolve(),
                    'exact conditional App-owned child-focus observation required')
                env['atomic'](env['Q']/'ROOT-C8-CHILD-FOCUS-DIAGNOSTIC-OBSERVED.json',{'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'status':body['status'],'source_response':self.current_attempt['response'],
                    'ordinary_cycle_credit':0,'business_action_credit':0,'replay_allowed':False},limit=16384)
                return
            return super().check_after(tool,arguments,body)
    return Life4102DiagnosticWarmQueue
