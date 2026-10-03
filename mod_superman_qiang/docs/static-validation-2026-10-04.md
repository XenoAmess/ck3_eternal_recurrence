# 首轮 L0 验证结果

2026-10-04，解释器 `tools/.venv/Scripts/python.exe`，Python 3.14.7。执行包 `builder-L0-A0001`，源身份 `d5c411fe8f889ec36d8c88525628feffaf0a3e86` 加本次新产品尚未提交的精确源文件，摘要详见外置报告。候选没有正式 tag，不称为最终 release。

| 实际检查 | 结果 |
| --- | --- |
| 共享原创构建器回归 | 10 tests PASS，原创 upstream ID 可为 None，既有维护产品规则保持。 |
| 产品发布边界测试 | 5 tests PASS。 |
| 产品静态负例测试 | 7 tests PASS。 |
| 生成器一致性 | 12 个生成运行文件逐字节一致。 |
| 本地化格式 | 实际九语言每语 10 keys；BOM/header/解析/key 集合/保护 token PASS。非中文仅 format-certified。 |
| 正式包隔离 | allowlist 精确 21 文件；docs/tools/夹具排除，内层 descriptor 无 remote_file_id。 |
| 双构建 | manifest 和 ZIP 字节相同，候选 staging 再次 verify 21 文件 PASS。 |
| 封面 | 从源图重建一致，640×640 PNG，778,046 字节。 |

实际命令：

```text
tools\.venv\Scripts\python.exe tools\test_independent_mod_release.py
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\test_build_release.py
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\test_runtime.py
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\validate_static.py --report D:/ck3-superman-qiang-20261004/builder-L0-A0001/static-validation.json
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\build_release.py --check
```

候选及完整报告保留在 `D:/ck3-superman-qiang-20261004/builder-L0-A0001/`。manifest SHA-256 `0764b719`、ZIP SHA-256 `24529fce` 是本条便于识别的摘要前缀，不替代报告里的完整摘要。正式发布使用 clean commit/tag 重新构建并冻结完整摘要。

首次执行中发现构建 wrapper 导入同名根级 validator 的优先级问题及一项测试建目录问题，均已修复；旧 RED attempt 保留，修复后的新 attempt 通过。未运行 CK3 的静态检查不能证明原版效果覆盖有效、技能即时读回、计数极值、保存重载或玩家 UI。下一门槛是 [L1–L3 实机矩阵](test-plan.md)。
