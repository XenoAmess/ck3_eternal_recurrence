# 首继承人婚姻结果：保留观察，只省内部历史复制

`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮源码与已完成小回执观察为 `2026-10-19T03:46:04Z`—`03:49:20Z`；[精简证据](evidence/first-heir-result-history-free-performance-2026-10-19.json)固定来源、结果与源码 SHA。本轮 0 Game/Native/MCP/桌面操作，未读活 Driver、SAVE 或媒体，未改运行树。当前 SDK063 已冻结，本改动只供后续 owner 正式维护采用。

首 10 日三次 `query-observed-first-heir-marriage-result-v1-private` 的 1.759878 秒不能全算重复工作。已完成的原小回执证明，它们处于同一 actor/episode/提案，但分别来自 **Native revision 7、8、18**：

| 原 AUTO 回执 | 原 Native revision | pending 的上次检查 | 实际结果 | 原 RPC 秒数 |
| --- | ---: | ---: | --- | ---: |
| 0040 | 7 | 尚未检查 | pending | 0.7392703 |
| 0046 | 8 | 7 | pending | 0.6205337 |
| 0054 | 18 | 8 | pending | 0.4000737 |
| 0081，后继结果 | 24 | 18 | betrothal，material=true | 0.4415865 |

其中前两份 compact 的 `before` 都还指向 Native 7，但 0046 的实际 `planning_source_frame` 已是 Native 8；只看旧 MET 会误判成同帧重复。原 actor 为 31254，episode 为 `native-31254-6271ac8cd441`；提案双方 40526/40408、recipient33767。0081 只证明当时原生双边婚约结果，不是未来婚姻、子嗣或联盟结果。未为读取这些结论新增查询。

`family_marriage_formal_consumer.py:551`—`:562` 已比较实际 PID/birth 与 `last_checked_native_revision`；同来源、同 Native revision 不再选结果查询，新的 Native revision 或必要 cold 身份才重新读取。原 pending/accepted_pending 结果写回上次检查，resolved 则结束义务。本轮没有发现可据此删掉的同 actor/episode/revision 结果 RPC，因此不降低结果或继承观察频率，不改原业务义务和游戏推进 horizon。

实际可省的是 [独立 action transport](../../ck3_autonomous_player/src/xar_autoplayer/bridge/observed_heir_marriage_private_action_v1.py) 的 `_paused`：它原先调用默认 `driver.take_snapshot()`，实际 Native driver 因而深复制完整 `_command_history`；此模块只消费暂停、角色、revision、日期及 exact-build provenance，没有消费 transcript。现在优先使用已有 `take_snapshot_without_native_command_history()`，旧 driver 缺该接口仍走原 fallback。实际 Native 的有限接口仍进入同一次 `take_internal_semantic_snapshot`、原 episode/声明/婚姻观察与 rollback 投影；不缓存或复用旧世界帧，不省 Native command，不改结果或 timeout。

新增一个有限 compound fixture，使用生产 Native `take_snapshot`、有限 accessor 与 `_history_snapshot`，对有/无 history accessor 的 pending、material、非 later revision、未暂停四个输入比较结果/原错误、semantic read 次数与去 request UUID 后的 Native payload：全部相等；每次仍 1 次 semantic，原历史复制 1 次→0。该夹具没有大历史或性能计时，不把消除一次 copy 夸成某个秒数收益。这个 leaf 的原 11 项 transport 验证加新 1 项共 **12 passed，0.81 秒，外层0**；保留原提交、cold 与 alliance 语义测试，未重跑整个 agent 矩阵。

后续实际维护采用只需更新该叶并冻结原 SDK/source tuple，保留原公共完整回执与可请求的历史输出。当前冻结运行没有热换，实际吞吐收益尚未测量；不能声称省掉原 1.76 秒或达到秒/游戏日目标。M3 历史资格与 G2 6/8 均不变。新增源码与小回执远小于 1 MiB，不进行新重型写入、删除或其他机器容量推断；记录复核点为 `2027-04-17T03:49:20Z`。
