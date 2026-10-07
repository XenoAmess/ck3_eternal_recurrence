"""Preserve selected original CI evidence as immutable archive members."""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
DBAF = BASE / 'r18-exact-head-ci-20261007-001'
DOCS = BASE / 'r18-docs-exact-head-ci-20261007-002'
TRANSPORT = BASE / 'r18-docs-exact-head-ci-20261007-001'
DBAF_HEAD = 'dbaf5f8db2067419838b814e278d962f428dc33c'
DOCS_HEAD = '3475ba2eac392221321c9c83e62f918fd3339db1'

if {path.name for path in ROOT.iterdir()} != {'preserve_evidence.py'}:
    raise RuntimeError('create-only evidence directory is not empty except for this authoring script')

selected = []

def add(base, relative, member, head, run_ids, role):
    selected.append({'source': base / relative, 'archive_member': member, 'exact_head': head, 'run_ids': run_ids, 'role': role})

for stem, run_ids in [
    ('actions-runs', [37556702028, 37556702039]),
    ('jobs-37556702028', [37556702028]),
    ('jobs-37556702039', [37556702039]),
    ('failed-logs-37556702039', [37556702039]),
]:
    for suffix in ['stdout', 'stderr', 'receipt.json']:
        name = stem + '.' + suffix
        add(DBAF, 'snapshot-001/' + name, 'dbaf-ci/' + name, DBAF_HEAD, run_ids, 'actual final API/jobs or failed-step original and receipt')
add(DBAF, 'REPORT.final.md', 'source-reports/dbaf-REPORT.final.md', DBAF_HEAD, [37556702028, 37556702039], 'original final CI report')
add(DBAF, 'candidate-001/FAILED.actual.json', 'candidate-001/FAILED.actual.json', DBAF_HEAD, [37556702039], 'retained failed candidate attempt; not CI failure')
for name in ['candidate.patch', 'MANIFEST.json', 'DOC-CHECK.actual.json', 'git-apply-check.stdout', 'git-apply-check.stderr', 'REPORT.md']:
    add(DBAF, 'candidate-002/' + name, 'candidate-002/' + name, DBAF_HEAD, [37556702039], 'exact four-document candidate; integrated by ROOT as docs HEAD ' + DOCS_HEAD)

for stem in ['actions-runs', 'jobs-37558948225']:
    for suffix in ['stdout', 'stderr', 'receipt.json']:
        name = stem + '.' + suffix
        add(DOCS, 'snapshot-002/' + name, 'docs-3475-ci/' + name, DOCS_HEAD, [37558948225], 'actual final API/jobs and receipt')
add(DOCS, 'REPORT.final.md', 'source-reports/3475-REPORT.final.md', DOCS_HEAD, [37558948225], 'original final follow-up CI report')
add(TRANSPORT, 'FAILED.transport.actual.json', 'transport-001/FAILED.transport.actual.json', DOCS_HEAD, [37558948225], 'original proxy transport failure; not CI failure')
for stem in ['actions-runs', 'jobs-37558948225']:
    for suffix in ['stdout', 'stderr', 'receipt.json']:
        name = stem + '.' + suffix
        add(TRANSPORT, 'snapshot-006/' + name, 'transport-001/' + name, DOCS_HEAD, [37558948225], 'original run GET and failed jobs GET bytes/receipt')

