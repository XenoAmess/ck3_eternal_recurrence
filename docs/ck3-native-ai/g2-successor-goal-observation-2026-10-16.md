# M7 新罗贝尔战役的继承后意图观测

2026-10-16。G2 仍为 6/8；M7 未完成。此包只消费两份已闭场 MCP 回执，零游戏/进程/桌面操作，不读活跃 Driver，不阻塞自动游玩。

既有源码在普通 campaign 中创建并保存 `dynasty_continuity`，matched successor continuation 更新 current/progress，hot/cold adoption 保留 goal；`GameplayBridgeService.plan_turn` 将其交给完整 planner 并记录 `campaign_goal_plan_used`。本包复用此链，不修改策略或恢复器。

## 实际增量

N41 P07 SAVE13 与 N42 P03 SEM1 记录的 goal 全值相同：campaign `native-31254-96253c58fd68`，origin31254/current40526，reconciled_successions1，last transition31254→40526；matched titles2191/2204/2230/2231，expected other-heir title2262。两者同 raw53327184、episode `native-40526-c7a6edcc32b8`；回执实际 Game PID 为255216→249712。SEM 为 alive/paused/map_ready。

SAVE13 为 h1142、126616629 bytes，checkpoint SHA-256 `7cfca088d84d7d49354eebd5dc9557e50e6dd4cee17d6afdcbf60770074c3ea5`。replace receipt 记录 save_binding_verified=true，scope 为 `WRITE_REPLACE_RETURNED_NOT_FSYNC`。

原件根目录：`D:/codex-ck3-demos/2026-10-14-robert-30year/`。

| 闭场原件 | SHA-256 |
| --- | --- |
| `continuation41-cold-prep/p07-responses/0013-1-result.json` | `b48af6d2febc1e6bcc5286aea3f733c57288ad9837e6b06429084239febf70ea` |
| `continuation42-cold-prep/p03-responses/0001-1-result.json` | `dc3d97bf43ffd1f562e1a9ff4479e22a2c8c43f30161a57e13833afe1f225eec` |

[仓库内精简摘录](g2-successor-goal-observation-2026-10-16.json)与外置原摘录字节一致。外置原摘录：同根 `g2-m-gap-research-20261016/m7-goal/ACTUAL-CLOSED-SUCCESSOR-GOAL-PROJECTION.json`，SHA-256 `b9650bbc5d84ea9294599cf2ea3027f4e290cf280b68399cfedf67ba02f5ed38`。

## 边界与后续

可确认继承后 intent 随 checkpoint 持久化，并在另一实际 Game PID 的同日同 episode 语义帧完整保留。两原件没有 normal-plan consumption 或完整 physical cold-anchor 对比字段；不把同日期、不同 PID 当作全部恢复资格，也不混入旧29829战役。

后续离线消费正常完成的 successor plan 与 Root 已有 cold custody 小回执；不新增 MCP 查询或重启。广泛 rulers/seeds/governments 继续未完成。新的连续30年无停机修复目标由主 continuity ledger 计数，本包增加0天。

复用工具：[extract_g2_goal_continuity.py](../../tools/extract_g2_goal_continuity.py)。一次实际摘录和3个必要 projection cases 已通过；旧4项 goal 矩阵未重跑。`open_kaishek` 为 not-applicable：这里只投影 JSON/Python semantic fields，无 Paradox parser/IR/finite-runtime 语义；参考 checkout `1643d03d3a8d2ae1547e352d724e2b1a721c98ba`。精确游戏版本1.20.0.4，EXE SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。
