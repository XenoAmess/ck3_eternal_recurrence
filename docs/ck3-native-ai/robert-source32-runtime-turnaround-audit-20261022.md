# Source32：实际吞吐与运行周转审计（2026-10-22）

`machine_id: xenoamess-full-tower-eb9d2c1186`。审计观察截止 `2026-10-22T11:14:00Z`；执行 `tools/ck3_live_run_id.py machine` 实际 exit 0 读回上述 ID。作者 `/root/throughput_audit`，Root 委派只读审计与本小文档；没有 Git、财务、账本、Task、Steam、Game 或原生 RPC 操作，没有读取 Driver、SAVE 或 MKV 正文。本记录不增加启动门，不授予 N46 运行资格。

保存前沿仍为 **5628 / 10950 日、1082-02-15、5182 周期、SAVE11469**。G2 仍为 6/8；1 秒/日、30 年与 M6/M7 均未完成。N41 观测到的 6 日未保存且已回退；N45 首 FULL 为零 RPC 本地拒绝，新增保存日为 0。源码、测试或回执增加不能折算为这些目标的进展。

## 证据与观察范围

`C = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01`。

| 来源 | 实际读取范围与身份 |
| --- | --- |
| `C/runtime-a41/p37-responses/11474-1-result.json` | 2205 B；SHA-256 `340844de45b2daca127ca6f9ae6b316d738ade05e63e2e2a828dd07bdb27664a`；原 FULL 汇总 |
| `C/runtime-a41/p37-queue/CONTROL-TIMING-11474.json` | 24111 B；SHA-256 `f5674ac2e85808293032c301debc9b1417c00704484c806a2387c477d2d97d28`；原有可选 probe，machine ID 一致，原观察终点 04:52:45.938349Z |
| N41 原响应 11475–11534 | 54 份小于 256 KiB 的原响应；6 份约 1.15 MB 的 mercenary 响应分别读 4096 B 头，后各再读 512 B 头计算原 elapsed；没有读取完整业务载荷或复制输出 |
| [N39/N41 交接](../handover/2026-10-22-robert-source32-n39-quality-handoff.md)、[当日日报](../autonomous-agent-progress/daily/2026-10-22.md) | N41 原生产者 publish→validated receipt 墙钟 35.3458871 秒与未保存事实；未从旧响应重造生产者时钟 |
| [N45 实际闭场](evidence/robert-source32-a45-zero-rpc-closeout-20261022.json) | Root 10:40:23.181862Z 复核的 29 个来源 pins、实际 SDK/Game/Task/Screen 终态；审计另读对应小回执时间字段 |
| N45 实际 ordinary feeder | `C/runtime-a45/root_p37c23_same_game_loop_feeder100.py`，34079 B，SHA-256 `928bb4da7fb9926bdaf6a4b15e9c60dd85c0dfd9cd581897006face4571a4b5f`；只读现有 main/hold/collect_incidents，未加载或执行 |

N45 元数据根 `Q45 = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/current-saved-a45-runtime-prep01`。以下时刻来自各原 JSON 的观察时间；它们之间包含 Root 编排、人工审看与工具周转，不能全部归因于游戏加载或 CPU。

## N45：零进展运行的实际关键路径

全部时间为 **2026-10-22 UTC**。

