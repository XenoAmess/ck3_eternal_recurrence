# 1.20.0.4：真实围城 writer 的原预算栈捕获

2026-10-16；源码基线 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。
来源机器 `machine_id=desktop-3fevhd2-1c74096080`；实际捕获时间、解释器和逐次I/O见下述外置回执。
复用Root冻结的CK3 1.20.0.4 / Steam25734779 / EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，没有重新全读或hash EXE。

## 新闭合的最小来源

现有writer `2634190`并没有一个独立的“围城专属”入口：实际callback `24E3410`先分别形成供给、围城和劫掠预算，
再在 `24E3646–3656` 把原siege与raid相加，preferred在 `24E3777`调用同一writer，return PC为`24E377C`。
因此继续只看这个return PC，或只看当下siege/raid端点，不能证明这一笔的raid分量为0。

本次在预注册窄计划下实际读取：callback完整1580B、siege predicate完整212B、预算getter三个实际`.pdata`片段24+117+66=207B。
合计新函数字节**1999B**；另有具名`.pdata`二分metadata **360B**，没有全段扫描、邻居函数读取或EXE执行。
旧Z原件在本机不可读；新的本机held ASM位于
`C:/ck3-e04-resume-20261015-a01/high-parallel-siege-source-a03/`，后续分析消费这些小原件，不再重读EXE。

| actual4 原生位置 | 读到的执行事实 |
| --- | --- |
| `24E3410/3415` | callback先保存RCX，`sub rsp,68h`建立固定native callback frame。 |
| `24E3430–344E` | updater成功才调用supply getter；否则预算0。`344E`把原supply整数预算写到native callback `RSP+20`。 |
| `24E3453–3474` | 调用`24E8540`实际predicate；true时`3466`调用`24DD560`，`346B`把EAX写到`RSP+80`；false分支`3474`明确写0。 |
| `24E347B–349C` | 实际比较CArmy+1E8与-1；有效时`348E`调用同getter，`3493`写到`RSP+88`；否则`349C`写0。 |
| `24E345C/3484` | 两次getter的RCX分别来自RIP槽`5C69618`和`5C69098`；RDX为相同actual CArmy。 |
| `24E35FA/3633` | supply preferred与flags2 residual在siege/raid预算形成之后执行。 |
| `24E3646–3656` | `R10D=[RSP+88]+[RSP+80]`，32位相加，再覆盖`RSP+88`；`RSP+80`仍是原siege。 |
| `24E3777/377C` | combined preferred CALL/return；CALL压入8B return address，因此此writer的incoming return slot等于native callback RSP-8。 |
| `24E37A5–37AE` | 后续flags0 residual仍共用allocator；本leaf不把它分成siege/raid，也不从其它位置读本布局。 |

`24E8540..24E8614`完成Unit full-generation解析、Unit+18/170条件、位置identity及Province+788检查，最后调用`2C16670`。
该最后callee本次没有展开；这里没有重新命名其内部逻辑。重要的是：原callback已经执行了真实predicate和预算getter，
捕获的是其**真正写入的结果**，不是我方重算该predicate。

`24DD560..24DD62F`三个连续runtime片段现均已实际读到；首24B有到`24DD5ED`的跳转，不能把那24B误称完整逻辑函数。
闭合后的getter遍历原Army ArRg顺序，以generation/magic/fullID校验的cached current作signed32累加，rate限制在0..100000，
执行整数乘除/截断并cap到current。它没有physical写回；预算和实际physical debit继续分开。

## 默认关闭的12B增量

沿现有默认OFF的 `XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004`，不加entry detour、query或新调度平台。
在真实 `XarActualLossWriterHook12004V1`入口取得MSVC `_AddressOfReturnAddress()`，
把该**真实incoming return slot指针**显式传给现有typed producer；不能在后者自己的helper frame里再次取地址。

只在实际caller `24E377C` 且现有supply parent context可得时，使用既有fault-bounded reader读：

| 从真实writer incoming return slot的偏移 | 实际量 |
| --- | --- |
| `+28`，4B | 原supply预算，等于native callback RSP+20。额外供R05排混合原因使用；不以stock0→0猜预算0。 |
| `+88`，4B | 原siege预算，等于native callback RSP+80。 |
| `+90`，4B | combined siege+raid预算，等于native callback RSP+88。 |

`derived_original_raid_budget_soldiers = wrap32(combined-original_siege)`，保留native32位加法的逆运算和signed值。
例如siege=INT32_MAX、combined=INT32_MIN时，raid为1，不能用Python无限精度减法得到-4294967295。
两个核心DWORD完整时才发derived raid。单独supply读取失败保留null/flag2，不抹掉完整的siege/raid两项；
返回槽缺失、siege或combined读失败都保留unknown，不填0。

新增owned字段为writer event的可选 `siege_budget_at_writer_v1`，不向wire泄露stack指针。
缺leaf仍是合法旧wire。自然hook原参数和原trampoline不变；共享producer只新增default-null内部参数，保留唯一
`original(regiment,request_raw)`调用。未来coherent构建须重编受该内部C++声明影响的调用者，不能混用旧helper对象。
当前R0175/a06不能因源码存在而声称已经加载此leaf；它只供下一正常构建/冷载。

## 视频claim与智能体共同准入

已有[R03消费者](army-siege-parent-loss-consumer-12004.md)继续要求实际installed journals、同一callback token、双FullID/date、
daily callback来源`2A9AB4B`、direct preferred caller`24E377C`、fresh sequence和完整positive physical debit。
增加leaf后，只有该笔 `siege>0`、derived `raid==0`、核心capture完整且无对应失败flag，才进入
`siege_only_positive_writer_events`并使`source_siege_only_budget_bound=true`。

这允许视频精确说“这个围城preferred原生调用实际扣掉了N个物理兵员”，也允许智能体把该笔归入siege原因。
N仍取即时unique physical槽before-minus-after，不能换成预算、request、Army净差或死亡数。
原supply预算即使非0，也不会把**另一独立combined preferred阶段**的事件改成supply；它另列，不能把所有阶段混作围城。

raid非0、预算0/负、栈partial、wrong caller、无parent、缺physical或旧wire，都只保留原combined/physical事实，
不授siege-only原因。residual和完整区间/整军因果总额仍不ready。
本leaf不提供周期间隔全部写回、补员抵消、invocation-time ArRg所属CArmy列表或动态镜头clean span。
正式影片仍须本期Robert实际原件/时码；条件模型、源码和synthetic用例不抵扣新业务。

## 实际验证及复核期限

本包已对修改后的真实writer TU执行ON/OFF各一次`/Zs /W4 /WX`，两者返回0；未生成object、DLL或EXE，未运行native fixture。
constexpr偏移/32位逆运算在编译期检查。8个新增Python用例实际通过，覆盖合格单因果、混合raid、缺槽/partial、
独立supply失败、signed32 wrap、wrong helper basis/caller、旧wire和strict边界。
旧9tests、上游7tests及游戏/SDK均未重跑，新增live证据为0。

实际回执为外置 `SYNTAX.actual.json`、`NEW-TESTS.actual.json`、`READ-*.actual.json`和最终`ROOT-DELIVERY.actual.json`。
普通research-plan check只授record/file integrity；本轮offline源字节读取不授任何游戏操作资格。
全部外置产物≤8MiB，沿Root共享512MiB与`2026-10-16T07:45:01.597Z`期限，不另预留、不延期。
