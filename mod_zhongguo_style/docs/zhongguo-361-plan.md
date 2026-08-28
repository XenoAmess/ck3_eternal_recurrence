# 天朝特色361制封臣绩效考核（ZhongGuo 361 Style）— 详细设计计划

版本：v1.0（2026-08-28，规划基线）
状态：**已获所有者批准，待一期施工**
命名空间：脚本 `zg361_`；事件 `namespace = zg361`；验收夹具 `zg361a_`

---

## 1. 一句话概念

把阿里 "361" 绩效考核（头部 30% = 3.75 超出预期 / 中间 60% = 3.5 符合预期 / 尾部 10% = 3.25 待改进，
横向排名、强制分布、连续两年 3.25 末位淘汰）完整搬进 CK3 的天朝制官僚体系：
皇帝每年给全体在任封臣打分排名，发榜、奖惩、校准、淘汰；玩家既可以当考核别人的皇帝，
也可以当被 AI 皇帝打了 3.25 后想办法翻盘的封臣。

## 2. 决策确认记录（所有者拍板）

| 决策点 | 结论 |
|---|---|
| AI 适用性 | **AI 天朝统治者也执行完整考核**（AGENTS.md 默认玩家限定约束的第二个已授权例外，首个为 ox_here）。AI 静默结算，事件只弹玩家 |
| AI 末位淘汰策略 | **激进版**：所有 AI 皇帝均可对连续 3.25 封臣执行免费夺爵，裁决取决于好感、能力、家族势力、派系、性格、财政等因素（详见第 5 节权重表） |
| 政府范围 | 仅 `celestial_government`（判定用 `government_has_flag = government_is_celestial`），不含 meritocratic / administrative / japan_administrative |
| 文案风格 | **纯梗直给**：直接写"绩效 3.75/3.5/3.25""末位淘汰""绩效改进计划（PIP）""野狗/小白兔"，互联网黑话入戏 |
| 交付节奏 | 三期递进：一期核心循环 → 二期博弈层 → 三期表现层（活动/GUI/发布） |

## 3. 原版机制映射（调研证据，CK3 1.19 / All Under Heaven）

361 的每个要素在天朝制里都有成熟原生落点，无需发明轮子：

| 361 概念 | CK3 原生落点 | 证据（游戏本体路径） |
|---|---|---|
| KPI 业绩分 | `governor_efficiency` 总督效率（scripted value，五维×1.7 + 官职经验 + 庄园 + 契约，展示值 −50~+50%），被引擎直接消费于税/兵缩放与夺爵成本 | `common/script_values/07_ep3_values.txt:1381`（`governor_efficiency_presented` 于 2154） |
| 职级/薪级 | merit 贤能品级 0–9（不入流~一品），引擎自动套 `merit_level_N` modifier 并按品级发俸禄（`monthly_treasury_from_salary_budget_base`）——天然薪级工资 | `common/modifiers/00_basic_modifiers.txt:252+`；`common/defines/00_defines.txt:157 LEVELS_MERIT` |
| 绩效奖金/扣薪 | `add_treasury` / `remove_treasury` / `change_merit`（scripted value 参数，支持负值） | `common/scripted_effects/10_dlc_tgp_scripted_effects.txt:1359` |
| 晋升门票 | 任命继承 `candidate_score`；原版已预留变量通道 `var:merit_civilian_career_score_bonus` / `merit_military_career_score_bonus`，**mod 写入即被原版任命排序消费**，零侵入 | `common/succession_appointment/celestial_governor.txt:116-124`；清空逻辑 `title_on_actions.txt:2213` |
| 末位淘汰 | `governor_removal_interaction` / `force_governor_removal_interaction` / `revoke_title_interaction`（低效率还降低夺爵影响力成本）；opinion modifier 支持 `revoke_title_reason = yes` 提供合法夺爵理由 | `common/character_interactions/06_ep3_interactions.txt:6180/6687`；`00_revoke_title_interaction.txt:327` |
| 年度考核 tick | `yearly_playable_pulse`（每个 count+ 角色每年生日触发一次，root=本人），用 `on_actions = { 自定义钩子 }` 无侵入挂载（本仓库既定模式） | `common/on_action/yearly_on_actions.txt:840`；扩展规范 `_on_actions.info:102-117` |
| 横向排名 | 原版无封臣百分位排名，但**科举殿试排名模式**可直接复用：每个封臣数"分数 ≥ 自己的同侪数量"→ 名次，再除 cohort 总数 → 百分位 | `common/scripted_effects/tgp_imperial_examination_scripted_effects.txt:1986`（`exam_grab_entrant_position_effect`） |
| 校准会议 | Hold Court 式"决议 + 事件链"成熟可行；三期可升级为 activity（模板 = `imperial_examination` 殿试：cohort 管理 / 排名 / 分档奖励全套） | `common/activities/activity_types/imperial_examination.txt` |
| 价值观双轨 | 好感度 + 罪行特质 + 派系成员状态，输入齐全 | — |
| 治理任务 KPI | 原版 task contracts（治理任务）本就是"领导下达的 KPI"，完成/失败自带 merit 奖惩，可作为考核输入 | `common/task_contracts/tgp_admin_contracts.txt` |
| 中文风味 | 简中原版已就位：天朝制 / 贤能品级 / 一品~九品 / 总督效率 / 国库 / 吏部尚书 | `localization/simp_chinese/dlc/tgp/tgp_china_government_l_simp_chinese.yml` |

