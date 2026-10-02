# R0266：在建造与现役战争之间共用现金

R0266 的 `H2825/raw53217624` 是一个已暂停的同帧观察：`snapshot_id=native:3`、公开修订 `4`、原生修订 `3`、`episode_run_id=native-29829-2bc2d599f7f9`、玩家 `29829`、战争 `16777231`。建造候选 `farm_estates_01` 的原生价格为 `18,000,000` 个 Q100000 金币原始单位，即 180 金；玩家库存 `111,861,020`，即 1118.61020 金。现有建造政策额外要求保留 `20,000,000`，即 200 金。三者只说明**尚未计算战争负担的余额**为 `111,861,020 - 18,000,000 - 20,000,000 = 73,861,020`，即 738.61020 金；不能据此批准建造。`+70` 百分之一金币/月是建筑定义的潜在收入，尚非实际入账。

## 已有字段与缺口

| 项目 | H2825 状态 | 来源和含义 |
| --- | --- | --- |
| 现有国库 | `111,861,020`，Q100000 | R0266 同帧原生建造观察的 `candidate.gold_before_raw`，与快照的 `played_character_gold.raw` 对接时须核对一致。 |
| 活跃战争 | WarID `16777231`，现役玩家军队 1 支 | R0266 同帧建造观察及战争计划；军队数量本身不是维护费。 |
| 已提交、尚待执行的战争现金 | `null` | 缺少同帧战争待办动作账本及费用读回；`null` 不代表无待办。 |
| 本次战争动作的即时费用 | `null` | 缺少所选战争动作的原生费用或能证明免费之证据。只读查询可以是 0，但必须与同一计划动作及来源绑定。 |
| 战争政策最低现金保留 | `null` | 目前没有适用于该战争的已发布保留金政策。建造自身 200 金保留额不得冒充战争政策。 |
| 未来战争现金上界与风险预算 | `null` | 缺少带期限的费用上界来源和政策风险额；`player_monthly_gold_income` 是当前净收入观察，不能倒推出总维护费，也不能证明未来费用上界。 |

`H2908/raw53217816` 是后来的另一帧，只能作后续检查点，不能填补 H2825 的同帧现金字段。以上数据来自 [R0266 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-R0266-JOINT-CASH-20260928.json)和其[证据摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0266-JOINT-CASH-20260928.construction-frame.json)。本机在 UTC 20:38 的独立恢复 attempt `D:/ck3-research-artifacts/war31-h2743-20260928/attempt-06-r0266-cash/steam-stale-recovery-07/` 取得窗口位移的新桌面像素，人工查看到 Steam“离线模式”；任务栏时钟仍停在旧时间，任何实际启动前须重新取证。此处没有新的 CK3 实机读回。

[2026-09-28 分配器审计](../autonomous-agent-progress/daily/2026-09-28.md)确认 R0263–R0267 是未分配的历史尝试标签，不能充当 canonical 操作轮次。R0266 请求里的 `run_round` 只标识那份物理观察和交接来源；本页的 H2825 金额、日期及后续哈希边界不因此消失，但也不能据此增加正式长期游玩里程碑。新近 H3075 的同一日报记录又在另一帧观察到同一建筑价格 `18,000,000`、国库 `111,907,131`，战争共同承诺与未来费用仍为 `null`；它不能代填 H2825 同帧输入。

原版 AI 的战争储备规则提供了**后续取数路径**：当前游戏 `game/common/defines/ai/00_ai.txt:135-154` 把按 tier 的最低战争储备设为 `25/25/50/100/200/300/400` 金，并指定 `MONTHS_OF_MAINTENANCE_IN_WAR_CHEST=18`，即与 18 个月最大维护费需求比较。此前[原生宣战输入研究](war-film-declaration-inputs-2026-09-23.md)静态定位了 `war_chest_gold` 的预算字段和需求构造 helper。这说明“原版 AI 希望保留多少战争储备”有可追的原生入口；**还没有** H2825 同帧的角色 tier、最大维护费原生读数、当前 `war_chest_gold` 或与玩家建造消费共享的预算所有权读回。原版 AI 的宣战储备也不自动等于本游玩智能体在现役战争中的最低现金政策，因此当前收据继续保留 `policy_minimum_gold_reserve_raw=null`。

H2743 的另一次只读存档检查进一步提醒这个区别。已在接收机核验的原始 `xar_checkpoint.ck3` SHA-256 为 `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9`；使用 SHA-256 `E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D` 的 Rakaly 0.8.19 解码到仓库外独立目录，melted SHA-256 为 `1F12D756D3643CFE7AC7D4A13ED1F39A95EBC508633B63415D6706C1BA71F233`。文本的 `ai_strategies` 中可以看到其他角色的 `budget_war_chest` / `desired_war_chest`，全文只有两处 `29829={`，分别位于角色数据库和一条 `child_born` 记忆，没有以玩家 29829 为键的 AI strategy 行。这是 **H2743 保存层** 的负面观察，既不证明 H2825 的实际状态，也不证明内存里绝不存在其他预算表示；它足以阻止把其他 AI 角色的战争储备读数移植给玩家 Robert。解码素材永久保留在 `D:/ck3-research-artifacts/war31-h2743-20260928/attempt-06-r0266-cash/`。

