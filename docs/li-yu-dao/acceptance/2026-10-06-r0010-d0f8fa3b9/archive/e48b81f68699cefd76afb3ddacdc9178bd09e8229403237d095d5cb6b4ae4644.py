from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
PRIOR = BASE / 'r10-incremental-evidence-ledger-through150-20261006-001'
OUT = BASE / 'r10-incremental-evidence-ledger-through150-20261006-001-addendum-001'
READBACK = BASE / 'r10-actual-sixth-post-cancel-readback-20261006-001'
LINEAGE = BASE / 'r10-actual-fifth-consumption-release-lineage-independent-review-20261006-001'

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

assert not OUT.exists(), 'Refusing to overwrite an existing addendum'
refs = {}

def pin(path):
    path = Path(path)
    assert path.suffix.lower() != '.ck3'
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    row = {'path': path.relative_to(BASE).as_posix(), 'bytes': len(data), 'sha256': sha(data),
           'stat_unchanged_during_read': True}
    if row['path'] in refs:
        assert row == refs[row['path']]
    refs[row['path']] = row
    return row

prior_index = pin(PRIOR / 'INDEX.json')
assert prior_index['sha256'] == '20e4434c8e1cad1789600e0fc9882a4a7fd51527d0374a4a88c33e23e2ee9230'
pin(PRIOR / 'LEDGER-SUMMARY.json')
assert refs[f'{PRIOR.name}/LEDGER-SUMMARY.json']['sha256'] == '068cdfcb8842e79afe400ac4462149cfde31cdd32fdb11e724720f3f0dfe42fc'
assert read_json(PRIOR / 'LEDGER-SUMMARY.json')['sixth_proposal']['independent_post_cancel_AST_seal'] == 'PENDING'

def verify_package(path, expected_index):
    ref = pin(path / 'INDEX.json')
    assert ref['sha256'] == expected_index
    value = read_json(path / 'INDEX.json')
    for row in value['files']:
        actual = pin(path / row['path'])
        assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256'])
    return ref, len(value['files'])

readback_index, payload_count = verify_package(READBACK,
    'a3e63dbca5853d8181d31ac94e48e008e836f79c207c216d30d3612cc2981dc0')
assert payload_count == 45
report = read_json(READBACK / 'REPORT.json')
assert refs[f'{READBACK.name}/REPORT.json']['sha256'] == '1c4d9886460b9aaa15bfcdfdfd806e389cc4d3025f43d72c2007b1a0979d26ac'
assert len(report['all_binding_and_protection_checks']) == 62
assert all(report['all_binding_and_protection_checks'].values())
assert report['actual_AST_parse_count'] == 1 and report['old_save_reparsed'] is False
assert report['final_JOIN_credit'] is False and report['fresh150_query_new_initiation_credit'] is False
assert report['save']['sha256'] == '5ab8d308bd2f3858388f86cc34289683c30cf8efa43515283c001421c40affe1'
assert report['save']['bytes'] == 91537192
assert report['typed_facts']['sha256'] == '02c83d64da99e65d0a8c54e0c1ff80c16b16f2ccba6e011e58f9d806155ef5bb'
assert report['complete_Rite_Faith_AST_diff']['sha256'] == '910eba9a825f056d1a5912aa281c4fcfac389e8740f46577c07f6628bd429122'
lineage_index, lineage_payload_count = verify_package(LINEAGE,
    'd9cff47fb7c4539a0ecd9a107fe1f508c3889497b725880555816fd0ce6afb60')
assert refs[f'{LINEAGE.name}/REPORT.json']['sha256'] == '99e8a8cddda666b85824107fa968fde0c642b784598853c7ca7ae125e0985e33'

