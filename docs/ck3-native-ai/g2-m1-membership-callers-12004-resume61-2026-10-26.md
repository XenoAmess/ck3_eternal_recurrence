# M1：派系成员变化、拒绝君主要求与实际调用者

`machine_id: xenoamess-full-tower-eb9d2c1186`；本轮源审观察于 `2026-10-25T21:37:39Z`，北京时间 2026-10-26。研究目标沿用既有 CK3 1.20.0.4 / build25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，这不是重新核验安装、运行 EXE 或 Loaded 状态。十二份本机原版目录文件已逐份指纹核对；原件路径、SHA、精确阅读范围、边和未闭案例保存在 [本轮 plan](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m1_research/membership88/plan.json)。本轮不改策略、不调用游戏，不重做 Gift86 的修正类型与账本语义。

**当前成员读回、AI 是否愿意入派系，以及哪些角色在拒绝君主要求后直接参加叛乱，是三个输入合同。** `vassal_would_join_rebel_faction_*` 虽然带 faction 名称，所核实际消费者调用 `add_attacker`，不能把它当作普通派系成员表的生产者。

| 路径 | 候选来源与过滤 | 实际消费者与边界 |
| --- | --- | --- |
| 普通原生 AI | `.info` 规定 `ai_join_score` 的 root 为候选角色、scope:faction 为既有派系，另由代码加入 Boldness/Dread、Energy、Rationality；候选枚举、索引、缓存及重算入口本轮未定位 | AI defines 的加入/退出阈值只描述配置；没有 exact .4 caller，不能给实际退派系日期 |
| 玩家 GUI | `FactionsWindow.GetJoinableFactions` 发布列表；Join 按钮另验 `FactionItem.CanJoinFaction`，Leave 另验 `IsPlayerMember` 和 `CanLeaveFaction` | 按钮调用 `JoinFaction` / `LeaveFaction`；本轮没有迁移其 native 方法体，也没有证明与 AI 枚举同路 |
| Befriend 普通成功 | `befriend_success.random_events` 列 `.2006`，定义权重 20；事件要求 AI target、target 的直接 liege 是 owner、双方均不旅行、owner 的 targeting faction 中包含 target | immediate 保存一份仍匹配的 faction；**选项**调用 leave + cooldown；不是任何好感变化都执行此效果 |
| Befriend 严重成功 | `befriend_critical_success.random_events` 列 `.6006`，权重 20；同样要求 AI target/direct liege/不旅行，并且 target 是某 targeting faction 的 leader | immediate 保存匹配 faction；选项通知其中的人类成员，然后 `destroy_faction`；不是 `.2006` 的简单别名 |
| 逮捕失败后的拒命战争 | 见下文真实 effect 链；候选从当前 liege 的 `every_vassal` 开始 | 构造 effect-scope `joining_vassals`，再往指定 `refused_liege_demand_war` 加 attacker，不先走普通 `ai_join_score` |
| 我方 bridge | 当前已选 Faction 查询读取同帧 targeting rows、leader/member、压力与 at-war；普通 Realm 读取同帧当前县成员集 | 它们不是 NPC AI 的候选生成器或调度器；前后成员差分本身不提供原因或赠礼归因 |

## 明确改变成员的事件分支

当前 `common/schemes/scheme_types/befriend_scheme.txt` 的 `on_phase_completed` 保存 scheme/target/owner，再触发 hidden `.0001`。`.0001:162–206` 对 AI target 按 friends/potential flag 分别调用 critical-success/success；人类 target 另收选择事件。outcome 文件旧注释写 `on_ready`，不能据此覆盖当前实际 scheme callback 或推测执行时刻。

`common/on_action/schemes/befriend_on_actions.txt:158–187` 将 leader/member 两种结果放在不同 outcome 表。权重 20 不是“20%”，也不是必出的成功结果；本轮未重建其余事件 eligibility、随机抽样顺序或 critical-success 生产概率。

`befriend_scheme_outcome_events.txt:872–929` 的 `.2006` 在 option `.2006.a` 才调用 `leave_faction_with_cooldown_effect { FACTION=scope:targeting_faction YEARS=10 }`。共享 effect `00_faction_effects.txt:41–58` 先 `leave_faction`，再对非 landless-adventurer 写 `joining_faction_block`；有该特殊政府身份时不能从 `YEARS=10` 直接外推一定写了十年阻挡。事件 immediate 的潜在友谊效果与该 option 的离开效果须分别记。

`.6006:1953–2015` 是独立的 leader 路径：先挑出该 AI target 领导、且当前针对 owner 的一份 faction；选项结束 scheme，通知其中人类成员并销毁这一份 faction。不能因同用 `.2006.a` 的选项名，把它解释成只移出 leader。实际 faction 是否消失、是否仍有其他 targeting faction，以及实际战争是否结束，仍须各自读回。

因此，自然 Befriend 后观察到 faction 消失有一个已查明的**显式事件原因候选**；这与“赠礼提高好感后，AI 以后重算分数可能退出”不同。只有实际事件实例、被选选项和独立后态能把该候选升级为本局原因。本轮没有这类实机证据，也没有因此给 Robert 新增可执行 Befriend 策略。

