"""Offline public-profile projection and host driver binding regressions."""
import ast
import asyncio
import copy
import hashlib
import importlib.util
import json
import os
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
from test_ck3_host_terminal_observation import REVISION, public_terminal_result


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
    @unittest.skipUnless(os.environ.get('XAR_CK3_1210_OFFLINE_METADATA_GAME_DIR'),
        'explicit actual installed 1.21 game root required; no Game is launched')
    def test_actual_installed_florin_metadata_builder_host_driver_client_chain(self):
        from xar_autoplayer.bridge.normal_exit_public_wire_v2 import normal_exit_public_result_v2
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.normal_exit_contract_v1 import CORE_EXIT_EXE_SHA256
        from test_normal_exit_core1210_v1 import CoreDriver
        from ck3_mod_acceptance import normal_exit_static_binding_v1
        from ck3_mod_acceptance_client import typed_normal_quit_evidence_v1
        game=Path(os.environ['XAR_CK3_1210_OFFLINE_METADATA_GAME_DIR']).resolve()
        executable=public_profile.pin(game/'binaries/ck3.exe')
        self.assertEqual(executable['sha256'].upper(),CORE_EXIT_EXE_SHA256)
        with tempfile.TemporaryDirectory(prefix='OFFLINE_ACTUAL_FLORIN_METADATA_') as temporary:
            root=Path(temporary).resolve();state=root/'state';live=root/'allocated-offline-core-run'
            live.mkdir();userdir=state/'profile';userdir.mkdir(parents=True)
            put(userdir/'pdx_settings.txt',b'# authored offline settings; no Game\n')
            product=REPO/'mod_financial_markets'
            put(userdir/'mod/product.mod',('name="Actual product static metadata"\npath="'+product.as_posix()+'"\n').encode())
            put(userdir/'dlc_load.json',b'{"enabled_mods":["mod/product.mod"],"disabled_dlcs":[]}')
            prep={'schema':'ck3-mod-acceptance-prepared-fixture-v1','state_dir':str(state),
                'profile_dir':str(userdir),'game_version':'1.21.0','exe_sha256':executable['sha256']}
            prep_ref=put(root/'prepared/profile-preparation.json',json.dumps(prep).encode())
            put(state/'preparation.json',json.dumps({'schema':'ck3-mod-acceptance-profile-startup-evidence-v1',
                'profile_dir':str(userdir),'preparation':prep_ref}).encode())
            args=SimpleNamespace(state_dir=state,game_dir=game,bridge_dll=root/'software-native.dll',
                bridge_injector=root/'software-injector.exe',output=live/'native-report.json')
            runtime={'game_dir':str(game),'paths':{'dll':str(args.bridge_dll),'injector':str(args.bridge_injector)}}
            manifest={'game':{'version':'1.21.0','exe_sha256':executable['sha256']},
                'native':{'dll':{'path_key':'dll','sha256':'1'*64},'injector':{'path_key':'injector','sha256':'2'*64}}}
            manifest_ref=put(root/'manifest.json',json.dumps(manifest).encode())
            profile_ref=public_profile.create_profile(args,runtime,manifest,manifest_ref,live/'normal-exit-binding',builder)
            normal_exit_static_binding_v1(profile_ref,state_dir=state,run_dir=live,runtime_manifest=manifest_ref)
            args.normal_exit_managed_profile=Path(profile_ref['path'])
            args.normal_exit_managed_profile_sha256=profile_ref['sha256']
            driver=CoreDriver(state/'native-session');driver.path.mkdir()
            host_binding()(driver,args)
            service=GameplayBridgeService(driver)
            # Keep the allocated immutable settings snapshot, using the actual
            # running-input verifier used by the common managed host.
            original_settings=put(live/'input-snapshots/profile/pdx_settings.txt',(userdir/'pdx_settings.txt').read_bytes())
            frozen={'run_id':live.name,'state_dir':str(state),'identity_allocation':{'machine_id':'4-8e1c2f1861'},
                'argv':['SOFTWARE_NO_GAME','--normal-exit-managed-profile',profile_ref['path'],
                    '--normal-exit-managed-profile-sha256',profile_ref['sha256']],
                'files':{str(userdir/'pdx_settings.txt'):{k:original_settings[k] for k in ('bytes','sha256')},
                         original_settings['path']:{k:original_settings[k] for k in ('bytes','sha256')}}}
            frozen_ref=put(live/'frozen-argv.json',json.dumps(frozen).encode())
            context={'run_id':live.name,'run_dir':str(live),'frozen_argv':frozen_ref,'normal_exit_managed_profile':profile_ref}
            put(live/'ready-context.json',json.dumps(context).encode())
            query=service.query_normal_exit_context_v1(expected_revision=72)
            terminal=service.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=query['exit_context_signature'])
            self.assertTrue(terminal['typed_normal_exit_observed'])
            self.assertEqual(len(driver.sent),1)
            bridge=REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge'
            index=root/'source-index.json'
            index_ref=put(index,json.dumps({'schema':'ck3-common-source-index-v1','files':{
                (bridge/(name+'.py')).relative_to(REPO).as_posix():{k:public_profile.pin(bridge/(name+'.py'))[k]
                    for k in ('bytes','sha256')} for name in ('normal_exit_process_observer_v1',
                        'normal_exit_contract_v1','normal_exit_public_wire_v2')}}).encode())
            report={'error':None,'steps':[{'id':'original-core-exit','ok':True,'finished_at':'software-observed',
                'plan':{'tool':'ck3_request_normal_exit_v1','args':{'action':'confirm_desktop','expected_revision':'72',
                    'expected_exit_context_signature':query['exit_context_signature']}},
                'result':normal_exit_public_result_v2(terminal)}]}
            evidence=typed_normal_quit_evidence_v1(report,live=live,state=state,
                retained_value={'pid':43,'creation_filetime_100ns':str(driver.api.creation),
                    'retained_synchronize_query_handle_acquired':True},context_value=context,frozen_value=frozen,
                source_root=REPO,source_index=index,source_index_reference=index_ref)
            self.assertIsNotNone(evidence)
            self.assertIsNone(evidence['autosave_disabled'])
            self.assertFalse(evidence['autosave_verified'])

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
    def test_confirm_and_owned_observer_keep_typed_result_without_fresh(self) -> None:
        for tool, arguments, observed, signaled in (
            ('ck3_request_normal_exit_v1',
             {'action': 'confirm_desktop', 'expected_revision': str(REVISION),
              'expected_exit_context_signature': '1' * 64}, False, True),
            ('ck3_observe_normal_exit_v1', {}, True, False),
        ):
            with self.subTest(tool=tool):
                # Real classifier -> public V2 encoder, not an obsolete partial
                # V1 DTO that bypasses the published receipt contract.
                result = public_terminal_result(observed=observed, signaled=signaled)
                state = production_execute(result)
                asyncio.run(state.execute([{'id': tool, 'kind': 'tool', 'tool': tool,
                                            'args': arguments, 'fresh_revision': False}]))
                self.assertEqual(state.fresh_count, 0)
                self.assertEqual(state.invocation_count, 1)
                row = state.report['steps'][0]
                self.assertTrue(row['ok'])
                self.assertEqual(row['result'], result)
                self.assertNotIn('after_snapshot', row)

    def test_ordinary_nonterminal_gets_fresh_and_malformed_terminal_fails_closed(self) -> None:
        terminal = {'schema': 'ck3-normal-exit-request-result-v1', 'action': 'confirm_desktop',
                    'snapshot_after_required': False}
        ordinary = [
            ('ck3_take_snapshot', {}, terminal),
            ('ck3_request_normal_exit_v1', {'action': 'prepare_confirmation'},
             {**terminal, 'action': 'prepare_confirmation'}),
        ]
        malformed = [
            ('ck3_request_normal_exit_v1', {'action': 'confirm_desktop'},
             {**terminal, 'snapshot_after_required': True}),
            ('ck3_request_normal_exit_v1', {'action': 'confirm_desktop'},
             {**terminal, 'snapshot_after_required': 0}),
            ('ck3_observe_normal_exit_v1', {}, {'snapshot_after_required': False, 'error': 'failed'}),
        ]
        for tool, arguments, result in ordinary:
            with self.subTest(tool=tool, result=result):
                state = production_execute(result)
                asyncio.run(state.execute([{'kind': 'tool', 'tool': tool, 'args': arguments}]))
                self.assertEqual(state.fresh_count, 1)
                self.assertEqual(state.report['steps'][0]['after_snapshot'], {'revision': 8})
        for tool, arguments, result in malformed:
            with self.subTest(tool=tool, result=result):
                state = production_execute(result)
                with self.assertRaises(ValueError):
                    asyncio.run(state.execute([{'kind': 'tool', 'tool': tool, 'args': arguments}]))
                self.assertEqual(state.fresh_count, 0)
                self.assertFalse(state.report['steps'][0]['ok'])

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
