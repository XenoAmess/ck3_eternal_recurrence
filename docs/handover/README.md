# CK3 项目当前交接

更新于 **2026-11-28 01:11（北京时间）**。实机观察仅适用于机器 `xenoamess-full-tower-eb9d2c1186`。长期规则见[项目指引](../../AGENTS.md)、[自动游玩手册](../maintenance/autoplayer-workflow.md)和[实机与机器授权](../maintenance/ck3-operating-authority.md)。

## 自动游玩现状

- **CK3 已退出。** 01:11 只读核对无 CK3 进程，原 R0034 Game PID 233756 和 keeper PID 257164 均已结束。守护回执记录 00:30:06 自然退出，退出码 1，Job 清理完成。退出原因待查。Java Dev PID 115676 和 Steam PID 312640 仍在，业务工作者此前已退出。
- **第 10 批完成，第 11 批中断。** 原版独立配置已核对为无模组。Full111 已在实机读取并处理礼仪事件 `rite_growth.0010`。第 10 批自主选策、推进 30 日，新增文件评审请求为 0，原动作在 seq164 入账并在 seq167 结算。第 11 批在任何新动作发出前因缺少 `query-pending-character-interaction-context-v1` 停在规划阶段，业务工作者于 11 月 27 日 23:36:04 退出。账本当前 seq170 `BATCH_INTERRUPTED`，状态 `repair_required`，无干净重接票据。
- **1070.12.15 是最后观测日。** 11 月 27 日 23:34:30 的完整快照 `native:66` 确认原角色 31254 存活、地图暂停、无普通活动事件；有角色互动实例 939524106，发起者 36700，`auto_accept=false`。与命名档相比累计观察推进 67 日，该段无可核验的物理存档。
- **最近可读物理档为 1070.10.09。** 原版命名档 `阿普利亚公爵，罗贝尔_1070_10_09.ck3` 为 15,133,986 字节，SHA-256 为 `44a659781863dec57b435ea053727630b7fc2be3234af199da7a8a62d299fe61`。业务账本最后确认的物理保存日为 1070.09.14。本次新增确认保存日为 0。第 10 批完整墙钟为 851.517 秒，目前没有可报告的秒数／已保存日。

## 续行优先级

1. 由 Runtime 核对当前本机进程、Steam 实际模式及账本。用户授权仅本机可以使用 Steam 在线启动和游玩 CK3。在线启动须核对账号占用。上一份 Steam 离线实际回执只代表当次启动。
2. 优先补齐原版 Full111 的角色互动上下文读取。绑定实际角色、实例、发起者及可执行选项，经真实原生回读后进入既有互动处理流程。上述实例是退出前的历史观测，从物理档恢复后，以当前观测为准。
3. CK3 进程确需重启时，优先从已核对的 1070.10.09 命名档接续同一战役。保留 seq170 与已有动作事实，经原账本允许的接续入口恢复。已结算和 UNKNOWN 原动作均禁止重发或续旧期限。普通业务修复只热载工作者。
4. 先恢复真实完整规划循环。归档去重候选 `0e2fdc2741` 已用该局原 seq153→154 做同结果回放，读取 936→466 次、1,729,593→861,229 字节。实机提交热点仍待对照。详细经过见[实机日报](../autonomous-agent-progress/daily/2026-11-27.md#2334-全自动三十日动作完成并继续)。

## 本机入口与证据

- 正式工作树为 `D:/master-branch-close-20261126`，日常增量构建输出在 `D:/codex-ck3-background/autoplayer-continuation-20261126`。在用或有未提交修改的工作树按其原 owner 管理。
- 持久状态根位于 `D:/ck3-state/ck3-version-migration-20261118/agent-live01/independent-writer01`。账本和批次历史在 `business-root56/continuity/continuity.json`、`business-root56/state/worker-batches.jsonl`。1070.10.09 命名档在 `profile-next56/save games`，1070.09.14 的原业务物理档在 `profile-next41/save games/xar_checkpoint.ck3`。
- 实机证据目录为 `D:/ck3-state/ck3-runtime-continuation-20261126/source56-autonomous-recovery-20261127/named-lease-remount-preparation`。查第 10 批与下一批启动用 `ACTUAL-R0034-BATCH10-CYCLE-SETTLED-BATCH11-ACTIVE.json`，第 11 批停止用 `lease-ordinary-worker-dev.stdout`，窗口退出用 `owner-option-lease/terminal.json`。
- C 盘本轮清理后仍有低余量波动。新工作树、构建和状态优先使用 D 盘。保留依赖缓存及在用目录，详情见[机器存储规则](../maintenance/ck3-operating-authority.md#按机器和任务适用的授权)及 `D:/ck3-state/c-drive-cleanup-20261127/SUMMARY.json`。

每次交接更新本页并删去已完成事项、过期限制和失效入口。发布记录、专题合同和原始证据继续随各自主题维护。旧交接从 [Git 当时的目录](https://github.com/XenoAmess/ck3_eternal_recurrence/tree/76344db33c2226294f16b78e3f316859e9f7adca/docs/handover)查阅。
