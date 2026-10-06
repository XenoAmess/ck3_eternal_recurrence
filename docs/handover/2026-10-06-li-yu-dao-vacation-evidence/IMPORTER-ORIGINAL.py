"""Preserve sealed drafts as inert documentation; never imports or applies them."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
REPO = Path('C:/workspace/ck3_eternal_recurrence')
OUT = REPO / 'docs/handover/2026-10-06-li-yu-dao-vacation-evidence'
OUT.mkdir(exist_ok=False)
(OUT / 'objects').mkdir()

PACKAGES = [
    ('i3b-sdk-checkpoint-qualification-adapter-20261006-001', '76a50872caf2cc062725cdaad1d4b73b1aa809a2909b4aea0d826f04e932864e'),
    ('i3b-sdk-checkpoint-seam-review-20261006-003', 'c9b9fc385b49418ef382a1dd7cfc30cb7f7240d6d661ae114bab15f771cda0f0'),
    ('i3b-r13-formal-route23-20261006-001', '8157e7916786cf9327a17b238fb54c7957a08a012252993995493077315360ff'),
    ('c3-native-challenger-graph-addon-20261006-001', '8bed0edb845567fdc1dbd7436337fea8a05ed4d844ee0596401bb73a2c9f52c1'),
    ('i3b-current-faith-challenger-sponsor-abi-contract-sourceonly-20261006-001', '3dffb1d4ee1fa0e100ea26b12f577841317ebdcae4d6e702282bad768ceadfb1'),
    ('readonly-revision-inline-sourceonly-20261006-001', '948d451bf44142d1236f58681291438eec00d15ed8b43d82ced8b032f617dfed'),
    ('i3b-is-imprisoned-abi-contract-20261006-001', 'da2d0e841d616d1f15860c5421b85bbd8f817cc936ae473b9e9bc6953da0c197'),
    ('lyd-r13-official-mcp-private23-template-20261006-001', '688f6ca863e4d701c9a233b468e5054979f628a7e6f7a3076dd06d4443c691e1'),
    ('r13-clean-source-metadata-routing-20261006-001', '3fb0ceb0f9428017d1c448b336ecda654e598b9b847992263424cdd0b612eadd'),
    ('r13-canonical-head-export-helper-20261006-001', '302ded75bf1c726a207e515631786087ed9e4aab64ee0aac91802c12f7615be3'),
    ('r13-clean-native-build-helper-20261006-002', '42071faa1e4095d2f140e2a8be65348ba7d2c6c47712e194dc2d5ab8911ba282'),
    ('r13-launch-profile-input-templates-20261006-001', '152de00ddc1fbb67e94df9e43e5340ca50a109c1de696166f6c925a10060c7f4'),
    ('r13-c3-private23-route-adaptation-20261006-001', '7235de1e8f8fc25f6b08d9e5c4beaa28ecf9bf682af10d3031c3ca403ba7d122'),
]

rows, objects, packages = [], {}, []
excluded_suffixes = {'.ck3', '.dll', '.exe', '.zip', '.tar', '.pdb', '.obj'}

def require(condition, message):
    if not condition: raise ValueError(message)

def preserve(path, package, expected_bytes=None, expected_sha=None):
    path = path.resolve()
    require(path.is_relative_to(BASE), 'source outside external runtime: ' + str(path))
    require(path.suffix.lower() not in excluded_suffixes, 'binary body must stay external: ' + str(path))
    require(path.stat().st_size <= 3_000_000, 'large body must stay external: ' + str(path))
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_bytes is not None: require(len(raw) == expected_bytes, 'byte mismatch: ' + str(path))
    if expected_sha is not None: require(digest == expected_sha.lower(), 'SHA mismatch: ' + str(path))
    if digest not in objects:
        encoded = gzip.compress(raw, compresslevel=9, mtime=0)
        target = OUT / 'objects' / (digest + '.bin.gz')
        target.write_bytes(encoded)
        require(gzip.decompress(target.read_bytes()) == raw, 'lossless mismatch')
        objects[digest] = {'path': target.relative_to(OUT).as_posix(),
                           'bytes': len(encoded), 'sha256': hashlib.sha256(encoded).hexdigest(),
                           'decoded_bytes': len(raw), 'decoded_sha256': digest}
    rows.append({'package': package, 'source_path': str(path), 'bytes': len(raw),
                 'sha256': digest, 'object': objects[digest]['path']})

for name, digest in PACKAGES:
    root = BASE / name
    index = root / 'INDEX.json'
    preserve(index, name, expected_sha=digest)
    data = json.loads(index.read_bytes())
    files = data.get('files')
    require(isinstance(files, list), 'unexpected package index: ' + name)
    for row in files:
        path = Path(row['path'])
        if not path.is_absolute(): path = root / path
        preserve(path, name, row['bytes'], row['sha256'])
    packages.append({'root': str(root), 'index_sha256': digest, 'indexed_payloads': len(files),
                     'installation': 'NOT_APPLIED_BY_THIS_ARCHIVE',
                     'new_head_runtime_acceptance': None})

# Existing large packages are referenced, not reimported or recompressed.
i4_root = BASE / 'i4-matrix-resume-review-20261005-001/pf8-frozen632-cold-inputs-016'
preserve(i4_root / 'INDEX.json', 'i4-reference-only', expected_sha='f3bf4bd225dd9bada1a1ea24e00e099266e62a8bbc97ad1468e2afabadcea4c6')
preserve(i4_root / 'REPORT-zh.md', 'i4-reference-only')

for name in [
    'r13-root-rebased-python-focused-tests-20261006-002',
    'r13-root-rebased-python-focused-tests-20261006-003',
    'r13-root-reader-line-ending-projection-20261006-001',
    'vacation-root-closeout-observation-20261006-001',
    'vacation-root-bus-observation-20261006-001',
]:
    for path in sorted((BASE / name).rglob('*')):
        if path.is_file(): preserve(path, name)

for name in ['root-r13-python-focused-argv-20261006-001.json',
             'root_vacation_collect_20261006_001.py',
             'root_vacation_archive_20261006_001.py',
             'root_r13_source_bus_poll_list_20261006_001.py']:
    preserve(BASE / name, 'root-closeout-tools')

document = {'schema': 'lyd.vacation.inert-source-preservation.v1',
    'at_utc': datetime.now(timezone.utc).isoformat(),
    'source_commit': 'ee752979e75029a86e972f9cdcc7a793dc6705dd',
    'purpose': 'handover only; source-only, draft and not-run statuses remain unchanged',
    'packages': packages, 'references': rows, 'objects': list(objects.values()),
    'original_reference_count': len(rows), 'unique_object_count': len(objects),
    'old_r11_r12_archives_recompressed': 0, 'old_game_save_body_reads': 0,
    'candidate_execution_or_installation': False, 'new_game_or_native_build': False}
raw = (json.dumps(document, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
(OUT / 'INDEX.json').write_bytes(raw)
(OUT / 'README.md').write_text(
    '# 度假交接证据\n\n'
    '本目录只保存未合入候选及收尾回执，不应用或执行任何候选。全部状态以原始报告为准。\n\n'
    'INDEX.json 逐件列出外置来源、原始字节数与 SHA-256、gzip 对象及解压后 SHA-256。'
    'objects/*.bin.gz 是惰性档案；解压还原到新的外置目录后，再根据目标包 EXPORT/APPLY-MANIFEST 做增量集成。'
    '绝不可把压缩对象或过时的共享文件副本直接放入生产目录。\n\n'
    'R11/R12 和已整合 L0 的旧档案不重压缩；大存档与 DLL/EXE、原始构建目录继续留在外置 runtime。'
    'I4 只保留索引与报告，原 016 payload 仍在外置目录。\n', encoding='utf-8', newline='\n')
print(json.dumps({'output': str(OUT), 'index_bytes': len(raw),
                  'index_sha256': hashlib.sha256(raw).hexdigest(),
                  'references': len(rows), 'objects': len(objects),
                  'compressed_bytes': sum(x['bytes'] for x in objects.values())}))
