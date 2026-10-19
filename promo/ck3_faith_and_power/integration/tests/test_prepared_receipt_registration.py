from pathlib import Path
import tempfile,unittest,sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from faith_power_promo import full_episode as c
from xar_promo.operations import start_run,preserve_artifact
from xar_promo.project import load_document
PROJECT={'format_version':1,'kind':'xar_promo_project_config','project':{'id':'receipt-contract-test','title':'Receipt path contract'},
 'pipeline':{'adapter':'faith-power-opening','preset':'faith-power-opening-1440p30'},'locales':{'narration':'zh-CN','subtitles':['zh-CN','en']},
 'constraints':{'duration_limit_seconds':570},'chapters':[{'id':'C1','type':'mixed-explainer','state':'planned','title':{'zh-CN':'Test'},'artifact_ids':[],
 'cues':[{'id':'T1','narration':{'zh-CN':'测试'},'subtitles':{'zh-CN':'测试','en':'Test'}}]}]}
class Contract(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
  (self.root/'audit').mkdir()
  config=c.write(self.root/'project.json',PROJECT);self.run=start_run(config,run_id='test-receipt',run_directory=self.root/'native-run')
 def tearDown(self):self.temp.cleanup()
 def test_original_external_audit_is_refused_by_actual_consumer(self):
  source=c.write(self.root/'audit/receipt.json',{'test':'external'})
  with self.assertRaises(ValueError):c.direct_register(self.run,[('receipt','exact-prepared-retirement',source,'application/json')])
 def test_future_run_relative_receipt_registers_without_copy(self):
  media=self.run.parent/'derived/direct';media.mkdir(parents=True)
  visual=media/'cue.visual.mp4';clip=media/'cue.mp4';visual.write_bytes(b'prepared-unit-fixture');clip.write_bytes(b'voiced-unit-fixture')
  probe={'format':{'duration':'1'},'streams':[{'codec_type':'video','codec_name':'h264','width':2560,'height':1440},{'codec_type':'audio','codec_name':'aac'}]}
  receipt=c.retire_prepared(visual,clip,probe,1,self.run.parent/'derived/receipts/prepared-retirement/cue','unit-test')
  c.direct_register(self.run,[('receipt','exact-prepared-retirement',receipt,'application/json')])
  actual=load_document(self.run,check_files=True).run;self.assertEqual(len(actual.artifacts),1);self.assertTrue(actual.artifacts[0].path.startswith('derived/receipts/'))
 def test_existing_external_receipt_public_preserve_is_valid_recovery(self):
  source=c.write(self.root/'audit/receipt.json',{'test':'existing-external'})
  item=preserve_artifact(self.run,source,artifact_id='receipt',collection='raw',role='exact-prepared-retirement',label=None,media_type='application/json')
  actual=load_document(self.run,check_files=True).run;self.assertEqual(len(actual.artifacts),1);self.assertEqual(item.bytes,source.stat().st_size)
if __name__=='__main__':unittest.main()
