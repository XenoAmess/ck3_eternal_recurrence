# CK3 1.20.0.4：R0178 两个真实缓存 writer 与完整赋值函数

R0178 首次实际观察到 played Character secondary context 的 `+2C0/+2C8` 写入，并完整取得唯一包含函数 `28A63E0..28A6697`。该函数把同对象的 `+18/+20` 直接复制到这两个字段；这闭合两个 raw store 及其直接输入来源，**没有闭合 getter 语义、军事已付维护费、调用者或结算周期**，`maintenance_attribution=unclosed`。它推进了 [R08 getter/cache 研究](war-payment-maintenance-cache-source-12004.md) 与 [真实 R0174 settlement 父链](war-payment-r0174-actual-parent-source-12004.md)，历史 unknown 回执保持原样。

机器 `desktop-3fevhd2-1c74096080`；精确游戏 1.20.0.4 / Steam25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。R0178 使用 source `b42afbbd85df3802b1fa6222f7aac403c2adf735`、PID24740/create134365733009843924/gen1、actor31254、window1/epoch1、episode `native-31254-0665741d68fc`。实际时间和原始 pins 见 [FACTS](acceptance/2026-10-16-r0178-maintenance-writers/FACTS.actual.json)。本机 PID/地址/epoch/观察资格不得迁移为另一机器的入场凭证。

## 真实窗口及恢复

Root 从独立配对的暂停态 current cash query 获得稳定、完整的 `current_raw_context_v1`，context 两读均为2296003269728，raw 为 `[384653,0,273262,0]`。保留原 day0 证据，writer 入场实际使用新 `date53146896` 配对包。原逐日 runner 在 validated one-day Arm 与 fresh before-resume snapshot 后，执行一次有限 writer attach，实际 ready110线程后才提交原 single Resume。下一暂停帧为53146920；没有第二 Arm/Resume 或热替 DLL。

真实 raw 共224行：start1、成功arm110、已退出thread1、physical write trap2、restore109、terminal1。两次 trap 均来自线程17340，分别写 `context+2C0` 与 `context+2C8`，raw 仍为384653和0，是**真实同值写入**。窗口达到30秒 timeout，native返回1；actual reader返回0，restored/detached/cleanup_complete/cleanup_proved均true，pending_event=false。独立核对109份原 debug 向量 readback与唯一退出TID10908，未把退出线程当作未恢复 live thread。

两个 paused query 的四字段值完全相同，只说明两个样本的净差为0。`+28/+30` 未保留 trap，不证明无 writer 或无费用。窗口 `full_window_all_writes_covered=false`；trap 本身没有实际 game date/trigger phase。原始 calendar 来源的下一 day0/month0 是条件推导，不能单凭跨月窗口给 trap 命名为月结事件。before/after辅助报告未传完整 Strength packet，calendar 栏继续 unknown，没有回填。

## 已证指令及唯一完整函数

最初授权只读两 post-PC 前32/后16字节窗口的并集：59B、1 read、0 EXE metadata。完整 MOV 恰好结束于真实 post-PC，且实际寄存器/有效地址一致，确定 store 起点；没有用 `RIP_after-1` 冒充指令起点。随后独立计划以已证起点 `28A6454` 查 `.pdata`：唯一 unchained extent为 `28A63E0..28A6697`，695B完整 code、220B metadata、20 reads，147条指令完整解码。两轮均复用既有 exact4 frozen image 身份和 PE mapping，没有整EXE哈希、xref/邻域扫描、callee读取、SDK或游戏操作。

| 位置 | 完整函数中的实际指令 | 可证关系 |
| --- | --- | --- |
| 28A640D | `MOV R9,[RCX+1C0]` | entry RCX 的 secondary context 指针，经解引用 |
| 28A6450→28A6454 | `MOV RAX,[R9+18]`；`MOV [R9+2C0],RAX` | 原始 +18 复制到 raw term a；实际 store post-PC28A645B |
| 28A645B→28A645F | `MOV RAX,[R9+20]`；`MOV [R9+2C8],RAX` | 原始 +20 复制到 raw term b；实际 store post-PC28A6466 |

