"""Offline public-profile projection and host driver binding regressions."""
import ast
import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))
import ck3_mod_acceptance_normal_exit_profile as public_profile
import build_normal_exit_source_inventory_v1 as builder
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.normal_exit_contract_v1 import NORMAL_EXIT_MAP_CAPABILITY
from xar_autoplayer.bridge.normal_exit_map_driver_v1 import _prepare


def host_binding():
    path = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'bind_normal_exit_managed_profile')
    namespace = {'Path': Path, 'hashlib': hashlib, 'json': json, 're': re}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['bind_normal_exit_managed_profile']


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return public_profile.pin(path)


class NormalExitPublicProfileTests(unittest.TestCase):
    def test_actual_public_projection_builds_and_binds_existing_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            state, game = root / 'state', root / 'game-install'
            userdir = state / 'profile'
            executable = put(game / 'binaries/ck3.exe', b'offline synthetic executable fixture')
            for relative in builder.STOCK_GUI_PATHS:
                put(game / 'game' / relative, ('# synthetic stock ' + relative).encode())
            product = userdir / 'mod-content/product'
            put(product / 'descriptor.mod', b'name="offline product"\n')
            put(product / 'common/scripted_effects/fixture.txt', b'fixture_effect = {}\n')
            put(userdir / 'mod/product.mod', ('name="offline product"\npath="' + product.as_posix() + '"\n').encode())
            put(userdir / 'pdx_settings.txt', b'offline_fixture=yes\n')
            put(userdir / 'dlc_load.json', b'{"enabled_mods":["mod/product.mod"],"disabled_dlcs":[]}')
            prep = {'schema': 'ck3-mod-acceptance-prepared-fixture-v1',
                    'state_dir': str(state), 'profile_dir': str(userdir),
                    'game_version': 'synthetic-offline-build', 'exe_sha256': executable['sha256']}
            prep_ref = put(root / 'prepared/profile-preparation.json', json.dumps(prep).encode())
            put(state / 'preparation.json', json.dumps({
                'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1',
                'profile_dir': str(userdir), 'preparation': prep_ref}).encode())
            args = SimpleNamespace(state_dir=state, game_dir=game,
                bridge_dll=root / 'retained.dll', bridge_injector=root / 'retained.exe',
                output=root / 'run/native-report.json')
            runtime = {'game_dir': str(game), 'paths': {'dll': str(args.bridge_dll),
                                                      'injector': str(args.bridge_injector)}}
            manifest = {'game': {'version': prep['game_version'], 'exe_sha256': executable['sha256']},
                'native': {'dll': {'path_key': 'dll', 'sha256': '1' * 64},
                           'injector': {'path_key': 'injector', 'sha256': '2' * 64}}}
            manifest_ref = put(root / 'manifest.json', json.dumps(manifest).encode())
            profile_ref = public_profile.create_profile(args, runtime, manifest, manifest_ref,
                                                        state / 'normal-exit-binding', builder)
            args.normal_exit_managed_profile = Path(profile_ref['path'])
            args.normal_exit_managed_profile_sha256 = profile_ref['sha256']
            driver = SimpleNamespace()
            host_binding()(driver, args)
            bound = driver.normal_exit_managed_profile
            verified = builder.verify_source_inventory_v1(bound['normal_exit_source_inventory'], bound)
            self.assertTrue(verified['static_sources_verified'])
            self.assertEqual(bound['userdir'], str(userdir))
            self.assertEqual(bound['guard']['target']['executable'], str(game / 'binaries/ck3.exe'))
            self.assertFalse(bound['guard']['launch_authority'])
            self.assertEqual(verified['enabled_mod_count'], 1)
            # A changed actual source still fails the original verifier.
            (product / 'common/scripted_effects/fixture.txt').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'bytes|changed|size'):
                builder.verify_source_inventory_v1(bound['normal_exit_source_inventory'], bound)

    def test_unconfigured_host_keeps_original_provider_default_off(self):
        driver = SimpleNamespace(capabilities=lambda: {'bridge_capabilities': [NORMAL_EXIT_MAP_CAPABILITY]})
        host_binding()(driver, SimpleNamespace())
        self.assertFalse(hasattr(driver, 'normal_exit_managed_profile'))
        with self.assertRaisesRegex(UnsupportedStepError, 'fixed actual managed-source inventory'):
            _prepare(driver, 1)


