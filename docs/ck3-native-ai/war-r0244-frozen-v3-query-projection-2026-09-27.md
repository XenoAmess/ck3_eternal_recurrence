# R0244 冻结失败帧的 v3 查询投影复核（2026-09-27）

本复核读取 [R0244 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0244-20260927.json)
和 Git 内 [正式失败报告](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0244-20260927.formal-report.json)，
后者 SHA-256 为 `07994F762425CCFF912BF697DCBF95BA1E00F374D646BE060748420526040E6F`。
没有启动 CK3，也没有使用原机存档或 DLL。报告在 blocked turn 保留了
路线与接触查询的**结果**，但未保留完整 transport 命令 envelope；
[回归测试](../../ck3_autonomous_player/tests/unit/test_r0244_frozen_v3_query_projection.py)
只根据报告里的已选步骤和返回值重构这两条 envelope，测试当前策略
的离线投影，**不等于原机重放**。

冻结帧是 Robert WarID `48`，episode `native-29829-2bc2d599f7f9`、
`native:3`、public/native revision `4/3`、date_raw `53154936`、
connection generation `1`。Army `16777237` 从 Province `2619`
沿 `[2624,2631,2630,2629,8753,2626,2627,2633,2634,2640]`
接近位于 `2640` 的敌军 `16777417`。路线最后进入边是 `2634→2640`；
同帧接触结果为 `one_day_contact_free=true`、`conflicts=[]`。
旧 blocked plan 位于 `native_war_general_battle_inputs_query`，
`selected_step=null`。当前策略在精确参数化 v3 capability 存在时，
从上述冻结形状得到只读命令：

```text
query-combat-simulation-inputs-v3-2640-2634-a-1-16777237-d-1-16777417
```

这条字面命令不需要出现在 `action_steps` 枚举中；但**只有当前 DLL
宣告并能执行该 capability**，生产路径才能发查询。driver 仍须在查询
前后验证暂停帧、encounter scope、版本和缓存身份；若返回 unavailable
或缺少兵团输入，不得把它当作零损失或可接触结论。本测试没有 v3
返回数据，因此没有运行整场预测、没有选一跳行军或产生游戏资源变化。

请求中的 EXE SHA 是请求方冻结的来源身份；正式失败报告自身
`identity.ck3_executable_sha256=null`，所以该报告不能独立证明当时
进程 EXE 字节。报告中的 bridge DLL SHA 与请求一致，checkpoint SHA
与请求一致。原 War48 save（SHA `3E6E66CED57EE8D13707259D9D9656AA54C24F782598C86B192958CCA0B5A734`）、
driver（配对索引 SHA `EF09027B2F8438F99446C82A3E870AF1547CE1D25214F671C59346E3AC17D495`）、
DLL（SHA `CE57BB7F67B3B6646796E9679B5D198557CE175C056000C8FE4DFCB940F2FB0C`）
仅有另一台机器的 `Z:` 历史路径，未转入本机。下一步真实验收仍需
单独转入并核对 save/driver/sidecars/DLL、做新 PID 的前后同帧查询，
验证实际 v3 状态和后续第一跳的独立动作/读回/下一 turn/恢复。

离线回归在普通与 `-O` Python 下各 1 项通过。此前四个 v3/策略/first-hop
模块在当前 master 下两种模式各 `50 passed, 46 subtests passed`；
这些结果只确认当前接口合同和冻结形状投影，不能填写 R0244 的原机
`verification=passed`。
