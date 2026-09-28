# R0266 / M5：五类现金输入的最小生产者和失效门禁

状态：**静态设计候选；没有 Robert 的新增现金实值。**基线为 R0266 工作树 `0489f49d6191d77b2afb46cdc71fc2a99217df95`、原版 CK3 1.19.0.6。H3446 官方 rebound 六资产、H3492 官方 rebound 六资产及其历史 M6 二进制均已有精确传输验收，但没有受管同帧现金读回。来源 09:39Z 提供 R0298 正式 H3603/raw53219352 冻结配对，接收端七件传输 7/7 SHA 验收；R0299 H3670 随后完成但未传大件，R0300 又给出更晚 H3674/raw53219496。H3674 只有原始 save/driver 身份，未做官方 rebound/no-launch，也无停帧窗口。H3603/H3568/H3492 均只作历史诊断。五金额仍是 `null`。本文不填零，不批准建设或战争费用。

| 输入 | 最小生产者 | 同帧证据和失效条件 |
| --- | --- | --- |
| **待提交战争现金** `pending_war_cash_raw` | 唯一 native owner 的完整未结交易账本：请求 ID、实际选中动作、原生报价 Q100000、提交与结算状态；外部游戏自动扣费还需独立读回。现有 `NativeOwnerCommandLedger` 仅跟踪 request 生命周期，金额仍 `null`。 | 每行绑定 player、WarID、episode、checkpoint、native/public revision、日期；启动/恢复后未结项不能丢。空历史、空本进程账本或 ACK 都不能证明 0。存在未知写入者、超时、重连、未核结算即失效。 |
| **本次战争动作即时费用** `immediate_war_action_cost_raw` | 先冻结 `selected_step` 及 typed args。纯读 query 可由精确原生命令副作用审计加同帧国库不变证明零；移动若可能上船，需原生 `FleetPredictionMapIcon.GetEmbarkCost` Q100000 报价，绑定 army、原点、目标、全路线及 preview 序号。GUI 图标 `+0x68` 指向费用行，静态候选 raw 位于该行 `+0x78`；图标自身 `+0x78` 不是金额，也没有已核 live 报价。 | 报价对象与计划必须逐项相等；任何改选、改路、刷新图标、日期/修订变化立刻重取。`GetEmbarkCost` 下层纯读性及缓存刷新尚未证明，不能主动调用或从格式化 `V0` 文字反推 raw。纯读 query 的零证明不能复用到移动、投降或雇佣。 |
| **战争政策最低保留** `policy_minimum_gold_reserve_raw` | 战争侧版本化、明确作用范围的玩家政策输入；原版 AI `MIN_WAR_CHEST` 和 18 个月维护费目标只能作设计参考，不能冒充玩家政策。 | 政策版本、玩家、WarID、财政口径、期限和独立于未来支付的恢复能力目标须和本帧绑定。政策不明确时保持 `null`；不能把 M5 建设域的 200 金最低额直接当作战争侧保留。 |
| **有期限未来战争成本** `future_war_cost_upper_raw` 与独立风险额 `future_risk_budget_raw` | 同帧当前与全军满员预测月费的原生 Q100000 rate、当前 army/补员/舰队/佣兵合同、下一付款时间与金额、期限内已排定费用及风险政策。原版 `MilitaryView` getter 是月费率；舰队可使实际维护费超过预测。 | 最短期限可取至下一游戏日首次暂停帧，重新读回前不得继续消费。即使保守预留整月费，原生支付节奏、舰队/补员、事件/雇佣/上船等完整上界不明时仍只能是条件性政策候选，不能声称数学上界。不能将月费除以 30 当一日付款。兵数、补员开关、海路、合同、日期或 frame 变化均失效。 |
| **现有已承诺支出** `existing_commitments.gold_raw` | M5 跨域 owner 已承诺交易表与战争未结现金账本的去重汇总；将前述 `pending_war_cash_raw` 纳入一次，另列已锁定建设/外交/婚姻等成本。`M5FrameDispatcher` 的内存保留只覆盖本实例，不能证明外部交易全空。 | 每项具有交易 ID、来源域、玩家、frame、结算状态和金额；跨恢复连续。R0266 collector 目前只核总额不小于战争 pending，不能证明其他域项完整。总额、war pending、当次 action fee 三者不得互相重复计入。 |

## 最短实机路径

1. 先确定**当前最新已冻结**的 Robert checkpoint；来源给出 H3603 七件官方 rebound/family/no-launch 白名单，且接收端已逐 SHA 传输验收，但 R0299/R0300 已继续推进，H3603 降为历史隔离研发资产。H3670 七件仅被接受为历史传输，源确认未传；H3674 仅有 raw pair 元数据。接收端对任何新 pair 仍需独立官方 no-launch 与受管暂停帧前后身份双读。H3446/H3492/H3568/H3603/H3670 的既有资产不得跨帧借数；只有生产者可审核后才请求最新帧的大件及停帧窗口。
2. 在暂停帧只读读取 gold、WarID、唯一 owner 请求状态；被动扫描 `MilitaryView` 缓存并核玩家 subject、刷新、新鲜度和 GUI 值。此步最多得到**月费率候选**，不能生成未来上界或任何零证明。
3. 冻结具体下一战争 step，按上表收集原生报价与完整未结账本；补出付款时点和政策文本。任一项缺失时继续输出 typed `null` 和明确缺口。
4. 在 M5 消费前重读同一 frame/step/路线/国库，按用途相加独立建设最低额与战争未来成本、风险额、战争最低额。已接入的两个 M5 selector 在有活跃战争且消费非战争提案时累加独立最低额；战争提案自身与全局战争保留额可用 `max` 避免双计。纯结构候选见 `m5_war_cash_binding_candidate.py`，其返回值固定为 `formal_action_ready=false`。正式战争继续作战提案现要求同帧 typed step/参数和报价结构逐项相等，但原生报价来源与新鲜度仍未证。

精确源链参见 [现金节奏静态审计](r0266-war-cash-cadence-static-audit-2026-09-28.md)、[动作绑定门禁](r0266-war-cash-action-binding-followup-2026-09-28.md)和[上船报价 ABI](r0266-embark-quote-abi-static-2026-09-28.md)。

**额外原版 GUI 线索。**`game/gui/hud.gui:6121-6131` 的常驻黄金 tooltip 将 `InGameTopbar.GetGoldIncomeBreakdown` 和 `GetGoldExpensesBreakdown` 分开，`6183-6193` 又显示 `GetGoldBalance`。精确 EXE 静态校验定位 callback、渲染帧驱动的缓存刷新与 played CharacterID 来源，见[顶栏费用 ABI 审计](r0266-topbar-expense-static-2026-09-28.md)。getter 会刷新并写缓存，不能直接作为纯读桥接调用；被动缓存也没有 H3603 同帧实例、新鲜度、独立军事行或现金账期证明。总支出即使取得，也不能自行分离战争未结占款或形成未来费用上界，不能代填五项现金字段。
