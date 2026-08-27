# 玩家陆军反制策略（Counter-policy）

## 目的与证据语言

- [inference][counter-policy] 本文把 [army-controller.md](army-controller.md) 中已经冻结的原版陆军 AI
  事实转换成我方 planner 的保守决策树；它描述“我方应如何行动”，不是对 CK3 原生 controller 的又一次
  反编译，也不把我方规则冒充成原生行为。
- [static-confirmed] 本文引用的原生阈值只绑定 CK3 `1.19.0.6` 与 EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；其原始证据和升级边界以
  [README.md](README.md) 与 [army-controller.md](army-controller.md) 为准。
- [live-confirmed] 文中的战争 `16777290`、敌军 `357` / `33554657` 和游戏日期 `53175984` 来自
  2026-08-24 的 exact-build paused 快照；编写本文没有读取新进程、推进游戏时间或执行 CK3 命令。
- [inference][counter-policy] 本文所有 planner 选择、失败关闭、观察窗口、合军建议和测试预期都标为
  `inference`；即使它们引用 `static-confirmed` 常量，也不因此升级为原生 static fact。
- [unknown] 原生 exact stance、assignment kind、最终评分账本、事件驱动 invalidation 表与完整 power / combat
  prediction 输入仍未闭合；任何需要这些语义的策略分支必须保持不可达。

## 可消费输入与禁止推断

| 证据 | 输入或边界 | Counter-policy 用法 |
|---|---|---|
| [inference][counter-policy] | paused snapshot 的 `date_raw`、`war_id`、`player_side`、`player_is_primary_war_leader` | 划分恢复分支、战争分支与观察纪元；不按 `date_raw % 7/14` 猜原生 timer 相位。 |
| [inference][counter-policy] | 每支军队的 full-generation `army_id`、`current_province_id`、`move_target_province_id`、`route_province_ids` | 以 `(war_id, army_id)` 独立建账，规范化 current、first hop 与 endpoint。 |
| [inference][counter-policy] | `army_state` / `army_state_code`、`in_combat`、`retreating` | 只采用公开状态值触发等待、路线重审和纪元重置，不反推内部 controller 分支。 |
| [inference][counter-policy] | exact `war_objective_province_ids`、occupation、fort、garrison 与 active siege 子域 | 识别我方 durable objective 和已有围城；能力缺失时不以 null 冒充零或“无目标”。 |
| [inference][counter-policy] | 已有 paused-to-paused `war_progress_before/after` 历史 | 复原连续 endpoint 观察；成功 restore、战争结束或 ArmyID generation 改变时截断。 |
| [static-confirmed] | 原版目标 power 曲线的输入是质量化 `OurPower` / `EnemyPower` | UI / snapshot `soldiers` 不是这两个量的 exact 替代品。 |
| [inference][counter-policy] | `soldiers` | 最多作为显示或诊断信息；不得据它选择原生 stronger/weaker、lopsided、0.5 倍猎物分支或 combat 阈值。 |
| [unknown] | `CAISubunitStack+0x48`、assignment enum、local-objective helper、跨 owner shared coordinator | 不读取、不命名、不从 endpoint 倒推 support / intercept / defend / siege。 |

- [inference][counter-policy] 对 moving 军队，正整数 target、完整正整数 route、规范化后的最后一跳等于 target
  才构成可审计 observation；缺字段、route 为空或 endpoint/target 不一致时保持暂停。
- [inference][counter-policy] 只有通过 raw-kind `0` 与 CUnit→CArmy→canonical CUnit backlink 门的 tactical army，
  才能在 route 为空时把 current province 解释为明确 `hold`；CFleet carrier 不进入 stationary 集合，也不能伪造空
  route 的 endpoint assignment。
- [unknown] 当前 schema 没有语义明确的 exact combat prediction ratio；所以本文的主动接战分支在当前版本
  必须失败关闭。

## 敌方 stance 与 objective 风险包络

- [live-confirmed] 战争 `16777290` 中玩家位于 attacker side，因此敌对一侧位于 defender side。
- [static-confirmed] 原版 defender 的默认候选包括 `defender_offensive`、`defender_defensive` 和
  `defender_desperate`；选择还依赖质量化相对 power、desperate 条件、`can_be_picked` 与 `ai_will_do`。
- [unknown] 当前稳定 snapshot 不能闭合敌军采用了哪一个 stance，也不能闭合同分、hard-coded 特例或最终
  path-cost 账本。
- [static-confirmed] 三个 defender stance 的首个 objective block 都把 wargoal 设为 `500`，并把位于
  wargoal 或 primary-defender area 的可见敌军候选设为 `250`。
- [static-confirmed] `defender_offensive` / `defender_defensive` 还给任意可见敌军 `200`；
  `defender_desperate` 没有该通用项，因此不能把“任意敌军一定被追”当成三 stance 的共同规则。
- [inference][counter-policy] 我方只采用上述 stance **并集风险包络**：战争目标区域和其中的玩家军属于高汇聚
  风险，区域外玩家军仍可能成为目标；不为敌军生成一个伪造的 exact stance 标签或数字总分。
- [inference][counter-policy] 我方自身使用词典序优先级而不是复刻原生 score ledger：先保证观察和生存，再
  保证全军路线与 cohesion，然后保留安全既有意图，最后才在围城、exact objective 与接战候选之间选择。

## 主决策树

```mermaid
flowchart TD
    P["[inference][counter-policy]<br/>取得 paused exact snapshot"] --> E{"[inference][counter-policy]<br/>全部 moving/route 字段可审计？"}
    E -->|no| B["[inference][counter-policy]<br/>保持暂停；请求完整 state"]
    E -->|yes| L["[inference][counter-policy]<br/>按 WarID + ArmyID 建 enemy endpoint ledger"]
    L --> X["[inference][counter-policy]<br/>构造 M hostile × N player route matrix"]
    X --> U{"[inference][counter-policy]<br/>任一 active route 不安全？"}
    U -->|yes| R["[inference][counter-policy]<br/>同日替换安全路线；无解则阻断"]
    U -->|no| T{"[inference][counter-policy]<br/>任一 stationary army 遭汇聚？"}
    T -->|yes| R
    T -->|no| C{"[inference][counter-policy]<br/>任一玩家军 combat / retreat？"}
    C -->|yes| W["[inference][counter-policy]<br/>不对该军 move/split/merge；<br/>其余路线全审计后最多推进一日"]
    C -->|no| H{"[inference][counter-policy]<br/>多军 cohesion 证明完整？"}
    H -->|no, same province| M["[inference][counter-policy]<br/>恢复合军；保持暂停并重观测"]
    H -->|no, separated| J["[inference][counter-policy]<br/>选择安全 rendezvous；不得再 split"]
    H -->|yes| A{"[inference][counter-policy]<br/>已有安全 active route？"}
    A -->|yes| K["[inference][counter-policy]<br/>保留 intent；不追 enemy current 改令"]
    A -->|no| S{"[inference][counter-policy]<br/>安全 active siege / Assault？"}
    S -->|yes| G["[inference][counter-policy]<br/>按既有 exact 合约推进并逐片重审"]
    S -->|no| O{"[inference][counter-policy]<br/>存在 safe exact objective route？"}
    O -->|yes| Q["[inference][counter-policy]<br/>fresh preview 后前往 durable objective"]
    O -->|no| F{"[unknown]<br/>存在语义明确的 exact combat forecast？"}
    F -. "[unknown] no exact capability in current build" .-> D["[inference][counter-policy]<br/>安全 hold / rendezvous；不主动接战"]
    F -. "[unknown] future exact capability" .-> I["[inference][counter-policy]<br/>仅按该 capability 的公开语义评估 intercept"]
    R --> Z["[inference][counter-policy]<br/>重新取得 paused snapshot"]
    W --> Z
    M --> Z
    J --> Z
    K --> Z
    G --> Z
    Q --> Z
    D --> Z
    I --> Z
    Z --> P
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class F unknown;
```

