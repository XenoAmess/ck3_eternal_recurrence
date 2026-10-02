# R0266：战争动作报价、待办现金与保留额的最小接线

此页补充[月费节奏静态审计](r0266-war-cash-cadence-static-audit-2026-09-28.md)。范围是 CK3 1.19.0.6 的**静态来源和现有 owner 协议**；未启动游戏，未得到 Robert 的新金额。本页的候选政策不填历史 H2825 收据。

## 即时费用必须绑定被选择的动作

`active_defensive_war_continuation_proposal` 现在要求 `plan.selected_step`、计划中的 typed `priced_command` 与观测中的 `immediate_action_quote` 在同帧、WarID、命令参数和金额上逐项匹配；同价的另一条 step 会被拒绝。收据中的每项金额仍只核 `{raw, scale, source, source_frame, war_id}`；`source` 可以是任意非空字符串（`m5_war_cash_resource_v1.py`）。此结构门**不证明**报价来自安全原生读口、新鲜缓存或游戏实际扣款，当前正式读数仍不存在。未来生产者须提供并核对结构化 `priced_action`：

```text
{selected_step, parsed_command_kind, typed_arguments, army_id?,
 origin_province_id?, target_province_id?, route_preview_query_sequence?,
 route_province_ids_sha256?, native_quote_identity?, source_frame, war_id}
```

生产者与 `plan.selected_step` 必须逐项相等；`move-army` 还要同一暂停帧的原点、目标和路线；动作或路线变更立即作废报价。若报价原生接口只能返回格式化文本，须另取无损 Q100000 原始值及比例。提交后的 `war_action` ACK 不能倒填提交前的报价。

当前 `PreviewMoveArmy` 只返回路线省份和状态，`SubmitMoveArmy` 只检合法性并提交命令（`native_bridge/src/ck3_11906.cpp:11359-11431,11434-11649`）。Python owner 只复核同帧路线/日期及移动后目标状态（`bridge/native_driver.py:10006-10129,10131-10233`）。这些回执没有上船标志、原生费用、月费变化或国库前后值。原版另有上船即时费与舰队维护费（`game/common/defines/00_defines.txt:695-699`）；因此“移动 preview 可用”或“move ACK 成功”都**不能**证明即时费用为零。最小扩展是同帧路线 sea/embark 分类、原生上船 Q100000 报价、并在实际提交后核国库和军费；若限定纯陆地，也要有路线逐段为陆地及该命令无其他即时费用的原生证据。只读 native query 如有纯读实现证明和同帧国库前后不变的回读，可为**该次实际选中的查询 step**提出 0 费用证据。终战动作涉及 CB 特定代价，不能沿用移动或查询的零费证明。

精确 EXE 的只读[上船 getter 名称探针](../../ck3_autonomous_player/native_bridge/research/war_cash_embark_cost_candidate.py)在 RVA `0x4101938` 找到唯一 `GetEmbarkCost` 字符串，并验证其 RIP 相对引用指令 RVA `0xE1659`；普通与 `-O` 均通过。该引用位于 GUI 名称构造路径，**还没有**定位 callback、参数、原生数值单位、海路费用关联或纯读性。探针固定输出 `safe_to_call_from_live_bridge=false`、`same_frame_amount_observed=false`；不能把它当报价接口或 R0266 实测。

## 待办现金须有完整所有权

owner 的 `_record_command` 保存的是历史命令、成功与结果，`_driver_state_payload_locked` 保存 checkpoint、命令历史等（`bridge/native_driver.py:7029-7086,7374-7417`）；这不是带金额与结算状态的**待办支出账本**。它不能覆盖未经过该 driver 的游戏行为，也没有在每条历史命令上给出尚待付款的 Q100000 金额。当前 M5 collector 只要求外部 `existing_commitments.gold_raw` 不小于战争收据的 `pending_war_cash_raw`（`m5_formal_proposal_collector.py:140-180`），不能从 collector 空预留或历史尾部没有支出命令推断待办战争现金为 0。

可实现的最小账本行是 `{transaction_id, episode_run_id, war_id, priced_action, amount_raw, scale:100000, submitted_frame, settlement_state, settled_frame?}`。只对本回合唯一 owner 所有、且确认没有未纳管写入者的动作集合求和；恢复 checkpoint、会话更替和跨进程历史必须保留未结项或显式拒绝。`pending_war_cash_raw=0` 仅在同帧完成**全部写入者和全部未结交易**的扫描、无未知交易后成立。账本金额与本次新动作即时金额分开，M5 只叠加一次。

