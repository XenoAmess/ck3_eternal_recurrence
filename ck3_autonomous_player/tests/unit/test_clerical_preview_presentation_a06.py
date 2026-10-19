"""Focused synthetic transport, actual Driver/Service/registered MCP validation.

No C++ fixture, native callback, CK3 window, or rendered pixel is executed.
"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'src'))
from test_faith_power_presentation_ui_v6 import Driver, raw, normalize, RECEIPT
from xar_autoplayer.bridge.clerical_preview_ui_contract import KEYS, OPTION_KEYS
from xar_autoplayer.bridge.religion_presentation_ui_contract import request_fields

OBSERVATIONS = []
RECIPIENT = 0x80123456


def context(target):
    return {'interaction_key': KEYS[target], 'definition_hash': 187654,
        'actor_id': 29829, 'recipient_id': RECIPIENT, 'effective_actor_id': 29829,
        'interface_kind': 0, 'needs_confirmation': True, 'declared_option_count': 6,
        'selected_option_count': 0, 'roles': [29829, RECIPIENT, None, None, None, 29829],
        'options': [{'key': name, 'flag_id': i+100, 'bank_value': 0, 'selected': False}
                    for i, name in enumerate(OPTION_KEYS)]}


def packet(target, operation='query', phase='default_observed'):
    value = raw('clerical_interaction', operation, RECIPIENT, target=target)
    leaf = value['presentation_ui']
    visible = phase in {'visible_observed', 'close_pending'}
    query = operation == 'query'
    value.update(effective_visible=visible, subject_id_available=visible,
        current_subject_id=RECIPIENT if visible else None, verification_pending=not query)
    value['tree']['widgets'][0]['effective_visible'] = visible
    leaf.update(subject_id=RECIPIENT if visible else None, target_index=None,
        receipt_id=RECEIPT, post_window_visible=visible if query else None,
        source_bound=visible, preview_observed=visible and query,
        hover_source_matches=False, tooltip_stack_observed=False, tooltip_root_visible=False,
        tooltip_active_count=None, tooltip_top_locked=None,
        action_owner_epoch=None if phase == 'default_observed' else 12,
        observation_owner_epoch=14 if query else None)
    sample = context(target)
    leaf['clerical_preview'] = {'available': True, 'root_bound': True,
        'window_visible': visible if query else None, 'phase': phase,
        'default_context': sample,
        'window_context': copy.deepcopy(sample) if query and visible else None,
        'command_submitted': False, 'options_mutated': False, 'business_outcome_observed': False}
    return value


class ClericalPreviewContracts(unittest.TestCase):
    def test_finite_requests_and_actual_context_default_ack_negative_cases(self):
        for target in KEYS:
            self.assertEqual(request_fields('query', 'clerical_interaction', RECIPIENT,
                presentation_target=target), {'presentation_target': target})
        for operation, kind, subject, fields in [
            ('open_clerical_preview', 'clerical_interaction', RECIPIENT, {'presentation_target': 'clerical_puppet'}),
            ('query', 'clerical_interaction', 0, {'presentation_target': 'clerical_puppet'}),
            ('query', 'faith', 50, {'presentation_target': 'clerical_puppet'}),
            ('query', 'clerical_interaction', RECIPIENT, {'presentation_target': 'clerical_puppet', 'presentation_index': 0}),
            ('query', 'clerical_interaction', RECIPIENT, {'presentation_target': 'clerical_puppet', 'presentation_tab': ''}),
            ('query', 'clerical_interaction', RECIPIENT, {'presentation_target': 'make_clerical_puppet_interaction'}),
        ]:
            with self.subTest(operation=operation, kind=kind, fields=fields), self.assertRaises(ValueError):
                request_fields(operation, kind, subject, **fields)
        target = 'clerical_puppet'
        good = packet(target)
        normalize(good, kind='clerical_interaction', subject=RECIPIENT, presentation_target=target)
        for key, bad in [('needs_confirmation', False), ('declared_option_count', 5),
                ('selected_option_count', 1), ('interface_kind', 2), ('recipient_id', RECIPIENT & 0xFFFFFF)]:
            changed = copy.deepcopy(good)
            changed['presentation_ui']['clerical_preview']['default_context'][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize(changed, kind='clerical_interaction', subject=RECIPIENT, presentation_target=target)
        ack = packet(target, 'open_clerical_preview', 'open_pending')
        normalize(ack, operation='open_clerical_preview', kind='clerical_interaction', subject=RECIPIENT,
            presentation_target=target, presentation_receipt=RECEIPT)
        ack['presentation_ui']['clerical_preview']['window_visible'] = True
        with self.assertRaises(ValueError):
            normalize(ack, operation='open_clerical_preview', kind='clerical_interaction', subject=RECIPIENT,
                presentation_target=target, presentation_receipt=RECEIPT)
        for wrong in ('faith', 'holding', 'personal_beliefs'):
            with self.subTest(slot_wrong_window=wrong), self.assertRaises(ValueError):
                request_fields('hover_presentation_tooltip', wrong, 19,
                    presentation_target='rite_core_tenet_slot', presentation_index=0)


class ClericalPreviewMcp(unittest.IsolatedAsyncioTestCase):
    async def test_actual_registered_mcp_two_key_default_open_post_close_hidden(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        for target in KEYS:
            sequence = ['default_observed', 'open_pending', 'visible_observed', 'close_pending', 'hidden_observed']
            def response(fields):
                return packet(target, fields.get('operation', 'query'), sequence.pop(0))
            driver = Driver(response)
            common = {'window_kind': 'clerical_interaction', 'subject_id': RECIPIENT,
                'expected_revision': 4, 'presentation_target': target}
            steps = [
                ('ck3_query_faith_power_ui_v1', common),
                ('ck3_present_faith_power_ui_v1', {**common, 'operation': 'open_clerical_preview', 'presentation_receipt': RECEIPT}),
                ('ck3_query_faith_power_ui_v1', {**common, 'presentation_receipt': RECEIPT}),
                ('ck3_present_faith_power_ui_v1', {**common, 'operation': 'close_clerical_preview', 'presentation_receipt': RECEIPT}),
                ('ck3_query_faith_power_ui_v1', {**common, 'presentation_receipt': RECEIPT}),
            ]
            async with Client(create_server(driver)) as client:
                for tool, args in steps:
                    result = await client.call_tool(tool, args)
                    self.assertFalse(result.is_error, result)
                    value = result.structured_content
                    leaf = value['presentation_ui']
                    OBSERVATIONS.append({'tool': tool, 'arguments': args,
                        'phase': leaf['clerical_preview']['phase'], 'post_window_visible': leaf['post_window_visible'],
                        'primitive': driver.calls[-1][0], 'actual_transport_synthetic': True, 'native_executed': False})
                self.assertEqual(len(driver.calls), 5)
                self.assertFalse(value['effective_visible'])
                count = len(driver.calls)
                bad = await client.call_tool('ck3_present_faith_power_ui_v1',
                    {**common, 'operation': 'open_clerical_preview', 'presentation_receipt': RECEIPT, 'callback': 'Send'})
                self.assertTrue(bad.is_error)
                self.assertEqual(len(driver.calls), count)

    async def test_actual_registered_mcp_visible_core_slot_hover_and_later_read(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        def response(fields):
            return raw('rite_creation', fields.get('operation', 'query'), 0,
                target=fields['presentation_target'], index=fields['presentation_index'],
                receipt=fields.get('presentation_receipt'))
        driver = Driver(response)
        common = {'window_kind': 'rite_creation', 'subject_id': 0, 'expected_revision': 4,
            'presentation_target': 'rite_core_tenet_slot', 'presentation_index': 0}
        async with Client(create_server(driver)) as client:
            for tool, args in [
                ('ck3_present_faith_power_ui_v1', {**common, 'operation': 'hover_presentation_tooltip'}),
                ('ck3_query_faith_power_tooltip_v1', {**common, 'presentation_receipt': RECEIPT}),
            ]:
                result = await client.call_tool(tool, args)
                self.assertFalse(result.is_error, result)
                self.assertEqual(driver.calls[-1][1]['request_fields']['presentation_target'], 'rite_core_tenet_slot')
                OBSERVATIONS.append({'tool': tool, 'arguments': args, 'primitive': driver.calls[-1][0],
                    'actual_transport_synthetic': True, 'native_executed': False, 'rendered_pixels_observed': False})
            count = len(driver.calls)
            bad = await client.call_tool('ck3_present_faith_power_ui_v1',
                {**common, 'operation': 'hover_presentation_tooltip', 'window_kind': 'faith'})
            self.assertTrue(bad.is_error)
            self.assertEqual(len(driver.calls), count)

if __name__ == '__main__':
    unittest.main()
