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
        self.profile=prepare.materialize_product_profile(self.context,self.product,configs)
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


if __name__=='__main__':unittest.main()
