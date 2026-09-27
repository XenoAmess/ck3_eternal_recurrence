# 现役战斗研究核的追击修正输入缺口（CK3 1.19.0.6）

适用原版 `1.19.0.6-steam23530548`，本机只读复验的 `ck3.exe` SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本轮没有启动 CK3。`verify_combat_pursuit_modifier_readback_abi.py` 的 11 处锚点、`verify_combat_final_side_attribution_static.py` 的 12 处 site / 8 条直接调用边均通过。以下分清原版静态证据、既有实机样本和研究核的条件性修复。

## 原生链与偏差

[主研究的追击节](battle-simulation.md#pursuit--screen)给出 exact ABI：每日 `0x23CD2E0` 通过 `0x23C8FF0` 从**胜方有效 side** 读 enum `0x105` pursuit efficiency，从**败方有效 side** 读 enum `0x18B` retreat losses。读数进入每日追击预算的合并倍率；`0x23CD660` 按冻结初始软伤池、征召兵先于职业兵士的存储顺序，做两遍分摊。第一遍 `0x23CDA59` 和第二遍 `0x23CDC77` 都先调用 `0x239C840` 写底层硬伤，随后分别在 `0x23CDA72`、`0x23CDC89` 扣 combat entry 软伤。[写入顺序的独立 verifier](combat-pursuit-write-order-and-final-side-attribution-static-2026-09-27.md)约束的是原生指令和直接调用，不证明任意未来局面的完整整场概率。

`combat_core.apply_three_day_pursuit` 已有两个 signed raw 入参和上述数值链；真实偏差在 `research_envelope.PhaseEventsDisabledResearchKernel` 的现役恢复路径：调用这个函数时过去没有传侧修正，因而 Python 默认两者为 `0`。这会让研究核在胜方/败方恰好有非零修正时，尽管拿到了正确 entry，也算错追击期硬伤。它不是 `combat_core` 分摊算法本身的错。

[attempt-004 的原版三日追击](battle-simulation-episode01-live-case.md#2026-09-26-追击三日同一独立回放的逐团与账本对拍)给出一个量化反例：胜方效率 `0`、败方退却损失 `-25,000`，沿相同首日 entry 和冻结池连算，正确模型每日硬伤 raw 为 `2,070,677 / 2,097,473 / 2,126,119`，总计 `6,294,269` Q100000，匹配该样本已可读的原版账本。只把败方修正误置零，其余输入保持一致，则依次成为 `2,760,921 / 2,808,726 / 2,861,216`，总计 `8,430,863` Q100000：高出 `2,136,594` raw，约 `21.36594` 名实际兵员的量纲。后一列是**模型反事实**，不是另一条原版观测。[机器夹具和回归](../../ck3_autonomous_player/tests/unit/test_native_pursuit_receipt_parity.py)锁定这两个结果。

## 本次最小修正及证据边界

`ActiveRouteSideState` 现在要求显式提供两侧各自的 `pursuit_efficiency_modifier_raw` 和 `retreat_losses_modifier_raw`，拒绝缺值、布尔值或非 signed int64。现役恢复研究核在已判定的终局中，取**胜方** route 的前一项与**败方** route 的后一项送给三日追击。两种败方朝向都有定向回归；对固定接战预演路径，原先“未观测修正置零”的研究假设保持原样。manifest 更新为 `active-main-resume-research-v2`，明确声明“按输入侧修正冻结至终局”是研究假设，`fidelity_gate` 仍为 false。

`battle_control_snapshot.pursuit_modifier_sides` 已有按 CombatID / side 对齐的 signed raw 字段及规范化校验，但**生产游玩策略尚未构造 `ActiveMainResumeState`**；本次用的是测试显式给出的同帧值，不可宣称实战 agent 已自动吃进这些修正。若未来主阶段跨日后 commander、modifier、援军或 side 成员变化，冻结值可能失效。应先在同一 CombatID、side、日期与 modifier revision 下组装 active input，再做跨日/终局的原版对拍；非零败方 screen、部分撤退同步追击和终局事件副作用仍各有独立缺口。这个修复只消除一个已量化的研究核输入遗漏，不把单日或单战例 parity 提升为整场胜率校准。

复核命令（无 CK3 启动）：

```text
py ck3_autonomous_player/native_bridge/research/verify_combat_pursuit_modifier_readback_abi.py --exe <exact-ck3.exe>
py ck3_autonomous_player/native_bridge/research/verify_combat_final_side_attribution_static.py --exe <exact-ck3.exe>
set PYTHONPATH=ck3_autonomous_player/src&& tools/.venv/Scripts/python.exe -m pytest -q ck3_autonomous_player/tests/unit/test_native_pursuit_receipt_parity.py ck3_autonomous_player/tests/unit/test_active_combat_resume_kernel.py ck3_autonomous_player/tests/unit/test_active_counter_output_098_envelope.py
```
