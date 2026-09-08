# R349 人才与进修汇总中断（2026-09-09）

## 实机结果

- R349 从冻结 R248 候选存档经 MCP 推进 cross-cycle/endgame source 路径，
  在 `date_raw=53221752`、event instance `342` 安全停于首次进入这条固定
  长时间线的产品事件 `zg361cl.390`；root/player 均为 `32904`。
- 当前窗口精确包含 `60` 个 inherited saved scopes，其中 `25 character +
  35 value`；snapshot 与 rendered option count 均为 `1`，唯一选项为
  rendered/native `0/0`，shown/enabled 且非 fallback/cancel。
- 未知事件在选择前 RED；实例 `342` 不在 140 条已 drain 记录中，最后一次
  选择仍是实例 `341` 的原版事件。cleanup GREEN、failed checks 为空、进程
  树已回收。
- 冻结输入前后均为 `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
  report / cleanup SHA-256 分别为
  `77E0145C142202FA3BF68BD1F66FF8F594526EB35C2FED96E0C154A53AED524D` /
  `34DBE6F8C12E815C8824D91D963CA607830C3957E95B712A026A9F60DE6A0099`。

## 权威业务链

权威生成器 `gen_361_career_learning_runtime.py` 规定：AH/AI 两域最终 stage
完成后，只有同一 portfolio cycle、两域 completed 均达到 expected、玩家
尚未显示 digest 且无 pending 时，才会设置 `digest_pending=1`、
`digest_shown=1` 并在 D+1 触发 `.390`。

`.390` 只有一个按钮：“收存本轮人才案回执；不新增付款或期限。”该按钮
仅移除 `zg361_cl_digest_pending`，不付款、不新增期限、不调度另一个事件，
也不直接改变 career/learning case。它是当前卡的 terminal acknowledgement，
不是整条时间线终点；随后既有 Central pump 才可完成 stage 9 并进入
stage 10 manager governance。

## 合同、验证与 Git

- 合同精确绑定本轮 60 个 scope 名称与总数、唯一选项、日期窗口及玩家
  root；这些 inherited scopes 不被 `.390` 按钮消费，因此没有冻结 25 个
  动态 character ID 或伪造 35 个 value payload。
- career-learning 专测 normal / `-O` 各 `2/2` GREEN；promotion source
  checkpoint runner normal / `-O` 各 `83/83` GREEN；`py_compile` 与
  `git diff --check` GREEN。
- 修复 commit `ff8dd16` 已 ordinary fast-forward push 到 `origin/master`，
  未 merge、未 force-push。

本轮证明了 stage 9 的真实前置汇总卡已可达，但尚未证明按钮后的 stage 9
transition 完成，因此正式 stage 计数仍保持 `8/11`。canonical source
registry 仍为 `3/4`；R350 继续 `capture_cross_cycle_endgame`。
