"""Create a partial first-430 evidence package from existing JSON bytes only."""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-018'
HEAD = 'dbaf5f8db2067419838b814e278d962f428dc33c'
DOCS_HEAD = '3475ba2eac392221321c9c83e62f918fd3339db1'
ALLOWED = {'inspect_existing_json.py', 'preserve_partial_first430.py'}
if {path.name for path in ROOT.iterdir()} != ALLOWED:
    raise RuntimeError('create-only PARTIAL directory contains unexpected entries')

files = [
    (BASE / 'r18-root-head-export-20261007-002/REPORT.json', 'source/export-002-REPORT.json', 'exact frozen source export and production staging', None),
    (BASE / 'r18-actual-sdk-metadata-20261007-001/RESULT.json', 'source/sdk-metadata-RESULT.json', 'actual official SDK metadata and fresh-source qualification', None),
    (RUN / 'native-profile-with-exit-inventory.json', 'binding/native-profile-with-exit-inventory.json', 'profile bytes bound by actual request 13', '0189ab2c8ec4135b8b007d4a8254cb859ae970e5fe852de75015ca9846e3c404'),
    (RUN / 'baseline-author-001/RESULT.json', 'baseline-author-001/RESULT.json', 'already completed baseline author result; one original body read', None),
    (RUN / 'baseline-author-001/STATE.json', 'baseline-author-001/STATE.json', 'already parsed baseline observations; not a new reader run', None),
    (RUN / 'baseline-author-001/TYPED-PROTECTION.json', 'baseline-author-001/TYPED-PROTECTION.json', 'already parsed typed protection with 87 checks', None),
    (RUN / 'initial0240-political-control-002/REPORT.json', 'initial0240-political-control-002/REPORT.json', 'completed pure seven-title whole political AST control', '86f1c86a25aa8a9b95830408e4f23793e57213b261b098940b7eebb438d8b5fb'),
    (RUN / 'root-request-executions/013-first430-wait/RESULT.actual.json', 'request-013/RESULT.actual.json', 'actual request/enqueue and official SDK result provenance', None),
    (RUN / 'root-request-executions/013-first430-wait/REQUEST.actual.json', 'request-013/REQUEST.actual.json', 'exact action arguments', None),
    (RUN / 'mcp-client-001/0012-r18-012-first430-reference-query.native-01.json', 'sdk-012/0012-r18-012-first430-reference-query.native-01.json', 'actual event identity and option context before action', None),
    (RUN / 'mcp-client-001/0012-r18-012-first430-reference-query.sdk-result.json', 'sdk-012/0012-r18-012-first430-reference-query.sdk-result.json', 'official SDK query result', None),
    (RUN / 'mcp-client-001/0013-r18-013-first430-wait.native-01.json', 'sdk-013/0013-r18-013-first430-wait.native-01.json', 'actual event selection and native before/after postcondition', '50ebcbfacd880194e643366ac11b4b2486befe5933260f5d5744459ed7792132'),
    (RUN / 'mcp-client-001/0013-r18-013-first430-wait.sdk-result.json', 'sdk-013/0013-r18-013-first430-wait.sdk-result.json', 'official SDK action result', None),
    (RUN / 'root-preflight-001/RESULT.json', 'initial-attempts/root-preflight-001-RESULT.json', 'original pre-game path-identity RED', None),
    (RUN / 'root-preflight-002/RESULT.json', 'initial-attempts/root-preflight-002-RESULT.json', 'subsequent preflight-only completion; not game acceptance', None),
    (RUN / 'root-profile-request-001/RESULT.json', 'initial-attempts/root-profile-request-001-RESULT.json', 'original foreground-condition RED before profile freeze', None),
]

