from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'
PRIOR = BASE / 'r10-incremental-evidence-ledger-through150-20261006-001'
ADDON = BASE / 'r10-incremental-evidence-ledger-through150-20261006-001-addendum-001'
OUT = BASE / 'r10-incremental-evidence-ledger-151-200-20261006-001'
PROFILE = '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'
SESSION = '53bd96329c5541f7a403c5cecf61d8ba'
RECOVER_FROM_COMPLETED_HASH_AUDITS = True
RECOVERY_CACHE = BASE / 'r10-ledger151-200-collection-recovery-20261006-001'

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

assert not OUT.exists(), 'New incremental package only'
refs = {row['path']: row for row in read_json(PRIOR / 'SOURCE-REFS.json')['files']}
for row in read_json(ADDON / 'NEW-SOURCE-REFS.json')['files']:
    if row['path'] in refs:
        assert (refs[row['path']]['bytes'], refs[row['path']]['sha256']) == (row['bytes'], row['sha256'])
    refs[row['path']] = row
new_paths = []

def pin(path):
    path = Path(path)
    assert path.suffix.lower() != '.ck3', 'No save bodies are reread, hashed or copied'
    relative = path.relative_to(BASE).as_posix()
    if relative in refs:
        return refs[relative], None
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), relative
    row = {'path': relative, 'bytes': len(data), 'sha256': sha(data), 'stat_unchanged_during_read': True}
    refs[relative] = row
    new_paths.append(relative)
    return row, data

