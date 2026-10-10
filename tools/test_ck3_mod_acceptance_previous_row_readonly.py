"""Pure fixtures exercise actual candidate queue/host/adapter entries; no live I/O."""
import argparse
import ast
import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from jsonschema.exceptions import ValidationError

_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument('--repository-root', type=Path, default=Path(__file__).resolve().parents[1])
_parser.add_argument('--candidate-author', type=Path)
_options, _unittest_args = _parser.parse_known_args()
REPO = _options.repository_root.resolve()
AUTHOR = _options.candidate_author.resolve() if _options.candidate_author else None
HOST = 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
QUEUE = 'tools/ck3_mod_acceptance_queue.py'
ADAPTER = 'tools/ck3_mod_acceptance_cases/lyd_i4_natural_expiry_adapter.py'
QUERY = 'ck3_query_ingame_decision_item_v1'
TREE = 'ck3_inspect_gui_window_tree_v1'
sys.path.insert(0, str(REPO / 'tools'))
from test_ck3_mod_acceptance_i4_batch_002 import Client, model


def require(condition, message):
    if not condition:
        raise ValueError(message)


def actual_namespaces():
    if AUTHOR is None:
        # Installed repo entry exercises its actual source, without external B dependencies.
        changes = {rel: {'after_text': (REPO / rel).read_text(encoding='utf-8-sig')}
                   for rel in (HOST, QUEUE, ADAPTER)}
    else:
        spec = importlib.util.spec_from_file_location('readonly_candidate_author', AUTHOR)
        author = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(author)
        require(author.ROOT.resolve() == REPO, 'Candidate author and actual dependency repo differ')
        changes = author.transformations()
        expected = json.loads((AUTHOR.parent / 'TARGETS.json').read_text(encoding='utf-8'))
        for row in expected['targets']:
            for side in ('before', 'after'):
                raw = changes[row['target']][side]
                require(len(raw) == row[side]['bytes'] and hashlib.sha256(raw).hexdigest() == row[side]['sha256'],
                        'Exact reviewed candidate source pin changed')
    queue_tree = ast.parse(changes[QUEUE]['after_text'])
    queue_body = [n for n in queue_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_steps']
    q = {'require': require, 'json': json, 'copy': copy, 're': re}
    exec(compile(ast.Module(body=queue_body, type_ignores=[]), QUEUE, 'exec'), q)
    host_tree = ast.parse(changes[HOST]['after_text'])
    host_body = [n for n in host_tree.body if isinstance(n, ast.FunctionDef) and n.name in {'lookup', 'resolve'}]
    client_node = next(n for n in host_tree.body if isinstance(n, ast.ClassDef) and n.name == 'PlanClient')
    methods = [n for n in client_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in {'execute', 'invoke', 'bind_previous_revision_arguments'}]
    host_body.append(ast.ClassDef(name='PlanClient', bases=[], keywords=[], decorator_list=[], body=methods))
    h = {'json': json, 'copy': copy, 'now': lambda: 'SYNTHETIC-completed', 'asyncio': asyncio}
    exec(compile(ast.fix_missing_locations(ast.Module(body=host_body, type_ignores=[])), HOST, 'exec'), h)
    a = {'__file__': str(REPO / ADAPTER), '__name__': 'candidate_i4_readonly_adapter'}
    exec(compile(changes[ADAPTER]['after_text'], ADAPTER, 'exec'), a)
    return q, h, a


class PreviousRowReadonly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q, cls.h, cls.a = actual_namespaces()

    def schemas(self):
        query = {'type': 'object', 'properties': {'decision_key': {'type': 'string', 'minLength': 1},
            'expected_revision': {'type': 'integer', 'minimum': 1}},
            'required': ['decision_key', 'expected_revision'], 'additionalProperties': False}
        tree = {'type': 'object', 'properties': {'window_kind': {'const': 'decision_detail'}},
            'required': ['window_kind'], 'additionalProperties': False}
        return {QUERY: {'inputSchema': query}, TREE: {'inputSchema': tree},
            'ck3_select_ingame_decision_item_v1': {'inputSchema': copy.deepcopy(query)}}

    def steps(self):
        return [{'id': 'before', 'tool': QUERY, 'args': {'decision_key': 'school', 'expected_revision': 5}, 'fresh_revision': False},
            {'id': 'tree', 'tool': TREE, 'args': {'window_kind': 'decision_detail'}, 'fresh_revision': False},
            {'id': 'after', 'tool': QUERY, 'args': {'decision_key': 'school'}, 'fresh_revision': False, 'bind_previous_revision': True}]

    def report(self):
        return {'steps': [], 'mcp_tools': {'tools': [{'name': k, **v} for k, v in self.schemas().items()]}}

    def host(self, revisions=(11, 37, 41)):
        c = self.h['PlanClient'].__new__(self.h['PlanClient'])
        c.report = self.report(); c.tools = self.schemas(); c.results = {}; c.snapshot = {'revision': 5}
        c.args = SimpleNamespace(frontend_mod_load_observation=False); c.episode_identity = None
        c.write = lambda: None; c.calls = []; c.fresh_calls = 0
        values = iter(revisions)
        async def call(name, arguments):
            c.calls.append((name, copy.deepcopy(arguments)))
            c.snapshot = {'revision': 999999}  # Must not become the binding source.
            return {'read_only': True, 'queried_arguments': copy.deepcopy(arguments)}
        async def fresh():
            c.fresh_calls += 1; c.snapshot = {'revision': next(values)}
            return copy.deepcopy(c.snapshot)
        c.call = call; c.fresh = fresh
        return c

    def adapter_client(self):
        data = self.a['contract']()
        c = Client(data['decision_key'])
        c.execute_plan = lambda steps, name: (c.plans.append((copy.deepcopy(steps), name)) or copy.deepcopy(c.rows))
        return c, data

    def test_actual_host_execute_binds_adjacent_completed_after_frame_without_fresh(self):
        c = self.host(); asyncio.run(c.execute(self.steps()))
        self.assertEqual(c.calls[-1][1]['expected_revision'], 37)
        self.assertEqual(c.fresh_calls, 3)
        self.assertEqual(c.report['steps'][2]['previous_revision_binding']['source_step_id'], 'tree')
        self.assertEqual(c.report['steps'][1]['after_snapshot']['revision'], 37)
        self.assertNotIn('after_snapshot', c.results['tree'])

    def test_actual_host_first_or_cross_plan_row_rejects_before_call(self):
        c = self.host(); asyncio.run(c.execute(self.steps()[:2])); before = len(c.calls)
        with self.assertRaisesRegex(ValueError, 'completed predecessor'):
            asyncio.run(c.execute([self.steps()[2]]))
        self.assertEqual(len(c.calls), before)
        self.assertIs(c.report['steps'][-1]['ok'], False)

    def test_actual_host_default_legacy_explicit_revision_remains_unchanged(self):
        c = self.host(); steps = self.steps(); steps[2].pop('bind_previous_revision')
        steps[2]['args']['expected_revision'] = 123
        asyncio.run(c.execute(steps))
        self.assertEqual(c.calls[-1][1]['expected_revision'], 123)
        self.assertNotIn('previous_revision_binding', c.report['steps'][-1])

    def test_actual_host_foreign_unfinished_failed_or_invalid_revision_rejects(self):
        for defect in ('foreign', 'unfinished', 'failed', 'absent', 'zero', 'bool', 'overflow'):
            c = self.host(); row = {'id': 'prior', 'ok': True, 'finished_at': 'done', 'after_snapshot': {'revision': 37}}
            c.report['steps'].append(row)
            if defect == 'foreign': c.report['steps'].clear()
            elif defect == 'unfinished': row.pop('finished_at')
            elif defect == 'failed': row.update(ok=False, error='ORIGINAL-FAILURE')
            else: row['after_snapshot']['revision'] = {'absent': None, 'zero': 0, 'bool': True, 'overflow': 2**64}[defect]
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                c.bind_previous_revision_arguments(QUERY, {'decision_key': 'school'}, [row])

    def test_actual_host_disallows_nonreadonly_mixed_references_fresh_or_menu(self):
        for defect in ('write', 'schema', 'explicit', 'reference', 'fresh', 'bool', 'menu'):
            c = self.host(); steps = self.steps()
            if defect == 'write': steps[2]['tool'] = 'ck3_select_ingame_decision_item_v1'
            elif defect == 'schema': c.tools[QUERY]['inputSchema']['properties'].pop('expected_revision')
            elif defect == 'explicit': steps[2]['args']['expected_revision'] = 37
            elif defect == 'reference': steps[2]['args']['decision_key'] = {'$ref': 'results.tree'}
            elif defect == 'fresh': steps[2]['fresh_revision'] = True
            elif defect == 'bool': steps[2]['bind_previous_revision'] = 1
            else: c.args.frontend_mod_load_observation = True; steps = [steps[2]]
            with self.subTest(defect=defect), self.assertRaises(ValueError): asyncio.run(c.execute(steps))
            self.assertLessEqual(len(c.calls), 2)

    def test_actual_queue_schema_only_exempts_expected_revision_for_optin(self):
        self.assertEqual(self.q['validate_steps'](self.steps(), self.report()), ['before', 'tree', 'after'])
        for defect in ('legacy', 'missing-key', 'extra', 'key-type'):
            steps = self.steps()
            if defect == 'legacy': steps[2].pop('bind_previous_revision')
            elif defect == 'missing-key': steps[2]['args'].pop('decision_key')
            elif defect == 'extra': steps[2]['args']['extra'] = True
            else: steps[2]['args']['decision_key'] = 12
            with self.subTest(defect=defect), self.assertRaises((ValueError, ValidationError)): self.q['validate_steps'](steps, self.report())

    def test_actual_queue_rejects_first_write_fresh_explicit_symbolic_and_nonbool(self):
        for defect in ('first', 'write', 'fresh', 'explicit', 'symbolic', 'nonbool', 'advance'):
            steps = self.steps()
            if defect == 'first': steps = [steps[2]]
            elif defect == 'write': steps[2]['tool'] = 'ck3_select_ingame_decision_item_v1'
            elif defect == 'fresh': steps[2]['fresh_revision'] = True
            elif defect == 'explicit': steps[2]['args']['expected_revision'] = 37
            elif defect == 'symbolic': steps[2]['args']['decision_key'] = '$revision'
            elif defect == 'nonbool': steps[2]['bind_previous_revision'] = 0
            else: steps[2] = {'id': 'advance', 'kind': 'advance_day', 'days': 1, 'bind_previous_revision': True}
            with self.subTest(defect=defect), self.assertRaises((ValueError, ValidationError)): self.q['validate_steps'](steps, self.report())

    def test_adapter_three_readonly_rows_keep_both_native_model_anchors(self):
        c, data = self.adapter_client(); after = c.rows[1]['after_snapshot']; after.update(revision=20, native_revision=19)
        c.rows[2]['result'] = model(after, data['decision_key']); c.rows[2]['after_snapshot'] = copy.deepcopy(after)
        result = self.a['observe_decision'](c, data, 7)
        self.assertEqual([len(p[0]) for p in c.plans], [3]); self.assertEqual(c.snapshot_calls, 1)
        final = c.plans[0][0][2]
        self.assertIs(final['bind_previous_revision'], True); self.assertIs(final['fresh_revision'], False)
        self.assertNotIn('expected_revision', final['args']); self.assertEqual(result['model_after']['native_revision'], 19)
        self.assertFalse(result['decision_executed']); self.assertEqual(len(c.checkpoints), 1)

    def test_adapter_retains_model_tree_and_all_after_frame_refusals(self):
        for defect in ('before-native', 'final-native', 'tree', 'reorder', 'missing-after', 'pid', 'generation', 'actor', 'date', 'paused', 'event'):
            c, data = self.adapter_client()
            if defect == 'before-native': c.rows[0]['result']['native_revision'] += 1
            elif defect == 'final-native': c.rows[2]['result']['native_revision'] += 1
            elif defect == 'tree': c.rows[1]['result']['truncated'] = True
            elif defect == 'reorder': c.rows[0]['id'], c.rows[1]['id'] = c.rows[1]['id'], c.rows[0]['id']
            elif defect == 'missing-after': c.rows[2].pop('after_snapshot')
            else:
                v = c.rows[2]['after_snapshot']
                if defect == 'pid': v['diagnostics']['bridge_pid'] += 1
                elif defect == 'generation': v['diagnostics']['connection_generation'] += 1
                elif defect == 'actor': v['played_character']['character_id'] += 1
                elif defect == 'date': v['date_raw'] += 1
                elif defect == 'paused': v['paused'] = False
                else: v['active_event'] = {'unexpected': True}
            with self.subTest(defect=defect), self.assertRaises((ValueError, KeyError)): self.a['observe_decision'](c, data, 7)
            self.assertEqual(c.checkpoints, []); self.assertEqual(len(c.plans), 1)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *_unittest_args])
