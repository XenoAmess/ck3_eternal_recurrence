# CK3 1.19.0.6 战斗 phase effect：本场回流分类

## 冻结边界

- 原版 EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。以下脚本行号只针对该 build 的 `Crusader Kings III/game`，不把其他版本或 mod 加载表外推到当前场景。
- R0207 Robert h2134 原始 v3 查询 SHA-256 `8621F26CFC14841444C81A7377723D0B87945C10289C0741E6BAACD0DA55A196`（冻结索引 `1A8499E91F645C68CBA2BE4052AB6E5523DBDC6711045EF6C89AC9D23BA77B24`）：24 个 root，9 类 stock row 在首帧 trigger valid 且整数权重为正。敌侧 acclaimed knight `29963` 的 `knight_wounded/maimed/killed` 权重分别为 `89/33/25`。
- R0209 旧独立战斗的一日原版 trace 已严格捕获七个边界（原始 JSON SHA-256 `175D14E489B98BC9A287DF9CA1F5D88124703C682A17EFA2CD988D40E58F5CFF`；冻结索引 `B1C3008925E7B096AA9EE40A2B8DEEE031D29B6585B5C036BE1A21E2DFD22FA3`）。两个 schedule 边界在 D，四个 fire 和 final 在 D+24；两次 fire 的 global RNG counter 各加一，但七个边界的 `battle_events` 均为空，`full_mutable_transition_bundle_complete=false`。此 trace 只校准无效果日的顺序，不能校准事件回流或 Robert 当前战局。

**正权重行可达不等于 effect 分支必定执行，更不等于该 effect 改变本场胜率。** 下表用现有 stock 源码与已逆向的调用链区分下一次 main tick 可能消费的状态、战后数据候选和仍需回调证据的条件路径。所有“候选不回流”都还不是 simulator fidelity GREEN；若脚本变量、native callback 或加载 mod 使同场状态变化，须重新分类。

## 15 类 effect 的最小依赖账本

| Effect 类 | 现有 exact-build/stock 依据 | 对本场胜率的处理 |
| --- | --- | --- |
| `glory` | `00_knight_phase_events.txt` 多处 `add_glory`；native `0x2E5B6F0 → 0x251C2F0` 改 `CAccolade+0xB0`，rank helper `0x251B780` 可改 tier。13 行 AST 再读双方 accolade parameters；R0207 的 29963 确为 acclaimed 且伤/残/死行有正权重。 | **直接回流候选，优先建模** glory/rank 与后续 event weight、knight contribution/advantage；核对 rank-change 回调及 recipient。 |
| `delayed_infection_or_treatment` | `20_health_effects.txt:1159–1167` 在 2–3 天安排伤口治疗/感染；`root.traits.wounded.rank_raw`、alive 与 effective stats 是后续输入。 | **时间条件下可回流**；battle 未在触发日前结束时，必须模拟调度和状态重算。 |
| `delayed_epilepsy_risk` | `20_health_effects.txt:1055–1063` 的分支安排 `trait_specific.2001` 于 30–300 天；当前研究 horizon 为 120 天，不能仅用“通常战斗较短”忽略。 | **时间条件下可回流**；可用独立原版结束上界证明本场先结束，或模拟延迟事件。 |
| `toast` | `send_interface_toast` native wrapper `0x2E7A9A1..0x2E7A9EE` 在 `0x3380840` 恰执行一次 nested wound/maim/death effect，随后才处理消息容器。 | 内层人物转移必须保留且只执行一次；**wrapper 自身是否额外写战斗状态待四边界 delta**，不把整段忽略或重复伤害。 |
| `cranial_trophy` | `00_knight_phase_events.txt:1302–1319` 是条件脚本；`10_dlc_tgp_scripted_effects.txt:4443` 起创建 artifact、`flag_as_trash_artifact`、加 piety，脚本没有显式装备。 | **条件回调未闭合**；需证 create-artifact 是否自动装备/改 effective stat。不得从 artifact modifier 名称直接推断本场加成，也不扩大宗教策略研究。 |
| `prestige` | phase 脚本在伤/杀敌分支 `add_prestige`；13 行冻结 AST 的 132 个 ref 不读取 prestige 原值，但资源更新可触发 native 派生修正。 | **回调未闭合**；只查本场角色 prestige 写入前后 fame/modifier、commander/knight stat delta 与下个 tick 的消费。 |
| `battle_event` | native `0x2EB4330 → 0x130A660` 向 BattleResult `+0x188` 追加有序 row；R0209 该容器没有新增 row。 | **战报输出候选**；须查 append helper 的 write-set 与任何 main tick 对此 ledger 的读 xref，不能仅凭空 ledger 认定 inert。 |
| `accolade_eligibility_interface_message` | `00_knight_phase_events.txt:1539–1881` 的多个 unlock 分支写入变量后调用 `send_interface_message`；13 行 AST 读取 unlock 变量，消息发送本身是另一调用。 | unlock 变量须保留以影响后续选行；**UI 消息回调待证不回流**，不要把二者混为一项。 |
| `slain_list` | `00_knight_phase_events.txt:1285/1333` 写 `slain_side_knights` 并注明 after-battle messaging；`events/war_events/combat_events.txt:1026–1038` 在战后汇入名单并清空。 | **强候选为仅战后消费**；再核 native variable-list writer 无即时 callback、loaded playset 无额外消费者后可从本场数值转移排除，战后结果仍保存。 |
| `battle_location_variable` | `00_knight_phase_events.txt:533–540` 在 `knight_becomes_incapable` 加 incapable trait 后，把地点写进新 memory。 | incapable trait 本身直接影响角色；**memory 地点元数据待证仅叙事**，需要 memory-variable callback/consumer check。 |
| `memory` | 同一事件 `create_character_memory` 后设地点；13 行 AST 不读取 memory，但 native 创建回调未对拍。 | **回调未闭合**；只查创建前后 trait/stat/side 与后续 main-tick 读取，不另造通用记忆模型。 |
| `house_relation` | `00_knight_phase_events.txt:1290–1300` 在击杀分支调用 `change_house_relation_effect`；13 行 AST 读 house identity，不读关系值。 | **回调未闭合**；检查关系变更是否即时改变 combat modifier/participant，不把 house identity 与 relation 混同。 |
| `hold_court_delayed_event` | `00_knight_phase_events.txt:1220–1235` 清 promise 并延迟 1 天触发 `hold_court.8053`；对应事件 immediate 对该已死 knight 显示 tooltip death，且有玩家选项。 | **运行控制与外部事件路径**；需要确认晚到事件不二次改变 combat side，也要由正式事件处理器消费提示；不把 prompt 算战斗概率。 |
| `battle_death_variables` | `00_death_management_effects.txt:111–123` 给死者保存 enemy/leader/location；`death_management_events.txt:125–137` 在死亡事件读取并移除，后续死亡事件分支引用这些 scope。 | **死亡链外部回调未闭合**；核心死亡/撤出已建模，但需查死亡链是否同日改变当前战斗、战争或玩家身份；后两者还影响行动效用。 |
| `mongol_beheaded_variables` | `00_knight_phase_events.txt:1360–1423` 在条件分支向 liege 写 beheaded-warrior 相关变量。 | **条件故事路径未闭合**；先由 stock 条件/原版 effect occurrence 确认本帧实际触发，再查变量消费者与即时回调；不得因 R0207 faith ID 为 opaque 就猜条件真假。 |

