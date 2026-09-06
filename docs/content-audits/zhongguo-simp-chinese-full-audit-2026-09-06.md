# 天朝二期简体中文文案与事件合理性全量审计

- 审计日期：2026-09-06
- 审计对象：`mod_zhongguo_style`
- 基准语言：简体中文
- 初始审计结论：**RED；初始产品不能通过中文内容验收。**
- 最新整改结论：**以第 18 节为当前状态。§17.5 后追回的 39 个简中 key、18 个问题簇已 39/39、18/18 静态修复；用户点名的 N-01/N-02 两类机器可判定失败均为 0。STATIC GREEN；人工语义复审与 5 速实机复验仍待完成。**
- 审计性质：本文从静态全量审计起步，后续章节同时保留历次 CK3 实机证据。当前最终账本仍不能静态证明动态插值、按钮实际截断、字体排版或事件发生时的完整语境，因此这些边界保持 **LIVE PENDING**。

这里的 `blocker` 指“在宣称天朝二期中文内容完成或发布前必须修复”，不等同于“必然导致 CK3 无法启动”。编码、键引用和生成可复现性基本健康；主要问题是玩家文案与实际 effect 不一致、案件缺少人物与事实、开发诊断语直接进入正式界面，以及大量模板卡不能支持知情选择。

## 1. 覆盖与方法

本轮不是抽样。审计把简中值、事件声明、玩家可见字段、决议/互动/活动、GUI 及生成器权威源做了全量清点和交叉引用。下表及 1.1/1.2 是初始审计提交 `e603baa` 的历史基线，不是当前产品清单；当前可复现清单以第 18 节链接的机器账本为准。

| 对象 | 全量覆盖 | 结果 |
|---|---:|---|
| `localization/simp_chinese/*.yml` | 22/22 文件，3,488/3,488 个唯一 key | 重复 key 0；缺 BOM 0；空值 0；等于 key 的占位 0；TODO/TBD 0；乱码/U+FFFD 0；未闭合 `$...$` 0；方括号不平衡 0 |
| 生成器产出的简中产品 | 21 个 YML，3,245 个 key/value | 另有手写 `zg361_l_simp_chinese.yml` 243 keys；总数与上行相符 |
| `events/*.txt` | 77/77 文件，992/992 个事件 | 玩家可见 622，hidden 370；可见事件均有 title/desc |
| 事件直接 loc 引用 | 2,987 个唯一简中 key | 缺失 0；另两个初报为多行 `set_variable name=`，不是 loc |
| 361 机制事件 | 361/361 个事件，1,083/1,083 个选项及 effect 调用 | 1,805 个事件使用 key 完整；机制主表共 1,848 keys |
| 机制 A/B 权威数据 | `tools/mechanism_choices/*.json` 722/722 条 | A/B 精确重复 0 |
| GUI | 5/5 文件；4 个自定义界面（榜单 + 3 个桥） | 143 个唯一静态 text/tooltip key 全有简中；917 个动态表达式均可归类为角色、头衔或变量 |
| 决议、互动、活动 | 7 项决议、6 项角色互动、1 项京察活动 | 玩家可见 key 齐全；无自定义 scheme |
| 静态校验 | `py mod_zhongguo_style/tools/validate_local.py` | GREEN，但它只证明结构，不证明语义、格式标记安全或 effect 一致性 |
| 生成复现 | `py mod_zhongguo_style/tools/gen_361_mechanisms.py --check` | GREEN：361 mechanisms / 208 files |

### 1.1 简中清单

| 文件 | key 数 | 文件 | key 数 |
|---|---:|---|---:|
| `zg361_b1_l_simp_chinese.yml` | 84 | `zg361_b2_l_simp_chinese.yml` | 41 |
| `zg361_career_hc_l_simp_chinese.yml` | 238 | `zg361_career_learning_l_simp_chinese.yml` | 93 |
| `zg361_compensation_runtime_l_simp_chinese.yml` | 34 | `zg361_credit_project_l_simp_chinese.yml` | 135 |
| `zg361_feedback_promotion_pip_l_simp_chinese.yml` | 258 | `zg361_incident_platform_l_simp_chinese.yml` | 81 |
| `zg361_l_simp_chinese.yml` | 243 | `zg361_manager_governance_l_simp_chinese.yml` | 6 |
| `zg361_mechanisms_l_simp_chinese.yml` | 1,848 | `zg361_phase2_central_l_simp_chinese.yml` | 3 |
| `zg361_phase3_metrics_delivery_l_simp_chinese.yml` | 175 | `zg361_workforce_ad_fact_l_simp_chinese.yml` | 15 |
| `zg361_workforce_appointment_fact_l_simp_chinese.yml` | 2 | `zg361_workforce_attribution_fact_l_simp_chinese.yml` | 5 |
| `zg361_workforce_endgame_l_simp_chinese.yml` | 212 | `zg361_workforce_exit_fact_l_simp_chinese.yml` | 2 |
| `zg361_workforce_normal_exit_fact_l_simp_chinese.yml` | 3 | `zg361_workforce_probation_fact_l_simp_chinese.yml` | 3 |
| `zg361_workforce_rehire_fact_l_simp_chinese.yml` | 3 | `zg361_workforce_remediation_fact_l_simp_chinese.yml` | 4 |

### 1.2 事件清单

| namespace / 家族 | 事件总数 | 玩家可见 | hidden |
|---|---:|---:|---:|
| `zg361`（含京察） | 16 | 13 | 3 |
| `zg361m` | 361 | 361 | 0 |
| `zg361b1` | 15 | 3 | 12 |
| `zg361b2` | 23 | 7 | 16 |
| `zg361ch` | 83 | 50 | 33 |
| `zg361cl` | 40 | 7 | 33 |
| `zg361cp` | 30 | 27 | 3 |
| `zg361pp` | 119 | 53 | 66 |
| `zg361comp` | 18 | 7 | 11 |
| `zg361ip` | 54 | 3 | 51 |
| `zg361mg` | 12 | 2 | 10 |
| `zg361p2c` | 7 | 1 | 6 |
| `zg361p3` | 37 | 35 | 2 |
| `zg361wad` | 5 | 5 | 0 |
| `zg361we` | 149 | 43 | 106 |
| 其余 Workforce fact | 23 | 5 | 18 |
| **合计** | **992** | **622** | **370** |

量化叙事证据：613 个 `.desc` 简中键中只有 19 个含角色、scope 或动态值；`zg361ch/cp/pp/p3/we` 合计 208 个玩家可见事件实例使用 205 个静态描述键，没有一条正文点出所绑定受评者。玩家文案中“冻结”约 316 次、“回执”68 次、`owner` 77 次、`HC` 107 次、`PIP` 92 次、“制度债”490 次。

## 2. 严重度总览

本报告按“问题簇”计数，不把同一生成模板波及的数百条字符串重复计为数百个问题：

| 严重度 | 问题簇 | 典型影响 |
|---|---:|---|
| Blocker | 12 | 文案承诺与 effect 相反/不存在、关键选项不可达、伪造结果、CK3 格式标记风险 |
| High | 24 | 无法知情选择、主体错位、隐藏代价、开发语泄露、按钮与案情不匹配 |
| Medium | 14 | 术语/时间/状态表达不清、死文案、重复和节奏问题 |
| Low | 7 | 明确病句、引号、标点和格式一致性 |

## 3. Blocker

