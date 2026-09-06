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
兼容 policy 输出、完整/缺项 file manifest、哈希漂移与输出覆盖保护；normal 与 `python -O` 均通过。
相关 owner/white-peace/three-way/source-specific intake 回归也在同一矩阵中复跑。本包没有 CK3 进程、
MCP query、mutation 或 readiness promotion。
