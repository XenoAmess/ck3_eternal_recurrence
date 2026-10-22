"""Real Service -> registered MCP -> JSON -> shared parser, with no native I/O."""
from __future__ import annotations

import copy
import json
import unittest

from xar_autoplayer.bridge.normal_exit_contract_v1 import (
    NATIVE_PROOF_KEYS, TARGET_BOOLEAN_KEYS, DISPATCH_BOOLEAN_KEYS,
    classify_terminal_exit_receipt,
)
from xar_autoplayer.bridge.normal_exit_process_observer_v1 import RetainedProcessIdentity
from xar_autoplayer.bridge.normal_exit_public_wire_v2 import (
    UINT64_MAX, NormalExitPublicResultV2, normal_exit_public_result_v2,
    parse_normal_exit_public_result_v2, parse_normal_exit_public_revision_v2,
)
from xar_autoplayer.bridge.service import GameplayBridgeService

BIRTH = 134371180626519916
REVISION = 2**53 + 1


def native(action: str, *, birth: int = BIRTH) -> dict[str, object]:
    dispatches = [{key: False for key in DISPATCH_BOOLEAN_KEYS} for _ in range(3)]
    if action == 'confirm_desktop':
        dispatches[2] = {key: True for key in DISPATCH_BOOLEAN_KEYS}
    return {
        'schema': 'ck3-normal-exit-map-v1', 'step': 'normal-exit-map-v1', 'action': action,
        'status': 'context_observed' if action == 'query_context' else 'dispatch_pending',
        'native_revision': REVISION, 'connection_generation': UINT64_MAX,
        'game_pid': 43, 'played_character_id': 9301,
        'process_creation_filetime_100ns': birth, 'pump_epoch': 2**53 + 2,
        **{key: True for key in NATIVE_PROOF_KEYS},
        'context_signature_verified': action != 'query_context', 'confirmation_visible': True,
        'stage_consumed': [True, True, action == 'confirm_desktop'],
        'orderly_exit_verified': False, 'autosave_verified': False,
        'exit_context_signature': 'c' * 64, 'reason': '',
        'targets': [{**{key: True for key in TARGET_BOOLEAN_KEYS},
                     'target_vtable_rva': 123} for _ in range(3)],
        'dispatches': dispatches,
    }


def context(*, birth: int = BIRTH) -> dict[str, object]:
    return {'schema': 'ck3-normal-exit-context-result-v1', 'status': 'context_observed',
            'public_revision': REVISION, 'native_observation': native('query_context', birth=birth),
            'exit_context_signature': 'c' * 64, 'source_inventory_sha256': 'b' * 64,
            'process_creation_filetime_100ns': birth, 'claim_consumed': False,
            'retry_authorized': False, 'orderly_exit_verified': False, 'autosave_verified': False}


def terminal(*, unknown: bool = False) -> dict[str, object]:
    observation: dict[str, object] = {
        'pid': 43, 'creation_filetime_100ns': BIRTH, 'retained_handle_token': 'original-token',
        'wait_result': 0, 'wait_state': 'signaled', 'exit_code': 0,
        'process_identity_verified': True, 'process_exit_observed': True,
        'observed_monotonic_ns': UINT64_MAX, 'timeout_ms': 5000,
        'observation_deadline_reached': False, 'observation_clock_domain': 'driver_monotonic_v1',
        'errors': [],
    }
    pin = {'pid': 43, 'creation_filetime_100ns': BIRTH, 'retained_handle_token': 'original-token',
           'wait_result': 258, 'verified_monotonic_ns': 2**53 + 1,
           'observation_clock_domain': 'driver_monotonic_v1'}
    receipt = None if unknown else UINT64_MAX - 1
    observed_native = None if unknown else native('confirm_desktop')
    facts = classify_terminal_exit_receipt(observed_native, observation,
        driver_dispatch_receipt_observed_monotonic_ns=receipt,
        expected_process_identity=RetainedProcessIdentity(43, BIRTH, 'original-token'))
    return {'schema': 'ck3-normal-exit-request-result-v1', 'action': 'confirm_desktop', **facts,
            'native_observation': observed_native, 'process_observation': observation,
            'process_preconfirm_pin': pin,
            'driver_dispatch_receipt_observed_monotonic_ns': receipt,
            'receipt_clock_meaning': 'driver receipt', 'snapshot_after_required': False,
            'reason': None, 'observer_retained': False, 'public_revision': REVISION,
            'request_id': 'normal-exit-confirm-fixture', 'claim_path': 'memory-only-claim',
            'source_inventory_sha256': 'b' * 64, 'process_creation_filetime_100ns': BIRTH,
            'uses_desktop_input': False, 'uses_ocr': False, 'native_submission_count': 1}


def observed() -> dict[str, object]:
    result = terminal()
    result.update({'schema': 'ck3-normal-exit-process-observation-result-v1',
                   'native_submission_count': 0, 'receipt_path': 'memory-only-observation'})
    return result


class MemoryDriver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int | None]] = []

    def capabilities(self) -> dict[str, object]:
        raise AssertionError('public test touched capabilities')

    def take_snapshot(self) -> dict[str, object]:
        raise AssertionError('public test touched a game snapshot')

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        raise AssertionError('public test touched native transport')

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float) -> dict[str, object]:
        raise AssertionError('public test waited on a game')

    def query_normal_exit_context_v1(self, *, expected_revision: int) -> dict[str, object]:
        self.calls.append(('query', expected_revision))
        return context()

    def request_normal_exit_v1(self, action: str, *, expected_revision: int,
                               expected_exit_context_signature: str) -> dict[str, object]:
        if action != 'confirm_desktop' or expected_exit_context_signature != 'c' * 64:
            raise AssertionError('unexpected actual wrapper arguments')
        self.calls.append(('request', expected_revision))
        return terminal()

    def observe_normal_exit_v1(self) -> dict[str, object]:
        self.calls.append(('observe', None))
        return observed()


