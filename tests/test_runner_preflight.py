from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from g2_saved_campaign.runner_preflight import require_published_full, interruption_evidence_id

class Tests(unittest.TestCase):
    def test_missing_request_is_rejected_before_caller_can_attach(self):
        with tempfile.TemporaryDirectory() as tmp:
            events=[]
            with self.assertRaises(ValueError):
                require_published_full(27,inbox=Path(tmp),read=lambda p:json.loads(p.read_bytes()))
                events.append('attach')
            self.assertEqual(events,[])

    def test_exact_bounded_full_and_malformed_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'0027-1-result.json'
            read=lambda p:json.loads(p.read_bytes())
            for value in [True,0,31,'30']:
                path.write_text(json.dumps({'sequence':27,'command':'full_loop','arguments':{'max_turns':value}}))
                with self.subTest(value=value),self.assertRaises(ValueError):require_published_full(27,inbox=root,read=read)
            valid={'sequence':27,'command':'full_loop','arguments':{'max_turns':30}}
            path.write_text(json.dumps(valid));self.assertEqual(require_published_full(27,inbox=root,read=read),valid)
            path.write_text(json.dumps({**valid,'tool':'ck3_auto_turn'}))
            with self.assertRaises(ValueError):require_published_full(27,inbox=root,read=read)

    def test_same_source_path_changed_content_has_new_identity(self):
        data={'source':'queue/state.json','source_pins':{'settled_state':{'sha256':'old'}},
          'reason':'fixture failure','frame':{'date_raw':12000},'completed_cycles':52}
        first=interruption_evidence_id(**data)
        self.assertEqual(first,interruption_evidence_id(**copy.deepcopy(data)))
        data['source_pins']['settled_state']['sha256']='new'
        self.assertNotEqual(first,interruption_evidence_id(**data))

if __name__=='__main__':unittest.main()
