# 1.20.0.4 事件选择：嵌套命令、选项处理与后态的先后

本页记录已封 Select 全函数的指令顺序：`29BDDE0` 在调用选项处理入口前，先对同一实例分派另一条命令。容器的权威研究与取证已归并到本轮 ledger_writer 的[实际移除路径 86](event-removal-container-segments-12004.md#后继-86实际移除路径与别名分支)，本页只消费其正式结果，不另采同一 helper。不能把这个中间步骤、队列接受、窗口变化或最终物质效果合并为同一个完成点。

静态复核时间为 2026-10-25 UTC（北京时间 10 月 26 日），执行机器 `machine_id: xenoamess-full-tower-eb9d2c1186`，身份沿用本轮 Root 的 `tools/ck3_live_run_id.py machine` 读回。旧 Oct7 字节采集记录未声明机器 ID，其采集机器记为 `unknown`；本次只读回原件，不追认旧现场属于本机。目标固定 CK3 **1.20.0.4 / build 25734779**，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，取自已有迁移原件绑定，没有重新读取或哈希 EXE。

原入口是[既有默认 Events 迁移](default-events-mcp-migration-12004.md)。六份原始文件及一份后继 86 正式记录的哈希、生产/调用/消费链、未闭边与零样本解释保存在[研究 plan](research/event-select-poststate-order-12004-20261026.plan.json)；[同源生成图](research/event-select-poststate-order-12004-20261026.graph.md)不手改。`native_research_plan.py check` 的结构与文件身份检查不证明语义或实机结果。

## 已能确定的调用顺序

| 阶段 | 精确入口与实际操作 | 能证明的范围 |
| --- | --- | --- |
| 我方 bridge | `SubmitSelectEventOption` 重新读取当前玩家事件，检查索引范围，构造实例 ID/索引，提交 channel 7 | `submitted` 就是 `submit_command` 的布尔返回；此叶不读取选择后的窗口或资源 |
| 原生外层执行 | `29BDDFE` 从 secondary command `+8` 取实例 ID；`29BDE56` 调 `29C5640` 取索引；负索引或空对象走退出分支 | 执行时重新解析，未复用提交时的事件裸指针；实际排队时延仍未知 |
| 栈上上下文 | `29BDE8B` 以当前事件指针为参数调用 `1822C30`；随后从 Event `+1BC` 取完整 ID，写入另一条栈上命令 | 只能说构造了供后续调用使用的栈对象；没有证明其深拷贝、引用计数或所有权细节 |
| 嵌套分派 | `29BDEC8 -> 2967680`；secondary vptr `4773478` 的 `+8` 指向 `29BE0D0` | 这是另一条命令的执行路由，不是可忽略的 UI 文本读取 |
| 嵌套执行 | `29BE0FC` 再按同一实例 ID 查索引；读取 EventDef `+250` 分支，可能调用 interface vtable `+A0`；随后 `29BE208 -> 29C6A70`，实参为 `GameData+36398` 容器和索引 | 后继 86 已确认合法非空索引路径的槽级移除、尾元素填补、清理调用及 count 递减；类别 1/2 业务名、GUI 通知含义与最终释放尚未确认 |
| 最后选项入口 | 嵌套分派返回后才有 `29BDED5` 的索引符号分支；非负时最终 `29BDF68 -> 37BA990`，参数含原选项索引和栈上下文 | 调用先后已确定；`37BA990` 的完整语义、脚本效果、后继事件与最终后态仍未知 |

通用 `2967680` 的旧完整 249 B 源已由[原 R08 阶段研究](evidence/episode04-r08-task-construction-20261021/phase-a04/FINDINGS.md)解释为 `+10 → +20 分支 → +8（直接或经 29677C0）→ +18`。此处重用的是同一 exact-build 字节，不把 DailyTick 的业务语义移植到事件上。嵌套表 `+20=855AA0` 的已留 16 B 叶为 `mov al,1; ret`，所以该对象走带包装的 `29677C0` 分支；不据此宣称异步、阻塞或具体线程切换。这一补充叶原件是 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-00855AA0-00855AB0.bin`，本次实际 16 B / SHA `28cf35ca20ab81145888939f458aa7ea20071702d666a8c9049eef19ce7dccc3`，未据此增加新的完成边。

外层还有一个内部负索引分支：嵌套分派已调用，而 `37BA990` 可被跳过。我方现行 bridge 拒绝负索引，故该分支不构成新增操作方式。它说明这两个调用本来就是两个不同阶段，不能凭其中一个阶段出现就推导另一个阶段已完成。

## 剩余的具体缺口

原 `29C6A70` cache 的 **46 B** 前缀不足以证明完整逻辑。ledger_writer 后继 86 已消费唯一 native reader 本轮实际取得的 **205 B / 2 次读取**：续行与 epilogue 80 B、直接 callee 125 B。它闭合了正常非空、合法索引路径的槽级移除：清尾槽、对非空旧选中对象执行四次清理调用、把尾指针填入选中槽，wrapper 最后把 count 减一。选中槽等于尾槽时，callee 跳过清理，wrapper 清理一次；不是把两个对象简单交换。本页没有重新读取 EXE，也不把最终 allocator 释放或 ID 退休归入已证范围。

正式结果原件是 `resume61/ledger_writer/EVENT-MANAGER-REMOVAL-ACTUAL86.json`（4834 B / SHA `ea489414ce03fa63f87470a78481e60c60a6c53f00511978a441b4af775a8df6`），其 held 身份、原始窗口和实际 child 回执以该记录及 [86 专题](event-removal-container-segments-12004.md)为准。本岗重复的 helper 请求已撤销。将该结果接回已封 Select 指令顺序，可以静态确认：**manager 槽级移除与清理调用先返回，外层随后才调用 `37BA990` 处理非负选项**。因此旧实例从 manager 消失可发生在最终选项处理之前，不能单凭“窗口已消失”证明物质效果完成。栈上下文在移除前由 `1822C30` 构造，但其深拷贝、所有权与被移除对象生命周期仍未闭合，不据此推导安全持有或悬空指针。

`37BA990` 的完整体、脚本效果及后继事件发布仍未知；槽级移除也未闭合 ID 查找表更新、ID 复用、后继显示顺序和 SAVE/LOAD 合同。这里的调用顺序与 [Java 动作结算合同](../java-event-action-outcome-continuation-20261026.md)一致：事件 primitive 的 APPLIED 可证明原窗口消费；需要物质结论时仍须独立原生后态，UNKNOWN 不能重投。本轮普通事件调度回归候选正验证真实 writer 的 retain → fresh SEM → settle → 下一 ordinary step；源码候选不计为已编译、JUnit 或实机通过。

当前 M2 / OutcomeArchive 继续按实际 producer 保存失败读取原件、可选 observed-after 与依赖 JSON。这里的失败读证据是 **DATA**；它既不是窗口选择结果，也不授当前 occurrence、下一动作资格或物质效果。没有 after 的 opaque 失败保留为空，不能靠本研究推造 after。相关真实 I/O 失败与 opaque-after 回归归 M2；Host 为唯一整合与编译者。

本岗没有执行原生命令、SDK、游戏、构建或测试 JVM，没有采到新的窗口消失、物质效果或游戏日；205 B 取证属于原唯一 native reader，未在本岗重复计数。更新后四条静态边与三条 unknown 边只覆盖本专题，不代表 M2 或八个 M 实机验收完成。
