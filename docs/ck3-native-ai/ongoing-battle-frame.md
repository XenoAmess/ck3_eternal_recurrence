# CK3 1.19.0.6 战中控制帧：`query-battle-control-snapshot-v1`

> 当前实机增量见文末 [1.20.0.3 玩家战斗日记录](#current-v47-player-battle)：2026-10-04 第三 attempt保存24h/1日，第四保存48h/2日并观测maneuver→main，第五又保存168h/7日并实见主军抵达2618、加入玩家defender侧与Robert29829成为commander。能力限定同一单战斗的有限有界loop与行军入战。此前两次零日RED与下文1.19.0.6历史ABI/验收原文全部保留；旧build地址、readiness和overshoot记录只说明各自冻结时的事实，不外推到当前.3。


本文冻结 P1 第一口可施工的战中 typed observation。它回答的不是“谁会赢”，而是同一 paused revision 中：

1. 玩家究竟在打哪一场 `CCombat`，当前 phase/day/winner/finalizer 状态是什么；
2. attacker/defender 两侧按原生顺序还保留哪些 army 与 regiment entry；
3. 每个 retained entry 的 starting/current/soft 与可判定的 hard（或明确 unavailable）是什么；
4. 当前 battle commander、roll、advantage 与原生 `side_strength` 是什么；
5. 所选 CUnit 属于哪一侧、主动撤退影响 full side 还是同 owner subset，以及当前四个原生 legality gate 是什么；
6. bounded hold 推进一天后，控制器应拿什么真实状态做后置验证。

机器契约是
[battle_control_snapshot_v1_abi.json](../../ck3_autonomous_player/native_bridge/research/battle_control_snapshot_v1_abi.json)。
本文不设计 retreat mutation，不猜增援 ETA，也不把原生 prediction ratio 或 side strength 叫作胜率。

## 冻结边界

| 项 | 值 |
|---|---|
| game version | `1.19.0.6` |
| `ck3.exe` | `Crusader Kings III/binaries/ck3.exe` |
| SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| preferred image base | `0x140000000` |
| 地址 | 下文全部是 RVA |
| 研究日期 | 2026-08-26 |

本能力先完成 bounded static inspection，再于 2026-08-26 用 production exact bridge 完成 managed cold-restore
实机验收。证据标签沿用本目录约定：

- **[static-confirmed]**：由冻结 EXE 指令、RTTI/serializer 或已有 exact helper 直接证明；
- **[live-confirmed]**：已在真实 paused application-main frame 对拍；
- **[unknown]**：仍需逆向或实机 trace；Mermaid 中以虚线表示。

P0 已 [live-confirmed] 当前持续 checkpoint 的 `CombatID=335544325`、Province `2586`、attacker
`[83886341]`、defender `[357,33554657]`，并完成战中 cold restore。P1 随后从 cold checkpoint
`9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63` 连续观测 maneuver 1 至 main 2，
闭合 retained entry ledger、owner hard ledger、strength、合法 stale tick-start cache 与真实 casualty delta。因此
`battle_identity_live_ready=true`、`battle_hold_ready=true`，且 production planner 已连续两轮完成 query→advance→requery；
retreat target/order 的军队语义层与 prior-CombatID full-side transition 后来也已 live，但 owner-subset 与 reinforcement
timeline 仍未就绪。

状态必须拆开读：旧 artifact 与两个 live readiness 只覆盖**原 battle frame**；后来追加的 active-retreat
selected identity、owner scope、side flags 与四 gate legality 又在 fresh production paused query 中完成了 day 0→16 的验收，
因此当前 expanded frame 的 `active_combat_retreat_projection_production_live_ready=true`。随后 production composition 已完成
target preview/token/order 并实见 retreating/target/route；独立 full-CombatID lifecycle query 又绕开旧 frame 的 retreating
subject gate，读到 `main/12→pursuit/0`、winner 与双方 stored order。full-side 后置条件已完成，owner-subset 尚未完成。

## 一页结论

- [static-confirmed] `CCombat+0x08/+0x6B8/+0x6B0/+0x6B4/+0x6E0/+0x704` 足以直接发布
  CombatID、Province、phase、phase day、winner 与 finalizer-entered。`phase=done` 和 `finalized=true` 是两个字段，
  不能互推。
- [static-confirmed + P0 live-confirmed] `CCombat+0x20/+0x368` 两个 side 的 `+0x10/+0x1C` 是 full
  `CArmyID` 原生 stored order；每项经 `CArmy+0x124` 映射 public `CUnitID`，不得排序。
- [static-confirmed + live-confirmed] 两个 side entry bucket 是 levy `+0x28/+0x34` 与 men-at-arms `+0x40/+0x4C`，stride
  `0x60`。entry `+0x10/+0x18/+0x20` 分别是 starting/current/soft，均为 signed Q100000。
- [static-confirmed] **不存在独立的 per-entry hard 字段。只有 `fights_in_main_phase=true` 的 retained entry，
  hard 才能确定性派生为 `starting-current-soft`。**非主战单位在构造时就是
  `starting>0,current=0,soft=0`；差额含尚未投入/尚未 route 的 reserve，绝不能冒充 hard。
- [static-confirmed + live-confirmed] side `+0x58/+0x64` 另有 stride `0x18` 的 participant-owner hard ledger，row
  `+0x08` 是 CharacterID、`+0x10` 是累计 hard raw。它保存 owner 历史账；被 partial retreat 移除的 regiment row
  已不能再从当前 entry arrays 恢复 per-regiment hard，所以两类 ledger 必须分开发布。
- [static-confirmed] battle commander 是 `CCombatSide+0x74`，不是 `CArmy+0x120`；roll 是
  `CCombat+0x6D0/+0x6D4`，roll cadence 是 `+0x6E4`。
- [static-confirmed, correcting width] `CCombat+0x6C8` 与 `+0x710` 都由 exact helper 以 **qword** load/store，
  是 int64 Q100000 base/resolved advantage raw。v1 禁止沿用旧 ongoing DTO 的 int32 读取，否则会截断。
- [static-confirmed + live-confirmed] `0x23CC340(CCombatSide*)` 与 `0x23D2D70(entry*)` 是同步只读 strength leaves；
  `side_strength_raw` 不是 soldier count、AI power 或 win probability。
- [static-confirmed + live-confirmed] side `+0x98/+0xA0` 是本 tick 开始时由 `0x23CB840` 刷新的 cache，
  不是 paused frame 中 entry current 的强制一致性字段。main damage 已写 entry 而 cache 尚未二次 refresh 时，
  `stored_*_matches_derived=false` 是合法、稳定且必须发布的观测，不得把它拒成 unavailable。
- [static-confirmed + live-confirmed] expanded frame 已按 selected side 发布 `+0xC0/+0xC1/+0xC2`、
  strict day-14/phase/landless gate、`0x2308250(combat, army, nullptr)` boolean，以及镜像 `0x2308850` owner scan 的
  `full_side | owner_subset` 和 affected/unaffected stored-order public IDs。当前 live 场景确认 full-side；owner-subset 仍只有 unit
  fixture，必须在 mixed-owner 动作矩阵中另做实机验证。

## 原生控制树中的位置

```mermaid
flowchart TD
    S["[live-confirmed] public CUnitID"] --> A["strict CUnit → CArmy<br/>CArmy+0x128 CombatID"]
    A --> C["strict live CCombat<br/>Province / phase / day / winner"]
    C --> O["side0 attacker / side1 defender<br/>ordered CArmy → public CUnit"]
    O --> E["two retained Entry60 buckets<br/>starting/current/soft"]
    E --> H["main-fighting: hard = starting-current-soft<br/>non-main: typed unavailable<br/>participant owner-hard rows"]
    C --> R["battle commander / rolls<br/>int64 advantage totals / strength"]
    C --> L["[implementation-confirmed] 0x2308250 null-sink<br/>four retreat legality gates"]
    O --> RS["[implementation-confirmed] owner scan<br/>full-side / owner-subset stored order"]
    H --> F["BattleControlSnapshotV1"]
    R --> F
    L --> F
    RS --> F
    F --> B["request one-day hold at speed 1"]
    B --> D{"paused reobservation<br/>actual date delta"}
    D -->|24| O["verify one native daily transition"]
    D -->|48; observed overshoot| T["require same identity/phase<br/>phase-day +2 + coherent ledger"]
    D -->|other| X["block and recover checkpoint"]
    RP["[unknown] generic active AI policy<br/>native destination scorer"] -.-> RA["planner target + exact preview/order<br/>semantic action live"]
    RA --> RT["[live-confirmed] prior CombatID transition query<br/>winner / phase / side order"]
    RF["[unknown] helper assignment / ETA<br/>same-day join order"] -.-> FC["future reinforcement forecast"]
    TE["[unknown] result effects / teardown<br/>assignment re-entry"] -.-> TF["future terminal frame"]
    F -.-> RA
    F -.-> FC
    F -.-> TF
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class RP,RF,FC,TE,TF unknown;
```

“hold” 本身不是 CK3 mutation；它是 controller 的策略选择。生产动作请求一个游戏日并在 speed 1 运行，但异步 pause
可能在第一个可观测日界之后才生效。ACK 后必须读取动作实际 start/end/elapsed，再重读本帧：通常接受同 CombatID 的
`+24 / phase_day +1`；已实证的 `+48 / phase_day +2` 只有在 identity、phase 与 exact ledger 一致时才接受。其它跨度继续阻断；
显式 join/reopen/terminal/removal 仍走自己的 discriminant。日期前进或命令 ACK 单独都不算验证。

## exact-build 布局

### Combat identity 与阶段

| 字段 | exact layout | typed 语义 |
|---|---|---|
| identity | CCombat storage `module+0x570C758`，object `+0x08` | full-generation `CombatID` |
| sides | `+0x20` / `+0x368` | side0 attacker / side1 defender |
| phase/day | `+0x6B0/+0x6B4` int32 | `0/1/2/3=maneuver/main/pursuit/done` 与当前 phase day |
| Province | `+0x6B8 CProvince*` | strict `CProvince+0x10` full ID |
| width | `+0x6C0/+0x6C4` int32 | current base/final width；不是 precontact initial width |
| advantage | `+0x6C8/+0x710` int64 | base/resolved signed Q100000 |
| rolls | `+0x6D0/+0x6D4` int32 | 当前 side0/side1 commander roll points |
| winner | `+0x6E0` int32 | `-1` none，`0` attacker，`1` defender |
| roll cadence | `+0x6E4` int32 | 下一次原生 roll 调度所消费的 counter |
| forced winner | `+0x700` int32 | `-1/0/1`，与已经记录的 winner 分开 |
| finalized | `+0x704` byte | finalizer entered；不能由 phase 推断 |
| daily update | `+0x705` byte | dispatcher 正在更新；query 只接受 `0` |
| battle result | `+0x708` full ID | `-1` 才输出 null；其它值严格 generation readback |

`0x27FB6BA..0x27FB717` 先增 `+0x6B4`，再按 `+0x6B0` dispatch，并在回到稳定边界前清
`+0x705`。`0x230A5C4` 在 finalizer 入口写 `+0x704=1`。所以 v1 必须直接发布二者，不能把
`phase=3` 改写成 `finalized=true`。

### Side identity、commander 与 totals

| CCombatSide offset | 内容 |
|---|---|
| `+0x10/+0x1C` | full CArmyID data/count，原生 stored order |
| `+0x28/+0x34` | levy Entry60 data/count |
| `+0x40/+0x4C` | men-at-arms Entry60 data/count |
| `+0x58/+0x64` | participant hard-ledger rows，stride `0x18` |
| `+0x70` | primary participant owner CharacterID |
| `+0x74` | selected battle commander CharacterID；`-1` 合法 absent |
| `+0x98` | tick-start cached 两 bucket fighting raw 总和，int64 Q100000；main damage 后可合法落后于 entry rows |
| `+0xA0` | tick-start cached levy fighting raw subtotal，int64 Q100000；main damage 后可合法落后于 entry rows |
| `+0xB8` | parent `CCombat*` back-pointer |
| `+0xC0/+0xC1/+0xC2` | `disallow_retreat` / `allow_early_retreat` / `skip_pursuit`；最后一项不是 legality gate |

`0x23CB840` 先清 `+0xA0`，按 levy stored order 加 entry `+0x18`，复制到 `+0x98`，再按 MAA stored
order 加到 `+0x98`。exact daily caller `0x2309E80` 先在 `0x2309E8F/0x2309EA1` 调它刷新双方 cache，随后才计算
damage；`0x2309FE8` 与 tail `0x230A002` 调 `0x23CE080`，后者经 `0x23CDF70` 在 `0x23CDFC3` 写 entry soft、
在 `0x23CDFCB` 扣 entry current，而本 tick 结束前不再调用 `0x23CB840`。所以 main-phase 稳定 paused frame 中
`+0x98/+0xA0` 可以保留 tick-start 值，entry rows 才是当前伤亡后的权威值。

query **不得调用**这个 mutator，也不得以 cache 与 derived sum 不等拒绝整帧；它只读并保留两个 cache，同时发布
`stored_current_matches_derived` 与 `stored_levy_current_matches_derived`。双采样仍要求 cache、entries 与 equality
booleans 全部稳定且一致，真假都可构成合法帧。

`CCombatSide+0x74` 是 battle-wide canonical commander。原 contact builder 使用 `0x23C8A60` 从 side army order
选出并写它；这与单军 `CArmy+0x120` raised commander 不是同一观测。v1 只发布当前 full CharacterID 与 absent，
角色属性继续复用 combat-v3，不复制另一套 Character schema。

### Entry60 与 hard casualty 恒等式

两个 bucket 的 row 都是：

```text
Entry60 {
  +0x08 full CRegimentID
  +0x10 int64 starting_raw
  +0x18 int64 current_fighting_raw
  +0x20 int64 soft_casualties_raw
  +0x30 int32 effective_max_size
  +0x38/+0x40/+0x48/+0x50/+0x58
        int64 siege/damage/toughness/pursuit/screen raw
}
```

所有数量/四维 raw 的 scale 都是 `100000`。`+0x08` 先 strict-resolve CRegiment，再以
`CRegiment+0x140` 找 owning CArmy；该 ArmyID 必须位于当前 side 的 ordered army array，并经
`CArmy+0x124 → CUnit+0x178` 完成 public ID round trip。

per-entry hard 的 exact 证明链：

1. `0x23D0520` 把 `CRegiment+0x38 * 100000` 写到 starting `+0x10`，soft `+0x20=0`；类型参加 main 时
   current `+0x18=starting`。`0x23D05E4..0x23D05FA` 证明不参加 main 时 current 保持零，因此该类 row
   一出生就不满足 `starting=current+soft+hard`；差额此时是 reserve，不是 hard。
2. `0x23091DB..0x230926B` 对 route/non-main transition 把 starting 或 current 加到 soft，再把 current 清零。
3. `0x23CDF70` 的写点是 `+0x20 += soft_delta`，随后 `+0x18 -= soft_delta + hard_delta`。
4. 对参加 main 的 retained row，pursuit 从 soft pool 转成 permanent loss 时，soft 减少相同 hard 数量；
   current 已不增加。

因此只对**当前仍保留且 `fights_in_main_phase=true` 的 row**：

```text
hard_casualties_raw = starting_raw - current_fighting_raw - soft_casualties_raw
```

这是确定性派生，不是估计。wire 必须同时发送 `hard_casualties_status=available` 与
`hard_casualties_source=derived_starting_minus_current_minus_soft`，避免使用方误认为 `+0x28` 等位置有一个原生 hard
字段。计算用 checked int64 signed subtraction；不 clamp 负数，也不先换算为 whole soldiers。

对 `fights_in_main_phase=false` 的 row，v1 固定返回
`hard_casualties_status=unavailable`、`hard_casualties_raw=null`、
`hard_casualties_unavailable_reason=non_main_reserve_not_distinguishable_from_hard`。即使某些 loser/pursuit 帧中
`starting-soft` 恰好等于 hard，v1 也不先猜 route lifecycle；后续只有闭合独立 per-entry route marker 后才能收紧。

边界是 partial owner retreat 等路径可以从 live side 删除 entry。删除后无法从当前数组恢复该 regiment 的历史 hard；
side `+0x58/+0x64` 的 row `+0x08 CharacterID/+0x10 hard_raw` 是独立、累计的 owner ledger，v1 必须原序发布。
所以：

- `derived_main_fighting_entry_hard_casualties_raw` 只合计仍在数组中且参加 main 的 rows；
- `non_main_start_minus_current_minus_soft_raw` 仅为诊断差额，字段名明确不把它称作 hard；
- `participant_hard_total_raw` 是当前保存的 owner 历史 ledger；
- 两者不能无条件要求相等，也不能拿 owner total 反分摊到已消失的 regiment。

## strength、roll 与 advantage 的闭合/未知边界

| 域 | v1 能发布什么 | 证据状态 | 不能据此声称什么 |
|---|---|---|---|
| battle commander | side `+0x74` full CharacterID / absent | static-confirmed | AI 何时替换 commander、角色未来是否受伤 |
| current roll | combat `+0x6D0/+0x6D4`，cadence `+0x6E4` | static-confirmed | 下一次随机结果；bounds 需复用 combat-v3 |
| base/resolved advantage | `+0x6C8/+0x710` int64 Q100000 | static-confirmed | 完整 ongoing source identity、未来 event/effect 反馈 |
| entry strength | `0x23D2D70(entry)` int32 | static-confirmed | soldier count 或概率 |
| side strength | `0x23CC340(side)` int32、scale `100000` | static-confirmed + live-confirmed | AI power、win probability |
| current fighting | entry-current checked sum；side `+0x98/+0xA0` 另作 tick-start cache 发布 | static-confirmed + live-confirmed | 初始军力、未来增援 |
| exact forecast | 不在 v1 发布 | unknown / incomplete | `continue` 的 calibrated 胜率 |

`0x23CC340` 严格先扫 levy、再扫 MAA，并对每 row 调 `0x23D2D70`。后者读取 current `+0x18` 与
damage/toughness `+0x40/+0x48`。这两个 helper 是允许的只读调用；`0x2308D50` 和 `0x23CB840` 会写真实
combat/side，禁止在 query 中调用。

exact disassembly 同时纠正一个实现陷阱：`0x2308D9A` 对 base advantage 使用 `mov rbx,qword ptr
[combat+0x6C8]`，`0x2308DCE` 以 `mov qword ptr [combat+0x710],rbx` 写 resolved。v1 的 C++ contract、JSON 与
Python normalizer 都使用 int64 `_raw`；legacy ongoing-combat 投影也已同步升级，不能在任一消费层截回 int32。

## 最小 typed wire

顶层只接受 public full CUnitID：

```text
query_battle_control_snapshot_v1(subject_public_cunit_id, expected_revision)
```

核心 DTO：

```text
BattleControlSnapshotV1 {
  snapshot_revision, observed_date_raw,
  subject_public_cunit_id, subject_native_carmy_id,
  combat_id, province_id,
  selected_public_cunit_id, selected_native_carmy_id,
  selected_owner_character_id, combat_province_id,
  side_index, side_scope: full_side | owner_subset,
  affected_public_cunit_ids_in_stored_order,
  unaffected_same_side_public_cunit_ids_in_stored_order,
  side_flags: {
    disallow_retreat, allow_early_retreat, skip_pursuit
  },
  legality: {
    status, native_boolean,
    phase_raw, phase,
    retreat_elapsed_baseline_date_raw,
    elapsed_whole_days,
    minimum_elapsed_whole_days_exclusive,
    landless_gate_allows_retreat, legal_now,
    reason_codes_in_native_order,
    native_reason_keys_in_native_order,
    earliest_day_gate_date_raw
  },
  phase, phase_raw, phase_day,
  winner_side, winner_raw,
  forced_winner_side, forced_winner_raw,
  finalized, battle_result_id?,
  base_combat_width, final_combat_width,
  roll_cadence_counter,
  base_advantage_raw, resolved_advantage_raw,
  attacker: BattleControlSideV1,
  defender: BattleControlSideV1
}

BattleControlSideV1 {
  side_index, role,
  primary_participant_character_id,
  selected_commander_character_id?,
  current_roll_points,
  ordered_armies: [{
    native_carmy_id, public_cunit_id,
    owner_character_id, combat_backlink_id
  }],
  levy_entries: [BattleControlRegimentEntryV1],
  men_at_arms_entries: [BattleControlRegimentEntryV1],
  stored_current_fighting_raw,
  stored_levy_current_fighting_raw,
  stored_current_matches_derived,
  stored_levy_current_matches_derived,
  derived_current_fighting_raw,
  derived_soft_casualties_raw,
  derived_main_fighting_entry_hard_casualties_raw,
  non_main_start_minus_current_minus_soft_raw,
  participant_hard_ledger: [{ participant_character_id, hard_casualties_raw }],
  participant_hard_total_raw,
  side_strength_raw, side_strength_scale
}
```

Entry DTO 的完整字段和 exact type 由 machine ABI 冻结。两个 bucket 分开发，不合并后重排；bucket index 是
原生 row index。这样 phase event knight source、casualty remainder 与 pursuit stored order 后续都能直接复用。

## application-main 与 generation gates

该 query 必须复用 P0 actual-contact 的 identity spine，不在 Python service 层拼接两个独立 native 查询。一次
application-main callback 内执行：

1. outer `game::ReadSnapshot`：要求 paused，并冻结 revision/date/played character；
2. sample A：strict CUnit→CArmy→CCombat→Province→双方 Army/entry/Character 全图；
3. sample B：重新读取完整全图和所有 derived/helper 值；
4. outer snapshot 再读：paused、revision/date/played character 必须不变；
5. 只有 A/B 完全相等才发布。

关键 full-generation 条件：

- subject `CUnit+0x178` 与 `CArmy+0x124` 双向一致；`CArmy+0x128` 严格解析同一 CCombat；
- embedded side `+0xB8` 都指向该 CCombat；subject 只出现于一侧，两侧 nonempty、disjoint；
- 每个 side Army 都以 `CArmy+0x128` 回指同一 CombatID，再映射 public CUnit；
- 每个 entry RegimentID 必须 strict resolve，`CRegiment+0x140` 指向当前 side Army，且该 Army 的 regiment
  container 含同一 full ID；
- primary、commander、owner-hard CharacterID 都按 full generation 回读；
- selected IDs/owner/combat Province 必须与既有 subject/combat identity 同帧相等；selected CArmy 只出现于一侧；
- scope 对 selected side 的每个 Army owner 按原生 stored order 重算；affected 仅含 selected owner，unaffected 含其余 owner；
- `BattleResultID==-1` 才允许读 `module+0x57C0320` fallback；任何其它 signed full ID 的 stale generation 必须返回
  `state_changed`；负值本身不是 missing；
- `0x2308250` 只以 null ErrorSink 调用；`0x26165B0` 只读取返回对象 `+0x38` bit 10。四 gate 的 raw inputs
  在调用前后保持稳定，reason 顺序必须是 disallow → day → phase → landless，且 `legal_now==native_boolean`；
- phase 只接受 `0..3`，winner/forced winner 只接受 `-1..1`；
- `+0x705==0`；`+0x98/+0xA0` 与 entry checked sums 都以 checked int64 保留，两个 match boolean 必须如实反映
  比较结果，但 `false` 不会让帧 unavailable；
- 任一 count 为负、越界、算术溢出或两次 sample 漂移，整帧 unavailable，并给稳定 reason。

首版 native traversal bounds：side armies `4096`、每个 entry bucket `16384`、participant-hard rows `4096`、
per-army regiments `4096`。wire 另有 `900 KiB` snapshot payload 上限，为 protocol 的 `1 MiB` frame 留出 envelope；
过大的真实战斗帧在 `WriteFrame` 前转为 bounded command error，不会在 application-main 查询完成后断开 pipe。这个边界直接
服务于大战可用性，不扩展额外安全协议。

## 最小 production live acceptance

起点 lineage 使用已经存在的战中 source save，并由托管会话物化实际 cold checkpoint：

- source save SHA-256 `40D4E73D2B45BEF7F8F94F9FC8007A5A039031840C24D72758E5D6452E1A2C6C`；
- fresh acceptance 实际 cold-restore checkpoint SHA-256
  `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`；
- subject `83886341`；
- expected `CombatID=335544325`、Province `2586`；
- attacker `[83886341]`、defender `[357,33554657]`。

v1 最小实机矩阵：

1. paused application-main 查询 `available`，identity/side order 与 P0 artifact 完全一致；
2. 两 bucket 每 row 完成 Regiment→Army→public CUnit→same Combat 回读；
3. 每个 main-fighting retained row 验证 `hard=starting-current-soft`；每个 non-main row 必须返回 typed
   unavailable 而非伪造 hard；side `+0x98/+0xA0` cache 与 entry sum 分别保留，match boolean 必须真实；
4. 连续两次查询除 request/query sequence 元数据外 byte-identical；
5. managed cold restore 后 identity、phase/day、全 ledger、commander、roll、int64 advantage、strength 全等；
6. 请求一日的 bounded advance 后，按动作实际 start/end/elapsed 验证同 CombatID 的 phase/day 与 ledger：通常为
   `+24 / +1`；只有已实证的 pause overshoot 可为 `+48 / +2`，且必须保持 identity/phase 与 exact ledger coherent；
   否则返回显式 terminal/removal discriminant 或阻断；ACK 或 date 单独不算；
7. managed cleanup 后 CK3 process 为零，并恢复基线 checkpoint/driver state。

这组原始矩阵已完成，并且第 6 项覆盖 main day 1 与 day 2 的真实 soft/hard/current ledger delta，故
`battle_identity_live_ready=true` 仍成立。历史 `+24 / +1` hold primitive 也仍有效；但下述正式长跑反例否定了执行器
“请求一日必然只观察到一个日界”的假设，因此最小修复与 checkpoint 复跑前 `planner_battle_hold_live_ready=false`。
这些 readiness 只允许 controller 观察战斗与选择 bounded hold；retreat command 的后续独立证据和 reinforcement forecast
不能由它们推断。

这里的“已完成”最初只指原 frame 字段；下列旧 artifact 的 canonical hashes 不含后来追加的 active-retreat 字段。随后 fresh
production run 从同一 immutable battle save 查询 17 帧：elapsed day 0–14 均为 native false + `too_early`，day 15/16 在 main
phase 翻转为 native true 且 reasons 为空；identity、full-side stored order、flags、landless 与立即双查询都稳定。因此只读
expanded projection 已 live。之后 full-side 真实动作通过 target/route/retreating 军队语义层，prior-CombatID
winner/phase/side order 也由后述 full-ID query 验收；仅 mixed-owner owner-subset 仍未验收。

新增 progression artifact 位于
`C:\Users\xenoa\AppData\Local\Temp\xar-active-retreat-query-v1-a72f4846fa01477ab26860479927c1b3\logs\active-retreat-query-days-live.json`，
size `3710489`，SHA-256 `FB521B39AD5529434596212DB9ADC1EA27D4C270D28D13575B9A2D80913BCF40`；使用 DLL SHA-256
`490E90B41AF43747E43CAE104D11DEFA20D3E27353577114DB7874E1ED09A190`，managed cleanup 成立。

full-side semantic action artifact 位于
`C:\Users\xenoa\AppData\Local\Temp\xar-active-retreat-query-v1-a72f4846fa01477ab26860479927c1b3\logs\active-retreat-action-full-side-live-v4.json`，
size `627856`，SHA-256 `A57FF20DCAD39DF79DAB6A9418054C36B0F5489C5D8B5E9E880CE899AE89DF9C`。day 15 的
`CombatID=335544325`、main/12、full-side `[83886341]` 经 exact route `[2579]` 与单次 token 提交后，在更新 paused snapshot
成为 `in_combat=true/retreating=true`、target/route `2579`；managed cleanup 成立。旧 subject-bound query 随后按 retreating
拒绝，因此本证据只令 `retreat_semantic_action_live_ready=true`，不令 full-side postcondition ready。

full-side complete transition artifact 位于
`C:\Users\xenoa\AppData\Local\Temp\xar-active-retreat-query-v1-a72f4846fa01477ab26860479927c1b3\logs\active-retreat-action-full-side-transition-live-v6.json`，
size `629571`，SHA-256 `21D58737126CA4ED8B0B49DB7749EA4701F3BA6F94A8B8493698F8737E5784FA`。新增
`query-battle-transition-v1-335544325` 不依赖 selected CUnit eligibility；同一 day15 command 后返回 `available`、
`pursuit/0`、winner=`defender`、forced winner=`none`，attacker `[83886341]`、defender `[357,33554657]`。
同一更新帧的军队 retreating/target/route 仍成立，source save SHA `9104CC...CC63` 未变，managed cleanup 后 CK3 process 为零。
因此 `prior_combat_transition_query_ready=true`、`full_side_live_acceptance_ready=true`。

planner-integrated hold artifact 位于
`C:\Users\xenoa\AppData\Local\Temp\xar-planner-battle-control-live-20260826-0910.json`，size `432082`，SHA-256
`96CE25384517F0060A58623958DE071F43C3C2F7B68AEB6E668473E986C1DD57`。`choose_one_life_turn` 在严格动作白名单下完成两轮
battle query→one-day life advance→battle requery：同一 `CombatID=335544325`，日期
`53178264→53178288→53178312`，maneuver day `1→2→3`，两轮 transition 都是 `same_combat_advanced`；撤退动作执行数为 0。
source autosave SHA 前后不变，managed cleanup 与临时 profile clone 删除均成立。因此
`planner_battle_hold_live_ready=true`，但这不解锁 forecast/retreat strategy。

### 2026-08-27 production longrun：两日 paused overshoot blocker

正式 `native-one-generation` 在 turn `1134` 的 speed-1 `life-advance` 中实际返回
`53195880→53195928`、`elapsed_days=2`、`progress_status=postcondition`。前后 exact frame 都绑定
`CombatID=687865860`、同 CArmy/Province、`phase=main`，phase day 为 `32→34`；双方 current/soft/hard ledger
同时演进：attacker `397120/34722071/14880809 → 0/35000056/14999944`，defender
`16941842/27900826/11957332 → 16818259/27987341/11994400`。这与 exact-build dispatcher 每个 native day
令 phase-day 加一的树一致，不能判成原生非法跳跃。

旧 verifier 把所有 post-advance frame 固定限制为 `before_date+24`，因此在 turn `1136` 返回
`native_war_battle_transition_invalid`。report size `6519552`、SHA-256
`E1710E19DC4039716D3EC7A42BC6729D6245E6D99F2FDDDD0771E8FC7CC36403`；first blocker size `4814`、SHA-256
`DBACD2824CCB8E382CEC1EFB5649A634D305D957BEED3082144C08E1526F1470`。最后 durable checkpoint
`date_raw=53195880/history=1888`、SHA-256 `3F8A3355ADFC00190C4679ED887114A4E70C4FCEDD7DECF5E7FBB935B3EE4355`，
角色 `29829` 存活且 cleanup 全绿。修复边界只覆盖 action 自报 `elapsed_days=2`、`date_delta=48`、同 identity/phase、
`phase_day_delta=2` 与 coherent ledger；不放宽任意多日或任意 phase 跳跃。

### 2026-08-26 production 实机证据

- artifact：`C:\Users\xenoa\AppData\Local\Temp\xar-war-entry-production6b-state\logs\battle-control-v1-cold-main-cache-fix-fresh-live.json`，
  size `1253493`，SHA-256 `A0FC6BB7268E38026CC8EED6D6388BFD675AD5DCFB60A1A65FE1C1B64E816AC6`；
- fresh bridge DLL SHA-256 `2F50F14699B8E6D9DF468DCFBEDD145814E50CAC0204D70A32E8CBFD36C34E8F`，
  injector SHA-256 `B22548AEC9EE2B60EBA14CCDE2290AA1CED47EE5D2D277D5031742D683E0F1A3`；
- managed CK3 PID `80196` 从上述 `9104CC...CC63` checkpoint cold restore；session report、shutdown、
  `tree_gone`、`cleanup_proven` 与 driver close 全为 true；
- 每一帧都连续查询两次，canonical frame 相等且 query sequence 严格增加。

| date raw | phase/day | canonical frame SHA-256 | attacker current/cache 与 casualty | defender current/cache 与 casualty |
|---:|---|---|---|---|
| `53178264` | maneuver/1 | `C110C9F4EE97056E452B02009D86D7A9DAF4C38EA9ED5B415AF5EEE5E15CB992` | stored=derived `140300000`，match true | stored=derived `322100000`，match true |
| `53178288` | maneuver/2 | `6F365F256736DA492A92F51441EF5137DBF5B8273B2180FECC007B606A26AB3D` | stored=derived `140300000`，match true | stored=derived `322100000`，match true |
| `53178312` | maneuver/3 | `F5F00242F6E5466B0044170626EA0116DAE5CFFA58F3D1863F18B8A4A78E6D29` | stored=derived `140300000`，match true | stored=derived `322100000`，match true |
| `53178336` | main/0 | `335FCF0B8BC50A5C899CDA8FB4269FB4F694BF2EB36445DAA267A26D27736D17` | stored=derived `140300000`，match true | stored=derived `322100000`，match true |
| `53178360` | main/1 | `F958D0321EDFE91EEA11A25C4A5A7E1245450497ED6314B00F5B355054C4D6D0` | stored `140300000` / derived `132798475`，match false；soft `4800997`，hard/participant-hard `2700528` | stored `322100000` / derived `314910073`，match false；soft `4709424`，hard/participant-hard `2480503` |
| `53178384` | main/2 | `A6683FE0DEF812E608B3E2A8A87D6191DB3082832EAB5CDD4C14727B91C2CEED` | stored `132798475` / derived `124946803`，match false；soft `9826086`，hard/participant-hard `5527111` | stored `314910073` / derived `309820894`，match false；soft `8042853`，hard/participant-hard `4236253` |

levy cache 也独立闭合：main day 1 attacker `84300000 → 78321731`、defender
`201300000 → 195382026`；main day 2 attacker `78321731 → 72118421`、defender
`195382026 → 191206818`，四个 `stored_levy_current_matches_derived` 都为 false。

## 实现记录

1. **[completed] P1.1 identity/mailbox**：复用 actual-contact C++ resolver 与 application-main mailbox；新 query 不复制第二套
   CombatID/side reader。
2. **[completed] P1.2 retained ledger**：投影 ordered armies、两个 Entry60 buckets、participant-hard rows。
3. **[completed] P1.3 hard derivation**：只对 main-fighting row 以 checked int64 `starting-current-soft` 发布 per-entry hard；
   non-main row 返回明确 unavailable，同时保留独立 owner-history ledger，禁止混账。
4. **[completed] P1.4 current metrics**：直读 commander/roll/width/int64 advantage，并调用只读
   `0x23D2D70/0x23CC340`；不得调用 refresh/finalize mutation helper。
5. **[completed] P1.5 production surface**：C++ typed contract、serializer、严格 Python normalizer、service/MCP facade、synthetic
   generation/order/ledger tests。
6. **[completed] P1.6 live**：paused checkpoint → cold restore → bounded transition through two main casualty days；
   battle identity/hold readiness 已关闭。
7. **[completed] P1.7 active-retreat read-only projection**：同一 C++ 双采样帧追加
   selected identity、owner scope、affected/unaffected stored order、side flags 与 exact 四 gate legality；fixtures 已覆盖严格
   day 14、allow-early、四 reason 顺序、合法 `-1` fallback、mixed owner、native/raw mismatch 与超 int32 earliest date；production
   paused run 又直接证明 full-side 与 day 14 false → day 15 true。
8. **[completed] P1.8 active-retreat command/semantic layer**：Python production composition 将 battle frame、exact
   `PreviewMoveArmy`、target route 与一次性 token 全绑定，复用玩家 move command；full-side 实机看到真实 retreating/target/route，
   ACK 保持 verification pending。
9. **[live RED] P1.9 planner-integrated hold**：历史 planner 连续两轮 exact battle query、`+24` advance 与同 CombatID requery
   仍为有效证据；正式长跑又实见请求一日后 paused envelope 实际为 `+48 / phase_day +2`，旧 verifier 因硬编码单日上限阻断。
   最小 correlated-overshoot 修复与 checkpoint 复跑前不得恢复完成态；全程没有调用 retreat 或视觉 fallback。
10. **[completed] P1.10 full-CombatID transition live**：新增不依赖 retreating subject 的 paused lifecycle query；full-side
    实机闭合 `main/12→pursuit/0`、opposite winner 与双方 stored order。

下一项构造 owner-subset 场景，同时进入 reinforcement assignment/timeline query。generic native-AI destination scorer 继续作为 opponent model unknown，不阻塞
planner-selected exact target 动作。

## 复现命令

```text
py tools/file_sha256.py "Crusader Kings III/binaries/ck3.exe"

'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x23D0520 --size 0xE0
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x23CDF70 --size 0x110
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x23CB840 --size 0x90
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x23CC340 --size 0x90
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x2308D50 --size 0xA0
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x2309E80 --size 0x1A0
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x23CE080 --size 0xA0
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x27FB617 --size 0x160
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x230A590 --size 0x80
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x2308250 --size 0x600
'tools/.venv/Scripts/python.exe' 'ck3_autonomous_player/native_bridge/research/disasm_ck3.py' 0x26165B0 --size 0x80
```

关键复核点：`0x23D0520` 的 entry 初始化；`0x23CDFC3/0x23CDFCB` 的 soft/current 写点；
`0x23CB845..0x23CB8C4` 的 two-bucket tick-start cache；`0x2309E8F/0x2309EA1` 的 refresh-before-damage；
`0x2309FE8/0x230A002 → 0x23CE080 → 0x23CDF70` 的 damage 后 entry 写点；`0x2308D9A/0x2308DCE` 的 qword advantage load/store；
`0x27FB67C/+0x717` 的 in-progress byte；`0x230A5C4` 的 finalized byte。

<a id="current-v47-player-battle"></a>

## 2026-10-04：1.20.0.3 实际玩家战斗日与失败恢复

[live-confirmed / production-live loop，限定单场 battle-day及行军入战] 本节独立绑定owner已封存的g51/source1c/R24/PID32372、CK3 1.20.0.3、普通Robert29829玩家战役；复用五份sealed append/receipt，不读取旧版地址来补当前状态。CombatID1543503874、玩家defender side1、cursor17的有限“观察 → 决定有界等待 → 实际推进 → 战中重查与正常保存”子循环已覆盖03保存一日、04再保存两日并观测maneuver进入main、05再保存七日并实见main军队到达与加入defender侧。完整phase/outcome controller、terminal、玩家胜利与整局OODA仍未由这些局部证据完成；报告采用另增0保存日/0whole-OODA计数。day06不在本次封存范围。

按已关闭 attempt 时序保留以下记录。

### 1.20.0.3 实际玩家战斗：首轮零日 RED 与现有推进模式边界

2026-10-04，g51/source1c/R24/PID32372 的普通 Robert29829 战役，已关闭的 `actual-v47-player-battle-day-01` SDK18278 attempt 为 RED。实际 `003` control GREEN：玩家 defender side1、J CUnit167772189/native CArmy83886088 在2618，CombatID1543503874，enemy CUnit50331920/owner30097 为 attacker。玩家侧 commander34867、敌侧 commander30097。观察为 native57/public2/raw53241288，`battle_control_ready=true`，maneuver/raw0/day1，cadence0、roll0/0、resolvedadvantage0、combatwidth1543、winner/forcedwinner none、finalizedfalse。J仍 controllable/in_combat、非 retreat；main83886367 仍从8754沿[2632,2617,2618]向2618行军。

唯一实际推进 `005 battle-decision-epoch-advance-to-53241312` 返回 `native tactical sentinel cannot execute ...`。未推进时间：raw53241288→53241288，0h/0保存日/0 bounded成功日。`007` 正常保存 h5602、91928475B、SHA256 `1ba89bc910802652883af517bcbff0e40d8fe8e8f4aec6c793bec9a603fe4c36`；总保存日4040、Oct4+15不变。失败 attempt 保留，不重发同一 sentinel 指令。

源码定位为 `native_driver.py::execute_step` 8470–8491：base `battle-decision-epoch-advance` 不在发布的 composite steps 时，在 `_execute_battle_sentinel_advance` 调用前拒绝。1986–2005 的发布条件包含 snapshot/wait-for-change、native sentinel arm/status、paused/map_ready、无 active event/pending interaction、完整 controllable ArmyID watch set、resume-map/pause-map 与 set-speed-3。g51 `.3` descriptor 继承的 `.2` capabilities 未发布 sentinel arm/status/cancel，Crozier startup 在旧11906 sentinel install 前 return；当前没有可开启 `.3` sentinel 的已有 runtimeflag。因此这个失败不能归因于 maneuver 或 roll/input/fullv3 readiness。现有独立 `life-advance-one-day` composite（1967–1976）是当前恢复入口；Root 新尝试保持 CombatID/cursor17。

`active_combat_resume_inputs_v1` 实际 aggregate unavailable/`same_frame_resume_operands_incomplete`：四缺口为 selected_commander_next_roll_bounds、active_regiment_counter_class_stack_context、next_day_non_roll_advantage_sources、battle_knight_participation_and_dynamic_entry_transitions。两侧 next-main-roll bounds 因 `next_main_roll_not_applicable_in_phase` unavailable，作为该阶段真实字段记录；不增设推进门禁。原生 retreat legality 为 false/too_early，elapsed0，exclusive minimum14、earliest date53241648，未发 retreat。journal 仅保留初始 latest/cursor17，未消费 terminal raw 或推断结算；BattleResultID存在不代表结束。

Root 通知的独立 exact-day02 attempt 在初始001/002 snapshot unavailable阶段已关闭 RED，尚无 execute/control/post-save，0h/0day；本 lane 没有再次消费其 raw。它不是 life-advance 拒绝。最新正常保存仍 h5602/raw53241288。

可核验索引：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-first-day-consumption/ROOT-DELIVERY.json`；8个首轮实际 capture pins、缓存字段与 interval CSV 位于 actual-player-day-lane；source exactlines/pins 位于 metadata-fieldmap-lane。此次仅文件消费，SDK/游戏操作/Start/advance/测试/Git/窗口/共享编辑均为0。readiness限于 production-live primitive；未计战斗单日 loop、胜利、伤亡结算或额外保存日。

### 实际桥状态恢复与最小 battle helper 初始化适配

2026-10-04，关闭后的 diagnostics-first SDK36947 receipt 为 GREEN/normal_client_close=true，001 diagnostics、002 capabilities、003 snapshot 全 GREEN。仍为 PID32372、exact1.20.0.3，diagnostics connected=true/semantic_state_available=true、adapter ready/build_match=true、connection_generation14，last_error/transport_fatal_error null；快照 native60/public2/raw53241288、paused/map_ready true、played Robert29829、同 episode。

当前实际 composite 表发布 `life-advance-one-day` 和 `life-advance`，没有 base `battle-decision-epoch-advance`；本实际帧无 sentinel composite/native广告。此前 .3 descriptor source结论直接复用，不再重新研究。此bundle没有新的 battle control查询，不能把此前 maneuver/day1改写为 fresh phase。

`battle_speed_readiness` 的 decision/route/hold/terminal flags 实际为true，但当前战斗epoch composite仍未发布；这些flags不能替代当前可执行能力表。diagnostics的 faction async observer状态仅为其自身字段，不作为 bridge故障或战斗phase判断。

实际恢复仅证明本次三项读取成功，首轮 sentinel unsupported RED 与第二轮 initial snapshot unavailable RED 保留；不能据此证明 diagnostics priming 因果修复。源脚本 actual retry_loops=0、game_clock_input_stop_or_save_calls=0；无 restart/rebind/rollback/restore/advance/save。latest正常保存仍 h5602/raw53241288，total4040/Oct4+15、本次保存日credit0。

Root请求的外置 helper复制冻结 preimage ff920c067f29b5c0b9adf30b100b732de3324713ed96bc00c79bbb7d3644de18，仅在新client首次round的首snapshot之前调用现有 archived `ck3_get_bridge_diagnostics({})` 一次。投影 SHA256 727d4cb20ae50cb9570330420d7574d0b92630e3ad120015a708e4406c454026；prior CombatID1543503874/side1/cursor17、normalSAVE、phase/day/actualtime逻辑保持原样，无新retry/wait/gate。该适配由 Root 第三 actual attempt验证；本lane没有执行 SDK或游戏动作。

索引：ROOT-DELIVERY.json、BRIDGE-READINESS-AND-OCT4-FIELDS.json、SOURCE-PINS.json（四个 actual file pins）、HELPER-PROJECTION-ROOT-DELIVERY.json、one-hunk patch。日报/周报标记 readonly状态恢复与最小外置helper ready，不能提前计第三attempt loop成功。

### 实际玩家战斗 exact-day03：一日推进与敌方编组变化

2026-10-04，已封存 SDK65600 正常关闭 exit0；`actual-v47-player-battle-exact-day-03` 为 STOPPED/`actual_battle_decision_state_changed_requires_root`，error null。复用诊断先行外置helper执行唯一 `life-advance-one-day`，speed1/exact_one_day_unavoidable_contact，actual raw53241288→53241312（24h），正常保存1日、bounded成功1日。保存 h5607、91942797B、SHA256 `ece3d52af3e5fb39374ace119ff3104b5f70630a4b6b60a88df4375bb4be15b5`；final native64/public5/paused+mapready true，总4040→4041、Oct4+15→16。此前两次零日RED完整保留；本次成功不能证明初始化诊断的因果修复。

原 CombatID1543503874/player defender side1/J CUnit167772189/native CArmy83886088@2618 延续，original/current cursor17。control before native61/date53241288 与 after native64/date53241312 均 readytrue。phase仍 maneuver/raw0，day1→2，cadence0，roll0/0，winner/forcedwinner none、finalizedfalse。具体停止字段是 ordered_rosters + selected_commanders，不能写成 phase切换：enemy CUnit83886484/native CArmy150995083/owner35357实际加入 attacker0，与50331920/owner30097同侧；selected attacker commander30097→35357，defender commander34867保持；resolvedadvantage raw0→-3000000，width1543→1673。

双方 current stored/derived fighting raw一致：attacker131700000→157600000，defender177000000保持。此变化包含真实敌军加入，不能当作伤亡；snapshot army soldiers仍null，不冒充fresh strength query。J仍@2618/combat、controllable、route空、无retreat；main83886367实际8754→2632，仍 moving目标2618、route[2617,2618]，未进入combat。native retreat仍false/too_early，elapsed1、earliest raw53241648，未发retreat。

active resume inputs aggregate仍unavailable，四operand缺口仅入质量账；maneuver next-main-roll bounds阶段性unavailable不构成新推进门禁。readiness可记为生产实际一日有界战斗OODA loop；不计完整phase/outcome controller、玩家胜利或终结。terminal/ID-transition raw留专属outcomes owner，本lane没有消费或推断。

唯一索引：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day03-consumption/ROOT-DELIVERY.json`。11个actual file pins、完整control/command缓存、interval CSV与normalpair字段已外置。本lane无SDK/游戏动作/测试/共享修改/Git/窗口动作；报告adoption另增日数0。Root在新的独立目录据最新编组继续同Combat与cursor17，下一批不得重复计本日。

### 玩家战斗 exact-day04：两日保存与真实 maneuver→main 边界

2026-10-04，SDK34732正常关闭 exit0；封存 `actual-v47-player-battle-exact-day-04` STOPPED/`actual_battle_decision_state_changed_requires_root`、error null。本批两次 `life-advance-one-day` 各实际24h/正常保存1日/bounded1：53241312→53241336→53241360，共48h/saved2/bounded2。总4041→4043、Oct4+16→18，Root报resume890。末保存h5616、91982553B、SHA256 `a90ce4d26566ee2cd41abfeeeda3cb0957e29e83ae7519483e23b4399ce08497`，native73/public9/暂停地图就绪。同一 Combat1543503874/玩家defender1/J167772189，原始与当前journal cursor17；前一03日不重复计。

第一日 maneuver day2→3，helper changed_decision_fields=[]；第二日实际 maneuver/raw0/day3→main/raw1/day0，changed_decision_fields精确为[phase_raw]，触发停止。两日控制均readytrue，无winner/forcedwinner、finalizedfalse。main入口cadence0/roll0/0；双方selected commanders35357/34867的next-main-roll bounds由阶段性不适用变为available0..10。resume aggregate仍unavailable，但selected_commander_next_roll_bounds缺口消除，余三个operand缺口仅入质量账，不加full-v3推进门禁。

编组保持 attacker[50331920 owner30097,83886484 owner35357]，defender[J167772189 owner29829]；无新roster或commander变化。J仍@2618/combat、controllable、route空、无retreat。main83886367仍@2632/moving target2618/route[2617,2618]，尚未加入battle。native retreat false/too_early、elapsed3、earliest raw53241648，无retreat动作。

既有合同明确 resolved advantage为attacker−defender/Q100000；本批末raw-2100000=攻击方方向−21点（玩家防守方向+21仅可标派生换算）。stored fighting raw attacker157600000/defender177000000保持，Q100000缩放当前参战缓存1576/1770，不能称whole-army兵数、损失或胜率。此batch没有额外strength查询或terminalraw消费。

readiness为两次实际有界战斗OODA与maneuver→main相变观测；不是完整battle outcome controller或玩家胜利。Root依据main0真实状态继续同battle的独立后续预算。唯一索引 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day04-consumption/ROOT-DELIVERY.json`，含19个actual pins、两个正常日CSV、control/command缓存、known人物字段和sign/scale合同receipt链接；本lane无SDK/游戏动作/测试/Git/共享/窗口，报告额外credit0。

### 玩家战斗 exact-day05：七个实际保存日与主军真实加入

2026-10-04，已封存 SDK99839 正常关闭 exit0；`actual-v47-player-battle-exact-day-05` 为 STOPPED/`actual_battle_decision_state_changed_requires_root`，error null。七个正常有界 `life-advance-one-day` 分别实际24h、保存1日、bounded1；总 raw53241360→53241528（168h），saved7/bounded7，累计4043→4050、Oct4+18→25，Root报resume897。同 Combat1543503874/subject J167772189/玩家defender1、original/current cursor17。末保存 h5645、92050133B、SHA256 `3529f5f276a7ab1b489852bcd74709e5a9cfede177ddd04fbf48b7c39546ac6b`，native102/public29/paused+map_ready true。

最后第7日主军83886367/native CArmy50331794实际抵达2618：snapshot current2618/combat/in_combat true、route空、targetnull；battle control defender ordered armies从[J167772189]变成[J167772189,83886367]，两者owner29829并backlink同Combat。affected side units两军、unaffected=[]，selected defender commander34867→Robert29829。STOP字段精确为 ordered_rosters + selected_commanders；这次是按真实后态确认行军到达并加入战斗，无合军命令或phase切换。

phase main/raw1 day0→7；7个daily后态cadence为[1,2,0,1,2,0,1]，attacker/defender roll依次[2/10,2/10,2/10,8/8,8/8,8/8,2/10]。末main7/cadence1、selected commanders35357/29829、next-roll bounds双方available0..10。敌方编组仍[50331920 owner30097,83886484 owner35357]。width1673→2352，resolved advantage仍raw-2100000（attacker-oriented−21）；winner/forcedwinner none，finalizedfalse。native retreat false/too_early、elapsed10、earliest raw53241648，两支玩家军均未retreat。

严格分列末帧fighting Q100000原字段：attacker stored cache102725776、entry derived87067996；defender stored cache367832611、entry derived364444825。这些值实际不相等，分别保留，不拿差值推断终局伤亡、死亡或whole-army兵数；军队snapshot soldiers仍null。resume aggregate仍false、三个缺口仅入质量账，不加full-v3 gate；没有补查强度或terminalraw。

readiness为七个连续实际有界战斗日，以及主军行军到同一玩家battle side的有限loop；不计完整战争/战斗结束或玩家胜利。06运行中目录不读，待Root封存再独立计新日；不得重复03/04/05任何保存日。索引 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day05-consumption/ROOT-DELIVERY.json`，59个actual pins、日interval与control/command/SAVE缓存、日级轨迹CSV lane及Oct4/W40 fields；本lane SDK/游戏动作/测试/Git/窗口/共享修改全0，报告额外credit0。

### 字段尺度与当前封存边界

尺度沿用此前已消费的owner [ADVANTAGE-SCALE-RECEIPT.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-first-day-consumption/metadata-fieldmap-lane/ADVANTAGE-SCALE-RECEIPT.json)；本次只读05 sealed summary/append/日周字段，不重复读取raw、query、capability、sourcecpp或cached-trajectory lane。

| 字段 | 已封存变化 / 05末帧 | 限定解释 |
|---|---|---|
| `resolved_advantage_raw` | 03为`0 → -3000000`；04、05末为`-2100000`，signed Q100000 | 全局attacker-minus-defender，分别为`-30`、`-21` attacker points；玩家defender相对`+30/+21`仅派生换算，不是新增原生字段或胜率 |
| current-fighting Q100000 | 05 attacker stored cache`102725776` / entry derived`87067996`；defender stored cache`367832611` / entry derived`364444825` | cache与derived分别保留且实际不相等；不以差值认定伤亡、死亡、whole-army兵数或胜率。03/04的`1576/1770`是当时缩放的cache，不能当作05fresh人数。snapshot soldiers仍null，无额外strength查询 |
| 停止原因 | 03：rosters+commanders；04：`[phase_raw]`；05第7round：`[ordered_rosters,selected_commanders]` | 04是maneuver day3→main day0；05是主军抵达并加入defender，仍main，无合军命令或phase切换 |
| 05主军入战 | CUnit83886367 / native CArmy50331794；current2618、in_combat true、route空、targetnull | 与J167772189形成defender stored order`[J167772189,83886367]`，两者owner29829、backlink同Combat1543503874；selected defender commander34867→Robert29829 |
| phase / cadence / roll | 05 main/raw1/day0→7；末cadence1、attacker/defender roll`2/10`；width2352 | winner/forcedwinner none、finalizedfalse；双方next-roll bounds仍available`0..10`，三个resume缺口仅入质量账、aggregatefalse，无新增gate |
| 当前normal SAVE | h5645 / raw53241528 / 92050133B；native102/public29/paused+map_ready | SHA256 `3529f5f276a7ab1b489852bcd74709e5a9cfede177ddd04fbf48b7c39546ac6b`；total4050 / resume897（Root报告）/ Oct4+25；05实际168h、saved7/bounded7，与03/04各自分开计，文档采用另增0日 |
| 当前continuation | 同Combat1543503874 / player side1 / original=current cursor17；两军defender、Robert29829 commander | native retreat仍false/too_early、elapsed10、earliest raw53241648，两军未retreat；06运行中未纳入本包 |

既有`.3` capability结论与两次零日RED原样保留：当时发布`life-advance-one-day`，未发布可执行battle sentinel epoch；首轮拒绝在native sentinel调用前，第二轮仅初始snapshot unavailable。只读恢复以及03/04/05成功分别成立，不据此声称diagnostics priming是因果修复，也不新增重试或门禁。

04进入main时next-main-roll bounds已available；余三个operand为active_regiment_counter_class_stack_context、next_day_non_roll_advantage_sources、battle_knight_participation_and_dynamic_entry_transitions，05仍为质量账。当前新价值是七个连续实际battle-day与main军队的行军入战，完整battle outcome controller、terminal、玩家胜利和整局OODA仍未由这些证据完成。Root已启动06独立预算；本包不读取06、不预计其日数或结论，终结/ID-transition raw留专属outcomes owner。05 primary已sole封存，无需等cached-trajectory追加lane才能采用。


<a id="v47-postbattle-06-09"></a>

## 2026-10-04：06–09有限战斗循环、零日RED与战后regular

[production-live loop，限定同一单场战斗] 本次只续接已发布05之后的sealed owner字段，沿用R24普通Robert29829、CK3 1.20.0.3、Combat1543503874/player defender1/cursor17的实际战役。06/07/09分别保存5/2/4日，合计11个新保存日；08与只读诊断02均0日。文档采用另增0日，不重复03–05或新建whole-OODA计数。

| 已封存attempt | 实际推进与正常SAVE | 可核验状态与停止边界 |
|---|---|---|
| 06 / SDK68214 closed exit0 | 120h / saved5 / bounded5；h5666/raw53241648；total4055/res902/Oct4+30 | main7→12；第5round仅`retreat_legal_now`变化：elapsed14 false/too_early→elapsed15 true/reasons空。两玩家军仍2618/in_combat、nonretreat；没有retreat动作，资格不等于已撤退 |
| 07 / SDK1424 closed exit0 | 48h / saved2 / bounded2；h5676/raw53241696；total4057/res904/Oct4+32 | 第二round main13→pursuit0，winner none→defender1、forcedwinner-1、finalizedfalse；两我军仍combat/nonretreat。current winner已观测，尚不能单凭此帧认定终局；retreat资格因pursuit转false |
| 08 / SDK54525 closed exit1 | initial/finalization snapshot RED；0h / 0saved / 0bounded；无execute或SAVE | diagnostics虽GREEN，gen20 semantic_state_available=false/heartbeat absent；工具“state not available yet”不证明CK3真的loading或pursuit不能推进。source RED与file consumer首attempt RED分别保留，无fresh状态，不改07结论 |
| pursuit diagnostics02 / closed GREEN | 独立diag→cap→snapshot三项GREEN；0保存日；raw53241696 | 新gen21 semantic=true、heartbeat present、native136/public2/paused+map_ready；life-advance-one-day已发布，battle epoch/sentinel广告空。只说明当前读取恢复；v48 helper首次diagnostics后加一次capabilities输入，不证明priming因果修复，不增retry/wait/gate |
| 09 / SDK99589 closed exit0 | 96h / saved4 / bounded4；h5697/raw53241792；total4061/res908/Oct4+36 | STOP=`actual_subject_left_combat_requires_root`。fresh末snapshot两军regular/state1、controllable、in_combat=false、retreating=false、route空/targetnull，均current2618；没有合军或新军令 |

09末正常SAVE为92163403B、SHA256 `10ee6273a5521493576bf41b7a90bb1dad6be5eb36b8b796b412e4d7f52ca0ec`，native152/public17/paused+map_ready。最后一天已出combat，没有post-step battle-control；最后control是before raw53241768/native149/pursuit3/currentwinner defender/finalizedfalse历史帧，不能冒充raw53241792当前combat或终局字段。

06的current-fighting stored/derived仍分别保存Q100000，07的attacker fighting0不等于全部死亡/wipe或最终损失；不以cache差值推断伤亡、whole-army人数或胜率。阶段不适用的next-main-roll bounds与resume三/四缺口保留质量账，不加full-v3推进门禁。08失败、只读恢复和09成功分别成立，不把后来成功改写成根因修复。

专属owner已封存该场真实normal_result/event58/winner defender1。这里只引用 [terminal owner回执](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-casualty-outcomes/player-combat-1543503874-actual-terminal/ROOT-DELIVERY.json) 与 [后续link addendum](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day09-consumption/TERMINAL-OWNER-LINK-ADDENDUM.json)，终结/人物/损失/warscore由专属专题维护，未二读terminal body。09原receipt的terminal pending仅是当时事实，后续addendum闭合最终结果。当前完成的是这一场实际玩家battle loop，不升级完整通用battle/战争controller；文档整合不新增胜利或终结信用。

[21个既有正常保存日索引](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-first-battle-saved-days-index/ROOT-DELIVERY.json) 与 [CSV](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-first-battle-saved-days-index/TWENTY-ONE-NORMAL-SAVED-DAYS.csv) 仅链接，未二解析；失败/诊断没有day row。

sealed来源： [06](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day06-consumption/ROOT-DELIVERY.json)、[07](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day07-consumption/ROOT-DELIVERY.json)、[08](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day08-consumption/ROOT-DELIVERY.json)、[diagnostics02](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/pursuit-v47-bridge-diagnostics-02/ROOT-DELIVERY.json)、[09](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/player-v47-exact-day09-consumption/ROOT-DELIVERY.json)。本增量SDK/raw/query/cap/source audit/Git/tests/window/shared动作均0。

### 2026-10-04：第三场 2629 战斗实际新增敌军 473（v51/day01）

`Combat1593835526` 的同一份归一化 `DAY01-CACHED-CRITICAL.json` 保留了推进前后军列：maneuver day1 attacker 为 `[251658381]`，day2 变为 `[251658381,473]`；defender 始终仅 `[83886367]`。新增项为 public CUnit `473`、native CArmy `461`、owner `70766`、`combat_backlink_id=1593835526`，是本战实际加入。两侧当前 commander 分别仍为 `70766 / Robert29829`，没有 commander-change 信用。

| 同战观察 | attacker ordered CUnit IDs | defender ordered CUnit IDs | 已验证新增 |
| --- | --- | --- | --- |
| 推进前，maneuver day1 | `[251658381]` | `[83886367]` | — |
| 正常一日后，maneuver day2 | `[251658381,473]` | `[83886367]` | attacker `473` |

一日为 raw `53248344→53248368`（`+24`）；终帧 `native:1141 / public revision5 / native revision1141 / paused=true`。两侧当前 stored 与 derived fighting 相等：attacker `295700000`、defender `391100000`，Q100000 后为 `2957 / 3911`。resolved advantage raw `-1000000`，attacker 视角 `-10`、defender `+10`；没有证据把这项变化或人数差额单独归因于 join。本 cache 没有发布该 post-join 帧逐军 current/max，不能从 Root 提供的起始整军 `1944` 与侧 fighting `2957` 差额推出 473 的加入人数或伤亡。

此前 day55 的 `Combat1577058310` 实际 attacker 为 `150995107`，`251658381/473` 尚在 `2628` 且未加入；当时 `1363+2066+1134=4563` 只是条件整军人数算式。旧数与第三战不是同一 Combat/帧，不覆盖新的 actual `2957`，也不构成加入时刻或成功率预测。join 的原生语义见 [battle-reinforcement-and-join.md](battle-reinforcement-and-join.md)。

一日观察器因 `ordered_rosters` 改变而暂停，stop reason 为 `actual_battle_decision_state_changed_requires_root`；新军列经同 Combat backlink 验证并正常保存，有限的“前帧 → 正常日 → 军列变化暂停 → 后帧验证/保存”达到 `production-live loop`。本战仍 `winner=none/finalized=false`；retreat 原生结果为 elapsed `1`、`legal_now=false/reason=too_early`。没有解围完成、战斗终态、完整战役或新的候选门禁信用，Root 已继续执行后续实际战斗。

normalSAVE：`h6565 / date53248368 / 93544360 B / SHA532c1edf19ed41ee5c77f45ad55284576447b04132e974ac1ddb570c586c2323`。源归一化 cache `9784 B / SHA4c2d9a1359d85c3ab013e14fefbf79544e507253ac2f898fa1e101fb4d21257c`，本消费者仅读一次、0 raw/SDK/推进。军事 owner 已计该一日，截止 global `4335 / resumed1182 / Oct4+310`；消费者附加信用为 `0`。实际 binding 按 cache 保留 `R25/Py g56/nativeg54`；已构建但未部署的 g57 不作此帧 runtime 证据。封存包：`army-reinforcement-raise/runtime-v51-third-battle-actual-join-consumption/ROOT-FINAL-DELIVERY.json`。
