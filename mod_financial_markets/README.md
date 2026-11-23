# 期货与虚拟货币市场

[Steam 创意工坊：0.1.0-alpha.1](https://steamcommunity.com/sharedfiles/filedetails/?id=3844765196) · 首次公开 Alpha，完整实机与规模验收仍在推进。

一个独立 CK3 Mod，共用账本，包含虚拟货币现货与期货两个内部模块。面向 CK3 1.21.0。

- [综合设计](../docs/design/futures-and-virtual-currency-markets.md)
- [实现计划](docs/implementation-plan.md)
- [测试与验收方案](docs/test-and-acceptance-plan.md)
- [施工状态及实际验证](docs/development-status.md)
- [中文玩家手册](docs/player-guide.md)

当前为 Alpha 试用版，完整实机业务、规模及长期性能验收仍在推进，不宣称正式版或全产品验收通过。安装入口与已知范围见[Alpha 玩家说明](docs/releases/0.1.0-alpha.1-player-notes.md)。玩家运行时只使用 CK3 脚本及界面；tools 中 Java / Maven / Quarkus 是开发、构建与验证工具。

已写入原生模块的功能：

- 所有阶层成年 AI 的付费发行与轮转交易、个人／宗族／政权等发行主体、真实认购与退款、锁仓和增发、宣传及操盘行动。
- 共同资金账户、限价和即时委托、价格时间优先、部分成交、累计手续费、撤单、每日行情与市场窗口。
- 多空期货、保证金和杠杆、逐日盯市、永续资金费、真实盘口减仓和止损、有限违约基金及未付索偿。
- 独立价格参考、粮食／军需／商贸模组指数、30日退市流程、OTC与继承后的权利保留。
- 严重债务援助与重整、20种非血腥成人AI危机叙事、面向全部玩家的新闻队列。

默认活跃币上限4,096，AI每日轮转512名；2,048与8,192档可在游戏规则中选择。上限是配置，尚未授予相应性能信用。接口见[原生运行合同](docs/runtime-contract.md)、[价格来源](docs/oracle-runtime-contract.md)与[债务新闻](docs/debt-news-runtime.md)。
