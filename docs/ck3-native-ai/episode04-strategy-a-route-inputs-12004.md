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
