# P83：战时建设资金门槛与筹款接口缺口

2026-10-18 公共源码候选，**未提交、未推送、未部署 R9，SDK05 的 9032 / Native26 冻结输入未修改**。`machine_id: xenoamess-full-tower-eb9d2c1186`。源文件 SHA、stock 摘录、资格实际 UTC 与私有小包路径见 [source proof](evidence/p83-wartime-construction-cash-and-financing-gaps-2026-10-18.json)。这是离线 source / mock 资格，没有新增真实取消、退款、借款、雇佣或战果。

## 用户规则与公共 gate

用户新增三条战争开支规则已写入 AGENTS：战时只有军费非常充裕才新建建筑、升级或建新地产；缺钱或危局评估取消在建项目换军费；绝境评估合法借款，不预记未到账资金。这些用户规则没有固定金额或月份。

新 `wartime_construction_cash_v1` 将当前政策写成可审参数：一次可选建设全部付款后，还须保留 **max(400 金，当前最大军费 × 24 月) + 已有未付承诺 + 当前原生雇佣应急报价**。400 与 24 均是候选政策，不是用户硬门槛、原生规则或未来费用上界。军费是跨战争的当前最大值，只计一次；正收入、未到账借款和未获退款不提前入账。已付合同已反映在当前钱包，不再次扣除。

应急报价按以下顺序留款：

1. 使用来源绑定、同帧已评估且足够当前已知缺口的合格采购报价，并在提交前重新校验当前市场。
2. 否则，在完整原生合法市场中，取能补足当前保护战争已知兵数缺口的最低完整合同报价。兵数不等于战斗有效兵力或胜率。
3. 缺口未知或没有一家公司足量时，保守保留当前完整合法市场的**最大合同报价**；不以廉价弱兵代替战争应急资金。

Native CanHire / CanAfford、完整十槽费用、当前可用兵数与原生出生省就绪仍是报价资格。当前出生省已有可见敌军者不作为可用应急选项。所有市场行保留比较。抵达 ETA 和战斗胜率仍 unknown；最大报价只是现金政策，不说明任何公司能解围或获胜。

当前市场缺失或过期时，延期可选建设并继续原 war / clock。完整查询确认市场为空时，单列 `complete_empty` 与“当前无公司”事实，按保守政策同样延期；不伪称缺读，也不为建设等待补读。费用、最大军费或已有支出意向不全，同样只延期新支出。

已接入的空槽新建筑和经济升级共用原 construction consumer：可选查询前做一次零费用预检，取得真实完整工程报价后检查实际全款，Native 发送前再根据当前输入重验，拒绝时不创建工程 intent。原 pending / applied 回执继续在新资金 gate 之前处理。

`new_holding` 已纳入同一资金分类，但现有生产桥没有新地产 Native action 接口，明确返回 `new_holding_native_action_interface_unavailable`；不新造公开按钮或声称有可执行建地产能力。对低战分己方战争，既有现金保护仍可进一步禁止可选建设。和平建设规则保持原路径。

## 当前 R9 的狭范围保护

Root 另要求核本场 −87、防御战争 `100663323`、目标 `2230`、约 228 金是否已经禁新建。只读已装源码得出：SDK48 construction 本体没有 losing-war 守卫；保护来自 R9 bootstrap 按 SHA 安装的 P62 `war_finance_startup_v1` wrapper。

该 wrapper 的 `construction` 在 `primary + defender + targets非空 + score<0` 的现金保护条件下保留原战争 / 时钟并延期新经济建设，只允许既有工程回执处理。对应源文件均匹配 bootstrap pin。因此 **Root 提供的本场字段落在既有保护范围**；这里没有独立读取新的 live 帧，也不外推“所有战争已采用 P83”。完整四个小叶 SHA 与片段在 `R9-OLD-WAR-CASH-SOURCE-CHECK.json`。没有改动当前 R9 源码或现场。

## 取消工程：已核来源和最小接口设计

实际读取仓库参考 stock：

