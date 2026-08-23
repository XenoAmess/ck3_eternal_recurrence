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

`arrange-marriage-<choice>` 返回的 `proposal_submitted` 只证明提案已发出，不算婚约成功；只有既有
确认链的 `marriage_result.status=accepted_betrothal` 计入跨局成就。
