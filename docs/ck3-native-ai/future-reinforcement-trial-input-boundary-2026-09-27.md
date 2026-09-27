# CK3 1.19.0.6：未来增援路线输入与整场 trial 的边界

本页研究的是**当前暂停帧能否提前产生某个既有 CombatID 的 `participant-update` 事件**，而不是已经抵达后的战宽计算。版本限定为 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。R0244 所需的同帧 v3 接战查询已有独立交付；其原始 War 48 仍待请求方复验，本页不改变该 response 或已有胜率结论。

## 现有读口实际能给什么

| 来源 | 当前帧可核验的事实 | 不能由此推出的未来事实 |
| --- | --- | --- |
| `query-route-contact-horizon-v1-...` | 一个**可控** subject 的已提交或预览路线、逐边 `arrival_date_raws`，以及全部当前敌军的路线；`one_day_contact_free`/`conflicts` 只覆盖 `[date_raw,date_raw+24]`。Python 正规化要求完整敌军作用域、同日与 revision。 | 友方 AI 增援的援助意图、整条路线未来都无接触、目标日仍按原路线行军、目标 CombatID 仍存在。不能把完整路线时间数组误当完整路线的接战证明。 |
| `query-battle-reinforcement-assignment-v1-<CUnitID>` | generation-validated AI stack 的 `asking_for_help`、`assigned_to_help`、assignment Province；已对齐的当前 CUnit route 可给 `assignment_eta_date_raw`，普通 route 也可能有 `arrival_date_raws`。读口双采样并绑定 paused date/revision。 | assignment target 是 Province，**不是 future CombatID**；`contact_if_now_selected_combat_id` 的合同明确为 `present_time_only_not_future_binding`。无 assignment 的普通移动也可能抵达同一省；052 的实际军队就未出现 help assignment。已提交路线也可在下一次 AI 决策、撤退或受阻后变化。 |
| `query-battle-control-snapshot-v1-<CUnitID>` | 可控且已开战 subject 的当前 CombatID、两侧 stored-order CArmy/CUnit/owner、完整 entry 与当前战宽。 | 不可控 AI-only 战斗没有该读口的可控 subject 门；当前 roster 不能包含未来尚未加入的 entry，也不能给未来主阶段前旧 entry 刷新值。 |
| `query-combat-simulation-inputs-v3-...` | 显式列举、同一 active war 的双方 ArmyID，在当前目标 Province 的逐团/骑士属性、反制及其他接战输入；v3 phase roster 严格等于 v2 base roster。 | 它是**当前帧假设接战**的有序输入，不是已有 CCombat 的未来 entry 快照；不能从其当前 `CRegiment` 值构造抵达日的伤亡、有效属性、selected commander 或旧 entry pools。 |
| 078 join 观测 + 静态 join spine | Army 22 在同日进入 Combat `16777218` 后，缓存战宽 `(1645,1480)→(2467,2220)`；入场当前 totals 为 `[410690163,82785368]` Q100000。join 按 stored-order tail append，并在后段刷新两侧 cache。 | 078 原始 collector 仍 RED、phase-fire 第三点缺失；该旧案例不能替代任意当前帧的未来 ETA/名单，更不能用旧 cache 加新军人数。080 同 hook full-entry 合同尚未实采。 |