**可行性结论**：排名为中等工作量（手写百分位，O(N²) 但年度 × 直接封臣 < 50 无性能之忧）；
活动为三期可选项；其余全部为 Easy。无 Hard 项。

## 4. 核心设计（一期主体）

### 4.1 考核对象与周期

- **考核单元**：每位天朝制统治者（`government_has_flag = government_is_celestial`，且为独立领主）
  + 其**直接封臣中的在职官员**（`is_governor = yes`；不含朝贡国、不含宫廷大臣——大臣纳入二期评估）。
- **周期**：默认每年一次，挂 `yearly_playable_pulse`（各领主生日年度 tick，天然错峰）。
  游戏规则 `zg361_review_frequency`：年度（默认，阿里梗）/ 三年（明代大计梗）。
- **新人保护**：上任不满 1 年（变量 `var:zg361_appointed_on` 记录任命年，由 title on_action 或年度快照兜底）
  的封臣**免于被打 3.25**（仍可得 3.5/3.75）。对应现实"新员工容易成为低绩效候选人"痛点的反向保护。
- **小团队松绑**：cohort < 10 时末位名额 `floor(n × 10%)` 自然为 0；
  游戏规则"刚性 361"开启时 n ≥ 5 保底 1 个 3.25（还原"全员达标也必须有人背 3.25"的荒诞感——梗的核心）。

### 4.2 KPI 公式（一期草案）

全部参数集中于 `common/script_values/zg361_values.txt` 单一入口，便于调平衡：

```
zg361_kpi_score =
    governor_efficiency_presented × 2      # 产出：-100 ~ +100，权重最大
  + merit_level × 8                        # 职级匹配：0 ~ 72
  + ( 当年 merit 净增量 ÷ 10 )             # 成长：跨年快照 var:zg361_merit_snapshot 对比
  + ( 皇帝对封臣好感 ÷ 5 )                 # 上级评价：-20 ~ +20
  + 治理任务完成奖励（二期接入 task contracts 记录）
  - 价值观红线扣分（见下）
```

价值观红线（每项独立扣分，可叠加）：

| 红线 | 扣分 |
|---|---|
| 在反皇帝派系中 | −40 |
| 与皇帝交战/曾起兵 | −60 |
| 持有 kinslayer / murderer 等重罪特质 | −30 |
| 超退休年龄仍占位 | −25（"该让位了"） |

一期开工第一步：**数值摸底探针**——对 1066 宋廷开局封臣 dump `governor_efficiency_presented` /
merit_level 分布，再敲定上表权重（探针走 debug_log `ZG361:` 标记，验收 runner 可复用）。

### 4.3 排名算法（脚本层，科举模式）

每年考核 tick（root = 领主）：