- `gui/window_county_view.gui:1639–1641` 有 `HoldingView.CanCancelConstruction` / `CancelHoldingConstruction`；`3088–3091` 有 `GUITrackItem.CanShowCancel` / `CanCancel` / `Cancel` / `GetCancelTooltip`。
- `common/buildings/_buildings.info:394–406` 记录 `on_start / on_cancelled / on_complete` 生命周期。
- 当前 `.4` construction Native / Python source 只有选购、提交与材料回执，没有已闭的取消 final gate、数值退款报价或取消 receiver。GUI 名称和 tooltip 不能替代数值报价与 ABI 证明。

这些参考 stock 文件的 SHA 已冻结；没有验证它们等于当前已安装游戏，不能据盘符或旧资料追认其机器/build 效力。这里不采用任何退款百分比。

最小后续只读接口应按 exact build / actor / episode / native frame 枚举正在进行的工程，给出省份、头衔、槽位、建筑与项目身份、当前进度、最终 `CanCancel`、完整原生退款与取消费用资源向量及来源。任一 getter / 身份 / ABI 未闭时返回 unavailable 和真实原因。建议私有查询名 `query-player-construction-cancel-terms-v1`，**尚未实现或注册**。

后续提交只消费同帧 Native 合法条款：先保存唯一 pending claim，再经真实原生 validator / receiver 单发取消；未知 ACK 不重放。随后分别读取新帧钱包与确切项目状态。钱包差额或项目消失各自都不能单独证明退款成功，更不能由 ACK 宣称两者已生效。该完整路径尚未实现。

## 合法债务：已核来源和最小接口设计

参考 stock `00_holy_order_decisions.txt` 确实包含 `borrow_from_holy_order_decision`：检查已有贷款、同信仰组织、贷款方资金与关系，再经 `holy_order.0200` 事件分支处理。实际选择与到账不能由决议名字推断。

现有 `player_holy_order_loan_context_private_transport` **只接受 exact 1.20.0.3 且为 read-only**：可读本金报价、既有欠款、贷款人、年限、borrow / repay 的原生 shown / CanTake / affordability / costs。它不是 `.4` 借款动作。公共 decision browser 的 confirm 另受 `expected_window_kind == vivhite_courtier` 限制，也不能泛化成借款执行通道。没有当前 `.4` 借款 final terms → submit → 独立债务 / 钱包到账全链。

最小后续 `.4` 只读接口应来源绑定地枚举当前真实合法的贷款决议与贷款方，读取最终资格、完整成本、本金、既有债务、冷却、偿还与违约条件，以及是否需要事件选择；缺省值不可伪作零。建议私有查询名 `query-player-emergency-loan-terms-v1`，**尚未实现或注册**。未来执行需独立唯一 claim、原生合法单发、记录实际事件与选项，并读回债务身份和钱包到账。尚未到账的本金不能用于 Native CanAfford 或佣兵预算。

未来若退款或贷款确实到账，应以独立确认、可归因的资金回执在**同一采购 epoch**追加 funding revision，按 receipt ID 去重并累计已付及未知承诺；不能换 epoch 刷新当前现金比例。现 P80 的原包现金上限不会因为本诊断自动扩大，接口缺失阶段不做这项 credit、不凭钱包差额假记本金。

## 决策显示与资格

新筹款诊断会在缺钱或真实危局时说明：需要考虑取消 / 合法借款，但当前缺少对应可核退款 / 借款执行通道；不计划动作，不制造预期资金，继续战争。已有工程 intent 不等于当前项目仍在施工；上屏原因保持这一区分。

早期回归 **80 passed**；市场策略 review 后，新 gate 与真实普通 MCP / GameplayBridgeService 的富裕战时建造 → 单次提交 → 独立材料 → 冷恢复组合 **19 passed**。新负例覆盖弱廉价公司、空市场与未知市场、三个建设分类、过期输入、原生拒绝、未决雇佣、实际全款边界，以及提交前缺输入时零 intent / 零 Native send。两次 Service 夹具 RED 是新资金读取所需 `readiness` 缺失，已保留并修正夹具，未放宽生产守卫。最后补齐当前合格采购优先、过期采购失效断言后，改变后的完整 losing-war CI 分组为 **112 passed in 12.90s**；实际 UTC、完整命令和日志见 source proof。尚未取得实际发布 commit 的远端 CI 结果。

