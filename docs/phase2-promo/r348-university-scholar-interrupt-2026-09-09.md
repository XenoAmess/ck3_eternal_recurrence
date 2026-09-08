# R348 大学学者事件中断（2026-09-09）

## 实机结果

- R348 从冻结 R248 候选存档经 MCP 推进 cross-cycle/endgame source 路径，
  在 `date_raw=53215344`、event instance `277` 安全停于此前未注册的
  `major_decisions.2011`；root/player 均为 `32904`。
- 当前窗口仅保存动态 `new_courtier: character=16842782`。snapshot authored
  option count 与 rendered count 均为 `2`，native indices 精确为 `(0,1)`，
  两项均 shown/enabled 且非 fallback/cancel。
- 未知事件在选择前 RED；driver 最后一条命令是当前窗口 context query，没有
  对 instance `277` 提交 select。cleanup GREEN、failed checks 为空、进程树
  已回收。
- 冻结输入前后均为 `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
  report / cleanup SHA-256 分别为
  `CD982E14712EC4C92CDAB24AEDA4876C14C1E9BEC6F10E53D8B846A93EB9B41B` /
  `8529DC16EAB7BF088055D1EC18FAA73E24771228C0E1D2DF19990A3DE1D0D672`。

## 精确原版合同

冻结 CK3 1.19.0.6 的
`events/decisions_events/major_decisions_events.txt` SHA-256 为
`AA8BE60D8BEF5A902E55865A918574BDBAE5092E94EF07985A68F1BCF1979667`。
事件 immediate 会创建并雇用一名 scholar character：

- native `0`（“欢迎，欢迎！”）保留已受雇学者，并使其对玩家获得
  `friendliness_opinion +15`；
- native `1`（“这里没有你的位置。”）把学者移回 pool，并使该动态角色对
  玩家获得 `disappointed_opinion -10`。

两项均不调度后续事件。虽然 native `0` 的脚本语句更少，但它会永久保留
新学者并改变玩家宫廷结构；native `1` 更接近恢复随机事件发生前的产品
时间线，因此采用 option `2` / native `1` 作为最小终止路线。

该事件可来自年度随机池，也可由大学决议、大学建筑完成或 EP3 重建大学
决议延迟调度。R348 没有 caller provenance，故不把当前一次出现伪定性为
其中某条唯一入口。事件本身无 cooldown；当前只按一次真实出现设置
`max_occurrences=1`，若固定长时间线再次出现则继续凭 live evidence 最小放宽。

## 验证与 Git

- manager-court 专测 normal / `-O` 各 `2/2` GREEN；
- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` 与 `git diff --check` GREEN；
- 修复 commit `1942cd1401624169c1f6765c6fbea0365d7eb146` 已 ordinary
  fast-forward push 到 `origin/master`，未 merge、未 force-push。

本轮只闭合真实随机中断，不新增业务 scene、definition、stage 或宣传素材
计数。canonical source registry 仍为 `3/4`；R349 继续
`capture_cross_cycle_endgame`。
