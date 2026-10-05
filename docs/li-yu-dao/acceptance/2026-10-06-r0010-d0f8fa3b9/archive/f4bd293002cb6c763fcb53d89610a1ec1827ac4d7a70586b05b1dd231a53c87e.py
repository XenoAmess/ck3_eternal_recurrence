from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'
PRIOR = BASE / 'r10-test-report-draft-20261005-004'
OUT = BASE / 'r10-incremental-evidence-ledger-through150-20261006-001'
PROFILE = '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'
SESSION = '53bd96329c5541f7a403c5cecf61d8ba'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def dump_new(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

assert not OUT.exists(), 'Refusing to overwrite an existing evidence package'
refs = {row['path']: row for row in read_json(PRIOR / 'SOURCE-REFS.json')['files']}
new_paths = []

def pin(path):
    path = Path(path)
    assert path.suffix.lower() != '.ck3', 'Save bodies are not copied or reparsed by this ledger'
    rel = path.relative_to(BASE).as_posix()
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), rel
    row = {'path': rel, 'bytes': len(data), 'sha256': sha(data), 'stat_unchanged_during_read': True}
    if rel in refs:
        assert (refs[rel]['bytes'], refs[rel]['sha256']) == (row['bytes'], row['sha256'])
    else:
        new_paths.append(rel)
    refs[rel] = row
    return row, data

