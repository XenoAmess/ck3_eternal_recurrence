# P32 连续和平窗口的实际成本（只读）

范围固定为 `native21-cold-generation03/p32-responses/0738-1-result.json` 至 `1017-1-result.json`，2026-10-16 21:05:52.516662–21:10:52.428643 UTC。只读取 275 个已完成回执和 `ordinary-stage-timings.jsonl` 的一次完整行前缀，未读取活跃 Driver state、未调用 Game/MCP/OBS。末端序号固定为 1017；后续新回执不改变本报告。相邻回执最大间隙 1.389 秒，因此此段没有人为调试长停顿。

299.911981 秒内真实推进 288 游戏日，**完整墙钟 1.041361 秒/日**；MCP 回执耗时合计 284.107856 秒，回执间隙 15.804125 秒（0.054875 秒/日）。37 次 `life-advance` 的 `war_progress_before.wars` 全为空，全部 speed 5；35 次推进 8 日、一次 7 日、一次 1 日，合计 288 日。30 次规划阶段为 `native_war_discovery_cooldown`，7 次为 `native_war_entry_forecast_required`。本结论仅适用于该和平窗口，不外推为整个 30 年或战时成绩。

| 操作 | 次数 | 完整耗时 s | s/游戏日 | 说明 |
|---|---:|---:|---:|---|
| `life-advance` | 37 | 173.812445 | 0.603515 | 包含时钟等待、规划、持久化，不能与其内部阶段相加 |
| `query-declarable-wars` | 8 | 47.245715 | 0.164048 | 零日；Native 读回等待和规划都占用明显时间 |
| `query-war-entry-assessments-v1-1-*` | 37 | 18.078753 | 0.062773 | 六个候选目标合计；零日、同帧风险评估 |
| `ck3_save_checkpoint` | 3 | 16.474773 | 0.057204 | 真实游戏存档；其内 Driver JSON 写入仅 2.622004 秒 |
| `query-war-results-window-v1` | 40 | 10.907956 | 0.037875 | 零日、战果 UI 观察 |
| `private-query-player-construction-receipt-v1` | 6 | 9.875112 | 0.034289 | 零日、建设完成回读；其内 Driver JSON 写入 4.453757 秒 |
| 事件上下文查询与 3 次事件选择 | 6 | 6.192318 | 0.021501 | 必答 UI 不能按普通 noop 跳过 |
| 135 次 metrics + 3 次语义快照 | 138 | 1.520783 | 0.005280 | Root 读回成本较小 |

实际阶段计时：37 次推进的 `driver.life_advance_progress_wait` 共 97.354787 秒（0.338037 秒/日），`service.normal_plan_turn` 共 39.115562 秒（0.135818 秒/日），`driver.full_state_persistence` 共 27.063434 秒（0.093970 秒/日）。全窗口 52 次 Driver 全态写入共 38.726398 秒（0.134467 秒/日），134 次普通规划共 77.277282 秒（0.268324 秒/日）。阶段会嵌套：`driver.life_advance_public_change_wait` 99.402704 秒在进度等待路径中，`_plan_turn_internal` 64.070659 秒有重复规划调用；均不可与父阶段直接相加。`query-declarable-wars` 的 16 条 `driver.native_command_result_wait` 共 33.820706 秒，8 条外层 `normal_plan_turn` 共 12.676714 秒；等待计时是墙钟，不等于纯 Native CPU。

源码链：`strategy.py:15602–15622` 仅在空战争列表、宣战机会冷却生效后选择日期推进；`native_driver.py:24257–24505` 设速度、恢复游戏并等待日期/原生暂停；`native_driver.py:11625–11665` 在写锁内编码冻结 Driver state 后原子替换。此窗口中 8 次完整宣战查询/288 日，现有 2 次无宣战→30 日规则确实在起作用。G2 已有另一个和平 horizon 候选，本包没有重复实现或宣称其 Native 多日停止安全已验收。

当前无需热切补丁。仅把 40 次战果窗查询全部消掉，理论上最多节省 0.037875 秒/日，却会放弃当前 UI 观察；仅把本窗口 52 次 Driver 写入全消掉，理论上最多 0.134466 秒/日，但会破坏已承诺的崩溃恢复。稳定执行优先。要低于 1 秒/日，必须在完整战术和业务回读不变的前提下实机验证后续 horizon/时钟方案；此窗口不能证明只改 Python 浅复制或跳过持久化可安全达标。

数据与脚本：`P32-PEACE-5MIN.json`、`analyze_peace.py`。回执范围、完整计时日志前缀字节数与 SHA-256、每类操作和阶段样本数均在 JSON；原始回执仍位于上述只读路径。
