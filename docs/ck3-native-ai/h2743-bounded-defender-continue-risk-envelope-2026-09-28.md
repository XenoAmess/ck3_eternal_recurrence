# H2743 防守方续战：有界观测与不可用风险合同

状态：**可复用只读合同已实现；没有战争退出排序或新实机结果。** [`formal_defender_continue_risk_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/formal_defender_continue_risk_v1.py) 接收同一 paused WarID 帧及可选的同帧路线接触、围城时钟，返回条件性时间观测和明确的 `typed_unavailable` 项。它从不输出胜率、预期损失、效用区间或退出命令；不修改[`formal_defender_exit_observation.py`](../../ck3_autonomous_player/src/xar_autoplayer/formal_defender_exit_observation.py)和 exit terms 文件。调用者必须先校验来源 SHA 对应的原生报告及 query 绑定；函数只校验传入的完整帧身份和字段形状，不能自行证明 SHA 背后的字节来自 CK3。

## 现有帧能限定到哪里

| 检查点 | 已有证据 | 可用的风险边界 |
| --- | --- | --- |
| H2743 `native:3`、raw `53217264` | [同帧退出选项](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.local-h2743-options.json)记录 Robert 相对战分 `-12`；敌军 `50331920` 在玩家附庸省份 `2628` 围城，**剩 1 日估计**，另一敌军正向那里移动。投降合法且会被接受，白和平和胜利不可用，CB 条款不可见。目标郡 `2128`、其直属头衔/契约和资源仅有同一存档的保存层基线；R0197 的实际投降为历史先例。 | `53217264+24=53217288` 只是当前围城倒计时的估计时间，**不是完成时间上界**；本帧没有同帧路线接触期或整场续战损失上界。历史 title/封臣状态不能充作 H2743 投降后的变化。 |
| H2825 R0264 `native:40` 与 R0265 `native:3` | [有界风险审计](h2825-bounded-continue-war-risk-2026-09-28.md)记录 R0264 战分 `-24`、围城剩 `292` 日；另一个恢复帧 R0265 玩家预计 `44` 日到目标、场外敌军预计 `96` 日到目标，接触查询只证明下一日无接触。 | `292-44=248` 日只是**跨帧条件算式**，不能进入本合同的同帧围城或安全余量。军队人数、基础战力及到达先后不是战斗胜率。 |
| R0271 turn 36 `native:30`、raw `53219160` | [精确阻断摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json)记录战分 `-21`、下一日接触无冲突至 `53219184`，首路点 `2614` 到达 `53219328`，玩家到目标 `2629` 为 `53220216`，场外敌军 `83886484` 到目标为 `53219928`。 | 首路点在接触证明边界后 **144 raw ticks，即 6 日**；从当前帧到首路点共 168 ticks，即 7 日。按当前命令，场外敌军到目标比玩家早 **288 ticks，即 12 日**。这解释参战集合为何不可证，不能把一日无接触推广到首路点、目标接战或整个战争。R0271 摘录无同帧围城剩余时间和当前原生退出选项，必须维持不可用。 |

H2743 的 `-12`、H2825 的 `-24`、R0271 的 `-21` 来自不同日期/修订/动作路径，不能作同一战争分数的无干预趋势，更不能外推下一日分数。R0271 `2332` 对两敌合计 `1747` 兵数和 AI 基础战力只是兵力现状，不是接战时参战集合、胜率或伤亡上界。

## v1 合同

输入 `frame` 固定 snapshot ID、public/native revision、date raw、episode、connection generation、角色、WarID 和当前玩家视角分数。可选 `contact`/`siege` 必须带与之**完全相同**的 `source_frame` 及来源 SHA-256；跨帧输入抛错，不从旧查询补零。`contact` 只有在原生条件为 `one_day_contact_free=true`、冲突列表空、窗口从当前 raw date 精确覆盖 `24` ticks 时，才输出 `bounded_current_orders_one_day_only`。首路点是否落在该窗口之外另列；已列出的场外敌军早于玩家到达目标只输出 `listed_offsite_hostile_may_precede_target_entry`，并固定 `offsite_roster_complete_proven=false`，不能自动纳入或排除最终战斗。`siege` 的剩余日数只输出 `current_timer_estimate_only`，其 `completion_upper_bound_proven=false`。

每份结果固定保留 `continuation_loss_upper_raw=null`、`continuation_win_probability=null`、`surrender_vs_continue_utility_interval=null`、`material_comparison_ready=false`、`recommended_outcome=null`、`action_literal=null`。资产暴露和估值、CB 真实条款、完整参战集合、有限期战争现金和损失上界均列入 blocker。这样后续消费者能使用**短时复观测边界**，但不能误将它当成“继续作战更优”或“应投降”的决策证书。

## 仍需取得的原生输入

1. 当前同帧的目标 title/直属封臣与正在受围城省份的资产关系，及每项价值单位；保存层 H2743 基线只能列为候选暴露，无法证明 R0271 当前关系或投降/续战的尾部损失。
2. 对完整敌军名册的同帧接触/入战和围城时钟，且每次最多推进一日后重审；R0271 到首路点约七日，不能以现有下一日无接触回执授权整个路点。
3. CB 特定投降变化、双方有符号资源、定向休战；战争支出和扣款期限上界。没有这些，就没有可比较的统一效用单位或保守尾损失上界。

聚焦测试 [`test_formal_defender_continue_risk_v1.py`](../../ck3_autonomous_player/tests/unit/test_formal_defender_continue_risk_v1.py)直接读取 H2743 与 R0271 的已入库摘录，检查一日接触边界、七日首路点、场外敌军先到、围城时钟非上界、跨帧/跨目标省份拒绝及始终不产生命令。普通和 `-O` Python 各四项通过；没有启动 CK3、运行正式规划器或提交动作。
