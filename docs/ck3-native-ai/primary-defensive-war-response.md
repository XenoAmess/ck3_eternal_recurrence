# CK3 1.19.0.6 新发生主防守战争的原生响应树

## 结论

- [static-confirmed + inference] 原版 AI 在一场新发生的主防守战争中，并不先计算完整 campaign forecast 或三种退出结果的
  完整动态条款，再决定能否集结和移动。原版数据分别定义兵力集结门、defender stance / objective controller 和
  战争终止 interaction；没有终止候选时继续运行军事 controller 是这三条已证独立链的 fallthrough 解释，尚未把外层
  scheduler 的每条 C++ edge 都命名。
- [static-confirmed] 三个默认 defender stance 都把 `wargoal_province` 设为最高基础 priority `500`。
  因此尚未读出相对总兵力、无法区分 offensive / defensive / desperate 时，**战争目标仍是三者的共同原生输入**；
  相对兵力影响后续目标质量，不是新战争从零开始行动的绝对门禁。
- [production-blocker-live] run `20260828T053149Z-one-generation-9ace0939` 中，玩家 `29829` 在
  `date_raw=53232216` 成为 `naval_expansion_cb` 的 primary defender，WarID `100663382`、战分 `0`、
  objective Province `2627`。`raise-troops-default` 已在同一暂停日期生成可控 ArmyID `100663369`，随后 planner
  仍因完整 victory / white-peace / surrender terms 和 campaign forecast 缺失而停止；这是我方门禁，不是原版继续作战门。
- [static-confirmed + production-blocker-live] 当前 source `88dba0a` 还有一个更早的语义错误：
  `ReadWarTerminationOptions` 把 `0xC569F0` 的 bool 当成“绝对 attacker victory”，但该参数已经由战争面板调用链
  闭合为 `player_victory`。所以玩家为 defender 时，当前 query 的 `victory` 与 `surrender` context 实际互换；
  本次 live 返回值恰好与该互换完全吻合。修正并加 primary-defender golden 以前，这两行不得作为退出决策输入。
- [counter-policy input] 解除当前 B1 的最小输入不是完整战争模拟器：先修正 defender outcome 极性；随后在
  day-0 / score-0、没有可执行胜利且未选择退出时，允许已经集结的军队消费 exact wargoal、army route/state、
  route preview/contact 与 tactical safety，继续既有军事 OODA。完整条款与 campaign forecast 只在真正比较或提交
  white peace / surrender 时成为门，不应阻塞无退出动作的普通防守行动。

## 版本、原版数据与 live artifact

- [static-confirmed] CK3 `1.19.0.6`；`ck3.exe` SHA-256：
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- [static-confirmed] 原版数据均来自同一安装包：

| 文件 | SHA-256 | 本文消费的原生输入 |
|---|---|---|
| `game/common/ai_war_stances/_ai_war_stances.info` | `0F01AAAB6922FDCA19B87A4421768F83B0C75534A128A73AF8CECADD52F6205E` | stance 选择顺序、相对兵力和 objective 语义 |
| `game/common/ai_war_stances/00_ai_war_stances.txt` | `4F5AA322C4D7272338F4C7B111B7462D4A1FEC886E93E7178084D318CEB8E294` | 三个 defender stance 的 objective priorities |
| `game/common/defines/ai/00_ai.txt` | `C78F9CD8DF9938CC9F38E817BCB6E32CD13720B5BD9DE077B85E3E1C6F030293` | 集结阈值、安全集结范围、目标/stance cadence |
| `game/common/character_interactions/00_war.txt` | `5C99B8F14893929A9BC2DBB5B258CDD2D4233D5805091952209413DE876EE09F` | 胜利、白和、投降的主动提出和接受树 |
| `game/common/casus_belli_types/07_ep3_admin_cbs.txt` | `305622DE1A876510380355B2328E6989E377E5D32133A03AA24D9AB35B44D5A6` | `naval_expansion_cb` 的目标和三结果 effect |

