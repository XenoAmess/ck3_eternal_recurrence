import json
import unittest
from xar_autoplayer.bridge.normal_exit_contract_v1 import (
    ExitWireBinding, encode_normal_exit_map_request, normalize_query_arguments,
    normalize_request_arguments, MAP_EXIT_ACTIONS,
)


class ContractTests(unittest.TestCase):
    def binding(self): return ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)
    def encode(self, action='query_context', **kwargs):
        return encode_normal_exit_map_request(request_id='req-1', action=action,
                                             binding=self.binding(), request_nonce='nonce-1', **kwargs)

    def test_query_requires_positive_exact_revision_and_closed_keys(self):
        self.assertEqual(normalize_query_arguments({'expected_revision': 72}), {'expected_revision': 72})
        for arguments in [{'expected_revision': value} for value in [0, -1, True, 72.0]] + [
                {'expected_revision': 72, 'skip_save': True}, {}]:
            with self.assertRaises(ValueError): normalize_query_arguments(arguments)

    def test_request_closed_map_actions_and_signature(self):
        for action in MAP_EXIT_ACTIONS:
            result = normalize_request_arguments({'action': action, 'expected_revision': 72,
                                                  'expected_exit_context_signature': 'a' * 64})
            self.assertEqual(result['action'], action)
        for action in ['frontend_quit', 'query_context', 'terminate', True]:
            with self.assertRaises(ValueError): normalize_request_arguments({
                'action': action, 'expected_revision': 72, 'expected_exit_context_signature': 'a' * 64})
        with self.assertRaises(ValueError): normalize_request_arguments({
            'action': 'confirm_desktop', 'expected_revision': 72,
            'expected_exit_context_signature': 'a' * 64, 'widget_path': 'caller'})

    def test_signature_rejects_nonhex_uppercase_wronglength(self):
        for signature in ['G' * 64, 'A' * 64, 'a' * 63, None, True]:
            with self.assertRaises(ValueError): self.encode('confirm_desktop',
                                                          expected_exit_context_signature=signature)

    def test_actual_encoder_preserves_exact_uint64_filetime(self):
        packet = self.encode()
        decoded = json.loads(packet)
        self.assertEqual(decoded['expected_process_creation_filetime_100ns'], 133000000000000043)
        self.assertIs(type(decoded['expected_process_creation_filetime_100ns']), int)
        self.assertEqual(decoded['step'], 'normal-exit-map-v1')
        self.assertFalse(packet.endswith(b'\n'))
        self.assertNotIn('expected_exit_context_signature', decoded)

    def test_query_signature_rejected_mutation_required(self):
        with self.assertRaises(ValueError): self.encode(expected_exit_context_signature='a' * 64)
        with self.assertRaises(ValueError): self.encode('confirm_desktop')
        self.assertEqual(json.loads(self.encode('prepare_confirmation',
                                               expected_exit_context_signature='a' * 64))['action'],
                         'prepare_confirmation')

    def test_binding_rejects_booleans_float_frontend_and_missing_process(self):
        for revision in [0, True, 72.0]:
            with self.assertRaises(ValueError): ExitWireBinding(revision, 9301, 43, 8, 133000000000000043, 'b' * 64)
        for creation in [0, True, 133000000000000043.0]:
            with self.assertRaises(ValueError): ExitWireBinding(72, 9301, 43, 8, creation, 'b' * 64)


if __name__ == '__main__': unittest.main()