继续沿 `0x184093A` 的直接调用追踪，独立的[精确版本静态校验器](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_maintenance_candidate.py)核对了 EXE RVA `0x290BA70..0x290BDAC` 的完整函数字节 SHA-256 `A6D40023A1B422DF749610533E403A8BE054A46D952D36D3785973A5485F6B2F` 和 11 个指令锚点。该函数的直接指令以 RCX 接收输出缓冲区、RDX 接收角色指针，清零 0x50 字节输出，读取角色 `+0x1B8` 扩展，经过下层调用对十个 QWORD 槽累加，并将原输出指针返回；这比“只能读 AI strategy 预算”更接近一个可用于玩家角色的**候选维护资源源头**。但 `0x290B8A0`、`0x2395370` 及间接调用的传递读写尚未闭合，也没有对玩家 Robert 的同帧值或费用语义做实机验收。校验器明确输出 `safe_to_call_from_live_bridge=false`，不能因静态 ABI 看起来合理就调用它、把 slot 0 当成金币维护费，或为 H2825 填数。普通 Python 与 `-O` 精确 EXE 校验均通过；完整反汇编保存在上述仓库外 attempt 的 `maintenance-disasm-v2.txt`。

对两个下层函数的初步只读反汇编显示，`0x290B8A0` 自己也构造十槽向量并读角色属性；`0x2395370` 在 `0x23953C1` 通过 vtable 间接调用，还在数条分支中调用其他金额／状态 helper。因而单看上层十槽累加没有足够证据证明它纯读取或各槽的最终经济语义。下层反汇编保存在同一外置 attempt 的 `helper-290b8a0-disasm.txt`、`helper-2395370-disasm.txt`；它们是候选调用图，不是可执行的桥接合同。

进一步的精确版本校验把两个下层函数的完整边界也冻结了：`0x290B8A0..0x290BA64` SHA-256 为 `DBA09E9FC922EF274A31DAA2C029053BE39E20DC127E2DF606A5B3E515069A1D`，在 `0x290BA44` 向选定输出槽累加；`0x2395370..0x2395604` SHA-256 为 `6AE006D6CA955A245D37429596864593CAC71625AC4A81728A8D46D0D45BB7B9`，在 `0x23953C1` 经虚表间接调用，还可能在 `0x23954F2/0x2395509` 递归调用自身，或走 `0xC883C0/0xC88270` 两条计算路径。校验器在普通 Python 和 `-O` 下均对精确 EXE 通过，但这些静态锚点**没有**闭合虚表目标、所有下层副作用或槽位经济含义，`safe_to_call_from_live_bridge` 仍为 `false`。精确函数反汇编另保存在同一 attempt 的 `helper-290b8a0-exact-function.txt` 和 `helper-2395370-exact-function.txt`。

## 已落入运行时的接口

`m5_war_cash_resource_v1.observe_active_war_cash_resource_v1` 产出只读 `xar.ck3.m5-active-war-cash-resource.v1` 收据。输入必须包括完整 `source_frame`（玩家、`snapshot_id`、公开/原生修订、日期、episode）和 WarID。五项金额各使用 `{raw, scale:100000, source, source_frame, war_id}`，逐项核对同帧、同一场战争：已提交战争现金、本次动作即时费用、指定期限内未来费用上界、该期限的额外风险预算、战争政策最低保留额。收据的 `amount_observations` 保留每项金额的这五个原始证据字段，消费端再次逐项核对，不能仅信任收据顶层帧或来源字符串。未来上界还要声明 `horizon_days` 和文字假设。未知输入以 `null` 和机器可读 `missing` 原因输出；显式的 0 同样需要来源。收据始终 `formal_action_ready:false`。

全项齐备时，三种现金用途分别进入**现有** M5 资源合同：

1. `existing_shared_gold_commitment_raw = pending_war_cash_raw`，计入 `existing_commitments.gold_raw` 一次；先前其他领域的承诺仍应叠加。
2. `immediate_war_action_cost_raw` 与战争提案 `gold_cost_raw` 相同，仅在选择该战争动作时由 M5 预留。
3. `joint_gold_reserve_raw = future_war_cost_upper_raw + future_risk_budget_raw + policy_minimum_gold_reserve_raw`，作为所有候选共享的 `gold_reserve_raw` 下界；即使战争动作不是本次候选，建造也不能挪用这笔保留金。