外置工作包独占 `N/p83-wartime-cash01`，全部源码 / 摘要 / 测试 / scratch / 日志严格不超过 512 KiB；每次测试前按 retained + 256 KiB scratch + 32 KiB 日志预检，TMP / TEMP 在同一根，`-B`，闭场回收本次临时夹具。旧 P71 冻结，不增加它的内容或期限；未动游戏、Driver 大体、媒体、存档、Native 构建和当前冻结部署。

## 追加：实际公共发布（2026-10-18）

截至本次回执观察 **2026-10-18T03:14:15.957854+00:00**，Root 已实际发布 `64b241e4e1f83628bfaa4ad4d965099951c504b1`（actual push 回执 `exec chunk fc251a`）。正常 rebase 保留远端 `6000cbde8beedae53048a4ce1ffbecf576e3cb6d` 及其新增 6 个提交；原未发布候选 `556253c25b2a73dff37fade4456459732efd8829` 保存在 `archive/p83-pre-rebase-20261018T0311`。本地读回该 published commit 的 Git commit 时间为 `2026-10-18T11:11:51+08:00`；未把它冒充推送时刻。

初次 candidate、原源码 SHA、112 项本地 CI 分组与 19 项 Service 资格均保留为历史事实。对应远端 CI 由既有 watcher 独占监看：Official `39092773492`、Linear `39092773483`，**最终结果待该 exact commit 的终态回执**；不沿用原未发布候选的 CI。当前 R9 和冻结 SDK05 未因本公共发布切换，主线恢复与录制继续独立推进。

## 追加勘误：push 回执与后续时间线（2026-10-18）

本次勘误观察于 `2026-10-18T03:17:18.230812+00:00`，`machine_id: xenoamess-full-tower-eb9d2c1186`。此前 publication 追加将 push 工具回执的末尾多抄一位；**依据 Root 原始工具结果，准确的 `chunk_id` 为 `fc251a`**，上节有效引用已纠正。Git CommitDate、原 candidate、源码 SHA 和资格历史没有因此修改。

Root 随后补充小型 SEM1540（报告 actual `03:11:09`）的 `active_wars=[]`：截至该帧已经没有活跃战争。较早 −87 本场保护只是当时 Root 所报字段的历史源码适用判断；本 agent 未独立读取新的现场帧。**终战方式、胜败与领土损失尚未核实，不能据战争消失宣称获胜。**

## 追加：P83 exact commit 的远端双 CI 终态（2026-10-18）

复用既有 sole watcher 的实际终态回执，观察 UTC **2026-10-18T03:33:25.894990+00:00**、`machine_id: xenoamess-full-tower-eb9d2c1186`：已发表 **`64b241e4e1f83628bfaa4ad4d965099951c504b1`** 的 [Official Runner CI 39092773492](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39092773492) 与 [Linear history 39092773483](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39092773483) 均 completed / success；Official 的 static job `117572827195` 于 `03:32:39Z` 完成。两份工作流的 `headSha` 都精确等于该已发布提交。

此前 pending、未发布 `556`、原 candidate、源码 SHA 和本地资格仍保留为历史；本终态只授上述 exact `64b` CI 信用。上次 publication 勘误四文档已由 Root 发布为 `65c5861b9e650d8def33ef789600612bf29ad2f3`（push `e39e95`，exit 0），该后续文档提交不另借本 CI 的资格。当前追加观察时间为 `2026-10-18T03:35:50.441082+00:00`；未再查询远端、重跑测试或提交 / 推送。本事实不证明 R9 / 冻结 SDK 已加载 P83，也不授实机结果或 G2 信用；P80 未修改。

## 追加勘误：实际安装借贷定义与可复用提交入口（2026-10-18）

