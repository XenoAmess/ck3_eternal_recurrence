"""Focused actual saved-packet reader and rejection checks; no live calls."""
from pathlib import Path
import argparse,importlib.util,json,sys,unittest
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT
if __name__=='__main__':
 p=argparse.ArgumentParser(add_help=False);p.add_argument('--repo',type=Path,default=ROOT)
 args,rest=p.parse_known_args();REPO=args.repo;sys.argv=[sys.argv[0],*rest]
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
path=ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_r09_selected93_actual_12004.py'
spec=importlib.util.spec_from_file_location('r09_saved_actual',path)
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
P=ROOT/'docs/ck3-native-ai/evidence/episode04-r09-selected93-12004/actual-literal-projection.json'
def fixture():return json.loads(P.read_text(encoding='utf-8'))
class ReaderTests(unittest.TestCase):
 def test_saved_actual_exact_exception_passes_without_full_card_credit(self):
  value=reader.qualify_r0176_selected93_micro_12004(fixture())
  self.assertTrue(value['accepted']);self.assertFalse(value['strict_unrelated_freeze_pass'])
  self.assertFalse(value['R09_full_card_closed']);self.assertIsNone(value['actual_physical_refill'])
 def test_physical_change_is_refused(self):
  value=fixture();row=value['stages']['post_merge']['packet']['query']['army_strengths'][1]
  row['regiment_replenishment_records_v1'][0]['records'][0]['current_soldiers']-=1
  with self.assertRaises(ValueError):reader.qualify_r0176_selected93_micro_12004(value)
 def test_other_character_or_commander_is_refused(self):
  value=fixture();packet=value['stages']['post_split']['packet']
  packet['commanders']['162']['army_commander_candidates']['current_commander']['character_id']+=1
  with self.assertRaises(ValueError):reader.qualify_r0176_selected93_micro_12004(value)
 def test_original_strict_failure_cannot_be_erased(self):
  value=fixture();del value['strict_failure_literal']
  with self.assertRaises(ValueError):reader.qualify_r0176_selected93_micro_12004(value)
 def test_stale_frame_or_unavailable_reclassification_is_refused(self):
  for mutation in ('frame','unavailable'):
   value=fixture();packet=value['stages']['post_merge']['packet']
   if mutation=='frame':packet['frame']['revision']=value['stages']['post_split']['packet']['frame']['revision']
   else:packet['excluded_unavailable_cohorts'][0]['strengths_qualified']=True
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):reader.qualify_r0176_selected93_micro_12004(value)
if __name__=='__main__':unittest.main()