| ID | 定位与原文摘要 | 问题 | 建议改法 |
|---|---|---|---|
| B-01 | `common/scripted_effects/zg361_b1_runtime_001_case_bootstrap_policy_kpi_effects.txt:879-887` 对所有人预置离任 route/grade=0；`common/scripted_effects/zg361_generated_scoreboard_snapshots.txt:9486-9510` 把非 1/3（含 0）映射为 3.50；GUI `gui/zg361_scoreboard.gui:7211-7227`，标签 `zg361_b1_l_simp_chinese.yml:45-51` | 非离任者会被榜单伪造成“离任者证据应得档/公示终档=3.50”，属于展示事实错误。 | 在 `tools/gen_scoreboard_snapshot.py` 只对真实离任且 route 非 0 的案卷显示离任行；sentinel 0 显示“不适用”，不得映射为 3.50。 |
| B-02 | 361 机制生成核心 `tools/gen_361_mechanisms.py:75-100`；无消费者的 ID 范围为 `18-31,38-39,42,44-46,48-52,54-68,82-134,146-191,229-344,355-357,360-361` | 仅 101/361 个 choice 变量有下游业务消费者；其余 **260/361** 的退款、发薪、招聘、晋升、调岗、合同、移交等文案承诺并不会发生，只改变通用组织账本、计数与 checksum。 | 给每个承诺补真实 consumer；未接入前把玩家文案明确降格为“组织政策倾向，只改变下列组织指标”，不得声称具体业务结果已经兑现。 |
| B-03 | 361/361 个 C 均为“这季度先不碰，登记制度债”，权威源 `tools/gen_361_mechanisms.py:642`；事件 trigger 又要求 choice 尚不存在，全仓无 remove/expiry | C 实际永久写入 choice=3，使该机制本局不再出现，并非“本季度延期”。 | 真正实现按季度/下轮 requeue 和到期清理，或诚实改成“本局搁置，不会自动再提案”。 |
| B-04 | 机制 84：`zg361_mechanisms_l_simp_chinese.yml:461-463`；effect `common/scripted_effects/zg361_generated_mechanism_043_policy_083_084_effects.txt:88-110` | A“三年递延”实际 `pay_debt -3, budget_pressure +3`；B“当期全发”实际 `pay_debt +2, budget_pressure -2`，账本效果与语义正反；且无业务 consumer。 | 先核定变量正负语义并修生成数据/effect，再补真实发放/递延 consumer；验收时同时断言文案方向和账本方向。 |
| B-05 | 三个比例决议：`common/decisions/zg361_decisions.txt:84-85,112-113,140-141` 只写 override=10/5/0；当前 B1 配额固定见 `common/scripted_effects/zg361_b1_runtime_004_quota_bank_debt_effects.txt:191-198,269-281`；文案 `zg361_l_simp_chinese.yml:26-37` | 玩家选择 10%/5%/0% 不影响当前 B1。严格版还声称池子≥5必有末位，但参考向量显示 5/6 人为 0、7 人才为 1。另有“刚性1比例”错词（loc :17/:31）。 | 把 override/game rule 接入当前 B1 并定义取整/最小人数；或功能接通前隐藏三个决议。同步改“刚性末位比例”。 |
| B-06 | `zg361_l_simp_chinese.yml:22-25`：“现在就……开榜排名/立即考核/开榜！”；decision `common/decisions/zg361_decisions.txt:5-29`，GUI bridge `common/scripted_guis/zg361_scoreboard_guis.txt:3-17`；下一阶段约 180 日后见 `common/scripted_effects/zg361_b1_runtime_002_cycle_self_review_effects.txt:178-186` | 点击只启动多阶段考核季，不会立即开榜或出结果。 | 改成“立即启动本年度考核流程/冻结名册”，确认按钮用“启动考核”，正文说明后续阶段与大致期限；或真正实现即时排名。 |
| B-07 | 京察 loc `zg361_l_simp_chinese.yml:78-82,196` 声称“落幕，考核结果张榜”；活动完成 `common/activities/activity_types/zg361_jingcha.txt:136-155` 只清 flag、给小量贤能/好感；考核季另在 `common/scripted_effects/zg361_jingcha_mandate_effects.txt:34-37` 启动 | 京察活动结束并不排名、张榜或推进到最终考核结果。 | 把文案改成“京察差事告一段落，考核季另行推进”，或让完成 hook 真正联动公示并提供专属内容。 |
| B-08 | `zg361pp.181`：events `zg361_feedback_promotion_pip_runtime_events.txt:3404-3507`，loc :193-197，生成器 `gen_361_feedback_promotion_pip_runtime.py:1444-1457,1541-1550` | A/B 宣称三分诊或归为“不愿做”，实际均写 `primary_category=0`、truth=0、RED=1；全模组无其他 writer。转岗要求 category=3，因此文案承诺的真实转岗不可达。 | 接真实证据写 1/2/3；证据未知时不要展示“已分诊”，明确材料不足并阻断后续分类。 |
| B-09 | `zg361pp.186`：events :3907-4018，loc :218-222，生成器 :1507-1514；hidden audit :6755-6799 | B 宣称“直接加码并生成目标膨胀违规”，A/B 却都写 workload/replacement/extension=0 且 `goal_creep_violation=0`，只有 route 计数不同。 | A 写等量替换/延期/复核，B 写新增工作量和 violation=1；没有真实观测前只能写“登记经理意向，尚无法判定”。 |
| B-10 | `zg361pp.5151`：events :4563-4595；复用 loc `zg361_feedback_promotion_pip_l_simp_chinese.yml:12-13,43-44` | 当事人被要求“确认收到并同意/保留异议”，正文却是经理/实现说明，不展示档位、理由、证据、送达人或申诉期限；这是无内容签字。 | 新建独立 `.5151.t/.desc`，列明冻结档位、理由、证据摘要、经理和 90 日期限；“确认收到”与“同意内容”必须分离。 |
| B-11 | `zg361pp.189`：events :4179-4295，loc :233-237，生成器 :1535-1563 | A 只说系统会在二次 PIP/调岗中择一路，玩家点击前不知道结果；受 B-08 影响，category 恒 0，A 当前恒退化为二次 PIP。 | 拆为条件互斥且结果明确的“调往 [receiver] 门下”和“开启二次 PIP”，显示支持、空缺、类别与合法性。 |
| B-12 | `zg361_b1_l_simp_chinese.yml:62-85` 24 条 `#141-#145`；`zg361_b2_l_simp_chinese.yml:24` 的 `PP #157`；`zg361_workforce_probation_fact_l_simp_chinese.yml:3` 的 `Workforce #269` | **26 条玩家可见文本**含未闭合 ASCII `#数字`。项目生成器 `tools/gen_361_mechanisms.py:722-734` 已记录该格式会让 CK3 把后文当格式标记并吞掉。 | 在对应生成源改为“第 141 项/晋升机制第 157 项/第 269 项用工案”等纯文本编号；禁止裸 `#数字`，不要凭空补 `#!`。 |

## 4. High

