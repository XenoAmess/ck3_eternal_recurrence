"""Known actual 812/814/816 DTOs through real transport and ordinary planner.

Only the Native endpoint is fake. Subsequent visible-window and scope-transition
variants are explicitly synthetic; they are not new Game observations.
"""
from copy import deepcopy
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

PACK=Path(__file__).resolve().parents[1] / 'fixtures'
from xar_autoplayer.bridge import war_results_window_transport as new
from xar_autoplayer.bridge import war_results_window_contract as c
from xar_autoplayer import ordinary_war_results_window_v1 as newplan

fixture=json.loads((PACK/'p41_results_close_query_projection.json').read_bytes())
CLOSE=fixture['rows']['814']['result'];VISIBLE=fixture['rows']['812']['result'];HIDDEN=fixture['rows']['816']['result']

def snapshot(z):
    return dict(snapshot_id=z['queried_snapshot_id'],revision=z['queried_revision'],native_revision=z['queried_native_revision'],
        date_raw=z['queried_date_raw'],episode_run_id=z['queried_episode_run_id'],paused=True,map_ready=True,
        played_character={'character_id':z['played_character_id'],'alive':True},active_wars=[],
        diagnostics={'connection_generation':z['connection_generation'],'bridge_pid':51028,
            'hello':{'pid':51028,'connection_generation':z['connection_generation'],
                     'expected_ck3_version':z['game_version'],'expected_ck3_sha256':z['executable_sha256']}})

def frame(z,rid):
    leaf={k:z[k] for k in c._B15_FIELDS};leaf['request_id']=rid
    owner=deepcopy(z['native_command_result'][c.OWNER_RECEIPT_KEY]);owner['request_id']=rid
    return dict(type='command_result',protocol_version=1,request_id=rid,ok=True,result=leaf,**{c.OWNER_RECEIPT_KEY:owner})

class Driver:
    def __init__(self):
        self._driver_state_lock=threading.RLock();self.command_timeout_seconds=.1
        self._war_results_window_attempt=0;self._war_results_window_close_pending=None
        self._war_results_window_observation=None;self._war_results_window_query_attempt=None;self._war_results_window_last_clear=None
        self.snapshot=snapshot(CLOSE);self.after=None;self.reads=0;self.reply=deepcopy(CLOSE)
        self.sent=[];self.recorded=[];self.timeout=False;self.late={};self.refuse_query=False
        self.endpoint=SimpleNamespace(send=lambda request:self.sent.append(request))
        self.state=SimpleNamespace(capabilities=lambda:{'bridge_capabilities':[c.QUERY_CAPABILITY,c.CLOSE_CAPABILITY]},wait_for_command_result=self.wait)
    def wait(self,rid,timeout):
        if timeout==0:return self.late.pop(rid,None)
        if self.timeout:return None
        if self.refuse_query:return dict(type='command_result',protocol_version=1,request_id=rid,ok=False,error='state_changed')
        return frame(self.reply,rid)
    def take_internal_semantic_snapshot(self):
        self.reads+=1
        return deepcopy(self.after if self.after is not None and self.reads%2==0 else self.snapshot)
    def _record_command(self,*a,**kw):self.recorded.append((a,kw))

def execute(module,d,operation):return module.execute_war_results_window_v1(d,operation=operation,expected_revision=d.snapshot['revision'])
def decision(module,planner,d):
    s=deepcopy(d.snapshot);s.update(module.war_results_window_snapshot_fields(d,s))
    return planner.plan_ordinary_war_results_window_v1(s,action_steps=[c.QUERY_STEP,c.CLOSE_STEP],bridge_capabilities=[c.QUERY_CAPABILITY,c.CLOSE_CAPABILITY])

def later_visible(d,*,days=6):
    """Synthetic subsequent visibility with the real observed query shape."""
    d.reply=deepcopy(VISIBLE);d.snapshot['native_revision']+=1;d.snapshot['revision']+=1
    d.snapshot['snapshot_id']='native:'+str(d.snapshot['native_revision']);d.snapshot['date_raw']+=days*24
    d.reply.update(native_revision=d.snapshot['native_revision'],date_raw=d.snapshot['date_raw'],ticket_sequence=847,pump_epoch=310540)
    owner=d.reply['native_command_result'][c.OWNER_RECEIPT_KEY]
    owner.update(ticket_sequence=847,executor_started_sequence=847,completed_sequence=847,pump_epoch=310540,date_raw=d.snapshot['date_raw'])

