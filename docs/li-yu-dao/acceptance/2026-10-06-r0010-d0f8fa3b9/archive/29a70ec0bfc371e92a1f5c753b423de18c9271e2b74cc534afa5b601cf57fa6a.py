from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'
PRIOR = BASE / 'r10-test-report-draft-20261005-003'
OUT = BASE / 'r10-test-report-draft-20261005-004'
PROFILE_SHA = '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'
NATIVE_SESSION = '53bd96329c5541f7a403c5cecf61d8ba'
PERMIT_SHA = '6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84'
CLAIM_PREFIX = '8bfa5f050fb5b9b7f74d683c7a08ed76fdfbdce007bf582f6e3f5cba2be13a13'


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
refs = {row['path']: row for row in read_json(PRIOR / 'SOURCE-REFS.json')['files']}
new_paths = []


def preserve_ref(path):
    path = Path(path)
    assert path.suffix.lower() != '.ck3', 'No checkpoint-body reread or copy is authorized'
    relative = path.relative_to(BASE).as_posix()
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), relative
    row = {'path': relative, 'bytes': len(data), 'sha256': sha(data), 'stat_unchanged_during_read': True}
    if relative in refs:
        assert (refs[relative]['bytes'], refs[relative]['sha256']) == (row['bytes'], row['sha256'])
    else:
        new_paths.append(relative)
    refs[relative] = row
    return row, data


def check_declared_ref(declared):
    actual, data = preserve_ref(declared['path'])
    assert actual['sha256'] == declared['sha256']
    if 'bytes' in declared:
        assert actual['bytes'] == declared['bytes']
    return actual, data


