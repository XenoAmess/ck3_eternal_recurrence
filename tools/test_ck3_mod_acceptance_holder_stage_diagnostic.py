"""Offline seams for the new holder diagnostic; no SDK, prepare or save body."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(os.environ.get('XAR_CK3_REPO_ROOT', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(REPO / 'tools'))
MODULE = Path(__file__).with_name('ck3_mod_acceptance_cases') / 'lyd_holder_stage_diagnostic_adapter.py'
spec = importlib.util.spec_from_file_location('holder_stage_diagnostic_test_subject', MODULE)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
DATA = adapter.contract()


def frame(revision):
    return {'snapshot_id': 'native:' + str(revision), 'revision': revision, 'native_revision': revision,
            'date_raw': DATA['expected']['date_raw'], 'diagnostics': {'bridge_pid': 123, 'connection_generation': 1}}


def cache(ids, current):
    actor = DATA['expected']['actor_character_id']
    return {'queried_snapshot_id': current['snapshot_id'], 'queried_revision': current['revision'],
        'queried_native_revision': current['native_revision'], 'date_raw': current['date_raw'],
        'game_pid': 123, 'connection_generation': 1, 'player_character_id': actor,
        'native_result': {'actor_cached_succession': {'available': True, 'read_only': True, 'roster_complete': True,
            'native_count': len(ids), 'complete_cached_successor_ids': ids, 'played_character_id': actor,
            'played_character_full_id': actor, 'date_raw': current['date_raw']}}}


class FakeClient:
    def __init__(self, after_ids):
        self.before, self.after, self.after_ids = frame(1), frame(2), after_ids
        self.calls, self.checkpoints = [], {}

    def retain_process(self):
        pass

    def snapshot(self, **kwargs):
        return self.before

    def checkpoint(self, name, value):
        self.checkpoints[name] = value

    def execute_plan(self, steps, name, timeout):
        tool, args = steps[0]['tool'], steps[0]['args']
        self.calls.append(tool)
        if tool == 'ck3_query_current_event_window_context_v1':
            result = {}
        elif tool == 'ck3_query_actor_cached_succession_v1':
            current = self.before if args['expected_revision'] == 1 else self.after
            result = cache(DATA['baseline_cached_succession'] if current is self.before else self.after_ids, current)
        elif tool == 'ck3_select_event_option':
            result = {'accepted': True, 'event_instance_id': 121, 'option_number': 1, 'option_index': 0}
        elif tool == 'ck3_save_checkpoint':
            result = {'accepted': True, 'step': 'save-checkpoint', 'checkpoint': {'test_only': True}}
        else:
            raise AssertionError('Unexpected offline fake tool: ' + tool)
        return [{'ok': True, 'result': result}]


class HolderDiagnosticTests(unittest.TestCase):
    def test_changed_complete_cache_reaches_the_single_save(self):
        after_ids = DATA['baseline_cached_succession'][:40]
        client = FakeClient(after_ids)
        context = {'product': 'li-yu-dao', 'case': 'holder-stage-diagnostic', 'case_contract': DATA,
                   'run_id': 'offline-unit', 'repo_root': str(REPO), 'state_dir': 'not-read'}
        def saved(*args):
            self.assertEqual(client.calls.count('ck3_save_checkpoint'), 1)
            return {'complete_cached_successor_ids': after_ids, 'save_body_reads': 1, 'baseline_body_reads': 0,
                    'political_titles': {key: {} for key in DATA['political_title_ast_sha256']},
                    'diagnostic_observation_only': True}
        with mock.patch.object(adapter, 'admit_saved_startup_event', return_value={}), \
             mock.patch.object(adapter.base, 'observe_terminal', return_value=(client.after, 122)), \
             mock.patch.object(adapter.base, 'observe_event', return_value={}), \
             mock.patch.object(adapter, 'log_offsets', return_value={}), \
             mock.patch.object(adapter, 'stage_log_windows', return_value=[]), \
             mock.patch.object(adapter, 'read_saved_diagnostic', side_effect=saved):
            facts = adapter.run_case(context, client)
        self.assertEqual(client.calls.count('ck3_select_event_option'), 1)
        self.assertEqual(client.calls.count('ck3_save_checkpoint'), 1)
        self.assertTrue(facts['cache_changed'])
        self.assertEqual(len(facts['cache_after_ids']), 40)
        self.assertFalse(facts['business_pass'])
        self.assertIsNone(facts['formal_institution_pass'])

    def test_after_cache_rejects_a_stale_frame(self):
        current = frame(2)
        packet = cache(DATA['baseline_cached_succession'][:40], current)
        packet['queried_native_revision'] = 1
        with self.assertRaisesRegex(ValueError, 'frame differs'):
            adapter.observe_cache_after(current, packet, DATA)

    def test_after_cache_still_requires_a_complete_collection(self):
        current = frame(2)
        packet = cache(DATA['baseline_cached_succession'][:40], current)
        packet['native_result']['actor_cached_succession']['native_count'] = 45
        with self.assertRaisesRegex(ValueError, 'Complete ordered'):
            adapter.observe_cache_after(current, packet, DATA)

    def test_saved_changed_AST_and_absent_control_marker_are_observations(self):
        reader = adapter.base._reader(REPO)
        ids = DATA['baseline_cached_succession'][:40]
        actor = {'character_id': 31254, 'variables': {},
                 'landed_data': [{'key': 'succession', 'value': [{'key': None, 'value': str(value)} for value in ids]}]}
        titles = {}
        for title in [int(key) for key in DATA['political_title_ast_sha256']] + [DATA['new_title_id']]:
            entries = [{'key': 'holder', 'value': '31254'}, {'key': 'offline_test_only', 'value': str(title)}]
            titles[title] = {'holder': 31254, 'entries': entries, 'AST_sha256': reader.ast_sha(entries)}
        facts = adapter.evaluate_saved_diagnostic(reader, actor, titles, DATA)
        self.assertIsNone(facts['control_completed_value_observed'])
        self.assertFalse(facts['political_full_AST_equal'])
        self.assertEqual(len(facts['political_titles']), 7)
        self.assertTrue(all(row['after_AST'] for row in facts['political_titles'].values()))
        self.assertEqual(facts['complete_cached_successor_ids'], ids)
        self.assertFalse(facts['business_pass'])

    def test_verification_never_promotes_diagnostic_to_product_success(self):
        with tempfile.TemporaryDirectory() as directory:
            facts = {'run_id': 'unit', 'product': 'li-yu-dao', 'case': 'holder-stage-diagnostic',
                'diagnostic_capture_complete': True, 'business_actions_submitted': 1, 'selected_option_number': 1,
                'stopped_at_definition': 'lyd_factory_diag.2', 'cache_before_ids': DATA['baseline_cached_succession'],
                'saved': {'save_body_reads': 1, 'baseline_body_reads': 0, 'diagnostic_observation_only': True,
                          'political_titles': {key: {} for key in DATA['political_title_ast_sha256']}},
                'business_pass': True, 'product_release_pass': True, 'formal_institution_pass': True}
            (Path(directory) / 'holder-stage-diagnostic-case-result.json').write_text(json.dumps(facts), encoding='utf-8')
            result = adapter.verify_case({'run_id': 'unit', 'product': 'li-yu-dao', 'case': 'holder-stage-diagnostic',
                'case_contract': DATA, 'output': directory})
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['product_release_pass'])
        self.assertIsNone(result['formal_institution_pass'])


if __name__ == '__main__':
    unittest.main()