| ID | 定位与原文摘要 | 问题 | 建议改法 |
|---|---|---|---|
| H-01 | `zg361ch/cp/pp/p3/we` 208 个可见事件；例 `events/zg361_career_hc_runtime_events.txt:5`、`zg361_credit_project_runtime_events.txt:5`、`zg361_phase3_metrics_delivery_runtime_events.txt:5`、`zg361_workforce_endgame_event_001_ab_mechanisms_stage01_03_events.txt:7` | 代码绑定真实 owner/subject，正文却只写“受评者/本案/团队”，不显示姓名、职位、项目、触发原因、冻结事实或当前资源。玩家不知道正在裁决谁的什么事。 | 所有案件固定给出当事人、裁决者、触发原因、当前事实、资源/期限；每个选项写立即代价、后续期限与人物后果。 |
| H-02 | Career/HC 44 卡 `zg361ch.19-25,92-128`；loc `zg361_career_hc_l_simp_chinese.yml:20-239`；模板源 `gen_361_career_hc_runtime.py:2360-2392` | 从晋升资格到强制分布全部使用同一“按证据办/按政治办/延期”，具体事件内容和路线语义丢失。 | 权威模型增加逐项 `desc_cn/route_*_cn`，把 361 目录中的具体决策/后果改写为绑定角色的案件正文。 |
| H-03 | Career/HC IDs 21、25、101、104、112、114、119；event 起点 :163,491,1645,1894,2714,3095,3502；成本源 `gen_361_career_hc_runtime.py:80-83` | 这些选项会同时扣管理者国库 5 和个人金钱 5，UI 完全不披露。 | 在 A/B 选项或 tooltip 直接写明两笔费用的承担者、金额与受益对象。 |
| H-04 | Career Learning 生成器 `gen_361_career_learning_runtime.py:1531-1568` | 22 套机制中仅 314/315/318/319/321/333 有主体事件；其余 16 套自动选择 A。93 个简中 key 中 71 个不可达，汇总也不说明默认选择。 | 玩家需决策的内容应批量呈现；纯自动政策则删除死文案，并在总结中明确默认规则及后果。 |
| H-05 | `zg361cl.318/.319`：events `zg361_career_learning_runtime_events.txt:743,826`，loc `zg361_career_learning_l_simp_chinese.yml:31-38`，权威源 `gen_361_career_learning_runtime.py:79,97` | ROOT 是受评者本人，按钮却是经理动作：“经理超时返还名额”“拒绝后按时放人/全都答应然后全不兑现”。主体和动机错误。 | 拆“经理承诺”与“当事人回应”；当事人按钮改成接受明确条件或拒绝并继续调动。 |
| H-06 | Phase3 统一逻辑 `gen_361_phase3_metrics_delivery_runtime.py:592-599`；例 effect `...aa_m230...:719`、`...aj_m343...:770` | 35/35 个 B 路线都会暗加 `management_debt`，包括“联合对账”“双方各半”“有条件验收”等正常治理方案，文案从未提示。 | 逐机制决定 B 是否真应罚；保留债务时在选项中明确数量和原因，不能统一暗扣。 |
| H-07 | CP `.27/.57/.64` 与 P3 `.304/.310/.343`；生成源 `gen_361_credit_project_runtime.py:515-517,614,678-679`、`gen_361_phase3_metrics_delivery_runtime.py:802-803,867-868,1043-1048` | 玩家一次点击便把其他角色登记为已签署/同意，文案伪造多人主动同意。 | 增加真实回应链；若不实现回应，改成“拟定/责令/登记待签”，不得写“已共同签署”。 |
| H-08 | CP `.29/.61/.62/.67`，P3 `.240/.309/.335/.337/.338/.340/.343`；覆盖源 `gen_361_credit_project_runtime.py:82-89`、`gen_361_phase3_metrics_delivery_runtime.py:69-72` | 描述预告专属第三种业务处置，但 C 已统一替换成普通延期，正文和可选路线不一致。 | 恢复机制专属 C，或同步改写描述，只陈述 A/B/延期三条真实路线。 |
| H-09 | PP 146-191：events :5-4559，loc `zg361_feedback_promotion_pip_l_simp_chinese.yml:19-247`，默认 C 与推进逻辑 `gen_361_feedback_promotion_pip_runtime.py:116-117,2473-2496` | 46/46 正文重复“消费/回写/投影/状态机”；46/46 C 写“延期”，实际立即记债、consume 并推进下一机制，完全不 requeue。 | 实现真正延期，或把 C 改成“放弃本项并转下一项”；将实现术语移至 debug/验收视图。 |
| H-10 | PP 9001-9004：events :7283/7412/7567/7722，loc :248-259，gate `gen_361_feedback_promotion_pip_runtime.py:2722-2738` | 宣称“全部回执、资源和期限已收口”，但仅 185/187/188 阻塞 stage，149/150/151 等 90/180/365 日审计仍在未来，9004 也可能早于 D+30。 | 改为“本轮决策录入完成，后续审计待结算”，另设真正等待所有审计完成的结案卡。 |
| H-11 | PP 146-191 多项：如 149/150 无付款仍按时自动判履约；152 固定 25×4/10；160 固定 80/120；162 固定 365/730；173/177/178 固定分数；191 固定付款 3+2+0+5 | 文案使用“证据、付款、候选、项目、履约”等真实语义，实际多数是固定常量或 flag，并未观察相应人物/资源事实。 | 有数据就显示并据实计算；没有观测口时明确写“政策模拟/登记意向”，不得冒充已发生的业务事实。 |
| H-12 | B2 `.160-.162`：events `zg361_b2_runtime_events.txt:704-806`，loc `zg361_b2_l_simp_chinese.yml:32-36` | 提出异议后，D+90 无证据、听证或复核人便固定 `review_outcome=2`，删除处分；拒签反而 D+7 执行。实质是“一键异议自动胜诉”。 | 增加独立复核、证据与裁决者；或诚实改成“提出异议会自动中止本次处分”。 |
| H-13 | B2 `.40/.50/.131/.160`，loc `zg361_b2_l_simp_chinese.yml:2-36` | 多张卡要求接受、签收、申诉或回应，却不展示改进任务、支持、期限、裁决、新档位、失当事实、证据或拟议处理。 | 每卡补足要被签收的具体材料；信息不足时只能选择“继续补证/保持冻结”，不能要求确认。 |
| H-14 | B2 `.110`：events :255-347，loc :16-21 | 事件 ROOT 是被处分者，却让其自行在延期/降岗/致仕/裁撤中决定并立即执行，没有授权或协商框架。 | 经理先提出处分；当事人只回应接受、申诉或协商。若保留自选，正文必须解释这是可协商方案。 |
| H-15 | 举荐/攻讦 interaction `common/character_interactions/zg361_interactions.txt:132-178`；隐藏 commit guard 在 `common/scripted_effects/zg361_b1_runtime_010_appeal_peer_submission_effects.txt:83-87,153-168,213-305,429-522`；loc `zg361_l_simp_chinese.yml:43-46` | UI 只检查同案同槽；实际还要求同一场有效战争、同阵营、peer mode、未重复。失败可静默 no-op，攻讦仍可能收费/进 cooldown；文案还只说协作±10/15，实际三维同改。 | 把 guard 提升到 `is_valid`/失败 tooltip；no-op 不收费不冷却；写清同战证据、重复限制及三维影响。 |
| H-16 | 夺爵/致仕 interaction `zg361_interactions.txt:193-240`；B2 block `zg361_b2_358_separate_adverse_action_effects.txt:13-29`、`zg361_core_elimination_effects.txt:123-150` | 申诉期内仍显示可点，实际不执行且不给原因。 | 在 UI 阻断并显示“申诉期内不得执行”；或明确登记为待执行队列。 |
| H-17 | 结果说明 decision `zg361_l_simp_chinese.yml:213-216`；`common/decisions/zg361_decisions.txt:41-53`；event `events/zg361_events.txt:356-396` | 文案承诺事实、终档、KPI、送达、回执均可查看，但 decision 只凭 serial/owner 显示；state<3 或 ACL 可隐藏细节。 | 收紧 shown gate，或在文案中明确“依案卷阶段与披露权限显示”。 |
| H-18 | Core `.5.c` events `zg361_events.txt:487-499`/loc :105；`.4.b` events :70-104/loc :98；`.30.a` events :638-647/loc :128 | “再观察一年”在 streak≥3 时其实立即降岗；“三成机会”有质量 bonus 时为 40%；“野狗留用观察”对野狗无任何观察/PIP 写入。 | 使用动态后果提示；补真实观察路径或改文案，不要把条件分支写成固定承诺。 |
| H-19 | Compensation `zg361_generated_compensation_runtime_events.txt:274-306`，loc `zg361_compensation_runtime_l_simp_chinese.yml:3-20`，生成源 `gen_361_compensation_runtime.py:2760-2790,3067-3102` | 一个事件、三枚通用按钮承载 14/15 个不同阶段；没有 subject 姓名，金额、付款人、受益人、期限和当前阶段都不清楚。 | 至少拆成奖金、薪酬调整、长期功赏三类卡；按钮动态显示本阶段金额、双方与到期日。 |
| H-20 | Workforce Endgame 40 主卡 `zg361we.242-277/355/356/360/361`，loc :2-201，模板源 `gen_361_workforce_endgame_runtime.py:374-410`；M264 handoff events `_012...:6-95` | 正文统一“案卷来到标题”，无当事人/现状/原因/数值；C 写“不创建业务对象”。M264 又让 owner 或 subject 共用“提交/拒绝”，责任主体不明。 | 引入逐项 `desc_cn`；按具体岗位/合同/计划写 C；handoff 为两个角色使用不同文案和动作。 |
| H-21 | Workforce AD events `zg361_workforce_ad_fact_runtime_events.txt:6-192`，loc :2-14；attribution signature events :8-88，loc :2-6；remediation events :6-47，loc :2-5 | 内推、表决、Offer、归因签署和整改确认经常不显示候选人、条款、拒绝理由或整改要求，却要求玩家接受/签字。 | 动态显示候选、提名人/评委、岗位薪资、拒绝理由、整改项；无法观测时只允许继续冻结。 |
| H-22 | `zg361_phase2_central_l_simp_chinese.yml:3-5`；`zg361_manager_governance_l_simp_chinese.yml:2-7`；appointment/probation/exit fact loc :3 | 玩家界面直接显示“流水线、成功域、N/A、RED、外部依赖、availability/source serial、九宫格 code、fingerprint、CK3 原生任命、Workforce 回执”等 QA/实现语言。 | 玩家卡改为结论、具体原因、后果和下一步；所有 serial/code/fingerprint/批次号移到 acceptance-only 或 debug 视图。 |
| H-23 | ledger-only HUD `gui/zg361_scoreboard.gui:27` 仍叫“考核榜”，loc `zg361_l_simp_chinese.yml:130-131`；system 页标题/页脚 `gui/...:38,7456-7477,7560`，loc :132/:148 | 制度账本入口称“最近一期官员考核榜”；制度页没有官员行，却固定提示点击官员。界面导航与内容不符。 | 单独使用“制度账本/查看已定案机制及组织影响”；tab 条件化标题与页脚。 |
| H-24 | B1 shadow event `zg361_b1_l_simp_chinese.yml:7-10` 显示代码 1/2/3；榜单 `zg361_l_simp_chinese.yml:163,182-189,245-246` 与 B1 :32,38,44,51,55,57 显示大量 reason/state/receipt/0-1 code | 文案声称“说明”校准与审计，实际把 raw code/boolean 直接交给玩家，无法理解其业务含义。 | 对档位、是/否、送达方式、申诉结果和理由码做中文映射；raw code 仅作为次要审计值。 |

## 5. Medium

