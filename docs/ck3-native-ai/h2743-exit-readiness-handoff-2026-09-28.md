# Robert H2743 守方退出决策：有界续战交接（2026-09-28）

## 现有同帧结论

[H2743 精确只读复验](h2743-native-exit-readonly-2026-09-28.md)在 WarID `16777231`、`native:3`、raw date `53217264`、Robert `29829` 为主防守方、战争分数 `-12` 的暂停帧确认：投降原生 validator 通过且对手现在接受；白和平、胜利均不可用。查询没有提交游戏动作，前后日期和快照 ID 相同。[R0264 H2825 独立摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.r0264-h2825-war-options.json)在另一份存档和 DLL 上看到 `-24` 及同样的选项可用性；不能倒灌到 H2743 的当前帧。

当前投降的具体 title／个人封臣、双方有符号资源、定向停战没有同帧读数。[原始 H2743 存档](h2743-native-exit-readonly-2026-09-28.md)中的 `c_foggia` holder `33435`、个人领主 `29829` 和三军人数是**行动前基线**。[R0197 唯一一次获授权的投降](war31-r0197-one-shot-live-result-2026-09-28.md)证明同一战争早期确有领地、直属封臣、威望和休战风险，但它不是 H2743 的反事实条款；该授权已消耗。

## 精确接口缺口

生产版 `ReadWarTerminationTerms` 在 `ck3_autonomous_player/native_bridge/src/ck3_11906.cpp` 只接受 `claim_cb` 和 `raiktor_claim_cb`；`individual_county_de_jure_cb` 被明确标为 `unsupported_casus_belli`。生产版 `ReadWarTerminationExitTerms` 因历史实机崩溃禁用，返回 `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668`。因此对 H2743 反复调用通用 claim 条款查询不会补齐 de-jure 的实际代价，也不能用静态脚本推演或早期投降净变化填零。

退出排序还缺一份**同一当前帧**的有界续战损失与接触风险。H2743 三军当前人数原生/存档核对分别为 `2329`、`1462`、`311`，但敌人处于不同省份，围城余一天；总人数相加不是接触时间、实际参战阵容或胜率。R0271 的围城参战集合判定是正式续跑的直接门禁，退出决策不能抢用其尚未闭合的风险结论。

## 正式策略交接

`formal_defender_exit_observation.py` 现在在合法性读数后附 `decision_readiness`：列出当前原生合法且对手接受的结果，并明确四类阻断观察；`generic_claim_cb_terms_query_applicable=false`、`historical_surrender_result_reusable_as_current_terms=false`。它继续保持 `recommended_outcome=null`、`action_literal=null`。

`strategy.py` 同时保留原有战术规划器选出的非终战候选步骤，附于 `continuation_handoff.candidate_selected_step`。这个字段只是**可恢复候选**：下次正式执行仍须按原有同帧、路线、接触、围城及动作回执合同重新验证。若战术规划器没有候选，记录 `no_tactical_candidate`。若其 `selected_step` 是**这场受观察 de-jure 守方战争**的投降或白和平，正式返回计划会清除该步骤并记录 `native_war_defender_exit_material_blocked`；其它 WarID 不被此门禁误拦。这个门禁不影响现有进攻方独立紧急退战策略。

## 已发生的 15 天续战代价

[精确续战投影器](../../ck3_autonomous_player/tools/project_h2743_h2825_continuation.py)对 H2743/H2825 保存和 driver 共四份原件逐字节校验 SHA-256，并要求前 2742 条历史完全一致、H2825 从 H2743 恢复、九段推进日期与分数连续、没有提交终战动作。两端军力查询与原生暂停快照也逐项配对。外置 append-only 结果 `D:/ck3-research-artifacts/war31-h2743-20260928/observed-continuation-02.json` SHA-256 **`FECDC23B556353D4FB9CB08D9E5842EC726C20E47E6333AAE6AE70D1E893195C`**；跨机精简摘录见[证据](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.h2743-h2825-continuation.json)。

| 已发生的变化 | H2743 | 第一天后 | H2825 |
| --- | ---: | ---: | ---: |
| Robert 相对战争分数 | −12 | −25 | −24 |
| 攻方占领分 | +39 | +52 | +52 |
| 攻方计时分 | −27 | −27 | −28 |

第一个游戏日分数跳变 −13，与攻方占领分 +13 精确对应；最后的 +1 来自攻方计时分 −1。两端战斗和囚禁分均为 0。精确 H2743、H2825 原生查询的三军人数都为 `2329/1462/311`，Robert 金币 `111861020/100000`、当前威望 `253090010/100000` 的**两端净变化**也均为 0。两份资源读数不能说明期间无其他写入，不能代表虔诚、对手资源，也不是投降后的资源 delta。这个历史序列只说明**该已发生路线** 15 日后局面仍可恢复且战分净恶化 12；不能把它当成下一步战果概率、R0271 围城参战集合或投降反事实效用。

精确原版脚本 `00_dejure_war.txt:435–497` 的 `on_victory`（守方投降）没有直接调用 `pay_short_term_gold_reparations_effect(GOLD_VALUE=3)`；该调用在 `on_defeat`。这排除把这笔**直接赔款**误算到 H2743 投降，但不证明金币总差额是 0。目标 Title `2128`、当前 holder/封臣和原版 `type=conquest` 的脚本设置仍不能确定实际迁移清单。

下一次具备相同精确输入的只读研究应先取得 de-jure 当前领地/封臣、双方资源变化与定向休战的可复核读口，再把 R0271 接触／围城分区及有界损失模型绑定到同一战争帧。只有三路选择和正式 typed consumer 的版本、动作、后置条件、下一回合及冷恢复均通过，才能主张可复用退出闭环；本次没有提交投降、白和平或时间推进。
