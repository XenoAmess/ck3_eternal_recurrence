"""Offline relay contracts only; synthetic rows never award runtime qualification."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,importlib.util,json,sys,tempfile,unittest

ap=argparse.ArgumentParser(add_help=False);ap.add_argument('--repo',type=Path,required=True)
opts,rest=ap.parse_known_args();sys.argv=[sys.argv[0],*rest]
sys.path.insert(0,str(opts.repo.resolve()/'ck3_autonomous_player/src'))
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
HERE=Path(__file__).parent
relay=module(HERE/'root_relay.py','r09_relay_test')
consumer=module(HERE/'army_split_transfer_assertions_12004.py','r09_consumer_test')

def context_proof():
 run=relay.MACHINE+'--vanilla--R0176'
 context={'machine_id':relay.MACHINE,'source_head':relay.SOURCE,
  'identity':{'machine_id':relay.MACHINE,'source_head':relay.SOURCE,'run_id':run,'sequence':176,'mod_key':'vanilla'}}
 proof={'machine_id':relay.MACHINE,'source_head':relay.SOURCE,'run_id':run,
  'pid':222,'process_creation_filetime_100ns':333,'connection_generation':4,
  'actual_runtime_character_full_id':7,'episode_run_id':'synthetic-only',
  'stable_character_intent':{'historical_id':1128,'bookmark_character_name_key':'bookmark_rags_to_riches_duke_robert'}}
 return context,proof,run
def frame():
 return {'snapshot_id':'synthetic','revision':10,'native_revision':100,'date_raw':999,
  'player_armies':[{'army_id':500,'source':'native','controllable':True,'owner_character_id':7,
                   'in_combat':False,'retreating':False,'current_province_id':100}]}
def caps():
 return {'backend_id':'native-headless','fallback_enabled':False,
  'bridge_capabilities':list(relay.READ_CAPS|{relay.ACTION_CAP['split']}),'action_steps':['split-army-half-500']}
def army(role=False):
 identity=2000 if role else 1000
 strength={'army_regiment_id':identity,'current_soldiers':1 if role else 50,'maximum_soldiers':1 if role else 60,'scale':1}
 record={'record_index':0,'persistent_regiment_id':1000,'chunk_index':0,'status':'available','unavailable_reason':None,
  'current_soldiers':50,'maximum_soldiers':60,'effective_current_soldiers':50,'state_raw':0,'chunk_army_regiment_id':1000,
  'native_can_replenish':False,'native_chunk_can_replenish':False,'persistent_monthly_replenishment_fraction_raw':0,
  'persistent_prepared_replenishment_fraction_raw':0,'persistent_monthly_replenishment_fraction_scale':100000,
  'persistent_prepared_replenishment_fraction_scale':100000}
 data={'army_regiment_id':identity,'source':'native_all_data_records','status':'available','ready':True,
  'native_data_record_count':0 if role else 1,'unavailable_reason':None,'native_loss_writer_skipped':role,
  'loss_writer_admission_unavailable_reason':None,'records':[] if role else [record]}
 if role:
  data['native_character_role_v1']={'source':'native_selected_ArRg_character_role_raw','status':'available',
   'army_regiment_id':identity,'native_carmy_id':8000,'arrg_army_id_140':8000,'character_raw_id_148':70,
   'resolved_character_id':70,'character_magic_1c':0x43686172,'resolution_used_fallback':False,
   'native_character_predicate':True,'character_extension_present':True,'extension_army_id_f4':-1,
   'extension_arrg_id_f8':identity,'same_ArRg_instance_after':True,'unavailable_reason':None}
 return {'army_id':500,'native_carmy_id':8000,'regiment_strengths':[strength],
         'regiment_replenishment_records_v1':[data]}

class RelayContracts(unittest.TestCase):
 def test_new_runtime_admission_and_old_or_foreign_rejection(self):
  context,proof,run=context_proof()
  self.assertEqual(relay.admission(context,proof,run_id=run)['pid'],222)
  for field,value in [('run_id',relay.MACHINE+'--vanilla--R0175'),('machine_id','another-machine'),
                      ('connection_generation',0),('process_creation_filetime_100ns',None)]:
   wrong=copy.deepcopy(proof);wrong[field]=value
   with self.subTest(field=field),self.assertRaises(RuntimeError):relay.admission(context,wrong,run_id=run)
 def test_missing_capability_concrete_step_and_owner_rejected(self):
  relay.action_gate(frame(),caps(),'split-army-half-500','split',[500],7)
  for change in ('capability','step','owner','combat'):
   s,c=frame(),caps()
   if change=='capability':c['bridge_capabilities']=[]
   if change=='step':c['action_steps']=[]
   if change=='owner':s['player_armies'][0]['owner_character_id']=8
   if change=='combat':s['player_armies'][0]['in_combat']=True
   with self.subTest(change=change),self.assertRaises(RuntimeError):relay.action_gate(s,c,'split-army-half-500','split',[500],7)
 def mock_live(self,root,outcome):
  live=relay.Relay.__new__(relay.Relay);live.case=root/'case';live.case.mkdir()
  live.run=root/'run';live.a=SimpleNamespace(attempt='testonly',army_id=500)
  live.meta={'machine_id':'synthetic-test-only','binding':{'actor':7}}
  live.binding={'actor':7};live.serial=0;live.calls=[]
  live.saved=lambda name:{'source_army_id':500,'packet':{'frame':frame()}}
  live.snapshot=lambda name:(frame(),{})
  def request(name,tool,arguments):
   live.serial+=1;live.calls.append(tool)
   if tool=='ck3_get_capabilities':return {'body':caps()},{}
   self.assertTrue((live.case/'split.once.claim.json').is_file())
   if outcome=='timeout':raise TimeoutError('synthetic original pending')
   return {'body':{'accepted':False,'step':'split-army-half-500','error':'CK3 rejected split-army-half validation'}},{}
  live.request=request;return live
 def test_unknown_submission_claim_precedes_request_and_survives(self):
  with tempfile.TemporaryDirectory() as directory:
   live=self.mock_live(Path(directory),'timeout')
   with self.assertRaises(TimeoutError):live.submit_once('split')
   with self.assertRaises(FileExistsError):live.submit_once('split')
   self.assertEqual(live.calls.count('ck3_execute_step'),1)
   claim=relay.load(live.case/'split.once.claim.json')
   self.assertTrue(claim['no_replay_even_if_rejected_or_timeout'])
   self.assertIsNone(claim['gate']['native_validator_result_before_submission'])
 def test_native_validator_false_is_retained_without_replay(self):
  with tempfile.TemporaryDirectory() as directory:
   live=self.mock_live(Path(directory),'rejected')
   with self.assertRaises(RuntimeError):live.submit_once('split')
   value=relay.load(live.case/'split.submission.actual.json')
   self.assertFalse(value['actual_native_validator_and_queue_accepted'])
   self.assertEqual(value['body']['error'],'CK3 rejected split-army-half validation')
   with self.assertRaises(FileExistsError):live.submit_once('split')
   self.assertEqual(live.calls.count('ck3_execute_step'),1)
 def test_same_paused_frame_drift_refuses_action(self):
  with tempfile.TemporaryDirectory() as directory:
   live=self.mock_live(Path(directory),'timeout');changed=frame();changed['revision']+=1
   live.snapshot=lambda name:(changed,{})
   with self.assertRaises(RuntimeError):live.submit_once('split')
   self.assertEqual(live.calls,[])
   self.assertFalse((live.case/'split.once.claim.json').exists())
 def test_merge_DATA_preserved_with_separate_empty_Character_record(self):
  base=army();after=copy.deepcopy(base);character=army(role=True)
  after['regiment_strengths']+=character['regiment_strengths']
  after['regiment_replenishment_records_v1']+=character['regiment_replenishment_records_v1']
  value=relay.compare_data_roles(consumer,[base],[after])
  self.assertTrue(value['accepted']);self.assertEqual(value['added_empty_Character_1_1_ids'],[2000])
  self.assertEqual(value['unique_physical_after_current_max'],[50,60])
  self.assertFalse(value['birth_producer_observed']);self.assertIsNone(value['native_Knight_membership'])
 def test_merge_complete_physical_change_or_unknown_empty_record_refused(self):
  base=army();changed=copy.deepcopy(base)
  changed['regiment_replenishment_records_v1'][0]['records'][0]['current_soldiers']=51
  self.assertFalse(relay.compare_data_roles(consumer,[base],[changed])['accepted'])
  unknown=army(role=True);del unknown['regiment_replenishment_records_v1'][0]['native_character_role_v1']
  value=relay.compare_data_roles(consumer,[base],[base,unknown])
  self.assertFalse(value['accepted']);self.assertIn('unexplained_ArRg_birth_or_removal',value['reasons'])

if __name__=='__main__':unittest.main()
