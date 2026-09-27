# WAR31 双点硬件采样：实验驱动与证据边界（2026-09-27）

本页承接 [WAR31 静态追踪](war-termination-war31-static-followup-2026-09-27.md)
和 [R0221 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)。
本次只完成采样工具及离线验收；**没有附加 CK3，没有取得 WAR31 真实双点，
也没有提交投降动作**。精确版本是 CK3 1.19.0.6，`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

## 观察点与行为

[实验性 Win32 采样器](../../ck3_autonomous_player/native_bridge/research/war31_two_point_hwprobe.cpp)
在 `0x2E9F746`（`mov rsi,rax`）与 `0x2EC4410`
（`cmp dword ptr [rax+0x268],0x17`）指令执行前使用线程硬件断点，
读取该线程 `RAX` 和 `[RAX+0x268]` 的原始 dword。每次命中写入新建
NDJSON；必须按此顺序在同一线程、同一非零指针上恰好命中两次。
采样器不会提交游戏动作或改写 CK3 代码/目标内存，但调试附加、
线程暂停、DR0/DR1/DR7 和 RF 操作会改变被观察进程的执行环境，
因此不能称为零扰动观测。只可在另行协调的新受管 attempt 中使用。

CMake 中的生产目标 `xar_ck3_war31_two_point_hwprobe` 默认不构建，
只接受明确 PID；`--inspect-pid` 只读核验进程名、创建 FILETIME 和
内存中的精确指令字节，不附加调试器。夹具目标
`xar_ck3_war31_two_point_hwprobe_fixture` 才支持 `--fixture-pid` 与
一次性假进程地址，不能把夹具原始流用作 CK3 证据。

## 单次动作门禁

[受管驱动](../../ck3_autonomous_player/native_bridge/research/run_war31_two_point_hwprobe.py)
的 `assets` 模式只核文件，`live` 模式只查明确 PID 与内存锚点，
均不会附加。`capture --arm` 还要求此前各项 GREEN、全新外置 attempt
目录，才附加并等待。采样器写出 ready 后，**外部已授权受管动作执行者**
在同一个新 attempt 中提交唯一指定的 `surrender-war-16777231`；
本工具不点击、不调用投降。不可复用已完成的 104 或任何旧 attempt。

manifest schema 是 `xar.ck3.war31.hwprobe_manifest.v1`，必须固定
R0221 请求 ID、WarID `16777231`、episode
`native-29829-2bc2d599f7f9`、上述 EXE 哈希、
`approved_action_step=surrender-war-16777231` 和
`source_evidence_status=separately_authorized_unverified_by_probe`；还要有
本次动作 ID、原始日期、帧和 effect 调用 ID、预期 PID/创建时间、
以及 bridge DLL、checkpoint、driver state、sidecar、采样器和授权
回执 SHA-256。上述文件加 EXE 共七份必须逐字节匹配。
外部回执 schema `xar.ck3.war31.single_action_authorization.v1`
需同请求、WarID、episode、动作 ID/步骤一致，状态为 `authorized`，
且注明授权来源。驱动只能检查这些字段和字节，**不能自行鉴定回执
是否真的出自授权方**。动作 ID/帧/effect 调用 ID 等也来自外部源，
不是断点直接观察的事实。预检的具体参数以驱动 `--help` 为准；
不得为通过门禁自行制造回执或把夹具值带入实机 manifest。

采样器在取得双点、超时、取消或异常时尝试清除 DR 寄存器并脱离；
原始 terminal 分别写明清理与脱离是否成功。任一步未证实都判 RED，
不得升级为有效配对。若控制中断后采样器仍卡住，驱动保留进程和
全部素材，写 `manual-recovery-required.json` 交受管执行者处理，
不能强杀调试器来伪造清理成功。ready、原始 NDJSON、stdout、stderr、
预检和报告保留在该 attempt，不覆盖旧结果。

[离线组装器](../../ck3_autonomous_player/native_bridge/research/assemble_war31_hwprobe_trace.py)
要求原始流恰好一条 start、两个指定顺序的 sample、一条成功清理
terminal，且同 PID/创建时间、线程、指针、递增序号与 QPC。
结果始终是 `STRUCTURAL_PAIR_ONLY`：它不能认证真实 WarID、授权、
同帧或实际比较分支；更不能证明 title、holder、liege、vassal、资源、
停战到期日或其他投降条款已经写回。正式证据还需独立源报告与
游戏前后状态绑定。

## 已完成的离线验证

MSVC x64 Release 编译和生产目标 `--self-test` 通过；外置
`D:/ck3-research-artifacts/war31-hwprobe-20260927/fixture-007` 在同指针
同线程读得两次 type `0x17`，`fixture-008` 超时后报告 DR 清理和
脱离，假进程随后正常执行并退出。组装器与驱动 6 个单元测试在
普通和 `-O` Python 下均通过。夹具仅证明实验代码的正常和超时
路径，**绝非 WAR31 实机证据**。调试 API 的行为依据微软
[DebugActiveProcess](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-debugactiveprocess)、
[WaitForDebugEvent](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-waitfordebugevent)
与 [GetThreadContext](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getthreadcontext)；
RF 对硬件执行断点重触发的约束见
[Intel SDM 卷 3B](https://cdrdv2-public.intel.com/812388/253669-sdm-vol-3b.pdf)。
