# R10 A：将路线与补给压力接入实际决策

新增[小型适配器](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_a_route_inputs.py)直接消费已准入的 `strategy_a` state、现有 endpoint pin 和同帧 native preview，不新增公共 MCP、顶层 schema 或假想军队。它保留 A 的冻结整军直达策略；拆军属于另一策略选择，不能在已看结果后悄悄更改 A。

```python
from strategy_a_route_inputs import next_decision
decision = next_decision(state, evidence, fresh_preview_pin)
```

返回沿用 `proposed_call` 的现有调用形状：尚未下达时保留原 A Move；途中缺新 preview 时可准备原 `ck3_execute_step(preview-move-army-…-to-…)`；已到达/90日或需要普通战斗等规划时不发新命令。附加供给字段缺失不会否定合法 Move，也不会把 unknown 当零。消费者本身永不 dispatch。调用方继续使用既有事件/战争/实际后态流程。

`current_aggregate_pressure_suggests_review` 只回答**当前 native aggregate usage 是否大于当前 native limit**。true 可触发对现状的审视；false 只排除这个当前超限事实，不能排除未来县进入、围城、饥饿等损耗。它不推荐拆几军、每军几人或保证省兵。当前人数/库存、原 cohort、完整 DATA、当前月贡献和当前 attrition 与未来结果分列，完整 ABC/费用资格仍归公用比较器。

| 输入 | 可直接用于当前决策 | 必须保持 unknown |
| --- | --- | --- |
| accepted/available、实际 Army/owner/origin、完整路径及 queried frame | 当前可达目标和合法 Move，保留公开 CUnit 与 native CArmy 的区别 | 实际 Move/到场、整段路径费用和地形效果 |
| `province_supply.current` 的 scale1 native limit/usage | 当前 owner/统帅上下文下的聚合占用比较；合法0与 INT32_MAX 保留 | 单军总人数不是 supply-eligible 聚合占用的替代值 |
| `province_supply.target` | **当前帧**目标省 native usage/limit；一个 row 缺失时另一个可单独使用 | target usage 不含未来入军；到场后的占用、完整 rate、库存和恢复日期 |
| 已下达 route/target | 当前排队路径，与重新 preview 的候选路径分开 | 路线列表中的中间省不能当实际已途经；不从省ID推海陆/地形 |
| 独立 snapshot 的 current Province | 实际在该省被观察；保留日期、endpoint pin 与 frame | 每日采样跨过的中间省不能追认；当前位置变化不能归因县扣兵 |
| 当前 attrition=0 / rate<0 | 该 Army 的当前 getter 值，可提示继续观察库存压力 | 下一 callback、未来补员/维护实付和最终损失；不能用率×日数补齐 |

现有可选 `captured_target_land_supply_inputs_v1` 还提供当前目标 resupply predicate、局部 component 和 loaded gain；`current_first_route_target_supply_contributors_v1` 可保留已下达首边目标的原始贡献者。这些各有既有 normalizer/readiness 合同，本小适配器不重算或重复发布它们。当前目标 operands 可知不等于未来完整 rate、真实到场占用或补员结果；需要时调用方沿原字段独立使用。

最小反例：Army 仅100人，current native usage=6000、limit=4000，则当前聚合超限2000。把这100人分成两支50人，不能从“两支各小于4000”推出省内占用变成50或已经避损。native usage统计当前同 owner/共同战争同侧的合格兵团兵数，而非仅所选 Army 的公开总数；同省拆军也不自动把其他贡献者排除。另一反例是目标 current usage=0、limit=3000：它没有把尚在别处的入军加入，不能写成到场后肯定 underlimit。这两个例子是显式 synthetic 检查，不是本场实测数字。

适配器另保留 `initial_preview_route`、`queued_route`、`fresh_preview_route` 和 `actual_observed_on_initial_route`。例如初始路线 `[20,30]`、下一次独立观察已在30，20仍列为 `not_independently_observed_province_ids`；不会因到终点就补造20的中途读数。

源码基线 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。依据是 `ck3_12002_adapter.cpp:313` 的 `.4` preview复用、`ck3_12002_military.cpp:353` 的合法性/完整路径、`native_driver.py:14400` 的同帧绑定、`army_strength_v1_serializer.hpp:1297` 的当前月贡献/attrition数值及 `:1602` 的 province_supply 真实 wire。省级usage含义沿用[既有专题](province-supply-limit-native-usage-preview-12003.md)；其 `.3` 实例只保留原版本资格，不能授新 `.4` T0。县损耗及 residual 的实际归因仍见[独立R04专题](episode04-county-entry-loss-12004.md)，本模块不重做其 source 分支或乘法。

本包只执行 Python 离线反例，未读取 EXE、save/raw 或调用 SDK/game/desktop。`machine_id: desktop-3fevhd2-1c74096080`；准确时间、候选字节和命令见[回执](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/validation/strategy-a-route-inputs.actual.json)。`open_kaishek: not-applicable`，只消费导出JSON，无 CK3 script/IR 语义。测试 PASS 不授实际新 T0、完整路径损耗、维护费/补员资格、游戏日、研究卡或影片完成信用。


## 当前钱包、首次抵达和其他军队：同一决策入口的最小补齐

`next_decision` 继续使用原签名、已准入的 state 和精确 endpoint pins，另把已有
证据里的 `account_observation`、`arrival_observation` 交给调用方，不增加公共
schema、付费探针或 runner。当前供给量仍在 `observed_current.stock_raw`，其
容量、当前月贡献、当前 attrition 也保持原值和原单位。月贡献不能乘旅行天数
外推库存，库存恢复不能冒充补员。