### 词典序细则

1. [inference][counter-policy] **Evidence gate**：任何 moving 状态、target 或 route 子域不完整时，禁止
   life-advance、split、merge 与主动接战；先恢复 paused exact observation。
2. [inference][counter-policy] **Global emergency**：先处理 unsafe active route，再处理已通过 canonical tactical identity
   门且受汇聚威胁的 stationary `regular/sieging` 军队；一支安全军队不能替另一支危险军队放行时间。
3. [inference][counter-policy] **Combat / retreat**：不向该军发送 CK3 不可接受或语义未知的新命令；其他军队
   仍需全局审计，之后才允许一个 bounded paused-to-paused slice。
4. [inference][counter-policy] **Cohesion**：多个玩家 stack 必须各自拥有 durable goal、全敌交叉安全和明确
   reunion；证明不全时优先恢复合军或 rendezvous。
5. [inference][counter-policy] **Current intent**：已接受且仍安全的玩家路线优先保留；敌军只改变 current 而
   target/endpoint 未变，不足以让玩家每日反向改令。
6. [inference][counter-policy] **Siege**：我方 exact siege / Assault 沿各自已冻结的进度与威胁合约处理；敌军
   sieging 只作为 soft anchor，不能当作 immobile lock。
7. [inference][counter-policy] **Objective**：safe exact wargoal / target-title objective 优先于追逐移动敌军；
   fort / garrison rank 只能在所有路线均通过安全矩阵后用于排序。
8. [inference][counter-policy] **Contact**：没有 exact combat forecast 时不主动前往敌军所在省；安全 hold、
   rendezvous 或另一个 exact objective 优先。

## Enemy endpoint epoch：7 / 14 日是 milestone，不是锁

- [static-confirmed] 普通原生 target evaluation 周期为 `7` 日；一边质量化 power 不超过另一边 `0.33` 时，
  lopsided 周期为 `14` 日。
- [static-confirmed] 原版当前 target 有 `+100`，比当前 target 更远的新候选有 `-100`；这形成黏性，但不
  排除事件驱动的提前 invalidation。
- [unknown] timer 的当前相位、jitter、逐字段映射和即时 invalidation 事件表没有闭合；snapshot 兵数也不能
  判定 lopsided。
- [inference][counter-policy] 每个敌军 epoch 保存：`war_id`、full-generation `army_id`、current、first hop、
  endpoint、target、完整 route、combat/retreat state、`epoch_started_date` 与 `last_seen_date`。
- [inference][counter-policy] target / endpoint / combat-retreat state 变化，或 remaining route 发生非自然后缀
  改道时关闭旧 epoch；自然行军只消费旧 remaining route 的前缀，且 current 前进到最后一个已消费 hop 时，
  仍属于同一 intent epoch。route 清空、ArmyID 消失、战争结束或成功 restore 也关闭旧 epoch；下一个
  observation 从 age `0` 开始。
- [inference][counter-policy] age `<7`、`7..13`、`>=14` 只表示观察已跨过哪些已证 cadence 窗；跨线本身既
  不强制我方改令，也不证明敌军已经或尚未重算。
- [inference][counter-policy] 无 exact native power 时同时维护 7 日与 14 日两个 milestone，不选择一个伪造
  的 `normal/lopsided` 标签。

```mermaid
stateDiagram-v2
    [*] --> NewEpoch: [inference] 首份完整 paused observation
    NewEpoch --> Before7: [inference] age = 0
    Before7 --> Before7: [inference] 字段不变或自然消费route前缀；每帧仍审计
    Before7 --> Crossed7: [inference] age >= 7 days
    Crossed7 --> Crossed7: [inference] 字段不变或自然消费route前缀；不声称已重算
    Crossed7 --> Crossed14: [inference] age >= 14 days
    Crossed14 --> Crossed14: [inference] 字段不变或自然消费route前缀；只证持续观察
    Before7 --> NewEpoch: [inference] endpoint/target/state或非后缀route提前变化
    Crossed7 --> NewEpoch: [inference] endpoint/target/state或非后缀route变化
    Crossed14 --> NewEpoch: [inference] endpoint/target/state或非后缀route变化
    Before7 --> Closed: [inference] route清空/ID消失/war结束/restore
    Crossed7 --> Closed: [inference] route清空/ID消失/war结束/restore
    Crossed14 --> Closed: [inference] route清空/ID消失/war结束/restore
    Closed --> [*]
```

- [inference][counter-policy] 任一玩家或相关敌军存在 tactical route、或我方 Assault active 时，观察用
  life-advance 应保持一日 **requested horizon**；其余推进也不得无观察地跨过下一个 7 / 14 日 milestone。
  requested horizon 与 timeline speed 是两个不同参数，异步暂停后的实际跨度必须按 action 的 start/end/elapsed
  和更新 paused state 验证，不能把 speed 1 冒充严格一日。
- [inference][counter-policy] 上述一日采样用于重新获得 running 帧不会提供的完整 route，不表示原生 AI 每日
  重算 target。
- [inference][counter-policy] planner 自己的 move-deferred `7/14/30` backoff、same-province stale contact
  计数和原生 target cadence 是三个不同机制，不得共用语义标签。

### 自适应时间线速度