| ID | 定位与原文摘要 | 问题 | 建议改法 |
|---|---|---|---|
| M-01 | 明确无运行时/GUI 引用的简中 key 共 161：incident platform 74、Career Learning 71、旧榜单 9、废弃 hidden event 7 | 不会显示 raw key，但这些死文案会虚增“已完成中文内容”统计并增加维护噪声。 | 确认产品路径后删除，或标为测试/未来用途并从玩家内容完成率中排除。 |
| M-02 | 15/21 个生成产品、约 351 个值含企业英文；高频 `HC/PIP/owner/KPI/Offer/sponsor/backfill/Cliff/FIFO/WIP/SLA/toil/onboarding` | 企业讽刺可以保留，但当前多数无首次释义，同一词还有大小写/写法差异。 | 建词表：`owner→责任人`、`Offer→录用邀约`、`sponsor→提名担保人`、`backfill→补岗`、`Cliff→归属等待期`、`Good/Bad Leaver→正常/有责离任`、`FIFO→先进先出` 等；只保留有设定价值且首次释义的缩写。 |
| M-03 | `zg361_credit_project_l_simp_chinese.yml:58`“诚信收执”；全仓还混用 manager/management/上司/leader、回执/确认/收据 | 角色和凭证名不稳定，玩家难以判断同词是否同物。 | 固定角色词：受评官员、直属上司、隔级上司、考核人；固定凭证词：回执=动作确认，收据=金钱支付，案卷=案件记录。 |
| M-04 | `zg361_l_simp_chinese.yml:55` 对 3.5 写“做得很好，继续保持”；`:93` 写“不好不坏，不上不下” | 同一档位评价基调矛盾。 | 统一为中性“完成岗位要求，表现符合预期”。 |
| M-05 | 京察拒办 tooltip `zg361_l_simp_chinese.yml:208`；mandate `zg361_jingcha_mandate_effects.txt:59-67,96-107` | 文案暗示任何上级都会造成好感和下一期 KPI -50；实际只有合格天朝 reviewer 才有 KPI 惩罚，普通上级只有好感。 | 条件化显示后果，或在正文限定“若对方是本期合格考核人”。 |
| M-06 | 5% 决议 loc `zg361_l_simp_chinese.yml:30-32`；script value `common/script_values/zg361_values.txt:361-370` | 未说明向下取整且无最少 1 人；1-19 人的池子实际强制末位为 0。 | 明写“不足 20 人不产生强制末位”，并在 UI 示例显示取整规则。 |
| M-07 | 立即考核 decision `common/decisions/zg361_decisions.txt:11`；loc `zg361_l_simp_chinese.yml:22-25` | 实际还有滚动 1 年 cooldown，文案只说“每个自然年一次”。 | 改为“每次发起至少间隔一年，且每个自然年最多结算一次”。 |
| M-08 | 361 目录标题含编号、章节字母和 P0/P1/P2；如 loc :46“事件窗口/live 值”、:86“玩家/AI 经理”、:151“HC 不是 CK3 角色数”、:301“GUI”、:1766“AI 事件负担” | 作为政策百科概念总体可读，作为人物事件则像设计文档；章节 `AI` 又容易被理解成人工智能。 | 保留为制度百科/驾驶舱条款；正式弹窗只在具体人物或资源冲突时出现。用玩家语言替换开发分类码。 |
| M-09 | 生成器精确重复延期类文案约 576 条（约占生成 key 17.8%）：机制 361、CP/P3 62、PP 46、HC 44、WE 40、CL 23 | 统一语法本身无错，但没有说明延期对象、期限和代价，机械重复放大了“填表”感。 | 保留共享 tooltip；按钮正文按机制写“延期至何时、本轮增加多少债、暂不建立什么”。 |
| M-10 | 1,760 个 option-like loc key 中，>25 字约 431，>30 字 258，>40 字 146，>50 字 3 | 存在 CK3 按钮截断/换行风险；本轮没有实机截图，故只列中风险。 | 重写时把结果摘要放按钮、细节放 tooltip；最终以 5 速实机事件矩阵抽检。 |
| M-11 | 固定 D+1 后继：Career HC 43、Credit Project 23、Phase3 32、PP 28 | 流程能跑，但缺少“上一步结果→为何进入下一步”的叙事连接，玩家会连续数日处理表单。 | 后台合批纯参数步骤；只弹人物回应、资源支付或真正承担后果的节点，并在下一卡承接前一结果。 |
| M-12 | PP `.153/.154/.155/.157/.159/.161/.167/.168/.174/.179/.185/.187/.188/.5166/.5190` | 方向多半与 effect 一致，但缺候选、证据、当前进度、资源、接收经理或代理指标说明；如 `.188`“长期标签”实际固定 365 日。 | 逐卡补角色和当前事实；“长期”改成“一年内任意低档均算复发”；代理变量必须向玩家说明。 |
| M-13 | Compensation `.902/.904`，loc :29-34；生成源 `gen_361_compensation_runtime.py:3097,3101` | 直接显示“可见模式 [数字]”“离任分类 [数字]”；“FIFO 与双付款仍有效”易被理解为重复付款。 | 映射为中文枚举；“双付款”改为“国库与个人两名付款方的约束仍有效”，并说明 70/30 的两个维度。 |
| M-14 | Incident 37 个 `_result` loc，`zg361_incident_platform_l_simp_chinese.yml:10-82`；源 `gen_361_incident_platform_runtime.py:2175-2184` | 静态交叉引用未找到玩家路径；即使启用，内容也只说“冻结 A/B/C、五元回执、送入本领域结算”，没有路线、事故或后果。 | 确认无引用后删除；若要展示，生成具体事故结果、选中路线、债务和下一动作。 |

## 6. Low

| ID | 定位与原文摘要 | 问题 | 建议改法 |
|---|---|---|---|
| L-01 | Career HC loc :66/:166/:216；Workforce Endgame :13/:158/:193 | 六处标题模板形成嵌套中文双引号，如“微职级与“升半级”缓冲”。 | 模板不再给完整标题套外引号，或内层统一用 `‘’`。 |
| L-02 | Career Learning loc :41“把投诉重新分类没”、:75“一名学员同时一个导师”；Phase3 loc :55“采用与价值均衡结算” | 明确病句/漏字。 | 分别改为“通过改类掩去投诉”“一名学员同时只能有一名导师”“采用率与价值均衡结算”。 |
| L-03 | 机制 A/B：ID 1-120 共 240 条有句末标点，ID 121-361 共 482 条无句末标点 | 数据边界处风格突然变化。 | 权威 choices JSON 统一句末标点策略。 |
| L-04 | Career Learning 汇总 loc :3-4：“二十二封弹窗”“日报只写一封” | 量词不自然。 | 改为“二十二个弹窗”“日报只写一条/一份”。 |
| L-05 | `zg361_l_simp_chinese.yml:43-46`：“背靠背互评窗” | 中文通常联想到连续比赛，不能自然表达独立提交。 | 改为“本期独立互评窗口”。 |
| L-06 | Workforce/机制中“二种合同”；`zg361_credit_project_l_simp_chinese.yml:58`“诚信收执” | 量词与用词不规范。 | 改为“两种合同”“诚信回执”。 |
| L-07 | 同一批文案混用“300日/七日/90 日/365 日”，例 `zg361_l_simp_chinese.yml:206,218,221` | 数字、空格和中文数字格式不一致。 | 操作性期限统一为阿拉伯数字 + 空格 + 单位，如 `7 日、90 日、300 日`。 |

## 7. 内容与机制的总体判断

### 7.1 可以保留的骨架

- 核心 `zg361.1-6/10-12/30/40/50/53` 的考核关系相对最清楚。
- B1 的“自评→影子档→逐人公示”、B2 的“送达→PIP→处置→独立新案”、PP 的“反馈→提名→答辩→PIP”流程顺序大体成立。
- 361 机制目录的“决策/后果/A/B”作为制度百科是当前概念最完整的部分，722 条 A/B 没有精确重复。
- Workforce 归因签署能列出三名评委，是当前最接近合格上下文事件的样例。

### 7.2 当前不能交付的核心原因

当前问题不是“中文翻译缺了一些”，而是产品层仍混合了三种不同东西：制度设计目录、自动化验收/状态机日志、真正的人物事件。很多卡在代码中拥有具体 subject，却在文本中把人抹掉；另一些卡又把固定 flag 或模拟常量写成已经发生的付款、证据、签字和履约。最终结果是玩家能看见大量字，但无法回答四个最基本的问题：**谁出了什么事、为什么现在找我、我选什么、选完实际会怎样。**

## 8. 琉焰卿人格边界

简中玩家文案中未发现琉焰卿本人台词、自称或“旅人/典当/垂青/咒痕/余烬”等明确人格入口；本轮因此没有把现代企业讽刺文本强行改写成琉焰卿口吻，也没有发现可判定的人格违规。后续若新增琉焰卿 narrator，必须遵守项目设定：温柔有礼、诱惑性强、恶意隐于措辞，不可直白自曝恶劣。

## 9. 权威修改入口

生成文件不得直接手改。建议按以下入口施工：

| 内容 | 权威入口 |
|---|---|
| 361 标题/说明/决策/后果 | `docs/361-expansion-options.md`，由 `tools/zg361_mechanism_data.py:187-225` 解析 |
| 361 A/B 选项 | `tools/mechanism_choices/choices_*.json` |
| 361 公共文本和 C | `tools/gen_361_mechanisms.py:580-660` |
| 榜单快照与 GUI 投影 | `tools/gen_scoreboard_snapshot.py` |
| B1/B2/HC/CL/CP/PP/Compensation/P3/Workforce | 各自 `tools/gen_*_runtime.py` / `tools/gen_zg361_*_fact.py` |
| 手写核心 loc | `localization/simp_chinese/zg361_l_simp_chinese.yml` |

## 10. 建议整改顺序与验收门槛

1. 先修 B-01 至 B-12：伪造离任档、无 consumer、永久锁死、反向账本、比例/京察/立即开榜虚假承诺、PP 不可达路径、裸 `#`。
2. 接着修所有主体与知情选择：HC、CL、PP、B2、Compensation、WE、Workforce AD。
3. 清除玩家层 QA/实现词，并为 raw code/boolean 建中文语义映射。
4. 修复隐藏费用、统一管理债、自动代签、被删除的 C 路线和 interaction 静默 no-op。
5. 再做术语、死 key、按钮长度、病句、引号和时间格式收口。
6. 生成器重建并跑现有静态检查；增加三类静态回归：玩家 loc 禁止裸 `#数字`、选择文案/effect 契约、可见案件必须引用 subject/case fact。
7. 最后进入 CK3 实机：默认 5 速，以“同一次启动连续跑不依赖代码变更的场景”为原则，抽检长按钮、动态角色名、条件 tooltip、实际扣款/债务/转岗/申诉/公示结果。仅修改文案或夹具时不应为每个场景重复启动 CK3。

