"""Use the real retained-host producer with harmless Python children only."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_client as source
from ck3_mod_acceptance_launcher import retain_host


class ReadinessHostExitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='readiness-original-host-exit-')
        self.addCleanup(temporary.cleanup)
        self.live = Path(temporary.name) / 'synthetic-run'
        self.live.mkdir()
        self.output = self.live / 'case-output'
        self.output.mkdir()
        self.now = 100.0
        self.sleeps = []
        self.client = source.CaseClient.__new__(source.CaseClient)
        self.client.live = self.live
        self.client.output = self.output
        self.client.state = self.live / 'state'
        self.client.report_path = self.live / 'native-report.json'
        self.client.selection = SimpleNamespace(prepared={'preparation': {}},
            case={'budgets': {'readiness_timeout': 400, 'timeout': 2100}},
            runtime={'manifest': {'path': 'runtime-manifest', 'bytes': 1, 'sha256': 'a' * 64}})
        self.clock = patch.object(source.time, 'monotonic', lambda: self.now)
        self.sleep = patch.object(source.time, 'sleep', self.tick)
        self.clock.start()
        self.sleep.start()
        self.addCleanup(self.clock.stop)
        self.addCleanup(self.sleep.stop)

    def tick(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    @staticmethod
    def pin(path):
        raw = path.read_bytes()
        return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def child(self, code):
        frozen = {'run_id': self.live.name, 'screen_task': 'synthetic-screen',
                  'argv': [sys.executable, '-c', code], 'lease_anchor': str(self.live)}
        self.client.frozen = frozen
        path = self.live / 'frozen-argv.json'
        path.write_text(json.dumps(frozen), encoding='utf-8')
        self.client.context = {'frozen_argv': self.pin(path)}
        return retain_host(self.live, frozen, {}, {'lease': {}})

    def result(self):
        return json.loads((self.output / 'readiness-window-result.json').read_bytes())

    def test_actual_failed_host_does_not_wait_for_missing_report(self):
        message = 'normal-exit private V1 does not support enabled mod GUI files'
        self.assertEqual(self.child('raise ValueError(' + repr(message) + ')'), 1)
        with self.assertRaisesRegex(ValueError, 'Original shared host exited before report') as raised:
            self.client.wait_hold()
        self.assertIn('ValueError: ' + message, str(raised.exception))
        result = self.result()
        self.assertEqual(result['status'], 'READINESS_HOST_EXIT_BEFORE_REPORT')
        self.assertEqual(result['elapsed_seconds'], 0)
        self.assertTrue(result['within_original_deadline'])
        self.assertEqual(self.sleeps, [])
        proof = result['host_exit_before_report']
        for key, filename in [('host_started', 'host-started.json'), ('host_exit', 'host-original-process-exit.json'),
                              ('host_stderr', 'host-stderr.log')]:
            self.assertEqual(proof[key], self.pin(self.live / filename))
        self.assertEqual(proof['host_returncode'], 1)
        for key in ('native_report_observed', 'normal_close_qualified', 'native_exit_zero_proven', 'business_pass'):
            self.assertIs(proof[key], False)
        self.assertFalse(self.client.report_path.exists())

    def test_host_exit_zero_still_cannot_supply_native_or_business_success(self):
        self.assertEqual(self.child('pass'), 0)
        with self.assertRaisesRegex(ValueError, 'before report \\(exit 0\\)'):
            self.client.wait_hold()
        proof = self.result()['host_exit_before_report']
        self.assertEqual(proof['host_returncode'], 0)
        self.assertFalse(proof['native_exit_zero_proven'])
        self.assertFalse(proof['normal_close_qualified'])

    def test_receipt_for_another_pid_is_a_readiness_error(self):
        self.child('raise ValueError("real harmless child failure")')
        path = self.live / 'host-original-process-exit.json'
        exited = json.loads(path.read_bytes())
        exited['pid'] += 1
        path.write_text(json.dumps(exited), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'differs from allocated run/PID/argv/retained wait'):
            self.client.wait_hold()
        self.assertEqual(self.result()['status'], 'READINESS_ERROR')
        self.assertIsNone(self.result()['host_exit_before_report'])

    def test_incomplete_receipt_waits_only_until_original_producer_write_completes(self):
        self.child('raise ValueError("original write completes")')
        path = self.live / 'host-original-process-exit.json'
        original = path.read_bytes()
        path.write_bytes(b'{')

        def complete(seconds):
            self.tick(seconds)
            path.write_bytes(original)

        with patch.object(source.time, 'sleep', complete):
            with self.assertRaisesRegex(ValueError, 'original write completes'):
                self.client.wait_hold()
        self.assertEqual(self.sleeps, [.1])
        self.assertEqual(self.result()['status'], 'READINESS_HOST_EXIT_BEFORE_REPORT')
        self.assertAlmostEqual(self.result()['elapsed_seconds'], .1)


if __name__ == '__main__':
    unittest.main()