summary = {'schema': 'lyd.r10.incremental-ledger150.actual149-sealed-addendum.v1',
    'utc': datetime.now(timezone.utc).isoformat(),
    'status': 'ACTUAL_SIXTH_CANCELLATION_BOUND_NOT_GREEN', 'SDK_cutoff_unchanged': 150,
    'prior_ledger_index': prior_index, 'prior_pending_record_preserved': True,
    'supersession_scope': 'Only adds sealed actual149 AST facts after prior PENDING record; no rewrite or higher SDK cutoff',
    'actual_post_cancel_package_index': readback_index,
    'actual_report': refs[f'{READBACK.name}/REPORT.json'],
    'typed_facts': refs[f'{READBACK.name}/TYPED-FACTS.json'],
    'complete_Rite_Faith_AST_diff': refs[f'{READBACK.name}/COMPLETE-RITE-FAITH-AST-DIFF.json'],
    'actual_payload_count_verified': payload_count, 'all62_binding_and_protection_checks': report['all_binding_and_protection_checks'],
    'sixth_terminal_facts': {'nonce': 12, 'result': 3, 'outcome': 'CANCELLED', 'active_present': False,
        'source_signed': 1, 'target_requested': None, 'target_requested_presence': 'ABSENT',
        'target_signed': None, 'target_signed_presence': 'ABSENT',
        'source_yes': 2, 'source_total': 2, 'player_yes': 1, 'player_total': 1,
        'target_yes': None, 'target_yes_reason': 'SAVED_VALUE_IDENTITY_OMITTED', 'target_total': 1,
        'player_current_round_vote_yes': 1, 'player_round': 12,
        'sourceNPC_current_round_yes': 1, 'targetNPC_current_round_vote': None,
        'Rite159_owner_released': True, 'Rite169_owner_released': True,
        'historical_lock_serial12_retained': True, 'retry_transition_cooldown_present': False,
        'fixture_reset_count': 5, 'wallet_delta': [0, 0, 0], 'XP_delta': 0,
        'completed_history_changed': False,
        'full_Faith_AST_unchanged': True, 'Rite_AST_changes_match_only_owner_and_serial_history': True,
        'political7_person_heads_full_tenets_protected_both125_129_baselines': True},
    'reader_actual_AST_parse_count': 1, 'old_save_reparsed_by_reader': False,
    'AST_parse_count_by_addendum_writer': 0,
    'new_actual_fifth_consumption_release_lineage_review': {'index': lineage_index,
        'report': refs[f'{LINEAGE.name}/REPORT.json'], 'payload_count': lineage_payload_count,
        'scope': 'Fifth nonce10-to11 proposal-opened consumption and actual permit350483 to sixth ordinal5; no sixth savednonce consumption credit'},
    'current_ready150_has_new_initiation_credit': False,
    'actual_sixth_post_cancel_save': report['save'],
    'R10_completed_JOIN_count': 0, 'final_JOIN_credit': False, 'fullcycle_credit': False,
    'normal_exit': 'NOT_RUN', 'Client_profile_lease_closed': False,
    'latest_log_cutoff': 108, 'wholefinal_log_credit': False,
    'seventh_proposal_started_credit': False,
    'future_sixth_consumption_release_credit': False,
    'main_Git_game_native_Client_pipe_bus_mutations': False,
    'tests_or_old_AST_reruns': False}
OUT.mkdir()
dump_new(OUT / 'ADDENDUM.json', summary)
dump_new(OUT / 'NEW-SOURCE-REFS.json', {'schema': 'lyd.r10.small-addendum-source-refs.v1',
    'previous_ledger_index': prior_index, 'files': sorted(refs.values(), key=lambda row: row['path'])})
write_new(OUT / 'NOTES-zh.md', '''# R10 ledger150 小补充：149独立保存终态（2026-10-06）

原ledger中PENDING记录保留不改。本补充只在149独立包真正seal之后绑定其45件精确bytes／SHA、62项全部成立的检查；cutoff仍SDK150，不重写全报告。

第六nonce12真实保存result3 CANCELLED／active缺失，source_signed1，target requested／signed缺失；source2／2、player1／1及current12玩家YES1，sourceNPC YES1，target票identity省略保持NULL。Rite159／169 ownerlocks移除，历史lockserial12留存，retry／transitionCD缺失，fixture reset仍5。钱包、XP与completed joins1／detaches2没有新增；保护相对cached125及129均成立。

完整Faith AST不变；159／169完整Rite AST对开案129只移除owner，对125只更新历史lock／proposalserial12；其余heads、完整tenets、政治7title与person保护保持。完整差分SHA `910eba9a825f056d1a5912aa281c4fcfac389e8740f46577c07f6628bd429122`。reader只解析新149一次，旧保存缓存复用，本补充没有解析保存。

另新增第五actual emit／release→第六ordinal5独立审查索引：范围为第五nonce10→11开案消费及permit350483继承，同六身份／PID／create／generation1。它不证明第六savednonce消费或后续新意图；ROOT正在处理的第六释放与第七提案不在本补充结论内。

0个R10成功JOIN、fullcycle=false，SDK150 fresh ready只有query信用。正常退出、Client／profile／lease闭合未发生，wholelogs仍只有108证据。NOT_GREEN。
'''.encode('utf-8'))
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.small-actual-evidence-addendum-index.v1', 'files': files})
for row in files:
    data = (OUT / row['path']).read_bytes()
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
print(json.dumps({'status': summary['status'], 'path': str(OUT), 'reference_count': len(refs),
    'actual149_payloads': payload_count, 'checks': 62,
    'addendum_sha256': sha((OUT / 'ADDENDUM.json').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=False))