- [production-blocker-live] run：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260828T053149Z-one-generation-9ace0939`。
  `report.json` SHA-256
  `433A661EABBE554626A6936D0711012C711CFD87E36AC7E78BC882FB2B7D82C5`；`first-blocker.json` SHA-256
  `1C74C447EC1982BE80CD026EE3CAD62F92A3828C01C4B77720F9E5960BEEF24A`；seed checkpoint SHA-256
  `EDEF4C588C0BA937B45605C3DED1747A95FD0F1B6898501BE1614555B321D4FE`。
- [evidence-boundary] 该 report 的 `ck3_executable_sha256` 字段为 `null`，所以它本身不独立证明 EXE hash；
  live 证据只能与 report 广告的 `game_adapter_id=ck3-1.19.0.6-msvc-x64` 和本目录已有 exact-build 冻结并列使用，
  不能把空字段改写成 live hash observation。

## 当前 B1 的真实时间线

| turn | 日期 | 已观测事实 |
|---:|---:|---|
| 11 | `53231952 → 53232216` | [production-blocker-live] 原 30 日非战术推进在第 11 日被 `war_changed` 停止；新 WarID `100663382`，玩家无军，objective=`[2627]`，敌 primary default rally=`476`。 |
| 12 | `53232216` | [production-blocker-live] 第一次 `query-war-termination-options-100663382` 成功。 |
| 13 | `53232216` | [production-blocker-live] `raise-troops-default` submitted；after snapshot 新增 ArmyID `100663369`，日期未推进。 |
| 14 | `53232216` | [production-blocker-live] 第二次同帧 termination query 成功。 |
| 15 | `53232216` | [production-blocker-live] planner 以 `defensive_war_exit_evidence_required` 停止，没有发出移动或时间推进命令。 |

[production-blocker-live] blocker row 还确认：玩家是 primary defender；primary attacker 是 CharacterID `31948`；
战争日数 `0`；attacker / defender score 及 battles / imprisonment / occupation / ticking 全为 `0`；CB database index
`69`、key `naval_expansion_cb`、允许白和。当前 artifact 没有发布 ArmyID `100663369` 的省份、兵力或 route，
因此本研究不猜它的实际集结省，也不宣称 Province `2627` 已经 route-safe。

## 原生第一步：兵力集结

### 原版 AI 数据门

[static-confirmed] `00_ai.txt` 明确给出：

- AI 尚无已集结军队时，待集结兵力至少达到自身最大兵力的 `0.3`，**或**至少达到敌军的 `0.5`，才会集结；
- 已有军队后再次尝试集结 levy 的 cooldown 是 `180` 日；
- 决定需要更多军队后，新增可集结兵力至少累积到自身 possible troops 的 `0.1`，避免频繁生成极小军团；
- defender 和 attacker 的 safe raise 搜索距离均为 `1` county；
- 计算到 war-goal counties 的距离后，improved raising 从最近的 `5` 个 safe counties 中选择实际集结县。

[unknown] exact-build 中消费这些 define 的 AI tick 入口、五个 safe county 的完整评分/tie-break、事件触发与周期重试的
精确顺序尚未闭合。原版数据能证明这些是原生 AI 的集结输入，不能证明当前角色在当前帧实际选中了哪一个县。

### 当前 bridge 命令不是原生 AI 的完整集结选择器

- [static-confirmed] 当前 `raise-troops-default` 使用 `0x224CC80(Character*)` 解析角色的 default rally Province，
  再由 `0x26D6FC0` 构造单省 `CRaiseTroopsCommand`、`0x26D7150` validator、flags `7` queue 和
  `0x10E7950` teardown。它是合法的原生玩家命令 ABI。
- [static-confirmed] 因为这个写口只消费 default rally Province，它没有复现上述 war-aware safe-county candidate tree。
  本次命令成功只能证明“一次合法集结已生成可控军”，不能写成“与原生 AI 选择了同一集结县”。
- [counter-policy input] 对当前已经成功集结的 B1，不应为了追求完整 AI rally parity 再冻结推进；先读取新 ArmyID 的
  current/route/state 并做下一条 exact route 决策。只有后续真实 outcome 证明 default rally 导致不可用或危险，才把
  safe-rally selector 提升为该 run 的新 blocker。

## 原生第二步：defender stance 与移动

[static-confirmed] `_ai_war_stances.info` 的顺序是：按 participant side 与计入 elite troop quality 的相对 army size
产生 `stronger / weaker` 属性；defender 显著弱势且接近战败或只剩一个 landed title 时还可进入 `desperate`；先执行
behaviour attribute 过滤，再执行 `can_be_picked`，最后取最高 `ai_will_do` score 的 stance。

三个普通 defender stance 的第一个 objective block 为：

| stance | 共同最高项 | 其它主要项 |
|---|---|---|
| `defender_offensive` / stronger | `wargoal_province=500` | wargoal/primary-defender area enemy unit `250`；任意 enemy unit `200`；enemy capital `150`；enemy province `100` |
| `defender_defensive` / weaker | `wargoal_province=500` | area enemy unit `250`；任意 enemy unit `200`；`defend_wargoal_province=100`；capitals `50` |
| `defender_desperate` | `wargoal_province=500` | area enemy unit `250`；own capital `50`；own province `25` |

- [static-confirmed] 每个 unit stack 先得到 preliminary goals，仅 top `10` 进入包含 pathfinding 的 final evaluation；
  assignment 最终落为 Province target，再走普通 native move command。
- [static-confirmed] stance 正常每 `30` 日重算；split/merge 每 `14` 日；target 正常每 `7` 日重算，lopsided
  power ratio 不高于 `0.33` 时为 `14` 日。事件驱动的更早 invalidation 仍是 unknown。
- [static-confirmed] all-defender common invariant 是 exact war goal，而不是 enemy default rally Province。
  当前 active-war snapshot 已发布 objective `2627`；因此下一军事 epoch 应优先对这个 exact objective 做军队状态和 route
  查询，不能把 `476` 当作自动目标。
- [unknown] 当前 report 没有双方 aggregate power、selected stance、ArmyID `100663369` 的位置/route 或敌已集结军，
  所以本研究不选择具体 move literal，也不声称 `2627` 已安全。

## 原生第三步：胜利、白和、投降或继续

### 主防守方的普通主动终止树

[static-confirmed] 原版的三种战争终止 interaction 与军事 controller 是分离的：

- 防守方执行胜利使用 `end_war_attacker_defeat_interaction`。普通 AI defender 在 defender score `100` 时主动执行；
  Peacemaker、文化、dynasty 或断首变量可在带附加门的 `90/70` 分支提前执行。
- 防守方投降使用 `end_war_attacker_victory_interaction`。当 AI actor 是 defender 时，普通主动分支要求
  attacker score `100`，并在 maximum war score 停留至少 `180` 日；这不是未来战斗预测。
- 防守方主动提出 white peace 的普通早期分支要求战争至少 `182` 日且 defender score 不高于 `15`；
  至少 `365` 日又有长期战争分支；债务分支也要求至少 `182` 日。conqueror defender 对 AI attacker 有独立 `+100`
  特例，人质分支通常要求至少 `365` 日。
- `ai_will_do` base 为 `0`。没有任何主动终止分支形成正权重时，原版继续执行 war coordinator；
  `00_war.txt` 的这些分支不消费 battle Monte Carlo、完整 campaign outcome distribution 或 CB structured terms query。

[inference] 因此在普通 day-0 / score-0 防守战中，若没有未观测的 conqueror 等特例，原版行为是“继续军事 controller”，
不是“因没有 forecast 而暂停”。当前角色是否带所有特例变量没有在本 artifact 发布；该缺口不改变完整 forecast 并非
原版普通 continue gate 的静态事实。

### `naval_expansion_cb` 的当前结果方向

[static-confirmed] 对玩家 defender：

| 玩家结果 | 绝对 CB result | 原版脚本的关键后果 |
|---|---|---|
| surrender | attacker victory | target county holder 改为 attacker；attacker 获得 victory legitimacy/influence/prestige-experience，并建立 truce |
| white peace | white peace | 不转移 target title；attacker 损失 `minor_prestige_value`，双方按人格承受可能 stress，并建立 truce |
| victory | attacker defeat | attacker 支付 `pay_short_term_gold_reparations_effect(GOLD_VALUE=2)`、损失 medium prestige/legitimacy/influence；defender 获得 medium prestige，并建立 truce |

[static-confirmed] 这足以证明 surrender 会放弃目标 county，而 white peace / victory 不会；但 dynamic gold、实际 target
holder operations、truce expiry、盟友、战俘和当前资源仍未进入 production terms wire。它们在真正比较退出效用时仍是质量依赖，
不应被写成已完成。

## 当前 primary-defender query 的极性错误

### exact-build builder 合同

[static-confirmed] WarOverview 的 `SetEffectsTabVictory` 调
`0xC569F0(war, true)`，`SetEffectsTabDefeat` 调 `0xC569F0(war, false)`。函数内部只在玩家为 attacker 时
反转该 bool，再按结果选择 index `2` attacker-victory 或 index `4` attacker-defeat。由此 bool 的 caller 语义明确是
`player_victory`：

- `0xC56A14` 读取 primary attacker，`0xC56A20` 与 local player 比较；命中 attacker 后在
  `0xC56A24` 改取 primary defender recipient，并于 `0xC56A2A` 执行 `xor sil,1`；
- 玩家是 primary defender 时，`0xC56A30–0xC56A3C` 保留输入 bool；`0xC56A41–0xC56A4B` 再把结果映射到
  interaction database slot。

| 想构造的玩家结果 | 必须传入 |
|---|---:|
| surrender / player defeat | `false` |
| victory / player victory | `true` |

[static-confirmed] 该输入不随玩家 side 改变；side 极性已经由 `0xC569F0` 内部处理。

### source `88dba0a` 与 live fingerprint

[static-confirmed] commit `88dba0a244a93a7d5c054e4909fdfa4f8eb31a6e` 的
`ck3_autonomous_player/native_bridge/src/ck3_11906.cpp`（Git blob
`1621592442a7cc8f465b8e3bc38dfd805421804d`）在 `ReadWarTerminationOptions` 中却调用：

```text
surrender: EvaluateWarResolutionContext(..., !player_is_attacker)
victory:   EvaluateWarResolutionContext(...,  player_is_attacker)
```

[static-confirmed] 这只在玩家是 attacker 时偶然等价于 `false / true`；玩家是 defender 时变成 `true / false`，
恰好交换两个 context。

[production-blocker-live] 当前 artifact 的两行形成独立 fingerprint：

- JSON `surrender` 标成 `attacker_victory`，但实际传入 `true`，所以构造的是玩家胜利 / `attacker_defeat`；
  在 score `0` 时 validator=false、raw=`-99`、auto=false。
- JSON `victory` 标成 `attacker_defeat`，但实际传入 `false`，所以构造的是玩家失败 / `attacker_victory`；
  在 score `0` 时 validator=true、raw=`-99`；recipient 是 AI primary attacker，原版该 interaction 的 auto-accept
  条件因此为 true，最终 status=`0` / would-accept=true。
- white peace 用独立 special index `3`，本次 validator=false、raw=`-30`、status unavailable；不受 bool 互换影响。

这组 validator/auto-accept 组合与原版两个 interaction 的脚本门逐项吻合，不能解释成“victory 在 0 分已可执行”。
在修复 defender polarity 并加一个 score-0 primary-defender golden 前，当前 `options.victory/surrender` 是 invalid machine input；
先研究完整 dynamic terms 或 campaign forecast 不能修复这个标签错误。

## 合并后的原生响应树

```mermaid
flowchart TD
    N["[live-confirmed] 新主防守战争<br/>WarID 100663382 / day 0 / score 0"] --> R{"[static-confirmed] 已有可用兵力？"}
    R -->|no| Q{"[static-confirmed] 可集结量 ≥ own 0.3<br/>或 ≥ enemy 0.5？"}
    Q -->|yes| SAFE["[static-confirmed] safe raise 搜索<br/>defender distance=1 / closest candidates=5"]
    Q -->|no| WAIT["[static-confirmed] 暂不集结；等待兵力累计"]
    SAFE -. "[unknown] exact AI candidate score / tie-break" .-> RU["[unknown] 当前 AI 会选的具体集结县"]
    R -->|yes| ST{"[static-confirmed] defender relative-power stance"}
    SAFE --> ST
    ST -->|stronger| OFF["defender_offensive"]
    ST -->|weaker| DEF["defender_defensive"]
    ST -->|desperate| DES["defender_desperate"]
    ST -. "[unknown] 当前 aggregate power / selected stance" .-> SU["[unknown] 当前分支"]
    OFF --> WG["[static-confirmed] wargoal Province priority 500"]
    DEF --> WG
    DES --> WG
    WG --> TOP["[static-confirmed] preliminary goals → top 10 final pathfinding"]
    TOP --> MOVE["[static-confirmed] Province assignment → native movement/controller"]
    N --> EXIT{"[static-confirmed] 主动终止候选有正权重？"}
    EXIT -->|defender victory score threshold| ENF["执行 defender victory"]
    EXIT -->|WP age / debt / special motive| WP["提出 white peace"]
    EXIT -->|attacker score 100 + max 180d| SUR["defender surrender"]
    EXIT -->|ordinary day-0: none| CONT["[inference] 继续 war coordinator"]
    CONT --> ST
    EXIT -. "[unknown] scheduler 的确切发送日" .-> EU["[unknown] interaction dispatch timing"]
    BUG["[live-confirmed] 当前 defender query<br/>victory / surrender context 互换"] --> BAD["修正 polarity 前不得消费两行"]
    BAD --> FIX["[counter-policy input] surrender=false / victory=true<br/>加 primary-defender golden"]
    FIX --> EXIT
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class RU,SU,EU unknown;
```

## 最小 counter-policy 输入与质量债

### 当前 B1 可以立即消费的最小集合

1. [counter-policy input] 修正并 fixture-lock `player_victory` 极性：surrender=`false`、victory=`true`，不按 side
   改调用参数；white peace 保持 index `3`。
2. [counter-policy input] 继续门只要求：paused same-frame WarID、玩家 side/primary-leader、战争仍 active、
   `player_relative_war_score`、没有 100% enforce、没有已选择且已核验的退出动作。structured exit terms 缺失不能自动变成 hold。
3. [counter-policy input] 无军则沿现有合法 `raise-troops-default`；已有军后读取 ArmyID 的 current Province、route、
   target、combat/retreat/siege 状态。
4. [counter-policy input] 从 exact `war_objective_province_ids` 取 `2627`，只在 fresh native route preview、route-contact
   audit 与既有 tactical gate 通过后提交 move。`enemy_primary_default_raise_province_id=476` 只作诊断，不作 objective。
5. [counter-policy input] 敌军出现、route 相交、进入 combat/retreat、objective occupation 改变或 termination legality
   改变时打开新 epoch；否则按既有有界战争推进，不为每个军事 order 重查完整三结果条款。

### 不阻塞当前 continue、但仍需保留的质量债

- [unknown] 双方 aggregate campaign power 与当前 defender stance；补齐后可在共同 wargoal 基线上改善 offensive / defensive
  选择，但不应让 ArmyID `100663369` 永久停住。
- [unknown] war-aware safe rally 的具体候选、评分和 tie-break；只有 default rally 的真实坏 outcome 才把它升级为本局 blocker。
- [unknown] `naval_expansion_cb` 的 production structured dynamic terms、当前资源、战俘/盟友/合约和完整 campaign forecast；
  在选择 white peace / surrender 时必须继续 fail closed，在普通 continue 时不是硬门。
- [unknown] 当前 attacker 是否已经在未发布范围集结其它军队、其 ETA 与海运路径；敌军一旦进入 snapshot，必须重新走
  route/contact 和 tactical safety，不能因当前未见就推断不存在。
- [unknown] 原生 interaction scheduler 把 `ai_frequency_by_tier` 与正 `ai_will_do` 映射到具体发送日的 C++ 顺序。

## 与既有专题的边界

- stance、objective、target cadence 与 movement 主干见 [army-controller.md](army-controller.md)。
- termination context、AI acceptance 和三种 interaction 见 [war-termination.md](war-termination.md)。
- 当前 query 极性错误取代“player-defender polarity 仅待 fixture”的旧宽泛表述；只升级这次已证 B1，不把其它 CB、
  hostage 或 dynamic terms 宣称为 complete。
- 我方策略设计仍属于 [player-war-exit-policy.md](player-war-exit-policy.md)；本文只给出可消费的原生事实和最小输入，
  不实现 planner。

## R0050：-100 分的封臣化主防守战，军事继续与投降分离

- [production RED] `formal-R0050` 在 CK3 `1.19.0.6` 的 turn 32、战争 `150994969` / `vassalization_cb`、
  `duration_days=153`、玩家主防守方 score `-100` 停于 `native_war_no_safe_target`。唯一 Army `301989888`
  在 Province `8750` 仅 2 人；敌军 `184549393`、`301989919` 的已观测路线正向该点收敛。此前已做同帧
  接触证明约束下的受控逐日推进，turn 32 没有新的实质动作；本次报告未独立记录 EXE SHA，不能据此
  宣称本轮重新核验了二进制哈希。
- [static-confirmed] 本文冻结的 `1.19.0.6` 原版 `common/character_interactions/00_war.txt` 普通 AI 主防守方
  主动投降条件为攻击方 score `100` **且**保持 maximum war score 至少 `180` 日；单凭战争已持续 `153` 日、
  当前 score `-100` 不能推出 180 日持续时长，也不能推出 interaction 调度会在哪一日执行。军事
  controller 的守卫 `own capital` / `own province` 候选与终止 interaction 是独立树。
- [static-confirmed] exact 原版 `common/casus_belli_types/00_vassalization.txt` 的 `on_victory` 通过
  `create_title_and_vassal_change(type=swear_fealty)` 与 defender `change_liege(liege=attacker)` 改写隶属，
  另含声望和停战效果；因此“合法且对方会接受的 surrender”不等于“无害的继续手段”。当前 native
  `termination_terms` / `campaign_outcome_forecast` 仍未知，不得仅凭 ACK 或 score 猜测结果并自动投降。
- [inference / counter-policy input] `-100` 只能解除现有原生集结点守备观测的人工分数截断，不能解除
  同帧 campaign-root、直属领首府的完整投影、native preview、全敌军 scope、one-day contact horizon、
  有效军队绑定、未知动作和 pending interaction 拒绝；无已证安全候选或完整 horizon 时仍 RED 零动作。
  不把普通 `life-advance` 或任何战争终止动作列作这次修复的 fallback。
- [unknown] 当前交战方/战役的动态投降条款、maximum-score 起始日期、敌军未来调度与当前接触后的
  物质结果均没有 R0050 独立后置证据。只有新制品在真实 paused frame 重新查 root/route/horizon 并推进、
  下一 turn 消费结果后，才可把本修复从静态候选升为 production-live。

```mermaid
flowchart TD
    R["[live-confirmed] R0050 score -100 / threatened rally"] --> N{"[static-confirmed] native AI surrender<br/>attacker 100 + max-score 180d?"}
    N -. "[unknown] max-score onset / scheduler" .-> U["[unknown] actual native termination timing"]
    R --> C["[counter-policy] military continuation independent of surrender"]
    C --> P{"fresh root + complete hostiles + native route/contact proof?"}
    P -->|yes| A["one bounded nonterminal action; re-observe"]
    P -->|no| X["RED / zero action / fill missing observation"]
    R -. "[unknown] dynamic vassalization terms" .-> S["no automatic surrender"]
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class U,S unknown;
```

## R0160: an observed hostile siege invalidates an indefinite objective hold

- [production-blocker-live] `formal-R0160` had two simultaneous
  `naval_expansion_cb` wars (`16777250` and `95`) with Robert as primary
  defender.  The only controllable army, `83886367`, stayed idle on shared
  war-goal Province `2638` while the exact paused snapshots published hostile
  Army `50331863` sieging Province `2635` and hostile Army `83886252` sieging
  Province `2627`.
- [production-blocker-live] Before command-history entry `801`, War `95` had
  score `+9`, occupation `0`, and ticking `-9`.  During that seven-day
  stationary hold, Army `50331863` changed from `sieging` to `regular` at
  Province `2635`; the next termination query reported score `-23`, occupation
  `32`, and ticking `-9`.  The same failure repeated at entry `897`: War
  `16777250` changed from `+17` to `-15` as Army `83886252` completed its siege
  at Province `2627` and started moving toward `2619`.
- [production-blocker-live] The same-frame strength rows were already
  available.  At the first reversal, the player had `2329` current soldiers
  and native base power `7578100000`; the sieging army in War `95` had `267`
  and `1140800000`.  Before the second reversal, the player had `2339` and
  `7598100000`; the sieging army in War `16777250` had `545` and
  `1237200000`.  This is sufficient to identify a conservative operational
  overmatch candidate.  It is not a battle-win forecast.
- [static-confirmed] The frozen exact-build stance tree already ranks
  `wargoal_province` first and enemy units in the war area next for every
  ordinary defender stance.  R0160 does not identify the exact native C++
  target selected in either frame, but it confirms that our execution-only
  stationary hold omitted an observed enemy-unit input that the native stance
  data considers.
- [counter-policy input] A stationary primary-defender war-goal hold is not
  eligible while any active primary-defensive war publishes a non-retreating
  hostile army in `sieging` state and the complete same-frame strength query
  proves at least a 2:1 friendly margin in both current soldiers and native
  base power for that war.  Select one deterministic siege relief target,
  bind the sole idle controllable army to it, and use the existing native route
  preview plus complete hostile contact-horizon audit before a typed move.
  One army receives one target even when several wars publish sieges.
- [evidence-boundary] Enemy siege progress, days remaining, fort strength, and
  occupation ownership for Provinces `2635` and `2627` were not published.
  The counter-policy therefore consumes only the observed hostile
  `army_state=sieging`, current Province, complete same-frame per-war strength,
  and existing route/contact proof.  Missing strength, incomplete hostile
  position/route state, an unsafe preview, or an unavailable contact horizon
  remains zero-action fail closed.  Static tests can prove target selection and
  typed-move readiness, not battle or war victory.
- [artifact] Frozen driver state:
  `g2-robert-mainline-r0160-defense-stationary-red-20260923/R0160-final-frozen-pair/driver-state.json`,
  SHA-256 `DE2C7FC2FC674176A84493EDD3EB7A975E26C28AFA86C022B5C13AE9AF3B0177`.
  Pair manifest SHA-256:
  `6BB0D8D5A8AB106E6D9EFA7235608E59C465A69C8A16FEBCEEA54A586FDB3946`.

```mermaid
flowchart TD
    H["paused primary-defender objective hold"] --> S{"any observed hostile sieging?"}
    S -->|no| B["existing bounded hold policy"]
    S -->|yes| F{"same-frame per-war strength complete<br/>and friendly >= 2x soldiers + power?"}
    F -->|no / unknown| X["fail closed; no time advance"]
    F -->|yes| O["choose one stable war + enemy Province<br/>bind one idle controllable army"]
    O --> P{"fresh native route preview complete?"}
    P -->|no| Q["query preview"]
    P -->|unsafe / unavailable| X
    P -->|route intersects hostile| C{"complete one-day contact horizon safe?"}
    C -->|unknown / unsafe| X
    C -->|yes| M["typed move to siege-relief Province"]
    P -->|safe| M
    M --> R["re-observe army, battle, siege and war score"]