| 时刻 | 原始来源与事实 |
| --- | --- |
| 10:11:18.509107 | `Q45/ROOT-A45-PUBLIC-PREPARE-ACTUAL01.json`：public Prepared 完成，Game 尚未启动 |
| 10:12:38.061793 | `Q45/ROOT-A45-COMPLETE-ORIGINAL-PREFIX01.json`：完整原 prefix 通过 |
| 10:13:06.894525 | `runtime-a45/ROOT-ACTUAL-GAME-LAUNCH-C23.json`：实际 Game creation_date；launch 回执观察 10:13:10.169962 |
| 10:13:29.545104 | `Q45/ROOT-A45-PLACEMENT-DISPATCH02.json`：placement exit 0 |
| 10:13:38.536784 | `Q45/ROOT-A45-DISPLAY-RUN01.json`：Task 调度 ACK，不能据此声称业务已发生 |
| 10:16:14.703614 | `Q45/ROOT-A45-FROZEN-FRAME01.json`：实际冻结帧审看 |
| 10:17:13.588732 | `runtime-a45/ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json`：SDK pair 原句柄绑定，RPC 尚未开始 |
| 10:17:52.460900 | `Q45/ROOT-A45-READINESS-SUBMITTED-11538.json`：SEM 提交；这是提交观察时刻 |
| 10:18:25.895633 | 同目录 `ROOT-A45-READINESS-SUBMITTED-11539.json`：CAP 提交 |
| 10:19:00.007200 | `Q45/ROOT-A45-WARM-BOUND-ACTUAL01.json`：warm 结果读回 |
| 10:20:01.248316 | `runtime-a45/ROOT-CAMPAIGN-MAP-ADMITTED-C23.json`：Root 地图回执 GREEN；FILETIME 字段合同实际错误 |
| 10:20:17.293439 | `Q45/ROOT-A45-FEEDER-QUALIFY-ACTUAL01.json`：qualify exit 0；当时消费者未拒绝错误合同 |
| 10:20:31.747763 | `Q45/ROOT-A45-FEEDER-RUN01.json`：feeder Task run ACK |
| 10:20:37.608442 | `runtime-a45/p37-responses/11540-1-result.json`：原 FULL 在 camera admission 处本地拒绝，AUTO/MET/SEM/SAVE 均 0 |
| 10:27:51.631054 | `runtime-a45/ROOT-SUPERVISOR-SDK-PROCESSES-EXITED-C23.json`：实际 SDK queue/application 为 1/0，不能报正常双 0 |
| 10:28:00.274625 | 录制 `completed.json`：后台最终封装完成；原引擎正常退出，非 Game 正常退出证明 |
| 10:28:32.618325 | `runtime-a45/ROOT-ACTUAL-GAME-EXIT-C23.json`：Game kernel exit 1，原 Job 强制清理，正常退出未资格化 |
| 10:30:09.998116 | `Q45/ROOT-A45-SCREEN-RELEASE-ACTUAL02.json`：Screen 真正释放；第一份失败 CAS 保留 |

Prepared→FULL 本地拒绝 **559.099335 秒**；Game 出生→拒绝 **450.713917 秒**；拒绝→Game kernel 终态又 **475.009883 秒**。Prepared→Screen 释放 **1131.489009 秒**。这一个周转约 18.9 分钟，保存收益为零。不能从这些间隔推断“CK3 加载用了 7.5 分钟”，也不能因内层只有零 RPC 就把真实周转从性能账排除。

直接原因是 Root 把 Python-only 地图回执的整数 FILETIME 写成十进制字符串，warm/feeder 路径当时接受，原 Queue 的严格整数比较最后拒绝。它与此前 owner 128 KiB 上限、SDK 源读取 1 MiB 上限一样，暴露出实际生产者到全部消费者的闭环验证不足。整图之外逐个局部通过，直到实机才发现下一个问题，放大了重启与恢复成本。守卫阻止错误继续执行有价值；反复到实机才发现合同错误是我方工程与编排问题。

## N41：35.35 秒的 6 日到底花在哪里

这是**未保存的观测窗口**，可用于定位耗时，不能作为新增保存日或目标达标成绩。原 FULL 为 30 AUTO + 30 MET，正推进 6 日；没有 SEM/SAVE。新的首 FULL 自动保存会增加 SEM/SAVE，不能与旧窗口直接作等相位提速比较。

| 互不重叠的原 RPC 分类 | 次数 | 既有 RPC 墙钟和（秒） |
| --- | ---: | ---: |
| route-contact 1 日推进 AUTO | 6 | 12.120353 |
| army-strengths 查询 AUTO | 7 | 6.083374 |
| mercenary context 查询 AUTO | 6 | 2.580442 |
| route-contact horizon 查询 AUTO | 6 | 1.247723 |
| 其他 AUTO（war-results/root-context/heir/termination） | 5 | 3.984413 |
| MET | 30 | 1.306874 |
| 全部 RPC 区间 union | 60 | 27.323178 |
| 完整 FULL publish→validated receipt 的其余墙钟 | — | 8.022709 |
| 完整 FULL | — | **35.345887** |

30 次 AUTO 合计 26.016305 秒。6 次推进均实际 1 日，使用 `exact_one_day_contact_free_speed_3`；首个 4.177723 秒，之后五个 1.490619–1.694828 秒。这个 AUTO 区间仍包含合法规划、桥接与持久化，**不是纯原生日期计时**。缺少内部实测，不能说 12.12 秒全部是游戏引擎，更不能直接提高战时速度或扩大 horizon。

