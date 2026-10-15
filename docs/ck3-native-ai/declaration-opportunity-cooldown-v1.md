# 宣战机会查询冷却（开发期）

用户要求：连续两次宣战查询尝试没有实际造成宣战，暂停主动宣战机会查询 30 游戏日。状态存在受管 `state_dir/declaration-opportunity-cooldown-v1.json`，按角色与 episode 绑定；SDK/Service 重建不因 connection generation 改变而清零。冷启动如换 state 目录，只有在同一存档场次且 actor/episode 仍相符时才可搬运这份小状态。Game PID 改变会丢弃尚未结算的查询轮，保留已完成轮数与到期日。

一轮先要求原生 `query-declarable-wars` 返回完整 `available`、`accepted`、`query_sequence` 和声明列表；pending collect、重复同序号返回不计。查询结束只登记待评估轮。后续真实 `life-advance` 返回 `progress_status=postcondition`，开始/结束日期与新的同角色、同 episode 原生帧一致，并在暂停状态下确认没有战争、事件、待处理交互或未结算宣战，才记作一次“未宣战”。真实 `war_declaration_continuity_v1.war_started` 还须有 accepted native 响应、`postcondition_verified` 和活跃进攻战争 ID，才清零连续次数/冷却。单纯提交 ACK 不算开战。第二个独立未宣战轮在其推进结束日设置 `+30*24` raw 日期；到期当日恢复机会查询。

冷却只在当前和平、既有战争/防御/事件/未结算宣战优先级之后拦截主动机会分支；此时选择既有 `life-advance`，并跳过旧声明列表触发的 prewar v2 查询。现有战争、事件和政务规划继续照常仲裁。存储或绑定失败不得重放已完成业务命令；Service 在回执中保留 `declaration_opportunity_cooldown_v1.status=unavailable` 诊断，下一轮规划读取损坏状态则在提交新业务前拒绝。

连续次数在达到两次后保持为 `2`，到期不清零。到期恢复的一次完整查询轮如果仍未实际宣战，在该轮推进结束后重新冷却 30 日；只有上述核验过的真实宣战才把次数与期限清零。旧 v1 的 `0`/`1` 状态仍可读：没有期限时保留原值，有既有期限时该期限证明此前已达到阈值，读取时归一为 `2`（包括期限已过）；后续既有状态写入会保存归一值。新写入的 `2` 也直接兼容同一 schema。

2026-10-16 离线定位使用 N41 既有 `p06-responses`：FULL 6 和 67 共推进 155 日、耗时 105.572 秒；7 次宣战查询占 42.592 秒。查询发生在相对第 0、9、54、62、64、110、119 日，未出现真实宣战步骤，对应 METRICS 的战争数均为 0。旧逻辑每次设置冷却期限时把连续数清为 0，实际三次冷却在第 18、73、128 日启动，期限分别为第 48、103、158 日。因此期限过后重复承担第二次无效查询。第 62 日查询随后遇到事件，未形成已结算查询轮；本次保持该既有处理逻辑。上述耗时来自完整已有回执，不能作为此修复已在实机提速的证明。

离线回归：`test_declaration_opportunity_cooldown_v1.py` 验证两轮与到期、到期后单轮再次冷却、旧状态归一与新 `2` 状态、重复 collect、pending/ACK、真实宣战、跨 Service/PID/episode、陈旧候选与防御优先级。上线前这只是源码候选；实际 CK3 耗时和 30 日行为需以运行回执核验。
