"""Portable pure regression entry for the strict same-owner rejection diagnostic.

Extract only two pure functions from the checked-in host; never import its live
runtime or require CK3, MCP, external B directories, a process, or a saved game.
"""
import ast
import json
from pathlib import Path
import unittest

PACKAGE=Path(__file__).resolve().parents[2]
HOST=PACKAGE/'native_bridge/research/run_ck3_12002_mcp_live.py'
BASELINE=Path(__file__).parent/'fixtures/campaign_pause_same_owner_guard_before_diagnostic.py'
MESSAGE='campaign pause readback lost the complete same-owner frame'

def load_pure(tree,names):
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 namespace={}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'extracted-pure-pause-guard','exec'),namespace)
 return namespace['campaign_pause_frame_binding']

original_tree=ast.parse(BASELINE.read_text(encoding='utf-8'))
candidate_tree=ast.parse(HOST.read_text(encoding='utf-8'))
original_function=next(n for n in original_tree.body if isinstance(n,ast.FunctionDef) and n.name=='campaign_pause_frame_binding')
candidate_function=next(n for n in candidate_tree.body if isinstance(n,ast.FunctionDef) and n.name=='campaign_pause_frame_binding')
original_guard=next(n for n in ast.walk(original_function) if isinstance(n,ast.If) and len(n.body)==1
 and isinstance(n.body[0],ast.Raise) and isinstance(n.body[0].exc,ast.Call)
 and n.body[0].exc.args and isinstance(n.body[0].exc.args[0],ast.Constant) and n.body[0].exc.args[0].value==MESSAGE)
if not any(isinstance(n,ast.If) and ast.dump(n.test)==ast.dump(original_guard.test) for n in ast.walk(candidate_function)):
 raise RuntimeError('Original same-owner strict guard Boolean AST changed')
old_guard=load_pure(original_tree,{'campaign_pause_frame_binding'})
new_guard=load_pure(candidate_tree,{'campaign_pause_frame_binding','_campaign_pause_frame_rejection_detail'})

def fixture():
 return {'episode_projection':'native_campaign','backend_id':'native-headless','source':'injected-dll-named-pipe','map_ready':True,
 'format_version':1,'complete_snapshot':True,'paused':True,'played_character':{'character_id':29829,'alive':True},
 'active_event':None,'one_life_terminal_reason':None,'snapshot_id':'native:2','native_revision':2,'revision':3,
 'date_raw':53144712,'local_player_id':0,'speed':1,'diagnostics':{'connected':True,'semantic_state_available':True,
 'last_error':None,'transport_fatal_error':None,'bridge_pid':100,'connection_generation':1,'rejected_state_snapshot_count':0,'pipe_name':'synthetic-only',
 'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':'98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518','game_adapter_id':'ck3-1.20.0.4-msvc-x64','ck3_build_match':True,'connection_generation':1,'pid':100},
 'last_heartbeat':{'pid':100,'main_thread_query_mailbox_v1':{'owner_tid':22,'current_tid':22,'owner_verified_pump_epochs':10,
 'installed':True,'ready':True,'stop':False,'failure':0,'stamp_read_success':True,'date_raw':53144712,
 'application_main_observed':True,'paused':True,'paused_main_thread_observed':True,'consecutive_verified':2}}}}

class Focused(unittest.TestCase):
 def test_valid_paused_and_running_results_unchanged(self):
  row=fixture();self.assertEqual(old_guard(row),new_guard(row))
  row['paused']=False;m=row['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1'];m.update(ready=False,paused=False,paused_main_thread_observed=False,consecutive_verified=0)
  self.assertEqual(old_guard(row,allow_running=True),new_guard(row,allow_running=True))
 def diagnostic(self,row,token):
  with self.assertRaises(RuntimeError) as old:old_guard(row)
  with self.assertRaises(RuntimeError) as new:new_guard(row)
  self.assertEqual(type(old.exception),type(new.exception));self.assertEqual(str(old.exception),str(new.exception));self.assertEqual(str(new.exception),MESSAGE)
  detail=new.exception.ck3_campaign_pause_frame_diagnostic
  first=detail['conditions'][detail['first_failed_condition']]
  self.assertTrue(first['failed']);self.assertIn(token,first['source']);self.assertFalse(detail['additional_snapshot_or_RPC_or_retry']);self.assertFalse(detail['business_credit'])
  self.assertLess(len(json.dumps(detail)),16384)
  return detail
 def test_date_mismatch_remains_rejected_and_identified(self):
  row=fixture();row['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['date_raw']+=24
  self.diagnostic(row,"mailbox[\"date_raw\"]")
 def test_foreign_tid_remains_rejected(self):
  row=fixture();row['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['current_tid']=23
  self.diagnostic(row,"current_tid")
 def test_missing_pid_preserves_first_failure_and_unknown_later_value(self):
  row=fixture();del row['diagnostics']['hello']['pid']
  detail=self.diagnostic(row,'hello.get("pid")')
  self.assertIsNone(detail['observations']['hello.pid']['value']);self.assertFalse(detail['observations']['hello.pid']['present'])
  self.assertTrue(any(c['unavailable_reason']=='KeyError' and c['failed'] is None for c in detail['conditions']))
 def test_lost_semantic_state_not_relaxed(self):
  row=fixture();row['diagnostics']['semantic_state_available']=False
  self.diagnostic(row,'semantic_state_available')
 def test_earlier_build_guard_remains_original_no_new_diagnostic(self):
  row=fixture();row['diagnostics']['hello']['ck3_build_match']=False
  with self.assertRaises(RuntimeError) as old:old_guard(row)
  with self.assertRaises(RuntimeError) as new:new_guard(row)
  self.assertEqual(str(old.exception),str(new.exception));self.assertFalse(hasattr(new.exception,'ck3_campaign_pause_frame_diagnostic'))

if __name__=='__main__':
 unittest.main()
