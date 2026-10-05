from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
CANDIDATE = BASE / 'r10-terminal-report-candidate-20261006-001'
OUT = BASE / 'r10-terminal-import-plan-correction-20261006-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    return json.loads(path.read_bytes().decode('utf-8-sig'))

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def dump_new(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    write_new(path, data)
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}

assert not OUT.exists()
OUT.mkdir()
plan_raw = (CANDIDATE / 'IMPORT-PLAN.json').read_bytes()
assert sha(plan_raw) == '9e3856d0653ae212145facc19b0f6151a3cccd2568669c4bf180909e1135f010'
plan = json.loads(plan_raw.decode('utf-8-sig'))
origins = load(CANDIDATE / 'ORIGIN-MAP.plan.json')
corrections = []
for row in plan['objects']:
    path = Path(row['source_absolute_path'])
    if path.is_file() and path.stat().st_size == row['original_bytes']:
        continue
    assert '/inputs/lyd-i3b-detached-authority-source-review-20261005-001/review-package-002/' in path.as_posix(), str(path)
    canonical = BASE / path.as_posix().split('/inputs/', 1)[1]
    data = canonical.read_bytes()
    assert (len(data), sha(data)) == (row['original_bytes'], row['original_sha256'])
    corrections.append({'declared_nested_source_path': str(path),
                        'declared_nested_source_absent': not path.is_file(),
                        'actual_canonical_source': str(canonical),
                        'bytes': len(data), 'sha256': sha(data),
                        'actual_source_exact_byte_SHA_verified': True})
    row['declared_borrowed_INDEX_source_path'] = str(path)
    row['source_absolute_path'] = str(canonical)
    row['actual_selected_source_origin'] = canonical.relative_to(BASE).as_posix()
    row['recovery_basis'] = 'Borrowed INDEX contains declared nested source paths with no body at those copies. Actual canonical source package bytes matched the exact sealed SHA; no replacement byte or history rewrite.'
assert len(corrections) == 12
for correction in corrections:
    origin = Path(correction['declared_nested_source_path']).relative_to(BASE).as_posix()
    match = next(row for row in origins['files'] if row['origin'] == origin)
    match['declared_source_path_exists_at_import_preflight'] = False
    match['actual_canonical_source'] = correction['actual_canonical_source']
    match['actual_canonical_bytes_SHA_verified'] = True
origins['status'] = 'ORIGINAL_BYTES_PINNED_WITH12_DECLARED_NESTED_PATHS_BOUND_TO_EXACT_CANONICAL_SOURCE'
origin_ref = dump_new(OUT / 'ORIGIN-MAP.plan.actual-source-correction.json', origins)
plan['supersedes_original_plan_SHA'] = sha(plan_raw)
plan['origin_map_override'] = origin_ref
plan['candidate_metadata_revision'] = 'Original candidate unchanged; append importer source-path correction only'
plan['source_path_corrections'] = corrections
plan_ref = dump_new(OUT / 'IMPORT-PLAN.v2.json', plan)
dump_new(OUT / 'CORRECTION.json', {'schema': 'lyd.r10.append-only-import-source-correction.v1',
    'at_utc': datetime.now(timezone.utc).isoformat(), 'candidate_unchanged_INDEX': 'b50384a6aaa3a6edb14ae41a48cabb103b7de53613f98ba0c8c2f8890617f429',
    'actual_first_check_plan_exit_code': 1, 'first_failed_check_was_stat_only': True,
    'reason': '12 borrowed input INDEX paths describe nested source copies without file bodies. Every corresponding actual canonical source was read once and exact SHA/bytes verified.',
    'corrections': corrections, 'new_plan': plan_ref,
    'old_SDK_raw_body_reads': 0, 'save_body_reads': 0,
    'old_package_or_candidate_rewrites': False, 'game_or_main_operations': False})
write_new(OUT / 'failed-importer-source-001.py', (BASE / 'import_r10_closed_report_root_only_20261006_001.py').read_bytes())
write_new(OUT / 'FAILED-CHECK-TOOL-TRANSCRIPT-EXCERPT.txt', (
    'Tool transcript excerpt, not a captured raw stdout file.\n'
    '2026-10-06 ROOT report import plan metadata/stat preflight:\n'
    'Executed import_r10_closed_report_root_only_20261006_001.py --check-plan.\n'
    'Actual tool exit_code=1. AssertionError reported 12 FileNotFoundError entries under\n'
    'r10-full-runtime-independent-review-20261005-001/review-package-002/evidence/lineage-002/inputs/lyd-i3b-detached-authority-source-review-20261005-001/review-package-002/.\n'
    'No main target was created, no raw SDK body was read, no game operation performed.\n'
    'Exact missing paths and verified canonical byte/SHA replacements are in CORRECTION.json.\n').encode('utf-8'))
write_new(OUT / 'NOTES-zh.md', ('''# R10导入源路径追加勘误

原candidate及IMPORT-PLAN001不改，第一次check-plan实际exit1原失败保留。12个borrowed INDEX的嵌套source路径没有file body；这只是INDEX所列路径，不能伪称这些nested copies存在。对应canonical原source包12件均真实读一次并匹配原sealed bytes／SHA，v2计划以实际canonical路径导入相同字节，ORIGIN-map保留原声明路径、absent事实及真实来源。未重扫SDK1–200或保存／AST／测试。

ROOT报告主线fetch+rebase后为3b4bbcadcbadf05474dadfc388dfabe3eb26af44；R10实际游戏源与验收始终绑定d0f8，不授新HEAD实机信用。旧CI neutral-docs候选的beforeSHA因remote更新已失效，不能wholefile overlay；ROOT须按新文件必要定位最小修改，通用CI尚未复验GREEN。此说明与原冻结结果分列。
''').encode('utf-8'))
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.import-source-correction-index.v1', 'files': files})
print(json.dumps({'path': str(OUT), 'correction_count': len(corrections),
    'plan_sha256': plan_ref['sha256'], 'origin_sha256': origin_ref['sha256'],
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=True))
