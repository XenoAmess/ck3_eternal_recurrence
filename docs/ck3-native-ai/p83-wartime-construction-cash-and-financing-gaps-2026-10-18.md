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
