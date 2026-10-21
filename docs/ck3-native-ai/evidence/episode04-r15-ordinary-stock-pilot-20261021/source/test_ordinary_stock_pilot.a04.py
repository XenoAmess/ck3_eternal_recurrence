"""Pure fake-client checks of the production finite pilot; no native qualification."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import json
import os
import sys
import tempfile
import unittest

TOOLS = os.environ['CK3_PILOT_PUBLIC_TOOLS']
sys.path.insert(0, TOOLS)
spec = importlib.util.spec_from_file_location('ordinary_stock_pilot_subject', Path(__file__).with_name('ordinary_stock_pilot.py'))
if spec is None or spec.loader is None:
    raise ValueError('Pilot source missing')
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)


class FakeClient:
    def __init__(self, output: Path) -> None:
        self.output = output
        self.split = False
        self.elapsed = 0
        self.serial = 0
        self.days = 0
        self.checkpoints: dict[str, object] = {}

    def retain_process(self) -> object:
        return {'synthetic': True}

    def guard(self, reserve: float = 90) -> object:
        if reserve != 90:
            raise ValueError('Original requested reserve differs')
        return {'synthetic': True}

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        self.serial += 1
        def army(identity: int) -> dict[str, object]:
            return {'army_id': identity, 'source': 'native', 'controllable': True,
                'owner_character_id': 31254, 'in_combat': False, 'retreating': False,
                'army_state': 'regular', 'route_read_status': 'complete_empty',
                'route_province_ids': [], 'move_target_province_id': None,
                'current_province_id': 2624}
        return {'paused': True, 'map_ready': True, 'episode_run_id': None,
            'revision': self.serial, 'native_revision': self.serial,
            'snapshot_id': 'SYNTHETIC:' + str(self.serial), 'date_raw': 53146848 + self.elapsed,
            'played_character': {'character_id': 31254},
            'diagnostics': {'bridge_pid': 1234, 'connection_generation': 1},
            'player_armies': [army(123)] + ([army(456)] if self.split else []),
            'active_event': None, 'pending_character_interaction': None}

    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        if days != 1 or not allow_event_boundary:
            raise ValueError('Original finite day flags differ')
        self.days += 1
        self.elapsed += 24
        return {'ok': True, 'result': {'requested_days': 1, 'requested_interval_complete': True,
                                      'event_boundary': None, 'elapsed_hours': 24}}

    def checkpoint(self, name: str, value: object) -> Path:
        self.checkpoints[name] = value
        return self.output / (name + '.json')


class FakeRelay:
    def __init__(self, client: FakeClient, *, headroom: bool = True, unknown_split: bool = False) -> None:
        self.client = client
        self.headroom = headroom
        self.unknown_split = unknown_split
        self.split_calls = 0
        self.claimed: set[str] = set()

    def request(self, identifier: str, tool: str, arguments: dict[str, object],
                timeout: float | None = None) -> object:
        if identifier in self.claimed:
            raise ValueError('No original request may replay')
        self.claimed.add(identifier)
        if tool == 'ck3_execute_step':
            self.split_calls += 1
            if arguments['step'] != 'split-army-half-123':
                raise ValueError('Stale historical Army ID used')
            self.client.split = True
            if self.unknown_split:
                raise RuntimeError('synthetic unknown original acknowledgement')
            body: dict[str, object] = {'accepted': True}
        elif tool == 'ck3_query_army_strengths':
            ids = arguments['army_ids']
            if not isinstance(ids, list):
                raise ValueError('Actual query scope invalid')
            strengths: list[dict[str, object]] = []
            for identity in ids:
                stock = 10000000 if identity == 123 or not self.headroom else 5000000 + self.client.elapsed * 100
                strengths.append({'army_id': identity, 'status': 'available',
                    'current_supply_raw': stock, 'current_supply_scale': 100000, 'unavailable_reason': None,
                    'current_supply_capacity_raw': 10000000, 'current_supply_capacity_scale': 100000,
                    'current_supply_change_monthly_raw': 2000000, 'current_supply_change_monthly_scale': 100000})
            full = arguments['profile'] == 'observed_history_full_v1'
            if not full:
                strengths = [{key: value for key, value in row.items() if key not in (
                    'current_supply_capacity_raw', 'current_supply_capacity_scale',
                    'current_supply_change_monthly_raw', 'current_supply_change_monthly_scale')} for row in strengths]
            body = {'accepted': True, 'army_strengths_profile': arguments['profile'],
                    'army_strengths' if full else 'armies': strengths}
        else:
            raise ValueError('Unexpected SDK tool: ' + tool)
        return {'is_error': False, 'body': body}


class PilotContract(unittest.TestCase):
    def test_actual_retained_r226_core_compact_keeps_partial_and_null_fields(self) -> None:
        retained = Path(os.environ['CK3_PILOT_RETAINED_CORE'])
        carrier = subject.obj(json.loads(retained.read_bytes()), 'original R226 control carrier')
        row = subject.rows(carrier['rows'], 'actual original rows')[0]
        body = subject.obj(row['result'], 'actual compact body')
        class ActualCoreRelay(FakeRelay):
            def request(self, identifier: str, tool: str, arguments: dict[str, object],
                        timeout: float | None = None) -> object:
                if tool != 'ck3_query_army_strengths' or arguments.get('profile') != 'ordinary_core_v1':
                    raise ValueError('Retained fixture is core only; never pretend it is full wire')
                return {'is_error': False, 'body': body}
        with tempfile.TemporaryDirectory(dir=os.environ['CK3_PILOT_SCRATCH']) as temporary:
            client = FakeClient(Path(temporary))
            relay = ActualCoreRelay(client)
            context: dict[str, object] = {'case_inputs': {'ordinary_stock_pilot': {
                'actor_id': 31254, 'origin_province_id': 2624, 'split_once_authorized': True,
                'maximum_day_requests': 1, 'one_day_timeout': 120}}}
            pilot = subject.Pilot(context, client, relay, 'SYNTHETIC-read-only-retained-source')
            frame = subject.obj(row['after_snapshot'], 'actual original after snapshot')
            scope = [subject.integer(x, 'actual scope id') for x in body['army_ids']]
            actual = pilot.strengths('retained-core', frame, scope, full=False)
            parsed = [pilot.core_stock(x) for x in actual]
            self.assertEqual(parsed[0]['stock_raw'], 10000000)
            self.assertIsNone(parsed[0]['capacity_raw'])
            self.assertIsNone(parsed[0]['final_monthly_rate_raw'])
            self.assertEqual(parsed[1]['status'], 'unavailable')
            self.assertIsNone(parsed[1]['stock_raw'])
            with self.assertRaisesRegex(ValueError, 'capacity'):
                pilot.stock(actual[0])

    def test_native_event_query_refreshes_revision_before_the_only_submission(self) -> None:
        class ModalClient(FakeClient):
            modal = True
            def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
                frame = subject.obj(super().snapshot(allow_actor_change, require_event_free), 'fake modal frame')
                if self.modal:
                    frame['active_event'] = {'instance_id': 123, 'options': [{'option_number': 1, 'enabled': True}]}
                return frame
        class ModalRelay(FakeRelay):
            selections = 0
            def request(self, identifier: str, tool: str, arguments: dict[str, object],
                        timeout: float | None = None) -> object:
                if tool == 'ck3_query_current_event_window_context_v1':
                    return {'is_error': False, 'body': {'current_event_window_context': {
                        'schema': 'current-event-window-context-v1', 'status': 'available',
                        'current_event_instance_id': 123, 'date_raw': 53146848,
                        'snapshot_revision': self.client.serial, 'event_definition_key': 'synthetic.uncovered',
                        'readiness': {'option_presentation_ready': True},
                        'options': [{'rendered_index': 0, 'native_option_index': 0, 'shown': True, 'enabled': True}]}}}
                if tool == 'ck3_select_event_option':
                    if arguments.get('expected_revision') != self.client.serial or self.client.serial != 2:
                        raise ValueError('Modal selection did not use independent refreshed revision')
                    self.selections += 1
                    client.modal = False
                    return {'is_error': False, 'body': {'accepted': True}}
                return super().request(identifier, tool, arguments, timeout)
        with tempfile.TemporaryDirectory(dir=os.environ['CK3_PILOT_SCRATCH']) as temporary:
            client = ModalClient(Path(temporary))
            relay = ModalRelay(client)
            context: dict[str, object] = {'shared_source_root': str(Path(temporary) / 'no-registry'),
                'case_inputs': {'ordinary_stock_pilot': {'actor_id': 31254, 'origin_province_id': 2624,
                    'split_once_authorized': True, 'maximum_day_requests': 1, 'one_day_timeout': 120}}}
            pilot = subject.Pilot(context, client, relay, 'SYNTHETIC-not-native')
            after = pilot.drain(subject.obj(client.snapshot(), 'initial modal'))
            self.assertIsNone(after['active_event'])
            self.assertEqual(relay.selections, 1)
            self.assertEqual(client.days, 0)

    def test_actual_pilot_split_day_and_refusals(self) -> None:
        for label, headroom, unknown, expected_days in [('growth', True, False, 1),
                ('full-child', False, False, 0), ('unknown-split', True, True, 0)]:
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=os.environ['CK3_PILOT_SCRATCH']) as temporary:
                client = FakeClient(Path(temporary))
                relay = FakeRelay(client, headroom=headroom, unknown_split=unknown)
                context: dict[str, object] = {'case_inputs': {'ordinary_stock_pilot': {
                    'actor_id': 31254, 'origin_province_id': 2624, 'split_once_authorized': True,
                    'maximum_day_requests': 1, 'one_day_timeout': 120}}}
                pilot = subject.Pilot(context, client, relay, 'SYNTHETIC-not-native')
                if unknown:
                    with self.assertRaisesRegex(RuntimeError, 'unknown original'):
                        pilot.run()
                else:
                    result = pilot.run()
                    self.assertEqual(result['stock_growth_observed'], headroom)
                    self.assertFalse(result['formal_B_site_qualified'])
                    self.assertEqual(result['formal_ABC_completed'], 0)
                self.assertEqual(relay.split_calls, 1)
                self.assertEqual(client.days, expected_days)
                self.assertEqual(pilot.result['split_submissions'], 1)
                frame = subject.obj(client.snapshot(), 'test frame')
                del frame['episode_run_id']
                with self.assertRaisesRegex(ValueError, 'Episode presence'):
                    subject.bound(frame, None, 31254)


if __name__ == '__main__':
    unittest.main()
