# CK3 自动游玩智能体：终极目标、当前能力与完整路线图

## 终极目标

构建一整套能够高智商游玩 CK3 的玩家智能体。它必须在 exact-build 原生桥之上长期、无人接管地反复完成：

```mermaid
flowchart LR
    O["观察：typed world state"] --> D["决策：候选、效用与长期目标"]
    D --> A["操作：generation-bound semantic action"]
    A --> V["验证：下一 paused frame / 后置状态"]
    V --> M["记忆：checkpoint、结果与校准"]
    M --> O
```

最终智能体不是固定开局脚本，也不是若干命令的集合。它应覆盖当前 playset 中玩家可执行的全部主要玩法能力，能够处理
中断、并发目标、资源预算和不确定性；从开局选择开始，跨和平、战争、事件、家庭、统治与继承，完成自然统治者生命周期，
并在普通 campaign 模式跨继承继续。

## 冻结边界与本页口径

- 当前 exact build：CK3 `1.19.0.6`。
- `ck3.exe` SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 本页盘点日期：2026-08-27；实现与验收合同盘点基线：聚合 runtime `5c85824`。
- 能力明细以
  [`autonomous-capability-roadmap.md`](../ck3-native-ai/autonomous-capability-roadmap.md) 为施工账本，
  以 [`docs/ck3-native-ai/README.md`](../ck3-native-ai/README.md) 为原生 AI 证据索引。
- 本页只汇总已经有证据支持的状态。`static-ready`、`fixture-live`、`production-live primitive` 与
  `production-live loop` 不互相混写。

一个玩法域只有同时具备以下五层，才可以标为 `complete`：

1. 冻结 exact build 并梳理原生 AI 决策树，证据正文与 Mermaid 分支同步；
2. 决策输入由 typed native observation 提供，并在 paused production frame 验证 identity、generation 与真实值；
3. 操作使用有前置验证的 semantic command，并以新状态而非 ACK 判断成功；
4. planner 能比较多个合法候选，结合长期目标、机会成本、风险与不确定性；
5. production 实机完成完整 OODA，持续域还要通过 checkpoint 冷恢复与重复长跑。

截至本页盘点，没有理由宣称“全游戏自治”或“高智商 CK3 智能体”已经完成。

## 2026-W35 最高优先级：先完整游玩一代人

所有者在 2026-08-27 09:47（Asia/Shanghai）明确把本周最高目标改为：**Agent 作为玩家，无人接管地完整游玩一局 CK3
的一代人过程**。本周 stage 的最低验收定义是：

1. 从一个固定、可复现的 production map-ready seed 和存活玩家角色开始；
2. 由 Agent 自己反复执行观察、决策、原生动作和后置验证，人工不代为点击游戏内容；
3. 事件、通知、人物互动、战争、暂停/推进与 checkpoint 恢复不能永久卡住主循环；
4. 持续运行到该玩家角色死亡，并读取、处理和保存一代结算结果；
5. runner 保存全程动作/结果与能力债，进程和临时现场可回收，失败时能指出第一个真实 blocker。

这一 stage 不要求所有策略已是最优，也不要求一次覆盖所有政府、DLC、战争类型或 ruler。输入不完整时允许使用明确标记的
`degraded heuristic` 让合法游戏继续，并把缺失观测、选择理由与实际后置结果记账；不得用命令 ACK 冒充成功，也不得用人工
操作跨过 blocker。当前账本见 [`one-generation-blocker-ledger.md`](one-generation-blocker-ledger.md)。首次一代 GREEN 后，
再用重复 run、更多 seed 与原生决策树逐步替换这些降级策略。

normal-desktop 启动合同与历史双 profile handoff 见
[`one-generation-canary-handoff.md`](one-generation-canary-handoff.md)。当前 `xenoa / WinSta0\\Default` 已连续完成 strict runner、窄
`claim_cb` 白和、`pay_ransom` 回复、`NO_DECLARE` 续跑与 checkpoint 冷恢复，旧 sandbox desktop 不再是当前 blocker。最新 run
`20260827T074858Z-one-generation-0e20ca35` 从 `date_raw=53178504` 推进至 `53179800`，完成 `100/100` turns、`49` visible
gameplay turns 与 `5` durable checkpoints；最终 CharacterID `29829` 仍存活，因人工 turn bound 正确输出 `bounded_incomplete`。
report SHA-256 为 `784B6D17AC7F6C220C5E234914E03FA2539CD801E29FAC4F5C2ED4A91D8E827C`，最终 checkpoint SHA-256 为
`71F23BB9F735AE118E4580AE62A9B3CE4C22AEB2AF22A91447A0484FCE38C1BF`。这证明 runner 已 production-live 且可恢复，仍绝不冒充 G1。

