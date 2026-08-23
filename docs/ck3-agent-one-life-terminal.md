# CK3 Agent 一代制终局状态机

更新时间：2026-08-24。

本文记录自动游玩 Agent 消费 Mod 死亡结算的 Python/MCP 路径。Mod 的生产写入顺序和 native
内存字段来源见 [ck3-native-settlement-contract.md](ck3-native-settlement-contract.md)。

## 公共协议

- capability：`game.state.xar-one-life-settlement`
- snapshot key：`one_life_settlement`
- MCP 读取：`ck3_get_one_life_settlement`
- MCP 结算：`ck3_settle_one_life`
- 既有通用动作：`death-terminal`

Native 的两个 `CFixedPoint` 分数以显式 `{raw, scale}` 传输。Python 只按消息携带的 scale
换算为分数，不猜测内存缩放；整数结果规范为 `int`，含小数结果为有限 `float`。Data Mod
若直接发布语义 JSON number，也进入同一规范化结果。

## 状态流

```text
正常游玩
  -> episode CharacterID 死亡或 GetPlayer 切换
  -> planner 只允许 death-terminal，不再规划婚姻、战争、存档或 life-advance
  -> capability 不存在：立即返回 settlement_unavailable（旧 DLL 兼容），不写跨局 episode
  -> capability 存在：有界等待 ready=1 且 source_character_id=episode CharacterID
  -> 读取 final_score 和结算明细
  -> record_written=1 且 candidate>0：有界等待 tutorial.txt 出现对应 xar_hs_ge_<candidate>
     并连续两次观察到文件内容不变
  -> 未破纪录或 candidate=0：不等待 tutorial.txt
  -> 只有完整且 score 非空时 record_one_life_episode
  -> terminal_complete；后续 auto-turn 不再重复结算，也绝不游玩继承人
```

成功终局固定返回非空 `score`、`continue_as_heir_after_death=false` 和
`heir_gameplay_actions=0`。新纪录 lesson 未在时限内稳定落盘时，本次动作失败并可重试；Agent
不会先写跨局 episode 再退出 CK3。旧 DLL 没有 capability 时保持原先的即时终局行为，但明确返回
`settlement_status=settlement_unavailable` 和 `score=null`，且不进入等待、不消费完成态。当前 backend
仍无该 capability 时 planner 停在 `terminal_settlement_unavailable`，不会忙循环；同一进程随后接入
新版 native 或匹配的 Data Mod 投影后，会重试并只记录一次真实分数 episode。

`hybrid-fallback` 只合并 native 与 Data Mod 明确发布的 semantic capability 和 snapshot 投影；
读取结算不会触发 OCR、恢复窗口或键鼠输入。若 native DLL 尚无结算 capability、Data Mod 已发布
匹配 payload，`hybrid-fallback` 由 native driver 消费该 semantic payload、等待纪录位并记录 episode；
Data Mod 和视觉 backend 都不会执行终局输入动作。

## 跨局成就归一

跨局记录同时识别视觉旧步骤和 native 动态步骤：

- `war-enforce-demands` 与 `enforce-demands-<war_id>` 的
  `war_victory.status=victory_enforced`；
- `war-disband-armies` 与 `disband-army-<army_id>` 的
  `army_disband.status=disbanded` 或 `war_action.status=disbanded`。

`arrange-marriage-<choice>` 返回的 `proposal_submitted` 只证明提案已发出，不算婚约成功。Native
driver 只有在后续快照中看到该候选精确出现在玩家的 `betrothed_id` 或 `spouse_ids`，才会把
`marriage_result.status=accepted_betrothal` / `accepted_marriage` 与
`source=native_relationship_snapshot` 写回命令历史并计入跨局成就；视觉旧链仍以稳定可见的
`marriage-confirm-response` 为准。

## 跨局启动与策略消费

终局只有在 `settlement_status=complete`、`score` 非空且同一 run 已写入 `one-life-history.json` 后，才会公开 `start-next-episode`。该动作从不可变
`xar_episode_seed.ck3` 启动新 run；不会继续扮演继承人，也不会把 recovery `xar_checkpoint.ck3` 当作下一局种子。返回结果包含来源/新
`episode_run_id`、`lifecycle_intent=new_episode` 与 `cross_run_plan_used`。

新局 planner 读取最新 `next_run_plan.priorities`，把最高优先项映射到 war / marriage / succession 开局族。至少战争优先会让 baseline checkpoint 后先做 native war discovery，婚姻优先则先做 native marriage discovery；返回的 plan 同样带 `cross_run_plan_used`，因此可直接观察跨局经验是否实际改变了行动顺序。没有已完成 episode 的第一局保持原默认顺序。

## Minimized 实机闭环

2026-08-24 的有继承人样本完成了端到端闭环。episode CharacterID `29829` 切换到继承人
`38822` 后，Agent 只执行 `death-terminal`；native settlement 给出分数 `6.8`，并确认
`tutorial.txt` 的 `xar_hs_ge_6` 连续两次稳定。跨局记录中
`continue_as_heir_after_death=false`、`heir_gameplay_actions=0`，继承人没有收到婚姻、战争、
存档或时间推进命令。

随后 `start-next-episode` 从不可变 `xar_episode_seed.ck3` 把 CK3 从 PID `119628` 重启为
PID `110972`，`lifecycle_intent=new_episode`。虽然 baseline 使用相同 CharacterID `29829`，
新的 `episode_run_id` 与上一局不同，terminal 标记已清零，history 从
`start-next-episode` 重新开始，结果携带上一局生成的 `cross_run_plan_used`。窗口最小化后，第二局
继续通过 native MCP 提交一次军队移动，再推进 7 游戏日；军队省份 `2618 -> 2615`，最终地图暂停且
`IsIconic=true`。该样本证明“结算上一局 -> 不玩继承人 -> 新建 run -> 在最小化状态继续自动游玩”
已真实贯通。无继承人死亡仍是单独的待验收分支。