## 下一次最小施工与验收

### 2026-09-24 梅西纳独立回放的局部事件时序

[episode01 共用阶段事件观察](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_phase_event_observations.json)（SHA-256 `94831B16AE56BC050833D7BEE9064170D118F77700DE672A0977E68F47C98AAE`）从 attempt-004 原始回执逐份校验后投影。第 5、7、9、15、16、19 日均有一次 battle-event ledger 追加；对应局部 fire 前后已捕获的 character core 和 accolade 字段六次全无 delta。第 5 日受伤目标 36303 的勇武在 fire 前后及下一源日 schedule 前均为 8，下一源日 fire 前为 6。第 15 日阵亡目标 36673 的 death marker 在 fire 后仍为 false，下一源日 fire 前为 true。第 15、16 日只满足局部成对记录条件，整日 trace 仍为 `trace_unavailable`。

exact-build stock `game/common/combat_phase_events/00_knight_phase_events.txt` SHA-256 `E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1` 中，受伤分支先写 `battle_event`（727–733），后调用 `increase_wounds_effect`（734）；击杀分支先写 `battle_event`（1277–1282），后执行 `death`（1318–1320）。脚本顺序与“账本先可见”相容，但不能据此推出运行时同步边界，也不能把脚本行号当作实际写集回执。

这些观察把“事件账本何时追加”与“被追踪字段何时变化”明确分开；它们**没有**捕获完整 mutable write-set，也没有证明勇武/死亡变化唯一由对应条目造成。后续验收必须定位账本 append 之后到下一次 phase read 之前的实际 callback/调度边界，并同时读取受伤 trait、死亡链、荣誉/威望、参战身份和 outgoing damage。不能用账本条目本身代替 effect 执行回执。

1. 用新的七边界 ordered levy/MAA `starting/current_fighting/soft/hard`、owner-hard ledger 与双方 outgoing damage、`0x18C/0x18D/0x19F` 有效 raw，对拍一个**无事件** main tick 的确定性伤亡；R0209 的旧 DTO 只有聚合，不能给这一步填期望值。
2. 从合法自然战斗中捕获一个**非空原版 effect** 的有界一天：同 CombatID/date split、实际 selected row/root、fire 前后 RNG、root trait/health、participant/commander、accolade rank/参数和下个 tick 读回。调用已合入的 `execute_phase_event_trial_sequence` 做同一 root 的 effect 对拍，再补跨 root/side 写回。对不一致字段只修对应 source/transition。
3. 对表中战报/叙事候选做**定向** callback write-set 与 13 行/主 tick consumer 检查，证明本场不回流者即可排除数值模拟；有反馈者继续建模。迟发事件按当前 battle horizon 判定，不永久要求所有故事系统完整实现。
4. 只有原版状态转移、battle-end/retreat 和当前候选输入对拍后，Monte Carlo 才可能成为合格胜率，再由正式 `combat-entry-eu-v1` 比较进攻、绕行、等待与角色/兵力风险。R0207 的 1.56×人数比和旧 4096/4096 phase-events-disabled 研究胜都不能代替这一步。
