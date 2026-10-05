from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
PRIOR = BASE / 'r10-test-report-draft-20261005-002'
OUT = BASE / 'r10-test-report-draft-20261005-003'
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'
NEGATIVE = BASE / 'r10-actual-post-source-sign-readback-20261005-001'
PROFILE_SHA = '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'
NATIVE_SESSION = '53bd96329c5541f7a403c5cecf61d8ba'


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


if OUT.exists():
    raise SystemExit('Refusing to overwrite an existing report revision')
# Only new SDK26-38 and new source evidence are read. Prior refs remain the
# immutable prior records, authenticated by the prior INDEX below.
refs = {row['path']: row for row in read_json(PRIOR / 'SOURCE-REFS.json')['files']}
new_paths = []


def preserve_ref(path):
    path = Path(path)
    relative = path.relative_to(BASE).as_posix()
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), relative
    row = {'path': relative, 'bytes': len(data), 'sha256': sha(data), 'stat_unchanged_during_read': True}
    if relative in refs:
        assert refs[relative]['bytes'] == row['bytes'] and refs[relative]['sha256'] == row['sha256']
    else:
        new_paths.append(relative)
    refs[relative] = row
    return row, data


for name in ['INDEX.json', 'REPORT.md', 'REPORT.json', 'SDK1-25-EVIDENCE.json', 'SOURCE-REFS.json']:
    preserve_ref(PRIOR / name)
prior_index = read_json(PRIOR / 'INDEX.json')
for row in prior_index['files']:
    if row['path'] in ['REPORT.md', 'REPORT.json', 'SDK1-25-EVIDENCE.json', 'SOURCE-REFS.json']:
        actual = refs[(PRIOR / row['path']).relative_to(BASE).as_posix()]
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
prior_ledger = read_json(PRIOR / 'SDK1-25-EVIDENCE.json')['results']
ledger = list(prior_ledger)
new_sdk_bytes = 0
for sequence in range(26, 39):
    matches = list(SDK.glob(f'{sequence:04d}-*.response.json'))
    assert len(matches) == 1, (sequence, len(matches))
    response_path = matches[0]
    response_ref, response_data = preserve_ref(response_path)
    response = json.loads(response_data.decode('utf-8-sig'))
    assert response['sequence'] == sequence and response['status'] == 'MCP_RESULT_RECORDED'
    prefix = response_path.name[:-len('.response.json')]
    request_ref, request_data = preserve_ref(SDK / (prefix + '.request.json'))
    request = json.loads(request_data.decode('utf-8-sig'))
    assert request_ref['sha256'] == response['request_sha256']
    started_ref, _ = preserve_ref(SDK / (prefix + '.started.json'))
    sdk_ref, sdk_data = preserve_ref(SDK / response['sdk_result'])
    assert sdk_ref['sha256'] == response['sdk_result_sha256']
    sdk_value = json.loads(sdk_data.decode('utf-8-sig'))
    sdk_error = sdk_value.get('isError', sdk_value.get('is_error'))
    assert sdk_error is not True
    new_sdk_bytes += sdk_ref['bytes']
    natives = []
    for native in response.get('native_receipts', []):
        native_ref, native_data = preserve_ref(SDK / native['copy'])
        assert native_ref['sha256'] == native['sha256']
        value = json.loads(native_data.decode('utf-8-sig'))
        if value.get('profile_sha256') is not None:
            assert value['profile_sha256'] == PROFILE_SHA
        if value.get('session_id') is not None:
            assert value['session_id'] == NATIVE_SESSION
        natives.append({'ref': native_ref, 'original_native_path': native['path'],
                        'status': value.get('status'), 'profile_sha256': value.get('profile_sha256'),
                        'native_session_id': value.get('session_id')})
    ledger.append({'sequence': sequence, 'request_id': request['request_id'],
                   'operation': request['operation'], 'tool': request.get('name'),
                   'arguments': request.get('arguments'), 'response_status': response['status'],
                   'response_is_error': response.get('is_error'), 'SDK_explicit_error_flag': sdk_error,
                   'request': request_ref, 'response': response_ref, 'started': started_ref,
                   'sdk': sdk_ref, 'native_receipts': natives,
                   'started_utc': response['started_at_utc'], 'finished_utc': response['finished_at_utc']})
