"""Preserve only existing JSON needed for the two rounds and unresolved lock."""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-018'
HEAD = 'dbaf5f8db2067419838b814e278d962f428dc33c'
CUTOFF = '2026-10-07T03:04:00Z'
allowed = {'inspect_existing_json.py', 'inspect_round_facts.py', 'inspect_final_fact_fields.py', 'preserve_rounds_lock_partial.py'}
if {path.name for path in ROOT.iterdir()} != allowed:
    raise RuntimeError('new append-only evidence directory contains unexpected entries')

selected = []

def add(source, member, role, expected=None):
    selected.append({'source': Path(source), 'member': member, 'role': role, 'expected': expected})

for round_number in [1, 2]:
    directory = RUN / f'B3-r{round_number}-pending-author-001'
    for name in ['STATE.json', 'TYPED-PROTECTION.json', 'RESULT.json']:
        expected = None
        if round_number == 2:
            expected = {
                'STATE.json': '13062d7242beaf1897c23de67f9425d68d7fd43b3b46ab089968439353eecf98',
                'TYPED-PROTECTION.json': '42f43a6219162ace5ee26f16d16a2a25343d7e679730e6ef1ed2ea8009628707',
                'RESULT.json': '06f50ab7f4f7a60be373222270e5186910768fe83c086857ca9a73bcd13c9c69',
            }[name]
        add(directory / name, f'round-{round_number}/pending-author-{name}', 'existing observed pending state or protection/author result', expected)
    cancel_dir = RUN / f'formal-r{round_number}-cancel-001'
    add(cancel_dir / 'RESULT.actual.json', f'round-{round_number}/cancel-RESULT.actual.json', 'actual four-call cancellation sequence provenance')
    add(cancel_dir / 'FINAL-SNAPSHOT.actual.json', f'round-{round_number}/cancel-FINAL-SNAPSHOT.actual.json', 'actual same-process post-cancel snapshot')
    cancel_result = json.loads((cancel_dir / 'RESULT.actual.json').read_text(encoding='utf-8'))
    confirmed = cancel_result['calls'][-1]['original_native_receipt']
    add(confirmed['path'], f'round-{round_number}/cancel-confirm-native.json', 'actual final native cancellation receipt, rather than command exit ACK', confirmed['sha256'])

for attempt in [1, 2]:
    add(BASE / f'r18-root-B3-r2-pending-materialize-execution-20261007-{attempt:03d}/RESULT.actual.json', f'SAVE72-recovery/materializer-{attempt:03d}-RESULT.actual.json', 'original failed attempt or separate actual successful Python materialization')
add(RUN / 'B3-r2-pending-author-001/CHECKPOINT-TRANSITION.actual.json', 'SAVE72-recovery/CHECKPOINT-TRANSITION.actual.json', 'existing same-frame checkpoint transition evidence')
for name in ['INDEX.json', 'HOTFIX-SOURCE-PROJECTION.actual.json']:
    add(BASE / 'r18-checkpoint-author-sourceonly-20261008-003' / name, 'source-preparation/cp003-' + name, 'source-only timing-path correction; execution credit comes from separate actual results')
add(BASE / 'r18-formal-capture-root-sourceonly-20261007-004/INDEX.json', 'source-preparation/capture004-INDEX.json', 'future capture source preparation only; no actual capture', 'f0b8012f6b3e91ea7156253695a5ad0fa05e0f5296ebbcc8e5c5d6df733fa9c7')

for number, label in [(72, '072-r2-pending-save'), (86, '086-r2-cancel-cleanup-save')]:
    result_path = RUN / 'root-request-executions' / label / 'RESULT.actual.json'
    add(result_path, f'SDK-{number}/ROOT-RESULT.actual.json', 'actual SDK save request provenance; not an unlock acknowledgement')
    result = json.loads(result_path.read_text(encoding='utf-8'))
    receipt = result['official_native_copies'][0]
    add(receipt['path'], f'SDK-{number}/native.json', 'existing native checkpoint result and same-process frame', receipt['sha256'])

