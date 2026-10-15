# R06：选实际补员采样对象，保留零值原因

本页衔接 [真实ADD与开关](episode04-refill-application-12004.md)、[persistent与chunk资格](episode04-special-troop-refill-eligibility-12004.md) 和 [现有普通选军策略](army-current-replenishment-normal-selector-12004.md)。机器可读当前选择见 [selector输出](evidence/episode04-refill-sampling-target-selection-12004/selection.json)。它是读取次序与准入知识，不提交游戏动作、不制造实际ADD。

## 此刻应先测谁

R0177 已有小型记录只允许预选，不允许把旧字段拼成下一 a08 帧：

- **优先重新查询普通 Army18**。Root 已确认该军当前1195、有缺员；初始010的 public/native ID均18。缺员只是寻找正请求的起点，不等于任一 physical chunk已有正q。
- **Army93/native85 暂不作为正ADD首选**。新正常 S0 `e6ee…7d67` 的该军为特殊兵250/250。它仍可用于满员/开关观察对照，但不应仅因开关开启就为它等待一个月并期待ADD。该兵类称呼来自Root正常现场，不由250/250或 raw138臆造永久类别。
- 若18的完整新帧投影没有合适正请求，记录具体门和缺项，再查询另一支有实际物理缺额的受控军队；不回填93的旧 permission或旧帧data，也不宣称93永久不能补员。

R0177 的 [CURRENT小记录](acceptance/2026-10-16-episode04-r0177-a07-current-literals/README.md) 在日期53146632有以下直接开关字面值：18包含21个persistent，其中19个为非GDbo定义bypass，2个从来源Character31254实际读取 `4A9=1/enabled=true`；93包含4个persistent，其中1个bypass，3个从31254读取开启。**这些是开关读数，不是CanReplenish、prepared148、q或ADD结果。** 本页的 [来源分组](evidence/episode04-refill-sampling-target-selection-12004/source-groups.json)保留精确persistent身份；原DATA occurrence未删除。93开关为ON与它满员、可能被其它原生门拒绝并不矛盾。

新 a08 完整同帧数据尚未取得。本轮输出 `WAIT_FRESH_A08_INPUTS`，推荐先读18；`eligible_for_positive_ADD_capture` 为null，不伪报通过。

## 直接复用已有入口

1. 取得新鲜暂停帧与同一已完成 `ck3_query_army_strengths` 的完整目标cohort；保留 snapshot/revision/nativeRevision/date/episode/generation、owner和双Army FullID。不能将小型scalar/开关投影当完整family传给normalizer。
2. 调用 `bridge.army_persistent_refill_eligibility_12004.classify_army_persistent_refill_eligibility_12004(frame, packet, army_id=...)`。它已经核身份，按 persistent FullID+physical index 去重，保留 DATA occurrence、两native bool、containing138/definition、observed prepared148、fresh及条件normal preparation，单列empty Character角色。不要再建一套reader或推断兵种registry。
3. 对同一次query的原目标Army row调用 `bridge.army_scoped_ordered_refill_projection.project_scoped_observed_prepared_ordered_refill(row)`。需要完整七槽、native persistent occurrence顺序、q-index及raw cleanup/position上下文；`ordered_core_ready`不完整时直接列 `missing_inputs`，不能拿单槽简算或改global complete代替。
4. 优先选完整投影中某一真实物理槽有**正的最终共享 q-buffer 请求**的候选。保留其Regi FullID、physical slot、q-index、manager occurrence和别名Army/ArRg引用；若能同时看到预测raised净增加，作为镜头可见性的次级排序。q>0仍只是条件请求，不能记实际ADD。若随后pair-clear导致净0或负值，分开解释。
5. 依据新鲜身份绑定现有自然 regular-core/实际指令观察合同；取得真实callback父链、TID、Regi/slot与原生写入前后。部署/启用/自然触发/回读各自保存，query-time roster不能补成执行时身份。窗口采集不足或未触发保留unknown。

