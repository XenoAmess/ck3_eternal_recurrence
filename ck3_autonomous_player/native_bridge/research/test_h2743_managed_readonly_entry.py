"""Deterministic current-path checks; no CK3 or authoritative bus access."""
from __future__ import annotations

import copy
from contextlib import contextmanager
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge import h2743_exit_readonly_transport as transport
from xar_autoplayer import h2743_exit_readonly_live as live


def paused_frame():
    return {'map_ready': True, 'paused': True, 'date_raw': 53217264,
            'episode_run_id': 'native-29829-2bc2d599f7f9', 'snapshot_id': 'native:3',
            'revision': 4, 'native_revision': 3,
            'played_character': {'character_id': 29829},
            'diagnostics': {'connection_generation': 1},
            'active_wars': [{'war_id': 16777231, 'player_side': 'defender',
                             'player_is_primary_war_leader': True,
                             'primary_opponent_character_id': 30097,
                             'targeted_title_ids': [2128]}]}


class FakeDriver:
    instances = []

    def __init__(self, *args, **kwargs):
        self.frame = paused_frame()
        self.calls = []
        self.closed = False
        self.instances.append(self)
        self.envelope = {'step': transport.BASELINE_STEP, 'accepted': True,
                         'status': 'baseline_only', 'query_sequence': 1,
                         'defender_de_jure_exit_terms_v1': {'synthetic': True}, 'backend_id': 'native'}

    def take_internal_semantic_snapshot(self):
        return copy.deepcopy(self.frame)

    take_snapshot = take_internal_semantic_snapshot

    def _execute_primitive_step(self, step, **options):
        self.calls.append((step, options))
        return copy.deepcopy(self.envelope)

    def execute_step(self, step, **options):
        self.calls.append((step, options))
        return {'accepted': True, 'status': 'available', 'war_termination_options': {'war_id': 16777231}}

    def close(self):
        self.closed = True


class FakeKeeper:
    def __init__(self, fail_live=False):
        self.abort = threading.Event()
        self.starts = self.stops = self.gates = 0
        self.fail_live = fail_live

    def start(self):
        self.starts += 1

    def refresh(self):
        pass

    def require_live(self):
        if self.fail_live:
            raise RuntimeError('synthetic lease expired')

    @contextmanager
    def process_create_gate(self):
        self.gates += 1
        yield

    def stop(self):
        self.stops += 1

    def report(self):
        return {'failure': 'expired' if self.fail_live else None}


class H2743ManagedQueryTests(unittest.TestCase):
    def test_native_query_uses_exact_capability_and_frame(self):
        driver = FakeDriver()
        normalized = {'border_raid_storage_candidate_v1': {'status': 'structural_candidate_only'},
                      'material_complete': False, 'action_literal': None}
        with patch.object(transport, 'normalize_defender_dejure_exit_terms_v1', return_value=normalized):
            result = transport.query_h2743_exit_baseline(driver, expected_frame=paused_frame())
        self.assertEqual(driver.calls, [(transport.BASELINE_STEP,
            {'expected_revision': 4, 'required_capability': transport.CAPABILITY,
             'internal_semantic_snapshot': True})])
        self.assertEqual(result['queried_connection_generation'], 1)
        self.assertFalse(result['defender_de_jure_exit_terms_v1']['material_complete'])

    def test_wrong_actor_or_date_sends_no_query(self):
        for change in ({'date_raw': 53217288}, {'played_character': {'character_id': 30097}}):
            with self.subTest(change=change):
                driver = FakeDriver()
                driver.frame.update(change)
                with self.assertRaises(BridgeUnavailableError):
                    transport.query_h2743_exit_baseline(driver, expected_frame=paused_frame())
                self.assertEqual(driver.calls, [])

    def test_loading_frame_waits_without_query(self):
        frame = paused_frame()
        frame['played_character'] = None
        frame['active_wars'] = []
        self.assertIsNone(transport.target_frame(frame))

    def test_native_query_rejects_stale_claim_before_wire(self):
        driver = FakeDriver()
        claim = paused_frame()
        claim['diagnostics']['connection_generation'] = 2
        with self.assertRaises(BridgeUnavailableError):
            transport.query_h2743_exit_baseline(driver, expected_frame=claim)
        self.assertEqual(driver.calls, [])

    def test_unavailable_storage_is_not_promoted(self):
        driver = FakeDriver()
        normalized = {'border_raid_storage_candidate_v1': {'status': 'unavailable'}}
        with patch.object(transport, 'normalize_defender_dejure_exit_terms_v1', return_value=normalized):
            with self.assertRaises(BridgeUnavailableError):
                transport.query_h2743_exit_baseline(driver, expected_frame=paused_frame())


