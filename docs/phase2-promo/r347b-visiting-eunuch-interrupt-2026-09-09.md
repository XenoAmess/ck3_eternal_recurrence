# R347b 来访阉人事件中断（2026-09-09）

## Harness 预检更正

首次 R347 wrapper 在启动 CK3 前即发现干净 rebase worktree 不含被 Git 忽略的
本地 bridge DLL，因而 `FileNotFoundError` 退出；没有创建游戏进程，也没有
消费 CK3 串行门。R347b 保留旧 worktree 中已冻结且已哈希的 DLL 路径，只把
Python import 路径切到 rebase 后主集成 worktree。没有复制或重建二进制。

## 实机结果

- R347b 从冻结 R248 候选存档推进 cross-cycle/endgame source 路径；输入为
  `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- 时间线在 `date_raw=53205336`、event instance `204` 暂停于此前未登记的
  `ep1_flavor.1000`；root/player 为 `32904`，完整 saved scopes 为：
  `eunuch_target_culture: culture`、
  `eunuch_target: character=16841156`、`new_court: landed_title`。
- snapshot authored option count 与 rendered count 均为 `3`，native indices
  精确为 `(0,1,2)`，三项均 shown/enabled 且非 fallback/cancel。未知事件在
  选择前 RED，没有对 instance `204` 提交 select。
- cleanup GREEN、failed checks 为空、进程树已回收，冻结输入存档前后不变。
  report / cleanup SHA-256 分别为
  `CBBB584574DCB79544CAB562C1D5D101EE59DAB479E38B6A5A18899716E6BA5E` /
  `95B7690C8F274063046B91777DD8B76A6076ABF2234FA309A4DF436C04CD4DC6`。

## 精确原版合同

CK3 1.19.0.6 原版
`events/dlc/ep1/ep1_flavor_events.txt` SHA-256 为
`CC4CD67B77F9FA7B83E3B7A5534045F0DBFC1E724C53182E19ED7884BAD10924`；
yearly on_action 文件 SHA-256 为
`0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA`。
该事件是有 10 年 cooldown 的来访阉人提议：immediate 解析或创建访客，并在
存在相邻顶级领地时保存未受雇访客的 `new_court`。

- native `0` 支付金钱、雇佣访客、可能授予宫廷职位并改变好感；
- native `1` 执行 diplomacy duel，可能雇佣访客，也可能损失 prestige、
  建立潜在 rival 并移动访客；
- native `2` 不支付、不雇佣、不触发后续事件，只把访客移到 immediate 已选
  的 pool court，并执行玩家性格相关 stress impact。

因此 option `3` / native `2` 是最小终止路线。合同绑定精确三 scope 类型、
动态非玩家访客、三项 native 映射与当前实证的 `max_occurrences=1`。

## 验证与 Git

- EP1 flavor 专测 normal / `-O` 各 `1/1` GREEN；
- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` 与 `git diff --check` GREEN；
- 修复 commit `548b5cb683ad23d195d78f7b91bf4d7e35088531` 已 ordinary
  fast-forward push 到 `origin/master`，未 merge、未 force-push。

本轮只闭合真实随机中断，不新增业务 scene、definition、stage 或宣传素材
计数。canonical source registry 仍为 `3/4`，R348 继续
`capture_cross_cycle_endgame`。
