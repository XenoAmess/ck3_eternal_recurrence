"""Portable checks of actual driver UI method and existing campaign binding helper."""
from __future__ import annotations

import argparse
import ast
import copy
from pathlib import Path
import sys
from types import MethodType
import unittest

REPO = Path(__file__).resolve().parents[1]
DRIVER_SOURCE: Path | None = None


def actual_functions(path: Path, names: set[str], namespace: dict) -> dict:
    tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    nodes = []
    for name in names:
        found = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name]
        if len(found) != 1:
            raise RuntimeError('actual source function not unique: ' + name)
        nodes.extend(found)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class Fixture:
    def __init__(self, method, before, raw, after=None):
        self.before, self.after, self.raw = before, after or before, raw
        self.reads = 0
        self.calls, self.records = [], []
        self._ingame_ui_v1 = MethodType(method, self)

    def take_snapshot(self):
        self.reads += 1
        return copy.deepcopy(self.before if self.reads == 1 else self.after)

    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append((step, copy.deepcopy(kwargs)))
        return copy.deepcopy(self.raw)

    def _record_command(self, step, **kwargs):
        self.records.append((step, copy.deepcopy(kwargs)))


class ManagedUiBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError
        from xar_autoplayer.bridge.title_map_navigation_contract import (
            normalize_title_map_navigation_v1_binding, managed_campaign_title_map_navigation_v1_binding)
        from xar_autoplayer.bridge.version_identity import CK3_12004
        cls.build = CK3_12004
        cls.frame_error = BridgeUnavailableError
        cls.revision_error = PreSubmissionRevisionMismatchError
        source = DRIVER_SOURCE or REPO / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
        namespace = {'__package__': 'xar_autoplayer.bridge', 'copy': copy,
            'BridgeUnavailableError': BridgeUnavailableError,
            'PreSubmissionRevisionMismatchError': PreSubmissionRevisionMismatchError,
            'normalize_title_map_navigation_v1_binding': normalize_title_map_navigation_v1_binding,
            'managed_campaign_title_map_navigation_v1_binding': managed_campaign_title_map_navigation_v1_binding}
        cls.functions = actual_functions(source, {'_ingame_ui_v1', '_same_paused_native_frame',
            '_title_map_navigation_binding_from_snapshot', '_title_camera_navigation_binding_from_snapshot'}, namespace)
        # Reuse existing raw-result fixture; never import/run its old suite.
        cls.raw_functions = actual_functions(REPO / 'ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py',
            {'result', 'snapshot'}, {})

    def snapshot(self, managed=True):
        value = self.raw_functions['snapshot']()
        if not managed:
            return value
        value.update(episode_run_id=None, episode_projection='native_campaign', format_version=1,
            backend_id='native-headless', source='injected-dll-named-pipe', active_event=None, local_player_id=1,
            managed_campaign_run_binding={'run_id': 'portable-managed-run', 'state_dir': 'portable/state',
                'bridge_pipe': 'portable-pipe', 'host_path': 'portable/host.py', 'frozen_argv_sha256': 'a' * 64})
        value['played_character']['source'] = 'native'
        value['diagnostics'].update(connected=True, bridge_pid=1234, pipe_name='portable-pipe',
            hello={'pid':1234, 'connection_generation':2, 'game_adapter_id':'ck3-1.20.0.4-msvc-x64',
                'ck3_build_match':True, 'expected_ck3_version':self.build.game_version,
                'expected_ck3_sha256':self.build.executable_sha256},
            last_heartbeat={'pid':1234, 'main_thread_query_mailbox_v1':{
                'installed':True, 'ready':True, 'stop':False, 'failure':0, 'owner_tid':77, 'current_tid':77,
                'pump_epochs':14, 'owner_verified_pump_epochs':14, 'stamp_read_success':True,
                'date_raw':value['date_raw']},
                'snapshot_observer_12002':{'read_in_progress':False,'started_ms':20,'completed_ms':21}})
        return value

    def raw(self, managed=True, operation='query', kind='army', subject=0):
        value = self.raw_functions['result'](kind, operation, subject)
        if managed:
            value.update(native_backend_id=self.build.backend_id('ingame-ui-v1'),
                game_version=self.build.game_version, executable_sha256=self.build.executable_sha256,
                current_subject_id=subject, native_army_id=83,
                owner_character_id_available=True, owner_character_id=29829)
        return value

    def fixture(self, before=None, raw=None, after=None):
        return Fixture(self.functions['_ingame_ui_v1'], before or self.snapshot(), raw or self.raw(), after)

    def query(self, driver):
        return driver._ingame_ui_v1('query', 'army', 0, expected_revision=4)

    def test_actual_episode_binding_and_character_path_remain(self):
        before = self.snapshot(False)
        self.assertEqual(self.functions['_title_camera_navigation_binding_from_snapshot'](before),
            self.functions['_title_map_navigation_binding_from_snapshot'](before))
        driver = self.fixture(before, self.raw(False, 'open_character', 'character', 33437))
        got = driver._ingame_ui_v1('open_character', 'character', 33437, expected_revision=4)
        self.assertEqual(got['episode_run_id'], before['episode_run_id'])
        self.assertTrue(got['verification_pending'])
        self.assertEqual(len(driver.calls), 1)

    def test_actual_managed_ui_cross_call_without_fabricated_episode(self):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'episode_run_id'):
            self.functions['_title_map_navigation_binding_from_snapshot'](before)
        driver = self.fixture(before)
        got = self.query(driver)
        self.assertIsNone(got['episode_run_id'])
        self.assertEqual(got['queried_revision'], 4)
        self.assertEqual(got['queried_native_revision'], 3)
        self.assertEqual(got['queried_connection_generation'], 2)
        self.assertEqual(driver.calls[0][1]['request_fields'], {'window_kind':'army', 'subject_id':0})
        self.assertTrue(driver.records[-1][1]['ok'])

    def test_unbound_transport_owner_actor_or_frame_never_dispatches(self):
        mutations = [
            ('diagnostics.connected', False), ('diagnostics.pipe_name', 'another-pipe'),
            ('diagnostics.hello.pid', 4321), ('diagnostics.hello.connection_generation', 3),
            ('diagnostics.last_heartbeat.pid', 4321),
            ('diagnostics.last_heartbeat.main_thread_query_mailbox_v1.current_tid', 78),
            ('diagnostics.last_heartbeat.main_thread_query_mailbox_v1.date_raw', 0),
            ('diagnostics.last_heartbeat.snapshot_observer_12002.read_in_progress', True),
            ('played_character.character_id', 0), ('native_revision', 0), ('active_event', {'instance':1})]
        for path, value in mutations:
            before = self.snapshot()
            target = before
            keys = path.split('.')
            for key in keys[:-1]: target = target[key]
            target[keys[-1]] = value
            driver = self.fixture(before)
            with self.subTest(path=path), self.assertRaises((ValueError, self.frame_error)):
                self.query(driver)
            self.assertEqual(driver.calls, [])
        driver = self.fixture()
        with self.assertRaises(self.revision_error):
            driver._ingame_ui_v1('query', 'army', 0, expected_revision=3)
        self.assertEqual(driver.calls, [])

    def test_changed_managed_identity_preserves_failure_and_raw_once(self):
        before = self.snapshot()
        endings = []
        for field, value in [('run_id','different-run'), ('bridge_pipe','different-pipe'),
            ('frozen_argv_sha256','b' * 64)]:
            after = copy.deepcopy(before)
            after['managed_campaign_run_binding'][field] = value
            if field == 'bridge_pipe': after['diagnostics']['pipe_name'] = value
            endings.append((field, after))
        for field, value in [('local_player_id',2), ('revision',5), ('native_revision',4), ('snapshot_id','native:4')]:
            after = copy.deepcopy(before); after[field] = value; endings.append((field, after))
        after = copy.deepcopy(before); after['played_character']['character_id'] = 33437; endings.append(('actor', after))
        after = copy.deepcopy(before)
        after['diagnostics']['connection_generation'] = after['diagnostics']['hello']['connection_generation'] = 3
        endings.append(('generation', after))
        after = copy.deepcopy(before)
        after['diagnostics']['bridge_pid'] = after['diagnostics']['hello']['pid'] = after['diagnostics']['last_heartbeat']['pid'] = 4321
        endings.append(('PID', after))
        after = copy.deepcopy(before)
        mailbox = after['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']
        mailbox['owner_tid'] = mailbox['current_tid'] = 78
        endings.append(('coherently_changed_owner', after))
        after = copy.deepcopy(before); after['date_raw'] += 24
        after['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['date_raw'] = after['date_raw']
        endings.append(('date', after))
        for field, after in endings:
            driver = self.fixture(before, self.raw(), after)
            with self.subTest(field=field), self.assertRaises((ValueError, self.frame_error)):
                self.query(driver)
            self.assertEqual(len(driver.calls), 1)
            self.assertFalse(driver.records[-1][1]['ok'])
            self.assertEqual(driver.records[-1][1]['result']['raw_native_ui_result'], driver.raw)

    def test_current_character_scope_remains_rejected_without_send(self):
        driver = self.fixture()
        with self.assertRaisesRegex(ValueError, 'army query and select only'):
            driver._ingame_ui_v1('open_character', 'character', 33437, expected_revision=4)
        self.assertEqual(driver.calls, [])

    def test_actual_result_revision_actor_date_normalizer_remains(self):
        for key, value in [('native_revision',4), ('played_character_id',33437), ('date_raw',0)]:
            raw = self.raw(); raw[key] = value
            driver = self.fixture(raw=raw)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                self.query(driver)
            self.assertEqual(len(driver.calls), 1)
            self.assertEqual(driver.records[-1][1]['result']['raw_native_ui_result'], raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=REPO)
    parser.add_argument('--driver-source', type=Path)
    args, unittest_args = parser.parse_known_args()
    REPO = args.repo_root.resolve()
    DRIVER_SOURCE = args.driver_source.resolve() if args.driver_source else None
    unittest.main(argv=[sys.argv[0], *unittest_args])