原 control probe 给出了嵌套范围：

| 原 probe 区域 | 次数 | 秒 | 含义 |
| --- | ---: | ---: | --- |
| relay_total | 60 | 4.077145 | 真实结果投影、来源校验及同步 TEXT_PUBLISHED 等待总范围，完整 FULL 的约 11.54%；没有细分 ACK/poll 实测 |
| atomic_write | 729 | 0.938623 | 原 Queue 元数据写范围；与父区域重叠 |
| consume_guard | 91 | 0.191644 | 原守卫范围；本窗口不是秒级主热点 |
| pending_paths | 60 | 0.007392 | 原 pending 枚举；不能据历史 P11 慢扫描继续归因当前瓶颈 |
| classifier | 60 | 0.111542 | 原结果分类范围 |

这些嵌套秒数不能与 RPC 或彼此直接累加。`call_total` 33.074986 秒、`loop_step` 35.010580 秒都包含下层工作，不能作为额外耗时加到 35.345887 秒上。所有数字都是墙钟，未采集进程 CPU、线程调度或 OS I/O 归因。

样本观测速率为 **5.890981 秒/日**，尚未包含后续保存与退出。即假设全部控制残差和全部 MET 耗时消失，26.016305 / 6 仍约 4.336051 秒/日；只保留推进 AUTO 的极端理论算术仍约 2.020059 秒/日。这些是说明差距的上界算术，不是合法删查询方案或优化成绩。单改 JSON、扫描、ACK poll 都无法证明达到 1 秒/日。

## Root 从下一批立即执行的工作基线

1. **先建立持续保存的主干。** 当前阻塞的共享合同和真实恢复完成后，用一份新冻结图开局；首次成功保存后尽量在同 Game、同 SDK、同录制与同 feeder 中连续执行。独立性能研究、M6/M7 与事件离线分析并发推进，不为每份研究或每批测试重启。
2. **将实际失败路径提前覆盖。** 公共生成→全部来源表→固定点封包→导入→实际 warm/feeder/Queue 消费者执行同一字段合同。修共享生产者与消费者，不热改冻结图，不靠扩大所有上限或别名容错隐藏问题。这是既有 CI/合同规则的执行要求，本审计不新增准入环节。
3. **收拢 Root 顺序编排。** 已授权步骤用同一顺序执行器接续；消费真实 exit/timeout/CLOSED，再做依赖操作。独立读审与研究并行；Game、原请求、ledger 与 Task 保持唯一 writer。把状态间长时间停顿作为周转损耗记录，不能用提高线程数掩盖 Root 串行瓶颈。
4. **先 SAVE，再停止录制。** 首批复用现有自动 SEM→SAVE→小回执读回→HOLD。后续保存按原 checkpoint 合同执行；即将达到有限截止或媒体余量时提前停发新批，在 settled 边界留足实际保存、至少 15 秒尾录与退出时间。300 秒是原显式预留，不是硬实时保证，也不代表后续批可运行到最后一秒。
5. **记录两个真实效率数。** 用完整 FULL 提交→校验→实际保存读回的墙钟及保存新增日评价批效率；同时保留原 campaign T0 至当前保存前沿的累计墙钟，包含 cold、修复、等待与闭场。零保存时速率报告“未形成有效样本”，不能删去失败窗口。报告源版本、阶段范围与实际天数；不同战况、速度和保存频率不作直接因果 A/B。

## N46 首批后：同 Game 连续运行的最短操作

以下是对现有控制流的操作说明，不代表 N46 已 prepare、qualified、启动或成功。`N`、首 FULL 序号与 review deadline 都取 N46 的实际新 admission；禁止把 N45 的 11540 或旧截止复制进去。

