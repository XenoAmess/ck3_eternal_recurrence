"""C7 same-Game source maintenance; no completed result supply or action replay."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
SCHEMA='xar.C7-source-only-day381-warm/v1'
BUSINESS='8e1e59f073f239d266f5b59f57c65b5645658512'
LEAVES=frozenset(('xar_autoplayer/bridge/faction_gift_formal_route_v1.py',
    'xar_autoplayer/bridge/readonly_planning_retry_v1.py','xar_autoplayer/ordinary_sway_lifecycle_observation_v1.py'))


def require(ok,why):
    if not ok:raise ValueError('C7 source-only warm denied: '+why)


def checked(ref,limit=262144):
    path=Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)<=limit and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],
        'exact bounded input differs: '+str(path))
    return json.loads(raw)


def warm_inputs(admission):
    require(admission['schema']==SCHEMA and admission['machine_id']==MACHINE,'finite C7/day381 admission')
    require(admission['clean_seed']['sha256']=='391ed071e1603917b4bab11d3653109b4a7cb9b1e33afa0a15cdd4cc8ce793ca',
        'exact cleared219 clean seed required')
    require(admission['post_close']['sha256']=='b5be46c4574cab58c0b5ffab1b6660e168d1218ef552e3d442e359c467f64e3c',
        'actual C6 postclose provenance required')
    seed=checked(admission['clean_seed']);post=checked(admission['post_close'])
    refs={Path(ref['original_source']).name:ref for ref in seed['source_refs']}
    state=checked(refs['ROOT-CUMULATIVE-LOOP-STATE.json']);gov=checked(refs['ROOT-GOVERNANCE-RESULT-STATE.json'])
    gift=checked(refs['faction-gift-pending-v1.json'])
    require(state['completed_cycles']==219 and state['start_date_raw']==53144328
        and all(state.get(k) is None for k in ('pending_cycle','pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and state['before']['date_raw']==53153472 and state['before']['actor_character_id']==31254
        and state['before']['episode_run_id']=='native-31254-6271ac8cd441'
        and gov['completed_cycles']==219 and gov['pending_cycle'] is None
        and refs['faction-gift-pending-v1.json']['sha256']=='24268466d6c3a9c521885c9dee0aeaff7e035e9ec3f6d5af0862c54a3e9768a0'
        and gift['pending']['request_id']=='faction-gift-d29a273508614be4aa0fdfaba560667c'
        and gift['pending']['status']=='submitted_verification_pending',
        'clean219/day381 queue and unresolved old gift required')
    plan=checked(admission['original_PLAN517'])
    require(admission['original_PLAN517']['sha256']=='7df0fe8ccb389f387b37d0aa409b9dfd9187182902c61caff0b285c5bdcaa184'
        and plan['request']=={'sequence':517,'tool':'ck3_plan_turn','arguments':{}}
        and plan.get('client_error') is None and plan['result']['is_error'] is False
        and plan['result']['result_type']=='complete'
        and plan['result']['structured_content']['plan']['selected_step']=='private-query-faction-gift-cold-recovery-v1',
        'original517 retained as a plan only; cold action not executed')
    closed=checked(admission['old_closed']);pair=checked(admission['old_pair'])
    require(admission['old_pair']['sha256']==refs['ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C6.json']['sha256']
        and Path(admission['old_pair']['path']).name=='ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C6.json',
        'retained actual C6 SDK pair pin required')
    require(closed['status']=='ACTUAL_BOTH_SDK_EXITS_OBSERVED' and closed['normal'] is True
        and closed['launcher_exit_code']==0 and closed['machine_id']==MACHINE
        and closed['Game_stopped'] is False and closed['recording_stopped'] is False
        and len(closed['processes'])==len(pair['processes'])==2,'actual normal C6 SDK-only closure required')
    for row in closed['processes']:
        require(row['exit_code']==0 and row['kernel_exit_observed'] is True and row['wait_result']==0
            and row['observation_error'] is None and any(original['role']==row['role']
                and all(original[k]==row[k] for k in ('pid','creation_filetime','executable'))
                for original in pair['processes']),'exact old C6 SDK generation must be closed')
    require(post['machine_id']==MACHINE and post['actual_sdk_closed']==admission['old_closed']
        and post['Game_pid']==153556 and post['Game_creation_filetime']==134368602545256920
        and post['completed_cycles']==219 and post['next_sequence']==518,'same Game/clean219/postclose source required')
    postrefs={Path(ref['original_source']).name:ref for ref in post['source_refs']}
    for name in ('ROOT-CUMULATIVE-LOOP-STATE.json','ROOT-GOVERNANCE-RESULT-STATE.json',
            'faction-gift-pending-v1.json','active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json'):
        require(postrefs[name]['sha256']==refs[name]['sha256'] and checked(postrefs[name])==checked(refs[name]),
            'postclose retained source differs: '+name)
    # Driver's newest checkpoint and the ordinary loop's historical save cache
    # are separate inputs. Do not turn the former into a fabricated cadence SAVE.
    require(post['closed_Driver']['bytes']==4216827
        and post['closed_Driver']['sha256']=='77aaa5fdf746693e71c5594df9b4b5930cd0ea10db6f14a5778402de7c3b87f2'
        and post['loop_cached_checkpoint']==state['actual_saved_checkpoint']
        and post['actual_Driver_checkpoint']['sha256']==gift['pending']['checkpoint_sha256_before_submit']
        and post['actual_Driver_checkpoint']['date_raw']==53153472
        and post['actual_Driver_checkpoint']['succession_lifecycle']==state['actual_saved_checkpoint']['succession_lifecycle'],
        'postclose Driver provenance required without reading its large body')
    return state,gov,gift,seed,post


def make_source_only_warm_queue_v1(base,env,*,admission_path):
    class SourceOnly381WarmQueue(base):
        def preflight(self):
            from root_continuous_segment_auto_c6 import verify_segment
            from root_decision_text_api_c6 import load_api,started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission=env['read'](Path(admission_path),65536);state,gov,gift,seed,post=warm_inputs(admission)
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir()))
                and admission['next_sequence']==518 and self.launch['pid']==153556
                and self.launch['creation_filetime']==134368602545256920,'new C7 queue/same Game/next518 required')
            for key,name in (('queue_source','root_p37c7_sdk_queue.py'),('entry_source','root_p37c7_mcp_entry.py'),
                    ('native_binding_source','root_native_build_binding_p37c7.py')):
                ref=admission[key];path=Path(ref['path']).resolve(strict=True);raw=path.read_bytes()
                require(path==(env['N']/name).resolve() and len(raw)<=1024**2 and len(raw)==ref['bytes']
                    and hashlib.sha256(raw).hexdigest()==ref['sha256'],'actual C7 source differs: '+name)
            require(Path(env['__file__']).resolve()==Path(admission['queue_source']['path']).resolve(),'executing C7 queue source differs')
            self.job,self.record_started,self.first=verify_segment(env['N'],env['R'],self.launch,self.record_job,
                self.args.first_frame_admission,env['read'],env['aware'],env['now'])
            api=load_api(env['N'])
            require(started_reference(env['N'],api)==admission['retained_C6_publisher_started']
                and str(self.record_job.resolve())==str(Path(admission['retained_recording_job']).resolve())
                and str(self.args.first_frame_admission.resolve())==str(Path(admission['retained_first_frame_admission']).resolve())
                and api.process_identity(153556)['creation_filetime']==134368602545256920,
                'existing C6 publisher/OBS/Game must be retained exactly')
            absence=checked(admission['mod_absence'])
            require(absence['machine_id']==MACHINE and absence['game_pid']==153556
                and absence['game_creation_filetime']==134368602545256920,'same physical Game mod-absence proof required')
            self.expected_lifecycle_binding=bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest),'verified_mod_absence':absence},
                lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding==state['actual_saved_checkpoint']['succession_lifecycle'],'existing lifecycle differs')
            freeze=checked(admission['sdk_freeze'],2*1024**2)
            require(Path(admission['sdk_freeze']['path']).name=='ROOT-FINAL-SDK-FREEZE-P37C7.json'
                and freeze['business_source_commit']==BUSINESS and set(admission['changed_sdk_leaves'])==LEAVES
                and Path(admission['current_map_admission']).resolve()==(env['N']/'ROOT-CAMPAIGN-MAP-ADMITTED-C7.json').resolve(),
                'exact Root canonical C7 three-leaf source/current map required')
            for relative,ref in admission['changed_sdk_leaves'].items():
                path=Path(ref['path']).resolve(strict=True);raw=path.read_bytes()
                require(path==(Path(freeze['source_root'])/relative).resolve() and len(raw)<=1024**2
                    and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],
                    'exact canonical SDK leaf differs: '+relative)
            self.frozen_head=freeze['git_head'];self.frontend_done=len(env['FRONTEND']);self.checkpoint_mode=True
            self.next_sequence=518;self.initial_frame=self.initial_save=None
            self._source_only381={'phase':'semantic','admission':admission,'state':state,'gov':gov,'gift':gift,'seed':seed,'post':post}
            self.guard(reserve=False)

        async def call(self,session,request,path):
            if self._source_only381['phase']=='semantic' and request.get('tool')==env['SEMANTIC']:
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c6_overlay_relay import relay_compact
                return await startup_readiness_call(self,session,request,path,env,relay_compact=relay_compact)
            return await super().call(session,request,path)

        def check_before(self,tool,arguments):
            resume=self._source_only381
            if resume['phase']!='ready':
                require(tool==(env['SEMANTIC'] if resume['phase']=='semantic' else env['CAPABILITIES']) and arguments=={},
                    'one new SEM518 then CAP519 required')
                return
            return super().check_before(tool,arguments)

        def check_after(self,tool,arguments,body):
            resume=self._source_only381
            if resume['phase']=='semantic' and tool==env['SEMANTIC']:
                attempt=self.current_attempt;row=attempt['row'];request=attempt['request']
                require(request=={'sequence':518,'tool':env['SEMANTIC'],'arguments':{}}
                    and row['request']==request and row.get('client_error') is None and row['result']['is_error'] is False
                    and row['result']['result_type']=='complete' and env['decoded'](row)==body and self.next_sequence==518,
                    'actual successful first SEM518 context required')
                actual=env['frame'](body,semantic=True,expected_lifecycle=self.expected_lifecycle_binding)
                diag=body.get('diagnostics') or {};hello=diag.get('hello') or {}
                require(all(actual[k]==resume['state']['before'][k] for k in ('date_raw','actor_character_id','episode_run_id'))
                    and actual['native_revision']>=419 and diag.get('bridge_pid')==hello.get('pid')==153556
                    and diag.get('pipe_name')==self.launch['pipe']
                    and type(diag.get('connection_generation')) is int and diag['connection_generation']>0
                    and diag['connection_generation']==hello.get('connection_generation')
                    and hello.get('ck3_build_match') is True and hello.get('game_adapter_id')=='ck3-1.20.0.4-msvc-x64'
                    and hello.get('game_adapter_status')=='ready' and body.get('campaign_goal')==resume['state']['campaign_goal_anchor'],
                    'fresh same-Game day381/actor/episode/Native/goal differs')
                source=Path(attempt['response']).resolve(strict=True)
                require(source.is_relative_to(env['N'].resolve()) and env['read'](source,env['REPLY_RESERVE'])==row,
                    'actual readiness source row required')
                from root_score_month_samples_c4 import observe_semantic
                observe_semantic(env['N'],body,self.launch,source)
                self.semantic=body;self.initial_frame=copy.deepcopy(actual)
                self.cold_semantic_response_path=str(env['OUTBOX']/'0518-1-result.json')
                resume.update(phase='capabilities',opening=actual)
                return
            if resume['phase']=='capabilities' and tool==env['CAPABILITIES']:
                control=body.get('native_session_control') or {};opening=resume['opening']
                require(body.get('episode_run_id')==opening['episode_run_id'] and body.get('episode_character_id')==opening['actor_character_id']
                    and body.get('episode_identity_pending') is False and body.get('one_life_terminal') is False
                    and control.get('driver_state_restored') is True and control.get('driver_state_restore_kind')=='same_pid_hot'
                    and control.get('episode_binding_state')=='active_resumed' and control.get('driver_state_error') is None
                    and control.get('cold_candidate_rejection') is None,'actual same_pid_hot restore required')
                refs={Path(ref['original_source']).name:ref for ref in resume['seed']['source_refs']}
                for name in ('faction-gift-pending-v1.json','active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json'):
                    ref=refs[name];raw=Path(ref['original_source']).read_bytes()
                    require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'live retained sidecar differs: '+name)
                self.full_loop_state=copy.deepcopy(resume['state']);self.governance_result_state=copy.deepcopy(resume['gov']['state'])
                self.lifestyle_pending_focus=copy.deepcopy(resume['gov']['pending_focus']);self.initial_save=copy.deepcopy(self.full_loop_state['actual_saved_checkpoint'])
                self.full_loop_state.update(before=copy.deepcopy(opening),before_metrics_response=self.cold_semantic_response_path,
                    before_source_kind='actual_sameGame_source_only_warm_semantic_snapshot')
                pin=checked(resume['admission']['classifier_pin'],16384);self.result_classifier=env['load_cold_result_classifier']()
                path=Path(self.result_classifier.__code__.co_filename).resolve(strict=True);raw=path.read_bytes()
                require(path==Path(pin['source']).resolve() and len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                    'current classifier source differs')
                self.result_classifier_pin={k:pin[k] for k in ('source','sha256')}
                self.capabilities_verified=self.cold_readiness_verified=self.checkpoint_bootstrap_verified=True
                self.halted=self.halt_cause=self.current_attempt=self.held_control=None;resume['phase']='ready';self.persist_loop_state()
                env['atomic'](env['Q']/'ROOT-C7-SOURCE-ONLY-WARM-BOUND.json',{'schema':SCHEMA,'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'fresh_opening':opening,'fresh_semantic_response':self.cold_semantic_response_path,
                    'completed_cycles':219,'pending_cycle':None,'gift_pending_request_id':resume['gift']['pending']['request_id'],
                    'ordinary_cycle_credit':0,'business_action_credit':0,'original515_or_gift_replayed':False,
                    'retained_C6_publisher_started':resume['admission']['retained_C6_publisher_started'],
                    'retained_recording_job':resume['admission']['retained_recording_job'],
                    'T0_date_raw':self.full_loop_state['start_date_raw'],'SDK_source_commit':BUSINESS},limit=16384)
                return
            return super().check_after(tool,arguments,body)

    return SourceOnly381WarmQueue
