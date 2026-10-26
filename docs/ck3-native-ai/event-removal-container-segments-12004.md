# 事件容器移除：pdata 片段与完整执行路径

2026-10-26，`machine_id: xenoamess-full-tower-eb9d2c1186`。本条研究冻结的 CK3 **1.20.0.4**，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。不证明当前安装、加载或运行的版本。

已取得的 `0x29C6A70..0x29C6A9E` 共 46 字节是完整的 **pdata 记录**，却不是完整的逻辑函数。它调用另一个函数后仍有条件跳转和顺序续行，没有 `RET`。旧研究 76/77 中“完整 wrapper”的表述因此需要收窄；旧原件保留，本条与 correction84 追加更正。

后继 86 已消费实际取得的 205 字节，闭合尾槽清空、尾元素搬移、清理调用与 count 递减；最终释放函数、ID 回收及保存序列化仍未查明。以下先保留原始边界，再列新取得的路径。

## 已还原的生产与消费链

| 层次 | 已确认的来源、顺序和行为 | 仍未知 |
| --- | --- | --- |
| 当前事件选择 | `GetCurrentEvent 0x29C5780` 从已有指针数组尾部反向扫描，按角色和定义的原始 subtype 分支返回一个当前实例；没有评分循环 | 数组填充、实例 ID 分配、复用及保存恢复的生产者 |
| 桥接提交 | 重新读取玩家、完整实例 ID 和选项范围，再构造、复制并入队 | 入队 ACK 不提供执行后态 |
| 实际选择执行者 | 既有 477 字节 `0x29BDDE0..0x29BDFBD` 先查 ID、取指针，再调用 `0x1822C30` 捕获局部 context，随后运行辅助对象，最后分支调用选项执行者 | context 深拷贝、引用计数与定义的所有权；选项执行完整副作用 |
| 实际辅助执行者 | 既有 347 字节 `0x29BE0D0..0x29BE22B` 经 ID 查找获得索引，以计数器的 bit0/占用者排空协议进入容器修改，实际调用 `0x29C6A70` | 外层对象最终销毁、ID 映射删除或复用 |
| 本次 46 字节 | 读取容器基址和 count，形成当前槽与最后槽的两个地址，调用 `0x29C6C80`，再读 count 并跳转或续行 | callee 的实际内容、后续 count 写入、释放和返回 |
| Java 账本 | 真实动作材料另由唯一 writer/reducer 验证与持久化；原生当前选择变化与账本提交属于不同事实 | 本研究不提供实际动作、恢复或下一阶段业务资格 |

这些是玩家事件选择与引擎状态转换的已到达路径。原生 NPC 的事件决策候选、评分、调度和重算机制尚未由本链证明，不能把桥接调用原版入口称作已复刻原生 AI。

## 46 字节的确切边界

| 指令位置 | 静态确认 |
| --- | --- |
| `0x29C6A76` | 从容器 `+0xC` 读取 32 位 count，计算 `count - 1` 并符号扩展 |
| `0x29C6A7C..0x29C6A8A` | 从容器 `+0` 读取指针基址，令 `RCX = &slot[index]`、`RDX = &slot[count-1]`，步长 8 字节 |
| `0x29C6A8E` | 实际相对 `CALL 0x29C6C80` |
| `0x29C6A93..0x29C6A9E` | 重读 count，零值 `JE 0x29C6AE8`，否则加载基址并续行到 `0x29C6A9E` |

不能仅根据“两个槽地址”的形态把 callee 命名为 swap、删除或析构函数，也不能把局部元数据边界当成函数返回。现有 pdata 分为：

| 记录序号 | RVA 范围 | unwind RVA |
| --- | --- | --- |
| 143502 | `0x29C6A70..0x29C6A9E` | `0x510B454` |
| 143503 | `0x29C6A9E..0x29C6AE8` | `0x528EB24` |
| 143504 | `0x29C6AE8..0x29C6AEE` | `0x528EB38` |
| 143507 | `0x29C6C80..0x29C6CFD` | `0x5109E4C` |

