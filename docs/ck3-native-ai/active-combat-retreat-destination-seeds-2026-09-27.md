# 游玩智能体战中撤退：目的地种子与单跳门

日期：2026-09-27。对象为**我方自有策略**的目的地输入，不是原版 AI 的候选枚举、目的地评分或胜率阈值。普通战争原版 AI 的这三项仍为 unknown；引擎可执行边界见 [主动撤退总专题](active-combat-retreat.md)，策略总缺口见 [队列生产端审计](ordinary-war-active-retreat-queue-audit-2026-09-27.md)。本轮没有启动 CK3；Steam 当前可读离线画面门仍为 RED。

## 已落地的最小候选来源

`native_driver._action_steps` 原先给战中 CUnit 的移动预览目标主要是敌军当前省、我军已有移动目标、敌方默认集结省、战争目标省。这些是接敌/战役目标，不是可靠的撤退目的地。现在对**paused、可控且仍在 active combat** 的 CUnit，额外发布指向当前快照里其他驻扎的**玩家可控军队**所在地的只读 `preview-move-army-<CUnit>-to-<Province>`。驻军必须为 `regular`/`sieging`，不能正处战斗或撤退；目标不能等于本场省，也不能是已观测敌军当前省、移动目标或路由上的省。此步只产生目的地种子，不能证明可达、安全或适合撤退；没有对应我军时可以合法返回空集。盟军省份暂不作为通用种子，因为此投影尚无战中 CombatID 到具体 WarID 的绑定，不能把另一场战争的盟军混入。

已有 `_fresh_preview_first_hop_steps` 会从**同一 paused snapshot ID、public/native revision、日期、episode 和连接世代**的成功原生 `PreviewMoveArmy` 路线提取第一站，发布第一站的 exact preview 和完整敌军 scope 的 route-contact 查询。对 active-combat CUnit，本轮禁止它顺带发布第一站的直接 `move-army` 字面命令：必须走 `preview-active-combat-retreat-v1` 的 native legality、scope、exact route 与一次性 token，再用 `order-active-combat-retreat-v1` 提交。非战中 first-hop 行为保持原样。

## 策略接入的可核验合同

目的地选择可以沿下列顺序消费上述能力；任何前置证据缺失时保持暂停并返回结构化 unknown，而非猜一个省：

1. 战中当前帧确认 `WarID/CombatID/CUnit/owner`、`side_scope=full_side`、`legal_now=true`。`owner_subset` 尚缺完整 live 后置验收，不能自动进入首批动作。
2. 为每个我军驻地种子取同帧 exact `PreviewMoveArmy`。若原生路线超过一站，只把其**第一站**作为新候选，再针对第一站重新取 exact 原生预览；候选路线去掉可选 origin 前缀后必须恰为 `[target]`。初始长路线不能冒充单跳撤退路线。
3. 在同一暂停帧绑定完整、唯一的非撤退敌军 ID 范围及其路线/时间信息。先排除目的地/单跳路线上已观测的敌军当前、目标或路径冲突，再对该第一站做 `query-route-contact-horizon-v1`；要求查询的 snapshot ID、public/native revision、日期、episode、连接世代、subject、target、完整敌军 ID 和原生路线均与选定帧一致，`one_day_contact_free=true`。这只证明**一日窗口**；若第一站预计抵达时间超过该窗口，或 native query 在战中 CUnit 上不能给有效 subject route，必须标 unknown，不能把一日无冲突外推到整个撤退行程。
4. 安全候选按确定性规则排序（例如本回合显式的战役价值、可观测 ETA，再以 ProvinceID 打破完全同分）；原版 AI 的 destination score/tie-break 仍保持 unknown。选择结果必须写入回执，不能仅保存一个隐式 ID。
5. 对最终目标调用 typed `preview-active-combat-retreat-v1`，只消费其中的 `target_preview.order_step`。提交前 bridge 会重新读取 battle-control、重新预览路线、核对 revision/CombatID/side/scope/affected 与一次性 token；任何变化直接拒绝并重观测。
6. `order` 的 `accepted_verification_pending` 只是提交回执。新 paused revision 对 affected CUnit 的 `retreating`、target、route 逐一读回，并按旧完整 CombatID 查询 full-side winner/phase；mixed-owner 要另核对 unaffected entries、backlinks 和同步 pursuit。不能用 ACK、单一 `route` 字段或一天后的自动败退代替完整后置条件。

当前代码只实现**目的地种子和第一站防绕过**；第 3 项中的战中 route-contact 原生查询与到站时间边界尚无生产 live 配对，策略也尚未将这些步骤连成自动撤退选择。它们是启动前必须验证的能力条件，不应作为“尚未研究原版 AI”而搁置全部我方策略，但也不能将静态可构造的命令写成已经自动安全撤退。对应聚焦检查为 `test_active_combat_retreat_destination_seeds.py`、`test_native_first_hop_projection.py` 与既有 `test_active_combat_retreat_v1_bridge.py`，共 30 项 no-launch PASS；没有新增实机 GREEN。