assert ledger[29]['request_id'] == 'r10-0031-review-again-query'
assert ledger[30]['request_id'] == 'r10-0032-post-source-sign-save'
assert ledger[37]['request_id'] == 'r10-0039-current-ready-query'
for path in sorted((RUN / 'root-explicit-mcp-requests/r10-0030-review-again-query').iterdir()):
    if path.is_file():
        preserve_ref(path)
rejected = read_json(RUN / 'root-explicit-mcp-requests/r10-0030-review-again-query/request.json')
assert rejected['name'] == 'ck3_query_profile_decision_v1'
assert not list((RUN / 'mcp-queue-002').glob('r10-0030-review-again-query*'))
assert not list(SDK.glob('*-r10-0030-review-again-query.*'))
filetime_ref, filetime_raw = preserve_ref(RUN / 'root-process-filetime-001/PROCESS-IDENTITY.actual.json')
filetime = json.loads(filetime_raw.decode('utf-8-sig'))
assert filetime['pid'] == 13436 and filetime['creation_filetime_100ns'] == 134356699957422997
assert filetime['handle_closed'] is True and filetime['normal_exit_original_handle_retained'] is False
preserve_ref(RUN / 'checkpoints/0031-post-source-sign-save/checkpoint-metadata.json')
checkpoint = read_json(RUN / 'checkpoints/0031-post-source-sign-save/checkpoint-metadata.json')
assert checkpoint['save']['bytes'] == 91532053
assert checkpoint['save']['sha256'] == '885393b25bca235361e0d2a242bb2791eaa5d578ef03ed9c849c0849370fc4d4'
assert checkpoint['sdk']['sha256'] == ledger[30]['sdk']['sha256']
# The independently authored package must be sealed before this report seals.
negative_index = read_json(NEGATIVE / 'INDEX.json')
preserve_ref(NEGATIVE / 'INDEX.json')
preserve_ref(NEGATIVE / 'REPORT.json')
preserve_ref(NEGATIVE / 'REPORT-zh.md')
negative_report = read_json(NEGATIVE / 'REPORT.json')
assert refs[(NEGATIVE / 'REPORT.json').relative_to(BASE).as_posix()]['sha256'] == 'd6639a0ba10bc7608328340b7153e653bf519687521b5db872178e3e0f10c4c1'
assert negative_report['status'] == 'ACTUAL_RESULT2_REJECTED_NO_JOIN_TRANSITION_OR_FEE'
assert negative_report['final_JOIN_credit'] is False
assert len(negative_report['binding_and_protection_checks']) == 32
assert all(negative_report['binding_and_protection_checks'].values())
for row in negative_index['files']:
    if row['path'] in ['REPORT.json', 'REPORT-zh.md', 'REASON-EVIDENCE.json']:
        actual, _ = preserve_ref(NEGATIVE / row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
for key in ['typed_facts', 'pair_diff_report']:
    if key in negative_report:
        declared = negative_report[key]
        actual, _ = preserve_ref(Path(declared['path']))
        assert (actual['bytes'], actual['sha256']) == (declared['bytes'], declared['sha256'])
query38 = read_json(SDK / '0038-r10-0039-current-ready-query.native-01.json')
current = query38['result']['character_interaction_ordinary_context']
assert current['shown'] is True and current['can_send'] is True and current['ready_to_initiate'] is True
assert current['active_event_present'] is False and current['incoming_interaction_present'] is False
assert current['date_raw'] == 53144712 and current['game_pid'] == 13436
assert query38['result']['queried_revision'] == 17 and query38['result']['queried_native_revision'] == 16
assert query38['business_effects_verified'] is False
report = read_json(PRIOR / 'REPORT.json')
report.update({
    'revision': 3, 'utc': datetime.now(timezone.utc).isoformat(),
    'status': 'IN_PROGRESS_NOT_GREEN_SAVED_SIGNATURE_REJECTION_FIRST_JOIN_FALSE',
    'evidence_cutoff': 'ROOT-authorized actual SDK sequences1-through38; only26-through38 newly read',
    'previous_report_index_sha256': refs[(PRIOR / 'INDEX.json').relative_to(BASE).as_posix()]['sha256'],
    'SDK_count_through_cutoff': 38, 'SDK_result_recorded_count': 38,
    'sdk_new26_through38_raw_bytes': new_sdk_bytes,
    'sdk_total_raw_bytes': report['sdk_total_raw_bytes'] + new_sdk_bytes,
    'process_creation_FILETIME': filetime,
    'process_FILETIME_receipt': filetime_ref,
    'normal_exit_retained_handle_credit_from_FILETIME': False,
    'actual_post_source_sign_save': checkpoint['save'],
    'source_signature_rejection_report': refs[(NEGATIVE / 'REPORT.json').relative_to(BASE).as_posix()],
    'negative_saved_facts': {
        'result': 2, 'source_signed': 1, 'target_requested': 1, 'target_signed': None,
        'target_signed_presence': 'ABSENT', 'source_total': 2, 'source_yes': 2,
        'target_total': 1, 'target_yes': 1, 'player_total': 1, 'player_yes': 1,
        'actor_vote_and_player_nonce': 7, 'active_presence': 'ABSENT',
        'Rite169_retry_cooldown': {'value': 1, 'tick': 365},
        'historical_lock_serial7_retained': True, 'Rite169_owner_lock_released': True,
        'Rite159_owner_lock_released': True, 'Faith_Rite_affiliations_changed': False,
        'wallet_changed': False, 'stage': 'SIGNATURE_ACCEPTANCE_REJECTION',
        'route_proof': 'FROZEN_SOURCE_PLUS_SAVE_INFERENCE',
        'target_ballot_rejection_claim': False, 'AI_option_execution_trace': None,
        'specific_random_branch': None},
    'business_final_JOIN_credit': False,
    'first_JOIN_terminal_business_outcome': 'REJECTED_AT_SIGNATURE_STAGE_SAVED_RESULT2',
    'later_fresh_query38': {
        'request_id': ledger[37]['request_id'], 'sequence': 38, 'public_revision': 17,
        'native_revision': 16, 'date_raw': 53144712, 'shown': True, 'can_send': True,
        'ready_to_initiate': True, 'active_event_present': False, 'incoming_interaction_present': False,
        'new_proposal_initiated_credit': False, 'host_consumption_or_release_credit': False},
    'prequeue_bad_request': {
        'request_id': rejected['request_id'], 'wrong_tool': rejected['name'],
        'enqueue_validation_exit_code': 1, 'SDK_sequence': None, 'entered_queue': False,
        'actual_sequence30_request_id': ledger[29]['request_id']},
})
for row in report['matrix']:
    if row['area'] == 'formalrepeat':
        row.update({'status': 'FIRST_JOIN_SIGNATURE_REJECTION_SAVED_RESULT2_RESET_DONE_READY38_NO_NEW_PROPOSAL',
                    'JOIN1': {'proposal_opened': True, 'source_signature_operation_recorded': True,
                              'final_result': 'SIGNATURE_REJECTED_RESULT2', 'final_credit': False},
                    'DETACH': None, 'JOIN2': None})
    if row['area'] == 'livebaseline':
        row['actual_post_source_sign_checkpoint'] = checkpoint['save']
    if row['area'] == 'normalexit':
        row['FILETIME_read_only_handle_closed'] = True
        row['FILETIME_is_original_retained_exit_handle'] = False
OUT.mkdir()
dump_new(OUT / 'SOURCE-REFS.json', {'schema': 'lyd.r10.report.actual-source-refs.v3',
                                  'source_cutoff_sequence': 38,
                                  'inherited_previous_index': refs[(PRIOR / 'INDEX.json').relative_to(BASE).as_posix()],
                                  'new_reference_paths': new_paths,
                                  'files': sorted(refs.values(), key=lambda row: row['path'])})
dump_new(OUT / 'SDK1-38-EVIDENCE.json', {'schema': 'lyd.r10.actual-sdk-result-ledger.v2',
                                      'cutoff': 38, 'newly_read_sequences': [26, 38],
                                      'inherited_sdk1_through25_index': refs[(PRIOR / 'SDK1-25-EVIDENCE.json').relative_to(BASE).as_posix()],
                                      'new_sdk_raw_bytes': new_sdk_bytes, 'results': ledger})
dump_new(OUT / 'REPORT.json', report)
TEXT = '''# R10 实机验收进度草稿 003（2026-10-05）

当前状态为 **进行中／NOT_GREEN：first JOIN 在签署接收阶段拒绝，保存result2，最终 JOIN 信用仍false**。本修订只追加真实SDK26–38、保存31的独立负向读回、进程FILETIME及入队前错误工具名拒绝；SDK1–25及预检／源码／构建／旧失败引用由冻结002的INDEX继承，不重新解析旧大保存或复跑旧检查。001／002保持原样。

`SDK1-38-EVIDENCE.json`明确列出SDK sequence与request ID，`SOURCE-REFS.json`记录新增原件bytes／SHA及前继索引。cutoff为实际SDK38：当前新提案尚未发起，后续live结果不纳入或猜测。整个新稿只写外置新文件，没有main／Git／game／Client／pipe／bus操作。

## 真实签署操作及保存结果

SDK26查询review event47=`lyd.220`。SDK27在该事件选择public option1（source签署），之后出现event48=`lyd.228`；SDK28取得该ACK上下文，SDK29选ACK后无active event。真实SDK30的review决议查询得到requested key不在actual rows／available=false；不能据决议消失猜测成功。

实际SDK31（request ID `r10-0032-post-source-sign-save`）保存并由ROOT保全 `checkpoints/0031-post-source-sign-save/checkpoint.ck3`，91,532,053字节，SHA `885393b25bca235361e0d2a242bb2791eaa5d578ef03ed9c849c0849370fc4d4`。原SDK SHA `0ae847445f65ec3aac099f5dbbc45272e6809ff13641e37b40e11b1aa3a9259b`，public revision15／native14，date53144712／1066.10.1、paused、PID13436。读回包单次AST解析此保存，之后复用缓存；本稿没有再解析或复制90MB本体。

独立保存读回的当前事实：result2，source_signed1、target_requested1，target_signed字段缺失；source2／2、target1／1、player1／1，发起者本轮vote与player票据nonce7；active字段缺失。Rite169 retry cooldown存在、value1／tick365，Rite159／169的owner locks释放，历史lock_serial7仍保留；Faith／Rite归属与钱包不变。**这属于签署接收阶段的拒绝，不是target ballot未达标或拒绝。** 接收签署receive_no route是冻结源码加保存状态的推断，不是独立AI选项执行trace。target_signed缺失不擅改为0；没有实际随机分支回执，具体随机原因保持NULL。

0016开案保存中的旧玩家票nonce6早于SDK20，本稿由0031的新本轮7票据追加其后事实，旧0016不追写。先前PROPOSAL_OPENED、YES回调及source签署操作都是真实阶段证据，不能把这些阶段或`.228`ACK合并成最终JOIN成功。first JOIN仍false，joins／detaches没有新成功业务信用，后续DETACH／JOIN2／完整循环仍NOT_RUN。

## 入队前拒绝与序号错位

原ROOT request `r10-0030-review-again-query`使用错误工具名 `ck3_query_profile_decision_v1`，enqueue的validate_request拒绝，exit1；request／argv／stderr／invocation原件保留。它没有进入SDK queue，也没有SDK result或业务dispatch，不能伪造SDK0030失败返回。

| 真实SDK sequence | 实际request ID／操作 |
| --- | --- |
| 26 | r10-0026-review-event-query |
| 27 | r10-0027-source-sign |
| 28 | r10-0028-sign-ack-query |
| 29 | r10-0029-sign-ack-select |
| 30 | **r10-0031-review-again-query**：正确decision-item query，review行不存在 |
| 31 | **r10-0032-post-source-sign-save**：真实保存31 |
| 32 | r10-0033-current-join-query |
| 33 | r10-0034-reset-query |
| 34 | r10-0035-reset-select |
| 35 | r10-0036-reset-confirm |
| 36 | r10-0037-reset-ack-query |
| 37 | r10-0038-reset-ack-select |
| 38 | **r10-0039-current-ready-query** |

SDK33–37是实际显式fixture reset→ACK event49的流程，不能给自然冷却到期信用。SDK38 ordinary query真实shown／CanSend／ready_to_initiate=true，active event与incoming interaction均false，actor31254／recipient65866，public revision17／native16／date53144712，精确profile／native session／PID一致。query仍business_effects_verified=false／full_product_acceptance_credit=false；当前可发资格不等于新提案已发，也不等于旧claim消费证明、host release permit或新的独立意图完成。

## FILETIME身份证据的边界

`root-process-filetime-001/PROCESS-IDENTITY.actual.json`实际读取PID13436／creation1791196395.7422996，raw creation FILETIME **134356699957422997**，access4096，调用OpenProcess／GetProcessId／GetProcessTimes／CloseHandle。回执handle_closed=true、normal_exit_original_handle_retained=false，无gameplay／OCR／desktop输入。

这是一份只读进程身份回执，不能当作正常退出的原保留HANDLE。原进程身份可以用于后续明确的receipt字段绑定，但本局normalexit request、原HANDLE终态、clientclose、keeper FINAL、CASrelease、sourcefreeze释放均未在本修订发生，继续NULL／NOT_RUN。

## 当前验收矩阵与保留的原结果

| 项目 | cutoff38结论 |
| --- | --- |
| preflight | fresh离线审图及check-only002通过；旧appmanifest／request SHA／launch001大小写参数及002receipt-path拒绝全部保留 |
| source | 固定d0f8 clean export／70production及SOURCE_ONLY review；原9profile不改，派生10field含exit inventory。主树冻结未解除 |
| build | Release编译PASS与Defender单次Add设置失败并存；原外层RED／exit1、effectiveness未证，不改写 |
| livebaseline | original PID13436／creation／HWND、MCP epoch002／Client19428及13／16／31保存均有精确绑定；FILETIME新增仅身份读回 |
| formalrepeat | first JOIN开案／YES／source签署发生，31保存签署拒绝result2；最终JOINfalse。reset／ready38发生，新的提案未发；DETACH／JOIN2／fullcycle NOT_RUN |
| I3b | 正式common32／动态Faith完整同意→签署→宗主创建及actualHoR后验NOT_RUN／NULL |
| C3 | 正式challenger／withdraw→register／双challenger／death／followership NOT_RUN／NULL，teacher不等于HoR |
| practice | 本局修习、实际XP／stress差额、自然冷却、五校／三负例实机NOT_RUN／NULL |
| I4 | 静态144产品矩阵／夹具准备保留，native cases0；不能把fixture日志或ACK当业务PASS |
| reload | post-reset before13及后续提案／拒绝保存实际读回；业务后冷重载／reconcile NOT_RUN |
| normalexit | 十字段source inventory已准备，FILETIME查询句柄已关闭；正常退出与全生命周期闭合未执行 |

SDK1–38只证明逐项回执所声明的状态；签署拒绝是实际负向业务结果，不给整个产品或所有负例GREEN。具体stage的result2与target ballots1／1分开记录，避免把拒绝误报成初始投票失败。

原冷载16文件日志前缀578条／289签名I4 unused-variable，仅有该前缀分类证据；本稿未读取当前增长日志，没有wholefinal或本轮所有业务无新错结论。exactd0f8礼与道CI159／static70／repro实际成功，通用CI仍两docs历史名称2violations失败。两文件中性称谓候选仍外置等待R10闭合后ROOT合回及CI复验，不改当前冻结源。

后续ROOT实际新提案、后保存、负向原因收据、独立verifier、claim release、日志或退出事实必须进入新的revision。这个003 seal后保持原字节，旧失败和旧NOT_GREEN不覆盖。
'''
write_new(OUT / 'REPORT.md', TEXT.encode('utf-8'))
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.external-report-draft-index.v3', 'files': files})
print(json.dumps({'status': 'R10_REPORT_DRAFT_003_SEALED_NOT_GREEN', 'path': str(OUT),
                  'reference_count': len(refs), 'new_reference_count': len(new_paths),
                  'new_sdk_count': 13, 'new_sdk_raw_bytes': new_sdk_bytes,
                  'report_md_sha256': sha((OUT / 'REPORT.md').read_bytes()),
                  'report_json_sha256': sha((OUT / 'REPORT.json').read_bytes()),
                  'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=False))