```
# 1. 建 cohort 并打分
every_vassal = {
    limit = { is_governor = yes 非新人保护 }
    set_variable KPI → var:zg361_kpi
    add_to_list = zg361_cohort
}
cohort_n = list_size:zg361_cohort  → 存领主 var:zg361_cohort_n

# 2. 百分位（对 cohort 内每人）
every_in_list zg361_cohort → root_vassal:
    every_in_list zg361_cohort → peer:
        limit = { peer.var:zg361_kpi >= root_vassal.var:zg361_kpi }
        add_to_list = zg361_rank_list
    rank = list_size:zg361_rank_list          # 并列同名次，符合直觉
    percentile = rank / cohort_n

# 3. 分档
percentile <= 0.30 → 3.75
percentile >  (1 - 末位比例) → 3.25（新人保护豁免；豁免者自动升入 3.5，末位顺延给下一名）
其余 → 3.5
```

- 末位比例由游戏规则/决议提供：刚性 10% / 松绑 5% / 放养 0%。
- 同分并列：用 `>=` 计数 → 并列者同名次，可能使 3.75 略超 30%、3.25 名额被并列挤占——
  这正是"校准会议"要解决的戏剧张力，不视为 bug。

### 4.4 分档结果与奖惩

三档均发**限时 1 年 modifier**（`add_character_modifier years = 1`，自动过期 = 天然年度刷新，
无需清理逻辑；重新考核即覆盖）：

| 档位 | modifier `zg361_grade_*` | 实质后果 |
|---|---|---|
| **3.75 超出预期** | 外交+1、领主好感+15、`monthly_merit_mult +0.3`、封臣好感+10 | `change_merit = major`；**绩效奖金**（`add_treasury`，按俸禄档位缩放）；**晋升提名** `var:merit_civilian_career_score_bonus +30`（原版任命系统直接消费）；`var:zg361_streak_top += 1`、`streak_bottom = 0` |
| **3.5 符合预期** | 中性（领主好感+3） | 小额 merit；事件文案阿里味废话文学（"你做得很好，继续保持"） |
| **3.25 待改进** | 领主好感−20、`monthly_merit_mult −0.5`、每月威望−0.5 | merit 扣减（`medium_merit_loss`）；获得 **PIP** 标记 1 年（`var:zg361_pip`）；皇帝对其获得 `zg361_poor_review` opinion modifier（**带 `revoke_title_reason = yes`**，提供合法夺爵理由）；`streak_bottom += 1`、`streak_top = 0` |

**连续追踪（梗的灵魂）**：

- **连续两次 3.75** → "晋升通道开启"事件：`var:merit_civilian_career_score_bonus +80`（大额）+
  临时 `character_max_merit_level_add +1` modifier（淘天"连续两季度 3.75 晋升"梗）。
- **连续两次 3.25** → **末位淘汰**（第 5 节）：玩家领主弹处置决策事件；AI 领主按激进裁决表静默执行。
- 连续两年数据全部存封臣变量，跨存档持久（CK3 var 随存档）。

### 4.5 事件投递分流（AI 例外下的玩家闸门）

年度 tick root = 领主（可能是 AI）：

- 领主是 AI → 后台静默结算全部封臣奖惩与淘汰；**仅当某封臣是玩家**时，向该玩家投递
  "你的考核结果"事件（root = 玩家封臣）。
- 领主是玩家 → 结算后投递"考核季结果"总览事件 +（二期）校准会议事件链；
  每个玩家封臣也各收自己的结果事件。
- 所有事件带 `theme =`；事件文件 `namespace = zg361`。

## 5. AI 末位淘汰裁决（激进版，所有者指定）

触发：封臣 `var:zg361_streak_bottom >= 2` 进入淘汰名单。领主（AI 或玩家）对每名淘汰候选人
选择四种处置之一；玩家走事件选项，AI 走下述评分。

### 5.1 四种处置

