# 将领内部二次调用 aggregator：103 bit64 的原版控制流（2026-09-27）

103 的受管原调用诊断出现 `available=false, failure_flags=64`，但记录中的两侧分项和最终缓存等式闭合。该 bit 由 bridge 的 `AggregatorHook` 未通过调用点/side/顺序 gate 设置，不能仅因数学闭合而清除。103 原始 attempt 保留 RED；本页只给 CK3 `1.19.0.6`、`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的独立静态解释和修复门槛，未启动 CK3。

[`verify_active_advantage_nested_calls.py`](../../ck3_autonomous_player/native_bridge/research/verify_active_advantage_nested_calls.py) 只读原始 EXE，先复核[现有来源链](active-combat-next-day-advantage-components-2026-09-27.md)的 SHA、`.pdata` owner 和调用链，再核下表六处精确字节及两个 `call` 的共同目标 `0x2307230`：

| 原版路径 | 精确指令 | 对返回值的归属 |
| --- | --- | --- |
| 将领内部嵌套调用 | `0x23079FE call 0x2307230` → `0x2307A03 mov rcx,[rax]` → `0x2307A06 add [rsi],rcx` | 这次 aggregator 返回已经并入 **commander_raw**，发生在 `CommanderHook` 返回前。 |
| side total 主调用 | `0x2307EB5 call 0x2307230` → `0x2307EBA mov rcx,[rax]` → `0x2307EBD add [r12],rcx` | 这次返回才属于独立的 **aggregator_raw**。 |

103 的旧 hook 在 `g_side_context` 有效时把两次调用都按主调用检查；嵌套调用返回地址为 `0x2307A03`，且当时 `helper_calls=0`，不满足原 gate 的 `0x2307EBA`/`helper_calls=1`，因此**这条原版路径足以产生** bit64。之后主调用仍能成功记下数值，能解释“行内 complete、全局 unavailable”的并存。103 的旧 wire 没有首失败调用点，不能仅凭数值闭合断定它是唯一触发者，更不能直接清除异常标记。

修复后的 hook 以精确返回点分类：`0x2307A03` 仅在同 Combat、同 side、将领仍未返回、且此前未见嵌套调用时记录 `nested_aggregator_calls`；不单独写 `aggregator_raw`，因为原版已将它合进将领输出。`0x2307EBA` 仅在将领已返回、同 side、且主调用尚未记录时写 `aggregator_raw`。未知 caller、空返回、Combat/side 不符、重复或顺序不符继续标 bit64，同时固定首个失败 gate、线程、调用绝对地址/RVA、side 和 helper 调用数供下一次定位。Python 合同接受旧 103 形状作历史诊断；新 wire 的 strict key、调用计数、首因范围及 bit64 一致性由 `normalize_runtime_advantage_components_v1` 校验，外层 finish 回执由 `normalize_experimental_advantage_components_response_v1` 校验。所有结果继续 `forecast_usable=false`。

104 须使用私有 trace 选项为 ON 的新 DLL，先过[离线字符串门禁](active-combat-original-advantage-observer-2026-09-27.md)，再从冻结存档新建 attempt 取样。只有 104 的原始调用归属、两侧等式、补丁清场和与无探针基线的状态对拍同时闭合，才能把当前调用的分项诊断视为 live-confirmed。即使如此，未来日非掷骰优势的输入叶子及转移仍未完成，不移除 `next_day_non_roll_advantage_sources`。