通过中文内容验收至少需要满足：Blocker=0、High=0；所有可见案件能回答“人物—前因—选择—后果”；文案承诺与 effect/consumer 一致；静态 raw key 和格式标记检查 GREEN；随后保留一轮完整 5 速实机证据。

## 11. 本轮未做的事情

- 未启动 CK3，未取得视觉截断或动态渲染截图；M-10 只能判风险，不能声称 live RED。
- 未修改任何产品代码、本地化、生成器、日报、周报或 coverage ledger。
- 未补写其他语言；日常开发仍以简中和英文为范围，本报告只以简中为基准。
- 未触碰当前 R104 工作文件；本文件是唯一新增审计产物。

## 12. R105 整改复核（2026-09-06；结论已被 R106 实机推翻）

本节原先把首轮批量整改误记为 **Blocker 0/12、High 0/24**。R106 首次实机显示
`zg361cl.314` 后，玩家截图直接证明该结论不成立：标题仍是制度口号，正文仍在解释 scope/权限，按钮仍有
“有钱的调任包”“绩效锅”等网络化、含混措辞。原审计其实已在 H-01/H-04/H-05 点名 Career Learning
缺少处境和主体错位；整改只修了部分按钮与死 key，却没有逐卡复核生成后的玩家可见成品。下面的清单只能
视为 R105 当时完成的改动，不能再作为“全量文案 GREEN”证据。

- B-01 至 B-12：修复离任快照污染、机制 84 反向账本、严格/宽松配额取整、京察/立即考核虚假承诺、
  PP 151/181/186/189 的不可达或假流程、未接业务机制的虚假可执行措辞，以及玩家文案中的裸 `#数字`。
- H-01 至 H-24：事件正文补入可用的当事人、裁决者、阶段和边界；把 ledger-only 机制明确写成政策配置；
  B2 申诉改为独立复核，处分改为协商回应；移除代签/共同同意式措辞；举荐、攻讦和不利处分把真实 guard
  提到交互可见层且 no-op 不收费；薪酬与 Workforce 结果卡改为业务枚举和具体责任主体；玩家卡移除
  `RED/N/A/fingerprint/流水线` 等验收术语。
- M/L 静态整改：删除 Career Learning 71 条、Incident 74 条及核心榜单/废弃 carrier 的死文案；统一
  `HC/PIP/owner/KPI/Offer/sponsor/backfill/Cliff/FIFO/WIP/SLA/toil/onboarding` 的玩家中文；统一 3.5
  中性评价、期限格式、“两种合同”“诚信回执”、中文嵌套引号和 361 A/B 句末标点。术语归一器保护
  `[...]` 内的 CK3 scope/变量，不改写脚本标识。
- 可复核静态证据：所有受影响生成器 `--check` GREEN；`validate_local.py` GREEN；
  `py -m unittest discover -p "test*.py"` 共 **1655 项 GREEN**。发布本地化因删除 6 个 core 死 key，
  冻结合同同步为 **2085 keys / 18 batches**。

R106 证明遗留项不止按钮换行/截断：至少 Career Learning 六张主体卡及一张汇总卡仍有已知静态文案错误。
因此本报告恢复为 **RED**；在逐项整改账、生成成品复核和新一轮 5 速实机都完成前，不再给出 Blocker/High
归零声明。

## 13. R106 `.314` 实机 RED 与审计流程纠正（2026-09-06）

- 证据：R106 在 1,107 游戏日、279 次 paused native/MCP 观测和 123 次精确事件处理后停在
  `zg361cl.314`；用户提供的实机截图显示旧标题、公共权限模板和两枚不合格按钮。旧产品在点击前保持暂停，
  没有把文案 RED 误计为机制验收通过。
- 漏检链：H-01/H-04/H-05 已写入原审计 → R105 只对 `.318/.319` 按钮、死 key 和公共模板做机械修改 →
  原测试反而断言公共模板必须存在 → 复核没有逐张读取最终简中 YML → 报告按问题簇整批销账。
- 当前整改：六张主体卡改为六段独立中英文处境，明确期限、费用/配额、退出条件与实际后果；`.319` 明写
  route B 当前会在 90 日后按失约结案；汇总卡移除“机制合批、证据路线、业务回执、状态报告”等流水线语言。
- 新门禁：独立 `test_zg361_career_learning_copy.py` 检查六段正文互不复用、关键利害完整，并禁止旧公共模板、
  “有钱的调任包”“绩效锅”及开发合同语言回流。结构测试不再把公共模板的存在当作 GREEN。
- 口径：静态测试通过只说明本组生成与规则合同成立；修改后的玩家成品必须由 fresh product 在 5 速下再次
  到达并人工阅读，才能把本组文案提升为实机 GREEN。其他审计项继续按单项证据关闭，不再批量销账。

## 14. R107 全量销项状态复核（2026-09-06）

- 明确结论：当前**没有修完**本报告列出的全部问题。commit `275ee65` 只重写了六张 Career Learning
  主体回应卡和一张汇总卡，最多只能部分覆盖 H-04/H-05；它不能证明 12 个 Blocker、24 个 High 已归零。
- R107 的 937-file release-identical 产品完成 303/303 loader、fatal 0；同一 CK3 PID 在默认 5 速下累计
  推进 918 游戏日，取得 221 次 paused native/MCP 观测和 68 次精确事件处理，并完整经过 44 张
  Career/HC 卡。这个结果只证明事件链可加载、可执行，同时也证明 H-01/H-02/H-03 所指模板卡仍在正式产品路径上。
- R107 尚未再次到达并人工阅读上述六张已改 Career Learning 卡，因此它们当前只有静态生成与加载字节证据，
  不能记作视觉文案 GREEN。后续实机已暂停，先完成本报告逐项整改与最终简中成品复核。
- 本轮同时冻结了 recurring `.1` 的四种精确 scope 形态，以及资源充足/不足时双成本选项的原生投影差异；
  这些属于验收夹具修正，不属于文案审计销项。

## 15. 重新生成的逐项整改账（基线 `275ee65`，2026-09-06）

本节推翻 R105 的批量销账，状态只按当前生成器、最终简中 YML 和运行逻辑逐项复核。`部分修复` 与
`待复核` 一律按**未闭合**处理；没有最终成品复读与新一轮实机视觉证据，不得改成 GREEN。

### 15.1 Blocker

| 状态 | 项目 | 当前证据或剩余边界 |
|---|---|---|
| 已修复 | B-01～B-07、B-09、B-12 | 非离任档、consumer 口径、永久搁置、84 号账本、比例/立即开榜/京察、PP 186、裸 `#数字` 已按当前生成物与逻辑复核。 |
| 部分修复 | B-08、B-11 | PP 仍把 reason 5“被强制分布压档”伪映射为岗位错配，并据此开放真实调岗；必须接真实错岗事实，缺失时保持未知并只允许二次改进。 |
| 部分修复 | B-10 | `.5151` 已分离“收件”与“同意”，也显示角色、档位、期限；仍只显示原始理由编号与证据数量，必须改成可读理由和证据摘要。 |

统计：**已修 9/12；未闭合 3/12**。

### 15.2 High

| 状态 | 项目 | 当前证据或剩余边界 |
|---|---|---|
| 已修复 | H-03、H-05～H-07、H-09、H-14～H-18、H-23 | 已复核费用披露、主体错位、隐藏管理债、代签措辞、PP 路线 C、B2 处分主体、interaction guard/no-op、核心动态后果和制度账本标题。 |
| 部分修复 | H-01、H-02 | Career/HC 44、PP 46、Workforce Endgame 40 虽已补角色和独立 A/B，但正文仍共享标题复述/流程模板，缺当前事实、触发原因和资源冲突。 |
| 部分修复 | H-04 | Career Learning 死 key 已清，但 16 个后台自动项仍未在汇总中披露默认规则和实际后果。 |
| 部分修复 | H-08 | CP/P3 若干正文仍预告已经不存在的第三种业务路线，而真实 C 是关闭本项并记债。 |
| 部分修复 | H-10 | PP 后续审计已不再冒充完成，但 9001～9004 标题仍声称“案卷已结”。 |
| 部分修复 | H-11 | 多张 PP 卡仍把固定模拟常量写成真实付款、候选、履约或业务事实。 |
| 部分修复 | H-12 | B2 异议不再自动胜诉，但仍由系统在 90 日后凭旧 flag 裁决，正文却声称有在位复核人实施独立复核。 |
| 部分修复 | H-13 | B2 `.50` 不显示裁决结果/证据；`.160` 不显示新低档事实和复核人。 |
| 部分修复 | H-19 | 薪酬卡已有阶段正文，仍由一张卡和三个通用按钮承载全部阶段，金额、付款人、期限未落到按钮。 |
| 部分修复 | H-20 | M264 已修；其余 40 张 Workforce 主卡仍复用公共模板，并把“业务对象”等实现词放给玩家。 |
| 部分修复 | H-21 | 面试无证据仍可判充分、录用邀约无条款仍可接受、整改没有新旧条款仍可确认完成。 |
| 部分修复 | H-22 | 仍有“第 269 项消费结局”“原生职业槽”等实现语言；经理卡声称说明理由却只给理由数量。 |
| 部分修复 | H-24 | 影子档、榜单枚举、布尔值、理由和部分回执仍直接显示原始数字。 |

统计：**已修 11/24；未闭合 13/24**。

### 15.3 Medium / Low 与本轮新增问题

