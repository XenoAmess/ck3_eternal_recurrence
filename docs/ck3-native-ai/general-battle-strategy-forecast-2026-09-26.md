# 游玩智能体通用战斗预测接线（2026-09-26）

## 当前行为

本次把研究版整场模拟接入 `choose_one_life_turn` 的战争动作边界。`planner_usable=false` 仍准确表示**尚未达到原版逐日转移完全对拍**；它不再作为“所有战争动作一律不看模型”的开关。智能体现在使用模型估计作决策，同时在计划回执中保留模型来源、输入哈希、样本数、假设、未知项及风险阈值。不能把模型输出称为原版准确胜率。

| 场景 | 输入与算法 | 行动规则 |
| --- | --- | --- |
| 已开战、原策略拟向敌军所在省份行军 | 精确同帧 route preview、全敌 route-contact horizon、`combat-simulation-inputs-v3` 有序参战者和逐兵团输入；`general_battle_forecast.py` 调用既有 `research_envelope.py`，默认 256 trial、120 日 | Wilson 已结算胜利下界至少 0.65，p90 硬伤亡至多 25%，模型全军覆没/人物死亡各至多 5%，未决战斗至多 10%。单跳且一日内抵达才可提交该接战移动；长路线只可在再次证明首跳无接战后移动一跳，并在下一帧重估。风险超限则不提交该接战移动。 |
| 已有主防守战争解围 | 原先 512 trial 的窄门仍在，Wilson 下界 0.70、p90 硬伤亡 20%、全军覆没/人物死亡各 2%、未决至多 10% | 保留已有同帧战争退出比较和短段行军限制；通用动作审查不会重复运行该窄门。 |
| 和平时原生 final-legal 宣战候选 | 兵团尚未物化；`prewar_battle_proxy.py` 用同帧原生 actor base power 与 target total power 做 256 次、120 日**聚合战斗代理试算** | 只在既有合法候选、同帧标准封建/经济/身份约束及 Wilson 下界 ≥0.95、未决 ≤5% 时提交 typed declaration；其余候选继续观察或查询。代理模型不是逐兵团模拟，也不是校准的 CK3 战斗概率。 |

聚合代理的显式政策假设：己方可到场 base power 取原值 65%–100%，敌方取 total power 的 110%–145%，双方未知将领掷骰各取 0–20；每轮双方按剩余聚合力量的 3% 同时出伤。种子绑定宣战 ID 与原生 power 输入。它用于**压倒性优势候选的行动先验**，并不把战争战略军力比改名为“原版胜率”。一旦可获取真实参战者和 v3 输入，改用逐兵团整场试算。

## 不一致性与下一轮研究

- 首轮接线回归发现，若只以 `source=native` 与 typed step 为准入，通用宣战入口会绕过玩家本人 claim、标准封建政府、同帧经济与派系约束；该不一致已在提交前修复，通用入口现重新核对这些字段。对应战争入口测试保留错误身份/政体/旧帧样本作回归。
- 路线回归发现，较远终点的预期敌军接触不能直接视为**当天首跳**的冲突；现在先核对全路线只含目标战斗，再用独立的一跳原生预览和接触查询证明首跳安全，下一帧重估。同样，其他战争的空敌军列表不会中断接战审查。
- 宣战回执区分“预测已计算但风险准入失败”和“原生输入缺失”；前者保留完整代理试算，并将 `prewar_forecast_admission_available` 记为 true。未进入代理模型的合法候选回执列出实际不满足的同帧策略约束，不能再笼统写成“模型不完备”。
- 实机每次接战后应把预测输入哈希、模型构建、三分结果（赢/输/未决）、p90 损失与实际 CombatID/战果对齐，分开统计“结果预测偏差”和“原版采集器 RED”。目前 Episode 1 Messina 的部分逐日 trace 因新军加入和终局身份回读而 RED，不能冒充模型公式偏差；见 [实机案例](battle-simulation-episode01-live-case.md)。
- 固定参战者研究核仍禁用 loaded phase-event effects 与自愿撤退，未纳入途中新军加入；战争中的计划会在每个新暂停帧重新读取路线、敌军与输入，不复用旧候选。原版 effect/撤退/增援对拍完成后应替换相应研究假设，并以现有原版 trace 和实际战果做回归。
- `COMBAT_ENTRY_EU_ACTIVATION_ENABLED=false` 仍表示**正式的胜率＋战役期望效用合同**未启用；本次启用的是独立、有风险预算和来源标记的 bounded-model 动作路径。二者状态不得混写。

## 静态验收

```text
tools\.venv\Scripts\python.exe -m pytest ck3_autonomous_player\tests\unit\test_general_battle_forecast.py ck3_autonomous_player\tests\unit\test_general_battle_strategy.py ck3_autonomous_player\tests\unit\test_prewar_battle_proxy.py ck3_autonomous_player\tests\unit\test_combat_provisional_defense_canary.py ck3_autonomous_player\tests\unit\test_war_entry_assessments_bridge.py -q
```

该验收证明代码接入、冻结实机输入计算和拒绝/放行分支，不声称已在当前实机完成一次新宣战或接战后的战果回读。
