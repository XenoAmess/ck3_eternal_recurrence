"""Synthetic current-role consumers; no native packet or game qualification."""
from pathlib import Path
import copy,importlib.util,unittest,sys,types,json,os

ROOT=Path(__file__).resolve().parents[3]
path=ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/army_regiment_character_role_12004.py'
spec=importlib.util.spec_from_file_location('character_role',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def inputs():
 strength={'army_regiment_id':900,'current_soldiers':1,'maximum_soldiers':1,'scale':1}
 data={'army_regiment_id':900,'native_data_record_count':0,'records':[],
       'native_loss_writer_skipped':True}
 link={'source':'native_selected_ArRg_character_role_raw','status':'available',
       'army_regiment_id':900,'native_carmy_id':88,'arrg_army_id_140':88,
       'character_raw_id_148':300,'resolved_character_id':300,'character_magic_1c':0x43686172,
       'resolution_used_fallback':False,'native_character_predicate':True,
       'character_extension_present':True,'extension_army_id_f4':-1,'extension_arrg_id_f8':900,
       'same_ArRg_instance_after':True,'unavailable_reason':None}
 return strength,data,link

def classify(values,current=None,knights=None):
 return module.classify_current_regiment_character_role_12004(*values,native_carmy_id=88,
   current_commander=current or {'status':'available','character_id':400},knights=knights)

class CurrentRoleTests(unittest.TestCase):
 def test_literal_leaf_strict_schema_and_full_data_pipeline(self):
  package=types.ModuleType('role_fixture_bridge');package.__path__=[str(path.parent)]
  sys.modules[package.__name__]=package
  from importlib import import_module
  contract=import_module('role_fixture_bridge.army_replenishment_records_contract')
  values=inputs();link=values[2]
  row={**values[1],'source':'native_all_data_records','status':'available','ready':True,
       'loss_writer_admission_unavailable_reason':None,'unavailable_reason':None,
       'native_character_role_v1':link}
  normalized=contract.normalize_regiment_replenishment_records_v1([row])[0]
  self.assertEqual(normalized['native_character_role_v1'],link)
  legacy=copy.deepcopy(row);del legacy['native_character_role_v1']
  self.assertNotIn('native_character_role_v1',contract.normalize_regiment_replenishment_records_v1([legacy])[0])
  for field,value in [('native_carmy_id',True),('character_magic_1c',-1),
                      ('army_regiment_id',901),('unavailable_reason','wrong'),
                      ('native_character_predicate',False),('same_ArRg_instance_after',False)]:
   broken=copy.deepcopy(row);broken['native_character_role_v1'][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):
    contract.normalize_regiment_replenishment_records_v1([broken])
  broken=copy.deepcopy(row);broken['native_character_role_v1']['extra']=1
  with self.assertRaises(ValueError):contract.normalize_regiment_replenishment_records_v1([broken])

 @unittest.skipUnless(os.environ.get('XAR_CHARACTER_ROLE_NATIVE_FIXTURE_JSON'),'native fixture output not supplied')
 def test_compiled_native_all_data_literal_serializer_roundtrip(self):
  package=types.ModuleType('role_fixture_bridge');package.__path__=[str(path.parent)]
  sys.modules[package.__name__]=package
  from importlib import import_module
  contract=import_module('role_fixture_bridge.army_replenishment_records_contract')
  rows=json.loads(Path(os.environ['XAR_CHARACTER_ROLE_NATIVE_FIXTURE_JSON']).read_text(encoding='utf-8'))
  normalized=contract.normalize_regiment_replenishment_records_v1(rows)
  self.assertEqual(normalized[0]['native_character_role_v1']['resolved_character_id'],300)
  self.assertEqual(normalized[0]['native_character_role_v1']['extension_army_id_f4'],-1)
  self.assertEqual(normalized[0]['native_data_record_count'],0)
  self.assertNotIn('native_character_role_v1',normalized[1])

 def test_old_commander_character_record_is_not_called_current_commander_or_knight(self):
  result=classify(inputs())
  self.assertEqual(result['linked_character_id'],300)
  self.assertFalse(result['is_current_commander'])
  self.assertTrue(result['observed_ArRg_backlink_matches'])
  self.assertIsNone(result['native_knight_member'])
  self.assertIsNone(result['physical_refill_applied'])
  self.assertFalse(result['birth_producer_observed'])

 def test_commander_and_knight_are_independent_roles_for_the_same_character(self):
  values=inputs();values[2]['extension_army_id_f4']=88
  result=classify(values,current={'status':'available','character_id':300},
    knights={'available':True,'members':[{'source_regiment_id':900,'army_id':88,
      'character_id':300,'eligible':True,'participant_army_membership_verified':True}]})
  self.assertTrue(result['is_current_commander'])
  self.assertTrue(result['native_knight_member'])
  no_knight=classify(values,current={'status':'available','character_id':300},
    knights={'available':True,'members':[]})
  self.assertTrue(no_knight['is_current_commander'])
  self.assertFalse(no_knight['native_knight_member'])

 def test_unknown_predicate_and_commander_do_not_become_false_or_a_knight_label(self):
  values=inputs();values[1]['native_loss_writer_skipped']=None
  values[2].update(status='partial',native_character_predicate=None,resolved_character_id=None,
                   same_ArRg_instance_after=False)
  result=classify(values,current={'status':'unavailable','character_id':None})
  self.assertIsNone(result['native_character_predicate'])
  self.assertIsNone(result['linked_character_id'])
  self.assertIsNone(result['is_current_commander'])
  self.assertIsNone(result['native_knight_member'])

 def test_unrelated_full_generation_and_native_knight_membership_are_rejected(self):
  for change in ('different_arrg','different_army','predicate_disagreement','stale_instance'):
   values=inputs()
   if change=='different_arrg':values[2]['army_regiment_id']=901
   if change=='different_army':values[2]['native_carmy_id']=89
   if change=='predicate_disagreement':values[1]['native_loss_writer_skipped']=False
   if change=='stale_instance':values[2]['same_ArRg_instance_after']=False
   with self.subTest(change=change),self.assertRaises(ValueError):classify(values)
  bad={'available':True,'members':[{'source_regiment_id':900,'army_id':89,
      'character_id':300,'eligible':True,'participant_army_membership_verified':True}]}
  with self.assertRaises(ValueError):classify(inputs(),knights=bad)

 def test_known_no_commander_is_distinct_from_a_failed_query(self):
  absent=classify(inputs(),current={'status':'absent','character_id':None})
  failed=classify(inputs(),current={'status':'unavailable','character_id':None})
  self.assertFalse(absent['is_current_commander'])
  self.assertTrue(absent['current_commander_role_observable'])
  self.assertIsNone(failed['is_current_commander'])
  self.assertFalse(failed['current_commander_role_observable'])

if __name__=='__main__':unittest.main()
