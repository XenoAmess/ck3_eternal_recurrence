"""Offline tests of new public wiring only; no provider/DLL/game invocation."""
from pathlib import Path
import ast,copy,importlib.util,json,sys,tempfile,types,unittest
import argparse
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--support-repo',type=Path,default=Path(__file__).resolve().parents[1])
options,remaining=parser.parse_known_args()
MAIN=options.support_repo
sys.path.insert(0,str(MAIN/'tools'))
import ck3_mod_acceptance_appointment as a
import ck3_mod_acceptance_client as clientmod
from ck3_mod_acceptance_cases import xqol_government_adapter as gov

LAW='celestial_appointment_succession_law'
def frame():
 return {'source':'injected-dll-named-pipe','backend_id':'native-headless','map_ready':True,'paused':True,
  'episode_projection':'native_campaign','native_revision':9,'date_raw':8000,'episode_run_id':'offline-test',
  'played_character':{'character_id':101,'alive':True,'source':'native'},'diagnostics':{'bridge_pid':1001,
  'connection_generation':4,'pipe_name':'test-only','hello':{'bridge_pid':1001,'connection_generation':4,
  'game_version':'1.20.0.4','executable_sha256':a.EXE_SHA}}}
def row(offset=0,end=2,count=2,score=120000,breakdown=101):
 f=frame();cs=[{'character_id':101+i,'list_index':i,'native_rank':i+1,'score_present':True,
  'score_raw':score if i==0 else 500000,'alive':True,'is_human_player':i==0,'is_ai':i!=0,'candidate_pool_member':True}
  for i in range(offset,end)]
 v={'schema':'ck3-current-title-appointment-v1','available':True,'requested_title_id':14770,
  'requested_holder_character_id':201,'native_group_branch':'character_1c0','group_first_title_id':990,
  'resolved_title_id':990,'current_window_title_id':990,'requested_resolves_to_current':True,
  'current_holder_character_id':201,'current_title_key':'k_liangzhe','resolved_title_key':'k_liangzhe',
  'effective_succession_law_key':LAW,'full_candidate_count':count,'source_pool_count':count,
  'candidate_offset':offset,'next_offset':end,'pool_consistency_token':'fnv1a64:0123456789abcdef',
  'score_fixed_point_scale':100000,'candidate_scope':a.SCOPE,'ai_control_available':True,'candidates':cs,
  'breakdown_character_id':breakdown or 0,'breakdown_getter_invoked':bool(breakdown),
  'breakdown_cache_refresh_only':True,'breakdown_available':bool(breakdown),
  'breakdown':{'value_raw':score,'children':[]} if breakdown else None}
 raw={'schema':'ck3-ingame-ui-window-v1','accepted':True,'available':True,'status':'observed',
  'window_kind':'title_appointment','window_name':'title_appointment','window_exists':True,'effective_visible':True,
  'enabled':True,'dispatch_invoked':False,'verification_pending':False,'paused':True,'played_character_id':101,
  'native_revision':9,'queried_native_revision':9,'date_raw':8000,'queried_connection_generation':4,
  'episode_run_id':'offline-test','application_owner_thread_verified':True,'gui_owner_binding_verified':True,
  'game_version':'1.20.0.4','executable_sha256':a.EXE_SHA,'current_subject_id':990,'owner_character_id':201,
  'title_appointment':v}
 return {'id':'offline-page-'+str(offset),'ok':True,'finished_at':'offline-only','error':None,'result':raw,'after_snapshot':f}
def join(rows,breakdown=101):
 return a.join_pages(rows,frame(),requested_title_id=14770,requested_title_key='d_zhexi',expected_law=LAW,
                     breakdown_character_id=breakdown)
def nav():
 return {'id':'offline-navigation','ok':True,'finished_at':'offline-only','error':None,'after_snapshot':frame(),
  'result':{'accepted':True,'step':'center-map-on-landed-title-v1','status':'centered',
   'title':{'title_id':14770,'key':'d_zhexi'},'binding':{'bridge_pid':1001,'connection_generation':4,
   'played_character_id':101,'date_raw':8000,'native_revision':9}}}

