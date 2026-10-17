"""Actual617 + actual1779 through real transport/normalizer/planner, fake Native I/O."""
from copy import deepcopy
from pathlib import Path
import json
import threading
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parents[1] / 'fixtures'
from xar_autoplayer.bridge import war_declared_overview_transport as t
from xar_autoplayer.bridge import war_declared_overview_contract as c
from xar_autoplayer.ordinary_war_declared_overview_v1 import plan_ordinary_war_declared_overview_v1 as plan
fixture=json.loads((HERE/'p43_close_later_query_projection.json').read_bytes())
OLD=fixture['original_close'];SEM=fixture['later_semantic'];QUERY=fixture['later_query']

class Driver:
    def __init__(self):
        self._driver_state_lock=threading.RLock()
        self._war_declared_overview_attempt=0
        self._war_declared_overview_close_pending=None
        self._war_declared_overview_query_attempt=None
        self._war_declared_overview_observation=None
        self.command_timeout_seconds=.1
        self.sent=[];self.recorded=[]
        self.snapshot=deepcopy(SEM)
        self.reply=deepcopy(QUERY)
        self.endpoint=SimpleNamespace(send=self.send)
        self.state=SimpleNamespace(capabilities=lambda:{'bridge_capabilities':[c.QUERY_CAPABILITY,c.CLOSE_CAPABILITY]},wait_for_command_result=self.wait)
    def send(self,request): self.sent.append(request)
    def wait(self,rid,timeout):
        z=deepcopy(self.reply)
        receipt=z['native_command_result'][c.OWNER_RECEIPT_KEY]
        leaf={k:z[k] for k in c._CLOSE_TRACE_FIELDS}
        leaf['request_id']=rid;receipt['request_id']=rid
        return dict(type='command_result',protocol_version=1,request_id=rid,ok=True,result=leaf,**{c.OWNER_RECEIPT_KEY:receipt})
    def take_internal_semantic_snapshot(self): return deepcopy(self.snapshot)
    def _record_command(self,*a,**kw): self.recorded.append((a,kw))

def prior(driver,old=OLD):
    old=deepcopy(old)
    binding={v:old[k] for k,v in c.LEASE_KEYS.items()}
    driver._war_declared_overview_close_pending=dict(native_request_id=old['native_request_id'],step=c.CLOSE_STEP,
        status=old['status'],error=old['unavailable_reason'],binding=binding,native_generation=5,collectable=False,
        completed_response=old,**{k:old[k] for k in c.LEASE_KEYS})

def decide(driver):
    snap=deepcopy(driver.snapshot)
    snap.update(t.war_declared_overview_snapshot_fields(driver,snap))
    return plan(snap,action_steps=[c.QUERY_STEP,c.CLOSE_STEP],bridge_capabilities=[c.QUERY_CAPABILITY,c.CLOSE_CAPABILITY])

