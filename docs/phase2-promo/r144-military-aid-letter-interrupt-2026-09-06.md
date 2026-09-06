# R144 军事援助来函中断合同（2026-09-06）

## 实机边界

- frozen source：`c9bfb48002560c90ea11e1910d3ec19b26c13607`；源码 ZIP SHA-256：`3606252984B23D8A494C8A22C297DD325CD46E78AED5E87ABC6A1E61C138EFCF`。
- no-launch preflight GREEN，R130 的 1031-file 产品投影与四个关键 B2 effect 保持逐字节一致。
- CK3 PID `178136`、玩家 CharacterID `32904`、默认 5 速；acceptance-only 存活保护在日志中精确应用一次：`health=10 epidemic_resistance=100 days=1100`。
- 玩家保持存活并越过 R143 的第 42 日终止点；本轮先精确处理 `tribute_mission.1002` 与 `.1005`，随后在 `date_raw=53156904` 捕获原版 `tgp_interaction_event.0015`，event instance `16`，B1 仍 active。
- `manager-cycle-recovery.json` SHA-256：`4AE137F90C7E662635A0EEB1C3A988AF3F96945B8375FDBDDCE023BD60909E11`。
- `runner-report.json` SHA-256：`9F4958BAC31A3E062BF7A4AD9558A36FBBCA11722E527D6BEF6AF9E672C38A6B`。

## 精确事件合同

原版 interaction 在来函打开前已经把援军管理者加入收件人的战争；`.0015` 的 immediate 只显示 tooltip，唯一 option 也没有 gameplay effect。因此 runner 选择 authored option 1 / native index 0，但只在以下完整形状同时成立时允许：

- root 为当前玩家 `32904`；
- saved scopes 恰为 7 个：`actor`、`recipient`、`secondary_actor`、`secondary_recipient`、`intermediary`、`governor_at_war`、`governor_joining`；
- `recipient` 与 `governor_at_war` 都等于玩家；
- `secondary_actor` 与 `intermediary` 是类型为 character、typed identity unavailable 的 source-defined 空角色 scope；
- `secondary_recipient` 与 `governor_joining` 是同一名非玩家角色；
- 只有一个 shown/enabled、非 fallback/cancel 的 native option 0。

该事件是原版已经发生的军事援助通知，不是产品 RED，也不提升逐号 readiness。manager-recovery 用途分片测试现为 6 个场景，仍处于每文件 1–10 的目标内。
