# CK3 1.20.0.4：经济 NET、负支分配函数与军事 applied component 边界

首版是离线可行性和最小施工合同，没有 C++ patch、hook 安装、SDK、游戏、桌面、新构建或 EXE 执行。当前 source b42 冻结，R179 继续原对照场。建议 a09 先保留现有经济 NET 对账 partial；**本轮不盲加“军事维护费”字段**。完整 source 已闭合两个 raw copy 和负 NET 的整数分配函数，但尚无 `context+28/+30` 的业务来源，增加一个 entry/return 观察叶不会自行补出军事语义。

## 现有记录已足够完成的实际工作

个人 ADD 的 `kind2/caller28A6D7C` 已保存实际 wrapper/Character、amount、整原函数 entry/return 余额、共享 event clock/thread/session，以及 optional generic raw 四项 before/after、signed wrap 算式匹配和 parent trace。仅在实际 own-account、完整 callback、配对当前 session、无丢失/覆盖及 formula match 后，可输出“这笔实际个人钱包净入账与已观测四项算式一致”。它不是整个经济 settlement 的 entry/return，更不是军事支出流水。

正 generic callback 的实际 amount 可以独立核对；本专题只保存源码研究，没有新增对 R178 day32 原 packet 的重放信用。该净额不能改名为军费。既有 `generic_wallet_context_v1` 只在这一 kind/caller 上出现，personal SUB kind3 虽已有实际 amount 和 wallet before/after，却没有该 generic raw 扩展。

## 完整574B给出的分支

定义 a=`context+2C0`、b=`+2C8`、c=`+28`、d=`+30`；均为 signed64 raw。`context=*(Character+1C0)`，所有源码加减/NEG按64位环绕。令 T=wrap(c+d)，N=wrap(a-b-T)。

| source 分支 | 实际行为 | observer 当前缺口 |
| --- | --- | --- |
| N>0 且 personal wrapper存在 | 一次 ADD(N)，return28A6D7C | 已有 generic 记录可复核这笔实际净入账；未观察整个 settlement入口/返回 |
| N<=0 且 T!=0 | x=wrap(-N)；F(x,c,T)返回r1，非零时 SUB(r1)/return28A6E05；F(x,d,T)返回r2，非零时 SUB(r2)/return28A6EC2 | 两个 kind3 wallet 记录可保留，但没有 unique settlement parent event关联；c/d业务未知 |
| N<=0 且 T==0 | 不调用F，不执行这些wallet SUB | 缺 wallet 记录不能单独证明走了此分支或费用为零 |
| N==0 且 T!=0 | 仍进入分配支，正常输入下两个F为0，跳过SUB | 需要实际 settlement entry/return才可声明此轮零净变动；仅空journal不够 |

正 N 路径不调用 F。因此在负支加 allocator 观察，也不能关闭 R178 正 ADD 的军事分量。574B 未直接调用当前五个 income/expenses/maintenance getter；695B复制函数只闭合 `+18→2C0`、`+20→2C8`，不生产 c/d。

## 新闭合的唯一 callee

Root 单独授权的 `.pdata` 读取得到 `28A6B50..28A6D03`，435B/116条指令、220Bmetadata/20reads，unchained，完整入口解码。ABI source 为 `(RCX=output*, RDX=x, R8=y, R9=T)`，将一个qword写到output并返回同一output指针。没有 CALL、外部 tail jump、游戏对象字段读取、getter 或军事类别来源；唯一 direct JMP 是内部28A6C00。

正常安全分支的精确两阶段算式是：

```text
q = trunc_toward_zero(x*y / 100000)
result = trunc_toward_zero(q*100000 / T)
```

第一阶段直接乘法仅在 x/y 各处于[-3037000499,3037000499]时采用。其他输入通过 quotient/remainder拆分来计算中间q。第二阶段仅当q处于[-92233720368547,92233720368547]时直接放大；大q还按机器 abs(T)与10000000000分支，分别用缩放分母或quotient/remainder计算。不能全域改写为一次 `x*y/T`，不能宣称饱和或 `0<=result<=y` 的无条件边界。

T==0时source写入 `0x00000000FFFFFFFF`，即4294967295，不是signed -1；已知574B调用方先在T==0退出，故不会经此已知调用路径到达该分母零分支。未新增额外异常或修正规则。

例如正常域 x=1、c=d=50000、T=100000，两个内层q都为0，两个结果都为0，其和不等于deficit1。x=200000、y=T=100000时结果200000，也说明函数本身不把结果clamp到component100000。这里是源码算式示例，**不是新native测试或游戏观测**；真实 applied 标量仍以捕获的实际wallet参数及余额变化为准。

## 若继续施工，最小范围是什么

