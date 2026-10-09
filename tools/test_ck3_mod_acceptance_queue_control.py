"""Four portable producer checks; every live/control/report path is synthetic."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PRODUCER = Path(__file__).with_name('ck3_mod_acceptance_queue_control.py')


class QueueFailureSuccessorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='SYNTHETIC_QUEUE_NO_GAME_')
        self.addCleanup(self.directory.cleanup)
        self.live = Path(self.directory.name)/'synthetic-live'
        self.controls = self.live/'controls'
        self.controls.mkdir(parents=True)
        self.report = {'phase':'hold', 'finished_at':None, 'error':None, 'steps':[]}
        self.report_path = self.live/'native-report.json'
        self.frozen_path = self.live/'frozen-argv.json'
        self.frozen_path.write_text(json.dumps({'argv':['SYNTHETIC-NO-HOST',
            '--control-plan-dir',str(self.controls)]}),encoding='utf-8')
        self.plan_path = self.live/'synthetic-reviewed-plan.json'
        self.name = 'synthetic-once.json'

    def failure_plan(self):
        return {'steps':[{'id':'synthetic-failure-finish','kind':'finish_hold','failure_shutdown':True,
            'expect':{'hold_finished':True,'failure_preserved':True,
                'business_pass':False,'normal_close_qualified':False}}]}

    def submit(self,plan):
        raw = json.dumps(plan,indent=2).encode('utf-8')
        self.plan_path.write_bytes(raw)
        self.report_path.write_text(json.dumps(self.report),encoding='utf-8')
        before = self.report_path.read_bytes()
        frozen = self.frozen_path.read_bytes()
        # -O must not disable any producer input gate.
        result = subprocess.run([sys.executable,'-B','-O','-X','utf8',str(PRODUCER),
            '--live',str(self.live),'--plan',str(self.plan_path),'--name',self.name],capture_output=True)
        self.assertEqual(self.report_path.read_bytes(),before)
        self.assertEqual(self.frozen_path.read_bytes(),frozen)
        return result,raw

    def test_original_success_business_queue_bytes_and_receipt_are_preserved(self):
        plan = {'steps':[{'id':'synthetic-success-business','tool':'SYNTHETIC-NO-REAL-TOOL'}]}
        result,raw = self.submit(plan)
        self.assertEqual(result.returncode,0,result.stderr.decode())
        self.assertEqual((self.controls/self.name).read_bytes(),raw)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertIs(receipt['business_result_pending'],True)
        self.assertNotIn('failure_lifecycle_transport_only',receipt)

    def test_errored_business_queue_is_rejected_without_creating_request(self):
        self.report['error'] = 'SYNTHETIC ORIGINAL BUSINESS FAILURE'
        result,_ = self.submit({'steps':[{'id':'synthetic-business','tool':'SYNTHETIC-NO-REAL-TOOL'}]})
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'only one preserved-failure finish_hold',result.stderr)
        self.assertEqual(list(self.controls.iterdir()),[])

    def test_exact_failed_finish_queue_preserves_error_and_grants_no_pass(self):
        self.report['error'] = 'SYNTHETIC ORIGINAL BUSINESS FAILURE'
        result,raw = self.submit(self.failure_plan())
        self.assertEqual(result.returncode,0,result.stderr.decode())
        self.assertEqual((self.controls/self.name).read_bytes(),raw)
        receipt = json.loads(result.stdout)
        self.assertIs(receipt['failure_lifecycle_transport_only'],True)
        self.assertEqual(receipt['host_error_preserved'],self.report['error'])
        self.assertIs(receipt['business_result_pending'],False)
        self.assertIs(receipt['business_pass'],False)
        self.assertIs(receipt['normal_close_qualified'],False)

    def test_duplicate_name_is_rejected_once_without_overwriting_request(self):
        self.report['error'] = 'SYNTHETIC ORIGINAL BUSINESS FAILURE'
        target = self.controls/self.name
        target.write_bytes(b'SYNTHETIC EXISTING UNCONSUMED REQUEST')
        result,_ = self.submit(self.failure_plan())
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'Already dispatched; inspect, never replay',result.stderr)
        self.assertEqual(target.read_bytes(),b'SYNTHETIC EXISTING UNCONSUMED REQUEST')
        self.assertFalse(target.with_suffix('.tmp').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
