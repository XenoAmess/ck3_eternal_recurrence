# R06：default OFF 的 .4 指令级 ADD 硬件观察候选

本候选来源机器 `machine_id=desktop-3fevhd2-1c74096080`，源码冻结
`1463bd9b4b89612d283dd45ac4ec9efbf22f048d`。源约束为 CK3 1.20.0.4 / Steam25734779 /
EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
外置 `high-parallel-refill-a02` 在2026-10-15完成源码和MSVC `/Zs` 检查；
**没有生成/执行新EXE、attach进程、启动SDK/游戏、操作桌面或取得实际ADD样本**。
R0174当前现场不使用此候选，必须等待新的独立冷窗口。

## 选用已存在的外部硬件断点路线

现有 `native_bridge/research/war31_two_point_hwprobe.cpp` 是具名可复用基础，
原文件 SHA `6c9bd24437c44d0906624468b874694d6d81b5f853652c3564ed757a6322beb9`。
它使用外部 `DebugActiveProcess`、线程 DR0/DR1 和 `ReadProcessMemory`，
目标线程不运行观察器C++。不能直接运行它的旧1.19地址/EXE或继承旧业务资格。

新 `research/refill_add_hwprobe_12004.cpp` 仍使用同一调试循环，但固定为实际 .4 两点：

| 点 | 实际原字节 | 捕获意义 |
|---|---|---|
| `2A98B88` | `01 50 F4`，`add dword ptr [rax-C],edx` | 原ADD尚未执行，读真实RAX/RSI/RDX/RCX与物理前态 |
| `2A98B8B` | `8B 48 F4 3B 48 F0`，MOV/CMP | ADD已由CPU执行，MOV尚未执行，独立读即时物理后态 |

这些字节直接复用[已闭合的 .4 源](army-natural-regular-core-entry-observation-12004.md)
和[补员应用专题](episode04-refill-application-12004.md)；本a02不新增EXE读取。
此路线没有修改ADD代码、猜patch长度、跳回重放、模拟current写入或向目标注入C++回调。
它只修改调试寄存器、清自己的Dr6状态并设置RF，以正常继续原生指令。
因此无需把普通函数入口wrapper冒充任意指令处的GPR/flags/XSTATE trampoline。

## default OFF、输入与实际留存

`XAR_ENABLE_REFILL_ADD_HWPROBE_12004=0` 是源码默认值，程序直接退出3，
不打开目标进程。ON构建仍要求显式 `--enable`，实际PID/create-time、唯一线程、
完整Regi FullID（raw u32）、物理slot0..6、机器ID、独立新raw/ready路径和有限timeout。
原生literal code bytes、ck3.exe模块和实际create-time不符则拒绝attach；
完整EXE版本/SHA来自现场owner的实际冻结runtime准入，窄内存签名不代替整build身份。

指定cohort须来自当次正常paused Army→ArRg→DATA的完整generation+physical映射，
不能复用其他PID的地址或以Public CUnit ID代替Regi FullID。只有显式目标TID被设置DR；
目标已有debugger、Dr0..Dr3/Dr7占用或TF stepping时拒绝。

每个留存边界独立读取实际 RSI Regi、Regi+10 FullID/+14魔数、当前RBX manager occurrence
所存FullID、RAX锚点、RSP、真实EDX q bits和RCX q-index，以及完整252B七槽。
要求 `RAX=RSI+28+slot*24`（十六进制），target current=`RAX-C`、maximum=`RAX-10`。
还读取raw关联ArRg ID，按已闭合全generation resolver核实际ArRg/CArmy，独立复制关联ArRg
的完整DATA（最多64条；原count超界保持不完整，不截断盖章）。七槽以原始hex保全，
DATA保留stored ordinal、raw0/raw4、persistent ID和physical ordinal及真实重复别名。
这只是关联ArRg的DATA，不声称发现世界中所有其他共享别名。

配对须为同一PID/create-time/module/TID、相邻probe ordinal、相同RSI/RAX/RSP/RBX、
完整generation、物理slot、q-index和EDX，且除该current DWORD外七槽逐字节不变。
验证 `after_u32 == uint32(before_u32 + actual_EDX_u32)`。
q=0和负q同样保留；signed endpoint数学净差与DWORD模加分别说明。
matching关联DATA前后完整一致时单独标记，不用DATA别名重复计物理ADD。
硬件前/后两点不会采到之后 `2A98BEF` 的pair clear，因此不把此ADD等同最终core净变化。

全manager热循环仍会产生非目标CPU trap，过滤只减少留存。候选有**总100000 debug hit**
和1–300秒显式wall上限；命中不足、超限或任一配对歧义均为真实RED/unknown，
不能说无ADD或零补员。调试暂停开销也不能拿去比较正常行军性能。

## 共用自然父token的边界

