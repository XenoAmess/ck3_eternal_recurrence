from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004/r5-loading-crash-red-package-001')
OUT = BASE / 'permanent-projection-001'
EXPECTED_INDEX = 'ba4ef8a6b8d1aba9b8e703f299a3b8324d73a6988dc7766ff7a511556ca4cbb5'
EXPECTED_REPORT = '143db3dd145e8ba5a60dcf2d460aedfce324a11a296a4c25679e91db566b4fe5'

def digest(data):
    return sha256(data).hexdigest()

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)

def write_json(path, obj):
    write_new(path, (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

old_index_bytes = (BASE / 'index.json').read_bytes()
assert digest(old_index_bytes) == EXPECTED_INDEX
old_files = json.loads(old_index_bytes)['files']
old_files = [*old_files, {'path': 'index.json', 'bytes': len(old_index_bytes), 'sha256': EXPECTED_INDEX}]
assert len(old_files) == 234
assert sum(item['bytes'] for item in old_files) == 22721214
assert digest((BASE / 'REPORT.md').read_bytes()) == EXPECTED_REPORT
assert (OUT / 'REPORT.md').is_file()
assert not (OUT / 'index.json').exists(), 'Frozen projection cannot be overwritten'

selected_screens = {'screens/loading-first.png', 'screens/normal-exit-check.png', 'screens/crashed-exit-readback.png'}
excluded_run = {
    'run/ck3-stdout.txt': '完整4.77MB stdout不用于判定本次四条最终错误或退出；实际error、launch、stderr和独立退出回执保留，完整stdout原件仍在大包。',
    'run/screen-prelaunch-all-notices.stdout.json': '全历史5000条prelaunch通知集合不代表当前轮状态；保留本轮root review、prelaunch check、注册、FINAL/CAS与allocator回执，历史集合仍在大包。',
    'run/native-profile.template.json': '只有模板、没有当次native attach；不把模板投影为当前profile，完整模板仍在大包。',
}
renames = {'REPORT.md': 'outer-REPORT.raw.md', 'report.json': 'outer-report.raw.json', 'index.json': 'outer-index.raw.json'}

def policy(path):
    if path in renames:
        return renames[path], '原234件包报告与完整原索引的原字节副本，保留独立历史边界。'
    if path in excluded_run:
        return None, excluded_run[path]
    if path.startswith(('inputs/', 'ci/', 'crash/', 'offline/', 'lifecycle/', 'source/')):
        return path, '必要原输入、官方CI原件、崩溃小件、Steam新鲜度对照、生命周期或执行源码，逐字节保留。'
    if path.startswith('run/'):
        return path, '当次root review及实际run原回执／窗口元数据，逐字节保留。'
    if path.startswith('screens/'):
        if path in selected_screens:
            return path, '必要实际原图，保持完整原像素与编码。'
        return None, '同阶段或重复桌面原图省略；必要Steam位移双图、冷加载、大厅及崩溃后桌面原图保留，完整原图仍在大包。'
    if path.startswith('logs/pre-exit/'):
        if path in {'logs/pre-exit/report.json', 'logs/pre-exit/error.log'}:
            return path, '退出前error和原报告保留，绑定加载RED的实际时间与错误。'
        return None, '退出前非判别日志省略；其原报告与哈希保留，debug原字节已在crash小件中保留。'
    if path.startswith('logs/crash-observed/'):
        if path.endswith('/debug.log'):
            return None, '相同SHA的debug复本省略；完整原字节在crash/ck3_20261004_192419/logs/debug.log保留。'
        return path, '最终崩溃观察报告及实际最终日志原字节保留。'
    if path.startswith('logs/final-userdir/'):
        return None, '相同最终userdir日志复本省略；最终error在logs/crash-observed/logs/error.log、debug在crash原件保留，原SHA继续在完整索引。'
    if path in {'error-classification.json', 'full-external-index.json'}:
        return path, '完整源索引及实际错误分类原字节保留。'
    raise AssertionError('Unreviewed path: ' + path)

projection = []
for item in old_files:
    data = (BASE / item['path']).read_bytes()
    assert len(data) == item['bytes'] and digest(data) == item['sha256'], item['path']
    target, reason = policy(item['path'])
    row = {**item, 'retained': target is not None, 'projected_path': target, 'reason_zh': reason}
    projection.append(row)
    if target is not None:
        write_new(OUT / target, data)

assert not list(OUT.rglob('*.dmp'))
assert len([row for row in projection if row['path'].startswith('inputs/production/')]) == 59
assert len([row for row in projection if row['path'].startswith('inputs/fixture/')]) == 7
assert len([row for row in projection if row['path'].startswith('inputs/i2-fixture/')]) == 7
write_new(OUT / 'source/prepare_r5_small_projection.py', Path(__file__).read_bytes())
write_json(OUT / 'projection-map.json', {
    'schema': 'ck3.lyd.r0005-small-projection-map.v1',
    'source_package': str(BASE).replace('\\', '/'),
    'source_index_sha256': EXPECTED_INDEX,
    'source_files': 234,
    'source_bytes': 22721214,
    'originals_preserved': True,
    'files': projection,
})

# Recheck the existing immutable 234-file parent index, not recursive children added by this projection.
for item in old_files:
    data = (BASE / item['path']).read_bytes()
    assert len(data) == item['bytes'] and digest(data) == item['sha256'], item['path']
assert digest((BASE / 'index.json').read_bytes()) == EXPECTED_INDEX

report = {
    'schema': 'ck3.lyd.r0005-small-permanent-projection.v1',
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'NATIVE_LOADING_RED_AND_CRASH_OBSERVED',
    'normal_exit': False,
    'cause': 'NOT_PROVEN',
    'commit': '18b1944d1784d3e4ec57189c016335ef135b9b34',
    'product_tree': '77f74591f299874efcd20c2672f143c362e54caa',
    'execution_uuid': 'bf0a2e3a-f038-4fac-9ab1-f7b6d1ccba6d',
    'task_id': 'ck3-lyd-live-006-20261004',
    'immutable_parent': {'path': str(BASE).replace('\\', '/'), 'files': 234, 'bytes': 22721214, 'index_sha256': EXPECTED_INDEX, 'report_sha256': EXPECTED_REPORT, 'all_234_paths_verified_unchanged': True},
    'retained_originals': sum(row['retained'] for row in projection),
    'omitted_originals': sum(not row['retained'] for row in projection),
    'retained_original_bytes': sum(row['bytes'] for row in projection if row['retained']),
    'omitted_original_bytes': sum(row['bytes'] for row in projection if not row['retained']),
    'mounted_inputs': {'production': 59, 'entry_fixture': 7, 'i2_fixture': 7, 'expected_fixture_setup': '36->35+1', 'fixture_setup_actual': 'NOT_RUN'},
    'final_error_e_count': 4,
    'final_error_sha256': '3c6efe65ca5e46aa5604eebbc3a401cf8a4bfe9cfac9184d36ffa7bbdd5319d5',
    'ci': {'status': 'OFFICIAL_L0_SUCCESS', 'exact_head': '18b1944d1784d3e4ec57189c016335ef135b9b34', 'source': 'ci/FINAL-CI-RECEIPT.json', 'not_native_acceptance': True},
    'not_run': ['campaign', 'native_attach', 'current_native_profile', 'save', 'formal_I1', 'formal_I2', 'formal_I3', 'formal_I4', 'D+1', 'D+30', 'reload'],
    'coordinate_rejection': {'utc': '2026-10-04T11:27:32Z', 'proof_boundary': 'root tool output note only; no independent refusal receipt', 'input_executed': False, 'normal_exit_proven': False},
    'crash_originals': {'files': 7, 'bytes': 39858628, 'external_path': 'C:/workspace/ck3_lyd_runtime_20261004/live-attempt-005/userdir/crashes/ck3_20261004_192419', 'all_preserved': True, 'minidump_copied': False, 'minidump_bytes': 39386417},
    'projection_policy': {'target_max_bytes': 10000000, 'photos_original_bytes': True, 'no_raw_asset_deletion': True, 'no_game_screen_ci_network_or_tracked_mutation': True, 'source_full_index_preserved': True},
    'size_boundary': 'index lists every projection file except itself; package total is externally reported after index freeze',
}
write_json(OUT / 'report.json', report)
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': digest(data)})
write_json(OUT / 'index.json', {'schema': 'ck3.lyd.r0005-small-permanent-projection-index.v1', 'files': files, 'self_boundary': 'index excludes itself', 'source_index_sha256': EXPECTED_INDEX})
total = sum(item['bytes'] for item in files) + (OUT / 'index.json').stat().st_size
assert total <= 10000000, total
print(json.dumps({'path': str(OUT).replace('\\', '/'), 'files': len(files) + 1, 'bytes': total, 'retained_originals': report['retained_originals'], 'omitted_originals': report['omitted_originals'], 'index_sha256': digest((OUT / 'index.json').read_bytes()), 'report_sha256': digest((OUT / 'report.json').read_bytes()), 'parent_234_verified_unchanged': True}, ensure_ascii=False, indent=2))
