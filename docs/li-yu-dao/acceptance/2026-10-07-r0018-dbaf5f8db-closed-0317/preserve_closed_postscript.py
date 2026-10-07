import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
MAIN = Path('C:/workspace/ck3_eternal_recurrence')
RUN = BASE / 'live-attempt-018'
OUT = Path(__file__).resolve().parent
HEAD = 'dbaf5f8db2067419838b814e278d962f428dc33c'
CUTOFF = '2026-10-07T03:17:47.829692+00:00'
members = {}

def read_json(path):
    return json.loads(Path(path).read_bytes())

def add(path, expected=None, scope='actual R18 closure evidence'):
    path = Path(path)
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected is not None and digest != expected:
        raise RuntimeError('Exact original bytes changed: ' + str(path))
    path_key = str(path.resolve())
    if path_key not in members:
        member = path.relative_to(BASE).as_posix()
        members[path_key] = {'source_path': path.as_posix(), 'member': member,
                             'bytes': len(data), 'sha256': digest, 'source_head': HEAD,
                             'scope': scope, 'data': data}
    return members[path_key]

def add_ref(ref, scope='actual R18 closure evidence'):
    return add(ref['path'], ref.get('sha256'), scope)

def write_new(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)

closed = BASE / 'r18-actual-closed-boundary-20261007-001'
index_path = closed / 'INDEX.json'
add(index_path, 'c26113977c50c29c649c3fa40e7130d952a387bb9f74ae99ec37dbcb50e350c1')
index = read_json(index_path)
for key in ('review', 'verifier', 'verifier_dependencies', 'request', 'author_source'):
    add_ref(index[key], 'original closed-boundary author/verifier inputs or source; no replay')
review = read_json(index['review']['path'])
for value in review.values():
    if isinstance(value, dict) and 'path' in value and 'sha256' in value:
        add_ref(value)
add(closed / 'VERIFIED.actual.json')
verified = read_json(closed / 'VERIFIED.actual.json')
for value in verified['actual_original_exec_process_results'].values():
    add_ref(value, 'original retained execution session completion, scope preserved verbatim')
deps = read_json(index['verifier_dependencies']['path'])
for value in deps.values():
    if isinstance(value, dict) and 'path' in value and 'sha256' in value:
        add_ref(value, 'original closure verifier dependency; archived without executing')

author_execution_path = BASE / 'r18-root-closed-boundary-author-execution-20261007-001/RESULT.actual.json'
add(author_execution_path, '410d8fa89f0938d42b3604e7c8e66e5f9a74e7cd0c543ebc21d6aaa47627c780')
author_execution = read_json(author_execution_path)
for key in ('argv_input', 'stdout', 'stderr'):
    add_ref(author_execution[key], 'actual original author execution provenance')

phase_results = {}
for name in ('r18-root-guarded-client-close-20261007-001',
             'r18-root-guarded-keeper-stop-20261007-001',
             'r18-root-guarded-screen-release-20261007-001'):
    result_path = BASE / name / 'RESULT.actual.json'
    add(result_path)
    result = read_json(result_path)
    phase_results[name] = result
    for value in result['result'].values():
        if isinstance(value, dict) and 'path' in value and 'sha256' in value:
            add_ref(value)
add(RUN / 'root-request-executions/096-normal-exit-original-handle-observation/RESULT.actual.json')

