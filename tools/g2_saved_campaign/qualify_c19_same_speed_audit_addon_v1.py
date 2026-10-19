"""Small addon integrity/import check; reuse M0's frozen functional proof."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib
import json
from pathlib import Path
import sys
import types

import prepare_c19_same_speed_audit_addon_v1 as producer

PROOF = 'docs/ck3-native-ai/evidence/c19-same-speed-audit-addon-source-qualification-2026-10-20.json'
PLAN = 'docs/ck3-native-ai/evidence/c19-same-speed-audit-addon-source-plan-2026-10-20.json'
OWN_FILES = ('tools/g2_saved_campaign/prepare_c19_same_speed_audit_addon_v1.py',
             'tools/g2_saved_campaign/qualify_c19_same_speed_audit_addon_v1.py')


def qualify():
    producer.require(sys.dont_write_bytecode, 'use -B; no bytecode scratch is admitted')
    producer.require(not any(n == 'xar_autoplayer' or n.startswith('xar_autoplayer.')
                            for n in sys.modules), 'fresh import qualifier required')
    changed, rows, report = producer.compose()
    sys.path.insert(0, str(producer.BASE_ROOT))
    try:
        package = importlib.import_module('xar_autoplayer.bridge')
        name = 'xar_autoplayer.bridge.exact_day_speed_configuration_v1'
        module = types.ModuleType(name); module.__package__ = package.__name__
        module.__file__ = str(producer.BASE_ROOT/producer.HELPER)
        sys.modules[name] = module
        exec(compile(changed[producer.HELPER], '<C19-audit-addon-memory>', 'exec', dont_inherit=True), module.__dict__)
        dependency_paths = []
        by_name = {row['relative']: row for row in rows}
        for relative in ('xar_autoplayer/bridge/driver.py', 'xar_autoplayer/bridge/version_identity.py'):
            imported = sys.modules[relative[:-3].replace('/', '.')]
            path = Path(imported.__file__).resolve()
            producer.require(path == (producer.BASE_ROOT/relative).resolve(), 'import escaped source15')
            row = by_name[relative]; raw = path.read_bytes()
            producer.exact.check_bytes(raw, (row['bytes'], row['sha256']), 'actual imported dependency')
            producer.require(producer.exact.blob_sha(raw) == row['git_blob_sha1'], 'imported Gitblob differs')
            dependency_paths.append({'relative': relative, 'path': str(path), **producer.exact.pin(raw)})
        for imported_name, imported in list(sys.modules.items()):
            if imported_name == 'xar_autoplayer' or imported_name.startswith('xar_autoplayer.'):
                path = getattr(imported, '__file__', None)
                if path:
                    producer.require(Path(path).resolve().is_relative_to(producer.BASE_ROOT.resolve()),
                                     'production import escaped original source15: '+imported_name)
        report['status'] = 'SOURCE_INTEGRITY_AND_IMPORT_PASS_NOT_ADOPTED'
        report['qualification'] = {
            'full_parent_rows_checked': 1454, 'unchanged_parent_rows': 1453,
            'helper_exact_insertion_inverse_compile_AST': 'PASS',
            'candidate_helper_import_against_original_source15_dependencies': 'PASS',
            'actual_dependency_pins': dependency_paths,
            'functional_M0_tests_reused_not_repeated': 3, 'M0_original_result_tool': '50b77d',
            'prior_five_cross_package_57_M7_10_WAL_12_timing_matrices_repeated': False,
            'new_functional_tests_or_Game_calls': 0, 'Root_writer_recipe_executed': False,
            'test_scratch_files': 0, 'Git_D_Task_Game_Native_writes': 0,
            'actual_H': 'unknown', 'actual_seconds_saved': None,
        }
        return report
    finally:
        sys.path.remove(str(producer.BASE_ROOT))
        for name in list(sys.modules):
            if name == 'xar_autoplayer' or name.startswith('xar_autoplayer.'):
                del sys.modules[name]


def freeze():
    card = producer.source_commitment()
    now = datetime.now(timezone.utc)
    producer.require(now < datetime.fromisoformat(card['review_at_utc']), 'source commitment review expired')
    paths = [producer.REPO/PROOF, producer.REPO/PLAN]
    producer.require(all(not path.exists() for path in paths), 'frozen addon proof or plan already exists')
    report = qualify()
    encode = lambda doc: (json.dumps(doc, ensure_ascii=False, indent=2)+'\n').encode()
    proof_raw = encode(report)
    sources = [{'path': str(producer.REPO/name), **producer.exact.pin((producer.REPO/name).read_bytes())}
               for name in OWN_FILES]
    proof_pin = {'path': str(producer.REPO/PROOF), **producer.exact.pin(proof_raw)}
    plan = {
        'schema': 'xar.c19.same-speed-audit-addon-frozen-source-plan/v1',
        'machine_id': producer.MACHINE, 'observed_at_utc': now.isoformat(),
        'machine_source': 'tools/ck3_live_run_id.py machine; tool329d4e',
        'status': 'SOURCE_FROZEN_FUTURE_COLD_NOT_ADOPTED',
        'producer': sources[0], 'qualifier': sources[1], 'qualification': proof_pin,
        'entry': 'prepare_c19_same_speed_audit_addon_v1.compose() -> one changed byte leaf, full1454 rows, small proof; no writes.',
        'base': {'freeze': report['actual_source15_base'], 'business_commit': producer.BASE,
                 'family_fix': report['family_fix_preserved']},
        'immutable_parent': report['parent'], 'output': {'complete_manifest': report['complete_manifest'],
            'delta_from_parent': 1, 'unchanged_parent_rows': 1453, 'delta_from_actual_source15': 16,
            'nine_new_seven_existing_changes_1438_unchanged_original': True,
            'prospective_dual_changed_data4096cluster_upper': 4177920},
        'one_delta': report['delta_from_parent'][0], 'operation': report['operation'],
        'prior_fifteen_delta_rows_unchanged': True, 'epoch_source_model': report['epoch_source_model'],
        'epoch_reason': report['epoch_unchanged_reason'],
        'semantics': report['semantics'], 'reused_M0_proof': report['reused_M0_functional_qualification'],
        'qualification_scope': report['qualification'],
        'Root_canonical_recipe': {'call': 'canonical_anchor_with_root_writer(Root_git_writer, anchor_ref=NEW_REF, root_release_sha256=exact_new_release_SHA)',
            'parent_commit': producer.PARENT, 'create_only_ref': producer.NEW_REF,
            'new_blob': report['delta_from_parent'][0]['after']['git_blob_sha1'],
            'behavior': 'Root writes one helper blob and only its ancestor trees/new commit/ref; all sibling entries retained. Old65f branch/master/index/checkout untouched.',
            'executed_by_source_qualification': False,
            'requires': 'Separate Root Git-object budget/release and then exact new commit capacity card; this source card authorizes neither.'},
        'future_controls_business_adapter': {
            'owner': 'perf_harness; new files preserve frozen prior controls',
            'required': ['Bind this new plan SHA and fullrows443af to the new Root addon commit, not old65f',
                         'Validate old65f/a91 provenance and one493573 helper delta; complete_files remains1454',
                         'Preserve familyd8bb/M7/WAL/M2 and unchanged epoch3642; no extra SDK leaf',
                         'Keep genuinely enabled M7 custody graph, Native30 transition and separately chosen FULL timing'],
            'old_control_source_or_runtime_changed': False},
        'boundaries': {'D_Git_Task_Game_RPC_writes': 0, 'Driver_SAVE_ledger_body_reads': 0,
            'full_Driver_or_SDK_copy_output': False, 'Native30_qualification_added': 0,
            'actual_H': 'unknown', 'actual_performance_credit': None,
            'historical_F94_recovery_or_turn_bundle_copy_optimization_included': False,
            'M0_source_test_copied_or_doublecharged': False},
        'storage': {'source_card': {'path': str(producer.SOURCE_CARD), **dict(zip(('bytes', 'sha256'), producer.CARD_PIN))},
            'hard_bytes': producer.SOURCE_CAP, 'owned_retained_files_excluding_this_plan': sources+[proof_pin],
            'total_retained_logical_including_this_plan': 0, 'new_scratch_bytes': 0,
            'allocated_bytes': None, 'physical_release_credit_bytes': 0, 'future_writes_after_freeze': 0,
            'review_at_utc': card['review_at_utc'], 'small_record_review_at_utc': (now+timedelta(days=180)).isoformat()},
        'remaining': ['Root review and separate new create-only canonical anchor',
                      'New controls business pins and real Native30 qualification/transition',
                      'Exact then-cold inputs/capacity/admission and actual custody/H/performance evidence'],
    }
    retained = sum(row['bytes'] for row in sources)+len(proof_raw)
    while True:
        raw = encode(plan); total = retained+len(raw)
        if total == plan['storage']['total_retained_logical_including_this_plan']:
            break
        plan['storage']['total_retained_logical_including_this_plan'] = total
    producer.require(total <= producer.SOURCE_CAP, 'complete addon source package exceeds96KiB')
    with paths[0].open('xb') as stream:
        stream.write(proof_raw)
    with paths[1].open('xb') as stream:
        stream.write(raw)
    return {'qualification': proof_pin, 'plan': {'path': str(paths[1]), **producer.exact.pin(raw)},
            'producer': sources[0], 'qualifier': sources[1], 'complete_source_bytes': total,
            'full_rows': report['complete_manifest'], 'epoch_model': producer.EPOCH}


if __name__ == '__main__':
    if sys.argv[1:] == ['--freeze']:
        print(json.dumps(freeze(), ensure_ascii=False, indent=2))
    else:
        producer.require(not sys.argv[1:], 'only --freeze or no arguments')
        print(json.dumps(qualify(), ensure_ascii=False, indent=2))
