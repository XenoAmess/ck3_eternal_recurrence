# 县residual的最小原生父调用scope（1.20.0.4）

本候选用**一个新detour**在 `2A957E0` residual allocator的非零预算continuation建立同线程token，写入现有2634190 loss writer事件。县来源由真实直属返回点 `24E2630` 与实际array receiver关系判定；周期来源由真实返回点位于已闭合 `24E3410..24E3A3C`、最近显式periodic callback及其实际receiver关系判定。不使用整段县回调的任意transitive子调用作县损耗标签，不新增loss ring或公共MCP工具。

当前是 **source candidate，3 TU syntax GREEN，7 Python synthetic-wire tests GREEN**。新native fixture未编译、链接或执行，生产DLL/冷载/自然hook/实机parent归因仍未验收。Root当前a05与主树1463保持冻结，本候选供后续a06采用。

## exact source与有限读取

来源机器 `machine_id: desktop-3fevhd2-1c74096080`，观察时间 `2026-10-15T15:22:44.185269+00:00`。来源为Root已核验冻结EXE的 `IDENTITY.actual.json`，CK3 `1.20.0.4 / Steam25734779`，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本包先有限索引既存原件；本机限定范围NOTHELD后，经Root明确批准，只读 `[2A957E0,2A95941)` **353B/1read**，新metadata、邻域、callee读取及全EXE hash均0。section map复用同机已冻结付款源，未重扫header/pdata。

外置 `high-parallel-county-a02/READ-RECEIPT.actual.json` 保存argv、file offset44649440、实际读取量、原件身份与缓存section-map SHA；`RESIDUAL-2A957E0.actual.bin/.json/.asm` 保存原始字节、98条完整反汇编及源pin。353B SHA为 `7503ed163f05b1c3c3e06bf523078db997acb9bf59c1e55cbd7cf48c01058190`。这些是本机source读数，不给其他机器的部署或实机资格。

实际source首部：

```text
2A957E0 85d2                 TEST EDX,EDX
2A957E2 0f8458010000         JE 2A95940   ; zero-budget RET
2A957E8 48894c2408           MOV [RSP+8],RCX
2A957ED 53                   PUSH RBX
2A957EE 56                   PUSH RSI
2A957EF 4155                 PUSH R13
2A957F1 4883ec30             SUB RSP,30
2A957F5 48896c2458           MOV [RSP+58],RBP
2A957FA 410fb6d8             MOVZX EBX,R8B
```

从真正entry粗拷前15B会带着relative JE，不能原样搬到任意trampoline。候选在 **2A957E8** 处使用18B完整MOV/PUSH/SUB/MOV前缀，无branch/RIP operand；绝对FF25跳转和trampoline复用项目现有方式。安装另外核首8B zero bypass。预算0在原生入口直接RET，永远不走writer，因此不需要为其制造parent token。没有引入branch-relocation框架，也不把continuation hook说成尚未执行TEST的完整入口。

实际逻辑ABI为 `opaque_RAX(CArray<int32>* RCX, int32 EDX, uint8 R8B)`。原始RAX是不解释的返回寄存器；wrapper原样返回一次continuation的结果。flags只有R8B被原生读取，不把上24位命名为有效flags。原始array字段为data@0、capacity@8、count@C；实际writer CALL `2A958E3 ->2634190`，返回 `2A958E8`。

## 何者是receiver，何者是来源

county callback的RCX是CArmy；allocator的RCX是CArmy内的**array header**；writer的RCX是ArRg。三种receiver不能互相强转。

已闭合县源码在 `24E2627 LEA RCX,[R13+38]` 后，传EDX=保存的正剩余预算、R8D=0，于 `24E262B` 调allocator，返回 `24E2630`。仅这个实际返回点允许从array地址减38得到县source CArmy；不能对任意allocator caller做此推断。allocator通过同一array顺序解析ArRg full ID后调用writer，完整353B source再次确认其full-generation/magic/非-1检查。

候选在allocator entry保存实际CArmy的native FullID@10、magic `Army`@14、public Unit FullID@124与array header；writer entry独立重读并核相等，再从该实际array找到writer已捕获的完整ArRg ID。`matching_roster_occurrence`只是当场可读的匹配项索引，不声称它是allocator此轮正在处理的ordinal。所有读取由已有guarded reader完成，无原生getter、查询重放或写入。count超过4096或任一所需读取失败只降低source_complete，不阻断原函数。