class H2743ManagedSessionTests(unittest.TestCase):
    def run_fake_session(self, *, fail_live=False, cleanup=True):
        from xar_autoplayer.bridge import native_driver
        from xar_autoplayer import native_session, runtime
        keeper, calls = FakeKeeper(fail_live), []

        def fake_session(spec, **kwargs):
            calls.append(kwargs)
            with kwargs['before_process_create']():
                pass
            if not kwargs['stop_event'].wait(5):
                raise RuntimeError('test entry failed to stop native session')
            return {'shutdown': {'cleanup_proven': cleanup}}

        normalized = {'border_raid_storage_candidate_v1': {'status': 'structural_candidate_only'},
                      'material_complete': False, 'action_literal': None}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            spec = SimpleNamespace(state_dir=output / 'state', profile_dir=output / 'profile')
            config = SimpleNamespace(pipe_name='synthetic-pipe')
            with patch.object(native_driver, 'NativeHeadlessGameplayDriver', FakeDriver), \
                 patch.object(native_session, 'native_session', fake_session), \
                 patch.object(runtime, 'ck3_process_inventory', return_value={'processes': []}), \
                 patch.object(transport, 'normalize_defender_dejure_exit_terms_v1', return_value=normalized):
                result = live.run_owned_read(spec=spec, config=config, keeper=keeper,
                                             output=output, timeout_seconds=1)
            artifacts = sorted(path.name for path in output.iterdir())
        return result, keeper, calls, FakeDriver.instances[-1], artifacts

    def test_current_session_receives_single_owned_gate_and_cleans_up(self):
        result, keeper, calls, driver, artifacts = self.run_fake_session()
        self.assertEqual(result['status'], 'READONLY_BASELINE_AVAILABLE_MATERIAL_PENDING')
        self.assertEqual((keeper.starts, keeper.stops, keeper.gates), (1, 1, 1))
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0]['stop_event'], keeper.abort)
        self.assertEqual(calls[0]['before_process_create'], keeper.process_create_gate)
        self.assertTrue(driver.closed)
        self.assertEqual([step for step, _ in driver.calls],
                         [transport.BASELINE_STEP, transport.OPTIONS_STEP, transport.BASELINE_STEP])
        self.assertEqual(result['query_attempts'], 3)
        self.assertIsNone(result['action_literal'])
        self.assertFalse(result['material_complete'])
        self.assertEqual(artifacts, ['after-frame.json', 'baseline-1.json', 'baseline-2.json',
                                    'before-frame.json', 'termination-options.json'])

    def test_lease_failure_prevents_queries_and_stops_session(self):
        result, keeper, calls, driver, _ = self.run_fake_session(fail_live=True)
        self.assertEqual(result['status'], 'RED')
        self.assertEqual(driver.calls, [])
        self.assertEqual(result['query_attempts'], 0)
        self.assertTrue(keeper.abort.is_set())
        self.assertEqual(keeper.stops, 1)
        self.assertTrue(result['session_thread_exited'])

    def test_successful_queries_without_cleanup_are_red(self):
        result, _, _, _, _ = self.run_fake_session(cleanup=False)
        self.assertEqual(result['query_attempts'], 3)
        self.assertEqual(result['status'], 'RED')
        self.assertFalse(result['managed_cleanup_verified'])

    def test_failed_source_check_preserves_new_red_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory) / 'attempt'
            with patch.object(live, 'verify_pair', side_effect=ValueError('synthetic source mismatch')):
                with self.assertRaises(ValueError):
                    live.main(['--no-launch', '--pair-manifest', 'pair.json',
                               '--native-source-checkout', '.', '--game-dir', '.',
                               '--attempt-dir', str(attempt)])
            result = live.read_object(attempt / 'report.json')
        self.assertEqual(result['status'], 'RED')
        self.assertIn('synthetic source mismatch', result['error'])


if __name__ == '__main__':
    unittest.main()
