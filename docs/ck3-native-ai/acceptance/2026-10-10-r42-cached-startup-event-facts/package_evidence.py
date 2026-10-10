"""Preserve the completed file-only R42 cached facts as a small new archive."""
from pathlib import Path
import hashlib
import json
import zipfile

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
SOURCE = BASE / 'r42-seed-marker-event-cached-readonly-20261010-001'
OUT = BASE / 'r42-cached-startup-event-permanent-archive-20261010-001'
KEY = '2026-10-10-r42-cached-startup-event-facts'
CANDIDATE = OUT / 'candidate'
REL = Path('docs/ck3-native-ai/acceptance') / KEY
ACCEPTANCE = CANDIDATE / REL

def sha(body):
    return hashlib.sha256(body).hexdigest()

def ref(path, body=None):
    body = path.read_bytes() if body is None else body
    return {'path': str(path), 'bytes': len(body), 'sha256': sha(body)}

def write_new(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(body)

def json_new(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

if CANDIDATE.exists():
    raise ValueError('Candidate already exists')
original_index = SOURCE / 'INDEX.json'
if sha(original_index.read_bytes()) != 'd1f97d0f8136f861eccf61f3f3d94d84df1027898f1b3a7f03526b745560ad05':
    raise ValueError('Sealed source INDEX differs')
selected = [
    ('original/INDEX.json', original_index),
    ('original/SUMMARY.actual.json', SOURCE / 'SUMMARY.actual.json'),
    ('original/REPORT.zh.md', SOURCE / 'REPORT.zh.md'),
    ('cached-fragments/CACHED-ACTOR-MARKER-VERIFIED.actual.json', SOURCE / 'CACHED-ACTOR-MARKER-VERIFIED.actual.json'),
    ('source-cuts/SOURCE-RELATIONSHIP-CUTS.actual.json', SOURCE / 'SOURCE-RELATIONSHIP-CUTS.actual.json'),
    ('index-lookup/EVENT-QUEUE-INDEX-LOOKUP.actual.json', OUT / 'EVENT-QUEUE-INDEX-LOOKUP.actual.json'),
]
for path in sorted((SOURCE / 'source-inputs').iterdir()):
    if path.is_file():
        selected.append(('source-inputs/' + path.name, path))
for name in ('r42_cached_marker_event_inquiry_20261010.py', 'r42_inspect_cached_paths_20261010.py', 'r42_extract_cached_marker_event_20261010.py', 'r42_inspect_cached_actor_and_handler_20261010.py', 'r42_verify_cached_marker_relationship_20261010.py', 'r42_seal_cached_marker_event_report_20261010.py', 'r42_read_archive_rules_and_indices_20261010.py'):
    selected.append(('authors/' + name, BASE / name))
for run, name in (('034','0014-r34-D2a-stage-window-001'), ('038','0004-r38-D2a-window-001')):
    for suffix in ('.sdk-result.json', '.native-01.json'):
        path = BASE / ('live-attempt-' + run) / 'diagnostic-mcp-client-001' / (name + suffix)
        selected.append(('sdk-event-receipts/R' + run + '/' + path.name, path))
selected.append(('authors/package_evidence.py', Path(__file__)))

ACCEPTANCE.mkdir(parents=True, exist_ok=False)
zip_path = ACCEPTANCE / 'RAW-EVIDENCE.zip'
members = []
source_bytes = {}
with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, path in selected:
        if name in source_bytes:
            raise ValueError('Duplicate member')
        body = path.read_bytes()
        source_bytes[name] = body
        info = zipfile.ZipInfo(name, date_time=(2026,10,10,0,0,0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, body)
        members.append({'member': name, 'source': ref(path, body), 'bytes': len(body), 'sha256': sha(body)})

# One archival verification: member set, CRC, exact original bytes and SHA.
with zipfile.ZipFile(zip_path) as archive:
    if archive.testzip() is not None or archive.namelist() != list(source_bytes):
        raise ValueError('Archive member/CRC check failed')
    for row in members:
        body = archive.read(row['member'])
        if body != source_bytes[row['member']] or sha(body) != row['sha256']:
            raise ValueError('Archive member changed')
validation = {'schema':'lyd.r42.cached-startup-facts.archive-validation.v1','ok':True,'layer':'archive bytes only, not tests or CK3 qualification','member_count':len(members),'member_set_crc_exact_bytes_sha_verified':True,'raw_archive':ref(zip_path),'source_index':ref(original_index),'save_body_reads':0,'new_SDK_game_or_native_actions':0,'new_tests':[],'open_kaishek':'not-applicable: completed cached JSON/source/receipt archival; no new CK3 semantic execution'}
json_new(ACCEPTANCE / 'VALIDATION.actual.json', validation)
index = {'schema':'lyd.r42.cached-startup-event-facts.archive-index.v1','archive_relative_path':'RAW-EVIDENCE.zip','raw_archive':ref(zip_path),'original_source_index':ref(original_index),'members':members,'subset_boundary':'Selected evidence from original INDEX; unselected original artifacts and the three 1.54MB cache packets remain external with existing pins. No .ck3 save or native binary is included.','event_queue_index_lookup':'index-lookup/EVENT-QUEUE-INDEX-LOOKUP.actual.json','actual_business_credit':None,'startup_root_cause':'UNKNOWN'}
json_new(ACCEPTANCE / 'INDEX.json', index)
write_new(ACCEPTANCE / '.gitattributes', b'* -text\n')
write_new(ACCEPTANCE / 'package_evidence.py', Path(__file__).read_bytes())
readme = '''# R42 cached startup event facts: compact raw evidence

`RAW-EVIDENCE.zip` preserves the original report/INDEX/SUMMARY, authors, exact cached actor variable AST fragments, pinned case/handler source and two historical SDK/native event pairs. Each member preserves original bytes and source SHA. Original INDEX references intentionally remain original external paths; this archive INDEX enumerates the selected permanent members separately.

The complete 1.54 MB cache packets, seed/save bodies, native binaries and prior full archives are not repeated. Three actor variable fragments preserve the complete raw variable nodes, source packet and save pins; they are observations from existing JSON, not a new save parse or checkpoint qualification.

Only the four named existing indexes were checked for an event-manager/saved-queue projection reference. None identified such a projection; no exhaustive filesystem absence claim is made. No SDK/game query, save read, test or runtime action occurred.
'''
write_new(ACCEPTANCE / 'README.md', readme.encode('utf-8'))
doc = '''# R42：已缓存启动事件是 `.20`，completed marker 属于后继 `.2`

既有 R34 D2a、D2b 和 R38 selection 后的 JSON 都保存 actor31254 完整 `alive_data.variables` AST，三份各103个变量。`lyd_factory_diag_empty_transaction_completed` 在这三个原始变量节点及完整缓存包中均不存在。此次只读已有 JSON，没有重新读取91MB存档正文；完整缓存包和 seed 继续外置，只保存变量精确片段及其来源 pin。

R34 D2a 的原 SDK/native event 回执和 R38 重新载入后的原回执均确认 namespace `lyd_factory_diag`、definition `.20`、instance121、root31254、date53144712，native option0 显示且可用。两轮 calculatedEventId/运行目录序号不同，不用它们替代 definition/instance 身份。Source03 的 C4 prepared 合同准确等待 `.20`，并绑定同一 D2a seed：91,711,686字节，SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。

旧 R38 与当前 overlay 的 `.20` 源块（事件文件52–77行）逐字相同。它的 event/option guard 只含 stage20 与 unheld-title，不检查 completed marker。选择该 option 后，73行才调用 D2 effect；当前 effect121行写 marker、123行触发后继 `.2`，`.2` 的87/94行才读取 marker。这一阶段关系不支持把 seed 中 marker 缺失当作启动故障或据此修改夹具。

Source03 host 在稳定 native owner/map frame 和 campaign-root 查询之后，820行才调用 saved-startup admission。产品 `admit_saved_startup_event`（195–201行）只核 `.20` 身份，返回 `business_pass=false`，不选择选项、不检查 marker。handler24389字节、SHA-256 `f2fbbfc3c78d7cfe7d45b5c2d0afd0337dd9ebd834f7c81ce46c672dfff49964`；依赖 case JSON3257字节、SHA-256 `fd3ebf58bd01cb2998a47c5f9faa0225d478692134b2185510074b3c0cba0955`。R42 的未注入加载超时尚未进入这个 typed handler；实际失败见[独立 R42 RED 报告](2026-10-10-r42-shared-runtime-startup-red.md)。

全局保存事件队列不在这三份角色/title缓存内。只查本轮、R41加载诊断、R42 RED及 saved-startup admission 四个既有 INDEX，其元数据没有标识 event-manager/saved-queue 离线投影；这不是对全盘文件的不存在声明。加载停在 powerful vassals 的原因仍 UNKNOWN，未以 marker 缺失归因，未更改夹具或安排新启动。若继续选择保存事件恢复方向，须另行明确一次有界队列投影的输入与范围，本包没有执行它。

永久证据：[INDEX.json](acceptance/2026-10-10-r42-cached-startup-event-facts/INDEX.json)、[VALIDATION.actual.json](acceptance/2026-10-10-r42-cached-startup-event-facts/VALIDATION.actual.json)、[RAW-EVIDENCE.zip](acceptance/2026-10-10-r42-cached-startup-event-facts/RAW-EVIDENCE.zip)及[归档生产器](acceptance/2026-10-10-r42-cached-startup-event-facts/package_evidence.py)。ZIP原件 bytes/SHA、成员集合与CRC核验一次通过。原外置 INDEX/SUMMARY/报告均原样保存，历史 R42 RED不改。此次无新测试、SDK查询、游戏操作、存档正文读取或原生扫描；不授启动成功、C3或产品业务信用。`open_kaishek` 为 not-applicable：仅归档已有JSON、源码片段与原收据，没有新增 CK3 语义执行。
'''
write_new(CANDIDATE / 'docs/ck3-native-ai' / (KEY + '.md'), doc.encode('utf-8'))
files = [{'relative_path':p.relative_to(CANDIDATE).as_posix(),'source':ref(p)} for p in sorted(CANDIDATE.rglob('*')) if p.is_file()]
result = {'schema':'lyd.r42.cached-startup-facts.archive-candidate.v1','expected_parent_head':'6baf0b73ecad9bcf9940144093293b6a1d80de4d','candidate_root':str(CANDIDATE),'owned_paths':['docs/ck3-native-ai/' + KEY + '.md',REL.as_posix()],'files':files,'validation':validation,'main_applied':False}
json_new(OUT / 'RESULT.actual.json', result)
print(json.dumps({'result':ref(OUT / 'RESULT.actual.json'),'archive':ref(zip_path),'members':len(members),'candidate_files':len(files),'archive_validation':True},ensure_ascii=False,indent=2))
