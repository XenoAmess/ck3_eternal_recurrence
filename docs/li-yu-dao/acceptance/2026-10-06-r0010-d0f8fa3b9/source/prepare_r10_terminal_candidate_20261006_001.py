from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'
OUT = BASE / 'r10-terminal-report-candidate-20261006-001'
PRIOR = BASE / 'r10-incremental-evidence-ledger-151-200-20261006-001'
BOUNDARY = BASE / 'r10-root-actual-closed-boundary-20261006-001'
PROFILE = '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'
SESSION = '53bd96329c5541f7a403c5cecf61d8ba'
HEAD = 'd0f8fa3b9d444828759443aa018bfd7ad31b398d'
LANDING = 'docs/li-yu-dao/acceptance/2026-10-06-r0010-d0f8fa3b9'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def dump_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

assert not OUT.exists(), 'Append new candidate only'
prior_index_raw = (PRIOR / 'INDEX.json').read_bytes()
assert sha(prior_index_raw) == '86bd947e189d54240e695d5b977329f9537ab660ee71fb1218b0e09b625f22cf'
prior_index = json.loads(prior_index_raw.decode('utf-8-sig'))
for name in ['SOURCE-REFS.json', 'LEDGER-SUMMARY.json']:
    data = (PRIOR / name).read_bytes()
    row = next(row for row in prior_index['files'] if row['path'] == name)
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
refs = {row['path']: dict(row) for row in load(PRIOR / 'SOURCE-REFS.json')['files']}
old_paths = set(refs)
new_paths = []
json_cache = {}
package_records = []

def add_indexed(path, size, digest, basis):
    path = Path(path)
    if path.suffix.lower() == '.ck3':
        return None
    origin = path.relative_to(BASE).as_posix()
    if origin in refs:
        assert (refs[origin]['bytes'], refs[origin]['sha256']) == (size, digest), origin
    else:
        refs[origin] = {'path': origin, 'bytes': size, 'sha256': digest,
                        'hash_verification_basis': basis, 'body_read_this_final_assembly': False}
    return refs[origin]

def pin(path):
    path = Path(path)
    assert path.suffix.lower() != '.ck3', 'No checkpoint bodies read/hash/parse/copy'
    origin = path.relative_to(BASE).as_posix()
    if origin in refs:
        return refs[origin], None
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), origin
    refs[origin] = {'path': origin, 'bytes': len(data), 'sha256': sha(data),
                   'stat_unchanged_during_read': True, 'body_read_this_final_assembly': True}
    new_paths.append(origin)
    return refs[origin], data

def known_json(path):
    path = Path(path)
    key = str(path)
    if key not in json_cache:
        row, raw = pin(path)
        if raw is None:
            # Small metadata/report only; never use this function on old SDK,
            # typed AST or save bodies.
            assert path.name in {'INDEX.json', 'INDEX-final.json', 'REPORT.json',
                                 'LEDGER-SUMMARY.json', 'checkpoint-metadata.json'}, path
            raw = path.read_bytes()
            assert (len(raw), sha(raw)) == (row['bytes'], row['sha256'])
        json_cache[key] = json.loads(raw.decode('utf-8-sig'))
    return json_cache[key]

def pin_direct_files(directory):
    directory = Path(directory)
    if directory.is_dir():
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() != '.ck3':
                pin(path)

def package(directory, expected):
    directory = BASE / directory
    row, data = pin(directory / 'INDEX.json')
    assert row['sha256'] == expected
    if data is None:
        data = (directory / 'INDEX.json').read_bytes()
        assert sha(data) == expected
    index = json.loads(data.decode('utf-8-sig'))
    added = []
    for item in index['files']:
        actual = add_indexed(directory / item['path'], item['bytes'], item['sha256'],
                             'Authenticated sealed package INDEX ' + expected)
        if actual is not None:
            added.append(actual['path'])
    record = {'package': directory.relative_to(BASE).as_posix(), 'index': row,
              'indexed_payload_count': len(index['files']), 'payload_origins': added,
              'full_index_metadata_reused_without_AST_or_old_SDK_body_read': True}
    package_records.append(record)
    return record

for path in [PRIOR / 'INDEX.json', PRIOR / 'SOURCE-REFS.json', PRIOR / 'LEDGER-SUMMARY.json', PRIOR / 'NOTES-zh.md',
             BASE / 'r10-incremental-evidence-ledger-through150-20261006-001/SOURCE-REFS.json',
             BASE / 'r10-incremental-evidence-ledger-through150-20261006-001-addendum-001/NEW-SOURCE-REFS.json']:
    pin(path)

