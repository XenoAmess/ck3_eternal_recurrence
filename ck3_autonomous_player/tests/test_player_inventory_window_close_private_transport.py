"""Actual shared consumers; native DTOs and managed-source admission are authored fixtures."""
from pathlib import Path
from copy import deepcopy
import ast
import importlib.util
import types
import unittest
from unittest.mock import patch
from xar_autoplayer.bridge import player_inventory_window_close_private_transport_v1 as C
from xar_autoplayer.bridge import player_inventory_window_private_transport_v1 as I
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.version_identity import CK3_12004

ROOT = Path(__file__).resolve().parents[2]
TOOLS = frozenset({'ck3_query_player_inventory_window_close_v1', 'ck3_close_player_inventory_window_v1',
    'ck3_query_player_inventory_window_close_post_v1'})
OPEN_TOOLS = {'ck3_open_player_inventory_window_v1', 'ck3_query_player_inventory_window_open_post_v1'}
SOURCE_SHA = 'b' * 64


def view(*, epoch=10, hidden=False, generation=1):
    return {'available': True, 'native_revision': 77, 'capture_epoch': epoch, 'date_raw': 500,
        'game_pid': 4242, 'connection_generation': generation, 'played_character_id': 100,
        'selected_character_id': 100, 'window_present': True, 'root_present': True,
        'native_visible': not hidden, 'effective_visible': not hidden, 'current_player_selected': True}


def body(operation, *, mode='pending', has_intent=True, original=None, generation=1):
    current = view(epoch=12 if operation != 'close' else 10,
        hidden=mode in {'resolved', 'already_hidden'}, generation=generation)
    claimed = has_intent and mode not in {'already_hidden', 'pending_rejected', 'pre_rejected'}
    resolved = operation == 'post' and mode == 'resolved'
    status = ('inventory_window_observed' if operation == 'query' else
        ('inventory_window_closed_observed' if resolved else
            'inventory_intent_previously_resolved_current_window_not_observed' if mode == 'historical' else
            'inventory_intent_pending_or_unknown') if operation == 'post' else
        'inventory_already_hidden_no_call' if mode == 'already_hidden' else
        'inventory_close_pending_or_once_intent_rejected' if mode == 'pending_rejected' else
        'inventory_close_gui_sources_unverified' if mode == 'pre_rejected' else 'inventory_close_invoked_post_pending')
    return {'schema': 'ck3_12004_player_inventory_window_close_v1', 'game_version': CK3_12004.game_version,
        'executable_sha256': CK3_12004.executable_sha256, 'operation': operation, 'read_only': operation != 'close',
        'available': True, 'unavailable_reason': None, 'loaded_code_pins_verified': True,
        'loaded_gui_sources_verified': True, 'current': current, 'intent_sequence': 17 if claimed else 0,
        'intent_found': claimed, 'once_intent_consumed': claimed, 'invoked': claimed, 'call_returned': claimed,
        'needs_recovery': claimed and not resolved and mode != 'historical', 'desired_window_observed': resolved,
        'status': status, 'before': deepcopy(original or view()) if claimed else deepcopy(current) if operation == 'close' else None,
        'after': deepcopy(current) if operation == 'post' else None,
        'artifact_equipped_observed': False, 'actor_aggregate_observed': False,
        'personal_net_effect_attributed': False, 'business_outcome_observed': False, 'automatic_retry': False}


class Endpoint:
    pipe_name = r'\\.\pipe\inventory-close-authored-fixture-only'
    def __init__(self):
        self.requests = []; self.mode = 'pending'; self.has_intent = False; self.generation = 1
        self.original = view(); self.mutate = None; self.reject_close = False; self.not_found = False
    def start(self, on_frame, on_disconnect): self.on_frame = on_frame
    def publish(self, frame): self.on_frame(deepcopy(frame))
    def transport_error(self): return None
    def close(self): pass
    def send(self, request):
        self.requests.append(deepcopy(request))
        if request.get('type') != 'execute_step': return
        op = {C.QUERY: 'query', C.CLOSE: 'close', C.POST: 'post'}[request['step']]
        if op == 'close' and self.mode not in {'already_hidden', 'pending_rejected', 'pre_rejected'}:
            self.has_intent = True
        if (self.reject_close and op == 'close') or (self.not_found and op == 'post'):
            self.publish({'type': 'command_result', 'protocol_version': 1, 'request_id': request['request_id'],
                'ok': False, 'error': 'inventory_close_intent_not_found_do_not_replay' if op == 'post' else 'authored_unknown_ack'})
            return
        value = body(op, mode=self.mode, has_intent=self.has_intent, original=self.original, generation=self.generation)
        packet = {'type': 'command_result', 'protocol_version': 1, 'request_id': request['request_id'], 'ok': True,
            'result': {'step': request['step'], 'accepted': True, 'private_build': True, 'read_only': op != 'close',
                'advertised': False, 'game_version': CK3_12004.game_version,
                'executable_sha256': CK3_12004.executable_sha256,
                'backend_id': CK3_12004.backend_id('player-inventory-window-close-v1-private'),
                'domain_key': C.DOMAIN, 'snapshot_revision': 77, 'date_raw': 500, 'game_pid': 4242,
                'connection_generation': self.generation, 'status': 'observed', C.KEY: value}}
        if self.mutate: self.mutate(packet)
        self.publish(packet)


