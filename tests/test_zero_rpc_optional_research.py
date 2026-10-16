from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest
PACK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PACK/'tools'))
from g2_saved_campaign.zero_rpc_optional_research import (
    qualify_optional_research_preflight_v1,settle_optional_research_preflight_v1,ARMY_CONFIG_TOOL)

def bytes_for(value):return json.dumps(value,separators=(',',':')).encode()
def inputs():
    fixture=json.loads((Path(__file__).parent/'fixtures'/'zero_rpc_optional_research_synthetic.json').read_bytes())
    mode=bytes_for(fixture['mode']);semantic=bytes_for(fixture['semantic_row'])
    digest='a'*64
    kwargs=dict(error=fixture['error'],state=fixture['state'],readonly_research_tools=[ARMY_CONFIG_TOOL],
      semantic_row=fixture['semantic_row'],semantic_raw=semantic,semantic_source='responses/retained-sem.json',
      semantic_sha256=hashlib.sha256(semantic).hexdigest(),unused_sequence=19,inflight_requests={},before_submit_sequences=[],
      expected_game=fixture['game'],observed_game_creation_filetime=1001,expected_lifecycle=fixture['lifecycle'],
      source_mode_raw=mode,source_mode_sha256=hashlib.sha256(mode).hexdigest(),expected_driver_source='source/native_driver.py',
      source_pins={'source/native_driver.py':digest},observed_source_hashes={'source/native_driver.py':digest})
    return fixture['original'],kwargs

class Tests(unittest.TestCase):
    def test_positive_is_zero_credit_and_parameterized(self):
        original,args=inputs();result=qualify_optional_research_preflight_v1(original,**args)
        self.assertEqual(result['completed_cycles'],52)
        self.assertEqual(result['original_request']['sequence'],17)
        self.assertEqual(result['unused_sequence'],19)
        self.assertEqual(result['new_MCP_or_native_calls'],0)
        self.assertFalse(result['original_request_replayed']);self.assertFalse(result['succession_performed'])
        self.assertEqual(result['new_business_credit'],0)

    def test_rejects_wrong_original_or_dispatch(self):
        changes=[lambda o,a:o.update(row={}),lambda o,a:o.update(response='response.json'),
          lambda o,a:a['error'].update(message='unknown error'),
          lambda o,a:o['request']['arguments'].update(mode='use'),
          lambda o,a:a.update(readonly_research_tools=[]),
          lambda o,a:a.update(inflight_requests={17:{'tool':ARMY_CONFIG_TOOL}}),
          lambda o,a:a.update(before_submit_sequences=[17]),
          lambda o,a:a.update(inflight_requests={18:{'tool':'ck3_auto_turn'}}),
          lambda o,a:a['state'].update(pending_cycle={'stage':'unknown'})]
        for change in changes:
            original,args=inputs();change(original,args)
            with self.subTest(change=change),self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)

    def test_rejects_unbound_source_mode_and_file_identity(self):
        for field,value in [('source_file','other.py'),('before_submit_observation',False),('policy_replaced',True)]:
            original,args=inputs();mode=json.loads(args['source_mode_raw']);mode[field]=value
            args['source_mode_raw']=bytes_for(mode);args['source_mode_sha256']=hashlib.sha256(args['source_mode_raw']).hexdigest()
            with self.subTest(field=field),self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)
        original,args=inputs();args['observed_source_hashes']['source/native_driver.py']='b'*64
        with self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)
        original,args=inputs();args['source_mode_sha256']='c'*64
        with self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)

    def test_rejects_changed_game_or_retained_semantic(self):
        changes=[lambda b:b.update(paused=False),lambda b:b.update(date_raw=12024),
          lambda b:b['played_character'].update(character_id=10),lambda b:b['diagnostics'].update(bridge_pid=99),
          lambda b:b.update(succession_lifecycle={'lifecycle':'different'}),lambda b:b.update(one_life_terminal=True)]
        for change in changes:
            original,args=inputs();change(args['semantic_row']['result']['structured_content'])
            args['semantic_raw']=bytes_for(args['semantic_row']);args['semantic_sha256']=hashlib.sha256(args['semantic_raw']).hexdigest()
            with self.subTest(change=change),self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)
        original,args=inputs();args['observed_game_creation_filetime']=1002
        with self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)
        original,args=inputs();args['semantic_row']['result']['structured_content']['date_raw']+=24
        with self.assertRaises(ValueError):qualify_optional_research_preflight_v1(original,**args)

    def test_local_commit_preserves_counts_and_orders_clear_last(self):
        original,args=inputs();qualified=qualify_optional_research_preflight_v1(original,**args);events=[];saved=[]
        receipt=settle_optional_research_preflight_v1(qualified,control_sequence=19,state=args['state'],
          consume_sequence=lambda seq:events.append('consume') or seq,
          write_audit=lambda value:events.append('audit'),persist_state=lambda value:saved.append(value) or events.append('persist'),
          write_response=lambda value:events.append('response'),clear_halt=lambda:events.append('clear'))
        self.assertEqual(events,['consume','audit','persist','response','clear'])
        self.assertEqual(saved[0]['counts'],args['state']['counts'])
        self.assertEqual(saved[0]['completed_cycles'],52);self.assertTrue(receipt['counts_unchanged'])

    def test_duplicate_or_changed_state_does_not_consume(self):
        original,args=inputs();qualified=qualify_optional_research_preflight_v1(original,**args);events=[]
        callbacks=dict(consume_sequence=lambda seq:events.append('consume') or seq,write_audit=lambda v:None,
          persist_state=lambda v:None,write_response=lambda v:None,clear_halt=lambda:events.append('clear'))
        with self.assertRaises(ValueError):settle_optional_research_preflight_v1(qualified,control_sequence=19,state=args['state'],audit_exists=True,**callbacks)
        args['state']['counts']['observations']+=1
        with self.assertRaises(ValueError):settle_optional_research_preflight_v1(qualified,control_sequence=19,state=args['state'],**callbacks)
        self.assertEqual(events,[])

    def test_write_failure_never_clears_halt(self):
        original,args=inputs();qualified=qualify_optional_research_preflight_v1(original,**args);events=[]
        def fail(value):events.append('audit');raise OSError('simulated atomic write failure')
        with self.assertRaises(OSError):settle_optional_research_preflight_v1(qualified,control_sequence=19,state=args['state'],
          consume_sequence=lambda seq:events.append('consume') or seq,write_audit=fail,persist_state=lambda v:events.append('persist'),
          write_response=lambda v:events.append('response'),clear_halt=lambda:events.append('clear'))
        self.assertEqual(events,['consume','audit'])

if __name__=='__main__':unittest.main(verbosity=2)
