# 游玩智能体战中撤退：目的地种子与单跳门

日期：2026-09-27。对象为**我方自有策略**的目的地输入，不是原版 AI 的候选枚举、目的地评分或胜率阈值。普通战争原版 AI 的这三项仍为 unknown；引擎可执行边界见 [主动撤退总专题](active-combat-retreat.md)，策略总缺口见 [队列生产端审计](ordinary-war-active-retreat-queue-audit-2026-09-27.md)。本轮没有启动 CK3；Steam 当前可读离线画面门仍为 RED。

## 已落地的最小候选来源

`native_driver._action_steps` 原先给战中 CUnit 的移动预览目标主要是敌军当前省、我军已有移动目标、敌方默认集结省、战争目标省。这些是接敌/战役目标，不是可靠的撤退目的地。现在对**paused、可控且仍在 active combat** 的 CUnit，额外发布指向当前快照里其他驻扎的**玩家可控军队**所在地的只读 `preview-move-army-<CUnit>-to-<Province>`。驻军必须为 `regular`/`sieging`，不能正处战斗或撤退；目标不能等于本场省，也不能是已观测敌军当前省、移动目标或路由上的省。此步只产生目的地种子，不能证明可达、安全或适合撤退；没有对应我军时可以合法返回空集。盟军省份暂不作为通用种子，因为此投影尚无战中 CombatID 到具体 WarID 的绑定，不能把另一场战争的盟军混入。

已有 `_fresh_preview_first_hop_steps` 会从**同一 paused snapshot ID、public/native revision、日期、episode 和连接世代**的成功原生 `PreviewMoveArmy` 路线提取第一站，发布第一站的 exact preview 和完整敌军 scope 的 route-contact 查询。对 active-combat CUnit，本轮禁止它顺带发布第一站的直接 `move-army` 字面命令：必须走 `preview-active-combat-retreat-v1` 的 native legality、scope、exact route 与一次性 token，再用 `order-active-combat-retreat-v1` 提交。非战中 first-hop 行为保持原样。

## 策略接入的可核验合同

目的地选择可以沿下列顺序消费上述能力；任何前置证据缺失时保持暂停并返回结构化 unknown，而非猜一个省：

1. 战中当前帧确认 `WarID/CombatID/CUnit/owner`、`side_scope=full_side`、`legal_now=true`。`owner_subset` 尚缺完整 live 后置验收，不能自动进入首批动作。
2. 为每个我军驻地种子取同帧 exact `PreviewMoveArmy`。若原生路线超过一站，只把其**第一站**作为新候选，再针对第一站重新取 exact 原生预览；候选路线去掉可选 origin 前缀后必须恰为 `[target]`。初始长路线不能冒充单跳撤退路线。
3. 在同一暂停帧绑定完整、唯一的非撤退敌军 ID 范围及其路线/时间信息。先排除目的地/单跳路线上已观测的敌军当前、目标或路径冲突，再对该第一站做 `query-route-contact-horizon-v1`；要求查询的 snapshot ID、public/native revision、日期、episode、连接世代、subject、target、完整敌军 ID 和原生路线均与选定帧一致，`one_day_contact_free=true`。还必须要求 `subject_route.arrival_date_raws[-1] <= horizon_end_date_raw`，这样这条单跳路在所检查的一日内确已到站；若预计抵达时间超过该窗口，或 native query 在战中 CUnit 上不能给有效 subject route，必须标 unknown，不能把一日无冲突外推到整个撤退行程。
4. 安全候选按确定性规则排序（例如本回合显式的战役价值、可观测 ETA，再以 ProvinceID 打破完全同分）；原版 AI 的 destination score/tie-break 仍保持 unknown。选择结果必须写入回执，不能仅保存一个隐式 ID。
5. 对最终目标调用 typed `preview-active-combat-retreat-v1`，只消费其中的 `target_preview.order_step`。提交前 bridge 会重新读取 battle-control、重新预览路线、核对 revision/CombatID/side/scope/affected 与一次性 token；任何变化直接拒绝并重观测。
6. `order` 的 `accepted_verification_pending` 只是提交回执。新 paused revision 对 affected CUnit 的 `retreating`、target、route 逐一读回，并按旧完整 CombatID 查询 full-side winner/phase；mixed-owner 要另核对 unaffected entries、backlinks 和同步 pursuit。不能用 ACK、单一 `route` 字段或一天后的自动败退代替完整后置条件。