- Medium 已修复：M-01、M-03～M-07、M-13、M-14，共 **8/14**。死 key、凭证词、3.5 档口径、
  京察条件、比例/冷却说明、薪酬枚举和 Incident 死文案已经复核。
- Medium 部分修复：M-02、M-08、M-09、M-12，共 **4/14**。残留点分别是未首次释义的 PIP/KPI，
  361 正文中的 CK3/GUI/live/P0 等设计稿语言，数百条重复搁置模板，以及 PP 缺候选、证据、进度和接收人。
- Medium 未修复：M-10、M-11，共 **2/14**。1,752 个同类按钮中仍有 880 个超过 25 字、773 个超过
  30 字、446 个超过 40 字、165 个超过 50 字；HC/CP/P3/PP 的固定次日表单链也尚未合批或建立叙事承接。
- Low 已修复：L-01～L-07，共 **7/7**。嵌套引号、病句、句末标点、量词、术语和期限格式已逐项复核。
- N-01（未修）：运行时可为空的动态前缀后直接拼接句号，导致玩家所见正文以“。”开头；同时存在正文复述标题、
  只说明“案卷来到当前节点”的无价值模板。
- N-02（未修）：多组正文先替玩家概述路线甲/乙或列出决策内容，按钮却只写“按甲/按乙/按证据办/按政治办”；
  决策语义没有落在按钮，玩家无法从按钮本身确认将要执行的动作。

原审计 57 簇当前合计：**已修 35、部分修 20、未修 2**。加入本轮 N-01/N-02 后为：
**已修 35/59、未闭合 24/59**；其中“部分修复”也计入未闭合。

### 15.4 恢复实机前的新增硬门禁

1. 全量扫描玩家可见简中正文：禁止以句号、逗号、分号、冒号、叹号或问号起头；禁止动态前缀为空后留下孤立标点。
2. 正文不得复述标题凑字，也不得用“案卷来到……、路线甲乙会……”替代案情；必须说明人物、已发生事实、触发原因和当前利害。
3. 每个可执行选项的按钮必须独立说清动作与主要代价/后果；禁止只写“按 A/按 B、路线甲/乙、按证据/政治办”。
4. 正文可以解释背景和共同约束，但不能代替按钮列出玩家将执行的不同选择。
5. 以上规则必须写入自动化 copy gate，并对生成后的简中 YML 运行；随后逐卡复读所有受影响家族。
6. 只有 B/H/N 全部闭合，M/L 完成重查且最终生成物门禁 GREEN 后，才允许 fresh product、默认 5 速的 CK3 实机复验。

## 16. 第一轮已修 / 未修清单（2026-09-06；已由第 17 节交叉复审替代）

本节记录第一轮并发整改后的生成树；第 17 节随后又由独立复审追回并修复漏项，因此本节数字只保留为
过程证据，不再代表当前最终树。结论严格拆成两层：
已知文案/逻辑缺陷已经静态闭合；动态渲染、换行与真实 scope 仍必须由 fresh product 实机确认。

| 级别 | 静态已修 | 静态未修 | 当前边界 |
|---|---:|---:|---|
| Blocker | 12/12 | 0 | B2 理由/证据、独立复核、真实错岗条件、资金与处置路径已复核 |
| High | 24/24 | 0 | 各家族案情、人物、按钮动作、scope、付款/期限、枚举与业务承诺已复核 |
| Medium | 14/14 | 0 | 缩写/实现术语、重复模板、按钮长度和固定 D+1 表单噪声已闭合 |
| Low | 7/7 | 0 | 病句、引号、量词、期限与标点格式已闭合 |
| 新增 N-01/N-02 | 2/2 | 0 | 动态/标点句首、标题复读、正文越权写选择、空泛按钮已设产品级门禁 |
| **合计** | **59/59** | **0** | **STATIC GREEN；LIVE PENDING** |

### 16.1 本轮关键整改

- Career/HC、PP、Workforce Endgame、CP/P3 与 Career Learning 的公共模板改为逐案事实；正文只交代人物、
  前因与利害，按钮独立说明动作和主要后果。
- PP `.5166/.5190` 改用 subject 专属正文与 `zg361_pp_subject_prompt_*` scope；经理 `.166/.190`
  保持 manager prompt scope，避免本人事件出现空名或旧人物。
- 补偿 14 个阶段的金额、付款方、期限与归属结果落到按钮；总报酬 45/37 与其中本阶段奖金 20/16、
  国库/私库拆分不再混写。最终按钮长度均不超过 48 个静态中文字符。
- B1/B2、`received`、PIP、OKR、HR、ID、cohort、PPT、`vs` 等内部阶段词或未释义缩写均已改为
  当前界面内可理解的中文业务语义。
- HC、CP、P3、PP 增加每轮一次办案方式选择。统一办理只覆盖冻结的低风险白名单，仍逐项调用原
  core/consumer/deadline/receipt；guard、依赖或资源不足时精确恢复原编号卡。付款、本人回应、人物去留、
  限期复核与最终结算继续逐案呈报。
- effect 继续按用途分片：本轮全局边界检查未发现超过 20 个 effect 的文件；相关生成器目标仍为每片 1–10。

### 16.2 最终静态复审证据

- 最终简中：22 个 YML、5,002 个 key。
- 标点或动态表达式起句：0；正文精确复述标题：0；“案卷来到/当前节点/本卡”空模板：0；
  正文枚举 A/B、路线甲乙或“按证据/政治办”：0。
- 未释义企业英文及玩家可见的 B1/B2/`received` 内码：0。剩余 Latin 仅为已附中文释义的
  `Stay Interview` 与业务档位 B/C。
- 产品级 `test_zg361_chinese_copy_quality.py`：普通与 `-O` 均 15/15 GREEN。
- 完整 mod discovery：普通与 `-O` 均 1,724/1,724 GREEN；`validate_local.py`、根级
  `tools/validate_static.py`、release reproducibility 与 `git diff --check` 均 GREEN。

### 16.3 实机待验收项

以下只代表 **LIVE PENDING**，不把它们重新记成静态“未修”：

1. fresh 945-file product 在默认 5 速下完成 303/303 loader、fatal 0，并抽检动态人物名、事实、金额、期限与按钮渲染。
2. 重点到达 B1/B2 申诉、PP `.5166/.5190` 本人回应、PP `.181/.186/.189`、补偿 14 阶段及互动可见性。
3. 核对 HC/CP/P3/PP 合批后的实际窗口数量、关键案保留和 guard 失败时精确回退。
4. 复验 Career Learning、Workforce、结果说明与 scoreboard 的布局、换行和枚举映射。
5. 在真实动态 scope 下确认 N-01/N-02 没有孤立标点、空名字或按钮截断；取得截图、native/MCP snapshot、
   error/debug log 与 hash-bound artifact 后，才把本报告提升为最终 LIVE GREEN。

## 17. 并发逐 key 复审与最终静态销账（2026-09-06；阶段状态，已由第 18 节替代）

用户指出原复审仍有明显漏网后，本轮不再按一条总流水线串行处理，而是按 PP、HC/Career、CP/P3、B1/B2、
Career Learning、Compensation、Workforce/Endgame、Incident/Governance/Central、机制目录和 core/scoreboard
拆成互不覆盖的修改包，并另设两个只读复审包交叉验证最终生成物。只读复审实际追回了三类原门禁未覆盖问题：

- M-01 的 161 个死本地化：Incident 74、Career Learning 71、旧榜单 9、hidden carrier 7，现为 161/161 清除；
- Career Learning 总览仍残留“第一项 / 不另开窗口”等实现口吻，以及 #314/#321 未完整披露真实付款方；
- Workforce `.244/.273/.360` 的标题被模板再次套入中文引号，形成嵌套引号。

以上问题均从权威生成源修复并加入禁止回流测试；PP `.9001–.9004` 也从公共结案模板拆为 T/U/V/W
四套独立正文和归档动作。最终只读复扫不沿用旧销账结论，得到：

| 级别 | 已闭合 | 未闭合 |
|---|---:|---:|
| Blocker | 12/12 | 0 |
| High | 24/24 | 0 |
| Medium | 14/14 | 0 |
| Low | 7/7 | 0 |
| N-01/N-02 | 2/2 | 0 |
| **合计** | **59/59** | **0** |

本节当时的阶段树包含 22 个简中 YML、4,970 个 `zg361` key、85 个事件文件、635 个 visible event 和 372 个 hidden
event；这里的 **1,007 个事件只是该阶段的历史计数**，不能继续当作当前 inventory。3,237 个 visible-event 唯一 loc 引用、230 个 GUI loc 引用、7 个决议的 28 个 loc 引用、6 个互动的
14 个 loc 引用均无缺失。产品门禁覆盖 796 个 body 与 1,849 个 option；标点或动态表达式起句、标题复读、
正文枚举路线、正文逐字复制按钮、抽象 A/B/“按证据办”按钮、玩家可见实现/UI 术语均为 0。Unicode 引号栈
扫描为 0 嵌套、0 不平衡。

合并后完整 discovery 在绑定已更新且 clean 的 `Z:\workspace\xar_promo_toolchain` 后，普通与 `-O` 均为
1,755/1,755 GREEN；promotion source runner 普通与 `-O` 均 50/50 GREEN；`validate_local.py`、根级
`tools/validate_static.py` 与 `git diff --check` GREEN。normal/`-O` discovery 必须串行：部分生成器测试会在
产品目录临时创建“应被拒绝的旧单体文件”，两进程并发会互相看见对方的临时残留并产生 harness-only RED。

