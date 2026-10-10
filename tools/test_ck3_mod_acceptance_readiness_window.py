"""Offline diagnostics for the original readiness interval; never a game fixture."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
import json
import tempfile
import ck3_mod_acceptance_client as source


class Clock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class ReadinessBoundary(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.clock = Clock()
        self.client = source.CaseClient.__new__(source.CaseClient)
        c = self.client
        c.output = self.output
        c.live = self.output / 'actual-run'
        c.state = self.output / 'actual-state'
        c.frozen = {'run_id': 'synthetic-distinct-run', 'screen_task': 'synthetic-distinct-screen'}
        c.context = {'frozen_argv': {'path': 'actual-frozen-argv', 'bytes': 17, 'sha256': 'd' * 64}}
        c.selection = SimpleNamespace(prepared={'preparation': {}},
            case={'budgets': {'readiness_timeout': 900, 'timeout': 8400}},
            runtime={'manifest': {'path': 'actual-runtime-manifest', 'bytes': 23, 'sha256': 'e' * 64}})
        self.calls = []
        c.retain_held_process = lambda report: self.calls.append('retain-held')
        c.retain_process = lambda: self.calls.append('retain-process')
        c.guard = lambda: self.calls.append('guard')
        self.report = {'phase': 'hold', 'steps': [], 'started_at': 'host-start',
            'saved_campaign_restore': {'status': 'ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND',
                'finished_at': 'actual-restore-finish'}, 'hold_until_utc_estimated': 123456.0}
        c.read_report = lambda **kwargs: self.report
        self.addCleanup(patch.stopall)
        patch.object(source.time, 'monotonic', self.clock.monotonic).start()
        patch.object(source.time, 'sleep', self.clock.sleep).start()

    def read(self, name):
        return json.loads((self.output / name).read_bytes())

    def test_ready_before_unchanged_deadline_records_exact_binding(self):
        self.client.guard = lambda: setattr(self.clock, 'now', 999.999)
        self.assertIs(self.client.wait_hold(), self.report)
        window = self.read('readiness-window.json')
        end = self.read('readiness-window-result.json')
        self.assertEqual((window['started_monotonic'], window['budget_seconds'], window['deadline_monotonic']), (100.0, 900, 1000.0))
        self.assertEqual(window['budget_name'], 'readiness_timeout')
        self.assertEqual(window['binding']['frozen_argv'], self.client.context['frozen_argv'])
        self.assertEqual(window['binding']['runtime_manifest'], self.client.selection.runtime['manifest'])
        self.assertEqual(window['binding'], end['binding'])
        self.assertEqual(end['status'], 'READINESS_HOLD_OBSERVED')
        self.assertIs(end['within_original_deadline'], True)
        self.assertEqual(end['restore_finished_at'], 'actual-restore-finish')
        self.assertFalse(end['business_pass'])
        self.assertEqual(self.clock.sleeps, [])

    def test_equal_deadline_never_returns_hold_success(self):
        self.client.guard = lambda: setattr(self.clock, 'now', 1000.0)
        with self.assertRaisesRegex(TimeoutError, 'Original case readiness budget elapsed'):
            self.client.wait_hold()
        end = self.read('readiness-window-result.json')
        self.assertEqual(end['status'], 'READINESS_TIMEOUT')
        self.assertIs(end['within_original_deadline'], False)
        self.assertEqual(end['elapsed_seconds'], 900.0)
        self.assertEqual(self.clock.sleeps, [])

    def test_slow_guard_past_deadline_is_not_reclassified_ready(self):
        self.client.guard = lambda: setattr(self.clock, 'now', 1000.25)
        with self.assertRaises(TimeoutError):
            self.client.wait_hold()
        end = self.read('readiness-window-result.json')
        self.assertEqual(end['elapsed_seconds'], 900.25)
        self.assertEqual(end['status'], 'READINESS_TIMEOUT')
        self.assertFalse(end['new_wait_or_replay'])
        self.assertEqual(self.calls, ['retain-held', 'retain-process'])

    def test_original_host_error_receipt_exists_before_outer_handler(self):
        def fail(**kwargs):
            raise ValueError('actual-host-error')
        self.client.read_report = fail
        with self.assertRaisesRegex(ValueError, 'actual-host-error'):
            self.client.wait_hold()
        end = self.read('readiness-window-result.json')
        self.assertEqual(end['status'], 'READINESS_ERROR')
        self.assertEqual(end['error'], 'ValueError: actual-host-error')
        self.assertIsNone(end['host_phase'])
        self.assertEqual(self.calls, [])

    def test_missing_report_consumes_only_original_window(self):
        def missing(**kwargs):
            self.clock.now = 1000.0
            raise FileNotFoundError('not-yet-written')
        self.client.read_report = missing
        with self.assertRaises(TimeoutError):
            self.client.wait_hold()
        self.assertEqual(self.clock.sleeps, [.1])
        self.assertEqual(self.read('readiness-window-result.json')['status'], 'READINESS_TIMEOUT')
        self.assertEqual(self.client._readiness_limit, 1000.0)

    def test_existing_initial_business_budget_choice_preserved(self):
        self.client.selection.prepared = {'preparation': {'initial_plan_original_business': True}}
        self.client.wait_hold()
        window = self.read('readiness-window.json')
        self.assertEqual((window['budget_name'], window['budget_seconds'], window['deadline_monotonic']), ('timeout', 8400, 8500.0))

    def test_diagnostics_are_create_once_not_overwritten_by_reentry(self):
        self.client.wait_hold()
        original = (self.output / 'readiness-window.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.client.wait_hold()
        self.assertEqual((self.output / 'readiness-window.json').read_bytes(), original)


if __name__ == '__main__':
    main()