def sealed_package(directory, expected_report_sha=None):
    directory = Path(directory)
    index_ref, raw = preserve_ref(directory / 'INDEX.json')
    index = json.loads(raw.decode('utf-8-sig'))
    for row in index['files']:
        actual, _ = preserve_ref(directory / row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
    if expected_report_sha is not None:
        assert refs[(directory / 'REPORT.json').relative_to(BASE).as_posix()]['sha256'] == expected_report_sha
    return index_ref


for name in ['INDEX.json', 'REPORT.md', 'REPORT.json', 'SDK1-38-EVIDENCE.json', 'SOURCE-REFS.json']:
    preserve_ref(PRIOR / name)
prior_index = read_json(PRIOR / 'INDEX.json')
for row in prior_index['files']:
    if row['path'] in ['REPORT.md', 'REPORT.json', 'SDK1-38-EVIDENCE.json', 'SOURCE-REFS.json']:
        actual = refs[(PRIOR / row['path']).relative_to(BASE).as_posix()]
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
ledger = list(read_json(PRIOR / 'SDK1-38-EVIDENCE.json')['results'])
assert len(ledger) == 38
new_sdk_bytes = 0
new_native_values = {}
for sequence in range(39, 56):
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
        new_native_values[sequence] = value
    assert natives, sequence
    ledger.append({'sequence': sequence, 'request_id': request['request_id'],
                   'operation': request['operation'], 'tool': request.get('name'),
                   'arguments': request.get('arguments'), 'response_status': response['status'],
                   'response_is_error': response.get('is_error'), 'SDK_explicit_error_flag': sdk_error,
                   'request': request_ref, 'response': response_ref, 'started': started_ref,
                   'sdk': sdk_ref, 'native_receipts': natives,
                   'started_utc': response['started_at_utc'], 'finished_utc': response['finished_at_utc']})
assert ledger[54]['request_id'] == 'r10-0056-receiving-sign-result-query'

before_dir = BASE / 'r10-actual-new-intent-before-readback-20261005-001'
second_dir = BASE / 'r10-actual-second-open-join-readback-20261005-001'
before_index = sealed_package(before_dir, '86838da8a9126df53ae6b557587a67821cfb5b61d0a84f3d30f55f19ba88880b')
second_index = sealed_package(second_dir, '4846d30c937881b47820c5682a276b170eee4f62a29ee007eeb274a4ec10f2df')
before_report = read_json(before_dir / 'REPORT.json')
second_report = read_json(second_dir / 'REPORT.json')
assert len(before_report['all_binding_and_protection_checks']) == 32
assert all(before_report['all_binding_and_protection_checks'].values())
assert before_report['natural_cooldown_expiry_credit'] is False
assert len(second_report['binding_and_protection_checks']) == 37
assert all(second_report['binding_and_protection_checks'].values())
assert second_report['final_JOIN_credit'] is False
facts_ref, facts_raw = check_declared_ref(second_report['typed_facts'])
facts = json.loads(facts_raw.decode('utf-8-sig'))
assert facts['actual_claim_ordinal'] == 1 and facts['first_ordinal0_claim_preserved'] is True
assert facts['actual_actionUUID'] == 'ordinary-interaction-a50373f260354f6f83c8052eaf837c7f'
assert facts['old_player_round7_ballot_or_consent_not_round8_credit'] is True
assert facts['saved_type_value_identity_omission_kept_null_not_zero'] is True

emission_dir = BASE / 'r10-first-proposal-emitted-evidence-20261005-004'
emission_index = sealed_package(emission_dir)
manifest = read_json(emission_dir / 'CONSUMPTION-MANIFEST.json')
emission_status = read_json(emission_dir / 'EMISSION-STATUS.json')
for key in ['packet', 'native_result', 'before_artifact', 'after_artifact', 'independent_report']:
    check_declared_ref(manifest[key])
check_declared_ref(emission_status['claim'])
check_declared_ref(emission_status['frozen_provider_index'])
assert emission_status['actual_host_release'] is False
assert emission_status['full_C2_cycle_credit'] is False
independent_review_dir = BASE / 'r10-first-consumption004-independent-review-20261005-002'
independent_review_index = sealed_package(independent_review_dir,
    '3a8164ae966d6ca167d4be3873442600113e3a3b62300b984ca08a4062cf450a')
independent_review = read_json(independent_review_dir / 'REPORT.json')
assert all(row['matched'] for row in independent_review['checks'])
assert independent_review['actual_ROOT_emitter_executed'] is True
assert independent_review['JOIN_business_credit'] is False
check_declared_ref(independent_review['first_review_refusal_preserved'])

invocation_refs = {}
for name in ['root-first-consumption-emit-invocation-001',
             'root-first-consumption-emit-invocation-002',
             'root-first-consumption-release-invocation-001',
             'root-first-consumption-host-request-001']:
    directory = RUN / name
    rows = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            row, _ = preserve_ref(path)
            rows.append(row)
    invocation_refs[name] = rows
for name in ['root-first-consumption-emit-invocation-002', 'root-first-consumption-release-invocation-001']:
    directory = RUN / name
    value = read_json(directory / 'RESULT.json')
    assert value['exit_code'] == 0
    for filename, field in [('stdout.txt', 'stdout_sha256'), ('stderr.txt', 'stderr_sha256')]:
        assert refs[(directory / filename).relative_to(BASE).as_posix()]['sha256'] == value[field]

actions = RUN / 'native-state/native-session/ordinary-interaction-actions'
action_refs = {}
for ordinal in [0, 1]:
    for suffix in ['claim.json', 'claim.packet.bin', 'claim.native-result.json', 'claim.receipt.json']:
        path = actions / f'{CLAIM_PREFIX}.{ordinal:08d}.{suffix}'
        row, _ = preserve_ref(path)
        action_refs[f'ordinal{ordinal}.{suffix}'] = row
parent = read_json(actions / f'{CLAIM_PREFIX}.00000000.claim.json')
child = read_json(actions / f'{CLAIM_PREFIX}.00000001.claim.json')
assert parent['claim_ordinal'] == 0 and parent['status'] == 'claimed_result_unknown_no_retry'
assert sha((actions / f'{CLAIM_PREFIX}.00000000.claim.json').read_bytes()) == '3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce'
assert child['claim_ordinal'] == 1 and child['status'] == 'claimed_result_unknown_no_retry'
assert child['action_identity'] == parent['action_identity']
assert child['new_intent_lineage']['permit_sha256'] == PERMIT_SHA
permit_ref, permit_raw = preserve_ref(actions / f'{CLAIM_PREFIX}.00000000.claim.release.json')
assert permit_ref['sha256'] == PERMIT_SHA
permit = json.loads(permit_raw.decode('utf-8-sig'))
assert permit['business_acceptance_credit'] is False
consumed_ref, consumed_raw = preserve_ref(actions / f'{CLAIM_PREFIX}.00000000.claim.release.consumed.json')
consumed = json.loads(consumed_raw.decode('utf-8-sig'))
assert consumed['permit_sha256'] == PERMIT_SHA
assert consumed['next_intent_id'] == permit['next_intent_id']
assert new_native_values[42]['result']['action_request_id'] == child['request_id']
assert new_native_values[42]['result']['action_claim_path'] == str(actions / f'{CLAIM_PREFIX}.00000001.claim.json')
assert new_native_values[42]['result']['business_effects_verified'] is False
assert new_native_values[42]['result']['full_product_acceptance_credit'] is False
release_output = read_json(RUN / 'root-first-consumption-release-invocation-001/stdout.txt')
assert release_output['permit_sha256'] == PERMIT_SHA
assert release_output['game_command_sent'] is False and release_output['business_acceptance_credit'] is False
for key in ['manifest', 'registry', 'verifier_bundle']:
    check_declared_ref(permit[key])

query55 = new_native_values[55]['result']
event55 = query55['current_event_window_context']
assert event55['current_event_instance_id'] == 54 and event55['event_definition_key'] == 'lyd.228'
assert query55['queried_revision'] == 25 and query55['queried_native_revision'] == 24
assert event55['date_raw'] == 53144712
selection54 = new_native_values[54]['result']['event_selection']
assert selection54['old_event_instance_id'] == 53 and selection54['new_event_instance_id'] == 54
assert selection54['selected_option_number'] == 1 and selection54['selected_native_option_index'] == 0
assert selection54['postcondition_verified'] is True

report = read_json(PRIOR / 'REPORT.json')
report.update({
    'revision': 4, 'utc': datetime.now(timezone.utc).isoformat(),
    'status': 'IN_PROGRESS_NOT_GREEN_SECOND_PROPOSAL_OPENED_SIGNATURE_ACK_FINAL_SAVE_PENDING',
    'evidence_cutoff': 'ROOT-authorized actual SDK sequences1-through55; only39-through55 newly read; last actual request r10-0056',
    'previous_report_index_sha256': refs[(PRIOR / 'INDEX.json').relative_to(BASE).as_posix()]['sha256'],
    'SDK_count_through_cutoff': 55, 'SDK_result_recorded_count': 55,
    'sdk_new39_through55_raw_bytes': new_sdk_bytes,
    'sdk_total_raw_bytes': report['sdk_total_raw_bytes'] + new_sdk_bytes,
    'next_intent_before39_report': refs[(before_dir / 'REPORT.json').relative_to(BASE).as_posix()],
    'next_intent_before39_index': before_index,
    'second_proposal_open43_report': refs[(second_dir / 'REPORT.json').relative_to(BASE).as_posix()],
    'second_proposal_open43_index': second_index,
    'second_proposal_typed_facts': facts_ref,
    'second_proposal_fields_at_saved43': {key: facts[key] for key in [
        'actual_actionUUID', 'actual_claim_ordinal', 'first_ordinal0_claim_preserved',
        'actual_round_change', 'actual_quorum_rows', 'actual_actor_C2_lists', 'actual_tickets',
        'actual_player_consent_rows', 'old_player_round7_ballot_or_consent_not_round8_credit',
        'saved_type_value_identity_omission_kept_null_not_zero', 'actual_Rite_locks_cooldowns',
        'saved_current_roles', 'actual_wallet', 'actual_wallet_Decimal_delta', 'actual_history',
        'fixture_reset_count', 'actual_saved_stress', 'expected_actual_stress']},
    'actual_emit004_index': emission_index,
    'actual_emit004_independent_review': independent_review_index,
    'actual_emit_and_release_invocations': invocation_refs,
    'actual_host_release': {'completed': True, 'permit': permit_ref, 'consumption_receipt': consumed_ref,
                            'new_ordinal1_action': action_refs['ordinal1.claim.json'],
                            'new_action_UUID': child['request_id'], 'consumed_by_SDK_sequence': 42,
                            'old_ordinal0_claim': action_refs['ordinal0.claim.json'],
                            'old_claim_status_retained': parent['status'],
                            'new_claim_status': child['status'], 'game_command_sent_by_release': False,
                            'JOIN_business_acceptance_credit': False},
    'last_actual_event_query55': {'sequence': 55, 'request_id': ledger[54]['request_id'],
        'event_instance_id': 54, 'event_definition_key': 'lyd.228',
        'public_revision': 25, 'native_revision': 24, 'date_raw': 53144712,
        'event_query_receipt': ledger[54]['native_receipts'][0]['ref'],
        'second_signature_final_saved_result': None, 'final_rejection_reason': None,
        'AI_option_execution_trace': None, 'specific_random_branch': None,
        'JOIN_success_inferred_from_ACK': False},
    'second_proposal_final_saved_outcome': None,
    'second_proposal_final_JOIN_credit': False,
    'business_final_JOIN_credit': False,
    'R10_all_lifecycle_closed': False,
    'current_whole_log_final_credit': False,
})
for row in report['matrix']:
    if row['area'] == 'formalrepeat':
        row.update({'status': 'SECOND_PROPOSAL_OPENED_ROUND8_YES_AND_SIGNATURE_ACK55_FINAL_SAVE_PENDING',
                    'second_proposal': {'proposal_opened': True, 'independent_saved43_checks': 37,
                                        'player_YES_callback_recorded': True,
                                        'source_ballot_YES_callback_recorded': True,
                                        'source_signature_callback_recorded': True,
                                        'last_typed_event': 'lyd.228',
                                        'final_saved_result': None, 'final_credit': False},
                    'DETACH': None, 'JOIN2': None})
    if row['area'] == 'livebaseline':
        row['new_before39_checkpoint'] = before_report['save']
        row['second_open43_checkpoint'] = second_report['save_after']
    if row['area'] == 'reload':
        row['new_actual_readbacks'] = ['EXPLICIT_RESET_BEFORE39', 'SECOND_PROPOSAL_OPEN43']

OUT.mkdir()
dump_new(OUT / 'SOURCE-REFS.json', {'schema': 'lyd.r10.report.actual-source-refs.v4',
    'source_cutoff_sequence': 55,
    'inherited_previous_index': refs[(PRIOR / 'INDEX.json').relative_to(BASE).as_posix()],
    'new_reference_paths': new_paths,
    'files': sorted(refs.values(), key=lambda row: row['path'])})
dump_new(OUT / 'SDK1-55-EVIDENCE.json', {'schema': 'lyd.r10.actual-sdk-result-ledger.v3',
    'cutoff': 55, 'newly_read_sequences': [39, 55],
    'inherited_sdk1_through38_index': refs[(PRIOR / 'SDK1-38-EVIDENCE.json').relative_to(BASE).as_posix()],
    'new_sdk_raw_bytes': new_sdk_bytes, 'results': ledger})
dump_new(OUT / 'REPORT.json', report)
TEXT = '''# R10 实机验收进度草稿 004（2026-10-05）

当前状态为 **进行中／NOT_GREEN：第二次提案已开案并执行YES与source签署，最后typed query为lyd.228；尚无本次签署后的保存AST，完整JOIN信用false**。本稿严格截止真实SDK55（ROOT request `r10-0056-receiving-sign-result-query`），只新增SDK39–55、真实emit004／host release／permit消费及39→43保存独立读回。旧001／002／003不改，旧负向结果与失败保留。

`SDK1-55-EVIDENCE.json`逐项记录sequence、request ID、request／started／response／原SDK及native-copy的bytes／SHA；`SOURCE-REFS.json`继承冻结003的引用，并列出本次新增原件。SDK1–38不重复读取；90MB checkpoint本体没有在本稿重读、复制或AST解析。ROOT继续是唯一MCP／game／Git mutator，本稿只有外置新文件。

## 原提案消费证明与新意图许可

ROOT实际执行emit004，进程exit0，生成冻结 `r10-first-proposal-emitted-evidence-20261005-004`。CONSUMPTION-MANIFEST SHA `5f0ec75c2eaa9dbe3da15f691a49c291594b7f7de388035da5f5becad55f24a7`；原SDK15 ordinary action UUID `ordinary-interaction-0771f580b861428398ec6ec493944c23` 的packet、native result、13→16保存nonce6→7及独立事实均精确绑定。证明模式为PROPOSAL_OPENED，消费证明范围是原操作实际开了案，JOIN成功及fullcycle仍false。

emit包中的actual_host_release=false／registry_enabled=false是**生成该包时**的真实状态，原件不追写。随后ROOT另一次host release实际exit0，release stdout SHA `b4407252cc5693b881a8b6ba994454deb4b785b5900096f8590bc355c7654a59`，生成next-intent permit SHA **`6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84`**，scope为一个独立新意图。release自身game_command_sent=false／business_acceptance_credit=false。

原ordinal0 claim SHA **`3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce`**仍原样，status=`claimed_result_unknown_no_retry`，没有改写UNKNOWN或重新dispatch。新SDK42实际UUID `ordinary-interaction-a50373f260354f6f83c8052eaf837c7f`，ordinal1，新claim SHA `7c2d0d36486fc2ec6c0d44fb24319affdce818feb3edb59d6878921e3d00c021`，六部分action identity与parent相同，new_intent_lineage精确绑定parent及permit。`.release.consumed.json`证明同一个permit由新意图消费。新claim本身仍UNKNOWN_no_retry，nativepending回执business_effects_verified=false；后来的保存开案读回另行提供业务阶段证据。

emit004独立review002所有检查matched；原review001的fresh-output-absence拒绝完整保留，来源是ROOT并发真实成功emit已创建目录，该拒绝不是游戏产品RED。首次失败emit invocation也保留原stdout／stderr／exit，不把失败或旧状态刷绿。host release成功与旧UNKNOWN、新pending、保存开案分别记录。

## 显式reset的BEFORE及第二次开案

39保存91,531,932字节，SHA `0aac6341204b39048646c81eff068d3d7a9a6cb849388871910673ef15d1bdaa`；SDK39 public18／native17、paused／date53144712。独立BEFORE报告32项检查成立：fixture_reset_count3→4、Rite169 retry移除，旧nonce／serial7和签署拒绝result2保留，wallet／history／图和政治、人身保护未改。SDK40、41的新ordinary query实际CanSend／ready=true、公18／native17。**这是人为reset准备，不是自然一年或五年到期。**

新SDK42使用新意图permit实际发起JOIN提案，仍pending而无成功业务后验。SDK43保存91,536,022字节，SHA **`bfa49f033f3296b4561be7ca78e3c3b9bc3186741044d87af07e50b9cf1d3391`**，public20／native19。独立39→43读回包REPORT SHA `4846d30c937881b47820c5682a276b170eee4f62a29ee007eeb274a4ec10f2df`，typed facts SHA `d43ee38000ecceced01626dba772f434dee76659ecae1c17cdc3bdda84fc5855`；36件冻结索引、37项绑定／保护检查均成立。43保存只单次AST解析，39缓存复用。

实际nonce／serial7→8、active1，旧result2与旧签署行清除，本轮两名NPC票owner31254／round8／yes1。source1／2、target1／1；玩家旧round7票不计round8，saved type=value省略identity的player_yes保留NULL而不填0或1。新两Rite ownerlocks31254／lockserial8，retry／transition相关冷却缺失。钱包1543G／5650P／2200prestige、XP0、completed joins1／detaches2均不变；Faith mains、Rite parents、heads／完整tenets／doctrines、七政治title完整AST及选定person保护均相等。这是**第二提案PROPOSAL_OPENED**，并非第二次成功JOIN或正式JOIN→DETACH→JOIN2循环。

## SDK39–55的实际阶段

ROOT早期wrong-tool request0030在入队前被拒绝，导致后续SDK sequence与request ID相差1；此处继续保留，不能把request0056写成SDK56。

| SDK sequence | ROOT request／实际阶段 |
| --- | --- |
| 39 | 0040：显式reset后的新BEFORE保存 |
| 40 | 0041：current ordinary ready query |
| 41 | 0042：新意图fresh ordinary ready query |
| 42 | 0043：新ordinal1提案，pending；实际消费permit |
| 43 | 0044：开案保存public20／native19 |
| 44 | 0045：event52 typed lyd.200 wait |
| 45 | 0046：event52 option1 wait，public20→21 |
| 46 | 0047：event51 typed lyd.212个人同意 |
| 47 | 0048：event51 option1 YES，public21→22 |
| 48 | 0049：event50 typed lyd.210 source ballot |
| 49 | 0050：event50 option1 YES，public22→23 |
| 50 | 0051：review决议实际query |
| 51 | 0052：review select |
| 52 | 0053：confirm_outcome要求lyd.220；实际新event53／public24／native23 |
| 53 | 0054：event53 typed lyd.220 query |
| 54 | 0055：event53 option1 source签署，实际53→54／public24→25 |
| **55** | **0056：event54 typed query实际lyd.228，public25／native24** |

所有17项新增response为MCP_RESULT_RECORDED，原SDK无显式error true，request／SDK／native SHA及profile／session核对成立。option1是public选项号，对应native option index0；public／native revision列不当成选项号。SDK47、49、54的postcondition_verified只证明对应选项推进。SDK52的UI结果验证范围为receiver_dispatch_and_declared_ui_outcome，business_effects_verified=false／full_product_acceptance_credit=false。

SDK55实际lyd.228包含一项“记下本轮经过”，仅提供当前事件typed身份；**不据ACK写本次最终result2、具体拒绝原因、target ballot拒绝、随机40%分支或任何JOIN完成**。新的签署后保存、独立AST、AI执行trace当前均NULL。003中已保存的首轮result2签署拒绝是独立历史事实，不自动外推为round8结果。

## 当前矩阵

| 项目 | cutoff55结论 |
| --- | --- |
| preflight | 实际fresh离线审图／cold check002通过；旧request／appmanifest／launch001参数／002receipt-path失败原样保留 |
| source | d0f8 clean freeze／70production／SOURCE_ONLY审查保留；主树冻结未解除 |
| build | 编译PASS与Defender一次Add设置失败并存，原外层REDexit1不改写 |
| livebaseline | PID13436／creation／profile／session及13／16／31／39／43保存精确绑定；FILETIME仅查询身份且handle已关闭 |
| formalrepeat | 首轮31保存签署拒绝result2；原操作消费证明emit004与host release成功，新ordinal1开案round8、YES及签署ACK55实际发生；本次最终保存结果NULL，JOIN信用false，DETACH／JOIN2／fullcycle NOT_RUN |
| I3b | 正式共同同意→签署→宗主创建及actualHoR后验NOT_RUN／NULL |
| C3 | 正式宗主／challenger／双challenger／withdraw／death／followership场景NOT_RUN／NULL，teacher不等于HoR |
| practice | 本局修习／实际XP-stress差额／自然冷却／五校三负例实机NOT_RUN／NULL |
| I4 | 静态144及外置夹具准备保留；native cases0，无业务信用 |
| reload | 已有保存状态独立读回；业务后冷重载与reconcile仍NOT_RUN |
| normalexit | exit source inventory、外置root future sequence计划已准备；实际正常退出／clientclose／keeper FINAL／lease释放／sourcefreeze解除未执行 |

本稿未读取增长日志，没有wholefinal／所有业务无新错或全局GREEN信用。原prefix578条I4 unused-variable与原构建设置RED继续保留。exactd0f8礼与道CI159／static70／repro实际成功，通用CI两docs名称引用失败尚未由新CI复验；两文件外置候选待R10真正闭合后ROOT应用。

后续SDK、保存AST、typed终态、完整日志及生命周期闭合进入新revision；本004封存后不覆盖。
'''
write_new(OUT / 'REPORT.md', TEXT.encode('utf-8'))
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
write_new(OUT / 'source/inspect_r10_report004_actual_fields.py',
          (BASE / 'inspect_r10_report004_actual_fields.py').read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.external-report-draft-index.v4', 'files': files})
for row in files:
    assert sha((OUT / row['path']).read_bytes()) == row['sha256']
print(json.dumps({'status': 'R10_REPORT_DRAFT_004_SEALED_NOT_GREEN', 'path': str(OUT),
    'reference_count': len(refs), 'new_reference_count': len(new_paths),
    'new_sdk_count': 17, 'new_sdk_raw_bytes': new_sdk_bytes,
    'report_md_sha256': sha((OUT / 'REPORT.md').read_bytes()),
    'report_json_sha256': sha((OUT / 'REPORT.json').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=False))
