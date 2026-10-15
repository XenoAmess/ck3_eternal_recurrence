# 四期 R04：现有第一站到达 consumer 的县入境风险解释

现有 `query_army_strengths` 已生成到达前 `24E23E0` 调用选择，但没有把
同帧 `county_entry_inputs_v1` 转成路线解释。本增量直接在现有
`current_unit_arrival_prestore_disembark_write_v1[*].projection` 内加入
`county_entry_risk_v1`。Service 只把已经计算的 movement prefix 继续传入，
不新增 MCP、query、hook、native getter 或动作提交。

## 输入和可以做出的判断

输入继续通过生产 strict county normalizer。现有 Service 仅在
snapshot ID、revision、native revision 全部对应 query 时传入 Army context；
解释器再核完整 route 的第一站与 native condition 的 source/target。
没有这个连接时，当前 native B 仍可展示，下一站风险保持 unknown，
`required_observations` 给出缺失的具体字段。
fresh 完整 route 为空时则明确返回 `no_current_first_edge_to_assess`，保留
当前 Province 和观察到的空路线，不把“无第一站”写成“上下文读取失败”。

| 已有输入 | 使用方式和边界 |
|---|---|
| native current B/F/M/minimum N | 原样显示当前 `24E6650` 结果；不以 GUI5%或 Python 合并取整重算 |
| existing arrival-prestore call selection | 复用 typed current Province、Unit kind、distinct typed first target 的已闭 consumer |
| old/target definition `+1B` | 分别保留原始字节，只用非零准入，不命名未证地形或敌我 |
| movement prefix 的 conditional post-entry Unit170 | 在同一 held-input 条件下，descriptor1=`prior signed170>0`，从而解释县特殊 flag；它不是未来回调实测 |
| `24E2230` condition | 同帧 actual actor、旧省份、第一站和 mode 的 native boolean；false 保留为观察值 |
| loaded floor child | 原样保留 signed64 两下限、raw Army1D4 和独立 unavailable；缺失不填0/100000 |
| loss application 的 definition≤0 current count | 同 W 时给 `P=min(B,S_pref)`、`R=B-P` 的预算分桶；不展开逐团 writer 或 physical debit |

所有条件的 conjunction 支持 true / false / unknown。任一已知 false 可
证明这个条件分支不选择正县预算，不要求补齐已经不被该分支需要的字段。
预算 B0 同样不是“实际县损耗0”。空 ring、不变兵数及同日周期损耗均不参与
这份风险解释。实际扣兵继续使用 [县 writer consumer](episode04-county-entry-loss-12004.md)。

解释器另外分开“下次 entry 是否选中到达”与“这个第一站若到达是否选择县预算”。
下次 entry 没到达，只能令当前局部分支不调用县 callback，不能抹掉仍在行进路线
上的县风险。`conditional_positive_county_budget_if_this_edge_arrives` 使用已有原始
typed current/target、Unit kind、distinct ID 与县准入；路线审视依据此字段，而非
仅用 next-entry call=false 判定路线免损。

## loaded floor 使哪一种零倍率可以被区分

[完整 multiplier 源码](episode04-county-entry-multiplier-12004.md) 给出：

```text
raw Army1D4==0                            ->24DD830=false
24DD830=true                             ->M=0 直接返回
raw Army1D4!=0 且24DD830=false             ->M>=实际 loaded 第二下限（signed64 max）
```

因此同一 captured frame 的 `raw1D4!=0 && M==0 && second_floor>0`
可以推出这次 native M getter 的 zero predicate 为 true。这是源码推导，
不是额外调用 predicate；只知道 M0 而缺下限时仍为 unknown。
`raw1D4==0` 的 M0 可以来自普通1A7路径，不能称为特殊免疫。
非零 M 则排除该次 getter 的 zero-predicate true 路径。
另在 raw1D4为0且 M 严格大于实际 base floor 时，signed max 没有选择下限，
可按 wrap64 逆解 `ArmyProperty1A7=wrap64(M-100000)`；M等于下限时不作此逆解。

这不闭合 Army1D4、Army1D8、Government definition+17E 或 property1A7/1A8
的正式类型、名称或 producer；也不把当前 M 的一次观察冒充预算内部第二次
getter 的独立回执。它们的边界与原始专题一致。

## 给智能体的只读选择

正县预算和准入均可判定时，返回 `review_current_edge_before_advancing`。
可以保持暂停审视当前第一站，或比较**已经取得合法 native route preview**
的候选第一站：候选实际 definition1B为0、或实际 `24E2230=false`，可在其余
输入保持时绕过该县预算分支。没有候选 native 字段时，解释器只列出需要
观察的字段，不指定 Province，也不构造 move step。

只有县预算分支被排除时，返回 `no_positive_county_budget_on_this_local_branch`。
这不证明整条路线、补给、战斗或围城安全。所有结果保留
`route_overall_safe=null`、`actual_physical_debit_soldiers=null` 和
`selected_new_target_province_id=null`。不建议按尚未证明的 modifier 名称换
将领或改编成，也不把预算直接当节省的兵员数。

## 验证与 actual 边界

本增量最多四项新行为检查：现有 Service 转交同帧 prefix 并保留 native
预算及 P/R；false/zero分支；缺 fresh context/prefix 的精确缺口；loaded
positive second floor 对零倍率原因的区分。早期 movement/selection 输出
只在新 Service seam case 中作为合成 held inputs，旧套件没有重跑。

