"""One new cross-package source seam; no replay of owner functional matrices."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys

import prepare_source20_minimal_warm_sdk_v1 as producer

PROOF = 'docs/ck3-native-ai/evidence/source20-minimal-warm-sdk-source-qualification-2026-10-20.json'
PLAN = 'docs/ck3-native-ai/evidence/source20-minimal-warm-sdk-source-plan-2026-10-20.json'
OWN = ('tools/g2_saved_campaign/prepare_source20_minimal_warm_sdk_v1.py',
       'tools/g2_saved_campaign/qualify_source20_minimal_warm_sdk_v1.py')


class MemorySource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, changed):
        self.sources = {n[:-3].replace('/', '.'): (n, raw) for n, raw in changed.items()}
        self.loaded = []
    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.sources:
            return importlib.util.spec_from_loader(fullname, self, origin='<Source20-RAM>')
        return None
    def create_module(self, spec):
        return None
    def get_source(self, name):
        return self.sources[name][1].decode('utf-8-sig')
    def exec_module(self, module):
        relative, raw = self.sources[module.__name__]
        # A virtual path for relative import/inspect conventions, never an
        # assertion that the new file exists in the old physical Source15 tree.
        module.__file__ = str(producer.BASE_ROOT/relative)
        exec(compile(raw, '<Source20-RAM/'+relative+'>', 'exec', dont_inherit=True), module.__dict__)
        self.loaded.append({'module': module.__name__, 'relative': relative, **producer.exact.pin(raw)})


def shared_budget_to_actual_MCP_diagnostic_cross():
    from xar_autoplayer.bridge import service, mcp_server
    from xar_autoplayer.bridge import campaign_root_terminal_retry_v1 as terminal
    from xar_autoplayer.bridge import campaign_root_retry_diagnostic_v1 as diagnostic
    from xar_autoplayer.bridge import readonly_planning_retry_v1 as readonly
    from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
    require = producer.require
    require(service.claim_campaign_root_terminal_retry_v1 is terminal.claim_campaign_root_terminal_retry_v1,
            'candidate Service does not use the composed claim helper')
    failure = {'query_type': 'campaign', 'stage': 'wait', 'wait_completed': False,
        'wait_result': 'executor_failed', 'executor_enter': False, 'executor_finish': None,
        'executor_typed_result': None, 'typed_result': None, 'frame_stable': None,
        'final_read': None, 'final_equal': None,
        'executor_exception': {'code': 0, 'image': 'none', 'rva': None}}
    raw_error = 'application-main typed query failed or its snapshot changed'
    # Explicit synthetic fixture, using the actual unchanged Source15 exception
    # class and the raw/frame text split received by the normal MCP diagnostic.
    error = _NativeCommandRejectedError.__new__(_NativeCommandRejectedError)
    Exception.__init__(error, 'synthetic Source20 cross-package rejection')
    error.native_request_id = 'synthetic-source20-cross'
    error.native_request_frame = {'type': 'execute_step', 'protocol_version': 1,
        'request_id': error.native_request_id, 'step': 'query-campaign-root-context-v1', 'expected_revision': 71}
    error.native_command_result_frame = {'type': 'command_result', 'protocol_version': 1,
        'request_id': error.native_request_id, 'ok': False, 'result': None,
        'error': raw_error, 'typed_query_failure_v1': failure}
    error.native_error = raw_error+'; typed_query_failure_v1='+json.dumps(failure, sort_keys=True, separators=(',', ':'))
    budget = {'remaining': 1, 'rejections': []}; token = readonly._RETRY_BUDGET.set(budget)
    try:
        require(terminal.is_campaign_root_terminal_rejection_v1(error, {'native_revision': 71}), 'typed fixture not recognized')
        require(terminal.claim_campaign_root_terminal_retry_v1(error, {'native_revision': 71})
                and budget == {'remaining': 0, 'rejections': []}, 'first claim did not share the actual outer budget')
        require(not terminal.claim_campaign_root_terminal_retry_v1(error, {'native_revision': 71}),
                'second inner claim exceeded the shared whole-plan budget')
        native = mcp_server._native_command_rejection_diagnostic(error)
        require(native['native_error'] == raw_error, 'actual MCP diagnostic lost the raw error binding')
        projected = diagnostic.project_campaign_root_retry_diagnostic_v1(error, native)
        require(projected['status'] == 'declined'
            and projected['reason'] == 'shared_readonly_retry_budget_exhausted'
            and projected['retry_authorized'] is False and len(json.dumps(projected).encode()) <= 2048,
            'shared budget decline is not bounded and visible')
        require('typed_query_failure_v1' not in json.dumps(projected)
                and 'native_request_frame' not in projected and 'native_command_result_frame' not in projected,
                'full native frame leaked into optional retry projection')
    finally:
        readonly._RETRY_BUDGET.reset(token)
    return {'kind': 'synthetic cross-package seam using actual unchanged Source15 exception and actual MCP diagnostic function',
        'passed': True, 'shared_budget_first_true_second_false': True,
        'replan_audit_not_fabricated': True, 'bounded_MCP_budget_decline': True,
        'Game_Native_commands_or_reads': 0}


def qualify():
    producer.require(sys.dont_write_bytecode, 'run -B')
    producer.require(not any(n == 'xar_autoplayer' or n.startswith('xar_autoplayer.') for n in sys.modules),
                     'fresh source qualifier required')
    changed, rows, report = producer.compose()
    loader = MemorySource(changed); sys.meta_path.insert(0, loader); sys.path.insert(0, str(producer.BASE_ROOT))
    try:
        for name in sorted(loader.sources):
            importlib.import_module(name)
        cross = shared_budget_to_actual_MCP_diagnostic_cross()
        producer.require(len(loader.loaded) == 6, 'all six candidate modules must load once')
        for name, module in list(sys.modules.items()):
            if name == 'xar_autoplayer' or name.startswith('xar_autoplayer.'):
                path = getattr(module, '__file__', None)
                if path:
                    producer.require(Path(path).resolve().is_relative_to(producer.BASE_ROOT.resolve()),
                                     'production import escaped Source15 '+name)
        old = producer.actual_source(producer.READONLY, {r['relative']: r for r in json.loads(
            producer.BASE_FREEZE.read_bytes())['files']})
        producer.require(producer.exact.function_asts(old)['retry_readonly_planning_once_v1'] ==
            producer.exact.function_asts(changed[producer.READONLY])['retry_readonly_planning_once_v1'],
            'original outer retry loop AST changed')
        report['status'] = 'SOURCE_INTEGRITY_IMPORT_AND_CROSS_PACKAGE_PASS_NOT_ADOPTED'
        report['qualification'] = {'new_cross_package_checks': [cross], 'loaded_RAM_modules': loader.loaded,
            'other_production_imports': 'actual frozen Source15; RAM modules use virtual __file__ paths, no new physical authority',
            'Service_and_MCP_and_readonly_inverse': 'PASS', 'full1445_original_Git_metadata_and1447_rows': 'PASS',
            'original_outer_loop_AST': 'UNCHANGED', 'owner_tests_reused': 'M0 3; M5 final43+actualSource15 outer12; MCP original7+bounded2+budget1. None repeated here.',
            'withdrawn_five_delta_31case_candidate_used_as_final': False,
            'Root_writer_recipe_executed': False, 'scratch_files': 0, 'Git_D_Task_Game_RPC_writes': 0,
            'actual_runtime_recovery_or_performance_credit': False}
        return report
    finally:
        sys.meta_path.remove(loader); sys.path.remove(str(producer.BASE_ROOT))
        for name in list(sys.modules):
            if name == 'xar_autoplayer' or name.startswith('xar_autoplayer.'):
                del sys.modules[name]


def freeze():
    card = json.loads(producer.exact.check_bytes(producer.CARD.read_bytes(), producer.CARD_PIN, 'Source20 source card'))
    now = datetime.now(timezone.utc); scope = card['scopes']['composer_Source20_minimal_warm_source64KiB']
    producer.require(card['machine_id'] == producer.MACHINE and card['status'] == 'ADMITTED_SOURCE_ONLY'
        and scope['owner'] == 'warm_sdk_composer' and scope['hard_bytes'] == producer.SOURCE_CAP
        and now < datetime.fromisoformat(card['review_at_utc']), 'source commitment differs or expired')
    paths = [producer.REPO/PROOF, producer.REPO/PLAN]
    producer.require(all(not path.exists() for path in paths), 'frozen Source20 report already exists')
    report = qualify(); encode = lambda doc: (json.dumps(doc, ensure_ascii=False, indent=2)+'\n').encode()
    proof = encode(report)
    own = [{'path': str(producer.REPO/n), **producer.exact.pin((producer.REPO/n).read_bytes())} for n in OWN]
    proof_pin = {'path': str(paths[0]), **producer.exact.pin(proof)}
    plan = {'schema': 'xar.source20.minimal-warm-sdk-frozen-source-plan/v1',
        'machine_id': producer.MACHINE, 'observed_at_utc': now.isoformat(),
        'machine_source': 'tools/ck3_live_run_id.py machine; tool329d4e; base machine verified in pinned624c inventory',
        'status': 'SOURCE_FROZEN_NOT_DEPLOYED', 'producer': own[0], 'qualifier': own[1], 'qualification': proof_pin,
        'entry': 'prepare_source20_minimal_warm_sdk_v1.compose() returns changed6 bytes, complete1447 row manifest and proof in RAM.',
        'base': report['base'], 'output': {'complete_manifest': report['complete_manifest'],
            'changed_existing_leaves': 4, 'new_leaves': 2, 'unchanged_original_leaves': 1441,
            'delta_row_source': proof_pin},
        'family_fix_preserved': report['family_fix_preserved'],
        'existing_frozen_inputs': {'complete_paths_bytes_SHA_table_in': proof_pin,
            'M5_final_authority': producer.M5_PROOF, 'MCP_final_authority': producer.MCP_BUDGET_PROOF},
        'qualification_scope': {'full_detail_in': proof_pin, 'new_cross_package_check': report['qualification']['new_cross_package_checks'][0],
            'six_RAM_modules_and_other_Source15_imports': 'PASS', 'all_three_transforms_inverse': 'PASS',
            'original_Service_retry_and_outer_loop': 'UNCHANGED', 'owner_matrices_repeated': False},
        'shared_once_budget': {'actual_existing_helper': 'bridge/readonly_planning_retry_v1.py',
            'claim_API': 'claim_guarded_campaign_root_retry_v1', 'Service_three_gates': 'claim_campaign_root_terminal_retry_v1',
            'pure_recognition_separate': True, 'outer_loop_and_original_Service_retry_method': 'unchanged',
            'final_authority': producer.M5_PROOF, 'old31case_five_delta_proof': 'withdrawn candidate history only'},
        'prospective_capacity': {k: v for k, v in report['prospective_capacity'].items() if k != 'Git_object_inventory'},
        'complete_Git_object_inventory_in': proof_pin, 'proposed_roots': producer.PROPOSED_ROOTS,
        'Root_anchor_recipe': {'call': 'canonical_anchor_with_root_writer(Root_git_writer, anchor_ref=NEW_REF, root_release_sha256=exact_Root_release_SHA)',
            'create_only_ref': producer.NEW_REF, 'parent': producer.BASE, 'candidate_tree_RAM_model': report['candidate_Git_tree_model'],
            'object_recipe': 'Six exact blobs + five child-first ancestor trees; full1447 metadata check; new commit-tree and create-only ref. No master/index/checkout changes.',
            'source_run_executed': False, 'permission': 'Root must read actual separate Git-object capacity/release; a SHA argument alone is not authorization.'},
        'boundaries': report['boundaries'], 'future_materialization': report['future_materialization'],
        'storage': {'source_card': {'path': str(producer.CARD), **dict(zip(('bytes', 'sha256'), producer.CARD_PIN))},
            'complete_hard_bytes': producer.SOURCE_CAP, 'owned_retained_files_excluding_this_plan': own+[proof_pin],
            'total_retained_logical_including_this_plan': 0, 'allocated_bytes': None, 'physical_release_credit_bytes': 0,
            'source_test_owners_reused_in_place_not_doublecharged': ['M0', 'M5', 'perf_harness'],
            'new_scratch_bytes': 0, 'future_writes_after_freeze': 0, 'review_at_utc': card['review_at_utc'],
            'small_record_review_at_utc': (now+timedelta(days=180)).isoformat()},
        'remaining': ['Root source review and actual create-only business anchor under separate Git capacity',
            'Then actual C20 controls/feeder/Task/atomic exact pins and complete capacity card',
            'Normal SDK close/new Source20 materialization and warm constructor by sole runtime owner',
            'Actual bounded retry outcome/diagnostic/performance evidence; current C18 stays unchanged']}
    retained = sum(x['bytes'] for x in own)+len(proof)
    while True:
        raw = encode(plan); total = retained+len(raw)
        if total == plan['storage']['total_retained_logical_including_this_plan']:
            break
        plan['storage']['total_retained_logical_including_this_plan'] = total
    producer.require(total <= producer.SOURCE_CAP, 'complete Source20 source package exceeds64KiB: '+str(total))
    with paths[0].open('xb') as stream:
        stream.write(proof)
    with paths[1].open('xb') as stream:
        stream.write(raw)
    return {'producer': own[0], 'qualifier': own[1], 'qualification': proof_pin,
        'plan': {'path': str(paths[1]), **producer.exact.pin(raw)}, 'complete_source_bytes': total,
        'full_manifest': report['complete_manifest'], 'prospective_capacity': report['prospective_capacity']['components'],
        'complete_stage_quote': report['prospective_capacity']['complete_stage_quote_upper']}


if __name__ == '__main__':
    if sys.argv[1:] == ['--freeze']:
        print(json.dumps(freeze(), ensure_ascii=False, indent=2))
    else:
        producer.require(not sys.argv[1:], 'only --freeze or no arguments')
        print(json.dumps(qualify(), ensure_ascii=False, indent=2))
