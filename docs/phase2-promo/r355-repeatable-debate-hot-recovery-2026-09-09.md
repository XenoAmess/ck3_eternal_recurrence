# R355：重复辩论投递与同 PID 热恢复

## 结论

R355 在 `date_raw=53236224` 遇到本时间线第 4 次原版
`debate_event.5110`。事件仍为精确的 7-scope regular variant、native options
`(0, 1)`，玩家为 `32904`，且尚未选择按钮；唯一 RED 是旧合同
`max_occurrences=3`。

原版 `debate_events.txt` 的 “Should only fire once” 位于单场 debate activity
的结束投递逻辑内，限制的是每场活动一次，不是整局或 5,000 日产品观察窗只能
投递一次。R285、R327 与 R355 已累计证明同一受限产品时间线可由不同活动合法
投递至少四次。继续把实见次数逐次写成全局上限只会制造 harness RED，不提供
额外的事件身份保护。

合同因此改为
`occurrence_policy=repeatable-within-product-observation-window`：

- 不再对该事件施加按实见次数增长的全局 occurrence cap；
- 每次投递仍完整核验 event key、root、日期观察窗、所有 scope 名称/类型/别名、
  option 投影及 event-instance-advanced 后置条件；
- 仍固定选择确认计算胜者的 authored option 2 / native option 1；
- 总推进仍受 `MAX_ADVANCE_DAYS=5000` 与 absolute end date 约束。

## 同 PID park

R355 的临时 source-capture owner 在合同异常处先复核 paused/map/event instance，
再进入 Python 热恢复控制台，没有退出 supervisor：

- CK3 PID：`69176`
- connection generation：`1`
- event instance：`356`
- park artifact：
  `Z:\ck3_mod_rewrite\_runtime\p2r355endgamesource\contract-red-hot-park.json`
- park SHA-256：
  `BA3906CB618569ECE4BCCD20B3C5416ED82FC9DE238EDC1C456FC206B5CEAA41`
- `safe_paused_event_unchanged=true`
- `selection_attempted=false`

外部合同提交后只 reload Python 合同/production-entry 模块并从该事件继续；不因
runner-only 修复重启 CK3。若 paused frame、PID/connection 或 event instance 已
变化，则此路径拒绝热续。

## 静态回归

- occurrence-policy 精确测试：normal `1/1`、`python -O` `1/1` GREEN。
- manager-recovery 合同组：normal `41/41`、`python -O` `41/41` GREEN
  （各含 1 个环境条件 skip）。
- promotion source checkpoint runner：normal `83/83`、`python -O`
  `83/83` GREEN。

最终 live continuation、source registry 与 cleanup 字段将在同一 R355 会话完成后
补入本页。

## 同会话第二次合同 RED：查找秘密兜底

热恢复越过辩论事件后，同一 CK3 PID、connection generation 和暂停恢复链在
`date_raw=53239344` 遇到 `spymaster_task.0359` 的下一次精确投递。旧合同仅因
此前 R201 实见两次而设置 `max_occurrences=2`，因此在选择按钮前以
`known-interrupt-occurrence-bound` 保留 RED。

CK3 1.19.0.6 原版 `councillor_on_actions.txt` 将 `.0359` 放在
`task_find_secrets_reveal_selection` 的 `first_valid` 末位：每当一次 Find Secrets
任务发现的秘密没有更具体事件可用时，它都会作为兜底重新投递。事件定义的唯一
option 只对本次 `secret_to_reveal` 执行 `reveal_to = root`，不存在整局两次上限。

因此该合同同样改为
`occurrence_policy=repeatable-within-product-observation-window`。这不放宽任何
事件形状或选择条件：完整十 scope、角色别名/互异关系、root、唯一 native option
与 event-instance-advanced 后置条件仍逐次验证；总运行仍受 5,000 日产品观察窗
限制。该修复属于外部 Python 合同变更，将继续在 PID `69176` 上热重载，不重启
CK3。
