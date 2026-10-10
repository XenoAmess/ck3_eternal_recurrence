# R0321 围城接战预测生产缺口（2026-09-28）

本记录基于固定 OneDrive `WAR/M5-WAR-CASH-20260928/SOURCE-R0321-WAR-FORECAST-RED-v1.json` 的精确 6CCA6BE7CD31828F662271C9FF0B58E9C7D48081A587C9D5833DA9A7C2D6DD20 字节哈希，以及来源 commit `a6d1ae845f11e1e0bae79cac3fd9c30b00afae59` 的静态代码。来源正式报告、检查点存档、driver 与原生二进制尚未在接收机核验；本文不是实机预测或行动授权。

## 精确停顿

R0321 在第 27 turn、`native:23`、public revision 24、native revision 23、日期 raw 53219928 停于 WarID 16777231。我方 ArmyID 83886367 在 2610，目标 2629 有敌军 50331920 与 83886484。围城目标参与者分区为 `available`，场外敌军列表为空；本轮的停顿不再是 R0271 最初的参与者未知问题。原生 v3 接战输入查询被接受并返回 `available`，但 `monte_carlo_ready=false`、`planner_usable=false`，正式计划 `selected_step=null`、`active_attack_allowed=false`。

## 两层独立阻断

1. [`strategy.py`](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py) 的 `_qualified_siege_forecast_move` 从顶层 snapshot 读取 `combat_entry_eu_v1`；字段不存在时直接返回 `producer_unavailable`（约 16959–16961 行）。同一来源树中，原生 bridge 和 native driver 没有此字段的生产、查询或顶层投影；现有出现处是策略消费与合成单元测试的人工注入。`combat_entry_action_components_v1` 也只有这个消费口和测试注入。
2. `_provisional_defense_research_assessment` 显式要求 `len(defender_army_ids)==1`（约 16880 行），R0321 当前有两支敌军，因此返回 `same_frame_encounter_scope_mismatch`，没有进入研究模拟。即使扩展多守军研究路径，当前 `forecast_fixed_contact` 仍标注 phase events、人物伤亡、未来每日状态等未建模；研究结果不能升格为正式胜率。

