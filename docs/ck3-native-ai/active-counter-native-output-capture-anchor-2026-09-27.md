# 原版日界反制输出的被动捕获锚点（2026-09-27）

证据级别：[static-confirmed]，仅绑定 CK3 `1.19.0.6` exact EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本次扩大只读反汇编器 `counter_damage_wrapper` 范围至完整函数 `0x23CAE70..0x23CB1D0`，定位到**不主动调用原版 helper**即可观察它真实输出的点；尚未装载新 detour 或做日界实机验收。

原版 wrapper 在 `0x23CAF13..20` 以 `R9=RBX` context、`R8=&[RBP]` 输出 header、`RDX=RDI` 反制方 MAA header、`RCX=RSI` 被反制方 MAA header 调用 `resolve_counter_classes` (`0x23CF1B0`)。它在调用前将 `[RBP]` 数据指针和 `[RBP+8]` capacity 清零、`[RBP+0xC]` count 清零，并在 `[RBP+0x20]` 设置 caller-owned backing。紧接调用返回的 `0x23CAF25` 是候选被动捕获点：此时 caller 栈仍有效，输出 header 可直接检查；`0x23CB042..46` 随后以 MAA class index 读取 `[RBP]` 所指 `int64` 向量用于原版出伤。这个后续消费互证了向量含义，而不是仅凭 helper 名称推断。

exact 入口字节：`0x23CAF20: E8 8B 42 00 00` 是 helper call。候选补丁位置 `0x23CAF25` 起 14 字节为 `4D 89 3E 48 8B 3E 48 63 46 0C 4C 8D 3C 40`，恰好覆盖四条完整指令：`mov [r14],r15`、`mov rdi,[rsi]`、`movsxd rax,[rsi+0xC]`、`lea r15,[rax+rax*2]`。任何运行时探针都必须先逐字节验证 exact anchor，完整重放这些指令，并在所有失败/清场路径恢复原字节。这里给出的是施工锚点，**没有**宣称补丁已安全实现。

最小安全探针应复用现有受管、默认关闭的 `combat_phase_event_trace` 生命周期：只在暂停且证明无正在执行的战斗日界时装载；跟踪原 caller 的 CombatID、side 与原始 `+0x40` MAA 顺序；在同一线程的 `0x23CAF25` 仅复制 `RBP` header 和有界 `int64[class_count]`，核对 header count/capacity、可读性、前后身份与 canary，不调用 helper、不改变 RNG、world 或 entry；两侧输出必须成对出现。`0x23CAE70` 是两侧出伤共用 wrapper，不能把同一回调的两次结果混成一个方向。装载、日界、卸载及进程清场都要保留独立 attempt 的原始回执。

捕获后须对照 088 当前帧 census 和 092 原生增援重排：输入 header 的 full RegimentID/current raw、primary owner/context、class_count 必须与捕获时刻原生 side 一致；class 为负、兵团归零、增援或主参与者变化分别验证。**本锚点本身不关闭** `active_regiment_counter_class_stack_context`；只有配对日界实证和 Python/智能体消费合同均通过后，才能让现役续算使用该结果。
