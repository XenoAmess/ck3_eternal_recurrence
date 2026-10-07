import hashlib, json, shutil
from pathlib import Path
from datetime import datetime, timezone
B = Path('C:/workspace/ck3_lyd_runtime_20261004')
M = Path('C:/workspace/ck3_eternal_recurrence')
out = M/'docs/li-yu-dao/acceptance/2026-10-07-r0024-prelaunch-configure-guard'
out.mkdir()
sources = {
    'FAILED-NATIVE-RESULT.json': B/'r24-native-build-20261007-001/RESULT.json',
    'FAILED-PRODUCER-RESULT.json': Path('C:/lr24b1/native-msvc-result.json'),
    'FAILED-CONFIGURE.log': Path('C:/lr24b1/msvc-configure.log'),
    'FAILED-ROOT-EXEC.json': B/'r24-root-build-original-exec-20261007-001/RESULT.actual.json',
    'CHECK-ARGV.json': B/'r24-root-cmake-guard-check-ARGV.actual.json',
    'CHECK-ROOT-EXEC.json': B/'r24-root-cmake-guard-check-original-exec-20261007-001/RESULT.actual.json',
    'CHECK-stdout.txt': B/'r24-root-cmake-guard-check-original-exec-20261007-001/stdout',
    'CHECK-stderr.txt': B/'r24-root-cmake-guard-check-original-exec-20261007-001/stderr',
    'CHECK-CONFIGURE.log': Path('C:/lr24cf1/msvc-configure.log'),
    'CHECK-PRODUCER-RESULT.json': Path('C:/lr24cf1/native-msvc-result.json'),
    'SOURCE.py': Path(__file__),
}
rows = []
for name, source in sources.items():
    raw = source.read_bytes()
    with (out/name).open('xb') as stream: stream.write(raw)
    rows.append({'original': source.resolve().as_posix(), 'archived': name,
        'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
(out/'INDEX.json').write_text(json.dumps({'copied_at_utc': datetime.now(timezone.utc).isoformat(),
    'files': rows, 'CK3_launches': 0, 'save_body_reads': 0, 'native_compilation_credit': False}, indent=2)+'\n', encoding='utf-8', newline='\n')
(out/'REPORT.md').write_text('''# 宗主续跑前的 CMake 配置修复

新 clean source `c2bd0c38da34b78187f47a82552007ec707e430a` 的 native 构建在 CMake 配置阶段失败，未编译 DLL，也未执行 focused tests。新增 crown-authority whole fixture 在 BUILD_TESTING/Windows 下无条件进入子目录，并要求 realm-law 私有开关开启；《礼与道》的实际十二项配置将该开关关闭，因此触发 FATAL_ERROR。本次属于构建入口故障，不是新的游戏实机结果。R24 尚未分配或启动。

最小修复只给父级 add_subdirectory 加上对应 `XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1` 条件。realm-law 开启时仍执行原测试目录及校验；关闭时不加入该专属测试。未改变生产业务字节或《礼与道》配置，没有为了消除错误启用无关能力。

一次实际 configure-only 验证以相同十二项私有开关、BUILD_TESTING=ON、realm-law=OFF 运行，原执行退出码0，配置成功。不把 configure-only 当编译、fixture运行或实机通过。原 configure失败、原producer误导性的configured/built启动标记及original wrapper1保留，能力状态依据实际process结果和actual_compilation_pass=false。

原始失败和验证 argv/stdio/producer/log 在 INDEX 逐字节绑定。下一步将修复提交推送后，导出新的 clean HEAD，在新 build 目录完成实际编译和 focused tests，再恢复真实withdraw存档。旧C:/lr24s1、C:/lr24b1、C:/lr24cf1及所有原过程保留。
''', encoding='utf-8', newline='\n')
stamp = datetime.now(timezone.utc).isoformat()
note = f'\n\n## 本机《礼与道》续跑构建故障修复（{stamp}）\n\n新c2bd clean native配置实际RED，新增Crown专属fixture无条件要求realm-law ON，与本LYD十二项OFF配置冲突；未编译/未focused/未分配或启动R24。最小父CMake开关条件修复后，同配置唯一configure-only原exec0，不授编译或live信用。[原始回执](../../li-yu-dao/acceptance/2026-10-07-r0024-prelaunch-configure-guard/REPORT.md)保留。c2bd Official/Linear exact CI成功仍只对应原HEAD；新修复提交后需新clean构建资格。下一步继续withdraw cold/合法新轮，整体NOT_GREEN/约75%不变，无Workshop。\n'
for name in ['docs/autonomous-agent-progress/daily/2026-10-07.md', 'docs/autonomous-agent-progress/weekly/2026-W41.md']:
    with (M/name).open('ab') as stream: stream.write(note.encode('utf-8'))
print(json.dumps({'report': out.as_posix(), 'files': len(rows), 'configure_only': True}))
