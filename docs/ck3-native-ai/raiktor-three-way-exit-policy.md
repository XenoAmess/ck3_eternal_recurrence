# Raiktor 三方退出决策静态核心

状态：**static/fixture-ready，not live，not action-ready**。本专题只记录
`raiktor-three-way-exit-policy-v1` 的输入、选择规则和当前真实 RED；它不修改
native bridge、MCP、planner 或 CK3 写口，也不关闭 `GEN-034`。

## 目标与边界

当前 G2 冻结点中，玩家 CharacterID `29829` 是 WarID `50331699` 的 primary
attacker，CB 为 `raiktor_claim_cb`，战分 `-50`、持续 1281 日。原生查询已经证明
surrender 合法且会被接受，但这些事实只建立候选，不能证明“现在投降最好”。

新核心把已有两项合同组合起来：

1. `raiktor-surrender-six-domain-v1`：投降 claims base 与六个 dynamic domain；
2. `raiktor-continue-vs-surrender-policy-v1`：continue 与 surrender 的保守 pairwise
   比较。

它再要求显式 owner budget 和 white-peace comparison，才能比较 continue、white
peace、surrender。输出最多是静态 `recommended_outcome`；始终保持
`action_ready=false / action_literal=null / automatic_surrender_ready=false`。pending、
cooldown、唯一 submit、ACK 后状态与六域 action-boundary postcondition 都不在本核心
内，不能由 fixture GREEN 推导为已完成。

还有一个必须保留的继承边界：当前 six-domain v1 只携带 revision/date/WarID/CB/角色
身份，没有 `connection_id / episode_id / ck3_pid`。campaign 与 white-peace 证书会绑定
完整 frame，但这不能反向证明 six-domain child 的 session provenance。因而本静态核心
即使收到标成 production 的 synthetic/provider flags，也固定保持
`production_recommendation_ready=false`；以后必须先在 public aggregate wire 补齐并实机
验证这三个字段，才能由上层 production gate 升级。

## 三类新增输入

### Campaign dominance certificate

沿用 pairwise 核心的 `raiktor-campaign-dominance-certificate-v1`。证书必须绑定同一
paused frame、candidate SHA-256、六域 terms SHA-256 与 owner pairwise limits
SHA-256，并完整声明：

- campaign outcome distribution 与所有合理 encounter；
- 当前可动员兵、reserve、补员、围城与增援 ETA；
- finance endurance；
- model risk、tail risk、sunk-cost exclusion；
- claims base 和六域的 valuation；
- continue/surrender 的保守 utility interval 与 hard-budget breaches。

当前仓库没有生产该证书的 provider。战分和战争时长只是必须 hash-bind 的模型输入，
不是替代证书的投降阈值。

### Owner budget profile

`raiktor-owner-budget-profile-v1` 显式包含 profile identity、provenance、source artifact
SHA-256 与 production eligibility。它复用 pairwise limits，并另外冻结 white peace
允许的 gold transfer、prestige loss、removed claims、favor hook 与 truce days。外层
profile identity 必须与内嵌 pairwise limits 完全一致。

当前没有 owner-approved profile provider，因此真实 checkpoint 返回
`owner_budget_profile_unavailable`。测试里的数值全部标为 synthetic/do-not-ship；核心
没有默认阈值，也不会从玩家余额、战分或历史行为猜 owner 偏好。

### White-peace comparison certificate

`raiktor-white-peace-comparison-certificate-v1` 必须同时绑定 candidate、surrender
terms、campaign certificate 与 owner budget 的 SHA-256，并在相同 paused frame 提供：

- context、native validator、available 与 typed final recipient response；
- declared-target claim retention 与 title-holder change count；
- actual primary gold transfer、attacker prestige delta、truce duration；
- prisoner-release pairs、favor-hook application 与 hostage variant；
- 同一 `owner_utility_q100000` 单位的 conservative white-peace interval；
- completeness、model risk、hard-budget breach 与 producer provenance。

只读到“白和按钮可点”或 acceptance raw 为正不够；final typed response 和实际条款仍须
由 provider 发布。当前这个 provider 也不存在，所以真实 checkpoint 返回
`white_peace_comparison_certificate_unavailable`。

## 选择规则

先剔除未通过 candidate-specific legality / hard budget 的结果。对剩余候选，仅当某一
候选的 utility lower bound 至少高于所有其它候选的 utility upper bound 加上 owner
`minimum_switch_margin_raw` 时，才发布该唯一 `recommended_outcome`。否则返回
`three_way_underdetermined`。

这个规则允许三种静态结果都被独立覆盖：

- safe objective 已证明、continue 在 tail/hard budget 内且稳健占优：`continue`；
- white peace 的完整条款在 budget 内且稳健占优：`white_peace`；
- 无 safe objective、无及时可信援军、continue tail budget 已越界，且 surrender
  条款在 budget 内并稳健占优：`surrender`。

缺 provider 是 `evidence_required`，不是 underdetermined。提供了证书但区间重叠才是
`three_way_underdetermined`。这样可以区分“还没观测”与“已经观测但没有稳健赢家”。

## 不得猜测的战争兵力

Raiktor 脚本最初生成六支、每支 500 人的事件军，只证明 authored source count。
`3000` 不是 measured pre-soldiers，也不是 current soldiers 或 proven loss。现有 generic
war-bound current 只能作为 conservative exposure；没有 source attribution / pre snapshot /
action-bound loss provider 时，这三项继续为 false。新核心没有 `3000` 数值字段，也不因
缺失这些字段把它填入 campaign certificate。

## 当前真实 readiness

当前冻结 checkpoint 的 typed RED 是：

- public same-frame six-domain aggregate 仍需由其它施工包完成实机闭环；truce 的
  `evaluated_days` leaf 已接入 terms/MCP public wire，但尚无 paused/live shape artifact；
- six-domain public aggregate 还必须补齐 connection/episode/PID session binding；
- `raiktor-campaign-dominance-certificate-provider-v1` unavailable；
- `raiktor-owner-budget-profile-provider-v1` unavailable；
- `raiktor-white-peace-comparison-provider-v1` unavailable。

所以当前仍是：

```text
recommended_outcome = null
production_recommendation_ready = false
full_exit_decision_ready = false
action_ready = false
action_literal = null
automatic_surrender_ready = false
GEN-034 = unresolved
```

后续最小路径是先补上述只读 provider、剩余 aggregate public wire，并完成 truce
`evaluated_days` 的 paused/live shape probe，再把静态 recommendation 接入 typed
termination submit gate；最后在一次 CK3 启动里完成双查询、唯一 submit、六域
postcondition、postwar checkpoint。不得用 OCR 或重复跑局替代缺失 provider。

## 离线验收

```powershell
$env:PYTHONPATH = "ck3_autonomous_player/src;ck3_autonomous_player/tests/unit"
py -m unittest ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_policy.py
py -O -m unittest ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_policy.py
```

测试覆盖三种稳健赢家、区间重叠、missing provider、stale hash、incomplete domain、owner
profile identity drift、white-peace budget breach、claim retention 未证明，以及所有 action/live
字段继续关闭。测试只使用 synthetic fixture，不是 CK3 paused artifact。
