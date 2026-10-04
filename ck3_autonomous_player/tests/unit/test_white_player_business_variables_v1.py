"""New fixed-key DTO/request boundaries only; synthetic data, no native endpoint."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256
from xar_autoplayer.bridge.white_player_business_variables_contract import (
    STEP, CAPABILITY, SCHEMA, VARIABLE_KEYS, business_binding, normalize_white_player_business_variables,
)


def frame():
    return dict(revision=9, native_revision=77, snapshot_id='synthetic-white-paused-77',
        episode_run_id='synthetic-white-variable-episode', paused=True, map_ready=True,
        active_event=None, date_raw=53144328, played_character=dict(character_id=7001, alive=True),
        diagnostics=dict(connection_generation=3, pid=99999, hello=dict(pid=49777,
            ck3_build_match=True, game_adapter_id='ck3-1.20.0.3-msvc-x64',
            expected_ck3_version='1.20.0.3', expected_ck3_sha256=EXE_SHA256)))


def scalar(payload=100000, kind=1):
    return dict(present=True, actual_kind=kind, actual_payload=payload,
                fixed_raw=payload if kind == 1 else None,
                integer_value=payload // 100000 if kind == 1 and payload % 100000 == 0 else None)


def absent():
    return dict(present=False, actual_kind=None, actual_payload=None, fixed_raw=None, integer_value=None)


def observation():
    binding = business_binding(frame())
    return dict(schema=SCHEMA, step=STEP, available=True, all_eight_numeric_integers=True,
        **{key: binding[key] for key in ('native_revision', 'connection_generation', 'game_pid', 'played_character_id', 'date_raw')},
        owner_thread_verified=True, frame_verified=True, source_abi_pins_verified=True,
        player_scope_verified=True, stable_two_pass_values=True, rendered_text_available=False,
        selected_down_available=False, scriptvalue_price_available=False, application_thread_id=7401,
        application_pump_epoch=88, application_tls_context=0x1000, variable_context=0x2000,
        character_address=0x3000, fixed_scale=100000,
        fields={key: scalar(0 if index == 0 else 100000) for index, key in enumerate(VARIABLE_KEYS)},
        status='observed_business_variables', unavailable_reason='')


class SyntheticDriver:
    query_white_player_business_variables_v1 = NativeHeadlessGameplayDriver.query_white_player_business_variables_v1

    def __init__(self, raw=None):
        self.frame = frame()
        self.raw = deepcopy(observation() if raw is None else raw)
        self.allowed = True
        self.snapshots = 0
        self.submissions = []
        self.error = None
        self.after = None

    def capabilities(self):
        return {'bridge_capabilities': [CAPABILITY] if self.allowed else []}

    def take_snapshot(self):
        self.snapshots += 1
        value = deepcopy(self.frame)
        if self.snapshots > 1 and self.after:
            self.after(value)
        return value

    def _execute_primitive_step(self, step, **kwargs):
        self.submissions.append((step, kwargs))
        if self.error:
            raise self.error
        return deepcopy(self.raw)


class WhiteBusinessVariableTests(unittest.TestCase):
    def test_real_zero_absent_wrong_type_and_fraction_stay_distinct(self):
        for value in [scalar(0), absent(), scalar(-123, 4), scalar(150001), scalar(-150001)]:
            raw = observation()
            raw['fields'][VARIABLE_KEYS[0]] = deepcopy(value)
            raw['all_eight_numeric_integers'] = value['present'] and value['integer_value'] is not None
            result = normalize_white_player_business_variables(raw, business_binding(frame()))
            self.assertEqual(result['fields'][VARIABLE_KEYS[0]], value)
            self.assertTrue(result['available'])
            self.assertIsNot(result['fields'], raw['fields'])

    def test_scalar_bool_width_or_invented_numeric_projection_rejects(self):
        mutations = [dict(actual_kind=True), dict(actual_kind=65536), dict(actual_payload=2**63),
                     dict(actual_payload=True), dict(fixed_raw=True), dict(integer_value=True),
                     dict(fixed_raw=0), dict(integer_value=2),
                     dict(actual_kind=4, fixed_raw=100000, integer_value=1),
                     dict(actual_payload=150001, fixed_raw=150001, integer_value=1),
                     dict(present=False, actual_kind=0, actual_payload=0, fixed_raw=None, integer_value=None)]
        for change in mutations:
            with self.subTest(change=change):
                raw = observation()
                raw['fields'][VARIABLE_KEYS[1]].update(change)
                with self.assertRaises(ValueError):
                    normalize_white_player_business_variables(raw, business_binding(frame()))

    def test_fixed_key_census_scale_status_and_no_gui_credit_reject(self):
        changes = [('fixed_scale', True), ('fixed_scale', 1000), ('all_eight_numeric_integers', False),
                   ('status', 'default_initialized'), ('unavailable_reason', 'unexpected'),
                   ('rendered_text_available', True), ('selected_down_available', True),
                   ('scriptvalue_price_available', True), ('available', 1)]
        for key, value in changes:
            raw = observation()
            raw[key] = value
            with self.assertRaises(ValueError):
                normalize_white_player_business_variables(raw, business_binding(frame()))
        for change in ['missing', 'unknown', 'unexpected-field']:
            raw = observation()
            if change == 'missing': raw['fields'].pop(VARIABLE_KEYS[0])
            elif change == 'unknown': raw['fields']['arbitrary_variable'] = scalar()
            else: raw['fields'][VARIABLE_KEYS[0]]['guess'] = 0
            with self.assertRaises(ValueError):
                normalize_white_player_business_variables(raw, business_binding(frame()))

    def test_available_requires_actual_owner_abi_frame_and_request_identity(self):
        for key in ['owner_thread_verified', 'source_abi_pins_verified', 'player_scope_verified',
                    'stable_two_pass_values', 'frame_verified']:
            raw = observation()
            raw[key] = False
            with self.assertRaises(ValueError):
                normalize_white_player_business_variables(raw, business_binding(frame()))
        for key in ['native_revision', 'game_pid', 'connection_generation', 'played_character_id', 'date_raw']:
            for value in [True, observation()[key] + 1]:
                raw = observation()
                raw[key] = value
                with self.assertRaises(ValueError):
                    normalize_white_player_business_variables(raw, business_binding(frame()))
        raw = observation()
        raw['character_address'] = 0
        with self.assertRaises(ValueError):
            normalize_white_player_business_variables(raw, business_binding(frame()))

    def test_unavailable_keeps_refusal_and_never_partial_values(self):
        raw = observation()
        raw.update(available=False, all_eight_numeric_integers=False, frame_verified=False,
                   status='unavailable', unavailable_reason='pipe_completion_business_binding_changed',
                   fields={key: absent() for key in VARIABLE_KEYS})
        self.assertEqual(normalize_white_player_business_variables(raw, business_binding(frame())), raw)
        for name in ['missing-reason', 'partial-value']:
            bad = deepcopy(raw)
            if name == 'missing-reason': bad['unavailable_reason'] = ''
            else: bad['fields'][VARIABLE_KEYS[0]] = scalar(0)
            with self.assertRaises(ValueError):
                normalize_white_player_business_variables(bad, business_binding(frame()))

    def test_snapshot_qualification_requires_actual_exact_noevent_episode(self):
        for change in [lambda s: s.update(active_event={'event_id': 'synthetic'}),
                       lambda s: s.pop('active_event'), lambda s: s.update(episode_run_id=None),
                       lambda s: s['played_character'].update(alive=False),
                       lambda s: s['diagnostics']['hello'].update(expected_ck3_version='1.20.0.2')]:
            state = frame()
            change(state)
            with self.assertRaises(ValueError): business_binding(state)

    def test_driver_binds_actual_native_pid_and_service_forwarding_once(self):
        driver = SyntheticDriver()
        service = SimpleNamespace(driver=driver)
        result = GameplayBridgeService.query_white_player_business_variables_v1(service, expected_revision=9)
        self.assertEqual(driver.submissions, [(STEP, dict(expected_revision=9, required_capability=CAPABILITY,
            request_fields=dict(expected_player_character_id=7001, expected_game_pid=49777,
                                expected_connection_generation=3)))])
        self.assertEqual(driver.snapshots, 2)
        self.assertEqual(result['queried_revision'], 9)
        self.assertEqual(result['fields'][VARIABLE_KEYS[0]]['integer_value'], 0)
        self.assertTrue(result['read_only'])
        for key in ['gui_acceptance_credit', 'uses_mouse', 'uses_keyboard', 'uses_ocr',
                    'rendered_text_available', 'selected_down_available', 'scriptvalue_price_available']:
            self.assertIs(result[key], False)

    def test_unsupported_strict_revision_and_active_event_fail_before_submit(self):
        driver = SyntheticDriver()
        driver.allowed = False
        with self.assertRaises(UnsupportedStepError): driver.query_white_player_business_variables_v1()
        self.assertEqual(driver.snapshots, 0)
        for value in [True, '9', -1, 2**64]:
            driver = SyntheticDriver()
            with self.assertRaises(ValueError): driver.query_white_player_business_variables_v1(expected_revision=value)
            self.assertEqual(driver.snapshots, 0)
            self.assertEqual(driver.submissions, [])
        driver = SyntheticDriver()
        with self.assertRaises(PreSubmissionRevisionMismatchError): driver.query_white_player_business_variables_v1(expected_revision=8)
        self.assertEqual(driver.submissions, [])
        driver = SyntheticDriver()
        driver.frame['active_event'] = {'event_id': 'synthetic'}
        with self.assertRaises(BridgeUnavailableError): driver.query_white_player_business_variables_v1()
        self.assertEqual(driver.submissions, [])

    def test_later_generation_episode_actor_date_or_snapshot_change_rejects(self):
        for change in [lambda s: s['diagnostics'].update(connection_generation=4),
                       lambda s: s.update(episode_run_id='later-episode'),
                       lambda s: s['played_character'].update(character_id=7002),
                       lambda s: s.update(date_raw=53144329),
                       lambda s: s.update(snapshot_id='later-snapshot'),
                       lambda s: s.update(active_event={'event_id': 'later-event'})]:
            driver = SyntheticDriver()
            driver.after = change
            with self.assertRaises(BridgeUnavailableError): driver.query_white_player_business_variables_v1()
            self.assertEqual(len(driver.submissions), 1)

    def test_native_error_is_not_retried_or_replaced_with_defaults(self):
        driver = SyntheticDriver()
        driver.error = TimeoutError('synthetic native timeout')
        with self.assertRaises(TimeoutError): driver.query_white_player_business_variables_v1()
        self.assertEqual(len(driver.submissions), 1)
        self.assertEqual(driver.snapshots, 1)

    def test_service_rejects_missing_backend_or_unsupported_gui_credit(self):
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService.query_white_player_business_variables_v1(SimpleNamespace(driver=object()))
        driver = SyntheticDriver()
        result = driver.query_white_player_business_variables_v1()
        result['selected_down_available'] = True
        fake = SimpleNamespace(query_white_player_business_variables_v1=lambda **kwargs: result)
        with self.assertRaises(BridgeUnavailableError):
            GameplayBridgeService.query_white_player_business_variables_v1(SimpleNamespace(driver=fake))


if __name__ == '__main__':
    unittest.main()
