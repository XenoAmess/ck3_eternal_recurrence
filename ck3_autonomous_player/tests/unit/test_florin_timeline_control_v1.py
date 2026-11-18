"""Actual C++ ACKs through the shared primitive; authored inert world, no CK3."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.timeline_control_ack_v1 import (
    FLORIN_CLOCK_CAPABILITY, FLORIN_CLOCK_STEPS, florin_date_arm_spec_v1,
    normalize_florin_clock_ack_v1, require_florin_control_ready_v1)
from xar_autoplayer.bridge.version_identity import florin_full_source
from test_normal_exit_core1210_v1 import CoreDriver, RESOURCES

ARM = 'research-arm-tactical-daily-sentinel-v1-24000-to-24024-speed-5-mode-terminal-a-0'
STATUS = 'research-query-tactical-daily-sentinel-v1'


class ClockDriver(CoreDriver):
    _execute_primitive_step = NativeHeadlessGameplayDriver._execute_primitive_step
    _verify_idempotent_map_control_postcondition = NativeHeadlessGameplayDriver._verify_idempotent_map_control_postcondition

    def __init__(self, directory):
        super().__init__(directory)
        self.snapshot.update(date_raw=24000, speed=5, active_wars=[], player_armies=[])
        self.snapshot['has_active_event'] = False
        self._request_sequence = 0
        self.ack_file = 'full-clock-ack-submitted01.json'
        self.fail_send = False
        self.status_generation = 1

    def capabilities(self):
        return {'bridge_capabilities': [FLORIN_CLOCK_CAPABILITY,
            'game.command.research-arm-tactical-daily-sentinel-v1-N',
            'game.command.research-query-tactical-daily-sentinel-v1'],
            'action_steps': list(FLORIN_CLOCK_STEPS)}

    def _h3937_date_hold_active(self, snapshot=None): return False
    def take_internal_semantic_snapshot(self): return self.take_snapshot()
    def take_snapshot_without_native_command_history(self): return self.take_snapshot()

    def send(self, request, **kwargs):
        self.sent.append(copy.deepcopy(request))
        if self.fail_send: raise OSError('authored missing ACK after possible dispatch')

    def wait_for_command_result(self, request_id, timeout):
        step = self.sent[-1]['step']
        if step in (ARM, STATUS):
            row = json.loads((RESOURCES / 'date-arm1210/armed-generation1.json').read_text())
            if step == STATUS:
                row['result']['tactical_daily_sentinel']['generation'] = self.status_generation
        else:
            row = json.loads((RESOURCES / 'newnative/full-clock1210' / self.ack_file).read_text())
        row['request_id'] = request_id; row['result']['step'] = step
        return row


class FlorinClockTests(unittest.TestCase):
    def test_actual_cpp_pause_and_save_ack_through_primitive_exact_claims(self):
        for step, fixture in [('pause-map','full-clock-ack-submitted01.json'),
                              ('save-checkpoint','full-clock-ack-save01.json')]:
            with self.subTest(step=step), tempfile.TemporaryDirectory() as temporary:
                driver = ClockDriver(Path(temporary)); driver.ack_file = fixture
                if step == 'save-checkpoint': driver.snapshot['date_raw'] = 123456
                result = driver._execute_primitive_step(step, expected_revision=72)
                self.assertEqual(result['queue_status'], 'submitted')
                self.assertIs(result['physical_save_confirmed'], False)
                request = driver.sent[0]
                self.assertEqual(request['expected_revision'], 11)
                claim = request['full_snapshot_clock_control']
                self.assertEqual(claim['native_revision'], 11)
                self.assertEqual(claim['snapshot_id'], 'native:11')
                self.assertEqual(set(claim), {'schema','game_version','executable_sha256','adapter_id','backend',
                    'snapshot_id','native_revision','deadline_unix_ms'})
                self.assertEqual(len(list(Path(temporary).rglob('*.qualified.json'))), 1)
                if step == 'save-checkpoint': self.assertEqual(result['submission']['sequence'], 19)

    def test_unknown_save_consumes_claim_and_blocks_new_revision_connection_and_actions(self):
        for fixture in ['full-clock-ack-indeterminate01.json','full-clock-ack-attempted-rejected01.json']:
            with self.subTest(fixture=fixture), tempfile.TemporaryDirectory() as temporary:
                driver = ClockDriver(Path(temporary)); driver.ack_file = fixture
                with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('pause-map')
                driver.snapshot.update(revision=73,native_revision=12,snapshot_id='native:12')
                driver.snapshot['diagnostics']['connection_generation'] = 9
                with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('save-checkpoint')
                self.assertEqual(len(driver.sent), 1)
                self.assertEqual(len(list(Path(temporary).rglob('*.response.json'))), 1)

    def test_missing_ack_survives_driver_recreation_and_forbids_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = ClockDriver(Path(temporary)); driver.fail_send = True
            with self.assertRaises(OSError): driver._execute_primitive_step('save-checkpoint')
            resumed = ClockDriver(Path(temporary))
            with self.assertRaises(BridgeUnavailableError): resumed._execute_primitive_step('pause-map')
            self.assertEqual(resumed.sent, [])

    def test_resume_requires_qualified_same_run_arm_and_independent_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = ClockDriver(Path(temporary))
            with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('resume-map')
            self.assertEqual(driver.sent, [])
            driver._execute_primitive_step(ARM, required_capability='game.command.research-arm-tactical-daily-sentinel-v1-N')
            self.assertIn('date_sentinel_arm', driver.sent[0])
            result = driver._execute_primitive_step('resume-map')
            self.assertTrue(result['accepted'])
            self.assertEqual([row['step'] for row in driver.sent], [ARM, STATUS, 'resume-map'])
            with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('resume-map')
            self.assertEqual(len(driver.sent), 3)
        with tempfile.TemporaryDirectory() as temporary:
            driver = ClockDriver(Path(temporary))
            driver._execute_primitive_step(ARM, required_capability='game.command.research-arm-tactical-daily-sentinel-v1-N')
            driver.status_generation = 2
            with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('resume-map')
            self.assertEqual([row['step'] for row in driver.sent], [ARM, STATUS])

    def test_arm_rejects_wrong_scope_wars_armies_and_unbounded_aliases_before_write(self):
        for changed in [{'active_wars':[{}]}, {'player_armies':[{}]}, {'date_raw':24024}, {'speed':4}]:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                driver = ClockDriver(Path(temporary)); driver.snapshot.update(changed)
                with self.assertRaises(BridgeUnavailableError):
                    driver._execute_primitive_step(ARM, required_capability='game.command.research-arm-tactical-daily-sentinel-v1-N')
                self.assertEqual(driver.sent, [])
        for value in [ARM+'-', ARM.replace('a-0','a-1-99'), ARM.replace('24024','25000'), ARM.replace('24000','024000')]:
            with self.subTest(value=value), self.assertRaises(ValueError): florin_date_arm_spec_v1(value)

    def test_actual_cpp_expired_ack_is_preserved_rejected_and_not_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = ClockDriver(Path(temporary)); driver.ack_file = 'full-clock-ack-expired01.json'
            with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('pause-map')
            require_florin_control_ready_v1(driver._native_driver_state_path(), florin_full_source(driver.snapshot,72))
            self.assertEqual(len(list(Path(temporary).rglob('*.qualified.json'))),1)

    def test_arm_permission_does_not_cross_connection_actor_or_allocated_run(self):
        for change in ('connection','actor','episode'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                driver=ClockDriver(Path(temporary))
                driver._execute_primitive_step(ARM,required_capability='game.command.research-arm-tactical-daily-sentinel-v1-N')
                if change=='connection': driver.snapshot['diagnostics']['connection_generation']=9
                elif change=='actor': driver.snapshot['played_character']['character_id']=54
                else: driver.snapshot['episode_run_id']='other-allocated-run'
                with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('resume-map')
                self.assertEqual(len(driver.sent),1)

    def test_save_wrong_date_or_forged_completion_is_unknown_and_never_retried(self):
        for defect in ('wrong_date','physical_save'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temporary:
                driver=ClockDriver(Path(temporary));driver.ack_file='full-clock-ack-save01.json'
                if defect=='physical_save':
                    actual=driver.wait_for_command_result
                    def malformed(request_id,timeout):
                        frame=actual(request_id,timeout)
                        frame['result']['physical_save_confirmed']=True
                        return frame
                    driver.wait_for_command_result=malformed
                with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('save-checkpoint')
                with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('set-speed-4')
                self.assertEqual(len(driver.sent),1)

    def test_qualified_receipt_identity_is_checked_before_another_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver=ClockDriver(Path(temporary));driver._execute_primitive_step('set-speed-3')
            path=next(Path(temporary).rglob('*.qualified.json'))
            row=json.loads(path.read_text());row['request_id']='foreign-request'
            path.write_text(json.dumps(row))
            with self.assertRaises(BridgeUnavailableError): driver._execute_primitive_step('save-checkpoint')
            self.assertEqual(len(driver.sent),1)

    def test_exact_day_observes_existing_florin_speed_without_redundant_setter(self):
        from xar_autoplayer.bridge.exact_day_speed_configuration_v1 import prepare_exact_day_speed_v1
        with tempfile.TemporaryDirectory() as temporary:
            driver=ClockDriver(Path(temporary));actions=[]
            observed=prepare_exact_day_speed_v1(driver,driver.take_snapshot(),speed=5,actions=actions)
            self.assertEqual(driver.sent,[])
            self.assertEqual(observed['speed'],5)
            self.assertIsNone(actions[0]['result']['accepted'])
            self.assertIs(actions[0]['result']['submitted'],False)
            self.assertTrue(actions[0]['result']['observation_proof']['observation_only'])
            self.assertEqual(actions[0]['result']['observation_proof']['played_character_id'],-2130706431)
            starting=driver.take_snapshot();driver.snapshot['speed']=4
            with self.assertRaises(BridgeUnavailableError):
                prepare_exact_day_speed_v1(driver,starting,speed=5,actions=actions)
            self.assertEqual(driver.sent,[])

    def test_complete_new_speed_observation_function_scope_is_strict(self):
        import ast
        from mypy import api
        from unittest.mock import patch
        import xar_autoplayer.bridge.exact_day_speed_configuration_v1 as speed_source
        tree=ast.parse(Path(speed_source.__file__).read_text(encoding='utf-8'))
        names={'FlorinSpeedObservationDriverV1','_florin_same_speed_v1'}
        nodes=[node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
        self.assertEqual(len(nodes),len(names))
        prefix='''from __future__ import annotations
from typing import Protocol
from xar_autoplayer.bridge.version_identity import florin_full_source
from xar_autoplayer.bridge.driver import BridgeUnavailableError
'''
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'actual_florin_speed_scope.py'
            path.write_text(prefix+ast.unparse(ast.Module(body=nodes,type_ignores=[])),encoding='utf-8')
            source=Path(__file__).resolve().parents[2]/'src'
            with patch.dict('os.environ',{'MYPYPATH':str(source)}):
                stdout,stderr,code=api.run(['--strict','--strict-equality','--follow-imports=silent',
                    '--no-incremental','--cache-dir','nul',str(path)])
        self.assertEqual(code,0,stdout+stderr)


if __name__ == '__main__': unittest.main(verbosity=2)
