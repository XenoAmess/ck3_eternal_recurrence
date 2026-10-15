"""Offline boundary tests; generated packets are synthetic, not gameplay evidence."""
import ast,copy,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('common_t0_checker',HERE.parent/'validate_common_t0_control.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
REPO=Path(__file__).resolve().parents[6]

class CommonT0Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.freeze=json.loads((REPO/'docs/ck3-native-ai/evidence/episode04-common-t0-control-12004/common-t0-r0173.receipt-freeze.actual-a01.json').read_text(encoding='utf-8'))
        self.freeze['machine_id']='archive-fixture-machine'
        self.seed=self.freeze['T0'];self.date=self.seed['date_raw']
        self.j=json.loads((HERE/'fixtures/payment_compiled_personal.json').read_text())['value']
        self.j['machine_id']='archive-fixture-machine'
        self.m=json.loads((HERE.parent/'common_t0_control.manifest.template.json').read_text())
        self.m['machine_id']='archive-fixture-machine'
        self.m['source_contract']['source_head']='a'*40
        self.m['source_contract']['bridge_dll_sha256']='b'*64
        self.m['common_t0_freeze']=self.writepin('freeze.json',self.freeze)
        self.arm={'assets_root':'control','run_dir':'control/run-new','run_id':'run-new',
          'pid':9001,'create_filetime':123456789,'generation':1,'episode':'new-episode',
          'prepared':'control/prepared.json','identity_receipt':'control/identity.json',
          'admission':'control/admission.json','driver_state_path':'control/state/native-session/driver-state.json',
          't0_snapshot':'control/run-new/responses/t0.json','t0_ordinary_response':'control/run-new/responses/ordinary.json',
          'baseline_cash_before_snapshot':'control/run-new/responses/t0.json','baseline_cash':'control/run-new/responses/cash.json',
          'halt_response':'control/run-new/responses/halt.json','after_halt_snapshot':'control/run-new/responses/after-halt.json',
          'daily_summaries':[]}
        self.m['control']=self.arm
        self.s={'paused':True,'map_ready':True,'revision':5,'native_revision':4,'date_raw':self.date,
          'episode_run_id':'new-episode','played_character':{'character_id':31254,'alive':True},
          'diagnostics':{'bridge_pid':9001,'connection_generation':1,'hello':{
              'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':self.m['source_contract']['executable_sha256']}},
          'active_wars':self.seed['active_wars'],'player_armies':[{'army_id':18,'owner_character_id':31254,
              'controllable':True,'current_province_id':2624,'move_target_province_id':1033,
              'route_read_status':'complete_nonempty','route_source_count':4,'route_province_ids':[1036,8653,1034,1033],
              'army_state':'moving','in_combat':False,'retreating':False}]}
        self.packet(self.arm['t0_snapshot'],'ck3_take_snapshot',self.s)
        halted=copy.deepcopy(self.s);halted['player_armies'][0].update(route_read_status='complete_empty',
            route_source_count=0,route_province_ids=[],move_target_province_id=None,army_state='stationary')
        self.packet(self.arm['after_halt_snapshot'],'ck3_take_snapshot',halted)
        self.packet(self.arm['halt_response'],'ck3_execute_step',{'accepted':True},{'step':'halt-army-18'})
        self.put(self.arm['prepared'],{'machine_id':self.m['machine_id'],'assets_root':'control','state_dir':'control/state',
          'target_build':{'version':'1.20.0.4','steam_build':25734779,'exe_sha256':self.m['source_contract']['executable_sha256']},
          'game':{'sha256':self.m['source_contract']['executable_sha256']},'bridge_dll':{'sha256':'b'*64},
          'checkpoint':{'source':{'save':{'sha256':self.seed['save']['sha256'],'bytes':self.seed['save']['size']}}}})
        self.put(self.arm['identity_receipt'],{'machine_id':self.m['machine_id'],'source_head':'a'*40,
          'run_id':'run-new','pid':9001,'process_creation_filetime_100ns':123456789,'connection_generation':1,
          'episode_run_id':'new-episode','actual_runtime_character_full_id':31254,'initial_date_raw':self.date,
          'stable_character_intent':{'historical_id':1128,'bookmark_character_name_key':'bookmark_rags_to_riches_duke_robert'}})
        # An admitted but empty baseline is a valid fence, never proof of zero expenses.
        j=copy.deepcopy(self.j);j.update(records=[],natural_parent_returns=[],qualified_boarding_debits=[],latest_sequence=0,oldest_sequence=0)
        j['sampling'].update(retained_records=0,qualified_records=0)
        j['natural_journal_status']['retained_records']=0
        j['current_session'].update(pid=9001,process_create_time_100ns=123456789,connection_generation=1,
            player_character_full_id=31254,snapshot_revision=4,native_date_raw=self.date)
        self.j0=j
        self.put(self.arm['admission'],{'machine_id':self.m['machine_id'],'session':j['current_session'],'sampling':j['sampling']})
        self.packet(self.arm['baseline_cash'],'ck3_query_war_cash_current_resources_private_v1',{
            'snapshot_revision':4,'date_raw':self.date,'current_treasury':self.seed['treasury'],
            'war_payment_observations_v1':j,'war_payment_control_v1':{'requested':'query','accepted':True,'reason':'queried'}},
            {'payment_sampling':'query','expected_revision':5})
        army={'army_id':18,'current_movement_progress':{'normalized_edge_progress':self.seed['progress'],
              'loaded_movement_lock_cutoff':self.seed['cutoff']},'current_soldiers':1196,'maximum_soldiers':1196,'current_supply_raw':30000000}
        raw={'queried_date_raw':self.date,'queried_connection_generation':1,'queried_episode_run_id':'new-episode',
             'query_sequence':1,'army_strengths_query_scope':{'army_ids':[18]},'queried_revision':5,'queried_native_revision':4,
             'army_strengths':[army]}
        ref=self.writepin('control/state/native-session/ordinary.json',raw)
        ref.update(kind='complete-driver-army-query-result-json-v1',wire_bytes_preserved=False)
        self.packet(self.arm['t0_ordinary_response'],'ck3_query_army_strengths',{'query_sequence':1,
            'army_strengths_profile':'ordinary_core_v1','source':{'revision':5,'native_revision':4}},extra={
            'army_history_evidence':{'full_result_preserved':True,'request_id':'ordinary.json','query_sequence':1,
             'army_strengths_profile':'ordinary_core_v1','queried_revision':5,'queried_native_revision':4,'raw_result_reference':ref}})
    def put(self,path,value):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8');return p
    def writepin(self,path,value):
        p=self.put(path,value);raw=p.read_bytes();return {'path':path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    def packet(self,path,tool,body,args=None,extra=None):
        row={'machine_id':'archive-fixture-machine','is_error':False,
             'request':{'tool':tool,'request_id':Path(path).name,'arguments':args or {}},'body':body}
        row.update(extra or {});self.put(path,row)
    def mutate(self,path,change):
        row=json.loads((self.root/path).read_text());change(row);self.put(path,row)
    def check(self):return v.check(self.m,'baseline',self.root)
    def test_valid_foreign_machine_archive_baseline(self):
        self.assertEqual(self.check()['control_baseline'],'PASS')
    def test_actor_mix_rejected(self):
        self.mutate(self.arm['t0_snapshot'],lambda x:x['body']['played_character'].update(character_id=29829))
        with self.assertRaisesRegex(ValueError,'actor'):self.check()
    def test_source_commit_mix_rejected(self):
        self.mutate(self.arm['identity_receipt'],lambda x:x.update(source_head='f'*40))
        with self.assertRaisesRegex(ValueError,'source binding'):self.check()
    def test_executable_build_mix_rejected(self):
        self.mutate(self.arm['prepared'],lambda x:x['game'].update(sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'exact source'):self.check()
    def test_dll_mix_rejected(self):
        self.mutate(self.arm['prepared'],lambda x:x['bridge_dll'].update(sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'exact source'):self.check()
    def test_other_window_cash_with_same_numeric_epoch_rejected(self):
        self.mutate(self.arm['baseline_cash'],lambda x:x['body']['war_payment_observations_v1']['current_session'].update(controlled_window_id=999))
        with self.assertRaisesRegex(ValueError,'window cash'):self.check()
    def test_other_creation_time_rejected(self):
        self.mutate(self.arm['baseline_cash'],lambda x:x['body']['war_payment_observations_v1']['current_session'].update(process_create_time_100ns=123456790))
        with self.assertRaisesRegex(ValueError,'window cash'):self.check()
    def test_two_arms_cannot_share_process_by_changing_run_name(self):
        a={'window_identity':['fixture','a',9,10,1,1],'binding':{'run_id':'a','pid':9,'create_filetime':10}}
        b={'window_identity':['fixture','b',9,10,1,1],'binding':{'run_id':'b','pid':9,'create_filetime':10}}
        with self.assertRaisesRegex(ValueError,'independent run and process'):v.distinct_windows(a,b)
    def test_archive_escape_rejected(self):
        v.configure(self.m,self.root)
        with self.assertRaisesRegex(ValueError,'escapes'):v.resolve('../other.json')
    def test_unmapped_old_absolute_rejected(self):
        v.configure(self.m,self.root)
        with self.assertRaisesRegex(ValueError,'prefix map'):v.resolve('C:/old/response.json')
    def test_explicit_archive_mapping(self):
        self.m['archive_prefix_map']={'C:/old':'control'};v.configure(self.m,self.root)
        self.assertEqual(v.resolve('C:/old/prepared.json'),self.root/'control/prepared.json')
    def test_raw_callback_amount_not_net(self):
        s=self.j['current_session'];snap=copy.deepcopy(self.s)
        snap.update(native_revision=s['snapshot_revision'],date_raw=s['native_date_raw']&0xffffffff)
        snap['played_character']['character_id']=s['player_character_full_id']
        snap['diagnostics'].update(bridge_pid=s['pid'],connection_generation=s['connection_generation'])
        j=v.normalize_journal(self.j,snapshot=snap,machine_id='archive-fixture-machine')
        self.assertEqual(len(j['qualified_boarding_debits']),1)
        self.assertEqual(j['balance_boundary'],'whole_original_callback_entry_return')
        self.assertEqual(j['maintenance_attribution'],'unclosed')
        bad=copy.deepcopy(self.j);bad['qualified_boarding_debits'][0]['requested_amount_raw']+=1
        with self.assertRaisesRegex(ValueError,'raw parent/amount/return'):v.normalize_journal(bad,snapshot=snap,machine_id='archive-fixture-machine')
    def test_high_storage_bits_not_relabelled_date(self):
        self.mutate(self.arm['baseline_cash'],lambda x:x['body']['war_payment_observations_v1']['current_session'].update(native_date_raw=(7<<32)+self.date))
        self.assertEqual(self.check()['control_baseline'],'PASS')
    def test_frozen_pin_mutation_rejected(self):
        self.mutate('freeze.json',lambda x:x['T0'].update(actor=1))
        with self.assertRaisesRegex(ValueError,'projection pin'):self.check()
    def test_pending_control_not_reported_observed(self):
        self.arm['pid']=None
        with self.assertRaisesRegex(ValueError,'pending'):self.check()
    def test_already_embarked_control_rejected(self):
        self.mutate(self.arm['after_halt_snapshot'],lambda x:x['body']['player_armies'][0].update(army_state='embarked'))
        with self.assertRaisesRegex(ValueError,'without route/boarding'):self.check()

    def test_halt_from_other_run_rejected(self):
        old=self.arm['halt_response']
        self.arm['halt_response']='another-run/responses/halt.json'
        self.put(self.arm['halt_response'],json.loads((self.root/old).read_text()))
        with self.assertRaisesRegex(ValueError,'Halt source outside'):self.check()
    def test_ordinary_reference_wrong_episode_rejected(self):
        path='control/state/native-session/ordinary.json'
        self.mutate(path,lambda x:x.update(queried_episode_run_id='old-episode'))
        raw=(self.root/path).read_bytes()
        self.mutate(self.arm['t0_ordinary_response'],lambda x:x['army_history_evidence']['raw_result_reference'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        with self.assertRaisesRegex(ValueError,'other query/window'):self.check()
    def test_partial_sidecar_rejected_before_json_parse(self):
        path=self.root/'control/state/native-session/ordinary.json'
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError,'size differs'):self.check()

    def binder_inputs(self):
        # If imported/executed, the reviewed input would fail. Binding must only parse it.
        text="from pathlib import Path\nBASE=Path('old-base')\nREPO=Path('old-repo')\nASSETS=BASE/'old-assets'\nRUN_ID='old'\nPID=1\nCREATED=1\nEPISODE='old'\nGEN=1\nSTART=1\nDRIVER_STATE=BASE/'old-state'\nraise RuntimeError('binding must never execute reviewed source')\nhelper=BASE/'scoped_requests_a04.py'\ndef check_frame(frame,date=None,paused=True): return frame\nclass Runner: pass\nif __name__=='__main__': pass\n"
        (self.root/'reviewed.py').write_text(text,encoding='utf-8')
        self.arm['request_helper']='helper.py'
        (self.root/'helper.py').write_text("raise RuntimeError('helper must not be imported')\n",encoding='utf-8')
        self.put('pair.json',self.m)
        return [sys.executable,'-B',str(HERE.parent/'bind_common_t0_control_runner.py'),
            '--archive-root',str(self.root),'--manifest','pair.json','--runner-source','reviewed.py',
            '--runner-sha256',hashlib.sha256((self.root/'reviewed.py').read_bytes()).hexdigest(),'--output',str(self.root/'candidate.py')]
    def test_binder_rebinds_paths_without_running_source_or_helper(self):
        cmd=self.binder_inputs();done=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(done.returncode,0,done.stderr)
        tree=ast.parse((self.root/'candidate.py').read_text())
        assignments={node.targets[0].id:node.value for node in tree.body
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
        self.assertEqual(ast.literal_eval(assignments['BASE'].args[0]),str(self.root))
        self.assertEqual(ast.literal_eval(assignments['REPO'].args[0]),str(REPO))
        self.assertTrue((self.root/'candidate.binding.json').exists())
    def test_binder_wrong_source_sha_cannot_emit(self):
        cmd=self.binder_inputs();cmd[cmd.index('--runner-sha256')+1]='0'*64
        done=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(done.returncode,0)
        self.assertFalse((self.root/'candidate.py').exists())

if __name__=='__main__':unittest.main()
