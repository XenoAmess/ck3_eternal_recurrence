# R0303 战时最低现金保留额：静态来源与拒绝条件

本页针对 WAR R0303 转达的 H3686 同帧建造候选：`farm_estates_01` 原生价格仍为 Q100000 raw `18,000,000`，国库约 raw `119.944m`。该帧五项战争现金输入仍为 `null`；本页没有新 CK3 实机读回，也不把 H2825/H3075 旧帧价格之外的现金读数迁移到 H3686。

## 现有来源能证明什么

`m5_war_cash_resource_v1.py:15-20,53-77,89-113` 要求 `policy_minimum_gold_reserve_raw` 与另外四项现金同帧、同 WarID、Q100000、非负，并计算 `joint_gold_reserve_raw = future_war_cost_upper_raw + future_risk_budget_raw + policy_minimum_gold_reserve_raw`。`m5_formal_proposal_collector.py:140-170` 检查共享保留额覆盖该和；两个 M5 selector 对活跃战争中的非战争提案把自身最低保留额与全局战争保留额相加，对战争提案自身与全局战争保留额可取 `max` 避免重复。这些是**消费合同**，没有定义 Robert 的战争政策金额、作者、版本、有效期或风险覆盖。

现有建造政策 `bridge/domain_construction_private_transport_v1.py:23-27` 的 `RESERVE_RAW=20,000,000` 是建造动作完成后的 200 金保留门；派系赠礼 `bridge/faction_gift_formal_route_v1.py:36-39` 另有 100 金门。二者的 domain 和消费动作不同，不能直接填战争政策项。原版 AI `game/common/defines/ai/00_ai.txt:135-154` 的 `MIN_WAR_CHEST=25/25/50/100/200/300/400` 金与 18 个月维护量，静态调用链在 [宣战输入研究](war-film-declaration-inputs-2026-09-23.md) 中闭合到 **AI 宣战前**的 war chest 检查；它不是玩家 Robert 现役防守战争的最低保留政策。H2743 存档中还没有玩家 CharacterID 29829 的 AI strategy 行，见 [R0266 来源说明](r0266-war-cash-resource-2026-09-28.md)。因此目前不能为 H3686 提出有来源的非零战争最低保留额；也不能以零代替缺失政策。

## 可审阅的政策候选与版本门

2026-10-03 项目所有者已全面授权当前执行者继续战争研究、实现、现金政策及实机运行，旧战争暂停与非战争限定已撤销。发布**新的玩家战争现金政策**时，最低可审阅字段应包含：政策 ID 与版本、仓库跟踪文件的固定 SHA-256、作者/复核证据、玩家 CharacterID、WarID、episode、生效与失效帧日期、适用 horizon、Q100000 金额和计算依据。政策必须明确表示该金额是**支付期限内未来支出后还要留下的终点流动性**，不是未来费用或风险支出的另一个名字。若基于军费率设定，先取得该军费率完整同帧原生证据并说明政策系数；原版 AI 18 个月公式和建造 200 金都不能自动作为玩家政策版本。

[候选 provenance gate](../../ck3_autonomous_player/src/xar_autoplayer/war_cash_floor_policy_provenance_v1.py) 只验证传入政策文档 bytes 与外部可信配置中已固定的 SHA-256 相等、玩家/WarID/episode/日期/horizon 匹配、用途为 `terminal_liquidity_after_horizon`，并要求终点流动性、期限内未来支出、额外风险支出的现金用途 ID 两两不重叠。按当前原生日期单位一游戏日为 24 raw，政策失效日期还必须覆盖整个 `horizon_days`；只覆盖本帧而不覆盖下一日的文件会拒绝。缺政策来源返回 `policy_source_unavailable_unknown`；旧版、串帧、重复用途或凭空省略风险范围会拒绝。通过后状态仅为 `candidate_document_and_claims_valid`，始终输出 `formal_cash_receipt_eligible=false`：调用者仍须证明**固定 SHA 来自已发布政策**、未来及风险用途 ID 来自同帧原生/政策收据、五项现金金额有实证，才能考虑接入 M5。测试里的 250 金与 0 金仅为 synthetic fixture，**不是 Robert 政策**。

## 三个桶的防重复计数规则

1. `future_war_cost_upper_raw` 是明确 horizon 内已列成本的上界；`future_risk_budget_raw` 只能覆盖该上界**未涵盖**且有明确政策额度的额外不确定现金用途。若两者指向同一笔上船费、补员或维护扣款，就已重复；若未知事件无法给有限风险额，则风险仍为 `null`。
2. `policy_minimum_gold_reserve_raw` 是到 horizon 末的保留余额。它与期限内支出可相加，仅在政策明确两者用途和时间界限时成立；把“再备一月军费”同时计入未来上界、风险额和终点保留，会三重计数。候选门要求三组用途 ID 两两分离。
3. 建造自己的 200 金保留门与全局战争保留额是**余额下限**。当前 M5 选择器在活跃战争中先按独立用途相加，以确保建造完成、期限内战争费用支付后仍有建造政策要求的余额；若以后有正式政策证明两项重叠，须另写版本化合同后才能缩减，不能凭相同单位取 `max`。待办战争付款则进入 `existing_commitments.gold_raw` 一次，本次战争动作费用只进入选中提案的 `gold_cost_raw` 一次。

H3686 现在仍需保持 `policy_minimum_gold_reserve_raw=null`、`future_risk_budget_raw=null`，整份战争现金收据为 `incomplete`，建造可负担性未评估。即使后来发布最低保留政策，只填其中一项也不会解除其余四项的门；任何金额、用途或战局变化都须在新暂停帧重审。
