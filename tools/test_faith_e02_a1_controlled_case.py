"""Finite authored consumers of the real public A1 adapter. No native credit."""
from __future__ import annotations
import base64,copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('C:/workspace/ck3_eternal_recurrence')
sys.path[:0]=[str(HERE),str(ROOT/'tools'),str(ROOT)]
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.append(str(HERE/'ck3_mod_acceptance_cases'))
spec=importlib.util.spec_from_file_location('ck3_mod_acceptance_cases._a1_test',HERE/'ck3_mod_acceptance_cases/faith_e02_a1_controlled_adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);Q=A.Q
from ck3_mod_acceptance_client import CaseClient
OTHER=0x01000003
EXE=A.EXE
def frame(piety=425000000):
 return {'source':'injected-dll-named-pipe','backend_id':'native-headless','episode_projection':'native_campaign',
  'snapshot_id':'AUTHORED-A1','revision':5,'native_revision':4,'date_raw':51394920,'paused':True,'map_ready':True,
  'played_character':{'character_id':15893,'alive':True,'source':'native'},'active_event':None,'pending_character_interaction':None,
  'episode_run_id':None,'played_character_piety':{'raw':piety,'scale':100000},
  'played_character_gold':{'raw':100000000,'scale':100000},'played_character_prestige':{'raw':300000000,'scale':100000},
  'diagnostics':{'bridge_pid':1234,'connection_generation':4,'hello':{'pid':1234,'connection_generation':4,
   'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':EXE,'ck3_build_match':True,'game_adapter_id':'ck3-1.20.0.4-msvc-x64'}}}
class AuthoredPublicClient(CaseClient):
 operator_reviewer='AUTHORED-A1-reviewer'
 def __init__(self,image):
  self.image=image;self._binding=None;self.manifest={'game':{'version':'1.20.0.4','exe_sha256':EXE},'native':{'dll':{'sha256':'a'*64}}}
  self.calls=[];self.snapshot_calls=0;self.checkpoints={};self.demoted=False;self.denied=False;self.allowed=True;self.lost_ack=False
  self.level_drift=False;self.other_grade_drift=False;self.text_drift=False;self.wrong_rite=False;self.claim_source=False;self.stale_skill=False
  self.quote_drift=False;self.reviews=0;self.wallet_error=False
 def snapshot(self,**kwargs):
  self.snapshot_calls+=1
  return self.validate_frame(frame(325000000 if self.demoted and not self.wallet_error else 425000000))
 def remaining(self):return 1800
 def guard(self,reserve=90,**kwargs):
  if reserve<120:raise AssertionError('A1 discarded Quit reserve')
  return {}
 def checkpoint(self,name,value):
  if name in self.checkpoints:raise AssertionError('Duplicate public checkpoint')
  self.checkpoints[name]=copy.deepcopy(value)
 def root_checkpoint(self,name,request,reserve):
  self.guard(reserve);self.reviews+=1
  value={'run_id':'AUTHORED-A1','reviewer':self.operator_reviewer,'status':'complete'}
  if request.get('approval_key'):
   value.update(original_image_directly_reviewed=True,original_image=A.pin(self.image),
    reviewed_native_observation_sha256=A.digest(request['native_observation']),demote27_once_authorized=not self.denied)
  return value
 def execute_plan(self,steps,name,timeout=None):
  Q.validate({'steps':steps});result=[]
  for s in steps:
   self.calls.append(copy.deepcopy(s))
   if s['tool']==Q.CONFIRM:
    self.demoted=True
    if self.lost_ack:
     result.append({'ok':False,'error':'AUTHORED lost callback ACK','after_snapshot':frame(325000000)});continue
   result.append({'ok':True,'result':self.response(s['tool'],s['args']),
    'after_snapshot':frame(325000000 if self.demoted else 425000000)})
  return result
 def response(self,tool,args):
  common={'available':True,'read_only':True,'played_character_id':15893,'date_raw':51394920}
  if tool==Q.RELIGION:return {**common,'rite_id':15,'faith_id':50}
  if tool==Q.SITES:
   rows=[]
   for i,t,b in ((27,'medina',8492),(0,'jerusalem',8857)):
    major=not self.demoted if i==27 else not (self.demoted and self.other_grade_drift)
    rows.append({'available':True,'holy_site_id':i,'type_key':t,'barony_title_id':b,
      'associated_faiths':[{'available':True,'faith_id':50,'faith_lists_site':True,'eminent':major}],
      'inventory':{'available':True,'artifact_ids':[61,62]if i==27 else[63]}})
   return {**common,'current_faith_holy_site_ids':[27,0],'current_faith_sites':rows}
  if tool==Q.RELIC:
   target=args['holy_site_id']
   return {**common,'requested_holy_site_id':target,
    'county_context':{'available':True,'barony_title_id':8492 if target==27 else 8857,'county_title_id':8491,
      'county_holder_id':OTHER,'county_holder_rite_id':15,'county_holder_faith_id':50},
    'cached_world_state':{'available':True,'is_active':True,'total_active_artifact_rarity':8},
    'inventory':{'available':True,'artifact_ids':[61,62],
      'slots':[{'slot_index':0,'artifact_id':61},{'slot_index':1,'artifact_id':62},{'slot_index':2,'artifact_id':None}],
      'artifact_objects':[{'available':True,'artifact_id':i,'rarity_level':4,'native_holy_site_owner_id':27}for i in (61,62)]}}
  if tool==Q.ACTOR:
   target=args['character_id'];level=4 if target==15893 else 2
   if self.demoted and self.level_drift:level+=1
   diplomacy=15 if target==15893 else 10
   if self.demoted and not self.stale_skill:diplomacy-=4 if target==15893 else 2
   return {**common,'character_id':target,'requested_skill':'diplomacy','requested_skill_enum':0,
    'game_version':'1.20.0.4','executable_sha256':EXE,'two_pass_stable':True,'callback_provenance':'exact4_native',
    'rite_id':16 if self.wrong_rite and target==OTHER else 15,'faith_id':50,
    'current_skill_points':dict(zip(A.SKILLS,(diplomacy,9,8,7,6,5))),
    'effective_devotion_level':level,'devotion_total_raw':40000000 if target==15893 else 20000000,
    'actual_skill_breakdown':'AUTHORED whole Faith aggregate, not selected site proof'+(' changed'if self.demoted and self.text_drift else''),
    'site_attribution_observed':self.claim_source,'selected_site_contribution_raw':None,'cache_generation_time_known':False}
  if tool==Q.DETAIL:
   cost=200000000 if self.quote_drift and self.reviews else 100000000
   return {**common,'requested_holy_site_id':27,'action':'demote','decision_key':'demote_holy_site_decision',
    'requested_decision_key':'demote_holy_site_decision','detail_actor_id':15893,'current_actor_id':15893,
    'parameter_holy_site_id':27,'selected_holy_site_id':27,'selected_item_token':3,'parameter_and_selection_match':True,
    'native_detail_context_verified':True,'normal_requirements_legality_observed':True,'normal_requirements_can_confirm':self.allowed,
    'native_can_confirm':self.allowed,'bypass_requirements_observed':True,'bypass_requirements_raw':0,
    'native_resource_quote_available':True,'native_resource_quote':{'raw_scale':100000,'resource_vector_raw':[0,0,cost,0,0,0,0,0,0,0],
     'costs_raw':{'gold':0,'prestige':0,'piety':cost,'treasury':0},'native_affordable':True},
    'native_requirements_description_available':True,'native_requirements_description':'AUTHORED original requirements',
    'native_cost_description_available':True,'native_cost_description':'AUTHORED 1000 Piety'}
  if tool=='ck3_query_ingame_ui_window_v1':return {'available':True,'effective_visible':True,'subject_id_available':True,'current_subject_id':27}
  return {**common,'invoked':tool==Q.CONFIRM,'business_outcome_observed':False}

class A1Consumers(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='A1-authored-',dir=HERE.parents[1]);cls.work=Path(cls.temp.name)
  cls.image=cls.work/'AUTHORED-not-game.png';cls.image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='))
  cls.receipt=cls.work/'AUTHORED-cohort.json';cls.receipt.write_text('{"scope":"AUTHORED not a native qualification"}',encoding='utf-8')
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def context(self):
  out=self.work/('out-'+str(len(list(self.work.glob('out-*')))));out.mkdir()
  ledger=self.work/('ledger-'+out.name)
  c={'schema':'faith-e02-a1-controlled-case-v1','case':A.CASE,'product':A.PRODUCT,'machine_id':'4-8e1c2f1861',
   'saved_input':{'save':'AUTHORED-not-restored.ck3',**A.SAVE},'scope':A.SCOPE,'profile':{'enabled_mods':[],'product_files':[]},'max_public_calls':A.MAX_CALLS,
   'dependencies':[A.pin(p)for p in (A.__file__,Q.__file__,A.shared_opening_binding.__code__.co_filename,A.require_root_visual_review.__code__.co_filename)],
   'native_cohort':{'dll_sha256':'a'*64,'qualification_receipt':A.pin(self.receipt)},'intent_ledger_root':str(ledger),
   'intent_review_after_utc':'2026-10-27T00:00:00Z'}
  return {'case_contract':c,'case_spec':{'required_mcp_tools':sorted(A.REQUIRED),'opt_in_read_only_mcp_tools':sorted(Q.READONLY),
   **{k:False for k in A.CLOSED},'whole_product_acceptance_credit':False,'business_contract_applicable':False,
   'budgets':{'hold_seconds':1800,'timeout':2700}},'product':A.PRODUCT,'case':A.CASE,'run_id':'AUTHORED-A1','output':str(out),
   'shared_source_root':str(ROOT),'case_inputs':{'intent_ledger_root':str(ledger)}}
 def run_one(self,client,context=None):return A.run_case(context or self.context(),client)
 def count(self,c,tool):return sum(s['tool']==tool for s in c.calls)
 def test_controlled_pair_and_real_wallet_delta_remain_unattributed(self):
  c=AuthoredPublicClient(self.image);r=self.run_one(c)
  self.assertEqual(r['world_confirm_attempts'],1);self.assertEqual(self.count(c,Q.CONFIRM),1)
  self.assertEqual(r['status'],'GRADE_AND_TWO_ACTOR_READBACK_OBSERVED_ATTRIBUTION_PENDING')
  self.assertEqual([x['unattributed_diplomacy_delta']for x in r['post_observation']['pairs']],[-4,-2])
  self.assertEqual(r['major_site_ids_before'],[0,27]);self.assertEqual(r['post_observation']['major_site_ids_after'],[0])
  self.assertFalse(r['required_slots']['E2-A1']['closed']);self.assertFalse(r['site_attribution_observed']);self.assertIsNone(r['selected_site_contribution_raw'])
  self.assertLessEqual(r['public_calls_used'],48)
 def test_after_only_host_rows_use_independent_counted_action_preframes(self):
  c=AuthoredPublicClient(self.image);r=self.run_one(c)
  self.assertEqual(self.count(c,Q.CONFIRM),1)
  self.assertEqual(r['public_calls_used'],len(c.calls)+c.snapshot_calls)
  self.assertTrue(all('before_snapshot'not in row['row']for row in r['submitted_rows']))
  action_rows=[row for row in r['submitted_rows']if row['step']['tool']in Q.PRESENT|{Q.CONFIRM}]
  self.assertTrue(action_rows)
  self.assertTrue(all(isinstance(row.get('independent_before_snapshot'),dict)for row in action_rows))
 def test_denied_ordinary_legality_never_confirms(self):
  c=AuthoredPublicClient(self.image);c.allowed=False;r=self.run_one(c);self.assertEqual(self.count(c,Q.CONFIRM),0)
 def test_Root_PNG_denial_never_confirms(self):
  c=AuthoredPublicClient(self.image);c.denied=True;r=self.run_one(c);self.assertEqual(self.count(c,Q.CONFIRM),0)
 def test_changed_quote_after_review_never_confirms(self):
  c=AuthoredPublicClient(self.image);c.quote_drift=True;r=self.run_one(c);self.assertEqual(self.count(c,Q.CONFIRM),0)
 def test_lost_ACK_independent_post_does_not_replay_or_claim_source(self):
  c=AuthoredPublicClient(self.image);c.lost_ack=True;r=self.run_one(c)
  self.assertEqual(self.count(c,Q.CONFIRM),1);self.assertTrue(r['transport_outcome_unknown'])
  self.assertTrue(r['post_observation']['only_selected_major_relation_changed']);self.assertFalse(r['required_slots']['E2-A1']['closed'])
 def test_consumed_intent_survives_new_run_with_same_ledger(self):
  first=self.context();c=AuthoredPublicClient(self.image);c.lost_ack=True;self.run_one(c,first)
  second=self.context();second['case_contract']['intent_ledger_root']=first['case_contract']['intent_ledger_root'];second['case_inputs']['intent_ledger_root']=first['case_inputs']['intent_ledger_root']
  c2=AuthoredPublicClient(self.image);r=self.run_one(c2,second);self.assertEqual(self.count(c2,Q.CONFIRM),0)
  self.assertTrue(r['transport_outcome_unknown']);self.assertIsNotNone(r['historical_consumed_intent_blocked'])
 def test_failed_intent_fsync_never_submits_and_retains_exclusive_claim(self):
  context=self.context();c=AuthoredPublicClient(self.image)
  with patch.object(A.os,'fsync',side_effect=OSError('AUTHORED fsync failure')):r=self.run_one(c,context)
  self.assertEqual(self.count(c,Q.CONFIRM),0);self.assertEqual(r['world_confirm_attempts'],0)
  self.assertEqual(len(list(Path(context['case_contract']['intent_ledger_root']).glob('*.intent.json'))),1)
 def test_changed_own_level_or_other_major_or_wallet_is_partial(self):
  for field in ('level_drift','other_grade_drift','wallet_error'):
   with self.subTest(field=field):
    c=AuthoredPublicClient(self.image);setattr(c,field,True);r=self.run_one(c)
    self.assertEqual(self.count(c,Q.CONFIRM),1);self.assertEqual(r['status'],'DEMOTE_ATTEMPTED_POST_PARTIAL_OR_UNKNOWN');self.assertFalse(r['required_slots']['E2-A1']['closed'])
 def test_unchanged_cached_skill_is_retained_not_fabricated_minus_L(self):
  c=AuthoredPublicClient(self.image);c.stale_skill=True;r=self.run_one(c)
  self.assertEqual([x['unattributed_diplomacy_delta']for x in r['post_observation']['pairs']],[0,0])
  self.assertFalse(r['required_slots']['E2-A1']['closed']);self.assertFalse(r['post_observation']['cache_refresh_observed'])
 def test_different_Rite_or_attribution_claim_blocks_before_world_action(self):
  for field in ('wrong_rite','claim_source'):
   with self.subTest(field=field):
    c=AuthoredPublicClient(self.image);setattr(c,field,True);r=self.run_one(c);self.assertEqual(self.count(c,Q.CONFIRM),0)
 def test_required_tools_all_declared_once_no_late_addition(self):
  context=self.context();context['case_spec']['required_mcp_tools'].remove(Q.ACTOR)
  with self.assertRaises(ValueError):A.validate_contract(context)
  context=self.context();context['case_spec']['required_mcp_tools'].append(Q.ACTOR)
  with self.assertRaises(ValueError):A.validate_contract(context)
 def test_manual_public_Quit_cannot_be_replaced_by_product_automation(self):
  c=AuthoredPublicClient(self.image);c.selection=SimpleNamespace(normal_quit_automation={'AUTHORED':'forbidden helper'})
  with self.assertRaises(ValueError):self.run_one(c)
  self.assertEqual(self.count(c,Q.CONFIRM),0)
 def test_queue_only_one_demote27_and_fresh_revision_binding(self):
  good=Q.step('legal',Q.CONFIRM,{'action':'demote','holy_site_id':27});Q.validate({'steps':[good]})
  for change in ({'tool':'ck3_create_holy_site_once_v1'},{'args':{'action':'promote','holy_site_id':27}},
                 {'args':{'action':'demote','holy_site_id':0}},{'fresh_revision':False},
                 {'args':{'action':'demote','holy_site_id':27,'expected_revision':True}}):
   with self.subTest(change=change),self.assertRaises(ValueError):Q.validate({'steps':[{**good,**change}]})
  with self.assertRaises(ValueError):Q.validate({'steps':[good,{**good,'id':'second'}]})
 def test_cooldown_has_no_site_argument_and_unknown_cannot_become_zero(self):
  Q.validate({'steps':[Q.step('cooldown',Q.COOLDOWN,{'action':'demote'})]})
  with self.assertRaises(ValueError):Q.validate({'steps':[Q.step('bad',Q.COOLDOWN,{'action':'demote','holy_site_id':27})]})
  v=AuthoredPublicClient(self.image).response(Q.ACTOR,{'character_id':15893});v['available']=False
  with self.assertRaises(ValueError):A.actor(v,15893,15893,51394920)
if __name__=='__main__':unittest.main(verbosity=2)
