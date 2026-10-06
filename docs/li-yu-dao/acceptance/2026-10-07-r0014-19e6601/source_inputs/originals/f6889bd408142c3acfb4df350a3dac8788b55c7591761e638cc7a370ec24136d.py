"""Versioned saved AST semantics; no save, game or native predicate query."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import test_i3b_reader as authored
reader=authored.reader

def remove_head_group(rows, keys):
 # Actual Rite doctrine rows are inside data, while actual Faith rows are top level.
 return [{'key':r['key'],'value':remove_head_group(r['value'],keys) if isinstance(r['value'],list) else r['value']}
         for r in rows if not(r['key']=='doctrine' and isinstance(r['value'],str) and reader.unquote(r['value']) in keys)]

class SavedFaithSemanticsV2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  d=Path(__file__).parent/'fixtures'
  cls.fixture=json.loads((d/'ACTUAL-R14-B5-saved-Faith-head-selected-AST.json').read_text(encoding='utf-8'))
  cls.request=json.loads((d/'ACTUAL-R14-B5-v2-Faith-semantics-request.json').read_text(encoding='utf-8'))
 def data(self):
  d=copy.deepcopy(self.fixture['reconstructed']);d['request']=copy.deepcopy(self.request)
  for key in ('characters','faiths','rites','titles'):d[key]={int(i):r for i,r in d[key].items()}
  return d
 def run_data(self,d):return authored.run(d)
 def model(self):return reader.saved_faith_semantics_contract(self.request)
 def test_actual_v2_direct_and_effective_are_distinct_no_native_credit(self):
  s=self.run_data(self.data());obs=s['faith_doctrine_observation']
  self.assertEqual(obs['direct_saved_faith_doctrine_keys'],['doctrine_no_head'])
  self.assertEqual(obs['direct_saved_main_rite_doctrine_keys'],['doctrine_temporal_head'])
  self.assertEqual(obs['effective_head_doctrine_keys'],['doctrine_temporal_head'])
  self.assertEqual(obs['precedence_source'],'main_rite');self.assertIsNone(obs['native_predicate_observed'])
  self.assertIsNone(obs['native_runtime_credit']);self.assertEqual(s['faith']['entries'],self.fixture['faith_after']['entries'])
 def test_declared_faith_delta_matches_and_political_red_remains(self):
  s=self.run_data(self.data());delta=s['faith_expected_factory_AST_delta']
  self.assertTrue(delta['matches']);self.assertTrue(delta['direct_doctrine_raw_unchanged'])
  self.assertEqual([r['name'] for r in s['checks'] if not r['matches']],[f'political_{i}_full_AST_protected' for i in (2230,2231,2235,2262,2264)])
  self.assertEqual(s['assessment'],'OBSERVED_CONTRACT_MISMATCH');self.assertIsNone(s['actual_pass']);self.assertIsNone(s['formal_mandate_credit'])
 def test_v1_keeps_original_direct_doctrine_expectation(self):
  s=self.run_data(copy.deepcopy(self.data()) | {'request':copy.deepcopy(self.fixture['reconstructed']['request'])})
  self.assertEqual(s['saved_faith_semantics_version'],'legacy-v1');self.assertIsNone(s['faith_doctrine_observation'])
  self.assertFalse(next(r['matches'] for r in s['checks'] if r['name']=='faiths_107_native_temporal_doctrine'))
 def test_wrong_or_missing_semantic_binding_rejected(self):
  for field in ('contract_sha256','schema'):
   d=self.data();d['request']['saved_faith_semantics_binding'][field]='wrong'
   with self.assertRaises(ValueError):self.run_data(d)
  d=self.data();del d['request']['saved_faith_semantics_binding']
  with self.assertRaises(ValueError):self.run_data(d)
 def test_wrong_main_rite_or_parent_faith_rejected(self):
  for target,key,value in (('faiths','main_rite','159'),('rites','faith','104')):
   d=self.data();rows=d[target][107 if target=='faiths' else 169]
   next(r for r in rows if r['key']==key)['value']=value
   with self.assertRaises(ValueError):self.run_data(d)
 def test_ambiguous_same_group_doctrines_rejected(self):
  for key,i in (('faiths',107),('rites',169)):
   d=self.data();d[key][i].append({'key':'doctrine','value':'doctrine_spiritual_head'})
   with self.assertRaises(ValueError):self.run_data(d)
 def test_missing_both_head_groups_rejected(self):
  d=self.data();keys=set(self.model()['head_group']['doctrine_keys'])
  for key,i in (('faiths',107),('rites',169)):d[key][i]=remove_head_group(d[key][i],keys)
  with self.assertRaises(ValueError):self.run_data(d)
 def test_unoccupied_main_group_uses_direct_faith_additive(self):
  d=self.data();keys=set(self.model()['head_group']['doctrine_keys'])
  d['rites'][169]=remove_head_group(d['rites'][169],keys)
  s=self.run_data(d);obs=s['faith_doctrine_observation']
  self.assertEqual(obs['precedence_source'],'Faith_additive');self.assertEqual(obs['effective_head_doctrine_keys'],['doctrine_no_head'])
  self.assertFalse(next(r['matches'] for r in s['checks'] if r['name']=='faiths_107_derived_effective_temporal_doctrine'))
 def test_missing_baseline_full_ast_rejected(self):
  d=self.data();del d['request']['baseline']['graphs']['faiths']['107']['entries']
  with self.assertRaises(ValueError):self.run_data(d)
 def test_unrelated_faith_row_drift_not_whitelisted(self):
  d=self.data();d['faiths'][107].append({'key':'extra_engine_field','value':'unexpected'})
  s=self.run_data(d);self.assertFalse(s['faith_expected_factory_AST_delta']['matches'])
 def test_direct_faith_doctrine_row_order_and_status_drift_rejected(self):
  d=self.data();rows=d['faiths'][107];indices=[i for i,r in enumerate(rows) if r['key']=='doctrine']
  rows[indices[0]],rows[indices[1]]=rows[indices[1]],rows[indices[0]]
  s=self.run_data(d);self.assertFalse(s['faith_expected_factory_AST_delta']['matches'])
  self.assertFalse(next(r['matches'] for r in s['checks'] if r['name']=='faiths_107_direct_saved_tenet_status_projection'))
 def test_wrong_recognized_leader_typed_value_or_duplicates_rejected(self):
  for variant in ('wrong_actor','wrong_type','duplicate','missing'):
   d=self.data();variables=reader.one(d['faiths'][107],'variables');rows=reader.one(variables,'data')
   row=next(r for r in rows if reader.unquote(reader.one(r['value'],'flag') or '')=='lyd_c3_recognized_leader')
   if variant=='duplicate':rows.append(copy.deepcopy(row))
   elif variant=='missing':rows.remove(row)
   else:
    inner=reader.one(row['value'],'data');next(r for r in inner if r['key']==('identity' if variant=='wrong_actor' else 'type'))['value']='65865' if variant=='wrong_actor' else 'faith'
   with self.assertRaises(ValueError):self.run_data(d)
 def test_other_variable_drift_not_whitelisted(self):
  d=self.data();variables=reader.one(d['faiths'][107],'variables');rows=reader.one(variables,'data')
  row=next(r for r in rows if reader.unquote(reader.one(r['value'],'flag') or '')=='free_holy_site_actions')
  next(r for r in reader.one(row['value'],'data') if r['key']=='identity')['value']='400000'
  self.assertFalse(self.run_data(d)['faith_expected_factory_AST_delta']['matches'])
 def test_preexisting_recognized_leader_baseline_rejected(self):
  d=self.data();baseline=d['request']['baseline']['graphs']['faiths']['107'];rows=reader.one(reader.one(baseline['entries'],'variables'),'data')
  actual=reader.one(reader.one(d['faiths'][107],'variables'),'data')
  rows.insert(0,copy.deepcopy(actual[0]));baseline['AST_sha256']=reader.ast_sha(baseline['entries'])
  with self.assertRaises(ValueError):self.run_data(d)
 def test_wrong_head_delta_or_old_dual_field_form_rejected(self):
  for old in (False,True):
   d=self.data()
   if old:d['faiths'][107].append({'key':'religious_head_title','value':'18373'})
   else:next(r for r in d['faiths'][107] if r['key']=='religious_head')['value']='18374'
   if old:
    with self.assertRaises(ValueError):self.run_data(d)
   else:
    s=self.run_data(d);self.assertFalse(next(r['matches'] for r in s['checks'] if r['name']=='faith_and_receipt_actual_title_agree'))

if __name__=='__main__':unittest.main(verbosity=2)