当前代码只实现**目的地种子和第一站防绕过**；第 3 项中的战中 route-contact 原生查询与到站时间边界尚无生产 live 配对，策略也尚未将这些步骤连成自动撤退选择。它们是启动前必须验证的能力条件，不应作为“尚未研究原版 AI”而搁置全部我方策略，但也不能将静态可构造的命令写成已经自动安全撤退。对应聚焦检查为 `test_active_combat_retreat_destination_seeds.py`、`test_native_first_hop_projection.py` 与既有 `test_active_combat_retreat_v1_bridge.py`，共 30 项 no-launch PASS；没有新增实机 GREEN。

静态检查给第 3 项提供一个可测试入口：`native_bridge/src/ck3_11906.cpp` 的 `BuildSubjectRouteTimeline` 在 `12286..12319` 仅对**非战中、非撤退**的同省 stationary hold 走特例；其他 subject 经 `12320..12420` 的原生 `get_army_move_mode`、`resolve_move_origin`、`build_army_move_route` 和 `ProjectPathTimeline` 构造路线。`ReadRouteContactHorizon` 的 `12623..12696` 随后核完整 hostile scope、双方路线、前后快照，再比较一日时间区间。这里没有显式拒绝 active-combat subject，但也没有证明构造的行军时间等于**提交撤退后**的移动速度、追击损失或完整到站安全。因此下一次实机配对须把战中查询路线/ETA、typed preview 路线、提交后的 route/速度状态与新 paused frame 对齐，不能仅凭 C++ 控制流把它标成 live-ready。

更精确的时间边界：`ProjectPathTimeline` 的 `11784..11876` 逐段以**当前 CUnit** 调用原生 `read_route_travel_duration` 取得预计抵达日；`AppendContactConflicts` 的 `12480..12535` 只在 `[date_raw, date_raw+24]` 裁剪后比较同省和反向边冲突。冻结的 `game/common/defines/00_defines.txt:629` 写 `MOVEMENT_SPEED_RETREAT = 4.5`。因此即使战中查询可用，也不能静态断言下单后 `retreating` 状态的速度与下单前预测完全相同；`one_day_contact_free=true` 更不能证明超过 `+24` 的到站窗口安全。最小 live 配对需要保存以下字节与字段：同一 CombatID/full-side day15 checkpoint、EXE/DLL SHA、seed preview 与单跳 typed preview、route-contact 的全部 `subject_route/hostile_routes/arrival_date_raws/conflicts`、order ACK、新 paused frame 的 retreat route/state，以及必要的原生速度/到站读回。ACK 或成功查询任一项都不能单独升格为撤退安全门 GREEN。

恢复 Steam 新鲜离线画面门后，沿既有 `native_bridge/research/run_active_combat_retreat_live_acceptance.py` 的独立 checkpoint/受管进程流程新增两个**不同 attempt**，不改写旧成功/失败记录：

1. **A：只读配对。** 从 day15 的 full-side active CombatID 暂停帧取 `snapshot_id/revision/native_revision/date_raw/episode_run_id/connection_generation`，查询 `battle-control-snapshot-v1` 并证实 subject、owner、scope、legality。对第一个同帧我军驻军省份执行 `preview_move_army_step(subject, seed)`；取首站后执行 `preview_move_army_step(subject, first_hop)`、`query_route_contact_horizon_step(subject, first_hop, all_current_nonretreating_hostile_ids)` 和 typed `preview_active_combat_retreat_v1(subject, first_hop, expected_revision=revision)`。每次读回都核同一六元帧、CombatID 与同一原生路线。保存原始请求/响应与 SHA；无候选、route 不匹配、scope 不完整、ETA 超 `+24`、或战中 query 返回 unavailable，均记该 fixture RED/unknown，不提交动作。
2. **B：动作配对。** 仅在 A 的只读条件全过后，从**独立 cold restore** 的同一 checkpoint 重取全部查询与一次性 token；不要复用 A 的 token。以 typed `order_step` 提交一次，ACK 仅记 pending。新 paused revision 查询受影响 CUnit 的 `retreating/target/route` 与 prior full CombatID 的 phase/winner；再取新状态下的路线/到站时间读回，比较 A 的预测与撤退后的实际速度、路线和接敌时间。若任一项不同，保存反例而不是直接放开自动策略；不能把第二个 attempt 当作与 A 同一帧的证据拼接。

这两段的调用是现有 `GameplayBridgeService.execute_step(step, expected_revision=...)` 与 typed `preview_active_combat_retreat_v1`/`order_active_combat_retreat_v1`，步名由 `war_contract` 的 `preview_move_army_step`、`query_route_contact_horizon_step` 构造；它们不是新增 CLI。真实执行前先按项目实机门禁核 Steam 离线新鲜画面并独占 CK3。本轮门禁仍 RED，所以 A/B 均未运行，不能把上述静态合同记作已验结果。
