# G2 全游戏自治需求与现行施工队列

状态日期：2026-09-12（Asia/Shanghai）。机器可读权威状态为
[`g2-requirements-v1.json`](g2-requirements-v1.json)；玩法覆盖、Native/MCP 缺口与资料依据见
[`g2-ck3-gameplay-coverage-gap-research-2026-09-12.md`](g2-ck3-gameplay-coverage-gap-research-2026-09-12.md)。

## 口径纠正

G2 的终点是能够跨继承、跨玩法域持续完成“观察 → 决策 → 操作 → 验证”的 CK3 玩家智能体。历史上的 fixed-seed
`start-next-episode` 和第二寿命证明了进程接管、恢复与 episode 生命周期；它们不等于普通 campaign 的真实继承，也不等于
整套玩法覆盖。

G2 现采用固定的 **8 个可见 OODA 里程碑**，当前为 **0/8 complete**。以后只汇报 `完成里程碑/8`、当前里程碑及其子包，
不再汇报没有固定分母的“G2 90%”。旧 `T1=90%` 只曾表示 GEN-034 这个窄战争退出包接近当时定义的收口，且随着真实证据
改写了剩余输入，它已失去可比性。

| 里程碑 | 优先级 | 当前状态 | 可见验收结果 |
|---|---:|---|---|
| G2-M0 GEN-034 三路战争退出 | P0 | in progress | 同帧比较继续、白和、投降；只提交一次；验证战后并冷恢复 |
| G2-M1 实体发现与 core turn bundle | P1-A | in progress | 一次聚合查询提供人物、头衔、首都、领主/封臣、邻居与最低 ruler/realm/succession alerts |
| G2-M2 自然事件语义闭环 | P1-B | in progress | 三个自然事件按目标评分并验证结果，至少两个为多选 |
| G2-M3 继承与 realm survival | P1-C | not started | 死前预测逐头衔分配，死后对账并由真实继承人继续 |
| G2-M4 和平治理纵向切片 | P1-D | not started | 两年内完成并验证建设、内阁调整和一次封臣/派系处理 |
| G2-M5 家庭、外交与完整战争 | P2 | not started | 比较至少五个候选，执行一条从机会选择到最终后置的完整路径 |
| G2-M6 谋略、制度与活动 | P3 | not started | 谋略、囚犯/制度、非宗教决议/法律与活动各完成一个 OODA |
| G2-M7 身份适配与长期整局 | P4-P5 | not started | 跨 ruler/seed/government 资格矩阵及 checkpoint/继承后的高层目标恢复 |

只有一项 query 或一个 fixture 时，状态仍按 `research`、`static-ready`、`fixture-live`、`production-live primitive`、
`production-live loop` 与 `complete` 的既有词汇记录；它不会增加 8 项完成数。每个里程碑必须具备 `latest_evidence`、
`planner_consumer` 和 `visible_outcome`，三者由机器可读文件固定。`py tools/validate_g2_requirements.py` 校验固定 8 项分母、
当前完成数、状态词汇与 GEN-034 子包计数；需求或进度修改后必须运行一次。

## 当前 P0：GEN-034

GEN-034 当前是 **2/4 子包完成**，但已有重要前置原语：R459 已真实提交一次 surrender，证明 source-specific
`3000→0`、persisted truce expiry `53227656` 与战后生命周期；R471 已在同一 paused frame 两次读取玩家
`13075500000`、对手 `16770900000` 的 strategic power，原生 ratio 为 `128262/100000`。

现行四包为：

1. `GEN-034-A`（**complete**）：把 R471 strategic-power 原语接成 policy-level campaign dominance certificate；
2. `GEN-034-B`（**complete**）：提供有版本、来源、仓库默认值和显式 operator override 的 strategy budget/profile；
3. `GEN-034-C`：在同一 paused frame 取得 white-peace terms 与 utility comparison；
4. `GEN-034-D`：三路 recommendation → 一次 semantic action → WarID/loss/truce/resources 后置 → checkpoint/cold restore。

旧的 index `9/10`、root shape 与 Truce vtable 枚举已被后续证据淘汰。不得再以它们作为当前入口。source attribution、
pre/loss、实际 expiry 和 active-war strategic power 已有证据，不得重复跑这些已关闭的单字段场景。