[live-confirmed] 2026-08-27 当前正式恢复段提供了提速必要性证据：从 `restore history=2170` 到
`history=2575` 共执行 `154` 次 speed-1 与 `5` 次 speed-5 `life-advance`；其中 `97` 次属于“全部玩家军
stationary、至少一支敌军 moving、敌军 current/target/完整 remaining route 均不与玩家 current province 相交”的
远端敌军路线场景，
累计只推进 `213` 游戏日。该 97 次的实际跨度为 `3 x 1`、`72 x 2`、`22 x 3` 日，已经不是严格逐日。
独立 checkpoint wall-time 样本还显示：恢复段早期 speed-5 约 `1918` 游戏日/现实小时，后续连续 speed-1 约
`207` 游戏日/现实小时；这是约 `9.25x` 的真实吞吐差，不是理论优化。

[inference][counter-policy] 因而时间线速度采用以下词典序，不再把“任意敌军有 route”一律等同于 speed 1：

1. exact route-contact 一日 transaction、任一 controllable player route、active combat、retreat 或玩家 Assault：
   `speed=1`，保留既有 identity/route/battle/assault 后置验证；
2. `army-routes` 与 Assault 观测均可用；top-level 玩家军集合、每场战争的 controllable allied 集合及其位置完全一致；
   所有玩家军均为已知 stationary `regular/sieging`；至少一支敌军有完整可审计 route；每场战争的 allied/enemy 数组
   完整；并且所有非撤退敌军的 current、target 与**完整 remaining route 的每个 vertex**都不等于任一玩家 current
   province：保持一日 requested horizon，但用 `speed=3`，暂停后重读全部 route、combat、retreat 与 siege state；
3. 任一敌军 current/target/完整 route 与玩家 current 相交，或玩家 state、route、Assault、allied/enemy 投影有任一
   缺失/不一致：`speed=1`；深层 endpoint 指向玩家也属于相交，不能只检查 first hop；
4. active war 中没有 tactical route/Assault/combat/retreat：沿既有七日 horizon 使用 `speed=5`；和平沿既有三十日
   horizon 使用 `speed=5`。

```mermaid
flowchart TD
    P["[counter-policy] paused life-advance"] --> X{"exact contact transaction<br/>player route / combat / retreat / Assault?"}
    X -->|yes| S1["speed 1<br/>one-day requested horizon"]
    X -->|no| R{"存在 active enemy route？"}
    R -->|no| S5["speed 5<br/>war 7d / peace 30d horizon"]
    R -->|yes| E{"全部 active enemy route 完整？<br/>player/war 投影一致？"}
    E -->|no / unknown| S1
    E -->|yes| I{"enemy current / target / full route<br/>与任一 stationary player current 相交？"}
    I -->|yes or unknown| S1
    I -->|no| S3["speed 3<br/>one-day requested horizon"]
    S1 --> V["paused postcondition<br/>按实际 elapsed 重读战术状态"]
    S3 --> V
    S5 --> V
    O["[unknown] speed-3 active-war overshoot envelope"] -. "live A/B 后校准；不放宽关键 transaction" .-> S3
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class O unknown;
```

[live-confirmed + counter-policy] 当前 production 尾帧是新门的反例，不得为了眼前提速把深层 endpoint 漏掉。
`history=2575` 的 after snapshot 中，玩家主军 `33554797` 在 Province `5598` stationary siege，另外五支玩家军在
`2619` stationary；敌军 `117440838` 位于 `496`，完整 target/route 为
`5598 / [5565,5566,5567,5568,5576,5577,753,5684,5683,5596,5597,5598]`。其 endpoint 最终指向玩家，
另一敌军 `83886265` 已在 `702` siege、route 为空。把这个真实 paused shape 输入新选择器，结果必须是
`horizon=1`、`speed=1`、`timeline_policy=enemy_route_imminent_or_unknown`；这已由对应 production-shape fixture
锁定。新分支实际解除的是同一 artifact 已出现的 `97` 个 full-route-disjoint 帧及未来同类帧，不是这个确有来敌
终点的尾帧。在获得 isolated active-war speed-3 elapsed 分布前，不声称它严格停在一个日界，也不把 speed 3 扩展到
上述 speed-1 关键分支。

[live-confirmed + counter-policy] `history=2421` 的 after snapshot（也是 `history=2424` advance 的 before shape）是
真实命中例：六支玩家军仍分别 stationary 于 `5598 / 2619`；敌军 `83886265` 位于 `5740`，target/remaining route
为 `701 / [5739,5733,5734,5735,5731,5732,701]`，另一敌军 `117440838` gathering 于 `496` 且 route 为空。
全部敌军 current/target/route vertex 都与两个玩家 current province 不相交；同一 paused shape 的 fixture 因而返回
`requested_horizon_days=1`、`timeline_speed=3`、`timeline_policy=remote_enemy_route`。原 production action 仍是旧策略的
speed 1，实际推进两日；fixture 只证明 selector 与 paused 后置字段，不把合成的 speed-3 elapsed 当成实机调度证据。

[live-confirmed + static-ready] stationary `target=current` query 已证明会在 interval projection 前返回
`route_unavailable`；但成功的 moving horizon 已发布完整 hostile timed routes，可以按同一闭区间语义重投影同帧 hold 的
一日 contact 关系。该共享-timeline counter-policy 尚待 live replay，production action surface 也仍只对已 committed player
route 发布 proof-bound advance，而且 speed-3 异步暂停的最大 overshoot 尚未闭合。因此，若要继续加速 endpoint 最终指向
玩家的具体帧，下一入口仍是先用隔离 A/B 冻结 speed-3 elapsed envelope，再以 timed arrival 与该 envelope 的明确余量授权；
不能用 route 长度或 first hop 代替 ETA，也不能把现有 speed-1 exact transaction 直接改成 speed 3。

### 2026-08-28 同 checkpoint live A/B：查询提速已闭合，speed 3 仍未命中

[live-confirmed] 三轮 A/B 都从 `date_raw=53209560`、SHA-256
`A8DD4034C32856B8D1E05D6B834BBBF3C51AA74DA038BB22A0CA23A998AD76CF` 的同一 checkpoint 起跑，只替换 Python
snapshot/transcript 复制实现，不改变上述时间线选择词典序。运行段依次为：

| runtime | 运行段 | query 首 / 尾 | life-advance 首 / 尾 |
|---|---:|---:|---:|
| `79b8d2a` | `48.134s` | `3.398s / 2.579s` | `5.065s / 4.600s` |
| `e0688c7` | `44.875s` | `3.317s / 2.516s` | `4.583s / 4.111s` |
| `9ff04ae` | `24.684s` | 约 `0.050s / 0.068s` | `4.569s / 3.643s` |