def production_execute(result=None, error=None):
    """Run the real host method against an inert tool response and snapshot reader."""
    path = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    client = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'PlanClient')
    method = copy.deepcopy(next(node for node in client.body if isinstance(node, ast.AsyncFunctionDef)
                                and node.name == 'execute'))
    namespace = {'now': lambda: '2026-10-12T00:00:00+00:00', 'copy': copy}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), namespace)
    state = SimpleNamespace(args=SimpleNamespace(frontend_mod_load_observation=False),
        report={'steps': []}, results={}, snapshot={'revision': 7}, episode_identity=None,
        write=lambda: None, fresh_count=0, invocation_count=0)
    async def invoke(*args, **kwargs):
        state.invocation_count += 1
        if error is not None: raise error
        return copy.deepcopy(result)
    async def fresh():
        state.fresh_count += 1
        return {'revision': 8}
    state.invoke, state.fresh = invoke, fresh
    state.execute = lambda steps: namespace['execute'](state, steps)
    return state


class NormalExitTerminalExecuteTests(unittest.TestCase):
    def test_confirm_and_owned_observer_keep_typed_result_without_fresh(self):
        for tool, schema, arguments, status, signaled in (
            ('ck3_request_normal_exit_v1', 'ck3-normal-exit-request-result-v1',
             {'action': 'confirm_desktop', 'expected_revision': 7,
              'expected_exit_context_signature': '1' * 64}, 'process_exit_observed_zero', True),
            ('ck3_observe_normal_exit_v1', 'ck3-normal-exit-process-observation-result-v1',
             {}, 'dispatch_pending', False),
        ):
            with self.subTest(tool=tool):
                # Flat fields are the actual service/provider return contract.
                result = {'schema': schema, 'action': 'confirm_desktop',
                    'snapshot_after_required': False, 'status': status,
                    'process_exit_observed': signaled, 'exit_code': 0 if signaled else None,
                    'typed_normal_exit_observed': signaled, 'observer_retained': not signaled,
                    'process_preconfirm_pin': {'pid': 123, 'creation_filetime_100ns': 456,
                                              'retained_handle_token': 'fixture-owned-handle'}}
                state = production_execute(result)
                asyncio.run(state.execute([{'id': tool, 'kind': 'tool', 'tool': tool,
                                            'args': arguments, 'fresh_revision': False}]))
                self.assertEqual(state.fresh_count, 0)
                self.assertEqual(state.invocation_count, 1)
                row = state.report['steps'][0]
                self.assertTrue(row['ok'])
                self.assertEqual(row['result'], result)
                self.assertNotIn('after_snapshot', row)

    def test_ordinary_nonterminal_or_invalid_marker_still_gets_fresh(self):
        terminal = {'schema': 'ck3-normal-exit-request-result-v1', 'action': 'confirm_desktop',
                    'snapshot_after_required': False}
        scenarios = [
            ('ck3_take_snapshot', {}, terminal),
            ('ck3_request_normal_exit_v1', {'action': 'prepare_confirmation'},
             {**terminal, 'action': 'prepare_confirmation'}),
            ('ck3_request_normal_exit_v1', {'action': 'confirm_desktop'},
             {**terminal, 'snapshot_after_required': True}),
            ('ck3_request_normal_exit_v1', {'action': 'confirm_desktop'},
             {**terminal, 'snapshot_after_required': 0}),
            ('ck3_observe_normal_exit_v1', {}, {'snapshot_after_required': False, 'error': 'failed'}),
        ]
        for tool, arguments, result in scenarios:
            with self.subTest(tool=tool, result=result):
                state = production_execute(result)
                asyncio.run(state.execute([{'kind': 'tool', 'tool': tool, 'args': arguments}]))
                self.assertEqual(state.fresh_count, 1)
                self.assertEqual(state.report['steps'][0]['after_snapshot'], {'revision': 8})

    def test_mcp_error_preserves_original_failure_without_successful_row(self):
        error = RuntimeError('MCP tool ck3_request_normal_exit_v1 returned an error: fixture')
        state = production_execute(error=error)
        with self.assertRaisesRegex(RuntimeError, 'returned an error'):
            asyncio.run(state.execute([{'id': 'once', 'kind': 'tool',
                'tool': 'ck3_request_normal_exit_v1', 'args': {'action': 'confirm_desktop'}}]))
        row = state.report['steps'][0]
        self.assertFalse(row['ok'])
        self.assertIn('returned an error', row['error'])
        self.assertEqual(state.invocation_count, 1)
        self.assertNotIn('result', row)
        self.assertNotIn('after_snapshot', row)


if __name__ == '__main__': unittest.main()
