# 正在进行的战斗：整场预测输入审计（2026-09-27）

## 结论

[source-confirmed] 现有有界整场模型只实现**假定从此刻首次接战**的固定参战者试算，不能据其输出对已经存在的 `CombatID` 判断“继续打还是主动撤退”。`combat-simulation-inputs-v3` 虽可包含被选军队的 `ongoing_combats` 观察，却仍以调用者给出的目标省、假定入场边和攻守名单构建 v2 `base_inputs`，没有把原版战斗 entry 恢复为模型初态。生产适配器现对非空 `ongoing_combats` 返回 `active_combat_requires_resume_input`；缺失该字段也拒绝估计。此门只约束决策用的 `forecast_fixed_contact`，不改变历史研究夹具用 `freeze_combat_simulation_input` 做条件计算。

[source-confirmed] `battle-control-snapshot-v1` 已发布高价值的真实进行中状态，不能笼统称输入全无。但它与 v3 分属两个查询；即使两次外层读回显示同一公开 revision，也没有一个**同一 native application-main 采样**同时冻结下面全部状态，且当前 trial kernel没有“从主阶段第 N 日继续”的入口。因此本审计没有提高 active-combat 决策的可用性等级，也没有启动 CK3。Steam 当前画面新鲜度门仍按 [既有规则](steam-offline-frame-freshness.md)执行。

## 逐域可用性

| 现役战斗所需输入 | 当前已发布证据 | 当前限制 |
| --- | --- | --- |
| 精确身份与操作范围 | `battle-control-snapshot-v1` 从可控 CUnit 解析 full `CombatID`、CArmy backlink、真实 Province、side、该 owner 可撤军范围，双采样并前后核 paused 世界帧。 | v3 请求没有 `CombatID`；它只按请求名单构造假定攻守，不能证明该列表就是当前战斗两侧完整名单。 |
| 阶段、日数与随机进度 | battle-control 提供 `phase_raw/phase_day`、`roll_cadence_counter`、双方 `current_roll_points`、winner/finalized。 | `ResearchEnvelopeKernel.simulate_trial` 无条件从 `maneuver_days=3`、`main_days=0`、`roll_cadence=0`、双方 roll=0 开始；没有 resume 初态。 |
| 当前兵量与伤亡 | battle-control 的两侧 `ordered_armies`、`levy_entries/men_at_arms_entries` 包含各 entry `starting_raw/current_fighting_raw/soft_casualties_raw`、硬伤状态和值、有效攻防追击掩护，以及侧汇总与差额。 | v3 的 army/regiment `current_soldiers` 是军团观测，不是战斗 entry 的 Q100000 当前/软伤状态；不能以一个数替代三者。硬伤 unavailable 必须保留。 |
| 战宽、将领与优势 | battle-control 提供真实 `base/final_combat_width`、双方实际 `selected_commander_character_id`、当前 roll、base/resolved advantage。 | v3 的 `precontact_width` 和按假定请求顺序选出的 commander/holding 不是当前缓存战宽、当前选中将领或既有优势；实际将领的下一次 roll bounds 和动态优势分解须同帧补齐。 |
| 反制、骑士与动态参战者 | v3 可读当前军团类型、modifier、骑士及假定接战 counter；battle-control 可读当前 side 的完整 ordered army/entry census。 | 原生 v2 `BuildCounterSideEntries` 用 `regiment.current_soldiers * 100000`，不是 battle entry `current_fighting_raw`。v3 的 knight roster 也未与当前 battle-side 存活/参与集合逐项配对。现有 trial 在开头冻结军队与 entry，未来加入/退出仍是 `fixed_participants` 假设。 |
| 撤退可行性与终局 | battle-control 另给该 owner 的 native retreat legality、side flags、winner/finalized；现有撤退 read/action 研究单独维护。 | 可否下达撤退与“继续/撤退哪项更好”是不同问题。本审计只定义后者的输入边界，不声明原版 AI 撤退评分已闭合。 |