`GEN-034-B` 已由 `strategies/raiktor_exit_budget_v1.json` 与通用 provider/CLI 闭合：仓库默认 profile 为 `1.0.0`，完整
operator override 必须绑定默认 profile ID/version，实际输入按源文件 SHA-256 绑定。GREEN 离线收据为
`Z:\ck3_mod_rewrite\_runtime\g2-gen034-strategy-profile-20260912\repository-default-profile.json`，SHA-256
`BB20D87233DF6C854DD668FD1641AE590DFFA3BD87CF82099A1A97EBF20C7981`；它只提供策略参数，不提供 campaign 或 white-peace
观测，也不授权 action。

`GEN-034-A` 已由 `raiktor_campaign_dominance_provider.py` 和 hash-bound CLI 闭合。R471 receipt 为
`Z:\ck3_mod_rewrite\_runtime\g2-gen034-a-campaign-dominance-20260912\r471-certificate.json`，SHA-256
`AB0DB5678F65631D63E5A54BA66B61A6F5956179C0A4D3970B78BEAC5E9E0569`。它只发布实测兵力关系；campaign forecast、exit utility、
recommendation 与 action 均保持关闭。`GEN-034-C/D` 需要 CK3 时必须服从 T0 资源让位和单实例轮次规则。
下一次 live 只允许一个有界 paused 场景，完成同帧 white-peace comparison；若输入齐全则在同一受管会话继续唯一 action 与
postwar 验证。单字段修复只跑聚焦测试和这一个场景，不扩成永久长跑。

## GEN-034 后的固定顺序

GEN-034 关闭后立即转向公共 P1，不再继续横向扩展单一 CB 的 ABI：

1. `entity-directory-v1` 与 `ck3_query_turn_bundle_v1` 的 current-feudal-ruler 最小切片；
2. `event-context-v2` 与 registry-driven natural event policy；
3. `succession-state-v1`、health/stress/legitimacy 与 vassal/faction alert 组成的 realm survival；
4. 建设、内阁与派系处理组成的和平治理 OODA。

G2-M1 的前两个 native 子包已达到 `static-ready / live=false`：既有 `campaign-root-context-v1` 现在在同一 paused
application-main 双采样中发布 `direct_landed_vassal_character_ids` 和
`adjacent_external_province_holder_character_ids`。前者枚举 alive、landed 且 immediate liege 为玩家的完整 generation
CharacterID；后者从 exact Province array/native holder/adjacency rows 出发，以“immediate-liege 链是否到达玩家”区分玩家子领地，
再发布边界外直接相邻 Province holder 的升序去重 ID。两项都不借用离线 save topology；Release DLL、native
reader/source-contract 与 Python normal/optimized 聚焦测试均 GREEN。

其上的 canonical relationship-search 切片也已达到 `static-ready / live=false`。独立只读 MCP 工具
`ck3_search_entities_v1` 只消费一次现有 campaign-root query，以 relation filter 和 keyset pagination 返回 self、直属有地封臣和
相邻外部 Province holder 的稳定 CharacterID。新增 `related_character_contexts` 在同一双采样中逐 ID 发布 native primary title、
合法可空 capital、immediate/top liege 与 independent；相邻 holder 保留 source role，再按 top liege 归一 realm identity。
entity-directory 的当前 title/realm components 因而已完整。`ck3_query_turn_bundle_v1` 已聚合最低 ruler/realm/succession alerts、
玩家完整月收入和 exact-build domain size/limit，`ruler_resources_ready` 与 `realm_domain_ready` 都可由真实输入变绿。M1 仍缺
health、council、faction、partition 与共享 live 验收，固定 G2 完成数仍是 `0/8`。下一次允许实机时只在本来就需要的 paused G2
会话顺带读取两个非空 vector、related contexts、income 和 domain capacity 并验证 directory/bundle，不为单字段安排长跑。

## G2-M2 离线 direct-projection consumer

机器由人工占用、禁止启动 CK3 期间，M2 的非冲突静态子包已先行完成。`vanilla_events/policy.py` 现在把 shared
exact-build registry 接入 `one-life-turn-v1`：当同帧 event key、玩家 root、saved scopes、snapshot/rendered option count、
native index 与 enabled 投影全部匹配时，planner 采用登记的 source-reviewed bounded continuation。当前真实阻点
`tgp_travel_events.0030` 因此会选择 authored 2/native 1，而不再被通用最小索引 fallback 导向随机学习对决。