[implementation-confirmed] life history 完整复制从 `9 → 1 → 0`；planning transcript 从 `1 → 0`，局部耗时约
`600.637ms → 5.813ms`；termination query 内部从 `3 → 0`，局部耗时约 `1815.527ms → 1.852ms`。完整数据、
durable/cleanup 合同与验证矩阵见 [testing-workflow.md](../testing-workflow.md)。这些变化解释 query 的数量级下降；它们没有修改
原生路线、敌军风险或 speed selector，也不证明 life-advance 剩余的 3.6–4.6 秒成本已经消失。

[live-confirmed + counter-policy] 最新 `9ff04ae` 轮完成 `12/12` turns，其中 `6` gameplay、`6` queries、`2` checkpoints。
六次 gameplay 全部命中 `timeline_policy=player_tactical`：玩家仍有已提交的 12-hop route，敌军仍在追尾；selector 因而六次都用
`speed=1`，各推进 `1` 游戏日并回到 `paused=true`。最终 checkpoint 为 `date_raw=53209704`、SHA-256
`39379D0224788198FECCCA82DA4B7B7257DB7E1AEE6B3750F62AA845E312678A`，cleanup 全绿。这是真实的 speed-1 安全回退
production evidence，不是 speed-3 live evidence。

[unknown] speed 3 的 production gate 仍未满足：本轮没有任何 `remote_enemy_route` 起始帧，因此没有实际 speed-3
`elapsed_days`、overshoot 或 after-frame contact envelope。下一轮应继续正常 G1，而不是人为取消玩家路线或避开追尾来制造样本；
只有战局自然进入完整 route-disjoint 帧时，才按既有 gate 执行 speed 3 并记录真实 paused post-state。

## M hostile × N player route matrix

- [live-confirmed] 同一 current province 的敌军可以有不同 endpoint：战争 `16777290` 中 `357` 和
  `33554657` 都从 `2581` 出发，但 endpoint 分别为 `2596` 与 `2587`。
- [inference][counter-policy] 因此每一个玩家 route candidate 必须分别与每一个非 retreating hostile 的
  current、target、first hop、完整 route 和 endpoint 审计，不能把敌军合并成一个视觉 blob。
- [inference][counter-policy] 单格至少检查 enemy current on route、enemy target on route、shared next hop、
  future route intersection 和 opposite directed edge。current/same-day 冲突直接 unsafe；只有 future geometric
  intersection 可以在推进**一个日界**前交给 exact timed horizon 进一步判定，不能把“route 中以后会经过”自动写成
  “本日必接触”，也不能把一日 safe 反推成长路线永久安全。
- [inference][counter-policy] 不使用“每个敌军只会追一支玩家军”的 matching 假设；两支敌军可以分别压迫两半，
  也可以共同汇聚同一 stack。
- [unknown] endpoint 不公开 objective kind；`33554657 → 2587` 不能被命名为 support、intercept、defend 或
  staging。

```mermaid
flowchart LR
    W["[live-confirmed] war 16777290"] --> E1["[live-confirmed] hostile 357<br/>2581 → 2587 → 2597 → 2596"]
    W --> E2["[live-confirmed] hostile 33554657<br/>2581 → 2587"]
    W --> P1["[live-confirmed] player main<br/>2596 → target 2604"]
    W --> P2["[live-confirmed] player sibling<br/>2596 → target 2600"]
    E1 --> C11["[inference] audit 357 × main"]
    E1 --> C12["[inference] audit 357 × sibling"]
    E2 --> C21["[inference] audit 33554657 × main"]
    E2 --> C22["[inference] audit 33554657 × sibling"]
    C11 --> A["[inference] union conflicts"]
    C12 --> A
    C21 --> A
    C22 --> A
    A --> S{"[inference] all cells safe<br/>and cohesion proven?"}
    S -->|yes| K["[inference] candidate may remain active"]
    S -->|no| R["[inference] reroute / rendezvous / merge / block"]
    E2 -. "[unknown] assignment kind" .-> U["[unknown] do not name"]
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class U unknown;
```

- [inference][counter-policy] 非 exact-objective 的敌军所在省也必须经过接战能力闸；不能用“允许 enemy at
  destination”绕过 route matrix。
- [inference][counter-policy] 每支玩家军最终都要有 `escape/reunion`、`safe siege`、`exact objective` 或
  `explicit safe hold` 之一；另一支军有安全 active route 不足以替一个无目标或受威胁 stack 放行时间。

### 2026-08-28 多军团 horizon blocker：复用同帧 hostile timeline

[live-confirmed] 最新正式长跑的 paused `native:167` / revision `168` 在 `date_raw=53212728` 有六支可控军。
moving Army `33554818` 与 stationary Army `150995278` 同在 Province `8658`；前者的 fresh one-day horizon
已经是 true，后者无 target、route 为空。enemy `117440646` 的完整 timed route 虽含 `8658`，但原生
arrival 是 `53215944`，距当前 `134` 游戏日。旧 `_stationary_province_threats` 只看 route membership，遂把后者
当成立即 threatened，返回
`native_war_route_contact_horizon_global_blocked / complete-global-route-contact-horizon`。报告 SHA-256
`FC7D4E5069C84A4D10A3E5359A387C3F9BD5CD422FFE20D45ACCEB0ADDD4DF90`，first-blocker SHA-256
`AB9FDD76D0251070F1A12AAE8CAE51C2CB23B0CA675EF229DF42724C35500AB0`；原生接触与 interval 证据详见
[army-contact-resolution.md](army-contact-resolution.md)。

[live-confirmed] commit `1048a45` 的 replay 随后确实广告并提交了 stationary literal
`query-route-contact-horizon-v1-150995278-to-8658-h-3-83886265-117440646-117440838`，但 exact-build reader 返回
`route_unavailable / CK3 could not build a complete contact route`。report SHA-256
`396003CC8C325C0D2B8B02082E0F2B19831DC52E90922354725234FD012655F1`，first-blocker SHA-256
`04017F1AE0D414EA755168F7D534481D4B3B6A0476064645E7AA7F55A219ACC8`。wire/schema 虽允许空 subject timeline，
native `BuildSubjectRouteTimeline` 却会在 same-current return 之前先要求 move mode 与 effective origin；所以“schema 可接收
target=current”不能升级成“exact-build reader 能为 regular hold 生成该结果”。

[inference][counter-policy] 这个 blocker 仍不需要新的 native observation schema。前一条成功的 moving query 已在同一
paused frame 返回完整 hostile scope 的每条 `hostile_routes` 与 arrival dates；其发布还受完整 snapshot
completion/current/previous 相等门禁约束。最小施工改为：

1. 保留 moving Army `33554818` 的 fresh、`one_day_contact_free=true` horizon，并取得其中全部 hostile timelines；
2. 从同一 snapshot 选出 `regular/sieging`、无 target、空 route、非 combat/retreat 的 controllable rows；不再为它们
   广告或提交 `target=current` query；
