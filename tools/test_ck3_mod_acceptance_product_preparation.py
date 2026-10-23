"""Product preparation must be consumable by the real normal-exit inventory path."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'ck3_autonomous_player/src')]
import ck3_mod_acceptance_prepare as prepare
import ck3_mod_acceptance_normal_exit_profile as normal
import build_normal_exit_source_inventory_v1 as builder
from ck3_mod_acceptance_cases import generic_product_adapter as generic


class ProductPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.state=self.root/'state';self.game=self.root/'game'
        self.output=self.root/'prepared';self.output.mkdir()
        self.executable=self.put(self.game/'binaries/ck3.exe',b'offline synthetic engine')
        for relative in builder.STOCK_GUI_PATHS:
            self.put(self.game/'game'/relative,('# offline stock '+relative).encode())
        source=self.root/'shared-source/tools/fixture_engine_prepare.py'
        self.put(source,b"import hashlib\nfrom pathlib import Path\ndef engine_identity(repo,*,game_dir,steam_manifest=None):\n return {'game_version':'offline-product-build','exe_sha256':hashlib.sha256((Path(game_dir)/'binaries/ck3.exe').read_bytes()).hexdigest()}\n")
        self.product=self.root/'product'
        self.put(self.product/'descriptor.mod',b'name="offline product"\n')
        self.put(self.product/'common/scripted_effects/product.txt',b'product_effect = {}\n')
        configs={name:self.put(self.root/'plain'/name,b'offline config\n') for name in prepare.CONFIG_NAMES}
        self.context={'state_dir':str(self.state),'output':str(self.output),
            'shared_source_root':str(source.parents[1]),'game_dir':str(self.game),'case_inputs':{},
            'shared_game':{'version':'offline-product-build','exe_sha256':self.executable['sha256']}}
        from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2
        self.profile=materialize_saved_profile_v2(self.context,self.product,configs,source_role='formal_product')
        self.args=SimpleNamespace(state_dir=self.state,game_dir=self.game,
            bridge_dll=self.root/'native.dll',bridge_injector=self.root/'injector.exe',
            output=self.root/'run/native-report.json')
        self.runtime={'game_dir':str(self.game),'paths':{'dll':str(self.args.bridge_dll),
                                                     'injector':str(self.args.bridge_injector)}}
        self.manifest={'game':copy.deepcopy(self.context['shared_game']),
            'native':{'dll':{'path_key':'dll','sha256':'1'*64},
                      'injector':{'path_key':'injector','sha256':'2'*64}}}

    def put(self,path,raw):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        return prepare.pin(path)

    def finish(self):
        return prepare.finish_product_profile(self.context,self.profile,provenance={'kind':'saved-product'})

    def project(self):
        return normal.project_profile(self.args,self.runtime,self.manifest,{'sha256':'3'*64},
                                      self.state/'normal-exit-binding')

    def test_materialize_finish_actual_normal_exit_inventory_chain(self):
        result=self.finish()
        receipt=json.loads(Path(result['preparation']['path']).read_bytes())
        self.assertEqual(receipt['schema'],'ck3-mod-acceptance-prepared-product-v1')
        self.assertEqual(receipt['exe_sha256'],self.executable['sha256'])
        self.assertFalse(receipt['fixture_mounted'])
        self.assertNotIn('fixture_start_policy',result)
        self.assertFalse((self.output/'frontend-fixture-start-policy.json').exists())
        profile=normal.create_profile(self.args,self.runtime,self.manifest,{'sha256':'3'*64},
                                     self.state/'normal-exit-binding',builder)
        self.assertTrue(Path(profile['path']).is_file())
        verified=json.loads((self.state/'normal-exit-binding/RESULT.actual.json').read_bytes())
        self.assertTrue(verified['verification']['static_sources_verified'])
        self.assertEqual(verified['verification']['enabled_mod_count'],1)
        self.assertFalse(verified['game_started'])

    def test_selected_engine_mismatch_rejected_before_startup_evidence(self):
        self.context['shared_game']['exe_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'game differs'):self.finish()
        self.assertFalse((self.state/'preparation.json').exists())

    def test_profile_changed_before_finish_is_not_reinventoried_as_original(self):
        (self.state/'profile/pdx_settings.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'files changed'):self.finish()

    def test_inventory_changed_before_finish_rejected(self):
        Path(self.profile['product_inventory']['path']).write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'inventory changed'):self.finish()

    def test_finished_preparation_still_requires_matching_runtime_engine(self):
        self.finish();self.manifest['game']['version']='different-engine'
        with self.assertRaisesRegex(ValueError,'identities differ'):self.project()

    def test_changed_prepared_file_rejected_by_normal_exit_projection(self):
        self.finish();(self.state/'profile/pdx_settings.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'file bytes changed'):self.project()

    def test_startup_file_hash_bindings_must_match_preparation(self):
        self.finish();path=self.state/'preparation.json';value=json.loads(path.read_bytes())
        value['profile_input_sha256']['pdx_settings.txt']='0'*64
        path.write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'file bindings differ'):self.project()

    def test_private_product_schema_is_not_accepted_as_standard_evidence(self):
        result=self.finish();path=Path(result['preparation']['path']);value=json.loads(path.read_bytes())
        value['schema']='private-product-preparation-v1';path.write_text(json.dumps(value),encoding='utf-8')
        startup=self.state/'preparation.json';value=json.loads(startup.read_bytes())
        value['preparation']=prepare.pin(path);startup.write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'identities differ'):self.project()


class OrdinaryPromotionTests(ProductPreparationTests):
    def ordinary_context(self):
        context=copy.deepcopy(self.context)
        context.update(state_dir=str(self.root/'ordinary/state'), run_dir=str(self.root/'run'),
            output=str(self.root/'ordinary/prepared'),
            product='living-artifacts', case='ordinary-promotion', run_id='ordinary-R1',
            case_contract=json.loads((ROOT/'tools/ck3_mod_acceptance_cases/living_artifacts_ordinary_promotion.json').read_bytes()))
        Path(context['output']).mkdir(parents=True, exist_ok=True)
        context['case_inputs']={'product_dir':str(self.product),
            'formal_product_files':{p.relative_to(self.product).as_posix():prepare.pin(p)
                for p in self.product.rglob('*') if p.is_file()},
            'plain_configuration':{name:prepare.pin(self.root/'plain'/name) for name in prepare.CONFIG_NAMES}}
        return context

    def test_ordinary_actual_prepare_to_normal_exit_inventory_without_carrier(self):
        context=self.ordinary_context()
        result=generic.prepare_case(context)
        self.assertEqual(result['startup'],{'mode':'ordinary_gui_campaign','state_dir':context['state_dir']})
        self.assertEqual(json.loads(Path(result['initial_plan']['path']).read_bytes()),{'steps':[]})
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['profile']['fixture_mounted'])
        self.assertFalse((Path(context['state_dir'])/'profile/mod-content/fixture').exists())
        self.assertFalse((self.output/'empty-load-carrier').exists())
        self.args.state_dir=Path(context['state_dir'])
        profile=normal.create_profile(self.args,self.runtime,self.manifest,{'sha256':'3'*64},
            self.args.state_dir/'normal-exit-binding',builder)
        self.assertTrue(Path(profile['path']).is_file())

    def test_ordinary_unknown_or_effect_inputs_rejected_before_profile(self):
        for key in ('fixture_dir','saved_campaign','frontend_rules'):
            context=self.ordinary_context();context['case_inputs'][key]={}
            with self.assertRaisesRegex(ValueError,'only formal'):generic.prepare_case(context)
            self.assertFalse(Path(context['state_dir']).exists())

    def test_ordinary_manifest_rejects_wrong_missing_bool_and_changed_bytes(self):
        for mutation in ('missing','bool','digest','extra'):
            context=self.ordinary_context();files=context['case_inputs']['formal_product_files']
            if mutation=='missing':files.pop('descriptor.mod')
            elif mutation=='bool':files['descriptor.mod']['bytes']=True
            elif mutation=='digest':files['descriptor.mod']['sha256']='0'*64
            else:files['unshipped.txt']=copy.deepcopy(files['descriptor.mod'])
            with self.assertRaises(ValueError):generic.prepare_case(context)
            self.assertFalse(Path(context['state_dir']).exists())

    def capture_evidence(self):
        context=self.ordinary_context();root=self.root/'captures';take=root/'take01'
        raw=self.put(take/'raw-gameplay.mkv',b'actual synthetic media boundary')
        final=self.put(take/'recorder-final.json',(json.dumps({
            'schema':'ck3-mod-acceptance-recorder-final-v2','machine_id':'offline-machine',
            'result':'ENCODED_UNREVIEWED','budget_qualified':True,'probe_exit_code':0,
            'job':{'state':'NORMAL_TREE_EMPTY','job_active_processes':0},'raw':raw})+'\n').encode())
        config=self.put(self.root/'recording-config.json',(json.dumps({
            'schema':'ck3-mod-acceptance-recording-config-v2','machine_id':'offline-machine',
            'capture_root':str(root)})+'\n').encode())
        self.put(Path(context['run_dir'])/'frozen-argv.json',(json.dumps({
            'run_id':context['run_id'],'files':{config['path']:{k:config[k] for k in ('bytes','sha256')}}})+'\n').encode())
        response={'status':'complete','run_id':context['run_id'],'reviewer':'/root',
            'recorder_config':config,'captures':[final],'evidence':[raw],
            'assertions':{key:True for key in generic.ORDINARY_REVIEW_ASSERTIONS}}
        return context,response

    def test_ordinary_verifies_actual_allocated_recorder_pin_and_raw_roundtrip(self):
        context,response=self.capture_evidence()
        result=generic.validate_ordinary_capture_evidence(context,json.loads(json.dumps(response)))
        self.assertEqual(result['captures'],response['captures'])
        self.assertFalse(result['human_review_performed'])
        Path(response['evidence'][0]['path']).write_bytes(b'tampered media')
        with self.assertRaisesRegex(ValueError,'bytes changed'):
            generic.validate_ordinary_capture_evidence(context,response)

    def test_ordinary_ack_missing_capture_and_unallocated_config_rejected(self):
        context,response=self.capture_evidence()
        for key in ('captures','recorder_config','evidence','assertions'):
            bad=copy.deepcopy(response);bad.pop(key)
            with self.assertRaises(ValueError):generic.validate_ordinary_capture_evidence(context,bad)
        frozen=Path(context['run_dir'])/'frozen-argv.json'
        frozen.write_bytes(json.dumps({'run_id':context['run_id'],'files':{}}).encode())
        with self.assertRaises(ValueError):generic.validate_ordinary_capture_evidence(context,response)

    def test_ordinary_recorder_bool_exit_does_not_pass_as_zero(self):
        context,response=self.capture_evidence();path=Path(response['captures'][0]['path'])
        value=json.loads(path.read_bytes());value['job']['job_active_processes']=False
        path.write_bytes(json.dumps(value).encode());response['captures']=[prepare.pin(path)]
        with self.assertRaisesRegex(ValueError,'terminal'):
            generic.validate_ordinary_capture_evidence(context,response)


if __name__=='__main__':unittest.main()
