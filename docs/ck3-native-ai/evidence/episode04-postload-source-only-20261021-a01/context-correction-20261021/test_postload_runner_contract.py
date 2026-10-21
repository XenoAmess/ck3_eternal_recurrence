"""Pure source/JSON regression checks. Never instantiate Windows or run native code."""
import copy
from pathlib import Path
import unittest

import run_parent_postload_cold as runner
from postload_common_models import flag, strings
from postload_models import JsonObject
from postload_runner_models import AuditRow, Identity, target_result


class PostloadRunnerContractTests(unittest.TestCase):
    def test_explicit_21_case_selection_and_late_last(self) -> None:
        self.assertEqual(len(runner.CASES), 21)
        self.assertEqual(len(set(runner.CASES)), 21)
        self.assertEqual(runner.CASES[-1], 'cancel_late')
        self.assertEqual(runner.select_cases(runner.CASES), runner.CASES)
        for selection in ((), ('timeout', 'timeout'), ('cancel_late', 'timeout'), ('not-a-case',)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                runner.select_cases(selection)

    def test_actual_target_body_counts_cover_all_selected_cases(self) -> None:
        # Bound to the retained C++ branches, not observer captures: the target
        # continues its own declared calls after observer cleanup at the cap.
        for case in runner.CASES:
            expected = (0, 1)
            if case == 'foreign257_then_target' or case in runner.FAULTS:
                expected = (257, 1)
            elif case in {'foreign4096_limit', 'cancel_late'}:
                expected = (4096, 1)
            elif case == 'timeout' or case in runner.REFUSALS:
                expected = (0, 0)
            self.assertEqual(runner.expected_body_counts(case), expected, case)
        with self.assertRaises(ValueError):
            runner.expected_body_counts('unrecognized')

    def test_new_observer_cli_and_refusal_switches(self) -> None:
        for case in runner.CASES:
            argv, timeout = runner.observer_argv(Path('observer.exe'), Path('meta.txt'), Path('raw'), Path('ready'), 'synthetic-machine', case)
            self.assertEqual('--enable-parent-postload-execution-cold' in argv, case != 'default-off')
            self.assertEqual('--explicit-postload-execution-breakpoint-v1' in argv, case != 'missing-ack')
            self.assertNotIn('--enable-parent-pointer-read-cold', argv)
            self.assertEqual(timeout, 750 if case == 'timeout' else 30000 if case == 'foreign4096_limit' else 15000)
            self.assertEqual('--cold-fault' in argv, case in runner.FAULTS)

    def test_exact_synthetic_event_binding(self) -> None:
        meta = {key: 'Local\\XarPostloadCold41' + suffix for key, suffix in (
            ('go_event', 'Go'), ('cancel_event', 'Cancel'), ('audit_event', 'Audit'),
            ('finish_event', 'Finish'), ('fault_release_event', 'FaultRelease'))}
        runner.validate_meta_events(meta, 41)
        for key in meta:
            invalid = dict(meta)
            invalid[key] = invalid[key].replace('Cold41', 'Cold42')
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.validate_meta_events(invalid, 41)
        with self.assertRaises(ValueError):
            runner.validate_meta_events(meta, True)

    def test_scalar_parser_rejects_equal_but_wrong_types(self) -> None:
        self.assertIs(flag(True, 'flag'), True)
        self.assertIs(flag(False, 'flag'), False)
        for value in (0, 1, 'true', None, 1.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                flag(value, 'flag')
        with self.assertRaises(ValueError):
            strings(['a', 1], 'names')

    @staticmethod
    def refusal() -> tuple[list[JsonObject], dict[str, str], Identity]:
        meta = {'parent_schema': 'xar.maintenance.parent_postload.cold-meta.v1',
            'pid': '41', 'created': '134370000000000001', 'parent_postload': '65536',
            'subject_field_address': '131520', 'post_pc': '65562'}
        rows: list[JsonObject] = [
            {'kind': 'start', 'schema': 'xar.maintenance.parent_postload.raw.v1',
             'mode': 'player-parent-postload-execution-once-v1', 'machine_id': 'synthetic-machine',
             'synthetic': True, 'owner_binding': None, 'pid': 41, 'created': meta['created'],
             'entry': meta['parent_postload'], 'subject_field_address': meta['subject_field_address'],
             'post_pc': meta['post_pc']},
            {'kind': 'arm', 'success': False, 'saved_debug': [], 'readback': True,
             'armed_debug': ['0'] * 6, 'thread_id': 8, 'thread_generation': 1, 'thread_created': '134370000000000002'},
            {'kind': 'terminal', 'restored': True, 'detached': True, 'cleanup_complete': True,
             'pending_event': False, 'process_exited': False}]
        return rows, meta, Identity(pid=41, created=134370000000000001)

    def test_zero_arm_exception_uses_current_subject_field(self) -> None:
        rows, meta, identity = self.refusal()
        self.assertTrue(runner.synthetic_detached_cleanup_proven(rows, meta, identity, 1, True, 'synthetic-machine', True))
        for mutation in ('success', 'saved', 'pending', 'subject', 'unwaited', 'nonrefusal'):
            bad = copy.deepcopy(rows)
            if mutation == 'success': bad[1]['success'] = True
            elif mutation == 'saved': bad[1]['saved_debug'] = ['0'] * 6
            elif mutation == 'pending': bad[-1]['pending_event'] = True
            elif mutation == 'subject': bad[0]['subject_field_address'] = '131528'
            self.assertFalse(runner.synthetic_detached_cleanup_proven(bad, meta, identity, 1,
                mutation != 'unwaited', 'synthetic-machine', mutation != 'nonrefusal'), mutation)

    def test_full_six_audit_drift_remains_rejected(self) -> None:
        saved = [0, 0, 0, 0, 0xffff0ff0, 1024]
        before = [AuditRow(tid=8, created=134370000000000002, complete=True, eflags=514, dr=saved)]
        rows: list[JsonObject] = [{'kind': 'arm', 'success': True, 'readback': True,
            'thread_id': 8, 'thread_generation': 1, 'thread_created': '134370000000000002',
            'saved_debug': [str(value) for value in saved]}]
        result = runner.verify_audit(rows, before, copy.deepcopy(before))
        self.assertTrue(result['all_required_owned_DR_vectors_equal'])
        for slot in range(6):
            after = copy.deepcopy(before)
            after[0]['dr'][slot] ^= 1
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                runner.verify_audit(rows, before, after)

    def test_target_result_uses_decimal_u64_and_strict_warmup(self) -> None:
        row: JsonObject = dict(return_failures=0, audit_failures=0, foreign_body_calls=4096,
            target_body_calls=1, actual_body_calls='4097', other_access_calls='0', loaded_context='0',
            post_arithmetic_flags=0, worker_tid=0, occupied_warmup_calls=1)
        result = target_result(row)
        self.assertEqual(result.actual_body_calls, 4097)
        self.assertEqual(result.occupied_warmup_calls, 1)
        for key, value in (('actual_body_calls', 4097), ('occupied_warmup_calls', True), ('occupied_warmup_calls', 1.0)):
            bad = dict(row)
            bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                target_result(bad)

    def test_native_source_name_is_the_existing_exact_file(self) -> None:
        source = Path(runner.__file__).read_text()
        self.assertIn("'parent_postload_execution_once.inc'", source)
        self.assertNotIn("'parent_postload_once.inc'", source)
        self.assertNotIn("meta['watch_address']", source)


if __name__ == '__main__':
    unittest.main()
