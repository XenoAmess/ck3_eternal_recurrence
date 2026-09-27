# 现役反制输出追踪 097：暂停查询线程不等于战斗执行线程

本页接续 [096](active-counter-output-trace-attempt-096-2026-09-27.md)，仅适用于 CK3 1.19.0.6、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 与第 11 日冻结存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`。097 独立 DLL SHA-256 `B854EA319A560E66DC5AFA373F2BF15F726339437CBEECCA582CB0730FA15C44`，原始目录 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-097`。独立移动窗口截图 `steam-topmost-2.png` SHA-256 `57F9D0A17CE1DBDCE3548FB3F89A874FA2B73B107F6898ECFC8B68D58854690F` 显示 Steam 左下“离线模式”；未切换 Steam 模式。

从同一存档再次只推进一个原生日界，原始 `c097-trace-finish.json` SHA-256 `838AABF41F0E4D8FBB089364428FB00BA22B51FD8D1EB4CAF538636E17B84BA5`。`runtime_counter_output` 明确返回 `requested=true, hook_calls=12, target_calls=2, count=0, pair_complete=false, first_failure_gate=33`，`failure_flags=1048576`。`33` 是 096 合并码 `3` 的细化：目标战斗调用已通过 committed boundary 六条、侧方捕获次序与 caller/header 身份检查，但 `GetCurrentThreadId()!=plan.owner_thread_id`。这里的 plan owner 来自暂停查询，而真实日 tick 可在另一个执行线程；同一个 096 实机 join-width 已给出独立的执行线程 `7364`。因此原拒收是研究钩子自己的线程假设错误，不能据此推断原生反制为空。

097 的七个原生边界、两侧 post-counter attack 与 outgoing damage 仍成对，完整 trace 因这一项返回 `trace_unavailable`。只读摘录 `readonly-summary.json` SHA-256 `67F979A2AB0FD3C4E1597AEEA4E158D813AE1011F3349A0266710D50BCD5CF82`；由 096 脚本克隆时内部 `attempt` 字段仍误写 `96`，以目录、`c097-*` 原始请求/回包和本页哈希为准，历史文件不改写。`cleanup-check.json` SHA-256 `44AD6AE207BCF36B8B668790DACDDF3E11C22F6F56020C6482814746BA6F226D` 记录 CK3 进程树、job 和控制文件全部清理。

下一版诊断桥接保留 outer outgoing caller 的线程局部上下文、目标战斗双侧指针、原生返回地址、header、六边界和侧方次序等校验；移除与暂停 UI owner 的不成立线程相等约束。新的跨线程单元测试模拟 UI owner 与战斗计算线程不同，确认捕获原生输出而不改变原函数结果。此修改只有在新的独立实机 attempt 得到双方 class 向量且同日 entry、增援和反制后数值能核对时，才可提升为智能体续算输入；097 自身仍是 RED 诊断证据。
