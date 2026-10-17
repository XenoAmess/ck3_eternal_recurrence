import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('mechanism_prepare',Path(__file__).with_name('ck3_mod_acceptance_prepare.py'))
prepare=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class MechanismProfilePreparationTests(unittest.TestCase):
    def inputs(self,root,scenario=True):
        fixture=root/'fixture';fixture.mkdir();(fixture/'descriptor.mod').write_text('name="fixture"\nsupported_version="1.20.*"\n',encoding='utf-8')
        (fixture/'events').mkdir();(fixture/'events/fixture.txt').write_text('namespace = fixture\n',encoding='utf-8-sig')
        configuration={}
        for index,name in enumerate(prepare.CONFIG_NAMES):
            path=root/f'config-{index}.txt';path.write_text(f'fixture-{index}\n',encoding='utf-8');configuration[name]=prepare.pin(path)
        output=root/'output';output.mkdir()
        contract={'post_start':{'government_key':'clan_government','primary_title_tier_key':'empire','independent':True},'required_startup':['fixture marker'],'forbidden_startup':[]}
        if scenario:
            contract['frontend_scenario']={'profile_id':'faith-and-power-e01-abbasid-867','frontend_target':{'bookmark_key':'bm_xar_faith_h01_867','character_name_key':'bookmark_xar_faith_h01_abbasid','government_key':'clan_government','start_date_raw':51394920,'bookmark_group_key':'bm_group_867'},'startup_event_admission':{'mode':'observe_only','event_definition_key':'xar_faith_h01_prepare.1','option_count':2}}
        return fixture,configuration,{'state_dir':str(root/'state'),'output':str(output),'case_contract':contract}

    def test_explicit_mechanism_profile_mounts_only_fixture_and_binds_v2_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fixture,configuration,context=self.inputs(root)
            with patch.object(prepare,'_engine',return_value=(None,{'game_version':'test-only','exe_sha256':'a'*64})):
                result=prepare.materialize_fixture_profile(context,fixture,None,configuration)
            profile=Path(result['profile']);load=json.loads((profile/'dlc_load.json').read_text())
            self.assertEqual(load,{'enabled_mods':['mod/fixture.mod'],'disabled_dlcs':[]})
            self.assertFalse((profile/'mod/product.mod').exists())
            policy=json.loads(Path(result['fixture_start_policy']['path']).read_text())
            self.assertEqual(policy['schema'],'ck3-frontend-fixture-start-policy-v2')
            self.assertEqual(policy['schema_version'],2)
            for key,value in context['case_contract']['frontend_scenario'].items():self.assertEqual(policy[key],value)
            receipt=json.loads(Path(result['preparation']['path']).read_text())
            self.assertEqual(receipt['files'],result['files'])
            self.assertEqual(receipt['provenance']['kind'],'standalone-mechanism-fixture')
            self.assertIsNone(receipt['provenance']['product'])

    def test_existing_dual_mod_preparation_keeps_mount_order_and_v1(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fixture,configuration,context=self.inputs(root,scenario=False)
            product=root/'product';product.mkdir();(product/'descriptor.mod').write_text('name="product"\n',encoding='utf-8')
            with patch.object(prepare,'_engine',return_value=(None,{'game_version':'test-only','exe_sha256':'a'*64})):
                result=prepare.materialize_fixture_profile(context,fixture,product,configuration)
            load=json.loads((Path(result['profile'])/'dlc_load.json').read_text())
            self.assertEqual(load['enabled_mods'],['mod/product.mod','mod/fixture.mod'])
            policy=json.loads(Path(result['fixture_start_policy']['path']).read_text())
            self.assertEqual(policy['schema'],'ck3-frontend-fixture-start-policy-v1')
            self.assertEqual(policy['schema_version'],1)
            self.assertNotIn('frontend_target',policy)

    def test_incomplete_scenario_declaration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture,configuration,context=self.inputs(Path(temporary))
            del context['case_contract']['frontend_scenario']['startup_event_admission']
            with patch.object(prepare,'_engine',return_value=(None,{'game_version':'test-only','exe_sha256':'a'*64})):
                with self.assertRaisesRegex(ValueError,'exact declared target and startup event admission'):
                    prepare.materialize_fixture_profile(context,fixture,None,configuration)


if __name__=='__main__':unittest.main()
