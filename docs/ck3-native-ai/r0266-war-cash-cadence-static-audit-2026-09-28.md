# R0266 战时现金：月费节奏与短期上界静态审计

状态：**静态来源已核；现金实值、扣款时点和完整上界未核。** 本审计只针对本机原版 CK3 1.19.0.6（`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）。没有启动游戏、读取 Robert 新帧或填写 R0266 收据的任何金额。历史 H2825 建造帧仍是五个战争金额输入 `null`。

## 原版实际说明了什么

| 现金项 | 原版来源 | 对 R0266 的含义 |
| --- | --- | --- |
| 当前军费与全军征召预测军费 | `game/gui/window_military.gui:535-658,944-1052` 分别展示 `GetGoldMilitaryExpenses` 与 `GetAllRaisedGoldMilitaryExpenses`；`game/localization/english/gui/militaryview_l_english.yml:45-47` 将后者定义为“全军征召且满员时”的**预测月费**，并明确舰队可使实际维护费更高。 | 两者均是费用率/预测，不能当作已扣现金；后者单独不能构成未来总现金上界。R0266 候选 `MilitaryView+0x740/+0x748` 只给预测缓存 raw/scale 的被动读取路线；必须证明实例属于玩家、缓存属于当前暂停帧且和可见值相符。当前费用 getter 会写 view 状态，不宜由桥接主动调用。 |
| 征召兵与兵员补充 | `game/common/defines/00_defines.txt:628-635` 给兵员补充速度与 `GOLD_COST_PER_SOLDIER=0.003`；`game/common/men_at_arms_types/_men_at_arms_types.info:35-37` 分开购买费用、未征召且满员/停补时的低维护费、征召或未满员时的高维护费。`game/gui/window_military.gui:489-505,899-915` 还提供补员开关及费用 tooltip；`game/localization/english/gui/menatarmsview_l_english.yml:9` 把兵团补员费用标成每月。 | 当前兵数、补员是否开启、兵团满员状态和未来补员都影响费用。静态 define 不是 Robert 的动态 Q100000 实值；不得仅用当前较低费用外推。 |
| 舰队与上船 | `game/common/defines/00_defines.txt:695-699` 指定 `EMBARK_GOLD_COST_PER_HUNDRED=1`（上船费用）和 `GOLD_COST_MAINTENANCE_MULT=0.25`（上船期间增加军费）；`game/gui/map_icon_layer.gui:650-663` 与 `game/localization/english/gui/mapicons_l_english.yml:27` 有预览上船费用的 GUI 入口。 | 上船即时支出必须和之后的舰队维护费分开预算。预览文本采用 `V0` 格式，不能反推出精确 raw；海路可发生而未证明费用时，短期上界保持未知。 |
| 佣兵 | `game/common/defines/00_defines.txt:1176-1200` 给雇佣期限、按兵力计价等参数；`game/gui/window_military.gui:3674-3895` 展示雇用状态、债务判断和 `MercenaryCompany.GetCostDesc`；`game/localization/english/gui/hired_troops_view_l_english.yml:62-64` 明确区分雇用与延长契约的费用；`game/common/important_actions/00_mercenaries_actions.txt:1-12` 在到期不足 180 日提供提醒。 | 必须同帧枚举已雇佣军团、到期日、待办雇用/续约动作和各动作精确原生费用。到期提醒不能证明自动续费，也不能把未计划续约直接填 0。 |

原版脚本的 `on_army_monthly` 在 `game/common/on_action/army_on_actions.txt:1-7` 注释为“每 30 日、日期依 army ID”，但它是军队事件 hook，**不能**证明角色金币或军费的扣款日期。上述 GUI、defines、script values 与 on_action 均没有给出本版本 Robert 金币维护费的结算日、结算顺序或一次扣费的精确原生入口。`game/common/script_values/01_dynamic_values.txt:2021-2024` 还明确把 `monthly_character_income_minus_expenses` 写成 `monthly_character_income - monthly_character_expenses`；不能从现有 `player_monthly_gold_income` 单字段倒推出军事支出。第一日、每月首日或每日按比例扣款都**尚未得到本审计证明**。

## 同帧读回清单

每项都绑定同一个玩家完整 CharacterID、WarID、episode、`snapshot_id`、公开/原生修订与日期，并在暂停帧前后双读。`raw` 必须来自已确认 Q100000 的原生字段，或从原生已核固定小数做无损转换；GUI 的舍入文本不合格。

1. 国库原生 `gold_raw` 与建造报价；独立读取当前军费、全军征召满员预测军费及各自 breakdown，核 `MilitaryView` 的玩家 subject、缓存刷新时机、raw 与 scale（候选 scale 为 `100000`）。读取值仍只是**月费率**。
2. 当前所有兵团/征召兵人数、未满员和补员开关、是否已征召/在舰队，以及已雇佣佣兵的所有权和剩余契约期；与当次战争计划的路线/动作绑定。新增兵团、征召、补员状态、上船、雇用、续约均使旧预算失效。
3. 战争待办动作账本逐项金额；当次唯一战争动作的即时费用或有来源的精确 0。上船预览、佣兵报价和兵团购买费用应查原生数值，不能使用 GUI `V0` 字符串。
4. 明示 `horizon_days`、下一次强制重审边界、预测月费到期限内现金扣款的转换依据、舰队/即时费用和额外风险预算；另由战争政策给出最低现金保留额。原版 AI 的 `MONTHS_OF_MAINTENANCE_IN_WAR_CHEST=18`（`game/common/defines/ai/00_ai.txt:135-154`）可作政策设计参考，不能冒充 Robert 玩家已有的原生保留金。

## 可恢复的一日 horizon 风险合同

先将决策期限收窄为**至多下一个游戏日**，每次推进前重新观察，日期推进后立即暂停并重审。只允许已报价、无海路、无雇佣/续约/购买的既定动作；任何弹窗、战斗、人数/补员/舰队/价格/战争/玩家身份变化均停止复用旧收据。即使只推进一日，也至少把**一个完整月**的、同帧核实的 `max(当前军费率, 全军征召满员预测军费率)` 放入风险预留，绝不按 `1/30` 缩小；若存在上船或其他单次费用，再单列原生报价。下一日如果不能完成重新观察，则停止花费决策。

这是一条**条件性政策候选**，不是已证明的数学上界：一日最多结算一次月费、预测月费覆盖这支军队、无未列事件支出等前提仍缺少原生/实机证据。要将它写入 `future_war_cost_upper_raw`，须在受管实机跨实际扣款窗口前后读取国库、收入、军费 breakdown 与所有即时账目，证明结算节奏及上界适用性，并由战争侧明确接受其事件风险预算。否则 `future_war_cost_upper_raw=null`、`future_risk_budget_raw=null`，`cash_inputs_status=incomplete`；即便被动缓存找到唯一值也不得批准受影响的建造。
