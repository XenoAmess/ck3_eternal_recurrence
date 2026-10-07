import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
CANDIDATE = BASE / 'r18-decision-predispatch-fix-20261007-001'
MERGED = BASE / 'r19-root-focused-integration-20261007-001'
OUT = Path(__file__).resolve().parent
DOC = OUT.parents[1] / 'decision-selection-predispatch-refusal.md'
entries = {}

def original(path, expected=None, scope='saved source/focused evidence'):
    path = Path(path)
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected is not None and digest != expected:
        raise RuntimeError('Original evidence SHA mismatch: ' + str(path))
    key = path.as_posix()
    if key not in entries:
        entries[key] = {'source_path': key, 'member': path.relative_to(BASE).as_posix(),
                        'bytes': len(data), 'sha256': digest, 'scope': scope, 'data': data}
    return json.loads(data) if path.suffix == '.json' else None

index = original(CANDIDATE / 'INDEX.json')
manifest = original(index['integration_manifest']['path'], index['integration_manifest']['sha256'])
original(index['patch']['path'], index['patch']['sha256'])
original(CANDIDATE / 'ROOT-HANDOFF.md')
for key in ('preserved_failed_check', 'focused_checks'):
    ref = manifest[key]
    result = original(ref['path'], ref['sha256'], 'Original candidate focused check; failure preserved')
    for log_key in ('stdout.txt', 'stderr.txt'):
        log = result[log_key]
        original(log['path'], log['sha256'], 'Original focused stdout/stderr bytes')
for name in ('run_focused_checks.py', 'run_focused_checks002.py'):
    original(CANDIDATE / name, scope='Original focused runner source; archived without replay')
for name in ('patch-check.stdout.txt', 'patch-check.stderr.txt', 'reverse-check.stdout.txt', 'reverse-check.stderr.txt'):
    original(CANDIDATE / name, scope='Original source patch-check stdio; no repeated check')
merged = original(MERGED / 'actual-001/RESULT.actual.json',
                  '5e55e05aa2d5724c21c3bdb75d8c6bb0b4ef9fc3e80b61c9b01a20389ad0748f',
                  'ROOT actual merged source focused check at e53011d06984c3d1bf6192394014e9fc6f8436ae')
for key in ('stdout', 'stderr'):
    ref = merged[key]
    original(ref['path'], ref['sha256'], 'ROOT actual merged focused stdout/stderr bytes')
original(MERGED / 'run_focused.py', scope='ROOT original merged focused runner; archived without replay')

