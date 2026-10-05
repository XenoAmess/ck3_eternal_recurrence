"""Continuation never repeats an uncertain earlier preparation dispatch."""
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_normal_exit_integrated_v1 import (
    FakeExitDriver, native_observation, driver_module, NATIVE_PROOF_KEYS,
    NativeHeadlessGameplayDriver, NativeNamedPipeServer, GameplayBridgeService,
    NativeProfileService, ExitWireBinding,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.normal_exit_contract_v1 import (
    MAP_EXIT_ACTIONS, REQUEST_INPUT_SCHEMA, continue_preparation_context_ready_v1,
    encode_normal_exit_map_request, encode_normal_exit_map_packet,
    normalize_native_exit_observation, normalize_public_exit_result,
)


class ContinueExitDriver(FakeExitDriver):
    def __init__(self, path):
        super().__init__(path)
        self.revision = 72
        self.generation = 8
        self.consumed = [False, False, False]
        self.menu_open = False
        self.fail_continue = False
        self.query_mutation = None

    def take_snapshot(self):
        snapshot = super().take_snapshot()
        snapshot['revision'] = snapshot['native_revision'] = self.revision
        snapshot['diagnostics']['connection_generation'] = self.generation
        return snapshot

    def send(self, request):
        action = request['action']
        if action == 'confirm_desktop':
            self.consumed[2] = True
            return super().send(request)
        self.sent.append(copy.deepcopy(request))
        if action == 'prepare_confirmation':
            self.consumed[0] = True
            self.menu_open = True
            raise OSError('fixture missing preparation ACK after actual menu-stage consumption')
        if action == 'continue_preparation':
            self.consumed[1] = True
            self.modal = True
            if self.fail_continue:
                raise OSError('fixture missing continuation ACK after actual stage-1 consumption')

    def wait_for_command_result(self, request_id, timeout):
        request = self.sent[-1]
        observation = native_observation(request, modal=self.modal)
        observation['stage_consumed'] = list(self.consumed)
        observation['targets'][2]['root_visible'] = self.modal
        for key in observation['targets'][1]:
            if key not in {'read_complete', 'target_vtable_rva'}:
                observation['targets'][1][key] = self.menu_open
        if request['action'] == 'continue_preparation':
            observation['status'] = 'confirmation_observed'
            observation['dispatches'][1] = {
                key: True for key in observation['dispatches'][1]}
        if request['action'] == 'query_context' and self.query_mutation is not None:
            self.query_mutation(observation)
        return {'ok': True, 'request_id': request_id, 'result': observation}


class ContinuePreparationTests(unittest.TestCase):
    def sources(self):
        return patch.object(driver_module, 'verify_source_inventory_v1',
                            return_value={'source_inventory_sha256': 'b' * 64})

    def unknown_prepare(self, driver):
        context = driver.query_normal_exit_context_v1(expected_revision=driver.revision)
        result = GameplayBridgeService(driver).request_normal_exit_v1(
            'prepare_confirmation', expected_revision=driver.revision,
            expected_exit_context_signature=context['exit_context_signature'])
        self.assertEqual(result['status'], 'dispatch_unknown_claimed')
        self.assertTrue(result['claim_consumed'])
        return result

    def continue_request(self, driver, *, service=None):
        context = driver.query_normal_exit_context_v1(expected_revision=driver.revision)
        return (service or GameplayBridgeService(driver)).request_normal_exit_v1(
            'continue_preparation', expected_revision=driver.revision,
            expected_exit_context_signature=context['exit_context_signature'])

    def test_unknown_prepare_fresh_progress_continues_only_remaining_stage(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            driver = ContinueExitDriver(Path(temporary))
            original = self.unknown_prepare(driver)
            claim = Path(original['claim_path'])
            original_bytes = claim.read_bytes()
            continued = self.continue_request(driver)
            self.assertTrue(continued['confirmation_observed'])
            self.assertTrue(continued['claim_consumed'])
            self.assertFalse(continued['retry_authorized'])
            self.assertFalse(continued['process_exit_observed'])
            self.assertFalse(continued['typed_normal_exit_observed'])
            self.assertEqual(continued['native_submission_count'], 1)
            self.assertEqual(claim.read_bytes(), original_bytes)
            native = continued['native_observation']
            self.assertEqual(native['stage_consumed'], [True, True, False])
            self.assertTrue(native['dispatches'][1]['dispatch_invoked'])
            self.assertFalse(native['dispatches'][0]['dispatch_invoked'])
            self.assertFalse(native['dispatches'][2]['dispatch_invoked'])
            self.assertEqual([request['action'] for request in driver.sent],
                             ['query_context', 'prepare_confirmation',
                              'query_context', 'continue_preparation'])
            self.assertNotEqual(continued['claim_path'], original['claim_path'])

    def test_continuation_own_claim_survives_unknown_revision_reconnect_and_new_driver(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            directory = Path(temporary)
            driver = ContinueExitDriver(directory)
            prepare = self.unknown_prepare(driver)
            driver.fail_continue = True
            continued = self.continue_request(driver)
            self.assertEqual(continued['status'], 'dispatch_unknown_claimed')
            claim_bytes = Path(continued['claim_path']).read_bytes()
            old_prepare_bytes = Path(prepare['claim_path']).read_bytes()
            replacement = ContinueExitDriver(directory)
            replacement.revision = 91
            replacement.generation = 32
            # A reconnect's genuine fresh remaining-stage observation cannot
            # clear a client claim whose earlier stage-1 delivery was unknown.
            replacement.consumed = [True, False, False]
            replacement.menu_open = True
            context = replacement.query_normal_exit_context_v1(expected_revision=91)
            calls = len(replacement.sent)
            with self.assertRaisesRegex(BridgeUnavailableError, 'already claimed'):
                replacement.request_normal_exit_v1(
                    'continue_preparation', expected_revision=91,
                    expected_exit_context_signature=context['exit_context_signature'])
            self.assertEqual(len(replacement.sent), calls)
            with self.assertRaisesRegex(BridgeUnavailableError, 'already claimed'):
                replacement.request_normal_exit_v1(
                    'prepare_confirmation', expected_revision=91,
                    expected_exit_context_signature=context['exit_context_signature'])
            self.assertEqual(Path(continued['claim_path']).read_bytes(), claim_bytes)
            self.assertEqual(Path(prepare['claim_path']).read_bytes(), old_prepare_bytes)

    def test_continuation_requires_fresh_query_after_stage_zero(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            driver = ContinueExitDriver(Path(temporary))
            self.unknown_prepare(driver)
            driver.revision += 1
            calls = len(driver.sent)
            with self.assertRaisesRegex(BridgeUnavailableError, 'not a fresh'):
                driver.request_normal_exit_v1('continue_preparation', expected_revision=driver.revision,
                                             expected_exit_context_signature='c' * 64)
            self.assertEqual(len(driver.sent), calls)
            self.assertFalse(any('continue_preparation' in row.read_text()
                                 for row in (Path(temporary) / 'normal-exit-map-requests').glob('*.claim.json')))

    def test_each_actual_progress_or_target_defect_blocks_before_claim_and_send(self):
        mutations = [
            lambda observation: observation.update(stage_consumed=[False, False, False]),
            lambda observation: observation.update(stage_consumed=[True, True, False]),
            lambda observation: observation.update(stage_consumed=[True, False, True]),
            lambda observation: observation.update(confirmation_visible=True),
            lambda observation: observation['targets'][2].update(root_visible=True),
            lambda observation: observation['targets'][1].update(target_vtable_rva=0),
        ]
        for field in ['read_complete', 'root_exists', 'root_visible', 'target_exists',
                      'target_visible', 'target_enabled', 'unique_target', 'dispatch_admitted']:
            mutations.append(lambda observation, field=field: observation['targets'][1].update({field: False}))
        for index in [0, 2]:
            mutations.append(lambda observation, index=index: observation['targets'][index].update(read_complete=False))
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index), tempfile.TemporaryDirectory() as temporary, self.sources():
                driver = ContinueExitDriver(Path(temporary))
                self.unknown_prepare(driver)
                driver.query_mutation = mutation
                context = driver.query_normal_exit_context_v1(expected_revision=72)
                calls = len(driver.sent)
                claims = sorted((Path(temporary) / 'normal-exit-map-requests').glob('*.claim.json'))
                with self.assertRaisesRegex(BridgeUnavailableError, 'continuation requires fresh'):
                    driver.request_normal_exit_v1('continue_preparation', expected_revision=72,
                        expected_exit_context_signature=context['exit_context_signature'])
                self.assertEqual(len(driver.sent), calls)
                self.assertEqual(sorted((Path(temporary) / 'normal-exit-map-requests').glob('*.claim.json')), claims)

    def test_unavailable_defaults_never_admit_continuation(self):
        binding = ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)
        request = json.loads(encode_normal_exit_map_request(
            request_id='query', action='query_context', binding=binding, request_nonce='query'))
        raw = native_observation(request)
        raw.update(status='unavailable', stage_consumed=[False, False, False], reason='owner unavailable')
        native = normalize_native_exit_observation(raw, binding, 'query_context')
        self.assertFalse(continue_preparation_context_ready_v1(native))

    def test_progress_requires_closed_three_exact_booleans(self):
        binding = ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)
        request = json.loads(encode_normal_exit_map_request(
            request_id='query', action='query_context', binding=binding, request_nonce='query'))
        for value in [None, (), [], [True, False], [True, False, False, False], [1, False, False],
                      [True, 0, False], [True, False, None], 'true,false,false']:
            raw = native_observation(request)
            raw['stage_consumed'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_native_exit_observation(raw, binding, 'query_context')
            self.assertFalse(continue_preparation_context_ready_v1(raw))
        raw = native_observation(request)
        del raw['stage_consumed']
        with self.assertRaises(ValueError): normalize_native_exit_observation(raw, binding, 'query_context')

    def test_continue_backend_ack_cannot_claim_other_stages_or_process_exit(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            driver = ContinueExitDriver(Path(temporary))
            self.unknown_prepare(driver)
            result = self.continue_request(driver)
            native = result['native_observation']
            binding = ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)
            for stage in [0, 2]:
                for field in ['claim_latched', 'dispatch_invoked']:
                    forged = copy.deepcopy(native)
                    forged['dispatches'][stage][field] = True
                    with self.assertRaises(ValueError):
                        normalize_native_exit_observation(forged, binding, 'continue_preparation')
            for field in ['typed_normal_exit_observed', 'process_exit_observed']:
                forged = copy.deepcopy(result)
                forged[field] = True
                with self.assertRaises(ValueError):
                    normalize_public_exit_result(forged, action='continue_preparation', expected_revision=72)

    def test_existing_retained_handle_terminal_path_after_continuation(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            driver = ContinueExitDriver(Path(temporary))
            self.unknown_prepare(driver)
            self.continue_request(driver)
            context = driver.query_normal_exit_context_v1(expected_revision=72)
            before = driver.snapshot_calls
            result = GameplayBridgeService(driver).request_normal_exit_v1(
                'confirm_desktop', expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            self.assertTrue(result['process_exit_observed'])
            self.assertTrue(result['typed_normal_exit_observed'])
            self.assertEqual(driver.snapshot_calls, before + 1)
            self.assertFalse(result['autosave_verified'])

    def test_existing_profile_method_forwards_continuation_without_after_guard(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            directory = Path(temporary)
            driver = ContinueExitDriver(directory)
            self.unknown_prepare(driver)
            context = driver.query_normal_exit_context_v1(expected_revision=72)
            class Backend:
                def poll(self, profile): return {'ack': True}
            class BoundProfile(NativeProfileService):
                def _bound_frame(self, revision, *, paused): return self.driver.take_snapshot()
                def _gameplay_service(self): return GameplayBridgeService(self.driver)
                def guard(self): raise AssertionError('unexpected postdispatch guard')
            profile = {'evidence_directory': str(directory / 'profile-evidence'), 'profile_sha256': 'd' * 64,
                       'normal_exit_source_inventory': {'path': 'fixture', 'sha256': 'b' * 64}}
            service = BoundProfile(profile, backend=Backend())
            service.driver = driver
            receipt = service.request_normal_exit('continue_preparation', 72, context['exit_context_signature'])
            self.assertTrue(receipt['result']['confirmation_observed'])
            self.assertFalse(receipt['snapshot_after_required'])
            self.assertEqual(driver.sent[-1]['action'], 'continue_preparation')


class ContinueEncoderAndSchemaTests(unittest.TestCase):
    def test_same_closed_request_schema_and_actual_encoder_thirteen_fields(self):
        self.assertEqual(MAP_EXIT_ACTIONS,
                         ('prepare_confirmation', 'continue_preparation', 'confirm_desktop'))
        self.assertEqual(REQUEST_INPUT_SCHEMA['properties']['action']['enum'], list(MAP_EXIT_ACTIONS))
        self.assertFalse(REQUEST_INPUT_SCHEMA['additionalProperties'])
        arguments = {'request_id': 'continue-request', 'action': 'continue_preparation',
                     'request_nonce': 'continue-nonce', 'expected_exit_context_signature': 'c' * 64,
                     'binding': ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)}
        payload = encode_normal_exit_map_request(**arguments)
        self.assertEqual(len(json.loads(payload)), 13)
        self.assertEqual(json.loads(payload)['action'], 'continue_preparation')
        packets = []
        endpoint = NativeNamedPipeServer(r'\\.\pipe\offline_continue_fixture')
        with patch.object(endpoint, '_current_handle', return_value=999), patch(
                'xar_autoplayer.bridge.native_driver._write_all',
                side_effect=lambda handle, data: packets.append(data) or True):
            endpoint.send(json.loads(payload))
        self.assertEqual(packets, [encode_normal_exit_map_packet(**arguments)])
        self.assertEqual(packets[0][4:], payload)

    def test_both_sdk_servers_keep_existing_tool_names_and_closed_action_enum(self):
        from xar_autoplayer.bridge.mcp_server import create_server as create_broad_server
        from ck3_native_profile_mcp import create_server as create_profile_server
        async def schemas(server):
            return {tool.name: tool.input_schema for tool in await server.list_tools()}
        class NoBusiness:
            def capabilities(self):
                raise AssertionError('schema construction called backend capabilities')
            def take_snapshot(self):
                raise AssertionError('schema construction called a live snapshot')
            def __getattr__(self, name):
                # getattr(..., default) may inspect static feature availability;
                # an attribute lookup is distinct from invoking a callback.
                raise AttributeError(name)
        broad = asyncio.run(schemas(create_broad_server(NoBusiness())))
        profile = asyncio.run(schemas(create_profile_server(NoBusiness())))
        self.assertEqual(len(profile), 21)
        for tools in [broad, profile]:
            schema = tools['ck3_request_normal_exit_v1']
            self.assertEqual(schema['properties']['action']['enum'], list(MAP_EXIT_ACTIONS))
            self.assertFalse(schema['additionalProperties'])
            self.assertEqual(set(schema['required']),
                             {'action', 'expected_revision', 'expected_exit_context_signature'})
            self.assertFalse(any('continue' in name for name in tools))


if __name__ == '__main__':
    unittest.main()