| 处置 | 效果 |
|---|---|
| **免费夺爵** | 直接剥夺主头衔（携带 `zg361_poor_review` 合法理由，无暴政）；皇帝直辖或转封心腹 |
| **强制致仕** | 调用致仕逻辑（仿 `governor_removal_interaction` 结果）：封臣退位，头衔走任命继承；无合法理由负担，体面 |
| **降岗留用** | 契约义务降级 + 俸禄档降级 + merit 中额扣减；`streak_bottom` 清零、PIP 重置 1 年（"再观察一年"） |
| **再留一年** | 仅 PIP 延期（罕见；第三次 3.25 时不再可选） |

### 5.2 裁决分 `zg361_ai_purge_score`（基础 100，越高越倾向夺爵）

**好感因子**（皇帝对封臣 opinion）：

| 条件 | 加减 |
|---|---|
| opinion ≤ −50 | +120 |
| opinion ≤ −20 | +60 |
| opinion ≤ 0 | +20 |
| opinion ≥ +20 | −40 |
| opinion ≥ +50 | −100（亲信基本豁免夺爵，最多致仕/降岗） |

**能力因子**：

| 条件 | 加减 |
|---|---|
| 当年百分位 < 5%（淘汰者中也垫底） | +50 |
| merit_level ≤ 1 | +40 |
| merit_level ≤ 3 | +20 |
| merit_level ≥ 6 | −60（高品级人才难得） |
| governor_efficiency_presented < −10 | +30 |
| governor_efficiency_presented > +20 | −40（能吏偶失常） |

**威胁/忠诚因子**：

| 条件 | 加减 |
|---|---|
| 在反皇帝派系 | +80 |
| 与皇帝互为宿敌/仇恨 | +40 |
| 封臣征召兵 > 皇帝 20% | −50（硬夺可能逼反，改致仕） |
| 封臣属 powerful/dominant family | −30（同上，世家给体面） |

**年龄/潜力因子**：超退休年龄 → 处置**锁定为强制致仕**（不进夺爵判定）；年龄 < 30 → −20（年轻可塑）。

**皇帝性格因子**：sadistic / deceitful / ambitious / arbitrary 各 +30；
compassionate / forgiving / trusting 各 −40；lunatic / possessed +20。

**财政因子**：皇帝国库欠债 +30；直辖未满 +20（夺爵回血动机）。

**连续因子**：streak_bottom = 3 → +80；≥ 4 → +150（几乎必夺爵）。

**随机抖动**：最终 + `integer_range(0, 40)`，避免玩家对 AI 行为完全可预测。

### 5.3 处置映射

```
超退休年龄 且 opinion ≥ 0          → 强制致仕
军力强或世家大族                   → 强制致仕（夺爵风险高）
purge_score ≥ 200                 → 免费夺爵
120 ≤ purge_score < 200           → opinion < 0 → 强制致仕；merit ≥ 5 → 降岗留用；其余取致仕
60 ≤ purge_score < 120            → 降岗留用
purge_score < 60 且 opinion ≥ 30  → 再留一年（streak_bottom < 3 时才可选）
```

### 5.4 玩家封臣的淘汰保护阀（激进下的唯一出口）

玩家作为 AI 皇帝的封臣被判淘汰时，收到淘汰通知事件，获得一次性翻盘窗口：

- **最后申诉**：消耗影响力 + 人情 hook，按真实百分位重裁（翻案成功 → 降岗留用）；
- **散尽家财**：支付大额金币/国库 → 改降岗留用（"花钱保命"）；
- **掀桌起兵**：直接获得对皇帝的宣称战争 CB / 加入或创建反皇帝派系（"绩效逼反"，给出反抗出口）；
- **认命致仕**：体面退场，保留 merit 与好感（留得青山在）。

## 6. 二期：玩家博弈层

- **绩效校准会议**（Hold Court 式决议 + 事件链）：自动排名出榜后、公示前，玩家皇帝可对
  边缘人选微调——抬一个 3.5→3.75（顶掉榜尾 3.75，被顶者记恨 opinion modifier）；
  踩一个 3.5→3.25（凑末位指标/打击政敌）。每次动手脚有曝光检定，曝光 →
  全封臣 `zg361_rigged_review`（考核黑幕）好感 −10、持续 5 年。
- **末位比例决议**：刚性 10% / 松绑 5%（2020 改革梗，"361 的打分要坚持，刚性 1 比例需要松绑"）
  / 放养 0%，调整消耗威望或国库。
