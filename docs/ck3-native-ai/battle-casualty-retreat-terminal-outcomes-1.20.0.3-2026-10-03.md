# CK3 1.20.0.3：首次战斗的伤亡、败退与结束结果观测

2026-10-03。Exact build 为 CK3 `1.20.0.3`、Steam `25652598`，EXE SHA-256
`94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`。
本页整理已存在的原生观测树和安装版 stock 规则，供 Robert `29829` 原普通战役首次战斗 OODA 使用。
战争已获全面授权；未实现的预测质量不构成战争禁令。本文没有提交动作、推进日期或操作窗口。

## 原生输入和证据

施工前读取 [battle 迁移](ck3-1.20.0.2-battle-migration.md)、
[伤亡账解释](combat-casualty-chain-explainer.md)、[终结与再入战](battle-terminal-and-reentry.md)及
[1.20.0.3 ABI 复用](crozier-1.20.0.3-native-migration.md)。1.19 的精确 casualty 数学和 phase-day
调用顺序仍是其原构建的研究证据；本页不将旧 EXE 地址或旧实战自动升级为 .3 live。

.3 production 在完整 descriptor 匹配后使用 `ReviewedCrozierAbiSha256` 选择已证明 unchanged 的 .2
ABI。永久证据 `native_bridge/research/ck3_1_20_0_3_abi_reuse.json` 的 `combat` 和 `battle`
模块分别引用 `ck3_1_20_0_2_combat.json`、`ck3_1_20_0_2_battle.json`；
`ck3_12003_abi_profile.cpp:18` 和 `bridge.cpp` 的 `ExecuteTypedQuery12002` 连接真实 owning-thread
paused snapshot 与现有 battle reader。实际 .3 身份来自 runtime freeze，而非为旧 binder 增加 SHA 例外。

已有原生读取入口及其职责如下：

| 入口 | 原生输入/结果 | 对首次战斗的用途 |
|---|---|---|
| `ck3_query_battle_transition_v1` | CCombat storage `5D1DE70`；完整 CombatID；phase `+6B0`、day `+6B4`、winner `+6E0`、forced winner `+700`、finalized `+704`、result ID `+708`；两侧 stored-order CArmy→CUnit 回链 | 给任何已实际观测的战斗定位阶段和成员，玩家尚未参战或已撤离时仍可查询 |
| `ck3_query_battle_control_snapshot_v1` | 玩家可控、正在战斗、未撤退 CUnit；两侧 Entry60 和 owner hard ledger；native strength `2651100/2657B50`；retreat validator `258AA10`、owner-taking rules `28C2E10` | 玩家实际入战后读取当前 fighting、soft、hard 和真实撤退资格 |
| `ck3_query_battle_terminal_transition_v1` | startup 安装的 natural finalizer `258CD50` 与 warscore writer `249A940` 被动 journal；旧 CombatID/省份/result、subject route/backlink、successor | 旧战斗删除后继续证明正常结果或无正常结果，并决定战后下一步 |
| `ck3_query_army_strengths` + `ck3_take_snapshot` | 完整 CUnit/CArmy；当前/最大整数兵数、所属战争、位置、路线、combat/retreat；snapshot 的玩家身份/存活和 native command history | 战前与战后可用军队兵力和行动状态差分，供继续围城、行军或撤退使用 |

`ck3_12002_battle.cpp::TransitionSample/Bucket/Side/Retreat/TerminalSample` 是本页字段语义的生产来源。
`bridge.cpp::XarCk3BridgePrepareStartup` 对 reviewed Crozier 构建安装 terminal journal；无需另行开启
旧 `WAR_CASH/PREWAR` 才能读取这些核心字段。

```mermaid
flowchart TD
    S[真实 paused snapshot: actor/date/full IDs] --> C[实际 CCombat ID 与 stored-order 两侧成员]
    C --> T[transition: phase/day/winner/finalized]
    C --> J[terminal baseline: latest_sequence; 0 对应 null cursor]
    C --> P{玩家实际属于战斗且可控、未撤退?}
    P -->|是| L[control: entry current/soft/main hard + owner ledger + retreat legality]
    P -->|否| H[仅观测敌军战斗; 不请求 player control]
    T --> D[Root 以真实快照执行一次有界动作或一天推进]
    L --> D
    H --> D
    D --> R[新 paused snapshot 与同 full CombatID transition]
    R -->|仍 active| L2[phase/member/entry 差分; 重判下一步]
    R -->|旧 ID 消失或 phase done| E[terminal journal: normal_result / no_normal_result]
    J --> E
    E --> O[实际 winner + WarID/战分方向 + subject route/retreat/successor]
    O --> N[存活军队的新整数兵数; 下一次观察→决策]
    L2 -. 未闭合 .-> U[完整 .3 伤亡公式复算、人物事件全写集与胜率]
    E -. 未闭合 .-> K[死亡/被俘具体原因的专门人物事件观测]
```