### 17.1 R108 实机证据与停止理由

R108 的 945-file release-identical product 已完成 303/303 loader、fatal 0；同一 CK3 PID 69184 在默认 5 速下，
由初始客户端及五个 replacement client 累计推进 508 游戏日、完成 206 次 paused native/MCP 观测与 50 次精确
事件处理，全程没有重启，也没有 OCR。过程中确认新的 HC 办案方式卡、14 阶段补偿卡、PP 办案方式卡及多种原版
事件 scope 变体均可加载和执行。

R108 最终停在 `zg361pp.149`，原因是专用 source-checkpoint runner 在 `.9100` 选择了自动合批 A，而旧合同仍等待
已由 A 正常后台办理的 `.146/.147`；这是验收夹具与新产品流程不一致，不是 MOD 功能 RED。runner 已改为在该专用
采集场景选择逐案 D，使 `.146 option 1 → D+1 .147` 保持可达。随后本轮文案修复改变了 MOD 字节，旧进程不再能
代表修复后产品，因此通过受管停止队列正常回收；下一轮使用 fresh R109 product，只启动一次 CK3，并在同一未改
MOD 的进程内继续多个验收场景。

本节结论仍是 **STATIC GREEN / LIVE PENDING**。动态人物、金额、期限、按钮换行、合批顺序与 guard fallback 必须在
R109 默认 5 速实机中完成，不能用本节静态结果冒充最终 live GREEN。

### 17.2 effect 数量与字节体量双门（2026-09-06）

文案整改完成后又对全部 scripted-effect 文件做了 brace-depth=0 复扫，并把文件体量由经验项提升为静态硬门：
每文件目标 1–10 个顶层 effect、原则上不超过 20，且单文件不得超过 200 KiB；即使文件只有一个顶层 effect，
超过字节门也必须继续抽取用途 helper，不能豁免。

本轮并发修复了 HC 生命周期、Compensation portfolio、Incident Z、PP T/U/V/W、scoreboard 与 Workforce M360：

- 删除 5.48 MB 的 scoreboard 聚合 owner，改为 65 个同用途片、77 个顶层 effect，最大 125,044 bytes；
- 删除四个 319–479 KB 的 Workforce owner，改为 validation、cleanup、materialize、business 与 public
  orchestration 用途片，新 M360 分片最大 98,364 bytes；
- Compensation 29-effect owner 改为 5 个单职责单-effect 文件；Incident 两个 11/12-effect owner 改为
  4 个各 3-effect 文件；HC P lifecycle 改为开案、AI runner、五阶段和结案片；
- PP 修正生成器中嵌套分支的错误顶格输出，39 个分片现在均为 2–10 个真正的顶层 effect。

最终全局结果为 **713 files / 3,813 effects / target miss 0 / `>20` 0 / `>200 KiB` 0 / max 10 effects /
max 130,221 bytes**。旧 owner 的 active consumer 也已同步迁移：scoreboard 统一使用 canonical shard reader，
Incident CMake source-contract 改读四个新片，Workforce 两个 preflight 与 source-contract fixture 改读新的
business/public 片；历史 hash-bound artifact 保留原路径，只作为历史证据。该门禁及测试夹具隔离规则已经写入
`docs/testing-workflow.md`。

### 17.3 R109 实机 RED 与 Workforce 参数精确修复

R109 fresh product 在默认 5 速下完成了 **303/303** 个 loader node，但 `debug.log` 出现 **7 条错误、归并为
2 个唯一 helper 签名**，因此本轮明确记为产品 loader RED。错误均为 `Scripted effect should have no arguments`：
无参 `zg361_we_m360_materialize_cleanup_effect` 与无参
`zg361_we_m360_route_b_validate_collective_step_2_effect` 被机械传入四个 ticket 参数。本轮未进入 gameplay，
全程未使用 OCR；发现 loader RED 后通过 managed stop 正常回收进程，不能把 303/303 单独写成实机 GREEN。

根因是 Workforce 生成器原先把 `TICKET_OWNER / TICKET_SUBJECT / TICKET_CYCLE / TICKET_CASE` 无条件转发给
所有新 helper，而 CK3 只接受被 callee 正文以 `$ARG$` 实际消费的参数。修复后，生成器直接从每个 helper
definition 推导实际占位符集合：有参数时只传完全匹配的 named args，无参数时生成裸 `helper = yes`；静态合同
覆盖全部 16 个新 helper 及其所有调用点，不是只对日志中的两个样本打补丁。该改动只校正调用 ABI，没有改变
Workforce 的业务顺序、写入和玩家文案。

修复后静态结果：Workforce runtime 普通模式与 `-O` 各 **123/123 GREEN**，boundary 普通模式与 `-O`
各 **6/6 GREEN**，generator `--check`、B4/B6 回归与 `git diff --check` 均 GREEN；全局 effect 边界仍为
**713 files / 3,813 effects / `>10` 0 / `>20` 0 / `>200 KiB` 0 / max 10 effects / max 130,221 bytes**。
因此当前结论是 **R109 LIVE RED 已定位，参数修复 STATIC GREEN，修复后 LIVE PENDING**；必须由下一次 fresh CK3
loader 将这两类签名归零后，才恢复后续 gameplay 文案验收。

### 17.4 R110 实机续跑、失效 seed 与四类运行时修复

R110 fresh product 完成 **303/303** 个 loader node，fatal 0；R109 的两类
`Scripted effect should have no arguments` 签名均归零，因此本轮 loader 为 GREEN。首次 gameplay 客户端在
`zg361.6` 的 exact saved-scope 清单上报 harness RED：窗口本身、玩家 root 和可用选项均有效，只是合同尚未纳入
当前谱系新增的 self/shadow ticket scope。修正纯验收合同后，续跑复用同一 CK3 PID **112096**、同一 pipe 与同一
episode，没有重启游戏。

续跑对已在窗口中的 `.6.a` 选择“最后申诉”；该路线只有 40% 改判机会，本次随机失败。`debug.log` 随即明确记录
`elimination -> purge (title stripped)` 与 `final appeal rejected, purged`。玩家 `29037` 没有死亡，也没有发生
继承或角色重绑定，但已失去全部 landed title，因此该 seed 不再具备后续晋升/B1 验收资格。之后 Central 从 true
转为 false、再等待 550 日仍未出现新 B1，不能解释为产品晋升链卡死；resume 报告中的 observation-bound RED 是
失效 seed 上继续观察的场景结果。

独立按首次客户端冻结日志与 live append-only 日志的字节边界复核，resume 增量共有 **41,958 条产品归因运行时
错误记录**，归并为四域：

1. Core/B2 淘汰 option tooltip 在预求值时没有提交前置 prepare effect，却直接读取
   `zg361_b2_adverse_action_allowed`；unset variable、unset `var` scope、invalid comparison 三种签名各
   **13,976** 次，共 **41,928** 条。
2. Central 汇总正文的四个 `ROOT.Var(...)` 不是合法的事件本地化数据表达式，产生 8 条 data-function 转换错误和
   1 条 `zg361_p2c_summary_desc` data error，共 **9** 条。
3. Career Learning 的 M317/M329 在冻结 owner 已死亡后仍执行 `add_opinion`，两个路径各 10 次，共 **20** 条。
4. Career/HC transfer vacancy guard 在 landed-title 内层 scope 用 `holder = this`，造成 character 与
   landed_title 类型比较错误 **1** 条。

四域静态修复现已落盘：淘汰四路线用 lazy `has_variable` 边界读取 scratch 值；Central 九语言生成源改用
`ROOT.MakeScope.Var(...).GetValue`；Career Learning 所有 relationship consumer 在写 opinion 前验证冻结 owner
存在且存活；Career/HC 四处 title-holder guard 改为引用外层角色的 `holder = prev`。对应生成源和回归断言已同步，
但这些改动尚无修复后 live 证据，不能把 STATIC 修复记成运行时归零。

R110 全程使用默认 **5 速**，没有 OCR；失效谱系审计完毕后已通过 managed stop 回收，未让旧产品进程继续承担
修复后验收。当前状态为 **R110 loader GREEN / gameplay seed invalid / 四域修复 STATIC GREEN / LIVE PENDING**；
下一步必须由 **R111 fresh product** 重新验证 303/303 loader、上述 41,958 条签名归零，并从仍有地且具备资格的
玩家谱系完成晋升链与文案实机验收。

### 17.5 最终文案复审改为宽并发后的追补整改（阶段状态，已由第 18 节替代）

用户再次指出“正文替按钮做决定”和“正文以孤立标点起句”属于可并行清理的问题后，调度改为八个互不覆盖的
文件族并发：PP、Career/HC、CP/P3、Workforce、Career Learning/Compensation、B1/B2/core、
Incident/Manager/Central、361 mechanisms。各包只修改自己的权威生成源、生成产物与专项测试；共享的全量
discovery、根级校验、release 构建和 CK3 启动继续串行。该轮没有沿用第 17 节的“59/59 已闭合”结论，而是
重新逐 key 复读最终简中成品，追回并闭合以下漏项：

