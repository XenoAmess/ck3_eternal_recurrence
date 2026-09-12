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
| G2-M1 实体发现与 core turn bundle | P1-A | not started | 一次聚合查询提供人物、头衔、首都、领主/封臣、邻居与最低 ruler/realm/succession alerts |
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
主 DLL、native fixture 与 Python 正常/异常合同均 GREEN；旧 snapshot 不带字段时仍兼容。当前状态仅为
`static-ready / live=false`。下一次可用实机先读取一个 paused frame；随后 registry consumer 才能把 `.0030` 的选择前后
压力点接成同角色后置验证。若选择前压力已经为零，该次安全关闭不能计入 material-delta。详见
[`played-character-stress.md`](../ck3-native-ai/played-character-stress.md)。

战争 controller 的既有成熟执行器继续保留；assigned reinforcement、terminal 长尾与更多 CB 改为真实 encounter 驱动。
宗教域继续暂缓，只允许战争中的圣战和婚姻合法性/接受度所需的最小原生最终判定，不借此扩展通用宗教模型。

## 报告规则

- 总进度只写 `G2-Mx / 8`，当前为 `0/8`；
- 当前工作包另写 `完成子包/总子包`，当前 GEN-034 为 `2/4`；
- query/tool 数量只作 surface inventory，不得换算为玩法完成率；
- 任何 `live` 提升必须链接 paused artifact；ACK、schema、单元测试和单场 fixture 不得冒充 OODA；
- 对已取得证据的输入直接复用，新的 live 只验证本包新增的最小事实或动作后置。