members = []
parsed = {}
archive_path = ROOT / 'FIRST430-PARTIAL.original-json.zip'
with archive_path.open('xb') as archive_stream:
    with zipfile.ZipFile(archive_stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, member, role, expected in files:
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if expected is not None and digest != expected:
                raise RuntimeError('source bytes differ from supplied exact receipt: ' + str(source))
            obj = json.loads(data.decode('utf-8-sig'))
            parsed[member] = obj
            info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members.append({'source_path': str(source), 'archive_member': member, 'bytes': len(data), 'sha256_original_and_member': digest, 'frozen_runtime_head': HEAD, 'role': role, 'top_level_status': obj.get('status'), 'top_level_schema': obj.get('schema')})

hashes = {item['archive_member']: item['sha256_original_and_member'] for item in members}
native = parsed['sdk-013/0013-r18-013-first430-wait.native-01.json']
query = parsed['sdk-012/0012-r18-012-first430-reference-query.native-01.json']
root_request = parsed['request-013/RESULT.actual.json']
selection = native['result']['event_selection']
before = native['snapshot_before']
after = native['snapshot_after']
baseline = parsed['baseline-author-001/RESULT.json']
typed = parsed['baseline-author-001/TYPED-PROTECTION.json']
political = parsed['initial0240-political-control-002/REPORT.json']
preflight_red = parsed['initial-attempts/root-preflight-001-RESULT.json']
profile_red = parsed['initial-attempts/root-profile-request-001-RESULT.json']
cutoff = root_request['finished_at_utc']
facts = {
    'status': 'PARTIAL_NOT_GREEN',
    'cutoff_evidence_utc': cutoff,
    'runtime_frozen_head': HEAD,
    'documentation_fix_head': DOCS_HEAD,
    'profile_sha256': native['profile_sha256'],
    'session_id': native['session_id'],
    'pid': selection['bridge_pid'],
    'connection_generation': selection['connection_generation'],
    'actor': before['played_character']['character_id'],
    'query_event_definition': query['result']['event_definition_key'],
    'query_event_instance_id': query['result']['current_event_instance_id'],
    'first430_native_status': native['status'],
    'event_selection': selection,
    'wallet_before': {key: before[key] for key in ['played_character_gold', 'played_character_prestige', 'played_character_piety']},
    'wallet_after': {key: after[key] for key in ['played_character_gold', 'played_character_prestige', 'played_character_piety']},
    'SDK13_isError': root_request['sdk_isError'],
    'baseline_author_game_calls': baseline['game_calls'],
    'baseline_author_original_save_body_reads': baseline['save_body_reads'],
    'baseline_typed_check_count': len(typed['checks']),
    'baseline_protection_checks_match': typed['protection_checks_match'],
    'political_title_count': len(political['political_titles']),
    'political_complete_AST_matches': political['complete_political_AST_matches'],
    'first_preflight_original_status': preflight_red['status'],
    'first_preflight_original_error': preflight_red['error'],
    'first_profile_request_original_status': profile_red['status'],
    'first_profile_request_original_error': profile_red['error'],
    'normal_exit': 'UNVALIDATED at this cutoff',
    'formal_acceptance': None,
    'new_T_credit': None,
    'C3_credit': None,
    'I4_credit': None,
    'whole_business_status': 'NOT_GREEN',
    'this_archive_operation': {'save_body_reads': 0, 'binary_reads': 0, 'SDK_calls': 0, 'game_calls': 0, 'process_mutations': 0, 'main_mutations': 0, 'retests': 0, 'CI_polls': 0},
}
with (ROOT / 'FIRST430-PARTIAL.facts.json').open('x', encoding='utf-8') as stream:
    json.dump(facts, stream, indent=2, ensure_ascii=False)
    stream.write('\n')

report = f'''# R0018 首个 430：PARTIAL 快照

本报告仅冻结到真实 request 13 完成时刻 `{cutoff}`。它是 append-only 的 **PARTIAL，整体业务 NOT_GREEN**；后续 runtime 结果应另建报告，不覆盖此快照。不赋予 formal、新 T、C3 或 I4 信用；正常退出在本截止点为 **UNVALIDATED**。

当前 cold 实例为 PID `{selection['bridge_pid']}`、connection generation `{selection['connection_generation']}`、角色 `{before['played_character']['character_id']}`、session `{native['session_id']}`。运行源码、编译 lineage 和 SDK profile 均冻结到 `{HEAD}`，profile SHA-256 为 `{native['profile_sha256']}`。文档修复提交 `{DOCS_HEAD}` 的 CI 成功属于文档提交；本实机输入没有以它重新解释。源码 export-002 与实际 SDK metadata 的原 JSON 随包保留；metadata 的 28 项工具清单属于既有源绑定事实，不替代业务验收。

既有 baseline author 的 `RESULT.json` 记录 `game_calls=0`、一次原保存正文解析；`STATE.json` 和 `TYPED-PROTECTION.json` 已产生，后者有 `{len(typed['checks'])}` 项保护检查并记录 `protection_checks_match={str(typed['protection_checks_match']).lower()}`，即既有 87/87 匹配。此处只归档已经解析的 JSON，没有再读取存档正文或重跑 reader。STATE 的旧 schema/source-head lineage 和 `INCOMPLETE_NATIVE_QUALIFICATION` 原标签保持原样，不能把 baseline 保护检查改写为正式回合通过。

已完成的纯政治对照包含 `{len(political['political_titles'])}` 个政治 title，`complete_political_AST_matches={str(political['complete_political_AST_matches']).lower()}`；原报告 SHA-256 为 `{hashes['initial0240-political-control-002/REPORT.json']}`。它证明原 0240 与 initial cold 的完整政治 AST/holder 对照，不能推断此前没有发生过动作，也不提供 C3/I4 或正式信用。

request 12 的实际 native query 确认事件定义 `{query['result']['event_definition_key']}`、instance `{query['result']['current_event_instance_id']}`。request 13 通过官方 SDK 执行 `select-event-option-3`，native option index `{selection['selected_native_option_index']}`；原 SDK `isError={str(root_request['sdk_isError']).lower()}`。native 原回执记录 `{native['status']}`、`postcondition_verified={str(selection['postcondition_verified']).lower()}`：旧 instance `{selection['old_event_instance_id']}` 关闭，后续 active event 为 null，revision `{selection['starting_revision']} → {selection['ending_revision']}`，同一 PID/generation，日期保持 `{before['date_raw']}`。这确认修复后的 native dispatch 在首个 430 的实际 SDK 路径上完成了事件后置读回，范围只限本次选择。

本次 native before/after 钱包保持相同：gold raw `{before['played_character_gold']['raw']}`、prestige raw `{before['played_character_prestige']['raw']}`、piety raw `{before['played_character_piety']['raw']}`，scale 均为 `100000`；stress 仍为 `0`。它不证明 commit fee、完整制度生命周期、C3 或 I4 已闭环。

首个 430 的 native JSON SHA-256 为 `{hashes['sdk-013/0013-r18-013-first430-wait.native-01.json']}`；对应 ROOT request `RESULT.actual.json` SHA-256 为 `{hashes['request-013/RESULT.actual.json']}`。本报告依据 actual native 后置结果，不用 request/enqueue ACK 替代成功。

早期失败分别保留其层次：`root-preflight-001/RESULT.json` 原 `RED` 为 `{preflight_red['error']}`，发生于启动前路径身份检查，原文件记录未创建游戏、未注入；`root-preflight-002/RESULT.json` 后续仅完成 `ACTUAL_NEW_FORMAL_PREFLIGHT_ONLY_NO_GAME`，不是实机业务通过。`root-profile-request-001/RESULT.json` 原 `RED` 为 `{profile_red['error']}`，属于 profile 冻结前的现场前台条件，不等同 native dispatch 故障。baseline 原 RESULT 还保留 `original_outer_exit_code=1` 和 compiler Defender `settings_failed` 的既有事实，不外推为全局 native build GREEN。

首次 source export-001 的指定位置没有可归档的直接 JSON 正文。按 ROOT 交接，原 stdout 保留在外置工具历史；本包将该项列为“未归档”，不猜正文、不补造错误或评级。

本包的 [FIRST430-PARTIAL.original-json.zip](FIRST430-PARTIAL.original-json.zip) 只含选定的现有 JSON 原字节；[FIRST430-PARTIAL.inventory.json](FIRST430-PARTIAL.inventory.json) 给出每个成员的原路径、SHA、层次与冻结 HEAD；[FIRST430-PARTIAL.facts.json](FIRST430-PARTIAL.facts.json) 是明确标为 PARTIAL 的摘要。没有保存二进制、存档正文或全量运行树；原外置 attempt 不移动、不删除、不改写。所有进一步结论仍须由 ROOT 在原 live 链上取得。

报告代理只做现有 JSON 读取和独立 worktree 的 create-only 写入；SDK/game/process/main mutation、retest 和 CI poll 均为零。ROOT 持有当前 live 执行链，报告归档与其并行；日报拓扑字段交由 ROOT 合并，避免编辑冲突。
'''
with (ROOT / 'PARTIAL-20261007-FIRST430.md').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(report)
archive_data = archive_path.read_bytes()
inventory = {
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'PARTIAL_NOT_GREEN',
    'cutoff_evidence_utc': cutoff,
    'runtime_frozen_head': HEAD,
    'archive': {'path': archive_path.name, 'bytes': len(archive_data), 'sha256': hashlib.sha256(archive_data).hexdigest(), 'members': len(members), 'member_bytes': 'exact original JSON bytes'},
    'members': members,
    'not_archived': [{'source_path': str(BASE / 'r18-root-head-export-20261007-001'), 'reason': 'no direct JSON body found at the supplied location; original stdout remains in external tool history per ROOT; no content or rating inferred'}],
    'partial_scope': {'normal_exit': 'UNVALIDATED', 'formal': None, 'new_T': None, 'C3': None, 'I4': None, 'whole_business': 'NOT_GREEN'},
    'authoring_actions': facts['this_archive_operation'],
}
with (ROOT / 'FIRST430-PARTIAL.inventory.json').open('x', encoding='utf-8') as stream:
    json.dump(inventory, stream, indent=2, ensure_ascii=False)
    stream.write('\n')
print(json.dumps({'report': str(ROOT / 'PARTIAL-20261007-FIRST430.md'), 'archive': inventory['archive'], 'request13_result_sha256': hashes['request-013/RESULT.actual.json'], 'scope': inventory['partial_scope']}, indent=2, ensure_ascii=False), flush=True)
