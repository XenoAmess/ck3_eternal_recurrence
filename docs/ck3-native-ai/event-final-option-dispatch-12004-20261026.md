# 1.20.0.4 Select 最终入口：索引范围、两条调用路径与效果边界

本轮已完整读取并解码 `37BA990..37BAD3D` 的 **941 B**，确认 Select 最终入口的直接控制流。它先检查选项索引，再调用选中项的 `+0x310` 路径；随后另有 definition `+0x208` 的可选调用。完整入口没有直接读取物化选项的 enabled／shown 字段，**这不证明禁用项可以执行**：下游通用执行器和完整引擎资格仍未闭合。

`machine_id: xenoamess-full-tower-eb9d2c1186`；本岗实际读回与源审时间 `2026-10-25T23:50:17Z`。目标固定 CK3 **1.20.0.4 / build 25734779**，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本岗没有直接读取 EXE、运行游戏、调用 SDK 或启动编译／测试 JVM。

941 B 来自唯一采集者 `b64_execution` 的本轮 batch06：`D:/ck3-state/ck3-java-g2-native-static-resume61/batch06/capture01/window-004.raw`，SHA `939a02d0053fabf119192c95178d14bf78d12898670ecf8a70f73baaedb263ca`。本岗逐字节读回、SHA 与实际 result 相符，完整反汇编覆盖 941 B，终点 `37BAD3C RET`，未读取相邻 413 B。正式 batch 原件 `resume61/b64_execution/BATCH06-RESULT01.json` 为 22660 B / SHA `cede0d05a748a5715f77678f66dccd904df6938e96382fd4908309991f498aca`；来源身份、Request/Auth/Admission、三个实际 phase 的退出码与 Job/守卫按该记录。静态源取得不代表 Loaded/Game。

既有 Select 时序见[先移除、后处理选项](event-select-execution-poststate-order-12004-2026-10-26.md)。该页已被其他正式 plan 绑定哈希，本轮不改旧页；新证据与新结论保留在本页、[同源研究 plan](research/event-final-option-dispatch-12004-20261026.plan.json)和[生成图](research/event-final-option-dispatch-12004-20261026.graph.md)。

## 实际参数和直接分支

原 Select execute 的 `29BDF5B..29BDF68` 将栈上下文地址放入 `RDX`，从该上下文 `+0x1B0` 位置取对象指针放入 `RCX`，将 command choice 放入 `R8D`，然后调用 `37BA990`。941 B 入口把三者分别保存在 `RBX`、`R15`、有符号扩展的 `RDI`。当前 bridge 的既有源码也从 Event `+0x1B0` 取 definition，再从 definition `+0x1AC` 读选项数量；这里将其记为 definition，是实际 caller 与该源码布局的共同对应，不从函数名称猜测。

| 实际位置 | 可确认的直接行为 | 范围 |
| --- | --- | --- |
| `37BAA9D..37BAAAD` | 读 `[RBX+0x1AC]`；count 为 0、choice 大于等于 count、choice 为负，均跳到 `37BAB0E` | 选中项路径的索引范围检查；不等于完整选项合法性 |
| `37BAAB4..37BAAEE` | 条件分支中读取另一个全局表，满足范围时对 choice 对应的整型槽执行 `lock xadd` | 只记录读表及自增，不推导该表的业务名、资格或资源效果 |
| `37BAAF3..37BAB08` | 从 `[RBX+0x1A0]` 指针数组取 `choice` 项，对其 `+0x310` 地址调用 `3765860`，`RDX=R15` 原上下文 | 选中项的实际调用边 |
| `37BAC6A..37BAC79` | 单独读取 `[RBX+0x208]`；非空则同样调用 `3765860`，仍传原上下文 | 此路径在前述选中项范围检查的汇合点之后，不以选中项路径已执行为必要条件 |
| `37BAD16..37BAD3C` | 恢复寄存器并返回 | 两次 `3765860` 返回后均未对其返回值做成功／失败判断；Select caller 也没有消费该调用的成功值 |

这份完整 body 没有直接读取物化 option 的 enabled／shown，也没有把 `+0x310` 或 `+0x208` 命名为完整业务效果。条件是否在更下层判定、选项效果如何展开，仍需实际 callee；外层 validator 的单独范围见[借款事件 validator 原件](loan-event-native-validator-frontier-12004-20261026.md)。不能把某一层没读 enabled，外推成引擎不存在最终限制。

索引失败后仍可到达 `+0x208` 分支，是这个 callee 的静态控制流。现 bridge 自己检查当前实例和 option count，普通事件策略使用真实显示项绑定；本页不据此新增非法索引入口、守卫或假定一个生产可达故障。

## 已有 265 B 包装入口与下一条未闭边

实际 caller 两次调用的 `3765860..3765969` 已在旧共享 cache 中完整保留，本轮直接复用 **265 B**，没有重复采集：

`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-03765860-03765969.bin`，SHA `aee8d876e5d6e8c26817f83cf34a1a80f09e744481cbea1e3f0ac1bf2ecc0c82`。其 `.json`、`.claim` 与原 `guest-cost-native/function-map/normal_rule_effect-DETAIL.json` 保留原取证路径；旧采集机器未声明，记为 `machine_id: unknown`。旧记录的 `normal_rule_effect` 是来源标签，本页只使用真实原字节和直接调用边，不将标签当作语义证明，也不将旧缓存追认为本轮 held 文件。

265 B 全部可解码到 `3765968 RET`。入口保留两个原参数，调用 `37652B0`、`3736040`、`3735F90` 建立栈对象，将原上下文及一个全局 byte 写入栈上的结构，再以原 `RCX` 和该结构调用 **`3765E50`**。之后调用 **`373B5D0`** 并释放局部容器；没有把 `3765E50` 的返回值转换成对上层可消费的成功／失败分支。

因此本轮把“未知 `37BA990`”收窄为明确的两个对象路径及共享包装入口；新的核心边是 **`3765E50` 内部执行／条件语义与 `373B5D0` 后处理**。二者没有在本轮展开，不能据 wrapper 返回宣布脚本、金币、债务、关系或后继窗口效果已经完成。`1822C30` 栈上下文构造的拷贝／所有权、最终 manager ID 查找表与 SAVE/LOAD 生命周期继续未知。

## 对 Java 消费者的实际含义

原窗口退出 manager、进入选项处理、下游脚本调用和独立物质后态是不同事实。本轮结果不改变 [Java 事件结算合同](../java-event-action-outcome-continuation-20261026.md)：确认原窗口消费的 primitive 可以结算；物质结论仍需要独立原生后态，UNKNOWN 原动作不重投。实际 ordinary 后态测试候选和 Holding 归档消费者补丁另由 Host 编译、运行，此处静态源审不计为 Java 或游戏验收。

本轮新增取得的 941 B 只归入 b64 batch06 一次；265 B 属既有缓存复用。没有新的窗口采样、贷款支付、游戏日或性能结果。研究 plan 检查只验证结构与列出的原件身份，不自动验证上述人工指令解释。
