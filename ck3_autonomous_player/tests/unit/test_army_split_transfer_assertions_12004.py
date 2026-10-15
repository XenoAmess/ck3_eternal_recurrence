"""Synthetic typed split packets; no native, SDK, game, build, or EXE execution."""
from pathlib import Path
import copy,importlib.util,os,sys,unittest

ROOT=Path(__file__).resolve().parents[3]
REPO=Path(os.environ.get('XAR_REPO_ROOT',str(ROOT)))
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
path=ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/army_split_transfer_assertions_12004.py'
spec=importlib.util.spec_from_file_location('split_transfer_candidate',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def record(persistent,index,current=50):
 return {'record_index':index,'persistent_regiment_id':persistent,'chunk_index':0,
  'status':'available','unavailable_reason':None,'current_soldiers':current,
  'maximum_soldiers':60,'effective_current_soldiers':current,'state_raw':0,
  'chunk_army_regiment_id':persistent,'native_can_replenish':False,
  'native_chunk_can_replenish':False,'persistent_monthly_replenishment_fraction_raw':0,
  'persistent_prepared_replenishment_fraction_raw':0,
  'persistent_monthly_replenishment_fraction_scale':100000,
  'persistent_prepared_replenishment_fraction_scale':100000}

def regiment(identity,army,*,role=False):
 strength={'army_regiment_id':identity,'current_soldiers':1 if role else 50,
           'maximum_soldiers':1 if role else 60,'scale':1}
 data={'army_regiment_id':identity,'source':'native_all_data_records','status':'available',
       'ready':True,'native_data_record_count':0 if role else 1,'unavailable_reason':None,
       'native_loss_writer_skipped':role,'loss_writer_admission_unavailable_reason':None,
       'records':[] if role else [record(identity,0)]}
 if role:
  data['native_character_role_v1']={'source':'native_selected_ArRg_character_role_raw',
   'status':'available','army_regiment_id':identity,'native_carmy_id':army,
   'arrg_army_id_140':army,'character_raw_id_148':70,'resolved_character_id':70,
   'character_magic_1c':0x43686172,'resolution_used_fallback':False,
   'native_character_predicate':True,'character_extension_present':True,
   'extension_army_id_f4':-1,'extension_arrg_id_f8':identity,
   'same_ArRg_instance_after':True,'unavailable_reason':None}
 return strength,data

def army(public,native,pairs):
 return {'army_id':public,'native_carmy_id':native,'status':'available',
  'regiment_count':len(pairs),'regiment_strengths':[p[0] for p in pairs],
  'regiment_replenishment_records_v1':[p[1] for p in pairs],
  'current_soldiers':sum(p[0]['current_soldiers'] for p in pairs),
  'maximum_soldiers':sum(p[0]['maximum_soldiers'] for p in pairs)}

def frame(name,revision,ids):
 return {'snapshot_id':name,'revision':revision,'native_revision':revision+100,
  'paused':True,'map_ready':True,'date_raw':999,'episode_run_id':'synthetic-split',
  'diagnostics':{'bridge_pid':222,'connection_generation':4},
  'played_character':{'character_id':7,'alive':True},'player_armies':[
   {'army_id':i,'owner_character_id':7,'current_province_id':10,'controllable':True}
   for i in ids]}

def commander(frame,public,native,character):
 return {'accepted':True,'read_only':True,'queried_snapshot_id':frame['snapshot_id'],
  'queried_revision':frame['revision'],'queried_native_revision':frame['native_revision'],
  'army_commander_candidates':{'army_id':public,'native_carmy_id':native,
   'date_raw':frame['date_raw'],'snapshot_revision':frame['native_revision'],
   'current_commander':{'status':'absent' if character is None else 'available',
                        'character_id':character}}}

def fixture():
 before=frame('before',1,[500]);after=frame('after',2,[500,501])
 first=regiment(1000,8000);second=regiment(1001,8000)
 pre={'accepted':True,'queried_snapshot_id':'before','queried_revision':1,
      'queried_native_revision':101,'army_strengths':[army(500,8000,[first,second])]}
 post={'accepted':True,'queried_snapshot_id':'after','queried_revision':2,
       'queried_native_revision':102,'army_strengths':[
        army(500,8000,[copy.deepcopy(first)]),
        army(501,8001,[copy.deepcopy(second),regiment(2000,8001,role=True)])]}
 return {'before':before,'after':after,'source_army_id':500,'pre_strengths':pre,
         'post_strengths':post,'pre_commander':commander(before,500,8000,70),
         'post_commanders':{500:commander(after,500,8000,None),
                            501:commander(after,501,8001,80)}}

class SplitTransferTests(unittest.TestCase):
 def test_uneven_cache_and_new_character_record_preserve_physical_DATA(self):
  result=module.assert_fresh_split_transfer_12004(**fixture())
  self.assertTrue(result['accepted'])
  self.assertEqual(result['unique_physical_before_current_max'],[100,120])
  self.assertEqual(result['unique_physical_after_current_max'],[100,120])
  self.assertEqual(result['whole_cache_after_current_max'],[101,121])
  self.assertEqual(result['added_empty_character_1_1_ids'],[2000])
  self.assertEqual(result['actual_commanders_after'],{500:None,501:80})
  self.assertIsNone(result['native_knight_membership'])
  self.assertIsNone(result['actual_physical_refill'])
  self.assertFalse(result['birth_producer_observed'])

 def test_complete_physical_change_returns_named_refusal(self):
  args=fixture();child=args['post_strengths']['army_strengths'][0]
  child['regiment_replenishment_records_v1'][0]['records'][0]['current_soldiers']=51
  result=module.assert_fresh_split_transfer_12004(**args)
  self.assertFalse(result['accepted'])
  self.assertIn('physical_chunk_values_changed',result['reasons'])
  self.assertIsNone(result['video_claim'])

 def test_unknown_empty_record_is_not_explained_as_character(self):
  args=fixture();data=args['post_strengths']['army_strengths'][1]['regiment_replenishment_records_v1'][1]
  del data['native_character_role_v1'];data['native_loss_writer_skipped']=None
  result=module.assert_fresh_split_transfer_12004(**args)
  self.assertFalse(result['accepted'])
  self.assertIn('unexplained_ArRg_birth_or_removal',result['reasons'])

 def test_aliases_are_deduplicated_for_physical_totals_but_not_occurrences(self):
  args=fixture()
  for packet in (args['pre_strengths'],args['post_strengths']):
   for child in packet['army_strengths']:
    for data in child['regiment_replenishment_records_v1']:
     if data['army_regiment_id']==1000:
      alias=copy.deepcopy(data['records'][0]);alias['record_index']=1
      data['records'].append(alias);data['native_data_record_count']=2
  result=module.assert_fresh_split_transfer_12004(**args)
  self.assertTrue(result['accepted'])
  self.assertEqual(result['unique_physical_after_current_max'],[100,120])
  row=args['post_strengths']['army_strengths'][0]['regiment_replenishment_records_v1'][0]
  row['records'].pop();row['native_data_record_count']=1
  result=module.assert_fresh_split_transfer_12004(**args)
  self.assertFalse(result['accepted'])
  self.assertIn('DATA_occurrence_or_ArRg_backlink_changed',result['reasons'])

 def test_incomplete_query_or_commander_is_rejected(self):
  for change in ('partial','commander','stale','wrong_native_army'):
   args=fixture()
   if change=='partial':args['post_strengths']['army_strengths'][0]['regiment_replenishment_records_v1'][0]['status']='partial'
   if change=='commander':args['post_commanders'][500]['army_commander_candidates']['current_commander']['status']='unavailable'
   if change=='stale':args['after']['snapshot_id']='before'
   if change=='wrong_native_army':args['post_strengths']['army_strengths'][1]['regiment_replenishment_records_v1'][1]['native_character_role_v1']['native_carmy_id']=8000
   with self.subTest(change=change),self.assertRaises(ValueError):module.assert_fresh_split_transfer_12004(**args)

if __name__=='__main__':unittest.main()
