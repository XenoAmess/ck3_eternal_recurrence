"""Focused controlled-initializer contracts. Synthetic relay only, no CK3."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile,unittest
from unittest import mock
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def inputs():
    row={'army_id':18,'owner_character_id':42,'current_province_id':2644,'controllable':True,'source':'native',
        'in_combat':False,'retreating':False,'army_state':'regular','army_state_code':1,
        'route_read_status':'complete_empty','route_source_count':0,'route_province_ids':[]}
    frame={'snapshot_id':'native:23','revision':31,'native_revision':23,'date_raw':53149000,'episode_run_id':'synthetic-episode',
        'paused':True,'map_ready':True,'active_event':None,'pending_character_interaction':None,
        'played_character':{'character_id':42,'alive':True},'player_armies':[row],
        'diagnostics':{'bridge_pid':101,'connection_generation':3,
            'hello':{'game_version':'1.20.0.4','executable_sha256':M.EXE_SHA}}}
    data={'record_index':0,'persistent_regiment_id':123,'chunk_index':0,'current_soldiers':100,'maximum_soldiers':100,
        'effective_current_soldiers':100,'state_raw':0,'native_can_replenish':True,'native_chunk_can_replenish':True,
        'persistent_monthly_replenishment_fraction_raw':0,'persistent_prepared_replenishment_fraction_raw':0,
        'persistent_monthly_replenishment_fraction_scale':100000,'persistent_prepared_replenishment_fraction_scale':100000,
        'status':'available','unavailable_reason':None,'chunk_army_regiment_id':2}
    regiment={'army_regiment_id':2,'source':'native_all_data_records','status':'available','ready':True,
        'native_data_record_count':1,'unavailable_reason':None,'records':[data]}
    fixed={'source':'native_scoped_fixed_chunk0_preparation_inputs','entry_kind':'current_frozen_context_preparation',
        'status':'available','ready':True,'subject_army_id':18,'subject_carmy_id':85,'referenced_persistent_ids_complete':True,
        'unavailable_reason':None,'persistent_regiments':[{'persistent_regiment_id':123,'fixed_chunk_index':0,
            'status':'available','ready':True,'unavailable_reason':None,'fraction_scale':100000,
            'containing_guard_138_raw':0,'containing_definition_magic_38':123456,
            'native_fixed_chunk0_can_replenish':True,'fresh_fraction_raw':0}]}
    army={'status':'available','scope_role':'player','army_id':18,'native_carmy_id':85,'regiment_count':1,
        'current_soldiers':100,'maximum_soldiers':100,'gathering_days_ready':True,'gathering_days_left':0,
        'current_supply_raw':30000000,'current_supply_scale':100000,
        'current_supply_capacity_raw':30000000,'current_supply_capacity_scale':100000,
        'current_supply_change_monthly_raw':-175438,'current_supply_change_monthly_scale':100000,
        'regiment_replenishment_records_v1':[regiment],'fixed_chunk0_preparation_inputs_v1':fixed}
    query={'queried_snapshot_id':frame['snapshot_id'],'queried_revision':31,'queried_native_revision':23,'army_strengths':[army]}
    return frame,query

class Relay:
    def __init__(self,run,machine,*,capabilities=None,unknown=False):
        self.RUN=run;self.CONTEXT={'machine_id':machine};self.calls=[];self.frame,self.query=inputs()
        self.capabilities=list(M.REQUIRED_CAPABILITIES if capabilities is None else capabilities);self.unknown=unknown
    def snapshot(self,identifier):
        self.calls.append(('snapshot',identifier));return copy.deepcopy(self.frame)
    def request(self,identifier,tool,args):
        self.calls.append((tool,copy.deepcopy(args)))
        if tool=='ck3_get_capabilities':return {'body':{'bridge_capabilities':self.capabilities}}
        if tool=='ck3_query_army_strengths':
            if args['expected_revision']!=self.frame['revision']:raise RuntimeError('wrong public revision')
            q=copy.deepcopy(self.query);q.update(queried_snapshot_id=self.frame['snapshot_id'],
                queried_revision=self.frame['revision'],queried_native_revision=self.frame['native_revision'])
            return {'body':q}
        if args['expected_revision']!=self.frame['revision']:raise RuntimeError('wrong action revision')
        if tool=='ck3_confirm_ingame_decision_outcome_v1':
            if self.unknown:raise TimeoutError('ack unknown')
            self.query['army_strengths'][0]['current_supply_raw']=30000
        elif tool not in {'ck3_open_ingame_decisions_v1','ck3_select_ingame_decision_item_v1'}:
            raise RuntimeError('unexpected tool '+tool)
        self.frame['revision']+=1;self.frame['native_revision']+=1;self.frame['snapshot_id']='native:'+str(self.frame['native_revision'])
        return {'body':{'accepted':True,'postcondition_verified':False}}

class Contracts(unittest.TestCase):
    def witness(self,f=None,q=None):
        if f is None:f,q=inputs()
        return M.target_witness(f,q,actor_id=42,army_id=18,carmy_id=85,province_id=2644)
    def test_controlled_package_and_drift(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);p=root/'package';M.generate_fixture(p,province_id=2644,machine_id='test-machine')
            manifest=M.validate_fixture(p/'fixture-manifest.json')
            text=(p/'common/decisions/xar_r05_low_supply_fixture.txt').read_text(encoding='utf-8-sig')
            self.assertEqual(text.count('subtract_supply ='),1)
            for forbidden in ['deplete_army','spawn_army','change_soldiers','trigger_event','random =']:
                self.assertNotIn(forbidden,text)
            profile=root/'profile';(profile/'mod').mkdir(parents=True)
            mounted=M.mount_fixture(profile,p/'fixture-manifest.json')
            (profile/'dlc_load.json').write_text(json.dumps({'enabled_mods':[M.OUTER_REF],'disabled_dlcs':[]}))
            self.assertEqual(M.validate_mount(profile,mounted),[M.OUTER_REF])
            target=profile/'mod'/M.MOD_NAME/'common/decisions/xar_r05_low_supply_fixture.txt'
            target.write_bytes(target.read_bytes()+b'\n# changed')
            with self.assertRaises(ValueError):M.validate_mount(profile,mounted)
    def test_fraction_and_injection_rejected(self):
        for fraction in ['1','0','-0.1','0.999999','0.9 } deplete_army_by_percentage = 1']:
            with self.assertRaises(ValueError):M.config(2644,fraction)
        with self.assertRaises(ValueError):M.config(2644,'0.999','unsafe_decision')
    def test_unique_ordinary_target_and_revision_separation(self):
        f,q=inputs();w=self.witness(f,q);self.assertEqual(w['carmy_id'],85)
        cases=[]
        a=copy.deepcopy(f);a['player_armies'].append({**a['player_armies'][0],'army_id':19});cases.append((a,q))
        for field,value in [('retreating',True),('in_combat',True),('army_state','sieging')]:
            a=copy.deepcopy(f);a['player_armies'][0][field]=value;cases.append((a,q))
        a=copy.deepcopy(q);a['queried_revision']=23;cases.append((f,a))
        a=copy.deepcopy(q);a['army_strengths'][0]['gathering_days_left']=1;cases.append((f,a))
        a=copy.deepcopy(q);a['army_strengths'][0]['regiment_replenishment_records_v1'][0]['ready']=False;cases.append((f,a))
        for frame,query in cases:
            with self.assertRaises(ValueError):self.witness(frame,query)
    def test_mixed_physical_classes_are_preserved_not_misnamed(self):
        f,q=inputs();army=q['army_strengths'][0]
        data=copy.deepcopy(army['regiment_replenishment_records_v1'][0]['records'][0])
        data.update(record_index=1,persistent_regiment_id=124)
        army['regiment_replenishment_records_v1'][0]['records'].append(data)
        army['regiment_replenishment_records_v1'][0]['native_data_record_count']=2
        fixed=copy.deepcopy(army['fixed_chunk0_preparation_inputs_v1']['persistent_regiments'][0])
        fixed.update(persistent_regiment_id=124,containing_guard_138_raw=1)
        army['fixed_chunk0_preparation_inputs_v1']['persistent_regiments'].append(fixed)
        witness=self.witness(f,q)
        self.assertTrue(witness['mixed_raw138_classes'])
        self.assertEqual(witness['raw138_by_persistent'],[[123,0],[124,1]])
        self.assertEqual(len(witness['physical_slots']),2)
    def test_physical_identity_not_net_strength(self):
        before=self.witness();after=copy.deepcopy(before);after['current_supply_raw']=30000
        out=M.assess_initialization(before,after)
        self.assertTrue(out['positive_low_stock_can_cross_zero_in_one_same_rate_update'])
        self.assertFalse(out['starvation_casualty_proven'])
        after['physical_slots'][0]['current_soldiers']=99
        with self.assertRaises(ValueError):M.assess_initialization(before,after)
        after=copy.deepcopy(before);after['current_supply_raw']=30000;after['machine_independent_frame']['date_raw']+=24
        with self.assertRaises(ValueError):M.assess_initialization(before,after)
    def run_relay(self,root,*,capabilities=None,unknown=False,prefix='new-root-prefix'):
        package=root/'package'
        if not package.exists():M.generate_fixture(package,province_id=2644,machine_id='test-machine')
        profile=root/'profile'
        if not profile.exists():
            (profile/'mod').mkdir(parents=True);mounted=M.mount_fixture(profile,package/'fixture-manifest.json')
            (profile/'dlc_load.json').write_text(json.dumps({'enabled_mods':[M.OUTER_REF],'disabled_dlcs':[]}))
            (root/'mounted.json').write_text(json.dumps(mounted))
        mounted=json.loads((root/'mounted.json').read_text())
        helper=Relay(root/'run','test-machine',capabilities=capabilities,unknown=unknown)
        binding={'machine_id':'test-machine','run_dir':str(root/'run'),'actor_id':42,'pid':101,
            'create_filetime':444,'episode':'synthetic-episode','generation':3}
        prepared={'machine_id':'test-machine','profile_dir':str(profile),'r05_low_supply_fixture':mounted,'game':{'sha256':M.EXE_SHA}}
        result=R.initialize_once(helper,M,binding=binding,prepared=prepared,package=M.validate_fixture(package/'fixture-manifest.json'),
            army_id=18,carmy_id=85,prefix=prefix,claims_dir=root/'claims',current_machine='test-machine')
        return helper,result
    def test_real_relay_flow_once_then_independent_post(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            helper,result=self.run_relay(Path(t))
            names=[x[0] for x in helper.calls]
            self.assertEqual(names.count('ck3_confirm_ingame_decision_outcome_v1'),1)
            self.assertTrue(result['assessment']['physical_soldiers_unchanged'])
            self.assertFalse(result['assessment']['natural_update_observed'])
            with self.assertRaises(ValueError):self.run_relay(Path(t),prefix='different-prefix-cannot-bypass')
    def test_off_native_gate_precedes_navigation_and_unknown_never_replays(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            with self.assertRaises(ValueError):self.run_relay(Path(t),capabilities=[])
            self.assertFalse((Path(t)/'claims').exists())
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            with self.assertRaises(TimeoutError):self.run_relay(Path(t),unknown=True)
            self.assertEqual(len(list((Path(t)/'claims').glob('*.claim.json'))),1)
            self.assertEqual(len(list((Path(t)/'claims').glob('*.failure.json'))),1)
            with self.assertRaises(ValueError):self.run_relay(Path(t),prefix='replacement-forbidden')
    def common_inputs(self,root,*,parser_status='DETERMINISTIC_SCRIPT_SUBSET_PASSED'):
        # This parser receipt and checkpoint result are synthetic I/O boundaries,
        # never retained as actual parser/game qualifications. Real generator,
        # common materializer and strict mounted-profile checks execute below.
        import ck3_mod_acceptance_prepare as common
        output=root/'prepare';output.mkdir()
        config={}
        for n,relative in enumerate(common.CONFIG_NAMES):
            p=root/'plain'/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# synthetic configuration '+str(n))
            config[relative]=common.pin(p)
        save=root/'normal.ck3';save.write_bytes(b'synthetic-not-a-save')
        receipts=[]
        for name in ('save-receipt.json','source-build.json'):
            p=root/name;p.write_text('{}\n');receipts.append(common.pin(p))
        corpus={n:M.digest(raw) for n,raw in M.render_files(M.config(2644)).items()}
        raw=root/'synthetic-actual-report.json'
        raw.write_text(json.dumps({'schema':'open_kaishek.preflight.v1','status':'GREEN',
            'build_fingerprint':{'version':'1.20.0.4','exe_sha256':M.EXE_SHA},
            'root_scan':{'parser':{'status':'GREEN','files':1,'bytes':len(M.render_files(M.config(2644))['common/decisions/xar_r05_low_supply_fixture.txt']),'diagnostics':0},
                'validator':{'status':'GREEN','diagnostics':0}}}))
        p=root/'synthetic-parser.json'
        p.write_text(json.dumps({'machine_id':'test-machine','status':parser_status,'corpus_sha256':corpus,
            'ck3_exe_sha256':M.EXE_SHA,'open_kaishek_commit':'1'*40,'profile_version':'synthetic-only',
            'actual_command':['synthetic-parser-not-executed'],'unsupported_semantics':['all native effect semantics'],
            'actual_preflight_report':M.pin(raw)}))
        context={'case_inputs':{'normal_checkpoint_receipt':receipts[0],'normal_checkpoint_build_receipt':receipts[1],
            'open_kaishek_preflight':common.pin(p),'plain_configuration':config,'province_id':2644,'army_id':18,'carmy_id':85},
            'output':str(output),'state_dir':str(root/'state'),'shared_source_root':str(DEPENDENCIES),
            'repo_root':str(ROOT),'runtime_manifest':{'synthetic':True},'saved_campaign':{'save':str(save),
                'bytes':save.stat().st_size,'sha256':M.digest(save.read_bytes()),'player_id':42,'date_raw':53149000},
            '_selected_engine':(None,{'game_version':'1.20.0.4','exe_sha256':M.EXE_SHA})}
        reader=SimpleNamespace(game_target=lambda version:{'version':version},
            checkpoint_source=lambda *a:{'actor_id':42,'date_raw':53149000,'save':M.pin(save),'synthetic_boundary_only':True})
        return context,reader
    def test_actual_checkpoint_reader_import_is_library_only(self):
        before=list(sys.path)
        module=A.load('r05_test_actual_checkpoint_reader',DEPENDENCIES/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py')
        self.assertEqual(module.game_target('1.20.0.4')['exe_sha256'],M.EXE_SHA)
        self.assertTrue(callable(module.checkpoint_source))
        self.assertEqual(sys.path,before)
    def test_public_common_adapter_profile_and_actual_load_declaration(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            context,reader=self.common_inputs(Path(t))
            with mock.patch.object(A,'load',return_value=reader),mock.patch('ck3_live_run_id.current_machine_id',return_value='test-machine'):
                result=A.prepare_case(context)
            self.assertEqual(result['startup']['mode'],'saved_campaign')
            profile=Path(result['profile_preparation']['profile'])
            self.assertEqual(M.validate_mount(profile,M.common_mount_receipt(profile)),['mod/product.mod'])
            self.assertTrue(result['research_fixture_mounted'])
            self.assertFalse(result['R05_pass'])
            self.assertFalse(result['profile_preparation']['fixture_mounted']) # generic carrier has no second fixture mod
            self.assertTrue(result['profile_preparation']['preparation'])
            self.assertNotIn('host',result);self.assertNotIn('dll',result)
            (profile/'dlc_load.json').write_text(json.dumps({'enabled_mods':[],'disabled_dlcs':[]}))
            with self.assertRaises(ValueError):M.common_mount_receipt(profile)
    def test_public_common_adapter_missing_parser_gate_blocks_before_profile(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            context,reader=self.common_inputs(Path(t),parser_status='NOT_RUN')
            with mock.patch.object(A,'load',return_value=reader),mock.patch('ck3_live_run_id.current_machine_id',return_value='test-machine'):
                with self.assertRaises(ValueError):A.prepare_case(context)
            self.assertFalse((Path(context['state_dir'])/'profile').exists())
    def test_actual_parser_only_receipt_preserves_validator_red(self):
        # Consume the small frozen actual CLI packets when supplied, never run
        # the parser again and never use its unrelated synthetic IR/runtime.
        if ACTUAL_PREFLIGHT is None:self.skipTest('optional actual parser binding not supplied')
        p=json.loads(ACTUAL_PREFLIGHT.read_bytes())
        package=M.validate_fixture(ACTUAL_PREFLIGHT.parent/'fixture/fixture-manifest.json')
        # Receipt paths are portable relative to their own evidence directory.
        for key in ('actual_preflight_report','actual_validate_report'):
            ref=p[key];p[key]={**ref,'path':str((ACTUAL_PREFLIGHT.parent/ref['path']).resolve())}
        scope=A.script_preflight_scope(p,package,M,'desktop-3fevhd2-1c74096080')
        self.assertIn('validator_RED',scope);self.assertIn('NOT_QUALIFIED',scope)
    def test_real_public_selector_preserves_common_runtime_and_unbound_inputs(self):
        import ck3_mod_acceptance as public
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);paths={}
            for key in ('host','source_index','native_source_index','dll','injector'):
                p=root/(key+'.synthetic');p.write_text('synthetic-source-only\n');paths[key]=str(p)
            paths['source_root']=str(DEPENDENCIES)
            ref=lambda key:{'path_key':key,**{k:v for k,v in M.pin(paths[key]).items() if k!='path'}}
            manifest={'schema':public.MANIFEST_SCHEMA,'source_root':{'path_key':'source_root'},
                'game':{'version':'1.20.0.4','exe_sha256':M.EXE_SHA},'host':ref('host'),
                'source_index':ref('source_index'),'native_source_index':ref('native_source_index'),
                'native':{'dll':ref('dll'),'injector':ref('injector')}}
            mp=root/'manifest.json';mp.write_text(json.dumps(manifest))
            runtime={'schema':public.RUNTIME_SCHEMA,'paths':paths,'manifest':M.pin(mp),
                'python':sys.executable,'repo_root':str(ROOT),'game_dir':str(root/'game'),
                'userdir_root':str(root/'userdir'),'artifacts_root':str(root/'artifacts')}
            rp=root/'runtime.json';rp.write_text(json.dumps(runtime))
            plan=public.Selection(rp,ROOT/'tools/ck3_mod_acceptance_r05_products.json',
                'r05-mechanism-research','initialize-ordinary-low-supply').describe()
            argv=plan['host_argv'];self.assertEqual(argv[4],paths['host'])
            self.assertEqual(argv[argv.index('--agent-source-root')+1],str(DEPENDENCIES))
            self.assertIn('--fixture-profile',argv)
            self.assertTrue(any('Saved campaign input unbound' in b for b in plan['blockers']))
            self.assertTrue(any('Original case budget unbound' in b for b in plan['blockers']))
            self.assertEqual(plan['runtime_status'],'NOT_RUN')
    def test_public_adapter_binds_current_ids_through_existing_common_relay(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);package=root/'package';M.generate_fixture(package,province_id=2644,machine_id='test-machine')
            profile=root/'profile';(profile/'mod').mkdir(parents=True)
            mounted=M.mount_fixture(profile,package/'fixture-manifest.json')
            (profile/'dlc_load.json').write_text(json.dumps({'enabled_mods':[M.OUTER_REF],'disabled_dlcs':[]}))
            prepared=root/'root-prepared.json';prepared.write_text(json.dumps({'machine_id':'test-machine',
                'profile_dir':str(profile),'game':{'sha256':M.EXE_SHA},'r05_low_supply_fixture':mounted}))
            relay=Relay(root/'run','test-machine')
            class Client:
                _process={'pid':101,'create_time':1750000000.125}
                selection=SimpleNamespace(prepared={'preparation':{'root_prepared':M.pin(prepared)}})
                def retain_process(self):pass # synthetic held OS boundary
                def snapshot(self):return relay.snapshot('synthetic-common-snapshot')
                def execute_plan(self,steps,name):
                    self_outer=steps[0]
                    return [{'ok':True,'result':relay.request(self_outer['id'],self_outer['tool'],self_outer['args'])['body']}]
                def checkpoint(self,name,value):
                    (root/(name+'.json')).write_text(json.dumps(value))
            context={'repo_root':str(ROOT),'run_dir':str(root/'run'),'state_dir':str(root/'state'),
                'saved_campaign':{'player_id':42},'case_inputs':{'province_id':2644}}
            with mock.patch('ck3_live_run_id.current_machine_id',return_value='test-machine'):
                result=A.run_case(context,Client())
            self.assertTrue(result['controlled_initializer_qualified'])
            self.assertEqual(result['natural_days_advanced'],0);self.assertFalse(result['R05_pass'])
            self.assertEqual([r[0] for r in relay.calls].count('ck3_confirm_ingame_decision_outcome_v1'),1)
            receipt=json.loads((root/'r05-controlled-initializer-outcome.json').read_bytes())
            self.assertEqual(receipt['army_id'],18);self.assertEqual(receipt['carmy_id'],85)
            self.assertIn('unix_seconds',receipt['process_creation'])

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=ROOT);p.add_argument('--temp-root',type=Path,required=True)
    p.add_argument('--actual-preflight',type=Path,default=ROOT/'docs/ck3-native-ai/acceptance/2026-10-18-r05-controlled-low-supply/script-preflight.actual.json')
    a=p.parse_args();DEPENDENCIES=a.repo_root.resolve();sys.path[:0]=[str(DEPENDENCIES/'ck3_autonomous_player/src'),str(DEPENDENCIES/'tools')]
    M=load('xar_autoplayer.bridge.r05_low_supply_fixture',ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
    R=load('r05_root_once_runner',ROOT/'tools/run_r05_low_supply_initializer_once.py')
    A=load('r05_common_case_adapter',ROOT/'tools/ck3_mod_acceptance_cases/r05_low_supply_adapter.py')
    ACTUAL_PREFLIGHT=a.actual_preflight if a.actual_preflight.is_file() else None
    TEMP=a.temp_root;TEMP.mkdir(parents=True,exist_ok=True)
    unittest.main(argv=[__file__],verbosity=2)
