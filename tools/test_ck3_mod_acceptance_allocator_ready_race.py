"""Real-file consumers for incomplete keeper READY publication; no game/CAS."""
from pathlib import Path
import io,json,subprocess,sys,tempfile,time,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import ck3_mod_acceptance_allocate as allocation

class Clock:
    def __init__(self,now=0,on_sleep=None):self.now=now;self.sleeps=[];self.on_sleep=on_sleep
    def monotonic(self):return self.now
    def sleep(self,seconds):
        self.sleeps.append(seconds);self.now+=seconds
        if self.on_sleep:self.on_sleep(len(self.sleeps))

class KeeperReadyRaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.live=self.root/'live';self.live.mkdir()
        self.keeper=self.root/'keeper';self.keeper.mkdir();self.ready=self.keeper/'ready.json'
        self.child=SimpleNamespace(pid=77,poll=Mock(return_value=None),wait=Mock(return_value=7))
        self.stdout=io.BytesIO();self.stderr=io.BytesIO()
        self.value={'at_utc':'2026-10-20T00:00:00+00:00','lease':{'task_id':'synthetic','sequence':9},
                    'inputs':{'path':'synthetic-inputs','sha256':'a'*64},'text':'中文'}
    def wait(self,started=0):
        return allocation.wait_for_keeper_ready(self.child,self.keeper,self.live,started,self.stdout,self.stderr)
    def clock(self,clock):
        return patch.multiple(allocation.time,monotonic=clock.monotonic,sleep=clock.sleep)
    def test_empty_then_partial_json_then_valid_returns_original_object(self):
        self.ready.write_bytes(b'')
        states=[b'{',b'{"lease":',b'{"lease":tru',json.dumps(self.value,ensure_ascii=False).encode()]
        clock=Clock(on_sleep=lambda count:self.ready.write_bytes(states[count-1]))
        with self.clock(clock):actual=self.wait()
        self.assertEqual(actual,self.value);self.assertEqual(len(clock.sleeps),4)
        self.child.wait.assert_not_called();self.assertFalse(self.stdout.closed)
    def test_split_utf8_byte_is_retried_until_actual_full_object(self):
        self.ready.write_bytes(b'{"text":"\xe4')
        clock=Clock(on_sleep=lambda count:self.ready.write_text(json.dumps(self.value,ensure_ascii=False),encoding='utf-8'))
        with self.clock(clock):self.assertEqual(self.wait(),self.value)
        self.assertEqual(clock.sleeps,[.02])
    def test_missing_path_then_empty_then_complete_uses_same_original_deadline(self):
        stages=[b'',json.dumps(self.value).encode()]
        clock=Clock(29.90,on_sleep=lambda count:self.ready.write_bytes(stages[count-1]))
        with self.clock(clock):self.assertEqual(self.wait(),self.value)
        self.assertAlmostEqual(clock.now,29.94);self.assertEqual(len(clock.sleeps),2)
    def test_changing_incomplete_bytes_never_reset_original_deadline(self):
        self.ready.write_bytes(b'{')
        clock=Clock(29.95,on_sleep=lambda count:self.ready.write_bytes(b'{'+b' '*count))
        with self.clock(clock),self.assertRaisesRegex(ValueError,'existing bound') as caught:self.wait()
        self.assertIsInstance(caught.exception.__cause__,json.JSONDecodeError)
        self.assertLessEqual(len(clock.sleeps),3);self.assertGreaterEqual(clock.now,30)
        self.assertFalse((self.live/'ready-context.json').exists());self.child.wait.assert_not_called()
    def test_already_elapsed_original_deadline_does_not_accept_even_valid_json(self):
        self.ready.write_text(json.dumps(self.value),encoding='utf-8');clock=Clock(30)
        with self.clock(clock),self.assertRaisesRegex(ValueError,'existing bound'):self.wait()
        self.assertEqual(clock.sleeps,[])
    def test_persistently_corrupt_json_is_not_swallowed_or_marked_ready(self):
        broken=b'{"lease":]}'
        self.ready.write_bytes(broken);clock=Clock(29.99)
        with self.clock(clock),self.assertRaisesRegex(ValueError,'existing bound') as caught:self.wait()
        self.assertIsInstance(caught.exception.__cause__,json.JSONDecodeError)
        self.assertEqual(caught.exception.__cause__.doc,broken.decode())
        self.assertEqual(self.ready.read_bytes(),broken);self.assertFalse((self.live/'ready-context.json').exists())
    def test_persistently_invalid_utf8_retains_original_decode_error(self):
        self.ready.write_bytes(b'\xff');clock=Clock(29.99)
        with self.clock(clock),self.assertRaisesRegex(ValueError,'existing bound') as caught:self.wait()
        self.assertIsInstance(caught.exception.__cause__,UnicodeDecodeError)
    def test_complete_non_object_json_is_immediate_fatal(self):
        self.ready.write_text('[]',encoding='utf-8');clock=Clock()
        with self.clock(clock),self.assertRaises(ValueError):self.wait()
        self.assertEqual(clock.sleeps,[]);self.child.wait.assert_not_called()
    def test_non_transient_io_error_is_immediate_fatal(self):
        clock=Clock()
        with (self.clock(clock),patch.object(allocation,'read_json',side_effect=PermissionError('test denied')),
              self.assertRaisesRegex(PermissionError,'test denied')):
            self.wait()
        self.assertEqual(clock.sleeps,[])
    def test_done_original_child_is_really_waited_even_if_ready_path_exists(self):
        self.ready.write_bytes(b'{');self.child.poll.return_value=7
        with self.assertRaisesRegex(ValueError,'Original keeper failed before READY'):self.wait()
        self.child.wait.assert_called_once_with()
        proof=allocation.read_json(self.live/'keeper-pre-ready-parent-exit.json')
        self.assertEqual(proof['actual_poll_exit_code'],7);self.assertEqual(proof['keeper_actual_exit_code'],7)
        self.assertTrue(proof['actual_original_popen_wait']);self.assertFalse(proof['ready_absent'])
        self.assertTrue(self.stdout.closed and self.stderr.closed);self.assertFalse(proof['business_pass'])
    def test_child_dying_during_partial_file_keeps_decoder_cause_and_actual_wait(self):
        self.ready.write_bytes(b'{');self.child.poll.side_effect=[None,7];clock=Clock()
        with self.clock(clock),self.assertRaisesRegex(ValueError,'Original keeper failed') as caught:self.wait()
        self.assertIsInstance(caught.exception.__cause__,json.JSONDecodeError)
        self.child.wait.assert_called_once_with()
    def test_actual_subprocess_partial_byte_publisher_consumed_while_alive(self):
        script=self.root/'publish.py'
        script.write_text('''from pathlib import Path
import json,sys,time
p=Path(sys.argv[1]);p.write_bytes(b'')
payload=json.dumps({'lease':{'sequence':9},'text':'中文'},ensure_ascii=False).encode('utf-8')
with p.open('wb') as f:
    for byte in payload:
        f.write(bytes([byte]));f.flush();time.sleep(.002)
stop=p.with_name('DONE')
deadline=time.monotonic()+5
while not stop.exists() and time.monotonic()<deadline:time.sleep(.01)
''',encoding='utf-8')
        child=subprocess.Popen([sys.executable,'-B',str(script),str(self.ready)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(lambda:child.kill() if child.poll() is None else None)
        started=time.monotonic()
        try:
            value=allocation.wait_for_keeper_ready(child,self.keeper,self.live,started,self.stdout,self.stderr)
            self.assertEqual(value,{'lease':{'sequence':9},'text':'中文'});self.assertIsNone(child.poll())
        finally:
            (self.keeper/'DONE').write_text('test completed',encoding='utf-8')
            out,err=child.communicate(timeout=5)
        self.assertEqual(child.returncode,0,(out,err))

if __name__=='__main__':unittest.main(verbosity=2)
