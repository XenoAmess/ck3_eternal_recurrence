# 战斗推进速度与暂停边界

状态：**static-confirmed / live A/B pending**

冻结构建：CK3 `1.19.0.6`，`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

本文使用以下证据标签：

- **[static-confirmed]**：冻结原版 defines、EXE 调用链或 exact-build bridge 代码直接证明；
- **[live-confirmed]**：已经有真实 CK3 artifact；
- **[implementation-confirmed]**：当前生产代码确实这样选择或限制，但不等于相应速度已实机验收；
- **[counter-policy]**：我方准备实测的控制策略；
- **[unknown]**：仍缺 live 分布或原生 stop primitive，不能写成 production-live。

## 直接结论

[static-confirmed] CK3 在 public speed `1/2/3/4/5` 下都逐 native day 执行同一条
`army movement -> contact queue -> CCombat daily state machine`。高倍速不会少算
移动、接敌、伤害或追击；它只缩短 Python 在两个游戏日之间介入的现实时间。

所以：

1. **战斗并不要求每天暂停。** maneuver、没有撤退/改派决策的 main、pursuit 都会由原生日更自动继续；当前
   “推进一天 -> 暂停 -> rich query”是自动玩家的保守事务边界，不是 CK3 的计算要求。
2. **2 速实时粗判可行，3 速有条件可行。** 250 ms heartbeat 在 defines 的名义速率下分别有约 `4`、`2`
   个观察机会/游戏日，足以让 running-safe sentinel 发现状态 epoch 变化并请求暂停；但完整 battle-control query
   仍要求 paused，且 Windows 调度、CK3 负载和 command queue 会吃掉余量，因此必须先实测 pause overshoot。
3. **4/5 速不能靠 Python 轮询逐日兜底。** 4 速只有 `0.8 heartbeat/day`；5 速是负载相关的无节流档，现实侧
   没有有限的“下一日反应窗口”。战中 4/5 速必须由 CK3 application-main 的同日 sentinel/deadline guard 停住。
4. **“兵力悬殊”不能只由人数比证明。** exact-build 原生 power share、soldier ratio 与
   `side_strength_raw` 都不是胜率。它们可筛选 A/B 样本，不能单独授权 5 速生产直跑；当前
   `monte_carlo_ready=false`，所以 5 速 crush 仍是 research。

按 defines 计算，连续 15 个纯原生日的理论时间是：1 速 `30s`、2 速 `15s`、3 速 `7.5s`、4 速
`3s`、5 速负载相关。若一次“游戏日”事务现实里接近半分钟，主要成本来自 pause、paused rich query、Python
决策与 driver-state barrier，不是 CK3 每日战斗计算本身。减少不必要暂停比单独提高速度更有价值。

## 五档现实时间与外部反应能力

`Crusader Kings III/game/common/defines/00_defines.txt`（SHA-256
`C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807`）给出如下秒/游戏日。
Bridge heartbeat 名义周期是 250 ms；表中 heartbeat 数量只用于比较反应余量，**不是硬实时保证**。

| 速度 | defines 秒/游戏日 | 名义 heartbeat/日 | Python 在下一日界前的名义窗口 | 当前 composite selector | 战争定位 |
|---:|---:|---:|---:|---|---|
| 1 | `2.0s` | `8` | `2.0s` | tactical route/combat/retreat/Assault | 最宽外部反应窗；决策边界与未知状态回退档 |
| 2 | `1.0s` | `4` | `1.0s` | 尚不自动选择；原生命令已支持 | 第一档 battle A/B；目标是取代大部分 1 速自动阶段 |
| 3 | `0.5s` | `2` | `0.5s` | 已用于完整且远离玩家的敌军路线 | 第二档 battle A/B；只在 speed-2 envelope 闭合后晋级 |
| 4 | `0.2s` | `0.8` | 小于一个 heartbeat | 尚不自动选择；原生命令已支持 | 只能配 native deadline/sentinel；检验它是否有独立于 5 速的价值 |
| 5 | `0.0s` | 负载相关 | 无有限上界 | route-free bounded slice | 和平、无路线战争、普通围城；战斗只准 crush + native sentinel |

[implementation-confirmed] exact adapter 和 wire 已经发布 `set-speed-1..5`，`SubmitSetSpeed` 也接受完整
`1..5` 并写 native `0..4`；不需要为 2/4 速新增 ABI。当前 Python `_life_advance_timeline_policy` 只自动选择
`1/3/5`，而 controllable combat/retreat 的 horizon 固定为一日并选择 speed 1。2/4 速 A/B 只需最小 selector/harness
接线，不能把“命令存在”写成战斗策略已经 live。

## 采样词汇与 guard

下面矩阵区分两类采样：

- `HB`：running-safe 轻量 snapshot/heartbeat，名义 250 ms；它可发现 date、粗 army state、`in_combat`、
  `retreating` 等变化，但不能代替 paused battle-control query；
- `RQ`：暂停后的 rich query，读取 CombatID、phase/day、ordered participants、ledger、撤退 gate、增援等精确状态。

[counter-policy] 对每个速度 `s`，先用 live 样本建立：

- `E_s = 一次 stop request 最终 paused date 相对目标日期的实测 p100 超调日数`；
- `G_s = E_s + 1` 日的初始 guard；
- `C = 当前 paused frame 能证明的最早关键边界日`，例如接触、可撤退 day 15、增援抵达或事件 deadline；
- 允许的 running tranche 必须满足 `tranche_end <= C - G_s`。若 `E_s` 未知，则该速度不得用于依赖外部
  pause 的硬边界。

[live-confirmed] speed 1 也不是“请求一天就严格一天”：97 个一日切片曾得到
`3 x 1日 / 72 x 2日 / 22 x 3日`，正式战斗出现过同 CombatID `main/32 -> main/34`。speed 3 只有一次
最小非战斗一日链；speed 5 旧事务曾推进两日，另有 12 秒约 35 日的原始移动样本；speed 2/4 尚无 live
分布。因此所有速度都必须按最终 paused date 与 rich state 验证，不能信 speed、请求 horizon 或 ACK 本身。

## 行军、接敌与已接战执行矩阵

表中“无需逐日暂停”只描述**目标策略**；当前 production controllable combat 仍是一日 horizon、speed 1、每事务
暂停重查。凡标为 native sentinel 的格子，在该能力 live 前都不得启用。

| 阶段 | 1 速 | 2 速 | 3 速 | 4 速 | 5 速 | 必须 RQ 的边界与漏过风险 |
|---|---|---|---|---|---|---|
| 远距离行军，离最早接触日 `C` 足够远 | `HB`；`RQ <= min(7, C-G1)` 日；无需逐日暂停 | 首轮 A/B 后用同一公式；无需逐日暂停 | speed-2 GREEN 后开放；无需逐日暂停 | 仅 native date/contact guard；无需逐日暂停 | 仅 route/target 完整且 native guard；无需逐日暂停 | route/target/current Province、敌军 endpoint epoch 或 earliest contact 改变。漏过会跨过改道/避战点 |
| 接敌 guard 区 `date >= C-Gs` | 当前回 1 速并做 paused one-day contact transaction | 外部 stop envelope 未绿前降 1；未来可由 contact sentinel 保持 2 | 降 1；只有同 tick contact sentinel live 后才保持 3 | 禁止外部轮询；必须 native contact sentinel | 禁止外部轮询；必须 native contact sentinel | 同一 native day 先 movement 后 contact，不能在“抵达”和“接敌”之间插手；晚一日可能已经建战/入旧战 |
| maneuver 与 main、elapsed `<15` | 当前逐事务 RQ；目标只在 phase/roster/terminal 或 day-14 guard RQ | 第一候选：先 1 日，再 2–3 日 tranche；`HB` 触发 pause；无需逐日 RQ | speed-2 GREEN 后做 1/2/3 日 tranche；无需逐日 RQ | 仅 `run-until phase/roster/day14/terminal` | 只在 crush gate；同左 native sentinel | 参战者加入、pursuit 重开、事件/人物风险、提前终局。漏过会用旧 roster/forecast 继续跑 |
| main、elapsed `>=15`，撤退已可能合法 | RQ 后预先决定 hold/retreat；若 hold 条件稳定，不必每天停 | forecast/policy 与 roster epoch 稳定时可实时 hold；变化即停 | 同左，但必须留 `G3` 且 speed-2 已绿 | 只准 crush gate + native sentinel | 只准 crush gate + native sentinel | retreat legality、forecast epoch、roster、phase、winner、人物事件。漏过会错过本来要撤退的首个决策点 |
| pursuit | 原生自动，目标是 terminal/reopen 时 RQ，不逐日停 | 同左，首选 | speed-2 GREEN 后开放 | native `terminal-or-reopen` sentinel | native `terminal-or-reopen` sentinel | 新军加入可把 `pursuit -> main` 并清 winner；只等旧 CombatID 消失会漏掉重开 |
| done/finalizer/旧 CombatID 清理 | 1 速最多一个受控 cleanup slice | 只在 speed-1 parity 后 | 暂不需要 | 不准 | 不准 | `phase=done`、`finalized`、Result/terminal journal、CombatID 删除是不同边界；漏过会误报赢家或重复推进 |

补充的非野战边界保持不变：普通围城最适合用 `3/4/5` 做多日 tranche；Assault 先保持 1 速逐日，2 速只做
严格一日 A/B，3/4/5 暂不准入；撤退行军可在落点 guard 之前用 2/3 速，但 target/current Province、
`retreating` 或接触风险变化必须停。

## 2/3 速“实时判定”到底能做到什么

答案分成两层：

| 判定层 | 2 速 | 3 速 | 原因 |
|---|---|---|---|
| 发现 date、`in_combat`/`retreating`；sentinel live 后再发现 phase/roster epoch 并请求暂停 | **可做 A/B，最优先** | **有条件可做 A/B** | 名义分别有 4/2 heartbeat 每日；当前 HB 只有粗状态，phase/roster 仍是待施工 sentinel |
| running 状态下完成完整 participant/ledger/撤退/forecast 判定 | **当前不可** | **当前不可** | rich battle-control mailbox 明确要求 paused owner-verified frame |
| 在已证明“本 tranche 没有玩家决策”的自动阶段连续推进 | **可行候选** | **speed-2 GREEN 后的可行候选** | CK3 自己每日计算；只需在 phase/roster/deadline sentinel 停住 |
| 保证恰好在某个游戏日、接触前或 day-15 前停止 | **当前未证** | **当前未证，余量更小** | heartbeat 与 pause command 都是异步；必须使用 `G_s` 或 native same-tick guard |

因此“2/3 速实时判定”不是让 Python 在地图运行时遍历完整 `CCombat`，而是：running-safe sentinel 负责廉价发现
变化，native stop 或 pause request 负责停表，然后只在真正的决策 epoch 做一次 RQ。近期可以先用 2 速、1–3 日
tranche 得到实际收益；不需要等 4/5 速设施全部完成才开始优化。

## 为什么战斗不需要每天暂停

- [static-confirmed] 原生不存在 `keep_fighting` 动作。没有撤退或外部终止时，战斗每日自动推进。
- [static-confirmed] maneuver 固定自动运行三日；通常 elapsed whole day `15` 才允许主动撤退，live 已证明 day 14
  非法、day 15 合法；pursuit 自动运行三日并在下一日转 done。
- [implementation-confirmed] 当前 planner 战中每日 RQ 后大多仍选择下一次 `life-advance`，并未提交额外的
  “继续战斗”命令；这些暂停主要重复支付 query、pause/resume 与 driver-state barrier。
- [counter-policy] 初始优化只合并**无新决策的连续天数**：maneuver、day-15 以前且 roster 不变的 early battle、
  已预先选择 hold 且 forecast epoch 不变的 main、以及 pursuit。任何 sentinel 变化仍立即回到 paused RQ。

用这种边界，一个 15 日自动段可以从最多 15 次 pause/RQ/barrier 收缩为开头、变化点、day-14/15 与终局的
2–4 次事务；这是直接减少用户已经观察到的半分钟级事务成本，而不是理论性的优化。

## 4/5 速碾压战斗准入门

[counter-policy] 先把“碾压样本”和“生产授权”分开：

- exact native power share、双方 current fighting totals 或 `>=4:1` 的士兵筛选可以挑选 A/B 场景；
- 这些筛选值不是概率，**无论比率多大都不单独打开 4/5 速生产分支**。

正式 crush gate 至少要求：

1. exact CombatID、participant ordered roster、phase 与 forecast epoch 全部绑定同一 paused revision；
2. `monte_carlo_ready=true`；以至少 1,000 次顺序 Monte Carlo 得到 Wilson 95% 胜率下界 `>=99.5%`，
   no-resolution/失败上界 `<=0.5%`。该阈值是待 A/B 校准的 counter-policy，不是原生事实；
3. p99 预计终局日期加对应 `G_s` 内没有敌我 reinforcement/contact ETA；
4. 没有 active event、pending interaction、Assault、人物生死风险或其它玩家军需要中途操作；
5. application-main 提供 `run-until terminal-or-sentinel`：roster/phase/forecast epoch、retreat gate、event、
   terminal/reopen 任一变化就在该 native day 的稳定边界暂停；不得依赖 250 ms Python polling；
6. 同一 immutable checkpoint 的 speed-1 / speed-4 / speed-5 配对，赢家、终局日期、伤亡、撤退路线、战争分、
   人物结果与 cleanup 全部 parity GREEN。

在第 5 条 live 前，4/5 速只能作为受控 A/B arm。若 speed 4 相比 speed 3 没有稳定吞吐收益，或其超调/负载波动
没有明显优于 speed 5，就删除独立 speed-4 selector，不为“档位齐全”增加长期复杂度。

## 最小必要的新原语

现有实现已经足够做 2/3 速短 tranche A/B；为 4/5 速增加两个能力有直接必要性：4 速每个 heartbeat 名义跨
`1.25` 个游戏日，5 速无现实日长上界，而 rich query 又要求 paused。预期收益是把每游戏日的暂停/查询/持久化
合并成每个真实决策 epoch 一次。

1. running-safe `battle_tactical_sentinel_v1`：date、subject CombatID、phase/day、winner/finalized、participant
   roster epoch/hash、retreat earliest/legal、最早 reinforcement/contact ETA、event/terminal/reopen bit；它由
   application-main 的 daily journal/atomic mirror 发布，不让 250 ms worker 遍历完整可变战斗图。
2. `run-until-date-or-sentinel`：设置 absolute date 与 sentinel epoch，在每个原生日更后的稳定边界检查，满足任一
   条件即暂停。ACK 只证明提交，最终仍要求 paused state、actual date delta 与 RQ 后置验证。

```mermaid
flowchart TD
    P["[implementation-confirmed] paused rich frame"] --> B{"[counter-policy] active decision now?"}
    B -->|yes| S1["speed 1; decide and re-query"]
    B -->|no| C{"critical boundary distance > target guard?"}
    C -->|no| S1
    C -->|yes; 2 envelope live| S2["speed 2 bounded tranche"]
    S2 --> G2{"post-pause parity GREEN?"}
    G2 -->|no| S1
    G2 -->|yes; 3 envelope live| S3["speed 3 bounded tranche"]
    S3 --> N{"native same-day sentinel live?"}
    N -->|no| RQ["pause + rich query at boundary"]
    N -->|yes; noncombat deadline| S4["speed 4 capped cruise"]
    N -->|yes; crush gate| S5["speed 5 terminal-or-sentinel"]
    S4 --> RQ
    S5 --> RQ
    U["[unknown] speed 2/4 overshoot and crush parity"] -. "live A/B required" .-> G2
    RQ --> P

    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class U unknown;
