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

## 当前结果

仓库仍没有 owner-approved budget source、production campaign certificate、同帧 Raiktor
white-peace terms observation 或 owner utility evaluation。对当前输入调用统一 intake 会保持
`status=evidence_required`，并明确列出这些缺项。完整 synthetic 测试可以得到
`static_recommendation_available`，但该结果仍没有 production/action 权限。

因此 G2 的 source-specific live adapter、三方 production recommendation、typed submit、
postcondition 与 `GEN-034` 均没有因本包升级。下一条有实际价值的 live 入口仍是排他 CK3 槽中的
source-specific same-lifecycle adapter；非 CK3 侧等待 owner source 与真实 production producer。

## 离线验收

新增 4 项 focused tests，覆盖缺输入、完整绑定、draft owner 和 stale utility SHA；normal 与
`python -O` 均通过。相关 owner/white-peace/three-way/source-specific intake 回归也在同一矩阵中
复跑。本包没有 CK3 进程、MCP query、mutation 或 readiness promotion。