## 当前原战役真实基线

复用 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-battle-phase/actual-battle-transition-v34-01/004-ck3_query_battle_transition_v1.json`，
不重复实测：native revision `16` / public `2` / paused date raw `53236608`；CombatID
`1577058305`、province `2640`，maneuver `0` / day `0`，winner 与 forced winner 均 `none`、finalized false。
实际 attacker CUnits `[251658381,473,474]`，defender `[50331920,83886484]`。
Robert 军 `83886367` 不在双方数组。ResultID `1493172226` 在此机动初帧已经分配，因此 **result ID
非空不是战斗结束证据**。这些实际成员不能由另一份“玩家对叛军”的假想 v2 partition 替换。

本基线提升的是敌军战斗生命周期 `production-live primitive`；Robert 未参战，也尚无本战的伤亡、
结束、胜利或完整战争 OODA。敌军战斗的 terminal baseline 可以以实际 rebel CUnit `251658381`
作为 subject；该 query 没有 controllable 或 player-army 闸门。其 subject 状态描述这支叛军，不能写成 Robert 状态。

## 伤亡字段单位与差分

Entry 的 `starting_raw/current_fighting_raw/soft_casualties_raw/hard_casualties_raw` 和 owner hard
ledger 都是 **Q100000 兵员账**，除以 `100000` 才是人数当量。属性 damage/toughness/pursuit/screen、
native side strength 与 AI base power 各自保留计算单位，不能直接念为兵数或胜率。
`army-strength` 的 `current_soldiers/maximum_soldiers` 已是整数人数，不能再次除以 Q。

对 `fights_in_main_phase=true` 的保留 entry，reader 以 `starting-current-soft` 计算累计 hard；非 main
entry 的同一残差可能包含 reserve，其 `hard_casualties_status=unavailable`、raw null，不能补成 0。
同一 full CombatID、同一 full RegimentID 两帧的累计 hard 差才是该间隔的该行永久损失。owner hard
ledger 包含其自身归因，不将消失兵团的损失重新分摊给仍保留 entry。

`derived_current_fighting_raw` 是即时 entry 合计；`stored_current_fighting_raw` 可保留 tick-start cache。
既有 .2 fixture-live 已观察二者在 main 帧不同，这个标志不单独阻断 action readiness。
soft 是战斗中已溃散兵员；它可以在追击中转成 hard，战后可用军队整数兵数可以回升。
战前/战后整数军队人数差是净兵力变化，不能冒充 exact hard loss 或人物死亡人数。

## 最小结果验收

1. 战前保存现有实际 snapshot/army-strength，并为实际 CombatID 读取一次 terminal baseline。取
   `terminal_journal.latest_sequence` 为后续 cursor；正数原样传，`0` 传 `None`。
2. 若 Robert 真正入战，在新 snapshot 的真实 side membership 上查询 control + transition + terminal，
   记录 entry/owner ledger、phase/day、winner、retreat legality 和 cursor。对当前仅敌军战斗不调用 control。
3. Root 一次有界动作/一天推进后保存 paused snapshot；SDK root helper 给每个 query 绑定 fresh public
   revision。复用 native command history 与实际状态验证动作；ACK 不计后置条件。
4. 同 CombatID 仍 active 时记录阶段、成员、伤亡差分。owner-subset 撤退只移除 affected owner，其他成员
   和原战斗可继续；full-side 撤退后进入 pursuit 也可暂时保留原 CombatID/backlink。
5. 正常结束由 terminal journal `event_status=observed`、新的 event sequence、`normal_result`、实际
   winner/result 及 removal 证明。`combat_not_found` 只证明旧 generation 删除；`phase=done`、retreating、
   非空 result ID 或 winner 任一单字段均不单独证明正常胜利。`no_normal_result` 单独保留。
6. 战后记录 terminal subject 的 exists/route/retreat/backlink/blocked 和 successor；重新读取实际存活军队
   的 current/max 人数。journal 的真实 `war_id`、`winner_is_war_attacker` 与 attacker-relative delta 决定
   战分归属，combat attacker 不能自动当作 war attacker；当前多战争场景不可按目标省份猜归属。

2026-10-03 v35 实机 terminal baseline RED 纠正了此前“空字段不阻断”的判断：
`prior.phase_day` 是 active 与 observed terminal 的现有序列化必需字段，observed terminal 还必须有
`prior.terminal_date_raw`。原 .3 reader 未投影它们，导致 `typed query result is inconsistent`，
因此该查询不能作为当时已可用的胜负/战分/战后状态观测。最小修复沿现有 native reader/journal
投影真实 phase day 与捕获日期；外部 focused reader→serializer→Python 两场已 GREEN，仍待新 DLL
paused live 验收。`hard_loss_inputs` 仍是可选缺口，未在本修复扩大 producer。
详见 [v35 terminal 实际故障与定向修复](battle-terminal-phase-date-production-fault-1.20.0.3-2026-10-03.md)。

## Root 查询配方与报告

外部工作包目录：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-casualty-outcomes/`。
`CURRENT-HOSTILE-TERMINAL-BASELINE-CALLS.json` 为当前真实敌军战斗只生成一个尚未采集的 terminal baseline。
`build_outcome_recipe.py` 只写配置，不发送 SDK/game 调用；baseline 阶段仅 terminal，player-contact
阶段 control/transition/terminal，post 阶段 transition/terminal。Root 在新实际 snapshot 选取阶段与完整 ID，
`root_sdk_capture_continue.py` 为每一调用刷新 revision。配置是 `{"calls":[...]}` 对象。