## 拒绝君主要求的实际候选与消费者

已核 `00_prison_interactions.txt:600–630`：当前合格的既有非 populist faction 成员会先走 `imprisonment_retribution_start_faction_war_if_valid`；仅当没有 `joined_faction.faction_war` 时才继续普通 `war_for_imprison_effect`。不处于该分支的角色另走直接调用。已有派系开战与拒命战争不能合成一个“退派系/加入派系”状态。

`00_interaction_effects.txt:751–900` 的普通链为：

1. 保存当前 `liege_temp/rebel_temp`，以 rebel 向 liege 启动 `refused_liege_demand_war`。
2. 无 imprisonment reason 的分支，从 liege 的**全部直接 vassal** 枚举。base trigger 要求高于男爵、当前可用 AI、未被囚/无能、不在与 rebel 或 liege 交战，并排除对 liege 好感至少 80、或 dread-modified boldness 低至 -50 的对象。
3. 再评估关系支持、非法行为/荣誉支持，或强烈反感 liege 且未过度反感 rebel 等 OR 分支；不同 difficulty 对人类 liege 的阈值不同。这些是显式当前输入，不是普通 `ai_join_score` 的取值。
4. 有 leading house 的候选还受 house-head 条件；随后 `bloc_member_join_war_effect:1390–1410` 另外从 rebel 的 top-liege 下枚举相同 house-confederation 的 vassal，加入列表。该补充明确独立于前一组 legality，不能把 base filter 当完整必要条件来裁剪全名单。
5. `vassal_join_rebel_war_effect:866–900` 只从 rebel 的 wars 找 `refused_liege_demand_war` 且 primary attacker/defender 与本次 rebel/liege 一致的战争，排除已有 participant，设置 called-to 后 `add_attacker`。随后对 liege 写 rebellious-vassal opinion。

玩家分支另由 `every_player` 选 liege 的 vassal，触发 `char_interaction.0232`；不能把自动 AI 过滤器套在人类选择上。revoke 与 retraction 的相邻效果沿相似列表和 consumer，但 reason、行政制度、头衔与具体好感分支不同；本轮没有声称三种拒命名单等价。

还有一个可直接避免误读的 AI 估计边界：`00_interaction_values.txt:525–536` 的 `revoke_refusal_war_rising_strength_value` 使用 `every_powerful_vassal` 加 base + tyranny trigger，实际 effect 使用 `every_vassal`、多条 OR 和 bloc 补充。实际消费者已继续定位为 `00_interaction_triggers.txt:200–205` 的 `revoke_refusal_war_would_be_massive_trigger`，再由 `00_revoke_title_interaction.txt:1474–1500` 的 `ai_will_do` 两处 `factor=0` 分支消费。初版将这处称为“预览”，当时未定位 GUI caller，该措辞现更正为已证 AI 意愿输入。该数值不能从源码直接认证为真实参战者完整兵力总和。本轮没有证明它是当前我方某消费者的缺陷，没有增加替代评分器或新 guard；完整来源见 [后继实际 consumer91](g2-m1-revoke-refusal-ai-consumer-12004-resume61-2026-10-26.md)。

## 重新验证、缓存和下一定位入口

`_factions.info` 区分持续 `is_character_valid`、加入 `can_character_join`、create、leave callbacks 及 `inherit_membership`。`00_rules.txt:265–349` 的全局 hard/soft block 又独立于 faction 自身定义。已有 common join trigger 对人类/AI 的关系分支，与全局 hard block 的 friendship 条件在源码上并非同一段；没有实际 code composition，不擅自判定哪段绕过、哪段覆盖，也不放宽我方准入。

`.info:57` 将 `update_effect` 注释绑定 `NDefines::NFaction::UPDATE_INTERVAL_DAYS`；本轮在当前 `common/defines` 和 `common/factions` 的有界搜索只找到这条引用，未找到键定义或任何 faction 的 `update_effect` 实现。它不能推出“没有更新”，也不能推出每日/月初固定重算。普通 AI 实际候选容器、分数缓存失效、成员重验与最终退出 call 仍是下一 exact .4 原生定位入口；不得拿旧版 RVA 或文档注释填成已闭合边。

生成图与源表见 [同一 plan 生成的边记录](evidence/g2-m1-membership-callers-12004-resume61-graph02-2026-10-26.md)。所有已知 effect 链只标 `static-confirmed`，运行调度、提交和实际后态保持虚线。工具检查仅验证记录结构/文件身份，不验证语义，也不产生 live 结论。初版 plan 把 supports 错写为数组，实际 check 曾 exit2；已按既有合同改回文本，保留该失败事实，未改检查器。

本轮无生产修改、Maven/Native/JUnit/Game/Steam/窗口操作、无新动作、无新增游戏日、无业务验收。Gift87 是 Host 已读回采用的编译候选，当前 M1 的真实测试仍由 Host 局部构建通过后调度；本页源审不代替它。输出限于 128 KiB 以内的小型 plan/正文/生成图，受本轮 source grant 管理；旧租约未复用，未删除或复制冻结原件，record 按通用策略 180 日复核。
