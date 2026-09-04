# Cross-cycle endgame production choreography（离线取证）

取证基线：`d97527f`；目标构建：CK3 `1.19.0.6`，`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

状态：`static-ready-live-pending`。本次只读产品脚本、现有 seed 合同和前三条
source-checkpoint 合同；未启动 CK3，未使用 fixture、控制台或命令 ACK，也没有生成新的
live checkpoint。

## 结论

在当前可选起点中，**最短的合格候选是 owner-facing 的 `zg361cp.26` 项目
checkpoint**，不是 registry 中排在它后面的 `zg361.50`：Central 的产品顺序是 stage 3
promotion、stage 4–6 incidents、stage 7 metrics、stage 8 credit/project、stage 9 career
learning、stage 10 manager governance、stage 11 Workforce。registry 行顺序是宣传 span
顺序，不是游戏时间顺序。

但 `zg361cp.26` 只有同时满足以下条件时才是合法 endgame 起点：checkpoint 仍属于一个
未漂移的真实 Central tuple；当前玩家就是事件 root/owner；后续一直沿同一个
owner/subject/cycle 运行；而且若目标不仅是第一个 `zg361we.356`，还要在同一 cell 到达
`#360C -> #361`，该存档必须已经带有前两次合格 Workforce cycle 的历史。当前 schema-2
source registry 记录 event/owner/player/date/save lineage，却不发布 Central stage 或
Workforce completed-cycle ledger，因此**仅有 registry receipt 不能证明这些条件**。

`zg361we.356` 的最后一跳很短且完全确定：在 AL state 1 的真实 owner-facing
`zg361we.355` 选择任一可见路线；三条产品 option 都在同一 effect 完成后立即
`trigger_event = { id = zg361we.356 }`，没有日期推进。source capture 随后只查询
`#356` 的 event/root/saved-scopes/options 并保存原字节 checkpoint，不能选 option 或推进
时间。

## 起点排序与合法路径

| 起点 | 玩家视角和位置 | 到 `#356` 的最短合法路径 | 资格结论 |
|---|---|---|---|
| paused seed | player `29037`；matrix owner `32904`；seed 是 bootstrap-fixture 生成的 restart base | 用真实产品闭合 B1 publication，然后从 Central stage 1 依次跑到 stage 11，完成 Workforce AB→AC→AD→AL，在 `#355` 选 option | 不能直接作为 owner-facing `#356` 起点。若未来 AL owner 仍为 `32904` 且 player 仍为 `29037`，`is_ai = no` / `this = owner` 明确不成立；只能通过正常游戏形成“玩家就是 celestial-liege owner”的新 cycle，不能 rebind |
| `zg361.50` incident prefix | received-self：player 是 subject，notice owner 必须不同 | 选固定 option 1，完成真实 result flow；随后仍需 Central 未完成 stages 和 Workforce 全组合 | 这是 incident span 的正确 source，但不是同一帧可继续的 owner-facing endgame anchor；禁止用 generic player rebind 跨过该角色差异 |
| `zg361pp.147` promotion prefix | owner-facing，Central stage 3 portfolio 内 | 选固定 option 1，完成 promotion/compensation 及 stages 4–11，再完成 AB→AC→AD→AL，`#355` 选 option | 合法 fallback，前提是同一 Central tuple 和 player=owner 持续成立 |
| `zg361cp.26` projects prefix | owner-facing，Central stage 8 credit/project portfolio 内 | 按已捕获 route A/B 选 option，完成项目 portfolio；再完成 stages 9、10、11 和 AB→AC→AD→AL，`#355` 选 option | 最短候选；仍须在 restore 后由真实 paused state 验证 tuple/角色/历史，不可只按 registry 行号选择 |

仓库在此基线上定义的前三条 prefix 是：

1. `capture_promotion_compensation` → `zg361pp.147`
2. `capture_projects_metrics` → `zg361cp.26`
3. `capture_incidents_operations` → `zg361.50`