3. planner 与 advance advertisement 共用一个 helper，逐字复刻 `BuildTimelineIntervals` 的闭区间：stationary Province
   占用 `[start,end]`；hostile current 占用到 first arrival，每个 route Province 从自身 arrival 占用到 next arrival/end；
4. hostile 已在该省或任一该省 arrival `<= end`（包括恰在一日末端）即 unsafe；stationary 没有 edge，故此派生层只产生
   `same_province`，moving subject 的 `opposing_edge` 仍以原生 horizon 为准；
5. 只有 moving proof、所有派生 stationary rows、其余 geometric-safe rows与无其它 combat/retreat 条件全部成立，才广告并
   执行既有 moving-proof-bound one-day advance；任一 frame binding、timeline、hostile scope 或 army shape 不完整都阻断。

[inference][counter-policy] “safe”在这里严格只表示当前 active routes 下下一日没有接触，不表示战力有利、长期 hold
安全、敌军 134 日内不会 retarget，也不授权 speed 2..5。共享 hostile timeline 是同帧原生观测上的 counter-policy
派生，不冒充 stationary ArmyID 自己取得了 subject-bound native proof；没有 exact combat forecast 时也不把 contact 改写成
“可以打”。

[production-live loop] 共享 hostile timeline 已由 `e619219` cold canary 完成 `12/12` turns、4 次一日推进、2 个
checkpoint 与 cleanup GREEN；正式 run 随后又连续推进 38 日。因此 GEN-018 的时间维度丢失已经关闭。正式 run 新暴露的
不是“所有军队都 stationary”，而是一个表面 stationary、实际与 embarked 主体连续同省移动的 non-orderable CUnit；它不能
继续套用独立 hold 模型。

```mermaid
flowchart TD
    P["[live-confirmed] paused frame<br/>M hostile × N controllable"] --> G["[counter-policy] complete geometric audit"]
    G --> C["[live-confirmed] moving 33554818<br/>fresh one-day proof=true"]
    C --> H["[live-confirmed] extract complete hostile routes<br/>from the same fresh result"]
    G --> T{"[counter-policy] stationary current appears<br/>in hostile current/target/route?"}
    T -->|no| GS["[counter-policy] geometric-safe row"]
    T -->|yes| X{"[counter-policy] closed stationary occupancy overlaps<br/>same-frame hostile intervals?"}
    H --> X
    X -->|yes / unavailable / stale| B["[counter-policy] reroute / rendezvous / merge / block"]
    X -->|no| SS["[counter-policy] derived stationary row safe one day"]
    C --> A{"[counter-policy] conjunction over every controllable row<br/>and no other combat/retreat?"}
    GS --> A
    SS --> A
    A -->|yes| D["[counter-policy] existing moving proof-bound<br/>one-day advance"]
    A -->|no| B
    D --> R["[counter-policy] paused re-observe all armies"]
    F["[live-confirmed] stationary target=current query<br/>route_unavailable"] --> N["[counter-policy] do not issue a second query"]
    N --> H
    U["[unknown] shared-timeline production result"] -. "[unknown] fresh replay" .-> A
    V["[unknown] future all-stationary advance shape"] -. "[unknown] only if a real blocker appears" .-> D
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class U,V unknown;
```

### 2026-08-28 CFleet carrier：从 tactical set 源头排除

[live-confirmed] `date_raw=53213736` 时，CUnit `150995278` 与 `33554818` 同在 Province `951`；后者继续沿
`[8672,5696,5709,704,5715]` 航海，前者仍被旧 reader 显示为 `regular / target=null / route=[]`。回看 history 可见两者
连续 59 个游戏日逐省同步。对前者提交的 186 个 route previews 均为 `army_not_move_ready`，合计 `572.765s`。
完整 artifact/hash 与 raw-kind/CFleet 原生树见 [army-contact-resolution.md](army-contact-resolution.md)。

[counter-policy] tactical army 集合必须先服从原生 movement/contact identity gate：只接受 raw-kind `0`，再闭合
`CUnit+0x178 → generation-valid CArmy → CArmy+0x124 == 当前完整 CUnitID`。raw-kind `1` 的 CFleet carrier 是运输表示，
不是第二支 stationary army；它既不参加 M × N stationary threat，也不接受 route preview。无需把 canonical 主军的 horizon
“转授”给 carrier，因为 carrier 根本不进入独立战术主体集合。

[counter-policy] 仍保留成本止损：若某个真正进入 tactical set 的 threatened CUnit 在同一 paused revision 第一次 preview
就被原生 move-mode/state gate 拒绝，立即保留 exact rejection stage 并停止其余 target 枚举，返回窄观测 blocker；不得再用
不同目标重复测试同一 subject 的 orderability。该止损本身不授权推进时间或接战。

```mermaid
flowchart TD
    U["[static-confirmed] CUnit row"] --> K{"raw-kind == 0?"}
    K -->|no / CFleet-linked| X["[counter-policy] exclude from tactical set"]
    K -->|yes| C{"CArmy full ID valid<br/>and +0x124 backlink matches?"}
    C -->|no| X
    C -->|yes| P["[counter-policy] publish ArmySnapshot"]
    P --> T["[counter-policy] route / stationary threat audit"]
    T --> D{"first native preview deferred?"}
    D -->|yes| B["[counter-policy] preserve rejection stage<br/>stop target scan"]
    D -->|no| A["[counter-policy] continue normal route policy"]
```

## Cohesion、Split 与 Merge

- [static-confirmed] 原版 AI 每 `14` 日评估 split/merge；低于 preferred stack size 的 `0.75` 尝试 merge，
  高于 `1.1` 尝试 split，并以最强对手约 `1.5` 倍等质量化 power 目标计算 stack size。
- [unknown] 当前稳定 snapshot 没有原生 preferred stack size、质量化 power 或 exact combat prediction，不能
  直接移植这些数字。
- [static-confirmed] 原版敌军目标 power multiplier 在目标约为本 stack power 的 `0.5` 时达到 `1`；接近或
  超过本 stack power 时降到 `0`。
- [inference][counter-policy] 把一支接近敌 stack power 的玩家军拆成两半，可能把一个低吸引目标变成两个理想
  猎物；multi-stack 敌军又可以给两半不同 endpoint，所以默认禁止自动 split。
- [static-confirmed] `CHASE_MIN_SIZE=500` 会阻止原版费力追逐更小 stack，但 wargoal、路径、相邻 combat 和
  其它 objective 仍独立存在。
- [inference][counter-policy] “拆到 500 以下”不是安全证明，也不能绕过 cohesion gate。

### 保持已拆状态的最小证明

