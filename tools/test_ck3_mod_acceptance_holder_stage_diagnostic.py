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
STARTUP_R48 = json.loads('{"schema":"lyd.r48.actual-startup-proof-offline-input.v1","source_report":{"path":"C:\\\\workspace\\\\ck3-common-runtime\\\\runs\\\\bf-202609141645-5434332d4d--li-yu-dao--R0048\\\\native-report.json","bytes":523643,"sha256":"c57d2b6e13cd928c7bc16b8419f43640012bc2ce0c8906406000206145d9f12a"},"source_record_path":"$.saved_campaign_restore.startup_case","source_snapshot_path":"$.saved_campaign_restore.startup_case.snapshot","source_event_packet_path":"$.saved_campaign_restore.startup_case.event_context","original_error":"ValueError: saved startup pure proof did not bind the exact declared event identities","selection_attempted":false,"snapshot":{"snapshot_id":"native:1","revision":2,"native_revision":1,"date_raw":53144712,"played_character":{"character_id":31254,"alive":true,"source":"native","stress_points":0,"event_trait_membership":{"schema":"xar.ck3.player-event-trait-membership/v1","game_version":"1.20.0.4","executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518","status":"available","snapshot_revision":1,"date_raw":53144712,"played_character_id":31254,"traits":{"lifestyle_poet":false,"journaller":false},"unavailable_reason":null},"betrothed_id":null,"primary_spouse_id":36311,"spouse_ids":[36311]},"active_event":{"source":"native","instance_id":121,"option_count":1,"title":null,"options":[{"index":0,"option_number":1,"label":null,"enabled":true}]},"paused":true,"map_ready":true,"episode_projection":"native_campaign","local_player_id":1},"event_packet":{"step":"query-current-event-window-context-v1","accepted":true,"status":"available","query_sequence":1,"snapshot_revision":1,"current_event_window_context":{"schema":"current-event-window-context-v1","schema_version":1,"status":"available","snapshot_revision":1,"date_raw":53144712,"current_event_instance_id":121,"window_match_count":1,"unavailable_reason":null,"event_definition_key":"lyd_factory_diag.20","calculated_event_id":1460020,"runtime_stats_ordinal":1185,"root_scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"available","kind":"character","character_id":31254}},"saved_scopes":[{"name":"puppeteer","name_identifier":228,"scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"unavailable","reason":"character_scope_is_null"}}},{"name":"lyd_i3b_actor","name_identifier":12670,"scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"available","kind":"character","character_id":31254}}},{"name":"lyd_i3b_event_serial","name_identifier":12728,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"300000","scale":100000,"decimal_value":"3","integer_value":"3"}}},{"name":"lyd_i3b_event_nonce","name_identifier":43395,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"600000","scale":100000,"decimal_value":"6","integer_value":"6"}}},{"name":"lyd_i3b_event_phase","name_identifier":43396,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"200000","scale":100000,"decimal_value":"2","integer_value":"2"}}},{"name":"lyd_i3b_signature_actor","name_identifier":47481,"scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"available","kind":"character","character_id":31254}}},{"name":"lyd_c3_factory_had_same_faith_law","name_identifier":47245,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"100000","scale":100000,"decimal_value":"1","integer_value":"1"}}},{"name":"my_faith","name_identifier":47114,"scope":{"status":"available","raw_type_index":13,"type_key":"faith","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"}}},{"name":"lyd_c3_factory_faith","name_identifier":43581,"scope":{"status":"available","raw_type_index":13,"type_key":"faith","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"}}},{"name":"lyd_factory_diag_stage","name_identifier":43582,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"2000000","scale":100000,"decimal_value":"20","integer_value":"20"}}},{"name":"new_title","name_identifier":70,"scope":{"status":"available","raw_type_index":5,"type_key":"landed_title","subtype":0,"typed_identity":{"status":"available","kind":"landed_title","title_id":18373}}}],"options":[{"rendered_index":0,"native_option_index":0,"shown":true,"enabled":true,"fallback":false,"cancel":false,"resolved_name":"仅推进下一个诊断边界","unavailable_reason":"","effect_indicators":{"status":"available","coverage":"played-character-event-icon-indicators-1.20.0.4-v1","complete_effect_set":false,"rows":[]},"effect_preview":{"status":"unavailable","reason":"indicator_subset_has_no_completeness_signal"},"resource_deltas":{"status":"unavailable"},"relationship_deltas":{"status":"unavailable"}}],"readiness":{"event_definition_identity_ready":true,"root_scope_ready":true,"saved_scopes_ready":true,"option_presentation_ready":true,"effect_indicators_ready":true,"effect_preview_ready":false,"semantic_decision_ready":false},"provenance":{"root":"module+0x5C6A520->+0x10","idler_vtable_rva":"0x44BC418","manager_offset":"+0x28","backend_id":"ck3-1.20.0.4-native-event-window-v1"}},"backend_id":"native-headless","schema":"current-event-window-context-v1","schema_version":1,"date_raw":53144712,"current_event_instance_id":121,"window_match_count":1,"unavailable_reason":null,"event_definition_key":"lyd_factory_diag.20","calculated_event_id":1460020,"runtime_stats_ordinal":1185,"root_scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"available","kind":"character","character_id":31254}},"saved_scopes":[{"name":"puppeteer","name_identifier":228,"scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"unavailable","reason":"character_scope_is_null"}}},{"name":"lyd_i3b_actor","name_identifier":12670,"scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"available","kind":"character","character_id":31254}}},{"name":"lyd_i3b_event_serial","name_identifier":12728,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"300000","scale":100000,"decimal_value":"3","integer_value":"3"}}},{"name":"lyd_i3b_event_nonce","name_identifier":43395,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"600000","scale":100000,"decimal_value":"6","integer_value":"6"}}},{"name":"lyd_i3b_event_phase","name_identifier":43396,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"200000","scale":100000,"decimal_value":"2","integer_value":"2"}}},{"name":"lyd_i3b_signature_actor","name_identifier":47481,"scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,"typed_identity":{"status":"available","kind":"character","character_id":31254}}},{"name":"lyd_c3_factory_had_same_faith_law","name_identifier":47245,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"100000","scale":100000,"decimal_value":"1","integer_value":"1"}}},{"name":"my_faith","name_identifier":47114,"scope":{"status":"available","raw_type_index":13,"type_key":"faith","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"}}},{"name":"lyd_c3_factory_faith","name_identifier":43581,"scope":{"status":"available","raw_type_index":13,"type_key":"faith","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"}}},{"name":"lyd_factory_diag_stage","name_identifier":43582,"scope":{"status":"available","raw_type_index":1,"type_key":"value","subtype":0,"typed_identity":{"status":"unavailable","reason":"generic_scope_payload_identity_not_closed"},"numeric_value":{"raw_fixed_point":"2000000","scale":100000,"decimal_value":"20","integer_value":"20"}}},{"name":"new_title","name_identifier":70,"scope":{"status":"available","raw_type_index":5,"type_key":"landed_title","subtype":0,"typed_identity":{"status":"available","kind":"landed_title","title_id":18373}}}],"options":[{"rendered_index":0,"native_option_index":0,"shown":true,"enabled":true,"fallback":false,"cancel":false,"resolved_name":"仅推进下一个诊断边界","unavailable_reason":"","effect_indicators":{"status":"available","coverage":"played-character-event-icon-indicators-1.20.0.4-v1","complete_effect_set":false,"rows":[]},"effect_preview":{"status":"unavailable","reason":"indicator_subset_has_no_completeness_signal"},"resource_deltas":{"status":"unavailable"},"relationship_deltas":{"status":"unavailable"}}],"readiness":{"event_definition_identity_ready":true,"root_scope_ready":true,"saved_scopes_ready":true,"option_presentation_ready":true,"effect_indicators_ready":true,"effect_preview_ready":false,"semantic_decision_ready":false},"provenance":{"root":"module+0x5C6A520->+0x10","idler_vtable_rva":"0x44BC418","manager_offset":"+0x28","backend_id":"ck3-1.20.0.4-native-event-window-v1"},"current_event_window_context_ready":true,"current_event_effect_indicators_ready":true,"queried_snapshot_id":"native:1","queried_revision":2,"queried_native_revision":1,"scope":"exact-current-event-window","source":{"snapshot_id":"native:1","revision":2,"native_revision":1,"date_raw":53144712,"paused":true,"backend_id":"native-headless"},"binding":{"snapshot_id":"native:1","revision":2,"native_revision":1,"date_raw":53144712,"expected_revision":2,"event_instance_id":121}},"original_adapter_sha256":"7970717d37897b9287073fb836ff0333535e8677625591c481188cee1e75a912","actual_source09_host":{"path":"C:\\\\csr9\\\\ck3_autonomous_player\\\\native_bridge\\\\research\\\\run_ck3_12002_mcp_live.py","bytes":244512,"sha256":"a9895e966590d669bbef3f625c808b95dea1e4fca4561fe5bc0be1b647178b33"},"offline_fixture_is_not_a_new_runtime_or_business_qualification":true}')


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


    def _source09_startup_helpers(self):
        # Compile the complete actual host validation functions, with no SDK import.
        import ast
        import copy
        import hashlib
        source = Path(os.environ.get('XAR_CK3_STARTUP_HOST_SOURCE',
            REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'))
        names = {'verify_fixture_startup_case_contract',
                 'verify_saved_campaign_startup_case_contract', 'fixture_startup_case_proof'}
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        namespace = {'Path': Path, 'json': json, 'hashlib': hashlib, 'sys': sys, 'copy': copy}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
        return namespace

    def _pinned_startup_contract(self, module_path, state_dir):
        import hashlib
        def pin(path):
            raw = path.read_bytes()
            return {'path': str(path.resolve()), 'bytes': len(raw),
                    'sha256': hashlib.sha256(raw).hexdigest()}
        return {'schema': 'ck3-saved-campaign-startup-case-contract-v1',
                'state_dir': str(Path(state_dir).resolve()),
                'handler': {**pin(module_path), 'function': 'admit_saved_startup_event'},
                'dependencies': [pin(module_path.with_name('lyd_holder_stage_diagnostic.json')),
                                 pin(Path(adapter.base.__file__))], 'expected': DATA['expected']}

    def test_startup_proof_passes_actual_host_validation_with_r48_packet(self):
        helper = self._source09_startup_helpers()['fixture_startup_case_proof']
        with tempfile.TemporaryDirectory() as directory:
            contract = self._pinned_startup_contract(MODULE, directory)
            proof = helper(contract, STARTUP_R48['snapshot'], STARTUP_R48['event_packet'],
                           Path(directory), saved_campaign=True)
        self.assertEqual(set(proof), {*DATA['expected'], 'proof', 'business_pass'})
        self.assertEqual(proof['proof']['baseline_saved_campaign'], DATA['saved_campaign'])
        self.assertEqual(proof['proof']['production_source_head'], DATA['production_source_head'])
        self.assertEqual(proof['proof']['actions_submitted'], 0)
        self.assertFalse(proof['business_pass'])

    def test_actual_host_rejects_original_r48_outer_provenance_key(self):
        import hashlib
        helper = self._source09_startup_helpers()['fixture_startup_case_proof']
        fixed = "    proof['baseline_saved_campaign'] = data['saved_campaign']\n    proof['production_source_head'] = data['production_source_head']\n    return {**context['expected'], 'proof': proof, 'business_pass': False}\n"
        original = "    return {**context['expected'], 'proof': proof, 'business_pass': False,\n            'baseline_saved_campaign': data['saved_campaign']}\n"
        source = MODULE.read_text(encoding='utf-8')
        self.assertEqual(source.count(fixed), 1)
        source = source.replace(fixed, original)
        self.assertEqual(hashlib.sha256(source.encode('utf-8')).hexdigest(),
                         STARTUP_R48['original_adapter_sha256'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / MODULE.name
            path.write_text(source, encoding='utf-8', newline='\n')
            path.with_name('lyd_holder_stage_diagnostic.json').write_bytes(
                MODULE.with_name('lyd_holder_stage_diagnostic.json').read_bytes())
            contract = self._pinned_startup_contract(path, directory)
            with self.assertRaisesRegex(ValueError,
                    'saved startup pure proof did not bind the exact declared event identities'):
                helper(contract, STARTUP_R48['snapshot'], STARTUP_R48['event_packet'],
                       Path(directory), saved_campaign=True)


if __name__ == '__main__':
    unittest.main()
