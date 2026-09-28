# R0266 战争现金：顶栏自然刷新与五项输入的最小取证合同

状态：**静态路径已核，Robert 的五项现金实值与 horizon 仍未知。**本页只读原版 CK3 1.19.0.6 `ck3.exe`（SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）、原版 GUI 和已提交的 R0266 合同；没有读取进行中的 attempt、游戏进程或屏幕。对应 #449 顶栏诊断基线为 `dc436f03b`。

## 费用缓存何时可能自然重算

精确 EXE 的 `ResetLastUpdateFrame` 名称 RVA `0x40E5F28` 经注册 `0xB1063`、回调 `0xD49B20` 到 `0xD462B0`；后者把顶栏 `this+0xF88` 的 qword 上次更新 tick 写成 `0`。原版 `game/gui/hud.gui:6109-6131` 把金币 widget 的 `_mouse_enter` 绑定该 reset，并把 tooltip 费用区绑定 `GetGoldExpensesBreakdown`。独立静态校验器 [`verify_war_cash_topbar_mouse_enter_refresh_edge.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_topbar_mouse_enter_refresh_edge.py) 以 EXE SHA、精确指令/RVA 和 GUI 绑定拒绝版本漂移；普通及 `-O` 对原版 EXE/GUI 均通过。

费用 getter `0xD47680` 读 GUI 渲染上下文全局 RVA `0x576CC68` 所指对象 `+0x180` 的 qword tick，读 RVA `0x570D8D0` 的 signed dword 刷新间隔，比较 `tick - this+0xF88`。若不低于间隔，它在 `0xD476B1` **先**写新 tick，才在 `0xD476B8` 调用 `0xD476D0` 重算。故鼠标进入后、当前 tick 达到正间隔时，下一次实际执行 getter 应进入重算分支；但 `+0xF88=当前 tick` 可以出现在重算完成前。`tick` 相等、两次 RPM 相同、甚至稳定的行数组，都不能单独证明完成或属于同一个游戏 native revision。严禁 headless reader 直接调用 reset/getter；它们写 GUI 状态。GUI owner 可以在独占屏幕与新鲜 Steam 离线证据下自然悬停，读取器仍只用 `ReadProcessMemory`。

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
