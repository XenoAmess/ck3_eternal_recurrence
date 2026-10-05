"""Replay an actual pending receipt offline; no new command or claim is made."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import threading
import unittest

from xar_autoplayer.bridge import ordinary_interaction_contract as c
from xar_autoplayer.bridge.service import GameplayBridgeService

FIXTURE = Path(__file__).parent / 'fixtures/ordinary_interaction_after_observation_r8.json'


class AfterObservationTests(unittest.TestCase):
    def setUp(self):
        data = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.before = data['before_frame']
        self.after = data['later_frame']
        self.binding = data['original_claim_binding']
        self.native = data['native_result']['result']
        self.receipt = data['driver_receipt']['result']
        self.key = self.native[c.INITIATE_PAYLOAD]['interaction_key']
        self.recipient = self.native[c.INITIATE_PAYLOAD]['recipient_id']
        self.calls = 0

    def later(self, frame=None):
        return c.after_control_binding(self.before, frame or self.after, self.binding)

    def service(self, after=None, result=None):
        owner = self
        class CapturedReceiptBackend:
            def take_snapshot(self):
                return deepcopy(owner.before if owner.calls == 0 else after or owner.after)
            def initiate_character_interaction_ordinary_v1(self, *args, **kwargs):
                # Return the immutable recorded receipt. This is not a send.
                owner.calls += 1
                return deepcopy(result or owner.receipt)
        return GameplayBridgeService(CapturedReceiptBackend())

    def test_actual_native_ack_and_driver_after_are_preserved_at_later_wrapper_frame(self):
        self.assertEqual(c.normalize_native_initiation(self.native, self.binding, self.key, self.recipient), self.native)
        result = c.normalize_public_initiation(self.receipt, self.binding, self.key, self.recipient, self.later())
        self.assertEqual(result, self.receipt)
        self.assertEqual((result['after_revision'], result['after_native_revision'], result['after_snapshot_id']), (3, 2, 'native:2'))
        self.assertEqual((self.after['revision'], self.after['native_revision']), (4, 3))
        self.assertEqual(result['status'], 'pending')
        self.assertFalse(result['business_effects_verified'])
        self.assertFalse(result['full_product_acceptance_credit'])

    def test_actual_service_method_does_not_reject_forward_state_publication(self):
        result = self.service().initiate_character_interaction_ordinary_v1(self.key, self.recipient, expected_revision=3)
        self.assertEqual(self.calls, 1)
        self.assertEqual(result, self.receipt)

    def test_actual_profile_method_accepts_an_additional_later_observation(self):
        import ck3_native_profile_mcp as profile
        instance = profile.NativeProfileService.__new__(profile.NativeProfileService)
        instance._lock = threading.RLock()
        instance.driver = SimpleNamespace()
        instance.profile = {'guard': {'target': {'pid': self.binding['game_pid'], 'process_create_time': 1791173103.5222309}},
            'profile_sha256': '1' * 64, 'guard_profile_sha256': '2' * 64}
        instance.session_id = '3' * 32
        instance.pipe_name = '\\\\.\\pipe\\xar_profile_' + instance.session_id
        instance.backend = SimpleNamespace(poll=lambda _: {})
        instance.guard = lambda: {}
        instance._bound_frame = lambda *args, **kwargs: deepcopy(self.before)
        instance._snapshot = lambda: deepcopy(self.after)
        instance._gameplay_service = lambda: self.service()
        instance._receipt = lambda action, value: {'action': action, **value}
        result = instance.initiate_ordinary_interaction(self.key, self.recipient, 3)
        self.assertEqual(self.calls, 1)
        self.assertEqual(result['status'], 'native_ordinary_interaction_pending')
        self.assertEqual(result['result'], self.receipt)
        self.assertFalse(result['business_effects_verified'])

    def test_backwards_future_bool_float_and_snapshot_mismatch_are_rejected(self):
        mutations = [('after_revision', 2), ('after_revision', 5), ('after_revision', True), ('after_revision', 3.0),
            ('after_native_revision', 1), ('after_native_revision', 4), ('after_native_revision', False),
            ('after_native_revision', 2.0), ('after_snapshot_id', 'native:3'), ('after_snapshot_id', None),
            ('after_control_frame_verified', False), ('business_effects_verified', True), ('full_product_acceptance_credit', True)]
        for field, value in mutations:
            raw = deepcopy(self.receipt); raw[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                c.normalize_public_initiation(raw, self.binding, self.key, self.recipient, self.later())

    def test_same_public_revision_cannot_name_a_different_native_frame(self):
        raw = deepcopy(self.receipt); raw['after_native_revision'] = 3; raw['after_snapshot_id'] = 'native:3'
        with self.assertRaises(ValueError):
            c.normalize_public_initiation(raw, self.binding, self.key, self.recipient, self.later())
        raw = deepcopy(self.receipt); raw['after_revision'] = 4
        with self.assertRaises(ValueError):
            c.normalize_public_initiation(raw, self.binding, self.key, self.recipient, self.later())

    def test_mid_interval_native_identity_is_checked_without_claiming_business(self):
        # A synthetic later publication after the actual captured native:3.
        after = deepcopy(self.after); after.update(revision=5, native_revision=4, snapshot_id='native:4')
        raw = deepcopy(self.receipt); raw.update(after_revision=4, after_native_revision=3, after_snapshot_id='native:3')
        result = c.normalize_public_initiation(raw, self.binding, self.key, self.recipient, self.later(after))
        self.assertEqual(result, raw)
        raw['after_snapshot_id'] = 'native:4'
        with self.assertRaises(ValueError):
            c.normalize_public_initiation(raw, self.binding, self.key, self.recipient, self.later(after))

    def test_later_control_drift_still_fails_without_another_backend_call(self):
        changes = [lambda f: f.update(date_raw=f['date_raw'] + 1), lambda f: f.update(paused=False),
            lambda f: f.update(speed=3), lambda f: f.update(map_ready=False),
            lambda f: f['played_character'].update(character_id=31255),
            lambda f: f['diagnostics'].update(connection_generation=2),
            lambda f: f['diagnostics']['hello'].update(pid=3525)]
        for mutation in changes:
            self.calls = 0
            after = deepcopy(self.after); mutation(after)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.service(after).initiate_character_interaction_ordinary_v1(self.key, self.recipient, expected_revision=3)
            self.assertEqual(self.calls, 1)

    def test_native_preflight_still_requires_exact_original_before(self):
        for field, value in [('snapshot_revision', 3), ('game_pid', 3525), ('connection_generation', 2)]:
            raw = deepcopy(self.receipt)
            raw[c.INITIATE_PAYLOAD]['preflight_context'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                c.normalize_public_initiation(raw, self.binding, self.key, self.recipient, self.later())


if __name__ == '__main__':
    unittest.main()
