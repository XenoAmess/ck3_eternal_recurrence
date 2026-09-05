# 天朝二期简体中文文案与事件合理性全量审计

- 审计日期：2026-09-06
- 审计对象：`mod_zhongguo_style`
- 基准语言：简体中文
- 审计结论：**RED；当前不能通过中文内容验收。**
- 审计性质：静态全量审计。没有启动 CK3，因此不把按钮实际截断、字体渲染和运行时条件本地化效果声称为已实机确认。

这里的 `blocker` 指“在宣称天朝二期中文内容完成或发布前必须修复”，不等同于“必然导致 CK3 无法启动”。编码、键引用和生成可复现性基本健康；主要问题是玩家文案与实际 effect 不一致、案件缺少人物与事实、开发诊断语直接进入正式界面，以及大量模板卡不能支持知情选择。

## 1. 覆盖与方法

本轮不是抽样。审计把简中值、事件声明、玩家可见字段、决议/互动/活动、GUI 及生成器权威源做了全量清点和交叉引用。

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
