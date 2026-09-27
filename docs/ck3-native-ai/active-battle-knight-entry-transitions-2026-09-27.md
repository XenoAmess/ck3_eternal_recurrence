# 现役战斗骑士与动态 entry 转移：静态边界（2026-09-27）

本页只针对 CK3 `1.19.0.6`、`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。目标是拆开现役战斗续算缺域 `battle_knight_participation_and_dynamic_entry_transitions` 的可观测状态、原版生产顺序和未闭合的跨日转移。本轮只读既有原始证据和 exact-build 指令；没有启动 CK3、调用原生 mutator 或新增生产读口。已有 [阶段事件研究](combat-phase-events.md)、[七边界追踪](combat-phase-event-trace.md)、[自然增援](battle-reinforcement-and-join.md) 和 [战斗控制器](battle-controller.md) 是下述证据的上游。

## 四种不能混作一个名单的身份

| 名单／字段 | 原生来源与顺序 | 本轮可确认的用途和边界 |
| --- | --- | --- |
| 战斗双方军队 | `CCombatSide+0x10/count+0x1C` 的 full `CArmyID` stored order | `0x23C8A60` 每日从每军 `CArmy+0x120` 取候选将领；增援尾插、owner-subset 撤退抽离会改变它。 |
| 战斗兵团 entry | levy `side+0x28/+0x34`，MAA-like `+0x40/+0x4C`，每 row `0x60` byte，`+0x08` full `RegimentID` | 现有 `battle-control-snapshot-v1` 同帧读两 bucket、current/soft/effective stats、主阶段资格及 army backlink；它没有逐行 `CRegiment+0x148` 骑士 CharacterID、事件排程/火点状态或下一日未来 entry。见 [`ReadBattleControlEntryBucket`](../../ck3_autonomous_player/native_bridge/src/ck3_11906.cpp)。 |
| 脚本 `random_side_knight` 候选源 | `0x19DD670` 按上述 MAA entry order 解析 Regiment 后读 `CRegiment+0x148`；只跳过 `-1`，不在 materializer 做 alive filter | 后续 compiled predicate 与尾项填洞可改变候选顺序；不能拿按 CharacterID 去重/排序的公开骑士表代替。详见 [原生选择器](combat-phase-events.md#原生-random_side_knight-顺序与抽签)。 |
| 每日骑士事件排程 | `0x23C8750` 清 `side+0xE4`，按 MAA entry order 读取同一 `+0x148`，角色有效性 vfunc 为真且 `(CharacterID + day_index) % COMBAT_EVENT_DAYS == 0` 才送 `0x2E1C570`；非空事件 append `{effect pointer, RegimentID}` 至 `side+0xD8/+0xE4` | 事件 row 冻结的是 RegimentID，**不是**未来火点的 CharacterID。`0x23C9900` 重新解析 Regiment、现有 `+0x148` 和仍在战斗的 Army；故排程、脚本候选、真实出伤参与者不能共用一个布尔量。这里“角色有效性”只按该 vfunc 的返回描述，未把它外推为所有脚本 `alive` 语义。 |

`0x23C8750` 的将领事件另读当时 `side+0x74`，写 `side+0xF0`；函数尾调用 `0x23CB8D0` 从军队 stored order 重建 `side+0xF8/+0x104` 的一军一 owner 权重 row。主 tick 的 `0x23CA2F0` 先由 `0x23CBC20` 校正 **primary participant `side+0x70`**，再按 `+0xF8` row 更新 `+0x58` participant ledger，最后尾跳 `0x23C9900` 发事件。`side+0x70` 与 **selected commander `side+0x74`** 是不同字段；不能把前者的 first-army owner fallback 写成将领替换规则。

## 原版已确认的日内顺序

1. 同一 `CCombatManager` 日更循环在 `0x27FB57A` 调 `0x2308D50`，内部分别以 `0x23CBCE0` 刷新两侧骑士/称号 modifier 聚合，再由 `0x23CC2B0→0x23D2CE0→0x239CAE0` 逐 entry 写回有效伤害 `+0x40` 与坚韧 `+0x48`；之后在 `0x27FB58F` 开始 side0 `0x23C8750` 排程。`0x23CBCE0` 过滤失效角色并重建称号 modifier 缓存，**不会由自身删除兵团 entry**。先前两次实机已观察到暂停值与排程入口的骑士属性变化，例如 RegimentID `220` 的伤害／坚韧由 `20,000,000/4,000,000` 变成 `18,500,000/3,700,000` Q100000，见 [属性刷新证据](battle-reinforcement-and-join.md#2026-09-26到达日首次安排事件前会重算兵团有效属性)。不能将暂停 entry 的有效属性直接沿用到下一日。
2. exact-build 日常 `CCombatManager` dispatcher `0x27FB5D0` 在 `0x27FB683` 对 side0、`0x27FB6A2` 对 side1 依次调用 `0x23C8A60(CCombatSide*)`，取返回角色的 full CharacterID 写 `Combat+0x94` 与 `+0x3DC`，即两侧 `side+0x74`；然后在 `0x27FB6C6` 递增 phase day，主阶段分支于 `0x27FB6FD` 进入 `0x2309E80`。`0x23C8A60` 从 army stored order 取每军 `CArmy+0x120`，过滤无效候选，多候选时经 `0x2307080/0x2307680` 比较及索引重排；精确排名/tiebreak 尚未在本轮闭合。因此 **当前 `battle-control` 的 selected commander 和 roll bounds 不等于下一 tick 必然所选**，尤其存在伤亡、增援或撤离时。只读生产采集应截取原调用返回，不能在暂停查询中再调用该 helper。
3. `0x2309E80` 依次进入 side0、side1 的 `0x23CA2F0→0x23C9900`，再处理后续掷骰、优势、两侧出伤及伤亡写回。side0 效果可以在 side1 火点之前修改角色与链接；目前没有证据把“角色死亡”直接等同于“同日兵团 entry 已被删除”或“已刷新两侧所有有效属性”。不同 manager 的全局同日先后，以及 phase event 与随后属性重算的完整同步点，仍须原调用边界对拍。

## 已观察的转移与真正的缺口

- [production-live] 第 26 日独立 [骑士击杀回流](combat-phase-event-trace.md#2026-09-26第-26-日骑士击杀者抽签实机闭合)：载入行 `11 knight_killed` 的目标 CharacterID `33437`、RegimentID `65`；`random_side_knight` 14 人过滤后选 index `8`／CharacterID `34120`。七边界的火点 5 目标仍活、有效勇武 `4`、兵团 65；边界 6 出现 death marker、有效勇武 `2`、兵团链接清空。后存档有 `death_battle/killer=34120`。另一同源 [下一暂停帧对照](combat-phase-event-trace.md#事件后的下一帧智能体输入) 显示 69→68 团、30→29 名骑士，仅 65／33437 消失。这个**单案**证明死亡 detach 可回流下一帧，不证明所有 wound/maim/death effect 的完整写集、同日伤害重算或死亡当刻 entry 删除顺序。
- [static-confirmed] [库存事件树](combat-phase-events.md#战斗相关-scripted-effect-转移)中 `increase_wounds_effect` 在 wounded rank 3 再受伤可死亡；maim 分支可再调用 wound；直接 killed 分支写角色 death。非致命伤可能改变下一次有效勇武/属性，不能一律移除骑士。下一日取值还依赖 trait、modifier、实际兵团链接和原生属性刷新。
- [static-confirmed + production-live] 兼容战斗自然增援沿 `0x23C9100/0x23CEFC0/0x23D0520` 尾插 incoming ArmyID 与兵团 entry，main participant 与 reserve 从原始兵力初始化，写 `CArmy+0x128` CombatID backlink，刷新双方 aggregate；pursuit join 还把 phase 重置 main。第 11→12 日 ArmyID `22` 的 side0 兵团 27→40，第 21→22 日 ArmyID `28` 的 39→44，两案首次 side0 火点已见新增军队并同日出伤，见 [七边界投影](battle-join-schedule-boundaries-2026-09-27.md)。`0x23C9100` 只追加，不重置旧 entry 的 current/soft；新 entry 有主阶段资格和 reserve 区分，不能把“骑士兵团在 roster”直接当本日出伤。
- [static-confirmed + production-live] full-side 撤退与 mixed-owner partial 是不同转移。后者 `0x23CA360` 逆 stored order 抽 owner subset、清撤离军的 CombatID backlink，其余 owner 继续战斗；已有原版 [owner-subset 样本](battle-reinforcement-and-join.md#2026-09-27三军结构门通过但自然求援未触发) 从 side0 `[16777221,16777231,27,22]` 移除 `16777221`，保留其余。不能按全侧终局重置处理。

## 最小只读 producer 与对拍门槛

先在**同一 CombatID、同一 native revision、同一原始日更线程**采两侧有序 full ArmyID、每军 commander CharacterID 与 owner、两 bucket 逐 entry full RegimentID／army backlink／`CRegiment+0x148`／主阶段资格／starting-current-soft/effective stats；每个 CharacterID 严格 generation 校验，并读取当刻 alive/伤势/有效勇武及会影响骑士效能的来源。另按 schedule 入口/出口保留事件指针在**同进程载入表**中的 load index、RegimentID、当刻 CharacterID 和空排程状态；按原始 `0x23C8A60` 调用记录两侧选中将领前后 ID。火点分别记录重解后的 regiment/character、effect root 身份与写回后链接、entry、modifier 缓存，再在后续出伤/伤亡边界核 entry/current/soft 与下一暂停帧存档。任何 count/pointer/generation、对象身份、revision、线程或边界缺失，整组转移 `unavailable`；不得把 v3 假想接战名单或暂停帧属性冒充下一日现役状态。

有界实机矩阵至少含：无事件对照；非致命 wound、maim、rank-3 wound death、直接 knight death；side0→side1 与反向击杀；被排程人物在火点前已死亡/链接改变；将领死亡与多军候选重选；主战／reserve 骑士；同日加入和 owner-subset 离开。每案以原版七边界原始回执、源档/EXE/DLL hash、loaded event index、clean exit 与下一暂停帧作同身份前后对拍。零次事件、零次将领更换或零次增援只意味着**该自然窗口未命中**，不能排除生产路径。必须由已有受管 runner 的新独立 attempt 执行，保持只读钩子默认关闭；本备忘录本身不开放游戏启动权限。

在死亡/伤势对有效属性与 entry 的原始同步点、真实下一日 commander 重选结果及 join/leave 的 phase/width/事件联合状态尚未同帧闭合前，`battle_knight_participation_and_dynamic_entry_transitions` 仍是整场原生校准胜率的 missing domain。