```

## 最小 live A/B（本轮只设计，不启动 CK3）

### A. 五档 stop envelope

1. 选一个无事件、无接触、无人物风险的 immutable checkpoint；在同一个恢复 episode 内交错轮换速度
   `1/2/3/4/5`，每档连续做至少六次“目标一日 -> pause -> paused readback”，避免为每个样本重复冷启动。
2. 每笔记录 target date 首次到达、pause submit/ACK 时间、最终 paused date、elapsed wall time、elapsed game days、
   heartbeat/state frame 数、connection generation 与 cleanup。
3. 分别计算 `E_1..E_5`。5 速若无法得到有限、稳定 envelope，结果就是“external guard 不可用”，不为了凑齐表格
   伪造 p100。

### B. 行军/接触 parity

1. 同一 pre-contact checkpoint 做 speed `1/2/3` 配对：停止目标均为 `C-G_s`，然后统一回 1 速完成最后的
   contact transaction。
2. 核对 actual contact date、CombatID、Province、ordered sides、route endpoint 与接触前事件；不得跨过 `C`。
3. native date/contact sentinel live 后再加 speed `4/5` arm；在此之前不做盲跑接触实验。

### C. 已接战 parity 与逐日暂停消除

1. 同一 maneuver 或 early-main checkpoint，speed 1 baseline 使用当前逐日事务；speed 2 arm 依次试 1 日、2 日、3 日
   tranche。对每个 tranche 核对 CombatID、phase/day 实际 delta、ordered roster 与 casualty ledger。
2. speed 2 全绿后才加 speed 3；两档都必须在 day-14 guard、roster epoch、phase 变化、terminal/reopen 或事件时停。
3. 吞吐门：speed 2 相对当前 speed 1 至少 `1.5x`，speed 3 至少 `2x`；达不到就不增加 selector 分支。
4. crush forecast 与 native sentinel live 后，从同一 overwhelming checkpoint 做 speed `1/4/5` terminal 配对，核对
   第 4/5 速准入门第 6 条的全部结果。
5. 每个 arm 都必须保存请求前 paused artifact、最终 paused artifact、actual date delta、checkpoint 和 managed cleanup；
   harness RED 与 capability/parity RED 分开记录。

## Readiness 边界

本页把以下结论提升为 `static-confirmed` / `implementation-confirmed`：五档都执行同一逐日 native 计算；1/2/3/4/5
的 defines 日长；2/3 速的名义 heartbeat 余量；4/5 速为何不能依赖外部逐日 polling；当前 bridge 已具备 2/4 speed
primitive，但 composite battle selector 尚未使用。

仍没有 speed-2/4 战斗 live sample、五档 `E_s`、running-safe tactical sentinel、native same-day stop、speed-3 多日战斗
parity 或 speed-4/5 crush artifact。因此：

- 当前 production 战中仍按一日 horizon、speed 1、paused RQ 工作；
- speed 2 是下一档应立即实测的候选，speed 3 紧随其后；
- speed 4/5 战斗保持 research，不得写为 production-live。
