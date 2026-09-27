# 现役战斗非掷骰优势：将领与 side 聚合项的最小取证（2026-09-27）

本文接续[优势缓存来源链](active-combat-next-day-advantage-sources-2026-09-27.md)，只审 CK3 `1.19.0.6`、`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的原版 `0x2307CB0→0x2307680/0x2307230` 路径和 `14b23e1e2e5e35c13e74dfc2fdc355aa5c98d730` 时 bridge 源码。此次没有启动 CK3，未把暂停帧的 `resolved-base-roll` 算术残差升级成原版来源，也没有新开生产 bridge 字段。

## exact-build 来源链与可观察累加点

只读 [`extract_active_advantage_sources.py`](../../ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py) 的 `--verify-components --expected` 同时检查 EXE SHA、[缓存路径](active-combat-next-day-advantage-sources-2026-09-27.md)的 18 个锚点、PE `.pdata` 精确函数边界和本页 25 处指令地址/操作数。冻结的 [`active_advantage_component_sources_11906_v3.json`](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_component_sources_11906_v3.json) SHA-256 为 `4831C966BB93DAD30EBEF4B20F5D90B313128F518684AD62530CFE906A70B14A`。它只读原始 EXE，不调用游戏。

本轮较早的[初始范围回执](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_component_sources_11906.json)与[累加点回执](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_component_sources_11906_v2.json)保留为过程资产；前者尚未覆盖 total 累加点，后者尚未在同次校验中包含缓存调用链。正式结论以 v3 为准，不用旧回执提高证明等级。

| 原版阶段 | 本轮证明的机器事实 | 对观测的意义 |
| --- | --- | --- |
| 两侧 total 初始值 | `0x2307CE7` 将当前 side roll×`100000` 写入输出 qword；`0x2308D50` 的两次调用均以 R9=0 进入 helper，跳过 target-context 条件支路 | 在这条缓存生成路径，初始值是当次调用所见 roll；暂停查询的现时 roll 未必是它。 |
| 将领贡献 | `0x2307E88` 调 `0x2307680`，`0x2307E8D` 从返回指针取 qword，`0x2307E90` 加到同一输出 qword | 原调用边界可只读记录**该次返回的数值及相同调用前后 total**，无须暂停时重入 helper。 |
| side 聚合贡献 | `0x2307EB5` 调 `0x2307230`，`0x2307EBA` 从返回指针取 qword，`0x2307EBD` 加到同一输出 qword | 可在原调用后记录第二项和最终 per-side total；两侧按原 `base+side0-side1` 组合。 |
| 将领 helper 实际依赖 | `.pdata` `0x2307680..0x2307A2D`；读角色对象 `+0xD8`、side index，调用 `0x2306940/0x2306C70` 与 modifier-set resolver `0x26172C0`，还读人物兵团链接 `+0x1B0`、做身份比较 | 仅有将领 ID 或通用优势点数不能构造完整当日贡献；`+0xD8` 和具体枚举不在本轮凭偏移猜成人类字段名。 |
| side helper 实际依赖 | `.pdata` `0x2307230..0x2307679`；处理 null context，读 `side+0x110` 聚合器的 modifier set，调用 `0x2940D50`、`0x20AB950`，并沿 combat `+0x6B8` 战场上下文及 `+0x6FD` flag 走分支 | 聚合值不是可从当前人数、战宽或 GUI generic advantage 直接反推的单一常数；具体 modifier enum 名及每项语义仍未完全闭合。 |

`0x2308D50` 的每次调用分别先得 side0、再得 side1 total，最终写 `Combat+0x710`。本表只对这一来源路径负责；不同 manager 的全局次序、事件/增援引发的 source mutation 和下一日具体贡献没有实机对拍。

## 当前 bridge census 覆盖

`game_contract.hpp` 的 `BattleControlSideSnapshot` 含 `selected_commander_character_id`、`selected_commander_next_roll_bounds`、`current_roll_points` 和军队/两类 entry；总快照含 `base_advantage_raw`、`resolved_advantage_raw`、cadence。`ck3_11906.cpp::ReadBattleControlSide` 校验当前将领身份，并仅用原版掷骰 endpoints 计算下次 roll bounds；`ReadBattleControlSnapshotSample` 读取当前缓存和 roll。Python `battle_control_contract.py` 校验这些字段。它们**没有** `commander_contribution_raw`、`side_aggregator_contribution_raw`、这次缓存重算所见 roll、或每侧 total 的独立读数。

战前 `CombatCommanderSnapshot.generic_advantage_points` 通过 `get_commander_advantage(commander,-1,false)` 取得，是另一接口/语境；`CombatCommanderContextSnapshot` 的战前 base advantage 也不是现役 `0x2307680` 与 `0x2307230` 在原调用下的返回值。不可将任一项回填到当前 `BattleControlSideSnapshot`。这些结构体和读法在上述 commit 的 `game_contract.hpp:1301`、`ck3_11906.cpp:14354`、`:14985`、`:8307` 和 `battle_control_contract.py:435` 可复核。

## 最小安全暴露方案及验收门槛

先做**默认关闭的只读原调用追踪**，不在暂停查询中调用 `0x2307680`、`0x2307230` 或任何 modifier helper。对一个 generation-valid CombatID，在 `0x2308D50` 的每次原始调用给单调 `materialization_ordinal`、线程、日期和调用点（已知至少 `0x27FB4AC`、`0x27FB57A`）；在两侧 `0x2307CB0` 的 roll 初始化、将领累加 `0x2307E90` 后、side 累加 `0x2307EBD` 后，只复制相同输出 qword、side index、将领 full ID、side 聚合器身份 token 和当前 roll。`0x2308DCE` 写入后复制 base/resolved，并在消费 `0x2309F55` 前复制缓存与 roll。所有记录限长、预分配、无游戏内分配/RNG/回入；指针只作同进程短期 token，不跨进程当永久 ID。

一组 attempt 必须同 CombatID、同线程、同一次 materialization，把每侧 `total=roll×100000+commander+aggregator` 和 `resolved=base+side0_total-side1_total` 用 checked int64 对拍；任一调用漏采、覆盖、指针/ID generation 变化、overflow、跨 revision 或同日多次重算混合时整组标 `unavailable`。至少再配一组事件日与一组增援日，记录主战消费处是否沿用同代缓存；只有这些原始前后边界闭合，才把**当前调用的分项数值**暴露为 typed diagnostic。它仍不足以预测下一日：需要由原版来源 leaf 和人物/side/战场转移重算每项，并对拍相邻日期，才能从 missing domain 中移除 `next_day_non_roll_advantage_sources`。
