# R0284 单跳远期接战的首日行军门

## 来源与实际断点

固定 OneDrive `WAR/R0284-H90-CONTACT-20260928` 的九件素材已在接收机逐项核验（9/9）；源请求和传输清单的精确字节已镜像到 [Git 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-R0284-CONTACT-20260928.json)引用的 evidence。源是 **H90 derivative**，不能算 Robert 正式日期信用。原 run 的 256 个 turn 成功；第 257 turn 在 raw `53157816` 规划阶段 RED，未提交该 turn 动作。最后耐久存档是 h907/raw `53157768`/SHA-256 `64D669CE…2075`。收到的原 driver 还含 h908–h933 的存档后历史（其中含日期推进与失败帧查询）；必须由官方重绑/冷恢复处理，不能把存档和尾帧物理强配成已成功的第 257 turn。

同一失败帧的 h928 原生预览给出我军 `16777450` 从省 `2634` 到省 `2640` 的精确单跳。h930 的完整敌军接触查询只见敌军 `16777537` 留在 `2640`，预计到达 raw `53157960`，比当前帧晚 `144` raw 小时，即六天；raw `53157816` 至 `53157840` 的一天 `one_day_contact_free=true`、`conflicts=[]`。h932 的 v3 接战输入查询成功。源报告的风险准入为 admitted，但该输入冻结当前参战者，不能保证六天后的参战集合、敌军位置或战斗结果。原规划器只接受“单跳抵达在当前一天内”，因此返回 `native_war_general_battle_arrival_blocked`。精确缩减证据在 [blocker excerpt](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0284-CONTACT-20260928.blocker-excerpt.json)。

## 有界修复

`_general_battle_forecast_ingress` 仍先要求当前暂停帧、精确路线预览、当前完整敌军接触查询、同帧 v3 输入以及既有风险准入。只在下列条件同时成立时，才允许把**发起一条单跳路线**作为动作：

- 当前只有一个可识别的 WarID；该战事 `allied_armies` 必须明确包含同省的可控我军 ArmyID，`enemy_armies` 与本帧 contact 查询的完整非撤退敌军 ID 列表必须精确一致；原生路线是当前 ArmyID/出发省到目标省的单跳，且到达晚于当前一天；
- 原生接触时间线可见并绑定同一 ArmyID、出发省、目标省和预计到达日；其当前一天窗口与当前帧日期完全相等，`one_day_contact_free=true` 且冲突列表为空；
- `move-army` 是本帧公开的精确 typed action。无法识别单一 WarID、缺少 typed move，或 ArmyID/路线/日期/查询结果与当前帧不一致时，维持 RED；当前敌军存储路线已经穿过目标省而模型未纳入它时，同样停下。

返回的 `native_war_general_battle_distant_route_start` 只授权**下达移动命令**，明确 `future_contact_authorized=false`。它不授权六天时间跳跃、最终接战、胜率承诺、终战动作或施工完成。后续由既有 committed-route 分支在每个新帧重新读取完整敌军 contact horizon；每次时间推进至多一天，并检查其他可控军队。如果当前一天的接触不再为空，必须在该日之前停下或重新走同帧接战风险门。此修复没有改 native DLL/ABI、经济或终战策略。

## 已验证与待验证

本地纯 Python 聚焦测试：`test_general_battle_strategy.py` 常规 16/16、`-O` 16/16；新断言使用 `unittest` 方法，优化模式仍执行。新增源绑定回归直接读取 h928/h930/h932 的 Git 冻结摘录，验证精确路线只发起移动；把 native revision 改旧或加入另一敌军时，规划器只选择重新查询。另有 WarID/我军关联缺失、异军、异省、不可控、contact 敌军名单不一致的拒绝测试。源摘录没有携带完整 `active_wars.allied_armies` 帧；测试的战事成员行是合成的，实际成员关联仍须实机读取。另两项 `test_gameplay_bridge.py` 聚焦测试分别通过，覆盖既有行军每日新查询和不安全接触日拒绝盲推。测试使用本 worktree 的 `ck3_autonomous_player/src` 与主 worktree `tools/.venv` 解释器；没有 C++ 构建或游戏启动。