安装版 stock 规则与人物结果的差分边界见 [安装版人物结果链](battle-character-result-stock-1.20.0.3-2026-10-03.md)
与本工作包 `stock/STOCK-EVIDENCE.json`（九份实际安装版文件 SHA 与行号）。其中 main 基础 hard 转换
配置 `0.3`、pursuit 三日/转换 `1`、manual-retreat 配置 `14` 都不是人物死亡率或本战实际结果。
现行 `on_combat_end_winner→combat_event.1001→.1002` 捕获链要求双方 primary participant 真实交战；
仅 hostile 而无相互战争的战斗不走此链。`battle_event`/候选列表与真正 `house_arrest`/jailer 回读分开。
指挥官与骑士阶段受伤/死亡资格也分别读取，不能把骑士 wounded3 排除外推给指挥官。
首次作战主线先验收实际军事结果；
被俘与死亡只有在真实人物/羁押或事件证据出现后才计入，不因普通兵员 hard loss、骑士 entry 减少或
人物从一侧数组消失自动认定。

## 2026-10-03 v40：败军现有路线实读，零日增量

Root 的实际 `004` / `006` 查询在同一暂停日期 `date_raw=53238336` 读取两支败军；runtime 为 `v40` / `R0019` / PID `28788`，冻结源 `Z:/g42` / `02e88d57fcef399368f34b23f497d3e8565af95d`。复用 owner 已消费的 `battle-retreat-pursuit/query-increment/actual-v40-01/ROOT-DELIVERY.json` 与 `DAY-WEEK-FIELDS.json`，本段不重测原生树、终结或游戏状态。Exact build 仍为本文的 `1.20.0.3` / Steam `25652598` / Root EXE freeze。

`50331920` 仍在 `2634` 撤退，已提交路线为 `2633→2627→2626→8753→2629→2630→2631`，最终 move target `2631`；对应原生 arrival raw 数组为 `[53238480,53238720,53238936,53239080,53239272,53239440,53239560]`，相对本帧的预计到达分别为 `[6,16,25,31,39,46,51]` 日。`83886484` 同样仍在 `2634` 撤退，路线为 `1032→8645→8754`、move target `8754`，arrival raw `[53238960,53239104,53239344]`，预计 `[26,32,42]` 日。两行 `status=available`、coordinator `16777247`、`route_alignment=no_assignment`，assignment ETA 均合法 `null`。完整已提交 route/ETA 与原生 AI membership 已可读取，无需为这两条 timeline 新增 API。

两军的 `asking_for_help` / `assigned_to_help` / `asking_changed_last_evaluation` 均为 false；`cross_coordinator_request_valid_raw=0`，power basis 与 cross request power 保留 `null`。首条 route edge 的 remaining duration Q100000 分别为 `638752` 与 `2559441`，不替换已发布的 rounded arrival dates。该增量是两支实际败军路线与 AI membership 的 **production-live primitive**；ETA 是当前预计，不能证明撤退解除、保护期、实际到达、追击动作、玩家接战或胜率。原生继续/撤退树及策略仍由对应 owner 维护，见 [撤退锁、接触过滤与再交战原生树](battle-retreat-pursuit-reengagement-12003.md)。

本轮 latest normal pair 为 `h5034` / raw `53238336` / `91105480` B / save SHA-256 `7ebe6682539b7e5477566a4613afc2b36356e0880ed94a0d7f9c4a3b62758983`，R0019 / PID28788 已正常退出 `exit 0`。读取新增 `0` 日：累计仍 `3917/36524`，恢复后 `764` 日，2026-10-03 增量 `669` 日。未计撤退解除、收复、玩家胜利或完整战争完成；下一步在真实日期推进后重读撤退、位置和 route，继续以当前围城实际 outcome 决策。