- **角色互动**：
  - 封臣→领主：**绩效申诉**（消耗影响力/人情翻案，AI 按真实百分位裁决）；**邀功请赏**。
  - 领主→封臣：**绩效沟通**（一对一安抚消 stress / 敲打加压力降派系倾向）。
  - 封臣→封臣：**举荐 / 攻讦**（影响对方明年 KPI 分；攻讦失败反扣自己价值观分——
    原版 `boost/damage_efficiency_interaction` 的 361 化）。
- **价值观双轨**：业绩分 × 价值观分（好感 / 诚实系特质 / 罪行 / 派系）→
  **野狗**（高业绩低价值观：忍痛留用 with 代价 or 严惩事件）与
  **小白兔**（低业绩高价值观：安抚性致仕事件）。
- **大臣纳入考核**（评估后定）：吏部尚书等朝臣进入 cohort 或单独榜单。

## 7. 文案基调示例（纯梗直给）

- 决议组：`绩效考核`
- 决议：`开展年度绩效考核` / `调整末位淘汰比例` / `召开绩效校准会议`
- modifier：`绩效3.75·超出预期` / `绩效3.5·符合预期` / `绩效3.25·待改进` / `绩效改进计划（PIP）`
- 事件标题：`年度绩效考核季` / `绩效校准会议` / `你被打了3.25` / `末位淘汰名单` / `野狗与小白兔`
- 结果事件选项（玩家封臣被打 3.25）：`【认命】` `【申诉】` `【摆烂】` `【奋发】`
- 3.5 通知文案："你的表现符合预期。皇帝陛下对你的工作表示满意，并勉励你继续努力。"（废话文学）

日常开发只写简体中文 + 英文；其余 7 语言英文占位保持可加载，发布时走 MiniMax 流程补齐。

## 8. Mod 骨架（文件级设计）

```
mod_zhongguo_style/
  descriptor.mod                     # 无 BOM；version 0.1.0；supported_version 1.19.0.6；无 remote_file_id
  README.md                          # 源码树 only
  docs/zhongguo-361-plan.md          # 本文档
  common/
    script_values/zg361_values.txt          # KPI 公式、阈值、奖惩数值、AI 裁决权重（唯一调平衡入口）
    scripted_triggers/zg361_triggers.txt    # 分档判定（仿科举 has_perfect_score_trigger 参数化模式）
    scripted_effects/zg361_effects.txt      # 打分/快照/排名/结算/奖惩/淘汰裁决
    on_action/zg361_on_actions.txt          # yearly_playable_pulse += on_actions = { zg361_annual_review }
    modifiers/zg361_modifiers.txt           # 三档限时 modifier + PIP + 晋升通道
    opinion_modifiers/zg361_opinions.txt    # 天子垂青 / 考绩不佳(revoke_title_reason) / 考核黑幕
    game_rules/zg361_game_rules.txt         # 考核频率(年度/三年)、末位比例(刚性10/松绑5/放养0)
    customizable_localization/zg361_custom_loc.txt   # 考绩评语按档位切换
    decision_group_types/zg361_decision_group_types.txt   # 二期
    decisions/zg361_decisions.txt           # 二期：校准/比例/立即考核
    character_interactions/zg361_interactions.txt         # 二期：申诉/沟通/举荐/攻讦
  events/zg361_events.txt                   # namespace = zg361；全部带 theme
  localization/{english,simp_chinese,...×9}/zg361_l_<lang>.yml   # 全 BOM
  # 三期追加：
  # common/activities/activity_types/zg361_jingcha.txt（京察大计活动，殿试模板）
  # gui/zg361_scoreboard.gui + gui/scripted_widgets/（考核榜面板，须注册）
```

关键坑预防（仓库 docs 已沉淀，施工时必须遵守）：

- 决议 `effect`/`hidden_effect` 会被 UI 预执行 → 复杂后果走 pending flag + GUI bridge（ox_here 模式），
  不在决议里写有序事件链；