`current_replenishment_army_selector_v1.select_current_replenishment_army_v1` 是普通战争规划的另一个策略：在实际兵力相同的军队中，派走**较小正补员机会**者，让较有机会者留守。R06寻找正ADD的目的不同，不能直接照搬它的最小值排序或要求等兵力。分类器与顺序投影已经具备本页所需判据；本补充不改正常战争规划排名。

## 为什么0不等于关开关

| 观察到的0或false | 已闭合解释 | 不能据此推出 |
|---|---|---|
| Army current==maximum | 没有整军层面可见缺员；仍须检查physical数据 | 特殊兵永久不能补员、开关关闭 |
| physical maximum0或current>=maximum | 独立chunk predicate先拒绝；不产生该槽缺额请求 | 来源角色4A9为0 |
| native CanReplenish=false | 可能raw138==1、Army门、来源角色开关、政府/资源分支或chunk门 | 一定因资金或开关；一定没有旧缓存请求 |
| `native_chunk_can_replenish=false` | 独立物理槽状态/地点/Army等门 | persistent Can也必为false；两bool应人工AND |
| fresh fraction>0但prepared148=0 | fresh与已缓存输入是两种事实，normal preparation尚未执行或选择了拒绝分支 | 当前core已经获得fresh正F |
| current Can=false、observed prepared148>0、chunk true | cached core不重新检查persistent permission，仍不能排除请求 | 开关关闭使本轮q必为0 |
| prepared正、chunk true、实际缺额正、q=0 | Q100000向零整数截断、共享q-index覆盖等仍可给0 | 原生AL=false或客户端开关关闭 |
| 原生请求AL=true、q=0 | source允许进入ADD循环并加0 | 实际补了人；无任何原生写入 |
| Army净增0、callback physical净0 | 别名、pair-clear、其它损耗/刷新可抵销，或确无正请求 | 无实际ADD；开关为OFF |

源码 `262C6E0` 的persistent guard138与 `uses_supply`所用141是不同输入轴；不能把是否耗补给当补员许可，亦不能因138枚举名尚未闭合就改称“所有特殊兵永不补员”。本页不增加141读取，也不从供给损耗资格填CanReplenish。

`currentlyNeeds`在此选择中使用实际physical current/effective/max的缺额与现有native predicate，不虚构一个当前DTO未公布的同名bool。state3/current0的effective current按源码为maximum，不能看物理0就当缺员。empty DATA的1/1 Character角色也不计入可补物理槽。

来源Character及资金/人力相关门继续按实际分支分别保存：先解析真实来源角色，再读其4A9和原生Can。permission源码出现 personal/Land/military raw负值及定义位分支；没有对应当前operand或来源语义时，输出 `resource_cause_unknown`。玩家现金非负、开关开启或一个总funds数字不能代替分支通过；也不能把本包未展开的raw值强叫manpower不足。正q优选不需要新增这些raw reader，细分拒绝原因确有阻断时再报具名输入缺口。

## 别名、权重和真正缺的当前输入

同一 `(persistent FullID,physical index)` 物理槽在多个DATA/Army里可有别名，缺额及物理净变化只计一次；DATA引用关系另保留。manager里的重复persistent occurrence却代表重复执行，不能从顺序模型去重。q-index也不等于physical index；整向量算完再ADD，按最终共享槽判断。补给/分军权重不参与制造补员人数。

本轮仍缺新a08同帧：完整目标Army身份与current/max、allDATA七槽与别名、两native bool、containing guard/definition、observed prepared148与fresh、manager occurrence/q-index、位置与raw cleanup门、完整顺序投影结果。若解释开关，还需**实际来源角色**的独立4A9前后及自然preparation缓存后验；若解释资源拒绝，则需该分支实际source resource operands。实际ADD另需生产观察器本场安装/采样回读、自然父链、完整指令前后与窗口fence。

这里只给下一采样入口与缺项，不把旧R0176 guard1或R0177 initial010 switch填给新S0，不把静态模型升级为原生执行。无新代码、测试重跑、EXE读取/构建、SDK/桌面或游戏动作；本机外置128KiB子包计Root active32MiB池，原2026-10-16T07:45:01.597Z复核期限不延长。
