# M5 后继：已发布参与战争的事实范围

本包是[首次 M5 范围研究](g2-m5-research-2026-10-19.md)的独立后继。执行 `machine_id: xenoamess-full-tower-eb9d2c1186`，身份由 `python tools/ck3_live_run_id.py machine` 实读（`31f603`），研究观察时间 `2026-10-19T02:39:18Z` 来自时钟工具，当时 HEAD 为 `dc4b7d56787ac769c809d1ab0d7b6057be2377e6`（`a1dfaf`）。本包不触碰当前运行 COW、冻结 SDK 或 Native25；新局按既定源继续，不等待或采用本候选。

## 结论

**当前普通战术已经把已发布的非主导参战敌军纳入路线与接触风险。** 首次研究发现的是现金/采购优先范围及其摘要边界，不能扩大成“普通规划器完全漏掉宗主战争敌军”。使用现存同帧字段可以完整聚合**已发布 player-participant 战争内的已观察军队身份**，并在兵数可读时去重计数；不能由此闭合非 participant 宗主战争、未动员敌军、败战土地后果或非主导行动权限。

## 现有真实来源与消费者

| 链路 | 已有事实和边界 |
| --- | --- |
| `ck3_12004_world.cpp` → `ck3_12002_world.cpp` | exact `.4` 绑定后复用 `ReadWorldSnapshot` / `ReadActiveWars`，遍历活动战争；原生 `contains_war_participant` 判定玩家实际处于哪一方，保留主导标志、对方主将、目标、战分及双方当前军队。没有主导角色过滤。 |
| `.4 adapter` → `bridge.cpp` | `.4 ReadCk3_12004Snapshot` 仅在 `WorldReadResult::available` 时发布；partial / unavailable 使读取失败。序列化逐条保留 active wars 和敌军，不筛 primary。这里证明源码发布规则，不证明当前新局某一帧已被本包读取。 |
| `native_driver._semantic_snapshot_from_frame` → `normalize_active_wars` | 保留已发布非主导战争，规范为 `source: native`；玩家军队也会从 explicit / allied lane 合并。 |
| `army_strength_scope` → `_army_strength_cache_for_snapshot` | 原查询范围已经遍历全部参与战争，按完整 ArmyID 去重并保留 WarIDs。Driver 校验 actor、native/public frame、日期、connection、episode 以及完整 scope；不需要新增全战争兵数 RPC。缺兵数仍是 unknown。 |
| ordinary `strategy` | `route_threat_enemies` 使用 `enemy_armies_from_wars(active_wars)`，已有非主导进攻者的 exact capital hold / regroup 分支；路线和接触证明继续受原守卫约束。局部 tactical war 选择不等于全局路线风险范围。 |
| `observe_war_spending_priority_v1` → construction / strategic reserve | 主导战争敌军 union 与 protect reasons 是现有现金/采购策略范围；它不是全部参与战争敌军总量。P83 另对所有战时可选建设执行资金门。 |

源码哈希和精确读点见[本包小证据](evidence/g2-m5-participating-war-threats-2026-10-19.json)。没有读取活跃 Driver/SAVE 大体、没有调用新 RPC 或编译 Native。

## Snapshot 未暴露，不等于 Native reader 缺失

最小 active-war snapshot 没有 CB 名称、己方主将和全部政治角色。**已有 query DTO 已经暴露其中一些事实：**

- `ReadWarTerminationOptions` 对非主导 participant 也会先读取 CB 身份、双方战分与时长，再跳过仅主导可执行的 option validator。其当前帧缓存由 Driver 绑定。不能把“非主导没有谈和动作”误写为“连 CB 都无原生读器”。
- `war_occupation_targets_v1` 的查询范围只要求当前完整 WarID、暂停且玩家为实际 participant，不要求 primary；DTO 已有双方主将 ID、双方原生占领计数与具体地产状态。已有当前同帧结果应直接复用，不能为了重新取得相同字段再制造接口。
- 现有 generic `claim_cb` exit terms 是有限 slice，不能把其中双方角色/头衔效果泛化到任意 CB 或宗主战争。

仍需后续生产 consumer 补齐的是：把现存同帧 CB / occupation DTO 与当前 root 宗主链、玩家头衔身份和已审原版 CB 效果连接起来。若所需结果当前没有，保留真实缺口，不把上一帧结果补作当前，也不为了本事实投影新增查询。对 snapshot 范围外、原生未判定玩家 participant 的宗主战争，本包不能证明它们不存在或不会影响玩家；将来需要覆盖时，先定义最小来源绑定的宗主战争枚举需求，再审 exact-build 原生来源，当前未实现该能力。

## 最小纯事实候选及其独立价值

[`participating_war_threat_observation_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/participating_war_threat_observation_v1.py) 是**未接入任何生产消费者的候选**。它仅从既有暂停 snapshot 聚合：所有参与 WarIDs、primary / non-primary / leadership-unknown 分组、对立军队 ArmyID→WarIDs 关系与去重已动员兵数。缺数组、帧或身份时返回 unavailable；重复 ArmyID 的冲突人数保留 unknown；已观察空数组与缺读分别处理。它复用现有 `_count` 的当前 detached strength/fallback 语义，不授采购、移动、投降或胜率。

候选沿现有 `army_strength_scope` 的 positive int32 WarID 资格；底层 world reader / `normalize_active_wars` 则允许原始 ID 0。候选对 0 保守返回 unavailable，不宣称已有覆盖该原始边界。以后若接入，先统一这项 ID 合同并定向验证，不把保守拒绝当作没有该战争；本次没有为未采用候选扩大测试轮或修改新局。

现有 `army_strength_scope` 仍是兵数查询的唯一 scope owner，本候选不替代它、不新增第二套查询。两者用途有一项区别：查询 scope 混合 player / allied / enemy 并采用角色优先级；某军队在一场 allied、另一场 enemy 时，仅筛其最终 `scope_role` 会丢失“在任一参与战争中为对立军队”的关系。本候选保留逐战对立 membership，并在聚合层区分未知、重复冲突和已观察空值。当前路线消费者仍使用原 `enemy_armies_from_wars`，没有新增热路径工作。

如后续确需普通规划报告呈现此范围，最小替代位置是 `war_mercenary_consumer_v1.annotate_war_decision_reason_v1` 的现有 `war_decision_reason_scope_v1` 摘要：以该事实适配替换对应摘要聚合，同时继续把 primary 现金优先 scope 单列。**不应为了显示再增加并行的第三个聚合接口或把候选自动接进采购/投降。** 本包没有执行该接线；当前新局、冻结 Host 与普通 policy 返回完全不变。

## 必要离线验证与收口

定向测试仅运行本候选的 9 项，实际 `7f5568` / exit 0，`9 passed in 0.56s`。覆盖与现有 tactical enemy union 的身份等价、primary 现金策略原值保持、跨战 ArmyID 去重、当前/过期 strength、缺字段、重复身份冲突、unknown leadership、空 scope 与输入不变。首次 pytest 收集因工作区包未安装而 `ModuleNotFoundError`（`8ac6cc` / exit 2）；随后只给 runner 明确加入源码路径，没有修改生产守卫。首轮 RED 保留于证据，未重跑其他矩阵。

统一存储策略仍为 `1.0.0`，共享研究剩余额度 128 MiB。本包只有新小源码、测试、文档和 JSON，无重型写入、删除、游戏/桌面操作、Driver/SAVE 导出或 Native 构建。源验证不授部署、实机战果或新的 G2/M5 信用；Root 统一审阅和提交，本代理不 stage / commit。
