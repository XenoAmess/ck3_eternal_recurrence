"""Portable menu-mode boundaries compiled from the actual shared host source."""
from __future__ import annotations

import argparse
import ast
import asyncio
import copy
from datetime import datetime
import json
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch


REPO = Path(__file__).resolve().parents[1]
HOST = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'


class SharedMenuModLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HOST.read_text(encoding='utf-8-sig')
        tree = ast.parse(source)
        names = {'require_menu_observation_step', 'validate_menu_observation_options',
                 'menu_observation_native_identity', 'observe_frontend_mod_load',
                 'fixture_session', 'load_plan', 'parser', 'lookup', 'resolve',
                 'finished_native_process_exit_zero_proof', 'finished_native_exit_zero_proof',
                 'PlanClient',
                 'require_consistent_frontend_observation', 'wait_for_consistent_frontend'}
        nodes = [node for node in tree.body if getattr(node, 'name', None) in names]
        if {node.name for node in nodes} != names:
            raise AssertionError('The checked-in shared host must provide all real menu boundaries')
        namespace = {'argparse': argparse, 'asyncio': asyncio, 'copy': copy,
                     'datetime': datetime, 'json': json, 'Path': Path, 're': re,
                     'threading': threading, 'time': time, '__doc__': __doc__,
                     'now': lambda: 'SYNTHETIC_ONLY_NOT_ACTUAL_GAME'}
        module = ast.fix_missing_locations(ast.Module(body=[
            ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
            *nodes], type_ignores=[]))
        exec(compile(module, str(HOST), 'exec'), namespace)
        cls.functions = namespace
        cls.real_client = namespace['PlanClient']
        cls.package_src = str(REPO / 'ck3_autonomous_player/src')
        sys.path.insert(0, cls.package_src)
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.ck3_runtime_diagnostics import ENGINE_DIAGNOSTICS_SCHEMA_V1
        cls.current4 = CK3_12004
        cls.engine_schema = ENGINE_DIAGNOSTICS_SCHEMA_V1

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(cls.package_src)

    def args(self, *extra):
        return self.functions['parser']().parse_args([
            '--frontend-mod-load-observation', '--fixture-profile', *extra])

    def identity_packets(self, profile):
        pid, generation = 2468, 7
        pipe = r'\\.\pipe\synthetic-menu-mode-only'
        hello = {'pid': pid, 'connection_generation': generation, 'ck3_build_match': True,
                 'expected_ck3_version': self.current4.game_version,
                 'expected_ck3_sha256': self.current4.executable_sha256,
                 'game_adapter_id': 'ck3-1.20.0.4-msvc-x64', 'game_adapter_status': 'ready'}
        packet = {'pipe': pipe, 'transport_error': None, 'diagnostics': {
            'connected': True, 'bridge_pid': pid, 'connection_generation': generation,
            'pipe_name': pipe, 'hello': hello, 'transport_fatal_error': None, 'last_error': None}}
        launch = {'status': 'ACTUAL_SINGLE_MENU_LAUNCH_RECORDED', 'pid': pid,
                  'ck3_creation_date': 'SYNTHETIC_ONLY_WMI_CREATION_DATE',
                  'profile_dir': str(profile.resolve()),
                  'actual_command': ['synthetic-only-ck3.exe', '-gdpr-compliant', f'-userdir={profile.resolve()}'],
                  'continue_last_save': False, 'load_save_name': None}
        return pipe, packet, launch

    def test_real_cli_excludes_every_campaign_and_action_path(self):
        validate = self.functions['validate_menu_observation_options']
        validate(self.args())
        validate(self.args('--server'))
        # Ordinary modes retain their existing validation owner.
        validate(self.functions['parser']().parse_args(['--frontend-robert-bootstrap']))
        exclusions = [[], ['--saved-campaign-save', 'save.ck3'], ['--saved-campaign-server'],
                      ['--frontend-robert-bootstrap'], ['--frontend-fixture-start-policy', 'policy.json'],
                      ['--frontend-fixture-startup-case-contract', 'contract.json'],
                      ['--frontend-rules-plan', 'rules.json'], ['--frontend-rules-diagnostic'],
                      ['--frontend-rules-diagnostic-new-game'], ['--frontend-diagnostic-only'],
                      ['--allow-verified-direct-bookmarks'], ['--cold-start-checkpoint'], ['--turns', '1'],
                      ['--native-fixture-inbox'], ['--sdk-smoke-test'], ['--sdk-error-smoke-test'],
                      ['--fixture-server'], ['--print-default-plan']]
        for flags in exclusions:
            with self.subTest(flags=flags):
                args = self.args(*flags)
                if not flags:
                    args.fixture_profile = False
                with self.assertRaises(SystemExit):
                    validate(args)
        with tempfile.TemporaryDirectory() as temporary:
            plan = Path(temporary) / 'plan.json'
            plan.write_text(json.dumps({'steps': []}), encoding='utf-8')
            args = self.args('--plan', str(plan))
            validate(args)
            plan.write_text(json.dumps({'steps': [{'tool': 'ck3_activate_frontend_new_game_v1'}]}), encoding='utf-8')
            with self.assertRaises(ValueError):
                validate(args)

    def test_actual_native_identity_rejects_pid_generation_pipe_and_build_drift(self):
        pipe, packet, launch = self.identity_packets(Path('synthetic-profile'))
        bind = self.functions['menu_observation_native_identity']
        value = bind(packet, launch, pipe)
        self.assertEqual(value['bridge_pid'], launch['pid'])
        self.assertEqual(value['connection_generation'], 7)
        cases = [(('diagnostics', 'connected'), False), (('transport_error',), 'broken'),
                 (('diagnostics', 'bridge_pid'), 2469), (('diagnostics', 'bridge_pid'), True),
                 (('diagnostics', 'connection_generation'), 0),
                 (('diagnostics', 'hello', 'connection_generation'), 8),
                 (('diagnostics', 'hello', 'pid'), 2469), (('pipe',), pipe + '-other'),
                 (('diagnostics', 'last_error'), 'error'),
                 (('diagnostics', 'hello', 'game_adapter_status'), 'unsupported'),
                 (('diagnostics', 'hello', 'ck3_build_match'), False),
                 (('diagnostics', 'hello', 'expected_ck3_sha256'), '0' * 64),
                 (('diagnostics', 'hello', 'game_adapter_id'), 'ck3-1.20.0.3-msvc-x64')]
        for keys, invalid in cases:
            with self.subTest(keys=keys, invalid=invalid):
                candidate = copy.deepcopy(packet)
                node = candidate
                for key in keys[:-1]:
                    node = node[key]
                node[keys[-1]] = invalid
                with self.assertRaises((RuntimeError, ValueError)):
                    bind(candidate, launch, pipe)

    def test_actual_session_wrapper_launches_menu_once_without_continue_or_save(self):
        calls = []
        module = ModuleType('xar_autoplayer.native_session')
        profile = Path('synthetic-menu-profile').resolve()
        handle = SimpleNamespace(process=SimpleNamespace(pid=2468), ck3_creation_date='SYNTHETIC_WMI_DATE',
                                 command=['synthetic-only-ck3.exe', f'-userdir={profile}'])
        def launch(*positional, **kwargs):
            calls.append(copy.deepcopy(kwargs))
            return handle
        module.launch = launch
        exec('def _native_session_locked(spec, **kwargs):\n'
             '    launch(spec, continue_last_save=True)\n'
             '    if spec.second_launch:\n'
             '        launch(spec, continue_last_save=True)\n'
             '    return {"kind": "SYNTHETIC_ONLY_NO_GAME"}\n'
             'def native_session(spec, **kwargs):\n'
             '    return _native_session_locked(spec, **kwargs)\n', vars(module))
        args = self.args()
        stop = threading.Event()
        spec = SimpleNamespace(profile_dir=profile, second_launch=False)
        record = {'status': 'WAITING_FOR_ACTUAL_SINGLE_MENU_LAUNCH'}
        with patch.dict(sys.modules, {'xar_autoplayer.native_session': module}):
            result = self.functions['fixture_session'](spec, object(), args, stop, launch_record=record)
            self.assertTrue(result['fixture_profile'])
            self.assertEqual(len(calls), 1)
            self.assertIs(calls[0]['continue_last_save'], False)
            self.assertIs(calls[0]['verify_prepared_profile'], False)
            self.assertEqual(record['pid'], handle.process.pid)
            self.assertEqual(record['ck3_creation_date'], handle.ck3_creation_date)
            self.assertEqual(record['profile_dir'], str(profile))
            self.assertEqual(record['actual_command'], handle.command)
            self.assertIs(module.launch, launch)
            calls.clear()
            spec.second_launch = True
            with self.assertRaisesRegex(RuntimeError, 'cannot relaunch'):
                self.functions['fixture_session'](spec, object(), args, stop,
                    launch_record={'status': 'WAITING_FOR_ACTUAL_SINGLE_MENU_LAUNCH'})
            self.assertEqual(len(calls), 1)  # second attempt is rejected before launch
            calls.clear()
            args.frontend_mod_load_observation = False
            spec.second_launch = False
            self.functions['fixture_session'](spec, object(), args, stop)
            self.assertEqual(len(calls), 1)
            self.assertIs(calls[0]['continue_last_save'], True)

    def test_real_menu_observer_uses_complete_two_poll_frontend_and_profile_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            profile = state_dir / 'profile'
            pipe, diagnostics, launch = self.identity_packets(profile)
            route = {'schema': 'ck3-frontend-gui-route-v1', 'accepted': True, 'route': 'main_menu'}
            tree = {'schema': 'ck3-frontend-gui-tree-inspection-v1', 'accepted': True,
                    'status': 'available', 'scope_root_name': 'mainmenu_panel_bottom',
                    'root_available': True, 'read_only': True, 'truncated': False, 'widget_count': 2,
                    'widgets': [{'runtime_name': 'mainmenu_panel_bottom', 'vtable_rva': 1,
                                 'effective_visible': True, 'child_path': ''},
                                {'runtime_name': 'new_game_button', 'vtable_rva': 2,
                                 'effective_visible': True, 'enabled': True, 'child_path': '0'}]}
            engine = {'schema': self.engine_schema, 'read_only': True, 'profile_dir': str(profile.resolve()),
                      'logs': {'system': {'exists': False}}, 'path_argument_accepted': False,
                      'regex_argument_accepted': False}
            calls = []
            async def call(name, arguments=None):
                calls.append((name, copy.deepcopy(arguments)))
                if name == 'ck3_query_frontend_gui_route_v1': return copy.deepcopy(route)
                if name == 'ck3_inspect_frontend_gui_tree_v1': return copy.deepcopy(tree)
                if name == 'ck3_migration_pipe_diagnostics': return copy.deepcopy(diagnostics)
                if name == 'ck3_query_engine_diagnostics_v1': return copy.deepcopy(engine)
                self.fail('Unexpected action or gameplay query: ' + name)
            client = SimpleNamespace(args=SimpleNamespace(state_dir=state_dir, bridge_pipe=pipe), call=call,
                tools={name: {} for name in ('ck3_query_frontend_gui_route_v1', 'ck3_inspect_frontend_gui_tree_v1',
                    'ck3_migration_pipe_diagnostics', 'ck3_query_engine_diagnostics_v1', 'ck3_query_engine_log_literals_v1')})
            report = {'frontend_mod_load_launch': launch}
            writes = []
            event = threading.Event()
            observe = self.functions['observe_frontend_mod_load']
            value = asyncio.run(observe(client, report=report, write=lambda: writes.append(copy.deepcopy(report)),
                                      timeout=1, managed_done=event, poll_interval=0))
            self.assertEqual(value['status'], 'ACTUAL_STABLE_MAIN_MENU_OBSERVED_READ_ONLY')
            self.assertEqual(value['proof']['consecutive_consistent_observations'], 2)
            self.assertEqual([name for name, _ in calls].count('ck3_query_frontend_gui_route_v1'), 4)
            self.assertEqual([name for name, _ in calls].count('ck3_inspect_frontend_gui_tree_v1'), 2)
            self.assertIs(value['product_acceptance_proven'], False)
            self.assertIs(value['actual_cache_mount_proven'], False)
            self.assertIs(value['campaign_started'], False)
            self.assertEqual(value['actions_submitted'], 0)
            self.assertNotIn('snapshot_id', report['readiness'])
            self.assertNotIn('actual_cache_path', value)
            self.assertTrue(writes)
            for invalid in ('-continuelastsave', '-loadsave=old', '-userdir=other'):
                with self.subTest(command=invalid):
                    bad_launch = copy.deepcopy(launch)
                    bad_launch['actual_command'].append(invalid)
                    with self.assertRaises(RuntimeError):
                        asyncio.run(observe(client, report={'frontend_mod_load_launch': bad_launch}, write=lambda: None,
                                            timeout=1, managed_done=event, poll_interval=0))
            engine['profile_dir'] = str(state_dir / 'other-profile')
            with self.assertRaisesRegex(RuntimeError, 'profile engine diagnostics'):
                asyncio.run(observe(client, report={'frontend_mod_load_launch': launch}, write=lambda: None,
                                    timeout=1, managed_done=event, poll_interval=0))
            event.set()
            with self.assertRaises(RuntimeError):
                asyncio.run(observe(client, report={'frontend_mod_load_launch': launch}, write=lambda: None,
                                    timeout=1, managed_done=event, poll_interval=0))

    def client(self, report=None):
        client = self.real_client.__new__(self.real_client)
        client.args = self.args()
        client.report = report if report is not None else {'steps': []}
        client.results, client.snapshot, client.episode_identity = {}, {}, None
        client.managed_done = threading.Event()
        client.write = lambda: None
        client.call = AsyncMock(return_value={'read_only': True})
        client.invoke = AsyncMock(side_effect=AssertionError('Menu mode must not invoke a gameplay action'))
        client.fresh = AsyncMock(side_effect=AssertionError('Menu mode must not require a playable-map snapshot'))
        return client

    def test_real_plan_executor_has_no_gameplay_dispatch_or_map_snapshot(self):
        client = self.client()
        asyncio.run(client.execute([]))
        self.assertEqual(client.report['steps'], [])
        row = {'tool': 'ck3_query_engine_log_literals_v1',
               'args': {'log_name': 'system', 'literals': ['SYNTHETIC_ONLY'], 'sample_limit': 1}}
        asyncio.run(client.execute([row]))
        client.call.assert_awaited_once_with(row['tool'], row['args'])
        self.assertIs(client.report['steps'][0]['ok'], True)
        client.fresh.assert_not_awaited()
        client.invoke.assert_not_awaited()
        for step in ({'kind': 'advance_day', 'days': 1}, {'kind': 'raw_step', 'step': 'pause-map'},
                     {'tool': 'ck3_execute_step', 'args': {'step': 'pause-map'}},
                     {'tool': 'ck3_activate_frontend_new_game_v1'},
                     {'tool': 'ck3_activate_frontend_start_1066_bookmark_character_v1'},
                     {'kind': 'frontend_read_only', 'tool': 'ck3_take_snapshot'},
                     {'kind': 'hold'}, {'kind': 'episode_identity_anchor'}):
            with self.subTest(step=step):
                blocked = self.client()
                with self.assertRaises(ValueError):
                    asyncio.run(blocked.execute([step]))
                blocked.call.assert_not_awaited()
                blocked.invoke.assert_not_awaited()
                self.assertIs(blocked.report['steps'][-1]['ok'], False)

    def test_real_finish_hold_requires_original_completion_and_cleanup_proof(self):
        pipe = r'\\.\pipe\synthetic-menu-mode-only'
        report = {'steps': [], 'fixture_only': False, 'error': None, 'pipe': pipe,
                  'session': {'error': None, 'report': {
                      'kind': 'ck3_native_headless_session', 'mode': 'native-headless', 'format_version': 1,
                      'ok': True, 'error': None, 'exit_reason': 'process_exit', 'process_exit_code': 0,
                      'pid': 2468, 'pipe': pipe, 'started_at': '2026-10-08T10:00:00+00:00',
                      'finished_at': '2026-10-08T10:00:10+00:00', 'shutdown': {
                          'ok': True, 'cleanup_proven': True, 'tree_gone': True, 'ck3_pid': 2468,
                          'ck3_exit_code': 0, 'job_active_processes_final': 0, 'contract_errors': [],
                          'watchdog_state_after': 'absent', 'nonce': 'a' * 32,
                          'ck3_creation_date': 'SYNTHETIC_WMI_DATE', 'control_files_absent': {'ck3.json': True},
                          'final_ck3_inventory': {'tasklist_returncode': 0, 'tasklist_pids': [], 'wmi_pids': [],
                                                 'native_pids': [], 'processes': []}}}}}
        step = {'id': 'normal-finish', 'kind': 'finish_hold'}
        pending = self.client(copy.deepcopy(report))
        with self.assertRaises(RuntimeError):
            asyncio.run(pending.execute([step]))
        self.assertNotIn('hold_finished_by_control_plan', pending.report)
        for key, value in (('process_exit_code', 1), ('process_exit_code', False)):
            invalid = copy.deepcopy(report)
            invalid['session']['report'][key] = value
            client = self.client(invalid)
            client.managed_done.set()
            with self.assertRaises(RuntimeError):
                asyncio.run(client.execute([step]))
            self.assertNotIn('hold_finished_by_control_plan', client.report)
        invalid = copy.deepcopy(report)
        invalid['session']['report']['shutdown']['cleanup_proven'] = False
        blocked = self.client(invalid)
        blocked.managed_done.set()
        with self.assertRaises(RuntimeError):
            asyncio.run(blocked.execute([step]))
        qualified = self.client(copy.deepcopy(report))
        qualified.managed_done.set()
        asyncio.run(qualified.execute([step]))
        self.assertIs(qualified.report['hold_finished_by_control_plan'], True)
        self.assertIs(qualified.report['steps'][-1]['ok'], True)
        self.assertEqual(qualified.report['post_exit_finish_hold']['proof']['process_exit_code'], 0)
        self.assertIs(qualified.report['post_exit_finish_hold']['proof']['alive_or_business_credit'], False)
        qualified.fresh.assert_not_awaited()
        qualified.invoke.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
