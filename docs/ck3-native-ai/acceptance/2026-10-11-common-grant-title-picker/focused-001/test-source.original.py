"""Offline public grant routing: real MCP models, service code and existing driver.

No SDK, pipes, CK3, source freeze or loaded native binary is opened. The transport
stub returns synthetic DTOs; those values never qualify a real Title or NPC.
"""
from __future__ import annotations

import argparse
import ast
import copy
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import Annotated

_options = argparse.ArgumentParser(add_help=False)
_options.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
_options.add_argument('--candidate-author', type=Path)
_args, _remaining = _options.parse_known_args()
sys.argv = [sys.argv[0], *_remaining]
REPO = _args.repo.resolve()
sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))

from mcp.server import MCPServer
from pydantic import AfterValidator, Field, ValidationError
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.grant_title_picker_v1 import PERMISSION, SCHEMA, title_ids
from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004

SERVICE_PATH = 'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py'
MCP_PATH = 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
HOST_PATH = 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
ENTRY_PATH = 'tools/ck3_mod_acceptance.py'
PATHS = (SERVICE_PATH, MCP_PATH, HOST_PATH, ENTRY_PATH)
if _args.candidate_author:
    _spec = importlib.util.spec_from_file_location('reviewed_grant_candidate', _args.candidate_author)
    _author = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_author)
    _, SOURCES = _author.candidate_sources(REPO)
else:
    SOURCES = {path: (REPO / path).read_bytes() for path in PATHS}
TREES = {path: ast.parse(raw.decode('utf-8-sig'), filename=path) for path, raw in SOURCES.items()}


def function(path, name):
    found = [node for node in ast.walk(TREES[path])
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(found) != 1:
        raise AssertionError(f'Expected one production function {path}:{name}')
    return copy.deepcopy(found[0])


def project(nodes, namespace, filename):
    """Compile actual production nodes, including their branches and annotations."""
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(module, filename, 'exec'), namespace)
    return namespace


def service_for(driver):
    node = function(SERVICE_PATH, 'grant_title_picker_v1')
    namespace = {'__name__': 'xar_autoplayer.bridge.reviewed_public_grant_service',
                 '__package__': 'xar_autoplayer.bridge', 'UnsupportedStepError': UnsupportedStepError}
    project([node], namespace, SERVICE_PATH)
    return types.SimpleNamespace(driver=driver,
        grant_title_picker_v1=types.MethodType(namespace['grant_title_picker_v1'],
                                              types.SimpleNamespace(driver=driver)))


def server_for(driver, service=None):
    aliases = {'NormalExitRevisionV1', 'OrdinaryRecipientIdV1', 'GrantTitleFullIdV1',
               'GrantTitleIdsV1', 'GrantSendTitleIdsV1', 'GrantDesiredSelectedV1'}
    nodes = [copy.deepcopy(node) for node in TREES[MCP_PATH].body
             if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id in aliases for target in node.targets)]
    namespace = {'__name__': 'reviewed_public_grant_mcp', 'Annotated': Annotated,
                 'Field': Field, 'AfterValidator': AfterValidator,
                 'validate_grant_title_ids_v1': title_ids,
                 'GRANT_TITLE_PICKER_PERMISSION_V1': PERMISSION}
    project([*nodes, function(MCP_PATH, '_forbid_unknown_tool_arguments_v1'),
             function(MCP_PATH, 'register_stock_grant_title_picker_tools')], namespace, MCP_PATH)
    server = MCPServer('offline-public-grant-test')
    namespace['register_stock_grant_title_picker_tools'](server, service or service_for(driver), driver)
    return server


def invoke(server, operation, **arguments):
    tool = server._tool_manager._tools[f'ck3_{operation}_grant_title_picker_v1']
    validated = tool.fn_metadata.arg_model.model_validate(arguments)
    return tool.fn(**validated.model_dump())


def frame():
    return {'revision': 7, 'native_revision': 6, 'paused': True, 'map_ready': True,
            'date_raw': 123456, 'episode_run_id': 'synthetic-offline-episode',
            'played_character': {'character_id': 31254, 'alive': True},
            'diagnostics': {'connection_generation': 2, 'hello': {
                'pid': 999, 'ck3_build_match': True,
                'game_adapter_id': 'ck3-1.20.0.4-msvc-x64',
                'expected_ck3_version': CK3_12004.game_version,
                'expected_ck3_sha256': CK3_12004.executable_sha256}}}


TITLE = 0x0100004D  # Synthetic generation-bearing ID, never an actual C3 Title.