boundary_ref, boundary_raw = pin(BOUNDARY / 'PREVIOUS-BOUNDARY.actual.json')
assert (boundary_ref['bytes'], boundary_ref['sha256']) == (3360, '898fd997fbbaac6bb127a5d8f9f080077baf545b24b990db7d6d4c6811b6000c')
boundary = json.loads(boundary_raw.decode('utf-8-sig'))
assert boundary['source_head'] == HEAD and boundary['status'] == 'ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY'
for key, row in boundary.items():
    if isinstance(row, dict) and {'path', 'bytes', 'sha256'} <= row.keys():
        actual, data = pin(row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
        if data is not None and Path(row['path']).suffix.lower() == '.json':
            json_cache[str(Path(row['path']))] = json.loads(data.decode('utf-8-sig'))
closure = json_cache[str(Path(boundary['closure']['path']))]
assert closure['process_exit_observed'] and closure['exit_code'] == 0 and closure['typed_normal_exit_observed']
assert closure['client_exit_code'] is None and closure['keeper_exit_code'] is None
assert closure['client_ended'] and closure['keeper_ended']
absence = json_cache[str(Path(boundary['process_absence']['path']))]
assert absence['all_ck3_processes_absent'] and absence['all_consumer_processes_ended'] and absence['all_keeper_processes_ended']
keeper = json_cache[str(Path(boundary['keeper_final']['path']))]
assert keeper['thread_exited'] and keeper['failure'] is None and keeper['last_sequence'] == 3160
freeze = json_cache[str(Path(boundary['source_freeze_release']['path']))]
assert freeze['source_freeze_released'] and freeze['screen_release_sequence'] == 3161
pin_direct_files(BOUNDARY)
for row in [absence.get('earlier_win32_probe')]:
    if row:
        actual, _ = pin(row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
for directory in [BASE / 'screen-lease-live-r0010',
                  BASE / 'r10-final-screen-release-invocation-20261006-001',
                  BASE / 'r10-final-after-list-invocation-20261006-001',
                  BASE / 'r10-after-client-close-process-readback-20261006-001']:
    pin_direct_files(directory)

ledger = []
native_values = {}
new_sdk_bytes = 0
for sequence in range(201, 255):
    matches = list(SDK.glob(f'{sequence:04d}-*.response.json'))
    assert len(matches) == 1, sequence
    response_path = matches[0]
    response_ref, response_raw = pin(response_path)
    response = json.loads(response_raw.decode('utf-8-sig')) if response_raw is not None else load(response_path)
    assert response['sequence'] == sequence
    prefix = response_path.name[:-len('.response.json')]
    request_ref, request_raw = pin(SDK / (prefix + '.request.json'))
    request = json.loads(request_raw.decode('utf-8-sig'))
    assert request_ref['sha256'] == response['request_sha256']
    started_ref, _ = pin(SDK / (prefix + '.started.json'))
    sdk_ref = None
    sdk_error = None
    natives = []
    not_copied_native_refs = []
    if sequence == 254:
        assert response['status'] == 'CLIENT_CLOSE_REQUESTED' and response.get('sdk_result') is None
    else:
        assert response['status'] == 'MCP_RESULT_RECORDED'
        sdk_ref, sdk_raw = pin(SDK / response['sdk_result'])
        assert sdk_raw is not None and sdk_ref['sha256'] == response['sdk_result_sha256']
        sdk_value = json.loads(sdk_raw.decode('utf-8-sig'))
        sdk_error = sdk_value.get('isError', sdk_value.get('is_error'))
        new_sdk_bytes += sdk_ref['bytes']
        for item in response.get('native_receipts', []):
            if item.get('status') == 'NOT_COPIED':
                # The original raw receipt is retained separately and pinned;
                # do not invent a copied-native SHA absent from the response.
                original = Path(item['path'])
                actual, native_raw = pin(original)
                not_copied_native_refs.append({'response_declared_status': 'NOT_COPIED',
                    'response_reason': item.get('reason'), 'actually_preserved_original': actual})
            else:
                actual, native_raw = pin(SDK / item['copy'])
                assert actual['sha256'] == item['sha256']
            value = json.loads(native_raw.decode('utf-8-sig'))
            if value.get('profile_sha256') is not None:
                assert value['profile_sha256'] == PROFILE
            if value.get('session_id') is not None:
                assert value['session_id'] == SESSION
            result = value.get('result') or {}
            natives.append({'ref': actual, 'original_native_path': item['path'],
                'status': value.get('status'), 'reason': value.get('reason'),
                'result_status': result.get('status'),
                'postcondition_verified': result.get('postcondition_verified'),
                'business_effects_verified': result.get('business_effects_verified'),
                'profile_sha256': value.get('profile_sha256'), 'native_session_id': value.get('session_id')})
            if sequence not in native_values or 'result' in value:
                native_values[sequence] = value
    ledger.append({'sequence': sequence, 'request_id': request['request_id'],
        'operation': request['operation'], 'tool': request.get('name'), 'arguments': request.get('arguments'),
        'response_status': response['status'], 'response_is_error': response.get('is_error'),
        'SDK_explicit_error_flag': sdk_error, 'request': request_ref, 'response': response_ref,
        'started': started_ref, 'sdk': sdk_ref, 'native_receipts': natives,
        'response_NOT_COPIED_original_receipts': not_copied_native_refs,
        'started_utc': response['started_at_utc'], 'finished_utc': response['finished_at_utc']})
    pin_direct_files(RUN / 'root-explicit-mcp-requests' / request['request_id'])
    pin_direct_files(RUN / 'root-call-stdio' / request['request_id'])
assert len(ledger) == 54 and sum(row['sdk'] is not None for row in ledger) == 53
collection = BASE / 'r10-terminal-report-collection-20261006-001'
collection.mkdir(exist_ok=False)
dump_new(collection / 'COLLECTION.json', {'schema': 'lyd.r10.once-terminal-sdk-collection.v1',
    'ledger': ledger, 'refs': refs, 'new_paths': new_paths, 'new_sdk_bytes': new_sdk_bytes,
    'native_values': {str(key): value for key, value in native_values.items()},
    'all53_new_raw_SDK_hash_assertions_completed': True, 'old1_200_body_read': False})
collection_data = (collection / 'COLLECTION.json').read_bytes()
dump_new(collection / 'INDEX.json', {'schema': 'lyd.r10.once-collection-index.v1', 'files': [
    {'path': 'COLLECTION.json', 'bytes': len(collection_data), 'sha256': sha(collection_data)}]})
pin(collection / 'INDEX.json')
pin(collection / 'COLLECTION.json')

# Preserve new directly held claims/normal-exit dispatch observations and
# original consumer/session closure markers. Inherited old objects are not reread.
for directory in ['root-explicit-arguments', 'native-state/native-session/normal-exit-map-requests',
                  'native-state/native-session/ordinary-interaction-actions',
                  'native-state/native-session/ingame-decision-item-actions',
                  'native-state/native-session/ingame-decisions-opener-actions']:
    pin_direct_files(RUN / directory)
for filename in ['session.json', 'session-closed.json']:
    pin(SDK / filename)
for seq in [235, 240]:
    matches = list((RUN / 'checkpoints').glob(f'{seq:04d}-*/checkpoint-metadata.json'))
    assert len(matches) == 1
    pin(matches[0])

package('r10-actual-detach-second-precommit-readback-20261006-001',
        'a3053a70763a8e2a76e580aabb77c1f1cf2cb33a624e53ce8b77f1f99bda5d62')
package('r10-actual-detach-second-post-readback-20261006-001',
        '1d2170e5e97044d8546e78b9b2f3d1c45b880ea9a57bfcc7a54688a5cd67d304')
package('r10-log-preterminal-cut244-readonly-review-20261006-001',
        '255ebf66babbe0f559e7328ba7fe09199ccb34ca5a340f91ff65073ef92285aa')
detach = known_json(BASE / 'r10-actual-detach-second-post-readback-20261006-001/REPORT.json')
assert detach['final_DETACH_credit'] and len(detach['all_binding_and_protection_checks']) == 120 and all(detach['all_binding_and_protection_checks'].values())
precommit = known_json(BASE / 'r10-actual-detach-second-precommit-readback-20261006-001/REPORT.json')
logs = known_json(BASE / 'r10-log-preterminal-cut244-readonly-review-20261006-001/REPORT.json')

# Expand authenticated old package index metadata so permanently retained
# graph diff/source/RED payloads are not accidentally lost merely because an
# incremental narrative selected fewer reports. No old body/AST scan.
processed_indexes = set()
while True:
    pending = [row for row in refs.values() if row['path'] not in processed_indexes and
               Path(row['path']).name in {'INDEX.json', 'INDEX-final.json'}]
    if not pending:
        break
    for row in pending:
        processed_indexes.add(row['path'])
        index_path = BASE / row['path']
        raw = index_path.read_bytes()
        assert (len(raw), sha(raw)) == (row['bytes'], row['sha256'])
        value = json.loads(raw.decode('utf-8-sig'))
        if not isinstance(value.get('files'), list):
            continue
        for item in value['files']:
            if not isinstance(item, dict) or not {'path', 'bytes', 'sha256'} <= item.keys():
                continue
            path = Path(item['path'])
            if not path.is_absolute():
                path = index_path.parent / path
            add_indexed(path, item['bytes'], item['sha256'], 'Authenticated package INDEX ' + row['sha256'])

last = native_values[244].get('result', {})
blocked = native_values[243]
assert blocked['status'] == 'RED' and 'already claimed with an unresolved result' in blocked['reason']
observed = json_cache[str(Path(boundary['original_handle_observation']['path']))]
assert observed['process_observation']['retained_handle_token'] == 'c3d6cb9a49b45eacdd12e64815c8f49a'
assert observed['native_submission_count'] == 0 and observed['typed_normal_exit_observed']
closed = json_cache[str(Path(boundary['consumer_closed']['path']))]
assert ledger[-1]['finished_utc'] < logs['logs'][0]['raw']['capture_started_utc']

summary = {'schema': 'lyd.r10.final.closed-report-candidate.v1',
    'status': 'R10_CLOSED_NOT_GREEN_PHASE1_INCOMPLETE', 'report_utc': datetime.now(timezone.utc).isoformat(),
    'source_HEAD': HEAD, 'stock_version': '1.20.0.3', 'original_pid': 13436,
    'original_process_creation_filetime_100ns': 134356699957422997,
    'business_cutoff_SDK': 244, 'final_MCP_cutoff_SDK': 253, 'client_close_sequence': 254,
    'new_SDK_sequences': [201, 253], 'new_SDK_count': 53, 'new_raw_SDK_bytes': new_sdk_bytes,
    'prior_SDK1_200_body_scans': 0, 'save_body_reads_hashes_or_AST_runs': 0,
    'business': {'R10_actual_final_JOIN_count': 1, 'R10_actual_final_DETACH_count': 1,
        'campaign_saved_JOINs': 2, 'campaign_saved_DETACHs': 3,
        'wallet_gold': 1043, 'wallet_piety': 3150, 'wallet_prestige': 2200,
        'JOIN14': {'save_sequence': 192, 'checks': 183, 'fee_gold': 300, 'fee_piety': 1500,
                   'moving_Rite169_parentFaith': 104, 'targetFaith104_mainRite': 159, 'oldFaith106_backupMainRite': 187},
        'DETACH16': {'precommit_sequence': 235, 'save_sequence': 240, 'checks': 120,
                     'fee_gold': 200, 'fee_piety': 1000, 'newFaith': 107, 'newFaith107_mainRite': 169,
                     'moving_Rite169_parentFaith': 107, 'moving_Rite169_HoR': 31254,
                     'newFaith107_HoF': None, 'newFaith107_head_title': None,
                     'moving_transition_CD_tick': 1825, 'reset_count': 6},
        'first_DETACH_201_216': {'native_withdraw_trace_preserved': True, 'independent_save': None,
                               'AST_result3_credit': False},
        'formal_second_JOIN': 'NOT_RUN', 'full_JOIN_DETACH_JOIN_cycle': 'NOT_COMPLETE',
        'natural_five_year_cooldown_expiry': 'NOT_RUN'},
    'failure_boundaries': {'SDK196_original_status': 'RED', 'SDK196_later_actual_reset200': True,
                          'SDK196_claim_verified': False, 'SDK243_original_status': blocked['status'],
                          'SDK243_exact_reason': blocked['reason'],
                          'SDK243_new_reset_dispatched': False, 'SDK243_claim_clear_or_overwrite': False,
                          'SDK244_fresh_noevent_public112_native111': True},
    'lifecycle': {'canonical_ROOT_boundary': boundary_ref, 'closure': boundary['closure'],
        'original_HANDLE_exit_code': 0, 'typed_normal_exit_observed': True,
        'original_retained_HANDLE_token': observed['process_observation']['retained_handle_token'],
        'observer_native_submission_count': 0, 'normal_exit_autosave_verified': False,
        'client_session_closed': True, 'client_OS_exit_code': None,
        'keeper_STOP_FINAL_thread_exited': True, 'keeper_failure': None,
        'keeper_OS_exit_code': None, 'keeper_last_sequence': 3160,
        'lease_CAS_after_sequence': 3161, 'lease_resource_list': [],
        'fresh_no_holder_list': boundary['after_list'], 'all_processes_absent': True,
        'source_freeze_released': True, 'source_freeze_release': boundary['source_freeze_release']},
    'logs': {'package': 'r10-log-preterminal-cut244-readonly-review-20261006-001',
             'directory_name_is_historical_not_capture_phase': True,
             'capture_phase_correction': 'ACTUAL_CAPTURE_POST_GAME_EXIT_AND_POST_CLIENT_SESSION_CLOSE',
             'capture_UTC': [row['raw']['capture_finished_utc'] for row in logs['logs']],
             'fixture_unused_records': 578, 'production_unused_records': 0,
             'runtime_effect_trigger_scope_error_records_in_captured_bytes': 0,
             'actual_other_W_records': 12, 'cap_reached': None, 'truncation': None,
             'continuous_late_runtime_log_coverage': None, 'whole_log_GREEN': False},
    'not_run': ['formal secondJOIN', 'R11 reloaded persistent evidence', 'C3 formal lord/challenger/death/reload',
                'I3b formal dynamicFaith ritual run', 'practice character-switch mutations', 'I4 formal144product cases'],
    'phase1_overall_complete': False, 'overall_PASS': False,
    'ROOT_only_main_import': True, 'main_Git_game_MCP_Client_pipe_lease_bus_mutations_by_author': False}

matrix = [
 {'area': '冻结源与静态L0', 'result': 'SOURCE_STATIC_PASS', 'boundary': '复用d0f8生产70、fixture52与已封159/static/repro；不授实机业务信用'},
 {'area': 'release实际编译', 'result': 'COMPILE_PASS_OUTER_BUILD_RED', 'boundary': '真实编译成功；Defender一次注册失败effectivenessfalse／outerexit1保留'},
 {'area': '通用CI', 'result': 'RED_REMEDIATION_CANDIDATE_ONLY', 'boundary': '两处历史文档名称最小修正候选外置；本包未应用或复跑CI'},
 {'area': 'launch预检与actual冷启', 'result': 'ACTUAL_ONE_CREATED_WITH_PRIOR_FAILED_ATTEMPTS', 'boundary': '001argcase／002refpathbug／nofork检查与003actualPID13436均保留'},
 {'area': '正式JOIN nonce14', 'result': 'ACTUAL_PASS_183CHECKS', 'boundary': '171opening、187三签授权、189commit、192保存分别绑定；-300G/-1500P'},
 {'area': '前七轮JOIN未成功', 'result': 'REJECTED_OR_CANCELLED_NOT_JOIN', 'boundary': '两次签署接收拒绝及五次取消，票identity省略保持NULL、不推随机原因'},
 {'area': '第一次DETACH withdraw201–216', 'result': 'NATIVE_TRACE_ONLY_NO_AST_RESULT', 'boundary': '没有独立保存，不倒填ASTresult3或结案信用'},
 {'area': '正式DETACH nonce16', 'result': 'ACTUAL_PASS_120CHECKS', 'boundary': '235授权、237commit、240保存；-200G/-1000P，new107/main169，HoR31254不等于HoF'},
 {'area': 'SDK196fixture与SDK243复位阻止', 'result': 'ORIGINAL_RED_PRESERVED', 'boundary': '196原调用RED但200实际reset；未验证claim使243在派发前阻止，未reset或clearclaim'},
 {'area': 'JOIN→DETACH→第二JOIN完整循环', 'result': 'NOT_COMPLETE_SECOND_JOIN_NOT_RUN', 'boundary': '下次session从actual240继续；本轮不授fullcycle'},
 {'area': '自然冷却到期／直接禁用观察', 'result': 'NOT_RUN_QUERY_LIMIT', 'boundary': 'fixture reset非自然到期；193action_qualified=false为恒值不证明CD拒绝'},
 {'area': 'I3b／C3／修习切人／I4正式矩阵／reload', 'result': 'NOT_RUN', 'boundary': '离线构建、sourceproof、inert helper不替代实际操作'},
 {'area': '同原HANDLE正常退出', 'result': 'ACTUAL_EXIT0_TYPED_PASS', 'boundary': '245query→246prepareunknown→247fresh→248stage→249continueunknown→250fresh→251query→252confirmonce→253原HANDLEobserver；autosaveverifiedfalse'},
 {'area': 'Client／keeper／lease／source freeze', 'result': 'ACTUAL_CLOSED_RELEASED_OS_EXIT_CODES_UNKNOWN', 'boundary': '254sessionclose+allabsent；keeperSTOPFINAL3160；CAS3161DONEresources[]；freshnoholder；ROOT释放源门禁；两OSexitcodeNULL'},
 {'area': '退出后error/debug日志', 'result': 'SNAPSHOT_CLASSIFIED_COVERAGE_UNKNOWN', 'boundary': 'UTC18:07真实postexit/clientclose捕获；578I4unused+12W保留；cap/truncation/continuouscoverageNULL，无wholeGREEN'},
 {'area': 'Phase1总体', 'result': 'NOT_GREEN_INCOMPLETE', 'boundary': '已完成本轮限定JOIN和DETACH并闭合生命周期；剩余验收未完成'}]

# External checkpoint registry is only small metadata. Do not read save bodies.
save_rows = {}
for path in sorted((RUN / 'checkpoints').glob('*/checkpoint-metadata.json')):
    seq = int(path.parent.name[:4])
    if seq > 244:
        continue
    origin = path.relative_to(BASE).as_posix()
    # Metadata may have been inherited without a direct source-ref; pin is cheap.
    row, data = pin(path)
    value = json.loads(data.decode('utf-8-sig')) if data is not None else load(path)
    for key in ['save', 'checkpoint', 'preserved_save']:
        item = value.get(key)
        if isinstance(item, dict) and {'path', 'bytes', 'sha256'} <= item.keys() and str(item['path']).lower().endswith('.ck3'):
            save_rows[item['path']] = {'SDK_sequence': seq, **item, 'metadata': row,
                                      'body_read_hashed_parsed_or_copied_by_report_author': False}
for save in [detach['save']]:
    save_rows[save['path']] = {'SDK_sequence': 240, **save, 'binding_report': 'r10-actual-detach-second-post-readback-20261006-001/REPORT.json',
                             'body_read_hashed_parsed_or_copied_by_report_author': False}

OUT.mkdir()
dump_new(OUT / 'SDK201-254-EVIDENCE.json', {'schema': 'lyd.r10.terminal.incremental-sdk201-254.v1',
    'MCP_range': [201, 253], 'close_marker_sequence': 254, 'results': ledger,
    'new_raw_SDK_bytes': new_sdk_bytes, 'old_SDK1_200_raw_body_scans': 0})
dump_new(OUT / 'REPORT.json', summary)
dump_new(OUT / 'RESULT-MATRIX.json', {'schema': 'lyd.r10.closed.result-matrix.v1', 'overall': 'NOT_GREEN_PHASE1_INCOMPLETE', 'rows': matrix})
dump_new(OUT / 'CHECKPOINT-EXTERNAL-INDEX.json', {'schema': 'lyd.r10.external-save-body-index.v1',
    'all_save_bodies_external_not_committed': True, 'save_body_verification_reused_only': True,
    'files': sorted(save_rows.values(), key=lambda row: row.get('SDK_sequence', 0))})
dump_new(OUT / 'LOG-TIMING-CORRECTION.json', {'schema': 'lyd.r10.append-only-log-phase-correction.v1',
    'unchanged_original_package': 'r10-log-preterminal-cut244-readonly-review-20261006-001',
    'unchanged_original_index_sha256': '255ebf66babbe0f559e7328ba7fe09199ccb34ca5a340f91ff65073ef92285aa',
    'reason': 'The old filename and parent-reported capture context were prepared while terminal receipts were unavailable. Actual finalized SDK253/254 timestamps precede the single actual18:07 capture.',
    'actual_game_exit_observed_SDK253_finished_utc': ledger[-2]['finished_utc'],
    'actual_client_close254_finished_utc': ledger[-1]['finished_utc'],
    'actual_log_capture': logs['logs'],
    'corrected_phase': 'POST_ACTUAL_GAME_EXIT_AND_POST_CLIENT_SESSION_CLOSE',
    'business_cut244_is_data_scope_not_capture_phase': True,
    'old_package_renamed_rewritten_or_live_logs_reread': False,
    'normal_exit_credit_based_on_logs': False, 'whole_log_GREEN_credit': False})
dump_new(OUT / 'SOURCE-REFS.json', {'schema': 'lyd.r10.final.import-original-byte-refs.v1',
    'source_HEAD': HEAD, 'old1_200_metadata_reused': True,
    'new_direct_hash_reference_count': len(new_paths), 'total_reference_count': len(refs),
    'sealed_package_records': package_records, 'files': sorted(refs.values(), key=lambda row: row['path'])})
origin_rows = []
objects = {}
for row in sorted(refs.values(), key=lambda row: row['path']):
    assert not row['path'].lower().endswith('.ck3')
    size = row['bytes']
    extension = Path(row['path']).suffix.lower()
    mode = 'gzip' if size >= 131072 or extension == '.log' else 'exact_copy'
    suffix = '.gz' if mode == 'gzip' else extension if extension in {'.md', '.json', '.txt', '.py', '.jsonl', '.csv'} else '.bin'
    target = 'archive/' + row['sha256'] + suffix
    object_key = row['sha256']
    if object_key in objects:
        previous = objects[object_key]
        assert previous['original_bytes'] == size and previous['storage_mode'] == mode
        target = previous['target_relative_path']
    else:
        objects[object_key] = {'source_absolute_path': str(BASE / row['path']),
            'source_relative_origin': row['path'], 'original_bytes': size, 'original_sha256': row['sha256'],
            'target_relative_path': target, 'storage_mode': mode,
            'stored_bytes': None if mode == 'gzip' else size,
            'stored_sha256': None if mode == 'gzip' else row['sha256'],
            'compressed_bytes_SHA_are_ROOT_import_actuals_not_fabricated': mode == 'gzip'}
    origin_rows.append({'origin': row['path'], 'original_bytes': size, 'original_sha256': row['sha256'],
                        'stored_relative_path': target, 'storage_mode': mode,
                        'verification_basis': row.get('hash_verification_basis', 'Actual direct immutable-byte SHA audit')})
dump_new(OUT / 'ORIGIN-MAP.plan.json', {'schema': 'lyd.r10.root-only-content-sha-origin-map-plan.v1',
    'status': 'ORIGINAL_BYTES_PINNED_STORED_GZIP_HASHES_PENDING_ROOT_COPY', 'files': origin_rows})

def link(origin, label):
    match = next(row for row in origin_rows if row['origin'] == origin)
    return '[' + label + '](' + match['stored_relative_path'] + ')'

TEXT = '''# 礼与道 R10 实机验收终局记录（2026-10-06）

**R10生命周期已实际闭合，Phase1总体仍NOT_GREEN／未完成。** 本局完成限定的一次正式JOIN与一次正式DETACH；第二JOIN、完整JOIN→DETACH→JOIN循环、R11冷载持久性与C3／I3b／修习切人／I4正式矩阵未执行。本报告允许保存真实RED与NOT_RUN，不把正常退出当业务总验收通过。

冻结源d0f8fa3b9d444828759443aa018bfd7ad31b398d，stock1.20.0.3，production70＋fixture52；本局actualPID13436、create1791196395.7422996、creationFILETIME134356699957422997。实际SDK1–253、254Client关闭标记均有原request／response／SDK／native／本地收据映射；requestId与sequence在原0030工具名拒绝后错位，仍按真实两个字段保存。历史报告001–004、cut150及149补充、151–200ledger和全部坏attempt不改。

## 业务结论

首次实际JOIN仅授给nonce14：171为opening，187为sourceSigned／targetRequested／targetSigned均1的三签授权，189正式commit→190 typed lyd.228→191ACK→192独立保存183检查。joins1→2／detaches2，扣300G／1500P，钱包1543／5650／2200→1243／4150／2200。Rite169 parentFaith106→104；Faith104 mainRite159是另一字段。actor31254及sourceNPC65865随169转104，targetNPC65866仍104／159。旧Faith106创建backupmainRite187，完整tenets与旧169一致；既有heads、完整tenets、政治7title、person、actorlanded与playable保护成立。169HoR31254、transitionCD1825、ownerreleased、reset5、XP0。保存body留外置，191ACK及193行查询本身不授结案／冷却禁用信用。

原前七轮仍分别保留：两次接收签署拒绝与五次取消；NPC票的identity省略保持NULL，不补0、不推随机draw或AI具体原因。171原owner-only RED及新增targetRite159合法当轮票counter资格证据分列，不能改写原失败或倒填precommit／final facts。

第一次DETACH的201–216实际事件／withdraw trace保留，但没有独立保存，**不倒填AST result3**。第二次nonce16：235独立source签署／source2of2／player1of1授权，237 formal native1／publicoption2→238 typed100 lyd.228→239ACK→240独立保存120检查。DETACH2→3、JOIN2保持，扣200G／1000P，钱包1243／4150／2200→1043／3150／2200。新Faith107 mainRite169，169 parentFaith104→107；旧104 main159及106 main187保留。169HoR31254，但107 HoF invalid／无headtitle，**不能称actor为HoF**。transitionCD1825、ownerrelease、reset6、XP0以及全registry合法关系／tenets／heads／政治7title／person／actorlanded／playable保护成立。仅本轮16记1次正式DETACH。

196fixture confirm原RED（actual frame crossed）完整保留；197独立观察／198typedfixture.4／199ACK／200保存证明操作实际reset5→6、169transitionCD删除，schoolCD349保持。未验证的原claim未清除或覆盖，因此243新的reset confirm在派发前被安全门拒绝：`decision action already claimed with an unresolved result; no retry at any revision`。**243无新reset派发**；244fresh仍public112／native111／noevent，钱包1043／3150／2200。不能把196后验reset改为原调用PASS，也不能把243改为fixture又成功。

第二JOIN本轮NOT_RUN，完整循环未完成；下次session可从actual240同campaign续测。显式fixture reset不等于自然五年到期。193action_qualified=false是serializer恒值，当前query没有enabled／is_valid字段，MCP直接禁用或CD rejection未观察；源码＋保存的CD资格推断另列。

## 实际生命周期闭合

245只读query→246prepareunknown→247freshsnapshot→248stage查询→249continueonceunknown→250freshsnapshot→251query→252confirmonce→253**同原retained HANDLE**只读observer。原HANDLEtoken c3d6cb9a49b45eacdd12e64815c8f49a，waitsignaled／exit0／typed_normal_exit=true，observer native_submission_count0并dispose；未知dispatch返回与后续真实终态分别记录，没有重发prepare／continue／confirm。autosave_verified=false，最后保全业务存档是240，不伪称退出autosave验证。

254实际Client close／sessionclosed，OS process census证明CK3／Client／keeper全absent。keeper STOP→FINAL thread_exited=true、failureNULL、lastseq3160；freshCAS3160→3161 DONE、resources[]，freshlist无holder，ROOT据实际闭合释放source freeze。**Client与keeper的OS exit code未实际取得，均NULL／UNKNOWN，不写0。** 原keeper FINAL里的screen_released=false是CAS前事实，不能单独替代后续3161 release收据。

## 日志与未完成范围

日志包名称r10-log-preterminal-cut244-readonly-review-20261006-001保持历史原样；最终收据证明其UTC18:07:35单次capture发生在18:04实际游戏退出及Client sessionclose**之后**。cut244表示业务数据范围，并非实际capture阶段；本报告追加时间勘误，不重写旧包或重读live日志。

新error.log138556B，SHA2da1ee0f6bb1469b250707790d0abd221d1b32f0e395ae221988cb3e1e59ed1a；debug.log666846B，SHAd8174957720cceaab1c1044c3defbdf1a8300037234f35d3c69141720b4a8460。578个完整unused记录／289签名各2次均绑定重新核SHA的I4fixture，production0；捕获字节内runtimeeffect／trigger／scope错误0。12条其他W（3bookmark＋9holyorder优先级）及账号无token、camera、占位材质等debug问题原样保留。**cap／truncation／后期持续coverage／flush完整性仍NULL，无whole日志GREEN或整体产品PASS。**

实际release编译成功，但outerbuildREDexit1／Defender一次注册失败effectivenessfalse保留；礼与道静态159／static70／repro属于已封sourceL0。通用CI两历史文档名称失败仍RED，最小两文件修正候选留外置，本包不改main或复跑CI。launch001argcase／002refpathbug、nofork检查与003actualonecreated、等待超时却后来返回而未重发、错误期待值、prequeue拒绝、reader期待key错误、helper002资格拒绝等各自保留并区分作者／reader／环境／业务来源。

C3宗主／挑战者／death／reload，I3b正式dynamicFaith仪式，修习切人四mutations，I4正式144product矩阵与R11冷载持久性均NOT_RUN。inert helper、离线构建、源码匹配和MCP ACK不能替代这些业务事实。

## 证据与导入

本候选只新增SDK201–253及254close原件核查，旧1–200 raw body／90MB存档／AST与旧测试不重扫。SOURCE-REFS复用旧ledger及认证sealed INDEX全部payload映射；所有大保存只列外置路径、bytes与历史SHA。ROOT-only importer按originalSHA短路径保留全部所列必要原件；原字节单次读、hash核对、lossless gzip并当场解压SHA验证，生成真实storedbytes／SHA和ORIGIN／INDEX，避免长路径与伪造压缩摘要。候选及旧失败均append保留，主树／Git／游戏操作仅ROOT执行。
'''
TEXT += '\n关键原件：' + '；'.join([
    link('r10-actual-eighth-post-join-readback-20261006-001/REPORT.json', '192 JOIN 183检查'),
    link('r10-actual-detach-second-precommit-readback-20261006-001/REPORT.json', '235授权'),
    link('r10-actual-detach-second-post-readback-20261006-001/REPORT.json', '240 DETACH 120检查'),
    link('r10-root-actual-closed-boundary-20261006-001/PREVIOUS-BOUNDARY.actual.json', 'ROOT终局边界'),
    link('r10-root-actual-closed-boundary-20261006-001/CLOSURE.actual.json', '生命周期闭合')]) + '。\n'
write_new(OUT / 'REPORT.md', TEXT.encode('utf-8'))
progress = '''礼与道R10（d0f8fa3b9／stock1.20.0.3）已实际正常退出并闭合Client、keeper、CAS3161与source freeze。本轮独立保存证明nonce14正式JOIN（183检查、300G／1500P）及nonce16正式DETACH（120检查、200G／1000P）；campaign历史2JOIN／3DETACH包含加载旧历史，R10新增各1次。最终钱包1043G／3150P／2200prestige，Rite169属于新Faith107／main169，HoR31254，107无HoF／headtitle。第二JOIN、完整循环、R11冷载持久性、C3／I3b／修习切人／I4正式矩阵仍未完成，Phase1总体NOT_GREEN。196原RED与后验actualreset、243before-dispatch阻止、外层build／通用CI失败及日志coverage未知均保留；Client／keeper OS exitcode为NULL。完整报告：[R10终局验收](acceptance/2026-10-06-r0010-d0f8fa3b9/REPORT.md)。
'''
write_new(OUT / 'README-PROGRESS-APPEND.md', progress.encode('utf-8'))
write_new(OUT / '.gitattributes', b'* -text\narchive/** -text\n')
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
dump_new(OUT / 'IMPORT-PLAN.json', {'schema': 'lyd.r10.root-only-permanent-import-plan.v1',
    'status': 'CONCRETE_ORIGINAL_SHA_COPY_PLAN_READY_FOR_ROOT', 'repository': 'C:/workspace/ck3_eternal_recurrence',
    'landing_relative_path': LANDING, 'candidate_directory': str(OUT),
    'require_ROOT_only_execution': True, 'append_new_target_only': True,
    'require_all_green': False, 'canonical_closed_boundary': boundary_ref,
    'objects': sorted(objects.values(), key=lambda row: row['target_relative_path']),
    'original_reference_count': len(origin_rows), 'unique_object_count': len(objects),
    'large_save_body_objects': 0, 'candidate_all_archive_bytes_already_copied': False,
    'compressed_stored_SHA_bytes_are_actual_generated_by_ROOT_importer': True})
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.terminal-report-candidate-index.v1', 'files': files})
print(json.dumps({'path': str(OUT), 'status': summary['status'], 'SDK_MCP_added': 53,
    'SDK254': 'CLIENT_CLOSE_REQUESTED_SESSION_MARKER', 'new_raw_SDK_bytes': new_sdk_bytes,
    'references': len(refs), 'unique_objects': len(objects), 'oldSDK_body_scan': 0,
    'report_sha256': sha((OUT / 'REPORT.json').read_bytes()),
    'report_md_sha256': sha((OUT / 'REPORT.md').read_bytes()),
    'plan_sha256': sha((OUT / 'IMPORT-PLAN.json').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=True))
