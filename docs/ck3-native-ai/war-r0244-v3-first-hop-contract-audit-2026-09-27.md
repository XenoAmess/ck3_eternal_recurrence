# R0244：v3 战斗输入与接触前一跳合同复核

本复核只读取 Git 中的 R0244 失败证据与当前代码，不启动 CK3，不重放另一台机器
上的 Robert War48 存档，也不把本机 War4 类比验收当成 War48 结果。

| 冻结输入 | SHA-256（本次逐文件回读） |
| --- | --- |
| [R0244 request](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0244-20260927.json) | `56CC01A3AFE7B49981893E21E121F933A4A249DDA0E875C67DA19F4253E3B035` |
| [正式失败报告](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0244-20260927.formal-report.json) | `07994F762425CCFF912BF697DCBF95BA1E00F374D646BE060748420526040E6F` |
| [operator 回执](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0244-20260927.operator-receipt.json) | `788F08A51C90F6A455739288D6732249DE57937FBC23C0DDA8DB355C62BB96C8` |
| [配对身份索引](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0244-20260927.pair-identity.json) | `9E7FB3DD88999C00E270EF82B607F73D0A998A5977E87D2029A8CEC02E43485E` |

原失败发生在 WarID `48`、玩家 ArmyID `16777237` 向 ProvinceID `2640`
接近敌方 ArmyID `16777417` 时。暂停帧为 `native:3`、public/native revision
`4/3`、date raw `53154936`。全路线 contact query 已在同一帧返回 available，
第一日 `one_day_contact_free=true`、`conflicts=[]`；当时 planner 在
`native_war_general_battle_inputs_query` 无可选 v3 查询字面动作而停止。
正式报告的 blocked turn 没有提交 gameplay action、日期没有推进，active event
与 pending character interaction 均为 `null`。这些是**历史失败观察**。

## 当前 master 的交接链

1. `strategy.py` 的 `_general_battle_forecast_ingress` 从当前敌军目标、原生路线最后一条进入边、
   玩家和防守方 ArmyID 构造**完整参数化**的
   `query-combat-simulation-inputs-v3` 字面命令。它检查 bridge capability，
   不要求驱动把所有参数组合列进 `action_steps`。未有匹配同帧查询时，
   `selected_step` 是这条只读查询；无 capability 时为 `null`。
2. `native_driver.py` 的 v3 查询先后读取暂停快照，并要求
   `_same_paused_native_frame`、public revision 与双方 encounter scope 不变。
   驱动只在绑定 native/public revision、snapshot ID、connection generation、
   episode、target/entry 和双方 ArmyID 的 cache 与新快照一致时投影输入。
   状态 `unavailable` 或缺输入不能被解释为“零伤亡”或可出发的估计。
3. 策略的模型 admission 只对精确目标接触生效。多段路线中，还须完整路线
   `one_day_contact_free=true`、第一 waypoint 的单跳原生 preview 精确、
   第一跳针对完整 hostile roster 的 contact query 证明
   `one_day_contact_free=true` 且 `conflicts=[]`，才选择**第一 waypoint** 的
   `move-army`；走后重查，不把“远端接触可接受”当作整条路线的通行证。
4. 驱动的一跳动作投影要求 paused、map ready、无 active event/待处理人物互动、
   军队可控、完整 hostile roster、相同 snapshot/public/native revision、
   connection generation、episode、日期、起点和路线终点。审计发现该投影
   原本没有排除最近一次成功 `restore-checkpoint` 之前的 preview：恢复后
   帧标识可能重现，从而让旧预览再次授权一跳。`02fd5a560` 已复用驱动
   既有的 `_native_history_after_latest_restore` 过滤器；回归测试覆盖旧预览
   被拒、恢复后的新预览可用。策略本身的 `_fresh_*` 路线证明已经使用
   恢复后的 history，本修复收紧的是**驱动 capability 投影**。

只读查询、路线预览与接触查询本身不提交行军、停战或其它资源变更，也不创建
War48 的 pending terminal action。**实际执行**一跳 `move-army` 则是另一条
游戏动作，需要其自身 ACK、路线/军队读回、下一 turn 与恢复证据；本复核没有
提交这条动作，也没有证明 War48 中它一定会被选择。`COMBAT_ENTRY_EU_ACTIVATION_ENABLED`
仍为 `False`，并未借此次复核启用另一套策略。

聚焦验证覆盖驱动 v3 生产查询、策略、first-hop 投影：普通 Python 与 `-O`
各 `50 passed, 46 subtests passed`。测试中新增 pending-interaction 负例，
及成功 restore 前后的 first-hop 证据失效/重建。原始 War48 save、driver 和 DLL
未通过 Git 提供，因此请求方仍需在正式配对上读取新 master、独立复验实际
`selected_step`、动作结果及下一 turn，才能填写 `verifications/R0244` 的通过状态。
