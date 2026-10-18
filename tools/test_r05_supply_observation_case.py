"""Focused synthetic controls through real R05 consumers; never live evidence."""
from pathlib import Path
import copy,datetime,gzip,importlib.util,json,sys,tempfile,time,unittest
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def family(events,callback):
    result=dict(status='available',source='native_natural_supply_callback_entry_return' if callback else 'native_natural_writer_entry_return',
        observer_installed=True,oldest_available_sequence=1 if events else 0,latest_sequence=len(events),
        overwritten_events=0,unattributed_capture_failures=0,event_count=len(events),events=events)
    result['identity_basis' if callback else 'membership_basis']='public_unit_and_native_carmy_full_ids_at_invocation' if callback else 'membership_at_query'
    return result

def packets(*,debit=5,callback=True,writer=True,aliases=True,stock=30000):
    frame,query=I.inputs();frame['date_raw']=53149000
    army=query['army_strengths'][0];army['current_supply_raw']=stock
    # Two DATA aliases resolve to one physical slot; only unique debit counts.
    if aliases:
        group=army['regiment_replenishment_records_v1'][0]
        alias=copy.deepcopy(group['records'][0]);alias['record_index']=1
        group['records'].append(alias);group['native_data_record_count']=2
    army[O.CALLBACK]=family([],True);army[O.WRITER]=family([],False)
    before=copy.deepcopy((frame,query))
    frame=copy.deepcopy(frame);query=copy.deepcopy(query);army=query['army_strengths'][0]
    frame.update(date_raw=frame['date_raw']+24,revision=32,native_revision=24,snapshot_id='native:24')
    query.update(queried_revision=32,queried_native_revision=24,queried_snapshot_id='native:24')
    army['current_soldiers']=100-debit
    for row in army['regiment_replenishment_records_v1'][0]['records']:
        row['current_soldiers']=row['effective_current_soldiers']=100-debit
    invocation=dict(invocation_token=7,native_thread_id=101,nesting_depth=1,parent_invocation_token=None,
        callback_caller_return_rva=O.DISPATCH_RETURN,callback_entry_rva=0x24E3410,receiver_basis='actual_24E3410_rcx_carmy')
    values=lambda s:dict(supply_raw=s,last_supply_update_date_raw64=before[0]['date_raw'],supply_updated_byte_raw=1,province_id=2644)
    cb=dict(sequence=1,army_id=18,native_carmy_id=85,passed_date_raw64=frame['date_raw'],
        caller_return_rva=O.DISPATCH_RETURN,before=values(stock),after=values(stock),same_instance_after=True,
        capture_failure_flags=0,supply_parent_invocation_v1=copy.deepcopy(invocation))
    pv=lambda n:dict(current_soldiers=n,maximum_soldiers=100,state_raw=0)
    count=2 if aliases else 1
    wr=dict(sequence=1,army_regiment_id=2,request_raw=500000,request_scale=100000,caller_return_rva=0x24E35FF,
        caller_kind='supply_preferred',observed_date_raw=frame['date_raw'],before_current_soldiers=100,
        before_maximum_soldiers=100,after_current_soldiers=200-debit,after_maximum_soldiers=200,
        same_instance_after=True,cached_current_delta=100-debit,cached_maximum_delta=100,capture_failure_flags=0,
        native_data_record_count=count,captured_data_record_count=count,physical_capture_complete=True,
        physical_debit_observed=True,actual_physical_soldier_debit=debit,physical_slot_count=1,
        data_aliases=[dict(data_record_index=i,persistent_regiment_id=123,data_chunk_ordinal=0,physical_slot_index=0) for i in range(count)],
        physical_slots=[dict(physical_slot_index=0,before=pv(100),after=pv(100-debit),same_instance_after=True)],
        supply_parent_context_v1=dict(invocation=invocation,army_id=18,native_carmy_id=85,passed_date_raw64=frame['date_raw'],
            stock_at_writer_entry_raw=stock,stock_scale=100000,receiver_identity_matches=True,capture_failure_flags=0))
    army[O.CALLBACK]=family([cb] if callback else [],True);army[O.WRITER]=family([wr] if writer else [],False)
    return before,(frame,query)

def normalize(pair):
    return O.normalized_army(*pair,actor_id=42,army_id=18,carmy_id=85,province_id=2644)

