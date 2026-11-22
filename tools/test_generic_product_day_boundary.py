"""Real public day producer -> generic consumer; transport and Root are offline.

The R26 diagnostic/native wire are retained as actual RED evidence. Native-day
response envelopes and projection metadata below are authored test inputs, not
replacement live frames or claims that R26 used the native-day route.
"""
from __future__ import annotations

import copy
import asyncio
from types import SimpleNamespace
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from ck3_mod_acceptance_background_types import JsonObject, json_object
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_native_day import (PendingInteractionPolicy, admit_pending_interaction_policy_v1,
    pending_interaction_policy_v1, pending_inbox_observation_v1)


def object_row(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError('Object required')
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError('String key required')
        result[key] = item
    return result


def object_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError('Object list required')
    return [object_row(item) for item in value]


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
        self.selection = SimpleNamespace(adapter_context=lambda: {})
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
                    allow_actor_change: bool = False,
                    pending_interaction_policy: PendingInteractionPolicy = "stop_at_boundary") -> dict[str, object]:
        result: object = CaseClient.advance_day(self, days, timeout,
                                                allow_event_boundary, allow_actor_change, pending_interaction_policy)
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
        for relative in ('mod/product.mod', 'mod-content/product/descriptor.mod', 'mod/fixture.mod'):
            path = profile / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('name="authored product"', encoding='utf-8')
        (profile / 'dlc_load.json').write_text(json.dumps({'enabled_mods': ['mod/product.mod', 'mod/fixture.mod']}), encoding='utf-8')
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


