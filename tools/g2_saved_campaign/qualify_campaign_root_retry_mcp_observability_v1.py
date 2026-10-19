"""Focused bounded projection and actual MCP error-handler source qualification."""
import argparse
import ast
import copy
import importlib
import json
import sys
import types
import unittest
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import prepare_campaign_root_retry_mcp_observability_v1 as transform

OWN = Path(__file__).resolve().parent
REPO = OWN.parent.parent
SRC = REPO/'ck3_autonomous_player/src'
sys.path.insert(0, str(SRC))
from xar_autoplayer.bridge.campaign_root_retry_diagnostic_v1 import project_campaign_root_retry_diagnostic_v1 as project
HELPER = SRC/'xar_autoplayer/bridge/campaign_root_retry_diagnostic_v1.py'
MCP = SRC/'xar_autoplayer/bridge/mcp_server.py'
ACTUAL = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src15/xar_autoplayer/bridge/mcp_server.py')
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
ROOT = 'query-campaign-root-context-v1'


class BridgeFailure(Exception):
    pass


class NativeFailure(BridgeFailure):
    def __init__(self, step=ROOT):
        super().__init__('original native error; typed_query_failure_v1={"executor_enter":false}')
        self.native_request_frame = {'type':'execute_step', 'protocol_version':1,
            'request_id':'fixture-query-1', 'step':step, 'expected_revision':4360}
        self.native_command_result_frame = {'type':'command_result', 'protocol_version':1,
            'request_id':'fixture-query-1', 'ok':False,
            'error':'application-main typed query failed or its snapshot changed'}
        self.native_request_id = 'fixture-query-1'


def diagnostic(error):
    return {'diagnostic_only':True, 'native_request_id':error.native_request_id,
        'native_step':error.native_request_frame['step'], 'expected_native_revision':4360,
        'native_error':error.native_command_result_frame['error']}


def decline():
    return {'status':'declined', 'reason':'fresh_frame_checks_failed',
        'failed_checks':['same_date', 'fresh_native_revision'],
        'old_frame':{'revision':1693, 'native_revision':4360, 'date_raw':53274576,
                     'snapshot_id':'must-not-leave', 'private_secret':object()},
        'fresh_frame':{'revision':1694, 'native_revision':4361, 'date_raw':53274576},
        'old_connection':{'bridge_pid':30852, 'connection_generation':3},
        'fresh_connection':{'bridge_pid':30852, 'connection_generation':3},
        'history_tail':[object()], 'starting_snapshot':object(), 'fresh_snapshot':object()}


def source_function(raw, name, scope):
    nodes = [node for node in ast.walk(ast.parse(raw))
        if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise ValueError('exactly one source function required: '+name)
    node = copy.deepcopy(nodes[0]); node.decorator_list = []
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), name, 'exec'), scope)
    return scope[name]


