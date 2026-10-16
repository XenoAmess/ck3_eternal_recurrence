# R04：同次preview的P返回值窄probe候选

本候选的最终相对patch基于 `d730cc0a4713874dffb6e741d0671668dd0877d6`；复用09b83已集成的preview及[a14实际false](episode04-r181-county-false-conjunct-12004.md)，只解决2644→2637尚未分开的三个P调用。新增开关 `XAR_ENABLE_COUNTY_PREVIEW_P_TRACE_12004` **默认OFF**。这是外置source候选：没有native编译、hook/unwind执行、SDK或游戏调用，不是已经部署的能力。R181的实际P结果仍unknown，未授R04 positive，也不归因此前进程退出码1。

准备机器 `machine_id: desktop-3fevhd2-1c74096080`；本次时间、源码和held source pins见 `ROOT-DELIVERY.actual-a22.json`。没有重新读EXE/save/游戏raw或重新hash完整EXE；复用actual4已持131B和420B来源。

## 能证伪什么

现有 `24E2230` 单次原生调用不变。只在exact4 suspended-primary startup安装一个 `2C09DF0` 观察wrapper，并在既有preview调用周围建立局部TLS scope。按**实际native return address**区分固定三槽：

| 槽 | 原生CALL / return | 记录的实际bool |
|---|---|---|
|source P|24E22AE / **24E22B3**|2C09DF0(actor,sourceCounty)实际返回|
|target P first|24E22EC / **24E22F1**|第一次target P实际返回|
|target P second|24E2343 / **24E2348**|第二次target P实际返回；不能合并|

observer每次都把原actor/County参数传给original**恰一次**，并原样透传entry R8/R9的opaque整数位，不给继承寄存器分配业务类型。完整P body没有读取额外entry stack参数。不额外执行P、Q或native condition，不重放native body，不hook尚未持prologue的Q。scope外仅passthrough；同scope的其它caller单独计数、不冒充这三槽；P内部递归调用不覆盖外层槽；嵌套scope遮蔽并恢复旧scope。固定三槽，无ring、保留全局历史、MCP、route写入或Move。

假设未来取得available trace：

- source P实际false，target槽未调用/null：证伪“source P已通过”；只授这次source P false，不给它补敌我/控制权名称。
- source true、target first false，第二次target未调用：定位第一次target P；source分支不再作为本次false原因。
- source和target first true、target second false：保留两次不同的native返回；不以同参数合并。
- 三个P均实际true但最终condition false：**源码推断**剩余拒绝落在target邻接链。`neighbor_Q_observed=false`，具体邻居和Q bool仍null，不能冒充实际Q事件。
- 共同raw门已拒绝而没有P调用：记录零次和未调用null；不是“P false”。

## 同一接口与availability

在既有 `/route_preview/county_entry_condition_v1` 增加可选 `predicate_trace_v1`。默认OFF不安装hook、不建立scope，也不发布此leaf。原最终condition bool及路线仍独立有效；trace失败只降级trace。

trace的available要求：hook实际安装、mode1 scope进入、同线程、original condition返回、外层既有身份/输入前后匹配、三槽实际argument指针匹配及source-proven顺序覆盖。记录 `call_count`、`actual_caller_return_rva`、`argument_identity_matched`、`returned`；未调用三个字段均null。expected顺序由已读raw gates和前一P实际返回确定；漏hook、重复槽、错caller/参数或gap都不能成为available。

unavailable有独立原因；其阶段记录只作诊断，不授本次分支结论。mode0明确unavailable，不借mode1逻辑命名它。leaf带 `additional_native_predicate_calls=0` 和 `neighbor_Q_observed=false`。父字段 `internal_subpredicates_observed` 仅在available trace至少一个P被实际观察时为true；它表示**部分P**，不表示所有内部关系/邻接都已观察。`actual_loss_observed`始终false。

Python production parent normalizer兼容旧leaf缺席，严格消费新leaf。纯只读解释器 `explain_county_predicate_trace_v1` 只输出observed P false或明确标为source_inference的剩余邻接结论，不选省、不提交动作、不授物理损耗。

## 已持source与安装候选

actual4 `2C09DF0..2C09E73` 完整131B SHA `344dc31069a905f0615c45fd59967f35530a14f75e496cda079841c897a3652b`。候选核前16B：`40534883ec2081bae003000061446f43`，是完整push RBX/sub RSP32/cmp County+3E0,CoDa；没有RIP或相对分支。复制后用不改flags的绝对jump到原`2C09E00`，随后原mov/JNE继续。startup写16B detour，只允许exact SHA、主线程已暂停且尚未attempt；字节不匹配使PrepareStartup失败。

trampoline候选自带x64 unwind metadata：push RBX结束offset2、alloc32结束offset6，prefix16+jump14的函数范围[0,30)，xdata位于32；经RtlAddFunctionTable注册。模块和reachable trampoline在进程生命周期内保留；startup失败保持主线程暂停并尝试回滚，不能卸载可能仍被指向的hook。这些是源码施工事实，**RtlVirtualUnwind、SEH异常路径和native执行均NOTRUN**。

`24E2230` 的420B源码及三个精确CALL/return由已有独立source合同闭合。原P wrapper内部关系callee仍有未闭语义；observer只保留原调用顺序和次数，不自称已证明或重新实现它们的业务含义。没有新增P/Q native调用，故本probe也不引入额外一次未知callee执行。

## 已做与下一次资格

只运行四项新Python合同检查：source false且后两槽null；三P true/final false仅给邻接源码推断；错native return拒收；unavailable trace保留父bool且实际a14旧child缺leaf兼容。新native context fixture已写为独立 `EXCLUDE_FROM_ALL` target `xar_ck3_county_predicate_trace_fixture`，不链完整bridge，但**未build/未run**；覆盖恰一次original、opaque寄存器透传、两次target独立、三P true及嵌套/身份fence，不能写成native GREEN。

Root后续若采纳：先正常审查/窄编译并运行新native fixture，验证OFF/ON链接和unwind，再在当场fresh exact4绑定中启用开关。用既有只读preview重现实际首边2644→2637（或一个有来源的当前合法route）；仅当fresh child仍是同一首边时比较。保存一份生产wire由严格normalizer消费，原最终bool/route必须保留。trace缺失或unavailable就保留unknown，不重发Move。无需为采P观察推进一天或实际入境。

native source/trampoline/serializer执行和fresh wire尚未取得；本包所有合成trace均明确不是R181 actual P evidence。实际县writer、unique physical DATA debit和整县总额的边界维持原consumer合同。