原生 AI 研究前置保持不变：遇到相关玩法，先冻结并落盘 exact-build 原版决策树、输入和 unknown 分支；完成这一步后，我方不必立刻复制
整棵树，可以选择足以继续游戏的最小实现。原生树中尚未采用的输入/分支必须作为可追踪能力债记录，后续以 production outcome
决定替换和校准顺序。

## 已经完成或真实可用的能力

下表列的是已闭合的基础或窄里程碑，不把部分闭环扩义成整个玩法域完成。

| 能力 | 当前证据等级 | 已经能做什么 | 仍不能据此声称什么 |
|---|---|---|---|
| exact-build 会话与时间 | `production-live primitive` | 识别地图就绪、玩家与日期；暂停、速度和有界时间推进；最小化窗口运行。 | 不代表会选择长期目标。 |
| checkpoint / 冷恢复 / 进程回收 | `production-live loop` | 保存、冷恢复、校验日期/角色/history anchor，并维持 managed cleanup。 | 不代表恢复后所有高层 intent 已重建。 |
| 既有战争的基础移动与围城 | `production-live loop`（部分场景） | 集结、路线 preview、移动、split/merge 恢复、目标/围城观察及一日节拍控制。 | 不代表任意战争都能自主打到终局，也不包含完整补给、海运或多军团调度。 |
| route-contact 与实际接敌 identity | `production-live loop`（create-new） | 预测接触日，读取真实 CombatID、Province 和双方 stored order；战中 checkpoint 冷恢复后可复查。 | `join_existing`、多个 compatible combats 和通用接战策略仍未闭合。 |
| ongoing battle observation / hold | `production-live loop` | 读取 phase/day、双方军队、current/soft/hard ledger，并做 bounded one-day hold 后同 CombatID 复查。 | 还没有校准胜率或 Monte Carlo 决策。 |
| active retreat | `production-live loop`（full-side 与 owner-subset） | 读取 day-15 legality，绑定目标路线 token，执行玩家军队撤退并验证旧 CombatID/双方后置状态。 | 不代表已闭合原生 AI 的通用撤退目的地评分或所有战斗策略。 |
| reinforcement assignment observation | `production-live primitive` | 读取 asking、AI parent stored order、route 和 active CombatID；见过 owner-subset 后 membership reopen。 | assigned+aligned ETA、真实 join 和改派动作仍未完成。 |
| battle terminal | `production-live primitive/loop`（normal 分支） | 通过 journals/query 识别 normal terminal、旧 CombatID 删除、战分和玩家 retreat。 | no-normal、residual、assignment-reopened 分支尚未 live，aggregate readiness 仍为 false。 |
| 窄 `claim_cb` white-peace termination | `production-live loop` | 当前 primary-attacker 场景已按 options → v1 claim terms → literal offer 提交，AI 异步响应后旧 WarID 消失；残军解散、即时 checkpoint、冷恢复与继续推进均已实走。 | 不是完整 v2/campaign 战争退出；其它 CB/角色、holy war、surrender、victory/defeat 与完整 outcome utility 仍未闭合。 |
| pending character interaction | typed query `production-live primitive`；`pay_ransom` degraded reply `production-live loop` | 读取 stable kind、五 roles、routing、deadline、send options 与四路 legality；exact `pay_ransom_interaction` 已完成 typed query→reject→旧 full ID 消失→时间推进/checkpoint，100% enforce-demands 始终优先。 | reject-first 不是赎金语义最优或原生等价；`spar`/unique-accept、其它 stock definition、intermediary/notification live 与 structured terms/effects 仍缺。 |
| auto-accept notification ACK | `fixture-live` | 非宗教 definition-only fixture 中完成 query/query/ACK/旧 full ID 消失。 | 不是 stock/production-only 语义证据，自然 stock 与 intermediary 仍待验。 |
| campaign root 与 loaded feature manifest | `production-live primitive` | 读取玩家主头衔/tier、capital、liege、government/rules，以及当前进程 feature registry/runtime keys。 | 开局选择、全部政府/DLC 场景和 entitlement provenance 尚未完成。 |
| 婚姻关系与最小候选动作 | `implemented`，部分结果 live | 读取配偶/婚约关系，枚举合法 CharacterID 候选并提交、等待关系结果。 | 当前仍可能选择首个候选，不是智能婚姻策略。 |
| 一代结算 | `production-live primitive` | 读取死亡结算 snapshot、分数/纪录/契约进度并可从 immutable seed 开新 episode。 | 自然死亡完整 episode 与普通 campaign 跨继承仍未完成。 |
| 一代人严格 runner | `production-live loop` | 复用纯原生 owner，从归档的 exact cold seed 持续 OODA；最新正常桌面 run 完成 `100/100` turns、`49` gameplay 与 `5` durable checkpoints，并在 cleanup 后留下可冷恢复的 `53179800` anchor。 | CharacterID `29829` 仍存活，未生成 terminal settlement；人工 bound 只算 `bounded_incomplete`，G1 仍未取得。 |