def settings():
    return dict(maximum_actual_days=2,maximum_modal_choices=4,max_packet_bytes=1024*1024,
        max_retained_capture_bytes=1024*1024,cleanup_capture_reserve_bytes=65536,
        one_day_timeout_seconds=2,normal_close_reserve_seconds=90,cleanup_save_reserve_seconds=30,
        poll_interval_seconds=0.1,speed=5,deadline_utc=datetime.datetime.fromtimestamp(time.time()+800,datetime.timezone.utc).isoformat())

def clock_status(start,*,stopped=False):
    return dict(state='triggered' if stopped else 'armed',generation=17,starting_date_raw=start,target_date_raw=start+24,
        last_observed_date_raw=start+24 if stopped else start,trigger_date_raw=start+24 if stopped else 0,speed=5,
        mode='terminal_or_sentinel',army_count=0,combat_count=0,completed_daily_ticks=1 if stopped else 0,
        intermediate_pause_count=0,trigger_flags=1 if stopped else 0,trigger_reasons=['date_deadline'] if stopped else [],
        signed_date_delta_from_target_raw=0,overshoot_days=0 if stopped else -1,pause_wrapper_called=stopped,
        pause_observed=stopped,terminal_observed=False,abnormal=False)

class Client:
    """Only the existing public queue boundary is synthetic."""
    def __init__(self,root,*,unknown_resume=False,no_callback=False,zero=False):
        self.output=root;self._hold=time.time()+600;self.calls=[];self.enabled=False;self.epoch=0
        self.before,self.after=packets(debit=0 if zero else 5,callback=not no_callback,writer=not no_callback,stock=0 if zero else 30000)
        self.frame,self.query=copy.deepcopy(self.before);self.start=self.frame['date_raw'];self.stopped=False
        self.unknown_resume=unknown_resume;self.case={'budgets':{'command_timeout':10}}
        self.selection=SimpleNamespace(case=self.case,effective_budgets=self.case['budgets'])
    def remaining(self):return self._hold-time.time()
    def guard(self,reserve=90):assert self.remaining()>reserve
    def validate_frame(self,frame,**kwargs):
        # Actual public native-envelope validator is the synthetic boundary.
        if kwargs.get('require_paused') is True:assert frame['paused'] is True
    def checkpoint(self,name,value):
        p=self.output/(name+'.json');p.write_text(json.dumps(value),encoding='utf-8');return p
    def execute_plan(self,steps,name,timeout=None,reserve=90):
        s=steps[0];tool,args=s['tool'],s['args'];self.calls.append((tool,copy.deepcopy(args)))
        if tool=='ck3_get_capabilities':r={'bridge_capabilities':list(O.CLOCK_CAPABILITIES),'action_steps':[]}
        elif tool=='ck3_take_snapshot':r=copy.deepcopy(self.frame)
        elif tool=='ck3_query_army_strengths':
            assert args['profile']=='observed_history_full_v1' and args['expected_revision']==self.frame['revision']
            r=copy.deepcopy(self.query)
        elif tool in ('ck3_query_army_observer_research_sampling_v1','ck3_set_army_observer_research_sampling_v1'):
            mode='query'
            if 'enabled' in args:
                self.enabled=args['enabled'];self.epoch+=1;mode='enable' if self.enabled else 'disable'
            f=dict(installed=True,available=True,capture_enabled=self.enabled,busy=False,clear_completed=not self.enabled,
                epoch=self.epoch,active_captures=0,retained_records=0,qualified_records=0,
                status='enabled' if self.enabled else 'disabled',readiness='awaiting_sample' if self.enabled else 'off')
            r=dict(step=mode+'-army-observer-research-sampling-v1',accepted=True,status='completed',
                army_observer_research_sampling_v1={'natural_phase':f},backend_id='native-headless',
                queried_revision=self.frame['revision'],queried_native_revision=self.frame['native_revision'],queried_date_raw=self.frame['date_raw'])
        elif tool=='ck3_execute_step':
            step=args['step']
            if step.startswith('research-arm-'):
                self.start=self.frame['date_raw'];self.stopped=False
                r={'step':step,'accepted':True,'status':'available','tactical_daily_sentinel':clock_status(self.start)}
            elif step=='resume-map':
                if self.frame['date_raw']==self.before[0]['date_raw']:
                    self.frame,self.query=copy.deepcopy(self.after)
                else:
                    self.frame['date_raw']+=24
                self.stopped=True
                if self.unknown_resume:raise TimeoutError('synthetic lost Resume ACK after actual day')
                r={'step':step,'accepted':True}
            elif step=='research-query-tactical-daily-sentinel-v1':
                r={'tactical_daily_sentinel':clock_status(self.start,stopped=self.stopped)}
            elif step=='pause-map':self.frame['paused']=True;r={'accepted':True}
            else:raise AssertionError(step)
        elif tool=='ck3_save_checkpoint':r={'accepted':True,'step':'save-checkpoint','checkpoint':{'status':'saved'}}
        else:raise AssertionError(tool)
        rows=[{'id':s['id'],'ok':True,'result':r}]
        self.checkpoint(name+'.actual-results',{'rows':rows});return rows

