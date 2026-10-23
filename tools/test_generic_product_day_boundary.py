"""Real public day producer -> generic consumer; transport and Root are offline.

The R26 diagnostic/native wire are retained as actual RED evidence. Native-day
response envelopes and projection metadata below are authored test inputs, not
replacement live frames or claims that R26 used the native-day route.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from ck3_mod_acceptance_background_types import JsonObject, json_object
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
from ck3_mod_acceptance_client import CaseClient


def object_row(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError('Object required')
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError('String key required')
        result[key] = item
    return result


def evidence() -> JsonObject:
    path = Path(__file__).with_name('testdata') / 'generic_product_day_boundary/r26-pause-admission.actual.json'
    return json_object(json.loads(path.read_bytes()))


def frames() -> tuple[dict[str, object], dict[str, object]]:
    actual = evidence()
    before = object_row(copy.deepcopy(actual['actual_before_projection_subset']))
    record = object_row(actual['actual_native_wire_record'])
    message = object_row(record['message'])
    after = copy.deepcopy(before)
    after.update(object_row(copy.deepcopy(message['state'])))
    # A native wire state is not a complete public frame. These metadata fields
    # are an authored projection for exercising the existing public consumer.
    after['revision'] = int(str(before['revision'])) + 1
    after['native_revision'] = message['revision']
    actor = object_row(after['played_character'])
    actor['source'] = 'native'  # Authored public projection metadata, absent in wire state.
    after['played_character'] = actor
    return before, after


def native_row(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    return {'id': 'authored-native-response-over-retained-state', 'ok': True, 'error': None,
            'after_snapshot': copy.deepcopy(after), 'result': {
                'step': 'life-advance-one-day', 'source': 'native-composite',
                'backend_id': 'native-headless', 'starting_date_raw': before['date_raw'],
                'ending_date_raw': after['date_raw'], 'paused': True, 'requested_horizon_days': 1,
                'active_event': copy.deepcopy(after['active_event']),
                'pending_character_interaction': copy.deepcopy(after['pending_character_interaction']),
                'ordinary_events': [], 'actions': [], 'progress_status': 'event_boundary',
                'event_resolution': 'typed_query_required'}}


class PublicPort:
    """Use CaseClient methods unchanged, replacing only transport and Root IO."""
    def __init__(self, output: Path) -> None:
        self.output = output
        self.before, self.after = frames()
        self.fresh = copy.deepcopy(self.before)
        self.row = native_row(self.before, self.after)
        self._seq = 0
        self._binding: tuple[int, int, int] | None = None
        hello = object_row(object_row(self.before['diagnostics'])['hello'])
        self.manifest = {'game': {'version': hello['expected_ck3_version'],
                                  'exe_sha256': hello['expected_ck3_sha256']}}
        self.sent: list[dict[str, object]] = []
        self.requests: list[JsonObject] = []
        self.dispatched = False
        self.resolved = False
        self.resolve_on_ack = True
        self.boundary_successors: list[dict[str, object]] = []
        self.failure: Exception | None = None
        self.advertise_native = True
        self.report: dict[str, object] = {'steps': [], 'readiness': self.before, 'capabilities': {
            'action_steps': ['life-advance-one-day'], 'bridge_capabilities': [
                'game.command.research-arm-tactical-daily-sentinel-v1-N',
                'game.command.research-query-tactical-daily-sentinel-v1',
                'game.command.research-cancel-tactical-daily-sentinel-v1-generation-N',
                'game.command.query-current-event-window-context-v1']}}

    def guard(self, reserve: int = 90) -> dict[str, object]:
        if reserve != 90:
            raise AssertionError('Normal-close reserve changed')
        if not self.advertise_native:
            caps = object_row(self.report['capabilities'])
            caps['action_steps'] = []
            self.report['capabilities'] = caps
        return self.report

    def validate_frame(self, frame: object, allow_actor_change: bool = False,
                       require_event_free: bool = True, require_paused: bool = True) -> dict[str, object]:
        result: object = CaseClient.validate_frame(self, frame, allow_actor_change,
                                                   require_event_free, require_paused)
        return object_row(result)

    def snapshot(self, allow_actor_change: bool = False,
                 require_event_free: bool = True) -> JsonObject:
        result: object = CaseClient.snapshot(self, allow_actor_change, require_event_free)
        return json_object(result)

    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> dict[str, object]:
        result: object = CaseClient.advance_day(self, days, timeout,
                                                allow_event_boundary, allow_actor_change)
        return object_row(result)

    def execute_plan(self, steps: list[dict[str, object]], name: str,
                     timeout: float | None = None, reserve: int = 90) -> list[dict[str, object]]:
        if len(steps) != 1 or reserve != 90:
            raise AssertionError('Once-only public submission contract changed')
        self.sent.extend(copy.deepcopy(steps))
        if steps[0].get('tool') == 'ck3_take_snapshot':
            frame = copy.deepcopy(self.after if self.dispatched else self.fresh)
            if self.resolved:
                if self.boundary_successors:
                    frame = self.boundary_successors.pop(0)
                    self.after = copy.deepcopy(frame)
                    self.resolved = False
                else:
                    frame['active_event'] = None
                    frame['pending_character_interaction'] = None
            return [{'id': steps[0]['id'], 'result': frame}]
        self.dispatched = True
        if self.failure is not None:
            raise self.failure
        return [copy.deepcopy(self.row)]

    def checkpoint(self, name: str, value: object) -> Path:
        path = self.output / (name + '.json')
        path.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')
        return path

    def retain_process(self) -> JsonObject:
        return {}

    def log_bytes(self) -> bytes:
        return b'FIXTURE PASS' if self.dispatched or self.resolved else b''

    def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90) -> JsonObject:
        self.requests.append(copy.deepcopy(request))
        required = request['required_assertions']
        if not isinstance(required, list) or not all(isinstance(key, str) for key in required):
            raise AssertionError('Typed Root requirements required')
        proof = self.output / 'root-proof.txt'
        proof.write_text('authored original-context review; no game IO', encoding='utf-8')
        self.resolved = self.resolve_on_ack
        return json_object({'run_id': 'authored-run', 'reviewer': '/root',
                            'assertions': {str(key): True for key in required},
                            'evidence': [{'path': str(proof), 'bytes': proof.stat().st_size,
                                          'sha256': hashlib.sha256(proof.read_bytes()).hexdigest()}]})

    def world_calls(self) -> list[dict[str, object]]:
        return [step for step in self.sent if step.get('tool') != 'ck3_take_snapshot']


class GenericDayBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='generic-day-boundary-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.port = PublicPort(self.root)
        self.config: JsonObject = {'acceptance_scope': 'business', 'maximum_natural_days': 2,
                                  'gui_phases': [], 'failure_prefixes': [], 'source_contracts': []}
        self.context: JsonObject = {'product': 'authored-product', 'case': 'authored-case',
                                   'run_id': 'authored-run', 'state_dir': str(self.root),
                                   'case_contract': {},
                                   'case_spec': {'budgets': {'command_timeout': 300}}}

    def run_fixture(self) -> JsonObject:
        profile = self.root / 'profile'
        for relative in ('mod/product.mod', 'mod-content/product/descriptor.mod'):
            path = profile / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('name="authored product"', encoding='utf-8')
        (profile / 'dlc_load.json').write_text(json.dumps({'enabled_mods': ['mod/product.mod']}), encoding='utf-8')
        compiled = {'product': self.context['product'], 'case': self.context['case'],
                    'config': self.config, 'required_markers': ['FIXTURE PASS'],
                    'product_marker_minimum': {}}
        path = profile / 'mod-content/fixture/_case_contract.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(compiled), encoding='utf-8')
        return adapter.run_case(self.context, self.port)

    def test_actual_r26_only_failed_event_admission_preserves_red_diagnostic(self) -> None:
        actual = evidence()
        diagnostic = json_object(actual['campaign_pause_frame_diagnostic'])
        conditions = diagnostic['conditions']
        self.assertIsInstance(conditions, list)
        if not isinstance(conditions, list):
            self.fail('Actual diagnostic conditions missing')
        failed = [json_object(row) for row in conditions if json_object(row)['failed'] is True]
        self.assertEqual(len(conditions), 32)
        self.assertEqual([row['index'] for row in failed], [9])
        self.assertEqual(failed[0]['source'], 'snapshot.get("active_event") is not None and allowed_event_instance is None')
        self.assertEqual(actual['runtime_status'], 'RED')
        self.assertNotIn('allow_event_boundary', json_object(actual['failed_plan']))
        state = json_object(json_object(json_object(actual['actual_native_wire_record'])['message'])['state'])
        self.assertIs(state['paused'], True)
        self.assertEqual(state['active_event'], {'instance_id': 1, 'option_count': 2, 'option_indexes': [1, 2]})

    def test_day_protocol_matches_actual_public_producer_signature(self) -> None:
        self.assertEqual(inspect.signature(adapter.FixtureDayClient.advance_day),
                         inspect.signature(CaseClient.advance_day))

    def test_generic_uses_public_native_producer_then_root_exact_event_frame(self) -> None:
        facts = self.run_fixture()
        calls = self.port.world_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['tool'], 'ck3_execute_step')
        self.assertEqual(object_row(calls[0]['args'])['step'], 'life-advance-one-day')
        self.assertEqual(len(self.port.requests), 1)
        self.assertEqual(self.port.requests[0]['actual_snapshot'], self.port.after)
        self.assertEqual(self.port.requests[0]['required_assertions'], [
            'actual_current_event_resolved_with_typed_or_reviewed_original_evidence'])
        self.assertIs(facts['case_contract_qualified'], True)
        self.assertIs(facts['business_pass'], False)
        self.assertFalse(any('select' in str(call.get('tool', '')) for call in self.port.sent))

    def test_zero_hour_pre_dispatch_event_goes_to_root_without_world_dispatch(self) -> None:
        self.port.fresh['active_event'] = copy.deepcopy(self.port.after['active_event'])
        facts = self.run_fixture()
        self.assertEqual(self.port.world_calls(), [])
        self.assertEqual(len(self.port.requests), 1)
        self.assertEqual(json_object(self.port.requests[0]['actual_snapshot'])['date_raw'], self.port.before['date_raw'])
        self.assertIs(facts['case_contract_qualified'], True)

    def test_pending_notification_uses_separate_root_contract_and_readback(self) -> None:
        self.port.after['active_event'] = None
        self.port.after['pending_character_interaction'] = {
            'instance_id': 77, 'sender_character_id': 31408,
            'auto_accept_notification': False, 'source': 'native'}
        self.port.row = native_row(self.port.before, self.port.after)
        self.run_fixture()
        self.assertEqual(self.port.requests[0]['required_assertions'], [
            'actual_pending_character_interaction_resolved_with_typed_or_reviewed_original_evidence'])
        self.assertEqual(len(self.port.world_calls()), 1)

    def test_two_instances_on_same_date_have_distinct_root_checkpoints_without_day_replay(self) -> None:
        next_frame = copy.deepcopy(self.port.after)
        next_frame['active_event'] = {'instance_id': 2, 'option_count': 1, 'option_indexes': [1]}
        next_frame['revision'] = int(str(next_frame['revision'])) + 1
        self.port.boundary_successors = [next_frame]
        facts = self.run_fixture()
        self.assertEqual(len(self.port.world_calls()), 1)
        self.assertEqual(len(self.port.requests), 2)
        snapshots = [json_object(row['actual_snapshot']) for row in self.port.requests]
        self.assertEqual([row['date_raw'] for row in snapshots], [self.port.after['date_raw']] * 2)
        self.assertEqual([json_object(row['active_event'])['instance_id'] for row in snapshots], [1, 2])
        self.assertEqual(set(json_object(facts['root_phases'])), {
            'actual-event-boundary-001', 'actual-event-boundary-002'})

    def test_root_ack_does_not_clear_event_or_pending_and_never_advances_again(self) -> None:
        for kind in ('event', 'notification'):
            with self.subTest(kind=kind):
                output = self.root / kind
                output.mkdir()
                self.port = PublicPort(output)
                self.port.resolve_on_ack = False
                if kind == 'notification':
                    self.port.after['active_event'] = None
                    self.port.after['pending_character_interaction'] = {
                        'instance_id': 77, 'sender_character_id': 31408,
                        'auto_accept_notification': False, 'source': 'native'}
                    self.port.row = native_row(self.port.before, self.port.after)
                with self.assertRaises(ValueError):
                    self.run_fixture()
                self.assertEqual(len(self.port.world_calls()), 1)
                self.assertEqual(len(self.port.requests), 1)

    def test_successor_requires_strict_distinct_native_instance_identity(self) -> None:
        for bad_id in (True, 1.0, 0, None, '2', 1):
            with self.subTest(instance_id=bad_id):
                next_frame = copy.deepcopy(self.port.after)
                next_frame['active_event'] = {'instance_id': bad_id}
                with self.assertRaises(ValueError):
                    adapter._require_fixture_boundary_resolved(self.port.after, next_frame, 'event')

    def test_explicit_transition_keeps_original_wait_field_and_sequence_only(self) -> None:
        row = adapter._advance_fixture_day(self.port, {'actor_transition_days': [1]}, 1, 300)
        self.assertEqual(row, self.port.row)
        self.assertEqual(self.port.world_calls(), [{'id': 'product-natural-day-001', 'kind': 'advance_day',
            'days': 1, 'timeout': 300, 'wait_for_played_character_change': True}])
        other = PublicPort(self.root)
        adapter._advance_fixture_day(other, {'actor_transition_days': [1]}, 2, 300)
        self.assertEqual(len(other.world_calls()), 1)
        self.assertEqual(other.world_calls()[0]['tool'], 'ck3_execute_step')

    def test_fallback_and_actor_policy_retain_existing_public_event_boundary_route(self) -> None:
        from ck3_mod_acceptance_native_day import project_native_day
        for actor_change in (False, True):
            with self.subTest(actor_change=actor_change):
                port = PublicPort(self.root)
                port.advertise_native = actor_change
                port.row = project_native_day(port.row, port.before, allow_event_boundary=True)
                adapter._advance_fixture_day(port, {'allow_actor_change': actor_change}, 1, 300)
                call = port.world_calls()[0]
                self.assertEqual(call['kind'], 'advance_day')
                self.assertIs(call['allow_event_boundary'], True)
                self.assertEqual(call.get('allow_actor_change', False), actor_change)
                self.assertNotIn('wait_for_played_character_change', call)

    def test_policy_boundary_rejects_bool_float_ids_flags_and_invalid_timeouts(self) -> None:
        cases: list[tuple[object, object, object]] = [
            ({'actor_transition_days': [True]}, 1, 300), ({'actor_transition_days': [1.0]}, 1, 300),
            ({'actor_transition_days': [0]}, 1, 300), ({'actor_transition_days': [1, 1]}, 1, 300),
            ({'actor_transition_days': None}, 1, 300), ({'allow_actor_change': 1}, 1, 300),
            ({}, True, 300), ({}, 1.0, 300), ({}, 1, True), ({}, 1, 0),
            ({}, 1, float('inf')), ({}, 1, float('nan'))]
        for config, sequence, timeout in cases:
            with self.subTest(config=config, sequence=sequence, timeout=timeout):
                with self.assertRaises(ValueError):
                    adapter._advance_fixture_day(self.port, config, sequence, timeout)
        self.assertEqual(self.port.sent, [])

    def test_real_pause_owner_build_and_date_guards_remain_strict(self) -> None:
        for field in ('paused', 'owner', 'build', 'date'):
            with self.subTest(field=field):
                port = PublicPort(self.root)
                after = object_row(port.row['after_snapshot'])
                if field == 'paused':
                    after['paused'] = False
                elif field == 'owner':
                    diagnostics = object_row(after['diagnostics'])
                    diagnostics['bridge_pid'] = 9999
                    after['diagnostics'] = diagnostics
                elif field == 'build':
                    diagnostics = object_row(after['diagnostics'])
                    hello = object_row(diagnostics['hello'])
                    hello['ck3_build_match'] = False
                    diagnostics['hello'] = hello
                    after['diagnostics'] = diagnostics
                else:
                    after['date_raw'] = int(str(after['date_raw'])) + 24
                port.row['after_snapshot'] = after
                with self.assertRaises(ValueError):
                    adapter._advance_fixture_day(port, {}, 1, 300)
                self.assertEqual(len(port.world_calls()), 1)
                self.assertEqual(port.requests, [])

    def test_unknown_submission_never_falls_back_or_replays(self) -> None:
        self.port.failure = TimeoutError('Authored once-only response lost')
        with self.assertRaises(TimeoutError):
            self.run_fixture()
        self.assertEqual(len(self.port.world_calls()), 1)
        self.assertEqual(self.port.world_calls()[0]['tool'], 'ck3_execute_step')
        self.assertEqual(self.port.requests, [])


if __name__ == '__main__':
    unittest.main()
