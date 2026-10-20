"""Finite authored consumers of the real public MECCA adapter. No native credit."""
from __future__ import annotations
import base64,copy,importlib.util,json,os,shutil,sys,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('XAR_CASE_TEST_SOURCE_ROOT',str(HERE.parent))).resolve()
sys.path[:0]=[str(HERE),str(ROOT/'tools'),str(ROOT)]
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.append(str(HERE/'ck3_mod_acceptance_cases'))
spec=importlib.util.spec_from_file_location('ck3_mod_acceptance_cases._mecca_test',HERE/'ck3_mod_acceptance_cases/faith_e02_mecca_knight_controlled_adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);Q=A.Q
from ck3_mod_acceptance_client import CaseClient
OTHER=0x01000003
EXE=A.EXE
def frame(piety=425000000,date=51394920):
 return {'source':'injected-dll-named-pipe','backend_id':'native-headless','episode_projection':'native_campaign',
  'snapshot_id':'AUTHORED-MECCA','revision':5,'native_revision':4,'date_raw':date,'paused':True,'map_ready':True,
  'played_character':{'character_id':15893,'alive':True,'source':'native'},'active_event':None,'pending_character_interaction':None,
  'episode_run_id':None,'played_character_piety':{'raw':piety,'scale':100000},
  'played_character_gold':{'raw':100000000,'scale':100000},'played_character_prestige':{'raw':300000000,'scale':100000},
  'diagnostics':{'bridge_pid':1234,'connection_generation':4,'hello':{'pid':1234,'connection_generation':4,
   'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':EXE,'ck3_build_match':True,'game_adapter_id':'ck3-1.20.0.4-msvc-x64'}}}
class AuthoredPublicClient(CaseClient):
 operator_reviewer='AUTHORED-MECCA-reviewer'
 def __init__(self,image):
  self.image=image;self._binding=None;self.manifest={'game':{'version':'1.20.0.4','exe_sha256':EXE},'native':{'dll':{'sha256':'a'*64}}}
  self.calls=[];self.snapshot_calls=0;self.checkpoints={};self.demoted=False;self.denied=False;self.allowed=True;self.lost_ack=False
  self.level_drift=False;self.other_grade_drift=False;self.text_drift=False;self.wrong_rite=False;self.claim_source=False;self.stale_skill=False
  self.quote_drift=False;self.reviews=0;self.wallet_error=False;self.stale_skill=True
  self.date=51394920;self.day_calls=0;self.day_elapsed=24;self.day_unknown=False;self.day_raises=False;self.day_level_drift=False
  self.knight_unavailable=False;self.knight_shared_fallback=False;self.knight_quote_drift=False;self.stale_knight=False;self.foreign_faith=False
  self.natural_allowed=False;self.natural_limit=3
 def snapshot(self,**kwargs):
  self.snapshot_calls+=1
  return self.validate_frame(self.current_frame(325000000 if self.demoted and not self.wallet_error else 425000000))
 def current_frame(self,piety=None):return frame((325000000 if self.demoted else 425000000)if piety is None else piety,self.date)
 def remaining(self):return 3600
 def guard(self,reserve=90,**kwargs):
  if reserve<120:raise AssertionError('MECCA discarded Quit reserve')
  return {}
 def checkpoint(self,name,value):
  if name in self.checkpoints:raise AssertionError('Duplicate public checkpoint')
  self.checkpoints[name]=copy.deepcopy(value)
 def root_checkpoint(self,name,request,reserve):
  self.guard(reserve);self.reviews+=1
  value={'run_id':'AUTHORED-MECCA','reviewer':self.operator_reviewer,'status':'complete'}
  if request.get('approval_key'):
   value.update(original_image_directly_reviewed=True,original_image=A.pin(self.image),
    reviewed_native_observation_sha256=A.digest(request['native_observation']),demote26_once_authorized=not self.denied)
  if request.get('approval_key')=='natural_refresh_observation_authorized':
   value.update(natural_refresh_observation_authorized=self.natural_allowed,max_natural_days=self.natural_limit)
  return value
 def execute_plan(self,steps,name,timeout=None):
  Q.validate({'steps':steps});result=[]
  for s in steps:
   self.calls.append(copy.deepcopy(s))
   if s.get('kind')=='advance_day':
    before=self.current_frame();self.day_calls+=1;self.date+=self.day_elapsed;after=self.current_frame()
    if self.day_raises:raise TimeoutError('AUTHORED execute_plan raised after actual clock moved')
    if self.day_unknown:result.append({'ok':False,'error':'AUTHORED natural clock ACK unknown','after_snapshot':after});continue
    result.append({'ok':True,'result':{'before':before,'after':after,'elapsed_hours':self.day_elapsed,
      'requested_interval_complete':True,'event_boundary':None},'after_snapshot':after});continue
   if s['tool']==Q.CONFIRM:
    self.demoted=True
    if self.lost_ack:
     result.append({'ok':False,'error':'AUTHORED lost callback ACK','after_snapshot':self.current_frame()});continue
   result.append({'ok':True,'result':self.response(s['tool'],s['args']),'after_snapshot':self.current_frame()})
  return result
 def response(self,tool,args):
  common={'available':True,'read_only':True,'played_character_id':15893,'date_raw':self.date}
  if tool==Q.RELIGION:return {**common,'rite_id':15,'faith_id':50}
  if tool==Q.SITES:
   rows=[]
   for i,t,b in ((26,'mecca',8518),(0,'jerusalem',8857)):
    major=not self.demoted if i==26 else not (self.demoted and self.other_grade_drift)
    rows.append({'available':True,'holy_site_id':i,'type_key':t,'barony_title_id':b,
      'associated_faiths':[{'available':True,'faith_id':50,'faith_lists_site':True,'eminent':major}],
      'inventory':{'available':True,'artifact_ids':[61,62]if i==26 else[63]}})
   return {**common,'current_faith_holy_site_ids':[26,0],'current_faith_sites':rows}
  if tool==Q.RELIC:
   target=args['holy_site_id']
   return {**common,'requested_holy_site_id':target,
    'county_context':{'available':True,'barony_title_id':8518 if target==26 else 8857,'county_title_id':8491,
      'county_holder_id':OTHER,'county_holder_rite_id':15,'county_holder_faith_id':50},
    'cached_world_state':{'available':True,'is_active':True,'total_active_artifact_rarity':8},
    'inventory':{'available':True,'artifact_ids':[61,62],
      'slots':[{'slot_index':0,'artifact_id':61},{'slot_index':1,'artifact_id':62},{'slot_index':2,'artifact_id':None}],
      'artifact_objects':[{'available':True,'artifact_id':i,'rarity_level':4,'native_holy_site_owner_id':26}for i in (61,62)]}}
  if tool==Q.KNIGHT:
   target=args['character_id'];raw=120000 if target==15893 else 125000
   if self.demoted and not self.stale_knight:raw-=4000
   if self.knight_quote_drift and self.reviews:raw+=1
   text='AUTHORED native-style original, Mecca source '+str(raw)
   return {**common,'schema':'ck3_12004_character_knight_effectiveness_v1','backend_id':'native-headless',
    'domain_key':'character_knight_effectiveness_v1','status':'available','snapshot_revision':4,'queried_native_revision':4,
    'available':not(self.knight_unavailable and target==OTHER),'character_id':target,
    'rite_id':16 if self.wrong_rite and target==OTHER else 15,'faith_id':50,
    'game_version':'1.20.0.4','executable_sha256':EXE,'two_pass_stable':True,
    'own_actor_context_verified':not self.knight_shared_fallback,'callback_provenance':'exact4_native',
    'knight_effectiveness_raw':raw,'actual_knight_effectiveness_breakdown':text,'raw_scale':100000,
    'modifier_cache_refreshed':False,'cache_generation_time_known':False,'site_attribution_observed':False,
    'selected_site_contribution_raw':None,'gameplay_command_submitted':False,'raw_pointer_fields_persisted':False,'script_cache_rng_effects':'unknown'}
  if tool==Q.ACTOR:
   target=args['character_id'];level=4 if target==15893 else 2
   if self.demoted and self.level_drift or self.day_calls and self.day_level_drift:level+=1
   diplomacy=15 if target==15893 else 10
   if self.demoted and not self.stale_skill:diplomacy-=4 if target==15893 else 2
   return {**common,'character_id':target,'requested_skill':'diplomacy','requested_skill_enum':0,
    'game_version':'1.20.0.4','executable_sha256':EXE,'two_pass_stable':True,'callback_provenance':'exact4_native',
    'rite_id':16 if self.wrong_rite and target==OTHER else 15,'faith_id':51 if self.foreign_faith and target==OTHER else 50,
    'current_skill_points':dict(zip(A.SKILLS,(diplomacy,9,8,7,6,5))),
    'effective_devotion_level':level,'devotion_total_raw':40000000 if target==15893 else 20000000,
    'actual_skill_breakdown':'AUTHORED whole Faith aggregate, not selected site proof'+(' changed'if self.demoted and self.text_drift else''),
    'site_attribution_observed':self.claim_source,'selected_site_contribution_raw':None,'cache_generation_time_known':False}
  if tool==Q.DETAIL:
   cost=200000000 if self.quote_drift and self.reviews else 100000000
   return {**common,'requested_holy_site_id':26,'action':'demote','decision_key':'demote_holy_site_decision',
    'requested_decision_key':'demote_holy_site_decision','detail_actor_id':15893,'current_actor_id':15893,
    'parameter_holy_site_id':26,'selected_holy_site_id':26,'selected_item_token':3,'parameter_and_selection_match':True,
    'native_detail_context_verified':True,'normal_requirements_legality_observed':True,'normal_requirements_can_confirm':self.allowed,
    'native_can_confirm':self.allowed,'bypass_requirements_observed':True,'bypass_requirements_raw':0,
    'native_resource_quote_available':True,'native_resource_quote':{'raw_scale':100000,'resource_vector_raw':[0,0,cost,0,0,0,0,0,0,0],
     'costs_raw':{'gold':0,'prestige':0,'piety':cost,'treasury':0},'native_affordable':True},
    'native_requirements_description_available':True,'native_requirements_description':'AUTHORED original requirements',
    'native_cost_description_available':True,'native_cost_description':'AUTHORED 1000 Piety'}
  if tool=='ck3_query_ingame_ui_window_v1':return {'available':True,'effective_visible':True,'subject_id_available':True,'current_subject_id':26}
  return {**common,'invoked':tool==Q.CONFIRM,'business_outcome_observed':False}


class MeccaConsumers(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='MECCA-authored-',dir=Path(os.environ.get('XAR_CASE_TEST_SCRATCH_ROOT',str(HERE.parent))));cls.work=Path(cls.temp.name)
  cls.image=cls.work/'AUTHORED-not-game.png';cls.image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='))
  cls.receipt=cls.work/'AUTHORED-cohort.json';cls.receipt.write_text('{"scope":"AUTHORED not native qualification"}',encoding='utf-8')
  cls.original_constants=A.PROTECTED27
 @classmethod
 def tearDownClass(cls):A.PROTECTED27=cls.original_constants;cls.temp.cleanup()
 def setUp(self):self.created=[]
 def tearDown(self):
  # Only this test's resolved owned fixture directories, never a live ledger.
  for p in reversed(list(dict.fromkeys(self.created))):
   require_owned=p.resolve().is_relative_to(self.work.resolve())and p.resolve()!=self.work.resolve()and not p.is_symlink()
   if not require_owned:raise AssertionError('Fixture cleanup escaped owned temporary root')
   if p.exists():shutil.rmtree(p)
 def context(self,ledger=None,natural=False):
  out=self.work/('out-'+str(len(list(self.work.glob('out-*')))));out.mkdir()
  ledger=ledger or self.work/('ledger-'+out.name);ledger.mkdir(exist_ok=True)
  self.created.extend([out,ledger])
  scope={'machine_id':'4-8e1c2f1861','saved_sha256':A.SAVE['sha256'],'date_raw':A.SAVE['date_raw'],
   'played_character_id':A.SAVE['player_id'],'action':'demote','holy_site_id':27}
  protected=ledger/(A.digest(scope)+'.intent.json')
  if not protected.exists():protected.write_text(json.dumps({'scope':scope,'AUTHORED':True,'business_outcome_observed':False}),encoding='utf-8')
  protected_pin=A.pin(protected);A.PROTECTED27={k:protected_pin[k]for k in ('bytes','sha256')}
  c={'schema':'faith-e02-mecca-knight-controlled-case-v1','case':A.CASE,'product':A.PRODUCT,'machine_id':'4-8e1c2f1861',
   'saved_input':{'save':'AUTHORED-not-restored.ck3',**A.SAVE},'scope':A.SCOPE,'profile':{'enabled_mods':[],'product_files':[]},'max_public_calls':A.MAX_CALLS,
   'dependencies':[A.pin(p)for p in (A.__file__,Q.__file__,A.shared_opening_binding.__code__.co_filename,A.require_root_visual_review.__code__.co_filename)],
   'native_cohort':{'dll_sha256':'a'*64,'qualification_receipt':A.pin(self.receipt)},'intent_ledger_root':str(ledger),
   'protected_demote27_intent':protected_pin,'allow_natural_refresh':natural,'intent_review_after_utc':'2026-10-27T00:00:00Z'}
  return {'case_contract':c,'case_spec':{'required_mcp_tools':sorted(A.REQUIRED),'opt_in_read_only_mcp_tools':sorted(Q.READONLY),
   **{k:False for k in A.CLOSED},'whole_product_acceptance_credit':False,'business_contract_applicable':False,
   'budgets':{'hold_seconds':3600,'timeout':4500}},'product':A.PRODUCT,'case':A.CASE,'run_id':'AUTHORED-MECCA','output':str(out),
   'shared_source_root':str(ROOT),'case_inputs':{'intent_ledger_root':str(ledger)}}
 def run_one(self,c,context=None):
  context=context or self.context();out=Path(context['output']).resolve()
  def archive_sink(path,value):
   if Path(path).resolve().parent!=out:raise AssertionError('Authored archive sink escaped output root')
   json.dumps(value) # Archive IO seam only; all action/intent/fsync guards remain real.
  with patch.object(A,'write_once',side_effect=archive_sink):return A.run_case(context,c)
 def count(self,c,tool):return sum(s.get('tool')==tool for s in c.calls)
 def test_two_backed_knights_and_cost_post_are_observed_without_attribution(self):
  c=AuthoredPublicClient(self.image);r=self.run_one(c)
  self.assertEqual(self.count(c,Q.CONFIRM),1,r.get('failure'));self.assertEqual(r['status'],'GRADE_AND_TWO_KNIGHT_READBACK_OBSERVED_ATTRIBUTION_PENDING')
  self.assertEqual([p['unattributed_knight_effectiveness_delta_raw']for p in r['post_observation']['pairs']],[-4000,-4000])
  self.assertTrue(r['post_observation']['wallet_matches_original_quote']);self.assertFalse(r['site_attribution_observed'])
  self.assertIsNone(r['selected_site_contribution_raw']);self.assertFalse(r['required_slots']['E2-A1']['closed'])
  self.assertEqual(r['public_calls_used'],len(c.calls)+c.snapshot_calls)
 def test_unavailable_second_or_shared_fallback_never_confirms(self):
  for field in ('knight_unavailable','knight_shared_fallback','foreign_faith'):
   with self.subTest(field=field):
    c=AuthoredPublicClient(self.image);setattr(c,field,True);r=self.run_one(c)
    self.assertEqual(self.count(c,Q.CONFIRM),0,r.get('failure'))
 def test_typed_knight_schema_scale_full_target_and_native_revision_guards(self):
  c=AuthoredPublicClient(self.image);v=c.response(Q.KNIGHT,{'character_id':15893})
  A.knight(v,15893,15893,51394920)
  for changes in ({'schema':'wrong'},{'backend_id':'wrong'},{'character_id':OTHER},{'raw_scale':True},
    {'snapshot_revision':True},{'queried_native_revision':5}):
   with self.subTest(changes=changes),self.assertRaises(ValueError):A.knight({**v,**changes},15893,15893,51394920)
 def test_each_own_rite_may_differ_and_is_independently_stable(self):
  c=AuthoredPublicClient(self.image);c.wrong_rite=True;r=self.run_one(c)
  self.assertEqual(self.count(c,Q.CONFIRM),1,r.get('failure'));self.assertTrue(all(x['own_identity_and_level_stable']for x in r['post_observation']['pairs']))
 def test_changed_knight_after_review_or_quote_denial_never_confirms(self):
  for field in ('knight_quote_drift','quote_drift','denied'):
   with self.subTest(field=field):
    c=AuthoredPublicClient(self.image);setattr(c,field,True);r=self.run_one(c);self.assertEqual(self.count(c,Q.CONFIRM),0,r.get('failure'))
 def test_native_ordinary_legality_false_never_confirms(self):
  c=AuthoredPublicClient(self.image);c.allowed=False;r=self.run_one(c);self.assertEqual(self.count(c,Q.CONFIRM),0)
 def test_unknown_ack_keeps_independent_post_no_repeat_or_day(self):
  c=AuthoredPublicClient(self.image);c.lost_ack=True;c.natural_allowed=True;r=self.run_one(c,self.context(natural=True))
  self.assertEqual(self.count(c,Q.CONFIRM),1);self.assertTrue(r['transport_outcome_unknown']);self.assertEqual(c.day_calls,0)
  self.assertTrue(r['post_observation']['only_selected_major_relation_changed'])
 def test_original27_remains_and_new26_claim_fixed_to_mother_date(self):
  context=self.context();protected=Path(context['case_contract']['protected_demote27_intent']['path']);before=protected.read_bytes()
  c=AuthoredPublicClient(self.image);r=self.run_one(c,context);self.assertEqual(protected.read_bytes(),before)
  scope=A.read(r['consumed_intent']['path'])['scope'];self.assertEqual(scope['holy_site_id'],26);self.assertEqual(scope['date_raw'],A.SAVE['date_raw'])
  self.assertEqual(Path(r['consumed_intent']['path']).parent,protected.parent)
 def test_consumed26_blocks_new_run_and_even_different_prior_date(self):
  first=self.context();ledger=Path(first['case_contract']['intent_ledger_root']);scope={'machine_id':'4-8e1c2f1861','saved_sha256':A.SAVE['sha256'],
   'date_raw':A.SAVE['date_raw']+24,'played_character_id':15893,'action':'demote','holy_site_id':26}
  (ledger/(A.digest(scope)+'.intent.json')).write_text(json.dumps({'scope':scope,'business_outcome_observed':False}),encoding='utf-8')
  c=AuthoredPublicClient(self.image);r=self.run_one(c,first)
  self.assertEqual(self.count(c,Q.CONFIRM),0);self.assertTrue(r['transport_outcome_unknown']);self.assertIsNotNone(r['historical_consumed_intent_blocked'])
 def test_cannot_move_ledger_root_or_replace_original27_pin(self):
  context=self.context();moved=self.work/'wrong-ledger';moved.mkdir();context['case_contract']['intent_ledger_root']=str(moved);context['case_inputs']['intent_ledger_root']=str(moved)
  with self.assertRaises(ValueError):A.validate_contract(context)
  context=self.context();context['case_contract']['protected_demote27_intent']['sha256']='b'*64
  with self.assertRaises(ValueError):A.validate_contract(context)
 def test_failed_fsync_retains_new26_claim_and_never_confirms(self):
  context=self.context();c=AuthoredPublicClient(self.image)
  with patch.object(A.os,'fsync',side_effect=OSError('AUTHORED fsync failure')):r=self.run_one(c,context)
  self.assertEqual(self.count(c,Q.CONFIRM),0);self.assertEqual(r['world_confirm_attempts'],0)
  self.assertEqual(len(list(Path(context['case_contract']['intent_ledger_root']).glob('*.intent.json'))),2)
 def test_after_only_rows_keep_counted_independent_action_preframes(self):
  c=AuthoredPublicClient(self.image);r=self.run_one(c)
  self.assertEqual(self.count(c,Q.CONFIRM),1);self.assertTrue(all('before_snapshot'not in row['row']for row in r['submitted_rows']))
  acts=[x for x in r['submitted_rows']if x['step']['tool']in Q.PRESENT|{Q.CONFIRM}]
  self.assertTrue(all(isinstance(x.get('independent_before_snapshot'),dict)for x in acts))
 def test_explicit_natural_scope_three_actual_days_no_world_replay(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;r=self.run_one(c,self.context(natural=True))
  self.assertEqual(self.count(c,Q.CONFIRM),1,r.get('failure'));self.assertEqual(c.day_calls,3,r.get('failure'))
  self.assertEqual(r['actual_advanced_hours'],72);self.assertFalse(r['natural_day_transport_unknown']);self.assertFalse(r['required_slots']['E2-A1']['closed'])
  rows=r['natural_refresh_observations'];self.assertEqual([x['actual_elapsed_hours']for x in rows],[24,24,24]);self.assertEqual(len({x['claim']['path']for x in rows}),3)
  self.assertEqual(r['public_calls_used'],len(c.calls)+c.snapshot_calls)
 def test_natural_phase_never_implicit_and_no_monthly_or_L_inference(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;r=self.run_one(c)
  self.assertEqual(c.day_calls,0);self.assertEqual(r['actual_advanced_hours'],0)
  self.assertTrue(all(p['diplomacy_or_level_inferred_from_Knight']is False and p['piety_level_impact_observed']is False for p in r['post_observation']['pairs']))
 def test_unknown_day_keeps_independent_after_and_never_replays(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;c.day_unknown=True
  r=self.run_one(c,self.context(natural=True));self.assertEqual(c.day_calls,1,r.get('failure'));self.assertEqual(self.count(c,Q.CONFIRM),1)
  self.assertTrue(r['natural_day_transport_unknown']);self.assertEqual(r['actual_advanced_hours'],24)
  self.assertIn('knights',r['natural_refresh_observations'][0]['independent_after_on_unknown'])
 def test_thrown_day_timeout_keeps_real_independent_after_without_replay(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;c.day_raises=True;c.day_elapsed=25
  r=self.run_one(c,self.context(natural=True));self.assertEqual(c.day_calls,1,r.get('failure'));self.assertEqual(self.count(c,Q.CONFIRM),1)
  self.assertTrue(r['natural_day_transport_unknown']);self.assertEqual(r['actual_advanced_hours'],25)
  row=r['natural_refresh_observations'][0];self.assertNotIn('row',row)
  self.assertIn('TimeoutError',row['execution_exception']);self.assertIn('TimeoutError',r['failure'])
  self.assertEqual(row['unknown_post_status'],'INDEPENDENT_READ_OBSERVED_TRANSPORT_STILL_UNKNOWN')
  self.assertEqual(row['independent_after_snapshot_on_unknown']['date_raw'],51394945)
  self.assertEqual(row['actual_elapsed_hours'],25);self.assertEqual(len(row['independent_after_on_unknown']['knights']),2)
  self.assertTrue(row['independent_after_on_unknown']['selected_relic_identity_and_actor_controls_stable'])
  self.assertTrue(Path(row['claim']['path']).is_file());self.assertEqual(r['public_calls_used'],len(c.calls)+c.snapshot_calls)
 def test_actual25_hour_reads_are_valid_and_remaining22_prevents_third_request(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;c.day_elapsed=25
  r=self.run_one(c,self.context(natural=True));self.assertEqual(c.day_calls,2,r.get('failure'))
  self.assertEqual(r['actual_advanced_hours'],50);self.assertTrue(r['natural_remaining_actual_hours_below_one_day'])
  self.assertFalse(r['natural_day_transport_unknown']);self.assertFalse(r['actual_time_budget_exceeded'])
  self.assertTrue(all(x['actual_post_observation']['selected_relic_identity_and_actor_controls_stable']for x in r['natural_refresh_observations']))
 def test_actual_horizon_exceed_preserves_typed_read_and_honest_budget_diagnostic(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;c.day_elapsed=80
  r=self.run_one(c,self.context(natural=True));self.assertEqual(c.day_calls,1,r.get('failure'))
  self.assertEqual(r['actual_advanced_hours'],80);self.assertTrue(r['actual_time_budget_exceeded'])
  self.assertFalse(r['natural_day_transport_unknown']);self.assertIn('knights',r['natural_refresh_observations'][0]['actual_post_observation'])
  self.assertEqual(self.count(c,Q.CONFIRM),1);self.assertFalse(r['required_slots']['E2-A1']['closed'])
 def test_natural_own_level_drift_stops_with_actual_observation_retained(self):
  c=AuthoredPublicClient(self.image);c.natural_allowed=True;c.stale_knight=True;c.day_level_drift=True;r=self.run_one(c,self.context(natural=True))
  self.assertEqual(c.day_calls,1,r.get('failure'));self.assertEqual(self.count(c,Q.CONFIRM),1)
  self.assertFalse(r['natural_refresh_observations'][0]['actual_post_observation']['selected_relic_identity_and_actor_controls_stable'])
 def test_one_fixed26_or_one_explicit_day_only_and_no_public_raw_action(self):
  good=Q.step('one',Q.CONFIRM,{'action':'demote','holy_site_id':26});Q.validate({'steps':[good]})
  day={'id':'day','kind':'advance_day','days':1,'allow_event_boundary':True,'allow_actor_change':False,'timeout':60,'continue_on_error':True};Q.validate({'steps':[day]})
  for bad in ({**good,'args':{'action':'demote','holy_site_id':27}},{**good,'fresh_revision':False},
   {**good,'tool':'ck3_execute_step','args':{'step':'resume-map'}},{**day,'days':True},{**day,'days':2},{**day,'allow_actor_change':True}):
   with self.subTest(bad=bad),self.assertRaises(ValueError):Q.validate({'steps':[bad]})
  with self.assertRaises(ValueError):Q.validate({'steps':[day,day]})
 def test_declared_tools_exact_and_manual_normal_quit_unchanged(self):
  self.assertEqual(len(A.REQUIRED),23);self.assertEqual(len(Q.READONLY),7)
  context=self.context();context['case_spec']['required_mcp_tools'].remove(Q.KNIGHT)
  with self.assertRaises(ValueError):A.validate_contract(context)
  c=AuthoredPublicClient(self.image);c.selection=SimpleNamespace(normal_quit_automation={'AUTHORED':'forbidden'})
  with self.assertRaises(ValueError):self.run_one(c)
if __name__=='__main__':unittest.main(verbosity=2)
