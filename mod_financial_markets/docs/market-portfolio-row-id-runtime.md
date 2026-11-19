# 市场投资组合行的数值身份解析

本包修复 3 个 GUI 中 37 处行参数，不包含债务、新闻和 OTC 的其余 6 处回调。原生表达式采用 MakeScopeValue(Scope.Var('...id').GetValue)；R0020 的同账户真实历史三行只读探针已经证明正例 enabled、负例 disabled 且无相关解析错误。此事实没有替代本包撤单、仓位选择与减仓的后继实机验收。

行只提交数值，不把数值当 Story。服务器在当前 UI 页重新解析，先要求完整匹配数等于一，再保存实际 Story scope，返回角色根作用域，重新检查原权限并调用原业务 effect。所有 IsValid、IsValidTooltip 与 visible 路径只读。订单 ID 使用现货／期货类型、实际 xfm_kind（现货缺失为 0，期货为 2）、active/history 表域共同区分。现货持仓使用当前账户和 coin_id，期货持仓使用 position_id；缺失或非数值 ID 的 GetValue 为零，入口拒绝 ID <= 0。

持仓／活跃订单／现货历史各缓存最多 16 个真实引用。缓存仅由现有正常 open/refresh、分页、切账户、提交或撤单重建；无每日任务、全世界或全市场解析。显式重建各遍历一次当前账户的对应维护列表，行校验只遍历当前 16 项。快照记录账户和 offset，任一改变立即使旧快照无效。执行时另核实际维护列表的当前成员资格；缓存内同类型同 ID 的多个对象全部拒绝，不选第一个。取消仍检查原订单状态、账户与真实 holder，期货仓位选择另拒绝已关闭仓位。账户选择器延续原 owned accounts 列表，当前没有额外 16 行上限；本包不声称它已分页。

币选择的纯 IsValid 只解析既有 16 币页；原全局 registry 成员校验完整留在 effect 执行前原文重验，不在逐帧校验中搜索全 registry。期货盘口只解析原有每侧 5 笔快照，保留当前合约、资金与关联方检查，允许读取真实外部委托，绝不套用本人订单条件。全部金融效果、资金、ID 分配、撮合、强平、止损与规则保持原生产实现。

源码测试分两层：MarketOrderRowContextContractTest 检查 GUI / handler / cache / inventory 生成引用；FuturesBookUiScriptContractTest 执行实际新 resolver、SGUI、现货撮合与撤单、期货减仓订单及保证金 producer。其既有期货 matcher port 仍只执行真实余量入簿，不造 fill；四手仓减两手的测试验证真实 close order，不将它写成仓位已经成交减到两手。新软件 case 不授予游戏内 API 或物理 SAVE 后态。

后继正常验收：从最新真实 SAVE 打开市场并正常刷新；定位实际 order13/14 各余5的独立行，单次撤销后物理 SAVE 分别核 selected order、status、remaining 与 reserved，以及其他订单不变。选择真实 grain position11（native1251、四手）后，普通数量／限价控件提交两手减仓；分别记录已提交、是否自然撮合和后态。不得重放旧 order760。后台仍保持最小化，不热改冻结 runtime，不靠 UI flags 代替 SAVE 对账。
