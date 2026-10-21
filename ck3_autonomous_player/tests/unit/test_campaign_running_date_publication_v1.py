"""Typed actual-guard producer to readonly pending classifier regressions."""
from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.campaign_running_date_publication_v1 import AdvanceRequestV1, advance_frame_date_v1, pending_running_date_v1

Object = dict[str, object]
HOST = Path(__file__).resolve().parents[2] / 'native_bridge/research/run_ck3_12002_mcp_live.py'


def obj(value: object) -> Object:
    if not isinstance(value, dict):
        raise ValueError('Test object required')
    result: Object = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError('Test string keys required')
        result[key] = item
    return result


def raw_node(value: Object, path: tuple[str, ...]) -> Object:
    current: object = value
    for key in path:
        if not isinstance(current, dict):
            raise ValueError('Test nested object required')
        current = current[key]
    if not isinstance(current, dict):
        raise ValueError('Test final object required')
    result: Object = current
    return result


def frame(*, snapshot_date: int = 1024, mailbox_date: int = 1000) -> Object:
    return {'episode_projection': 'native_campaign', 'backend_id': 'native-headless',
            'source': 'injected-dll-named-pipe', 'map_ready': True, 'format_version': 1,
            'complete_snapshot': True, 'paused': False, 'played_character': {'character_id': 47, 'alive': True, 'source': 'native'},
            'active_event': None, 'one_life_terminal_reason': None, 'snapshot_id': 'native:12',
            'native_revision': 12, 'revision': 13, 'date_raw': snapshot_date, 'local_player_id': 1, 'speed': 1,
            'diagnostics': {'connected': True, 'semantic_state_available': True, 'last_error': None,
            'transport_fatal_error': None, 'bridge_pid': 400, 'connection_generation': 1,
            'rejected_state_snapshot_count': 0, 'pipe_name': 'synthetic-publication',
            'hello': {'expected_ck3_version': '1.20.0.4',
                'expected_ck3_sha256': '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518',
                'game_adapter_id': 'ck3-1.20.0.4-msvc-x64', 'ck3_build_match': True, 'connection_generation': 1, 'pid': 400},
            'last_heartbeat': {'pid': 400, 'main_thread_query_mailbox_v1': {
                'owner_tid': 500, 'current_tid': 500, 'owner_verified_pump_epochs': 20,
                'installed': True, 'ready': False, 'stop': False, 'failure': 0, 'stamp_read_success': True,
                'date_raw': mailbox_date, 'application_main_observed': True, 'paused': False,
                'paused_main_thread_observed': False, 'consecutive_verified': 0}}}}


def source() -> Object:
    return {'identity': (400, 1, 47, 1, 1, 'synthetic-publication', 500, None),
            'date': 1000, 'revision': 11, 'native_revision': 10, 'pump': 19, 'rejections': 0, 'pause_transition': False}


def original_error(snapshot: Object) -> RuntimeError:
    tree = ast.parse(HOST.read_text(encoding='utf-8-sig'))
    names = {'_campaign_pause_frame_rejection_detail', 'campaign_pause_frame_binding'}
    nodes: list[ast.stmt] = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if len(nodes) != 2:
        raise ValueError('Actual original guard seam missing')
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(HOST), 'exec'), namespace)
    function: object = namespace['campaign_pause_frame_binding']
    if not callable(function):
        raise ValueError('Actual original guard must be callable')
    try:
        result: object = function(snapshot, allow_running=True)
    except RuntimeError as error:
        return error
    raise AssertionError('Original guard unexpectedly admitted pending frame: ' + repr(result))