源码锚点：`native_bridge/src/ck3_11906.cpp` 的 `ReadCombatSimulationInputs`（`10506` 起）和 `ReadBattleControlSnapshotSample`（`14669` 起）、`native_bridge/src/combat_v3.cpp` 的 `ReadCombatSimulationInputsV3`（`4166` 起）、`simulation/combat_input.py` 的 `freeze_combat_simulation_input`（`676` 起）、`simulation/research_envelope.py` 的 `simulate_trial`（`173` 起）。路径均相对 `ck3_autonomous_player/`。这些是代码合同，不代替新的实机同帧回读。

## 最小新增 typed 只读接口

建议 `query-active-combat-forecast-inputs-v1-<subject_public_cunit_id>`。返回 `status=available|unavailable`、机器可读 `unavailable_reason`、`input_observation_ready`，并采用与 battle-control 相同的 paused、application-main、double-sample、前后 revision/episode/date/connection generation 和 full-generation ID 校验。输入必须是可控、尚未最终结算且未在 daily dispatch 中的真实 `CombatID`；终局、phase 非法、角色/side 变化、逐 entry 不完整或任一必需源为 unavailable 时整体拒绝，不能部分字段默认 0。

`available` 的最小载荷：

1. **绑定**：exact EXE/build、`snapshot_id`、公开/native revision、date、episode、connection generation、source `CombatID`/Province/subject CUnit/CArmy、读取的 native 线程与两次采样一致性。
2. **现役 side**：真实 side0/side1 和 coalition 映射、完整且有序的 current ArmyID/CArmyID/owner 列表；每军真实选中 commander 与后续 roll bounds，当前 phase/day/roll/cadence、优势源、winner/forced/finalized、双方 cached base/final width；不得从假定 entry/请求顺序回填。
3. **战斗 entry**：每个 levy/MAA 的 generation-valid RegimentID、军队和 side backlink、当前 `starting/current_fighting/soft/hard` Q100000、main phase 资格、当前有效 damage/toughness/pursuit/screen、class/stack/counter operands；逐侧 entry 求和必须与原生 stored fighting/soft/side-strength 对照，并明确每个不等式或不可得原因。骑士参与/死亡/受伤状态与 phase-effect 来源需单独配对，不得仅以军团当前 knights 列表推断。
4. **决策前提**：真实地形/原接战 crossing/holding、双方当前反制/损伤修正、当前可撤军的 owner subset 与 native legality；后一项仅作行动可行性，不能偷换成撤退效用分数。

新载荷使用独立 `participant_policy=observed_active_combat_resume_fixed_future_participants`，不可伪装成 `explicit_hypothetical_fixed_at_contact_no_reinforcements`。下游需要独立的 resumed trial 初态：从所读 phase/day、roll/cadence、entry soft/current、当前 cached width、已知已发生的硬伤基线起跑；只计**从现在起**的新增伤亡与结果。未来加入/撤退仍须以独立未知项或有证据的动态事件表示。模型试算可继续采用显式风险预算，但风险阈值需要按“继续打”与“合法撤退”的后续代价定义，不能直接复用战前接战的 25% p90 硬伤门。

在此接口和 resumed kernel 实现、聚焦静态回归及同一原版存档暂停帧 live 配对前，智能体应继续正常使用现有**战前接战**有界预测；对现役 `CombatID` 只能使用已经独立证实的控制/撤退合法性，不得把 v3 的假想接战分布写成该战的继续打胜率。

## 本轮聚焦验收

在隔离工作区 `D:/wai`，显式使用主工作区 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；相对 venv 不存在。解释器与依赖 probe 为 Python `3.14.7`、pytest `9.1.1`，`PYTHONPATH=D:/wai/ck3_autonomous_player/src` 指向本 worktree：`test_general_battle_strategy.py`、`test_combat_input_adapter.py`、`test_general_battle_forecast.py` 共 **19 passed、11 subtests passed**；`git diff --check` 通过。测试使用现有原版 v2 fixture 证明战前估计仍可运行，并对“选中军队已有 ongoing CombatID”与“该观察字段缺失”分别断言决策入口拒绝。本检查不构成 active-combat 原生读口或实机验收。
