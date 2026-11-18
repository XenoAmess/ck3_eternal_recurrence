# 施工状态

2026-11-18，machine_id: 4-8e1c2f1861。

## 当前交付边界

已开始 A0 原型。一个 Mod，共用金融底座，现货与期货作为内部模块维护。阶段范围、退出标准和性能预算见 [实现计划](implementation-plan.md)，具体用例见 [测试验收](test-and-acceptance-plan.md)。

Java 参考账本已实现稳定账户/币/受益人 ID、有限供应发行及增发、真实费用金库、100 枚一手、整数分、价格时间优先、部分成交、原订单累计手续费、冻结与撤单、关联受益人自成交拒绝、跨币共享资金和失败整笔回滚。日序可以同日幂等推进，但尚无期货日清算。该核心是开发参考，不是游戏运行时，也未证明 CK3 性能。

发行资金参考计算已加入：微型R20需要6金费用或限制，剩余14金；标准R200需要55金费用或限制，剩余145金。费用、维护预存、履约保证金和做市资本分别记账。实际认购、滚动融资上限、风险服务准入仍需生产接线。

14个游戏文件已落地：收费发行、有限双向报价/买卖、每日AI候选、持仓故事和托管候选、玩家决议/互动/回执、中英本地化。首包保护值为32个累计登记身份，并非最终容量。详见[A0原生说明与来源](a0-runtime-notes.md)。完整订单簿尚未接入游戏；合格继承管理入口、全世界公平发现和存档寿命仍待补。

## 已有软件结果

2026-11-18 08:46:16 UTC：

~~~text
mvn -f mod_financial_markets/tools/pom.xml -Dtest=FinancialMarketTest test
~~~

26 tests，0 failure / 0 error / 0 skipped，JUnit 0.426s，Maven 27.844s，exit0。包含确定性随机资金/币守恒序列、先成交外部订单后遇自成交的全笔回滚、跨币余额不能重复冻结。Java release21，-Xlint:all -Werror 编译通过。软件结果不授游戏交易或存档通过。

08:58:55 UTC 新增执行：mvn -f mod_financial_markets/tools/pom.xml -Dtest=ListingFundingTest,PoolQuoteTest test，9项全部通过，Maven14.594s，exit0。两档发行资金分类及A0有理数池报价/双边手续费、最小成交拒绝和溢出边界通过；这是独立计算模型，不证明原生脚本精度。

09:02:17 UTC 执行 mvn -f mod_financial_markets/tools/pom.xml -Dtest=BuildContractTest verify：新增5项构建合同测试全部通过，Maven15.765s，exit0；Quarkus augmentation 1758ms，工具打包完成。含BOM/未定义effect/未列入runtime文件/本地化不一致/路径逃逸/输出覆盖/清单SHA等边界验证。

本轮共40个不同软件用例全部通过。随后对最终报价作用域修订文件运行Quarkus CLI validate：14文件、11个effect、每语言26键，exit0。两个native文件的修订仅有静态信用；事件上下文、引擎语义和业务仍NOT_RUN。GitHub新增 financial-markets-static 工作流执行完整软件验证，不调用游戏。

显式清单见[运行文件清单](../runtime-files.json)，候选工具输出content/与独立manifest.json，排除tools、docs和验收数据。外置候选与实际文件SHA保留在 C:/workspace/ck3-market-task-20261118/candidate-a0-01；这不是已发布包或实机通过凭据。

## 实机状态

本机此前已更新到 CK3 1.21.0 / build26622941，见 [本机更新记录](../../docs/maintenance/2026-11-18-machine4-ck3-update-and-market-design.md)。本轮 08:43 UTC 进程只读检查未见 CK3，未启动游戏、注入或恢复旧自动游玩。

08:43:20.845669Z 公共 steam_offline_state_probe.py 实际 exit2：status=unavailable，reason=cdp_not_enabled，native_provider_unavailable=invalid_input，owned_debugger_candidates=0。原件：C:/workspace/ck3-market-task-20261118/implementation-steam-offline-probe-01.json。该结果不能证明当前在线，也不能作为可启动凭据；本产品尚无1.21共同后台业务场次和公共adapter资格，实机状态为 NOT_RUN / prerequisite BLOCKED。

不通过抢前台或复用1.20 DLL绕过。第一场先做金额精度、故事实体/死亡托管、保存冷载及日历合同，再扩大到百币和完整每日委托簿。

## 后续未完成

1. A1：对照原型真实验证金币精度、资产故事身份、无继承人托管、同日交易和冷载。
2. A2：把参考委托簿落到游戏运行脚本，完整市场列表/搜索、AI候选轮转与至少百币，并验证冷币当天交易。
3. B–E：宗族/政权等发行主体、宣传操盘、完整认购成本、期货多空杠杆/债务、退市、20种剧情与全球新闻、规模和多人。

4096/8192尚未压测，不是已支持容量；尚未 Workshop 首发。

## 工程与资源

默认 Maven 实测3.10.0，Java25.0.4.1，编译目标21。源码及增量构建/候选包峰值预留256MiB，08:43 UTC C盘可用74,891,210,752字节；完整旧库存加512MiB保守增长上界仍低于当日有效配额，未删除旧资料。原件及容量保护按通用存储策略复核，不将历史构建永久保留为默认。

跨产品可复用的是整数资金/资产守恒用例和清单打包合同。当前金融策略专属于本产品；工具留在tools内部，公共实机入口直接复用，不另建host/DLL/启动器。未来有第二个消费者时再提取稳定Java模块，避免在接口未验证前扩散原型。