class PublicationContractTests(unittest.TestCase):
    def test_actual_modified_host_defs_have_no_strict_diagnostics(self) -> None:
        root = Path(__file__).resolve().parents[3]
        helper = root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_running_date_publication_v1.py'
        environment = os.environ.copy()
        environment['MYPYPATH'] = os.pathsep.join((str(root / 'tools'), str(root / 'ck3_autonomous_player/src')))
        command = [sys.executable, '-B', '-X', 'utf8', '-m', 'mypy', '--strict', '--follow-imports=skip',
            '--no-incremental', '--cache-dir', 'nul', '--no-pretty', '--no-color-output',
            '--show-column-numbers', '--hide-error-context', '--no-error-summary', str(HOST), str(helper)]
        completed = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, encoding='utf-8')
        # Full diagnostics stay in the real test/CI stdout; only owned defs are
        # gated. This deliberately does not certify the entire historical host.
        print(completed.stdout, end='')
        print(completed.stderr, end='')
        self.assertIn(completed.returncode, (0, 1), 'Actual checker failed before producing type diagnostics')
        tree = ast.parse(HOST.read_text(encoding='utf-8-sig'))
        ranges: list[tuple[int, int]] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == '_campaign_pending_running_date':
                ranges.append((node.lineno, node.end_lineno or node.lineno))
            if isinstance(node, ast.ClassDef) and node.name == 'PlanClient':
                for method in node.body:
                    if isinstance(method, ast.AsyncFunctionDef) and method.name == 'advance':
                        ranges.append((method.lineno, method.end_lineno or method.lineno))
        self.assertEqual(len(ranges), 2, 'Actual owned host defs missing')
        pattern = re.compile(r'^(.+?):([0-9]+):[0-9]+: error: (.*)$')
        owned: list[str] = []
        for line in completed.stdout.splitlines():
            match = pattern.match(line)
            if match is not None and Path(match.group(1)).resolve() == HOST.resolve():
                number = int(match.group(2))
                if any(start <= number <= end for start, end in ranges):
                    owned.append(line)
        self.assertEqual(owned, [], 'Strict type errors in the actual modified host defs')

    def test_advance_request_is_typed_and_rejects_bad_counts_or_timeouts(self) -> None:
        self.assertEqual(AdvanceRequestV1.parse({}, 5), AdvanceRequestV1(1, 5.0, False))
        self.assertEqual(AdvanceRequestV1.parse({'days': 1, 'timeout': .3, 'wait_for_played_character_change': True}, 5),
                         AdvanceRequestV1(1, .3, True))
        cases: list[object] = [None, [], {'days': True}, {'days': 1.0}, {'days': 0}, {'days': -1},
            {'days': None}, {'timeout': None}, {'timeout': True}, {'timeout': float('inf')},
            {'timeout': float('nan')}, {'timeout': 0}, {'timeout': -1}, {'timeout': 6},
            {'timeout': 10**1000}, {'wait_for_played_character_change': None}]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                AdvanceRequestV1.parse(value, 5)
        for maximum in (None, True, float('inf'), float('nan'), 0):
            with self.subTest(maximum=maximum), self.assertRaises(ValueError):
                AdvanceRequestV1.parse({}, maximum)
        self.assertEqual(advance_frame_date_v1({'date_raw': 1024}), 1024)
        for value in (None, {}, {'date_raw': True}, {'date_raw': 1.0}, {'date_raw': '1024'}):
            with self.subTest(frame=value), self.assertRaises(ValueError):
                advance_frame_date_v1(value)

    def test_both_actual_directions_stay_unqualified_and_do_not_repair(self) -> None:
        for snapshot_date, mailbox_date, direction in ((1024, 1000, 'snapshot-ahead'), (1000, 1024, 'mailbox-ahead')):
            value = frame(snapshot_date=snapshot_date, mailbox_date=mailbox_date)
            unchanged = copy.deepcopy(value)
            pending = pending_running_date_v1(source(), value, original_error(value))
            self.assertEqual(pending.direction, direction)
            self.assertEqual((pending.date_raw, pending.mailbox_date_raw), (snapshot_date, mailbox_date))
            self.assertEqual(value, unchanged)

    def test_internal_binding_json_roundtrip_is_explicit(self) -> None:
        value = frame()
        original = pending_running_date_v1(source(), value, original_error(value))
        decoded: object = json.loads(json.dumps(source()))
        self.assertEqual(pending_running_date_v1(decoded, value, original_error(value)), original)

    def test_wrong_numeric_aliases_missing_null_and_source_binding_rejected(self) -> None:
        for key, bad in (('date_raw', True), ('date_raw', 1024.0), ('revision', True), ('native_revision', None)):
            value = frame()
            error = original_error(value)
            value[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(RuntimeError) as rejected:
                pending_running_date_v1(source(), value, error)
            self.assertIs(rejected.exception, error)
        for bad_source in (None, {}, {'identity': None}, {**source(), 'pump': True}, {**source(), 'rejections': 0.0},
                           {**source(), 'pending_mailbox_date': None}, {**source(), 'clock_alias': 1000},
                           {key: value for key, value in source().items() if key != 'pause_transition'}):
            value = frame()
            error = original_error(value)
            with self.subTest(source=bad_source), self.assertRaises(RuntimeError) as rejected:
                pending_running_date_v1(bad_source, value, error)
            self.assertIs(rejected.exception, error)

    def test_clock_owner_pump_and_rejection_changes_are_not_waitable(self) -> None:
        paths = [(('diagnostics',), 'bridge_pid', 401), (('played_character',), 'character_id', 48),
                 (('diagnostics',), 'connection_generation', 2), (('diagnostics',), 'pipe_name', 'foreign'),
                 (('diagnostics',), 'rejected_state_snapshot_count', 1),
                 (('diagnostics', 'last_heartbeat', 'main_thread_query_mailbox_v1'), 'owner_verified_pump_epochs', 18)]
        for path, key, bad in paths:
            value = frame()
            error = original_error(value)
            raw_node(value, path)[key] = bad
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                pending_running_date_v1(source(), value, error)
        for snapshot_date, mailbox_date in ((1048, 1000), (1000, 976), (976, 1000), (1024, 999)):
            value = frame(snapshot_date=snapshot_date, mailbox_date=mailbox_date)
            with self.subTest(dates=(snapshot_date, mailbox_date)), self.assertRaises(RuntimeError):
                pending_running_date_v1(source(), value, original_error(value))

    def test_event_interaction_and_changed_diagnostic_are_not_waitable(self) -> None:
        for key in ('active_event', 'pending_character_interaction'):
            value = frame()
            error = original_error(value)
            value[key] = {'instance_id': 1}
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                pending_running_date_v1(source(), value, error)
        value = frame()
        for key, bad in (('first_failed_condition', True), ('conditions', None), ('schema', 'another')):
            error = original_error(value)
            detail = raw_node(obj(error.__dict__), ('ck3_campaign_pause_frame_diagnostic',))
            detail[key] = bad
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                pending_running_date_v1(source(), value, error)
        error = original_error(value)
        detail = raw_node(obj(error.__dict__), ('ck3_campaign_pause_frame_diagnostic',))
        conditions = detail['conditions']
        if not isinstance(conditions, list) or not isinstance(conditions[31], dict):
            raise ValueError('Actual diagnostic conditions required')
        del conditions[31]['unavailable_reason']
        with self.assertRaises(RuntimeError):
            pending_running_date_v1(source(), value, error)

    def test_each_observed_clock_is_monotonic_independently(self) -> None:
        first = frame()
        pending = pending_running_date_v1(source(), first, original_error(first))
        before = pending.to_host_binding()
        repeated = frame()
        self.assertEqual(pending_running_date_v1(before, repeated, original_error(repeated)), pending)
        backward = frame(snapshot_date=1000, mailbox_date=1024)
        with self.assertRaises(RuntimeError):
            pending_running_date_v1(before, backward, original_error(backward))

    def test_large_internal_generation_remains_exact_and_wrong_error_rejected(self) -> None:
        large = 2**53 + 1
        value, before = frame(), source()
        raw_node(value, ('diagnostics',))['connection_generation'] = large
        raw_node(value, ('diagnostics', 'hello'))['connection_generation'] = large
        before['identity'] = (400, large, 47, 1, 1, 'synthetic-publication', 500, None)
        pending = pending_running_date_v1(before, value, original_error(value))
        self.assertEqual(pending.identity[1], large)
        for wrong in (None, True, 'error', ValueError('wrong')):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                pending_running_date_v1(before, value, wrong)


if __name__ == '__main__':
    unittest.main()
