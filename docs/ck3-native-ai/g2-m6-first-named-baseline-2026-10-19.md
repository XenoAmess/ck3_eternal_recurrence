# M6：30 日时首次实际命名基线

`machine_id: xenoamess-full-tower-eb9d2c1186`，场次 `robert-first30-v20261019`。
本次离线观察于 `2026-10-19T04:13:54Z` 读取 M0 已冻结的 META、ledger、schedule，
逐份符合其 bytes/SHA。冻结发生于 `04:13:02.764407Z`；其原 AUTO143 于 `04:06:04.167529Z` 返回错误。
[小回执](evidence/g2-m6-first-named-baseline-2026-10-19.json)区分内部读观测、外层错误和后续消费。

原 [AUTO48 Start](g2-m6-first-natural-start-2026-10-19.md) 的 action
`sway-88765ff2258b45f88acb5eeabc1f63c2`、actor `31254`、target `33946`、full SchemeID `2`、generation `0` 均未改变。
这次实际 material 来源为 Native revision `58`、raw date `53145048`，距 Start 的 `53144328` 正好 30 日。
completion 对同实例仍为 active/continue，storage 没复用，owner 仍是玩家；material 的 completion 来源也为 revision `58`。

首次读到的目标总好感是 `17`。具名 `scheme_sway_opinion` 与 `sway_blocker_opinion` 均为
`observed=true / present=false / value=null`，所以两个命名项是已知零。
`previous_scheme_sway_opinion=null`、`incremental_named_gain_observed=false`、`dedicated_benefit_observed=false`，
没有 `first_named_gain_intervention`。这是本次 30 日时的真实 active 命名基线，
不能倒填 Start 当天的意见，不能由总好感 17 推出 Sway 收益，也不是首次具名正增量。

内部读取和持久化已发生，但 AUTO143 在 fallback 重新进入提交前回调时返回
`this decision was already published; no action replay`。
M0 的冻结源审明确其后普通 Driver dispatch 未发生，原 Sway 也没有重新 Start。
原 result 的 `structured_content=null / is_error=true` 保留；不把这次局部只读观察记为完成普通 AUTO。
总体 observer summary 返回值没有留存，本包不补造 `status=observed` 或其它摘要字段。

新 material 的 `next_turn_consumed=false`，所以尚无后来普通回合消费这份基线。
Start 和旧 active observation 中保存的 following revision `18`、date `53144520` 来自更早 AUTO50，
早于这次 revision `58`、date `53145048`，不能借来证明新基线已消费。
`terminal_intervention` 字段当前仍是 active/continue、terminal=false，也不是自然终态。
schedule 记 `observe_applied`，本次日期 `53145048`，下一期限 `53145768`，为开局后第 60 日。

本次只对已冻结小原件运行现 [collector](../../tools/g2_saved_campaign/m6_closed_evidence_collector_v1.py)一次：
[manifest](evidence/g2-m6-first-baseline-manifest-2026-10-19.json)与
[指针索引](evidence/g2-m6-first-baseline-pointer-index-2026-10-19.json)保留这份局部 producer 来源。
该索引不授 M6、不把 ledger 来源冒充 ordinary AUTO。没有读取活跃 ledger、Driver、SAVE、大 AUTO 或媒体，
没有新增 RPC、Start/Stop、重放 143、编译或现场操作，也没有重跑软件矩阵。

当前 Game 仍按 runtime owner 给出的 Native25/C3 范围记录；后继 Native gate 源码和构建不能回填本次现场资格。
M6 已有真实 Start、Start 后普通消费及 30 日命名基线；真正具名正增量、自然终态和其后普通消费仍未观察。
G2 保持 **6/8**、M6 `in_progress`。后续只在 owner 正常已结算的新观察面出现时采证，长局继续推进。
全部新增物是小记录，沿统一 policy 1.0.0 的原预算和 48 小时派生复核，无重型写入、删除或新容量信用。

## 04:19Z：后来 AUTO147 已消费这份基线

runtime owner 交来原 `0147-1-result.json`，160649 B、SHA `e5cf5bfc…7ea75`，
本包独立核 pin 后只读该已结束回执。它于 `04:18:04.551908Z` 正常返回 Service
`executed / life-advance`，原 `sway_following_turn/material_intervention` 保持 baseline 的
source revision `58`、date `53145048`、具名零值和同一原实例，另外实际新增
`next_turn_consumed=true / following_native_revision=68 / following_date_raw=53145240`。
该源的 Native clock 从 `53145048` 到 `53145240`，实际 8 日并在 exact target paused。
这次可以记录这份基线被后来真实普通 Service 执行消费；基线测量来源没有被后来的日期替换。

原147仍有独立外层边界：queue 旧 classifier 因附加 pause-map 的 rejected ACK 拒绝，
runtime owner 正纯离线处理；本包观察时 paired MET 尚未给出。
所以不授完整外层已结算 AUTO，不把内部消费抹掉，也不因分类失败重放原147。
没有 first gain 或自然 terminal，原143错误仍保留。

对这个新的 baseline-consumption 观察面，collector 仅再运行一次，
以[新 manifest](evidence/g2-m6-baseline-following-manifest-2026-10-19.json)同时引用原143冻结baseline和原147，
[新指针索引](evidence/g2-m6-baseline-following-pointer-index-2026-10-19.json)将同一 measurement 去重，
分别保留早期未消费 ledger 来源与后来普通执行消费来源。没有新 RPC、活 ledger 读取或旧矩阵复测。