class OfflineNativeDriver:
    grant_title_picker_v1 = NativeHeadlessGameplayDriver.grant_title_picker_v1

    def __init__(self, state):
        self.state = state
        self.current = frame()
        self.calls = []
        self.mode = 'unavailable'
        self.snapshot_reads = 0
        self.drift_after = False
        setattr(self, PERMISSION, True)

    def take_snapshot(self):
        self.snapshot_reads += 1
        value = copy.deepcopy(self.current)
        if self.drift_after and self.snapshot_reads > 1:
            value['date_raw'] += 1
        return value

    def capabilities(self):
        return {'bridge_capabilities': ['game.command.' + op + '-grant-title-picker-v1'
                                        for op in ('query', 'prepare', 'select', 'send')]}

    def _native_driver_state_path(self):
        return self.state / 'driver-state.json'

    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append((step, copy.deepcopy(kwargs)))
        operation = step.removesuffix('-grant-title-picker-v1')
        complete = self.mode in {'pending', 'verified', 'warning-false-proof'}
        transferred = self.mode in {'verified', 'warning-false-proof'}
        def observation(after=False):
            holder = 65865 if after and transferred else 31254
            return {'available': complete, 'window_visible': complete,
                'window_binding_verified': complete, 'rows_complete': complete,
                'native_can_send': True if complete else None,
                'warning_confirmation_required': self.mode == 'warning-false-proof' if complete else None,
                'rows': [{'title_full_id': TITLE, 'holder_character_full_id': holder,
                          'selected': True, 'selectable': True}] if complete else [],
                'selected_title_full_ids': [TITLE] if complete else [],
                'requested_title_holders': [{'title_full_id': TITLE, 'available': True,
                    'holder_character_full_id': holder}] if complete else []}
        result = {'schema': SCHEMA, 'operation': operation,
            'exact_build': CK3_12004.game_version,
            'executable_sha256': CK3_12004.executable_sha256,
            'recipient_character_full_id': 65865,
            'owner_thread_verified': complete, 'frame_verified': complete,
            'source_abi_pins_verified': complete, 'dispatch_invoked': complete,
            'native_call_completed': complete, 'selection_verified': False,
            'transfer_verified': transferred, 'business_full_credit': False,
            'before': observation(), 'after': observation(True),
            'status': 'holder_transfer_observed' if transferred else 'pending' if complete else 'unavailable',
            'unavailable_reason': '' if complete else 'synthetic_offline_unavailable'}
        result.update({key: value for key, value in opening_binding(self.current).items()
                       if key != 'episode_run_id'})
        return result