入口先对 `+88/+8C` 的 dword 值作条件转存到 `+3D8/+3DC` 并置-1；两个分支都汇合到28A6450。两个 raw copy 位于首次 call 之前，没有根据费用正负跳过它们的分支，因此本轮两个实际 store 的直接值来源是进入函数前已经存在的 `+18/+20`，不是在此块调用财务 getter 后新算出的值。

第一次 direct call 在复制之后的 `28A6535→28D6170`，传 context+368 及保存 Character 指针的局部对象。其余具名 direct call 为29591E0、2468AC0、25FB1D0，均没有在本轮展开；没有直接 call 既有 settlement28A6D10、personal ADD285EE40或已绑定五个财务 getter 的边。后部还有 indirect calls 与经 entry RDX 派生的 indexed output，不能据完整函数已有 fixed-offset store 清单断言所有 alias/传递副作用都不存在。

已证 [R0174 settlement](war-payment-r0174-actual-parent-source-12004.md) 读取 `2C0/2C8/28/30` 并形成 signed64 `a-b-(c+d)`，正值路径进入个人 ADD。该消费 source 与本次两个生产 store 在字段层衔接；本次没有捕获 writer 调用栈，不能将本 store 的调用者接到 R0174 的父链，也不能把另一 session 的数值搬过来建立一次交易。

## 智能体 decision 消费说明

| 输入/等级 | Agent 可使用的事实 | 业务决策边界 |
| --- | --- | --- |
| paused `current_raw_context_v1` | 当前 actor/frame 的四个 raw 读回与身份/完整性状态 | 不是 callback 或 payer wallet 扣款 |
| actual writer projection | 本次入场身份绑定下，真实 field address、线程、post-PC、same-value write、有限终态与恢复事实 | 不把 timeout/no trap/净差0当作零费用；不把 admission date当trap日期 |
| 本次完整函数 source | `context+18→2C0`、`context+20→2C8` 的无条件直接复制，以及 raw consumer 的后续字段关系 | +18/+20 的业务名称、刷新/失效、caller/date cadence仍unknown |
| military paid decision | 本轮没有新的可用金额分量 | 费用率getter可按既有独立估计合同使用，不能写成实际已付维护费；generic ADD或缓存不能进入qualified military claim |

Agent 应继续保留 `known_producer=false` 的生产输出和 `maintenance_attribution=unclosed`，可另记 source 层的两个 raw store 已知。两种状态并不冲突：字段写指令已定位，但业务生产者及已付军费语义未闭。不要改现有 DTO、将字段改名为军费、回填旧seq12、对四项求和当作军事总支出，或把两种替代维护费率相加。

下一最小现场若需继续追直接值生产者，应由 Root 新建独立 fresh current window，重新读当前 Character/context，再显式选择 `+18/+20` 的只读 data-write 观察合同；旧地址和本次观察资格不复用。源码下一步需真实 caller或实际新writer PC，再给具名有限计划；本轮不追加广扫或未经授权的新字段观察。

## 原件与普通 clone 复用

[原件archive](acceptance/2026-10-16-r0178-maintenance-writers/originals.zip) 保留本次 original raw、实际 reader/cleanup/beforeafter、两个有限 source scope 的计划/回执/hex/bin/asm和独立分析。精确成员字节/SHA及原件性质见 [索引](acceptance/2026-10-16-r0178-maintenance-writers/ARCHIVE-INDEX.json)。archive 内带 C盘历史 argv 的 source executor 只供阅读，不能直接作为别机命令；读取新EXE或接游戏需要新计划与资格。没有复制 EXE/DLL、媒体、SYSTEM大回包或全游戏镜像。

普通 clone 运行如下 stdlib verifier，无 CK3、SDK、capstone或本机C盘依赖：

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-r0178-maintenance-writers/verify_repository.py
```

它核对新文件/所有archive成员、source原始695B与固定指令、实际两trap和原DR恢复事实；只重放保留字节和已声明事实，不重新执行 actual admission/观察，不证明人工签核、任意机器运行或军事语义。历史完整 cash/before 大包仍由当次 Root run保存，archive保留其精确pins及实际consumer输出；本 verifier没有伪造重放这些未内嵌的大包。
