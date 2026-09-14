# 有界原版事件地平线验收

## 目的

`run_registered_event_horizon_material_live_acceptance.py` 处理“已有检查点早于目标事件，但目标位于短而确定的时间窗内”的 G2 输入。调用者必须声明
source/target exact date 和按顺序出现的前置事件。runner 在单次冷恢复中只推进到目标日期，每个前置事件都先查询 exact-build context，再由
production registry 选择，不能用硬编码选项绕过策略。目标事件复用相同 registry，并额外要求 material comparator 返回
`verified_change` 后才保存 successor。

该入口不允许跳过未声明事件、超出目标日期、使用未知事件 fallback 或提交战争动作。它是可切换操作者和机器的内部 MCP consumer；所有输入路径、
角色、日期、哈希和事件顺序都由调用者显式传入，不依赖固定 PID、账号或 CK3 轮次。

## 当前冻结输入

R555 已证明一条短轨迹：source `date_raw=53155680`，依次经过 `sway_outcome.1001`、
`stress_threshold.1011`，于 `date_raw=53155992` 到达 `tgp_travel_events.0030`。对应 checkpoint SHA-256 为
`352AA495934DC49AE5567D8422147139B02BDE8979F4943636975460B80CFA76`，driver-state SHA-256 为
`1867E8C35158416F8DA9B8352D4D0C69D3D4ACCE5D8A53308AB8DC4B7815F6BA`，CharacterID 为 `27181`。

这只冻结可执行输入和验证方法；在新的 production-live report 出现前，不改变 `tgp_travel_events.0030` 的 live 状态。

R666 证明 speed 5 下先等待事件再暂停会跨过 `sway_outcome.1001` 所在日期；R667 又证明 resume 后立即 pause 会产生大量零日期脉冲，最终仍可能
跨日。R668 进一步证明 command `submitted` 不是状态已物化：必须先观察 `speed=1`，再提交 resume 并观察 `paused=false`，之后才能等待日期首次增加并
立即暂停。R669 已取得两个连续 `+24 raw`，同时证明事件会在到达日期后的暂停刷新中才物化；现行入口只在调用者声明的事件日期等待最多 5 秒，不在普通
日期增加等待。单次脉冲超过 24 raw 会直接 RED；这些轮次都在选择前停止，source 未变且 cleanup GREEN，因此保留为 harness RED，不是产品结果。

## 验收边界

GREEN 必须同时证明：

- exact-build、DLL、注入器、checkpoint 与 driver-state 哈希一致；
- source 是预期玩家、日期、暂停且无活动事件的地图帧；
- 初始无事件帧要求通用 query/select capability 与当下可执行的 resume/pause/save steps；具体 query/select step 由事件出现后的真实调用验证；
- 前置事件按声明顺序出现，均由 production registry 推荐并关闭；
- 目标事件在 exact target date 出现，registry 发布 campaign utility；
- 目标选项只提交一次，event instance 前进，material comparator 观测到真实变化；
- successor checkpoint 落盘、source 不变、CK3 cleanup GREEN；
- 完整 native command delta 与实际允许的 resume/pause/query/select/save 序列一致。

## R670 disposition

R670 exposed one more bounded runtime condition on the unchanged source: `set-speed-1` was submitted, but speed one did not materialize within ten seconds. The runner sent no resume, query, or option selection. Source integrity and cleanup are GREEN. The report is `Z:\ck3_mod_rewrite_process_assets\g2-m2-r670-tgp0030-material-89ae41f\report.json`, SHA-256 `79FB89A4D28AF6841BBBC60C70A30CA469D550FB988FF374280D56F7FC5ED3B0`.

The old R555 timeline is removed from the active retry queue. `tgp_travel_events.0030` remains pending for a new near-event encounter; R665-R670 remain harness RED and do not change its live status.