周期来源还要求最近的generic frame确为 `periodic_supply_callback`，其typed actual receiver加38等于allocator RCX，且真实直属return位于已source-closed callback extent内。真实return保留在wire，不用flags0将周期围城与县剩余混为一谈；本包也不把周期residual再细分为饥饿/围城/劫掠。原始flags只代表**allocator入口flags**，不能冒充内部第二pass清bit后的当前flags。

writer context只有其实际caller return=`2A958E8`才可能source_complete。allocator内其他callee若又间接调用writer，不会因处于scope而被归因到这笔分配。这是选择allocator scope而非整24E23E0 scope的关键边界。

## 与供给parent共享和嵌套

复用R05独占的 `ck3_12004_native_invocation_context.hpp`：单一inline atomic token和TLS链；`NativeInvocationScope12004(kind,thread_id,typed_payload)`，kind4为residual_allocator。县/周期receiver、entry/return RVA与金额属于各typed payload，generic primitive不解释它们。没有第二套counter、TLS栈或loss journal。

两类来源不设互斥假定。县源码包含Fleet Unit递归和后续common/script callbacks，现有source未证明县与周期callback永不嵌套；库必须支持最近scope遮蔽和正常return恢复。partial/unknown typed receiver也建立最近scope，不能继承外层的已知身份。县直属return2630即使处于外层periodic scope，仍标县；一个真实periodic callback在内层时则通过其自身receiver关系标周期。typed payload裸地址只在同步调用期间使用，不过wire。

allocator token与enclosing callback token分别保存。它证明某个writer实际在这次非零allocator调用内，不是整个county callback的共同invocation ID。若以后要把primary与residual归成**同一次完整县回调总额**，仍需额外24E23E0 entry/return父token及窗口覆盖；这个候选不授该总额或父调用完整return信用。

R05的既有supply_parent_context必须继续保留在直属周期residual writer上。新的residual scope会遮蔽generic top；兼容接线只在已核直属周期return与其紧邻periodic frame时，显式调用R05的受限FromFrame读取口，继续从真实callback CArmy读取writer-entry stock。县return2630不满足这条兼容路由，不能借用外层periodic stock或标签。此兼容小接口由R05维护，不用临时改写TLS current或任意遍历祖先。

## defaultOFF与接线

`XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004` 默认OFF；开启才把新hook TU加入Runtime、给Runtime/Bridge定义开关，并在既有 `.4` suspended-primary PrepareStartup中安装。只核exact build、首8B和18Bcontinuation前缀；保留原过程一次执行、零预算bypass与opaque返回。安装失败保持startup失败，已可能被引用的hook/trampoline不释放；不热换当前a05。

现有 `ArmyActualLossWriterObservationV1` 新增optional `residual_parent_context_v1`，由原writer wrapper在真实before读取之后复制；使用原512事件ring、序号、overwrite和FullID查询join。native serializer和strict normalizer均additive；OFF/旧producer缺字段保持缺字段。`request_source`、token、thread/depth、实际allocator caller、entry budget/flags、actual CArmy IDs、array/writer身份和失败位均保留。

R04只读consumer接受source_complete的 `county_entry_residual` 或 `periodic_callback_residual`；physical debit仍复用R03逐槽事实判定。来源已知不代表已扣兵；physical零/负值/未知独立保留。没有context、ID变化、范围截断或thread不符时继续unknown，不用预算或cached delta填physical数值。`county_total_debit`、`periodic_total_debit`继续null；current-query全军历史membership边界不变。

采用顺序为R03 shared physical primitive、R04 a01、R05 shared-parent a02与FromFrame兼容delta，再采用本a02相对patch。公共token header不在本补丁中重复定义。bridge.cpp只增加guarded include和实际startup调用；没有新增公共query/command、自动enable或runtime sampling开关。

## 实际检查和下一资格

