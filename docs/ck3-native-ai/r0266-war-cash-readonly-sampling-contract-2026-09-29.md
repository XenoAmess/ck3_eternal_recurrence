# R0266 战争现金：顶栏自然刷新与五项输入的最小取证合同

状态：**静态路径已核，Robert 的五项现金实值与 horizon 仍未知。**本页只读原版 CK3 1.19.0.6 `ck3.exe`（SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）、原版 GUI 和已提交的 R0266 合同；没有读取进行中的 attempt、游戏进程或屏幕。对应 #449 顶栏诊断基线为 `dc436f03b`。

## 费用缓存何时可能自然重算

精确 EXE 的 `ResetLastUpdateFrame` 名称 RVA `0x40E5F28` 经注册 `0xB1063`、回调 `0xD49B20` 到 `0xD462B0`；后者把顶栏 `this+0xF88` 的 qword 上次更新 tick 写成 `0`。原版 `game/gui/hud.gui:6109-6131`（SHA-256 `1AE3F1371E0A9C43D0B62FC1C1F3A0CDBB0EAB9CF08B85545556CBF3D7386312`）把金币 widget 的 `_mouse_enter` 绑定该 reset，并把 tooltip 费用区绑定 `GetGoldExpensesBreakdown`。独立静态校验器 [`verify_war_cash_topbar_mouse_enter_refresh_edge.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_topbar_mouse_enter_refresh_edge.py) 以 EXE/GUI 双 SHA、精确指令/RVA 和 GUI 绑定拒绝版本漂移；普通及 `-O` 对原版 EXE/GUI 均通过。

费用 getter `0xD47680` 读 GUI 渲染上下文全局 RVA `0x576CC68` 所指对象 `+0x180` 的 qword tick，读 RVA `0x570D8D0` 的 signed dword 刷新间隔，比较 `tick - this+0xF88`。若不低于间隔，它在 `0xD476B1` **先**写新 tick，才在 `0xD476B8` 调用 `0xD476D0` 重算。故鼠标进入后、当前 tick 达到正间隔时，下一次实际执行 getter 应进入重算分支；但 `+0xF88=当前 tick` 可以出现在重算完成前。`tick` 相等、两次 RPM 相同、甚至稳定的行数组，都不能单独证明完成或属于同一个游戏 native revision。严禁 headless reader 直接调用 reset/getter；它们写 GUI 状态。GUI owner 可以在独占屏幕与新鲜 Steam 离线证据下自然悬停，读取器仍只用 `ReadProcessMemory`。

独立复核以另一限界反汇编器重读上述 RVA，普通与 `-O` 校验均返回 `formal_cash_eligible=false`；把非 EXE 文件作为输入会在 EXE SHA 门退出 1，把原版 GUI 拷贝末尾附加无关注释会在 GUI SHA 门退出 1。此项负例只验证版本身份失败关闭，未观察游戏或任何费用刷新完成。

要把顶栏行从**诊断候选**升级为当前军费率，至少要有独立的、绑定该具体实例与这次鼠标进入的 tooltip/render **完成后**回执；证明 reset 后执行了对应 getter 且重算返回，不能用 tick 代替。还要在前后各取一次正式 paused native snapshot，精确绑定 PID+creation、EXE/DLL、唯一 live 顶栏 owner 链、玩家完整 CharacterID、WarID、episode、snapshot/public/native revision、date 和 treasury；任何变化即撤销。被动读取全部根行、嵌套行、名称字节、`+0xB50` signed raw/`+0xB58` scale 与各行 `+0x78/+0x80`，scale 必须精确 `100000`。将军费行树与同帧 `MilitaryView.GetGoldMilitaryExpenses` 原生总额和可见 tooltip 交叉核对；六个军费标签可能嵌套或重复，不能逐名盲加。刷新函数的 played ID 比较及 fallback 分支亦须排除错误玩家。若无法取得完成后回执，**当前军费率仍是 null**；当前 `war_cash_topbar_bounded_sample.py` 的输出固定 `formal_cash_eligible=false` 是正确边界。

## 五项战争现金的来源门

| R0266 输入 | 最小真实来源及同帧核验 | 顶栏能否单独给出 |
| --- | --- | --- |
| `pending_war_cash_raw` | 完整 owner 写入者范围、跨重连保留的未结交易、每条 typed action 报价、提交/结算回执；空账本也须证明没有其他写入者。现有 `war_cash_pending_ledger_v1.py` 只报记录中未结报价和 unknown。 | 不能；月费缓存不是未结现金账本。 |
| `immediate_war_action_cost_raw` | 正式计划**选中的同一 typed step**、WarID、路线/海路/佣兵等参数、原生无损 Q100000 报价或该精确只读查询的无提交+国库同帧前后零费回执。查询零费不能转用到移动、上船、雇佣或终战。 | 不能；总月支出不含动作报价。 |
| `future_war_cost_upper_raw` | 明确 horizon 终点与下一强制重审点；原生/实机证明金币维护费扣款节奏和一次扣款上界，再覆盖期限内军队征召/补员/上船舰队、佣兵到期/续约、计划动作与自动事件。每个费用需有独立 Q100000 上界和 claim ID。 | 不能；当前月费率或“全征召满员”预测率不是期限内现金上界，舰队还可能更高。不得除以 30。 |
| `future_risk_budget_raw` | 战争政策明确未被已报价未来费用覆盖的风险事件、金额、失效日期和独立 claim ID；与未来费用及最低保留项不重复。未知而无有界政策时保持 null。 | 不能；缓存不记录事件风险。 |
| `policy_minimum_gold_reserve_raw` | 玩家战争政策的版本化、审阅并独立 pin 的文档，绑定玩家/episode/WarID、有效起止 date 与 horizon、Q100000 floor、用途和与未来/风险互斥的 claim ID；可用 `war_cash_floor_policy_provenance_v1.py` 做候选核验，正式性另证。 | 不能；原版 AI war chest 与建造域 200 金都不是 Robert 玩家政策。 |

所有实值应进入 `m5_war_cash_resource_v1.py` 的同帧收据；其 `source` 非空字符串只是形状门，**不**能替代上表的原始回执与来源审查。即使选中 termination query 的即时费用有条件证明为 0，其余四项和 horizon 仍未知，不能打开联合建造预算。

## 最小可执行观察顺序与失败关闭

1. 在新的、精确匹配的 source pair 和官方 no-launch 校验后，由屏幕 owner 获取当次 Steam 离线画面、独占屏幕及受管暂停帧。被动进程采样只开查询/读权限；先校 EXE/DLL/PID+creation、owner 链和正式 native frame。旧 H3911/R0326 或进行中 attempt 的字节不能代替本次帧。
2. 若要研究顶栏月费，屏幕 owner 自然悬停金币栏，保全 reset/tooltip 完成证据；读取器在前后原生帧之间被动双读 GUI 根、行、渲染上下文与 interval。若 tick 为 0、倒退、结构/scale/玩家/WarID/修订/费用总额不符，或无法证明重算返回，输出诊断 RED，不填战争现金。
3. 同帧读取军队、舰队、补员、佣兵和完整费用行树，另以正式选中 step 的原生报价/零费合同和持久待办账本取即时及待办值。不可从历史无命令、旧 tooltip 或 renderer tick 推 0。
4. 期限建议先限定到下一游戏日首个暂停帧并强制重审，但**一天 horizon 本身不是上界证明**。未找到维护费真实结算时点、舰队/补员/自动事件的完整上界前，`future_war_cost_upper_raw` 和 `future_risk_budget_raw` 继续 null；月费率即使刷新完成也不能乘以天数或除以 30。若任何新动作、人数、路线、日期、玩家、战局、政策或来源收据改变，先撤销旧预算再观察。

本合同只给下一轮受管取证的通过条件。静态 `ResetLastUpdateFrame` 路径证明自然 GUI 重算**可被触发**，没有提供 Robert 当下支出、真实扣款节奏或任何正式金额。

## 下一轮最小只读查询的字段与付款分区

这里的“查询”是待实现的受管观察合同，不是当前 DLL 已实现的命令。每个结果都需要前后正式暂停帧、PID+creation、EXE/DLL/source pair、玩家完整 ID、WarID、episode、date、snapshot/public/native revision，以及原始 Q100000 数值的来源 bytes/hash。若任何字段缺失或前后变化，只输出 `null` 和机器可读 `missing`；不得借旧帧补值。`date_raw` 在现有政策门按每游戏日 24 单位换算，政策 `valid_until_date_raw` 必须覆盖 `frame.date_raw + horizon_days * 24`；未来扣费本身仍需独立证明。

| 欲生产的金额 | 最小新增只读结果 | 分类和时间门 |
| --- | --- | --- |
| `pending_war_cash_raw` | 完整 owner 写入者登记和跨重连 journal：每个 `request_id` 的 typed action、WarID、source frame、原生报价、是否已提交、原生应用状态、独立结算/未应用回执；另证明游戏侧延期扣款及其他 writer 是否在覆盖范围内。现有 `war_cash_pending_ledger_v1.py` 只有“已记录未结报价之和”的下界，不能报告全集。 | 仅未结且**已经提交或被正式保留**的 claim 入 pending；同一 claim 不再计入当次 action 或未来 due event。无记录、空 history、ACK、驱动重连均不能证明零。无法枚举所有 writer 时保留 null。 |
| `immediate_war_action_cost_raw` | 冻结正式 `selected_step`、完整 typed 参数和原生预览的 army/origin/target/整条 ProvinceID 路线；若涉及上船，另读取唯一 GUI owner 图标对应的 CUnitID 集、缓存完成证据、原生费用行 `+0x78` Q100000 和实际首次扣款边界。`move-army` 预览目前没有价格或海路标记；上船图标金额只有预测身份。 | 仅**提交选中动作到下一强制重审前必发生**的首次扣款可入 immediate。若路程后段才上船，把已证报价放入未来 due event；时点不明则即时与未来均不能填零。`selected_step:null` 只有精确同帧正式计划可给本项 0；纯读 selected query 的零证明不能迁移到 move/hire/surrender。 |
| `future_war_cost_upper_raw` | 每类未来现金流的原生 due event `{cash_claim_id, kind, first_due_date_raw, latest_due_date_raw, maximum_single_debit_raw, maximum_count_through_horizon, source_frame, evidence_sha256}`，至少覆盖征召兵、MAA 补员、舰队/上船后维护、已雇佣合同到期/续约、已排定的战争动作及自动现金事件；同时有相同暂停帧的兵团/舰队/补员/佣兵 roster 和状态。实际军费结算函数或一次精确扣款窗口的前后收据须证明次数与 Q100000 金额上界。 | 只汇总 deadline 内**不属于 pending/immediate** 的独立 claim。`MilitaryView.GetGoldMilitaryExpenses` 与 `GetAllRaisedGoldMilitaryExpenses` 是月费率/预测，原版 GUI 明说舰队可高于后者；`on_army_monthly` 是军队事件 hook，非金币扣款日。未证明扣款 cadence、次数上限或任何自动费用类时，future upper 保持 null；禁止月费/30。 |
| `future_risk_budget_raw` | 由另行审阅并固定 hash 的玩家战争政策给出风险覆盖集合、每类有界金额、claim ID、有效截止日和强制重审点；它补偿已经明确列出的未能精确报价风险，不可由费用缓存自证。 | 与未来 due event 和最低储备的 claim ID 两两不交。开放式或无法给上界的风险类不能靠任意有限金额掩盖，应使期限内消费决策失败关闭。 |
| `policy_minimum_gold_reserve_raw` | 独立发布/pin 的玩家战争政策 bytes，`war_cash_floor_policy_provenance_v1.py` 已提供候选形状门：政策版本、玩家、episode、WarID、Q100000 floor、`terminal_liquidity_after_horizon` 用途、有效起止及不交叠 claim ID。 | 这是**付款后仍须留在国库**的政策底线，不能用原版 AI 的 `MIN_WAR_CHEST`/18 个月目标或建造域 200 金静默代入；候选 helper 固定 `formal_cash_receipt_eligible=false`，直到审阅来源和其余费用真实来源闭合。 |

`next_review_date_raw` 应由受管推进器给出一个实际可执行的首个暂停重审点；`horizon_end_date_raw` 不得晚于它，且政策有效期须覆盖终点。在下一次花费授权前强制重新读完整输入。只声明 `horizon_days=1`、读取到当天月费或读到稳定 GUI tick，均不证明这一天的扣款次数或未来上界。若当前步只做纯读查询，查询零费只处理当次动作，未来战费和旧待付账仍在原分区。

## 需要先跑成 RED 的负例

1. **同 WarID、异路线上船。**保持 ArmyID/目标/国库不变，只改预览中间 ProvinceID 或 CUnit 集；旧图标金额应失效。另造“首段陆路、后段上船”与“首段上船”两条路，不能将两者都当首跳即时费。
2. **图标构造零值。**费用行初始化为 0，但尚无图标自然刷新完成、唯一 owner 和 CUnit 对应；不得输出免费。`GetEmbarkCost` callback 只复制缓存，不重新计价。
3. **空账本与迟到 ACK。**当前 driver journal 空、历史命令空，但存在重连前请求或未知结果；`pending_war_cash_raw` 必须 null。提交 ACK 后尚未有独立已扣/未应用回执，仍不得核销。
4. **跨结算日的一日窗口。**当前与预测月费率相同，窗口内出现一次真实月费扣款或舰队倍率变化；按 rate/30 的候选必须拒绝。没有原生“最多一次”证据时，保留整月 rate 也不能升级为正式 upper。
5. **佣兵与自动事件。**合同将在 horizon 内到期，或脚本可能触发战争现金事件，但 roster/due event 查询遗漏该类；即使没有主动续约命令，future upper 仍 null。
6. **自证政策。**把刚读到的 policy bytes 自己哈希作 pin、把 AI war chest 当玩家 floor、政策今晚到期却宣称覆盖明日、或 future/risk/floor 共用一个 claim ID；政策门必须拒绝，不能用 `source` 非空字符串绕过。
7. **同一费用跨分区。**一笔上船报价既在 owner pending、又进当次 immediate 或 future；合计会双计，claim ID 去重门必须拒绝而非静默相加。

上述负例建议用离线合成帧与已钉住的原生静态来源测试，不能把合成正例写成 Robert 实机 GREEN。当前 #449 的五项现金实值和期限保持 `null`；待新受管 attempt 完整回执冻结后，再决定哪些只读观察可提升为正式生产者。