```

## R0161: accepted siege relief must enter the existing in-flight route tree

- [production-live primitive] At `date_raw=53189208`, the R0161 formal loop
  observed hostile Army `50331863` sieging Province `2627`.  The R0160 policy
  selected that Province, obtained native route preview
  `[2643,2639,2633,2627]`, and obtained a complete-scope contact horizon with
  `one_day_contact_free=true` for hostile IDs `50331863` and `83886252`.
- [production-live primitive] Typed command
  `move-army-83886367-to-2627` was accepted.  Its independent postcondition
  published the same Army as `moving`, with `move_target_province_id=2627`
  and the same complete route.  This closes route selection and typed move
  submission for the observed frame; it does not prove arrival, battle, siege
  relief, or war victory.
- [production blocker] On the same date, campaign-root and strength queries
  refreshed successfully.  The siege-relief admission then rejected the
  moving Army as if its idle binding were missing and returned
  `single-idle-controllable-army-binding`, before the older active-route tree
  could consume the accepted move.  The run stopped without advancing the
  route.
- [counter-policy input] A complete nonempty passive route whose target equals
  the observed move target, plus a matching accepted native move intent, owns
  the Army before a new siege-relief selection.  The siege helper yields to
  the existing active-route audit.  That tree must obtain a fresh complete
  hostile contact horizon when the move postcondition changes native revision,
  then consume only its proof-bound advance step.  It must not submit the move
  again.
- [evidence-boundary] A moving Army without a matching accepted intent, a
  missing or malformed passive route, a route ending at another Province, or
  an unsafe/unavailable current-frame contact horizon remains zero-action fail
  closed.  R0161 contains no date advance after the move, so continued route
  consumption remains a static-ready candidate pending the next bounded live
  run.
- [artifact] Driver state SHA-256:
  `AA82C7A9FB34310680677BEE38644AFEBC9E2A8D05771E8844D166D54EFA7969`.
  Formal report SHA-256:
  `4B62ABDE57DFFDA5E53E80D0FAA9243BDEA77EABDCB05BB89C2E30C87C25C8DD`.

```mermaid
flowchart TD
    S["observed hostile siege"] --> A{"sole controlled Army state"}
    A -->|idle regular| N["R0160 strength + target selection"]
    A -->|moving / embarked| I{"matching accepted move intent<br/>and complete route to same target?"}
    I -->|no / unknown| X["fail closed; no move and no time advance"]
    I -->|yes| R["existing passive route audit"]
    R --> C{"fresh complete hostile contact horizon?"}
    C -->|no| Q["query current-frame horizon"]
    C -->|unsafe / unavailable| X
    C -->|contact-free| P["proof-bound route advance"]
    P --> O["re-observe route, contact, battle and siege"]
    N --> R
