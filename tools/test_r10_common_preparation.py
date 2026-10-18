"""One compound regression for compact common rows versus legacy envelopes.

Synthetic transport only: proves delegation/origin/once behaviour, not live
military readiness, native ABI, B-site growth, formal ABC or media credit.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument('--source-repo', type=Path, default=Path(__file__).resolve().parents[1])
_arguments, _remaining = _parser.parse_known_args()
sys.path.insert(0, str(_arguments.source_repo / 'tools'))
sys.path.insert(0, str(_arguments.source_repo / 'ck3_autonomous_player/src'))
_path = Path(__file__).parent / 'ck3_mod_acceptance_cases/r10_prepare_adapter.py'
_spec = importlib.util.spec_from_file_location('r10_adapter_under_test', _path)
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)


class CommonSeam(unittest.TestCase):
    def test_original_compact_row_derived_full_body_and_once_delegation(self):
        from xar_autoplayer.bridge import episode04_ready_t0_12004 as ready
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            class Client:
                output = root
                calls = []
                def execute_plan(self, steps, name, timeout=None):
                    self.calls.append(steps)
                    step = steps[0]
                    public_id = 'owned-' + step['id']
                    body = ({'revision': 11} if step['tool'] == 'ck3_take_snapshot'
                            else {'accepted': True})
                    original = {'id': public_id, 'ok': True, 'result': dict(body)}
                    result = {**original, 'id': step['id'], 'continuation_public_step_id': public_id}
                    if step['tool'] == 'ck3_query_army_strengths':
                        original['result'] = {'result_location': 'compact_mcp_summary'}
                        result['result'] = {'accepted': True, 'army_strengths': [{'army_id': 0}]}
                        result['wire_full_result_proof'] = {'original_wire_range': [10, 20],
                            'representation': 'derived production-normalized native wire result; not complete Driver packet'}
                    (root / (public_id + '.actual-results.json')).write_text(json.dumps({'rows': [original]}), encoding='utf-8')
                    return [result]
                def checkpoint(self, name, value):
                    path = root / (name + '.json')
                    with path.open('x', encoding='utf-8') as stream:
                        json.dump(value, stream)
                    return path
            client = Client()
            context = {'run_dir': str(root / 'machine--r10-common-preparation--R0001'),
                'run_id': 'machine--r10-common-preparation--R0001',
                'case_inputs': {'army_id': 0, 'native_carmy_id': 0, 'war_id': 1,
                    'goal_province_id': 1527, 'staging_province_id': 1506, 'agreed_commander_id': 33388}}
            relay = adapter.CommonRequestRelay(context, client, machine='synthetic-machine')
            with patch.object(ready, 'evaluate_episode04_ready_t0_12004', return_value={'military_t0_frame_ready': False}) as evaluate:
                output = adapter.collect_ready_t0(context, relay, source_binding={'synthetic_only': True})
            self.assertIs(relay.client, client)
            self.assertEqual(len(client.calls), 6)
            self.assertEqual([x[0]['tool'] for x in client.calls], ['ck3_take_snapshot', 'ck3_query_army_strengths',
                'ck3_query_army_commander_candidates_v1', 'ck3_query_war_cash_current_resources_private_v1',
                'ck3_execute_step', 'ck3_take_snapshot'])
            self.assertEqual(evaluate.call_args.kwargs['strengths']['army_strengths'], [{'army_id': 0}])
            original = json.loads((root / 'owned-r10-ready-strengths.actual-results.json').read_bytes())
            self.assertEqual(original['rows'][0]['result'], {'result_location': 'compact_mcp_summary'})
            envelope = json.loads((root / 'r10-ready-strengths-r10-common-envelope.json').read_bytes())
            self.assertEqual(envelope['body']['army_strengths'], [{'army_id': 0}])
            self.assertIn('derived', envelope['transport_origin'])
            self.assertFalse(envelope['original_Driver_raw_result_reference_available'])
            self.assertNotIn('army_history_evidence', envelope)
            self.assertEqual(envelope['wire_full_result_proof']['original_wire_range'], [10, 20])
            self.assertFalse(output['formal_ABC_arm'])
            with self.assertRaisesRegex(ValueError, 'never replay'):
                relay.request('r10-ready-strengths', 'ck3_query_army_strengths', {})
            self.assertEqual(len(client.calls), 6)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *_remaining])
