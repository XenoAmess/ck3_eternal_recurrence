# 固定接战预测：已观察到目标省份入境路线时暂缓最终一跳

**结论与动作边界。**生产 `forecast_fixed_contact` 使用原生同帧 v3 输入和现有 `research_envelope`，但 `participant_policy=explicit_hypothetical_fixed_at_contact_no_reinforcements`；试验全程冻结双方军队/兵团，不能自动纳入接战后的增援与退出。策略现在仍计算并回报该有界分布；若暂停同帧另有**不在 v3 defender 名单内**、未撤退、当前不在目标省份的敌军，其原生存储 `route_province_ids` 明示路线经过目标省份，则禁止仅凭固定参战分布提交**最终一跳**。返回 `native_war_general_battle_observed_inbound_reinforcement`、敌军 ID 和 `inbound_arrival_before_battle_resolution_proven=false`。长路线仍可在现有 `one_day_contact_free` 等门槛满足时走安全第一跳，下一帧重查。没有可读的额外入境路线时，原有有界模型准入继续使用；这不是要求未来参战者完整可知才使用模拟器。

**来源与可证程度。**CK3 `1.19.0.6`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。项目桥接层 `ck3_autonomous_player/native_bridge/src/ck3_11906.cpp` 的 `ReadUnitRoute` 从 CUnit 存储路线 `+0x44` 行数及对应 ProvinceInfo 顺序读取全路线；`ReadWarsAndArmies` 在暂停快照以 `include_full_routes=output.paused` 调它，并将敌军放入 `active_wars.enemy_armies`。`war_contract.py` 保留、校验 `route_province_ids`；生产策略的目标省份和 v3 defender IDs 已有同帧查询及命令历史绑定。这里确证的是**当前已存路线经过目标**，不是敌军一定会按此路线走完、一定在战斗结束前到达，更不是加入同一 CombatID。现有一日 `route_contact_horizon` 只证明路途/接战前短窗，不为最长 120 日模拟期间的所有增援提供排除证明。

风险边界恰与现有实机增援证据相符：在[原生 Army 22 的日内增援](battle-reinforcement-and-join.md)中，先前 18/14 MAA 固定名单于 day11→day12 变为 24/14，加入后当天开火；[098 原生反制向量](active-counter-output-cross-check-098-2026-09-27.md)的玩家 class 1 从增援前输入算 `54257`，加入后原生为 `10000`。这证明固定名单可能给出错误的动态反制、战宽和出伤；它**没有**证明任何未来存储路线必然加入，不能把 Army 22 的案例复制为新门槛的概率或 ETA。

`contact_admission` 的 `unquantified_risks` 现显式列 `future_reinforcement_and_participant_exit` 与 `voluntary_retreat`，即使有界模型被准入也不隐去这些缺域。新增单测用合成同帧敌军路线验证：模型真实被调用、已观察到目标路线时最终一跳被拦、第一跳在一日安全门满足时继续放行；旧的无额外路线准入测试继续通过。这些是生产策略行为测试，**不是**原版 AI 到达率或整场胜率实机校准。

**最小实机对拍。**在独立受管 attempt 的暂停同帧记录目标省份、已选攻守军 ID、所有敌军当前省份/原顺序存储路线、v3 输入哈希、route-contact-horizon、生产预测与动作回执。选一个额外敌军路线包含目标、但当前不在目标的样本；证明它不在 v3 defender 列表并且接战前一日查询没有提前接战。只在另有授权且安全时推进一日，再以新 snapshot 观察其路线/位置、目标军队身份和实际行动；若发生战斗，用 `battle-control` 的 CombatID、ordered armies 与 phase-fire 入口确认是否加入、加入时刻及战宽/反制更新。路线取消、转向、未按期到达都应如实保留为阴性样本。只有这种逐帧证据才可估计入境路线的实战风险；本次没有启动 CK3，也未把该门槛当成未来确定性预测。
