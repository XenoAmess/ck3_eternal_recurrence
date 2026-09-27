# 104：同源日界原版优势分项观测闭合

104 从 [099 冻结的第 12 日暂停存档](active-counter-output-day12-checkpoint-attempt-099-2026-09-27.md)独立启动 CK3 1.19.0.6，并与 [100 原生反制输出](active-counter-output-cross-check-100-2026-09-27.md)对照同一 CombatID `16777218` 从原始日期 `53146512` 到 `53146536` 的一天。两次输入存档 SHA-256 都是 `E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731`，配对保存回执都是 `A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415`。104 启动清单与实测 preflight 的 EXE SHA-256 均为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；本次 DLL SHA-256 为 `DB4E5EE96EAA72836D3F853618A65A16F7346F6CC6B1E34C0F8E672138589B6E`。

104 使用[修复后的原调用观测器](../../ck3_autonomous_player/native_bridge/src/combat_advantage_components_observer_v1.cpp)区分指挥官 helper 内部的嵌套聚合调用与外层主聚合调用。受管 trace 七条边界齐全，主 trace `failure_flags=0`；优势分项 `available=true`、`failure_flags=0`、首失败 gate `0`，双方各有一次嵌套与一次外层调用。完整的一条缓存求值如下，数值单位均为引擎 Q100000：

| 项 | 原始整数 | 换算 |
| --- | ---: | ---: |
| 基础优势 | `-300000` | `-3` |
| side 0，指挥官 `34320`，roll `7` | roll `700000` + commander `3500000` + aggregator `0` = `4200000` | `42` |
| side 1，指挥官 `29829`，roll `8` | roll `800000` + commander `4200000` + aggregator `0` = `5000000` | `50` |
| 已解析优势 | `-300000 + 4200000 - 5000000 = -1100000` | `-11` |

双方选中指挥官 ID 与 roll 来自这一日**已经执行的原版缓存求值**，不是对以后每天选人、骰子或动态修正的预测。`aggregator_raw=0` 仅是这次两个原调用的返回值，不能泛化为游戏恒为零。标准化合同 `diagnostic_observation_complete=true`，同时明确 `forecast_usable=false`；暂停帧优势输入的刷新时序和仍缺的动态域见[优势叶子研究](active-combat-original-advantage-observer-2026-09-27.md)。

只读[104/100 对拍器](../../ck3_autonomous_player/tools/project_advantage_components_ab_104_100.py)按精确 SHA 读取两次 input-freeze、preflight、trace-finish，并冻结 104 的 session、report、cleanup 原始字节；用生产 `normalize_runtime_advantage_components_v1` 重验数值等式、调用计数与受管停机条件。[机器投影](../../ck3_autonomous_player/native_bridge/research/fixtures/advantage_components_ab_104_100.json)的 `--expected --check` 返回 GREEN。除上述优势行，100 与 104 的两侧 13 类反制向量、反制后攻击 `7086468150 / 1367059376`、最终出伤 `116572401 / 63568260` 原始整数逐值相同。反制 context 分别为 side 0 `125000`、side 1 `100000`，非满额类仍为 side 0 class 8，以及 side 1 class 0、1。

原始 attempt 保留在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-components-attempt-104`。`c104-trace-finish.json` SHA-256 `B92CF0978C4B5954704ADACE63C4DC5B3936396F491DA3872163BE7F4BA02A68`；input-freeze `855D2F8A763547C1054AA2FCCD167FB3652C351FAD8E6770BA3148066D75F3F4`。`cleanup-check.json` 记录 capture 退出码 `0`、`cleanup_ok=true`、最后 CK3 进程数 `0`，绑定 session/report SHA-256 `72571438CC5AC209B15AD3B0009089C29537B50B3DE815DD87C7ED372B003FFD` / `82F9ED3F1ACB5F939F3DA17C3ED734C1B21AFE7957C276189F4D7D71EB5697C1`。

这为同一存档的一次普通主战日提供了原版优势**回顾性分解**，且说明该观测器在此处没有改变已有反制和出伤。它不证明所有战局都无扰动，也不填平 `full_mutable_transition_bundle_complete=false`、`original_trace_ready=false` 所标的下一日可变输入缺域。[103 的失败清单与 bit 64](active-advantage-observer-103-100-ab-2026-09-27.md)仍按原始 attempt 保留为 RED，104 是单独的新尝试，不能倒填旧结果。
