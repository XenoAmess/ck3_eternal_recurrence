# 105/098 同源反制回执：同帧诊断的后验边界（2026-09-27）

**结论：**两次从同一 day11 存档重放的 battle-control 回执足以核对生产同帧反制诊断在 **各自观察帧** 对 class/stack/context 的计算，并暴露增援前后输入变化；它们**不能**验证 day11 诊断对 day12 原生日界输出的预测。105 的原生日界向量虽然与 098 数值逐项相同，但其整体 trace `status=failed, failure_flags=0x410`，边界顺序、side/return-site 身份及最终有界采集失败，加入军队 22 的 `runtime_join_full_entries` 没有有效回执。因此 105 不得作为第二次正式原生反制或出伤 parity。098 的单日反制向量对拍仍按[既有 098 结论](active-counter-output-cross-check-098-2026-09-27.md)限定。

只读[哈希绑定校验器](../../tools/audit_active_counter_105_retrospective.py)核对 098/105 各自的 `input-freeze.json`、preflight、前后 battle-control、trace-finish 原始 SHA-256，以及共同的 CK3 1.19.0.6 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 与 day11 save SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`。它调用生产 `normalize_battle_control_snapshot_v1`、`project_current_counter_attack_raw`、`outgoing_damage_raw`，输出[机器夹具](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_counter_105_retrospective_gate.json)。`--check` 的成功只表示这些**有限读数与 RED 门禁**没有漂移；其 stdout 始终明确 `formal_native_parity_105=RED`、`day11_to_day12_forecast_validated=false`。

| 观察点 | 侧 0 / 侧 1 MAA 数 | 侧 0 军队 22 | 实际战宽 | 生产同帧反制 class 1，侧 1 | 生产条件出伤前 attack，侧 0 / 侧 1 | 生产 neutral-advantage 条件 outgoing，侧 0 / 侧 1 |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| day11 暂停控制，`date_raw=53146488, phase_day=7` | 18 / 14 | 未加入 | 1480 | 54257 | 2844673326 / 1035382439 | 78769004 / 31061473 |
| day12 日界之后控制，`date_raw=53146512, phase_day=8` | 24 / 14 | 已加入 | 2220 | 10000 | 7086468150 / 1367059376 | 114871648 / 41011781 |
| day12 原生日界 hook，098 GREEN；105 仅局部数值可读、整体 RED | 24 / 14 | 098 的加入边界有证，105 缺边界 | 本表不把后帧宽度冒充开火前宽度 | 10000 | 7163402981 / 1455075113 | 116118762 / 67660992 |

所有整数均为 Q100000 域；表中的生产条件出伤固定优势乘数 `100000`，并不是当日日界真实掷骰/优势。098 与 105 的同帧投影数值完全一致；两者的原生日界向量、post-counter attack 与 outgoing 记录数值也完全一致。这是同一存档的确定性重放，不能当作独立战例。day11 的侧 1 class 1 为 `54257`，与 day12 原生 `10000` 不同：它**直接阻止**“把前一天的同帧诊断当成次日日界预测”的推断。day12 控制回执已在开火后，虽然其 class 1 也为 `10000`，但多个类碰到 `10000` 下限，而且人数、战宽、有效伤害和其他动态量可能在日界中变化，数值相等无法倒推开火前输入。后帧 attack/outgoing 与 hook 数值不同也不构成同阶段公式对拍；它们读取的时点与优势条件不同。

生产决策的可用边界因此保持：只在当前暂停帧、完整 `full_side` census 下把该条件反制用于缩短**可恢复的观察步长**；`next_tick_retention_validated=false`、`whole_battle_win_probability=null`。这次只复算生产数值核，没有重放完整策略查询绑定或一次真实行动选择。若要验证跨日预测，需要另一次身份与最终查询 GREEN 的受管采样，在增援**之后、主战开火之前**同时读取同日 class/stack/context、兵团人数、战宽及优势，再与该日原生反制与出伤逐阶段对照；day11 暂停帧或 day12 开火后帧都不能替代这个缺失切片。

本机复核：`D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe tools\audit_active_counter_105_retrospective.py --check`。原始 098/105 attempt 保存在 `D:\workspace\ck3_native_war_ai_promo_work\`，脚本只读，不启动 CK3，也不修改原始 RED attempt。