- Career/HC：6 个 key；批量办理口径不再掩盖“关系优先”，并消除“材料已送齐却让按钮再次提交”、
  “强留或降级”等矛盾或不确定动作。
- Career Learning：5 个按钮；补清只收存回执、不新增付款/期限，以及 20 金、6 金、90 日和 18 金追偿边界。
- Incident：3 段正文补入真实受评人和下一轮利害，1 个归档按钮补入下一轮核算后果；交叉复核曾拦截一处
  `[scope:<saved>.GetShortUIName]` 错误回流，最终使用已由 R116 实机证明正确的
  `[<saved>.GetShortUIName]`。
- Credit/Project 与 Phase3 Metrics Delivery：74 条生成文案；删除产品没有记录的“亲自签字/同意/回应”，
  把小时、槽位、份额、释放/保留及主要代价落到按钮，删除 P3.343 并不存在的“跟进债”。
- 361 mechanisms：9 段正文删除路线/选择元叙述；722 个 A/B 按钮补入对应真实账本的主要收益和成本，
  361 个 C 按钮及 361 个 C tooltip 明示“制度债 +3、行政负担 -1”。
- PP、Workforce、Compensation、B1/B2/core、Manager/Governance 与 Central 逐卡复读没有发现新的
  N-01/N-02 产品文案；Workforce 仍新增 43 个可见事件、46 个正文变体和 132 个按钮的逐卡防回流门禁。

本轮新增追补共 **1,542 个生成 key 行级闭合项**；不是把旧 59 簇重新计数。该阶段曾记录原 59 簇
**59/59 静态闭合、未闭合 0**，新增追补项 **1,542/1,542 静态闭合、未闭合 0**；但后续复审又追回
39 个简中 key、18 个问题簇，因此这里的“未闭合 0”已经过时，只能作为历史阶段结果。动态布局和实际 scope
渲染始终保持 **LIVE PENDING**，不得用静态结果冒充实机 GREEN。

合并后的专项矩阵 normal/`-O` 全部 GREEN。第一次全量 discovery 为 1,740/1,780，并准确暴露 Workforce
旧测试仍强制错误的 `[scope:<saved>.GetShortUIName]`；产品没有被改回错误语法，测试改为要求正确形并显式
拒绝旧形。重跑后 normal 与 `-O` 均为 **1,780/1,780 GREEN**；`validate_local.py`、根级
`tools/validate_static.py`、release deterministic `--check` 与 `git diff --check` 均 GREEN。effect 双边界仍为
**713 files / 3,817 effects / target miss 0 / `>20` 0 / `>200 KiB` 0 / max 10 effects / max 130,221 bytes**。
上述门禁完成前没有恢复 CK3 点击或启动。

## 18. 可复现账本与最终已修 / 未修清单（基线 `7778b67`，2026-09-06）

本节替代第 16、17、17.5 节的阶段性“当前状态”。机器可复现证据为
[`zg361-copy-ledger/index.json`](zg361-copy-ledger/index.json)：账本由提交 `7778b67` 纳入版本库，输入快照绑定
最后一次修改事件/本地化产品的提交 `6db27be`。账本当前记录 4,999 个最终本地化 key、1,009 个事件定义
（635 visible、374 hidden）、844 个可见正文绑定和 1,856 个可见按钮绑定；`machine_failure_count = 0`，
`machine_failures = []`。因此第 17 节的 635 visible + 372 hidden = 1,007 只能解释为旧阶段计数。

### 18.1 §17.5 后追回的 39 个 key / 18 个问题簇

下表逐簇记录最终状态；“2 个 key 删除”同样计入 39 个受影响简中 key，但不再存在于最终 4,999-key 产品中。

| # | 问题簇 | 受影响简中 key | 数量 | 修复提交 | 最终状态 |
|---:|---|---|---:|---|---|
| 1 | B1 结果正文复读标题事实 | `zg361b1.126.desc` | 1 | `1d2fb8d` | 已修 |
| 2 | 关闭设置说明只复述标题、没有实际边界 | `setting_zg361_off_desc` | 1 | `1d2fb8d` | 已修 |
| 3 | 试任结局正文与按钮都是无信息模板 | `zg361wpf.2.desc/.a` | 2 | `1d2fb8d` | 已修 |
| 4 | PP 166 按钮把“继续预审”误写成“劝候选硬上” | `zg361pp.166.b/.b.tt` | 2 | `cdee586` | 已修 |
| 5 | PP 181 按钮用证据免责声明代替实际动作 | `zg361pp.181.a/.a.tt` | 2 | `cdee586` | 已修 |
| 6 | PP 187 两路按钮解释系统权限而不说明选择 | `zg361pp.187.a/.b/.a.tt/.b.tt` | 4 | `cdee586` | 已修 |
| 7 | Manager 220 “照所列事项续办”动作空泛 | `zg361mg.220.a` | 1 | `cdee586` | 已修 |
| 8 | HC 六张卡复用“归档。下轮再见。” | `zg361ch.901.a`～`zg361ch.906.a` | 6 | `cc52566` | 已修 |
| 9 | Workforce 246 标题、正文和按钮没有写明五日工时及兑现值 | `zg361we.246.t/.desc/.a/.a.tt/.b` | 5 | `8045e4c` | 已修 |
| 10 | Workforce 259 tooltip 暴露原始 C 档码 | `zg361we.259.b.tt` | 1 | `8045e4c` | 已修 |
| 11 | Workforce 276 tooltip 暴露原始 `3.25` 档位值 | `zg361we.276.b.tt` | 1 | `8045e4c` | 已修 |
| 12 | Workforce 360 标题使用“硬背 C”内部口吻 | `zg361we.360.t` | 1 | `8045e4c` | 已修 |
| 13 | B2 50 标题与正文重复“申诉驳回”，没有交代最后举证利害 | `zg361b2.50.t/.desc` | 2 | `b6f194a` | 已修 |
| 14 | PP 本人回应卡没有独立标题，主体/动作不清 | `zg361pp.5166.t/.5190.t` | 2 | `b6f194a` | 已修 |
| 15 | 面试表决正文用“下列选项……”代替当前一票的利害 | `zg361wad.vote.desc` | 1 | `8b7e59b` | 已修 |
| 16 | 核心结果按钮以孤立省略号起句 | `zg361.3.a` | 1 | `af7f92c` | 已修 |
| 17 | Workforce 260 合同按钮没有独立写清动作、责任和变更后果 | `zg361we.260.a/.a.tt/.b/.b.tt` | 4 | `1efdf22` | 已修 |
| 18 | PP 189 两条抽象路线文案没有任何实际事件绑定 | `zg361pp.189.a/.a.tt` | 2 | `6db27be` | 已删除并设防回流 |
| **合计** | **18 个问题簇** |  | **39** |  | **39/39 已修；18/18 已闭合** |

提交 `f1342df` 先把全局门禁改为按实际事件绑定核对，并新增去除 CK3 格式码后的句首检查、标题归一化包含/
相似度筛查和空泛按钮检查；后续提交针对门禁追回项逐一修复。`8b7e59b` 将“下列选项”加入正文越权回归，
`af7f92c` 把实际事件按钮纳入句首检查，`6db27be` 同时断言 PP 189 的两个死 key 不得在事件、生成器输出或
最终本地化中回流。`7778b67` 最后将这些绑定、值、来源快照和检查结果冻结为可复现分片账本。

### 18.2 用户点名的两类问题：静态已修 / 未修

| 用户点名的问题 | 机器可判定范围 | 已修 | 静态未闭合 | 不能由机器证明的边界 |
|---|---|---:|---:|---|
| N-01：孤立标点起句、正文复读标题或用无价值模板凑正文 | 去格式码后的可见首字符、实际事件 title/desc 归一化包含、标题相似度候选和已知空模板 | 39-key 清单中的相关簇均已修 | **0** | 相似但不构成字面包含的叙事是否冗余，仍需人工按场景判断 |
| N-02：正文替玩家列选择，按钮只写“按 A 做”或其他空泛动作 | 实际事件 body/option 绑定、正文选择元话语、正文复制按钮、空泛按钮、未绑定 option-like key | 39-key 清单中的相关簇均已修 | **0** | 按钮是否足以让玩家理解完整利害，仍需结合人物、前因和 effect 人工复读 |

这里的“静态未闭合 0”只表示上述已编码规则没有失败，不能外推为“全部中文语义已由机器证明合理”。账本明确保留：

- `human_semantic_review_status = review`：635 个事件分片仍需人工判断处境、因果、人物口吻和信息价值；
- 9 个源文件的权威生成入口不能唯一解析，状态为 `authority_source_not_unique / review`；这不是当前文案失败，
  但在把修改追溯性称为完全闭合前仍需补齐唯一权威声明；
- `live_render_validation_status = pending`：动态人物名与数值插值、条件文本、换行/截断、字体排版，以及窗口出现时
  是否与真实剧情上下文自然一致，都保持 **LIVE PENDING**。

最终清单因此是：**已知且机器可定位的 N-01/N-02 静态缺陷未修 0；机器失败 0；人工语义复审未完成；
修复后全量 5 速实机语境、动态插值和排版验收未完成。** 后两项是“未验”，不能偷换成已修缺陷，也不能用
`machine_failures = 0` 冒充最终 LIVE GREEN。
