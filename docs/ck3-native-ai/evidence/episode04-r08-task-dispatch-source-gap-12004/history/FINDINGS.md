# R08 task+68：上游选择／构造的来源停止点

本轮没有找到已持有的构造或 enqueue 指令。机器 `desktop-3fevhd2-1c74096080`，来源树 `ba3528fc04621529ed528930623b5d34826a46a4`；只有旧1.20.0.4原始来源与当前字段合同复核，0SDK／游戏／GUI／EXE新读／构建／主树和D盘写入，0旧测试重跑。

已闭合的是执行侧：`3F90A6F` 对 `*(job+38)` 的 vtable+10 做虚调用；`290DC00` 已在消费 task 的 count、chunk 和 `*(task+68)` descriptor。`290FD20` 从已选数组按实际 index 取 Character，再 tail-jump 至 `28F7840`。这些 body 不含 task+68 的构造 store，也不说明数组是在何处、按哪条日期规则选出的。job+68 在另一个 job wrapper 中是耗时输出，绝不能与这个 task+68 descriptor 按 offset 同名。

旧实测栈还保留 return `3F921CF / 3F90B4A / 3FBCF01 / 3FBD0DA / 4244F90`；其中第一项的函数元数据候选 PC 是 `3F921CE`。它们是可引用的真实旧 unwind 候选，当前没有完整 body 或直接 caller/constructor/xref 证明。不能把下一层 worker 调用自动改名为日/月调度，也不建议只为继续追栈再读它们。

最小有用的新来源是**实际 task 实例到其构造／enqueue producer 的连接**。现成 current-cash/payment query 没有 task、descriptor、index、vptr 或选择谓词字段，重复 query 不会补出这条边。已有 `28F7840` parent-entry 方案尚未实现；若后续获准开发，可在真实 source chain 内保存原 RCX/RDX/R8D、raw return、同过程/线程/日期/clock/token，并有限读取候选 `task=RCX-70` 的 descriptor、count/chunk、vptr/slot与唯一实际 array[index]，验证它确实选中同一 RDX Character。

这首先只产生可定位的 task/descriptor/vptr 锚点；仍须找到**同一实例**的构造赋值或 enqueue 生产 PC 与 calendar 输入，才有资格展开那个有限来源。当前该 PC 为 NOTHELD。事后才安装的 task+68 write-watch不能追回过去的构造写入；不能假定 worker stack 包含 producer，也不扫描邻近函数或全 image。

因此本轮交付准确停止点，不新增 hook/query/测试框架。parent invocation 内一次 settlement 不等于每日或每月一次；没有钱包记录也不能证明未执行 settlement。c/d业务名、实际军事付款／payer和cadence继续 unknown。

精确原件的仓库相对路径、SHA、实际旧栈候选与未实现观测合同见 [TASK-SELECTION.contract.json](TASK-SELECTION.contract.json)。这是可移机知识；旧机器的安装、进程、绝对指针或现场资格不能随它迁移。
