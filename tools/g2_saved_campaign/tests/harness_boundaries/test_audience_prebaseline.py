import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from tools.g2_saved_campaign import audience_sdk_binding as binding
from tools.g2_saved_campaign.runtime_repair_prebaseline import PrebaselinePublisher

FIXTURES = Path(__file__).resolve().parent



class FastModules(unittest.TestCase):
    def fixture(self):
        return json.loads((FIXTURES/'actual-audience-binding.json').read_bytes())

    def fix(self, row):
        return binding.corrected(row['before'], row['launch'], row['recording_request'],
            row['actual_pair_pin'], row['actual_pair'], runtime_root=row['runtime_root'], sdk_prefix='p37')

    def test_actual_audience_session_and_recording_sid_are_separate(self):
        row = self.fixture();fixed = self.fix(row)
        self.assertEqual(fixed['session'], str(Path(row['runtime_root']).resolve()))
        self.assertEqual(fixed['recording_session_id'], row['before']['session'])
        self.assertEqual(row['before']['session'], row['recording_request']['session_id'])
        for key, value in [('game_creation_filetime', 1), ('session', 'other-recording')]:
            wrong = copy.deepcopy(row);wrong['before'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.fix(wrong)

    def test_qualified_pair_and_observer_are_required(self):
        row = self.fixture();row['actual_pair']['observer'] = 'unretained'
        with self.assertRaises(ValueError): self.fix(row)
        row = self.fixture();row['actual_pair']['processes'] = []
        with self.assertRaises(ValueError): self.fix(row)

    def test_bytes_preserved_and_only_metadata_fields_replaced(self):
        row = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);path = root/'active.json'
            original = json.dumps(row['before'], separators=(',', ':')).encode()
            path.write_bytes(original)
            proof = binding.compare_and_replace(path, self.fix(row),
                expected_sha256=hashlib.sha256(original).hexdigest(), backup_path=root/'before.json', audit_path=root/'audit.json')
            self.assertEqual((root/'before.json').read_bytes(), original)
            self.assertEqual(json.loads(path.read_bytes())['session'], str(Path(row['runtime_root']).resolve()))
            self.assertFalse(proof['repair_incident_created'])
            with self.assertRaises(ValueError):
                binding.compare_and_replace(path, self.fix(row), expected_sha256='0'*64,
                    backup_path=root/'other-before.json', audit_path=root/'other-audit.json')

    def publisher(self, root):
        queue = root/'p38-queue';queue.mkdir()
        pub = object.__new__(PrebaselinePublisher)
        pub.session, pub.prefix, pub.queue = root, 'p38', queue
        return pub

    def test_missing_prebaseline_is_unknown_not_synthetic_zero_credit(self):
        with tempfile.TemporaryDirectory() as temp:
            pub = self.publisher(Path(temp));value = pub.small_inputs()
            self.assertEqual(value[0], {})
            self.assertNotIn('completed_cycles', value[0])
            self.assertIsNone(pub.observe_recording_pause())

    def test_missing_established_and_corrupt_baseline_remain_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            pub = self.publisher(Path(temp));loop = pub.queue/'ROOT-CUMULATIVE-LOOP-STATE.json'
            loop.write_text('{bad', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError): pub.small_inputs()
            loop.write_text('{}', encoding='utf-8');pub.small_inputs();loop.unlink()
            with self.assertRaises(FileNotFoundError): pub.small_inputs()
        for marker in ('ROOT-CLEAN-CAMPAIGN-VERIFIED.json', 'ROOT-COLD-CAMPAIGN-VERIFIED.json'):
            with tempfile.TemporaryDirectory() as temp:
                pub = self.publisher(Path(temp));(pub.queue/marker).write_text('{}', encoding='utf-8')
                with self.subTest(marker=marker), self.assertRaises(FileNotFoundError): pub.small_inputs()


if __name__ == '__main__': unittest.main()
