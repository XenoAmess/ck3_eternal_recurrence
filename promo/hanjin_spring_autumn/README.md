# 汉晋春秋

人物驱动的模组推荐系列。用户已确定 **第一期董卓，第二期曹操**，每期 5–30 分钟，不严格卡秒；重点是讲清模组，做出故事和趣味，让玩家想亲自试。

- [两期导演案总览](director.md)：章节分工、长度与跨集关系。
- [第一期董卓导演案](episode-01-dong-zhuo.md)：已定片名《洛阳炙手，公卿憎我，天下讨我》，片头独白以“且看我董卓”收束；手握天子与强兵，如何面对诸侯讨伐和未央之约；建议约 12–18 分钟，可伸缩。
- [第二期曹操导演案](episode-02-cao-cao.md)：三县起家、旧交与扩张、两份和约的取舍；建议约 10–16 分钟，可伸缩。
- [选角研究](research/character-selection.md)：曹操、刘备、孙坚等候选的具体理由。
- [董卓专题](research/dong-zhuo.md)：权臣、郿侯、西凉兵、本纪，以及未央之约的称病选择。
- [代码分析](research/code-analysis.md)：人物链、官制、服装、议和和组合覆盖问题。
- [本地模型使用与审阅](research/local-model-review.md)：28 次真实调用，采用与剔除的结论。
- [下载、空间与机器记录](research/operations.md)：订阅、下载、退订、Steam 离线及保留期限。

2026-10-31 已完成三件指定物品的订阅与下载，共 **12,791,293,914 B**，Steam 已恢复离线。导演案按源码编写，尚未启动本组合游戏或拍摄；组合存在需要实机确认的版本和宣战理由覆盖问题，详见代码分析。

指定组合：

- [汉晋春秋内测](https://steamcommunity.com/sharedfiles/filedetails/?id=3780919688)
- [战争谈判和议和机制内测](https://steamcommunity.com/sharedfiles/filedetails/?id=3820784621)
- [HanJIn_Clothes](https://steamcommunity.com/sharedfiles/filedetails/?id=3797664499)，由指定内测主模组的必需物品列表确认。

研究机器：`machine_id: 4-8e1c2f1861`。开始日期：2026-10-31。大型下载留在本机 Steam 管理的安装目录，分析临时文件与本地模型请求保存在 `C:/workspace/hanjin-spring-autumn-20261031/`；本机已核只有 C 盘，不套用其他机器的 D 盘路径。

研究与导演案使用本地 `qwen38-coder`，首轮 20 次 POST，董卓追问追加 5 次，两期导演案追加 3 次；合计 28 次、实际并发峰值 6。24 份传输完整候选、4 次长度截断。完整返回仍逐项审阅；旁白与实际游戏结果分别处理。

机器可读摘要：[安装与机器回执](research/machine-receipt.json)、[关键源码的 SHA-256](research/source-pins.json)、[逐次模型用量](research/local-model-usage.json)。第三方源码和美术载荷不入库。
