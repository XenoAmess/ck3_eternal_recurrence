# R0068：受控引擎资金费六格有限通过

2026-11-22，machine_id: 4-8e1c2f1861，scene20261122e／R0068。登记源码及Core47为 `12451f0bcf4dc2ffb04d5bc6b78e1e31fc25fa15`，Core47含234文件；640项既有软件窗口不在本场重新计数。本场使用独立、明确含合成出资的schema3引擎fixture，不是自然AI流动性、日常128手策略或原金融主线恢复。

Root手读实际Raw／audit／Whole、源角色与逐分Fraction核算后，六个受控引擎格均OBSERVED。公共run0／verify0、case与boundary有限通过，generic case_contract_qualified及gui_contract_qualified为true；严格保留 `SOURCE_CASE_OBSERVED_PENDING_PRODUCT_AGGREGATION`、business_pass=false和product_release_pass=false。它与原期货GUI有限6/6是不同范围，不能相加成整产品或十二格总完成率。

## 实付资金费与MTM分开

以下仓、合约、指数和关闭切片号码均为native story ID；原三仓永久ID分别为1／2／3。

| 受控仓／合约／指数 | 手数与实际mark | LONG侧MTM | 实际资金费 |
| --- | --- | --- | --- |
| p67／62／53 | 128手，106→96 | −1280分 | rate=＋1/1000，floor=12分，LONG抵押→SHORT可用 |
| n75／70／54 | 128手，96→107 | ＋1408分 | rate=−1/1000，floor=13分，SHORT抵押→LONG可用 |
| s82／62／53 | 1手，106→96 | −10分 | floor=0，只付MTM，不虚造递延1分 |

合约62真实成交129手／13674分／day0／VWAP106，合约70为128手／12288分／day0／VWAP96，day1真实oracle current／quality3；原≥10手、≥10000分及前日成交新鲜度等门不变。单手仓共享合格合约成交上下文，不能把它说成自身成交10手。开仓费用p／n／s各侧41／37／1分，合计158分，未混入MTM或资金费。

原声明的同日callback重试对三仓各46个typed捕获字段完全相同。第二自然日mark不变、last_settled_day=2，而旧execution_day=0已过day2−1的新鲜度门；last_funding_day仍1，余额／抵押未再扣，旧rate变量不代表又付款。

## 全额平仓、费用与完整权利

正常close控制请求后，SELL14／16／18与独立BUY15／17／19经原双边reduce／match实际满额。原native67／75／82均lots0／status2；P1关闭切片710／717／724及其历史128／128／1手保留，不能因正手数将已关闭slice当作新未平仓权利。六个账户reserved0，六原保证金及六slice保证金共12项remaining0，原status1／关闭status2分别保持。

平仓每侧手续费37／42／1分，共160分。p、n、s按LONG／SHORT顺序的六个最终free为98630／101214／101342／98500／99988／100008分，总计599682＝受控初始600000−开仓158−平仓160；两侧MTM与资金费各自净零。这只核六个测试账户，不宣称全市场现金600000守恒或把外部AI变化算成受控收益。

Whole记录11→180→671；终点financial audit670、账户273／币4／positions12／debt0。Whole-only native244为news_entry1，canonical570字节，原Whole／物理档完整保留，并非丢记录。外部AI、旧外仓及其他自然变化保留，不要求全图不变，也不据币4推导四次付费发行。全局news缺前置字段仍UNKNOWN，退出autosave_verified=false保持，不能补作送达或自动保存单独核实。

## 原失败、手工判定与真实闭场

三份SAVE日期raw53144328／53144352／53144376，恰两自然日；每档audit2＋Whole2＋Raw两组2，共6次原parser pass，三档总18。本稿和后继metadata consumer没有新读SAVE或parser pass。

baseline05原pipeline1／6.0092402秒保留：metadata-root误纳实体.ck3，AUTHOR-archive／ARCHIVE已0。严格续行06原0／62.7447909秒，从首次audit／Whole／Raw开始，无新SAVE、copy或archive；funding02原0／69.7147941秒、terminal02原0／73.2177339秒。R67原128MiB失败不改写。

公共phase先消费Root显式手工判断；闭场后08:09UTC的consumer02再以既有JSON计算，原0／0.4744139秒，unknown_required_fields为空，三仓六腿／gates／retry全true。它不填Root断言或生成OBSERVED／business pass，且明确next_day_and_close_not_evaluated=true；后两格仍来自Root终点手读核账，不授“Root判断自动化”。consumer的49个派生retry键不等同Root原46个typed捕获字段，也不是新增测试方法或不可变资金费收据。

Game7060／birth134398058218167988，Game／Host／Job／keeper／allocator均实际0，CAS16139→16140、done/resources[]。run原2576.4662186秒、START外层2579.6873911秒、verify0／0.7656191秒；这些含保存和人工核账，不授自然容量／性能目标。仅本受控engine六格有限通过；自然AI、逐日覆盖、20个债务剧情、全局通知、完整Mod与Workshop首发仍待，后继继续真实通知验证。

[三档、原失败、Root各phase／Fraction核账、后继consumer及闭场pins](../../docs/maintenance/evidence/2026-11-22-financial-markets-r0068-controlled-funding.json)。本文不执行Game、测试、编译、Git或SAVE读取，也不改R67旧失败。