独立候选实现 [`war_cash_pending_ledger_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/war_cash_pending_ledger_v1.py) 把这条边界编码成按 `episode_run_id + WarID` 分文件的 append-only SHA-256 链。`scope_open` 绑定 owner/checkpoint；`reserve` 必须在提交动作前保存同帧 `source_frame`、精确 Q100000 报价、`selected_step`、原生命令种类、typed arguments、路线哈希及报价证据哈希；`ack` 只登记“已提交、待验证”；`resolve` 要求另给与动作身份、玩家、战局、后验帧和实收金额相符的独立回执。每次写入都锁文件、重读链并检查预期前一哈希，拒绝并发写入导致的旧状态追加。截断、篡改、跨 episode、重复 request、不同动作和回档到报价前日期都会拒绝或返回 unknown；未结项可由新进程从 `state_dir/native-session/war-cash/` 读回。

该实现故意只给 `recorded_unresolved_quote_sum_raw`（**记录中未结报价之和**），始终输出 `pending_war_cash_raw=null`、`formal_cash_receipt_eligible=false`。报价不等于已实际扣款，也没有证据证明此 driver 覆盖全部游戏内写入者；即使账本为空也不能推导正式 0。`price_evidence_sha256` 和 `independent_receipt.source_sha256` 只是外部证据引用，账本本身不验证那些文件或原生 getter 的真实性。它目前是可复用的持久化门和审计夹具，**未接入正式 owner 提交路径，也不能据此将 H2825/R0266 的五项实际输入填值**。接入时仍需原生无损报价生产者、动作提交前 reserve、后验核销来源及全部写入者范围证明；如果任何一项缺失，正式资源收据保持 `incomplete`。

## 一日未来费用、风险与政策最低保留

原版 `MilitaryView.GetAllRaisedGoldMilitaryExpenses` 是“全军征召且满员”的预测**月费率**，其英文 tooltip 警告舰队可能更高（`game/localization/english/gui/militaryview_l_english.yml:47`）。如果以后实机确认该 rate 的玩家身份、Q100000 缓存、新鲜度和组成，并核对实际扣款节奏，战争侧可以提出 `horizon_days=1`、截止**下一个游戏日首次暂停帧**的政策：在本日保留至少整整一次 `max(当前军费率, 预测全征召满员军费率)`，再加已报价的上船/到期续约等期限内费用；一天推进后重读所有值，第二天前没有新收据就停止消费。该式仍需单独覆盖舰队、补员状态变化、额外军队、自动事件和终战支出；缺任何必需项时 `future_war_cost_upper_raw=null`，不能把月费率除以 30。

`future_risk_budget_raw` 应是**版本化战争政策**对未能精确预测的期限内损失设置的独立现金缓冲，其金额和覆盖集合须明示，不得把未知费用写成零。`policy_minimum_gold_reserve_raw` 也应由战争侧发布显式玩家政策，例如“完成这一天后仍保留一整月可核军费”的恢复能力下限；它与本日未来支出是两个不同桶，不得把建造域的 200 金保留额移作战争政策。原版 AI 的 `MIN_WAR_CHEST={25,25,50,100,200,300,400}` 与 `MONTHS_OF_MAINTENANCE_IN_WAR_CHEST=18`（`game/common/defines/ai/00_ai.txt:135-154`）只说明 AI 的**期望**储备，不是玩家 Robert 已有的政策或现金承诺。H2743 保存层也未找到以玩家 29829 为键的 AI strategy 行，见[现有来源说明](r0266-war-cash-resource-2026-09-28.md)。

同帧 `source_frame`、WarID、玩家、选中 step/路线/报价、军队与佣兵清单、补员/上船状态、月费与国库、政策版本、风险覆盖或账本任一变化，均应在下一笔支出前重算；无论是否变化，每推进**一个游戏日**都必须在下一暂停帧重审。月费实际扣款日期、单日可能的自动费用及完整动态上界仍未由静态来源证明：没有这些证据时，H2825 历史帧的五个现金输入仍为 `null`，新帧中未证明的分项继续为 `null`，`cash_inputs_status` 为 `incomplete`；不能把此政策候选写成实测金额。