1. [inference][counter-policy] 两半各自有 exact、durable 且不是仅为风筝敌军 current 的目标。
2. [inference][counter-policy] 两半的完整 route 分别通过全部 hostile 的 M × N audit。
3. [inference][counter-policy] 存在语义明确的 exact combat forecast，且每一个可能接触 pair 都满足我方公开的
   安全条件；`soldiers` 不能代替。
4. [inference][counter-policy] 有不穿越 hostile current / route / endpoint 的明确 rendezvous province 与
   重聚路线。
5. [inference][counter-policy] 任一证明 unavailable 时，若两军同省则优先 merge；若已分开则不得再 split，先
   建立 rendezvous。

- [inference][counter-policy] 已闭环的 generation-bound split / merge primitive 应保留为显式恢复能力；当前
  planner 不应因为缺少自动 split 门槛而删除底层能力。
- [inference][counter-policy] Merge 用于恢复拆分时，原本需要保留的主军应为 destination；只有 exact literal
  当前被广告、两军同省且非 combat/retreat 时才提交。
- [inference][counter-policy] `merge_submitted` 不是完成；至少要重新观察 destination ID / owner / province
  保留、source 消失和玩家可控 ID 集合精确减少 source。完整边界见
  [ck3-native-merge-contract.md](../ck3-native-merge-contract.md)。
- [inference][counter-policy] Merge 后不假定 destination 继承哪条活动 route；保持暂停，取得新 snapshot，
  再用当前 origin/date fresh preview 后才允许推进。

## Siege、Combat 与 Retreat 行为包络

- [static-confirmed] 原版已在目标省 sieging 的 unit 有 `+500`，继续本 stack 的 ongoing siege 有 `+80`，
  会开始新 siege 有 `+70`；打断有 occupation 价值的 ongoing siege 有基础 `-100` 惩罚。
- [static-confirmed] 没有 siege weapons 时，只有预计至少还需 `30` 日才结束，相关 AI subunit stack 才允许
  放弃 siege。
- [static-confirmed] 解围候选有 `+190`，开始 combat 有 `+80`；接近胜利时 easy battle、跨 stack 救援和
  battle multiplier 仍可能压过 siege 黏性。
- [inference][counter-policy] 因此敌军 `sieging` 只构成 soft anchor：可用于规划行动窗口，但每次 target/route、
  combat/retreat、求援或战争分变化后必须重新审计，不能假定其固定 30 日。
- [inference][counter-policy] 我方 active siege / Assault 继续使用 exact SiegeID、进度、garrison、eligible
  besieging strength 与一日/七日后置条件；不把原版 AI 的 score 常量混入我方 siege parser。

| 证据 | 原版边界 | Counter-policy 允许的结论 |
|---|---|---|
| [static-confirmed] | 普通 combat prediction ratio `>=0.5`；desperate `>=0.4` | [inference] 敌军可能接受的接战区间；当前无 exact ratio，不能据兵数主动接战。 |
| [static-confirmed] | prediction `<0.66` 请求增援，达到 `0.75` 停止继续请求 | [inference] 单支敌军的暂时优势不能排除另一 stack 加入；不实现伪造的 help 状态。 |
| [static-confirmed] | 当前 unit stack 被敌方 out-powered 达 `ASK_FOR_HELP_OTHER_STACK_TROOPS_RATIO=1.5` 门槛时尝试请求附近友军；不把该 define 猜成确定分子/分母公式 | [inference] M × N 审计不能只看准备接触的一个敌军。 |
| [static-confirmed] | siege progress `>=0.6` 时，打断 siege 救援门槛更保守为 `1.7` | [inference] 高进度围城可能更黏，但不是 immobile lock。 |
| [static-confirmed] | prediction `<0.45` 且另处至少有本军 25% strength，或两省内有更好地形时满足 retreat 条件 | [inference] 只在公开 `retreating` 变真后按 retreat 处理，不预测目的地。 |
| [static-confirmed] | stand-and-fight 最长 30 日，放弃后 45 日 cooldown | [inference] 只作敌方行为上界背景；当前不实现内部 controller 状态机。 |

- [unknown] combat 开始后的 exact controller 调度、撤退命令构造和目的地评分仍未闭合；Mermaid 主树中的
  future exact forecast 分支不得由这些阈值自行解锁。

## 战争 `16777290` 的初始 paused 决策 / 日期 `53175984`

- [live-confirmed] 两支玩家可控军仍同在省 `2596`；主军有 target `2604`，拆出的 sibling 有 target `2600`。
- [live-confirmed] 敌军 `357` 位于 `2581`，route 为 `[2587,2597,2596]`，endpoint 是玩家旧位置 `2596`。
- [live-confirmed] 敌军 `33554657` 位于 `2581`，route 为 `[2587]`，endpoint 为 `2587`。
- [live-confirmed] 两敌 endpoint 已分化；`2587` 同时是 `357` 的 first hop 和 `33554657` 的 endpoint hazard。
- [unknown] 当前资料没有给出两个玩家 route 的全部 hop、每半对两敌的 exact combat forecast、两 endpoint 是否
  都是 durable objective，也没有 `33554657` 的 assignment kind。
- [inference][counter-policy] “两条路线暂未发现几何冲突”不等于“两个半栈独立安全”；当前不满足保持 split 的
  最小证明。
- [inference][counter-policy] 建议在这个 paused frame 把 sibling merge 回原主军，原主军作为 destination；若
  exact merge literal 不可用或原生 validator 拒绝，则保持暂停并改走 rendezvous，不推进时间。
- [inference][counter-policy] Merge 后先验证 source 消失与 destination 保留，再把 route 当作需要重新观察；
  不假定继续前往 `2604` 或继承 sibling 的 `2600` intent。
- [inference][counter-policy] 下一步只在 fresh preview 通过全部 hostile matrix 后离开 `2596`；避免穿过
  `2587`，并由 exact objective 状态决定 `2604`、`2600` 或其它候选，不能仅凭 endpoint 拍板。
- [inference][counter-policy] `357` 的 current-target `+100` 黏性可能让其暂时继续前往旧位置 `2596`，但这是
  可利用的观察窗口，不是 7 日安全承诺；任何提前 target/route 变化都立即重开 epoch。

### 执行结果 / 日期 `53176104`

- [live-confirmed] planner 选择 `merge-armies-83886341-with-16777558`；暂停快照证明 sibling 消失且原主军
  保留，日期未在合军事务内推进。
- [live-confirmed] Merge barrier 拒绝合军前 preview；合军后 fresh preview 与 observed remaining route 均为
  `[2595,2603,2604]`，随后所有推进均使用 speed 1 的一日 paused-to-paused 切片。
