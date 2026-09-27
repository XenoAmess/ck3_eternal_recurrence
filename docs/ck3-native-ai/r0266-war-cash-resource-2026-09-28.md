# R0266：在建造与现役战争之间共用现金

R0266 的 `H2825/raw53217624` 是一个已暂停的同帧观察：`snapshot_id=native:3`、公开修订 `4`、原生修订 `3`、`episode_run_id=native-29829-2bc2d599f7f9`、玩家 `29829`、战争 `16777231`。建造候选 `farm_estates_01` 的原生价格为 `18,000,000` 个 Q100000 金币原始单位，即 180 金；玩家库存 `111,861,020`，即 1118.61020 金。现有建造政策额外要求保留 `20,000,000`，即 200 金。三者只说明**尚未计算战争负担的余额**为 `111,861,020 - 18,000,000 - 20,000,000 = 73,861,020`，即 738.61020 金；不能据此批准建造。`+70` 百分之一金币/月是建筑定义的潜在收入，尚非实际入账。

## 已有字段与缺口

| 项目 | H2825 状态 | 来源和含义 |
| --- | --- | --- |
| 现有国库 | `111,861,020`，Q100000 | R0266 同帧原生建造观察的 `candidate.gold_before_raw`，与快照的 `played_character_gold.raw` 对接时须核对一致。 |
| 活跃战争 | WarID `16777231`，现役玩家军队 1 支 | R0266 同帧建造观察及战争计划；军队数量本身不是维护费。 |
| 已提交、尚待执行的战争现金 | `null` | 缺少同帧战争待办动作账本及费用读回；`null` 不代表无待办。 |
| 本次战争动作的即时费用 | `null` | 缺少所选战争动作的原生费用或能证明免费之证据。只读查询可以是 0，但必须与同一计划动作及来源绑定。 |
| 战争政策最低现金保留 | `null` | 目前没有适用于该战争的已发布保留金政策。建造自身 200 金保留额不得冒充战争政策。 |
| 未来战争现金上界与风险预算 | `null` | 缺少带期限的费用上界来源和政策风险额；`player_monthly_gold_income` 是当前净收入观察，不能倒推出总维护费，也不能证明未来费用上界。 |

`H2908/raw53217816` 是后来的另一帧，只能作后续检查点，不能填补 H2825 的同帧现金字段。以上数据来自 [R0266 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-R0266-JOINT-CASH-20260928.json)和其[证据摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0266-JOINT-CASH-20260928.construction-frame.json)。本机桌面截图仍陈旧；此处没有新的实机读回。

## 已落入运行时的接口

`m5_war_cash_resource_v1.observe_active_war_cash_resource_v1` 产出只读 `xar.ck3.m5-active-war-cash-resource.v1` 收据。输入必须包括完整 `source_frame`（玩家、`snapshot_id`、公开/原生修订、日期、episode）和 WarID。五项金额各使用 `{raw, scale:100000, source}`：已提交战争现金、本次动作即时费用、指定期限内未来费用上界、该期限的额外风险预算、战争政策最低保留额。未来上界还要声明 `horizon_days` 和文字假设。未知输入以 `null` 和机器可读 `missing` 原因输出；显式的 0 同样需要来源。收据始终 `formal_action_ready:false`。

全项齐备时，三种现金用途分别进入**现有** M5 资源合同：

1. `existing_shared_gold_commitment_raw = pending_war_cash_raw`，计入 `existing_commitments.gold_raw` 一次；先前其他领域的承诺仍应叠加。
2. `immediate_war_action_cost_raw` 与战争提案 `gold_cost_raw` 相同，仅在选择该战争动作时由 M5 预留。
3. `joint_gold_reserve_raw = future_war_cost_upper_raw + future_risk_budget_raw + policy_minimum_gold_reserve_raw`，作为所有候选共享的 `gold_reserve_raw` 下界；即使战争动作不是本次候选，建造也不能挪用这笔保留金。

`active_defensive_war_continuation_proposal` 核对战争提案的费用与收据相同，并将收据放入提案证据。`collect_m5_formal_proposals` 在有一个现役战争时核对收据、既有承诺与共享保留额；缺失、不完整、跨帧、跨 WarID 或预算遗漏都会拒绝这次联合比较。现有 `M5FrameDispatcher` 仍负责单帧唯一分析预留。该预留只存在于这一帧的 dispatcher 实例；状态改变时需创建新实例、重新观察和预留，不能沿用旧帧。这里没有第二个建造 consumer，也没有开启 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED`。多个同时进行的战争尚无合并合同，明确拒绝，避免只为其中一场战争保留现金。

目前没有能为 H2825 填入未来费用上界、待办现金或战争最低保留额的同帧原生字段，因此 H2825 对应收据是 `incomplete`，联合建造可负担性仍是 `unassessed`。下一步需在受管实机恢复后读取战争待办费用与原生军队维护费/补员费用的同帧来源，并给出一个明确期限及风险预算；有界输入齐备后再由非战争执行者做受影响的建造候选集成及正式动作/回执验收。