- on_action 同名覆盖不合并 → 只加 `on_actions = {}` 条目；
- 自定义顶层窗口必须注册 `gui/scripted_widgets/`；
- 全部脚本/yml 文件 UTF-8 BOM；`script_values` 目录名不能写成 `scripted_values`；
- customizable_localization 的 key 必须在当前游戏语言 yml 里存在；
- 事件必须有 `theme`；option 内没有 `after` 字段；
- 变量读取前必须确认已 set（或写默认分支）。

## 9. 三期路线图与验收标准

### 一期 · 核心循环（纯脚本可玩）

交付：骨架 + 游戏规则 + 年度 tick + KPI + 30/60/10 排名 + 三档 modifier + merit/国库/好感奖惩
+ 连续计数 + 玩家结果事件（领主/封臣两侧）+ AI 静默结算与激进淘汰 + zh/en 本地化。

验收（实机 runner GREEN）：
1. 1066 宋廷开局 → 跑年度 tick → 断言三档人数比例 ≈ 3/6/1（含小 cohort 松绑边界用例）；
2. 断言 modifier / merit / 国库 / 变量正确落账，存档读档后 streak 变量完好；
3. 玩家作为 AI 皇帝封臣收到结果事件；连续两次 3.25 的玩家封臣收到淘汰事件且四个出口可用；
4. AI 皇帝对连续 3.25 封臣按权重表执行处置（构造低好感低能力用例断言夺爵发生）；
5. error.log 0 条 `zg361` 错误。

### 二期 · 博弈层

交付：校准会议事件链 + 末位比例决议 + 四个角色互动 + 野狗/小白兔双轨事件 + 完整末位淘汰链 UI。

验收：校准抬/踩正确互换两人档位且曝光惩罚可触发；申诉按真实百分位裁决；
淘汰链四处置各有实机证据。

### 三期 · 表现层与发布

交付：京察大计活动（殿试模板）+ 考核榜 GUI 面板 + thumbnail/决议图素材（compose 工具）
+ 九语言 MiniMax 翻译 + 工坊页面（bbcode/截图账本）+ `build_mod_zhongguo_style_release.py` 发布管线。

验收：活动全程 GREEN；面板排名与结算数据一致；发布构建 `--check` 双构建可复现；
CI 接入（test / --check / dispatch 构建 / `zhongguo-361-v*` tag release）。

## 10. 构建 / 测试 / 发布管线

- 构建器：克隆 `tools/build_ox_here_release.py` → `tools/build_mod_zhongguo_style_release.py`
  （`PRODUCT_ID = "mod_zhongguo_style"`、tag 前缀 `zhongguo-361-v`、
  `FORBIDDEN_WORKSHOP_ITEM_IDS` 加入三家现有 ID）；配套 `test_build_mod_zhongguo_style_release.py`。
- 实机验收：克隆 `tools/run_ox_here_acceptance.py` 模式 → `tools/run_zhongguo_acceptance.py`
  （一次性 `-userdir`、外部夹具 `tools/fixtures/zg361_acceptance`、
  `PROJECT_TOKENS = ("zg361", "zg361a_")`、`debug_log` 前缀 `ZG361:`）。CI 保持 L0-only。
- 用户目录注册：`mod/mod_zhongguo_style.mod` = 内层 descriptor + `path=`；
  `remote_file_id` 仅在首次工坊上传后写入外层，永不进仓库。

## 11. 风险与开放问题

1. **KPI 权重需数值摸底**：`governor_efficiency_presented` 在天朝封臣上的实际分布未知，
   一期第一步先做分布探针再定权重（验收 runner 可复用该探针）。
2. **排名 O(N²)**：年度 × 直接封臣（通常 < 50）无虞；cohort 异常膨胀时加 `max` 截断保护。
3. **激进 AI 淘汰的次生风险**：AI 皇帝频繁夺爵可能扰动原版王朝循环催化剂平衡
   （任命低贤能官员已有催化剂）；一期实机观察后再决定是否加全局冷却。
4. **merit 快照边界**：任命/死亡跨年边界用"无快照 → 当年只记不评"兜底，新官不背锅。
5. **大臣（吏部尚书等）是否进 cohort**：一期不含；二期评估其头衔结构后决定。
6. **并列名次的档位膨胀**：视为校准会议戏剧张力素材，不修复。

