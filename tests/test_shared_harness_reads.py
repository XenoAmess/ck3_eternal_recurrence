from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from g2_saved_campaign import shared_harness_reads as shared


class SharedHarnessReadTests(unittest.TestCase):
    def test_sharing_retry_returns_exact_bytes(self):
        attempts=[];sleeps=[]
        def reader(path):
            attempts.append(path)
            if len(attempts)<3:
                error=PermissionError(13,'simulated sharing collision');error.winerror=32;raise error
            return b'{"frame":7}'
        self.assertEqual(shared.read_bytes('fixture',_reader=reader,_sleep=sleeps.append),b'{"frame":7}')
        self.assertEqual(len(attempts),3)
        self.assertEqual(sleeps,[.01,.02])

    def test_permanent_denial_bounded_unrelated_error_not_retried(self):
        for code,expected in ((5,6),(2,1),(87,1)):
            with self.subTest(code=code):
                calls=[]
                def reader(path):
                    calls.append(path);error=OSError('simulated');error.winerror=code;raise error
                with self.assertRaises(OSError):shared.read_bytes('fixture',_reader=reader,_sleep=lambda _:None)
                self.assertEqual(len(calls),expected)

    def test_real_read_and_decode_then_invalid_json_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'fixture.json';p.write_bytes(b'{invalid')
            original=shared._read_once;calls=[]
            def read(path):calls.append(path);return original(path)
            with patch.object(shared,'_read_once',read):
                with self.assertRaises(json.JSONDecodeError):json.loads(shared.read_bytes(p))
            self.assertEqual(len(calls),1)
            p.write_bytes(b'\xef\xbb\xbf{"frame":7}\r\n')
            self.assertEqual(shared.read_bytes(p),p.read_bytes())
            self.assertEqual(json.loads(shared.read_text(p,encoding='utf-8-sig')),{'frame':7})

    def test_invalid_text_is_not_a_sharing_retry(self):
        with patch.object(shared,'_read_once',return_value=b'\xff') as read:
            with self.assertRaises(UnicodeDecodeError):shared.read_text('fixture',encoding='utf-8')
            self.assertEqual(read.call_count,1)

    def test_nested_opt_in_restores_path_methods(self):
        original=(Path.read_bytes,Path.read_text)
        with shared.installed():
            self.assertIs(Path.read_bytes,shared.read_bytes)
            with shared.installed():self.assertIs(Path.read_text,shared.read_text)
            self.assertIs(Path.read_text,shared.read_text)
        self.assertEqual((Path.read_bytes,Path.read_text),original)

    def test_normal_batch_avoids_state_but_actual_halt_and_recovery_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);queue=root/'p4-queue';queue.mkdir()
            (queue/'ROOT-CUMULATIVE-LOOP-STATE.json').write_bytes(b'invalid state must not be read')
            self.assertFalse(shared.recovery_may_be_needed(3,root,queue))
            current=root/'ROOT-CURRENT-HALT-P4.json'
            current.write_text(json.dumps({'original_request':{'sequence':10,'tool':'ck3_auto_turn'},
                'original_response':str(root/'p4-responses/0010-1-result.json')}),encoding='utf-8')
            self.assertFalse(shared.recovery_may_be_needed(3,root,queue))
            (queue/'ROOT-REQUEST-HALTED-0010.json').write_bytes(b'{}')
            self.assertTrue(shared.recovery_may_be_needed(3,root,queue))
            self.assertFalse(shared.recovery_may_be_needed(20,root,queue))
            (queue/'ROOT-OPTIONAL-FRAME-FEEDER-0020.json').write_bytes(b'{}')
            self.assertTrue(shared.recovery_may_be_needed(20,root,queue))
            current.write_bytes(b'invalid')
            with self.assertRaises(json.JSONDecodeError):shared.recovery_may_be_needed(21,root,queue)

    def test_explicit_paths_do_not_require_campaign_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);queue=root/'queue';queue.mkdir()
            current=root/'current.json';responses=root/'observations'
            current.write_text(json.dumps({'original_request':{'sequence':8,'tool':'ck3_auto_turn'},
                'original_response':str(responses/'0008-1-result.json')}),encoding='utf-8')
            (queue/'ROOT-REQUEST-HALTED-0008.json').write_bytes(b'{}')
            self.assertTrue(shared.recovery_may_be_needed(3,root,queue,
                current_halt=current,response_root=responses))


if __name__=='__main__':unittest.main(verbosity=2)
