"""Focused offline C3 provider tests; native DTOs grant no game acceptance."""
from __future__ import annotations
import asyncio, copy, inspect, json, os, struct, sys, threading, types, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_confucian_readonly_private_v1 as base
from xar_autoplayer.bridge import confucian_challenger_graph_v1 as graph
from xar_autoplayer.bridge import confucian_readonly_private_v1 as query
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from pydantic import ValidationError

FAITHS = [0, 0xAB000003]
T = 0x81000001


def title(identity=T, *, faith=0, absent=False):
    leaf = {'available': not absent, 'unavailable_reason': 'native_title_absent' if absent else None}
    return {'available': True, 'unavailable_reason': None, 'title_absent': absent,
        'title_full_id': None if absent else identity, 'native_title_class': None if absent else 'CLandedTitle',
        'holder_absent': None if absent else False, 'holder_character_full_id': None if absent else 0x82000002,
        'holder_current_faith_full_id': None if absent else faith,
        'title_properties': {**leaf, **{key: None if absent else True for key in graph.PROPERTY_FIELDS}},
        'title_laws': {**leaf, 'native_count': None if absent else 1,
            'complete_laws': None if absent else [{'native_definition_id': 27, 'key': graph.LAW}],
            'expected_law_key': graph.LAW, 'expected_law_member': None if absent else True}}


def payload(binding):
    relation = {'challenger_title_full_id': T, 'available': True, 'unavailable_reason': None,
        'challenger_title': title(), 'registered_sponsor_title': title(),
        'scope_sponsor_available': True, 'scope_lookup_complete': True,
        'scope_sponsor_unavailable_reason': None, 'scope_lookup_faith_full_id': 0,
        'scope_lookup_native_count': 1, 'scope_lookup_faith_matches_collection': True,
        'scope_matches_registered_pair': True, 'scope_sponsor_title': title()}
    return {'schema': graph.SCHEMA, 'game_version': '1.20.0.3',
        'executable_sha256': query.CK3_12003.executable_sha256, 'read_only': True,
        'available': True, 'graph_complete': True, 'unavailable_reason': None,
        'capture_epoch': 44, 'date_raw': binding['date_raw'],
        'played_character_id': binding['played_character_id'],
        'played_character_full_id': binding['played_character_id'] & 0xFFFFFFFF,
        'requested_faith_full_ids': FAITHS.copy(), 'faiths': [
            {'requested_faith_full_id': 0, 'available': True, 'collection_complete': True,
                'unavailable_reason': None, 'native_count': 1,
                'complete_native_challenger_title_ids': [T], 'challengers': [relation]},
            {'requested_faith_full_id': FAITHS[1], 'available': True, 'collection_complete': True,
                'unavailable_reason': None, 'native_count': 0,
                'complete_native_challenger_title_ids': [], 'challengers': []}],
        'mod_owned_markers': None, 'saved_owner_faith_variables': None,
        'qualification': copy.deepcopy(graph.QUALIFICATION)}


def envelope(binding, value=None):
    return base.envelope('challenger_graph', binding, value or payload(binding))


def driver(*, after=None, response=None):
    d = base.inert_driver('religious_title', after=after, response=response)
    d.allow_private_confucian_challenger_queries = True
    binding = query.query_binding(base.frame(), 3)
    if response is None:
        d.state.wait_for_command_result = lambda request, timeout: {
            'type': 'command_result', 'protocol_version': 1, 'request_id': request,
            'ok': True, 'result': envelope(binding)}
    return d


