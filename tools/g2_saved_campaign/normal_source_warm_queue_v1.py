"""Normal clean same-Game source maintenance; boundary comes from sealed inputs."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
SCHEMA='xar.normal-clean-source-warm/v1'
SIDECARS=('faction-gift-pending-v1.json','active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json')


def require(ok,why):
    if not ok:raise ValueError('normal source warm denied: '+why)


def checked(ref,limit=262144):
    path=Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)<=limit and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],
        'exact bounded input differs: '+str(path))
    return json.loads(raw)


def normal_warm_inputs(admission):
    require(admission['schema']==SCHEMA and admission['machine_id']==MACHINE,'normal clean admission required')
    seed=checked(admission['clean_seed']);post=checked(admission['post_close']);b=admission['boundary']
    refs={Path(r['original_source']).name:r for r in seed['source_refs']}
    postrefs={Path(r['original_source']).name:r for r in post['source_refs']}
    state=checked(refs['ROOT-CUMULATIVE-LOOP-STATE.json']);gov=checked(refs['ROOT-GOVERNANCE-RESULT-STATE.json'])
    for name in ('ROOT-CUMULATIVE-LOOP-STATE.json','ROOT-GOVERNANCE-RESULT-STATE.json',*SIDECARS):
        require(refs[name]['sha256']==postrefs[name]['sha256'] and checked(refs[name])==checked(postrefs[name]),
            'clean seed and actual postclose differ: '+name)
    before=state['before']
    require(seed['machine_id']==post['machine_id']==MACHINE and state['completed_cycles']==b['completed_cycles']
        and gov['completed_cycles']==b['completed_cycles'] and state['start_date_raw']==b['start_date_raw']
        and all(state.get(k) is None for k in ('pending_cycle','pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and gov['pending_cycle'] is None and before['native_revision']==b['min_native_revision']
        and all(before[k]==b[k] for k in ('date_raw','actor_character_id','episode_run_id')),
        'one exact normal clean boundary required; no failed-result recovery')
    for key in ('Game_pid','Game_creation_filetime','completed_cycles','date_raw','actor_character_id','min_native_revision','next_sequence','start_date_raw'):
        require(type(b[key]) is int and b[key]>0,'positive boundary scalar required: '+key)
    require(isinstance(b['episode_run_id'],str) and b['episode_run_id'].startswith(f"native-{b['actor_character_id']}-")
        and b['date_raw']>=b['start_date_raw'],'played actor/episode boundary required')
    closed=checked(admission['old_closed']);pair=checked(admission['old_pair'])
    require(closed['status']=='ACTUAL_BOTH_SDK_EXITS_OBSERVED' and closed['normal'] is True
        and closed['launcher_exit_code']==0 and closed['machine_id']==MACHINE
        and closed['Game_stopped'] is False and closed['recording_stopped'] is False
        and len(closed['processes'])==len(pair['processes'])==2,'actual normal SDK-only closure required')
    for p in closed['processes']:
        require(p['exit_code']==0 and p['kernel_exit_observed'] is True and p['wait_result']==0 and p['observation_error'] is None
            and any(q['role']==p['role'] and all(q[k]==p[k] for k in ('pid','creation_filetime','executable')) for q in pair['processes']),
            'exact old SDK generation must be closed')
    require(post['actual_sdk_closed']==admission['old_closed']
        and post['Game_pid']==b['Game_pid'] and post['Game_creation_filetime']==b['Game_creation_filetime']
        and post['completed_cycles']==b['completed_cycles'] and post['next_sequence']==b['next_sequence']
        and post['loop_cached_checkpoint']==state['actual_saved_checkpoint']
        and type(post['closed_Driver']['bytes']) is int and post['closed_Driver']['bytes']>0
        and len(post['closed_Driver']['sha256'])==64,
        'postclose source and canonical Driver provenance required without reading Driver body')
    return state,gov,seed,post,b,refs


def make_normal_source_warm_queue_v1(base,env,*,admission_path):
    class NormalSourceWarmQueue(base):
        def preflight(self):
            from root_continuous_segment_auto_c6 import verify_segment
            from root_decision_text_api_c6 import load_api,started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission=env['read'](Path(admission_path),65536);state,gov,seed,post,b,refs=normal_warm_inputs(admission)
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir()))
                and admission['next_sequence']==b['next_sequence'] and self.launch['pid']==b['Game_pid']
                and self.launch['creation_filetime']==b['Game_creation_filetime'],'new C9 queue/same physical Game required')
            for key,name in (('queue_source','root_p37c9_sdk_queue.py'),('entry_source','root_p37c9_mcp_entry.py'),
                    ('native_binding_source','root_native_build_binding_p37c9.py')):
                ref=admission[key];path=Path(ref['path']).resolve(strict=True);raw=path.read_bytes()
                require(path==(env['N']/name).resolve() and len(raw)<=1024**2 and len(raw)==ref['bytes']
                    and hashlib.sha256(raw).hexdigest()==ref['sha256'],'actual C9 source differs: '+name)
            require(Path(env['__file__']).resolve()==Path(admission['queue_source']['path']).resolve(),'executing C9 queue differs')
            self.job,self.record_started,self.first=verify_segment(env['N'],env['R'],self.launch,self.record_job,
                self.args.first_frame_admission,env['read'],env['aware'],env['now'])
            api=load_api(env['N'])
            require(started_reference(env['N'],api)==admission['retained_C6_publisher_started']
                and self.record_job.resolve()==Path(admission['retained_recording_job']).resolve()
                and self.args.first_frame_admission.resolve()==Path(admission['retained_first_frame_admission']).resolve()
                and api.process_identity(b['Game_pid'])['creation_filetime']==b['Game_creation_filetime'],
                'retained C6 publisher/recording and exact Game required')
            absence=checked(admission['mod_absence'])
            require(absence['machine_id']==MACHINE and absence['game_pid']==b['Game_pid']
                and absence['game_creation_filetime']==b['Game_creation_filetime'],'physical Game mod absence differs')
            self.expected_lifecycle_binding=bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest),'verified_mod_absence':absence},
                lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding==state['actual_saved_checkpoint']['succession_lifecycle'],'lifecycle differs')
            freeze=checked(admission['sdk_freeze'],2*1024**2)
            require(Path(admission['sdk_freeze']['path']).name=='ROOT-FINAL-SDK-FREEZE-P37C9.json'
                and isinstance(admission['business_source_commit'],str) and len(admission['business_source_commit'])==40
                and freeze['business_source_commit']==admission['business_source_commit']
                and Path(admission['current_map_admission']).resolve()==(env['N']/'ROOT-CAMPAIGN-MAP-ADMITTED-C9.json').resolve(),
                'Root-pinned new source and explicit C9 map required')
            self.frozen_head=freeze['git_head'];self.frontend_done=len(env['FRONTEND']);self.checkpoint_mode=True
            self.next_sequence=b['next_sequence'];self.initial_frame=self.initial_save=None
            self._normal_source_warm={'phase':'semantic','admission':admission,'state':state,'gov':gov,
                'seed':seed,'post':post,'boundary':b,'refs':refs}
            self.guard(reserve=False)

        async def call(self,session,request,path):
            if self._normal_source_warm['phase']=='semantic' and request.get('tool')==env['SEMANTIC']:
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c6_overlay_relay import relay_compact
                return await startup_readiness_call(self,session,request,path,env,relay_compact=relay_compact)
            return await super().call(session,request,path)

        def check_before(self,tool,arguments):
            resume=self._normal_source_warm
            if resume['phase']!='ready':
                require(tool==(env['SEMANTIC'] if resume['phase']=='semantic' else env['CAPABILITIES']) and arguments=={},
                    'normal fresh semantic then capabilities required')
                return
            return super().check_before(tool,arguments)

        def check_after(self,tool,arguments,body):
            resume=self._normal_source_warm;b=resume['boundary'];sequence=b['next_sequence']
            if resume['phase']=='semantic' and tool==env['SEMANTIC']:
                attempt=self.current_attempt;row=attempt['row'];request=attempt['request']
                require(request=={'sequence':sequence,'tool':env['SEMANTIC'],'arguments':{}}
                    and row['request']==request and row.get('client_error') is None and row['result']['is_error'] is False
                    and row['result']['result_type']=='complete' and env['decoded'](row)==body and self.next_sequence==sequence,
                    'actual successful first semantic context required')
                actual=env['frame'](body,semantic=True,expected_lifecycle=self.expected_lifecycle_binding)
                diag=body.get('diagnostics') or {};hello=diag.get('hello') or {}
                require(all(actual[k]==b[k] for k in ('date_raw','actor_character_id','episode_run_id'))
                    and actual['native_revision']>=b['min_native_revision'] and diag.get('bridge_pid')==hello.get('pid')==b['Game_pid']
                    and diag.get('pipe_name')==self.launch['pipe']
                    and type(diag.get('connection_generation')) is int and diag['connection_generation']>0
                    and diag['connection_generation']==hello.get('connection_generation')
                    and hello.get('ck3_build_match') is True and hello.get('game_adapter_id')=='ck3-1.20.0.4-msvc-x64'
                    and hello.get('game_adapter_status')=='ready' and body.get('campaign_goal')==resume['state']['campaign_goal_anchor'],
                    'fresh same-Game actor/episode/date/Native/goal differs')
                source=Path(attempt['response']).resolve(strict=True)
                require(source.is_relative_to(env['N'].resolve()) and env['read'](source,env['REPLY_RESERVE'])==row,'actual readiness row required')
                from root_score_month_samples_c4 import observe_semantic
                observe_semantic(env['N'],body,self.launch,source)
                self.semantic=body;self.initial_frame=copy.deepcopy(actual)
                self.cold_semantic_response_path=str(env['OUTBOX']/f'{sequence:04d}-1-result.json')
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
                self.full_loop_state.update(before=copy.deepcopy(opening),before_metrics_response=self.cold_semantic_response_path,
                    before_source_kind='actual_sameGame_normal_source_warm_semantic_snapshot')
                pin=checked(resume['admission']['classifier_pin'],16384);self.result_classifier=env['load_cold_result_classifier']()
                path=Path(self.result_classifier.__code__.co_filename).resolve(strict=True);raw=path.read_bytes()
                require(path==Path(pin['source']).resolve() and len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                    'current classifier source differs')
                self.result_classifier_pin={k:pin[k] for k in ('source','sha256')}
                self.capabilities_verified=self.cold_readiness_verified=self.checkpoint_bootstrap_verified=True
                self.halted=self.halt_cause=self.current_attempt=self.held_control=None;resume['phase']='ready';self.persist_loop_state()
                env['atomic'](env['Q']/'ROOT-C9-NORMAL-SOURCE-WARM-BOUND.json',{'schema':SCHEMA,'machine_id':MACHINE,
                    'observed_at_utc':env['now']().isoformat(),'fresh_opening':opening,'fresh_semantic_response':self.cold_semantic_response_path,
                    'completed_cycles':self.full_loop_state['completed_cycles'],'pending_cycle':None,'ordinary_cycle_credit':0,'business_action_credit':0,
                    'source_seed':resume['admission']['clean_seed'],'postclose_source':resume['admission']['post_close'],
                    'T0_date_raw':self.full_loop_state['start_date_raw'],'SDK_source_commit':resume['admission']['business_source_commit'],
                    'old_result_replayed':False,'retained_C6_publisher_started':resume['admission']['retained_C6_publisher_started']},limit=16384)
                return
            return super().check_after(tool,arguments,body)
    return NormalSourceWarmQueue
