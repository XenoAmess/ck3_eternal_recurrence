# R0167 Robert 战时生活方式加点：只读结果与正式入口边界

状态：**production-live private readback；战时 typed 动作未执行**。本记录只界定下一项动作包，不改变 G2-M4 合同或里程碑计数。

## 同一 paused 帧已知事实

R0167 从 Robert 正式主线 h1082/raw53190528 配对冷恢复。冻结 EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，私有 DLL SHA-256 为 `A9E1293F1E5912439793E51FD55282EDCB58359CB49737993900FD941D763CDB`。actor `29829`，episode `native-29829-2bc2d599f7f9`；这些值只定位证据，不是策略常量。

冻结 [R0167 readback manifest](Z:/ck3_mod_rewrite_process_assets/g2-m4-robert-r0167-three-query-green-20260923/R0167-evidence-freeze/R0167-readback-freeze.json) SHA-256 `AEAB84B6BDD6548685FC89757675CEBB7BD05532EE6AA984CE373B559B9259D3` 与 [formal private query](Z:/ck3_mod_rewrite_process_assets/g2-m4-robert-r0167-three-query-green-20260923/R0167-evidence-freeze/private-query-player-lifestyle-formal-v1.json) SHA-256 `D5FD7875CFCC7AB0164F397762A7546181253B0CAFD584CB149BA9F08267F339` 显示：当前 focus 为 `stewardship_wealth_focus`，管理生活方式总 XP 为 `2131.25`、未花点数 `2`、已花点数 `4`，私有原生最终合法候选只包含 `cutting_corners_perk`。同一正式报告的 `readiness.active_context.war_ids` 为 `[16777250, 95]`。三次查询均只读；typed 动作 `0`、日期推进 `0`、进程已回收。没有 `HasPerk` 后置或下一正式 turn 消费证据。

## 当前合同为何没有提交

[G2-M4 权威合同](../autonomous-agent-progress/g2-requirements-v1.json) 是两年内完成建设、议会调整及封臣/派系响应的**和平治理**切片。现有 [LIFE1 原生树和最小策略](lifestyle-focus-perk-ai.md) 将 `cutting_corners_perk` 放在标准封建和平治理候选中，并要求独立 campaign-root/war 状态给出和平；[正式消费者说明](g2-m4-life-formal-consumer-20260916.md) 明确只有普通和平 `life-advance` 才查询并提交该 perk。代码中的 `same_frame_feudal_peace_scope` 对非空 `active_wars` 返回 `outside_scene`，`choose_min_feudal_lifestyle_action` 同样要求 `at_peace=True`。R0167 的私有原生合法性因此没有授权现有 LIFE formal consumer 越过场景门，更不能算一次 M4 动作验收。

`same_frame_feudal_peace_scope` 同时供建设正式消费者使用。直接放松此函数会把建设一并带进战时场景，超出本次证据和改动边界。原生树只把**战时军事重心**交给战争 OODA；R0167 要花的是已有管理重心的一个管理 perk，不能把这条说明曲解为军事重心已完成研究。

## 最小后续能力包

可单列 `G2-LIFE-WAR-PERK` 战时能力候选，不增加或改写 G2 的八个里程碑，也不把战时读回记作 M4 和平切片完成。复用当前 exact-build 私有读回、`cutting_corners_perk` allowlist、最终原生合法性、typed transport 和 receipt。新入口只考虑**已有**管理 focus 的合法 perk；不在此包切换 focus、猜其他技能、不改建设消费者的和平门，也不挤占尚待处理的战争 RED/互斥动作。

候选启动前在同一 paused 帧重新确认玩家/episode/版本/日期、当前 focus、未花点数、未拥有目标 perk、原生最终合法候选和当前战争决策。只有正式战争规划本轮没有应立即执行的动作且没有待确认互斥动作时，才能提交**一个** typed perk。独立下一 paused revision 核对 `HasPerk=true`、管理点数变化与相同 action ID 的 receipt，再由下一正式 turn 消费；动作状态不明先核对，不重复提交。若这些条件不能同时成立，保留战时能力候选缺口，等待和平后使用现有 LIFE 正式入口或补最小所缺观测。该动作即使 GREEN，也只证明本场景战时加点，M4 两年治理及公共能力广告仍依各自合同验收。