class Qualification(unittest.TestCase):
    def test_shared_budget_decline_is_visible(self):
        error = NativeFailure()
        error.read_only_query_retry_decline = {'status':'declined',
            'reason':'shared_readonly_retry_budget_exhausted', 'failed_checks':[]}
        out = project(error, diagnostic(error))
        self.assertEqual(out['status'], 'declined')
        self.assertEqual(out['reason'], 'shared_readonly_retry_budget_exhausted')
        self.assertEqual(out['failed_checks'], [])
        self.assertFalse(out['retry_authorized'])

    def test_source_function_rejects_duplicate_nodes(self):
        raw = 'def duplicate(): return 1\ndef duplicate(): return 2\n'
        with self.assertRaises(ValueError):
            source_function(raw, 'duplicate', {})

    def test_absent_is_unknown(self):
        error = NativeFailure(); native = diagnostic(error); before = copy.deepcopy(native)
        out = project(error, native)
        self.assertEqual(out['status'], 'evidence_absent')
        self.assertIn('unknown', out['evidence_meaning'])
        self.assertFalse(out['retry_authorized']); self.assertEqual(native, before)

    def test_decline_allowlist_and_no_nested_payload(self):
        error = NativeFailure(); error.read_only_query_retry_decline = decline()
        out = project(error, diagnostic(error)); raw = json.dumps(out)
        self.assertEqual(out['status'], 'declined')
        self.assertEqual(out['failed_checks'], ['same_date', 'fresh_native_revision'])
        self.assertEqual(out['old_frame'], {'revision':1693, 'native_revision':4360, 'date_raw':53274576})
        self.assertNotIn('history', raw); self.assertNotIn('snapshot', raw)
        self.assertIs(error.read_only_query_retry_decline['old_frame']['private_secret'].__class__, object)

    def test_second_rejection_utf8_and_escaped_json_cap(self):
        for text in ('二次拒绝'*400, '\x00\n"\\'*600):
            with self.subTest(text=text[:4]):
                error = NativeFailure(); error.read_only_query_retry = dict(decline(), second_error=text)
                out = project(error, diagnostic(error))
                self.assertEqual(out['status'], 'second_rejection')
                self.assertLessEqual(len(out['second_error'].encode()), 512)
                self.assertLessEqual(len(json.dumps(out, ensure_ascii=False, separators=(',', ':')).encode()), 2048)
                self.assertTrue(out['second_error_truncated'])

    def test_integer_and_check_limits(self):
        error = NativeFailure(); value = decline()
        value['old_frame'] = {'revision':True, 'native_revision':-1, 'date_raw':2**65}
        value['failed_checks'] = ['foreign-secret', 'same_date']*100
        error.read_only_query_retry_decline = value
        out = project(error, diagnostic(error))
        self.assertEqual(out['old_frame'], {})
        self.assertLessEqual(len(out['failed_checks']), 16)
        self.assertNotIn('foreign-secret', json.dumps(out))
        self.assertTrue(out['evidence_truncated'])

    def test_foreign_rejection_is_omitted(self):
        for change in ('step', 'request_id', 'error', 'boolean_revision'):
            with self.subTest(change=change):
                error = NativeFailure(); native = diagnostic(error)
                if change == 'step': error.native_request_frame['step'] = 'send-gift'
                elif change == 'request_id': error.native_command_result_frame['request_id'] = 'foreign'
                elif change == 'error': error.native_command_result_frame['error'] = 'other failure'
                else: native['expected_native_revision'] = True
                self.assertIsNone(project(error, native))

    def test_actual_handler_preserves_error_and_native_diagnostic(self):
        candidate, _ = transform.transform_mcp_source_v1(ACTUAL.read_bytes())
        scope = {'__package__':'xar_autoplayer.bridge', 'json':json, 'Mapping':Mapping,
            '_NativeCommandRejectedError':NativeFailure, 'BridgeUnavailableError':BridgeFailure,
            'start_army_timing':lambda name:None, 'successor_owner':None,
            'before_auto_turn_submit':None}
        native_project = source_function(candidate, '_native_command_rejection_diagnostic', scope)
        handler = source_function(candidate, 'ck3_auto_turn', scope)
        fake_types = types.ModuleType('mcp.types')
        fake_types.CallToolResult = fake_types.TextContent = types.SimpleNamespace
        construction = types.ModuleType('xar_autoplayer.bridge.domain_construction_private_transport_v1')
        construction.construction_transport_diagnostic = lambda error: None
        def failing(error):
            def auto_turn(): raise error
            scope['service'] = types.SimpleNamespace(auto_turn=auto_turn)
        modules = {'mcp.types':fake_types,
            'xar_autoplayer.bridge.domain_construction_private_transport_v1':construction}
        with patch.dict(sys.modules, modules):
            for state in ('evidence_absent', 'declined', 'second_rejection'):
                error = NativeFailure()
                if state == 'declined': error.read_only_query_retry_decline = decline()
                if state == 'second_rejection': error.read_only_query_retry = dict(decline(), second_error='second unchanged refusal')
                original_native = native_project(error); failing(error); out = handler()
                self.assertTrue(out.is_error)
                self.assertEqual(out.content[0].text, f'Error executing tool ck3_auto_turn: {error}')
                self.assertEqual(out.structured_content['diagnostics']['native_command_rejection'], original_native)
                self.assertEqual(out.structured_content['diagnostics']['campaign_root_readonly_retry_v1']['status'], state)
            foreign = NativeFailure('pause-map'); failing(foreign)
            self.assertNotIn('campaign_root_readonly_retry_v1', handler().structured_content['diagnostics'])
            other = BridgeFailure('not a native rejection'); failing(other)
            with self.assertRaises(BridgeFailure) as caught: handler()
            self.assertIs(caught.exception, other)

    def test_exact_source_inverse(self):
        actual, self.report = transform.transform_mcp_source_v1(ACTUAL.read_bytes())
        master = MCP.read_bytes()
        restored = master.decode().replace(transform.NEW, transform.OLD, 1).encode()
        self.assertEqual(transform.sha(restored), transform.MASTER_SHA)
        reproduced, _ = transform.transform_mcp_source_v1(restored, expected_sha256=transform.MASTER_SHA)
        self.assertEqual(reproduced, master)
        self.assertEqual(actual.decode().replace(transform.NEW, transform.OLD, 1).encode(), ACTUAL.read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--proof', type=Path)
    parser.add_argument('--targeted', action='store_true')
    parser.add_argument('--budget-only', action='store_true'); args = parser.parse_args()
    suite = (unittest.TestSuite(Qualification(name) for name in (
        'test_source_function_rejects_duplicate_nodes', 'test_second_rejection_utf8_and_escaped_json_cap'))
        if args.targeted else unittest.defaultTestLoader.loadTestsFromTestCase(Qualification))
    if args.budget_only:
        suite = unittest.TestSuite([Qualification('test_shared_budget_decline_is_visible')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
    _, report = transform.transform_mcp_source_v1(ACTUAL.read_bytes())
    paths = [MCP, HELPER, Path(transform.__file__), Path(__file__)]
    proof = {'schema':'xar.source20.campaign-root-retry-observability-source-qualification/v1',
        'machine_id':MACHINE, 'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'machine_source':'tools/ck3_live_run_id.py machine; current readback xenoamess-full-tower-eb9d2c1186',
        'status':'SOURCE_QUALIFIED_NOT_ADOPTED', 'focused_tests_passed':result.testsRun,
        'files':[{ 'path':str(p.resolve()), 'bytes':p.stat().st_size, 'sha256':transform.sha(p.read_bytes())} for p in paths],
        'actual_Source15_MCP_transform':report, 'actual_error_handler_AST_executed':True,
        'unrelated_construction_transport_and_MCP_result_types_stubbed':True,
        'JSON_limit_bytes':2048, 'second_error_UTF8_limit_bytes':512, 'known_failed_checks_limit':16,
        'retry_strategy_or_Native_calls_added':False, 'old_error_and_native_diagnostic_preserved':True,
        'absent_evidence_does_not_prove_no_retry':True, 'large_frame_history_snapshot_projected':False,
        'D_Git_Task_Game_RPC_Driver_SAVE_operations':0, 'scratch_files':0,
        'source_card_sha256':'fbcc467fdece4f2edc7075b06a4f01bb63ad551e6f1e7bc67e9190039aaec00a',
        'complete_source_cap_bytes':327680, 'retained_bytes_excluding_this_proof':sum(p.stat().st_size for p in paths),
        'actual_Native_root_cause_or_runtime_success_claimed':False,
        'record_review_at_utc':'2027-04-17T20:34:22+00:00', 'future_writes_after_freeze':0}
    if args.targeted or args.budget_only:
        old = REPO/'docs/ck3-native-ai/evidence/source20-campaign-root-retry-mcp-observability-2026-10-20.json'
        old_raw = old.read_bytes()
        if len(old_raw) != 2744 or transform.sha(old_raw) != 'd821fdd4705266b2d1c855286bb0c98e7b6cf13a11442e08ca0226783c3fe9f0':
            raise ValueError('original 7-PASS proof changed')
        proof.update(schema='xar.source20.campaign-root-retry-observability-bounded-input-addendum/v1',
            original_qualification={'path':str(old), 'bytes':len(old_raw), 'sha256':transform.sha(old_raw)},
            original_seven_tests_repeated=False, targeted_tests_passed=result.testsRun,
            optimized_mode=not __debug__, input_function_duplicates_rejected=True,
            text_encoding_bounded_before_encode=True, actual_error_handler_AST_executed=False,
            original_actual_handler_evidence_reused=True)
        proof['retained_bytes_excluding_this_proof'] += len(old_raw)
    if args.budget_only:
        previous = REPO/'docs/ck3-native-ai/evidence/source20-campaign-root-retry-mcp-bounded-input-addendum-2026-10-20.json'
        previous_raw = previous.read_bytes()
        if len(previous_raw) != 3254 or transform.sha(previous_raw) != '3e3ec2ae12d2d8db78165b7d074561fefd02cf308babccf13cca7e82b864f78d':
            raise ValueError('bounded-input addendum changed')
        proof.update(schema='xar.source20.campaign-root-retry-shared-budget-observability-addendum/v1',
            prior_bounded_input_proof={'path':str(previous), 'bytes':3254, 'sha256':transform.sha(previous_raw)},
            prior_targeted_tests_repeated=False, shared_budget_decline_reason_visible=True,
            input_function_duplicates_rejected='prior proof; not repeated in this increment',
            text_encoding_bounded_before_encode='prior proof; not repeated in this increment')
        proof['retained_bytes_excluding_this_proof'] += len(previous_raw)
    raw = (json.dumps(proof, ensure_ascii=False, indent=2)+'\n').encode()
    if len(raw) > 4096 or proof['retained_bytes_excluding_this_proof']+len(raw) > 327680:
        raise ValueError('complete source/proof cap exceeded')
    if args.proof:
        with args.proof.open('xb') as output: output.write(raw)
    print(json.dumps({'tests':result.testsRun, 'proof_bytes':len(raw), 'proof_sha256':transform.sha(raw),
        'complete_retained_bytes':proof['retained_bytes_excluding_this_proof']+len(raw), 'actual_candidate':report}))
