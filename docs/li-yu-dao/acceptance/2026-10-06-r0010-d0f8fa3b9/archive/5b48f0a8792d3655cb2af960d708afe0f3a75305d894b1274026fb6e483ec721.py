import hashlib
import json
from pathlib import Path
import shutil
root = Path(__file__).resolve().parent
out = Path('C:/workspace/ck3_lyd_runtime_20261004/r10-actual-release-build-20261005-001')
build = Path('C:/lydr10-release-20261005-001')
def fact(path):
    raw = path.read_bytes(); return {'path': path.resolve().as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
result_path = out / 'RESULT.json'
result = json.loads(result_path.read_bytes())
assert result['status'] == 'ACTUAL_RELEASE_BUILD_RED' and result['exit_code'] == 1
assert result['actual_compilation_pass'] is True
assert result['source_revision'] == 'd0f8fa3b9d444828759443aa018bfd7ad31b398d'
assert result['native_tree'] == '789eab5ae1c3015fe210de508fdd730a13bbb8db'
assert result['source_before'] == result['source_after'] and result['source_after']['status'] == ''
assert result['exported_source_exact_before_after'] is True
inner = json.loads(Path(result['native_msvc_result']['path']).read_bytes())
assert inner['status'] == 'built_defender_registration_failed' and inner['build_succeeded'] is True
assert inner['defender_exclusions']['status'] == 'settings_failed'
for reference in [*result['targets'].values(), result['native_msvc_result'], result['actual_cmake_cache'], *result['actual_Defender_receipt_refs'].values(), result['stdout'], result['stderr'], result['Defender_actual_before'], result['Defender_actual_after']]:
    assert fact(Path(reference['path'])) == reference
receipt = json.loads(Path(result['actual_Defender_receipt_refs']['receipt']['path']).read_bytes())
sources = [root / 'build_exact_release.py', root / 'defender_read_only_probe.py', root / 'execute_authorized_once.py', root / 'AUTHORIZED-ONCE-INVOCATION.json', Path(__file__), build / 'native-msvc-result.json', build / 'CMakeCache.txt', build / 'msvc-build.log', build / 'msvc-configure.log', build / 'build.ninja', Path(result['actual_Defender_receipt_refs']['manifest']['path']), Path(result['actual_Defender_receipt_refs']['receipt']['path'])]
for path in sources:
    target = out / 'evidence' / path.name
    target.parent.mkdir(exist_ok=True)
    assert not target.exists()
    shutil.copyfile(path, target)
    assert fact(path)['sha256'] == fact(target)['sha256']
summary = {'status': 'ACTUAL_COMPILATION_PASS_DEFENDER_SETTINGS_FAILED_NATIVE_NOT_RUN',
           'RESULT': fact(result_path), 'source_revision': result['source_revision'], 'native_tree': result['native_tree'],
           'targets': result['targets'], 'inner_native_msvc_receipt': result['native_msvc_result'],
           'Defender_manifest': result['actual_Defender_receipt_refs']['manifest'],
           'Defender_receipt': result['actual_Defender_receipt_refs']['receipt'],
           'Defender_error_stage': receipt.get('error_stage'), 'Defender_calls': receipt.get('calls'),
           'actual_returncode': 1, 'compilation_pass': True, 'settings_effectiveness': False,
           'game_calls': 0, 'native_pipe_calls': 0, 'build_retries': 0}
(out / 'SUMMARY.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode())
md = '''R10 实际 Release 编译与链接通过，唯一一次构建使用64jobs、指定8个开关，源码前后精确绑定 d0f8fa3 / native tree789eab5。新 DLL 与注入器已保存；未启动游戏或进行注入。

当前 canonical helper 实际读取 Git-local opt-in 并执行新输出登记。Defender WMI 读取失败，原 helper 返回1，整体 RESULT 保持 ACTUAL_RELEASE_BUILD_RED；actual_compilation_pass=true 独立保留。设置未生效，未启用服务、安装任务或重试。冷载消费者必须按已审的编译/设置分离合同核验原 RED 回执及新产物，不改写为整体 PASS。
'''
(out / 'REPORT-zh.md').write_bytes(md.encode())
files = []
for path in sorted(out.rglob('*')):
    if path.is_file():
        value = fact(path); value['path'] = path.relative_to(out).as_posix(); files.append(value)
(out / 'INDEX.json').write_bytes((json.dumps({'schema': 'lyd.r10.actual-release-build-index.v1', 'status': summary['status'], 'files': files, 'external_targets_verified': result['targets']}, indent=2) + '\n').encode())
for row in files: assert fact(out / row['path'])['sha256'] == row['sha256']
print(json.dumps({'summary': summary, 'INDEX': fact(out / 'INDEX.json'), 'payload_count': len(files)}, indent=2))