2026-09-04 本次离线审计在仓库和已索引的 process-assets 中没有发现可直接消费的
三条真实 schema-2 prefix manifest。因此上表是生产恢复时的选择规则，不是“该
checkpoint 已存在且可达”的 live 声明。

## 必须冻结的 tuple

进入 Central 前，owner 必须是启用规则的 celestial liege，并有同一 review cycle 的真实
B1 closure：`b1_cycle_state=8`、`b1_closure_state=4`，且 M013 route A/B 有当前 receipt，
或 route C 有当前 policy-debt proof。Central 随后冻结：

- `p2c owner = 当前玩家 = celestial-liege owner`；
- `p2c subject = 一个真实 direct reviewable vassal`；
- `p2c cycle = review_serial = b1_cycle`；
- `p2c case` 是 Central 自己的 serial；B1 result case 和各 domain case 不得互换。

进入 `#355/#356` 时，Workforce AL 又冻结同一 owner/subject/cycle 和自己的 AL case；
必须满足 AL active、state 1，事件 root 必须等于 owner，并且 owner 必须是非 AI 的
celestial liege。restore 后任何 owner、subject、cycle、AL case 或 played-character 漂移都
应 typed RED；不得靠一个已提交的 click ACK 继续。

若这个 `#356` 还要供现有 cross-cycle endgame cell 使用，则有一项额外的跨周期前置：
M360 后的 history gate 只有在 owner ledger 恰有 3 个按 cycle 严格递增的 completed
Workforce cycles，且第三条就是当前 AL cycle/case/subject 时，才会准备 M361 evidence。
第一或第二 cycle 的 `#356` 是真实、可见、可保存的 source，但它之后会走
history-accruing close，不会出现 `#361`；因此不能冒充该 cell 的合格 source。

## 动作和时间推进

生产会话的统一规则是：有事件时先暂停，查询 exact event definition、root、saved scopes
和 enabled option；只提交该事件的显式 authored option。没有事件时才允许 speed 1 / resume，
并在每次新窗口出现时立即暂停重查。ACK 只说明输入已提交。

从最短候选 `zg361cp.26` 起：

1. restore bytes/SHA/save-lineage 绑定的 product-only checkpoint；验证 `player=event root=
   project owner`，以及 saved subject/cycle/case 与当前 Central tuple 一致。
2. 重放 receipt 指定的 route A 或 B。产品从 `#26` 到下一项目窗口含 D+1 边；继续逐个处理
   项目窗口直到 stage 8 的 portfolio closure 被 Central 观察到。
3. Central serial pump 只能按 stage 9 → 10 → 11 前进。正常 pump 重试是 D+2；domain 内
   还有 D+1 transition gaps。静态脚本不能给出 stage 8 到 AL 的单一确定天数，因为它取决于
   实际候选、窗口选择和 deadline；应采用有上限的 speed-1 观察，而不是跳日期。
4. stage 11 打开并真实完成 Workforce AB → AC → AD → AL。AL launch 冻结当前
   owner/subject/cycle/case，若 owner 是人类 celestial liege，立即打开 `zg361we.355`。
5. 在 `#355` 查询三项 option 后选一项；产品同 tick 打开 `zg361we.356`。暂停、不选择
   `#356`，调用 save-checkpoint，记录 bytes/SHA/seed+capture lineage/source receipt。

从 promotion checkpoint 起要先补 stage 3 的其余窗口及 stages 4–8；从 received-self
incident 或 seed 起还要补更早的 B1/Central 路径。不得把一个宣传 span 的 checkpoint
receipt 当成修改游戏状态的 action。

## `#356` 之后的边界

现有 exact-build live seam 固定选择 `#356` option 1（route A）。产品将 AL 从 state 1
推进到 state 2，并设置 `awaiting_al_357_359=1`、`portfolio_status=5`；这是 external wait，
不是成功。然后允许真实时间推进，当前 runner 上限为 **730 game days**：

