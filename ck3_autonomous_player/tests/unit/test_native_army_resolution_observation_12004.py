"""Focused normalized-row consumer regressions; no live qualification."""
import copy
import importlib.util
from pathlib import Path
import unittest
MODULE=Path(__file__).resolve().parents[3]/'ck3_autonomous_player/src/xar_autoplayer/bridge/army_split_merge_observation_12004.py'
spec=importlib.util.spec_from_file_location('native_resolution_contract',MODULE)
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
def row():
    return {'status':'available','army_id':99,'native_carmy_id':18,
        'native_army_resolution_v1':{'status':'available','ready':True,'branch':'resolved',
            'raw_reference':18,'reference_index':18,'storage_capacity':2048,'entry_full_id':18}}
class NativeArmyResolutionTests(unittest.TestCase):
    def test_normalized_row_without_legacy_bool_preserves_distinct_id_domains(self):
        actual=row();self.assertNotIn('native_carmy_id_observable',actual)
        result=contract.read_bound_native_army_resolution(actual,army_id=99)
        self.assertEqual(result['army_id'],99);self.assertEqual(result['native_carmy_id'],18)
    def test_legacy_true_cannot_hide_unavailable_or_wrong_generation_or_storage(self):
        for field,value in (('entry_full_id',19),('ready',False),('reference_index',2048)):
            actual=copy.deepcopy(row());actual['native_carmy_id_observable']=True
            actual['native_army_resolution_v1'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                contract.read_bound_native_army_resolution(actual,army_id=99)