- [live-confirmed] 第五个切片后主军抵达 `2595`，remaining route 自然消费为 `[2603,2604]`；这是 P02
  的同一 intent epoch，不因 route 前缀被正常消费而重开。
- [live-confirmed] 同一切片后 `357` 的 endpoint 从 `2596` 改为 `2595`，新 route 为
  `[2587,2599,2598,2595]`；旧 endpoint epoch 当帧关闭，新 epoch 从 `53176104` 开始。
- [inference][counter-policy] 玩家 `[2603,2604]` 与当前两敌 remaining route 暂无几何交叉，但 `357`
  endpoint 等于玩家 current，且没有双方 ETA/exact combat forecast；因此仍只允许一日推进并在每帧重审。
- [unknown] target 变化的确切内部触发未知；实现只消费已发布的新 target/route，不把它命名为即时追踪或
  定时器触发。
- [live-confirmed] 到日期 `53176248`，玩家自然抵达 `2603`、remaining route 只剩 `[2604]`；`357` 同帧
  再把 endpoint 改成 `2603`，并发布一条不与玩家 `[2604]` 相交的长 remaining route。counter-policy
  关闭 `2595` epoch、建立 `2603` epoch，但不追敌 current，也不由两次相关观察推断内部触发器。
- [live-confirmed] 日期 `53176344`，`357` 又把 endpoint 改为玩家 destination `2604`。暂停态重新预览全部
  exact 目标后，每条 native route 都因边内 effective origin 而先经过 `2604`，因此都与敌 route/target
  冲突；planner 返回 `native_war_no_safe_exact_route`、`selected_step=None`，没有用 advance 逃逸。
- [inference][counter-policy] 这个 live 分支验证 P03/P07/P08 的组合门：敌 endpoint 提前变化立即关闭旧
  epoch；所有候选做完整 M × N 审计；没有 exact combat forecast 时，共享终点不能作为主动接战例外。

### 生产 owner 的 checkpoint 重放 / 日期 `53176176`

- [live-confirmed] 2026-08-26 的 default-OFF production12 `native-auto-run` 从 `53176104` 连续完成三次一日
  paused-to-paused 推进，并由生产 owner 在 `53176176` 自动物化 checkpoint；ArmyID `83886341` 位于 `2603`、
  remaining route 为 `[2604]`，敌军 `357` 位于 `2583`、target 为 `2604`、remaining route 为
  `[2594,2599,2598,2595,2603,2604]`。
- [live-confirmed] 独立 PID `34084` 随后从该 checkpoint 恢复到同一日期、CharacterID `29829` 与战争
  `16777290`。对 `2568/2585/2596/2600` 的 fresh preview 分别返回
  `[2604,8759,2602,2591,2589,2579,2574,2572,2568]`、
  `[2604,2603,2595,2598,2599,2587,2585]`、`[2604,2603,2595,2596]` 与
  `[2604,2603,2595,2600]`；四条路线都至少经过敌军 target/route 中的 `2604`。
- [live-confirmed] planner 因而返回 `native_war_no_safe_exact_route`，没有提交 move 或 advance；生产 owner
  仍按 `stop_event -> native-session stop_tracked -> driver.close` 完整回收。该结果证明 checkpoint 可恢复，也证明
  当前整局循环在真实的边内 committed movement/contact 局面会被缺失的 exact forecast 阻断。
- [inference][counter-policy] 在该次安全停止时，下一项施工依赖不是放宽 M × N 冲突矩阵，也不是用 base power 或
  soldiers 猜输赢；当时应先补能区分“完成已承诺边后尚有脱离窗口”与“不可避免接触”的 exact-build contact/ETA
  观测。下节已闭合 arrival 与一日脱离窗口；当前依赖收窄为 same-day candidate/stored order 的 actual-contact
  scope，随后才是在确实需要接战时补语义明确的 exact combat forecast。本节既有 fail-closed 分支保持不变。

### Exact route-contact 一日窗口实机闭合

- [live-confirmed] 首次从日期 `53176176` 重放时，typed route ticket 在 application-main 执行前仍处于
  `queued`，被通用 2 s 等待取消；exact EXE SHA、adapter 与 timing bindings 均已通过。生产 worker 改为让同一
  queued ticket 最多存活 8,000 ms，进入 `executing` 后按 2,000 ms slice 等到 terminal；2,200 ms delayed-pump
  fixture 证明原 ticket 只执行一次且可回收。
- [live-confirmed] 最终生产 DLL
  `7AF3472A67218BDC407693D93A51826E2D99E29DB101EF724DC0B10FA60DC524` 在 2.466 s 内返回 `available`，
  mailbox `executed_requests` 从 `0` 增至 `1`。ArmyID `83886341` 到 `2604`、完整敌军 scope
  `[357,33554657]` 的 exact timeline 给出 `one_day_contact_free=true`，于是 planner 只授权 speed 1 的一日
  paused-to-paused 推进 `53176176 -> 53176200`；war projection 确有变化，未把 command ACK 冒充进展。
- [live-confirmed] 推进后 checkpoint SHA-256 为
  `51A3C202D6785988F3E3E7F028B64C4F0949DD83A4E32F3222E286B110224BE8`，normal managed cleanup 完整证明。
  因而 production arrival/一日 route-contact horizon 已闭合；`actual_contact_scope_ready` 仍为 `false`，同日
  candidate/stored order 与真实 contact sides/order 不能从本结果推断。

[live-confirmed continuation] 随后从 `53176200` 连续完成 `12 + 30 + 90 + 60 + 15` turns 的五轮 qualified
托管冷恢复；连同首轮 3 turns，共 `210/210` successful turns、78 个 visible gameplay turns，并从 `53176176`
累计推进 75 game days 至 `53177976`。循环先后使用多次 route horizon、普通 clear-route advance、到达 `2568`
后的逐候选 preview、对 `2600` 的 candidate contact horizon、move submission 及周期/最终 checkpoint；没有
recovery，所有 cleanup proven，当前 checkpoint SHA-256 为
`12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D`。这证明 post-fix 循环可以持续产生可见游戏
进展，但不代表整局完成，也不使 `actual_contact_scope_ready` 变为 `true`。

### 连续恢复的有界失败入口记忆

- [live-confirmed] 从同一 checkpoint origin `2598` 已观察到两条最终进入无安全出口并执行 restore 的入口：
  `target=2585, route=[2599,2587,2585]` 与
  `target=2568, route=[2599,2587,2581,2568]`。
- [live-confirmed] 第二次 restore 后，旧的单条 `native_rollback_war_failure` 只保留较新的 `2568` 入口；若只
  消费这个字段，planner 会重新选择已经封口的 `2585` 分支。