```

## R0162: a relief arrival may become a proof-bound recovery siege

- [production-live primitive] The official cold restore resumed the R0161
  checkpoint and did not issue a second move while Army `83886367` retained
  its accepted target.  Four committed-route sentinel slices advanced it from
  Province `2638` through `2643`, `2639`, and `2633` to Province `2627`.
- [production-live primitive] The independent arrival frame published the
  player Army at Province `2627` with `army_state=sieging`, a null move target,
  and an empty route.  Hostile Army `50331863` had left that Province toward
  `2626/8753`.  The defensive war scores improved from `-10/-11` to `-8/-9`.
  This proves route consumption and arrival; it does not yet prove occupation
  recovery or either war's resolution.
- [production blocker] A concurrent hostile siege by Army `83886252` at
  Province `2619` caused the siege-relief admission to demand a new idle Army
  binding.  That check ran before the existing player siege progress tree and
  stopped the already executing recovery siege.
- [counter-policy input] When the latest accepted typed move for the sole
  controlled Army targets its current Province, and the paused frame reports
  that Army as noncombat `sieging` with no move target and no remaining route,
  the arrival remains bound to that move.  A concurrent hostile siege cannot
  retarget it or require a new idle binding.  The existing exact or bounded
  siege progress path retains its threat checks and owns the next slice.
- [recovery binding] A move before the latest cold restore remains eligible
  only when an official `save-checkpoint` after that move has the same history
  index, date, and SHA-256 consumed by the `native-session-cold-start` restore,
  and the fresh native snapshot still publishes the same target and route or
  the completed siege arrival.  An unmatched restore remains a hard barrier.
- [evidence-boundary] A siege without the matching accepted move, a different
  latest target, a nonempty route, a new move target, combat, retreat, an
  expired intent window, or a stationary threat remains zero action.  The
  durable R0162 checkpoint is `date_raw=53189712`; the arrival at `53190000`
  is a recoverable driver tail and must not be counted twice after restore.
- [artifact] Frozen save SHA-256:
  `9B7ACD64CBA42EA7AB828C1A5DE3701176167B87211D6F7F4BE83ACED47A949E`.
  Driver SHA-256:
  `20A1E3CFE160EF60784F03B2780C2AD8C50B2256D048959CE0D2ED3E0525854E`.
  Formal report SHA-256:
  `5B18CC33388ECED5F95CD1F8D24E7B4061DF9BFB3D2AED3E861DFC4C93FEDDAC`.

```mermaid
flowchart TD
    A["accepted relief move"] --> M["proof-bound route consumption"]
    M --> R{"Army reached the accepted target?"}
    R -->|no| M
    R -->|yes| S{"native state sieging<br/>target null, route empty?"}
    S -->|no / unknown| X["fail closed"]
    S -->|yes| P["existing siege progress and threat checks"]
    P --> O["re-observe occupation, Army and both wars"]