已有 managed war run 的已记录量化里程碑为 `210/210` 成功回合、78 个可见 gameplay 回合和 75 个游戏日；这是既有战争
checkpoint 的稳定性证据，不是全游戏覆盖率。

最新 strict one-generation continuation 的量化里程碑为 `100/100` 成功回合、49 个可见 gameplay 回合、5 个 durable checkpoints，
`date_raw 53178504→53179800`；cleanup 全绿但角色仍存活，因此它只提升 runner/readiness 证据，不提升 G1。

production6b 还带有一个明确的 G2 债务：`episode-seed.json` 指向另一 state，而复制体内没有配套
`xar_episode_seed.ck3`。它不影响当前固定 checkpoint 的单寿命 G1 canary/死亡结算，但会阻塞之后的
`start-next-episode`；跨代前必须复制并验证真实 seed，或明确清理旧 metadata 后重新建立，不能声称 strict wrapper 已自动重绑。

## 当前事件能力的精确状态

事件会中断几乎所有长期循环，因此当前优先闭合 `current-event-window-context-v1`：

- 生产实现已经静态发布 canonical event key、process-local calculated ID/runtime ordinal、实际物化的 shown/enabled/name/reason、
  authored native index、fallback/cancel，以及有损的 played-character trait/stress/death/scheme/unknown indicator 子集。
- `CEventWindowData+0x2C` 已纠正为 timeout index；cancel 从 authored `CEventOption+0x47A` 逐项读取，允许多个 cancel。
- indicator 空 rows 只表示该有损 GUI 子集为空，不能推导“选项没有效果”。resource/relationship delta、scope identity、完整性信号和
  full effect preview 仍 unavailable。
- Attempt1 是路径 harness RED；Attempt2 是旧 cancel ABI capability RED；Attempt3 已证明 cancel/空 indicators/readiness 在 seed 与
  cold 都正确，但因 runner 把 process-local 两个数值误当跨进程 identity 而保持 immutable RED。
- 2026-08-27 的修正合同 Attempt4 已整体 GREEN：seed PID `22976` 与 fresh-cold PID `43140` 跨 checkpoint 保持
  full instance `17`、canonical key 和三条 materialized option 一致，native index `3` 真实 `cancel=true`，cold 双查询严格
  相等。artifact SHA-256 为 `690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B`。
- 因此 current-window read-only query、definition identity、presentation/cancel 与 empty-indicator surface 升级为
  `fixture-live`。后继非空 fixture 又实读了 `trait/add brave`、`stress/increase`（`affected=false`、
  `critical=false`）与 `death/played_character` backing rows。`readiness.semantic_decision_ready` 仍为 false；stock
  events、其余 indicator 分支与视觉图标、selection lifecycle、scopes 与完整 effects 仍未完成。

## 还没有完成的主要能力

以下能力不能由现有窄接口代替：完整事件效果与多选语义；通用经济/domain/building；council/lifestyle；军备、补给、损耗、
海运与 raid；智能宣战、盟友与多战争；婚姻/教育/继承/王朝；外交、封臣、契约与派系；谋略、秘密与 hooks；囚犯、犯罪与
tyranny；健康、压力与生育；法律、政府、文化、创新与非宗教决议；活动、旅行、宫廷、宝物、勋号及各 enabled DLC/government；
通用世界发现；跨域长期目标、预算、学习与跨继承记忆。

视觉 fallback 中已有的经济、内阁、婚姻、继承和巴勒莫战争流程主要绑定 1066 罗贝尔固定场景，只能保留为 regression fixture，
不能记为通用能力。