## 12. AGENTS.md 联动（施工时同步）

- 在"硬性约束"AI 条款中登记本 mod 为**第二个已授权例外**（激进策略要点一并落档）；
- 项目结构一节加入 `mod_zhongguo_style/` 条目；
- 构建/测试命令清单在一期管线落地后同步；
- 新踩的 Paradox 脚本坑当场沉淀 `docs/grammar/pitfalls.md`（症状/原因/解法三栏）。

---

## 13. 一期实施偏差记录（2026-08-28 静态施工，未经实机）

一期代码已落地（仅 `mod_zhongguo_style/` 内，未经实机验证）。相对上文计划的偏差：

1. **玩家领主淘汰处置改为批量三选**（依律处置/全部降岗/网开一面，zg361.5），
   放弃逐人事件——跨事件传 scope 无安全机制（名单 list 不跨链存活），逐人细化移至二期
   （用 character_interaction 原生 recipient scope 实现）。
2. **玩家封臣"掀桌起兵"出口暂缓**（需 faction/战争 effect 核实），一期 zg361.6 只给
   最后申诉/散尽家财/认命致仕三个出口。
3. **派系红线未进 KPI**：`is_in_faction` 触发器未在本体文件中找到可靠形态，一期红线只含
   与领主交战、重罪特质、年满 60。派系维度随二期价值观双轨一起做。
4. **merit 增量快照用品级（merit_level）而非原始 currency**：原始 merit 未证实可按值读取；
   品级差 ×10 夹 ±20 进 KPI。
5. **AI 裁决的随机性**用"15% 概率宽宥 −40 分"实现（integer_range 在 vanilla script_values
   无先例，不用）。
6. **好感入 KPI 用分档 if 链**（±5/±10/±20），不做精确线性读取。
7. **降岗暂不动契约义务等级**（contract obligation 操作留二期），一期降岗 =
   merit 大额扣减 + `zg361_demoted` modifier + PIP 重置。
8. **退休年龄用平铺 `age >= 60`**，未接 `tgp_is_above_retirement_age_trigger`
   （该触发器依赖 celestial_retirement_law  realm law，二期再接）。
9. 事件文案暂不打印各档人数（跨链 scope 变量在 loc 中打印未核实），数字表现留三期 GUI 面板。
10. 新增"首年试用期"语义：无 merit 快照的官员当年只记不评（顺带解决中途任命/旧存档引入问题）。

### 13.1 查漏补缺闭环（2026-08-28 第二轮自审）

首轮实施后对照 §4/§5 重新逐条核对，补齐以下遗漏：

- AI 裁决分补上**军力对比**（封臣兵力 > 皇帝 20% → −50；> 50% → 处置强制锁致仕）、
  **皇帝直辖未满**（+20 夺爵回血动机）、**淘汰者垫底**（名次 = cohort 末位 → +50）三个因子，
  均以 effect 层已验证语法实现（saved-scope 点读 `current_military_strength`、`domain_size < domain_limit`、
  跨 scope 变量比较）。
- 3.75 晋升提名与连续 3.75 晋升加成**按文官/武将分写** `merit_civilian_career_score_bonus` /
  `merit_military_career_score_bonus`（以 `vassal_contract_has_flag = celestial_military_appointment` 判别）。
- 绩效奖金从固定 100 改为**按贤能品级缩放**（60 + 品级×15），贴合"按俸禄档位缩放"的设计意图。
- 皇帝性格因子采用 sadistic/deceitful/ambitious/arbitrary/callous 与 compassionate/forgiving/trusting；
  lunatic/possessed 未纳入（未在本体 00_traits.txt 直接命中形态，保守舍弃）。

### 13.2 二期/三期静态施工记录（2026-08-28 第三轮，所有者指令"全都要"）

**本期新增落地**：

- **绩效校准会议**（zg361.10/11/12）：考核主链改为"待定分档（var:zg361_pending_grade）→ 校准 → 结算"
  三段式；AI 直接结算，玩家领主先收校准会议事件：直接公示 / 抬一人（末名 3.75 与头名 3.5 互换）/
  踩一人（末名 3.5 打进 3.25，原头名 3.25 获救；末位名额为 0 时踩最后一名硬造一个 3.25——刚性 361 之味）。
  每次动手 25% 曝光：全考核池获得 `考核黑幕` 好感（-10 / 5 年衰减）。