完整选择执行者在调用辅助执行者后不再解引用先前的 Event 指针；它使用辅助调用前捕获的局部 context。这个顺序与“当前实例已变化”同时成立，也仍不足以证明旧对象的生命期已结束。局部 context 的真实持有机制需要独立定位。

## 对自动游玩的约束与下一步

队列接受、当前实例推进、实际选项效果、旧对象销毁和账本持久化应继续分开记录。当前实例 ID 变更只能证明 selector 的结果变更；它不能补足缺失的效果证明，也不能使 UNKNOWN 动作重新提交。这里没有策略修改或性能改善结论。

初稿的下一条静态取证请求仅包含已到达续行与 epilogue 的 80 字节，以及实际直接 callee 的 125 字节，共 205 字节、2 次读取。该范围已在后继 86 取得，不授权继续展开后续 callee、相邻构造函数、ID allocator、RTTI、全 EXE 扫描或游戏采样。

原始 46 字节沿用共享缓存：`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-029C6A70-029C6A9E.bin`，SHA-256 `b68748a3c604520cf3782b64843c8b620d5e09233704a5b7e5a2675bc3899935`。原始 acquisition 见 `D:/ck3-state/ck3-java-g2-r4-sourcebatch03/capture03/CAPTURE03.json`；当时读前后源文件身份一致，只证明该次取证。

