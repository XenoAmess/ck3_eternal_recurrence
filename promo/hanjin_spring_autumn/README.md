# 汉晋春秋

人物驱动的模组推荐系列。用户已确定 **第一期董卓，第二期曹操**，每期 5–30 分钟，不严格卡秒；重点是讲清模组，做出故事和趣味，让玩家想亲自试。

- [两期导演案总览](director.md)：章节分工、长度与跨集关系。
- [第一期董卓导演案](episode-01-dong-zhuo.md)：已定片名《洛阳炙手，公卿憎我，天下讨我》，片头独白以“且看我董卓”收束；完整重剪版8分24.757秒，从190开局拍至191.6.1入朝死亡及继承后态。[交付记录](research/filming-03/delivery-snapshot.json)。
- [第二期曹操导演案](episode-02-cao-cao.md)：已定片名《帮过我的朋友，挡住了我的去路》，片头独白以“天下是我的。我不会停下。谁也别想拦我”收束；三县起家、旧交与扩张、两份和约的取舍；建议约 10–16 分钟，可伸缩。
- [选角研究](research/character-selection.md)：曹操、刘备、孙坚等候选的具体理由。
- [董卓专题](research/dong-zhuo.md)：权臣、郿侯、西凉兵、本纪，以及未央之约的实际入朝结局。
- [第一期完整续拍](research/filming-03/README.md)：从五月真实保存继续到191.6.1，伊阙胜利、未央入朝、董卓死亡及董璜继承；旧470秒版已被用户否定。
- [代码分析](research/code-analysis.md)：人物链、官制、服装、议和和组合覆盖问题。
- [本地模型使用与审阅](research/local-model-review.md)：28 次真实调用，采用与剔除的结论。
- [下载、空间与机器记录](research/operations.md)：订阅、下载、退订、Steam 离线及保留期限。

2026-10-31已完成三件指定物品的订阅与下载，共 **12,791,293,914 B**。第一期现已从190.1.1实际拍到191.6.1，共516游戏日；董卓入朝被谋杀，接着拍到死讯与董璜继承。新版删除全部下期／机制预告，正文按正常玩家口吻重写，战斗精简，结尾注明模组和Steam创意工坊搜索方式。完整组合业务未逐项穷举，不能由这条故事外推全部机制验收。Game正常退出，Steam后台仍离线；机器记录见完整续拍。

指定组合：

- [汉晋春秋内测](https://steamcommunity.com/sharedfiles/filedetails/?id=3780919688)
- [战争谈判和议和机制内测](https://steamcommunity.com/sharedfiles/filedetails/?id=3820784621)
- [HanJIn_Clothes](https://steamcommunity.com/sharedfiles/filedetails/?id=3797664499)，由指定内测主模组的必需物品列表确认。

研究机器：`machine_id: 4-8e1c2f1861`。开始日期：2026-10-31。大型下载留在本机 Steam 管理的安装目录，分析临时文件与本地模型请求保存在 `C:/workspace/hanjin-spring-autumn-20261031/`；本机已核只有 C 盘，不套用其他机器的 D 盘路径。

前期研究与导演案使用本地 `qwen38-coder`，首轮20次POST，董卓追问追加5次，两期导演案追加3次；这一历史批次合计28次、实际并发峰值6。24份传输完整候选、4次长度截断。后续拍摄、续拍及剪辑的新调用另留各自原件，不回填这28次；完整返回仍逐项审阅，模型候选与实际游戏结果分别处理。

机器可读摘要：[安装与机器回执](research/machine-receipt.json)、[关键源码的 SHA-256](research/source-pins.json)、[逐次模型用量](research/local-model-usage.json)。第三方源码和美术载荷不入库。
