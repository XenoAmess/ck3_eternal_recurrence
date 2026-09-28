# R0271：围城未来参战集合未明时的首路点续行（2026-09-28）

## 冻结输入与边界

[R0271 正式失败摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json)来自失败报告 SHA-256 `A5C5D21266D7ACFDC2CDD4C619B2846DE100BFF7F4CAD1E261DC116B880790CD`。阻断帧为 `native:30`、public revision `31`、native revision `30`、raw `53219160`、WarID `16777231`。玩家军 `83886367` 在 `2610`，到围城目标 `2629` 的当前路线预计 raw `53220216` 到达；敌围城军 `50331920` 已在 `2629`，场外敌军 `83886484` 在 `3719`，其当前路线预计 raw `53219928` 到达目标，**早于玩家 288 raw ticks（12 游戏日）**。两军都必须留在全敌接触名册内。

这组当前命令的 ETA 不能证明敌军 `83886484` 未来一定参战，也不能证明它会缺席；AI 命令、围城和战况可变。原 `offsite_hostile_may_join_by_target_entry` 阻断对**目标处的未来单次遭遇**是正确的。不能用只含 `50331920` 的 V3 输入批准接战，也不能把尚在 `3719` 的军队假装成当前固定守军。当前没有可据此声称的整场胜率、围城最终结果或终战净收益。

## 可恢复首路点

生产规划器仅在这个精确阻断理由出现、目标路线至少还有两个路点、目标路线的下一日全敌接触查询 `one_day_contact_free=true` 且 `conflicts=[]` 时，转入**不依赖战斗预测的探索路径**：

1. 原生预览从 `2610` 到首路点 `2614`，要求返回的完整路线恰为 `[2614]`。
2. 针对首路点重新查询包含 `50331920`、`83886484` 的同帧全敌接触；要求下一日无接触、无冲突，并核两次接触查询的逐军当前位置一致。缺读、位置矛盾或变化都停止。
3. 只有上述条件全部成立且 typed `move-army-83886367-to-2614` 可用，才提交该**首路点行军命令**。输出保留 `participant_scope_unresolved`、`active_attack_allowed=false` 和原始阻断理由；从未把目标 `2629` 的行军或战斗授权给该分支。

`2614` 的当前预计到达时间 raw `53219328` 距阻断帧 7 游戏日，而原生接触证明仅覆盖下一日。因此首路点命令**不是七日安全承诺**。命令后，既有受管 moving 路径在每个新的暂停帧重新取得完整敌军路线接触查询；缺当前帧证明或有接触会阻断下一次推进。`native_driver.py` 的 active-route 时域将每次推进限为 1 游戏日，并在执行前重验当前 revision 的证明。旧查询随日期或 native revision 变化失效。到达首路点后，规划器须重新识别围城、敌军位置、路线、现金和退战选项，再决定下一个动作；在到达前也不得把未来参战集合当成已知。这里的风险预算只覆盖逐日**即时接触**，不量化因行军而发生的围城损失、军费或远期战斗结果。

## 验证与剩余工作

聚焦测试以 Git 保存的 R0271 路线、ArmyID、日期和 ETA 重放规划器查询链，并反证首路点冲突、下一日接触不安全、过期读数及敌军位置不一致不会得到行军命令。普通和 `-O` 模式均通过；既有 `test_committed_route_requires_fresh_daily_horizon_even_when_sentinel_live` 核下一帧必须重新查询。测试中的完整战争帧和个别兵团实力是合成夹具，不能当作原生 R0271 实机复验。

当前独立 worktree 没有相对 `.venv`；静态复验显式使用主 worktree 的 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（Python `3.14.7`），依赖 probe 为 pytest `9.1.1`、NumPy `2.5.2`、Pillow `12.3.0`，并以 `PYTHONPATH=D:/w/r0271/ck3_autonomous_player/src` 指向本 worktree 源码。`test_combat_provisional_defense_canary.py` 普通与 `-O` 各 8 项通过；上述既有 moving 路线回归 1 项通过；`tools/validate_python_only.py` 为 `PYTHON-ONLY GREEN`。`-O` 模式 pytest 会对自身断言改写发出一条警告，测试主体使用 `unittest` 断言，结果仍为 8 通过。

本机选择同步的 OneDrive 目录尚无 H3388/R0271 精确 source pair，Git 只携带身份和失败摘录。匹配候选实测仍须取得 H3388 save、原始 driver、家庭 sidecar、配对索引和指定 DLL/injector，逐项验 SHA 后走官方 prepare/rebind/no-launch，再在受管新鲜 Steam 离线帧上用新的 attempt 查询与执行。不得将 H3446 存档与失败后已变异的 R0271 driver 强行配对。R0271 原失败保持 RED；此静态修复尚不新增 Robert 持久游戏日。