`active_defensive_war_continuation_proposal` 核对战争提案的费用与收据相同，并将收据放入提案证据。`collect_m5_formal_proposals` 在有一个现役战争时核对收据、既有承诺与共享保留额；缺失、不完整、跨帧、跨 WarID 或预算遗漏都会拒绝这次联合比较。现有 `M5FrameDispatcher` 仍负责单帧唯一分析预留。该预留只存在于这一帧的 dispatcher 实例；状态改变时需创建新实例、重新观察和预留，不能沿用旧帧。这里没有第二个建造 consumer，也没有开启 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED`。多个同时进行的战争尚无合并合同，明确拒绝，避免只为其中一场战争保留现金。

目前没有能为 H2825 填入未来费用上界、待办现金或战争最低保留额的同帧原生字段，因此 H2825 对应收据是 `incomplete`，联合建造可负担性仍是 `unassessed`。下一步需在受管实机恢复后读取战争待办费用与原生军队维护费/补员费用的同帧来源，并给出一个明确期限及风险预算；有界输入齐备后再由非战争执行者做受影响的建造候选集成及正式动作/回执验收。

## 2026-10-02 补入：PR #449 的 1.19 现金研究与历史 RED

本节补入 [PR #449](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/449) 冻结来源 `3bc267e0d3c565249f9a93ac24e33acb0a44ded7` 的 2026-09-28–30 研究。上文与原始证据保留；本节仅保存该来源的知识与结果，不把旧分支的命令账本、正式查询收据模式或 M5 合同候选写成当前运行时已接入。它们绑定 CK3 **1.19.0.6**、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，不能外推为升级后的 1.20 实机能力。完整来源响应、逐次证据和限制保存在 [R0266 响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-ROBERT-R0266-JOINT-CASH-20260928.json) 的 `historical_pr449_20260928_20260930` 补充键；原顶层状态与日期没有改写。

### 费用来源及单位

旧段把 `player_monthly_gold_income` 称为净收入；#449 的来源审查只确认当前月收入读数，未闭合其总收入、支出与净额构成。因此该读数不能倒推出军费或未来现金上界。H2825、H2908、H3911 的金额分别属于各自帧，不能跨日期或会话拼接。

原版 `MilitaryView.GetAllRaisedGoldMilitaryExpenses` 的最大月维护费是全军征召、满员条件下的 GUI 预测；原版英文提示明确说明舰队可使实际费用更高。精确 EXE 校验定位注册引用 `0x19EDE9`、回调 `0x11FCAA0` 与 getter `0x11F7D90`；最大费用 getter 返回 `MilitaryView+0x758` 的 `ValueBreakdown` 地址。当前费用 getter `0x11F7D00` 经 `0x11F7370`，并在 `0x11F7426` 写回 `MilitaryView+0xB38`。它们不是已经读出的 Q100000 金额，当前费用 getter 也不是已证明的纯读取。详见 [MilitaryView 精确静态校验](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_military_view_candidate.py)、[顶栏费用链](r0266-topbar-expense-static-2026-09-28.md)、[HUD 所有权链](r0303-war-cash-hud-owner-chain-2026-09-28.md) 和 [被动实例边界](r0303-war-cash-passive-instance-gate-2026-09-28.md)。

上船报价的静态更正是 `FleetPredictionMapIcon+0x68` 指向费用行，**费用行 `+0x78`** 才是 raw；`icon+0x70` 是 `ValueBreakdown` wrapper。旧的直接 `icon+0x78` 解释有误。图标会汇总一组预测记录，尚未建立这个缓存总额与单一 ArmyID、typed MoveArmy、起终省份、路线、付款人和当帧报价的对应关系。佣兵 `GetCostDesc` 是文本回调，也没有由此获得原生数值雇佣/续约报价。见 [embark ABI](r0266-embark-quote-abi-static-2026-09-28.md)、[selected move 对照](r0266-selected-move-embark-quote-crosswalk-2026-09-28.md) 与 [其他费用来源边界](r0266-other-war-cash-static-boundaries-2026-09-28.md)。

月费率与下一日实际扣款是两个问题。军队每 30 日 hook 不能证明金币扣款日，月费除以 30 不能直接成为下一日费用上界；舰队、补员、雇佣、续约、征召及费率变化仍需各自来源。[扣款节奏静态审计](r0266-war-cash-cadence-static-audit-2026-09-28.md) 只给出有前提的短期预算候选，没有闭合扣款次数或事件支出上界，五项正式战争现金仍为 `null`。

### 来源分支中的账本与消费候选

#449 保存了 `NativeOwnerCommandLedger` 的进程内原生命令生命周期观察：发送前登记 request、发送、响应及历史入账分别记录；发送失败、超时和重连保留未知结果，观察器自身故障不替换原生命令结果或历史持久化。该分支的 driver hooks 是归档候选，当前主线没有据本次文档补入安装这些 hooks。即使在来源分支，它也不覆盖其他进程、通道、游戏侧延期扣款或所有 typed 调用，且不为请求定价；空账本仍固定 `pending_war_cash_raw=null`、`zero_pending_war_cash_proven=false`。持久 journal 的 [owned writer 子集检查](r0266-h3937-owned-pending-source-candidate-2026-09-29.md) 同样只核已登记来源，不能从 quote 字节 SHA 推导原生费用或全部 writer 覆盖。

来源还提出了三类 M5 候选：报价必须绑定所选动作及路线；未来假设使用 `{version, assumptions, source_frame, war_id, horizon_days}`；活动战争的未来保留金与非战争候选自身支付后的 floor 分开计量。原数值例是国库 1000、建造价 800、未来军费 150、建造 floor 200：若两种用途不可重叠，`max(150,200)` 会在之后付军费时只剩 50。另有“同帧明确无选步”只能证明该计划即时动作费为 0 的诊断；其他四项金额及正式资格继续未知。以上源码与合成测试被保全，**没有本次接入这些 dormant 合同，也没有交付现金生产者**；它们不是新增部署门禁或当前玩法完成项。来源边界见 [动作绑定候选](r0266-war-cash-action-binding-followup-2026-09-28.md)、[无选步诊断](r0303-no-selected-war-action-fee-2026-09-28.md) 和 [政策来源审计](r0303-war-cash-policy-floor-static-audit-2026-09-28.md)。

### H3911 正式查询的逐次结果

来源保留了六个 H3911 源资产的精确摄入、独立 rebind/no-launch 与分开的 live attempts。更早 H3446、H3492、H3568、H3603、H3670、H3770 资产与 ACK 仍是各自历史来源；文件转移、来源配对资格、接收端无启动准备和 live 查询是不同证据，不能拼成当前帧现金。来源政策所有者明确暂缓 Robert 战争最低储备、期限、未来费用上界与风险方法，暂缓不等于零储备。

| H3911 接收 attempt | 已观察与保留的 RED |
| --- | --- |
| 01 | 正式选择并执行 `query-war-termination-options-16777231`，但收据缺少完整国库/协议详情，停于 `same_paused_treasury_unproven`；未到被动采样。见 [attempt01](r0266-h3911-formal-query-attempt01-red-2026-09-29.md)。 |
| 03 | compact readiness 错作现金 BEFORE，缺国库和顶层战争；完整 AFTER 与内层缓存前后均为 raw `120644281`。这是接收合同/投影缺项，不证明实际扣费或零费。见 [attempt03](r0266-h3911-formal-query-attempt03-cached-before-red-2026-09-29.md)。 |
| 04 | 完整缓存 BEFORE/AFTER 同值，但门要求实际 auto-turn outcome 未提供的顶层 frame 字段，停于 `actual_auto_turn_selected_typed_query_unproven`；来源随后改为核 queried 字段，旧 RED 保留。见 [attempt04](r0266-h3911-formal-query-attempt04-executed-outcome-red-2026-09-29.md)。 |
| 05 | 来源 `dcba09d4584e326d72df01db5fbe13786d27a4a8` 的正式 typed query 被 accepted/available、sequence1；六字段帧与缓存余额不变，游戏动作0。查询 postcheck 通过，现金正式资格仍 false、即时费仍 null。见 [attempt05](r0266-h3911-formal-query-attempt05-passive-red-2026-09-29.md)。 |

attempt05 的正式收据 SHA-256 为 `10F4A8B67D0635743EF2E41F82A17B063F66B32BD5B4CBED2A6B0F1F6FA73460`。同会话被动 topbar 只读两次，共读取 11,432 bytes，匹配静态 owner 路径与玩家 29829，却拒绝不对齐的 expense array 和无效 render tick/interval；未读到军费率。该诊断 SHA-256 为 `EA46AEEEC87E303B0E691C8211F3DDEE3EC9C478D05A212E03A70420DB7F48CA`，独立审计 SHA-256 为 `DB6D50752C826912D5743C5D85C98D4EAE79CE4FBCC505868F6236D63608C577`。精确记录仅是 Python 解析后的 request/envelope，不是原始 named-pipe bytes；缓存余额相等不排除临时或延期费用，两个零费 approval registry 仍为空。后续 v5 纠正 v4 的“raw protocol”字段措辞，均按原字节保留。

该来源在 2026-09-30 07:35:55 的 intake 只观察到本地固定 WAR 目录无新 SOURCE-ACK/正式回件、最新 a13 仍为 prelaunch watchdog RED；本地 inventory 不是来源侧 ACK。历史结论持续是 **五项正式金额、期限和假设未知，M5 spend false**。本次补知识没有读取游戏、调用 GUI getter、计量新费用或启动后续安全/协议工作。
