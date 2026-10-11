"""New continuation fixtures only. No bus, queue, game, native or saved body access."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--candidate', type=Path)
parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
options, remaining = parser.parse_known_args()
sys.path.insert(0, str(options.repo_root / 'tools'))
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as natural

candidate = options.candidate or options.repo_root / 'tools/ck3_mod_acceptance_cases/lyd_i4_natural_event_continuation_adapter.py'
spec = importlib.util.spec_from_file_location('ck3_mod_acceptance_cases.continuation_candidate', candidate)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
GAME = {'version': '1.20.0.4', 'exe_sha256': '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'}


def event(instance=101):
    return {'source': 'native', 'instance_id': instance, 'option_count': 3, 'title': None,
            'options': [{'index': i, 'option_number': i + 1, 'label': None, 'enabled': True} for i in range(3)]}


def frame(date=53144712, revision=1, active=None, pid=1234):
    return {'revision': revision, 'native_revision': revision, 'snapshot_id': 'native:' + str(revision),
        'date_raw': date, 'paused': True, 'source': 'injected-dll-named-pipe', 'backend_id': 'native-headless',
        'map_ready': True, 'episode_projection': 'native_campaign', 'active_event': active,
        'played_character': {'character_id': 31254, 'alive': True, 'source': 'native', 'stress': 0},
        'diagnostics': {'bridge_pid': pid, 'connection_generation': 1, 'hello': {
            'expected_ck3_version': GAME['version'], 'expected_ck3_sha256': GAME['exe_sha256'],
            'ck3_build_match': True, 'pid': pid, 'connection_generation': 1}}}


def recommendation():
    return {'schema': 'xar.ck3.vanilla-event-registry-choice', 'status': 'recommended',
        'source': 'shared_vanilla_event_registry', 'event_definition_key': 'bookmark.1070',
        'ck3_build': GAME['version'], 'ck3_exe_sha256': GAME['exe_sha256'],
        'selected_native_option_index': 2, 'selected_option_number': 3, 'selected_rendered_index': 2,
        'semantic_decision_ready': False, 'semantic_optimal': False, 'native_ai_equivalent': False,
        'checks': {'fixture_reviewed_policy': True}, 'failed_checks': []}


class Policy:
    def __init__(self, client, *, fail_reload=False):
        self.client, self.calls, self.reloads, self.fail_reload = client, [], [], fail_reload

    def recommend(self, typed, snapshot, context):
        self.calls.append((copy.deepcopy(typed), copy.deepcopy(snapshot)))
        return recommendation(), {'actual_imported_sources': [], 'fixture_only': True}

    def reload(self, binding):
        self.reloads.append(binding)
        if self.fail_reload:
            raise ValueError('reviewed source pin rejected')


class Client:
    validate_frame = CaseClient.validate_frame

    def __init__(self, output, *, definition='bookmark.1070', answers=(), boundary_hours=6):
        self.output, self.manifest, self._binding = Path(output), {'game': GAME}, None
        self.current, self.definition = frame(), definition
        self.answers, self.boundary_hours = list(answers), boundary_hours
        self.plans, self.checkpoints, self.gaps, self.advances = [], {}, [], 0
        self.keep_instance, self.wrong_after_owner, self.next_instance = False, False, None
        self.validate_frame(self.current)

    def snapshot(self, *, require_event_free=False):
        value = self.current
        self.current = frame(value['date_raw'], value['native_revision'] + 1, copy.deepcopy(value['active_event']))
        return self.validate_frame(copy.deepcopy(self.current), require_event_free=require_event_free)

    def advance_day(self, *, days, timeout, allow_event_boundary):
        if (days, timeout, allow_event_boundary) != (1, 300, True):
            raise ValueError('Original public day opt-in differs')
        before = copy.deepcopy(self.current)
        self.advances += 1
        active = event() if self.advances == 1 else None
        hours = self.boundary_hours if active else 24
        self.current = frame(before['date_raw'] + hours, before['native_revision'] + 1, active)
        boundary = copy.deepcopy(self.current) if active else None
        if boundary:
            boundary['paused'] = False
        return {'id': 'day-' + str(self.advances), 'ok': True, 'after_snapshot': copy.deepcopy(self.current),
            'result': {'before': before, 'after': copy.deepcopy(self.current), 'event_boundary': boundary,
                'requested_days': 1, 'elapsed_hours': hours, 'requested_interval_complete': active is None,
                'selected_event_options': 0, 'event_resolution': 'typed_query_required' if active else 'none'}}

    def execute_plan(self, steps, name):
        if set(s['id'] for s in steps) & {s['id'] for p in self.plans for s in p}:
            raise ValueError('Original control ID already consumed')
        self.plans.append(copy.deepcopy(steps))
        if len(steps) != 1 or steps[0]['fresh_revision'] is not False:
            raise ValueError('Only one exact current-frame query or choice permitted')
        step = steps[0]
        instance = self.current['active_event']['instance_id']
        if step['args']['expected_revision'] != self.current['revision'] or step['args']['event_instance_id'] != instance:
            raise ValueError('Not bound to current event revision/instance')
        if step['tool'] == adapter.TOOL:
            typed = {'schema': 'current-event-window-context-v1', 'status': 'available',
                'current_event_instance_id': instance, 'date_raw': self.current['date_raw'],
                'snapshot_revision': self.current['native_revision'], 'event_definition_key': self.definition,
                'root_scope': {'status': 'available', 'typed_identity': {'character_id': 31254}},
                'provenance': {'backend_id': 'ck3-1.20.0.4-native-event-window-v1'},
                'options': [{'native_option_index': i, 'rendered_index': i, 'shown': True, 'enabled': True}
                            for i in range(3)]}
            result = {'accepted': True, 'scope': 'exact-current-event-window', 'status': 'available',
                'current_event_window_context_ready': True, 'queried_revision': self.current['revision'],
                'queried_native_revision': self.current['native_revision'], 'queried_snapshot_id': self.current['snapshot_id'],
                'current_event_window_context': typed}
        elif step['tool'] == adapter.SELECT:
            if step['args']['option_number'] != 3:
                raise ValueError('Only actual third option reviewed')
            result = {'accepted': True, 'event_instance_id': instance, 'option_index': 2, 'option_number': 3}
            self.current = frame(self.current['date_raw'], self.current['revision'] + 1,
                                 event(instance) if self.keep_instance else event(self.next_instance) if self.next_instance else None, 9999 if self.wrong_after_owner else 1234)
        else:
            raise ValueError('Unexpected action in bounded event fixture')
        row = {'id': name, 'ok': True, 'result': result, 'after_snapshot': copy.deepcopy(self.current)}
        (self.output / (name + '.actual-results.json')).write_text(json.dumps({'rows': [row]}), encoding='utf-8')
        return [row]

    def checkpoint(self, name, value):
        if name in self.checkpoints:
            raise ValueError('Checkpoint overwrite')
        self.checkpoints[name] = copy.deepcopy(value)

    def root_checkpoint(self, name, request):
        self.gaps.append((name, copy.deepcopy(request), copy.deepcopy(self.current)))
        if not self.answers:
            raise ValueError('Fixture unexpected unreviewed policy gap')
        value = self.answers.pop(0)
        if callable(value):
            value = value(self)
        return value


class ContinuationTests(unittest.TestCase):
    def context(self):
        return {'repo_root': str(options.repo_root), 'shared_game': GAME, 'product': 'li-yu-dao',
                'case': adapter.CASE, 'case_contract': adapter.contract()}

    def handle(self, client, policy=None, choices=0):
        client.current = frame(53144718, 2, event())
        return adapter.handle_event(self.context(), client, adapter.contract(), copy.deepcopy(client.current),
                                    1, choices, policy or Policy(client), elapsed=6)

    def test_partial_interval_then_choice_and_next_day_are_contiguous_once(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory)
            def observed(client, data, ordinal, **kwargs):
                return {'frame': copy.deepcopy(client.current), 'confirm_enabled': ordinal == 2}
            with patch.object(adapter, 'reopen_school', side_effect=lambda c, d, f, n: observed(c, d, n)) as reopened, \
                 patch.object(natural, 'observe_decision', side_effect=observed):
                value = adapter.observe_existing(self.context(), client, adapter.contract(), frame(), frame(), Policy(client))
            self.assertEqual(value['elapsed_natural_hours'], 30)
            self.assertEqual([r['elapsed_hours'] for r in value['natural_intervals']], [6, 24])
            self.assertEqual([r['request_ordinal'] for r in value['natural_intervals']], [1, 2])
            self.assertEqual(client.advances, 2)
            self.assertEqual(reopened.call_count, 1)
            self.assertEqual(value['event_choice_actions'], 1)
            self.assertEqual(value['status'], 'PARTIAL_EXISTING_COOLDOWN_OBSERVED')
            self.assertEqual(sum(s['tool'] == adapter.SELECT for p in client.plans for s in p), 1)

    def test_unknown_contract_holds_same_frame_then_explicit_abort_without_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory, definition='unreviewed.event', answers=[{'action': 'abort'}])
            after, value, aborted = self.handle(client)
            self.assertTrue(aborted)
            self.assertEqual(after['active_event']['instance_id'], 101)
            self.assertEqual(client.advances, 0)
            self.assertEqual(len(client.plans), 1)
            request = client.gaps[0][1]
            self.assertEqual(request['elapsed_natural_hours'], 6)
            self.assertFalse(request['advance_or_choice_replay_allowed'])
            self.assertEqual(request['school_choice_actions'], 0)

    def test_explicit_reevaluate_fresh_query_then_sole_choice_no_advance_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            def reviewed(client):
                client.definition = 'bookmark.1070'
                return {'action': 'reevaluate', 'reviewed_policy_binding': {'fixture': 'reviewed'}}
            client = Client(directory, definition='unreviewed.event', answers=[reviewed])
            policy = Policy(client)
            after, value, aborted = self.handle(client, policy)
            self.assertFalse(aborted)
            self.assertIsNone(after['active_event'])
            self.assertEqual(len(policy.reloads), 1)
            self.assertEqual([p[0]['tool'] for p in client.plans], [adapter.TOOL, adapter.TOOL, adapter.SELECT])
            self.assertEqual(len({p[0]['id'] for p in client.plans}), 3)
            self.assertEqual(client.advances, 0)
            self.assertFalse(value['army_material_credit'])

    def test_failed_reload_stays_in_gap_and_cannot_fall_back_to_old_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            def reviewed(client):
                client.definition = 'bookmark.1070'
                return {'action': 'reevaluate', 'reviewed_policy_binding': {'fixture': 'bad-pin'}}
            client = Client(directory, definition='unreviewed.event', answers=[reviewed, {'action': 'abort'}])
            policy = Policy(client, fail_reload=True)
            _, _, aborted = self.handle(client, policy)
            self.assertTrue(aborted)
            self.assertEqual(policy.calls, [])
            self.assertEqual(len(client.gaps), 2)
            self.assertTrue(all(p[0]['tool'] == adapter.TOOL for p in client.plans))

    def test_submitted_choice_old_instance_or_owner_mismatch_never_replays(self):
        for field in ('keep_instance', 'wrong_after_owner'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                client = Client(directory)
                setattr(client, field, True)
                with self.assertRaises(ValueError):
                    self.handle(client)
                self.assertEqual(sum(p[0]['tool'] == adapter.SELECT for p in client.plans), 1)
                self.assertEqual(client.gaps, [])

    def test_actual_snapshot_count_and_current_typed_identity_are_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory)
            client.current = frame(53144718, 2, event())
            packet = adapter.event_query(client, copy.deepcopy(client.current), 'fixture-query')
            adapter.qualified_context(packet, self.context())
            for change in ('count', 'instance', 'revision', 'root'):
                mutant = copy.deepcopy(packet)
                if change == 'count':
                    mutant['frame']['active_event']['option_count'] = 2
                elif change == 'instance':
                    mutant['typed_context']['current_event_instance_id'] = 102
                elif change == 'revision':
                    mutant['original_result']['queried_native_revision'] -= 1
                else:
                    mutant['typed_context']['root_scope']['typed_identity']['character_id'] = 9999
                with self.subTest(change=change), self.assertRaises(ValueError):
                    adapter.qualified_context(mutant, self.context())

    def test_boundary_owner_date_cap_and_complete_hours_remain_original_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory)
            row = client.advance_day(days=1, timeout=300, allow_event_boundary=True)
            for change in ('owner', 'date', 'cap', 'complete'):
                mutant = copy.deepcopy(row)
                if change == 'owner':
                    mutant['after_snapshot']['diagnostics']['bridge_pid'] = 9999
                elif change == 'date':
                    mutant['result']['after']['date_raw'] += 1
                elif change == 'complete':
                    mutant['result']['requested_interval_complete'] = True
                with self.subTest(change=change), self.assertRaises(ValueError):
                    adapter.boundary_interval(client, mutant, frame(), frame(), 0, 0 if change == 'cap' else 366)

    def test_consumed_event_choice_cannot_be_submitted_again(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory, answers=[{'action': 'abort'}])
            _, _, aborted = self.handle(client, choices=1)
            self.assertTrue(aborted)
            self.assertEqual([p[0]['tool'] for p in client.plans], [adapter.TOOL])

    def test_explicit_shared_main_namespace_and_reviewed_overlay_source_consumed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / 'ck3_autonomous_player/src/xar_autoplayer/vanilla_events'
            base.mkdir(parents=True)
            (base.parent / '__init__.py').write_text('')
            (base / '__init__.py').write_text('')
            (base / 'review.json').write_text('MAIN packaged resource')
            (base / 'policy.py').write_text('def recommend_registered_vanilla_event_option_v1(*args, **kwargs):\n return {"origin":"MAIN"}\n')
            overlay = root / 'reviewed/xar_autoplayer/vanilla_events'
            overlay.mkdir(parents=True)
            path = overlay / 'policy.py'
            path.write_text('from importlib import resources\ndef recommend_registered_vanilla_event_option_v1(*args, **kwargs):\n return {"origin":"reviewed", "resource":resources.files(__package__).joinpath("review.json").read_text()}\n')
            policy = adapter.ReviewedPolicy({'repo_root': str(root)})
            native = frame(active=event())
            result, proof = policy.recommend({}, native, self.context())
            self.assertEqual(result['origin'], 'MAIN')
            self.assertFalse(proof['installed_or_Csr_policy_import_used'])
            binding = {'root': str(overlay.parent), 'files': [adapter._pin_python(path)]}
            policy.reload(binding)
            result, proof = policy.recommend({}, native, self.context())
            self.assertEqual(result['origin'], 'reviewed')
            self.assertEqual(result['resource'], 'MAIN packaged resource')
            self.assertIn(binding['files'][0], proof['actual_imported_sources'])
            bad = copy.deepcopy(binding)
            bad['files'][0]['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                policy.reload(bad)


    def test_new_instance_after_sole_choice_reaches_hold_with_unique_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client(directory, answers=[{'action': 'abort'}])
            client.next_instance = 102
            value = adapter.observe_existing(self.context(), client, adapter.contract(), frame(), frame(), Policy(client))
            self.assertEqual(value['status'], 'PARTIAL_POLICY_GAP_PRESERVED')
            self.assertEqual(value['event_choice_actions'], 1)
            self.assertEqual(value['elapsed_natural_hours'], 6)
            self.assertEqual(client.advances, 1)
            ids = [step['id'] for plan in client.plans for step in plan]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual([p[0]['tool'] for p in client.plans], [adapter.TOOL, adapter.SELECT, adapter.TOOL])
            self.assertIn('-instance-101-', ids[0])
            self.assertIn('-instance-102-', ids[-1])
            self.assertEqual(len(client.gaps), 1)
            self.assertEqual(client.gaps[0][2]['active_event']['instance_id'], 102)
            self.assertEqual(client.gaps[0][1]['event_choice_actions'], 1)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