def package(directory, expected_index=None, selected_only=False):
    directory = BASE / directory
    ref, raw = pin(directory / 'INDEX.json')
    if expected_index:
        assert ref['sha256'] == expected_index
    index = json.loads(raw.decode('utf-8-sig'))
    for row in index['files']:
        if selected_only and not (row['path'].startswith(('REPORT', 'TYPED-FACTS', 'PROPOSAL-OPENED-FACTS', 'CONTROL-EVIDENCE', 'LINEAGE-EVIDENCE'))):
            continue
        actual, _ = pin(directory / row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
    return ref

def pin_directory(directory):
    for path in sorted(Path(directory).iterdir()):
        if path.is_file():
            pin(path)

for name in ['INDEX.json', 'SOURCE-REFS.json', 'SDK1-55-EVIDENCE.json', 'REPORT.json', 'REPORT.md']:
    pin(PRIOR / name)
for row in read_json(PRIOR / 'INDEX.json')['files']:
    if row['path'] in ['SOURCE-REFS.json', 'SDK1-55-EVIDENCE.json', 'REPORT.json', 'REPORT.md']:
        actual = refs[(PRIOR / row['path']).relative_to(BASE).as_posix()]
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
ledger = list(read_json(PRIOR / 'SDK1-55-EVIDENCE.json')['results'])
assert len(ledger) == 55
native_values = {}
new_bytes = 0
for sequence in range(56, 151):
    matches = list(SDK.glob(f'{sequence:04d}-*.response.json'))
    assert len(matches) == 1
    response_path = matches[0]
    response_ref, raw = pin(response_path)
    response = json.loads(raw.decode('utf-8-sig'))
    assert response['sequence'] == sequence and response['status'] == 'MCP_RESULT_RECORDED'
    prefix = response_path.name[:-len('.response.json')]
    request_ref, raw = pin(SDK / (prefix + '.request.json'))
    request = json.loads(raw.decode('utf-8-sig'))
    assert request_ref['sha256'] == response['request_sha256']
    started_ref, _ = pin(SDK / (prefix + '.started.json'))
    sdk_ref, raw = pin(SDK / response['sdk_result'])
    assert sdk_ref['sha256'] == response['sdk_result_sha256']
    sdk = json.loads(raw.decode('utf-8-sig'))
    error = sdk.get('isError', sdk.get('is_error'))
    assert error is not True
    new_bytes += sdk_ref['bytes']
    native_refs = []
    for item in response.get('native_receipts', []):
        actual, raw = pin(SDK / item['copy'])
        assert actual['sha256'] == item['sha256']
        value = json.loads(raw.decode('utf-8-sig'))
        if value.get('profile_sha256') is not None:
            assert value['profile_sha256'] == PROFILE
        if value.get('session_id') is not None:
            assert value['session_id'] == SESSION
        native_values[sequence] = value
        native_refs.append({'ref': actual, 'original_native_path': item['path'],
                            'status': value.get('status'), 'profile_sha256': value.get('profile_sha256'),
                            'native_session_id': value.get('session_id')})
    assert native_refs
    ledger.append({'sequence': sequence, 'request_id': request['request_id'],
        'operation': request['operation'], 'tool': request.get('name'), 'arguments': request.get('arguments'),
        'response_status': response['status'], 'response_is_error': response.get('is_error'),
        'SDK_explicit_error_flag': error, 'request': request_ref, 'response': response_ref,
        'started': started_ref, 'sdk': sdk_ref, 'native_receipts': native_refs,
        'started_utc': response['started_at_utc'], 'finished_utc': response['finished_at_utc']})
    pin_directory(RUN / 'root-explicit-mcp-requests' / request['request_id'])
    local_stdio = RUN / 'root-call-stdio' / request['request_id']
    if local_stdio.is_dir():
        pin_directory(local_stdio)

readback_specs = [
 ('r10-actual-second-post-sign-readback-20261005-001', '823fad359a3394f5538b948a39657b5b416ccbbc79feb26cefd58967a7c67e4c', 8, 'REJECTED_RESULT2', 57),
 ('r10-actual-third-before-readback-20261005-001', 'ea1be27380db9f59eacc1e6842cf270887a1940b9ec9a4fdfc766e92f31cc323', 8, 'EXPLICIT_RESET_BEFORE', 63),
 ('r10-actual-third-open-join-readback-20261005-001', '98dd1157870b267cf15ef2b28258e3066c335bfc96f91ccb41c9a32ba3d3f258', 9, 'PROPOSAL_OPENED', 68),
 ('r10-actual-third-post-cancel-readback-20261005-001', '653b4be1efb09e72760bf8381de94345e63291a132511cd7f1dbb9b11fa362c9', 9, 'CANCELLED_RESULT3', 82),
 ('r10-actual-fourth-open-join-readback-20261005-001', '3c0811d784761325f41e45b327dd3bc949dd95b95e04075a9e6f6e60deff831f', 10, 'PROPOSAL_OPENED', 88),
 ('r10-actual-fourth-post-cancel-readback-20261005-001', '3966d4a212ba2efe1fdce454b0d1c99bec3937529273017e78f5088c8d232fa0', 10, 'CANCELLED_RESULT3', 107),
 ('r10-actual-fifth-open-join-readback-20261005-001', '44c0bf5edc6e03c8cf5e1589ee8854842b12359449e5b9862b0d50ee79a20ba0', 11, 'PROPOSAL_OPENED', 111),
 ('r10-actual-fifth-post-cancel-readback-20261005-001', '78b4b12f716e3a89905596b1fd82546e5c583f9dc6b4b9aac7ad8a09ec797202', 11, 'CANCELLED_RESULT3', 125),
 ('r10-actual-sixth-open-join-readback-20261005-001', '9d725b7c8695f3a037f4061ff8729b4256d56f5d9fb1d308c5837dd10b572ac4', 12, 'PROPOSAL_OPENED', 129),
]
readbacks = []
for directory, index_sha, nonce, status, sequence in readback_specs:
    index = package(directory, index_sha, selected_only=True)
    report = read_json(BASE / directory / 'REPORT.json')
    assert report['final_JOIN_credit'] is False
    checks = report.get('binding_and_protection_checks', report.get('all_binding_and_protection_checks'))
    assert checks is not None and all(checks.values())
    readbacks.append({'package_index': index,
        'report': refs[f'{directory}/REPORT.json'], 'declared_status': report['status'],
        'nonce': nonce, 'stage': status, 'save_SDK_sequence': sequence,
        'binding_and_protection_check_count': len(checks),
        'all_declared_checks_true': True, 'final_JOIN_credit': False,
        'AST_reread_or_parser_called_by_ledger': False})

lineage_specs = [
 ('r10-actual-first-release-lineage-independent-review-20261005-002', '98fb96035455b111ce2774c81a0285cf2fd4f5f5c094c11055d73ba5b0a82f20'),
 ('r10-actual-second-consumption-release-lineage-independent-review-20261005-001', '5768eaea896731cb879d4d604c6f79a184ed756aceb93c8745d38fec73beea3b'),
 ('r10-actual-third-consumption-release-lineage-independent-review-20261005-001', 'dca4616739c4ffb97d6b021a6f4d2da71eafcc75bf6986f37575f348170f9d0b'),
 ('r10-actual-fourth-consumption-release-lineage-independent-review-20261005-001', 'ccb5f0c6160af6f6b84c4d547bdd63e0a05397391d810c76e327778eb1935168')]
lineages = [{'index': package(directory, expected), 'report': refs[f'{directory}/REPORT.json']}
            for directory, expected in lineage_specs]
for ordinal in ['second', 'third', 'fourth', 'fifth']:
    package(f'r10-{ordinal}-proposal-emitted-evidence-20261005-002')
    for step in ['bind', 'emit', 'release']:
        pin_directory(RUN / f'root-{ordinal}-consumption-{step}-invocation-001')
    pin_directory(RUN / f'root-{ordinal}-consumption-host-request-001')

# Only append new immutable action files. Previous ordinal0/1 bytes in prior refs
# remain authenticated by prior INDEX and are not all rehashed by this ledger.
actions = RUN / 'native-state/native-session/ordinary-interaction-actions'
for path in sorted(actions.iterdir()):
    if path.is_file() and path.relative_to(BASE).as_posix() not in refs:
        pin(path)

log_index = package('r10-log-checkpoint108-readonly-review-20261005-001',
    '6604b1765aa1b82f699542167ba72992a8ac9b0fbc79a7e228d4bb248645a0c7', selected_only=True)
log_report = read_json(BASE / 'r10-log-checkpoint108-readonly-review-20261005-001/REPORT.json')
assert log_report['whole_final_log_credit'] is False

package('lyd-r10-proposal-input-assembler-20261005-002',
        '465a71a42e98e0d6d86107cb1d9bb0f55fdf624f8c6b0e8dfabcd9183267bf46')
assembler_rejection_index = package('r10-proposal-assembler-independent-review-20261005-001',
        'f3c2ee7d3bd9dbda4aa3ff5099e94030469d4da267b8fca5171100b8c8f54c2f')
rejection = read_json(BASE / 'r10-proposal-assembler-independent-review-20261005-001/REPORT.json')
assert rejection['qualified_for_ROOT_reuse'] is False
assembler3_index = package('lyd-r10-proposal-input-assembler-20261006-003',
        '9e1b6d82d36a67a75e9c22e0875d5bf028939c7fd571bcd3db7573adb4784ca7')
assert refs['lyd-r10-proposal-input-assembler-20261006-003/assemble_proposal_inputs.py']['sha256'] == 'aeecd4f13521f0056934887deb2d2e4173002ba82f8477ae91ca2ee2388a114e'

for filename in ['root_r10_one_explicit_small_call_v3_20261005.py',
                 'root_r10_one_explicit_small_call_v4_20261005.py',
                 'root_r10_wait_read_response_20261005.py',
                 'root-r10-caller-v4-source-receipt-20261005.json']:
    pin(BASE / filename)
assert refs['root_r10_one_explicit_small_call_v4_20261005.py']['sha256'] == '79a011ccaf87a5626a3d42034316cbc558a2f5d649a1381c6897c4fdddd411f8'
local_pending_path = RUN / 'root-call-stdio/r10-0143-sixth-final-review-detail/1.stdout.bin'
local_pending = read_json(local_pending_path)
assert local_pending['status'] == 'RESPONSE_STILL_PENDING_NO_RETRY'
assert ledger[141]['sdk']['bytes'] == 5894299
assert ledger[141]['sdk']['sha256'] == '654b00c7336b0c1c7b7806cc74f107f44c907fbb9631cbcce1ee5eacd16d4957'
assert ledger[141]['request_id'] == 'r10-0143-sixth-final-review-detail'
assert ledger[142]['request_id'] == 'r10-0144-sixth-detail-readback'
assert ledger[143]['request_id'] == 'r10-0145-sixth-final-review-confirm'
assert len(list(SDK.glob('*-r10-0143-sixth-final-review-detail.response.json'))) == 1
duration = (datetime.fromisoformat(ledger[141]['finished_utc']) - datetime.fromisoformat(ledger[141]['started_utc'])).total_seconds()
orphan_args_ref, _ = pin(RUN / 'root-explicit-arguments/0144-sixth-final-review-confirm.json')
assert not list((RUN / 'mcp-queue-002').glob('r10-0144-sixth-final-review-confirm*'))
assert not list(SDK.glob('*-r10-0144-sixth-final-review-confirm.*'))

checkpoint_path = RUN / 'checkpoints/0149-sixth-post-cancel-save/checkpoint-metadata.json'
checkpoint_ref, _ = pin(checkpoint_path)
checkpoint = read_json(checkpoint_path)
assert checkpoint['save']['bytes'] == 91537192
assert checkpoint['save']['sha256'] == '5ab8d308bd2f3858388f86cc34289683c30cf8efa43515283c001421c40affe1'
assert checkpoint['sdk']['sha256'] == ledger[148]['sdk']['sha256']
assert checkpoint['actual_public_revision'] == 70 and checkpoint['actual_native_revision'] == 69
ordinary = native_values[150]['result']['character_interaction_ordinary_context']
assert native_values[150]['result']['queried_revision'] == 70
assert native_values[150]['result']['queried_native_revision'] == 69
assert ordinary['date_raw'] == 53144712 and ordinary['game_pid'] == 13436
assert ordinary['can_send'] is True and ordinary['ready_to_initiate'] is True
assert ordinary['active_event_present'] is False and ordinary['incoming_interaction_present'] is False
assert ledger[149]['sdk']['sha256'] == '27fff1d1a7533e83d39b72684a33f43a637c1dbb56110f0d9fe1c8cbfb8534ee'
selection = native_values[146]['result']['event_selection']
assert selection['selected_option_number'] == 5 and selection['selected_native_option_index'] == 4
event147 = native_values[147]['result']['current_event_window_context']
assert event147['current_event_instance_id'] == 77 and event147['event_definition_key'] == 'lyd.228'

summary = {
    'schema': 'lyd.r10.incremental-evidence-ledger-through150.v1',
    'status': 'IN_PROGRESS_NOT_GREEN_INCREMENT_ONLY_NO_FULL_REPORT',
    'sealed_utc': datetime.now(timezone.utc).isoformat(), 'SDK_cutoff': 150,
    'last_request_id': ledger[149]['request_id'], 'previous_draft4_index': refs[f'{PRIOR.name}/INDEX.json'],
    'newly_read_SDK_sequences': [56, 150], 'new_SDK_count': 95, 'new_raw_SDK_bytes': new_bytes,
    'SDK_recorded_count_through_cutoff': 150, 'readback_packages': readbacks,
    'independent_lineage_packages': lineages,
    'runtime_current': {'public_revision': 70, 'native_revision': 69, 'date_raw': 53144712,
        'PID': 13436, 'wallet': {'gold': 1543, 'piety': 5650, 'prestige': 2200},
        'ordinary_can_send': True, 'ordinary_ready': True, 'active_event_present': False,
        'current_query': ledger[149]['sdk']},
    'fourth_proposal': {'nonce': 10, 'terminal_saved_result': 3, 'terminal_stage': 'CANCELLED', 'JOIN_credit': False},
    'fifth_proposal': {'nonce': 11, 'terminal_saved_result': 3, 'terminal_stage': 'CANCELLED', 'JOIN_credit': False},
    'sixth_proposal': {'nonce': 12, 'withdraw_selection_recorded': True,
        'withdraw_public_option': 5, 'withdraw_native_index': 4,
        'typed_ACK': 'lyd.228', 'ACK_selection_recorded': True,
        'actual_post_cancel_save_metadata': checkpoint_ref, 'actual_save': checkpoint['save'],
        'independent_post_cancel_AST_seal': 'PENDING', 'independent_final_result': None,
        'JOIN_credit': False},
    'completed_R10_JOIN_count': 0, 'completed_history_joins1_detaches2_are_prior_saved_history': True,
    'fullcycle_credit': False,
    'local_wait142': {'ROOT_request': ledger[141]['request_id'],
        'v3_wait_seconds': 20, 'local_result': local_pending,
        'local_pending_raw': refs[local_pending_path.relative_to(BASE).as_posix()],
        'local_wrapper_failure': 'ROOT_REPORTED_AND_SOURCE_ASSERTION_INFERRED; no separate raw caller exit receipt fabricated',
        'actual_original_sdk_result': ledger[141]['sdk'], 'actual_original_sdk_status': 'MCP_RESULT_RECORDED',
        'actual_started_utc': ledger[141]['started_utc'], 'actual_finished_utc': ledger[141]['finished_utc'],
        'actual_duration_seconds': duration, 'same_action_replayed': False,
        'next_readonly_query143': ledger[142]['request'], 'later_confirm144': ledger[143]['request'],
        'orphan0144_original_confirm_arguments': orphan_args_ref,
        'orphan0144_confirm_enqueued': False,
        'v4_source': refs['root_r10_one_explicit_small_call_v4_20261005.py'], 'v4_readonly_wait_seconds': 45},
    'helper_source_reviews': {'assembler002_independent_rejection': assembler_rejection_index,
        'assembler002_status': rejection['status'], 'accepted_invalid_metadata_cases': 4,
        'assembler002_qualified_for_live_proofs': False,
        'assembler003_index': assembler3_index, 'assembler003_author_directed_checks': 28,
        'assembler003_independent_review': 'PENDING', 'assembler003_live_assemble_execution': False},
    'latest_log_evidence': {'cutoff': 108, 'index': log_index,
        'raw_error_log_sha256': log_report['raw_error_log']['sha256'],
        'whole_final_credit': False, 'cap_reached': None, 'truncation': None,
        'continuous_runtime_coverage': None},
    'normal_exit': 'NOT_RUN', 'SDK_Client_closed': False, 'keeper_FINAL': None,
    'lease_released': False, 'source_freeze_released': False,
    'no_full_report_rewrite': True, 'old_draft_or_failed_attempt_overwrite': False,
    'new_AST_parses_by_ledger': 0, 'old_AST_or_tests_rerun': False,
    'main_Git_game_native_Client_pipe_bus_mutations': False,
}
OUT.mkdir()
dump_new(OUT / 'SDK1-150-EVIDENCE.json', {'schema': 'lyd.r10.actual-sdk-result-ledger.v4',
    'cutoff': 150, 'newly_read_sequences': [56, 150], 'inherited_sdk1_through55': refs[f'{PRIOR.name}/SDK1-55-EVIDENCE.json'],
    'new_sdk_raw_bytes': new_bytes, 'results': ledger})
dump_new(OUT / 'SOURCE-REFS.json', {'schema': 'lyd.r10.incremental.actual-source-refs.v1',
    'SDK_cutoff': 150, 'inherited_previous_index': refs[f'{PRIOR.name}/INDEX.json'],
    'new_reference_paths': new_paths, 'files': sorted(refs.values(), key=lambda row: row['path'])})
dump_new(OUT / 'LEDGER-SUMMARY.json', summary)
TEXT = '''# R10 增量证据 ledger：截止 SDK150（2026-10-06）

这是一次外置增量索引，**IN_PROGRESS／NOT_GREEN，0个本轮成功JOIN，fullcycle=false**；不重写完整验收报告，不改冻结草稿001–004，最终报告仍等实际正常退出与ROOT最终cutoff。

SDK1–55继承004封存索引；只新增读取SDK56–150，共95项真实MCP结果，逐项绑定request／started／response／原SDK／native-copy的bytes和SHA。读取原件不调用任何工具服务，未执行AST解析、旧测试、Client／pipe／游戏／总线／Git操作。

本次保存与独立后验追加：第二提案nonce8签署拒绝result2；第三nonce9正常选取消、保存result3；第四nonce10、第五nonce11均正常native选择取消、独立保存result3。各轮开案、取消及source签署状态各有自己的sealed包，NPC票identity省略保留NULL，旧票不沿用到新nonce；钱与prior completed history未新增成功业务。原保存中的joins1／detaches2属于本局加载的既有历史，不能计为R10成功循环。

第六nonce12开案129独立包32checks已封。SDK146（ROOT0147）在event76选择public option5／native index4 withdraw→event77；SDK147 typed query明确lyd.228，SDK148 ACK后无event，SDK149实际保存 **91,537,192B／SHA `5ab8d308bd2f3858388f86cc34289683c30cf8efa43515283c001421c40affe1`**。第六post-cancel独立AST尚未sealed，本ledger不使用reader初报，保存result、保护检查及最后独立业务结果维持pending／NULL。

SDK150（ROOT0151）真实fresh ordinary query **SHA `27fff1d1a7533e83d39b72684a33f43a637c1dbb56110f0d9fe1c8cbfb8534ee`**，public70／native69／date53144712，PID13436，钱包1543G／5650P／2200prestige，CanSend／ready=true、active／incoming=false。可发资格不自动给下一次host release、permit消费或新提案信用。

SDK142与本地等待的边界：ROOT request0143通过v3实际入队一次。20秒只读等待的原stdout为`RESPONSE_STILL_PENDING_NO_RETRY`，v3随后要求MCP_RESULT_RECORDED的本地调用失败仍保留；没有单独raw caller退出回执时，不伪造exitcode或错误文件。原SDK142在 **34.057316秒** 后实际完成，**5,894,299B／SHA `654b00c7336b0c1c7b7806cc74f107f44c907fbb9631cbcce1ee5eacd16d4957`**，native结果verified_selected_detail；没有重发原选择。

ROOT0144后来是新的只读detail query（SDK143），ROOT0145才是新的confirm（SDK144）。0144原confirm arguments文件留存但没入queue／SDK。v4只把只读等待20→45秒，源码SHA **`79a011ccaf87a5626a3d42034316cbc558a2f5d649a1381c6897c4fdddd411f8`**；延长本地观察不等于重试或改变业务。

helper002源码独立审查拒绝HELPER_QUERY_METADATA_GATES_INCOMPLETE：4项无效metadata被接受，缺少同frame provenance／正actor及alive、ctx alive门禁，还有output alias缺口；旧作者PASS与真实独立拒绝均保留，002不作为live proofs。003追加修正、作者28项定向检查PASS，但独立审查仍pending，尚未实际prepare／assemble任何live refs。源码检查不外推为真实permit／业务执行。

追加实际emit/release与ordinal继承的独立索引，按各自save nonce变化和旧claim／permit不可变SHA记录；没有把pending ACK写成JOIN。日志证据仍只到checkpoint108的138,556B快照：578条I4 unused诊断，cap／truncation／后续持续coverage未知，不补造后续日志覆盖。

Client、profile与lease未关闭，normalexit NOT_RUN，keeper FINAL／sourcefreeze解除未发生。本索引封存后保持原样，之后真实第六AST或退出收据应另追加证据包。
'''
write_new(OUT / 'NOTES-zh.md', TEXT.encode('utf-8'))
for filename in [Path(__file__).name, 'inspect_r10_incremental_ledger150_20261006_001.py']:
    write_new(OUT / 'source' / filename, (BASE / filename).read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.incremental-ledger-index.v1', 'files': files})
for row in files:
    data = (OUT / row['path']).read_bytes()
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
print(json.dumps({'status': summary['status'], 'path': str(OUT), 'reference_count': len(refs),
    'new_reference_count': len(new_paths), 'new_SDK_count': 95, 'new_SDK_bytes': new_bytes,
    'sixth_AST': 'PENDING_UNSEALED', 'summary_sha256': sha((OUT / 'LEDGER-SUMMARY.json').read_bytes()),
    'notes_sha256': sha((OUT / 'NOTES-zh.md').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=False))
