from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).with_name('ck3_mod_acceptance_prepare.py')
spec=importlib.util.spec_from_file_location('vanilla_saved_profile_prepare_test',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class VanillaSavedProfileTests(unittest.TestCase):
    def inputs(self,root):
        rows={}
        for index,name in enumerate(module.CONFIG_NAMES):
            path=root/'inputs'/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(('plain original config '+str(index)).encode())
            rows[name]=module.pin(path)
        return {'state_dir':root/'state','output':root/'output'},rows

    def test_explicit_none_builds_empty_mod_inventory_without_placeholder_mod(self):
        with tempfile.TemporaryDirectory() as directory:
            context,configs=self.inputs(Path(directory))
            profile=module.materialize_product_profile(context,None,configs)
            path=Path(profile['profile'])
            inventory=json.loads(Path(profile['product_inventory']['path']).read_text())
            self.assertEqual(inventory,{'schema':'ck3-saved-campaign-vanilla-profile-v1',
                'profile_path':str(path.resolve()),'enabled_mods':[],'product_files':[]})
            self.assertEqual(json.loads((path/'dlc_load.json').read_text())['enabled_mods'],[])
            self.assertEqual(set(profile['files']),{*module.CONFIG_NAMES,'dlc_load.json'})
            self.assertFalse((path/'mod').exists())
            self.assertFalse((path/'mod-content').exists())
            self.assertFalse(profile['fixture_mounted'])
            self.assertTrue(profile['vanilla_profile'])
            for name,row in configs.items():self.assertEqual(module.pin(path/name)['sha256'],row['sha256'])

    def test_existing_product_profile_keeps_nonempty_exact_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);context,configs=self.inputs(root)
            product=root/'product';product.mkdir()
            (product/'descriptor.mod').write_text('name="Existing product"\nsupported_version="1.20.*"\n')
            (product/'example.txt').write_text('source unchanged')
            profile=module.materialize_product_profile(context,product,configs)
            inventory=json.loads(Path(profile['product_inventory']['path']).read_text())
            self.assertEqual(inventory['schema'],'ck3-saved-campaign-product-only-profile-v1')
            self.assertEqual(inventory['enabled_mods'],['mod/product.mod'])
            self.assertEqual(len(inventory['product_files']),3)
            self.assertNotIn('vanilla_profile',profile)

    def test_vanilla_cannot_smuggle_workshop_cache_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            context,configs=self.inputs(Path(directory))
            with self.assertRaisesRegex(ValueError,'vanilla saved campaign'):
                module.materialize_product_profile(context,None,configs,workshop_cache_files=[])

    def test_common_finish_records_vanilla_preparation_without_fixture_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            context,configs=self.inputs(Path(directory))
            profile=module.materialize_product_profile(context,None,configs)
            context['_selected_engine']=(None,{'game_version':'1.20.0.4','exe_sha256':'a'*64})
            finished=module.finish_product_profile(context,profile,provenance={'kind':'explicit-vanilla-coldload'})
            receipt=json.loads(Path(finished['preparation']['path']).read_text())
            self.assertEqual(receipt['provenance'],{'kind':'explicit-vanilla-coldload'})
            self.assertFalse(receipt['fixture_mounted'])
            self.assertFalse((Path(context['output'])/'frontend-fixture-start-policy.json').exists())


if __name__=='__main__':unittest.main()
