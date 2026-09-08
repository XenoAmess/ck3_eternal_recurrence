# R346 附身幻视事件中断（2026-09-09）

## 实机结果

- R346 从冻结 R248 候选存档推进 cross-cycle/endgame source 路径；输入为
  `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- 时间线在 `date_raw=53219640`、event instance `211` 暂停于此前未登记的
  `trait_specific_ongoing.2001`；root/player 为 `32904`，完整 saved scopes
  只有 `clergy: character=28662`。
- snapshot authored option count 与 rendered count 均为 `3`，native indices
  精确为 `(0,1,2)`，三项都 shown/enabled 且非 fallback/cancel。未知事件在
  选择前 RED，没有对 instance `211` 提交 select。
- cleanup GREEN、failed checks 为空、进程树已回收，冻结输入存档前后不变。
  report / cleanup SHA-256 分别为
  `2BB3C4830F17C2082D0D118A052B2D740BA694B998433975911895949DB98B27` /
  `ED81F9D5ED934127F9042A5601439D3C8B33DC267B3A62D1C569BB69C545B624`。

## 精确原版合同

CK3 1.19.0.6 原版
`events/trait_specific_events/trait_specific_ongoing_events.txt` SHA-256 为
`34A53CF4AA0B2AE955211024D5C0AF3753A05A4C3529CFE553BA5711C37F50BD`。
`.2001` 是 possessed 角色的一次性幻视事件；immediate 先写
`had_event_trait_specific_ongoing_2001` lifetime flag，再从宫廷司祭或同信仰
廷臣中解析 `clergy`。

- native `0` 执行 learning duel：成功可获得预言幻视 modifier 与 piety，
  失败会损失 piety 并改变 clergy opinion；
- native `1` 随机安排 7–21 天后的 `.2002` 或 `.2003`，明确进入 witch /
  secret knowledge 后续链；
- native `2` 只执行 `add_stress = medium_stress_loss`，没有 clergy、faith、
  piety 变化，也没有 `trigger_event`。

因此 option `3` / native `2` 是唯一最小、非宗教且终止当前窗口的路线。
合同绑定唯一动态非玩家 clergy、精确 1-scope / 3-option 帧和 lifetime flag
支持的 `max_occurrences=1`。本轮没有借事件扩展 faith/doctrine/witch 策略域。

## 验证与 Git

- trait-specific 专测 normal / `-O` 各 `1/1` GREEN；
- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` 与 `git diff --check` GREEN；
- 修复 commit `020a5e1bd2c731d6b32b3aa3c1a074e0ffcb9cea` 已 ordinary
  fast-forward push 到 `origin/master`，未 merge、未 force-push。

本轮只闭合真实随机中断，不新增业务 scene、definition、stage 或宣传素材
计数。canonical source registry 仍为 `3/4`，R347b 继续
`capture_cross_cycle_endgame`。