- [inference][counter-policy] 失败入口记忆严格限制为同 episode、checkpoint、war、army 和 restored origin 下
  最新两条；按 target + route 逐项相同才阻断，fresh route 变化立即放行，第三条更旧记录淘汰。这是两次连续
  restore 的最小闭环，不扩展成通用学习或永久目标黑名单。
- [inference][counter-policy] factual command history 仍在 restore anchor 截断；失败入口属于 advisory，不能
  复活已回滚分支中的 score、siege completion、cooldown 或 move intent。

```mermaid
flowchart TD
    R["[live-confirmed] successful restore"] --> D["[inference][counter-policy] derive discarded-branch entry route"]
    D --> S{"[inference][counter-policy] same episode/checkpoint/war/army/origin?"}
    S -->|no| C["[inference][counter-policy] start a new bounded list"]
    S -->|yes| U["[inference][counter-policy] exact target+route dedupe; newest first"]
    C --> K["[inference][counter-policy] retain at most two entries"]
    U --> K
    K --> P["[inference][counter-policy] fresh preview compares every retained entry"]
    P -->|exact match| B["[inference][counter-policy] block this route only"]
    P -->|route changed| A["[inference][counter-policy] allow normal M×N audit"]
    B --> N["[inference][counter-policy] preview another exact objective or remain paused"]
```

### Restore 后的 14 日 milestone 实证

- [live-confirmed] 新分支中 `33554657` 从 `53174328` 到 `53174640` 保持 endpoint `2604`，并在
  `53174664` 改回 `2543`；两个端点起始观察相差恰好 14 游戏日。
- [inference][counter-policy] ledger 只把它记录为“已跨普通 7 日与 lopsided 14 日两个 milestone，随后观测到
  endpoint 变化”；它不会反推 native power 比、stance 或 timer identity。
- [unknown] 改令是否由 lopsided timer、普通评估叠加、objective invalidation 或其它事件触发仍未闭合。
  策略的正确性来自每个 paused frame 重读 target/route，而不是预测第 14 日必改令。

## 定向测试矩阵

| ID | 证据 | Fixture | 预期 Counter-policy | 禁止的推断或动作 |
|---|---|---|---|---|
| P01 | [inference][counter-policy] | 两敌同 current、endpoint 分别为 `2596` / `2587` | 建两份 ledger，M × N 独立审计，保留 `2587` hazard | 合并成一个 blob；命名第二军 assignment |
| P02 | [inference][counter-policy] | 敌 current 每日变化，target/endpoint/route intent 不变 | 保持仍安全的玩家 route，仅逐日重审 | 追着 enemy current 每日反向改令 |
| P03 | [inference][counter-policy] | endpoint 在第 3 日提前变化 | 当帧关闭旧 epoch、重审所有路线 | 把 7 日当作不可提前 invalidation 的锁 |
| P04 | [inference][counter-policy] | endpoint 连续跨过第 7 与第 14 日不变 | 只记录两个 milestone，继续按实测字段决策 | 宣称已经重算、必将改令或仍锁定 |
| P05 | [inference][counter-policy] | snapshot `soldiers` 比例小于等于 `0.33` | 仍同时维护 7 / 14 milestone | 由 UI 兵数判 lopsided 或 stance |
| P06 | [inference][counter-policy] | moving 但 target/route 缺失，或 route endpoint != target | 保持暂停；不 advance / split / merge | 用 partial route 猜目的地 |
| P07 | [inference][counter-policy] | 2 玩家军 × 2 敌军，只有第四格路线冲突 | 否决对应候选；每一格都必须执行 | 只审计 strongest 或只匹配一敌一军 |
| P08 | [inference][counter-policy] | 非 objective destination 有敌军，exact combat forecast 缺失 | 拒绝主动接战路线，选择 objective/hold/rendezvous | `allow_enemy_at_destination` 绕过安全门 |
| P09 | [inference][counter-policy] | 玩家 `1700 soldiers`、敌军 `800/2400`，无 exact power | 不因 `2400` 最大而追其 current；走 safe exact objective 或 hold | 把 soldiers 最大目标当成安全目标 |
| P10 | [inference][counter-policy] | 已拆两军同省，任一 half-stack 安全证明 unavailable | 选择 original-main <- sibling Merge recovery；本 turn 不推进 | 再 split 或让两半直接出发 |
| P11 | [inference][counter-policy] | Merge ACK 后 source 消失、destination 保留 | 关闭旧双军 intent，取得新 snapshot 和 fresh preview | 复用 merge 前任一 route |
| P12 | [inference][counter-policy] | 两半都有 durable goal、全 M × N exact-safe、reunion 完整 | 可以保持已拆状态；仍不自动新增 split | 仅凭路线无交叉就证明 cohesion |
| P13 | [inference][counter-policy] | 敌军 sieging，随后 target/route 或 combat state 改变 | soft-anchor epoch 立即失效并重审 | 假定围城军固定 30 日 |
| P14 | [inference][counter-policy] | 任一玩家军 combat / retreat，另一军有安全 route | 不向前者 move/split/merge；全局审计后最多推进一日 | 用另一军安全路线放行长时间 |
| P15 | [inference][counter-policy] | restore、战争结束、enemy ArmyID generation 改变 | 截断 ledger/history；新分支 age 从 0 开始 | 跨时间线复用 endpoint 黏性 |
| P16 | [inference][counter-policy] | `war=16777290,date=53175984` 的双玩家/双敌快照 | 推荐 paused Merge recovery，随后 fresh preview；`2587` 保持 hazard | 追 `2581`、穿 `2587`、命名 `33554657`、直接 advance |
| P17 | [inference][counter-policy] | 同一 checkpoint origin 连续两次 restore，入口分别为 `2585` / `2568` | 最新两条 advisory 都参与 exact route 比较；第三旧淘汰 | 单条覆盖后重演较早失败；把 target 永久拉黑 |

## 实现与验证边界

- [inference][counter-policy] 第一实现阶段应先增加纯 Python endpoint ledger、词典序选择和上述 fixture，不新增
  native memory 字段，也不修改 CK3。
- [inference][counter-policy] 现有 route normalization、全军 stationary threat、exact objective preview、
  SiegeID / Assault 生命周期和 restore-history 隔离应作为复用基础，而不是另建平行协议。
- [inference][counter-policy] 只有公开且语义冻结的 exact combat forecast capability 出现后，P08/P09/P12 的
  contact 分支才可从 fail-closed 升级；新增能力前不得为测试伪造 unknown native 语义。
- [unknown] 原生 stance identity、power aggregation、combat/retreat controller 与 assignment kind 的未来研究
  不属于 counter-policy 实现的前置条件；策略可以在这些字段永久 unknown 的情况下按本文安全运行。
