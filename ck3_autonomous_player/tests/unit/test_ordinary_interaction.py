"""Synthetic terms/frames and actual production encoder into memory only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import ordinary_interaction_contract as c
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeNamedPipeServer, _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge import native_driver as native_module

KEY = 'ordinary_fixture_interaction'
RECIPIENT = 0x80000002

def source_frame():
    return {'revision': 1, 'native_revision': 7, 'snapshot_id': 'synthetic-ordinary-frame-7',
        'paused': True, 'map_ready': True, 'speed': 3, 'date_raw': 12345,
        'episode_run_id': 'synthetic-ordinary-episode', 'episode_character_id': 7001,
        'local_player_id': 0, 'one_life_terminal_reason': None,
        'played_character': {'character_id': 7001, 'alive': True, 'stress_points': 17},
        'active_event': None, 'pending_character_interaction': None,
        'diagnostics': {'connected': True, 'connection_generation': 2, 'bridge_pid': 991,
            'hello': {'pid': 991, 'ck3_build_match': True, 'game_adapter_id': 'ck3-1.20.0.3-msvc-x64',
                'expected_ck3_version': '1.20.0.3', 'expected_ck3_sha256': c.EXE_SHA256}}}

def context(frame=None, recipient=RECIPIENT, *, available=True):
    binding = c.interaction_binding(frame or source_frame(), (frame or source_frame())['revision'])
    result = {'schema': c.QUERY_SCHEMA, 'status': 'available' if available else 'unavailable',
        'source': 'native_current_ordinary_interaction_context_1.20.0.3', 'read_only': True,
        'exact_build': '1.20.0.3', 'executable_sha256': c.EXE_SHA256.upper(),
        'snapshot_revision': binding['native_revision'], 'date_raw': binding['date_raw'],
        'game_pid': binding['game_pid'], 'connection_generation': binding['connection_generation'],
        'player_character_id': binding['played_character_id'], 'recipient_id': recipient, 'interaction_key': KEY,
        'actor_alive': True, 'recipient_alive': True, 'definition_stable_hash': 4294967295,
        'effective_roles': {key: (7001 if key == 'actor_id' else recipient if key == 'recipient_id' else None) for key in c.ROLES},
        'declared_option_count': 0, 'selected_option_count': 0, 'special_payload_present': False,
        'shown': True, 'can_send': True, 'costs_raw': [0, -100000, 30000, 0, 0, 0, 0, 0, 0, 0],
        'cost_scale': 100000, 'cost_order': c.COST_ORDER, 'auto_accept': True,
        'recipient_score_raw': 1234567890123, 'intermediary_score_raw': -10000, 'outer_answer_status': 2,
        'native_context_available': True, 'ordinary_context_supported': True,
        'active_event_present': binding['active_event_present'], 'incoming_interaction_present': binding['incoming_interaction_present'],
        **{key: available for key in c.PROOFS}, 'owner_thread_id': 345, 'owner_pump_epoch': 678,
        'ready_to_initiate': not binding['active_event_present'] and not binding['incoming_interaction_present'],
        'unavailable_reason': None, 'unsupported_reason': None, 'business_postcondition_verified': False}
    if not available:
        result.update({key: None for key in c.TERM_KEYS})
        result.update(effective_roles={key: None for key in c.ROLES}, owner_thread_id=0, owner_pump_epoch=0,
            native_context_available=False, ordinary_context_supported=False, ready_to_initiate=False,
            unavailable_reason='synthetic_context_unavailable', unsupported_reason='synthetic_context_unavailable')
    return result

def envelope(payload, *, initiating=False):
    return {'step': c.INITIATE_STEP if initiating else c.QUERY_STEP, 'accepted': True,
        'status': payload['status'], 'read_only': not initiating, 'query_sequence': 11,
        **{key: payload[key] for key in c.FRAME_KEYS},
        c.INITIATE_PAYLOAD if initiating else c.QUERY_PAYLOAD: payload, 'backend_id': 'native-headless'}

def native_ack(frame=None, recipient=RECIPIENT, *, queue='submitted', dispatch=True):
    preflight = context(frame, recipient)
    ack = {key: deepcopy(preflight[key]) for key in c.COMMON_KEYS}
    ack.update(schema=c.INITIATE_SCHEMA, status='pending' if dispatch else 'not_dispatched',
        source='native_current_ordinary_interaction_command_1.20.0.3', read_only=False,
        native_call_completed=dispatch, dispatch_invoked=dispatch, native_queue_result=queue,
        queue_submitted=queue == 'submitted', verification_pending=dispatch, postcondition_verified=False,
        reason=None if queue == 'submitted' else 'synthetic_queue_not_submitted', preflight_context=preflight)
    return envelope(ack, initiating=True)

class MemoryDriver:
    query_character_interaction_ordinary_v1 = NativeHeadlessGameplayDriver.query_character_interaction_ordinary_v1
    initiate_character_interaction_ordinary_v1 = NativeHeadlessGameplayDriver.initiate_character_interaction_ordinary_v1
    _execute_primitive_step = NativeHeadlessGameplayDriver._execute_primitive_step
    _verify_idempotent_map_control_postcondition = NativeHeadlessGameplayDriver._verify_idempotent_map_control_postcondition

    def __init__(self, folder):
        self.frame = source_frame()
        self.folder = folder
        self._ordinary_interaction_host_provenance = {'process_create_time':1234567890.5,
            'profile_sha256':'1'*64,'guard_profile_sha256':'2'*64,'session_id':'3'*32,
            'pipe_name':'\\\\.\\pipe\\xar_profile_'+'3'*32}
        self.caps = {c.QUERY_CAPABILITY, c.INITIATE_CAPABILITY}
        self._request_sequence = 0
        self.command_timeout_seconds = .01
        self.packets = []
        self.timeout_send = False
        self.after_send = None
        self.custom_context = None
        self.custom_ack = None
        self.endpoint = SimpleNamespace(send=self.capture_request)
        self.state = SimpleNamespace(wait_for_command_result=self.wait_result)

    def take_snapshot(self):
        return deepcopy(self.frame)

    def capabilities(self):
        return {'bridge_capabilities': sorted(self.caps), 'action_steps': []}

    def _native_driver_state_path(self):
        return self.folder / 'native-session' / 'driver-state.json'

    def capture_request(self, request, *, packet_evidence_path=None):
        fake_pipe = SimpleNamespace(_write_lock=threading.Lock(), _current_handle=lambda: 1)
        def collect(handle, packet):
            self.packets.append(bytes(packet))
            artifact_root = os.environ.get('XAR_ORDINARY_TEST_WIRE')
            if artifact_root:
                root = Path(artifact_root)
                root.mkdir(parents=True, exist_ok=True)
                path = root / (request['request_id'] + '.packet.bin')
                path.write_bytes(packet)
                path.with_suffix('.compact.json').write_bytes(packet[4:])
            return True
        with patch('xar_autoplayer.bridge.native_driver._write_all', side_effect=collect):
            NativeNamedPipeServer.send(fake_pipe, request, packet_evidence_path=packet_evidence_path)

    def wait_result(self, request_id, timeout):
        request = json.loads(self.packets[-1][4:])
        if request['step'] == c.INITIATE_STEP:
            if self.timeout_send:
                return None
            result = self.custom_ack or native_ack(self.frame, request['recipient_id'])
            if self.after_send:
                self.after_send(self.frame)
        else:
            result = envelope(self.custom_context or context(self.frame, request['recipient_id']))
        return {'type': 'command_result', 'request_id': request_id, 'ok': True, 'result': deepcopy(result)}

class ContractTests(unittest.TestCase):
    def binding(self): return c.interaction_binding(source_frame(), 1)

    def test_full_uint32_ids_preserve_generation(self):
        for value in (1, 0x00800002, RECIPIENT, 0xFF000002, 0xFFFFFFFE):
            self.assertEqual(c.validate_recipient_id(value), value)
        for value in (0, -1, 0xFFFFFFFF, 0x100000000, True, 1.0, '2', None):
            with self.subTest(value=value), self.assertRaises(ValueError): c.validate_recipient_id(value)

    def test_keys_reject_unicode_spaces_injection_empty_and_overlength(self):
        for key in ('', 'a b', 'a\n', 'a.b', '中文', 'x' * 129, True, None):
            with self.subTest(key=key), self.assertRaises(ValueError): c.validate_interaction_key(key)
        self.assertEqual(c.validate_interaction_key('ABC_012'), 'ABC_012')

    def test_available_raw_terms_no_formula_or_probability(self):
        raw = envelope(context())
        value = c.project_query(raw, self.binding(), KEY, RECIPIENT)
        self.assertEqual(value[c.QUERY_PAYLOAD]['recipient_score_raw'], 1234567890123)
        self.assertEqual(value['queried_revision'], 1)
        self.assertEqual(value['snapshot_revision'], 7)
        self.assertTrue(value[c.QUERY_PAYLOAD]['auto_accept'])

    def test_unavailable_all_terms_null_not_zero(self):
        raw = envelope(context(available=False))
        self.assertEqual(c.normalize_native_query(raw, self.binding(), KEY, RECIPIENT), raw)
        for key in c.TERM_KEYS:
            bad = deepcopy(raw); bad[c.QUERY_PAYLOAD][key] = 0
            with self.subTest(key=key), self.assertRaises(ValueError): c.normalize_native_query(bad, self.binding(), KEY, RECIPIENT)

    def test_query_can_observe_event_and_incoming_but_not_ready(self):
        for key in ('active_event', 'pending_character_interaction'):
            frame = source_frame(); frame[key] = {'instance_id': 101}
            value = c.project_query(envelope(context(frame)), c.interaction_binding(frame, 1), KEY, RECIPIENT)
            self.assertFalse(value[c.QUERY_PAYLOAD]['ready_to_initiate'])
            with self.assertRaises(ValueError): c.interaction_binding(frame, 1, initiating=True)

    def test_closed_missing_and_extra_fields_rejected(self):
        for scope in ('envelope', 'payload'):
            for extra in (True, False):
                raw = envelope(context()); target = raw if scope == 'envelope' else raw[c.QUERY_PAYLOAD]
                if extra: target['unexpected'] = 1
                else: target.pop('status')
                with self.subTest(scope=scope, extra=extra), self.assertRaises(ValueError):
                    c.normalize_native_query(raw, self.binding(), KEY, RECIPIENT)

    def test_exact_identity_proofs_costs_and_no_business_overcredit(self):
        cases = [('recipient_id', RECIPIENT ^ 0x01000000), ('interaction_key', KEY.upper()),
                 ('player_character_id', 7002), ('snapshot_revision', 1), ('date_raw', 12346),
                 ('connection_generation', 3), ('game_pid', 992), ('owner_thread_id', 0),
                 ('business_postcondition_verified', True), ('cost_scale', 1000),
                 ('costs_raw', [0] * 9), ('costs_raw', [False] * 10)] + [(key, False) for key in c.PROOFS]
        for key, value in cases:
            raw = envelope(context()); raw[c.QUERY_PAYLOAD][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): c.normalize_native_query(raw, self.binding(), KEY, RECIPIENT)

    def test_options_and_special_payload_are_available_unsupported(self):
        for key in ('options', 'payload'):
            value = context()
            if key == 'options': value['declared_option_count'] = 1
            if key == 'payload': value['special_payload_present'] = True
            value.update(ordinary_context_supported=False, ready_to_initiate=False, unsupported_reason='synthetic_unsupported')
            self.assertFalse(c.normalize_context_payload(value, self.binding(), KEY, RECIPIENT)['ready_to_initiate'])

    def test_redirected_actual_two_roles_remain_actual(self):
        value = context(); value['effective_roles']['recipient_id'] = 0xFF000003
        self.assertEqual(c.normalize_context_payload(value, self.binding(), KEY, RECIPIENT)['effective_roles']['recipient_id'], 0xFF000003)

    def test_actual_extra_redirected_roles_remain_native_supported(self):
        # Native compiled positive reader redirects these slots while retaining
        # ordinary support for the two-role input and no option/special payload.
        value=context()
        value['effective_roles']['secondary_actor_id']=0xF1000001
        value['effective_roles']['sixth_role_id']=0x01000001
        result=c.normalize_context_payload(value,self.binding(),KEY,RECIPIENT)
        self.assertTrue(result['ordinary_context_supported'])
        self.assertTrue(result['ready_to_initiate'])
        self.assertEqual(result['effective_roles'],value['effective_roles'])

    def test_ack_queue_submitted_rejected_and_unavailable_stay_pending(self):
        for queue in ('submitted', 'rejected', 'unavailable'):
            raw = native_ack(queue=queue)
            ack = c.normalize_native_initiation(raw, self.binding(), KEY, RECIPIENT)[c.INITIATE_PAYLOAD]
            self.assertEqual(ack['status'], 'pending')
            self.assertTrue(ack['verification_pending'])
            self.assertFalse(ack['postcondition_verified'])
            self.assertFalse(ack['business_postcondition_verified'])

    def test_ack_false_dispatch_not_attempted_only_and_overcredit_rejected(self):
        raw = native_ack(queue='not_attempted', dispatch=False)
        self.assertEqual(c.normalize_native_initiation(raw, self.binding(), KEY, RECIPIENT)['status'], 'not_dispatched')
        for key, value in (('verification_pending', False), ('postcondition_verified', True),
                           ('business_postcondition_verified', True), ('queue_submitted', False), ('status', 'not_dispatched')):
            raw = native_ack(); raw[c.INITIATE_PAYLOAD][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): c.normalize_native_initiation(raw, self.binding(), KEY, RECIPIENT)

class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.driver = MemoryDriver(Path(self.temp.name))
    def tearDown(self): self.temp.cleanup()

    def test_actual_production_query_packet_public_to_native_mapping(self):
        value = self.driver.query_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        packet = self.driver.packets[0]
        self.assertEqual(struct.unpack('<I', packet[:4])[0], len(packet) - 4)
        request = json.loads(packet[4:])
        self.assertEqual(request['expected_revision'], 7)
        self.assertEqual(request['recipient_id'], RECIPIENT)
        self.assertEqual(request['expected_player_character_id'], 7001)
        self.assertNotIn('expected_snapshot_revision', request)
        self.assertEqual(value['queried_revision'], 1)

    def test_actual_send_packet_pending_and_persistent_evidence(self):
        value = self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        self.assertEqual(len(self.driver.packets), 2)
        self.assertEqual(value['status'], 'pending')
        claim = Path(value['action_claim_path'])
        self.assertEqual(claim.with_suffix('.packet.bin').read_bytes(), self.driver.packets[-1])
        self.assertTrue(claim.with_suffix('.native-result.json').is_file())
        self.assertTrue(claim.with_suffix('.receipt.json').is_file())
        self.assertFalse(value['business_effects_verified'])
        self.assertFalse(value['full_product_acceptance_credit'])

    def test_stale_public_revision_bool_and_missing_cap_never_send(self):
        for revision in (7, True, 1.0):
            with self.subTest(revision=revision), self.assertRaises((ValueError, BridgeUnavailableError)):
                self.driver.query_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=revision)
        self.driver.caps.remove(c.INITIATE_CAPABILITY)
        with self.assertRaises(UnsupportedStepError): self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        self.assertEqual(self.driver.packets, [])

    def test_actual_final_refusal_or_unsupported_does_not_claim_or_send(self):
        value = context(); value['can_send'] = False; value['ready_to_initiate'] = False
        self.driver.custom_context = value
        with self.assertRaises(BridgeUnavailableError): self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        self.assertEqual(len(self.driver.packets), 1)
        self.assertFalse(list(self.driver.folder.rglob('*.claim.json')))

    def test_timeout_claim_does_not_unlock_with_new_rev_or_reconnect(self):
        self.driver.timeout_send = True
        with self.assertRaises(BridgeUnavailableError): self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        claim = next(self.driver.folder.rglob('*.claim.json'))
        original = claim.read_bytes()
        self.assertTrue(claim.with_suffix('.unknown.json').is_file())
        for revision, generation in ((2, 2), (3, 3)):
            self.driver.frame.update(revision=revision, native_revision=revision + 7, snapshot_id=f'synthetic-frame-{revision}')
            self.driver.frame['diagnostics']['connection_generation'] = generation
            self.driver.timeout_send = False
            before_count = len(self.driver.packets)
            with self.assertRaises(BridgeUnavailableError): self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=revision)
            self.assertEqual(len(self.driver.packets), before_count + 1)  # readonly preflight only
            self.assertEqual(claim.read_bytes(), original)

    def test_pending_autoaccept_ack_alone_does_not_authorize_another_send(self):
        self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        self.driver.frame.update(revision=2, native_revision=8, snapshot_id='synthetic-next-frame')
        with self.assertRaises(BridgeUnavailableError): self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=2)
        self.assertEqual(sum(json.loads(p[4:])['step'] == c.INITIATE_STEP for p in self.driver.packets), 1)

    def test_legal_event_resources_change_after_send_remains_pending(self):
        def mutate(frame):
            frame.update(revision=2, native_revision=8, snapshot_id='synthetic-after-frame', active_event={'instance_id': 21})
            frame['played_character'].update(stress_points=27, faith_id=900, gold=50)
        self.driver.after_send = mutate
        value = self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        self.assertEqual(value['after_revision'], 2)
        self.assertEqual(value['status'], 'pending')
        self.assertFalse(value['business_effects_verified'])

    def test_after_actor_date_pid_gen_or_pause_drift_is_unknown_no_resend(self):
        for mutation in (lambda f: f.update(date_raw=12346), lambda f: f.update(paused=False),
                lambda f: f['played_character'].update(character_id=7002),
                lambda f: f['diagnostics'].update(connection_generation=3),
                lambda f: f['diagnostics']['hello'].update(pid=992)):
            with tempfile.TemporaryDirectory() as folder:
                driver = MemoryDriver(Path(folder)); driver.after_send = mutation
                with self.assertRaises(BridgeUnavailableError): driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
                self.assertEqual(sum(json.loads(p[4:])['step'] == c.INITIATE_STEP for p in driver.packets), 1)
                self.assertTrue(list(Path(folder).rglob('*.claim.json')))

    def test_generation_different_full_recipient_is_not_silently_reused(self):
        self.driver.initiate_character_interaction_ordinary_v1(KEY, RECIPIENT, expected_revision=1)
        other = RECIPIENT ^ 0x01000000
        value = self.driver.initiate_character_interaction_ordinary_v1(KEY, other, expected_revision=1)
        self.assertEqual(value[c.INITIATE_PAYLOAD]['recipient_id'], other)
        self.assertEqual(len(list(self.driver.folder.rglob('*.claim.json'))), 2)

    def test_primitive_reserved_protocol_alias_or_identity_overrides_rejected(self):
        with self.assertRaises(ValueError): self.driver._execute_primitive_step(c.QUERY_STEP,
            expected_revision=1, required_capability=c.QUERY_CAPABILITY, request_fields={'expected_revision': 99})
        self.assertEqual(self.driver.packets, [])

    def test_service_and_profile_return_pending_never_gameplay_verified(self):
        sys.path.insert(0,str(Path(native_module.__file__).resolve().parents[4]/'tools'))
        import ck3_native_profile_mcp as profile
        service = profile.NativeProfileService.__new__(profile.NativeProfileService)
        service._lock = threading.RLock(); service.profile = {'guard':{'target':{'process_create_time':1234567890.5,'pid':991}},
            'profile_sha256':'1'*64,'guard_profile_sha256':'2'*64}
        service.driver = self.driver; service.session_id = '3'*32; service.pipe_name = '\\\\.\\pipe\\xar_profile_'+'3'*32
        service.backend = SimpleNamespace(poll=lambda _: {})
        service.guard = lambda: {}
        service._snapshot = self.driver.take_snapshot
        service._receipt = lambda operation, payload: {'operation': operation, **payload}
        service._gameplay_service = lambda: GameplayBridgeService(self.driver)
        value = service.initiate_ordinary_interaction(KEY, RECIPIENT, 1)
        self.assertEqual(value['status'], 'native_ordinary_interaction_pending')
        self.assertNotEqual(value['status'], 'native_gameplay_postcondition_verified')
        self.assertFalse(value['business_effects_verified'])

    def test_typed_only_capability_does_not_create_parameterless_planner_action(self):
        self.assertEqual(_action_steps([c.QUERY_CAPABILITY,c.INITIATE_CAPABILITY],paused=True),[])

if __name__ == '__main__': unittest.main()
