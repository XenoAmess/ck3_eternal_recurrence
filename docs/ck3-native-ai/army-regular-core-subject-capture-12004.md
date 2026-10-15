# 1.20.0.4：限定 CArmy 的 regular-core 原始物理采集

这是供智能体开发、决策消费者和战争四期共同引用的采集合同。2026-10-15 的离线资格来自
`machine_id=desktop-3fevhd2-1c74096080`；当前补丁尚未取得实机采样资格。不得把模拟测试、源码分析或新构建当作实际补员/损耗结果。

## 修复的问题及范围

4096 上限位于自然 regular-core **采集**，先复制全 manager 的对象可能耗尽额度；后来按 Army 过滤查询结果不能补回已漏采的 entry/return。
本改动允许在启用前明确绑定目标完整 CArmy generation ID，只复制这些目标的 DATA 物理闭包。
仍保留全部 manager occurrence 顺序、重复 ordinal、共享 DATA/ArRg alias 和完整七槽，不按归属过滤共享物理引用。
4096 个 combined physical object 与4 MiB读取上限均不提高。

限定范围时全局 `capture_complete` **始终为 false**，原全局消费门禁不放宽。
新增 `subject_coverage_v1` 单独描述目标闭包：实际scope epoch、GameState、owner、完整 CArmy↔Unit 身份见证、manager occurrence覆盖与缺失原因。
其中scope epoch是采样epoch，不是load epoch。

## 实时启用与消费

先读取当前 paused frame 和目标 Army strengths，取得真正的 `native_carmy_id`。
不要以 Public Unit ID、角色ID或其他进程的 CArmy ID 替代。
沿用现有 `ck3_set_army_observer_research_sampling_v1`，仅在
`observer_family="regular_core", enabled=true` 时传
`regular_core_full_carmy_ids=[actual_full_carmy_id]`。

scope只在disabled且无active capture时绑定。原生入口核完整CArmy、magic、owner、Unit反链及fresh controllable player列表；身份前后变化则拒绝，不退回普通全局启用。
显式null、空/重复/负ID、超过64项、query/disable/all/其他family均拒绝。
不传新字段保留原行为。改变范围需完成disable，再用新鲜帧显式enable；不得为了抹去已发生的丢样自动清环。

只在自己的进程、创建时间、connection generation、GameState及采样epoch内比较完整entry/return。
`subject_raw_physical_delta_v1` 对稳定物理token的七槽原始净变化去重，共享alias不重复累加。
未知manager解析、主体不在原roster、身份变化、容量/读取预算、缺七槽、fallback或未闭合override均保持局部不完整。

该值**不是**指令局部actual ADD、完整原因分解、Army总变化或全局monthly模型。
决策系统可据它判断“本次原始物理采样完整/不完整”，不能据此把补员、饥饿或围城原因标为已证。
相应业务结论仍须绑定具体自然阶段、真实执行分支与独立实际后果。

## 代码与可复核资格

- 采集与身份绑定：[army_regular_core_passive_12004.cpp](../../ck3_autonomous_player/native_bridge/src/army_regular_core_passive_12004.cpp)。
- 严格范围解析：[army_regular_core_scope_request_12004.hpp](../../ck3_autonomous_player/native_bridge/include/xar_bridge/army_regular_core_scope_request_12004.hpp)。
- 局部闭包与物理净变化消费者：[army_subject_physical_coverage_12004.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_subject_physical_coverage_12004.py)。
- 可跨机重建的原生夹具：[说明及源码](../../ck3_autonomous_player/native_bridge/tests/army_regular_core_subject_capture/README.md)。
- Python反例：[test_army_subject_physical_coverage_12004.py](../../ck3_autonomous_player/tests/unit/test_army_subject_physical_coverage_12004.py)。

作者实际完成36项原生行为检查、32个constexpr解析例、2个MCP→Driver连接例，及真实未改写native JSON→normalizer→consumer的1个event/1个raw pair。
Root整合后，范围、控制、付款新增消费者共162项聚焦测试通过，既有R0173便携实证在`-O`下仍能重算。
mock内的foreign persistent引用不是已证不同角色政治所有权；夹具未到达的political abort边界不能变成生产实现。
实机新scope启用、样本与应用原因均待下一正常进程观察。