class PublicWireTests(unittest.TestCase):
    def roundtrip(self, result: dict[str, object]) -> NormalExitPublicResultV2:
        wire = normal_exit_public_result_v2(result)
        parsed = parse_normal_exit_public_result_v2(json.loads(json.dumps(wire)),
            expected_process_creation_filetime_100ns=BIRTH)
        self.assertEqual(parsed.to_memory(), result)
        self.assertEqual(parsed.to_wire(), wire)
        return parsed

    def test_actual_service_three_shapes_roundtrip_without_number_loss(self) -> None:
        driver = MemoryDriver()
        service = GameplayBridgeService(driver)
        for result in (service.query_normal_exit_context_v1(expected_revision=REVISION),
                       service.request_normal_exit_v1('confirm_desktop', expected_revision=REVISION,
                           expected_exit_context_signature='c' * 64),
                       service.observe_normal_exit_v1()):
            parsed = self.roundtrip(result)
            self.assertEqual(parsed.process_creation_filetime_100ns, BIRTH)
            self.assertEqual(parsed.public_revision, REVISION)

    def test_uint64_and_safe_integer_boundaries_are_explicit(self) -> None:
        for value in (1, 2**53 - 1, 2**53, 2**53 + 1, UINT64_MAX):
            self.assertEqual(parse_normal_exit_public_revision_v2(str(value)), value)
            sample = context(birth=value)
            parsed = parse_normal_exit_public_result_v2(normal_exit_public_result_v2(sample),
                expected_process_creation_filetime_100ns=value)
            self.assertEqual(parsed.process_creation_filetime_100ns, value)
        for invalid in (True, 1.0, 1, None, '', '01', '+1', '-1', '0', str(UINT64_MAX + 1)):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                parse_normal_exit_public_revision_v2(invalid)

    def test_missing_null_wrong_type_and_foreign_birth_fail(self) -> None:
        wire = normal_exit_public_result_v2(terminal())
        for field in ('public_revision', 'process_creation_filetime_100ns', 'native_observation'):
            bad = copy.deepcopy(wire); del bad[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_normal_exit_public_result_v2(bad)
        for value in (None, True, float(BIRTH), BIRTH, '0134371180626519916', str(UINT64_MAX + 1)):
            bad = copy.deepcopy(wire); bad['process_creation_filetime_100ns'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_normal_exit_public_result_v2(bad)
        with self.assertRaises(ValueError):
            parse_normal_exit_public_result_v2(wire, expected_process_creation_filetime_100ns=BIRTH + 1)
        bad = copy.deepcopy(wire); bad['native_submission_count'] = 2**53
        with self.assertRaises(ValueError): parse_normal_exit_public_result_v2(bad)
        bad = copy.deepcopy(wire); bad['native_submission_count'] = True
        with self.assertRaises(ValueError): parse_normal_exit_public_result_v2(bad)
        bad = copy.deepcopy(wire); bad['unrecognized_birth'] = str(BIRTH)
        with self.assertRaises(ValueError): parse_normal_exit_public_result_v2(bad)

    def test_unknown_dispatch_null_remains_null_and_cannot_prove_route(self) -> None:
        parsed = self.roundtrip(terminal(unknown=True))
        wire = parsed.to_wire()
        self.assertIsNone(wire['native_observation'])
        self.assertIsNone(wire['driver_dispatch_receipt_observed_monotonic_ns'])
        self.assertFalse(wire['typed_normal_exit_observed'])


class RegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_three_wrappers_validate_inputs_and_emit_safe_v2_json(self) -> None:
        # Import is deliberate: missing MCP is a test failure, never a skipped pass.
        from mcp import Client
        from mcp.types import TextContent
        from xar_autoplayer.bridge.mcp_server import create_server
        driver = MemoryDriver()
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            properties = tools['ck3_query_normal_exit_context_v1'].input_schema['properties']
            self.assertEqual(properties['expected_revision']['type'], 'string')
            cases: tuple[tuple[str, dict[str, object]], ...] = (
                ('ck3_query_normal_exit_context_v1', {'expected_revision': str(REVISION)}),
                ('ck3_request_normal_exit_v1', {'action': 'confirm_desktop',
                    'expected_revision': str(REVISION), 'expected_exit_context_signature': 'c' * 64}),
                ('ck3_observe_normal_exit_v1', {}),
            )
            for tool, arguments in cases:
                reply = await client.call_tool(tool, arguments)
                self.assertFalse(reply.is_error)
                parsed = parse_normal_exit_public_result_v2(reply.structured_content,
                    expected_process_creation_filetime_100ns=BIRTH)
                self.assertEqual(parsed.public_revision, REVISION)
                # Exercise the actual MCP textual serializer, not a mirrored encoder.
                serialized = [item.text for item in reply.content if isinstance(item, TextContent)]
                self.assertEqual(len(serialized), 1)
                text_parsed = parse_normal_exit_public_result_v2(json.loads(serialized[0]),
                    expected_process_creation_filetime_100ns=BIRTH)
                self.assertEqual(text_parsed.to_memory(), parsed.to_memory())
            self.assertEqual(driver.calls, [('query', REVISION), ('request', REVISION), ('observe', None)])
            for invalid in (REVISION, True, float(REVISION), '01', str(UINT64_MAX + 1), None):
                before = list(driver.calls)
                reply = await client.call_tool('ck3_query_normal_exit_context_v1',
                                               {'expected_revision': invalid})
                self.assertTrue(reply.is_error)
                self.assertEqual(driver.calls, before)


if __name__ == '__main__':
    unittest.main()
