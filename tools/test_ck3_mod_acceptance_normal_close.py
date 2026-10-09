"""Portable Root-review race regressions using the actual client and native predicate."""
from __future__ import annotations
import argparse
import copy
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
CLIENT_SOURCE = REPO / 'tools/ck3_mod_acceptance_client.py'
HOST_SOURCE = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'


class NormalCloseReviewRaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('_normal_close_client_under_test', CLIENT_SOURCE)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def make_client(self, root, *, review_at=.3, deadline=1, os_exit=0, native_exit=0, reviewer='/root'):
        module = self.module
        client = module.CaseClient.__new__(module.CaseClient)
        client.output = root
        client._handle = object()
        client._process = {'pid': 2468, 'create_time': 123.5}
        client.frozen = {'run_id': 'SYNTHETIC_ROOT_REVIEW_RACE'}
        client._hold = deadline
        client._started = 0
        client.manifest = {'host': {}}
        client.selection = SimpleNamespace(case={'budgets': {}}, manifest_path_key=lambda _: HOST_SOURCE)
        client.execute_plan = Mock(side_effect=AssertionError('No finish/control submission after terminal host'))
        clock = SimpleNamespace(now=0.0, review_written=False)
        image = root / 'synthetic-reviewed-quit.not-image'
        image.write_bytes(b'SYNTHETIC ONLY: no actual GUI review or input')
        evidence = {'path': str(image), 'bytes': image.stat().st_size,
                    'sha256': hashlib.sha256(image.read_bytes()).hexdigest()}
        response = root / 'normal-quit-root-result.json'
        def sleep(seconds):
            clock.now += seconds
            if review_at is not None and clock.now >= review_at and not clock.review_written:
                module.write_once(response, {'run_id': client.frozen['run_id'], 'reviewer': reviewer,
                    'normal_gui_quit': True, 'evidence': [evidence]})
                clock.review_written = True
        client_time = SimpleNamespace(time=lambda: clock.now, sleep=sleep)
        def exit_code(_handle, pointer):
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32)).contents.value = os_exit
            return 1
        client._kernel = SimpleNamespace(WaitForSingleObject=lambda _handle, _timeout: 0,
                                        GetExitCodeProcess=exit_code)
        pipe = r'\\.\pipe\synthetic-root-review-race'
        report = {'fixture_only': False, 'error': None, 'pipe': pipe, 'phase': 'hold',
            'finished_at': '2026-10-09T10:00:11+00:00', 'managed_session_done': True,
            'managed_session_thread_finished': True, 'cleanup_ok': True,
            'session': {'error': None, 'report': {
                'kind': 'ck3_native_headless_session', 'mode': 'native-headless',
                'format_version': 1, 'ok': True, 'error': None,
                'exit_reason': 'process_exit', 'process_exit_code': native_exit, 'pid': 2468, 'pipe': pipe,
                'started_at': '2026-10-09T10:00:00+00:00', 'finished_at': '2026-10-09T10:00:10+00:00',
                'shutdown': {'ok': True, 'cleanup_proven': True, 'tree_gone': True,
                    'ck3_pid': 2468, 'ck3_exit_code': native_exit, 'job_active_processes_final': 0,
                    'contract_errors': [], 'watchdog_state_after': 'absent', 'nonce': 'a' * 32,
                    'ck3_creation_date': 'synthetic-creation-date',
                    'control_files_absent': {'ck3.json': True, 'watchdog.json': True},
                    'final_ck3_inventory': {'tasklist_returncode': 0, 'tasklist_pids': [], 'wmi_pids': [],
                        'native_pids': [], 'processes': []}}}}}
        client.read_report = lambda allow_error=False: report
        return client, clock, client_time, report

    def test_terminal_host_and_os0_wait_for_explicit_root_review(self):
        with tempfile.TemporaryDirectory() as directory:
            client, clock, fake_time, report = self.make_client(Path(directory))
            self.assertIsNotNone(client.native_zero_proof(report))  # The actual shared full predicate.
            with patch.object(self.module, 'time', fake_time):
                result = client.normal_close('synthetic-delayed-root-review')
            self.assertGreaterEqual(clock.now, .3)
            self.assertTrue(result['normal_close_qualified'])
            self.assertEqual(result['root_normal_gui_review']['reviewer'], '/root')
            self.assertIsNotNone(result['native_zero_proof'])
            client.execute_plan.assert_not_called()

    def test_missing_review_waits_only_to_original_deadline_and_stays_unqualified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client, clock, fake_time, _ = self.make_client(root, review_at=None, deadline=.4)
            with patch.object(self.module, 'time', fake_time):
                result = client.normal_close('synthetic-missing-root-review')
            self.assertGreaterEqual(clock.now, .4)
            self.assertLess(clock.now, .51)
            self.assertFalse(result['normal_close_qualified'])
            self.assertIsNone(result['root_normal_gui_review'])
            self.assertFalse((root / 'normal-quit-root-result.json').exists())
            client.execute_plan.assert_not_called()

    def test_late_review_cannot_replace_either_real_zero_proof(self):
        for os_exit, native_exit in ((1, 0), (0, 1)):
            with self.subTest(os_exit=os_exit, native_exit=native_exit), tempfile.TemporaryDirectory() as directory:
                client, _, fake_time, _ = self.make_client(Path(directory), os_exit=os_exit, native_exit=native_exit)
                with patch.object(self.module, 'time', fake_time):
                    result = client.normal_close('synthetic-nonzero-preserved')
                self.assertFalse(result['normal_close_qualified'])
                client.execute_plan.assert_not_called()

    def test_late_review_from_another_reviewer_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            client, _, fake_time, _ = self.make_client(Path(directory), reviewer='not-root')
            with patch.object(self.module, 'time', fake_time), self.assertRaisesRegex(ValueError, 'crossed scene'):
                client.normal_close('synthetic-wrong-reviewer')
            self.assertFalse((Path(directory) / 'normal-close-result.json').exists())
            client.execute_plan.assert_not_called()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-source', type=Path, default=CLIENT_SOURCE)
    parser.add_argument('--host-source', type=Path, default=HOST_SOURCE)
    parser.add_argument('--tools-dir', type=Path, default=REPO / 'tools')
    args, remaining = parser.parse_known_args()
    CLIENT_SOURCE, HOST_SOURCE = args.client_source.resolve(), args.host_source.resolve()
    sys.path.insert(0, str(args.tools_dir.resolve()))  # Only the original pure check_pin import.
    unittest.main(argv=[sys.argv[0], *remaining])