class UnansweredInboxPolicyTests(unittest.TestCase):
    """Actual Host/SDK software producer -> public day client -> generic case.

    The Host helper uses existing C++ Full/ACK sources and real bounded clock
    methods. Only OS/Game IO and public queue transport are software fixtures.
    No actual scene or SAVE certification is inferred from these tests.
    """
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='inbox-observation-public-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def producer(self, before: dict[str, object] | None, after: dict[str, object] | None,
                 *, case: str = 'market-evolution', event: dict[str, object] | None = None,
                 date: int = 24024) -> tuple[dict[str, object], list[dict[str, object]]]:
        from test_ck3_mod_acceptance_campaign_event import FlorinCampaignEventTests
        FlorinCampaignEventTests.setUpClass()
        source = FlorinCampaignEventTests()
        self.addCleanup(source.doCleanups)
        directory = self.root / ('host-' + str(len(list(self.root.glob('host-*')))))
        directory.mkdir()
        host = source.client(directory, starting_pending=before, pending=after,
                             event=event, boundary_date=date, purpose=('financial-markets', case))
        # A normalized semantic character is not a native Full payload: its
        # nested build metadata has already been consumed. Preserve that actual
        # metadata from the exact C++ packet, and update only the inert clock
        # fixture's observed world fields before using the real SDK decoder.
        from xar_autoplayer.bridge.native_driver import NativeProtocolState
        fixtures = Path(__file__).resolve().parents[1] / 'java/ck3-control/native-transport/src/test/resources/newnative'
        raw = (fixtures / 'full1210/full-snapshot-producer-102.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5')
        template = object_row(json.loads(raw))
        protocol = NativeProtocolState('software-inbox-public-projection')
        capabilities = object_row(host.driver.capabilities())
        hello = object_row(object_row(capabilities['diagnostics'])['hello'])
        self.assertEqual(protocol.ingest(hello), 'hello')
        original_fresh = host.fresh

        async def public_fresh() -> dict[str, object]:
            snapshot: object = await original_fresh()
            internal = object_row(snapshot)
            packet = copy.deepcopy(template)
            state = object_row(packet['state'])
            for field in ('date_raw', 'speed', 'paused', 'active_event',
                          'pending_character_interaction', 'active_wars', 'player_armies',
                          'episode_projection', 'episode_run_id'):
                state[field] = copy.deepcopy(internal[field])
            self.assertEqual(state['played_character'], object_row(template['state'])['played_character'])
            packet.update(snapshot_id=internal['snapshot_id'],
                          revision=internal['native_revision'], state=state)
            self.assertEqual(protocol.ingest(packet), 'state_snapshot')
            public = object_row(protocol.semantic_snapshot())
            self.assertEqual(public['source'], 'injected-dll-named-pipe')
            # Both sides of the inert transport now use the same SDK-issued
            # public revision; the real primitive still checks that revision.
            host.snapshot = copy.deepcopy(public)
            host.driver.snapshot = copy.deepcopy(public)
            return public

        host.fresh = public_fresh
        result: object = asyncio.run(host.advance_event_boundary(source.inbox_step()))
        return object_row(result), [object_row(row) for row in host.driver.sent]

    def port(self, result: dict[str, object], *, case: str = 'market-evolution', declared: bool = True) -> PublicPort:
        directory = self.root / ('public-' + str(len(list(self.root.glob('public-*')))))
        directory.mkdir()
        port = PublicPort(directory)
        port.before = copy.deepcopy(object_row(result['before']))
        port.fresh = copy.deepcopy(port.before)
        port.after = copy.deepcopy(object_row(result['after']))
        hello = object_row(object_row(port.before['diagnostics'])['hello'])
        port.manifest = {'game': {'version': hello['expected_ck3_version'], 'exe_sha256': hello['expected_ck3_sha256']}}
        port.row = {'id': 'software-actual-host-producer', 'ok': True, 'error': None,
                    'result': copy.deepcopy(result), 'after_snapshot': copy.deepcopy(port.after)}
        port.advertise_native = False
        port.report = {'steps': [], 'readiness': port.before,
                       'capabilities': {'action_steps': [], 'bridge_capabilities': []}}
        contract = {'product': 'financial-markets', 'case_id': case}
        if declared:
            contract['pending_interaction_policy'] = 'observe_unanswered_inbox'
        port.selection = SimpleNamespace(adapter_context=lambda: {
            'product': 'financial-markets', 'case': case, 'case_contract': contract})
        return port

    def generic(self, port: PublicPort, *, case: str = 'market-evolution') -> JsonObject:
        profile = port.output / 'profile'
        for relative in ('mod/product.mod', 'mod-content/product/descriptor.mod', 'mod/fixture.mod'):
            path = profile / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('name="authored software product"', encoding='utf-8')
        (profile / 'dlc_load.json').write_text(json.dumps({'enabled_mods': ['mod/product.mod', 'mod/fixture.mod']}), encoding='utf-8')
        config = {'product': 'financial-markets', 'case_id': case, 'pending_interaction_policy': 'observe_unanswered_inbox',
                  'acceptance_scope': 'authored observation', 'maximum_natural_days': 1,
                  'gui_phases': [], 'failure_prefixes': [], 'source_contracts': []}
        compiled = {'product': 'financial-markets', 'case': case, 'config': config,
                    'required_markers': ['FIXTURE PASS'], 'product_marker_minimum': {}}
        path = profile / 'mod-content/fixture/_case_contract.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(compiled), encoding='utf-8')
        context = {'product': 'financial-markets', 'case': case, 'run_id': 'authored-run',
                   'state_dir': str(port.output), 'case_contract': config,
                   'case_spec': {'budgets': {'command_timeout': 300}}}
        return json_object(adapter.run_case(context, port))

    @staticmethod
    def inbox(identity: int = 33554448, sender: int = 34232) -> dict[str, object]:
        return {'instance_id': identity, 'sender_character_id': sender,
                'auto_accept_notification': False, 'source': 'native'}

    def test_actual_host_producer_reaches_both_declared_cases_without_reply_or_root_notification_phase(self) -> None:
        for case in ('market-evolution', 'delisting-gui'):
            with self.subTest(case=case):
                pending = self.inbox()
                result, native_steps = self.producer(pending, pending, case=case)
                port = self.port(result, case=case)
                facts = self.generic(port, case=case)
                self.assertEqual(len(port.world_calls()), 1)
                self.assertEqual(port.world_calls()[0]['kind'], 'advance_day')
                self.assertEqual(port.world_calls()[0]['pending_interaction_policy'], 'observe_unanswered_inbox')
                self.assertIs(port.world_calls()[0]['allow_event_boundary'], True)
                self.assertEqual(port.requests, [])
                self.assertIs(facts['business_pass'], False)
                observed = object_rows(facts['pending_interaction_observations'])
                self.assertEqual(observed, [result['pending_interaction_observation']])
                self.assertIs(object_row(observed[0])['resolved'], False)
                self.assertEqual(object_row(observed[0])['modal_status'], 'not_observed')
                sent = [str(row['step']) for row in native_steps]
                self.assertEqual(sent.count('resume-map'), 1)
                self.assertEqual(sum(step.startswith('research-arm-') for step in sent), 1)
                self.assertFalse(any('reply' in step or 'select-event' in step for step in sent))

    def test_actual_host_changes_are_retained_without_resolution_credit_and_signed_full_ids_survive(self) -> None:
        pending = self.inbox(0, -(2**31))
        other = self.inbox(-(2**31), 0)
        scenarios: list[tuple[dict[str, object] | None, dict[str, object] | None, str]] = [
            (None, pending, 'appeared'), (pending, None, 'disappeared'), (pending, other, 'changed')]
        for before, after, kind in scenarios:
            with self.subTest(kind=kind):
                result, _ = self.producer(before, after)
                port = self.port(result)
                row = port.advance_day(allow_event_boundary=True, pending_interaction_policy='observe_unanswered_inbox')
                observation = object_row(object_row(row['result'])['pending_interaction_observation'])
                self.assertEqual(observation['before'], before)
                self.assertEqual(observation['after'], after)
                self.assertEqual([object_row(change)['change'] for change in object_rows(observation['changes'])], [kind])
                self.assertIs(observation['resolved'], False)
                self.assertIs(observation['reply_attempted'], False)
                self.assertEqual(len(port.world_calls()), 1)

    def test_actual_event_is_still_a_root_event_boundary_with_inbox_preserved(self) -> None:
        pending = self.inbox()
        result, _ = self.producer(pending, pending, event={'instance_id': 42}, date=24012)
        port = self.port(result)
        successor = copy.deepcopy(port.after)
        successor['active_event'] = None
        port.boundary_successors = [successor]
        facts = self.generic(port)
        self.assertEqual(len(port.requests), 1)
        self.assertEqual(port.requests[0]['required_assertions'], [
            'actual_current_event_resolved_with_typed_or_reviewed_original_evidence'])
        self.assertEqual(port.after['pending_character_interaction'], pending)
        self.assertIs(object_rows(facts['pending_interaction_observations'])[0]['resolved'], False)
        self.assertEqual(len(port.world_calls()), 1)

    def test_scope_and_policy_types_refuse_before_public_world_dispatch(self) -> None:
        result, _ = self.producer(self.inbox(), self.inbox())
        for value in (None, True, False, 0, 1.0, '', 'observe-unanswered-inbox', 'unknown'):
            with self.subTest(policy=value):
                port = self.port(result)
                with self.assertRaises(ValueError):
                    CaseClient.advance_day(port, allow_event_boundary=True, pending_interaction_policy=value)
                self.assertEqual(port.sent, [])
        for case, declared in (('spot', True), ('market-evolution', False)):
            with self.subTest(case=case, declared=declared):
                port = self.port(result, case=case, declared=declared)
                with self.assertRaises(ValueError):
                    port.advance_day(allow_event_boundary=True, pending_interaction_policy='observe_unanswered_inbox')
                self.assertEqual(port.sent, [])
        port = self.port(result)
        with self.assertRaises(ValueError):
            port.advance_day(allow_event_boundary=False, pending_interaction_policy='observe_unanswered_inbox')
        self.assertEqual(port.sent, [])

    def test_actual_producer_payload_mutations_never_become_a_false_observation(self) -> None:
        result, _ = self.producer(None, self.inbox())
        original = object_row(result['pending_interaction_observation'])
        mutations = [('resolved', True), ('reply_attempted', True), ('modal_status', 'non_modal'),
                     ('starting_snapshot_id', 'other'), ('changes', [])]
        for field, wrong in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(original); changed[field] = wrong
                with self.assertRaises(ValueError):
                    pending_inbox_observation_v1(changed, object_row(result['before']), object_row(result['after']))
        for field in ('instance_id', 'sender_character_id'):
            for bad in (True, 1.0, -1, -(2**31)-1, 2**31):
                with self.subTest(field=field, bad=bad):
                    changed = copy.deepcopy(original)
                    changed_after = object_row(changed['after'])
                    changed_after[field] = bad
                    changed['after'] = changed_after
                    with self.assertRaises(ValueError):
                        pending_inbox_observation_v1(changed, object_row(result['before']), object_row(result['after']))

    def test_unfinished_original_day_and_unknown_still_fail_without_retry_or_fallback(self) -> None:
        result, _ = self.producer(self.inbox(), self.inbox())
        port = self.port(result)
        unfinished = object_row(port.row['result'])
        unfinished['requested_interval_complete'] = False
        port.row['result'] = unfinished
        with self.assertRaises(ValueError):
            port.advance_day(allow_event_boundary=True, pending_interaction_policy='observe_unanswered_inbox')
        self.assertEqual(len(port.world_calls()), 1)
        lost = self.port(result)
        lost.failure = TimeoutError('authored original queue result unknown')
        with self.assertRaises(TimeoutError):
            lost.advance_day(allow_event_boundary=True, pending_interaction_policy='observe_unanswered_inbox')
        self.assertEqual(len(lost.world_calls()), 1)
        self.assertEqual(lost.requests, [])

    def test_only_two_actual_case_files_declare_the_optin_and_other_scopes_keep_default(self) -> None:
        root = Path(__file__).resolve().parents[1]
        declared = {}
        for path in (root / 'tools/ck3_mod_acceptance_cases').glob('financial_markets_*.json'):
            config = json.loads(path.read_text(encoding='utf-8-sig'))
            value = adapter._fixture_pending_interaction_policy(config)
            if value == 'observe_unanswered_inbox':
                declared[config['case_id']] = value
            else:
                self.assertEqual(value, 'stop_at_boundary', str(path))
                self.assertTrue('pending_interaction_policy' not in config
                                or config['pending_interaction_policy'] == 'stop_at_boundary', str(path))
        self.assertEqual(declared, {'market-evolution': 'observe_unanswered_inbox',
            'market-evolution-continuation21': 'observe_unanswered_inbox', 'delisting-gui': 'observe_unanswered_inbox'})
        self.assertEqual(pending_interaction_policy_v1('stop_at_boundary'), 'stop_at_boundary')
        self.assertEqual(admit_pending_interaction_policy_v1('stop_at_boundary', product='anything', case=None), 'stop_at_boundary')
        for product, case in (('other', 'market-evolution'), ('financial-markets', 'spot'), ('financial-markets', None)):
            with self.assertRaises(ValueError):
                admit_pending_interaction_policy_v1('observe_unanswered_inbox', product=product, case=case)


if __name__ == '__main__':
    unittest.main()
