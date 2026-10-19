from pathlib import Path
import sys,importlib.util,tempfile,unittest,json,copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from faith_power_promo import full_episode as common
from faith_power_promo import formal_episode as formal
class Contract(unittest.TestCase):
 def fixture(self):
  d={'scope':'episode02-review-segment','review_content_kind':'rules-and-previews-only','machine_id':'test-machine','cues':[{'id':'c','content_class':'preview'}],'pending_result_slots':{},'voice_authoring_catalog':'voices','cue_evidence_catalog':'evidence'}
  v={'schema':formal.VOICE_CATALOG_SCHEMA,'machine_id':d['machine_id'],'voice_authoring_projection':True,'projection_is_original_TTS_freeze':False,'cue_count':1,'cues':[{'id':'c'}],'new_live_result_voice_slots':{}}
  e={'schema':formal.EVIDENCE_SCHEMA,'machine_id':d['machine_id'],'cues':[{'id':'c','claim_ids':['p'],'shot_ids':['s'],'source_refs':[]}],'claims':[{'id':'p','claim_kind':'observed-preview'}],'native_checks':[]}
  f=formal.FormalInputs(d,common);f.load=lambda key:{'voices':v,'evidence':e}[key]
  return d,v,e,f
 def test_actual_formal_consumer_accepts_explicit_preview_excerpt(self):
  d,v,e,f=self.fixture();old,claims,checks=f.value_v3_inventory();self.assertEqual(old['c']['claim_ids'],['p'])
 def test_formal_full_still_requires_live_slots(self):
  d,v,e,f=self.fixture();d['scope']='episode02-formal-review'
  with self.assertRaisesRegex(ValueError,'preserve'):f.value_v3_inventory()
 def test_result_claim_cannot_use_empty_slot_exception(self):
  d,v,e,f=self.fixture();e['claims'][0]['claim_kind']='observed-live-result'
  with self.assertRaisesRegex(ValueError,'preserve'):f.value_v3_inventory()
 def test_nonempty_pending_not_erased(self):
  d,v,e,f=self.fixture();d['pending_result_slots']={'equip':None}
  with self.assertRaisesRegex(ValueError,'preserve'):f.value_v3_inventory()
 def test_real_profile_quality_and_measured_budget(self):
  rows=[{'duration_seconds':18.0} for _ in range(28)]+[{'duration_seconds':62.0}];d,_,_,_=self.fixture();d['prepared_visual_policy']=common.PREPARED_RETIRE_POLICY
  b=common.document_budget(d,rows,profile=common.EPISODE02_SAMPLE_PROFILE)
  self.assertLess(b['peak_new_bytes'],640*1024**2-8*1024**2)
  self.assertEqual(b['geometry'],[2560,1440,30]);self.assertEqual(b['crf'],21)
  self.assertEqual(b['video_maxrate_bps'],3000000);self.assertEqual(b['required_workers'],1)
  with self.assertRaises(ValueError):common.peak_budget(571,29,profile=common.EPISODE02_SAMPLE_PROFILE)
 def probe(self):return {'format':{'duration':'1.0'},'streams':[{'codec_type':'video','codec_name':'h264','width':2560,'height':1440},{'codec_type':'audio','codec_name':'aac'}]}
 def test_exact_retirement_keeps_clip_source_and_receipts(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);v=p/'cue.visual.mp4';t=p/'cue.mp4';s=p/'source.png'
   v.write_bytes(b'generated prepared');t.write_bytes(b'verified voiced');s.write_bytes(b'original source')
   receipt=common.retire_prepared(v,t,self.probe(),1,p/'receipt','test-machine')
   self.assertFalse(v.exists());self.assertTrue(t.exists());self.assertTrue(s.exists())
   saved=json.loads(receipt.read_text(encoding='utf-8'));self.assertFalse(saved['prepared_exists_after']);self.assertTrue((receipt.parent/'before-delete.json').exists())
 def test_bad_voiced_clip_keeps_prepared(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);v=p/'cue.visual.mp4';t=p/'cue.mp4';v.write_bytes(b'prepared');t.write_bytes(b'clip')
   probe=self.probe();probe['streams']=probe['streams'][:1]
   with self.assertRaisesRegex(ValueError,'complete voiced'):common.retire_prepared(v,t,probe,1,p/'receipt','test-machine')
   self.assertTrue(v.exists());self.assertFalse((p/'receipt').exists())
 def test_other_prepared_path_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);v=p/'other.visual.mp4';t=p/'cue.mp4';v.write_bytes(b'prepared');t.write_bytes(b'clip')
   with self.assertRaisesRegex(ValueError,'exact corresponding'):common.retire_prepared(v,t,self.probe(),1,p/'receipt','test-machine')
   self.assertTrue(v.exists())
if __name__=='__main__':unittest.main()
