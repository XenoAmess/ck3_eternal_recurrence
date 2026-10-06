"""Actual parsed AST rows only; synthetic reconstruction never opens a save."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import test_i3b_reader as authored
reader=authored.reader

class SavedFaithHeadTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.fixture=json.loads((Path(__file__).parent/'fixtures/ACTUAL-R14-B5-saved-Faith-head-selected-AST.json').read_text(encoding='utf-8'))
 def data(self):return copy.deepcopy(self.fixture)
 def reference(self,data):return reader.saved_faith_religious_title_reference(data['faith_after'],107)
 def test_actual_headless_and_title_reference_preserve_raw(self):
  d=self.data();f=copy.deepcopy(d['faith_after']);before=copy.deepcopy(f)
  r=self.reference(d);self.assertEqual(r['full_id'],18373);self.assertEqual(r['entity_kind'],'landed_title')
  self.assertIsNone(r['native_qualification']);self.assertEqual(f,before)
  self.assertIsNone(reader.saved_faith_religious_title_reference(d['faith_before'],107)['full_id'])
 def test_actual_title_full_ast_holder_join(self):
  d=self.data();r=reader.derive_saved_faith_head_title_holder(self.reference(d),{18373:d['title_after']},18373,31254)
  self.assertEqual(r['holder_full_id'],31254);self.assertEqual(r['title_AST_sha256'],d['title_after']['AST_sha256'])
  self.assertEqual(r['raw_title_entries'],d['title_after']['entries']);self.assertIsNone(r['native_getter_credit'])
 def test_wrong_faith_rejected(self):
  d=self.data();d['faith_after']['id']=106
  with self.assertRaises(ValueError):self.reference(d)
 def test_wrong_result_title_rejected(self):
  d=self.data()
  with self.assertRaises(reader.ReadbackError):reader.derive_saved_faith_head_title_holder(self.reference(d),{18373:d['title_after']},18374,31254)
 def test_missing_title_entity_rejected(self):
  d=self.data()
  with self.assertRaises(reader.ReadbackError):reader.derive_saved_faith_head_title_holder(self.reference(d),{},18373,31254)
 def test_wrong_holder_rejected(self):
  d=self.data();t=d['title_after']
  next(r for r in t['entries'] if r['key']=='holder')['value']='65865';t['holder']=65865;t['AST_sha256']=reader.ast_sha(t['entries'])
  with self.assertRaises(reader.ReadbackError):reader.derive_saved_faith_head_title_holder(self.reference(d),{18373:t},18373,31254)
 def test_projection_holder_disagrees_with_ast_rejected(self):
  d=self.data();d['title_after']['holder']=65865
  with self.assertRaises(reader.ReadbackError):reader.derive_saved_faith_head_title_holder(self.reference(d),{18373:d['title_after']},18373,31254)
 def test_missing_raw_head_and_old_dual_field_shape_rejected(self):
  for old in (False,True):
   d=self.data();f=d['faith_after']
   if old:f['entries'].append({'key':'religious_head_title','value':'18373'});f['heads']['religious_head_title']='18373'
   else:f['entries']=[r for r in f['entries'] if r['key']!='religious_head'];f['heads']['religious_head']=None
   f['AST_sha256']=reader.ast_sha(f['entries'])
   with self.assertRaises(ValueError):self.reference(d)
 def test_noncanonical_or_typed_scalar_rejected(self):
  for token in ('018373','-1','18373.0',18373):
   d=self.data();f=d['faith_after'];next(r for r in f['entries'] if r['key']=='religious_head')['value']=token
   f['heads']['religious_head']=token;f['AST_sha256']=reader.ast_sha(f['entries'])
   with self.assertRaises(ValueError):self.reference(d)
 def test_raw_ast_and_projection_drift_rejected(self):
  for kind in ('ast','projection'):
   d=self.data();f=d['faith_after']
   if kind=='ast':f['AST_sha256']='0'*64
   else:f['heads']['religious_head']='18374'
   with self.assertRaises(ValueError):self.reference(d)
 def test_title_ast_identity_or_digest_drift_rejected(self):
  for key,value in (('title_id',18374),('AST_sha256','0'*64)):
   d=self.data();d['title_after'][key]=value
   with self.assertRaises(reader.ReadbackError):reader.derive_saved_faith_head_title_holder(self.reference(d),{18373:d['title_after']},18373,31254)
 def test_main_observe_text_uses_correct_join_and_keeps_original_red(self):
  d=self.data()['reconstructed']
  for key in ('characters','faiths','rites','titles'):d[key]={int(i):r for i,r in d[key].items()}
  state=authored.run(d)
  failed=[r['name'] for r in state['checks'] if not r['matches']]
  self.assertEqual(failed,self.fixture['expected_fieldmap_only_false_checks'])
  self.assertEqual(state['typed_religious_title_reference']['full_id'],18373)
  self.assertEqual(state['saved_faith_head_title_holder_join']['holder_full_id'],31254)
  self.assertEqual(state['faith']['entries'],self.fixture['faith_after']['entries'])
  self.assertEqual(state['faith']['AST_sha256'],self.fixture['faith_after']['AST_sha256'])
  self.assertEqual(state['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  self.assertIsNone(state['actual_pass']);self.assertIsNone(state['formal_mandate_credit'])
 def test_main_observe_text_wrong_join_does_not_gain_credit(self):
  d=self.data()['reconstructed']
  for key in ('characters','faiths','rites','titles'):d[key]={int(i):r for i,r in d[key].items()}
  next(r for r in d['titles'][18373] if r['key']=='holder')['value']='65865'
  s=authored.run(d)
  self.assertFalse(next(r['matches'] for r in s['checks'] if r['name']=='actual_saved_faith_head_title_holder_actor'))
  self.assertEqual(s['assessment'],'OBSERVED_CONTRACT_MISMATCH');self.assertIsNone(s['actual_pass'])

if __name__=='__main__':unittest.main(verbosity=2)