inventory = []
archive_path = ROOT / 'evidence.originals.zip'
with archive_path.open('xb') as archive_stream:
    with zipfile.ZipFile(archive_stream, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in selected:
            data = item['source'].read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(item['archive_member'], date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            inventory.append({
                'archive': archive_path.name,
                'archive_member': item['archive_member'],
                'source_path': str(item['source']),
                'bytes': len(data),
                'sha256_original_and_member': digest,
                'exact_head': item['exact_head'],
                'repository': 'XenoAmess/ck3_eternal_recurrence',
                'run_ids': item['run_ids'],
                'event': 'push',
                'ref': 'refs/heads/master',
                'run_attempt': 1,
                'role': item['role'],
            })

reports = ROOT / 'source-reports'
reports.mkdir(exist_ok=False)
for item in selected:
    if item['archive_member'].startswith('source-reports/'):
        data = item['source'].read_bytes()
        destination = ROOT / item['archive_member']
        with destination.open('xb') as stream:
            stream.write(data)

report = f'''# R0018：CI 文档修复与真实结果

本包只记录 GitHub Actions 的真实结果及四文档修复。来源仓库为 `XenoAmess/ck3_eternal_recurrence`；所有下列 run 都是自然 `push`、`refs/heads/master`、首次 `attempt 1`，没有 dispatch 或重跑。

| exact HEAD | 工作流 | 实际结论 | run |
| --- | --- | --- | --- |
| `{DBAF_HEAD}` | Li Yu Dao static checks | `completed/success` | [37556702028](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37556702028) |
| `{DBAF_HEAD}` | Official Runner CI | `completed/failure` | [37556702039](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37556702039) |
| `{DOCS_HEAD}` | Official Runner CI | `completed/success` | [37558948225](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37558948225) |
| `{DOCS_HEAD}` | Li Yu Dao static checks | `NOT_TRIGGERED`，不是 GREEN | 无 run；四份文档不匹配现有 workflow paths |

`dbaf` 的 Official Runner 在 step 43 `Enforce Python-only Windows automation` 失败：该步骤的九项测试先通过，随后四份文档中的旧禁用 shell 字面量触发四项违规。公共 CUnit step 16 已通过，之后未执行的静态与可复现构建检查不能补写为通过。原失败 run、正文和回执保持失败事实。

外置 candidate-002 只改四份文档的四个段落：三处未执行恢复脚本使用描述性名称；一处仍明确记载历史实际使用了禁止的 Windows shell 与 .NET，并保留原执行 provenance、完整 argv 原件和不二次 capture 的边界。未把历史 executor 改写为 Python，未修改校验规则或业务源码。补丁 SHA-256 为 `8a82f34f3d7d1e4772a8d19927a28c0b55465031f693effb33b1a3afdc25e56a`；此前已经完成的四文档校验及对冻结原文的应用检查结果随原件保存，本次归档没有重复检查。candidate-001 的字面量大小写匹配失败也保留原 FAILED 回执。

ROOT 在独立 worktree 采纳补丁，形成四文件四行文档提交 `{DOCS_HEAD}` 并推送；该提交的 Official Runner 首次运行在 `2026-10-07T01:58:03Z` 完成并成功，原失败的 Python-only 步骤亦通过。这个新的成功不改写 `dbaf` 的失败。

跟踪新提交期间，第一次本地读取的 jobs GET 因既有代理连接被远端关闭而中断。`transport-001` 保留原 stdout、stderr、receipt 和 FAILED 记录；这是读取故障，不是 CI RED。新外置 attempt 复用既有 exact commit identity，继续读取同一个 run，并取得最终成功。

**CI only；native/game 业务 `NOT_GREEN`。** 按 ROOT 本次交接，当前 R18 编译与 SDK profile 的冻结来源仍是 `{DBAF_HEAD}`，主执行树尚未快进到文档提交。此包不证明 native 构建或实机业务通过，也不填入 C3/I4 成功事实。

所有选定原件均以精确原字节保存在 [evidence.originals.zip](evidence.originals.zip) 的成员中；[INVENTORY.json](INVENTORY.json) 列出成员、原始路径、原 SHA-256、exact HEAD、run ID 和实际 ref。原 RED 日志及补丁包含需永久保全的旧字面量，所以使用二进制归档保存原件，避免重新作为项目操作正文进入文本校验；没有删改原件或放宽规则。两份来源最终报告另外原样复制在 `source-reports/`。完整外置 attempt 与原素材仍留在原路径，没有移动或清理。

本次只向 `C:/lci18w1/docs/li-yu-dao/acceptance/2026-10-07-r0018-ci-recovery/` create-only 写入此证据包。主执行树写入、commit/push、move/delete、新审计、重 check/tests、CI dispatch/rerun、native 编译、game、SDK 与 bus 操作均为零。
'''
with (ROOT / 'REPORT.md').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(report)

archive_data = archive_path.read_bytes()
package = {
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'archive': {'path': archive_path.name, 'bytes': len(archive_data), 'sha256': hashlib.sha256(archive_data).hexdigest(), 'members': len(inventory), 'format': 'deterministic ZIP; each member contains exact original bytes'},
    'sources': inventory,
    'runtime_frozen_head': DBAF_HEAD,
    'docs_fix_head': DOCS_HEAD,
    'actual_results': [
        {'head': DBAF_HEAD, 'run_id': 37556702028, 'workflow': 'Li Yu Dao static checks', 'status': 'completed', 'conclusion': 'success'},
        {'head': DBAF_HEAD, 'run_id': 37556702039, 'workflow': 'Official Runner CI', 'status': 'completed', 'conclusion': 'failure'},
        {'head': DOCS_HEAD, 'run_id': 37558948225, 'workflow': 'Official Runner CI', 'status': 'completed', 'conclusion': 'success'},
        {'head': DOCS_HEAD, 'run_id': None, 'workflow': 'Li Yu Dao static checks', 'status': 'NOT_TRIGGERED', 'conclusion': None},
    ],
    'native_game_business': 'NOT_GREEN',
    'C3_I4_business_success': 'not asserted by this CI package',
    'write_scope': str(ROOT),
    'main_execution_tree_writes': 0,
    'commit_push_move_delete': 0,
    'new_audits_rechecks_tests_CI_dispatch_rerun_native_game_SDK_bus': 0,
}
with (ROOT / 'INVENTORY.json').open('x', encoding='utf-8') as stream:
    json.dump(package, stream, indent=2, ensure_ascii=False)
    stream.write('\n')
print(json.dumps({'directory': str(ROOT), 'archive': package['archive'], 'report': str(ROOT / 'REPORT.md'), 'inventory': str(ROOT / 'INVENTORY.json'), 'main_execution_tree_writes': 0}, indent=2, ensure_ascii=False), flush=True)