class Tests(unittest.TestCase):
    def test_actual_close_execute_stores_completion_before_later_query(self):
        d=Driver();d.reply=deepcopy(OLD)
        for k,v in c.LEASE_KEYS.items():
            if v=='actor_character_id': d.snapshot['played_character']['character_id']=OLD[k]
            elif v=='connection_generation':
                d.snapshot['diagnostics']['connection_generation']=OLD[k]
                d.snapshot['diagnostics']['hello']['connection_generation']=OLD[k]
            else: d.snapshot[v]=OLD[k]
        original=t.execute_war_declared_overview_v1(d,operation='close',expected_revision=631)
        self.assertEqual(original['status'],'verification_pending')
        self.assertIn('completed_response',d._war_declared_overview_close_pending)
        sent_close=d.sent[-1]['request_id']
        d.snapshot=deepcopy(SEM);d.reply=deepcopy(QUERY)
        result=t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
        self.assertIsNone(d._war_declared_overview_close_pending)
        self.assertEqual(result['prior_close_execution_observation']['native_request_id'],sent_close)
        self.assertEqual([x['step'] for x in d.sent],[c.CLOSE_STEP,c.QUERY_STEP])
    def test_normal_query_without_pending_is_unchanged(self):
        d=Driver()
        z=t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
        self.assertNotIn('prior_close_execution_observation',z)
        self.assertEqual(decide(d)['selected_step'],c.CLOSE_STEP)
    def test_actual_later_visible_rearms_current_intent(self):
        d=Driver();prior(d)
        result=t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
        self.assertIsNone(d._war_declared_overview_close_pending)
        self.assertEqual(decide(d)['selected_step'],c.CLOSE_STEP)
        self.assertFalse(result['prior_close_execution_observation']['close_action_credit'])
        self.assertEqual([x['step'] for x in d.sent],[c.QUERY_STEP])
        self.assertNotEqual(d.sent[0]['request_id'],OLD['native_request_id'])
    def test_later_absent_or_hidden_sends_no_close(self):
        for presence in ['absent','hidden']:
            with self.subTest(presence=presence):
                d=Driver();prior(d);z=d.reply
                z.update(status=presence,window_present=presence=='hidden',effective_visible=False,
                    post_window_present=presence=='hidden',post_effective_visible=False,
                    root_observation_source='guarded_top_level_and_complete_owner_tree',
                    post_observation_source='guarded_top_level_and_complete_owner_tree')
                t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
                self.assertIsNone(d._war_declared_overview_close_pending);self.assertIsNone(decide(d))
                self.assertEqual([x['step'] for x in d.sent],[c.QUERY_STEP])
    def test_same_native_frame_visible_is_deferred_not_a_close_loop(self):
        d=Driver();old=deepcopy(OLD)
        for k in c.LEASE_KEYS: old[k]=QUERY[k]
        old.update(native_revision=QUERY['native_revision'],date_raw=QUERY['date_raw'])
        old['native_command_result'][c.OWNER_RECEIPT_KEY]['date_raw']=QUERY['date_raw']
        prior(d,old)
        result=t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
        self.assertTrue(result['close_retry_deferred_for_native_frame']);self.assertIsNone(decide(d))
    def test_unknown_or_incomplete_original_stays_pending(self):
        for field,value in [('completed_response',None),('collectable',True),('native_generation',6)]:
            with self.subTest(field=field):
                d=Driver();prior(d);d._war_declared_overview_close_pending[field]=value
                t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
                self.assertIsNotNone(d._war_declared_overview_close_pending)
    def test_old_owner_pump_or_foreign_scope_cannot_retire(self):
        for mutation in ['oldpump','oldticket','thread','actor','episode','connection','backdate']:
            with self.subTest(mutation=mutation):
                d=Driver();prior(d)
                old=d._war_declared_overview_close_pending['completed_response']
                if mutation=='oldpump': old['native_command_result'][c.OWNER_RECEIPT_KEY]['pump_epoch']=QUERY['pump_epoch']
                elif mutation=='oldticket': old['native_command_result'][c.OWNER_RECEIPT_KEY]['ticket_sequence']=QUERY['ticket_sequence']
                elif mutation=='thread': old['native_command_result'][c.OWNER_RECEIPT_KEY]['thread_id']+=1
                elif mutation=='actor': old['queried_actor_character_id']+=1
                elif mutation=='episode': old['queried_episode_run_id']='foreign'
                elif mutation=='connection': old['queried_connection_generation']+=1
                else: d._war_declared_overview_close_pending['binding']['date_raw']=QUERY['date_raw']+24
                t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
                self.assertIsNotNone(d._war_declared_overview_close_pending)
    def test_bad_query_is_rejected_by_real_contract(self):
        for key,value in [('scope_unchanged',False),('post_observed',False),('played_character_id',3)]:
            with self.subTest(key=key):
                d=Driver();prior(d);d.reply[key]=value
                with self.assertRaises(t.BridgeUnavailableError):
                    t.execute_war_declared_overview_v1(d,operation='query',expected_revision=1882)
                self.assertIsNotNone(d._war_declared_overview_close_pending)

if __name__=='__main__': unittest.main()
