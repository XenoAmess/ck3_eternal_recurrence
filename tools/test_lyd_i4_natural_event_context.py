"""Four new offline discovery guards; no runtime, queue, bus or game access."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

arguments = argparse.ArgumentParser(add_help=False)
arguments.add_argument('--candidate', type=Path)
arguments.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
options, remaining = arguments.parse_known_args()
sys.path.insert(0, str(options.repo_root / 'tools'))
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as natural

candidate = options.candidate or options.repo_root / 'tools/ck3_mod_acceptance_cases/lyd_i4_natural_event_context_adapter.py'
spec = importlib.util.spec_from_file_location('ck3_mod_acceptance_cases.event_discovery_candidate', candidate)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def frame(date=53144712, revision=1, event=None, pid=1234):
    return {'revision': revision, 'native_revision': revision, 'snapshot_id': 'native:' + str(revision),
        'date_raw': date, 'paused': True, 'source': 'injected-dll-named-pipe', 'backend_id': 'native-headless',
        'map_ready': True, 'episode_projection': 'native_campaign', 'active_event': event,
        'played_character': {'character_id': 31254, 'alive': True, 'source': 'native'},
        'diagnostics': {'bridge_pid': pid, 'connection_generation': 1,
            'hello': {'expected_ck3_version': '1.20.0.4', 'expected_ck3_sha256': 'a' * 64,
                      'ck3_build_match': True, 'pid': pid, 'connection_generation': 1}}}


class Client:
    validate_frame = CaseClient.validate_frame

    def __init__(self, output, event_on=1, wrong_owner=False):
        self.output, self.event_on, self.wrong_owner = Path(output), event_on, wrong_owner
        self.manifest = {'game': {'version': '1.20.0.4', 'exe_sha256': 'a' * 64}}
        self._binding, self.current, self.days, self.plans = None, frame(), 0, []
        self.validate_frame(self.current)

    def advance_day(self, *, days, timeout, allow_event_boundary):
        if days != 1 or timeout != 300 or allow_event_boundary is not True:
            raise ValueError('Exact public event-boundary opt-in missing')
        self.days += 1
        before = copy.deepcopy(self.current)
        event = {'instance_id': 600} if self.days == self.event_on else None
        hours = 6 if event else 24
        after = frame(before['date_raw'] + hours, before['native_revision'] + 1, event)
        boundary = copy.deepcopy(after) if event else None
        if boundary:
            boundary['paused'] = False
        self.current = after
        return {'id': 'day-' + str(self.days), 'ok': True, 'after_snapshot': copy.deepcopy(after),
            'result': {'before': before, 'after': copy.deepcopy(after), 'event_boundary': boundary,
                'requested_days': 1, 'elapsed_hours': hours, 'requested_interval_complete': event is None,
                'selected_event_options': 0, 'event_resolution': 'typed_query_required' if event else 'none'}}

    def snapshot(self, *, require_event_free):
        self.current = frame(self.current['date_raw'], self.current['native_revision'] + 1, self.current['active_event'])
        return self.validate_frame(copy.deepcopy(self.current), require_event_free=require_event_free)

    def execute_plan(self, steps, name):
        self.plans.append(copy.deepcopy(steps))
        if len(steps) != 1 or steps[0]['tool'] != adapter.TOOL or steps[0]['fresh_revision'] is not False:
            raise ValueError('Only one read-only typed discovery query is permitted')
        query = steps[0]
        if query['args'] != {'event_instance_id': 600, 'expected_revision': self.current['revision']}:
            raise ValueError('Query did not bind the actual event frame')
        typed = {'schema': 'current-event-window-context-v1', 'status': 'available',
            'current_event_instance_id': 600, 'date_raw': self.current['date_raw'],
            'snapshot_revision': self.current['native_revision'], 'event_definition_key': 'fixture.encounter',
            'root_scope': {'status': 'available', 'typed_identity': {'character_id': 31254}},
            'options': [{'native_option_index': 2, 'rendered_index': 0, 'shown': True, 'enabled': False}]}
        result = {'accepted': True, 'scope': 'exact-current-event-window', 'status': 'available',
            'current_event_window_context_ready': True, 'queried_revision': self.current['revision'],
            'queried_native_revision': self.current['native_revision'],
            'queried_snapshot_id': self.current['snapshot_id'], 'current_event_window_context': typed}
        after = copy.deepcopy(self.current)
        if self.wrong_owner:
            after['diagnostics']['bridge_pid'] = after['diagnostics']['hello']['pid'] = 9999
        row = {'id': name, 'ok': True, 'result': result, 'after_snapshot': after}
        (self.output / (name + '.actual-results.json')).write_text(json.dumps({'rows': [row]}), encoding='utf-8')
        return [row]


class DiscoveryTests(unittest.TestCase):
    def observe(self, client):
        initial = frame()
        return adapter.observe_until_event(client, adapter.contract(), initial, initial)

    def test_typed_boundary_preserves_real_partial_interval_and_zero_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory)
            value = self.observe(client)
            self.assertEqual(value['status'], 'PARTIAL_EVENT_CONTEXT_OBSERVED')
            self.assertEqual(value['elapsed_natural_hours'], 6)
            self.assertFalse(value['natural_intervals'][0]['requested_interval_complete'])
            self.assertEqual(value['event']['typed_context']['options'][0]['native_option_index'], 2)
            self.assertFalse(value['event']['typed_context']['options'][0]['enabled'])
            self.assertEqual(value['event']['event_choice_actions'], 0)
            self.assertEqual(value['event']['school_choice_actions'], 0)
            original = natural.base._checked_json(value['event']['original_result_ref'])
            self.assertEqual(original['rows'][0]['result'], value['event']['original_result'])
            self.assertEqual(len(client.plans), 1)

    def test_existing_nonboundary_day_keeps_original_day_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory, event_on=2)
            value = self.observe(client)
            self.assertEqual(value['elapsed_natural_hours'], 30)
            self.assertEqual(value['natural_intervals'][0]['interval_kind'], 'complete_natural_day')
            self.assertEqual(client.days, 2)
            mutant = Client(directory, event_on=2)
            original = mutant.advance_day
            def bad_interval(**kwargs):
                row = original(**kwargs)
                row['result']['elapsed_hours'] = 23
                return row
            mutant.advance_day = bad_interval
            with self.assertRaises(ValueError):
                self.observe(mutant)
            self.assertEqual(mutant.plans, [])

    def test_ninety_days_without_event_is_no_event_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory, event_on=None)
            value = self.observe(client)
            self.assertEqual(value['status'], 'NO_EVENT_OBSERVED')
            self.assertIsNone(value['event'])
            self.assertEqual(value['elapsed_natural_hours'], 90 * 24)
            self.assertEqual(len(value['natural_intervals']), 90)
            self.assertEqual(client.days, 90)
            self.assertEqual(client.plans, [])

    def test_cross_owner_typed_query_is_rejected_without_second_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory, wrong_owner=True)
            with self.assertRaises(ValueError):
                self.observe(client)
            self.assertEqual(client.days, 1)
            self.assertEqual(len(client.plans), 1)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