def verify_new_package(directory, expected_index, selected_only=True):
    directory = BASE / directory
    ref, raw = pin(directory / 'INDEX.json')
    assert raw is not None, 'Package already inherited; use its existing exact index'
    assert ref['sha256'] == expected_index
    index = json.loads(raw.decode('utf-8-sig'))
    selected = []
    for row in index['files']:
        label = row['path'].upper()
        if selected_only and not (row['path'].startswith(('REPORT', 'TYPED-FACTS', 'PROPOSAL-OPENED-FACTS',
                    'CONTROL-EVIDENCE', 'LINEAGE-EVIDENCE', 'TARGET-RITE-BALLOT-QUALIFICATION', 'SOURCE-SEMANTICS'))
                    or any(value in label for value in ['FAILED', 'FAILURE', 'INITIAL', 'OWNER-ONLY', 'OWNER_ONLY', 'ORIGINAL-RESET-RED'])):
            continue
        actual, _ = pin(directory / row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
        selected.append(actual)
    return {'index': ref, 'indexed_payload_count': len(index['files']), 'selected_exact_refs': selected}

def pin_directory(directory):
    for path in sorted(Path(directory).iterdir()):
        if path.is_file():
            pin(path)

# Authenticate small prior ledgers and their indexes. Prior raw SDK1-150, save
# bodies, old sources and AST payloads are not reread.
prior_index_raw = (PRIOR / 'INDEX.json').read_bytes()
assert sha(prior_index_raw) == '20e4434c8e1cad1789600e0fc9882a4a7fd51527d0374a4a88c33e23e2ee9230'
addon_index_raw = (ADDON / 'INDEX.json').read_bytes()
assert sha(addon_index_raw) == 'ba1f2c100bccb5be7b34ef1aac783dc948414cac431b366e95336fff52036ad2'
for directory, index_raw in [(PRIOR, prior_index_raw), (ADDON, addon_index_raw)]:
    for row in json.loads(index_raw.decode('utf-8-sig'))['files']:
        if row['path'] in ['SOURCE-REFS.json', 'NEW-SOURCE-REFS.json', 'LEDGER-SUMMARY.json', 'ADDENDUM.json']:
            raw = (directory / row['path']).read_bytes()
            assert (len(raw), sha(raw)) == (row['bytes'], row['sha256'])
    for filename in ['INDEX.json', 'LEDGER-SUMMARY.json' if directory == PRIOR else 'ADDENDUM.json']:
        path = directory / filename
        if path.relative_to(BASE).as_posix() not in refs:
            pin(path)
ledger = []
native_values = {}
new_sdk_bytes = 0
for sequence in range(151, 201):
    matches = list(SDK.glob(f'{sequence:04d}-*.response.json'))
    assert len(matches) == 1
    response_path = matches[0]
    response_ref, raw = pin(response_path)
    assert raw is not None
    response = json.loads(raw.decode('utf-8-sig'))
    assert response['sequence'] == sequence and response['status'] == 'MCP_RESULT_RECORDED'
    prefix = response_path.name[:-len('.response.json')]
    request_ref, raw = pin(SDK / (prefix + '.request.json'))
    request = json.loads(raw.decode('utf-8-sig'))
    assert request_ref['sha256'] == response['request_sha256']
    started_ref, _ = pin(SDK / (prefix + '.started.json'))
    sdk_path = SDK / response['sdk_result']
    if RECOVER_FROM_COMPLETED_HASH_AUDITS:
        # Both preserved first attempts finished all50 full SDK hash assertions
        # before later summary schema failures. Recover immutable digest/size
        # from the exact response and stat; do not do a third raw SDK sweep.
        before = sdk_path.stat()
        with sdk_path.open('rb') as stream:
            beginning = stream.read(1024)
            stream.seek(max(0, before.st_size - 1024))
            ending = stream.read(1024)
        after = sdk_path.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        flags = set(re.findall(rb'"isError"\s*:\s*(true|false)', beginning + b'\n' + ending))
        flags.update(re.findall(rb'"is_error"\s*:\s*(true|false)', beginning + b'\n' + ending))
        error = flags.pop() == b'true' if len(flags) == 1 else None
        sdk_ref = {'path': sdk_path.relative_to(BASE).as_posix(), 'bytes': before.st_size,
            'sha256': response['sdk_result_sha256'], 'stat_unchanged_during_read': True,
            'hash_verification_basis': 'Both preserved author attempts completed exact raw SDK hash assertions before later semantic schema errors; no third body sweep',
            'SDK_error_flag_basis': 'Bounded first/last1024 bytes; conflicting or absent flags remainNULL'}
        refs[sdk_ref['path']] = sdk_ref
        new_paths.append(sdk_ref['path'])
        raw = None
    else:
        sdk_ref, raw = pin(sdk_path)
        sdk_value = json.loads(raw.decode('utf-8-sig'))
        error = sdk_value.get('isError', sdk_value.get('is_error'))
    assert sdk_ref['sha256'] == response['sdk_result_sha256']
    new_sdk_bytes += sdk_ref['bytes']
    natives = []
    for item in response.get('native_receipts', []):
        actual, raw = pin(SDK / item['copy'])
        assert actual['sha256'] == item['sha256']
        value = json.loads(raw.decode('utf-8-sig'))
        if value.get('profile_sha256') is not None:
            assert value['profile_sha256'] == PROFILE
        if value.get('session_id') is not None:
            assert value['session_id'] == SESSION
        result = value.get('result', {})
        context = result.get('current_event_window_context') or {}
        natives.append({'ref': actual, 'original_native_path': item['path'],
            'status': value.get('status'), 'result_status': result.get('status'),
            'expected_outcome': result.get('expected_outcome'),
            'postcondition_verified': result.get('postcondition_verified'),
            'verification_pending': result.get('verification_pending'),
            'business_effects_verified': result.get('business_effects_verified', value.get('business_effects_verified')),
            'full_product_acceptance_credit': result.get('full_product_acceptance_credit', value.get('full_product_acceptance_credit')),
            'current_event_id': context.get('current_event_instance_id'),
            'current_event_definition_key': context.get('event_definition_key'),
            'public_revision': result.get('queried_revision'),
            'native_revision': result.get('queried_native_revision'),
            'profile_sha256': value.get('profile_sha256'), 'native_session_id': value.get('session_id')})
        native_values[sequence] = value
    assert natives
    ledger.append({'sequence': sequence, 'request_id': request['request_id'],
        'operation': request['operation'], 'tool': request.get('name'), 'arguments': request.get('arguments'),
        'response_status': response['status'], 'response_is_error': response.get('is_error'),
        'SDK_explicit_error_flag': error, 'request': request_ref, 'response': response_ref,
        'started': started_ref, 'sdk': sdk_ref, 'native_receipts': natives,
        'started_utc': response['started_at_utc'], 'finished_utc': response['finished_at_utc']})
    pin_directory(RUN / 'root-explicit-mcp-requests' / request['request_id'])
    local = RUN / 'root-call-stdio' / request['request_id']
    if local.is_dir():
        pin_directory(local)
assert len(ledger) == 50
assert ledger[-1]['sequence'] == 200
RECOVERY_CACHE.mkdir(exist_ok=False)
dump_new(RECOVERY_CACHE / 'COLLECTION.json', {'schema': 'lyd.r10.recovered-completed-hash-collection.v1',
    'ledger': ledger, 'refs': refs, 'new_paths': new_paths,
    'native_values_needed_for_summary': {str(seq): native_values[seq] for seq in [196, 197, 198, 199]},
    'source_failure_basis': ['r10-ledger151-200-author-attempt-20261006-001', 'r10-ledger151-200-author-attempt-20261006-002'],
    'third_full_raw_SDK_sweep_performed': False})
cache_raw = (RECOVERY_CACHE / 'COLLECTION.json').read_bytes()
dump_new(RECOVERY_CACHE / 'INDEX.json', {'schema': 'lyd.r10.collection-cache-index.v1', 'files': [
    {'path': 'COLLECTION.json', 'bytes': len(cache_raw), 'sha256': sha(cache_raw)}]})
pin(RECOVERY_CACHE / 'INDEX.json')
pin(RECOVERY_CACHE / 'COLLECTION.json')

specs = [
 ('r10-actual-seventh-open-join-readback-20261006-001', '0569e4a4681810aafc14e1c1fb8c428381633e97ccf079b73b49d1a5a7df4a63', 153),
 ('r10-actual-seventh-post-cancel-readback-20261006-001', '2f6df477a00c2a9200da1eeda06630b6211a9f8b0ec9330e1ecf92aa8ff0ff60', 167),
 ('r10-actual-eighth-open-join-readback-20261006-001', '9dffe39055cf5f3371f500312c9050e737a8b7f46005fc65f97548724e8da197', 171),
 ('r10-actual-eighth-precommit-readback-20261006-001', '4ac330318ec419d4049486d60232f7e7e0164531ab382635310e59a592ac1ad9', 187),
 ('r10-actual-eighth-post-join-readback-20261006-001', 'd090b1ff7fb5a4af0669aa3a569c63d601141ef5d1a15d1431910374b121a368', 192),
 ('r10-actual-cycle-before-detach-readback-20261006-001', 'ba671760a0e85e5e4bfc70812ef1d203e0b0a4dc611d1ffd523b9c9c0b94e197', 200)]
readbacks = []
for directory, index_sha, sequence in specs:
    package = verify_new_package(directory, index_sha)
    report = read_json(BASE / directory / 'REPORT.json')
    checks = report.get('binding_and_protection_checks', report.get('all_binding_and_protection_checks'))
    if checks is None:
        checks = report.get('qualified_binding_and_protection_checks')
    assert checks is not None and all(checks.values())
    package.update({'report': refs[f'{directory}/REPORT.json'], 'status': report['status'],
        'save_SDK_sequence': sequence, 'check_count': len(checks),
        'final_JOIN_credit': report.get('final_JOIN_credit', report.get('new_JOIN_or_DETACH_credit', False))})
    readbacks.append(package)
assert readbacks[4]['final_JOIN_credit'] is True and readbacks[4]['check_count'] == 183
assert all(row['final_JOIN_credit'] is False for i, row in enumerate(readbacks) if i != 4)
join_report = read_json(BASE / specs[4][0] / 'REPORT.json')
assert join_report['save']['bytes'] == 91604449
assert join_report['save']['sha256'] == '9534d61d4f426ca8df0f4866695b7234f5ff477c296f084c1868a29424ae06d0'
assert refs[f'{specs[4][0]}/REPORT.json']['sha256'] == '9f0b3463d523081d4613100da6c8712bc2e10cb25b13c4aad69c7bbd49ca33c1'
assert ledger[192-151]['sdk']['bytes'] == 8056003
assert ledger[192-151]['sdk']['sha256'] == '01d0423c11b77729082189df4a76c3ef4f2ab556238d0511c2a0a2582012863a'

lineage = verify_new_package('r10-actual-sixth-consumption-release-lineage-independent-review-20261006-002',
    'bdc8c2ce956aa95204f260ea7781b2c680ff02e89dafedaea502143e4a17b5f4', selected_only=False)
failed_lineage = BASE / 'r10-actual-sixth-consumption-release-lineage-independent-review-20261006-001'
for path in sorted(failed_lineage.iterdir()):
    if path.is_file():
        pin(path)
cooldown = verify_new_package('r10-decision-cooldown-query-boundary-independent-review-20261006-001',
    '934b9febadbd51f771174b3c46dcc764cf916ff0342a13c00630d4123e389d9f', selected_only=False)

for sequence in [153, 167, 171, 187, 192, 200]:
    path = next((RUN / 'checkpoints').glob(f'{sequence:04d}-*/checkpoint-metadata.json'))
    row, _ = pin(path)
    value = read_json(path)
    assert value['sdk']['sha256'] == ledger[sequence-151]['sdk']['sha256']

# New immutable action/permit and actual ROOT emit/release evidence only.
actions = RUN / 'native-state/native-session/ordinary-interaction-actions'
for path in sorted(actions.iterdir()):
    if path.is_file() and path.relative_to(BASE).as_posix() not in refs:
        pin(path)
for ordinal in ['sixth', 'seventh']:
    for step in ['bind', 'emit', 'release']:
        directory = RUN / f'root-{ordinal}-consumption-{step}-invocation-001'
        if directory.is_dir():
            pin_directory(directory)
    directory = RUN / f'root-{ordinal}-consumption-host-request-001'
    if directory.is_dir():
        pin_directory(directory)

fixture196 = ledger[196-151]
assert fixture196['arguments']['expected_outcome'] == 'decision_closed'
native196 = native_values[196].get('result', {})
query198 = native_values[198]['result']['current_event_window_context']
assert query198['event_definition_key'] == 'lyd_r4_fixture.4'
selection199 = native_values[199]['result']['event_selection']
assert selection199['selected_option_number'] == 1 and selection199['new_event_instance_id'] is None
checkpoint200_path = next((RUN / 'checkpoints').glob('0200-*/checkpoint-metadata.json'))
checkpoint200 = read_json(checkpoint200_path)
author_failure = verify_new_package('r10-ledger151-200-author-attempt-20261006-001',
    'e7e3ca5ce1e2b451607eb0474c6df6ca129038c0cfee399f0b4e39e9ad7eed56', selected_only=False)
author_failure2 = verify_new_package('r10-ledger151-200-author-attempt-20261006-002',
    'd47d63060edfc718e8d899abc164ba108d2910076ecfcf256a7a2e5926254bb5', selected_only=False)

summary = {'schema': 'lyd.r10.incremental-evidence-ledger151-through200.v1',
    'status': 'IN_PROGRESS_NOT_GREEN_ONE_ACTUAL_JOIN_VERIFIED_CYCLE_AND_EXIT_PENDING',
    'utc': datetime.now(timezone.utc).isoformat(), 'SDK_cutoff': 200,
    'last_request': ledger[-1]['request_id'],
    'inherited_ledger150_index_sha256': sha(prior_index_raw),
    'inherited_actual149_addendum_index_sha256': sha(addon_index_raw),
    'new_SDK_sequences': [151, 200], 'new_SDK_count': 50, 'new_raw_SDK_bytes': new_sdk_bytes,
    'author_first_schema_failure': author_failure,
    'author_second_schema_failure': author_failure2,
    'new_SDK_hash_audit_pass_count': 2,
    'repeat_boundary': 'Two full SDK151-200 hash audits finished before later semantic schema errors. Digests recovered from immutable exact response refs plus both failure-source traces; third pass only bounded SDK metadata, no body sweep. SDK1-150/save bodies unread.',
    'SDK_error_flag_true_sequences': [row['sequence'] for row in ledger if row['SDK_explicit_error_flag'] is True],
    'response_error_flag_true_sequences': [row['sequence'] for row in ledger if row['response_is_error'] is True],
    'readbacks': readbacks, 'new_sixth_release_lineage_review': lineage,
    'seventh_round13': {'result': 3, 'stage': 'CANCELLED', 'JOIN_credit': False,
        'NPC_current_tickets_with_omitted_vote_identity_kept_NULL': True},
    'eighth_round14_stages': {
        'opening171': {'stage': 'PROPOSAL_OPENED', 'fee_delta': [0, 0], 'new_history_JOIN': False,
            'current_sourceNPC_yes': 1, 'current_targetNPC_yes': 1,
            'qualified_targetRite_counter1_evidence_retains_initial_owner_only_RED': True},
        'precommit187': {'three_signatures_present1': True, 'quorum_source2of2_target1of1_player1of1': True,
            'all_current14_votes_yes': True, 'fee_delta': [0, 0], 'JOIN_credit': False},
        'actual_commit189': {'event_instance': 87, 'native_option_index': 1, 'public_option_number': 2,
            'real_sdk': ledger[189-151]['sdk'], 'gold1543_to1243': True, 'piety5650_to4150': True},
        'result190': {'typed_event': 'lyd.228'}, 'ACK191': {'recorded': True},
        'independent_post_save192': {'result': 1, 'final_JOIN_credit': True,
            'save': join_report['save'], 'checks': 183,
            'history_joins_before': 1, 'history_joins_after': 2, 'history_detaches': 2,
            'wallet_gold': 1243, 'wallet_piety': 4150, 'wallet_prestige': 2200,
            'fee_gold': 300, 'fee_piety': 1500, 'native_stress0_saved_stress_absent_NULL': True,
            'moving_Rite169_parentFaith_before': 106, 'moving_Rite169_parentFaith_after': 104,
            'targetFaith104_mainRite': 159, 'actor31254_Rite': 169, 'actor31254_Faith': 104,
            'sourceNPC65865_Rite': 169, 'sourceNPC65865_Faith': 104,
            'targetNPC65866_Rite': 159, 'targetNPC65866_Faith': 104,
            'oldFaith106_newBackupMainRite': 187, 'backupRite187_parentFaith': 106,
            'backup187_full_tenets_match_previous169': True,
            'moving169_HoR31254_retained': True, 'transition169_value1_tick1825': True,
            'actor_school_CD_tick349': True, 'owner_locks_released': True, 'reset_count': 5,
            'political7_person_actor_landed_playable_full_tenets_heads_protected': True,
            'graph_parent159_claim': False}},
    'decision193_boundary': {'independent_review': cooldown,
        'available_unique_DETACH_row_observed': True, 'action_qualified_false_is_serializer_constant': True,
        'MCP_direct_disabled_or_CD_rejection_credit': False,
        'source_and_saved_CD_inference_is_separate': True},
    'fixture196_original_RED_and_later_evidence': {
        'original_request': fixture196['request_id'], 'original_arguments': fixture196['arguments'],
        'original_response_is_error': fixture196['response_is_error'],
        'original_SDK_error_flag': fixture196['SDK_explicit_error_flag'],
        'original_native_status': native_values[196].get('status'),
        'original_native_reason': native_values[196].get('reason'),
        'original_native_result_status': native196.get('status'),
        'original_postcondition_verified': native196.get('postcondition_verified'),
        'original_native_handled': native196.get('native_handled'),
        'original_actual_record': fixture196,
        'later_new_readonly_snapshot197': ledger[197-151],
        'later_typed_query198': {'actual_event_key': query198['event_definition_key'],
            'actual_event_instance': query198['current_event_instance_id'], 'sdk': ledger[198-151]['sdk']},
        'later_ACK199': {'public_option': 1, 'new_event': None, 'sdk': ledger[199-151]['sdk']},
        'later_actual_save200': checkpoint200,
        'original_failure_not_rewritten': True, 'fixture_confirm_not_replayed': True,
        'reset200_independent_AST': 'SEALED67CHECKS', 'schoolCD349_removed_by_reset200': False,
        'transition169_tick1825_removed_by_reset200': True,
        'fixture_reset_count5_to6': True,
        'actual_reset200_readback': readbacks[5],
        'natural_cooldown_expiry_credit': False},
    'R10_completed_formal_JOIN_count': 1,
    'R10_completed_DETACH_credit': False, 'R10_formal_JOIN2_credit': False, 'fullcycle_credit': False,
    'normal_exit': 'NOT_RUN', 'SDK_Client_closed': False, 'keeper_FINAL': None,
    'lease_released': False, 'source_freeze_released': False,
    'wholelogs_latest_actual_cutoff': 108, 'wholefinal_log_credit': False,
    'old_SDK1_to150_raw_rehashed': False, 'save_bodies_hashed_or_parsed': False,
    'old_tests_rerun': False, 'old_ledgers_or_reports_modified': False,
    'main_Git_game_native_Client_pipe_bus_mutations': False}

OUT.mkdir()
dump_new(OUT / 'SDK151-200-EVIDENCE.json', {'schema': 'lyd.r10.incremental-actual-sdk-results.v1',
    'sequences': [151, 200], 'author_schema_failure_requires_second_read_preserved': True,
    'new_raw_SDK_bytes': new_sdk_bytes, 'results': ledger})
dump_new(OUT / 'SOURCE-REFS.json', {'schema': 'lyd.r10.incremental.actual-source-refs.v2',
    'SDK_cutoff': 200, 'inherited_ledger150_index_sha256': sha(prior_index_raw),
    'inherited_actual149_addendum_index_sha256': sha(addon_index_raw),
    'new_reference_paths': new_paths, 'files': sorted(refs.values(), key=lambda row: row['path'])})
dump_new(OUT / 'LEDGER-SUMMARY.json', summary)
TEXT = '''# R10 增量证据：SDK151–200（2026-10-06）

**R10仍LIVE／NOT_GREEN；首次正式JOIN已由独立192保存验证，完整JOIN→DETACH→JOIN2及正常退出尚未发生。** 本包只新增SDK151–200的50项原件审阅和新sealed引用，继承原150ledger与149addon，不重读1–150原SDK、不hash／parse91MB保存、不重跑旧测试、不改原报告或主树。

第七nonce13开案153与取消167各自封存：result3 CANCELLED，NPC当轮票identity省略保留NULL、玩家13YES不倒填opening；钱包／history／XP及全部保护不变。第六消费release→ordinal6的真实父链另有独立002审查，001期待seventh_role_id误名的审阅者失败保留，不作为产品RED。

第八三段信用严格分列：171 opening nonce14、两NPC当前YES、0fee、history不新增；187 current14三签均1及quorum2／2、1／1、1／1，仍0fee／无最终JOIN；189 event87选择public option2／native index1实际commit→190 event88 typed lyd.228→191 ACK→192保存。192独立包183项检查成立，actual result1／active移除，历史joins1→2、detaches2不变，**-300G／-1500P**，钱包1243G／4150P／2200prestige，native stress0、保存stress缺失仍NULL。

实际图：Rite169的parent **Faith106→Faith104**，Faith104的main **Rite159**另列；不能写parent159。actor31254与sourceNPC65865保留Rite169并随之转Faith104，targetNPC65866保持Faith104／Rite159。旧Faith106新backup main Rite187／parentFaith106，backup187完整tenets与旧169相同；既有heads／完整tenets和政治7title／person／actorlanded／playable保护成立，169HoR31254保留、owner释放。仅本轮14记1个正式成功JOIN，之前七轮提案／签署／取消和fixture不记成功。

192保存91,604,449B／SHA `9534d61d4f426ca8df0f4866695b7234f5ff477c296f084c1868a29424ae06d0`，原SDK8,056,003B／SHA `01d0423c11b77729082189df4a76c3ef4f2ab556238d0511c2a0a2582012863a`，public91／native90。独立finalJOIN REPORT SHA `9f0b3463d523081d4613100da6c8712bc2e10cb25b13c4aad69c7bbd49ca33c1`、INDEX `d090b1ff7fb5a4af0669aa3a569c63d601141ef5d1a15d1431910374b121a368`。171原owner-only RED与后来的真实targetRite合法票counter资格补充保留，不覆盖。

SDK193只读unique DETACH行available=true、detailhidden／action_qualified=false；独立审查证明该false是serializer恒值、当前query没有enabled／is_valid，不能把它写成MCP直接观测冷却禁用或CD negative test。192保存schoolCD349及169transitionCD1825配合冻结源码必要门可作资格false推断，单列为source+save inference。

SDK196原fixture confirm要求expected decision_closed，原structured.status为RED，精确reason为BridgeUnavailableError: generic Confirm outcome read crossed its actual frame；原返回原字节保持。没有重复confirm：197为新的独立snapshot观察，198 typed query实际lyd_r4_fixture.4，199 ACK，200再次保存。新200独立包67项检查成立，实际reset5→6／169transition1825删除，钱包／history2join2detach和保护保持，证明原操作实际发生。原失败与后续观察不合并成原调用PASS；人为reset不授自然五年到期信用。

索引作者两次均已完成新50项SDK字节核对，随后摘要schema适配失败：先假定196错误回执有result，后假定reset200报告有final_JOIN_credit。两个作者失败的源码／真实tool-transcript退出和错误位置单独保留，属于索引代码错误。收口恢复两次已完成的hash断言及不可变response摘要，SDK只读首尾metadata，未第三次扫描完整SDK body；1–150与所有保存本体仍未读取，旧测试未重跑，不伪称作者首遍成功。

所有SDK151–200保留其实际status／error flag／native状态；MCP_RESULT_RECORDED只证明结果记录，不代表每条验证或业务成功。完整profile／session与request-SDK-native SHA绑定在逐项ledger。原150本地等待失败、未入队参数和所有旧失败不追写。

当前normalexit NOT_RUN，Client／keeper／lease／source freeze均未闭合；wholelogs只到108、后续coverage未知。最后章节／apply-map骨架仍待ROOT实际cycle终态与退出闭合后单次生成永久候选；本包不延展SDK201+。
'''
write_new(OUT / 'NOTES-zh.md', TEXT.encode('utf-8'))
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.incremental-ledger151-200-index.v1', 'files': files})
for row in files:
    data = (OUT / row['path']).read_bytes()
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
print(json.dumps({'status': summary['status'], 'path': str(OUT), 'new_SDK_count': 50,
    'new_raw_SDK_bytes': new_sdk_bytes, 'reference_count': len(refs), 'new_reference_count': len(new_paths),
    'SDK_error_flag_true_sequences': summary['SDK_error_flag_true_sequences'],
    'fixture196_actual_native_status': summary['fixture196_original_RED_and_later_evidence']['original_native_status'],
    'fixture196_actual_result_status': summary['fixture196_original_RED_and_later_evidence']['original_native_result_status'],
    'summary_sha256': sha((OUT / 'LEDGER-SUMMARY.json').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=False))
