# R0168：Root 已审十二单帧的术语索引

本页只记录 Root 已直接审阅的十二张 decoded PNG，完整逐帧 bytes/SHA、actual PTS/timebase 与原版 key/GUI 对应见 [index.json](index.json)、[Root 单帧声明](root-single-frame-review.json)和[stock 来源](stock-source-join.json)。既有三十候选的 pending 记录保存在 [candidate-index.json](candidate-index.json)，本次追加只提升其中十二帧的内容，不改旧报告。

| actual PTS | Root 实际读图内容 | PNG SHA-256 |
| --- | --- | --- |
| 254.133s | 集结军队维护 −3.8 金币/月；完整当前军事费用提示。 | `9bc1e8671e38f7acd7c090db00838c2a2de53bb25c7e11aa22bdbc8e5b2257ae` |
| 291.833s | 军队登船的额外维护说明；不证明登船实付。 | `c904af6a47f293e2dc962702b89add539fa56b4e8844bc725913781509aa99cf` |
| 528.133s | 野驴炮三个项目，各20/20。 | `c7dbb07fdba6b37ba5632ff5aed435c471a52cdf4988f53b5d1112387d995847` |
| 761.033s | Brest预期52天，1067年3月4日；会支付登船费；5660/4000。 | `81d10bc5cb27e999030275a59ea32104866f657aa821639e9e5cde553c504bad` |
| 1843.933s | Holding当地上限3680：基础2000、发展1200、沿海+25%、森林−10%。 | `6f7f816e46c077ab605afcdfdc743e67677e87aaaf01ae11d0ec2ba79d5e7764` |
| 1926.933s | 外层Holding提示仍在，完整补给上限child概念展开。 | `580f5d80221708e74986b511988f7a6d816038cf61de764531d5cc0379484779` |
| 1315.433s | Sea射石机9/10；旧onager目录名不作为中文兵种名称。 | `b0ff6d2135632da521b281cc219607cd0a79bf9aeb6a345986acdc58a865e6e8` |
| 2950.433s | Sea1086，291补给/300容量；HUD1067年1月15日；移动ETA1月20日剩5天，移动锁定。 | `11c9bf578287968bdb56fdb102ffd5fdc7e757cc052176368220e0f25a028aa9` |
| 2990.033s | 移动锁定child概念，简中原文描述完成一半进度。 | `93d817e18070e3c712702a2181638b5f4cc1a8438902a2e95a481384e0ca1a9d` |
| 3464.9s | Sea1086，分出新军队tooltip；不作为平分/整编/可用合并按钮。 | `c2c91e2e282fb3078d7c7419fb6169be570e1e82efc0c1f0b2e7046d30a91157` |
| 3524.9s | 真实postmerge Main6746，补给116/300，将领portrait，HUD1月20日。 | `81b327192c1ed807870448277d4aa6712523771b7c8ea9122636002a6a4af8ca` |
| 3574.9s | 真实postmerge Main6746，补给116/300，将领portrait，HUD1月20日。 | `a645b7f288348f8fdb7455ec106a51bed6efeef066c0dbd3e5ba2438f244f30c` |

原清单整项新增 TERM-03（Holding 上限/breakdown）、TERM-06（下令前 ETA/进军与登船警告）、TERM-11（月维护提示、同日暂停 cash 读数与登船费警告）。加上 R0165 已授01/02/05/07，当前7/11，约64%，只计固定术语清单。04欠携带补给概念child；08有锁定及概念像素，但欠同帧 native progress；09欠每月补员勾选框/费用提示；10欠完整平分/整编/可用合并提示。

day4 两份 hover snapshot 均 raw53147256、public14/native13、paused，HUD 是1月15日，正文1月20日是 ETA；不能写成实际已到达或1月20日观测。该 snapshot 无 Strength 行，不能挪用 Jan11 的 native progress。射石机9/10与野驴炮3×20/20按真实中文兵种分开，不按目录名混称。

R0168 raw 为4955431127B/SHA `48fde0d7645d9ba7331dcd2a4b8dc93c93474ad2fd9cb95a59aea059e13481b9`，实际 duration3584.933s、107548frames/packets、1920×1080/30fps、无音频，完整机器媒体及严格decode PASS。这里复用既有完整audit，未重hash原片、启动媒体或游戏。机器PASS及十二单帧不证明连续clean spans、全部三十候选审阅、完整1×观看或signoff；这些门槛保持false。

3524.9s与3574.9s只授postmerge界面6746、116/300、将领portrait和Jan20；实际合军整数公式与身份由 [独立合军索引](../r0168-merge/index.json)闭合，不能由这两帧倒推出原始API时间码或容量截断。登船费用提示与海军月维护不是已付款流水；NET 已包含军费，不再扣一次。
