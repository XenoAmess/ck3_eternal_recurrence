# H2743 终战选项 payload 的可见边界（2026-09-29）

## 已冻结的两次读数

| 证据 | 帧与查询 | 实际可读 | 不能推出 |
| --- | --- | --- | --- |
| H2743 attempt-11 `war-options-query-payload.json`，SHA-256 `D7C6A50F5120944B4C53C42B52D0C64734BE9B169235F1C5764B3AABEA0DD2EB` | `native:3`，revision 4/native revision 3，date raw `53217264`，WarID `16777231`，Robert `29829`，CB index 17，战分 `-12` | 原生 query accepted/available；投降 `native_validator_passed=true`、`available=true`，recipient `would_accept_now=true`；白和平和胜利不可用 | 三个选项的 `terms_observable=false`，`terms.status=unavailable`，reason `cb_specific_terms_not_observable`；无领地、封臣、资源、休战实际变化 |
| H3911 R0266 attempt-05 `formal-selected-query-receipt.json`，SHA-256 `10F4A8B67D0635743EF2E41F82A17B063F66B32BD5B4CBED2A6B0F1F6FA73460` | `native:3`，revision 4/native revision 3，date raw `53219928`，同 WarID，战分 `-19`；正式选择器选中 typed `read_only_query/war_termination_options` | 解析后的协议 request/response ID 相同，query sequence 1；原生 accepted/available，投降合法且 recipient 接受，前后暂停帧和缓存金库相等 | 同样三个选项均 `terms_observable=false`；`formal_cash_receipt_eligible=false`、即时费 null。此为另一个日期，不能拼到 H2743 或更新后的 Robert 帧 |

H2743 的 [attempt-11 原始记录](h2743-defender-dejure-readonly-attempt-11-2026-09-28.md)保存直接 query 的 request、envelope 和 payload；H3911 的 [#449 固定提交中的 attempt-05 记录](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/d0f1329020984672b568bfcea8356c2d85e15dba/docs/ck3-native-ai/r0266-h3911-formal-query-attempt05-passive-red-2026-09-29.md)保存正式选中 query 的 Python 解析后协议对象，**没有**独立保全管道原始字节。该回执原件位于 `D:/ck3-research-artifacts/r0266-h3911-formal-cash-20260929/attempt-05/formal-query-receipt/formal-selected-query-receipt.json`，SHA-256 `10F4A8B67D0635743EF2E41F82A17B063F66B32BD5B4CBED2A6B0F1F6FA73460`。两者都不是终战条款的价格表。`recipient_response.would_accept_now` 只回答当前提案会否被接受；战分只描述当前战争局面。把任一读数解释成具体终战资源差额、零费用或退出许可，都越过证据边界。

## 为什么重读同一 query 不会补齐条款

#448 当前 v5 源码 `ck3_autonomous_player/native_bridge/src/bridge.cpp:3623-3678` 的 `AppendWarTerminationOption` 对每个 option **固定序列化** `terms_observable=false` 和 `cb_specific_terms_not_observable`，同时另行序列化 validator、可用性和 recipient response。当前候选 DLL 的终战选项 wire 没有 CB 具体效果、Title2128 的终态、14 行资源签名变化或实际单向休战期限。H3911 的另一 DLL 已在实际响应里显示同样的不可见状态；#448 源码本身不作为那份 DLL 的构建证明。

#448 v5 的另一个只读 query `query-defender-de-jure-exit-terms-v1-16777231` 可以给出当前 Title holder/直接领主前态、双方 14 行资源余额、月度金币收入，以及部分休战条件输入。`bridge.cpp:4395-4464` 明确把 `short`、`long`、`border_raid_pair` 的原版条件置为 unavailable，`evaluated_days`、`persisted_expiry_date_raw`、`title_vassal_delta`、`signed_resource_delta`、`directed_truce` 置 null，`material_complete=false`。v5 新增的全 WarManager 槽扫描最多提供 `border_raid_storage_candidate_v1.status=structural_candidate_only`；未证明等价于原版 `any_character_war`，不能转为休战天数。Python 投影 `ck3_autonomous_player/src/xar_autoplayer/bridge/defender_dejure_exit_terms_v1.py:242-249,299-309` 也拒绝把这些空值转成已知条款或动作。

## attempt-15 的可恢复回读

若 attempt-15 经独立新屏幕租约和新鲜离线证据实际运行，先分别保留它的外置 attempt 原件与 SHA。#448 runner 在同一受管会话里先取得完整 H2743 暂停前帧，然后双读 V1 baseline、读一次 `query-war-termination-options-16777231`，最后取后帧；它对 query 的六字段身份、完整战争集合和后帧稳定性作门禁，最后还要求受管退出与输入哈希未变。只有这些门都过，才可把该次 baseline 和该次终战选项作为**同帧只读观察**联读。attempt-13/14 均在冷加载/绑定门前 RED，没有发出这两种 native query，也不能作为 v5 读数。

成功的 attempt-15 可能验证 v5 槽扫描是否能稳定遍历目标战争，并再次验证当前选项合法性、战分、recipient 反应和已有的部分前态。它无法通过现有两个 wire 取得实际终战 title/封臣/资源 delta、完整休战期限、有限续战损失上界或推荐动作。若只为补终战代价而重跑同一候选，输出预期仍是 material RED；下一项实质生产者必须新增并独立审计这些具体效果/终态或有界风险读口，且依旧需要同帧身份和无动作证明。

## CB effect 同帧只读 producer 的准入判断

目前没有符合风险合同、能在**权威 H2743 暂停进程**主动调用并完整输出 `individual_county_de_jure_cb` 终战效果的只读 producer。原版 `00_dejure_war.txt:455-472` 在循环外把运行时 `scope:target` 送入 `setup_de_jure_cb`，随后 `resolve_title_and_vassal_change`；输入 `targeted_title_ids=[2128]` 不是已解析 scope，也不是终态。现有[静态逆向](h2743-dejure-counterfactual-clone-boundary-2026-09-29.md)发现 `setup` 的 `cb_prestige_factor` 路径写上下文 row，`resolve` 走全局 change 队列；浅拷贝或在权威进程调用所谓 preview/resolve 均没有无副作用证明。先前广义 effect preview 曾发生 live crash，不能恢复为正式读口。

当前唯一能讨论的较窄路径是**先研究，后准入**：在精确 EXE/脚本 SHA 下，证明自然 `setup` 调用中 War 指针、context 指针、CB、双方、目标 Title scope 与同一 H2743 帧的身份关系；建立完整编译后 CB 根、间接 scripted effect 和共有 war-end 根的 node/source 对应及条件覆盖；闭合 change 队列的所有写集合、资源第三方副作用与持久化有向休战规则；再把这些纯数据输入交给经过负例验证的纯函数投影。任何原生 effect/preview 不能为取值而在权威暂停进程额外执行。已有[被动观察点静态候选](h2743-clone-passive-observer-seams-2026-09-29.md)仅适用于未来**隔离副本的自然投降**研究，还未通过 observer 安装/卸载安全、上下文同一性或全树覆盖验证，因此不是当下可接入的同帧只读条款 producer。

在这些前提未闭合前，完整 title/封臣 old→new、`cb_prestige_factor`、14 行有符号资源总差额、全部条件 effect、实际休战期限与 effect-tree 覆盖都维持 typed unavailable。即使以后隔离副本可重复执行并给出后态，仍需证明副本前态与待决策帧在所有 effect 输入上等价；其一次观测不是权威帧的只读查询，也不能独自补有限续战损失上界或授予终战动作。
