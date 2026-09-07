# G2 Raiktor 三方退出统一 intake

状态：**static-ready / no launch / production inputs pending**。

## 本次闭合内容

现有 owner-budget provider、white-peace comparison provider 与三方退出策略此前只有各自入口，
完整拼接只存在于测试代码。`raiktor_three_way_exit_intake.py` 现在提供单一、纯离线的
fail-closed 合取入口：

1. 只从显式路径读取 owner-authored budget source，不内置或推断阈值；
2. 把 owner profile、campaign certificate、同帧 white-peace terms observation 与 owner utility
   evaluation 交给既有 white-peace provider；
3. 只把 provider 实际发布的 comparison certificate 交给既有三方策略；
4. 在一个结果里保留 owner、white-peace 与 policy 的全部 typed blocker；
5. 无论输入是否完整，都固定保持 `production_recommendation_ready=false`、`action_ready=false`、
   `action_literal=null`。

这使未来 source-specific live report 和其它真实 provider 输出有一个不会绕过现有 SHA/frame/owner
合同的消费入口。它不新增 campaign producer，不把 synthetic fixture 包装成 production evidence，
也不查询、启动或修改 CK3。

现有 `prepare_g2_source_specific_comparison_intake.py` 已改为经过这条统一入口：验证后的
`observed_surrender_outcome` 先进入 intake，再从 `assessment` 取得原三方 policy 结果；输出同时保留
`three_way_intake_result` 与兼容字段 `three_way_policy_result`。因此未来真实 lifecycle 后处理不再需要
调用方手工拆接 provider，同时仍一次性列出 campaign、owner 与 white-peace 缺项。

历史 outcome 是可选的校准证据，不是三方 pre-action comparison 的必要输入。未提供它时，intake
继续在 `inputs` 中如实标记 `observed_surrender_outcome_supplied=false`，但不再把
`observed_surrender_outcome_unavailable` 混入决策 blocker；显式提供却不合格时仍由既有严格 normalizer
拒绝或报告 source-attribution blocker。

## Hash-bound 文件入口

`prepare_g2_three_way_exit_file_intake.py` 将同一合取开放为离线 manifest runner。manifest 对
candidate、surrender terms、campaign certificate、owner budget source、white-peace terms、utility
evaluation 和可选历史 outcome 分别绑定路径与精确 SHA-256；相对路径只相对于 manifest 所在目录解析。
文件缺省必须显式为 `null`，这会得到正常的 `evidence_required` 结果，而不是加载默认 fixture。

成功处理会原子写入一份结果 JSON，保留 manifest/input 路径与哈希、完整 intake 结果以及固定的
`ck3_started_or_attached=false`、`bridge_queried=false`、`mutation_commands=[]`、
`action_ready=false` 边界。manifest/输入哈希漂移、字段集合漂移、坏 UTF-8/JSON 或覆盖已有输出都会
直接失败。即使完整 synthetic manifest 得到静态赢家，这个 runner 也不会升级 production readiness。

`observed_surrender_outcome` 文件项现在可直接绑定完整的
`xar.ck3.g2_source_specific_comparison_intake.v1` 后处理 envelope，无需调用方手工抽字段。runner 会先
验证 envelope 的完整字段集、source report SHA、三项 remaining provider、source-specific readiness、
全部 false 的 decision/action/GEN-034 边界，以及嵌套 intake/policy/projection 一致性，再提取已验证的
outcome。任何 readiness 过报或嵌套结果漂移都会使整个文件 intake 失败；原始
`raiktor-observed-surrender-outcome-v1` 对象仍保持兼容。

## 当前结果

仓库仍没有 owner-approved budget source、production campaign certificate、同帧 Raiktor
white-peace terms observation 或 owner utility evaluation。对当前输入调用统一 intake 会保持
`status=evidence_required`，并明确列出这些缺项。完整 synthetic 测试可以得到
`static_recommendation_available`，但该结果仍没有 production/action 权限。

因此 G2 的 source-specific live adapter、三方 production recommendation、typed submit、
postcondition 与 `GEN-034` 均没有因本包升级。下一条有实际价值的 live 入口仍是排他 CK3 槽中的
source-specific same-lifecycle adapter；非 CK3 侧等待 owner source 与真实 production producer。

## 离线验收

focused tests 覆盖缺输入、完整绑定、draft owner、stale utility SHA、source-specific 后处理接线、
兼容 policy 输出、完整/缺项 file manifest、哈希漂移、输出覆盖保护、完整 source-specific envelope
直连与 envelope readiness 过报拒绝；normal 与 `python -O` 均通过。
相关 owner/white-peace/three-way/source-specific intake 回归也在同一矩阵中复跑。本包没有 CK3 进程、
MCP query、mutation 或 readiness promotion。

已有 R3 generic postwar receipt 的离线 adapter 也已改走同一统一入口，并在输出中新增完整
`three_way_intake_result`、保留 `three_way_policy_result` 兼容字段。R3 的 source attribution 仍为 RED，
因此该接线只统一 typed blocker 与 provider 边界，不改变任何 production/action readiness。

hash-bound 文件入口现在也可直接绑定这份完整 R3 generic postwar envelope，无需调用方手工抽取
`observed_surrender_outcome`。入口验证 receipt/outer checks、嵌套 intake/policy 一致性、source report SHA
绑定、remaining provider 和全部 false 的 readiness 边界后才提取 projection；提取后的 generic outcome 仍返回
`source_specific_war_loss_attribution_unavailable`，不会被提升为 source-specific loss。

统一入口现也调用既有 `raiktor-surrender-execution-policy-v1`，把三方 assessment、同一 candidate 与 six-domain
surrender terms 投影为独立 `surrender_execution_readiness`。可选的 aggregate session binding 只能关闭
`six_domain_session_provenance_not_bound`；typed submit、pending/cooldown、persisted expiry、source-specific cleanup
与八项 action-boundary postcondition 仍由原执行合同保持关闭。candidate/terms 未提供的历史 outcome-only adapter 返回
`surrender_execution_readiness=null`，不会伪造执行输入；顶层 `action_ready=false/action_literal=null` 恒不变。

hash-bound runner 保留原 `raiktor-three-way-exit-file-intake-manifest-v1`，并新增显式 v2 合同；v2 只增加
`surrender_aggregate_session_binding` 路径与 SHA-256 绑定。完整 fixture 证明该输入可令 execution projection 的
`session_provenance_ready=true`，但 `action.ready=false`、`postcondition.ready=false` 与 literal `null` 不变。
v1 manifest 的输入集合和行为保持兼容；声明 v2 却缺少 session input 会直接作为 manifest shape RED。