已登记 key 若投影漂移、目标选项 disabled，或合同需要尚未实现的人物关系、scope/option variant、动态 native prefix、occurrence 上限、延后选择或场景失效
语义，planner 返回 `active_event_registry_contract_blocked` 并保持不输入；未知 key 才继续旧 degraded fallback。该子包为
`static-ready / live=false`，普通与 optimized 聚焦测试各 `30/30` GREEN。它没有改变 current-window、registry 或 MCP 公共 schema，
也没有提升固定 `0/8` 完成数。M2 仍需 variant-aware consumer、event-context-v2 结构化效果、campaign objective 评分，以及三个
自然事件（至少两个多选）的动作与物质状态后置实机证据。

为关闭其中一个真实后置缺口，通用 native state snapshot 已在 `played_character` 上增加可选 `stress_points`。它复用
战争退出资源读取器已使用的 exact-build `CCharacter+0x1A8 -> extension+0x2F8` 路径，不新建另一套 mailbox/MCP。
主 DLL、native fixture 与 Python 正常/异常合同均 GREEN；旧 snapshot 不带字段时仍兼容。registry consumer 现在仅对
`.0030` authored option 2/native 1 绑定同帧角色、snapshot/revision 和选择前压力。native action 复用已经捕获的前后 paused
snapshot，service 输出 `verified_change`、`verified_no_change`、`failed` 或 `unavailable`；压力上升、角色漂移或 ready 合同缺少
动作后读数都会让 auto-run 保持 RED。若选择前压力已经为零，该次安全关闭不会计入 material-delta。

该链仍为 `static-ready / live=false`。下一次允许实机时只需一次有界 `.0030` 复核，同时完成字段 paused read 与 comparator
production proof，不为单事件扩成长跑矩阵。详见
[`played-character-stress.md`](../ck3-native-ai/played-character-stress.md)。

首个 option-variant consumer 也已按真实 R374 阻点收口。`natural_disaster.7031` 的 exact source 和冻结 live frame 证明 native 2
在单选 `[2]`、实际 R374 的 `[0,2]` 与完整 `[0,1,2]` 三种投影中都存在，且只显示 warning tooltip。policy 现在先把当前
option projection 精确匹配到登记 variant，再进入既有 scope/enable 检查；`[0,1]` 等未登记投影继续 blocked。准入目前只限该
event key，其他带 `option_variants` 的合同仍返回 `registered_contract_requires_extended_consumer`，避免一次静态改动暗中扩大事件面。
聚焦测试 normal/optimized 各 `8/8` GREEN；状态为 `static-ready / live=false`。

两条已进入 planner 的选择现在还带有机器可读的 `xar.ck3.vanilla-event-choice-effect` 档案。`.0030` 记录 authored
`medium_stress_impact_loss = -30`，同时明确 `runtime_delta_exact=false`，因为人物压力影响修正尚未观测；其 comparator 从同一档案读取
`played_character.stress_points / non_increasing`，不再另写一份效果假设。`natural_disaster.7031` 则区分 selected native 2 的纯
warning tooltip 与所有选项之后必经的 character variable 写入，并把后者标为当前不可观测。两条档案都由既有只读
`ck3_query_vanilla_event_knowledge_v1.analysis` 对外查询，policy 只在 exact native choice 对齐时返回副本。

这项能力是 `source-structured / static-ready / live=false`，只覆盖两条 exact source-reviewed 选择；它没有实现通用
`event-context-v2` effect visitor，也没有把未观测的 runtime magnitude 或 common-after variable 冒充为 live 后置证据。普通与
optimized 聚焦测试各 `27/27` GREEN。

第二条 material comparator 现覆盖 R414 的 `trait_specific.8001`。authored option 2/native 1 的 effect profile 记录
`add_gold = minor_gold_value`，但由于原版动态值依赖月收入、treasury 与 era，只承诺 Q100000
`played_character_gold.raw / strictly_increasing`，不预报精确 delta。native state snapshot 复用既有 exact-build
`extension+0x100` 金币 leaf；planner、action 与 service 绑定同一 CharacterID 和选择前 snapshot/revision，只有动作后 raw 严格增加
才算 material change。不变、下降、身份漂移或缺读数保持失败/不可用。

主 DLL 与 native fixture GREEN，Python normal/optimized 聚焦测试各 `30/30` GREEN；状态仍为 `static-ready / live=false`。
`.0030` 与 `.8001` 各只待一次 bounded live action 证明，不为任一单事件启动长跑。连同下述第三条静态路径，G2-M2 仍需
campaign objective 评分与三个 production event loops，固定总进度保持 `0/8`。详见
[`played-character-gold.md`](../ck3-native-ai/played-character-gold.md)。

