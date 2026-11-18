"""Actual Core ACK producer -> existing driver/service/public codec; no Game."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import normal_exit_map_driver_v1 as route
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _semantic_snapshot_from_frame
from xar_autoplayer.bridge.normal_exit_contract_v1 import (
    CORE_EXIT_CAPABILITY, CORE_EXIT_ROUTE, CORE_EXIT_EXE_SHA256, normalize_core_exit_ack_v1)
from xar_autoplayer.bridge.normal_exit_public_wire_v2 import (
    normal_exit_public_result_v2, parse_normal_exit_public_result_v2)
from xar_autoplayer.bridge.service import GameplayBridgeService
from test_normal_exit_process_observer_v1 import FakeApi

REPO = Path(__file__).resolve().parents[3]
RESOURCES = REPO / 'java/ck3-control/native-transport/src/test/resources'


class CoreDriver:
    query_normal_exit_context_v1 = NativeHeadlessGameplayDriver.query_normal_exit_context_v1
    request_normal_exit_v1 = NativeHeadlessGameplayDriver.request_normal_exit_v1
    observe_normal_exit_v1 = NativeHeadlessGameplayDriver.observe_normal_exit_v1

    def __init__(self, directory: Path):
        self.path = directory; self.api = FakeApi(); self.endpoint = self; self.state = self
        self.normal_exit_process_api_factory = lambda: self.api
        self.normal_exit_managed_profile = {'normal_exit_source_inventory': {'path': 'fixture', 'sha256': 'b'*64},
            'game_version':'1.21.0', 'guard':{'target':{'executable_sha256':CORE_EXIT_EXE_SHA256}}}
        self.command_timeout_seconds = 0.01; self.sent = []; self.snapshots = 0
        self.dead = False; self.fail_send = False; self.pending = False; self.invalid_ack = False
        raw = json.loads((RESOURCES / 'newnative/full1210/full-snapshot-producer-102.json').read_text())
        self.snapshot = _semantic_snapshot_from_frame(raw)
        self.snapshot.update({'revision': 72, 'native_revision': 11, 'snapshot_id': 'native:11', 'episode_run_id': 'fixture-core-run',
            'diagnostics': {'bridge_pid': 43, 'connection_generation': 8,
                'hello': {'pid': 43, 'ck3_build_match': True, 'game_adapter_id': 'ck3-1.21.0-msvc-x64',
                    'expected_ck3_version': '1.21.0', 'expected_ck3_sha256': CORE_EXIT_EXE_SHA256}}})

    def _native_driver_state_path(self): return self.path / 'driver-state.json'
    def capabilities(self): return {'bridge_capabilities': [CORE_EXIT_CAPABILITY]}
    def take_snapshot(self):
        if self.dead: raise AssertionError('No live read after original terminal dispatch')
        self.snapshots += 1; return copy.deepcopy(self.snapshot)
    def send(self, request):
        self.sent.append(copy.deepcopy(request))
        if not self.pending:
            self.dead = True; self.api.wait_result = 0; self.api.code = 0
        if self.fail_send: raise OSError('software transport failure after possible dispatch')
    def wait_for_command_result(self, request_id, timeout):
        ack = json.loads((RESOURCES / 'native1210/application-exit-producer-ack01.json').read_text())
        ack['request_id'] = request_id
        if self.invalid_ack: ack['result']['normal_exit_confirmed'] = True
        return ack


class CoreExitTests(unittest.TestCase):
    def source(self):
        return patch.object(route, 'verify_source_inventory_v1', return_value={'source_inventory_sha256': 'b'*64})

    def test_exact_cpp_ack_to_driver_service_public_wire_and_natural_os_zero(self):
        with tempfile.TemporaryDirectory() as temporary, self.source():
            driver = CoreDriver(Path(temporary)); service = GameplayBridgeService(driver)
            query = service.query_normal_exit_context_v1(expected_revision=72)
            self.assertEqual(query['route'], CORE_EXIT_ROUTE); self.assertEqual(driver.sent, [])
            before = driver.snapshots
            result = service.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=query['exit_context_signature'])
            self.assertEqual(driver.snapshots, before+1); self.assertEqual(len(driver.sent), 1)
            packet = driver.sent[0]
            self.assertEqual(packet['step'], 'normal-exit-application-v1'); self.assertEqual(packet['expected_revision'], 0)
            self.assertEqual(packet['core_application_exit']['played_character_id'], -2130706431)
            self.assertNotIn('normal-exit-map-v1', json.dumps(packet))
            self.assertTrue(result['typed_normal_exit_observed']); self.assertTrue(result['process_exit_observed'])
            self.assertFalse(result['autosave_verified']); self.assertFalse(result['observer_retained'])
            wire = normal_exit_public_result_v2(result)
            self.assertIs(type(wire['process_creation_filetime_100ns']), str)
            self.assertEqual(parse_normal_exit_public_result_v2(wire).to_memory(), result)

    def test_missing_ack_preserves_unknown_original_claim_even_when_os_zero(self):
        with tempfile.TemporaryDirectory() as temporary, self.source():
            driver = CoreDriver(Path(temporary)); query = driver.query_normal_exit_context_v1(expected_revision=72)
            driver.fail_send = True
            result = driver.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=query['exit_context_signature'])
            self.assertTrue(result['process_exit_observed']); self.assertFalse(result['typed_normal_exit_observed'])
            self.assertIsNone(result['native_observation']); self.assertTrue(result['claim_consumed'])
            self.assertEqual(len(driver.sent), 1)
            driver.dead = False
            again = driver.query_normal_exit_context_v1(expected_revision=72)
            with self.assertRaises(BridgeUnavailableError):
                driver.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                    expected_exit_context_signature=again['exit_context_signature'])
            self.assertEqual(len(driver.sent), 1)

    def test_pending_retains_original_handle_then_read_only_observer_proves_exit(self):
        with tempfile.TemporaryDirectory() as temporary, self.source():
            driver = CoreDriver(Path(temporary)); driver.pending = True
            query = driver.query_normal_exit_context_v1(expected_revision=72)
            result = driver.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=query['exit_context_signature'])
            self.assertTrue(result['observer_retained']); self.assertFalse(result['process_exit_observed'])
            before = driver.snapshots
            with self.assertRaises(BridgeUnavailableError): driver.query_normal_exit_context_v1(expected_revision=72)
            self.assertEqual(driver.snapshots, before)
            driver.api.wait_result = 0; driver.api.code = 0; driver.dead = True
            observed = GameplayBridgeService(driver).observe_normal_exit_v1()
            self.assertTrue(observed['typed_normal_exit_observed']); self.assertEqual(observed['native_submission_count'], 0)
            self.assertEqual(driver.snapshots, before); self.assertEqual(len(driver.sent), 1)
            parse_normal_exit_public_result_v2(normal_exit_public_result_v2(observed))

    def test_no_gui_preparation_phase_or_save_integrity_from_ack(self):
        raw = json.loads((RESOURCES / 'native1210/application-exit-producer-ack01.json').read_text())['result']
        for key in ('normal_exit_confirmed', 'complete_snapshot', 'physical_save_confirmed'):
            changed = {**raw, key: True}
            with self.subTest(key=key), self.assertRaises(ValueError): normalize_core_exit_ack_v1(changed)
        with tempfile.TemporaryDirectory() as temporary, self.source():
            driver = CoreDriver(Path(temporary)); query = driver.query_normal_exit_context_v1(expected_revision=72)
            for action in ('prepare_confirmation', 'continue_preparation', 'disable_exit_autosave'):
                with self.subTest(action=action), self.assertRaises(UnsupportedStepError):
                    driver.request_normal_exit_v1(action, expected_revision=72,
                        expected_exit_context_signature=query['exit_context_signature'])
            self.assertEqual(driver.sent, [])

    def test_malformed_ack_remains_unknown_after_independent_zero(self):
        with tempfile.TemporaryDirectory() as temporary, self.source():
            driver = CoreDriver(Path(temporary)); driver.invalid_ack = True
            query = driver.query_normal_exit_context_v1(expected_revision=72)
            result = driver.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=query['exit_context_signature'])
            self.assertTrue(result['process_exit_observed']); self.assertFalse(result['typed_normal_exit_observed'])
            self.assertIsNone(result['native_observation']); self.assertEqual(len(driver.sent), 1)

    def test_actual_common_client_uses_core_route_without_gui_phase(self):
        from ck3_mod_acceptance_client import _typed_quit_run_v1
        from xar_autoplayer.bridge import normal_exit_public_wire_v2 as codec
        with tempfile.TemporaryDirectory() as temporary, self.source():
            driver = CoreDriver(Path(temporary)); service = GameplayBridgeService(driver); calls = []
            def invoke(tool, arguments):
                calls.append(tool)
                if tool == 'ck3_query_normal_exit_context_v1':
                    result = service.query_normal_exit_context_v1(expected_revision=72)
                elif tool == 'ck3_request_normal_exit_v1':
                    result = service.request_normal_exit_v1(arguments['action'], expected_revision=int(arguments['expected_revision']),
                        expected_exit_context_signature=arguments['expected_exit_context_signature'])
                else: result = service.observe_normal_exit_v1()
                return codec.normal_exit_public_result_v2(result)
            result = _typed_quit_run_v1(codec, invoke, lambda: 30.0, pid=43, birth=driver.api.creation)
            self.assertTrue(result['typed_normal_exit_observed'])
            self.assertEqual(calls, ['ck3_query_normal_exit_context_v1', 'ck3_request_normal_exit_v1'])
            self.assertEqual(len(driver.sent), 1)

    def test_complete_new_core_contract_function_scope_is_strict(self):
        import ast
        from mypy import api
        import xar_autoplayer.bridge.normal_exit_contract_v1 as contract
        tree=ast.parse(Path(contract.__file__).read_text(encoding='utf-8'))
        names={'CoreExitPrefixV1','CoreExitObservationV1','normalize_core_exit_ack_v1',
            'normalize_core_exit_observation_v1','_normalize_core_public_exit_result_v1'}
        nodes=[node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
        constants=[node for node in tree.body if isinstance(node,(ast.Assign,ast.AnnAssign))
            and any(isinstance(child,ast.Name) and child.id.startswith('CORE_EXIT_') for child in ast.walk(node))]
        self.assertEqual(len(nodes),len(names))
        prefix='''from __future__ import annotations
from typing import Literal,TypedDict
from xar_autoplayer.bridge.normal_exit_process_observer_v1 import RetainedProcessIdentity
from xar_autoplayer.bridge.normal_exit_contract_v1 import positive_integer,exit_signature,classify_terminal_exit_receipt
'''
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'actual_core_exit_contract_scope.py'
            path.write_text(prefix+ast.unparse(ast.Module(body=constants+nodes,type_ignores=[])),encoding='utf-8')
            with patch.dict('os.environ', {'MYPYPATH': str(REPO/'ck3_autonomous_player/src')}):
                stdout,stderr,code=api.run(['--strict','--strict-equality','--follow-imports=silent',
                    '--no-incremental','--cache-dir','nul',str(path)])
        self.assertEqual(code,0,stdout+stderr)


if __name__ == '__main__': unittest.main(verbosity=2)