额外的激活门独立存在：[`combat_decision_contract.py`](../../ck3_autonomous_player/src/xar_autoplayer/simulation/combat_decision_contract.py) 的 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED=False`（第 22 行）。合成测试即便注入完整 `combat_entry_eu_v1` 与三行动 trial tape，仍返回 `calculated_not_activated`。不能只补 snapshot 字段或改布尔值来授权攻击。

## 缺少的生产者与 ABI

当前 v3 native mailbox（`combat_simulation_inputs_v3_mailbox.cpp`、`combat_v3.cpp` 和 `combat_v3.hpp`）只读同帧 `base_inputs` 和 `phase_event_inputs`，并核前后 frame；它不是战斗结果采样器。v2 基层 `ck3_11906.cpp` 初始化 `monte_carlo_ready=false`，且明列 `damage_to_casualty_allocation`、`pursuit_transition`、`battle_end_and_retreat_transition`、`phase_event_rng_and_effects` 缺失域。Python `combat_phase_contract.py:577–581` 对 v3 归一化更明确地固定 `monte_carlo_ready=false`、`transition_fidelity_gate=false`、`planner_usable=false`、`active_attack_allowed=false`。Python 的 `research_envelope` 关闭 phase events；`general_battle_forecast` 的人物死亡风险为 `null`。正式 EU 合同还要求同帧观察/预测身份、经校验的模拟器与输入 SHA、胜负和未决分布、Wilson 区间、伤亡与人物尾部、战役反馈，以及 attack/avoid/wait 三行动逐 trial 成分与有来源的效用政策。

可复用生产者应以精确 paused main-thread 帧为输入，把 WarID、目标省/入口省和有序 ArmyID 向量绑定到全代际原生对象；输出须携带查询代次、snapshot/public/native revision、日期和源 EXE/DLL/模型哈希。要得到可行动的胜率，还需补全上述原生状态转移与 phase 事件，做独立多守军轨迹/概率校准，再产生完整 EU 合同和三行动 trial tape。正式激活应是后续独立门禁，须验证非同帧、缺域、两守军、接触集合漂移及回退都拒绝动作。

## 本轮可安全推进

先取得来源已有的 388302 字节 `formal-report.txt`（SHA-256 `7A7774C59DA6099B0A1FFD650AB21A29407BD8B22B1056C7B6F5053251A5CF30`），核对 v3 原始 payload、查询回执和前后帧，再决定是否需要 78 MB 检查点/driver/二进制的隔离只读复现。若要做短期代码增量，可增加**只读**两守军研究诊断与细粒度缺域状态，但继续保留 `selected_step=null`、`active_attack_allowed=false`，不能把这项诊断包装成 R0321 GREEN。

## 2026-09-29 后续原始输入核对（2026-10-10 合回）

本文最初关于正式报告尚未接收的说明记录首次摄入状态。后续来源正式报告已按 388302 字节/SHA-256 `7A7774C59DA6099B0A1FFD650AB21A29407BD8B22B1056C7B6F5053251A5CF30` 验收：V3 查询位于 `/auto_run/turns/25/result`，`accepted=true/status=available/query_sequence=1`，身份为 `native:23/public24/native23`，相邻 before/after 都是暂停 raw53219928；终止计划位于 `/auto_run/turns/26/plan`。该报告仅含 V3 command envelope，原始对象位于 H3911 driver `/command_history/3919/result/combat_simulation_inputs`。H3911 摘录与母 driver 的后续接收、完整值相等和接收端 attempt4 已记在 [硬伤换算来源专题](r0321-hard-conversion-source-audit-2026-09-29.md)，不再把最初缺件请求作为当前待办。

原分支 `658456459d9a0fc2a26b3679f1a23cb6002ea8ac` 的 2026-09-29 补录另保留 R0345 对象深比较的精确身份。R0345 post-run 摘录为 2081860 字节/SHA-256 `C91DDA8284E414D96FA7705AA0881A048CF0CAB2F83AB4817F7826F5C5A63F67`，由 `RECEIVER-ACK-R0345-H3928-V3-RAW-EXCERPT-v1.json` 绑定；与 H3911 摘录在各自 `/command_row/result/combat_simulation_inputs` 的完整 JSON 值相等，各有 **78887 个标量路径**，路径和值差异均为0。使用 Python3.14.7 的 `json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')` 规范化后，两对象均为 **2077900 字节**，SHA-256 **`EF7DCDFDC4E3FE730B7046292FCC12C481002C4E8F511F53278D5C9E4BFEC377`**。对象含军队当前省份 `[2610,2629,2629]`、逐团兵数、目标环境和空的活动战斗列表；这比字段形状相等更强。

对象外查询身份分别为 H3911 `native:23/public24/native23` 与 R0345 `native:3/public4/native3`。两份正式报告均记录暂停 raw53219928、episode `native-29829-2bc2d599f7f9`、connection generation1；R0345 摘录行只含 index/command/ok/result，帧字段由其正式报告提供。当时 46065605 字节的 R0345 post-run 母 driver 未转运，不能将摘录深比较写成对母件无损相等或每字段重新从游戏读取的证明。其只读结论文件 `RECEIVER-R0345-V3-FORECAST-DIAGNOSTIC-v1.json` 为7095字节/SHA-256 `5E1CA252034AFA483F3557F5F5B4ACCBFEE8A6D73AB4FE314994A5CA380E2439`；[当日日报](../autonomous-agent-progress/daily/2026-09-29.md) 已保存 R0345 的实际失败、无物质动作或日期增长，以及接收与母件边界。两个对象相等不能区分未改变的暂停战局与复用/缓存。

双守军研究的后续动作域修正已见 [现有研究专题](r0321-multi-defender-research-gate-2026-09-28.md)，硬伤诊断与后续原生输入缺口沿其原生专题处理。本补录只合回遗漏的历史出处和精确比较结果，不恢复旧分支的阶段性转运计划、draft状态或旧待办，也不重复读取大件、执行测试或增加当前实机/预测/行动完成度。