def publish_current(endpoint):
    endpoint.publish({'type': 'hello', 'protocol_version': 1, 'bridge_version': 'authored-close-only', 'pid': 4242,
        'session_generation': 0, 'connection_generation': endpoint.generation, 'ck3_build_match': True,
        'expected_ck3_version': CK3_12004.game_version, 'expected_ck3_sha256': CK3_12004.executable_sha256,
        'capabilities': ['game.state.snapshot']})
    endpoint.publish({'type': 'state_snapshot', 'protocol_version': 1, 'snapshot_id': 'native:authored-close', 'revision': 77,
        'state': {'phase': 'map_hud', 'date': 'authored', 'date_raw': 500, 'speed': 1, 'paused': True, 'map_ready': True,
            'history': [], 'active_event': None, 'pending_character_interaction': None, 'player_armies': [], 'active_wars': [],
            'played_character': {'character_id': 100, 'alive': True}}})


def driver(*, enabled=True, open_enabled=False):
    endpoint = Endpoint()
    value = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1,
        allow_private_player_inventory_window_close=enabled, allow_private_player_inventory_window_open=open_enabled)
    value.normal_exit_managed_profile = {'normal_exit_source_inventory': {'path': 'AUTHORED_REFERENCE_ONLY'}}
    publish_current(endpoint)
    return value, endpoint


def sources():
    return patch.object(I, 'verify_source_inventory_v1', return_value={'source_inventory_sha256': SOURCE_SHA})