```

## R0166: repeated cold restores during one recovery siege

- [production blocker] R0166 restored the R0164 checkpoint at history index
  `1082`, `date_raw=53190528` and planned zero gameplay actions. Its paused
  frame still showed Army `83886367` sieging the accepted destination Province
  `2627`; another hostile siege remained visible. The relief admission rejected
  the arrival proof because the history also contained the earlier cold restore
  at index `989`. The existing lookup stopped at the second restore without
  checking either checkpoint identity.
- [recovery binding] The accepted typed move at history index `976` targets
  `2627`. A save after it at index `988` has checkpoint history index `989`,
  date `53189712` and SHA-256 `9B7ACD64...47A949E`, matching restore `989`.
  The later save at index `1081` has checkpoint history index `1082`, date
  `53190528` and SHA-256 `C2E8778D...B2F7E2`, matching restore `1082`.
  Every intervening cold restore must independently match a later official
  save after the accepted move; any unmatched restore breaks the binding.
- [production-live loop] Between those restores, R0164 issued 22 successful
  bounded siege progress slices. The latest independent after-state at
  `53190528` still showed this Army sieging Province `2627` with no move target
  and no route. This is evidence of continued occupation work, not another
  movement command or the final capture of that Province.
- [counter-policy input] The 90-day movement intent limit governs an Army
  still travelling. After arrival, the same native siege can continue only
  while successful bounded progress results consistently keep the Army
  sieging the accepted Province and the latest result reaches the current
  paused date. A contradictory Army state, another typed move, an unmatched
  restore or incomplete progress evidence stops continuation. The existing
  stationary threat and exact siege checks still apply each slice.

```mermaid
flowchart TD
    A["accepted relief move"] --> R{"each later cold restore has<br/>matching official save?"}
    R -->|no / unknown| X["stop for observation"]
    R -->|yes| P{"current Army at accepted Province,<br/>sieging without route or target?"}
    P -->|no / unknown| X
    P -->|yes| C{"movement window open or<br/>continuous bounded siege after-state?"}
    C -->|no / unknown| X
    C -->|yes| S["existing stationary threat and siege progress checks"]
    S -.-> U["unknown: capture or war termination"]