1. B1 必须产生 M357 state-8 receipt；B2 必须产生 M358 state-3、route!=C receipt，及
   M359 state-2/3、route!=C receipt。三个 receipt id/hash 都必须为正且两两不同，
   owner/subject/cycle 必须匹配。
2. Central stage 11 的唯一自动 handoff 消费上述真实 receipts；bridge 顺序推进 AL
   2→3→4，并标记 external count=3、last operation=359。
3. Central 还必须冻结三个不同 manager 的 M360 sources，cohort count=3、total quota 1..6，
   且第一个 manager 就是当前 AL subject。缺 source、N/A 或 identity drift 都不能打开
   `zg361we.360`。
4. 在 owner-facing `#360` 选择 option 3（route C）。它把 AL 4→5，建立
   `m360_debt_due_cycle = current cycle + 1`，而不是建立成功 business object；满足第三周期
   history gate 后，产品同 tick 打开 owner-facing `zg361we.361`。
5. `#361` 必须仍是相同 owner/subject/cycle/case，AL state 5，external receipts verified，
   且三周期 evidence ready/未消费。此窗口和保存后的 bytes/SHA 是 owner-visible result
   checkpoint；option ACK 本身仍不是 Workforce postcondition。

## 尚未闭合的 production seam

Workforce provider 是 **played-subject 侧**的现有只读查询，owner 只是请求 filter；
`#356/#360/#361` 则要求 **played-owner**。同一未变 player frame 不可能同时证明两边。
现有 `zg361_phase2_cross_cycle_endgame_live_seam.py` 在保存 `#361` 后使用命名的
acceptance-only typed event fixture 完成 owner→subject transition；它明确不是任意 rebind，
也不写 business state，但仍然不是 production-only 证明。

所以当前可以诚实关闭的是：真实 `#356` source capture 的静态接入和
`#356 → real M357–359 → #360C → owner-visible #361` 的产品 choreography。仍未关闭的是：

- 一个真实、第三周期合格的 `#356` paused checkpoint；
- 从该 checkpoint 实跑到 `#361` 的 no-fixture live artifact；
- 保存 `#361` 后，通过正常产品 lifecycle/reload 让同 lineage 的 subject 成为 played
  character，再由既有 Workforce provider 观察业务 postcondition。

在最后一项完成前，readiness 保持 `live-pending`。事件可见、save ACK、option ACK、fixture
transition 或 generic rebind 都不得把它改成 GREEN。

## 静态证据入口

- `tools/zg361_phase2_seed_contract.json`
- `tools/zhongguo_phase2_source_checkpoint_provider.py`
- `tools/zhongguo_phase2_event_choreography.py`
- `mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_004_lifecycle_hooks_effects.txt`
- `mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_010_serial_pump_effects.txt`
- `mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_009_stage11_workforce_endgame_effects.txt`
- `mod_zhongguo_style/events/zg361_workforce_endgame_event_009_m355_target_ratchet_events.txt`
- `mod_zhongguo_style/events/zg361_workforce_endgame_event_010_m356_outcome_timing_events.txt`
- `mod_zhongguo_style/events/zg361_workforce_endgame_event_011a_al_m360_collective_events.txt`
- `mod_zhongguo_style/events/zg361_workforce_endgame_event_011b_al_m361_charter_events.txt`
- `mod_zhongguo_style/common/scripted_effects/zg361_b2_collective_receipt_handoff_effects.txt`
- `mod_zhongguo_style/common/scripted_effects/zg361_workforce_endgame_002_al_receipt_bridge_effects.txt`
- `mod_zhongguo_style/common/scripted_effects/zg361_workforce_endgame_007_m361_charter_history_gate_effects.txt`
- `tools/zg361_phase2_cross_cycle_endgame_source_capture.py`
- `tools/zg361_phase2_cross_cycle_endgame_live_seam.py`