class PublicGrantRoutingTests(unittest.TestCase):
    def driver(self, directory):
        return OfflineNativeDriver(Path(directory))

    def test_default_off_independent_permission_and_create_server_registration(self):
        for permission in (None, False, 1, 'true'):
            driver = types.SimpleNamespace(allow_private_confucian_challenger_queries=True)
            if permission is not None:
                setattr(driver, PERMISSION, permission)
            self.assertEqual(server_for(driver)._tool_manager._tools, {})
        driver = types.SimpleNamespace(**{PERMISSION: True})
        self.assertEqual(len(server_for(driver)._tool_manager._tools), 4)
        calls = [node for node in ast.walk(function(MCP_PATH, 'create_server'))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == 'register_stock_grant_title_picker_tools']
        self.assertEqual(len(calls), 1)

    def test_metadata_annotations_and_closed_strict_schemas(self):
        driver = types.SimpleNamespace(**{PERMISSION: True})
        server = server_for(driver)
        base = {'recipient_id': 65865, 'title_full_ids': [TITLE], 'expected_revision': 7}
        for operation in ('query', 'prepare'):
            tool = server._tool_manager._tools[f'ck3_{operation}_grant_title_picker_v1']
            self.assertFalse(tool.parameters['additionalProperties'])
            tool.fn_metadata.arg_model.model_validate({**base, 'title_full_ids': [0]})
            invalid = [dict(base, unexpected=True)]
            invalid += [dict(base, expected_revision=value) for value in (True, '7', 7.0, 0, 2**64)]
            invalid += [dict(base, recipient_id=value) for value in (True, 0, '65865', 2**32-1)]
            invalid += [dict(base, title_full_ids=value) for value in
                        (None, (TITLE,), '1', [True], ['1'], [1.0], [2**32-1], [TITLE, TITLE], list(range(65)))]
            for arguments in invalid:
                with self.subTest(operation=operation, arguments=arguments), self.assertRaises(ValidationError):
                    tool.fn_metadata.arg_model.model_validate(arguments)
        select = server._tool_manager._tools['ck3_select_grant_title_picker_v1']
        valid = {'recipient_id': 65865, 'title_full_id': 0, 'desired_selected': True,
                 'expected_selected_title_full_ids': [], 'expected_revision': 7}
        select.fn_metadata.arg_model.model_validate(valid)
        for value in (1, 'true', None):
            with self.assertRaises(ValidationError):
                select.fn_metadata.arg_model.model_validate(dict(valid, desired_selected=value))
        send = server._tool_manager._tools['ck3_send_grant_title_picker_v1']
        with self.assertRaises(ValidationError):
            send.fn_metadata.arg_model.model_validate({'recipient_id': 65865,
                'expected_selected_title_full_ids': [], 'expected_revision': 7})
        expected = {'query': (True, False, True), 'prepare': (False, None, False),
                    'select': (False, None, False), 'send': (False, True, False)}
        for operation, hints in expected.items():
            annotation = server._tool_manager._tools[f'ck3_{operation}_grant_title_picker_v1'].annotations
            self.assertEqual((annotation.readOnlyHint, annotation.destructiveHint, annotation.idempotentHint), hints)

    def test_service_checks_permission_and_fields_before_existing_driver(self):
        calls = []
        driver = types.SimpleNamespace(grant_title_picker_v1=lambda *a, **k: calls.append((a, k)))
        service = service_for(driver)
        kwargs = {'expected_revision': 7, 'requested_title_full_ids': [TITLE],
                  'expected_selected_title_full_ids': []}
        with self.assertRaises(UnsupportedStepError):
            service.grant_title_picker_v1('query', 65865, **kwargs)
        setattr(driver, PERMISSION, True)
        for replacement in ({'expected_revision': True}, {'requested_title_full_ids': None},
                            {'requested_title_full_ids': [TITLE, TITLE]},
                            {'expected_selected_title_full_ids': [TITLE]}):
            with self.assertRaises(ValueError):
                service.grant_title_picker_v1('query', 65865, **(kwargs | replacement))
        with self.assertRaises(ValueError):
            service.grant_title_picker_v1('automatic-send', 65865, **kwargs)
        self.assertEqual(calls, [])

    def test_all_four_public_tools_reach_real_native_driver_without_autoselection(self):
        with tempfile.TemporaryDirectory() as directory:
            driver = self.driver(directory)
            server = server_for(driver)
            for operation in ('query', 'prepare', 'select', 'send'):
                arguments = {'recipient_id': 65865, 'expected_revision': 7}
                if operation in {'query', 'prepare'}:
                    arguments['title_full_ids'] = [TITLE]
                elif operation == 'select':
                    arguments.update(title_full_id=TITLE, desired_selected=True,
                                     expected_selected_title_full_ids=[])
                else:
                    arguments['expected_selected_title_full_ids'] = [TITLE]
                result = invoke(server, operation, **arguments)
                self.assertEqual(result['status'], 'unavailable')
                self.assertFalse(result['business_full_credit'])
                step, packet = driver.calls[-1]
                self.assertEqual(step, operation + '-grant-title-picker-v1')
                self.assertEqual(packet['required_capability'], 'game.command.' + step)
                self.assertEqual(packet['expected_revision'], 7)
                self.assertTrue(packet['protocol_request_id'].startswith('grant-'))
                fields = packet['request_fields']
                self.assertEqual(fields['recipient_character_full_id'], 65865)
                self.assertEqual(fields['requested_title_full_ids'], str(TITLE))
                self.assertEqual(fields['expected_game_pid'], 999)
                self.assertEqual(fields['expected_connection_generation'], 2)
                self.assertEqual(fields['expected_player_character_id'], 31254)
            self.assertEqual(len(driver.calls), 4)

    def test_real_driver_revision_and_after_frame_guards_remain_effective(self):
        with tempfile.TemporaryDirectory() as directory:
            driver = self.driver(directory)
            server = server_for(driver)
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                invoke(server, 'query', recipient_id=65865, title_full_ids=[TITLE], expected_revision=8)
            self.assertEqual(driver.calls, [])
            driver.drift_after = True
            driver.snapshot_reads = 0
            with self.assertRaisesRegex(ValueError, 'paused episode'):
                invoke(server, 'query', recipient_id=65865, title_full_ids=[TITLE], expected_revision=7)
            self.assertEqual(len(driver.calls), 1)

    def test_pending_send_claim_blocks_resend_and_holder_readback_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            driver = self.driver(directory)
            driver.mode = 'pending'
            server = server_for(driver)
            arguments = {'recipient_id': 65865, 'expected_selected_title_full_ids': [TITLE], 'expected_revision': 7}
            pending = invoke(server, 'send', **arguments)
            self.assertFalse(pending['transfer_verified'])
            self.assertTrue(Path(pending['action_claim_path']).is_file())
            driver.current['revision'] = 8
            with self.assertRaisesRegex(ValueError, 'no retry'):
                invoke(server, 'send', **(arguments | {'expected_revision': 8}))
            self.assertEqual(len(driver.calls), 1)
        with tempfile.TemporaryDirectory() as directory:
            driver = self.driver(directory)
            driver.mode = 'verified'
            verified = invoke(server_for(driver), 'send', **arguments)
            self.assertTrue(verified['transfer_verified'])
            self.assertFalse(verified['business_full_credit'])
            self.assertEqual(verified['after']['requested_title_holders'][0]['holder_character_full_id'], 65865)

    def test_warning_branch_cannot_be_promoted_to_transfer_success(self):
        with tempfile.TemporaryDirectory() as directory:
            driver = self.driver(directory)
            driver.mode = 'warning-false-proof'
            with self.assertRaisesRegex(ValueError, 'holder readback'):
                invoke(server_for(driver), 'send', recipient_id=65865,
                       expected_selected_title_full_ids=[TITLE], expected_revision=7)
            self.assertEqual(len(driver.calls), 1)

    def test_public_feature_parser_forwarding_and_permission_binding(self):
        # Compile the actual feature section of Selection.build_argv, not a mirror.
        method = function(ENTRY_PATH, 'build_argv')
        start = next(i for i, node in enumerate(method.body)
                     if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                     and node.targets[0].id == 'features')
        end = next(i for i, node in enumerate(method.body[start:], start)
                   if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == 'budgets')
        section = method.body[start:end]
        def argv(features):
            namespace = {'self': types.SimpleNamespace(manifest={'host_features': features}),
                         'argv': [], 'startup': {'mode': 'saved_campaign'}}
            project(copy.deepcopy(section), namespace, ENTRY_PATH)
            return namespace['argv']
        self.assertNotIn('--private-grant-title-picker', argv({}))
        self.assertNotIn('--private-grant-title-picker', argv({'stock_grant_title_picker': False}))
        self.assertNotIn('--private-grant-title-picker', argv({'confucian_challenger_readonly': True}))
        self.assertEqual(argv({'stock_grant_title_picker': True}), ['--private-grant-title-picker'])
        for features in ({'stock_grant_title_picker': 1}, {'stock_grant_title_picker': None},
                         {'stock_grant_title_picker': 'true'}, {'grant': True}):
            with self.assertRaises(ValueError):
                argv(features)
        namespace = {'__name__': 'reviewed_public_grant_host', 'argparse': argparse, 'Path': Path}
        project([function(HOST_PATH, 'parser'), function(HOST_PATH, 'bind_stock_grant_title_picker_permission')],
                namespace, HOST_PATH)
        parser = namespace['parser']()
        self.assertFalse(parser.parse_args([]).private_grant_title_picker)
        self.assertTrue(parser.parse_args(['--private-grant-title-picker']).private_grant_title_picker)
        binder = namespace['bind_stock_grant_title_picker_permission']
        driver = types.SimpleNamespace()
        binder(driver, False)
        self.assertIs(getattr(driver, PERMISSION), False)
        binder(driver, True)
        self.assertIs(getattr(driver, PERMISSION), True)
        with self.assertRaises(ValueError):
            binder(driver, 1)
        host_nodes = list(ast.walk(TREES[HOST_PATH]))
        calls = [node for node in host_nodes if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == 'bind_stock_grant_title_picker_permission']
        self.assertEqual(len(calls), 1)
        forwards = [copy.deepcopy(node) for node in host_nodes if isinstance(node, ast.If)
                    and isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Name)
                    and node.test.func.id == 'getattr' and len(node.test.args) >= 2
                    and isinstance(node.test.args[1], ast.Constant)
                    and node.test.args[1].value == 'private_grant_title_picker']
        self.assertEqual(len(forwards), 1)
        for enabled in (False, True):
            namespace = {'args': types.SimpleNamespace(private_grant_title_picker=enabled), 'child_args': []}
            project(copy.deepcopy(forwards), namespace, HOST_PATH)
            self.assertEqual(namespace['child_args'], ['--private-grant-title-picker'] if enabled else [])


if __name__ == '__main__':
    unittest.main()