class Tests(unittest.TestCase):
    def test_actual_close_then_hidden_is_settled_without_close_credit(self):
        d=Driver();original=execute(new,d,'close');d.reply=deepcopy(HIDDEN)
        result=execute(new,d,'query')
        self.assertEqual(original['status'],'verification_pending');self.assertIsNone(d._war_results_window_close_pending)
        self.assertFalse(result['prior_close_execution_observation']['close_action_credit'])
        self.assertEqual(result['prior_close_execution_observation']['native_request_id'],d.sent[0]['request_id'])
        self.assertIsNone(decision(new,newplan,d))
        fields=new.war_results_window_snapshot_fields(d,d.snapshot)
        self.assertFalse(fields['war_results_window_v1_check_due'])  # existing 6-day negative-read cadence preserved.
        later_visible(d);execute(new,d,'query')
        self.assertEqual(decision(new,newplan,d)['selected_step'],c.CLOSE_STEP)
    def test_later_visible_directly_rearms_only_a_new_current_intent(self):
        d=Driver();execute(new,d,'close');oldid=d.sent[0]['request_id'];later_visible(d)
        result=execute(new,d,'query')
        self.assertIsNone(d._war_results_window_close_pending)
        self.assertEqual(decision(new,newplan,d)['selected_step'],c.CLOSE_STEP)
        self.assertFalse(result['prior_close_execution_observation']['original_action_replayed'])
        self.assertEqual(sum(x['step']==c.CLOSE_STEP for x in d.sent),1)
        self.assertEqual(result['prior_close_execution_observation']['native_request_id'],oldid)
    def test_same_frame_visible_defers_instead_of_zero_day_close_query_loop(self):
        d=Driver();execute(new,d,'close');d.reply=deepcopy(HIDDEN)
        d.reply.update(status='visible',effective_visible=True,post_effective_visible=True)
        result=execute(new,d,'query')
        self.assertTrue(result['close_retry_deferred_for_native_frame'])
        self.assertIsNone(decision(new,newplan,d));self.assertEqual(len(d.sent),2)
    def test_normal_verified_close_still_uses_its_original_success_path(self):
        d=Driver();d.reply.update(available=True,accepted=True,status='closed_verified',unavailable_reason='',closure_verified=True,post_effective_visible=False)
        result=execute(new,d,'close');self.assertTrue(result['closure_verified']);self.assertIsNone(d._war_results_window_close_pending)
        self.assertNotIn('prior_close_execution_observation',result)
    def test_late_original_callback_is_collected_without_a_second_close(self):
        d=Driver();d.timeout=True
        with self.assertRaises(new.BridgeUnavailableError):execute(new,d,'close')
        rid=d.sent[0]['request_id'];d.timeout=False;d.late[rid]=frame(CLOSE,rid);d.reply=deepcopy(HIDDEN)
        execute(new,d,'query')
        self.assertIsNone(d._war_results_window_close_pending)
        self.assertEqual(sum(x['step']==c.CLOSE_STEP for x in d.sent),1)
        self.assertTrue(d.recorded[0][1]['result']['late_original_response'])
    def test_unknown_original_response_cannot_be_replaced_by_a_fresh_query(self):
        d=Driver();d.timeout=True
        with self.assertRaises(new.BridgeUnavailableError):execute(new,d,'close')
        rid=d.sent[0]['request_id'];d.timeout=False;d.reply=deepcopy(HIDDEN)
        execute(new,d,'query')
        self.assertEqual(d._war_results_window_close_pending['native_request_id'],rid)
        self.assertNotIn('completed_response',d._war_results_window_close_pending)
    def test_callback_pending_keeps_independent_scope_transition_contract(self):
        d=Driver();d.reply.update(scope_unchanged=False,post_observed=False,
            unavailable_reason='war_results_ui_scope_transition;snapshot_changed',post_observation_source='')
        d.after=deepcopy(d.snapshot);d.after.update(native_revision=587,revision=570,snapshot_id='native:587')
        result=execute(new,d,'close');self.assertFalse(result['scope_unchanged'])
        self.assertIn('completed_response',d._war_results_window_close_pending)
        d.snapshot=d.after;d.after=None;d.reply=deepcopy(HIDDEN);d.reply['native_revision']=587
        execute(new,d,'query');self.assertIsNone(d._war_results_window_close_pending)
        self.assertIsNone(decision(new,newplan,d))
    def test_old_pump_ticket_and_foreign_scope_do_not_retire(self):
        for change in ['pump','ticket','thread','actor','episode','connection']:
            with self.subTest(change=change):
                d=Driver();execute(new,d,'close');d.reply=deepcopy(HIDDEN)
                receipt=d.reply['native_command_result'][c.OWNER_RECEIPT_KEY]
                if change=='pump':d.reply['pump_epoch']=receipt['pump_epoch']=CLOSE['pump_epoch']
                elif change=='ticket':
                    d.reply['ticket_sequence']=CLOSE['ticket_sequence']
                    for key in ['ticket_sequence','executor_started_sequence','completed_sequence']:receipt[key]=CLOSE['ticket_sequence']
                elif change=='thread':d.reply['thread_id']=receipt['thread_id']=9
                elif change=='actor':d.snapshot['played_character']['character_id']=d.reply['played_character_id']=12
                elif change=='episode':d.snapshot['episode_run_id']='foreign'
                else:
                    d.snapshot['diagnostics']['connection_generation']=4;d.snapshot['diagnostics']['hello']['connection_generation']=4
                    d.reply['connection_generation']=receipt['connection_generation']=4
                execute(new,d,'query');self.assertIsNotNone(d._war_results_window_close_pending)
    def test_original_callback_not_returned_stays_unresolved(self):
        d=Driver();d.reply.update(dismiss_stage='callback_entered',dispatch_invoked=False,native_handled=False)
        execute(new,d,'close');d.reply=deepcopy(HIDDEN);execute(new,d,'query')
        self.assertIsNotNone(d._war_results_window_close_pending)
    def test_state_changed_query_keeps_technical_read_defer_and_pending(self):
        d=Driver();execute(new,d,'close');d.refuse_query=True
        result=execute(new,d,'query')
        self.assertEqual(result['schema'],'xar.war-results-readonly-state-changed/v1')
        self.assertFalse(result['business_submission']);self.assertFalse(result['request_retried'])
        self.assertIsNotNone(d._war_results_window_close_pending)

if __name__=='__main__':unittest.main()
