"""Offline source regression; all pipe responses are synthetic in-process mocks."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from xar_autoplayer import optional_check_cadence_v1 as cadence
from xar_autoplayer import private_council_formal_consumer_v1 as consumer
from xar_autoplayer.bridge import council_private_transport_v1 as transport
from xar_autoplayer.bridge import service
from xar_autoplayer.bridge.driver import BridgeUnavailableError, StepPostconditionError


def frame():
    return dict(snapshot_id='native:100', revision=7, native_revision=100, date_raw=53349816,
                episode_run_id='synthetic-12', diagnostics=dict(connection_generation=2, bridge_pid=999),
                played_character=dict(character_id=12, alive=True), paused=True, map_ready=True,
                active_event=None, pending_character_interaction=None)


class FakeDriver:
    def __init__(self, directory, replies=('absent',), changed=False):
        self.state_dir = Path(directory)
        self.command_timeout_seconds = 0.2
        self.allow_private_council_action = True
        self.before = frame()
        self.requests = []
        self.replies = iter(replies)
        self.changed = changed
        self.endpoint = SimpleNamespace(send=self.requests.append)
        self.state = SimpleNamespace(wait_for_command_result=self.wait)
        self.query_calls = 0

    def take_internal_semantic_snapshot(self):
        result = copy.deepcopy(self.before)
        if self.changed and self.requests:
            result['date_raw'] += 24
        return result

    def wait(self, request_id, remaining):
        reply = next(self.replies)
        if reply == 'absent':
            return None
        if reply == 'pending':
            return dict(type='command_result', protocol_version=1, request_id=request_id, ok=True,
                        result=dict(private_council_transport=True, advertised=False, status='pending'))
        if reply == 'rejected':
            return dict(type='command_result', protocol_version=1, request_id=request_id,
                        ok=False, error='synthetic native negative')
        raise AssertionError(reply)

    def query_council_final_gates_private_v1(self, **kwargs):
        self.query_calls += 1
        return transport.query_council_private_v1(self, query_step=transport.PRIVATE_GATES_STEP,
                                                  timeout_seconds=0.2, **kwargs)


def planned():
    current = frame()
    return dict(snapshot_id=current['snapshot_id'], revision=current['revision'],
                plan=dict(selected_step='life-advance', phase='native_life_advance', reason='ordinary day'))


def run_plan(driver):
    return consumer.plan_council_private(driver, planned(), frame(), [], {'life-advance'})


class CouncilTechnicalDeferTests(unittest.TestCase):
    def test_transport_records_real_synthetic_request_and_absent_response(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            with self.assertRaises(BridgeUnavailableError) as caught:
                driver.query_council_final_gates_private_v1(expected_revision=7)
            diagnostic = caught.exception.council_planning_read_unavailable_v1
            self.assertEqual(diagnostic['transport_steps'][0]['native_request'], driver.requests[0])
            self.assertEqual(diagnostic['query_step'], transport.PRIVATE_GATES_STEP)
            self.assertIsNone(diagnostic['last_command_result'])
            self.assertEqual(diagnostic['command_result_presence'], 'absent_or_invalid')
            self.assertIs(diagnostic['business_submission'], False)

    def test_status_poll_retains_both_requests_and_existing_pending_result(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory, replies=('pending', 'absent'))
            with self.assertRaises(BridgeUnavailableError) as caught:
                driver.query_council_final_gates_private_v1(expected_revision=7)
            steps = caught.exception.council_planning_read_unavailable_v1['transport_steps']
            self.assertEqual([x['step'] for x in steps], [transport.PRIVATE_GATES_STEP, transport.PRIVATE_STATUS_STEP])
            self.assertEqual(steps[0]['command_result']['result']['status'], 'pending')
            self.assertIsNone(steps[1]['command_result'])

    def test_optional_planning_failure_keeps_life_and_preserves_counters(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            current = cadence.frame(driver.before)
            cadence.record(Path(directory), 'council', (current[0], current[1]-24, current[2]-1), actual_action=False)
            result = run_plan(driver)
            self.assertEqual(result['plan']['selected_step'], 'life-advance')
            self.assertIs(result['plan']['council_observation_consumed'], False)
            self.assertEqual(result['plan']['council_observation_status'], 'technical_unavailable')
            defer = result['plan']['council_technical_defer']
            self.assertIs(defer['no_action_counter_incremented'], False)
            row = cadence._load(Path(directory), current[0])['domains']['council']
            self.assertEqual(row['consecutive_no_action'], 1)
            self.assertIsNone(row['last_actual_action_frame'])
            self.assertEqual(row['next_due_date_raw'], current[1]+720)
            self.assertEqual(json.loads(Path(defer['evidence_path']).read_text())['transport_steps'][0]['native_request'], driver.requests[0])
            self.assertIsNone(consumer.read_council_ledger(Path(directory))['pending'])

    def test_existing_service_result_observer_does_not_increment_noop(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            result = run_plan(driver)
            current = cadence.frame(driver.before)
            service._optional_check_result(driver, 'council', current, 'life-advance', result)
            row = cadence._load(Path(directory), current[0])['domains']['council']
            self.assertEqual(row['consecutive_no_action'], 0)
            self.assertEqual(row['next_due_date_raw'], current[1]+720)

    def test_existing_service_cadence_skips_query_until_month_expires(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            result = run_plan(driver)
            current = cadence.frame(driver.before)
            deferred = service._optional_check_due(driver, 'council', (current[0], current[1]+24, current[2]+1))
            self.assertEqual(deferred['status'], 'technical_read_unavailable_deferred')
            self.assertEqual(deferred['remaining_game_days'], 29)
            self.assertEqual(driver.query_calls, 1)
            self.assertIsNone(service._optional_check_due(driver, 'council', (current[0], current[1]+720, current[2]+30)))

    def test_native_negative_response_is_preserved_as_raw_evidence(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory, replies=('rejected',))
            result = run_plan(driver)
            evidence = json.loads(Path(result['plan']['council_technical_defer']['evidence_path']).read_text())
            self.assertIs(evidence['last_command_result']['ok'], False)
            self.assertEqual(evidence['last_command_result']['error'], 'synthetic native negative')
            self.assertEqual(evidence['command_result_presence'], 'present')

    def test_changed_frame_remains_halted_without_defer(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory, changed=True)
            with self.assertRaises(BridgeUnavailableError):
                run_plan(driver)
            self.assertFalse((Path(directory)/cadence.PATH_NAME).exists())

    def test_plain_error_without_query_diagnostic_remains_halted(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            with patch.object(consumer, '_query_position', side_effect=BridgeUnavailableError('private council operation command_result is unavailable')):
                with self.assertRaises(BridgeUnavailableError):
                    run_plan(driver)
            self.assertFalse((Path(directory)/cadence.PATH_NAME).exists())

    def test_unknown_action_timeout_remains_halted(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            error = StepPostconditionError('private council submission result unavailable; action state unknown',
                                          selected_step=transport.PRIVATE_ASSIGN_STEP, step_result={})
            with patch.object(consumer, '_query_position', side_effect=error):
                with self.assertRaises(StepPostconditionError):
                    run_plan(driver)
            self.assertFalse((Path(directory)/cadence.PATH_NAME).exists())

    def test_pending_assignment_is_retained_and_query_not_attempted(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            pending = dict(episode_run_id=driver.before['episode_run_id'], action_request_id='existing-action', action_ack=None)
            consumer._write(Path(directory), {'schema': consumer._SCHEMA, 'pending': pending, 'applied': None})
            result = run_plan(driver)
            self.assertEqual(result['plan']['phase'], 'council_pending_later_frame')
            self.assertIsNone(result['plan']['selected_step'])
            self.assertEqual(consumer.read_council_ledger(Path(directory))['pending'], pending)
            self.assertEqual(driver.query_calls, 0)
            self.assertFalse((Path(directory)/cadence.PATH_NAME).exists())

    def test_success_and_normal_three_noop_cooldown_contract_unchanged(self):
        with TemporaryDirectory() as directory:
            current = cadence.frame(frame())
            for index in range(3):
                cadence.record(Path(directory), 'council', (current[0], current[1]+index*24, current[2]+index), actual_action=False)
            deferred = cadence.deferred(Path(directory), 'council', (current[0], current[1]+72, current[2]+3))
            self.assertEqual(deferred['status'], 'cooldown_after_three_no_action_checks')
            self.assertEqual(deferred['consecutive_no_action'], 0)

    def test_real_action_can_clear_technical_defer_without_noop_credit(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            run_plan(driver)
            current = cadence.frame(frame())
            row = cadence.record(Path(directory), 'council', current, actual_action=True)
            self.assertIsNone(row['next_due_date_raw'])
            self.assertNotIn('technical_defer', row)
            self.assertEqual(row['last_actual_action_frame'], list(current[1:]))


if __name__ == '__main__':
    unittest.main()