## 全部后续工作

下面是完整工作包；每一包都按“原生 AI 树 → typed observation → semantic action → planner policy → production OODA”施工。

### F0：通用发现、开局与 feature manifest

- 枚举 bookmark、ruler、game rules、难度、政府与 enabled features，进入地图后验证实际设置。
- 扩展通用 character/title/province/realm 搜索与关系图，避免各剧本重复发明发现逻辑。
- 补非 duchy、非 feudal、landless、legal-absent、installed-but-disabled/offline-store/cold-restore 矩阵。

### P1：真实战斗 controller 收口

- 完成 `join_existing`、multiple-compatible combat、动态 join/leave 与同日顺序。
- 构造三同侧 CUnit fixture，闭合 assigned reinforcement、aligned ETA、真实 join、改派与后置验证。
- 覆盖 no-normal、same-Province residual、assignment-reopened/AI re-entry terminal。
- 闭合 loaded phase-event/effect feedback/original trace，输出有校准边界的胜率与损失分布。
- 让 planner 比较接战、绕行、等援、撤退和牺牲阻滞，并与真实结果对账。

### P2：从既有战争打到合法终局

- 补 score breakdown/ticking、occupation、participants、盟友 ETA、财政 runway、补给/损耗、完整 objective 与 exit terms。
- GEN-004 的最窄 `claim_cb` white-peace 已在 normal desktop 完成 final response、options → v1 terms → offer、AI 异步应用、
  WarID 消失、残军解散、保存与冷恢复；继续以 production outcome 扩其它 CB/角色及未采用的 v2/campaign 输入。
- 实机验收 raise、assault start/stop、disband、enforce；继续扩展其它 CB 的 white peace 与独立 surrender surface。
- 增加 call ally、rally、embark、reassignment、mercenary 等动作和后置状态。
- 从 active-war checkpoint 无人工输入走到 victory/white peace/surrender，处理战后、保存并冷恢复。

### P3：事件、通知与人物互动语义

- Attempt4 已闭合 current-window identity/presentation/empty-indicator transport；继续补 stable root/saved scope identity、
  resource/relationship/health/character/title/war delta 与 completeness。
- 发布足以区分长期后果的 structured effect/terms，并把原生 AI raw weight 仅作为先验，不冒充玩家效用。
- 覆盖多页事件、letter、toast、普通请求、auto-accept、intermediary 与 deadline。
- planner 对多个合法选项按长期目标评分；production 长跑连续处理至少 50 个不同 key，零固定首项、零默认接受。

### P4：和平期经济、domain、council 与军备

- 建立 economy/building、council/development、military-preparation 原生 AI 树。
- 读取资源及收支、holdings/buildings/construction、control/development、council/tasks、MAA/levy/knights/commanders/mercenaries。
- 实现建设、council、lifestyle/perk、MAA、knight/commander 与雇佣兵动作。
- 完成至少十年生产自治，并用积累的军备完成一战。

### P5：智能宣战、联盟与多战争

- 完整比较所有合法 CB、目标 title 价值、成本、双方 reserve、盟友接受/ETA、其它战争、truce、faction 与 succession 风险。
- 实现 declare、call/join/offer war 及可验证 participant 后置状态。
- planner 能在至少五个候选中选择目标/CB，也能选择“现在不打”，并处理进攻、防御、盟友与同时两战。
- 圣战/大圣战只读取战争 OODA 必需的原生合法性、目标、费用、参战与结束结果；faith 保持 opaque/minimal。

### P6：家庭、婚姻、教育、继承与王朝

- 梳理婚姻/联盟、教育/guardian、继承/title planning 原生树。
- 读取家族、继承序列、titles/laws/claims、年龄、属性、traits、health/fertility、联盟价值、接受度与 partition 风险。
- 实现婚姻、教育、title grant/create/destroy/usurp、继承修复和合法的 dynasty 资源动作。
- 让婚姻从“首个合法 ID”升级为联合评分，并验证死亡后的 title distribution；普通 campaign 跨继承继续。
- 只有婚姻合法性、接受度、费用或结果确实依赖信仰时，调用最小原生最终判定/原因。

### P7：外交、封臣、契约、派系与叛乱