`account_observation` 的 T0/current player wallet 来自两个实际 endpoint 的
`played_character_gold.raw`；其差只叫 `unattributed_wallet_net_raw`。例如期间
进账12、实付3，钱包净增9；9既不是免费，也不能改名为费用−9。尚未归因的
登船、维护、其他收入与费用各为null。金额0只可能来自该字段自己的合格实付
证据，不能由当前月维护显示、generic wallet callerPC、空支付记录或钱包净差
推出。已有 source-qualified boarding writer→gateway→transition→natural-return
链可以支撑该窗口实付（`war_payment_observations_v1.expected_debits`），但它
仍需匹配本臂自己的同账户/区间及selected Army；旧R0173三金币不进入新A账。
费用比较是否预注册由 `fee_comparison_requested` 保留；本适配器不授R07/R08
资格、不改变计划，也不会因费用unknown取消当前合法Move。

`arrival_observation.first_arrival_actual` 保留第一次到场的完整实际库存/队列/
钱包/日期；`current_actual` 是本次最新endpoint，允许在预注册后续政策下不同。
它们不能互相覆盖。首次抵达区间沿现有逐日scan，预注册报告日只返回本臂已有
endpoint；共同日期表仍null，D90必须真实到90日且预注册。到场时不自动续跑。
例如第2日到场库存10、第3日库存20，抵达列仍是10，不能用第3日替换或把两者
当共同日期比较。独立post阶段复读同日实际到场仍由既有stages/reader核验。

`other_observed_player_armies` 仅保留同一snapshot里其他玩家军队的位置、状态
和combat/retreat标记。94/95在别处参战不是selected93合法行军的自动硬拒绝；
它们的经济影响也未因此被排除。`economic_isolation_from_other_armies_proved`
固定false，所有相关成本保持unknown；要解释同一角色的钱包/维护，必须独立
取得能分离selected93与其他军队的应用账、收入和其他支出。世界事件、接敌与
本臂测量资格沿原合同分别记录，不能为了宣称经济纯净冻结全世界。

### R0177准备S0到正式A的最短路径

本次离线读取的来源机器为 `desktop-3fevhd2-1c74096080`，source
`d9322bcfb3e17a3fe78607cea777bbfaf7be0a11`。Root的正常准备保存回执记录
checkpoint `e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67`、
71,631,396 bytes、raw53146848，Army93在2624驻定，CArmy85，250/250、4团/
4 DATA、stock100（raw10000000）。Root提供的统帅34232仍须在正式endpoint
绑定自己的同帧source；这些是源会话事实，不能预填未来freshload数字。此处
没有读取、复制或重新hash存档，也不把准备行军当正式A或R10完成。

最小缺口和顺序如下；B/C可以独立准备，不阻止先取得A自身正式输入：

1. 将受保护正常S0的完整保存回执、origin/build/source/DLL pin和实际baseline
   endpoint接入已有PLAN。目标目前未冻结；从共同策略目标取得具名Province，
   同帧普通snapshot→单Army `ordinary_core_v1` complete Driver reference→
   commander/loaded features bound source→native direct preview。先冻结goal、
   arrival states、原始全cohort、报告日、事件/墙钟/90日及到场后政策。已有
   `PLAN.template.UNBOUND.json` 的null不能由旧London或旧角色数字代填。
2. A独立正常freshload这个精确SHA；取得自己的machine/PID/create-time/gen/
   episode/actor与T0完整观测及fresh preview，调用已有`strategy_a.admit`。
   当前保护S0是准备输入，不是这次独立冷载本身。B/C正式比较也要各自freshload
   同一SHA并核baseline；不能沿用R0177行军前2619帧作新T0。
3. 通过既有Root relay分阶段执行一次typed Move，独立post观察实际queued route；
   后续每个实际自然日提供exact clock+同帧完整endpoint给`strategy_a.update`，
   首次抵达立即保存actual，再独立同日post。当前R10 reader/stages固定speed5
   date-only/a-0；R0177准备helper的speed3 watched日志不能直接贴入该clock schema。
   复用现有R10阶段，不重造runner、不把准备day计入正式D1。
4. 用本入口读取当前stock/压力、账户净差、首次到场post和世界上下文。若预注册
   `compare_fees=true`，完整费用表还缺本臂合格R07/R08与应用账/钱包对账；保持
   unknown，不事后关掉费用列。各臂抵达表和共同自然日报告分别交给比较器。

这次增量只增加离线决策消费与合成反例，不授新实机、通用完整路线费用、影片
或正式R10信用；原07:45Z有限Root运行截止没有成为永久公共ready条件。

上述S0元数据的原观察时间为2026-10-15T20:25:31.384013Z，证据是Root现有
`normalprepare93-stages/newstationary-commonS0.actual.json`，本次只读该小回执。
它引用的selected93完整结果为7,865,022 bytes；四军全history的30MB结果不能
直接送入本比较器的单文件16MiB上限。完整scope不是全世界scope，正式A沿用
单Army `ordinary_core_v1` 与其完整Driver原件，不拿MCP摘要凑全体DATA。
实际日数/目标未定时不承诺90日会装进512MiB；现有A阶段每日前后各取一次
endpoint，Root须按实际单军query大小和最快正式到场pilot核峰值，保留容量
守卫的真实STOP。准备行军到场不替代正式时长、全90日容量或墙钟资格。