与starvation/county lane共用 `ck3_12004_native_invocation_context.hpp` 的
`NativeInvocationScope12004` 和 `regular_refill_core=3`，不另起counter/TLS栈。
候选给现有 `InvokeArmyRegularCorePassive12004` 增加单独default OFF宏
`XAR_ENABLE_REFILL_CORE_INVOCATION_PARENT_12004`，仅围绕真实 `original(manager)`
建立同thread scope，typed payload为当次 `ArmyRegularCoreObservation12004`；原函数仍一次。
该scope的token和既有native event clock是不同域，必须通过实际payload关联，不能把数值当相同。

**外部debugger不能调用目标线程TLS。** 本候选没有伪造跨进程token通道，
raw输出中 `native_core_token=null`、`natural_parent_token=null`、
`natural_attribution_ready=false`、`full_window_coverage_ready=false` 保持固定。
RSP+58只是原始返回地址；原core已被普通entry detour包裹时，那里可能是opaque wrapper
continuation，不能因此拒绝真实physical ADD，也不能用它冒充自然post-date父链。

要补严格共同token，下一小步是在实际core-owning-thread将共用frame的**标量副本**
发布到单独read-only diagnostic carrier：schema/source epoch、active、TID、parent kind、
invocation token、actual core entry event和natural parent event/date/manager/GameState。
使用前后sequence fence防撕裂，original返回时明确inactive；private握手发布当前carrier地址。
外部probe两端须各自读到同一稳定active frame并与其actual TID对应。
不得让query线程读自己TLS，不把stack payload地址、PID、QPC或相邻journal序号生成token。
该carrier尚未实现，不能把本硬件候选标为完整自然R06归因。

## 现有MCP与最小开关只读接口

对当前bridge/mcp/native的具名检索没有 `IsMilitaryReinforcementsEnabled`、
`ToggleMilitaryReinforcements` 或对应action/readback provider。`ck3_click_white_control_v1`
仅允许白绮固定按钮，numeric版本仅六项技能；它们不能组合为军事页任意checkbox。
当前native permission bool可以读到结果，无法独立读回“这次toggle已经改变”。

新增 `ck3_12004_military_refill_switch_readonly.hpp` 给出最小只读primitive：
`ReadMilitaryRefillSwitch12004(read,context,source_character_pointer,full_id,actual_exe_sha)`。
它要求actual .4 hash，核Character完整generation+Char魔数，读取+1C0组件与byte4A9，
并独立重读身份/组件；真实0得到enabled=false，missing组件/失败/身份改变保留null。
caller必须先沿真实Regi+130/+12C来源分支解析补员owner，不能统一传玩家角色。
此primitive没有setter、GUI callback或action ACK，不扩张成普通toggle命令。

后续可在已有army-strength完整DATA查询的persistent来源条目附加optional
`military_refill_switch_state_v1`，携带实际来源CharacterID、原始byte、enabled和读取诊断；
缺少来源解析就拒绝该叶。普通toggle action仍需单独封闭实际原版GUI callback/validator，
并在合法动作后用此读口独立读回，再观察下一自然preparation和真实ADD。

## 后续冷fixture与放行顺序

当前完成的是exact源码复用及MSVC `/Zs`：probe OFF/ON、只读switch header、
同shared-context header的core scope ON。没有native运行或live GREEN。

下一步用标准producer在获准research根构建，取得精确EXE SHA对应的SYSTEM verified
排除回执后才允许运行新EXE。只在隔离的自建fixture进程验证同字节ADD前后两点：
正常q、q0、signed wrap和负q；完整/部分/重复DATA；非目标TID/cohort和hit/time超限；
已有DR/debugger/TF拒绝；异常/取消/线程退出；Get/SetContext、ContinueDebugEvent失败；
所有正常和失败出口精确恢复原DR0..3/Dr6/Dr7并实际detach、原进程存活、原指令一次、
完整GPR/flags和启用XSTATE不被观察器改写。fixture地址只允许编译期fixture入口，
不能成为生产任意地址API或旧1.19执行入口。

修正了旧helper的具体清理缺陷：cleanup循环真实检查 `ContinueDebugEvent` 返回，
失败时保留pending，后续使用原exception disposition；不再把ACK当成功继续。
observer内C++异常也走cleanup而不直接跳出wmain。任何恢复/继续/detach失败都是独立RED，
尚需上述故障注入证明其安全恢复，不能先给当前游戏运行资格。

冷fixture和独立clean detach通过后，再由Root另冻结正常战役、Steam离线、runtime/
Defender/source/容量及finite observation plan，才可取得一条实际physical ADD；
缺carrier时只授该条物理写入，完整自然父链、开关对照和整窗累计继续单列。

外置回执 `high-parallel-refill-a02/DELIVERY.actual.json`、`SYNTAX-ONLY.final.actual.json`
及相对patch绑定本机与具体文件。共享512MiB池中本lane上限8MiB，原复核期限
`2026-10-16T07:45:01.597Z` 不自动延长。主树仍完全冻结，Root闭场后再合入。


受控 synthetic 双 EXE 的实际冷运行、DWORD wrap、TID/失配、有限退出与 debug-register 恢复资格，以及已修的 process-query 权限阻点，见[冷夹具资格](episode04-refill-hardware-add-cold-qualification-12004.md)。该资格不计作 CK3 actual ADD 或 R06 业务验收。
