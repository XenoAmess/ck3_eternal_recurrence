# G2 campaign certificate provider 施工审计

状态：**NO-GO / no implementation / no readiness change**。

本轮只回答一个问题：现有生产者和 owner 输入是否已经足以实现
`raiktor-campaign-dominance-certificate-v1` provider，并直接解除 Raiktor
white-peace comparison 的 campaign 输入缺口。结论是否定的；因此本轮不新增 provider、
schema、fixture 或默认值，也不改变任何 policy/action readiness。

## 已存在的消费合同

`raiktor_continue_vs_surrender_policy.py` 已冻结
`raiktor-campaign-dominance-certificate-v1` 的严格 normalizer。现有三方策略与
white-peace comparison provider 都只消费该证书；仓库中没有生成该证书的模块、命令、
live runner 或 production artifact。

证书要求同一 paused frame 内的完整 campaign outcome distribution、所有合理 encounter、
reserve/补员/围城/增援 ETA、finance endurance、model/tail risk、claims 与六域估值、
continue/surrender utility interval 和 hard-budget breach。严格消费者存在，不等于这些事实
已经有生产者。

## 为什么当前不能实现

### 1. v3 combat input 不是 campaign forecast

`combat_simulation_inputs_v3_production_available.json` 是单元测试 fixture；其
`request_id` 以 `fixture-` 开头，scenario 是
`explicit_hypothetical_contact`，participant policy 明确固定接触时双方且不计增援。
即使该 fixture 的 132 个 phase-event state ref 可读，其 completeness 仍明确为：

```text
input_observation_ready = true
monte_carlo_ready = false
```

它还列出 damage-to-casualty allocation、pursuit、battle-end/retreat transition 与
phase-event RNG/effects 等缺口。该输入不能提供当前 Raiktor 战局的 outcome distribution，
更不能覆盖所有合理 encounter、路线、补员、围城和财政。

### 2. 现有 100,000 次输出仍是 research-only

`rev4_phase_events_disabled_n100000_seed_c0319a06.json` 的四个 fixed-contact 场景各有
100,000 次样本，但 artifact 自身固定声明：

```text
model_fidelity = research-only-bounded-core
phase_events_disabled = true
planner_usable = false
active_attack_allowed = false
```

其假设还排除 voluntary/partial retreat。样本量不会提升模型证据等级；这些 wins/losses
不能改名为当前 campaign 胜率，也不能生成 production certificate。

### 3. encounter 决策合同也保持关闭

现有 `combat-entry-eu-v1` 合同要求七项 fidelity gate、六项 campaign feedback 和一组
显式 utility coefficients，并固定 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED = False`。
`combat_core.py` 不读 CK3、paused snapshot 或 planner/MCP。现有代码没有从 encounter
research output 推导 campaign outcome 的 production 路径。

### 4. owner 权威输入尚不完整

owner budget profile provider 已能严格读取 owner-authored source，但仓库没有
owner-approved profile instance。该 profile 冻结的是退出 hard budget；它也不是
combat/campaign utility coefficient 的默认来源。当前不得从玩家余额、战分、研究 fixture
或历史行为猜测 owner 偏好。

## 施工重开条件

只有以下生产入口都有明确来源后，才重开 campaign provider 实现：

1. 当前同帧战局观测能枚举合理 encounter，并读取双方现役兵、reserve、补员、路线、
   围城/目标与增援 ETA、补给/损耗和 finance endurance；
2. encounter forecast 的 exact-build transition fidelity 与 original trace 闭合，实际输出
   明确为 `planner_usable=true`，或者另有等价、可核验的 production forecast producer；
3. claims 与六域 valuation、campaign feedback 和 utility coefficients 有 owner-approved
   权威来源，而非代码默认值或测试 fixture；
4. 上述生产者能绑定同一 connection/episode/PID/paused frame、WarID、candidate 与输入
   SHA-256，并明确模型风险、tail risk 和缺失域；
5. 至少一个真实 paused artifact 能覆盖 Raiktor 当前战局，且消费者保持 fail-closed。

届时应复用已经冻结的 `raiktor-campaign-dominance-certificate-v1`，除非真实生产者证明
现有字段不足；在此之前不再增加一层只包装 synthetic/external JSON 的 provider。

## 当前最小有效后续

本审计不改变以下真实边界：campaign certificate unavailable、white-peace comparison
unavailable、`production_recommendation_ready=false`、`action_ready=false`、`GEN-034`
unresolved。当前已有更直接价值的入口是：在排他 CK3 槽可用时执行已经 static-ready 的
source-specific same-lifecycle adapter，取得现有 provider 所需的真实 source/current/action/
postwar artifact；以及由 owner 提供经批准的 profile/valuation source。二者都不能由本轮
离线静态代码代替。

## 证据入口

- [combat-simulator-core.md](combat-simulator-core.md)：exact build、transition fidelity 与
  `planner_usable=false` 的权威边界；
- [combat-simulation-inputs.md](combat-simulation-inputs.md)：v3 只读输入合同；
- [player-war-exit-policy.md](player-war-exit-policy.md)：退出策略所需 campaign forecast；
- [raiktor-three-way-exit-policy.md](raiktor-three-way-exit-policy.md)：现有 certificate
  consumer 与三方 readiness；
- [g2-owner-budget-profile-provider-2026-09-06.md](g2-owner-budget-profile-provider-2026-09-06.md)：
  owner source 审批边界。