class GraphContractTests(unittest.TestCase):
    def setUp(self): self.binding = query.query_binding(base.frame(), 3)

    def test_strict_selectors_zero_high_generations_and_bounds(self):
        self.assertEqual(graph.validate_faith_ids([0, 2**32-2]), [0, 2**32-2])
        for invalid in (None, (), [], [True], [1.0], ['0'], [-1], [2**32-1], [0, 0], list(range(9))):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                graph.validate_faith_ids(invalid)

    def test_self_sponsor_known_empty_and_absent_scope_preserved(self):
        value = payload(self.binding)
        self.assertEqual(graph.normalize_graph(value, self.binding, FAITHS), value)
        row = value['faiths'][0]['challengers'][0]
        row['challenger_title']['holder_current_faith_full_id'] = FAITHS[1]
        row['registered_sponsor_title']['holder_current_faith_full_id'] = FAITHS[1]
        row.update(scope_lookup_faith_full_id=FAITHS[1], scope_lookup_native_count=0,
            scope_lookup_faith_matches_collection=False, scope_matches_registered_pair=False,
            scope_sponsor_title=title(absent=True))
        actual = graph.normalize_graph(value, self.binding, FAITHS)
        self.assertEqual(actual['faiths'][0]['challengers'][0]['registered_sponsor_title']['title_full_id'], T)
        self.assertIsNone(actual['faiths'][0]['challengers'][0]['scope_sponsor_title']['title_full_id'])

    def test_unknown_collection_stays_null_and_cannot_claim_business(self):
        value = payload(self.binding)
        value.update(available=False, graph_complete=False, faiths=None, unavailable_reason='native_copy_failed')
        result = graph.project_native_graph_query(envelope(self.binding, value), self.binding, FAITHS)
        self.assertFalse(result['business_postcondition_verified'])
        self.assertFalse(result['full_product_acceptance_credit'])
        value['faiths'] = []
        with self.assertRaises(ValueError): graph.normalize_graph(value, self.binding, FAITHS)

    def test_partial_count_duplicate_row_and_wrong_leaf_refused(self):
        mutations = [lambda v: v['faiths'].pop(), lambda v: v['faiths'][0].update(native_count=0),
            lambda v: v['faiths'][0].update(collection_complete=False),
            lambda v: v['faiths'][0]['complete_native_challenger_title_ids'].append(T),
            lambda v: v['faiths'][0]['challengers'][0].update(challenger_title_full_id=0),
            lambda v: v['faiths'][0]['challengers'][0]['challenger_title']['title_properties'].update(definitive_form=None),
            lambda v: v['faiths'][0]['challengers'][0]['challenger_title']['title_laws'].update(native_count=2),
            lambda v: v['faiths'][0]['challengers'][0]['challenger_title']['title_laws'].update(expected_law_member=False),
            lambda v: v.update(mod_owned_markers=True), lambda v: v.update(saved_owner_faith_variables=0),
            lambda v: v['qualification'].update(runtime_acceptance=True),
            lambda v: v.update(requested_faith_full_ids=[0, 3]),
            lambda v: v.update(played_character_full_id=True)]
        for mutate in mutations:
            value = payload(self.binding); mutate(value)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                graph.normalize_graph(value, self.binding, FAITHS)

    def test_scope_uses_challenger_holder_current_faith(self):
        for mutate in (lambda r: r.update(scope_lookup_faith_full_id=FAITHS[1]),
                       lambda r: r.update(scope_lookup_faith_matches_collection=False),
                       lambda r: r.update(scope_matches_registered_pair=False),
                       lambda r: r.update(scope_lookup_native_count=0),
                       lambda r: r.update(scope_sponsor_title=title(absent=True))):
            value = payload(self.binding); mutate(value['faiths'][0]['challengers'][0])
            with self.assertRaises(ValueError): graph.normalize_graph(value, self.binding, FAITHS)

    def test_real_driver_production_wire_and_canonical_native_revision(self):
        d = driver(); result = d.query_confucian_challenger_graph_v1(FAITHS, expected_revision=3)
        self.assertEqual(result['queried_native_revision'], 7)
        packet = d.endpoint.packets[0]
        self.assertEqual(struct.unpack('<I', packet[:4])[0], len(packet)-4)
        data = json.loads(packet[4:])
        self.assertEqual(set(data), {'type', 'protocol_version', 'request_id', 'step',
            'expected_snapshot_revision', 'faith_full_ids'})
        self.assertEqual(data['faith_full_ids'], FAITHS)
        self.assertEqual(data['expected_snapshot_revision'], 7)
        self.assertNotIn('expected_revision', data)
        # Caller-owned selector mutation after send cannot reinterpret the capture.
        mutable_selector = FAITHS.copy()
        d = driver(); original_wait = d.state.wait_for_command_result
        def mutate_caller_selector(request, timeout):
            mutable_selector[:] = [99]
            return original_wait(request, timeout)
        d.state.wait_for_command_result = mutate_caller_selector
        stable = d.query_confucian_challenger_graph_v1(mutable_selector, expected_revision=3)
        self.assertEqual(mutable_selector, [99])
        self.assertEqual(stable['native_result']['confucian_challenger_graph']['requested_faith_full_ids'], FAITHS)
        self.assertEqual(json.loads(d.endpoint.packets[0][4:])['faith_full_ids'], FAITHS)
        # A backend result that changes the actual graph selection must fail.
        d = driver(); original_wait = d.state.wait_for_command_result
        def mutate_native_selection(request, timeout):
            native = original_wait(request, timeout)
            native['result']['confucian_challenger_graph']['requested_faith_full_ids'] = [99]
            return native
        d.state.wait_for_command_result = mutate_native_selection
        with self.assertRaises(BridgeUnavailableError):
            d.query_confucian_challenger_graph_v1(FAITHS, expected_revision=3)
        if os.environ.get('XAR_C3_PACKET_OUTPUT'):
            Path(os.environ['XAR_C3_PACKET_OUTPUT']).write_bytes(packet[4:])

    def test_default_off_bad_selector_stale_and_crossed_owner_send_boundary(self):
        d = driver(); d.allow_private_confucian_challenger_queries = False
        with self.assertRaises(UnsupportedStepError): d.query_confucian_challenger_graph_v1(FAITHS, expected_revision=3)
        self.assertFalse(d.endpoint.packets)
        self.assertIs(inspect.signature(base.native_driver.NativeHeadlessGameplayDriver).parameters[
            'allow_private_confucian_challenger_queries'].default, False)
        for selector, revision, error in (([0, 0], 3, ValueError), (FAITHS, 4, BridgeUnavailableError)):
            d = driver()
            with self.assertRaises(error): d.query_confucian_challenger_graph_v1(selector, expected_revision=revision)
            self.assertFalse(d.endpoint.packets)
        for change in (lambda f: f['diagnostics']['hello'].update(pid=992),
                       lambda f: f.update(native_revision=8), lambda f: f.update(date_raw=53144713)):
            after = base.frame(); change(after); d = driver(after=after)
            with self.assertRaises(BridgeUnavailableError): d.query_confucian_challenger_graph_v1(FAITHS, expected_revision=3)
            self.assertEqual(len(d.endpoint.packets), 1)

    def test_service_profile_permission_restore_and_disabled23(self):
        d = driver(); d.take_snapshot = base.frame
        gameplay = object.__new__(base.GameplayBridgeService); gameplay.driver = d
        profile = base.load_profile_module(); owner = object.__new__(profile.NativeProfileService)
        owner.driver = d; owner._lock = threading.RLock()
        owner._bound_frame = lambda revision, paused=False: base.frame()
        owner._gameplay_service = lambda: gameplay
        owner._receipt = lambda operation, value: {'operation': operation, **value}
        owner._confucian_readonly_tools_enabled_v1 = True
        with self.assertRaises(RuntimeError): owner.query_confucian_readonly('challenger_graph', 3, FAITHS)
        owner._confucian_challenger_tools_enabled_v1 = True
        d.allow_private_confucian_challenger_queries = False
        d.allow_private_confucian_readonly_queries = False
        result = owner.query_confucian_readonly('challenger_graph', 3, FAITHS)
        self.assertFalse(result['business_effects_verified'])
        self.assertFalse(d.allow_private_confucian_challenger_queries)
        self.assertFalse(d.allow_private_confucian_readonly_queries)

    def test_actual_sdk21_23_24_preserves_all_earlier_tool_metadata(self):
        module = base.load_profile_module()
        def tools(**flags):
            server = module.create_server(types.SimpleNamespace(), **flags)
            metadata = {tool.name: tool.model_dump(mode='json', by_alias=True, exclude_none=True)
                        for tool in asyncio.run(server.list_tools())}
            return server, metadata
        _, before = tools(); _, old = tools(confucian_readonly_tools=True)
        server, new = tools(confucian_challenger_tools=True)
        self.assertEqual((len(before), len(old), len(new)), (21, 23, 24))
        self.assertEqual({name: new[name] for name in old}, old)
        self.assertEqual({name: old[name] for name in before}, before)
        name = 'ck3_query_profile_confucian_challenger_graph_v1'
        self.assertEqual(set(new)-set(old), {name})
        schema = new[name]['inputSchema']
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(set(schema['required']), {'expected_revision', 'faith_full_ids'})
        self.assertEqual(schema['properties']['faith_full_ids']['maxItems'], 8)
        self.assertTrue(schema['properties']['faith_full_ids']['uniqueItems'])
        model = server._tool_manager._tools[name].fn_metadata.arg_model
        for invalid in ({}, {'expected_revision': True, 'faith_full_ids': FAITHS},
            {'expected_revision': 3, 'faith_full_ids': [True]},
            {'expected_revision': 3, 'faith_full_ids': [0, 0]},
            {'expected_revision': 3, 'faith_full_ids': [2**32-1]},
            {'expected_revision': 3, 'faith_full_ids': list(range(9))},
            {'expected_revision': 3, 'faith_full_ids': FAITHS, 'title_id': T}):
            with self.assertRaises(ValidationError): model.model_validate(invalid)
        self.assertEqual(model.model_validate({'expected_revision': 3, 'faith_full_ids': FAITHS}).faith_full_ids, FAITHS)
        for invalid in (1, None, 'true'):
            with self.assertRaises(ValueError): module.create_server(types.SimpleNamespace(), confucian_challenger_tools=invalid)

    @unittest.skipUnless(os.environ.get('XAR_C3_NATIVE_FIXTURES'), 'requires actual focused native fixture output')
    def test_actual_native_serializer_interchange(self):
        folder = Path(os.environ['XAR_C3_NATIVE_FIXTURES'])
        f = base.frame(); f.update(date_raw=720123)
        f['played_character']['character_id'] = 0x81000000
        binding = query.query_binding(f, 3)
        for name in ('complete-self-sponsor.json', 'old-owner-scope-mismatch.json'):
            value = json.loads((folder/name).read_bytes())
            result = graph.project_native_graph_query(envelope(binding, value), binding, FAITHS)
            self.assertEqual(result['native_result']['confucian_challenger_graph'], value)
            self.assertFalse(result['business_postcondition_verified'])


if __name__ == '__main__': unittest.main()
