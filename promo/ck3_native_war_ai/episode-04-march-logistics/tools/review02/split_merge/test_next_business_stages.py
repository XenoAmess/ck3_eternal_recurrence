"""Four new offline behavior checks only; all values are synthetic."""
from pathlib import Path
from types import SimpleNamespace
import copy,importlib.util,json,tempfile,unittest
spec=importlib.util.spec_from_file_location('r09_next',Path(__file__).with_name('root_relay.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def frame():
 return {'snapshot_id':'synthetic','revision':3,'native_revision':2,'date_raw':1,
  'player_armies':[{'army_id':i,'source':'native','controllable':True,'owner_character_id':7,
   'current_province_id':8,'in_combat':False,'retreating':False} for i in (93,162)]}
def caps():
 return {'backend_id':'native-headless','fallback_enabled':False,
  'bridge_capabilities':list(r.READ_CAPS|{r.ACTION_CAP['merge']}),'action_steps':['merge-armies-162-with-93','merge-armies-93-with-162']}
def row(i,stock,cap,weight):
 return {'army_id':i,'current_soldiers':250,'current_supply_raw':stock,'current_supply_scale':100000,
  'current_supply_capacity_raw':cap,'current_supply_capacity_scale':100000,
  'merge_supply_destination_weight_raw':weight,'merge_supply_destination_weight_scale':100000,'status':'available'}
def packet(rows):return {'frame':frame(),'query':{'army_strengths':rows},'capabilities':caps()}
class NextStages(unittest.TestCase):
 def test_reverse_claim_uses_fresh_child_destination_and_unknown_is_never_replayed(self):
  with tempfile.TemporaryDirectory() as d:
   live=r.Relay.__new__(r.Relay);live.case=Path(d)/'case';live.case.mkdir();live.run=Path(d)/'run'
   live.a=SimpleNamespace(attempt='synthetic',merge_destination='sibling');live.serial=0;live.binding={'actor':7};live.meta={}
   live.saved=lambda phase:{'source_army_id':93,'packet':packet([]),
    'split_assertion':{'accepted':True,'identity':{'sibling_army_id':162}}}
   live.snapshot=lambda name:(frame(),{});calls=[]
   def request(name,tool,args):
    calls.append((tool,args))
    if tool=='ck3_get_capabilities':return {'body':caps()},{}
    self.assertTrue((live.case/'merge.once.claim.json').exists());raise TimeoutError('synthetic pending')
   live.request=request
   with self.assertRaises(TimeoutError):live.submit_once('merge')
   claim=r.load(live.case/'merge.once.claim.json')
   self.assertEqual(claim['army_ids'],[162,93]);self.assertEqual(claim['step'],'merge-armies-162-with-93')
   with self.assertRaises(FileExistsError):live.submit_once('merge')
   self.assertEqual(sum(tool=='ck3_execute_step' for tool,args in calls),1)
 def test_clamp_requires_observed_postcap_and_exact_two_stage_result(self):
  before=packet([row(93,30000000,30000000,25000000),row(162,10000000,10000000,1)])
  after=packet([row(93,10000000,10000000,0)])
  value=r.compare_merge_supply(before,after,[93,162])
  self.assertEqual(value['weights_raw'],[25000000,25000000])
  self.assertEqual(value['preclamp_raw'],20000000);self.assertTrue(value['upper_clamp_observed'])
  after['query']['army_strengths'][0]['current_supply_raw']-=1
  self.assertFalse(r.compare_merge_supply(before,after,[93,162])['upper_clamp_observed'])
  del before['query']['army_strengths'][0]['merge_supply_destination_weight_raw']
  self.assertEqual(r.compare_merge_supply(before,after,[93,162])['status'],'HOLD_NATIVE_SUPPLY_OR_WEIGHT_UNAVAILABLE')
  # Historical .3 arithmetic vector only; no .4 or new runtime credit.
  before=packet([row(93,8299737,10000000,566000000),row(162,29122808,30000000,108100000)])
  before['query']['army_strengths'][1]['current_soldiers']=1086
  after=packet([row(93,11651751,30000000,0)])
  value=r.compare_merge_supply(before,after,[93,162])
  self.assertEqual(value['shares_raw'],[83901,16098]);self.assertEqual(value['contributions_raw'],[6963562,4688189])
  self.assertTrue(value['weighted_supply_match']);self.assertFalse(value['upper_clamp_observed'])
  live=r.Relay.__new__(r.Relay);live.original=lambda kind:({'army_ids':[93,162],'before_phase':'pre-merge'}, {})
  live.saved=lambda phase:{'merge_DATA_roles':{'accepted':False,'exact_source_removal_observed':False}}
  with self.assertRaises(RuntimeError):live.supply_clamp()
 def test_explicit_new_normal_run_admission_is_still_source_machine_sequence_bound(self):
  source='a'*40;run=r.MACHINE+'--vanilla--R0177'
  context={'machine_id':r.MACHINE,'source_head':source,'identity':{'machine_id':r.MACHINE,'run_id':run,'sequence':177,'mod_key':'vanilla'}}
  proof={'source_head':source,'machine_id':r.MACHINE,'run_id':run,'pid':1,'process_creation_filetime_100ns':2,
   'connection_generation':1,'actual_runtime_character_full_id':7,'episode_run_id':'synthetic',
   'stable_character_intent':{'historical_id':1128,'bookmark_character_name_key':'bookmark_rags_to_riches_duke_robert'}}
  self.assertEqual(r.admission(context,proof,run_id=run,source=source,sequence=177)['actor'],7)
  for wrong in ({'source':'b'*40},{'sequence':178}):
   args={'run_id':run,'source':source,'sequence':177};args.update(wrong)
   with self.subTest(wrong=wrong),self.assertRaises(RuntimeError):r.admission(context,proof,**args)
 def test_bad_premerge_packet_is_preserved_without_creating_an_action_ready_phase(self):
  with tempfile.TemporaryDirectory() as d:
   live=r.Relay.__new__(r.Relay);live.case=Path(d);live.a=SimpleNamespace(army_id=93,merge_source_army_id=162,merge_destination='source')
   live.binding={'actor':7};live.meta={};observed=packet([row(93,100,100,1)])
   live.packet=lambda name:observed
   live.save_packet=lambda name,p,**extra:r.write_new(live.case/(name+'.actual.json'),{'packet':p,**extra})
   with self.assertRaises(RuntimeError):live.pre_merge()
   self.assertTrue((live.case/'pre-merge-observation.actual.json').exists())
   self.assertFalse((live.case/'pre-merge.actual.json').exists());self.assertFalse((live.case/'merge.once.claim.json').exists())
if __name__=='__main__':unittest.main()
