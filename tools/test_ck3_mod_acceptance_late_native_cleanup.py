"""Late Job cleanup never rewrites an earlier unsignaled retained wait."""
from __future__ import annotations

import copy
import unittest

from ck3_mod_acceptance_allocate import (
    validate_late_failed_day, validate_late_native_cleanup, validate_late_public_wait,
)


def example() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    game = {'pid': 2718, 'create_time': 100.5, 'retained_synchronize_query_handle_acquired': True}
    retained = {**game, 'signaled': False, 'exit_code': None, 'actual_retained_os0': False}
    normal = {'retained_handle': copy.deepcopy(retained), 'normal_close_qualified': False,
        'business_pass': False, 'failure_lifecycle_completed': False, 'managed_thread_finished': False,
        'host_finished_at': None, 'cleanup_ok': None, 'host_error': 'Original day unknown'}
    native = {'pid': 2718, 'finished_at': '2026-10-20T13:30:29+00:00',
        'process_exit_code': None, 'exit_reason': 'stop', 'shutdown': {
            'ck3_pid': 2718, 'ck3_exit_code': 1, 'ok': True,
            'tree_gone': True, 'cleanup_proven': True, 'job_active_processes_final': 0}}
    return normal, retained, game, native, {'error': 'Original day unknown'}


class LateCleanupTest(unittest.TestCase):
    def test_original_wait_and_later_native_exit_remain_distinct(self) -> None:
        values = example()
        original = copy.deepcopy(values)
        facts = validate_late_native_cleanup(*values, normal_written_ns=1)
        self.assertIsNone(facts['original_ck3_exit_code'])
        self.assertFalse(facts['original_retained_wait_signaled'])
        self.assertFalse(facts['actual_retained_os0'])
        self.assertFalse(facts['failure_lifecycle_completed'])
        self.assertIsNone(facts['native_cleanup_qualified'])
        self.assertEqual(facts['native_reported_ck3_exit_code'], 1)
        self.assertEqual(values, original)

    def test_wrong_retained_wait_or_normal_credit_is_rejected(self) -> None:
        for field, value in [('signaled', True), ('exit_code', 0), ('actual_retained_os0', True)]:
            with self.subTest(field=field):
                normal, retained, game, native, report = example()
                retained[field] = value
                normal['retained_handle'] = copy.deepcopy(retained)
                with self.assertRaises(ValueError):
                    validate_late_native_cleanup(normal, retained, game, native, report, 1)
        normal, retained, game, native, report = example()
        normal['failure_lifecycle_completed'] = True
        with self.assertRaises(ValueError):
            validate_late_native_cleanup(normal, retained, game, native, report, 1)

    def test_wrong_identity_and_bool_pid_are_rejected(self) -> None:
        for pid in (True, 2719):
            normal, retained, game, native, report = example()
            retained['pid'] = pid
            normal['retained_handle'] = copy.deepcopy(retained)
            with self.assertRaises(ValueError):
                validate_late_native_cleanup(normal, retained, game, native, report, 1)

    def test_unknown_cleanup_and_reversed_time_are_rejected(self) -> None:
        for field, value in [('ck3_exit_code', None), ('ck3_exit_code', True),
                             ('tree_gone', False), ('job_active_processes_final', False)]:
            with self.subTest(field=field, value=value):
                normal, retained, game, native, report = example()
                native['shutdown'][field] = value
                with self.assertRaises(ValueError):
                    validate_late_native_cleanup(normal, retained, game, native, report, 1)
        with self.assertRaises(ValueError):
            validate_late_native_cleanup(*example(), normal_written_ns=9_000_000_000_000_000_000)

    def test_actual_public_wait_format_not_legacy_aliases(self) -> None:
        argv = ['python.exe', 'ck3_mod_acceptance.py', 'allocate']
        common = {'machine_id': 'authored-machine', 'argv': argv,
            'argv_sha256': '0' * 64, 'started_at_utc': '2026-10-20T11:00:00+00:00',
            'original_popen_wait_result': None}
        process = {**common, 'pid': 99}
        complete = {**process, 'original_popen_wait_result': 0, 'exit_code': 0,
            'finished_at_utc': '2026-10-20T13:00:00+00:00'}
        self.assertEqual(validate_late_public_wait(complete, common, process, argv,
            'authored-machine', 'allocate', 0), argv)
        complete['original_popen_wait_result'] = False
        with self.assertRaises(ValueError):
            validate_late_public_wait(complete, common, process, argv, 'authored-machine', 'allocate', 0)

    def test_failed_host_day_is_not_mislabeled_as_mcp_tool(self) -> None:
        diagnostic = {'step_id': 'original-day', 'kind': 'advance_day'}
        row = {'id': 'original-day', 'ok': False, 'error': 'Original unknown',
            'finished_at': '2026-10-20T11:43:15+00:00',
            'plan': {'kind': 'advance_day', 'days': 1}}
        validate_late_failed_day(diagnostic, row)
        for value in (None, 'ck3_execute_step'):
            with self.assertRaises(ValueError):
                validate_late_failed_day({**diagnostic, 'tool': value}, row)
        row['plan']['days'] = True
        with self.assertRaises(ValueError):
            validate_late_failed_day(diagnostic, row)


if __name__ == '__main__':
    unittest.main(verbosity=2)
