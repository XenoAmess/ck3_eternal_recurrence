# M4：借款门槛和声明成本的独立投影

观察于 **2026-10-19T03:49:53.573665Z**，`machine_id: xenoamess-full-tower-eb9d2c1186`，身份复用 `tools/ck3_live_run_id.py`。本次仅读取仓库源码及已绑定原版定义审计，没有游戏、桌面、RPC、活跃 Driver/SAVE、冻结 SDK 或运行树访问，没有重新编译已通过的 provider。源码 SHA、单次测试的精确命令和日志在[小证据](evidence/g2-m4-loan-decision-projection-2026-10-19.json)。M4 历史 complete 不变。

新增[纯投影叶](../../ck3_autonomous_player/src/xar_autoplayer/holy_order_loan_decision_observation_v1.py)消费前一阶段[编译通过的只读 provider](g2-m4-research-2026-10-19.md)。它分开表达当前原生 shown、CanTake、CanAfford 和全部十槽声明成本；不再需要未来 consumer 自行把四资源 DTO 当作完整报价。它没有任何 driver、IO、查询、提交或资金写入，也没有接普通 planner 或公开路由。

| 所需事实 | 已核来源与实际能读到的范围 | 当前剩余缺口 |
| --- | --- | --- |
| 实际选中借款决议 | `ingame_decision_item_v1.cpp` 与 `normalize_decision_item` 绑定完整 key、实际列表 model/selected detail、actor、revision、PID/connection | 该 DTO 不含原生数值本金或完整成本；选中/显示不能替代借款条款 |
| 决议最终资格 | `.4` provider 复用现有 DecisionBindings 的 shown、CanTake、CanAfford | 已实际编译，尚未注册或在 `.4` 真实帧执行；本轮 synthetic true/false 不能授当前角色资格 |
| 声明费用 | 同一 provider 调用原生 evaluator，完整十个 signed int64 resource slots，scale100000 | 仍须未来 query owner 的真实同帧读取；不能把静态50虔诚或 fixture 当作本帧成本 |
| 借款本金 | 已绑定原版定义的 `holy_order_gold_value` 在玩家作用域实际求值；不是固定300金 | `.4` plain-value registry/evaluator ABI 尚未闭合，当前 provider 没有该 getter；本轮保持 `null` |
| 事件可见金额 | 原版 `.0200` 使用一天期限的角色变量 `amount_to_loan` 作 tooltip；实际 `.0200.a` 会重新求值 | 现有 event-context 的 saved_scopes 读命名 scope token，不能因此读到任意角色变量。不能把它作为已出现的 numeric saved scope、本金锁价或到账 |
| 决议执行与事件出现 | 既有 generic Confirm 验当前实际选中的合法 receiver，独立核 `holy_order.0200` 与玩家 root | 这是决议/窗口结果；成本支出、贷款成立和到账须分别读回 |
| 事件实际选项 | 既有事件原生接口提供实例、定义与当前显示顺序/可用项，按当前实例绑定原生选项 | 未来贷款 consumer 须单独绑定实际可用的 `.0200.a`，不能由定义后缀猜固定 Native 索引；未知单发不重放 |
| 既有债务和偿还本金 | 原版 setup 写 owed/holder/双方原身份和 lender 债务人列表，repay effect 支付当前 owed | `.4` typed 债务/双方关系读取尚缺。repay 声明成本全零也不能推导总偿还支出为零 |
| 真正可花资金 | 新帧钱包加独立匹配的本金、holder、双方债务关系及可归因资金回执 | ACK、Confirm、tooltip、事件关闭或单独钱包差额都不足；本投影始终零资金信用 |

原版定义的依据继续是[2026-10-18 已安装文件审计](evidence/p87-loan-actual-install-source-2026-10-18.json)，其 `machine_id` 与本次相同；该审计明确没有独立确认当前已加载定义或当前角色资格。本轮没有重读安装目录，不把昨天的来源读回更新为本轮实机事实。当前 GUI/接口范围来自证据中逐叶 SHA 固定的 Native/Python 源码；没有用截图、OCR 或展示文本推测数值。

投影对当前 provider 的 exact `.4`、actor/date/capture epoch、ten-slot 布局和三项独立 bool 做局部合同核对。未来 query owner 仍须提供真实 PID/episode/revision 外层信封；本叶不制造该信封。不可用结果保留 gate/cost `null`。可用结果保留所有 signed 槽，构造新列表供消费者使用，不截为四资源、不把 bool 当金额。

即使三个原生门槛都 true，输出仍保留 `principal_quote_raw=null`、`existing_debt_principal_raw=null`、`repayment_total_outlay_raw=null`、`complete_loan_terms=false`、`submission_qualified=false` 和 `funding_credit_raw=0`。其中 `native_gates_allow_decision` 仅是三项 bool 的合取。隐藏的 repay 即使 CanTake/CanAfford 均 true，合取仍 false；零声明费用仍不说明没有欠款。拒绝把额外伪造的本金、债务、submit 或资金信用混入这个有限 provider。

最小后继接线仍复用现有通道：真实 query owner 包装该 provider → 本叶投影门槛/成本 → 另补 `.4` 本金和 typed 债务 → 原 select/generic Confirm 的唯一 claim → 独立验证 `.0200` → 实际事件选项单发 → 新帧债务与钱包共同后验。只有最后已确认、可归因的唯一 receipt 可以修订**原采购 epoch**，继续累计已付和未知承诺，随后重读当前雇佣市场。期间不能预花本金、清旧采购包或重放未知动作。这条后继链尚未接入，也不阻塞当前合法战争行动或新局。

[定向 fixture](../../ck3_autonomous_player/tests/unit/test_holy_order_loan_decision_observation_v1.py)只跑一次，**20 passed in 0.57s，exit0**。覆盖隐藏 repay/CanTake true、全部 gate true 仍无本金/资金、完整十槽 signed 数值和列表脱离、unavailable 保持 unknown、截断/布尔/溢出成本、错 actor/date/epoch/build，以及伪造本金/债务/信用拒绝。全部是合成 provider 值；未授 Native getter、借款、付款、到场或战果信用。

本轮外置测试使用 storage01 已登记独立小叶，预算256KiB、硬1MiB，关闭 pycache/cacheprovider/plugin autoload；没有复开已闭 compile01。临时日志按通用策略在 `2026-10-21T03:48:40.352809Z` 复核，小型源码证据按180天归纳。无新增全局预留、无旧资产删除或物理释放量信用；最终精确逻辑量及 future0 由同一小叶闭账回执保存。
