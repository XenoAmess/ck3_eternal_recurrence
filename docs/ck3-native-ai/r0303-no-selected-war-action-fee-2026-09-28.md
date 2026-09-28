# R0266 / R0303：本轮未选择战争动作时的即时费用零值

正式 M5 战时只读计划现在有一个严格的条件性生产者：[`war_cash_no_selected_action_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/war_cash_no_selected_action_v1.py)。它只在暂停地图、唯一匹配 WarID、计划顶层 `snapshot_id`/`revision` 与原生观测一致、`one-life-turn-v1` 计划含有**显式** `selected_step: null` 时，返回 `immediate_war_action_cost_raw=0`，附同帧、WarID、Q100000 和来源。任意查询、移动、投降步骤、缺少键、旧计划、多场战争或非暂停帧都拒绝零值。

这个零值的含义仅为**当前计划没有选出要执行的战争动作**，不证明某个具体行动免费，也不证明历史待付款项为零。正式观测最多把这一项从缺失列表中移除；`pending_war_cash_raw`、未来上界、风险预算、战争最低保留额、期限与假设仍保持缺失，`formal_cash_receipt_eligible=false`、`formal_action_ready=false`。原生动作报价、付款后核销、玩家政策和下一次暂停帧重审仍各需独立来源。

R0303 来源消息只给出了摘要中的 `selected_war_action_step=null`，没有交付接收端可复核的同帧完整计划和后验帧，因此**不能倒填 R0303 的即时费用为零**。本代码供后续正式运行在实际满足上述门时生成新回执；不能把它当作 H3686 实测。聚焦回归覆盖正例与查询/移动、缺键、跨快照、多战争和非暂停拒绝，并验证正式报告只投影有界的来源字段。
## Full frame requirement

The diagnostic also requires the same construction observation to carry an
exact source frame: snapshot ID, public and native revisions, game date,
episode run ID, and actor CharacterID. This is a plan-local proof of *no
selected action on that frame*. It is not a native price quote. If a selected
step appears later, the report projector drops the zero observation and puts
`immediate_war_action_cost_raw` back in the missing list. A new paused native
frame and formal postcheck are required before any value could be considered
for a consumer; current R0303 history supplies neither.