优先方案0：零新增detour。使用现有kind2 generic ADD和完整账户/clock/session绑定做经济 NET 对账partial；增加文档/离线projection即可，不变更生产military资格。当前 source 信息不足以批准“军事已付”产物，因此 a09 不应仅为补标签增加 hook。

如果 Root 明确需要完整同一次经济 settlement 观察，最小方案1是扩展现有 payment observer 的**一个专用 source entry/return叶**：entry28A6D10，已证16B完整非RIP-relative前缀 `41574883ec40488b81c00100004c8bf9`；source给出Character为RCX，但raw return ABI尚须沿用现有原函数once/return-bit保留方式作窄native fixture。没有新顶层query、新getter、通用执行框架或新游戏动作。

复用原 journal、sampling permit、共享event clock/session、actor读取和原函数once边界。一个 TLS parent entry token只标记当前真实结算 invocation；在最终 return发布其完整 entry/return记录，wallet子记录保留该token。这样可用 entry<child.entry<child.return<parent.return、同clock/线程/actor/完整session、实际无丢失条件连接 ADD或两笔SUB。entry raw读取标记为“original前采样”，不能把它改写为源指令寄存器快照。record publication不得事后改写已发布子记录；可以新增一个被consumer显式识别的 settlement kind，或明确可版本化的独立小parent-return集合，不能静默把kind2形状改成另一种业务。

最小未来字段为 actual source entry/caller、Character/fullID/context、raw四项entry/return、shared entry/return event、session两端、actual wallet balance两端、original called/returned、raw returnbits、TLS depth/采样不完整诊断；子记录只需parent entry event和固定source role：NET_ADD、RAW_C_SHARE_SUB、RAW_D_SHARE_SUB。角色名保持raw，不叫military。raw snapshot已有helper可复用，默认不开，源/anchor只授精确.4；编译flag必须传播到真实cash/runtime TU，不能重犯a07宏缺传。

需要改动的独占范围是 payment passive DTO/helper、runtime第六source slot、JSON、Python payment consumer以及窄fixture，必要时CMake选项传播；不碰army/refill GUI leaf。现有5个hook默认行为、boarding资格及legacy未扩展记录保持兼容。与refill owner已直联，无war_payment文件冲突。此处是施工合同，未生成这一native候选，也未声明可直接用于CK3。

仅在Root批准实现后做必要的3类窄验证：positive ADD和negative两SUB均有同次parent；零NET或无wallet分支不伪造callback；关闭/缺parent/不完整时不能升级军事资格。无需重跑既有cold全部矩阵。生产build/精确EXE登记/新现场actual验证仍由Root在配对场结束后安排。

## 真正能闭合军事 applied component 的剩余来源

必须得到 c/d或其明确子分量的业务producer source，以及它进入本次实际N/F/wallet参数的路径。当前新callee没有任何下一外部call，不能再凭此扩读邻居。唯一有证据的下一入口是**新现场真实 c/d writer PC或真实caller**，再按它做有限source读取。已取得的2C0/2C8 writer只能说明raw snapshot复制，不能替代 c/d类别。

当军事分量最终有来源时，输出须同时保留“本次结算实际应用的军事分量”和“本次实际钱包净 ADD/SUB”两个金额及同次token。正NET时军事分量可能已在净额中抵消；不能再从实际钱包净额中额外扣一次，造成双计。负NET的两个比例分量及rounding也不能强制求和为-deficit。未取得该来源前，军事金额必须为unknown/null，不能填0，`maintenance_attribution=unclosed`不变。

本首版可移机复用的是源字节、精确算式、observer施工合同和decision边界，不是PID、指针、SYSTEM状态或现场观察资格。

## 原件和普通 clone 复用

精确版本为1.20.0.4/Steam25734779/SHA98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518，机器desktop-3fevhd2-1c74096080。新计划和源读取时间/字节/SHA见[原件索引](acceptance/2026-10-16-net-settlement-allocator/ARCHIVE-INDEX.json)；[source合同](acceptance/2026-10-16-net-settlement-allocator/SOURCE-CONTRACT.actual.json)保留逐branch机器规则。原始435B、574B源合同、asm、plan/check/read回执和首版工程决策均在[小archive](acceptance/2026-10-16-net-settlement-allocator/originals.zip)，不含EXE/DLL/媒体。历史C盘argv仅供阅读，不作为新host命令。

复制已证来源见[R0178 writer专题](war-payment-r0178-writer-source-12004.md)，旧generic合同见[raw context专题](war-payment-generic-context-12004.md)。本研究没有新allocator现场callback，原件中的旧unknown保留历史含义。当前军事applied金额及c/d类别均unknown。

普通clone可运行标准库字节复核，不需要CK3/SDK/capstone或本机C盘：

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-net-settlement-allocator/verify_repository.py
```

它核对archive成员、435B唯一extent、分母零分支字节及574B两个call target，不执行allocator、不重现完整付款窗口、不授军事归因或新机器观察资格。