def init_result(client):
    return dict(pid=101,episode='synthetic-episode',army_id=18,carmy_id=85,
        independent_after=dict(actor_id=42,generation=3,province_id=2644),
        assessment=dict(status='prepared_low_stock',physical_soldiers_unchanged=True,
            initialization_at_zero=client.before[1]['army_strengths'][0]['current_supply_raw']==0,
            actual_after_stock_raw=client.before[1]['army_strengths'][0]['current_supply_raw']))

class Contracts(unittest.TestCase):
    def test_positive_aliases_periodic_parent_and_stock_operand(self):
        a,b=packets();r=O.assess_supply_window(normalize(a),normalize(b),exact_day_verified=True)
        self.assertTrue(r['R05_positive']);self.assertEqual(r['qualified_supply_physical_debit_soldiers'],5)
        self.assertFalse(r['updater_AL_observed']);self.assertFalse(r['whole_army_net_loss_attributed'])
        for stock in (1000000,-1):
            a,b=packets(stock=stock)
            self.assertFalse(O.assess_supply_window(normalize(a),normalize(b),exact_day_verified=True)['R05_positive'])
    def test_partial_physical_and_unknown_day_never_credit(self):
        a,b=packets();e=b[1]['army_strengths'][0][O.WRITER]['events'][0]
        e.update(physical_capture_complete=False,physical_debit_observed=False,actual_physical_soldier_debit=None)
        self.assertFalse(O.assess_supply_window(normalize(a),normalize(b),exact_day_verified=True)['R05_positive'])
        a,b=packets();self.assertFalse(O.assess_supply_window(normalize(a),normalize(b),exact_day_verified=False)['R05_positive'])
    def test_residual_periodic_supply_and_county_are_separate(self):
        for source,outer,flags,expected in [('periodic_callback',0x24E3638,2,True),('county_entry',0x24E2630,0,False)]:
            a,b=packets();e=b[1]['army_strengths'][0][O.WRITER]['events'][0]
            e.update(caller_return_rva=0x2A958E8,caller_kind='residual_allocator',residual_parent_context_v1=dict(
                parent_kind=4,invocation_token=8,native_thread_id=101,nesting_depth=2,parent_invocation_token=7,
                allocator_caller_return_rva=outer,enclosing_parent_kind=1 if source=='periodic_callback' else None,
                allocator_entry_rva=0x2A957E0,observed_continuation_rva=0x2A957E8,requested_budget=5,flags_raw=flags,
                request_source=source,army_id=18,native_carmy_id=85,matching_roster_occurrence=0,receiver_identity_matches=True,
                array_header_matches=True,writer_full_id_in_actual_array=True,source_complete=True,capture_failure_flags=0))
            self.assertIs(O.assess_supply_window(normalize(a),normalize(b),exact_day_verified=True)['R05_positive'],expected)
    def test_observation_minimum_does_not_reapply_initializer_floor(self):
        f,q=I.inputs();data=q['army_strengths'][0]['regiment_replenishment_records_v1'][0]['records'][0]
        data['current_soldiers']=data['effective_current_soldiers']=19
        with self.assertRaises(ValueError):M.target_witness(f,q,actor_id=42,army_id=18,carmy_id=85,province_id=2644)
        w=M.target_witness(f,q,actor_id=42,army_id=18,carmy_id=85,province_id=2644,minimum_physical_current=0)
        self.assertEqual(w['physical_slots'][0]['current_soldiers'],19)
    def run_client(self,**kw):
        temp=tempfile.TemporaryDirectory(dir=TEMP);self.addCleanup(temp.cleanup);root=Path(temp.name)
        client=Client(root,**kw)
        context=dict(output=str(root),machine_id='synthetic-machine-not-live',command_timeout=10,state_dir=str(root/'state'))
        r=O.observe_initialized_supply(client,settings(),context=context,initialization=init_result(client))
        return client,r
    def test_public_control_exact_day_positive_off_clear_normal_save(self):
        c,r=self.run_client();self.assertEqual(r['status'],'strict_supply_physical_positive')
        self.assertEqual(r['verified_actual_days'],1);self.assertTrue(r['R05_positive'])
        self.assertTrue(r['cleanup']['sampling_OFF_clear_verified']);self.assertTrue(r['cleanup']['save_verified'])
        self.assertFalse(c.enabled);self.assertTrue(r['normal_close_pending'])
        self.assertEqual(sum(tool=='ck3_execute_step' and a['step'].startswith('research-arm-') for tool,a in c.calls),1)
        self.assertTrue(any('before-full-history' in ref.get('path','') for ref in r['originals']))
    def test_unknown_resume_readonly_convergence_never_replays(self):
        c,r=self.run_client(unknown_resume=True)
        self.assertEqual(r['status'],'unknown_or_incomplete_observation_no_replay');self.assertFalse(r['R05_positive'])
        self.assertEqual(r['verified_actual_days'],0)
        self.assertFalse(r['unverified_day_readonly_assessment']['exact_day_verified'])
        self.assertTrue(r['cleanup']['sampling_OFF_clear_verified']);self.assertTrue(r['cleanup']['save_verified'])
        self.assertEqual(sum(tool=='ck3_execute_step' and a['step']=='resume-map' for tool,a in c.calls),1)
        self.assertEqual(sum(tool=='ck3_execute_step' and a['step'].startswith('research-arm-') for tool,a in c.calls),1)
    def test_known_modal_nonpaused_at_target_keeps_original_clock(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);c=Client(root);original=c.execute_plan
            def execute(steps,name,timeout=None,reserve=90):
                rows=original(steps,name,timeout,reserve)
                if steps[0]['tool']=='ck3_execute_step' and steps[0]['args']['step']=='resume-map':
                    c.frame['paused']=False;c.frame['active_event']={'instance_id':2,'option_count':1}
                return rows
            c.execute_plan=execute
            io=O.ObservationIO(c,settings(),context=dict(output=str(root),machine_id='synthetic-machine-not-live',
                command_timeout=10,state_dir=str(root/'state')),initialization=init_result(c))
            def resolve(frame):
                self.assertIs(frame['paused'],True);c.frame['active_event']=None
                io.modals.append({'synthetic_modal_resolution_boundary':True});return copy.deepcopy(c.frame)
            with mock.patch.object(io,'handle_modals',side_effect=resolve):
                frame,receipt=io.exact_day(normalize(c.before))
            self.assertEqual(frame['date_raw'],c.before[0]['date_raw']+24)
            self.assertTrue(receipt['exact_day_verified']);self.assertEqual(receipt['modal_actions'],1)
            self.assertEqual(sum(tool=='ck3_execute_step' and a['step']=='resume-map' for tool,a in c.calls),1)
    def test_zero_stock_zero_debit_and_day_cap_are_distinct(self):
        c,r=self.run_client(zero=True);self.assertTrue(r['initializer_at_zero']);self.assertFalse(r['R05_positive'])
        self.assertEqual(r['status'],'first_complete_callback_physical_debit_zero')
        a,b=packets(callback=False,writer=False);r=O.assess_supply_window(normalize(a),normalize(b),exact_day_verified=True)
        self.assertFalse(r['complete_natural_callback_observed']);self.assertTrue(r['no_retained_matching_writer'])
        c,r=self.run_client(no_callback=True)
        self.assertEqual(r['status'],'actual_day_cap_without_complete_matching_callback')
        self.assertEqual(r['verified_actual_days'],2);self.assertFalse(r['R05_positive'])
    def test_current_modal_capabilities_known_and_unknown_first_option(self):
        source=DEPENDENCIES/'docs/ck3-native-ai/evidence/episode04-pam-bull0004-r186-12004/actual-packet.json.gz'
        packet=json.loads(gzip.decompress(source.read_bytes()))
        # Frozen actual typed packet is replayed through a synthetic queue;
        # source-machine event facts are not new live observation.
        for unknown in (False,True):
            with self.subTest(unknown=unknown),tempfile.TemporaryDirectory(dir=TEMP) as t:
                root=Path(t);c=Client(root);typed=copy.deepcopy(packet['context'])
                if unknown:typed['event_definition_key']='r05_synthetic_unregistered.1'
                c.frame.update(date_raw=typed['date_raw'],native_revision=typed['snapshot_revision'],
                    snapshot_id='native:'+str(typed['snapshot_revision']),played_character={'character_id':31254,'alive':True},
                    active_event={'instance_id':typed['current_event_instance_id'],'option_count':2})
                initial=init_result(c);initial['independent_after']['actor_id']=31254
                context=dict(output=str(root),machine_id='synthetic-machine-not-live',command_timeout=10,state_dir=str(root/'state'))
                original=c.execute_plan
                def execute(steps,name,timeout=None,reserve=90):
                    s=steps[0];tool,args=s['tool'],s['args']
                    if tool=='ck3_get_capabilities':r={'action_steps':['select-event-option-1']}
                    elif tool=='ck3_query_current_event_window_context_v1':
                        r=dict(accepted=True,queried_revision=c.frame['revision'],queried_native_revision=c.frame['native_revision'],
                            queried_snapshot_id=c.frame['snapshot_id'],current_event_window_context=typed)
                    elif tool=='ck3_select_event_option':
                        self.assertEqual(args['option_number'],1);c.frame['active_event']=None
                        r=copy.deepcopy(packet['selection_receipt'])
                    else:return original(steps,name,timeout,reserve)
                    c.calls.append((tool,copy.deepcopy(args)))
                    rows=[{'id':s['id'],'ok':True,'result':r}];c.checkpoint(name+'.actual-results',{'rows':rows});return rows
                c.execute_plan=execute
                io=O.ObservationIO(c,settings(),context=context,initialization=initial)
                after=io.handle_modals(copy.deepcopy(c.frame));self.assertIsNone(after['active_event'])
                self.assertEqual(len(io.modals),1);self.assertTrue(io.modals[0]['old_window_gone_independent'])
                self.assertIs(io.modals[0]['offline_followup_required'],unknown)
                self.assertEqual(sum(tool=='ck3_select_event_option' for tool,a in c.calls),1)
    def test_interaction_left_reject_false_argument_and_disabled_left(self):
        factory=load('r05_pending_typed_factory',DEPENDENCIES/'ck3_autonomous_player/tests/unit/test_pending_character_interaction_context_v1_bridge.py')
        for left_enabled in (True,False):
            with self.subTest(left_enabled=left_enabled),tempfile.TemporaryDirectory(dir=TEMP) as t:
                root=Path(t);c=Client(root);typed=factory._frame()
                typed['legality']['reject'].update(allowed=left_enabled,reason=None if left_enabled else 'reject_not_legal')
                actor=typed['routing']['played_character_id'];instance=typed['pending_interaction_id']
                c.frame.update(date_raw=typed['date_raw'],native_revision=typed['snapshot_revision'],
                    snapshot_id='native:'+str(typed['snapshot_revision']),played_character={'character_id':actor,'alive':True},
                    pending_character_interaction={'instance_id':instance,'sender_character_id':typed['roles']['actor_character_id'],
                        'auto_accept_notification':False},active_wars=[])
                initial=init_result(c);initial['independent_after']['actor_id']=actor
                context=dict(output=str(root),machine_id='synthetic-machine-not-live',command_timeout=10,state_dir=str(root/'state'))
                original=c.execute_plan
                def execute(steps,name,timeout=None,reserve=90):
                    s=steps[0];tool,args=s['tool'],s['args']
                    if tool=='ck3_get_capabilities':r={'action_steps':['accept-pending-character-interaction','reject-pending-character-interaction']}
                    elif tool=='ck3_query_pending_character_interaction_context_v1':
                        r=dict(accepted=True,queried_revision=c.frame['revision'],queried_native_revision=c.frame['native_revision'],
                            queried_snapshot_id=c.frame['snapshot_id'],pending_character_interaction_context=typed)
                    elif tool=='ck3_reply_pending_character_interaction':
                        self.assertIs(args['accept'],False);c.frame['pending_character_interaction']=None
                        r={'accepted':False,'step':'reject-pending-character-interaction','paused':True,
                            'interaction_result':{'status':'rejected','instance_id':instance},'remaining_pending_character_interaction':None}
                    else:return original(steps,name,timeout,reserve)
                    c.calls.append((tool,copy.deepcopy(args)))
                    rows=[{'id':s['id'],'ok':True,'result':r}];c.checkpoint(name+'.actual-results',{'rows':rows});return rows
                c.execute_plan=execute;io=O.ObservationIO(c,settings(),context=context,initialization=initial)
                if left_enabled:
                    after=io.handle_modals(copy.deepcopy(c.frame));self.assertIsNone(after['pending_character_interaction'])
                    row=io.modals[0];self.assertIs(row['interaction_accept_argument'],False)
                    self.assertIsNone(row['command_acknowledged']);self.assertTrue(row['control_row_ok'])
                    self.assertTrue(row['old_window_gone_independent'])
                    self.assertEqual(sum(tool=='ck3_reply_pending_character_interaction' for tool,a in c.calls),1)
                else:
                    with self.assertRaises(ValueError):io.handle_modals(copy.deepcopy(c.frame))
                    self.assertFalse(any(tool=='ck3_reply_pending_character_interaction' for tool,a in c.calls))
    def test_public_adapter_continuation_and_verify_need_cleanup_and_close(self):
        temp=tempfile.TemporaryDirectory(dir=TEMP);self.addCleanup(temp.cleanup);root=Path(temp.name)
        client=Client(root);init=init_result(client)
        delegate=SimpleNamespace(run_case=lambda context,c:c.checkpoint('r05-controlled-initializer-outcome',init),
            verify_case=lambda context:{'gui_contract_qualified':True})
        ctx=dict(output=str(root),repo_root=str(ROOT),case_inputs={'observation':settings()},state_dir=str(root/'state'))
        with mock.patch.object(A,'initializer',return_value=delegate),mock.patch('ck3_live_run_id.current_machine_id',return_value='synthetic-machine-not-live'):
            r=A.run_case(ctx,client);self.assertEqual(r['verified_actual_days'],1)
            self.assertFalse(A.verify_case(ctx)['R05_pass'])
            client.checkpoint('normal-close-result',{'normal_close_qualified':True})
            self.assertTrue(A.verify_case(ctx)['R05_pass'])
    def test_initializer_commands_preserve_cleanup_room(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            client=Client(Path(t));s=O.observation_settings(settings())
            proxy=A.InitializerBudget(client,s,10)
            frame=proxy.snapshot();self.assertEqual(frame['date_raw'],client.frame['date_raw'])
            client._hold=time.time()+119
            count=len(client.calls)
            with self.assertRaises(ValueError):proxy.snapshot()
            self.assertEqual(len(client.calls),count)
    def test_pre_enable_failure_does_not_claim_or_disable_foreign_sampling(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);c=Client(root);c.enabled=True
            context=dict(output=str(root),machine_id='synthetic-machine-not-live',command_timeout=10,state_dir=str(root/'state'))
            r=O.observe_initialized_supply(c,settings(),context=context,initialization=init_result(c))
            self.assertEqual(r['status'],'unknown_or_incomplete_observation_no_replay')
            self.assertFalse(r['cleanup']['sampling_OFF_clear_verified']);self.assertFalse(r['cleanup']['sampling_owned'])
            self.assertTrue(c.enabled);self.assertFalse(any(tool=='ck3_set_army_observer_research_sampling_v1' for tool,a in c.calls))
            self.assertTrue(r['cleanup']['save_verified']);self.assertFalse(r['R05_positive'])

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--initializer-root',type=Path,default=ROOT);p.add_argument('--temp-root',type=Path,required=True)
    args=p.parse_args();DEPENDENCIES=args.repo_root.resolve();TEMP=args.temp_root;TEMP.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(DEPENDENCIES/'ck3_autonomous_player/src'),str(DEPENDENCIES/'tools')]
    M=load('xar_autoplayer.bridge.r05_low_supply_fixture',ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
    I=load('r05_initializer_fixture_factory',args.initializer_root/'tools/test_r05_low_supply_fixture.py');I.M=M
    O=load('xar_autoplayer.bridge.r05_supply_observation_case',ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_supply_observation_case.py')
    A=load('r05_observe_public_adapter',ROOT/'tools/ck3_mod_acceptance_cases/r05_initialize_observe_adapter.py')
    unittest.main(argv=[__file__],verbosity=2)
