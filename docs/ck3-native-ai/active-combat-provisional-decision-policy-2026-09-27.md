# 现役战斗的同帧观察比较与限时决策（2026-09-27）

本项是**智能体策略阈值**，不是 CK3 原生胜率公式，也没有把现役整场续算标为已完成。它只比较暂停同帧已出现的主战兵力：两侧各自的 `current_fighting_raw` 总量，以及 `current_fighting_raw / starting_raw` 留存比例。整数除法复用 `combat_core.fixed_div` 的 `100000` 定点尺度。只计 `fights_in_main_phase=true` 的征召兵和职业兵士条目；储备、骑士和未来增援不填零，也不以玩家 UI 总兵力替代原生战斗条目。

策略仅在 battle-control 父帧、查询序号、subject、snapshot ID、公开 revision、native revision、日期与受控军队战斗状态一致，且父帧通过 `normalize_battle_control_snapshot_v1` 时生成比较。如果存在 `active_combat_resume_inputs_v1`，还必须通过与父帧的严格校验。战斗必须处在未结束的 main phase，两侧起始与当前主战量都大于零且 `current<=starting`。否则比较为 `null`，既有策略不变。多场活跃战斗时，比较不能代表全部 CombatID，也不改变全局推进。

当**我方当前主战量不高于对方一半，且我方留存比例不高于对方一半**时，标记 `severe_observed_disadvantage=true`。这是保守的观察阈值，并非胜负判定。若既有策略原本要启动较长的 decision-epoch 哨兵，且 `life-advance` 可用，智能体改为只推进一天后重新查询。精确的 terminal-cruise 门槛不受这个粗比较覆盖；不据此撤退或下达路线命令。一般接战入口继续禁止把已在战斗中的军队送入首次接战 v3 计算，其状态可显示 provisional 比较，但不能据此授权新接战。

输出把 `whole_battle_win_probability` 保持为 `null`，`model_fidelity=observed-current-and-starting-only`。`active_combat_resume_input.status` 仍是 `unavailable`、`input_observation_ready=false`、`used_for_decision=false`，只在独立的 `provisional_comparison_status`、`provisional_comparison` 和 `provisional_comparison_used_for_decision` 中报告这项策略证据。这使原生续算缺域与已使用的保守观察阈值不混淆。缺域以当次有效原生回执为准；没有回执时仅列已知研究缺域，不声称它们已在该帧核实。

后续要将现役比较升级为整场胜率，至少仍需验证下一日反制 class/stack/context 的取值顺序、非骰子优势来源、骑士参与和动态兵团入场、增援/撤退以及终局写回，并做跨日原版对拍。详见[现役战斗输入缺口](active-combat-forecast-input-gap-2026-09-27.md)与[战斗后半程计划](battle-second-half-research-plan-2026-09-26.md)。本次仅完成离线合成回归；没有启动 CK3，没有取得新的实机策略行动回执。
