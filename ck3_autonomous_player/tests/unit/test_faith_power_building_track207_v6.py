"""Only new op207 and optional owned-tracks contract; no native/game fixture."""
import copy
import unittest
from test_faith_power_presentation_ui_v6 import Driver, raw, normalize
from xar_autoplayer.bridge.ingame_ui_contract import validate_ui_request

MCP_OBSERVATIONS = []
FIELDS = {'presentation_target': 'holding_building', 'presentation_index': 0}


def result(operation='open_building_track'):
    return raw('holding', operation, 1503, target='holding_building' if operation != 'query' else None,
        index=0 if operation != 'query' else None)


def tracks():
    return {'available': True, 'unavailable_reason': None, 'owner_bound': True,
        'window_exists': True, 'root_exists': True, 'effective_visible': True,
        'selection_category_id': 0, 'selection_mode': None, 'selection_action_raw': None,
        'selected_building_key': None}


class BuildingTrack207(unittest.TestCase):
    def test_new_operation_uses_only_original_installed_row_and_finite_budget(self):
        for index in (0, 127):
            validate_ui_request('open_building_track', 'holding', 1503, 4,
                presentation_target='holding_building', presentation_index=index)
        for fields in ({'presentation_target': 'holding_building_preview', 'presentation_index': 0},
                {**FIELDS, 'presentation_index': 128}, {**FIELDS, 'presentation_tab': 'beliefs'},
                {**FIELDS, 'presentation_receipt': '1' * 32}, {'presentation_index': 0}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                validate_ui_request('open_building_track', 'holding', 1503, 4, **fields)
        with self.assertRaises(ValueError):
            validate_ui_request('open_building_track', 'faith', 50, 4, **FIELDS)
        # One existing finite literal remains admitted; no old test matrix rerun.
        validate_ui_request('select_presentation_tab', 'faith', 0, 4, presentation_tab='beliefs')

    def test_ack_requires_actual_current_source_and_installed_row_identity(self):
        ack = normalize(result(), operation='open_building_track', kind='holding', subject=1503, **FIELDS)
        self.assertTrue(ack['verification_pending'])
        for mutation in (lambda x: x.update(source_bound=False), lambda x: x.update(target_index=1),
                lambda x: x.update(target_kind='holding_building_preview'), lambda x: x.update(subject_id=1504)):
            value = result(); mutation(value['presentation_ui'])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                normalize(value, operation='open_building_track', kind='holding', subject=1503, **FIELDS)

    def test_driver_reuses_normal_single_navigation_and_preserves_unknown_attempt(self):
        driver = Driver(result())
        driver.present_faith_power_ui_v1('open_building_track', 'holding', 1503, expected_revision=4, **FIELDS)
        self.assertEqual(len(driver.calls), 1)
        self.assertEqual(driver.calls[0][0], 'navigate-ingame-ui-v1')
        self.assertEqual(driver.calls[0][1]['request_fields']['operation'], 'open_building_track')
        value = result()
        value.update(available=False, accepted=False, status='unavailable', dispatch_invoked=False,
            native_dispatch_attempted=True, verification_pending=False, unavailable_reason='original_toggle_fault_do_not_retry')
        value['presentation_ui'].update(available=False, status='unavailable', unavailable_reason=value['unavailable_reason'])
        driver = Driver(value)
        returned = driver.present_faith_power_ui_v1('open_building_track', 'holding', 1503, expected_revision=4, **FIELDS)
        self.assertFalse(returned['available']); self.assertTrue(returned['native_dispatch_attempted'])
        self.assertEqual(len(driver.calls), 1)

    def test_optional_tracks_absence_remains_unknown_and_owned_visibility_is_independent(self):
        for observed in ('absent', None, tracks()):
            value = result('query')
            if observed != 'absent': value['presentation_ui']['holding_tracks'] = observed
            returned = normalize(value, kind='holding', subject=1503, presentation_tab='')
            self.assertEqual(returned['presentation_ui'].get('holding_tracks'), None if observed == 'absent' else observed)
        mutations = [lambda x: x.update(owner_bound=False), lambda x: x.update(window_exists=False),
            lambda x: x.update(root_exists=None), lambda x: x.update(selection_category_id=True),
            lambda x: x.update(selected_building_key=17), lambda x: x.update(available=False),
            lambda x: x.update(foreign_pointer=1)]
        for mutate in mutations:
            value = result('query'); value['presentation_ui']['holding_tracks'] = tracks()
            mutate(value['presentation_ui']['holding_tracks'])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                normalize(value, kind='holding', subject=1503, presentation_tab='')
        value = result('query'); value['presentation_ui']['holding_tracks'] = tracks()
        value['presentation_ui']['source_bound'] = False
        with self.assertRaises(ValueError): normalize(value, kind='holding', subject=1503, presentation_tab='')


class BuildingTrack207Mcp(unittest.IsolatedAsyncioTestCase):
    async def test_registered_enum_and_independent_track_observation(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        def response(fields):
            value = result(fields.get('operation', 'query'))
            if fields.get('operation', 'query') == 'query': value['presentation_ui']['holding_tracks'] = tracks()
            return value
        driver = Driver(response)
        async with Client(create_server(driver)) as client:
            tools = await client.list_tools()
            tool = next(t for t in tools.tools if t.name == 'ck3_present_faith_power_ui_v1')
            self.assertIn('open_building_track', tool.input_schema['properties']['operation']['enum'])
            for tool_name, arguments in [
                ('ck3_present_faith_power_ui_v1', {'operation': 'open_building_track', 'window_kind': 'holding',
                    'subject_id': 1503, 'expected_revision': 4, **FIELDS}),
                ('ck3_query_faith_power_ui_v1', {'window_kind': 'holding', 'subject_id': 1503, 'expected_revision': 4})]:
                packet = await client.call_tool(tool_name, arguments)
                self.assertFalse(packet.is_error)
                MCP_OBSERVATIONS.append({'tool': tool_name, 'arguments': arguments,
                    'structured_content': packet.structured_content, 'snapshot_transport_synthetic': True,
                    'native_cpp_executed': False})
            self.assertTrue(packet.structured_content['presentation_ui']['holding_tracks']['effective_visible'])
            count = len(driver.calls)
            bad = await client.call_tool('ck3_present_faith_power_ui_v1', {'operation': 'open_building_track',
                'window_kind': 'holding', 'subject_id': 1503, 'expected_revision': 4,
                'presentation_target': 'holding_building_preview', 'presentation_index': 0})
            self.assertTrue(bad.is_error); self.assertEqual(len(driver.calls), count)
