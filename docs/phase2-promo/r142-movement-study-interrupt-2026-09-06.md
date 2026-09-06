# R142 原版运动研习事件中断合同（2026-09-06）

## 实机边界

- frozen source：`75ffcad258c6a4b3c69c59c98443b383ff4014a2`。
- no-launch preflight：GREEN；报告 `Z:\p2m142_pre_a\preflight.json` SHA-256 为 `DA98C2B5F2838F8080795DA7FC229E81E046687C10570B0D2FEF7A4AC2BBE61A`。
- CK3 PID `69976`，玩家 CharacterID `32904`，默认 5 速；R130 的 1,031-file 产品投影及关键 B2 字节等价门保持 GREEN。
- 在 `date_raw=53150712` 捕获原版 `tgp_movement_events.0070`，event instance `16`；玩家存活且 B1 active，本轮没有 owner terminal。
- 本轮已经严格处理 `tribute_mission.1002` 与 `tribute_mission.1005`；随机时间线没有重现 R141 的尚书事件，这不改变其已登记合同。
- `manager-cycle-recovery.json` SHA-256：`8CCA1B0F39FF6E3E5F008A4C159A6BC32D9A28BD9B09356ABBA28EF5BFC3786`。
- `runner-report.json` SHA-256：`0E262B77E7A74651A7C34974B33B6419DA6D53730707F0F709ADC2626C76729F`。

## 精确事件合同

实机窗口 saved scopes 恰为 `my_movement:situation_participant_group` 与 `councillor:character(29889)`；三个 rendered options 依次映射 native indices `0,1,2`，均 shown/enabled，均非 fallback/cancel。

原版三个分支分别为：

1. 与廷臣推进友谊关系，并结算 trait-dependent stress；
2. 给廷臣增加两点相关/最高技能，并结算 stress；
3. 给玩家与廷臣各增加一点最高技能，并结算 stress。

为避免改变玩家技能或用人评价输入，runner 固定选择 authored option 1 / native index 0。它不是无副作用按钮，但在三个原版分支中对天朝二期产品时间线干扰最小。合同只登记这一精确 key、两个 scope、三按钮形状、manager root 与 observation window；任何漂移继续在操作前 RED。

该中断属于原版玩法事件，不是产品 RED，也不提升逐号 readiness。用途分组的 manager-recovery interrupt 测试文件现有 5 个场景，仍在每文件 1–10 的目标内。
