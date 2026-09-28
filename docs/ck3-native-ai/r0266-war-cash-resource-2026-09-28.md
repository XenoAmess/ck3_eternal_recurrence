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

### 原版军事窗口的维护费来源候选（2026-09-28 只读静态结果）

另一个更直接的取数入口来自原版 `game/gui/window_military.gui:643,1037`：`MilitaryView.GetAllRaisedGoldMilitaryExpenses` 是“每月最大维护费”栏的 `ValueBreakdown`，与当前军费栏 `GetGoldMilitaryExpenses` 分开。原版英文 `game/localization/english/gui/militaryview_l_english.yml:47` 将最大值解释为**全军征召且满员时的预测军事费用**，并明确警告舰队上的军队可让实际维护费更高。因此它并非当前已花费金币，也不是无条件的未来费用上界；尤其不能替代补员、雇佣、运输或临时动作的单独预算。

只读探针 [`war_cash_military_view_probe.py`](../../ck3_autonomous_player/native_bridge/research/war_cash_military_view_probe.py) 在 SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的原版 EXE 中定位了注册字符串；[`verify_war_cash_military_view_candidate.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_military_view_candidate.py) 进一步核对 RVA `0x19EDE9` 的注册引用、`0x11FCAA0` 回调与 `0x11F7D90` getter。最大费用 getter 只返回 `MilitaryView+0x758` 的 `ValueBreakdown` 字段地址；这不是可直接填入 Q100000 收据的金额。当前费用 getter `0x11F7D00` 进入共享 helper `0x11F7370`，后者在 `0x11F7426` 写回 `MilitaryView+0xB38`；不能把当前费用查询也视为已证明的纯读取。校验同时核对原版 GUI 与英文语义文本，普通 Python 和 `-O` 均 GREEN。其输出明确标为 `same_frame_player_amount_observed=false`、`complete_future_war_cost_upper_bound=false`、`safe_to_call_from_live_bridge=false`；没有调用游戏函数或写入任何 H2825 数值。

对玩家绑定继续静态追踪：当前费用 helper 从 `MilitaryView+0x248` 读取 subject handle，经原版句柄表解析后才调用 `0x290A720` 构造当前费用 `ValueBreakdown`。原版 `0x11F36F6..0x11F3708` 仅在这个字段为 `-1` 时，从已知的玩家 CharacterID 全局槽 RVA `0x4FE7EE0` 自动填入；若窗口已选别的角色，该字段可不被覆盖。所以后续必须**实际比较字段中的完整角色 ID、全局玩家 ID、同帧快照玩家 ID并核对句柄解析**，不能因自动填入分支便假定任意 MilitaryView 都属于 Robert。也尚未证明无窗口的 headless 状态有可读 `MilitaryView` 实例。原生 `ReadCharacterExitResources` 已有通过 `ResolveTermsCharacter` 核对角色身份、并从角色扩展读取 Q100000 国库的模式；它可复用作玩家身份与国库交叉核对，但不包含军事维护费、战争待办动作或未来开销。`M5FrameDispatcher` 的预留在新实例中起始为空，只描述该实例的分析预留；因此也不能用它推断游戏或其他策略的待办战争现金为零。

后续要在**新的同一暂停帧**先证明 MilitaryView 属于玩家 Robert，读回 `ValueBreakdown` 的真实定点数值与单位，并与可见窗口值交叉核对；再确认窗口缓存更新时机。若用它构造有限期维护费预算，必须同时冻结兵团/雇佣与舰队状态、期限、可能改变维护倍率的条件，并把舰队及其他未覆盖战争开支列入单独有来源的风险额。待办战争动作账本、所选动作的即时费用和战争政策最低保留额仍需分别提供来源。只有这些输入共同闭合，才能将未来上界、风险额与政策保留额写入同帧收据。R0266 H2825 历史帧没有这些读数，仍保持 `null`。

## 已落入运行时的接口

`m5_war_cash_resource_v1.observe_active_war_cash_resource_v1` 产出只读 `xar.ck3.m5-active-war-cash-resource.v1` 收据。输入必须包括完整 `source_frame`（玩家、`snapshot_id`、公开/原生修订、日期、episode）和 WarID。五项金额各使用 `{raw, scale:100000, source, source_frame, war_id}`，逐项核对同帧、同一场战争：已提交战争现金、本次动作即时费用、指定期限内未来费用上界、该期限的额外风险预算、战争政策最低保留额。收据的 `amount_observations` 保留每项金额的这五个原始证据字段，消费端再次逐项核对，不能仅信任收据顶层帧或来源字符串。未来上界还要声明 `horizon_days` 和文字假设。未知输入以 `null` 和机器可读 `missing` 原因输出；显式的 0 同样需要来源。收据始终 `formal_action_ready:false`。

全项齐备时，三种现金用途分别进入**现有** M5 资源合同：

1. `existing_shared_gold_commitment_raw = pending_war_cash_raw`，计入 `existing_commitments.gold_raw` 一次；先前其他领域的承诺仍应叠加。
2. `immediate_war_action_cost_raw` 与战争提案 `gold_cost_raw` 相同，仅在选择该战争动作时由 M5 预留。
3. `joint_gold_reserve_raw = future_war_cost_upper_raw + future_risk_budget_raw + policy_minimum_gold_reserve_raw`，作为所有候选共享的 `gold_reserve_raw` 下界；即使战争动作不是本次候选，建造也不能挪用这笔保留金。

`active_defensive_war_continuation_proposal` 核对战争提案的费用与收据相同，并将收据放入提案证据。`collect_m5_formal_proposals` 在有一个现役战争时核对收据、既有承诺与共享保留额；缺失、不完整、跨帧、跨 WarID 或预算遗漏都会拒绝这次联合比较。现有 `M5FrameDispatcher` 仍负责单帧唯一分析预留。该预留只存在于这一帧的 dispatcher 实例；状态改变时需创建新实例、重新观察和预留，不能沿用旧帧。这里没有第二个建造 consumer，也没有开启 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED`。多个同时进行的战争尚无合并合同，明确拒绝，避免只为其中一场战争保留现金。

目前没有能为 H2825 填入未来费用上界、待办现金或战争最低保留额的同帧原生字段，因此 H2825 对应收据是 `incomplete`，联合建造可负担性仍是 `unassessed`。下一步需在受管实机恢复后读取战争待办费用与原生军队维护费/补员费用的同帧来源，并给出一个明确期限及风险预算；有界输入齐备后再由非战争执行者做受影响的建造候选集成及正式动作/回执验收。