本机记录：`machine_id: desktop-3fevhd2-1c74096080`。源码基线
`94e7ad31e336790297d40c3b1f580867b18e5d66`，任务首次观察
`2026-10-15T19:53:03Z`；外置包为
`C:/ck3-e04-resume-20261015-a01/county-route-decision-a07/`，
`BASE-PINS.actual.json` 和 `FIRST-INCREMENT.actual.json` 保存精确来源和新检查。
运行期间的 actual 验证等待 Root 的同机 a07 query，不以合成 case 充当实机结果。
后续实际 current 和 post-Move 验证见下文；它们没有把合成 case 升格为实机到达。

## R0177：当前预算与 loaded floor 的真实验证

`machine_id: desktop-3fevhd2-1c74096080`，Root 的 R0177 a07 查询为
`native:3 / public revision4 / native revision3 / date53146632`，运行角色31254，
PID7240/create134365679117288462/connection generation1，episode
`native-31254-00b796ef873c`。原010 envelope的 `army_history_evidence` 引用
完整 Driver result；本lane没有读取/复制/重新hash它的30MB原件。

integration 将原 leaf 原样保存于
[CURRENT.actual-a01.json](acceptance/2026-10-16-episode04-r0177-a07-current-literals/CURRENT.actual-a01.json)
（214670B，SHA256 `a13d858d529b591d19db182b1573212bab74935c1f85039aa78591011301f4c2`）及
[CONTEXT.actual-a01.json](acceptance/2026-10-16-episode04-r0177-a07-current-literals/CONTEXT.actual-a01.json)
（64049B，SHA256 `ba556ebde9639f7cc7c0b936928d312b440f47862156daab0950b42e93d80860`）。
本lane在 `2026-10-15T20:14:14Z` 已核实际机器、两精确pin，并直接用现有
county/movement/loss-application strict normalizer 消费，没有手抄字段伪装wire。
`ACTUAL-CURRENT-CONSUMER.actual.json` 保存具体 JSON pointer、原件pin和输出。

| Army/public →native | whole | native B | F / M / N | base floor / nonzero floor / raw1D4 |
|---|---:|---:|---|---|
|18→18|1195|100|5000 / 100000 / 100|10000 / 0 / 0|
|93→85|250|100|5000 / 100000 / 100|10000 / 0 / 0|
|94→86|250|100|5000 / 100000 / 100|10000 / 0 / 0|
|95→87|250|100|5000 / 100000 / 100|10000 / 0 / 0|

实际 loaded floor 是 **10000和0**，不能沿用未观测时的0/100000假设。
本场 raw1D4=0，源码因此排除 zero-predicate true 路径，第二floor不被该次
M getter分支消费；M100000严格高于base10000，可按已闭公式逆解本次普通
ArmyProperty1A7聚合值为0。后两项是标明来源的推导，不冒充额外 getter 原始观察。

四军 condition 都是 `unavailable/no_stored_route`，其 actor/target/mode/passes
仍为null；这是 producer 对完整空route的实际分支，不是false condition或0目标。
解释器四项均返回 `no_current_first_edge_to_assess`。native预算100保持可用，
没有声称发生了县到达、writer或physical扣兵。Root 后来的preview/Move属于
另一frame，不能反写此010 leaf。

短口播：“当前四军的原生县预算都是100。1195人的军队也不是按5%就只算59；
实际读取的两下限是10000和0，原始Army1D4为0，当前倍率100000。当前没有路线
第一站，这些是当前预算和分支解释，不是已发生的县扣兵。”

## R0177 post-Move93：有路线时预算100仍不等于入境扣100

Root 随后真实 Move93→2624；本lane只消费其已保存的
[POSTMOVE93.actual-a01.json](acceptance/2026-10-16-episode04-r0177-a07-current-literals/POSTMOVE93.actual-a01.json)
（5731B，SHA256 `b4476af4356ebd95f34661f53b941c68cb9f4755a3b595d639a0862e283c351d`）。
来源是具名7,611,522B Driver result 的窄原leaf摘录；本lane未读/复制/hash该大原件。
其 machine、PID/create/generation/episode与上文一致，实际frame改为
`native:4 / public revision5 / native revision4 / paused date53146632`。
snapshot和query这三项逐一相等后，才把原 snapshot Army context送入解释器。
同时精确核验原 runtime/actor proof 的6123B及SHA256
`48d5773f8bd621c86a38e3f636d1a9c6182aedba4e4fdb9dedff58b2692b3b52`。

实际 Army93/native85 位于2619，完整route为 `[2624]`。whole250、B100、
F5000、M100000、N100和floor10000/0/raw1D4=0继续可用；county condition现在
**available/false**，actual actor31254、source2619、target2624、mode1。
因此即使部分早期到达prefix不在该紧凑包内，已知false也足以排除当前held-input
条件下这条边的正县预算，结果为 `no_positive_county_budget_on_this_local_branch`。
不把缺失prefix填0；不因预算B100就要求改道，也不授整条路线安全。

movement原leaf的累计weight是0，edge cost4200000、current rate525000、
normalized progress0、remaining800000，原 committed timeline预计日期53146824。
这些都没有证明已经到达；特别不能把 edge cost4200000抄成已累计weight。
`ACTUAL-POSTMOVE93-CONSUMER.actual.json` 保存消费、原值和精确来源。

短口播：“Army93现在从2619走向2624。当前原生整军县预算是100，但同帧县进入
条件为false，所以在这些输入保持到入境时，这条第一站不选择县预算。还没有到县，
也不能称实际扣兵为零；补给、围城等损耗仍需分开观察。”