for number in [80, 84, 88]:
    paths = sorted((RUN / 'mcp-client-001').glob(f'{number:04d}-*.native-01.json'))
    if len(paths) != 1:
        raise RuntimeError('ambiguous saved native-copy identity')
    native_path = paths[0]
    request_id = native_path.name.split('-', 1)[1].removesuffix('.native-01.json')
    add(native_path, f'SDK-{number}/native-copy.json', 'native pre-dispatch rejection' if number == 80 else 'Python unresolved-result lock; native-copy filename does not change the error layer')
    add(RUN / 'root-request-executions' / request_id / 'RESULT.actual.json', f'SDK-{number}/ROOT-RESULT.actual.json', 'actual official SDK request and envelope provenance')

objects = {}
inventory = []
archive_path = ROOT / 'ROUNDS-LOCK-0304.original-json.zip'
with archive_path.open('xb') as archive_stream:
    with zipfile.ZipFile(archive_stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in selected:
            data = item['source'].read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if item['expected'] is not None and digest != item['expected']:
                raise RuntimeError('source bytes differ from supplied original: ' + str(item['source']))
            obj = json.loads(data.decode('utf-8-sig'))
            objects[item['member']] = obj
            info = zipfile.ZipInfo(item['member'], date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            inventory.append({'archive_member': item['member'], 'source_path': str(item['source']), 'bytes': len(data), 'sha256_original_and_member': digest, 'frozen_runtime_head': HEAD, 'role': item['role'], 'original_status': obj.get('status'), 'original_schema': obj.get('schema')})

hashes = {item['archive_member']: item['sha256_original_and_member'] for item in inventory}
rounds = []
for number in [1, 2]:
    state = objects[f'round-{number}/pending-author-STATE.json']
    typed = objects[f'round-{number}/pending-author-TYPED-PROTECTION.json']
    author = objects[f'round-{number}/pending-author-RESULT.json']
    members = state['roster']['members']
    iterable = members.values() if isinstance(members, dict) else members
    votes = [{key: row.get(key) for key in ['character_id', 'was_elector', 'was_player', 'player_yes', 'vote']} for row in iterable if row.get('character_id') in [31254, 65865]]
    cancel = objects[f'round-{number}/cancel-RESULT.actual.json']
    final = objects[f'round-{number}/cancel-FINAL-SNAPSHOT.actual.json']
    confirmed = objects[f'round-{number}/cancel-confirm-native.json']
    rounds.append({'round_number': number, 'raw_round': state['round'], 'identity': state['identity'], 'schools': state['schools'], 'human_and_NPC_votes': votes, 'original_STATE_assessment': state.get('assessment'), 'original_observation_checks_match': state.get('observation_checks_match'), 'typed_checks': len(typed['checks']), 'typed_protection_checks_match': typed['protection_checks_match'], 'author_game_calls': author['game_calls'], 'author_original_save_body_reads': author['save_body_reads'], 'cancel_status': cancel['status'], 'cancel_confirm_native_status': confirmed.get('status'), 'cancel_final_frame': {key: final.get(key) for key in ['revision', 'native_revision', 'snapshot_id', 'active_event', 'paused', 'date_raw']}, 'formal_credit': None})

errors = []
for number in [80, 84, 88]:
    native = objects[f'SDK-{number}/native-copy.json']
    result = objects[f'SDK-{number}/ROOT-RESULT.actual.json']
    before = native['snapshot_before']
    errors.append({'SDK_sequence': number, 'original_status': native['status'], 'original_reason': native['reason'], 'layer': 'native pre-dispatch binding refusal' if number == 80 else 'Python unresolved decision-action claim', 'SDK_envelope_isError': result.get('sdk_isError'), 'before_revision': before['revision'], 'before_native_revision': before['native_revision'], 'bridge_pid': before['diagnostics']['bridge_pid'], 'connection_generation': before['diagnostics']['connection_generation'], 'native_copy_sha256': hashes[f'SDK-{number}/native-copy.json']})

facts = {
    'status': 'PARTIAL_NOT_GREEN', 'runtime_cutoff_utc': CUTOFF, 'runtime_frozen_head': HEAD,
    'rounds': rounds, 'SDK_errors': errors,
    'materializer001_exit_code': objects['SAVE72-recovery/materializer-001-RESULT.actual.json']['exit_code'],
    'materializer002_exit_code': objects['SAVE72-recovery/materializer-002-RESULT.actual.json']['exit_code'],
    'cleanup86_native_status': objects['SDK-86/native.json'].get('status'),
    'source_cp003_original_status': objects['source-preparation/cp003-INDEX.json'].get('status'),
    'capture004_original_status': objects['source-preparation/capture004-INDEX.json'].get('status'),
    'normal_exit': 'UNVALIDATED at runtime cutoff', 'formal': None, 'new_T': None, 'C3': None, 'I4': None, 'whole_business': 'NOT_GREEN',
    'this_documentation_operation': {'SDK_calls': 0, 'game_calls': 0, 'process_mutations': 0, 'main_writes': 0, 'save_body_reads': 0, 'source_binary_reads': 0, 'retests': 0, 'CI_polls': 0, 'commit_push': 0},
}
with (ROOT / 'ROUNDS-LOCK-0304.facts.json').open('x', encoding='utf-8') as stream:
    json.dump(facts, stream, indent=2, ensure_ascii=False)
    stream.write('\n')

report = f'''# R0018 两轮自然 NO、SAVE72 恢复及 R3 未决锁：PARTIAL

本追加快照的实机截止点为 `{CUTOFF}`，冻结运行来源仍为 `{HEAD}`，PID `5920`、generation `1`、session `9cdca47579f54d3191efdecdb7400374`。整体 **NOT_GREEN**；没有 formal、新 T、C3 或 I4 信用，正常退出在本截止点仍 **UNVALIDATED**。ROOT 后续正常 close 应另写 CLOSED 追加记录；本文件不覆盖首个 430 报告，也不吸收截止点之后的退出结果。

两轮原 STATE 中 rite `169` 的 school 均记录 `total=2`、`yes=1`、`signed=0`：人类 `31254` 为 `was_player=1/player_yes=1/vote=1`，NPC `65865` 为 `was_player=0/vote=0`，保留自然 NO。这里“2/1”指选举人数/YES 数；R1 的原 serial/nonce/phase 为 `1/2/2`，R2 为 `2/4/2`。两轮尚未够 quorum，pending 本来不是正式通过。

两份 `TYPED-PROTECTION.json` 均有 87 项检查且 `protection_checks_match=true`，只提供本阶段保护信用。两份 STATE 原 `observation_checks_match=false`、`assessment=OBSERVED_CONTRACT_MISMATCH`、实际通过字段 null 均保留，不以 typed 87 项替换整体原评级。R2 STATE 原 SHA-256 为 `{hashes['round-2/pending-author-STATE.json']}`，typed 原 SHA-256 为 `{hashes['round-2/pending-author-TYPED-PROTECTION.json']}`。

`formal-r1-cancel-001` 与 `formal-r2-cancel-001` 的实际结果均为 `EXPLICIT_STEP_ACTUALLY_COMPLETED`；四次调用的原 provenance、最后 native confirmation 和实际 final snapshot 已保存。取消后的 frame 分别为 revision/native `16/15` 与 `25/24`，active event 均 null，仍是同一 PID/generation。取消完成不等于制度提交或完整产品通过。

SAVE72 的原 SDK 保存与 G2/G3 链保持既有来源。首次 source002 materializer 原执行 exit `{facts['materializer001_exit_code']}` 保留在 `r18-root-B3-r2-pending-materialize-execution-20261007-001/RESULT.actual.json`，原 stdout/stderr 的来源与 SHA 也仍在该原 JSON 中。source cp003 仅补既有白名单中的一个诊断路径 `last_heartbeat.snapshot_observer_12002.last_read_ms` 及合同 SHA pin；原 `HOTFIX-SOURCE-PROJECTION.actual.json` 记录既有 native/save/G2/G3/SDK/descriptor 与业务 frame 检查未变。

后续独立 materializer002 已真实执行，exit `{facts['materializer002_exit_code']}`，RESULT SHA-256 为 `{hashes['SAVE72-recovery/materializer-002-RESULT.actual.json']}`。R2 author001 已真实执行，RESULT SHA-256 为 `{hashes['round-2/pending-author-RESULT.json']}`，原 `game_calls=0/save_body_reads=1`。这是一段保留同一 live PID 的纯 Python materializer/author 恢复；原 author 只解析一次已保存正文，本报告代理没有再次读取正文。不能用 source-only INDEX 的准备状态代替这些实际执行，也不能把恢复记为 formal 成功。

R3 的三次错误必须分层：

| SDK sequence | 原状态与 reason | 层次 |
| --- | --- | --- |
| 80 | `RED`；`_NativeCommandRejectedError: native gameplay step failed: exact_alive_paused_decision_action_binding_changed` | 首次 native 绑定校验在派发前拒绝 |
| 84 | `RED`；`BridgeUnavailableError: decision action already claimed with an unresolved result; no retry at any revision` | Python 未决 decision-action claim 锁 |
| 88 | 同上 Python reason | cleanup SAVE86 后仍有同一类 Python 锁 |

SDK84/88 的 `native-01.json` 文件名和统一 receipt schema 不能把 Python 拒绝变成 native 再次派发；此前摘要的“native 重复拒绝”层次表述以这里的原 reason 纠正。原 SDK envelope 的 `isError=false` 也不能覆盖内层 `status=RED`。本归档没有重新调用或尝试解除锁。

cleanup SAVE86 的原 ROOT RESULT SHA-256 为 `{hashes['SDK-86/ROOT-RESULT.actual.json']}`，保存成功后 frame 为 revision/native `26/25`；随后 SDK88 的 before frame 也是 `26/25`，仍返回 Python 未决锁。因此换 revision 或 cleanup save 没有在本次链上解除锁，不能补写为可重试或已恢复。

cp003 的原 INDEX SHA-256 为 `{hashes['source-preparation/cp003-INDEX.json']}`，保留其最初 source-only 标签；materializer/one-body 的实际信用仅来自后续执行结果。capture004 的 INDEX SHA-256 为 `{hashes['source-preparation/capture004-INDEX.json']}`，仅是 future source preparation，**没有实际 capture**。这些源准备材料单独归档，不作为退出、formal 或新 T 的实际观测。

选定的既有 JSON 原字节收在 [ROUNDS-LOCK-0304.original-json.zip](ROUNDS-LOCK-0304.original-json.zip)，每个成员的原路径、SHA、冻结来源与证据层次见 [ROUNDS-LOCK-0304.inventory.json](ROUNDS-LOCK-0304.inventory.json)；[ROUNDS-LOCK-0304.facts.json](ROUNDS-LOCK-0304.facts.json) 保留上述原评级及错误层次。没有复制可执行文件、存档正文、全部运行树或整份源码；原外置 attempt 留在原处。

报告代理只读取现有 JSON，并向独立 worktree 的此新后缀目录 create-only 写入；主树、SDK、游戏、进程、存档正文、CI、重测及提交推送操作均为零。ROOT 当前执行链不因本包被重启或重解释。
'''
with (ROOT / 'PARTIAL-20261007-ROUNDS-LOCK-0304.md').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(report)
archive_bytes = archive_path.read_bytes()
package = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'runtime_cutoff_utc': CUTOFF, 'status': 'PARTIAL_NOT_GREEN', 'runtime_frozen_head': HEAD, 'archive': {'path': archive_path.name, 'bytes': len(archive_bytes), 'sha256': hashlib.sha256(archive_bytes).hexdigest(), 'members': len(inventory), 'member_bytes': 'exact original JSON bytes'}, 'members': inventory, 'scope': {'normal_exit': 'UNVALIDATED at cutoff', 'formal': None, 'new_T': None, 'C3': None, 'I4': None, 'whole_business': 'NOT_GREEN'}, 'authoring_actions': facts['this_documentation_operation']}
with (ROOT / 'ROUNDS-LOCK-0304.inventory.json').open('x', encoding='utf-8') as stream:
    json.dump(package, stream, indent=2, ensure_ascii=False)
    stream.write('\n')
print(json.dumps({'report': str(ROOT / 'PARTIAL-20261007-ROUNDS-LOCK-0304.md'), 'archive': package['archive'], 'materializer002_SHA': hashes['SAVE72-recovery/materializer-002-RESULT.actual.json'], 'cleanup86_ROOT_SHA': hashes['SDK-86/ROOT-RESULT.actual.json'], 'scope': package['scope']}, indent=2, ensure_ascii=False), flush=True)
