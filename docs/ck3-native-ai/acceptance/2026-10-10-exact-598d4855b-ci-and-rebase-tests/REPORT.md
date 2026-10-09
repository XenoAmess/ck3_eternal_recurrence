# 精确 598d4855b 官方 CI 与 rebase 回归证据（2026-10-10）

精确提交 `598d4855b1a5e7678fa2253e5664acb991c0c825` 的 Official Runner CI 与 Linear history 均已实际完成并成功。
Li Yu Dao static checks 为 **NOT_TRIGGERED**，不计为成功。

| 工作流 | 实际终态 | 原始运行 |
| --- | --- | --- |
| Official Runner CI | completed / success | [37988052013](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37988052013) |
| Linear history | completed / success | [37988052148](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37988052148) |
| Li Yu Dao static checks | NOT_TRIGGERED | 精确 HEAD 的真实 API 无对应 run |

官方共享 `Test shared CK3 acceptance without installed CK3` 步骤明确成功。
两份完整官方日志 ZIP、terminal jobs、FINAL、TERMINAL-EVIDENCE 及全部 50 组实际
API/query stdout、stderr、metadata 均保留原字节；查询中短暂失败的 jobs 回执也原样保留。
Official 日志 ZIP 为 119776 bytes，SHA-256
`ff2f14cf2f678ae9487c5fcdef336c0cf00c7eda4199f64e821725bd135b38e8`；
Linear 日志 ZIP 为 16390 bytes，SHA-256
`6b56ad13ff1290d07b1a27d5a3aaede10895e5f695c4a3c07dedd7fedae0d68f`。

Root rebase 后的五份本地实际命令回执另行保全，共 **54 项 PASS**：

| 原目录 | 测试集 | 实际结果 |
| --- | --- | --- |
| rebase-check-001 | adapters | 9 / 9 |
| rebase-check-002 | bootstrap | 10 / 10 |
| rebase-check-003 | entry | 15 / 15 |
| rebase-check-004 | operator quit | 16 / 16 |
| rebase-check-005 | normal close | 4 / 4 |

五份原始 RESULT 的退出码均为 0，stdout/stderr pins 与原件相同，unittest 原日志的数量及 OK
均已核对；命令与 UTC 时间见 [RESULT.actual.json](RESULT.actual.json)。原本地回执没有
HEAD/source pins，本包保留该原始边界，不补造精确源码绑定；精确 SHA 的通过结论来自上述官方 CI。

封存 [raw-evidence.zip](raw-evidence.zip)：279014 bytes，SHA-256
`dda4acc17a83784ca9b8e62b43295ff94961252e1caa76aaa0e56899f94e3c81`。全部 190 项原件的源路径、大小与 SHA 见
[INDEX.json](INDEX.json)，[ARCHIVE-VALIDATION.actual.json](ARCHIVE-VALIDATION.actual.json)
记录 ZIP CRC 与逐项 byte-exact 读回。生产脚本在 ZIP 的 `package-producer/produce-package.py`；
它只读取既有回执，不调用测试、GitHub API 或仓库写入。

旧 `00b88fc4d` 官方失败与修复前复现继续保留于
[公共 allocator CI 夹具修复](../../2026-10-10-common-allocator-ci-fixture.md)，本记录是另一精确来源的成功结果。
本次只是既有证据封存，没有重跑测试/CI，没有修改冻结 checkout；CI 成功与静态回归不授予
共享 runtime 资格、R40 实机通过或产品业务 GREEN。