**接收机 exact-source 实机仍待执行。**官方 ordinary-seed rebind 要求 CK3 进程数为零，且必须取得无争用的 `ck3-screen` 窗口。接收机将用独立 profile/attempt 完成官方重绑、no-launch；来源机的小文件回件只按其精确字节和声明的语义入账，来源机的大存档、driver 与正式报告哈希尚未经接收机逐字节读取。

## 来源机 R0291 至 R0297 实测边界

R0291 的 12/12 turn 只到路线预览，未查询目标的完整敌军/v3，也未提交 move，故为语义 RED。R0293 与 R0295 各跑 8/8 turn，两个冷 PID 都重复同一八步前缀：先恢复施工/婚姻查询，再查终战、兵力、预览、完整敌军首日接触与 v3 输入；末步均停在 v3 **只读**查询，0 move、0 日期推进。v3 自身的 `planner_usable=false` 不是有界 forecast 必然拒绝的证据；第九步的正式规划决策此前未被观测。两轮原始小文件及哈希在 [R0293/R0295 verification](../autonomous-agent-progress/coordination/war-requests/verifications/WAR-ROBERT-R0284-CONTACT-20260928.R0293-R0295-inputs-bound.json) 中保全，旧 RED 不覆盖。

R0297 从来源机精确 h968 冷配对独立跑了 9/9 turn。第九步同帧 `native:3`/revision 4/native revision 3/raw `53157816` 的完整敌军名单是 `[16777537]`，原生首日窗口至 `53157840` 无接触；v3 输入 `input_observation_ready=true`。有界 forecast 的 256 样本全胜、Wilson 95% 胜率下界约 `0.9852`、p90 硬损耗约 `0.0641`、堆叠歼灭概率 `0`，在原风险合同下 `admitted=true`；这仍是研究型有界模型，原生战斗 parity、角色死亡、未来援军和每日变化未证明。正式规划器选择 `native_war_general_battle_distant_route_start`，只提交一次 `move-army-16777450-to-2640`。动作 ACK accepted；独立新原生 `native:4`/revision 5 快照显示我军仍在出发省 `2634`、状态 `moving`、目标 `2640`、剩余路线 `[2640]`，且仍为 raw `53157816`。操作器按事先约定停机并保存 h987 checkpoint；正式报告 `ok=false` 的 `operator_stop_checkpointed` 是请求的动作后停机，不能单独当动作失败或成功证据。接受移动动作与独立后态合起来证明**来源机同 PID 的路线发起 GREEN**；[R0297 verification](../autonomous-agent-progress/coordination/war-requests/verifications/WAR-ROBERT-R0284-CONTACT-20260928.R0297-route-start.json) 限定了证据范围。

h987 save/driver 仍在来源机；尚无新 PID 冷读回证明该路线被持久恢复，也没有任何 +24 raw 小时的每日安全重查。来源机 [NEXT-DAY 条件单](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0284-CONTACT-20260928.R0297-NEXT-DAY-READ-CONDITIONS.json.raw) 只是 proposal。接收方已在固定 WAR 目录同意两阶段边界：先用官方重绑和新 PID **只读**核 actor/WarID/ArmyID、原省、目标与剩余路线；若路线丢失即 RED，不能重发 move。仅第一阶段 GREEN 后，才在独立 attempt 重新查本帧所有敌军与所有可控军队安全、原生首日 contact horizon，并且只有正式 committed-route 规划器选既有推进动作时才至多 +24；随后读回日期、路线和 checkpoint 后停机。当前 R0297 日期推进 `0`，H90 derivative 对 Robert 正式日期信用始终 `0`。