archive_path = OUT / 'CLOSED-0317.original-evidence.zip'
with archive_path.open('xb') as raw:
    with zipfile.ZipFile(raw, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in sorted(members.values(), key=lambda value: value['member']):
            info = zipfile.ZipInfo(item['member'], date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, item['data'], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
archive_data = archive_path.read_bytes()
inventory = {
    'schema': 'lyd.r18.closed-postscript.original-evidence-inventory.v1',
    'source_head': HEAD, 'runtime_cutoff_utc': CUTOFF,
    'archived_at_utc': datetime.now(timezone.utc).isoformat(),
    'archive': {'path': archive_path.name, 'bytes': len(archive_data),
                'sha256': hashlib.sha256(archive_data).hexdigest(), 'members': len(members)},
    'entries': [{key: value for key, value in item.items() if key != 'data'}
                for item in sorted(members.values(), key=lambda value: value['member'])],
    'scope': 'Exact selected saved JSON, original close-author/verifier source and actual execution stdio only. No binary or save body.',
    'replayed_checks': 0, 'SDK_calls': 0, 'game_calls': 0, 'process_lookups': 0,
    'main_tree_writes': 0, 'commit_push': 0,
}
write_new('CLOSED-0317.inventory.json', json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')

sdk = read_json(review['original_handle_observation']['path'])
sdk_inner = sdk['structuredContent']
census = read_json(review['process_absence']['path'])
release = read_json(review['release_receipt']['path'])
keeper_completion = read_json(verified['actual_original_exec_process_results']['keeper']['path'])
holder_completion = read_json(verified['actual_original_exec_process_results']['holder']['path'])
facts = {
    'schema': 'lyd.r18.closed-postscript.saved-facts.v1', 'source_head': HEAD,
    'runtime_cutoff_utc': CUTOFF, 'normal_exit': sdk_inner,
    'original_exit_observation_limits': verified['actual_exit_observation_limits'],
    'original_exec_wrapper_capture_scopes': {
        'keeper': keeper_completion['raw_tool_result'].get('output_capture_scope'),
        'holder': holder_completion['raw_tool_result'].get('output_capture_scope'),
    },
    'release_sequence': release['event']['sequence'], 'release_state': release['task']['state'],
    'release_resources': release['task']['resources'],
    'same_original_identities_absent': census['same_original_identities_absent'],
    'no_current_managed_game_or_native_services': census['no_current_managed_game_or_native_services'],
    'original_identities': census['original_identities'],
    'boundary_author_actual_exit_code': author_execution['exit_code'],
    'boundary_index_original_status': index['status'],
    'whole_status': 'NOT_GREEN', 'formal_acceptance': None, 'new_T': None, 'C3': None, 'I4': None,
    'autosave_verified': False,
    'earlier_partials_unchanged': [
        '../2026-10-07-r0018-dbaf5f8db/PARTIAL-20261007-FIRST430.md',
        '../2026-10-07-r0018-dbaf5f8db-rounds-lock-0304-002/PARTIAL-20261007-ROUNDS-LOCK-0304.md'],
}
write_new('CLOSED-0317.facts.json', json.dumps(facts, ensure_ascii=False, indent=2) + '\n')

source_specs = [
    ('mod_li_yu_dao/common/scripted_effects/lyd_i3b_setup_effects.txt', 'name = lyd_i3b_vote value = -1'),
    ('mod_li_yu_dao/common/scripted_effects/lyd_i3b_response_effects.txt', 'name = lyd_i3b_vote value = $YES$'),
    ('mod_li_yu_dao/events/lyd_i3b_institution_events.txt', 'lyd.411 ='),
]
source_refs = []
for relative, needle in source_specs:
    path = MAIN / relative
    data = path.read_bytes()
    lines = data.decode('utf-8-sig').splitlines()
    matches = [{'line': line_number, 'text': text} for line_number, text in enumerate(lines, 1) if needle in text]
    if not matches:
        raise RuntimeError('Requested existing source line unavailable: ' + relative)
    source_refs.append({'source_head': HEAD, 'path': relative, 'original_path': path.as_posix(),
                        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'selected_original_lines': matches})
write_new('NATURAL-NO.source-provenance.json', json.dumps({
    'schema': 'lyd.r18.natural-no.saved-source-interpretation.v1', 'source_head': HEAD,
    'scope': 'Source interpretation for actual saved R1/R2 vote0 only; no runtime replay or R3 forecast.',
    'sources': source_refs,
    'interpretation': 'The saved NPC vote0 is the NO callback value, not the untouched initial -1; original R1/R2 school counts and assessment remain unchanged.',
}, ensure_ascii=False, indent=2) + '\n')

report = '''# R0018 CLOSED 追加后记：原 HANDLE 退出、实际缺席与释放

本后记覆盖原件截止 `2026-10-07T03:17:47.829692+00:00`，运行来源仍是冻结的 `dbaf5f8db2067419838b814e278d962f428dc33c`。原游戏 PID `5920`、creation FILETIME `134358115483546531`、native generation `1`、session `9cdca47579f54d3191efdecdb7400374`。**本轮正常退出现已取得实际信用**：`TYPED_NORMAL_EXIT_AND_ORIGINAL_PROCESS_HANDLE_EXIT0`；ROOT 的实际闭合边界状态为 `ACTUAL_R18_CLOSED_RELEASED_BOUNDARY_VERIFIED`。整体业务仍 **NOT_GREEN**，没有 formal、新 T、C3 或 I4 信用，autosave 仍未验。

FIRST430 与 03:04 两轮 PARTIAL 是各自截止点的原快照，保持原样。它们当时的退出 `UNVALIDATED` 不再代表本轮最终退出状态；后续判断须同时读取本后记。两轮 STATE 原 mismatch、NPC 自然 NO、两 cancel、首次 materializer 失败、SDK80 native 派发前拒绝和 SDK84/88 Python 未决锁都保留。

SDK96 原记录为 `process_exit_observed_zero`，`typed_normal_exit_observed=true`；预确认原 retained HANDLE 的初始 wait `258`，最终 wait `0`、exit `0`，并核对原 PID 和创建身份。原 SDK SHA-256 为 `45cff8feb685cd9b65cd2853fa0b714d9df9889cea537058afb763dc43ee7063`，对应 native receipt SHA-256 为 `d461504832780fff672bb3b6a2d7091a5b22984beb219ad21488735ad452d202`。其嵌套 `native_observation` 保留中间 `dispatch_pending`、`orderly_exit_verified=false`，不把这些旧阶段字段重写；最终实际信用来自 typed 退出与独立原 HANDLE 的 exit 0。ROOT 已有的 VERIFIED 原件另记录 terminal native ACK 和 normal-exit callback 核验成功。

Client PID `16100` 与 keeper PID `11024` 的关闭前保留原 HANDLE 均实际 wait `0`、exit `0`；原创建身份分别保留。Client 正常 close 的 response 与 `session-closed.json` 已归档；keeper 实际 FINAL 的 `thread_exited=true`，last sequence `3535`。原 holder 执行 session 是 **37726**，原 keeper 执行 session 是 `55834`，两原执行 completion 的 exit 均为 `0`。keeper completion 的 stdout **只保全实际回调中的首个完整行投影**，其原件明确写出完整回调仍在工具 transcript；不能把该投影宣称为完整 stdout。原 helper HANDLE exit 0 提供独立证明。

实际 screen CAS release 的 event sequence 为 `3536`，task state `done`，resources 为空，原 RELEASE SHA-256 为 `fc835cd90a5c12f88345c7298ffcc9c5d70580a48700f521e0ad37c3f04f1030`。这来自已保存的实际回执，本报告没有再调用任务总线。keeper FINAL 自身的 `screen_released=false` 保留；实际 release 属于后续 ROOT CAS 阶段。

ROOT 于 `03:17:36.669198Z` 的实际 post-release census 记录 game/client/keeper/holder 四个原 PID/创建身份均缺席，且 `no_current_managed_game_or_native_services=true`；该原件 SHA-256 为 `3f8c41a29657e3b955118da084070fa021c6a4b895bc9e677fe2d370c4b0784a`。Steam 明确在此 census 的闭合范围之外。ROOT 的闭合边界作者原 execution RESULT 于 `03:17:47.829692Z` 完成，actual exit `0`，SHA-256 为 `410d8fa89f0938d42b3604e7c8e66e5f9a74e7cd0c543ebc21d6aaa47627c780`，automatic retry 为 false。作者产生的 INDEX、PREVIOUS-BOUNDARY、VERIFIED 与原 verifier/author inputs 分层保存；本报告代理没有重复执行作者或 verifier。

R1/R2 自然 NO 的解释有冻结源码支持：setup 原第 65 行把 vote 初始化为 `-1`，response 原第 4 行仅在实际 vote effect 回调中设为 `$YES$`，event 411 原第 4 行给 YES/NO 分别传 `1/0`，AI base 分别为 `60/40`。所以本轮保存的 NPC `65865 vote=0` 已是 NO 回调值，不能当成未处理的初始值。精确源码原文件 SHA 和所引原行见 [NATURAL-NO.source-provenance.json](NATURAL-NO.source-provenance.json)。这一解释只用于已保存的 R1/R2，不预测 R3，也不预填任何 YES。

选定的实际原 JSON、execution stdio、闭合 verifier/author 和必要依赖源码以原 bytes 保存在 [CLOSED-0317.original-evidence.zip](CLOSED-0317.original-evidence.zip)。完整来源与 SHA 见 [CLOSED-0317.inventory.json](CLOSED-0317.inventory.json)，分层原事实见 [CLOSED-0317.facts.json](CLOSED-0317.facts.json)。没有可执行文件、存档正文或整份 runtime/source 树。

本后记 create-only 写入独立 worktree 的新目录。报告代理主树写入、SDK/游戏调用、进程查询/操作、任务总线调用、CI、重复 checks、commit/push 均为零。原运行和失败证据没有移动、删除或改写。
'''
write_new('CLOSED-POSTSCRIPT-20261007-0317.md', report)
print(json.dumps({'report': str(OUT / 'CLOSED-POSTSCRIPT-20261007-0317.md'),
                  'archive': inventory['archive'], 'source_line_numbers': [[entry['line'] for entry in ref['selected_original_lines']] for ref in source_refs]}, ensure_ascii=False))
