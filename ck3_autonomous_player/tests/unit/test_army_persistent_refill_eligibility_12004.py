"""New eligibility/cached-stage contracts only; no SDK or new game observation."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--repo',type=Path,default=ROOT)
 args,rest=parser.parse_known_args();REPO=args.repo;sys.argv=[sys.argv[0],*rest]
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
import xar_autoplayer.bridge
path=ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/army_persistent_refill_eligibility_12004.py'
spec=importlib.util.spec_from_file_location('xar_autoplayer.bridge.army_persistent_refill_eligibility_12004',path)
candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
PACKET=ROOT/'docs/ck3-native-ai/evidence/episode04-persistent-refill-eligibility-12004/actual-query-projection.json'

def fixture():
 value=json.loads(PACKET.read_text(encoding='utf-8'))
 return value['frame'],value['query']
def first(packet):
 army=packet['army_strengths'][0];record=army['regiment_replenishment_records_v1'][0]['records'][0]
 raw=next(row for row in army['fixed_chunk0_preparation_inputs_v1']['persistent_regiments']
          if row['persistent_regiment_id']==record['persistent_regiment_id'])
 return army,record,raw

class EligibilityTests(unittest.TestCase):
 def run_value(self,frame,packet):return candidate.classify_army_persistent_refill_eligibility_12004(frame,packet,army_id=93)
 def test_existing_actual93_guard1_inputs_are_classified_without_added_refill_credit(self):
  frame,packet=fixture();value=self.run_value(frame,packet)
  self.assertEqual(value['unique_physical_chunk_count'],4)
  self.assertEqual({row['containing_guard_138_raw'] for row in value['physical_chunks']},{1})
  self.assertTrue(all(row['native_can_replenish'] is False for row in value['physical_chunks']))
  self.assertTrue(all(row['conditional_prepared_if_normal_preparation_called_raw']==0 for row in value['physical_chunks']))
  self.assertFalse(value['actual_ADD_observed']);self.assertIsNone(value['actual_physical_refill'])
  self.assertFalse(value['permanent_nonreplenishing_category_proven'])
  self.assertTrue(all(row['player_origin_category'] is None for row in value['physical_chunks']))
 def test_current_permission_false_cannot_cancel_already_prepared_positive_cache(self):
  frame,packet=fixture();army,record,raw=first(packet)
  record['persistent_prepared_replenishment_fraction_raw']=10000
  record['native_chunk_can_replenish']=True
  value=self.run_value(frame,packet)['physical_chunks']
  row=next(row for row in value if row['persistent_regiment_id']==record['persistent_regiment_id'])
  self.assertTrue(row['current_permission_false_does_not_rule_out_stored_core_request'])
  self.assertEqual(row['conditional_prepared_if_normal_preparation_called_raw'],0)
  self.assertFalse(row['actual_ADD_observed'])
 def test_non_GDbo_preparation_bypass_does_not_AND_the_two_native_booleans(self):
  frame,packet=fixture();army,record,raw=first(packet)
  raw.update(containing_guard_138_raw=0,containing_definition_magic_38=0,
             native_fixed_chunk0_can_replenish=False,fresh_fraction_raw=10000)
  record.update(native_can_replenish=True,native_chunk_can_replenish=False,
                persistent_monthly_replenishment_fraction_raw=10000)
  row=next(row for row in self.run_value(frame,packet)['physical_chunks']
           if row['persistent_regiment_id']==record['persistent_regiment_id'])
  self.assertEqual(row['conditional_prepared_if_normal_preparation_called_raw'],10000)
  self.assertTrue(row['native_can_replenish']);self.assertFalse(row['native_chunk_can_replenish'])
  self.assertEqual(row['permission_source_branch'],'non_GDbo_direct_true_after_Army_guards')
 def test_missing_containing_family_retains_observed_bools_and_unknown_cause(self):
  frame,packet=fixture();del packet['army_strengths'][0]['fixed_chunk0_preparation_inputs_v1']
  value=self.run_value(frame,packet)
  self.assertFalse(value['containing_inputs_available'])
  self.assertTrue(all(row['conditional_prepared_if_normal_preparation_called_raw'] is None for row in value['physical_chunks']))
  self.assertTrue(all(row['player_origin_category'] is None for row in value['physical_chunks']))
 def test_empty_Character_1_1_is_separate_from_physical_eligibility(self):
  frame,packet=fixture();army=packet['army_strengths'][0];identity=123456
  army['regiment_strengths'].append({'army_regiment_id':identity,'current_soldiers':1,'maximum_soldiers':1,'scale':1})
  army['regiment_count']+=1;army['current_soldiers']+=1;army['maximum_soldiers']+=1
  army['regiment_replenishment_records_v1'].append({'army_regiment_id':identity,'source':'native_all_data_records',
   'status':'available','ready':True,'native_data_record_count':0,'unavailable_reason':None,'records':[],
   'native_loss_writer_skipped':True,'loss_writer_admission_unavailable_reason':None,
   'native_character_role_v1':{'source':'native_selected_ArRg_character_role_raw','status':'available',
    'army_regiment_id':identity,'native_carmy_id':85,'arrg_army_id_140':85,'character_raw_id_148':70,
    'resolved_character_id':70,'character_magic_1c':0x43686172,'resolution_used_fallback':False,
    'native_character_predicate':True,'character_extension_present':True,'extension_army_id_f4':-1,
    'extension_arrg_id_f8':identity,'same_ArRg_instance_after':True,'unavailable_reason':None}})
  value=self.run_value(frame,packet)
  self.assertEqual(value['unique_physical_chunk_count'],4)
  self.assertEqual(value['empty_ArRg_rows'][0]['kind'],'empty_Character_role_record')
  self.assertIsNone(value['empty_ArRg_rows'][0]['persistent_refill_eligibility'])
 def test_aliases_deduplicate_physical_chunks_but_keep_DATA_occurrences(self):
  frame,packet=fixture();army,record,raw=first(packet)
  ar=army['regiment_replenishment_records_v1'][0];alias=copy.deepcopy(record);alias['record_index']=len(ar['records'])
  ar['records'].append(alias);ar['native_data_record_count']+=1
  value=self.run_value(frame,packet)
  self.assertEqual(value['unique_physical_chunk_count'],4);self.assertEqual(len(value['DATA_occurrences']),5)
 def test_stale_partial_duplicate_and_conflicting_guard_are_rejected(self):
  for change in ('frame','partial','duplicate','guard'):
   frame,packet=fixture();army,record,raw=first(packet)
   if change=='frame':packet['queried_connection_generation']+=1
   if change=='partial':army['regiment_replenishment_records_v1'][0]['status']='partial';army['regiment_replenishment_records_v1'][0]['ready']=False
   if change=='duplicate':army['fixed_chunk0_preparation_inputs_v1']['persistent_regiments'].append(copy.deepcopy(raw))
   if change=='guard':record['native_can_replenish']=True
   with self.subTest(change=change),self.assertRaises(ValueError):self.run_value(frame,packet)

if __name__=='__main__':unittest.main()