1. 等原 feeder 的首 FULL 终态及 `root_review_hold`。确认原 FULL 为成功 bounded result，`first_full_checkpoint.status=CHECKPOINT_VERIFIED`；原 `FIRST-FULL-CHECKPOINT-<control六位>-VERIFIED.json`、`CUMULATIVE-SAVE-<cycles六位>.json`、小型累计状态与原 SEM/SAVE 响应路径相符，没有 pending。仅 STARTED、ACK 或内存日期前进不算保存。原 finalizer 已保存时不再手动重复 SEM/SAVE。
2. 读取 `N/p37-offline-batches/<control至少四位>.json` 的 `new_incidents`，交给并发离线分析者核原版定义/效果/来源 SHA 并补共享规则。原现场已合法选择并有后验的陌生事件，不等待逐条研究完成才继续；当批确有结果未知或终态故障，则沿原处理路径保留，不重放。
3. Root 完成首批实际结果与决策显示审看后，从 `N/CURRENT-SAVED-FEEDER-STATUS.json` 取得 **原样的 `first_batch` 对象**，以 create-only 原子发布 `N/CURRENT-SAVED-FIRST-FULL-CONTINUE.json`：四个字段精确为 `schema="xar.C23-first-FULL-root-continue/v1"`、`reviewer="/root"`、实际 `reviewed_at_utc`、`first_batch=原对象`。不要重算含 `hold_started_at_utc` 的对象、修改旧 marker 或先手动提交下一 FULL。实际审看时间必须在原 hold 开始后、原有限 deadline 前。
4. 保持原 Game、SDK、录制、feeder 和 Task 存活。原 `c23_first_batch_hold` 消费 marker 后只把 `first_batch_reviewed` 置真一次，`main` 按当前结果的 `next_sequence` 自动发布后续 **30 周期**有界 FULL；后续不重复首批 HOLD。只读确认状态转为 `following_actual_control` 并观察实际新响应/保存；不再运行冷 `prepare`、注册另一个 feeder 或手动争抢 NEXT。
5. 之后原 feeder 每批收集事件、保留原连续性与计时，研究者在旁路离线补齐。Root 监控实际媒体/期限及完整批结果，按原收尾路径在需维护或资格变化时才闭场；截止前停止发新批、完成需保存的 settled 状态与尾录，再停止 SDK/录制/Game，读真实终态。陌生事件本身不构成每批重启理由。

来源：[共享 feeder](../../tools/g2_saved_campaign/current_saved_campaign_feeder_v1.py) 保留 ordinary `main/status/result_for/publish_or_follow/collect_incidents`，替换冷边界；[首 FULL 保存 finalizer](../../tools/g2_saved_campaign/first_full_checkpoint_v1.py) 实现保存后 HOLD。实读 N45 ordinary 的 `c23_gate_expected` 111–113 行、continue 校验 116–126 行、HOLD 130–147 行与主循环 557–597 行；用于解释原流程，不拿旧场次文件授新场次资格。旧 `A45-FIRST-FULL-ROOT-RUN-ORDER01.json` 的 `close_after_saved_first_FULL` 是当时首批限定试跑方案，不能外推为每个正常批次都必须退出。

## 可落代码的热点与边界

当前可靠的大收益首先是减少失败恢复和重新冷启，收益要用实际新增保存日证明。尚无足够证据选择一项可立即承诺秒数的战时 query 删除方案。

- **显示发布路径**：`tools/g2_saved_campaign/decision_text_publisher.py` 的 `wait_text_published/run/validate_started` 与 `migrate_p51_decision_text_v20261019.py` 的 relay 生产者是独立边界。原调用双方都 20 ms 轮询；但 4.077145 秒 relay 总和还包含来源、进程身份、投影与写入，不能全归为 sleep。先在既有受限 probe 内细分现有调用，保留精确发布 ACK 和源/进程守卫，再考虑通知或减少同次校验重复 I/O；不另起通信平台，不假定跨帧缓存安全。即全部 relay 消失的极端上界也只有约 0.679524 秒/观测日，当前真实可实现收益 unknown。
- **战时查询/推进**：`ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py` 的 route/exact-day 路径和原完整 planner 是下一层边界。7 次 strengths、6 次 mercenary、6 次 horizon 绑定不同实际帧，零日不等于无用；同帧重复、数据生命周期与原生候选搜索未证明前不裁剪。6 次推进自身 12.120353 秒需要原 Service/Driver/Native 调用分解后再选改动，不能只调速度、horizon、战争意愿或跳过观察。
- 已有 stale combat frame 提前拒绝和 Driver bytes 单次 join 在当前仓库已经存在；不再次以“计划修复”邀功。旧 P49/P11 的 I/O/扫描结论保留其旧来源范围，不能替代 N41 的实测分布。

本轮只交付这个审计与最短续行说明，没有性能源码变更、benchmark 或实机提速资格。建议复核期限 `2026-10-29T11:14:00Z`；获得第一个完整保存窗口后追加新观察与来源，不覆盖以上 RED 或未保存事实。