```

## R0168: a relief route entering combat transfers to the battle controller

- [production-live blocker] At `date_raw=53192304`, the official committed-route
  sentinel for Army `83886367` stopped with both `route_target_changed` and
  `combat_transition`. The independent after-state placed that Army in combat
  at Province `2638`, with no move target and no remaining route. A separate
  hostile Army was still sieging Province `2619` in primary defensive War
  `16777250`. The relief admission demanded `single-idle-controllable-army-binding`
  before the existing battle controller could consume the observed combat.
- [exact-build readback] The paused `native:163` battle-control query for the
  sole controllable Army was available on the same date and Province, bound to
  CombatID `738197508`. Its phase was `maneuver`; native retreat legality was
  false with reason `too_early` and earliest gate `53192664`. This is an
  observed battle, not proof of victory or a safe retreat.
- [counter-policy input] An Army with exact current combat state and a
  same-frame, same-Province, same-subject battle-control frame passes to the
  existing global battle audit. The relief selector does not retarget an Army
  already fighting. Missing or stale battle identity remains an observation
  block. A noncombat siege still requires its accepted-arrival proof, and an
  idle Army still requires the relief strength and route gates.
- [offline replay] Replaying the frozen R0168 driver history and the official
  last after-state with the same-frame battle query yields battle-control
  `ready`, relief `active_combat`, then the existing
  `native_war_global_battle_control_progress` plan for one bounded day. This
  is a static plan result; a resumed live outcome remains unknown.
- [artifact] The read-only R0168 frozen pair is
  `g2-robert-mainline-r0168-new-siege-binding-red-20260923/R0168-final-frozen-pair`.
  Its save SHA-256 is
  `C21E594004B3CFB8125CE5C98D70230996F12823238EACAEC5163038013ED9CA`;
  driver SHA-256 is
  `14207EC4C2A694D764E41FAD5282124C29B8FDE6645152482095E47915C2AE03`.
  The raw driver has a post-checkpoint query tail and must pass official
  recovery before another launch.

```mermaid
flowchart TD
    A["relief route sentinel stops"] --> B{"sole controlled Army in exact combat?"}
    B -->|no| R["existing siege relief and route checks"]
    B -->|yes| C{"current battle-control frame matches<br/>subject, Province, date and CombatID?"}
    C -->|no / unknown| X["stop for battle observation"]
    C -->|yes| D["existing global battle audit"]
    D --> E["bounded battle decision or observation slice"]
    E -.-> U["unknown: battle result and war termination"]
```