本轮精确更正、研究记录、同源生成的 Mermaid 和取证请求保存在 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/ledger_writer/`：`EVENT-REMOVAL-SEGMENT-CORRECTION84.json`、`NATIVE-PLAN84.json`、`NATIVE-GRAPH84.md`、`NATIVE-SOURCE-REQUEST84.json`。`native_research_plan.py check` 的文件完整性与结构检查通过；`check --for-observation` 正确拒绝该 offline-only 方案，没有实时观测窗口或真实 producer trigger 的资格。没有新 EXE 读取、游戏动作或业务验收。

## 后继 86：实际移除路径与别名分支

`b64_execution` 的实际 batch02 于 `2026-10-25T22:08:31.092404+00:00` 记录取证成功。其三阶段实际 child 均退出 0，Job 活跃进程为 0，input/runtime 守卫均为 MATCH，input 为 CLOSED、未知读取为 0。本岗消费原输出，没有再次读取 EXE 或复制原始窗口。当前 held 文件为来源机器的 Steam 安装目录；它与原迁移缓存是不同文件身份，不能把旧 FileID 当成本轮 held FileID。绑定、请求、准入和实际 held 身份均以 `resume61/b64_execution/BATCH02-RESULT01.json` 为准，SHA-256 为 `4f117d56895dd986010e34f3691601bc882e218c34acbf4811513bf174ebf3bb`。

实际窗口：

| 原输出 | RVA / 长度 | SHA-256 |
| --- | --- | --- |
| `D:/ck3-state/ck3-java-g2-native-static-resume61/batch02/capture01/window-003.raw` | `0x29C6A9E..0x29C6AEE` / 80 B | `85a141ad3a61e8b457db0b9ce51d123dedb6a412d0a617f41a3c7d271cdae812` |
| 同目录 `window-004.raw` | `0x29C6C80..0x29C6CFD` / 125 B | `ac3a86e0264e3a089e7319091a2476e35886876ab479b6bc4784c55a959d810c` |

125 字节 callee 的完整已解码路径先将 `lastPtr = *lastSlot` 暂存在寄存器，然后清空 `*lastSlot`，再读取 `oldSelected = *selectedSlot`。当后者非空时，实际调用顺序是：

1. `0x856050(oldSelected + 0x188)`；
2. `0x856050(oldSelected + 0x168)`；
3. `0x87E0E0(oldSelected)`；
4. `0x4223F44(oldSelected, 0x1C8)`。

最后将寄存器中的 `lastPtr` 写回选中槽并返回。调用与参数已静态确认，尚未把这几个未展开函数的内部语义定名为最终析构或 allocator 释放。

wrapper 续段重新读取尾槽；若尾槽仍非空，它执行同样的四次调用，随后重读 count，在容器 `+0xC` 写入 `count - 1`，恢复寄存器并 `RET`。原 count 为 0 的分支直接进入 epilogue，不执行递减；这不证明任意越界索引或空容器调用合法。

| 真实地址关系 | 指针与清理顺序 |
| --- | --- |
| 选中槽与尾槽不同 | callee 清尾槽，对非空旧选中指针执行清理调用，再将尾元素搬到选中槽；wrapper 看到空尾槽，只递减 count |
| 选中槽就是尾槽 | callee 清空后从同一槽读到 null，跳过自身清理，再把寄存器中的原指针还原该槽；wrapper 对这个尾指针执行清理调用一次，再递减 count |

这条正常非空、合法索引路径是“移除选中槽，用尾元素填补空位”，不应再泛称为 swap。它证明 manager 槽级移除和实际清理调用，仍不证明 ID 查找表删除、ID 永久退休、释放后能否复用或 SAVE/LOAD 身份合同；也不能代替真正的选项执行者及独立物质后态。

后继静态记录为 `EVENT-MANAGER-REMOVAL-ACTUAL86.json`（4834 B，SHA-256 `ea489414ce03fa63f87470a78481e60c60a6c53f00511978a441b4af775a8df6`），同源计划与图为 `NATIVE-PLAN86.json`、`NATIVE-GRAPH86.md`。结构与四份精确证据文件检查通过；无新的游戏观察、效果资格、UNKNOWN 重投或性能结论。

## 后继 90：复用已有缓存，闭合到 HeapFree 调用

本岗重新读取并核对了已有的四段缓存，共 88 字节，没有新增 EXE 读取或复制原始窗口。`0x4223F44` 的真实 5 字节为 `e9e785ecff`，相对跳转到 `0x40EC530`；其后直接复用[已闭合的 actual4 原始缓冲区释放链](native71-army-assault-group-release-12004.md)：5 字节跳转到 `0x423543C`，17 字节 wrapper 跳转到 `0x424E364..0x424E3A1` 的 61 字节终端。四段实际长度、字节、来源 claim 与既有解码全部相符，后三段 SHA 也与原记录一致。历史取证原件未记录机器 ID，按 `machine_id: unknown` 保留；这里只复用同 EXE SHA 的静态代码知识，不追认当前运行环境。

终端把传入的旧指针从 `RCX` 移到 `R8`，将 `EDX` 清零，从 `0x5C5DE30` 加载 heap handle 到 `RCX`，再调用 `0x43DA748` 的导入项。既有 actual4 导入解析将其绑定为 `KERNEL32.dll!HeapFree`。因此前级传入的 `0x1C8` 并不是该 HeapFree 调用的 flags 或大小；实际 flags 为 0，raw buffer 是原指针。这个结论来自静态指令与既有导入来源，没有读取运行时 heap handle 或 IAT。

HeapFree 成功和失败路径都能正常返回；失败路径另取错误并写 CRT errno。manager wrapper 不检查其返回值，正常返回后仍继续槽位和 count 后缀。所以现在可以确认源码到达了原指针的堆释放请求，仍不能根据“正常返回”断言该次释放成功。此前两个子对象清理函数、ID map、ID 复用、context 所有权、SAVE/LOAD 与实际选项效果仍保留原边界。

精确复用记录为同一 `resume61/ledger_writer/` 下的 `EVENT-CLEANUP-HEAP-BOUNDARY90.json`，8051 B，SHA-256 `ec9d91cde2299322d5d06b466c91257230f4cd7dbeb27c4dd7d6f4a1674f4d2d`。待取证请求 88/89 已由这次缓存复用解决，不再补采 48 字节或邻接代码；没有实机执行、业务天数或 UNKNOWN 重投资格。

## 后继 94：第三次清理的真实 header 写入

继续复用已有 `new-0087E0E0-0087E15E.bin` 的 126 字节，SHA-256 `878033e650050b820387c6748a75d38d89750ebe8bfd7c88053b70189e8bd43a`。实际字节与 Army 和 religion 两份既有 actual4 解码逐条相符，共 35 条指令，claim 范围一致；没有新 EXE 读取。历史记录仍缺机器 ID，不外推当前环境。

`0x87E0E0` 先以 `base+0x118` 调用 `0x889700`。当 `QWORD[base+0x100]` 非零时，以 `base+0x100` 调用 `0x889780`，返回后重新加载 `RCX=[base+0x110]`、`RDX=[base+0x100]`、`R8D=8` 并调用 receiver 的 `vtable+0x10`；正常返回后清 `QWORD[base+0x100]` 和 `DWORD[base+0x108]`。不能假定直接 callee 没有改变这些被重读字段。

另一非空分支取 `RDX=[base+0x18]`、`RCX=[base+0x28]`、`R8D=8`，先写 `DWORD[base+0x24]=0`，再执行 `vtable+0x10`，正常返回后清 `QWORD[base+0x18]` 与 `DWORD[base+0x20]`。空分支跳过对应调用与清理。因而这里已确认 header 写入和精确的前后顺序，不能把历史取证清单里的“read-only bound callback”标签当作本 caller 没有写入的证据。

两个直接 callee 和动态回调目标仍未展开；没有据这些写入授予复制所有权、回调成功、IDmap、ID 复用或 SAVE 生命周期。正式记录 `EVENT-SCOPE-CLEANUP94.json` 为 11344 B，SHA-256 `f3a8d9a3c1e299f484e01b5eb6aa11b92048c5b39a42e95eb92db180486cf1d0`。与后继 90 一样，它是静态调用边界，没有实机事件执行或效果资格。


## 补充 95：两个成员的原生字符串清理

在相同 EXE SHA 的既有 Core 缓存中找到 `0x856050..0x8560AE` 的完整 94 字节：`function-match-core/new-00856050-008560AE.bin`，SHA-256 `843bdfaa61cdacef620b1edffed48e2023fa0fc922e95a29a8c3c77fbe86be4e`。实际原件与既有 law migration Detail 的全部 26 条指令逐字节一致，两个直接 call 的相对目标也重新计算一致；这次没有新增 EXE 读取。历史原采集机器仍为 `machine_id: unknown`，本轮只复用同版本静态知识。

该函数读取 `member+0x18` 的 capacity。无符号 capacity 小于 16 时跳过释放分支；否则从成员首字段取指针，传递的大小先为 `capacity+1`。该大小达到 `0x1000` 时，再取 `[pointer-8]` 作为原分配基址、大小加 `0x27`；无符号 `(pointer-base-8)>0x1F` 时转入 `0x4232A70` 后接 `INT3`，本段没有证明这条分支正常返回。普通释放分支调用 `0x4223F44`，正是补充 90 已核到 HeapFree 请求的原路径。

正常续行随后写 `QWORD[member+0x10]=0`、`QWORD[member+0x18]=15`、`member[0]=0` 并返回。manager 在补充 86 中实际分别以 `oldSelected+0x188`、`oldSelected+0x168` 调用这同一函数，因此两个成员的清理与置空已经接回实际 Event 移除链；尚未据此给它们指定业务名称。底层释放失败仍可返回，调用者没有检查返回值，所以这些字段已空也不能证明其堆分配实际释放成功，更不能证明最终选项效果、ID-map 或 SAVE 生命周期。

精确复用记录为 `resume61/ledger_writer/EVENT-MEMBER-CLEANUP95.json`，8073 B，SHA-256 `290a32de05a9778d169bcc20159d9f3ae3777b7b61128c5f08b6a91a53f0ac75`。`0x4232A70` 内部与具体运行时分支仍未展开；本轮没有运行游戏、构建或赋予 UNKNOWN 重投资格。

## 补充 97：scope 清理的两个直接调用

补充 94 的两条直接调用已用既有 prisoner 映射原件接回：`0x889700..0x889776` 的 118 B、SHA-256 `0f1a84cdd95dd6db78e7a49d4fc754164bb8340f4374073dc71f7531d63c0db8`，以及 `0x889780..0x8897DD` 的 93 B、SHA-256 `7156a7e95cb379797e67d986f4cdbe2936ee932f6dca093cdad0669de1994d10`。实际 raw 与原 Detail 的 33/29 条指令、claim 范围及相对分支目标一致，manifest 明确绑定同一 actual4 EXE SHA。没有新增 EXE 读取；历史原采集机器仍未核实。

`0x889700` 的实参是 `oldSelected+0x118`。第一个非空分支在 `argument+0x30`（即 `oldSelected+0x148`）调用 `0x889780`；回来重新取 `[argument+0x40]` 为 receiver、`[argument+0x30]` 为 backing，以 `R8D=8` 调用 receiver 的 `vtable+0x10`，正常续行后清 pointer 与 `argument+0x38` 的 DWORD。第二个非空分支在 `argument+0x10`（即 `oldSelected+0x128`）调用尚未展开的 `0x889660`，再重新取 receiver/backing、调用 `vtable+0x10`，正常返回后清 pointer 与 `argument+0x18` 的 DWORD。两个空分支跳过各自调用和清字段；不得假定中间 callee 没有改写随后重载的字段。

93 B 的 `0x889780` 声明窗口跨 runtime fragments，不能据此称完整逻辑函数。入口读取 header `+0xC` 的有符号 count；非正数出口仍写该 count 为 0。正数分支把原 count 和 backing 分别留在寄存器，每行以 `RCX=row`、`EDX=0` 调用该行 `vtable+0`，按 `0x48` 步长推进，递减保留 count；它没有逐行重读 header count。循环正常返回后同样清原 header 的 count。manager 也实际用 `oldSelected+0x100` 调用它，因此该有符号分支与 count 重置可接回这条调用边，但没有任何具体运行时 count 或回调目标观察。

精确记录 `EVENT-SCOPE-CALLEES97.json` 为 16992 B，SHA-256 `32ed2175bf5fb415e619b6b6712c1ba96b5d3109f7de408ced4ea8900b91d28a`。动态行回调、allocator slot、`0x889660` 及其后态仍未知；此处的条件清理和 header 写入不能授予成功释放、实例 ID 延续或 SAVE 身份。

## 补充 102：第二组行的真实有限窗口

唯一读取器 b64 的实际 batch07 已返回 `0x889660..0x8896BD` 的 93 B，原件 `D:/ck3-state/ck3-java-g2-native-static-resume61/batch07/capture01/window-020.raw`，SHA-256 `56aaf173ebfa9caaf44aac682ba2704609be627d9eb02b9ccf701f6ef666de58`。采集机器为 `xenoamess-full-tower-eb9d2c1186`，时间 `2026-10-26T00:06:56.748306+00:00`；结果记录为 `BATCH07-RESULT01.json`，19267 B / `beb69b6948738f9cfb395d3c06cf3dcafe3b6711af0931a99849cad06809c8a9`，三 phase 退出 0、输入/运行时核对 MATCH、input CLOSED、未知读取结果 0。这里只解码该原件，没有另开 EXE reader。

29 条指令完全覆盖这个 20+55+18 B 的三段 runtime region，仍不把它默认称完整逻辑函数。实参 header 来自补充 97 的 `oldSelected+0x128`：读取 header `+0xC` 的有符号 count，非正数出口也会把 count 清零；正数分支保存原 count/backing，每行设置 `RCX=row`、`EDX=0`，调用该行 `vtable+0`，按 `0x20` 步长前进，最后清原 header count 并返回。它与 `0x889780` 的 `0x48` 行步长明确不同，不能由共享的虚表入口给两组行赋予相同业务类型。

补充 97 中未展开的这一直接函数边已接上；具体行/allocator 回调、运行时分支、释放结果、ID-map 与 SAVE 身份仍未证明。正式记录 `EVENT-SECOND-VECTOR-ACTUAL102.json` 为 8908 B，SHA-256 `e99d443a94429e63e2829e14e6587681c99b4a75e23535288c9aeb1981c817a4`。没有自动跟进任何动态 destructor/allocator 或邻接字节，也没有新游戏日或选项效果资格。