- 读取 opinion breakdown、relations、alliances、truce、hooks、vassal contracts、faction power/discontent 与 realm stability。
- 实现 gift/sway/befriend、contract、grant/revoke/transfer、council appeasement 与 faction response。
- 对真实强派系比较让步、分化、结盟、威慑和镇压，验证意见、财政与权力后置状态。

### P8：谋略、秘密、囚犯、犯罪、健康与压力

- 建立 scheme/secret、prisoner/crime、health/stress 原生 AI 树。
- 读取 scheme progress/secrecy/agents、hooks/secrets、crime/tyranny、prisoners/ransom、disease/stress/death risk。
- 实现 scheme、blackmail/expose、imprison/release/ransom/punish、physician/treatment/stress decisions。
- 完成 hostile/personal scheme、囚犯处置和疾病/高压力三类 production OODA。

### P9：法律、政府、文化、创新与非宗教决议

- 建立 laws/government、culture/innovations、decisions 原生树。
- 读取 authority/laws/succession law、culture/traditions/acceptance、innovations 和非宗教 decision eligibility/cost/effect。
- 实现 law/authority、culture/fascination 与非宗教 major decision，并跨年验证长期效果。
- 通用 faith/doctrine/tenet/fervor、改宗、宗教改革及 holy order 继续 owner-deferred，不计完成。

### P10：活动、旅行、宫廷、宝物、勋号与 DLC/government packs

- 按 loaded feature manifest 分别施工 activities/travel、royal court/artifacts、accolades，以及 administrative、clan、tribal、
  nomad、landless/adventurer、regency/diarchy、plague、legend 等当前启用系统。
- 每个 enabled feature 至少完成一个 production OODA；未启用项明确记为 `not_present`，既不算失败也不算支持。

### P11：长期世界模型、目标调度与整局验收

- 建立 canonical world state、变化历史、预算、deadline、多目标依赖和 outcome calibration。
- 统一 semantic action registry；checkpoint 后重建 intent，避免重复不可逆动作。
- 实现生存/继承、战争/稳定、经济增长、王朝/制度的层次化规划及反事实比较。
- 完成整局矩阵：自然一代结算、普通 campaign 跨继承、伯爵/公爵/国王、进攻/防御/内战/盟友战争、十年和平后战争、
  至少两种政府、全部 enabled feature 代表场景，以及冷恢复后继续相同高层计划。

## 当前执行顺序

截至 2026-08-27，最近的施工队列是：

1. 从 `date_raw=53179800` 的 durable checkpoint 冷恢复，以 `50000 / 604800 / 300 / 3` bounds 继续同一 CharacterID `29829`
   的全寿命 strict run；
2. 若仅耗尽 turn/wall bound 且 checkpoint/cleanup 全绿，直接从最新恢复点续跑；若出现真实 B0/B1，保留 artifact，先更新对应
   exact-build 原生树，再做最小合法 blocker-removal；
3. 直到生成匹配本 episode 的自然死亡 `terminal-settlement.json`，并确认 `death-terminal` 已等到琉焰卿 Mod 发布
   `ready=true`、`commit_serial=1`、source CharacterID 匹配的 committed settlement；该文件
   `one_life_settlement.final_score` 是权威“人生分数”，必须与顶层 `score`、`recorded_episode.score` 完全一致，且必要 record
   persistence、零继承人 gameplay 与 cleanup 全部 GREEN，才标记 G1；
4. G1 后处理 `GEN-009` episode seed 债务并重复一轮取得 G2；
5. 完整 effects、reinforcement/join、terminal 剩余分支、forecast、智能宣战及 P4–P10 通用玩法域若未成为真实 blocker，继续按
   B2/B3 账本排序，不抢占首次 G1。

真实 run 出现更高优先级的观测阻点时，可以调整相邻工作包，但不得通过重复返回 `unknown/unavailable` 代替补观测口。

## 宗教域暂缓边界

在项目所有者明确通知“可以开始宗教相关内容”之前：

- 不深入研究或实现通用 faith/doctrine/tenet/fervor、改宗、宗教改革、宗教专用 AI、bridge、策略或实机矩阵；
- holy order 继续暂缓；
- 只允许两项窄例外：完整战争 OODA 所必需的圣战/大圣战输入与动作；婚姻确实依赖信仰时的最小原生判定；
- 两类例外优先消费原生最终 legality/acceptance/result/reason，faith/religion 只保留 opaque identity 或直接必要输入；
- 暂缓不等于完成。解除暂缓后，通用宗教域仍须补齐五层完成门与整局矩阵。