archive_path = OUT / 'SOURCE-FOCUSED.original-evidence.zip'
with archive_path.open('xb') as raw:
    with zipfile.ZipFile(raw, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in sorted(entries.values(), key=lambda value: value['member']):
            info = zipfile.ZipInfo(item['member'], date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, item['data'], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
archive_bytes = archive_path.read_bytes()
inventory = {
    'schema': 'lyd.decision-predispatch-source-focused-original-inventory.v1',
    'archived_at_utc': datetime.now(timezone.utc).isoformat(),
    'candidate_base_head': manifest['base_head'], 'merged_base_head': merged['base_head'],
    'merged_source_files_original_pins': merged['source_files'],
    'archive': {'path': archive_path.name, 'bytes': len(archive_bytes),
                'sha256': hashlib.sha256(archive_bytes).hexdigest(), 'members': len(entries)},
    'entries': [{key: value for key, value in item.items() if key != 'data'}
                for item in sorted(entries.values(), key=lambda value: value['member'])],
    'credit': {'source_applied_by_ROOT': True, 'candidate_focused_pass': 35,
               'merged_focused_pass': 37, 'native_compile': None, 'live': None,
               'old_SDK80_raw_ACK_recovered': False, 'business_GREEN': False},
    'archiver_actions': {'checks_replayed': 0, 'SDK_calls': 0, 'game_calls': 0,
                         'save_body_reads': 0, 'main_tree_writes': 0, 'commit_push': 0},
    'large_source_copy': False,
}
with (OUT / 'INVENTORY.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(inventory, stream, ensure_ascii=False, indent=2)
    stream.write('\n')

report = '''# 决议 Select 派发前拒绝：保全错误与后续显式请求

R18 冻结来源 `dbaf5f8db2067419838b814e278d962f428dc33c` 的 SDK80 在 native 派发前返回 `exact_alive_paused_decision_action_binding_changed`；随后 SDK84/88 被 Python 的 unresolved decision-action claim 锁拒绝，cleanup SAVE86 没有解除锁。这段真实记录及失败层次保留在 [R18 两轮原报告](../li-yu-dao/acceptance/2026-10-07-r0018-dbaf5f8db-rounds-lock-0304-002/PARTIAL-20261007-ROUNDS-LOCK-0304.md)。旧 producer 没有保留该次原 ERROR bytes，不能事后补造 raw ACK、rejection sidecar 或成功记录。

本次修复保留原 admission predicates 及短路顺序。拒绝 ERROR 增加固定 typed pre-dispatch 数据：实际 request ID/step/key、`before_main_thread_submit`、submitted/dispatch_invoked 为 false、首个实际求值失败的 predicate、expected/actual binding、原 current/previous snapshots，以及 26 个 Snapshot 顶层成员中的实际差异字段。没有再读取游戏或发布新 snapshot；未求值条件不写成失败。

Python 保留实际发送的解析后 request 和收到的解析后 ERROR，create-only 写入 `.claim.error.json`；原 `.claim.json` 不改写。只有匹配此固定 typed 派发前分支的证据才新增 `.claim.rejected-before-dispatch.json`，并与 claim 和 ERROR 的 SHA 绑定。这不是 verified success，不产生 `.verified.json`，也不自动重试。后续必须是新的显式 Select，请求的 public 与 native revision 都严格更高，且 PID/actor/date/generation/episode 相同；原 fresh decision model/frame guards 仍执行。Confirm、unknown/missing/foreign ERROR、timeout、after-submit failure、reconnect、相同 revision 或损坏证据继续锁定。

已应用到 canonical 源码的五个文件：

- [bridge.cpp](../../ck3_autonomous_player/native_bridge/src/bridge.cpp)
- [native_driver.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)
- [ingame_decision_outcome_contract.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_outcome_contract.py)
- [ingame_decision_predispatch_contract.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_predispatch_contract.py)
- [test_ingame_decision_predispatch_rejection.py](../../ck3_autonomous_player/tests/unit/test_ingame_decision_predispatch_rejection.py)

| 实际检查层次 | 原结果 |
| --- | --- |
| candidate focused attempt001，base dbaf | 35 项，0 failures、46 errors；Windows 长路径文件创建失败，原 FAILED 及完整 stdio 保留 |
| candidate focused attempt002 | 35 PASS；Select/primitive/实际 encoder 使用内存低层 transport，无 SDK/游戏调用 |
| ROOT merged actual001，base `e53011d06984c3d1bf6192394014e9fc6f8436ae` | 37 PASS、0 failures/errors；原 35 项加 native dispatch topology 2 项，记录于 `2026-10-07T03:23:58.042672Z` |

候选源 INDEX、manifest 和 40,905 B patch 分别固定原来源；patch SHA-256 为 `06d8e64e7f2c4fed8eddf6b006c62778788576d25ce550cfb31bd6a69c324323`。ROOT 在包含并发 remote 变化的 e530 基础上应用后执行了必要的一次 merged focused 检查，原 RESULT SHA-256 为 `5e55e05aa2d5724c21c3bdb75d8c6bb0b4ef9fc3e80b61c9b01a20389ad0748f`。candidate 和 merged 的五源文件 SHA 分层保留；尤其 merged bridge.cpp 的 SHA `67dcea4a2338108f73410695d67fc07f2a6a7ae050ecf00fbfb66967faed783f` 不冒用 candidate 的源 pin。

**当前信用仅为源码集成和 focused Python 检查。native compile 与 live 均为 NULL，整体业务不获 GREEN。** 必须使用含此修复的新版 binary，在新的合格 cold run 中取得实际派发前 typed ERROR 和后续显式 Select 结果，才能授予 live 信用。R18 已闭合的旧现场没有 hot reload，也不会补记 SDK80 原 ERROR 或改变历史锁结果。

永久小档见 [SOURCE-FOCUSED.original-evidence.zip](acceptance/2026-10-07-decision-selection-predispatch-refusal/SOURCE-FOCUSED.original-evidence.zip)，原字节 SHA、来源、失败/成功层次和 merged 五源 pins 见 [INVENTORY.json](acceptance/2026-10-07-decision-selection-predispatch-refusal/INVENTORY.json)。只保全 patch、源 manifest/INDEX、focused 原 RESULT/stdio 与原 runner；没有复制两份约 1.4 MB 的全文源码、存档正文或重读 R18 body。本报告代理未重跑 checks、CI/native、SDK/游戏，也未写主树或 commit/push。
'''
with DOC.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(report)
print(json.dumps({'report': DOC.as_posix(), 'inventory': (OUT / 'INVENTORY.json').as_posix(),
                  'archive': inventory['archive'], 'original_index_sha256': entries[(CANDIDATE / 'INDEX.json').as_posix()]['sha256']}, ensure_ascii=False))
