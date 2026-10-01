# CK3 1.20.0.2 草案分组专用 named-slot 单场景验证

状态：**static-ready named queue fixture**。中央确认
`permitted_executor_religion_draft_groups12002` install/runtime/copy/admission 字段 READY 后，
本包唯一必要 `/O2 /W4 /WX` 单场景首轮 GREEN：**1 case / 7 checks**；未声称 live。
原 [四场景 generic caller](religion_reform12002_group_mailbox_fixture.md) 已冻结，不重跑。

新 `religion_reform12002_group_named_test.cpp` 复用被冻结的 group memory / owner helpers，
只运行一个 `visible-multi-slots` backing。submit 前将 generic primary 清空，
由 actual group callback 的专用 named slot 准入，随后执行真正的
`TrySubmit → ownerDrain → Read/Finish → Wait/Reclaim → complete command_result`。

原 group CPP 已将内层 12-case main 重命名；runner 为它生成仅在 Z artifact 中的 exact helper copy，
只把外层 4-case main 改名为 `FrozenDraftGroups4CaseMainNotExecuted`。
两个旧 main 都不调用，旧源不修改。复用被冻结的 `/O2` 库对象，仅编译当前 shared mailbox/layout 代码及新 test。
实际完整输出与相同 native input 的已冻 generic caller 逐字节相同，协议 metadata 只来自实际 C++ 序列化器。

生产定义为 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1=1`；
`XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1` 只供离线 fixture stub，不能进入生产 DLL。
本场景只覆盖 runtime named admission，install-environment 的传播由中央接线另行负责。
没有 CK3、pipe、UI、Steam、战争研究或 Git 操作。

Artifact：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\query-group-named\attempt-001`。
`result.json` SHA-256：`92e07abffa70cd2e8d76bb822d04238ff38c3725c21ae341e0bee410a1c39663`。
实际 `wire/visible-multi-slots.json` 为 complete command_result；source/defines、冻结对象来源、
helper template/copy SHA 与字节比较结果均保留在 receipt。无 RED，无 `/Od` 或旧矩阵重跑。
