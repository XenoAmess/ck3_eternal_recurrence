# Source16/17 冗余源码回收

按[统一时效与容量策略](../storage-retention-policy.md)，本轮解除已替代源码副本的运行用途保护。保留 Source18 作为同路径、同大小、同 SHA 的逐文件来源，后续 Source19 只从 Source18 派生；不再安排 Source16/17 旧 payload 的重放。

2026-10-11T13:47:50Z 至 13:52:23Z，18 批原命令全部实际成功，删除 `C:/csr16`、`C:/csr17` 中 17,492 个 non-host 文件，共 295,101,828 字节（约 281 MiB）。这是逻辑删除量，不能直接等同于磁盘物理可用空间增加。每个目标由原 held-handle 执行器在删除前核对 donor 与 target 的精确 SHA；删除、关闭句柄及原路径消失分别有逐文件回执，单批最多 1,000 文件。未递归删除目录，也未重放旧删除或旧信用。

两个独有旧 host 共 551,583 字节继续保留。Common 元数据、Git 来源、旧 indices、现用 Source18、Cbr3/native057、全部图形缓存、R54 seed、原始 0240 及其他 SAVE 均保留。旧来源保护与期限作为历史记录保留，本轮不续期。

独立准入为 cleanup 40 MiB，加 ROOT 交付、MAIN/Git 增量的固定 8 MiB；初始小输入另有原 128 KiB 保守上界。Git 后台维护新增 pack 与索引后，ROOT 的保守增量略超 8 MiB；从原 cleanup 未用余量中另保留 4 MiB，将 ROOT 上界设为 12 MiB、关闭输出上界从 1 MiB 增至 5 MiB。原合计 48 MiB 准入不变，这 4 MiB 不计为回收收益。全部交付 writer 停止后，原关闭命令实际返回 0，18 批的单一 credit event 只消费一次，future reservation 归零；固定上界不因未用完而退款。具体 carry 和 retained 数字以[实际关闭原件](acceptance/2026-10-11-source16-17-retirement/CLOSED-RESERVATION.actual.json)为准。

原件：[准入](acceptance/2026-10-11-source16-17-retirement/ADMISSION.actual.json)、[计划](acceptance/2026-10-11-source16-17-retirement/PLAN.actual.json)、[执行聚合](acceptance/2026-10-11-source16-17-retirement/AGGREGATE.actual.json)、[单一信用事件](acceptance/2026-10-11-source16-17-retirement/CREDIT-EVENT.actual.json)、[关闭命令](acceptance/2026-10-11-source16-17-retirement/close-RESULT.actual.json)、[逐项来源索引](acceptance/2026-10-11-source16-17-retirement/INDEX.actual.json)。完整逐文件 ledger 留在原独立外置批次根，不把大副本重新导入仓库。

共享日期等待与失败退出修复已经发布到 master；三个旧 AST 测试夹具依赖补修提交为 `e1ce87ebf22cef5e743cd73d7d431e27033647f8`，相关 8+12+3 项测试各一次通过。此精确提交的 Official CI（run `38144837218` / job `114485908623`）与 Linear（run `38144837223` / job `114485908459`）均实际 SUCCESS，attempt 1；原件见[封包](acceptance/2026-10-11-source16-17-retirement/e1ce-ci-INDEX.json)和[终态](acceptance/2026-10-11-source16-17-retirement/e1ce-ci-REPORT.terminal.json)。本次回收不增加 I4 业务信用，一期仍约 75%（估计）/ NOT_GREEN。
