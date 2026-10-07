# R0018：CI 文档修复与真实结果

本包只记录 GitHub Actions 的真实结果及四文档修复。来源仓库为 `XenoAmess/ck3_eternal_recurrence`；所有下列 run 都是自然 `push`、`refs/heads/master`、首次 `attempt 1`，没有 dispatch 或重跑。

| exact HEAD | 工作流 | 实际结论 | run |
| --- | --- | --- | --- |
| `dbaf5f8db2067419838b814e278d962f428dc33c` | Li Yu Dao static checks | `completed/success` | [37556702028](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37556702028) |
| `dbaf5f8db2067419838b814e278d962f428dc33c` | Official Runner CI | `completed/failure` | [37556702039](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37556702039) |
| `3475ba2eac392221321c9c83e62f918fd3339db1` | Official Runner CI | `completed/success` | [37558948225](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37558948225) |
| `3475ba2eac392221321c9c83e62f918fd3339db1` | Li Yu Dao static checks | `NOT_TRIGGERED`，不是 GREEN | 无 run；四份文档不匹配现有 workflow paths |

`dbaf` 的 Official Runner 在 step 43 `Enforce Python-only Windows automation` 失败：该步骤的九项测试先通过，随后四份文档中的旧禁用 shell 字面量触发四项违规。公共 CUnit step 16 已通过，之后未执行的静态与可复现构建检查不能补写为通过。原失败 run、正文和回执保持失败事实。

外置 candidate-002 只改四份文档的四个段落：三处未执行恢复脚本使用描述性名称；一处仍明确记载历史实际使用了禁止的 Windows shell 与 .NET，并保留原执行 provenance、完整 argv 原件和不二次 capture 的边界。未把历史 executor 改写为 Python，未修改校验规则或业务源码。补丁 SHA-256 为 `8a82f34f3d7d1e4772a8d19927a28c0b55465031f693effb33b1a3afdc25e56a`；此前已经完成的四文档校验及对冻结原文的应用检查结果随原件保存，本次归档没有重复检查。candidate-001 的字面量大小写匹配失败也保留原 FAILED 回执。

ROOT 在独立 worktree 采纳补丁，形成四文件四行文档提交 `3475ba2eac392221321c9c83e62f918fd3339db1` 并推送；该提交的 Official Runner 首次运行在 `2026-10-07T01:58:03Z` 完成并成功，原失败的 Python-only 步骤亦通过。这个新的成功不改写 `dbaf` 的失败。

跟踪新提交期间，第一次本地读取的 jobs GET 因既有代理连接被远端关闭而中断。`transport-001` 保留原 stdout、stderr、receipt 和 FAILED 记录；这是读取故障，不是 CI RED。新外置 attempt 复用既有 exact commit identity，继续读取同一个 run，并取得最终成功。

**CI only；native/game 业务 `NOT_GREEN`。** 按 ROOT 本次交接，当前 R18 编译与 SDK profile 的冻结来源仍是 `dbaf5f8db2067419838b814e278d962f428dc33c`，主执行树尚未快进到文档提交。此包不证明 native 构建或实机业务通过，也不填入 C3/I4 成功事实。

所有选定原件均以精确原字节保存在 [evidence.originals.zip](evidence.originals.zip) 的成员中；[INVENTORY.json](INVENTORY.json) 列出成员、原始路径、原 SHA-256、exact HEAD、run ID 和实际 ref。原 RED 日志及补丁包含需永久保全的旧字面量，所以使用二进制归档保存原件，避免重新作为项目操作正文进入文本校验；没有删改原件或放宽规则。两份来源最终报告另外原样复制在 `source-reports/`。完整外置 attempt 与原素材仍留在原路径，没有移动或清理。

本次只向 `C:/lci18w1/docs/li-yu-dao/acceptance/2026-10-07-r0018-ci-recovery/` create-only 写入此证据包。主执行树写入、commit/push、move/delete、新审计、重 check/tests、CI dispatch/rerun、native 编译、game、SDK 与 bus 操作均为零。
