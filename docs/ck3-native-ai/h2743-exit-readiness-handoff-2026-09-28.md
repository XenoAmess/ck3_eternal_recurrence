# Robert H2743 守方退出决策：有界续战交接（2026-09-28）

## 现有同帧结论

[H2743 精确只读复验](h2743-native-exit-readonly-2026-09-28.md)在 WarID `16777231`、`native:3`、raw date `53217264`、Robert `29829` 为主防守方、战争分数 `-12` 的暂停帧确认：投降原生 validator 通过且对手现在接受；白和平、胜利均不可用。查询没有提交游戏动作，前后日期和快照 ID 相同。[R0264 H2825 独立摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.r0264-h2825-war-options.json)在另一份存档和 DLL 上看到 `-24` 及同样的选项可用性；不能倒灌到 H2743 的当前帧。

当前投降的具体 title／个人封臣、双方有符号资源、定向停战没有同帧读数。[原始 H2743 存档](h2743-native-exit-readonly-2026-09-28.md)中的 `c_foggia` holder `33435`、个人领主 `29829` 和三军人数是**行动前基线**。[R0197 唯一一次获授权的投降](war31-r0197-one-shot-live-result-2026-09-28.md)证明同一战争早期确有领地、直属封臣、威望和休战风险，但它不是 H2743 的反事实条款；该授权已消耗。

## 精确接口缺口

生产版 `ReadWarTerminationTerms` 在 `ck3_autonomous_player/native_bridge/src/ck3_11906.cpp` 只接受 `claim_cb` 和 `raiktor_claim_cb`；`individual_county_de_jure_cb` 被明确标为 `unsupported_casus_belli`。生产版 `ReadWarTerminationExitTerms` 因历史实机崩溃禁用，返回 `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668`。因此对 H2743 反复调用通用 claim 条款查询不会补齐 de-jure 的实际代价，也不能用静态脚本推演或早期投降净变化填零。

退出排序还缺一份**同一当前帧**的有界续战损失与接触风险。H2743 三军当前人数原生/存档核对分别为 `2329`、`1462`、`311`，但敌人处于不同省份，围城余一天；总人数相加不是接触时间、实际参战阵容或胜率。R0271 的围城参战集合判定是正式续跑的直接门禁，退出决策不能抢用其尚未闭合的风险结论。

## 正式策略交接

`formal_defender_exit_observation.py` 现在在合法性读数后附 `decision_readiness`：列出当前原生合法且对手接受的结果，并明确四类阻断观察；`generic_claim_cb_terms_query_applicable=false`、`historical_surrender_result_reusable_as_current_terms=false`。它继续保持 `recommended_outcome=null`、`action_literal=null`。

`strategy.py` 同时保留原有战术规划器选出的候选步骤，附于 `continuation_handoff.candidate_selected_step`。这个字段只是**可恢复候选**：下次正式执行仍须按原有同帧、路线、接触、围城及动作回执合同重新验证。若战术规划器没有候选，记录 `no_tactical_candidate`；如果其候选是这场战争的投降或白和平，观察器不会把它登记为续战候选。附注不改变正式 `selected_step`，也不授权退出动作。

下一次具备相同精确输入的只读研究应先取得 de-jure 当前领地/封臣、双方资源变化与定向休战的可复核读口，再把 R0271 接触／围城分区及有界损失模型绑定到同一战争帧。只有三路选择和正式 typed consumer 的版本、动作、后置条件、下一回合及冷恢复均通过，才能主张可复用退出闭环；本次没有提交投降、白和平或时间推进。
