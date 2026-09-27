# 现役战斗策略：条件化当日出伤基数与观察步长

适用原版 CK3 `1.19.0.6-steam23530548` 的已确认战斗算术，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本轮只修改离线游玩策略，没有启动 CK3，以下**不是**新一轮实机对拍。

## 审计结果

生产 `strategy.py` 不构造也不调用 `ActiveMainResumeResearchKernel`。[研究核追击修正](pursuit-modifier-active-resume-gap-2026-09-27.md)目前只保证显式提供完整 typed input 时的研究计算；生产 `active_combat_resume_inputs_v1` 协议始终返回 `status=unavailable`，严格禁止以它生成整场胜率。缺口至少有下一日有效反制、非掷骰优势变化、骑士/兵团动态入场和完整跨日转移；当前兵团有效属性和本帧宽度也不能直接冒充未来状态。

生产已有同帧 `battle_control_snapshot_v1`，并已用当前参战人数及相对保有率，在显著劣势时把战斗推进从速度 3 的哨兵改为**最多一日的 `life-advance`**。本次在该决定前加入原有 `combat_core.fixed_mul` 与 `combat_core.outgoing_damage_raw` 的一个条件化计算。每侧只取当前主阶段 entry 的 `effective_damage_raw × current_fighting_raw`，逐 entry 向零截断后求和；再以中性优势 `100000`、现有 `final_combat_width` 和本侧核对过的 stored 当前参战总量，运行原生顺序的宽度/伤害缩放。结果称为“中性优势、未计反制、冻结此帧的一日出伤基数”；它**不是**真实下一日伤害的上下界，更不是软伤、硬伤或胜率。

只有暂停帧与查询的 snapshot/revision/native revision 一致、战斗仍在主阶段、完整 side、双方 roster 与 stored/derived 当前兵力一致、宽度为正、每侧兵团不超过 512、军队不超过 64、参战 entry 的伤害值非负时，才调用底层出伤函数。即使基数可算，也仅当己方当前人数和保有率都不优于敌方、且己方基数不超过敌方一半时，才触发谨慎的一日观察。此信号**只缩短观察步长**；不命令开战、撤退、终局处理，也不改变常规安全门。任何入参门槛缺失时不调用出伤函数，原人数/保有率判断仍可独立工作。

[聚焦回归](../../ck3_autonomous_player/tests/unit/test_battle_control_snapshot_v1_bridge.py)从同一合法帧出发，只调低己方 `effective_damage_raw`，验证策略由速度 3 转为一日、真正调用 `outgoing_damage_raw`、输出 `whole_battle_win_probability=None`，且缺宽度和过期帧均不调用模型。这是生产策略**使用有界计算**的代码证据，不是原版实机策略效果验证。
