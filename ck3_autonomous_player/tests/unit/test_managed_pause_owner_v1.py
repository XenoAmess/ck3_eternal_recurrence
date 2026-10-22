"""Actual pause recovery with the R7 campaign frame and authored transport."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.managed_pause_owner_v1 import managed_pause_owner_v1
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _NativeCommandRejectedError
from xar_autoplayer.bridge.driver import StepPostconditionError
from test_native_bridge_driver import FakeEndpoint


def captured_frame() -> dict[str, object]:
    path = Path(__file__).resolve().parents[3] / 'mod_living_artifacts/docs/evidence/r7-running-pause-frame.json'
    value = json.loads(path.read_bytes())
    frame: object = value['projection']
    if not isinstance(frame, dict) or any(type(key) is not str for key in frame):
        raise ValueError('Actual frame projection is malformed')
    return {key: item for key, item in frame.items()}


def authored_successor(frame: dict[str, object], *, paused: bool) -> dict[str, object]:
    value = copy.deepcopy(frame)
    for key, amount in (('revision', 1), ('native_revision', 1), ('date_raw', 24)):
        previous = value[key]
        if type(previous) is not int or not isinstance(previous, int):
            raise ValueError('Captured frame lacks an exact native number')
        value[key] = previous + amount
    value['paused'] = paused
    return value


class PauseTransportDriver(NativeHeadlessGameplayDriver):
    """Only snapshot delivery and primitive wire responses are authored."""
    def __init__(self, frame: dict[str, object], refreshed: dict[str, object]) -> None:
        endpoint = FakeEndpoint()
        super().__init__(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        self.frame = copy.deepcopy(frame)
        self.refreshed = copy.deepcopy(refreshed)
        self.dispatches: list[dict[str, object]] = []

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.frame)

    def _execute_primitive_step(self, step: str, **kwargs: object) -> dict[str, object]:
        self.dispatches.append({'step': step, **kwargs})
        if len(self.dispatches) == 1:
            self.frame = copy.deepcopy(self.refreshed)
            raise _NativeCommandRejectedError('CK3 map state is unavailable', native_request_id='authored-rejected-pause-1')
        self.frame = authored_successor(self.frame, paused=True)
        return {'step': step, 'accepted': True, 'status': 'submitted', 'backend_id': 'native-headless'}


class ManagedPauseOwnerTests(unittest.TestCase):
    def test_actual_r7_campaign_without_episode_gets_its_own_validated_owner(self) -> None:
        frame = captured_frame()
        self.assertNotIn('episode_run_id', frame)
        actual = managed_pause_owner_v1(frame)
        self.assertIsNotNone(actual)
        self.assertEqual(actual, managed_pause_owner_v1(authored_successor(frame, paused=True)))

    def test_real_failed_pause_path_uses_one_bound_idempotent_retry(self) -> None:
        frame = captured_frame()
        driver = PauseTransportDriver(frame, authored_successor(frame, paused=False))
        result = driver._execute_generic_pause_map(expected_revision=1)
        recovery = result['map_control_recovery']
        if not isinstance(recovery, dict):
            self.fail('Actual recovery metadata missing')
        self.assertIs(recovery['postcondition_verified'], True)
        self.assertEqual([row['step'] for row in driver.dispatches], ['pause-map', 'pause-map'])
        self.assertIsNone(driver.dispatches[1]['expected_revision'])
        self.assertIs(driver.dispatches[1]['internal_semantic_snapshot'], True)
        self.assertIs(driver.frame['paused'], True)

    def test_already_paused_fresh_frame_does_not_dispatch_again(self) -> None:
        frame = captured_frame()
        driver = PauseTransportDriver(frame, authored_successor(frame, paused=True))
        result = driver._execute_generic_pause_map(expected_revision=1)
        self.assertEqual(result['status'], 'already_paused')
        self.assertEqual(len(driver.dispatches), 1)

    def test_owner_actor_transport_run_or_popup_drift_never_retries(self) -> None:
        mutations = ('pid', 'generation', 'actor', 'run_id', 'pipe', 'state_dir', 'argv_sha', 'popup')
        for change in mutations:
            frame = captured_frame()
            refreshed = authored_successor(frame, paused=False)
            diagnostic = refreshed['diagnostics']
            run = refreshed['managed_campaign_run_binding']
            actor = refreshed['played_character']
            if not all(isinstance(value, dict) for value in (diagnostic, run, actor)):
                self.fail('Captured metadata missing')
            if not isinstance(diagnostic, dict) or not isinstance(run, dict) or not isinstance(actor, dict):
                raise AssertionError('Native objects required')
            if change == 'pid': diagnostic['bridge_pid'] = 77
            elif change == 'generation': diagnostic['connection_generation'] = 77
            elif change == 'actor': actor['character_id'] = 77
            elif change == 'run_id': run['run_id'] = 'other-run'
            elif change == 'pipe': run['bridge_pipe'] = 'other-pipe'
            elif change == 'state_dir': run['state_dir'] = 'other-state'
            elif change == 'argv_sha': run['frozen_argv_sha256'] = 'f' * 64
            else: refreshed['active_event'] = {'instance_id': 99}
            driver = PauseTransportDriver(frame, refreshed)
            with self.subTest(change=change), self.assertRaises(StepPostconditionError):
                driver._execute_generic_pause_map(expected_revision=1)
            self.assertEqual(len(driver.dispatches), 1)

    def test_equal_wrong_types_missing_fields_and_wrong_build_rejected(self) -> None:
        for wrong in (True, 1.0):
            frame = captured_frame()
            frame['local_player_id'] = wrong
            self.assertIsNone(managed_pause_owner_v1(frame))
        frame = captured_frame()
        del frame['managed_campaign_run_binding']
        self.assertIsNone(managed_pause_owner_v1(frame))
        frame = captured_frame()
        diagnostic = frame['diagnostics']
        if not isinstance(diagnostic, dict) or not isinstance(diagnostic['hello'], dict):
            self.fail('Actual hello missing')
        diagnostic['hello']['expected_ck3_sha256'] = 'a' * 64
        self.assertIsNone(managed_pause_owner_v1(frame))


if __name__ == '__main__':
    unittest.main()