- **末位比例决议 ×3**（刚性 10% / 松绑 5% / 放养 0%）：写领主变量 `zg361_ratio_override`，
  阈值计算优先于游戏规则；威望 75，冷却 1 年，AI 不用。
- **立即开榜决议**：威望 150 + 冷却 1 年；按决议安全模式只发延迟 1 日的隐藏载体事件 zg361.20，
  考核主链在其 immediate 执行（规避决议 UI 预评估坑）。
- **角色互动 ×6**：绩效申诉（封臣→领主，150 影响力，AI 按好感/品级/交战状态裁决，翻案改判 3.5 并
  修正领主侧计数）；绩效沟通（领主→封臣，减压+好感）；举荐（同侪→同侪，对方下期 KPI+10）；
  攻讦（同侪→同侪，50 威望，七成对方下期 KPI−15，三成反噬自己并被对方记恨）；
  末位处置·夺爵 / 勒令致仕（领主→淘汰候选人，逐人执行，复用淘汰 effect）。
  全部 `ai_will_do = 0`：AI 走年度自动裁决，不与互动双重执行。
- **价值观双轨**：新增 `zg361_values_score_value`（忠诚好感/品性特质/重罪/交战/朋党），
  野狗（KPI≥50 且价值观≤−20）与小白兔（KPI≤0 且价值观≥20）分类；玩家领主收到 zg361.30
  （打印两类人数），选项：宽严相济（安抚小白兔）/ 严惩+劝退（野狗扣贤能入 PIP，小白兔致仕，+50 威望）。
- **派系红线**：`exists = joined_faction` 入 KPI（−25）与裁决分（+80）。
- **降岗减俸**：`zg361_demoted` 增加 `monthly_treasury_from_salary_budget_mult = -0.5`（俸禄减半），
  不动契约义务等级（原版无可读的当前等级触发器，无法安全逐级降档；此为最终方案，偏差 #7 关闭）。
- **玩家"掀桌起兵"出口**：zg361.6 新增选项 d——建立独立派系对抗皇帝（`can_create_faction` /
  `create_faction` 原版互动同款形态）。偏差 #2 关闭。
- **各档人数进事件文本**：zg361.1/5/10/30 用 `save_scope_value_as` + `[TopScope.GetValue('...')|0]`
  打印各档人数（原版 coronation/accolade 同款形态）。偏差 #9 关闭。
- **京察大计活动**（`activity_zg361_jingcha`）：首都单阶段集会，邀请全体在任封臣，
  落幕时立即跑一次完整考核；赴会者小额 merit + 对主办方 +10 好感；冷却 3 年；成本走 gold
  （天朝制政府规则自动转为国库支出）；AI 不主动举办。骨架字段全部克隆自 camp_party/feast 已验证形态。
- 静态校验器扩展：decisions / character_interactions / decision_group_types / activities 的
  loc key 覆盖检查；当前 GREEN。

**本期仍存的已知边界**：

1. 考核榜 GUI 面板**降级为不做**：纯脚本 GUI 无法迭代任意角色列表渲染排行榜
   （角色列表需要 code 侧 data context）；排名信息已由事件文本计数 + 封臣 modifier 承载。
2. 校准抬/踩对**并列同档者**整批互换（设计上接受为戏剧张力）。
3. 活动未经实机：`window_characters` 与 travel 细节省略，实机验收时重点看活动窗口表现。
4. 发布管线（构建器/CI/工坊）在仓库根目录，属于其他工作流范围，待所有者另行安排。

一期交付物：游戏规则 ×3、KPI/阈值/裁决分 script values、排名与结算 effects、
年度 on_action 钩子、6 modifier、6 opinion modifier、6 事件、九语言本地化（zh+en 创作，
7 语言英文占位）、本目录静态校验器 `tools/validate_local.py`（当前 GREEN）。
实机验收由所有者另行安排。
