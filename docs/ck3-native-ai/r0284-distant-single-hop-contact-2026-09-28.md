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

**本机 exact-source 实机仍待执行。**官方 ordinary-seed rebind 要求 CK3 进程数为零，且必须取得无争用的 `ck3-screen` 窗口。R0284 将用独立 profile/attempt 完成官方重绑、no-launch，再依次证明本机同帧读数、typed move/poststate、下一天 fresh full-hostile recheck；任何失败保留为新的 RED attempt，不覆盖源 run 或旧素材。来源机 R0291 的 12/12 有界 turn 只走到路线预览，没有 target full-hostile/v3 查询或 typed move，因此仍是语义 RED；详情见本请求的 R0291 验证记录。
