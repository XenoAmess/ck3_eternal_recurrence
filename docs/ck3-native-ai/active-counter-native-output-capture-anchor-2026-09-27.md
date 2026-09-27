# 原版日界反制输出的被动捕获锚点（2026-09-27）

证据级别：[static-confirmed]，仅绑定 CK3 `1.19.0.6` exact EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本次扩大只读反汇编器 `counter_damage_wrapper` 范围至完整函数 `0x23CAE70..0x23CB1D0`，定位到**不主动调用原版 helper**即可观察它真实输出的点；尚未装载新 detour 或做日界实机验收。

原版 wrapper 在 `0x23CAF13..20` 以 `R9=RBX` context、`R8=&[RBP]` 输出 header、`RDX=RDI` 反制方 MAA header、`RCX=RSI` 被反制方 MAA header 调用 `resolve_counter_classes` (`0x23CF1B0`)。它在调用前将 `[RBP]` 数据指针和 `[RBP+8]` capacity 清零、`[RBP+0xC]` count 清零，并在 `[RBP+0x20]` 设置 caller-owned backing。紧接调用返回的 `0x23CAF25` 是候选被动捕获点：此时 caller 栈仍有效，输出 header 可直接检查；`0x23CB042..46` 随后以 MAA class index 读取 `[RBP]` 所指 `int64` 向量用于原版出伤。这个后续消费互证了向量含义，而不是仅凭 helper 名称推断。

exact 入口字节：`0x23CAF20: E8 8B 42 00 00` 是 helper call。候选补丁位置 `0x23CAF25` 起 14 字节为 `4D 89 3E 48 8B 3E 48 63 46 0C 4C 8D 3C 40`，恰好覆盖四条完整指令：`mov [r14],r15`、`mov rdi,[rsi]`、`movsxd rax,[rsi+0xC]`、`lea r15,[rax+rax*2]`。任何运行时探针都必须先逐字节验证 exact anchor，完整重放这些指令，并在所有失败/清场路径恢复原字节。这里给出的是施工锚点，**没有**宣称补丁已安全实现。

最小安全探针应复用现有受管、默认关闭的 `combat_phase_event_trace` 生命周期：只在暂停且证明无正在执行的战斗日界时装载；跟踪原 caller 的 CombatID、side 与原始 `+0x40` MAA 顺序；在同一线程的 `0x23CAF25` 仅复制 `RBP` header 和有界 `int64[class_count]`，核对 header count/capacity、可读性、前后身份与 canary，不调用 helper、不改变 RNG、world 或 entry；两侧输出必须成对出现。`0x23CAE70` 是两侧出伤共用 wrapper，不能把同一回调的两次结果混成一个方向。装载、日界、卸载及进程清场都要保留独立 attempt 的原始回执。

捕获后须对照 088 当前帧 census 和 092 原生增援重排：输入 header 的 full RegimentID/current raw、primary owner/context、class_count 必须与捕获时刻原生 side 一致；class 为负、兵团归零、增援或主参与者变化分别验证。**本锚点本身不关闭** `active_regiment_counter_class_stack_context`；只有配对日界实证和 Python/智能体消费合同均通过后，才能让现役续算使用该结果。

## 输出 header 只读复制器的静态施工

[`ReadCombatCounterOutputV1`](../../ck3_autonomous_player/native_bridge/include/xar_bridge/combat_counter_output_readout_v1.hpp) 已按 exact 16 字节 header 布局实现有界复制：调用方必须给出预期 class 数 `1..4096`；数据指针非空、`count==expected`、`count<=capacity<=4096`，复制后再次核对 header，访问异常使整个结果失败并清零。合成 MSVC 测试覆盖正常向量、错 class 数、容量不足、空指针、超界容量和不可读指针。它只是被动探针的内存读取原语，不独立证明游戏机制。

## 受管、可选探针施工状态

随后已在源码中加入默认关闭的 `capture_runtime_counter_output`：原始 `0x23CAF25` 14 字节先逐字节比对，再于已暂停且无追踪环执行时安装独立 detour；trampoline 在原版 helper 返回后、四条原指令执行前传递 `RBP/RSI/RDI/RBX`，保留标志位和易变寄存器，复制两侧输出，然后逐条重放原指令。安装、卸载失败均保留补丁所有权并让受管驱动停止进程，禁止悬空跳转。追踪环核对原始 caller、CombatID、side backpointer、MAA header、次序和容量；显式启用时才在 wire 中给出输出向量及是否成对，普通七边界回执不改变。独立合成测试覆盖默认关闭、两侧复制、坏 header、原始补丁恢复和 wire 合同。

上述只是**实现与离线合成验收**；尚未获得同一存档、同一 exact EXE 的实机两侧原始输出。`active_regiment_counter_class_stack_context` 因而仍是缺项，现役续算不得把探针源码当作已验证输入。下一步必须记录单独日界 attempt 的 EXE/DLL/save SHA、完整命令回执、原始向量、七边界状态、进程清场，并以两侧 class 与 088 census/092 增援顺序交叉核对。
