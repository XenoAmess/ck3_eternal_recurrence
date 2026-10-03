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

候选及完整报告保留在 `D:/ck3-superman-qiang-20261004/builder-L0-A0001/`。原 manifest、静态报告的精确字节以及已执行测试的会话输出转录，永久收录于 [完整构建证据](build-report-2026-10-04-L0-A0001.json) 和同名 `build-evidence-2026-10-04-L0-A0001/` 目录。单测文本是 stdout/stderr 合并回执的 UTF-8/LF 转录，明确标注采集方式；这次归档未重跑测试。

- manifest SHA-256：`0764b719983c53460d5927269a285154cd2a5ce2d0028352c501e571bd077198`。
- ZIP SHA-256：`24529fcec3ef55b72ce90a06f392bfebfe5d42143de71a241db3a9e363385df9`。

正式发布在最终实机决定及源码 commit/tag 完成后重新构建，保存另一份完整摘要，不覆盖本候选。

首次执行中发现构建 wrapper 导入同名根级 validator 的优先级问题及一项测试建目录问题；中英六技能显示改用 ScriptValue 时，七语言的旧保护标记也曾触发 RED。三项均在上述 GREEN 执行前修复，原失败执行回执保留在会话工具记录，完整构建证据逐项索引其实际退出码与失败原因；未把失败执行改称成功。

首轮 L0 没有用实际引擎预验 `open_kaishek` 语法 corpus；后续 acceptance 对已生成夹具的预检属于其独立 attempt，不能倒填为本轮已完成检查。未运行 CK3 的静态检查不能证明原版效果覆盖有效、技能即时读回、回滚或技能下限、计数极值、保存重载及玩家 UI。下一门槛是 [L1–L3 实机矩阵](test-plan.md)。

官方 Windows CI 的 [run 37147338623，第 27 步](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37147338623/job/111273893736#step:27:1) 实际在 `2026-10-03 19:19:15–19:19:20 UTC` 完成，结论 `success`，commit 为 `ebeb394634cc2a1e1ebd013b56c3e6952f4ce88e`。该步骤执行本产品 5 项发布测试、7 项静态测试、静态验证及双构建；此记录仅认证本产品步骤，不推定整个仓库 CI 或实机验收的结果。

后续实际查询也已确认两个完整 workflow 均 `completed / success`：[run 37147338623](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37147338623) 于 `2026-10-03 19:26:16 UTC` 回读，源码 commit 为 `ebeb394634cc2a1e1ebd013b56c3e6952f4ce88e`；[run 37147208568](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37147208568) 于 `19:26:20 UTC` 回读，源码 commit 为 `f643b32e6146dce73f77fedfefd8471da59fb04f`。查询 argv、准确起止时间及原始返回摘要保存在 [完整 CI 结论证据](build-report-ci-final-2026-10-04.json)，没有重跑测试。
