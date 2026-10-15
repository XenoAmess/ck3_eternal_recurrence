# 宣战机会查询冷却（开发期）

用户要求：连续两次宣战查询尝试没有实际造成宣战，暂停主动宣战机会查询 30 游戏日。状态存在受管 `state_dir/declaration-opportunity-cooldown-v1.json`，按角色与 episode 绑定；SDK/Service 重建不因 connection generation 改变而清零。冷启动如换 state 目录，只有在同一存档场次且 actor/episode 仍相符时才可搬运这份小状态。Game PID 改变会丢弃尚未结算的查询轮，保留已完成轮数与到期日。

一轮先要求原生 `query-declarable-wars` 返回完整 `available`、`accepted`、`query_sequence` 和声明列表；pending collect、重复同序号返回不计。查询结束只登记待评估轮。后续真实 `life-advance` 返回 `progress_status=postcondition`，开始/结束日期与新的同角色、同 episode 原生帧一致，并在暂停状态下确认没有战争、事件、待处理交互或未结算宣战，才记作一次“未宣战”。真实 `war_declaration_continuity_v1.war_started` 还须有 accepted native 响应、`postcondition_verified` 和活跃进攻战争 ID，才清零连续次数/冷却。单纯提交 ACK 不算开战。第二个独立未宣战轮在其推进结束日设置 `+30*24` raw 日期；到期当日恢复机会查询。

冷却只在当前和平、既有战争/防御/事件/未结算宣战优先级之后拦截主动机会分支；此时选择既有 `life-advance`，并跳过旧声明列表触发的 prewar v2 查询。现有战争、事件和政务规划继续照常仲裁。存储或绑定失败不得重放已完成业务命令；Service 在回执中保留 `declaration_opportunity_cooldown_v1.status=unavailable` 诊断，下一轮规划读取损坏状态则在提交新业务前拒绝。

离线回归：`test_declaration_opportunity_cooldown_v1.py` 验证两轮与到期、重复 collect、pending/ACK、真实宣战、跨 Service/PID/episode、陈旧候选与防御优先级。上线前这只是源码候选；实际 CK3 耗时和 30 日行为需以运行回执核验。
