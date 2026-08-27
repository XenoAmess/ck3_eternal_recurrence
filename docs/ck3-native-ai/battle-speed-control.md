# 战斗推进速度与暂停边界

状态：**static-confirmed / live A/B pending**
冻结构建：CK3 `1.19.0.6`，`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

## 结论

CK3 在 public speed `1..5` 下都逐 native day 执行同一条
`army movement -> contact queue -> CCombat daily state machine`。高倍速不会少算
战斗、移动或接触；它只缩短 Python 在两个游戏日之间介入的现实时间。当前自动玩家的
“推进一天、暂停、查询”是保守的观测策略，不是引擎要求。

因此吞吐优化的主方向不是单纯把每日事务从 1 速改成 5 速，而是把暂停点收缩到真正的
决策边界。近期最小可施工路线是先让早期战斗采用 **2 速有界多日推进**；3 速在同一
checkpoint A/B 闭合后开放。4 速只保留为有原生 deadline guard 的 capped cruise；
5 速战斗只在终局 sentinel 与高置信度碾压 forecast 都真实可用后准入。

## 原生时间定义

`Crusader Kings III/game/common/defines/00_defines.txt`（SHA-256
`C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807`）给出的现实秒/游戏日如下。Bridge heartbeat 名义周期为
250 ms，但 snapshot 构造、pipe、Python 调度、命令入队和 CK3 主线程负载都会继续
增加停表延迟，所以 heartbeat 数量不是硬实时保证。

| 速度 | 配置现实秒/游戏日 | 名义 heartbeat/日 | 当前定位 |
|---:|---:|---:|---|
| 1 | `2.0s` | `8` | 突击、撤退决策边界、观测不全或 deadline 临近 |
| 2 | `1.0s` | `4` | 首选战斗 cruise 档；先做 live A/B |
| 3 | `0.5s` | `2` | 有余量的路线/战斗 tranche；须在 2 速 GREEN 后开放 |
| 4 | `0.2s` | `0.8` | 只有原生硬截止时的 capped cruise；否则没有独立价值 |
| 5 | `0.0s` | 负载相关 | 和平、route-free 战争、普通围城；战斗仍未授权 |

现有 live 样本不能给高档速度建立硬超调上界：97 个 speed-1 一日切片曾得到
`3 x 1日 / 72 x 2日 / 22 x 3日`；正式战斗也出现同 CombatID
`main/32 -> main/34`。speed 3 只有一次最小化非战斗一日链，speed 5 旧一日事务曾
推进两日，另有 12 秒约推进 35 日的原始移动样本；speed 2 和 speed 4 尚无 live
分布。故任何未实测档都不能进入硬 deadline 分支。

## 为什么不需要每天暂停

- 原生没有 `keep_fighting` 动作。无撤退或外部终止时，战斗每天自动推进。
- maneuver 固定自动运行三日；通常 whole day 15 才允许主动撤退，live 已证明 day 14
  非法、day 15 合法；pursuit 最多再自动运行三日。
- 当前 planner 在战中每日查询后大多仍只选择下一次 `life-advance`，并未提交新的
  “继续战斗”命令。每天暂停主要重复支付 pause、query 和 driver-state barrier 成本。
- 250 ms running snapshot 能发现 date、战争、粗 army state、`in_combat` 与
  `retreating` 变化，但完整 battle control query 仍要求 paused；所以可以实时发现
  粗变化并请求暂停，却不能在 running frame 上完成丰富战术判定。

## 分阶段速度策略

| 阶段 | 当前可安全试验 | 暂停/降速边界 | 4/5 速边界 |
|---|---|---|---|
| 接触前行军 | 2/3 速有界 cruise | 在最早危险接触日之前；route/target/current province/敌军 epoch 变化即停 | 仅在有原生 deadline guard 且离危险日足够远时 |
| early battle `< day 15` | 先以 2 速跑到 day 14 或更早 sentinel | terminal、参战者、增援/接触或事件变化；day 14 必停并取完整帧 | 暂不准入 |
| battle `>= day 15` | forecast 未闭合时回 1 速 | 每个撤退/继续决策点 | 仅未来 crush gate |
| 普通围城 | 3/4/5 速多日 tranche 可做 A/B | siege terminal、敌军接触、事件或目标变化 | 当前最适合检验 4 速是否有价值 |
| Assault | 1 速逐日；2 速只做严格 A/B | 任一请求实际超过一日即 RED | 3/4/5 暂不准入 |
| 撤退 | 2/3 速跑到预计落点前 guard | current province、target、retreating 或接触风险变化 | 暂不准入 |
| pursuit | 2/3 速到 terminal | 必须识别同 CombatID `pursuit -> main` 被增援重开 | 需 native sentinel 后再议 |

同一 native day 内先完成 movement，随后才解决 contact；Python 不能在“抵达”与
“接敌”之间插手。因此接触前 guard 必须停在危险日之前，不能等双方已经同省再暂停。

## 5 速碾压战斗准入

人数比、soldier ratio 或现有 deterministic power share 都不是胜率。当前 combat-v3
仍明确 `monte_carlo_ready=false`，所以 `4:1`、`10:1` 只能筛选 A/B 场景，不能单独
授权 speed 5。正式 crush gate 至少要求：

1. exact CombatID、participant roster 与 forecast epoch 一致；
2. 至少 1,000 次顺序 Monte Carlo，Wilson 95% 胜率下界 `>= 99.5%`，失败/未结算
   上界 `<= 0.5%`；
3. p99 结束日期加 guard 内没有敌我增援或新接触；
4. 没有其它玩家军、Assault、事件或人物风险需要介入；
5. 使用原生 `run-until terminal-or-sentinel`，任一 roster/phase/forecast epoch 变化
   同 tick 停止，而不是依赖 Python 250 ms 轮询；
6. 从同一 immutable checkpoint 做 speed 1 / speed 5 配对，核对赢家、终局日期、
   伤亡、存活/撤退路线、战争分和人物结果。

## 最小新增观测与动作

当前唯一有直接功能收益的新增只读口是 running-safe
`battle_tactical_sentinel_v1`：date、subject-to-CombatID、phase/day、winner/finalized、
participant roster epoch/hash、retreat legal/earliest date、最早 reinforcement/contact
ETA 与 terminal/replacement 标志。它应由 application-main 的逐日 journal/atomic
mirror 发布，不能让 250 ms worker 遍历完整可变战斗图。

与之配套的唯一新动作是 `run-until-date-or-sentinel`。没有这个同 tick 停止原语，
4/5 速就没有硬的最大超调边界。两者都是 battle speed 优化的必要依赖，不扩张为通用
安全或全仓门禁。

## 最小 live A/B

1. 同一无危险 immutable checkpoint，对 1/2/3/4/5 各做至少六次一日事务，记录目标
   日期首次到达、pause ACK、最终 paused date、elapsed、额外超调、heartbeat 数和吞吐。
2. 每档建立 `E_s = 实测 p100 elapsed_days`，初始战术 guard 为 `E_s + 1` 日；无样本
   的速度不得进入硬 deadline 分支。
3. 做同阶段配对：pre-contact `1/2/3`；early battle/day-14 `1/2`，GREEN 后加 3；
   ordinary siege `3/4/5`；Assault `1/2`；retreat/pursuit `2/3`；crush 在 forecast
   ready 后做 `1/5`。
4. 接触前必须严格停在最早接触日前；battle 不得跨 day-15 等最早决策日；Assault
   必须恰好一日；pursuit 不得漏掉 reopen；每个 arm 最终都必须 paused、checkpoint
   和 cleanup GREEN。
5. speed 2 战斗 tranche 相对当前 speed 1 至少 `1.5x`；speed 3 至少 `2x`；speed 4
   相对 speed 3 至少 `1.25x` 且明显低于 speed 5 的时延/超调波动，否则删除独立
   speed-4 selector 分支。

## Readiness 边界

本页只把原生逐日计算等价性、五档候选定位和施工顺序提升为 `static-confirmed`。
没有 speed 2/4 战斗 live sample、没有高档 p100 overshoot、没有 tactical sentinel，
也没有 5 速 crush parity artifact；因此不能把任何新战斗速度写成 production-live。