class CloseConsumers(unittest.TestCase):
    def query(self, d):
        return d.query_player_inventory_window_close_private_v1(expected_revision=d.take_snapshot()['revision'])
    def close_inventory(self, d):
        return d.close_player_inventory_window_private_v1(expected_revision=d.take_snapshot()['revision'])
    def post(self, d, sequence=17):
        return d.query_player_inventory_window_close_post_private_v1(expected_revision=d.take_snapshot()['revision'],
            expected_intent_sequence=sequence)
    def test_independent_defaultoff_refuses_all_three_before_source_or_native(self):
        d, endpoint = driver(enabled=False, open_enabled=True); self.addCleanup(d.close)
        with patch.object(I, 'verify_source_inventory_v1', side_effect=AssertionError('forbidden')):
            for call in (self.query, self.close_inventory, self.post):
                with self.assertRaises(UnsupportedStepError): call(d)
        self.assertFalse(any(r.get('type') == 'execute_step' for r in endpoint.requests))
        with self.assertRaises(ValueError): driver(enabled=1)
    def test_actual_six_frame_fields_private_source_and_ack_is_pending(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources(): result = self.close_inventory(d)
        request = next(r for r in endpoint.requests if r.get('type') == 'execute_step')
        self.assertEqual([request[k] for k in ('expected_revision', 'expected_snapshot_revision', 'expected_date_raw',
            'expected_actor_character_id', 'expected_game_pid', 'expected_connection_generation')], [77, 77, 500, 100, 4242, 1])
        self.assertEqual(request['source_inventory_sha256'], SOURCE_SHA)
        self.assertNotIn('request_sequence', request); self.assertNotIn('subject_id', request)
        self.assertFalse(result['desired_window_observed']); self.assertTrue(result['client_replay_blocked'])
    def test_unknown_ack_cannot_be_unlocked_by_latest_historical_sequence_or_post(self):
        d, endpoint = driver(open_enabled=True); self.addCleanup(d.close); endpoint.reject_close = True
        with sources():
            with self.assertRaises(BridgeUnavailableError): self.close_inventory(d)
            endpoint.reject_close = False
            with self.assertRaises(BridgeUnavailableError): self.close_inventory(d)
            with self.assertRaises(BridgeUnavailableError):
                d.open_player_inventory_window_private_v1(expected_revision=d.take_snapshot()['revision'])
            endpoint.mode = 'resolved'; value = self.query(d)
            self.assertEqual(value['intent_sequence'], 17); self.assertTrue(value['client_replay_blocked'])
            self.assertFalse(value['desired_window_observed'])
            with self.assertRaises(BridgeUnavailableError): self.post(d, 18)
            value = self.post(d); self.assertTrue(value['desired_window_observed']); self.assertTrue(value['client_replay_blocked'])
            self.assertIsNone(C._pending(d)[(4242, 100)]['intent_sequence'])
            with self.assertRaises(BridgeUnavailableError): self.close_inventory(d)
        self.assertEqual(sum(r.get('step') == C.CLOSE for r in endpoint.requests), 1)
        self.assertFalse(any(r.get('step') == I.OPEN for r in endpoint.requests))
    def test_open_unknown_blocks_close_atomically_with_same_mutex(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        I._pending(d)[(4242, 100)] = {'intent_sequence': 11}
        with sources(), self.assertRaises(BridgeUnavailableError): self.close_inventory(d)
        self.assertFalse(any(r.get('type') == 'execute_step' for r in endpoint.requests))
    def test_exact_post_hidden_resolves_with_retained_root(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources():
            self.close_inventory(d)
            with self.assertRaises(ValueError): self.post(d, 18)
            endpoint.mode = 'resolved'; result = self.post(d)
        self.assertTrue(result['desired_window_observed']); self.assertTrue(result['after']['root_present'])
        self.assertFalse(result['after']['native_visible']); self.assertFalse(result['after']['effective_visible'])
    def test_post_does_not_require_root_disappearance(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources():
            self.close_inventory(d); endpoint.mode = 'resolved'
            def mutate(packet):
                for name in ('current', 'after'): packet['result'][C.KEY][name]['root_present'] = False
            endpoint.mutate = mutate
            self.assertTrue(self.post(d)['desired_window_observed'])
    def test_pending_notfound_and_historical_resolution_keep_unknown(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources():
            self.close_inventory(d); self.assertTrue(self.post(d)['needs_recovery'])
            endpoint.not_found = True
            with self.assertRaises(BridgeUnavailableError): self.post(d)
            endpoint.not_found = False; endpoint.mode = 'historical'; result = self.post(d)
            self.assertFalse(result['needs_recovery']); self.assertFalse(result['desired_window_observed'])
            self.assertTrue(result['client_replay_blocked'])
            with self.assertRaises(BridgeUnavailableError): self.close_inventory(d)
    def test_new_generation_retains_historical_before_and_unknown(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources():
            self.close_inventory(d); endpoint.generation = 2; publish_current(endpoint)
            endpoint.original.update(native_revision=900, date_raw=510)
            value = self.post(d)
        self.assertEqual(value['before']['connection_generation'], 1)
        self.assertEqual(value['before']['native_revision'], 900); self.assertTrue(value['client_replay_blocked'])
    def test_already_hidden_no_call_does_not_claim_or_resolve(self):
        d, endpoint = driver(); self.addCleanup(d.close); endpoint.mode = 'already_hidden'
        with sources(): result = self.close_inventory(d)
        self.assertFalse(result['once_intent_consumed']); self.assertFalse(result['invoked'])
        self.assertFalse(result['desired_window_observed']); self.assertFalse(result['client_replay_blocked'])
    def test_native_pending_rejection_retains_local_lock(self):
        d, endpoint = driver(); self.addCleanup(d.close); endpoint.mode = 'pending_rejected'
        with sources():
            self.assertTrue(self.close_inventory(d)['client_replay_blocked'])
            with self.assertRaises(BridgeUnavailableError): self.close_inventory(d)
    def test_false_post_proofs_reject_epoch_generation_actor_or_either_visibility(self):
        for field, value in (('capture_epoch', 10), ('connection_generation', 2), ('selected_character_id', 200),
                ('native_visible', True), ('effective_visible', True)):
            d, endpoint = driver()
            try:
                with sources():
                    self.close_inventory(d); endpoint.mode = 'resolved'
                    def mutate(packet, f=field, v=value):
                        for name in ('current', 'after'): packet['result'][C.KEY][name][f] = v
                    endpoint.mutate = mutate
                    with self.assertRaises(BridgeUnavailableError): self.post(d)
                    self.assertIn((4242, 100), C._pending(d))
            finally: d.close()
    def test_false_once_original_hidden_or_query_resolved_or_foreign_schema_reject(self):
        d, endpoint = driver(); self.addCleanup(d.close); snapshot = d.take_snapshot()
        mutations = [lambda r: r['before'].update(native_visible=False),
            lambda r: r.update(desired_window_observed=True), lambda r: r.update(intent_sequence=True),
            lambda r: r.update(schema='ck3_12004_player_inventory_window_v1'),
            lambda r: r.update(actor_aggregate_observed=True), lambda r: r.update(extra_pointer=17)]
        for mutate in mutations:
            value = body('query'); mutate(value)
            with self.assertRaises(ValueError): C.normalize_player_inventory_window_close_v1(value, snapshot=snapshot, operation='query')
    def test_outer_invalid_preserves_history_but_nulls_current(self):
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources():
            self.close_inventory(d)
            def invalidate(packet):
                value = packet['result'][C.KEY]; value.update(available=False, unavailable_reason='actual_owner_changed')
                for name in ('current', 'after'):
                    value[name]['available'] = False; value[name]['selected_character_id'] = None
                    for field in I._STATES: value[name][field] = None
                packet['result']['status'] = 'unavailable'
            endpoint.mutate = invalidate; value = self.post(d)
        self.assertFalse(value['available']); self.assertTrue(value['before']['available'])
        self.assertIsNone(value['current']['native_visible']); self.assertTrue(value['client_replay_blocked'])
    def test_wrong_outer_pid_generation_bool_and_unverified_sources_reject(self):
        mutations = [lambda p: p['result'].update(game_pid=4243), lambda p: p['result'].update(connection_generation=2),
            lambda p: p['result'].update(connection_generation=True),
            lambda p: p['result'][C.KEY].update(loaded_gui_sources_verified=False)]
        for mutate in mutations:
            d, endpoint = driver(); endpoint.mutate = mutate
            try:
                with sources(), self.assertRaises(BridgeUnavailableError): self.query(d)
            finally: d.close()
    def test_old_open_body_stays_25_fields_and_original_status(self):
        d, endpoint = driver(); self.addCleanup(d.close); value = body('query', has_intent=False)
        value['schema'] = 'ck3_12004_player_inventory_window_v1'
        self.assertEqual(len(value), 25)
        self.assertIs(I.normalize_player_inventory_window_v1(value, snapshot=d.take_snapshot(), operation='query'), value)


class PublicCloseConsumers(unittest.IsolatedAsyncioTestCase):
    async def test_actual_registered_service_driver_close_chain_and_independent_flags(self):
        from mcp import Client
        for close_enabled, open_enabled in ((False, False), (False, True), (True, False), (True, True)):
            d, endpoint = driver(enabled=close_enabled, open_enabled=open_enabled)
            try:
                with sources():
                    async with Client(create_server(d)) as client:
                        tools = {t.name: t for t in (await client.session.list_tools()).tools}
                        self.assertEqual(TOOLS & tools.keys(), TOOLS if close_enabled else set())
                        self.assertEqual(OPEN_TOOLS & tools.keys(), OPEN_TOOLS if open_enabled else set())
                        if not close_enabled: continue
                        self.assertFalse(tools['ck3_close_player_inventory_window_v1'].annotations.read_only_hint)
                        self.assertTrue(tools['ck3_query_player_inventory_window_close_post_v1'].annotations.read_only_hint)
                        for tool in ('ck3_query_player_inventory_window_close_v1', 'ck3_close_player_inventory_window_v1'):
                            result = await client.session.call_tool(tool, {'expected_revision': d.take_snapshot()['revision']})
                            self.assertFalse(result.is_error, str(result)); self.assertFalse(result.structured_content['desired_window_observed'])
                        endpoint.mode = 'resolved'
                        result = await client.session.call_tool('ck3_query_player_inventory_window_close_post_v1',
                            {'expected_revision': d.take_snapshot()['revision'], 'expected_intent_sequence': 17})
                        self.assertFalse(result.is_error, str(result)); self.assertTrue(result.structured_content['desired_window_observed'])
            finally: d.close()
    async def test_registered_inputs_forbid_bool_coercion_and_private_injections(self):
        from mcp import Client
        d, endpoint = driver(); self.addCleanup(d.close)
        with sources():
            async with Client(create_server(d)) as client:
                base = {'expected_revision': d.take_snapshot()['revision']}
                for extra in ({'expected_revision': True}, {'subject_id': 100}, {'artifact_id': 5}, {'path': 'other'},
                        {'source_inventory_sha256': SOURCE_SHA}, {'request_sequence': 17}, {'expected_intent_sequence': 17}):
                    result = await client.session.call_tool('ck3_close_player_inventory_window_v1', {**base, **extra})
                    self.assertTrue(result.is_error)
                result = await client.session.call_tool('ck3_query_player_inventory_window_close_post_v1',
                    {**base, 'expected_intent_sequence': True})
                self.assertTrue(result.is_error)
        self.assertFalse(any(r.get('type') == 'execute_step' for r in endpoint.requests))
    async def test_actual_public_builder_maps_only_independent_manifest_optin(self):
        from mcp import Client
        path = ROOT / 'tools/ck3_mod_acceptance_build_runtime.py'
        spec = importlib.util.spec_from_file_location('close_actual_public_builder', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for case, enabled in (({}, False), ({'opt_in_player_inventory_window_open': True}, False),
                ({'opt_in_player_inventory_window_close': True}, True)):
            async with Client(create_server(module.registration_driver(case))) as client:
                names = {tool.name for tool in (await client.session.list_tools()).tools}
                self.assertEqual(TOOLS & names, TOOLS if enabled else set())
        for tool in TOOLS:
            self.assertEqual(module.EXTRA_CAPABILITIES[tool], ['XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1'])
        self.assertEqual(module.REGISTRATION_ACTION_FLAGS['opt_in_player_inventory_window_close'], C.PERMISSION)


class PublicHostConsumers(unittest.TestCase):
    def test_actual_shared_host_parent_child_and_strict_permission_binding(self):
        tree = ast.parse((ROOT / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py').read_text(encoding='utf-8-sig'))
        helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'bind_player_inventory_window_close_permission')
        scope = {}; exec(compile(ast.Module(body=[helper], type_ignores=[]), '<actual-host-helper>', 'exec'), scope)
        for enabled in (False, True):
            d = types.SimpleNamespace(); scope[helper.name](d, enabled); self.assertIs(getattr(d, C.PERMISSION), enabled)
        with self.assertRaises(ValueError): scope[helper.name](types.SimpleNamespace(), 1)
        forward = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and
            '--allow-private-player-inventory-window-close' in ast.unparse(n) and 'child_args.append' in ast.unparse(n) and len(n.body) == 1)
        for enabled in (False, True):
            argv = []; exec(compile(ast.fix_missing_locations(ast.Module(body=[forward], type_ignores=[])), '<actual-parent-child>', 'exec'),
                {'args': types.SimpleNamespace(allow_private_player_inventory_window_close=enabled), 'child_args': argv})
            self.assertEqual(argv, ['--allow-private-player-inventory-window-close'] if enabled else [])
        self.assertFalse(parser().parse_args([]).private_player_inventory_window_close)
    def test_actual_acceptance_requires_explicit_bool_and_complete_three_tools(self):
        tree = ast.parse((ROOT / 'tools/ck3_mod_acceptance.py').read_text(encoding='utf-8-sig'))
        init = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '__init__' and
            any(isinstance(x, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == 'opt_in_player_inventory_window_close' for t in x.targets) for x in n.body))
        start = next(i for i, n in enumerate(init.body) if isinstance(n, ast.Assign) and
            any(isinstance(t, ast.Attribute) and t.attr == 'opt_in_player_inventory_window_close' for t in n.targets))
        validation = compile(ast.fix_missing_locations(ast.Module(body=init.body[start:start+4], type_ignores=[])), '<actual-case-admission>', 'exec')
        for case, valid in (({}, True), ({'opt_in_player_inventory_window_close': True, 'required_mcp_tools': list(TOOLS)}, True),
                ({'opt_in_player_inventory_window_close': 1}, False), ({'required_mcp_tools': list(TOOLS)}, False),
                ({'opt_in_player_inventory_window_close': True, 'required_mcp_tools': [next(iter(TOOLS))]}, False)):
            scope = {'self': types.SimpleNamespace(case=case), 'CASE_PLAYER_INVENTORY_WINDOW_CLOSE_MCP_TOOLS': TOOLS}
            if valid: exec(validation, scope)
            else:
                with self.assertRaises(ValueError): exec(validation, scope)


if __name__ == '__main__':
    unittest.main(verbosity=2)