class Wiring(unittest.TestCase):
 def test_real_requested_d_resolves_to_actual_k(self):
  p=join([row()]);o={'requested_title_id':14770,'requested_title_key':'d_zhexi','title_id':990,
   'title_key':'k_liangzhe','law':LAW}
  a.bind_observation(o,p,requested_key='d_zhexi',law=LAW)
  self.assertEqual(o['native_title_normalization']['requested_title_id'],14770)
  self.assertEqual(o['native_title_normalization']['current_window_title_id'],990)
  self.assertEqual(a.target_score(p,101,1.2),120000)
  o['title_key']='d_zhexi'
  with self.assertRaises(ValueError):a.bind_observation(o,p)
 def test_input_must_have_independent_current_typed_navigation(self):
  self.assertEqual(a.navigation_anchor(nav(),frame(),14770,'d_zhexi')['step_id'],'offline-navigation')
  for field,value in [('title_id',990),('key','k_liangzhe')]:
   n=nav();n['result']['title'][field]=value
   with self.assertRaises(ValueError):a.navigation_anchor(n,frame(),14770,'d_zhexi')
 def test_every_page_must_keep_scene_and_scope(self):
  for path,value in [(('after_snapshot','diagnostics','bridge_pid'),1002),
   (('after_snapshot','diagnostics','connection_generation'),5),
   (('after_snapshot','date_raw'),8001),(('after_snapshot','paused'),False),
   (('result','title_appointment','pool_consistency_token'),'fnv1a64:fedcba9876543210'),
   (('result','title_appointment','effective_succession_law_key'),'other_law'),
   (('result','title_appointment','current_window_title_id'),991),
   (('result','title_appointment','requested_resolves_to_current'),False),
   (('result','title_appointment','full_candidate_count'),3)]:
   with self.subTest(path=path):
    rows=[row(0,1),row(1,2)];node=rows[1]
    for key in path[:-1]:node=node[key]
    node[path[-1]]=value
    with self.assertRaises(ValueError):join(rows)
 def test_truncated_duplicate_skipped_pool_rejected(self):
  for rows in [[row(0,1)],[row(1,2)],[row(0,1),row(0,1)]]:
   with self.assertRaises(ValueError):join(rows)
  rows=[row(0,1),row(1,2)];rows[1]['result']['title_appointment']['candidates'][0]['character_id']=101
  with self.assertRaises(ValueError):join(rows)
 def test_eligibility_comes_from_filtered_engine_pool_never_score(self):
  r=row(breakdown=None);c=r['result']['title_appointment']['candidates'][0]
  c['native_rank']=-1;c['score_present']=False;c['score_raw']=0
  p=join([r],None)
  self.assertTrue(p['candidates'][0]['eligible'])
  self.assertTrue(p['eligibility_provenance']['score_present_is_not_eligibility'])
  with self.assertRaises(ValueError):a.target_score(p,101)
  c['alive']=False
  with self.assertRaises(ValueError):join([r],None)
 def test_manual_candidate_eligibility_or_ai_cannot_override_native(self):
  p=join([row()]);o={'requested_title_id':14770,'requested_title_key':'d_zhexi','title_id':990,
   'title_key':'k_liangzhe','law':LAW,'candidates':copy.deepcopy(p['candidates'])}
  o['candidates'][1]['is_ai']=False
  with self.assertRaises(ValueError):a.bind_observation(o,p)
 def test_breakdown_and_exact_fixed_point_score_required(self):
  r=row();r['result']['title_appointment']['breakdown']['value_raw']=120001
  with self.assertRaises(ValueError):join([r])
  with self.assertRaises(ValueError):a.target_score(join([row()]),101,1.20001)
 def test_public_collector_fetches_and_preserves_complete_two_pages(self):
  with tempfile.TemporaryDirectory() as tmp:
   c=object.__new__(clientmod.CaseClient);c.output=Path(tmp);c._seq=0;c.frozen={'run_id':'offline-run'}
   c.selection=types.SimpleNamespace(case={'id':'ui_tail','required_mcp_tools':[a.TOOL],'opt_in_read_only_mcp_tools':[a.TOOL]})
   c._process={'pid':1001,'create_time':123.0,'retained_synchronize_query_handle_acquired':True}
   c.guard=lambda *x,**kw:None;c.snapshot=lambda:frame();c.validate_frame=lambda f:f
   c.read_report=lambda:{'steps':[nav()]};calls=[]
   def execute(steps,name):
    s=steps[0];calls.append(s)
    if s['tool']=='ck3_query_title_holder_v1':
     return [{'result':{'title_holder':{'available':True,'title_key_available':True,'title_id':14770,
      'title_key':'d_zhexi','holder_character_id':201,'actor_character_id':101,'date_raw':8000}},'after_snapshot':frame()}]
    start=s['args']['candidate_offset'];r=row(start,min(65,start+64),65);r['id']=s['id'];return [r]
   c.execute_plan=execute
   result=c.query_appointment_pool(requested_title_id=14770,requested_title_key='d_zhexi',expected_law=LAW,
    navigation_step_id='offline-navigation',breakdown_character_id=101)
   self.assertEqual(len(result['proof']['candidates']),65)
   self.assertEqual([s['args'].get('candidate_offset') for s in calls[1:]],[0,64])
   self.assertEqual(c.appointment_receipt(result['appointment_pool'],frame()),result['proof'])
   bad=copy.deepcopy(result['appointment_pool']);bad['sha256']='0'*64
   with self.assertRaises(ValueError):c.appointment_receipt(bad)
   c.selection.case['id']='prison_payment'
   with self.assertRaises(ValueError):c.query_appointment_pool(requested_title_id=14770,requested_title_key='d_zhexi',
    expected_law=LAW,navigation_step_id='offline-navigation')
 def test_government_exact_million_actual_ai_and_successor_still_required(self):
  pools={phase:join([row(score=score)]) for phase,score in [('off',120000),('on',120000-100000000000),('restored',120000)]}
  slot={'requested_title_id':14770,'requested_title_key':'d_zhexi','title_id':990,'title_key':'k_liangzhe',
   'law':LAW,'appointment_pool_off':'off','appointment_pool_on':'on','appointment_pool_restored':'restored',
   'score_off':1.2,'score_on':-999998.8,'score_restored':1.2,'direct_original_review':True,
   'full_candidates_reviewed':True,'eligibility_and_score_breakdown_reviewed':True,
   'independent_human_candidate':True,'auto_appointment_enabled_off':False,'auto_appointment_enabled_on':True,
   'auto_appointment_enabled_restored_score':False,'original_switch_enabled':True,'original_switch_restored':True,
   'final_switch_enabled':True,'chosen_character_id':102,'actual_successor_character_id':102,'native_appointment_confirmed':True}
  c=types.SimpleNamespace(appointment_receipt=lambda ref,*args,**kw:pools[ref]);contract={'appointment_laws':[LAW]}
  self.assertTrue(gov.verify_native_slots(c,[slot],contract,101,frame()))
  self.assertTrue(gov.verify_slots([slot],contract,101))
  for key,value in [('actual_successor_character_id',999),('chosen_character_id',101),('original_switch_restored',False)]:
   bad=copy.deepcopy(slot);bad[key]=value
   with self.assertRaises(ValueError):gov.verify_slots([bad],contract,101)
 def test_checkpoint_readonly_action_served_once_with_no_gui_action(self):
  with tempfile.TemporaryDirectory() as tmp:
   c=object.__new__(clientmod.CaseClient);c.output=Path(tmp);c.frozen={'run_id':'offline-run'}
   c.operator_reviewer='/root/operator';c._hold=1234;c.remaining=lambda:200;c.guard=lambda *a,**k:None
   c.selection=types.SimpleNamespace(case={'id':'administrative_appointments','opt_in_read_only_mcp_tools':[a.TOOL]})
   args={'requested_title_id':14770,'requested_title_key':'d_zhexi','expected_law':LAW,'navigation_step_id':'offline-navigation'}
   action={'action':'appointment-full-pool','run_id':'offline-run','reviewer':'/root/operator','sequence':0,'arguments':args}
   (Path(tmp)/'test-readonly-request-0000.json').write_text(json.dumps(action),encoding='utf-8')
   (Path(tmp)/'test-root-result.json').write_text(json.dumps({'run_id':'offline-run','reviewer':'/root/operator'}),encoding='utf-8')
   calls=[];c.query_appointment_pool=lambda **kw:calls.append(kw) or {'business_acceptance':'NOT_ASSESSED'}
   c.root_checkpoint('test',{},read_only_appointment=True)
   self.assertEqual(calls,[args]);self.assertTrue((Path(tmp)/'test-readonly-0000-once-intent.json').exists())
   self.assertEqual(json.loads((Path(tmp)/'test-readonly-response-0000.json').read_text())['business_acceptance'],'NOT_ASSESSED')

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*remaining],verbosity=2)
