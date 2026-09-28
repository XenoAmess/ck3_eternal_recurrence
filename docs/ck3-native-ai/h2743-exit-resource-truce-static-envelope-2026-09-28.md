# H2743 守方投降：资源与休战的原版静态边界

本记录只读 CK3 `1.19.0.6-steam23530548` 的本机 EXE、七份原版脚本和已入库的 H2743 原生选项摘录。它没有启动 CK3，没有调用 `setup_de_jure_cb`、effect 或 preview，也没有提交投降。可重跑的[提取器](../../ck3_autonomous_player/native_bridge/research/project_h2743_exit_static_envelope.py)对 EXE、脚本和 H2743 帧逐文件校验 SHA-256；[机器回执](../../ck3_autonomous_player/native_bridge/research/h2743_exit_static_resource_envelope_1_19_0_6.json)保留脚本表达式和所有未知值。脚本的完整 SHA 清单在回执中。

H2743 `native:3`、raw date `53217264` 的 Robert `29829` 是 WarID `16777231` 的主守方，Landolf `30097` 是主攻方，CB 为 `individual_county_de_jure_cb` index `17`、目标输入 `[2128]`。本帧原生选项确认守方投降合法且对方接受，绝对结果为 `attacker_victory`；条款仍不可观察。[原始摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.local-h2743-options.json) SHA-256 `CAFA45C85F6F80BF71C155AB6D4C553D698CA33D47F82AC2FFC5B587FB0F137E`。若该帧或游戏构建变动，提取器拒绝重用。

| 分量 | 精确原版连线 | H2743 可发布值 |
| --- | --- | --- |
| Robert 当前威望 | `00_dejure_war.txt:474–484` 将守方设为 loser；`00_casus_belli_effects.txt:136–159` 对非宗教战 `add_prestige`，其直接分量是 `max(-10 × P, -1000)`，`P=scope:cb_prestige_factor`。 | `P` 尚未取得；直接分量未求值，总签名差额为 `null`。 |
| Landolf 累计威望／名望进度 | 同一 fame 效果的进攻方胜利分支 `00_casus_belli_effects.txt:37–65` 写 `add_prestige_experience`，直接分量为 `min(10 × P, 1000)`。 | 原版走的是进度字段，不能用 Landolf 当前可花费威望代替；实际值 `null`。 |
| 正统性与虔诚 | `add_legitimacy_attacker_victory_effect` 进入 `war_end_legitimacy_effect`，受合法性和双方 title tier 等条件控制；`mandala_war_victory_effects` 对守方的 `add_piety_experience` 受 `piety_devotion_from_defensive_wars` 领地法控制。 | 未取得本帧条件及完整 effect 结果；各项总变化不能写零。 |
| 金币与人情 | EP3 的 `laamp_as_mercenary_payout_tooltip_effect` 包含按参战者、合同和欠款变量条件触发的 `pay_short_term_gold`；de-jure liege 的 favor hook 也有作用域、AI、可加 hook 的条件。 | 未取得本帧合同、欠款和 hook 条件；不将脚本未列常量费用误写为总金币变化零。 |
| 单向休战 | `on_victory` 调 `add_truce_attacker_victory_effect`；唯一 one-way leaf 的 owner 是进攻方 `30097`，toward 是守方 `29829`，result 参数为 `victory`。 | 仅脚本方向已知；本帧实际天数与结束日期仍为 `null`。 |

休战天数的原版表达式是 `D = (2 if B else 1) × max(730, 1825 - 450×FLEX - 900×SHORT + 900×LONG - 730×NOMAD_BOTH)`。`FLEX` 是进攻方灵活休战 perk，`SHORT`／`LONG` 是有关 struggle 参数，`NOMAD_BOTH` 是双方游牧政府标志，`B` 是当前进攻方其他同人物对战争中有 `fp2_border_raid` 的条件。**这里的 `FLEX` 与上表威望因子 `P` 是不同变量。**原版顺序先做 730 天下限，后做可能的两倍乘数。实际条件未在 H2743 同帧读出，也没有安全的本 CB 休战天数原生 evaluator 读回；不能从脚本常数计算到期日。R0197 投降后存档里的 `30097→29829` 休战是历史先例，不是 H2743 当前反事实。

脚本 `on_victory` 还调用 POW 提示、骑士荣誉和 FP1 征服纪念等效果，且战争结算可有 CB 块之外的全局效果。回执中的条件列表明确不是全 effect 树的穷尽证明。`setup_de_jure_cb` 生成 `P` 的 native 路径目前只静态定位到 helper 计数和 identifier 写入调用；计数业务含义、运行时目标 scope、最终 `P` 存储及纯读安全性未闭合。**不得为取得 `P` 在正式存档调用 setup 或通用 preview。**

下一步只读输入门禁：先证明 `P` 与目标 scope 的无副作用生产者及其同帧 revision/generation；再取得两方资源、合同／领地法／正统性条件和休战 evaluator 参数的同帧值；最后验证 CB 和战争结束全 effect 树，才能给有符号总资源差额。领地／封臣 old→new 图和有界续战风险还需独立 producer。现有[纯函数比较合同](h2743-formal-exit-comparison-contract-2026-09-28.md)因此仍返回 `unavailable`，没有推荐结果或投降动作。

聚焦验证：`py ck3_autonomous_player/tests/unit/test_project_h2743_exit_static_envelope.py` 与 `py -O ck3_autonomous_player/tests/unit/test_project_h2743_exit_static_envelope.py` 均检查精确脚本回执、错误 EXE／H2743 帧拒绝以及实际资源、F 和期限保持未知。它们只验证静态边界，不代替原生同帧条款查询。
