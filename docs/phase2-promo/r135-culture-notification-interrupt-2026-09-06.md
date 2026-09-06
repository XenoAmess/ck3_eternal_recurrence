# R135 管理周期文化通知阻塞取证（2026-09-06）

## 结论

- R135 在 frozen source `899ecc105366918052717ec29d215789a2b00169` 与 R130 正式产品投影下成功加载：loader 303、fatal 0。
- 5 速推进到 `date_raw=53148048` 时，原版事件 `culture_notification.1111` 暂停流程。玩家仍为存活的管理者 `32904`，B1 仍 active；本轮不是角色死亡，也不是产品 RED。
- 当前玩家不是文化创建者。原版两个选项由互斥 trigger 控制，实机只渲染 authored/native index `1`（按钮编号 2）。该选项只有 `custom_tooltip`，没有游戏状态 effect，可以在完整帧严格匹配后关闭。
- 验收器只允许这一条实测形状：根角色、五个 saved scopes、snapshot 两个 authored slots、一个可见且可点击的 native index 1，以及单次出现上限。任一字段漂移都继续 fail closed。

## 精确实机形状

- root：character `32904`
- saved scopes：`founder` character `35761`、`parent_culture_1` culture、`new_culture` culture、`parent_1` culture、`ethos` flag
- snapshot option count：2
- rendered option count：1
- rendered/native mapping：`0 -> 1`
- fixed selection：按钮 2 / native index 1

## 来源与证据

- 原版源文件：`game/events/culture_events/culture_notification_events.txt`
- CK3 1.19.0.6 原版源文件 SHA-256：`875A91E2E308DCFB15AD8DD99D267F721985798FB6B6AD0E605011FE1AB9AC8F`
- 实机事件帧：`Z:\p2m135_a\manager-cycle-recovery.json`
- 实机结论边界：只证明这一非创建者分支是无状态变更的通知关闭；不建立事件命名空间 allowlist，也不自动选择其他文化事件。

## 后续

R136 继续使用 frontend-first、默认 5 速与同一 R131 checkpoint。只有再次出现真实 `one_life_terminal_reason=played_character_changed` 才累计 manager-owner terminal 次数；R135 不计入该次数。