第三条静态 material path 现选定已有真实证据的 `death_management.1007`。R374 已证明唯一 authored1/native0 的 event instance
advance；本包为该 key 精确消费 distinct `dead_character` scope，发布 authored `minor_stress_impact_gain = +20` 档案，并复用
玩家压力字段验证 `non_decreasing`。正向 delta 才计 material evidence；压力封顶导致的不变被记录为非 material，反向下降或身份漂移
不能通过。其它 unique-exclude 合同仍 blocked。

该 comparator 为 `static-ready / live=false`。R374 的旧 hot park 没有 durable checkpoint，不能冒充可冷恢复输入；今后只在正常
campaign 自然再遇时顺手做一次 bounded 前后对账，不为 `.1007` 单独长跑。至此三个目标事件均已有静态 material comparator，但
三条 production material loops 与跨事件 campaign objective 评分仍未闭合，所以 G2-M2 继续 in progress、总进度仍为 `0/8`。
详见 [`heir-death-stress.md`](../ck3-native-ai/heir-death-stress.md)。

三个目标事件的 bounded campaign objective/utility 输入也已 static-ready。每个 analysis record 现发布 versioned ordinal profile；
policy 只在 exact native choice 对齐时复制，`one-life-turn-v1` 把它写入 `event_campaign_utility`。`.0030` 以“减压且不延误旅程”
为目标，`.8001` 以“增加流动金币且不引入随机持久状态”为目标，两者都将 native1 排为当前首选；`.1007` 则诚实记录唯一合法路线
及其不可避免的压力成本。planner 因此不再只写“bounded continuation”，而是保存 objective、selected rank、utility 特征和替代原因。

该评分为 source-reviewed ordinal，不是跨域数值模型：`cross_event_numeric_score=null`、`calibration_status=not_calibrated`、
`semantic_optimal=false`。它关闭三个 exact 事件的最小静态“目标和 utility”输入；实时压力/财政/继承风险驱动的动态目标切换、通用
event-context-v2 effect visitor 与更多事件仍是扩展债，不再作为这三个事件 live loop 的前置。聚焦测试 normal/optimized 各
`26/26` GREEN，详见 [`event-campaign-utility.md`](../ck3-native-ai/event-campaign-utility.md)。

战争 controller 的既有成熟执行器继续保留；assigned reinforcement、terminal 长尾与更多 CB 改为真实 encounter 驱动。
宗教域继续暂缓，只允许战争中的圣战和婚姻合法性/接受度所需的最小原生最终判定，不借此扩展通用宗教模型。

## 报告规则

- 总进度只写 `G2-Mx / 8`，当前为 `0/8`；
- 当前工作包另写 `完成子包/总子包`，当前 GEN-034 为 `2/4`；
- query/tool 数量只作 surface inventory，不得换算为玩法完成率；
- 任何 `live` 提升必须链接 paused artifact；ACK、schema、单元测试和单场 fixture 不得冒充 OODA；
- 对已取得证据的输入直接复用，新的 live 只验证本包新增的最小事实或动作后置。

## G2-M1 目标派系最低告警

原版 `has_targeting_faction` trigger 已按 CK3 1.19.0.6 exact build 冻结：注册链最终进入
`0x283FAE0..0x283FB51` evaluator，其语义为解析完整 generation 的玩家 Character，读取
`CCharacter+0x1B8` land state，并以 `land_state+0x12C` 的非零有符号计数判断是否存在以玩家为目标的派系。

现有 `campaign-root-context-v1` 在同一双采样内发布非负 `player_targeting_faction_count`；身份、指针、计数或两次采样漂移时，
整帧以 `player_targeting_factions_unavailable` 失败。`ck3_query_turn_bundle_v1` 将它投影为
`realm.targeting_factions.{count,threatened}`、`alerts.faction_threat` 和 `realm_faction_alert_ready=true`。
该切片只关闭“是否已被派系针对”的最低告警，不宣称已经观测派系身份、类型、成员、军力、不满度、诉求或最后期限。

状态为 `static-ready / live=false`。MSVC Release reader/source-contract fixtures 为 GREEN，Python campaign-root、live-harness 与
turn-bundle 聚焦测试在普通及 optimized 模式均为 `40/40`。它将与已经待验的 related contexts、收入和 domain capacity 共用
一次有界 paused R558 读取；不为该单字段扩成长跑。G2-M1 仍缺 health、council、partition 及两场景 live 验收，G2 总完成数保持
`0/8`。
