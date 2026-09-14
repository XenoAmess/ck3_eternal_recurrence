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

时间推进使用 R555 已实证的短脉冲：每次 `resume-map` 提交后立即 `pause-map`，再读取暂停帧。不得先轮询等待事件再暂停；R666 证明这种顺序会在
speed 5 下跨过 `sway_outcome.1001` 所在日期，直接撞到下一事件。R666 在选择前停止，source 未变且 cleanup GREEN，因此该结果保留为
harness RED，不是产品结果。

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