路线读口的边界直接来自 `war_contract.py` 的 `normalize_route_contact_horizon`/`_normalize_timed_route`，`ck3_11906.cpp` 的 `BuildSubjectRouteTimeline`/`ProjectPathTimeline`。AI assignment 的 `ReadBattleReinforcementRoute` 仅在 direct `CUnit+0x30` 与 route final 都指向分配目标、时间轴可用时发布 ETA；`ReadBattleReinforcementContactProjection` 只扫描**现在** Province 的 active combat。`battle_reinforcement_assignment_contract.py` 对 `unbound_until_contact` 和 present-time semantics 均作严格校验。[增援专题](battle-reinforcement-and-join.md#future-assignment-与-eta-从哪里读)给出了对应原生地址和历史 live 门；其中 `native_assignment_live_ready=false`、`aligned_assignment_eta_live_ready=false`，不能写成已在生产战况观察到完整 help-assignment→ETA→同 CombatID join。

## 为什么现在不能生成生产 `participant-update`

一个可交给整场 trial 的事件必须至少确定 `{CombatID, native date/phase order, incoming full CUnitID/CArmyID, side, ordered new RegimentID/knight states, same-day refreshed old entries, both post-join +0x98 totals, width update gate}`。现有来源的组合在以下位置断开：

1. **未来 CombatID 与 side 不是 route 字段。** 到达时 `0x2208320` 才按目标 Province 当时的 active combat stored order 和 owner 对双方代表的 XOR hostility 选择最后一个 compatible CombatID；`0x23040A0` 再用反向关系判 side。同日其他军先后到达也改变可见候选和 tail-append 顺序。现在的 `contact_if_now_selected_combat_id` 不能预签未来选择。
2. **ETA 是当前路线的条件投影。** route timeline 使用当前速度、首边 progress、相邻省和现有 route；它不承诺到达前没有新命令、截击、撤退、战斗终局或跨日属性变化。`route-contact-horizon` 虽返回全路线时间数组，却只给一日接战证明。AI 求援链的首边 duration 也不是完整 assignment ETA。
3. **入场名单需要同日状态。** v3 可以读当前 CRegiment 及当前有效属性；join 会依当时 CArmy 的 RegimentID 顺序建新 entry，首次 schedule 前又可能刷新旧/新团属性。仅冻结今天的 v3 与 ETA，不能得出入场日的 current/soft/hard、骑士状态、旧 roster 更新后 totals 或战宽输入。078 的旧缓存与 entry 求和相差 `5627319` Q100000，已实证不能用“旧 cache + 新军”填空。
4. **trial kernel 目前冻结名单。** `research_envelope.py` 在 trial 开头固定 army/entry/counter census，后续每日都用同一个 `encounter.final_width`。只加入一个日期或只更新战宽，会让出伤、承伤和 counter 名册不一致；生产 `forecast_fixed_contact` 正确地继续标 `fixed_participants`。

因此这轮**不增加会宣称未来 join 已确认的 typed producer，也不向生产 forecast 注入历史 Army 22**。已有 route、assignment、battle-control、v3 都是严格 typed 只读合同；缺的是跨读口、跨未来日期的真实事件证据，而不是 JSON 字段校验。能安全供用户看的只是“若当前路线和战斗持续，此军预计在 raw 日期 X 到目标 Province”的**条件候选**，不得称为“raw 日期 X 加入 CombatID Y”。

## 下一道可执行的采集与接线合同

1. 在同一暂停帧保留 `snapshot_id`、公开/native revision、connection generation、episode、`date_raw`，查询相关 AI CUnit 的 assignment 和 route、当前 CCombat 两侧 roster/entries、显式当前 v3 逐团输入。若该战斗没有可控 subject，现有 battle-control 读口不能提供完整 entry，须另建 generation-bound 的只读 battle reader，不可拼历史帧。若查询间任一 identity/revision/route 改变，整组丢弃；无 assignment 或不对齐时只能标 `candidate_route_only`，不能补猜 assignment ETA。即使 aligned ETA 等于当前日期，也不能把“已经在目标省”当作已入战。可控 subject 的 route-contact 只作为**一天**接触门。
2. 为自然发生的正例，在不改变原版状态的逐日受管回放里，按日重新查询同一 CUnit 的 assignment、route、ETA 与 Combat 的存在/两侧名单。要求先观察真实 `assigned_to_help=true` 且 `route_alignment=aligned_to_assignment`，随后到达同一 Province；若中途改路、撤退或战斗结束，记录分叉而不是继续沿用旧 ETA。052 仅证明普通移动，不能代替该正例。
3. 到达当日以 080 的**同一次 wrapper 入口/返回**采两侧完整 entry 和 incoming CArmy regiment 顺序，并记录 contact queue/stored combat 候选、实际 selected CombatID/side、原生日期与 phase 顺序；首次 side0 出伤钩子须回读实际 `R8D`。同一 CombatID/日期和完整 ID/指针代际、两侧 `cache-Σentry.current`、old-row 变化、新 entry、`+0x6C0/+0x6C4` 与宽度更新门逐项核对。任何一项缺失保留 RED/partial，不能用 078 补齐。
4. 先用上述**实采事件**建立只读投影器与离线回归；trial 只接受带来源与完整状态的显式 `participant-update`，在对应日先扩双方 army/entry/counter 名册，再以 event 的刷新后 totals 更新战宽，随后两侧使用同一 final width 出伤。未来 ETA 进入策略时仍为条件场景，逐帧重估并对照实际 join/terminal；不能把条件场景的 trial 分布改名为原版无条件整场胜率。

当前 Steam 离线 UI 新鲜帧门为 RED，079 没有启动 CK3；本页仅静态核验，不报告新的实机成功。相关原始案例、限制与 080 合同见[战宽专题](join-width-production-and-fire.md#080-私有同帧-full-entry-取样合同只设计未启动)及[通用策略接线](general-battle-strategy-forecast-2026-09-26.md)。

## 2026-09-27 后续证据范围更新

上段记述的是本页写成时的 079 门禁，不代表全天都未能实机回放。桌面后来恢复，[独立 083 attempt](join-width-production-and-fire.md#083-同一次自然增援的三点实采)取得同一 CombatID/ArmyID/日期的 join 入口、返回、首次 side0 出伤三点：base/final `1645/1480→2467/2220`，实际出伤入参 `R8D=2220`，collector 与清场回执通过。它闭合**这一次 join 的宽度传递**，但没有补出未来 ETA 或当次 wrapper 同帧 full-entry；上述 `participant-update` 的跨未来日期缺口维持不变。[080 同帧 full-entry 采集器](join-full-entry-collector-static-080.md)已实现并通过聚焦离线测试，尚待独立实机 attempt。