`syntax-a02.actual.json`绑定兼容接线后最终三个候选TU的SHA、精确 `/Zs /std:c++20 /W4 /WX /permissive-` argv及exit0：新hook、typed fixture、既有writer接线。它未生成对象或EXE，也不证明detour执行。更早的 `SYNTAX.actual.json` 是FromFrame接线前记录，未覆盖后来的compatibility/fixture增量，原记录保留。`PYTHON-TESTS.actual.json`记录7个 `-O` synthetic wire tests，通过typed decoder和R04生产consumer，验证同日同writer-return的县/周期区分、partial保留physical、旧包unknown及必要来源约束；不是compiled native wire或live结果。

新typed fixture源码涵盖一次原调用、opaque返回、县与周期同栈共享token、来源优先级、跨kind遮蔽/恢复、CArmy代际变化和writer同index异代际；**执行NOT_RUN**。Root后续a06需先做该fixture实际执行及生产compile/link，再验actual非零continuation自然触发、源caller与physical事件同一packet。任何native或live GREEN只授其实际边界，当前R0174/a05不会被此候选追认。

本机工作包共用Root512MiB池，本lane≤8MiB，截止 `2026-10-16T07:45:01.597Z`，不延长。没有游戏/SDK/桌面、大存档/raw读取、生产构建或主树写入。`open_kaishek: not-applicable`，本题为编译原生ABI/自然scope和已保存wire消费，不含脚本有限运行时可替代的子集。


## 2026-10-16 narrow native fixture qualification

Machine-specific qualification: `machine_id: desktop-3fevhd2-1c74096080`.
Observed UTC times and exact source/command/EXE/wire pins are recorded in
`C:/ck3-war-episode04-research-20261004-a01/e04-county-residual-fixture-20261015-a01/RESULT.actual.json`.
This qualification uses the frozen source1463 plus R03/R04a01/R05 shared-a02 /
FromFrame-a03/R04a02 dependencies. It executes two project translation units
only: the residual fixture and actual loss-writer producer/DTO serializer.
No CK3 EXE instruction, SDK, game, desktop, bridge DLL, full production build,
new binary read, old seven Python cases or old three syntax cases was run.

ON and default OFF compile/link/run pass with `/W4 /WX /permissive-` after
standard build-producer registration and exact SYSTEM `verified` settings
receipts. Each mode forwards nine nonzero residual originals exactly once,
preserves the opaque return and native arguments, models two zero-budget
bypasses without allocating a scope/token, and invokes fourteen local writer
originals. Two DATA aliases resolve to one physical slot; each actual writer
capture has debit5, distinct from allocator budget7. The first8 native TEST/JE
are source-reviewed and modeled locally; they are not executed by this test.

The actual writer hook now captures its natural return PC and forwards to
`InvokeActualLossWriterJournalWithCaller12004V1`, the same producer called by
the fixture with **explicit synthetic RVA premises**. No image-base tuning,
wire setter, saved-event mutation, or claim of an observed game caller is used.

Native assertions cover direct county return24E2630 versus a direct periodic
range premise with immediate typed parent, CArmy generation change, source
roster ArRg FullID generation mismatch, wrong writer return, a nearest unknown
scope, an actual foreign `std::thread`, wrong thread ID, restoration of the
residual frame and then the original supply frame, and FromFrame token/stock
identity retention. County/unknown contexts never borrow the outer supply
receiver or stock. Default OFF allocates no token and emits no parent fields.

Actual serializer outputs `on/NATIVE-WIRE.json` and `off/NATIVE-WIRE.json` are
consumed unchanged by exact copied production strict-contract and county
consumer modules. `native-qualification-a03/WIRE-CONSUMER.actual.json` records
the source pins and results. Both wires truthfully have
`observer_installed=false`: fixture initialization installed no game detour.
The strict normalizer retains all14 local physical values and source fields;
the production evidence consumer returns `incomplete` with
`natural_observer_not_installed` and grants zero qualified live physical events.
It also keeps both complete county/periodic totals null. This refusal is an
expected successful fixture boundary, not a positive actual4 game observation.

Build/source increment is below16MiB in the existing Root512MiB pool; all
artifacts share the original `2026-10-16T07:45:01.597Z` review deadline. No
reservation was extended. Runtime installation, bridge-TU/full production
qualification and natural actual4 positive evidence remain unrun.
