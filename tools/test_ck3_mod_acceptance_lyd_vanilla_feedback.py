"""Portable offline case-contract tests. Synthetic observations are not CK3 credit."""
from __future__ import annotations

import ast
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = next((p for p in HERE.parents if (p / 'AGENTS.md').is_file()), None)
# External review uses only these candidate modules plus actual repository helpers.
# Once adopted, all files resolve directly in the repository.
if REPO is None:
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--repo', type=Path, required=True)
    if __name__ == '__main__':
        args, remaining = parser.parse_known_args()
        REPO = args.repo.resolve()
        sys.argv = [sys.argv[0], *remaining]
    else:
        raise ImportError('External candidate needs explicit --repo; repository import is portable')
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(HERE))
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.insert(0, str(HERE / 'ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import lyd_vanilla_feedback_adapter as case
import prepare_lyd_vanilla_feedback_fixture as producer


def frame(revision=8):
    return {'revision': revision, 'native_revision': 7, 'date_raw': 53144712, 'paused': True,
        'active_event': None, 'played_character': {'character_id': 29829, 'alive': True},
        'diagnostics': {'bridge_pid': 4321, 'connection_generation': 1}}


class Client:
    operator_reviewer = '/root'

    def __init__(self, evidence, *, bad=None, soft_failure=None):
        self.evidence, self.bad, self.soft_failure = evidence, bad, soft_failure
        self.steps, self.reviews = [], []
        self.current = frame()

    def snapshot(self, **kwargs):
        return copy.deepcopy(self.current)

    def execute_plan(self, steps, name):
        self.steps.extend(copy.deepcopy(steps))
        step = steps[0]
        key = step['args'].get('decision_key')
        tool = step['tool']
        if 'query_ingame' in tool:
            model = {'schema': 'ck3-ingame-decision-item-v1', 'read_only': True, 'available': True,
                'decision_key': 'wrong' if self.bad == 'target' else key,
                'game_pid': 4321, 'connection_generation': 1, 'played_character_id': 29829,
                'date_raw': 53144712, 'native_revision': 7}
            model.update({k: True for k in ('owner_thread_verified', 'frame_verified',
                'source_abi_pins_verified', 'gui_owner_binding_verified', 'decisions_tree_complete',
                'decisions_root_visible', 'row_owner_verified')})
        elif 'select_ingame' in tool:
            model = {'schema': 'ck3-ingame-decision-item-action-v1', 'decision_key': key,
                'action': 'select', 'status': 'acknowledged_verification_pending',
                'postcondition_verified': False, 'verification_pending': True}
        else:
            model = {'accepted': True}
        return [{'id': step['id'], 'ok': True, 'result': model}]

    def root_checkpoint(self, name, request, reserve=420):
        if reserve != 420:
            raise ValueError('Seven-minute normal exit reserve required')
        phase = request['phase']
        self.reviews.append(phase)
        facts = {key: True for key in request['requirements']}
        if self.bad == 'faith':
            facts['faith_identity_preserved'] = False
        if self.bad == 'head' and phase == 'baseline':
            facts['no_head_of_faith_observed'] = False
        expected = case.MODIFIERS.get(phase, {})
        source = 'lyd_tenet_investigate_principle' if phase == 'school' else 'lyd_tenet_reverent_heaven'
        values = {k: {'value': v, 'source_tenet_key': source, 'effective_on_actor': True,
                      'evidence_kind': 'actual_actor_modifier_breakdown'} for k, v in expected.items()}
        if phase == self.soft_failure:
            values = None
            facts['core_T14_effective_actor_modifier_observed' if phase == 'school' else
                  'personal_T01_effective_actor_modifier_observed'] = False
        return {'status': 'complete', 'run_id': 'SYNTHETIC-RUN', 'reviewer': '/root',
            'facts': facts, 'before_native_binding': request['before_native_binding'],
            'actor_character_id': 29829, 'faith_key': 'confucian_faith',
            'rite_key': request['expected_rite_key'], 'evidence': [self.evidence],
            'effective_modifier_contributions': values, 'test_data': True}


class FeedbackContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'output'
        self.output.mkdir()
        evidence = self.root / 'synthetic-GUI.txt'
        evidence.write_text('Synthetic offline observation, not actual GUI', encoding='utf-8')
        self.evidence = case.pin(evidence)
        self.context = {'product': 'li-yu-dao', 'case': case.CASE, 'run_id': 'SYNTHETIC-RUN',
                        'output': str(self.output), 'state_dir': str(self.root / 'state')}
        contract = self.root / 'state/profile/mod-content/fixture/_case_contract.json'
        contract.parent.mkdir(parents=True)
        contract.write_text(json.dumps({'product': 'li-yu-dao', 'case': case.CASE,
            'config': {'case_id': case.CASE}, 'test_data': True}), encoding='utf-8')

    def test_setup_is_self_only_and_never_business_effect_proof(self):
        receipt = producer.generate(self.root / 'emission', {'TEST_DATA': True})
        effect = (self.root / 'emission/common/on_action/lyd_feedback_setup.txt').read_text(encoding='utf-8-sig')
        self.assertIn('random_player', effect)
        self.assertIn('is_ai = no', effect)
        self.assertIn('set_character_rite = rite:jingxue', effect)
        for forbidden in ('set_character_faith', 'set_main_rite', 'every_', 'set_holder',
                          'lyd_enter_effect', 'add_character_modifier', 'lyd_enabled', 'trigger_event'):
            self.assertNotIn(forbidden, effect)
        self.assertFalse(receipt['business_pass'])
        self.assertFalse(receipt['fixture_flag_is_business_proof'])
        with self.assertRaises(ValueError):
            producer.generate(self.root / 'emission', {})

    def test_wrong_actor_or_bool_identity_rejected(self):
        for key, value in [('character_id', 31254), ('character_id', True)]:
            value_frame = frame()
            value_frame['played_character'][key] = value
            with self.assertRaises(ValueError):
                case.frame_binding(value_frame)

    def test_failed_faith_or_no_head_guard_submits_no_decision(self):
        for bad in ('faith', 'head'):
            output = self.root / bad
            output.mkdir()
            context = {**self.context, 'output': str(output)}
            client = Client(self.evidence, bad=bad)
            with self.assertRaises(ValueError):
                case.run_case(context, client)
            self.assertEqual(client.steps, [])
            self.assertEqual(json.loads((output / case.RESULT).read_text())['runtime_status'], 'RED')

    def test_wrong_decision_target_has_no_select_or_retry(self):
        client = Client(self.evidence, bad='target')
        with self.assertRaises(ValueError):
            case.decision(client, 'entry', frame())
        self.assertEqual(len(client.steps), 2)
        self.assertFalse(any('select' in step['tool'] for step in client.steps))

    def test_real_host_invoke_explicit_revision_route_does_not_refresh(self):
        # Execute the actual repository host method with inert call/fresh only.
        # This catches stale explicit revision + fresh_revision=true without SDK.
        path = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PlanClient')
        method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'invoke')
        code = ast.Module(body=[method], type_ignores=[])
        namespace = {'json': json, 'resolve': lambda args, ctx: args}
        exec(compile(code, str(path), 'exec'), namespace)
        client = Client(self.evidence)
        case.decision(client, 'entry', frame())
        class Host:
            tools = {tool: {'inputSchema': {'properties': {'expected_revision': {}}}} for tool in case.TOOLS}
            snapshot = frame()
            results = {}
            episode_identity = {}
            refreshes = 0
            async def fresh(self):
                self.refreshes += 1
            async def call(self, name, args):
                return name, args
        host = Host()
        for step in client.steps:
            result = asyncio.run(namespace['invoke'](host, step['tool'], step['args'], fresh_revision=step['fresh_revision']))
            self.assertEqual(result[1]['expected_revision'], 8)
        self.assertEqual(host.refreshes, 0)
        self.assertEqual([s['kind'] for s in client.steps], ['tool'] * 3)

    def test_pending_ack_requires_later_root_actual_review(self):
        client = Client(self.evidence)
        result = case.run_case(self.context, client)
        self.assertTrue(result['case_contract_qualified'])
        self.assertFalse(result['business_pass'])
        self.assertEqual(client.reviews, list(case.PHASES))
        self.assertEqual(len([s for s in client.steps if s['tool'] == case.TOOLS[3]]), 5)
        self.assertFalse(any('confirm' in s['tool'] or 'select_event' in s['tool'] for s in client.steps))
        self.assertTrue(case.verify_case(self.context)['case_contract_qualified'])

    def test_unobservable_core_is_red_but_other_representatives_are_recorded(self):
        client = Client(self.evidence, soft_failure='school')
        result = case.run_case(self.context, client)
        self.assertFalse(result['case_contract_qualified'])
        self.assertEqual(client.reviews, list(case.PHASES))
        self.assertEqual([r['phase'] for r in result['observations'] if not r['qualified']], ['school'])
        with self.assertRaises(ValueError):
            case.verify_case(self.context)

    def test_tooltip_values_and_nonfinite_numbers_cannot_prove_modifiers(self):
        row = {'effective_modifier_contributions': {k: {'value': v,
                'source_tenet_key': 'lyd_tenet_reverent_heaven', 'effective_on_actor': True,
                'evidence_kind': 'actual_actor_modifier_breakdown'} for k, v in case.MODIFIERS['personal'].items()}}
        self.assertTrue(case.modifier_qualified('personal', row))
        for value, kind in [('NaN', 'actual_actor_modifier_breakdown'), ('0.05', 'tenet_tooltip_description')]:
            changed = copy.deepcopy(row)
            changed['effective_modifier_contributions']['monthly_legitimacy_add'].update(value=value, evidence_kind=kind)
            self.assertFalse(case.modifier_qualified('personal', changed))

    def test_verify_rejects_changed_gui_evidence(self):
        case.run_case(self.context, Client(self.evidence))
        Path(self.evidence['path']).write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            case.verify_case(self.context)


if __name__ == '__main__':
    unittest.main()
