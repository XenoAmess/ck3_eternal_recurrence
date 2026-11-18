# 金融市场 Mod：实现计划、验收方案与 A0 开工交付

2026-11-18，machine_id: 4-8e1c2f1861。

用户要求“输出实现计划，以及测试验收方案。然后，给我开工。”本包完成两份方案并交付第一批代码；不是整款 Mod 完工或实机通过。

## 方案与维护决定

- [实现计划](../../mod_financial_markets/docs/implementation-plan.md)：一个 Mod / 一个 Workshop 条目，内部拆金融底座、现货、期货、主体宣传、债务新闻。按 A0→A1存储日历→A2完整每日现货→B政治操盘→C多空杠杆→D退市/世界后果→E规模扩展推进。
- [测试验收方案](../../mod_financial_markets/docs/test-and-acceptance-plan.md)：精确资金与供应守恒、发行成本、委托、AI、日清算、穿仓债务、价格源、退市、继承冷载、20种非细节离世叙事、全世界通知、多人和性能。
- [施工状态](../../mod_financial_markets/docs/development-status.md)、[原生实现边界](../../mod_financial_markets/docs/a0-runtime-notes.md)、[原版来源索引](../../mod_financial_markets/docs/a0-native-sources.json)。

最终4096币是标准目标，2048保守、8192扩展、16384探索，均未压测。A0仅32个累计登记身份，用于先查清存储和引擎语义。

## 首批源码

产品目录 mod_financial_markets，命名空间xfm_。14个运行文件、11个effect、中英各26键。收费发行个人币、独立币/持仓故事、有限资金双向整手报价、每日有限AI候选、玩家决议/角色互动与回执。每手100币；微型R0支付或限制5.6金；双方各0.3%手续费，最低各1分。创建对象先清旧alias并验证身份，报价绑定事件币身份、revision及金额。本金和费用先转分再算，避免过早在金币小数上截断。

Java参考核心另实现整数账本、稳定主体ID、有限供应、价格时间优先限价撮合、部分成交、原订单累计费、冻结/撤单、同受益人拒绝及失败回滚。**游戏原型仍是有限池swap，未采用完整订单簿。** Java工具不构成玩家运行依赖。

本包仍有明确缺口：尚无完整市场列表、全世界公平AI发现、合法继承后的发行管理入口、已证存档寿命、完整认购/宗族政治与宣传操盘、期货清算、退市、债务剧情和全球通知。这些继续按阶段施工，不因参考模型或设计文档存在而授完成。

## 实际验证

产品源码：[b021c196d62a4b1c4eca844229bbe94542fc2dbd](https://github.com/XenoAmess/ck3_eternal_recurrence/commit/b021c196d62a4b1c4eca844229bbe94542fc2dbd)。期间同步并线性接收其他产品提交，未修改其内容。

| 验证 | 实际结果 |
| --- | --- |
| 本地 FinancialMarketTest | 26项全通过，Maven27.844s |
| 本地 ListingFundingTest / PoolQuoteTest | 4+5项全通过，Maven14.594s |
| 本地 BuildContractTest + Quarkus verify | 5项全通过，Maven15.765s，工具打包完成 |
| 最终原生静态校验 | 14文件BOM/清单/定义/引用/本地化一致，exit0 |
| 官方CI | [44273780360，attempt2](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/44273780360/attempts/2)全链成功，4套40项，0失败/错误/跳过；含源码校验及候选构建 |
| 候选02 | sourceRevision=b021c196d…，14文件实际bytes/SHA与当前源码一致，manifest及content分开 |
| CK3业务/保存/性能 | NOT_RUN，未启动/注入游戏，whole_product_pass=false |

失败和重试保留：[首次44272883501](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/44272883501)因Windows checkout历史promo长路径失败，未到测试；补core.longpaths后已通过检出。中间旧源44273334643因新源码替代而提交取消，最终源44273780360的attempt1因官方Maven HTTP完整body超时失败，attempt2原样重试成功。未改最低Maven版本、校验pin或弱化通过条件。

## 原件与后续实机

候选01保留旧输入，最终候选02在 C:/workspace/ck3-market-task-20261118/candidate-a0-02/；主证据摘要见[implementation-summary.json](evidence/2026-11-18-financial-markets-a0/implementation-summary.json)。本地测试报告、官方4份JUnit报告、失败日志和CI元数据位于同一外置任务根，按通用存储策略复核，不默认永久保留全部派生物。

本机公共Steam离线探针08:43:20Z返回unavailable/cdp_not_enabled，native_provider_unavailable=invalid_input，不能作启动凭据。无当前1.21产品公共adapter业务资格，不借1.20 DLL或抢前台运行。下一包先补后台/离线资格，再按公共 plan/prepare/allocate/preflight/run/verify 核对金额、故事身份、日历、无地AI实际发行、死亡/继承和保存冷载。

始终保持全部现金（含费用和受限款）与币总量对账。具体首场数据为[发行100金/买方30金、一手来回总现金130金及10000币](../../mod_financial_markets/acceptance/a0-business-vectors.json)，目前是预期数据，未在游戏执行。

资源：本轮峰值预留256MiB，未删除旧资料、未运行本地模型或旧自动游玩。收束时C盘仍约74.8GB可用，候选及增量工具输出处于预留范围内。