本次只读观察截止 **2026-10-18T06:41:00Z**，`machine_id: xenoamess-full-tower-eb9d2c1186`。完整小型来源、实际安装 SHA 和读取边界见 [借贷 source proof](evidence/p87-loan-actual-install-source-2026-10-18.json)。Root 已核本场为 `.4`、EXE SHA 前缀 `98702F`；本 agent 没有读取、stat 或 hash EXE、冻结运行树或现场。以下证明当前安装目录的 stock 定义，不替代当前加载定义、角色合法性或 Native 报价。

此前“公共 decision confirm 只支持白绮”的判断过宽：旧 `ck3_confirm_ingame_decision_item_v1` 确有限定，但已有 **`ck3_confirm_ingame_decision_outcome_v1`** 可对实际选中的玩家决议，单发原生可见且 enabled 的唯一 Confirm，并独立验证声明的事件窗口。其 Native admission 明确接受 exact `.3/.4`；既有跨 revision 未知 claim 不重放。因此未来借款可复用 select `borrow_from_holy_order_decision` → generic Confirm，预期 `holy_order.0200`。当前 DLL 是否公告该能力、当帧人物是否可借尚未查询；这不是已执行贷款，也不是已闭贷款业务链。

实际安装两叶与原仓库参考不同：`00_holy_order_decisions.txt` 为 `137cc1b2…`，`holy_order_events.txt` 为 `f4820ff4…`，不能把旧参考 SHA 追认为当前安装。实际借款展示要求可玩、高于男爵、同信仰存在军事类团长、没有已有 owed／holder；合法候选团长须拥有不少于 **借款人** `holy_order_gold_value` 的现金，且没有所列坏关系。坏关系实际是 potential rival／victim／bully／rival，不等同于总好感负数。费用为 50 虔诚，冷却 5475 天；没有禁止战争的条件，也不能跳过原生合法性。

**本金和债务不是在 Confirm 时产生。** 决议随机选合格团长并打开 `holy_order.0200`；该事件的 `amount_to_loan` 是仅保留一天的 tooltip 变量。选择实际可用的 `holy_order.0200.a` 才重新求值本金并调用 `set_up_loan_effect`，写 owed／holder、borrower years=0、原双方身份和 lender 的债务人列表，再由 lender 支付。实际安装本金表达式为 `12 × monthly_character_income`，下限 `300 × era_factor`、上限 `750 × era_factor`；无 culture 时系数 1，否则前早期中世纪／早期／高／晚分别为 0.75／1／1.5／3。这是定义公式，**不是当前报价，也不授权提前计入现金**。

实际 repay 决议要求 owed 及债主列表中的本人、`is_available` 和金币足额，支付 owed 本金后清相关变量、借款 flag 和债务人列表。所核 setup／年度／repay 链没有本金利息累加或额外还款收费；不外推到其他借贷、mod 或未经观察的执行结果。年度是角色随机年度脉冲，`.0206` 增加借款人年数；`.0202` 却在 holder 作用域检查年数，因此不能承诺固定十年催收。催收可合法还款、虔诚等级至少 3 时申请五年延期，或承受拒付后果；后续有条件以 25／75 权重要求租地／子女，并可能产生 −30、20 年衰减意见及虔诚等级损失。权重不是实测概率，移除借款 flag 不等于消除本金债务。

最短缺口应缩窄为 **`.4` 贷款条款及独立债务读器、策略 consumer 与到账后资金回执**，无需先重造一套借款 command。已有 `.4` `religion_context_addons::DecisionBindings` 可复用最终决议门槛和成本 ABI；旧 loan query 仍硬限 `.3`，且费用 DTO 只投影四种资源。未来补 exact `.4` 原生本金求值、十槽费用及 typed owed／holder／双方身份／债务人关系，复用 generic Confirm 和原事件选择，再由新帧钱包与债务关系共同确认到账。已确认资金应以唯一 receipt 在原采购 epoch 累计修订；不能换包刷新、预花预期本金或由 ACK／钱包差额单独记贷款成功。取消工程的数值退款、合法取消及项目／钱包后验仍未实现。本追加没有代码、构建、测试、部署或现场操作；旧历史及 DELIVERY 均保留。
