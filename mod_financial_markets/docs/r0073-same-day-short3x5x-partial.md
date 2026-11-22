# R0073：同日3倍／5倍做空已保存，整案PARTIAL

2026-11-23，machine_id: `4-8e1c2f1861`。实际装载来源`0164dcbe8dce186762afd828010c155de966201b`，scene22j／runtime-futures35；从R72累计D30的最新物理档继续。三份SAVE均为raw53152080、financial319，零新增自然日，没有重ARM、重发旧交易或以新世界替换旧状态。

| 正常GUI动作 | 已保存的成交与抵押 |
| --- | --- |
| SHORT739，3倍1手 | 94分成交，新仓232；玩家空方保证金32分、独立多方94分，玩家手续费1分、对手增量手续费1分 |
| SHORT740，5倍1手 | 同价94分成交，新仓233；空方保证金19分、多方94分，玩家手续费1分；原BUY累计手续费仍1分，本次增量0分 |

两笔均与原独立BUY696／账户2175（native8008、holder和受益人32995）成交；PRIMARY账户2／native54的holder和受益人为31254。合约为既有dated27／native83903530，到期金融日330，本场未到期。PRIMARY可用／冻结8176／299→8143／331→8123／350，对手0／700→19／680→38／661；原BUY剩余2→1→0、累计gross0→94→188、订单预留227→113→0。这里的手续费0是已读累计1→1的增量，不把缺字段当0。

Root闭场后按三份原读回独立核算两笔成交。三倍档至五倍档原有232条position canonical全部一致，所有不相关旧记录不变；Whole21061→21066→21071，每步新增5、变化7、缺失0，保留真实相关账本差异，不称交易前后全图相等。

## 原失败和凭据边界

基线原pipeline退出1／51.4107973秒，Whole构造器退出1／3.0579103秒：完整audit18876495字节超过原16MiB输入帽。后继只去JSON空白，完整值相等且无字段删除；复用已成功的SAVE／archive／audit，首次Whole读回及后缀完成，不重SAVE。恢复摘要保留原两个1，21061条Whole及globals与R72来源精确相同、20921条投影无差异，基线阶段于17:39:58 UTC接受。两笔后态pipeline04原0／112.8637648秒和0／114.1342469秒，不是旧失败改成0。

新仓各有P1十项核心原始字段，包括双侧intent0；`buy_close_source_id`、`sell_close_source_id`和`slice_source_position_id`在本次开仓中不存在，不填0、不回填历史。原helper把三条件字段也列为必需，保留`observed=false`及missing清单；最终Root辅助作者在要求该helper为true的断言处停止。Root未在原17:49:16 UTC退出预留前发表最终阶段，公开run2／verify2、原timeout与PARTIAL保持；闭场后的数核不倒签phase、不新增OBSERVED格，原GUI有限累计6/6不增加。

## 正常闭场与后继

Game16244实际正常0、Host0、Native Job0、cleanup与thread结束均有原件；run于17:49:46 UTC结束，原2081.4589779秒，fresh verify在17:51:37 UTC退出2／0.4244222秒且正常退出合格。keeper和allocator实际0，STOP0，CAS16238→16239 done／resources[]。正常闭场不升级业务；退出autosave_verified=false，不宣称另核退出自动保存。

后继只沿最新short5档（222163234字节，SHA-256 `ab386f902834079748dd7fd8f4df1d721d1815a48c225965c1177a2b7f939ff6`）继续，不重交易。645项软件仍属原来源窗口，本场零新增测试；35日、容量／395日性能、20剧情实机、全游戏送达、完整产品与Workshop首发均未授。当前诊断必需原件按存储策略限期保护，派生资产退役不改写失败事实。

[原收据、三档来源、数核及闭场完整pins](../../docs/maintenance/evidence/2026-11-23-financial-markets-r0073-same-day-shorts.json)。R72已完成的缓存／副本退役及NTFS保全另见[维护摘要](r0072-closed-maintenance.md)，不混算业务进展。
